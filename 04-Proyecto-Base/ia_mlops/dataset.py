"""Fuente, RAW y MASTER: descargar el archivo, ingerir la base operacional en RAW y depurarla en MASTER.

Es la traduccion a Python de los cuadernos 00_pipeline_operacional.ipynb (lectura del archivo) y
01_pipeline_raw_a_master.ipynb. La base operacional se construye con ia_mlops/operacional.py.

RAW (dato crudo)
    Copia FIEL de cada tabla del operacional (clientes -> raw_clientes, ...). No corrige ni valida nada: por eso sus tablas
    no tienen claves. La ingesta es una carga completa: borra RAW y lo vuelve a copiar. Linaje: cada fila conserva su clave
    de origen y _carga_id, que apunta a raw_carga (tabla copiada, filas, huella sha256 del contenido y momento de la carga).
    Si la huella no cambia entre dos cargas, el origen no ha cambiado.

MASTER (dato maestro)
    Dato depurado y relacional, regenerable desde RAW (sql/master/). Recorta y pone en mayusculas, descarta duplicados y
    nulos obligatorios CON SU MOTIVO (master_descartes) y marca cada linea como venta valida o no. Despues evalua las reglas
    de calidad de calidad.py; si falla una regla dura, se detiene.

Por que dos capas: las reglas de limpieza cambian; con RAW intacto, MASTER se rehace sin volver a pedir los datos al origen.

Uso desde la terminal (en la carpeta del proyecto):
    python -m ia_mlops.dataset descargar            # baja el Excel original de UCI y verifica su huella
    python -m ia_mlops.dataset raw                  # ingiere la base operacional retail.db en RAW
    python -m ia_mlops.dataset master               # construye MASTER y evalua la calidad
    python -m ia_mlops.dataset muestra              # regenera la muestra del repositorio (necesita el Excel completo)

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
TABLAS_OPERACIONALES = ['clientes', 'productos', 'facturas', 'lineas_factura']


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


# --------------------------------------------------------------------------------------------------- fuente
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


def leer_lineas(fuente):
    """Lee el archivo y devuelve (ruta, lineas): una tupla por fila, en el orden del archivo, con tipos coherentes.
    Orden de la tupla: linea_id, factura_id, codigo_producto, descripcion, cantidad, registrada_en, precio_unitario, cliente_id, pais."""
    ruta, hojas = leer_fuente(fuente)
    lineas = []
    for nombre, df in hojas:
        faltan = [c for c in COLUMNAS if c not in df.columns]
        if faltan:
            raise ValueError(f'A la hoja {nombre!r} le faltan las columnas {faltan}')
        for r in df[COLUMNAS].itertuples(index=False, name=None):
            lineas.append((len(lineas) + 1, _texto(r[0]), _texto(r[1]), _texto(r[2]), _numero(r[3], entero=True),
                           _fecha_iso(r[4]), _numero(r[5]), _numero(r[6], entero=True), _texto(r[7])))
    return ruta, lineas


# --------------------------------------------------------------------------------------------------- RAW
def huella_tabla(con, tabla):
    """(filas, sha256) del contenido de una tabla, recorrida en su orden de insercion."""
    h, n = hashlib.sha256(), 0
    for fila in con.execute(f'SELECT * FROM {tabla} ORDER BY rowid'):
        h.update(repr(fila).encode('utf-8'))
        n += 1
    return n, h.hexdigest()


def cargar_raw(con=None, ruta_operacional=None, verbose=True):
    """Ingesta: copia cada tabla de la base operacional en su tabla RAW, TAL COMO ESTA, y registra la carga en raw_carga."""
    ruta_operacional = Path(ruta_operacional or config.DB_OPERACIONAL)
    if not ruta_operacional.exists():
        raise FileNotFoundError(f'No existe la base operacional {ruta_operacional}. Creala con: python -m ia_mlops.operacional')
    cierre = con is None
    con = con or db.conectar()
    db.ejecutar_script(con, config.SQL / 'raw' / '01_crear_raw.sql')
    con.execute('ATTACH DATABASE ? AS retail', (str(ruta_operacional),))
    try:
        ahora = datetime.now().isoformat(timespec='seconds')
        total = 0
        for tabla in TABLAS_OPERACIONALES:
            filas, huella = huella_tabla(con, f'retail.{tabla}')
            carga = con.execute('INSERT INTO raw_carga (origen, tabla, filas, sha256, extraido_en) VALUES (?,?,?,?,?)',
                                ('retail', tabla, filas, huella, ahora)).lastrowid
            con.execute(f'INSERT INTO raw_{tabla} SELECT t.*, ? FROM retail.{tabla} AS t ORDER BY t.rowid', (carga,))
            total += filas
            if verbose:
                print(f'  RAW: raw_{tabla:15s} {filas:>10,} filas')
        con.commit()
    except Exception:
        con.rollback()   # una ingesta a medias no se queda en RAW
        raise
    finally:
        con.execute('DETACH DATABASE retail')
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
    """Crea la muestra del repositorio a partir del Excel COMPLETO (semilla fija, reproducible)."""
    salida = Path(salida or config.FUENTES['muestra'])
    _, lineas = leer_lineas('completo')
    df = pd.DataFrame(lineas, columns=['_id'] + COLUMNAS)
    df['Customer ID'] = df['Customer ID'].astype(float)   # el original guarda el cliente como decimal (14748.0)
    ids = pd.Series(sorted(df['Customer ID'].dropna().astype(int).unique()))
    elegidos = set(ids.sample(clientes, random_state=semilla))
    con_cliente = df[df['Customer ID'].isin(elegidos)]
    sin_cliente = df[df['Customer ID'].isna()].sample(lineas_sin_cliente, random_state=semilla)
    muestra = pd.concat([con_cliente, sin_cliente]).sort_values('_id')[COLUMNAS]
    muestra.to_csv(salida, index=False)
    print(f'Muestra: {len(muestra):,} filas -> {salida} ({salida.stat().st_size / 1e6:.2f} MB)')
    return muestra


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='orden', required=True)
    p = sub.add_parser('descargar'); p.add_argument('--forzar', action='store_true')
    sub.add_parser('raw')
    sub.add_parser('master')
    p = sub.add_parser('muestra'); p.add_argument('--clientes', type=int, default=150); p.add_argument('--semilla', type=int, default=42)
    a = ap.parse_args()
    if a.orden == 'descargar':
        descargar(a.forzar)
    elif a.orden == 'raw':
        cargar_raw()
    elif a.orden == 'master':
        construir_master()
    else:
        crear_muestra(a.clientes, semilla=a.semilla)
