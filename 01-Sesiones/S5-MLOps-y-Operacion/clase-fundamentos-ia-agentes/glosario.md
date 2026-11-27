# Glosario: fundamentos de la IA, los LLM, los RAG y los agentes

De lo más general a lo más concreto. Cada término lleva una definición corta y, cuando existe, un ejemplo de **nuestro caso** del curso (¿volverá a comprar un cliente en los próximos 90 días?: cliente 12369, modelo `retencion-90d@champion`, servidores MCP del extra de S5).

Generado por `generar.py` (consulta de fuentes: 26/11/2026). Las fuentes están en la última diapositiva de `index.html`.

## 1. Lo general

### Inteligencia artificial (IA)

Sistemas que hacen tareas que normalmente exigen inteligencia humana: percibir, decidir, generar lenguaje.

*En nuestro caso:* Un sistema de reglas que marca los pedidos que hay que revisar es IA aunque no aprenda de datos.

### Aprendizaje automático (ML)

Sistemas que aprenden patrones a partir de los datos en lugar de seguir reglas escritas a mano.

*En nuestro caso:* El modelo retencion-90d aprende de las compras pasadas de los clientes.

### Aprendizaje profundo (DL)

Aprendizaje automático con redes neuronales de muchas capas; brilla con imágenes, audio y texto.

*En nuestro caso:* Reconocer un producto en una foto; un LLM es una red profunda.

### IA generativa

Modelos que crean contenido nuevo: texto, imágenes, código.

*En nuestro caso:* Redactar el borrador de la recomendación para un gestor.

## 2. Datos y aprendizaje automático

### Variable (feature)

Una característica medible del caso que el modelo recibe como entrada.

*En nuestro caso:* recencia_dias = 413 y frecuencia_180d = 0 del cliente 12369; el modelo usa 13 variables.

### Modelo

Función aprendida de los datos que convierte variables en una predicción.

*En nuestro caso:* retencion-90d@champion devuelve 0,3035 para el cliente 12369.

### AUC

Medida de cuán bien un modelo ordena a los positivos por delante de los negativos: 0,5 es azar y 1 es perfecto.

*En nuestro caso:* Versión 6 del modelo: 0,6982 en validación y 0,7471 en test.

### Sobreajuste

Memorizar los datos de entrenamiento y fallar con datos nuevos; se detecta con validación y test.

*En nuestro caso:* El error de entrenamiento baja pero el de validación vuelve a subir.

## 3. Redes y modelos de lenguaje

### Red neuronal

Neuronas artificiales (suma ponderada + activación) conectadas en capas.

*En nuestro caso:* Nuestra regresión logística equivale a una sola neurona con sigmoide.

### Transformer

Arquitectura de red basada en atención; es la base de los LLM actuales (Vaswani et al., 2017).

### Atención

Mecanismo por el que cada token pondera a los demás para interpretar su significado en contexto.

*En nuestro caso:* En «el pedido… estaba roto», «estaba» mira sobre todo a «pedido».

### Token

Pieza de texto (trozo de palabra, signo) que el modelo procesa; coste y límites se miden en tokens.

*En nuestro caso:* El troceado real depende del modelo.

### Parámetros

Los números que el modelo aprende en el entrenamiento; son su «saber» estable.

### Ventana de contexto

La cantidad de tokens que el modelo puede considerar a la vez en una llamada.

*En nuestro caso:* Si algo no cabe en la ventana, para el modelo no existe.

### LLM (modelo de lenguaje grande)

Red transformer entrenada para predecir el siguiente token; genera y entiende lenguaje.

*En nuestro caso:* Qwen2.5 en Ollama, en el laboratorio de agentes de S5.

### Preentrenamiento

Fase inicial: leer muchísimo texto prediciendo el siguiente token.

### Ajuste fino (fine-tuning)

Seguir entrenando un modelo con ejemplos de tu tarea.

### LoRA

Ajuste fino que entrena solo unas matrices pequeñas añadidas y deja fijo el resto (Hu et al., 2021).

### RLHF (valoraciones humanas)

Alineación: ajustar el modelo con preferencias humanas para que siga instrucciones.

### Prompt

El texto de entrada: instrucciones del sistema, ejemplos, contexto y pregunta.

*En nuestro caso:* «¿Qué probabilidad tiene el cliente 12369?»

### Temperatura

Parámetro que controla cuánto se arriesga al elegir el siguiente token: baja = predecible, alta = variada.

### Alucinación

Contenido plausible pero inventado, dicho con aplomo.

*En nuestro caso:* Una probabilidad del cliente 12369 «de memoria» en vez de la de la herramienta.

