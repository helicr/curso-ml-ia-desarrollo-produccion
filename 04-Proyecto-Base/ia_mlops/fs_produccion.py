"""La FS de producción: las 13 variables del corte que se puntuó, guardadas para consultarlas después sin recalcular.

POR QUÉ EXISTE
    `fs_cliente_corte` (la capa FS del pipeline) solo tiene los cortes de ENTRENAMIENTO (el último es 2011-09-01). Pero
    el negocio puntúa «hoy», con un corte posterior. Cada vez que `explotacion` puntúa a todos los clientes, guarda aquí
    las variables de ese corte; quien pregunte «¿qué probabilidad tiene el cliente 13599?» puede LEERLAS (consulta por
    clave, sin cálculo) en vez de calcularlas otra vez. Es la inferencia «bajo demanda».

ESQUEMA (tabla `fs_produccion` de la base analítica, curso.db)
    cliente_id INTEGER, fecha_corte TEXT (AAAA-MM-DD), las 13 columnas de config.FEATURES con sus mismos nombres,
    huella_modelo TEXT, version_modelo INTEGER, creado_en TEXT (ISO). Clave primaria (cliente_id, fecha_corte).
    `huella_modelo` y `version_modelo` salen de models/referencia.json (la versión en producción); si no existe, NULL.

CADA ESCRITURA REEMPLAZA EL CORTE ENTERO: puntuar dos veces el mismo corte deja una sola copia (idempotente).
"""
import sqlite3
from datetime import datetime

import pandas as pd

from . import config, produccion

TABLA = 'fs_produccion'
COLUMNAS = ['cliente_id', 'fecha_corte', *config.FEATURES, 'huella_modelo', 'version_modelo', 'creado_en']

# Los tipos de las 13 variables son los de la capa FS (sql/fs/01_crear_fs.sql): REAL las continuas, INTEGER el resto.
_REALES = {'monto_total', 'ticket_medio', 'monto_90d', 'dias_medios_entre_compras'}


def _ddl():
    cols = ',\n    '.join(f'{c} {"REAL" if c in _REALES else "INTEGER"}' for c in config.FEATURES)
    return (f'CREATE TABLE IF NOT EXISTS {TABLA} (\n    cliente_id INTEGER NOT NULL,\n    fecha_corte TEXT NOT NULL,\n    {cols},\n'
            '    huella_modelo TEXT,\n    version_modelo INTEGER,\n    creado_en TEXT NOT NULL,\n    PRIMARY KEY (cliente_id, fecha_corte)\n)')


def crear_tabla(con):
    """Crea fs_produccion si no existe (no toca lo que ya haya)."""
    con.execute(_ddl())
    con.commit()


def version_del_modelo(ruta_referencia=None):
    """(version, huella) de la versión en producción según models/referencia.json; (None, None) si no existe o no es válida."""
    try:
        ref = produccion.leer_referencia(ruta_referencia)
    except produccion.ErrorReferencia:
        return None, None
    return ref['version'], ref['huella_datos']


def guardar_corte(con, df, corte, ruta_referencia=None):
    """Guarda las variables de `df` (con cliente_id y las 13 variables) como el corte `corte`, reemplazando ese corte.

    Devuelve cuántas filas escribió. Los demás cortes no se tocan.
    """
    crear_tabla(con)
    version, huella = version_del_modelo(ruta_referencia)
    ahora = datetime.now().isoformat(timespec='seconds')
    cuerpo = df[['cliente_id', *config.FEATURES]].astype(object).where(df[['cliente_id', *config.FEATURES]].notna(), None)
    filas = [(int(r[0]), str(corte), *r[1:], huella, version, ahora) for r in cuerpo.itertuples(index=False, name=None)]
    marcas = ','.join('?' * len(COLUMNAS))
    with con:                                    # una transacción: o se reemplaza el corte entero o no cambia nada
        con.execute(f'DELETE FROM {TABLA} WHERE fecha_corte = ?', (str(corte),))
        con.executemany(f'INSERT INTO {TABLA} ({", ".join(COLUMNAS)}) VALUES ({marcas})', filas)
    return len(filas)


def ultimo_corte(con):
    """El corte más reciente guardado, o None si la tabla no existe o está vacía."""
    try:
        return con.execute(f'SELECT MAX(fecha_corte) FROM {TABLA}').fetchone()[0]
    except sqlite3.OperationalError:             # la tabla todavía no existe
        return None


def leer_fs_produccion(con, cliente_ids=None, corte=None):
    """Lee variables de la FS de producción. Devuelve un DataFrame con las columnas de COLUMNAS.

    corte=None: el ÚLTIMO corte disponible. cliente_ids=None: todos los clientes de ese corte; si se indican, solo esos
    (un cliente que no está en el corte simplemente no aparece: la comparación con los ids pedidos la hace quien llama).
    Si la tabla no existe o el corte no tiene filas, devuelve un DataFrame vacío con las mismas columnas.
    """
    corte = corte or ultimo_corte(con)
    if corte is None:
        return pd.DataFrame(columns=COLUMNAS)
    sql, par = f'SELECT {", ".join(COLUMNAS)} FROM {TABLA} WHERE fecha_corte = ?', [str(corte)]
    if cliente_ids is not None:
        ids = [int(i) for i in cliente_ids]
        if not ids:
            return pd.DataFrame(columns=COLUMNAS)
        sql += f' AND cliente_id IN ({",".join("?" * len(ids))})'
        par += ids
    try:
        return pd.read_sql(sql + ' ORDER BY cliente_id', con, params=par)
    except (sqlite3.OperationalError, pd.errors.DatabaseError):   # la tabla no existe
        return pd.DataFrame(columns=COLUMNAS)
