#!/usr/bin/env bash
# borrar.sh (practica 01) - Donde: Cloud Shell. Idempotente. Borra el servicio de Cloud Run, el repositorio (con su imagen) y la imagen local.
# Las APIs habilitadas se quedan habilitadas (no cuestan nada).
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/variables.sh"

comprobar_entorno

aviso "Cloud Run: $NOMBRE_SERVICIO"
if existe gcloud run services describe "$NOMBRE_SERVICIO" --region "$REGION" --project "$PROYECTO"; then
  gcloud run services delete "$NOMBRE_SERVICIO" --region "$REGION" --project "$PROYECTO" --quiet
else
  echo "No existe (nada que borrar)."
fi

aviso "Artifact Registry: $NOMBRE_REPO (borra tambien las imagenes que contiene)"
if existe gcloud artifacts repositories describe "$NOMBRE_REPO" --location "$REGION" --project "$PROYECTO"; then
  gcloud artifacts repositories delete "$NOMBRE_REPO" --location "$REGION" --project "$PROYECTO" --quiet
else
  echo "No existe (nada que borrar)."
fi

aviso "Imagen local de Cloud Shell"
if command -v docker >/dev/null 2>&1; then docker image rm -f "$IMAGEN_COMPLETA" >/dev/null 2>&1 || echo "No estaba."; fi

aviso "Lo que queda (debe estar vacio)"
gcloud run services list --region "$REGION" --project "$PROYECTO" || true
gcloud artifacts repositories list --location "$REGION" --project "$PROYECTO" || true
