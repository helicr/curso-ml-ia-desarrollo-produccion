# De cuaderno a Python: cómo y por qué

Un cuaderno es ideal para **explorar, explicar y construir** un pipeline. Un servicio en producción necesita **código que se pueda importar, probar,
empaquetar y automatizar**. En este proyecto los cuadernos son los pipelines y el paquete `ia_mlops` es su traducción.

## Los dos caminos
| | Traducción literal | Refactorización |
|---|---|---|
| Herramienta | `jupytext --to py:percent` | A mano, con criterio |
| Resultado | Un `.py` por cuaderno, celda a celda | Funciones con nombre en módulos (`dataset.py`, `features.py`…) |
| Para qué sirve | Ejecutar un cuaderno sin Jupyter; revisar cambios en Git | Reutilizar, probar, importar desde la API, empaquetar |
| Rutas y parámetros | Variables de entorno (`CURSO_DB`, `CURSO_MODELOS`…) | `config.py` y argumentos de línea de comandos |
| Limitación | Sigue siendo un script lineal | Hay que mantenerlo sincronizado con el cuaderno |

```text
make traducir          # o:  jupytext --to py:percent notebooks/01_pipeline_raw_a_master.ipynb -o scripts_desde_notebooks/01.py
```

## El mapa: cada cuaderno y su traducción
| Cuaderno (el pipeline) | Pipeline `.py` (se ejecuta solo) | Usa la lógica de | Lee | Escribe en |
|---|---|---|---|---|
| `00_pipeline_operacional` | `python -m ia_mlops.operacional` *(simulación del origen)* | `operacional.py` | archivo de UCI | `data/external/retail.db` |
| `01_pipeline_raw_a_master` (sección 1) | `python -m ia_mlops.pipeline_ingesta_raw` | `dataset.cargar_raw()` | `retail.db` | `curso.db`: `raw_*` |
| `01_pipeline_raw_a_master` (secciones 2–4) | `python -m ia_mlops.pipeline_ingesta_master` | `dataset.construir_master()`, `calidad.py` | `raw_*` | `curso.db`: `master_*` |
| `02_pipeline_master_a_fs` + `03_pipeline_fs_a_ml` | `python -m ia_mlops.pipeline_ml` | `features.construir_fs()`, `ml_dataset.construir_ml()` | `master_*` | `curso.db`: `fs_*`, `ml_*` |
| `04_entrenamiento_y_seguimiento` | `python -m ia_mlops.pipeline_train` | `train.entrenar()` | `ml_dataset` | `models/`, `reports/metricas.json`, MLflow |
| (los cuatro, en orden) | `python -m ia_mlops.pipeline` *(orquestador, sin lógica propia)* | los cuatro de arriba | | |
| (base de la API de S2) | `python -m ia_mlops.modeling.predict --cliente 12369 --corte 2011-09-01` | `predict.py` | `fs_*`, `models/` | nada |

## Pipelines independientes e idempotentes
- **Independiente:** cada pipeline se ejecuta solo. No necesita que se hayan ejecutado los anteriores «en la misma sesión»: le basta con que su capa de
  entrada exista. Si no existe, se detiene con un mensaje que dice qué pipeline ejecutar antes (código de salida 2, útil en GitHub Actions).
- **Idempotente:** ejecutarlo una vez o diez seguidas deja **el mismo resultado**. Dos mecanismos (`ia_mlops/control.py`):
  1. Cada pipeline reconstruye su capa **desde cero** (`DROP` + `CREATE` en sus SQL): nunca añade filas a lo que había.
  2. Antes de trabajar calcula su **huella de entrada**: el contenido de lo que lee + el código que aplica (SQL y Python) + la configuración
     (cortes, ventana, variables). Si coincide con la de su última ejecución correcta y su salida existe, termina con «sin cambios».
     Así no cambian ni las marcas de tiempo ni se acumulan en MLflow ejecuciones repetidas.
