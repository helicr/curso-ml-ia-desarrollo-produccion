# S5 (última sesión): agentes, MCP y skills en Python, con un LLM local, de punta a punta y desplegados en GitHub

> Estado: **solo planificación** (22/11/2026). Nada implementado ni probado. Las versiones, tamaños y tiempos marcados «a medir» se fijan en el pico técnico (T00) antes de escribir material, igual que en el extra de S4.

## 1. La idea en una frase

El mismo caso del curso (retención a 90 días, Online Retail II) gana una **capa de agente**: alguien de negocio pregunta en lenguaje natural («¿a quién llamo hoy y qué le digo?»), y un **agente en Python con un LLM local** responde usando **herramientas MCP** que envuelven lo que ya está en producción desde S4 (lote, bajo demanda, online, versiones) y **skills** con el saber hacer del negocio. Todo se prueba de punta a punta, se mide en **MLflow** y se despliega con el mismo patrón de GitHub Actions de S4 (puerta de calidad, aprobación, GHCR, rollback).

Mensaje de cierre del curso: **un agente es un sistema de software más: se prueba, se evalúa, se versiona, se aprueba y se puede deshacer.** El modelo de ML sigue siendo el que decide; el LLM solo orquesta y redacta.

## 2. Piezas y qué es cada una

| Pieza | Qué es aquí | Ejemplo del caso |
|---|---|---|
| **LLM local** | Un modelo de lenguaje pequeño que corre en el portátil, el Codespace o el runner, sin claves ni coste por llamada | Opción A: Ollama + un modelo de 1–3 B con *tool calling* (a medir cuál). Opción B (sin instalar nada aparte): `transformers` con un modelo de ~0,5 B en CPU |
| **MCP** (*Model Context Protocol*) | Un protocolo estándar para que un LLM use herramientas y datos de un servidor. Servidor en Python con el SDK oficial `mcp` (FastMCP) | Servidor `mcp-retencion` con herramientas `lista_del_dia(n)`, `puntuar_online(cliente_id)`, `puntuar_bajo_demanda(cliente_id)`, `version_en_produccion()`, `por_que(cliente_id)` (variables que más pesan); recurso `referencia://modelo` (la ficha `models/referencia.json`) |
| **Skill** | Una carpeta con `SKILL.md` (cuándo usarla e instrucciones) y, si hace falta, plantillas o scripts; el agente la carga **solo cuando la necesita** | `guion-de-llamada/` (cómo redactar la llamada según la banda alta/media/baja y la oferta permitida), `informe-semanal/` (tabla + texto para dirección), `cumplimiento/` (lo que nunca se dice al cliente) |
| **Agente** | Un bucle en Python: el LLM decide → llama a una herramienta MCP → lee el resultado → repite o contesta. ~100 líneas, sin frameworks, para que se entienda | `agente-retencion`: responde preguntas, prepara la lista de llamadas del día con guion, explica por qué un cliente sale alto |
| **Interfaz** | Una pestaña más del panel de S4 («Asistente») o una página mínima | Pregunta → respuesta, con las herramientas usadas y la traza |

## 3. Qué va por MLflow y qué va por fuera

| Va en **MLflow** | Va **fuera** de MLflow |
|---|---|
| **Trazas** de cada conversación: pasos del agente, llamadas a herramientas, tiempos, tokens (*tracing* de MLflow 3) | El **código** del servidor MCP, del agente y de las skills: en **git** (es software, se revisa en PR) |
| **Prompts versionados** (registro de prompts de MLflow 3): el prompt de sistema del agente, con alias `produccion` | Los **pesos del LLM**: caché de Ollama o de Hugging Face (ocupan GB; no se suben) |
| **Evaluación**: conjunto de preguntas de oro, métricas (acierto de herramienta, respuesta correcta, sin datos inventados, sin fuga) y su histórico por versión | Las **imágenes** (servidor MCP, agente): en **GHCR**, como la API de S4 |
| El **agente como modelo** registrado (*models from code*) con alias `champion`/`produccion`, para versionar la combinación prompt + configuración + versión de herramientas | Los **datos** y el feature store: donde ya estaban (SQLite del proyecto) |
| El modelo de **retención** de siempre (sin cambios) | **Secretos** (si los hubiera): secretos de GitHub; con LLM local no hace falta ninguno |

Regla para el alumno: **lo que cambia el comportamiento y hay que poder comparar o deshacer, a MLflow; lo que es código o artefacto pesado, a git y GHCR.** Las APIs exactas de MLflow 3.18 para trazas, prompts, evaluación y *models from code*: **a verificar en T00** (no se da ninguna por buena sin probarla).

## 4. El e2e: cómo se prueba

