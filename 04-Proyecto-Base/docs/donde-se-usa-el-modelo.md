# Dónde se llama al modelo: la API, la interfaz y los tres modos

Este documento responde a cuatro preguntas que salen en cuanto el modelo está «en producción»: *¿qué servicio hace qué?*, *¿qué código llama de verdad al modelo?*, *¿qué significa cada código de respuesta?* y *¿de dónde salen las 13 variables en cada modo?* Cada afirmación cita el archivo y la función o la línea donde se comprueba (las líneas son las del código a fecha de este documento: si el código cambia, busca la función).

No repite cómo se construyen las imágenes ni cómo se levantan los contenedores: eso está en [`del-ordenador-al-servicio.md`](del-ordenador-al-servicio.md) (y, para la API sola, en [`api-y-contenedor.md`](api-y-contenedor.md); para la página de consulta, en [`interfaz-de-consulta.md`](interfaz-de-consulta.md)).

Todas las órdenes se lanzan desde `04-Proyecto-Base`, con el entorno `env-ia-mlops` activo.

---

## 1. Dos servicios, dos puertos

| Servicio | Puerto | Se arranca con | Qué rutas tiene |
|---|---|---|---|
| **API del modelo** | **8080** | `python -m uvicorn ia_mlops.api.app:app --port 8080` | **solo cinco:** `GET /salud`, `GET /listo`, `GET /modelo`, `POST /predecir`, `POST /predecir/lote` (`ia_mlops/api/app.py`, líneas 78-104) |
| **Interfaz** | **8090** | `python -m ia_mlops.interfaz --url http://127.0.0.1:8080` | `/`, `/panel`, `/recomendar`, `/bajo-demanda`, `/online`, `/modos`, `/demo/*`, `/asistente`… (`ia_mlops/interfaz/app.py`, líneas 102-168) |

**Consecuencia práctica.** `/bajo-demanda`, `/online`, `/modos` y `/panel` **no existen en la API**: viven en la interfaz. Si pides `http://127.0.0.1:8080/online/13599` la API responde, con toda la razón:

```json
{"detail":"Not Found"}
```

No es un fallo del modelo ni de la red: has llamado al servicio equivocado. La misma petición al **8090** sí es una ruta de la interfaz. (Comprobado: la API arrancada en local responde `404` con ese cuerpo.)

Por qué están separados: la API **solo conoce el modelo** y pide las 13 variables ya calculadas; la interfaz **conoce el dato** (calcula o lee las variables desde el id del cliente) y llama a la API (`ia_mlops/interfaz/app.py`, docstring, líneas 3-4). Así la imagen del modelo no lleva datos de clientes.

---

## 2. Dónde se carga y dónde se usa el modelo

```text
 arranque de la API                          cada petición
 ──────────────────                          ─────────────
 FastAPI (ciclo de vida)                     POST /predecir          POST /predecir/lote
   └─ Servicio.cargar()                          │                        │
        └─ mlflow.sklearn.load_model()           └──────────┬─────────────┘
              (UNA vez)                                     ▼
                                                Servicio.predecir()  ──►  modelo.predict_proba()
```

| Qué | Dónde | Detalle |
|---|---|---|
| **Cargar el modelo (una vez)** | `ia_mlops/api/servicio.py`, `Servicio.cargar` (líneas 30-45); la llamada final es `mlflow.sklearn.load_model(...)` (línea 45) | Comprueba antes que la **firma** del modelo coincide con `models/metadatos.json` |
| **Cuándo se carga** | `ia_mlops/api/app.py`, función `ciclo` (líneas 36-48): `Servicio.cargar(carpeta_modelo)` en la línea 40, dentro del *lifespan* de FastAPI | Es decir, **al arrancar el proceso**, no en cada petición |
| **Usar el modelo** | `ia_mlops/api/servicio.py`, `Servicio.predecir` (líneas 70-76): `self.modelo.predict_proba(df)[:, 1]` en la línea 75 | Convierte la lista de diccionarios en un `DataFrame` con las columnas en el orden de la firma |
| **Quién lo invoca** | `app.py`: `predecir` (líneas 95-99) y `predecir_lote` (líneas 101-104) llaman a `s.predecir(...)` | `app.py` **no** conoce el modelo |

