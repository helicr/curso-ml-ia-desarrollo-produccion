"""Pruebas estáticas de los workflows del agente (no ejecutan GitHub Actions: leen los archivos y comprueban lo que se promete).

Cómo se ejecutan (desde la carpeta del laboratorio, con el entorno del curso):
    python -m pytest -q pruebas -p no:cacheprovider

Qué comprueban, y por qué importa (imitan las de S4, laboratorio-produccion-e2e/pruebas/test_nueva_version.py):
    * el YAML es válido (PyYAML lee la clave `on` como True: ojo al leerla);
    * los disparadores son los prometidos y las ramas de ensayo que cuentan las cabeceras coinciden con los `on: push`;
    * permisos mínimos por trabajo; el environment «produccion» solo en publicar; `working-directory: .` donde no hay checkout;
    * nueva versión y rollback comparten grupo de concurrency (y el CI y la evaluación, no);
    * los comandos llaman a módulos, órdenes y opciones que existen de verdad en 04-Proyecto-Base, y a scripts que existen aquí;
    * el modelo de LLM de los workflows es el de la referencia del agente (misma huella) y los escenarios hacen lo que dicen
      (igual → misma huella; prompt nuevo → otra huella; rechazo → rechazada aunque todo salga perfecto);
    * los scripts de apoyo (aplicar_prompt, historial_agente, resumen_evaluacion) funcionan;
    * los fragmentos de Python y de bash de los pasos no tienen errores de sintaxis.
"""
import ast
import fnmatch
import glob
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
import yaml

LAB = Path(__file__).resolve().parents[1]
RAIZ = LAB.parents[2]
PROYECTO = RAIZ / '04-Proyecto-Base'
CI, EVALUAR, NUEVA, ROLLBACK = (LAB / n for n in ('agente-ci.yml', 'agente-evaluar.yml', 'agente-nueva-version.yml', 'agente-rollback.yml'))
TODOS = [CI, EVALUAR, NUEVA, ROLLBACK]
ACCIONES = {'actions/checkout@v4', 'actions/setup-python@v5', 'actions/cache@v4', 'actions/upload-artifact@v4', 'actions/download-artifact@v4'}


def cargar(ruta):
    return yaml.safe_load(ruta.read_text(encoding='utf-8'))


def disparadores(wf):
    """PyYAML (YAML 1.1) lee `on` como el booleano True: se busca de las dos maneras."""
    return wf.get('on', wf.get(True))


def pasos(job):
    return job.get('steps', [])


def scripts(wf):
    """Todos los `run:` del workflow, con el nombre del trabajo y del paso."""
    for nombre, job in wf['jobs'].items():
        for i, paso in enumerate(pasos(job)):
            if 'run' in paso:
                yield nombre, paso.get('name', f'paso {i}'), paso['run']


def todo_el_texto(wf):
    return '\n'.join(c for _, _, c in scripts(wf))


@pytest.fixture(scope='module')
def ci():
    return cargar(CI)


@pytest.fixture(scope='module')
def evaluar():
    return cargar(EVALUAR)


@pytest.fixture(scope='module')
def nueva():
    return cargar(NUEVA)


@pytest.fixture(scope='module')
def rollback():
    return cargar(ROLLBACK)


# ------------------------------------------------------------------------------------------------ YAML y disparadores
@pytest.mark.parametrize('ruta', TODOS, ids=lambda r: r.name)
def test_los_archivos_son_yaml_validos(ruta):
    wf = cargar(ruta)
    assert isinstance(wf, dict) and wf['name'] and wf['jobs']
    assert True in wf and 'on' not in wf                     # PyYAML lee `on:` como True (YAML 1.1)


def test_disparadores_de_cada_workflow(ci, evaluar, nueva, rollback):
    esperados = {'ci': (ci, 'lab/agente/**', {'push', 'workflow_dispatch'}),
                 'evaluar': (evaluar, 'lab/agente-evaluar/**', {'push', 'workflow_dispatch'}),
                 'nueva': (nueva, 'lab/agente-version/**', {'push', 'workflow_dispatch'}),
                 'rollback': (rollback, 'lab/agente-rollback/**', {'push', 'workflow_dispatch'})}
    for nombre, (wf, rama, eventos) in esperados.items():
        d = disparadores(wf)
        assert set(d) == eventos, f'{nombre}: eventos distintos de los prometidos'
        assert d['push']['branches'] == [rama], f'{nombre}: el push solo puede venir de {rama}'
        assert not set(d['push']) & {'branches-ignore', 'tags', 'paths'}, f'{nombre}: nada de etiquetas ni de ramas sin filtro'


def test_las_ramas_de_ensayo_de_los_workflows_no_se_pisan(ci, evaluar, nueva, rollback):
    """Un push a lab/agente/x no debe lanzar también la evaluación ni la nueva versión: los patrones no se solapan con otros."""
    patrones = {n: disparadores(w)['push']['branches'][0] for n, w in (('ci', ci), ('evaluar', evaluar), ('nueva', nueva), ('rollback', rollback))}
    ejemplos = {'ci': 'lab/agente/ci', 'evaluar': 'lab/agente-evaluar/3b', 'nueva': 'lab/agente-version/igual', 'rollback': 'lab/agente-rollback/v1'}
    for dueño, rama in ejemplos.items():
        lanzan = [n for n, p in patrones.items() if fnmatch.fnmatch(rama, p)]
        assert lanzan == [dueño], f'la rama {rama} lanza {lanzan} y solo debería lanzar {dueño}'


def _ramas_documentadas(ruta, patron):
    cabecera = ruta.read_text(encoding='utf-8').split('\non:\n')[0]
    return sorted(set(re.findall(patron, cabecera)))


