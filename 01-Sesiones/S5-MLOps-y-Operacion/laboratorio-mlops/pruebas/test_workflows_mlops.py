"""Pruebas del workflow de monitoreo (no ejecutan GitHub Actions: leen el archivo, comprueban lo que se promete y ejecutan lo que SÍ se puede).

Cómo se ejecutan (desde la carpeta del laboratorio, con el entorno del curso):
    python -m pytest -q pruebas -p no:cacheprovider

Qué comprueban (imitan las de test_workflows_agente.py y las de S4):
    * el YAML es válido (PyYAML lee la clave `on` como True: ojo al leerla);
    * disparadores (schedule en un minuto no redondo, workflow_dispatch con sus tres entradas, push a lab/monitoreo/**) y ramas de ensayo;
    * permisos mínimos: contents: read en todo y `issues: write` SOLO en el trabajo de alerta; sin secretos propios;
    * `working-directory: .` en el trabajo sin checkout; concurrency propio; tiempos límite y acciones fijadas;
    * los comandos `python -m ia_mlops.deriva …` llaman a subcomandos y opciones que existen de verdad en 04-Proyecto-Base;
    * `bash -n` de cada bloque `run` (si hay el bash de Git) y compilación de los fragmentos de Python;
    * ESCENARIOS SOBRE LOS DATOS REALES: se prepara una copia del proyecto en una carpeta temporal (operacional + pipeline, como el
      primer trabajo del workflow, unos 40 s) y se comprueba que `estable` da salida 0 y `deriva` da salida 1, con las variables que
      cuenta la guía; y que el resumen y el cuerpo del issue (los scripts de Python del propio workflow) se generan bien con esos JSON.
      Para saltarse esa parte: variable de entorno CURSO_SIN_ESCENARIOS=1.
    * la lógica de la alerta (etiqueta, no duplicar issue) está escrita como se promete.
"""
import ast
import fnmatch
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
YML = LAB / 'monitoreo.yml'


def cargar():
    return yaml.safe_load(YML.read_text(encoding='utf-8'))


def disparadores(wf):
    """PyYAML (YAML 1.1) lee `on` como el booleano True: se busca de las dos maneras."""
    return wf.get('on', wf.get(True))


def pasos(job):
    return job.get('steps', [])


def scripts(wf):
    for nombre, job in wf['jobs'].items():
        for i, paso in enumerate(pasos(job)):
            if 'run' in paso:
                yield nombre, paso.get('name', f'paso {i}'), paso['run']


def paso_con(wf, trabajo, fragmento):
    for p in pasos(wf['jobs'][trabajo]):
        if fragmento in p.get('name', ''):
            return p
    raise AssertionError(f'no hay un paso con «{fragmento}» en {trabajo}')


@pytest.fixture(scope='module')
def wf():
    return cargar()


# ------------------------------------------------------------------------------------------------ YAML y disparadores
def test_el_archivo_es_yaml_valido(wf):
    assert isinstance(wf, dict) and wf['name'] == 'Monitoreo del modelo' and wf['jobs']
    assert True in wf and 'on' not in wf                       # PyYAML lee `on:` como True (YAML 1.1)
    assert list(wf['jobs']) == ['datos', 'deriva', 'alerta']


def test_disparadores(wf):
    d = disparadores(wf)
    assert set(d) == {'schedule', 'workflow_dispatch', 'push'}
    assert d['push']['branches'] == ['lab/monitoreo/**']
    assert not set(d['push']) & {'branches-ignore', 'tags', 'paths'}


def test_schedule_diario_en_un_minuto_no_redondo(wf):
    cron = disparadores(wf)['schedule'][0]['cron']
    minuto, hora, resto = cron.split(None, 2)
    assert resto == '* * *', 'diario'
    assert minuto.isdigit() and minuto not in ('0', '00', '30'), 'a las horas en punto GitHub va cargado'
    assert cron == '23 5 * * *'


def test_las_entradas_a_mano(wf):
    entradas = disparadores(wf)['workflow_dispatch']['inputs']
    assert set(entradas) == {'referencia', 'actual', 'umbral_psi'}
    assert entradas['referencia']['default'] == '2010-12-01' and entradas['actual']['default'] == '' and entradas['umbral_psi']['default'] == '0.25'


