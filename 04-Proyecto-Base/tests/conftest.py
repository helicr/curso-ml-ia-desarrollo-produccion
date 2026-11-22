"""Fixtures compartidas. Construyen UNA vez el operacional y la base analitica (raw -> master -> fs -> ml) desde la muestra incluida."""
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from ia_mlops import config, db, operacional as op, pipeline  # noqa: E402
from ia_mlops.modeling import predict, train  # noqa: E402


@pytest.fixture(scope='session')
def rutas(tmp_path_factory):
    carpeta = tmp_path_factory.mktemp('base')
    operacional, analitica = carpeta / 'retail.db', carpeta / 'prueba.db'
    op.crear_operacional('muestra', operacional, verbose=False)
    pipeline.ejecutar(['pipeline_ingesta_raw', 'pipeline_ingesta_master', 'pipeline_ml'], ruta_db=analitica,
                      ruta_operacional=operacional, verbose=False)
    return operacional, analitica


@pytest.fixture(scope='session')
def ruta_db(rutas):
    return rutas[1]


@pytest.fixture(scope='session')
def ruta_operacional(rutas):
    return rutas[0]


@pytest.fixture()
def con(ruta_db):
    c = db.conectar(ruta_db)
    yield c
    c.close()


@pytest.fixture()
def con_operacional(ruta_operacional):
    c = db.conectar(ruta_operacional)
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


# ------------------------------------------------------------------------------------------------ agente (S5)
@pytest.fixture(scope='module')
def entorno_agente(ruta_db, carpeta_modelo, tmp_path_factory):
    """Todo lo que leen las herramientas del agente, en una carpeta temporal (nunca la base ni los reportes reales):
    una copia de la base con fs_produccion, una campaña de lote, la referencia y el historial de versiones.

    Apunta ia_mlops.agente.herramientas a esa carpeta y devuelve un objeto con `ruta_db`, `corte`, `carpeta_modelo` y `entorno`
    (las variables CURSO_* que necesita un proceso hijo, p. ej. el servidor MCP por stdio).
    """
    import json
    import shutil
    from types import SimpleNamespace

    import pandas as pd

    from ia_mlops import explotacion as ex
    from ia_mlops.agente import herramientas
    from ia_mlops.interfaz.consulta import Consulta

    carpeta = tmp_path_factory.mktemp('agente')
    ruta = carpeta / 'curso.db'
    shutil.copyfile(ruta_db, ruta)
    con = db.conectar(ruta, solo_lectura=False)
    corte = ex.corte_por_defecto(con)
    df = ex.variables_en_corte(con, corte)
    con.execute('DROP TABLE IF EXISTS fs_produccion')
    con.execute(f'''CREATE TABLE fs_produccion (cliente_id INTEGER NOT NULL, fecha_corte TEXT NOT NULL,
        {", ".join(f"{c} REAL" for c in config.FEATURES)},
        huella_modelo TEXT, version_modelo INTEGER, creado_en TEXT, PRIMARY KEY (cliente_id, fecha_corte))''')
    df.assign(fecha_corte=corte, huella_modelo='h-prueba', version_modelo=1, creado_en='2011-12-10T00:00:00')[
        ['cliente_id', 'fecha_corte', *config.FEATURES, 'huella_modelo', 'version_modelo', 'creado_en']
    ].to_sql('fs_produccion', con, if_exists='append', index=False)
    con.commit()
    # la campaña del lote: los mismos clientes puntuados con el modelo de la prueba, como la escribe explotacion.py
    todos = Consulta(ruta_db=ruta, url_api='', carpeta_modelo=carpeta_modelo).puntuacion_del_corte(con, corte)
    con.close()
    n_campana = max(1, len(todos) // 10)
    tabla = pd.DataFrame({'puesto': todos['puesto'], 'cliente_id': todos['cliente_id'], 'probabilidad': todos['probabilidad'],
                          'n_advertencias': todos['advertencias'].map(len), 'advertencias': todos['advertencias'].map(' | '.join),
                          'decil': todos['decil'], 'en_campana': todos['puesto'] <= n_campana})
    campana = carpeta / 'campana'
    campana.mkdir()
    tabla.to_csv(campana / f'campana_{corte}.csv', index=False)
    (campana / f'campana_{corte}.json').write_text(json.dumps({
        'corte': corte, 'clientes_puntuados': int(len(tabla)), 'clientes_en_campana': int(n_campana), 'modelo': 'regresion_logistica',
        'huella_datos': 'h', 'archivos': ['C:/ruta/privada/campana.csv']}), encoding='utf-8')
    # la versión en producción: copia de la ficha del repositorio (solo se lee) y un historial propio
    ref = json.loads(config.REFERENCIA.read_text(encoding='utf-8'))
    ruta_ref = carpeta / 'referencia.json'
    ruta_ref.write_text(json.dumps(ref), encoding='utf-8')
    (carpeta / 'historial_versiones.json').write_text(json.dumps({'versiones': [
        {'version': ref['version'], 'etiqueta_imagen': ref['etiqueta_imagen'], 'estado': 'produccion'}]}), encoding='utf-8')

    mp = pytest.MonkeyPatch()
    mp.setenv('CURSO_CAMPANA', str(campana))
    mp.setattr(config, 'REFERENCIA', ruta_ref)
    herramientas.configurar(ruta_db=ruta, carpeta_modelo=carpeta_modelo, url_api='')
    entorno = {'CURSO_DB': str(ruta), 'CURSO_MODELOS': str(carpeta_modelo), 'CURSO_CAMPANA': str(campana),
               'CURSO_REFERENCIA': str(ruta_ref), 'CURSO_URL_API': '', 'MLFLOW_DISABLE_AGENT_HINT': '1', 'PYTHONUTF8': '1'}
    yield SimpleNamespace(ruta_db=ruta, corte=corte, carpeta_modelo=carpeta_modelo, campana=campana, referencia=ref, entorno=entorno)
    herramientas.configurar()
    mp.undo()


# ------------------------------------------------------------------------------------------------ marca «gcp»
def omitir_gcp(items, entorno=None):
    """Las pruebas marcadas @pytest.mark.gcp necesitan una cuenta real de GCP: se omiten salvo que CURSO_PRUEBAS_GCP=1. Nunca fallan en CI."""
    import os
    entorno = os.environ if entorno is None else entorno
    if entorno.get('CURSO_PRUEBAS_GCP') == '1':
        return
    omitir = pytest.mark.skip(reason='necesita GCP real: se omite por defecto (CURSO_PRUEBAS_GCP=1 para ejecutarla)')
    for item in items:
        if item.get_closest_marker('gcp'):
            item.add_marker(omitir)


def pytest_collection_modifyitems(config, items):
    omitir_gcp(items)
