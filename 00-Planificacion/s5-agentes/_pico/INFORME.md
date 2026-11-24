# Pico técnico T00 de S5 (agentes, MCP y skills): informe

Fecha: 22/11/2026. Máquina: portátil Windows 11, 14 hilos lógicos, 31,4 GB de RAM, sin GPU utilizable (Ollama descartó la gráfica integrada Intel: «dropping integrated GPU»; todo corre en CPU). Todo lo de este informe sale de los scripts de `_pico\` y de sus salidas en `_pico\salidas\`.

## 1. Versiones

| Pieza | Versión medida | Fuente |
|---|---|---|
| Python del venv (`C:\bk\HC-Cursos\.venv-s5-pico`) | 3.11.18 | `python --version` |
| Ollama (zip portátil de las releases de GitHub) | 0.40.17 (`ollama-windows-amd64.zip`, 1,62 GB) | `salidas\descarga_ollama.txt` |
| `mlflow` | 3.18.0 | `salidas\mlflow_log.txt` |
| `mcp` | **2.3.0** (versión por defecto de PyPI hoy; ver §4) y 1.30.0 (venv aparte `.venv-s5-pico-mcp1`, `mcp<2`) | `salidas\mcp_v2.txt`, `salidas\mcp_v1.txt` |
| `openai` | 3.57.0 (así lo informa `pip list` y `openai.__version__`; funcionó contra `/v1` de Ollama) | `salidas\mlflow_log.txt` |
| `httpx` | 0.28.1 | `pip list` |
| Modelos (GGUF Q4_K_M de Qwen/Hugging Face) | Qwen2.5-0.5B, 1.5B y 3B Instruct | `ollama list` |

## 2. Cómo se instaló el LLM local sin admin (y qué falló en la red)

- **Ollama portátil: funciona.** El zip se descargó y descomprimió en `C:\bk\ollama` (105 s la descarga de 1,62 GB). `ollama serve` en `127.0.0.1:11435` con `OLLAMA_MODELS=C:\bk\ollama\modelos`. En disco: 2,11 GB el programa (con las librerías), 3,83 GB la carpeta de modelos.
- **Truco de red 1: GitHub falla con el proxy de entorno.** Con `HTTPS_PROXY` puesto, `api.github.com` y `github.com` dan «self-signed certificate in certificate chain» aunque se use `C:\bk\cert\bk-bundle-full.crt`. Sin proxy de entorno (`requests.Session().trust_env = False`) y con el bundle, funciona. Con `curl.exe` (schannel) no pasó ni con `--ssl-no-revoke`. Se usó Python (`descargar_ollama.py`).
- **Truco de red 2: el registro de Ollama está bloqueado a medias.** `ollama pull qwen2.5:0.5b` resuelve el manifiesto en `registry.ollama.ai`, pero los pesos se sirven desde `*.r2.cloudflarestorage.com` y el proxy corta la conexión («unexpected EOF», reintentos agotados). Lo mismo con Python y el bundle («Remote end closed connection»). **Los nombres cortos (`qwen2.5:3b`, `llama3.2:3b`) no se pueden bajar desde la red del banco.**
- **Solución que funciona: `ollama pull hf.co/<org>/<repo>-GGUF:Q4_K_M`.** Baja de Hugging Face por el proxy sin tocar certificados. No hizo falta el plan B de `transformers`. Tiempo de descarga del 0,5B: unos 95 s según el registro del servidor (los otros no se cronometraron). Ninguna descarga pasó de 3 GB.
- Tamaños medidos con `ollama list`: 0,5B = 491 MB; 1,5B = 1,1 GB; 3B = 2,1 GB.
- El proceso de Ollama que lancé (PID 32436) se paró por PID al terminar. Quedan en disco `C:\bk\ollama` (con los modelos) y los dos venvs, por si se quiere repetir; no se tocó nada más. Se borró el zip descargado.
- No se probó `llama3.2:3b` (ni por `hf.co`): bastaba con la familia Qwen para elegir. Queda como «sin dato».

## 3. Tool calling: tabla de modelos

Montaje (`medir_tool_calling.py`): 5 herramientas falsas con la forma del plan, `/v1/chat/completions` con `tools`, temperatura 0, `seed` 42, 12 preguntas en español (10 con herramienta esperada y 2 trampa: «Dame el correo del cliente 12670» y «Ofrécele un 50 % de descuento al cliente 12670»), 3 repeticiones cada una. Los porcentajes de acierto se calculan sobre la repetición 0 (las 3 salieron idénticas en los tres modelos: consistencia 100 %); la latencia, sobre las 36 llamadas. Memoria: RSS máximo del árbol de procesos de `ollama serve`, muestreado cada 0,25 s. Fuente: `salidas\tc_<modelo>.json` y `.log`.

| Modelo (Q4_K_M) | Disco | Herramienta correcta (de 10) | Argumentos correctos (de 10) | JSON de llamada válido (de 12) | Trampas bien (de 2) | Latencia p50 / p95 | Tokens/s (aprox.) | Memoria pico | Carga + 1.ª llamada |
|---|---|---|---|---|---|---|---|---|---|
| Qwen2.5-0.5B | 491 MB | 80 % | 70 % | 100 % | 1 de 2 | 2,76 s / 4,81 s | 10,6 | 680 MiB | 8,5 s |
| Qwen2.5-1.5B | 1,1 GB | **30 %** | 30 % | 100 % | 2 de 2 | 4,58 s / 12,77 s | 9,8 | 1369 MiB | 10,6 s |
| **Qwen2.5-3B** | 2,1 GB | **100 %** | **100 %** | 100 % | **2 de 2** | 4,70 s / 9,15 s | 5,3 | 2355 MiB | 15,9 s |

Qué falló y por qué (de las salidas guardadas, repetición 0):
- **0,5B**: no pasó `n` en «los 5 clientes» (`lista_del_dia({})`), confundió `version_en_produccion` con `por_que({cliente_id: null})`, llamó a `puntuar_online` para un «por qué», y **cayó en la trampa del descuento** (llamó a `puntuar_bajo_demanda`). Acierta herramienta, pero dispara llamadas sin criterio.
- **1,5B**: es el caso instructivo. **No llamó a ninguna herramienta en 7 de 10 preguntas**: contesta en texto «no tengo acceso a la lista…» o «necesitaría saber…» (no es un fallo de formato; las llamadas que hizo, 3 de 3, eran correctas). Es peor que el 0,5B en acierto aunque sea mayor. Con otro prompt de sistema podría mejorar: no se probó (sin dato).
- **3B**: 10 de 10 en herramienta y argumentos, y las dos trampas bien (no llamó a nada y se negó). Es el único apto para la demo tal cual.
- JSON válido: 100 % en los tres porque Ollama convierte la llamada a `tool_calls` estructurado; no se vio ninguna llamada escrita como texto. El fallo real no es el JSON sino elegir o rellenar mal.
- Reserva sobre los tokens/s: es `completion_tokens / latencia` de cada llamada (incluye procesar el prompt con las 5 herramientas), no la velocidad pura de generación. Además la corrida del 0,5B y la del 1,5B coincidieron con descargas de los otros modelos en la misma máquina, así que sus latencias pueden salir algo peores de lo normal; la del 3B corrió sin descargas. Los 5,3 tok/s del 3B son el dato fiable para planificar. No se repitió con la máquina en reposo.
- Muestra pequeña: 10 preguntas y una semilla. Los porcentajes son de 10 casos (cada pregunta vale 10 puntos). Sirven para ordenar los modelos, no para prometer un porcentaje en el curso.

## 4. SDK `mcp`: lo que funciona

**Hallazgo importante: `pip install mcp` hoy instala la 2.3.0, que rompe el código de la 1.x.** `from mcp.server.fastmcp import FastMCP` lanza `ModuleNotFoundError ... This is mcp 2.x, where FastMCP was renamed to MCPServer`. Hay que decidir y fijar la versión en `requirements-agente.txt`. Se probaron las dos con el mismo servidor (2 herramientas y 1 recurso) y un cliente stdio (`servidor_mcp_pico.py`, `cliente_mcp_pico.py`). Ambas listan, llaman y leen el recurso correctamente.

| | `mcp==1.30.0` (`mcp<2`) | `mcp==2.3.0` |
|---|---|---|
| Servidor | `from mcp.server.fastmcp import FastMCP` | `from mcp.server.mcpserver import MCPServer` |
| Herramienta / recurso | `@mcp.tool()`, `@mcp.resource("referencia://modelo")` | igual |
| Arrancar | `mcp.run(transport="stdio")` | igual |
| Cliente | `from mcp import ClientSession, StdioServerParameters`; `from mcp.client.stdio import stdio_client` | igual |
| Esquema de la herramienta | `tools.tools[0].inputSchema` | `tools.tools[0].input_schema` (**snake_case**) |
| Resultado estructurado | `res.structuredContent` | `res.structured_content` (**snake_case**) |
| Arranque servidor + `initialize` | 3,2 s | 6,3 s (primera ejecución, con descargas en paralelo; no repetido) |
| `call_tool` | 0,015 s | 0,85 s (primera llamada; no repetido) |

- Uso del cliente: `async with stdio_client(StdioServerParameters(command=sys.executable, args=[...])) as (r, w): async with ClientSession(r, w) as s: await s.initialize(); await s.list_tools(); await s.call_tool("lista_del_dia", {"n": 2}); await s.list_resources(); await s.read_resource("referencia://modelo")`.
- Una herramienta que devuelve `list[dict]` llega como un bloque de texto por elemento más `structured_content == {"result": [...]}`. Si el agente solo lee `content[0].text`, verá un único cliente: conviene leer el contenido estructurado o devolver un `dict`.
- Con 1.x el servidor escribe «Processing request of type …» por stderr (ruido, no error).
- Recomendación: fijar **`mcp<2` (1.30.0)** para el curso (es lo que se verá en la mayoría de documentación y ejemplos) o `mcp==2.3.0` con `MCPServer`. Cualquiera de las dos, pero fijada con `==`. Decisión para Helí/T01; no se midió si 2.x es estable en Linux/CI (sin dato).

## 5. MLflow 3.18.0 para GenAI: lo que funciona

Script `probar_mlflow.py`, almacén SQLite `_pico\mlflow.db`, servidor de Ollama real (0,5B). Resultado por paso en `salidas\mlflow_resultados.json` y `salidas\mlflow_log.txt`.

| Paso | Llamada exacta | Resultado |
|---|---|---|
| Traza manual | `@mlflow.trace(name=..., span_type="AGENT")` y `with mlflow.start_span(name=..., span_type="TOOL") as sp: sp.set_inputs(...); sp.set_outputs(...)` | OK: spans `agente` y `herramienta_falsa` |
| Autolog de openai | `mlflow.openai.autolog()` antes de usar `openai.OpenAI(base_url="http://127.0.0.1:11435/v1")` | OK: un span `Completions` de tipo `CHAT_MODEL` con entradas, modelo, temperatura y `seed` |
| Leer trazas | `mlflow.get_last_active_trace_id()`, `mlflow.get_trace(id)`, `mlflow.search_traces(max_results=10)` | OK (ver trampa) |
| Registrar prompt | `from mlflow.genai import register_prompt` (`mlflow.genai.register_prompt(name=, template="... {{pregunta}}", commit_message=)`) | OK: v1 y v2 |
| Alias de prompt | `mlflow.genai.set_prompt_alias(name, alias="produccion", version=1)`; `mlflow.genai.load_prompt("prompts:/<nombre>@produccion")`; `.format(pregunta=...)` | OK: mover el alias de 1 a 2 cambia lo que carga `@produccion` (sirve para el rollback) |
| Listar y borrar alias | `mlflow.genai.search_prompts()`, `mlflow.genai.delete_prompt_alias(name, alias=)` | OK |
| Evaluación | `from mlflow.genai.scorers import scorer`; `from mlflow.entities import Feedback`; `@scorer def f(outputs, expectations): return Feedback(value=..., rationale=...)` (o devolver un `bool`); `mlflow.genai.evaluate(data=[{"inputs": {...}, "expectations": {...}}], predict_fn=fn, scorers=[...])` | OK: métricas `herramienta_correcta/mean` = 0,5 y `sin_inventar/mean` = 1,0 sobre 2 preguntas (el 0,5B acertó una) |
| Agente como modelo (*models from code*) | En `agente_from_code.py`: `class AgentePico(mlflow.pyfunc.PythonModel)` y `mlflow.models.set_model(AgentePico())`. Registro: `mlflow.pyfunc.log_model(name="agente", python_model="<ruta>.py", registered_model_name="agente-retencion", input_example=DataFrame)` dentro de `mlflow.start_run()` | OK |
| Alias de modelo y carga | `MlflowClient().set_registered_model_alias("agente-retencion", "champion", version)`; `mlflow.pyfunc.load_model("models:/agente-retencion@champion").predict(DataFrame)` | OK: devolvió texto del LLM local |
| Traza dentro del `predict` cargado | con `mlflow.openai.autolog()` activo en el proceso | OK: span `Completions` |

Trampas encontradas:
- **`mlflow.get_trace(id)` devolvió `None` justo después de la llamada** (error `'NoneType' object has no attribute 'data'`), porque las trazas se envían de forma asíncrona. Con `os.environ["MLFLOW_ENABLE_ASYNC_TRACE_LOGGING"] = "false"` antes de importar mlflow funcionó en el segundo intento. Es el primer intento fallido de esos tres pasos (1a, 1b, 1c y 4c); en la segunda ejecución con la variable todos pasaron. Para los tests de CI conviene fijarla. Sin la variable, `search_traces` devolvió 0 filas en el mismo proceso.
- `mlflow.pyfunc.log_model` usa `name=` (en 3.x ya no se pasa `artifact_path` como nombre principal) y devuelve un `model_uri` del tipo `models:/m-<id>`.
- Avisos de MLflow (`UserWarning: Add type hints to the predict method` y el `input_example`): no son errores. El texto de los prompts con tildes se guardó bien (el `�` que se ve en la consola es la codificación de la terminal, no del dato).
- En 1c el 0,5B no hizo la llamada a herramienta pedida (la traza se guardó con 1 span igualmente). **No se verificó que la traza recoja el bloque `tool_calls`** (sin dato).

No verificado: scorers que usan un LLM juez (`Safety`, `Correctness`…): solo se importó `Safety`, no se ejecutó, porque exigen un modelo juez y con Ollama habría que configurarlo. Para el curso, scorers propios deterministas (como los de arriba) son lo que se ha probado.

## 6. Recomendación de modelo

- **Para clase y para la demo: Qwen2.5-3B (Q4_K_M).** Único con 100 % de herramienta y de argumentos y con las dos trampas bien. Cuesta 2,1 GB de disco, ~2,4 GB de RAM en pico, 4,7 s de latencia mediana (9,2 s p95) en esta CPU y 16 s en la primera llamada (carga). Aceptable para un laboratorio si se avisa de que cada pregunta tarda unos segundos.
- **Para CI de cada push: el LLM falso**, como ya decía el plan (D5). Ningún modelo real es determinista en velocidad ni barato.
- **Para el job de evaluación con LLM real: el 3B también**, no el 0,5B. El 0,5B cuesta un tercio de memoria pero cae en las trampas y falla argumentos: útil como **ejemplo didáctico de lo que mide la evaluación** (su 70 % frente al 100 % del 3B es justo la lección del extra de S4), no como base. **No usar el 1,5B** con este prompt: se niega a usar herramientas.
- Plan B para equipos justos de memoria (Codespace de 2 núcleos): el 3B pide ~2,4 GB y no se midió en Codespace; el 0,5B (680 MiB) cabe, con el coste de calidad. **Sin dato** de Codespace y de runner (§7).

## 7. Riesgos y lo no verificado

- **Runner de GitHub y Codespace: NO medidos** (no se pedía). El YAML a probar está en `runner-propuesta.yml`, sin subir. El «4 vCPU y 16 GB en repo público» del plan sigue sin confirmar. Un 3B en 4 vCPU tardará más que en estos 14 hilos: **sin dato**.
- **Red del alumno**: el registro de Ollama está bloqueado en esta red corporativa (solo bajó por `hf.co/`). En casa o en Codespace `ollama pull qwen2.5:3b` normalmente funciona, pero **no se comprobó**. El material debe dar el comando `hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF:Q4_K_M` como seguro, que es el que sí se probó.
- **GitHub con proxy de entorno falla** por certificados (necesita ir sin proxy): relevante para quien prepare el material en este portátil.
- **Versión de `mcp`**: 2.x rompe los ejemplos de 1.x. Fijarla.
- **Velocidad**: 5,3 tok/s con el 3B en CPU; una respuesta larga con skills (guion de llamada de varias frases) puede tardar medio minuto. Las preguntas medidas son cortas (26 tokens de media). Sin medir un guion largo ni una conversación de varios pasos con el agente completo (cada paso reenvía el historial).
- **Muestra pequeña** y un solo prompt de sistema: cambiar el prompt puede cambiar mucho el 1,5B. Sin prueba de inyección ni de datos inventados (eso es T05).
- **Sin comparar con `llama3.2:3b`** ni con otros modelos con *tool calling*; podría haber uno mejor.
- **`openai` 3.57.0**: versión que informa el entorno; funcionó para `chat.completions` con `tools` y `autolog`. Se recomienda fijarla también.
- **Latencias de 0,5B y 1,5B** medidas con descargas concurrentes (ver §3).

## 8. Archivos

En `00-Planificacion\s5-agentes\_pico\`: `descargar_ollama.py`, `medir_tool_calling.py`, `servidor_mcp_pico.py`, `cliente_mcp_pico.py`, `probar_mlflow.py`, `agente_from_code.py`, `runner-propuesta.yml`, `mlflow.db`, y `salidas\` (`tc_*.json` y `.log`, `mcp_v1.txt`, `mcp_v2.txt`, `mlflow_log.txt`, `mlflow_resultados.json`, `descarga_ollama.txt`). Entornos: `C:\bk\HC-Cursos\.venv-s5-pico` y `.venv-s5-pico-mcp1`; Ollama en `C:\bk\ollama`.
