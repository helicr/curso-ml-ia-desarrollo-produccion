"""Fuentes de datos de la migracion: de donde se lee el ORIGEN y el DESTINO que `validar` compara.

`validar(origen, destino)` no sabe si habla con SQLite, con una carpeta de Parquet o con BigQuery: solo usa los
metodos de esta interfaz (`validar.py` no cambia). Hay tres fuentes; las dos primeras son LOCALES:

    FuenteSQLite(ruta_db)      el origen (y, si se quiere, tambien puede ser destino: una SQLite contra otra)
    FuenteParquet(carpeta)     el destino local: una carpeta con un archivo <tabla>.parquet por tabla
    FuenteBigQuery(proyecto, dataset)   el destino en la nube (necesita google-cloud-bigquery; sin verificar contra BigQuery real)

Interfaz que debe cumplir una fuente:
    nombre                                      texto corto para los informes (sin rutas personales)
    tablas() -> list[str]                       todas las tablas que ve
    esquema(tabla) -> list[Columna]             columnas EN ORDEN con su tipo logico (ver tipos.py)
    clave(tabla) -> list[str]                   columnas de la clave primaria (vacia si no la conoce)
    filas(tabla) -> int
    agregados(tabla, columnas) -> dict          por columna: nulos, distintos, minimo, maximo y (si es numerica) suma
    muestra(tabla, columnas, clave, n) -> list[tuple]   las n primeras y las n ultimas filas ordenadas por clave (n=None: todas)
    integridad() -> list[(archivo, ok, detalle)]        comprobaciones propias de la fuente (p. ej. huellas); puede ser []
"""
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .. import db
from . import tipos

PREFIJOS_POR_DEFECTO = ('master_', 'fs_', 'ml_')

# Tablas que EMPIEZAN por un prefijo de capa pero NO son la capa analítica a migrar: son ESTADO DE PRODUCCIÓN (lo que va
# dejando la explotación al puntuar, o la demo), no resultado del pipeline. Se excluyen de la selección por prefijos;
# si alguien las pide por nombre (--tablas), se migran igual.
TABLAS_EXCLUIDAS = frozenset({'fs_produccion', 'demo_compras'})


class MigracionError(Exception):
    """Un problema que se explica al usuario (no un fallo del programa): tabla inexistente, tipo imposible, carpeta vacia..."""


@dataclass(frozen=True)
class Columna:
    nombre: str
    tipo: str          # tipo logico (tipos.TIPOS_LOGICOS) o «otro:<tipo>» si la fuente trae algo que no encaja


def seleccionar(tablas_disponibles, prefijos=PREFIJOS_POR_DEFECTO, tablas=None):
    """Tablas a migrar: las indicadas explicitamente o las que empiezan por alguno de los prefijos. Ordenadas por nombre."""
    if tablas:
        faltan = [t for t in tablas if t not in tablas_disponibles]
        if faltan:
            raise MigracionError(f'No existen en el origen las tablas: {", ".join(faltan)}')
        return sorted(tablas)
    return sorted(t for t in tablas_disponibles if t.startswith(tuple(prefijos)) and t not in TABLAS_EXCLUIDAS)


def _q(identificador):
    return '"' + identificador.replace('"', '""') + '"'


