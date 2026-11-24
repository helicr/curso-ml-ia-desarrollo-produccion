# Configurar el repositorio para los workflows del agente

Es lo mismo que en S4. Antes de nada, haz lo de **[`S4-Orquestacion-y-CI-CD/laboratorio-produccion-e2e/CONFIGURAR-REPOSITORIO.md`](../../S4-Orquestacion-y-CI-CD/laboratorio-produccion-e2e/CONFIGURAR-REPOSITORIO.md)** (ruta desde la raíz del repositorio: `01-Sesiones/S4-Orquestacion-y-CI-CD/laboratorio-produccion-e2e/CONFIGURAR-REPOSITORIO.md`), una sola vez:

- **Activar las Actions** si es un *fork* (apartado 0).
- **El *environment* `produccion` con revisores** (apartado 1): `agente-nueva-version.yml` usa **el mismo** que el modelo. Si ya lo hiciste en S4, no hay que hacer nada.
- **Permiso para que las Actions abran *pull requests*** (apartado 2): lo necesitan el último trabajo de `agente-nueva-version.yml` y `agente-rollback.yml`. Igual que en S4.
- **Visibilidad del paquete en GHCR** (apartado 3): la primera publicación crea el paquete `interfaz-agente`, que es **otro paquete** que `retencion-api`: si quieres descargarlo sin iniciar sesión, hay que ponerlo público también (**Packages** › `interfaz-agente` › **Package settings** › **Change visibility**). El paquete `interfaz-agente` se publicó de verdad el 23/11/2026 (run nº 45069539053, etiqueta `v2-68d30075097172de`); poner ese paquete **público** y descargarlo sin iniciar sesión: **sin verificar**.

## Los cuatro workflows

Cópialos a `.github/workflows/` de tu repositorio, sin tocarlos:

| Archivo de esta carpeta | Dónde va en tu repositorio | Para qué |
|---|---|---|
| `agente-ci.yml` | `.github/workflows/agente-ci.yml` | Pruebas de los niveles 1 a 3 con el LLM falso y humo del compose; en cada push a `lab/agente/**` |
| `agente-evaluar.yml` | `.github/workflows/agente-evaluar.yml` | Las 25 preguntas de oro con Ollama dentro del runner; a mano o push a `lab/agente-evaluar/**` |
| `agente-nueva-version.yml` | `.github/workflows/agente-nueva-version.yml` | Evaluar → construir → aprobar y publicar → PR de la referencia; push a `lab/agente-version/**` |
| `agente-rollback.yml` | `.github/workflows/agente-rollback.yml` | PR que restaura la referencia anterior; push a `lab/agente-rollback/**` |

## Lo nuevo respecto a S4

1. **Los workflows usan scripts de esta carpeta** (`aplicar_prompt.py`, `historial_agente.py`, `resumen_evaluacion.py` y `prompts/sistema-v2.txt`). Por eso tu repositorio debe contener también la carpeta `01-Sesiones/S5-MLOps-y-Operacion/laboratorio-agentes/` (con un *fork* del repositorio del curso ya está). Si la mueves, cambia la variable `LAB` de los workflows.
2. **No hace falta ningún secreto**: el LLM es local (Ollama dentro del runner) y todo lo demás usa el `GITHUB_TOKEN` de cada ejecución.
3. **La evaluación con el LLM real es lenta**: el trabajo tiene un tiempo límite de 120 a 150 minutos a propósito. En un portátil de 14 hilos, las 25 preguntas tardaron unos 14 minutos; en un runner estándar de GitHub, la evaluación del run nº 45067018776 tardó **780 s** (el run entero, 15 min 30 s) y usó unos **4 GB** de 16. Un repositorio **público** usa minutos de Actions gratuitos; en uno **privado** cuentan contra tu cuota.
4. **La primera evaluación descarga unos 2 GB** (el modelo); las siguientes usan la caché de Actions (que GitHub borra si lleva sin usarse unos días).
5. **El rollback no mueve MLflow de verdad** (comprobado en Actions el 23/11/2026, run nº 45278456252): el almacén de MLflow del workflow es efímero (vive en el runner). El *pull request* cambia lo que está en git; los alias de MLflow se mueven en el servidor donde se registraron, que en este laboratorio no existe de forma permanente. Está explicado en la cabecera de `agente-rollback.yml`.
6. Los nombres de las ramas de ensayo **eligen el escenario** (`lab/agente-version/igual`, `…/prompt-nuevo`, `…/rechazo`), como en S4. Un *run* de `agente-nueva-version.yml` esperando aprobación **bloquea** al siguiente del mismo grupo (también al rollback): cancélalo o apruébalo.

## Comprobación de que todo está listo

| Comprobación | Debes ver |
|---|---|
| Actions habilitadas | Los cuatro workflows «Agente · …» aparecen a la izquierda en la pestaña **Actions** |
| *Environment* y permiso de PR | Los de S4 (apartados 1 y 2 de su guía) |
| Primera ejecución | Un push a `lab/agente/ci` lanza «Agente · CI»: dos trabajos en verde (run nº 45067003924, **4 min 7 s**) |
