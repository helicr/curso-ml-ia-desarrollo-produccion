"""Pruebas de los tres workflows (vertex-desplegar.yml, vertex-rollback.yml, vertex-borrar.yml). No ejecutan GitHub Actions: leen los archivos,
comprueban lo que prometen y ejecutan lo que SÍ se puede (bash -n de cada paso, las opciones de los scripts que llaman).

Estilo de las pruebas test_workflows_*.py de los otros laboratorios: YAML válido (PyYAML lee `on` como True), disparadores, permisos mínimos,
environment con aprobación, entrada a Google Cloud SIN CLAVES (WIF), sin secretos en claro, entradas bien usadas, que los comandos
coinciden con los scripts y que haya concurrency.
"""
import re
import subprocess
from pathlib import Path

import pytest
import yaml

from conftest import AQUI, PROYECTO, RAIZ
from test_scripts import BASH, necesita_bash

NOMBRES = ['vertex-desplegar.yml', 'vertex-rollback.yml', 'vertex-borrar.yml']
WF = {n: yaml.safe_load((AQUI / n).read_text(encoding='utf-8')) for n in NOMBRES}
TEXTO = {n: (AQUI / n).read_text(encoding='utf-8') for n in NOMBRES}


def disparadores(wf):
    return wf.get('on', wf.get(True))


def pasos(job):
    return job.get('steps', [])


def runs(wf):
    for nombre, job in wf['jobs'].items():
        for p in pasos(job):
            if 'run' in p:
                yield nombre, p.get('name', ''), p['run']


def trabajos_con_gcp(wf):
    return {n: j for n, j in wf['jobs'].items() if any(str(p.get('uses', '')).startswith('google-github-actions/auth@') for p in pasos(j))}


@pytest.fixture(params=NOMBRES)
def nombre(request):
    return request.param


# ------------------------------------------------------------------------------------------------ YAML y disparadores
def test_son_yaml_valido_con_nombre_y_trabajos(nombre):
    wf = WF[nombre]
    assert isinstance(wf, dict) and wf['name'].startswith('Vertex AI ·') and wf['jobs']
    assert True in wf and 'on' not in wf


def test_disparadores():
    d = disparadores(WF['vertex-desplegar.yml'])
    assert set(d) == {'push', 'workflow_dispatch'} and d['push']['branches'] == ['lab/vertex-champion/**']
    assert set(d['workflow_dispatch']['inputs']) == {'version_mlflow', 'dos_versiones', 'region', 'maquina', 'min_replicas', 'canario', 'auc_minimo', 'promover', 'retirar_anterior'}
    assert set(disparadores(WF['vertex-rollback.yml'])) == {'workflow_dispatch'}
    assert set(disparadores(WF['vertex-borrar.yml'])) == {'workflow_dispatch'}      # borrar NUNCA por un push
    assert set(disparadores(WF['vertex-rollback.yml'])['workflow_dispatch']['inputs']) == {'a_version', 'region', 'retirar_actual'}
    assert set(disparadores(WF['vertex-borrar.yml'])['workflow_dispatch']['inputs']) == {'confirmacion', 'region', 'con_imagenes'}


def test_los_valores_por_defecto_de_las_entradas_coinciden_con_los_de_los_scripts():
    entradas = disparadores(WF['vertex-desplegar.yml'])['workflow_dispatch']['inputs']
    v = (AQUI / 'scripts' / 'variables.sh').read_text(encoding='utf-8')
    assert entradas['maquina']['default'] == re.search(r'MAQUINA="\$\{CURSO_MAQUINA:-([\w-]+)\}"', v).group(1)
    assert entradas['min_replicas']['default'] == re.search(r'MIN_REPLICAS="\$\{CURSO_MIN_REPLICAS:-(\d+)\}"', v).group(1)
    assert entradas['canario']['default'] == re.search(r'CANARIO="\$\{CURSO_CANARIO:-(\d+)\}"', v).group(1)
    assert entradas['auc_minimo']['default'] == '0.65'
    import manifiesto_champion as mc
    assert float(entradas['auc_minimo']['default']) == mc.AUC_MINIMO
    assert entradas['promover']['default'] is True and entradas['retirar_anterior']['default'] is False and entradas['dos_versiones']['default'] is True


def test_no_estan_instalados_en_el_repositorio_del_curso():
    carpeta = RAIZ / '.github' / 'workflows'
    existentes = {p.name for p in carpeta.glob('*')} if carpeta.exists() else set()
    assert not existentes & set(NOMBRES), 'los workflows del extra se copian al fork del alumno: no van en .github/workflows del curso'


