# Rúbrica de la tarea S4 · avance 4 (100 puntos)

Es la rúbrica del avance 4 de tu caso: los mismos tres criterios y pesos que S1, S2, S3 y [`rubrica-avance.md`](../../../02-Proyecto-Transversal/alumno/rubrica-avance.md). Lo que se observa en cada criterio es nuevo y está marcado como **propuesta** hasta que el instructor lo confirme. La parte de Google Cloud se evalúa igual **con nube que sin nube**: no tenerla no resta; fingir que se hizo algo, sí.

| Criterio | Peso | Qué se observa |
|---|---|---|
| **Reproducibilidad** | 20 | Otra persona clona tu rama `avance-4`, mira el workflow y la evidencia y puede repetir la ejecución. El workflow está en `.github/workflows/` y **se ejecutó de verdad**: hay enlaces a la ejecución en rojo, a la verde que la arregla y a la última de la rama (en verde), con sus commits. Versiones fijadas, cómo llegan los datos al runner explicado, artefactos descargables y comandos para repetirlo en local. |
| **Técnica** | 40 | Pipeline orquestado en etapas (datos → entrenamiento → métricas → artefacto) con **al menos dos trabajos unidos por `needs:`**; las pruebas corren antes de entrenar; se guarda un **artefacto** con el modelo y las métricas; disparo en `push` a `avance-4`; **permisos mínimos** (`contents: read` por defecto), `timeout-minutes` y **ningún secreto**; el **rojo viene de una comprobación del pipeline** (prueba o puerta de calidad) y el arreglo es un cambio real, no borrar ni saltar la comprobación. Opcional: *environment* con aprobación comprobada; MLflow; Google Cloud sin claves y con todo borrado. |
| **Análisis y decisión** | 40 | Las etapas explicadas (qué entra, qué sale, por qué en ese orden); **fallos encontrados** con síntoma, línea del registro, causa y arreglo; qué leíste en el registro para saber qué fallaba; diferencias entre tu Codespace y el runner, si las hubo; **una decisión argumentada** con evidencia y riesgos; qué harías después; y **lo que no se hizo**, dicho con claridad y con el error exacto. |

## Qué se observa en cada parte (propuesta)

| | Lo mínimo para «Logrado» | Lo que lleva a «Sobresaliente» |
|---|---|---|
| Etapas y trabajos | Cuatro etapas (datos, entrenamiento, métricas, artefacto) en al menos dos trabajos con `needs:`; pruebas antes de entrenar | Además: la tabla de etapas completa (entra / sale / dónde corre), caché de dependencias y `concurrency`, cada uno con su porqué |
| Artefactos | Un artefacto descargable con el modelo y las métricas | Además: lo que se pasa entre trabajos explicado, y MLflow registrado y subido como artefacto |
| Rojo → verde | Enlace a un rojo provocado por una comprobación del pipeline y a la verde del arreglo | Además: el registro del rojo leído e interpretado (qué línea, qué valor) y el arreglo explicado |
| Fallos | Dos fallos documentados con causa y arreglo | Además: los fallos de infraestructura (YAML, dependencias, datos, permisos) separados de los de comprobación, y qué cambió en el diseño por ellos |
| Permisos y secretos | `contents: read`, sin secretos, sin claves en el repositorio | Además: permisos ampliados solo en el trabajo que los necesita y justificados |
| Aprobación (opcional) | *Environment* con revisores y captura de que espera | Además: comprobado qué pasa si el nombre es otro o no existe |
| Google Cloud (opcional) | Si se hizo: sin claves guardadas (WIF) y **todo borrado**; si no, el motivo exacto | Además: variables (no secretos) y cuenta de servicio con permisos mínimos explicadas |

## Niveles por criterio

| Nivel | Reproducibilidad (20) | Técnica (40) | Análisis (40) |
|---|---|---|---|
| Sobresaliente | 18–20 · un tercero reproduce sin ayuda y las ejecuciones enlazadas lo confirman | 36–40 · pipeline en etapas con `needs:` y artefacto, permisos mínimos, rojo provocado por una comprobación real | 36–40 · etapas, fallos y decisión argumentados, riesgos y lo no hecho declarado |
| Logrado | 14–17 | 28–35 | 28–35 |
| En proceso | 8–13 · faltan pasos, versiones o algún enlace | 16–27 · el rojo no viene de una comprobación, o falta el artefacto, o un solo trabajo | 16–27 · enlaces y salidas pegados sin interpretar; un solo fallo documentado |
| Insuficiente | 0–7 | 0–15 | 0–15 |

## Qué riesgos se esperan reconocidos
Elige los que correspondan a tu caso y explica qué harías:
- Un pipeline que pasa en tu Codespace y falla en el runner (o al revés): datos que no están en el repositorio, versiones distintas, rutas absolutas.
- Perder el modelo o las métricas porque no se guardaron como artefacto (el runner se destruye).
- Una comprobación que no puede fallar no protege nada: ¿cómo sabes que la tuya sí?
- «Arreglar» el rojo borrando, saltando o relajando la comprobación.
- Un *environment* con otro nombre o inexistente: GitHub lo crea sin revisores y **no pide aprobación**.
- Un run esperando aprobación bloquea el siguiente del mismo grupo `concurrency`.
- Un token o una clave en el repositorio o en el registro del workflow da acceso a quien lo lea.
- Un recurso de Google Cloud olvidado sigue cobrando; una alerta de presupuesto avisa, pero no corta el gasto.
- Lo que **no** pudiste hacer y el error exacto.

## Descuentos y alertas
Topes **propuestos** para este avance, en línea con los de la rúbrica de S3 y con [`rubrica-avance.md`](../../../02-Proyecto-Transversal/alumno/rubrica-avance.md):
- **Una credencial o un token en el repositorio** (también en el workflow, en su registro o en capturas), o una clave JSON de cuenta de servicio: la técnica no supera 25.
- **Un workflow que nunca se ejecutó, o que solo se demuestra con capturas** sin enlace a las ejecuciones: la reproducibilidad no supera 8.
- **Presentar como hecho lo que no se hizo** (un rojo que no existe, una aprobación que nunca esperó, un despliegue que no se hizo): el análisis no supera 20.
- **El verde se consiguió borrando, saltando o vaciando la comprobación que daba rojo**, sin decirlo: la técnica no supera 25.
- **Recursos de Google Cloud creados y no borrados** al entregar (si se hizo la parte opcional): el análisis no supera 25. No se aplica si no se creó nada.
- **Capturas con el correo o los identificadores de proyecto o de facturación sin tapar**: se pide corregirlas; si se repite, la técnica no supera 30.

## Lo que no se evalúa
- Que tengas cuenta de Google Cloud o facturación, ni cuánto gastaste.
- Que uses una herramienta concreta de orquestación distinta de GitHub Actions.
- Cuántas pruebas o etapas tienes: cuenta que el pipeline sea real, que el rojo → verde sea real y que lo expliques.
- Que tu modelo sea mejor que el de otra persona.
