"""Pestaña «Lote»: los endpoints /api/lote/* contra un Airflow FALSO (extra-composer-batch/pruebas/airflow_falso.py).

No arrancan los servidores MCP (sin `with TestClient`, la vida de la aplicación no se ejecuta) y no tocan el registro de MLflow.
Lo que prueban es la interfaz y el cliente; que un Airflow real acepte estas llamadas NO está probado.
"""
import socket
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app as modulo_app

pytestmark = pytest.mark.skipif(modulo_app.airflow_cli is None, reason='No está la carpeta extra-composer-batch')
UI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(modulo_app.LOTE_DIR / 'pruebas'))
from airflow_falso import crear_app  # noqa: E402


@contextmanager
def falso(**opciones):
    import uvicorn
    app = crear_app(**opciones)
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        puerto = s.getsockname()[1]
    srv = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=puerto, log_level='error'))
    hilo = threading.Thread(target=srv.run, daemon=True)
    hilo.start()
    while not srv.started:
        time.sleep(0.02)
    try:
        yield f'http://127.0.0.1:{puerto}', app
    finally:
        srv.should_exit = True
        hilo.join(timeout=5)


@pytest.fixture
def web(monkeypatch, tmp_path):
    for v in ('AIRFLOW_URL', 'AIRFLOW_AUTH', 'AIRFLOW_USUARIO', 'AIRFLOW_CLAVE', 'AIRFLOW_TOKEN', 'LOTE_IMAGEN_DEFECTO', 'AIRFLOW_API'):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv('CURSO_REPORTES', str(tmp_path / 'reports'))
    modulo_app.app.state.cliente_lote = None
    return TestClient(modulo_app.app)


def seguir(web, run_id, tope=40):
    for _ in range(tope):
        r = web.get(f'/api/lote/run/{run_id}').json()
        if r.get('final'):
            return r
    raise AssertionError('el run no terminó')


def test_config_no_filtra_secretos_ni_credenciales_de_la_url(web, monkeypatch):
    monkeypatch.setenv('AIRFLOW_URL', 'http://alguien:clave-en-la-url@localhost:8080/')
    monkeypatch.setenv('AIRFLOW_AUTH', 'basic')
    monkeypatch.setenv('AIRFLOW_USUARIO', 'airflow')
    monkeypatch.setenv('AIRFLOW_CLAVE', 'clave-secreta-123')
    monkeypatch.setenv('AIRFLOW_TOKEN', 'token-secreto-456')
    texto = web.get('/api/lote/config').text + web.get('/api/lote/estado').text
    for secreto in ('clave-secreta-123', 'token-secreto-456', 'clave-en-la-url'):
        assert secreto not in texto
    cfg = web.get('/api/lote/config').json()
    assert cfg['url'] == 'http://localhost:8080' and cfg['url_con_credenciales'] and cfg['credenciales'] == {'usuario': True, 'clave': True, 'token': True}
    e = web.get('/api/lote/estado').json()
    assert e['ok'] is False and 'usuario ni contraseña' in e['error']


def test_sin_airflow_lo_dice_claro_y_no_simula(web, monkeypatch):
    e = web.get('/api/lote/estado').json()
    assert e['ok'] is False and 'AIRFLOW_URL' in e['error'] and 'docker compose' in e['como_arrancarlo']
    monkeypatch.setenv('AIRFLOW_URL', 'http://127.0.0.1:9')
    e = web.get('/api/lote/estado').json()
    assert e['ok'] is False and 'No se pudo conectar' in e['error']
    r = web.post('/api/lote/lanzar', json={'confirmado': True, 'corte': '2011-12-10'})
    assert r.status_code in (400, 502) and 'run_id' not in r.json()
    h = web.get('/api/lote/historial')
    assert h.status_code == 200 and h.json()['runs'] == [] and h.json()['error']


@pytest.mark.parametrize('api', ['v1', 'v2'])
def test_lanzar_seguir_historial_y_log(web, monkeypatch, api):
    with falso(api=api) as (url, app):
        monkeypatch.setenv('AIRFLOW_URL', url)
        e = web.get('/api/lote/estado').json()
        assert e['ok'] and e['api'] == api and e['dag'] == 'retencion_lote' and not e['en_pausa']
        r = web.post('/api/lote/lanzar', json={'corte': '2011-12-10', 'imagen': 'retencion-lote:local', 'capacidad': 0.2, 'confirmado': True})
        assert r.status_code == 200, r.text
        run_id = r.json()['run_id']
        assert run_id.startswith('ui-') and '/dags/retencion_lote/' in r.json()['enlace']
        assert app.state.runs[run_id]['conf'] == {'corte': '2011-12-10', 'imagen': 'retencion-lote:local', 'capacidad': 0.2}
        vistos = []
        fin = seguir(web, run_id)
        assert fin['estado'] == 'success' and [t['tarea'] for t in fin['tareas']] == ['entradas', 'comprobar', 'ejecutar_lote', 'validar', 'resumir']
        assert all(t['estado'] == 'success' for t in fin['tareas'])
        h = web.get('/api/lote/historial').json()['runs']
        assert h[0]['run_id'] == run_id and h[0]['corte'] == '2011-12-10'
        log = web.get(f'/api/lote/log/{run_id}/resumir').json()
        assert 'servidor de prueba' in log['texto']


