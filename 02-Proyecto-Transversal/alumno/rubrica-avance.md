# Rúbrica de cada avance del caso propio (100 puntos)

Sirve para los cuatro avances (ver `tu-caso-bank-marketing.md`, apartado 9). Los tres criterios y sus pesos son los mismos que los de las tareas de S1 y S2; cambia lo que se observa en la técnica, según el avance.

| Criterio | Peso | Qué se observa |
|---|---|---|
| **Reproducibilidad** | 20 | Otra persona clona, ejecuta los comandos indicados y obtiene tus resultados. Pasos en orden, versiones, semilla, rama o commit. Cifras de tu carga que coinciden con las de la hoja del caso. |
| **Técnica** | 40 | Lo que pide el avance (tabla de abajo), con pruebas propias que **fallan si se rompe la regla**. |
| **Análisis y decisión** | 40 | Una decisión argumentada **con evidencia** (filas afectadas, métricas, ejecuciones comparables), alternativas consideradas, límites y riesgos reconocidos, y lo que no pudiste ejecutar con el error exacto. |

## Niveles por criterio

| Nivel | Reproducibilidad (20) | Técnica (40) | Análisis (40) |
|---|---|---|---|
| Sobresaliente | 18–20 · un tercero reproduce sin ayuda | 36–40 · todo en verde, con pruebas propias que fallan si se rompe la regla | 36–40 · decisión clara con evidencia, alternativas y riesgos |
| Logrado | 14–17 | 28–35 | 28–35 |
| En proceso | 8–13 · faltan pasos o versiones | 16–27 · falta alguna capa, prueba o comprobación | 16–27 · cifras sin interpretar |
| Insuficiente | 0–7 | 0–15 | 0–15 |

## Qué se pide en la técnica de cada avance

| Avance | Se observa |
|---|---|
| **1 · capas y entrenamiento** | RAW → MASTER → FS → ML con un cuaderno por capa; **`raw = master + descartes`** comprobado; catálogo de FS con por qué cada variable se conoce antes de llamar; **`duration` fuera, con una prueba que lo vigila**; partición estratificada con semilla guardada; tres modelos con métricas en validación y prueba y ejecuciones de MLflow comparables. |
| **2 · Python, API y contenedor** | Prueba de equivalencia entre cuadernos y paquete; contrato de la API que sale de la firma del modelo; 422, 503 y 500 distinguibles y probados; registro sin datos del cliente; `Dockerfile` y `.dockerignore` que dejan fuera datos y secretos. Mismo detalle que la rúbrica de S2. |
| **3 · GCP** | Inventario; datos migrados con una validación que demuestra que coinciden con los de local; servicio desplegado; secretos fuera del código; registros del servicio. *Se concretará al preparar S3.* |
| **4 · GitHub Actions** | Workflow en verde con historial de ejecuciones (también de las que fallaron y por qué); autenticación con GCP sin claves guardadas; el pipeline raw → modelo orquestado. *Se concretará al preparar S4.* |

## Descuentos y alertas
- **`duration` o cualquier variable que no se conozca antes de llamar entra en el modelo:** la técnica no supera 15, aunque mejore la métrica.
- **No se dice que la partición aleatoria es optimista** (avances 1 y 2): el análisis no supera 25.
- **Presentar solo capturas**, sin código, pruebas ni pasos ejecutables: la reproducibilidad no supera 8.
- **Sin cita de la fuente del dato** (la licencia CC BY 4.0 la exige): la reproducibilidad no supera 15.
- **Claves, tokens o credenciales en el repositorio:** la técnica no supera 25.
- **Presentar como ejecutado lo que no se ejecutó**, u ocultar un fallo: el análisis no supera 20.
- Comparar ejecuciones con huellas de datos distintas sin decirlo: el análisis no supera 20.

## Lo que no se evalúa
- Que tu métrica sea alta. No hay modelo de referencia: una decisión de «no» bien argumentada vale tanto como una de «sí».
- Que uses una herramienta u otra, mientras puedas justificarla y reproducirla.

*El peso de cada avance en la nota final y la rúbrica de la entrega final están por definir.*
