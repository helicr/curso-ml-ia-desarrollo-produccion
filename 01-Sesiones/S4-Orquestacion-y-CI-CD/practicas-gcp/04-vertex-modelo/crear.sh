#!/usr/bin/env bash
# crear.sh (practica 04) - Donde: Cloud Shell. Idempotente.
#
# QUE CREA en project-curso-ml-ia / southamerica-west1 (Vertex AI):
#   1. Un bucket de Cloud Storage (NOMBRE_BUCKET) con model.joblib (el modelo de retencion reentrenado con scikit-learn 1.6).
#   2. Un modelo en el Model Registry (NOMBRE_MODELO) con el contenedor pre-construido de scikit-learn 1.6.
#   3. Un endpoint (NOMBRE_ENDPOINT) con el modelo desplegado en UNA maquina e2-standard-2. ¡ESTO COBRA MIENTRAS ESTE DESPLEGADO!
# COMO SE BORRA: ./borrar.sh (undeploy -> endpoint -> modelo -> bucket). No dejes el endpoint desplegado al acabar.
# Fuentes: https://docs.cloud.google.com/vertex-ai/docs/predictions/pre-built-containers
#          https://docs.cloud.google.com/sdk/gcloud/reference/ai/models/upload
#          https://docs.cloud.google.com/sdk/gcloud/reference/ai/endpoints/deploy-model
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/variables.sh"

comprobar_entorno
habilitar_apis aiplatform.googleapis.com storage.googleapis.com
preparar_proyecto

aviso "1. Reentrenar el modelo con scikit-learn $VERSION_SKLEARN (entorno aparte: $VENV16)"
if [ ! -x "$VENV16/bin/python" ]; then python3 -m venv "$VENV16"; fi
if ! "$VENV16/bin/python" -c "import sklearn,sys; sys.exit(0 if sklearn.__version__=='$VERSION_SKLEARN' else 1)" >/dev/null 2>&1; then
  "$VENV16/bin/pip" install -q "scikit-learn==$VERSION_SKLEARN" "numpy==$VERSION_NUMPY" "pandas==$VERSION_PANDAS" joblib
fi
mkdir -p "$TRABAJO"
"$VENV16/bin/python" "$DIR/entrenar_sklearn16.py" --proyecto "$DIR_PROYECTO" --salida "$TRABAJO" --clientes "$CLIENTES_EJEMPLO"

aviso "2. Bucket gs://$NOMBRE_BUCKET y subida de model.joblib"
if existe gcloud storage buckets describe "gs://$NOMBRE_BUCKET" --project "$PROYECTO"; then
  echo "Ya existe el bucket."
else
  gcloud storage buckets create "gs://$NOMBRE_BUCKET" --project "$PROYECTO" --location "$REGION_VERTEX" \
    --uniform-bucket-level-access --public-access-prevention
fi
gcloud storage cp "$TRABAJO/model.joblib" "gs://$NOMBRE_BUCKET/modelo/model.joblib"

aviso "3. Registrar el modelo en Vertex AI Model Registry"
if existe gcloud ai models describe "$NOMBRE_MODELO" --region "$REGION_VERTEX" --project "$PROYECTO"; then
  echo "Ya existe el modelo $NOMBRE_MODELO."
else
  gcloud ai models upload --project "$PROYECTO" --region "$REGION_VERTEX" --model-id "$NOMBRE_MODELO" \
    --display-name "$NOMBRE_MODELO" --container-image-uri "$CONTENEDOR" \
    --artifact-uri "gs://$NOMBRE_BUCKET/modelo" --labels "curso=ml-ia"
fi

aviso "4. Endpoint"
if existe gcloud ai endpoints describe "$NOMBRE_ENDPOINT" --region "$REGION_VERTEX" --project "$PROYECTO"; then
  echo "Ya existe el endpoint $NOMBRE_ENDPOINT."
else
  gcloud ai endpoints create --project "$PROYECTO" --region "$REGION_VERTEX" --endpoint-id "$NOMBRE_ENDPOINT" \
    --display-name "$NOMBRE_ENDPOINT" --labels "curso=ml-ia"
fi

aviso "5. Desplegar el modelo en el endpoint ($MAQUINA x $REPLICAS; tarda varios minutos, sin medir)"
DESPLEGADOS="$(gcloud ai endpoints describe "$NOMBRE_ENDPOINT" --region "$REGION_VERTEX" --project "$PROYECTO" --format 'value(deployedModels[].id)')"
if [ -n "$DESPLEGADOS" ]; then
  echo "El endpoint ya tiene un modelo desplegado ($DESPLEGADOS)."
else
  gcloud ai endpoints deploy-model "$NOMBRE_ENDPOINT" --project "$PROYECTO" --region "$REGION_VERTEX" \
    --model "$NOMBRE_MODELO" --display-name "$NOMBRE_DESPLIEGUE" --machine-type "$MAQUINA" \
    --min-replica-count "$REPLICAS" --max-replica-count "$REPLICAS"
fi

echo; echo "Listo. Ahora: ./probar.sh   y, SIN DEJARLO PARA DESPUES: ./borrar.sh"
