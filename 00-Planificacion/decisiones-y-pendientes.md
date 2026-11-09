# Decisiones y pendientes

## Acordado
- Proyecto transversal desde S1 con avances en la siguiente sesión.
- Scripts y notebooks base para ejecutar y adaptar, no programar todo desde cero.
- Capas: raw → master → fs → ml → entrenamiento → artefactos.
- SQLite local; prefijos master_, fs_, ml_. Originales conservados.
- FS didáctica, no plataforma completa de feature store.
- ML clásico end-to-end como núcleo obligatorio.
- Preparación de entorno obligatoria en Parte B de S0, no en anexos.
- Estadísticas y costes ampliados en consulta opcional.
- No depender de GPU ni asumir disponibilidad en la prueba cloud.

## Ajustes del 08/11/2026
- **Alcance:** IA generativa y relacionado pasa a **opcional**: red neuronal, LLM abierto, RAG,
  LLMOps/IAOps/AgentOps. MCP y agentes siguen fuera del curso.
- **Docker y Kubernetes sin instalación local:** se trabajan en Codespaces (docker, kind, kubectl).
  Docker Desktop local es opcional. GKE no es requisito (ver `03-Entorno/guias/docker-y-kubernetes-sin-instalacion-local.md`).
- **Orquestación con GitHub Actions** como hilo didáctico: primer workflow en S2 (construir imagen),
  pipeline completo en S5 (pruebas, construcción, publicación y despliegue).
- **S4 rediseñada:** pasa a «Orquestación y CI/CD con GitHub Actions» (núcleo). S5 se centra en versionado, deriva,
  monitoreo y rollback. El LLM abierto queda como sesión extra opcional (`06-Modulo-LLMs/`).
- **Hilo de migración de on-premise a GCP:** lo local (SQLite, archivos, Docker, MLflow) en S1 y S2 hace de on-premise simulado;
  S3 migra a GCP (Cloud Storage, BigQuery, Secret Manager, Artifact Registry, Cloud Run). El laboratorio de Kubernetes pasa a «si hay tiempo».
- **MLflow en el núcleo, versión ligera:** seguimiento en S1, carga del modelo y firma como contrato en S2,
  registro desde el workflow en S4, registro de modelos con alias y rollback en S5. Backend SQLite y artefactos en carpeta local.
- **S0:** Parte A 25 min, pausa 15, Parte B 70, cierre 10 (las slides son la referencia).

## Pendiente
1. Seleccionar y licenciar dataset y caso definitivo.
2. Fijar calendario y fechas; resolver incoherencias del sílabo original.
3. Elegir versiones y probar instalaciones por sistema operativo (local: Git, VS Code, Miniconda, SQLite, gcloud).
4. Implementar scripts, entornos, notebooks, API, workflows y pruebas.
5. Decidir si se imparte la sesión extra opcional de LLMs abiertos y en qué fecha; elegir motor y modelo.
6. Crear y validar el Codespace del curso (docker, kind, kubectl); revisar cuota gratuita vigente.
7. Definir autenticación de GitHub Actions con GCP (Workload Identity Federation, sin claves en el repo).
8. Validar cloud, accesos, costes y limpieza.
9. **Fusionar `develop` en `main` antes de S0** y subir los commits a GitHub (requiere instalar el Claude GitHub App o hacerlo desde tu PC).
10. Probar la presentación de S0 en Google Meet, otros navegadores y proyector (ya probada en Chromium).
11. Cifras de MLOps para la slide 5: no se pudieron verificar fuentes primarias (arxiv.org y datatalks.club fuera de la red de la sesión). Candidatas a comprobar: Naming the Pain in ML-Enabled Systems Engineering (arXiv 2406.04359, menos de 40 % de los modelos en producción se monitorean), encuesta DataTalks.Club 2025–2026 (30 % no monitorea; 7 % con MLOps avanzado; muestra autoseleccionada) y Gartner (54 % de modelos pasan de piloto a producción). Hasta verificarlas no están en las slides.
11b. MLflow: fijar la versión (las etapas del registro están en desuso a favor de alias; comprobarlo), decidir si reemplaza o convive con `joblib`+JSON, y validarlo en Codespaces y en un workflow.
12. Migración a GCP: definir el proyecto por alumno o compartido y el control de costes; probar SQLite → Cloud Storage → BigQuery; escribir scripts de exportación, carga y validación (ver `03-Entorno/guias/migracion-on-premise-a-gcp.md`).
13. Rúbrica y formato de la evaluación final (`08-Evaluacion-Final` está vacío).
14. Módulos opcionales: `05-Modulo-Redes-Neuronales` y `06-Modulo-LLMs` en la raíz son su ubicación definitiva (resuelto); falta el contenido de ambos.

## Evaluación propuesta
Conservar 20 % conocimiento, 40 % desempeño y 40 % producto por unidad,
sujeto a validación institucional. Los avances alimentan las evidencias acumulativas.
