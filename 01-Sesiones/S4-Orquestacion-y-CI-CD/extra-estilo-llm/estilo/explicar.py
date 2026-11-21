"""Acto 3: del JSON de ajustes a una explicación en español, y cómo medirla.

Aquí no hay ningún modelo: solo las **reglas** que fabrican la frase correcta
(``frase_objetivo``) y la **métrica automática** que dice si una frase escrita
por un LLM es correcta (``evaluar_frase``). Como la frase sale de reglas,
conocemos siempre la respuesta buena y podemos medir contra ella.

Regla de intensidad
-------------------
``intensidad = (valor - neutro) / (media anchura del rango)``. Va de -1 a 1.

* Si ``|intensidad| < 0,15`` el ajuste es «casi nulo» y **no se menciona**.
* Si ``|intensidad| < 0,5`` es «un poco»; si no, «bastante».
"""
from __future__ import annotations

import hashlib
import re

import numpy as np

from .ajustes import AJUSTES, NOMBRES, a_json

# Por debajo de UMBRAL_NULO el ajuste se ignora; por debajo de UMBRAL_BASTANTE es «un poco».
UMBRAL_NULO, UMBRAL_BASTANTE = 0.15, 0.5

#            (adjetivo si sube, adjetivo si baja, acción si sube, acción si baja)
FRASES = {
    "exposicion": ("más luminosa", "más oscura", "se sube {i} la exposición", "se baja {i} la exposición"),
    "temperatura": ("más cálida", "más fría", "se sube {i} la temperatura", "se baja {i} la temperatura"),
    "tinte": ("más magenta", "más verdosa", "se lleva el tinte {i} hacia el magenta", "se lleva el tinte {i} hacia el verde"),
    "contraste": ("con más contraste", "con menos contraste", "se sube {i} el contraste", "se baja {i} el contraste"),
    "saturacion": ("más saturada", "menos saturada", "se sube {i} la saturación", "se baja {i} la saturación"),
}

# Patrones para medir si una frase menciona cada ajuste y en qué sentido:
# (sube, baja, cualquier mención). _NO_CRUZAR impide saltar de una acción a la siguiente.
_NO_CRUZAR = r"(?:(?!\by\b|sube|baja|lleva|,|;|\.)[^\n]){0,25}"
PATRONES = {
    "exposicion": (rf"sube{_NO_CRUZAR}exposici|más luminos|más clar", rf"baja{_NO_CRUZAR}exposici|más oscur", r"exposici|luminos|oscur|\bclar"),
    "temperatura": (rf"sube{_NO_CRUZAR}temperatura|más cálid|más calid", rf"baja{_NO_CRUZAR}temperatura|más frí|más fri", r"temperatura|cálid|calid|frí|\bfria"),
    "tinte": (r"magenta", r"verd", r"tinte|magenta|verd"),
    "contraste": (rf"sube{_NO_CRUZAR}contraste|más contraste", rf"baja{_NO_CRUZAR}contraste|menos contraste", r"contraste"),
    "saturacion": (rf"sube{_NO_CRUZAR}saturaci|más saturad", rf"baja{_NO_CRUZAR}saturaci|menos saturad", r"saturaci|saturad"),
}


def intensidad(k: str, v: float) -> float:
    """Cuánto se aleja el valor ``v`` del ajuste ``k`` de su neutro, entre -1 y 1 (según el rango)."""
    lo, hi, n = AJUSTES[k]
    return (v - n) / ((hi - lo) / 2)


def ajustes_relevantes(p: dict) -> dict:
    """``{ajuste: +1 o -1}`` de los ajustes que no son casi nulos, en el orden fijo de ``NOMBRES``.

    +1 = el ajuste sube respecto al neutro; -1 = baja.
    """
    return {k: (1 if intensidad(k, p[k]) > 0 else -1) for k in NOMBRES if abs(intensidad(k, p[k])) >= UMBRAL_NULO}


def _unir(trozos: list) -> str:
    return trozos[0] if len(trozos) == 1 else ", ".join(trozos[:-1]) + " y " + trozos[-1]


def entrada_explicacion(p: dict, formato: str = "facil") -> str:
    """Texto que recibe el LLM para explicar los ajustes ``p``.

    * ``"json"``: el JSON tal cual. El modelo tiene que decidir él el sentido y la intensidad.
    * ``"facil"``: el sentido («sube» o «baja») y la intensidad («un poco» o «bastante») ya
      vienen calculados con las reglas; el modelo solo tiene que **redactar**.
    """
    if formato == "json":
        return "Ajustes: " + a_json(p)
    trozos = []
    for k in NOMBRES:
        x = intensidad(k, p[k])
        if abs(x) < UMBRAL_NULO:
            trozos.append(f"{k}: sin cambio")
        else:
            trozos.append(f"{k}: {'sube' if x > 0 else 'baja'} {'un poco' if abs(x) < UMBRAL_BASTANTE else 'bastante'}")
    return "Cambios: " + "; ".join(trozos)


