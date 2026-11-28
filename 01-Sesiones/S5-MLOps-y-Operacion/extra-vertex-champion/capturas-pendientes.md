# Capturas pendientes del extra «Del alias champion de MLflow a un endpoint de Vertex AI»

Todo lo de esta lista **no se ha podido capturar** porque requiere ejecutar el extra de verdad (GitHub Actions o Vertex AI) y aún no se ha hecho. Las diapositivas dibujan hoy un recuadro **«Captura pendiente»** con el nombre del archivo; cuando exista el `.webp` en `img/` basta ejecutar `python generar.py` y el recuadro se convierte en la imagen (con lupa para ampliar). **Nunca se ha puesto una imagen inventada.**

**Intento de ensayo del 28/11/2026 (sin terminar, sin recursos de pago creados):** en Cloud Shell salió bien clonar `develop`, crear el entorno, instalar `requirements-dev.txt` y entrenar la v1 (AUC de validación 0.6982 y de test 0.7471), y `docker version` responde. **Falló** el `docker build` de `scripts/subir_modelo.sh`: el `docker pull python:3.11-slim` (desde Docker Hub y desde `mirror.gcr.io`) se quedó parado y el build estuvo más de 24 minutos sin usar CPU. No se creó ningún modelo ni endpoint. Lo único que dejó es el repositorio de Artifact Registry `curso` (vacío, en `southamerica-west1`), que crea la propia `subir_modelo.sh`. **Propuesta, sin probar:** construir la imagen con Cloud Build (`gcloud builds submit`) en lugar del Docker de Cloud Shell. Las 13 capturas siguen pendientes.

**Antes de capturar:** hacer el **ensayo real** (`guia.md`, apartado 9) en la rama `lab/vertex-champion/ensayo`, con borrado inmediato. Encuadrar sin la barra de crédito de la prueba gratuita; **difuminar el correo y el nombre del proyecto**; guardar los originales **fuera** del repositorio; convertir a `.webp` (calidad 85) y poner el nombre exacto de la lista.

| # | Archivo (en `img/`) | Paso del laboratorio | Dónde |
|---|---|---|---|
| 1 | `pend-01-form-run-workflow.webp` | L5 · desplegar | GitHub, Actions |
| 2 | `pend-02-run-esperando-aprobacion.webp` | L5 · aprobación | GitHub, run |
| 3 | `pend-03-resumen-modelo.webp` | L5 · trabajo 1 | GitHub, run |
| 4 | `pend-04-resumen-desplegado.webp` | L5 · Job Summary | GitHub, run |
| 5 | `pend-05-ar-imagen.webp` | L3 · subir | Consola, Artifact Registry |
| 6 | `pend-06-registro-versiones.webp` | L3 · subir | Consola, Vertex AI |
| 7 | `pend-07-endpoint-canario.webp` | L3 · canario | Consola, Vertex AI |
| 8 | `pend-08-cloudshell-subir.webp` | L3 · subir | Cloud Shell |
| 9 | `pend-09-cloudshell-probar.webp` | L3 · probar | Cloud Shell |
| 10 | `pend-10-rollback-run.webp` | L4 · rollback | GitHub, run |
| 11 | `pend-11-borrar-confirmacion.webp` | L6 · borrar | GitHub, Actions |
| 12 | `pend-12-vacio-final.webp` | L6 · borrar | Consola y Cloud Shell |
| 13 | `pend-13-variables-gcp-repo-ar.webp` | L3 · variables | GitHub, Settings |

## Cómo hacer cada captura

### 1 · `pend-01-form-run-workflow.webp` (L5, «Los tres workflows»)
1. En tu fork, abre la pestaña **Actions**.
2. En la barra lateral, pulsa **Vertex AI · desplegar el champion de MLflow** (el archivo debe estar ya en la rama por defecto del fork; si no, el botón no aparece).
3. Pulsa **Run workflow** (el desplegable gris de arriba a la derecha) **sin pulsar el botón verde de dentro**.
4. Encuadra el desplegable con las **nueve entradas** (`version_mlflow`, `dos_versiones`, `region`, `maquina`, `min_replicas`, `canario`, `auc_minimo`, `promover`, `retirar_anterior`) y cierra con Esc.

### 2 · `pend-02-run-esperando-aprobacion.webp` (L5, «El workflow de desplegar, por dentro»)
1. Haz `git push` a `lab/vertex-champion/ensayo` (o lanza el workflow a mano).
2. Abre el run desde **Actions** y espera a que el trabajo «1 · Champion, puerta de calidad y prueba de la imagen» esté en verde.
3. Con el trabajo «2 · Publicar en Artifact Registry y desplegar en Vertex AI (con aprobación)» en **Waiting**, encuadra: el grafo de trabajos, el aviso amarillo *requested your review to deploy to produccion* y el botón **Review deployments** (sin pulsarlo todavía).

### 3 · `pend-03-resumen-modelo.webp` (L5, «El resumen y el enlace»)
1. En el mismo run, con el trabajo 1 terminado, baja en la página **Summary** hasta el bloque **Champion listo para Vertex AI**.
2. Encuadra: la versión de MLflow, la etiqueta de la imagen probada en el runner, la línea de la puerta de calidad y la tabla de paridad con `IGUAL`.

### 4 · `pend-04-resumen-desplegado.webp` (L5, «El resumen y el enlace»)
1. Pulsa **Review deployments**, marca `produccion` y aprueba (lo hace quien tiene permiso de revisor).
2. Cuando acabe el trabajo 2, baja hasta el bloque **Desplegado en Vertex AI**.
3. Encuadra la tabla **MLflow | Vertex AI** (versión, huella, AUC), el aviso de que el endpoint cobra y la salida de paridad.

