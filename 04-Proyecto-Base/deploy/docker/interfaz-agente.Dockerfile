# syntax=docker/dockerfile:1
# Imagen de la INTERFAZ con la pestaña «Asistente» (S5): la de interfaz.Dockerfile + las skills del agente + httpx (para hablar con Ollama).
#
# Por qué una imagen aparte y no cambiar interfaz.Dockerfile: la interfaz de S2/S4 no necesita nada del agente y sus pruebas exigen que
# requirements-interfaz.txt solo lleve paquetes fijados por requirements-api.lock (httpx no está en ese lock). Aquí se añade httpx SIN fijar su versión
# (ni la de sus dependencias: httpcore, h11, anyio, certifi): es lo único no reproducible de esta imagen. Si el curso la adopta, hay que añadirlo al lock.
#
# El CÓDIGO sale del repositorio clonado en el commit exacto (FUENTE=git, por defecto) o de tu carpeta (FUENTE=contexto,
# para desarrollar), igual que en deploy/docker/Dockerfile; la etapa del clon se tira entera.
# Con FUENTE=contexto, que entra en el contexto lo decide  deploy/docker/interfaz-agente.Dockerfile.dockerignore.
#
# Construir, desde 04-Proyecto-Base:
#   docker build -f deploy/docker/interfaz-agente.Dockerfile --build-arg REF=<sha o rama> -t retencion-interfaz-agente .
#   docker build -f deploy/docker/interfaz-agente.Dockerfile --build-arg FUENTE=contexto -t retencion-interfaz-agente:local .
ARG FUENTE=git

FROM python:3.11-slim AS fuente-git
ARG REPO_URL=https://github.com/helicr/curso-ml-ia-desarrollo-produccion.git
ARG REF=develop
ARG CARPETA=04-Proyecto-Base
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*
RUN --mount=type=secret,id=git_token,required=false \
    set -eu; \
    url="$REPO_URL"; \
    if [ -s /run/secrets/git_token ]; then \
      url="$(printf '%s' "$REPO_URL" | sed "s#^https://#https://x-access-token:$(cat /run/secrets/git_token)@#")"; \
    fi; \
    git init -q /tmp/repo; \
    git -C /tmp/repo fetch -q --depth 1 "$url" "$REF"; \
    git -C /tmp/repo checkout -q FETCH_HEAD; \
    mkdir -p /src/sql/fs; \
    cp /tmp/repo/"$CARPETA"/requirements-api.lock /tmp/repo/"$CARPETA"/requirements-interfaz.txt /src/; \
    cp -r /tmp/repo/"$CARPETA"/ia_mlops /src/ia_mlops; \
    cp -r /tmp/repo/"$CARPETA"/skills /src/skills; \
    cp /tmp/repo/"$CARPETA"/sql/fs/02_poblar_fs.sql /src/sql/fs/; \
    git -C /tmp/repo rev-parse HEAD > /src/COMMIT; \
    rm -rf /tmp/repo

FROM scratch AS fuente-contexto
COPY requirements-api.lock requirements-interfaz.txt /src/
COPY ia_mlops/ /src/ia_mlops/
COPY skills/ /src/skills/
COPY sql/fs/02_poblar_fs.sql /src/sql/fs/02_poblar_fs.sql

FROM fuente-${FUENTE} AS fuente

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

COPY --from=fuente /src/requirements-api.lock /src/requirements-interfaz.txt ./
RUN pip install -c requirements-api.lock -r requirements-interfaz.txt httpx

COPY --from=fuente /src/ia_mlops/ ia_mlops/
COPY --from=fuente /src/skills/ skills/
COPY --from=fuente /src/sql/fs/02_poblar_fs.sql sql/fs/02_poblar_fs.sql

RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin appuser && mkdir /datos
USER 10001

EXPOSE 8090
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8090/salud', timeout=2)"

CMD ["uvicorn", "ia_mlops.interfaz.app:app", "--host", "0.0.0.0", "--port", "8090"]
