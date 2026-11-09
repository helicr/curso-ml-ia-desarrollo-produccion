"""Prediccion con el modelo entrenado. Es la base de la API de S2.

El modelo guardado incluye el preprocesamiento: la API solo debe entregarle las variables, en cualquier orden,
y este modulo se encarga de validarlas y ordenarlas. Asi el servicio y el entrenamiento comparten el MISMO preproceso.

Uso:
    from ia_mlops.modeling import predict
    predict.predecir_probabilidad({'recencia_dias': 12, 'frecuencia': 5, ...})
    python -m ia_mlops.modeling.predict --cliente 12347 --corte 2011-09-01     # desde la capa FS
"""
import argparse
import json

import joblib
import pandas as pd

from .. import config, db

_CACHE = {}


class VariablesFaltantesError(ValueError):
    pass


def cargar_modelo(ruta=None):
    """Carga el modelo y sus metadatos (se guardan en memoria para no leer el disco en cada prediccion)."""
    carpeta = ruta or config.MODELOS
    clave = str(carpeta)
    if clave not in _CACHE:
        modelo = joblib.load(carpeta / 'modelo.joblib')
        meta = json.loads((carpeta / 'metadatos.json').read_text(encoding='utf-8'))
        _CACHE[clave] = (modelo, meta)
    return _CACHE[clave]


def predecir_probabilidad(variables, ruta=None):
    """Probabilidad de que el cliente compre en los proximos 90 dias.

    variables: un diccionario o un DataFrame con las columnas de config.FEATURES. Devuelve un float si recibe un diccionario
    y una lista de floats si recibe un DataFrame. dias_medios_entre_compras puede ser None (el modelo lo imputa).
    """
    modelo, meta = cargar_modelo(ruta)
    df = pd.DataFrame([variables]) if isinstance(variables, dict) else pd.DataFrame(variables)
    faltan = [c for c in meta['variables'] if c not in df.columns]
    if faltan:
        raise VariablesFaltantesError(f'Faltan variables: {faltan}')
    prob = modelo.predict_proba(df[meta['variables']].astype(float))[:, 1]
    return float(prob[0]) if isinstance(variables, dict) else [float(p) for p in prob]


def predecir_cliente(cliente_id, fecha_corte, con=None, ruta=None):
    """Lee las variables del cliente en la capa FS y devuelve su probabilidad."""
    cierre = con is None
    con = con or db.conectar()
    fila = pd.read_sql('SELECT * FROM fs_cliente_corte WHERE cliente_id = :c AND fecha_corte = :f', con,
                       params={'c': int(cliente_id), 'f': fecha_corte})
    if cierre:
        con.close()
    if fila.empty:
        raise LookupError(f'No hay variables en FS para el cliente {cliente_id} en el corte {fecha_corte}.')
    return predecir_probabilidad(fila.iloc[0][config.FEATURES].to_dict(), ruta)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--cliente', type=int, required=True)
    ap.add_argument('--corte', required=True)
    a = ap.parse_args()
    print(f'Probabilidad de recompra en {config.VENTANA_OBJETIVO_DIAS} dias: {predecir_cliente(a.cliente, a.corte):.3f}')
