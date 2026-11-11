"""Pruebas de las capas FS y ML: sin fuga de informacion, particion temporal y objetivo bien definido."""
import shutil

import pandas as pd
import pytest

from ia_mlops import config, db
from ia_mlops import features


def _fs(con, corte=None):
    sql = 'SELECT * FROM fs_cliente_corte' + (' WHERE fecha_corte = :c' if corte else '') + ' ORDER BY cliente_id, fecha_corte'
    return pd.read_sql(sql, con, params={'c': corte} if corte else None)


def test_fs_tiene_una_fila_por_cliente_y_corte(con):
    assert db.escalar(con, 'SELECT COUNT(*) FROM (SELECT cliente_id, fecha_corte FROM fs_cliente_corte GROUP BY 1, 2 HAVING COUNT(*) > 1)') == 0


def test_fs_cubre_todos_los_cortes_de_la_configuracion(con):
    cortes = {c for (c,) in con.execute('SELECT DISTINCT fecha_corte FROM fs_cliente_corte')}
    esperados = {c for lista in config.CORTES.values() for c in lista}
    assert cortes == esperados


def test_fs_las_variables_tienen_valores_coherentes(con):
    df = _fs(con)
    assert (df['recencia_dias'] >= 0).all() and (df['antiguedad_dias'] >= df['recencia_dias']).all()
    assert (df['frecuencia'] >= 1).all() and (df['frecuencia_90d'] <= df['frecuencia_180d']).all()
    assert (df['frecuencia_180d'] <= df['frecuencia']).all() and (df['monto_total'] > 0).all()
    assert set(df['es_reino_unido'].unique()) <= {0, 1}


def test_fs_catalogo_describe_todas_las_variables(con):
    descritas = {f for (f,) in con.execute('SELECT feature FROM fs_catalogo')}
    assert set(config.FEATURES) <= descritas


@pytest.mark.parametrize('corte', ['2010-12-01', '2011-06-01'])
def test_fs_no_usa_informacion_del_futuro(con, ruta_db, tmp_path, corte):
    """Si borramos TODO lo posterior al corte y recalculamos, las variables no deben cambiar.

    Tambien se borra master_clientes: resume toda la historia del cliente (pais mas frecuente, ultimo movimiento),
    pasado y futuro, asi que FS no debe depender de ella."""
    original = _fs(con, corte)
    copia = tmp_path / 'sin_futuro.db'
    shutil.copy(ruta_db, copia)
    c2 = db.conectar(copia)
    c2.execute('PRAGMA foreign_keys = OFF')
    c2.execute('DELETE FROM master_lineas WHERE factura_id IN (SELECT factura_id FROM master_facturas WHERE fecha_factura >= ?)', (corte,))
    c2.execute('DELETE FROM master_facturas WHERE fecha_factura >= ?', (corte,))
    c2.execute('DELETE FROM master_clientes')
    c2.commit()
    features.construir_fs(c2, cortes=[corte], verbose=False)
    sin_futuro = _fs(c2, corte)
    c2.close()
    pd.testing.assert_frame_equal(original.reset_index(drop=True), sin_futuro.reset_index(drop=True))


def test_ml_las_particiones_son_temporales_y_no_se_solapan(con):
    p = pd.read_sql('SELECT * FROM ml_particiones ORDER BY fecha_corte', con)
    orden = {'train': 0, 'valid': 1, 'test': 2}
    assert list(p['particion'].map(orden)) == sorted(p['particion'].map(orden))      # train < valid < test en el tiempo
    por_particion = p.groupby('particion').agg(primero=('fecha_corte', 'min'), ultimo_corte=('fecha_corte', 'max'), fin=('fin_ventana', 'max'))
    assert por_particion.loc['train', 'fin'] <= por_particion.loc['valid', 'primero']
    assert por_particion.loc['valid', 'fin'] <= por_particion.loc['test', 'primero']


def test_ml_el_objetivo_es_binario_y_hay_las_dos_clases_en_cada_particion(con):
    df = pd.read_sql('SELECT particion, y FROM ml_dataset', con)
    assert set(df['y'].unique()) <= {0, 1}
    for particion in ('train', 'valid', 'test'):
        assert df[df['particion'] == particion]['y'].nunique() == 2, particion


def test_ml_las_variables_coinciden_con_fs(con):
    ml = pd.read_sql('SELECT cliente_id, fecha_corte, recencia_dias, monto_total FROM ml_dataset ORDER BY 1, 2', con)
    fs = pd.read_sql('SELECT cliente_id, fecha_corte, recencia_dias, monto_total FROM fs_cliente_corte ORDER BY 1, 2', con)
    pd.testing.assert_frame_equal(ml.reset_index(drop=True), fs.reset_index(drop=True))


def test_ml_el_objetivo_se_recalcula_igual_con_pandas(con):
    ml = pd.read_sql('SELECT cliente_id, fecha_corte, y FROM ml_dataset', con)
    ventas = pd.read_sql('''SELECT f.cliente_id, f.fecha_factura FROM master_lineas l
                            JOIN master_facturas f ON f.factura_id = l.factura_id
                            WHERE l.es_venta_valida = 1 AND f.cliente_id IS NOT NULL''', con)
    ventas['fecha'] = pd.to_datetime(ventas['fecha_factura'])
    muestra = ml.sample(min(300, len(ml)), random_state=0)
    for fila in muestra.itertuples():
        ini = pd.Timestamp(fila.fecha_corte)
        fin = ini + pd.Timedelta(days=config.VENTANA_OBJETIVO_DIAS)
        compra = ((ventas['cliente_id'] == fila.cliente_id) & (ventas['fecha'] >= ini) & (ventas['fecha'] < fin)).any()
        assert int(compra) == fila.y, (fila.cliente_id, fila.fecha_corte)
