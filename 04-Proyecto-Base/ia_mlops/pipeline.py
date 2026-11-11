"""Orquestador: ejecuta, en orden, los pipelines que se le pidan. No tiene logica propia.

Los pipelines son INDEPENDIENTES: cada uno se puede ejecutar solo, comprueba que existe su entrada y es IDEMPOTENTE
(si su entrada no cambio, no hace nada). Este modulo es solo una comodidad para lanzarlos seguidos; en S4 los lanzara
GitHub Actions, cada uno como un paso (o en su propio horario).

    pipeline_ingesta_raw     retail.db (operacional) -> RAW
    pipeline_ingesta_master  RAW -> MASTER (+ reglas de calidad)
    pipeline_ml              MASTER -> FS -> ML
    pipeline_train           ML -> modelo, metricas y MLflow

La base operacional NO es un pipeline: simula el sistema de origen. Se crea (una vez) con  python -m ia_mlops.operacional

Uso (desde 04-Proyecto-Base):
    python -m ia_mlops.pipeline                                   # los cuatro, en orden (los que no cambian, no hacen nada)
    python -m ia_mlops.pipeline --solo pipeline_ml pipeline_train # solo algunos
    python -m ia_mlops.pipeline --forzar                          # rehace todos aunque no haya cambios
    python -m ia_mlops.pipeline --sin-mlflow
"""
import argparse
import time

from . import control, pipeline_ingesta_master, pipeline_ingesta_raw, pipeline_ml, pipeline_train

PIPELINES = {
    'pipeline_ingesta_raw': lambda a: pipeline_ingesta_raw.ejecutar(a['ruta_db'], a['ruta_operacional'], a['forzar'], a['verbose']),
    'pipeline_ingesta_master': lambda a: pipeline_ingesta_master.ejecutar(a['ruta_db'], a['forzar'], a['verbose']),
    'pipeline_ml': lambda a: pipeline_ml.ejecutar(a['ruta_db'], a['forzar'], a['verbose']),
    'pipeline_train': lambda a: pipeline_train.ejecutar(a['ruta_db'], a['forzar'], a['usar_mlflow'], a['verbose']),
}


def ejecutar(pipelines=None, ruta_db=None, ruta_operacional=None, forzar=False, usar_mlflow=True, verbose=True):
    """Ejecuta los pipelines pedidos (todos por defecto) en su orden natural y devuelve el resultado de cada uno."""
    pedidos = pipelines or list(PIPELINES)
    desconocidos = [p for p in pedidos if p not in PIPELINES]
    if desconocidos:
        raise ValueError(f'Pipelines desconocidos: {desconocidos}. Validos: {list(PIPELINES)}')
    args = dict(ruta_db=ruta_db, ruta_operacional=ruta_operacional, forzar=forzar, usar_mlflow=usar_mlflow, verbose=verbose)
    resultados = []
    for nombre in PIPELINES:              # siempre en el orden natural, aunque se pidan desordenados
        if nombre in pedidos:
            t0 = time.time()
            resultados.append(PIPELINES[nombre](args))
            if verbose:
                print(f'  ({time.time() - t0:.1f} s)')
    return resultados


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--solo', nargs='+', choices=list(PIPELINES), help='solo estos pipelines')
    ap.add_argument('--forzar', action='store_true', help='rehace aunque la entrada no haya cambiado')
    ap.add_argument('--sin-mlflow', action='store_true')
    a = ap.parse_args()
    control.desde_terminal(ejecutar, pipelines=a.solo, forzar=a.forzar, usar_mlflow=not a.sin_mlflow)
