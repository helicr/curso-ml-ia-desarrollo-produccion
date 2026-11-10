"""Pruebas del entrenamiento, los artefactos y la prediccion."""
import json

import joblib
import pytest

from ia_mlops import config
from ia_mlops.modeling import predict, train


def test_entrena_y_guarda_los_artefactos(con, salidas_tmp):
    r = train.entrenar(con, usar_mlflow=False, verbose=False)
    assert r['mejor'] in ('regresion_logistica', 'gradient_boosting')
    modelo = joblib.load(salidas_tmp / 'models' / 'modelo.joblib')
    X = train.cargar_datos(con)[0]['test'][config.FEATURES]
    prob = modelo.predict_proba(X)
    assert prob.shape == (len(X), 2) and ((prob >= 0) & (prob <= 1)).all()
    meta = json.loads((salidas_tmp / 'models' / 'metadatos.json').read_text(encoding='utf-8'))
    assert meta['variables'] == config.FEATURES and len(meta['huella_datos']) == 16
    metricas = json.loads((salidas_tmp / 'reports' / 'metricas.json').read_text(encoding='utf-8'))
    assert metricas['mejor'] == r['mejor']


def test_la_referencia_sin_aprender_tiene_auc_de_azar(con, salidas_tmp):
    r = train.entrenar(con, usar_mlflow=False, verbose=False)
    assert abs(r['metricas']['referencia_sin_aprender']['test']['auc'] - 0.5) < 1e-9


def test_la_huella_de_los_datos_es_estable(con):
    _, df = train.cargar_datos(con)
    assert train.huella_datos(df) == train.huella_datos(df.sample(frac=1, random_state=1))


def test_entrena_registrando_en_mlflow(con, salidas_tmp):
    r = train.entrenar(con, usar_mlflow=True, verbose=False)
    assert (salidas_tmp / 'models' / 'mlflow.db').exists()
    import mlflow
    mlflow.set_tracking_uri('sqlite:///' + (salidas_tmp / 'models' / 'mlflow.db').as_posix())
    runs = mlflow.search_runs(experiment_names=['retencion-90d'])
    assert len(runs) >= 4          # tres modelos + el mejor
    assert r['mejor'] in ' '.join(runs['tags.mlflow.runName'].astype(str))


def test_predice_una_probabilidad_para_un_cliente(con, salidas_tmp):
    train.entrenar(con, usar_mlflow=False, verbose=False)
    predict._CACHE.clear()
    cliente = con.execute("SELECT cliente_id FROM fs_cliente_corte WHERE fecha_corte = '2011-09-01' LIMIT 1").fetchone()[0]
    p = predict.predecir_cliente(cliente, '2011-09-01', con=con)
    assert 0.0 <= p <= 1.0


def test_predecir_acepta_un_diccionario_sin_importar_el_orden(con, salidas_tmp):
    train.entrenar(con, usar_mlflow=False, verbose=False)
    predict._CACHE.clear()
    fila = con.execute(f"SELECT {', '.join(config.FEATURES)} FROM fs_cliente_corte LIMIT 1").fetchone()
    datos = dict(zip(config.FEATURES, fila))
    invertido = dict(reversed(list(datos.items())))
    assert predict.predecir_probabilidad(datos) == pytest.approx(predict.predecir_probabilidad(invertido))


def test_predecir_avisa_si_faltan_variables(con, salidas_tmp):
    train.entrenar(con, usar_mlflow=False, verbose=False)
    predict._CACHE.clear()
    with pytest.raises(predict.VariablesFaltantesError):
        predict.predecir_probabilidad({'frecuencia': 3})
