"""Pruebas de la versión en producción (ia_mlops/produccion.py): leer y validar models/referencia.json y compararla con una versión nueva."""
import json

import pytest

from ia_mlops import config, produccion
from ia_mlops.produccion import ErrorReferencia


@pytest.fixture()
def referencia():
    """Una referencia correcta, construida con las mismas funciones que usa el proyecto (sin entrenar nada)."""
    meta = {'modelo': 'regresion_logistica', 'huella_datos': 'aaaaaaaaaaaaaaaa', 'entrenado_en': '2026-01-01T10:00:00',
            'metricas_valid': {'auc': 0.70, 'precision_media': 0.74},
            'metricas_test': {'auc': 0.75, 'precision_media': 0.66, 'tasa_base': 0.40},
            'cortes': {'test': ['2011-06-01', '2011-09-01']}}
    return produccion.crear_referencia(meta, version=1, aprobado_en='2026-01-02T09:00:00')


@pytest.fixture()
def archivo(tmp_path, referencia, monkeypatch):
    """Escribe la referencia en una carpeta temporal y apunta config.REFERENCIA a ella."""
    ruta = tmp_path / 'referencia.json'
    produccion.escribir_referencia(referencia, ruta)
    monkeypatch.setattr(config, 'REFERENCIA', ruta)
    return ruta


def nueva(referencia, auc, huella='bbbbbbbbbbbbbbbb'):
    return {'huella_datos': huella, 'metricas_test': {'auc': auc}, 'cortes': {'test': referencia['cortes_test']}}


# ------------------------------------------------------------------------------------------------ leer y validar
def test_lee_y_valida(archivo, referencia):
    d = produccion.leer_referencia()
    assert d == referencia
    assert d['etiqueta_imagen'] == 'retencion-api:v1-aaaaaaaaaaaaaaaa'
    assert d['metrica_principal'] == config.METRICA_COMPARACION == 'auc'


def test_la_referencia_del_repositorio_es_valida():
    """models/referencia.json se versiona en el repositorio: si alguien la rompe, esta prueba lo dice."""
    ruta = config.RAIZ / 'models' / 'referencia.json'
    if not ruta.exists():
        pytest.skip('todavía no hay referencia en este clon')
    assert produccion.leer_referencia(ruta)['version'] >= 1


def test_no_existe_da_un_error_que_dice_que_hacer(tmp_path):
    with pytest.raises(ErrorReferencia, match='crear --version 1'):
        produccion.leer_referencia(tmp_path / 'no_existe.json')


def test_json_roto_da_error_claro(tmp_path):
    ruta = tmp_path / 'referencia.json'
    ruta.write_text('{esto no es json', encoding='utf-8')
    with pytest.raises(ErrorReferencia, match='no es un JSON válido'):
        produccion.leer_referencia(ruta)


def test_esquema_roto_falta_una_clave(referencia):
    del referencia['huella_datos']
    with pytest.raises(ErrorReferencia, match='falta la clave «huella_datos»'):
        produccion.validar_referencia(referencia)


@pytest.mark.parametrize('clave, valor, texto', [
    ('version', 0, '«version» debe ser un entero'),
    ('version', '1', '«version» debe ser un entero'),
    ('etiqueta_imagen', 'retencion-api:latest', 'no tiene la forma'),
    ('etiqueta_imagen', 'retencion-api:v2-aaaaaaaaaaaaaaaa', 'no coincide con «version» y «huella_datos»'),
    ('metricas_test', {'precision_media': 0.6}, 'no contiene la métrica principal'),
    ('cortes_test', [], '«cortes_test» debe ser una lista'),
    ('esquema', 99, 'esquema 99'),
])
def test_esquema_roto_valores_incorrectos(referencia, clave, valor, texto):
    referencia[clave] = valor
    with pytest.raises(ErrorReferencia, match=texto):
        produccion.validar_referencia(referencia)


# ------------------------------------------------------------------------------------------------ comparar
def test_misma_huella_es_igual_y_no_hay_nada_que_publicar(referencia):
    r = produccion.comparar_con_referencia(nueva(referencia, auc=0.10, huella=referencia['huella_datos']), referencia)
    assert r.decision == 'igual' and r.misma_huella_datos
    assert 'nada que publicar' in r.motivo


