"""Un agente en 100 líneas: un bucle con un LLM dentro.

    pregunta ──► [ LLM decide ] ──► ¿pide una herramienta? ──sí──► se ejecuta ──► el resultado vuelve al LLM ──┐
                      ▲                      │ no                                                                │
                      └──────────────────────┼───────────────────────────────────────────────────────────────────┘
                                             ▼
                                      respuesta final

Piezas (cada una en su archivo):
    llm.py      el LLM (Ollama real o el falso de las pruebas): `llm.chat(mensajes, tools)`
    cajas.py    las herramientas (en memoria o por MCP): `caja.listar()` y `caja.llamar(nombre, args)`
    skills.py   el saber hacer del negocio, en SKILL.md; se carga solo cuando hace falta

Reglas del bucle (lo que lo hace seguro):
    - máximo de pasos: un LLM puede dar vueltas para siempre; aquí se corta;
    - un error de herramienta NO rompe el agente: vuelve al LLM como observación y decide qué hacer;
    - una herramienta que no existe o con argumentos que no cumplen su esquema se rechaza (también como observación).

Uso:   python -m ia_mlops.agente.agente "Dame los 5 clientes a los que llamar hoy"
"""
import argparse
import json
from contextlib import contextmanager
from dataclasses import dataclass, field

from . import skills as modulo_skills

SISTEMA = ('Eres el asistente de retención de un negocio minorista. Respondes en español. Usa las herramientas para obtener datos reales '
           'y no inventes cifras. No tienes herramienta para datos personales (correo, nombre, teléfono) ni puedes conceder descuentos '
           'ni condiciones comerciales: si te lo piden, dilo y no llames a ninguna herramienta.')
USAR_SKILL = {'type': 'function', 'function': {
    'name': 'usar_skill', 'description': 'Carga las instrucciones completas de una skill del catálogo.',
    'parameters': {'type': 'object', 'properties': {'nombre': {'type': 'string'}}, 'required': ['nombre']}}}
_TIPOS = {'integer': int, 'number': (int, float), 'string': str, 'boolean': bool, 'array': list, 'object': dict}


@dataclass
class Respuesta:
    texto: str
    herramientas: list = field(default_factory=list)       # herramientas ejecutadas, en orden (con repeticiones)
    pasos: int = 0                                          # veces que se preguntó al LLM
    terminado: bool = True                                  # False si se cortó por el límite de pasos
    skills: list = field(default_factory=list)              # skills activadas por la pregunta


# ------------------------------------------------------------------------------------------------ trazas (MLflow)
class _SinTraza:
    def set_inputs(self, *_): pass
    def set_outputs(self, *_): pass


@contextmanager
def _span(activo, nombre, tipo, entradas):
    """Un tramo de la traza de MLflow (con su duración, entradas y salidas). Si las trazas están apagadas, no hace nada."""
    if not activo:
        yield _SinTraza()
        return
    import mlflow
    with mlflow.start_span(name=nombre, span_type=tipo) as sp:
        sp.set_inputs(entradas)
        yield sp


def _validar(args, esquema):
    """Comprueba los argumentos contra el JSON Schema de la herramienta. Devuelve el motivo del rechazo, o None si valen."""
    if not isinstance(args, dict):
        return 'Los argumentos deben ser un objeto JSON.'
    props = esquema.get('properties', {})
    for k in esquema.get('required', []):
        if k not in args:
            return f'Falta el argumento obligatorio «{k}».'
    for k, v in args.items():
        if k not in props:
            return f'Argumento desconocido «{k}». Admitidos: {sorted(props)}.'
        tipo = _TIPOS.get(props[k].get('type'))
        if tipo and (not isinstance(v, tipo) or (isinstance(v, bool) and tipo is not bool)):
            return f'El argumento «{k}» debe ser de tipo {props[k]["type"]} (llegó {v!r}).'
    return None


