"""Pruebas de la imagen de la INTERFAZ y del compose SIN Docker: lo que se comprueba leyendo los archivos.

Que se construyan y arranquen juntas solo lo demuestra Docker de verdad (Codespaces o GitHub Actions: ver
docs/del-ordenador-al-servicio.md, «Qué se probó»). Estas pruebas evitan llegar allí con errores que se ven a simple vista.
"""
import json
import re
import subprocess
import sys

import pytest

from ia_mlops import config
from tests.test_imagen import _instrucciones, _regex, _versiones

RAIZ = config.RAIZ
DOCKERFILE = RAIZ / 'deploy' / 'docker' / 'interfaz.Dockerfile'
IGNORAR = RAIZ / 'deploy' / 'docker' / 'interfaz.Dockerfile.dockerignore'
COMPOSE = RAIZ / 'deploy' / 'docker' / 'compose.yaml'


def ins():
    return _instrucciones(DOCKERFILE.read_text(encoding='utf-8'))


def entra_en_el_contexto(ruta):
    """Reglas de Docker: gana el ÚLTIMO patrón que coincide con la ruta o con una de sus carpetas; «!» vuelve a incluir."""
    partes = ruta.split('/')
    prefijos = ['/'.join(partes[:k]) for k in range(1, len(partes) + 1)]
    dentro = True
    for linea in IGNORAR.read_text(encoding='utf-8').splitlines():
        linea = linea.strip()
        if not linea or linea.startswith('#'):
            continue
        negar = linea.startswith('!')
        patron = _regex(linea.lstrip('!'))
        if any(patron.fullmatch(p) for p in prefijos):
            dentro = negar
    return dentro


# --- Dockerfile ------------------------------------------------------------------------------------------------------------------

def test_misma_base_y_mismas_versiones_que_la_imagen_de_la_api():
    assert [r for i, r in ins() if i == 'FROM'] == ['python:3.11-slim']
    pip = [r for i, r in ins() if i == 'RUN' and 'pip install' in r]
    assert len(pip) == 1 and '-c requirements-api.lock' in pip[0] and '-r requirements-interfaz.txt' in pip[0]
    bloqueadas = _versiones(RAIZ / 'requirements-api.lock')
    for nombre in (l.strip() for l in (RAIZ / 'requirements-interfaz.txt').read_text(encoding='utf-8').splitlines()):
        if nombre and not nombre.startswith('#'):
            assert nombre.lower() in bloqueadas, f'{nombre} no está en requirements-api.lock: su versión no quedaría fijada'


def test_no_lleva_ni_modelo_ni_datos_solo_codigo_y_el_sql_de_las_variables():
    copias = [r.split() for i, r in ins() if i == 'COPY']
    origenes = [o for c in copias for o in c[:-1]]
    assert sorted(origenes) == sorted(['requirements-api.lock', 'requirements-interfaz.txt', 'ia_mlops/', 'sql/fs/02_poblar_fs.sql'])
    assert not any(o.startswith(('models', 'data')) for o in origenes)


def test_la_configuracion_va_por_variables_de_entorno():
    env = ' '.join(r for i, r in ins() if i == 'ENV')
    assert 'CURSO_DB=/datos/curso.db' in env and 'CURSO_DB_SOLO_LECTURA=1' in env and 'CURSO_URL_API=http://api:8080' in env


def test_sin_root_con_salud_y_el_puerto_de_la_aplicacion():
    usuario = [r for i, r in ins() if i == 'USER']
    assert usuario and usuario[-1] not in ('root', '0')
    salud = [r for i, r in ins() if i == 'HEALTHCHECK']
    assert salud and '/salud' in salud[0] and '8090' in salud[0]
    assert [r for i, r in ins() if i == 'EXPOSE'] == ['8090']
    cmd = json.loads([r for i, r in ins() if i == 'CMD'][0])
    assert cmd[:2] == ['uvicorn', 'ia_mlops.interfaz.app:app'] and cmd[cmd.index('--host') + 1] == '0.0.0.0'
    assert cmd[cmd.index('--port') + 1] == '8090'


def test_el_contexto_solo_deja_pasar_lo_que_se_copia():
    for ruta in ('ia_mlops/interfaz/app.py', 'ia_mlops/explotacion.py', 'sql/fs/02_poblar_fs.sql', 'requirements-api.lock', 'requirements-interfaz.txt'):
        assert entra_en_el_contexto(ruta), ruta
    for ruta in ('data/processed/curso.db', 'models/metadatos.json', 'models/modelo_mlflow/MLmodel', 'sql/fs/01_crear_fs.sql', '.env',
                 'tests/test_api.py', 'notebooks/04_entrenamiento_y_seguimiento.ipynb', 'ia_mlops/__pycache__/config.cpython-311.pyc', 'mlruns/0/x'):
        assert not entra_en_el_contexto(ruta), ruta
    # y todo lo que se copia existe
    for o in ('requirements-api.lock', 'requirements-interfaz.txt', 'ia_mlops', 'sql/fs/02_poblar_fs.sql'):
        assert (RAIZ / o).exists(), o


def test_la_interfaz_no_carga_las_librerias_del_modelo():
    """La imagen no instala scikit-learn ni mlflow: importar la aplicación no debe necesitarlos."""
    codigo = ("import os, sys; os.environ['CURSO_URL_API'] = 'http://api:8080'; import ia_mlops.interfaz.app; "
              "print([m for m in ('sklearn', 'mlflow', 'scipy', 'joblib', 'matplotlib') if m in sys.modules])")
    salida = subprocess.run([sys.executable, '-c', codigo], cwd=RAIZ, capture_output=True, text=True, check=True).stdout.strip()
    assert salida == '[]'


# --- compose ---------------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope='module')
def compose():
    yaml = pytest.importorskip('yaml')
    return yaml.safe_load(COMPOSE.read_text(encoding='utf-8'))


def test_compose_dos_servicios_y_solo_la_interfaz_se_publica(compose):
    s = compose['services']
    assert set(s) == {'api', 'interfaz'}
    assert 'ports' not in s['api']                     # la API solo se alcanza desde la red interna
    assert s['interfaz']['ports'] == ['8090:8090']
    assert s['api']['build']['dockerfile'] == 'deploy/docker/Dockerfile'
    assert s['interfaz']['build']['dockerfile'] == 'deploy/docker/interfaz.Dockerfile'
    for nombre in ('api', 'interfaz'):
        assert (COMPOSE.parent / s[nombre]['build']['context'] / s[nombre]['build']['dockerfile']).resolve().is_file()


def test_compose_la_interfaz_llama_a_la_api_por_su_nombre_y_lee_los_datos_en_solo_lectura(compose):
    i = compose['services']['interfaz']
    assert i['environment']['CURSO_URL_API'] == 'http://api:8080'
    assert i['volumes'] == ['../../data/processed:/datos:ro']
    assert (COMPOSE.parent / '../../data/processed').resolve() == (RAIZ / 'data' / 'processed').resolve()
    assert i['depends_on'] == {'api': {'condition': 'service_healthy'}}
    assert re.search(r'HEALTHCHECK', (RAIZ / 'deploy' / 'docker' / 'Dockerfile').read_text(encoding='utf-8'))   # sin él, «healthy» no llega nunca
