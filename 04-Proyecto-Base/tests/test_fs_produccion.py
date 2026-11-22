"""Pruebas de la FS de producción (ia_mlops/fs_produccion.py): el corte que puntúa `explotacion` queda guardado y se puede leer."""
import shutil
import sqlite3

import pandas as pd
import pytest

from ia_mlops import config, explotacion as ex, fs_produccion as fsp


@pytest.fixture()
def con_copia(ruta_db, tmp_path):
    """Una COPIA de la base analítica: lo que se escribe aquí no llega a la base compartida de las demás pruebas."""
    copia = tmp_path / 'copia.db'
    shutil.copyfile(ruta_db, copia)
    con = sqlite3.connect(copia)
    yield con
    con.close()


@pytest.fixture()
def referencia_v7(tmp_path, monkeypatch):
    """Una referencia.json distinta de la real, para comprobar que la versión y la huella salen de ella."""
    import json
    ref = json.loads(config.REFERENCIA.read_text(encoding='utf-8'))
    ref.update(version=7, huella_datos='abc123', etiqueta_imagen='retencion-api:v7-abc123')
    ruta = tmp_path / 'referencia.json'
    ruta.write_text(json.dumps(ref), encoding='utf-8')
    monkeypatch.setattr(config, 'REFERENCIA', ruta)
    return ruta


def test_el_esquema_es_el_acordado(con_copia):
    fsp.crear_tabla(con_copia)
    info = con_copia.execute(f'PRAGMA table_info({fsp.TABLA})').fetchall()
    assert [f[1] for f in info] == ['cliente_id', 'fecha_corte', *config.FEATURES, 'huella_modelo', 'version_modelo', 'creado_en']
    tipos = {f[1]: f[2] for f in info}
    assert tipos['cliente_id'] == 'INTEGER' and tipos['fecha_corte'] == 'TEXT' and tipos['version_modelo'] == 'INTEGER'
    assert tipos['huella_modelo'] == 'TEXT' and tipos['creado_en'] == 'TEXT'
    clave = sorted((f[5], f[1]) for f in info if f[5])
    assert clave == [(1, 'cliente_id'), (2, 'fecha_corte')]


