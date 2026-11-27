# Capturas pendientes del extra Composer

Las diapositivas ya muestran estas pantallas como recuadro «captura pendiente». Cuando se hagan, guárdalas en `img/` como `.webp` con el nombre de la tabla y quita el recuadro en `generar.py` (diccionario `PENDIENTES`).

| Archivo | Paso del laboratorio | Cómo hacerla |
|---|---|---|
| `airflow-01-dag-en-la-lista.webp` | Local, paso 2 | 1. `docker compose -f docker-compose-airflow.yaml up -d`. 2. Abre http://localhost:8080 (airflow / airflow). 3. Captura la lista de DAGs con `retencion_lote`. |
| `airflow-02-grid-run-ok.webp` | Local, paso 2 | 1. `airflow dags trigger retencion_lote --conf '{…}'`. 2. Abre el DAG, vista Grid. 3. Captura con las cinco tareas en verde. |
| `airflow-03-registro-resumir.webp` | Local o Composer | 1. En el run, pulsa la tarea `resumir`, pestaña Logs. 2. Captura el resumen «Lote de retención». |
| `composer-01-entornos.webp` | Composer, paso 4 | 1. (Cuesta dinero) crea el entorno. 2. Consola → Composer → Entornos. 3. Captura la lista con el entorno `RUNNING`. Bórralo después. |
| `composer-02-bucket-dags.webp` | Composer, paso 4 | 1. Tras `dags import`, abre «Abrir carpeta DAGs». 2. Captura `retencion_lote.py` y `lote_logica.py`. |
| `composer-03-run.webp` | Composer, paso 4 | 1. `gcloud composer environments run … dags trigger`. 2. Interfaz de Airflow del entorno, Grid. 3. Captura. |
| `gcp-iam-roles.webp` | Composer, permisos | 1. Consola → IAM, cuenta de servicio del entorno y la de Actions. 2. Captura de roles (difumina el proyecto). |
| `actions-01-run-workflow.webp` | Actions | 1. Copia `lote-composer.yml` a `.github/workflows/` de la rama por defecto (en el repositorio del curso el botón «Run workflow» NO aparece en los workflows de S4 porque viven en ramas `lab/`). 2. Actions → «Lote en Cloud Composer» → Run workflow. 3. Captura el formulario con corte, imagen y capacidad (sin pulsar Run). |
| `actions-02-aprobacion.webp` | Actions | 1. Tras lanzarlo, el run espera en `produccion`. 2. Captura «Review deployments». |
| `actions-03-job-summary.webp` | Actions | 1. Run terminado. 2. Captura la página del run con el Job Summary (tabla de tareas y registro de `resumir`). |
| `actions-04-ensayo-airflow.webp` | Actions | 1. Sigue la receta «Ensayo en Actions» del README. 2. Captura el resumen del job. |
| `lote-ui-airflow-real.webp` | UI | 1. Con Airflow local en marcha, `AIRFLOW_URL=http://localhost:8080 AIRFLOW_AUTH=basic AIRFLOW_USUARIO=airflow AIRFLOW_CLAVE=airflow python app.py` en `extra-mcp-notebooks/ui`. 2. Pestaña Lote, lanza y captura el run. (Las capturas actuales son contra el servidor de PRUEBA.) |

Ya hechas (27/11/2026, solo lectura, de OTROS workflows ya existentes): gh-01-actions-lista, gh-02-nueva-version-runs, gh-03-puntuar-lote-resumen, gh-04-environments, gh-05-variables (valores de variables y avatar difuminados; originales fuera del repo en C:\bk\lab-prod\revision-composer\raw\).
