"""Fixtures compartidas. Construyen UNA vez la base completa (raw -> master -> fs -> ml) desde la muestra incluida."""
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from ia_mlops import config, db, pipeline  # noqa: E402


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
