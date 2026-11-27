# Checklist S5

Plan de hoy (10:00–14:00, hora de Perú): teoría corta, laboratorio de MLOps clásico (deriva, alias `champion`, monitoreo), laboratorio de agentes (L1 a L6) y la tarea final. **Hoy no se crea nada en Google Cloud.** Guía de la sesión: [`practica/guia-laboratorio.md`](practica/guia-laboratorio.md) · guion: [`guion.md`](guion.md).

## Antes de la sesión (docente)
- [ ] **Fork propio** del repositorio del curso con la rama `develop` copiada: al crearlo, **desmarcada** la casilla «Copy the main branch only». Comprobar que existe `develop`.
- [ ] **Actions activado** en el fork (pestaña Actions; los cuatro workflows «Agente · …» visibles tras copiarlos a `.github/workflows/`, según [`laboratorio-agentes/guia.md`](laboratorio-agentes/guia.md), 7.1).
- [ ] ***Environment* `produccion` con revisores** (tú mismo) y el permiso «Allow GitHub Actions to create and approve pull requests»: [`CONFIGURAR-REPOSITORIO.md`](laboratorio-agentes/CONFIGURAR-REPOSITORIO.md) y el de S4. Sin revisores, la publicación no espera.
- [ ] **Codespace propio** desde `develop`, arrancado y con `04-Proyecto-Base` preparado (`python -m ia_mlops.operacional`, `python -m ia_mlops.pipeline`, `python -m ia_mlops.explotacion`), y las pruebas en verde.
- [ ] **Ollama del docente servido** (puerto `11435` por defecto) con el modelo `hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF:Q4_K_M` ya descargado (2,1 GB: **no se baja en directo**). `mcp==1.30.0` instalado.
- [ ] **Runs de referencia a mano**, por si los runners van lentos: CI (nº 45067003924), «igual» (45067009924), evaluar (45067018776), «rechazo» (45067472249), «prompt-nuevo» (45069539053), rollback parado (45277896553) y rollback con PR (45278456252), en la cuenta del profesor; y los de tu fork, si los repites.
- [ ] **Ninguna ejecución esperando aprobación** de otra prueba (bloquea a las demás del grupo): cancelarla o aprobarla.
- [ ] **Laboratorio de MLOps clásico** (`laboratorio-mlops/`) con su guía revisada y su material probado; qué hace falta en el Codespace, según esa guía. *(En construcción cuando se escribió este checklist: comprobar su estado.)*
- [ ] Capturas de respaldo abiertas en pestañas ([`laboratorio-agentes/img/`](laboratorio-agentes/img/) y las de S4).
- [ ] **Decidir y anunciar**: cómo es la demostración (vídeo o sesión en vivo), los pesos de la rúbrica final y quién lee el formulario.
- [ ] Tener a mano el enlace del **formulario de Google del curso** y el usuario de GitHub del instructor (para repositorios privados).
- [ ] Repasar el bloque de costes **sin cifras**: nada de precios, créditos ni cuotas de GCP: «sin verificar; consulta la página oficial».
- [ ] Enlaces abiertos: [`teoria/README.md`](teoria/README.md), [`tarea/README.md`](tarea/README.md), [`tarea/rubrica.md`](tarea/rubrica.md), [`evidencias/plantilla-avance-5.md`](evidencias/plantilla-avance-5.md) y este checklist.

## Antes de la sesión (alumnado)
- [ ] Avance 4 entregado (el del pipeline orquestado), según indique el instructor.
- [ ] **Fork** del repositorio del curso con `develop` (casilla «Copy the main branch only» **desmarcada**) y **Actions activado**.
- [ ] ***Environment* `produccion`** con revisores (tú) y permiso de PR configurados (los de S4, si ya los hiciste, valen).
- [ ] **Codespace** desde tu fork en `develop`, con `04-Proyecto-Base` preparado como arriba; o tu equipo local con el entorno de S4.
- [ ] El **repositorio de tu caso propio** (el de los avances) a mano: es el de la tarea.
- [ ] Opcional: Ollama y el modelo ya bajados (2,1 GB; usa el nombre `hf.co/...`).

## Durante la sesión (alumnado)
- [ ] Laboratorio A: sabes **qué cambió** en los datos, **cuál es el campeón** y **cómo vuelves atrás** moviendo un puntero (ver su guía).
- [ ] L1 a L4: el servidor MCP responde, el agente con LLM falso da `['version_en_produccion'] 2`, y entiendes qué hace una skill.
- [ ] L5: con el LLM falso, **25 preguntas y 100 %** (prueba del sistema); sabes qué miden `acierto_herramienta` y `sin_inventar` y en qué orden decide la puerta.
- [ ] L6: «CI» en verde; «igual» en verde con los trabajos 2 a 4 omitidos; «prompt-nuevo» esperando y aprobado; PR fusionado; rollback (con el run y el PR). **Enlaces copiados.**
- [ ] Entiendes la diferencia entre **el servicio sano** y **el modelo bueno**, y por qué la deriva de rendimiento tarda 90 días en el caso Retail.
- [ ] Tarea (a) a (f) entendida y [`evidencias/plantilla-avance-5.md`](evidencias/plantilla-avance-5.md) descargada.
- [ ] Ninguna run en espera de aprobación al terminar.

## Después de la sesión (alumnado, antes del viernes 11 de diciembre, 10:00)
- [ ] Rama `avance-5` con el `README.md` reproducible, los workflows y las pruebas en verde (última ejecución enlazada).
- [ ] Una nueva versión con **puerta escrita antes**, decisión explicada (aceptada o rechazada), aprobación y **rollback** comprobado.
- [ ] Una comprobación de **deriva o monitoreo** de tu caso (con umbral y alerta) y/o la evaluación por orden de filas.
- [ ] Informe corto y demostración (vídeo o sesión, según indique el instructor).
- [ ] **Sin secretos**, sin datos del cliente en los registros, sin claves en capturas.
- [ ] **Limpieza:** cancelar los runs esperando aprobación; cerrar los PR de ensayo sin fusionar; **parar o borrar el Codespace**; y **borrar lo creado en la nube** (en S5 no hace falta crear nada: comprobar que no queda nada vivo y que, si usaste facturación, hay un presupuesto con alertas, que **avisa pero no corta el gasto**).
- [ ] Evidencia completada y entrega con el formulario de Google del curso.

## Después de la sesión (docente)
- [ ] **Parar o borrar** el Codespace propio y el de pruebas.
- [ ] Cancelar o aprobar cualquier run pendiente de tu fork.
- [ ] Apuntar incidencias: Actions en fork, ejecuciones en cola, *environment*, Ollama, laboratorio de MLOps.
- [ ] Actualizar el estado de lo **sin verificar** ([`laboratorio-agentes/guia.md`](laboratorio-agentes/guia.md), apartado 10) con lo que ocurrió en vivo (el agente en un Codespace, `@champion` con el LLM real, etc.).
- [ ] Confirmar la rúbrica final y publicar el enlace de la demostración.
- [ ] Revisar que no queda **ningún recurso de GCP** creado para el curso en esta sesión (no debería haber).

## Registro de incidencias
Paso / esperado / obtenido / mensaje / acción. Sin credenciales ni identificadores.
