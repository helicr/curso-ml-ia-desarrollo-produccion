"""Exporta a CSV las lineas de venta del caso (capa MASTER de 04-Proyecto-Base/data/processed/curso.db), con la factura, el cliente y el pais.

Es el dato que se sube a Cloud Storage y que lee el job de Spark. Solo usa la biblioteca estandar de Python.

Uso:  python3 exportar_datos.py --proyecto RUTA/04-Proyecto-Base --salida /tmp/curso-dataproc/ventas_lineas.csv
"""
import argparse
import csv
import sqlite3
from pathlib import Path

CONSULTA = """
SELECT l.linea_id, l.factura_id, f.cliente_id, f.fecha_factura, f.pais, f.es_cancelacion,
       l.codigo_producto, l.cantidad, l.precio_unitario, l.monto_linea, l.es_venta_valida
FROM master_lineas l JOIN master_facturas f ON f.factura_id = l.factura_id
ORDER BY l.linea_id
"""


def exportar(base, destino):
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(f'{Path(base).resolve().as_uri()}?mode=ro', uri=True)   # solo lectura
    try:
        cursor = con.execute(CONSULTA)
        columnas = [c[0] for c in cursor.description]
        n = 0
        with open(destino, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(columnas)
            for fila in cursor:
                w.writerow(fila)
                n += 1
    finally:
        con.close()
    return n, columnas


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--proyecto', required=True, help='carpeta 04-Proyecto-Base')
    ap.add_argument('--salida', required=True, help='CSV de salida')
    a = ap.parse_args()
    n, columnas = exportar(Path(a.proyecto) / 'data' / 'processed' / 'curso.db', a.salida)
    print(f'{n} lineas exportadas a {a.salida}')
    print('columnas:', ', '.join(columnas))
