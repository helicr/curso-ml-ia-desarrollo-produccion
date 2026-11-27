# Levantar la producción completa en el Codespace del curso

> **Estado: sin verificar en Codespace.** Cada orden de esta página está sacada de los archivos del repositorio, pero todavía no se ha ejecutado en un Codespace. Las partes que sí se han comprobado hasta ahora son la lógica de la interfaz (en local, sin contenedores) y las pruebas estáticas del compose. Todo lo que dice «qué debes ver» y «si falla» está **sin verificar en Codespace** hasta que se ejecute y se anote aquí.

Vas a levantar dos contenedores, la **API del modelo** y la **interfaz con el panel de producción**, y a ver los tres modos de inferencia (lote, bajo demanda y online) con un cliente real del caso Online Retail II.

Todas las órdenes se ejecutan desde la carpeta del proyecto:

```bash
cd 04-Proyecto-Base
```

## 0. Traer lo último de `develop`

Un Codespace **no se actualiza solo**: si el profesor ha publicado cambios después de crearlo, tráelos antes de empezar.

```bash
git fetch origin
git status -sb          # debe decir «behind N»
git pull origin develop
```

Si `develop` no existe en tu fork, lo hiciste con «Copy the `main` branch only» (ver `CONFIGURAR-REPOSITORIO.md`, apartado 0). Si alguna orden de `curl` de esta página no te funciona en tu portátil con Windows, mira las variantes para `cmd` y PowerShell 5.1 en la guía, apartado 4.1.

## 1. Preparar los datos y el modelo

El compose no crea los datos: se dejan antes con tres órdenes.

```bash
python -m ia_mlops.operacional      # la base operacional (la fuente)
python -m ia_mlops.pipeline         # entrena el modelo (models/) y crea la base analítica (data/processed/curso.db)
python -m ia_mlops.explotacion      # el lote: escribe reports/campana/ y la tabla fs_produccion en curso.db
```

**Qué debes ver (sin verificar en Codespace).** El último comando imprime el resumen de la campaña y deja en `reports/campana/` dos archivos, `campana_<corte>.csv` y `campana_<corte>.json`. Compruébalo con:

```bash
ls reports/campana
```

**Si falla (sin verificar en Codespace).**
- «No existe ...»: te has saltado un paso; ejecuta las tres órdenes en ese orden.
- Un `ModuleNotFoundError`: instala las dependencias con `pip install -r requirements-dev.txt && pip install -e . --no-deps`.

## 2. Levantar el compose

```bash
docker compose -f deploy/docker/compose-produccion.yaml up --build -d
docker compose -f deploy/docker/compose-produccion.yaml ps
```

**Qué debes ver (sin verificar en Codespace).** Dos servicios, `api` e `interfaz`. La `api` pasa a «healthy» y la `interfaz` arranca después. La `api` no muestra puertos publicados; la `interfaz` publica el `8090`. La primera vez tarda unos minutos porque construye las dos imágenes.

Espera a que la interfaz esté lista:

```bash
curl -fsS http://127.0.0.1:8090/listo
```

Debe responder con `"estado": "listo"`. Si todavía no responde, repite la orden pasados unos segundos.

**Si falla (sin verificar en Codespace).**
- `curl` responde 503: lee el motivo en el JSON; casi siempre la API aún no está sana. Mira `docker compose -f deploy/docker/compose-produccion.yaml logs api interfaz`.
- Error al montar `models/historial_versiones.json` o `reports/campana`: falta el archivo o la carpeta porque no ejecutaste el paso 1 (o estás en otra carpeta que no es `04-Proyecto-Base`).
- Quieres usar la imagen publicada en GHCR en vez de construirla: `export IMAGEN_API=ghcr.io/<propietario-en-minúsculas>/retencion-api:<etiqueta>` (la etiqueta está en `models/referencia.json`) y levanta con `up -d --pull always --no-build`.

## 3. Abrir el panel

En la pestaña **Puertos** del Codespace, abre el puerto **8090** y añade `/panel` a la dirección. Las pestañas son **Lote**, **Bajo demanda**, **Online** y **Versiones**.

**Qué debes ver (sin verificar en Codespace).**
- **Lote:** la última campaña, con su corte, la versión del modelo y los primeros clientes.
- **Versiones:** la versión en producción de `models/referencia.json` y su historial.

**Si falla (sin verificar en Codespace).**
- Pestaña Lote vacía con «Todavía no hay campaña»: la carpeta `reports/campana` estaba vacía al levantar; repite el paso 1 y reinicia con `down` y `up`.
- La página no abre: comprueba en la pestaña Puertos que el 8090 está publicado.

## 4. Probar la compra simulada

Con el mismo cliente en los dos modos (por ejemplo, el primero de la lista de la pestaña **Lote**; sustituye `ID` por su número):

```bash
ID=13599   # pon aquí el cliente que viste en la pestaña Lote
curl -s http://127.0.0.1:8090/bajo-demanda/$ID
curl -s http://127.0.0.1:8090/online/$ID
```

**Qué debes ver (sin verificar en Codespace).** La misma `probabilidad` en los dos y el mismo `corte`: mientras no llegan datos nuevos, leer las variables de la tabla `fs_produccion` o calcularlas al vuelo da lo mismo.

Ahora llega una compra nueva y se vuelve a preguntar:

```bash
curl -s -X POST http://127.0.0.1:8090/demo/compra -H 'content-type: application/json' \
     -d "{\"cliente_id\": $ID, \"importe\": 120.5, \"unidades\": 3}"
curl -s http://127.0.0.1:8090/bajo-demanda/$ID
curl -s http://127.0.0.1:8090/online/$ID
```

**Qué debes ver (sin verificar en Codespace).** La `probabilidad` de **bajo demanda no cambia** (lee la tabla de ayer) y la de **online cambia** (suma la compra nueva a lo que ya sabía el sistema). En el panel, la pestaña **Online** tiene el botón «Simular una compra nueva» y la comparación de los tres modos. La compra se guarda en una **copia** de la base dentro del contenedor, nunca en la del proyecto.

Para dejar la demo como al principio sin parar nada:

```bash
curl -s -X POST http://127.0.0.1:8090/demo/reiniciar
```

**Si falla (sin verificar en Codespace).**
- `404` con «no está en fs_produccion»: ese cliente no tiene compras válidas antes del corte; elige otro de la lista del lote.
- `404` con «El modo demo está apagado»: la interfaz no arrancó con `CURSO_DEMO=1`; comprueba que usas `compose-produccion.yaml` y no `compose.yaml`.
- Error al escribir la compra: mira `docker compose -f deploy/docker/compose-produccion.yaml logs interfaz`.

## 5. Parar y limpiar

```bash
docker compose -f deploy/docker/compose-produccion.yaml down
```

**Qué debes ver (sin verificar en Codespace).** Se paran y borran los dos contenedores y la red. La copia de demo vive en memoria del contenedor, así que las compras simuladas desaparecen; tus datos (`data/processed`, `models`, `reports`) no se tocan.
