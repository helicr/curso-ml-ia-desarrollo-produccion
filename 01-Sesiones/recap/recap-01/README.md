# Recap 01 · S1 en 5 minutos: de los datos al modelo

Se abre al empezar S2, durante la revisión del entorno (minutos 0–30 de la agenda de S2). Abrir `index.html` con doble clic.

## Las 12 diapositivas
| # | Diapositiva | Qué se recuerda |
|---|---|---|
| 1 | Portada | El recorrido de S1 en seis pasos |
| 2 | La pregunta en un dibujo | Un ejemplo = un cliente en una fecha de corte; variables hacia atrás, objetivo en los 90 días siguientes |
| 3 | El recorrido por capas | OPERACIONAL → RAW → MASTER → FS → ML. **Interactiva:** al pulsar una capa se ve qué entra, qué sale y su regla clave |
| 4 | MASTER | Conciliación RAW = MASTER + descartes y los tres tipos de regla de calidad |
| 5 | FS | Las 13 variables en cuatro grupos y la tarea de S1 |
| 6 | Partición temporal | train, valid y test en la línea de tiempo, con filas y tasa de recompra; temporal frente a aleatoria |
| 7 | Tres modelos | AUC por partición en barras; sobreajuste del gradient boosting |
| 8 | Leer el AUC | El AUC como «duelo» entre dos clientes y los aciertos en el 10 % mejor |
| 9 | MLflow | Experimento, ejecuciones y **registro de modelos**; cómo abrir la interfaz y qué falló al preparar S1 |
| 10 | Del cuaderno al Python | Cuadernos, paquete `ia_mlops`, prueba de equivalencia e idempotencia |
| 11 | Autoevaluación | Seis preguntas; **interactiva:** la respuesta aparece al pulsar |
| 12 | Puente a S2 | Del modelo guardado a la API, la imagen Docker y GitHub Actions; qué traer listo |

## De dónde salen las cifras
- **Dato completo** (diapositivas 2, 4, 6 y 7): las de la presentación de S1 (`01-Sesiones/S1-Datos-y-Entrenamiento/slides/index.html`), obtenidas con `04-Proyecto-Base` sobre el Excel de UCI.
- **Muestra del curso** (diapositivas 7 y 8): las salidas del cuaderno `04-Proyecto-Base/notebooks/04_entrenamiento_y_seguimiento.ipynb` (regresión logística valid 0,698 · test 0,747; aciertos en el 10 % mejor en test 88 %, referencia 24 %, tasa base 40,4 %).
- **MLflow** (diapositiva 9): la salida real de `python -m ia_mlops.mlflow_ui` en Windows 11 el 13/11/2026. El número de ejecuciones depende de cuántas veces se haya entrenado.

## Qué está comprobado
- Las 12 diapositivas sin desbordes a 1280 × 720, sin errores de JavaScript, y las capas y las preguntas responden al clic (Chrome, 13/11/2026).
- **Sin hacer:** el PDF del recap (no está en `00-Planificacion/pdfs/contenido_pdfs.py`) y su enlace desde el índice de S2.

## Nota sobre la presentación de S1
La diapositiva 11 de S1 titula «13 variables, **5 familias**», pero muestra cuatro grupos. Este recap usa los cuatro grupos tal como aparecen allí.
