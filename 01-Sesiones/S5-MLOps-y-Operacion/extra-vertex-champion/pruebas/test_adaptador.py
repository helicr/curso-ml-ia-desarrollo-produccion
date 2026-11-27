"""Pruebas del adaptador de Vertex AI (imagen/vertex_adaptador.py) sobre el modelo REAL del proyecto (en una copia del registro).

Qué vigilan:
    * el CONTRATO de Vertex: ruta de salud, ruta de predicción, {"instances": [[13 números]]} -> {"predictions": [...]}, una predicción por instancia;
    * PARIDAD EXACTA con el modelo cargado como lo hace `alias_modelo.cargar_y_puntuar` (por alias de MLflow) y con el cargado a mano;
    * errores claros (422) sin romper el servicio, sin repetir los valores recibidos y sin escribirlos en el registro;
    * el arranque REAL (`python vertex_adaptador.py` en la carpeta de la imagen, con AIP_HTTP_PORT, AIP_HEALTH_ROUTE y AIP_PREDICT_ROUTE);
    * el Dockerfile.vertex: sin variables AIP_*, sin latest, sin root, y que lo que copia existe en el contexto que prepara preparar_contexto.py.
"""
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import vertex_adaptador as va
from conftest import AQUI, PROYECTO

CLIENTES = json.loads((AQUI / 'clientes_ejemplo.json').read_text(encoding='utf-8'))
EJEMPLO = json.loads((PROYECTO / 'tests' / 'datos' / 'cliente_ejemplo.json').read_text(encoding='utf-8'))


def instancia(c):
    from ia_mlops import config
    return [c[v] for v in config.FEATURES]


@pytest.fixture(scope='module')
def cliente_http(contexto):
    with TestClient(va.crear_app(contexto / 'modelo', '/salud', '/predict')) as c:
        yield c


def predecir(c, instancias):
    return c.post('/predict', json={'instances': instancias})


# ------------------------------------------------------------------------------------------------ contrato
def test_la_ruta_de_salud_responde_200_con_el_modelo_cargado(cliente_http):
    r = cliente_http.get('/salud')
    assert r.status_code == 200 and r.json() == {'estado': 'ok'}


def test_una_prediccion_por_instancia_con_probabilidad_clase_y_tramo(cliente_http, manifiesto):
    r = predecir(cliente_http, [instancia(c) for c in CLIENTES.values()])
    assert r.status_code == 200
    cuerpo = r.json()
    assert list(cuerpo) == ['predictions']
    assert len(cuerpo['predictions']) == len(CLIENTES)
    from ia_mlops import config
    segmentos = {s['segmento'] for s in config.SEGMENTOS_RECOMPRA}
    for p in cuerpo['predictions']:
        assert set(p) == {'probabilidad', 'clase', 'tramo', 'version_mlflow'}
        assert 0 <= p['probabilidad'] <= 1 and isinstance(p['probabilidad'], float)
        assert p['clase'] == int(p['probabilidad'] >= 0.5)
        assert p['tramo'] in segmentos
        assert p['version_mlflow'] == manifiesto['mlflow_version']


def test_devuelve_la_probabilidad_no_la_clase(cliente_http):
    """La diferencia con el contenedor pre-construido de la práctica 04: aquí hay probabilidades continuas, no solo 0 o 1."""
    ps = [p['probabilidad'] for p in predecir(cliente_http, [instancia(c) for c in CLIENTES.values()]).json()['predictions']]
    assert any(0 < p < 1 for p in ps) and len(set(ps)) > 1


def test_los_tramos_siguen_los_umbrales_de_negocio():
    assert va.tramo(0.70) == 'alta' and va.tramo(0.6999) == 'media' and va.tramo(0.40) == 'media' and va.tramo(0.39) == 'baja' and va.tramo(0.0) == 'baja'


def test_un_cliente_de_una_sola_factura_admite_null_en_dias_medios(cliente_http):
    r = predecir(cliente_http, [instancia(CLIENTES['una_factura'])])
    assert r.status_code == 200 and 0 <= r.json()['predictions'][0]['probabilidad'] <= 1


def test_el_cuerpo_puede_traer_parameters_y_se_ignora(cliente_http):
    r = cliente_http.post('/predict', json={'instances': [instancia(EJEMPLO)], 'parameters': {'x': 1}})
    assert r.status_code == 200


def test_la_ruta_modelo_dice_que_version_es(cliente_http, manifiesto):
    m = cliente_http.get('/modelo').json()
    assert m['mlflow_version'] == manifiesto['mlflow_version'] and m['huella_datos'] == manifiesto['huella_datos'] and len(m['variables']) == 13