# ------------------------------------------------------------------------------------------------ el agente
class Agente:
    def __init__(self, llm, caja, skills=None, max_pasos=6, trazas=False, max_observacion=8000, sistema=None):
        self.llm, self.caja, self.skills = llm, caja, skills or {}      # skills: lo que devuelve skills.cargar_skills()
        self.max_pasos, self.trazas, self.max_observacion = max_pasos, trazas, max_observacion
        self.sistema = sistema or SISTEMA       # S5·T04: el prompt de sistema puede venir del registro de prompts de MLflow (registro.py)

    def ejecutar(self, pregunta):
        with _span(self.trazas, 'agente', 'AGENT', {'pregunta': pregunta}) as raiz:
            r = self._bucle(pregunta)
            raiz.set_outputs({'texto': r.texto, 'herramientas': r.herramientas, 'pasos': r.pasos})
            return r

    def _bucle(self, pregunta):
        activadas = modulo_skills.activadas(self.skills, pregunta)
        sistema = self.sistema                                              # 1. lo que el LLM sabe antes de empezar:
        if self.skills:
            sistema += '\n\nSkills disponibles (pide una con usar_skill si la necesitas):\n' + modulo_skills.catalogo(self.skills)
        for nombre in activadas:                                            #    las skills que la pregunta activa, ya cargadas
            sistema += f'\n\n## Skill «{nombre}» (obligatoria)\n{self.skills[nombre]["cuerpo"]}'
        tools = self.caja.listar() + ([USAR_SKILL] if self.skills else [])
        mensajes = [{'role': 'system', 'content': sistema}, {'role': 'user', 'content': pregunta}]
        usadas = []
        for paso in range(1, self.max_pasos + 1):
            with _span(self.trazas, f'paso_{paso}', 'LLM', {'mensajes': len(mensajes)}) as sp:
                respuesta = self.llm.chat(mensajes, tools)                  # 2. el LLM decide
                sp.set_outputs(respuesta)
            llamadas = respuesta.get('tool_calls') or []
            if not llamadas:                                                # 3a. sin herramientas pedidas: es la respuesta final
                return Respuesta(respuesta.get('content') or '', usadas, paso, True, activadas)
            mensajes.append(respuesta)
            for c in llamadas:                                              # 3b. ejecutar cada herramienta y devolver lo observado
                observacion = self._usar_herramienta(c, tools, usadas)
                mensajes.append({'role': 'tool', 'tool_call_id': c['id'], 'content': observacion})
        return Respuesta(f'No he podido terminar en {self.max_pasos} pasos; paro aquí para no dar vueltas sin fin.',
                         usadas, self.max_pasos, False, activadas)

    def _usar_herramienta(self, llamada, tools, usadas):
        """Ejecuta UNA petición del LLM y devuelve siempre un texto (el resultado o el motivo del error)."""
        nombre = llamada['function']['name']
        esquemas = {t['function']['name']: t['function']['parameters'] for t in tools}
        with _span(self.trazas, nombre, 'TOOL', {'argumentos': llamada['function'].get('arguments')}) as sp:
            try:
                if nombre not in esquemas:
                    raise ValueError(f'Herramienta desconocida «{nombre}». Las disponibles son: {sorted(esquemas)}.')
                args = json.loads(llamada['function'].get('arguments') or '{}')
                if (motivo := _validar(args, esquemas[nombre])):
                    raise ValueError(motivo)
                usadas.append(nombre)
                if nombre == 'usar_skill':
                    resultado = self.skills[args['nombre']]['cuerpo'] if args['nombre'] in self.skills else \
                        f'No existe la skill «{args["nombre"]}». Hay: {sorted(self.skills)}.'
                else:
                    resultado = self.caja.llamar(nombre, args)
            except Exception as e:                                          # noqa: BLE001 - un fallo es una observación, no un cuelgue
                resultado = {'error': f'{type(e).__name__}: {e}'}
            texto = resultado if isinstance(resultado, str) else json.dumps(resultado, ensure_ascii=False, default=str)
            if len(texto) > self.max_observacion:
                texto = texto[:self.max_observacion] + ' …[recortado]'
            sp.set_outputs(texto)
            return texto


def principal(argv=None):
    from .cajas import CajaMCP
    from .llm import ClienteOllama
    p = argparse.ArgumentParser(description='Agente de retención con un LLM local y herramientas MCP.')
    p.add_argument('pregunta')
    p.add_argument('--max-pasos', type=int, default=6)
    p.add_argument('--trazas', action='store_true', help='registrar la conversación como traza de MLflow')
    p.add_argument('--sin-skills', action='store_true')
    a = p.parse_args(argv)
    skills = {} if a.sin_skills else modulo_skills.cargar_skills()
    with CajaMCP() as caja:
        r = Agente(ClienteOllama(), caja, skills, a.max_pasos, a.trazas).ejecutar(a.pregunta)
    print(r.texto)
    print(f'\n[herramientas: {r.herramientas or "ninguna"} · pasos: {r.pasos} · skills activadas: {r.skills or "ninguna"}]')


if __name__ == '__main__':
    principal()
