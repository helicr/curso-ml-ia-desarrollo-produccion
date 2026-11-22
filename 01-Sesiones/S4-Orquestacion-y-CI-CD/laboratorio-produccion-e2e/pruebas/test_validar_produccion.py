"""Prueba estática de validar-produccion.yml y de compose-produccion.yaml (sin red, sin Docker, sin ejecutar nada).

Nota: PyYAML lee la clave `on` como el booleano True, por eso se busca con ambas.
Ejecutar:  python -m pytest -q 01-Sesiones/S4-Orquestacion-y-CI-CD/laboratorio-produccion-e2e/pruebas
"""
from pathlib import Path

import yaml

LAB = Path(__file__).resolve().parent.parent
RUTA_WF = LAB / "validar-produccion.yml"
RAIZ_CURSO = LAB.parents[2]
RUTA_COMPOSE = RAIZ_CURSO / "04-Proyecto-Base" / "deploy" / "docker" / "compose-produccion.yaml"


def _wf():
    return yaml.safe_load(RUTA_WF.read_text(encoding="utf-8"))


def _compose():
    return yaml.safe_load(RUTA_COMPOSE.read_text(encoding="utf-8"))


def _on(wf):
    return wf[True] if True in wf else wf["on"]


def _pasos(wf):
    return [p for job in wf["jobs"].values() for p in job["steps"]]


def _comandos(wf):
    return "\n".join(p.get("run", "") for p in _pasos(wf))


# ---------------------------------------------------------------------------------------------------------- compose
def test_compose_valido_con_los_dos_servicios():
    c = _compose()
    assert set(c["services"]) == {"api", "interfaz"}
    assert c["name"] == "retencion-produccion"


def test_api_sin_puertos_y_con_imagen_publicable():
    api = _compose()["services"]["api"]
    assert "ports" not in api, "la API no se publica fuera: solo la interfaz la llama, por su nombre"
    assert "build" in api, "por defecto se construye desde el repositorio"
    assert "${IMAGEN_API:-retencion-api:local}" in api["image"], "con IMAGEN_API se usa la imagen publicada en GHCR"


def test_interfaz_en_modo_demo_y_puerto_8090():
    i = _compose()["services"]["interfaz"]
    assert i["environment"]["CURSO_DEMO"] == "1"
    assert i["environment"]["CURSO_URL_API"] == "http://api:8080", "la API por nombre; 127.0.0.1 dentro del contenedor es la propia interfaz"
    assert i["environment"]["CURSO_CAMPANA"] == "/campana"
    assert "8090:8090" in i["ports"]


def test_volumenes_de_la_interfaz_son_de_solo_lectura():
    vols = _compose()["services"]["interfaz"]["volumes"]
    assert vols, "la interfaz monta la base y la campaña"
    for v in vols:
        assert v.endswith(":ro"), f"el volumen {v} debe ser de solo lectura"
    por_destino = {v.split(":")[1]: v for v in vols}
    assert por_destino["/datos"].startswith("../../data/processed:")
    assert por_destino["/campana"].startswith("../../reports/campana:")
    assert "/app/models/referencia.json" in por_destino
    assert "/app/models/historial_versiones.json" in por_destino


def test_la_copia_de_demo_tiene_donde_escribir():
    # El modo demo copia la base a un directorio temporal: /tmp en tmpfs es escribible para el usuario sin privilegios (uid 10001).
    assert "/tmp" in _compose()["services"]["interfaz"]["tmpfs"]


def test_interfaz_espera_a_que_la_api_este_sana():
    dep = _compose()["services"]["interfaz"]["depends_on"]
    assert dep["api"]["condition"] == "service_healthy"


def test_la_imagen_de_la_interfaz_incluye_los_archivos_nuevos():
    base = RAIZ_CURSO / "04-Proyecto-Base"
    ignore = (base / "deploy" / "docker" / "interfaz.Dockerfile.dockerignore").read_text(encoding="utf-8").splitlines()
    assert "!ia_mlops" in ignore, "todo ia_mlops entra en el contexto (modos.py y panel.py incluidos)"
    for f in ("modos.py", "panel.py"):
        assert (base / "ia_mlops" / "interfaz" / f).is_file()
    dockerfile = (base / "deploy" / "docker" / "interfaz.Dockerfile").read_text(encoding="utf-8")
    assert "COPY ia_mlops/ ia_mlops/" in dockerfile
    assert "USER 10001" in dockerfile


# --------------------------------------------------------------------------------------------------------- workflow
def test_yaml_valido_y_cabecera_con_ruta_destino():
    wf = _wf()
    assert wf["name"] == "Validar la producción completa"
    cabecera = "\n".join(RUTA_WF.read_text(encoding="utf-8").splitlines()[:12])
    assert ".github/workflows/validar-produccion.yml" in cabecera


def test_disparadores():
    on = _on(_wf())
    assert "workflow_dispatch" in on
    assert on["push"]["branches"] == ["lab/**"]
    rutas = on["push"]["paths"]
    assert "04-Proyecto-Base/ia_mlops/interfaz/**" in rutas
    assert "04-Proyecto-Base/deploy/docker/compose-produccion.yaml" in rutas
    assert ".github/workflows/validar-produccion.yml" in rutas


def test_permisos_minimos_y_timeout():
    wf = _wf()
    assert wf["permissions"] == {"contents": "read"}
    for job in wf["jobs"].values():
        assert 0 < job["timeout-minutes"] <= 30
        assert "permissions" not in job, "ningún job pide más permisos que los del workflow"


def test_prepara_datos_y_levanta_el_compose():
    cmd = _comandos(_wf())
    for orden in ("python -m ia_mlops.operacional", "python -m ia_mlops.pipeline", "python -m ia_mlops.explotacion"):
        assert orden in cmd
    assert cmd.index("ia_mlops.explotacion") < cmd.index("up --build -d"), "el lote va antes de levantar el compose"
    assert 'docker compose -f "$COMPOSE" up --build -d' in cmd
    assert _wf()["env"]["COMPOSE"] == "deploy/docker/compose-produccion.yaml"


def test_comprobaciones_con_curl():
    cmd = _comandos(_wf())
    for ruta in ("/listo", "/panel", "/panel/lote", "/bajo-demanda/", "/online/", "/demo/compra", "/panel/versiones"):
        assert ruta in cmd, f"falta comprobar {ruta}"
    assert "models/referencia.json" in cmd


def test_down_siempre_y_ultimo():
    pasos = _pasos(_wf())
    abajo = [p for p in pasos if "down" in p.get("run", "")]
    assert len(abajo) == 1 and abajo[0]["if"] == "always()"
    assert pasos[-1] is abajo[0]


def test_artefacto_y_resumen_aunque_algo_falle():
    pasos = _pasos(_wf())
    subir = [p for p in pasos if p.get("uses", "").startswith("actions/upload-artifact")]
    assert subir and subir[0]["if"] == "always()"
    resumen = [p for p in pasos if "GITHUB_STEP_SUMMARY" in p.get("run", "")]
    assert resumen and resumen[0]["if"] == "always()"


def test_sin_secretos_ni_rutas_personales():
    for ruta in (RUTA_WF, RUTA_COMPOSE):
        texto = ruta.read_text(encoding="utf-8")
        assert "secrets." not in texto and "C:\\" not in texto and "/Users/" not in texto