# ------------------------------------------------------------------------------------------------ permisos, environment y WIF
def test_permisos_minimos_contents_read_y_id_token_solo_donde_se_entra_en_google_cloud(nombre):
    wf = WF[nombre]
    assert wf['permissions'] == {'contents': 'read'}
    for n, job in wf['jobs'].items():
        permisos = job.get('permissions', {})
        assert permisos.get('contents', 'read') == 'read'
        if n in trabajos_con_gcp(wf):
            assert permisos == {'contents': 'read', 'id-token': 'write'}, n
        else:
            assert 'id-token' not in permisos, n
        assert not {k for k in permisos if k not in ('contents', 'id-token')}


def test_todo_trabajo_que_entra_en_google_cloud_pide_aprobacion_en_el_environment_produccion(nombre):
    wf = WF[nombre]
    assert trabajos_con_gcp(wf)
    for n, job in trabajos_con_gcp(wf).items():
        assert job.get('environment') == 'produccion', n
    for n, job in wf['jobs'].items():
        if n not in trabajos_con_gcp(wf):
            assert 'environment' not in job                         # lo que no toca la nube no espera a nadie


def test_wif_sin_claves_ni_secretos(nombre):
    t = TEXTO[nombre]
    assert 'secrets.' not in t and 'credentials_json' not in t and 'GOOGLE_APPLICATION_CREDENTIALS' not in t and 'private_key' not in t
    assert 'gcloud auth activate-service-account' not in t and '--key-file' not in t
    for job in trabajos_con_gcp(WF[nombre]).values():
        auth = next(p for p in pasos(job) if str(p.get('uses', '')).startswith('google-github-actions/auth@'))
        assert auth['with']['workload_identity_provider'] == '${{ vars.GCP_PROVEEDOR_WIF }}'
        assert auth['with']['service_account'] == '${{ vars.GCP_CUENTA_DESPLIEGUE }}' and auth['with']['project_id'] == '${{ vars.GCP_PROYECTO }}'
        assert any(str(p.get('uses', '')).startswith('google-github-actions/setup-gcloud@') for p in pasos(job))


def test_las_variables_de_github_son_variables_y_no_secretos(nombre):
    usadas = set(re.findall(r'vars\.(\w+)', TEXTO[nombre]))
    assert usadas <= {'GCP_PROYECTO', 'GCP_REGION', 'GCP_PROVEEDOR_WIF', 'GCP_CUENTA_DESPLIEGUE', 'GCP_REPO_AR', 'CURSO_MLFLOW_URI'}, usadas


def test_las_acciones_estan_fijadas_a_una_version_y_son_las_ya_usadas_en_el_curso(nombre):
    permitidas = {'actions/checkout': 'v4', 'actions/setup-python': 'v5', 'actions/upload-artifact': 'v4', 'actions/download-artifact': 'v4',
                  'google-github-actions/auth': 'v2', 'google-github-actions/setup-gcloud': 'v2'}
    for job in WF[nombre]['jobs'].values():
        for p in pasos(job):
            if 'uses' in p:
                accion, _, version = p['uses'].partition('@')
                assert permitidas.get(accion) == version, p['uses']


# ------------------------------------------------------------------------------------------------ entradas, concurrency, tiempos
def test_las_entradas_nunca_se_interpolan_dentro_de_los_scripts_run(nombre):
    """Una entrada con comillas o `$(...)` ejecutaría órdenes en el runner: las entradas pasan por `env:` y el script usa las variables."""
    for job, paso, run in runs(WF[nombre]):
        assert '${{ inputs.' not in run and '${{ github.event.' not in run and '${{ github.head_ref' not in run, f'{job} · {paso}'


def test_concurrency_comun_para_las_tres_operaciones_y_sin_cancelar():
    grupos = {WF[n]['concurrency']['group'] for n in NOMBRES}
    assert grupos == {'vertex-champion'} and all(WF[n]['concurrency']['cancel-in-progress'] is False for n in NOMBRES)


def test_todos_los_trabajos_tienen_tiempo_limite_y_shell_bash(nombre):
    for n, job in WF[nombre]['jobs'].items():
        assert isinstance(job['timeout-minutes'], int) and 0 < job['timeout-minutes'] <= 60, n
        if n != 'confirmar':
            assert job['defaults']['run']['shell'] == 'bash'


