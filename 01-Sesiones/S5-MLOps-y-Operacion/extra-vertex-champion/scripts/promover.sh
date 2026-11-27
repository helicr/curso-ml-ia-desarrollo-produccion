#!/usr/bin/env bash
# promover.sh - Donde: Cloud Shell. Idempotente.   Uso:  scripts/promover.sh [--retirar-anterior] [--anotar-mlflow]
#
# QUE HACE: pasa la versión del manifiesto del canario al 100 % del tráfico del endpoint (`endpoints update --traffic-split`).
#   --retirar-anterior  espera ESPERA_RETIRAR segundos (600 = 10 min; la documentación recomienda 10-15 min tras mover el tráfico, para que
#                       terminen las peticiones en vuelo) y hace undeploy de las demás versiones: DEJAN DE COBRAR. Sin esta opción la
#                       anterior sigue desplegada con 0 % de tráfico (sirve para volver rápido) y SIGUE COBRANDO.
#   --anotar-mlflow     escribe en la versión de MLflow dónde está en Vertex (etiquetas vertex_*): cierra el enlace en la otra dirección.
# Fuente: https://docs.cloud.google.com/vertex-ai/docs/predictions/undeploy-model  (espera de 10-15 min)
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/variables.sh"
RETIRAR=0; ANOTAR=0
while [ $# -gt 0 ]; do
  case "$1" in
    --retirar-anterior) RETIRAR=1; shift ;;
    --anotar-mlflow) ANOTAR=1; shift ;;
    *) echo "Opción desconocida: $1 (uso: scripts/promover.sh [--retirar-anterior] [--anotar-mlflow])" >&2; exit 2 ;;
  esac
done

comprobar_entorno
exigir_manifiesto
ALIAS_VERSION="$(mf alias_vertex)"

aviso "1. Pasar $ALIAS_VERSION al 100 % del tráfico"
guardar_endpoint
ID_NUEVO="$(ayuda desplegado --json "$TRABAJO/endpoint.json" --nombre "$ALIAS_VERSION")"
[ -n "$ID_NUEVO" ] || { echo "ERROR: $ALIAS_VERSION no está desplegada en $NOMBRE_ENDPOINT: ejecuta scripts/desplegar.sh." >&2; exit 1; }
REPARTO="$(ayuda split-solo --json "$TRABAJO/endpoint.json" --id "$ID_NUEVO")"
echo "Reparto: $REPARTO"
gcloud ai endpoints update "$NOMBRE_ENDPOINT" --project "$PROYECTO" --region "$REGION" --traffic-split "$REPARTO"
guardar_endpoint
ayuda trafico --json "$TRABAJO/endpoint.json"

if [ "$ANOTAR" -eq 1 ]; then
  aviso "2. Enlace en MLflow (etiquetas vertex_*)"
  guardar_versiones
  "$PY" "$DIR_EXTRA/manifiesto_champion.py" anotar --manifiesto "$MANIFIESTO" --vertex-modelo "$NOMBRE_MODELO" \
    --vertex-version "$(ayuda version-modelo --json "$TRABAJO/versiones.json" --alias "$ALIAS_VERSION")" \
    --endpoint "$NOMBRE_ENDPOINT" --deployed-model-id "$ID_NUEVO" --region "$REGION"
fi

if [ "$RETIRAR" -eq 1 ]; then
  aviso "3. Retirar las demás versiones (espero $ESPERA_RETIRAR s)"
  sleep "$ESPERA_RETIRAR"
  for ID in $(ayuda ids --json "$TRABAJO/endpoint.json"); do
    [ "$ID" = "$ID_NUEVO" ] && continue
    echo "undeploy del modelo desplegado $ID"
    gcloud ai endpoints undeploy-model "$NOMBRE_ENDPOINT" --project "$PROYECTO" --region "$REGION" --deployed-model-id "$ID" --quiet
  done
else
  echo; echo "La versión anterior (si la hay) sigue desplegada con 0 % y SIGUE COBRANDO. Retírala con  scripts/promover.sh --retirar-anterior  o borra todo con scripts/borrar.sh"
fi