def test_la_rama_base_no_dispara_y_las_dos_de_ensayo_si(wf):
    patrones = disparadores(wf)['push']['branches']

    def dispara(rama):
        return any(fnmatch.fnmatch(rama, p.replace('**', '*')) for p in patrones)
    assert dispara('lab/monitoreo/estable') and dispara('lab/monitoreo/deriva')
    assert not dispara('lab/mlops-s5') and not dispara('develop') and not dispara('lab/agente/ci') and not dispara('lab/agente-version/igual')


def test_la_cabecera_documenta_las_ramas_y_las_ramas_son_las_del_case(wf):
    texto = YML.read_text(encoding='utf-8')
    cabecera = texto.split('\nname:')[0]
    documentadas = set(re.findall(r'lab/monitoreo/([\w-]+)', cabecera))
    assert documentadas == {'estable', 'deriva'}
    paso = paso_con(wf, 'deriva', 'Elegir el escenario')
    en_case = set(re.findall(r'^\s*lab/monitoreo/([\w-]+)\)', paso['run'], re.M))
    assert en_case == {'estable', 'deriva'}
    for palabra in ('schedule', 'FORK', 'DESACTIVADOS', 'issue', 'ROJO', 'alerta-deriva', 'workflow_dispatch', '.github/workflows/monitoreo.yml',
                    'Disable workflow'):
        assert palabra in cabecera, palabra


# ------------------------------------------------------------------------------------------------ permisos y seguridad
def test_permisos_minimos_y_issues_write_solo_en_la_alerta(wf):
    assert wf['permissions'] == {'contents': 'read'}
    for nombre in ('datos', 'deriva'):
        assert 'permissions' not in wf['jobs'][nombre], f'{nombre}: hereda contents: read'
    assert wf['jobs']['alerta']['permissions'] == {'issues': 'write'}
    escriben = [n for n, j in wf['jobs'].items() if 'write' in (j.get('permissions') or {}).values()]
    assert escriben == ['alerta']
    assert 'write-all' not in YML.read_text(encoding='utf-8')


def test_sin_secretos_propios_ni_rutas_personales():
    texto = YML.read_text(encoding='utf-8')
    assert set(re.findall(r'secrets\.(\w+)', texto)) == set()
    assert 'id-token' not in texto
    assert 'github.token' in texto                         # el único «secreto»: el token del propio run
    assert not re.search(r'\b[A-Z]:\\|/home/(?!runner)|/Users/', texto)


def test_el_trabajo_sin_checkout_pone_working_directory_punto(wf):
    carpeta = wf['defaults']['run']['working-directory']
    assert carpeta == '04-Proyecto-Base'
    for nombre, job in wf['jobs'].items():
        usa_checkout = any(str(p.get('uses', '')).startswith('actions/checkout') for p in pasos(job))
        if not usa_checkout:
            assert nombre == 'alerta'
            assert job['defaults']['run']['working-directory'] == '.', 'sin checkout no existe 04-Proyecto-Base (lección real de S4)'
        else:
            assert 'defaults' not in job
    assert 'actions/checkout' not in json.dumps(wf['jobs']['alerta'])


def test_concurrency_propio_y_tiempos_limite_y_acciones_fijadas(wf):
    assert wf['concurrency'] == {'group': 'monitoreo', 'cancel-in-progress': False}
    for nombre, job in wf['jobs'].items():
        assert isinstance(job.get('timeout-minutes'), int) and job['timeout-minutes'] <= 20, nombre
        for p in pasos(job):
            if 'uses' in p:
                assert re.fullmatch(r'actions/[\w-]+@v\d+', p['uses']), p['uses']


def test_cadena_de_trabajos_y_condicion_de_la_alerta(wf):
    assert wf['jobs']['deriva']['needs'] == 'datos' and wf['jobs']['alerta']['needs'] == 'deriva'
    assert wf['jobs']['alerta']['if'] == "needs.deriva.outputs.alerta == 'true'"
    assert wf['jobs']['deriva']['outputs']['alerta'] == '${{ steps.medir.outputs.alerta }}'


