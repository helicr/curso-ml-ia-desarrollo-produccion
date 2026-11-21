"""Métricas del extra: cuánto se equivoca cada versión y cuánto se parece el resultado.

- ``error_por_ajuste``: MAE de cada ajuste y normalizado por su rango (0 = perfecto).
- ``delta_e``: diferencia de color en Lab (CIEDE2000; ≈1 apenas se nota, >10 muy distinto).
- ``distancia_histogramas``: parecido de la distribución de color (0 = iguales).
- ``ssim_contenido``: conservación de la estructura de la foto (1 = idéntica).
- ``porcentaje_json_valido``: cuántas respuestas del modelo se pueden leer.
"""
from __future__ import annotations

import warnings

import numpy as np
from PIL import Image

from .ajustes import AJUSTES, NOMBRES

# Reinhard y otras conversiones pueden pedir colores fuera de sRGB; se recortan.
warnings.filterwarnings("ignore", message="Conversion from CIE-LAB")


def a_lab(img: Image.Image) -> np.ndarray:
    """La imagen en espacio Lab (alto x ancho x 3)."""
    from skimage.color import rgb2lab

    return rgb2lab(np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0)


def delta_e(img1: Image.Image, img2: Image.Image) -> float:
    """ΔE medio CIEDE2000 píxel a píxel (≈1 apenas visible, >10 muy distinto)."""
    from skimage.color import deltaE_ciede2000

    return float(np.mean(deltaE_ciede2000(a_lab(img1), a_lab(img2))))


def distancia_histogramas(img1: Image.Image, img2: Image.Image, bins: int = 32) -> float:
    """Distancia de Bhattacharyya media de los histogramas L, a y b (0 = iguales, 1 = disjuntos)."""
    a, b = a_lab(img1), a_lab(img2)
    rangos = [(0, 100), (-100, 100), (-100, 100)]
    d = []
    for c, r in enumerate(rangos):
        h1, _ = np.histogram(a[..., c], bins=bins, range=r)
        h2, _ = np.histogram(b[..., c], bins=bins, range=r)
        h1 = h1 / h1.sum()
        h2 = h2 / h2.sum()
        d.append(np.sqrt(max(0.0, 1.0 - np.sum(np.sqrt(h1 * h2)))))
    return float(np.mean(d))


def ssim_contenido(img: Image.Image, contenido: Image.Image) -> float:
    """SSIM en escala de grises entre el resultado y la foto de contenido (1 = misma estructura)."""
    from skimage.metrics import structural_similarity

    g1 = np.asarray(img.convert("L"), dtype=np.float32) / 255.0
    g2 = np.asarray(contenido.convert("L"), dtype=np.float32) / 255.0
    return float(structural_similarity(g1, g2, data_range=1.0))


def error_por_ajuste(pred: list[dict], real: list[dict]) -> dict:
    """Error medio absoluto de cada ajuste y su versión normalizada por el rango.

    Devuelve ``mae_<ajuste>``, ``maen_<ajuste>`` y ``mae_normalizado_medio``.
    """
    res = {}
    for k in NOMBRES:
        e = np.mean([abs(p[k] - r[k]) for p, r in zip(pred, real)])
        res[f"mae_{k}"] = float(e)
        res[f"maen_{k}"] = float(e / (AJUSTES[k][1] - AJUSTES[k][0]))
    res["mae_normalizado_medio"] = float(np.mean([res[f"maen_{k}"] for k in NOMBRES]))
    return res


def porcentaje_json_valido(respuestas: list[str]) -> float:
    """Fracción (0 a 1) de respuestas en las que se encuentran los cinco ajustes."""
    from .vlm import parsear

    return float(np.mean([parsear(r)[1] for r in respuestas]))


def ajustes_medios(filas: list[dict]) -> dict:
    """Media de cada ajuste en las parejas dadas: la versión «media» (contestar siempre lo mismo)."""
    return {k: float(np.mean([f["ajustes"][k] for f in filas])) for k in NOMBRES}
