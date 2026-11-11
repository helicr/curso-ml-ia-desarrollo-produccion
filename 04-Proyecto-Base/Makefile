# Comandos del proyecto. Uso:  make <orden>
# En Windows no hay `make` por defecto: ejecuta las lineas que empiezan por `python` o `papermill` directamente
# desde Anaconda Prompt (cada orden indica su equivalente). En Codespaces y en GitHub Actions `make` si esta.
PYTHON ?= python
FUENTE ?= muestra

FORZAR ?=

.PHONY: ayuda datos operacional raw master ml train pipeline notebooks traducir test test-rapido diagramas limpiar

ayuda:  ## Muestra esta ayuda
	@grep -E '^[a-z-]+:.*##' Makefile | sed 's/:.*##/ -> /'

datos:  ## Descarga el dataset completo de UCI y verifica su huella
	$(PYTHON) -m ia_mlops.dataset descargar

operacional:  ## Simula la base de ventas retail.db desde el archivo de UCI (FUENTE=muestra|completo)
	$(PYTHON) -m ia_mlops.operacional --fuente $(FUENTE)

raw:  ## pipeline_ingesta_raw: retail.db -> RAW (idempotente; FORZAR=--forzar para rehacerlo)
	$(PYTHON) -m ia_mlops.pipeline_ingesta_raw $(FORZAR)

master:  ## pipeline_ingesta_master: RAW -> MASTER + reglas de calidad
	$(PYTHON) -m ia_mlops.pipeline_ingesta_master $(FORZAR)

ml:  ## pipeline_ml: MASTER -> FS -> ML
	$(PYTHON) -m ia_mlops.pipeline_ml $(FORZAR)

train:  ## pipeline_train: ML -> modelo, metricas y MLflow
	$(PYTHON) -m ia_mlops.pipeline_train $(FORZAR)

pipeline:  ## Los cuatro pipelines en orden (los que no tienen cambios no hacen nada). Antes: make operacional
	$(PYTHON) -m ia_mlops.pipeline $(FORZAR)

notebooks:  ## Ejecuta los cinco cuadernos-pipeline en orden y guarda las copias ejecutadas en reports/notebooks_ejecutados
	mkdir -p reports/notebooks_ejecutados
	papermill notebooks/00_pipeline_operacional.ipynb reports/notebooks_ejecutados/00.ipynb -p FUENTE $(FUENTE)
	papermill notebooks/01_pipeline_raw_a_master.ipynb reports/notebooks_ejecutados/01.ipynb
	papermill notebooks/02_pipeline_master_a_fs.ipynb reports/notebooks_ejecutados/02.ipynb
	papermill notebooks/03_pipeline_fs_a_ml.ipynb reports/notebooks_ejecutados/03.ipynb
	papermill notebooks/04_entrenamiento_y_seguimiento.ipynb reports/notebooks_ejecutados/04.ipynb

traducir:  ## Traduce literalmente los cuadernos a scripts .py (jupytext) en scripts_desde_notebooks/
	mkdir -p scripts_desde_notebooks
	for f in notebooks/*.ipynb; do jupytext --to py:percent "$$f" -o "scripts_desde_notebooks/$$(basename $$f .ipynb).py"; done

test:  ## Todas las pruebas (incluye ejecutar los cuadernos)
	$(PYTHON) -m pytest tests

test-rapido:  ## Pruebas sin ejecutar los cuadernos
	$(PYTHON) -m pytest tests -m "not lento"

diagramas:  ## Regenera las imagenes de docs/img (el cuaderno 00 las lleva embebidas: regeneralo despues)
	$(PYTHON) docs/img/generar_diagramas.py

limpiar:  ## Borra lo generado (bases de datos, modelos y reportes). No toca los datos originales
	rm -f data/external/retail.db data/processed/*.db models/*.joblib models/*.json models/mlflow.db reports/metricas.json
	rm -rf models/mlartifacts reports/notebooks_ejecutados scripts_desde_notebooks
