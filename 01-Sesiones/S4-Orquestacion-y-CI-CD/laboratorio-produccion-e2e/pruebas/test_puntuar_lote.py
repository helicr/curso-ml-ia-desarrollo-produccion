"""Prueba estática de puntuar-lote.yml (sin red, sin Docker, sin ejecutar nada).

Nota: PyYAML lee la clave `on` como el booleano True, por eso se busca con ambas.
Ejecutar:  python -m pytest -q 01-Sesiones/S4-Orquestacion-y-CI-CD/laboratorio-produccion-e2e/pruebas
"""
import re
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
RUTA = RAIZ / "puntuar-lote.yml"
GRAFO = {"datos": set(), "puntuar": {"datos"}, "resumen": {"puntuar"}}


def _wf():
    return yaml.safe_load(RUTA.read_text(encoding="utf-8"))


def _on(wf):
    return wf[True] if True in wf else wf["on"]


def _needs(job):
    n = job.get("needs", [])
    return {n} if isinstance(n, str) else set(n)


def _pasos(wf):
    for nombre, job in wf["jobs"].items():
        for paso in job["steps"]:
            yield nombre, paso


def test_yaml_valido_y_cabecera_con_ruta_destino():
    wf = _wf()
    assert wf["name"] == "Puntuar por lotes"
    cabecera = "\n".join(RUTA.read_text(encoding="utf-8").splitlines()[:8])
    assert ".github/workflows/puntuar-lote.yml" in cabecera


def test_disparadores():
    on = _on(_wf())
    assert set(on) == {"schedule", "workflow_dispatch", "push"}
    crons = [s["cron"] for s in on["schedule"]]
    assert len(crons) == 1
    minuto, hora, dia, mes, semana = crons[0].split()
    assert (dia, mes, semana) == ("*", "*", "*")            # diario (decisión D5)
    assert minuto.isdigit() and hora.isdigit() and 0 <= int(hora) <= 23
    assert minuto != "0"                                     # no a la hora en punto: GitHub va cargado
    assert on["push"]["branches"] == ["lab/**"]
    assert set(on["push"]["paths"]) == {".github/workflows/puntuar-lote.yml", "04-Proyecto-Base/ia_mlops/explotacion.py"}


def test_entradas_de_la_ejecucion_a_mano():
    entradas = _on(_wf())["workflow_dispatch"]["inputs"]
    assert {"capacidad", "corte", "imagen"} <= set(entradas)
    assert entradas["capacidad"]["default"] == "0.10"
    assert entradas["corte"]["default"] == ""
    assert entradas["imagen"]["type"] == "choice" and entradas["imagen"]["options"] == ["construir", "ghcr"]
    assert entradas["imagen"]["default"] == "construir"


def test_el_comentario_avisa_de_los_limites_del_schedule():
    texto = RUTA.read_text(encoding="utf-8")
    assert "FORK" in texto and "DESACTIVADOS" in texto
    assert "RETRASAR" in texto
    assert "UTC" in texto


def test_permisos_minimos():
    wf = _wf()
    assert wf["permissions"] == {"contents": "read"}
    for job in wf["jobs"].values():
        assert "permissions" not in job                      # nadie pide más que el mínimo


def test_cada_job_con_timeout():
    for nombre, job in _wf()["jobs"].items():
        assert isinstance(job.get("timeout-minutes"), int) and 0 < job["timeout-minutes"] <= 30, nombre


def test_grafo_needs_exacto():
    jobs = _wf()["jobs"]
    assert set(jobs) == set(GRAFO)
    for nombre, esperado in GRAFO.items():
        assert _needs(jobs[nombre]) == esperado, nombre


def test_las_descargas_tienen_su_subida_en_un_job_anterior():
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
    assert set(subidas) == {"datos-y-modelo", "campana", "base-fs-produccion"}
    bajadas = 0
    for nombre, paso in _pasos(wf):
        if str(paso.get("uses", "")).startswith("actions/download-artifact"):
            bajadas += 1
            art = paso["with"]["name"]
            assert art in subidas, art
            assert subidas[art] & anteriores(nombre), (nombre, art)
    assert bajadas == 3


def test_artefactos_de_la_campana_y_de_la_base():
    pasos = {p["with"]["name"]: p["with"] for n, p in _pasos(_wf()) if str(p.get("uses", "")).startswith("actions/upload-artifact")}
    campana = pasos["campana"]["path"]
    assert re.search(r"campana_\$\{\{ steps\.puntuar\.outputs\.corte \}\}\.csv", campana)
    assert re.search(r"campana_\$\{\{ steps\.puntuar\.outputs\.corte \}\}\.json", campana)
    assert "data/processed/curso.db" in pasos["base-fs-produccion"]["path"]
    assert "data/processed/curso.db" in pasos["datos-y-modelo"]["path"] and "models/" in pasos["datos-y-modelo"]["path"]
    # el id de paso «puntuar» existe y publica el corte que usan las subidas
    puntuar = _wf()["jobs"]["puntuar"]["steps"]
    paso = next(p for p in puntuar if p.get("id") == "puntuar")
    assert 'echo "corte=' in paso["run"] and "GITHUB_OUTPUT" in paso["run"]


def test_datos_ejecuta_operacional_y_pipeline():
    run = "\n".join(str(p.get("run", "")) for p in _wf()["jobs"]["datos"]["steps"])
    assert "python -m ia_mlops.operacional" in run and "python -m ia_mlops.pipeline" in run


def test_puntuar_construye_como_validar_dos_contenedores_y_deja_la_via_ghcr():
    wf = _wf()
    run = "\n".join(str(p.get("run", "")) for p in wf["jobs"]["puntuar"]["steps"])
    assert "docker build -f deploy/docker/Dockerfile" in run
    assert "ghcr.io/" in run and "referencia" in run and "etiqueta_imagen" in run
    assert "docker pull" in run
    assert "python -m ia_mlops.explotacion" in run and "--url http://127.0.0.1:8080" in run
    assert "--capacidad" in run and "--corte" in run
    assert "--sin-guardar-fs" not in run                    # el lote SÍ escribe fs_produccion
    assert wf["env"]["IMAGEN"].endswith("|| 'construir' }}")  # sin entradas (schedule/push) construye


def test_las_entradas_pasan_por_variables_de_entorno_y_no_dentro_del_script():
    texto = RUTA.read_text(encoding="utf-8")
    cuerpo = "\n".join(str(p.get("run", "")) for _, p in _pasos(_wf()))
    assert "${{ inputs." not in cuerpo and "${{ github.event.inputs" not in cuerpo
    assert "inputs.capacidad" in texto and "inputs.corte" in texto and "inputs.imagen" in texto


def test_resumen_con_lo_que_pide_el_laboratorio():
    run = "\n".join(str(p.get("run", "")) for p in _wf()["jobs"]["resumen"]["steps"])
    assert "GITHUB_STEP_SUMMARY" in run
    for texto in ("Corte", "Clientes puntuados", "Campaña", "Probabilidad media", "huella", "models/referencia.json",
                  "fuera de rango", "fs_produccion"):
        assert texto in run, texto


def test_la_comprobacion_de_version_falla_con_ghcr_y_avisa_con_construir():
    run = "\n".join(str(p.get("run", "")) for p in _wf()["jobs"]["puntuar"]["steps"])
    assert "::error::" in run and "::warning::" in run and "sys.exit(1)" in run


def test_se_para_la_api_siempre():
    pasos = _wf()["jobs"]["puntuar"]["steps"]
    parar = next(p for p in pasos if "docker rm -f api" in str(p.get("run", "")))
    assert parar["if"] == "always()"
