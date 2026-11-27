"""Servidor MCP «mcp-datos-master»: deja que un LLM consulte la capa master del caso Retail, en SQLite o en BigQuery.

POR QUÉ NO LE DAMOS «UN SQL LIBRE» SIN MÁS
    Un LLM que escribe SQL contra tu base de datos es potente y peligroso. Aquí hay cuatro capas, de fuera adentro:
      1. Herramientas con nombre y argumentos tipados (resumen_cliente, ventas_por_pais...): lo normal es no escribir SQL.
      2. Una herramienta de SQL libre (consulta_sql) pero VIGILADA: solo SELECT, una sentencia, sin comentarios, solo tablas master_*.
      3. La conexión solo puede leer: SQLite se abre en modo «ro»; BigQuery tiene un tope de bytes facturables por consulta.
      4. Un tope de filas devueltas (MAX_FILAS): el LLM no necesita 22 000 líneas, y su ventana de contexto tampoco.
    Las capas 3 y 4 no dependen del LLM ni de la vigilancia de la capa 2: si esta falla, siguen protegiendo.

DOS CONECTORES, LA MISMA INTERFAZ
    ConectorSQLite     lee curso.db (por defecto).            MCP_BACKEND=sqlite
    ConectorBigQuery   lee un dataset de BigQuery.            MCP_BACKEND=bigquery  GCP_PROJECT=...  BQ_DATASET=curso_master
    Ambos ofrecen tabla(), columnas() y ejecutar(). Las consultas usan parámetros con @nombre (valen para los dos motores).
"""
import json
import os
import re
import sqlite3
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from mcp.server.fastmcp import FastMCP

NOMBRE = 'mcp-datos-master'
TABLAS = ['master_clientes', 'master_facturas', 'master_lineas', 'master_productos']   # lo único que se puede consultar
MAX_FILAS = 50
MAX_BYTES_BQ = int(os.environ.get('MCP_BQ_MAX_BYTES', 100_000_000))                   # 100 MB por consulta: el dataset entero pesa ~2 MB


def _limpio(v):
    """Lo que devuelve una base de datos, a tipos que viajan por JSON."""
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    return v


# ------------------------------------------------------------------------------------------------ conectores
class ConectorSQLite:
    nombre = 'sqlite'

    def __init__(self, ruta):
        self.ruta = Path(ruta)
        if not self.ruta.is_file():
            raise FileNotFoundError(f'No existe {self.ruta.name}: crea la base con  python -m ia_mlops.pipeline  (desde 04-Proyecto-Base)')

    def tabla(self, t):
        return t

    def _abrir(self):
        con = sqlite3.connect(self.ruta.resolve().as_uri() + '?mode=ro', uri=True)      # SOLO LECTURA: un UPDATE falla aunque se cuele
        con.row_factory = sqlite3.Row
        return con

    def ejecutar(self, sql, params=None):
        con = self._abrir()
        try:
            filas = [dict(f) for f in con.execute(sql, params or {}).fetchmany(MAX_FILAS + 1)]
        finally:
            con.close()
        return [{k: _limpio(v) for k, v in f.items()} for f in filas]

    def columnas(self, t):
        con = self._abrir()
        try:
            return [{'nombre': r[1], 'tipo': r[2] or 'sin tipo'} for r in con.execute(f'PRAGMA table_info("{t}")')]
        finally:
            con.close()


class ConectorBigQuery:
    nombre = 'bigquery'

    def __init__(self, proyecto, dataset):
        from google.cloud import bigquery
        self.bq = bigquery
        self.proyecto, self.dataset = proyecto, dataset
        self.cliente = bigquery.Client(project=proyecto)

    def tabla(self, t):
        return f'`{self.proyecto}.{self.dataset}.{t}`'

    def ejecutar(self, sql, params=None):
        tipos = {bool: 'BOOL', int: 'INT64', float: 'FLOAT64', str: 'STRING'}
        parametros = [self.bq.ScalarQueryParameter(k, tipos[type(v)], v) for k, v in (params or {}).items()]
        config = self.bq.QueryJobConfig(query_parameters=parametros, maximum_bytes_billed=MAX_BYTES_BQ)   # tope de coste por consulta
        job = self.cliente.query(sql, job_config=config)
        return [{k: _limpio(v) for k, v in dict(f.items()).items()} for f in job.result(max_results=MAX_FILAS + 1)]

    def columnas(self, t):
        esquema = self.cliente.get_table(f'{self.proyecto}.{self.dataset}.{t}').schema
        return [{'nombre': c.name, 'tipo': c.field_type} for c in esquema]


