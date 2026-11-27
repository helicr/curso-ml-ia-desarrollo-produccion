# Guía de Docker para el laboratorio de retención

Esta guía resume cómo empaquetar la API del proyecto de retención de clientes en un
contenedor, pensada para ejecutarse en un portátil con CPU. Es un texto original del
curso. No reproduce documentación ajena.

## Idea central

Una **imagen** es una receta inmutable (capas de sistema de archivos más metadatos).
Un **contenedor** es un proceso que arranca a partir de esa imagen. Si la receta es
buena, el mismo artefacto corre en el portátil, en Codespaces y, más adelante, en un
Pod de Kubernetes.

## La imagen de ejemplo

En el repositorio del curso la API de ejemplo se publica con este nombre local:

```
retencion-api:local
```

El Dockerfile vive en `deploy/docker/Dockerfile`. La construcción se lanza **desde la
raíz del repositorio**, no desde la carpeta `deploy/docker/`, para que el contexto
incluya el código y el `lock` de dependencias:

```
docker build -f deploy/docker/Dockerfile -t retencion-api:local .
```

El contenedor expone el puerto **8080**. El servicio (Uvicorn) atiende `0.0.0.0:8080`.
El *healthcheck* de la imagen consulta la ruta **`/salud`**. Si esa ruta no responde
con éxito, el orquestador no debe enviar tráfico a esa réplica.

## Buenas prácticas que usamos en el taller

1. **Caché de capas.** Se copia primero el archivo de bloqueo de dependencias y se
   instalan paquetes; el código de la aplicación se copia después. Así un cambio en
   un `.py` no invalida la capa pesada de librerías.
2. **Usuario no root.** El proceso de la API no corre como administrador dentro del
   contenedor.
3. **Una responsabilidad.** Esta imagen sirve la API. El seguimiento de experimentos
   (MLflow) y la base de datos no se meten en el mismo contenedor en el laboratorio.
4. **Etiquetas explícitas.** Evitamos `latest` como única etiqueta cuando guardamos
   un artefacto que vamos a desplegar.

## Arranque local (comprobación)

```
docker run --rm -p 8080:8080 retencion-api:local
```

Comprobaciones útiles, en otra terminal:

- Documentación interactiva: `http://127.0.0.1:8080/docs`.
- Salud: `http://127.0.0.1:8080/salud`.
- Predicción por lotes: `POST /predecir_lote` (el cuerpo es un JSON con filas).

`docker logs`, `docker exec` e `docker inspect` sirven para diagnosticar. `docker history`
muestra las capas y ayuda a ver si el caché se está aprovechando.

## Codespaces y el 404 en `/docs`

Si abres la API en GitHub Codespaces y el navegador muestra 404, revisa la pestaña
PORTS: el puerto 8080 debe estar reenviado y, si hace falta, con visibilidad pública.
Un 404 en `*.app.github.dev` casi nunca significa que Uvicorn esté «mal instalado»;
casi siempre es un tema de reenvío o de que el proceso no está escuchando en `0.0.0.0`.

## Límites de este laboratorio

No usamos un registro privado obligatorio. Para el Avance 2 basta la imagen local
`retencion-api:local` y las evidencias de construcción, arranque y `/salud`. El paso
a un registro (Artifact Registry, por ejemplo) se discute en la sesión de despliegue
en la nube, no es un prerrequisito de Docker en el portátil.
