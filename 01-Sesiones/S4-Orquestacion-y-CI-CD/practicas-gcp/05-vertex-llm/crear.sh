#!/usr/bin/env bash
# crear.sh (practica 05) - Donde: Cloud Shell. Idempotente.
#
# QUE CREA: NINGUN recurso de GCP (Gemini es un servicio gestionado que se paga por uso: solo se habilita la API de Vertex AI).
#   En local (Cloud Shell): instala el SDK google-genai en el entorno del proyecto (el mismo de las practicas 01-04).
# COMO SE BORRA: ./borrar.sh (desinstala el SDK). La API habilitada se queda (no cuesta nada).
# Fuente: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/sdks/overview
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/variables.sh"

comprobar_entorno
habilitar_apis aiplatform.googleapis.com
preparar_proyecto

aviso "SDK $PAQUETE_SDK"
"$VENV/bin/pip" install -q "$PAQUETE_SDK"
"$VENV/bin/python" -c "import importlib.metadata as m; print('google-genai', m.version('google-genai'))"
echo; echo "Listo. Ahora: ./probar.sh   y cuando termines: ./borrar.sh"
