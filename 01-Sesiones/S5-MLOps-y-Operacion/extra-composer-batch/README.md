# Extra de S5 · Ejecución batch del modelo orquestada con Airflow de Google Cloud (Cloud Composer)

Cada día (o cuando alguien lo pide) hay que puntuar a **todos** los clientes con el modelo en producción. En S4 ya lo hace `puntuar-lote.yml` en GitHub Actions. Aquí lo orquestamos con **Airflow**, en su versión gestionada de Google Cloud (**Cloud Composer**): un DAG de cuatro pasos (comprobar, ejecutar, validar, resumir) sobre la imagen que ya lleva el modelo.

Decisión del profesor: Cloud Composer. Va como EXTRA en S5. Las diapositivas están en `index.html` (enlace «Índice» a `../index.html`).

## Qué hay

| Archivo | Para qué |
|---|---|
| `dags/retencion_lote.py` | El DAG `retencion_lote` (sin schedule, con `params`). Dos variantes de operador: `KubernetesPodOperator` (Composer) y `DockerOperator` (local), elegidas con `LOTE_MODO`. |
| `dags/lote_logica.py` | Validación y resumen de la salida, sin Airflow (se prueba en cualquier ordenador). |
| `lote.Dockerfile` (+ `.dockerignore`) | La imagen de la API más el SQL y la base de muestra: la API sola no puede correr el lote. |
| `docker-compose-airflow.yaml` | Airflow mínimo en local. **Sin verificar.** |
| `lanzar_lote.py` | Cliente de la API REST de Airflow (v1 y v2; token de Google, usuario/clave o sin auth). `--simular-url` no llama a nadie. |
| `comandos.md` | Los comandos manuales paso a paso, con «qué debes ver» y «si falla». |
| `lote-composer.yml`, `dags-composer.yml`, `ensayo-airflow.yml` | Los tres workflows (para copiar a `.github/workflows/`; **no están instalados**). |
| `index.html` (`generar.py`) | Las diapositivas del laboratorio. |
| `salidas/`, `img/` | Salidas reales de terminal y capturas (ver `capturas-pendientes.md` para las que faltan). |
| `pruebas/` | Pruebas, incluido un servidor Airflow FALSO (`airflow_falso.py`). |
| `../extra-mcp-notebooks/ui/` | La interfaz web, ahora con la pestaña **Lote**. |

## Qué está probado y qué NO

Probado (ejecutado el 27/11/2026, ordenador Windows sin Docker):
- El lote real `python -m ia_mlops.explotacion` sobre una copia de `curso.db` (148 clientes, 15 en campaña) y la lógica de validación sobre su salida real. El repositorio no cambió (hashes de `curso.db`, `metadatos.json` y `mlflow.db` iguales antes y después).
- El DAG: sintaxis y estructura con un Airflow *de cartón* (módulos falsos, para Airflow 2 y 3), elección de variante, que falte un proveedor no rompe la importación.
- `lanzar_lote.py` y la pestaña Lote contra un **servidor Airflow falso** (`airflow_falso.py`): lanzar, seguir, fallar, pausa, autenticación, historial, registro.
- Los YAML de los workflows: estructura, permisos, WIF, entradas y coherencia con `comandos.md`.

**Sin verificar** (no hay Airflow real, ni Docker, ni Composer, ni Actions ejecutado):
- El DAG dentro de un Airflow de verdad (`airflow dags test`, `DockerOperator`, `KubernetesPodOperator`, XCom del pod).
- La construcción de `lote.Dockerfile` y `docker-compose-airflow.yaml`.
- Todo lo que toca un entorno de Composer, Artifact Registry y los permisos de IAM.
- Los tres workflows en GitHub Actions.
- Que un Airflow real acepte exactamente las llamadas que acepta el servidor falso (los formatos de `/api/v1` y `/api/v2` están escritos de la referencia de Airflow; sólo `POST …/dags/{dag_id}/dagRuns` con `conf` y, en v2, `logical_date` se contrastó con la documentación de Composer).

## Relación con lo que ya existe

- **`puntuar-lote.yml` (S4)**: el mismo lote, pero GitHub Actions entrena y puntúa en el mismo run y con una API en un contenedor (`--url`). Aquí el DAG puntúa con el modelo local de la imagen (sin `--url`) y los datos van en la imagen.
- **La imagen**: sirve igual con el `Dockerfile` de develop (COPY del modelo) y con el multi-etapa de la rama `dockerfile-clon` (`--build-context modelo=…`): `lote.Dockerfile` parte de la imagen ya construida.
- **Interfaz web** (`extra-mcp-notebooks/ui`): pestaña «Lote». Variables `AIRFLOW_URL`, `AIRFLOW_AUTH`, `AIRFLOW_USUARIO`, `AIRFLOW_CLAVE` o `AIRFLOW_TOKEN`. No guarda ni muestra secretos y no simula ejecuciones.

