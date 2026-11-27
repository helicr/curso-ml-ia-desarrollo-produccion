# Guion del docente · S5 (240 min)

Sesión de 10:00 a 14:00 (hora de Perú); en la hoja del caso es el viernes 27 de noviembre. Última sesión del curso. **Todo el minutado es una PROPUESTA** (no son duraciones medidas): lo medido son los tiempos en Actions del laboratorio de agentes (22 y 23/11/2026): CI 4 min 7 s; «igual» 1 min 16 s; evaluación en el runner 780 s (run completo 15 min 30 s); «prompt-nuevo», unos 14 min de trabajo más la aprobación; rollback 1 min 24 s. Lo de Google Cloud, **sin verificar**: hoy no se crea nada allí.

Material: [`teoria/README.md`](teoria/README.md) · [`practica/guia-laboratorio.md`](practica/guia-laboratorio.md) · [`laboratorio-agentes/guia.md`](laboratorio-agentes/guia.md) y [diapositivas](laboratorio-agentes/index.html) · laboratorio de MLOps clásico: `laboratorio-mlops/` (**en construcción** cuando se escribió este guion: usa su guía y completa los «Qué decir» de ese bloque con ella) · [`tarea/README.md`](tarea/README.md) · [`tarea/rubrica.md`](tarea/rubrica.md) · [`checklist.md`](checklist.md).

## Mensajes que no deben perderse
1. **Operar es una disciplina, no una tarea al final.** Cinco preguntas: qué está sirviendo, con qué se hizo, si sigue funcionando, cómo lo cambio y cómo lo deshago.
2. **El servicio sano no es el modelo bueno.** Se miden por separado.
3. **La deriva de datos avisa; la de rendimiento confirma, tarde** (la etiqueta del caso llega 90 días después).
4. **Un registro no lleva datos del cliente.** Ni claves.
5. **Un presupuesto avisa, no corta el gasto.** Se crea antes y se borra lo creado.
6. **Un agente es software más:** se prueba, se evalúa, se versiona, se aprueba y se puede deshacer. El modelo de ML decide; el LLM solo orquesta y redacta.
7. **Una puerta escrita después de ver el resultado no es una puerta.**
8. **Declarar lo no hecho no resta; fingirlo, sí.**

## Minuto a minuto (propuesta)

