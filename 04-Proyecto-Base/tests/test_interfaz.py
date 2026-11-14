"""Pruebas de la interfaz de consulta (ia_mlops/interfaz): ids de cliente -> variables de FS -> modelo -> recomendación."""
import re

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from ia_mlops import config, explotacion as ex
from ia_mlops.interfaz import consulta as cq, pagina
from ia_mlops.interfaz.app import crear_app


@pytest.fixture()
def cliente(ruta_db, carpeta_modelo):
    return TestClient(crear_app(ruta_db=ruta_db, carpeta_modelo=carpeta_modelo, url_api=''))


def test_la_pagina_carga_y_no_usa_recursos_externos(cliente):
    r = cliente.get('/')
    assert r.status_code == 200 and 'text/html' in r.headers['content-type']
    assert not re.search(r'<(script|link|img|iframe)\b[^>]*\b(src|href)="https?://', pagina.HTML)
    assert 'fetch(' in pagina.HTML and "pedir('recomendar'" in pagina.HTML


def test_el_estado_da_el_corte_el_modelo_y_ejemplos_de_todos_los_tramos(cliente, con):
    e = cliente.get('/estado').json()
    assert e['corte_por_defecto'] == ex.corte_por_defecto(con) and e['primer_corte'] < e['corte_por_defecto']
    assert e['origen'].startswith('modelo local') and e['huella_datos'] and e['segmentos'] == config.SEGMENTOS_RECOMPRA
    tramos = {x['segmento'] for x in cliente.post('/recomendar', json={'cliente_ids': e['ejemplos']}).json()['resultados']}
    assert len(e['ejemplos']) == 5 and tramos == {s['segmento'] for s in config.SEGMENTOS_RECOMPRA}


def test_la_probabilidad_es_la_de_la_explotacion_y_la_recomendacion_sigue_la_regla(cliente, con, carpeta_modelo):
    tabla, _ = ex.campana(con, carpeta_modelo=carpeta_modelo, guardar=False)
    ids = tabla['cliente_id'].iloc[[0, 5, 40, -1]].tolist()
    r = cliente.post('/recomendar', json={'cliente_ids': ids}).json()
    assert r['encontrados'] == r['pedidos'] == 4 and r['clientes_en_el_corte'] == len(tabla)
    por_id = tabla.set_index('cliente_id')
    for x in r['resultados']:
        fila = por_id.loc[x['cliente_id']]
        assert x['probabilidad'] == round(float(fila['probabilidad']), 4)
        assert x['puesto'] == int(fila['puesto']) and x['decil'] == int(fila['decil'])
        s = cq.segmento_de(x['probabilidad'])
        assert (x['segmento'], x['recomendacion']) == (s['segmento'], s['recomendacion'])
        assert x['revisar'] == bool(x['advertencias']) and list(x['variables']) == config.FEATURES
    assert [x['puesto'] for x in r['resultados']] == sorted(x['puesto'] for x in r['resultados'])   # de mayor a menor probabilidad
    assert sum(r['por_segmento'].values()) == 4


def test_las_variables_son_las_de_la_capa_fs_en_un_corte_que_ya_existe(cliente, con):
    fs = pd.read_sql("SELECT * FROM fs_cliente_corte WHERE fecha_corte = '2011-09-01' ORDER BY cliente_id LIMIT 3", con)
    r = cliente.post('/recomendar', json={'cliente_ids': fs['cliente_id'].tolist(), 'corte': '2011-09-01'}).json()
    por_id = {x['cliente_id']: x['variables'] for x in r['resultados']}
    for f in fs.to_dict(orient='records'):
        for k in config.FEATURES:
            esperado = None if pd.isna(f[k]) else f[k]
            assert por_id[f['cliente_id']][k] == pytest.approx(esperado) if esperado is not None else por_id[f['cliente_id']][k] is None


def test_ids_desconocidos_sin_historia_y_repetidos(cliente, con):
    conocido = con.execute('SELECT cliente_id FROM fs_cliente_corte LIMIT 1').fetchone()[0]
    tardio = con.execute("SELECT cliente_id FROM master_clientes WHERE primer_movimiento >= '2011-06-01' LIMIT 1").fetchone()[0]
    r = cliente.post('/recomendar', json={'cliente_ids': [conocido, conocido, 99999999, tardio], 'corte': '2011-03-01'}).json()
    assert r['pedidos'] == 3 and r['encontrados'] == 1
    motivos = {f['cliente_id']: f['motivo'] for f in r['no_encontrados']}
    assert motivos[99999999] == 'no existe en MASTER' and motivos[tardio].startswith('sin compras válidas antes del corte')


@pytest.mark.parametrize('cuerpo,trozo', [
    ({'cliente_ids': []}, 'at least 1'),
    ({'cliente_ids': [1], 'corte': '01/03/2011'}, 'AAAA-MM-DD'),
    ({'cliente_ids': [1], 'corte': '2011-02-30'}, 'no es una fecha'),
    ({'cliente_ids': [1], 'corte': '2030-01-01'}, 'debe estar entre'),
    ({'cliente_ids': [1], 'otro': 1}, 'Extra inputs'),
    ({'cliente_ids': list(range(1, 1002))}, 'at most 1000'),
])
def test_peticiones_sin_sentido_dan_422(cliente, cuerpo, trozo):
    r = cliente.post('/recomendar', json=cuerpo)
    assert r.status_code == 422 and trozo in r.text


