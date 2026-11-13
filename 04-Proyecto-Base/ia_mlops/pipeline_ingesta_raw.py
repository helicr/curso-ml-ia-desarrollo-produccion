"""Pipeline de INGESTA A RAW: base operacional (retail.db) -> capa RAW de la base analitica (curso.db).

Cuaderno equivalente: notebooks/01_pipeline_raw_a_master.ipynb, seccion 1.
Entrada: las 4 tablas de negocio de retail.db (la crea `python -m ia_mlops.operacional`, que simula el sistema de ventas).
Salida:  raw_clientes, raw_productos, raw_facturas, raw_lineas_factura y raw_carga (filas y huella de cada tabla).

Idempotente (ver control.py): la huella de entrada es el CONTENIDO de las tablas de origen + el SQL de RAW + el codigo de la ingesta.
Si el origen no cambio desde la ultima ingesta, no hace nada; si cambio (aunque sea una fila), vuelve a copiar todo.

Uso (desde 04-Proyecto-Base):
    python -m ia_mlops.pipeline_ingesta_raw
    python -m ia_mlops.pipeline_ingesta_raw --forzar        # rehace la ingesta aunque el origen no haya cambiado
"""
import argparse
from pathlib import Path

from . import config, control, db, dataset

PIPELINE = 'pipeline_ingesta_raw'
SALIDA = ['raw_clientes', 'raw_productos', 'raw_facturas', 'raw_lineas_factura', 'raw_carga']


def huella_entrada(con, ruta_operacional):
    con.execute('ATTACH DATABASE ? AS retail', (str(ruta_operacional),))
    try:
        origen = {t: dataset.huella_tabla(con, f'retail.{t}') for t in dataset.TABLAS_OPERACIONALES}
    finally:
        con.execute('DETACH DATABASE retail')
    return control.huella(origen, control.huella_archivos(config.SQL / 'raw' / '01_crear_raw.sql'), control.huella_codigo(dataset.cargar_raw))


def ejecutar(ruta_db=None, ruta_operacional=None, forzar=False, verbose=True):
    ruta_operacional = Path(ruta_operacional or config.DB_OPERACIONAL)
    if not ruta_operacional.exists():
        raise control.EntradaFaltanteError(f'No existe la base operacional {ruta_operacional}. Creala con:  python -m ia_mlops.operacional')
    con = db.conectar(ruta_db)
    try:
        def trabajo():
            dataset.cargar_raw(con, ruta_operacional, verbose)
            return {'tablas': dict(con.execute('SELECT tabla, filas FROM raw_carga ORDER BY carga_id').fetchall())}
        return control.ejecutar(con, PIPELINE, huella_entrada(con, ruta_operacional),
                                lambda: all(control.existe(con, t) for t in SALIDA), trabajo, forzar, verbose)
    finally:
        con.close()


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--forzar', action='store_true', help='rehace la ingesta aunque el origen no haya cambiado')
    control.desde_terminal(ejecutar, forzar=ap.parse_args().forzar)