# ------------------------------------------------------------------------------------------------ paridad
def test_paridad_exacta_con_cargar_y_puntuar_por_alias(cliente_http, cliente_mlflow, champion):
    """El adaptador debe dar EXACTAMENTE lo que `alias_modelo.cargar_y_puntuar` da cargando models:/retencion-90d@champion."""
    from ia_mlops import alias_modelo
    esperado = alias_modelo.cargar_y_puntuar(cliente_mlflow, EJEMPLO)
    assert esperado['version'] == champion['version']
    p = predecir(cliente_http, [instancia(EJEMPLO)]).json()['predictions'][0]
    assert p['probabilidad'] == pytest.approx(esperado['probabilidad'], abs=1e-12)
    assert p['version_mlflow'] == esperado['version']


def test_paridad_exacta_con_el_modelo_cargado_a_mano(cliente_http, contexto):
    import mlflow.sklearn
    import pandas as pd
    from ia_mlops import config
    modelo = mlflow.sklearn.load_model(str(contexto / 'modelo' / 'modelo_mlflow'))
    df = pd.DataFrame([{k: (float('nan') if v is None else float(v)) for k, v in c.items()} for c in CLIENTES.values()])[config.FEATURES]
    esperado = modelo.predict_proba(df)[:, 1]
    clases = modelo.predict(df)
    r = predecir(cliente_http, [instancia(c) for c in CLIENTES.values()]).json()['predictions']
    for p, e, k in zip(r, esperado, clases):
        assert p['probabilidad'] == pytest.approx(float(e), abs=1e-12)
        assert p['clase'] == int(k)                       # el predict() del modelo (lo que devolvería el contenedor pre-construido)


def test_el_orden_de_las_variables_importa_y_el_contrato_lo_fija(cliente_http):
    """Si alguien cambia el orden de la lista, el modelo NO avisa: contesta otra cosa. Por eso se genera con instancias.py."""
    normal = instancia(CLIENTES['activo'])
    cambiado = list(normal)
    cambiado[0], cambiado[1] = cambiado[1], cambiado[0]       # recencia_dias <-> frecuencia
    a = predecir(cliente_http, [normal]).json()['predictions'][0]['probabilidad']
    r = predecir(cliente_http, [cambiado])
    assert r.status_code == 422 or r.json()['predictions'][0]['probabilidad'] != a


def test_el_comparador_de_paridad_acepta_la_respuesta_real_y_detecta_una_diferencia(cliente_http, contexto, tmp_path):
    import comparar_paridad as cp
    instancias = [instancia(c) for c in CLIENTES.values()]
    respuesta = predecir(cliente_http, instancias).json()['predictions']
    codigo, lineas = cp.comparar(respuesta, instancias, contexto / 'modelo')
    assert codigo == 0 and 'PARIDAD: las predicciones' in lineas[-1]
    mala = [dict(respuesta[0], probabilidad=respuesta[0]['probabilidad'] + 0.01)] + respuesta[1:]
    assert cp.comparar(mala, instancias, contexto / 'modelo')[0] == 1
    assert cp.comparar(respuesta, instancias, contexto / 'modelo', esperar_version=respuesta[0]['version_mlflow'] + 1)[0] == 3
    f_r, f_i = tmp_path / 'r.json', tmp_path / 'i.json'
    f_r.write_text(json.dumps({'predictions': respuesta}), encoding='utf-8')
    f_i.write_text(json.dumps({'instances': instancias}), encoding='utf-8')
    assert cp.main(['--respuesta', str(f_r), '--instancias', str(f_i), '--modelo-dir', str(contexto / 'modelo')]) == 0


# ------------------------------------------------------------------------------------------------ errores
@pytest.mark.parametrize('cuerpo, fragmento', [
    ({'instances': [{'recencia_dias': 1}]}, 'LISTA'),
    ({'instances': [[1, 2, 3]]}, 'lista de 13 números'),
    ({'instances': [['a'] * 13]}, 'número finito'),
    ({'instances': [[True] + [1] * 12]}, 'número finito'),
    ({'instances': []}, 'al menos una'),
    ({'instances': 'x'}, 'al menos una'),
    ({'otra': 1}, '"instances"'),
    ([1, 2], '"instances"'),
    ({'instances': [[1] * 13]}, 'dias_medios_entre_compras'),
])
def test_cuerpos_no_validos_dan_422_con_un_mensaje_claro(cliente_http, cuerpo, fragmento):
    r = cliente_http.post('/predict', json=cuerpo)
    assert r.status_code == 422
    assert fragmento in json.dumps(r.json(), ensure_ascii=False)
    assert r.json()['error']


