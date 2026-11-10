"""Pruebas de la imagen Docker SIN Docker: lo que se puede comprobar leyendo el Dockerfile, el .dockerignore y las dependencias.

Que NO prueban: que `docker build` y `docker run` funcionen. Eso solo lo demuestra ejecutarlos (en Codespaces o en GitHub Actions: ver
deploy/github-actions/ci.yml). Lo que si evitan es llegar al `docker build` con errores que se ven a simple vista.
"""
import json
import re
import shutil
import urllib.request
from pathlib import Path

import pytest

from ia_mlops import config
from ia_mlops.modeling import train

RAIZ = config.RAIZ
DOCKERFILE = RAIZ / 'deploy' / 'docker' / 'Dockerfile'


def _instrucciones(texto):
    """Instrucciones del Dockerfile (une las lineas que terminan en «\\» y descarta comentarios)."""
    unido = re.sub(r'\\\s*\n', ' ', texto)
    lineas = [l.strip() for l in unido.splitlines() if l.strip() and not l.strip().startswith('#')]
    return [(l.split(None, 1)[0].upper(), l.split(None, 1)[1] if ' ' in l else '') for l in lineas]


def _copias(texto):
    return [resto.split()[:-1] for inst, resto in _instrucciones(texto) if inst == 'COPY']


def _regex(patron):
    """Traduce un patron de .dockerignore a expresion regular: `*` no cruza «/», `**/` cruza carpetas, `?` es un caracter, `[abc]` es un conjunto."""
    p, salida, i = patron.rstrip('/'), '', 0
    while i < len(p):
        if p.startswith('**/', i):
            salida += '(?:.*/)?'
            i += 3
        elif p[i] == '*':
            salida += '[^/]*'
            i += 1
        elif p[i] == '?':
            salida += '[^/]'
            i += 1
        elif p[i] == '[':
            j = p.index(']', i)
            salida += p[i:j + 1]
            i = j + 1
        else:
            salida += re.escape(p[i])
            i += 1
    return re.compile(salida)


def _ignorado(ruta, patrones):
    """Reglas de .dockerignore: un patron se compara con la ruta (relativa al contexto) y con cada una de sus carpetas; si coincide una carpeta, se excluye todo lo que contiene.

    Ojo: `*.pyc` sin «**/» solo vale en la raiz del contexto; para cualquier carpeta hay que escribir `**/*.pyc`.
    """
    partes = ruta.split('/')
    prefijos = ['/'.join(partes[:k]) for k in range(1, len(partes) + 1)]
    return any(_regex(p).fullmatch(pre) for p in patrones for pre in prefijos)


def _patrones():
    return [l.strip() for l in (RAIZ / '.dockerignore').read_text(encoding='utf-8').splitlines() if l.strip() and not l.startswith('#')]


# --- Dockerfile ------------------------------------------------------------------------------------------------------------------

def test_el_dockerfile_usa_la_misma_version_de_python_que_el_entorno():
    base = [r for i, r in _instrucciones(DOCKERFILE.read_text(encoding='utf-8')) if i == 'FROM']
    assert base == ['python:3.11-slim']                  # environment.yml fija python=3.11


def test_las_dependencias_se_instalan_antes_de_copiar_el_codigo():
    """Si el codigo se copiara primero, cualquier cambio de una linea reinstalaria todas las dependencias."""
    orden = [(i, r) for i, r in _instrucciones(DOCKERFILE.read_text(encoding='utf-8')) if i in ('COPY', 'RUN')]
    instalar = next(k for k, (i, t) in enumerate(orden) if i == 'RUN' and 'pip install' in t)
    codigo = next(k for k, (i, t) in enumerate(orden) if i == 'COPY' and 'ia_mlops/' in t)
    assert instalar < codigo
    assert any(i == 'COPY' and 'requirements-api.lock' in t for i, t in orden[:instalar])
    assert 'requirements-api.lock' in [t for i, t in orden if i == 'RUN' and 'pip install' in t][0]


def test_no_se_ejecuta_como_root_y_tiene_comprobacion_de_salud():
    texto = DOCKERFILE.read_text(encoding='utf-8')
    usuario = [r for i, r in _instrucciones(texto) if i == 'USER']
    assert usuario and usuario[-1] not in ('root', '0')
    salud = [r for i, r in _instrucciones(texto) if i == 'HEALTHCHECK']
    assert salud and '/salud' in salud[0] and '8080' in salud[0]


