"""Capa ML: arma el dataset de entrenamiento = variables (FS) + objetivo (y) + particion temporal.

Es la traduccion a Python de  notebooks/03_pipeline_fs_a_ml.ipynb.

OBJETIVO (y)
    y = 1 si el cliente compra al menos una vez en la ventana [corte, corte + VENTANA_OBJETIVO_DIAS); 0 si no.
    Es lo unico que mira el FUTURO del corte, y es correcto: es la respuesta que el modelo debe anticipar.

PARTICION TEMPORAL (config.CORTES)
    train  el modelo aprende       valid  se comparan modelos y se elige       test  se mide el elegido, una sola vez
    Es por TIEMPO, nunca aleatoria: en produccion se entrena con el pasado y se predice el futuro. Las ventanas del objetivo
    no se solapan entre particiones (el ultimo corte de train + 90 dias = el corte de valid).

Antes de construir comprueba que la ventana del objetivo de cada corte cabe en los datos disponibles: si la ventana se sale
del ultimo dia con datos, el objetivo estaria incompleto y sesgado (muchos «no compro» solo por falta de datos).

Uso:  python -m ia_mlops.modeling.ml_dataset
"""
from .. import config, db


class VentanaIncompletaError(RuntimeError):
    pass


def construir_ml(con=None, verbose=True):
    """Registra los cortes en ml_particiones (comprobando que su ventana cabe) y llena ml_dataset con sql/ml/02_poblar_ml.sql."""
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
