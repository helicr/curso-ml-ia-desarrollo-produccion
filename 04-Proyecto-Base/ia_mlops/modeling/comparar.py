"""Compara las probabilidades de los distintos caminos hacia el MISMO modelo (S2: «comparar predicciones»).

Toma filas reales de la particion test de `ml_dataset` y calcula la probabilidad de cada una por:
  1. el paquete          (ia_mlops.modeling.predict)
  2. el archivo joblib   (models/modelo.joblib)
  3. el formato MLflow   (models/modelo_mlflow/)
  4. la API              (solo si se pasa --url: local, en un contenedor o, mas adelante, en Cloud Run)

Si el modelo es el mismo, las diferencias son ceros de maquina. Una diferencia mayor que la tolerancia significa que algo cambia
entre el entrenamiento y el servicio (otra version de una libreria, otro orden de columnas, otro preproceso) y hay que encontrarlo ANTES de desplegar.

Uso (desde 04-Proyecto-Base, con el modelo ya entrenado):
    python -m ia_mlops.modeling.comparar                              # paquete, joblib y MLflow
    python -m ia_mlops.modeling.comparar --url http://127.0.0.1:8080  # ademas, la API
Codigo de salida: 0 todo coincide · 1 hay diferencias · 2 no se pudo comparar (sin modelo, sin datos o la API no responde).
"""
import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .. import config, db
from . import predict

TOLERANCIA = 1e-9
LOTE_API = 500          # la API admite hasta 1000 clientes por peticion


class NoSePudoComparar(RuntimeError):
    pass


def filas_de_test(n, ruta_db=None):
    """Hasta `n` filas reales de la particion test (solo las variables, sin el objetivo)."""
    if not Path(ruta_db or config.DB).exists():
        raise NoSePudoComparar(f'No existe la base {ruta_db or config.DB}. Ejecuta antes: python -m ia_mlops.pipeline')
    con = db.conectar(ruta_db)
    try:
        df = pd.read_sql(f"SELECT {', '.join(config.FEATURES)} FROM ml_dataset WHERE particion = 'test' ORDER BY cliente_id, fecha_corte LIMIT {int(n)}", con)
    except Exception as e:      # noqa: BLE001 - sin tabla ml_dataset
        raise NoSePudoComparar(f'No se pudieron leer filas de test de {ruta_db or config.DB}: {e}. Ejecuta antes: python -m ia_mlops.pipeline') from e
    finally:
        con.close()
    if df.empty:
        raise NoSePudoComparar('La particion test esta vacia. Ejecuta antes: python -m ia_mlops.pipeline')
    return df


def del_paquete(df, carpeta):
    return np.array(predict.predecir_probabilidad(df, ruta=carpeta))


def del_joblib(df, carpeta):
    return joblib.load(carpeta / 'modelo.joblib').predict_proba(df[config.FEATURES].astype(float))[:, 1]


def del_mlflow(df, carpeta):
    import mlflow.sklearn
    ruta = carpeta / config.CARPETA_MODELO_MLFLOW
    if not ruta.exists():
        raise NoSePudoComparar(f'No existe {ruta}. Ejecuta antes: python -m ia_mlops.pipeline')
    return mlflow.sklearn.load_model(str(ruta)).predict_proba(df[config.FEATURES].astype(float))[:, 1]


def de_la_api(df, url):
    """Pide las probabilidades a la API (POST /predecir/lote, por tandas)."""
    filas = json.loads(df[config.FEATURES].to_json(orient='records'))     # NaN -> null
    salida = []
    for i in range(0, len(filas), LOTE_API):
        cuerpo = json.dumps({'clientes': filas[i:i + LOTE_API]}).encode('utf-8')
        peticion = urllib.request.Request(url.rstrip('/') + '/predecir/lote', data=cuerpo, headers={'content-type': 'application/json'})
        try:
            with urllib.request.urlopen(peticion, timeout=30) as r:
                respuesta = json.loads(r.read())
        except urllib.error.HTTPError as e:
            raise NoSePudoComparar(f'La API respondio {e.code} en {url}: {e.read().decode("utf-8", "replace")[:300]}') from e
        except (urllib.error.URLError, OSError) as e:
            raise NoSePudoComparar(f'No se pudo hablar con la API en {url}: {e}. ¿Esta arrancada? (make api, o el contenedor en el puerto indicado)') from e
        salida += [p['probabilidad'] for p in respuesta['predicciones']]
    return np.array(salida)


def comparar(n=100, url=None, carpeta=None, ruta_db=None, tolerancia=TOLERANCIA):
    """Devuelve (filas, n, tolerancia): una fila por camino con su diferencia maxima respecto al paquete."""
    carpeta = carpeta or config.MODELOS
    if not (carpeta / 'modelo.joblib').exists():
        raise NoSePudoComparar(f'No hay modelo en {carpeta}. Ejecuta antes: python -m ia_mlops.pipeline')
    df = filas_de_test(n, ruta_db)
    referencia = del_paquete(df, carpeta)
    caminos = [('paquete (referencia)', referencia), ('joblib', del_joblib(df, carpeta)), ('MLflow', del_mlflow(df, carpeta))]
    if url:
        caminos.append((f'API {url}', de_la_api(df, url)))
    filas = []
    for nombre, p in caminos:
        dif = float(np.max(np.abs(p - referencia)))
        filas.append({'camino': nombre, 'filas': int(len(p)), 'diferencia_maxima': dif, 'coincide': bool(len(p) == len(referencia) and dif <= tolerancia)})
    return filas, len(df), tolerancia


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--url', help='URL base de la API (p. ej. http://127.0.0.1:8080). Sin ella solo se comparan paquete, joblib y MLflow.')
    ap.add_argument('--n', type=int, default=100, help='cuantas filas de test usar (por defecto 100)')
    ap.add_argument('--tolerancia', type=float, default=TOLERANCIA)
    a = ap.parse_args(argv)
    try:
        filas, n, tol = comparar(a.n, a.url, tolerancia=a.tolerancia)
    except NoSePudoComparar as e:
        print(f'No se pudo comparar: {e}', file=sys.stderr)
        return 2
    print(f'{n} filas reales de la particion test · tolerancia {tol:g}')
    print(f'{"camino":<40}{"filas":>7}{"diferencia maxima":>22}  resultado')
    for f in filas:
        print(f'{f["camino"]:<40}{f["filas"]:>7}{f["diferencia_maxima"]:>22.3e}  {"coincide" if f["coincide"] else "DIFIERE"}')
    todo = all(f['coincide'] for f in filas)
    print('Todos los caminos dan la misma probabilidad.' if todo else 'HAY DIFERENCIAS: busca que cambia entre el entrenamiento y el servicio.')
    return 0 if todo else 1


if __name__ == '__main__':
    sys.exit(main())
