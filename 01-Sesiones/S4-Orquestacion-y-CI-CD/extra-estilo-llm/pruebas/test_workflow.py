"""Prueba estática del workflow extra-estilo-llm.yml (sin red, sin modelos).

Nota: PyYAML lee la clave `on` como el booleano True, por eso se busca con ambas.
"""
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
RUTA = RAIZ / "extra-estilo-llm.yml"

# Grafo del §11 de la planificación.
GRAFO = {
    "pruebas": set(),
    "preparar": {"pruebas"},
    "datos": {"preparar"},
    "zero-shot": {"datos"},
    "lora": {"datos"},
    "base-y-reinhard": {"datos"},
    "explicar": {"datos"},  # acto 3, en paralelo con los otros tres
    "comparar": {"zero-shot", "lora", "base-y-reinhard"},
    "resumen": {"comparar", "explicar"},
}
NOTEBOOKS = {
    "00_preparar_entorno.ipynb",
    "01_datos_fabricados.ipynb",
    "02_zero_shot.ipynb",
    "03_fine_tuning_lora.ipynb",
    "04_comparar_y_transferir.ipynb",
    "05_explicar_estilo.ipynb",
}


def _wf():
    return yaml.safe_load(RUTA.read_text(encoding="utf-8"))


def _needs(job):
    n = job.get("needs", [])
    return {n} if isinstance(n, str) else set(n)


def _pasos(wf):
    for nombre, job in wf["jobs"].items():
        for paso in job["steps"]:
            yield nombre, paso


def test_cabecera_con_ruta_destino():
    texto = RUTA.read_text(encoding="utf-8")
    cabecera = "\n".join(texto.splitlines()[:15])
    assert ".github/workflows/extra-estilo-llm.yml" in cabecera


def test_nombre_y_disparadores():
    wf = _wf()
    assert wf["name"] == "Extra S4 · estilo de color con un LLM"
    on = wf[True] if True in wf else wf["on"]
    assert on["push"]["branches"] == ["lab/**"]
    assert "workflow_dispatch" in on
    entradas = on["workflow_dispatch"]["inputs"]
    assert {"n_ejemplos", "epocas"} <= set(entradas)


def test_permisos_minimos():
    assert _wf()["permissions"] == {"contents": "read"}


def test_cada_job_con_timeout():
    for nombre, job in _wf()["jobs"].items():
        assert isinstance(job.get("timeout-minutes"), int), nombre


def test_grafo_needs_exacto():
    jobs = _wf()["jobs"]
    assert set(jobs) == set(GRAFO)
    for nombre, esperado in GRAFO.items():
        assert _needs(jobs[nombre]) == esperado, nombre


def test_descargas_tienen_subida_previa():
    wf = _wf()
    jobs = wf["jobs"]

    def anteriores(nombre):
        vistos, pila = set(), list(_needs(jobs[nombre]))
        while pila:
            j = pila.pop()
            if j not in vistos:
                vistos.add(j)
                pila.extend(_needs(jobs[j]))
        return vistos

    subidas = {}
    for nombre, paso in _pasos(wf):
        if str(paso.get("uses", "")).startswith("actions/upload-artifact"):
            subidas.setdefault(paso["with"]["name"], set()).add(nombre)
    descargas = 0
    for nombre, paso in _pasos(wf):
        if str(paso.get("uses", "")).startswith("actions/download-artifact"):
            descargas += 1
            art = paso["with"]["name"]
            assert art in subidas, art
            assert subidas[art] & anteriores(nombre), (nombre, art)
    assert descargas >= 5


