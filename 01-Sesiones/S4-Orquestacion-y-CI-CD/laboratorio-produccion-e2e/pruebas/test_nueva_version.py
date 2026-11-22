"""Pruebas estáticas de nueva-version.yml y rollback.yml (no ejecutan GitHub Actions: leen los archivos y comprueban lo que se promete).

Cómo se ejecutan (desde cualquier carpeta, con el entorno del curso):
    python -m pytest 01-Sesiones/S4-Orquestacion-y-CI-CD/laboratorio-produccion-e2e/pruebas -q

Qué comprueban, y por qué importa:
    * el YAML es válido (PyYAML lee la clave `on` como True: ojo al leerla);
    * solo se dispara a mano, y solo el trabajo «publicar» usa el environment «produccion» (la aprobación);
    * los permisos son los mínimos de cada trabajo: «packages: write» solo en publicar, «contents: write» solo donde se abre el PR;
    * los trabajos se encadenan con `needs:` y los artefactos que se descargan los sube un trabajo anterior;
    * ningún paso empuja a develop ni a main, y el único token es el GITHUB_TOKEN;
    * las órdenes de `ia_mlops` que llaman los workflows existen de verdad;
    * los fragmentos de Python y de bash de los pasos no tienen errores de sintaxis.
"""
import ast
import os
import re
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest
import yaml

LAB = Path(__file__).resolve().parents[1]
PROYECTO = LAB.parents[2] / '04-Proyecto-Base'
NUEVA, ROLLBACK = LAB / 'nueva-version.yml', LAB / 'rollback.yml'


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


@pytest.fixture(scope='module')
def nueva():
    return cargar(NUEVA)


@pytest.fixture(scope='module')
def rollback():
    return cargar(ROLLBACK)


# ------------------------------------------------------------------------------------------------ YAML y disparadores
def test_los_archivos_existen_y_son_yaml_validos(nueva, rollback):
    assert isinstance(nueva, dict) and isinstance(rollback, dict)
    assert nueva['name'] and rollback['name']
    assert True in nueva and 'on' not in nueva       # PyYAML lee `on:` como True (YAML 1.1): hay que saberlo para leer los disparadores


def test_los_trabajos_sin_checkout_no_heredan_la_carpeta_del_proyecto(nueva, rollback):
    # Si el workflow fija defaults.run.working-directory y un trabajo no descarga el repositorio, esa carpeta no existe
    # en su máquina y el primer «run» falla (pasó en el ensayo del 22/11/2026 con «publicar»).
    for wf in (nueva, rollback):
        carpeta = ((wf.get('defaults') or {}).get('run') or {}).get('working-directory')
        if not carpeta or carpeta == '.':
            continue
        for nombre, job in wf['jobs'].items():
            usa_checkout = any(str(p.get('uses', '')).startswith('actions/checkout') for p in job.get('steps', []))
            tiene_run = any('run' in p for p in job.get('steps', []))
            if tiene_run and not usa_checkout:
                propia = ((job.get('defaults') or {}).get('run') or {}).get('working-directory')
                assert propia is not None, f'{nombre}: no descarga el repositorio pero hereda working-directory={carpeta}'


def test_solo_se_dispara_a_mano(nueva, rollback):
    dr = disparadores(rollback)   # a mano; y SOLO para ensayarlo, push a ramas lab/rollback/**
    assert 'workflow_dispatch' in dr and set(dr) <= {'workflow_dispatch', 'push'}
    if 'push' in dr:
        assert all(r.startswith('lab/rollback/') for r in dr['push'].get('branches') or ['x']), 'el rollback solo se ensaya desde ramas lab/rollback/'
    # La versión nueva se lanza a mano; además, SOLO para ensayarla sin la rama principal, con un push a ramas lab/nueva-version/**.
    d = disparadores(nueva)
    assert set(d) <= {'workflow_dispatch', 'push'} and 'workflow_dispatch' in d
    if 'push' in d:
        ramas = d['push'].get('branches') or []
        assert ramas and all(r.startswith('lab/nueva-version/') for r in ramas), 'el push solo puede venir de ramas de ensayo'
        assert not set(d['push']) & {'branches-ignore', 'tags'}, 'nada de ramas sin filtro ni etiquetas'


