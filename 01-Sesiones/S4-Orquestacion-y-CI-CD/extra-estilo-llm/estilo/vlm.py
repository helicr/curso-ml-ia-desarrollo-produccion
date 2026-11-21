"""El LLM de visión (SmolVLM): cargarlo, construir el prompt y leer su respuesta.

Importar este módulo NO carga ningún modelo: ``torch`` y ``transformers`` se
importan dentro de las funciones que los necesitan. La caché de Hugging Face
sale de ``HF_HOME`` (ver ``datos.carpeta_trabajo``).
"""
from __future__ import annotations

import json
import os
import re

from PIL import Image

from .ajustes import NEUTRO, NOMBRES, a_json, recortar_a_rango
from .estadisticas_color import texto_estadisticas

# Salidas limpias en los notebooks: sin barras de progreso.
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("TQDM_DISABLE", "1")

MODELO_POR_DEFECTO = "HuggingFaceTB/SmolVLM-256M-Instruct"

# Versión A (zero-shot): hay que explicar la tarea entera en el prompt.
PROMPT = (
    "Look at the colors of this photo. Estimate the color edits that were applied to it "
    "and answer ONLY with a JSON object with these keys: "
    '"exposicion" (exposure in stops, -0.7 to 0.7), '
    '"temperatura" (white balance, -1 cool/blue to 1 warm/orange), '
    '"tinte" (tint, -1 green to 1 magenta), '
    '"contraste" (contrast factor, 0.6 to 1.5, 1 = unchanged), '
    '"saturacion" (saturation factor, 0.2 to 1.8, 1 = unchanged).'
)

# Tras el fine-tuning ya no hace falta explicar la tarea: basta una orden corta
# (secuencias más cortas = entrenamiento e inferencia más rápidos).
PROMPT_CORTO = "Color edits as JSON."


def prompt_con_estadisticas(img: Image.Image, corto: bool = True) -> str:
    """Prompt con las estadísticas de color de la foto escritas en texto (variante 2c).

    ``corto=True`` (para LoRA): «Color statistics: ... Color edits as JSON.»
    ``corto=False`` (zero-shot): «Color statistics of this photo: ... » + el prompt largo.
    """
    est = texto_estadisticas(img)
    if corto:
        return f"Color statistics: {est}. {PROMPT_CORTO}"
    return f"Color statistics of this photo: {est}. {PROMPT}"


def cargar_vlm(modelo: str = MODELO_POR_DEFECTO, adaptador: str | os.PathLike | None = None):
    """Carga el procesador y el modelo (float32, CPU). Con ``adaptador`` carga además la LoRA entrenada.

    Devuelve ``(proc, vlm)``. La primera vez descarga ~500 MB a ``HF_HOME``.
    """
    import torch
    from transformers import AutoModelForImageTextToText, AutoProcessor
    from transformers.utils import logging as tlog

    tlog.disable_progress_bar()
    tlog.set_verbosity_error()
    proc = AutoProcessor.from_pretrained(modelo)
    vlm = AutoModelForImageTextToText.from_pretrained(modelo, dtype=torch.float32)
    if adaptador is not None:
        from peft import PeftModel

        vlm = PeftModel.from_pretrained(vlm, str(adaptador))
    vlm.eval()
    return proc, vlm


def texto_prompt(proc, prompt: str = PROMPT) -> str:
    """El prompt con la plantilla de chat del modelo (una imagen + el texto)."""
    mensajes = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": prompt}]}]
    return proc.apply_chat_template(mensajes, add_generation_prompt=True)


def entradas(proc, imagenes, textos):
    """Tensores de entrada. Sin trocear la imagen: una vista de 512 px = 64 «palabras» de imagen."""
    return proc(text=textos, images=[[im] for im in imagenes], return_tensors="pt",
                padding=True, do_image_splitting=False)


