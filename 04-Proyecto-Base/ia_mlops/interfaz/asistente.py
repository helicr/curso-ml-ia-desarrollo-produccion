"""Pestaña «Asistente» del panel: POST /asistente {"pregunta": "..."} -> respuesta del agente de S5 + qué herramientas usó.

Es el agente de ia_mlops/agente (el bucle decidir -> herramienta -> observar) puesto detrás de un endpoint del panel.

    pregunta ──► Agente(LLM, caja de herramientas, skills) ──► respuesta + herramientas usadas (nombre, argumentos, resultado resumido)

EL LLM (variable CURSO_LLM, que se lee en cada petición)
    falso    (por defecto) un guion sin red ni Ollama: elige herramientas por palabras clave y contesta «LLM falso: …».
             Sirve para que el panel funcione en CI y en cualquier portátil. NO redacta: enseña los datos tal cual.
    ollama   el LLM real por /v1/chat/completions (CURSO_LLM_URL, CURSO_LLM_MODELO; ver ia_mlops/agente/llm.py).
             Si Ollama no responde, el panel lo dice en claro (503), sin traza de Python.

LAS HERRAMIENTAS
    Aquí el agente usa la caja EN MEMORIA sobre ia_mlops.agente.herramientas: por simplicidad, un solo proceso y nada que arrancar.
    En el compose (deploy/docker/compose-agente.yaml) se podría usar en su lugar el servidor MCP (CajaMCP): el agente no nota la
    diferencia, porque las dos cajas tienen la misma interfaz (listar / llamar). Las descripciones de abajo dicen expresamente que
    la probabilidad es la de VOLVER A COMPRAR: un LLM pequeño la confundió con la de abandono (prueba de humo del 22/11/2026).

PRIVACIDAD
    Las preguntas no se guardan: ni en disco ni en el registro (solo se anota la longitud y las herramientas usadas).
"""
import json
import logging
import os
import re
import time

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from ..api.registro import registrar

MAX_PREGUNTA = 1000
RESUMEN_MAX = 400             # caracteres del resultado de cada herramienta que se enseñan en el panel
TIMEOUT_LLM = 180             # segundos por llamada al LLM (un 3B en CPU tarda; el cuelgue indefinido no)
AVISO_RECOMPRA = 'La probabilidad es la de VOLVER A COMPRAR en 90 días, no la de abandonar: más alta = más probable que vuelva.'


class Pregunta(BaseModel):
    model_config = ConfigDict(extra='forbid', json_schema_extra={'examples': [{'pregunta': 'Dame los 5 clientes a los que llamar hoy y un guion para cada uno.'}]})
    pregunta: str


# ------------------------------------------------------------------------------------------------------------ herramientas
def _funciones():
    """Las herramientas del agente, con anotaciones (de ahí sale el esquema) y descripciones pensadas para un LLM pequeño."""
    from ..agente import herramientas as h

    def lista_del_dia(n: int = 10) -> dict:
        """Los n clientes con MÁS probabilidad de VOLVER A COMPRAR según el último lote, de mayor a menor (la lista del día para llamar)."""
        return h.lista_del_dia(n)

    def puntuar_bajo_demanda(cliente_id: int) -> dict:
        """Probabilidad de que el cliente VUELVA A COMPRAR en 90 días (no de que se vaya), con las variables de AYER (último lote)."""
        return h.puntuar_bajo_demanda(cliente_id)

    def puntuar_online(cliente_id: int, corte: str = '') -> dict:
        """Probabilidad de que el cliente VUELVA A COMPRAR en 90 días (no de que se vaya), con las variables de AHORA (incluye su última compra)."""
        return h.puntuar_online(cliente_id, corte or None)

    def version_en_produccion() -> dict:
        """Qué versión del modelo está en producción, desde cuándo, con qué métricas se aprobó y las versiones anteriores."""
        return h.version_en_produccion()

    def por_que(cliente_id: int, n: int = 5) -> dict:
        """Las variables que más empujan (hacia arriba o abajo) la probabilidad de VOLVER A COMPRAR de un cliente."""
        return h.por_que(cliente_id, n)

    return {f.__name__: f for f in (lista_del_dia, puntuar_bajo_demanda, puntuar_online, version_en_produccion, por_que)}


class _Registradora:
    """Envuelve una caja y apunta cada llamada (nombre, argumentos, resultado resumido) para enseñarla en el panel."""

    def __init__(self, caja):
        self.caja, self.llamadas = caja, []

    def listar(self):
        return self.caja.listar()

    def llamar(self, nombre, args):
        try:
            resultado = self.caja.llamar(nombre, args)
        except Exception as e:                                  # noqa: BLE001 - se apunta y se relanza: el agente lo trata como observación
            self.llamadas.append({'nombre': nombre, 'argumentos': args, 'resultado': f'error: {type(e).__name__}: {e}'[:RESUMEN_MAX], 'error': True})
            raise
        self.llamadas.append({'nombre': nombre, 'argumentos': args, 'resultado': _resumir(resultado),
                              'error': isinstance(resultado, dict) and 'error' in resultado})
        return resultado


