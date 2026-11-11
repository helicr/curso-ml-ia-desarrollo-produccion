"""Fixtures compartidas. Construyen UNA vez el operacional y la base analitica (raw -> master -> fs -> ml) desde la muestra incluida."""
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from ia_mlops import config, db, operacional as op, pipeline  # noqa: E402


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
