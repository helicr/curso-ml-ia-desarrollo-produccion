#!/usr/bin/env bash
# comun.sh - nombres y funciones compartidos por las practicas de GCP de S4. Se carga con `source`; no se ejecuta solo.
#
# DONDE SE USA: Cloud Shell (bash) con el proyecto del curso. Nada de claves de cuentas de servicio: se usa la sesion de Cloud Shell.
# REGIONES (se pueden cambiar con variables de entorno antes de ejecutar un script):
#   CURSO_REGION         southamerica-west1 (Santiago): Artifact Registry, Cloud Run, GKE Autopilot, Cloud Storage, Dataproc, Vertex AI
#   CURSO_REGION_VERTEX  por defecto igual que CURSO_REGION. Fuente (Vertex AI, Model Registry y prediccion online con modelos propios,
#                        fila "Santiago, Chile"): https://docs.cloud.google.com/vertex-ai/docs/general/locations
#   CURSO_REGION_GEMINI  global. Gemini NO aparece en Santiago; el endpoint "global" cubre todo el mundo (sin garantia de region de
#                        procesamiento): https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/locations
#   Cloud Run (Santiago, Tier 2): https://docs.cloud.google.com/run/docs/locations
#   Artifact Registry (Santiago): https://docs.cloud.google.com/artifact-registry/docs/repositories/repo-locations
#   GKE y Cloud Storage figuran entre los productos de toda region nueva: https://cloud.google.com/about/locations
#   Dataproc sin servidor (batches) en Santiago: SIN VERIFICAR (la documentacion no lo lista por region); si falla, ver 03/README.md.

DIR_COMUN="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PROYECTO="${CURSO_PROYECTO:-project-curso-ml-ia}"
REGION="${CURSO_REGION:-southamerica-west1}"
REGION_VERTEX="${CURSO_REGION_VERTEX:-$REGION}"
REGION_GEMINI="${CURSO_REGION_GEMINI:-global}"
ETIQUETA="curso=ml-ia"

# Imagen de la API de retencion (practicas 01 y 02). Etiqueta FIJA, nunca latest.
NOMBRE_REPO="curso-ml-imagenes"
NOMBRE_IMAGEN="retencion-api"
ETIQUETA_IMAGEN="v1"
IMAGEN_COMPLETA="${REGION}-docker.pkg.dev/${PROYECTO}/${NOMBRE_REPO}/${NOMBRE_IMAGEN}:${ETIQUETA_IMAGEN}"

# El proyecto del caso (04-Proyecto-Base) esta en la raiz del repositorio: practicas-gcp/../../.. = raiz.
RAIZ_CURSO="$(cd "$DIR_COMUN/../../.." && pwd)"
DIR_PROYECTO="${CURSO_DIR_PROYECTO:-$RAIZ_CURSO/04-Proyecto-Base}"
VENV="${CURSO_VENV:-$HOME/.venv-curso-ml}"          # entorno Python del proyecto (scikit-learn de requirements-api.txt)
CLIENTES_EJEMPLO="$DIR_COMUN/clientes_ejemplo.json"

aviso() { echo; echo "== $*"; }

# Cloud Shell ya trae gcloud autenticado; solo se fija el proyecto.
comprobar_entorno() {
  command -v gcloud >/dev/null 2>&1 || { echo "ERROR: no encuentro gcloud. Ejecuta esto en Cloud Shell." >&2; exit 2; }
  gcloud config set project "$PROYECTO" --quiet >/dev/null 2>&1
  local activo
  activo="$(gcloud config get-value project 2>/dev/null || true)"
  [ "$activo" = "$PROYECTO" ] || { echo "ERROR: el proyecto activo es '$activo' y deberia ser '$PROYECTO'." >&2; exit 2; }
  echo "Proyecto: $PROYECTO | region: $REGION"
}

# Habilitar una API es gratis y NO se deshace al borrar (otras practicas la usan): queda anotado en el README.
habilitar_apis() {
  aviso "Habilitando APIs: $*"
  gcloud services enable "$@" --project "$PROYECTO"
}

# Genera (si faltan) la base curso.db y el modelo de 04-Proyecto-Base con SUS propios pipelines, en un entorno virtual aparte.
preparar_proyecto() {
  aviso "Preparando 04-Proyecto-Base (modelo y datos)"
  [ -d "$DIR_PROYECTO/ia_mlops" ] || { echo "ERROR: no encuentro $DIR_PROYECTO/ia_mlops (clona el repositorio del curso en Cloud Shell)." >&2; exit 2; }
  python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' \
    || { echo "ERROR: hace falta Python 3.11 o superior (requirements-api.txt fija numpy 2.4). Tienes: $(python3 --version)" >&2; exit 2; }
  if [ ! -x "$VENV/bin/python" ]; then python3 -m venv "$VENV"; fi
  if ! "$VENV/bin/python" -c "import mlflow, fastapi, sklearn" >/dev/null 2>&1; then
    "$VENV/bin/pip" install -q -r "$DIR_PROYECTO/requirements-api.txt" "mlflow==3.18.0"
  fi
  if [ ! -f "$DIR_PROYECTO/models/modelo_mlflow/MLmodel" ] || [ ! -f "$DIR_PROYECTO/models/modelo.joblib" ] \
     || [ ! -f "$DIR_PROYECTO/data/processed/curso.db" ]; then
    (cd "$DIR_PROYECTO" && "$VENV/bin/python" -m ia_mlops.operacional --fuente muestra && "$VENV/bin/python" -m ia_mlops.pipeline)
  else
    echo "Ya existen models/ y data/processed/curso.db: no se vuelve a entrenar."
  fi
}

# Comprueba que existe un recurso: usar como  if existe gcloud run services describe X ...; then
existe() { "$@" >/dev/null 2>&1; }
