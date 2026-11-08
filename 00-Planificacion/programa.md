# Programa

Objetivo del curso: llevar un modelo de ML clásico desde el dato hasta un servicio
que otra persona pueda usar, documentar y operar (enfoque MLOps).

Lo relacionado con IA generativa es **opcional**: redes neuronales, LLM abiertos, RAG,
agentes, MCP y la visión de LLMOps/IAOps/AgentOps. Quedan fuera del núcleo obligatorio.

Docker y Kubernetes **no se instalan en local**: se trabajan en Codespaces.
Los pipelines se orquestan con GitHub Actions.

## S0 · Presentación y entorno · 2 horas

Contenido: Parte A: objetivos, recorrido, caso y entregas. Parte B: software local
(Git, VS Code, Miniconda, SQLite), repositorio, Docker y Kubernetes en Codespaces, cloud y diagnóstico.

Tarea: Completar preparación y leer el caso.

Evidencia: Entorno comprobado antes de S1.

## S1 · Datos y entrenamiento · 4 horas

Contenido: Raw → master → fs → ml; particiones, entrenamiento, evaluación y artefactos.

Tarea: Ejecutar scripts base y adaptar una transformación o variable.

Evidencia: Avance en S2: datos, modelo, métricas y explicación.

## S2 · API y Docker · 4 horas

Contenido: Carga del modelo, preprocesamiento, FastAPI, validación, errores, Dockerfile e imagen
(construida en Codespaces). Primer workflow de GitHub Actions que construye la imagen.

Tarea: Crear API propia, contenerizar y comparar predicciones.

Evidencia: Avance en S3: API, contenedor y pruebas.

## S3 · Despliegue en la nube · 4 horas (red neuronal opcional)

Contenido: Artifact Registry, Cloud Run, recursos y registros. Laboratorio acotado de Kubernetes
en Codespaces. Opcional: práctica neuronal guiada con PyTorch.

Tarea: Desplegar el servicio de ML. Opcional: reproducir el módulo neuronal ligero.

Evidencia: Avance en S4: despliegue y registros (más mediciones neuronales si se hace el módulo).

## S4 · LLMs abiertos · 4 horas (sesión opcional)

Contenido: Pesos, tokenizador, contexto, motor de inferencia, aplicación cliente y evaluación básica.

Estado: contenido y horario por confirmar. Ver propuesta en `decisiones-y-pendientes.md`.

Tarea: Opcional: adaptar aplicación consumidora y documentar respuestas y limitaciones.

Evidencia: Avance en S5, solo si se realiza el módulo.

## S5 · MLOps y operación · 4 horas

Contenido: Versionado, pruebas, orquestación del pipeline con GitHub Actions, registros, alertas,
actualización y rollback.

Tarea: Consolidar repositorio, informe y demostración.

Evidencia: Entrega posterior a S5; fecha por definir.

## Dinámica
S0: 25 min de Parte A, 15 min de pausa, 70 min de Parte B (entorno obligatorio) y 10 min de cierre = 120 min.
S1–S5: propuesta de 30 min de revisión, 60 min de teoría, 135 min de práctica y 15 min de siguiente entrega.
Trabajo autónomo orientativo: 2–3 horas entre sesiones.
