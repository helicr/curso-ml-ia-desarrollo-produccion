# Del ordenador al servicio: la API y la interfaz, paso a paso

> **La pregunta que nos hicieron.** «Ya tenemos el modelo expuesto en una API. Pero ¿dónde llama el usuario? ¿Cómo pone el id de un cliente, o de varios, o una lista, y recibe la predicción con una recomendación? ¿Y qué diferencia hay entre tenerlo en mi ordenador y tenerlo como un servicio de verdad?»

Esta guía responde desde lo más básico hasta el servicio final, en escalones. Cada escalón añade **una** idea y se puede ejecutar. Al terminar habrá dos contenedores que se hablan por una red, con los datos montados en solo lectura, y una lista clara de lo que todavía falta para estar en producción.

```text
 Escalón 1            Escalón 2              Escalón 3                Escalón 4                     Escalón 5         Escalón 6
 todo en mi     ──►   la API en una   ──►    la interfaz en     ──►   dos contenedores que   ──►   lo mismo en  ──►  lo que falta para
 ordenador            imagen                 su propia imagen         se hablan (red + volumen)     un archivo        producción (S3-S5)
 (procesos)           (bloque 4 de S2)                                                              (compose)
```

Requisitos: haber hecho el bloque 4 de la guía de laboratorio de S2 (la imagen de la API) y haber ejecutado `python -m ia_mlops.pipeline`. Los escalones 2 a 5 necesitan Docker: en el curso, un **Codespace** (ver la guía de Codespaces). Todos los comandos se lanzan desde `04-Proyecto-Base`.

---

## 0. El mapa: cuatro piezas y quién usa cada una

| Pieza | Qué es | Dónde está | Quién la usa |
|---|---|---|---|
| **Modelo** | Un archivo: la regresión logística entrenada, con su firma (las 13 variables que espera). | `models/modelo_mlflow/` | Nadie directamente: lo carga la API. |
| **API del modelo** | Un programa que carga el modelo y responde por HTTP: «dame 13 números y te devuelvo una probabilidad». | `ia_mlops/api/` | Otros programas. |
| **Datos y variables** | La base con el historial de compras (MASTER) y el SQL que calcula las 13 variables de un cliente en una fecha. | `data/processed/curso.db` y `sql/fs/02_poblar_fs.sql` | La interfaz. |
| **Interfaz** | Una página web y un programa: «dame ids de cliente y te devuelvo probabilidad, tramo y recomendación». | `ia_mlops/interfaz/` | **Personas** (quien prepara la campaña). |

La clave está en esta tabla. **La API no sabe qué es un id de cliente**: solo sabe de variables. **La persona no sabe qué son las variables**: solo conoce el id. La interfaz traduce de una cosa a la otra:

```text
  persona ──ids──► INTERFAZ ──(1) SQL de FS sobre curso.db──► 13 variables por cliente
                       │
                       └──(2) POST /predecir/lote con las variables──► API ──► modelo ──► probabilidades
                       │
                       └──(3) regla de negocio (config.SEGMENTOS_RECOMPRA)──► tramo + recomendación ──► persona
```

El detalle de la interfaz (cómo calcula las variables, la regla de tramos, los endpoints) está en [`interfaz-de-consulta.md`](interfaz-de-consulta.md). Aquí lo que importa es **dónde corre cada pieza y qué cambia al moverla**.

### La arquitectura de la exposición del modelo
Dos momentos distintos: lo que se **construye** una vez por versión del modelo y lo que **ocurre** en cada consulta.

```text
 CONSTRUCCIÓN · una vez por versión del modelo
 ┌───────────┐   ┌──────────────────────┐   ┌──────────────┐   ┌─────────────────────┐   ┌─────────────┐   ┌──────────────────┐
 │Operacional│──►│Pipelines             │──►│Entrenar      │──►│Modelo + firma       │──►│Imagen API   │   │Imagen interfaz   │
 │retail.db  │   │RAW→MASTER→FS→ML      │   │MLflow        │   │models/modelo_mlflow │   │retencion-api│   │código + SQL de FS│
 └───────────┘   └──────────┬───────────┘   └──────────────┘   └─────────────────────┘   └──────┬──────┘   └────────┬─────────┘
                            │ escribe curso.db                                          docker run│         docker run │
 EJECUCIÓN · cada consulta  │                                                                    │                    │
                            │      ┌─ red «retencion» ──────────────────────────────────────────┼────────────────────┼──┐
 ┌─────────┐  (1) ids       │      │  ┌──────────────────────────┐ (3) POST 13 variables  ┌────▼─────────────────────┐ │   ┌──────────────────────┐
 │ Persona │────────────────┼──────┼─►│ Contenedor interfaz :8090│───────────────────────►│ Contenedor API :8080     │ │   │ Operación            │
 │         │◄───────────────┼──────┼──│ (publicado con -p)       │◄───────────────────────│ (sin -p: no se publica)  │ │   │ /salud · /listo      │
 └─────────┘ (5) recomendación     │  │ ids → variables → tramo  │ (4) probabilidad+avisos│ contrato = firma · modelo│ │   │ registros JSON,      │
                            │      │  └────────────┬─────────────┘                        └──────────────────────────┘ │   │ sin datos de clientes│
                            │      └───────────────┼────────────────────────────────────────────────────────────────────┘   └──────────────────────┘
                            │                      │ (2) variables en el corte (SQL de FS)
                            │               ┌──────▼───────────────┐
                            └──────────────►│ curso.db             │
                                            │ volumen solo lectura │
                                            └──────────────────────┘
```