**Reparto de responsabilidades.** `app.py` solo gestiona HTTP: rutas, validación del cuerpo, códigos de respuesta, `X-Request-ID` y registro. **La capa `Servicio` es la única que conoce el modelo** (`servicio.py`, docstring: «No sabe nada de HTTP»). Por eso las pruebas pueden probar el modelo sin levantar un servidor, y por eso la interfaz y el lote (`ia_mlops/explotacion.py`, `puntuar_local`, línea 101) pueden usar **el mismo código** sin pasar por HTTP cuando no hay API.

**Y la interfaz, ¿cómo puntúa?** `ia_mlops/interfaz/consulta.py`, `Consulta._puntuar` (líneas 95-99): si hay URL de la API, llama a `POST /predecir/lote` (`explotacion.puntuar_api`, línea 88); si no, usa `Servicio.cargar` en el propio proceso (`_servicio_local`, línea 83). En los dos casos el modelo es el mismo y la probabilidad, la misma.

---

## 3. Códigos de respuesta de la API

| Código | Cuándo ocurre | Quién lo pone | Cuerpo |
|---|---|---|---|
| **200** | La petición es válida y el modelo está cargado | tu código | La probabilidad (`/predecir`) o la lista (`/predecir/lote`) |
| **422** | El cuerpo **no cumple el contrato**: **falta** una variable, **sobra** un campo, un valor está fuera de límites o es incoherente | FastAPI + pydantic (`ia_mlops/api/esquemas.py`) | `{"detail":[{"type":…,"loc":[…],"msg":…}]}` |
| **503** | El proceso **vive** pero el **modelo no está cargado** (`/salud` responde 200, `/listo` falla) | `app.py`, manejador `sin_modelo` (líneas 74-76) | `{"detalle":"No hay modelo en …","id_peticion":"…"}` |
| **500** | Una excepción **no prevista**: el detalle va al registro, **no** al cliente | `app.py`, `middleware_registro` (líneas 58-62) | `{"detalle":"Error interno","id_peticion":"…"}` |
| **404 / 405** | Ruta que no existe / método que no corresponde (por ejemplo `GET /predecir`) | **FastAPI**, no el código del proyecto | `{"detail":"Not Found"}` / `{"detail":"Method Not Allowed"}` |
| **400** | **Esta API no devuelve 400.** Un cuerpo mal formado o que incumple el contrato da **422** | — | — |

Detalles que conviene saber, todos de `esquemas.py`:

- **Sobra un campo → 422, a propósito.** `Cliente` tiene `extra='forbid'` (líneas 6-7 y 24). Si envías la etiqueta `y` (lo que se quiere predecir), la API **no la ignora en silencio: la rechaza**. Es una defensa contra la **fuga de datos**: una variable que se conocería *después* del corte no puede colarse sin que nadie lo vea.
- **Falta una variable → 422.** Las 13 variables son obligatorias, **salvo `dias_medios_entre_compras`**, que es **la única opcional** (`default=None`, líneas 36-37): vale `null` si el cliente tiene una sola factura, y el modelo usa entonces la mediana del entrenamiento (`servicio.py`, líneas 62-63).
- **Incoherencias → 422.** Por ejemplo, más facturas en 90 días que en total, o `ticket_medio` distinto de `monto_total / frecuencia` (`_coherencia`, líneas 41-53).
- **Fuera del rango de entrenamiento → 200 con `advertencias`**, no error: el valor es posible, pero el modelo no lo vio al entrenar (`servicio.py`, `advertencias`, líneas 59-68).
- **Dos formas de cuerpo de error.** Los de FastAPI (422, 404, 405) usan la clave inglesa **`detail`**; los del proyecto (503, 500) usan **`detalle`** (`esquemas.Error`, líneas 83-85).

### Provocar cada código con `curl`

Las órdenes usan `-i` para ver la línea de estado (`HTTP/1.1 …`). El cuerpo del cliente de ejemplo es el de `esquemas.EJEMPLO` (línea 15). **bash** (Codespace, Git Bash) frente a **Windows `cmd`** (sin `; echo`, comillas dobles y las interiores escapadas con `\"`):

**200 · petición válida**

```bash
curl -s -i -X POST http://127.0.0.1:8080/predecir -H 'content-type: application/json' -d '{"recencia_dias": 35, "frecuencia": 6, "monto_total": 1250.40, "ticket_medio": 208.4, "unidades_total": 410, "productos_distintos": 38, "antiguedad_dias": 310, "frecuencia_90d": 2, "monto_90d": 380.5, "frecuencia_180d": 4, "dias_medios_entre_compras": 55.0, "devoluciones": 1, "es_reino_unido": 1}'; echo
```

