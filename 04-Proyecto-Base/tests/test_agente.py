"""Pruebas de nivel 3 del agente: el bucle, con un LLM falso de guion y herramientas en memoria. Sin red, sin Ollama, sin servidor MCP."""
import importlib.util
import json
import os

import pytest

os.environ.setdefault('MLFLOW_ENABLE_ASYNC_TRACE_LOGGING', 'false')      # la traza queda escrita al terminar el span (ver informe del pico)

from ia_mlops.agente.agente import Agente                                  # noqa: E402
from ia_mlops.agente.cajas import CajaEnMemoria                            # noqa: E402
from ia_mlops.agente.llm import LLMFalso                                   # noqa: E402


def lista_del_dia(n: int = 5):
    """Los n clientes con más probabilidad."""
    return {'clientes': [{'cliente_id': 12670 + i, 'probabilidad': round(0.9 - 0.1 * i, 2)} for i in range(n)]}


def version_en_produccion():
    """Versión del modelo en producción."""
    return {'version': 'v7'}


def puntuar_online(cliente_id: int):
    """Probabilidad de un cliente."""
    if cliente_id == 0:
        raise KeyError('cliente 0 no existe')
    return {'cliente_id': cliente_id, 'probabilidad': 0.8}


@pytest.fixture
def caja():
    return CajaEnMemoria({f.__name__: f for f in (lista_del_dia, version_en_produccion, puntuar_online)})


def mensajes_tool(llm, turno):
    """Los mensajes de rol «tool» que el LLM falso recibió en el turno indicado (0 = primero)."""
    return [m for m in llm.llamadas[turno]['mensajes'] if m['role'] == 'tool']


def test_una_herramienta_y_respuesta_final(caja):
    llm = LLMFalso([('lista_del_dia', {'n': 2}), 'Llama a 12670 y 12671.'])
    r = Agente(llm, caja).ejecutar('Dame 2 clientes')
    assert r.texto == 'Llama a 12670 y 12671.'
    assert r.herramientas == ['lista_del_dia'] and r.pasos == 2 and r.terminado
    observado = json.loads(mensajes_tool(llm, 1)[0]['content'])           # el LLM vio el resultado real de la herramienta
    assert [c['cliente_id'] for c in observado['clientes']] == [12670, 12671]


def test_el_llm_recibe_las_herramientas_de_la_caja(caja):
    llm = LLMFalso(['hola'])
    Agente(llm, caja).ejecutar('hola')
    nombres = [t['function']['name'] for t in llm.llamadas[0]['tools']]
    assert nombres == ['lista_del_dia', 'version_en_produccion', 'puntuar_online']
    assert llm.llamadas[0]['tools'][2]['function']['parameters']['required'] == ['cliente_id']


def test_varios_pasos_y_varias_llamadas_en_un_turno(caja):
    llm = LLMFalso([[('version_en_produccion', {}), ('puntuar_online', {'cliente_id': 12670})], ('lista_del_dia', {'n': 1}), 'listo'])
    r = Agente(llm, caja).ejecutar('todo')
    assert r.herramientas == ['version_en_produccion', 'puntuar_online', 'lista_del_dia'] and r.pasos == 3
    assert len(mensajes_tool(llm, 1)) == 2 and len(mensajes_tool(llm, 2)) == 3     # el historial crece


def test_error_de_herramienta_vuelve_al_llm_sin_romper(caja):
    llm = LLMFalso([('puntuar_online', {'cliente_id': 0}), 'No tengo datos de ese cliente.'])
    r = Agente(llm, caja).ejecutar('puntúa al 0')
    assert r.texto == 'No tengo datos de ese cliente.' and r.terminado
    assert 'KeyError' in json.loads(mensajes_tool(llm, 1)[0]['content'])['error']


def test_herramienta_desconocida_se_rechaza(caja):
    llm = LLMFalso([('borrar_todo', {}), 'No puedo hacer eso.'])
    r = Agente(llm, caja).ejecutar('borra todo')
    assert r.herramientas == []                                               # no se ejecutó nada
    error = json.loads(mensajes_tool(llm, 1)[0]['content'])['error']
    assert 'desconocida' in error and 'lista_del_dia' in error                # y el LLM sabe cuáles hay


