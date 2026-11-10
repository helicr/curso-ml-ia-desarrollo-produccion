"""Pruebas de la API (S2): contrato, errores, paridad con el paquete, logs y comportamiento sin modelo."""
import json
import logging
import typing
import urllib.request

import joblib
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from ia_mlops import config, db
from ia_mlops.api import esquemas
from ia_mlops.api.app import crear_app
from ia_mlops.api.esquemas import EJEMPLO
from ia_mlops.api.servicio import ContratoRoto, Servicio
from ia_mlops.modeling import predict, train


@pytest.fixture(scope='module')
def cliente(carpeta_modelo):
    with TestClient(crear_app(carpeta_modelo)) as c:
        yield c


@pytest.fixture(scope='module')
def clientes_de_test(ruta_db):
    """Hasta 200 filas reales de la particion test, tal como las enviaria quien llama (sin el objetivo y).

    Incluye clientes con una sola factura (dias_medios_entre_compras = NULL), que llegan como null.
    """
    con = db.conectar(ruta_db)
    df = pd.read_sql(f"SELECT {', '.join(config.FEATURES)} FROM ml_dataset WHERE particion = 'test' ORDER BY cliente_id, fecha_corte LIMIT 200", con)
    con.close()
    return df


def _como_json(df):
    """DataFrame -> lista de diccionarios JSON (NaN pasa a None, numpy a tipos nativos)."""
    return json.loads(df.to_json(orient='records'))


def _lineas_json(texto):
    lineas = []
    for linea in texto.splitlines():
        if linea.startswith('{'):
            try:
                lineas.append(json.loads(linea))
            except ValueError:
                pass
    return lineas


# --- salud y estado --------------------------------------------------------------------------------------------------------------

def test_salud_y_listo(cliente):
    assert cliente.get('/salud').json() == {'estado': 'ok'}
    assert cliente.get('/listo').json() == {'estado': 'listo'}


def test_modelo_informa_de_los_datos_con_que_se_entreno(cliente, carpeta_modelo):
    r = cliente.get('/modelo').json()
    meta = json.loads((carpeta_modelo / 'metadatos.json').read_text(encoding='utf-8'))
    assert r['huella_datos'] == meta['huella_datos'] and r['variables'] == config.FEATURES
    assert set(r['metricas_valid']) >= {'auc', 'precision_media'}


def test_cada_peticion_devuelve_un_identificador(cliente):
    assert len(cliente.get('/salud').headers['x-request-id']) == 12
    assert cliente.get('/salud', headers={'X-Request-ID': 'abc-123'}).headers['x-request-id'] == 'abc-123'


# --- prediccion ------------------------------------------------------------------------------------------------------------------

def test_predice_una_probabilidad(cliente):
    r = cliente.post('/predecir', json=EJEMPLO)
    assert r.status_code == 200
    cuerpo = r.json()
    assert 0.0 <= cuerpo['probabilidad'] <= 1.0 and cuerpo['modelo'] in ('regresion_logistica', 'gradient_boosting')
    assert cuerpo['advertencias'] == []