def _resumir(resultado):
    texto = resultado if isinstance(resultado, str) else json.dumps(resultado, ensure_ascii=False, default=str)
    return texto if len(texto) <= RESUMEN_MAX else texto[:RESUMEN_MAX] + ' …'


# ------------------------------------------------------------------------------------------------------------ el LLM falso
def _linea_resultado(nombre, contenido):
    """Una frase corta con lo que devolvió una herramienta (para que el LLM falso la repita; no interpreta nada)."""
    try:
        d = json.loads(contenido)
    except (TypeError, ValueError):
        return f'{nombre}: {str(contenido)[:150]}'
    if not isinstance(d, dict):
        return f'{nombre}: {str(contenido)[:150]}'
    if 'error' in d:
        return f'{nombre}: error, {d["error"]}'
    if nombre == 'lista_del_dia':
        c = d.get('clientes', [])
        return f'{nombre}: {len(c)} cliente(s), con probabilidad de volver a comprar: ' + ', '.join(f'{x["cliente_id"]} ({x["probabilidad"]:.1%})' for x in c)
    if nombre in ('puntuar_online', 'puntuar_bajo_demanda'):
        return f'{nombre}: cliente {d.get("cliente_id")}, probabilidad de VOLVER A COMPRAR {d.get("probabilidad", 0):.1%} (corte {d.get("corte")})'
    if nombre == 'version_en_produccion':
        return f'{nombre}: versión {d.get("version")} en producción desde {d.get("en_produccion_desde")}'
    if nombre == 'por_que':
        v = d.get('variables_que_mas_pesan') or []
        return f'{nombre}: cliente {d.get("cliente_id")}, variables que más pesan: ' + (', '.join(f'{x["variable"]} ({x["efecto"]})' for x in v) or 'sin pesos (' + str(d.get('nota', ''))[:80] + ')')
    return f'{nombre}: {str(contenido)[:150]}'


class LLMDeGuion:
    """El LLM «falso» del panel: decide las herramientas por palabras clave de la pregunta y contesta con los datos, sin redactar.

    Cumple el contrato de ia_mlops/agente/llm.py (chat(mensajes, tools)), pero no entiende nada: solo hace que el panel se pueda
    enseñar sin Ollama. Con el LLM real, las mismas preguntas las resuelve el modelo.
    """

    def _plan(self, pregunta):
        p = pregunta.lower()
        ident = re.search(r'\b\d{4,}\b', p)
        cid = int(ident.group()) if ident else None
        if cid and re.search(r'por qu[eé]|motivo|explica', p):
            return [('por_que', {'cliente_id': cid})]
        if re.search(r'versi[oó]n|producci[oó]n', p) and not cid:
            return [('version_en_produccion', {})]
        if cid and re.search(r'probabilidad|cambiado|compr|riesgo|punt', p):
            return [('puntuar_bajo_demanda', {'cliente_id': cid}), ('puntuar_online', {'cliente_id': cid})]
        if re.search(r'llamar|clientes|lista|guion', p):
            n = re.search(r'\b(\d{1,2})\b', p)
            return [('lista_del_dia', {'n': int(n.group(1)) if n else 5})]
        return []

    def chat(self, mensajes, tools=None):
        from ..agente.llm import llamada
        pregunta = next((m['content'] for m in mensajes if m['role'] == 'user'), '')
        hechas = [m for m in mensajes if m['role'] == 'tool']
        plan = self._plan(pregunta)
        if len(hechas) < len(plan):
            nombre, args = plan[len(hechas)]
            return {'role': 'assistant', 'content': None, 'tool_calls': [llamada(nombre, args, id_=f'guion_{len(hechas)}')]}
        if not plan:
            return {'role': 'assistant', 'content': 'LLM falso: no sé qué herramienta usar para esta pregunta (es un guion, no entiende frases). '
                                                    'Prueba con uno de los ejemplos, o arranca el compose con Ollama para tener un LLM real.'}
        nombres = [n for n, _ in plan]
        lineas = '\n'.join('· ' + _linea_resultado(n, m['content']) for n, m in zip(nombres, hechas))
        return {'role': 'assistant', 'content': f'LLM falso: he ejecutado {", ".join(nombres)} y esto es lo que devolvieron (sin redactar):\n{lineas}'}


