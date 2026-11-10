"""Capas RAW y MASTER: descargar, cargar y depurar el dataset.

Es la traduccion a Python de los cuadernos  notebooks/01_pipeline_raw_a_master.ipynb.

Uso desde la terminal (en la carpeta del proyecto):
    python -m ia_mlops.dataset descargar            # baja el Excel original de UCI y verifica su huella
    python -m ia_mlops.dataset raw --fuente muestra # carga RAW
    python -m ia_mlops.dataset master               # construye MASTER y evalua la calidad
    python -m ia_mlops.dataset muestra              # regenera la muestra del repositorio (necesita la fuente completa en RAW)

Licencia del dato: CC BY 4.0.  Cita: Chen, D. (2012). Online Retail II [Dataset]. UCI. https://doi.org/10.24432/C5CG6D
"""
import argparse
import hashlib
import math
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd

from . import calidad, config, db

COLUMNAS = ['Invoice', 'StockCode', 'Description', 'Quantity', 'InvoiceDate', 'Price', 'Customer ID', 'Country']


# --------------------------------------------------------------------------------------------------- utilidades
def sha256_archivo(ruta):
    h = hashlib.sha256()
    with open(ruta, 'rb') as f:
        for bloque in iter(lambda: f.read(1024 * 1024), b''):
            h.update(bloque)
    return h.hexdigest()


def _nulo(valor):
    return valor is None or valor is pd.NaT or (isinstance(valor, float) and math.isnan(valor))


def _texto(valor):
    """Conserva el valor como texto. Los nulos siguen siendo nulos. 489434.0 se guarda como '489434'."""
    if _nulo(valor):
        return None
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return str(valor)


def _numero(valor, entero=False):
    if _nulo(valor):
        return None
    return int(float(valor)) if entero else float(valor)


def _fecha_iso(valor):
    if _nulo(valor):
        return None
    if isinstance(valor, str):
        return valor
    return pd.Timestamp(valor).strftime('%Y-%m-%d %H:%M:%S')


# --------------------------------------------------------------------------------------------------- descarga
def descargar(forzar=False):
    """Descarga el zip de UCI, verifica su sha256 y extrae el Excel a data/raw/online_retail_ii/."""
    destino = config.FUENTES['completo'].parent
    destino.mkdir(parents=True, exist_ok=True)
    xlsx = config.FUENTES['completo']
    if xlsx.exists() and not forzar:
        print(f'Ya existe {xlsx}. Usa --forzar para descargarlo de nuevo.')
        return xlsx
    zip_ruta = destino / 'online_retail_ii.zip'
    print('Descargando', config.URL_UCI)
    urllib.request.urlretrieve(config.URL_UCI, zip_ruta)
    huella = sha256_archivo(zip_ruta)
    print('sha256:', huella)
    if huella != config.SHA256_ZIP_UCI:
        raise RuntimeError('La huella no coincide con la esperada: el archivo cambio en el origen o la descarga quedo incompleta.\n'
                           f'  esperada: {config.SHA256_ZIP_UCI}\n  obtenida: {huella}')
    with zipfile.ZipFile(zip_ruta) as z:
        z.extractall(destino)
    print('Listo:', xlsx)
    return xlsx


# --------------------------------------------------------------------------------------------------- RAW
def leer_fuente(fuente):
    """Devuelve (ruta, [(nombre_de_hoja, DataFrame)]) con las columnas originales."""
    ruta = Path(config.FUENTES[fuente])
    if not ruta.exists():
        pista = ' Descargala con: python -m ia_mlops.dataset descargar' if fuente == 'completo' else ''
        raise FileNotFoundError(f'No existe {ruta}.{pista}')
    if ruta.suffix.lower() == '.csv':
        df = pd.read_csv(ruta, dtype=object, keep_default_na=False, na_values=[''])
        return ruta, [(ruta.name, df)]
    return ruta, list(pd.read_excel(ruta, sheet_name=None, dtype=object).items())


