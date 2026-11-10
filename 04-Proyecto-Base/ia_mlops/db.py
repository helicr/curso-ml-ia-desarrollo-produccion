"""Utilidades de acceso a SQLite."""
import sqlite3
from pathlib import Path

from . import config


def conectar(ruta=None):
    """Abre la base SQLite del proyecto (la crea si no existe) con claves foraneas activadas."""
    ruta = Path(ruta) if ruta else config.DB
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