def elegir_conector():
    backend = os.environ.get('MCP_BACKEND', 'sqlite').lower()
    if backend == 'sqlite':
        return ConectorSQLite(os.environ.get('CURSO_DB', 'curso.db'))
    if backend == 'bigquery':
        proyecto = os.environ.get('GCP_PROJECT')
        if not proyecto:
            raise RuntimeError('Con MCP_BACKEND=bigquery hace falta GCP_PROJECT (y, si no es curso_master, BQ_DATASET).')
        return ConectorBigQuery(proyecto, os.environ.get('BQ_DATASET', 'curso_master'))
    raise RuntimeError(f'MCP_BACKEND debe ser «sqlite» o «bigquery», no «{backend}».')


# ------------------------------------------------------------------------------------------------ vigilancia del SQL libre
PROHIBIDAS = re.compile(r'\b(insert|update|delete|drop|alter|create|attach|detach|pragma|replace|merge|truncate|grant|revoke|'
                        r'export|call|load|load_extension|readfile|writefile|fts3_tokenizer|vacuum|reindex|begin|commit|execute|set)\b', re.I)


def validar_sql(sql):
    """Devuelve (sql_limpio, None) si es aceptable, o (None, motivo). Es la capa 2: la que NO hay que creerse del todo."""
    if not isinstance(sql, str) or not sql.strip():
        return None, 'Escribe una consulta SELECT.'
    s = sql.strip()
    if '--' in s or '/*' in s or '#' in s:
        return None, 'No se admiten comentarios en la consulta.'
    s = s.rstrip(';').strip()
    if ';' in s:
        return None, 'Solo se admite una sentencia.'
    if not re.match(r'(?is)^(select|with)\b', s):
        return None, 'Solo se admiten consultas que empiecen por SELECT (o WITH).'
    m = PROHIBIDAS.search(s)
    if m:
        return None, f'Palabra no permitida: «{m.group(1).upper()}». Esta herramienta solo lee.'
    ctes = {c.lower() for c in re.findall(r'(?is)(?:\bwith|,)\s*(\w+)\s+as\s*\(', s)}
    for t in re.findall(r'(?is)\b(?:from|join)\s+([`"\[]?[\w.\-]+[`"\]]?)', s):
        t = t.strip('`"[]')
        if '.' in t:
            return None, f'Escribe solo el nombre de la tabla, sin proyecto ni dataset: «{t}».'
        if t.lower() not in TABLAS and t.lower() not in ctes:
            return None, f'La tabla «{t}» no está permitida. Tablas: {", ".join(TABLAS)}.'
    if re.search(r'(?is)\b(?:from|join)\s+\w+(?:\s+(?:as\s+)?\w+)?\s*,', s):
        return None, 'No se admiten listas de tablas separadas por comas: usa JOIN.'
    return s, None


def cualificar(sql, conector):
    """master_clientes -> `proyecto.dataset.master_clientes` en BigQuery (en SQLite no cambia). Solo detrás de FROM/JOIN."""
    return re.sub(r'(?is)\b(from|join)(\s+)(master_\w+)\b', lambda m: f'{m.group(1)}{m.group(2)}{conector.tabla(m.group(3).lower())}', sql)