1. La persona escribe ids en la página de la interfaz.
2. La interfaz calcula las 13 variables de cada cliente con el SQL de FS, sobre `curso.db` montada en solo lectura (la escriben los pipelines, no la interfaz).
3. Envía las variables a la API por la red; la API las valida contra la firma del modelo (422 si no cumplen).
4. La API devuelve la probabilidad y los avisos («fuera del rango visto al entrenar»).
5. La interfaz aplica la regla de tramos y devuelve tramo y recomendación.

En producción (apartado 9) **el dibujo es el mismo**; cambia en qué se convierte cada caja: Artifact Registry para las imágenes, Cloud Run para los dos contenedores, BigQuery para `curso.db`, el workflow de S4 para la construcción y registros y alertas centralizados para la operación.

Este recorrido tiene también su presentación, la que se proyecta en clase: `01-Sesiones/S2-API-y-Docker/del-ordenador-al-servicio/index.html`.

---

## 1. Conceptos básicos (todavía sin Docker)

### 1.1 Proceso y puerto
Un **proceso** es un programa en ejecución. Al lanzar `uvicorn`, tu sistema operativo crea un proceso que se queda **escuchando** en un **puerto**: un número del 0 al 65535 que identifica una «puerta» del equipo. La API escucha en el 8080 y la interfaz en el 8090. Dos procesos no pueden escuchar en el mismo puerto del mismo equipo: por eso cada pieza tiene el suyo. Si el puerto ya está ocupado, se ve `address already in use`.

### 1.2 `127.0.0.1` frente a `0.0.0.0`: quién puede llamar
Al arrancar, un servidor elige **en qué dirección escucha**:
- `127.0.0.1` (también llamado `localhost`) es la dirección de **bucle local**: solo atiende llamadas del **mismo equipo**. Ni tu compañero, ni tu móvil en la misma wifi, ni otro contenedor pueden llegar.
- `0.0.0.0` significa «en todas las direcciones de este equipo»: atiende también llamadas que llegan desde fuera, si la red y el cortafuegos las dejan pasar.

Por eso `make api` usa `--host 127.0.0.1` (para trabajar en tu equipo) y el `CMD` de las imágenes usa `--host 0.0.0.0`: dentro de un contenedor, las llamadas siempre llegan «desde fuera» del contenedor.

### 1.3 Cliente, servidor, HTTP y JSON
- El **servidor** espera peticiones: la API o la interfaz.
- El **cliente** las hace: tu navegador, `curl`, o la interfaz cuando llama a la API.

Hablan **HTTP**: un método (`GET` para leer, `POST` para enviar datos), una ruta (`/recomendar`) y un cuerpo en **JSON**. La respuesta lleva un **código**: 200 si fue bien, 422 si la petición no tiene sentido, 503 si el servicio no puede atender ahora. Una misma pieza puede ser las dos cosas: la interfaz es servidor para tu navegador y **cliente** de la API.

### 1.4 Dependencias: todo lo que un programa necesita y no está en su código
Para que la interfaz funcione hacen falta:
- **Python 3.11.**
- **Paquetes:** fastapi, uvicorn, pydantic, pandas.
- **Archivos:** `curso.db` y `sql/fs/02_poblar_fs.sql`.
- **Otro servicio:** la API.
- **Configuración:** la URL de la API.

En tu ordenador todo eso «está ahí» porque lo instalaste tú: el entorno conda, el clon del repositorio, el pipeline ejecutado. **Esa es la trampa**: funciona, pero depende de cosas que solo existen en tu equipo y que nadie más ve.

