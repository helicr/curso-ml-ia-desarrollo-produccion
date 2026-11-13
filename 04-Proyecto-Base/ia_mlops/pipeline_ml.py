"""Pipeline MASTER -> FS -> ML: variables por cliente y corte, objetivo y particion temporal.

Cuadernos equivalentes: notebooks/02_pipeline_master_a_fs.ipynb y 03_pipeline_fs_a_ml.ipynb.
Entrada: master_facturas y master_lineas (las produce pipeline_ingesta_master).
Salida:  fs_catalogo, fs_cliente_corte, ml_particiones y ml_dataset.
FS y ML van juntos porque ML se construye a partir de FS con los mismos cortes: no tiene sentido rehacer uno sin el otro.

Idempotente (ver control.py): la huella de entrada es el CONTENIDO de las tablas de MASTER que se leen + los SQL de FS y ML
+ los cortes y la ventana del objetivo (config.py). Si cambias un corte o una variable, cambia la huella y se rehace.

Uso (desde 04-Proyecto-Base):
    python -m ia_mlops.pipeline_ml
    python -m ia_mlops.pipeline_ml --forzar
"""
import argparse

from . import config, control, db, features
from .modeling import ml_dataset

PIPELINE = 'pipeline_ml'
ENTRADA = ['master_facturas', 'master_lineas']
SALIDA = ['fs_catalogo', 'fs_cliente_corte', 'ml_particiones', 'ml_dataset']


def huella_entrada(con):
    sql = sorted((config.SQL / 'fs').glob('*.sql')) + sorted((config.SQL / 'ml').glob('*.sql'))
    return control.huella(control.huella_tablas(con, *ENTRADA), control.huella_archivos(*sql),
                          config.CORTES, config.VENTANA_OBJETIVO_DIAS, control.huella_codigo(features, ml_dataset))


def ejecutar(ruta_db=None, forzar=False, verbose=True):
    con = db.conectar(ruta_db)
    try:
        control.exigir(con, ENTRADA, 'pipeline_ingesta_master')

        def trabajo():
            features.construir_fs(con, verbose=verbose)
            ml_dataset.construir_ml(con, verbose)
            filas = dict(con.execute('SELECT particion, COUNT(*) FROM ml_dataset GROUP BY particion').fetchall())
            return {'fs_filas': db.escalar(con, 'SELECT COUNT(*) FROM fs_cliente_corte'), 'ml_filas_por_particion': filas}
        return control.ejecutar(con, PIPELINE, huella_entrada(con), lambda: all(control.existe(con, t) for t in SALIDA), trabajo, forzar, verbose)
    finally:
        con.close()


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--forzar', action='store_true', help='rehace FS y ML aunque la entrada no haya cambiado')
    control.desde_terminal(ejecutar, forzar=ap.parse_args().forzar)