def test_las_ramas_de_ensayo_de_nueva_version_coinciden_con_el_on_push_y_con_la_logica(nueva):
    documentadas = _ramas_documentadas(NUEVA, r'lab/agente-version/([\w-]+)')
    assert documentadas == ['igual', 'prompt-nuevo', 'rechazo']
    patron = disparadores(nueva)['push']['branches'][0]
    assert all(fnmatch.fnmatch(f'lab/agente-version/{r}', patron) for r in documentadas)
    env = nueva['env']
    # el nombre de la rama elige la variante: prompt nuevo en prompt-nuevo y rechazo; tolerancia -0.10 solo en rechazo
    assert "contains(github.ref_name, 'prompt-nuevo')" in env['PROMPT'] and "contains(github.ref_name, 'rechazo')" in env['PROMPT']
    assert "contains(github.ref_name, 'rechazo') && '-0.10'" in env['TOLERANCIA_ENTRADA']
    assert 'igual' not in env['PROMPT'], 'la rama «igual» no cambia nada: el prompt es el actual'
    entradas = disparadores(nueva)['workflow_dispatch']['inputs']
    assert set(entradas) == {'prompt', 'tolerancia'} and entradas['prompt']['options'] == ['actual', 'nuevo'] and entradas['prompt']['default'] == 'actual'


def test_ramas_documentadas_del_rollback_y_de_la_evaluacion(rollback, evaluar):
    assert _ramas_documentadas(ROLLBACK, r'lab/agente-rollback/[\w<>-]+')
    assert fnmatch.fnmatch('lab/agente-rollback/v1-sin-comprobar', disparadores(rollback)['push']['branches'][0])
    assert 'sin-comprobar' in rollback['jobs']['rollback']['env']['COMPROBAR_IMAGEN']
    entradas = disparadores(rollback)['workflow_dispatch']['inputs']
    assert set(entradas) == {'version', 'comprobar_imagen'} and entradas['comprobar_imagen']['default'] is True
    assert set(disparadores(evaluar)['workflow_dispatch']['inputs']) == {'modelo', 'tolerancia'}


def test_todo_trabajo_tiene_limite_de_tiempo_y_las_acciones_fijadas():
    for ruta in TODOS:
        for nombre, job in cargar(ruta)['jobs'].items():
            assert isinstance(job.get('timeout-minutes'), int), f'{ruta.name}/{nombre}: sin timeout-minutes'
            for p in pasos(job):
                if 'uses' in p:
                    assert p['uses'] in ACCIONES, f'{ruta.name}/{nombre}: acción no revisada {p["uses"]}'


def test_el_tiempo_limite_de_la_evaluacion_es_generoso_y_esta_comentado(evaluar, nueva):
    assert evaluar['jobs']['evaluar']['timeout-minutes'] >= 90
    assert nueva['jobs']['evaluar']['timeout-minutes'] >= 90
    texto = EVALUAR.read_text(encoding='utf-8')
    assert 'timeout-minutes: 120' in texto and '14 min' in texto and '15 min 27 s' in texto   # tope frente a lo medido


# ------------------------------------------------------------------------------------------------ grafo de trabajos
def test_cadena_de_trabajos_de_nueva_version(nueva):
    jobs = nueva['jobs']
    assert list(jobs) == ['evaluar', 'construir-y-probar', 'publicar', 'referencia']
    assert 'needs' not in jobs['evaluar']
    assert jobs['construir-y-probar']['needs'] == 'evaluar'
    assert set(jobs['publicar']['needs']) == {'evaluar', 'construir-y-probar'}
    assert set(jobs['referencia']['needs']) == {'evaluar', 'construir-y-probar', 'publicar'}


def test_cadena_de_trabajos_del_ci_y_de_la_evaluacion(ci, evaluar, rollback):
    assert list(ci['jobs']) == ['pruebas', 'humo'] and ci['jobs']['humo']['needs'] == 'pruebas'
    assert list(evaluar['jobs']) == ['evaluar'] and list(rollback['jobs']) == ['rollback']


def test_igual_y_rechazada_no_llegan_a_construir(nueva):
    assert nueva['jobs']['construir-y-probar']['if'] == "needs.evaluar.outputs.decision == 'aceptada'"
    salidas = nueva['jobs']['evaluar']['outputs']
    assert {'decision', 'version_referencia', 'version_nueva', 'huella', 'etiqueta'} <= set(salidas)
    rechazo = [p for p in pasos(nueva['jobs']['evaluar']) if 'Rechazar' in p.get('name', '')]
    assert len(rechazo) == 1 and 'exit 1' in rechazo[0]['run'] and "decision == 'rechazada'" in rechazo[0]['if']
    assert pasos(nueva['jobs']['evaluar'])[-1] is rechazo[0], 'el rojo va el ÚLTIMO, cuando el resumen y los artefactos ya están escritos'
    cuerpo = todo_el_texto(nueva)
    assert 'GITHUB_STEP_SUMMARY' in cuerpo and 'codigo" = "2"' in cuerpo     # solo el código 2 (no se pudo comparar) corta antes del resumen


def test_la_huella_previa_evita_instalar_ollama_cuando_es_igual(nueva):
    job = nueva['jobs']['evaluar']
    previa = [p for p in pasos(job) if p.get('id') == 'previa']
    assert len(previa) == 1 and 'registro.huella_agente' in previa[0]['run'] and "referencia-agente.json" in previa[0]['run']
    asi = [p for p in pasos(job) if any(k in p.get('name', '') for k in ('Ollama', 'Descargar el modelo', 'Evaluar el agente', 'Comparar con'))]
    assert len(asi) == 5 and all(p.get('if') == "steps.previa.outputs.igual != 'true'" for p in asi)