def test_metrica_peor_que_la_tolerancia_se_rechaza(referencia):
    r = produccion.comparar_con_referencia(nueva(referencia, auc=0.75 - 0.05), referencia, tolerancia=0.02)
    assert r.decision == 'rechazada'
    assert r.diferencia == pytest.approx(-0.05)
    assert 'empeora más que la tolerancia' in r.motivo


def test_dentro_de_la_tolerancia_se_acepta(referencia):
    r = produccion.comparar_con_referencia(nueva(referencia, auc=0.75 - 0.01), referencia, tolerancia=0.02)
    assert r.decision == 'aceptada'
    assert 'dentro de la tolerancia' in r.motivo


def test_mejorar_se_acepta_y_el_limite_exacto_tambien(referencia):
    assert produccion.comparar_con_referencia(nueva(referencia, auc=0.80), referencia).decision == 'aceptada'
    justo = produccion.comparar_con_referencia(nueva(referencia, auc=0.75 - 0.02), referencia, tolerancia=0.02)
    assert justo.decision == 'aceptada'      # «empeora MÁS que» la tolerancia: justo en el límite no se rechaza


def test_tolerancia_por_defecto_es_la_de_config(referencia, monkeypatch):
    monkeypatch.setattr(config, 'TOLERANCIA_COMPARACION', 0.001)
    r = produccion.comparar_con_referencia(nueva(referencia, auc=0.745), referencia)
    assert r.tolerancia == 0.001 and r.decision == 'rechazada'


def test_cortes_de_test_distintos_no_se_comparan(referencia):
    candidata = nueva(referencia, auc=0.75)
    candidata['cortes'] = {'test': ['2012-01-01']}
    with pytest.raises(ErrorReferencia, match='no son comparables'):
        produccion.comparar_con_referencia(candidata, referencia)


def test_a_las_metricas_nuevas_les_falta_la_principal(referencia):
    with pytest.raises(ErrorReferencia, match='metricas_test.auc'):
        produccion.comparar_con_referencia({'huella_datos': 'x', 'metricas_test': {}}, referencia)


# ------------------------------------------------------------------------------------------------ terminal
def test_cli_mostrar(archivo, capsys):
    assert produccion.main(['mostrar']) == 0
    salida = capsys.readouterr().out
    assert 'Versión en producción: v1' in salida and 'retencion-api:v1-aaaaaaaaaaaaaaaa' in salida and 'auc 0.7500' in salida


def test_cli_mostrar_sin_referencia_sale_con_2(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(config, 'REFERENCIA', tmp_path / 'nada.json')
    assert produccion.main(['mostrar']) == 2
    assert 'crear --version 1' in capsys.readouterr().err


def test_cli_comparar_con_archivo_de_metricas(archivo, referencia, tmp_path, capsys):
    candidata = tmp_path / 'candidata.json'
    candidata.write_text(json.dumps(nueva(referencia, auc=0.60)), encoding='utf-8')
    assert produccion.main(['comparar', '--metricas', str(candidata)]) == 1
    assert 'RECHAZADA' in capsys.readouterr().out
    candidata.write_text(json.dumps(nueva(referencia, auc=0.76)), encoding='utf-8')
    assert produccion.main(['comparar', '--metricas', str(candidata)]) == 0
    assert 'ACEPTADA' in capsys.readouterr().out


def test_crear_con_los_metadatos_de_un_entrenamiento_real(carpeta_modelo, tmp_path):
    """Con los metadatos.json de un entrenamiento real (carpeta temporal) se crea la versión 3 y se lee de vuelta."""
    meta = json.loads((carpeta_modelo / 'metadatos.json').read_text(encoding='utf-8'))
    candidata = {**meta, 'metricas_test': {'auc': 0.7, 'precision_media': 0.6}}   # las de test salen de reports/metricas.json
    ruta = produccion.escribir_referencia(produccion.crear_referencia(candidata, version=3), tmp_path / 'referencia.json')
    leida = produccion.leer_referencia(ruta)
    assert leida['version'] == 3 and leida['etiqueta_imagen'] == f'retencion-api:v3-{meta["huella_datos"]}'
    assert leida['cortes_test'] == config.CORTES['test']
