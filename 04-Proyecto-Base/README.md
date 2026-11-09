# Proyecto base: retención de clientes con Online Retail II

> Proyecto Python con la estructura de **Cookiecutter Data Science**. Los **cuadernos** son los pipelines; el paquete **`ia_mlops`**
> es su traducción a `.py`, la que se empaqueta, se prueba y se despliega desde S2.

**Pregunta de negocio:** dado un cliente y una fecha de corte, ¿volverá a comprar en los **90 días siguientes**?
**Dato:** Online Retail II (UCI, licencia CC BY 4.0), 1 067 371 líneas de una tienda online, 2009–2011. Ver `docs/modelo-de-datos.md` y `references/fuente.md`.

## Las capas, en este orden
```
RAW  →  MASTER  →  FS  →  ML  →  ARTEFACTOS  →  SERVICIO (S2)
```
**FS va antes que ML:** ML se construye a partir de las variables de FS, más el objetivo y la partición.

| Capa | Cuaderno (el pipeline) | Paquete (traducción a `.py`) | SQL |
|---|---|---|---|
| RAW y MASTER | `notebooks/01_pipeline_raw_a_master.ipynb` | `ia_mlops/dataset.py`, `ia_mlops/calidad.py` | `sql/raw/`, `sql/master/` |
| FS | `notebooks/02_pipeline_master_a_fs.ipynb` | `ia_mlops/features.py` | `sql/fs/` |
| ML | `notebooks/03_pipeline_fs_a_ml.ipynb` | `ia_mlops/modeling/ml_dataset.py` | `sql/ml/` |
| Entrenamiento y MLflow | `notebooks/04_entrenamiento_y_seguimiento.ipynb` | `ia_mlops/modeling/train.py` | |
| Predicción (base de la API) | | `ia_mlops/modeling/predict.py` | |

## Estructura (Cookiecutter Data Science)
```
04-Proyecto-Base/
├── README.md · Makefile · pyproject.toml
├── data/
│   ├── raw/            muestra_online_retail_ii.csv (en el repo) y online_retail_ii/ (el original, se descarga)
│   ├── external/       datos de terceros                     interim/   pasos intermedios
│   └── processed/      curso.db: la base SQLite con todas las capas
├── docs/               modelo-de-datos.md · de-notebook-a-python.md
├── models/             modelo.joblib · metadatos.json · mlflow.db (se generan)
├── notebooks/          los cuatro cuadernos-pipeline
├── references/         fuente del dato y licencia
├── reports/            metricas.json y figures/ (se generan)
├── sql/                esquemas (DDL) y scripts de inserción de cada capa
├── ia_mlops/           el paquete Python
│   ├── config.py · db.py · calidad.py · dataset.py · features.py · pipeline.py
│   ├── modeling/       ml_dataset.py · train.py · predict.py
│   └── api/            la API de S2
├── deploy/             docker · cloud-run · kubernetes (S2 a S5)
└── tests/              34 pruebas, incluida la equivalencia cuaderno = paquete
```

## Empezar (con el entorno `env-ia-mlops` activo, desde esta carpeta)
```text
pip install -e .                                   # instala ia_mlops en modo editable (una vez)
python -m ia_mlops.pipeline                        # todo el flujo con la muestra (segundos)
```
Los **cuadernos** (el camino de S1): ábrelos en VS Code con el kernel `env-ia-mlops` y ejecútalos en orden, o desde la terminal:
```text
papermill notebooks/01_pipeline_raw_a_master.ipynb salida01.ipynb -p FUENTE muestra
```
Con el dato **completo** (1,07 millones de filas, unos 2 minutos):
```text
python -m ia_mlops.dataset descargar               # baja el Excel de UCI y verifica su huella sha256
python -m ia_mlops.pipeline --fuente completo
```
`make` hace lo mismo con atajos (`make pipeline`, `make notebooks`, `make test`, `make traducir`). En Windows no hay `make`: ejecuta las líneas `python` y `papermill` del `Makefile`.

## De cuaderno a Python
Dos caminos, y las pruebas exigen que den **el mismo resultado**: ver `docs/de-notebook-a-python.md`.
1. **Traducción literal** con jupytext: `make traducir` deja un `.py` por cuaderno en `scripts_desde_notebooks/`.
2. **Refactorización** a funciones con nombre, rutas configurables y registro: es el paquete `ia_mlops`.

## Pruebas
```text
python -m pytest tests                  # todas (incluye ejecutar los cuadernos)
python -m pytest tests -m "not lento"   # sin ejecutar los cuadernos
```
Comprueban, entre otras cosas: que `raw = master + descartes`, la integridad referencial, que **FS no usa información del futuro**, que la partición es temporal y sus
ventanas no se solapan, que el objetivo se recalcula igual con pandas, que los cuadernos y el paquete producen **las mismas tablas y las mismas métricas**, y que los cuadernos
traducidos a `.py` con jupytext también.

## Resultados con el dato completo
| Modelo | AUC en test | Aciertos entre el 10 % con más probabilidad |
|---|---|---|
| Referencia sin aprender (tasa base 38 %) | 0,500 | 34 % |
| **Regresión logística** | **0,796** | **90 %** |
| Gradient boosting | 0,781 | 88 % |

La tasa de recompra cambia entre periodos (48 % en train, 35 % en valid, 38 % en test): es el punto de partida para hablar de **deriva** en S5.
Las cifras salen de `reports/metricas.json` tras ejecutar el pipeline completo.

## Estado
S1 usa los cuatro cuadernos. S2 construirá la API en `ia_mlops/api/` sobre `predict.py`; los Dockerfile irán en `deploy/docker/`.
