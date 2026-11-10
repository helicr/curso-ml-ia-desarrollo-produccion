"""Prueba de humo del entorno env-ia-mlops.

Comprueba que las librerias del curso se importan y recorre un mini ciclo de ML clasico:
capas en SQLite -> entrenamiento con seguimiento en MLflow -> API con FastAPI -> validacion de entrada.
No necesita Internet ni cuentas. Escribe solo en una carpeta temporal.

Uso (con el entorno activo):
    conda activate env-ia-mlops
    python 03-Entorno/conda/prueba_de_humo.py

Debe terminar con la linea:  HUMO OK
Si falla, copia el mensaje completo y envialo al instructor.
"""
import importlib
import sqlite3
import sys
import tempfile
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

print('python', sys.version.split()[0])
MODULOS = ['pandas', 'pyarrow', 'numpy', 'sklearn', 'joblib', 'matplotlib', 'jupyterlab', 'ipykernel', 'mlflow',
           'fastapi', 'uvicorn', 'pydantic', 'httpx', 'requests', 'pytest', 'google.cloud.storage',
           'google.cloud.bigquery', 'db_dtypes', 'yaml', 'openpyxl', 'papermill', 'jupytext', 'nbclient']
fallan = []
for nombre in MODULOS:
    try:
        modulo = importlib.import_module(nombre)
        print(f'  ok    {nombre:24s}', getattr(modulo, '__version__', ''))
    except Exception as error:  # noqa: BLE001
        fallan.append(nombre)
        print(f'  FALLA {nombre}: {error}')
if fallan:
    sys.exit('Faltan librerias: ' + ', '.join(fallan))

import joblib
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

carpeta = Path(tempfile.mkdtemp(prefix='humo-'))

# 1) Capas en SQLite: raw -> master -> fs -> ml
rng = np.random.default_rng(0)
raw = pd.DataFrame({'cliente': rng.integers(1, 200, 2000), 'monto': rng.gamma(2, 20, 2000), 'dias': rng.integers(1, 90, 2000)})
con = sqlite3.connect(carpeta / 'curso.db')
raw.to_sql('raw_ventas', con, index=False)
con.execute('create table master_ventas as select cliente, monto, dias from raw_ventas where monto > 0')
con.execute('create table fs_cliente as select cliente, count(*) n, avg(monto) m, avg(dias) d from master_ventas group by cliente')
df = pd.read_sql('select * from fs_cliente', con)
df['y'] = (df['m'] > df['m'].median()).astype(int)
df.to_sql('ml_dataset', con, index=False)
tablas = [r[0] for r in con.execute("select name from sqlite_master where type='table' order by 1")]
con.close()
assert tablas == ['fs_cliente', 'master_ventas', 'ml_dataset', 'raw_ventas'], tablas
print('  sqlite: tablas', tablas)

# 2) Entrenar y registrar con MLflow (SQLite + carpeta local)
mlflow.set_tracking_uri('sqlite:///' + (carpeta / 'mlflow.db').as_posix())
mlflow.set_experiment('humo')
X, y = df[['n', 'd']], df['y']
Xtr, Xte, ytr, yte = train_test_split(X, y, random_state=0)
with mlflow.start_run():
    modelo = RandomForestClassifier(n_estimators=50, random_state=0).fit(Xtr, ytr)
    auc = roc_auc_score(yte, modelo.predict_proba(Xte)[:, 1])
    mlflow.log_param('n_estimators', 50)
    mlflow.log_metric('auc', auc)
    # Con MLflow 3, un RandomForest necesita declarar el tipo de arbol como confiable al guardarlo.
    mlflow.sklearn.log_model(modelo, name='modelo', skops_trusted_types=['sklearn.tree._tree.Tree'])
    run_id = mlflow.active_run().info.run_id
cargado = mlflow.sklearn.load_model(f'runs:/{run_id}/modelo')
assert (cargado.predict(Xte) == modelo.predict(Xte)).all()
joblib.dump(modelo, carpeta / 'modelo.joblib')
print('  mlflow: ejecucion', run_id[:8], '| auc', round(auc, 3))

# 3) API con FastAPI, probada sin levantar un servidor
class Entrada(BaseModel):
    n: int
    d: float


app = FastAPI()


@app.post('/predecir')
def predecir(entrada: Entrada):
    return {'clase': int(cargado.predict(pd.DataFrame([entrada.model_dump()]))[0])}


cliente = TestClient(app)
respuesta = cliente.post('/predecir', json={'n': 3, 'd': 20.0})
assert respuesta.status_code == 200 and 'clase' in respuesta.json(), respuesta.text
print('  api: respuesta', respuesta.json())
assert cliente.post('/predecir', json={'n': 'x'}).status_code == 422
print('  api: entrada invalida rechazada (422)')

print('HUMO OK')