def cargar_raw(fuente='muestra', con=None, verbose=True):
    """Crea las tablas RAW y guarda cada fila TAL COMO VIENE, con su linaje (_hoja, _fila) y la huella del archivo."""
    cierre = con is None
    con = con or db.conectar()
    db.ejecutar_script(con, config.SQL / 'raw' / '01_crear_raw.sql')
    ruta, hojas = leer_fuente(fuente)
    total = 0
    for nombre, df in hojas:
        faltan = [c for c in COLUMNAS if c not in df.columns]
        if faltan:
            raise ValueError(f'A la hoja {nombre!r} le faltan las columnas {faltan}')
        filas = (
            (nombre, i + 2,  # +2: la fila 1 es el encabezado y las filas se cuentan desde 1
             _texto(r[0]), _texto(r[1]), _texto(r[2]), _numero(r[3], entero=True), _fecha_iso(r[4]),
             _numero(r[5]), _numero(r[6]), _texto(r[7]))
            for i, r in enumerate(df[COLUMNAS].itertuples(index=False, name=None))
        )
        con.executemany(
            'INSERT INTO raw_online_retail_ii (_hoja, _fila, Invoice, StockCode, Description, Quantity, InvoiceDate, Price, Customer_ID, Country) '
            'VALUES (?,?,?,?,?,?,?,?,?,?)', filas)
        total += len(df)
        if verbose:
            print(f'  RAW: hoja {nombre!r}: {len(df):,} filas')
    con.execute('INSERT INTO raw_carga (fuente, archivo, sha256, filas, cargado_en) VALUES (?,?,?,?,?)',
                (fuente, ruta.name, sha256_archivo(ruta), total, datetime.now().isoformat(timespec='seconds')))
    con.commit()
    if verbose:
        print(f'  RAW: {total:,} filas cargadas desde {ruta.name}')
    if cierre:
        con.close()
    return total


# --------------------------------------------------------------------------------------------------- MASTER
def construir_master(con=None, verbose=True):
    """Depura RAW y lo convierte en un modelo relacional; despues evalua las reglas de calidad (ver calidad.py)."""
    cierre = con is None
    con = con or db.conectar()
    db.ejecutar_script(con, config.SQL / 'master' / '01_crear_master.sql')
    db.ejecutar_script(con, config.SQL / 'master' / '02_poblar_master.sql')
    resultados = calidad.evaluar(con, lanzar=True)
    if verbose:
        for tabla in ('master_clientes', 'master_productos', 'master_facturas', 'master_lineas', 'master_descartes'):
            print(f'  MASTER: {tabla:18s} {db.escalar(con, f"SELECT COUNT(*) FROM {tabla}"):>10,} filas')
        alertas = [r for r in resultados if r['estado'] == 'ALERTA']
        print(f'  MASTER: calidad: {len(resultados)} reglas, {len(alertas)} alertas')
    if cierre:
        con.close()
    return resultados


# --------------------------------------------------------------------------------------------------- muestra
def crear_muestra(clientes=150, lineas_sin_cliente=300, semilla=42, salida=None):
    """Crea la muestra del repositorio a partir del dataset COMPLETO ya cargado en RAW (semilla fija, reproducible)."""
    salida = Path(salida or config.DATA_RAW / 'muestra_online_retail_ii.csv')
    con = db.conectar()
    ids = pd.read_sql('SELECT DISTINCT CAST(Customer_ID AS INTEGER) AS c FROM raw_online_retail_ii '
                      'WHERE Customer_ID IS NOT NULL ORDER BY 1', con)['c']
    elegidos = ids.sample(clientes, random_state=semilla).tolist()
    marcas = ','.join('?' * len(elegidos))
    con_cliente = pd.read_sql(f'SELECT * FROM raw_online_retail_ii WHERE CAST(Customer_ID AS INTEGER) IN ({marcas})', con, params=elegidos)
    sin_cliente = pd.read_sql('SELECT * FROM raw_online_retail_ii WHERE Customer_ID IS NULL', con).sample(lineas_sin_cliente, random_state=semilla)
    df = pd.concat([con_cliente, sin_cliente]).sort_values('_id').rename(columns={'Customer_ID': 'Customer ID'})[COLUMNAS]
    df.to_csv(salida, index=False)
    con.close()
    print(f'Muestra: {len(df):,} filas -> {salida} ({salida.stat().st_size / 1e6:.2f} MB)')
    return df


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='orden', required=True)
    p = sub.add_parser('descargar'); p.add_argument('--forzar', action='store_true')
    p = sub.add_parser('raw'); p.add_argument('--fuente', choices=list(config.FUENTES), default='muestra')
    sub.add_parser('master')
    p = sub.add_parser('muestra'); p.add_argument('--clientes', type=int, default=150); p.add_argument('--semilla', type=int, default=42)
    a = ap.parse_args()
    if a.orden == 'descargar':
        descargar(a.forzar)
    elif a.orden == 'raw':
        cargar_raw(a.fuente)
    elif a.orden == 'master':
        construir_master()
    else:
        crear_muestra(a.clientes, semilla=a.semilla)