def test_entradas_de_nueva_version(nueva):
    entradas = disparadores(nueva)['workflow_dispatch']['inputs']
    assert set(entradas) == {'fuente', 'tolerancia'}
    assert entradas['fuente']['type'] == 'choice' and entradas['fuente']['options'] == ['muestra', 'completo']
    assert entradas['fuente']['default'] == 'muestra'
    assert entradas['tolerancia'].get('required') is False and entradas['tolerancia']['default'] == ''


def test_las_fuentes_del_workflow_son_las_de_config(nueva):
    config = (PROYECTO / 'ia_mlops' / 'config.py').read_text(encoding='utf-8')
    fuentes = re.search(r'FUENTES = \{(.*?)\n\}', config, re.S).group(1)
    assert sorted(re.findall(r"'(\w+)':", fuentes)) == sorted(disparadores(nueva)['workflow_dispatch']['inputs']['fuente']['options'])


def test_la_clave_de_la_cache_es_el_principio_del_sha256_de_config(nueva):
    config = (PROYECTO / 'ia_mlops' / 'config.py').read_text(encoding='utf-8')
    sha = re.search(r"SHA256_ZIP_UCI = '([0-9a-f]{64})'", config).group(1)
    claves = {p['with']['key'] for j in nueva['jobs'].values() for p in pasos(j) if str(p.get('uses', '')).startswith('actions/cache')}
    assert claves == {f'uci-online-retail-ii-{sha[:12]}'}


def test_todo_trabajo_tiene_limite_de_tiempo_y_las_acciones_fijadas(nueva, rollback):
    permitidas = {'actions/checkout@v4', 'actions/setup-python@v5', 'actions/cache@v4', 'actions/upload-artifact@v4',
                  'actions/download-artifact@v4'}
    for wf in (nueva, rollback):
        for nombre, job in wf['jobs'].items():
            assert isinstance(job.get('timeout-minutes'), int), f'{nombre}: sin timeout-minutes'
            for p in pasos(job):
                if 'uses' in p:
                    assert p['uses'] in permitidas, f'{nombre}: acción no revisada {p["uses"]}'


# ------------------------------------------------------------------------------------------------ grafo de trabajos
def test_cadena_de_trabajos(nueva):
    jobs = nueva['jobs']
    assert list(jobs) == ['entrenar', 'construir-y-probar', 'publicar', 'referencia']
    assert 'needs' not in jobs['entrenar']
    assert jobs['construir-y-probar']['needs'] == 'entrenar'
    assert set(jobs['publicar']['needs']) == {'entrenar', 'construir-y-probar'}
    assert set(jobs['referencia']['needs']) == {'entrenar', 'construir-y-probar', 'publicar'}


def test_igual_y_rechazada_no_llegan_a_construir(nueva):
    """«igual» omite los trabajos siguientes (condición en el primero que los cuelga) y «rechazada» pone en rojo el primero."""
    assert nueva['jobs']['construir-y-probar']['if'] == "needs.entrenar.outputs.decision == 'aceptada'"
    # publicar y referencia dependen de construir-y-probar: si ese se omite, también se omiten (GitHub omite lo que depende de un omitido)
    salidas = nueva['jobs']['entrenar']['outputs']
    assert {'decision', 'version_referencia', 'version_nueva', 'huella', 'etiqueta', 'fuente_referencia'} <= set(salidas)
    rechazo = [p for p in pasos(nueva['jobs']['entrenar']) if 'rechaz' in p.get('name', '').lower() and 'run' in p]
    assert len(rechazo) == 1 and 'exit 1' in rechazo[0]['run'] and "decision == 'rechazada'" in rechazo[0]['if']
    cuerpo = '\n'.join(s for _, _, s in scripts(nueva))
    assert 'decision=igual' not in cuerpo and "'igual': 'IGUAL" in cuerpo   # «igual» no falla: se explica en el resumen
    assert 'GITHUB_STEP_SUMMARY' in cuerpo


def test_los_pasos_que_usan_una_salida_la_tienen_definida(nueva):
    for nombre, job in nueva['jobs'].items():
        for p in pasos(job):
            for ref in re.findall(r'needs\.(\w[\w-]*)\.outputs\.(\w+)', yaml.dump(p)):
                assert ref[0] in job.get('needs', []) or ref[0] == job.get('needs'), f'{nombre} usa needs.{ref[0]} sin declararlo'
                assert ref[1] in nueva['jobs'][ref[0]]['outputs'], f'{nombre} usa la salida {ref[1]} que {ref[0]} no declara'
    for nombre, job in nueva['jobs'].items():
        for salida, valor in job.get('outputs', {}).items():
            paso = re.search(r'steps\.(\w+)\.outputs\.(\w+)', valor)
            assert paso and any(p.get('id') == paso.group(1) for p in pasos(job)), f'{nombre}: la salida {salida} no sale de un paso con id'


