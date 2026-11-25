#!/usr/bin/env bash
# crear.sh (practica 03) - Donde: Cloud Shell. Idempotente (cada ejecucion lanza un lote nuevo; el resultado se sobrescribe).
#
# QUE CREA en project-curso-ml-ia:
#   1. Un bucket de Cloud Storage (NOMBRE_BUCKET) en la region, con el CSV de ventas del caso y el job de PySpark.
#   2. (Solo si falta) el rol roles/dataproc.worker para la cuenta de Compute por defecto. Se anota y borrar.sh lo revierte.
#   3. Un lote (batch) de Dataproc sin servidor que ejecuta analisis_ventas.py y escribe en gs://BUCKET/salida.
#   No hay clúster: el lote desaparece solo al terminar (su registro se borra en borrar.sh).
# COMO SE BORRA: ./borrar.sh
# Fuentes: https://docs.cloud.google.com/dataproc-serverless/docs/quickstarts/spark-batch
#          https://docs.cloud.google.com/dataproc-serverless/docs/concepts/network
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/variables.sh"

comprobar_entorno
habilitar_apis dataproc.googleapis.com storage.googleapis.com
preparar_proyecto

aviso "1. Exportar las lineas de venta del caso (curso.db -> CSV)"
mkdir -p "$TRABAJO"
python3 "$DIR/exportar_datos.py" --proyecto "$DIR_PROYECTO" --salida "$TRABAJO/ventas_lineas.csv"

aviso "2. Bucket gs://$NOMBRE_BUCKET y subida de datos y job"
if existe gcloud storage buckets describe "gs://$NOMBRE_BUCKET" --project "$PROYECTO"; then
  echo "Ya existe el bucket."
else
  gcloud storage buckets create "gs://$NOMBRE_BUCKET" --project "$PROYECTO" --location "$REGION_SPARK" \
    --uniform-bucket-level-access --public-access-prevention
fi
gcloud storage cp "$TRABAJO/ventas_lineas.csv" "gs://$NOMBRE_BUCKET/entrada/ventas_lineas.csv"
gcloud storage cp "$DIR/analisis_ventas.py" "gs://$NOMBRE_BUCKET/job/analisis_ventas.py"

aviso "3. Permiso de la cuenta de Compute por defecto (Dataproc Worker)"
NUMERO="$(gcloud projects describe "$PROYECTO" --format 'value(projectNumber)')"
CUENTA="${NUMERO}-compute@developer.gserviceaccount.com"
TIENE="$(gcloud projects get-iam-policy "$PROYECTO" --flatten 'bindings[].members' \
  --filter "bindings.role=$ROL_WORKER AND bindings.members:serviceAccount:$CUENTA" --format 'value(bindings.role)')"
if [ -n "$TIENE" ]; then
  echo "$CUENTA ya tiene $ROL_WORKER."
else
  mkdir -p "$ESTADO"
  if gcloud projects add-iam-policy-binding "$PROYECTO" --member "serviceAccount:$CUENTA" --role "$ROL_WORKER" --condition=None >/dev/null; then
    echo "$CUENTA" > "$MARCA_ROL"
    echo "Concedido $ROL_WORKER a $CUENTA (borrar.sh lo quitara)."
    # IAM tarda en propagarse. El 25/11/2026, lanzar el lote justo después de conceder el rol falló con
    # «Permission 'dataproc.autoscalingPolicies.use' denied»; dos minutos después, el mismo lote terminó bien.
    echo "Espero 120 s a que el permiso se propague (si no, el lote falla con 'dataproc.autoscalingPolicies.use' denied)."
    sleep 120
  else
    echo "AVISO: no he podido conceder $ROL_WORKER (¿permisos?). Si el lote falla por permisos, pide que lo concedan." >&2
  fi
fi

aviso "4. Lote de Dataproc sin servidor (espera a que termine; unos minutos, sin medir)"
BATCH="${PREFIJO_BATCH}-$(date +%Y%m%d-%H%M%S)"
gcloud dataproc batches submit pyspark "gs://$NOMBRE_BUCKET/job/analisis_ventas.py" \
  --project "$PROYECTO" --region "$REGION_SPARK" --batch "$BATCH" --version "$VERSION_SPARK" \
  --deps-bucket "$NOMBRE_BUCKET" --labels "$ETIQUETA" \
  -- --entrada "gs://$NOMBRE_BUCKET/entrada/ventas_lineas.csv" --salida "gs://$NOMBRE_BUCKET/salida"

echo; echo "Listo (lote $BATCH). Ahora: ./probar.sh   y cuando termines: ./borrar.sh"