class FuenteSQLite:
    """Una base SQLite abierta en SOLO LECTURA (no se puede modificar el origen por error)."""

    def __init__(self, ruta):
        self.ruta = Path(ruta)
        self.nombre = self.ruta.name
        if not self.ruta.is_file():
            raise MigracionError(f'No existe la base SQLite {self.ruta.name}')
        self.con = db.conectar(self.ruta, solo_lectura=True)

    def cerrar(self):
        self.con.close()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.cerrar()

    # ---- catalogo
    def tablas(self):
        filas = self.con.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite\\_%' ESCAPE '\\' ORDER BY name")
        return [f[0] for f in filas]

    def vistas(self):
        return [f[0] for f in self.con.execute("SELECT name FROM sqlite_master WHERE type = 'view' ORDER BY name")]

    def indices(self, tabla):
        return [f[0] for f in self.con.execute(f'PRAGMA index_list({_q(tabla)})') if not f[1].startswith('sqlite_autoindex')]

    def columnas_declaradas(self, tabla):
        """[(nombre, tipo_declarado, es_clave, posicion_en_la_clave)] tal como lo declara SQLite."""
        info = self.con.execute(f'PRAGMA table_info({_q(tabla)})').fetchall()
        if not info:
            raise MigracionError(f'No existe la tabla {tabla} en {self.nombre}')
        return [(f[1], f[2], f[5], f[5]) for f in info]

    def _inferir(self, tabla, columna):
        """Tipo logico de una columna sin tipo declarado util (NUMERIC, DECIMAL, vacio): se mira que guardan sus valores."""
        vistos = {f[0] for f in self.con.execute(
            f'SELECT DISTINCT typeof({_q(columna)}) FROM {_q(tabla)} WHERE {_q(columna)} IS NOT NULL')}
        if not vistos:
            return tipos.TEXTO            # todo nulo: da igual; se exporta como texto
        if vistos == {'integer'}:
            return tipos.ENTERO
        if vistos <= {'integer', 'real'}:
            return tipos.REAL
        if vistos == {'text'}:
            return tipos.TEXTO
        if vistos == {'blob'}:
            return tipos.BINARIO
        raise MigracionError(f'{tabla}.{columna}: mezcla de tipos {sorted(vistos)} y sin tipo declarado; no hay un tipo unico al que migrarla')

    def esquema(self, tabla):
        columnas = []
        for nombre, declarado, _, _ in self.columnas_declaradas(tabla):
            logico = tipos.tipo_declarado_a_logico(declarado)
            if logico == tipos.A_INFERIR:
                logico = self._inferir(tabla, nombre)
            columnas.append(Columna(nombre, logico))
        return columnas

    def clave(self, tabla):
        pk = [(f[3], f[0]) for f in self.columnas_declaradas(tabla) if f[2]]
        return [nombre for _, nombre in sorted(pk)]

    # ---- contenido
    def filas(self, tabla):
        return self.con.execute(f'SELECT COUNT(*) FROM {_q(tabla)}').fetchone()[0]

    def agregados(self, tabla, columnas):
        if not columnas:
            return {}

        def consulta(suma):
            partes = []
            for c in columnas:
                q = _q(c.nombre)
                partes += [f'COUNT(*) - COUNT({q})', f'COUNT(DISTINCT {q})', f'MIN({q})', f'MAX({q})']
                if c.tipo in tipos.NUMERICOS:
                    partes.append(f'{suma}({q})')
            return f'SELECT {", ".join(partes)} FROM {_q(tabla)}'
        try:
            fila = self.con.execute(consulta('SUM')).fetchone()
        except sqlite3.OperationalError:          # SUM de enteros desbordado: TOTAL devuelve un real
            fila = self.con.execute(consulta('TOTAL')).fetchone()
        salida, i = {}, 0
        for c in columnas:
            d = {'nulos': fila[i], 'distintos': fila[i + 1], 'minimo': fila[i + 2], 'maximo': fila[i + 3]}
            i += 4
            if c.tipo in tipos.NUMERICOS:
                d['suma'] = fila[i]
                i += 1
            salida[c.nombre] = d
        return salida

    def muestra(self, tabla, columnas, clave, n):
        orden = ', '.join(_q(c) for c in (clave or columnas))
        cols = ', '.join(_q(c) for c in columnas)
        base = f'SELECT {cols} FROM {_q(tabla)} ORDER BY {orden}'
        total = self.filas(tabla)
        if n is None or total <= 2 * n:
            return [tuple(f) for f in self.con.execute(base)]
        primeras = [tuple(f) for f in self.con.execute(f'{base} LIMIT {int(n)}')]
        ultimas = [tuple(f) for f in self.con.execute(f'{base} LIMIT {int(n)} OFFSET {total - int(n)}')]
        return primeras + ultimas

    def integridad(self):
        return []


