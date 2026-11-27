# S5 · Guía de la práctica: orden de la sesión y de los laboratorios

Esta guía **no repite** los pasos de cada laboratorio: dice en qué orden se hacen, qué se aprende en cada uno, dónde está su guía y qué hace falta tener listo. Los pasos, las órdenes y los «qué debes ver» están en las guías de cada laboratorio.

> **El hilo de la sesión.** Primero se opera el **modelo** (¿cambiaron los datos?, ¿cuál es el campeón?, ¿cómo vuelvo atrás?) y después el **agente** que lo usa, con el mismo ciclo: se prueba, se evalúa, se versiona, se aprueba y se puede deshacer. Teoría de apoyo: [`teoria/README.md`](../teoria/README.md).

> **Reparto de tiempos: PROPUESTA.** Los minutos de abajo son una propuesta de reparto de las 4 horas, **no duraciones medidas**. Lo único medido son los tiempos de ejecución en Actions (runner de GitHub, 22 y 23/11/2026): CI del agente 4 min 7 s; escenario «igual» 1 min 16 s; **evaluación del agente 780 s** (el run entero, 15 min 30 s); nueva versión completa unos 14 min de trabajo más la aprobación (unos 10 min en el laboratorio de producción de S4, sin la evaluación con LLM); lote **unos 3 min**. Cuánto tarda cada alumno en sus laboratorios: **sin dato**.

## 1. Materiales y estado

| Laboratorio | Qué es | Dónde está | Estado |
|---|---|---|---|
| **A · MLOps clásico** | Deriva de datos y de rendimiento (PSI entre cortes), alias `champion` del modelo de retención con rollback moviendo el alias, y un workflow de monitoreo con alertas | Laboratorio de MLOps clásico: `laboratorio-mlops/` (esta misma sesión; **ver su guía**). Aún no está enlazado aquí porque lo termina otro equipo | **En construcción** al escribir esta guía: su contenido exacto y sus tiempos están en su guía, no aquí |
| **B · Agentes** (L1 a L6) | MCP, LLM local con Ollama, skills, evaluación con 25 preguntas de oro, puerta de calidad y 4 workflows de Actions (CI, evaluar, nueva versión con aprobación, rollback) | [`laboratorio-agentes/guia.md`](../laboratorio-agentes/guia.md) · [diapositivas](../laboratorio-agentes/index.html) (29) · [`CONFIGURAR-REPOSITORIO.md`](../laboratorio-agentes/CONFIGURAR-REPOSITORIO.md) | Ensayado en Actions el 22 y 23/11/2026; lo **sin verificar** está en el apartado 10 de su guía |
| **Reutilizado de S4** | API e interfaz del caso Retail (`04-Proyecto-Base`), workflows de producción, Cloud Journey y prácticas de GCP, clase «de on-premise a la nube» | [laboratorio de producción](../../S4-Orquestacion-y-CI-CD/laboratorio-produccion-e2e/guia.md) · [Cloud Journey](../../S4-Orquestacion-y-CI-CD/laboratorio-cloud-journey/guia.md) · [prácticas de GCP](../../S4-Orquestacion-y-CI-CD/practicas-gcp/README.md) · [clase on-premise a la nube](../../S4-Orquestacion-y-CI-CD/clase-onpremise-a-nube/guia.md) | Se usan como base y como consulta; en S5 **no se crea nada en Google Cloud** |

## 2. Antes de empezar (una sola vez, cada alumno)

Lo que necesita **todo** el que haga los laboratorios (el docente lo comprueba con [`checklist.md`](../checklist.md)):

1. Un **fork** del repositorio del curso con la rama `develop` incluida: al crearlo, **desmarca «Copy the main branch only»**. Sin eso, el fork no tiene `develop`.
2. **Actions activado** en el fork (pestaña **Actions**, aceptar el aviso).
3. El *environment* `produccion` con **revisores** y el permiso «Allow GitHub Actions to create and approve pull requests»: [`CONFIGURAR-REPOSITORIO.md`](../laboratorio-agentes/CONFIGURAR-REPOSITORIO.md) (remite al de S4, con capturas). Si ya lo hiciste en S4, no hay nada que hacer.
4. Un **Codespace** desde tu fork en `develop` (o tu equipo local), con `04-Proyecto-Base` y sus datos preparados: `python -m ia_mlops.operacional`, `python -m ia_mlops.pipeline` y, para el agente, `python -m ia_mlops.explotacion` ([guía de agentes](../laboratorio-agentes/guia.md), apartado 1).

## 3. El orden de la sesión (propuesta de 240 min)

| # | Bloque | Min (propuesta) | Qué se aprende | Material |
|---|---|---|---|---|
| 0 | Apertura y avance 4 | 15 | Cómo va el grupo; qué se entrega después de S5 | [`guion.md`](../guion.md) · [`tarea/README.md`](../tarea/README.md) |
| 1 | Teoría corta: versionar, medir, derivar, alertar, deshacer | 20 | El mapa de las cinco preguntas; deriva de datos frente a deriva de rendimiento | [`teoria/README.md`](../teoria/README.md) (apartados 0 a 3 y 6) |
| 2 | **Laboratorio A · MLOps clásico** | 50 | Detectar un cambio en los datos, mover el alias del campeón y volver atrás, y leer un monitoreo con alertas | `laboratorio-mlops/` (ver su guía) |
| 3 | Pausa | 15 | | |
| 4 | **B · L1 Mi primer servidor MCP** | 10 | Una herramienta MCP es una función con contrato; el LLM no ve tu base de datos | [guía de agentes, apartado 2](../laboratorio-agentes/guia.md) |
| 5 | **B · L2 Un LLM en mi portátil** | 15 | Local = sin claves ni coste por llamada, pero con límites que se miden (**demostración del docente**; lo demás, autoestudio) | [apartado 3](../laboratorio-agentes/guia.md) |
| 6 | **B · L3 Un agente en 100 líneas** | 15 | Un agente es un bucle con un LLM dentro, y la traza lo demuestra | [apartado 4](../laboratorio-agentes/guia.md) |
| 7 | **B · L4 Skills** | 10 | Separar el saber hacer del negocio del código y del prompt | [apartado 5](../laboratorio-agentes/guia.md) |
| 8 | **B · L5 E2E y evaluación** | 25 | Se evalúa con datos; la puerta de calidad; un evaluador también se prueba | [apartado 6](../laboratorio-agentes/guia.md) |
| 9 | **B · L6 Desplegarlo en GitHub** | 35 | Los cuatro workflows, la aprobación, el PR y el rollback | [apartado 7](../laboratorio-agentes/guia.md) |
| 10 | Colchón (retrasos, preguntas, runs en cola) | 15 | | |
| 11 | Tarea, costes y cierre | 15 | Qué se entrega y cómo; qué se borra; costes | [`tarea/README.md`](../tarea/README.md) · [`tarea/rubrica.md`](../tarea/rubrica.md) |