def test_los_pasos_que_usan_una_salida_la_tienen_definida(nueva):
    for nombre, job in nueva['jobs'].items():
        for p in pasos(job):
            for ref in re.findall(r'needs\.(\w[\w-]*)\.outputs\.(\w+)', yaml.dump(p)):
                assert ref[0] in job.get('needs', []) or ref[0] == job.get('needs'), f'{nombre} usa needs.{ref[0]} sin declararlo'
                assert ref[1] in nueva['jobs'][ref[0]]['outputs'], f'{nombre} usa la salida {ref[1]} que {ref[0]} no declara'
        for env_var, valor in (job.get('env') or {}).items():
            for ref in re.findall(r'needs\.(\w[\w-]*)\.outputs\.(\w+)', str(valor)):
                assert ref[1] in nueva['jobs'][ref[0]]['outputs'], f'{nombre}.{env_var}: salida {ref[1]} sin declarar'
    ids = {p.get('id') for p in pasos(nueva['jobs']['evaluar'])}
    for salida, valor in nueva['jobs']['evaluar']['outputs'].items():
        paso = re.search(r'steps\.(\w+)\.outputs\.(\w+)', valor)
        assert paso and paso.group(1) in ids, f'la salida {salida} no sale de un paso con id'


# ------------------------------------------------------------------------------------------------ environment, permisos y concurrency
def test_el_environment_produccion_solo_esta_en_publicar(ci, evaluar, nueva, rollback):
    con_environment = {n: j['environment'] for n, j in nueva['jobs'].items() if 'environment' in j}
    assert list(con_environment) == ['publicar']
    entorno = con_environment['publicar']
    assert (entorno['name'] if isinstance(entorno, dict) else entorno) == 'produccion'
    for wf in (ci, evaluar, rollback):
        assert not any('environment' in j for j in wf['jobs'].values()), 'solo la publicación espera aprobación; el rollback se aprueba al revisar el PR'


def test_permisos_minimos_por_trabajo(ci, evaluar, nueva, rollback):
    for wf in (ci, evaluar, nueva, rollback):
        assert wf['permissions'] == {'contents': 'read'}
    esperados = {
        'evaluar': {'contents': 'read'},
        'construir-y-probar': {'contents': 'read'},
        'publicar': {'contents': 'read', 'packages': 'write'},
        'referencia': {'contents': 'write', 'pull-requests': 'write'},
    }
    for nombre, job in nueva['jobs'].items():
        assert job['permissions'] == esperados[nombre], f'{nombre}: permisos distintos de los mínimos'
    escribe = {n: {k for k, v in j['permissions'].items() if v == 'write'} for n, j in nueva['jobs'].items()}
    assert [n for n, e in escribe.items() if 'packages' in e] == ['publicar']
    assert [n for n, e in escribe.items() if 'contents' in e] == ['referencia']
    assert [n for n, e in escribe.items() if 'pull-requests' in e] == ['referencia']
    assert rollback['jobs']['rollback']['permissions'] == {'contents': 'write', 'pull-requests': 'write', 'packages': 'read'}
    for wf in (ci, evaluar):                      # ni el CI ni la evaluación escriben nada en el repositorio ni en GHCR
        assert all('permissions' not in j or j['permissions'] == {'contents': 'read'} for j in wf['jobs'].values())


def test_solo_hay_el_github_token_y_ningun_secreto_propio():
    for ruta in TODOS:
        texto = ruta.read_text(encoding='utf-8')
        assert set(re.findall(r'secrets\.(\w+)', texto)) <= {'GITHUB_TOKEN'}, ruta.name
        assert 'id-token' not in texto
        assert not re.search(r'\b[A-Z]:\\|/home/(?!runner)|/Users/', texto), f'{ruta.name}: rutas personales'


def test_los_trabajos_sin_checkout_no_heredan_la_carpeta_del_proyecto(nueva):
    # Un trabajo sin checkout no tiene 04-Proyecto-Base: si hereda defaults.run.working-directory, su primer «run» falla (S4, 22/11/2026).
    for ruta in TODOS:
        wf = cargar(ruta)
        carpeta = ((wf.get('defaults') or {}).get('run') or {}).get('working-directory')
        if not carpeta or carpeta == '.':
            continue
        for nombre, job in wf['jobs'].items():
            usa_checkout = any(str(p.get('uses', '')).startswith('actions/checkout') for p in pasos(job))
            if any('run' in p for p in pasos(job)) and not usa_checkout:
                propia = ((job.get('defaults') or {}).get('run') or {}).get('working-directory')
                assert propia is not None, f'{ruta.name}/{nombre}: no descarga el repositorio pero hereda working-directory={carpeta}'
    assert nueva['jobs']['publicar']['defaults']['run']['working-directory'] == '.'
    assert not any(str(p.get('uses', '')).startswith('actions/checkout') for p in pasos(nueva['jobs']['publicar']))


def test_concurrency_nueva_version_y_rollback_comparten_grupo(ci, evaluar, nueva, rollback):
    assert nueva['concurrency'] == rollback['concurrency'] == {'group': 'agente-version', 'cancel-in-progress': False}
    # el CI y la evaluación NO tocan producción: grupos propios, y distintos del de producción
    assert ci['concurrency']['group'].startswith('agente-ci') and ci['concurrency']['cancel-in-progress'] is True
    assert evaluar['concurrency']['group'].startswith('agente-evaluar') and evaluar['concurrency']['cancel-in-progress'] is False
    grupos = {w['concurrency']['group'] for w in (nueva, rollback)}
    assert not any(w['concurrency']['group'].startswith('agente-version') for w in (ci, evaluar)) and grupos == {'agente-version'}
    for ruta in (NUEVA, ROLLBACK):                 # la razón está explicada en el propio archivo
        texto = ruta.read_text(encoding='utf-8')
        assert re.search(r'MISMO grupo|el mismo grupo', texto, re.I) and 'bloquea' in texto, ruta.name


