"""Pruebas de las capas RAW y MASTER."""
import pandas as pd

from ia_mlops import config, db


def test_raw_conserva_todas_las_filas_de_la_fuente(con):
    esperadas = len(pd.read_csv(config.FUENTES['muestra'], dtype=object))
    assert db.escalar(con, 'SELECT COUNT(*) FROM raw_online_retail_ii') == esperadas


def test_raw_registra_la_carga_con_su_huella(con):
    fuente, archivo, sha, filas = con.execute('SELECT fuente, archivo, sha256, filas FROM raw_carga').fetchone()
    assert fuente == 'muestra' and archivo.endswith('.csv') and len(sha) == 64 and filas > 0


def test_raw_tiene_linaje(con):
    nulos = db.escalar(con, 'SELECT COUNT(*) FROM raw_online_retail_ii WHERE _hoja IS NULL OR _fila IS NULL')
    assert nulos == 0


def test_raw_no_limpia_nada_las_facturas_canceladas_siguen_con_su_c(con):
    assert db.escalar(con, "SELECT COUNT(*) FROM raw_online_retail_ii WHERE Invoice LIKE 'C%'") > 0


def test_master_concilia_con_raw(con):
    raw = db.escalar(con, 'SELECT COUNT(*) FROM raw_online_retail_ii')
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