def test_valores_fuera_de_contrato_se_rechazan_como_la_api(cliente_http):
    mal = instancia(CLIENTES['activo'])
    mal[12] = 2                                                     # es_reino_unido solo 0 o 1
    r = predecir(cliente_http, [mal])
    assert r.status_code == 422 and any(e['campo'] == 'es_reino_unido' and e['instancia'] == 0 for e in r.json()['errores'])
    mal = instancia(CLIENTES['activo'])
    mal[0] = -3
    assert predecir(cliente_http, [mal]).status_code == 422


def test_json_roto_y_nan_dan_422(cliente_http):
    assert cliente_http.post('/predict', content=b'esto no es json').status_code == 422
    assert cliente_http.post('/predict', content=b'{"instances": [[NaN, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]]}',
                             headers={'content-type': 'application/json'}).status_code == 422


def test_mas_de_1000_instancias_se_rechazan(cliente_http):
    assert predecir(cliente_http, [instancia(EJEMPLO)] * 1001).status_code == 422
    assert predecir(cliente_http, [instancia(EJEMPLO)] * 1000).status_code == 200


def test_los_errores_no_repiten_los_valores_recibidos(cliente_http):
    mal = instancia(CLIENTES['activo'])
    mal[0] = 987654.321
    r = predecir(cliente_http, [mal])
    assert r.status_code == 422 and '987654.321' not in r.text


def test_un_error_no_rompe_el_servicio(cliente_http):
    assert predecir(cliente_http, [[1]]).status_code == 422
    assert predecir(cliente_http, [instancia(EJEMPLO)]).status_code == 200
    assert cliente_http.get('/salud').status_code == 200


def test_no_se_registran_los_datos_del_cliente(contexto, capsys):
    with TestClient(va.crear_app(contexto / 'modelo', '/salud', '/predict')) as c:
        predecir(c, [instancia(EJEMPLO)])
    salida = capsys.readouterr().out
    assert '"evento": "peticion"' in salida and '1250.4' not in salida and '208.4' not in salida


def test_sin_modelo_la_salud_y_la_prediccion_dan_503(tmp_path):
    with TestClient(va.crear_app(tmp_path, '/salud', '/predict')) as c:
        assert c.get('/salud').status_code == 503
        assert c.post('/predict', json={'instances': [[1] * 13]}).status_code == 503
        assert c.get('/modelo').status_code == 503


def test_una_firma_distinta_a_config_features_no_arranca_lista(contexto, tmp_path, monkeypatch):
    from ia_mlops import config
    monkeypatch.setattr(config, 'FEATURES', list(reversed(config.FEATURES)))
    with TestClient(va.crear_app(contexto / 'modelo', '/salud', '/predict')) as c:
        assert c.get('/salud').status_code == 503
        assert 'no coincide' in c.get('/salud').json()['detalle']


# ------------------------------------------------------------------------------------------------ rutas y puerto de Vertex
def test_las_rutas_salen_de_las_variables_aip(contexto, monkeypatch):
    monkeypatch.setenv('AIP_HEALTH_ROUTE', '/v1/endpoints/1/deployedModels/2')
    monkeypatch.setenv('AIP_PREDICT_ROUTE', '/v1/endpoints/1/deployedModels/2:predict')
    with TestClient(va.crear_app(contexto / 'modelo')) as c:
        assert c.get('/v1/endpoints/1/deployedModels/2').status_code == 200
        r = c.post('/v1/endpoints/1/deployedModels/2:predict', json={'instances': [instancia(EJEMPLO)]})
        assert r.status_code == 200 and len(r.json()['predictions']) == 1
        assert c.get('/salud').status_code == 200             # la ruta de siempre sigue para probar a mano


def test_el_puerto_sale_de_aip_http_port(monkeypatch):
    vistos = {}
    import uvicorn
    monkeypatch.setattr(uvicorn, 'run', lambda app, **kw: vistos.update(kw))
    monkeypatch.setenv('AIP_HTTP_PORT', '9123')
    va.main()
    assert vistos['port'] == 9123 and vistos['host'] == '0.0.0.0'
    monkeypatch.delenv('AIP_HTTP_PORT')
    va.main()
    assert vistos['port'] == 8080


