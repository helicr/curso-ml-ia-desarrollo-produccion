"""Pruebas de los modos de inferencia bajo demanda (variables leídas de fs_produccion) y online (calculadas al vuelo), sin red.

Paridad (mismo corte -> misma probabilidad y mismas variables), frescura (una compra de demo solo la ve el online), ausencia de fuga
(una compra posterior al corte pedido no entra) y modo demo apagado por defecto.
"""
import shutil
import sqlite3
import statistics
import time

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from ia_mlops import config, db, explotacion as ex
from ia_mlops.interfaz.app import crear_app

ESQUEMA_FS_PRODUCCION = f'''CREATE TABLE fs_produccion (
    cliente_id INTEGER NOT NULL, fecha_corte TEXT NOT NULL,
    {", ".join(f"{c} REAL" for c in config.FEATURES)},
    huella_modelo TEXT, version_modelo INTEGER, creado_en TEXT, PRIMARY KEY (cliente_id, fecha_corte))'''


@pytest.fixture(scope='module')
def base(ruta_db, tmp_path_factory):
    """Copia de la base de pruebas con una fs_produccion (esquema fijado) rellenada con las variables del corte «de hoy»."""
    ruta = tmp_path_factory.mktemp('modos') / 'curso.db'
    shutil.copyfile(ruta_db, ruta)
    con = db.conectar(ruta, solo_lectura=False)
    corte = ex.corte_por_defecto(con)
    df = ex.variables_en_corte(con, corte)
    con.execute('DROP TABLE IF EXISTS fs_produccion')      # otras pruebas del lote pueden haberla creado ya en la base de sesión
    con.execute(ESQUEMA_FS_PRODUCCION)
    df.assign(fecha_corte=corte, huella_modelo='h-prueba', version_modelo=3, creado_en='2011-12-10T00:00:00')[
        ['cliente_id', 'fecha_corte', *config.FEATURES, 'huella_modelo', 'version_modelo', 'creado_en']
    ].to_sql('fs_produccion', con, if_exists='append', index=False)
    con.commit()
    con.close()
    return ruta, corte


@pytest.fixture()
def demo(base, carpeta_modelo):
    ruta, _ = base
    return TestClient(crear_app(ruta_db=ruta, carpeta_modelo=carpeta_modelo, url_api='', demo=True))


@pytest.fixture()
def sin_demo(base, carpeta_modelo):
    ruta, _ = base
    return TestClient(crear_app(ruta_db=ruta, carpeta_modelo=carpeta_modelo, url_api='', demo=False))


def un_cliente(base, que='LIMIT 1 OFFSET 7'):
    con = sqlite3.connect(base[0])
    try:
        return con.execute(f'SELECT cliente_id FROM fs_produccion ORDER BY cliente_id {que}').fetchone()[0]
    finally:
        con.close()


def test_paridad_bajo_demanda_y_online_en_el_mismo_corte(sin_demo, base):
    ruta, corte = base
    ids = [un_cliente(base, f'LIMIT 1 OFFSET {n}') for n in (0, 7, 30, 90)]
    for i in ids:
        a, o = sin_demo.get(f'/bajo-demanda/{i}').json(), sin_demo.get(f'/online/{i}', params={'corte': corte}).json()
        assert a['corte'] == o['corte'] == corte
        assert a['probabilidad'] == pytest.approx(o['probabilidad'], abs=1e-9)
        for k in config.FEATURES:
            assert a['variables'][k] == pytest.approx(o['variables'][k]) if o['variables'][k] is not None else a['variables'][k] is None
        assert (a['segmento'], a['recomendacion']) == (o['segmento'], o['recomendacion'])
        assert a['modo'] == 'bajo_demanda' and o['modo'] == 'online' and a['ms'] > 0 and o['ms'] > 0
    # sin compras de demo, «ahora» es el corte del lote: online sin ?corte= da lo mismo
    i = ids[1]
    assert sin_demo.get(f'/online/{i}').json()['probabilidad'] == pytest.approx(sin_demo.get(f'/bajo-demanda/{i}').json()['probabilidad'], abs=1e-9)


def test_el_lote_devuelve_lo_mismo_que_los_individuales_y_avisa_de_los_que_faltan(sin_demo, base):
    ids = [un_cliente(base), un_cliente(base, 'LIMIT 1 OFFSET 20'), 99999999]
    r = sin_demo.post('/bajo-demanda', json={'cliente_ids': ids}).json()
    assert r['pedidos'] == 3 and r['encontrados'] == 2 and r['no_encontrados'][0]['cliente_id'] == 99999999
    for x in r['resultados']:
        assert x['probabilidad'] == pytest.approx(sin_demo.get(f'/bajo-demanda/{x["cliente_id"]}').json()['probabilidad'], abs=1e-12)
        assert x['version_modelo_del_lote'] == 3 and x['huella_modelo_del_lote'] == 'h-prueba'