- **Qué provoca que se rehaga:** cambió el origen (una línea en `retail.db`), una regla de MASTER, un corte o una variable en `config.py`, el código de entrenamiento…
  Solo se rehacen el pipeline afectado y los siguientes que vean su entrada cambiada; los demás siguen «sin cambios».
- **Si un pipeline falla a mitad**, no registra su huella: la siguiente ejecución lo rehace entero.
- `--forzar` rehace un pipeline aunque no haya cambios. El registro de cada ejecución está en la tabla `control_pipelines` de `curso.db`.
- `tests/test_pipelines.py` lo comprueba: sin su entrada fallan con el mensaje correcto, repetirlos no cambia nada, forzarlos da el mismo contenido,
  un cambio en el origen se detecta, y entrenar dos veces no duplica ejecuciones en MLflow.

Los SQL de `sql/` son **los mismos** para el cuaderno y para el paquete: la lógica de datos no se duplica, solo cambia quién la ejecuta.
Lo que el paquete **no** hace: dibujar. Las gráficas de exploración y de comparación son de los cuadernos (y las guardan en `reports/figures/`).

## Cómo ejecutarlo (Windows, Anaconda Prompt o terminal de VS Code con el entorno activo)
**Camino 1 · el paquete** (el que se empaqueta, se prueba y se despliega desde S2):
```text
conda activate env-ia-mlops
cd 04-Proyecto-Base
pip install -e .                                  # una vez: instala ia_mlops en modo editable
python -m ia_mlops.operacional                    # una vez: simula retail.db con la muestra (--fuente completo para el Excel)
python -m ia_mlops.pipeline_ingesta_raw           # cada pipeline por separado...
python -m ia_mlops.pipeline_ingesta_master
python -m ia_mlops.pipeline_ml
python -m ia_mlops.pipeline_train                 # (--sin-mlflow para no registrar; --forzar en cualquiera para rehacerlo)
python -m ia_mlops.pipeline                       # ...o los cuatro en orden; repetido, todos dicen «sin cambios»
python -m ia_mlops.pipeline --solo pipeline_ml pipeline_train
```
**Camino 2 · la traducción literal** (un `.py` por cuaderno, generado con jupytext). En PowerShell:
```text
conda activate env-ia-mlops
cd 04-Proyecto-Base
New-Item -ItemType Directory -Force scripts_desde_notebooks
Get-ChildItem notebooks\0*.ipynb | ForEach-Object { jupytext --to py:percent $_.FullName -o "scripts_desde_notebooks\$($_.BaseName).py" }
$env:MPLBACKEND = 'Agg'; $env:CURSO_SIN_PANTALLA = '1'      # sin ventanas de gráficos: se guardan en reports/figures
Get-ChildItem scripts_desde_notebooks\*.py | Sort-Object Name | ForEach-Object { python $_.FullName; if ($LASTEXITCODE) { throw "falló $($_.Name)" } }
```
Los scripts se ejecutan **en orden (00 → 04)**, igual que los cuadernos. Leen sus rutas de las variables `CURSO_DB_OPERACIONAL`, `CURSO_DB`, `CURSO_MODELOS` y
`CURSO_REPORTES`; si no existen, usan las rutas del proyecto. En Codespaces o Linux, `make traducir` genera los scripts.

## Reproducible: qué lo garantiza y cómo comprobarlo
Reproducible significa: **mismo código + mismos datos + mismo entorno ⇒ mismas tablas y mismas métricas**, en cualquier máquina y tantas veces como se ejecute.
| Fuente de variación | Cómo se controla aquí |
|---|---|
| El entorno (versiones de Python y librerías) | `03-Entorno/conda/environment.yml` fija las versiones; `verificar_s1.py` comprueba que las instaladas coinciden |
| Los datos | La muestra está en el repositorio; el Excel se verifica con su sha256. `origen_simulacion` guarda la huella del archivo y `raw_carga` la de cada tabla ingerida |
| El orden de las filas | Todo se recorre por clave (`linea_id`, `ORDER BY`); los duplicados se resuelven siempre con la primera fila |
| El azar | La partición es **por fecha**, sin sorteo. Lo aleatorio lleva semilla fija: `random_state=0` en el gradient boosting y en la importancia por permutación; semilla 42 en la muestra |
| Qué datos usó cada modelo | `huella_datos` (en `models/metadatos.json` y como parámetro en MLflow): misma huella = mismos datos de entrenamiento |

