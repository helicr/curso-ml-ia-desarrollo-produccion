"""Pruebas del manifiesto del champion (manifiesto_champion.py), de preparar_contexto.py y de instancias.py.

Todo sobre una COPIA del registro de MLflow del proyecto (ver conftest.py): el alias champion se mueve en la copia, nunca en el original.
"""
import json
import re

import pytest

import manifiesto_champion as mc
import preparar_contexto
import instancias
from conftest import AQUI, PROYECTO, REGISTRO_REAL, _sha

# ------------------------------------------------------------------------------------------------ etiquetas de Google Cloud
def test_las_reglas_de_etiquetas_de_gcp():
    assert mc.etiqueta_valida('mlflow_version', '6') and mc.etiqueta_valida('auc_valid', '0_6982') and mc.etiqueta_valida('a', '')
    assert not mc.etiqueta_valida('Mlflow', '6')                    # mayúsculas
    assert not mc.etiqueta_valida('1clave', '6')                    # debe empezar por letra
    assert not mc.etiqueta_valida('clave', '0.6982')                # el punto no vale
    assert not mc.etiqueta_valida('a' * 64, 'x') and not mc.etiqueta_valida('clave', 'x' * 64)
    assert mc.etiqueta_valida('a' * 63, 'x' * 63)


def test_sanear_deja_solo_minusculas_numeros_guiones_y_corta_a_63():
    assert mc.sanear('Champion V6!') == 'champion_v6_'
    assert mc.sanear('x' * 100) == 'x' * 63
    assert mc.numero_a_etiqueta(0.6982009925558312) == '0_6982'
    assert mc.numero_a_etiqueta(0.747092830088378) == '0_7471'


def test_etiquetas_de_un_manifiesto_son_todas_validas():
    datos = {'mlflow_version': 3, 'run_id': 'A' * 32, 'valid_auc': 0.6982, 'test_auc': 0.7471, 'huella_datos': '35a94deb4e04ab4a', 'version_anterior': 2}
    m = mc.construir(datos, 'retencion-90d', 'champion')
    assert m['etiquetas']['mlflow_version'] == '3' and m['etiquetas']['mlflow_version_anterior'] == '2' and m['etiquetas']['auc_valid'] == '0_6982'
    assert m['etiquetas']['mlflow_run'] == 'a' * 32                  # en minúsculas
    assert len(m['etiquetas']) <= 64 and all(mc.etiqueta_valida(k, v) for k, v in m['etiquetas'].items())
    assert m['etiquetas_gcloud'].count(',') == len(m['etiquetas']) - 1 and 'curso=ml-ia' in m['etiquetas_gcloud']
    assert m['etiqueta_imagen'] == 'v3-35a94deb4e04ab4a' and m['alias_vertex'] == 'mlflow-v3'


def test_sin_version_anterior_no_hay_etiqueta_anterior():
    m = mc.construir({'mlflow_version': 1, 'run_id': 'r', 'valid_auc': 0.7, 'test_auc': 0.7, 'huella_datos': 'h', 'version_anterior': None}, 'retencion-90d', 'champion')
    assert 'mlflow_version_anterior' not in m['etiquetas'] and m['version_anterior'] is None


# ------------------------------------------------------------------------------------------------ leer de MLflow (copia del registro)
def test_el_manifiesto_sale_del_registro_y_coincide_con_mlflow(manifiesto, cliente_mlflow, champion):
    from ia_mlops import alias_modelo
    e = alias_modelo.estado(cliente_mlflow)
    v = next(x for x in e['versiones'] if x['version'] == champion['version'])
    assert manifiesto['mlflow_version'] == champion['version'] == e['alias']['champion']
    assert manifiesto['version_anterior'] == champion['anterior']
    assert manifiesto['valid_auc'] == pytest.approx(v['valid_auc']) and manifiesto['test_auc'] == pytest.approx(v['test_auc'])
    assert manifiesto['huella_datos'] == v['huella_datos'] and manifiesto['run_id'] == v['run_id']
    assert manifiesto['simulado'] is False and manifiesto['modelo'] == 'retencion-90d'
    assert manifiesto['variables'][0] == 'recencia_dias' and len(manifiesto['variables']) == 13


def test_pedir_una_version_concreta_no_depende_del_alias(registro, champion):
    m = mc.generar(uri=registro['uri'], version=champion['anterior'])
    assert m['mlflow_version'] == champion['anterior']


def test_un_registro_sin_alias_o_sin_la_version_da_un_error_claro(registro, champion, cliente_mlflow):
    with pytest.raises(mc.ErrorManifiesto, match='no tiene el alias @otro'):
        mc.generar(uri=registro['uri'], alias='otro')
    with pytest.raises(mc.ErrorManifiesto, match='No existe la versión 999'):
        mc.generar(uri=registro['uri'], version=999)


