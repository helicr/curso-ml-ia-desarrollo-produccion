# Modelo de datos del caso transversal: Online Retail II

**Pregunta de negocio:** dado un cliente y una fecha de corte, ¿volverá a comprar en los **90 días siguientes**?
Es una clasificación binaria sobre clientes de una tienda online. Se entiende sin saber estadística, tiene dimensión temporal
(permite una partición sin fuga) y el dato original trae suciedad real que justifica cada capa.

**Fuente:** Online Retail II, UCI Machine Learning Repository. Licencia **CC BY 4.0** (verificada en la ficha oficial el 09/11/2026).
Cita: Chen, D. (2012). *Online Retail II* [Dataset]. https://doi.org/10.24432/C5CG6D · 1 067 371 filas · 01/12/2009 a 09/12/2011.

## El orden de las capas
```
RAW  →  MASTER  →  FS  →  ML  →  ARTEFACTOS  →  SERVICIO
```
**FS va antes que ML**: ML se construye a partir de las variables de FS, más el objetivo y la partición. Cada capa se puede borrar y regenerar
desde la anterior; nada se edita a mano.

| Capa | Qué contiene | Tablas | Se construye con |
|---|---|---|---|
| **RAW** | El dato original, sin limpiar, con linaje | `raw_online_retail_ii`, `raw_carga` | `sql/raw/` · `ia_mlops/dataset.py` |
| **MASTER** | El dato depurado y relacional | `master_clientes`, `master_productos`, `master_facturas`, `master_lineas`, `master_descartes`, `master_calidad` | `sql/master/` · `ia_mlops/dataset.py` |
| **FS** | Variables reutilizables por cliente y corte | `fs_cliente_corte`, `fs_catalogo` | `sql/fs/` · `ia_mlops/features.py` |
| **ML** | Dataset de entrenamiento: variables + objetivo + partición | `ml_dataset`, `ml_particiones` | `sql/ml/` · `ia_mlops/modeling/ml_dataset.py` |
| **ARTEFACTOS** | Modelo, métricas y metadatos | `models/`, `reports/` y MLflow | `ia_mlops/modeling/train.py` |

Cada capa tiene su **cuaderno** en `notebooks/` (el pipeline) y su traducción en el paquete `ia_mlops` (ver `de-notebook-a-python.md`).
Todo el flujo: `python -m ia_mlops.pipeline` (usa la muestra incluida) o `python -m ia_mlops.pipeline --fuente completo`.

## Diagrama de MASTER, FS y ML
```mermaid
erDiagram
    master_clientes ||--o{ master_facturas : "cliente_id"
    master_facturas ||--|{ master_lineas : "factura_id"
    master_productos ||--o{ master_lineas : "codigo_producto"
    master_clientes ||--o{ fs_cliente_corte : "cliente_id"
    fs_cliente_corte ||--|| ml_dataset : "cliente_id, fecha_corte"
    ml_particiones ||--o{ ml_dataset : "fecha_corte"

    master_clientes { int cliente_id PK; text pais; text primer_movimiento; text ultimo_movimiento }
    master_productos { text codigo_producto PK; text descripcion; int es_producto }
    master_facturas { text factura_id PK; int cliente_id FK; text fecha_factura; text pais; int es_cancelacion }
    master_lineas { int linea_id PK; text factura_id FK; text codigo_producto FK; int cantidad; real precio_unitario; real monto_linea; int es_venta_valida }
    fs_cliente_corte { int cliente_id PK; text fecha_corte PK; real recencia_dias; real frecuencia; real monto_total }
    ml_dataset { int cliente_id PK; text fecha_corte PK; text particion; int y }
    ml_particiones { text fecha_corte PK; text particion; int ventana_dias; text fin_ventana }
```

