"""Pruebas de nivel 1 del agente (S5): las herramientas como funciones Python, sin LLM y sin MCP.

Paridad con la API de S4 (puntuar_bajo_demanda y puntuar_online devuelven lo mismo que sus endpoints), lista del día ordenada y del tamaño
pedido, versión en producción, explicación exacta de la regresión logística y errores claros (una herramienta nunca lanza).
No tocan la base ni los reportes reales: todo sale de la fixture `entorno_agente` (conftest.py).
"""
import json
import math
import sqlite3

import pytest
from fastapi.testclient import TestClient

from ia_mlops import config, produccion
from ia_mlops.agente import herramientas as h
from ia_mlops.interfaz import panel
from ia_mlops.interfaz.app import crear_app

CLAVES_PERSONALES = {'nombre', 'name', 'apellido', 'email', 'correo', 'mail', 'telefono', 'phone', 'direccion', 'address', 'dni', 'nif'}


@pytest.fixture()
def api(entorno_agente):
    """Los endpoints de la interfaz sobre la misma base y el mismo modelo que las herramientas."""
    return TestClient(crear_app(ruta_db=entorno_agente.ruta_db, carpeta_modelo=entorno_agente.carpeta_modelo, url_api='', demo=False))


def ids_de(entorno, desplazamientos=(0, 7, 30, 90)):
    con = sqlite3.connect(entorno.ruta_db)
    try:
        return [con.execute('SELECT cliente_id FROM fs_produccion ORDER BY cliente_id LIMIT 1 OFFSET ?', [d]).fetchone()[0] for d in desplazamientos]
    finally:
        con.close()


def sin_ms(d):
    return {k: v for k, v in d.items() if k != 'ms'}


