"""Servidor MCP «mcp-retencion»: publica las herramientas de herramientas.py para que un LLM las use.

QUÉ ES MCP (Model Context Protocol)
    Un protocolo estándar para que un LLM use herramientas y lea datos de un servidor, sin que el LLM vea tu código ni tu base de datos.
    El servidor dice qué herramientas tiene (nombre, descripción y argumentos); el cliente (nuestro agente, VS Code...) las pide por nombre.

QUÉ HAY AQUÍ
    Cinco herramientas y un recurso. Este archivo NO tiene lógica: cada herramienta llama a la función del mismo nombre en
    herramientas.py (que es la que se prueba contra la API de S4). Lo único que se escribe aquí es la DESCRIPCIÓN: es lo que el LLM
    lee para decidir qué herramienta usar, así que es corta, en español y dice cuándo usarla y cuándo no.

        lista_del_dia(n)              a quién llamar hoy                         puntuar_online(cliente_id)     probabilidad con los datos de ahora
        puntuar_bajo_demanda(id)      probabilidad con los datos del último lote  por_que(cliente_id)           qué variables pesan en esa probabilidad
        version_en_produccion()       qué modelo hay publicado y desde cuándo     referencia://modelo (recurso)  la ficha del modelo en producción

    El servidor no devuelve nombres, correos ni teléfonos: el caso solo conoce el número de cliente y su país.

ARRANQUE (desde 04-Proyecto-Base, con el entorno de requirements-agente.txt):
    python -m ia_mlops.agente.servidor_mcp          # habla MCP por stdio: lo lanza el cliente, no se usa a mano
    Lee lo mismo que el resto del proyecto (CURSO_DB, CURSO_MODELOS, CURSO_REFERENCIA, CURSO_CAMPANA, CURSO_URL_API).
    Por stdio la salida estándar es el canal del protocolo: nada puede escribir en ella (los avisos van a stderr).
"""
import json
import sys

from mcp.server.fastmcp import FastMCP

from . import herramientas

NOMBRE = 'mcp-retencion'

servidor = FastMCP(NOMBRE, instructions=(
    'Herramientas del caso de retención: ¿qué clientes comprarán otra vez en los próximos 90 días? Todas las probabilidades son de '
    'VOLVER A COMPRAR: alta = buena noticia; no es un riesgo de abandono. Responde siempre con lo que devuelvan '
    'las herramientas; si una herramienta devuelve «error», díselo al usuario y no inventes datos. No hay nombres ni correos de clientes.'))


@servidor.tool(name='lista_del_dia', description=(
    'Lista de los n clientes con más probabilidad de la última campaña (de mayor a menor), con su tramo y la recomendación de negocio. '
    'Úsala cuando pregunten a quién llamar hoy o quiénes son los mejores clientes. n por defecto 10, máximo 100.'))
def lista_del_dia(n: int = 10) -> dict:
    return herramientas.lista_del_dia(n)


@servidor.tool(name='puntuar_online', description=(
    'Probabilidad de que UN cliente compre en los próximos 90 días, calculada ahora con sus datos más recientes (incluida su última compra). '
    'Úsala si preguntan por un cliente concreto o si acaba de comprar. Argumento: cliente_id (número). corte (AAAA-MM-DD) solo para comparar '
    'con otra fecha: normalmente no se pone.'))
def puntuar_online(cliente_id: int, corte: str | None = None) -> dict:
    return herramientas.puntuar_online(cliente_id, corte)


@servidor.tool(name='puntuar_bajo_demanda', description=(
    'Probabilidad de que UN cliente compre en los próximos 90 días con los datos del último lote (los de ayer, sin su última compra). '
    'Úsala para ver el valor «oficial» del lote o para comparar con puntuar_online. Argumento: cliente_id (número).'))
def puntuar_bajo_demanda(cliente_id: int) -> dict:
    return herramientas.puntuar_bajo_demanda(cliente_id)


@servidor.tool(name='version_en_produccion', description=(
    'Qué versión del modelo está en producción, desde cuándo, con qué métricas se aprobó y el historial de versiones. '
    'Úsala si preguntan qué modelo se usa, desde cuándo o qué tan fiable es. No necesita argumentos.'))
def version_en_produccion() -> dict:
    return herramientas.version_en_produccion()


@servidor.tool(name='por_que', description=(
    'Las variables que más empujan la probabilidad de UN cliente, hacia arriba o hacia abajo, con su valor real. '
    'Úsala cuando pregunten por qué un cliente sale alto o bajo. Argumentos: cliente_id (número) y n (cuántas variables, por defecto 5).'))
def por_que(cliente_id: int, n: int = 5) -> dict:
    return herramientas.por_que(cliente_id, n)


@servidor.resource('referencia://modelo', name='referencia_modelo', mime_type='application/json', description=(
    'La ficha de la versión del modelo en producción (models/referencia.json): versión, huella de los datos, métricas y fechas.'))
def referencia_modelo() -> str:
    return json.dumps(herramientas.referencia_del_modelo(), ensure_ascii=False, indent=2)


def main():
    motivo = herramientas.precargar()          # antes de abrir stdio (ver precargar); por stderr, que no es el canal del protocolo
    if motivo:
        print(f'{NOMBRE}: aviso al arrancar, las herramientas responderán con error hasta que exista el modelo: {motivo}', file=sys.stderr)
    servidor.run(transport='stdio')


if __name__ == '__main__':
    main()
