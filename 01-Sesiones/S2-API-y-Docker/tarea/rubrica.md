# Rúbrica de la tarea S2 (100 puntos)

| Criterio | Peso | Qué se observa |
|---|---|---|
| **Reproducibilidad** | 20 | Otra persona clona, sigue tus comandos y obtiene la misma API, la misma imagen y las mismas comparaciones. Versiones exactas (`requirements-api.lock` o equivalente), comandos en orden, rama indicada. |
| **Técnica** | 40 | Contrato que sale de la firma y falla al arrancar si no coincide; 422, 503 y 500 distinguibles y **probados**; registro JSON sin datos del cliente; `Dockerfile` con dependencias antes del código, usuario no root y `.dockerignore` que deja fuera datos y secretos; workflow en verde; comparación de caminos ejecutada contra el contenedor. |
| **Análisis y decisión** | 40 | Qué rechaza tu API y qué solo avisa, y por qué (con ejemplos reales); interpretación de la comparación (diferencias cero o explicadas); riesgos reconocidos (ver abajo) y qué harías después. |

## Niveles por criterio
| Nivel | Reproducibilidad (20) | Técnica (40) | Análisis (40) |
|---|---|---|---|
| Sobresaliente | 18–20 · un tercero reproduce sin ayuda | 36–40 · todo en verde, con pruebas propias que fallan si se rompe la regla | 36–40 · decisiones argumentadas con casos reales, riesgos y alternativas |
| Logrado | 14–17 | 28–35 | 28–35 |
| En proceso | 8–13 · faltan pasos o versiones | 16–27 · el contrato se copió a mano sin comprobar, o falta la prueba de algún código de error | 16–27 · cifras sin interpretar |
| Insuficiente | 0–7 | 0–15 | 0–15 |

## Qué riesgos se esperan reconocidos
Elige los que correspondan a tu caso y explica qué harías:
- El esquema y la firma pueden desincronizarse si alguien reentrena con una variable nueva (¿qué te lo dice, y cuándo?).
- Los límites de un campo pueden rechazar clientes reales si salen de «lo que vi al entrenar».
- Un valor posible pero fuera del rango de entrenamiento recibe una predicción sin respaldo (por eso se avisa).
- `cloudpickle` puede ejecutar código al cargarse: solo se carga un modelo que construyó tu propio pipeline.
- La imagen se construyó y probó en otra máquina que la de producción (versiones, arquitectura).
- Lo que **no** probaste (por ejemplo, Docker en tu equipo o el Codespace) y el error exacto.

## Descuentos y alertas
- El registro del servicio contiene datos del cliente (valores de variables): la técnica no supera 25.
- La imagen contiene datos, cuadernos o secretos, o corre como root sin explicarlo: la técnica no supera 25.
- Una diferencia distinta de cero entre caminos que no se explica ni se investiga: el análisis no supera 20.
- Presentar solo capturas, sin código, pruebas ni workflow ejecutables: la reproducibilidad no supera 8.
- Un error 500 que muestra detalles internos (rutas, trazas): la técnica no supera 30.
