"""Pruebas del extra «MCP en notebooks»: los servidores (con una base de juguete, sin tocar curso.db) y los notebooks ya ejecutados.

    python -m pytest pruebas/test_servidores_y_notebooks.py -q      (desde extra-mcp-notebooks/, con el entorno del curso)
No hace falta Internet ni BigQuery: el conector de BigQuery se prueba con un conector falso que solo comprueba cómo se reescribe el SQL.
La prueba REAL de BigQuery se hizo en Cloud Shell el 26/11/2026 y está descrita en README.md (no se puede repetir aquí sin credenciales).
"""
import json
import sqlite3
import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parents[1]
FUENTES = AQUI / 'fuentes'
pytest.importorskip('mcp', reason='falta el paquete mcp: pip install -r requisitos-extra-mcp.txt')
nbformat = pytest.importorskip('nbformat')
sys.path.insert(0, str(FUENTES))
import mcp_datos as D  # noqa: E402


@pytest.fixture()
def bd(tmp_path):
    ruta = tmp_path / 'juguete.db'
    con = sqlite3.connect(ruta)
    con.executescript('''
        CREATE TABLE master_clientes (cliente_id INTEGER, pais TEXT, primer_movimiento TEXT, ultimo_movimiento TEXT);
        CREATE TABLE master_facturas (factura_id TEXT, cliente_id INTEGER, fecha_factura TEXT, pais TEXT, es_cancelacion INTEGER);
        CREATE TABLE master_lineas (linea_id INTEGER, factura_id TEXT, codigo_producto TEXT, cantidad INTEGER, precio_unitario REAL, monto_linea REAL, es_venta_valida INTEGER);
        CREATE TABLE master_productos (codigo_producto TEXT, descripcion TEXT, es_producto INTEGER);
        CREATE TABLE secreta (dato TEXT);
        INSERT INTO master_clientes VALUES (1, 'Spain', '2010-01-01', '2010-06-01'), (2, 'France', '2010-02-01', '2010-07-01');
        INSERT INTO master_facturas VALUES ('F1', 1, '2010-06-01', 'Spain', 0), ('F2', 1, '2010-07-01', 'Spain', 1), ('F3', 2, '2010-07-02', 'France', 0);
        INSERT INTO master_lineas VALUES (1, 'F1', 'P1', 2, 5.0, 10.0, 1), (2, 'F1', 'P2', 1, 7.5, 7.5, 1), (3, 'F2', 'P1', -1, 5.0, -5.0, 0), (4, 'F3', 'P1', 3, 5.0, 15.0, 1);
        INSERT INTO master_productos VALUES ('P1', 'LAMP', 1), ('P2', 'MUG', 1);
        INSERT INTO secreta VALUES ('no debe verse');
    ''')
    con.commit()
    con.close()
    return ruta


@pytest.fixture()
def servidor(bd, monkeypatch):
    monkeypatch.setattr(D, '_conector', D.ConectorSQLite(bd))
    return D


# ------------------------------------------------------------------------------------------------ vigilancia del SQL
ACEPTADAS = ['SELECT * FROM master_clientes', 'select pais, count(*) from master_clientes group by pais;',
             'WITH x AS (SELECT cliente_id FROM master_clientes) SELECT COUNT(*) FROM x',
             'SELECT c.pais FROM master_clientes c JOIN master_facturas f ON f.cliente_id = c.cliente_id']
RECHAZADAS = {
    'DROP TABLE master_clientes': 'SELECT',
    "UPDATE master_clientes SET pais = 'X'": 'SELECT',
    'SELECT 1; DELETE FROM master_lineas': 'sola sentencia|una sentencia',
    'SELECT * FROM master_clientes -- x': 'comentario',
    'SELECT * FROM master_clientes /* x */': 'comentario',
    'SELECT * FROM secreta': 'no está permitida',
    'SELECT name FROM sqlite_master': 'no está permitida',
    'SELECT * FROM main.master_clientes': 'sin proyecto',
    'SELECT * FROM master_clientes, master_facturas': 'comas',
    'SELECT * FROM master_clientes WHERE 1=1 AND pais IN (SELECT dato FROM secreta)': 'no está permitida',
    'DELETE FROM master_clientes': 'SELECT',
    'SELECT load_extension("x")': 'no permitida',
    '': 'SELECT',
}


