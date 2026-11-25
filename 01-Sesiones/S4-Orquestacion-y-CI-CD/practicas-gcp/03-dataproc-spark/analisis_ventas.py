"""Job de PySpark: agregados de ventas del caso Online Retail II (se ejecuta en Dataproc sin servidor, NO en Cloud Shell).

Lee el CSV de lineas de venta (ventas_lineas.csv, generado con exportar_datos.py) y escribe dos tablas en Cloud Storage:
  por_pais/  por pais: facturas, clientes distintos, monto total y ticket medio (solo lineas de venta validas)
  rfm/       por cliente: recencia (dias desde su ultima compra hasta la ultima fecha de los datos), frecuencia (facturas) y monto

Uso (lo lanza crear.sh):  --entrada gs://BUCKET/entrada/ventas_lineas.csv --salida gs://BUCKET/salida
"""
import argparse

from pyspark.sql import SparkSession, functions as F


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--entrada', required=True)
    ap.add_argument('--salida', required=True)
    a = ap.parse_args()

    spark = SparkSession.builder.appName('ventas-retencion').getOrCreate()
    lineas = (spark.read.option('header', True).option('inferSchema', True).csv(a.entrada)
              .withColumn('fecha', F.to_timestamp('fecha_factura')))
    ventas = lineas.where(F.col('es_venta_valida') == 1)
    print(f'lineas leidas: {lineas.count()} | lineas de venta validas: {ventas.count()}')

    por_pais = (ventas.groupBy('pais')
                .agg(F.countDistinct('factura_id').alias('facturas'),
                     F.countDistinct('cliente_id').alias('clientes'),
                     F.round(F.sum('monto_linea'), 2).alias('monto_total'))
                .withColumn('ticket_medio', F.round(F.col('monto_total') / F.col('facturas'), 2))
                .orderBy(F.desc('monto_total'), 'pais'))
    por_pais.coalesce(1).write.mode('overwrite').option('header', True).csv(f'{a.salida}/por_pais')

    ultima = ventas.agg(F.max('fecha').alias('m')).first()['m']
    rfm = (ventas.groupBy('cliente_id')
           .agg(F.max('fecha').alias('ultima_compra'),
                F.countDistinct('factura_id').alias('frecuencia'),
                F.round(F.sum('monto_linea'), 2).alias('monto'))
           .withColumn('recencia_dias', F.datediff(F.lit(ultima), F.col('ultima_compra')))
           .select('cliente_id', 'recencia_dias', 'frecuencia', 'monto')
           .orderBy(F.desc('monto'), 'cliente_id'))
    rfm.coalesce(1).write.mode('overwrite').option('header', True).csv(f'{a.salida}/rfm')

    print('por_pais:')
    por_pais.show(10, truncate=False)
    print('rfm (los 5 con mas monto):')
    rfm.show(5, truncate=False)
    spark.stop()


if __name__ == '__main__':
    main()