# ------------------------------------------------------------------------------------------------ environment y permisos
def test_el_environment_produccion_solo_esta_en_publicar(nueva, rollback):
    con_environment = {n: j['environment'] for n, j in nueva['jobs'].items() if 'environment' in j}
    assert list(con_environment) == ['publicar']
    entorno = con_environment['publicar']
    assert (entorno['name'] if isinstance(entorno, dict) else entorno) == 'produccion'
    assert not any('environment' in j for j in rollback['jobs'].values()), 'el rollback se aprueba al revisar el PR, no con el environment'


def test_permisos_minimos_por_trabajo(nueva):
    assert nueva['permissions'] == {'contents': 'read'}
    esperados = {
        'entrenar': {'contents': 'read'},
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


def test_permisos_del_rollback(rollback):
    assert rollback['permissions'] == {'contents': 'read'}
    assert rollback['jobs']['rollback']['permissions'] == {'contents': 'write', 'pull-requests': 'write', 'packages': 'read'}


def test_solo_hay_el_github_token_y_ningun_secreto_propio(nueva, rollback):
    for ruta in (NUEVA, ROLLBACK):
        texto = ruta.read_text(encoding='utf-8')
        assert set(re.findall(r'secrets\.(\w+)', texto)) == {'GITHUB_TOKEN'}
        assert 'id-token' not in texto
        assert not re.search(r'\b[A-Z]:\\|/home/|/Users/', texto), 'rutas personales'


def test_solo_publicar_hace_login_y_push_en_ghcr(nueva):
    for nombre, paso, cuerpo in scripts(nueva):
        if 'docker push' in cuerpo or 'docker login' in cuerpo:
            assert nombre == 'publicar', f'{nombre}/{paso}: solo «publicar» inicia sesión en GHCR y sube la imagen'
    publicar = '\n'.join(c for n, _, c in scripts(nueva) if n == 'publicar')
    assert 'docker push "$destino"' in publicar and 'ghcr.io/${propietario}/retencion-api:${ETIQUETA}' in publicar
    assert "tr '[:upper:]' '[:lower:]'" in publicar          # GHCR exige minúsculas
    # la etiqueta viene ya formada de «entrenar» (v<N+1>-<huella>)
    etiqueta = nueva['jobs']['entrenar']['outputs']['etiqueta']
    assert etiqueta.endswith('steps.comparar.outputs.etiqueta }}')
    assert 'etiqueta=v{nueva}-{d[' in '\n'.join(c for n, _, c in scripts(nueva) if n == 'entrenar')


# ------------------------------------------------------------------------------------------------ artefactos
def _artefactos(wf):
    subidos, bajados = {}, {}
    for nombre, job in wf['jobs'].items():
        for p in pasos(job):
            usa = str(p.get('uses', ''))
            if usa.startswith('actions/upload-artifact'):
                subidos.setdefault(p['with']['name'], []).append((nombre, p['with']['path']))
            if usa.startswith('actions/download-artifact'):
                bajados.setdefault(p['with']['name'], []).append((nombre, p['with']['path']))
    return subidos, bajados


def _antecesores(wf, nombre):
    needs = wf['jobs'][nombre].get('needs', [])
    needs = [needs] if isinstance(needs, str) else needs
    resultado = set(needs)
    for n in needs:
        resultado |= _antecesores(wf, n)
    return resultado


def test_artefactos_coherentes(nueva):
    subidos, bajados = _artefactos(nueva)
    assert set(subidos) == {'candidata', 'comparacion', 'imagen'}
    assert set(bajados) == set(subidos), 'todo lo que se sube se baja, y al revés'
    for nombre, usos in bajados.items():
        for job, _ in usos:
            assert {j for j, _ in subidos[nombre]} <= _antecesores(nueva, job), f'{job} baja «{nombre}» sin depender del trabajo que lo sube'
    # los tres se suben desde una sola carpeta (estructura estable), y la misma carpeta se baja donde se necesita
    assert subidos['candidata'] == [('entrenar', '04-Proyecto-Base/paquete')]
    assert all(ruta == '04-Proyecto-Base/paquete' for _, ruta in bajados['candidata'])
    assert subidos['comparacion'] == [('construir-y-probar', '04-Proyecto-Base/comparacion')]
    assert bajados['comparacion'] == [('referencia', '04-Proyecto-Base/comparacion')]
    assert [j for j, _ in subidos['imagen']] == ['construir-y-probar'] and [j for j, _ in bajados['imagen']] == ['publicar']
    for pasos_, nombre in ((nueva['jobs']['entrenar'], 'candidata'), (nueva['jobs']['construir-y-probar'], 'imagen')):
        retencion = [p['with']['retention-days'] for p in pasos(pasos_) if str(p.get('uses', '')).startswith('actions/upload-artifact') and p['with']['name'] == nombre]
        assert retencion and retencion[0] <= 7


def test_el_paquete_de_la_candidata_lleva_lo_que_usan_los_trabajos_siguientes(nueva):
    empaquetar = '\n'.join(c for n, p, c in scripts(nueva) if n == 'entrenar' and 'Empaquetar' in p)
    for archivo in ('modelo_mlflow', 'modelo.joblib', 'metadatos.json', 'metricas.json', 'decision.json', 'paquete/test.csv'):
        assert archivo in empaquetar, archivo
    construir = '\n'.join(c for n, _, c in scripts(nueva) if n == 'construir-y-probar')
    assert 'paquete/test.csv' in construir and 'paquete/decision.json' in construir and 'cp -r paquete/models/. models/' in construir
    referencia = '\n'.join(c for n, _, c in scripts(nueva) if n == 'referencia')
    assert 'paquete/models' in referencia and 'paquete/reports' in referencia and 'paquete/decision.json' in referencia


# ------------------------------------------------------------------------------------------------ nada de push a develop/main
def _pushes(texto):
    return re.findall(r'^\s*git push[^\n]*', texto, re.M)


@pytest.mark.parametrize('ruta, trabajos_con_push', [(NUEVA, {'referencia'}), (ROLLBACK, {'rollback'})])
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
            # la rama siempre es nueva y hay una guarda explícita contra las ramas protegidas
            assert re.search(r'rama="referencia/', cuerpo) and re.search(r'case "\$rama" in main\|develop\|master\)', cuerpo)
            assert 'git checkout -b "$rama"' in cuerpo and 'gh pr create' in cuerpo and '--base "$BASE"' in cuerpo
    assert con_push == trabajos_con_push
    assert re.search(r'git push', ruta.read_text(encoding='utf-8'))


def test_la_rama_del_pr_lleva_la_version_nueva(nueva):
    cuerpo = '\n'.join(c for n, _, c in scripts(nueva) if n == 'referencia')
    assert 'rama="referencia/v${VERSION_NUEVA}-${GITHUB_RUN_ID}"' in cuerpo
    assert 'git add models/referencia.json models/historial_versiones.json' in cuerpo   # solo la ficha y su historial: nada más entra
    assert cuerpo.count('git add') == 1


def test_el_historial_se_actualiza_en_el_mismo_pr_que_la_referencia(nueva, rollback):
    cuerpo = '\n'.join(c for n, _, c in scripts(nueva) if n == 'referencia')
    assert 'cp models/referencia.json /tmp/ficha-anterior.json' in cuerpo           # antes de que `crear` la sobrescriba
    assert cuerpo.index('cp models/referencia.json') < cuerpo.index('produccion crear') < cuerpo.index('produccion historial')
    assert 'produccion historial --retira /tmp/ficha-anterior.json --estado-retirada anterior' in cuerpo
    cuerpo = '\n'.join(c for _, _, c in scripts(rollback))
    assert cuerpo.index('cp "$FICHA" /tmp/ficha-retirada.json') < cuerpo.index('git show "${COMMIT}:${FICHA}"') < cuerpo.index('produccion historial')
    assert 'produccion historial --retira /tmp/ficha-retirada.json --estado-retirada retirada' in cuerpo
    assert 'git add "$FICHA" "$HISTORIAL"' in cuerpo and cuerpo.count('git add') == 1
    assert rollback['jobs']['rollback']['env']['HISTORIAL'] == '04-Proyecto-Base/models/historial_versiones.json'


# ------------------------------------------------------------------------------------------------ las órdenes existen
def test_las_ordenes_de_ia_mlops_existen(nueva):
    texto = '\n'.join(c for _, _, c in scripts(nueva))
    produccion = (PROYECTO / 'ia_mlops' / 'produccion.py').read_text(encoding='utf-8')
    texto += '\n' + '\n'.join(c for _, _, c in scripts(cargar(ROLLBACK)))
    for sub in set(re.findall(r'ia_mlops\.produccion (\w[\w-]*)', texto)):
        assert f"sub.add_parser('{sub}'" in produccion, f'produccion no tiene la orden «{sub}»'
    for opcion in set(re.findall(r'(?:comparar|crear|comparar-tramos|exportar-test|historial)[^\n|]*?(--[\w-]+)', texto)):
        assert f"'{opcion}'" in produccion, f'produccion no tiene la opción {opcion}'
    pipeline = (PROYECTO / 'ia_mlops' / 'pipeline.py').read_text(encoding='utf-8')
    assert "'--fuente'" in pipeline and "'--sin-mlflow'" in pipeline
    assert "sub.add_parser('descargar')" in (PROYECTO / 'ia_mlops' / 'dataset.py').read_text(encoding='utf-8')
    for ruta in ('deploy/docker/Dockerfile', 'tests/datos/cliente_ejemplo.json', 'requirements-dev.txt'):
        assert (PROYECTO / ruta).exists(), ruta


def test_la_etiqueta_de_la_imagen_coincide_con_produccion_py(nueva):
    """La etiqueta que publica el workflow es v<N+1>-<huella>; la ficha dice retencion-api:v<N+1>-<huella> y se comprueba al crearla."""
    texto = '\n'.join(c for n, _, c in scripts(nueva) if n == 'referencia')
    assert "'retencion-api:' + os.environ['ETIQUETA']" in texto
    produccion = (PROYECTO / 'ia_mlops' / 'produccion.py').read_text(encoding='utf-8')
    assert "PREFIJO_IMAGEN = 'retencion-api'" in produccion


# ------------------------------------------------------------------------------------------------ sintaxis de los fragmentos
def _python_embebido(cuerpo):
    return [textwrap.dedent(m) for m in re.findall(r"python - <<'FIN'[^\n]*\n(.*?)\n\s*FIN\n", cuerpo + '\n', re.S)]


@pytest.mark.parametrize('ruta, minimo', [(NUEVA, 5), (ROLLBACK, 1)], ids=['nueva-version.yml', 'rollback.yml'])
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


@pytest.mark.parametrize('ruta', [NUEVA, ROLLBACK], ids=lambda r: r.name)
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


# ------------------------------------------------------------------------------------------------ rollback
def test_rollback_restaura_la_ficha_desde_el_historial(rollback):
    assert [p.get('name') for p in pasos(rollback['jobs']['rollback'])][1:] == [
        None, 'Buscar la ficha de la versión a restaurar en el historial', 'Comprobar que la imagen existe en GHCR',
        'Rama nueva, ficha restaurada y pull request']
    checkout = pasos(rollback['jobs']['rollback'])[0]
    assert checkout['with']['fetch-depth'] == 0
    cuerpo = '\n'.join(c for _, _, c in scripts(rollback))
    assert 'git show "${COMMIT}:${FICHA}" > "$FICHA"' in cuerpo
    assert 'referencia/rollback-v${VERSION}-${GITHUB_RUN_ID}' in cuerpo
    entradas = disparadores(rollback)['workflow_dispatch']['inputs']
    assert set(entradas) == {'version', 'comprobar_imagen'} and entradas['comprobar_imagen']['default'] is True


# ------------------------------------------------------------------------------------------------ texto para el alumnado
def test_la_cabecera_explica_en_castellano_decisiones_rollback_y_configuracion():
    texto = NUEVA.read_text(encoding='utf-8')
    cabecera = texto.split('\non:\n')[0]
    for palabra in ('igual', 'rechazada', 'aceptada', 'ROLLBACK', 'produccion', 'GHCR', 'CONFIGURAR-REPOSITORIO.md', 'CÓMO SE COMPARA CAMPEÓN Y CANDIDATA'):
        assert palabra in cabecera, palabra
    assert 'workflows/nueva-version.yml' in cabecera and 'workflows/rollback.yml' in ROLLBACK.read_text(encoding='utf-8')


def test_no_se_crea_nada_en_github():
    """Los workflows de este laboratorio se copian a .github/workflows/ cada alumno; aquí no se crea nada en .github."""
    assert not (LAB / '.github').exists()
    assert not list(LAB.rglob('.github'))
