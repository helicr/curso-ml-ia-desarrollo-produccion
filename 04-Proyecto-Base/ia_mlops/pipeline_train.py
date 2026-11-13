"""Pipeline de ENTRENAMIENTO: ML -> modelos comparados, el mejor guardado y todo registrado en MLflow.

Cuaderno equivalente: notebooks/04_entrenamiento_y_seguimiento.ipynb.
Entrada: ml_dataset (lo produce pipeline_ml).
Salida:  models/modelo.joblib, models/modelo_mlflow/ (con su firma: lo que sirve la API de S2), models/metadatos.json,
         reports/metricas.json y, en MLflow, una ejecucion por modelo + MEJOR-<modelo>.

Idempotente (ver control.py): la huella de entrada es la huella de los datos de entrenamiento (huella_datos) + las variables,
el objetivo, los cortes y la ventana + el codigo de entrenamiento. Si nada cambio y el modelo guardado corresponde a esos datos,
NO vuelve a entrenar: asi no se acumulan en MLflow ejecuciones repetidas que no aportan nada. Con --forzar entrena igualmente.

Uso (desde 04-Proyecto-Base):
    python -m ia_mlops.pipeline_train
    python -m ia_mlops.pipeline_train --forzar
    python -m ia_mlops.pipeline_train --sin-mlflow
"""
import argparse
import json

import pandas as pd

from . import config, control, db
from .modeling import train

PIPELINE = 'pipeline_train'
ENTRADA = ['ml_dataset']


def huella_entrada(con, usar_mlflow):
    datos = train.huella_datos(pd.read_sql('SELECT * FROM ml_dataset', con))
    return control.huella(datos, config.FEATURES, config.OBJETIVO, config.CORTES, config.VENTANA_OBJETIVO_DIAS,
                          control.huella_codigo(train), usar_mlflow), datos


def salida_ok(huella_datos, usar_mlflow):
    """El modelo guardado existe y se entreno con estos mismos datos."""
    meta = config.MODELOS / 'metadatos.json'
    if not ((config.MODELOS / 'modelo.joblib').exists() and meta.exists() and (config.REPORTES / 'metricas.json').exists()
            and (config.MODELOS / config.CARPETA_MODELO_MLFLOW / 'MLmodel').exists()):
        return False
    if usar_mlflow and not (config.MODELOS / 'mlflow.db').exists():
        return False
    return json.loads(meta.read_text(encoding='utf-8')).get('huella_datos') == huella_datos


def ejecutar(ruta_db=None, forzar=False, usar_mlflow=True, verbose=True):
    con = db.conectar(ruta_db)
    try:
        control.exigir(con, ENTRADA, 'pipeline_ml')
        huella, huella_datos = huella_entrada(con, usar_mlflow)

        def trabajo():
            r = train.entrenar(con, usar_mlflow, verbose)
            m = r['metricas'][r['mejor']]
            return {'mejor': r['mejor'], 'valid_auc': m['valid']['auc'], 'test_auc': m['test']['auc'], 'huella_datos': huella_datos}
        return control.ejecutar(con, PIPELINE, huella, lambda: salida_ok(huella_datos, usar_mlflow), trabajo, forzar, verbose)
    finally:
        con.close()


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--forzar', action='store_true', help='entrena aunque los datos y el codigo no hayan cambiado')
    ap.add_argument('--sin-mlflow', action='store_true', help='entrena sin registrar en MLflow')
    a = ap.parse_args()
    control.desde_terminal(ejecutar, forzar=a.forzar, usar_mlflow=not a.sin_mlflow)