```bat
curl -s -i -X POST http://127.0.0.1:8080/predecir -H "content-type: application/json" -d "{\"recencia_dias\": 35, \"frecuencia\": 6, \"monto_total\": 1250.40, \"ticket_medio\": 208.4, \"unidades_total\": 410, \"productos_distintos\": 38, \"antiguedad_dias\": 310, \"frecuencia_90d\": 2, \"monto_90d\": 380.5, \"frecuencia_180d\": 4, \"dias_medios_entre_compras\": 55.0, \"devoluciones\": 1, \"es_reino_unido\": 1}"
```

Responde `200 OK` y algo como `{"probabilidad":0.8278889191932138,"modelo":"regresion_logistica","huella_datos":"35a94deb4e04ab4a","advertencias":[]}` (salida real con el modelo de la muestra).

**422 · sobra un campo (la etiqueta `y`)**: el mismo cuerpo más `"y": 1`.

```bash
curl -s -i -X POST http://127.0.0.1:8080/predecir -H 'content-type: application/json' -d '{"recencia_dias": 35, "frecuencia": 6, "monto_total": 1250.40, "ticket_medio": 208.4, "unidades_total": 410, "productos_distintos": 38, "antiguedad_dias": 310, "frecuencia_90d": 2, "monto_90d": 380.5, "frecuencia_180d": 4, "dias_medios_entre_compras": 55.0, "devoluciones": 1, "es_reino_unido": 1, "y": 1}'; echo
```

```bat
curl -s -i -X POST http://127.0.0.1:8080/predecir -H "content-type: application/json" -d "{\"recencia_dias\": 35, \"frecuencia\": 6, \"monto_total\": 1250.40, \"ticket_medio\": 208.4, \"unidades_total\": 410, \"productos_distintos\": 38, \"antiguedad_dias\": 310, \"frecuencia_90d\": 2, \"monto_90d\": 380.5, \"frecuencia_180d\": 4, \"dias_medios_entre_compras\": 55.0, \"devoluciones\": 1, \"es_reino_unido\": 1, \"y\": 1}"
```

Responde `422 Unprocessable Entity` con `{"detail":[{"type":"extra_forbidden","loc":["body","y"],"msg":"Extra inputs are not permitted","input":1}]}` (salida real).

**422 · faltan variables**

```bash
curl -s -i -X POST http://127.0.0.1:8080/predecir -H 'content-type: application/json' -d '{"recencia_dias": 35}'; echo
```

```bat
curl -s -i -X POST http://127.0.0.1:8080/predecir -H "content-type: application/json" -d "{\"recencia_dias\": 35}"
```

Responde `422` con un error `missing` (`"Field required"`) por cada una de las once variables obligatorias que faltan; `dias_medios_entre_compras` no aparece porque es opcional.

**404 y 405 · los pone FastAPI**

```bash
curl -s -i http://127.0.0.1:8080/online/13599; echo
curl -s -i http://127.0.0.1:8080/predecir; echo
```

```bat
curl -s -i http://127.0.0.1:8080/online/13599
curl -s -i http://127.0.0.1:8080/predecir
```

La primera da `404` con `{"detail":"Not Found"}` (la ruta es de la interfaz, no de la API); la segunda da `405 Method Not Allowed`, con la cabecera `allow: POST`.

**503 · modelo no cargado.** Arranca **otra** API apuntando a una carpeta de modelos vacía (variable de entorno `CURSO_MODELOS`, `ia_mlops/config.py` línea 29) y pregúntale si está lista:

```bash
mkdir -p /tmp/vacio
CURSO_MODELOS=/tmp/vacio python -m uvicorn ia_mlops.api.app:app --port 8088
# en otra terminal:
curl -s -i http://127.0.0.1:8088/listo; echo
curl -s -i http://127.0.0.1:8088/salud; echo
```

```bat
mkdir %TEMP%\vacio
set CURSO_MODELOS=%TEMP%\vacio
python -m uvicorn ia_mlops.api.app:app --port 8088
REM en otra ventana de cmd:
curl -s -i http://127.0.0.1:8088/listo
curl -s -i http://127.0.0.1:8088/salud
```

`/listo` responde `503` con `{"detalle":"No hay modelo en … Entrenalo antes: python -m ia_mlops.pipeline","id_peticion":"…"}`; `/salud` responde `200`: **vivo no es lo mismo que listo**. En la terminal de esa API verás además el registro `modelo no cargado`.