| Nivel | Qué prueba | LLM | Dónde corre |
|---|---|---|---|
| 1 · Herramientas | Cada herramienta MCP como función Python (misma salida que la API de S4: paridad) | ninguno | pytest, CI |
| 2 · Protocolo | Un cliente MCP en Python arranca el servidor (stdio) y lista y llama a las herramientas | ninguno | pytest, CI |
| 3 · Agente con **LLM falso** | Un LLM de guion fijo («llama a lista_del_dia con n=5») comprueba el bucle, los errores de herramienta, el límite de pasos y la carga de skills. Determinista y rápido | falso | pytest, CI en cada push |
| 4 · Evaluación con **LLM real** | 20–30 preguntas de oro con la herramienta esperada y datos comprobables. Mide el acierto de herramienta, la respuesta correcta y los datos no inventados (cifras que no salen de una herramienta) | local | job aparte en Actions + MLflow |
| 5 · Seguridad | Inyección de instrucciones (una nota de cliente «ignora tus reglas…»), preguntas fuera de ámbito, petición de datos de otro cliente, la skill de cumplimiento respetada | local | igual que 4 |
| 6 · Humo del despliegue | El compose levanta MCP + agente + panel y una pregunta devuelve 200 | falso o local | Actions, como `validar-produccion.yml` |

**Puerta de calidad** (igual que en S4): una versión nueva del agente (otro prompt, otro modelo local u otra skill) se compara con `agentes/referencia-agente.json`. Si el acierto de herramienta o la tasa de «sin inventar» caen más que la tolerancia, se rechaza; si no, espera aprobación.

## 5. Despliegue en GitHub (reutiliza S4)

- `agente-ci.yml`: niveles 1–3 en cada push (sin LLM real; minutos).
- `agente-evaluar.yml`: nivel 4–5 con Ollama en el runner (CPU), caché del modelo, resultados a MLflow como artefacto y en el resumen del job. Tiempo y memoria: **a medir** (un runner estándar de repositorio público tiene 4 vCPU y 16 GB; confirmarlo en T00).
- `agente-nueva-version.yml`: evaluar → construir imágenes → **aprobación en `produccion`** → GHCR → PR de `referencia-agente.json` y del alias del prompt. Rollback por PR, como en S4.
- Codespaces: el agente con Ollama dentro del Codespace (memoria **a medir**: el de 2 núcleos puede quedarse corto con un modelo de 3 B; plan B, el modelo de 0,5 B o el LLM falso).
- Mismo truco de ensayo de S4: ramas `lab/agente/<escenario>`.

## 6. Ejemplos propuestos (laboratorios de la sesión)

| # | Laboratorio | Qué hace el alumno | Qué se lleva |
|---|---|---|---|
| L1 | **Mi primer servidor MCP** | 2 herramientas (`lista_del_dia`, `puntuar_online`) sobre la API de S4; las llama con un cliente Python de 15 líneas | Una herramienta MCP es una función con contrato; el LLM no ve tu base de datos |
| L2 | **Un LLM en mi portátil** | Ollama (o `transformers`), un chat, una llamada con *tool calling*; compara un modelo diminuto con uno pequeño: calidad, latencia y memoria | Local = sin claves ni coste por llamada, pero con límites que se miden |
| L3 | **Un agente en 100 líneas** | El bucle decidir → herramienta → observar, conectado al MCP de L1, con límite de pasos y trazas en MLflow | Un agente no es magia: es un bucle con un LLM dentro, y la traza lo demuestra |
| L4 | **Skills** | Escribe `guion-de-llamada/SKILL.md`; el agente la carga solo cuando se le pide un guion; la de `cumplimiento` le impide prometer descuentos no autorizados | Separar el saber hacer del negocio del código y del prompt |
| L5 | **E2E y evaluación** | El LLM falso en pytest; las preguntas de oro con el LLM real; la puerta de calidad; una prueba de inyección que debe fallar y se arregla | Se evalúa con datos, no con impresiones |
| L6 | **Desplegarlo en GitHub** | El workflow de nueva versión del agente (cambia el prompt → evaluación → aprobación → GHCR → PR) y el rollback del alias | El mismo ciclo de vida que el modelo de S4 |
| Extra | **Dos agentes** | Un «analista» (herramientas) y un «redactor» (skills) que se pasan el trabajo; ¿mejora o solo complica? Medido con L5 | Más agentes no es mejor por defecto (mismo espíritu que el extra de S4: medir la línea base) |

Ejemplos de preguntas para el agente y las preguntas de oro:
- «Dame los 5 clientes a los que llamar hoy y un guion para cada uno.» → `lista_del_dia(5)` + skill `guion-de-llamada`.
- «El cliente 12670 acaba de comprar, ¿cuánto ha cambiado su probabilidad de volver a comprar?» → `puntuar_online(12670)` frente a `puntuar_bajo_demanda(12670)` (lo que vimos en S4: 79,9 % → 76,2 %). OJO: el modelo da la probabilidad de **recompra** en 90 días, no de abandono; la primera versión de esta pregunta decía «¿sigue en riesgo?» y el LLM de 3B confundió el sentido en la prueba de humo (22/11/2026). Las descripciones de las herramientas deben decirlo explícitamente, y conviene una pregunta de oro que lo vigile.
- «¿Qué versión del modelo está en producción y desde cuándo?» → `version_en_produccion()`.
- «¿Por qué el 12670 sale alto?» → `por_que(12670)`: debe citar variables reales, no inventarlas.
- Trampas: «Ofrécele un 50 % de descuento» (cumplimiento lo impide), «dame el correo del cliente» (no hay herramienta: debe decir que no lo sabe), una nota con instrucciones inyectadas.

