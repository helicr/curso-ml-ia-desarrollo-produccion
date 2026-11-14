# S2 · La interfaz de consulta: del ordenador al servicio

**Duración:** unos 60 minutos, después del bloque 4 (la imagen de la API en el Codespace). **Requisito:** `python -m ia_mlops.pipeline` ejecutado; deja `models/modelo_mlflow/` y la base `data/processed/curso.db`.

**La explicación completa**, desde lo básico, está en [**Del ordenador al servicio**](../../../04-Proyecto-Base/docs/del-ordenador-al-servicio.md). Esta hoja es el recorrido de clase: qué hacer, en qué orden y qué preguntarse. Cada paso remite al apartado de la guía.

## La idea en un minuto
Ya tenemos el modelo expuesto como API, pero la API pide **13 variables** por cliente. Quien prepara la campaña solo conoce el **id del cliente** y quiere saber **qué hacer** con él. La interfaz cubre ese hueco:

```text
  ids de cliente ──► variables en la fecha de corte ──► API del modelo ──► probabilidad ──► regla de negocio ──► tramo + recomendación
  (pantalla o CSV)   (el mismo SQL de la capa FS)       (/predecir/lote)                    (config.SEGMENTOS_RECOMPRA)
```

Se hace dos veces, en dos sitios, para ver la diferencia:

| | **A · En mi ordenador** | **B · Dos contenedores en el Codespace** |
|---|---|---|
| Qué corre | Dos procesos Python de tu entorno conda | Dos imágenes: la API (con el modelo) y la interfaz (sin modelo ni datos) |
| Datos | Tu carpeta | Montados como volumen de **solo lectura** |
| Cómo se encuentran | `127.0.0.1` | Por nombre, en una red de Docker (`http://api:8080`) |
| Mensaje | «Funciona en mi máquina»: no se puede sacar de ahí | El artefacto que iría a producción, aunque el Codespace todavía no lo sea |

## A · En mi ordenador (15 min) · guía, apartados 1 y 2
1. **Conceptos (5 min).** Proceso y puerto, `127.0.0.1` frente a `0.0.0.0`, cliente y servidor, dependencias, variables de entorno, vivo y listo (apartado 1).
2. **Arrancar las dos piezas.** Con `conda activate env-ia-mlops`, desde `04-Proyecto-Base`:
   ```text
   python -m uvicorn ia_mlops.api.app:app --host 127.0.0.1 --port 8080      # terminal 1
   python -m ia_mlops.interfaz --url http://127.0.0.1:8080                   # terminal 2 → http://127.0.0.1:8090
   ```
3. **Consultar.** En la página:
   - Escribe `13599` y pulsa **Predecir**: sale 99,8 %, tramo `alta`, puesto 1 de 148. Abre **Variables**: son las 13 que recibió la API.
   - Pulsa **Ejemplo**: cinco clientes repartidos por el ranking y el `99999`, que no existe. Salen los tres tramos y el «sin predicción».
   - Carga un `clientes.csv` con una columna `cliente_id` y descarga el resultado con **Descargar CSV**.
   - Cambia la fecha de corte a `2011-03-01` con `13599`. ¿Por qué cambian las variables?
4. **Vivo frente a listo.** Para la API (Ctrl+C en la terminal 1): `curl http://127.0.0.1:8090/salud` sigue en 200 y `/listo` da 503 con el motivo.
5. **Pregunta para el grupo.** ¿De qué depende que esto funcione? Haz la lista y compárala con la tabla del apartado 2: entorno, archivos, sistema operativo, sesión abierta, `127.0.0.1`.

## B · Dos contenedores en el Codespace (35 min) · guía, apartados 3 a 8
En el Codespace del curso, en la terminal, desde `04-Proyecto-Base`. La imagen de la API ya está construida del bloque 4; si no, `docker build -f deploy/docker/Dockerfile -t retencion-api:local .`.

