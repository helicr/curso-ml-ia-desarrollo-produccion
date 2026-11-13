# MLflow paso a paso: de la base vacía a comparar modelos

Guía para el alumnado. Sirve para lo que no dio tiempo a terminar en S1: **abrir MLflow, ver las ejecuciones, compararlas y ver el modelo registrado**.
Tiempo: unos 10 minutos si ya ejecutaste el pipeline en S1.

> **Probado en Windows 11 el 13/11/2026** (terminal de PowerShell, entorno `env-ia-mlops`, MLflow 3.18.0, scikit-learn 1.9.1), con la muestra del curso
> y en una carpeta temporal. **En el Codespace no se ha probado esta guía**: los comandos son los mismos, pero el paso 6 (abrir la web) cambia; ver el
> apartado del Codespace.

---

## 1. Abre una terminal con el entorno del curso

| Dónde trabajas | Qué haces |
|---|---|
| **Windows · Anaconda Prompt** | Ábrelo desde el menú Inicio y escribe `conda activate env-ia-mlops`. |
| **Windows · terminal de VS Code** | *Terminal → Nueva terminal*. Si el indicador no dice `(env-ia-mlops)`, escribe `conda activate env-ia-mlops`. |
| **Codespace** | La terminal se abre ya con `(env-ia-mlops)`. Si dice `(base)`: `conda activate env-ia-mlops`. |

**Debe salir:** `(env-ia-mlops)` al principio de la línea.

## 2. Entra en la carpeta del proyecto

La terminal de VS Code y la del Codespace se abren en la **raíz del repositorio**, no en el proyecto. Entra siempre:

```
cd 04-Proyecto-Base
```

En Anaconda Prompt, antes, ve a la carpeta donde clonaste el repositorio (por ejemplo `cd C:\cursos\curso-ml-ia-desarrollo-produccion`).

**Comprueba:** `dir` (Windows) o `ls` (Codespace) muestra `ia_mlops`, `notebooks`, `models` y `pyproject.toml`.
Si no estás aquí, todo lo que sigue falla (ver la tabla *Si algo falla*).

## 3. Cómo se crea la base de MLflow (no hay que hacer nada aparte)

**No existe ningún comando para «crear la base de metadatos» de MLflow.** La crea **el primer entrenamiento** que se hace con MLflow activado:

| Lo que ejecutas | Dónde está el código |
|---|---|
| `python -m ia_mlops.pipeline` (o solo `python -m ia_mlops.pipeline_train`) | `ia_mlops/modeling/train.py`, función `entrenar()`, líneas 130–140 |
| El cuaderno `notebooks/04_entrenamiento_y_seguimiento.ipynb` con `USAR_MLFLOW = True` | Primera celda de código del apartado *3. Entrenar y registrar en MLflow* |

Ese código hace, en este orden (comprobado paso a paso el 13/11/2026):

1. `mlflow.set_tracking_uri('sqlite:///…/models/mlflow.db')` (línea 136). Solo **dice dónde** escribir, con la ruta **completa** de `models/`. Todavía no crea nada.
2. `mlflow.get_experiment_by_name('retencion-90d')` (línea 138). Es la primera vez que MLflow abre la base: como no existe, **crea el archivo
   `models/mlflow.db` con todas sus tablas** y un experimento `Default` que MLflow pone siempre. En la terminal aparece:
   ```
   INFO mlflow.store.db.utils: Creating initial MLflow database tables...
   INFO mlflow.store.db.utils: Updating database tables
   ```
3. `mlflow.create_experiment('retencion-90d', artifact_location=…/models/mlartifacts)` (línea 139). Añade el experimento del proyecto y le dice dónde
   guardar los archivos. La carpeta todavía no existe.
4. Cada `with mlflow.start_run(...)` (líneas 151 y 166) añade una **ejecución** con sus parámetros y métricas.
5. `mlflow.sklearn.log_model(..., registered_model_name='retencion-90d')` (líneas 175–176) guarda el modelo elegido: **ahora aparece la carpeta
   `models/mlartifacts/`** y se crea una **versión** del modelo registrado.

Resultado: dos cosas dentro de `04-Proyecto-Base/models/`:
- `mlflow.db`: una base SQLite con experimentos, ejecuciones, parámetros, métricas y el registro de modelos.
- `mlartifacts/`: los archivos (el modelo guardado, su firma, sus dependencias).

Si ya ejecutaste el pipeline en S1, **ya los tienes**. Si no:

```
python -m ia_mlops.pipeline
```

