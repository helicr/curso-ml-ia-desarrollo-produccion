#!/usr/bin/env bash
# borrar.sh (practica 04) - Donde: Cloud Shell. Idempotente. Orden obligatorio: undeploy -> endpoint -> modelo -> bucket -> entornos y temporales.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/variables.sh"

comprobar_entorno

aviso "Endpoint $NOMBRE_ENDPOINT: undeploy de cada modelo desplegado y borrado"
if existe gcloud ai endpoints describe "$NOMBRE_ENDPOINT" --region "$REGION_VERTEX" --project "$PROYECTO"; then
  for ID in $(gcloud ai endpoints describe "$NOMBRE_ENDPOINT" --region "$REGION_VERTEX" --project "$PROYECTO" --format 'value(deployedModels[].id)' | tr ';,' '  '); do
    echo "undeploy del modelo desplegado $ID"
    gcloud ai endpoints undeploy-model "$NOMBRE_ENDPOINT" --region "$REGION_VERTEX" --project "$PROYECTO" --deployed-model-id "$ID" --quiet
  done
  gcloud ai endpoints delete "$NOMBRE_ENDPOINT" --region "$REGION_VERTEX" --project "$PROYECTO" --quiet
else
  echo "No existe (nada que borrar)."
fi

aviso "Modelo $NOMBRE_MODELO del Model Registry"
if existe gcloud ai models describe "$NOMBRE_MODELO" --region "$REGION_VERTEX" --project "$PROYECTO"; then
  gcloud ai models delete "$NOMBRE_MODELO" --region "$REGION_VERTEX" --project "$PROYECTO" --quiet
else
  echo "No existe (nada que borrar)."
fi

aviso "Bucket gs://$NOMBRE_BUCKET"
if existe gcloud storage buckets describe "gs://$NOMBRE_BUCKET" --project "$PROYECTO"; then
  gcloud storage rm -r "gs://$NOMBRE_BUCKET" --project "$PROYECTO"
else
  echo "No existe (nada que borrar)."
fi

aviso "Entorno scikit-learn 1.6 y temporales locales"
rm -rf "$VENV16" "$TRABAJO"

aviso "Lo que queda (debe estar vacio)"
gcloud ai endpoints list --region "$REGION_VERTEX" --project "$PROYECTO" || true
gcloud ai models list --region "$REGION_VERTEX" --project "$PROYECTO" || true
gcloud storage buckets list --project "$PROYECTO" --format 'value(name)' | grep "$NOMBRE_BUCKET" || echo "(ningun bucket $NOMBRE_BUCKET)"
