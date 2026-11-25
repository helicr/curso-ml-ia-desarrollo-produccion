#!/usr/bin/env bash
# crear.sh (practica 02) - Donde: Cloud Shell. Idempotente.
#
# REQUISITO: la imagen de la practica 01 ya esta en Artifact Registry (ejecuta antes 01-docker-artifact-registry/crear.sh).
# QUE CREA en project-curso-ml-ia / southamerica-west1:
#   1. Un clúster GKE Autopilot (NOMBRE_CLUSTER). Tarda varios minutos (sin medir).
#   2. Dentro del clúster: un namespace, un Deployment y un Service (manifiestos/*.yaml).
# COMO SE BORRA: ./borrar.sh (borrar el clúster borra todo lo de dentro).
# Fuentes: https://docs.cloud.google.com/kubernetes-engine/docs/how-to/creating-an-autopilot-cluster
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/variables.sh"

comprobar_entorno
habilitar_apis container.googleapis.com artifactregistry.googleapis.com

aviso "0. ¿Esta la imagen de la practica 01?"
if ! existe gcloud artifacts docker images describe "$IMAGEN_COMPLETA" --project "$PROYECTO"; then
  echo "ERROR: no encuentro $IMAGEN_COMPLETA. Ejecuta antes ../01-docker-artifact-registry/crear.sh (y no ejecutes su borrar.sh hasta acabar esta)." >&2
  exit 1
fi

aviso "1a. Cuenta de servicio de los nodos ($SA_NODOS) con lo mínimo: ser nodo de GKE y leer imágenes"
existe gcloud iam service-accounts describe "$SA_NODOS_EMAIL" --project "$PROYECTO" || \
  gcloud iam service-accounts create "$SA_NODOS" --project "$PROYECTO" --display-name="GKE: nodos del clúster de la práctica"
for ROL in $ROLES_NODOS; do
  gcloud projects add-iam-policy-binding "$PROYECTO" --member="serviceAccount:$SA_NODOS_EMAIL" --role="$ROL" \
    --condition=None --format='value(etag)' >/dev/null
  echo "  $ROL"
done

aviso "1b. Clúster GKE Autopilot $NOMBRE_CLUSTER (con la cuenta de servicio de los nodos)"
if existe gcloud container clusters describe "$NOMBRE_CLUSTER" --region "$REGION" --project "$PROYECTO"; then
  echo "Ya existe el clúster."
else
  gcloud container clusters create-auto "$NOMBRE_CLUSTER" --region "$REGION" --project "$PROYECTO" --labels "$ETIQUETA" \
    --service-account="$SA_NODOS_EMAIL"
fi
gcloud container clusters get-credentials "$NOMBRE_CLUSTER" --region "$REGION" --project "$PROYECTO"

aviso "2. kubectl apply (namespace, deployment, service)"
kubectl apply -f "$DIR/manifiestos/namespace.yaml"
sed "s|__IMAGEN__|$IMAGEN_COMPLETA|" "$DIR/manifiestos/deployment.yaml" | kubectl apply -f -
kubectl apply -f "$DIR/manifiestos/service.yaml"

aviso "3. Esperando a que el pod este listo (Autopilot crea el nodo si hace falta: puede tardar unos minutos)"
kubectl -n "$NAMESPACE" rollout status deployment/retencion-api --timeout=900s
kubectl -n "$NAMESPACE" get pods,svc -o wide

echo; echo "Listo. Ahora: ./probar.sh   y cuando termines: ./borrar.sh"
