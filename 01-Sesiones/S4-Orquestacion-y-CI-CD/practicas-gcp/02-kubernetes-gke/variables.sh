#!/usr/bin/env bash
# variables.sh (practica 02). Lo cargan crear.sh, probar.sh y borrar.sh: los tres usan LOS MISMOS nombres.
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../comun.sh"

NOMBRE_CLUSTER="curso-ml-gke"     # clúster GKE Autopilot (siempre regional: la region se pasa con --region)
NAMESPACE="curso"                 # espacio de nombres de Kubernetes de la practica
PUERTO_LOCAL="8081"               # puerto local para kubectl port-forward (el 8080 lo usa la vista previa de Cloud Shell)
CONTEXTO_KUBECTL="gke_${PROYECTO}_${REGION}_${NOMBRE_CLUSTER}"
# Cuenta de servicio de los NODOS. En organizaciones nuevas la cuenta por defecto de Compute no tiene ningún rol: con ella los
# nodos no pueden descargar la imagen ni enviar registros y métricas, y el clúster acaba en estado ERROR (visto el 25/11/2026).
SA_NODOS="sa-gke-nodos"
SA_NODOS_EMAIL="${SA_NODOS}@${PROYECTO}.iam.gserviceaccount.com"
ROLES_NODOS="roles/container.defaultNodeServiceAccount roles/artifactregistry.reader"
