# Kubernetes, Pods, GKE y OpenShift (guía breve del curso)

Esta guía sitúa los conceptos de orquestación que aparecen en el taller. Es un texto
original, deliberadamente corto, para consultar hechos concretos del laboratorio.

## De un contenedor a un Pod

Docker nos sirve para construir y probar `retencion-api:local` en el portátil. Cuando
queremos varias réplicas, reinicios automáticos y una IP estable de servicio, entra
en juego un orquestador.

En Kubernetes, la unidad mínima de despliegue es el **Pod**. Un Pod encapsula uno o
más contenedores que comparten red y, si se configura, volúmenes. En nuestro ejemplo,
el Pod lleva un solo contenedor: la API de retención, escuchando en el puerto 8080.

Un **Deployment** declara el estado deseado. En el manifiesto de ejemplo del curso,
el Deployment de la API tiene **2 réplicas**. Si un Pod cae, el ReplicaSet arranca
otro. Un **Service** de tipo ClusterIP expone esas réplicas dentro del clúster en el
puerto 8080.

## Laboratorio local: kind, no un clúster real

En el aula practicamos con **kind** (Kubernetes in Docker) sobre la máquina del
estudiante o en WSL. No es obligatorio un clúster gestionado para aprobar el
laboratorio de orquestación. El flujo típico es:

1. Construir la imagen `retencion-api:local`.
2. Cargarla en kind (`kind load docker-image retencion-api:local`).
3. Aplicar el manifiesto de Deployment y Service.
4. Comprobar que las dos réplicas responden en `/salud`.

## GKE y OpenShift, en una frase cada uno

**GKE** (Google Kubernetes Engine) es el servicio gestionado de Kubernetes en Google
Cloud. El curso lo menciona como destino posible de producción, no como requisito del
Avance 3.

**OpenShift** es una plataforma de Red Hat construida sobre Kubernetes, con una
consola, rutas y políticas de seguridad más opinadas (por ejemplo, suelen evitar que
los contenedores corran como root, algo que ya anticipamos en el Dockerfile).

La diferencia práctica para el estudiante: el manifiesto de Kubernetes estándar suele
abrir la puerta a ambos; OpenShift puede exigir ajustes de seguridad y de rutas. GKE
se acerca más a Kubernetes «vainilla», con integraciones de IAM y de balanceo de Google.

## Convenio de nombres del material de ejemplo

- Deployment: `retencion-api`.
- Service: `retencion-api-svc`.
- *Namespace* de laboratorio: `curso-mlops`.
- Sonda de lectura (*readiness*): HTTP GET a `/salud` en el puerto 8080.
- Recursos de ejemplo por contenedor: 250 milicores de CPU y 256 Mi de memoria como
  petición, con un límite de 512 Mi.

## Lo que no haremos en el taller

No configuraremos un *service mesh*. No es obligatorio un Ingress público en kind.
No se pide un clúster de producción real para la nota. Si un equipo quiere desplegar
en GKE, el nombre de proyecto y las credenciales son responsabilidad del equipo y no
deben subirse al repositorio.
