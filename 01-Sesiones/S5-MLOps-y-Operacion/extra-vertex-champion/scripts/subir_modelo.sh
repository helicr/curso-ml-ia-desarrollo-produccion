#!/usr/bin/env bash
# subir_modelo.sh - Donde: Cloud Shell. Idempotente.   Uso:  scripts/subir_modelo.sh [VERSION_MLFLOW]
#
# QUE HACE: lleva el champion de MLflow (o la versión que pidas) al Model Registry de Vertex AI como UNA VERSIÓN NUEVA del modelo.
#   1. Genera vertex-manifiesto.json desde MLflow (versión, AUC, huella de datos, etiquetas) y el contexto de la imagen con el modelo dentro.
#   2. Crea (si falta) el repositorio de Artifact Registry y construye y sube la imagen, con la etiqueta = versión de MLflow + huella.
#   3. Sube el modelo a Vertex: la primera vez, el modelo; las siguientes, una VERSIÓN nueva con --parent-model y alias (champion y mlflow-vN).
# QUE COSTE TIENE: subir el modelo y la imagen cuesta almacenamiento (sin dato: https://cloud.google.com/vertex-ai/pricing); un modelo SUBIDO
#   pero NO desplegado no usa máquinas. Lo que cobra es desplegarlo (desplegar.sh). Se borra todo con scripts/borrar.sh.
# Fuentes: https://docs.cloud.google.com/sdk/gcloud/reference/ai/models/upload
#          https://docs.cloud.google.com/vertex-ai/docs/predictions/custom-container-requirements
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/variables.sh"
VERSION_PEDIDA="${1:-}"

comprobar_entorno
# Habilitar una API es gratis y NO se deshace al borrar. En los workflows no se hace (la cuenta de despliegue no tiene ese permiso:
# lo deja hecho preparar_gcp.sh): CURSO_SIN_HABILITAR_APIS=1.
if [ "${CURSO_SIN_HABILITAR_APIS:-0}" != "1" ]; then
  gcloud services enable aiplatform.googleapis.com artifactregistry.googleapis.com --project "$PROYECTO"
fi

aviso "1. Manifiesto del champion y contexto de la imagen"
if [ "${CURSO_REUTILIZAR:-0}" = "1" ] && [ -f "$MANIFIESTO" ] && [ -d "$CONTEXTO" ]; then
  # Lo usan los workflows: el manifiesto y el contexto los dejó el trabajo anterior (el que probó la imagen); aquí no hay registro de MLflow.
  echo "Se reutilizan $MANIFIESTO y $CONTEXTO (CURSO_REUTILIZAR=1)."
else
  if [ -n "$VERSION_PEDIDA" ]; then
    "$PY" "$DIR_EXTRA/manifiesto_champion.py" generar --version "$VERSION_PEDIDA" --salida "$MANIFIESTO"
  else
    "$PY" "$DIR_EXTRA/manifiesto_champion.py" generar --salida "$MANIFIESTO"
  fi
  (cd "$DIR_EXTRA" && "$PY" preparar_contexto.py --manifiesto "$MANIFIESTO" --destino "$CONTEXTO")
fi
ETIQUETA_IMAGEN="$(mf etiqueta_imagen)"
ALIAS_VERSION="$(mf alias_vertex)"
IMAGEN="$REGISTRO_IMAGENES/$NOMBRE_IMAGEN:$ETIQUETA_IMAGEN"

aviso "2. Artifact Registry ($REPO_AR, $REGION) y la imagen $NOMBRE_IMAGEN:$ETIQUETA_IMAGEN"
if existe gcloud artifacts repositories describe "$REPO_AR" --location "$REGION" --project "$PROYECTO"; then
  echo "Ya existe el repositorio $REPO_AR."
else
  gcloud artifacts repositories create "$REPO_AR" --repository-format docker --location "$REGION" --project "$PROYECTO" \
    --description "Imagenes del curso ML e IA" --labels curso=ml-ia
fi
if existe gcloud artifacts docker images describe "$IMAGEN" --project "$PROYECTO"; then
  echo "La imagen $ETIQUETA_IMAGEN ya está subida: no se vuelve a construir."
else
  # Plataforma de Vertex: linux/amd64. Docker viene en Cloud Shell (SIN VERIFICAR); si no hay, ver «Si falla» en guia.md.
  docker build --platform linux/amd64 -f "$CONTEXTO/Dockerfile.vertex" -t "$IMAGEN" "$CONTEXTO"
  gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet
  docker push "$IMAGEN"
fi

aviso "3. Modelo en el Model Registry de Vertex AI"
ETIQUETAS="$(mf etiquetas_gcloud)"
DESCRIPCION="MLflow $(mf modelo) v$(mf mlflow_version), huella $(mf huella_datos)"
COMUNES=(--project "$PROYECTO" --region "$REGION" --display-name "$NOMBRE_MODELO" --container-image-uri "$IMAGEN"
         --container-ports "$PUERTO" --container-predict-route "$RUTA_PREDICT" --container-health-route "$RUTA_SALUD"
         --labels "$ETIQUETAS" --version-description "$DESCRIPCION")
if existe gcloud ai models describe "$NOMBRE_MODELO" --region "$REGION" --project "$PROYECTO"; then
  guardar_versiones
  if [ -n "$(ayuda version-modelo --json "$TRABAJO/versiones.json" --alias "$ALIAS_VERSION")" ]; then
    echo "La versión $ALIAS_VERSION ya está en el Model Registry: no se sube otra."
  else
    gcloud ai models upload "${COMUNES[@]}" \
      --parent-model "projects/$PROYECTO/locations/$REGION/models/$NOMBRE_MODELO" \
      --version-aliases "$ALIAS_CHAMPION,$ALIAS_VERSION"
  fi
else
  gcloud ai models upload "${COMUNES[@]}" --model-id "$NOMBRE_MODELO" --version-aliases "$ALIAS_CHAMPION,$ALIAS_VERSION"
fi
guardar_versiones
VERSION_VERTEX="$(ayuda version-modelo --json "$TRABAJO/versiones.json" --alias "$ALIAS_VERSION")"
[ -n "$VERSION_VERTEX" ] || { echo "ERROR: no encuentro en Vertex la versión con el alias $ALIAS_VERSION (mira gcloud ai models list-version $NOMBRE_MODELO)." >&2; exit 1; }
echo "$VERSION_VERTEX" > "$TRABAJO/version_vertex.txt"

echo; echo "Listo: MLflow v$(mf mlflow_version) -> $NOMBRE_MODELO versión $VERSION_VERTEX (alias $ALIAS_VERSION). Sin desplegar: no cobra máquinas."
echo "Siguiente: scripts/desplegar.sh   y, SIN DEJARLO PARA DESPUÉS, scripts/borrar.sh"