### Salida estructurada

Respuesta en un formato fijo (por ejemplo JSON) que el código puede validar.

*En nuestro caso:* La respuesta de predecir_cliente: probabilidad, tramo y versión.

### Razonamiento

Pasos intermedios que el modelo escribe antes de responder; mejora problemas de varios pasos a cambio de más tokens.

## 4. Búsqueda y RAG

### Embedding

Vector de números que representa el significado de un texto (o imagen).

*En nuestro caso:* «¿Volverá a comprar?» queda cerca de «Retención a 90 días».

### Vector

Lista ordenada de números.

*En nuestro caso:* Los embeddings reales tienen cientos o miles; el ejemplo de la clase usa 3.

### Similitud (coseno)

Medida de parecido entre vectores por el ángulo que forman: 1 misma dirección, 0 sin relación.

*En nuestro caso:* En la clase: 0,949 para el texto de retención y 0,099 para la paella.

### Base vectorial (índice vectorial)

Almacén que guarda vectores y devuelve los k más parecidos a una consulta, normalmente de forma aproximada.

### Chunk (trozo)

Fragmento de un documento que se indexa y se recupera por separado.

*En nuestro caso:* Un apartado de una guía del curso.

### RAG (generación aumentada por recuperación)

Buscar trozos relevantes y dárselos al LLM en el prompt para que responda con ellos y cite.

*En nuestro caso:* Recuperar el apartado L6 de la guía para responder cómo hacer un rollback.

### Reranker

Segundo paso que reordena los trozos recuperados por relevancia antes de construir el prompt.

## 5. Contexto, herramientas y agentes

### Ingeniería de contexto

Diseñar qué entra en la ventana (instrucciones, historial, memoria, conocimiento, resultados, estado) en cada llamada.

### Function calling (llamada a funciones)

El modelo devuelve «quiero llamar a esta función con estos argumentos»; la aplicación la ejecuta.

*En nuestro caso:* predecir_cliente(cliente_id=12369).

### Herramienta

Función con contrato (nombre, descripción, argumentos) que un agente puede invocar.

*En nuestro caso:* resumen_cliente, predecir_cliente, por_que.

### MCP (Model Context Protocol)

Estándar abierto para conectar aplicaciones de IA con herramientas, recursos y prompts de servidores.

*En nuestro caso:* mcp-datos-master y mcp-modelo-retencion, del extra de S5.

### Skill

Carpeta con un SKILL.md: instrucciones que el agente carga solo cuando hacen falta.

*En nuestro caso:* Las skills del laboratorio de agentes de S5.

### Workflow

Sistema donde LLM y herramientas siguen caminos predefinidos en código.

*En nuestro caso:* Cada lunes: lista del día y redactar mensajes.

### Agente

Sistema donde el LLM dirige dinámicamente sus pasos y el uso de herramientas.

*En nuestro caso:* «¿A quién llamo hoy y qué le digo?»

### ReAct

Patrón que alterna razonar y actuar: pensar, llamar a una herramienta, observar y repetir (Yao et al., 2022).

*En nuestro caso:* Datos del cliente → probabilidad → respuesta.

### Multiagente

Varios agentes con roles distintos que se reparten una tarea.

*En nuestro caso:* En el curso: solo planteado, no implementado.

## 6. Evaluar y operar

### Guardrail (barrera)

Regla fuera del modelo, en código, que limita lo que entra, lo que hace o lo que sale.

*En nuestro caso:* Un tope de pasos; solo lectura en la base de datos.

### Humano en el bucle

Una persona aprueba las acciones sensibles antes de que se ejecuten.

*En nuestro caso:* La aprobación de un environment antes de desplegar un agente.

### Inyección de prompt

Texto (o documento) que intenta dar órdenes al agente para que se salte sus reglas.

### Evaluación (preguntas de oro)

Conjunto de preguntas con la herramienta esperada y un dato comprobable para medir un agente.

*En nuestro caso:* 25 preguntas de oro en el laboratorio de agentes de S5.

### Traza

Registro paso a paso de una conversación: llamadas al LLM, a herramientas y tiempos.

*En nuestro caso:* Las trazas del laboratorio se guardan en MLflow.

### LLMOps / AgentOps

Versionar, evaluar, aprobar, desplegar, observar y revertir prompts, skills y agentes, como se hace con un modelo.

*En nuestro caso:* Los workflows agente-ci, agente-evaluar, agente-nueva-version y agente-rollback.

### Alias / champion

Puntero con nombre a una versión de un modelo (o agente) en el registro: «la que manda ahora».

*En nuestro caso:* @champion apunta a la versión 6 de retencion-90d.

