#!/usr/bin/env bash
# variables.sh (practica 04). Lo cargan crear.sh, probar.sh y borrar.sh: los tres usan LOS MISMOS nombres.
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../comun.sh"

NOMBRE_BUCKET="${PROYECTO}-curso-ml-vertex"      # bucket del artefacto (misma region que el modelo: exigencia de Vertex AI)
NOMBRE_MODELO="retencion-90d-sklearn"            # ID del modelo en el Model Registry (--model-id)
NOMBRE_ENDPOINT="retencion-90d-endpoint"         # ID del endpoint (--endpoint-id)
NOMBRE_DESPLIEGUE="retencion-90d-v1"             # nombre visible del modelo desplegado

# Contenedor PRE-CONSTRUIDO de scikit-learn 1.6 (la mas reciente que ofrece Vertex AI el 25/11/2026; el proyecto usa 1.9.1, que NO esta
# soportada: por eso se reentrena el MISMO modelo con scikit-learn 1.6). Tabla de versiones y formato del URI:
# https://docs.cloud.google.com/vertex-ai/docs/predictions/pre-built-containers  (el prefijo us/europe/asia sirve la misma imagen; la etiqueta debe ser latest)
CONTENEDOR="us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-6:latest"
VERSION_SKLEARN="1.6.1"                          # parche exacto con el que se entrena: SIN VERIFICAR que coincida con el del contenedor
VERSION_NUMPY="1.26.4"                           # numpy 1.x: un pickle con numpy 2 puede no abrirse en un contenedor con numpy 1 (sin verificar la version del contenedor)
VERSION_PANDAS="2.2.3"
MAQUINA="e2-standard-2"                          # una de las de 2 vCPU que admite la prediccion online: https://docs.cloud.google.com/vertex-ai/docs/predictions/configure-compute
REPLICAS="1"                                     # minimo y maximo: un solo nodo

TRABAJO="/tmp/curso-vertex"
VENV16="${CURSO_VENV16:-$HOME/.venv-curso-sklearn16}"
