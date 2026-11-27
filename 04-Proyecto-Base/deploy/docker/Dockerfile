# syntax=docker/dockerfile:1
# Imagen de la API de recompra (S2, S4). Multi-etapa: el CÓDIGO sale del repositorio clonado en el commit exacto (o de tu
# carpeta, para desarrollar) y el MODELO entra aparte, por un contexto con nombre: el que se entrenó y validó, no otro.
#
# ¿Por qué así? (27/11/2026)
#   - Construir desde la carpeta de trabajo mete en la imagen lo que haya en ella: cambios sin commit, un modelo viejo
#     de otra prueba... La imagen saldría de TU Codespace, no del repositorio. Con FUENTE=git, la etapa «fuente-git»
#     clona el repositorio en una carpeta temporal, copia solo la carpeta del proyecto y esa etapa se TIRA entera: en la
#     imagen final no queda git, ni el clon, ni el token.
#   - El modelo NO se entrena aquí: en S4 la puerta de calidad aprueba UN modelo (entrenado con los datos completos, que
#     no están en el repositorio) y la imagen tiene que llevar ESE. Por eso entra como contexto «modelo»: una carpeta
#     con modelo_mlflow/ y metadatos.json.
#
# Construir (desde la carpeta del proyecto: 04-Proyecto-Base en el curso; la raíz de TU repositorio en tu caso):
#   make pipeline                                   # entrena: deja models/modelo_mlflow y models/metadatos.json
#   # producción (Actions): el código del commit, clonado
#   docker build -f deploy/docker/Dockerfile --build-arg REF=<sha o rama> --build-context modelo=models -t retencion-api .
#   # desarrollo (Codespace): el código de tu carpeta, para probar lo que aún no has subido
#   docker build -f deploy/docker/Dockerfile --build-arg FUENTE=contexto --build-context modelo=models -t retencion-api:local .
#   docker run --rm -p 8080:8080 retencion-api:local
#
# Argumentos (con FUENTE=git):
#   REPO_URL   repositorio a clonar (por defecto, el del curso). En TU repositorio: https://github.com/<tú>/<repo>.git
#   REF        commit o rama a clonar (por defecto develop). En Actions: ${{ github.sha }}, el commit que se ha probado.
#   CARPETA    carpeta del proyecto dentro del repositorio (04-Proyecto-Base en el curso; «.» si es la raíz).
#   Repositorio privado: el token entra como SECRETO de BuildKit (no queda en ninguna capa ni en `docker history`):
#     docker build ... --secret id=git_token,env=GIT_TOKEN        (en Actions: env GIT_TOKEN: ${{ github.token }})
ARG FUENTE=git

# ---- Código: del repositorio clonado (por defecto) ----------------------------------------------------------------
FROM python:3.11-slim AS fuente-git
ARG REPO_URL=https://github.com/helicr/curso-ml-ia-desarrollo-produccion.git
ARG REF=develop
ARG CARPETA=04-Proyecto-Base
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*
# Clon superficial del commit pedido en /tmp/repo, copia de lo necesario a /src y fuera el clon.
RUN --mount=type=secret,id=git_token,required=false \
    set -eu; \
    url="$REPO_URL"; \
    if [ -s /run/secrets/git_token ]; then \
      url="$(printf '%s' "$REPO_URL" | sed "s#^https://#https://x-access-token:$(cat /run/secrets/git_token)@#")"; \
    fi; \
    git init -q /tmp/repo; \
    git -C /tmp/repo fetch -q --depth 1 "$url" "$REF"; \
    git -C /tmp/repo checkout -q FETCH_HEAD; \
    mkdir -p /src; \
    cp /tmp/repo/"$CARPETA"/requirements-api.lock /src/; \
    cp -r /tmp/repo/"$CARPETA"/ia_mlops /src/ia_mlops; \
    git -C /tmp/repo rev-parse HEAD > /src/COMMIT; \
    rm -rf /tmp/repo

# ---- Código: de la carpeta de trabajo (FUENTE=contexto, para desarrollar) -----------------------------------------
FROM scratch AS fuente-contexto
COPY requirements-api.lock /src/
COPY ia_mlops/ /src/ia_mlops/

FROM fuente-${FUENTE} AS fuente

# ---- La imagen que se sirve ----------------------------------------------------------------------------------------
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    CURSO_MODELOS=/app/models

WORKDIR /app

# 1) Dependencias primero: esta capa solo se reconstruye si cambia el archivo de versiones exactas.
#    requirements-api.lock sale de requirements-api.txt con `make lock`.
COPY --from=fuente /src/requirements-api.lock .
RUN pip install -r requirements-api.lock

# 2) Código (de la fuente elegida) y modelo (del contexto «modelo»: el entrenado y validado).
COPY --from=fuente /src/ia_mlops/ ia_mlops/
COPY --from=modelo modelo_mlflow/ models/modelo_mlflow/
COPY --from=modelo metadatos.json models/metadatos.json

# 3) No se ejecuta como root.
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin apiuser
USER 10001

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/salud', timeout=2)"

CMD ["uvicorn", "ia_mlops.api.app:app", "--host", "0.0.0.0", "--port", "8080"]
