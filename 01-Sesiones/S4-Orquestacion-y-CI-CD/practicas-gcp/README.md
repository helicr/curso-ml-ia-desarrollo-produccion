# Prácticas en Google Cloud (S4): del contenedor al LLM gestionado

Cinco prácticas con NUESTRO caso (probabilidad de recompra a 90 días, `04-Proyecto-Base`). Todas se ejecutan en **Cloud Shell** (bash) y siguen la regla:

> **CREA → PRUEBA → BORRA.** Cada práctica tiene `crear.sh`, `probar.sh` y `borrar.sh`. No pases a la siguiente sin haber ejecutado `borrar.sh` (salvo la 02, que necesita la imagen de la 01; ver orden).

## Datos fijos

| Dato | Valor |
|---|---|
| Proyecto | `project-curso-ml-ia` |
| Región | `southamerica-west1` (Santiago): cercana a Perú |
| Dónde se ejecuta | Cloud Shell (la web de la consola: botón «Activar Cloud Shell») |
| Claves de cuentas de servicio | **Ninguna.** La organización lo prohíbe (`iam.disableServiceAccountKeyCreation`); se usa la sesión de Cloud Shell |
| Cuenta | Crédito de prueba: máquinas mínimas, 1 nodo, todo se borra al terminar |

## Primer uso (Cloud Shell)

```bash
# Cloud Shell: clona el repositorio del curso (si ya lo tienes, haz git pull) y entra en la carpeta
cd ~ && git clone https://github.com/helicr/curso-ml-ia-desarrollo-produccion.git   # (si el repositorio es privado: pide acceso; sin verificar)
cd curso-ml-ia-desarrollo-produccion/01-Sesiones/S4-Orquestacion-y-CI-CD/practicas-gcp
chmod +x *.sh */*.sh
gcloud config set project project-curso-ml-ia
```

Los scripts generan solos el modelo y los datos del proyecto la primera vez (`operacional` + `pipeline` de `04-Proyecto-Base`, en un entorno virtual `~/.venv-curso-ml`; hace falta Python 3.11 o superior en Cloud Shell: **sin verificar** qué versión trae hoy).

## Orden recomendado

| # | Práctica | Qué se aprende | APIs que habilita | Se queda del curso en GCP |
|---|---|---|---|---|
| 1 | `01-docker-artifact-registry` | Imagen → registro → Cloud Run | `artifactregistry`, `run` | nada tras `borrar.sh` |
| 2 | `02-kubernetes-gke` | Pod, Deployment, Service en GKE Autopilot | `container`, `artifactregistry` | nada |
| 3 | `03-dataproc-spark` | PySpark sin servidor sobre nuestros datos | `dataproc`, `storage` | nada |
| 4 | `04-vertex-modelo` | Model Registry + endpoint + predicción online | `aiplatform`, `storage` | nada |
| 5 | `05-vertex-llm` | Gemini explica la predicción | `aiplatform` | nada |

**Orden de ejecución con la menor factura:** 01 (crear y probar) → 02 (crear, probar, **borrar**) → 01 `borrar.sh` → 03 → 04 → 05. La 02 descarga la imagen que sube la 01, así que `01/borrar.sh` va después de la 02. Si algo queda sin borrar, `./borrar-todo.sh` lo limpia todo.

Las APIs habilitadas **no se deshabilitan** al borrar (no cuestan y otras prácticas las usan).

## Limpieza total

```bash
# Cloud Shell, en esta carpeta
./borrar-todo.sh
```

Ejecuta los cinco `borrar.sh` (de la 05 a la 01) y lista al final Cloud Run, clústeres, repositorios, lotes de Dataproc, endpoints, modelos y buckets. Debe salir todo vacío.

## Regiones elegidas (con fuente)

| Servicio | Región | Verificado |
|---|---|---|
| Artifact Registry | `southamerica-west1` | Sí: [repo-locations](https://docs.cloud.google.com/artifact-registry/docs/repositories/repo-locations) |
| Cloud Run | `southamerica-west1` | Sí (Tier 2): [run/docs/locations](https://docs.cloud.google.com/run/docs/locations) |
| GKE Autopilot | `southamerica-west1` | Parcial: GKE figura entre los productos de toda región ([about/locations](https://cloud.google.com/about/locations)); la página de Autopilot no la nombra: **sin verificar** |
| Cloud Storage | `southamerica-west1` | Igual que GKE (productos de toda región) |
| Dataproc sin servidor | `southamerica-west1` | **Sin verificar**: la documentación no lista regiones; alternativa `southamerica-east1` (variable `CURSO_REGION_SPARK`) |
| Vertex AI (modelo propio: registro, endpoint) | `southamerica-west1` | Sí: Santiago admite Model Registry, entrenamiento y predicción online de modelos propios ([locations](https://docs.cloud.google.com/vertex-ai/docs/general/locations)). No admite Model Monitoring, Experiments ni Explainable AI |
| Gemini (LLM gestionado) | `global` | Santiago **no** figura para Gemini. `global` es el endpoint mundial (sin garantía de región de procesamiento): [learn/locations](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/locations). La región más cercana, `southamerica-east1` (São Paulo), figura con tablas ilegibles en esa página: **sin verificar** modelo por modelo |

Cambiar de región: `export CURSO_REGION=...` (o `CURSO_REGION_VERTEX`, `CURSO_REGION_GEMINI`, `CURSO_REGION_SPARK`) antes de ejecutar los scripts.

## Costes

No se da ninguna cifra: no se ha podido leer la tabla de precios oficial. Consúltala con fecha el día de la clase y anótala:
[Cloud Run](https://cloud.google.com/run/pricing) · [GKE](https://cloud.google.com/kubernetes-engine/pricing) · [Artifact Registry](https://cloud.google.com/artifact-registry/pricing) · [Dataproc sin servidor](https://cloud.google.com/dataproc-serverless/pricing) · [Vertex AI](https://cloud.google.com/vertex-ai/pricing) · [Gemini](https://cloud.google.com/vertex-ai/generative-ai/pricing).
**Lo que más cobra si se olvida:** el endpoint de Vertex (04) y el clúster de GKE (02) cobran por tiempo mientras existen. Bórralos al acabar.

## Comprobar los scripts sin Google Cloud

```bash
python -m pytest -q pruebas -p no:cacheprovider
```
Comprueba sintaxis (`bash -n`), YAML, que no hay claves de cuentas de servicio, que cada `crear.sh` tiene su `borrar.sh` y que las regiones son las declaradas.

## Documentación oficial usada

- Contenedores pre-construidos de scikit-learn: https://docs.cloud.google.com/vertex-ai/docs/predictions/pre-built-containers
- Cloud Run: https://docs.cloud.google.com/run/docs/deploying
- GKE Autopilot: https://docs.cloud.google.com/kubernetes-engine/docs/how-to/creating-an-autopilot-cluster
- Dataproc sin servidor: https://docs.cloud.google.com/dataproc-serverless/docs/quickstarts/spark-batch
- Vertex AI predicción online: https://docs.cloud.google.com/vertex-ai/docs/predictions/get-online-predictions
- SDK de IA generativa: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/sdks/overview
- Ciclo de vida de los modelos Gemini: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versions
