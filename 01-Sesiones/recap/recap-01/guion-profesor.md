# Guion del profesor · Recap 01 al empezar S2 (15–20 minutos)

Objetivo: cerrar lo que quedó a medias en S1 (MLflow) **sin comerse la sesión**. Se cuenta con las diapositivas y se enseña en directo solo lo
imprescindible: arrancar MLflow bien, ver las ejecuciones y el registro, y enseñar que añadir un modelo es una entrada en `modelos()`.
La práctica completa (30–40 min) queda para casa o para el hueco de la revisión del entorno.

## Antes de clase (10 min, el día anterior o al llegar)

1. **Ten el MLflow del proyecto listo:** desde `04-Proyecto-Base`, `python -m ia_mlops.mlflow_ui --comprobar`. El 13/11/2026 daba
   `48 ejecuciones · … 1 versiones`. Si quieres enseñar la comparación de cinco modelos en tu propio MLflow, haz antes la práctica en tu proyecto
   (pasos 3–5) y **deshazla** (paso 6); o enséñala solo con la diapositiva 14.
2. **Deja preparada la prueba del fallo de S1:** en la raíz del repositorio sigue `models/mlflow.db` (11/11/2026, 1 MB): tiene **0 ejecuciones** y solo
   el experimento `Default`. Es la base vacía que creó `mlflow ui --backend-store-uri sqlite:///models/mlflow.db` lanzado desde la raíz. No la borres
   hasta después de clase: es la mejor demostración.
3. **Puerto 5000:** si lo tienes ocupado, usa `--port 5001` en todo lo que sigue.
4. **Codespace:** esta guía no se ha probado abriendo la interfaz por el puerto reenviado. Si alguien va a trabajar en el Codespace, pruébalo tú antes
   (`python -m ia_mlops.mlflow_ui` y panel *Puertos* → 5000).

## En clase

| Minuto | Qué | Diapositiva / directo |
|---|---|---|
| 0–5 | Recap rápido de S1: la pregunta, las capas, la partición, los tres modelos | Diapositivas 1–8, sin pararse (ya se vieron en S1) |
| 5–7 | Qué es MLflow en el proyecto y qué es el registro de modelos | Diapositiva 9 |
| 7–12 | **En directo: arrancar MLflow bien** | Diapositiva 11 en pantalla y la terminal al lado (ver abajo) |
| 12–14 | Por qué en S1 «no refrescaba» | Diapositiva 12 + `--comprobar` sobre la base vacía (ver abajo) |
| 14–18 | Añadir modelos y leer la comparación | Diapositivas 13 y 14 (sin editar código en directo) |
| 18–20 | Autoevaluación y puente a S2 | Diapositivas 15–16. Encargar la práctica |

### Directo 1 · arrancar MLflow (minutos 7–12), en este orden

1. Abre la **terminal de VS Code** (para que se vea que empieza en la raíz del repositorio) y escribe `cd 04-Proyecto-Base`.
2. `python -m ia_mlops.mlflow_ui --comprobar` → lee en voz alta la ruta completa y el número de ejecuciones.
3. `python -m ia_mlops.mlflow_ui` → abre http://127.0.0.1:5000.
4. En la web: **Model training** (arriba a la izquierda). Señala que el menú cambia de *AI Registry* a *Model registry*.
5. **Experiments → retencion-90d → Runs**. Botón **Columns**: añade `valid_auc`, `train_auc` y `huella_datos`.
6. Marca `regresion_logistica` y `gradient_boosting` → **Compare** → *Show diff only*. Pregunta: «¿cuál ha memorizado?» (1,000 frente a 0,803 en train).
7. **Model registry → retencion-90d**: la versión con sus etiquetas `modelo`, `huella_datos`, `valid_auc`.
8. Deja la interfaz abierta: la usarás en el minuto 12.

Frase clave sobre la base: *«No hay ningún comando para crear la base de MLflow. La crea el primer entrenamiento: `train.py` dice dónde
(`set_tracking_uri`, línea 136, con la ruta completa) y, al preguntar por el experimento (línea 138), MLflow abre la base, no la encuentra y la crea con
sus tablas. `create_experiment` (línea 139) añade `retencion-90d`, y la carpeta `mlartifacts/` aparece cuando se guarda el modelo (`log_model`, línea 175).»*
Comprobado paso a paso el 13/11/2026.

### Directo 2 · por qué no refrescaba (minutos 12–14)

1. En la terminal, **desde la raíz** del repositorio (`cd ..`), enseña la base vacía sin abrir otra interfaz. Por ejemplo, en PowerShell:
   `dir models` → aparece `mlflow.db`. Explica: «esta la creó el comando con ruta relativa; tiene 0 ejecuciones».
2. Vuelve a `04-Proyecto-Base` y repite `--comprobar`: 48 (o las que tengas). «Eran dos bases distintas.»
3. Opcional, si sobra un minuto: en otra terminal, `python -m ia_mlops.pipeline_train --forzar` (unos 20 s). Mientras, deja la página *Runs* abierta:
   en la prueba del 13/11 las 4 ejecuciones nuevas aparecieron solas en menos de 15 s. Si no aparecen, F5. **Ojo:** esto añade ejecuciones y una versión
   nueva a tu MLflow real; si no lo quieres, enséñalo solo con la diapositiva.
4. Cierra la interfaz con **Ctrl+C**.

### Diapositivas 13–14 · añadir modelos (minutos 14–18)

- No edites `train.py` en directo: enseña el código de la diapositiva 13 y abre `ia_mlops/modeling/train.py` en la función `modelos()` (líneas 76–84)
  para que vean dónde va.
- La idea que hay que llevarse: **una entrada más en el diccionario** y el resto (entrenar, medir, registrar, elegir con valid) funciona solo; y el
  pipeline vuelve a entrenar **sin `--forzar`** porque su huella incluye el código de `train.py`.
- En la diapositiva 14, la discusión buena: gana el bosque con valid por **0,005**, pero con 114 filas de valid esa diferencia no se distingue del azar
  (intervalo del 95 % de −0,043 a +0,049). La regla automática es un punto de partida; la decisión de qué va a producción es nuestra.
- Recordad el **paso 6 de la práctica**: `git restore ia_mlops/modeling/train.py` y volver a entrenar. Con el cambio puesto fallan 4 pruebas.

## Qué encargar

- Todos: [`mlflow-paso-a-paso.md`](mlflow-paso-a-paso.md) hasta el paso 10, antes del bloque de la API.
- Práctica: [`practica-mlflow-mas-modelos.md`](practica-mlflow-mas-modelos.md) (30–40 min), con las preguntas 1–8. Las respuestas están al final del
  mismo archivo: si se lo pasas al alumnado, quita esa sección o díselo.

## Si algo sale mal en directo

| Pasa | Haz |
|---|---|
| `No module named ia_mlops` | Te falta `cd 04-Proyecto-Base`. Es justo el error de S1: aprovéchalo |
| La web sale vacía | ¿Pulsaste *Model training*? Si sí: Ctrl+C y `--comprobar` |
| Puerto ocupado | `--port 5001` |
| `--forzar` tarda | Sigue con la diapositiva 13 mientras termina; vuelve a *Runs* y pulsa F5 |
