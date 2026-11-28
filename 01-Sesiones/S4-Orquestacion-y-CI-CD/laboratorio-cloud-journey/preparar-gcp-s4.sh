#!/usr/bin/env bash
# Preparación de Google Cloud para S4 (una vez, en Cloud Shell, con la cuenta del curso).
# Qué deja hecho: facturación vinculada, APIs, cuenta de servicio de despliegue con permisos mínimos,
# federación de identidades (WIF) para GitHub Actions SIN claves, y una alerta de presupuesto.
# NO crea Artifact Registry ni despliega nada en Cloud Run (eso va en el laboratorio).
set -euo pipefail

PROYECTO="project-curso-ml-ia"
REGION="southamerica-west1"
FACTURACION="${FACTURACION:-PON-AQUI-TU-ACCOUNT_ID}"
REPO_GITHUB="helicr/curso-ml-ia-desarrollo-produccion"
POOL="github"
PROVEEDOR="github"
SA_DESPLIEGUE="sa-github-despliegue"
SA_SERVICIO="sa-cloudrun-retencion"

if [ "$FACTURACION" = "PON-AQUI-TU-ACCOUNT_ID" ]; then
  echo "Falta tu ACCOUNT_ID de facturacion. Mira el tuyo con:  gcloud billing accounts list"
  echo "Y ponlo en la linea FACTURACION= de este script, o lanza:  FACTURACION=XXXXXX-XXXXXX-XXXXXX bash $0"
  exit 1
fi
paso() { echo; echo "=== $*"; }

paso "0 · Proyecto activo"
gcloud config set project "$PROYECTO"
NUMERO=$(gcloud projects describe "$PROYECTO" --format='value(projectNumber)')
echo "Número del proyecto: $NUMERO"

paso "1 · Vincular la facturación (prueba gratuita)"
gcloud billing projects link "$PROYECTO" --billing-account="$FACTURACION"

paso "2 · APIs"
gcloud services enable artifactregistry.googleapis.com run.googleapis.com iam.googleapis.com \
  iamcredentials.googleapis.com sts.googleapis.com cloudresourcemanager.googleapis.com billingbudgets.googleapis.com

paso "3 · Cuentas de servicio: una para desplegar (la usa GitHub) y otra con la que corre el servicio (sin roles)"
gcloud iam service-accounts describe "$SA_DESPLIEGUE@$PROYECTO.iam.gserviceaccount.com" >/dev/null 2>&1 || \
  gcloud iam service-accounts create "$SA_DESPLIEGUE" --display-name="GitHub Actions: publicar y desplegar"
gcloud iam service-accounts describe "$SA_SERVICIO@$PROYECTO.iam.gserviceaccount.com" >/dev/null 2>&1 || \
  gcloud iam service-accounts create "$SA_SERVICIO" --display-name="Cloud Run: servicio retencion-api (sin permisos)"

paso "4 · Permisos mínimos de la cuenta de despliegue"
for ROL in roles/artifactregistry.writer roles/run.admin; do
  gcloud projects add-iam-policy-binding "$PROYECTO" --member="serviceAccount:$SA_DESPLIEGUE@$PROYECTO.iam.gserviceaccount.com" \
    --role="$ROL" --condition=None --format='value(etag)' >/dev/null
  echo "  $ROL"
done
gcloud iam service-accounts add-iam-policy-binding "$SA_SERVICIO@$PROYECTO.iam.gserviceaccount.com" \
  --member="serviceAccount:$SA_DESPLIEGUE@$PROYECTO.iam.gserviceaccount.com" --role=roles/iam.serviceAccountUser --format='value(etag)' >/dev/null
echo "  roles/iam.serviceAccountUser sobre $SA_SERVICIO (para desplegar el servicio con esa identidad)"

