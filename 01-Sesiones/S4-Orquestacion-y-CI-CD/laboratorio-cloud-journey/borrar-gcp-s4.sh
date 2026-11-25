#!/usr/bin/env bash
# Borrado del laboratorio Cloud Journey de S4 (en Cloud Shell, con la cuenta del curso). Es idempotente: se puede repetir.
# Borra: el servicio de Cloud Run, el repositorio "curso" de Artifact Registry (con sus imagenes), los permisos y las dos
# cuentas de servicio del laboratorio, el proveedor y el pool de federacion (WIF) y el presupuesto "Curso ML e IA".
# NO borra: el proyecto, la cuenta de servicio sa-curso-ml-ia (ya existia), las APIs habilitadas (no cuestan nada) ni las
# variables de GitHub (se borran a mano en Settings).
# Opcional: DESVINCULAR_FACTURACION=si bash borrar-gcp-s4.sh   (desvincula la cuenta de facturacion del proyecto).
# Sin tildes a proposito: al teclear en Cloud Shell desde otra herramienta se pierden.
set -euo pipefail

PROYECTO="project-curso-ml-ia"
REGION="southamerica-west1"
FACTURACION="010A93-71D9FB-551CC6"
POOL="github"
PROVEEDOR="github"
SA_DESPLIEGUE="sa-github-despliegue"
SA_SERVICIO="sa-cloudrun-retencion"
SERVICIO="retencion-api"
REPO_AR="curso"
PRESUPUESTO="Curso ML e IA"
DESVINCULAR_FACTURACION="${DESVINCULAR_FACTURACION:-no}"

paso() { echo; echo "=== $*"; }
existe() { "$@" >/dev/null 2>&1; }

paso "0 - Proyecto activo"
gcloud config set project "$PROYECTO"

paso "1 - Cloud Run: servicio $SERVICIO"
if existe gcloud run services describe "$SERVICIO" --region="$REGION"; then
  gcloud run services delete "$SERVICIO" --region="$REGION" --quiet
else
  echo "No existe (nada que borrar)."
fi

paso "2 - Artifact Registry: repositorio $REPO_AR (borra tambien las imagenes que contiene)"
if existe gcloud artifacts repositories describe "$REPO_AR" --location="$REGION"; then
  gcloud artifacts repositories delete "$REPO_AR" --location="$REGION" --quiet
else
  echo "No existe (nada que borrar)."
fi

paso "3 - Permisos del proyecto de la cuenta de despliegue"
for ROL in roles/artifactregistry.writer roles/run.admin; do
  if gcloud projects get-iam-policy "$PROYECTO" --flatten="bindings[].members" \
       --filter="bindings.role=$ROL AND bindings.members=serviceAccount:$SA_DESPLIEGUE@$PROYECTO.iam.gserviceaccount.com" \
       --format="value(bindings.role)" | grep -q .; then
    gcloud projects remove-iam-policy-binding "$PROYECTO" \
      --member="serviceAccount:$SA_DESPLIEGUE@$PROYECTO.iam.gserviceaccount.com" --role="$ROL" --condition=None --format="value(etag)" >/dev/null
    echo "  quitado $ROL"
  else
    echo "  $ROL: ya no estaba"
  fi
done

paso "4 - Cuentas de servicio del laboratorio (sa-curso-ml-ia NO se toca)"
for SA in "$SA_DESPLIEGUE" "$SA_SERVICIO"; do
  if existe gcloud iam service-accounts describe "$SA@$PROYECTO.iam.gserviceaccount.com"; then
    gcloud iam service-accounts delete "$SA@$PROYECTO.iam.gserviceaccount.com" --quiet
  else
    echo "$SA: no existe (nada que borrar)."
  fi
done

paso "5 - Federacion de identidades (WIF): proveedor y pool"
if existe gcloud iam workload-identity-pools providers describe "$PROVEEDOR" --workload-identity-pool="$POOL" --location=global; then
  gcloud iam workload-identity-pools providers delete "$PROVEEDOR" --workload-identity-pool="$POOL" --location=global --quiet
else
  echo "El proveedor no existe (nada que borrar)."
fi
if existe gcloud iam workload-identity-pools describe "$POOL" --location=global; then
  gcloud iam workload-identity-pools delete "$POOL" --location=global --quiet
else
  echo "El pool no existe (nada que borrar)."
fi
echo "Aviso: Google guarda un pool borrado unos 30 dias y no deja reutilizar su nombre; para recuperarlo:"
echo "  gcloud iam workload-identity-pools undelete $POOL --location=global"

paso "6 - Presupuesto \"$PRESUPUESTO\""
PRES=$(gcloud billing budgets list --billing-account="$FACTURACION" --filter="displayName=\"$PRESUPUESTO\"" --format="value(name)")
if [ -n "$PRES" ]; then
  while IFS= read -r NOMBRE; do
    gcloud billing budgets delete "$NOMBRE" --billing-account="$FACTURACION" --quiet
  done <<< "$PRES"
else
  echo "No existe (nada que borrar)."
fi

paso "7 - Facturacion del proyecto"
if [ "$DESVINCULAR_FACTURACION" = "si" ]; then
  gcloud billing projects unlink "$PROYECTO"
else
  echo "Se deja vinculada. Para desvincularla: DESVINCULAR_FACTURACION=si bash borrar-gcp-s4.sh"
fi

paso "8 - Lo que queda (los cuatro primeros listados deben salir vacios)"
echo "--- Cloud Run";          gcloud run services list --region="$REGION"
echo "--- Artifact Registry";  gcloud artifacts repositories list --location="$REGION"
echo "--- Pools de WIF";       gcloud iam workload-identity-pools list --location=global
echo "--- Presupuestos";       gcloud billing budgets list --billing-account="$FACTURACION" --format="value(displayName)"
echo "--- Cuentas de servicio (debe quedar solo sa-curso-ml-ia)"
gcloud iam service-accounts list --format="value(email)"
echo "--- Facturacion del proyecto"
gcloud billing projects describe "$PROYECTO" --format="value(billingEnabled)"
echo; echo "FIN · borrado terminado"
