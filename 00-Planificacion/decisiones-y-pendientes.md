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
- **Instalación solo para Windows:** guía interactiva (`03-Entorno/guia-instalacion/`) con comandos para copiar y dos scripts equivalentes, en CMD y en PowerShell
  (`03-Entorno/scripts/instalar_entorno.cmd` y `.ps1`), que instalan con winget y verifican. Ruta sin instalación (Codespaces y Cloud Shell) para equipos sin permisos.
- **Caso transversal: Online Retail II** (UCI, CC BY 4.0, verificado). Pregunta: ¿el cliente vuelve a comprar en 90 días? Capas RAW → MASTER → FS → ML construidas y probadas con el dato completo.
- **Los pipelines son cuadernos; el paquete Python es su traducción.** Proyecto con la estructura de Cookiecutter Data Science (`04-Proyecto-Base/`, paquete `ia_mlops`).
  Pruebas de equivalencia cuaderno = paquete = `.py` de jupytext (tablas y métricas idénticas).
- **Nombres de los entornos de conda:** `env-ia-mlops` (núcleo obligatorio) y `env-ia-opcional` (red neuronal y LLM, opcional).
- **S0:** Parte A 25 min, pausa 15, Parte B 70, cierre 10 (las slides son la referencia).
- **Caso de la tarea (09/11/2026):** los alumnos repiten la receta (RAW → MASTER → FS → ML → entrenamiento, con cuadernos y su traducción a `.py`) sobre **Bank Marketing** (UCI, CC BY 4.0), decidido el 09/11/2026; **Default of Credit Card Clients** queda como referencia para investigar por su cuenta.
  Es el «caso propio» que acompaña a los alumnos de S1 a S5. Los datos están en `02-Proyecto-Transversal/datos/` (ver su `LEEME.md`). Olist queda descartado. Detalle en `02-Proyecto-Transversal/enunciado/README.md`.

## Pendiente
1. ~~Seleccionar y licenciar dataset y caso definitivo.~~ Resuelto el 09/11/2026: caso del instructor = Online Retail II; tarea = Default of Credit Card Clients o Bank Marketing (UCI, CC BY 4.0). Quedan los puntos 11f y 15.
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
11a. Instalación en Windows: la lógica de los dos scripts está probada con un winget falso (`03-Entorno/scripts/pruebas/`: PowerShell 7 en Linux y CMD en Wine); falta probarlos con los comandos de la guía en un equipo Windows limpio (10 y 11); confirmar los identificadores de winget
    (Git.Git, Microsoft.VisualStudioCode, Anaconda.Miniconda3, DBBrowserForSQLite.DBBrowserForSQLite, Google.CloudSDK), los de las extensiones y la ruta de Miniconda;
    revisar el enlace de descarga de Miniconda; validar el comportamiento en equipos corporativos con restricciones.
11b. MLflow: fijar la versión (las etapas del registro están en desuso a favor de alias; comprobarlo), decidir si reemplaza o convive con `joblib`+JSON, y validarlo en Codespaces y en un workflow.
11c. Términos de servicio de Anaconda: el Miniconda real bloquea `conda env create` hasta aceptarlos. Decidir entre (a) la configuración solo conda-forge de la guía,
    (b) aceptar los términos (revisar licencia de la organización) o (c) cambiar a Miniforge.
11d. MLflow 3 + scikit-learn: `log_model` de un `RandomForest` falla por defecto (skops). Elegir qué enseñar en S1: `skops_trusted_types=['sklearn.tree._tree.Tree']`
    o `serialization_format='cloudpickle'`; ambas probadas. Ver `03-Entorno/VALIDACION.md`.
11e. Crear y probar `env-ia-mlops` en Windows (hoy solo resuelve con `--dry-run` y se probó en Linux); crear `environment-opcional.yml`.
11f. ~~Dataset de la TAREA: Olist sin licencia confirmada.~~ Resuelto el 09/11/2026: se descarta Olist y la tarea usa Default of Credit Card Clients o Bank Marketing (UCI, CC BY 4.0, leído en las fichas oficiales; ver `02-Proyecto-Transversal/dataset-candidatos.md`).
12. Migración a GCP: definir el proyecto por alumno o compartido y el control de costes; probar SQLite → Cloud Storage → BigQuery; escribir scripts de exportación, carga y validación (ver `03-Entorno/guias/migracion-on-premise-a-gcp.md`).
13. Rúbrica y formato de la evaluación final (`08-Evaluacion-Final` está vacío).
14. Módulos opcionales: `05-Modulo-Redes-Neuronales` y `06-Modulo-LLMs` en la raíz son su ubicación definitiva (resuelto); falta el contenido de ambos.
15. **Datos de la tarea:** la copia (Bank Marketing y Default, con `SHA256SUMS` y atribución CC BY 4.0) ya está en `02-Proyecto-Transversal/datos/` desde el 09/11/2026. Falta, si hace falta, un script de descarga desde UCI (el proxy de la sesión bloquea `archive.ics.uci.edu`). El perfilado y el modelo base rápido están en `02-Proyecto-Transversal/verificacion-datos-tarea/`.
16. **Base de referencia de la tarea:** no existe. Para Bank Marketing (caso de los alumnos; y, si hay tiempo, Default como referencia) hay que construir y probar RAW → MASTER → FS → ML, un modelo base y las pruebas, como se hizo con Online Retail II,
    para poder dar un «resultado de referencia» y detectar errores antes que los alumnos. Orden de magnitud ya medido: Default, AUC de prueba 0,71–0,76.
17. **Reglas de la tarea:** ya decidido que el caso es Bank Marketing (09/11/2026); falta fechar los avances. Medido: Bank Marketing partido por orden de filas tiene una deriva extrema (AUC de prueba 0,51–0,58 sin `duration`);
    decidir si se parte aleatoriamente (optimista), por orden de filas (ejercicio de deriva para S5) o si queda como opción avanzada. `duration` hay que excluirla (ver el enunciado).
18. **`xlrd` en el entorno:** el `.xls` de Default no se lee con `env-ia-mlops` (trae `openpyxl`, no `xlrd`). Se entrega ya un CSV derivado (`convertir_xls_a_csv.py` lo regenera), así que no bloquea; queda decidir si se añade `xlrd` a `03-Entorno/conda/environment.yml` (y se revalida el entorno). El enunciado todavía lo presenta como hallazgo abierto.

## Evaluación propuesta
Conservar 20 % conocimiento, 40 % desempeño y 40 % producto por unidad,
sujeto a validación institucional. Los avances alimentan las evidencias acumulativas.
