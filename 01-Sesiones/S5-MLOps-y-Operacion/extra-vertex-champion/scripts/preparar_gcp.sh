#!/usr/bin/env bash
# preparar_gcp.sh - Donde: Cloud Shell, UNA VEZ, con la cuenta del curso (la persona que administra el proyecto). SIN EJECUTAR todavía.
#
# Añade a lo que dejó preparar-gcp-s4.sh (cuenta de despliegue sa-github-despliegue + federación WIF con GitHub) lo que necesita ESTE extra:
#   · las APIs de Vertex AI y Artifact Registry;
#   · el repositorio de Artifact Registry REGIONAL donde se sube la imagen;
#   · permisos de la cuenta de despliegue: roles/aiplatform.user (subir el modelo, crear el endpoint, desplegar, predecir) y
#     roles/artifactregistry.writer (subir la imagen; ya lo tiene del laboratorio de S4);
#   · opcional, SOLO para el workflow vertex-borrar.yml: roles/artifactregistry.repoAdmin en ESE repositorio (borrar imágenes).
# NO crea modelos, endpoints ni cuentas nuevas, y no cobra nada por sí mismo.
# El agente de servicio de Vertex AI necesita roles/artifactregistry.reader para LEER la imagen: la documentación dice que es automático
# cuando la imagen es del MISMO proyecto (https://docs.cloud.google.com/vertex-ai/docs/predictions/custom-container-requirements).
# SIN VERIFICAR: que roles/aiplatform.user baste para todo (undeploy y borrar endpoint incluidos); si falla con PERMISSION_DENIED, el
#   mensaje dice qué permiso falta; la alternativa es roles/aiplatform.admin solo en el proyecto del curso, sabiendo que es más amplio.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/variables.sh"
SA_DESPLIEGUE="${CURSO_SA_DESPLIEGUE:-sa-github-despliegue}"
CUENTA="serviceAccount:$SA_DESPLIEGUE@$PROYECTO.iam.gserviceaccount.com"
CON_BORRADO=0
[ "${1:-}" = "--con-borrado" ] && CON_BORRADO=1

paso() { echo; echo "=== $*"; }
command -v gcloud >/dev/null 2>&1 || { echo "ERROR: ejecuta esto en Cloud Shell." >&2; exit 2; }
gcloud config set project "$PROYECTO" --quiet >/dev/null

paso "1 · APIs"
gcloud services enable aiplatform.googleapis.com artifactregistry.googleapis.com --project "$PROYECTO"

paso "2 · Repositorio de Artifact Registry ($REPO_AR, $REGION)"
if existe gcloud artifacts repositories describe "$REPO_AR" --location "$REGION" --project "$PROYECTO"; then
  echo "Ya existe."
else
  gcloud artifacts repositories create "$REPO_AR" --repository-format docker --location "$REGION" --project "$PROYECTO" \
    --description "Imagenes del curso ML e IA" --labels curso=ml-ia
fi

paso "3 · Permisos de $SA_DESPLIEGUE"
for ROL in roles/aiplatform.user roles/artifactregistry.writer; do
  gcloud projects add-iam-policy-binding "$PROYECTO" --member="$CUENTA" --role="$ROL" --condition=None --format='value(etag)' >/dev/null
  echo "  $ROL"
done
if [ "$CON_BORRADO" -eq 1 ]; then
  gcloud artifacts repositories add-iam-policy-binding "$REPO_AR" --location "$REGION" --project "$PROYECTO" \
    --member="$CUENTA" --role=roles/artifactregistry.repoAdmin --format='value(etag)' >/dev/null
  echo "  roles/artifactregistry.repoAdmin sobre el repositorio $REPO_AR (para vertex-borrar.yml)"
fi

paso "4 · Lo que va en GitHub (Settings > Secrets and variables > Actions > Variables; NO son secretos)"
NUMERO="$(gcloud projects describe "$PROYECTO" --format='value(projectNumber)')"
echo "GCP_PROYECTO=$PROYECTO"
echo "GCP_REGION=$REGION"
echo "GCP_PROVEEDOR_WIF=projects/$NUMERO/locations/global/workloadIdentityPools/github/providers/github"
echo "GCP_CUENTA_DESPLIEGUE=$SA_DESPLIEGUE@$PROYECTO.iam.gserviceaccount.com"
echo "GCP_REPO_AR=$REPO_AR"
echo; echo "FIN · todo listo (no se ha creado ningún modelo ni endpoint)"
