"""Orquestador: ejecuta, en orden, los pipelines que se le pidan. No tiene logica de datos propia.

Los pipelines son INDEPENDIENTES: cada uno se puede ejecutar solo, comprueba que existe su entrada y es IDEMPOTENTE
(si su entrada no cambio, no hace nada). Este modulo es solo una comodidad para lanzarlos seguidos; en S4 los lanzara
GitHub Actions, cada uno como un paso (o en su propio horario).

    pipeline_ingesta_raw     retail.db (operacional) -> RAW
    pipeline_ingesta_master  RAW -> MASTER (+ reglas de calidad)
    pipeline_ml              MASTER -> FS -> ML
    pipeline_train           ML -> modelo, metricas y MLflow

La base operacional NO es un pipeline: simula el sistema de origen (python -m ia_mlops.operacional). Por comodidad,
este orquestador la crea con la muestra si todavia no existe (por ejemplo, en un clon recien hecho, en el CI o en un
Codespace), y la vuelve a crear desde la fuente pedida con --fuente. Los pipelines sueltos nunca la crean: si falta, lo dicen.

Uso (desde 04-Proyecto-Base):
    python -m ia_mlops.pipeline                                   # los cuatro, en orden (los que no cambian, no hacen nada)
    python -m ia_mlops.pipeline --fuente completo                 # rehace el operacional con el Excel completo y lo que dependa de el
    python -m ia_mlops.pipeline --solo pipeline_ml pipeline_train # solo algunos
    python -m ia_mlops.pipeline --forzar                          # rehace todos aunque no haya cambios
    python -m ia_mlops.pipeline --sin-mlflow
"""
import argparse
import time
from pathlib import Path

from . import config, control, operacional, pipeline_ingesta_master, pipeline_ingesta_raw, pipeline_ml, pipeline_train

PIPELINES = {
    'pipeline_ingesta_raw': lambda a: pipeline_ingesta_raw.ejecutar(a['ruta_db'], a['ruta_operacional'], a['forzar'], a['verbose']),
    'pipeline_ingesta_master': lambda a: pipeline_ingesta_master.ejecutar(a['ruta_db'], a['forzar'], a['verbose']),
    'pipeline_ml': lambda a: pipeline_ml.ejecutar(a['ruta_db'], a['forzar'], a['verbose']),
    'pipeline_train': lambda a: pipeline_train.ejecutar(a['ruta_db'], a['forzar'], a['usar_mlflow'], a['verbose']),
}


def preparar_operacional(fuente, ruta_operacional, verbose):
    """Crea la base operacional si no existe (con la muestra) o si se pide otra fuente explicitamente."""
    ruta = Path(ruta_operacional or config.DB_OPERACIONAL)
    if fuente is None and ruta.exists():
        return
    if verbose:
        motivo = f'se pide la fuente «{fuente}»' if fuente else 'todavia no existe'
        print(f'[operacional] creando {ruta.name} ({motivo}); es la simulacion del sistema de ventas, no un pipeline')
    operacional.crear_operacional(fuente or 'muestra', ruta, verbose)


def ejecutar(pipelines=None, ruta_db=None, ruta_operacional=None, forzar=False, usar_mlflow=True, verbose=True, fuente=None):
    """Ejecuta los pipelines pedidos (todos por defecto) en su orden natural y devuelve el resultado de cada uno."""
    pedidos = pipelines or list(PIPELINES)
    desconocidos = [p for p in pedidos if p not in PIPELINES]
    if desconocidos:
        raise ValueError(f'Pipelines desconocidos: {desconocidos}. Validos: {list(PIPELINES)}')
    if 'pipeline_ingesta_raw' in pedidos:
        preparar_operacional(fuente, ruta_operacional, verbose)
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
    ap.add_argument('--fuente', choices=list(config.FUENTES), help='vuelve a crear la base operacional desde esta fuente antes de ingerir')
    ap.add_argument('--forzar', action='store_true', help='rehace aunque la entrada no haya cambiado')
    ap.add_argument('--sin-mlflow', action='store_true')
    a = ap.parse_args()
    control.desde_terminal(ejecutar, pipelines=a.solo, forzar=a.forzar, usar_mlflow=not a.sin_mlflow, fuente=a.fuente)
