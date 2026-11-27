"""Interfaz del extra de S5: una página web que une los DOS servidores MCP (datos y modelo) con un LLM.

    python -m uvicorn app:app --port 8095        (o:  python app.py)      solo escucha en 127.0.0.1

El «Puente» arranca los dos servidores de ..\\fuentes\\ como procesos hijos (transporte stdio) y mantiene sus sesiones vivas
mientras dure la app. Cada llamada a una herramienta, venga de un clic, del explorador o del LLM, queda en una TRAZA en memoria.

Variables de entorno (todas opcionales):
    MCP_PROYECTO       carpeta 04-Proyecto-Base (por defecto, la del curso, dos carpetas por encima de S5)
    CURSO_DB           curso.db (por defecto, la de 04-Proyecto-Base)
    CURSO_MLFLOW_URI   almacén de MLflow (por defecto, models/mlflow.db de 04-Proyecto-Base)
    CURSO_LLM_URL      base OpenAI-compatible del LLM   (por defecto http://127.0.0.1:11434/v1)
    CURSO_LLM_MODELO   nombre del modelo                (por defecto qwen2.5:0.5b)
    GCP_PROJECT, BQ_DATASET   solo para el modo BigQuery (opcional)
    CURSO_UI_HOSTS     nombres de host extra admitidos, separados por comas (p. ej. *.app.github.dev en un Codespace)
"""
import asyncio
import getpass
import json
import os
import re
import sqlite3
import sys
import time
from collections import deque
from contextlib import AsyncExitStack, asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path

import anyio
import httpx
import jsonschema
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import BaseModel, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

os.environ.setdefault('MLFLOW_DISABLE_AGENT_HINT', '1')

AQUI = Path(__file__).resolve().parent
EXTRA = AQUI.parent
FUENTES = EXTRA / 'fuentes'
PROYECTO = Path(os.environ.get('MCP_PROYECTO') or EXTRA.parents[2] / '04-Proyecto-Base')
CURSO_DB = Path(os.environ.get('CURSO_DB') or PROYECTO / 'data' / 'processed' / 'curso.db')
TRABAJO = AQUI / '_trabajo'
LLM_URL_DEFECTO = 'http://127.0.0.1:11434/v1'
LLM_MODELO_DEFECTO = 'qwen2.5:0.5b'
MAX_PASOS = 5
MAX_TRAZA = 500
NOMBRES = {'datos': 'mcp-datos-master', 'modelo': 'mcp-modelo-retencion'}

os.environ['MCP_PROYECTO'] = str(PROYECTO)
os.environ['CURSO_DB'] = str(CURSO_DB)
if str(PROYECTO) not in sys.path:
    sys.path.insert(0, str(PROYECTO))
try:                                                     # el registro de modelos del curso (promover / volver / estado)
    from ia_mlops import alias_modelo, config as cfg_curso
except Exception:                                        # noqa: BLE001 - la UI arranca igualmente y lo dice en /api/estado
    alias_modelo = cfg_curso = None


# ------------------------------------------------------------------------------------------------ limpieza de rutas y secretos
def _prefijos_privados():
    cosas = {str(PROYECTO), PROYECTO.as_posix(), str(EXTRA), EXTRA.as_posix(), str(Path.home()), Path.home().as_posix(), str(AQUI), AQUI.as_posix()}
    try:
        usuario = getpass.getuser()
        if len(usuario) >= 3:
            cosas.add(usuario)
    except Exception:                                    # noqa: BLE001
        pass
    return sorted((c for c in cosas if c), key=len, reverse=True)


_PRIVADOS = _prefijos_privados()


