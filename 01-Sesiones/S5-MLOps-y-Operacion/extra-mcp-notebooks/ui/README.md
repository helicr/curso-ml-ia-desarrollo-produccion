# Interfaz web del extra de S5: dos servidores MCP y un LLM

Una página local (`http://127.0.0.1:8095`) que arranca **los dos servidores MCP** de `../fuentes/` (`mcp_datos.py` y `mcp_modelo.py`) y los une con un LLM. Solo escucha en tu equipo, no usa Internet ni CDNs y no modifica los servidores ni los notebooks.

**Diapositivas del laboratorio** (paso a paso, con capturas reales de cada pestaña): [`index_slides.html`](index_slides.html); se regeneran con `python generar_slides.py`.

| Pestaña | Qué hace |
|---|---|
| Cliente | Lista de clientes con su probabilidad y tramo; medidor, «qué empuja la cifra» (`por_que`) y ficha de datos. Cada bloque dice qué servidor y herramienta lo produjo. |
| ¿Y si…? | Las 13 variables del cliente con deslizadores y la probabilidad en vivo (`predecir_variables`). Mover una variable no es un cliente real y la relación no es causal. |
| Pregunta | Chat con el LLM (máximo 5 pasos). Cada respuesta lleva las llamadas a herramientas como chips desplegables. Los números salen de las herramientas, no del LLM. |
| Explorador MCP | Formulario generado desde el `inputSchema` de cada herramienta y «SQL con vigilancia» con 8 ataques de ejemplo y la capa que los frena. |
| Modelo | Versiones y AUC, promover / volver con diálogo propio y qué versión responde antes y después. |

La **traza MCP** (panel lateral) muestra todas las llamadas en vivo. La probabilidad es la de **volver a comprar en 90 días**: alta = buena noticia.

## Arrancar

Entorno del curso (`env-ia-mlops`, con `mcp==1.30.0`, `fastapi`, `uvicorn`, `httpx`, `mlflow`) y, desde S1, `curso.db` y el modelo registrado en `04-Proyecto-Base`.

Windows, cmd:
```
cd 01-Sesiones\S5-MLOps-y-Operacion\extra-mcp-notebooks\ui
python -m uvicorn app:app --port 8095
```
PowerShell: igual (`python -m uvicorn app:app --port 8095`). También vale `python app.py`.

Codespace / Linux: lo mismo desde la carpeta `ui`, y abre el puerto 8095 reenviado. Allí la página se sirve con otro nombre de host, así que admítelo antes de arrancar: `export CURSO_UI_HOSTS="*.app.github.dev"` (Codespace: **sin verificar**, solo se ha probado en Windows).

Si el modelo no tiene alias `champion`, la interfaz lo avisa y ofrece «Promover la vN a champion» con un botón: no lo hace sola.

## Variables de entorno (todas opcionales)

`MCP_PROYECTO` (carpeta 04-Proyecto-Base), `CURSO_DB`, `CURSO_MLFLOW_URI`, `CURSO_LLM_URL` (por defecto `http://127.0.0.1:11434/v1`), `CURSO_LLM_MODELO` (por defecto `qwen2.5:0.5b`), `GCP_PROJECT` y `BQ_DATASET` (solo modo BigQuery), `CURSO_UI_PUERTO`, `CURSO_UI_HOSTS`. La URL y el modelo del LLM también se cambian en «Ajustes del LLM».

## LLM

Cualquier servidor con `/v1/chat/completions` y herramientas. Con Ollama: `ollama serve` y `ollama pull qwen2.5:0.5b`. El curso usa Qwen2.5-3B-Instruct Q4 en el puerto 11435 (cámbialo en Ajustes). `qwen2.5:0.5b` es débil con herramientas y se equivocará. Sin LLM, la pestaña Pregunta lo dice y el resto sigue funcionando; no hay reglas que finjan inteligencia.

## BigQuery

El conmutador reinicia solo el servidor de datos. Exige `GCP_PROJECT` (o el campo del diálogo) y credenciales (`gcloud auth application-default login`); si faltan, error claro y se queda en SQLite. **Sin verificar con un proyecto real** (solo con un conector falso). No uses el proyecto de tu trabajo.

## Pruebas

Desde `extra-mcp-notebooks`: `python -m pytest ui/pruebas -q`. Usan la aplicación y los servidores reales, un LLM de guion y, si responde, Ollama real (sin exigir acierto). Si no existe el alias `champion`, lo ponen y al terminar dejan el registro como lo encontraron. `ui/pruebas/capturar.py` recorre la interfaz con Playwright y guarda capturas (`--promover` escribe en el registro).
