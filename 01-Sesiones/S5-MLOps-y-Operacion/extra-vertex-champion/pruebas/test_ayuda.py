"""Pruebas del ayudante JSON de los scripts (vertex_ayuda.py): el reparto de tráfico es lo que decide qué versión sirve.

No necesitan Google Cloud ni MLflow: son JSON de ejemplo con la forma de la API REST de Vertex AI (SIN VERIFICAR contra una cuenta real).
"""
import json

import pytest

import vertex_ayuda as va

VACIO = {'deployedModels': [], 'trafficSplit': {}}
UNO = {'deployedModels': [{'id': '111', 'displayName': 'mlflow-v5'}], 'trafficSplit': {'111': 100}}
DOS_CANARIO = {'deployedModels': [{'id': '111', 'displayName': 'mlflow-v5'}, {'id': '222', 'displayName': 'mlflow-v6'}],
               'trafficSplit': {'111': 90, '222': 10}}
VERSIONES = [{'versionId': '1', 'versionAliases': ['mlflow-v5'], 'labels': {'mlflow_version': '5'}},
             {'versionId': '2', 'versionAliases': ['champion', 'mlflow-v6'], 'labels': {'mlflow_version': '6', 'mlflow_version_anterior': '5'}}]


def test_endpoint_vacio_el_nuevo_recibe_todo():
    assert va.split_nuevo(VACIO, 10) == '0=100'
    assert va.split_nuevo(VACIO, 0) == '0=100'


def test_canario_reparte_el_resto_a_quien_mas_trafico_tenia():
    assert va.split_nuevo(UNO, 10) == '0=10,111=90'
    assert va.split_nuevo(UNO, 100) == '0=100,111=0'            # «todo al nuevo» también pone el viejo a 0: la suma debe ser 100
    assert va.split_nuevo(DOS_CANARIO, 20) == '0=20,111=80,222=0'


def test_el_reparto_siempre_suma_100():
    for ep in (VACIO, UNO, DOS_CANARIO):
        for n in (0, 1, 10, 50, 100):
            partes = dict(p.split('=') for p in va.split_nuevo(ep, n).split(','))
            assert sum(int(v) for v in partes.values()) == 100, (ep, n)


def test_porcentaje_fuera_de_rango_es_un_error():
    with pytest.raises(ValueError):
        va.split_nuevo(UNO, 101)
    with pytest.raises(ValueError):
        va.split_nuevo(UNO, -1)


def test_split_solo_manda_todo_a_uno_y_el_resto_a_cero():
    assert va.split_solo(DOS_CANARIO, '222') == '111=0,222=100'
    assert va.split_solo(DOS_CANARIO, '111') == '111=100,222=0'
    with pytest.raises(ValueError, match='no está en el endpoint'):
        va.split_solo(DOS_CANARIO, '999')


def test_actual_es_el_que_mas_trafico_recibe_y_vacio_si_no_hay():
    assert va.actual(DOS_CANARIO) == '111'
    assert va.actual(VACIO) == ''


def test_buscar_por_nombre_y_por_id():
    assert va.desplegado(DOS_CANARIO, 'mlflow-v6') == '222'
    assert va.desplegado(DOS_CANARIO, 'mlflow-v9') == ''
    assert va.nombre_de(DOS_CANARIO, '111') == 'mlflow-v5'


def test_versiones_del_modelo_por_alias_y_etiqueta():
    assert va.version_modelo(VERSIONES, 'mlflow-v6') == '2'
    assert va.version_modelo(VERSIONES, 'champion') == '2'
    assert va.version_modelo(VERSIONES, 'mlflow-v9') == ''
    assert va.etiqueta_de(VERSIONES, 'mlflow-v6', 'mlflow_version_anterior') == '5'
    assert va.etiqueta_de(VERSIONES, 'mlflow-v5', 'mlflow_version_anterior') == ''


def test_cli_imprime_lo_que_usan_los_scripts(tmp_path, capsys):
    f = tmp_path / 'ep.json'
    f.write_text(json.dumps(DOS_CANARIO), encoding='utf-8')
    assert va.main(['split-nuevo', '--json', str(f), '--porcentaje', '10']) == 0
    assert capsys.readouterr().out.strip() == '0=10,111=90,222=0'
    assert va.main(['ids', '--json', str(f)]) == 0
    assert capsys.readouterr().out.strip() == '111 222'
    assert va.main(['trafico', '--json', str(f)]) == 0
    assert capsys.readouterr().out.splitlines() == ['111\tmlflow-v5\t90%', '222\tmlflow-v6\t10%']
    assert va.main(['split-solo', '--json', str(f), '--id', '999']) == 2
    assert va.main(['ids', '--json', str(tmp_path / 'no-existe.json')]) == 2
