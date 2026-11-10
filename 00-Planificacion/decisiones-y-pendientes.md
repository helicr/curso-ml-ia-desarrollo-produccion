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
- **Caso de la tarea (09/11/2026):** los alumnos repiten la receta (RAW → MASTER → FS → ML → entrenamiento, con cuadernos y su traducción a `.py`) sobre **Bank Marketing**
  (UCI, CC BY 4.0; confirmado el 10/11/2026), con **Default of Credit Card Clients** como referencia opcional. Es el «caso propio» que acompaña a los alumnos de S1 a S5. Olist queda descartado. Detalle en `02-Proyecto-Transversal/enunciado/README.md`.

## Pendiente
1. ~~Seleccionar y licenciar dataset y caso definitivo.~~ Resuelto el 09/11/2026: caso del instructor = Online Retail II; tarea = Bank Marketing (UCI, CC BY 4.0), con Default of Credit Card Clients como referencia opcional (confirmado el 10/11/2026).
2. Fijar calendario y fechas; resolver incoherencias del sílabo original.
3. Elegir versiones y probar instalaciones por sistema operativo (local: Git, VS Code, Miniconda, SQLite, gcloud).
4. Implementar scripts, entornos, notebooks, API, workflows y pruebas.
5. Decidir si se imparte la sesión extra opcional de LLMs abiertos y en qué fecha; elegir motor y modelo.
6. Validar el Codespace del curso (docker, kind, kubectl); revisar cuota gratuita vigente. El 10/11/2026 se escribió `.devcontainer/devcontainer.json` (Python 3.11 y Docker en Codespaces; también una copia para el proyecto en `04-Proyecto-Base/.devcontainer/`) **sin abrir ningún Codespace**: hay que probarlo, y añadir `kind` y `kubectl` para S3.
7. Definir autenticación de GitHub Actions con GCP (Workload Identity Federation, sin claves en el repo).
8. Validar cloud, accesos, costes y limpieza.
9. **Fusionar `develop` en `main` antes de S0** y subir los commits a GitHub (requiere instalar el Claude GitHub App o hacerlo desde tu PC).
10. Probar la presentación de S0 en Google Meet, otros navegadores y proyector (ya probada en Chromium).
11. Cifras de MLOps para la slide 5: no se pudieron verificar fuentes primarias (arxiv.org y datatalks.club fuera de la red de la sesión). Candidatas a comprobar: Naming the Pain in ML-Enabled Systems Engineering (arXiv 2406.04359, menos de 40 % de los modelos en producción se monitorean), encuesta DataTalks.Club 2025–2026 (30 % no monitorea; 7 % con MLOps avanzado; muestra autoseleccionada) y Gartner (54 % de modelos pasan de piloto a producción). Hasta verificarlas no están en las slides.
11a. Instalación en Windows: la lógica de los dos scripts está probada con un winget falso (`03-Entorno/scripts/pruebas/`: PowerShell 7 en Linux y CMD en Wine); falta probarlos con los comandos de la guía en un equipo Windows limpio (10 y 11); confirmar los identificadores de winget
    (Git.Git, Microsoft.VisualStudioCode, Anaconda.Miniconda3, DBBrowserForSQLite.DBBrowserForSQLite, Google.CloudSDK), los de las extensiones y la ruta de Miniconda;
    revisar el enlace de descarga de Miniconda; validar el comportamiento en equipos corporativos con restricciones.
11c. Términos de servicio de Anaconda: el Miniconda real bloquea `conda env create` hasta aceptarlos. Decidir entre (a) la configuración solo conda-forge de la guía,
    (b) aceptar los términos (revisar licencia de la organización) o (c) cambiar a Miniforge.