**500 · error interno.** No hay una petición normal que lo provoque: solo sale ante un fallo no previsto del código. Lo importante es lo que **no** hace: no enseña el traceback al cliente; lo guarda en el registro junto con el `id_peticion`.

---

## 4. Los registros: qué se guarda y qué no

Cada petición deja **una línea JSON** por la salida estándar (`app.py`, `middleware_registro`, líneas 53-66; formato en `ia_mlops/api/registro.py`). Ejemplo real, de la petición `GET /online/13599` del apartado 1:

```json
{"severity": "INFO", "message": "GET /online/13599 404", "evento": "peticion", "id": "3a0936192f9c", "metodo": "GET", "ruta": "/online/13599", "codigo": 404, "ms": 1.4}
```

- **Qué lleva:** método, ruta, código de respuesta, milisegundos e `id`. **Nunca** los datos del cliente (`registro.py`, docstring, línea 9): el cuerpo de un `POST /predecir` no se escribe.
- **El `id` es el `X-Request-ID`.** Si la petición trae la cabecera `x-request-id`, se reutiliza; si no, se genera uno (línea 55). La **respuesta** lo devuelve en su cabecera `X-Request-ID` (línea 63): es el hilo que une lo que vio quien llamó con lo que quedó en el registro. En los errores 503 y 500 también va en el cuerpo (`id_peticion`).
- **Además** uvicorn imprime su propia línea (`INFO:     127.0.0.1:55958 - "GET /online/13599 HTTP/1.1" 404 Not Found`): es otro registro, no el de la aplicación. Las dos aparecen en la misma terminal (la JSON, por la salida estándar; la de uvicorn, por la de errores).

---

## 5. Los tres modos: de dónde salen las 13 variables

El modelo siempre recibe **las mismas 13 variables** (`config.FEATURES`). Lo que cambia entre modos es **de dónde salen y cuándo se calculan** (`ia_mlops/interfaz/modos.py`, docstring, líneas 1-6):

| Modo | Las 13 variables… | Corte | Dónde se usa |
|---|---|---|---|
| **Lote** | **calculadas para todos** los clientes y guardadas | el del día (`explotacion.corte_por_defecto`) | `python -m ia_mlops.explotacion` |
| **Bajo demanda** | **LEÍDAS** de la tabla `fs_produccion` (ya calculadas por el lote; sin cálculo) | el último corte escrito en `fs_produccion` | `GET /bajo-demanda/{id}` en la **interfaz** (`modos.py`, `bajo_demanda`, líneas 112-143) |
| **Online** | **CALCULADAS AL VUELO** para **un** cliente | «ahora» | `GET /online/{id}` en la **interfaz** (`modos.py`, `online`, líneas 202-225) |

### Cómo calcula el modo online

`Modos._variables_al_vuelo` (`modos.py`, líneas 177-200) hace esto, y nada más:

1. Crea **vistas temporales** `master_facturas` y `master_lineas` que son MASTER **filtrado a ese único cliente** (y, en modo demo, unido a `demo_compras`).
2. **Ejecuta `sql/fs/02_poblar_fs.sql`** (línea 195) con el corte pedido, sin cambiarle una coma, sobre una tabla temporal `fs_cliente_corte`. Por eso es rápido: solo calcula un cliente.
3. Lee el resultado, lo puntúa con el modelo y devuelve la probabilidad.

Lo que **no** hace: **no ejecuta el pipeline entero** (ni ingesta, ni MASTER, ni reentrenamiento); la capa FS del proyecto queda intacta.

- **Sin fuga.** El SQL solo mira facturas con `fecha_factura < :corte` (`02_poblar_fs.sql`, línea 3). Una compra posterior al corte pedido no entra.
- **Tan fresco como MASTER.** «Ahora» es el **día siguiente al último evento conocido** de MASTER (`ahora`, líneas 157-166); el dato del curso termina en 2011, así que no se usa el reloj del ordenador. En producción real, el modo online solo es tan reciente como la última carga de MASTER.
- **Paridad.** Como el modo online usa **el mismo SQL que el entrenamiento**, con el mismo corte da **las mismas variables** que `fs_cliente_corte` (las pruebas de la interfaz lo comprueban; la guía del apartado 7 te deja comprobarlo a ti).

### Para ver los tres modos

