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

aviso "Buckets que Dataproc crea por su cuenta (dataproc-staging-… y dataproc-temp-…)"
# Dataproc sin servidor crea él solo DOS buckets por proyecto y región, que no son de crear.sh (visto el 26/11/2026: seguían vivos,
# con restos del lote, tras borrar la práctica). Son compartidos por todo el Dataproc del proyecto: se borran SOLO si ya no queda
# ningún lote ni clúster de Dataproc en la región (nadie más los usa); si queda alguno, se dejan y se avisa.
OTROS_LOTES="$( { gcloud dataproc batches list --project "$PROYECTO" --region "$REGION_SPARK" --format 'value(name)' 2>/dev/null || true; } | grep -c . || true )"
CLUSTERES="$( { gcloud dataproc clusters list --project "$PROYECTO" --region "$REGION_SPARK" --format 'value(clusterName)' 2>/dev/null || true; } | grep -c . || true )"
if [ "$OTROS_LOTES" = "0" ] && [ "$CLUSTERES" = "0" ]; then
  BUCKETS_DATAPROC="$(gcloud storage buckets list --project "$PROYECTO" --format 'value(name)' | grep -E "^dataproc-(staging|temp)-${REGION_SPARK}-" || true)"
  if [ -n "$BUCKETS_DATAPROC" ]; then
    for B in $BUCKETS_DATAPROC; do
      echo "Borro gs://$B"
      gcloud storage rm -r "gs://$B" --project "$PROYECTO"
    done
  else
    echo "No hay buckets de Dataproc (nada que borrar)."
  fi
else
  echo "Quedan lotes ($OTROS_LOTES) o clústeres ($CLUSTERES) de Dataproc: no toco sus buckets."
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
gcloud storage buckets list --project "$PROYECTO" --format 'value(name)' | grep -E "$NOMBRE_BUCKET|^dataproc-(staging|temp)-" || echo "(ningun bucket de la practica ni de Dataproc)"
