# Imagen del LOTE: la imagen de la API (que ya lleva el modelo) + lo que necesita `python -m ia_mlops.explotacion`
# para calcular las 13 variables de cada cliente: el SQL de la capa FS y la base de muestra (curso.db).
#
# Parte de la imagen de la API YA CONSTRUIDA, así que vale igual con el Dockerfile de develop (COPY del modelo) y con el
# multi-etapa de la rama dockerfile-clon (--build-context modelo=models): lo que cambia es cómo se hizo la imagen base, no esta.
#
# La API sola NO puede correr el lote: su imagen no lleva sql/ ni data/ (los excluye .dockerignore). Por eso este paso.
# La base de muestra va DENTRO de la imagen porque el curso la congela (148 clientes). En una empresa los datos no se
# hornean en una imagen: se leerían de BigQuery o de un volumen. Es una simplificación del laboratorio, dicha en voz alta.
#
# Construir, desde 04-Proyecto-Base (después de `python -m ia_mlops.pipeline`, que deja data/processed/curso.db), SIN VERIFICAR (no hay Docker aquí):
#   docker build -f ../01-Sesiones/S5-MLOps-y-Operacion/extra-composer-batch/lote.Dockerfile \
#       --build-arg IMAGEN_API=retencion-api:local -t retencion-lote:local .
# Qué entra en el contexto lo decide lote.Dockerfile.dockerignore (junto a este archivo), no el .dockerignore de la raíz.
ARG IMAGEN_API=retencion-api:local
FROM ${IMAGEN_API}

USER root
COPY --chown=10001:10001 sql/fs/02_poblar_fs.sql /app/sql/fs/02_poblar_fs.sql
COPY --chown=10001:10001 data/processed/curso.db /app/data/processed/curso.db
# El lote escribe sus informes en /tmp/reports (CURSO_REPORTES, que fija el DAG): el sistema de archivos de /app no se toca.
USER 10001