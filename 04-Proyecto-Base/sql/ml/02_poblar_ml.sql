-- Puebla ml_dataset: une las variables de FS con el objetivo y la particion.
-- El objetivo mira el FUTURO del corte (esa es su funcion); las variables solo miran el PASADO.
INSERT INTO ml_dataset (
    cliente_id, fecha_corte, particion, y,
    recencia_dias, frecuencia, monto_total, ticket_medio, unidades_total, productos_distintos,
    antiguedad_dias, frecuencia_90d, monto_90d, frecuencia_180d, dias_medios_entre_compras,
    devoluciones, es_reino_unido
)
SELECT fs.cliente_id, fs.fecha_corte, p.particion,
       CASE WHEN EXISTS (
           SELECT 1
           FROM master_facturas f
           JOIN master_lineas l ON l.factura_id = f.factura_id
           WHERE f.cliente_id = fs.cliente_id
             AND l.es_venta_valida = 1
             AND f.fecha_factura >= p.fecha_corte
             AND f.fecha_factura <  p.fin_ventana
       ) THEN 1 ELSE 0 END AS y,
       fs.recencia_dias, fs.frecuencia, fs.monto_total, fs.ticket_medio, fs.unidades_total, fs.productos_distintos,
       fs.antiguedad_dias, fs.frecuencia_90d, fs.monto_90d, fs.frecuencia_180d, fs.dias_medios_entre_compras,
       fs.devoluciones, fs.es_reino_unido
FROM fs_cliente_corte fs
JOIN ml_particiones p ON p.fecha_corte = fs.fecha_corte;