### 1.5 Configuración por variables de entorno
El código no debe llevar escrito «la API está en `http://127.0.0.1:8080`», porque en otro sitio estará en otra dirección. Esa información se pasa **desde fuera**, en **variables de entorno**, y el mismo código sirve en cualquier sitio cambiando solo la configuración. La interfaz usa tres (`ia_mlops/config.py`):

| Variable | Para qué | En tu ordenador | En el contenedor |
|---|---|---|---|
| `CURSO_URL_API` | Dónde está la API del modelo | `--url http://127.0.0.1:8080` | `http://api:8080` |
| `CURSO_DB` | Dónde está la base de datos | `data/processed/curso.db` (por defecto) | `/datos/curso.db` |
| `CURSO_DB_SOLO_LECTURA` | Abrir la base sin poder escribir | (vacía: lectura y escritura) | `1` |

### 1.6 Vivo no es lo mismo que listo
Las dos piezas responden a dos preguntas distintas:
- **`/salud` (*liveness*, «¿estás vivo?»).** ¿El proceso responde? Si no, hay que reiniciarlo.
- **`/listo` (*readiness*, «¿puedes atender?»).** ¿Tiene lo que necesita? En la API, el modelo cargado. En la interfaz, la base y la API. Si no, **reiniciar no sirve**: hay que arreglar lo que falta, y el 503 dice qué es.

Esta distinción es la que usan Docker, Compose y los orquestadores (S3–S4) para decidir qué hacer con un servicio.

---

## 2. Escalón 1 · Todo en mi ordenador

```text
   TU ORDENADOR  (conda env-ia-mlops, el clon del repositorio, models/, data/)
   ┌───────────────────────────────────────────────────────────────────────┐
   │  navegador ──► 127.0.0.1:8090  interfaz (proceso python)              │
   │                     │  lee data/processed/curso.db                     │
   │                     └──► 127.0.0.1:8080  API (proceso python) ─► models/
   └───────────────────────────────────────────────────────────────────────┘
        nadie de fuera llega: todo escucha en 127.0.0.1
```

Con el entorno activo (`conda activate env-ia-mlops`), desde `04-Proyecto-Base`:
```text
# terminal 1: la API del modelo
python -m uvicorn ia_mlops.api.app:app --host 127.0.0.1 --port 8080

# terminal 2: la interfaz, que llama a esa API
python -m ia_mlops.interfaz --url http://127.0.0.1:8080
```
En la terminal 2 se ve `Interfaz en http://127.0.0.1:8090 · predicciones: http://127.0.0.1:8080`. Abre <http://127.0.0.1:8090>, pulsa **Ejemplo** y **Predecir**. Con la muestra, el cliente `13599` sale con 99,8 %, tramo `alta`, puesto 1 de 148.

Comprueba también las dos preguntas de salud:
```text
curl http://127.0.0.1:8090/salud     →  {"estado":"ok"}
curl http://127.0.0.1:8090/listo     →  {"estado":"listo","datos":"ok","modelo":"http://127.0.0.1:8080"}
```
Para la API (Ctrl+C en la terminal 1) y repite: `/salud` sigue en 200, pero `/listo` da **503** con el motivo («La API del modelo en … no responde»). Vuelve a arrancar la API.

### Qué demuestra este escalón y por qué «no se puede sacar»
Funciona. Pero mira de qué depende:

| Depende de… | ¿Qué pasa en otro equipo? |
|---|---|
| Tu entorno conda con unas versiones concretas | Otras versiones pueden dar otras probabilidades, o no arrancar (en Windows ya vimos el error `0xc06d007f` de scikit-learn sin activar el entorno). |
| Tus rutas y tus archivos (`models/`, `curso.db`) | Si no ejecutaste el pipeline, no existen. |
| Tu sistema operativo | Los comandos y las comillas cambian entre PowerShell y bash. |
| Tu sesión abierta | Si cierras la terminal o apagas el portátil, el servicio desaparece. |
| `127.0.0.1` | Nadie más puede llamarlo. Con `--host 0.0.0.0` lo verían otros de tu red… si tu cortafuegos lo permite y tu equipo sigue encendido. |

Es el famoso «**en mi máquina funciona**». Sirve para desarrollar y para demostrar la idea. No es un servicio: no se puede entregar a otra persona tal cual, y nadie puede depender de él.

---

## 3. Conceptos de contenedores (lo mínimo para seguir)

Repaso rápido de las presentaciones *Contenedores 1* y *Contenedores 2*. Si algo no te suena, vuelve a ellas.