def limpiar(obj):
    """Quita de cualquier cosa que salga hacia el navegador las rutas de esta máquina y el nombre del usuario."""
    if isinstance(obj, str):
        for p in _PRIVADOS:
            obj = obj.replace(p, '…')
        return obj
    if isinstance(obj, dict):
        return {k: limpiar(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [limpiar(v) for v in obj]
    return obj


def respuesta(obj, estado=200):
    return JSONResponse(limpiar(obj), status_code=estado)


# ------------------------------------------------------------------------------------------------ validación de argumentos
def _tipo_es(t):
    return {'integer': 'un número entero', 'number': 'un número', 'string': 'un texto', 'object': 'un objeto', 'array': 'una lista', 'boolean': 'verdadero o falso'}.get(t, t)


def preparar_argumentos(argumentos, esquema):
    """Convierte «12369» (texto) en 12369 cuando el esquema pide un número y valida. Devuelve (argumentos, avisos, error)."""
    if not isinstance(argumentos, dict):
        return None, [], 'Los argumentos deben ser un objeto JSON, por ejemplo {"cliente_id": 12369}.'
    props = (esquema or {}).get('properties', {})
    salida, avisos = dict(argumentos), []
    for k, v in argumentos.items():
        t = props.get(k, {}).get('type')
        if t in ('integer', 'number') and isinstance(v, str):
            try:
                salida[k] = int(v) if t == 'integer' else float(v)
                avisos.append(f'«{k}» llegó como texto y se pasó a número.')
            except ValueError:
                pass
        elif t == 'integer' and isinstance(v, float) and v.is_integer():
            salida[k] = int(v)
    errores = sorted(jsonschema.Draft202012Validator(esquema or {}).iter_errors(salida), key=lambda e: list(e.path))
    if errores:
        e = errores[0]
        campo = '.'.join(str(p) for p in e.path)
        if e.validator == 'required':
            falta = re.findall(r"'([^']+)'", e.message)
            return None, avisos, f'Falta el argumento «{falta[0] if falta else "?"}».'
        if e.validator == 'type':
            return None, avisos, f'«{campo}» debe ser {_tipo_es(e.validator_value if isinstance(e.validator_value, str) else "otro tipo")}, no «{e.instance}».'
        if e.validator == 'additionalProperties':
            return None, avisos, f'Argumento no reconocido: {e.message}'
        return None, avisos, f'Argumento no válido «{campo}»: {e.message}'
    return salida, avisos, None


def sin_titulos(esquema):
    """Quita los «title» autogenerados del esquema: ahorra tokens a un modelo pequeño."""
    if isinstance(esquema, dict):
        return {k: sin_titulos(v) for k, v in esquema.items() if k != 'title'}
    if isinstance(esquema, list):
        return [sin_titulos(v) for v in esquema]
    return esquema


# ------------------------------------------------------------------------------------------------ un servidor MCP vivo
class Servidor:
    """Un servidor MCP como proceso hijo. Abre y cierra la sesión en la MISMA tarea de fondo (lo exige anyio)."""

    def __init__(self, clave, script, entorno):
        self.clave, self.script, self.entorno = clave, Path(script), entorno
        self.sesion, self.herramientas, self.error = None, [], None
        self._tarea = self._parar = None

    @property
    def vivo(self):
        return self.sesion is not None and self._tarea is not None and not self._tarea.done()

    async def iniciar(self, script=None, entorno_extra=None):
        if script:
            self.script = Path(script)
        TRABAJO.mkdir(exist_ok=True)
        loop = asyncio.get_running_loop()
        self._parar, listo = asyncio.Event(), loop.create_future()
        self.error = None
        self._tarea = asyncio.create_task(self._vida(listo, dict(entorno_extra or {})))
        try:
            await asyncio.wait_for(asyncio.shield(listo), 90)
        except BaseException as e:                       # noqa: BLE001
            self.error = self.error or f'{type(e).__name__}: {e}'.strip(': ')
            await self.parar()
            raise

    async def _vida(self, listo, extra):
        try:
            async with AsyncExitStack() as pila:
                log = open(TRABAJO / f'{self.clave}.err', 'w', encoding='utf-8')     # lo que el servidor escribe por stderr
                pila.callback(log.close)
                entorno = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONIOENCODING': 'utf-8', **self.entorno(), **extra}
                params = StdioServerParameters(command=sys.executable, args=[str(self.script)], env=entorno, cwd=str(FUENTES))
                leer, escribir = await pila.enter_async_context(stdio_client(params, errlog=log))
                sesion = await pila.enter_async_context(ClientSession(leer, escribir, read_timeout_seconds=timedelta(seconds=180)))
                with anyio.fail_after(60):
                    await sesion.initialize()
                herramientas = (await sesion.list_tools()).tools
                self.herramientas = [{'nombre': t.name, 'descripcion': t.description or '', 'inputSchema': t.inputSchema} for t in herramientas]
                self.sesion = sesion
                if not listo.done():
                    listo.set_result(True)
                await self._parar.wait()
        except BaseException as e:                       # noqa: BLE001 - se cuenta, no revienta la app
            self.error = f'{type(e).__name__}: {str(e)[:300]}' if str(e) else type(e).__name__
            if not listo.done():
                listo.set_exception(RuntimeError(self.detalle_arranque() or self.error))
            if isinstance(e, (asyncio.CancelledError, KeyboardInterrupt)):
                raise
        finally:
            self.sesion = None
            if not listo.done():
                listo.set_exception(RuntimeError('El servidor se cerró al arrancar.'))
            listo.exception() if listo.done() and not listo.cancelled() else None    # evita «exception never retrieved»

    def detalle_arranque(self):
        """Última línea útil del stderr del servidor (por qué no arrancó)."""
        try:
            lineas = [l.strip() for l in (TRABAJO / f'{self.clave}.err').read_text(encoding='utf-8', errors='replace').splitlines() if l.strip()]
            return lineas[-1][:300] if lineas else ''
        except OSError:
            return ''

    async def parar(self):
        if self._parar is not None:
            self._parar.set()
        if self._tarea is not None:
            try:
                await asyncio.wait_for(asyncio.shield(self._tarea), 20)
            except BaseException:                        # noqa: BLE001
                pass
        self.sesion = None


class Puente:
    """Los dos servidores, su traza y las llamadas a herramientas."""

    def __init__(self):
        proy = {'MCP_PROYECTO': str(PROYECTO), 'CURSO_DB': str(CURSO_DB)}
        if os.environ.get('CURSO_MLFLOW_URI'):
            proy['CURSO_MLFLOW_URI'] = os.environ['CURSO_MLFLOW_URI']
        self.backend, self.bq_proyecto, self.bq_dataset = 'sqlite', None, None
        self.script_bq = None                            # solo pruebas: un servidor falso para el modo BigQuery
        self.servidores = {
            'datos': Servidor('datos', FUENTES / 'mcp_datos.py', lambda: {**proy, 'MCP_BACKEND': self.backend, **(
                {'GCP_PROJECT': self.bq_proyecto, 'BQ_DATASET': self.bq_dataset} if self.backend == 'bigquery' else {})}),
            'modelo': Servidor('modelo', FUENTES / 'mcp_modelo.py', lambda: dict(proy)),
        }
        self.traza = deque(maxlen=MAX_TRAZA)
        self._n = 0
        self.candado_backend = asyncio.Lock()

    async def arrancar(self):
        resultados = await asyncio.gather(*(s.iniciar() for s in self.servidores.values()), return_exceptions=True)
        for s, r in zip(self.servidores.values(), resultados):
            if isinstance(r, BaseException):
                s.error = s.detalle_arranque() or s.error or str(r)

    async def parar(self):
        await asyncio.gather(*(s.parar() for s in self.servidores.values()))

    def servidor_de(self, herramienta):
        for s in self.servidores.values():
            if any(h['nombre'] == herramienta for h in s.herramientas):
                return s
        return None

    def todas(self):
        return [{**h, 'servidor': s.clave, 'servidor_nombre': NOMBRES[s.clave]} for s in self.servidores.values() for h in s.herramientas]

    def apuntar(self, **datos):
        self._n += 1
        reg = {'id': self._n, 'hora': datetime.now().strftime('%H:%M:%S'), **datos}
        self.traza.append(reg)
        return reg

    async def llamar(self, herramienta, argumentos=None, origen='ui', registrar=True):
        """Llama a una herramienta de cualquiera de los dos servidores. NUNCA lanza: devuelve {'ok', 'resultado', 'ms', ...}."""
        t0 = time.perf_counter()
        srv = self.servidor_de(herramienta)
        argumentos = argumentos if argumentos is not None else {}
        avisos = []
        if srv is None:
            resultado = {'error': f'La herramienta «{herramienta}» no existe. Las disponibles: {", ".join(h["nombre"] for h in self.todas())}.'}
            clave = None
        else:
            clave = srv.clave
            esquema = next(h['inputSchema'] for h in srv.herramientas if h['nombre'] == herramienta)
            argumentos, avisos, motivo = preparar_argumentos(argumentos, esquema)
            if motivo:
                resultado = {'error': f'Argumentos no válidos para {herramienta}: {motivo}'}
                argumentos = None
            else:
                resultado = await self._invocar(srv, herramienta, argumentos)
        ms = round((time.perf_counter() - t0) * 1000)
        ok = isinstance(resultado, dict) and 'error' not in resultado
        reg = None
        if registrar:
            reg = self.apuntar(servidor=clave or '—', herramienta=herramienta, argumentos=argumentos, ms=ms, ok=ok, origen=origen,
                               resumen=self._resumen(resultado), resultado=self._acotar(resultado))
        return {'servidor': clave, 'servidor_nombre': NOMBRES.get(clave), 'herramienta': herramienta, 'argumentos': argumentos, 'ok': ok,
                'ms': ms, 'avisos': avisos, 'resultado': resultado, 'traza_id': reg['id'] if reg else None}

    async def _invocar(self, srv, herramienta, argumentos, reintento=True):
        if not srv.vivo:
            return {'error': f'El servidor {NOMBRES[srv.clave]} no está en marcha: {srv.error or "sin detalle"}'}
        try:
            r = await srv.sesion.call_tool(herramienta, argumentos)
        except Exception as e:                           # noqa: BLE001 - tubería rota, tiempo agotado...
            if reintento and not srv.vivo:
                try:
                    await srv.iniciar()
                    return await self._invocar(srv, herramienta, argumentos, reintento=False)
                except Exception:                        # noqa: BLE001
                    pass
            return {'error': f'{type(e).__name__}: {str(e)[:200]}'}
        if r.isError:                                    # el protocolo rechazó los argumentos (tipos)
            return {'error': r.content[0].text if r.content else 'Error del protocolo MCP.'}
        sc = r.structuredContent
        if isinstance(sc, dict) and set(sc) == {'result'} and isinstance(sc['result'], dict):
            sc = sc['result']
        if sc:
            return sc
        try:
            return json.loads(r.content[0].text)
        except Exception:                                # noqa: BLE001
            return {'error': 'La herramienta devolvió algo que no es JSON.'}

    @staticmethod
    def _resumen(resultado):
        if isinstance(resultado, dict) and 'error' in resultado:
            return 'error: ' + str(resultado['error'])[:140]
        txt = json.dumps(resultado, ensure_ascii=False)
        return txt if len(txt) <= 140 else txt[:137] + '…'

    @staticmethod
    def _acotar(resultado):
        txt = json.dumps(resultado, ensure_ascii=False)
        return resultado if len(txt) <= 20000 else {'recortado': True, 'texto': txt[:20000] + '…'}


# ------------------------------------------------------------------------------------------------ el modelo registrado (MLflow)
def registro():
    if alias_modelo is None:
        raise alias_error('No se puede importar ia_mlops: revisa MCP_PROYECTO (04-Proyecto-Base).')
    return alias_modelo.conectar()[1]


def alias_error(msg):
    return (alias_modelo.ErrorAlias if alias_modelo else RuntimeError)(msg)


def estado_registro():
    return alias_modelo.estado(registro())


# ------------------------------------------------------------------------------------------------ LLM
class ErrorLLM(RuntimeError):
    pass


class ClienteLLM:
    """POST a /chat/completions (formato OpenAI). Temperatura 0 y semilla fija. Es lo mismo que ClienteOllama del curso."""

    def __init__(self, url, modelo, timeout=180):
        self.url, self.modelo, self.timeout = url.rstrip('/'), modelo, timeout

    def chat(self, mensajes, tools=None):
        cuerpo = {'model': self.modelo, 'messages': mensajes, 'temperature': 0, 'seed': 42}
        if tools:
            cuerpo['tools'] = tools
        try:
            r = httpx.post(f'{self.url}/chat/completions', json=cuerpo, timeout=self.timeout)
            r.raise_for_status()
            return r.json()['choices'][0]['message']
        except (httpx.ConnectError, httpx.ConnectTimeout):
            raise ErrorLLM(ayuda_llm(self.url, self.modelo, 'no responde')) from None
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ErrorLLM(f'El LLM responde, pero no conoce el modelo «{self.modelo}». Descárgalo con:  ollama pull {self.modelo}') from None
            raise ErrorLLM(f'El LLM devolvió el error HTTP {e.response.status_code}.') from None
        except httpx.TimeoutException:
            raise ErrorLLM(f'El LLM tardó más de {self.timeout} s en responder (un modelo grande en CPU puede ser lento).') from None
        except (KeyError, IndexError, ValueError):
            raise ErrorLLM('El LLM respondió con un formato que no es el de /v1/chat/completions.') from None


def ayuda_llm(url, modelo, motivo):
    return (f'El LLM {motivo} en {url}. Arráncalo (Ollama): «ollama serve» y, si falta el modelo, «ollama pull {modelo}». '
            'Si tu LLM está en otro puerto (el curso usa Qwen2.5-3B-Instruct Q4 en el 11435), cámbialo en Ajustes. El resto de la interfaz funciona sin LLM.')


class Ajustes:
    def __init__(self):
        self.url = os.environ.get('CURSO_LLM_URL') or LLM_URL_DEFECTO
        self.modelo = os.environ.get('CURSO_LLM_MODELO') or LLM_MODELO_DEFECTO


def obtener_llm(app):
    return getattr(app.state, 'llm', None) or ClienteLLM(app.state.ajustes.url, app.state.ajustes.modelo)


async def comprobar_llm(app):
    aj = app.state.ajustes
    if getattr(app.state, 'llm', None) is not None:
        return {'ok': True, 'url': aj.url, 'modelo': 'LLM falso (pruebas)', 'detalle': 'LLM de guion inyectado', 'ayuda': ''}
    base = {'url': aj.url, 'modelo': aj.modelo}
    try:
        async with httpx.AsyncClient(timeout=2.5) as c:
            r = await c.get(f'{aj.url.rstrip("/")}/models')
        r.raise_for_status()
        ids = [m.get('id') for m in r.json().get('data', [])]
    except Exception:                                    # noqa: BLE001
        return {**base, 'ok': False, 'detalle': 'no responde', 'ayuda': ayuda_llm(aj.url, aj.modelo, 'no responde')}
    if aj.modelo not in ids:
        return {**base, 'ok': False, 'detalle': 'modelo no descargado', 'modelos': ids,
                'ayuda': f'El LLM responde, pero no tiene «{aj.modelo}». Descárgalo con:  ollama pull {aj.modelo}   (hay: {", ".join(ids) or "ninguno"}).'}
    return {**base, 'ok': True, 'detalle': 'responde', 'modelos': ids, 'ayuda': ''}


SISTEMA = ('Eres el asistente de datos del caso Retail del curso. Tienes herramientas: unas consultan los datos (clientes, facturas, países, productos) '
           'y otras llaman al modelo de predicción. Para cualquier cifra, país, cliente o probabilidad USA una herramienta: nunca la inventes ni la calcules tú. '
           'La probabilidad del modelo es la de que el cliente VUELVA A COMPRAR en los próximos 90 días: alta es buena noticia, no es riesgo de abandono. '
           'Si una herramienta devuelve «error», díselo al usuario con claridad. Responde en español, en pocas frases, con las cifras tal cual las devuelven las herramientas.')


# ------------------------------------------------------------------------------------------------ aplicación
@asynccontextmanager
async def vida(app):
    TRABAJO.mkdir(exist_ok=True)
    app.state.puente = Puente()
    app.state.ajustes = Ajustes()
    app.state.llm = None
    app.state.cache_clientes = {'version': None, 'datos': None}
    app.state.candado_clientes = asyncio.Lock()
    await app.state.puente.arrancar()
    try:
        yield
    finally:
        await app.state.puente.parar()


app = FastAPI(title='Interfaz MCP del extra de S5', lifespan=vida, docs_url=None, redoc_url=None, openapi_url=None)
_hosts = ['127.0.0.1', 'localhost', 'testserver'] + [h.strip() for h in os.environ.get('CURSO_UI_HOSTS', '').split(',') if h.strip()]
app.add_middleware(TrustedHostMiddleware, allowed_hosts=_hosts)          # frena el «DNS rebinding»: solo se atiende a este equipo
app.mount('/estatico', StaticFiles(directory=AQUI / 'estatico'), name='estatico')


@app.get('/')
async def portada():
    return FileResponse(AQUI / 'estatico' / 'index.html', headers={'Cache-Control': 'no-store'})


def puente(request) -> Puente:
    return request.app.state.puente


async def datos_modelo(request):
    """Qué versión responde ahora (llama a modelo_en_uso sin ensuciar la traza) y qué dice el registro."""
    p = puente(request)
    r = await p.llamar('modelo_en_uso', {}, origen='estado', registrar=False)
    res = r['resultado'] if isinstance(r['resultado'], dict) else {}
    try:
        reg = await asyncio.to_thread(estado_registro)
        error_reg = None
    except Exception as e:                               # noqa: BLE001
        reg, error_reg = None, str(e)[:300]
    versiones = reg['versiones'] if reg else []
    champion = reg['alias'].get('champion') if reg else None
    return {'version': res.get('version'), 'alias': res.get('alias'), 'valid_auc': res.get('valid_auc'), 'test_auc': res.get('test_auc'),
            'versiones_registradas': res.get('versiones_registradas', len(versiones)), 'error': res.get('error') or error_reg,
            'sin_alias': bool(reg) and champion is None, 'ultima_version': max((v['version'] for v in versiones), default=None),
            'alias_champion': champion, 'registro': reg}


@app.get('/api/estado')
async def estado(request: Request):
    p = puente(request)
    modelo, llm = await asyncio.gather(datos_modelo(request), comprobar_llm(request.app))
    servidores = {}
    for clave, s in p.servidores.items():
        servidores[clave] = {'nombre': NOMBRES[clave], 'vivo': s.vivo, 'error': None if s.vivo else (s.error or s.detalle_arranque() or 'no arrancó'),
                             'herramientas': s.herramientas}
    datos_ok = servidores['datos']['vivo']
    motor = None
    if datos_ok:
        r = await p.llamar('listar_tablas', {}, registrar=False)
        motor = r['resultado'].get('motor') if r['ok'] else None
    return respuesta({'servidores': servidores, 'backend': motor or p.backend, 'gcp_project_definido': bool(os.environ.get('GCP_PROJECT')),
                      'modelo': modelo, 'llm': llm, 'proyecto_ok': alias_modelo is not None and CURSO_DB.is_file(), 'max_pasos': MAX_PASOS})


class Herramienta(BaseModel):
    herramienta: str = Field(min_length=1, max_length=80)
    argumentos: dict = Field(default_factory=dict)
    servidor: str | None = None


@app.post('/api/herramienta')
async def herramienta(cuerpo: Herramienta, request: Request):
    return respuesta(await puente(request).llamar(cuerpo.herramienta, cuerpo.argumentos, origen='explorador'))


@app.get('/api/traza')
async def traza(request: Request, desde: int = 0):
    p = puente(request)
    return respuesta({'items': [t for t in p.traza if t['id'] > desde], 'ultimo_id': p._n})


@app.post('/api/traza/limpiar')
async def traza_limpiar(request: Request):
    puente(request).traza.clear()
    return {'ok': True}


# ------------------------------------------------------------------------------------------------ clientes (probabilidad de todos)
def ids_clientes():
    con = sqlite3.connect(CURSO_DB.resolve().as_uri() + '?mode=ro', uri=True)
    try:
        return [r[0] for r in con.execute('SELECT DISTINCT cliente_id FROM fs_produccion ORDER BY cliente_id')]
    finally:
        con.close()


@app.get('/api/clientes')
async def clientes(request: Request):
    p = puente(request)
    estado_modelo = await datos_modelo(request)
    if estado_modelo['error'] or estado_modelo['version'] is None:
        return respuesta({'clientes': [], 'version': None, 'error': estado_modelo['error'] or 'El modelo no responde.', 'sin_alias': estado_modelo['sin_alias']})
    cache = request.app.state.cache_clientes
    async with request.app.state.candado_clientes:
        if cache['datos'] is not None and cache['version'] == estado_modelo['version']:
            return respuesta({**cache['datos'], 'cacheado': True})
        try:
            ids = await asyncio.to_thread(ids_clientes)
        except Exception as e:                           # noqa: BLE001
            return respuesta({'clientes': [], 'version': None, 'error': f'No se pudo leer fs_produccion: {type(e).__name__}'})
        t0 = time.perf_counter()
        sem = asyncio.Semaphore(8)

        async def uno(i):
            async with sem:
                return await p.llamar('predecir_cliente', {'cliente_id': i}, registrar=False)

        rs = await asyncio.gather(*(uno(i) for i in ids))
        filas = [r['resultado'] for r in rs if r['ok']]
        fallos = len(rs) - len(filas)
        versiones = {f['version_modelo'] for f in filas}
        ms = round((time.perf_counter() - t0) * 1000)
        p.apuntar(servidor='modelo', herramienta=f'predecir_cliente ×{len(rs)}', argumentos={'cliente_id': f'{len(ids)} clientes de fs_produccion'}, ms=ms,
                  ok=fallos == 0, origen='clientes', resumen=f'{len(filas)} puntuados, {fallos} fallos (llamadas concurrentes)',
                  resultado={'puntuados': len(filas), 'fallos': fallos, 'versiones': sorted(versiones)})
        lista = [{'cliente_id': f['cliente_id'], 'probabilidad': f['probabilidad'], 'tramo': f['tramo'], 'variables': f['variables']} for f in filas]
        rangos = {}
        for v in (cfg_curso.FEATURES if cfg_curso else []):
            vals = [f['variables'][v] for f in lista if f['variables'].get(v) is not None]
            rangos[v] = {'min': min(vals), 'max': max(vals)} if vals else None
        datos = {'clientes': lista, 'version': next(iter(versiones)) if len(versiones) == 1 else None, 'rangos': rangos, 'fallos': fallos, 'ms': ms}
        if len(versiones) == 1:
            cache['version'], cache['datos'] = datos['version'], datos
        return respuesta({**datos, 'cacheado': False})


# ------------------------------------------------------------------------------------------------ chat (bucle de agente)
class Mensaje(BaseModel):
    role: str = Field(pattern='^(user|assistant)$')
    content: str = Field(max_length=4000)


class Chat(BaseModel):
    mensajes: list[Mensaje] = Field(min_length=1, max_length=40)


def evento(**d):
    return 'data: ' + json.dumps(limpiar(d), ensure_ascii=False) + '\n\n'


def resultado_para_llm(resultado, tope=5000):
    txt = json.dumps(resultado, ensure_ascii=False)
    return txt if len(txt) <= tope else txt[:tope] + '… [recortado]'


async def bucle_agente(request, mensajes_usuario):
    p = puente(request)
    llm = obtener_llm(request.app)
    herramientas = p.todas()
    tools = [{'type': 'function', 'function': {'name': h['nombre'], 'description': h['descripcion'], 'parameters': sin_titulos(h['inputSchema'])}} for h in herramientas]
    if not herramientas:
        yield evento(tipo='error', texto='No hay ningún servidor MCP en marcha: no hay herramientas que ofrecer al LLM.')
        yield evento(tipo='fin')
        return
    historial = [{'role': 'system', 'content': SISTEMA}] + [{'role': m.role, 'content': m.content} for m in mensajes_usuario]
    for paso in range(1, MAX_PASOS + 1):
        yield evento(tipo='paso', n=paso, de=MAX_PASOS)
        try:
            msg = await asyncio.to_thread(llm.chat, historial, tools)
        except ErrorLLM as e:
            yield evento(tipo='error_llm', texto=str(e))
            break
        except Exception as e:                           # noqa: BLE001
            yield evento(tipo='error_llm', texto=f'El LLM falló: {type(e).__name__}: {str(e)[:200]}')
            break
        pedidas = msg.get('tool_calls') or []
        contenido = (msg.get('content') or '').strip()
        if not pedidas:
            yield evento(tipo='final', texto=contenido or '(El modelo no devolvió texto.)', pasos=paso)
            break
        if contenido:
            yield evento(tipo='pensamiento', texto=contenido)
        historial.append({'role': 'assistant', 'content': msg.get('content'), 'tool_calls': pedidas})
        for i, tc in enumerate(pedidas):
            f = tc.get('function') or {}
            nombre, crudos = f.get('name') or '', f.get('arguments')
            try:
                args = json.loads(crudos) if isinstance(crudos, str) and crudos.strip() else (crudos or {})
                err_args = None
            except json.JSONDecodeError:
                args, err_args = None, f'Los argumentos no son JSON válido: «{str(crudos)[:100]}».'
            srv = p.servidor_de(nombre)
            yield evento(tipo='llamada', id=tc.get('id') or f'{paso}_{i}', servidor=srv.clave if srv else None, herramienta=nombre, argumentos=args if err_args is None else crudos)
            if err_args:
                r = {'servidor': srv.clave if srv else None, 'ok': False, 'ms': 0, 'avisos': [], 'resultado': {'error': err_args}, 'herramienta': nombre}
                p.apuntar(servidor=r['servidor'] or '—', herramienta=nombre, argumentos=None, ms=0, ok=False, origen='chat', resumen='error: ' + err_args, resultado=r['resultado'])
            else:
                r = await p.llamar(nombre, args, origen='chat')
            yield evento(tipo='resultado', id=tc.get('id') or f'{paso}_{i}', servidor=r['servidor'], herramienta=nombre, ok=r['ok'], ms=r['ms'], avisos=r['avisos'], resultado=r['resultado'])
            historial.append({'role': 'tool', 'tool_call_id': tc.get('id') or f'{paso}_{i}', 'name': nombre, 'content': resultado_para_llm(r['resultado'])})
    else:
        yield evento(tipo='limite', texto=f'Se alcanzó el límite de {MAX_PASOS} pasos sin una respuesta final. El modelo siguió pidiendo herramientas; '
                                         'prueba con una pregunta más concreta o con un modelo más capaz.')
    yield evento(tipo='fin')


@app.post('/api/chat')
async def chat(cuerpo: Chat, request: Request):
    if cuerpo.mensajes[-1].role != 'user':
        return respuesta({'error': 'El último mensaje debe ser del usuario.'}, 422)
    return StreamingResponse(bucle_agente(request, cuerpo.mensajes), media_type='text/event-stream', headers={'Cache-Control': 'no-store', 'X-Accel-Buffering': 'no'})


class AjustesCuerpo(BaseModel):
    url: str = Field(min_length=8, max_length=200, pattern=r'^https?://[^\s]+$')
    modelo: str = Field(min_length=1, max_length=120)


@app.get('/api/ajustes')
async def ajustes_leer(request: Request):
    a = request.app.state.ajustes
    return {'url': a.url, 'modelo': a.modelo}


@app.post('/api/ajustes')
async def ajustes_guardar(cuerpo: AjustesCuerpo, request: Request):
    a = request.app.state.ajustes
    a.url, a.modelo = cuerpo.url.rstrip('/'), cuerpo.modelo.strip()
    return {'url': a.url, 'modelo': a.modelo}


# ------------------------------------------------------------------------------------------------ modelo: promover y volver
class Version(BaseModel):
    version: int = Field(ge=1, le=100000)


async def tras_cambio(request, resultado):
    r = await puente(request).llamar('modelo_en_uso', {}, origen='modelo')       # la versión que responde AHORA, sin reiniciar nada
    return respuesta({'cambio': resultado, 'responde': r['resultado'], 'modelo': (await datos_modelo(request))})


@app.get('/api/modelo')
async def modelo_estado(request: Request):
    return respuesta(await datos_modelo(request))


@app.post('/api/modelo/promover')
async def modelo_promover(cuerpo: Version, request: Request):
    try:
        res = await asyncio.to_thread(lambda: alias_modelo.promover(registro(), cuerpo.version))
    except Exception as e:                               # noqa: BLE001 - ErrorAlias u otro: mensaje claro
        return respuesta({'error': str(e)[:400]}, 409)
    return await tras_cambio(request, res)


@app.post('/api/modelo/volver')
async def modelo_volver(request: Request):
    try:
        res = await asyncio.to_thread(lambda: alias_modelo.volver(registro()))
    except Exception as e:                               # noqa: BLE001
        return respuesta({'error': str(e)[:400]}, 409)
    return await tras_cambio(request, res)


# ------------------------------------------------------------------------------------------------ backend de datos
class CuerpoBackend(BaseModel):
    backend: str = Field(pattern='^(sqlite|bigquery)$')
    proyecto: str | None = Field(default=None, max_length=40)
    dataset: str | None = Field(default=None, max_length=100)


def comprobar_bigquery(proyecto):
    """Solo mira que existan la librería y las credenciales locales. NO hace ninguna llamada a BigQuery. Devuelve un motivo o None."""
    try:
        from google.cloud import bigquery  # noqa: F401
    except ImportError:
        return 'Falta la librería google-cloud-bigquery (pip install google-cloud-bigquery).'
    try:
        import google.auth
        google.auth.default()
    except Exception:                                    # noqa: BLE001
        return 'No hay credenciales de Google: ejecuta «gcloud auth application-default login» y vuelve a intentarlo.'
    return None


@app.post('/api/backend')
async def backend(cuerpo: CuerpoBackend, request: Request):
    p = puente(request)
    async with p.candado_backend:
        if cuerpo.backend == p.backend:
            return respuesta({'backend': p.backend, 'cambio': False})
        if cuerpo.backend == 'sqlite':
            p.backend = 'sqlite'
            await p.servidores['datos'].parar()
            try:
                await p.servidores['datos'].iniciar(script=FUENTES / 'mcp_datos.py')
            except Exception as e:                       # noqa: BLE001
                return respuesta({'error': f'No arrancó el servidor de datos en SQLite: {p.servidores["datos"].error or e}'}, 500)
            return respuesta({'backend': 'sqlite', 'cambio': True})
        proyecto = (cuerpo.proyecto or os.environ.get('GCP_PROJECT') or '').strip()
        dataset = (cuerpo.dataset or os.environ.get('BQ_DATASET') or 'curso_master').strip()
        if not proyecto:
            return respuesta({'error': 'El modo BigQuery exige un proyecto de Google Cloud (variable GCP_PROJECT o el campo del diálogo). Se queda en SQLite.', 'backend': p.backend}, 400)
        if not re.fullmatch(r'[a-z][a-z0-9\-]{4,28}[a-z0-9]', proyecto) or not re.fullmatch(r'[A-Za-z0-9_]{1,100}', dataset):
            return respuesta({'error': 'El identificador del proyecto o del dataset no es válido. Se queda en SQLite.', 'backend': p.backend}, 400)
        motivo = comprobar_bigquery(proyecto)
        if motivo:
            return respuesta({'error': motivo + ' Se queda en SQLite.', 'backend': p.backend}, 400)
        p.backend, p.bq_proyecto, p.bq_dataset = 'bigquery', proyecto, dataset
        srv = p.servidores['datos']
        await srv.parar()
        try:
            await srv.iniciar(script=p.script_bq or FUENTES / 'mcp_datos.py')
        except Exception as e:                           # noqa: BLE001 - vuelta atrás a SQLite
            motivo = srv.detalle_arranque() or srv.error or str(e)
            p.backend = 'sqlite'
            await srv.parar()
            try:
                await srv.iniciar(script=FUENTES / 'mcp_datos.py')
            except Exception:                            # noqa: BLE001
                pass
            return respuesta({'error': f'El servidor de datos no arrancó en modo BigQuery ({motivo}). Se vuelve a SQLite.', 'backend': 'sqlite'}, 500)
        return respuesta({'backend': 'bigquery', 'cambio': True})


# ------------------------------------------------------------------------------------------------ pestaña «Lote» (extra Composer)
# Lanza el DAG retencion_lote por la API REST de Airflow (local o Cloud Composer). El cliente es el de extra-composer-batch/lanzar_lote.py.
# Variables (todas opcionales): AIRFLOW_URL, AIRFLOW_AUTH (google|basic|token|ninguna), AIRFLOW_DAG, LOTE_IMAGEN_DEFECTO, LOTE_EXTRA (carpeta
# del extra) y, SEGÚN LA AUTENTICACIÓN, AIRFLOW_USUARIO/AIRFLOW_CLAVE o AIRFLOW_TOKEN. Los secretos solo se LEEN del entorno: nunca se
# guardan, no salen en ninguna respuesta y no se reciben por la interfaz. NO se simula ninguna ejecución: si Airflow no responde, se dice.
LOTE_DIR = Path(os.environ.get('LOTE_EXTRA') or EXTRA.parent / 'extra-composer-batch')
LOTE_URL_SUGERIDA = 'http://localhost:8080'
try:
    for _r in (LOTE_DIR, LOTE_DIR / 'dags'):
        if str(_r) not in sys.path:
            sys.path.insert(0, str(_r))
    import lanzar_lote as airflow_cli                    # noqa: E402
    import lote_logica                                   # noqa: E402
except Exception:                                        # noqa: BLE001 - la UI arranca igual y la pestaña lo explica
    airflow_cli = lote_logica = None

RUN_ID_RE = re.compile(r'^[A-Za-z0-9_.:+\-]{1,200}$')
TAREA_RE = re.compile(r'^[A-Za-z0-9_.\-]{1,100}$')
TTL_CLIENTE = 300
COMO_ARRANCAR = ('Arranca Airflow en local:  cd 01-Sesiones/S5-MLOps-y-Operacion/extra-composer-batch  y  '
                 'docker compose -f docker-compose-airflow.yaml up -d  (tarda 1-2 minutos). Después reinicia esta interfaz con '
                 'AIRFLOW_URL=http://localhost:8080 AIRFLOW_AUTH=basic AIRFLOW_USUARIO=airflow AIRFLOW_CLAVE=airflow. '
                 'En Cloud Composer: AIRFLOW_URL con el valor de «gcloud composer environments describe … --format="value(config.airflowUri)"» y AIRFLOW_AUTH=google.')


class ErrorLote(Exception):
    pass


class HTTPExceptionLote(Exception):
    def __init__(self, mensaje, estado):
        super().__init__(mensaje)
        self.mensaje, self.estado = mensaje, estado


def lote_config():
    url = (os.environ.get('AIRFLOW_URL') or '').strip().rstrip('/')
    con_credenciales = bool(re.match(r'^[a-z]+://[^/]*@', url))
    if con_credenciales:
        url = re.sub(r'^([a-z]+://)[^/]*@', r'\1', url)           # nunca se enseña ni se usa un usuario:clave escrito dentro de la URL
    auth = (os.environ.get('AIRFLOW_AUTH') or 'ninguna').strip().lower()
    return {
        'url': url, 'url_con_credenciales': con_credenciales, 'url_definida': bool(url), 'url_sugerida': LOTE_URL_SUGERIDA, 'auth': auth if auth in ('google', 'basic', 'token', 'ninguna') else 'ninguna',
        'dag': (os.environ.get('AIRFLOW_DAG') or 'retencion_lote').strip(), 'imagen_defecto': (os.environ.get('LOTE_IMAGEN_DEFECTO') or '').strip(),
        'credenciales': {'usuario': bool(os.environ.get('AIRFLOW_USUARIO')), 'clave': bool(os.environ.get('AIRFLOW_CLAVE')), 'token': bool(os.environ.get('AIRFLOW_TOKEN'))},
        'cliente_disponible': airflow_cli is not None, 'como_arrancarlo': COMO_ARRANCAR,
    }


def cliente_airflow(request, forzar=False):
    """Un cliente ya preparado (versión de la API y token), guardado unos minutos. Lanza ErrorAirflow si no hay manera."""
    cfg = lote_config()
    if airflow_cli is None:
        raise ErrorLote(f'No se encontró el extra de Composer en {LOTE_DIR.name} (variable LOTE_EXTRA).')
    if not cfg['url_definida']:
        raise ErrorLote('No hay AIRFLOW_URL: la interfaz no sabe a qué Airflow hablar.')
    if cfg['url_con_credenciales']:
        raise ErrorLote('AIRFLOW_URL no debe llevar usuario ni contraseña dentro: usa AIRFLOW_USUARIO y AIRFLOW_CLAVE.')
    clave = (cfg['url'], cfg['auth'], os.environ.get('AIRFLOW_USUARIO'), hash(os.environ.get('AIRFLOW_CLAVE')), hash(os.environ.get('AIRFLOW_TOKEN')))   # solo en memoria
    guardado = getattr(request.app.state, 'cliente_lote', None)
    if not forzar and guardado and guardado[0] == clave and time.time() - guardado[1] < TTL_CLIENTE:
        return guardado[2]
    c = airflow_cli.Cliente(cfg['url'], cfg['auth'], os.environ.get('AIRFLOW_API', 'auto'), timeout=15)
    c.preparar()
    request.app.state.cliente_lote = (clave, time.time(), c)
    return c


async def con_airflow(request, funcion):
    """Ejecuta `funcion(cliente)` fuera del bucle de eventos; si falla por la autenticación, reintenta una vez con un cliente nuevo."""
    def trabajo(forzar):
        return funcion(cliente_airflow(request, forzar))
    try:
        try:
            return await asyncio.to_thread(trabajo, False)
        except Exception as e:                           # noqa: BLE001
            if airflow_cli is None or not isinstance(e, airflow_cli.ErrorAirflow) or '401' not in str(e):
                raise
            return await asyncio.to_thread(trabajo, True)
    except ErrorLote as e:
        raise HTTPExceptionLote(str(e), 400)
    except Exception as e:                               # noqa: BLE001
        if airflow_cli is not None and isinstance(e, airflow_cli.ErrorAirflow):
            raise HTTPExceptionLote(str(e), 502)
        raise


@app.exception_handler(HTTPExceptionLote)
async def _error_lote(request, e):
    return respuesta({'error': e.mensaje}, e.estado)


class LoteCuerpo(BaseModel):
    corte: str = Field(default='', max_length=10)
    imagen: str = Field(default='', max_length=300)
    capacidad: float = Field(default=0.10, gt=0, le=1)
    huella_esperada: str = Field(default='', max_length=64, pattern=r'^[A-Za-z0-9]*$')
    confirmado: bool = False


def _tareas(c, dag, run_id):
    return [{'tarea': t['task_id'], 'estado': t.get('state'), 'intento': t.get('try_number') or 0} for t in c.tareas(dag, run_id)]


def _segundos(run):
    try:
        ini = datetime.fromisoformat(str(run.get('start_date')).replace('Z', '+00:00'))
        fin = datetime.fromisoformat(str(run['end_date']).replace('Z', '+00:00')) if run.get('end_date') else datetime.now(ini.tzinfo)
        return max(0, round((fin - ini).total_seconds()))
    except Exception:                                    # noqa: BLE001
        return None


@app.get('/api/lote/config')
async def lote_config_ep():
    return respuesta(lote_config())


@app.get('/api/lote/estado')
async def lote_estado(request: Request):
    cfg = lote_config()
    try:
        datos = await con_airflow(request, lambda c: {'api': c.api, 'dag': c.dag(cfg['dag'])})
    except HTTPExceptionLote as e:
        return respuesta({'ok': False, 'error': e.mensaje, 'como_arrancarlo': COMO_ARRANCAR})
    d = datos['dag']
    return respuesta({'ok': True, 'api': datos['api'], 'dag': cfg['dag'], 'en_pausa': bool(d.get('is_paused')), 'descripcion': d.get('description')})


@app.post('/api/lote/lanzar')
async def lote_lanzar(cuerpo: LoteCuerpo, request: Request):
    if not cuerpo.confirmado:
        return respuesta({'error': 'Falta la confirmación: el lote solo se lanza tras aceptar el diálogo.'}, 400)
    if airflow_cli is None:
        return respuesta({'error': 'No se encontró el extra de Composer.'}, 400)
    corte, imagen = cuerpo.corte.strip(), cuerpo.imagen.strip()
    if corte and not lote_logica.CORTE_RE.match(corte):
        return respuesta({'error': f'El corte «{corte}» no es una fecha AAAA-MM-DD.'}, 422)
    if imagen and not lote_logica.IMAGEN_RE.match(imagen):
        return respuesta({'error': f'La imagen «{imagen}» no es una referencia de imagen válida.'}, 422)
    cfg = lote_config()
    run_id = 'ui-' + datetime.now().strftime('%Y%m%dT%H%M%S')
    conf = {'corte': corte, 'imagen': imagen, 'capacidad': cuerpo.capacidad}
    if cuerpo.huella_esperada:
        conf['huella_esperada'] = cuerpo.huella_esperada

    def lanzar(c):
        if c.dag(cfg['dag']).get('is_paused'):
            raise ErrorLote(f'El DAG «{cfg["dag"]}» está en pausa: el run se quedaría en cola. Reactívalo con «airflow dags unpause {cfg["dag"]}».')
        c.lanzar(cfg['dag'], conf, run_id)
        return {'run_id': run_id, 'api': c.api, 'enlace': airflow_cli.enlace_ui(c.base, cfg['dag'], run_id, c.api), 'conf': conf}
    return respuesta(await con_airflow(request, lanzar))


@app.get('/api/lote/run/{run_id}')
async def lote_run(run_id: str, request: Request):
    if not RUN_ID_RE.match(run_id):
        return respuesta({'error': 'Identificador de run no válido.'}, 422)
    cfg = lote_config()

    def leer(c):
        r = c.run(cfg['dag'], run_id)
        return {'run_id': run_id, 'estado': r.get('state'), 'segundos': _segundos(r), 'conf': r.get('conf') or {}, 'tareas': _tareas(c, cfg['dag'], run_id),
                'enlace': airflow_cli.enlace_ui(c.base, cfg['dag'], run_id, c.api), 'final': r.get('state') in ('success', 'failed')}
    return respuesta(await con_airflow(request, leer))


@app.get('/api/lote/historial')
async def lote_historial(request: Request):
    cfg = lote_config()
    try:
        runs = await con_airflow(request, lambda c: [
            {'run_id': r.get('dag_run_id'), 'estado': r.get('state'), 'inicio': r.get('start_date'), 'segundos': _segundos(r),
             'corte': (r.get('conf') or {}).get('corte') or '(por defecto)', 'enlace': airflow_cli.enlace_ui(c.base, cfg['dag'], r.get('dag_run_id') or '', c.api)}
            for r in c.historial(cfg['dag'], 10)])
    except HTTPExceptionLote as e:                       # sin Airflow no hay historial: se dice, sin un error HTTP en la consola
        return respuesta({'runs': [], 'error': e.mensaje})
    return respuesta({'runs': runs})

@app.get('/api/lote/log/{run_id}/{tarea}')
async def lote_log(run_id: str, tarea: str, request: Request, intento: int = 1):
    if not (RUN_ID_RE.match(run_id) and TAREA_RE.match(tarea)) or not 1 <= intento <= 20:
        return respuesta({'error': 'Run, tarea o intento no válidos.'}, 422)
    cfg = lote_config()
    texto = await con_airflow(request, lambda c: c.log(cfg['dag'], run_id, tarea, intento))
    return respuesta({'tarea': tarea, 'texto': texto[-8000:]})


@app.get('/api/lote/resultado')
async def lote_resultado():
    """El último lote que hay en reports/campana de ESTE equipo. Solo tiene sentido si el lote corrió aquí (Airflow local con la carpeta montada)."""
    carpeta = Path(os.environ.get('CURSO_REPORTES') or PROYECTO / 'reports') / 'campana'
    jsons = sorted(carpeta.glob('campana_*.json'), key=lambda p: p.stat().st_mtime) if carpeta.is_dir() else []
    if not jsons:
        return respuesta({'disponible': False, 'motivo': 'No hay ningún campana_*.json en reports/campana de este equipo. Si el lote corre en Composer, su salida queda en el contenedor y aquí no se ve: mira el registro de la tarea «resumir».'})
    ruta = jsons[-1]
    r = json.loads(ruta.read_text(encoding='utf-8'))
    tramos = {'alta': 0, 'media': 0, 'baja': 0}
    try:
        import csv
        with open(ruta.with_suffix('.csv'), encoding='utf-8') as f:
            for fila in csv.DictReader(f):
                p = float(fila['probabilidad'])
                tramos['alta' if p >= 0.70 else 'media' if p >= 0.40 else 'baja'] += 1
    except (OSError, KeyError, ValueError):
        tramos = None
    return respuesta({'disponible': True, 'archivo': ruta.name, 'modificado': datetime.fromtimestamp(ruta.stat().st_mtime).isoformat(timespec='seconds'),
                      'corte': r.get('corte'), 'generado_en': r.get('generado_en'), 'clientes': r.get('clientes_puntuados'), 'en_campana': r.get('clientes_en_campana'),
                      'capacidad': r.get('capacidad'), 'probabilidad_media': r.get('probabilidad_media'), 'modelo': r.get('modelo'), 'huella_datos': r.get('huella_datos'),
                      'origen': r.get('origen'), 'tramos': tramos})


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=int(os.environ.get('CURSO_UI_PUERTO', '8095')), log_level='warning')
