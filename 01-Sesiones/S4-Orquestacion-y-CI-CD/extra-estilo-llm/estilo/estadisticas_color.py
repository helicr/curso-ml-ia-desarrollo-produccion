"""C_color: estadísticas de color de la foto + una regresión Ridge (segundos, sin red neuronal)."""
from __future__ import annotations

import numpy as np
from PIL import Image

from .ajustes import NOMBRES, recortar_a_rango
from .metricas import a_lab

N_ESTADISTICAS = 27  # longitud del vector de estadisticas_color


def estadisticas_color(img: Image.Image) -> np.ndarray:
    """27 números que resumen el color: media, desviación y percentiles en Lab y RGB.

    Orden: Lab media (3), Lab desviación (3), Lab percentiles 5/50/95 (9),
    RGB media (3), RGB desviación (3), RGB percentiles 1/99 (6) = 27.
    (El estudio técnico las llamaba «33»; el código mide 27, y esas 27 son las que dieron
    los resultados de C_color.)
    """
    x = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    lab, rgb = a_lab(img).reshape(-1, 3), x.reshape(-1, 3)
    return np.concatenate([lab.mean(0), lab.std(0), np.percentile(lab, [5, 50, 95], axis=0).ravel(),
                           rgb.mean(0), rgb.std(0), np.percentile(rgb, [1, 99], axis=0).ravel()])


def texto_estadisticas(img: Image.Image) -> str:
    """Las mismas estadísticas redondeadas y escritas como texto (para ponerlas en el prompt del LLM).

    Lab tal cual y RGB multiplicado por 100, todo en enteros.
    """
    s = estadisticas_color(img)
    s = np.concatenate([s[:15], s[15:] * 100])
    q = [int(round(v)) for v in s]

    def g(i, n):
        return " ".join(map(str, q[i:i + n]))

    return (f"Lab mean {g(0, 3)}; Lab std {g(3, 3)}; Lab p5 {g(6, 3)}; Lab p50 {g(9, 3)}; Lab p95 {g(12, 3)}; "
            f"RGB mean {g(15, 3)}; RGB std {g(18, 3)}; RGB p1 {g(21, 3)}; RGB p99 {g(24, 3)}")


def ajustar_ridge_color(imagenes: list[Image.Image], ajustes: list[dict]):
    """Entrena la regresión Ridge (con su alfa elegido por validación cruzada) estadísticas -> ajustes."""
    from sklearn.linear_model import RidgeCV

    X = np.array([estadisticas_color(im) for im in imagenes])
    Y = np.array([[a[k] for k in NOMBRES] for a in ajustes])
    return RidgeCV(alphas=np.logspace(-3, 3, 13)).fit(X, Y)


def predecir_ridge_color(regresion, imagenes: list[Image.Image]) -> list[dict]:
    """Predice los cinco ajustes de cada foto (recortados a su rango)."""
    salida = regresion.predict(np.array([estadisticas_color(im) for im in imagenes]))
    return [recortar_a_rango(dict(zip(NOMBRES, fila))) for fila in salida]