# ------------------------------------------------------------------------------------------------ ollama, mlflow y modelo
def test_la_evaluacion_con_ollama_en_el_runner(evaluar, nueva):
    for wf, job in ((evaluar, 'evaluar'), (nueva, 'evaluar')):
        env = wf['env']
        assert str(env['OLLAMA_CONTEXT_LENGTH']) == '8192' and str(env['MLFLOW_ENABLE_ASYNC_TRACE_LOGGING']).lower() == 'false'
        assert re.fullmatch(r'\d+\.\d+\.\d+', str(env['OLLAMA_VERSION']))
        texto = todo_el_texto(wf)
        assert 'ollama.com/install.sh' in texto and 'OLLAMA_VERSION="$OLLAMA_VERSION"' in texto
        assert 'ollama serve' in texto and 'ollama pull "$MODELO"' in texto
        assert 'evaluacion evaluar --llm ollama --json evaluacion.json' in texto and 'evaluacion comparar' in texto
        caches = [p for p in pasos(wf['jobs'][job]) if str(p.get('uses', '')).startswith('actions/cache')]
        assert len(caches) == 1 and caches[0]['with']['path'] == '~/ollama-modelos' and 'env.MODELO' in caches[0]['with']['key']
    texto = EVALUAR.read_text(encoding='utf-8')
    for palabra in ('780 s', '45067018776', 'qwen2.5:3b', '0.40.17'):   # cifras medidas en el run real, no «a medir»
        assert palabra.lower() in texto.lower(), palabra


def test_el_modelo_de_los_workflows_es_el_de_la_referencia_del_agente(evaluar, nueva):
    ref = json.loads((PROYECTO / 'agentes' / 'referencia-agente.json').read_text(encoding='utf-8'))
    llm = (PROYECTO / 'ia_mlops' / 'agente' / 'llm.py').read_text(encoding='utf-8')
    por_defecto = re.search(r"MODELO_POR_DEFECTO = '([^']+)'", llm).group(1)
    assert por_defecto == ref['llm'], 'la referencia se midió con otro modelo que el de llm.py'
    assert por_defecto in evaluar['env']['MODELO'] and por_defecto in evaluar['env']['CURSO_LLM_MODELO']
    assert evaluar['env']['MODELO'] == evaluar['env']['CURSO_LLM_MODELO'] and "inputs.modelo ||" in evaluar['env']['MODELO']
    assert nueva['env']['MODELO'] == nueva['env']['CURSO_LLM_MODELO'] == ref['llm'], 'misma huella que la referencia: mismo modelo que en clase'
    entradas = disparadores(evaluar)['workflow_dispatch']['inputs']
    assert entradas['modelo']['default'] == ref['llm']


def test_los_artefactos_de_la_evaluacion_y_de_nueva_version(evaluar, nueva):
    def subidos(wf):
        return {p['with']['name']: p['with']['path'] for j in wf['jobs'].values() for p in pasos(j) if str(p.get('uses', '')).startswith('actions/upload-artifact')}
    ev = subidos(evaluar)
    assert set(ev) == {'evaluacion-agente', 'mlflow-agente'}
    assert 'evaluacion.json' in ev['evaluacion-agente'] and 'mlflow-agente' in ev['mlflow-agente'] and 'mlruns' in ev['mlflow-agente']
    nv = subidos(nueva)
    assert set(nv) == {'candidata', 'mlflow-agente', 'imagen'}
    bajados = {p['with']['name'] for j in nueva['jobs'].values() for p in pasos(j) if str(p.get('uses', '')).startswith('actions/download-artifact')}
    assert bajados == {'candidata', 'imagen'}, 'todo lo que se baja lo sube un trabajo anterior'
    for nombre, job in nueva['jobs'].items():
        for p in pasos(job):
            if str(p.get('uses', '')).startswith('actions/download-artifact'):
                subidor = {'candidata': 'evaluar', 'imagen': 'construir-y-probar'}[p['with']['name']]
                assert subidor in job['needs'] or subidor == job['needs'], f'{nombre} baja «{p["with"]["name"]}» sin depender de {subidor}'
    for wf in (evaluar, nueva):
        for j in wf['jobs'].values():
            for p in pasos(j):
                if str(p.get('uses', '')).startswith('actions/upload-artifact'):
                    assert p['with']['retention-days'] <= 14


def test_la_candidata_lleva_lo_que_usa_el_pr(nueva):
    empaquetar = '\n'.join(c for n, p, c in scripts(nueva) if 'Empaquetar' in p)
    for archivo in ('referencia-anterior.json', 'crear-referencia', 'referencia-agente.json', 'decision.json', 'registro.json', 'prompt.txt'):
        assert archivo in empaquetar, archivo
    referencia = '\n'.join(c for n, _, c in scripts(nueva) if n == 'referencia')
    for archivo in ('paquete/referencia-agente.json', 'paquete/referencia-anterior.json', 'paquete/decision.json', 'paquete/prompt.txt'):
        assert archivo in referencia, archivo


# ------------------------------------------------------------------------------------------------ GHCR, PR y push
def test_solo_publicar_hace_login_y_push_en_ghcr(nueva, ci, evaluar, rollback):
    for nombre, paso, cuerpo in scripts(nueva):
        if 'docker push' in cuerpo or 'docker login' in cuerpo:
            assert nombre == 'publicar', f'{nombre}/{paso}: solo «publicar» inicia sesión en GHCR y sube la imagen'
    publicar = '\n'.join(c for n, _, c in scripts(nueva) if n == 'publicar')
    assert 'docker push "$destino"' in publicar and 'ghcr.io/${propietario}/interfaz-agente:${ETIQUETA}' in publicar
    assert "tr '[:upper:]' '[:lower:]'" in publicar          # GHCR exige minúsculas
    assert 'docker push' not in todo_el_texto(ci) + todo_el_texto(evaluar) + todo_el_texto(rollback)


