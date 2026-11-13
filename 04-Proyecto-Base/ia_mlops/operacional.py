"""Base operacional «retail»: simula el sistema de ventas de la tienda, que es la fuente del pipeline.

Es la traduccion a Python del cuaderno notebooks/00_pipeline_operacional.ipynb.

QUE ES UN SISTEMA OPERACIONAL (OLTP)
    La base con la que funciona el negocio: registra cada venta en el momento. Esta NORMALIZADA (cada dato se guarda
    una sola vez, en la tabla a la que pertenece) y tiene claves y restricciones. El pipeline analitico la LEE, nunca escribe en ella.

POR QUE SE SIMULA
    El dataset de UCI es una exportacion plana (una fila por linea de factura, con cliente y pais repetidos en cada linea).
    Aqui se hace el camino inverso: se reconstruye el modelo normalizado que tendria la tienda, y el pipeline ingiere
    desde una base de datos, como en produccion.

MODELO (sql/operacional/01_crear_operacional.sql)
    clientes 0..1 --- 0..n facturas 1 --- 1..n lineas_factura n --- 1 productos
    + origen_simulacion: control (de que archivo sale la simulacion y su huella). No es parte del negocio.

NO LIMPIA NADA
    La suciedad del origen (lineas repetidas, descripciones vacias, ventas sin cliente, cancelaciones, codigos que no son
    productos) se conserva para que RAW la reciba y MASTER la trate. Solo se comprueba que normalizar no pierde informacion:
    cada factura debe tener un unico cliente y un unico pais (la fecha, que si varia, se guarda en cada linea).

Uso desde la terminal (en la carpeta del proyecto):
    python -m ia_mlops.operacional                     # desde la muestra del repositorio (segundos)
    python -m ia_mlops.operacional --fuente completo   # desde el Excel original (descargalo antes)
"""
import argparse
from datetime import datetime

from . import config, db
from .dataset import leer_lineas, sha256_archivo

TABLAS = ['clientes', 'productos', 'facturas', 'lineas_factura']   # el modelo de negocio, en orden de dependencias


def comprobar_cabeceras(con):
    """Cada factura debe tener un solo cliente y un solo pais; si no, normalizar perderia informacion."""
    return {
        'facturas con varios clientes': db.escalar(con, 'SELECT COUNT(*) FROM (SELECT factura_id FROM temp.tmp_origen GROUP BY factura_id '
                                                        'HAVING COUNT(DISTINCT IFNULL(cliente_id, -1)) > 1)'),
        'facturas con varios paises': db.escalar(con, 'SELECT COUNT(*) FROM (SELECT factura_id FROM temp.tmp_origen GROUP BY factura_id '
                                                      'HAVING COUNT(DISTINCT pais) > 1)'),
    }


def crear_operacional(fuente='muestra', ruta=None, verbose=True):
    """Crea data/external/retail.db desde la fuente y devuelve el numero de lineas."""
    con = db.conectar(ruta or config.DB_OPERACIONAL)
    try:
        db.ejecutar_script(con, config.SQL / 'operacional' / '01_crear_operacional.sql')
        archivo, lineas = leer_lineas(fuente)
        con.execute('CREATE TEMP TABLE tmp_origen (linea_id INTEGER, factura_id TEXT, codigo_producto TEXT, descripcion TEXT, '
                    'cantidad INTEGER, registrada_en TEXT, precio_unitario REAL, cliente_id INTEGER, pais TEXT)')
        con.executemany('INSERT INTO temp.tmp_origen VALUES (?,?,?,?,?,?,?,?,?)', lineas)
        conflictos = {k: v for k, v in comprobar_cabeceras(con).items() if v}
        if conflictos:
            raise ValueError(f'El origen no se puede normalizar sin perder informacion: {conflictos}')
        db.ejecutar_script(con, config.SQL / 'operacional' / '02_poblar_operacional.sql')
        con.execute('INSERT INTO origen_simulacion (fuente, archivo, sha256, filas, creada_en) VALUES (?,?,?,?,?)',
                    (fuente, archivo.name, sha256_archivo(archivo), len(lineas), datetime.now().isoformat(timespec='seconds')))
        con.execute('DROP TABLE temp.tmp_origen')
        con.commit()
        if verbose:
            for tabla in TABLAS:
                print(f'  OPERACIONAL: {tabla:15s} {db.escalar(con, f"SELECT COUNT(*) FROM {tabla}"):>10,} filas')
        return len(lineas)
    finally:
        con.close()


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--fuente', choices=list(config.FUENTES), default='muestra')
    crear_operacional(ap.parse_args().fuente)