def test_el_trabajo_sin_checkout_no_hereda_working_directory():
    """Lección de S4: el trabajo que no descarga el repositorio no puede heredar una carpeta del proyecto. Aquí todos hacen checkout o no usan carpeta."""
    for nombre in NOMBRES:
        for n, job in WF[nombre]['jobs'].items():
            wd = job.get('defaults', {}).get('run', {}).get('working-directory')
            if wd:
                assert any(str(p.get('uses', '')).startswith('actions/checkout@') for p in pasos(job)), f'{nombre}:{n}'
                assert (RAIZ / wd).is_dir(), wd


def test_el_borrado_exige_confirmacion_escrita_antes_de_entrar_en_google_cloud():
    wf = WF['vertex-borrar.yml']
    assert wf['jobs']['borrar']['needs'] == 'confirmar'
    confirmar = wf['jobs']['confirmar']
    assert 'id-token' not in confirmar.get('permissions', {}) and 'environment' not in confirmar
    assert confirmar['env']['CONFIRMACION'] == '${{ inputs.confirmacion }}'
    run = '\n'.join(p['run'] for p in pasos(confirmar) if 'run' in p)
    assert '[ "$CONFIRMACION" != "BORRAR" ]' in run and 'exit 1' in run
    assert disparadores(wf)['workflow_dispatch']['inputs']['confirmacion']['required'] is True


def test_el_despliegue_prueba_antes_de_publicar_y_publica_la_misma_imagen():
    wf = WF['vertex-desplegar.yml']
    assert wf['jobs']['desplegar']['needs'] == 'modelo' and list(wf['jobs']) == ['modelo', 'desplegar']
    t = TEXTO['vertex-desplegar.yml']
    modelo = '\n'.join(p.get('name', '') for p in pasos(wf['jobs']['modelo']))
    assert modelo.index('PUERTA DE CALIDAD') < modelo.index('Construir la imagen') < modelo.index('Probar la imagen en el runner') < modelo.index('Guardar la imagen')
    assert 'docker save retencion-vertex:prueba' in t and 'docker load' in t and 'docker tag retencion-vertex:prueba' in t
    nombres_subidos = {p['with']['name'] for p in pasos(wf['jobs']['modelo']) if str(p.get('uses', '')).startswith('actions/upload-artifact')}
    nombres_bajados = {p['with']['name'] for p in pasos(wf['jobs']['desplegar']) if str(p.get('uses', '')).startswith('actions/download-artifact')}
    assert nombres_bajados == {'imagen', 'contexto'} and nombres_bajados <= nombres_subidos
    desplegar = [p.get('name', '') for p in pasos(wf['jobs']['desplegar'])]
    orden = [next(i for i, n in enumerate(desplegar) if frag in n) for frag in ('Entrar en Google Cloud', 'Subir la imagen', 'Registrar la versión', 'Desplegar en el endpoint', 'Probar una predicción', 'Pasar al 100')]
    assert orden == sorted(orden)


def test_los_pasos_que_llaman_a_los_scripts_usan_las_mismas_opciones_que_ellos():
    for n in NOMBRES:
        for job, paso, run in runs(WF[n]):
            for script, resto in re.findall(r'bash scripts/(\w+\.sh)([^\n|;&)]*)', run):
                p = AQUI / 'scripts' / script
                assert p.exists(), f'{n}: {script}'
                for opcion in re.findall(r'(--[\w-]+)', resto):
                    assert f'{opcion})' in p.read_text(encoding='utf-8'), f'{n}: {script} no acepta {opcion}'
            for a in re.findall(r'ARGS\+=\((--[\w-]+)', run) + re.findall(r'ARGS=\((--[\w-]+)', run):
                destino = 'volver.sh' if 'volver' in run else 'borrar.sh'
                assert f'{a})' in (AQUI / 'scripts' / destino).read_text(encoding='utf-8'), a


