"""Pruebas del alias `champion` (ia_mlops/alias_modelo.py): promover, volver atrás y cargar el modelo por alias.

MLflow escribe en una carpeta temporal (base SQLite y artefactos): nunca en models/mlflow.db. Sin red. Se registran tres versiones de
«retencion-90d» con modelos DISTINTOS (otra semilla y otros coeficientes), para que el alias se note en la probabilidad.
"""
import json
import os

import pytest

os.environ.setdefault('MLFLOW_DISABLE_AGENT_HINT', '1')

import mlflow                                                              # noqa: E402
import mlflow.sklearn                                                      # noqa: E402
import numpy as np                                                         # noqa: E402
import pandas as pd                                                        # noqa: E402
from sklearn.linear_model import LogisticRegression                        # noqa: E402
from sklearn.pipeline import make_pipeline                                 # noqa: E402
from sklearn.preprocessing import StandardScaler                           # noqa: E402

from ia_mlops import alias_modelo, config                                  # noqa: E402
from ia_mlops.alias_modelo import ErrorAlias                               # noqa: E402

NOMBRE = config.MODELO_REGISTRADO


@pytest.fixture(scope='module')
def registro(tmp_path_factory):
    """Un registro de MLflow temporal con tres versiones de «retencion-90d», cada una con un modelo distinto. Devuelve (uri, modelos)."""
    previo = mlflow.get_tracking_uri()
    carpeta = tmp_path_factory.mktemp('registro')
    uri = 'sqlite:///' + (carpeta / 'mlflow.db').as_posix()
    mlflow.set_tracking_uri(uri)
    mlflow.create_experiment('prueba-alias', artifact_location=(carpeta / 'artefactos').as_uri())   # sin esto, MLflow escribiría en ./mlruns
    mlflow.set_experiment('prueba-alias')
    modelos = {}
    for version, semilla in ((1, 1), (2, 2), (3, 3)):
        azar = np.random.default_rng(semilla)
        centro = np.array([float(ejemplo()[c]) for c in config.FEATURES])             # datos alrededor del cliente de ejemplo (así no saturan la probabilidad)
        escala = np.abs(centro) * 0.5 + 1
        X = pd.DataFrame(centro + azar.normal(size=(200, len(centro))) * escala, columns=config.FEATURES)
        y = ((X.iloc[:, semilla] - centro[semilla]) / escala[semilla] + azar.normal(scale=0.5, size=200) > 0).astype(int)   # cada versión aprende de una variable distinta
        modelo = make_pipeline(StandardScaler(), LogisticRegression()).fit(X, y)
        with mlflow.start_run(run_name=f'v{version}'):
            mlflow.log_metric('valid_auc', 0.60 + version / 100)
            mlflow.log_metric('test_auc', 0.70 + version / 100)
            info = mlflow.sklearn.log_model(modelo, name='modelo', serialization_format='cloudpickle', registered_model_name=NOMBRE)
        assert int(info.registered_model_version) == version
        modelos[version] = modelo
    yield uri, modelos
    mlflow.set_tracking_uri(previo)


@pytest.fixture()
def cliente(registro):
    """El cliente de MLflow con los alias y las etiquetas de promoción a cero antes de cada prueba."""
    uri, _ = registro
    _, c = alias_modelo.conectar(uri)
    for a in list(c.get_registered_model(NOMBRE).aliases):
        c.delete_registered_model_alias(NOMBRE, a)
    for v in c.search_model_versions(f"name='{NOMBRE}'"):
        if alias_modelo.ETIQUETA_ANTERIOR in (v.tags or {}):
            c.delete_model_version_tag(NOMBRE, v.version, alias_modelo.ETIQUETA_ANTERIOR)
    return c


def ejemplo():
    return json.loads(alias_modelo.CLIENTE_EJEMPLO.read_text(encoding='utf-8'))


def probabilidad_esperada(modelo):
    return float(modelo.predict_proba(pd.DataFrame([{c: float(ejemplo()[c]) for c in config.FEATURES}]))[:, 1][0])


