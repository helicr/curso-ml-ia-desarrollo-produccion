"""Proyecto base del curso ML e IA: de desarrollo a produccion. Caso transversal: Online Retail II.

Es la traduccion a .py de los cuadernos-pipeline de notebooks/.

PIPELINES (cada uno se ejecuta solo, comprueba su entrada y es idempotente; ver control.py):
    pipeline_ingesta_raw.py      cuaderno 01 (1)    retail.db -> RAW
    pipeline_ingesta_master.py   cuaderno 01 (2-4)  RAW -> MASTER + reglas de calidad
    pipeline_ml.py               cuadernos 02 y 03  MASTER -> FS -> ML
    pipeline_train.py            cuaderno 04        ML -> modelo, metricas y MLflow
    pipeline.py                  orquestador: lanza los cuatro en orden, por comodidad

SIMULACION DEL ORIGEN (no es un pipeline del proyecto):
    operacional.py               cuaderno 00        archivo de UCI -> retail.db

LOGICA que usan los pipelines:
    dataset.py, calidad.py       RAW y MASTER       features.py              FS
    modeling/ml_dataset.py       ML                 modeling/train.py        entrenamiento y MLflow
    modeling/predict.py          probabilidad para un cliente (base de la API de S2)
    config.py, db.py, control.py rutas y parametros, acceso a SQLite, idempotencia
"""
__version__ = "0.1.0"
