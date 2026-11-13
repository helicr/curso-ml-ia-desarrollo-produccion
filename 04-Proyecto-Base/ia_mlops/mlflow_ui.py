"""Abre la interfaz web de MLflow sobre el registro DEL PROYECTO (models/mlflow.db), lo lances desde donde lo lances.

Por qué existe: `mlflow ui --backend-store-uri sqlite:///models/mlflow.db` usa una ruta RELATIVA. Lanzado desde otra carpeta
(por ejemplo la raíz del repositorio, que es donde se abre la terminal de VS Code), MLflow crea allí una base NUEVA y vacía
sin dar ningún error: la interfaz arranca, pero no hay ni ejecuciones ni modelos. Este módulo calcula la ruta absoluta,
comprueba que el registro existe y tiene ejecuciones, y solo entonces arranca la interfaz.

Uso (desde 04-Proyecto-Base, con el entorno env-ia-mlops):
    python -m ia_mlops.mlflow_ui                 abre http://127.0.0.1:5000
    python -m ia_mlops.mlflow_ui --port 5001     si el 5000 está ocupado
    python -m ia_mlops.mlflow_ui --comprobar     solo dice qué hay en el registro, sin abrir nada
Para pararla: Ctrl+C en la misma terminal.

En la interfaz (MLflow 3): arriba a la izquierda elige «Model training» (no «GenAI»). Las ejecuciones están en
Experiments → retencion-90d → Training runs, y los modelos registrados en «Registered Models» (menú izquierdo, o
http://127.0.0.1:5000/#/models).
"""
import argparse
import sqlite3
import subprocess
import sys

from . import config

BASE = config.MODELOS / 'mlflow.db'


def uri():
    """Tracking URI absoluto del proyecto: el mismo en el que escribe train.py."""
    return 'sqlite:///' + BASE.resolve().as_posix()


def resumen():
    """(ejecuciones del experimento, versiones registradas del modelo) leyendo la base directamente; None si no existe."""
    if not BASE.exists():
        return None
    con = sqlite3.connect(BASE)
    try:
        def uno(sql, *a):
            try:
                return con.execute(sql, a).fetchone()[0]
            except sqlite3.Error:
                return 0
        ejecuciones = uno('SELECT COUNT(*) FROM runs r JOIN experiments e ON e.experiment_id = r.experiment_id '
                          "WHERE e.name = ? AND r.lifecycle_stage = 'active'", config.EXPERIMENTO_MLFLOW)
        versiones = uno('SELECT COUNT(*) FROM model_versions WHERE name = ?', config.MODELO_REGISTRADO)
        return ejecuciones, versiones
    finally:
        con.close()


def comando(puerto=5000, host='127.0.0.1'):
    """La orden que se ejecuta (con el Python del entorno, así no depende de qué `mlflow` haya en el PATH)."""
    return [sys.executable, '-m', 'mlflow', 'ui', '--backend-store-uri', uri(), '--host', host, '--port', str(puerto)]


def main(argv=None):
    ap = argparse.ArgumentParser(description='Interfaz web de MLflow sobre models/mlflow.db del proyecto.')
    ap.add_argument('--port', type=int, default=5000)
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--comprobar', action='store_true', help='solo informa de lo que hay en el registro')
    a = ap.parse_args(argv)

    r = resumen()
    print(f'Registro de MLflow: {BASE.resolve()}')
    if r is None:
        print('  No existe todavía. Entrena primero:  python -m ia_mlops.pipeline   (o ejecuta el cuaderno 04 con USAR_MLFLOW = True)')
        return 1
    ejecuciones, versiones = r
    print(f'  Experimento «{config.EXPERIMENTO_MLFLOW}»: {ejecuciones} ejecuciones · '
          f'modelo registrado «{config.MODELO_REGISTRADO}»: {versiones} versiones')
    if ejecuciones == 0:
        print('  Está vacío: entrena primero (python -m ia_mlops.pipeline).')
        return 1
    if a.comprobar:
        return 0
    print(f'Abriendo http://{a.host}:{a.port}  ·  En la web elige «Model training» (arriba a la izquierda).  ·  Para parar: Ctrl+C')
    try:
        return subprocess.call(comando(a.port, a.host))
    except KeyboardInterrupt:
        return 0


if __name__ == '__main__':
    sys.exit(main())
