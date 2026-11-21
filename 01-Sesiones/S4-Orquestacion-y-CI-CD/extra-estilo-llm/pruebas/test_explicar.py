"""Pruebas del acto 3 (``estilo.explicar``): sin modelos, sin red, unos segundos.

Se ejecutan con:  pytest -q pruebas/test_explicar.py
"""
import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import estilo  # noqa: E402
from estilo import (NEUTRO, NOMBRES, entrada_explicacion, evaluar_frase, frase_objetivo,  # noqa: E402
                    muestrear_ajustes, resumir_frases)


def con(**cambios) -> dict:
    """Ajustes neutros con algunos valores cambiados."""
    p = dict(NEUTRO)
    p.update(cambios)
    return p


def test_json_neutro_no_menciona_ajustes():
    frase = frase_objetivo(dict(NEUTRO), "x")
    assert "apenas tiene ajustes" in frase
    assert evaluar_frase(frase, dict(NEUTRO))["alucinados"] == []
    assert evaluar_frase(frase, dict(NEUTRO))["n_relevantes"] == 0


def test_ajustes_casi_nulos_se_ignoran():
    # Intensidad de la exposición = 0,1 < 0,15: no se menciona.
    p = con(exposicion=0.07, temperatura=0.6)
    assert list(estilo.ajustes_relevantes(p)) == ["temperatura"]
    assert "exposici" not in frase_objetivo(p, "a").lower()


def test_frase_objetivo_es_perfecta_en_muchos_casos():
    rng = np.random.default_rng(1)
    evals = []
    for i in range(300):
        p = muestrear_ajustes(rng)
        evals.append(evaluar_frase(frase_objetivo(p, f"id_{i}"), p))
    r = resumir_frases(evals)
    assert r["pct_ajustes_sentido_correcto"] == 100
    assert r["pct_ajustes_sentido_contrario"] == 0
    assert r["pct_frases_con_alucinacion"] == 0
    assert r["pct_frases_espanol_longitud_ok"] == 100
    assert r["pct_frases_perfectas"] == 100


def test_frase_objetivo_es_determinista_y_usa_las_tres_plantillas():
    p = con(exposicion=0.5, temperatura=-0.8)
    assert frase_objetivo(p, "a") == frase_objetivo(p, "a")
    inicios = {frase_objetivo(p, f"id_{i}").split()[0] for i in range(40)}
    assert inicios == {"La", "Para", "Estilo"}


def test_sentido_invertido_se_detecta():
    p = con(exposicion=0.6)  # hay que subir la exposición
    e = evaluar_frase("Para copiar este estilo, se baja bastante la exposición.", p)
    assert e["aciertos"] == 0 and e["sentido_contrario"] == 1
    r = resumir_frases([e])
    assert r["pct_ajustes_sentido_contrario"] == 100
    assert r["pct_frases_perfectas"] == 0


def test_ajuste_inventado_cuenta_como_alucinacion():
    p = con(temperatura=0.7)  # solo la temperatura es relevante
    e = evaluar_frase("Para copiar este estilo, se sube bastante la temperatura y se sube un poco la saturación.", p)
    assert e["aciertos"] == 1 and e["alucinados"] == ["saturacion"]
    r = resumir_frases([e])
    assert r["pct_frases_con_alucinacion"] == 100
    assert r["pct_frases_perfectas"] == 0


def test_un_adjetivo_de_mas_tambien_es_alucinacion():
    p = con(temperatura=0.7)
    e = evaluar_frase("La referencia es más oscura y más cálida: se sube bastante la temperatura.", p)
    assert e["alucinados"] == ["exposicion"]


def test_frase_en_ingles_o_demasiado_corta_no_es_espanol_ok():
    p = con(temperatura=0.7)
    assert not evaluar_frase("Increase the temperature of the photo.", p)["espanol_ok"]
    assert not evaluar_frase("Se sube.", p)["espanol_ok"]


def test_entrada_facil_contiene_sentido_e_intensidad():
    p = con(exposicion=-0.6, temperatura=0.2, tinte=0.01)
    t = entrada_explicacion(p, "facil")
    assert t.startswith("Cambios: ")
    assert "exposicion: baja bastante" in t
    assert "temperatura: sube un poco" in t
    assert "tinte: sin cambio" in t
    assert all(f"{k}:" in t for k in NOMBRES)


def test_entrada_json_es_el_json_tal_cual():
    p = con(exposicion=-0.6)
    t = entrada_explicacion(p, "json")
    assert t.startswith("Ajustes: {") and '"exposicion": -0.6' in t
    assert "baja" not in t
