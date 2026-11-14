# Imagen de la INTERFAZ de consulta (S2): ids de cliente -> variables (SQL de FS) -> API del modelo -> recomendacion.
#
# Es la segunda pieza del servicio. La primera es la API del modelo (deploy/docker/Dockerfile).
#   - NO lleva el modelo: se lo pide a la API por la red (CURSO_URL_API).
#   - NO lleva los datos: la base se monta como volumen de solo lectura en /datos.
#   - Solo lleva el codigo y el SQL con el que se calculan las variables (sql/fs/02_poblar_fs.sql).
#
# Construir, desde la carpeta del proyecto (04-Proyecto-Base en el curso):
#   docker build -f deploy/docker/interfaz.Dockerfile -t retencion-interfaz:local .
# Que entra en el contexto lo decide  deploy/docker/interfaz.Dockerfile.dockerignore  (no el .dockerignore de la raiz, que es el de la API).
#
# Ejecutar (con la API en la red «retencion» y el nombre «api»; ver docs/del-ordenador-al-servicio.md o compose.yaml):
#   docker run --rm --name interfaz --network retencion -p 8090:8090 -v "$PWD/data/processed:/datos:ro" retencion-interfaz:local
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    CURSO_DB=/datos/curso.db \
    CURSO_DB_SOLO_LECTURA=1 \
    CURSO_URL_API=http://api:8080

WORKDIR /app

# 1) Dependencias primero (capa que casi nunca cambia). Las versiones las fija el lock de la API: las dos imagenes usan las mismas.
COPY requirements-api.lock requirements-interfaz.txt ./
RUN pip install -c requirements-api.lock -r requirements-interfaz.txt

# 2) Codigo y el SQL de las variables. Nada de datos ni de modelo.
COPY ia_mlops/ ia_mlops/
COPY sql/fs/02_poblar_fs.sql sql/fs/02_poblar_fs.sql

# 3) Sin privilegios. El punto de montaje existe y es de solo lectura para el proceso.
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin appuser && mkdir /datos
USER 10001

EXPOSE 8090
# /salud y no /listo: si la API cae, la interfaz no se arregla reiniciandola (/listo lo explica con un 503).
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8090/salud', timeout=2)"

CMD ["uvicorn", "ia_mlops.interfaz.app:app", "--host", "0.0.0.0", "--port", "8090"]
