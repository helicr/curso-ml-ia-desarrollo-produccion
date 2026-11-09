-- Puebla MASTER desde RAW. Reglas de limpieza, en orden:
--   1. Recortar espacios y pasar codigos y descripciones a mayusculas.
--   2. Descartar duplicados exactos (se conserva la primera fila) y filas con datos obligatorios nulos.
--   3. Separar el modelo en clientes, productos, facturas y lineas.
--   4. Marcar que lineas son ventas validas (no cancelaciones, cantidad y precio positivos, producto real).
-- Todo lo descartado queda en master_descartes con su motivo: nada desaparece sin dejar rastro.

DROP TABLE IF EXISTS temp.tmp_raw_limpio;
CREATE TEMP TABLE tmp_raw_limpio AS
SELECT
    _id                                                AS raw_id,
    TRIM(Invoice)                                      AS factura_id,
    UPPER(TRIM(StockCode))                             AS codigo_producto,
    NULLIF(UPPER(TRIM(Description)), '')               AS descripcion,
    Quantity                                           AS cantidad,
    InvoiceDate                                        AS fecha_hora,
    Price                                              AS precio_unitario,
    CAST(Customer_ID AS INTEGER)                       AS cliente_id,
    TRIM(Country)                                      AS pais,
    ROW_NUMBER() OVER (
        PARTITION BY TRIM(Invoice), UPPER(TRIM(StockCode)), IFNULL(UPPER(TRIM(Description)), ''),
                     Quantity, InvoiceDate, Price, IFNULL(Customer_ID, -1), TRIM(Country)
        ORDER BY _id
    )                                                  AS rn
FROM raw_online_retail_ii;

INSERT INTO master_descartes (raw_id, motivo)
SELECT raw_id, 'duplicado_exacto' FROM temp.tmp_raw_limpio WHERE rn > 1;

INSERT INTO master_descartes (raw_id, motivo)
SELECT raw_id, 'dato_obligatorio_nulo'
FROM temp.tmp_raw_limpio
WHERE rn = 1
  AND (factura_id IS NULL OR factura_id = '' OR codigo_producto IS NULL OR codigo_producto = ''
       OR fecha_hora IS NULL OR cantidad IS NULL OR precio_unitario IS NULL OR pais IS NULL OR pais = '');

DROP TABLE IF EXISTS temp.tmp_raw_ok;
CREATE TEMP TABLE tmp_raw_ok AS
SELECT * FROM temp.tmp_raw_limpio
WHERE rn = 1 AND raw_id NOT IN (SELECT raw_id FROM master_descartes);

-- Clientes: un registro por Customer ID. El pais es el mas frecuente de sus movimientos.
INSERT INTO master_clientes (cliente_id, pais, primer_movimiento, ultimo_movimiento)
SELECT c.cliente_id, p.pais, c.primero, c.ultimo
FROM (
    SELECT cliente_id, MIN(fecha_hora) AS primero, MAX(fecha_hora) AS ultimo
    FROM temp.tmp_raw_ok WHERE cliente_id IS NOT NULL GROUP BY cliente_id
) c
JOIN (
    SELECT cliente_id, pais FROM (
        SELECT cliente_id, pais,
               ROW_NUMBER() OVER (PARTITION BY cliente_id ORDER BY COUNT(*) DESC, pais) AS rn
        FROM temp.tmp_raw_ok WHERE cliente_id IS NOT NULL GROUP BY cliente_id, pais
    ) WHERE rn = 1
) p ON p.cliente_id = c.cliente_id;

-- Productos: es_producto = 1 si el codigo empieza por 5 digitos (85123A). El resto son envio (POST),
-- comisiones (BANK CHARGES, AMAZONFEE), ajustes (ADJUST, B), regalos (gift_0001_20), pruebas (TEST001)...
INSERT INTO master_productos (codigo_producto, descripcion, es_producto)
SELECT codigo_producto, descripcion,
       CASE WHEN codigo_producto GLOB '[0-9][0-9][0-9][0-9][0-9]*' THEN 1 ELSE 0 END
FROM (
    SELECT codigo_producto, descripcion,
           ROW_NUMBER() OVER (PARTITION BY codigo_producto ORDER BY COUNT(*) DESC, IFNULL(descripcion, '')) AS rn
    FROM temp.tmp_raw_ok GROUP BY codigo_producto, descripcion
) WHERE rn = 1;

-- Facturas: una por numero. Si una factura trajera datos contradictorios, la regla de calidad R06 lo avisa.
INSERT INTO master_facturas (factura_id, cliente_id, fecha_factura, pais, es_cancelacion)
SELECT factura_id, MAX(cliente_id), MIN(fecha_hora), MIN(pais),
       CASE WHEN factura_id LIKE 'C%' THEN 1 ELSE 0 END
FROM temp.tmp_raw_ok GROUP BY factura_id;

-- Lineas: una por fila valida de RAW. linea_id = raw_id, asi se puede volver siempre al original.
INSERT INTO master_lineas (linea_id, factura_id, codigo_producto, cantidad, precio_unitario, monto_linea, es_venta_valida)
SELECT o.raw_id, o.factura_id, o.codigo_producto, o.cantidad, o.precio_unitario,
       ROUND(o.cantidad * o.precio_unitario, 2),
       CASE WHEN o.cantidad > 0 AND o.precio_unitario > 0 AND o.factura_id NOT LIKE 'C%' AND p.es_producto = 1
            THEN 1 ELSE 0 END
FROM temp.tmp_raw_ok o
JOIN master_productos p ON p.codigo_producto = o.codigo_producto;

DROP TABLE IF EXISTS temp.tmp_raw_ok;
DROP TABLE IF EXISTS temp.tmp_raw_limpio;