# ------------------------------------------------------------------------------------------------ servidor
servidor = FastMCP(NOMBRE, instructions=(
    'Consultas de LECTURA sobre la capa master del caso Retail (clientes, facturas, líneas y productos). Para lo habitual usa resumen_cliente, '
    'ultimas_facturas, ventas_por_pais o top_productos; consulta_sql solo si ninguna sirve. Responde con lo que devuelvan las herramientas; '
    'si devuelven «error», díselo al usuario y no inventes datos. No hay nombres ni correos: solo número de cliente y país.'))
_conector = None


def conector():
    global _conector
    if _conector is None:
        _conector = elegir_conector()
    return _conector


def _ejecutar(sql, params=None):
    c = conector()
    try:
        filas = c.ejecutar(cualificar(sql, c), params)
    except Exception as e:                                           # noqa: BLE001 - al LLM le llega el motivo, no un traceback
        return {'error': f'{type(e).__name__}: {str(e)[:300]}', 'motor': c.nombre}
    truncado = len(filas) > MAX_FILAS
    return {'motor': c.nombre, 'filas': filas[:MAX_FILAS], 'n': min(len(filas), MAX_FILAS), 'truncado': truncado}


def _entero(valor, nombre, minimo=1, maximo=None):
    try:
        v = int(valor)
    except (TypeError, ValueError):
        return None, {'error': f'«{nombre}» debe ser un número entero, no «{valor}».'}
    if v < minimo or (maximo is not None and v > maximo):
        return None, {'error': f'«{nombre}» debe estar entre {minimo} y {maximo if maximo is not None else "…"}.'}
    return v, None


@servidor.tool(name='listar_tablas', description='Las tablas de la capa master que se pueden consultar, con su número de filas y el motor (sqlite o bigquery). Empieza por aquí.')
def listar_tablas() -> dict:
    c = conector()
    salida = []
    for t in TABLAS:
        r = _ejecutar(f'SELECT COUNT(*) AS filas FROM {t}')
        salida.append({'tabla': t, 'filas': r['filas'][0]['filas'] if 'filas' in r else r})
    return {'motor': c.nombre, 'tablas': salida}


@servidor.tool(name='describir_tabla', description='Columnas (nombre y tipo) de una tabla master y 3 filas de ejemplo. Argumento: tabla (una de listar_tablas).')
def describir_tabla(tabla: str) -> dict:
    t = str(tabla).strip().lower()
    if t not in TABLAS:
        return {'error': f'La tabla «{tabla}» no existe o no está permitida. Tablas: {", ".join(TABLAS)}.'}
    try:
        columnas = conector().columnas(t)
    except Exception as e:                                           # noqa: BLE001
        return {'error': f'{type(e).__name__}: {str(e)[:300]}'}
    muestra = _ejecutar(f'SELECT * FROM {t} LIMIT 3')
    return {'tabla': t, 'motor': conector().nombre, 'columnas': columnas, 'muestra': muestra.get('filas', muestra)}


@servidor.tool(name='resumen_cliente', description=(
    'Resumen de UN cliente: país, primer y último movimiento, facturas, cancelaciones y monto de ventas válidas. '
    'Úsala cuando pregunten por un cliente concreto. Argumento: cliente_id (número).'))
def resumen_cliente(cliente_id: int) -> dict:
    cid, error = _entero(cliente_id, 'cliente_id', 0)
    if error:
        return error
    r = _ejecutar('''SELECT c.cliente_id, c.pais, c.primer_movimiento, c.ultimo_movimiento,
        COUNT(DISTINCT CASE WHEN f.es_cancelacion = 0 THEN f.factura_id END) AS facturas,
        COUNT(DISTINCT CASE WHEN f.es_cancelacion = 1 THEN f.factura_id END) AS cancelaciones,
        ROUND(SUM(CASE WHEN l.es_venta_valida = 1 THEN l.monto_linea ELSE 0 END), 2) AS monto_ventas
        FROM master_clientes c
        LEFT JOIN master_facturas f ON f.cliente_id = c.cliente_id
        LEFT JOIN master_lineas l ON l.factura_id = f.factura_id
        WHERE c.cliente_id = @cliente_id
        GROUP BY c.cliente_id, c.pais, c.primer_movimiento, c.ultimo_movimiento''', {'cliente_id': cid})
    if 'error' in r:
        return r
    if not r['filas']:
        return {'error': f'No existe el cliente {cid} en master_clientes.'}
    return {'motor': r['motor'], **r['filas'][0]}


