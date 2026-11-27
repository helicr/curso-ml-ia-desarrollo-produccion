"""Prepara la carpeta de construcción («contexto») de la imagen de Vertex con el modelo champion DENTRO.

Por qué existe: la imagen de Vertex lleva el modelo de la versión de MLflow que dice el manifiesto, y no depende de CÓMO se construya
la imagen de la API (la actual de develop, que copia models/modelo_mlflow, ni la multietapa con `--build-context modelo=models`).
Este script reúne en una carpeta, y solo ahí, lo que necesita `imagen/Dockerfile.vertex`:

    <destino>/Dockerfile.vertex
    <destino>/requirements-api.lock        las mismas versiones exactas que la imagen de la API (scikit-learn 1.9.1, no 1.6)
    <destino>/vertex_adaptador.py
    <destino>/ia_mlops/__init__.py, config.py, api/__init__.py, api/esquemas.py     (solo lo que importa el adaptador)
    <destino>/modelo/modelo_mlflow/        el modelo EXACTO de la versión del manifiesto, exportado del registro de MLflow
    <destino>/modelo/vertex-manifiesto.json

Comprueba además que la versión de scikit-learn con la que se guardó el modelo es la que instala el lock: un modelo guardado con una
versión no debe abrirse con otra.

Uso (desde esta carpeta):
    python preparar_contexto.py --manifiesto vertex-manifiesto.json [--destino build/vertex] [--uri URI] [--modelo-origen CARPETA]
    --modelo-origen  usa una carpeta ya exportada (un modelo MLflow) en lugar de leer el registro (pruebas)
Código de salida: 0 bien · 2 error.
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

import manifiesto_champion as mc

AQUI = Path(__file__).resolve().parent
MARCA = '.contexto-vertex'
DE_IA_MLOPS = ('__init__.py', 'config.py', 'api/__init__.py', 'api/esquemas.py')


def version_sklearn_del_modelo(carpeta):
    m = re.search(r'sklearn_version:\s*([\w.]+)', (Path(carpeta) / 'MLmodel').read_text(encoding='utf-8'))
    return m.group(1) if m else None


def version_sklearn_del_lock(lock):
    m = re.search(r'^scikit-learn==([\w.]+)', Path(lock).read_text(encoding='utf-8'), re.M)
    return m.group(1) if m else None


def preparar(manifiesto, destino, uri=None, modelo_origen=None, proyecto=None):
    proyecto = Path(proyecto or mc.PROYECTO)
    destino = Path(destino)
    if destino.exists():
        if not (destino / MARCA).exists():
            raise mc.ErrorManifiesto(f'{destino} existe y no es un contexto de este script (falta {MARCA}): no lo borro. Elige otra carpeta.')
        shutil.rmtree(destino)
    (destino / 'modelo').mkdir(parents=True)
    (destino / MARCA).write_text('Carpeta generada por preparar_contexto.py; se puede borrar.\n', encoding='utf-8')

    modelo = destino / 'modelo' / 'modelo_mlflow'
    if modelo_origen:
        shutil.copytree(modelo_origen, modelo)
    else:
        import mlflow.artifacts
        from ia_mlops import alias_modelo
        alias_modelo.conectar(uri)
        bajado = mlflow.artifacts.download_artifacts(artifact_uri=f'models:/{manifiesto["modelo"]}/{manifiesto["mlflow_version"]}', dst_path=str(destino / 'exportado'))
        shutil.copytree(bajado, modelo)
        shutil.rmtree(destino / 'exportado', ignore_errors=True)
    if not (modelo / 'MLmodel').exists():
        raise mc.ErrorManifiesto(f'No hay un modelo MLflow en {modelo}.')

    lock = proyecto / 'requirements-api.lock'
    if not lock.exists():
        raise mc.ErrorManifiesto(f'No encuentro {lock} (indica la carpeta del proyecto con CURSO_DIR_PROYECTO).')
    del_modelo, del_lock = version_sklearn_del_modelo(modelo), version_sklearn_del_lock(lock)
    if del_modelo != del_lock:
        raise mc.ErrorManifiesto(f'El modelo se guardó con scikit-learn {del_modelo} y el lock instalaría la {del_lock}: reentrena o regenera el lock (make lock).')
    shutil.copy2(lock, destino / 'requirements-api.lock')
    for f in DE_IA_MLOPS:
        (destino / 'ia_mlops' / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(proyecto / 'ia_mlops' / f, destino / 'ia_mlops' / f)
    shutil.copy2(AQUI / 'imagen' / 'vertex_adaptador.py', destino / 'vertex_adaptador.py')
    shutil.copy2(AQUI / 'imagen' / 'Dockerfile.vertex', destino / 'Dockerfile.vertex')
    (destino / 'modelo' / mc.NOMBRE_MANIFIESTO).write_text(json.dumps(manifiesto, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return {'destino': str(destino), 'sklearn': del_modelo, 'archivos': sum(1 for p in destino.rglob('*') if p.is_file())}


def main(argv=None):
    ap = argparse.ArgumentParser(description='Prepara el contexto de construcción de la imagen de Vertex con el modelo champion')
    ap.add_argument('--manifiesto', default=mc.NOMBRE_MANIFIESTO)
    ap.add_argument('--destino', default='build/vertex')
    ap.add_argument('--uri')
    ap.add_argument('--modelo-origen')
    a = ap.parse_args(argv)
    try:
        r = preparar(mc.cargar(a.manifiesto), a.destino, a.uri, a.modelo_origen)
    except mc.ErrorManifiesto as e:
        print(f'Error: {e}', file=sys.stderr)
        return 2
    print(f'Contexto listo en {r["destino"]}: {r["archivos"]} archivos; modelo guardado con scikit-learn {r["sklearn"]} (= el del lock).')
    print(f'Construir:  docker build --platform linux/amd64 -f {r["destino"]}/Dockerfile.vertex -t retencion-vertex:local {r["destino"]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
