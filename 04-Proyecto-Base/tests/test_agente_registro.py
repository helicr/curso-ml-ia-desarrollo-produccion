"""Pruebas del registro del agente en MLflow (S5·T04): prompt con alias, agente «models from code» con alias `champion`, rollback y CLI.

MLflow escribe en una base SQLite de una carpeta temporal (nunca en models/mlflow.db). Sin red y sin Ollama: al cargar el agente se le cambia el
LLM por uno falso y el servidor MCP por funciones en memoria.
"""
import os

import pytest

os.environ.setdefault('MLFLOW_ENABLE_ASYNC_TRACE_LOGGING', 'false')

import mlflow                                                              # noqa: E402
import pandas as pd                                                        # noqa: E402

from ia_mlops.agente import agente, registro                               # noqa: E402
from ia_mlops.agente.cajas import CajaEnMemoria                            # noqa: E402
from ia_mlops.agente.llm import LLMFalso                                   # noqa: E402


@pytest.fixture(scope='module')
def uri(tmp_path_factory):
    """Un almacén de MLflow temporal para todo el módulo; al terminar se devuelve MLflow a donde estaba."""
    previo = mlflow.get_tracking_uri()
    u = 'sqlite:///' + (tmp_path_factory.mktemp('mlflow') / 'mlflow.db').as_posix()
    registro.conectar(u)
    yield u
    mlflow.set_tracking_uri(previo)


def test_el_almacen_por_defecto_es_el_del_curso(monkeypatch):
    monkeypatch.delenv('CURSO_MLFLOW_URI', raising=False)
    assert registro.uri_por_defecto().startswith('sqlite:///') and registro.uri_por_defecto().endswith('models/mlflow.db')
    monkeypatch.setenv('CURSO_MLFLOW_URI', 'sqlite:///otro.db')
    assert registro.uri_por_defecto() == 'sqlite:///otro.db'


def test_registrar_el_prompt_y_mover_su_alias(uri):
    r1 = registro.registrar_prompt()
    assert r1 == {'nombre': 'agente-retencion-sistema', 'version': 1, 'alias': 'produccion', 'creada': True}
    assert registro.texto_del_prompt() == agente.SISTEMA                       # lo que carga el alias es el prompt del agente, con sus tildes
    assert registro.registrar_prompt()['creada'] is False                      # idempotente: el mismo texto no crea otra versión
    r2 = registro.registrar_prompt(agente.SISTEMA + ' Sé breve.')
    assert r2['version'] == 2 and r2['creada'] and registro.texto_del_prompt().endswith('Sé breve.')
    registro.mover_alias('prompt', 1)                                          # rollback del prompt
    assert registro.texto_del_prompt() == agente.SISTEMA and registro.texto_del_prompt(version=2).endswith('Sé breve.')
    with pytest.raises(registro.ErrorRegistro):
        registro.mover_alias('prompt', 99)
    with pytest.raises(registro.ErrorRegistro, match='ni «prompt» ni «agente»'):
        registro.mover_alias('otra', 1)


def test_la_huella_cambia_con_el_prompt_el_modelo_y_las_skills():
    s = {'a': {'descripcion': 'd', 'activar_si': [], 'cuerpo': 'c'}}
    base = registro.huella_agente('prompt', 'modelo', s)
    assert registro.huella_agente('prompt', 'modelo', s) == base
    assert registro.huella_agente('prompt 2', 'modelo', s) != base and registro.huella_agente('prompt', 'otro', s) != base
    assert registro.huella_agente('prompt', 'modelo', {'a': {**s['a'], 'cuerpo': 'c2'}}) != base
    assert registro.huella_agente('prompt', 'modelo', {}) != base


