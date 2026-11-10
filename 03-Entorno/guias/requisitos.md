# Entorno del curso

Solo Windows 10 (1809 o superior) y Windows 11. Guía interactiva y script: `03-Entorno/guia-instalacion/` y `03-Entorno/scripts/instalar_entorno.ps1` (sin probar).

## En tu equipo (obligatorio)
- Git y cuenta GitHub.
- VS Code: Python, Pylance, Jupyter, Container Tools, Kubernetes, Dev Containers.
- Miniconda y el entorno `env-ia-mlops` (`03-Entorno/conda/environment.yml`, 23 paquetes con versión fijada; probado en Linux, sin probar en Windows).
- SQLite (viene con Python) y, opcional, un visor (DB Browser for SQLite).
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

## Versiones
Fijadas en `03-Entorno/conda/environment.yml` (y espejadas en `requirements-dev.txt`); ver `03-Entorno/VALIDACION.md`.
Para dejar el equipo listo para S1, en orden y con comprobaciones: `01-Sesiones/S0-Presentacion-y-Entorno/slides/instalacion/index.html`
y `01-Sesiones/S0-Presentacion-y-Entorno/practica/guia-rapida-entorno-s0-s1.md`.

Los scripts `instalar_entorno.*` instalan los programas con winget y no se han probado en Windows real.
