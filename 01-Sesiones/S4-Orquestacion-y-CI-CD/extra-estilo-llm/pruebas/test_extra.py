"""Pruebas rápidas del paquete ``estilo`` (sin red, sin descargar modelos, unos segundos).

Se ejecutan con:  pytest -q pruebas/test_extra.py
"""
import importlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import estilo  # noqa: E402
from estilo import ajustes, metricas, vlm  # noqa: E402

# «estilo.reinhard» y «estilo.estadisticas_color» también son nombres de funciones
# exportadas en __init__, así que los módulos se importan por su ruta completa.
estadisticas_color = importlib.import_module("estilo.estadisticas_color")
reinhard = importlib.import_module("estilo.reinhard")


def foto(semilla: int = 0, lado: int = 48) -> Image.Image:
    """Una imagen sintética con degradados y ruido (no hace falta ninguna foto real)."""
    rng = np.random.default_rng(semilla)
    base = np.linspace(0, 1, lado, dtype=np.float32)
    x = np.stack([np.outer(base, base), np.outer(base[::-1], base), np.outer(base, base[::-1])], axis=-1)
    x = 0.2 + 0.6 * x + 0.1 * rng.random((lado, lado, 3), dtype=np.float32)
    return Image.fromarray((np.clip(x, 0, 1) * 255).astype(np.uint8))


# --- ajustes -----------------------------------------------------------------
def test_ajustes_neutros_no_cambian_la_foto():
    img = foto()
    assert np.array_equal(np.asarray(ajustes.aplicar_ajustes(img, ajustes.NEUTRO)), np.asarray(img))


def test_muestreo_con_semilla_es_reproducible_y_esta_en_rango():
    a = ajustes.muestrear_ajustes(np.random.default_rng(7))
    b = ajustes.muestrear_ajustes(np.random.default_rng(7))
    assert a == b
    assert set(a) == set(ajustes.NOMBRES)
    for k, v in a.items():
        assert ajustes.AJUSTES[k][0] <= v <= ajustes.AJUSTES[k][1]


def test_json_aplicado_a_la_original_reproduce_la_editada(tmp_path):
    original = foto(1)
    real = ajustes.muestrear_ajustes(np.random.default_rng(42))
    editada = ajustes.aplicar_ajustes(original, real)
    # La editada se guarda y se vuelve a leer, como en las parejas del extra.
    editada.save(tmp_path / "editada.png")
    leida = Image.open(tmp_path / "editada.png").convert("RGB")
    # El JSON (2 decimales) aplicado a la original da exactamente la editada.
    desde_json = ajustes.aplicar_ajustes(original, json.loads(ajustes.a_json(real)))
    assert np.array_equal(np.asarray(desde_json), np.asarray(leida))


def test_recortar_a_rango():
    p = ajustes.recortar_a_rango({k: 99.0 for k in ajustes.NOMBRES})
    assert all(p[k] == ajustes.AJUSTES[k][1] for k in ajustes.NOMBRES)


# --- métricas ----------------------------------------------------------------
def test_ssim_de_una_imagen_consigo_misma_es_1():
    img = foto(2)
    assert metricas.ssim_contenido(img, img) == pytest.approx(1.0)


def test_delta_e_e_histogramas_de_una_imagen_consigo_misma_son_0():
    img = foto(3)
    assert metricas.delta_e(img, img) == pytest.approx(0.0)
    assert metricas.distancia_histogramas(img, img) == pytest.approx(0.0, abs=1e-6)


def test_delta_e_crece_si_cambia_el_color():
    img = foto(4)
    mas_calida = ajustes.aplicar_ajustes(img, dict(ajustes.NEUTRO, temperatura=1.0))
    assert metricas.delta_e(img, mas_calida) > 1.0


def test_mae_de_prediccion_perfecta_es_cero():
    reales = [ajustes.muestrear_ajustes(np.random.default_rng(s)) for s in range(5)]
    e = metricas.error_por_ajuste(reales, reales)
    assert e["mae_normalizado_medio"] == 0.0
    assert all(e[f"mae_{k}"] == 0.0 for k in ajustes.NOMBRES)


def test_mae_normalizado_usa_el_rango():
    reales = [dict(ajustes.NEUTRO)]
    pred = [dict(ajustes.NEUTRO, exposicion=0.14)]  # rango de exposición = 1.4
    e = metricas.error_por_ajuste(pred, reales)
    assert e["maen_exposicion"] == pytest.approx(0.1)


def test_porcentaje_json_valido():
    buena = ajustes.a_json(ajustes.NEUTRO)
    assert metricas.porcentaje_json_valido([buena, "no hay json", buena, "{}"]) == 0.5


