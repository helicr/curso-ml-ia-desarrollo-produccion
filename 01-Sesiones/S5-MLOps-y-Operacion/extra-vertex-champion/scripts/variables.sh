#!/usr/bin/env bash
# variables.sh (extra «champion de MLflow a Vertex AI»). Lo cargan todos los scripts: usan LOS MISMOS nombres.
# Donde: Cloud Shell (bash) con el proyecto del curso. Nada de claves de cuentas de servicio: se usa la sesión de Cloud Shell
# (o, en los workflows de GitHub Actions, la identidad federada WIF que deja `google-github-actions/auth`).
#
# Los nombres NO chocan con la práctica 04 de S4 (retencion-90d-sklearn / retencion-90d-endpoint): se pueden tener las dos a la vez.
# Cualquier valor se cambia con una variable de entorno ANTES de ejecutar (CURSO_PROYECTO, CURSO_REGION_VERTEX, CURSO_MAQUINA...).

DIR_SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIR_EXTRA="$(cd "$DIR_SCRIPTS/.." && pwd)"

PROYECTO="${CURSO_PROYECTO:-project-curso-ml-ia}"
# Santiago admite Model Registry y predicción online de modelos propios (fila «Santiago, Chile»):
# https://docs.cloud.google.com/vertex-ai/docs/general/locations
REGION="${CURSO_REGION_VERTEX:-southamerica-west1}"
# La imagen debe estar en un repositorio de Artifact Registry REGIONAL y de la misma región que el endpoint (no multirregional):
# https://docs.cloud.google.com/vertex-ai/docs/predictions/custom-container-requirements
REPO_AR="${CURSO_REPO_AR:-curso}"
NOMBRE_IMAGEN="retencion-vertex"
NOMBRE_MODELO="retencion-90d-champion"          # ID del modelo en el Model Registry; cada versión de MLflow es una VERSIÓN de este modelo
NOMBRE_ENDPOINT="retencion-90d-champion-ep"     # ID del endpoint
ALIAS_CHAMPION="champion"                       # alias de la versión de Vertex que corresponde al champion de MLflow

MAQUINA="${CURSO_MAQUINA:-e2-standard-2}"       # una de las de 2 vCPU de predicción online: https://docs.cloud.google.com/vertex-ai/docs/predictions/configure-compute
MIN_REPLICAS="${CURSO_MIN_REPLICAS:-1}"         # con dedicadas, mínimo 1 (la documentación de deploy-model no admite 0 en un despliegue normal)
MAX_REPLICAS="${CURSO_MAX_REPLICAS:-$MIN_REPLICAS}"
CANARIO="${CURSO_CANARIO:-10}"                  # % de tráfico que recibe la versión nueva al desplegarla (0 = directamente el 100 %)
ESPERA_RETIRAR="${CURSO_ESPERA_RETIRAR:-600}"   # segundos entre mover el tráfico y retirar la versión vieja (la documentación recomienda 10-15 min)

PUERTO=8080
RUTA_SALUD="/salud"
RUTA_PREDICT="/predict"

PY="${CURSO_PYTHON:-python3}"
TRABAJO="${CURSO_TRABAJO:-/tmp/curso-vertex-champion}"
MANIFIESTO="$TRABAJO/vertex-manifiesto.json"
CONTEXTO="$TRABAJO/build/vertex"
REGISTRO_IMAGENES="${REGION}-docker.pkg.dev/${PROYECTO}/${REPO_AR}"
RAIZ_CURSO="$(cd "$DIR_EXTRA/../../.." && pwd)"
DIR_PROYECTO="${CURSO_DIR_PROYECTO:-$RAIZ_CURSO/04-Proyecto-Base}"
export CURSO_DIR_PROYECTO="$DIR_PROYECTO"

# Git Bash (Windows) convierte un argumento como «/predict» en «C:/.../predict» al llamar a un programa de Windows (gcloud): se le dice que no
# toque estas dos rutas de la imagen. En Linux y en Cloud Shell no hace nada.
export MSYS2_ARG_CONV_EXCL="${MSYS2_ARG_CONV_EXCL:+$MSYS2_ARG_CONV_EXCL;}/predict;/salud"

aviso() { echo; echo "== $*"; }

# Comprueba que existe un recurso: usar como  if existe gcloud ai models describe X ...; then
existe() { "$@" >/dev/null 2>&1; }

comprobar_entorno() {
  command -v gcloud >/dev/null 2>&1 || { echo "ERROR: no encuentro gcloud. Ejecuta esto en Cloud Shell." >&2; exit 2; }
  command -v "$PY" >/dev/null 2>&1 || { echo "ERROR: no encuentro $PY (hace falta Python 3.11 o superior)." >&2; exit 2; }
  gcloud config set project "$PROYECTO" --quiet >/dev/null 2>&1
  local activo
  activo="$(gcloud config get-value project 2>/dev/null || true)"
  [ "$activo" = "$PROYECTO" ] || { echo "ERROR: el proyecto activo es '$activo' y debería ser '$PROYECTO'." >&2; exit 2; }
  mkdir -p "$TRABAJO"
  echo "Proyecto: $PROYECTO | región: $REGION | trabajo: $TRABAJO"
}

# Un campo del manifiesto (vertex-manifiesto.json): mf etiqueta_imagen
mf() { "$PY" "$DIR_EXTRA/manifiesto_champion.py" leer --manifiesto "$MANIFIESTO" "$1"; }
# Ayudante JSON (lee lo que guardó gcloud --format json)
ayuda() { "$PY" "$DIR_EXTRA/vertex_ayuda.py" "$@"; }

exigir_manifiesto() {
  [ -f "$MANIFIESTO" ] || { echo "ERROR: falta $MANIFIESTO. Ejecuta antes  scripts/subir_modelo.sh  (o  $PY manifiesto_champion.py generar --salida $MANIFIESTO)." >&2; exit 2; }
}

# Guarda el estado del endpoint en $TRABAJO/endpoint.json y del modelo en $TRABAJO/versiones.json
guardar_endpoint() {
  gcloud ai endpoints describe "$NOMBRE_ENDPOINT" --region "$REGION" --project "$PROYECTO" --format json > "$TRABAJO/endpoint.json"
}
guardar_versiones() {
  gcloud ai models list-version "$NOMBRE_MODELO" --region "$REGION" --project "$PROYECTO" --format json > "$TRABAJO/versiones.json"
}
