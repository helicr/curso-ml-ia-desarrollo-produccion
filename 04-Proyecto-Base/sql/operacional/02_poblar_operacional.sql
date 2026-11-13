-- Deriva las tablas operacionales a partir de las lineas del archivo de origen (temp.tmp_origen, una fila por linea,
-- en el orden del archivo). Antes, el cuaderno 00 comprueba que cada factura tiene un solo cliente y un solo pais:
-- asi la normalizacion no pierde informacion y la ingesta en RAW puede reconstruir cada linea tal como era.

-- Clientes: uno por Customer ID. Su alta es su primera compra.
INSERT INTO clientes (cliente_id, fecha_alta)
SELECT cliente_id, MIN(registrada_en)
FROM temp.tmp_origen
WHERE cliente_id IS NOT NULL
GROUP BY cliente_id;

-- Catalogo de productos: un registro por codigo, con su descripcion mas frecuente.
INSERT INTO productos (codigo_producto, descripcion)
SELECT codigo_producto, descripcion
FROM (
    SELECT codigo_producto, descripcion,
           ROW_NUMBER() OVER (PARTITION BY codigo_producto ORDER BY COUNT(*) DESC, IFNULL(descripcion, '')) AS rn
    FROM temp.tmp_origen
    GROUP BY codigo_producto, descripcion
)
WHERE rn = 1;

-- Cabeceras de factura: cliente y pais son unicos por factura (comprobado antes); la fecha es la de la primera linea.
INSERT INTO facturas (factura_id, cliente_id, pais, fecha_emision)
SELECT factura_id, MAX(cliente_id), MAX(pais), MIN(registrada_en)
FROM temp.tmp_origen
GROUP BY factura_id;

-- Lineas: una por fila del archivo, incluidas las repetidas. Cada linea guarda su propia fecha y descripcion.
INSERT INTO lineas_factura (linea_id, factura_id, codigo_producto, descripcion, cantidad, precio_unitario, registrada_en)
SELECT linea_id, factura_id, codigo_producto, descripcion, cantidad, precio_unitario, registrada_en
FROM temp.tmp_origen
ORDER BY linea_id;