def test_la_etiqueta_de_la_imagen_es_la_misma_en_publicar_en_el_historial_y_en_el_rollback(nueva, rollback):
    assert "etiqueta=v{nueva}-{huella}" in todo_el_texto(nueva)
    assert 'etiqueta=interfaz-agente:v{v}-{d[\'huella_agente\']}' in todo_el_texto(rollback)
    historial = importlib.import_module('historial_agente')
    assert historial.etiqueta_imagen({'version': 3, 'huella_agente': 'abc'}) == 'interfaz-agente:v3-abc'


def _pushes(texto):
    return re.findall(r'^\s*git push[^\n]*', texto, re.M)


@pytest.mark.parametrize('ruta, trabajos_con_push', [(NUEVA, {'referencia'}), (ROLLBACK, {'rollback'})], ids=lambda x: getattr(x, 'name', ''))
def test_ningun_paso_empuja_a_develop_ni_a_main(ruta, trabajos_con_push):
    wf = cargar(ruta)
    con_push = set()
    for nombre, paso, cuerpo in scripts(wf):
        for push in _pushes(cuerpo):
            con_push.add(nombre)
            assert push.strip().startswith('git push origin "refs/heads/${rama}"'), f'{nombre}/{paso}: push distinto del de la rama del PR: {push}'
        assert not re.search(r'git push[^\n]*\b(develop|main|master|HEAD:|--force|-f\b)', cuerpo), f'{nombre}/{paso}: push peligroso'
        assert not re.search(r'git (merge|rebase|reset --hard)|gh pr merge|--admin', cuerpo), f'{nombre}/{paso}: no se fusiona desde el workflow'
        if _pushes(cuerpo):
            assert re.search(r'rama="referencia-agente/', cuerpo) and re.search(r'case "\$rama" in main\|develop\|master\)', cuerpo)
            assert 'git checkout -b "$rama"' in cuerpo and 'gh pr create' in cuerpo and '--base "$BASE"' in cuerpo
            assert cuerpo.count('git add') == 1
    assert con_push == trabajos_con_push
    for ruta_ in (CI, EVALUAR):
        assert 'git push' not in ruta_.read_text(encoding='utf-8').split('\njobs:\n')[1]


def test_el_pr_de_nueva_version_solo_lleva_la_ficha_y_el_historial(nueva):
    cuerpo = '\n'.join(c for n, _, c in scripts(nueva) if n == 'referencia')
    assert 'rama="referencia-agente/v${VERSION_NUEVA}-${GITHUB_RUN_ID}"' in cuerpo
    assert 'git add agentes/referencia-agente.json agentes/historial-agente.json' in cuerpo
    assert 'historial_agente.py" nueva' in cuerpo and '--anterior paquete/referencia-anterior.json' in cuerpo


def test_el_rollback_restaura_la_ficha_desde_el_historial_de_git(rollback):
    assert [p.get('name') for p in pasos(rollback['jobs']['rollback'])][2:] == [
        'Buscar la ficha de la versión a restaurar en el historial', 'Comprobar que la imagen existe en GHCR',
        'Demostración · mover el alias del prompt en un MLflow efímero', 'Rama nueva, ficha restaurada y pull request']
    assert pasos(rollback['jobs']['rollback'])[0]['with']['fetch-depth'] == 0
    cuerpo = todo_el_texto(rollback)
    assert 'git show "${COMMIT}:${FICHA}" > "$FICHA"' in cuerpo and 'referencia-agente/rollback-v${VERSION}-${GITHUB_RUN_ID}' in cuerpo
    assert cuerpo.index('cp "$FICHA" /tmp/ficha-retirada.json') < cuerpo.index('git show "${COMMIT}:${FICHA}"') < cuerpo.index('historial_agente.py" rollback')
    env = rollback['jobs']['rollback']['env']
    assert env['FICHA'] == '04-Proyecto-Base/agentes/referencia-agente.json' and env['HISTORIAL'] == '04-Proyecto-Base/agentes/historial-agente.json'
    demo = [p for p in pasos(rollback['jobs']['rollback']) if 'Demostración' in p.get('name', '')][0]
    assert demo['continue-on-error'] is True, 'la demostración del alias de MLflow no debe bloquear el rollback real'


def test_el_rollback_es_honesto_sobre_que_se_mueve_y_donde():
    texto = ROLLBACK.read_text(encoding='utf-8')
    for frase in ('QUÉ SE MUEVE Y DÓNDE', 'efímero', 'DEMOSTRACIÓN', 'NO un rollback', 'servidor', 'registro alias prompt --version N', '45278456252'):
        assert frase in texto, frase


# ------------------------------------------------------------------------------------------------ las órdenes existen
def _modulo(ruta_modulo):
    return (PROYECTO / ruta_modulo).read_text(encoding='utf-8')


def test_los_modulos_ordenes_y_opciones_que_llaman_existen():
    texto = '\n'.join(todo_el_texto(cargar(r)) for r in TODOS)
    modulos = set(re.findall(r'python -m (ia_mlops(?:\.\w+)+)', texto))
    assert {'ia_mlops.agente.evaluacion', 'ia_mlops.agente.registro', 'ia_mlops.pipeline', 'ia_mlops.operacional', 'ia_mlops.explotacion'} <= modulos
    for m in modulos:
        assert (PROYECTO / (m.replace('.', '/') + '.py')).exists(), f'no existe el módulo {m}'
    evaluacion, registro = _modulo('ia_mlops/agente/evaluacion.py'), _modulo('ia_mlops/agente/registro.py')
    for sub in set(re.findall(r'agente\.evaluacion (\w[\w-]*)', texto)):
        assert f"sub.add_parser('{sub}'" in evaluacion, f'evaluacion no tiene la orden «{sub}»'
    for sub in set(re.findall(r'agente\.registro (?:--uri \S+ )?(\w[\w-]*)', texto)):
        assert f"sub.add_parser('{sub}'" in registro or f"add_parser('{sub}'" in registro, f'registro no tiene la orden «{sub}»'
    for opcion in ('--llm', '--json', '--resultados', '--referencia', '--tolerancia', '--version'):
        assert f"'{opcion}'" in evaluacion, f'evaluacion no tiene la opción {opcion}'
    for opcion in ('--archivo', '--version'):
        assert f"'{opcion}'" in registro, f'registro no tiene la opción {opcion}'
    assert "choices=['falso', 'ollama']" in evaluacion
    assert "'prompt', 'agente'" in registro                       # `registro alias prompt --version N`
    assert "def estado" in registro and "def conectar" in registro and 'def huella_agente' in registro     # los usan los fragmentos de Python


