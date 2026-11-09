-- CAPA RAW: el dato original, sin limpiar.
-- Regla: RAW conserva los valores tal como vienen. SQLite necesita un tipo por columna, asi que las
-- columnas que en el original mezclan numeros y texto (Invoice, StockCode, Description) se guardan como TEXT.
-- Las columnas _id, _hoja y _fila son el LINAJE: permiten volver siempre a la fila original.
DROP TABLE IF EXISTS raw_online_retail_ii;
CREATE TABLE raw_online_retail_ii (
    _id          INTEGER PRIMARY KEY AUTOINCREMENT,  -- identificador de carga
    _hoja        TEXT,                               -- hoja del Excel o nombre del CSV de origen
    _fila        INTEGER,                            -- numero de fila en el archivo de origen
    Invoice      TEXT,                               -- numero de factura; empieza por 'C' si es una cancelacion
    StockCode    TEXT,                               -- codigo del producto (a veces texto, a veces numero)
    Description  TEXT,                               -- descripcion del producto
    Quantity     INTEGER,                            -- unidades (negativas en las cancelaciones)
    InvoiceDate  TEXT,                               -- fecha y hora en ISO 8601: AAAA-MM-DD HH:MM:SS
    Price        REAL,                               -- precio unitario en libras
    Customer_ID  REAL,                               -- el original lo guarda como decimal; puede ser nulo
    Country      TEXT
);

-- Auditoria de cada carga: que archivo, con que huella y cuantas filas.
DROP TABLE IF EXISTS raw_carga;
CREATE TABLE raw_carga (
    carga_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    fuente     TEXT NOT NULL,   -- 'muestra' o 'completo'
    archivo    TEXT NOT NULL,
    sha256     TEXT NOT NULL,   -- huella del archivo cargado
    filas      INTEGER NOT NULL,
    cargado_en TEXT NOT NULL
);
