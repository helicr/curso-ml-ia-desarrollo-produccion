# Ejercicios · Kubernetes con kind

Se hacen en el clúster de la práctica (diapositivas, bloque B). Si lo borraste, repite los pasos 1 a 3:
```bash
cd /workspaces/curso-ml-ia-desarrollo-produccion/04-Proyecto-Base
kind create cluster --name curso
kind load docker-image retencion-api:local --name curso
kubectl apply -f deploy/kubernetes/
kubectl rollout status deployment/retencion-api --timeout=180s
```
Cada ejercicio dice si su resultado **se comprobó** en el Codespace del curso (13/11/2026) o si es **lo esperado** según la documentación de Kubernetes y el código del proyecto. Si ves otra cosa, anótala con el mensaje exacto.

Al terminar cada ejercicio, vuelve al estado declarado: `git restore deploy/kubernetes/` y `kubectl apply -f deploy/kubernetes/`.

---

## 1 · Leer el clúster *(comprobado)*
**Pregunta.** ¿En qué nodo y con qué IP corre cada pod? ¿Qué une el Service con los pods?
```bash
kubectl get pods -o wide
kubectl describe service retencion-api
kubectl get endpoints retencion-api
```
<details><summary>Solución</summary>

Los dos pods corren en `curso-control-plane` (el único nodo) con IP de la red interna `10.244.0.x`. El Service tiene `Selector: app=retencion-api`: elige los pods con esa **etiqueta**, la misma que pone la plantilla del Deployment. `Endpoints` lista las IP de los pods que están **listos**, con el puerto 8080. Si un pod no pasa la readiness, su IP desaparece de esa lista (paso 10 de la práctica).
</details>

## 2 · Escalar de forma declarativa *(comprobado con `scale` + `apply`)*
**Pregunta.** Pasa a 3 réplicas **editando el YAML**. ¿En qué se diferencia de `kubectl scale`?
```bash
sed -i 's/replicas: 2/replicas: 3/' deploy/kubernetes/deployment.yaml
kubectl apply -f deploy/kubernetes/
kubectl get deployment retencion-api
git diff deploy/kubernetes/deployment.yaml
```
<details><summary>Solución</summary>

`apply` dice `deployment.apps/retencion-api configured` y el Deployment pasa a `3/3`. La diferencia: con `kubectl scale` el cambio vive solo en el clúster y el próximo `apply` lo deshace (paso 7 de la práctica: volvió a 2); con el YAML el cambio queda **escrito**, se revisa en `git diff` y se puede subir a Git. En un equipo, el YAML del repositorio es la fuente de verdad.
</details>

## 3 · Olvidar `kind load` *(comportamiento comprobado en el paso 8)*
**Pregunta.** Construye una etiqueta nueva y despliégala sin cargarla en el clúster. ¿Qué pasa? Arréglalo.
```bash
docker tag retencion-api:local retencion-api:v2
sed -i 's|image: retencion-api:local|image: retencion-api:v2|' deploy/kubernetes/deployment.yaml
kubectl apply -f deploy/kubernetes/
sleep 20; kubectl get pods
kubectl get events --field-selector reason=Failed | tail -3
```
<details><summary>Solución</summary>

El pod nuevo se queda en `ErrImagePull` y luego `ImagePullBackOff`: el nodo de kind no tiene `retencion-api:v2` y, como `imagePullPolicy: IfNotPresent`, intenta descargarla de `docker.io/library/retencion-api:v2`, que no existe (el evento dice *pull access denied*). Los pods antiguos siguen sirviendo. Arreglo:
```bash
kind load docker-image retencion-api:v2 --name curso
kubectl rollout status deployment/retencion-api
```
En GKE el equivalente es olvidarse del `docker push` a Artifact Registry o poner mal la ruta en `image:`.
</details>

## 4 · Un pod sin modelo *(lo esperado: código de la API y pruebas de S2)*
**Pregunta.** Haz que la API busque el modelo en una carpeta vacía. ¿El pod está **vivo**? ¿Está **listo**? ¿Por qué esa diferencia es justo la que queremos?
```bash
kubectl set env deployment/retencion-api CURSO_MODELOS=/tmp/sin-modelo
sleep 30; kubectl get pods
kubectl describe pod -l app=retencion-api | grep -A2 -i readiness | tail -4
```
<details><summary>Solución</summary>

El pod nuevo queda `Running` pero `0/1`, con `RESTARTS 0`. `/salud` responde (el proceso vive: la liveness pasa) y `/listo` da **503** porque no encuentra el modelo (la readiness falla: *Readiness probe failed … statuscode: 503*). Es lo que queremos: un pod sin modelo **no recibe tráfico** (no devuelve errores a los usuarios) y **no se reinicia en bucle** (reiniciar no traería el modelo). Si `/listo` fuera la liveness, el pod entraría en `CrashLoopBackOff`. Vuelve atrás con `kubectl rollout undo deployment/retencion-api`.
</details>

## 5 · Quedarse sin memoria *(lo esperado: documentación de Kubernetes; no ejecutado)*
**Pregunta.** Baja el límite de memoria a `64Mi` y aplica. ¿Qué ocurre? Busca la palabra clave.
```bash
sed -i 's/memory: 1Gi/memory: 64Mi/' deploy/kubernetes/deployment.yaml
kubectl apply -f deploy/kubernetes/
sleep 40; kubectl get pods
kubectl describe pod -l app=retencion-api | grep -i -E 'OOMKilled|Last State|Reason' | head
```
<details><summary>Solución</summary>

La API (Python con scikit-learn, pandas y MLflow) necesita bastante más de 64 MiB para arrancar: el núcleo de Linux la termina al superar el límite. `describe pod` muestra `Last State: Terminated · Reason: OOMKilled`, `RESTARTS` sube y el estado acaba en `CrashLoopBackOff`. Los pods antiguos siguen sirviendo porque los nuevos nunca llegan a estar listos. Moraleja: `limits.memory` es un techo duro; `requests` es lo que se reserva para decidir en qué nodo cabe. Vuelve con `git restore deploy/kubernetes/ && kubectl apply -f deploy/kubernetes/`.
</details>

## 6 · Llevarlo a GKE, en papel *(sin ejecutar)*
**Pregunta.** Escribe qué cambiarías en los YAML y la lista de comandos para desplegar en GKE. ¿Qué borrarías al acabar, y en qué orden?
<details><summary>Solución</summary>

**YAML.** En `deployment.yaml`, `image: us-central1-docker.pkg.dev/PROYECTO/curso-repo/retencion-api:v1` (la ruta de Artifact Registry, con etiqueta de versión, no `local`). En `service.yaml`, `type: LoadBalancer` si quieres una IP pública (cuidado: la API no tiene autenticación).

**Comandos** (de la documentación oficial; ver `chuleta.md`): crear el repositorio (`gcloud artifacts repositories create … --repository-format=docker --location=…`), `gcloud auth configure-docker REGIÓN-docker.pkg.dev`, `docker tag` y `docker push`, `gcloud container clusters create-auto … --location=…`, `gcloud container clusters get-credentials … --location …`, `kubectl apply -f deploy/kubernetes/` y `kubectl get service retencion-api` para ver `EXTERNAL-IP`.

**Borrar, en este orden:** `kubectl delete -f deploy/kubernetes/` (así se libera el balanceador), `gcloud container clusters delete …` (lo que más cuesta) y `gcloud artifacts repositories delete …` si ya no necesitas las imágenes. Antes de crear nada: calculadora de precios y alerta de presupuesto.
</details>

---
*Para limpiar al final:* `kind delete cluster --name curso` y para el Codespace.