# ------------------------------------------------------------------------------------------------ mostrar
def test_mostrar_lista_las_versiones_con_su_auc_y_sus_alias(cliente):
    alias_modelo.promover(cliente, 2)
    e = alias_modelo.estado(cliente)
    assert e['nombre'] == 'retencion-90d' and e['alias'] == {'champion': 2}
    assert [v['version'] for v in e['versiones']] == [1, 2, 3]
    por_version = {v['version']: v for v in e['versiones']}
    assert por_version[2]['alias'] == ['champion'] and por_version[1]['alias'] == [] and por_version[3]['alias'] == []
    assert por_version[1]['valid_auc'] == pytest.approx(0.61) and por_version[3]['test_auc'] == pytest.approx(0.73)
    texto = alias_modelo.texto_estado(e)
    assert '@champion -> v2' in texto and 'valid_auc 0.6100' in texto


def test_el_modelo_sin_registrar_da_un_error_claro(tmp_path):
    _, c = alias_modelo.conectar('sqlite:///' + (tmp_path / 'vacio.db').as_posix())
    with pytest.raises(ErrorAlias, match='no está en el registro'):
        alias_modelo.estado(c)


# ------------------------------------------------------------------------------------------------ promover
def test_promover_pone_el_alias_y_recuerda_el_champion_anterior(cliente):
    r1 = alias_modelo.promover(cliente, 1)
    assert r1 == {'nombre': NOMBRE, 'alias': 'champion', 'version': 1, 'anterior': None, 'cambio': True}
    assert alias_modelo.ETIQUETA_ANTERIOR not in (cliente.get_model_version(NOMBRE, '1').tags or {})     # no había anterior que recordar
    r2 = alias_modelo.promover(cliente, 3)
    assert r2['anterior'] == 1 and r2['version'] == 3
    assert int(cliente.get_model_version_by_alias(NOMBRE, 'champion').version) == 3
    assert cliente.get_model_version(NOMBRE, '3').tags[alias_modelo.ETIQUETA_ANTERIOR] == '1'            # la etiqueta está en la versión nueva
    assert alias_modelo.ETIQUETA_ANTERIOR not in (cliente.get_model_version(NOMBRE, '1').tags or {})


def test_promover_la_misma_version_no_pierde_a_donde_volver(cliente):
    alias_modelo.promover(cliente, 1)
    alias_modelo.promover(cliente, 2)
    r = alias_modelo.promover(cliente, 2)                                   # repetir no debe borrar «anterior = 1»
    assert r['cambio'] is False
    assert cliente.get_model_version(NOMBRE, '2').tags[alias_modelo.ETIQUETA_ANTERIOR] == '1'


def test_promover_una_version_que_no_existe_falla_y_no_mueve_nada(cliente):
    alias_modelo.promover(cliente, 1)
    with pytest.raises(ErrorAlias, match='No existe la versión 9'):
        alias_modelo.promover(cliente, 9)
    assert int(cliente.get_model_version_by_alias(NOMBRE, 'champion').version) == 1


# ------------------------------------------------------------------------------------------------ volver
def test_volver_mueve_el_puntero_atras_y_no_borra_nada(cliente):
    alias_modelo.promover(cliente, 1)
    alias_modelo.promover(cliente, 2)
    alias_modelo.promover(cliente, 3)
    r = alias_modelo.volver(cliente)
    assert r['version'] == 2 and r['retirada'] == 3
    assert int(cliente.get_model_version_by_alias(NOMBRE, 'champion').version) == 2
    assert alias_modelo.volver(cliente)['version'] == 1                     # la cadena v3 -> v2 -> v1
    assert len(cliente.search_model_versions(f"name='{NOMBRE}'")) == 3      # las tres versiones siguen registradas
    cliente.get_model_version(NOMBRE, '3')                                  # la retirada sigue ahí


def test_volver_sin_version_anterior_es_un_error_claro(cliente):
    alias_modelo.promover(cliente, 1)                                       # la primera promoción no deja nada a lo que volver
    with pytest.raises(ErrorAlias, match='no guardó una versión anterior'):
        alias_modelo.volver(cliente)
    assert int(cliente.get_model_version_by_alias(NOMBRE, 'champion').version) == 1