Salida real (muestra del curso, 13/11/2026; tardó 30 s, de ellos 23 s el entrenamiento):
```
[pipeline_train] ejecutando (huella de entrada 7108eeb2fa32)
  referencia_sin_aprender    AUC valid 0.500 | test 0.500 | precision media test 0.404
  regresion_logistica        AUC valid 0.698 | test 0.747 | precision media test 0.659
  gradient_boosting          AUC valid 0.663 | test 0.735 | precision media test 0.648
  Mejor modelo: regresion_logistica. Guardado en …\models\modelo.joblib
  Registrado en MLflow como «retencion-90d», version 1. Para verlo: python -m ia_mlops.mlflow_ui
```

## 4. Comprueba qué hay en la base, sin abrir nada

```
python -m ia_mlops.mlflow_ui --comprobar
```

**Debe salir** (con un solo entrenamiento):
```
Registro de MLflow: C:\…\04-Proyecto-Base\models\mlflow.db
  Experimento «retencion-90d»: 4 ejecuciones · modelo registrado «retencion-90d»: 1 versiones
```
Cuatro ejecuciones = una por modelo (3) + `MEJOR-regresion_logistica`. Si has entrenado más veces, verás más; es normal.

Si la base no existe todavía, sale esto y no se abre nada (salida real):
```
  No existe todavía. Entrena primero:  python -m ia_mlops.pipeline   (o ejecuta el cuaderno 04 con USAR_MLFLOW = True)
```

## 5. Abre la interfaz

```
python -m ia_mlops.mlflow_ui
```

Por dentro lanza `mlflow ui --backend-store-uri sqlite:///<ruta completa>/models/mlflow.db --host 127.0.0.1 --port 5000`.
La terminal se queda ocupada mientras la interfaz está abierta (es normal). **Para cerrarla: Ctrl+C** en esa terminal.
Si el puerto 5000 está ocupado: `python -m ia_mlops.mlflow_ui --port 5001`.

## 6. Abre el navegador

- **Windows:** http://127.0.0.1:5000 (o :5001 si usaste `--port 5001`).
- **Codespace:** el repositorio reenvía el puerto 5000 («MLflow UI», `forwardPorts` del `.devcontainer`). Abre el panel **Puertos** (*PORTS*), junto a
  la terminal, y pulsa el globo del 5000. *No probado en el Codespace con esta versión de MLflow:* si la página no carga o muestra un error, díselo al
  profesor y sigue la práctica con `--comprobar` y la tabla del paso 9.

## 7. Elige «Model training»

MLflow 3.18 abre en el modo **GenAI** (menús *AI Registry*, *AI Gateway*, *Traces*, *Prompts*…). Arriba a la izquierda hay dos botones:
**GenAI | Model training**. Pulsa **Model training**. El menú de la izquierda pasa a ser *Home · Experiments · Model registry*.

## 8. Mira las ejecuciones

1. **Experiments** → `retencion-90d` (verás también `Default`: lo crea MLflow solo, está vacío).
2. Pestaña **Runs**: una fila por ejecución, la más reciente arriba. En la columna **Models** la ejecución `MEJOR-…` muestra `retencion-90d v1`.
3. Botón **Columns**: añade `valid_auc`, `test_auc`, `train_auc` y `huella_datos` para verlas sin entrar en cada ejecución.

## 9. Compara dos ejecuciones

1. Marca la casilla de `regresion_logistica` y la de `gradient_boosting`.
2. Pulsa **Compare** (aparece arriba al marcar).
3. Se abre *Comparing 2 Runs from 1 Experiment*: arriba unas gráficas; abajo **Parameters** y **Metrics** lado a lado (*Show diff only* deja solo lo que cambia).

Qué mirar (valores reales de la muestra):

| Ejecución | train_auc | valid_auc | test_auc |
|---|---|---|---|
| regresion_logistica | 0,803 | **0,698** | 0,747 |
| gradient_boosting | 1,000 | 0,663 | 0,735 |

- **Antes de comparar:** las dos tienen la misma `huella_datos` (`35a94deb4e04ab4a` con la muestra). Si no coincide, se entrenaron con datos distintos y la comparación no es justa.
- El gradient boosting saca 1,000 en train y 0,663 en valid: ha **memorizado** (sobreajuste).
- Gana la regresión logística porque tiene **más AUC en valid**. Test se informa, no se usa para elegir.

## 10. Mira el modelo registrado

1. Menú izquierdo: **Model registry** → `retencion-90d`.
2. Una fila por versión (*Version 1*, *Version 2*…), con sus etiquetas `modelo`, `huella_datos` y `valid_auc`.
3. Entra en una versión: verás de qué ejecución salió (`MEJOR-…`) y su firma (13 entradas, 1 salida).

Cada entrenamiento nuevo crea **una versión nueva**; las anteriores no se borran. En S4 y S5 se pondrá a una versión el alias de producción.

---

## Por qué «no refrescaba»

