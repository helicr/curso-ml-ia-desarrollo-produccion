"""Pruebas de los scripts de Cloud Shell (scripts/*.sh).

Dos niveles:
    1. ESTÁTICO: `bash -n` de cada script, que lleven `set -euo pipefail`, que carguen variables.sh, que usen las opciones de gcloud que
       documenta Google (--parent-model, --version-aliases, --labels, --container-ports/-predict-route/-health-route, --traffic-split,
       undeploy-model, --min-replica-count), que NO usen --artifact-uri ni :latest ni claves, y que avisen de lo que cuesta.
    2. EJECUCIÓN REAL contra un `gcloud` SIMULADO (pruebas/gcloud_simulado.py): se lanzan los scripts con bash de verdad, con el
       registro de MLflow real (una copia) y el adaptador real, y el simulador comprueba las reglas de la documentación (el reparto de
       tráfico suma 100, no se borra un endpoint con modelos desplegados...). Es el recorrido completo: subir, desplegar, probar, subir una
       versión nueva, canario, promover, volver (con y sin la versión anterior desplegada), borrar. NO prueba Google Cloud.
Si no hay un bash (el de Git), el nivel 2 se omite; CURSO_BASH puede indicarlo.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import AQUI, PROYECTO, REGISTRO_REAL

SCRIPTS = sorted((AQUI / 'scripts').glob('*.sh'))
NOMBRES = [p.name for p in SCRIPTS]


def _bash():
    candidatos = [os.environ.get('CURSO_BASH'), r'C:\bk\software\git\bin\bash.exe', r'C:\Program Files\Git\bin\bash.exe',
                  str(Path.home() / 'AppData' / 'Local' / 'Programs' / 'Git' / 'bin' / 'bash.exe'), '/bin/bash', '/usr/bin/bash']
    for c in candidatos:
        if c and Path(c).exists():
            return c
    return None


BASH = _bash()
necesita_bash = pytest.mark.skipif(BASH is None, reason='no hay bash (instala Git for Windows o define CURSO_BASH)')


def codigo(p):
    """El script sin líneas de comentario ni vacías."""
    return '\n'.join(l for l in p.read_text(encoding='utf-8').splitlines() if l.strip() and not l.strip().startswith('#'))


# ------------------------------------------------------------------------------------------------ 1. estático
def test_estan_todos_los_scripts():
    assert NOMBRES == ['borrar.sh', 'desplegar.sh', 'preparar_gcp.sh', 'probar.sh', 'promover.sh', 'subir_modelo.sh', 'variables.sh', 'volver.sh']


@pytest.mark.parametrize('nombre', NOMBRES)
def test_higiene_de_cada_script(nombre):
    p = AQUI / 'scripts' / nombre
    datos = p.read_bytes()
    assert not datos.startswith(b'\xef\xbb\xbf') and b'\r\n' not in datos, 'sin BOM y con LF'
    datos.decode('utf-8')
    t = p.read_text(encoding='utf-8')
    assert t.startswith('#!/usr/bin/env bash')
    assert 'C:\\' not in t and 'AppData' not in t and not re.search(r'(token|password|secret|private_key)\s*[:=]\s*\S{6,}', t, re.I)
    assert '.json"' not in codigo(p) or 'credenciales' not in codigo(p)


@pytest.mark.parametrize('nombre', [n for n in NOMBRES if n != 'variables.sh'])
def test_cada_script_es_estricto_y_carga_las_variables_comunes(nombre):
    c = codigo(AQUI / 'scripts' / nombre)
    assert 'set -euo pipefail' in c and 'source "$DIR/variables.sh"' in c
    assert ':latest' not in c and '--artifact-uri' not in c


@necesita_bash
@pytest.mark.parametrize('nombre', NOMBRES)
def test_bash_n_de_cada_script(nombre):
    r = subprocess.run([BASH, '-n', str(AQUI / 'scripts' / nombre)], capture_output=True, text=True, encoding='utf-8')
    assert r.returncode == 0, r.stderr


def test_subir_modelo_usa_las_opciones_documentadas_de_models_upload():
    c = codigo(AQUI / 'scripts' / 'subir_modelo.sh')
    for opcion in ('gcloud ai models upload', '--container-image-uri', '--container-ports "$PUERTO"', '--container-predict-route "$RUTA_PREDICT"',
                   '--container-health-route "$RUTA_SALUD"', '--parent-model "projects/$PROYECTO/locations/$REGION/models/$NOMBRE_MODELO"',
                   '--version-aliases', '--labels "$ETIQUETAS"', '--model-id "$NOMBRE_MODELO"', '--version-description', 'docker push',
                   '--platform linux/amd64', 'gcloud artifacts repositories create', '--repository-format docker'):
        assert opcion in c, opcion
    assert 'mf etiquetas_gcloud' in c and 'mf etiqueta_imagen' in c


def test_desplegar_usa_traffic_split_con_la_clave_cero_y_replicas_minimas():
    c = codigo(AQUI / 'scripts' / 'desplegar.sh')
    for opcion in ('gcloud ai endpoints deploy-model', '--traffic-split "$REPARTO"', '--min-replica-count "$MIN_REPLICAS"', '--machine-type "$MAQUINA"',
                   '--model "$NOMBRE_MODELO@$VERSION_VERTEX"', 'split-nuevo', '--endpoint-id "$NOMBRE_ENDPOINT"'):
        assert opcion in c, opcion
    assert 'scale' not in c.lower()                          # nunca min 0


def test_promover_y_volver_mueven_el_trafico_con_endpoints_update_y_borrar_hace_undeploy_primero():
    assert 'gcloud ai endpoints update' in codigo(AQUI / 'scripts' / 'promover.sh') and 'split-solo' in codigo(AQUI / 'scripts' / 'promover.sh')
    v = codigo(AQUI / 'scripts' / 'volver.sh')
    assert 'gcloud ai endpoints update' in v and 'alias_modelo volver' in v and 'mlflow_version_anterior' in v and '--sin-mlflow' in v
    b = codigo(AQUI / 'scripts' / 'borrar.sh')
    assert b.index('undeploy-model') < b.index('gcloud ai endpoints delete') < b.index('gcloud ai models delete') < b.index('gcloud artifacts docker images delete')
    assert 'docker images describe' not in b          # sin etiqueta se mira con `images list` (SIN VERIFICAR que `describe` acepte la ruta sin etiqueta)
    assert 'retencion-90d-endpoint' not in b and 'retencion-90d-sklearn' not in b           # no toca la práctica 04


@pytest.mark.parametrize('nombre', ['subir_modelo.sh', 'desplegar.sh', 'probar.sh', 'promover.sh', 'volver.sh', 'borrar.sh'])
def test_los_scripts_que_crean_o_dejan_desplegado_avisan_de_lo_que_cuesta(nombre):
    t = (AQUI / 'scripts' / nombre).read_text(encoding='utf-8')
    cabecera = '\n'.join(t.splitlines()[:25])
    if nombre in ('desplegar.sh', 'volver.sh', 'subir_modelo.sh'):
        assert 'sin dato' in cabecera.lower() and ('COBRA' in cabecera or 'cobra' in cabecera)
    if nombre in ('probar.sh', 'promover.sh'):
        assert 'borrar.sh' in t
    assert 'Fuente' in t or 'Fuentes' in t or nombre in ('probar.sh', 'volver.sh', 'borrar.sh') or 'https://docs.cloud.google.com' in t


def test_variables_no_chocan_con_la_practica_04_y_usan_santiago():
    c = codigo(AQUI / 'scripts' / 'variables.sh')
    assert 'southamerica-west1' in c and 'retencion-90d-champion' in c and 'retencion-90d-champion-ep' in c
    assert 'retencion-90d-sklearn' not in c and 'retencion-90d-endpoint' not in c
    assert 'MIN_REPLICAS="${CURSO_MIN_REPLICAS:-1}"' in c


def test_preparar_gcp_no_crea_modelos_ni_endpoints_ni_cuentas_nuevas():
    c = codigo(AQUI / 'scripts' / 'preparar_gcp.sh')
    for prohibido in ('ai models upload', 'ai endpoints create', 'deploy-model', 'service-accounts create', 'buckets create'):
        assert prohibido not in c, prohibido
    assert 'roles/aiplatform.user' in c and 'roles/artifactregistry.writer' in c and 'GCP_PROVEEDOR_WIF' in c


# ------------------------------------------------------------------------------------------------ 2. ejecución contra gcloud simulado
@pytest.fixture(scope='module')
def entorno(tmp_path_factory, contexto):
    """Registro de MLflow COPIADO aparte (los scripts mueven el alias), `gcloud` y `docker` simulados y las variables de los scripts."""
    if not REGISTRO_REAL.exists():
        pytest.skip('no hay models/mlflow.db: entrena antes con  python -m ia_mlops.pipeline')
    base = tmp_path_factory.mktemp('scripts')
    models = base / 'models'
    models.mkdir()
    shutil.copy2(REGISTRO_REAL, models / 'mlflow.db')
    shutil.copytree(PROYECTO / 'models' / 'mlartifacts', models / 'mlartifacts')
    uri = 'sqlite:///' + (models / 'mlflow.db').as_posix()
    from ia_mlops import alias_modelo, config
    cliente = alias_modelo.conectar(uri)[1]
    versiones = sorted(int(v.version) for v in cliente.search_model_versions(f"name='{config.MODELO_REGISTRADO}'"))
    if len(versiones) < 2:
        pytest.skip('hacen falta dos versiones de «retencion-90d» en el registro para probar el rollback')
    alias_modelo.promover(cliente, versiones[-2])
    alias_modelo.promover(cliente, versiones[-1])
    # Lo que contestará el endpoint simulado: las predicciones reales del adaptador con el modelo del champion.
    import vertex_adaptador as va
    from fastapi.testclient import TestClient
    clientes = json.loads((AQUI / 'clientes_ejemplo.json').read_text(encoding='utf-8'))
    with TestClient(va.crear_app(contexto / 'modelo', '/salud', '/predict')) as c:
        base_pred = c.post('/predict', json={'instances': [[v[k] for k in config.FEATURES] for v in clientes.values()]}).json()['predictions']
    pred = base / 'predicciones.json'
    pred.write_text(json.dumps(base_pred), encoding='utf-8')
    bin_ = base / 'bin'
    bin_.mkdir()
    py = Path(sys.executable).as_posix()
    simulador = (AQUI / 'pruebas' / 'gcloud_simulado.py').as_posix()
    (bin_ / 'gcloud').write_bytes(f'#!/usr/bin/env bash\nexec "{py}" "{simulador}" "$@"\n'.encode())
    (bin_ / 'docker').write_bytes(
        f'#!/usr/bin/env bash\necho "docker $*" >> "$FAKE_GCLOUD_LOG"\nif [ "$1" = "push" ]; then "{py}" "{simulador}" __registrar_imagen "$2"; fi\n'.encode())
    env = {**os.environ, 'PATH': str(bin_) + os.pathsep + os.environ['PATH'], 'PYTHONUTF8': '1', 'PYTHONDONTWRITEBYTECODE': '1',
           'FAKE_GCLOUD_ESTADO': (base / 'estado.json').as_posix(), 'FAKE_GCLOUD_LOG': (base / 'llamadas.log').as_posix(),
           'FAKE_GCLOUD_PREDICCIONES': pred.as_posix(), 'FAKE_GCLOUD_PROYECTO': 'project-prueba',
           'CURSO_PROYECTO': 'project-prueba', 'CURSO_TRABAJO': (base / 'trabajo').as_posix(), 'CURSO_PYTHON': py,
           'CURSO_MLFLOW_URI': uri, 'CURSO_ESPERA_RETIRAR': '0', 'CURSO_DIR_PROYECTO': PROYECTO.as_posix()}
    env.pop('CURSO_MODELOS', None)
    return {'env': env, 'base': base, 'uri': uri, 'champion': versiones[-1], 'anterior': versiones[-2], 'cliente': cliente}


def ejecutar(entorno, script, *args, esperado=0):
    r = subprocess.run([BASH, str(AQUI / 'scripts' / script), *args], env=entorno['env'], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=600)
    salida = r.stdout + r.stderr
    assert r.returncode == esperado, f'{script} {args} salió con {r.returncode} (se esperaba {esperado}):\n{salida[-3000:]}'
    return salida


def estado(entorno):
    return json.loads(Path(entorno['env']['FAKE_GCLOUD_ESTADO']).read_text(encoding='utf-8'))


def llamadas(entorno):
    return Path(entorno['env']['FAKE_GCLOUD_LOG']).read_text(encoding='utf-8')


def trafico(entorno):
    ep = estado(entorno)['endpoints']['retencion-90d-champion-ep']
    nombre = {d['id']: d['displayName'] for d in ep['deployedModels']}
    return {nombre[i]: p for i, p in ep['trafficSplit'].items()}


@necesita_bash
def test_recorrido_completo_de_los_scripts_contra_gcloud_simulado(entorno):
    n, m = entorno['champion'], entorno['anterior']
    log_ant = lambda: llamadas(entorno)

    # 1. Subir la versión anterior (M) como primera versión del modelo
    s = ejecutar(entorno, 'subir_modelo.sh', str(m))
    e = estado(entorno)
    assert list(e['modelos']) == ['retencion-90d-champion'] and len(e['modelos']['retencion-90d-champion']['versiones']) == 1
    v1 = e['modelos']['retencion-90d-champion']['versiones'][0]
    assert v1['versionAliases'] == ['champion', f'mlflow-v{m}'] and v1['labels']['mlflow_version'] == str(m) and v1['labels']['curso'] == 'ml-ia'
    assert v1['imagen'].startswith('southamerica-west1-docker.pkg.dev/project-prueba/curso/retencion-vertex:v') and v1['imagen'].split(':')[1].startswith(f'v{m}-')
    assert v1['puerto'] == '8080' and v1['rutaPredict'] == '/predict' and v1['rutaSalud'] == '/salud'      # exactas: Git Bash no las convierte en rutas de Windows
    assert len(e['imagenes']) == 1 and e['repos'] == ['curso']
    assert 'docker build --platform linux/amd64' in log_ant() and 'docker push' in log_ant() and '--parent-model' not in log_ant()

    # 2. Repetirlo no hace nada nuevo (idempotente)
    s = ejecutar(entorno, 'subir_modelo.sh', str(m))
    assert 'ya está subida' in s and 'ya está en el Model Registry' in s
    assert len(estado(entorno)['modelos']['retencion-90d-champion']['versiones']) == 1

    # 3. Desplegar en un endpoint vacío: 100 % para la nueva
    s = ejecutar(entorno, 'desplegar.sh')
    assert 'Reparto de tráfico: 0=100' in s and trafico(entorno) == {f'mlflow-v{m}': 100}
    assert 'Ya está desplegada' in ejecutar(entorno, 'desplegar.sh')
    assert len(estado(entorno)['endpoints']['retencion-90d-champion-ep']['deployedModels']) == 1

    # 4. Probar: paridad con el modelo local
    s = ejecutar(entorno, 'probar.sh')
    assert 'PARIDAD: las predicciones del endpoint y las del modelo local coinciden.' in s and 'IGUAL' in s and 'DIFERENTE' not in s
    ejecutar(entorno, 'probar.sh')

    # 5. Subir el champion (N): una VERSIÓN NUEVA del mismo modelo, con la anterior recordada en sus etiquetas
    ejecutar(entorno, 'subir_modelo.sh')
    versiones = estado(entorno)['modelos']['retencion-90d-champion']['versiones']
    assert len(versiones) == 2 and versiones[1]['versionAliases'] == ['champion', f'mlflow-v{n}'] and versiones[0]['versionAliases'] == [f'mlflow-v{m}']
    assert versiones[1]['labels']['mlflow_version'] == str(n) and versiones[1]['labels']['mlflow_version_anterior'] == str(m)
    assert '--parent-model projects/project-prueba/locations/southamerica-west1/models/retencion-90d-champion' in log_ant()

    # 6. Desplegar en CANARIO: 10 % para la nueva, 90 % para la anterior; probar reintenta hasta que conteste la nueva
    s = ejecutar(entorno, 'desplegar.sh', '--canario', '10')
    assert re.search(r'Reparto de tráfico: 0=10,\d+=90', s) and trafico(entorno) == {f'mlflow-v{m}': 90, f'mlflow-v{n}': 10}
    s = ejecutar(entorno, 'probar.sh')
    assert 'intento 1: contestó otra versión' in s and 'PARIDAD: las predicciones' in s

    # 7. Promover: 100 % a la nueva; la anterior sigue desplegada y se avisa de que cobra
    s = ejecutar(entorno, 'promover.sh')
    assert trafico(entorno) == {f'mlflow-v{m}': 0, f'mlflow-v{n}': 100} and 'SIGUE COBRANDO' in s

    # 8. Rollback (la anterior sigue desplegada): solo se mueve el tráfico; con --sin-mlflow no se toca el alias
    s = ejecutar(entorno, 'volver.sh', '--sin-mlflow')
    assert trafico(entorno) == {f'mlflow-v{m}': 100, f'mlflow-v{n}': 0} and 'se mueve el tráfico' in s
    assert estado(entorno)['endpoints']['retencion-90d-champion-ep']['deployedModels'].__len__() == 2
    assert 'Sin cambios: ya sirve' in ejecutar(entorno, 'volver.sh', '--sin-mlflow', '--a-version', str(m))
    # la versión anterior no guardó otra anterior: volver sin decir a cuál es un error claro, y no toca el tráfico
    assert 'no hay a dónde volver' in ejecutar(entorno, 'volver.sh', '--sin-mlflow', esperado=1)
    assert trafico(entorno) == {f'mlflow-v{m}': 100, f'mlflow-v{n}': 0}

    # 9. Promover otra vez y retirar la anterior (undeploy): deja de haber dos máquinas
    ejecutar(entorno, 'promover.sh', '--retirar-anterior')
    assert trafico(entorno) == {f'mlflow-v{n}': 100}

    # 10. Rollback con la anterior YA RETIRADA: se vuelve a desplegar desde el Model Registry, y se mueve también el alias de MLflow
    from ia_mlops import alias_modelo
    assert alias_modelo.estado(entorno['cliente'])['alias'] == {'champion': n}
    s = ejecutar(entorno, 'volver.sh')
    assert 'se vuelve a desplegar' in s and trafico(entorno) == {f'mlflow-v{m}': 100, f'mlflow-v{n}': 0}
    assert alias_modelo.estado(entorno['cliente'])['alias'] == {'champion': m}, 'el alias champion de MLflow debe volver a la versión anterior a la vez'
    assert f'Rollback: @champion: v{n} -> v{m}' in s

    # 11. Borrar: todo fuera, el repositorio de Artifact Registry se queda (otras prácticas lo usan) y no se tocan los recursos de la práctica 04
    ejecutar(entorno, 'borrar.sh')
    e = estado(entorno)
    assert e['endpoints'] == {} and e['modelos'] == {} and e['imagenes'] == [] and e['repos'] == ['curso']
    assert not (entorno['base'] / 'trabajo').exists()
    assert 'retencion-90d-endpoint' not in llamadas(entorno) and 'retencion-90d-sklearn' not in llamadas(entorno)
    assert '--artifact-uri' not in llamadas(entorno)
    ejecutar(entorno, 'borrar.sh')                                                      # idempotente: no hay nada y no falla


@necesita_bash
def test_errores_de_uso_de_los_scripts(entorno):
    ejecutar(entorno, 'desplegar.sh', '--canario', '150', esperado=2)
    ejecutar(entorno, 'desplegar.sh', '--canario', 'x', esperado=2)
    ejecutar(entorno, 'desplegar.sh', '--otra', esperado=2)
    ejecutar(entorno, 'probar.sh', '--otra', esperado=2)
    ejecutar(entorno, 'promover.sh', '--otra', esperado=2)
    ejecutar(entorno, 'volver.sh', '--otra', esperado=2)
    ejecutar(entorno, 'borrar.sh', '--otra', esperado=2)
    s = ejecutar(entorno, 'desplegar.sh', esperado=2)                                  # sin manifiesto (se borró el trabajo)
    assert 'falta' in s and 'subir_modelo.sh' in s
