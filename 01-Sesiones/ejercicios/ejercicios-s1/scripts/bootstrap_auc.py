"""¿La mejora de AUC es mayor que el ruido? Compara dos versiones del modelo registrado con un bootstrap pareado.

Uso (desde 04-Proyecto-Base, con env-ia-mlops activado y la variable aplicada):
    python ../01-Sesiones/ejercicios/ejercicios-s1/scripts/bootstrap_auc.py --antes 1 --despues 2
Carga models:/retencion-90d/<versión> del MLflow del proyecto y puntúa las filas de valid y test de ml_dataset.
Cada modelo usa sus propias variables (feature_names_in_), así se comparan uno sin y otro con la variable nueva.
"""
import argparse
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
import mlflow  # noqa: E402
import mlflow.sklearn  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402

from ia_mlops import config  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('--antes', default='1')
ap.add_argument('--despues', default='2')
ap.add_argument('--remuestreos', type=int, default=2000)
a = ap.parse_args()
sys.stdout.reconfigure(encoding='utf-8')

mlflow.set_tracking_uri('sqlite:///' + (config.MODELOS / 'mlflow.db').resolve().as_posix())
m1 = mlflow.sklearn.load_model(f'models:/{config.MODELO_REGISTRADO}/{a.antes}')
m2 = mlflow.sklearn.load_model(f'models:/{config.MODELO_REGISTRADO}/{a.despues}')
ml = pd.read_sql('SELECT * FROM ml_dataset', sqlite3.connect(config.DB))
rng = np.random.default_rng(0)
for parte in ('valid', 'test'):
    d = ml[ml.particion == parte].reset_index(drop=True)
    y = d['y'].to_numpy()
    p1 = m1.predict_proba(d[list(m1.feature_names_in_)].astype(float))[:, 1]
    p2 = m2.predict_proba(d[list(m2.feature_names_in_)].astype(float))[:, 1]
    difs = []
    for _ in range(a.remuestreos):
        i = rng.integers(0, len(d), len(d))
        if len(set(y[i])) == 2:
            difs.append(roc_auc_score(y[i], p2[i]) - roc_auc_score(y[i], p1[i]))
    difs = np.array(difs)
    print(f'{parte}: {len(d)} filas · AUC antes {roc_auc_score(y, p1):.4f} · después {roc_auc_score(y, p2):.4f} · '
          f'diferencia {roc_auc_score(y, p2) - roc_auc_score(y, p1):+.4f} · intervalo 95 % '
          f'[{np.percentile(difs, 2.5):+.4f}, {np.percentile(difs, 97.5):+.4f}] · mejora en el {np.mean(difs > 0):.0%} de los remuestreos')
if 'modelo' in getattr(m2, 'named_steps', {}):
    coef = dict(zip(m2.feature_names_in_, m2.named_steps['modelo'].coef_[0]))
    print('coeficientes (variables escaladas) del modelo de después:', {k: round(float(v), 3) for k, v in coef.items() if k in ('ratio_devoluciones', 'devoluciones', 'frecuencia')})
