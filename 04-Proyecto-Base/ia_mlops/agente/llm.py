"""Los LLM del agente: uno real (Ollama, en tu portátil) y uno falso (de guion, para las pruebas).

EL CONTRATO (lo único que el agente necesita saber de un LLM)
    llm.chat(mensajes, tools) -> mensaje del asistente

    mensajes   lista de {"role": "system" | "user" | "assistant" | "tool", "content": ...}   (formato chat completions de OpenAI)
    tools      lista de {"type": "function", "function": {"name", "description", "parameters": <JSON Schema>}}
    devuelve   {"role": "assistant", "content": "texto" | None, "tool_calls": [{"id", "type": "function",
                "function": {"name": "...", "arguments": "<JSON en texto>"}}]}      (sin "tool_calls" si responde con texto)

Ollama expone ese mismo formato en /v1/chat/completions, así que ClienteOllama es solo un POST. LLMFalso lo imita con un guion fijo:
así el bucle del agente se prueba rápido, sin red y siempre con el mismo resultado.
"""
import json
import os

import httpx

URL_POR_DEFECTO = 'http://127.0.0.1:11435/v1'
MODELO_POR_DEFECTO = 'hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF:Q4_K_M'     # el único del pico T00 con 10/10 en herramientas
SEMILLA = 42


class ClienteOllama:
    """Cliente HTTP mínimo de /v1/chat/completions. Temperatura 0 y semilla fija: misma pregunta, misma respuesta."""

    def __init__(self, base_url=None, modelo=None, temperatura=0, semilla=SEMILLA, timeout=600):
        self.base_url = (base_url or os.environ.get('CURSO_LLM_URL') or URL_POR_DEFECTO).rstrip('/')
        self.modelo = modelo or os.environ.get('CURSO_LLM_MODELO') or MODELO_POR_DEFECTO
        self.temperatura, self.semilla, self.timeout = temperatura, semilla, timeout

    def chat(self, mensajes, tools=None):
        cuerpo = {'model': self.modelo, 'messages': mensajes, 'temperature': self.temperatura, 'seed': self.semilla}
        if tools:
            cuerpo['tools'] = tools
        r = httpx.post(f'{self.base_url}/chat/completions', json=cuerpo, timeout=self.timeout)
        r.raise_for_status()
        return r.json()['choices'][0]['message']


def llamada(nombre, argumentos=None, id_=None):
    """Una petición de herramienta tal y como la devuelve un LLM (los argumentos viajan como JSON en texto)."""
    return {'id': id_ or f'llamada_{nombre}', 'type': 'function',
            'function': {'name': nombre, 'arguments': json.dumps(argumentos or {}, ensure_ascii=False)}}


class LLMFalso:
    """LLM de guion: en cada turno devuelve la siguiente respuesta de la lista.

    Cada elemento del guion es uno de:
        "texto"                          respuesta final
        ("herramienta", {"arg": 1})      una llamada a herramienta
        [("a", {...}), ("b", {...})]     varias llamadas en el mismo turno
        {...}                            un mensaje ya hecho, tal cual
    `repetir=True` vuelve a dar la última respuesta cuando el guion se acaba (para probar el límite de pasos).
    Guarda en `.llamadas` lo que recibió en cada turno (copia de mensajes y tools), para comprobarlo en las pruebas.
    """

    def __init__(self, guion, repetir=False):
        self.guion, self.repetir, self.llamadas = list(guion), repetir, []

    def chat(self, mensajes, tools=None):
        self.llamadas.append({'mensajes': json.loads(json.dumps(mensajes)), 'tools': tools})
        turno = len(self.llamadas) - 1
        if turno >= len(self.guion):
            if not (self.repetir and self.guion):
                raise RuntimeError(f'El guion del LLM falso se acabó en el turno {turno + 1}.')
            turno = len(self.guion) - 1
        paso = self.guion[turno]
        if isinstance(paso, dict):
            return paso
        if isinstance(paso, str):
            return {'role': 'assistant', 'content': paso}
        pedidas = [paso] if isinstance(paso, tuple) else paso
        return {'role': 'assistant', 'content': None,
                'tool_calls': [llamada(n, a, id_=f'llamada_{turno}_{i}') for i, (n, a) in enumerate(pedidas)]}
