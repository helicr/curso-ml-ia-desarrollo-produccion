# Chuleta · Docker, Kubernetes (kind) y GKE

Para tener a mano en S2 y S3. Todo se ejecuta en la **terminal del Codespace**, en `04-Proyecto-Base`, con `(env-ia-mlops)`.
Las diapositivas con dibujos y capturas están en [`index.html`](index.html); los ejercicios, en [`ejercicios.md`](ejercicios.md).

**Qué se probó.** Docker: bloque 4 de S2 en el Codespace del curso (12/11/2026), salvo `docker push`. kind y kubectl: la práctica completa en el Codespace (13/11/2026; kind v0.27.0, Kubernetes v1.32.2, kubectl v1.37.2). **GKE y Artifact Registry: sin ejecutar**; los comandos salen de la documentación oficial de Google (consultada el 13/11/2026).

## Vocabulario en una línea
| Palabra | Qué es |
|---|---|
| **Imagen** | El molde: sistema base + dependencias + código + modelo. No cambia. `retencion-api:local` ocupa 826 MB. |
| **Contenedor** | Una ejecución de una imagen. Tiene estado y se puede borrar. |
| **Registro** | Almacén de imágenes. En GCP, Artifact Registry. En kind se sustituye por `kind load`. |
| **Clúster** | Un conjunto de máquinas (nodos) que Kubernetes gobierna. kind crea uno dentro de Docker. |
| **Nodo** | Una máquina del clúster. En kind, un contenedor (`curso-control-plane`). |
| **Pod** | La unidad que Kubernetes arranca: uno o más contenedores con una IP propia. Va y viene. |
| **Deployment** | «Quiero N réplicas de esta imagen así configuradas». Crea un ReplicaSet. |
| **ReplicaSet** | Cuenta los pods y repone los que faltan. |
| **Service** | Nombre e IP estables delante de los pods; reparte entre los que están **listos**. |
| **Readiness** | ¿Puede recibir tráfico? (`/listo`). Si falla: el pod sigue vivo pero sin tráfico (`0/1`). |
| **Liveness** | ¿Sigue vivo? (`/salud`). Si falla: Kubernetes reinicia el contenedor. |
| **Declarativo** | Describes el estado deseado (YAML) y Kubernetes lo mantiene. `kubectl apply` manda sobre los cambios a mano. |

## Docker
| Para | Comando |
|---|---|
| Construir | `docker build -f deploy/docker/Dockerfile -t retencion-api:local .` |
| Ver imágenes | `docker image ls` (Docker 29: DISK USAGE y CONTENT SIZE) |
| Arrancar | `docker run -d --name api -p 8080:8080 retencion-api:local` |
| Ver contenedores | `docker ps` · `docker ps -a` |
| Registros | `docker logs api` · `docker logs -f api` |
| Ejecutar dentro | `docker exec api id -u` · `docker exec -it api sh` |
| Parar y borrar | `docker stop api` · `docker rm -f api` |
| Etiquetar para un registro | `docker tag retencion-api:local LOCATION-docker.pkg.dev/PROYECTO/REPO/retencion-api:v1` |
| Subir | `docker push LOCATION-docker.pkg.dev/PROYECTO/REPO/retencion-api:v1` *(sin ejecutar)* |
| Espacio | `docker system df` · `docker system prune` |

## kind
| Para | Comando | Tiempo en el Codespace |
|---|---|---|
| Crear un clúster | `kind create cluster --name curso` | 1 min 4 s |
| Ver clústeres | `kind get clusters` | |
| Dar una imagen al clúster | `kind load docker-image retencion-api:local --name curso` | 42 s |
| Borrar el clúster | `kind delete cluster --name curso` | 25 s |

## kubectl
| Para | Comando |
|---|---|
| ¿A qué clúster hablo? | `kubectl config current-context` (en kind: `kind-curso`) |
| Desplegar / actualizar | `kubectl apply -f deploy/kubernetes/` |
| Borrar lo desplegado | `kubectl delete -f deploy/kubernetes/` |
| Ver todo | `kubectl get deployments,replicasets,pods,services` |
| Pods con IP y nodo | `kubectl get pods -o wide` · seguir cambios: `kubectl get pods -w` |
| A quién manda tráfico el Service | `kubectl get endpoints retencion-api` |
| Esperar a que esté listo | `kubectl rollout status deployment/retencion-api --timeout=180s` |
| Por qué algo no va | `kubectl describe pod NOMBRE` (sección *Events*) |
| Eventos del clúster | `kubectl get events --sort-by=.lastTimestamp` |
| Registros | `kubectl logs deployment/retencion-api` · `kubectl logs POD --previous` (intento anterior) |
| Hablar con la API | `kubectl port-forward service/retencion-api 8080:80 &` y `curl http://127.0.0.1:8080/listo` |
| Escalar (a mano) | `kubectl scale deployment/retencion-api --replicas=3` |
| Cambiar la imagen (a mano) | `kubectl set image deployment/retencion-api api=IMAGEN` |
| Deshacer el último despliegue | `kubectl rollout undo deployment/retencion-api` |
| Historial | `kubectl rollout history deployment/retencion-api` |
| Entrar en un pod | `kubectl exec -it POD -- sh` |
| Ayuda de un campo del YAML | `kubectl explain deployment.spec.template.spec.containers` |

Abreviaturas: `po` pods · `deploy` deployments · `rs` replicasets · `svc` services · `ep` endpoints.

## Estados que verás
| Estado | Qué significa | Qué hacer |
|---|---|---|
| `ContainerCreating` | Arrancando | Esperar unos segundos |
| `Running 1/1` | Vivo y listo | Nada |
| `Running 0/1` | Vivo pero la readiness falla | `describe pod`: «Readiness probe failed» |
| `ErrImagePull` / `ImagePullBackOff` | No encuentra la imagen | `kind load …` o revisar `image:` |
| `CrashLoopBackOff` | El proceso muere una y otra vez | `kubectl logs POD --previous` |
| `OOMKilled` | Superó el límite de memoria | Subir `limits.memory` |
| `Pending` | No cabe en ningún nodo | `describe pod`: «Insufficient …» |
| `Terminating` | Se está borrando | Esperar |

## GKE (sin ejecutar en el curso)
```bash
# repositorio de imágenes y permisos de Docker
gcloud artifacts repositories create curso-repo --repository-format=docker --location=us-central1 --description="Imágenes del curso"
gcloud auth configure-docker us-central1-docker.pkg.dev
# subir la imagen
docker tag retencion-api:local us-central1-docker.pkg.dev/PROYECTO/curso-repo/retencion-api:v1
docker push us-central1-docker.pkg.dev/PROYECTO/curso-repo/retencion-api:v1
# clúster Autopilot y credenciales para kubectl
gcloud container clusters create-auto curso-gke --location=us-central1
gcloud container clusters get-credentials curso-gke --location us-central1
# desplegar: en deployment.yaml, image: con la ruta de Artifact Registry; en service.yaml, type: LoadBalancer
kubectl apply -f deploy/kubernetes/
kubectl get service retencion-api        # columna EXTERNAL-IP
# borrar al terminar (lo que cuesta dinero mientras existe)
gcloud container clusters delete curso-gke --location us-central1
gcloud artifacts repositories delete curso-repo --location=us-central1
```
Fuentes: <https://docs.cloud.google.com/kubernetes-engine/docs/deploy-app-cluster> · <https://docs.cloud.google.com/artifact-registry/docs/docker/store-docker-container-images> (consultadas el 13/11/2026). No se dan precios: dependen de la región y del modo; usa la calculadora de Google Cloud y una alerta de presupuesto.
