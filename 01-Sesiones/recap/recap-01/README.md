# Recap 01 · S1 en 5 minutos: de los datos al modelo

Se abre al empezar S2, durante la revisión del entorno (minutos 0–30 de la agenda de S2). Abrir `index.html` con doble clic.
Con las diapositivas 11–14 (MLflow, que no dio tiempo a terminar en S1) el recap ocupa **15–20 minutos**: ver [`guion-profesor.md`](guion-profesor.md).

## Materiales
| Archivo | Para quién | Qué es |
|---|---|---|
| `index.html` | clase | La presentación (16 diapositivas) |
| [`mlflow-paso-a-paso.md`](mlflow-paso-a-paso.md) | alumnado | Cómo se crea la base de MLflow, cómo abrir la interfaz, comparar ejecuciones y ver el registro; por qué «no refrescaba»; tabla *Si algo falla* |
| [`practica-mlflow-mas-modelos.md`](practica-mlflow-mas-modelos.md) | alumnado (respuestas al final, para el profesor) | Práctica guiada de 30–40 min: añadir dos modelos, reentrenar, comparar en MLflow y deshacer con `git restore` |
| [`guion-profesor.md`](guion-profesor.md) | profesor | Cómo dar el recap en los primeros 15–20 minutos de S2 y qué mostrar en directo |

## Las 16 diapositivas
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
| 11 | MLflow: cómo arrancarlo | Siete pasos (entorno, `cd 04-Proyecto-Base`, `--comprobar`, abrir, *Model training*…) y quién crea `models/mlflow.db` |
| 12 | Por qué no se refrescaba | La ruta relativa abría otra base vacía; modo GenAI; registro vacío; la interfaz lee la base en cada consulta |
| 13 | Añadir modelos | Las dos entradas nuevas en `modelos()`, por qué no hace falta `--forzar`, nulos, cuaderno 04 y cómo deshacer |
| 14 | Comparar cinco modelos | AUC train/valid/test reales de los cinco modelos; gana el bosque por 0,005 (no se distingue del azar), misma huella, versiones 1–3 |
| 15 | Autoevaluación | Seis preguntas; **interactiva:** la respuesta aparece al pulsar |
| 16 | Puente a S2 | Del modelo guardado a la API, la imagen Docker y GitHub Actions; qué traer listo |

## De dónde salen las cifras
- **Dato completo** (diapositivas 2, 4, 6 y 7): las de la presentación de S1 (`01-Sesiones/S1-Datos-y-Entrenamiento/slides/index.html`), obtenidas con `04-Proyecto-Base` sobre el Excel de UCI.
- **Muestra del curso** (diapositivas 7 y 8): las salidas del cuaderno `04-Proyecto-Base/notebooks/04_entrenamiento_y_seguimiento.ipynb` (regresión logística valid 0,698 · test 0,747; aciertos en el 10 % mejor en test 88 %, referencia 24 %, tasa base 40,4 %).
- **MLflow** (diapositiva 9): la salida real de `python -m ia_mlops.mlflow_ui` en Windows 11 el 13/11/2026. El número de ejecuciones depende de cuántas veces se haya entrenado.
- **Diapositivas 11–14**: ejecución real en Windows 11 el 13/11/2026, con la muestra, en una carpeta temporal de `%TEMP%` (variables `CURSO_*`, sin tocar los datos ni el MLflow del proyecto): `operacional` → `pipeline` → `train.py` con dos modelos más → `pipeline_train` → comparación con `mlflow.search_runs` y en la interfaz (Chrome, puerto 5001) → `git restore` → `pipeline_train`. La base vacía de la diapositiva 12 (0 ejecuciones, solo `Default`) es la que quedó en la raíz del repositorio del profesor el 11/11/2026; las 48 ejecuciones son las de la base del proyecto. El intervalo de −0,043 a +0,049 es un *bootstrap* de valid (2 000 remuestreos, semilla 0). Detalle en `practica-mlflow-mas-modelos.md`.

## Qué está comprobado
- Las 16 diapositivas sin desbordes a 1280 × 720, sin errores de JavaScript, y las capas y las preguntas responden al clic (Chrome, `revisar_recap.py`, 13/11/2026).
- La guía y la práctica, paso a paso en Windows 11 (13/11/2026), incluido el cuaderno 04 con los dos modelos (ejecutado en memoria, sin modificar el archivo) y «empezar de cero» borrando `models/mlflow.db` y `models/mlartifacts/`.
- Enlazado desde el índice de S2. **Sin hacer:** el PDF del recap (no está en `00-Planificacion/pdfs/contenido_pdfs.py`). **No probado en el Codespace:** abrir la interfaz de MLflow por el puerto reenviado.