### 5 · `pend-05-ar-imagen.webp` (L3, «Subir el modelo»)
1. En la consola de Google Cloud, menú ☰ → **Artifact Registry** → **Repositorios**.
2. Abre el repositorio `curso`, después el paquete `retencion-vertex`.
3. Encuadra la lista de versiones con la etiqueta `v<N>-<huella>`; **difumina el nombre del proyecto**.

### 6 · `pend-06-registro-versiones.webp` (L3, «Subir el modelo»)
1. Consola → menú ☰ → **Vertex AI** → **Registro de modelos**.
2. En el selector **Región** elige **southamerica-west1 (Santiago)**.
3. Abre `retencion-90d-champion` y la pestaña **Versiones**.
4. Encuadra las dos versiones con sus **alias** (`champion`, `mlflow-vN`) y, si caben, las etiquetas.

### 7 · `pend-07-endpoint-canario.webp` (L3, «Desplegar en canario»)
1. Hazla **entre** `desplegar.sh --canario 10` y `promover.sh`.
2. Consola → **Vertex AI** → **Extremos** → región Santiago → `retencion-90d-champion-ep`.
3. Encuadra los **dos modelos desplegados** con su reparto de tráfico (**90 % / 10 %**).

### 8 · `pend-08-cloudshell-subir.webp` (L3, «Subir el modelo»)
1. En Cloud Shell, ejecuta `bash scripts/subir_modelo.sh`.
2. Cuando termine, encuadra las últimas líneas: `Listo: MLflow v… -> retencion-90d-champion versión …` y el aviso «Sin desplegar: no cobra máquinas».

### 9 · `pend-09-cloudshell-probar.webp` (L3, «Probar y comparar»)
1. Con el canario activo (antes de promover), ejecuta `bash scripts/probar.sh`.
2. Encuadra: el `intento N: contestó otra versión` (si hubo), la tabla de comparación con `IGUAL` y la línea `PARIDAD: las predicciones del endpoint y las del modelo local coinciden.`

### 10 · `pend-10-rollback-run.webp` (L4, «Volver a la versión anterior»)
1. En Actions, lanza **Vertex AI · volver a la versión anterior** (sin entradas, o con `a_version`).
2. Aprueba el despliegue en el environment `produccion`.
3. Cuando acabe, encuadra el **Summary** con la salida de `volver.sh` y el nuevo reparto de tráfico.

### 11 · `pend-11-borrar-confirmacion.webp` (L6, «Cuánto cuesta y cómo no dejarlo encendido»)
1. En Actions, abre **Vertex AI · borrar todo** y pulsa **Run workflow**.
2. Escribe `BORRAR` en la entrada `confirmacion`.
3. Captura el formulario **antes** de pulsar el botón verde.

### 12 · `pend-12-vacio-final.webp` (L6, «Cuánto cuesta y cómo no dejarlo encendido»)
1. Tras el borrado, en la consola abre **Registro de modelos** y **Extremos** (región Santiago): deben estar **vacíos**.
2. En Cloud Shell, ejecuta `gcloud ai endpoints list --region southamerica-west1` y `gcloud ai models list --region southamerica-west1`: sin filas.
3. Encuadra una de las dos pantallas vacías (o monta las dos en una sola imagen) y dala por buena solo si **todo** está vacío.

### 13 · `pend-13-variables-gcp-repo-ar.webp` (L3, «Preparar Google Cloud y GitHub»)
1. En tu fork: **Settings** → **Secrets and variables** → **Actions** → pestaña **Variables**.
2. Con `GCP_REPO_AR` ya añadida (y `CURSO_MLFLOW_URI` si se usa), encuadra la tabla **Repository variables**.
3. Difumina los valores salvo la región.

## Capturas que SÍ son reales (ya en `img/`)

| Archivo | Qué es | Origen |
|---|---|---|
| `vx-01-registro-modelos.webp` | Registro de modelos, **lista vacía** (el selector de región enseña `us-central1`: no se pudo cambiar sin interactuar con la página; en el laboratorio se elige `southamerica-west1`) | Consola de GCP, solo lectura, 27/11/2026, nombre del proyecto difuminado |
| `vx-02-endpoints.webp` | Extremos, lista vacía (mismo selector) | idem |
| `vx-03-artifact-registry.webp` | Artifact Registry sin repositorios (el `curso` de S4 se borró) | idem |
| `vx-04-iam.webp` | IAM del proyecto: **no** aparece `sa-github-despliegue` (se borró al acabar S4) | idem, con correos y nombre del proyecto difuminados |
| `vx-05-gh-actions.webp`, `vx-06-gh-variables.webp`, `vx-07-gh-environments.webp` | Actions, variables del repositorio (valores difuminados salvo la región; solo las cinco de S4: falta `GCP_REPO_AR`) y environment `produccion` con 1 regla de protección | GitHub, solo lectura, 27/11/2026 |
| `s4-aprobacion-environment.webp`, `s4-job-summary.webp` | La espera de aprobación (*Review deployments*) y un Job Summary **de otros workflows de S4**: el mecanismo es el mismo | S4, 25-26/11/2026 |
| `t-*.webp` | **Salidas reales de terminal** de esta carpeta (en `salidas/`), dibujadas como imagen con `terminal_a_imagen.py`: no son capturas de la ventana del terminal | Esta carpeta, 27/11/2026 |

No se pudo capturar el formulario **Run workflow**: las páginas de los workflows de S4 en GitHub no lo muestran porque esos archivos aún no están en la rama por defecto del repositorio.
