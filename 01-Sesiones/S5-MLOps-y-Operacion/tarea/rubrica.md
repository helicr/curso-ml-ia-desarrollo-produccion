# Rúbrica de la tarea S5 · entrega final (100 puntos)

Es la rúbrica de la entrega final de tu caso: los mismos tres criterios y pesos que S1, S2 y S3 y que [`rubrica-avance.md`](../../../02-Proyecto-Transversal/alumno/rubrica-avance.md). Esa hoja dice que **el peso de cada avance en la nota final y la rúbrica de la entrega final están por definir**: todo lo de aquí es una **propuesta** hasta que el instructor la confirme (fecha de entrega: **viernes 11 de diciembre, a las 10:00, hora de Perú**). La parte de la nube se evalúa igual **con o sin** ella: no usarla no resta; fingir que se hizo algo, sí.

| Criterio | Peso | Qué se observa |
|---|---|---|
| **Reproducibilidad** | 20 | Otra persona clona tu rama `avance-5`, sigue el `README.md` y obtiene lo que cuentas: pasos en orden, versiones fijadas, cómo llegan los datos, fuente del dato citada. Los workflows **se ejecutaron de verdad**: hay **enlaces** a las ejecuciones citadas y la última de la rama está en verde. Sin secretos en el repositorio. |
| **Técnica** | 40 | Pipeline y pruebas en verde (`duration` fuera, con su prueba); **una nueva versión con puerta de calidad** escrita antes del resultado, que decide con una ficha de referencia; **aprobación humana** y PR; **rollback** sin borrar nada y comprobado; **comprobación de deriva o de monitoreo** con umbral y alerta; permisos mínimos; ningún secreto; nada vivo en la nube. |
| **Análisis y decisión** | 40 | Una decisión (aceptada o rechazada) **explicada con cifras**: métrica, tolerancia, cambio observado y alternativas; qué significa la deriva en tu caso y por qué el rendimiento se mide tarde; limitaciones y costes; **lo que no se hizo, con el error exacto**; ayuda recibida (incluida IA) citada. |

## Qué se observa en cada parte (propuesta)

| | Lo mínimo para «Logrado» | Lo que lleva a «Sobresaliente» |
|---|---|---|
| Repositorio y README | Pregunta, estructura, versiones y comandos en orden; pruebas en verde; fuente del dato | Además: un tercero lo reproduce sin ayuda y el README dice qué cambia al cambiar de máquina |
| Workflows | Se ejecutan, están en verde, con permisos mínimos y enlaces a las ejecuciones | Además: caché, `timeout-minutes`, `concurrency` y el rojo que tuviste, explicado |
| Nueva versión y puerta | Ficha de referencia y puerta con métrica y tolerancia **escritas antes**; decisión con las cifras | Además: la tolerancia razonada (¿cuánta variación es azar? ¿repetiste con otra semilla?) y qué harías con una versión «igual» |
| Aprobación y rollback | Aprobación humana y un rollback ensayado, con ficha e historial coherentes antes y después | Además: se entiende **qué no se restaura** (por ejemplo, lo que nunca se publicó) y se comprueba el estado tras volver |
| Deriva o monitoreo | Una comprobación con código y resultado, y qué compara con qué | Además: umbral justificado, alerta que se pone en rojo de verdad y por qué el rendimiento se ve tarde en tu caso |
| Informe | Limitaciones, costes y lo no ejecutado, en lenguaje claro | Además: riesgos priorizados y qué harías con una semana más |
| Demostración | Muestra el repositorio, una ejecución en verde, la decisión y el rollback, sin datos sensibles | Además: se oye el porqué de cada decisión, no solo el qué |

## Niveles por criterio

| Nivel | Reproducibilidad (20) | Técnica (40) | Análisis (40) |
|---|---|---|---|
| Sobresaliente | 18–20 · un tercero reproduce sin ayuda y las ejecuciones enlazadas lo confirman | 36–40 · todo en verde; versión candidata con puerta previa, aprobación y rollback comprobados; deriva con umbral y alerta | 36–40 · decisión clara con cifras, alternativas, riesgos, costes y lo no hecho declarado |
| Logrado | 14–17 | 28–35 | 28–35 |
| En proceso | 8–13 · faltan pasos, versiones o algún enlace | 16–27 · falta la puerta, la aprobación, el rollback o la comprobación de deriva, o la puerta se escribió viendo el resultado | 16–27 · cifras y enlaces pegados sin interpretar |
| Insuficiente | 0–7 | 0–15 | 0–15 |

## Qué riesgos se esperan reconocidos
Elige los que correspondan a tu caso y explica qué harías:
- **Una puerta escrita después de ver el resultado** no es una puerta: decide lo que ya sabías.
- **Una tolerancia sin razón**: ¿cuánto cambia tu métrica solo por el azar de la partición o de la semilla?
- **Deriva de datos no es deriva de rendimiento**: una alerta de datos no prueba que el modelo falle.
- **La partición aleatoria es optimista**; la evaluación por orden de filas enseña lo que escondía.
- **Un rollback a lo que nunca se publicó no existe**; y **git y el registro de modelos son dos sitios**: restaurar uno no mueve el otro.
- **Un token o una clave** en el repositorio, en los registros o en una captura da acceso a quien lo vea.
- **Un recurso de la nube olvidado sigue cobrando**; un presupuesto con alertas avisa, pero no corta el gasto (compruébalo en la documentación vigente).
- **Datos del cliente en los registros.**
- Lo que **no** pudiste hacer y el error exacto.

## Descuentos y alertas
Topes **propuestos** para esta entrega, en línea con los de [`rubrica-avance.md`](../../../02-Proyecto-Transversal/alumno/rubrica-avance.md) y [S3](../../S3-Despliegue-y-Redes-Neuronales/tarea/rubrica.md):
- **Una credencial o un token en el repositorio** (también en un workflow, en su registro o en capturas): la técnica no supera 25.
- **`duration`, o cualquier variable que no se conozca antes de llamar, entra en el modelo**: la técnica no supera 15, aunque mejore la métrica.
- **Un workflow que nunca se ejecutó, o que solo se demuestra con capturas** sin enlace a las ejecuciones: la reproducibilidad no supera 8.
- **Sin cita de la fuente del dato**: la reproducibilidad no supera 15.
- **Presentar como hecho lo que no se hizo** (un rojo que no existe, una aprobación que nadie dio, un rollback que no se ensayó, una ejecución que no está) **u ocultar un fallo**: el análisis no supera 20. **Declarar con el error exacto lo no ejecutado no resta.**
- **El verde o la decisión se consiguieron cambiando la puerta o la prueba después de ver el resultado**, sin decirlo: la técnica no supera 25 (propuesta).
- **No se dice que la partición aleatoria es optimista** al comparar con la evaluación por orden de filas: el análisis no supera 25.
- **Recursos de la nube sin borrar** o con facturación y **sin presupuesto previo**: el análisis no supera 25 (propuesta). No se aplica si no se creó nada.
- **Datos de clientes en los registros** o en la evidencia: la técnica no supera 25 (propuesta).
- **No citar la ayuda recibida** (incluida la de IA): la reproducibilidad no supera 15 (propuesta).

## Lo que no se evalúa
- Que tu métrica sea alta. No hay modelo de referencia: una decisión de «rechazada» bien argumentada vale tanto como una de «aceptada».
- Que uses la nube ni cuánto gastaste (no hace falta gastar nada).
- Que uses una herramienta u otra, mientras puedas justificarla y reproducirla.
- Cuántos workflows tienes: cuenta que funcionen, estén enlazados y se entiendan.
