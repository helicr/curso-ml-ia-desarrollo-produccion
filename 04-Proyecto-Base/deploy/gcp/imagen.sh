#!/usr/bin/env bash
# imagen.sh - DEMO 2 (imagen): repositorio de Artifact Registry y docker build/tag/push de la imagen de la API de S2.
#
# QUE CREA (solo con --ejecutar; por defecto SOLO MUESTRA las ordenes):
#   1. Un repositorio Docker de Artifact Registry (una region, etiqueta curso=ml-ia).
#   2. Configura Docker para autenticarse con el ayudante de credenciales de gcloud (sin claves en disco).
#   3. docker build de deploy/docker/Dockerfile (requiere `make pipeline` antes: el modelo va dentro de la imagen), docker tag y
#      docker push con una ETIQUETA FIJA (CURSO_GCP_ETIQUETA_IMAGEN, por defecto s3-1). Nunca se usa ni se acepta "latest".
# QUE CUESTA: puede generar coste (almacenamiento de la imagen, de unos cientos de MB, en Artifact Registry); ver el presupuesto.
# COMO SE BORRA: ./limpiar.sh --confirmar (imagen y luego repositorio). Comprobacion: listados al final de limpiar.sh.
# Requisitos (modo real): docker con sesion, gcloud, y la carpeta 04-Proyecto-Base con models/ generado (make pipeline).
# Sin verificar contra GCP real: opciones de gcloud y tiempos del push (T10).

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$DIR/_comun.sh"
iniciar "$@"
cd "$DIR_PROYECTO" || exit 2
necesita_herramienta gcloud
necesita_herramienta docker
HOST_AR="${REGION}-docker.pkg.dev"

paso "1. Repositorio de Artifact Registry"
correr gcloud artifacts repositories create "$REPO_AR" --project "$PROYECTO" --repository-format=docker --location "$REGION" --labels=curso=ml-ia \
  --description "Imagenes de la demo del curso"

paso "2. Docker usa las credenciales de gcloud (sin claves en disco)"
correr gcloud auth configure-docker "$HOST_AR" --quiet

paso "3. build, tag y push con etiqueta fija ($ETIQUETA_IMAGEN)"
# El codigo, de esta carpeta (FUENTE=contexto); el modelo, el de models/ (contexto «modelo»). Ver la cabecera de deploy/docker/Dockerfile.
correr docker build -f deploy/docker/Dockerfile --build-arg FUENTE=contexto --build-context modelo=models -t "$IMAGEN:$ETIQUETA_IMAGEN" .
correr docker tag "$IMAGEN:$ETIQUETA_IMAGEN" "$IMAGEN_COMPLETA"
correr docker push "$IMAGEN_COMPLETA"

paso "Listado de comprobacion (con resumen/digest)"
leer gcloud artifacts docker images list "$HOST_AR/$PROYECTO/$REPO_AR" --include-tags