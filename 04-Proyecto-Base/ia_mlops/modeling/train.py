"""Entrenamiento y evaluacion, con seguimiento en MLflow.

Es la traduccion a Python de  notebooks/04_entrenamiento_y_seguimiento.ipynb.

METODO
    1. Cada modelo se entrena con train.  2. Se comparan con valid y se elige el de mayor AUC.
    3. El elegido se mide en test UNA vez (test no se usa para elegir: dejaria de ser un examen sorpresa).

MODELOS
    referencia_sin_aprender  da a todos la tasa base de train (AUC 0,5): el minimo que hay que superar.
    regresion_logistica      suma ponderada de variables -> probabilidad. Va en un Pipeline con imputar (mediana),
                             log1p (comprime variables asimetricas) y escalar: el preprocesamiento viaja DENTRO del modelo,
                             asi la API aplica exactamente el mismo.
    gradient_boosting        muchos arboles pequenos en secuencia; cada uno corrige los errores de los anteriores.

METRICAS (evaluar)
    auc                      probabilidad de puntuar mas alto a un cliente que si compro que a uno que no (0,5 azar, 1 perfecto).
    precision_media          calidad del orden mirando los positivos; se compara con tasa_base.
    aciertos_en_el_10_mejor  de los clientes con el 10 % de probabilidades mas altas, cuantos compraron de verdad.

MLFLOW: el cuaderno de laboratorio del proyecto
    experimento   agrupa todos los intentos de un mismo problema: 'retencion-90d'.
    ejecucion     (run) un entrenamiento concreto: una por modelo, mas 'MEJOR-<modelo>' para el elegido.
    parametros    lo que se decide ANTES de entrenar (modelo, ventana, n_variables, huella_datos).
    metricas      lo que se mide DESPUES, con el prefijo de la particion (valid_auc, test_auc...).
    artefactos    archivos de la ejecucion: el modelo del mejor, con su firma (columnas de entrada y salida).
    Donde se guarda: models/mlflow.db (backend store: experimentos, ejecuciones, parametros y metricas; es el tracking URI
    'sqlite:///models/mlflow.db') y models/mlartifacts/ (artifact store: los archivos). Para verlo en el navegador:
        mlflow ui --backend-store-uri sqlite:///models/mlflow.db      (anade --port 5001 si el 5000 esta ocupado)

SALIDAS
  models/modelo.joblib       el modelo completo (preprocesamiento + clasificador), el que carga predict.py
  models/modelo_mlflow/      el mismo modelo en formato MLflow, con su FIRMA (el contrato de entrada que usa la API de S2)
  models/metadatos.json      variables, particiones, huella de los datos, rangos de train, versiones de librerias (para reproducir)
  models/mlflow.db          seguimiento de MLflow (y models/mlartifacts/ con los modelos registrados)
  reports/metricas.json      metricas de todos los modelos

Uso:  python -m ia_mlops.modeling.train
"""
import hashlib
import json
import platform
import shutil
import sys
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

from .. import config, db


def cargar_datos(con):
    """Lee ml_dataset y lo separa por particion (sin mezclar filas entre particiones). Devuelve (partes, tabla completa)."""
    df = pd.read_sql('SELECT * FROM ml_dataset', con)
    return {p: df[df['particion'] == p].reset_index(drop=True) for p in ('train', 'valid', 'test')}, df


def huella_datos(df):
    """Huella del dataset: identifica con que datos se entreno el modelo."""
    h = hashlib.sha256(pd.util.hash_pandas_object(df.sort_values(['cliente_id', 'fecha_corte']), index=False).values.tobytes())
    return h.hexdigest()[:16]


def modelos():
    """Los tres modelos a comparar, sin entrenar. El preprocesamiento de la regresion logistica va dentro de su Pipeline."""
    log1p = FunctionTransformer(np.log1p, feature_names_out='one-to-one')
    return {
        'referencia_sin_aprender': DummyClassifier(strategy='prior'),
        'regresion_logistica': Pipeline([('imputar', SimpleImputer(strategy='median')), ('log', log1p),
                                         ('escalar', StandardScaler()), ('modelo', LogisticRegression(max_iter=1000))]),
        'gradient_boosting': HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, random_state=0),
    }


def evaluar(modelo, X, y):
    """Metricas de un modelo ya entrenado sobre una particion (ver METRICAS en la cabecera del modulo)."""
    prob = modelo.predict_proba(X)[:, 1]
    corte = max(1, int(round(len(y) * 0.10)))
    top = np.argsort(-prob)[:corte]
    return {
        'auc': float(roc_auc_score(y, prob)),
        'precision_media': float(average_precision_score(y, prob)),
        'tasa_base': float(np.mean(y)),
        'aciertos_en_el_10_mejor': float(np.mean(np.asarray(y)[top])),
    }


def exportar_modelo_mlflow(modelo, muestra, destino):
    """Guarda el modelo en formato MLflow: una carpeta autocontenida con MLmodel, firma y ejemplo de entrada.

    Es lo que carga la API y lo que se copia a la imagen Docker. La FIRMA (nombre y tipo de cada variable) viaja dentro del modelo.
    """
    import mlflow.models
    import mlflow.sklearn
    if destino.exists():
        shutil.rmtree(destino)
    firma = mlflow.models.infer_signature(muestra, modelo.predict_proba(muestra)[:, 1])
    # cloudpickle evita la verificacion de tipos de skops que MLflow 3 aplica a los arboles de scikit-learn.
    mlflow.sklearn.save_model(modelo, str(destino), signature=firma, serialization_format='cloudpickle', input_example=muestra.head(3))