```text
python -m ia_mlops.pipeline        # si aún no hay modelo ni datos
python -m ia_mlops.explotacion     # el lote: escribe fs_produccion (sin ella, bajo demanda no tiene qué leer)
python -m uvicorn ia_mlops.api.app:app --port 8080            # terminal 1: la API
python -m ia_mlops.interfaz --url http://127.0.0.1:8080       # terminal 2: la interfaz en el 8090
```

Y en el navegador (o con `curl`) la **interfaz**, no la API: `http://127.0.0.1:8090/bajo-demanda/13599` y `http://127.0.0.1:8090/online/13599`. Con la muestra y sin datos nuevos, los dos dan la misma probabilidad para el mismo cliente y corte.

---

## 6. Ver el modelo en la interfaz de MLflow

El modelo se entrena y se registra con MLflow (base `models/mlflow.db`). Para mirarlo en el navegador:

```bash
python -m ia_mlops.mlflow_ui              # http://127.0.0.1:5000
python -m ia_mlops.mlflow_ui --port 5001  # si el 5000 está ocupado
python -m ia_mlops.mlflow_ui --comprobar  # solo dice qué hay en el registro, sin abrir nada
```

- **Desde `04-Proyecto-Base`**, con el entorno `env-ia-mlops`.
- **En la web, arriba a la izquierda, elige «Model training»**, no «GenAI»: con «GenAI» la interfaz parece **vacía** aunque el registro esté lleno. Las ejecuciones están en *Experiments › retencion-90d › Training runs*, y los modelos en *Registered Models* (`mlflow_ui.py`, docstring, líneas 14-16).
- `--comprobar` (línea 75) imprime, por ejemplo, `Experimento «retencion-90d»: 64 ejecuciones · modelo registrado «retencion-90d»: 6 versiones` (salida real en el ordenador del profesor; las cifras dependen de cuántas veces hayas entrenado).
- Para parar: `Ctrl+C` en la misma terminal.

**Por qué NO lanzar `mlflow ui` a pelo desde otra carpeta.** La orden `mlflow ui --backend-store-uri sqlite:///models/mlflow.db` usa una ruta **relativa**. Si la lanzas desde otra carpeta (por ejemplo la raíz del repositorio, donde se abre la terminal de VS Code), MLflow **crea allí una base nueva y vacía sin avisar**: la interfaz arranca, pero no hay ni ejecuciones ni modelos, y no da ningún error (`mlflow_ui.py`, docstring, líneas 3-5). `python -m ia_mlops.mlflow_ui` calcula la ruta **absoluta** del registro del proyecto (función `uri`, línea 28) y, si el registro no existe o está vacío, se para y te dice que entrenes primero (líneas 66-74).

---

## 7. Comprobación guiada: el modo online da lo mismo que el entrenamiento

Vas a calcular **al vuelo** las variables de un cliente en el corte con el que se entrenó (`2010-12-01`), compararlas con las que **se guardaron** en `fs_cliente_corte` y comprobar que son iguales. Cliente de ejemplo: `13599`.

Guarda este script como `comparar_fs.py` **dentro de `04-Proyecto-Base`** (así Python encuentra el paquete `ia_mlops`) y ejecútalo desde esa carpeta con `python comparar_fs.py`:

```python
import pandas as pd
from ia_mlops import config, db, explotacion as ex

cid, corte = 13599, '2010-12-01'
con = db.conectar()
vuelo = ex.variables_en_corte(con, corte).query('cliente_id == @cid').reset_index(drop=True)
guardada = pd.read_sql("SELECT * FROM fs_cliente_corte WHERE cliente_id = ? AND fecha_corte = '2010-12-01'", con, params=[cid])
print(pd.concat([vuelo[config.FEATURES].T, guardada[config.FEATURES].T], axis=1, keys=['al vuelo', 'fs_cliente_corte']).to_string())
print('Iguales en el corte entrenado:', vuelo[config.FEATURES].equals(guardada[config.FEATURES]))
hoy = ex.variables_en_corte(con, ex.corte_por_defecto(con)).query('cliente_id == @cid')
print(hoy[['recencia_dias', 'frecuencia', 'monto_total', 'antiguedad_dias']].to_string(index=False))
```

Qué hace cada bloque: `ex.variables_en_corte` es la **misma función** que usa el modo online (ejecuta `02_poblar_fs.sql` sobre una tabla temporal; `explotacion.py`, líneas 47-62); `pd.read_sql` lee la fila ya guardada; la comparación usa las 13 columnas de `config.FEATURES`; y las dos últimas líneas calculan el **mismo cliente en el corte de hoy** para ver cuánto cambia.

