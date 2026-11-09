# Entorno del curso

Solo Windows 10 (1809 o superior) y Windows 11. Guía interactiva y script: `03-Entorno/guia-instalacion/` y `03-Entorno/scripts/instalar_entorno.ps1` (sin probar).

## En tu equipo (obligatorio)
- Git y cuenta GitHub.
- VS Code: Python, Pylance, Jupyter, Container Tools, Kubernetes, Dev Containers.
- Miniconda; entornos definitivos por publicar y probar.
- SQLite y visor de referencia (DB Browser for SQLite) por confirmar.
- Google Cloud CLI, cuenta elegible para trial y proyecto configurado (o usar Cloud Shell, ver guía).

## En la nube (sin instalar nada local)
- Codespaces del curso con Docker, kind y kubectl preconfigurados.
- GitHub Actions para orquestar pipelines y construir imágenes.
- Google Cloud: Artifact Registry y Cloud Run.

Docker Desktop local es **opcional**. GKE no es requisito.
Ver `docker-y-kubernetes-sin-instalacion-local.md`.

## Entornos de Python
- `env-ia-mlops`: el entorno del curso (obligatorio). Archivo: `03-Entorno/conda/environment.yml`.
- `env-ia-opcional`: red neuronal y LLM (opcional). Aún no existe.

## Opcional (ampliaciones)
PyTorch para el módulo neuronal; motor y modelo LLM por confirmar. No requieren GPU.

## Dependencias previstas, no versión definitiva
pandas, PyArrow, scikit-learn, joblib, MLflow, Jupyter, ipykernel,
FastAPI, Uvicorn, Pydantic, pytest y requests/httpx.

La implementación completa del instalador está pendiente. No se incluyen
archivos environment.yml ficticios ni scripts vacíos presentados como funcionales.
