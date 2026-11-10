# Comandos del proyecto. Uso:  make <orden>
# En Windows no hay `make` por defecto: ejecuta las lineas que empiezan por `python` o `papermill` directamente
# desde Anaconda Prompt (cada orden indica su equivalente). En Codespaces y en GitHub Actions `make` si esta.
PYTHON ?= python
FUENTE ?= muestra

.PHONY: ayuda datos pipeline notebooks traducir test test-rapido api comparar imagen contenedor lock limpiar

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

api:  ## Arranca la API en http://127.0.0.1:8080 (docs en /docs). Antes: make pipeline
	$(PYTHON) -m uvicorn ia_mlops.api.app:app --host 127.0.0.1 --port 8080

comparar:  ## Compara paquete, joblib y MLflow y, con URL=http://127.0.0.1:8080, tambien la API. Antes: make pipeline
	$(PYTHON) -m ia_mlops.modeling.comparar $(if $(URL),--url $(URL),)

imagen:  ## Construye la imagen Docker (en Codespaces; en tu equipo no hay Docker). Antes: make pipeline
	docker build -f deploy/docker/Dockerfile -t retencion-api:local .

contenedor:  ## Ejecuta la imagen en http://127.0.0.1:8080
	docker run --rm -p 8080:8080 retencion-api:local

lock:  ## Regenera requirements-api.lock (versiones exactas) en un entorno vacio con uv
	uv venv .venv-lock --python 3.11 -q && uv pip install -r requirements-api.txt --python .venv-lock/bin/python -q
	(echo "# Dependencias EXACTAS (directas y transitivas) de la imagen. Se genera con:  make lock   (a partir de requirements-api.txt, en un entorno vacio)"; echo "# La imagen instala ESTE archivo para que dos construcciones den las mismas versiones."; uv pip freeze --python .venv-lock/bin/python) > requirements-api.lock
	rm -rf .venv-lock

limpiar:  ## Borra lo generado (base de datos, modelos y reportes). No toca los datos originales
	rm -f data/processed/*.db models/*.joblib models/*.json models/mlflow.db reports/metricas.json
	rm -rf models/modelo_mlflow models/mlartifacts reports/notebooks_ejecutados scripts_desde_notebooks
