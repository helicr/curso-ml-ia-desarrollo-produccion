# Laboratorio S1 · 135 minutos

Se trabaja dentro de `04-Proyecto-Base/` con el entorno `env-ia-mlops` (terminal: **Anaconda Prompt** o la terminal de VS Code con el entorno activado).
Los comandos valen en CMD y PowerShell. `make` no existe en Windows: se usan las líneas equivalentes.

| Min | Bloque |
|---|---|
| 0–10 | 0. Preparar |
| 10–40 | 1. Cuaderno 01: RAW → MASTER |
| 40–65 | 2. Cuaderno 02: MASTER → FS |
| 65–75 | **Pausa** |
| 75–100 | 3. Cuaderno 03: FS → ML |
| 100–125 | 4. Cuaderno 04: entrenar y MLflow |
| 125–135 | 5. Traducir a `.py` y probar |

Los números que verás con la **muestra** (23 070 filas) son distintos de los del dato completo de las diapositivas. Es esperado.

## 0. Preparar (10 min)
```bash
conda activate env-ia-mlops
cd 04-Proyecto-Base
python -m pytest -q -m "not lento"
```
Esperado: `30 passed` (las 4 pruebas restantes ejecutan los cuadernos y son lentas). En VS Code abre cada `.ipynb` y elige el kernel **env-ia-mlops**.

## 1. Cuaderno 01 · RAW → MASTER (30 min)
Abre `notebooks/01_pipeline_raw_a_master.ipynb` y ejecuta celda a celda (parámetro `FUENTE = 'muestra'`).
**Mira:**
- La carga a RAW: 23 070 filas con `_id`, `_hoja`, `_fila`.
- `master_descartes`: cuántas filas y con qué motivo.
- La conciliación: `raw = master_lineas + descartes`.
- `master_calidad`: las 13 reglas deben estar en `OK`.

**Preguntas:** ¿cuántas líneas no tienen cliente? ¿Por qué no se descartan?
**Comprobación:** `SELECT COUNT(*) FROM raw_online_retail_ii;` da 23 070 en el visor SQLite.

## 2. Cuaderno 02 · MASTER → FS (25 min)
Ejecuta `notebooks/02_pipeline_master_a_fs.ipynb`.
**Mira:** `fs_catalogo` (13 variables), una fila de `fs_cliente_corte` y el recálculo manual con pandas del cliente de ejemplo.
**Haz:** cambia el corte de ejemplo a otra fecha y comprueba que la recencia cambia como esperas.
**Prueba definitiva** (terminal):
```bash
python -m pytest tests -k futuro -q
```
Esperado: `2 passed` (todas las pruebas cuyo nombre contiene «futuro»). Esta prueba borra todo lo posterior al corte y comprueba que las variables no cambian.

## Pausa (10 min)

## 3. Cuaderno 03 · FS → ML (25 min)
Ejecuta `notebooks/03_pipeline_fs_a_ml.ipynb`.
**Mira:** `ml_particiones` (ventanas que no se solapan), el número de filas y la tasa de recompra por partición (con la muestra: train 626 filas · 50,8 %, valid 114 · 45,6 %, test 250 · 40,4 %).
**Pregunta:** ¿por qué la tasa baja de train a test? ¿Qué implicaría para un modelo en producción?

## 4. Cuaderno 04 · Entrenar y MLflow (25 min)
Ejecuta `notebooks/04_entrenamiento_y_seguimiento.ipynb`.
**Mira:** la referencia (AUC 0,5), regresión logística y gradient boosting (con la muestra: regresión logística valid 0,698 · test 0,747; gradient boosting 0,663 · 0,735).
Después, desde una terminal en `04-Proyecto-Base`:
```bash
mlflow ui --backend-store-uri sqlite:///models/mlflow.db
```
Abre http://127.0.0.1:5000, entra al experimento `retencion-90d`, selecciona **dos ejecuciones** y pulsa *Compare*.
**Anota:** la huella del dato (`huella_datos`) de ambas. ¿Coincide? Solo entonces la comparación es válida.

## 5. Traducir a `.py` y probar (10 min)
```bash
python -m ia_mlops.pipeline
jupytext --to py:percent notebooks/01_pipeline_raw_a_master.ipynb -o scripts_desde_notebooks/01_pipeline_raw_a_master.py
python -m pytest tests/test_notebooks.py -q
```
(`jupytext` se convierte un cuaderno a la vez; repite con los otros tres si hay tiempo. La prueba de equivalencia puede tardar unos minutos.)
**Pregunta:** ¿qué demuestra la prueba de equivalencia?

## Si algo falla
| Síntoma | Qué hacer |
|---|---|
| `ModuleNotFoundError` en un cuaderno | Kernel equivocado: selecciona `env-ia-mlops`. |
| El 02 falla al leer tablas | Ejecuta primero el 01 completo. |
| `mlflow ui` no abre | Revisa que estés en `04-Proyecto-Base` y que exista `models/mlflow.db` (lo crea el cuaderno 04). |
| La prueba de equivalencia falla | Anota el mensaje en las evidencias; no lo ocultes. |

## Para quien termina antes
Empieza la tarea: [`../tarea/README.md`](../tarea/README.md).
