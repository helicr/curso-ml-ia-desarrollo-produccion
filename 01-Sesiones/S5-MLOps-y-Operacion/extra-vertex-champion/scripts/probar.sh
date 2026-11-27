#!/usr/bin/env bash
# probar.sh - Donde: Cloud Shell.   Uso:  scripts/probar.sh [--intentos N]
#
# QUE HACE: envía clientes de ejemplo al endpoint y comprueba la PARIDAD con el mismo modelo cargado en local (probabilidad, clase y tramo).
# Con una versión en canario (10 %) una petición puede contestarla la versión ANTERIOR: se reintenta hasta que conteste la del manifiesto
# (cada respuesta lleva `version_mlflow`). Se detiene si la paridad se rompe (salida 1) o si tras N intentos no contesta la esperada (salida 3).
# Formato de entrada: {"instances": [[13 números], ...]} en el orden de ia_mlops.config.FEATURES (lo genera instancias.py).
# Fuente: https://docs.cloud.google.com/vertex-ai/docs/predictions/get-online-predictions
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/variables.sh"
INTENTOS=40
while [ $# -gt 0 ]; do
  case "$1" in
    --intentos) INTENTOS="${2:?falta el número}"; shift 2 ;;
    *) echo "Opción desconocida: $1 (uso: scripts/probar.sh [--intentos N])" >&2; exit 2 ;;
  esac
done

comprobar_entorno
exigir_manifiesto
VERSION_MLFLOW="$(mf mlflow_version)"

aviso "Petición ($TRABAJO/instancias.json)"
"$PY" "$DIR_EXTRA/instancias.py" --salida "$TRABAJO/instancias.json"
cat "$TRABAJO/instancias.json"; echo

aviso "gcloud ai endpoints predict (hasta $INTENTOS intentos hasta que conteste la versión $VERSION_MLFLOW)"
CODIGO=3
for i in $(seq 1 "$INTENTOS"); do
  gcloud ai endpoints predict "$NOMBRE_ENDPOINT" --project "$PROYECTO" --region "$REGION" \
    --json-request "$TRABAJO/instancias.json" --format json > "$TRABAJO/respuesta.json"
  set +e
  "$PY" "$DIR_EXTRA/comparar_paridad.py" --respuesta "$TRABAJO/respuesta.json" --instancias "$TRABAJO/instancias.json" \
    --modelo-dir "$CONTEXTO/modelo" --esperar-version "$VERSION_MLFLOW" > "$TRABAJO/paridad.txt"
  CODIGO=$?
  set -e
  [ "$CODIGO" -ne 3 ] && break
  echo "intento $i: contestó otra versión (tráfico dividido); reintento..."
  sleep 2
done
cat "$TRABAJO/respuesta.json"; echo
aviso "Comparación con el modelo local"
cat "$TRABAJO/paridad.txt"
if [ "$CODIGO" -eq 0 ]; then
  echo; echo "Todo correcto. Si es el canario, siguiente: scripts/promover.sh. AHORA o al terminar: scripts/borrar.sh (el endpoint cobra mientras esté desplegado)."
fi
exit "$CODIGO"