def test_la_alerta_termina_en_rojo_y_es_lo_ultimo(wf):
    ultimo = pasos(wf['jobs']['alerta'])[-1]
    assert 'ROJO' in ultimo['name'] and ultimo['run'].rstrip().endswith('exit 1')
    assert 'if' not in ultimo, 'el rojo se da solo si los pasos anteriores (issue) han ido bien'


def test_no_abre_un_segundo_issue_y_crea_la_etiqueta_si_falta(wf):
    texto = '\n'.join(c for n, _, c in scripts(wf) if n == 'alerta')
    assert 'gh issue list --label alerta-deriva --state open' in texto
    assert 'gh label create alerta-deriva' in texto and 'gh label list' in texto
    assert 'gh issue comment' in texto and 'gh issue create' in texto and '--label alerta-deriva' in texto
    # primero se busca (list), después se decide: el create va en la rama «else»
    assert texto.index('gh issue list') < texto.index('gh issue comment') < texto.index('gh issue create')
    assert re.search(r'if \[ -n "\$ABIERTA" \]; then.*gh issue comment.*else.*gh issue create.*fi', texto, re.S)
    env = wf['jobs']['alerta']['env']
    assert env['GH_TOKEN'] == '${{ github.token }}' and env['GH_REPO'] == '${{ github.repository }}'     # sin checkout, gh necesita GH_REPO
    assert 'github.run_id' in env['URL_RUN']


# ------------------------------------------------------------------------------------------------ órdenes y opciones
def _modulo(ruta):
    return (PROYECTO / ruta).read_text(encoding='utf-8')


def test_los_comandos_de_deriva_usan_subcomandos_y_opciones_que_existen(wf):
    texto = '\n'.join(c for _, _, c in scripts(wf)).replace('\\\n', ' ')
    modulos = set(re.findall(r'python -m (ia_mlops(?:\.\w+)+)', texto))
    # alias_modelo solo aparece en el TEXTO del issue (qué hacer: promover una versión nueva): ha de existir esa orden y esa opción
    assert modulos == {'ia_mlops.deriva', 'ia_mlops.operacional', 'ia_mlops.pipeline', 'ia_mlops.alias_modelo'}
    alias = _modulo('ia_mlops/alias_modelo.py')
    assert re.search(r'python -m ia_mlops\.alias_modelo promover --version N', texto) and "add_parser('promover'" in alias and "'--version'" in alias
    for m in modulos:
        assert (PROYECTO / (m.replace('.', '/') + '.py')).exists(), m
    deriva = _modulo('ia_mlops/deriva.py')
    llamadas = re.findall(r'python -m ia_mlops\.deriva (\w+)([^\n|]*)', texto)
    assert {s for s, _ in llamadas} == {'cortes', 'datos', 'rendimiento'}
    for sub, resto in llamadas:
        assert f"sub.add_parser('{sub}'" in deriva, sub
        for opcion in re.findall(r'(--[\w-]+)', resto):
            assert f"'{opcion}'" in deriva, f'deriva {sub}: la opción {opcion} no existe'
    # opciones obligatorias presentes en cada llamada
    for sub, resto in llamadas:
        if sub == 'datos':
            assert '--referencia' in resto and '--actual' in resto and '--umbral-psi' in resto and '--json' in resto
        if sub == 'rendimiento':
            assert '--cortes' in resto and '--json' in resto
    assert 'sys.exit(main())' in deriva or 'sys.exit(main(' in deriva
    assert 'return 1 if hay else 0' in deriva and 'return 2' in deriva         # 0 sin deriva, 1 deriva, 2 error


def test_las_claves_json_que_lee_el_workflow_existen_en_deriva(wf):
    deriva = _modulo('ia_mlops/deriva.py')
    texto = '\n'.join(c for _, _, c in scripts(wf))
    for clave in set(re.findall(r"\b[dr]\['(\w+)'\]", texto)):
        assert f"'{clave}'" in deriva, f'la clave JSON «{clave}» que lee el workflow no existe en deriva.py'
    for clave in ('hay_deriva', 'superan_umbral', 'variables', 'hay_alerta', 'caida_maxima', 'avisos', 'cortes', 'umbral_psi', 'tolerancia'):
        assert f"'{clave}'" in deriva, clave