## Datos de producto citados (documentación oficial)

- Composer 3 ofrece Airflow 2 y Airflow 3; cada build recibe soporte entre 0 y 12 meses: <https://docs.cloud.google.com/composer/docs/composer-versioning-overview>
- Crear un entorno: «aproximadamente 25 minutos»: <https://docs.cloud.google.com/composer/docs/composer-3/create-environments>. Precio: la página lo trata aparte; **sin dato** aquí (no se cita ninguna cifra).
- Subir DAGs a `/dags` del bucket con `gcloud composer environments storage dags import`; retraso de 1-2 minutos: <https://docs.cloud.google.com/composer/docs/composer-3/manage-dags>
- `gcloud composer environments run ENTORNO --location REGION SUBCOMANDO -- ARGUMENTOS`: <https://docs.cloud.google.com/composer/docs/composer-3/access-airflow-cli>
- API REST: Airflow 3 usa v2 y Airflow 2 usa v1; URL con `config.airflowUri`; autenticación con credenciales de Google (alcance `cloud-platform`): <https://docs.cloud.google.com/composer/docs/composer-3/access-airflow-api>
- `KubernetesPodOperator` en Composer 3: espacio de nombres `composer-user-workloads`, `config_file="/home/airflow/composer_kube_config"`, XCom por `/airflow/xcom/return.json`: <https://docs.cloud.google.com/composer/docs/composer-3/use-kubernetes-pod-operator>
- `DockerOperator` (paquete `apache-airflow-providers-docker`): <https://airflow.apache.org/docs/apache-airflow-providers-docker/stable/_api/airflow/providers/docker/operators/docker/index.html>
- `CloudRunExecuteJobOperator` (alternativa si el lote fuera un Cloud Run Job; no se usa aquí): <https://airflow.apache.org/docs/apache-airflow-providers-google/stable/operators/cloud/cloud_run.html>
- `Param` y `--conf`: <https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/params.html>; CLI `dags trigger/test/list-runs`, `tasks states-for-dag-run`: <https://airflow.apache.org/docs/apache-airflow/stable/cli-and-env-variables-ref.html>
- Airflow en Docker (compose oficial, usuario `airflow`/`airflow`, no apto para producción): <https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html>. En Airflow 3 la API REST local pide un JWT de `POST /auth/token`; por eso `lanzar_lote.py --auth basic` lo canjea cuando detecta la v2.

**Dudas abiertas con el enunciado:** la documentación de Composer autentica la API con un token de acceso de Google, no con un token de identidad (ID token): `lanzar_lote.py` usa el de acceso (`gcloud auth print-access-token`). Cuánto cuesta un entorno: sin dato.

## Costes y limpieza

Un entorno de Composer **cuesta dinero mientras exista** y tarda ~25 minutos en crearse. Este extra NO crea ninguno. Si lo haces tú: bórralo al terminar (`gcloud composer environments delete`), y revisa el presupuesto de la cuenta del curso. Cloud Run Job o el propio puntuar-lote de S4 son alternativas mucho más baratas para un lote diario: Composer se justifica cuando hay MUCHOS flujos que coordinar.

## Pruebas

```bash
cd 01-Sesiones/S5-MLOps-y-Operacion/extra-composer-batch
python -m pytest pruebas -q -p no:cacheprovider
cd ../extra-mcp-notebooks && python -m pytest ui/pruebas -q -p no:cacheprovider
```

## Ensayo en Actions (cuando el profesor autorice el push)

1. Copia `ensayo-airflow.yml` a `.github/workflows/` en tu fork.
2. `git switch -c lab/composer/ensayo`, cambia una línea de un comentario de `dags/retencion_lote.py`, `git push -u origin lab/composer/ensayo`.
3. En Actions, abre «Ensayo del DAG sin Composer». Debes ver: `airflow dags list-import-errors` sin errores, `retencion_lote` en la lista, las tareas en `success` y el resumen del lote en el Job Summary.
4. Si falla, el fallo suele estar en `docker build` (falta `curso.db`: ¿se ejecutó `pipeline`?) o en la versión de Airflow / constraints. Anota el error en `capturas-pendientes.md`.

Para `lote-composer.yml` y `dags-composer.yml` hacen falta además un entorno de Composer y las variables `GCP_PROYECTO`, `GCP_PROVEEDOR_WIF`, `COMPOSER_CUENTA`, `COMPOSER_ENV`, `COMPOSER_REGION` y (opcional) `LOTE_IMAGEN`, más el environment `produccion` con revisores.