def test_los_scripts_del_laboratorio_que_llaman_los_workflows_existen():
    for ruta in TODOS:
        wf = cargar(ruta)
        texto = todo_el_texto(wf)
        for script in set(re.findall(r'\$\{?LAB\}?/([\w.-]+\.py)', texto)):
            assert (LAB / script).exists(), f'{ruta.name} llama a {script}, que no está en el laboratorio'
        for archivo in set(re.findall(r'\$\{?LAB\}?/(prompts/[\w.-]+)', texto)):
            assert (LAB / archivo).exists(), f'{ruta.name}: falta {archivo}'
        if 'LAB' in (wf.get('env') or {}) or any('LAB' in (j.get('env') or {}) for j in wf['jobs'].values()):
            lab = (wf.get('env') or {}).get('LAB') or next(j['env']['LAB'] for j in wf['jobs'].values() if 'LAB' in (j.get('env') or {}))
            assert (RAIZ / lab).resolve() == LAB, f'{ruta.name}: LAB={lab} no es la carpeta de este laboratorio'


def test_los_archivos_del_proyecto_que_usan_existen():
    for ruta in ('requirements-dev.txt', 'requirements-agente.txt', 'agentes/referencia-agente.json', 'agentes/preguntas_oro.json',
                 'deploy/docker/compose-agente.yaml', 'deploy/docker/interfaz-agente.Dockerfile', 'tests/test_skills.py', 'tests/test_servidor_mcp.py',
                 'tests/test_panel_asistente.py', 'ia_mlops/agente/agente.py'):
        assert (PROYECTO / ruta).exists(), ruta
    assert glob.glob(str(PROYECTO / 'tests' / 'test_agente*.py')), 'el glob tests/test_agente*.py no encuentra nada'
    pruebas = todo_el_texto(cargar(CI))
    for patron in ('tests/test_agente*.py', 'tests/test_skills.py', 'tests/test_servidor_mcp.py', 'tests/test_panel_asistente.py'):
        assert patron in pruebas, patron
    assert re.search(r'mcp==\d+\.\d+\.\d+', _modulo('requirements-agente.txt')), 'mcp debe ir fijado con =='


def test_el_compose_tiene_el_perfil_ci_y_el_puerto_que_usan_los_workflows():
    compose = yaml.safe_load(_modulo('deploy/docker/compose-agente.yaml'))
    assert compose['services']['interfaz-ci']['profiles'] == ['ci']
    assert compose['x-interfaz']['ports'] == ['8090:8090']
    assert compose['x-interfaz']['image'] == 'retencion-interfaz-agente:local'
    assert compose['services']['interfaz-ci']['environment']['CURSO_LLM'] == 'falso'
    for wf in (cargar(CI), cargar(NUEVA)):
        cuerpo = todo_el_texto(wf)
        assert '-f "$COMPOSE" --profile ci' in cuerpo and 'compose-agente.yaml' in yaml.dump(wf)
        assert 'http://127.0.0.1:8090/asistente' in cuerpo and "'content-type: application/json'" in cuerpo
        assert re.search(r'down -v', cuerpo), 'el compose se apaga siempre'
    humo = [p for p in pasos(cargar(CI)['jobs']['humo']) if 'Apagar' in p.get('name', '')][0]
    assert humo['if'] == 'always()'
    ci_cuerpo = todo_el_texto(cargar(CI))
    assert 'up -d --build' in ci_cuerpo, 'el humo del CI construye con el compose (el pedido en la tarea)'


# ------------------------------------------------------------------------------------------------ escenarios de ensayo
def _en_el_path():
    sys.path.insert(0, str(PROYECTO))
    sys.path.insert(0, str(LAB))


_en_el_path()


def _proyecto():
    try:
        return (importlib.import_module('ia_mlops.agente.registro'), importlib.import_module('ia_mlops.agente.evaluacion'),
                importlib.import_module('ia_mlops.agente.skills'), importlib.import_module('ia_mlops.agente.agente'))
    except ImportError as e:      # faltan dependencias del proyecto en este entorno
        pytest.skip(f'no se puede importar ia_mlops.agente: {e}')


def test_escenario_igual_la_huella_del_codigo_actual_es_la_de_la_referencia():
    registro, evaluacion, skills, agente = _proyecto()
    ref = json.loads((PROYECTO / 'agentes' / 'referencia-agente.json').read_text(encoding='utf-8'))
    assert registro.huella_agente(agente.SISTEMA, ref['llm'], skills.cargar_skills()) == ref['huella_agente'], \
        'lab/agente-version/igual dejaría de dar «igual»: la referencia ya no corresponde al código (prompt, modelo o skills)'