def test_el_puerto_y_el_comando_coinciden_con_la_aplicacion():
    ins = _instrucciones(DOCKERFILE.read_text(encoding='utf-8'))
    assert [r for i, r in ins if i == 'EXPOSE'] == ['8080']
    cmd = json.loads([r for i, r in ins if i == 'CMD'][0])
    assert cmd[:2] == ['uvicorn', 'ia_mlops.api.app:app'] and cmd[cmd.index('--port') + 1] == '8080'
    from ia_mlops.api.app import app            # el objeto que nombra el CMD existe
    assert app.title


def test_el_dockerfile_dice_donde_estan_los_modelos():
    env = ' '.join(r for i, r in _instrucciones(DOCKERFILE.read_text(encoding='utf-8')) if i == 'ENV')
    assert 'CURSO_MODELOS=/app/models' in env


def test_el_dockerfile_no_copia_datos_ni_secretos():
    for origen in sum(_copias(DOCKERFILE.read_text(encoding='utf-8')), []):
        assert not origen.startswith(('data', 'sql', 'tests', 'notebooks', '.env', '.git')) and '.db' not in origen, origen


# --- .dockerignore: lo que se copia no puede estar excluido ---------------------------------------------------------------------------

def _archivos_de_la_imagen(carpeta_modelos):
    """(ruta relativa al contexto, archivo) de lo que el Dockerfile copia, tras entrenar.

    El modelo recien entrenado esta en una carpeta temporal (carpeta_modelos); todo lo demas, en el proyecto.
    """
    rutas = []
    for origenes in _copias(DOCKERFILE.read_text(encoding='utf-8')):
        for origen in origenes:
            if origen.startswith('models/'):
                p, base = carpeta_modelos / origen[len('models/'):].rstrip('/'), carpeta_modelos.parent
            else:
                p, base = RAIZ / origen.rstrip('/'), RAIZ
            if p.is_dir():
                rutas += [(f.relative_to(base).as_posix(), f) for f in sorted(p.rglob('*')) if f.is_file()]
            else:
                rutas.append((p.relative_to(base).as_posix(), p))
    return rutas


@pytest.fixture(scope='module')
def modelo_entrenado(ruta_db, tmp_path_factory):
    destino = tmp_path_factory.mktemp('imagen')
    mp = pytest.MonkeyPatch()
    mp.setattr(config, 'MODELOS', destino / 'models')
    mp.setattr(config, 'REPORTES', destino / 'reports')
    from ia_mlops import db
    con = db.conectar(ruta_db)
    train.entrenar(con, usar_mlflow=False, verbose=False)
    con.close()
    yield destino / 'models'
    mp.undo()


def test_lo_que_el_dockerfile_copia_no_queda_excluido_por_dockerignore(modelo_entrenado):
    rutas = _archivos_de_la_imagen(modelo_entrenado)
    assert any(r.endswith('MLmodel') for r, _ in rutas) and any(r == 'models/metadatos.json' for r, _ in rutas) and any(r.startswith('ia_mlops/api/') for r, _ in rutas)
    for ruta, archivo in rutas:
        if '__pycache__' in ruta or ruta.endswith('.pyc'):
            continue
        assert archivo.exists(), ruta
        assert not _ignorado(ruta, _patrones()), f'{ruta} lo copia el Dockerfile pero .dockerignore lo excluye'


def test_dockerignore_deja_fuera_datos_pruebas_y_artefactos_pesados():
    patrones = _patrones()
    for ruta in ['data/raw/muestra_online_retail_ii.csv', 'data/processed/curso.db', 'tests/test_api.py', 'notebooks/01_pipeline_raw_a_master.ipynb',
                 'models/mlflow.db', 'models/mlartifacts/0/x/model.pkl', 'models/modelo.joblib', '.git/config', '.env', 'ia_mlops/__pycache__/x.pyc']:
        assert _ignorado(ruta, patrones), ruta
    for ruta in ['models/modelo_mlflow/MLmodel', 'models/metadatos.json', 'ia_mlops/api/app.py', 'requirements-api.lock']:
        assert not _ignorado(ruta, patrones), ruta