@pytest.mark.parametrize('args, motivo', [
    ({}, 'obligatorio'),
    ({'cliente_id': 'doce'}, 'tipo integer'),
    ({'cliente_id': True}, 'tipo integer'),
    ({'cliente_id': 1, 'extra': 2}, 'desconocido'),
])
def test_argumentos_invalidos_se_rechazan(caja, args, motivo):
    llm = LLMFalso([('puntuar_online', args), 'vale'])
    r = Agente(llm, caja).ejecutar('x')
    assert r.herramientas == []
    assert motivo in json.loads(mensajes_tool(llm, 1)[0]['content'])['error']


def test_argumentos_que_no_son_json_se_rechazan(caja):
    mensaje = {'role': 'assistant', 'content': None, 'tool_calls': [
        {'id': 'x', 'type': 'function', 'function': {'name': 'puntuar_online', 'arguments': '{no es json'}}]}
    llm = LLMFalso([mensaje, 'vale'])
    r = Agente(llm, caja).ejecutar('x')
    assert r.herramientas == [] and 'JSONDecodeError' in json.loads(mensajes_tool(llm, 1)[0]['content'])['error']


def test_limite_de_pasos(caja):
    llm = LLMFalso([('version_en_produccion', {})], repetir=True)             # nunca contesta: siempre pide otra herramienta
    r = Agente(llm, caja, max_pasos=3).ejecutar('x')
    assert not r.terminado and r.pasos == 3 and len(llm.llamadas) == 3 and len(r.herramientas) == 3
    assert '3 pasos' in r.texto


def test_observaciones_largas_se_recortan(caja):
    llm = LLMFalso([('lista_del_dia', {'n': 50}), 'ok'])
    Agente(llm, caja, max_observacion=100).ejecutar('x')
    contenido = mensajes_tool(llm, 1)[0]['content']
    assert contenido.endswith('[recortado]') and len(contenido) < 130


def test_si_el_guion_se_acaba_se_dice():
    with pytest.raises(RuntimeError, match='guion'):
        Agente(LLMFalso([]), CajaEnMemoria({})).ejecutar('x')


def test_se_registra_una_traza_en_mlflow(caja, tmp_path):
    import mlflow
    anterior = mlflow.get_tracking_uri()
    mlflow.set_tracking_uri(f'sqlite:///{(tmp_path / "mlflow.db").as_posix()}')
    try:
        mlflow.set_experiment('prueba-agente')
        llm = LLMFalso([('lista_del_dia', {'n': 1}), 'Hecho.'])
        Agente(llm, caja, trazas=True).ejecutar('Dame 1 cliente')
        trazas = mlflow.search_traces(return_type='list')
        assert len(trazas) == 1
        spans = {s.name: s for s in trazas[0].data.spans}
        assert {'agente', 'paso_1', 'paso_2', 'lista_del_dia'} <= set(spans)
        assert spans['lista_del_dia'].span_type == 'TOOL' and spans['agente'].span_type == 'AGENT'
    finally:
        mlflow.set_tracking_uri(anterior)


# ---------------------------------------------------------------------------------------------- con el servidor MCP real (nivel 2 + 3)
def _hay_servidor_mcp():
    return importlib.util.find_spec('mcp') is not None and importlib.util.find_spec('ia_mlops.agente.servidor_mcp') is not None


@pytest.mark.skipif(not _hay_servidor_mcp(), reason='falta el paquete mcp o el servidor ia_mlops.agente.servidor_mcp')
def test_la_caja_mcp_lista_y_llama(ruta_db, monkeypatch):
    from ia_mlops.agente.cajas import CajaMCP
    monkeypatch.setenv('CURSO_DB', str(ruta_db))
    with CajaMCP() as caja:
        nombres = {t['function']['name'] for t in caja.listar()}
        assert {'lista_del_dia', 'puntuar_online', 'puntuar_bajo_demanda', 'version_en_produccion', 'por_que'} <= nombres
        llm = LLMFalso([('version_en_produccion', {}), 'Listo.'])
        r = Agente(llm, caja).ejecutar('¿qué versión hay?')
    assert r.herramientas == ['version_en_produccion'] and mensajes_tool(llm, 1)
