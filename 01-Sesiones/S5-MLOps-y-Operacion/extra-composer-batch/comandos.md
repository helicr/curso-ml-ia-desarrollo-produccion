# Comandos manuales · lote orquestado con Airflow / Cloud Composer

Cada bloque lleva su estado: **[ejecutado]** = se ejecutó al preparar este extra y la salida es la real (carpeta `salidas/`);
**[sin verificar]** = escrito con la documentación oficial pero NO ejecutado (no había Docker, ni Airflow real, ni un entorno de Composer).
Los bloques de código están tal cual en los archivos del extra y `pruebas/` lo comprueba.

Todas las rutas son desde la raíz de tu copia del repositorio. Variables que usamos:

```bash
export EXTRA=01-Sesiones/S5-MLOps-y-Operacion/extra-composer-batch
export PROYECTO_GCP=<tu-proyecto>        # solo para Composer
export REGION=europe-west1               # solo para Composer
export ENTORNO=<tu-entorno-de-composer>  # solo para Composer
```

## 0 · El lote a mano, sin Airflow y sin Docker  [ejecutado]

Es lo que el DAG ejecutará dentro del contenedor. Si esto no funciona, el DAG tampoco.

```bash
cd 04-Proyecto-Base
python -m ia_mlops.operacional
python -m ia_mlops.pipeline
python -m ia_mlops.explotacion --corte 2011-12-10 --capacidad 0.1 --sin-guardar-fs
```

**Qué debes ver:** `Clientes puntuados: 148`, `Campaña: 15 clientes`, la tabla de los 10 primeros y `Guardado en: …campana_2011-12-10.csv y …json`. Código de salida 0.
**Si falla:** `MASTER está vacío` o `No existe la capa FS` → falta `python -m ia_mlops.pipeline`. `No se encuentra el modelo` → lo mismo.
(Con `CURSO_DB` y `CURSO_REPORTES` apuntando a una carpeta temporal no se toca el proyecto: así se probó.)

## 1 · Construir la imagen del lote  [sin verificar: no hay Docker aquí]

La imagen de la API lleva el modelo pero **no** el SQL ni los datos (su `.dockerignore` los excluye): sola no puede correr el lote. `lote.Dockerfile` parte de la imagen de la API y añade `sql/fs/02_poblar_fs.sql` y `curso.db`. Vale con el Dockerfile de develop (COPY del modelo) y con el multi-etapa (`--build-context modelo=models`) porque parte de la imagen ya construida.

```bash
cd 04-Proyecto-Base
docker build -f deploy/docker/Dockerfile -t retencion-api:local .
docker build -f ../$EXTRA/lote.Dockerfile --build-arg IMAGEN_API=retencion-api:local -t retencion-lote:local .
docker run --rm retencion-lote:local python -m ia_mlops.explotacion --corte 2011-12-10 --capacidad 0.1 --sin-guardar-fs
```

(Con el Dockerfile multi-etapa: `docker build -f deploy/docker/Dockerfile --build-arg FUENTE=contexto --build-context modelo=models -t retencion-api:local .`)

**Qué debes ver:** la misma salida que en el paso 0. **Si falla:** `Cannot connect to the Docker daemon` → Docker no está en marcha. `COPY failed: … curso.db` → falta `python -m ia_mlops.pipeline`. Error al escribir en `/app/reports` → el DAG fija `CURSO_REPORTES=/tmp/reports`; al probar a mano añade `-e CURSO_REPORTES=/tmp/reports`.

## 2 · En local con Airflow en Docker  [sin verificar]

```bash
cd $EXTRA
docker compose -f docker-compose-airflow.yaml up -d
```

**Qué debes ver:** tras 1-2 minutos, <http://localhost:8080> pide usuario `airflow` y contraseña `airflow`. **Si falla:** `docker compose logs airflow`; un `permission denied` sobre el socket de Docker se arregla con `DOCKER_GID` (ver el compose).

```bash
docker compose -f docker-compose-airflow.yaml exec airflow airflow dags list
docker compose -f docker-compose-airflow.yaml exec airflow airflow dags list-import-errors
```

**Qué debes ver:** `retencion_lote` en la lista y ningún error de importación. **Si falla:** el error de importación dice el módulo que falta (normalmente `apache-airflow-providers-docker`, que el compose instala al arrancar).

Probar el DAG entero sin planificador (ejecuta las tareas en el mismo proceso):

```bash
docker compose -f docker-compose-airflow.yaml exec airflow airflow dags test retencion_lote 2011-12-10 --conf '{"corte": "2011-12-10", "imagen": "retencion-lote:local", "capacidad": 0.1}'
```

Lanzarlo de verdad (queda en el historial) y mirar su estado:

```bash
docker compose -f docker-compose-airflow.yaml exec airflow airflow dags trigger retencion_lote --conf '{"corte": "2011-12-10", "imagen": "retencion-lote:local", "capacidad": 0.1}'
docker compose -f docker-compose-airflow.yaml exec airflow airflow dags list-runs -d retencion_lote
docker compose -f docker-compose-airflow.yaml exec airflow airflow tasks states-for-dag-run retencion_lote <run_id>
```

**Qué debes ver:** cinco tareas (`entradas`, `comprobar`, `ejecutar_lote`, `validar`, `resumir`) en `success` y, en el registro de `resumir`, el resumen «Lote de retención · corte 2011-12-10». **Si falla:** la tarea en rojo dice por qué; `ImagePullBackOff`/`pull access denied` → la imagen `retencion-lote:local` no existe en el Docker del equipo (paso 1). (En Airflow 3 `list-runs` recibe el DAG como argumento: `airflow dags list-runs retencion_lote`.)

Parar y borrar: `docker compose -f docker-compose-airflow.yaml down -v`.

