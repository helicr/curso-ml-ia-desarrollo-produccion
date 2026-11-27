#!/usr/bin/env bash
# borrar.sh - Donde: Cloud Shell. Idempotente.   Uso:  scripts/borrar.sh [--con-repositorio] [--sin-imagenes]
#
# BORRA TODO LO QUE CREÓ ESTE EXTRA, en este orden obligatorio: undeploy de cada versión desplegada -> endpoint -> modelo (con sus versiones)
# -> imágenes de Artifact Registry -> temporales locales. Al final enseña lo que queda (debe estar vacío).
#   --con-repositorio  borra también el repositorio de Artifact Registry ($REPO_AR). OJO: si otras prácticas usan ese repositorio, NO lo pongas.
# No hay bucket que borrar: la imagen lleva el modelo dentro y al subirlo no se usa --artifact-uri. No toca los recursos de la práctica 04
# (retencion-90d-endpoint, retencion-90d-sklearn): tienen otros nombres; se borran con su propio borrar.sh.
# Fuentes: https://docs.cloud.google.com/vertex-ai/docs/predictions/undeploy-model
#          https://docs.cloud.google.com/sdk/gcloud/reference/artifacts/docker/images/delete
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/variables.sh"
CON_REPO=0; CON_IMAGENES=1
while [ $# -gt 0 ]; do
  case "$1" in
    --con-repositorio) CON_REPO=1; shift ;;
    --sin-imagenes) CON_IMAGENES=0; shift ;;
    *) echo "Opción desconocida: $1 (uso: scripts/borrar.sh [--con-repositorio] [--sin-imagenes])" >&2; exit 2 ;;
  esac
done

comprobar_entorno

aviso "Endpoint $NOMBRE_ENDPOINT: undeploy de cada versión desplegada y borrado"
if existe gcloud ai endpoints describe "$NOMBRE_ENDPOINT" --region "$REGION" --project "$PROYECTO"; then
  guardar_endpoint
  for ID in $(ayuda ids --json "$TRABAJO/endpoint.json"); do
    echo "undeploy del modelo desplegado $ID"
    gcloud ai endpoints undeploy-model "$NOMBRE_ENDPOINT" --region "$REGION" --project "$PROYECTO" --deployed-model-id "$ID" --quiet
  done
  gcloud ai endpoints delete "$NOMBRE_ENDPOINT" --region "$REGION" --project "$PROYECTO" --quiet
else
  echo "No existe (nada que borrar)."
fi

aviso "Modelo $NOMBRE_MODELO del Model Registry (todas sus versiones)"
if existe gcloud ai models describe "$NOMBRE_MODELO" --region "$REGION" --project "$PROYECTO"; then
  gcloud ai models delete "$NOMBRE_MODELO" --region "$REGION" --project "$PROYECTO" --quiet
else
  echo "No existe (nada que borrar)."
fi

aviso "Imágenes $NOMBRE_IMAGEN de Artifact Registry"
if [ "$CON_IMAGENES" -eq 0 ]; then
  echo "Omitido (--sin-imagenes)."
elif [ -n "$(gcloud artifacts docker images list "$REGISTRO_IMAGENES/$NOMBRE_IMAGEN" --project "$PROYECTO" --format 'value(version)' 2>/dev/null)" ]; then
  # Borrar imágenes necesita roles/artifactregistry.repoAdmin (la cuenta de despliegue solo tiene writer): si falta, no se detiene lo demás.
  gcloud artifacts docker images delete "$REGISTRO_IMAGENES/$NOMBRE_IMAGEN" --delete-tags --project "$PROYECTO" --quiet \
    || echo "AVISO: no se pudo borrar la imagen (¿falta roles/artifactregistry.repoAdmin?). Bórrala desde Cloud Shell con scripts/borrar.sh."
else
  echo "No existe (nada que borrar)."
fi
if [ "$CON_REPO" -eq 1 ]; then
  if existe gcloud artifacts repositories describe "$REPO_AR" --location "$REGION" --project "$PROYECTO"; then
    gcloud artifacts repositories delete "$REPO_AR" --location "$REGION" --project "$PROYECTO" --quiet
  fi
fi

aviso "Temporales locales"
rm -rf "$TRABAJO"

aviso "Lo que queda (debe estar vacío de recursos de este extra)"
gcloud ai endpoints list --region "$REGION" --project "$PROYECTO" || true
gcloud ai models list --region "$REGION" --project "$PROYECTO" || true
gcloud artifacts docker images list "$REGISTRO_IMAGENES" --project "$PROYECTO" 2>/dev/null | grep "$NOMBRE_IMAGEN" || echo "(ninguna imagen $NOMBRE_IMAGEN)"