Suma: 15 + 20 + 50 + 15 + 10 + 15 + 15 + 10 + 25 + 35 + 15 + 15 = **240 min**.

**Por qué este orden.** La deriva y el alias del modelo van primero porque son la base conceptual (qué hay en producción y cómo se cambia). El agente después, porque reutiliza exactamente la misma idea: huella, puerta de calidad, aprobación y rollback. Si se invirtiera, el rollback del agente se vería como un truco y no como lo que es: un alias que se mueve.

**Dos decisiones del reparto que debe confirmar el instructor** (están abiertas):
- **L2 con Ollama no cabe en 15 min para todo el grupo:** el modelo pesa 2,1 GB y la descarga y la primera respuesta tardan (16 s la primera, según la guía). La propuesta es demostración del docente con su Ollama ya servido y autoestudio para el resto.
- **Los workflows de L6 se solapan con L5:** la evaluación en el runner tarda 780 s y la nueva versión se queda esperando la aprobación. Lanzar «CI» e «igual» durante L4 o L5 y dejar para L6 solo los escenarios con espera es una forma de que el tiempo no se vaya mirando una pantalla; el orden detallado está en el guion.

## 4. Qué hace cada laboratorio, en una línea y con su evidencia

**A · MLOps clásico** *(ver su guía para los pasos y las salidas esperadas)*
- Deriva: comparar los datos de otro periodo con los de entrenamiento con un índice (PSI), y entender por qué el rendimiento solo se mide tarde.
- Alias `champion`: apuntar el alias a una versión del modelo de retención y volver atrás moviéndolo.
- Monitoreo: un workflow que se pone en rojo si se cruza un umbral.
- **Qué te llevas para la tarea:** una comprobación de deriva o de monitoreo adaptada a tu caso y un rollback moviendo un puntero.

**B · Agentes** *(pasos en [`laboratorio-agentes/guia.md`](../laboratorio-agentes/guia.md))*

| | Qué haces | Cómo sabes que va bien |
|---|---|---|
| L1 | Arrancas `mcp-retencion` y lo llamas con un cliente de 20 líneas | Salen las cinco herramientas y un JSON con dos clientes |
| L2 | Ollama y el modelo Qwen2.5-3B (tabla de tres modelos) | Una respuesta de una frase; la tabla es del pico del profesor, **no la tuya** |
| L3 | El bucle con el LLM falso, la CLI con el LLM real y las trazas en MLflow | `['version_en_produccion'] 2` y una traza guardada |
| L4 | Las skills `guion-de-llamada`, `informe-semanal` y `cumplimiento` | La pregunta del descuento activa `cumplimiento` sin que el LLM haga nada |
| L5 | Seis niveles de prueba, 25 preguntas de oro y la puerta de calidad | Con el LLM falso, 25 preguntas y 100 % (es la prueba del sistema, no del LLM) |
| L6 | Cuatro workflows en ramas `lab/…` | Verde en «CI» e «igual»; «rechazo» en rojo a propósito; «prompt-nuevo» esperando aprobación; rollback con PR |

## 5. Para quien vaya rápido o lento

- **Rápido:** completa L5 con el LLM real (las 25 preguntas tardaron unos 14 minutos en un portátil de 14 hilos sin GPU) y lanza el escenario de evaluación en el runner (`lab/agente-evaluar/3b`, 15 min 30 s).
- **Lento o sin Ollama:** sigue con el LLM falso (L3 a L5 se pueden recorrer con él). En L6 no hace falta Ollama en tu máquina: «CI» usa el LLM falso, «igual» no usa LLM y los escenarios con evaluación instalan Ollama **dentro del runner**.
- **Sin repositorio propio de GitHub ese día:** no se pueden hacer los workflows; sigue las capturas de la guía y decláralo en la evidencia (con el error exacto).
- **El extra de dos agentes** no existe: es solo una propuesta (apartado 8 de la guía de agentes).

## 6. Al terminar (cada alumno)

1. Anota los **enlaces de las ejecuciones** que hayas hecho (CI, «igual», «rechazo», «prompt-nuevo», rollback): te sirven para la tarea.
2. **Cancela o aprueba** el run que esté esperando aprobación: bloquea a los siguientes del mismo grupo.
3. **Para o borra tu Codespace** al terminar la sesión (cuesta horas de uso). Y no dejes ejecuciones en cola.
4. Lo que hayas creado en Google Cloud (**no debería haber nada**: S5 no crea recursos): comprueba que no hay nada vivo.
5. Si no pudiste hacer algo, apúntalo con el error exacto: es parte de la evidencia.