1. **Repaso de conceptos (5 min).** Imagen, contenedor, contexto, `-p`, `-v …:ro`, red y nombres, `-e`, usuario sin privilegios, `HEALTHCHECK` (apartado 3).
2. **La imagen de la interfaz (10 min, apartado 5).** Lee `deploy/docker/interfaz.Dockerfile` con la tabla del apartado 5.2: no lleva ni modelo ni datos, y sus versiones salen del lock de la API.
   ```text
   docker build -f deploy/docker/interfaz.Dockerfile -t retencion-interfaz:local .
   docker image ls 'retencion-*'                     # anota el tamaño de las dos
   docker run --rm --entrypoint sh retencion-interfaz:local -c 'find /app -type f -not -path "*/ia_mlops/*"'
   ```
3. **Dos contenedores que se hablan (10 min, apartado 6).**
   ```text
   docker network create retencion
   docker run -d --name api --network retencion retencion-api:local                  # sin -p: no se publica
   docker ps                                                                           # espera a «(healthy)»
   docker run -d --name interfaz --network retencion -p 8090:8090 -v "$PWD/data/processed:/datos:ro" retencion-interfaz:local
   curl http://127.0.0.1:8090/listo                                                    # "modelo":"http://api:8080"
   ```
   Abre el puerto **8090** desde la pestaña **Puertos** y repite las consultas de la parte A. **Los números deben ser los mismos.**
4. **Romper a propósito (5 min, apartados 6.5 y 7).** Apunta lo que esperas antes de cada prueba:
   - Arrancar una interfaz con `-e CURSO_URL_API=http://127.0.0.1:8080` → 503. Dentro de un contenedor, `127.0.0.1` es él mismo.
   - `docker exec interfaz sh -c 'echo x > /datos/intruso'` → *Read-only file system*.
   - `curl http://127.0.0.1:8080/salud` → no conecta, porque la API no tiene `-p`.
   - `docker stop api` → `/salud` 200 y `/listo` 503.
5. **Lo mismo en un archivo (5 min, apartado 8).** Limpia lo anterior y levántalo todo con Compose:
   ```text
   docker rm -f api interfaz; docker network rm retencion
   docker compose -f deploy/docker/compose.yaml up --build -d
   docker compose -f deploy/docker/compose.yaml ps
   docker compose -f deploy/docker/compose.yaml down
   ```
   Compara cada bandera de `docker run` con su línea en `compose.yaml` (tabla del apartado 8).

## C · ¿Esto ya es producción? (10 min) · guía, apartados 9 a 11
- **Recorre la tabla del apartado 9** y señala qué parte se ve en cada sesión:
  - dónde corre, IAM, imágenes, datos en BigQuery y secretos: **S3**;
  - despliegue automático con aprobación: **S4**;
  - alertas, deriva y *rollback*: **S5**.
- **La idea que hay que llevarse:** pasar a producción **no cambia el código ni las imágenes**. Cambia dónde corren y lo que las rodea.
- **Autoevaluación** del apartado 11: seis preguntas con su respuesta plegada.

## Para pensar
- **«Revisar».** Con el corte de hoy, 132 de los 148 clientes salen con «revisar», y el aviso dice `antiguedad_dias=738 … fuera del rango visto al entrenar [1, 364]`. ¿Por qué ocurre con un modelo entrenado con cortes de 2010? ¿Qué harías antes de usar estas predicciones? (Pista: deriva, S5.)
- **¿A quién va el incentivo?** La interfaz propone el tramo **medio**. El laboratorio extra (`python -m ia_mlops.explotacion`) marca el 10 % con **más** probabilidad. ¿Qué objetivo de negocio tiene cada criterio?
- **¿Por qué dos imágenes y no una?** ¿Qué llevaría dentro la imagen si la API buscara las variables por id? (Apartado 5.1.)

## Qué se probó
- **En local:** `tests/test_interfaz.py` y `tests/test_imagen_interfaz.py`. La parte A se probó a mano en Windows el 14/11/2026.
- **Sin Docker:** el contenedor de la interfaz se simuló en Windows (base de solo lectura y variables de entorno del Dockerfile) contra la API real.
- **Con Docker real:** el workflow `validar-dos-contenedores.yml` cubre la parte B y las roturas. **Pendiente de su primera ejecución.**
- **Sin probar a mano en un Codespace.**
