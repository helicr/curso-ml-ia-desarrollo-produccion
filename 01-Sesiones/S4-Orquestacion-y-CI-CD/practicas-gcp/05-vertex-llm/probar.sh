#!/usr/bin/env bash
# probar.sh (practica 05) - Donde: Cloud Shell. Pide a Gemini que explique la prediccion de dos clientes del ejemplo (cada llamada cuesta unos centimos o menos; sin dato).
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/variables.sh"

comprobar_entorno
[ -x "$VENV/bin/python" ] || { echo "ERROR: no existe el entorno $VENV. Ejecuta ./crear.sh" >&2; exit 1; }

for CLIENTE in "$CLIENTE_EJEMPLO" dormido; do
  aviso "Cliente: $CLIENTE"
  "$VENV/bin/python" "$DIR/explicar_prediccion.py" --proyecto "$DIR_PROYECTO" --clientes "$CLIENTES_EJEMPLO" --cliente "$CLIENTE" \
    --id-proyecto-gcp "$PROYECTO" --ubicacion "$REGION_GEMINI" --modelo-llm "$MODELO_LLM"
done
echo; echo "Todo correcto. Cuando termines: ./borrar.sh"