@servidor.tool(name='ultimas_facturas', description='Las últimas n facturas de UN cliente (fecha, país, si es cancelación y total de la factura). Argumentos: cliente_id y n (por defecto 5, máximo 20).')
def ultimas_facturas(cliente_id: int, n: int = 5) -> dict:
    cid, error = _entero(cliente_id, 'cliente_id', 0)
    if error:
        return error
    n, error = _entero(n, 'n', 1, 20)
    if error:
        return error
    return _ejecutar('''SELECT f.factura_id, f.fecha_factura, f.pais, f.es_cancelacion, ROUND(SUM(l.monto_linea), 2) AS total
        FROM master_facturas f JOIN master_lineas l ON l.factura_id = f.factura_id
        WHERE f.cliente_id = @cliente_id
        GROUP BY f.factura_id, f.fecha_factura, f.pais, f.es_cancelacion
        ORDER BY f.fecha_factura DESC, f.factura_id DESC LIMIT @n''', {'cliente_id': cid, 'n': n})


@servidor.tool(name='ventas_por_pais', description='Los n países con más ventas válidas: facturas, clientes distintos y monto. Argumento: n (por defecto 5, máximo 50).')
def ventas_por_pais(n: int = 5) -> dict:
    n, error = _entero(n, 'n', 1, 50)
    if error:
        return error
    return _ejecutar('''SELECT f.pais, COUNT(DISTINCT f.factura_id) AS facturas, COUNT(DISTINCT f.cliente_id) AS clientes,
        ROUND(SUM(l.monto_linea), 2) AS monto
        FROM master_facturas f JOIN master_lineas l ON l.factura_id = f.factura_id
        WHERE l.es_venta_valida = 1
        GROUP BY f.pais ORDER BY monto DESC, f.pais LIMIT @n''', {'n': n})


@servidor.tool(name='top_productos', description='Los n productos más vendidos por unidades (solo ventas válidas y productos reales). Argumento: n (por defecto 5, máximo 50).')
def top_productos(n: int = 5) -> dict:
    n, error = _entero(n, 'n', 1, 50)
    if error:
        return error
    return _ejecutar('''SELECT p.codigo_producto, p.descripcion, SUM(l.cantidad) AS unidades, ROUND(SUM(l.monto_linea), 2) AS monto
        FROM master_lineas l JOIN master_productos p ON p.codigo_producto = l.codigo_producto
        WHERE l.es_venta_valida = 1 AND p.es_producto = 1
        GROUP BY p.codigo_producto, p.descripcion ORDER BY unidades DESC, p.codigo_producto LIMIT @n''', {'n': n})


@servidor.tool(name='consulta_sql', description=(
    f'Último recurso: una consulta SELECT propia sobre {", ".join(TABLAS)}. Una sola sentencia, sin comentarios, sin escribir proyecto ni dataset, '
    f'con alias de tabla; devuelve como máximo {MAX_FILAS} filas. Usa antes las otras herramientas. Argumento: sql.'))
def consulta_sql(sql: str) -> dict:
    limpio, motivo = validar_sql(sql)
    if motivo:
        return {'error': motivo, 'rechazada_por': 'vigilancia del SQL'}
    return _ejecutar(limpio)


def main():
    try:
        c = conector()
    except Exception as e:                                           # noqa: BLE001
        print(f'{NOMBRE}: no arranca: {e}', file=sys.stderr)
        sys.exit(1)
    print(f'{NOMBRE}: motor {c.nombre}', file=sys.stderr)               # por stderr: stdout es el canal del protocolo
    servidor.run(transport='stdio')


if __name__ == '__main__':
    main()
