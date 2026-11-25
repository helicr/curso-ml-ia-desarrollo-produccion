#!/usr/bin/env bash
# variables.sh (practica 05). Lo cargan crear.sh, probar.sh y borrar.sh: los tres usan LOS MISMOS nombres.
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../comun.sh"

# Gemini no figura en Santiago: se usa la ubicacion "global" (REGION_GEMINI en comun.sh).
# Modelo: gemini-3.1-flash-lite, la opcion "mas economica" de las que siguen vigentes el 25/11/2026 (gemini-2.5-flash y 2.5-flash-lite
# se retiraron el 20/10/2026): https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versions
# Que ese modelo este disponible en "global": SIN VERIFICAR (la ficha del modelo no lista ubicaciones).
MODELO_LLM="${CURSO_MODELO_LLM:-gemini-3.1-flash-lite}"
PAQUETE_SDK="google-genai"           # version sin fijar (la mas reciente): se imprime al instalar
CLIENTE_EJEMPLO="activo"             # activo | dormido (ver ../clientes_ejemplo.json)
