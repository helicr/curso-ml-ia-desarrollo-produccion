"""Fixtures compartidas. Construyen UNA vez la base completa (raw -> master -> fs -> ml) desde la muestra incluida."""
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from ia_mlops import config, db, pipeline  # noqa: E402
from ia_mlops.modeling import predict, train  # noqa: E402


@pytest.fixture(scope='session')
def ruta_db(tmp_path_factory):
    ruta = tmp_path_factory.mktemp('base') / 'prueba.db'
    pipeline.ejecutar('muestra', etapas=['raw', 'master', 'fs', 'ml'], ruta_db=ruta, verbose=False)
    return ruta


@pytest.fixture()
def con(ruta_db):
    c = db.conectar(ruta_db)
    yield c
    c.close()


@pytest.fixture()
def salidas_tmp(tmp_path, monkeypatch):
    """Desvia modelos y reportes a una carpeta temporal para no ensuciar el repositorio."""
    monkeypatch.setattr(config, 'MODELOS', tmp_path / 'models')
    monkeypatch.setattr(config, 'REPORTES', tmp_path / 'reports')
    return tmp_path


@pytest.fixture(scope='module')
def carpeta_modelo(ruta_db, tmp_path_factory):
    """Entrena una vez por modulo y deja el modelo (joblib + formato MLflow + metadatos) en una carpeta temporal."""
    destino = tmp_path_factory.mktemp('modelo_api')
    mp = pytest.MonkeyPatch()
    mp.setattr(config, 'MODELOS', destino / 'models')
    mp.setattr(config, 'REPORTES', destino / 'reports')
    con = db.conectar(ruta_db)
    train.entrenar(con, usar_mlflow=False, verbose=False)
    con.close()
    predict._CACHE.clear()
    yield destino / 'models'
    mp.undo()
    predict._CACHE.clear()


@pytest.fixture()
def arrancar_servidor(tmp_path):
    """Devuelve una funcion que arranca uvicorn COMO LO HACE EL CONTENEDOR (proceso aparte, salida a un archivo) y lo deja parado al terminar.

    arrancar(carpeta_modelos, cwd=None) -> (puerto, ruta_del_archivo_de_salida). Espera a que /listo responda.
    """
    import os
    import socket
    import subprocess
    import time
    import urllib.request

    procesos = []

    def _arrancar(carpeta_modelos, cwd=None):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            puerto = sock.getsockname()[1]
        entorno = dict(os.environ, CURSO_MODELOS=str(carpeta_modelos), MLFLOW_DISABLE_AGENT_HINT='1', PYTHONUNBUFFERED='1')
        salida = tmp_path / f'uvicorn-{puerto}.out'
        f = open(salida, 'w')
        proceso = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'ia_mlops.api.app:app', '--port', str(puerto)], stdout=f,
                                   stderr=subprocess.STDOUT, env=entorno, cwd=str(cwd) if cwd else None)
        procesos.append((proceso, f))
        for _ in range(80):
            try:
                urllib.request.urlopen(f'http://127.0.0.1:{puerto}/listo', timeout=1)
                return puerto, salida
            except Exception:           # noqa: BLE001 - todavia arrancando
                time.sleep(0.5)
        pytest.fail(f'el servidor no arranco:\n{salida.read_text()[-1500:]}')

    yield _arrancar
    for proceso, f in procesos:
        proceso.terminate()
        proceso.wait(timeout=10)
        f.close()