def test_las_rutas_de_los_artefactos_coinciden(wf):
    subida = wf['jobs']['deriva']['steps'][-1]['with']
    assert subida['name'] == 'monitoreo' and subida['path'] == '04-Proyecto-Base/reports/monitoreo/'
    bajada = pasos(wf['jobs']['alerta'])[0]['with']
    assert bajada == {'name': 'monitoreo', 'path': 'salidas'}
    texto = '\n'.join(c for n, _, c in scripts(wf) if n == 'alerta')
    assert 'salidas/datos.json' in texto and 'salidas/rendimiento.json' in texto
    gen = '\n'.join(c for n, _, c in scripts(wf) if n == 'deriva')
    assert 'reports/monitoreo/datos.json' in gen and 'reports/monitoreo/rendimiento.json' in gen and 'mkdir -p reports/monitoreo' in gen
    # el primer trabajo sube lo que el segundo necesita: modelo y base analítica
    primero = wf['jobs']['datos']['steps'][-1]['with']
    assert 'models/' in primero['path'] and 'curso.db' in primero['path']
    bajada_datos = [p['with'] for p in pasos(wf['jobs']['deriva']) if str(p.get('uses', '')).startswith('actions/download-artifact')]
    assert bajada_datos == [{'name': 'datos-y-modelo', 'path': '04-Proyecto-Base'}]


def test_exit_2_rompe_el_run_y_exit_0_y_1_no(wf):
    medir = paso_con(wf, 'deriva', 'Medir la deriva')['run']
    assert '|| cd_datos=$?' in medir and '|| cd_rend=$?' in medir
    assert 'shell' in paso_con(wf, 'deriva', 'Medir la deriva') and paso_con(wf, 'deriva', 'Medir la deriva')['shell'] == 'bash'   # pipefail
    assert '-ge 2' in medir and 'exit 1' in medir


# ------------------------------------------------------------------------------------------------ sintaxis
def _python_embebido(cuerpo):
    return [textwrap.dedent(m) for m in re.findall(r"python3? - <<'FIN'[^\n]*\n(.*?)\n\s*FIN\n", cuerpo + '\n', re.S)]


def test_los_fragmentos_de_python_compilan(wf):
    total = 0
    for nombre, paso, cuerpo in scripts(wf):
        for fragmento in _python_embebido(cuerpo):
            ast.parse(fragmento)
            total += 1
    assert total == 2          # el resumen (trabajo 2) y el título/cuerpo del issue (trabajo 3)


def _bash():
    if os.name == 'nt':        # en Windows solo vale el bash de Git (otros, como el de WSL o MKS, no son el de los runners)
        for c in (os.environ.get('CURSO_BASH'), r'C:\Program Files\Git\bin\bash.exe', r'C:\bk\software\git\bin\bash.exe'):
            if c and Path(c).exists():
                return c
        return None
    return shutil.which('bash')


def test_los_pasos_de_bash_tienen_sintaxis_correcta(wf, tmp_path):
    bash = _bash()
    if not bash:
        pytest.skip('no hay bash de Git para comprobar la sintaxis')
    n = 0
    for nombre, paso, cuerpo in scripts(wf):
        sin_expresiones = re.sub(r'\$\{\{.*?\}\}', 'valor', cuerpo)
        archivo = tmp_path / 'paso.sh'
        archivo.write_text(sin_expresiones, encoding='utf-8', newline='\n')
        r = subprocess.run([bash, '-n', str(archivo)], capture_output=True, text=True)
        assert r.returncode == 0, f'{nombre}/{paso}: {r.stderr}'
        n += 1
    assert n >= 8


def test_sin_bom_ni_crlf_ni_tabuladores():
    datos = YML.read_bytes()
    assert not datos.startswith(b'\xef\xbb\xbf') and b'\r\n' not in datos and b'\t' not in datos
    datos.decode('utf-8')


