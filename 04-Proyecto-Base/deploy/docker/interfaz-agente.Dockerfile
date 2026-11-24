# Imagen de la INTERFAZ con la pestaña «Asistente» (S5): la de interfaz.Dockerfile + las skills del agente + httpx (para hablar con Ollama).
#
# Por qué una imagen aparte y no cambiar interfaz.Dockerfile: la interfaz de S2/S4 no necesita nada del agente y sus pruebas exigen que
# requirements-interfaz.txt solo lleve paquetes fijados por requirements-api.lock (httpx no está en ese lock). Aquí se añade httpx SIN fijar su versión
# (ni la de sus dependencias: httpcore, h11, anyio, certifi): es lo único no reproducible de esta imagen. Si el curso la adopta, hay que añadirlo al lock.
# Que entra en el contexto lo decide  deploy/docker/interfaz-agente.Dockerfile.dockerignore.
#
# Construir, desde 04-Proyecto-Base:
#   docker build -f deploy/docker/interfaz-agente.Dockerfile -t retencion-interfaz-agente:local .
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    CURSO_DB=/datos/curso.db \
    CURSO_DB_SOLO_LECTURA=1 \
    CURSO_URL_API=http://api:8080 \
    CURSO_LLM=falso

WORKDIR /app

COPY requirements-api.lock requirements-interfaz.txt ./
RUN pip install -c requirements-api.lock -r requirements-interfaz.txt httpx

COPY ia_mlops/ ia_mlops/
COPY skills/ skills/
COPY sql/fs/02_poblar_fs.sql sql/fs/02_poblar_fs.sql

RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin appuser && mkdir /datos
USER 10001

EXPOSE 8090
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8090/salud', timeout=2)"

CMD ["uvicorn", "ia_mlops.interfaz.app:app", "--host", "0.0.0.0", "--port", "8090"]
