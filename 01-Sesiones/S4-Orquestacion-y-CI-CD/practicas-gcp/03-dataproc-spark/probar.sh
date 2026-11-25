#!/usr/bin/env bash
# probar.sh (practica 03) - Donde: Cloud Shell. Solo lee: estado del ultimo lote, resultado en Cloud Storage y comparacion con un calculo local.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/variables.sh"

comprobar_entorno

aviso "Ultimo lote"
BATCH="$(gcloud dataproc batches list --project "$PROYECTO" --region "$REGION_SPARK" --format 'value(name)' | grep -E "(^|/)${PREFIJO_BATCH}-" | sort | tail -n 1 || true)"
[ -n "$BATCH" ] || { echo "ERROR: no hay lotes ${PREFIJO_BATCH}-*. Ejecuta ./crear.sh" >&2; exit 1; }
ID="${BATCH##*/}"
ESTADO_LOTE="$(gcloud dataproc batches describe "$ID" --project "$PROYECTO" --region "$REGION_SPARK" --format 'value(state)')"
echo "Lote: $ID | estado: $ESTADO_LOTE"
[ "$ESTADO_LOTE" = "SUCCEEDED" ] || { echo "ERROR: el lote no termino bien (ver 'Si falla' en el README)." >&2; exit 1; }

aviso "Resultado en Cloud Storage"
gcloud storage ls -r "gs://$NOMBRE_BUCKET/salida/"

aviso "Descargar y mostrar por_pais"
rm -rf "$TRABAJO/salida" && mkdir -p "$TRABAJO/salida/por_pais" "$TRABAJO/salida/rfm"
gcloud storage cp "gs://$NOMBRE_BUCKET/salida/por_pais/part-*.csv" "$TRABAJO/salida/por_pais/"
gcloud storage cp "gs://$NOMBRE_BUCKET/salida/rfm/part-*.csv" "$TRABAJO/salida/rfm/"
head -n 11 "$TRABAJO"/salida/por_pais/part-*.csv
echo "..."
echo "RFM (5 primeras filas):"; head -n 6 "$TRABAJO"/salida/rfm/part-*.csv

aviso "Paridad: Spark frente a un calculo local con Python estandar"
[ -f "$TRABAJO/ventas_lineas.csv" ] || python3 "$DIR/exportar_datos.py" --proyecto "$DIR_PROYECTO" --salida "$TRABAJO/ventas_lineas.csv"
python3 "$DIR/comprobar_resultado.py" --entrada "$TRABAJO/ventas_lineas.csv" --por-pais "$TRABAJO/salida/por_pais"
echo; echo "Todo correcto. Cuando termines: ./borrar.sh"
