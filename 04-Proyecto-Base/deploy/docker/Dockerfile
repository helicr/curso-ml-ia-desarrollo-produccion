# Imagen de la API de recompra (S2). El modelo (models/) se ENTRENA antes con `make pipeline`: la imagen solo lo sirve.
#
# Construir y probar, desde la carpeta del proyecto (04-Proyecto-Base en el curso; la raiz de TU repositorio en tu caso):
#   make pipeline
#   docker build -f deploy/docker/Dockerfile -t retencion-api:local .
#   docker run --rm -p 8080:8080 retencion-api:local
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    CURSO_MODELOS=/app/models

WORKDIR /app

# 1) Dependencias primero: esta capa solo se reconstruye si cambia el archivo de versiones exactas.
#    requirements-api.lock sale de requirements-api.txt con `make lock`.
COPY requirements-api.lock .
RUN pip install -r requirements-api.lock

# 2) Codigo y modelo (solo lo necesario para servir; ver .dockerignore).
COPY ia_mlops/ ia_mlops/
COPY models/modelo_mlflow/ models/modelo_mlflow/
COPY models/metadatos.json models/metadatos.json

# 3) No se ejecuta como root.
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin apiuser
USER 10001

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/salud', timeout=2)"

CMD ["uvicorn", "ia_mlops.api.app:app", "--host", "0.0.0.0", "--port", "8080"]
