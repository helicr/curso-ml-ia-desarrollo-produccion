"""Utilidades de acceso a SQLite.

SQLite guarda una base de datos entera en UN archivo (.db) y viene incluido en Python (modulo sqlite3): no hay servidor.
El proyecto usa dos: data/external/retail.db (operacional) y data/processed/curso.db (analitica).
SQLite trae desactivada la comprobacion de claves foraneas; conectar() la activa en cada conexion.
"""
import sqlite3
from pathlib import Path

from . import config


def conectar(ruta=None, solo_lectura=None):
    """Abre la base SQLite del proyecto (la crea si no existe) con claves foraneas activadas.

    solo_lectura (por defecto, config.DB_SOLO_LECTURA): abre la base SIN poder escribir en ella y sin crearla si no existe.
    Lo usa el contenedor de la interfaz, que recibe la base como volumen de solo lectura (-v ...:/datos:ro). Las tablas
    TEMPORALES (las de explotacion.variables_en_corte) siguen funcionando: viven fuera del archivo.
    """
    ruta = Path(ruta) if ruta else config.DB
    solo_lectura = config.DB_SOLO_LECTURA if solo_lectura is None else solo_lectura
    if solo_lectura:
        if not ruta.is_file():
            raise RuntimeError(f'No existe la base {ruta}. ¿Has montado el volumen con los datos? (-v .../data/processed:/datos:ro)')
        con = sqlite3.connect(f'{ruta.resolve().as_uri()}?mode=ro', uri=True)
        con.execute('PRAGMA foreign_keys = ON')
        return con
    ruta.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(ruta)
    con.execute('PRAGMA foreign_keys = ON')
    return con


def ejecutar_script(con, archivo):
    """Ejecuta un archivo .sql con varias sentencias (sin parametros)."""
    con.executescript(Path(archivo).read_text(encoding='utf-8'))
    con.commit()


def ejecutar_sentencia(con, archivo, parametros=None):
    """Ejecuta un archivo .sql con UNA sentencia y parametros con nombre (:corte, :ventana...)."""
    con.execute(Path(archivo).read_text(encoding='utf-8'), parametros or {})
    con.commit()


def escalar(con, sql, parametros=None):
    """Devuelve el primer valor de la primera fila de una consulta."""
    fila = con.execute(sql, parametros or {}).fetchone()
    return None if fila is None else fila[0]