def test_run_fallido_se_ve_en_la_interfaz(web, monkeypatch):
    with falso() as (url, _):
        monkeypatch.setenv('AIRFLOW_URL', url)
        run_id = web.post('/api/lote/lanzar', json={'imagen': 'retencion-lote:falla', 'confirmado': True}).json()['run_id']
        fin = seguir(web, run_id)
        assert fin['estado'] == 'failed'
        estados = {t['tarea']: t['estado'] for t in fin['tareas']}
        assert estados['ejecutar_lote'] == 'failed' and estados['validar'] == 'upstream_failed'
        assert 'ImagePullBackOff' in web.get(f'/api/lote/log/{run_id}/ejecutar_lote').json()['texto']


def test_exige_confirmacion_y_valida_entradas(web, monkeypatch):
    with falso() as (url, app):
        monkeypatch.setenv('AIRFLOW_URL', url)
        assert web.post('/api/lote/lanzar', json={'corte': '2011-12-10'}).status_code == 400
        assert web.post('/api/lote/lanzar', json={'corte': '10/12/2011', 'confirmado': True}).status_code == 422
        assert web.post('/api/lote/lanzar', json={'imagen': 'x; rm -rf /', 'confirmado': True}).status_code == 422
        assert web.post('/api/lote/lanzar', json={'capacidad': 5, 'confirmado': True}).status_code == 422
        assert not app.state.runs, 'no debió lanzarse nada'


def test_dag_en_pausa_no_lanza(web, monkeypatch):
    with falso(pausado=True) as (url, app):
        monkeypatch.setenv('AIRFLOW_URL', url)
        assert web.get('/api/lote/estado').json()['en_pausa'] is True
        r = web.post('/api/lote/lanzar', json={'confirmado': True})
        assert r.status_code == 400 and 'unpause' in r.json()['error'] and not app.state.runs


def test_ids_de_run_y_tarea_no_validos(web, monkeypatch):
    assert web.get('/api/lote/run/a b').status_code in (404, 422)
    assert web.get('/api/lote/log/ok/..%2Fx').status_code in (404, 422)
    assert web.get('/api/lote/log/ok/tarea;ls').status_code == 422


def test_autenticacion_basica_v2_y_clave_mala(web, monkeypatch):
    with falso(api='v2', auth='bearer') as (url, _):
        monkeypatch.setenv('AIRFLOW_URL', url)
        monkeypatch.setenv('AIRFLOW_AUTH', 'basic')
        monkeypatch.setenv('AIRFLOW_USUARIO', 'airflow')
        monkeypatch.setenv('AIRFLOW_CLAVE', 'airflow')
        r = web.get('/api/lote/estado')
        assert r.json()['ok'] and r.json()['api'] == 'v2'
        monkeypatch.setenv('AIRFLOW_CLAVE', 'mala')
        e = web.get('/api/lote/estado').json()
        assert e['ok'] is False and '401' in e['error']


def test_resultado_lee_reports_campana(web, tmp_path):
    assert web.get('/api/lote/resultado').json()['disponible'] is False
    carpeta = tmp_path / 'reports' / 'campana'
    carpeta.mkdir(parents=True)
    (carpeta / 'campana_2011-12-10.json').write_text('{"corte":"2011-12-10","generado_en":"2026-11-27T10:00:00","clientes_puntuados":3,"clientes_en_campana":1,"capacidad":0.3,'
                                                      '"probabilidad_media":0.5,"modelo":"m","huella_datos":"abc","origen":"x"}', encoding='utf-8')
    (carpeta / 'campana_2011-12-10.csv').write_text('puesto,cliente_id,probabilidad,n_advertencias,advertencias,decil,en_campana\n1,1,0.9,0,,1,True\n2,2,0.5,0,,5,False\n3,3,0.1,0,,9,False\n', encoding='utf-8')
    r = web.get('/api/lote/resultado').json()
    assert r['disponible'] and r['clientes'] == 3 and r['tramos'] == {'alta': 1, 'media': 1, 'baja': 1} and r['corte'] == '2011-12-10'


def test_la_pestana_esta_en_la_pagina_y_el_js_no_usa_dialogos_nativos():
    html = (UI / 'estatico' / 'index.html').read_text(encoding='utf-8')
    assert 'id="t-lote"' in html and 'id="p-lote"' in html
    js = (UI / 'estatico' / 'app.js').read_text(encoding='utf-8')
    assert "'lote'" in js and 'Lanzar el lote' in js and 'dialogo({' in js and 'Esto no hace' in js