| Concepto | Qué es | Cómo se ve |
|---|---|---|
| **Imagen** | Una plantilla congelada: sistema base, Python, paquetes y código. No cambia. | `retencion-api:local` |
| **Contenedor** | Una imagen **en ejecución**: un proceso aislado con su sistema de archivos. Al borrarlo se pierde lo que escribió dentro. | `docker run …` |
| **Dockerfile** | La receta de la imagen, instrucción a instrucción. Cada instrucción es una **capa** que se reutiliza (caché). | `deploy/docker/Dockerfile` |
| **Contexto y `.dockerignore`** | Lo que se envía a Docker al construir, y la lista de lo que **no** se envía. | `docker build … .` (el punto final es el contexto) |
| **Publicar un puerto** (`-p equipo:contenedor`) | Abre una puerta del equipo hacia un puerto del contenedor. Sin `-p`, desde el equipo no se llega. | `-p 8090:8090` |
| **Volumen** (`-v origen:destino[:ro]`) | Monta una carpeta del equipo dentro del contenedor. Con `:ro`, en solo lectura. Los datos quedan **fuera** de la imagen. | `-v "$PWD/data/processed:/datos:ro"` |
| **Red** | Un espacio donde varios contenedores se ven entre sí **por su nombre**: Docker hace de «guía telefónica» (DNS). | `docker network create retencion` |
| **Variable de entorno** (`-e`, `ENV`) | La configuración que el contenedor recibe desde fuera. | `-e CURSO_URL_API=http://api:8080` |
| **Usuario sin privilegios** | El proceso no corre como `root`: si alguien lo ataca, puede hacer menos. | `USER 10001` |
| **`HEALTHCHECK`** | La orden con la que Docker pregunta periódicamente «¿estás vivo?». | `docker ps` muestra `(healthy)` |

---

## 4. Escalón 2 · La API en su imagen (repaso del bloque 4)

Lo hiciste en el bloque 4. Recuerda qué lleva y qué no:
```text
docker build -f deploy/docker/Dockerfile -t retencion-api:local .
docker run --rm -p 8080:8080 retencion-api:local
```
- **Lleva:** Python 3.11, las versiones exactas de `requirements-api.lock`, el código `ia_mlops/` y **el modelo** (`models/modelo_mlflow/` y `metadatos.json`).
- **No lleva:** datos de clientes, cuadernos, pruebas ni el SQL (lo excluye el `.dockerignore` de la raíz).
- **Qué ha cambiado respecto al escalón 1:** la API ya no depende de tu entorno conda ni de tu sistema operativo. Cualquier equipo con Docker obtiene **exactamente lo mismo**, con las mismas versiones y la misma probabilidad (lo comprobaste con `comparar`).

Pero la API sigue pidiendo 13 variables. Falta la pieza para personas.

---

## 5. Escalón 3 · La interfaz en su propia imagen

### 5.1 ¿Por qué otra imagen y no meter la interfaz en la de la API?
Por tres razones:
1. **La imagen del modelo no debe llevar datos de clientes.** Si la API buscara las variables por id, `curso.db` tendría que viajar dentro de la imagen, y cualquiera con la imagen tendría los datos.
2. **Cada pieza cambia por un motivo distinto.** Se reentrena el modelo sin tocar la interfaz, y se cambia la página o los tramos sin reconstruir la imagen del modelo.
3. **Cada pieza escala por separado.** En producción puede haber diez copias de la API y una sola de la interfaz.

### 5.2 La receta, línea a línea (`deploy/docker/interfaz.Dockerfile`)
| Instrucción | Qué hace | Por qué así |
|---|---|---|
| `FROM python:3.11-slim` | Parte de la misma base que la API. | El mismo Python que el entorno del curso. |
| `ENV CURSO_DB=/datos/curso.db CURSO_DB_SOLO_LECTURA=1 CURSO_URL_API=http://api:8080` | Fija la configuración por defecto. | Se puede cambiar al arrancar con `-e`, sin reconstruir. |
| `COPY requirements-api.lock requirements-interfaz.txt ./` y `RUN pip install -c requirements-api.lock -r requirements-interfaz.txt` | Instala **solo** fastapi, uvicorn, pydantic, pandas y numpy, con las versiones del lock de la API. | `-c` es un archivo de **restricciones**: no instala nada por sí mismo, solo fija la versión de lo que se instala. Las dos imágenes usan las mismas versiones. Sin scikit-learn ni mlflow: la interfaz no ejecuta el modelo. |
| `COPY ia_mlops/ ia_mlops/` y `COPY sql/fs/02_poblar_fs.sql …` | El código y el SQL de las variables. | Nada de `models/` ni de `data/`. |
| `RUN useradd --uid 10001 … && mkdir /datos` y `USER 10001` | Crea un usuario sin privilegios y el punto de montaje. | Mismo criterio que la API. |
| `EXPOSE 8090` | Documenta el puerto. | No lo publica: eso lo hace `-p`. |
| `HEALTHCHECK … /salud` | Docker pregunta «¿vivo?» cada 30 s. | `/salud` y no `/listo`: si la API cae, reiniciar la interfaz no arregla nada. |
| `CMD ["uvicorn", "ia_mlops.interfaz.app:app", "--host", "0.0.0.0", "--port", "8090"]` | Arranca la interfaz. | `0.0.0.0`: las llamadas llegan desde fuera del contenedor. |

