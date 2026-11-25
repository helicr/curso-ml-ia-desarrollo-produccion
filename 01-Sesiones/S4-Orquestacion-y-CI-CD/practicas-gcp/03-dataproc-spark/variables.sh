#!/usr/bin/env bash
# variables.sh (practica 03). Lo cargan crear.sh, probar.sh y borrar.sh: los tres usan LOS MISMOS nombres.
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../comun.sh"

REGION_SPARK="${CURSO_REGION_SPARK:-$REGION}"          # Dataproc sin servidor en Santiago: SIN VERIFICAR (ver README); alternativa: southamerica-east1
NOMBRE_BUCKET="${PROYECTO}-curso-ml-dataproc"          # los nombres de bucket son globales: se prefija con el proyecto
PREFIJO_BATCH="curso-ventas"                           # cada lote se llama PREFIJO_BATCH-AAAAMMDD-HHMMSS
VERSION_SPARK="2.3"                                    # runtime LTS (soporte hasta 2027/11/26): https://docs.cloud.google.com/dataproc-serverless/docs/concepts/versions/spark-runtime-versions
TRABAJO="/tmp/curso-dataproc"
ESTADO="$HOME/.curso-ml-gcp"                           # marcas locales (p. ej. si esta practica concedio un rol)
MARCA_ROL="$ESTADO/03-rol-dataproc-worker"
ROL_WORKER="roles/dataproc.worker"