def frase_objetivo(p: dict, clave: str) -> str:
    """La explicación correcta, fabricada con reglas (la respuesta que el LLM debería dar).

    Se ignoran los ajustes casi nulos, la intensidad decide «un poco» o «bastante» y el
    orden de los ajustes es fijo. Hay 3 plantillas de frase; la elige el hash de ``clave``
    (por ejemplo, el identificador de la foto), así la misma clave da siempre la misma frase.
    """
    rel = ajustes_relevantes(p)
    if not rel:
        return "La referencia apenas tiene ajustes de color: se deja la foto como está."
    adjs, acciones = [], []
    for k, s in rel.items():
        i = "un poco" if abs(intensidad(k, p[k])) < UMBRAL_BASTANTE else "bastante"
        adjs.append(FRASES[k][0 if s > 0 else 1])
        acciones.append(FRASES[k][2 if s > 0 else 3].format(i=i))
    plantilla = int(hashlib.md5(clave.encode()).hexdigest(), 16) % 3
    if plantilla == 0:
        return f"La referencia es {_unir(adjs)}: {_unir(acciones)}."
    if plantilla == 1:
        return f"Para copiar este estilo, {_unir(acciones)}."
    return f"Estilo {_unir(adjs)}. Cambios: {_unir(acciones)}."


_ESPANOL = re.compile(r"\b(se|la|el|más|menos|y|foto|referencia)\b", re.I)
_INGLES = re.compile(r"\b(the|is|and|image|photo|increase|decrease|color)\b", re.I)


def evaluar_frase(texto: str, p: dict) -> dict:
    """Mide una explicación frente a los ajustes reales ``p``, con expresiones regulares.

    Devuelve un diccionario con:

    * ``n_relevantes``: cuántos ajustes no son casi nulos (los que hay que mencionar).
    * ``aciertos``: cuántos de ellos menciona en el sentido correcto.
    * ``sentido_contrario``: cuántos menciona al revés (el error más grave).
    * ``alucinados``: ajustes casi nulos que la frase menciona igualmente (los inventa).
    * ``espanol_ok``: está en español y mide entre 20 y 300 caracteres.
    """
    t = texto.lower()
    rel = ajustes_relevantes(p)
    aciertos, contrario = 0, 0
    for k, s in rel.items():
        sube, baja, _ = PATRONES[k]
        ok = re.search(sube if s > 0 else baja, t) is not None
        aciertos += int(ok)
        contrario += int(not ok and re.search(baja if s > 0 else sube, t) is not None)
    alucinados = [k for k in NOMBRES if k not in rel and re.search(PATRONES[k][2], t)]
    return {"n_relevantes": len(rel), "aciertos": aciertos, "sentido_contrario": contrario, "alucinados": alucinados,
            "espanol_ok": bool(_ESPANOL.search(t)) and not _INGLES.search(t) and 20 <= len(texto) <= 300}


def resumir_frases(evaluaciones: list) -> dict:
    """Junta las evaluaciones de ``evaluar_frase`` de un conjunto de frases en cinco porcentajes.

    ``pct_ajustes_sentido_correcto``, ``pct_ajustes_sentido_contrario``,
    ``pct_frases_con_alucinacion``, ``pct_frases_espanol_longitud_ok`` y
    ``pct_frases_perfectas`` (todos los ajustes bien y ninguno inventado).
    """
    rel = sum(e["n_relevantes"] for e in evaluaciones) or 1
    return {"pct_ajustes_sentido_correcto": 100 * sum(e["aciertos"] for e in evaluaciones) / rel,
            "pct_ajustes_sentido_contrario": 100 * sum(e["sentido_contrario"] for e in evaluaciones) / rel,
            "pct_frases_con_alucinacion": 100 * float(np.mean([bool(e["alucinados"]) for e in evaluaciones])),
            "pct_frases_espanol_longitud_ok": 100 * float(np.mean([e["espanol_ok"] for e in evaluaciones])),
            "pct_frases_perfectas": 100 * float(np.mean([e["aciertos"] == e["n_relevantes"] and not e["alucinados"] for e in evaluaciones]))}