def test_escenario_prompt_nuevo_cambia_la_huella(tmp_path):
    registro, evaluacion, skills, agente = _proyecto()
    aplicar = importlib.import_module('aplicar_prompt')
    ref = json.loads((PROYECTO / 'agentes' / 'referencia-agente.json').read_text(encoding='utf-8'))
    codigo = (PROYECTO / 'ia_mlops' / 'agente' / 'agente.py').read_text(encoding='utf-8')
    nuevo = aplicar.aplicar(codigo, (LAB / 'prompts' / 'sistema-v2.txt').read_text(encoding='utf-8'))
    sistema_nuevo = next(ast.literal_eval(n.value) for n in ast.parse(nuevo).body if isinstance(n, ast.Assign) and n.targets[0].id == 'SISTEMA')
    assert sistema_nuevo != agente.SISTEMA and 'VOLVER A COMPRAR' in sistema_nuevo
    assert registro.huella_agente(sistema_nuevo, ref['llm'], skills.cargar_skills()) != ref['huella_agente']


def test_escenario_rechazo_se_rechaza_aunque_todo_salga_perfecto():
    """Con tolerancia -0,10 se exige MEJORAR 0,10: «sin inventar» ya está en 0,96 y no puede subir tanto. Rechazada pase lo que pase en el LLM."""
    registro, evaluacion, skills, agente = _proyecto()
    ref = evaluacion.leer_referencia(PROYECTO / 'agentes' / 'referencia-agente.json')
    perfecto = {'metricas': {'acierto_herramienta': 1.0, 'sin_inventar': 1.0}, 'huella_preguntas': ref['huella_preguntas'],
                'huella_agente': 'otra-huella', 'criticas_falladas': []}
    assert evaluacion.comparar_con_referencia(perfecto, ref, -0.10).decision == 'rechazada'
    assert evaluacion.comparar_con_referencia(perfecto, ref).decision == 'aceptada'                   # con la tolerancia normal, perfecto pasa
    assert evaluacion.comparar_con_referencia({**perfecto, 'huella_agente': ref['huella_agente']}, ref, -0.10).decision == 'igual'   # y «igual» gana a la tolerancia


# ------------------------------------------------------------------------------------------------ scripts de apoyo
def test_aplicar_prompt_es_idempotente_y_deja_python_valido(tmp_path):
    aplicar = importlib.import_module('aplicar_prompt')
    copia = tmp_path / 'agente.py'
    shutil.copy(PROYECTO / 'ia_mlops' / 'agente' / 'agente.py', copia)
    original = copia.read_text(encoding='utf-8')
    assert aplicar.main(['--agente', str(copia)]) == 0
    una = copia.read_text(encoding='utf-8')
    assert una != original and 'USAR_SKILL' in una and "SISTEMA = '" in una
    ast.parse(una)
    assert aplicar.main(['--agente', str(copia)]) == 0
    assert copia.read_text(encoding='utf-8') == una
    assert una.replace(re.search(r"SISTEMA = .*\n", una).group(0), '') == original.replace(re.search(r"SISTEMA = \(.*?\)\n(?=USAR_SKILL)", original, re.S).group(0), ''), \
        'solo cambia la constante SISTEMA'


def test_aplicar_prompt_falla_con_un_archivo_que_no_es_agente_py(tmp_path):
    aplicar = importlib.import_module('aplicar_prompt')
    otro = tmp_path / 'otro.py'
    otro.write_text('x = 1\n', encoding='utf-8')
    assert aplicar.main(['--agente', str(otro)]) == 2


FICHA_1 = {'version': 1, 'huella_agente': 'h1', 'llm': 'm', 'metricas': {'acierto_herramienta': .8, 'sin_inventar': .96, 'respuestas_correctas': .76}, 'generado_en': 'x'}
FICHA_2 = {**FICHA_1, 'version': 2, 'huella_agente': 'h2'}


def _json(ruta, d):
    ruta.write_text(json.dumps(d), encoding='utf-8')
    return str(ruta)


def test_historial_nueva_version_y_rollback(tmp_path):
    h = importlib.import_module('historial_agente')
    historial, f1, f2 = str(tmp_path / 'historial.json'), _json(tmp_path / 'f1.json', FICHA_1), _json(tmp_path / 'f2.json', FICHA_2)
    assert h.main(['nueva', '--historial', historial, '--anterior', f1, '--nueva', f2, '--prompt', 'nuevo', '--ejecucion', 'https://x/runs/1']) == 0
    d = json.loads(Path(historial).read_text(encoding='utf-8'))
    assert [(e['version'], e['estado']) for e in d['versiones']] == [(1, 'anterior'), (2, 'produccion')]
    assert d['versiones'][1]['etiqueta_imagen'] == 'interfaz-agente:v2-h2' and d['versiones'][1]['prompt'] == 'nuevo'
    assert h.main(['prompt-de', '--historial', historial, '--version', '2']) == 0 and h.prompt_de(h.leer(historial), 2) == 'nuevo'
    assert h.prompt_de(h.leer(historial), 1) == 'actual' and h.prompt_de(h.leer(historial), 99) == 'actual'
    assert h.main(['rollback', '--historial', historial, '--restaurada', f1, '--retirada', f2]) == 0
    d = json.loads(Path(historial).read_text(encoding='utf-8'))
    assert [(e['version'], e['estado']) for e in d['versiones']] == [(1, 'produccion'), (2, 'retirada')]
    assert h.main(['nueva', '--historial', historial, '--anterior', f1, '--nueva', f2]) == 0     # volver a avanzar no duplica
    d = json.loads(Path(historial).read_text(encoding='utf-8'))
    assert [(e['version'], e['estado']) for e in d['versiones']] == [(1, 'anterior'), (2, 'produccion')]


def test_historial_parte_de_cero_y_rechaza_un_esquema_ajeno(tmp_path):
    h = importlib.import_module('historial_agente')
    historial = str(tmp_path / 'nuevo' if False else tmp_path / 'h.json')
    f1, f2 = _json(tmp_path / 'f1.json', FICHA_1), _json(tmp_path / 'f2.json', FICHA_2)
    assert h.main(['rollback', '--historial', historial, '--restaurada', f1, '--retirada', f2]) == 0     # sin historial previo: lo crea con las dos
    assert [(e['version'], e['estado']) for e in h.leer(historial)['versiones']] == [(1, 'produccion'), (2, 'retirada')]
    ajeno = _json(tmp_path / 'ajeno.json', {'esquema': 7, 'versiones': []})
    assert h.main(['prompt-de', '--historial', ajeno, '--version', '1']) == 2


