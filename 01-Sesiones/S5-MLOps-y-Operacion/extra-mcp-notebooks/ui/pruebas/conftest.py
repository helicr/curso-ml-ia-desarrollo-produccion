"""Fixtures: la aplicación real (con sus dos servidores MCP) contra curso.db y el registro MLflow del curso.

El registro se deja EXACTAMENTE como se encontró (alias y etiquetas de cada versión), pase lo que pase.
"""
import json
import sys
from pathlib import Path

import pytest

UI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(UI))

import app as modulo_app                                 # noqa: E402

try:
    from ia_mlops.agente.llm import LLMFalso            # noqa: E402  (el LLM de guion del curso)
except Exception:                                        # noqa: BLE001
    LLMFalso = None

NOMBRE = 'retencion-90d'
MOTIVO = None
if not modulo_app.CURSO_DB.is_file():
    MOTIVO = 'No existe curso.db (crea la base con python -m ia_mlops.pipeline en 04-Proyecto-Base).'
elif modulo_app.alias_modelo is None:
    MOTIVO = 'No se puede importar ia_mlops (revisa MCP_PROYECTO).'
else:
    try:
        _c = modulo_app.alias_modelo.conectar()[1]
        if not _c.search_model_versions(f"name='{NOMBRE}'"):
            MOTIVO = 'El registro de MLflow no tiene versiones de retencion-90d.'
    except Exception as e:                               # noqa: BLE001
        MOTIVO = f'No se pudo abrir el registro de MLflow: {type(e).__name__}.'


def pytest_collection_modifyitems(config, items):
    if MOTIVO:
        for it in items:
            if 'cliente' in it.fixturenames or 'registro' in it.fixturenames:
                it.add_marker(pytest.mark.skip(reason=MOTIVO))


def _leer(c):
    return {'alias': {a: int(v) for a, v in (c.get_registered_model(NOMBRE).aliases or {}).items()},
            'tags': {int(v.version): dict(v.tags or {}) for v in c.search_model_versions(f"name='{NOMBRE}'")}}


def _restaurar(c, ini):
    ahora = _leer(c)
    for a in list(ahora['alias']):
        if a not in ini['alias']:
            c.delete_registered_model_alias(NOMBRE, a)
    for a, v in ini['alias'].items():
        if ahora['alias'].get(a) != v:
            c.set_registered_model_alias(NOMBRE, a, str(v))
    for v, tags in ahora['tags'].items():
        for k in tags:
            if k not in ini['tags'][v]:
                c.delete_model_version_tag(NOMBRE, str(v), k)
    for v, tags in ini['tags'].items():
        for k, val in tags.items():
            if ahora['tags'][v].get(k) != val:
                c.set_model_version_tag(NOMBRE, str(v), k, val)


@pytest.fixture(scope='session')
def registro():
    """Cliente MLflow + alias champion garantizado (lo pone solo si no existe) y restauración exacta al final."""
    c = modulo_app.alias_modelo.conectar()[1]
    inicial = _leer(c)
    ultima = max(inicial['tags'])
    if 'champion' not in inicial['alias']:
        modulo_app.alias_modelo.promover(c, ultima)
    yield c, inicial, ultima
    _restaurar(c, inicial)
    assert _leer(c) == inicial, 'El registro no quedó como se encontró'


@pytest.fixture(scope='module')
def cliente(registro):
    from fastapi.testclient import TestClient
    with TestClient(modulo_app.app) as c:
        yield c


@pytest.fixture
def llm_falso(cliente):
    """Inyecta un LLM de guion en la app; se quita al terminar."""
    def poner(guion, repetir=False):
        assert LLMFalso is not None, 'No se pudo importar LLMFalso del curso'
        falso = LLMFalso(guion, repetir=repetir)
        modulo_app.app.state.llm = falso
        return falso
    yield poner
    modulo_app.app.state.llm = None


def eventos(respuesta):
    return [json.loads(l[6:]) for l in respuesta.text.split('\n') if l.startswith('data: ')]
