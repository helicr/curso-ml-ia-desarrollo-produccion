-- CAPA FS (feature store didactica): variables REUTILIZABLES, calculadas por cliente y fecha de corte.
-- No es una plataforma de feature store: es una tabla con una regla de oro.
--     TODA variable se calcula SOLO con datos ANTERIORES a fecha_corte.
-- Asi se evita la fuga de informacion: el modelo nunca ve el futuro.
-- Granularidad: una fila por (cliente_id, fecha_corte).
DROP TABLE IF EXISTS fs_cliente_corte;
DROP TABLE IF EXISTS fs_catalogo;

CREATE TABLE fs_catalogo (
    feature      TEXT PRIMARY KEY,
    descripcion  TEXT NOT NULL,
    formula      TEXT NOT NULL,
    unidad       TEXT,
    entidad      TEXT NOT NULL DEFAULT 'cliente'
);

INSERT INTO fs_catalogo (feature, descripcion, formula, unidad) VALUES
 ('recencia_dias',            'Dias desde la ultima compra valida hasta el corte',          'corte - max(fecha_factura)',                          'dias'),
 ('frecuencia',               'Numero de facturas con ventas validas antes del corte',      'count(distinct factura)',                             'facturas'),
 ('monto_total',              'Gasto acumulado en ventas validas antes del corte',          'sum(monto_linea)',                                    'GBP'),
 ('ticket_medio',             'Gasto medio por factura',                                    'monto_total / frecuencia',                            'GBP'),
 ('unidades_total',           'Unidades compradas antes del corte',                         'sum(cantidad)',                                       'unidades'),
 ('productos_distintos',      'Productos distintos comprados antes del corte',              'count(distinct codigo_producto)',                     'productos'),
 ('antiguedad_dias',          'Dias desde la primera compra valida hasta el corte',         'corte - min(fecha_factura)',                          'dias'),
 ('frecuencia_90d',           'Facturas en los 90 dias previos al corte',                   'count(factura) con fecha >= corte - 90 dias',         'facturas'),
 ('monto_90d',                'Gasto en los 90 dias previos al corte',                      'sum(monto) con fecha >= corte - 90 dias',             'GBP'),
 ('frecuencia_180d',          'Facturas en los 180 dias previos al corte',                  'count(factura) con fecha >= corte - 180 dias',        'facturas'),
 ('dias_medios_entre_compras','Intervalo medio entre compras (NULL si solo hay una)',       '(ultima - primera) / (frecuencia - 1)',               'dias'),
 ('devoluciones',             'Facturas de cancelacion antes del corte',                    'count(distinct factura) con es_cancelacion = 1',      'facturas'),
 ('es_reino_unido',           'El cliente es del Reino Unido (1) o de otro pais (0)',       'pais = ''United Kingdom''',                           'indicador');

CREATE TABLE fs_cliente_corte (
    cliente_id                INTEGER NOT NULL REFERENCES master_clientes (cliente_id),
    fecha_corte               TEXT    NOT NULL,           -- AAAA-MM-DD; las variables usan solo datos anteriores
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
CREATE INDEX ix_fs_corte ON fs_cliente_corte (fecha_corte);