def rangos_de_entrenamiento(X):
    """Minimo y maximo de cada variable en train. La API avisa (no rechaza) cuando llega algo fuera de ese rango."""
    return {c: [float(X[c].min()), float(X[c].max())] for c in X.columns}


def entrenar(con=None, usar_mlflow=True, verbose=True):
    """Entrena y compara los modelos, registra cada uno como ejecucion de MLflow y guarda el mejor con sus metadatos."""
    cierre = con is None
    con = con or db.conectar()
    partes, df = cargar_datos(con)
    X = {k: v[config.FEATURES] for k, v in partes.items()}
    y = {k: v[config.OBJETIVO] for k, v in partes.items()}
    for k in ('train', 'valid', 'test'):
        if len(partes[k]) == 0 or y[k].nunique() < 2:
            raise RuntimeError(f'La particion {k} esta vacia o tiene una sola clase: revisa los cortes de config.py.')

    # MLflow: donde escribir (tracking URI) y en que experimento. El experimento se crea la primera vez con su carpeta de artefactos.
    mlflow = None
    if usar_mlflow:
        import mlflow
        import mlflow.sklearn
        config.MODELOS.mkdir(parents=True, exist_ok=True)
        mlflow.set_tracking_uri('sqlite:///' + (config.MODELOS / 'mlflow.db').as_posix())
        nombre = 'retencion-90d'
        if mlflow.get_experiment_by_name(nombre) is None:
            mlflow.create_experiment(nombre, artifact_location=(config.MODELOS / 'mlartifacts').resolve().as_uri())
        mlflow.set_experiment(nombre)

    resultados, ajustados = {}, {}
    for nombre_modelo, modelo in modelos().items():
        modelo.fit(X['train'], y['train'])
        metricas = {p: evaluar(modelo, X[p], y[p]) for p in ('train', 'valid', 'test')}
        resultados[nombre_modelo], ajustados[nombre_modelo] = metricas, modelo
        if verbose:
            print(f'  {nombre_modelo:26s} AUC valid {metricas["valid"]["auc"]:.3f} | test {metricas["test"]["auc"]:.3f}'
                  f' | precision media test {metricas["test"]["precision_media"]:.3f}')
        if mlflow:   # una ejecucion por modelo: parametros (lo decidido) y metricas (lo medido)
            with mlflow.start_run(run_name=nombre_modelo):
                mlflow.log_param('modelo', nombre_modelo)
                mlflow.log_param('ventana_objetivo_dias', config.VENTANA_OBJETIVO_DIAS)
                mlflow.log_param('n_variables', len(config.FEATURES))
                mlflow.log_param('huella_datos', huella_datos(df))
                for p, m in metricas.items():
                    for k, v in m.items():
                        mlflow.log_metric(f'{p}_{k}', v)

    # Se elige con VALID (nunca con test). La referencia solo sirve de minimo.
    mejor = max((n for n in resultados if n != 'referencia_sin_aprender'), key=lambda n: resultados[n]['valid']['auc'])
    modelo = ajustados[mejor]

    if mlflow:   # el elegido se registra con el modelo como artefacto, su firma y un ejemplo de entrada
        with mlflow.start_run(run_name=f'MEJOR-{mejor}'):
            mlflow.log_param('modelo', mejor)
            mlflow.log_param('huella_datos', huella_datos(df))
            for p, m in resultados[mejor].items():
                for k, v in m.items():
                    mlflow.log_metric(f'{p}_{k}', v)
            firma = mlflow.models.infer_signature(X['train'].head(200), modelo.predict_proba(X['train'].head(200))[:, 1])
            # cloudpickle evita la verificacion de tipos de skops que MLflow 3 aplica a los arboles de scikit-learn.
            mlflow.sklearn.log_model(modelo, name='modelo', signature=firma, serialization_format='cloudpickle',
                                     input_example=X['train'].head(3))

    config.MODELOS.mkdir(parents=True, exist_ok=True)
    config.REPORTES.mkdir(parents=True, exist_ok=True)
    joblib.dump(modelo, config.MODELOS / 'modelo.joblib')
    exportar_modelo_mlflow(modelo, X['train'].head(200), config.MODELOS / config.CARPETA_MODELO_MLFLOW)
    metadatos = {
        'modelo': mejor,
        'objetivo': 'el cliente compra al menos una vez en los siguientes %d dias' % config.VENTANA_OBJETIVO_DIAS,
        'variables': config.FEATURES,
        'cortes': config.CORTES,
        'filas': {k: int(len(v)) for k, v in partes.items()},
        'huella_datos': huella_datos(df),
        'metricas_valid': resultados[mejor]['valid'],
        'rangos_entrenamiento': rangos_de_entrenamiento(X['train']),
        'entrenado_en': datetime.now().isoformat(timespec='seconds'),
        'versiones': {'python': sys.version.split()[0], 'scikit-learn': sklearn.__version__, 'pandas': pd.__version__,
                      'numpy': np.__version__, 'plataforma': platform.system()},
    }
    (config.MODELOS / 'metadatos.json').write_text(json.dumps(metadatos, indent=2, ensure_ascii=False), encoding='utf-8')
    (config.REPORTES / 'metricas.json').write_text(json.dumps({'mejor': mejor, 'modelos': resultados}, indent=2), encoding='utf-8')
    if verbose:
        print(f'  Mejor modelo: {mejor}. Guardado en {config.MODELOS / "modelo.joblib"}')
    if cierre:
        con.close()
    return {'mejor': mejor, 'metricas': resultados, 'metadatos': metadatos}


if __name__ == '__main__':
    entrenar()