def claves(obj):
    """Todas las claves de un JSON anidado."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield str(k)
            yield from claves(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from claves(v)


# ----------------------------------------------------------------------------------------------------- paridad con la API
def test_bajo_demanda_es_lo_mismo_que_el_endpoint(entorno_agente, api):
    for i in ids_de(entorno_agente):
        herramienta, endpoint = h.puntuar_bajo_demanda(i), api.get(f'/bajo-demanda/{i}').json()
        assert 'error' not in herramienta
        assert sin_ms(herramienta) == sin_ms(endpoint)
        assert herramienta['modo'] == 'bajo_demanda' and herramienta['corte'] == entorno_agente.corte and herramienta['ms'] > 0


def test_online_es_lo_mismo_que_el_endpoint_con_y_sin_corte(entorno_agente, api):
    con_corte = 0
    for i in ids_de(entorno_agente):
        assert sin_ms(h.puntuar_online(i)) == sin_ms(api.get(f'/online/{i}').json())
        otro, r = h.puntuar_online(i, corte='2011-06-01'), api.get(f'/online/{i}', params={'corte': '2011-06-01'})
        if r.status_code == 200:                         # el cliente ya existía en ese corte: misma respuesta
            assert sin_ms(otro) == sin_ms(r.json()) and otro['corte'] == '2011-06-01' and otro['modo'] == 'online'
            con_corte += 1
        else:                                            # todavía no había comprado: el mismo motivo, como dato y no como excepción
            assert r.status_code == 404 and otro['error'] == r.json()['detalle']
    assert con_corte >= 1


def test_los_dos_modos_coinciden_sin_compras_nuevas(entorno_agente):
    # sin compras de demo, «ahora» es el corte del lote: el mismo cliente da la misma probabilidad por los dos caminos
    i = ids_de(entorno_agente)[1]
    assert h.puntuar_online(i)['probabilidad'] == pytest.approx(h.puntuar_bajo_demanda(i)['probabilidad'], abs=1e-9)


# ----------------------------------------------------------------------------------------------------- lista del día
def test_lista_del_dia_ordenada_y_del_tamano_pedido(entorno_agente):
    for n in (1, 5, 12):
        r = h.lista_del_dia(n)
        assert 'error' not in r and r['devueltos'] == len(r['clientes']) == n
        p = [c['probabilidad'] for c in r['clientes']]
        assert p == sorted(p, reverse=True)
        assert [c['puesto'] for c in r['clientes']] == list(range(1, n + 1))
        assert len({c['cliente_id'] for c in r['clientes']}) == n
        assert all(c['tramo'] in ('alta', 'media', 'baja') and c['recomendacion'] for c in r['clientes'])
    assert h.lista_del_dia()['devueltos'] == 10                     # por defecto, 10
    assert r['corte'] == entorno_agente.corte and r['campana'] == f'campana_{entorno_agente.corte}.csv'


def test_lista_del_dia_coincide_con_el_panel_y_con_puntuar(entorno_agente):
    r = h.lista_del_dia(5)
    assert [c['cliente_id'] for c in r['clientes']] == [x['cliente_id'] for x in panel.datos_lote()['primeros'][:5]]
    for c in r['clientes']:      # la campaña se escribió con el mismo modelo y las mismas variables: misma probabilidad
        assert c['probabilidad'] == pytest.approx(h.puntuar_bajo_demanda(c['cliente_id'])['probabilidad'], abs=1e-4)


def test_lista_del_dia_no_deja_rutas_y_respeta_el_maximo(entorno_agente):
    r = h.lista_del_dia(10 ** 6)
    assert r['devueltos'] <= h.MAXIMO_LISTA and (r['devueltos'] == h.MAXIMO_LISTA) == ('aviso' in r)
    assert 'archivos' not in r and 'privada' not in json.dumps(r)


@pytest.mark.parametrize('n', [0, -3, 'muchos', 2.5, None])
def test_lista_del_dia_con_n_no_valido(entorno_agente, n):
    assert 'error' in h.lista_del_dia(n)


def test_lista_del_dia_sin_campana(entorno_agente, tmp_path, monkeypatch):
    monkeypatch.setenv('CURSO_CAMPANA', str(tmp_path / 'no_hay'))
    r = h.lista_del_dia(3)
    assert 'ejecutar antes el lote' in r['error']


# ----------------------------------------------------------------------------------------------------- versión en producción
def test_version_en_produccion(entorno_agente):
    ref = produccion.leer_referencia()
    r = h.version_en_produccion()
    assert 'error' not in r
    assert r['version'] == ref['version'] and r['etiqueta_imagen'] == ref['etiqueta_imagen'] and r['huella_datos'] == ref['huella_datos']
    assert r['en_produccion_desde'] == ref['aprobado_en'] and r['metricas_test']['auc'] == ref['metricas_test']['auc']
    assert [v['version'] for v in r['historial']] == [ref['version']] and r['historial'][0]['estado'] == 'produccion'
    assert h.referencia_del_modelo() == ref


def test_version_sin_referencia_o_con_historial_roto(entorno_agente, tmp_path, monkeypatch):
    monkeypatch.setattr(config, 'REFERENCIA', tmp_path / 'no_existe.json')
    sin_ficha = h.version_en_produccion()
    assert 'No existe' in sin_ficha['error'] and sin_ficha['tipo'] == 'sin_referencia' and 'error' in h.referencia_del_modelo()
    # referencia correcta y historial ilegible: la versión se responde igualmente, con un aviso
    ref = tmp_path / 'referencia.json'
    ref.write_text(json.dumps(entorno_agente.referencia), encoding='utf-8')
    (tmp_path / 'historial_versiones.json').write_text('{no es json', encoding='utf-8')
    monkeypatch.setattr(config, 'REFERENCIA', ref)
    r = h.version_en_produccion()
    assert r['version'] == entorno_agente.referencia['version'] and r['historial'] is None and 'JSON' in r['aviso']


# ----------------------------------------------------------------------------------------------------- por qué
def test_por_que_es_exacto_con_la_regresion_logistica(entorno_agente):
    i = ids_de(entorno_agente)[1]
    r = h.por_que(i, n=len(config.FEATURES))
    assert 'error' not in r and r['metodo'] == 'regresion_logistica_exacto'
    assert [v['variable'] for v in r['variables_que_mas_pesan']].count('recencia_dias') == 1
    assert sorted(v['variable'] for v in r['variables_que_mas_pesan']) == sorted(config.FEATURES)
    pesos = [abs(v['peso_logit']) for v in r['variables_que_mas_pesan']]
    assert pesos == sorted(pesos, reverse=True)
    # intercepto + suma de pesos = logit, y la probabilidad sale de ahí: es la que devuelve el modelo
    logit = r['intercepto_logit'] + sum(v['peso_logit'] for v in r['variables_que_mas_pesan'])
    assert logit == pytest.approx(r['logit_total'], abs=1e-3)
    assert 1 / (1 + math.exp(-r['logit_total'])) == pytest.approx(h.puntuar_online(i)['probabilidad'], abs=1e-3)
    assert r['probabilidad'] == h.puntuar_online(i)['probabilidad']
    assert all(v['efecto'] == ('sube' if v['peso_logit'] > 0 else 'baja' if v['peso_logit'] < 0 else 'neutro') for v in r['variables_que_mas_pesan'])
    # los valores son los reales del cliente, no inventados
    reales = h.puntuar_online(i)['variables']
    assert all(v['valor'] == reales[v['variable']] for v in r['variables_que_mas_pesan'])


def test_por_que_devuelve_solo_las_n_primeras(entorno_agente):
    i = ids_de(entorno_agente)[0]
    completo, corto = h.por_que(i, n=13), h.por_que(i, n=3)
    assert len(corto['variables_que_mas_pesan']) == 3 and corto['variables_totales'] == 13
    assert corto['variables_que_mas_pesan'] == completo['variables_que_mas_pesan'][:3]
    assert len(h.por_que(i, n=99)['variables_que_mas_pesan']) == 13       # más de las que hay: todas
    assert 'error' in h.por_que(i, n=0)


def test_por_que_si_el_modelo_no_permite_descomponer(entorno_agente, monkeypatch):
    monkeypatch.setattr(h, '_pesos_exactos', lambda *a, **k: None)
    i = ids_de(entorno_agente)[2]
    r = h.por_que(i)
    assert r['metodo'] == 'solo_valores' and set(r['variables']) == set(config.FEATURES) and 'no permite' in r['nota']
    assert 'variables_que_mas_pesan' not in r and r['variables'] == h.puntuar_online(i)['variables']


def test_por_que_no_se_fia_de_una_descomposicion_que_no_cuadra(entorno_agente, monkeypatch):
    real = h._pesos_exactos

    def torcida(*a, **k):
        d = real(*a, **k)
        return {**d, 'probabilidad': d['probabilidad'] + 0.05}
    monkeypatch.setattr(h, '_pesos_exactos', torcida)
    r = h.por_que(ids_de(entorno_agente)[0])
    assert r['metodo'] == 'solo_valores' and 'no reproduce' in r['nota']


def test_precargar_carga_el_modelo_o_dice_por_que_no(entorno_agente, tmp_path):
    assert h.precargar() is None
    try:
        h.configurar(ruta_db=entorno_agente.ruta_db, carpeta_modelo=tmp_path / 'sin_modelo', url_api='')
        motivo = h.precargar()
        assert 'No hay modelo' in motivo                                          # sin modelo: no lanza, lo cuenta
        assert 'No hay modelo' in h.puntuar_online(ids_de(entorno_agente)[0])['error']
    finally:
        h.configurar(ruta_db=entorno_agente.ruta_db, carpeta_modelo=entorno_agente.carpeta_modelo, url_api='')


# ----------------------------------------------------------------------------------------------------- errores y datos personales
@pytest.mark.parametrize('herramienta', [h.puntuar_bajo_demanda, h.puntuar_online, h.por_que])
@pytest.mark.parametrize('cliente', [99999999, 0, -5, 'abc', '', None])
def test_cliente_inexistente_o_no_valido_da_error_claro(entorno_agente, herramienta, cliente):
    r = herramienta(cliente)
    assert set(r) >= {'error', 'tipo'} and isinstance(r['error'], str) and len(r['error']) > 10
    assert str(entorno_agente.ruta_db.parent) not in r['error']             # sin rutas de quien lo ejecuta


def test_cliente_sin_datos_dice_que_no_esta(entorno_agente):
    assert 'fs_produccion' in h.puntuar_bajo_demanda(99999999)['error'] and h.puntuar_bajo_demanda(99999999)['tipo'] == 'sin_datos'
    assert 'no tiene compras válidas' in h.puntuar_online(99999999)['error']


def test_corte_no_valido_y_base_ausente(entorno_agente, tmp_path):
    i = ids_de(entorno_agente)[0]
    assert 'AAAA-MM-DD' in h.puntuar_online(i, corte='ayer')['error']
    assert 'error' in h.puntuar_online(i, corte='2011-02-30') and 'error' in h.puntuar_online(i, corte='2030-01-01')
    try:
        h.configurar(ruta_db=tmp_path / 'no_existe.db', carpeta_modelo=entorno_agente.carpeta_modelo, url_api='')
        for r in (h.puntuar_bajo_demanda(i), h.puntuar_online(i), h.por_que(i)):
            assert 'No existe la base' in r['error'] and str(tmp_path) not in r['error']      # una base que falta no tumba al agente
        assert not (tmp_path / 'no_existe.db').exists()                                       # y tampoco se crea vacía
    finally:
        h.configurar(ruta_db=entorno_agente.ruta_db, carpeta_modelo=entorno_agente.carpeta_modelo, url_api='')


def test_todo_es_json_y_sin_datos_personales(entorno_agente):
    i = ids_de(entorno_agente)[1]
    respuestas = [h.lista_del_dia(5), h.puntuar_bajo_demanda(i), h.puntuar_online(i), h.version_en_produccion(), h.por_que(i),
                  h.referencia_del_modelo(), h.puntuar_online(99999999)]
    for r in respuestas:
        assert json.loads(json.dumps(r)) == r
        assert not CLAVES_PERSONALES & {k.lower() for k in claves(r)}
    # y el caso no tiene esos datos: ni en MASTER (clientes) ni en la campaña
    con = sqlite3.connect(entorno_agente.ruta_db)
    try:
        columnas = {c[1].lower() for c in con.execute('PRAGMA table_info(master_clientes)')}
    finally:
        con.close()
    assert columnas and not CLAVES_PERSONALES & columnas
