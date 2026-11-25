"""Comprueba el resultado de Spark: recalcula por_pais con la biblioteca estandar a partir del mismo CSV y lo compara con la salida del job.

Uso:  python3 comprobar_resultado.py --entrada ventas_lineas.csv --por-pais carpeta_con_part-*.csv
Termina con codigo 1 si algun pais no coincide.
"""
import argparse
import csv
import glob
from collections import defaultdict


def calcular(entrada):
    facturas, clientes, monto = defaultdict(set), defaultdict(set), defaultdict(float)
    with open(entrada, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['es_venta_valida'] != '1':
                continue
            p = r['pais']
            facturas[p].add(r['factura_id'])
            # Hay compras SIN cliente (cliente_id vacío). countDistinct de Spark, como COUNT(DISTINCT) en SQL, ignora los nulos;
            # contarlos aquí daba un cliente de más en EIRE y en Reino Unido (visto el 25/11/2026). Se cuentan igual que Spark.
            if r['cliente_id']:
                clientes[p].add(r['cliente_id'])
            monto[p] += float(r['monto_linea'])
    return {p: (len(facturas[p]), len(clientes[p]), round(monto[p], 2)) for p in facturas}


def leer_spark(carpeta):
    out = {}
    for ruta in sorted(glob.glob(f'{carpeta}/part-*.csv')):
        with open(ruta, newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                out[r['pais']] = (int(r['facturas']), int(r['clientes']), round(float(r['monto_total']), 2))
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--entrada', required=True)
    ap.add_argument('--por-pais', required=True)
    a = ap.parse_args()
    local, spark = calcular(a.entrada), leer_spark(a.por_pais)
    if not spark:
        raise SystemExit('ERROR: no hay ficheros part-*.csv en la salida de Spark')
    mal = [p for p in sorted(set(local) | set(spark))
           if p not in local or p not in spark or local[p][:2] != spark[p][:2] or abs(local[p][2] - spark[p][2]) > 0.02]
    if mal:
        for p in mal:
            print(f'DIFERENCIA en {p}: local={local.get(p)} spark={spark.get(p)}')
        raise SystemExit(1)
    print(f'OK: {len(spark)} paises; facturas, clientes y monto coinciden con el calculo local.')