| Hora | Min | Bloque | Qué decir | Qué demostrar en vivo |
|---|---|---|---|---|
| 10:00–10:15 | 15 | **0 · Apertura y avance 4** | Es la última sesión. Qué se hace hoy y qué se entrega después (el 11 de diciembre a las 10:00, hora de Perú: repositorio, informe y demostración). Quién tiene problemas con Actions o el *environment*. | Nada: ver quién tiene su fork con `develop`, Actions y `produccion` configurados ([`checklist.md`](checklist.md)). |
| 10:15–10:35 | 20 | **1 · Teoría corta** | Las cinco preguntas; huella → ficha → imagen; servicio frente a calidad; PSI y su umbral como **convención**; por qué la etiqueta tarda 90 días. | Abrir `models/referencia.json` y `historial_versiones.json` de `04-Proyecto-Base` y recorrer huella, etiqueta de imagen y estado. |
| 10:35–11:25 | 50 | **2 · Laboratorio A: MLOps clásico** | Detectar un cambio en los datos, mover el alias del campeón y volver atrás, leer el monitoreo con alertas. Las salidas esperadas están en su guía. | Lo que diga la guía del laboratorio. Si no está listo: ver «Si algo falla». |
| 11:25–11:40 | 15 | **Pausa** | Pedir que, en la pausa, hagan el apartado 7.1 de la guía de agentes (la rama `lab/agente-s5` con los workflows copiados; **no lanza nada**). | — |
| 11:40–11:50 | 10 | **3 · L1 MCP** | Una herramienta es una función con contrato; la descripción es lo que el LLM lee; las herramientas **nunca lanzan** y no devuelven datos personales. | `python mi_cliente_mcp.py` (guía, 2.1): cinco herramientas y dos clientes. |
| 11:50–12:05 | 15 | **4 · L2 LLM local** | Local = sin claves ni coste por llamada, pero con límites que se miden. La tabla de tres modelos es **del profesor, no de tu máquina**. Usar el nombre `hf.co/...` (el corto falla detrás de un proxy). | Tu Ollama ya servido: `ollama list` y una pregunta. La descarga de 2,1 GB, **no en directo**. |
| 12:05–12:20 | 15 | **5 · L3 Agente en 100 líneas** | Un agente es un bucle con un LLM dentro; el LLM falso hace el bucle rápido y siempre igual; la traza demuestra el recorrido. | `agente_falso.py` (4.1) y la traza en MLflow (4.3). En cuanto empiece, lanzar «CI» (7.2) en tu fork: tarda unos 4 min y se mira después. |
| 12:20–12:30 | 10 | **6 · L4 Skills** | Una skill es una carpeta; `activar_si` es para lo que no puede depender de que un LLM pequeño se acuerde; una coma cambia la huella. | `skills.activadas(...)` con «Ofrécele un 50 % de descuento» (apartado 5). |
| 12:30–12:55 | 25 | **7 · L5 E2E y evaluación** | Seis niveles; el LLM falso es un oráculo (prueba del sistema, no del LLM); 25 preguntas de oro con cifras calculadas; **el evaluador también se prueba** (64 % → 96 %); la puerta, en su orden. | `evaluar --llm falso` (100 %) y las cifras del 3B de la guía (6.5), sin esperar los 14 min. Lanzar «igual» (7.3). |
| 12:55–13:30 | 35 | **8 · L6 Desplegar en GitHub** | La rama elige el escenario; «igual» no gasta LLM; «rechazo» es un resultado válido; «prompt-nuevo» espera aprobación; el rollback restaura git, **no** mueve MLflow de verdad. | Lanzar **«prompt-nuevo» el último** (bloquea a los siguientes); aprobar con *Review deployments*; fusionar el PR (7.7); lanzar el rollback (7.8). Para «rechazo» y la evaluación en el runner, **ver «Si algo falla»** (los runs de referencia). |
| 13:30–13:45 | 15 | **Colchón** | Runs que tardan, preguntas, atascados. | Lo que haga falta. |
| 13:45–14:00 | 15 | **9 · Tarea, costes y cierre** | Qué se entrega y cómo: (a) a (f) de la tarea; la demostración, **«la que indique el instructor»** (decide antes y dilo). Honestidad. Costes: borrar lo creado. | Abrir la [tarea](tarea/README.md) y la [plantilla de evidencia](evidencias/plantilla-avance-5.md). Recordar parar el Codespace. |

Total: 15 + 20 + 50 + 15 + 10 + 15 + 15 + 10 + 25 + 35 + 15 + 15 = **240 min**.

## Orden de lanzamiento de los workflows (propuesta)
- **Durante la pausa:** cada alumno deja lista `lab/agente-s5` (no lanza nada).
- **Al empezar L3:** «CI» (`lab/agente/ci`), unos 4 minutos y no bloquea a nadie.
- **Al empezar L5:** «igual» (`lab/agente-version/igual`), 1 min 16 s, **sin LLM**. Si da tiempo y el grupo va bien, la evaluación en el runner (`lab/agente-evaluar/3b`, 15 min 30 s).
- **Al empezar L6:** «prompt-nuevo», **el último**: queda **esperando la aprobación** y bloquea a los siguientes del mismo grupo (también al rollback). Se aprueba, se fusiona el PR y después se lanza el rollback desde esa rama.
- «Rechazo» (13 min 37 s en rojo): **mostrar el run de referencia** (nº 45067472249) en lugar de lanzarlo por alumno, salvo que sobre tiempo. **Sin dato** de si dos runs del mismo grupo se cancelan o se esperan en una cuenta distinta a la del profesor: pruébalo antes.
- Rollback a la v1: **parado a propósito** (nº 45277896553, la v1 nunca se publicó); la variante `…-sin-comprobar` (nº 45278456252) ensaya el mecanismo completo.

## Si algo falla en directo