def test_se_escribe_el_corte_con_version_y_huella_de_la_referencia(con_copia, carpeta_modelo, referencia_v7):
    tabla, r = ex.campana(con_copia, carpeta_modelo=carpeta_modelo, guardar=False)
    fs = fsp.leer_fs_produccion(con_copia)
    assert len(fs) == r['clientes_puntuados'] == r['fs_produccion']['filas']
    assert set(fs['fecha_corte']) == {r['corte']}
    assert set(fs['version_modelo']) == {7} and set(fs['huella_modelo']) == {'abc123'}
    assert fs['creado_en'].str.match(r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d$').all()
    # las variables guardadas son las mismas que calcula el SQL de FS para ese corte
    calculadas = ex.variables_en_corte(con_copia, r['corte']).set_index('cliente_id')[config.FEATURES]
    pd.testing.assert_frame_equal(fs.set_index('cliente_id')[config.FEATURES], calculadas, check_dtype=False)


def test_reescribir_el_mismo_corte_no_duplica(con_copia, carpeta_modelo):
    _, r = ex.campana(con_copia, carpeta_modelo=carpeta_modelo, guardar=False)
    ex.campana(con_copia, carpeta_modelo=carpeta_modelo, guardar=False)
    n, distintos = con_copia.execute(f'SELECT COUNT(*), COUNT(DISTINCT cliente_id || fecha_corte) FROM {fsp.TABLA}').fetchone()
    assert n == distintos == r['clientes_puntuados']


def test_sin_guardar_fs_no_escribe(con_copia, carpeta_modelo):
    _, r = ex.campana(con_copia, carpeta_modelo=carpeta_modelo, guardar=False, guardar_fs=False)
    assert r['fs_produccion'] is None
    assert fsp.leer_fs_produccion(con_copia).empty
    assert fsp.ultimo_corte(con_copia) is None


def test_sin_referencia_version_y_huella_son_nulas(con_copia, carpeta_modelo, tmp_path, monkeypatch):
    monkeypatch.setattr(config, 'REFERENCIA', tmp_path / 'no_existe.json')
    ex.campana(con_copia, carpeta_modelo=carpeta_modelo, guardar=False)
    fs = fsp.leer_fs_produccion(con_copia)
    assert not fs.empty and fs['version_modelo'].isna().all() and fs['huella_modelo'].isna().all()


def test_se_lee_el_ultimo_corte_y_se_puede_pedir_uno_concreto(con_copia, carpeta_modelo):
    ex.campana(con_copia, corte='2011-09-01', carpeta_modelo=carpeta_modelo, guardar=False)
    ex.campana(con_copia, corte='2011-10-01', carpeta_modelo=carpeta_modelo, guardar=False)
    assert fsp.ultimo_corte(con_copia) == '2011-10-01'
    assert set(fsp.leer_fs_produccion(con_copia)['fecha_corte']) == {'2011-10-01'}
    assert set(fsp.leer_fs_produccion(con_copia, corte='2011-09-01')['fecha_corte']) == {'2011-09-01'}
    # escribir otro corte no borra los anteriores; reescribir uno solo reemplaza ese
    ex.campana(con_copia, corte='2011-10-01', carpeta_modelo=carpeta_modelo, guardar=False)
    assert con_copia.execute(f'SELECT COUNT(DISTINCT fecha_corte) FROM {fsp.TABLA}').fetchone()[0] == 2


def test_leer_por_clientes_y_cliente_inexistente(con_copia, carpeta_modelo):
    ex.campana(con_copia, carpeta_modelo=carpeta_modelo, guardar=False)
    todos = fsp.leer_fs_produccion(con_copia)
    ids = todos['cliente_id'].iloc[:3].tolist()
    algunos = fsp.leer_fs_produccion(con_copia, cliente_ids=ids)
    assert algunos['cliente_id'].tolist() == sorted(ids)
    # un cliente que no existe simplemente no aparece (no es un error)
    mezcla = fsp.leer_fs_produccion(con_copia, cliente_ids=[ids[0], 99999999])
    assert mezcla['cliente_id'].tolist() == [ids[0]]
    assert fsp.leer_fs_produccion(con_copia, cliente_ids=[99999999]).empty
    assert fsp.leer_fs_produccion(con_copia, cliente_ids=[]).empty
    assert list(fsp.leer_fs_produccion(con_copia, cliente_ids=[99999999]).columns) == fsp.COLUMNAS


def test_sin_tabla_o_con_corte_inexistente_devuelve_vacio(con_copia, carpeta_modelo):
    assert fsp.leer_fs_produccion(con_copia).empty and fsp.leer_fs_produccion(con_copia, corte='2011-01-01').empty
    ex.campana(con_copia, carpeta_modelo=carpeta_modelo, guardar=False)
    assert fsp.leer_fs_produccion(con_copia, corte='1999-01-01').empty


def test_la_migracion_no_trata_fs_produccion_como_capa_analitica(con_copia, carpeta_modelo):
    from ia_mlops.migracion import fuentes
    ex.campana(con_copia, carpeta_modelo=carpeta_modelo, guardar=False)
    tablas = [f[0] for f in con_copia.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
    assert fsp.TABLA in tablas
    assert fsp.TABLA in fuentes.TABLAS_EXCLUIDAS
    assert fsp.TABLA not in fuentes.seleccionar(tablas)               # por prefijo: no entra
    assert fsp.TABLA in fuentes.seleccionar(tablas, tablas=[fsp.TABLA])  # pedida por nombre: sí


def test_explotacion_reexporta_la_lectura():
    assert ex.leer_fs_produccion is fsp.leer_fs_produccion