### 5.3 Cada imagen, su lista de exclusiones
El `.dockerignore` de la raíz es el de la API y excluye `sql/`, pero esta imagen necesita un archivo de `sql/`. Docker (BuildKit) permite **un archivo de exclusiones por Dockerfile**: junto a `interfaz.Dockerfile` está `interfaz.Dockerfile.dockerignore`, y cuando se construye con `-f deploy/docker/interfaz.Dockerfile`, Docker usa ese y no el de la raíz. La estrategia es la más segura: **excluir todo** (`*`) y dejar pasar solo lo que se copia (`!ia_mlops`, `!sql/fs/02_poblar_fs.sql`, `!requirements-…`). Así, un archivo nuevo con secretos en la carpeta del proyecto nunca entra por descuido.

### 5.4 Construir y mirar dentro
```text
docker build -f deploy/docker/interfaz.Dockerfile -t retencion-interfaz:local .
docker image ls 'retencion-*'                                                    # compara el tamaño de las dos imágenes
docker run --rm --entrypoint sh retencion-interfaz:local -c 'find /app -type f -not -path "*/ia_mlops/*"'
```
Salida real (GitHub Actions, 14/11/2026):
```text
retencion-interfaz:local  423MB
retencion-api:local  826MB

/app/requirements-api.lock
/app/requirements-interfaz.txt
/app/sql/fs/02_poblar_fs.sql
```
Fuera de `ia_mlops/` solo hay tres archivos: **ni modelo ni datos**. La imagen de la interfaz ocupa **la mitad** que la de la API porque no lleva scikit-learn, scipy ni mlflow. Compruébalo: `docker run --rm --entrypoint python retencion-interfaz:local -c "import sklearn"` termina con `ModuleNotFoundError: No module named 'sklearn'`.

---

## 6. Escalón 4 · Dos contenedores que se hablan

```text
   EQUIPO (el Codespace)                                     red «retencion» (solo la ven los contenedores)
   ┌────────────────────────────────────────────────────────────────────────────────────────────────────┐
   │  navegador ──► :8090 ──(-p 8090:8090)──► contenedor «interfaz»  ──http://api:8080──► contenedor «api» │
   │                                            │  usuario 10001                            │ usuario 10001
   │  data/processed/ ──(-v …:/datos:ro)────────┘  sin modelo                               │ con el modelo
   │                                                                                       (sin -p: no se publica)
   └────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 6.1 La red
```text
docker network create retencion
```
Los contenedores conectados a la misma red **se encuentran por su nombre**. El nombre de un contenedor (`--name api`) funciona como un nombre de equipo dentro de la red. Por eso la interfaz llama a `http://api:8080` y no a una dirección IP que cambia cada vez.

### 6.2 La API, sin publicar
```text
docker run -d --name api --network retencion retencion-api:local
```
- **No lleva `-p`, a propósito.** Desde el equipo no se llega a la API; solo la interfaz, dentro de la red, puede llamarla. Es el principio de **exponer lo mínimo**: la persona usa la interfaz y nadie necesita hablar con la API directamente.
- **`-d`** (*detached*) la deja corriendo en segundo plano.

Espera a que esté sana: `docker ps` muestra `(health: starting)` mientras carga el modelo y después `(healthy)`. En GitHub Actions tardó unos segundos.

### 6.3 La interfaz, con su puerto y sus datos
```text
docker run -d --name interfaz --network retencion -p 8090:8090 -v "$PWD/data/processed:/datos:ro" retencion-interfaz:local
```
- **`-p 8090:8090`.** El puerto 8090 del equipo lleva al 8090 del contenedor. Es la única puerta abierta.
- **`-v "$PWD/data/processed:/datos:ro"`.** La carpeta de datos de tu proyecto aparece dentro del contenedor en `/datos`, en **solo lectura**. La interfaz puede leer el historial, pero no modificarlo ni borrarlo, aunque tuviera un error. Al borrar el contenedor, los datos siguen en tu carpeta.
- **Sin `-e`.** La interfaz usa `CURSO_URL_API=http://api:8080` del Dockerfile. Funciona porque la API se llama `api` en esa red.

