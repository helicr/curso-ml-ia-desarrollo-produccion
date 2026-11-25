#!/usr/bin/env bash
# borrar.sh (practica 02) - Donde: Cloud Shell. Idempotente. Borra el clúster GKE (y con el, todo lo de dentro) y limpia el contexto de kubectl.
# NO borra la imagen ni el repositorio de Artifact Registry: son de la practica 01 (01/borrar.sh).
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/variables.sh"

comprobar_entorno

aviso "Clúster GKE: $NOMBRE_CLUSTER"
if existe gcloud container clusters describe "$NOMBRE_CLUSTER" --region "$REGION" --project "$PROYECTO"; then
  gcloud container clusters delete "$NOMBRE_CLUSTER" --region "$REGION" --project "$PROYECTO" --quiet
else
  echo "No existe (nada que borrar)."
fi

aviso "Cuenta de servicio de los nodos: $SA_NODOS (primero sus roles, después la cuenta)"
for ROL in $ROLES_NODOS; do
  gcloud projects remove-iam-policy-binding "$PROYECTO" --member="serviceAccount:$SA_NODOS_EMAIL" --role="$ROL" \
    --condition=None --format='value(etag)' >/dev/null 2>&1 && echo "  quitado $ROL" || true
done
if existe gcloud iam service-accounts describe "$SA_NODOS_EMAIL" --project "$PROYECTO"; then
  gcloud iam service-accounts delete "$SA_NODOS_EMAIL" --project "$PROYECTO" --quiet
fi

aviso "Contexto local de kubectl"
if command -v kubectl >/dev/null 2>&1; then
  kubectl config delete-context "$CONTEXTO_KUBECTL" >/dev/null 2>&1 || true
  kubectl config delete-cluster "$CONTEXTO_KUBECTL" >/dev/null 2>&1 || true
  kubectl config unset "users.$CONTEXTO_KUBECTL" >/dev/null 2>&1 || true
fi

aviso "Lo que queda (debe estar vacio)"
gcloud container clusters list --project "$PROYECTO" || true
gcloud compute disks list --project "$PROYECTO" --filter="name~gke-$NOMBRE_CLUSTER" || true
gcloud compute forwarding-rules list --project "$PROYECTO" || true
