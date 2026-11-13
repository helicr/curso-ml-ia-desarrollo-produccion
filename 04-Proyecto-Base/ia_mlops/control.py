"""Control de ejecucion de los pipelines: idempotencia por HUELLA DE ENTRADA.

IDEMPOTENTE significa: ejecutar un pipeline una vez o diez veces seguidas deja EXACTAMENTE el mismo resultado.
Se consigue con dos reglas:
  1. Cada pipeline reconstruye su capa DESDE CERO (DROP + CREATE en sus SQL): nunca añade filas a lo que habia.
  2. Antes de trabajar calcula la huella de su ENTRADA (datos que lee + codigo SQL/Python que aplica + configuracion).
     Si coincide con la de su ultima ejecucion correcta y su salida sigue ahi, no hace nada («sin cambios»).
     Asi tampoco cambian las marcas de tiempo ni se anaden ejecuciones repetidas a MLflow.
Si un pipeline falla a mitad, no registra su huella: la siguiente ejecucion lo rehace entero.

Cada ejecucion correcta queda en la tabla control_pipelines (una fila por pipeline, la ultima).
"""
import hashlib
import inspect
import json
from datetime import datetime
from pathlib import Path

from . import db

DDL = '''CREATE TABLE IF NOT EXISTS control_pipelines (
    pipeline        TEXT PRIMARY KEY,
    huella_entrada  TEXT NOT NULL,      -- sha256 de datos de entrada + codigo + configuracion
    resumen         TEXT NOT NULL,      -- JSON con lo que produjo (filas, mejor modelo...)
    ejecutado_en    TEXT NOT NULL
)'''


class EntradaFaltanteError(RuntimeError):
    """La capa de entrada no existe: hay que ejecutar antes el pipeline que la produce."""


def huella(*partes):
    """sha256 de una lista de partes (textos, numeros, diccionarios...), en orden."""
    h = hashlib.sha256()
    for p in partes:
        h.update(json.dumps(p, sort_keys=True, default=str, ensure_ascii=False).encode('utf-8'))
        h.update(b'\x1f')
    return h.hexdigest()


def huella_archivos(*rutas):
    """Huella del CODIGO: contenido de archivos SQL o Python. Si cambia una regla, cambia la huella."""
    return huella(*[(Path(r).name, Path(r).read_text(encoding='utf-8')) for r in rutas])


def huella_codigo(*objetos):
    """Huella del codigo fuente de modulos o funciones de Python."""
    return huella(*[inspect.getsource(o) for o in objetos])


def huella_tablas(con, *tablas):
    """Huella del CONTENIDO de tablas, recorridas en su orden de insercion."""
    h = hashlib.sha256()
    for t in tablas:
        h.update(t.encode())
        for fila in con.execute(f'SELECT * FROM {t} ORDER BY rowid'):
            h.update(repr(fila).encode('utf-8'))
    return h.hexdigest()


def existe(con, tabla, minimo=1):
    """¿Existe la tabla y tiene al menos `minimo` filas?"""
    if not db.escalar(con, "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name = ?", (tabla,)):
        return False
    return db.escalar(con, f'SELECT COUNT(*) FROM {tabla}') >= minimo


def exigir(con, tablas, pipeline_previo):
    """Comprueba que la entrada existe; si no, explica que pipeline ejecutar antes."""
    faltan = [t for t in tablas if not existe(con, t)]
    if faltan:
        raise EntradaFaltanteError(f'Faltan {faltan} (o estan vacias). Ejecuta antes:  python -m ia_mlops.{pipeline_previo}')


def ultima(con, pipeline):
    """(huella_entrada, resumen) de la ultima ejecucion correcta, o (None, None)."""
    con.execute(DDL)
    fila = con.execute('SELECT huella_entrada, resumen FROM control_pipelines WHERE pipeline = ?', (pipeline,)).fetchone()
    return (fila[0], json.loads(fila[1])) if fila else (None, None)


def registrar(con, pipeline, huella_entrada, resumen):
    con.execute(DDL)
    con.execute('INSERT OR REPLACE INTO control_pipelines (pipeline, huella_entrada, resumen, ejecutado_en) VALUES (?,?,?,?)',
                (pipeline, huella_entrada, json.dumps(resumen, ensure_ascii=False, default=str), datetime.now().isoformat(timespec='seconds')))
    con.commit()


def desde_terminal(funcion, **argumentos):
    """Para los `python -m ia_mlops.pipeline_...`: si falta la entrada, un mensaje claro (sin traza) y codigo de salida 2."""
    import sys
    try:
        return funcion(**argumentos)
    except EntradaFaltanteError as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(2)


def ejecutar(con, pipeline, huella_entrada, salida_ok, trabajo, forzar=False, verbose=True):
    """Patron comun: si la entrada no cambio y la salida existe, no hace nada; si no, ejecuta `trabajo()` y registra.
    Devuelve {'pipeline', 'estado': 'ejecutado' | 'sin cambios', 'huella_entrada', 'resumen'}."""
    previa, resumen = ultima(con, pipeline)
    if not forzar and previa == huella_entrada and salida_ok():
        if verbose:
            print(f'[{pipeline}] sin cambios: la entrada es la misma que en la ultima ejecucion ({huella_entrada[:12]}). Usa --forzar para rehacerlo.')
        return {'pipeline': pipeline, 'estado': 'sin cambios', 'huella_entrada': huella_entrada, 'resumen': resumen}
    if verbose:
        print(f'[{pipeline}] ejecutando (huella de entrada {huella_entrada[:12]})')
    resumen = trabajo()
    registrar(con, pipeline, huella_entrada, resumen)
    return {'pipeline': pipeline, 'estado': 'ejecutado', 'huella_entrada': huella_entrada, 'resumen': resumen}