def _puerto_libre():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def test_arranque_real_como_en_la_imagen(contexto, tmp_path):
    """`python vertex_adaptador.py` EN LA CARPETA DEL CONTEXTO (lo que hace el CMD de la imagen), con las variables que pone Vertex."""
    puerto = _puerto_libre()
    entorno = {**os.environ, 'AIP_HTTP_PORT': str(puerto), 'AIP_HEALTH_ROUTE': '/salud', 'AIP_PREDICT_ROUTE': '/predict',
               'CURSO_MODELO_DIR': str(contexto / 'modelo'), 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONUTF8': '1'}
    entorno.pop('PYTHONPATH', None)
    proceso = subprocess.Popen([sys.executable, '-B', 'vertex_adaptador.py'], cwd=contexto, env=entorno, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')
    try:
        base = f'http://127.0.0.1:{puerto}'
        for _ in range(120):
            try:
                if urllib.request.urlopen(base + '/salud', timeout=2).status == 200:
                    break
            except (urllib.error.URLError, ConnectionError, OSError):
                time.sleep(0.5)
        else:
            pytest.fail('el servidor no respondió en /salud')
        peticion = urllib.request.Request(base + '/predict', data=json.dumps({'instances': [instancia(EJEMPLO)]}).encode(), headers={'content-type': 'application/json'})
        cuerpo = json.loads(urllib.request.urlopen(peticion, timeout=10).read())
        assert 0 < cuerpo['predictions'][0]['probabilidad'] < 1
    finally:
        proceso.terminate()
        salida, _ = proceso.communicate(timeout=20)
    assert '"evento": "modelo_cargado"' in salida


# ------------------------------------------------------------------------------------------------ Dockerfile.vertex y contexto
DOCKERFILE = (AQUI / 'imagen' / 'Dockerfile.vertex').read_text(encoding='utf-8')


def _instrucciones(texto):
    return [l.strip() for l in texto.splitlines() if l.strip() and not l.strip().startswith('#')]


def test_el_dockerfile_no_define_variables_aip_ni_usa_latest_ni_root():
    texto = '\n'.join(_instrucciones(DOCKERFILE))
    assert not re.search(r'\bAIP_\w+\s*=', texto), 'la documentación de Vertex dice: no definas variables con el prefijo AIP_'
    assert ':latest' not in texto and re.search(r'^FROM python:3\.11-slim', texto, re.M)
    assert 'USER 10001' in texto and 'useradd' in texto
    assert 'CMD ["python", "vertex_adaptador.py"]' in texto and 'EXPOSE 8080' in texto


def test_el_dockerfile_instala_el_mismo_lock_que_la_api_y_copia_solo_lo_que_hay(contexto):
    texto = '\n'.join(_instrucciones(DOCKERFILE))
    assert 'COPY requirements-api.lock .' in texto and 'pip install -r requirements-api.lock' in texto
    for origen in re.findall(r'^COPY (\S+) ', texto, re.M):
        assert (contexto / origen.rstrip('/')).exists(), f'el contexto no tiene {origen}'
    assert (contexto / 'requirements-api.lock').read_bytes() == (PROYECTO / 'requirements-api.lock').read_bytes()
    assert (contexto / 'modelo' / 'modelo_mlflow' / 'MLmodel').exists() and (contexto / 'modelo' / 'vertex-manifiesto.json').exists()


def test_compatible_con_las_dos_formas_de_construir_la_api(contexto):
    """No usa ni el COPY de models/ del Dockerfile de develop ni `--from=modelo` del multietapa: depende solo de su propio contexto."""
    texto = '\n'.join(_instrucciones(DOCKERFILE))
    assert '--from=' not in texto and 'build-context' not in DOCKERFILE.split('FROM python')[1] and 'models/modelo_mlflow' not in texto
    develop = (PROYECTO / 'deploy' / 'docker' / 'Dockerfile').read_text(encoding='utf-8')
    assert 'requirements-api.lock' in develop and 'COPY ia_mlops/ ia_mlops/' in develop        # el lock y el código que también usa esta imagen
    assert not (contexto / 'models').exists()


def test_el_contexto_solo_lleva_lo_minimo_de_ia_mlops(contexto):
    archivos = sorted(p.relative_to(contexto / 'ia_mlops').as_posix() for p in (contexto / 'ia_mlops').rglob('*.py'))
    assert archivos == ['__init__.py', 'api/__init__.py', 'api/esquemas.py', 'config.py']


def test_sin_rutas_personales_ni_credenciales_en_el_adaptador_y_el_dockerfile():
    for ruta in (AQUI / 'imagen' / 'vertex_adaptador.py', AQUI / 'imagen' / 'Dockerfile.vertex'):
        t = ruta.read_text(encoding='utf-8')
        assert 'C:\\' not in t and 'AppData' not in t and not re.search(r'(token|password|secret)\s*[:=]\s*\S{6,}', t, re.I)