class FuenteParquet:
    """Una carpeta con un <tabla>.parquet por tabla (lo que produce `exportar`). Es el destino local de la migracion."""

    def __init__(self, carpeta):
        self.carpeta = Path(carpeta)
        self.nombre = self.carpeta.name
        if not self.carpeta.is_dir():
            raise MigracionError(f'No existe la carpeta de destino {self.carpeta.name}')
        self._cache = {}

    def _ruta(self, tabla):
        return self.carpeta / f'{tabla}.parquet'

    def _leer(self, tabla):
        import pyarrow.parquet as pq
        if tabla not in self._cache:
            self._cache = {tabla: pq.read_table(self._ruta(tabla))}      # solo guarda la ultima: no se acumulan tablas grandes
        return self._cache[tabla]

    def tablas(self):
        return sorted(p.stem for p in self.carpeta.glob('*.parquet'))

    def esquema(self, tabla):
        import pyarrow.parquet as pq
        esq = pq.read_schema(self._ruta(tabla))
        return [Columna(f.name, tipos.tipo_arrow_a_logico(f.type)) for f in esq]

    def clave(self, tabla):
        return []

    def filas(self, tabla):
        import pyarrow.parquet as pq
        return pq.ParquetFile(self._ruta(tabla)).metadata.num_rows

    def agregados(self, tabla, columnas):
        import pyarrow.compute as pc
        t = self._leer(tabla)
        salida = {}
        for c in columnas:
            col = t.column(c.nombre)
            mm = pc.min_max(col)
            d = {'nulos': col.null_count, 'distintos': pc.count_distinct(col, mode='only_valid').as_py(),
                 'minimo': mm['min'].as_py(), 'maximo': mm['max'].as_py()}
            if c.tipo in tipos.NUMERICOS:
                d['suma'] = pc.sum(col).as_py()
            salida[c.nombre] = d
        return salida

    def muestra(self, tabla, columnas, clave, n):
        import pyarrow.compute as pc
        t = self._leer(tabla)
        orden = clave or columnas
        # nulos al principio, como SQLite en orden ascendente (null_placement por clave: forma vigente desde pyarrow 25)
        indices = pc.sort_indices(t, sort_keys=[(c, 'ascending', 'at_start') for c in orden])
        t = t.take(indices).select(list(columnas))
        total = t.num_rows
        if n is not None and total > 2 * n:
            t = _concatenar(t.slice(0, n), t.slice(total - n, n))
        return list(zip(*[t.column(c).to_pylist() for c in columnas])) if t.num_rows else []

    def integridad(self):
        from . import huella
        if not (self.carpeta / huella.NOMBRE).is_file():
            return []
        return huella.verificar(self.carpeta)


def _concatenar(a, b):
    import pyarrow as pa
    return pa.concat_tables([a, b])


MAX_BYTES_POR_DEFECTO = 1_000_000_000      # tope de bytes facturados por consulta: decision NUESTRA (no una cifra de Google)
_IDENTIFICADOR = re.compile(r'^[A-Za-z0-9_\-]+$')