paso "5 · Federación de identidades para GitHub Actions (sin claves)"
# Un pool o un proveedor BORRADO sigue respondiendo a «describe» (estado DELETED) durante 30 días y su nombre no se puede
# reutilizar: por eso se mira el ESTADO y no solo si responde. Visto el 26/11/2026 al repetir el laboratorio un día después de
# borrarlo: el script daba por bueno el pool borrado y «create-oidc» fallaba con NOT_FOUND.
ESTADO_POOL="$(gcloud iam workload-identity-pools describe "$POOL" --location=global --format='value(state)' 2>/dev/null || true)"
case "$ESTADO_POOL" in
  ACTIVE) echo "  El pool $POOL ya existe." ;;
  DELETED)
    echo "  El pool $POOL estaba borrado (Google lo guarda 30 días): lo restauro."
    gcloud iam workload-identity-pools undelete "$POOL" --location=global --format='value(name)' >/dev/null ;;
  *) gcloud iam workload-identity-pools create "$POOL" --location=global --display-name="GitHub Actions" ;;
esac

ESTADO_PROV="$(gcloud iam workload-identity-pools providers describe "$PROVEEDOR" --workload-identity-pool="$POOL" --location=global --format='value(state)' 2>/dev/null || true)"
case "$ESTADO_PROV" in
  ACTIVE) echo "  El proveedor $PROVEEDOR ya existe." ;;
  DELETED)
    echo "  El proveedor $PROVEEDOR estaba borrado: lo restauro."
    gcloud iam workload-identity-pools providers undelete "$PROVEEDOR" --workload-identity-pool="$POOL" --location=global --format='value(name)' >/dev/null
    sleep 5 ;;
  *) gcloud iam workload-identity-pools providers create-oidc "$PROVEEDOR" --workload-identity-pool="$POOL" --location=global \
       --display-name="GitHub" --issuer-uri="https://token.actions.githubusercontent.com" \
       --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
       --attribute-condition="assertion.repository=='$REPO_GITHUB'" ;;
esac
# Un proveedor restaurado conserva la condición de ANTES: se pone la de ahora (por si ahora es otro repositorio).
gcloud iam workload-identity-pools providers update-oidc "$PROVEEDOR" --workload-identity-pool="$POOL" --location=global \
  --attribute-condition="assertion.repository=='$REPO_GITHUB'" --format='value(name)' >/dev/null
gcloud iam service-accounts add-iam-policy-binding "$SA_DESPLIEGUE@$PROYECTO.iam.gserviceaccount.com" \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/$NUMERO/locations/global/workloadIdentityPools/$POOL/attribute.repository/$REPO_GITHUB" \
  --format='value(etag)' >/dev/null
echo "  solo el repositorio $REPO_GITHUB puede actuar como $SA_DESPLIEGUE"

paso "6 · Alerta de presupuesto (avisa por correo; no corta nada)"
if ! gcloud billing budgets list --billing-account="$FACTURACION" --format='value(displayName)' | grep -qx "Curso ML e IA"; then
  gcloud billing budgets create --billing-account="$FACTURACION" --display-name="Curso ML e IA" --budget-amount=20EUR \
    --filter-projects="projects/$PROYECTO" --threshold-rule=percent=0.5 --threshold-rule=percent=0.9 --threshold-rule=percent=1.0
fi

paso "7 · Lo que va en GitHub (Settings → Secrets and variables → Actions → Variables; NO son secretos)"
echo "GCP_PROYECTO=$PROYECTO"
echo "GCP_REGION=$REGION"
echo "GCP_PROVEEDOR_WIF=projects/$NUMERO/locations/global/workloadIdentityPools/$POOL/providers/$PROVEEDOR"
echo "GCP_CUENTA_DESPLIEGUE=$SA_DESPLIEGUE@$PROYECTO.iam.gserviceaccount.com"
echo "GCP_CUENTA_SERVICIO=$SA_SERVICIO@$PROYECTO.iam.gserviceaccount.com"
echo; echo "FIN · todo listo"
