"""La «caja de herramientas» del agente: lo único que el bucle necesita saber de las herramientas.

    caja.listar()                 -> lista de herramientas en formato OpenAI: {"type": "function", "function": {name, description, parameters}}
    caja.llamar(nombre, args)     -> el resultado (un diccionario o un texto); si falla, lanza una excepción

Dos implementaciones, intercambiables:
    CajaEnMemoria   funciones de Python normales. Para pruebas y para usar herramientas.py sin servidor.
    CajaMCP         se conecta por stdio al servidor MCP (python -m ia_mlops.agente.servidor_mcp) y usa sus herramientas.

El agente no sabe cuál de las dos tiene delante: por eso las pruebas con funciones en memoria valen para el MCP real.
"""
import asyncio
import inspect
import os
import sys
import threading
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]            # 04-Proyecto-Base
_TIPOS_JSON = {int: 'integer', float: 'number', str: 'string', bool: 'boolean', list: 'array', dict: 'object'}


class CajaEnMemoria:
    """Herramientas = funciones de Python. El esquema sale de la firma: tipos por las anotaciones, obligatorio si no hay valor por defecto."""

    def __init__(self, funciones, esquemas=None):
        self.funciones, self.esquemas = dict(funciones), esquemas or {}

    def listar(self):
        tools = []
        for nombre, f in self.funciones.items():
            params = inspect.signature(f).parameters
            props = {p: {'type': _TIPOS_JSON.get(a.annotation, 'string')} for p, a in params.items()}
            esquema = self.esquemas.get(nombre) or {'type': 'object', 'properties': props,
                                                    'required': [p for p, a in params.items() if a.default is a.empty]}
            tools.append({'type': 'function', 'function': {'name': nombre, 'description': inspect.getdoc(f) or nombre, 'parameters': esquema}})
        return tools

    def llamar(self, nombre, args):
        return self.funciones[nombre](**args)


class CajaMCP:
    """Cliente MCP por stdio. Arranca el servidor como proceso hijo y mantiene UNA sesión abierta mientras dura el `with`.

    El SDK de MCP es asíncrono y el agente no. Se concilian con un hilo que vive dentro del `with` y ejecuta la sesión
    (conectar → esperar → desconectar, todo en la misma tarea, como exige anyio); los métodos de la caja le piden cosas y esperan.
    """

    def __init__(self, comando=None, cwd=RAIZ, env=None, timeout=180):
        self.comando = comando or [sys.executable, '-m', 'ia_mlops.agente.servidor_mcp']
        self.cwd, self.env, self.timeout = str(cwd), env, timeout
        self._listo, self._error, self._sesion = threading.Event(), None, None

    # ------------------------------------------------------------------ sesión
    async def _vida(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        self._parar = asyncio.Event()
        try:
            params = StdioServerParameters(command=self.comando[0], args=self.comando[1:], cwd=self.cwd,
                                           env=self.env or dict(os.environ))       # sin env, stdio_client no pasa CURSO_DB y compañía
            async with stdio_client(params) as (leer, escribir):
                async with ClientSession(leer, escribir) as sesion:
                    await sesion.initialize()
                    self._sesion = sesion
                    self._listo.set()
                    await self._parar.wait()
        except BaseException as e:                                                # noqa: BLE001 - se lo contamos a quien espera
            self._error = e
        finally:
            self._listo.set()

    def __enter__(self):
        self._bucle = asyncio.new_event_loop()
        threading.Thread(target=self._bucle.run_forever, daemon=True).start()
        self._vida_futuro = asyncio.run_coroutine_threadsafe(self._vida(), self._bucle)
        if not self._listo.wait(self.timeout) or self._error:
            self.__exit__()
            raise RuntimeError(f'No se pudo conectar con el servidor MCP: {self._error or "tiempo agotado"}')
        return self

    def __exit__(self, *_):
        if hasattr(self, '_parar'):
            self._bucle.call_soon_threadsafe(self._parar.set)
        try:
            self._vida_futuro.result(timeout=30)
        except Exception:                                                         # noqa: BLE001
            pass
        self._bucle.call_soon_threadsafe(self._bucle.stop)

    def _pedir(self, corrutina):
        return asyncio.run_coroutine_threadsafe(corrutina, self._bucle).result(timeout=self.timeout)

    # ------------------------------------------------------------------ la interfaz de la caja
    def listar(self):
        herramientas = self._pedir(self._sesion.list_tools()).tools
        return [{'type': 'function', 'function': {
            'name': t.name, 'description': t.description or t.name,
            'parameters': getattr(t, 'inputSchema', None) or t.input_schema}} for t in herramientas]      # mcp 1.x: camelCase; 2.x: snake_case

    def llamar(self, nombre, args):
        res = self._pedir(self._sesion.call_tool(nombre, args))
        texto = '\n'.join(c.text for c in res.content if hasattr(c, 'text'))
        if getattr(res, 'isError', getattr(res, 'is_error', False)):
            raise RuntimeError(texto or 'el servidor MCP devolvió un error')
        estructurado = getattr(res, 'structuredContent', None) or getattr(res, 'structured_content', None)
        return estructurado if estructurado is not None else texto
