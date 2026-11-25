# Práctica 5: un LLM gestionado (Gemini en Vertex AI) explica la predicción

## Objetivo
Hacer lo mismo que el agente de S5 pero con un **LLM alojado por Google** en lugar de uno local: el **modelo** de retención calcula la probabilidad y cuánto pesa cada variable (cálculo exacto de la regresión logística) y **Gemini solo redacta** la explicación en español a partir de esos números. Sin claves: se usa la autenticación de Cloud Shell (credenciales predeterminadas de la aplicación).

- **Tiempo estimado:** 10-15 min (estimado, sin medir).
- **Coste aproximado:** sin dato ([precios de IA generativa](https://cloud.google.com/vertex-ai/generative-ai/pricing): la página no se pudo leer entera). Cada llamada usa unos cientos de tokens; no crea ningún recurso que cobre en reposo.
- **Ubicación:** `global`. Gemini **no** figura para Santiago (`southamerica-west1`); `global` es el endpoint mundial, sin garantía de dónde se procesa la petición. Aquí solo viajan variables agregadas de un cliente de ejemplo, ningún dato personal (el caso solo tiene un número de cliente y su país).
- **Modelo:** `gemini-3.1-flash-lite`, el más económico entre los vigentes el 25/11/2026. `gemini-2.5-flash` y `gemini-2.5-flash-lite` **se retiraron el 20/10/2026** ([ciclo de vida](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versions)), así que no uses ejemplos antiguos con esos nombres. Que `gemini-3.1-flash-lite` responda en `global`: **sin verificar**; se cambia con `export CURSO_MODELO_LLM=…` o `CURSO_REGION_GEMINI=…`.
- **SDK:** `google-genai`, el recomendado hoy ([guía](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/sdks/overview)). Versión instalada: la más reciente (se imprime en `crear.sh`); sin fijar.

## Qué crea
Ningún recurso en GCP. Habilita la API de Vertex AI e instala `google-genai` en el entorno `~/.venv-curso-ml` (el mismo de las otras prácticas).

## Pasos
1. **Cloud Shell:** `./crear.sh`.
2. **Cloud Shell:** `./probar.sh` (explica los clientes `activo` y `dormido` de `../clientes_ejemplo.json`).
3. **Cloud Shell:** `./borrar.sh` (desinstala el SDK y lista endpoints por si hiciste algo a mano).

## Qué debes ver
- Primero, los **hechos del modelo** en JSON: probabilidad, tramo (alta/media/baja según `config.SEGMENTOS_RECOMPRA`), recomendación de negocio y las 5 variables que más pesan con su efecto. Esos números son del modelo, no del LLM.
- Después, un párrafo en español (≤ 120 palabras) que cita la probabilidad y las variables. Termina con `OK: la explicación cita la probabilidad del modelo (xx.x %).` Si el texto no cita la cifra, el script avisa (código 2): **un LLM puede redactar mal; la cifra manda el modelo.**
- Con `temperatura 0` las respuestas son parecidas entre ejecuciones, pero no se garantiza que sean idénticas.

## Por qué así (ideas para la clase)
- El LLM **no calcula** la probabilidad: se le entrega calculada y se comprueba que la cita (misma regla que en S5: las herramientas devuelven los números, el LLM los cuenta).
- Instrucción de sistema: «usa solo los datos que te doy, no inventes causas».
- El peso por variable es exacto porque el modelo es una regresión logística (la suma de pesos más el intercepto reproduce la probabilidad; el script lo comprueba con una aserción).

## Nota: Model Garden (solo explicado, no se despliega nada)
**Model Garden** es la biblioteca de modelos de Vertex AI: modelos de Google y de socios que se pueden probar, ajustar y **desplegar en un endpoint propio** ([fuente](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/model-garden/explore-models)). Para modelos abiertos (por ejemplo, de Hugging Face) se paga **el cómputo que se use para desplegarlos en el endpoint**, por tiempo, igual que en la práctica 4 pero con máquinas mucho mayores (normalmente con GPU: requisitos, cuotas y regiones **sin verificar**, la página no los lista). Por eso en el curso **no se despliega**: no es barato ni cabe en el crédito de prueba sin riesgo. Si alguna vez se hace: consola ☰ > Vertex AI > Model Garden > tarjeta del modelo > Desplegar, y **deshacer el despliegue y borrar el endpoint al terminar** (`gcloud ai endpoints list` / `undeploy-model` / `delete`). Coste: sin dato.

## Si falla
| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| `404 … model not found` o «not supported in location» | El modelo no está en esa ubicación | Probar otro `CURSO_REGION_GEMINI` (p. ej. `southamerica-east1`; **sin verificar**) o ver los modelos vigentes en la página de ciclo de vida |
| `403` / `PERMISSION_DENIED` | Falta `roles/aiplatform.user` | Pedirlo al administrador |
| `API has not been used` / `SERVICE_DISABLED` | API sin habilitar | `gcloud services enable aiplatform.googleapis.com` (lo hace `crear.sh`) |
| `DefaultCredentialsError` | Credenciales de aplicación no disponibles | En Cloud Shell: `gcloud auth application-default login` (te da un enlace y un código; no crea claves en disco de cuentas de servicio) |
| Texto cortado | El modelo gastó los tokens pensando | Subir `max_output_tokens` en `explicar_prediccion.py` |
| Una política de la organización bloquea Gemini | Restricción de modelos | Consultarlo con quien administra la organización |

## Fuentes
- SDK y llamada: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/sdks/overview
- Ubicaciones y endpoint global: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/locations
- Ciclo de vida de modelos: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versions
- Model Garden: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/model-garden/explore-models