def test_paridad_api_paquete_joblib_y_mlflow_con_filas_reales(cliente, carpeta_modelo, clientes_de_test):
    """La API debe dar la MISMA probabilidad que el paquete, el modelo joblib y el modelo MLflow, cliente por cliente."""
    assert len(clientes_de_test) >= 100
    filas = _como_json(clientes_de_test)
    lote = cliente.post('/predecir/lote', json={'clientes': filas})
    assert lote.status_code == 200
    de_la_api = np.array([p['probabilidad'] for p in lote.json()['predicciones']])
    del_paquete = np.array(predict.predecir_probabilidad(clientes_de_test, ruta=carpeta_modelo))
    np.testing.assert_allclose(de_la_api, del_paquete, rtol=0, atol=1e-12)
    del_joblib = joblib.load(carpeta_modelo / 'modelo.joblib').predict_proba(clientes_de_test)[:, 1]
    np.testing.assert_allclose(de_la_api, del_joblib, rtol=0, atol=1e-12)
    import mlflow.sklearn
    del_mlflow = mlflow.sklearn.load_model(str(carpeta_modelo / config.CARPETA_MODELO_MLFLOW)).predict_proba(clientes_de_test)[:, 1]
    np.testing.assert_allclose(de_la_api, del_mlflow, rtol=0, atol=1e-12)
    # Y uno por uno, para comprobar que el lote y la peticion individual no difieren.
    for i in (0, len(filas) // 2, len(filas) - 1):
        una = cliente.post('/predecir', json=filas[i]).json()['probabilidad']
        assert una == pytest.approx(de_la_api[i], abs=1e-12)


def test_el_lote_mantiene_el_orden(cliente, clientes_de_test):
    filas = _como_json(clientes_de_test.head(5))
    directo = [p['probabilidad'] for p in cliente.post('/predecir/lote', json={'clientes': filas}).json()['predicciones']]
    invertido = [p['probabilidad'] for p in cliente.post('/predecir/lote', json={'clientes': filas[::-1]}).json()['predicciones']]
    assert directo == pytest.approx(invertido[::-1])


def test_un_cliente_con_una_sola_factura_llega_con_dias_medios_nulo_y_se_avisa(cliente):
    una_factura = {**EJEMPLO, 'frecuencia': 1, 'frecuencia_90d': 1, 'frecuencia_180d': 1, 'ticket_medio': EJEMPLO['monto_total'],
                   'dias_medios_entre_compras': None}
    r = cliente.post('/predecir', json=una_factura)
    assert r.status_code == 200 and 0 <= r.json()['probabilidad'] <= 1
    assert any('dias_medios_entre_compras' in a for a in r.json()['advertencias'])


def test_dias_medios_puede_omitirse_si_hay_una_sola_factura(cliente):
    una_factura = {**EJEMPLO, 'frecuencia': 1, 'frecuencia_90d': 1, 'frecuencia_180d': 1, 'ticket_medio': EJEMPLO['monto_total']}
    del una_factura['dias_medios_entre_compras']
    assert cliente.post('/predecir', json=una_factura).status_code == 200


def test_avisa_de_un_valor_valido_que_el_entrenamiento_no_vio(cliente):
    """Un gasto enorme es posible (no se rechaza) pero esta fuera del rango de train: el modelo extrapola y la API lo dice."""
    r = cliente.post('/predecir', json={**EJEMPLO, 'monto_total': 900000.0, 'ticket_medio': 150000.0, 'monto_90d': 380.5}).json()
    assert 0 <= r['probabilidad'] <= 1
    assert any('monto_total=900000' in a for a in r['advertencias']) and any('ticket_medio' in a for a in r['advertencias'])


# --- el contrato rechaza lo que no debe entrar --------------------------------------------------------------------------------------

@pytest.mark.parametrize('campo', ['y', 'cliente_id', 'fecha_corte', 'particion', 'compra_proximos_90d', 'campo_inventado'])
def test_rechaza_campos_que_no_son_del_contrato(cliente, campo):
    """El objetivo, un identificador o cualquier cosa que el modelo no usa: 422 en vez de ignorarse en silencio."""
    r = cliente.post('/predecir', json={**EJEMPLO, campo: 1})
    assert r.status_code == 422 and 'Extra inputs are not permitted' in json.dumps(r.json())


@pytest.mark.parametrize('cambio', [
    {'recencia_dias': -1}, {'recencia_dias': 5000}, {'recencia_dias': 'ayer'}, {'monto_total': -10.0}, {'devoluciones': -1},
    {'es_reino_unido': 2}, {'es_reino_unido': 'si'}, {'frecuencia': 0}, {'frecuencia': 2.5}, {'dias_medios_entre_compras': -3.0},
])
def test_rechaza_valores_fuera_de_dominio(cliente, cambio):
    assert cliente.post('/predecir', json={**EJEMPLO, **cambio}).status_code == 422


def test_rechaza_si_falta_una_variable(cliente):
    sin_frecuencia = {k: v for k, v in EJEMPLO.items() if k != 'frecuencia'}
    r = cliente.post('/predecir', json=sin_frecuencia)
    assert r.status_code == 422 and 'frecuencia' in json.dumps(r.json())


@pytest.mark.parametrize('cambio', [
    {'frecuencia_90d': 5},                                       # mas facturas en 90 dias que en 180
    {'frecuencia_180d': 7},                                      # mas facturas en 180 dias que en total
    {'antiguedad_dias': 10, 'recencia_dias': 35},                # la primera compra seria posterior a la ultima
    {'monto_90d': 5000.0},                                       # gasto reciente mayor que el total
    {'ticket_medio': 999.0},                                     # no es monto_total / frecuencia
    {'frecuencia': 1, 'frecuencia_90d': 1, 'frecuencia_180d': 1, 'ticket_medio': 1250.4},       # una factura pero con intervalo medio
    {'dias_medios_entre_compras': None},                         # seis facturas sin intervalo medio
])
def test_rechaza_combinaciones_imposibles(cliente, cambio):
    """Son combinaciones que la capa FS nunca produce: casi seguro un error de quien llama."""
    assert cliente.post('/predecir', json={**EJEMPLO, **cambio}).status_code == 422


def test_un_cliente_sin_historia_no_tiene_variables(cliente):
    """Sin compras antes del corte no hay fila en FS (frecuencia >= 1): la API no inventa valores para el."""
    sin_historia = {**EJEMPLO, 'frecuencia': 0, 'frecuencia_90d': 0, 'frecuencia_180d': 0, 'monto_total': 0.0, 'monto_90d': 0.0, 'ticket_medio': 0.0,
                    'dias_medios_entre_compras': None}
    assert cliente.post('/predecir', json=sin_historia).status_code == 422


def test_lote_vacio_o_demasiado_grande_se_rechaza(cliente):
    assert cliente.post('/predecir/lote', json={'clientes': []}).status_code == 422
    assert cliente.post('/predecir/lote', json={'clientes': [EJEMPLO] * 1001}).status_code == 422
    assert cliente.post('/predecir/lote', json={'clientes': [EJEMPLO] * 1000}).status_code == 200


def test_un_json_roto_es_un_error_del_cliente(cliente):
    assert cliente.post('/predecir', content='{no es json', headers={'content-type': 'application/json'}).status_code == 422


def test_metodo_o_ruta_inexistente(cliente):
    assert cliente.get('/predecir').status_code == 405
    assert cliente.get('/no-existe').status_code == 404


# --- el contrato coincide con el modelo y con los datos reales ---------------------------------------------------------------------

def _tipo_mlflow(campo):
    """Tipo MLflow que corresponde a un campo de Pydantic: int y 0/1 -> long; float -> double."""
    anotacion = campo.annotation
    if typing.get_origin(anotacion) is typing.Union:
        anotacion = [a for a in typing.get_args(anotacion) if a is not type(None)][0]
    if typing.get_origin(anotacion) is typing.Literal:
        return 'long'
    return {int: 'long', float: 'double'}[anotacion]


def test_el_esquema_de_la_api_coincide_con_la_firma_del_modelo(carpeta_modelo):
    """Nombres, orden, tipos y obligatoriedad: lo que la firma declara es lo que la API acepta."""
    import mlflow.models
    firma = mlflow.models.Model.load(str(carpeta_modelo / config.CARPETA_MODELO_MLFLOW)).signature
    columnas = firma.inputs.inputs
    assert list(esquemas.Cliente.model_fields) == config.FEATURES == [c.name for c in columnas]
    for c in columnas:
        campo = esquemas.Cliente.model_fields[c.name]
        assert _tipo_mlflow(campo) == c.type.name, c.name
        if not c.required:                       # si la firma admite que falte, la API debe admitirlo tambien
            assert not campo.is_required(), c.name


def test_todas_las_filas_reales_de_fs_cumplen_el_contrato(con):
    """Si la API rechazara una fila que FS produce, habria clientes a los que nadie puede pedirles prediccion."""
    df = pd.read_sql(f"SELECT {', '.join(config.FEATURES)} FROM fs_cliente_corte", con)
    assert len(df) > 500
    for fila in _como_json(df):
        esquemas.Cliente(**fila)


def test_el_ejemplo_de_la_documentacion_es_valido():
    esquemas.Cliente(**EJEMPLO)
    assert json.loads((config.RAIZ / 'tests' / 'datos' / 'cliente_ejemplo.json').read_text(encoding='utf-8')) == EJEMPLO


# --- fallos del servicio ---------------------------------------------------------------------------------------------------------

def test_sin_modelo_la_api_arranca_pero_dice_que_no_esta_lista(tmp_path):
    with TestClient(crear_app(tmp_path / 'vacia')) as c:
        assert c.get('/salud').status_code == 200                      # el proceso vive
        listo = c.get('/listo')
        assert listo.status_code == 503 and 'Entrenalo antes' in listo.json()['detalle']
        assert c.get('/modelo').status_code == 503
        assert c.post('/predecir', json=EJEMPLO).status_code == 503


def test_si_la_firma_no_coincide_con_los_metadatos_el_servicio_no_carga(carpeta_modelo, tmp_path):
    import shutil
    copia = tmp_path / 'models'
    shutil.copytree(carpeta_modelo, copia)
    meta = json.loads((copia / 'metadatos.json').read_text(encoding='utf-8'))
    meta['variables'] = meta['variables'][:-1]
    (copia / 'metadatos.json').write_text(json.dumps(meta), encoding='utf-8')
    with pytest.raises(ContratoRoto):
        Servicio.cargar(copia)
    with TestClient(crear_app(copia)) as c:
        assert c.get('/listo').status_code == 503 and 'no coincide' in c.get('/listo').json()['detalle']


def test_si_el_esquema_de_la_api_no_tiene_las_variables_del_modelo_no_esta_listo(carpeta_modelo):
    """Caso de la tarea: reentrenar con una variable nueva sin actualizar esquemas.Cliente. Debe verse en /listo, no en cada prediccion."""
    campos = list(esquemas.Cliente.model_fields)
    casos = [([c for c in campos if c != 'devoluciones'], "Faltan en la API: ['devoluciones']"), (campos + ['campo_inventado'], "Sobran en la API: ['campo_inventado']")]
    for malos, texto in casos:
        with TestClient(crear_app(carpeta_modelo, campos_contrato=malos)) as c:
            assert c.get('/salud').status_code == 200                     # el proceso esta vivo
            listo = c.get('/listo')
            assert listo.status_code == 503 and texto in listo.json()['detalle'] and 'esquemas.py' in listo.json()['detalle']
            assert c.post('/predecir', json=EJEMPLO).status_code == 503
    with TestClient(crear_app(carpeta_modelo)) as c:                        # y con el esquema real, listo
        assert c.get('/listo').status_code == 200


def test_un_error_inesperado_devuelve_500_sin_detalles_internos(carpeta_modelo, monkeypatch, capsys):
    def roto(self, filas):
        raise RuntimeError('detalle interno secreto: /ruta/privada')
    monkeypatch.setattr(Servicio, 'predecir', roto)
    with TestClient(crear_app(carpeta_modelo), raise_server_exceptions=False) as c:
        capsys.readouterr()
        r = c.post('/predecir', json=EJEMPLO)
    assert r.status_code == 500 and r.json()['detalle'] == 'Error interno'
    assert 'secreto' not in r.text and 'ruta' not in r.text
    assert r.json()['id_peticion'] == r.headers['x-request-id']
    salida = capsys.readouterr().out
    assert 'detalle interno secreto' in salida          # pero el log SI lo guarda, con el mismo identificador
    error = [l for l in _lineas_json(salida) if l.get('evento') == 'error_no_controlado'][0]
    assert error['severity'] == 'ERROR' and error['id'] == r.headers['x-request-id']


# --- registro ----------------------------------------------------------------------------------------------------------------------

def test_el_log_sale_por_stdout_en_json_y_no_contiene_datos_del_cliente(cliente, capsys):
    capsys.readouterr()
    cliente.post('/predecir', json={**EJEMPLO, 'monto_total': 7777.77, 'ticket_medio': 1296.29, 'monto_90d': 123.45})
    salida = capsys.readouterr().out
    peticion = [l for l in _lineas_json(salida) if l.get('evento') == 'peticion' and l['ruta'] == '/predecir'][-1]
    assert set(peticion) == {'severity', 'message', 'evento', 'id', 'metodo', 'ruta', 'codigo', 'ms'}
    assert peticion['severity'] == 'INFO' and peticion['message'] == 'POST /predecir 200'
    assert '7777' not in salida and '1296' not in salida


def test_crear_la_app_varias_veces_no_duplica_el_handler(carpeta_modelo, capsys):
    for _ in range(3):
        crear_app(carpeta_modelo)
    with TestClient(crear_app(carpeta_modelo)) as c:
        capsys.readouterr()
        c.get('/salud')
    assert len([l for l in _lineas_json(capsys.readouterr().out) if l.get('evento') == 'peticion']) == 1


def test_el_nivel_de_registro_se_puede_cambiar_con_una_variable_de_entorno(carpeta_modelo, monkeypatch, capsys):
    try:
        monkeypatch.setenv('CURSO_LOG_NIVEL', 'WARNING')
        with TestClient(crear_app(carpeta_modelo)) as c:
            capsys.readouterr()
            c.get('/salud')
        assert _lineas_json(capsys.readouterr().out) == []
    finally:                       # el resto de pruebas del modulo necesita el nivel INFO
        monkeypatch.setenv('CURSO_LOG_NIVEL', 'INFO')
        crear_app(carpeta_modelo)
    assert logging.getLogger('ia_mlops.api').level == logging.INFO


def test_con_uvicorn_de_verdad_las_lineas_json_llegan_a_stdout(carpeta_modelo, arrancar_servidor):
    """Con `caplog` o TestClient las lineas aparecen aunque el servidor real no emita nada (un logger sin handler).
    Esta prueba arranca el servidor como lo hace el contenedor y lee su salida estandar."""
    puerto, salida = arrancar_servidor(carpeta_modelo)
    peticion = urllib.request.Request(f'http://127.0.0.1:{puerto}/predecir', data=json.dumps({**EJEMPLO, 'monto_total': 7777.77, 'ticket_medio': 1296.29}).encode(),
                                      headers={'content-type': 'application/json', 'x-request-id': 'prueba-uvicorn'})
    respuesta = json.loads(urllib.request.urlopen(peticion, timeout=5).read())
    assert 0 <= respuesta['probabilidad'] <= 1
    texto = salida.read_text()
    lineas = _lineas_json(texto)
    assert any(l.get('evento') == 'modelo_cargado' for l in lineas), texto
    mia = [l for l in lineas if l.get('id') == 'prueba-uvicorn']
    assert mia and mia[0]['ruta'] == '/predecir' and mia[0]['codigo'] == 200 and mia[0]['severity'] == 'INFO'
    assert '7777' not in texto