class FuenteBigQuery:
    """Un dataset de BigQuery como DESTINO de la migracion (misma interfaz que FuenteSQLite y FuenteParquet).

    Seguridad de coste: cada consulta se lanza ANTES en modo dry run (no cuesta nada) y se rechaza si el volumen estimado supera
    `max_bytes_facturados`; la consulta real lleva ese mismo tope (`maximum_bytes_billed`) y la etiqueta curso=ml-ia.
    La biblioteca `google-cloud-bigquery` se importa SOLO al usarla: sin ella, falla con un mensaje claro (MigracionError).
    `cliente` permite inyectar un doble en las pruebas. SIN VERIFICAR contra BigQuery real (T09).
    """

    def __init__(self, proyecto, dataset, ubicacion=None, max_bytes_facturados=MAX_BYTES_POR_DEFECTO, cliente=None):
        for valor in (proyecto, dataset):
            if not valor or not _IDENTIFICADOR.match(valor):
                raise MigracionError('El proyecto y el dataset de BigQuery solo pueden llevar letras, numeros, guiones y guiones bajos')
        self.proyecto, self.dataset, self.ubicacion = proyecto, dataset, ubicacion
        self.max_bytes = int(max_bytes_facturados)
        self.nombre = f'BigQuery:{dataset}'          # sin el id del proyecto: los informes se guardan y se ensenan
        self.bytes_estimados = 0                     # suma de lo que estimaron los dry run (para el informe)
        self.consultas = 0
        self._bq = None
        self._cliente = cliente
        self._tablas = {}

    # ---- biblioteca y cliente (perezosos)
    def _biblioteca(self):
        if self._bq is None:
            try:
                from google.cloud import bigquery
            except ImportError as e:
                raise MigracionError('Falta la biblioteca google-cloud-bigquery. Instalala en TU entorno con: '
                                     'pip install google-cloud-bigquery  (y autenticate con gcloud auth application-default login)') from e
            self._bq = bigquery
        return self._bq

    def _cli(self):
        if self._cliente is None:
            bq = self._biblioteca()
            self._cliente = bq.Client(project=self.proyecto, location=self.ubicacion)
        return self._cliente

    def cerrar(self):
        if self._cliente is not None and hasattr(self._cliente, 'close'):
            self._cliente.close()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.cerrar()

    # ---- consultas con dry run y tope
    def _ref(self, tabla):
        if not _IDENTIFICADOR.match(tabla):
            raise MigracionError(f'Nombre de tabla no valido: {tabla}')
        return f'`{self.proyecto}.{self.dataset}.{tabla}`'

    def _consulta(self, sql):
        bq = self._biblioteca()
        cli = self._cli()
        previa = cli.query(sql, job_config=bq.QueryJobConfig(dry_run=True, use_query_cache=False), location=self.ubicacion)
        estimados = int(previa.total_bytes_processed or 0)
        if estimados > self.max_bytes:
            raise MigracionError(f'La consulta procesaria unos {estimados} bytes y el tope es {self.max_bytes}: no se ejecuta')
        self.bytes_estimados += estimados
        self.consultas += 1
        real = cli.query(sql, job_config=bq.QueryJobConfig(maximum_bytes_billed=self.max_bytes, labels={'curso': 'ml-ia'}),
                         location=self.ubicacion)
        return [tuple(f.values()) for f in real.result()]

    def _tabla(self, tabla):
        if tabla not in self._tablas:
            self._tablas = {tabla: self._cli().get_table(f'{self.proyecto}.{self.dataset}.{tabla}')}
        return self._tablas[tabla]

    # ---- catalogo
    def tablas(self):
        return sorted(t.table_id for t in self._cli().list_tables(f'{self.proyecto}.{self.dataset}'))

    def esquema(self, tabla):
        return [Columna(c.name, tipos.tipo_bigquery_a_logico(c.field_type)) for c in self._tabla(tabla).schema]

    def clave(self, tabla):
        return []

    # ---- contenido
    def filas(self, tabla):
        return int(self._consulta(f'SELECT COUNT(*) FROM {self._ref(tabla)}')[0][0])

    def agregados(self, tabla, columnas):
        if not columnas:
            return {}

        def consulta(numero):
            partes = []
            for c in columnas:
                q = f'`{c.nombre}`'
                partes += [f'COUNT(*) - COUNT({q})', f'COUNT(DISTINCT {q})', f'MIN({q})', f'MAX({q})']
                if c.tipo in tipos.NUMERICOS:
                    partes.append(f'SUM({numero.format(q)})')
            return f'SELECT {", ".join(partes)} FROM {self._ref(tabla)}'
        try:
            fila = self._consulta(consulta('{}'))[0]
        except MigracionError:
            raise
        except Exception:          # noqa: BLE001 - SUM de enteros desbordado: se repite sumando como reales
            fila = self._consulta(consulta('CAST({} AS FLOAT64)'))[0]
        salida, i = {}, 0
        for c in columnas:
            d = {'nulos': fila[i], 'distintos': fila[i + 1], 'minimo': fila[i + 2], 'maximo': fila[i + 3]}
            i += 4
            if c.tipo in tipos.NUMERICOS:
                d['suma'] = fila[i]
                i += 1
            salida[c.nombre] = d
        return salida

    def muestra(self, tabla, columnas, clave, n):
        cols = ', '.join(f'`{c}`' for c in columnas)
        orden = ', '.join(f'`{c}`' for c in (clave or columnas))
        inverso = ', '.join(f'`{c}` DESC' for c in (clave or columnas))
        base = f'SELECT {cols} FROM {self._ref(tabla)}'
        if n is None or self.filas(tabla) <= 2 * n:
            return self._consulta(f'{base} ORDER BY {orden}')
        primeras = self._consulta(f'{base} ORDER BY {orden} LIMIT {int(n)}')
        ultimas = self._consulta(f'{base} ORDER BY {inverso} LIMIT {int(n)}')
        return primeras + ultimas[::-1]

    def integridad(self):
        return []