def test_simular_no_abre_mlflow_y_se_marca(monkeypatch, tmp_path):
    from ia_mlops import alias_modelo
    monkeypatch.setattr(alias_modelo, 'conectar', lambda *a, **k: (_ for _ in ()).throw(AssertionError('no debería abrir MLflow')))
    salida = tmp_path / 'm.json'
    assert mc.main(['generar', '--simular', '--salida', str(salida)]) == 0
    m = json.loads(salida.read_text(encoding='utf-8'))
    assert m['simulado'] is True and m['mlflow_version'] == 6 and m['version_anterior'] == 5
    assert mc.puerta(m) and 'SIMULADO' in ' '.join(mc.puerta(m))    # un manifiesto simulado no pasa la puerta


# ------------------------------------------------------------------------------------------------ puerta de calidad
def test_la_puerta_de_calidad(manifiesto):
    assert mc.puerta(manifiesto) == []
    assert any('valid_auc' in f for f in mc.puerta(manifiesto, auc_minimo=0.99))
    sin_huella = dict(manifiesto, huella_datos=None)
    assert any('huella' in f for f in mc.puerta(sin_huella))
    sin_test = dict(manifiesto, test_auc=None)
    assert any('test_auc no está' in f for f in mc.puerta(sin_test))


def test_la_puerta_por_la_linea_de_ordenes(manifiesto, tmp_path, capsys):
    f = tmp_path / 'm.json'
    f.write_text(json.dumps(manifiesto), encoding='utf-8')
    assert mc.main(['puerta', '--manifiesto', str(f)]) == 0 and 'Puerta de calidad abierta' in capsys.readouterr().out
    assert mc.main(['puerta', '--manifiesto', str(f), '--auc-minimo', '0.99']) == 2 and 'CERRADA' in capsys.readouterr().err


# ------------------------------------------------------------------------------------------------ vuelta MLflow <- Vertex
def test_anotar_escribe_las_etiquetas_vertex_en_la_version_de_mlflow(manifiesto, registro, cliente_mlflow, champion):
    et = mc.anotar(manifiesto, vertex_version=3, endpoint='retencion-90d-champion-ep', deployed_model_id='123', region='southamerica-west1',
                   uri=registro['uri'], vertex_modelo='retencion-90d-champion')
    v = cliente_mlflow.get_model_version('retencion-90d', str(champion['version']))
    assert v.tags['vertex_model_version'] == '3' and v.tags['vertex_endpoint'] == 'retencion-90d-champion-ep'
    assert v.tags['vertex_deployed_model_id'] == '123' and v.tags['vertex_modelo'] == 'retencion-90d-champion'
    assert et['vertex_region'] == 'southamerica-west1'
    otra = cliente_mlflow.get_model_version('retencion-90d', str(champion['anterior']))
    assert 'vertex_endpoint' not in (otra.tags or {})                   # solo la versión desplegada
    assert v.tags.get('huella_datos') == manifiesto['huella_datos']      # no pisa las que ya tenía


def test_anotar_con_simular_no_escribe_nada(manifiesto, registro, cliente_mlflow, champion):
    antes = dict(cliente_mlflow.get_model_version('retencion-90d', str(champion['anterior'])).tags or {})
    et = mc.anotar(dict(manifiesto, mlflow_version=champion['anterior']), 7, 'ep', simular=True)
    assert et['vertex_model_version'] == '7'
    assert dict(cliente_mlflow.get_model_version('retencion-90d', str(champion['anterior'])).tags or {}) == antes


def test_anotar_una_version_que_no_existe_es_un_error_claro(manifiesto, registro):
    with pytest.raises(mc.ErrorManifiesto, match='No existe la versión 999'):
        mc.anotar(dict(manifiesto, mlflow_version=999), 1, 'ep', uri=registro['uri'])


def test_leer_un_campo_del_manifiesto_por_la_linea_de_ordenes(manifiesto, tmp_path, capsys):
    f = tmp_path / 'm.json'
    f.write_text(json.dumps(manifiesto), encoding='utf-8')
    assert mc.main(['leer', '--manifiesto', str(f), 'etiqueta_imagen']) == 0
    assert capsys.readouterr().out.strip() == f'v{manifiesto["mlflow_version"]}-{manifiesto["huella_datos"]}'
    assert mc.main(['leer', '--manifiesto', str(f), 'etiquetas.mlflow_alias']) == 0 and capsys.readouterr().out.strip() == 'champion'
    assert mc.main(['leer', '--manifiesto', str(f), 'no_existe']) == 2
    assert mc.main(['leer', '--manifiesto', str(tmp_path / 'no.json'), 'x']) == 2


