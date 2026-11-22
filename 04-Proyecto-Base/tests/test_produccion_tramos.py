"""Pruebas de lo que usa nueva-version.yml: la fuente de datos anotada en la referencia, la decisión en JSON y la comparación
campeón/candidata por tramos (ia_mlops/produccion.py)."""
import json

import joblib
import pandas as pd
import pytest
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from ia_mlops import config, produccion
from ia_mlops.produccion import ErrorReferencia


@pytest.fixture()
def referencia():
    meta = {'modelo': 'regresion_logistica', 'huella_datos': 'aaaaaaaaaaaaaaaa', 'entrenado_en': '2026-01-01T10:00:00',
            'metricas_valid': {'auc': 0.70}, 'metricas_test': {'auc': 0.75, 'precision_media': 0.66},
            'cortes': {'test': ['2011-06-01', '2011-09-01']}}
    return produccion.crear_referencia(meta, version=1, aprobado_en='2026-01-02T09:00:00')


# ------------------------------------------------------------------------------------------------ fuente de datos
def test_sin_fuente_se_entiende_muestra(referencia):
    assert 'fuente_datos' not in referencia
    assert produccion.fuente_de(referencia) == 'muestra'


def test_la_fuente_se_anota_y_se_valida(referencia):
    meta = {'modelo': 'm', 'huella_datos': 'bbbb', 'entrenado_en': 'x', 'metricas_valid': {'auc': 1}, 'metricas_test': {'auc': 0.7},
            'cortes': {'test': ['2011-06-01']}}
    d = produccion.crear_referencia(meta, version=2, fuente='completo')
    assert d['fuente_datos'] == 'completo' and produccion.fuente_de(d) == 'completo'
    d['fuente_datos'] = 'inventada'
    with pytest.raises(ErrorReferencia, match='fuente_datos'):
        produccion.validar_referencia(d)


def test_cli_crear_con_fuente(tmp_path, monkeypatch, referencia):
    """`crear --fuente completo` deja la clave en el archivo (con los metadatos y métricas que deja un entrenamiento)."""
    modelos, reportes = tmp_path / 'models', tmp_path / 'reports'
    modelos.mkdir(), reportes.mkdir()
    meta = {'modelo': 'm', 'huella_datos': 'cccc', 'entrenado_en': 'x', 'metricas_valid': {'auc': 0.7},
            'cortes': {'test': ['2011-06-01', '2011-09-01']}}
    (modelos / 'metadatos.json').write_text(json.dumps(meta), encoding='utf-8')
    (reportes / 'metricas.json').write_text(json.dumps({'mejor': 'm', 'modelos': {'m': {'test': {'auc': 0.71}}}}), encoding='utf-8')
    monkeypatch.setattr(config, 'MODELOS', modelos)
    monkeypatch.setattr(config, 'REPORTES', reportes)
    ruta = tmp_path / 'referencia.json'
    assert produccion.main(['--ruta', str(ruta), 'crear', '--version', '2', '--fuente', 'completo']) == 0
    d = produccion.leer_referencia(ruta)
    assert d['version'] == 2 and d['fuente_datos'] == 'completo' and d['etiqueta_imagen'] == 'retencion-api:v2-cccc'


# ------------------------------------------------------------------------------------------------ decisión en JSON
def test_comparar_guarda_la_decision_en_json(tmp_path, referencia, monkeypatch, capsys):
    ruta = tmp_path / 'referencia.json'
    produccion.escribir_referencia(referencia, ruta)
    candidata = tmp_path / 'candidata.json'
    candidata.write_text(json.dumps({'huella_datos': 'bbbb', 'metricas_test': {'auc': 0.60}, 'cortes': {'test': referencia['cortes_test']}}), encoding='utf-8')
    salida = tmp_path / 'decision.json'
    assert produccion.main(['--ruta', str(ruta), 'comparar', '--metricas', str(candidata), '--json', str(salida)]) == 1
    d = json.loads(salida.read_text(encoding='utf-8'))
    assert d['decision'] == 'rechazada' and d['version_referencia'] == 1 and d['fuente_referencia'] == 'muestra'
    assert d['metricas_test_referencia']['auc'] == 0.75 and d['metricas_test_candidata']['auc'] == 0.60
    assert d['huella_referencia'] == 'aaaaaaaaaaaaaaaa' and d['huella_candidata'] == 'bbbb'


def test_tolerancia_negativa_es_una_exigencia_de_mejora(tmp_path, referencia, capsys):
    """Con -0.10 la versión nueva debe MEJORAR al menos 0.10: una que mejora 0.05 se rechaza (así se ensaya el rechazo con datos que mejoran)."""
    ruta = tmp_path / 'referencia.json'
    produccion.escribir_referencia(referencia, ruta)
    candidata = tmp_path / 'candidata.json'
    candidata.write_text(json.dumps({'huella_datos': 'bbbb', 'metricas_test': {'auc': 0.80}, 'cortes': {'test': referencia['cortes_test']}}), encoding='utf-8')
    base = ['--ruta', str(ruta), 'comparar', '--metricas', str(candidata)]
    assert produccion.main(base + ['--tolerancia', '-0.10']) == 1
    assert 'RECHAZADA' in capsys.readouterr().out
    assert produccion.main(base + ['--tolerancia', '-0.04']) == 0
    assert 'ACEPTADA' in capsys.readouterr().out