def preguntar(proc, vlm, imagen: Image.Image, max_tokens: int = 80, prompt: str = PROMPT,
              inicio: str = "") -> str:
    """Genera la respuesta. ``inicio`` permite «empezar» la respuesta por el modelo
    (p. ej. '{"exposicion":') para forzar el formato sin enseñarle nada."""
    import torch

    inp = entradas(proc, [imagen], [texto_prompt(proc, prompt) + inicio])
    with torch.no_grad():
        out = vlm.generate(**inp, max_new_tokens=max_tokens, do_sample=False)
    return (inicio + proc.batch_decode(out[:, inp["input_ids"].shape[1]:], skip_special_tokens=True)[0]).strip()


def preparar_ejemplo(proc, vlm, imagen: Image.Image, ajustes: dict) -> dict:
    """Tokeniza (prompt corto + respuesta) y calcula UNA vez los rasgos de imagen.

    Como el codificador de imagen y el conector están congelados, su salida no
    cambia durante el entrenamiento: calcularla una sola vez ahorra más de la
    mitad del tiempo de cada paso.
    """
    import torch

    prefijo = texto_prompt(proc, PROMPT_CORTO)
    completo = prefijo + " " + a_json(ajustes) + "<end_of_utterance>"
    inp = entradas(proc, [imagen], [completo])
    n_prefijo = entradas(proc, [imagen], [prefijo])["input_ids"].shape[1]
    ids = inp["input_ids"][0]
    etiquetas = ids.clone()
    etiquetas[:n_prefijo] = -100  # solo se aprende la respuesta, no el prompt
    with torch.no_grad():
        rasgos = vlm.model.get_image_features(inp["pixel_values"], inp["pixel_attention_mask"],
                                              return_dict=True).pooler_output[0]
    return {"ids": ids, "etiquetas": etiquetas, "rasgos": rasgos}


def lote(ejemplos: list[dict], pad_id: int) -> dict:
    """Junta ejemplos de distinta longitud rellenando por la derecha."""
    import torch
    from transformers.modeling_outputs import BaseModelOutputWithPooling

    n = max(len(e["ids"]) for e in ejemplos)
    ids = torch.full((len(ejemplos), n), pad_id, dtype=torch.long)
    mascara = torch.zeros((len(ejemplos), n), dtype=torch.long)
    etiquetas = torch.full((len(ejemplos), n), -100, dtype=torch.long)
    for i, e in enumerate(ejemplos):
        L = len(e["ids"])
        ids[i, :L], mascara[i, :L], etiquetas[i, :L] = e["ids"], 1, e["etiquetas"]
    rasgos = BaseModelOutputWithPooling(pooler_output=[e["rasgos"] for e in ejemplos])
    return {"input_ids": ids, "attention_mask": mascara, "labels": etiquetas,
            "mm_encoder_outputs": {"image": rasgos}}


_NUM = r"(-?\d+(?:\.\d+)?)"


def parsear(respuesta: str) -> tuple[dict, bool]:
    """Saca los cinco números de la respuesta.

    Devuelve ``(ajustes, completo)``. Si falta alguno, pone el valor neutro y
    ``completo`` = False. Acepta JSON con texto alrededor, números entre
    comillas y, como último recurso, pares «clave: número». El resultado se
    recorta al rango de cada ajuste.
    """
    p, completo = {}, True
    try:
        trozo = re.search(r"\{.*?\}", respuesta, re.S)
        datos = json.loads(trozo.group(0)) if trozo else {}
    except Exception:
        datos = {}
    for k in NOMBRES:
        v = datos.get(k) if isinstance(datos, dict) else None
        if isinstance(v, str) and re.fullmatch(r"\s*-?\d+(\.\d+)?\s*", v):
            v = float(v)  # aceptamos «"0.7"» (número entre comillas)
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            m = re.search(rf'"?{k}"?\s*:\s*"?{_NUM}"?\s*[,}}]', respuesta)
            v = float(m.group(1)) if m else None
        if v is None:
            completo = False
            v = NEUTRO[k]
        p[k] = float(v)
    return recortar_a_rango(p), completo
