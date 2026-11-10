"""Los casos de la practica de S2 (tests/datos/casos/*.json) deben dar EXACTAMENTE lo que dice la guia del laboratorio y la presentacion."""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ia_mlops.api.app import crear_app

CASOS = Path(__file__).parent / 'datos' / 'casos'

# archivo, codigo esperado, texto que debe aparecer en la respuesta
ESPERADO = [
    ('01_correcto.json', 200, '"probabilidad"'),
    ('02_recencia_negativa.json', 422, 'recencia_dias'),
    ('03_con_el_objetivo_y.json', 422, 'extra_forbidden'),
    ('04_falta_frecuencia.json', 422, 'Field required'),
    ('05_reino_unido_2.json', 422, 'es_reino_unido'),
    ('06_frecuencia_90d_mayor_que_total.json', 422, 'frecuencia_90d <= frecuencia_180d <= frecuencia'),
    ('07_seis_facturas_sin_dias_medios.json', 422, 'null si y solo si hay una sola factura'),
    ('08_ticket_medio_enorme.json', 200, 'fuera del rango visto al entrenar'),
    ('09_una_sola_factura.json', 200, 'no informado'),
    ('10_frecuencia_cero.json', 422, 'greater than or equal to 1'),
]


@pytest.fixture(scope='module')
def cliente(carpeta_modelo):
    with TestClient(crear_app(carpeta_modelo)) as c:
        yield c


def test_la_lista_cubre_todos_los_archivos_de_casos():
    assert sorted(p.name for p in CASOS.glob('*.json')) == sorted(e[0] for e in ESPERADO)


@pytest.mark.parametrize('archivo,codigo,texto', ESPERADO)
def test_cada_caso_da_el_codigo_y_el_mensaje_de_la_guia(cliente, archivo, codigo, texto):
    r = cliente.post('/predecir', json=json.loads((CASOS / archivo).read_text(encoding='utf-8')))
    assert r.status_code == codigo, r.text
    assert texto in r.text, r.text


def test_el_caso_correcto_es_el_ejemplo_de_la_documentacion():
    ejemplo = json.loads((Path(__file__).parent / 'datos' / 'cliente_ejemplo.json').read_text(encoding='utf-8'))
    assert json.loads((CASOS / '01_correcto.json').read_text(encoding='utf-8')) == ejemplo


def test_el_lote_de_ejemplo_da_dos_predicciones_en_orden_y_la_segunda_avisa(cliente):
    lote = json.loads((Path(__file__).parent / 'datos' / 'lote_ejemplo.json').read_text(encoding='utf-8'))
    r = cliente.post('/predecir/lote', json=lote)
    assert r.status_code == 200, r.text
    preds = r.json()['predicciones']
    assert len(preds) == 2 and preds[0]['advertencias'] == [] and 'no informado' in preds[1]['advertencias'][0]
    assert preds[0]['probabilidad'] != preds[1]['probabilidad']
