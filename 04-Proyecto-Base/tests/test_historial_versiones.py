"""Pruebas del historial de versiones (models/historial_versiones.json), el que lee la pestaña «Versiones» del panel
y que nueva-version.yml y rollback.yml actualizan en el mismo pull request que models/referencia.json."""
import json
import subprocess

import pytest

from ia_mlops import config, produccion
from ia_mlops.produccion import ErrorReferencia


def ficha(version, huella, auc=0.75):
    meta = {'modelo': 'regresion_logistica', 'huella_datos': huella, 'entrenado_en': f'2026-01-0{version}T10:00:00',
            'metricas_valid': {'auc': 0.70}, 'metricas_test': {'auc': auc, 'precision_media': 0.66},
            'cortes': {'test': ['2011-06-01', '2011-09-01']}}
    return produccion.crear_referencia(meta, version=version, aprobado_en=f'2026-01-0{version}T12:00:00',
                                       fuente='completo' if version > 1 else None)


def estados(filas):
    return {f['version']: f['estado'] for f in filas}


def test_la_ruta_del_historial_va_junto_a_la_referencia(tmp_path):
    assert produccion.ruta_historial(tmp_path / 'referencia.json') == tmp_path / 'historial_versiones.json'
    assert produccion.ruta_historial().name == 'historial_versiones.json'
    assert produccion.ruta_historial().parent == config.REFERENCIA.parent


def test_sin_archivo_el_historial_esta_vacio(tmp_path):
    assert produccion.leer_historial(tmp_path / 'nada.json') == []


def test_la_primera_version_crea_el_historial(tmp_path):
    ruta = tmp_path / 'historial_versiones.json'
    filas = produccion.actualizar_historial(ficha(1, 'a' * 16), ruta=ruta)
    assert estados(filas) == {1: 'produccion'}
    d = json.loads(ruta.read_text(encoding='utf-8'))
    assert list(d) == ['versiones']
    fila = d['versiones'][0]
    assert set(fila) == {'version', 'etiqueta_imagen', 'huella_datos', 'modelo', 'fuente_datos', 'auc_test', 'entrenado_en', 'aprobado_en', 'estado'}
    assert fila['auc_test'] == 0.75 and fila['fuente_datos'] == 'muestra' and fila['etiqueta_imagen'] == 'retencion-api:v1-' + 'a' * 16
    assert all(not isinstance(v, (dict, list)) for v in fila.values()), 'el panel muestra solo campos escalares'


def test_una_version_nueva_pasa_la_anterior_a_anterior(tmp_path):
    ruta = tmp_path / 'h.json'
    v1, v2 = ficha(1, 'a' * 16), ficha(2, 'b' * 16, auc=0.80)
    produccion.actualizar_historial(v1, ruta=ruta)
    filas = produccion.actualizar_historial(v2, retira=v1, estado_retirada='anterior', ruta=ruta)
    assert estados(filas) == {1: 'anterior', 2: 'produccion'} and [f['version'] for f in filas] == [1, 2]
    assert filas[1]['fuente_datos'] == 'completo' and filas[1]['auc_test'] == 0.80
    assert produccion.leer_historial(ruta) == filas


def test_rollback_la_restaurada_vuelve_a_produccion_y_la_retirada_queda_retirada(tmp_path):
    ruta = tmp_path / 'h.json'
    v1, v2 = ficha(1, 'a' * 16), ficha(2, 'b' * 16)
    produccion.actualizar_historial(v1, ruta=ruta)
    produccion.actualizar_historial(v2, retira=v1, ruta=ruta)
    filas = produccion.actualizar_historial(v1, retira=v2, estado_retirada='retirada', ruta=ruta)
    assert estados(filas) == {1: 'produccion', 2: 'retirada'} and [f['version'] for f in filas] == [1, 2]   # sin duplicar y en su sitio
    filas = produccion.actualizar_historial(v2, retira=v1, estado_retirada='anterior', ruta=ruta)           # volver a avanzar
    assert estados(filas) == {1: 'anterior', 2: 'produccion'}


def test_repetir_la_misma_orden_no_cambia_nada(tmp_path):
    ruta = tmp_path / 'h.json'
    v1, v2 = ficha(1, 'a' * 16), ficha(2, 'b' * 16)
    produccion.actualizar_historial(v1, ruta=ruta)
    primera = produccion.actualizar_historial(v2, retira=v1, ruta=ruta)
    assert produccion.actualizar_historial(v2, retira=v1, ruta=ruta) == primera
    assert sum(f['estado'] == 'produccion' for f in primera) == 1


