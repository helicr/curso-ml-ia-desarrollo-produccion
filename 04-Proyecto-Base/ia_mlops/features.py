"""Capa FS: variables reutilizables por cliente y fecha de corte.

Es la traduccion a Python de  notebooks/02_pipeline_master_a_fs.ipynb.

Crea fs_catalogo y fs_cliente_corte (sql/fs/01_crear_fs.sql) y ejecuta sql/fs/02_poblar_fs.sql una vez por corte.
REGLA DE ORO: cada variable usa solo datos ANTERIORES a su fecha de corte (sin fuga de informacion).

Uso:  python -m ia_mlops.features
"""
from . import config, db


def todos_los_cortes():
    return [c for lista in config.CORTES.values() for c in lista]


def construir_fs(con=None, cortes=None, verbose=True):
    cierre = con is None
    con = con or db.conectar()
    db.ejecutar_script(con, config.SQL / 'fs' / '01_crear_fs.sql')
    for corte in (cortes or todos_los_cortes()):
        db.ejecutar_sentencia(con, config.SQL / 'fs' / '02_poblar_fs.sql', {'corte': corte})
        n = db.escalar(con, 'SELECT COUNT(*) FROM fs_cliente_corte WHERE fecha_corte = :c', {'c': corte})
        if verbose:
            print(f'  FS: corte {corte}: {n:,} clientes')
    if cierre:
        con.close()


if __name__ == '__main__':
    construir_fs()