# ------------------------------------------------------------------------------------------------ escenarios sobre los datos reales
def _copiar_proyecto(destino):
    """Copia ligera de 04-Proyecto-Base (sin datos generados, modelos ni el Excel completo)."""
    def ignorar(carpeta, nombres):
        rel = Path(carpeta).resolve().relative_to(PROYECTO.resolve()).as_posix()
        fuera = {'__pycache__', '.pytest_cache', '.git', '.venv', 'notebooks', 'deploy', 'agentes', 'skills', 'references'}
        if rel == '.':
            return [n for n in nombres if n in fuera or n in ('models', 'reports', 'tests', '.devcontainer')]
        if rel == 'data':
            return [n for n in nombres if n in ('external', 'processed')]
        if rel == 'data/raw':
            return [n for n in nombres if n == 'online_retail_ii']
        return [n for n in nombres if n in fuera]
    shutil.copytree(PROYECTO, destino, ignore=ignorar)
    (destino / 'models').mkdir()
    (destino / 'reports').mkdir()
    (destino / 'data' / 'external').mkdir(exist_ok=True)
    (destino / 'data' / 'processed').mkdir(exist_ok=True)
    (destino / 'tests' / 'datos').mkdir(parents=True)
    shutil.copy(PROYECTO / 'tests' / 'datos' / 'cliente_ejemplo.json', destino / 'tests' / 'datos' / 'cliente_ejemplo.json')


