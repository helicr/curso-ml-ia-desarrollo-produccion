# Programa

Objetivo del curso: llevar un modelo de ML clásico desde el dato hasta un servicio
que otra persona pueda usar, documentar y operar (enfoque MLOps).

Lo relacionado con IA generativa es **opcional**: redes neuronales, LLM abiertos, RAG,
agentes, MCP y la visión de LLMOps/IAOps/AgentOps. Quedan fuera del núcleo obligatorio.

En S1 y S2 todo corre en local (on-premise simulado); en S3 se migra a GCP.

Docker y Kubernetes **no se instalan en local**: se trabajan en Codespaces.
Los pipelines se orquestan con GitHub Actions.

## S0 · Presentación y entorno · 2 horas

Contenido: Parte A: objetivos, recorrido, caso y entregas. Parte B: software local
(Git, VS Code, Miniconda, SQLite), repositorio, Docker y Kubernetes en Codespaces, cloud y diagnóstico.

Tarea: Completar preparación y leer el caso de Bank Marketing (el de los alumnos; el del instructor es Online Retail II).

Evidencia: Entorno comprobado antes de S1.

## S1 · Datos y entrenamiento · 4 horas

Contenido: Raw → master → fs → ml; particiones, entrenamiento, evaluación y artefactos. Seguimiento de experimentos con MLflow (versión ligera, 15–20 min).

Tarea: Añadir una variable nueva a FS, reconstruir ML, reentrenar, comparar dos ejecuciones de MLflow y decidir con evidencia; entregar la traducción a `.py`.

Evidencia: Decisión escrita (`evidencias/plantilla-decision.md`), comparación en MLflow y avance en S2: datos, modelo, métricas y explicación.

Materiales preparados: `01-Sesiones/S1-Datos-y-Entrenamiento/` (slides, guion, checklist, teoría, práctica, tarea y rúbrica).

## S2 · API y Docker · 4 horas

Contenido: Carga del modelo (desde MLflow), preprocesamiento, FastAPI, validación, errores, Dockerfile e imagen
(construida en Codespaces). Primer workflow de GitHub Actions que construye la imagen.

Tarea: Crear API propia, contenerizar y comparar predicciones.

Evidencia: Avance en S3: API, contenedor y pruebas.

## S3 · De local a GCP: migración y despliegue · 4 horas (red neuronal opcional)

Contenido: Migrar de on-premise a GCP (evaluar, planificar, ejecutar y optimizar; rehost, replatform y refactor) y mapa de
equivalencias. Práctica: datos raw a Cloud Storage, tablas master/fs/ml de SQLite a BigQuery con validación, Secret Manager y cuenta
de servicio, Artifact Registry y Cloud Run, registros. Laboratorio de Kubernetes en Codespaces, si hay tiempo.
Opcional: práctica neuronal guiada con PyTorch.

Tarea: Migrar el caso propio a GCP y desplegar el servicio, documentando inventario, validaciones y registros.
Opcional: reproducir el módulo neuronal ligero.

Evidencia: Avance en S4: datos migrados y validados, servicio desplegado y registros.

Guía: `03-Entorno/guias/migracion-on-premise-a-gcp.md`.

## S4 · Orquestación y CI/CD con GitHub Actions · 4 horas

Contenido: Workflows, runners y disparadores; secretos y autenticación con GCP sin claves; pruebas,
pipeline raw → modelo, registro del modelo en MLflow, construcción y publicación de imagen, despliegue en Cloud Run con aprobación; depuración de workflows.

Tarea: Orquestar el pipeline del caso propio con un workflow y documentarlo.

Evidencia: Avance en S5: workflow funcionando, historial de ejecuciones y una decisión explicada.

## S5 · MLOps y operación · 4 horas

Contenido: Versionado de datos y modelos (registro de MLflow con alias), deriva, monitoreo, registros y alertas, seguridad, actualización y rollback,
introducción a costes.

Tarea: Consolidar repositorio, informe y demostración.

Evidencia: Entrega posterior a S5; fecha por definir.

## Módulo opcional: LLMs abiertos (sesión extra)
Fuera del núcleo; ver `06-Modulo-LLMs/README.md`. Se imparte solo si hay tiempo.

## Dinámica
S0: 25 min de Parte A, 15 min de pausa, 70 min de Parte B (entorno obligatorio) y 10 min de cierre = 120 min.
S1–S5: propuesta de 30 min de revisión, 60 min de teoría, 135 min de práctica y 15 min de siguiente entrega.
Trabajo autónomo orientativo: 2–3 horas entre sesiones.
