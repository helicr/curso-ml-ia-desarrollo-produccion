#!/usr/bin/env bash
# borrar.sh (practica 03) - Donde: Cloud Shell. Idempotente.
# Borra: el registro de los lotes de Dataproc, el bucket con todo su contenido, el rol que concedio crear.sh (solo si lo concedio el) y los temporales.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/variables.sh"

comprobar_entorno

aviso "Lotes de Dataproc ${PREFIJO_BATCH}-*"
for N in $(gcloud dataproc batches list --project "$PROYECTO" --region "$REGION_SPARK" --format 'value(name)' | grep -E "(^|/)${PREFIJO_BATCH}-" || true); do
  echo "Borro ${N##*/}"
  gcloud dataproc batches delete "${N##*/}" --project "$PROYECTO" --region "$REGION_SPARK" --quiet || echo "(no se pudo: ¿sigue en ejecucion? Cancelalo y repite)"
done

aviso "Bucket gs://$NOMBRE_BUCKET (y todo lo que contiene)"
if existe gcloud storage buckets describe "gs://$NOMBRE_BUCKET" --project "$PROYECTO"; then
  gcloud storage rm -r "gs://$NOMBRE_BUCKET" --project "$PROYECTO"
else
  echo "No existe (nada que borrar)."
fi

aviso "Rol $ROL_WORKER (solo si lo concedio crear.sh)"
if [ -f "$MARCA_ROL" ]; then
  CUENTA="$(cat "$MARCA_ROL")"
  gcloud projects remove-iam-policy-binding "$PROYECTO" --member "serviceAccount:$CUENTA" --role "$ROL_WORKER" --condition=None >/dev/null \
    && rm -f "$MARCA_ROL" && echo "Quitado $ROL_WORKER a $CUENTA."
else
  echo "Esta practica no concedio ningun rol: no se toca."
fi

aviso "Temporales locales"
rm -rf "$TRABAJO"

aviso "Lo que queda (debe estar vacio)"
gcloud dataproc batches list --project "$PROYECTO" --region "$REGION_SPARK" || true
gcloud storage buckets list --project "$PROYECTO" --format 'value(name)' | grep "$NOMBRE_BUCKET" || echo "(ningun bucket $NOMBRE_BUCKET)"