def test_errores_claros(sin_demo, base, carpeta_modelo, ruta_db):
    assert sin_demo.get('/bajo-demanda/99999999').status_code == 404
    assert 'fs_produccion' in sin_demo.get('/bajo-demanda/99999999').json()['detalle']
    assert sin_demo.get('/online/99999999').status_code == 404
    assert sin_demo.get(f'/online/{un_cliente(base)}', params={'corte': '2011-02-30'}).status_code == 422
    assert sin_demo.get(f'/online/{un_cliente(base)}', params={'corte': '2030-01-01'}).status_code == 422
    assert sin_demo.post('/bajo-demanda', json={'cliente_ids': []}).status_code == 422
    # sin la tabla fs_produccion: 503 con el motivo; online sigue funcionando
    sin_tabla = TestClient(crear_app(ruta_db=ruta_db, carpeta_modelo=carpeta_modelo, url_api='', demo=False))
    r = sin_tabla.get('/bajo-demanda/1')
    assert r.status_code == 503 and 'fs_produccion' in r.json()['detalle']
    assert sin_tabla.get(f'/online/{un_cliente(base)}').status_code == 200


def test_frescura_una_compra_de_demo_solo_la_ve_el_online(demo, base):
    i = un_cliente(base)
    antes_o, antes_b = demo.get(f'/online/{i}').json(), demo.get(f'/bajo-demanda/{i}').json()
    assert antes_o['probabilidad'] == pytest.approx(antes_b['probabilidad'], abs=1e-9)
    r = demo.post('/demo/compra', json={'cliente_id': i, 'importe': 80.0, 'unidades': 4})
    assert r.status_code == 200 and r.json()['compras_demo_del_cliente'] == 1
    o, b = demo.get(f'/online/{i}').json(), demo.get(f'/bajo-demanda/{i}').json()
    assert o['corte'] == antes_o['corte']                          # «ahora» no se mueve: la compra es del último día con datos
    assert o['variables']['recencia_dias'] == 0
    assert o['variables']['frecuencia'] == antes_o['variables']['frecuencia'] + 1
    assert o['variables']['unidades_total'] == antes_o['variables']['unidades_total'] + 4
    assert o['variables']['monto_total'] == pytest.approx(antes_o['variables']['monto_total'] + 80.0)
    assert o['variables']['frecuencia_90d'] == antes_o['variables']['frecuencia_90d'] + 1
    assert o['probabilidad'] != antes_o['probabilidad']
    assert b['variables'] == antes_b['variables'] and b['probabilidad'] == antes_b['probabilidad']
    # otro cliente no cambia; reiniciar devuelve el online al estado inicial
    otro = un_cliente(base, 'LIMIT 1 OFFSET 40')
    assert demo.get(f'/online/{otro}').json()['variables'] == sin_compras(demo, otro)
    assert demo.post('/demo/reiniciar').json()['compras_borradas'] == 1
    assert demo.get(f'/online/{i}').json()['variables'] == antes_o['variables']


def sin_compras(demo, i):
    return demo.get(f'/bajo-demanda/{i}').json()['variables']


def test_sin_fuga_una_compra_posterior_al_corte_no_entra(demo, base):
    i = un_cliente(base)
    corte = '2011-09-01'
    base_o = demo.get(f'/online/{i}', params={'corte': corte}).json()
    ruta_copia = demo.app.state.consulta.ruta_db
    con = sqlite3.connect(ruta_copia)
    con.execute("INSERT INTO demo_compras (cliente_id, fecha, importe, unidades, producto, pais) VALUES (?, '2011-09-15 10:00:00', 500, 9, 'DEMO', 'United Kingdom')", [i])
    con.execute("INSERT INTO demo_compras (cliente_id, fecha, importe, unidades, producto, pais) VALUES (?, '2011-08-31 23:59:59', 10, 1, 'DEMO', 'United Kingdom')", [i])
    con.commit()
    con.close()
    o = demo.get(f'/online/{i}', params={'corte': corte}).json()
    assert o['variables']['frecuencia'] == base_o['variables']['frecuencia'] + 1          # entra la del 31-08, no la del 15-09
    assert o['variables']['unidades_total'] == base_o['variables']['unidades_total'] + 1
    assert o['variables']['monto_total'] == pytest.approx(base_o['variables']['monto_total'] + 10.0)
    # y «ahora» sí las ve (la del 15-09 es anterior al día siguiente al último evento)
    assert demo.get('/modos').json()['ahora'] >= '2011-12-10'


