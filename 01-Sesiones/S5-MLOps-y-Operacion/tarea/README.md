# Tarea S5 · Consolidar repositorio, informe y demostración

**Esta tarea es la entrega final de tu caso propio (Bank Marketing).** No hay un ejercicio aparte sobre Online Retail II: lo que has visto en los laboratorios del caso Retail lo aplicas a **tu** caso.

**Entrega posterior a S5: viernes 11 de diciembre, a las 10:00 (hora de Perú)** · tu repositorio personal, rama `avance-5` (o carpeta comprimida si no hay repositorio, aunque entonces las partes con Actions no se pueden demostrar: ver «Honestidad»). Se entrega con el **formulario de Google del curso** (el instructor da el enlace en clase): tu nombre, «entrega final», el enlace a tu rama o carpeta, el enlace al informe y a la demostración, y «qué no pude ejecutar». Si tu repositorio es privado, añade al instructor como colaborador (su usuario lo indica en clase) para que pueda ver el código y las ejecuciones. Para ramas: [`git-y-ramas.md`](../../../07-Recursos/guias/git-y-ramas.md).

> **Sin sesión de presentación.** Tras S5 no hay sesión asignada en el calendario del curso. Dónde y cómo se hace la demostración (vídeo corto o sesión en vivo) **lo indica el instructor**; mientras tanto, prepara el vídeo, que sirve en los dos casos. La rúbrica y los pesos de la entrega final están marcados como **propuesta** hasta que el instructor los confirme.

## Qué se pide

Seis partes. Todas cuentan; la **(b)** y la **(c)** son las que más pesan. Parte de lo que ya tienes del avance 4 (el pipeline orquestado con GitHub Actions).

**(a) Repositorio consolidado, con un README reproducible.**
1. Una persona que clona tu rama `avance-5` encuentra en el `README.md` la **pregunta del caso**, la **estructura** del repositorio, las **versiones** (Python y librerías) y los **comandos en orden** para reproducirlo desde una copia limpia.
2. La **cita de la fuente del dato** (Moro, Rita y Cortez, 2014; licencia CC BY 4.0) y qué cambiaste del dato.
3. `duration` fuera del modelo, con la prueba que lo vigila, y `python -m pytest -q` en verde.
4. **Sin secretos**: ni claves, ni tokens, ni `.env`, ni el ID de tu proyecto, ni tu correo. Mira también los registros de los workflows y las capturas.

**(b) Workflow(s) de GitHub Actions en verde, con enlaces a las ejecuciones.** Tu pipeline del avance 4 (y las pruebas del avance 3) en `.github/workflows/`, con permisos mínimos (`permissions:`) y sin secretos. Entregas el **enlace a cada ejecución** que citas: una captura sin enlace no la demuestra. La **última ejecución de la rama `avance-5` está en verde**.

**(c) Una nueva versión con puerta de calidad, una decisión explicada y un rollback.**
1. **Una versión candidata** de tu modelo (por ejemplo, otro conjunto de variables, otro modelo o los datos de otro tramo). Pasa por una **puerta de calidad** que **escribiste antes de ver el resultado**: qué métrica, qué tolerancia y por qué.
2. La puerta la **compara con la versión de referencia** de tu repositorio (una ficha, como la `models/referencia.json` del caso Retail, con versión, huella de datos y métricas) y da una decisión: **aceptada** o **rechazada**. Las dos valen: lo que se evalúa es que la **expliques** con cifras (qué métrica, cuánto cambió, frente a qué tolerancia). Un rechazo bien argumentado vale tanto como una aceptación.
3. Una **aprobación humana** antes de que la candidata pase a ser «la de producción» (por ejemplo, el *environment* `produccion` con revisores y un PR que fusionas tú). Si tu caso no publica una imagen, la ficha y el historial de versiones bastan: dilo.
4. Un **rollback**: volver a la versión anterior **sin borrar nada** (restaurar la ficha desde el historial de git con un PR, o mover un alias del modelo en MLflow). Enlace a la ejecución o al PR, y qué comprobaste después de volver atrás.
5. Una **decisión** explicada: contexto, opciones, evidencia, decisión y riesgos (como en los avances anteriores).

Material de apoyo: el [laboratorio de producción de S4](../../S4-Orquestacion-y-CI-CD/laboratorio-produccion-e2e/guia.md) (`nueva-version.yml` y `rollback.yml`), el [laboratorio de agentes de S5](../laboratorio-agentes/guia.md) (la misma mecánica con otro objeto) y el laboratorio de MLOps clásico de esta sesión (`laboratorio-mlops/`: ver su guía). Lo que copies y lo que adaptes, anótalo.

**(d) Una comprobación de deriva o de monitoreo adaptada a tu caso.** Una de estas dos (o las dos), con código en tu repositorio y su resultado:
1. **La evaluación por orden de filas** que pide la hoja del caso ([apartado 8](../../../02-Proyecto-Transversal/alumno/tu-caso-bank-marketing.md)): el **mismo modelo** entrenado con las primeras filas y probado con las últimas. Compara con la partición aleatoria, explica la diferencia y **empieza por mirar qué proporción de síes hay en cada tramo**.
2. **Un monitoreo de deriva de datos** (por ejemplo, un índice como el PSI entre dos tramos de tus datos, como en el laboratorio de MLOps), con **un umbral que tú justificas** y una **alerta**: un workflow o prueba que se pone en rojo si se cruza.
- En las dos: di **qué** compararías con qué y **qué harías** si salta. Si hablas de deriva de rendimiento, explica por qué en tu caso se puede (o no) medir tarde.

