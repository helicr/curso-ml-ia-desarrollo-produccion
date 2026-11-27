"""El cliente REST (lanzar_lote.py) contra el Airflow FALSO. Prueba el cliente, no Airflow: un Airflow real no se ha usado."""
import json

import pytest

import lanzar_lote as ll


def lanzar(url, *extra, entorno=None, monkeypatch=None):
    return ll.main(['--url', url, '--intervalo', '0', '--espera', '30', *extra])


@pytest.mark.parametrize('api', ['v1', 'v2'])
def test_lanza_y_espera_hasta_success(falso, api, capsys, tmp_path):
    with falso(api=api) as (url, app):
        salida = tmp_path / 'r.json'
        resumen = tmp_path / 'resumen.md'
        codigo = lanzar(url, '--corte', '2011-12-10', '--imagen', 'retencion-lote:local', '--salida-json', str(salida), '--resumen-md', str(resumen))
        texto = capsys.readouterr().out
        assert codigo == ll.OK, texto
        assert f'API {api}' in texto and 'success' in texto
        run = next(iter(app.state.runs.values()))
        assert run['conf'] == {'corte': '2011-12-10', 'imagen': 'retencion-lote:local', 'capacidad': 0.1}
        assert json.loads(salida.read_text(encoding='utf-8'))['estado'] == 'success'
        assert '| resumir | success' in resumen.read_text(encoding='utf-8')
        if api == 'v2':
            assert ('POST', '/api/v2/dags/retencion_lote/dagRuns') in app.state.llamadas


def test_falla_si_el_dag_falla_y_muestra_el_registro(falso, capsys):
    with falso() as (url, app):
        codigo = lanzar(url, '--imagen', 'retencion-lote:falla')
        texto = capsys.readouterr().out
        assert codigo == ll.FALLO
        assert 'ejecutar_lote' in texto and 'failed' in texto and 'ImagePullBackOff' in texto


def test_dag_en_pausa_no_lanza_nada(falso, capsys):
    with falso(pausado=True) as (url, app):
        assert lanzar(url) == ll.PAUSA
        assert not app.state.runs
        assert 'unpause' in capsys.readouterr().out


def test_espera_agotada_devuelve_2_y_no_cancela(falso, capsys):
    with falso(seg_por_paso=60) as (url, app):
        assert ll.main(['--url', url, '--intervalo', '0', '--espera', '0']) == ll.ESPERA
        assert 'SIGUE en Airflow' in capsys.readouterr().out
        assert len(app.state.runs) == 1


def test_sin_servidor_da_codigo_3_con_mensaje(capsys):
    assert ll.main(['--url', 'http://127.0.0.1:9', '--espera', '1']) == ll.CONEXION
    assert 'Airflow' in capsys.readouterr().out


def test_dag_inexistente(falso, capsys):
    with falso() as (url, _):
        assert lanzar(url, '--dag', 'otro') == ll.CONEXION
        assert '404' in capsys.readouterr().out


def test_basic_v1_y_v2_con_jwt(falso, monkeypatch):
    monkeypatch.setenv('AIRFLOW_USUARIO', 'airflow')
    monkeypatch.setenv('AIRFLOW_CLAVE', 'airflow')
    for api in ('v1', 'v2'):
        with falso(api=api, auth='basic' if api == 'v1' else 'bearer') as (url, app):
            assert lanzar(url, '--auth', 'basic') == ll.OK
            if api == 'v2':
                assert ('POST', '/auth/token') in app.state.llamadas


def test_credenciales_malas_no_pasan(falso, monkeypatch, capsys):
    monkeypatch.setenv('AIRFLOW_USUARIO', 'airflow')
    monkeypatch.setenv('AIRFLOW_CLAVE', 'mala')
    with falso(auth='basic') as (url, app):
        assert lanzar(url, '--auth', 'basic') == ll.CONEXION
        assert '401' in capsys.readouterr().out and not app.state.runs


def test_token_google_simulado_con_variable(falso, monkeypatch):
    monkeypatch.setenv('AIRFLOW_TOKEN', 'token-de-google-de-prueba')
    with falso(auth='bearer') as (url, app):
        assert lanzar(url, '--auth', 'google') == ll.OK


def test_simular_url_no_hace_ninguna_llamada(capsys):
    assert ll.main(['--url', 'http://no-existe.invalido:1', '--simular-url', '--corte', '2011-12-10', '--imagen', 'x:1']) == ll.OK
    texto = capsys.readouterr().out
    assert 'No se ha enviado nada' in texto and '"corte": "2011-12-10"' in texto


def test_el_secreto_no_aparece_en_la_salida(falso, monkeypatch, capsys):
    monkeypatch.setenv('AIRFLOW_USUARIO', 'airflow')
    monkeypatch.setenv('AIRFLOW_CLAVE', 'clave-muy-secreta')
    with falso(auth='ninguna') as (url, _):
        lanzar(url, '--auth', 'basic')
    assert 'clave-muy-secreta' not in capsys.readouterr().out