## RAW: lo que se conserva
Una tabla plana con las 8 columnas del original (`Invoice`, `StockCode`, `Description`, `Quantity`, `InvoiceDate`, `Price`, `Customer_ID`, `Country`)
más el **linaje** `_id`, `_hoja` y `_fila`. `raw_carga` guarda la huella sha256 de cada archivo cargado.
RAW no corrige nada. Los problemas que se encuentran en el dato real (medidos sobre el archivo completo):
- `Invoice` mezcla números (1 047 871 filas) y texto como `C489449` (19 500 filas); `StockCode` mezcla enteros (932 385) y texto (134 986); `Description` trae a veces números.
- `Customer ID` viene como decimal y a veces falta.
- Hay duplicados exactos, cantidades negativas (cancelaciones), precios en cero y códigos que no son productos (`POST`, `BANK CHARGES`, `M`, `gift_0001_20`…).

## MASTER: reglas de limpieza
1. Recortar espacios y pasar `StockCode` y `Description` a mayúsculas.
2. Descartar **duplicados exactos** (se conserva la primera fila) y filas con datos obligatorios nulos. Todo lo descartado queda en `master_descartes` con su motivo.
3. Separar en clientes, productos, facturas y líneas. El `Customer ID` pasa a entero; una factura sin cliente se conserva con `cliente_id` nulo.
4. `es_cancelacion = 1` si el número de factura empieza por `C`.
5. `es_producto = 1` si el código empieza por 5 dígitos (`85123A`). El resto son envío, comisiones, ajustes, regalos o pruebas.
6. `es_venta_valida = 1` si la cantidad y el precio son positivos, la factura no está cancelada y el código es un producto real.

**Reglas de calidad** (`ia_mlops/calidad.py` y el cuaderno 01, resultado en `master_calidad`): conciliación `raw = master + descartes`, facturas sin líneas, integridad referencial,
monto coherente, fechas en rango (duras: si fallan, el pipeline se detiene); facturas con varios clientes y cancelaciones con cantidad positiva (alertas);
porcentaje de líneas sin cliente, de ventas válidas, duplicados, precios no positivos y códigos que no son producto (informativas).

## FS: variables por cliente y corte
Granularidad: una fila por `(cliente_id, fecha_corte)`. **Regla de oro: cada variable usa solo datos anteriores al corte.**
La prueba `test_fs_no_usa_informacion_del_futuro` lo verifica borrando todo lo posterior al corte y comprobando que las variables no cambian.
`fs_catalogo` describe cada variable con su fórmula y unidad. Es una capa didáctica, no una plataforma completa de feature store.

| Variable | Qué mide |
|---|---|
| `recencia_dias` | Días desde la última compra válida |
| `frecuencia` | Facturas con ventas válidas |
| `monto_total`, `ticket_medio` | Gasto acumulado y gasto medio por factura |
| `unidades_total`, `productos_distintos` | Volumen y variedad |
| `antiguedad_dias` | Días desde la primera compra |
| `frecuencia_90d`, `monto_90d`, `frecuencia_180d` | Actividad reciente |
| `dias_medios_entre_compras` | Ritmo de compra (nulo si solo hay una) |
| `devoluciones` | Facturas de cancelación |
| `es_reino_unido` | País del cliente |

## ML: objetivo y partición
`y = 1` si el cliente compra al menos una vez en la ventana **[corte, corte + 90 días)**. La partición es **temporal**, con ventanas que no se solapan:

| Partición | Cortes | Ventana del objetivo termina |
|---|---|---|
| train | 2010-06-01 a 2010-12-01 (mensual) | 2011-03-01 |
| valid | 2011-03-01 | 2011-05-30 |
| test | 2011-06-01 y 2011-09-01 | 2011-11-30 |

Antes de construir ML se comprueba que la ventana de cada corte cabe en los datos (el último día con datos es 2011-12-09).

## Cómo adaptar el caso a la tarea
La tarea de los alumnos repite esta receta con **otro dataset de estructura similar** (entidad, fecha de corte, objetivo y variables propias):
cambian `sql/master/`, las variables de `sql/fs/` y el objetivo de `sql/ml/`; se mantienen las reglas (RAW intacto, descartes con motivo, sin fuga, partición temporal)
y las pruebas de `tests/`. La tarea también es un cuaderno-pipeline: su traducción a `.py` es parte de la entrega. Entregable de S1: «adaptar una transformación o variable» (por ejemplo, añadir una variable a FS, documentarla en `fs_catalogo` y mostrar su efecto en el modelo).