@pytest.mark.parametrize('sql', ACEPTADAS)
def test_validar_sql_acepta_consultas_normales(sql):
    limpio, motivo = D.validar_sql(sql)
    assert motivo is None and limpio


@pytest.mark.parametrize('sql,patron', RECHAZADAS.items())
def test_validar_sql_rechaza_lo_peligroso(sql, patron):
    import re
    limpio, motivo = D.validar_sql(sql)
    assert limpio is None and re.search(patron, motivo, re.I), (sql, motivo)


def test_cualificar_solo_reescribe_detras_de_from_y_join():
    class Falso:
        def tabla(self, t):
            return f'`p.d.{t}`'
    sql = 'SELECT master_clientes.pais FROM master_clientes JOIN master_facturas f ON f.cliente_id = master_clientes.cliente_id'
    assert D.cualificar(sql, Falso()) == ('SELECT master_clientes.pais FROM `p.d.master_clientes` JOIN `p.d.master_facturas` f ON f.cliente_id = master_clientes.cliente_id')


# ------------------------------------------------------------------------------------------------ conector SQLite
def test_la_conexion_de_sqlite_es_de_solo_lectura(bd):
    c = D.ConectorSQLite(bd)
    with pytest.raises(sqlite3.OperationalError, match='readonly'):
        c.ejecutar("UPDATE master_clientes SET pais = 'X'")
    with pytest.raises(sqlite3.OperationalError, match='readonly'):
        c.ejecutar('DROP TABLE master_clientes')
    assert c.ejecutar('SELECT COUNT(*) AS n FROM master_clientes') == [{'n': 2}]


def test_conector_sqlite_sin_base_dice_que_hacer(tmp_path):
    with pytest.raises(FileNotFoundError, match='pipeline'):
        D.ConectorSQLite(tmp_path / 'no_existe.db')


def test_elegir_conector_exige_proyecto_para_bigquery(monkeypatch):
    monkeypatch.setenv('MCP_BACKEND', 'bigquery')
    monkeypatch.delenv('GCP_PROJECT', raising=False)
    with pytest.raises(RuntimeError, match='GCP_PROJECT'):
        D.elegir_conector()
    monkeypatch.setenv('MCP_BACKEND', 'oracle')
    with pytest.raises(RuntimeError, match='sqlite'):
        D.elegir_conector()


# ------------------------------------------------------------------------------------------------ herramientas
def test_resumen_cliente_cuenta_facturas_cancelaciones_y_monto_valido(servidor):
    r = servidor.resumen_cliente(1)
    assert (r['facturas'], r['cancelaciones'], r['monto_ventas'], r['pais'], r['motor']) == (1, 1, 17.5, 'Spain', 'sqlite')


def test_cliente_inexistente_y_argumentos_mal_dados_devuelven_error_no_excepcion(servidor):
    assert 'No existe' in servidor.resumen_cliente(99)['error']
    assert 'entero' in servidor.resumen_cliente('abc')['error']
    assert 'entre 1 y 20' in servidor.ultimas_facturas(1, 500)['error']
    assert 'no existe o no está permitida' in servidor.describir_tabla('secreta')['error']


def test_ventas_por_pais_y_top_productos_solo_cuentan_ventas_validas(servidor):
    paises = servidor.ventas_por_pais(5)['filas']
    assert paises == [{'pais': 'Spain', 'facturas': 1, 'clientes': 1, 'monto': 17.5}, {'pais': 'France', 'facturas': 1, 'clientes': 1, 'monto': 15.0}]
    top = servidor.top_productos(5)['filas']
    assert top[0]['codigo_producto'] == 'P1' and top[0]['unidades'] == 5


def test_el_parametro_no_permite_inyeccion(servidor):
    r = servidor.ultimas_facturas('1 OR 1=1', 5)
    assert 'error' in r                                   # no es un entero: ni llega al SQL


def test_consulta_sql_tiene_tope_de_filas(servidor, monkeypatch):
    monkeypatch.setattr(D, 'MAX_FILAS', 2)
    r = servidor.consulta_sql('SELECT * FROM master_lineas')
    assert r['n'] == 2 and r['truncado'] is True and len(r['filas']) == 2


