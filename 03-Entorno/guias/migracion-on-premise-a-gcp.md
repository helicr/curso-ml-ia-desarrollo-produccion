# De on-premise a GCP: hilo de migración del curso

Estado: propuesta de diseño del 08/11/2026. Nada de esto está implementado ni probado.
Servicios, cuotas y precios de GCP cambian: verificarlos antes de impartir.

## Idea
En S1 y S2 todo corre «en local»: archivos, SQLite, scripts, MLflow y Docker en la máquina del alumno (o Codespace).
Eso hace de **on-premise simulado**: la situación de partida de muchos equipos. En S3 se migra a GCP, y en S4 y S5 se
automatiza y se opera. Así se enseña a extrapolar el caso a la nube y a migrar lo que ya existe.

## Mapa de equivalencias
| Componente del curso | Local / on-premise | GCP | Estrategia |
|---|---|---|---|
| Archivos originales (`data/raw`) | Carpeta o servidor de archivos | Cloud Storage (bucket, versionado de objetos) | Replatform |
| Capas `master_`, `fs_`, `ml_` | SQLite | BigQuery (analítico) o Cloud SQL (transaccional) | Replatform |
| Pipeline de datos y entrenamiento | Scripts manuales o `cron` | GitHub Actions (curso). Alternativas: Cloud Build, Cloud Scheduler + trabajos de Cloud Run, Vertex AI Pipelines, Cloud Composer | Refactor |
| Seguimiento y registro de modelos | MLflow con SQLite y carpeta local | MLflow con Cloud SQL y Cloud Storage. Alternativa: Vertex AI Experiments y Model Registry | Replatform |
| Imágenes | Docker local | Artifact Registry | Rehost |
| Servicio de la API | `uvicorn` en un servidor o máquina virtual | Cloud Run (alternativas: Compute Engine, GKE) | Rehost / Replatform |
| Credenciales | Archivo `.env` | Secret Manager | Replatform |
| Identidad y permisos | Usuarios y claves locales | IAM, cuentas de servicio con mínimos privilegios, Workload Identity Federation | Refactor |
| Registros, métricas y alertas | Archivos de log | Cloud Logging y Cloud Monitoring | Replatform |
| Tareas programadas | `cron` | Cloud Scheduler | Replatform |
| Costes | Hardware fijo | Presupuestos y alertas de facturación | Nuevo |

## Estrategias de migración (3 de las 6 «R»)
- **Rehost** (*lift and shift*): mover tal cual. Ejemplo: la imagen Docker del servicio pasa a Artifact Registry y Cloud Run.
- **Replatform:** mover cambiando la plataforma, con ajustes mínimos. Ejemplo: SQLite → BigQuery, archivos → Cloud Storage.
- **Refactor:** rediseñar para aprovechar la nube. Ejemplo: scripts manuales → workflow orquestado, claves → identidad federada.
Las otras (retener, retirar, recomprar) se mencionan, sin práctica.

## Fases de una migración
Evaluar (inventario y dependencias) → planificar (orden, riesgos, rollback) → ejecutar → optimizar (coste y operación).
Contrastar los nombres de las fases con la documentación vigente de Google Cloud antes de citarlos.

## Práctica propuesta en S3 (migrar el caso)
1. Inventario: listar qué usa el caso hoy (archivos, tablas, secretos, servicio, MLflow).
2. Subir `data/raw` a Cloud Storage y comprobar la integridad con el SHA-256 de `MANIFEST.sha256`.
3. Exportar las tablas `master_`, `fs_` y `ml_` de SQLite (por ejemplo a Parquet) y cargarlas en BigQuery.
4. **Validar la migración:** comparar conteos, esquemas y agregados entre SQLite y BigQuery. Estas comprobaciones se vuelven `pytest`.
5. Mover los secretos a Secret Manager y crear una cuenta de servicio con permisos mínimos.
6. Publicar la imagen en Artifact Registry y desplegar en Cloud Run apuntando a los datos migrados.
7. Documentar el plan de rollback (cómo volver a lo local si falla).

## Tarea
Migrar el caso propio a GCP y entregar el inventario, los resultados de validación, la configuración y los registros.

## Riesgos y cautelas
- **Costes:** usar presupuestos y alertas, borrar recursos al terminar y no crear nada de pago en S0. Verificar los límites gratuitos
  de BigQuery y Cloud Storage antes del curso.
- **Datos:** ningún dato sensible ni personal en la nube del curso. Comprobar la licencia antes de subir un dataset.
- **Carga de S3:** la sesión es densa (migración, despliegue y laboratorio de Kubernetes). El laboratorio de Kubernetes pasa a «si hay tiempo»
  y la parte neuronal sigue siendo opcional.
- **Acceso:** los alumnos necesitan proyecto de GCP con facturación habilitada o una alternativa (proyecto compartido del instructor).

## Pendiente
- Definir el proyecto de GCP por alumno o compartido, y el control de costes.
- Probar el flujo completo SQLite → Cloud Storage → BigQuery con el dataset elegido.
- Decidir si MLflow se migra a Cloud SQL y Cloud Storage en el curso o solo se menciona (Vertex AI como alternativa).
- Escribir los scripts de exportación, carga y validación.