# ------------------------------------------------------------------------------------------------ campeón y candidata
@pytest.fixture()
def datos_test(con):
    """Las filas de test de ml_dataset de la muestra (la fuente que usa el resto de pruebas)."""
    return pd.read_sql("SELECT * FROM ml_dataset WHERE particion = 'test'", con)


def _guardar_modelo(carpeta, datos, c):
    """Un modelo sencillo entrenado con `datos` (regularización `c`), guardado como lo guarda train.py: models/modelo.joblib."""
    modelo = make_pipeline(SimpleImputer(strategy='median'), StandardScaler(), LogisticRegression(C=c, max_iter=1000))
    modelo.fit(datos[config.FEATURES].astype(float), datos[config.OBJETIVO])
    carpeta.mkdir(parents=True, exist_ok=True)
    joblib.dump(modelo, carpeta / 'modelo.joblib')
    return carpeta


def test_el_mismo_modelo_no_cambia_a_nadie_de_tramo(tmp_path, datos_test):
    datos = datos_test.fillna(0)
    carpeta = _guardar_modelo(tmp_path / 'a', datos, 1.0)
    r = produccion.comparar_tramos(carpeta, carpeta, datos)
    assert r['cambian'] == 0 and r['pct_cambian'] == 0.0 and r['dif_abs_max'] == 0.0
    assert r['filas'] == len(datos) and r['cortes'] == config.CORTES['test']
    assert sum(sum(fila.values()) for fila in r['matriz'].values()) == len(datos)
    assert r['auc_referencia'] == r['auc_candidata']


def test_dos_modelos_distintos_cambian_a_algunos_de_tramo(tmp_path, datos_test):
    datos = datos_test.fillna(0)
    ref = _guardar_modelo(tmp_path / 'ref', datos, 1.0)
    cand = _guardar_modelo(tmp_path / 'cand', datos.assign(**{config.OBJETIVO: 1 - datos[config.OBJETIVO]}), 1.0)   # aprende lo contrario
    r = produccion.comparar_tramos(ref, cand, datos)
    assert r['cambian'] > 0 and r['cambian'] == r['suben'] + r['bajan']
    assert sum(v['cambian'] for v in r['por_corte'].values()) == r['cambian']
    fuera_de_la_diagonal = sum(n for a, fila in r['matriz'].items() for b, n in fila.items() if a != b)
    assert fuera_de_la_diagonal == r['cambian']
    assert r['auc_candidata'] < r['auc_referencia']        # la que aprende lo contrario es peor sobre las mismas filas
    md = produccion.resumen_tramos_md(r, 1, 2)
    assert 'cambian de tramo' in md and 'v1' in md and 'v2' in md and 'AUC sobre estas mismas filas' in md


@pytest.mark.parametrize('p, esperado', [(0.95, 'alta'), (0.70, 'alta'), (0.69, 'media'), (0.40, 'media'), (0.39, 'baja'), (0.0, 'baja')])
def test_tramo_usa_los_umbrales_de_config(p, esperado):
    assert produccion.tramo(p) == esperado


def test_sin_modelo_o_sin_filas_da_error_claro(tmp_path, datos_test):
    with pytest.raises(ErrorReferencia, match='modelo.joblib'):
        produccion.comparar_tramos(tmp_path / 'no', tmp_path / 'no', datos_test)
    with pytest.raises(ErrorReferencia, match='No hay filas'):
        produccion.comparar_tramos(tmp_path, tmp_path, datos_test.iloc[0:0])


def test_exportar_test_y_cli_comparar_tramos(tmp_path, con, datos_test, capsys):
    csv = produccion.exportar_test(tmp_path / 'sub' / 'test.csv', con)
    leido = pd.read_csv(csv)
    assert len(leido) == len(datos_test) and set(leido['particion']) == {'test'}
    carpeta = _guardar_modelo(tmp_path / 'm', datos_test, 1.0)      # el modelo imputa lo que falte, como el real
    salida, md = tmp_path / 'tramos.json', tmp_path / 'tramos.md'
    assert produccion.main(['comparar-tramos', '--referencia', str(carpeta), '--candidata', str(carpeta), '--datos', str(csv),
                            '--salida', str(salida), '--markdown', str(md)]) == 0
    assert json.loads(salida.read_text(encoding='utf-8'))['cambian'] == 0
    assert 'cambian de tramo' in md.read_text(encoding='utf-8')
    assert produccion.main(['comparar-tramos', '--referencia', str(carpeta), '--datos', str(tmp_path / 'no.csv')]) == 2
