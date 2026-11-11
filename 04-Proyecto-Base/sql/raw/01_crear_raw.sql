-- CAPA RAW: copia fiel de la base operacional «retail», sin limpiar nada.
-- Regla: una tabla RAW por tabla de origen, con las mismas columnas y los mismos valores. RAW no valida ni corrige:
-- por eso no declara claves ni restricciones (si el origen trae un problema, RAW lo conserva y MASTER lo trata).
-- LINAJE: la clave de origen (cliente_id, factura_id, linea_id...) mas _carga_id, que apunta a raw_carga.
DROP TABLE IF EXISTS raw_clientes;
CREATE TABLE raw_clientes (
    cliente_id   INTEGER,
    fecha_alta   TEXT,
    _carga_id    INTEGER
);

DROP TABLE IF EXISTS raw_productos;
CREATE TABLE raw_productos (
    codigo_producto TEXT,
    descripcion     TEXT,
    _carga_id       INTEGER
);

DROP TABLE IF EXISTS raw_facturas;
CREATE TABLE raw_facturas (
    factura_id    TEXT,
    cliente_id    INTEGER,
    pais          TEXT,
    fecha_emision TEXT,
    _carga_id     INTEGER
);

DROP TABLE IF EXISTS raw_lineas_factura;
CREATE TABLE raw_lineas_factura (
    linea_id        INTEGER,
    factura_id      TEXT,
    codigo_producto TEXT,
    descripcion     TEXT,
    cantidad        INTEGER,
    precio_unitario REAL,
    registrada_en   TEXT,
    _carga_id       INTEGER
);

-- Auditoria de cada extraccion: de que tabla, cuantas filas y la huella sha256 de su contenido.
-- Si la huella cambia entre dos cargas, cambio el origen.
DROP TABLE IF EXISTS raw_carga;
CREATE TABLE raw_carga (
    carga_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    origen      TEXT NOT NULL,    -- 'retail'
    tabla       TEXT NOT NULL,
    filas       INTEGER NOT NULL,
    sha256      TEXT NOT NULL,
    extraido_en TEXT NOT NULL
);