def test_la_version_que_sale_se_anade_si_el_historial_es_posterior_a_ella(tmp_path):
    """Si el historial se creó después de la v1, el rollback de la v2 a la v1 deja ambas, con la v2 retirada."""
    ruta = tmp_path / 'h.json'
    v1, v2 = ficha(1, 'a' * 16), ficha(2, 'b' * 16)
    produccion.actualizar_historial(v2, ruta=ruta)
    filas = produccion.actualizar_historial(v1, retira=v2, estado_retirada='retirada', ruta=ruta)
    assert estados(filas) == {2: 'retirada', 1: 'produccion'}


def test_errores_claros(tmp_path):
    with pytest.raises(ErrorReferencia, match='Estado'):
        produccion.entrada_historial(ficha(1, 'a' * 16), 'inventado')
    with pytest.raises(ErrorReferencia, match='anterior'):
        produccion.actualizar_historial(ficha(1, 'a' * 16), estado_retirada='produccion', ruta=tmp_path / 'h.json')
    roto = tmp_path / 'roto.json'
    roto.write_text('{no es json', encoding='utf-8')
    with pytest.raises(ErrorReferencia, match='no es un JSON válido'):
        produccion.leer_historial(roto)
    roto.write_text('[]', encoding='utf-8')
    with pytest.raises(ErrorReferencia, match='«versiones»'):
        produccion.leer_historial(roto)


def test_cli_historial_con_retira(tmp_path, capsys):
    """La orden que usan los workflows: `historial --retira <ficha que sale>` sobre la referencia ya actualizada."""
    anterior, actual = tmp_path / 'anterior.json', tmp_path / 'referencia.json'
    produccion.escribir_referencia(ficha(1, 'a' * 16), anterior)
    produccion.escribir_referencia(ficha(2, 'b' * 16), actual)
    assert produccion.main(['--ruta', str(actual), 'historial', '--retira', str(anterior)]) == 0
    filas = produccion.leer_historial(tmp_path / 'historial_versiones.json')
    assert estados(filas) == {1: 'anterior', 2: 'produccion'}
    assert 'v2' in capsys.readouterr().out
    # rollback: la ficha restaurada es la v1 y la que sale es la v2
    produccion.escribir_referencia(ficha(1, 'a' * 16), actual)
    salida = tmp_path / 'sale.json'
    produccion.escribir_referencia(ficha(2, 'b' * 16), salida)
    assert produccion.main(['--ruta', str(actual), 'historial', '--retira', str(salida), '--estado-retirada', 'retirada']) == 0
    assert estados(produccion.leer_historial(tmp_path / 'historial_versiones.json')) == {1: 'produccion', 2: 'retirada'}
    assert produccion.main(['--ruta', str(actual), 'historial', '--retira', str(tmp_path / 'no.json')]) == 2


# ------------------------------------------------------------------------------------------------ el archivo del repositorio
def test_el_historial_del_repositorio_es_coherente_con_la_referencia():
    """models/historial_versiones.json se versiona: debe tener exactamente una versión en producción y ser la de referencia.json."""
    ruta = config.RAIZ / 'models' / 'historial_versiones.json'
    if not ruta.exists():
        pytest.skip('todavía no hay historial en este clon')
    filas = produccion.leer_historial(ruta)
    assert filas, 'el historial no puede estar vacío'
    en_produccion = [f for f in filas if f['estado'] == 'produccion']
    assert len(en_produccion) == 1 and all(f['estado'] in produccion.ESTADOS_HISTORIAL for f in filas)
    ref = produccion.leer_referencia(config.RAIZ / 'models' / 'referencia.json')
    assert en_produccion[0]['version'] == ref['version'] and en_produccion[0]['etiqueta_imagen'] == ref['etiqueta_imagen']
    assert en_produccion[0]['huella_datos'] == ref['huella_datos'] and en_produccion[0]['auc_test'] == ref['metricas_test']['auc']
    assert len({f['version'] for f in filas}) == len(filas), 'una fila por versión'


def test_el_gitignore_deja_versionar_el_historial():
    lineas = (config.RAIZ / '.gitignore').read_text(encoding='utf-8').splitlines()
    assert 'models/*.json' in lineas and '!models/referencia.json' in lineas and '!models/historial_versiones.json' in lineas
    assert lineas.index('!models/historial_versiones.json') > lineas.index('models/*.json')   # la excepción va DESPUÉS de la regla que ignora