def test_volver_sin_alias_champion_es_un_error_claro(cliente):
    with pytest.raises(ErrorAlias, match='no tiene el alias @champion'):
        alias_modelo.volver(cliente)


# ------------------------------------------------------------------------------------------------ cargar por alias
def test_cargar_usa_el_alias_para_decidir_que_modelo_se_sirve(cliente, registro):
    _, modelos = registro
    esperadas = {v: probabilidad_esperada(m) for v, m in modelos.items()}
    assert len({round(p, 6) for p in esperadas.values()}) == 3              # la prueba solo vale si las tres versiones puntúan distinto
    alias_modelo.promover(cliente, 1)
    r1 = alias_modelo.cargar_y_puntuar(cliente, ejemplo())
    assert r1['version'] == 1 and r1['uri'] == f'models:/{NOMBRE}@champion' and r1['probabilidad'] == pytest.approx(esperadas[1])
    alias_modelo.promover(cliente, 2)
    r2 = alias_modelo.cargar_y_puntuar(cliente, ejemplo())
    assert r2['version'] == 2 and r2['probabilidad'] == pytest.approx(esperadas[2])     # el MISMO código, otro modelo: lo decide el alias
    alias_modelo.volver(cliente)
    r3 = alias_modelo.cargar_y_puntuar(cliente, ejemplo())
    assert r3['version'] == 1 and r3['probabilidad'] == pytest.approx(esperadas[1])     # tras el rollback, otra vez el de antes


def test_cargar_un_alias_que_no_existe_es_un_error_claro(cliente):
    with pytest.raises(ErrorAlias, match='no tiene el alias @champion'):
        alias_modelo.cargar_y_puntuar(cliente, ejemplo())


def test_cargar_un_cliente_incompleto_es_un_error_claro(cliente):
    alias_modelo.promover(cliente, 1)
    incompleto = {k: v for k, v in ejemplo().items() if k != 'frecuencia'}
    with pytest.raises(ErrorAlias, match='faltan variables'):
        alias_modelo.cargar_y_puntuar(cliente, incompleto)


# ------------------------------------------------------------------------------------------------ terminal
def test_la_terminal_promueve_vuelve_y_devuelve_el_codigo_de_salida(cliente, registro, capsys, tmp_path):
    uri, _ = registro
    assert alias_modelo.main(['--uri', uri, 'promover', '--version', '1']) == 0
    assert alias_modelo.main(['--uri', uri, 'promover', '--version', '2']) == 0
    assert alias_modelo.main(['--uri', uri, 'volver']) == 0
    salida = tmp_path / 'cargar.json'
    assert alias_modelo.main(['--uri', uri, 'cargar', '--alias', 'champion', '--json', str(salida)]) == 0
    assert json.loads(salida.read_text(encoding='utf-8'))['version'] == 1
    assert 'versión 1' in capsys.readouterr().out
    assert alias_modelo.main(['--uri', uri, 'volver']) == 2                 # v1 no tiene anterior
    assert 'no guardó una versión anterior' in capsys.readouterr().err
    assert alias_modelo.main(['--uri', uri, 'promover', '--version', '9']) == 2
    ruta = tmp_path / 'mostrar.json'
    assert alias_modelo.main(['--uri', uri, 'mostrar', '--json', str(ruta)]) == 0
    assert json.loads(ruta.read_text(encoding='utf-8'))['alias'] == {'champion': 1}


def test_el_almacen_por_defecto_es_el_del_curso(monkeypatch):
    monkeypatch.delenv('CURSO_MLFLOW_URI', raising=False)
    assert alias_modelo.uri_por_defecto().startswith('sqlite:///') and alias_modelo.uri_por_defecto().endswith('models/mlflow.db')
    monkeypatch.setenv('CURSO_MLFLOW_URI', 'sqlite:///otro.db')
    assert alias_modelo.uri_por_defecto() == 'sqlite:///otro.db'
