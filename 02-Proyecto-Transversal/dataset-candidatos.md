# Candidatos de dataset para el Proyecto Transversal

Curso: "ML e IA: de desarrollo a producción" (UNTRM). Informe de investigación de datos, 2026-11-08.

## 0. Advertencia de honestidad (leer primero)

En el contenedor de investigación, el proxy bloqueó (HTTP 403 en CONNECT) todos los hosts de datos probados: `archive.ics.uci.edu`, `www.openml.org`, `www.kaggle.com`, `huggingface.co`, `zenodo.org`, `insideairbnb.com`, `d37ci6vzurychx.cloudfront.net` (NYC TLC), `data.cityofnewyork.us`, `data.cityofchicago.org`, `www.datosabiertos.gob.pe`, `catalog.data.gov`. WebFetch también falló para esos hosts. Solo respondieron `pypi.org` y `raw.githubusercontent.com`.

Consecuencias:

- **Ningún dataset pudo descargarse.** Todas las filas de la tabla comparativa figuran como "Verificado = NO". No hay tamaños reales, nulos ni tipos medidos, y no se entrenó ningún baseline. No se reporta ninguna métrica.
- **Las licencias salen de resúmenes de WebSearch** (que citan las páginas oficiales de UCI y otras), no de leer la página oficial. Cada afirmación lleva la URL citada por el buscador; hay que reconfirmarla abriendo la URL antes de publicar el repo.
- Las cifras con la etiqueta "(dato de búsqueda)" vienen de un resultado de búsqueda. Las etiquetadas "(memoria, no verificado)" son conocimiento previo del investigador y deben comprobarse con el archivo real.
- Lo único ejecutado: el DDL SQLite de la sección 3.4 se probó en `sqlite3` (se crean las 6 tablas sin error). Los scripts Python son borradores no probados.

Para completar la verificación basta permitir (allowlist) estos hosts en el entorno y re-ejecutar el script de la sección 5: `archive.ics.uci.edu`, `www.kaggle.com`, `insideairbnb.com`, `data.insideairbnb.com`.

## 1. Resumen ejecutivo y recomendación

| Rol | Primera opción | Alternativa |
|---|---|---|
| Caso del instructor (demo) | **Online Retail II** (UCI, CC BY 4.0): predecir si un cliente vuelve a comprar en los próximos 90 días | **Inside Airbnb** (listings + calendar + reviews, por ciudad y trimestre): regresión de precio |
| Tarea del alumno | **Olist Brazilian E-Commerce** (Kaggle, multi-tabla, Brasil): predecir entrega tardía de un pedido | **Default of Credit Card Clients** (UCI, CC BY 4.0): morosidad del siguiente mes |

Por qué Online Retail II para el instructor:

- Licencia CC BY 4.0, con DOI estable (10.24432/C5CG6D) y 1.067.371 filas (dato de búsqueda). Esto permite incluir una muestra pequeña en el repo y descargar el resto por script.
- Es transaccional (cliente, factura, producto, fecha). La entidad cliente y el tiempo dan FS con ventanas temporales y una partición sin fuga.
- Su ruido real justifica MASTER: Customer ID nulo, facturas canceladas (prefijo "C"), cantidades negativas, precios cero, códigos que no son producto (POSTAGE, etc.), duplicados (memoria, no verificado).
- Aunque el archivo es una sola tabla, MASTER la normaliza en cuatro tablas relacionales (clientes, productos, facturas, líneas), con joins reales en las capas posteriores.
- La reproducción en CPU es trivial (~1 M líneas, features agregadas por cliente/corte).
- La deriva se puede mostrar con datos reales: el archivo cubre dic-2009 a dic-2011 (dato de búsqueda: 2009-2011). Se entrena con el periodo antiguo y se evalúa en el nuevo.

Por qué Olist para la tarea:

- Mismo patrón (pedidos, clientes, ítems, pagos, vendedores), con contexto latinoamericano. El alumno cambia entidad (pedido en vez de cliente), objetivo y features, pero mantiene la receta de capas.
- Restricción de licencia: CC BY-NC-SA 4.0 según una fuente secundaria (no confirmado en Kaggle). Es NC (no comercial) y SA (compartir igual), así que **no debe incluirse en el repo**: se descarga por script con cuenta gratuita de Kaggle. El uso en un curso gratuito/educativo suele ser compatible con NC, pero hay que confirmarlo con el instructor/UNTRM si el curso es de pago.
- Si la restricción NC se considera inaceptable, la alternativa limpia es Default of Credit Card Clients (CC BY 4.0). Es más simple: una sola tabla ancha de 30.000 filas, con historial de 6 meses por cliente.

