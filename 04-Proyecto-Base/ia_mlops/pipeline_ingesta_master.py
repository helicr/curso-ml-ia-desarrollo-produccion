"""Pipeline RAW -> MASTER: depura RAW, construye el modelo relacional y evalua las reglas de calidad.

Cuaderno equivalente: notebooks/01_pipeline_raw_a_master.ipynb, secciones 2 a 4.
Entrada: la capa RAW (la produce pipeline_ingesta_raw).
Salida:  master_clientes, master_productos, master_facturas, master_lineas, master_descartes y master_calidad.
Si falla una regla de calidad DURA, se detiene con error y no registra la ejecucion.

Idempotente (ver control.py): la huella de entrada es la huella de cada tabla RAW (la guarda raw_carga) + los SQL de MASTER
+ las reglas de calidad. Si nada de eso cambio, no hace nada.

Uso (desde 04-Proyecto-Base):
    python -m ia_mlops.pipeline_ingesta_master
    python -m ia_mlops.pipeline_ingesta_master --forzar
"""
import argparse

from . import calidad, config, control, dataset, db

PIPELINE = 'pipeline_ingesta_master'
ENTRADA = ['raw_facturas', 'raw_lineas_factura', 'raw_carga']
SALIDA = ['master_clientes', 'master_productos', 'master_facturas', 'master_lineas', 'master_calidad']


def huella_entrada(con):
    raw = con.execute('SELECT tabla, filas, sha256 FROM raw_carga ORDER BY tabla').fetchall()
    sql = control.huella_archivos(config.SQL / 'master' / '01_crear_master.sql', config.SQL / 'master' / '02_poblar_master.sql')
    return control.huella(raw, sql, control.huella_codigo(calidad, dataset.construir_master))


def ejecutar(ruta_db=None, forzar=False, verbose=True):
    con = db.conectar(ruta_db)
    try:
        control.exigir(con, ENTRADA, 'pipeline_ingesta_raw')

        def trabajo():
            resultados = dataset.construir_master(con, verbose)
            filas = {t: db.escalar(con, f'SELECT COUNT(*) FROM {t}') for t in SALIDA + ['master_descartes']}
            return {'filas': filas, 'alertas': [r['regla'] for r in resultados if r['estado'] == 'ALERTA']}
        return control.ejecutar(con, PIPELINE, huella_entrada(con), lambda: all(control.existe(con, t) for t in SALIDA), trabajo, forzar, verbose)
    finally:
        con.close()


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--forzar', action='store_true', help='rehace MASTER aunque RAW y las reglas no hayan cambiado')
    control.desde_terminal(ejecutar, forzar=ap.parse_args().forzar)