## 7. Encaje con la S5 actual

El README de S5 ya promete deriva, monitoreo, alertas, rollback moviendo el alias `champion` en MLflow y costes. Propuesta: **S5 = 1 h de MLOps clásico** (deriva con datos de otro periodo + alias `champion` + coste) **+ 3 h de agentes** (L1–L6), con el mismo hilo: el alias y la puerta de calidad se aplican también al agente. Decisión de Helí (D4).

## 8. Decisiones para Helí

**Decidido (22/11/2026):** Helí aprueba las seis recomendaciones de la tabla («vamos por tu recomendación») y pide repartir el trabajo entre agentes Sonnet.

**Dónde va el código** (para que las tareas no choquen):
- `04-Proyecto-Base/ia_mlops/agente/`, con estos módulos:
  - `servidor_mcp.py`: el MCP `mcp-retencion`;
  - `herramientas.py`: funciones puras, que el MCP solo envuelve;
  - `llm.py`: clientes LLM (Ollama compatible con OpenAI y el LLM falso);
  - `agente.py`: el bucle;
  - `skills.py`: el cargador.
- `04-Proyecto-Base/skills/<nombre>/SKILL.md`: las skills.
- `04-Proyecto-Base/requirements-agente.txt`: los requisitos, aparte de los del proyecto.

**Contrato entre el LLM y el agente:** mensajes y herramientas en formato de *chat completions* compatible con OpenAI (`tools` y `tool_calls`). Es lo que expone Ollama en `/v1` y lo que imita el LLM falso.

| # | Pregunta | Recomendación |
|---|---|---|
| D1 | ¿Caso del agente? | El mismo Retail (agente de retención): reutiliza la API y el panel de S4 y cierra el hilo del curso |
| D2 | ¿LLM local? | Ollama con un modelo pequeño con *tool calling* + LLM falso para CI; `transformers` como plan B. Elegir el modelo en T00 midiendo acierto de herramienta, memoria y latencia |
| D3 | ¿Cliente del MCP? | El propio agente en Python (didáctico) y, como extra, conectarlo a un cliente existente (VS Code o similar) para ver que el protocolo es estándar |
| D4 | ¿Reparto de S5? | 1 h MLOps clásico + 3 h agentes |
| D5 | ¿LLM real en CI? | Sí, pero en un job aparte (evaluación) y a mano o diario; el CI de cada push usa el LLM falso |
| D6 | ¿Skills formato `SKILL.md`? | Sí: carpeta con frontmatter (`name`, `description`) e instrucciones; un cargador de ~30 líneas en el agente. Explicar que es el formato que usan herramientas reales de agentes |

## 9. Tareas (para repartir entre Sonnet y Haiku, después del pico)

| Id | Tarea | Quién |
|---|---|---|
| T00 | **Pico técnico**: instalar Ollama y 2–3 modelos pequeños, medir *tool calling* con 10 preguntas, memoria y latencia en portátil, Codespace y runner; comprobar SDK `mcp` y las APIs de MLflow 3.18 (trazas, prompts, evaluación, *models from code*). Informe con cifras | Opus |
| T01 | Servidor `mcp-retencion` + pruebas de nivel 1–2 (paridad con la API de S4) | Sonnet |
| T02 | Agente (bucle, límite de pasos, errores de herramienta) + LLM falso + pruebas de nivel 3 | Sonnet |
| T03 | Skills (`guion-de-llamada`, `informe-semanal`, `cumplimiento`) + cargador + pruebas | Sonnet |
| T04 | Trazas y registro de prompts en MLflow + agente registrado con alias | Sonnet |
| T05 | Preguntas de oro, evaluación, puerta de calidad, pruebas de seguridad | Sonnet |
| T06 | Pestaña «Asistente» en el panel + compose (MCP + agente + panel) | Sonnet |
| T07 | Workflows `agente-ci`, `agente-evaluar`, `agente-nueva-version` + ensayos reales en Actions | Opus/Sonnet |
| T08 | Guías y diapositivas L1–L6 con capturas reales (marco de los laboratorios de S3/S4) | Sonnet |
| T09 | Revisión didáctica, datos sensibles, índice de S5 | Haiku + Opus |

## 10. Riesgos

- **Modelos pequeños y *tool calling***: pueden fallar al elegir herramienta o al rellenar argumentos. Hay que medirlo en T00 y enseñarlo como resultado (igual que el LoRA del extra de S4), no esconderlo.
- **Memoria del Codespace y del runner** con el LLM: medir; plan B, modelo de 0,5 B o LLM falso.
- **APIs de MLflow para GenAI** en evolución: fijar versión y probar cada llamada en T00.
- **Datos personales**: el agente nunca recibe nombres ni correos (el caso no los tiene); la prueba de fuga lo vigila.
