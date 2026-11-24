"""Pruebas de nivel 2 del agente (S5): el PROTOCOLO. Un cliente MCP en Python arranca el servidor por stdio, lista sus herramientas y su
recurso y llama a algunas. Sin LLM.

Necesitan el paquete `mcp` (requirements-agente.txt): si no está instalado se omiten, y las de nivel 1 (test_agente_herramientas.py) siguen.
El servidor es un proceso aparte que lee la base, el modelo, la campaña y la referencia TEMPORALES de la fixture `entorno_agente`.
"""
import asyncio
import json
import os
import sqlite3
import sys

import pytest

mcp = pytest.importorskip('mcp', reason='falta el paquete «mcp»: pip install -r requirements-agente.txt (las pruebas de nivel 2 se omiten)')
from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402

from ia_mlops import config  # noqa: E402
from ia_mlops.agente import herramientas as h  # noqa: E402

RAIZ = config.RAIZ
HERRAMIENTAS = {'lista_del_dia', 'puntuar_online', 'puntuar_bajo_demanda', 'version_en_produccion', 'por_que'}
TIEMPO_MAXIMO = 180


def con_servidor(entorno_agente, escenario):
    """Arranca `python -m ia_mlops.agente.servidor_mcp` por stdio, abre una sesión MCP y ejecuta `escenario(sesion)`."""
    async def ejecutar():
        parametros = StdioServerParameters(command=sys.executable, args=['-m', 'ia_mlops.agente.servidor_mcp'], cwd=str(RAIZ),
                                           env={**os.environ, **entorno_agente.entorno})
        async with stdio_client(parametros) as (leer, escribir):
            async with ClientSession(leer, escribir) as sesion:
                await sesion.initialize()
                return await escenario(sesion)
    return asyncio.run(asyncio.wait_for(ejecutar(), TIEMPO_MAXIMO))


def datos(resultado):
    """El diccionario que devuelve una herramienta: viene como texto JSON en el contenido de la respuesta."""
    assert not resultado.isError, resultado.content
    return json.loads(resultado.content[0].text)


def un_cliente(entorno, desplazamiento=7):
    con = sqlite3.connect(entorno.ruta_db)
    try:
        return con.execute('SELECT cliente_id FROM fs_produccion ORDER BY cliente_id LIMIT 1 OFFSET ?', [desplazamiento]).fetchone()[0]
    finally:
        con.close()


def test_lista_las_cinco_herramientas_y_el_recurso(entorno_agente):
    async def escenario(sesion):
        return await sesion.list_tools(), await sesion.list_resources(), await sesion.read_resource('referencia://modelo')

    herramientas, recursos, ficha = con_servidor(entorno_agente, escenario)
    assert {t.name for t in herramientas.tools} == HERRAMIENTAS
    for t in herramientas.tools:
        assert t.description and len(t.description) > 40 and t.inputSchema['type'] == 'object'      # el LLM decide con esta descripción
    esquema = {t.name: t.inputSchema for t in herramientas.tools}
    assert 'cliente_id' in esquema['puntuar_online']['properties'] and 'cliente_id' in esquema['puntuar_online']['required']
    assert 'n' in esquema['lista_del_dia']['properties'] and not esquema['lista_del_dia'].get('required')
    assert not esquema['version_en_produccion'].get('properties')
    assert [str(r.uri) for r in recursos.resources] == ['referencia://modelo']
    assert json.loads(ficha.contents[0].text) == entorno_agente.referencia


def test_llama_a_dos_herramientas_y_da_lo_mismo_que_en_python(entorno_agente):
    cliente = un_cliente(entorno_agente)

    async def escenario(sesion):
        lista = await sesion.call_tool('lista_del_dia', {'n': 3})
        online = await sesion.call_tool('puntuar_online', {'cliente_id': cliente})
        version = await sesion.call_tool('version_en_produccion', {})
        return datos(lista), datos(online), datos(version)

    lista, online, version = con_servidor(entorno_agente, escenario)
    assert lista == h.lista_del_dia(3)
    local = h.puntuar_online(cliente)
    assert {k: v for k, v in online.items() if k != 'ms'} == {k: v for k, v in local.items() if k != 'ms'}
    assert version['version'] == entorno_agente.referencia['version'] and version == h.version_en_produccion()
    assert len(lista['clientes']) == 3


def test_un_error_de_la_herramienta_llega_como_dato_y_la_sesion_sigue(entorno_agente):
    async def escenario(sesion):
        inexistente = datos(await sesion.call_tool('puntuar_bajo_demanda', {'cliente_id': 99999999}))
        sigue = datos(await sesion.call_tool('por_que', {'cliente_id': un_cliente(entorno_agente), 'n': 2}))
        return inexistente, sigue

    inexistente, sigue = con_servidor(entorno_agente, escenario)
    assert 'fs_produccion' in inexistente['error']
    assert sigue['metodo'] == 'regresion_logistica_exacto' and len(sigue['variables_que_mas_pesan']) == 2
