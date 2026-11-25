#!/usr/bin/env bash
# probar.sh (practica 04) - Donde: Cloud Shell. Hace una prediccion online con el endpoint y la compara con el mismo modelo en local.
# Formato de entrada: {"instances": [[13 numeros], ...]} con las variables EN ESTE ORDEN (el del modelo, ia_mlops.config.FEATURES):
#   recencia_dias, frecuencia, monto_total, ticket_medio, unidades_total, productos_distintos, antiguedad_dias,
#   frecuencia_90d, monto_90d, frecuencia_180d, dias_medios_entre_compras, devoluciones, es_reino_unido
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/variables.sh"

comprobar_entorno
[ -f "$TRABAJO/instancias.json" ] || { echo "ERROR: falta $TRABAJO/instancias.json (ejecuta ./crear.sh en esta misma sesion)." >&2; exit 1; }

aviso "Peticion enviada ($TRABAJO/instancias.json)"
cat "$TRABAJO/instancias.json"; echo

aviso "gcloud ai endpoints predict"
gcloud ai endpoints predict "$NOMBRE_ENDPOINT" --project "$PROYECTO" --region "$REGION_VERTEX" \
  --json-request "$TRABAJO/instancias.json" --format json | tee "$TRABAJO/respuesta.json"

aviso "Comparacion con el mismo modelo en local"
python3 "$DIR/comparar_respuesta.py" --respuesta "$TRABAJO/respuesta.json" --esperado "$TRABAJO/esperado_local.json"
echo
echo "Nota: el contenedor pre-construido de scikit-learn llama a predict(): devuelve la CLASE (1 = comprara en 90 dias), no la probabilidad."
echo "La probabilidad (predict_proba) de arriba es la del modelo en local; para servirla desde Vertex haria falta un contenedor propio."
echo "Todo correcto. AHORA: ./borrar.sh (el endpoint cobra mientras este desplegado)."