**(e) Informe corto.** Un documento de **unas 3 a 5 páginas** (extensión orientativa, propuesta; `informe.md` en el repositorio o un PDF enlazado) con: qué hace tu caso y cómo está organizado; qué funciona y qué no; **limitaciones** (datos, partición, riesgos de la métrica); **costes** (qué uso de minutos de Actions, qué recursos de nube creaste y borraste, o «ninguno», con el apartado de costes de la [teoría](../teoria/README.md)); **qué no pudiste ejecutar** (error exacto); y las fuentes y la ayuda recibida.

**(f) Demostración.** Elige la que indique el instructor (**sin definir a la fecha de esta tarea**):
- **Vídeo corto** (duración orientativa, propuesta: unos **5 minutos**; enlace con acceso para quien lo tenga) que muestre: el repositorio, una ejecución en verde y una **decisión de la puerta de calidad**, el rollback y la comprobación de deriva. Habla de lo que ves, no leas.
- **Sesión en vivo**: el mismo recorrido en directo, en el tiempo que el instructor indique.
En los dos casos, **no se enseñan claves, tokens ni correos**.

## Dónde se hace
- En el repositorio de **tu caso** (el de los avances), con una rama `avance-5` desde la última que tengas al día.
- Los workflows son los tuyos: parte del `nueva-version.yml` y el `rollback.yml` de S4 o de los del agente, y adáptalos a tu caso (carpeta del proyecto, versión de Python, cómo se instalan tus dependencias, qué métrica usa tu puerta). **Lo que copies y lo que cambies, anótalo.**
- Si tus workflows necesitan datos, **decide cómo llegan al runner** y explícalo (CSV en el repositorio con la cita de su licencia, generados en el workflow o una muestra).
- **No hace falta Google Cloud.** Si lo usas (por ejemplo, para un despliegue), crea un presupuesto con alertas **antes** de nada, **borra lo creado** al terminar y dilo en el informe. Si no lo usas, di «ninguno».

## Pasos
1. Crea la rama `avance-5` y comprueba que `python -m pytest -q` sigue en verde.
2. Consolida el `README.md`: pregunta, estructura, versiones, comandos en orden, fuente del dato.
3. Escribe **la ficha de referencia** de tu modelo actual (versión, huella de los datos, métricas de test) y una **puerta de calidad** con su tolerancia, **antes** de entrenar la candidata.
4. Entrena la **candidata** y pasa la puerta. Anota la decisión con las cifras.
5. Añade la **aprobación** y el **PR** que actualiza la ficha y el historial. Fusiónalo si se acepta.
6. Haz el **rollback** y comprueba que la ficha y el historial dicen lo que deben.
7. Haz la **comprobación de deriva o de monitoreo** (d) y anota qué harías si salta.
8. Deja los workflows **en verde** y copia los enlaces de las ejecuciones.
9. Escribe el **informe** y prepara la **demostración**.
10. Completa [`evidencias/plantilla-avance-5.md`](../evidencias/plantilla-avance-5.md) (cópiala a tu repositorio). La [`plantilla-avance.md`](../../../02-Proyecto-Transversal/alumno/plantilla-avance.md) del caso aún no tiene una sección propia para la entrega final: si el instructor te la pide, usa sus apartados comunes (resultado, cómo se ejecuta, pruebas, decisión, lo que no pude ejecutar, fuentes) y enlaza esta evidencia.
11. **Limpieza:** nada vivo en la nube, sin secretos en el repositorio, y el Codespace, parado o borrado.
12. Comprueba que la última ejecución de `avance-5` está en verde y entrega con el formulario.

## Evidencia mínima
- El archivo de cada workflow y **el enlace a cada ejecución citada** (verde y, si hubo, roja con la causa).
- La **ficha de referencia** y el **historial de versiones** antes y después de la candidata y del rollback (los dos estados).
- La **decisión de la puerta** (aceptada o rechazada) con la métrica, la tolerancia y las cifras, y el enlace a la ejecución.
- El **PR** de la aprobación y el del rollback (o el mensaje del alias movido), con lo que comprobaste.
- La **comprobación de deriva o de monitoreo**: código, salida y umbral con su porqué.
- Salida de `python -m pytest -q` en tu Codespace.
- `informe.md` (o su PDF) y el enlace a la **demostración**.
- `evidencias/plantilla-avance-5.md` completada.

## Rúbrica
Ver [`rubrica.md`](rubrica.md): 20 % reproducibilidad, 40 % técnica, 40 % análisis y decisión (**propuesta**).

## Honestidad
No se evalúa solo por capturas. Si algo no lo pudiste hacer (sin repositorio en GitHub, Actions desactivado, sin permiso para abrir PR, un *environment* sin revisores, la nube, un fallo de tu equipo), escríbelo con el **error exacto**: **declararlo no resta; fingirlo, sí** (un rojo que no existe, una ejecución que no hiciste, una aprobación que nadie dio o un rollback que no ensayaste). Si algo salió mal y lo arreglaste, cuéntalo: un rojo explicado vale más que un verde sin historia. No pegues claves, tokens, el ID de tu proyecto, tu correo ni el identificador de tu cuenta de facturación (tapa también las capturas). **Cita la ayuda que recibiste** (personas, documentación y herramientas, **incluidas las de IA**) y para qué; si una IA te escribió un fragmento, dilo y di qué comprobaste tú.