11d. ~~MLflow 3 + scikit-learn: `log_model` de un `RandomForest` falla por defecto (skops).~~ Resuelto: el proyecto guarda con `serialization_format='cloudpickle'` (`04-Proyecto-Base/ia_mlops/modeling/train.py`; lo explica el README de S1). Su riesgo se trata en el punto 20.
11f. ~~Dataset de la TAREA: Olist sin licencia confirmada.~~ Resuelto el 09/11/2026: se descarta Olist y la tarea usa Bank Marketing (con Default of Credit Card Clients como referencia opcional; UCI, CC BY 4.0, leído en las fichas oficiales; ver `02-Proyecto-Transversal/dataset-candidatos.md`).
11e. Crear y probar `env-ia-mlops` en Windows (hoy solo resuelve con `--dry-run` y se probó en Linux); crear `environment-opcional.yml`.
11b. MLflow: fijar la versión (las etapas del registro están en desuso a favor de alias; comprobarlo), decidir si reemplaza o convive con `joblib`+JSON, y validarlo en Codespaces y en un workflow.
12. Migración a GCP: definir el proyecto por alumno o compartido y el control de costes; probar SQLite → Cloud Storage → BigQuery; escribir scripts de exportación, carga y validación (ver `03-Entorno/guias/migracion-on-premise-a-gcp.md`).
13. Rúbrica y formato de la evaluación final (`08-Evaluacion-Final` está vacío).
14. Módulos opcionales: `05-Modulo-Redes-Neuronales` y `06-Modulo-LLMs` en la raíz son su ubicación definitiva (resuelto); falta el contenido de ambos.
15. ~~Datos de la tarea.~~ Resuelto el 09/11/2026: la copia está en `02-Proyecto-Transversal/datos/` (CC BY 4.0, atribución y procedencia en `LEEME.md`, huellas en `SHA256SUMS`; `.gitattributes` evita que Git cambie los saltos de línea). Ya no hace falta un script de descarga; el proxy sigue bloqueando `archive.ics.uci.edu`, así que solo haría falta si se prefiere que cada alumno descargue de UCI.
16. **Base de referencia de la tarea:** no existe. Para Bank Marketing hay que construir y probar RAW → MASTER → FS → ML, un modelo base y las pruebas, como se hizo con Online Retail II,
    para poder dar un «resultado de referencia» y detectar errores antes que los alumnos. Orden de magnitud ya medido (una partición y una semilla): AUC de prueba ≈0,79–0,80 con partición aleatoria y sin `duration`, y 0,51–0,58 por orden de filas.
17. ~~Reglas de la tarea.~~ Resuelto el 10/11/2026: Bank Marketing para todos; `duration` fuera del modelo; partición aleatoria estratificada de S1 a S4, dejando escrito que es optimista; y el mismo modelo evaluado por orden de filas en S5 como ejercicio de deriva (detalle en `02-Proyecto-Transversal/enunciado/README.md`). Falta fechar los avances (punto 2).
18. ~~`xlrd` en el entorno.~~ Resuelto: se entrega `default_of_credit_card_clients.csv`, derivado del `.xls` con un solo encabezado y verificado igual (`convertir_xls_a_csv.py` lo regenera). `env-ia-mlops` sigue sin `xlrd` a propósito.

