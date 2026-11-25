# Configurar Google Cloud y GitHub para el laboratorio Cloud Journey (una sola vez)

Lo que hay que tener listo **antes** de lanzar `desplegar-gcp.yml`. El recorrido completo, con capturas, está en [`guia.md`](guia.md); aquí están los requisitos y los ajustes, y por qué. Todo lo de Google Cloud se hizo de verdad el 25/11/2026 con la cuenta de Google del curso; lo que no se pudo comprobar está marcado como **sin verificar**.

> **Esta práctica usa tu cuenta de Google Cloud y puede costar dinero.** Al terminar, ejecuta `borrar-gcp-s4.sh` (paso 10 de la guía).

## 1. En Google Cloud (la consola de Google Cloud)

| Qué | Cómo | Para qué |
|---|---|---|
| Cuenta de Google con Google Cloud | Activa la **prueba gratuita** con tu cuenta de Google. Importe y duración: **sin verificar**, consulta la oferta vigente | sin ella no hay proyecto ni facturación |
| Un proyecto | En «Administra recursos» crea o elige uno. El del curso es `project-curso-ml-ia`; el tuyo puede tener otro ID | todo lo que creas vive en él y se puede borrar junto |
| Una cuenta de facturación **activa** | Menú ☰ › **Facturación**. Apunta su ID (columna ACCOUNT_ID de `gcloud billing accounts list`) | un proyecto nuevo **no tiene facturación**; el script la vincula |
| La región | `southamerica-west1` (Santiago), la más cercana a Perú | latencia; todo el laboratorio va en ella |

Capturas: `img/gcp-01-proyectos.webp` (la lista de proyectos), `img/gcp-02-facturacion.webp` (la cuenta de facturación) y `img/gcp-03-facturacion-proyecto.webp` (el proyecto, aún sin facturación).

## 2. En Cloud Shell: el script `preparar-gcp-s4.sh`

Abre **Cloud Shell** (icono **>_**, arriba a la derecha de la consola), clona tu *fork* y entra en esta carpeta (órdenes exactas en la guía, paso 3). **Edita tres líneas** del principio del script:

| Línea | Valor |
|---|---|
| `PROYECTO=` | el ID de tu proyecto |
| `FACTURACION=` | el ACCOUNT_ID de tu cuenta de facturación |
| `REPO_GITHUB=` | `tu-usuario/curso-ml-ia-desarrollo-produccion` (el repositorio que podrá desplegar: **el único**) |

Después: `bash preparar-gcp-s4.sh`. Es idempotente: lo que ya existe no se vuelve a crear. Deja hecho:

1. la **facturación** vinculada al proyecto;
2. las **APIs**: Artifact Registry, Cloud Run, IAM, credenciales de IAM, STS, Resource Manager y Presupuestos;
3. **dos cuentas de servicio**: `sa-github-despliegue` (la usa GitHub Actions) y `sa-cloudrun-retencion` (con la que corre la API, **sin ningún rol**);
4. los **permisos mínimos** del desplegador: `roles/artifactregistry.writer`, `roles/run.admin` y `roles/iam.serviceAccountUser` **solo sobre** `sa-cloudrun-retencion`;
5. la **federación de identidades (WIF)**: pool `github`, proveedor `github` (OIDC de GitHub) con una `attribute-condition` que limita a tu repositorio, y el permiso `roles/iam.workloadIdentityUser` de ese repositorio sobre `sa-github-despliegue`;
6. un **presupuesto** «Curso ML e IA» de 20 EUR con alertas al 50, 90 y 100 % (avisa por correo, **no corta nada**);
7. la salida con **las cinco variables** que necesita GitHub.

Termina con «FIN · todo listo» (captura `img/gcp-23-preparar.webp`).

### Por qué sin claves

La organización del curso tiene aplicada la política `iam.disableServiceAccountKeyCreation` (captura `img/gcp-12-politica-claves.webp`): no se pueden crear claves JSON de cuentas de servicio. WIF no necesita ninguna: GitHub presenta un token OIDC de corta vida y Google lo cambia por acceso temporal de `sa-github-despliegue`. Mira también `img/gcp-09-cuentas-servicio.webp` («No hay claves», antes del script) y `img/gcp-11-wif.webp` (Workload Identity, antes del script).

## 3. El repositorio de Artifact Registry (Cloud Shell)

El script **no** lo crea. Una orden, **con la descripción sin tildes** (al teclear en Cloud Shell desde otra herramienta se perdieron):

```bash
gcloud artifacts repositories create curso --repository-format=docker --location=southamerica-west1 --description="Imagenes del curso"
```

Opcional: comprobar que la organización permite `allUsers` (la API se despliega con `--allow-unauthenticated`):

```bash
gcloud resource-manager org-policies describe iam.allowedPolicyMemberDomains --project=project-curso-ml-ia --effective
```

En el proyecto del curso salió `allValues: ALLOW` (captura `img/gcp-24-ar-y-politicas.webp`). Si en tu organización no lo permite: **sin verificar** qué ocurre exactamente.

## 4. En GitHub (la web de GitHub, en tu *fork*)

### 4.1 Las cinco variables (no son secretos)

**Settings** › **Secrets and variables** › **Actions** › pestaña **Variables** › **New repository variable**. Son *Repository variables* (no *Environment variables*). Valores del profesor; los tuyos son los que imprime **tu** script:

| Name | Value (las del profesor) |
|---|---|
| `GCP_PROYECTO` | `project-curso-ml-ia` |
| `GCP_REGION` | `southamerica-west1` |
| `GCP_PROVEEDOR_WIF` | `projects/61343545797/locations/global/workloadIdentityPools/github/providers/github` |
| `GCP_CUENTA_DESPLIEGUE` | `sa-github-despliegue@project-curso-ml-ia.iam.gserviceaccount.com` |
| `GCP_CUENTA_SERVICIO` | `sa-cloudrun-retencion@project-curso-ml-ia.iam.gserviceaccount.com` |

Captura: `img/cj-01-variables-github.webp`.

### 4.2 El *environment* `produccion` con revisores

Es el mismo del laboratorio anterior: sin él, el trabajo 2 **no espera** a nadie. Pasos y capturas en `../laboratorio-produccion-e2e/CONFIGURAR-REPOSITORIO.md`. Con un solo usuario te apruebas a ti mismo.

### 4.3 Actions activado en el *fork*

Pestaña **Actions** del *fork* y aceptar el aviso para activar los workflows.

## 5. Comprobación rápida antes de lanzar el ensayo

- [ ] `gcloud artifacts repositories list --location=southamerica-west1` (Cloud Shell) muestra `curso`.
- [ ] Las cinco variables están en **Repository variables**.
- [ ] El *environment* `produccion` tiene «1 protection rule» con tu usuario como revisor.
- [ ] El script salió con «FIN · todo listo».

## 6. Al terminar

`bash borrar-gcp-s4.sh` en Cloud Shell (idempotente; lista lo que queda). Se ejecutó de verdad el 25/11/2026 en la cuenta del curso: WIF y presupuesto borrados, listados vacíos y la facturación del proyecto se dejó vinculada a propósito. Las cinco variables de GitHub se borran a mano. Google guarda un pool de WIF borrado unos 30 días y no deja reutilizar su nombre (según su documentación; **sin verificar aquí**).