def test_artefactos_de_datos_se_bajan_y_los_notebooks_no():
    wf = _wf()
    subidos = {p["with"]["name"] for _, p in _pasos(wf) if str(p.get("uses", "")).startswith("actions/upload-artifact")}
    bajados = {p["with"]["name"] for _, p in _pasos(wf) if str(p.get("uses", "")).startswith("actions/download-artifact")}
    resultados = {a for a in subidos if not a.startswith("nb-")}
    assert resultados == bajados  # todo lo que se sube como dato se baja en algún job, y nada se baja sin subirse
    assert {"datos", "metricas-a", "adaptador-lora", "metricas-c-d", "explicacion", "comparacion"} <= bajados
    assert {"nb-05"} <= subidos


def test_explicar_acto_3():
    jobs = _wf()["jobs"]
    pasos = jobs["explicar"]["steps"]
    texto = "\n".join(str(p.get("run", "")) for p in pasos)
    assert "05_explicar_estilo.ipynb" in texto
    for parametro in ("N_FRASES", "EPOCAS", "FORMATO", "MODELO"):
        assert f"-p {parametro} " in texto, parametro
    # baja las parejas del job datos y sube el adaptador y las métricas como «explicacion»
    assert any(p.get("uses", "").startswith("actions/download-artifact") and p["with"]["name"] == "datos" for p in pasos)
    subida = [p for p in pasos if p.get("with", {}).get("name") == "explicacion"][0]["with"]["path"]
    for ruta in ("adaptador_explicacion", "metricas_explicacion.json", "explicaciones.jsonl"):
        assert ruta in subida, ruta
    nb = [p for p in pasos if p.get("with", {}).get("name") == "nb-05"][0]
    assert nb["if"] == "always()"


def test_explicar_en_el_resumen():
    wf = _wf()
    run = "\n".join(str(p.get("run", "")) for p in wf["jobs"]["resumen"]["steps"])
    assert "Acto 3 · explicar el estilo" in run
    for clave in ("pct_ajustes_sentido_correcto", "pct_frases_con_alucinacion", "pct_frases_perfectas", "metricas_explicacion.json"):
        assert clave in run, clave
    assert "A3" in run and "B3" in run
    assert "actos 1, 2 y 3" in run


def test_cache_del_tar_de_oxford_pet():
    wf = _wf()
    assert wf["env"]["ESTILO_TAR"].startswith("/tmp/")
    pasos = wf["jobs"]["datos"]["steps"]
    caches = [p for p in pasos if str(p.get("uses", "")).startswith("actions/cache@")]
    assert any("ESTILO_TAR" in str(c["with"]["path"]) for c in caches)
    # la caché va antes del notebook 01, que es quien lee ESTILO_TAR
    nombres = [str(p.get("name", "")) for p in pasos]
    i_cache = next(i for i, p in enumerate(pasos) if "ESTILO_TAR" in str(p.get("with", {}).get("path", "")))
    i_nb = next(i for i, n in enumerate(nombres) if "01_datos_fabricados" in n)
    assert i_cache < i_nb


def test_valores_por_defecto_y_timeouts_documentados():
    wf = _wf()
    on = wf[True] if True in wf else wf["on"]
    entradas = on["workflow_dispatch"]["inputs"]
    assert entradas["n_ejemplos"]["default"] == "60"
    assert entradas["epocas"]["default"] == "2"
    assert entradas["n_frases"]["default"] == "100"
    texto = RUTA.read_text(encoding="utf-8")
    assert "ajustar tras el run real" in texto


def test_notebooks_citados_son_los_seis():
    texto = RUTA.read_text(encoding="utf-8")
    import re

    citados = set(re.findall(r"\b\d\d_[a-z_]+\.ipynb", texto))
    # Las salidas de papermill (salidas/04_c_d.ipynb) no son entradas: se ignoran.
    citados -= {"04_c_d.ipynb"}
    assert citados == NOTEBOOKS


def test_notebook_ejecutado_se_sube_siempre():
    for nombre, paso in _pasos(_wf()):
        con = paso.get("with", {}) or {}
        if str(paso.get("uses", "")).startswith("actions/upload-artifact") and str(con.get("name", "")).startswith("nb-"):
            assert paso.get("if") == "always()", (nombre, con["name"])