def test_un_solo_cliente_por_get(cliente, con):
    conocido = con.execute("SELECT cliente_id FROM fs_cliente_corte WHERE fecha_corte = '2011-09-01' LIMIT 1").fetchone()[0]
    r = cliente.get(f'/recomendar/{conocido}', params={'corte': '2011-09-01'}).json()
    assert r['encontrados'] == 1 and r['resultados'][0]['cliente_id'] == conocido


def test_sin_modelo_o_sin_api_da_503(ruta_db, tmp_path):
    sin_modelo = TestClient(crear_app(ruta_db=ruta_db, carpeta_modelo=tmp_path / 'vacia', url_api=''))
    r = sin_modelo.post('/recomendar', json={'cliente_ids': [1]})
    assert r.status_code == 503 and 'python -m ia_mlops.pipeline' in r.json()['detalle']
    sin_api = TestClient(crear_app(ruta_db=ruta_db, url_api='http://127.0.0.1:9'))
    r = sin_api.post('/recomendar', json={'cliente_ids': [1]})
    assert r.status_code == 503 and '¿Está arrancada' in r.json()['detalle']


def test_la_regla_de_negocio(monkeypatch):
    assert [cq.segmento_de(p)['segmento'] for p in (0.99, 0.70, 0.69, 0.40, 0.39, 0.0)] == ['alta', 'alta', 'media', 'media', 'baja', 'baja']
    otra = [{'segmento': 'llamar', 'desde': 0.5, 'recomendacion': 'x'}, {'segmento': 'no', 'desde': 0.0, 'recomendacion': 'y'}]
    monkeypatch.setattr(config, 'SEGMENTOS_RECOMPRA', otra)
    assert cq.segmento_de(0.6)['segmento'] == 'llamar' and cq.segmento_de(0.1)['segmento'] == 'no'


def test_por_la_api_da_lo_mismo_que_en_local(ruta_db, carpeta_modelo, arrancar_servidor, cliente):
    puerto, _ = arrancar_servidor(carpeta_modelo)
    por_api = TestClient(crear_app(ruta_db=ruta_db, url_api=f'http://127.0.0.1:{puerto}'))
    ids = cliente.get('/estado').json()['ejemplos']
    a, b = por_api.post('/recomendar', json={'cliente_ids': ids}).json(), cliente.post('/recomendar', json={'cliente_ids': ids}).json()
    assert a['origen'] == f'http://127.0.0.1:{puerto}'
    assert [(x['cliente_id'], x['probabilidad'], x['segmento']) for x in a['resultados']] == \
           [(x['cliente_id'], x['probabilidad'], x['segmento']) for x in b['resultados']]


def test_salud_y_listo(cliente, ruta_db, tmp_path, monkeypatch):
    assert cliente.get('/salud').json() == {'estado': 'ok'}
    r = cliente.get('/listo')
    assert r.status_code == 200 and r.json()['datos'] == 'ok'
    # sin API: vivo (salud 200) pero no listo (503 con el motivo)
    sin_api = TestClient(crear_app(ruta_db=ruta_db, url_api='http://127.0.0.1:9'))
    assert sin_api.get('/salud').status_code == 200
    r = sin_api.get('/listo')
    assert r.status_code == 503 and 'no responde' in r.json()['detalle']
    # sin datos (el volumen no se montó): 503 que lo dice
    monkeypatch.setattr(config, 'DB_SOLO_LECTURA', True)          # como en la imagen
    r = TestClient(crear_app(ruta_db=tmp_path / 'no-existe.db', url_api='http://127.0.0.1:9')).get('/listo')
    assert r.status_code == 503 and 'volumen' in r.json()['detalle']
    assert not (tmp_path / 'no-existe.db').exists()             # en solo lectura no crea una base vacía


def test_con_la_base_en_solo_lectura_funciona_y_no_la_modifica(ruta_db, carpeta_modelo, tmp_path, monkeypatch):
    import hashlib
    import shutil
    import sqlite3
    copia = tmp_path / 'curso.db'
    shutil.copy(ruta_db, copia)
    huella = hashlib.sha256(copia.read_bytes()).hexdigest()
    monkeypatch.setattr(config, 'DB_SOLO_LECTURA', True)          # lo que hace CURSO_DB_SOLO_LECTURA=1 en la imagen
    c = TestClient(crear_app(ruta_db=copia, carpeta_modelo=carpeta_modelo, url_api=''))
    ids = c.get('/estado').json()['ejemplos']
    r = c.post('/recomendar', json={'cliente_ids': ids, 'corte': '2011-05-15'})      # corte nuevo: usa la tabla temporal
    assert r.status_code == 200 and r.json()['encontrados'] > 0
    from ia_mlops import db
    con = db.conectar(copia)
    with pytest.raises(sqlite3.OperationalError, match='readonly'):
        con.execute('CREATE TABLE intruso (x)')
    con.close()
    assert hashlib.sha256(copia.read_bytes()).hexdigest() == huella


def test_no_toca_la_capa_fs(cliente, con):
    antes = con.execute('SELECT COUNT(*), COUNT(DISTINCT fecha_corte) FROM fs_cliente_corte').fetchone()
    cliente.post('/recomendar', json={'cliente_ids': [1], 'corte': '2011-05-15'})
    assert con.execute('SELECT COUNT(*), COUNT(DISTINCT fecha_corte) FROM fs_cliente_corte').fetchone() == antes