def test_consulta_sql_devuelve_el_motivo_cuando_la_vigilancia_rechaza(servidor):
    r = servidor.consulta_sql('SELECT * FROM secreta')
    assert r['rechazada_por'] == 'vigilancia del SQL' and 'no está permitida' in r['error']


# ------------------------------------------------------------------------------------------------ notebooks
NOTEBOOKS = ['00_preparar_entorno.ipynb', '01_mcp_datos_sqlite_y_bigquery.ipynb', '02_mcp_modelo_prediccion.ipynb']


def leer(nombre):
    return nbformat.read(AQUI / nombre, 4)


def salidas(nb):
    return [o for c in nb.cells if c.cell_type == 'code' for o in c.get('outputs', [])]


@pytest.mark.parametrize('nombre', NOTEBOOKS)
def test_los_notebooks_estan_ejecutados_sin_errores(nombre):
    nb = leer(nombre)
    assert not [o for o in salidas(nb) if o['output_type'] == 'error']
    sin_salida = [i for i, c in enumerate(nb.cells) if c.cell_type == 'code' and not c.outputs and 'print' not in c.source and 'writefile' not in c.source
                  and 'import' not in c.source and 'class ' not in c.source and 'CASOS' not in c.source and '= ' not in c.source.splitlines()[0]]
    assert sin_salida == [], f'celdas de código sin ejecutar en {nombre}: {sin_salida}'


@pytest.mark.parametrize('servidor_py,nombre', [('mcp_datos.py', NOTEBOOKS[1]), ('mcp_modelo.py', NOTEBOOKS[2])])
def test_el_servidor_del_notebook_es_idéntico_al_archivo_fuente(servidor_py, nombre):
    celda = next(c for c in leer(nombre).cells if c.source.startswith(f'%%writefile _trabajo/{servidor_py}'))
    assert celda.source.split('\n', 1)[1].rstrip('\n') == (FUENTES / servidor_py).read_text(encoding='utf-8').rstrip('\n')


def texto_de_salidas(nb):
    return '\n'.join(o.get('text') or o.get('data', {}).get('text/plain', '') for o in salidas(nb) if o['output_type'] in ('stream', 'execute_result'))


def test_el_notebook_01_rechaza_los_ocho_ataques_y_recorta_a_50_filas():
    t = texto_de_salidas(leer(NOTEBOOKS[1]))
    assert t.count('RECHAZADA') == 8 and 'SE EJECUTÓ' not in t
    assert 'devuelve 50 filas (truncado: True)' in t


def test_el_notebook_01_dice_la_verdad_sobre_bigquery():
    nb = leer(NOTEBOOKS[1])
    texto = texto_de_salidas(nb)
    assert 'BigQuery SALTADO' in texto or 'IGUAL' in texto                    # o se saltó, o se comparó; nunca silencio
    if 'BigQuery SALTADO' in texto:
        assert 'IGUAL' not in texto and 'DISTINTO' not in texto


def test_el_notebook_02_tiene_paridad_exacta_y_rollback_sin_reiniciar():
    t = texto_de_salidas(leer(NOTEBOOKS[2]))
    assert 'Paridad exacta: la diferencia máxima es 0.0' in t
    assert 'SIN reiniciar el MCP' in t and 'rollback (volver)' in t
    assert 'volver a comprar' in ''.join(c.source for c in leer(NOTEBOOKS[2]).cells if c.cell_type == 'markdown').lower()


def test_el_notebook_02_no_afirma_que_la_recencia_baje_la_probabilidad():
    md = ' '.join(c.source for c in leer(NOTEBOOKS[2]).cells if c.cell_type == 'markdown')
    assert 'la probabilidad SUBE con la recencia' in md
    assert 'no es una relación causal' in md


def test_los_requisitos_fijan_mcp_a_la_1x():
    assert 'mcp==1.30.0' in (AQUI / 'requisitos-extra-mcp.txt').read_text(encoding='utf-8')


def test_las_fuentes_no_escriben_por_stdout():
    for f in FUENTES.glob('*.py'):
        for n, linea in enumerate(f.read_text(encoding='utf-8').splitlines(), 1):
            if linea.strip().startswith('print(') and 'file=sys.stderr' not in linea:
                pytest.fail(f'{f.name}:{n} escribe por stdout, que es el canal del protocolo MCP: {linea.strip()}')