# --- Reinhard ----------------------------------------------------------------
def test_reinhard_consigo_misma_casi_no_cambia_la_imagen():
    img = foto(5)
    salida = reinhard.reinhard(img, img)
    diferencia = np.abs(np.asarray(salida, dtype=float) - np.asarray(img, dtype=float))
    assert diferencia.mean() < 1.5  # niveles sobre 255 (ida y vuelta por Lab)
    assert metricas.delta_e(salida, img) < 1.0


# --- estadísticas de color ---------------------------------------------------
def test_estadisticas_de_color_tienen_longitud_fija_y_son_finitas():
    s = estadisticas_color.estadisticas_color(foto(6))
    # El código del pico produce 27 números (3+3+9 en Lab y 3+3+6 en RGB), aunque
    # el informe del pico las llame «33». Se fija la longitud real.
    assert s.shape == (estadisticas_color.N_ESTADISTICAS,) == (27,)
    assert np.all(np.isfinite(s))


def test_texto_de_estadisticas_menciona_cada_grupo():
    t = estadisticas_color.texto_estadisticas(foto(6))
    for trozo in ("Lab mean", "Lab std", "Lab p95", "RGB mean", "RGB p99"):
        assert trozo in t
    assert vlm.prompt_con_estadisticas(foto(6)).endswith(vlm.PROMPT_CORTO)


def test_ridge_color_aprende_y_predice_dentro_de_rango():
    fotos_base = [foto(s) for s in range(12)]
    reales = [ajustes.muestrear_ajustes(np.random.default_rng(s)) for s in range(12)]
    editadas = [ajustes.aplicar_ajustes(f, r) for f, r in zip(fotos_base, reales)]
    reg = estadisticas_color.ajustar_ridge_color(editadas, reales)
    pred = estadisticas_color.predecir_ridge_color(reg, editadas[:3])
    assert len(pred) == 3
    for p in pred:
        assert set(p) == set(ajustes.NOMBRES)
        for k, v in p.items():
            assert ajustes.AJUSTES[k][0] <= v <= ajustes.AJUSTES[k][1]


# --- vlm.py: parsear y que no cargue el modelo --------------------------------
def test_parsear_json_valido():
    p, ok = vlm.parsear('{"exposicion": 0.2, "temperatura": -0.5, "tinte": 0.1, "contraste": 1.2, "saturacion": 0.9}')
    assert ok
    assert p == {"exposicion": 0.2, "temperatura": -0.5, "tinte": 0.1, "contraste": 1.2, "saturacion": 0.9}


def test_parsear_json_con_texto_alrededor():
    r = ('Claro, aquí tienes: {"exposicion": 0.3, "temperatura": 0.4, "tinte": -0.2, '
         '"contraste": 1.1, "saturacion": 1.3} Espero que sirva.')
    p, ok = vlm.parsear(r)
    assert ok
    assert p["exposicion"] == 0.3 and p["saturacion"] == 1.3


def test_parsear_json_roto_pone_neutro_y_marca_fallo():
    p, ok = vlm.parsear("esto no es un json {{{")
    assert not ok
    assert p == {k: float(v) for k, v in ajustes.NEUTRO.items()}


def test_parsear_json_incompleto_recupera_lo_que_hay_y_recorta():
    p, ok = vlm.parsear('{"exposicion": 5, "temperatura": 0.5')
    assert not ok
    assert p["exposicion"] == 0.7  # recortado al máximo del rango
    assert p["contraste"] == 1.0  # lo que falta, en neutro


def test_vlm_se_importa_sin_cargar_el_modelo():
    for pesado in ("torch", "transformers", "peft"):
        if pesado in sys.modules:  # otro test o plugin ya lo importó: no se puede comprobar
            pytest.skip(f"{pesado} ya estaba importado")
    importlib.reload(vlm)
    assert all(m not in sys.modules for m in ("transformers", "peft"))
    assert callable(vlm.cargar_vlm) and "JSON" in vlm.PROMPT


# --- rutas -------------------------------------------------------------------
def test_carpeta_de_trabajo_sale_de_la_variable_de_entorno(tmp_path, monkeypatch):
    monkeypatch.setenv("ESTILO_TRABAJO", str(tmp_path / "t"))
    monkeypatch.setenv("HF_HOME", str(tmp_path / "hf"))
    assert estilo.carpeta_trabajo() == (tmp_path / "t").resolve()
    assert (tmp_path / "t").is_dir()


def test_el_paquete_no_tiene_rutas_fijas_de_windows():
    for archivo in (RAIZ / "estilo").glob("*.py"):
        texto = archivo.read_text(encoding="utf-8")
        assert "C:\\" not in texto and "C:/" not in texto, archivo.name