En PowerShell (Docker Desktop, sin probar): `-v "${PWD}\data\processed:/datos:ro"`.

### 6.4 Comprobar
```text
curl http://127.0.0.1:8090/listo
curl -X POST http://127.0.0.1:8090/recomendar -H "Content-Type: application/json" -d '{"cliente_ids": [13599, 18108, 13306, 99999]}'
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```
Salida real (GitHub Actions, 14/11/2026; `/recomendar` resumido):
```text
{"estado":"listo","datos":"ok","modelo":"http://api:8080"}

origen http://api:8080 | corte 2011-12-10
13599 0.9977 alta puesto 1
18108 0.4159 media puesto 75
13306 0.128 baja puesto 148
99999 no existe en MASTER

NAMES      STATUS                   PORTS
interfaz   Up 6 seconds (healthy)   0.0.0.0:8090->8090/tcp, [::]:8090->8090/tcp
api        Up 6 seconds (healthy)   8080/tcp
```
- **`/listo`** responde con `"modelo":"http://api:8080"`: la interfaz llegó a la API **por su nombre**.
- **`/recomendar`** da **los mismos números que en el escalón 1, en Windows**. El modelo y los datos son los mismos; solo ha cambiado dónde corren.
- **`docker ps`** enseña la diferencia de puertos. La interfaz tiene `0.0.0.0:8090->8090/tcp` (publicado). La API solo `8080/tcp`: escucha dentro de su red, pero no tiene puerta al equipo.

Abre la página: en el Codespace, desde la pestaña **Puertos**, el 8090.

### 6.5 El error clásico: `127.0.0.1` dentro de un contenedor
Prueba a arrancar otra interfaz diciéndole que la API está en `127.0.0.1`, como en el escalón 1:
```text
docker run -d --name interfaz-mal --network retencion -p 8091:8090 -e CURSO_URL_API=http://127.0.0.1:8080 -v "$PWD/data/processed:/datos:ro" retencion-interfaz:local
curl http://127.0.0.1:8091/listo
docker rm -f interfaz-mal
```
Salida real:
```text
{"detalle":"La API del modelo en http://127.0.0.1:8080 no responde ([Errno 111] Connection refused). ¿Está arrancada y /listo responde?"}
```
**Dentro de un contenedor, `127.0.0.1` es el propio contenedor**, no tu equipo ni el contenedor de al lado. Dentro de «interfaz-mal» no hay nada en el 8080. Es el error más frecuente al pasar de procesos a contenedores, y el 503 de `/listo` lo dice sin tener que adivinar.

---

## 7. Romper a propósito

Apunta lo que esperas **antes** de ejecutar cada prueba. Todas están automatizadas en el workflow `validar-dos-contenedores.yml`; la columna «Salida real» es la de su ejecución del 14/11/2026.

| Prueba | Orden | Salida real | Lección |
|---|---|---|---|
| Escribir en los datos | `docker exec interfaz sh -c 'echo x > /datos/intruso'` | `sh: 1: cannot create /datos/intruso: Read-only file system` | `:ro` protege el dato aunque el código tenga un error. |
| Llamar a la API desde el equipo | `curl http://127.0.0.1:8080/salud` | `curl: (7) Failed to connect to 127.0.0.1 port 8080 after 0 ms: Could not connect to server` | Sin `-p` no hay puerta. |
| Llamar a la API desde la interfaz | `docker exec interfaz python -c "import urllib.request; print(urllib.request.urlopen('http://api:8080/listo').read())"` | `b'{"estado":"listo"}'` | Dentro de la red, por nombre, sí. |
| Interfaz sin volumen | `docker run -d --name sin-datos --network retencion -p 8092:8090 retencion-interfaz:local` y `curl http://127.0.0.1:8092/listo` | 503 `{"detalle":"No existe la base /datos/curso.db. ¿Has montado el volumen con los datos? (-v .../data/processed:/datos:ro)"}` | Los datos no están en la imagen. |
| Parar la API | `docker stop api` y `curl http://127.0.0.1:8090/salud` y `/listo` | `/salud` 200; `/listo` 503 `{"detalle":"La API del modelo en http://api:8080 no responde ([Errno -3] Temporary failure in name resolution). …"}` | Vivo no es listo: reiniciar la interfaz no lo arregla. Y fíjate en el motivo: con la API parada, **el nombre `api` deja de existir en la red** (la «guía telefónica» de Docker ya no lo encuentra). |
| ¿Quién soy? | `docker exec interfaz id -u` | `10001` | Ni root ni privilegios. |