# ------------------------------------------------------------------------------------------------------------ el servicio
class Asistente:
    """Crea el agente en cada petición (el LLM se elige con CURSO_LLM) y ejecuta la pregunta. Se pueden cambiar `fabrica_llm` y `caja` en pruebas."""

    def __init__(self):
        self.fabrica_llm = None           # None -> según CURSO_LLM; en pruebas, una función sin argumentos que devuelve un LLM
        self.caja = None                  # None -> CajaEnMemoria sobre las herramientas de arriba
        self._skills = None

    def _llm(self):
        if self.fabrica_llm:
            return self.fabrica_llm(), {'tipo': 'prueba', 'modelo': None}
        tipo = (os.environ.get('CURSO_LLM') or 'falso').strip().lower()
        if tipo == 'falso':
            return LLMDeGuion(), {'tipo': 'falso', 'modelo': None}
        if tipo == 'ollama':
            from ..agente.llm import ClienteOllama                 # importa httpx: se carga solo si de verdad se usa Ollama
            c = ClienteOllama(timeout=TIMEOUT_LLM)
            return c, {'tipo': 'ollama', 'modelo': c.modelo}
        raise ErrorAsistente(500, f'CURSO_LLM debe ser «falso» u «ollama» (vale «{tipo}»).')

    def _skills_cargadas(self):
        if self._skills is None:
            from ..agente import skills
            try:
                self._skills = skills.cargar_skills()
            except Exception:                                      # noqa: BLE001 - sin carpeta de skills el agente funciona sin ellas
                self._skills = {}
        return self._skills

    def preguntar(self, pregunta):
        from ..agente.agente import Agente
        from ..agente.cajas import CajaEnMemoria
        try:
            llm, info = self._llm()
        except ImportError:
            raise ErrorAsistente(503, 'Falta la librería httpx para hablar con Ollama (en el compose la lleva la imagen interfaz-agente). '
                                      'Para probar el panel sin Ollama, usa CURSO_LLM=falso.') from None
        caja =_Registradora(self.caja or CajaEnMemoria(_funciones()))
        inicio = time.perf_counter()
        try:
            r = Agente(llm, caja, self._skills_cargadas(), max_pasos=6).ejecutar(pregunta)
        except ErrorAsistente:
            raise
        except Exception as e:                                     # noqa: BLE001 - el panel cuenta el motivo; la traza no sale al usuario
            raise ErrorAsistente(503, _motivo(e, info)) from None
        herramientas = list(caja.llamadas)
        for nombre in r.herramientas:                               # usar_skill no pasa por la caja: se añade sin argumentos
            if nombre == 'usar_skill':
                herramientas.insert(0, {'nombre': 'usar_skill', 'argumentos': None, 'resultado': 'instrucciones de una skill cargadas', 'error': False})
        return {'respuesta': r.texto, 'herramientas': herramientas, 'skills': r.skills, 'pasos': r.pasos, 'terminado': r.terminado,
                'latencia_ms': round((time.perf_counter() - inicio) * 1000), 'llm': info, 'aviso': AVISO_RECOMPRA}


class ErrorAsistente(Exception):
    def __init__(self, estado, detalle):
        super().__init__(detalle)
        self.estado, self.detalle = estado, detalle


def _motivo(e, info):
    """Un mensaje en claro para un fallo del LLM (sin traza ni rutas)."""
    nombre = type(e).__name__
    if info['tipo'] == 'ollama':
        url = os.environ.get('CURSO_LLM_URL') or 'la URL por defecto de CURSO_LLM_URL'
        if nombre == 'HTTPStatusError' and getattr(getattr(e, 'response', None), 'status_code', None) == 404:
            return (f'Ollama responde, pero no tiene el modelo «{info["modelo"]}». Descárgalo con deploy/docker/ollama-pull.sh '
                    f'(o: ollama pull {info["modelo"]}).')
        if nombre in ('ConnectError', 'ConnectTimeout', 'ReadTimeout', 'TimeoutException', 'ReadError', 'RemoteProtocolError', 'HTTPStatusError', 'ModuleNotFoundError'):
            return (f'El LLM (Ollama en {url}) no responde ({nombre}). ¿Está arrancado y con el modelo «{info["modelo"]}» descargado? '
                    'Para probar el panel sin Ollama, usa CURSO_LLM=falso.')
    return f'El asistente no pudo contestar ({nombre}). Para probar el panel sin LLM real, usa CURSO_LLM=falso.'


def registrar_asistente(app: FastAPI):
    asistente = Asistente()
    app.state.asistente = asistente

    @app.post('/asistente')
    def preguntar(peticion: Pregunta):
        """Pregunta al agente. Devuelve la respuesta, las herramientas usadas (nombre, argumentos, resultado resumido), las skills, los pasos y la latencia."""
        pregunta = peticion.pregunta.strip()
        if not pregunta:
            return JSONResponse(status_code=422, content={'detalle': 'Escribe una pregunta.'})
        if len(pregunta) > MAX_PREGUNTA:
            return JSONResponse(status_code=422, content={'detalle': f'La pregunta es demasiado larga ({len(pregunta)} caracteres; máximo {MAX_PREGUNTA}).'})
        try:
            r = asistente.preguntar(pregunta)
        except ErrorAsistente as e:
            registrar(logging.WARNING, 'asistente no disponible', evento='asistente_error', estado=e.estado)
            return JSONResponse(status_code=e.estado, content={'detalle': e.detalle})
        # el registro lleva cuántas herramientas y cuánto tardó, nunca la pregunta
        registrar(logging.INFO, 'asistente', evento='asistente', herramientas=len(r['herramientas']), pasos=r['pasos'], ms=r['latencia_ms'], llm=r['llm']['tipo'])
        return r
