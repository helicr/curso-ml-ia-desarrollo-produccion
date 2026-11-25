#!/usr/bin/env bash
# borrar.sh (practica 05) - Donde: Cloud Shell. Idempotente. No hay recursos en GCP que borrar: solo se desinstala el SDK del entorno local.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/variables.sh"

aviso "Desinstalar $PAQUETE_SDK del entorno $VENV"
if [ -x "$VENV/bin/pip" ]; then
  "$VENV/bin/pip" uninstall -y "$PAQUETE_SDK" || true
else
  echo "No existe el entorno (nada que desinstalar)."
fi

aviso "Lo que queda en GCP por esta practica: nada (Gemini no crea recursos). Despliegues de Model Garden, si hiciste alguno a mano:"
comprobar_entorno
gcloud ai endpoints list --region "$REGION_VERTEX" --project "$PROYECTO" || true
