#!/usr/bin/env bash
# volver.sh - Donde: Cloud Shell. Idempotente.   Uso:  scripts/volver.sh [--a-version N] [--sin-mlflow] [--retirar-actual]
#
# ROLLBACK: devuelve el tráfico del endpoint a la versión ANTERIOR de MLflow y, a la vez, mueve el alias champion de MLflow a ella
# (`python -m ia_mlops.alias_modelo volver`). Nada se borra: la versión que sale sigue en el Model Registry y en MLflow.
#   · La versión anterior es la que anotó el manifiesto al subir el modelo (etiqueta mlflow_version_anterior de la versión que sirve ahora),
#     o la que pidas con --a-version N (número de MLflow).
#   · Si esa versión sigue desplegada (con 0 % de tráfico) basta mover el tráfico: segundos. Si ya se retiró, se vuelve a DESPLEGAR desde el
#     Model Registry (varios minutos, sin medir) y se le da el 100 %.
#   --sin-mlflow      no toca el alias de MLflow (p. ej. en un workflow donde el registro no es el tuyo).
#   --retirar-actual  tras ESPERA_RETIRAR segundos hace undeploy de la versión mala: deja de cobrar.
# ¡COBRA! Mientras haya algo desplegado, el endpoint cobra. Precio: sin dato. Para dejarlo todo a cero: scripts/borrar.sh
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/variables.sh"
DESTINO=""; CON_MLFLOW=1; RETIRAR=0
while [ $# -gt 0 ]; do
  case "$1" in
    --a-version) DESTINO="${2:?falta el número de versión de MLflow}"; shift 2 ;;
    --sin-mlflow) CON_MLFLOW=0; shift ;;
    --retirar-actual) RETIRAR=1; shift ;;
    *) echo "Opción desconocida: $1 (uso: scripts/volver.sh [--a-version N] [--sin-mlflow] [--retirar-actual])" >&2; exit 2 ;;
  esac
done

comprobar_entorno
mkdir -p "$TRABAJO"
guardar_endpoint
guardar_versiones
ID_ACTUAL="$(ayuda actual --json "$TRABAJO/endpoint.json")"
[ -n "$ID_ACTUAL" ] || { echo "ERROR: no hay ningún modelo desplegado en $NOMBRE_ENDPOINT: no hay nada de lo que volver." >&2; exit 1; }
NOMBRE_ACTUAL="$(ayuda nombre-de --json "$TRABAJO/endpoint.json" --id "$ID_ACTUAL")"

aviso "1. A qué versión volver"
if [ -z "$DESTINO" ]; then
  DESTINO="$(ayuda etiqueta-de --json "$TRABAJO/versiones.json" --alias "$NOMBRE_ACTUAL" --clave mlflow_version_anterior)"
fi
[ -n "$DESTINO" ] || { echo "ERROR: $NOMBRE_ACTUAL no guardó una versión anterior: no hay a dónde volver. Si sabes cuál quieres: scripts/volver.sh --a-version N" >&2; exit 1; }
NOMBRE_DESTINO="mlflow-v$DESTINO"
echo "Sirve ahora: $NOMBRE_ACTUAL (modelo desplegado $ID_ACTUAL)  ->  vuelve a: $NOMBRE_DESTINO"
[ "$NOMBRE_ACTUAL" != "$NOMBRE_DESTINO" ] || { echo "Sin cambios: ya sirve $NOMBRE_DESTINO."; exit 0; }

aviso "2. Tráfico del endpoint"
ID_DESTINO="$(ayuda desplegado --json "$TRABAJO/endpoint.json" --nombre "$NOMBRE_DESTINO")"
if [ -n "$ID_DESTINO" ]; then
  echo "$NOMBRE_DESTINO sigue desplegada: se mueve el tráfico."
  gcloud ai endpoints update "$NOMBRE_ENDPOINT" --project "$PROYECTO" --region "$REGION" \
    --traffic-split "$(ayuda split-solo --json "$TRABAJO/endpoint.json" --id "$ID_DESTINO")"
else
  VERSION_VERTEX="$(ayuda version-modelo --json "$TRABAJO/versiones.json" --alias "$NOMBRE_DESTINO")"
  [ -n "$VERSION_VERTEX" ] || { echo "ERROR: $NOMBRE_DESTINO no está en el Model Registry (¿se borró?). Súbela con scripts/subir_modelo.sh $DESTINO" >&2; exit 1; }
  echo "$NOMBRE_DESTINO ya no está desplegada: se vuelve a desplegar la versión $VERSION_VERTEX del Model Registry (tarda varios minutos)."
  gcloud ai endpoints deploy-model "$NOMBRE_ENDPOINT" --project "$PROYECTO" --region "$REGION" \
    --model "$NOMBRE_MODELO@$VERSION_VERTEX" --display-name "$NOMBRE_DESTINO" --machine-type "$MAQUINA" \
    --min-replica-count "$MIN_REPLICAS" --max-replica-count "$MAX_REPLICAS" \
    --traffic-split "$(ayuda split-nuevo --json "$TRABAJO/endpoint.json" --porcentaje 100)"
fi
guardar_endpoint
ayuda trafico --json "$TRABAJO/endpoint.json"

if [ "$CON_MLFLOW" -eq 1 ]; then
  aviso "3. Alias champion de MLflow"
  (cd "$DIR_PROYECTO" && "$PY" -m ia_mlops.alias_modelo volver) || echo "AVISO: no se pudo mover el alias de MLflow (¿tienes el registro del curso?). El tráfico de Vertex YA está en $NOMBRE_DESTINO; mueve el alias a mano con  python -m ia_mlops.alias_modelo promover --version $DESTINO"
fi

if [ "$RETIRAR" -eq 1 ]; then
  aviso "4. Retirar $NOMBRE_ACTUAL (espero $ESPERA_RETIRAR s)"
  sleep "$ESPERA_RETIRAR"
  gcloud ai endpoints undeploy-model "$NOMBRE_ENDPOINT" --project "$PROYECTO" --region "$REGION" --deployed-model-id "$ID_ACTUAL" --quiet
else
  echo; echo "$NOMBRE_ACTUAL sigue desplegada con 0 % y SIGUE COBRANDO. Retírala con  scripts/volver.sh --retirar-actual  o borra todo con scripts/borrar.sh"
fi
