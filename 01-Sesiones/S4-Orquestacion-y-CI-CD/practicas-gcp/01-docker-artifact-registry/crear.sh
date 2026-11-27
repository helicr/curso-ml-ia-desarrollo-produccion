#!/usr/bin/env bash
# crear.sh (practica 01) - Donde: Cloud Shell. Idempotente: se puede repetir.
#
# QUE CREA en project-curso-ml-ia / southamerica-west1:
#   1. Un repositorio Docker de Artifact Registry (NOMBRE_REPO).
#   2. La imagen de la API de retencion (04-Proyecto-Base/deploy/docker/Dockerfile), construida AQUI con docker y subida con etiqueta fija.
#   3. Un servicio de Cloud Run PRIVADO (NOMBRE_SERVICIO) con esa imagen, 0 instancias en reposo y maximo 1.
# COMO SE BORRA: ./borrar.sh
# Fuentes: https://docs.cloud.google.com/artifact-registry/docs/docker/store-docker-container-images
#          https://docs.cloud.google.com/run/docs/deploying
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/variables.sh"

comprobar_entorno
habilitar_apis artifactregistry.googleapis.com run.googleapis.com
preparar_proyecto

aviso "1. Repositorio de Artifact Registry"
if existe gcloud artifacts repositories describe "$NOMBRE_REPO" --location "$REGION" --project "$PROYECTO"; then
  echo "Ya existe el repositorio $NOMBRE_REPO."
else
  gcloud artifacts repositories create "$NOMBRE_REPO" --repository-format=docker --location "$REGION" \
    --project "$PROYECTO" --labels="$ETIQUETA" --description "Imagenes del curso ML e IA"
fi

aviso "2. Construir y subir la imagen $IMAGEN_COMPLETA"
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
# El codigo, de la carpeta del proyecto en Cloud Shell (FUENTE=contexto); el modelo, el de models/ (contexto «modelo»).
docker build -f "$DIR_PROYECTO/deploy/docker/Dockerfile" --build-arg FUENTE=contexto --build-context modelo="$DIR_PROYECTO/models" \
  -t "$IMAGEN_COMPLETA" "$DIR_PROYECTO"
docker push "$IMAGEN_COMPLETA"

aviso "3. Cloud Run (servicio privado: solo con identidad)"
gcloud run deploy "$NOMBRE_SERVICIO" --image "$IMAGEN_COMPLETA" --region "$REGION" --project "$PROYECTO" \
  --no-allow-unauthenticated --port 8080 --memory "$MEMORIA_RUN" --cpu 1 \
  --min-instances 0 --max-instances "$MAX_INSTANCIAS" --labels "$ETIQUETA" --quiet

echo
echo "Listo. Ahora: ./probar.sh   y cuando termines: ./borrar.sh"
