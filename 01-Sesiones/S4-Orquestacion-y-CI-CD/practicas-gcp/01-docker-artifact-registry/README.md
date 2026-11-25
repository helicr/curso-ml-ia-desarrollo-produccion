# Práctica 1: Docker → Artifact Registry → Cloud Run

## Objetivo
Llevar la API de retención de S2 (la misma imagen del `Dockerfile` del proyecto) a la nube: construirla en Cloud Shell, guardarla en **Artifact Registry** (el almacén de imágenes de Google) y ejecutarla en **Cloud Run** (contenedores sin servidores que gestionar), como servicio **privado**.

- **Tiempo estimado:** 20-30 min (estimado, sin medir; el `docker push` de la imagen es lo más lento).
- **Coste aproximado:** sin dato (tabla oficial no consultada: [Cloud Run](https://cloud.google.com/run/pricing), [Artifact Registry](https://cloud.google.com/artifact-registry/pricing)). Con 0 instancias en reposo no hay instancia cobrando; sí hay almacenamiento de la imagen mientras exista.
- **Región:** `southamerica-west1` (Artifact Registry y Cloud Run la admiten, con fuente en el README general).
- **Dónde se ejecuta todo:** Cloud Shell (bash), dentro de `practicas-gcp/01-docker-artifact-registry`.

## Qué crea
| Recurso | Nombre |
|---|---|
| Repositorio Docker de Artifact Registry | `curso-ml-imagenes` |
| Imagen | `southamerica-west1-docker.pkg.dev/project-curso-ml-ia/curso-ml-imagenes/retencion-api:v1` |
| Servicio de Cloud Run (privado, 0-1 instancias, 1 GiB) | `retencion-api-practica` (otro nombre que el `retencion-api` del Cloud Journey, para no pisarlo) |

## Pasos
1. **Cloud Shell:** `./crear.sh`. Habilita las APIs, genera el modelo del proyecto si falta (`make pipeline` equivalente), construye la imagen con `docker build`, la sube y despliega el servicio.
2. **Cloud Shell:** `./probar.sh`. Llama a la API con un token de identidad de tu sesión (`gcloud auth print-identity-token`), sin claves.
3. **Cloud Shell:** `./borrar.sh`. (Si vas a hacer la práctica 2, hazla antes: usa esta imagen.)

## Qué debes ver
- `crear.sh` termina con `Service URL: https://retencion-api-…run.app`.
- `probar.sh`:
  - `/salud` → `{"estado":"ok"}`; `/listo` → `{"estado":"listo"}`; `/modelo` → ficha del modelo (13 variables, huella de datos).
  - `POST /predecir` con el cliente `activo` de `../clientes_ejemplo.json` → `{"probabilidad": 0.xx, …}` y la línea `OK: probabilidad de recompra a 90 dias = …`.
  - Un campo inventado → **422** (contrato estricto de la API).
  - Sin token → **401 o 403** (el servicio es privado: nada de `allUsers`).
- `borrar.sh` termina con los listados de Cloud Run y Artifact Registry vacíos.

## Qué enseña (conceptos)
Imagen frente a contenedor; registro de imágenes; etiqueta fija (`v1`, nunca `latest`); servicio privado con identidad; escala a cero.

## Si falla
| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| `docker: command not found` o no arranca el demonio | Cloud Shell sin Docker en esa sesión | Reinicia Cloud Shell; si persiste, construir con Cloud Build (`gcloud builds submit`; no incluido, sin verificar) |
| `denied: Permission … artifactregistry.repositories.uploadArtifacts` | Falta rol sobre el repositorio | Pedir `roles/artifactregistry.writer` o `roles/owner` al administrador |
| `Python 3.11 o superior` | Cloud Shell trae otra versión | Usar un entorno con Python ≥ 3.11 (`CURSO_VENV=…`) |
| El servicio no arranca (revisión sin listo) | Poca memoria o error en la imagen | `gcloud run services logs read retencion-api-practica --region southamerica-west1`; sube `MEMORIA_RUN` en `variables.sh` |
| Error de política de la organización al desplegar | La organización restringe algo (p. ej. invocaciones públicas) | Este servicio ya es privado; copia el mensaje y consúltalo con quien administra la organización |
| `probar.sh` da 403 con token | Tu usuario no tiene `roles/run.invoker` | `gcloud run services add-iam-policy-binding retencion-api-practica --region southamerica-west1 --member=user:TU_CORREO --role=roles/run.invoker` (se pierde al borrar el servicio) |

## Fuentes
- Subir imágenes a Artifact Registry: https://docs.cloud.google.com/artifact-registry/docs/docker/store-docker-container-images (no abierta durante la preparación; sin verificar los flags más allá de lo que usa el proyecto en `deploy/gcp/imagen.sh`)
- Desplegar en Cloud Run: https://docs.cloud.google.com/run/docs/deploying
