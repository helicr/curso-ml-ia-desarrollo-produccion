-- Puebla fs_cliente_corte para UNA fecha de corte (parametro :corte, formato AAAA-MM-DD).
-- Se ejecuta una vez por cada corte (ver ia_mlops/features.py y el cuaderno 02).
-- Regla de oro: todos los filtros usan  fecha_factura < :corte  (estrictamente antes del corte).
WITH ventas AS (
    SELECT f.cliente_id, f.factura_id, f.fecha_factura, l.codigo_producto, l.cantidad, l.monto_linea
    FROM master_lineas l
    JOIN master_facturas f ON f.factura_id = l.factura_id
    WHERE l.es_venta_valida = 1
      AND f.cliente_id IS NOT NULL
      AND f.fecha_factura < :corte
),
facturas AS (
    SELECT cliente_id, factura_id, MAX(fecha_factura) AS fecha, SUM(monto_linea) AS monto
    FROM ventas GROUP BY cliente_id, factura_id
),
por_cliente AS (
    SELECT cliente_id,
           COUNT(*)                                                                    AS frecuencia,
           SUM(monto)                                                                  AS monto_total,
           MAX(fecha)                                                                  AS ultima,
           MIN(fecha)                                                                  AS primera,
           SUM(CASE WHEN fecha >= date(:corte, '-90 day')  THEN 1     ELSE 0 END)     AS frecuencia_90d,
           SUM(CASE WHEN fecha >= date(:corte, '-90 day')  THEN monto ELSE 0 END)     AS monto_90d,
           SUM(CASE WHEN fecha >= date(:corte, '-180 day') THEN 1     ELSE 0 END)     AS frecuencia_180d
    FROM facturas GROUP BY cliente_id
),
productos AS (
    SELECT cliente_id, SUM(cantidad) AS unidades_total, COUNT(DISTINCT codigo_producto) AS productos_distintos
    FROM ventas GROUP BY cliente_id
),
devoluciones AS (
    SELECT cliente_id, COUNT(DISTINCT factura_id) AS devoluciones
    FROM master_facturas
    WHERE es_cancelacion = 1 AND cliente_id IS NOT NULL AND fecha_factura < :corte
    GROUP BY cliente_id
),
-- Pais del cliente EN EL CORTE: el mas frecuente de sus lineas anteriores al corte.
-- No se usa master_clientes.pais: resume TODA la historia del cliente (tambien el futuro) y seria una fuga.
pais AS (
    SELECT cliente_id, pais FROM (
        SELECT f.cliente_id, f.pais,
               ROW_NUMBER() OVER (PARTITION BY f.cliente_id ORDER BY COUNT(*) DESC, f.pais) AS rn
        FROM master_lineas l
        JOIN master_facturas f ON f.factura_id = l.factura_id
        WHERE f.cliente_id IS NOT NULL AND f.fecha_factura < :corte
        GROUP BY f.cliente_id, f.pais
    ) WHERE rn = 1
)
INSERT INTO fs_cliente_corte (
    cliente_id, fecha_corte, recencia_dias, frecuencia, monto_total, ticket_medio, unidades_total,
    productos_distintos, antiguedad_dias, frecuencia_90d, monto_90d, frecuencia_180d,
    dias_medios_entre_compras, devoluciones, es_reino_unido
)
SELECT p.cliente_id,
       :corte,
       CAST(julianday(:corte) - julianday(p.ultima)  AS INTEGER),
       p.frecuencia,
       ROUND(p.monto_total, 2),
       ROUND(p.monto_total * 1.0 / p.frecuencia, 2),
       pr.unidades_total,
       pr.productos_distintos,
       CAST(julianday(:corte) - julianday(p.primera) AS INTEGER),
       p.frecuencia_90d,
       ROUND(p.monto_90d, 2),
       p.frecuencia_180d,
       CASE WHEN p.frecuencia > 1
            THEN ROUND((julianday(p.ultima) - julianday(p.primera)) / (p.frecuencia - 1), 1) END,
       COALESCE(d.devoluciones, 0),
       CASE WHEN pa.pais = 'United Kingdom' THEN 1 ELSE 0 END
FROM por_cliente p
JOIN productos pr        ON pr.cliente_id = p.cliente_id
JOIN pais pa             ON pa.cliente_id = p.cliente_id
LEFT JOIN devoluciones d ON d.cliente_id  = p.cliente_id;
