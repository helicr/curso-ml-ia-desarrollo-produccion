"""Compara en MLflow las ejecuciones de antes y después de añadir una variable, y describe la variable en ml_dataset.

Uso (desde 04-Proyecto-Base, con env-ia-mlops activado):
    python ../01-Sesiones/ejercicios/ejercicios-s1/scripts/comparar_en_mlflow.py                    # base y MLflow del proyecto
    python ../01-Sesiones/ejercicios/ejercicios-s1/scripts/comparar_en_mlflow.py --variable ratio_devoluciones
Lee las rutas de ia_mlops.config (respeta CURSO_DB y CURSO_MODELOS).
"""
import argparse
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
import mlflow  # noqa: E402
import pandas as pd  # noqa: E402

from ia_mlops import config  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('--variable', default='ratio_devoluciones')
a = ap.parse_args()
sys.stdout.reconfigure(encoding='utf-8')
pd.set_option('display.width', 220)

mlflow.set_tracking_uri('sqlite:///' + (config.MODELOS / 'mlflow.db').resolve().as_posix())
runs = mlflow.search_runs(experiment_names=[config.EXPERIMENTO_MLFLOW], order_by=['start_time ASC'])
cols = ['tags.mlflow.runName', 'params.huella_datos', 'params.n_variables', 'metrics.train_auc', 'metrics.valid_auc',
        'metrics.test_auc', 'metrics.test_precision_media']
print(runs[[c for c in cols if c in runs.columns]].round(4).to_string(index=False))
for v in mlflow.MlflowClient().search_model_versions(f"name='{config.MODELO_REGISTRADO}'"):
    print('versión', v.version, '· huella', v.tags.get('huella_datos'), '· valid_auc', v.tags.get('valid_auc'))

con = sqlite3.connect(config.DB)
columnas = [c[1] for c in con.execute('PRAGMA table_info(ml_dataset)')]
if a.variable in columnas:
    ml = pd.read_sql(f'SELECT particion, y, devoluciones, {a.variable} FROM ml_dataset', con)
    train = ml[ml.particion == 'train']
    print(f'\n{a.variable} por partición:')
    print(ml.groupby('particion')[a.variable].describe().round(3).to_string())
    print(f'tasa de recompra en train según {a.variable} > 0:', train.groupby(train[a.variable] > 0)['y'].mean().round(3).to_dict())
    print('correlación con devoluciones (train):', round(train[[a.variable, 'devoluciones']].corr().iloc[0, 1], 3))
else:
    print(f'\n{a.variable} no está en ml_dataset (¿has deshecho el cambio?)')