def test_resumen_de_la_evaluacion(tmp_path, capsys):
    resumen = importlib.import_module('resumen_evaluacion')
    ref = json.loads((PROYECTO / 'agentes' / 'referencia-agente.json').read_text(encoding='utf-8'))
    informe = {**ref, 'metricas': {**ref['metricas'], 'acierto_herramienta': 0.88}}
    decision = {'decision': 'aceptada', 'motivo': 'dentro de la tolerancia', 'tolerancia': 0.1}
    md = resumen.markdown(informe, ref, decision)
    assert 'ACEPTADA' in md and '| acierto_herramienta | 88 % | 80 % | +8 puntos |' in md and '### Por categoría' in md
    for categoria in ref['por_categoria']:
        assert f'| {categoria} |' in md
    assert 'sin dato' not in md.split('### Por categoría')[0].split('latencia')[0]
    ruta_i, ruta_r, ruta_d = _json(tmp_path / 'i.json', informe), _json(tmp_path / 'r.json', ref), _json(tmp_path / 'd.json', decision)
    assert resumen.main(['--informe', ruta_i, '--referencia', ruta_r, '--decision', ruta_d]) == 0
    assert 'Evaluación del agente' in capsys.readouterr().out
    assert resumen.main(['--informe', str(tmp_path / 'no-existe.json')]) == 2
    assert 'Preguntas de seguridad falladas: s01' in resumen.markdown({**informe, 'criticas_falladas': ['s01']})


# ------------------------------------------------------------------------------------------------ sintaxis de los fragmentos
def _python_embebido(cuerpo):
    return [textwrap.dedent(m) for m in re.findall(r"python - <<'FIN'[^\n]*\n(.*?)\n\s*FIN\n", cuerpo + '\n', re.S)]


@pytest.mark.parametrize('ruta, minimo', [(CI, 1), (EVALUAR, 0), (NUEVA, 6), (ROLLBACK, 1)], ids=lambda x: getattr(x, 'name', ''))
def test_los_fragmentos_de_python_compilan(ruta, minimo):
    total = 0
    for nombre, paso, cuerpo in scripts(cargar(ruta)):
        for fragmento in _python_embebido(cuerpo):
            ast.parse(fragmento)
            total += 1
    assert total >= minimo


def _bash():
    if os.name == 'nt':      # en Windows solo vale el bash de Git (otros, como el de WSL o MKS, no son el de los runners)
        for c in (os.environ.get('CURSO_BASH'), r'C:\Program Files\Git\bin\bash.exe'):
            if c and Path(c).exists():
                return c
        return None          # sin bash de Git, la prueba se omite (se puede indicar con la variable CURSO_BASH)
    return shutil.which('bash')


@pytest.mark.parametrize('ruta', TODOS, ids=lambda r: r.name)
def test_los_pasos_de_bash_tienen_sintaxis_correcta(ruta, tmp_path):
    bash = _bash()
    if not bash:
        pytest.skip('no hay bash para comprobar la sintaxis')
    for nombre, paso, cuerpo in scripts(cargar(ruta)):
        sin_expresiones = re.sub(r'\$\{\{.*?\}\}', 'valor', cuerpo)
        archivo = tmp_path / 'paso.sh'
        archivo.write_text(sin_expresiones, encoding='utf-8', newline='\n')
        r = subprocess.run([bash, '-n', str(archivo)], capture_output=True, text=True)
        assert r.returncode == 0, f'{nombre}/{paso}: {r.stderr}'


# ------------------------------------------------------------------------------------------------ texto para el alumnado
def test_las_cabeceras_explican_en_castellano_y_son_honestas():
    for ruta in TODOS:
        cabecera = ruta.read_text(encoding='utf-8').split('\non:\n')[0]
        # Honestas = citan el run REAL de Actions donde se ejecutaron (22-23/11/2026), ya no «sin verificar».
        assert re.search(r'run \d{11}\b', cabecera) and 'ejecutado' in cabecera.lower(), \
            f'{ruta.name}: la cabecera debe citar el run real en el que se ejecutó'
        assert 'aún no se ha ejecutado' not in cabecera, f'{ruta.name}: la cabecera dice que no se ha ejecutado, y sí se ejecutó'
        assert f'.github/workflows/{ruta.name}' in cabecera, f'{ruta.name}: debe decir dónde se copia'
    cabecera = NUEVA.read_text(encoding='utf-8').split('\non:\n')[0]
    for palabra in ('igual', 'rechazada', 'aceptada', 'ROLLBACK', 'produccion', 'GHCR', 'CONFIGURAR-REPOSITORIO.md', 'ATAJO DIDÁCTICO', 'huella del agente'):
        assert palabra in cabecera, palabra


def test_configurar_repositorio_remite_al_de_s4():
    texto = (LAB / 'CONFIGURAR-REPOSITORIO.md').read_text(encoding='utf-8')
    assert 'S4-Orquestacion-y-CI-CD/laboratorio-produccion-e2e/CONFIGURAR-REPOSITORIO.md' in texto
    for palabra in ('produccion', 'pull requests', 'agente-ci.yml', 'agente-evaluar.yml', 'agente-nueva-version.yml', 'agente-rollback.yml'):
        assert palabra in texto, palabra
    assert (RAIZ / '01-Sesiones' / 'S4-Orquestacion-y-CI-CD' / 'laboratorio-produccion-e2e' / 'CONFIGURAR-REPOSITORIO.md').exists()


def test_no_se_crea_nada_en_github():
    assert not (LAB / '.github').exists() and not list(LAB.rglob('.github'))
