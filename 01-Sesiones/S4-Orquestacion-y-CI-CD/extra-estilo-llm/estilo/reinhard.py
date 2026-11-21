"""Referencia clásica sin aprendizaje: Reinhard et al. (2001) en Lab."""
from __future__ import annotations

import numpy as np
from PIL import Image

from .metricas import a_lab


def reinhard(referencia: Image.Image, contenido: Image.Image) -> Image.Image:
    """Iguala media y desviación de cada canal Lab del contenido a las de la referencia."""
    from skimage.color import lab2rgb

    r, c = a_lab(referencia), a_lab(contenido)
    salida = (c - c.mean((0, 1))) / (c.std((0, 1)) + 1e-6) * r.std((0, 1)) + r.mean((0, 1))
    rgb = np.clip(lab2rgb(salida), 0, 1)
    return Image.fromarray((rgb * 255 + 0.5).astype(np.uint8))