def test_la_imagen_simulada_arranca_solo_con_lo_que_el_dockerfile_copia(modelo_entrenado, arrancar_servidor, tmp_path):
    """Replica la disposicion de la imagen (/app/ia_mlops, /app/models/...) en una carpeta nueva, sin datos, SQL ni pruebas, y arranca uvicorn alli.

    Detecta dependencias ocultas del servicio (rutas relativas al proyecto, archivos de datos). NO prueba la imagen base ni `pip install`.
    """
    app = tmp_path / 'app'
    for ruta, archivo in _archivos_de_la_imagen(modelo_entrenado):
        if '__pycache__' in ruta or _ignorado(ruta, _patrones()):
            continue
        destino = app / ruta
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(archivo, destino)
    assert sorted(p.name for p in app.iterdir()) == ['ia_mlops', 'models', 'requirements-api.lock']
    puerto, salida = arrancar_servidor(app / 'models', cwd=app)
    base = f'http://127.0.0.1:{puerto}'
    assert json.loads(urllib.request.urlopen(base + '/listo', timeout=5).read()) == {'estado': 'listo'}
    ejemplo = (RAIZ / 'tests' / 'datos' / 'cliente_ejemplo.json').read_bytes()
    pet = urllib.request.Request(base + '/predecir', data=ejemplo, headers={'content-type': 'application/json'})
    assert 0 <= json.loads(urllib.request.urlopen(pet, timeout=5).read())['probabilidad'] <= 1
    # Y que el codigo servido es el de la copia, no el del proyecto (el paquete esta instalado en modo editable en este entorno):
    # uvicorn arranca con la carpeta actual al principio de sys.path, igual que este comando.
    import subprocess
    import sys
    r = subprocess.run([sys.executable, '-c', 'import ia_mlops; print(ia_mlops.__file__)'], cwd=app, capture_output=True, text=True)
    assert Path(r.stdout.strip()).is_relative_to(app)


# --- dependencias de la imagen ----------------------------------------------------------------------------------------------------

def _versiones(ruta):
    out = {}
    for linea in ruta.read_text(encoding='utf-8').splitlines():
        linea = linea.strip()
        if linea and not linea.startswith('#') and '==' in linea:
            nombre, version = linea.split('==')
            out[nombre.strip().lower().replace('_', '-')] = version.strip()
    return out


def test_el_archivo_de_versiones_exactas_contiene_las_dependencias_directas():
    directas, exactas = _versiones(RAIZ / 'requirements-api.txt'), _versiones(RAIZ / 'requirements-api.lock')
    assert directas
    for nombre, version in directas.items():
        assert exactas.get(nombre) == version, nombre


def test_la_imagen_no_lleva_herramientas_de_desarrollo_ni_mlflow_completo():
    exactas = _versiones(RAIZ / 'requirements-api.lock')
    for ausente in ('pytest', 'jupyterlab', 'papermill', 'jupytext', 'matplotlib', 'mlflow', 'openpyxl', 'httpx', 'sqlalchemy'):
        assert ausente not in exactas, ausente
    assert 'mlflow-skinny' in exactas and 'fastapi' in exactas and 'uvicorn' in exactas


def test_las_versiones_directas_coinciden_con_el_entorno_del_curso():
    """Quien entrena (env-ia-mlops) y quien sirve (la imagen) deben usar las mismas versiones de lo que afecta al modelo."""
    import yaml
    ruta_entorno = RAIZ.parent / '03-Entorno' / 'conda' / 'environment.yml'
    if not ruta_entorno.exists():
        pytest.skip('environment.yml solo existe en el repositorio del curso; en tu repositorio (la raiz es el proyecto) no hay con que comparar')
    entorno = yaml.safe_load(ruta_entorno.read_text(encoding='utf-8'))
    del_entorno = {}
    for d in entorno['dependencies']:
        if isinstance(d, str) and '=' in d:
            n, v = d.split('=', 1)
            del_entorno[n.lower()] = v
    for nombre, version in _versiones(RAIZ / 'requirements-api.txt').items():
        if nombre in del_entorno:
            assert del_entorno[nombre] == version, nombre
    for nombre in ('numpy', 'pandas', 'scikit-learn', 'joblib', 'fastapi', 'uvicorn', 'pydantic'):
        assert nombre in del_entorno, nombre