## 2. Tabla comparativa de candidatos

Verificado = ¿se descargó el archivo y se midió? En todos los casos: **NO** (red bloqueada, ver sección 0).

### 2.1 Caso del instructor

| # | Candidato | Licencia (URL de verificación) | Tamaño / filas | Tablas | Cuenta/API | Verificado | Veredicto |
|---|---|---|---|---|---|---|---|
| I1 | **Online Retail II** (UCI) | CC BY 4.0. https://archive.ics.uci.edu/dataset/502/online+retail+ii (OpenML espejo 43368 figura como CC0, discrepa: https://api.openml.org/d/43368) | 1.067.371 filas (dato de búsqueda); ~45 MB xlsx (memoria, no verificado) | 1 archivo (2 hojas, memoria) | No (descarga directa UCI) | NO | **Recomendado** |
| I2 | **Inside Airbnb** (listings/calendar/reviews) | CC BY 4.0 según resúmenes de búsqueda; una copia OpenML y un cuaderno de 2019 dicen CC0, así que hay conflicto. https://insideairbnb.com/data-policies/ y https://insideairbnb.com/get-the-data/ (no se pudo abrir) | Varía por ciudad: de decenas de miles de listings a millones de filas en calendar (memoria, no verificado) | 3 tablas relacionadas + vecindarios | No | NO | **Alternativa**. Riesgos: ciudades latinoamericanas disponibles no confirmadas, solo se conservan los últimos trimestres (estabilidad), datos personales de anfitriones y reseñas |
| I3 | NYC TLC Yellow Taxi (parquet) | Términos de uso de nyc.gov (no es CC estándar). https://registry.opendata.aws/nyc-tlc-trip-records-pds apunta a http://www1.nyc.gov/home/terms-of-use.page | ~3 M filas/mes, ~50 MB parquet/mes (memoria, no verificado) | 1 + tabla de zonas | No | NO | Descartado como principal: licencia no estándar y no verificada, dominio ajeno (NY). Buen respaldo técnico |
| I4 | Chicago Taxi Trips | data.gov lo lista como licencia no especificada y "Terms of Use distintos". https://catalog.data.gov/dataset/taxi-trips-2013-2023 | Muy grande (BigQuery) | 1 | Cuenta GCP para BigQuery | NO | **Descartado**: licencia no especificada |
| I5 | Capital Bikeshare | "Capital Bikeshare Data License Agreement" (no es CC). https://capitalbikeshare.com/system-data | Mensual, millones/año (memoria) | 1 | No | NO | **Descartado**: licencia propietaria; no permite asumir redistribución |

### 2.2 Tarea del alumno

| # | Candidato | Licencia (URL) | Tamaño / filas | Tablas | Cuenta/API | Verificado | Veredicto |
|---|---|---|---|---|---|---|---|
| T1 | **Olist Brazilian E-Commerce** | CC BY-NC-SA 4.0 según una fuente secundaria; **no confirmado en Kaggle**. https://scripts-and-tables.github.io/daa/data/ (secundaria); original https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce (no accesible) | 99.441 pedidos, 112.650 ítems, 103.886 pagos (datos de búsqueda); ~45 MB total (memoria, no verificado) | ~9 CSV relacionados | Kaggle (cuenta gratuita + API key) | NO | **Recomendado con condiciones** (NC-SA: no incluir en repo) |
| T2 | **Default of Credit Card Clients** (UCI) | CC BY 4.0 (OpenML espejo CC0). https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients | 30.000 filas; 23-24 columnas (dato de búsqueda); ~3 MB (memoria) | 1 | No | NO | **Alternativa** (licencia limpia, pero pequeño, 1 tabla, Taiwán 2005, sin dimensión temporal clara para partición) |
| T3 | **Bank Marketing** (UCI) | CC BY 4.0. https://archive.ics.uci.edu/dataset/222/bank+marketing | 45.211 filas (bank-full) (dato de búsqueda) | 1 | No | NO | Aceptable como respaldo de clasificación, pero por debajo del tamaño ideal (~4 MB, memoria); filas en orden cronológico (memoria), sin tablas |
| T4 | Seoul Bike Sharing Demand (UCI) | CC BY 4.0. https://archive.ics.uci.edu/dataset/560/seoul+bike+sharing+demand | 8.760 filas, 14 variables (dato de búsqueda) | 1 | No | NO | **Descartado**: demasiado pequeño y sin ruido real |
| T5 | UCI Bike Sharing (day/hour) | La licencia no se pudo confirmar en las búsquedas | hour.csv 1,1 MB | 2 | No | NO | **Descartado**: licencia no confirmada, tamaño pequeño |

