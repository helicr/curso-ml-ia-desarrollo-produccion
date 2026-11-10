-- CAPA ML: el dataset listo para entrenar = variables (FS) + objetivo (y) + particion.
-- Una fila por (cliente_id, fecha_corte).
--   y = 1 si el cliente compra al menos una vez en los 90 dias SIGUIENTES al corte; 0 si no.
-- La particion es TEMPORAL (train < valid < test), nunca aleatoria: asi el modelo se evalua como se usaria,
-- prediciendo un periodo que no ha visto.
DROP TABLE IF EXISTS ml_dataset;
DROP TABLE IF EXISTS ml_particiones;

CREATE TABLE ml_particiones (
    fecha_corte  TEXT    PRIMARY KEY,
    particion    TEXT    NOT NULL CHECK (particion IN ('train', 'valid', 'test')),
    ventana_dias INTEGER NOT NULL,   -- largo de la ventana en la que se mide el objetivo
    fin_ventana  TEXT    NOT NULL    -- fecha_corte + ventana_dias: la ventana es [fecha_corte, fin_ventana)
);

CREATE TABLE ml_dataset (
    cliente_id                INTEGER NOT NULL,
    fecha_corte               TEXT    NOT NULL REFERENCES ml_particiones (fecha_corte),
    particion                 TEXT    NOT NULL,
    y                         INTEGER NOT NULL CHECK (y IN (0, 1)),
    recencia_dias             INTEGER,
    frecuencia                INTEGER,
    monto_total               REAL,
    ticket_medio              REAL,
    unidades_total            INTEGER,
    productos_distintos       INTEGER,
    antiguedad_dias           INTEGER,
    frecuencia_90d            INTEGER,
    monto_90d                 REAL,
    frecuencia_180d           INTEGER,
    dias_medios_entre_compras REAL,
    devoluciones              INTEGER,
    es_reino_unido            INTEGER,
    PRIMARY KEY (cliente_id, fecha_corte)
);
CREATE INDEX ix_ml_particion ON ml_dataset (particion);
