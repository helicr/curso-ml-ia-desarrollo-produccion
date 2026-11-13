"""Pruebas de la base operacional y de las capas RAW y MASTER."""
import pandas as pd

from ia_mlops import config, db
from ia_mlops.dataset import TABLAS_OPERACIONALES, huella_tabla


# --------------------------------------------------------------------------------------------------- operacional
def test_operacional_respeta_sus_claves_foraneas(con_operacional):
    assert con_operacional.execute('PRAGMA foreign_key_check').fetchall() == []


def test_operacional_reconstruye_cada_fila_del_archivo(con_operacional):
    """Normalizar no pierde informacion: linea + cabecera = la fila original, en el mismo orden."""
    original = pd.read_csv(config.FUENTES['muestra'], dtype=object, keep_default_na=False, na_values=[''])
    reconstruido = pd.read_sql(
        'SELECT l.factura_id, l.codigo_producto, l.descripcion, l.cantidad, l.registrada_en, l.precio_unitario, f.cliente_id, f.pais '
        'FROM lineas_factura l JOIN facturas f ON f.factura_id = l.factura_id ORDER BY l.linea_id', con_operacional)
    assert len(reconstruido) == len(original)
    assert (reconstruido['factura_id'] == original['Invoice']).all()
    assert (reconstruido['cantidad'] == original['Quantity'].astype(int)).all()
    assert reconstruido['cliente_id'].isna().equals(original['Customer ID'].isna())


def test_operacional_conserva_la_suciedad_del_origen(con_operacional):
    assert db.escalar(con_operacional, "SELECT COUNT(*) FROM facturas WHERE factura_id LIKE 'C%'") > 0
    assert db.escalar(con_operacional, 'SELECT COUNT(*) FROM facturas WHERE cliente_id IS NULL') > 0
    assert db.escalar(con_operacional, 'SELECT COUNT(*) FROM lineas_factura WHERE descripcion IS NULL') > 0


# --------------------------------------------------------------------------------------------------- RAW
def test_raw_copia_cada_tabla_del_operacional_tal_cual(con, ruta_operacional):
    con.execute('ATTACH DATABASE ? AS retail', (str(ruta_operacional),))
    try:
        for tabla in TABLAS_OPERACIONALES:
            origen = pd.read_sql(f'SELECT * FROM retail.{tabla} ORDER BY rowid', con)
            copia = pd.read_sql(f'SELECT * FROM raw_{tabla} ORDER BY rowid', con).drop(columns='_carga_id')
            pd.testing.assert_frame_equal(origen, copia, obj=tabla)
    finally:
        con.execute('DETACH DATABASE retail')


def test_raw_registra_cada_carga_con_su_huella(con):
    cargas = pd.read_sql('SELECT * FROM raw_carga', con)
    assert list(cargas['tabla']) == TABLAS_OPERACIONALES and (cargas['origen'] == 'retail').all()
    for c in cargas.itertuples():
        n = db.escalar(con, f'SELECT COUNT(*) FROM raw_{c.tabla} WHERE _carga_id = ?', (c.carga_id,))
        assert n == c.filas > 0
        assert len(c.sha256) == 64


def test_raw_la_huella_identifica_el_contenido(con, ruta_operacional):
    """Misma tabla de origen -> misma huella; la huella de raw_carga es la del operacional."""
    con.execute('ATTACH DATABASE ? AS retail', (str(ruta_operacional),))
    try:
        sha = db.escalar(con, "SELECT sha256 FROM raw_carga WHERE tabla = 'lineas_factura'")
        assert huella_tabla(con, 'retail.lineas_factura') == (db.escalar(con, 'SELECT COUNT(*) FROM raw_lineas_factura'), sha)
    finally:
        con.execute('DETACH DATABASE retail')


def test_raw_tiene_linaje(con):
    nulos = db.escalar(con, 'SELECT COUNT(*) FROM raw_lineas_factura WHERE linea_id IS NULL OR _carga_id IS NULL')
    assert nulos == 0


def test_raw_no_limpia_nada_las_facturas_canceladas_siguen_con_su_c(con):
    assert db.escalar(con, "SELECT COUNT(*) FROM raw_facturas WHERE factura_id LIKE 'C%'") > 0


# --------------------------------------------------------------------------------------------------- MASTER
def test_master_concilia_con_raw(con):
    raw = db.escalar(con, 'SELECT COUNT(*) FROM raw_lineas_factura')
    master = db.escalar(con, 'SELECT COUNT(*) FROM master_lineas')
    descartes = db.escalar(con, 'SELECT COUNT(*) FROM master_descartes')
    assert raw == master + descartes


def test_master_no_tiene_reglas_de_calidad_en_error(con):
    estados = dict(con.execute('SELECT regla, estado FROM master_calidad').fetchall())
    assert len(estados) >= 10
    assert 'ERROR' not in estados.values(), estados


def test_master_respeta_las_claves_foraneas(con):
    assert con.execute('PRAGMA foreign_key_check').fetchall() == []


def test_master_cada_factura_tiene_lineas(con):
    assert db.escalar(con, 'SELECT COUNT(*) FROM master_facturas f WHERE NOT EXISTS '
                           '(SELECT 1 FROM master_lineas l WHERE l.factura_id = f.factura_id)') == 0


def test_master_marca_bien_las_ventas_validas(con):
    malas = db.escalar(con, '''
        SELECT COUNT(*) FROM master_lineas l
        JOIN master_facturas f ON f.factura_id = l.factura_id
        JOIN master_productos p ON p.codigo_producto = l.codigo_producto
        WHERE l.es_venta_valida = 1
          AND (l.cantidad <= 0 OR l.precio_unitario <= 0 OR f.es_cancelacion = 1 OR p.es_producto = 0)''')
    assert malas == 0


def test_master_las_cancelaciones_se_detectan_por_el_prefijo_c(con):
    assert db.escalar(con, "SELECT COUNT(*) FROM master_facturas WHERE (factura_id LIKE 'C%') <> (es_cancelacion = 1)") == 0


def test_master_los_codigos_que_no_son_producto_no_cuentan_como_venta(con):
    n = db.escalar(con, "SELECT COUNT(*) FROM master_productos WHERE es_producto = 0")
    assert n > 0   # la muestra incluye envios, comisiones u otros codigos que no son productos


def test_master_los_clientes_tienen_pais_y_fechas(con):
    assert db.escalar(con, 'SELECT COUNT(*) FROM master_clientes WHERE pais IS NULL OR primer_movimiento > ultimo_movimiento') == 0


def test_master_los_descartes_tienen_motivo_conocido(con):
    motivos = {m for (m,) in con.execute('SELECT DISTINCT motivo FROM master_descartes')}
    assert motivos <= {'duplicado_exacto', 'dato_obligatorio_nulo'}