# ------------------------------------------------------------------------------------------------ contexto de la imagen
def test_el_contexto_lleva_el_modelo_de_la_version_del_manifiesto(contexto, manifiesto):
    m = json.loads((contexto / 'modelo' / 'vertex-manifiesto.json').read_text(encoding='utf-8'))
    assert m == manifiesto
    assert preparar_contexto.version_sklearn_del_modelo(contexto / 'modelo' / 'modelo_mlflow') == preparar_contexto.version_sklearn_del_lock(contexto / 'requirements-api.lock')


def test_preparar_contexto_se_niega_a_borrar_una_carpeta_ajena(tmp_path, manifiesto):
    ajena = tmp_path / 'mis-cosas'
    ajena.mkdir()
    (ajena / 'importante.txt').write_text('no tocar', encoding='utf-8')
    with pytest.raises(mc.ErrorManifiesto, match='no lo borro'):
        preparar_contexto.preparar(manifiesto, ajena, modelo_origen=None)
    assert (ajena / 'importante.txt').read_text(encoding='utf-8') == 'no tocar'


def test_preparar_contexto_avisa_si_el_modelo_y_el_lock_tienen_otro_scikit_learn(contexto, manifiesto, tmp_path):
    lock = tmp_path / 'proyecto'
    lock.mkdir()
    (lock / 'requirements-api.lock').write_text('scikit-learn==1.6.1\n', encoding='utf-8')
    with pytest.raises(mc.ErrorManifiesto, match='1.6.1'):
        preparar_contexto.preparar(manifiesto, tmp_path / 'ctx', modelo_origen=contexto / 'modelo' / 'modelo_mlflow', proyecto=lock)


def test_preparar_contexto_por_la_linea_de_ordenes_con_un_modelo_ya_exportado(contexto, manifiesto, tmp_path, capsys):
    destino = tmp_path / 'ctx'
    f = tmp_path / 'm.json'
    f.write_text(json.dumps(manifiesto), encoding='utf-8')
    assert preparar_contexto.main(['--manifiesto', str(f), '--destino', str(destino), '--modelo-origen', str(contexto / 'modelo' / 'modelo_mlflow')]) == 0
    assert 'Contexto listo' in capsys.readouterr().out and (destino / 'Dockerfile.vertex').exists()
    assert preparar_contexto.main(['--manifiesto', str(tmp_path / 'no.json'), '--destino', str(destino)]) == 2


# ------------------------------------------------------------------------------------------------ instancias
def test_las_instancias_van_en_el_orden_de_config_features():
    from ia_mlops import config
    clientes = json.loads((AQUI / 'clientes_ejemplo.json').read_text(encoding='utf-8'))
    r = instancias.a_instancias(clientes)
    assert r['nombres'] == ['activo', 'dormido', 'una_factura']
    assert r['instances'][0] == [35, 6, 1250.4, 208.4, 410, 38, 310, 2, 380.5, 4, 55.0, 1, 1]
    assert r['instances'][2][10] is None and all(len(i) == 13 for i in r['instances'])
    assert [clientes['activo'][v] for v in config.FEATURES] == r['instances'][0]
    with pytest.raises(ValueError, match='faltan variables'):
        instancias.a_instancias({'roto': {'recencia_dias': 1}})


def test_los_clientes_de_ejemplo_son_los_de_la_practica_04_mas_uno():
    mios = json.loads((AQUI / 'clientes_ejemplo.json').read_text(encoding='utf-8'))
    s4 = json.loads((AQUI.parent.parent / 'S4-Orquestacion-y-CI-CD' / 'practicas-gcp' / 'clientes_ejemplo.json').read_text(encoding='utf-8'))
    assert all(mios[k] == s4[k] for k in s4)


# ------------------------------------------------------------------------------------------------ el registro real no se toca
def test_el_registro_real_del_proyecto_no_ha_cambiado(huella_registro_real_al_empezar):
    """Estas pruebas trabajan SIEMPRE sobre una copia. Si la huella del original cambia durante la sesión es porque OTRO proceso lo ha escrito
    (en un equipo compartido puede haber otras sesiones del curso usando models/mlflow.db): se avisa con un skip explícito, no se da por bueno en silencio."""
    actual = _sha(REGISTRO_REAL)
    if actual != huella_registro_real_al_empezar:
        pytest.skip('otro proceso ha escrito en models/mlflow.db durante la sesión (estas pruebas solo leen y copian: no son ellas)')
    assert actual == huella_registro_real_al_empezar