| Síntoma | Respuesta |
|---|---|
| El laboratorio de MLOps clásico no está listo o falla | No se bloquea la sesión: se explica con la teoría (apartados 3 y 6) y se enseñan sus salidas si existen. Anotar la causa en el registro de incidencias. **Sin dato** de su estado el día de esta redacción. |
| Una ejecución se queda «Pending» | Un run de `agente-version` espera aprobación y bloquea al siguiente: cancélalo o apruébalo. |
| La publicación no pide aprobación | El *environment* `produccion` no existe o no tiene revisores: [`CONFIGURAR-REPOSITORIO.md`](laboratorio-agentes/CONFIGURAR-REPOSITORIO.md). |
| El último trabajo falla al abrir el PR | Falta «Allow GitHub Actions to create and approve pull requests». Activarlo y relanzar el trabajo 4. |
| No aparece ninguna ejecución en un fork | Actions desactivado (aceptar el aviso en la pestaña Actions) o la rama no coincide con el disparador. |
| El fork no tiene `develop` | Se creó con «Copy the main branch only» marcada: crear la rama desde el fork a mano o rehacer el fork (con la casilla desmarcada). |
| `git push` da 403 | El gestor de credenciales tiene otra cuenta de GitHub: `git-credential-manager github login --username <usuario> --device`. |
| Ollama no baja el modelo (`unexpected EOF`) | Nombre corto o proxy: usar `hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF:Q4_K_M`. Si no hay tiempo, seguir con el LLM falso. |
| El Codespace del docente no responde | Todo lleva capturas y salidas reales; seguir con ellas. |
| La evaluación da otras cifras que la guía | El LLM no es determinista y la máquina es otra: comparar con la tolerancia, no a igualdad. |
| `0xc06d007f` al importar `scikit-learn` (Windows con conda) | `conda activate` el entorno (no llamar al `python.exe` a pelo). |
| Alguien pregunta por precios, créditos o cuotas de GCP | «Sin verificar; consulta la página oficial y anota lo que veas con la fecha». Sin cifras. |
| Preguntan si el agente es fiable | Mostrar los seis fallos del 3B (6.5) y el «sin inventar»: se mide, no se promete. |

## Si el tiempo se descontrola (orden de recorte)
1. L2: pasa a demostración del docente y autoestudio.
2. «Rechazo» y la evaluación en el runner: se enseñan los runs de referencia.
3. L4: lectura rápida.
4. **No se recortan:** la deriva y el alias (laboratorio A), la puerta de calidad (L5), la aprobación y el rollback (L6) ni la tarea y el cierre.

## Solo para el instructor (no compartir antes de que lo midan)
En Bank Marketing, la evaluación por orden de filas muestra una deriva muy fuerte: según las notas de preparación ([`02-Proyecto-Transversal/enunciado/README.md`](../../02-Proyecto-Transversal/enunciado/README.md), que **no se enlaza al alumnado**) la proporción de síes pasa del 5,6 % en entrenamiento al 38,5 % en prueba y el AUC cae hacia el azar. **No des estas cifras:** pide que cada alumno las mida en su copia y que expliquen la diferencia, como pide la tarea (d). Son medidas de las notas del curso, no de este repositorio de alumnos.

## Decisiones abiertas (del profesor)
- **Cómo y dónde es la demostración** (vídeo o sesión en vivo): decídelo y dilo en el cierre; la tarea dice «la que indique el instructor».
- **Pesos y topes de la rúbrica de la entrega final:** propuestos; confirmar.
- **Reparto de tiempos** del apartado anterior: propuesta; sobre todo, L2 y L6.
- **Cuánto del laboratorio A** y qué sale en su guía: pendiente de su cierre.
- **Nombre de la rama** (`avance-5`) y la fecha de entrega ya fijada (11 de diciembre, 10:00, hora de Perú).

## Registro de incidencias
Paso / esperado / obtenido / mensaje / acción. Sin credenciales ni identificadores. Prestar atención a: Actions en los fork, ejecuciones en cola, el *environment* sin revisores y el Codespace.
