"""Pipeline completo en Python: raw -> master -> fs -> ml -> entrenar.

Es la version en .py de los cuadernos 01 a 04 (que son los pipelines originales).

Uso:
    python -m ia_mlops.pipeline                          # usa la muestra incluida (rapido)
    python -m ia_mlops.pipeline --fuente completo        # usa el Excel original (descargalo antes)
    python -m ia_mlops.pipeline --etapas fs ml           # solo algunas etapas (las anteriores deben existir)
    python -m ia_mlops.pipeline --sin-mlflow             # entrena sin registrar en MLflow

El ORDEN importa: FS va antes que ML porque ML se construye a partir de las variables de FS.
"""
import argparse
import time

from . import config, db
from .dataset import cargar_raw, construir_master
from .features import construir_fs
from .modeling.ml_dataset import construir_ml
from .modeling.train import entrenar

ETAPAS = ['raw', 'master', 'fs', 'ml', 'entrenar']


def ejecutar(fuente='muestra', etapas=None, usar_mlflow=True, ruta_db=None, verbose=True):
    etapas = etapas or ETAPAS
    desconocidas = [e for e in etapas if e not in ETAPAS]
    if desconocidas:
        raise ValueError(f'Etapas desconocidas: {desconocidas}. Validas: {ETAPAS}')
    con = db.conectar(ruta_db)
    try:
        for etapa in ETAPAS:
            if etapa not in etapas:
                continue
            t0 = time.time()
            if verbose:
                print(f'[{etapa}]')
            if etapa == 'raw':
                cargar_raw(fuente, con, verbose)
            elif etapa == 'master':
                construir_master(con, verbose)
            elif etapa == 'fs':
                construir_fs(con, verbose=verbose)
            elif etapa == 'ml':
                construir_ml(con, verbose)
            elif etapa == 'entrenar':
                entrenar(con, usar_mlflow, verbose)
            if verbose:
                print(f'  ({time.time() - t0:.1f} s)')
    finally:
        con.close()


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--fuente', choices=list(config.FUENTES), default='muestra')
    ap.add_argument('--etapas', nargs='+', choices=ETAPAS)
    ap.add_argument('--sin-mlflow', action='store_true')
    a = ap.parse_args()
    ejecutar(a.fuente, a.etapas, usar_mlflow=not a.sin_mlflow)
