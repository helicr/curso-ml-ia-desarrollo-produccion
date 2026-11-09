# Comandos del proyecto. Uso:  make <orden>
# En Windows no hay `make` por defecto: ejecuta las lineas que empiezan por `python` o `papermill` directamente
# desde Anaconda Prompt (cada orden indica su equivalente). En Codespaces y en GitHub Actions `make` si esta.
PYTHON ?= python
FUENTE ?= muestra

.PHONY: ayuda datos pipeline notebooks traducir test test-rapido limpiar

ayuda:  ## Muestra esta ayuda
	@grep -E '^[a-z-]+:.*##' Makefile | sed 's/:.*##/ -> /'

datos:  ## Descarga el dataset completo de UCI y verifica su huella
	$(PYTHON) -m ia_mlops.dataset descargar

pipeline:  ## Ejecuta raw -> master -> fs -> ml -> entrenar con el codigo Python (FUENTE=muestra|completo)
	$(PYTHON) -m ia_mlops.pipeline --fuente $(FUENTE)

notebooks:  ## Ejecuta los cuatro cuadernos-pipeline en orden y guarda las copias ejecutadas en reports/notebooks_ejecutados
	mkdir -p reports/notebooks_ejecutados
	papermill notebooks/01_pipeline_raw_a_master.ipynb reports/notebooks_ejecutados/01.ipynb -p FUENTE $(FUENTE)
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

limpiar:  ## Borra lo generado (base de datos, modelos y reportes). No toca los datos originales
	rm -f data/processed/*.db models/*.joblib models/*.json models/mlflow.db reports/metricas.json
	rm -rf models/mlartifacts reports/notebooks_ejecutados scripts_desde_notebooks