def test_la_compra_de_demo_equivale_a_insertarla_en_master(demo, base, ruta_db, tmp_path):
    """Las variables online con la compra de demo son las que daría el lote si la compra estuviera en MASTER."""
    i = un_cliente(base)
    demo.post('/demo/compra', json={'cliente_id': i, 'importe': 33.0, 'unidades': 2, 'producto': 'demo'})
    o = demo.get(f'/online/{i}').json()
    copia = tmp_path / 'm.db'
    shutil.copyfile(ruta_db, copia)
    con = db.conectar(copia, solo_lectura=False)
    corte = ex.corte_por_defecto(con)
    dia = db.escalar(con, 'SELECT date(MAX(fecha_factura)) FROM master_facturas')
    pais = db.escalar(con, 'SELECT pais FROM master_clientes WHERE cliente_id = ?', [i])
    con.execute("INSERT OR IGNORE INTO master_productos VALUES ('DEMO', 'demo', 1)")
    con.execute('INSERT INTO master_facturas VALUES (?, ?, ?, ?, 0)', ['XDEMO1', i, f'{dia} 23:59:59', pais])
    con.execute("INSERT INTO master_lineas VALUES (-1, 'XDEMO1', 'DEMO', 2, 16.5, 33.0, 1)")
    con.commit()
    esperado = ex.variables_en_corte(con, corte).set_index('cliente_id').loc[i]
    con.close()
    for k in config.FEATURES:
        assert o['variables'][k] == pytest.approx(None if pd.isna(esperado[k]) else float(esperado[k])) if not pd.isna(esperado[k]) else o['variables'][k] is None


def test_modo_demo_apagado_por_defecto(sin_demo, base, monkeypatch, carpeta_modelo):
    i = un_cliente(base)
    assert sin_demo.get('/modos').json()['demo'] is False
    assert sin_demo.post('/demo/compra', json={'cliente_id': i, 'importe': 5}).status_code == 404
    assert sin_demo.post('/demo/reiniciar').status_code == 404
    monkeypatch.delenv('CURSO_DEMO', raising=False)
    assert crear_app(ruta_db=base[0], carpeta_modelo=carpeta_modelo, url_api='').state.modos.demo is False


def test_el_modo_demo_trabaja_sobre_una_copia_y_no_toca_la_original(base, carpeta_modelo):
    import hashlib
    ruta, _ = base
    huella = hashlib.sha256(ruta.read_bytes()).hexdigest()
    c = TestClient(crear_app(ruta_db=ruta, carpeta_modelo=carpeta_modelo, url_api='', demo=True))
    assert c.app.state.consulta.ruta_db != ruta
    c.post('/demo/compra', json={'cliente_id': un_cliente(base), 'importe': 9})
    assert hashlib.sha256(ruta.read_bytes()).hexdigest() == huella
    assert c.post('/demo/compra', json={'cliente_id': 99999999, 'importe': 9}).status_code == 404
    assert c.post('/demo/compra', json={'cliente_id': 1, 'importe': -1}).status_code == 422


def test_latencias_en_local(demo, base, capsys):
    """Mide p50/p95 de 50 peticiones con TestClient (en local, sin red real): solo se anotan, el techo es holgado."""
    i = un_cliente(base)
    demo.get(f'/bajo-demanda/{i}'), demo.get(f'/online/{i}')       # calienta: carga el modelo
    salida = {}
    for nombre, ruta in (('bajo-demanda', f'/bajo-demanda/{i}'), ('online', f'/online/{i}')):
        t = []
        for _ in range(50):
            t0 = time.perf_counter()
            assert demo.get(ruta).status_code == 200
            t.append((time.perf_counter() - t0) * 1000)
        t.sort()
        salida[nombre] = (statistics.median(t), t[int(0.95 * len(t)) - 1])
        assert salida[nombre][1] < 2000
    with capsys.disabled():
        print('\nLATENCIA (TestClient, local, 50 peticiones, base de muestra): ' +
              ' · '.join(f'{k}: p50 {a:.1f} ms, p95 {b:.1f} ms' for k, (a, b) in salida.items()))
