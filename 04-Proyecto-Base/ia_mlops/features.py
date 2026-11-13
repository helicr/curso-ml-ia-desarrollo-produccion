"""Capa FS: variables reutilizables por cliente y fecha de corte.

Es la traduccion a Python de  notebooks/02_pipeline_master_a_fs.ipynb.

QUE ES FS
    De «feature store», almacen de variables: las variables (numeros que describen a cada cliente) se calculan una vez,
    se documentan (fs_catalogo: descripcion, formula y unidad) y se reutilizan. Granularidad de fs_cliente_corte:
    una fila por (cliente_id, fecha_corte). Es una capa didactica, no una plataforma completa.

FECHA DE CORTE
    El «hoy» de una foto del pasado. Para cada corte se calcula lo que se sabia de cada cliente ESE dia. Varios cortes
    dan varias fotos del mismo cliente y mas ejemplos para entrenar. Los cortes estan en config.CORTES.

REGLA DE ORO
    Cada variable usa solo datos ANTERIORES a su fecha de corte (fecha_factura < :corte en sql/fs/02_poblar_fs.sql).
    Si mirara el futuro habria FUGA DE INFORMACION: metricas excelentes en el cuaderno y un modelo inutil en produccion.
    La prueba tests/test_fs_y_ml.py::test_fs_no_usa_informacion_del_futuro lo verifica.

Las variables siguen la idea RFM (recencia, frecuencia, monto) mas actividad reciente, ritmo, devoluciones y pais.

Uso:  python -m ia_mlops.features
"""
from . import config, db


def todos_los_cortes():
    """Todas las fechas de corte de config.CORTES (train, valid y test), en orden."""
    return [c for lista in config.CORTES.values() for c in lista]


def construir_fs(con=None, cortes=None, verbose=True):
    """Crea las tablas de FS y las llena ejecutando la sentencia de sql/fs/02_poblar_fs.sql una vez por corte."""
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