En S1 la interfaz se abrió pero **no se veían ejecuciones ni modelos**. No era un problema de refresco, sino de **qué base estaba leyendo**:

1. **Leía otra base, vacía.** El comando que se usó, `mlflow ui --backend-store-uri sqlite:///models/mlflow.db`, tiene la ruta **relativa**
   (`models/…` desde la carpeta en la que está la terminal). La terminal de VS Code está en la **raíz del repositorio**, así que MLflow usó
   `<raíz>/models/mlflow.db` y, como no existía, **la creó vacía sin dar ningún error**. El entrenamiento, en cambio, escribe en
   `04-Proyecto-Base/models/mlflow.db`. Eran dos bases distintas. `python -m ia_mlops.mlflow_ui` calcula la ruta completa y te dice antes qué hay.
2. **Estaba en el modo GenAI.** En ese modo los menús son de IA generativa y no se ven los entrenamientos: hay que pulsar *Model training*.
3. **El registro de modelos estaba vacío** porque entonces el código no registraba el modelo. Ahora `train.py` y el cuaderno 04 lo registran como
   `retencion-90d`.

**¿Y refrescar?** La interfaz no guarda copia de nada: **lee la base cada vez que pide datos**. En la prueba del 13/11/2026, con la página *Runs*
abierta, se entrenó en otra terminal y las 4 ejecuciones nuevas aparecieron solas en menos de 15 segundos. Si algo no aparece tras entrenar,
**recarga el navegador (F5)**. No hace falta reiniciar `mlflow_ui`.

**¿Y si entreno y no aparece nada nuevo?** Mira la salida del entrenamiento. Si dice
`[pipeline_train] sin cambios: la entrada es la misma que en la ultima ejecucion (…)`, **no ha entrenado**: el pipeline es idempotente y, si ni los datos ni
el código cambiaron, no repite el trabajo ni añade ejecuciones a MLflow. Para entrenar igualmente: `python -m ia_mlops.pipeline_train --forzar`.

## Si algo falla

| Lo que ves | Por qué | Qué haces |
|---|---|---|
| La interfaz abre pero no hay ejecuciones ni modelos | Estás leyendo otra base (ruta relativa desde otra carpeta) o sigues en el modo GenAI | Cierra con Ctrl+C. Desde `04-Proyecto-Base`: `python -m ia_mlops.mlflow_ui --comprobar` y después `python -m ia_mlops.mlflow_ui`. En la web, **Model training** |
| Tienes un `models/mlflow.db` en la raíz del repositorio | Lo creó el comando con ruta relativa: es una base vacía | Puedes borrarlo; el bueno es `04-Proyecto-Base/models/mlflow.db` |
| `--comprobar` dice «No existe todavía» o «Está vacío» | Aún no has entrenado con MLflow | `python -m ia_mlops.pipeline` (o el cuaderno 04 con `USAR_MLFLOW = True`) |
| Error de puerto en uso (el 5000 ya lo usa otro programa o otra interfaz que dejaste abierta) | Solo un programa puede escuchar en cada puerto | `python -m ia_mlops.mlflow_ui --port 5001` y abre http://127.0.0.1:5001, o cierra la otra con Ctrl+C |
| `No module named ia_mlops` | No estás en `04-Proyecto-Base` | `cd 04-Proyecto-Base` y repite |
| `No module named mlflow` o `ModuleNotFoundError` | No está activado el entorno del curso | `conda activate env-ia-mlops` |
| Menús *Traces*, *Prompts*, *AI Gateway*, *AI Registry* | Modo GenAI | Arriba a la izquierda: **Model training** |
| Entrenas y no aparece nada nuevo | El pipeline dijo «sin cambios» (no entrenó) | Lee la salida. Para forzar: `python -m ia_mlops.pipeline_train --forzar`. Si sí entrenó, recarga el navegador (F5) |
| Quieres **empezar de cero** | — | Cierra la interfaz (Ctrl+C). Borra `models/mlflow.db` **y** `models/mlartifacts/` (los dos; no se editan a mano). Ejecuta `python -m ia_mlops.pipeline`: al no encontrar la base, vuelve a entrenar sin `--forzar` y la crea de nuevo, con la versión 1 |

Para borrar, desde `04-Proyecto-Base`:
- Windows (PowerShell): `Remove-Item -Recurse -Force models\mlflow.db, models\mlartifacts`
- Codespace (bash): `rm -rf models/mlflow.db models/mlartifacts`

Comprobado el 13/11/2026 en la carpeta temporal: tras borrar los dos, `--comprobar` dijo «No existe todavía»; `python -m ia_mlops.pipeline` volvió a
entrenar (los otros tres pipelines, «sin cambios») y `--comprobar` dio 4 ejecuciones y 1 versión.