## 7. Google Cloud

### Plataforma de Gemini (antes Vertex AI)

Nombre en la consola en español de la «Gemini Enterprise Agent Platform», que la documentación presenta como una evolución de Vertex AI.

### Model Garden

Biblioteca para descubrir, probar, personalizar y desplegar modelos de Google y de socios.

### Agent Studio

Espacio para elegir modelos, refinar instrucciones y optimizar prompts.

### RAG Engine

Componente gestionado de la plataforma para montar RAG: ingesta, trocear, embeber, indexar, recuperar y generar.

### Búsqueda de vectores (Vector Search)

Motor de búsqueda vectorial de Google basado en ScaNN, con índices y extremos de índice.

### ADK (Agent Development Kit)

Marco de código abierto para construir agentes (Python, TypeScript, Go y Java).

### Agent Runtime

Entorno gestionado para desplegar y escalar agentes.

### Cloud Run

Plataforma gestionada para ejecutar contenedores; puede alojar servidores MCP con HTTP en streaming.

### Secret Manager

Servicio para guardar y controlar secretos y credenciales.

### Workload Identity Federation (WIF)

Permite que cargas externas accedan a Google Cloud con identidades federadas, sin claves de cuenta de servicio.

*En nuestro caso:* GitHub Actions con WIF en S4.

## Fuentes

- Dartmouth · El proyecto de verano de 1956: <https://home.dartmouth.edu/about/artificial-intelligence-ai-coined-dartmouth>
- Vaswani et al. · Attention Is All You Need (arXiv, jun 2017): <https://arxiv.org/abs/1706.03762>
- Lewis et al. · Retrieval-Augmented Generation (arXiv, may 2020): <https://arxiv.org/abs/2005.11401>
- Hu et al. · LoRA (arXiv, jun 2021): <https://arxiv.org/abs/2106.09685>
- Ouyang et al. · Training language models to follow instructions with human feedback (arXiv, mar 2022): <https://arxiv.org/abs/2203.02155>
- Yao et al. · ReAct (arXiv, oct 2022): <https://arxiv.org/abs/2210.03629>
- Anthropic · Introducing the Model Context Protocol (25/11/2024): <https://www.anthropic.com/news/model-context-protocol>
- Model Context Protocol · What is MCP?: <https://modelcontextprotocol.io/docs/getting-started/intro>
- Model Context Protocol · Architecture overview: <https://modelcontextprotocol.io/docs/learn/architecture>
- Anthropic · Building effective agents: <https://www.anthropic.com/engineering/building-effective-agents>
- Google Cloud · Gemini Enterprise Agent Platform overview: <https://docs.cloud.google.com/gemini-enterprise-agent-platform/overview>
- Google Cloud · Model Garden: explorar modelos: <https://docs.cloud.google.com/vertex-ai/generative-ai/docs/model-garden/explore-models>
- Google Cloud · Agent Studio: <https://docs.cloud.google.com/gemini-enterprise-agent-platform/agent-studio>
- Google Cloud · Text embeddings: <https://docs.cloud.google.com/vertex-ai/generative-ai/docs/embeddings/get-text-embeddings>
- Google Cloud · Vector Search overview: <https://docs.cloud.google.com/vertex-ai/docs/vector-search/overview>
- Google Cloud · RAG Engine overview: <https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-overview>
- Google Cloud · BigQuery vector search: <https://docs.cloud.google.com/bigquery/docs/vector-search-intro>
- Google Cloud · BigQuery: generar embeddings de texto: <https://docs.cloud.google.com/bigquery/docs/generate-text-embedding>
- Google Cloud · BigQuery ML.GENERATE_EMBEDDING (referencia): <https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-generate-embedding>
- Google Cloud · Agent Runtime (escalar agentes): <https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale>
- Google Cloud · Agent Development Kit (ADK): <https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/adk>
- Google Cloud · Observabilidad de agentes: <https://docs.cloud.google.com/gemini-enterprise-agent-platform/optimize/observability/overview>
- Google Cloud · ¿Qué es Cloud Run?: <https://docs.cloud.google.com/run/docs/overview/what-is-cloud-run>
- Google Cloud · Cloud Run: alojar servidores MCP: <https://docs.cloud.google.com/run/docs/host-mcp-servers>
- Google Cloud · Secret Manager overview: <https://docs.cloud.google.com/secret-manager/docs/overview>
- Google Cloud · Workload Identity Federation: <https://docs.cloud.google.com/iam/docs/workload-identity-federation>
- Google Cloud · Cloud Logging overview: <https://docs.cloud.google.com/logging/docs/overview>
