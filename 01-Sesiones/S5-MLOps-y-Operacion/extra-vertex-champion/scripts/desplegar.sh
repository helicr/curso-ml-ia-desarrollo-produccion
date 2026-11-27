#!/usr/bin/env bash
# desplegar.sh - Donde: Cloud Shell. Idempotente.   Uso:  scripts/desplegar.sh [--canario N]
#
# QUE HACE: despliega en el endpoint la versión de Vertex que subió subir_modelo.sh (la del manifiesto).
#   · Si el endpoint está vacío, la versión recibe el 100 % del tráfico.
#   · Si ya hay otra versión desplegada, la nueva entra en CANARIO: recibe solo N % (por defecto 10) y la anterior conserva el resto.
#     Se pasa al 100 % con scripts/promover.sh, después de probar. La anterior SIGUE desplegada (para volver rápido) hasta retirarla.
# ¡ESTO COBRA! Un endpoint cobra MIENTRAS TENGA UN MODELO DESPLEGADO, aunque no reciba peticiones, y con dos versiones desplegadas son
#   DOS máquinas ($MAQUINA x $MIN_REPLICAS cada una). Precio: sin dato (https://cloud.google.com/vertex-ai/pricing). Cuando acabes: scripts/borrar.sh
# Fuentes: https://docs.cloud.google.com/vertex-ai/docs/predictions/deploy-model-api   (--traffic-split, clave 0 = el modelo que se despliega)
#          https://docs.cloud.google.com/sdk/gcloud/reference/ai/endpoints/deploy-model
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/variables.sh"

while [ $# -gt 0 ]; do
  case "$1" in
    --canario) CANARIO="${2:?falta el porcentaje}"; shift 2 ;;
    *) echo "Opción desconocida: $1 (uso: scripts/desplegar.sh [--canario N])" >&2; exit 2 ;;
  esac
done
case "$CANARIO" in ''|*[!0-9]*) echo "ERROR: --canario debe ser un entero entre 0 y 100." >&2; exit 2 ;; esac
[ "$CANARIO" -le 100 ] || { echo "ERROR: --canario debe estar entre 0 y 100." >&2; exit 2; }

comprobar_entorno
exigir_manifiesto
ALIAS_VERSION="$(mf alias_vertex)"

aviso "1. Versión de Vertex con el alias $ALIAS_VERSION"
guardar_versiones
VERSION_VERTEX="$(ayuda version-modelo --json "$TRABAJO/versiones.json" --alias "$ALIAS_VERSION")"
[ -n "$VERSION_VERTEX" ] || { echo "ERROR: ese modelo no está subido: ejecuta scripts/subir_modelo.sh." >&2; exit 1; }
echo "$NOMBRE_MODELO versión $VERSION_VERTEX"

aviso "2. Endpoint $NOMBRE_ENDPOINT"
if existe gcloud ai endpoints describe "$NOMBRE_ENDPOINT" --region "$REGION" --project "$PROYECTO"; then
  echo "Ya existe."
else
  gcloud ai endpoints create --project "$PROYECTO" --region "$REGION" --endpoint-id "$NOMBRE_ENDPOINT" \
    --display-name "$NOMBRE_ENDPOINT" --labels "curso=ml-ia"
fi

aviso "3. Desplegar $ALIAS_VERSION ($MAQUINA x $MIN_REPLICAS; tarda varios minutos, sin medir)"
guardar_endpoint
if [ -n "$(ayuda desplegado --json "$TRABAJO/endpoint.json" --nombre "$ALIAS_VERSION")" ]; then
  echo "Ya está desplegada ($ALIAS_VERSION): no se vuelve a desplegar."
else
  REPARTO="$(ayuda split-nuevo --json "$TRABAJO/endpoint.json" --porcentaje "$CANARIO")"
  # Sin ningún modelo desplegado el reparto es 0=100 (todo para el nuevo), da igual el canario.
  echo "Reparto de tráfico: $REPARTO   (0 = el modelo que se despliega ahora)"
  gcloud ai endpoints deploy-model "$NOMBRE_ENDPOINT" --project "$PROYECTO" --region "$REGION" \
    --model "$NOMBRE_MODELO@$VERSION_VERTEX" --display-name "$ALIAS_VERSION" --machine-type "$MAQUINA" \
    --min-replica-count "$MIN_REPLICAS" --max-replica-count "$MAX_REPLICAS" --traffic-split "$REPARTO"
fi

guardar_endpoint
ID_NUEVO="$(ayuda desplegado --json "$TRABAJO/endpoint.json" --nombre "$ALIAS_VERSION")"
echo "$ID_NUEVO" > "$TRABAJO/id_desplegado.txt"
aviso "Tráfico ahora"
ayuda trafico --json "$TRABAJO/endpoint.json"
echo; echo "Listo. Siguiente: scripts/probar.sh ; si todo va bien: scripts/promover.sh ; y SIN DEJARLO PARA DESPUÉS: scripts/borrar.sh"
