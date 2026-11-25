#!/usr/bin/env bash
# probar.sh (practica 02) - Donde: Cloud Shell. Prueba la API dentro de Kubernetes, escala a 2 pods y borra un pod para ver que se recrea.
# Deja el Deployment en 2 replicas al terminar (se borra todo con borrar.sh).
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/variables.sh"

comprobar_entorno
gcloud container clusters get-credentials "$NOMBRE_CLUSTER" --region "$REGION" --project "$PROYECTO"
K="kubectl -n $NAMESPACE"

aviso "Pods, Deployment y Service"
$K get deployment,pods,svc

aviso "Probando la API a traves del Service (port-forward a localhost:$PUERTO_LOCAL)"
$K port-forward service/retencion-api "$PUERTO_LOCAL":80 >/tmp/port-forward.log 2>&1 &
PF=$!
trap 'kill $PF 2>/dev/null || true' EXIT
for _ in $(seq 1 20); do curl -fsS "http://127.0.0.1:$PUERTO_LOCAL/salud" >/dev/null 2>&1 && break; sleep 1; done
curl -fsS "http://127.0.0.1:$PUERTO_LOCAL/listo"; echo
CUERPO="$(python3 -c "import json,sys; print(json.dumps(json.load(open(sys.argv[1]))['activo']))" "$CLIENTES_EJEMPLO")"
RESPUESTA="$(curl -fsS -X POST -H 'Content-Type: application/json' -d "$CUERPO" "http://127.0.0.1:$PUERTO_LOCAL/predecir")"
echo "$RESPUESTA"
python3 - "$RESPUESTA" <<'PY'
import json, sys
p = json.loads(sys.argv[1])["probabilidad"]
assert 0.0 <= p <= 1.0, p
print(f"OK: probabilidad de recompra a 90 dias = {p:.3f}")
PY
kill $PF 2>/dev/null || true
trap - EXIT

aviso "Escalar a 2 replicas (deployment = «siempre N pods»)"
$K scale deployment/retencion-api --replicas=2
$K rollout status deployment/retencion-api --timeout=900s
$K get pods -o wide

aviso "Autorreparacion: borro UN pod y Kubernetes crea otro para mantener 2"
POD="$($K get pods -l app=retencion-api -o jsonpath='{.items[0].metadata.name}')"
echo "Borro $POD"
$K delete pod "$POD" --wait=false
LISTOS=""
for _ in $(seq 1 90); do      # hasta ~7 minutos: Autopilot puede tener que crear un nodo
  LISTOS="$($K get deployment retencion-api -o jsonpath='{.status.readyReplicas}')"
  [ "$LISTOS" = "2" ] && break
  sleep 5
done
$K get pods
[ "$LISTOS" = "2" ] || { echo "ERROR: se esperaban 2 replicas listas y hay '$LISTOS'" >&2; exit 1; }
echo "OK: 2 replicas listas otra vez."

aviso "Registro de un pod (JSON, una linea por peticion)"
$K logs deployment/retencion-api --tail 5 || true
echo; echo "Todo correcto. Cuando termines: ./borrar.sh"
