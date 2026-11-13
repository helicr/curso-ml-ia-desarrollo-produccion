"""Pruebas de la explotación por lotes (ia_mlops/explotacion.py): variables del corte de hoy, campaña y trazabilidad."""
import json
import math

import pandas as pd
import pytest

from ia_mlops import config, explotacion as ex


def test_el_corte_por_defecto_es_el_dia_siguiente_a_la_ultima_factura(con):
    ultima = con.execute('SELECT MAX(fecha_factura) FROM master_facturas').fetchone()[0]
    assert ex.corte_por_defecto(con) == str(pd.Timestamp(ultima[:10]) + pd.Timedelta(days=1))[:10]


def test_las_variables_del_corte_salen_del_mismo_sql_de_fs_y_no_tocan_la_capa(con):
    antes = con.execute('SELECT COUNT(*), COUNT(DISTINCT fecha_corte) FROM fs_cliente_corte').fetchone()
    # con un corte que ya existe en FS, el resultado debe ser idéntico al de la capa
    df = ex.variables_en_corte(con, '2011-09-01')
    fs = pd.read_sql("SELECT * FROM fs_cliente_corte WHERE fecha_corte = '2011-09-01' ORDER BY cliente_id", con)
    pd.testing.assert_frame_equal(df[config.FEATURES].reset_index(drop=True), fs[config.FEATURES].reset_index(drop=True))
    # y la capa FS sigue igual, sin la tabla temporal
    assert con.execute('SELECT COUNT(*), COUNT(DISTINCT fecha_corte) FROM fs_cliente_corte').fetchone() == antes
    assert not con.execute("SELECT COUNT(*) FROM sqlite_temp_master WHERE name = 'fs_cliente_corte'").fetchone()[0]


def test_la_campana_ordena_reparte_en_deciles_y_guarda_la_trazabilidad(con, carpeta_modelo, salidas_tmp):
    tabla, r = ex.campana(con, carpeta_modelo=carpeta_modelo, capacidad=0.10)
    n = len(tabla)
    assert n == r['clientes_puntuados'] > 0
    assert tabla['probabilidad'].is_monotonic_decreasing and tabla['puesto'].tolist() == list(range(1, n + 1))
    assert sorted(tabla['decil'].unique()) == list(range(1, 11)) and tabla['decil'].is_monotonic_increasing
    assert tabla['en_campana'].sum() == r['clientes_en_campana'] == math.ceil(0.10 * n)
    assert r['probabilidad_minima_en_campana'] == round(tabla.loc[tabla['en_campana'], 'probabilidad'].min(), 4)
    assert r['corte'] == ex.corte_por_defecto(con) and r['huella_datos'] and r['modelo']
    guardado = json.loads((salidas_tmp / 'reports' / 'campana' / f'campana_{r["corte"]}.json').read_text(encoding='utf-8'))
    assert guardado['clientes_en_campana'] == r['clientes_en_campana']
    assert len(pd.read_csv(salidas_tmp / 'reports' / 'campana' / f'campana_{r["corte"]}.csv')) == n


def test_por_la_api_da_exactamente_lo_mismo_que_en_local(con, carpeta_modelo, arrancar_servidor, salidas_tmp):
    puerto, _ = arrancar_servidor(carpeta_modelo)
    local, _ = ex.campana(con, carpeta_modelo=carpeta_modelo, guardar=False)
    api, r = ex.campana(con, url=f'http://127.0.0.1:{puerto}', guardar=False)
    assert r['origen'].startswith('http://127.0.0.1')
    pd.testing.assert_series_equal(local['cliente_id'], api['cliente_id'])
    assert (local['probabilidad'] - api['probabilidad']).abs().max() < 1e-12
    assert (local['n_advertencias'] == api['n_advertencias']).all()


def test_comparar_dos_campanas(tmp_path):
    actual = pd.DataFrame({'cliente_id': [1, 2, 3, 4], 'en_campana': [True, True, False, False]})
    otra = tmp_path / 'otra.csv'
    pd.DataFrame({'cliente_id': [2, 3, 4, 1], 'en_campana': [True, True, False, False]}).to_csv(otra, index=False)
    assert ex.comparar_campanas(actual, otra) == {'en_ambas': 1, 'solo_ahora': 1, 'solo_antes': 1}


def test_sin_modelo_lo_dice(con, tmp_path):
    from ia_mlops.api.servicio import ModeloNoDisponible
    with pytest.raises(ModeloNoDisponible):
        ex.campana(con, carpeta_modelo=tmp_path / 'vacia', guardar=False)
