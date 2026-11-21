"""Los cinco ajustes de color: definición exacta, cómo aplicarlos y cómo muestrearlos.

Un «ajuste» es un número que cambia el color de toda la foto. Como los
aplicamos nosotros, conocemos la respuesta correcta de cada foto editada:
así se fabrican los datos de entrenamiento.
"""
from __future__ import annotations

import json

import numpy as np
from PIL import Image

# Cada ajuste tiene un rango de muestreo y un valor «neutro» (no cambia nada).
AJUSTES = {
    #  nombre        (mínimo, máximo, neutro)
    "exposicion": (-0.7, 0.7, 0.0),   # pasos de diafragma: multiplica por 2**e
    "temperatura": (-1.0, 1.0, 0.0),  # >0 más cálida (más rojo, menos azul)
    "tinte": (-1.0, 1.0, 0.0),        # >0 más magenta (menos verde), <0 más verde
    "contraste": (0.6, 1.5, 1.0),     # factor alrededor del gris medio 0.5
    "saturacion": (0.2, 1.8, 1.0),    # 0 = blanco y negro, 1 = igual
}
NOMBRES = list(AJUSTES)
NEUTRO = {k: v[2] for k, v in AJUSTES.items()}


def aplicar_ajustes(img: Image.Image, p: dict) -> Image.Image:
    """Aplica los cinco ajustes, en este orden, sobre RGB en [0, 1].

    1. exposición:   x = x * 2**e
    2. temperatura:  R = R * (1 + 0.25 t);  B = B * (1 - 0.25 t)
    3. tinte:        G = G * (1 - 0.20 g)
    4. contraste:    x = (x - 0.5) * c + 0.5
    5. saturación:   Y = 0.299 R + 0.587 G + 0.114 B;  x = Y + (x - Y) * s
    y al final se recorta a [0, 1].
    """
    x = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    x = x * (2.0 ** p["exposicion"])
    x[..., 0] *= 1 + 0.25 * p["temperatura"]
    x[..., 2] *= 1 - 0.25 * p["temperatura"]
    x[..., 1] *= 1 - 0.20 * p["tinte"]
    x = (x - 0.5) * p["contraste"] + 0.5
    y = (0.299 * x[..., 0] + 0.587 * x[..., 1] + 0.114 * x[..., 2])[..., None]
    x = y + (x - y) * p["saturacion"]
    x = np.clip(x, 0.0, 1.0)
    return Image.fromarray((x * 255.0 + 0.5).astype(np.uint8))


def muestrear_ajustes(rng: np.random.Generator) -> dict:
    """Ajustes aleatorios uniformes dentro de cada rango, redondeados a 2 decimales.

    Con la misma semilla (``np.random.default_rng(semilla)``) salen siempre los mismos.
    """
    return {k: round(float(rng.uniform(lo, hi)), 2) for k, (lo, hi, _) in AJUSTES.items()}


def a_json(p: dict) -> str:
    """Texto JSON compacto que el modelo de visión tiene que aprender a escribir."""
    return json.dumps({k: round(float(p[k]), 2) for k in NOMBRES}, ensure_ascii=False)


def recortar_a_rango(p: dict) -> dict:
    """Limita cada ajuste a su rango (una predicción no puede salirse de él)."""
    return {k: float(np.clip(p[k], AJUSTES[k][0], AJUSTES[k][1])) for k in NOMBRES}
