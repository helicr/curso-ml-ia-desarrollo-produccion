# Extra de S5: dos servidores MCP, solo con notebooks

Construyes, sin salir de Jupyter, **dos servidores MCP** y un cliente que los usa:

| Notebook | Qué construyes | Qué aprendes |
|---|---|---|
| `00_preparar_entorno.ipynb` | Nada: comprueba datos, modelo y (opcional) BigQuery | Qué necesita el extra |
| `01_mcp_datos_sqlite_y_bigquery.ipynb` | `mcp-datos-master`: un LLM consulta la capa *master*, **en SQLite o en BigQuery** | Herramientas con nombre, SQL libre **vigilado**, defensa en capas, dos conectores con la misma interfaz y cómo comprobar que dan lo mismo |
| `02_mcp_modelo_prediccion.ipynb` | `mcp-modelo-retencion`: el modelo dentro del MCP; pasas un cliente y devuelve la predicción | Publicar un modelo como herramienta, cargarlo **por alias** (`@champion`), paridad con el modelo cargado a mano, rollback sin reiniciar, errores |

**Duración:** unos 60-75 minutos (estimado, sin medir con alumnado). **Diapositivas:** `index.html` (se abre desde el índice de S5).

> La probabilidad del modelo es la de **volver a comprar en 90 días**: alta = buena noticia. No es un riesgo de abandono.

## Cómo se usa

1. Entorno del curso (`env-ia-mlops`) y, desde `04-Proyecto-Base`, los datos y el modelo de S1: `python -m ia_mlops.pipeline` y `python -m ia_mlops.explotacion` (crea `fs_produccion`).
2. Abre `00_preparar_entorno.ipynb` y ejecútalo entero: instala `mcp==1.30.0` (`requisitos-extra-mcp.txt`) y comprueba todo.
3. Sigue con el 01 y el 02. Cada notebook **escribe sus servidores** en `_trabajo/` (con `%%writefile`) y los lanza como proceso aparte, como haría VS Code.

El código de los servidores vive en `fuentes/` (una sola fuente; los notebooks lo llevan copiado y una prueba comprueba que son idénticos). `construir_notebooks.py` regenera los notebooks (`--ejecutar` los ejecuta y guarda las salidas).

## BigQuery (opcional)

SQLite funciona sin nada más. Para el segundo conector hace falta **un proyecto de Google Cloud tuyo** y credenciales:

```
gcloud auth application-default login
gcloud config set project TU_PROYECTO
export GCP_PROJECT=TU_PROYECTO            # cmd de Windows: set GCP_PROJECT=TU_PROYECTO
```

El notebook sube las cuatro tablas *master* (22 000 filas, ~1 MB) a un dataset `curso_master` y **lo borra al final** (`BORRAR_DATASET`). **No uses el proyecto de tu trabajo.**

## Qué está probado y qué no (26/11/2026)

| Qué | Estado |
|---|---|
| Notebooks 00, 01 y 02 ejecutados de principio a fin en un portátil con Windows (Python 3.11, `mcp` 1.30.0): 0 errores, salidas guardadas | **Probado** |
| 38 pruebas (`pruebas/test_servidores_y_notebooks.py`): vigilancia del SQL (incluye 13 entradas rechazadas), solo lectura de SQLite, herramientas contra una base de juguete, notebooks ejecutados e idénticos a las fuentes | **Probado** |
| Conector de **BigQuery**, en Cloud Shell con la cuenta del curso (Python 3.12.3): las 7 llamadas dan lo mismo que con SQLite; con `maximum_bytes_billed=1` BigQuery responde «Query exceeded limit for bytes billed: 1. 20971520 or higher required»; dataset temporal creado y borrado, sin restos | **Probado a mano** con un script equivalente al notebook (no con el propio notebook): las celdas de BigQuery del 01 salen «saltada» en el archivo guardado |
| Vigilancia del SQL | Una expresión regular **no es un analizador de SQL**: se probó con los ataques del notebook y los de las pruebas, no es una garantía. Por eso hay más capas (solo lectura, topes) |
| Notebooks en un Codespace, y los servidores conectados a VS Code / Copilot (JSON de ejemplo en los notebooks) | **Sin verificar** |
| El LLM eligiendo bien la herramienta | **Sin verificar**: aquí el cliente llama a las herramientas a mano; no se probó con un LLM |

## Hallazgos del ensayo (para quien dé la clase)

- En Jupyter, `stdio_client` falla si no se le da `errlog=` (el `sys.stderr` del kernel no tiene `fileno`). El cliente del notebook lo resuelve con un archivo.
- Las seis versiones de `retencion-90d` salen con el mismo AUC (se entrenaron con los mismos datos): el rollback cambia la **versión** que responde, no la cifra.
- «¿Y si…?»: con el cliente de ejemplo, la probabilidad **sube** con la recencia (0,7533 con 5 días, 0,8965 con 365). Es lo contrario de la intuición; **no se ha investigado por qué** y no es causal. Es un buen punto de debate.
- Una consulta repetida en BigQuery sale de la caché y no se factura: para probar el tope de bytes hay que lanzar una consulta nueva.
- Si no hay `@champion`, el notebook 02 promueve la última versión (lo dice en su salida y explica cómo quitarlo).

## Relación con el resto de S5

El laboratorio de agentes (`../laboratorio-agentes/`) ya usa un servidor MCP (`mcp-retencion`) con un LLM local. Este extra es la versión **desde cero y con notebooks**: tú escribes el servidor, el cliente y las pruebas.
