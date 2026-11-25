#!/usr/bin/env bash
# borrar-todo.sh - Donde: Cloud Shell. Ejecuta el borrar.sh de TODAS las practicas, de la ultima a la primera
# (la 02 usa la imagen de la 01, asi que la 01 va la ultima). Idempotente: si algo ya no existe, lo dice y sigue.
# Al final lista lo que pueda quedar en el proyecto. No toca nada que no haya creado una practica.
set -uo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/comun.sh"

comprobar_entorno
FALLOS=()
for P in 05-vertex-llm 04-vertex-modelo 03-dataproc-spark 02-kubernetes-gke 01-docker-artifact-registry; do
  echo; echo "################ $P ################"
  if ! bash "$DIR/$P/borrar.sh"; then FALLOS+=("$P"); fi
done

aviso "Repaso final de lo que queda en $PROYECTO (todo debe estar vacio)"
gcloud run services list --region "$REGION" --project "$PROYECTO" || true
gcloud container clusters list --project "$PROYECTO" || true
gcloud artifacts repositories list --location "$REGION" --project "$PROYECTO" || true
gcloud dataproc batches list --region "$REGION" --project "$PROYECTO" || true
gcloud ai endpoints list --region "$REGION_VERTEX" --project "$PROYECTO" || true
gcloud ai models list --region "$REGION_VERTEX" --project "$PROYECTO" || true
gcloud storage buckets list --project "$PROYECTO" --format 'value(name)' || true

if [ "${#FALLOS[@]}" -gt 0 ]; then
  echo; echo "ATENCION: han fallado estos borrar.sh: ${FALLOS[*]}. Repitelos uno a uno y lee el error." >&2
  exit 1
fi
echo; echo "Todas las practicas estan borradas."