Para limpiar: `docker rm -f api interfaz sin-datos` y `docker network rm retencion`.

---

## 8. Escalón 5 · Lo mismo en un archivo: Docker Compose

Cuatro órdenes largas con banderas que hay que recordar no se pueden repetir igual cada vez. **Compose** las escribe una sola vez en un archivo, `deploy/docker/compose.yaml`, que también sirve de documentación.

```text
docker compose -f deploy/docker/compose.yaml up --build -d     # construye las dos imágenes, crea la red y arranca en orden
docker compose -f deploy/docker/compose.yaml ps                # estado y salud
docker compose -f deploy/docker/compose.yaml logs -f interfaz  # registros (Ctrl+C para salir)
docker compose -f deploy/docker/compose.yaml down              # para y borra contenedores y red; imágenes y datos se quedan
```
`ps`, salida real (con `--format 'table {{.Service}}\t{{.Status}}\t{{.Ports}}'`):
```text
SERVICE    STATUS                    PORTS
api        Up 11 seconds (healthy)   8080/tcp
interfaz   Up 5 seconds (healthy)    0.0.0.0:8090->8090/tcp, [::]:8090->8090/tcp
```
La interfaz arrancó **6 segundos después** que la API. Es `depends_on: condition: service_healthy`: Compose esperó a que la API estuviera sana.

| A mano (escalón 4) | En `compose.yaml` |
|---|---|
| `docker network create retencion` | Automático: una red por proyecto (`name: retencion`). |
| `--name api` | El nombre del servicio (`services: api:`). |
| `docker build -f deploy/docker/Dockerfile …` | `build: {context: ../.., dockerfile: deploy/docker/Dockerfile}` |
| `-p 8090:8090` | `ports: ["8090:8090"]` |
| `-v "$PWD/data/processed:/datos:ro"` | `volumes: ["../../data/processed:/datos:ro"]` (las rutas se resuelven desde `deploy/docker/`) |
| `-e CURSO_URL_API=…` | `environment: {CURSO_URL_API: http://api:8080}` |
| «Espera a que la API esté sana» (lo hacías tú mirando `docker ps`) | `depends_on: {api: {condition: service_healthy}}` |

Compose sirve para **un equipo**: tu Codespace, un servidor de pruebas. En producción, el mismo papel lo cumplen plataformas que reparten los contenedores entre muchas máquinas y los vigilan (S3 y S4).

---

## 9. Escalón 6 · Qué le falta para ser producción real

Ahora tienes **el mismo artefacto que iría a producción**: dos imágenes reproducibles, configuradas desde fuera, sin root, con salud y con los datos separados. Pero el Codespace **no es producción**: es una máquina privada en la nube que se para cuando no la usas. Esto es lo que añade una empresa, y dónde lo vemos en el curso:

| Aspecto | En el Codespace (S2) | En producción | En el curso |
|---|---|---|---|
| **Dónde corre** | Una máquina tuya que se apaga por inactividad. | Una plataforma gestionada que mantiene el servicio encendido y lo reinicia si cae. | S3 (Cloud Run) |
| **Quién llega** | Solo tú, por el puerto reenviado (privado por defecto). | Usuarios autenticados; la API, solo desde la interfaz o desde servicios autorizados. | S3 (IAM y cuentas de servicio) |
| **De dónde salen las imágenes** | Se construyen en tu Codespace. | Se construyen en el CI y se guardan, versionadas, en un registro de imágenes. Se despliega una versión concreta. | S3 y S4 (Artifact Registry, publicar desde el workflow) |
| **Los datos** | Un archivo SQLite montado como volumen. | Una base o un almacén gestionado, o un servicio de variables (*feature store* en línea), con permisos y copias. | S3 (de SQLite a BigQuery) |
| **Secretos** | No hay. | Contraseñas y claves en un gestor de secretos, nunca en la imagen ni en el repositorio. | S3 (Secret Manager) y S4 (secretos del workflow) |
| **Carga** | Un contenedor de cada. | Varias copias según la demanda. | S3 (Cloud Run) |
| **Despliegue** | `docker compose up` a mano. | Automático desde el repositorio, con pruebas y aprobación. | S4 (CI/CD con aprobación manual) |
| **Registros y alertas** | `docker logs`. | Registros centralizados, métricas del servicio y alertas. | S3 (registros) y S5 (monitoreo y alertas) |
| **Calidad del modelo** | El aviso «revisar» de la interfaz. | Seguimiento de la deriva, reentrenamiento y vuelta a la versión anterior si algo sale mal. | S5 (deriva y *rollback*) |

