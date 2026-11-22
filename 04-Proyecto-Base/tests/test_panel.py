"""Pruebas del panel de producción (GET /panel y /panel/*), sin red."""
import json

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from ia_mlops import config, produccion
from ia_mlops.interfaz import panel
from ia_mlops.interfaz.app import crear_app


@pytest.fixture()
def cliente(ruta_db, carpeta_modelo, tmp_path, monkeypatch):
    monkeypatch.setenv('CURSO_CAMPANA', str(tmp_path / 'no_hay'))
    return TestClient(crear_app(ruta_db=ruta_db, carpeta_modelo=carpeta_modelo, url_api='', demo=False))


@pytest.fixture()
def cliente_demo(ruta_db, carpeta_modelo, tmp_path, monkeypatch):
    monkeypatch.setenv('CURSO_CAMPANA', str(tmp_path / 'no_hay'))
    return TestClient(crear_app(ruta_db=ruta_db, carpeta_modelo=carpeta_modelo, url_api='', demo=True))


def escribir_campana(carpeta, corte='2011-12-10', n=30):
    carpeta.mkdir(parents=True, exist_ok=True)
    tabla = pd.DataFrame({'puesto': range(1, n + 1), 'cliente_id': range(1000, 1000 + n), 'probabilidad': [1 - i / (n + 1) for i in range(n)],
                          'n_advertencias': [0] * n, 'advertencias': [''] * n, 'decil': [i * 10 // n + 1 for i in range(n)],
                          'en_campana': [i < 3 for i in range(n)]})
    tabla.to_csv(carpeta / f'campana_{corte}.csv', index=False)
    resumen = {'corte': corte, 'clientes_puntuados': n, 'clientes_en_campana': 3, 'probabilidad_media': 0.5, 'modelo': 'regresion_logistica',
               'huella_datos': 'abc123', 'referencia': {'version': 1, 'etiqueta_imagen': 'retencion-api:v1-abc', 'huella_datos': 'abc123'},
               'archivos': ['ruta/personal/campana.csv']}
    (carpeta / f'campana_{corte}.json').write_text(json.dumps(resumen), encoding='utf-8')


def test_pagina_con_las_cuatro_pestanas(cliente):
    r = cliente.get('/panel')
    assert r.status_code == 200 and 'text/html' in r.headers['content-type']
    for nombre in ('Lote', 'Bajo demanda', 'Online', 'Versiones'):
        assert f'>{nombre}</button>' in r.text
    assert 'GitHub Actions' in r.text and 'Simular una compra nueva' in r.text and 'Reiniciar demo' in r.text
    assert 'http://' not in r.text.replace('http://127', '') and 'https://' not in r.text      # sin recursos externos


def test_las_rutas_anteriores_siguen(cliente):
    assert cliente.get('/').status_code == 200
    assert cliente.get('/salud').json() == {'estado': 'ok'}


def test_lote_sin_campana(cliente):
    d = cliente.get('/panel/lote').json()
    assert d['disponible'] is False and 'ejecuta el lote' in d['mensaje']
    assert cliente.get('/panel/lote.csv').status_code == 404
    assert cliente.get('/panel/lote/cliente/1000').status_code == 404


def test_lote_con_campana(cliente, tmp_path, monkeypatch):
    carpeta = tmp_path / 'campana'
    escribir_campana(carpeta, '2011-11-01', 5)
    escribir_campana(carpeta, '2011-12-10', 30)           # la más reciente por el corte del nombre
    monkeypatch.setenv('CURSO_CAMPANA', str(carpeta))
    d = cliente.get('/panel/lote').json()
    assert d['disponible'] and d['archivo'] == 'campana_2011-12-10.csv' and d['filas'] == 30
    assert len(d['primeros']) == 20 and d['primeros'][0]['cliente_id'] == 1000
    assert d['resumen']['corte'] == '2011-12-10' and d['resumen']['huella_datos'] == 'abc123'
    assert 'archivos' not in d['resumen']                  # sin rutas de quien lo ejecutó
    csv = cliente.get('/panel/lote.csv')
    assert csv.status_code == 200 and csv.text.startswith('puesto,cliente_id,probabilidad')
    c = cliente.get('/panel/lote/cliente/1003').json()
    assert c['cliente_id'] == 1003 and c['corte'] == '2011-12-10'
    assert cliente.get('/panel/lote/cliente/5').status_code == 404


def test_lote_apuntando_a_un_archivo(cliente, tmp_path, monkeypatch):
    escribir_campana(tmp_path / 'c', '2011-10-01', 8)
    monkeypatch.setenv('CURSO_CAMPANA', str(tmp_path / 'c' / 'campana_2011-10-01.csv'))
    assert cliente.get('/panel/lote').json()['filas'] == 8


def test_versiones_con_la_referencia_real(cliente):
    ref = produccion.leer_referencia()
    d = cliente.get('/panel/versiones').json()
    assert d['produccion']['version'] == ref['version'] and d['produccion']['etiqueta_imagen'] == ref['etiqueta_imagen']
    assert d['produccion']['metricas_test']['auc'] == ref['metricas_test']['auc']
    assert d['sirviendo']['huella_datos'] and d['sirviendo']['entrenado_en']
    assert d['coinciden'] == (ref['huella_datos'] == d['sirviendo']['huella_datos'])
    assert (d['aviso'] is None) == d['coinciden']
    assert d['historial'] is None or isinstance(d['historial'], list)
    assert len(d['flujo_nueva_version']) == 5


def test_versiones_aviso_si_no_coinciden(cliente, tmp_path, monkeypatch):
    ref = json.loads(config.REFERENCIA.read_text(encoding='utf-8'))
    ref['huella_datos'] = 'abcdef0123456789'
    ref['etiqueta_imagen'] = produccion.etiqueta_imagen(ref['version'], ref['huella_datos'])
    otra = tmp_path / 'referencia.json'
    otra.write_text(json.dumps(ref), encoding='utf-8')
    monkeypatch.setattr(config, 'REFERENCIA', otra)
    d = cliente.get('/panel/versiones').json()
    assert d['coinciden'] is False and 'no es el de la versión en producción' in d['aviso']


def test_versiones_sin_referencia_ni_romper(cliente, tmp_path, monkeypatch):
    monkeypatch.setattr(config, 'REFERENCIA', tmp_path / 'no_existe.json')
    d = cliente.get('/panel/versiones').json()
    assert d['produccion'] is None and 'No existe' in d['error_produccion'] and d['sirviendo'] is not None


def test_historial_si_existe(cliente, tmp_path, monkeypatch):
    (tmp_path / panel.HISTORIAL).write_text(json.dumps({'versiones': [{'version': 1, 'auc': 0.74}]}), encoding='utf-8')
    monkeypatch.setattr(config, 'MODELOS', tmp_path)
    assert cliente.get('/panel/versiones').json()['historial'] == [{'version': 1, 'auc': 0.74}]


def test_boton_de_demo_solo_con_demo_activo(cliente, cliente_demo):
    # la página decide con /modos: sin demo, el JSON lo dice y el POST se rechaza
    assert cliente.get('/modos').json()['demo'] is False
    assert cliente.post('/demo/compra', json={'cliente_id': 1, 'importe': 5}).status_code in (400, 403, 404, 409, 422)
    assert cliente_demo.get('/modos').json()['demo'] is True
    # la página oculta el bloque salvo que /modos diga demo=true
    assert "hidden = !MODOS.demo" in cliente.get('/panel').text and 'id="o-demo" hidden' in cliente.get('/panel').text
