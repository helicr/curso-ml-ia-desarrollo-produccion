-- BASE OPERACIONAL «retail»: simula el sistema de ventas de la tienda (OLTP).
-- Es la FUENTE del pipeline analitico: el cuaderno 00 la construye desde el archivo de UCI y el 01 la ingiere en RAW.
-- Modelo normalizado (cada dato se guarda una vez) y con restricciones, como un sistema transaccional.
-- Conserva la suciedad del origen (lineas repetidas, descripciones vacias, ventas sin cliente, cancelaciones,
-- codigos que no son productos): un sistema operacional real tambien la tiene, y es MASTER quien la trata.
DROP TABLE IF EXISTS lineas_factura;
DROP TABLE IF EXISTS facturas;
DROP TABLE IF EXISTS productos;
DROP TABLE IF EXISTS clientes;
DROP TABLE IF EXISTS origen_simulacion;

CREATE TABLE clientes (
    cliente_id   INTEGER PRIMARY KEY,
    fecha_alta   TEXT NOT NULL                -- primera compra registrada (ISO 8601)
);

CREATE TABLE productos (
    codigo_producto TEXT PRIMARY KEY,         -- StockCode tal como se tecleo (mayusculas y espacios incluidos)
    descripcion     TEXT                      -- descripcion de catalogo: la mas usada en sus lineas
);

CREATE TABLE facturas (
    factura_id    TEXT PRIMARY KEY,           -- empieza por 'C' si es una cancelacion
    cliente_id    INTEGER REFERENCES clientes (cliente_id),   -- nulo: venta sin cliente identificado
    pais          TEXT NOT NULL,
    fecha_emision TEXT NOT NULL               -- la de su primera linea
);

CREATE TABLE lineas_factura (
    linea_id        INTEGER PRIMARY KEY,      -- orden de registro
    factura_id      TEXT NOT NULL REFERENCES facturas (factura_id),
    codigo_producto TEXT NOT NULL REFERENCES productos (codigo_producto),
    descripcion     TEXT,                     -- texto impreso en la linea; puede diferir del catalogo o faltar
    cantidad        INTEGER NOT NULL,         -- negativa en las cancelaciones
    precio_unitario REAL NOT NULL,            -- libras
    registrada_en   TEXT NOT NULL             -- fecha y hora de la linea (ISO 8601)
);
CREATE INDEX ix_lineas_factura_factura ON lineas_factura (factura_id);

-- No es parte del negocio: deja constancia de que esta base es una SIMULACION y de que archivo sale.
CREATE TABLE origen_simulacion (
    fuente     TEXT NOT NULL,                 -- 'muestra' o 'completo'
    archivo    TEXT NOT NULL,
    sha256     TEXT NOT NULL,
    filas      INTEGER NOT NULL,
    creada_en  TEXT NOT NULL
);
