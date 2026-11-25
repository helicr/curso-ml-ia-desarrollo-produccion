#!/usr/bin/env bash
# probar.sh (practica 01) - Donde: Cloud Shell. Solo LEE y llama a la API; no crea nada.
# El servicio es privado: se llama con un token de identidad de TU sesion (gcloud auth print-identity-token), sin claves.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/variables.sh"

comprobar_entorno
URL="$(gcloud run services describe "$NOMBRE_SERVICIO" --region "$REGION" --project "$PROYECTO" --format 'value(status.url)')"
[ -n "$URL" ] || { echo "ERROR: no existe el servicio $NOMBRE_SERVICIO. Ejecuta ./crear.sh" >&2; exit 1; }
TOKEN="$(gcloud auth print-identity-token)"
CUERPO="$(python3 -c "import json,sys; print(json.dumps(json.load(open(sys.argv[1]))['activo']))" "$CLIENTES_EJEMPLO")"
echo "URL: $URL"

aviso "GET /salud (el proceso responde)"
curl -fsS -H "Authorization: Bearer $TOKEN" "$URL/salud"; echo

aviso "GET /listo (el modelo esta cargado)"
curl -fsS -H "Authorization: Bearer $TOKEN" "$URL/listo"; echo

aviso "GET /modelo (que modelo es)"
curl -fsS -H "Authorization: Bearer $TOKEN" "$URL/modelo"; echo

aviso "POST /predecir (cliente activo del ejemplo)"
RESPUESTA="$(curl -fsS -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "$CUERPO" "$URL/predecir")"
echo "$RESPUESTA"
python3 - "$RESPUESTA" <<'PY'
import json, sys
p = json.loads(sys.argv[1])["probabilidad"]
assert 0.0 <= p <= 1.0, p
print(f"OK: probabilidad de recompra a 90 dias = {p:.3f}")
PY

aviso "POST /predecir con un campo que no existe: debe dar 422 (contrato estricto)"
MALO="$(python3 -c "import json,sys; d=json.load(open(sys.argv[1]))['activo']; d['campo_inventado']=1; print(json.dumps(d))" "$CLIENTES_EJEMPLO")"
CODIGO="$(curl -s -o /dev/null -w '%{http_code}' -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "$MALO" "$URL/predecir")"
echo "Codigo HTTP: $CODIGO"
[ "$CODIGO" = "422" ] || { echo "ERROR: se esperaba 422" >&2; exit 1; }

aviso "Sin token: debe dar 401 o 403 (el servicio es privado)"
CODIGO="$(curl -s -o /dev/null -w '%{http_code}' "$URL/salud")"
echo "Codigo HTTP: $CODIGO"
case "$CODIGO" in 401|403) echo "OK: privado";; *) echo "ERROR: el servicio responde sin token" >&2; exit 1;; esac

aviso "Ultimas lineas del registro de la API (JSON, sin datos del cliente)"
gcloud run services logs read "$NOMBRE_SERVICIO" --region "$REGION" --project "$PROYECTO" --limit 5 || true
echo; echo "Todo correcto. Cuando termines: ./borrar.sh"