**Cómo comprobarlo:** ejecuta dos veces y compara `reports/metricas.json` y la `huella_datos` de `models/metadatos.json`; deben ser idénticas.
`python -m pytest tests` lo comprueba además entre los tres caminos (cuaderno, paquete y traducción jupytext).
Lo único que cambia entre ejecuciones son las **marcas de tiempo** (`creada_en`, `extraido_en`, `entrenado_en`) y los **identificadores** de MLflow (cada ejecución es nueva).

Verificado el 11/11/2026 en Windows: dos ejecuciones del paquete desde cero (operacional y pipelines) y una de los cinco scripts de jupytext produjeron las mismas tablas
(operacional, RAW, MASTER, FS y ML), las mismas métricas hasta el último decimal (AUC de validación 0,698200992556 con la muestra) y la misma huella de datos.

## Equivalencia: lo que no se puede romper
Si el cuaderno y el paquete dan resultados distintos, uno de los dos está mal. `tests/test_notebooks.py` lo verifica:
1. Ejecuta los cinco cuadernos con **papermill** sobre bases temporales.
2. Compara **todas las tablas** (operacional, RAW, MASTER, FS y ML) con las que construye el paquete.
3. Compara las **métricas** (AUC, precisión media…) y la **huella** de los datos de entrenamiento.
4. Traduce los cuadernos con **jupytext**, ejecuta los `.py` resultantes y vuelve a comparar.

Esta prueba ya detectó una deriva real: las descripciones de las reglas de calidad tenían tildes en el cuaderno y no en el paquete.
Con el dato completo (1 067 371 filas) las tablas son idénticas y los AUC coinciden hasta el último decimal.

## Qué cambia al traducir un cuaderno a módulos
| En el cuaderno | En el paquete |
|---|---|
| Celda de parámetros (`FUENTE`, `RUTA_DB`…) | `config.py`, variables de entorno y argumentos (`--fuente completo`, `--forzar`) |
| Celdas sueltas con funciones auxiliares | Funciones públicas con docstring (`crear_operacional`, `cargar_raw`, `construir_master`…) |
| Teoría en celdas de texto | Docstring del módulo: qué es la capa, su regla y qué tablas produce |
| `print` y tablas de `pandas` para mirar | `print` informativo (`verbose`) y datos devueltos para probar |
| Gráficos que se ven en pantalla | No hay gráficos: el paquete devuelve datos y métricas (las figuras las guardan los cuadernos en `reports/figures/`) |
| `assert` sueltos como controles | Reglas de calidad en `calidad.py` y pruebas en `tests/` |
| Ejecución manual celda a celda | Cuatro pipelines independientes e idempotentes (`python -m ia_mlops.pipeline_…`); en S4, cada uno será un paso de GitHub Actions |
| El cuaderno siempre rehace todo | El pipeline solo rehace si su entrada cambió (huella de entrada) |

## Reglas para que un cuaderno se pueda traducir bien
- Una celda de **parámetros** al inicio (con la etiqueta `parameters`), con los comentarios en líneas aparte.
- Nada de rutas escritas a mano: todo parte de la carpeta del proyecto.
- Sin `display()` ni comandos mágicos (`%`): el último valor de una celda se ve en el cuaderno y no estorba en un script.
- Cada cuaderno **empieza y termina** de forma explícita: crea sus tablas, comprueba y cierra la conexión.
- Los cuadernos se guardan **sin salidas** en Git, para que los cambios sean legibles.

## Ejercicio de S1
Elige la función de `ia_mlops/features.py`, léela junto a la celda de `02_pipeline_master_a_fs.ipynb` y señala **tres cosas** que cambiaron al traducirla.
