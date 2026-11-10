-- CAPA MASTER: el dato depurado, con tipos correctos, claves y relaciones.
-- De una sola tabla plana (raw) pasamos a un modelo relacional: clientes, productos, facturas y lineas.
-- Regla: MASTER se puede borrar y regenerar por completo desde RAW. Nada se edita a mano.
PRAGMA foreign_keys = OFF;
DROP TABLE IF EXISTS master_lineas;
DROP TABLE IF EXISTS master_facturas;
DROP TABLE IF EXISTS master_productos;
DROP TABLE IF EXISTS master_clientes;
DROP TABLE IF EXISTS master_descartes;
DROP TABLE IF EXISTS master_calidad;
PRAGMA foreign_keys = ON;

CREATE TABLE master_clientes (
    cliente_id         INTEGER PRIMARY KEY,     -- el Customer ID original, ya como entero
    pais               TEXT    NOT NULL,        -- pais mas frecuente del cliente
    primer_movimiento  TEXT    NOT NULL,        -- fecha y hora del primer movimiento (compra o cancelacion)
    ultimo_movimiento  TEXT    NOT NULL
);

CREATE TABLE master_productos (
    codigo_producto TEXT PRIMARY KEY,           -- StockCode en mayusculas y sin espacios
    descripcion     TEXT,                       -- descripcion mas frecuente
    es_producto     INTEGER NOT NULL CHECK (es_producto IN (0, 1))  -- 0 = envio, comisiones, ajustes, regalos, pruebas
);

CREATE TABLE master_facturas (
    factura_id     TEXT PRIMARY KEY,
    cliente_id     INTEGER REFERENCES master_clientes (cliente_id),  -- NULL si la factura no trae cliente
    fecha_factura  TEXT NOT NULL,               -- AAAA-MM-DD HH:MM:SS
    pais           TEXT NOT NULL,
    es_cancelacion INTEGER NOT NULL CHECK (es_cancelacion IN (0, 1))  -- 1 si el numero empieza por 'C'
);

CREATE TABLE master_lineas (
    linea_id        INTEGER PRIMARY KEY,        -- = _id de la fila en RAW (linaje)
    factura_id      TEXT    NOT NULL REFERENCES master_facturas (factura_id),
    codigo_producto TEXT    NOT NULL REFERENCES master_productos (codigo_producto),
    cantidad        INTEGER NOT NULL,
    precio_unitario REAL    NOT NULL,
    monto_linea     REAL    NOT NULL,           -- cantidad * precio_unitario
    es_venta_valida INTEGER NOT NULL CHECK (es_venta_valida IN (0, 1))
        -- 1 = cantidad > 0, precio > 0, factura no cancelada y codigo que es un producto real
);

-- Filas de RAW que NO pasaron a MASTER y por que. raw = master_lineas + master_descartes.
CREATE TABLE master_descartes (
    raw_id INTEGER PRIMARY KEY,
    motivo TEXT NOT NULL
);

-- Resultado de las reglas de calidad de la ultima ejecucion.
CREATE TABLE master_calidad (
    regla        TEXT PRIMARY KEY,
    descripcion  TEXT NOT NULL,
    valor        REAL,
    umbral       TEXT,
    estado       TEXT NOT NULL CHECK (estado IN ('OK', 'ALERTA', 'ERROR')),
    evaluado_en  TEXT NOT NULL
);

CREATE INDEX ix_master_facturas_cliente_fecha ON master_facturas (cliente_id, fecha_factura);
CREATE INDEX ix_master_facturas_fecha         ON master_facturas (fecha_factura);
CREATE INDEX ix_master_lineas_factura         ON master_lineas (factura_id);
CREATE INDEX ix_master_lineas_valida          ON master_lineas (es_venta_valida);
