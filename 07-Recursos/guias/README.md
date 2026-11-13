# Guías de uso de herramientas: índice e inventario

Chuletas para las herramientas que se usan en el curso: qué son, para qué sirven, comandos principales y errores frecuentes.
Se añaden **de forma incremental**, en el orden en que cada sesión las necesita. Este archivo es el inventario: qué hay, qué falta y para cuándo.

Estado a 09/11/2026. Solo Windows 10 (1809 o superior) y Windows 11 como equipo del alumno, con alternativa en la nube (Codespaces y Cloud Shell).

## Cómo están hechas
Todas siguen la misma estructura: **para qué sirve** · comprobación de la sesión · **chuleta** de comandos · errores frecuentes · **qué se probó y qué no**.
Los comandos se escriben para CMD y PowerShell (los dos valen salvo que se diga). Cada guía declara con honestidad dónde se ejecutó (hasta ahora, Linux) y qué queda sin verificar en Windows real.

## Hechas
| Guía | Sesiones | Estado de pruebas |
|---|---|---|
| [Miniconda y entornos](miniconda-y-entornos.md) | S0 y todas | Comandos ejecutados con conda 26.9.4 en Linux; entorno del curso creado y 34 tests en verde. Sin probar en Windows |
| [Git y ramas](git-y-ramas.md) | S0 y todas las entregas | Comandos ejecutados con Git 2.43 en Linux contra un remoto local. Sin probar en Windows ni con autenticación de GitHub |
| [Visual Studio Code](vscode.md) | S0 y todas | **Sin probar con VS Code real**: revisar menús y atajos antes de entregarla |
| [SQLite](sqlite.md) | S0, S1 (y S3) | Consultas y comandos ejecutados contra la base real del caso. DB Browser for SQLite sin probar |
| [Docker, Kubernetes y GKE](../../03-Entorno/guia-docker-kubernetes-gke/README.md) (diapositivas, [chuleta](../../03-Entorno/guia-docker-kubernetes-gke/chuleta.md) y [ejercicios](../../03-Entorno/guia-docker-kubernetes-gke/ejercicios.md)) | S2 (Docker) y S3 (Kubernetes, GKE) | Práctica de kind ejecutada entera en el Codespace del curso (13/11/2026), con capturas. GKE y Artifact Registry: comandos de la documentación oficial, sin ejecutar. Cubre la guía prevista `docker.md` |
| [Codespaces](../../03-Entorno/guia-codespaces/README.md) | S0, S2, S3 | Probada en un Codespace real del curso (12/11/2026), con capturas. Cubre la guía prevista `codespaces.md` |
| [Guía rápida del entorno (S0 → S1)](../../01-Sesiones/S0-Presentacion-y-Entorno/practica/guia-rapida-entorno-s0-s1.md) | S0 y S1 | Instalación en orden, entorno desde `environment.yml`, pruebas y verificador. Comandos de Python, conda, pytest, SQLite y MLflow ejecutados en Linux en un entorno creado desde cero, con sus salidas reales. Windows (winget, Anaconda Prompt, VS Code) sin probar. Versión en diapositivas: `01-Sesiones/S0-Presentacion-y-Entorno/slides/instalacion/index.html` |

## Pendientes, por orden de necesidad
Prioridad **A**: la sesión no se puede dar bien sin ella. **B**: ayuda mucho. **C**: opcional.