## 3 · Lanzarlo por la API REST con `lanzar_lote.py`  [ejecutado contra el servidor de PRUEBA; sin verificar contra Airflow real]

```bash
export AIRFLOW_USUARIO=airflow AIRFLOW_CLAVE=airflow
python $EXTRA/lanzar_lote.py --url http://localhost:8080 --auth basic --corte 2011-12-10 --imagen retencion-lote:local
python $EXTRA/lanzar_lote.py --url http://localhost:8080 --simular-url --corte 2011-12-10
```

**Qué debes ver:** una línea por cambio de estado de cada tarea y `Run …: success`. Código de salida 0 (1 = el DAG falló, 2 = se agotó la espera, 3 = no hay conexión o credenciales, 4 = DAG en pausa). `--simular-url` no llama a nadie: enseña qué enviaría. **Si falla:** el mensaje dice si es `401` (credenciales), `404` (nombre del DAG o versión de la API) o conexión rechazada (Airflow no está en marcha).

## 4 · En Cloud Composer  [sin verificar: no se creó ningún entorno; crear uno cuesta dinero]

Composer 3 ofrece Airflow 2 y Airflow 3 (<https://docs.cloud.google.com/composer/docs/composer-versioning-overview>). Crear un entorno tarda aproximadamente 25 minutos según la documentación (<https://docs.cloud.google.com/composer/docs/composer-3/create-environments>); el coste está en la página de precios y aquí no se cita ninguna cifra. **Bórralo al terminar el laboratorio.**

```bash
gcloud services enable composer.googleapis.com artifactregistry.googleapis.com --project $PROYECTO_GCP
gcloud composer environments create $ENTORNO --location $REGION --image-version composer-3-airflow-2 --project $PROYECTO_GCP
```

**Qué debes ver:** al cabo de ~25 min `gcloud composer environments list --locations $REGION` muestra el entorno en `RUNNING`. **Si falla:** `PERMISSION_DENIED` → faltan roles; `API not enabled` → el primer comando. (El alias `composer-3-airflow-2` aparece en la documentación de versiones.)

Subir el DAG a la carpeta `/dags` del bucket del entorno (<https://docs.cloud.google.com/composer/docs/composer-3/manage-dags>; Airflow tarda 1-2 minutos en verlo):

```bash
gcloud composer environments storage dags import --environment $ENTORNO --location $REGION --source=$EXTRA/dags/lote_logica.py
gcloud composer environments storage dags import --environment $ENTORNO --location $REGION --source=$EXTRA/dags/retencion_lote.py
gcloud composer environments run $ENTORNO --location $REGION dags list -- --output=json
```

**Qué debes ver:** `retencion_lote` en la lista. **Si falla:** si no aparece tras 5 minutos, abre la interfaz de Airflow: la pestaña de errores de importación dice qué falta.

La imagen del lote va a Artifact Registry (el repositorio `curso` de S4) y la cuenta de servicio del entorno debe poder leerla:

```bash
gcloud auth configure-docker $REGION-docker.pkg.dev
docker tag retencion-lote:local $REGION-docker.pkg.dev/$PROYECTO_GCP/curso/retencion-lote:v1
docker push $REGION-docker.pkg.dev/$PROYECTO_GCP/curso/retencion-lote:v1
```

Lanzar el DAG (patrón de la documentación: <https://docs.cloud.google.com/composer/docs/composer-3/access-airflow-cli>; los argumentos del DAG van tras `--`):

```bash
gcloud composer environments run $ENTORNO --location $REGION dags trigger -- retencion_lote --conf '{"corte": "2011-12-10", "imagen": "'$REGION'-docker.pkg.dev/'$PROYECTO_GCP'/curso/retencion-lote:v1", "capacidad": 0.1}'
gcloud composer environments run $ENTORNO --location $REGION dags list-runs -- retencion_lote
gcloud composer environments run $ENTORNO --location $REGION tasks states-for-dag-run -- retencion_lote <run_id>
```

**Qué debes ver:** el `trigger` devuelve el run creado; `list-runs` muestra `running` y luego `success`; `states-for-dag-run` lista las cinco tareas. **Si falla:** `ImagePullBackOff` en `ejecutar_lote` → la cuenta de servicio del entorno no puede leer Artifact Registry o la etiqueta no existe. Los pods corren siempre en el espacio de nombres `composer-user-workloads` (<https://docs.cloud.google.com/composer/docs/composer-3/use-kubernetes-pod-operator>). Si tu Airflow es 2.x, `list-runs` usa `-d retencion_lote`.

La API REST con la sesión de gcloud (Airflow 2 usa `/api/v1`, Airflow 3 usa `/api/v2`; <https://docs.cloud.google.com/composer/docs/composer-3/access-airflow-api>):

```bash
export AIRFLOW_URL=$(gcloud composer environments describe $ENTORNO --location $REGION --format="value(config.airflowUri)")
python $EXTRA/lanzar_lote.py --url $AIRFLOW_URL --auth google --corte 2011-12-10 --imagen $REGION-docker.pkg.dev/$PROYECTO_GCP/curso/retencion-lote:v1
```

**Qué debes ver:** lo mismo que en el paso 3. **Si falla:** `403` → falta rol de Airflow/IAM para la cuenta; la documentación dice que el usuario nuevo recibe el rol `Op` por defecto.

Borrar el entorno (para de cobrar):

```bash
gcloud composer environments delete $ENTORNO --location $REGION
```

## 5 · Con GitHub Actions  [sin ensayar]

Copia `lote-composer.yml` y `dags-composer.yml` (y, para ensayar sin Composer, `ensayo-airflow.yml`) a `.github/workflows/`. Variables y receta en `README.md`.