def _python(destino, *args):
    env = dict(os.environ, CURSO_SIN_PANTALLA='1', PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    return subprocess.run([sys.executable, '-W', 'ignore', *args], cwd=destino, env=env, capture_output=True, text=True, encoding='utf-8')


@pytest.fixture(scope='module')
def copia(tmp_path_factory):
    if os.environ.get('CURSO_SIN_ESCENARIOS') == '1':
        pytest.skip('CURSO_SIN_ESCENARIOS=1')
    destino = tmp_path_factory.mktemp('proyecto') / 'p'
    _copiar_proyecto(destino)
    for modulo in ('ia_mlops.operacional', 'ia_mlops.pipeline'):         # el primer trabajo del workflow
        r = _python(destino, '-m', modulo)
        assert r.returncode == 0, f'{modulo}: {r.stdout[-800:]} {r.stderr[-800:]}'
    return destino


def _escenario(wf, rama):
    """Lee del propio `case` del workflow qué referencia, actual y umbral da cada rama de ensayo (no se repiten aquí a mano)."""
    case = paso_con(wf, 'deriva', 'Elegir el escenario')['run']
    m = re.search(rf'lab/monitoreo/{rama}\)\s+REF=([\d-]+);\s+ACT=("?)(\S+?)\2;\s+UMBRAL=([\d.]+);', case)
    assert m, rama
    return m.group(1), m.group(3), m.group(4)


def test_escenario_estable_da_salida_0_sobre_los_datos_reales(wf, copia):
    ref, act, umbral = _escenario(wf, 'estable')
    assert (ref, act, umbral) == ('2010-08-01', '2010-09-01', '0.50')
    r = _python(copia, '-m', 'ia_mlops.deriva', 'datos', '--referencia', ref, '--actual', act, '--umbral-psi', umbral, '--json', 'reports/estable.json')
    assert r.returncode == 0, r.stdout
    d = json.loads((copia / 'reports' / 'estable.json').read_text(encoding='utf-8'))
    assert d['hay_deriva'] is False and d['superan_umbral'] == []
    por = {v['variable']: v for v in d['variables']}
    assert round(por['antiguedad_dias']['psi'], 3) == 0.410 and por['antiguedad_dias']['estado'] == 'moderada'
    assert 'Sin deriva relevante' in r.stdout
    # con el umbral por defecto la MISMA pareja sí alerta (lo que cuenta la guía)
    r2 = _python(copia, '-m', 'ia_mlops.deriva', 'datos', '--referencia', ref, '--actual', act)
    assert r2.returncode == 1 and 'DERIVA: 1 de 13 variables superan el umbral (antiguedad_dias)' in r2.stdout


def test_escenario_deriva_da_salida_1_con_las_cinco_variables_de_la_guia(wf, copia):
    ref, act, umbral = _escenario(wf, 'deriva')
    assert (ref, umbral) == ('2010-12-01', '0.25') and act == '$AHORA'
    r = _python(copia, '-m', 'ia_mlops.deriva', 'cortes', '--json', 'reports/cortes.json')
    assert r.returncode == 0
    ahora = json.loads((copia / 'reports' / 'cortes.json').read_text(encoding='utf-8'))['ahora']
    assert ahora == '2011-12-10'
    r = _python(copia, '-m', 'ia_mlops.deriva', 'datos', '--referencia', ref, '--actual', ahora, '--umbral-psi', umbral, '--json', 'reports/deriva.json')
    assert r.returncode == 1, r.stdout
    d = json.loads((copia / 'reports' / 'deriva.json').read_text(encoding='utf-8'))
    assert d['hay_deriva'] is True
    assert d['superan_umbral'] == ['antiguedad_dias', 'recencia_dias', 'frecuencia_180d', 'monto_90d', 'frecuencia_90d']
    psi = {v['variable']: round(v['psi'], 3) for v in d['variables']}
    assert (psi['antiguedad_dias'], psi['recencia_dias'], psi['frecuencia_180d'], psi['monto_90d'], psi['frecuencia_90d']) == (2.830, 0.437, 0.400, 0.293, 0.276)
    assert (psi['es_reino_unido'], psi['ticket_medio'], psi['devoluciones']) == (0.000, 0.012, 0.018)
    assert 'DERIVA: 5 de 13 variables' in r.stdout


def test_rendimiento_da_salida_0_en_los_dos_escenarios_y_1_con_un_corte_de_entrenamiento(wf, copia):
    cortes = re.search(r'CORTES_RENDIMIENTO: "([\d\- ]+)"', YML.read_text(encoding='utf-8')).group(1).split()
    assert cortes == ['2011-03-01', '2011-06-01', '2011-09-01']
    r = _python(copia, '-m', 'ia_mlops.deriva', 'rendimiento', '--cortes', *cortes, '--json', 'reports/rendimiento.json')
    assert r.returncode == 0, r.stdout
    d = json.loads((copia / 'reports' / 'rendimiento.json').read_text(encoding='utf-8'))
    assert d['hay_alerta'] is False
    assert [round(c['auc'], 4) for c in d['cortes']] == [0.6982, 0.7534, 0.7423]
    r = _python(copia, '-m', 'ia_mlops.deriva', 'rendimiento', '--cortes', '2010-12-01', *cortes)
    assert r.returncode == 1 and 'SOBREESTIMA' in r.stdout and round(0.8497, 4) == 0.8497 and '0.8497' in r.stdout


def _script_python(wf, trabajo, indice=0):
    cuerpos = [f for n, _, c in scripts(wf) if n == trabajo for f in _python_embebido(c)]
    return cuerpos[indice]


def _preparar_json(copia, tmp_path, escenario):
    carpeta = tmp_path / 'reports' / 'monitoreo'
    carpeta.mkdir(parents=True)
    ref, act, umbral = {'estable': ('2010-08-01', '2010-09-01', '0.50'), 'deriva': ('2010-12-01', '2011-12-10', '0.25')}[escenario]
    for sub, args, nombre in (('datos', ['--referencia', ref, '--actual', act, '--umbral-psi', umbral], 'datos.json'),
                              ('rendimiento', ['--cortes', '2011-03-01', '2011-06-01', '2011-09-01'], 'rendimiento.json')):
        _python(copia, '-m', 'ia_mlops.deriva', sub, *args, '--json', str(carpeta / nombre))
    return carpeta


def test_el_resumen_del_run_se_genera_con_los_json_reales(wf, copia, tmp_path):
    for escenario, esperado in (('estable', 'Sin alerta'), ('deriva', 'ALERTA')):
        base = tmp_path / escenario
        base.mkdir()
        carpeta = _preparar_json(copia, base, escenario)
        script = _script_python(wf, 'deriva')
        r = subprocess.run([sys.executable, '-c', script], cwd=base, capture_output=True, text=True, encoding='utf-8')
        assert r.returncode == 0, r.stderr
        assert f'**{esperado}**' in r.stdout and '## Monitoreo del modelo' in r.stdout
        assert '| Variable | PSI | KS | Estado |' in r.stdout and '| Corte | Uso | Clientes | AUC | Caída |' in r.stdout
        assert '| 2011-03-01 | validación | 114 | 0.6982 | +0.0000 |' in r.stdout and '| 2011-09-01 | prueba | 131 | 0.7423 | -0.0441 |' in r.stdout
        if escenario == 'deriva':
            assert '| `antiguedad_dias` | 2.830 | 0.736 | deriva **supera el umbral** |' in r.stdout
            assert 'Superan el umbral: **5 de 13** variables' in r.stdout
        else:
            assert '| `antiguedad_dias` | 0.410 | 0.261 | moderada |' in r.stdout and 'Superan el umbral: **0 de 13**' in r.stdout
            assert 'supera el umbral' not in r.stdout.replace('Superan el umbral', '')


def test_el_titulo_y_el_cuerpo_del_issue_se_generan_con_los_json_reales(wf, copia, tmp_path):
    carpeta = _preparar_json(copia, tmp_path, 'deriva')
    shutil.copytree(carpeta, tmp_path / 'salidas')
    script = _script_python(wf, 'alerta')
    env = dict(os.environ, URL_RUN='https://github.com/x/y/actions/runs/1', REF='2010-12-01', ACT='2011-12-10', UMBRAL='0.25')
    r = subprocess.run([sys.executable, '-c', script], cwd=tmp_path, env=env, capture_output=True, text=True, encoding='utf-8')
    assert r.returncode == 0, r.stderr
    titulo = (tmp_path / 'titulo.txt').read_text(encoding='utf-8')
    cuerpo = (tmp_path / 'cuerpo.md').read_text(encoding='utf-8')
    assert titulo == 'Alerta de deriva: 5 variables superan el PSI 0.25 (referencia 2010-12-01, actual 2011-12-10)'
    assert 'https://github.com/x/y/actions/runs/1' in cuerpo
    assert '| `antiguedad_dias` | 2.830 | 0.736 |' in cuerpo and '| `frecuencia_90d` | 0.276 | 0.213 |' in cuerpo
    assert '`es_reino_unido`' not in cuerpo and 'Qué hacer' in cuerpo and 'AUC cae' not in titulo
    assert '\n' not in titulo


def _bash_paso(copia, tmp_path, paso, **entorno):
    """Ejecuta de verdad (con el bash de Git y `-eo pipefail`, como los runners) el bloque `run` de un paso, dentro de la copia del proyecto."""
    bash = _bash()
    if not bash:
        pytest.skip('no hay bash de Git')
    archivo = tmp_path / f'{paso["id"]}.sh'
    archivo.write_text(paso['run'], encoding='utf-8', newline='\n')
    carpeta = Path(sys.executable).parent
    ruta = os.pathsep.join([str(carpeta), str(carpeta / 'Library' / 'bin'), str(carpeta / 'Scripts'), os.environ.get('PATH', '')])
    salida = tmp_path / f'{paso["id"]}.out'
    salida.write_text('', encoding='utf-8')
    env = dict(os.environ, PATH=ruta, PYTHONUTF8='1', CURSO_SIN_PANTALLA='1', GITHUB_OUTPUT=str(salida),
               CORTES_RENDIMIENTO='2011-03-01 2011-06-01 2011-09-01', **entorno)
    r = subprocess.run([bash, '--noprofile', '--norc', '-eo', 'pipefail', str(archivo).replace('\\', '/')], cwd=copia, env=env, capture_output=True,
                       text=True, encoding='utf-8')
    return r, dict(l.split('=', 1) for l in salida.read_text(encoding='utf-8').splitlines() if '=' in l)


def _paso_id(wf, identificador):
    return [p for p in pasos(wf['jobs']['deriva']) if p.get('id') == identificador][0]


def test_el_paso_de_elegir_escenario_funciona_en_bash_para_cada_disparador(wf, copia, tmp_path):
    paso = _paso_id(wf, 'escenario')
    casos = [
        ({'GITHUB_EVENT_NAME': 'push', 'GITHUB_REF_NAME': 'lab/monitoreo/estable'}, ('2010-08-01', '2010-09-01', '0.50')),
        ({'GITHUB_EVENT_NAME': 'push', 'GITHUB_REF_NAME': 'lab/monitoreo/deriva'}, ('2010-12-01', '2011-12-10', '0.25')),
        ({'GITHUB_EVENT_NAME': 'schedule', 'GITHUB_REF_NAME': 'develop'}, ('2010-12-01', '2011-12-10', '0.25')),
        # a mano desde una rama de ensayo: mandan las entradas, no el nombre de la rama
        ({'GITHUB_EVENT_NAME': 'workflow_dispatch', 'GITHUB_REF_NAME': 'lab/monitoreo/estable', 'ENTRADA_REFERENCIA': '2010-08-01',
          'ENTRADA_UMBRAL': '0.5'}, ('2010-08-01', '2011-12-10', '0.5')),
    ]
    for entorno, esperado in casos:
        base = dict(ENTRADA_REFERENCIA='', ENTRADA_ACTUAL='', ENTRADA_UMBRAL='')
        base.update(entorno)
        r, out = _bash_paso(copia, tmp_path, paso, **base)
        assert r.returncode == 0, r.stdout + r.stderr
        assert (out['referencia'], out['actual'], out['umbral']) == esperado, entorno
    # una rama de ensayo desconocida y una fecha mal escrita rompen el paso con un mensaje claro
    r, _ = _bash_paso(copia, tmp_path, paso, GITHUB_EVENT_NAME='push', GITHUB_REF_NAME='lab/monitoreo/otra', ENTRADA_REFERENCIA='', ENTRADA_ACTUAL='', ENTRADA_UMBRAL='')
    assert r.returncode == 1 and 'Rama de ensayo desconocida' in r.stdout
    r, _ = _bash_paso(copia, tmp_path, paso, GITHUB_EVENT_NAME='workflow_dispatch', GITHUB_REF_NAME='develop', ENTRADA_REFERENCIA='2010-12-1',
                      ENTRADA_ACTUAL='', ENTRADA_UMBRAL='')
    assert r.returncode == 1 and 'fecha no válida' in r.stdout


def test_el_paso_de_medir_funciona_en_bash_y_los_codigos_0_1_y_2_se_tratan_como_se_promete(wf, copia, tmp_path):
    paso = _paso_id(wf, 'medir')
    r, out = _bash_paso(copia, tmp_path, paso, REF='2010-12-01', ACT='2011-12-10', UMBRAL='0.25')
    assert r.returncode == 0 and out == {'alerta': 'true', 'salida_datos': '1', 'salida_rendimiento': '0'}, r.stdout + r.stderr       # deriva: el paso NO falla
    r, out = _bash_paso(copia, tmp_path, paso, REF='2010-08-01', ACT='2010-09-01', UMBRAL='0.50')
    assert r.returncode == 0 and out == {'alerta': 'false', 'salida_datos': '0', 'salida_rendimiento': '0'}, r.stdout + r.stderr
    r, out = _bash_paso(copia, tmp_path, paso, REF='2010-12-01', ACT='2011-12-10', UMBRAL='abc')                                        # error: sí falla
    assert r.returncode == 1 and 'terminó con error (2)' in r.stdout

# ------------------------------------------------------------------------------------------------ cabecera honesta y nada en GitHub
def test_la_cabecera_cuenta_el_estable_con_su_umbral_y_avisa_del_schedule_con_datos_congelados():
    cabecera = YML.read_text(encoding='utf-8').split('\nname:')[0]
    assert 'umbral de PSI 0,50' in cabecera and '0,410' in cabecera
    assert 'datos del curso están congelados' in cabecera
    assert '5 de 13' in cabecera


def test_no_se_crea_nada_en_github():
    assert not (LAB / '.github').exists() and not list(LAB.rglob('.github'))