Candidato mencionado y no evaluado: portales de datos abiertos de Perú (`datosabiertos.gob.pe`). La búsqueda no confirmó licencias por dataset ni encontró un dataset tabular grande y adecuado. Queda como pendiente (sección 7); algunos portales latinoamericanos (CDMX, Bogotá) publican con CC BY 4.0, pero no se encontró un dataset de ML con tamaño y variable objetivo adecuados.

## 3. Detalle de la recomendación del instructor: Online Retail II

Referencia a citar: Chen, D. (2012). Online Retail II [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5CG6D

### 3.1 Esquema de capas (para la Sesión 1)

```
RAW  ->  MASTER  ->  FS  ->  ML  ->  ARTEFACTOS  ->  SERVICIO  ->  PRODUCCIÓN
xlsx     master_*    fs_*    ml_*   joblib+json      FastAPI       Cloud Run
```

### 3.2 RAW

- Archivo: `online_retail_II.xlsx` dentro de `online+retail+ii.zip` (memoria: 8 columnas Invoice, StockCode, Description, Quantity, InvoiceDate, Price, Customer ID, Country; dos hojas "Year 2009-2010" y "Year 2010-2011"; comprobar con el archivo real).
- Descarga por script (borrador, sección 5). URL patrón `https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip` (memoria, no verificada) o paquete `ucimlrepo`. Alternativa: OpenML 43368 con `fetch_openml` (espejo, licencia discrepante).
- Estructura: `04-Proyecto-Base/data/raw/online_retail_ii/2026-xx-xx/` con el zip original, el xlsx extraído y `MANIFEST.sha256`.
- Integridad: calcular SHA-256 al descargar, guardar en `MANIFEST.sha256` (sí se versiona en git: el hash, no el dato). Ante cada ejecución, verificar el hash antes de continuar; marcar los archivos como solo lectura (`chmod a-w`). RAW nunca se edita; MASTER se regenera desde RAW.
- Repo: `data/raw` en `.gitignore`. Se puede incluir `muestra_2000_filas.csv` (CC BY lo permite con atribución) para pruebas pytest y CI sin red.

### 3.3 MASTER (tablas `master_*`)

| Tabla | Clave | Columnas principales (tipo) |
|---|---|---|
| `master_clientes` | `cliente_id` INTEGER | pais TEXT, primera_compra TEXT(ISO), ultima_compra TEXT |
| `master_productos` | `codigo_producto` TEXT | descripcion TEXT, es_producto INTEGER (0 = POSTAGE, M, BANK CHARGES, etc.) |
| `master_facturas` | `factura_id` TEXT | cliente_id INTEGER (nulo permitido), fecha_factura TEXT, es_cancelacion INTEGER, pais TEXT |
| `master_lineas` | `linea_id` INTEGER | factura_id, codigo_producto, cantidad INTEGER, precio_unitario REAL, monto_linea REAL |

Reglas de limpieza:

- Unir las dos hojas y eliminar duplicados exactos (registrar cuántos).
- `Invoice` que empieza con "C" -> `es_cancelacion=1`.
- `InvoiceDate` a ISO-8601 (UTC naive; documentar zona).
- `Customer ID` nulo: se conserva la factura con `cliente_id` NULL (no se usa en FS por cliente). Convertir a entero (viene como float).
- Normalizar `Description` (strip, mayúsculas, vacíos a NULL); `StockCode` a mayúsculas (tipos mixtos numérico/texto como "85123A").
- `Price <= 0`: ver política (precio 0 -> excluir de monto o marcar). Outliers de cantidad/precio: marcar, no borrar; winsorizar solo dentro de FS.
- Códigos no producto -> `es_producto=0`.

Checks de calidad (cada uno se vuelve un pytest):

- No hay duplicados de `linea_id`; `factura_id` único en `master_facturas`.
- Integridad referencial: toda línea tiene factura y producto.
- `fecha_factura` entre 2009-12-01 y 2011-12-31; sin fechas futuras.
- `precio_unitario >= 0`; `monto_linea == cantidad * precio_unitario` (tolerancia).
- Facturas con `es_cancelacion=1` tienen cantidades <= 0.
- El % de `cliente_id` nulo está bajo un umbral documentado (se mide con el dato real; no inventar el valor).
- Número de filas master + descartadas = filas RAW (conciliación).

### 3.4 DDL SQLite (probado en `sqlite3`: crea las 6 tablas sin error)

```sql
PRAGMA foreign_keys = ON;
CREATE TABLE master_clientes (
  cliente_id     INTEGER PRIMARY KEY,
  pais           TEXT NOT NULL,
  primera_compra TEXT NOT NULL,
  ultima_compra  TEXT NOT NULL
);
CREATE TABLE master_productos (
  codigo_producto TEXT PRIMARY KEY,
  descripcion     TEXT,
  es_producto     INTEGER NOT NULL CHECK (es_producto IN (0,1))
);
CREATE TABLE master_facturas (
  factura_id    TEXT PRIMARY KEY,
  cliente_id    INTEGER REFERENCES master_clientes(cliente_id),
  fecha_factura TEXT NOT NULL,
  es_cancelacion INTEGER NOT NULL CHECK (es_cancelacion IN (0,1)),
  pais          TEXT NOT NULL
);
CREATE TABLE master_lineas (
  linea_id        INTEGER PRIMARY KEY,
  factura_id      TEXT NOT NULL REFERENCES master_facturas(factura_id),
  codigo_producto TEXT NOT NULL REFERENCES master_productos(codigo_producto),
  cantidad        INTEGER NOT NULL,
  precio_unitario REAL NOT NULL CHECK (precio_unitario >= 0),
  monto_linea     REAL NOT NULL
);
CREATE INDEX ix_lineas_factura ON master_lineas(factura_id);
CREATE INDEX ix_facturas_cliente_fecha ON master_facturas(cliente_id, fecha_factura);

CREATE TABLE fs_cliente_corte (
  cliente_id       INTEGER NOT NULL,
  fecha_corte      TEXT NOT NULL,
  recencia_dias    INTEGER, frecuencia_90d INTEGER, frecuencia_365d INTEGER,
  monto_90d REAL, monto_total REAL, ticket_medio REAL,
  n_productos_distintos INTEGER, antiguedad_dias INTEGER,
  dias_entre_compras_media REAL, ratio_devoluciones REAL,
  tendencia_frecuencia REAL, es_reino_unido INTEGER,
  PRIMARY KEY (cliente_id, fecha_corte)
);

CREATE TABLE ml_recompra_90d (
  cliente_id INTEGER NOT NULL, fecha_corte TEXT NOT NULL,
  y_recompra_90d INTEGER NOT NULL CHECK (y_recompra_90d IN (0,1)),
  particion TEXT NOT NULL CHECK (particion IN ('train','valid','test')),
  version_datos TEXT NOT NULL,
  PRIMARY KEY (cliente_id, fecha_corte)
);
```

### 3.5 FS (tablas `fs_*`)

Granularidad: una fila por (`cliente_id`, `fecha_corte`). Regla anti-fuga: **toda variable usa solo facturas con `fecha_factura <= fecha_corte`** (y no canceladas, salvo `ratio_devoluciones`). Se construye con SQL (`sql/fs/`) parametrizado por fecha de corte.

| # | Variable | Cálculo |
|---|---|---|
| 1 | `recencia_dias` | fecha_corte - última factura |
| 2 | `frecuencia_90d` | nº facturas en los 90 días previos |
| 3 | `frecuencia_365d` | nº facturas en los 365 días previos |
| 4 | `monto_90d` | suma de monto_linea en 90 días |
| 5 | `monto_total` | suma histórica hasta el corte |
| 6 | `ticket_medio` | monto_total / nº facturas |
| 7 | `n_productos_distintos` | productos distintos comprados (es_producto=1) |
| 8 | `antiguedad_dias` | fecha_corte - primera compra |
| 9 | `dias_entre_compras_media` | promedio de intervalos entre facturas |
| 10 | `ratio_devoluciones` | líneas canceladas / líneas totales |
| 11 | `tendencia_frecuencia` | frecuencia_90d / (frecuencia de los 90 días anteriores + 1) |
| 12 | `es_reino_unido` | 1 si país = United Kingdom (codificación binaria) |

Por qué es "didáctica, no un feature store completo": son tablas SQLite regeneradas por script, sin registro de metadatos de variables, sin servicio online/offline, sin consistencia de punto en el tiempo garantizada por la plataforma (la garantiza la regla de corte y los tests), sin linaje automático. Enseña el concepto de variable reutilizable por entidad y fecha, no la herramienta (Feast, Vertex Feature Store).

### 3.6 ML (tablas `ml_*`)

- Población: pares (cliente, corte) con al menos una compra previa al corte y `cliente_id` no nulo.
- **Objetivo**: `y_recompra_90d = 1` si el cliente tiene al menos una factura no cancelada con fecha en (corte, corte + 90 días]; si no, 0.
- Cortes mensuales (fin de mes). Partición temporal con purga:
  - train: cortes 2010-03-31 a 2011-02-28 (etiquetas hasta 2011-05-29);
  - valid: corte 2011-05-31 (etiquetas hasta 2011-08-29; posterior a las etiquetas de train);
  - test: corte 2011-09-09 (etiquetas hasta 2011-12-08; el archivo termina hacia 2011-12-09, memoria, comprobar).
  - Un mismo cliente aparece en varias particiones con cortes distintos; es una validación temporal "out-of-time" y se documenta (alternativa más estricta: partición por cliente además del tiempo).
- Balance de clases: **no medido** (hay que calcularlo con el dato real; se espera una clase positiva mayoritaria o equilibrada en clientes activos, a confirmar).
- Métricas: principal ROC-AUC (o PR-AUC si hay desbalance); secundarias: F1/recall@umbral, Brier score, calibración, y métrica de negocio (lift@10%).

### 3.7 ARTEFACTOS

- `artifacts/modelos/modelo_recompra_<version>.joblib`: pipeline scikit-learn completo (ColumnTransformer + modelo).
- `artifacts/metricas/metricas_<version>.json`: métricas por partición, umbral, fecha.
- `artifacts/modelos/metadatos_<version>.json`: `version_datos` (hash SHA-256 del RAW y del snapshot de `ml_*`), commit de git, versiones de librerías, lista de features y su orden, rangos de entrenamiento (para monitoreo), semilla.
- Baseline propuesto: `HistGradientBoostingClassifier` (nativo con nulos, rápido en CPU) y un baseline trivial con `LogisticRegression` + `StandardScaler`. Línea base ingenua: "recompra = recencia < 90 días". **Resultado: no ejecutado; no se reporta métrica.**

### 3.8 SERVICIO Y MLOPS

Contrato de la API (Pydantic):

```
POST /predecir
{ "recencia_dias": int >=0, "frecuencia_90d": int >=0, "frecuencia_365d": int >=0,
  "monto_90d": float >=0, "monto_total": float >=0, "ticket_medio": float >=0,
  "n_productos_distintos": int >=0, "antiguedad_dias": int >=0,
  "dias_entre_compras_media": float|null, "ratio_devoluciones": float 0..1,
  "tendencia_frecuencia": float >=0, "es_reino_unido": 0|1 }
-> { "prob_recompra_90d": float, "clase": 0|1, "version_modelo": str }
GET /salud, GET /version
```

Monitoreo y deriva:

- Distribución de entradas frente al rango de entrenamiento (PSI o KS por variable) y de la probabilidad predicha; métricas con etiquetas retrasadas 90 días.
- Simulación: entrenar con cortes de 2010 y evaluar con cortes 2011 (ventana nueva); calcular PSI; disparar reentrenamiento si PSI > umbral o AUC cae X; comparar modelo v1 vs v2 y hacer rollback a la imagen anterior de Cloud Run.

Pipeline GitHub Actions (orden):

1. Lint + pytest (checks de MASTER sobre la muestra del repo, tests de FS sin fuga, tests de la API).
2. Reconstruir capas con la muestra (smoke).
3. Entrenar con la muestra o datos descargados (job manual/programado) y publicar artefactos.
4. Construir imagen Docker; subir a Artifact Registry.
5. Desplegar a Cloud Run (revisión nueva); prueba de humo; promover tráfico o rollback a la revisión previa.

### 3.9 Árbol de carpetas bajo `04-Proyecto-Base`

```
04-Proyecto-Base/
├── data/
│   ├── raw/online_retail_ii/        # zip, xlsx, MANIFEST.sha256 (gitignored salvo manifest y muestra)
│   ├── sqlite/proyecto.db           # master_*, fs_*, ml_*
│   └── exports/                     # parquet/csv derivados
├── sql/
│   ├── master/  001_master_*.sql
│   ├── fs/      010_fs_cliente_corte.sql
│   └── ml/      020_ml_recompra_90d.sql
├── src/
│   ├── datos/       descargar.py, verificar_checksum.py, raw_a_master.py
│   ├── features/    construir_fs.py
│   ├── modelado/    construir_ml.py, entrenar.py, evaluar.py
│   └── api/         main.py, esquemas.py
├── notebooks/
├── tests/           test_master.py, test_fs_sin_fuga.py, test_api.py
├── artifacts/{modelos,metricas}/
└── deploy/{docker,cloud-run,kubernetes}/
```

## 4. Detalle de la tarea: Olist (alternativa: Default of Credit Card Clients)

### 4.1 Tarea con Olist (estructura de capas igual al caso)

Datos (tablas según memoria, a confirmar con los CSV reales): `olist_orders_dataset`, `olist_order_items_dataset`, `olist_order_payments_dataset`, `olist_order_reviews_dataset`, `olist_customers_dataset`, `olist_products_dataset`, `olist_sellers_dataset`, `olist_geolocation_dataset`, `product_category_name_translation`. Pedidos 99.441, ítems 112.650, pagos 103.886 (datos de búsqueda).

- RAW: descarga con `kaggle datasets download -d olistbr/brazilian-ecommerce` (requiere `~/.kaggle/kaggle.json`; borrador no probado), checksum igual que el caso. No incluir en el repo.
- MASTER: `master_pedidos`, `master_items`, `master_pagos`, `master_clientes`, `master_vendedores`, `master_productos` (categoría traducida al inglés/español). Limpieza: fechas de texto a ISO, estados de pedido, categorías nulas, duplicados en geolocalización/reseñas, pedidos sin fecha de entrega.
- FS: granularidad pedido; variables conocidas **en el momento de la compra**: nº de ítems, valor total, flete, ratio flete/valor, peso/volumen del paquete, categoría, estado del cliente y del vendedor, misma región cliente-vendedor, plazo estimado (estimated - purchase), día de la semana, tasa histórica de entregas tardías del vendedor hasta el corte.
- ML: objetivo `entrega_tardia = 1` si fecha de entrega al cliente > fecha estimada, solo para pedidos entregados. Partición temporal por `order_purchase_timestamp` (rango aproximado 2016-2018, dato de búsqueda; fijar los cortes con los cuantiles reales). Prohibido usar fechas posteriores a la compra (aprobación, envío, entrega) como features: son fuga. Balance de clases: no medido.
- Qué cambia respecto al caso: dataset, entidad (pedido en vez de cliente), objetivo (retraso en vez de recompra), features (logística en vez de RFM), joins más numerosos.

### 4.2 Alternativa: Default of Credit Card Clients

30.000 clientes, 6 meses de montos de factura y pagos (PAY_0..PAY_6, BILL_AMT1..6, PAY_AMT1..6), objetivo "default payment next month" (memoria). Mismo patrón de capas (MASTER por cliente/mes en formato largo; FS con ratios pago/factura, utilización, tendencia). Sin dimensión temporal de corte real, la partición es por cliente (hash de `ID`). Datos de Taiwán 2005, menos cercanos al estudiante, pero licencia limpia.

### 4.3 Qué entregan los alumnos en la Sesión 1 ("adaptar una transformación o variable")

1. Ejecutar los scripts base del caso del instructor (descarga, checksum, MASTER, FS) sin errores.
2. Adaptar una transformación o variable al dataset de la tarea: por ejemplo, una regla de limpieza nueva en MASTER (y su check/pytest) o una variable nueva en FS con su fecha de corte.
3. Evidencia para S2: dato (tabla en SQLite), modelo, métricas y una explicación breve de la variable y por qué no hay fuga.

## 5. Scripts de ejemplo (borrador no probado)

```python
# BORRADOR NO PROBADO: descarga + checksum del RAW (Online Retail II)
import hashlib, pathlib, urllib.request, zipfile

URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"  # patron de memoria
DEST = pathlib.Path("data/raw/online_retail_ii"); DEST.mkdir(parents=True, exist_ok=True)

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

zpath = DEST / "online_retail_ii.zip"
if not zpath.exists():
    urllib.request.urlretrieve(URL, zpath)
with zipfile.ZipFile(zpath) as z:
    z.extractall(DEST)
(DEST / "MANIFEST.sha256").write_text(
    "\n".join(f"{sha256(p)}  {p.name}" for p in sorted(DEST.glob("*")) if p.is_file() and p.name != "MANIFEST.sha256")
)
```

```python
# BORRADOR NO PROBADO: perfilado rapido para verificar tamano, nulos, tipos
import pandas as pd
hojas = pd.read_excel("data/raw/online_retail_ii/online_retail_II.xlsx", sheet_name=None, dtype=str)
df = pd.concat(hojas.values(), ignore_index=True)
print(df.shape); print(df.isna().mean().round(4)); print(df.duplicated().sum())
```

## 6. Riesgos

| Riesgo | Detalle | Mitigación |
|---|---|---|
| Licencia | Online Retail II: CC BY 4.0 (atribución obligatoria, citar DOI). Olist: NC-SA (no confirmada). Inside Airbnb: CC BY vs CC0 discrepante. Espejos (OpenML/Kaggle) pueden etiquetar distinto del original. | Citar siempre la fuente original; reconfirmar en la página oficial antes de publicar; descargar por script, no versionar RAW. |
| Tamaño | Online Retail II ~45 MB xlsx (memoria); leer xlsx es lento (minutos). | Convertir a parquet/SQLite en MASTER; usar muestra en CI. |
| Fuga de datos | Features con fecha posterior al corte; cancelaciones que revelan el futuro; en Olist, fechas de entrega. | Regla `fecha <= corte`; test pytest que recalcula FS truncando el dato; purga entre ventanas de etiqueta. |
| Privacidad/ética | Online Retail II: IDs de cliente seudónimos, sin datos personales evidentes. Inside Airbnb: nombres de anfitriones y reseñas = datos personales. Olist: IDs anonimizados, reseñas con texto. Sesgo por país (mayoría Reino Unido) y por naturaleza mayorista del comercio. | Descartar columnas de texto libre/nombres en MASTER; documentar sesgo; no usar para decisiones sobre personas. |
| Cambio en la fuente | UCI/Kaggle pueden mover URLs; Inside Airbnb borra snapshots antiguos. | Checksum + copia de respaldo propia (si la licencia lo permite, CC BY); fijar `version_datos`. |
| Red del entorno | En esta sesión los hosts de datos estaban bloqueados; en el Codespace del curso debe comprobarse el acceso. | Probar `curl -I` a los hosts antes de la clase; plan B: muestra incluida en el repo. |
| Dominio | Retail británico 2009-2011 no es cercano a Perú. | Aceptable como demostración; la tarea con Olist aporta contexto latinoamericano. |

## 7. Pendientes

1. Habilitar los hosts de datos y ejecutar la verificación real: tamaño, filas, columnas, tipos, % de nulos, duplicados y balance del objetivo de Online Retail II y Olist (y de las alternativas).
2. Confirmar la licencia leyendo directamente: UCI (502, 350, 222), Kaggle (Olist) y `insideairbnb.com/data-policies`. Decidir si NC-SA de Olist es aceptable para el curso.
3. Verificar qué ciudades de Inside Airbnb están disponibles (incluidas latinoamericanas) y qué snapshots se conservan.
4. Buscar un dataset tabular peruano (datosabiertos.gob.pe, MINSA, OSCE, SENAMHI) con licencia clara; no se pudo evaluar por el bloqueo y por la falta de resultados de búsqueda.
5. Correr los baselines de scikit-learn y reportar métricas reales; fijar los cortes de partición con los datos reales.
6. Probar los scripts de la sección 5 (son borradores).