19. **S2, lo que falta por probar:** el Codespace (punto 6), `docker build` en un equipo propio, los comandos de la sesión en Windows, y la tarea con Bank Marketing (ruta B; ver 16). Pendiente menor: `starlette` avisa de que `TestClient` pasará a usar `httpx2`; las pruebas lo silencian con `filterwarnings` y hay que revisarlo al actualizar versiones.
20. **S2, decisiones de diseño a revisar con el grupo:** `cloudpickle` en el modelo MLflow (riesgo de ejecución de código al cargar; se documenta y en S5 se enlaza con la cadena de confianza), imagen de 826 MB (mlflow-skinny, scikit-learn, pandas y scipy), y que el contrato de la API se escribe en `esquemas.py` y se vigila contra la firma al arrancar en vez de generarse automáticamente.
21. **Guía de Codespaces para el alumnado (10/11/2026):** `03-Entorno/guia-codespaces/` (24 diapositivas + versión en texto + PDF). Se hizo con el diseño y los comandos del bloque 4 de S2, y con la documentación de GitHub para cuota, puertos y VS Code de escritorio. **Pendiente (antes de la clase):** abrir un Codespace real de la rama `develop`, ejecutar el bloque 4 y las rutas de interfaz de la guía (crear, PORTS, Export changes to a branch, conexión desde VS Code), y corregir `generar.py` si algo difiere. Revisar la cuota vigente (Free 120 h-núcleo/mes, Pro y Student Pack 180) y que las cuentas de estudiante tengan el Student Developer Pack. Para S3: añadir `kind` y `kubectl` al `devcontainer.json` y ampliar la guía.
22. **Autoestudio de contenedores antes de S2 (10/11/2026):** `01-Sesiones/S2-API-y-Docker/contenedores/` (dos presentaciones, guía práctica de nueve ejemplos, laboratorio de cinco roturas y PDF). Se decidió como trabajo previo en el Codespace, sin tocar la agenda de S2; los tiempos (≈60 min los ejemplos 1–6, ≈97 min todos, ≈34 min el laboratorio) son estimaciones sin cronometrar. Las salidas son de Docker real en GitHub Actions. **Pendiente (antes de la clase):** ejecutar `ejecutar.py --salida salidas-codespace.json` en un Codespace de verdad, comparar con `salidas-reales.json` y quitar la etiqueta «todavía no se han ejecutado en un Codespace del curso» si coincide; cronometrar con un par de personas; y decidir si el autoestudio es obligatorio o recomendado (hoy se presenta como recomendado, con los ejemplos 1–6 como mínimo). Lo que dicen las diapositivas de Cloud Run sale solo de la documentación de Google: se comprobará en S3 con un despliegue real.
23. **Material del alumnado para su caso propio (10/11/2026):** `02-Proyecto-Transversal/alumno/` (hoja, plantilla de avance y rúbrica) y la presentación «Tu caso de S1 a S5» en `01-Sesiones/S1-Datos-y-Entrenamiento/slides/caso-propio/` (12 diapositivas + 4 PDF). Todas las cifras son recuentos del CSV, ninguna de modelo. **Para decidir:**
    - **Dónde se presenta.** No está en la agenda de S1. Propuesta: 5 min en «Entrega y cierre» (diapositivas 18–20 de la presentación de S1) y lectura en casa; no cambia los tiempos del guion. Sin decidir.
    - **Los topes de la rúbrica de avance** (`duration` en el modelo → técnica ≤ 15; solo capturas → reproducibilidad ≤ 8; sin cita de la fuente → reproducibilidad ≤ 15; credenciales en el repositorio → técnica ≤ 25; presentar como ejecutado lo que no se ejecutó → análisis ≤ 20; partición aleatoria sin decir que es optimista → análisis ≤ 25) son una propuesta mía que sigue el patrón de las rúbricas de S1 y S2. Revisarlos.
    - **Pesos y nombres.** Las rúbricas pesan 20/40/40 en reproducibilidad, técnica y análisis, mientras que la «Evaluación propuesta» de abajo habla de 20 % conocimiento, 40 % desempeño y 40 % producto. Falta fijar la correspondencia (el índice de S1 decía lo segundo con los pesos de lo primero; se corrigió a los nombres reales de la rúbrica). Tampoco está definido el peso de cada avance en la nota final ni la rúbrica de la entrega final (punto 13).
    - **Avances 3 y 4.** Su técnica se limita a lo que dice el programa; se concretarán al preparar S3 y S4.
    - **Las cifras de referencia son públicas.** `02-Proyecto-Transversal/enunciado/README.md` y `verificacion-datos-tarea/salidas/modelo_base.txt` traen los AUC del instructor y el repositorio es público; `datos/LEEME.md` apunta a esa carpeta («Los números del perfilado»). Si no deben verlos los alumnos, hay que sacarlos del repositorio público o mover esos archivos a una rama o repositorio privado. El material nuevo de alumnos no los enlaza ni los repite (lo vigila una prueba).
    - **Sin probar:** que un alumno entienda la hoja sin ayuda (nadie la ha leído aún); el consejo de cambiar el nombre del paquete si se copia `04-Proyecto-Base/`; y la receta completa con Bank Marketing (punto 16).

## Evaluación propuesta
Conservar 20 % conocimiento, 40 % desempeño y 40 % producto por unidad,
sujeto a validación institucional. Los avances alimentan las evidencias acumulativas.
