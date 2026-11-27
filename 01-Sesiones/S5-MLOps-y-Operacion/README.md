# S5: MLOps y operación

Duración propuesta: 4 horas (la sesión del viernes 27/11 a las 10:00, hora de Perú), más una **sesión de cierre** con la clase de fundamentos.

## Contenido
Versionado de datos, variables, modelos, código e imágenes. Métricas del servicio frente a calidad del modelo.
Deriva de datos y rendimiento, registros y alertas, seguridad y mantenimiento, actualización y rollback, introducción a costes.
Agentes: servidor MCP, LLM local, trazas, evaluación y despliegue con aprobación.

## Práctica
Registrar versiones en el registro de MLflow; simular deriva con datos de otro periodo; revisar monitoreo y alertas; reentrenar y publicar una
nueva versión desde el workflow; practicar la recuperación de la versión anterior moviendo el alias del modelo (p. ej. `champion`).

## Tarea
Consolidar repositorio, informe y demostración (`tarea/README.md`, rúbrica en `tarea/rubrica.md`, plantilla en `evidencias/plantilla-avance-5.md`).

## Evidencia
Entrega posterior a S5: viernes 11 de diciembre, a las 10:00 (hora de Perú).

## Materiales (estado a 26/11/2026)

| Carpeta o archivo | Qué es | Estado |
|---|---|---|
| `teoria/`, `practica/`, `tarea/`, `evidencias/`, `guion.md`, `checklist.md` | Los siete documentos de la sesión | Escritos; los pesos de la rúbrica y la demostración final (vídeo o en vivo) **están por decidir** por el profesor |
| `laboratorio-mlops/` | MLOps clásico: deriva (PSI y KS), AUC por corte, alias `champion`, rollback y workflow de monitoreo con issue de alerta (27 diapositivas, ~140 min) | Ensayado en GitHub Actions el 26/11/2026 (estable en verde, deriva en rojo, el segundo run comenta en el mismo issue) |
| `laboratorio-agentes/` | Agente con servidor MCP, LLM local (Ollama), trazas, skills, evaluación y despliegue en GitHub | Cuatro workflows ensayados el 22 y 23/11/2026; el extra de dos agentes solo está planteado |
| `extra-mcp-notebooks/` | Extra opcional: dos servidores MCP solo con notebooks (datos en SQLite y BigQuery; el modelo con predicción), 26 diapositivas y una interfaz web (`ui/`) | Notebooks ejecutados en Windows; BigQuery probado en Cloud Shell con un script equivalente; **sin verificar** en Codespace, con VS Code/Copilot y con un LLM real eligiendo herramienta |
| `extra-destilacion-notebooks/` | Extra opcional: destilación de modelos en notebooks (v1: cuadernos 00-05; v2: 06-07, el estudiante de sentimiento sí se promociona), ejecutados en CPU | Salidas guardadas de una ejecución en CPU (Linux, Python 3.12, PyTorch solo CPU). **Sin verificar** en Windows, en un Codespace ni con el alumnado |
| `extra-rag-notebooks/` | Extra opcional: RAG en notebooks (00-06) con embeddings y un LLM pequeño en CPU, corpus propio en español y evaluación con/sin recuperación | Salidas guardadas de una ejecución en CPU (Linux, Python 3.12, modo rápido). **Sin verificar** en Windows, en un Codespace ni con el alumnado |
| `clase-fundamentos-ia-agentes/` | **Sesión de cierre**: fundamentos de IA, LLM, embeddings, RAG, agentes y sistemas agénticos, con 12 capturas reales de la consola de Google Cloud (41 diapositivas, ~64 min propuestos, sin límite: el profesor la imparte a su ritmo) | Revisada pantalla a pantalla; dos equivalencias de nombres de Google Cloud **sin verificar** (ver su diapositiva de fuentes) |

Cómo se reparten las 4 horas entre MLOps clásico y agentes (hay una propuesta en `guion.md`) y dónde cae la clase de cierre lo decide el profesor.