**Qué debes ver** (salida real de este script con la muestra del curso, cliente 13599):

```text
                          al vuelo fs_cliente_corte
                                 0                0
recencia_dias                21.00            21.00
frecuencia                   12.00            12.00
monto_total                4661.12          4661.12
ticket_medio                388.43           388.43
unidades_total             2955.00          2955.00
productos_distintos         100.00           100.00
antiguedad_dias             364.00           364.00
frecuencia_90d                6.00             6.00
monto_90d                  1752.00          1752.00
frecuencia_180d                6.00             6.00
dias_medios_entre_compras    31.20            31.20
devoluciones                  7.00             7.00
es_reino_unido                1.00             1.00
Iguales en el corte entrenado: True
 recencia_dias  frecuencia  monto_total  antiguedad_dias
             1          33      9811.04              738
```

(El formato exacto de la tabla depende de la versión de pandas; lo que importa es que las dos columnas coincidan y que la línea diga `True`.)

**Cómo leerlo.**

- `Iguales en el corte entrenado: True`: el cálculo al vuelo y el del entrenamiento dan **exactamente las mismas 13 variables**. Eso es la **paridad** entre entrenamiento y producción: el modelo ve en producción lo mismo que vio al aprender.
- Las dos columnas de la tabla coinciden porque se calculan con el mismo SQL sobre los mismos datos con el mismo corte.
- La última línea es el **mismo cliente** en el corte de hoy (`2011-12-10`), **374 días** después del corte entrenado (`2010-12-01`). Las variables **sí** cambian, y deben cambiar:

| Variable | Corte 2010-12-01 | Corte 2011-12-10 |
|---|---|---|
| `recencia_dias` | 21 | 1 |
| `frecuencia` | 12 | 33 |
| `monto_total` | 4661,12 | 9811,04 |
| `antiguedad_dias` | 364 | 738 |

`antiguedad_dias` pasa de 364 a 738: sube exactamente los **374 días** entre los dos cortes. Es también el motivo por el que, en el corte de hoy, el modelo avisa «fuera del rango visto al entrenar» (el máximo visto al entrenar fue 364; ver [`interfaz-de-consulta.md`](interfaz-de-consulta.md)).

**Si falla.**

- `ModuleNotFoundError: No module named 'ia_mlops'`: no has guardado el script en `04-Proyecto-Base` o lo ejecutas desde otra carpeta.
- `No existe la capa FS: ejecuta antes python -m ia_mlops.pipeline` (error de `variables_en_corte`): faltan los datos; ejecuta `python -m ia_mlops.pipeline`.
- La consulta de `guardada` devuelve una tabla vacía: ese cliente no tiene compras antes de ese corte; prueba con otro id o con otro corte que exista en `fs_cliente_corte`.

---

## 8. Resumen en una tabla

| Quiero… | Lo hago en… | Con… |
|---|---|---|
| La probabilidad si **ya tengo** las 13 variables | la **API** (8080) | `POST /predecir`, `POST /predecir/lote` |
| La probabilidad de un cliente **a partir de su id**, con variables de ayer | la **interfaz** (8090) | `GET /bajo-demanda/{id}` |
| La probabilidad de un cliente **con datos frescos** | la **interfaz** (8090) | `GET /online/{id}` |
| Puntuar **a todos** y ordenar | el **lote** | `python -m ia_mlops.explotacion` |
| Ver los tres modos y las versiones | la **interfaz** | `/panel` |
| Saber si la API está viva / lista | la **API** | `/salud` (viva) · `/listo` (con modelo) |
| Ver el modelo y sus ejecuciones | **MLflow** | `python -m ia_mlops.mlflow_ui` y «Model training» |

## Qué se probó y qué no

- **Probado el 26/11/2026** con la API arrancada en local (Windows, `curl.exe` desde `cmd`): el 200, los dos 422, el 404, el 405 y el 503 de la sección 3, los registros de la sección 4, `python -m ia_mlops.mlflow_ui --comprobar` y el script de la sección 7 (la salida pegada es la suya).
- **Sin probar en esta redacción:** las órdenes de **bash** (el `-d '…'` con comillas simples y el `; echo`) y el arranque de la interfaz y de `mlflow ui` en el navegador; se leyeron en el código, no se ejecutaron. El **500** no se provocó con `curl`: sale del código del middleware.
- Las **líneas citadas** son las del código a esta fecha.
