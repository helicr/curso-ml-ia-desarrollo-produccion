#!/usr/bin/env bash
# variables.sh (practica 01). Se carga con `source` desde crear.sh, probar.sh y borrar.sh: los tres usan LOS MISMOS nombres.
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../comun.sh"

# NOMBRE_REPO, NOMBRE_IMAGEN, ETIQUETA_IMAGEN e IMAGEN_COMPLETA vienen de ../comun.sh (la practica 02 usa la misma imagen).
NOMBRE_SERVICIO="retencion-api-practica"   # servicio de Cloud Run (distinto del «retencion-api» del Cloud Journey)
MEMORIA_RUN="1Gi"                 # decision nuestra, sin medir (mlflow-skinny + scikit-learn + pandas); sube si el servicio se reinicia
MAX_INSTANCIAS="1"                # coste minimo; min-instances 0 = no hay instancia en reposo