La idea clave: **pasar a producción no cambia el código ni las imágenes**. Cambia **dónde** corren y **lo que las rodea**. Por eso hemos separado las piezas, sacado los datos de la imagen y puesto la configuración en variables de entorno.

---

## 10. Resumen: los escalones en una tabla

| | Qué corre | Depende de | Quién llega | Datos | Si se apaga |
|---|---|---|---|---|---|
| **1 · Mi ordenador** | Dos procesos Python | Tu entorno conda, tus archivos, tu sistema operativo | Solo tú (`127.0.0.1`) | Tu carpeta, con permiso de escritura | Desaparece |
| **2 · API en imagen** | Un contenedor | Solo de la imagen (y de Docker) | Tú, por `-p 8080` | No usa datos | Se recrea con `docker run` |
| **3–4 · Dos contenedores** | Dos contenedores en una red | Solo de las imágenes | Tú, solo a la interfaz (`-p 8090`) | Volumen `:ro` | Se recrean igual |
| **5 · Compose** | Lo mismo, descrito en un archivo | El archivo y las imágenes | Igual | Igual | `docker compose up` |
| **6 · Producción** | Las mismas imágenes en una plataforma | La plataforma | Usuarios autenticados | Base gestionada | La plataforma lo reinicia |

---

## 11. Autoevaluación

<details><summary>1. ¿Por qué la interfaz llama a <code>http://api:8080</code> y no a <code>http://127.0.0.1:8080</code>?</summary>
Dentro de un contenedor, <code>127.0.0.1</code> es el propio contenedor. En la red <code>retencion</code>, Docker resuelve el nombre <code>api</code> al contenedor de la API.
</details>

<details><summary>2. ¿Por qué la API no lleva <code>-p</code>?</summary>
Porque nadie de fuera necesita hablar con ella: solo la interfaz, dentro de la red. Exponer lo mínimo reduce lo que puede atacarse o usarse mal.
</details>

<details><summary>3. ¿Por qué los datos van en un volumen y no dentro de la imagen?</summary>
Porque la imagen se copia y se comparte: no debe llevar datos de clientes. Además, los datos cambian (cada día hay facturas nuevas) y la imagen no tiene por qué reconstruirse por eso. Con <code>:ro</code>, el contenedor no puede estropearlos.
</details>

<details><summary>4. La API se cae. ¿Qué responden <code>/salud</code> y <code>/listo</code> de la interfaz, y por qué importa?</summary>
<code>/salud</code> 200 y <code>/listo</code> 503. Si el <code>HEALTHCHECK</code> mirara <code>/listo</code>, Docker daría la interfaz por enferma y la reiniciaría sin arreglar nada.
</details>

<details><summary>5. ¿Qué cambia en el código al pasar del escalón 1 al 4? ¿Y al 6?</summary>
Nada en ninguno de los dos casos. Solo cambian la configuración (variables de entorno) y dónde corren las piezas.
</details>

<details><summary>6. ¿Por qué la imagen de la interfaz no lleva scikit-learn?</summary>
Porque no ejecuta el modelo: le pide la probabilidad a la API por HTTP. Lleva menos paquetes, ocupa menos y tiene menos por donde fallar.
</details>

---

## 12. Qué se probó y qué no
- **Pruebas sin Docker** (`tests/test_imagen_interfaz.py` y `tests/test_interfaz.py`):
  - el Dockerfile: base, versiones fijadas con el lock, que no copia ni modelo ni datos, usuario, salud, puerto y comando;
  - qué entra en el contexto;
  - que la interfaz no importa scikit-learn ni MLflow;
  - Compose: servicios, puertos, volumen `:ro` y `depends_on`;
  - que con la base en solo lectura funciona y no la modifica;
  - y `/salud` y `/listo`.
- **Simulado en Windows sin Docker** (14/11/2026): `/app` y `/datos` copiados aparte, la base marcada de solo lectura y las variables de entorno del Dockerfile, contra la API real. El resultado: las mismas probabilidades, el 503 al parar la API y la base intacta.
- **Con Docker real:** el workflow `.github/workflows/validar-dos-contenedores.yml` ejecuta los escalones 3, 4 y 5 y todas las roturas del apartado 7. **En verde en GitHub Actions** (ubuntu-latest, 14/11/2026, dos ejecuciones). Las salidas reales de esta guía son las de esa ejecución: el workflow las publica como anotaciones en la página de la ejecución.
- **Sin probar:** en un Codespace a mano, y en Docker Desktop (Windows o Mac).