### Antes de S0 (mañana) y S1
| Prioridad | Guía prevista (archivo) | Sesión | Contenido previsto |
|---|---|---|---|
| A | `gcloud-y-cloud-shell.md` | S0 (punto 9 del checklist), S3, S4 | `gcloud auth login`, proyecto activo, `gcloud config list`, Cloud Shell, cuotas, qué **no** crear en S0. Hoy solo hay cuatro comandos en `03-Entorno/guias/preparacion-paso-a-paso.md` |
| A | `codespaces.md` | S0 (puntos 8 y 10), S2, S3 | Crear, abrir (navegador y VS Code), parar y borrar un Codespace; cuota gratuita; `devcontainer.json`; `gh codespace`. **Bloqueada:** el Codespace del curso aún no existe (pendiente 6) |
| A | `mlflow.md` | S1, S2, S4, S5 | `mlflow ui --backend-store-uri sqlite:///models/mlflow.db`, experimentos, comparar ejecuciones, huella del dato, firma del modelo, registro con alias y rollback. Incluir el fallo de `RandomForest` con skops (pendiente 11d) |
| A | `cuadernos-y-pruebas.md` | S1 | Ejecutar cuadernos como pipelines con `papermill`, traducirlos con `jupytext`, `pytest` (`-k`, `-m "not lento"`), equivalencia cuaderno = paquete |
| B | `terminal-en-windows.md` | S0 y todas | CMD frente a PowerShell frente a Git Bash; rutas con `\`; variables de entorno; redirección (`<` no existe en PowerShell); `where`; por qué no hay `make` |

### S2
| Prioridad | Guía prevista (archivo) | Contenido previsto |
|---|---|---|
| A | `docker.md` | Imagen frente a contenedor; `build`, `run -p`, `ps`, `logs`, `exec`, `stop`, `rm`, `images`, `system prune`; `Dockerfile` de la API; `.dockerignore`; variables de entorno; etiquetas; todo en Codespaces |
| A | `fastapi-y-probar-apis.md` | `uvicorn`, `/docs` (Swagger), validación con Pydantic, códigos de error (422), probar con `curl` y `httpx`, comparar predicciones |
| A | `github-actions.md` | **Solicitada.** Para qué sirve; anatomía de un workflow (`on`, `jobs`, `steps`, `runs-on`, `uses`); primer workflow que construye la imagen; chuleta de `gh` (`run list`, `run view --log`, `run watch`, `run rerun`, `workflow run`, `secret set`); depurar un workflow que falla |

### S3
| Prioridad | Guía prevista (archivo) | Contenido previsto |
|---|---|---|
| A | `gcp-datos-cloud-storage-y-bigquery.md` | Cargar archivos raw a Cloud Storage (`gcloud storage`), cargar tablas a BigQuery (`bq load` o cliente Python), consultar, validar conteos y esquemas frente a SQLite |
| A | `gcp-servicio-artifact-registry-y-cloud-run.md` | Publicar la imagen, `gcloud run deploy`, variables y secretos, URL del servicio, leer registros (Cloud Logging o `gcloud run services logs read`; comprobar la sintaxis vigente) |
| A | `gcp-secretos-e-iam.md` | Secret Manager, cuenta de servicio, permisos mínimos, qué nunca va al repositorio |
| A | `costes-y-limpieza-gcp.md` | Presupuestos y alertas, qué cuesta qué, **listado de recursos a borrar al terminar** |
| B | `kubernetes-kubectl-y-kind.md` | **Solicitada.** Pod, Deployment y Service en una página; `kind create cluster`, `kind load docker-image`; `kubectl get / describe / logs / apply / delete / port-forward`; manifiestos de `04-Proyecto-Base/deploy/kubernetes/`; limpiar. El laboratorio es «si hay tiempo»; el punto 10 del checklist de S0 solo comprueba que respondan `kind` y `kubectl` |
| C | `pytorch-modulo-neuronal.md` | Solo si se imparte la práctica neuronal opcional |

### S4 y S5
| Prioridad | Guía prevista (archivo) | Sesión | Contenido previsto |
|---|---|---|---|
| A | `github-actions.md` (ampliada) | S4 | Disparadores, secretos, variables y *environments* con aprobación, artefactos, caché, matrices, CI frente a CD |
| A | `autenticacion-actions-gcp-sin-claves.md` | S4 | Workload Identity Federation: qué es, configuración mínima, errores típicos de permisos |
| B | `monitoreo-y-registros-en-gcp.md` | S5 | Cloud Logging, lectura de registros desde `gcloud`, alertas, qué vigilar en el servicio y en el modelo |
| B | `versionado-y-rollback.md` | S5 | Qué se versiona (datos, variables, modelo, imagen), alias del registro de MLflow (`champion`), cómo volver a la versión anterior |

### Módulo opcional de LLMs (`06-Modulo-LLMs/`)
| Prioridad | Guía prevista (archivo) | Contenido previsto |
|---|---|---|
| C | `llm-local-con-ollama.md` | Instalar el motor, descargar un modelo pequeño, consumirlo desde Python, streaming. Depende de la elección de motor y modelo (pendiente 5) |

## Qué no tendrá guía propia
Librerías como `pandas` o `scikit-learn`: se enseñan en los cuadernos. `make`: no existe en Windows, y el README de `04-Proyecto-Base` ya da las líneas equivalentes.

## Material de sesión que también falta (no son guías de herramienta)
| Sesión | Qué hay | Qué falta |
|---|---|---|
| S0 | README, guion, checklist, slides | Tarea y teoría (carpetas vacías) |
| S1 | README, guion, checklist, slides, teoría, guía de laboratorio, tarea, rúbrica, plantilla de decisión | Completa |
| S2–S5 | Solo README | Guion, slides, teoría, laboratorio, tarea y rúbrica |
| `05-Modulo-Redes-Neuronales` | Vacío | Todo |
| `06-Modulo-LLMs` | README | Práctica y materiales |
| `08-Evaluacion-Final` | Vacío | Rúbrica y formato (pendiente 13) |

## Cómo añadir una guía
1. Copia la estructura de [`sqlite.md`](sqlite.md) (la más completa) y ejecuta cada comando antes de escribirlo.
2. Declara en «Qué se probó y qué no» dónde se ejecutó y qué quedó sin comprobar.
3. Cambia su estado en este inventario y enlázala en la tabla «Hechas».
