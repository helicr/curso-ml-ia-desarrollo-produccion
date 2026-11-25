# Práctica 2: Kubernetes en GKE Autopilot

## Objetivo
Ver los tres objetos básicos de Kubernetes con la **misma imagen** de la práctica 1:

| Objeto | En una frase | Fichero |
|---|---|---|
| **Pod** | La unidad mínima: uno o más contenedores que viven juntos. Nace y muere | (lo crea el Deployment) |
| **Deployment** | «Quiero N pods de esta imagen y siempre N»: repone los que caen y hace relevos | `manifiestos/deployment.yaml` |
| **Service** | Un nombre y una IP estables delante de los pods; reparte entre los que están *listos* | `manifiestos/service.yaml` |

Además: `readinessProbe` (`/listo`) y `livenessProbe` (`/salud`) de la API, escalado a 2 réplicas y autorreparación al borrar un pod.

- **Tiempo estimado:** 25-35 min (estimado, sin medir; crear el clúster es lo más lento).
- **Coste aproximado:** sin dato ([precios de GKE](https://cloud.google.com/kubernetes-engine/pricing); Autopilot cobra por los recursos que piden los pods, más una cuota de clúster que se detalla en esa página). Se cobra mientras el clúster exista: **bórralo al acabar**.
- **Región:** `southamerica-west1`. GKE Autopilot en Santiago: **sin verificar** (la página de Autopilot no la nombra).
- **Requisito:** haber hecho `crear.sh` de la práctica 01 (la imagen debe estar en Artifact Registry).

## Qué crea
Clúster GKE Autopilot `curso-ml-gke` (regional, 1 clúster) y, dentro: namespace `curso`, Deployment `retencion-api` (1 réplica; 2 tras `probar.sh`), Service `retencion-api` (tipo `ClusterIP`: sin IP pública ni balanceador de pago).

## Pasos
1. **Cloud Shell:** `./crear.sh` (crea el clúster, `get-credentials`, `kubectl apply` de los tres YAML y espera a que el pod esté listo).
2. **Cloud Shell:** `./probar.sh` (API a través del Service con `kubectl port-forward`, escala a 2 réplicas, borra un pod).
3. Para mirar a mano (**Cloud Shell**): `kubectl -n curso get deployment,pods,svc` · `kubectl -n curso describe pod -l app=retencion-api` · `kubectl -n curso logs deployment/retencion-api`.
4. **Cloud Shell:** `./borrar.sh`.

La consola web también lo muestra: menú ☰ > Kubernetes Engine > Cargas de trabajo.

## Qué debes ver
- `crear.sh` acaba con `deployment "retencion-api" successfully rolled out` y un pod `1/1 Running`.
- `probar.sh`: `{"estado":"listo"}`, la probabilidad del cliente `activo`, luego 2 pods `Running`, y tras borrar uno, otra vez `2` réplicas listas (`OK: 2 replicas listas otra vez.`).
- `borrar.sh`: el listado de clústeres sale vacío.

## Diferencias con el laboratorio de `kind` (S3)
Aquí la imagen se **descarga** de Artifact Registry (en `kind` se cargaba a mano con `kind load`); en Autopilot los límites de recursos se igualan a lo pedido; el Service es `ClusterIP` y se entra con `port-forward` en vez de exponerlo a Internet.

## Si falla
| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| `ERROR: no encuentro …retencion-api:v1` | No se hizo la práctica 01 (o se borró) | Ejecutar `../01-docker-artifact-registry/crear.sh` |
| Pod en `ImagePullBackOff` | Los nodos no pueden leer Artifact Registry | `kubectl -n curso describe pod …`; dar `roles/artifactregistry.reader` a la cuenta de Compute por defecto del proyecto |
| Pod `Pending` mucho rato | Autopilot está creando el nodo | Espera unos minutos; `kubectl -n curso describe pod …` (eventos) |
| Pod `CrashLoopBackOff` | La app no arranca | `kubectl -n curso logs deployment/retencion-api --previous` |
| Error al crear el clúster por región o política | Autopilot no disponible en la región o política de la organización | Copia el mensaje; alternativa `export CURSO_REGION=southamerica-east1` (y repetir la práctica 01 en esa región) |
| `gke-gcloud-auth-plugin` no encontrado | Plugin ausente | `gcloud components install gke-gcloud-auth-plugin` (en Cloud Shell suele venir instalado) |

## Fuentes
- Crear un clúster Autopilot: https://docs.cloud.google.com/kubernetes-engine/docs/how-to/creating-an-autopilot-cluster (no abierta durante la preparación; `create-auto --region` es el uso habitual: sin verificar)
- Manifiestos basados en `04-Proyecto-Base/deploy/kubernetes/`.
