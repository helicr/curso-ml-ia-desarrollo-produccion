"""Capa ML: arma el dataset de entrenamiento = variables (FS) + objetivo (y) + particion temporal.

Es la traduccion a Python de  notebooks/03_pipeline_fs_a_ml.ipynb.

Antes de construir comprueba que la ventana del objetivo de cada corte cabe en los datos disponibles: si la ventana se sale
del ultimo dia con datos, el objetivo estaria incompleto y sesgado.

Uso:  python -m ia_mlops.modeling.ml_dataset
"""
from .. import config, db


class VentanaIncompletaError(RuntimeError):
    pass


def construir_ml(con=None, verbose=True):
    cierre = con is None
    con = con or db.conectar()
    db.ejecutar_script(con, config.SQL / 'ml' / '01_crear_ml.sql')
    ultimo_dia = db.escalar(con, 'SELECT MAX(fecha_factura) FROM master_facturas')
    for particion, cortes in config.CORTES.items():
        for corte in cortes:
            fin = db.escalar(con, "SELECT date(:c, '+' || :d || ' day')", {'c': corte, 'd': config.VENTANA_OBJETIVO_DIAS})
            if fin > ultimo_dia[:10]:
                raise VentanaIncompletaError(
                    f'El corte {corte} necesita datos hasta {fin}, pero el ultimo dia con datos es {ultimo_dia[:10]}.')
            con.execute('INSERT INTO ml_particiones (fecha_corte, particion, ventana_dias, fin_ventana) VALUES (?,?,?,?)',
                        (corte, particion, config.VENTANA_OBJETIVO_DIAS, fin))
    con.commit()
    db.ejecutar_script(con, config.SQL / 'ml' / '02_poblar_ml.sql')
    if verbose:
        filas = con.execute('SELECT particion, COUNT(*), ROUND(100.0 * AVG(y), 1) FROM ml_dataset GROUP BY particion ORDER BY MIN(fecha_corte)').fetchall()
        for particion, n, tasa in filas:
            print(f'  ML: {particion:5s} {n:>7,} filas | tasa de recompra {tasa} %')
    if cierre:
        con.close()


if __name__ == '__main__':
    construir_ml()