def test_registrar_el_agente_con_su_configuracion_y_cargarlo_por_el_alias(uri):
    registro.registrar_prompt()
    registro.mover_alias('prompt', 1)
    r = registro.registrar_agente(llm_modelo='modelo-de-prueba', llm_url='http://127.0.0.1:1/v1')
    assert r['nombre'] == 'agente-retencion' and r['version'] == 1 and r['alias'] == 'champion'
    cfg = r['configuracion']
    assert cfg['llm_modelo'] == 'modelo-de-prueba' and cfg['prompt_version'] == 1 and cfg['prompt_nombre'] == 'agente-retencion-sistema'
    assert cfg['skills'] == ['cumplimiento', 'guion-de-llamada', 'informe-semanal'] and cfg['mcp_version'] and cfg['huella']
    assert registro.configuracion_registrada() == cfg                           # lo que se registró es lo que se lee del alias
    run = mlflow.get_run(r['run_id'])
    assert run.data.tags['huella_agente'] == cfg['huella']

    modelo = registro.cargar_agente()                                           # models:/agente-retencion@champion
    interno = modelo.unwrap_python_model()
    assert interno.config['llm_modelo'] == 'modelo-de-prueba' and interno.sistema == agente.SISTEMA and set(interno.skills) == set(cfg['skills'])

    # predict, con un LLM falso y herramientas en memoria (sin Ollama, sin servidor MCP)
    def version_en_produccion():
        """Versión del modelo."""
        return {'version': 7}
    llms = []
    interno.fabrica_llm = lambda: llms.append(LLMFalso([('version_en_produccion', {}), 'Está la versión 7.'])) or llms[-1]
    interno.fabrica_caja = lambda: CajaEnMemoria({'version_en_produccion': version_en_produccion})
    salida = modelo.predict(pd.DataFrame({'pregunta': ['¿Qué versión hay?', '¿Y ahora?']}))
    assert list(salida) == ['Está la versión 7.', 'Está la versión 7.']
    assert llms[0].llamadas[0]['mensajes'][0]['content'].startswith(agente.SISTEMA)    # el prompt de sistema salió del registro


def test_cambiar_el_alias_champion_y_volver_atras(uri):
    # (el prompt v2, con «Sé breve.», ya se registró en el primer test)
    v2 = registro.registrar_agente(llm_modelo='otro-modelo', version_prompt=2, alias=None)['version']   # sin mover el alias
    assert v2 == 2
    estado = {v['version']: v['alias'] for v in registro.estado()['agente']['versiones']}
    assert estado == {1: ['champion'], 2: []}
    registro.mover_alias('agente', 2)                                           # promocionar
    assert registro.configuracion_registrada()['llm_modelo'] == 'otro-modelo' and registro.configuracion_registrada()['prompt_version'] == 2
    registro.mover_alias('agente', 1)                                           # rollback: nada se borra, solo se mueve el puntero
    assert registro.configuracion_registrada()['llm_modelo'] == 'modelo-de-prueba'
    assert {v['version']: v['alias'] for v in registro.estado()['agente']['versiones']} == {1: ['champion'], 2: []}
    with pytest.raises(registro.ErrorRegistro, match='No existe la versión 9'):
        registro.mover_alias('agente', 9)


def test_el_agente_registrado_fija_la_version_del_prompt(uri):
    """Mover el alias del prompt NO cambia un agente ya registrado: su configuración lleva la versión fija."""
    registro.mover_alias('prompt', 1)
    modelo = registro.cargar_agente(version=2)
    assert modelo.unwrap_python_model().sistema.endswith('Sé breve.')
    registro.mover_alias('prompt', 1)
    assert registro.cargar_agente(version=2).unwrap_python_model().sistema.endswith('Sé breve.')


def test_sin_prompt_registrado_el_agente_no_se_registra(tmp_path):
    previo = mlflow.get_tracking_uri()
    try:
        registro.conectar('sqlite:///' + (tmp_path / 'vacio.db').as_posix())
        with pytest.raises(registro.ErrorRegistro, match='registrar-prompt'):
            registro.registrar_agente()
    finally:
        mlflow.set_tracking_uri(previo)


def test_cli(tmp_path, capsys):
    previo = mlflow.get_tracking_uri()
    u = 'sqlite:///' + (tmp_path / 'cli.db').as_posix()
    try:
        assert registro.main(['--uri', u, 'mostrar']) == 0
        assert 'sin registrar' in capsys.readouterr().out
        assert registro.main(['--uri', u, 'registrar-prompt']) == 0
        assert 'v1 → @produccion' in capsys.readouterr().out
        assert registro.main(['--uri', u, 'registrar-prompt']) == 0
        assert 'Sin cambios' in capsys.readouterr().out
        assert registro.main(['--uri', u, 'registrar-agente', '--llm-modelo', 'm1']) == 0
        assert 'agente-retencion v1 → @champion' in capsys.readouterr().out
        assert registro.main(['--uri', u, 'registrar-agente', '--llm-modelo', 'm2', '--sin-alias']) == 0
        assert registro.main(['--uri', u, 'alias', 'agente', '--version', '2']) == 0
        assert 'agente-retencion@champion → v2' in capsys.readouterr().out
        assert registro.main(['--uri', u, 'mostrar']) == 0
        salida = capsys.readouterr().out
        assert '@produccion → v1' in salida and 'v2  alias: @champion' in salida
        assert registro.main(['--uri', u, 'alias', 'agente', '--version', '9']) == 2
        assert 'No existe la versión 9' in capsys.readouterr().err
    finally:
        mlflow.set_tracking_uri(previo)
