"""Reglas de calidad de la capa MASTER.

Una regla de calidad es una consulta SQL que devuelve UN numero, mas un criterio que dice si ese numero es aceptable.
Hay tres tipos:
  duro    -> si falla, el pipeline se detiene (estado ERROR): seguir produciria resultados falsos.
             Ej.: R01, conciliacion: lineas de RAW = lineas de MASTER + descartes.
  alerta  -> se registra y se avisa, pero el pipeline sigue (estado ALERTA).
             Ej.: R06, facturas cuyas lineas tienen fechas distintas (MASTER toma la primera).
  info    -> solo informa (estado OK). Ej.: R08, porcentaje de lineas sin cliente.
El resultado queda en la tabla master_calidad, con fecha: es la evidencia de que el dato se reviso.
La misma lista esta en el cuaderno 01; las pruebas exigen que ambos produzcan la misma tabla.
"""
from datetime import datetime

FECHA_MINIMA = '2009-12-01'
FECHA_LIMITE = '2012-01-01'   # exclusiva


class CalidadError(RuntimeError):
    pass


def _reglas():
    cero = lambda v: v == 0  # noqa: E731
    return [
        ('R01_conciliacion', 'Líneas de RAW menos (líneas de MASTER + descartes). Debe ser 0.',
         "SELECT (SELECT COUNT(*) FROM raw_lineas_factura) - (SELECT COUNT(*) FROM master_lineas) - (SELECT COUNT(*) FROM master_descartes)",
         'duro', '= 0', cero),
        ('R02_facturas_sin_lineas', 'Facturas que no tienen ninguna línea.',
         "SELECT COUNT(*) FROM master_facturas f WHERE NOT EXISTS (SELECT 1 FROM master_lineas l WHERE l.factura_id = f.factura_id)",
         'duro', '= 0', cero),
        ('R03_integridad_referencial', 'Violaciones de claves foráneas.', None, 'duro', '= 0', cero),
        ('R04_monto_coherente', 'Líneas donde monto_linea no es cantidad por precio.',
         "SELECT COUNT(*) FROM master_lineas WHERE ABS(monto_linea - ROUND(cantidad * precio_unitario, 2)) > 0.01",
         'duro', '= 0', cero),
        ('R05_fechas_en_rango', f'Facturas fuera del rango {FECHA_MINIMA} a {FECHA_LIMITE} (exclusivo).',
         f"SELECT COUNT(*) FROM master_facturas WHERE fecha_factura < '{FECHA_MINIMA}' OR fecha_factura >= '{FECHA_LIMITE}'",
         'duro', '= 0', cero),
        ('R06_facturas_con_varias_fechas', 'Facturas de RAW cuyas líneas tienen fechas distintas (MASTER toma la primera).',
         "SELECT COUNT(*) FROM (SELECT TRIM(factura_id) FROM raw_lineas_factura "
         "GROUP BY TRIM(factura_id) HAVING COUNT(DISTINCT registrada_en) > 1)",
         'alerta', '= 0', cero),
        ('R07_cancelaciones_con_cantidad_positiva', 'Líneas de facturas canceladas con cantidad positiva.',
         "SELECT COUNT(*) FROM master_lineas l JOIN master_facturas f ON f.factura_id = l.factura_id WHERE f.es_cancelacion = 1 AND l.cantidad > 0",
         'alerta', '= 0', cero),
        ('R08_pct_lineas_sin_cliente', 'Porcentaje de líneas cuya factura no trae Customer ID (no entran en FS).',
         "SELECT ROUND(100.0 * SUM(CASE WHEN f.cliente_id IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2) "
         "FROM master_lineas l JOIN master_facturas f ON f.factura_id = l.factura_id",
         'info', 'informativo', None),
        ('R09_pct_ventas_validas', 'Porcentaje de líneas que son ventas válidas.',
         "SELECT ROUND(100.0 * SUM(es_venta_valida) / COUNT(*), 2) FROM master_lineas",
         'info', 'informativo', None),
        ('R10_duplicados_descartados', 'Filas descartadas por ser duplicados exactos.',
         "SELECT COUNT(*) FROM master_descartes WHERE motivo = 'duplicado_exacto'", 'info', 'informativo', None),
        ('R11_lineas_precio_no_positivo', 'Líneas con precio menor o igual a cero.',
         "SELECT COUNT(*) FROM master_lineas WHERE precio_unitario <= 0", 'info', 'informativo', None),
        ('R12_codigos_que_no_son_producto', 'Códigos de StockCode que no son productos (envío, comisiones, ajustes...).',
         "SELECT COUNT(*) FROM master_productos WHERE es_producto = 0", 'info', 'informativo', None),
        ('R13_clientes_distintos', 'Clientes distintos en MASTER.',
         "SELECT COUNT(*) FROM master_clientes", 'info', 'informativo', None),
    ]


def evaluar(con, lanzar=True):
    """Ejecuta todas las reglas, las guarda en master_calidad y devuelve la lista de resultados."""
    ahora = datetime.now().isoformat(timespec='seconds')
    resultados, errores = [], []
    con.execute('DELETE FROM master_calidad')
    for regla, descripcion, sql, tipo, umbral, cumple in _reglas():
        if regla == 'R03_integridad_referencial':
            valor = len(con.execute('PRAGMA foreign_key_check').fetchall())
        else:
            valor = con.execute(sql).fetchone()[0]
        if tipo == 'info':
            estado = 'OK'
        else:
            ok = cumple(valor)
            estado = 'OK' if ok else ('ERROR' if tipo == 'duro' else 'ALERTA')
        if estado == 'ERROR':
            errores.append(f'{regla}: {descripcion} -> {valor}')
        con.execute('INSERT INTO master_calidad (regla, descripcion, valor, umbral, estado, evaluado_en) VALUES (?,?,?,?,?,?)',
                    (regla, descripcion, valor, umbral, estado, ahora))
        resultados.append({'regla': regla, 'descripcion': descripcion, 'valor': valor, 'umbral': umbral, 'estado': estado})
    con.commit()
    if errores and lanzar:
        raise CalidadError('Fallaron reglas de calidad duras:\n  ' + '\n  '.join(errores))
    return resultados