def test_los_comandos_python_del_proyecto_existen_con_sus_opciones():
    t = TEXTO['vertex-desplegar.yml']
    for modulo in set(re.findall(r'python -m (ia_mlops[\w.]*)', t)):
        assert (PROYECTO / Path(*modulo.split('.'))).with_suffix('.py').is_file(), modulo
    assert "'--forzar'" in (PROYECTO / 'ia_mlops' / 'pipeline.py').read_text(encoding='utf-8')
    alias = (PROYECTO / 'ia_mlops' / 'alias_modelo.py').read_text(encoding='utf-8')
    for sub in set(re.findall(r'alias_modelo (mostrar|promover|volver|cargar)', t)):
        assert f"add_parser('{sub}'" in alias
    assert "add_argument('--json'" in alias and "'--version'" in alias
    for archivo in set(re.findall(r'\$EXTRA/(\w+\.py)', t)) | set(re.findall(r'python (\w+\.py)', t)):
        assert (AQUI / archivo).is_file(), archivo
    for prueba in re.findall(r'\$EXTRA/pruebas/(\w+\.py)', t):
        assert (AQUI / 'pruebas' / prueba).is_file(), prueba
    for opcion in re.findall(r'manifiesto_champion\.py"? (generar|anotar|puerta|leer)', t):
        assert f"add_parser('{opcion}'" in (AQUI / 'manifiesto_champion.py').read_text(encoding='utf-8')


def test_las_variables_que_pone_el_workflow_son_las_que_leen_los_scripts():
    v = (AQUI / 'scripts' / 'variables.sh').read_text(encoding='utf-8') + (AQUI / 'scripts' / 'subir_modelo.sh').read_text(encoding='utf-8')
    for n in NOMBRES:
        for job in WF[n]['jobs'].values():
            for clave in job.get('env', {}):
                if clave.startswith('CURSO_') and clave not in ('CURSO_SIN_PANTALLA', 'CURSO_DIR_PROYECTO', 'CURSO_TRABAJO', 'CURSO_PYTHON'):
                    assert clave in v, f'{n}: {clave} no la lee ningún script'
    assert 'CURSO_TRABAJO' in v and 'CURSO_PYTHON' in v and 'CURSO_DIR_PROYECTO' in v


def test_las_salidas_del_manifiesto_que_usa_el_segundo_trabajo_existen():
    wf = WF['vertex-desplegar.yml']
    assert set(wf['jobs']['modelo']['outputs']) == {'version_mlflow', 'etiqueta_imagen'}
    paso = next(p for p in pasos(wf['jobs']['modelo']) if p.get('id') == 'manifiesto')
    assert 'version_mlflow=' in paso['run'] and 'etiqueta_imagen=' in paso['run'] and '"$GITHUB_OUTPUT"' in paso['run']
    assert 'needs.modelo.outputs.etiqueta_imagen' in TEXTO['vertex-desplegar.yml']


def test_resumen_con_el_enlace_mlflow_vertex_y_aviso_de_coste():
    t = TEXTO['vertex-desplegar.yml']
    assert 'GITHUB_STEP_SUMMARY' in t and '| MLflow | Vertex AI |' in t and 'COBRA' in t and 'mlflow-v$VER_MLFLOW' in t
    assert 'cobra' in TEXTO['vertex-rollback.yml'].lower() and 'GITHUB_STEP_SUMMARY' in TEXTO['vertex-borrar.yml']


def test_la_cabecera_dice_lo_que_no_esta_verificado_y_de_donde_sale_el_champion(nombre):
    t = TEXTO[nombre]
    cabecera = t.split('\non:')[0]
    assert 'SIN VERIFICAR' in cabecera and 'DÓNDE SE COPIA' in cabecera
    if nombre == 'vertex-desplegar.yml':
        assert 'models/mlflow.db' in cabecera and 'servidor de MLflow compartido' in cabecera and 'limitación honesta' in cabecera


# ------------------------------------------------------------------------------------------------ bash -n de cada paso
@necesita_bash
def test_bash_n_de_cada_paso_run(nombre, tmp_path):
    for job, paso, run in runs(WF[nombre]):
        sin_expresiones = re.sub(r'\$\{\{.*?\}\}', 'EXPR', run)
        f = tmp_path / 'paso.sh'
        f.write_bytes(sin_expresiones.encode('utf-8'))
        r = subprocess.run([BASH, '-n', str(f)], capture_output=True, text=True, encoding='utf-8')
        assert r.returncode == 0, f'{nombre} · {job} · {paso}: {r.stderr}'


def test_sin_bom_ni_crlf_ni_rutas_personales(nombre):
    datos = (AQUI / nombre).read_bytes()
    assert not datos.startswith(b'\xef\xbb\xbf') and b'\r\n' not in datos
    t = datos.decode('utf-8')
    assert 'C:\\' not in t and 'AppData' not in t and not re.search(r'ghp_|github_pat_', t)
    assert 'project-curso-ml-ia' not in t, 'el proyecto va en variables de GitHub, no escrito en el workflow'
