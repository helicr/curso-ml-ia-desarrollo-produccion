"""Los otros dos modos de inferencia de la interfaz: BAJO DEMANDA y ONLINE (el tercero, el lote, es ia_mlops/explotacion.py).

    modo            ¿de dónde salen las 13 variables?                                          ¿qué corte usa?
    lote            calculadas para TODOS los clientes (explotacion.py) y guardadas             el del día
    bajo demanda    LEÍDAS de la tabla fs_produccion (ya calculadas por el lote): sin cálculo   el último corte escrito en fs_produccion
    online          CALCULADAS AL VUELO para ese cliente con el mismo SQL de FS (02_poblar_fs)  «ahora»

«AHORA» EN EL DATO DEL CURSO
    El dato termina en 2011: no se puede usar el reloj del ordenador. «Ahora» es el DÍA SIGUIENTE AL ÚLTIMO EVENTO CONOCIDO, contando
    MASTER y, en modo demo, también las compras de demo_compras. Sin compras de demo coincide con el corte del lote
    (explotacion.corte_por_defecto). Las compras de demo se fechan en el ÚLTIMO DÍA CON DATOS de MASTER (a las 23:59:59), así
    «ahora» no se mueve al simular una compra: el cliente pasa a recencia 0 y frecuencia +1 y el resto de clientes no cambia.

SIN FUGA
    El SQL de FS solo mira facturas con fecha_factura < corte. En online, MASTER y demo_compras se exponen al SQL como vistas TEMPORALES
    (con el mismo nombre que las tablas de MASTER) filtradas al cliente pedido: el SQL de FS se ejecuta sin cambiar una coma y solo
    calcula ese cliente (por eso es rápido). Una compra posterior al corte pedido no entra.

MODO DEMO (CURSO_DEMO=1; apagado por defecto)
    Trabaja sobre una COPIA de la base (nunca sobre la del proyecto ni sobre un volumen :ro). La copia tiene la tabla demo_compras.
    POST /demo/compra inserta una compra; POST /demo/reiniciar la vacía. Solo online la ve; bajo demanda y lote no, hasta que se
    recalcula fs_produccion.
"""
import atexit
import re
import shutil
import tempfile
import time
from datetime import date
from pathlib import Path

import pandas as pd

from .. import config, db, explotacion as ex
from .consulta import Consulta, PeticionNoValida, leer_ids, segmento_de

FECHA_HORA_DEMO = '23:59:59'
PRODUCTO_DEMO = 'DEMO'


class NoEncontrado(Exception):
    """El cliente no está donde se busca, o el modo demo está apagado: 404 con el motivo."""


def preparar_copia_demo(ruta_origen=None, carpeta=None):
    """Copia la base a una carpeta propia y le crea demo_compras. Devuelve la ruta de la COPIA (la original no se toca)."""
    origen = Path(ruta_origen or config.DB)
    if not origen.is_file():
        raise RuntimeError(f'No existe la base {origen}: no se puede preparar el modo demo. Ejecuta antes  python -m ia_mlops.pipeline')
    if carpeta is None:
        carpeta = Path(tempfile.mkdtemp(prefix='curso_demo_'))
        atexit.register(shutil.rmtree, carpeta, ignore_errors=True)
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    copia = carpeta / 'curso_demo.db'
    if copia.resolve() == origen.resolve():
        raise RuntimeError('La copia de demo no puede ser la base original.')
    shutil.copyfile(origen, copia)
    con = db.conectar(copia, solo_lectura=False)
    try:
        con.execute('''CREATE TABLE IF NOT EXISTS demo_compras (
            compra_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            fecha      TEXT    NOT NULL,      -- AAAA-MM-DD HH:MM:SS, como master_facturas.fecha_factura
            importe    REAL    NOT NULL CHECK (importe > 0),
            unidades   INTEGER NOT NULL CHECK (unidades > 0),
            producto   TEXT    NOT NULL,
            pais       TEXT    NOT NULL)''')
        con.commit()
    finally:
        con.close()
    return copia


class Modos:
    def __init__(self, consulta: Consulta, demo=False):
        self.c = consulta
        self.demo = bool(demo)

    # --- utilidades --------------------------------------------------------------------------------------------------------------
    def _con(self):
        return db.conectar(self.c.ruta_db)

    @staticmethod
    def _existe(con, tabla):
        return bool(db.escalar(con, "SELECT COUNT(*) FROM sqlite_master WHERE name = ? AND type = 'table'", [tabla]))

    def _resultado(self, modo, cliente_id, fila, probabilidad, avisos, corte, extra=None):
        s = segmento_de(probabilidad)
        variables = ex._filas(pd.DataFrame([fila]))[0]     # mismos tipos que los de la API: enteros como int, NaN como None
        r = {'modo': modo, 'cliente_id': int(cliente_id), 'corte': corte, 'probabilidad': float(probabilidad), 'segmento': s['segmento'],
             'recomendacion': s['recomendacion'], 'revisar': bool(avisos), 'advertencias': list(avisos), 'variables': variables}
        r.update(extra or {})
        return r

    def _cabecera(self):
        return {'origen': self.c.origen, **self.c.info_modelo()}

    def estado(self):
        con = self._con()
        try:
            corte_fs = None
            if self._existe(con, 'fs_produccion'):
                corte_fs = db.escalar(con, 'SELECT MAX(fecha_corte) FROM fs_produccion')
            return {'demo': self.demo, 'ahora': self.ahora(con), 'corte_lote_por_defecto': ex.corte_por_defecto(con),
                    'fs_produccion_ultimo_corte': corte_fs,
                    'compras_demo': db.escalar(con, 'SELECT COUNT(*) FROM demo_compras') if self.demo else None}
        finally:
            con.close()

    # --- modo 2: bajo demanda -----------------------------------------------------------------------------------------------------
    def bajo_demanda(self, ids):
        """Lee las variables del último corte de fs_produccion para los ids y los puntúa. Devuelve (resultados, no_encontrados, corte, ms)."""
        t0 = time.perf_counter()
        ids = leer_ids(ids)
        con = self._con()
        try:
            if not self._existe(con, 'fs_produccion'):
                raise RuntimeError('No existe la tabla fs_produccion: la escribe el lote diario (python -m ia_mlops.explotacion). '
                                   'Sin ella no hay variables que leer en modo bajo demanda.')
            corte = db.escalar(con, 'SELECT MAX(fecha_corte) FROM fs_produccion')
            if corte is None:
                raise RuntimeError('La tabla fs_produccion está vacía: ejecuta antes el lote diario (python -m ia_mlops.explotacion).')
            columnas = ', '.join(['cliente_id', *config.FEATURES, 'huella_modelo', 'version_modelo'])
            df = pd.read_sql(f'SELECT {columnas} FROM fs_produccion WHERE fecha_corte = ? AND cliente_id IN ({",".join("?" * len(ids))})',
                             con, params=[corte, *ids])
        finally:
            con.close()
        por_id = {int(r['cliente_id']): r for r in df.to_dict(orient='records')}
        encontrados = [i for i in ids if i in por_id]
        faltan = [{'cliente_id': i, 'motivo': f'no está en fs_produccion en el corte {corte} (sin compras válidas antes del corte, o no existe)'}
                  for i in ids if i not in por_id]
        resultados = []
        if encontrados:
            filas = ex._filas(pd.DataFrame([por_id[i] for i in encontrados]))
            probs, avisos = self.c._puntuar(filas)
            for i, p, a in zip(encontrados, probs, avisos):
                f = por_id[i]
                resultados.append(self._resultado('bajo_demanda', i, f, p, a, corte, {
                    'version_modelo_del_lote': None if pd.isna(f['version_modelo']) else int(f['version_modelo']),
                    'huella_modelo_del_lote': f['huella_modelo']}))
        ms = round((time.perf_counter() - t0) * 1000, 2)
        return resultados, faltan, corte, ms

    def bajo_demanda_uno(self, cliente_id):
        resultados, faltan, corte, ms = self.bajo_demanda([cliente_id])
        if not resultados:
            raise NoEncontrado(faltan[0]['motivo'])
        return {**resultados[0], **self._cabecera(), 'ms': ms}

    def bajo_demanda_lote(self, ids):
        resultados, faltan, corte, ms = self.bajo_demanda(ids)
        return {'modo': 'bajo_demanda', 'corte': corte, **self._cabecera(), 'pedidos': len(resultados) + len(faltan),
                'encontrados': len(resultados), 'resultados': resultados, 'no_encontrados': faltan, 'ms': ms}

    # --- modo 3: online -----------------------------------------------------------------------------------------------------------
    def ahora(self, con):
        """El día siguiente al último evento conocido (MASTER y, en demo, demo_compras)."""
        if self.demo:
            ultimo = db.escalar(con, 'SELECT MAX(f) FROM (SELECT MAX(fecha_factura) AS f FROM master_facturas '
                                     'UNION ALL SELECT MAX(fecha) FROM demo_compras)')
            ahora = db.escalar(con, "SELECT date(?, '+1 day')", [ultimo])
            if ahora is None:
                raise RuntimeError('MASTER está vacío: ejecuta antes  python -m ia_mlops.pipeline')
            return ahora
        return ex.corte_por_defecto(con)

    @staticmethod
    def _validar_fecha(corte):
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', str(corte)):
            raise PeticionNoValida(f'La fecha de corte «{corte}» debe tener la forma AAAA-MM-DD.')
        try:
            date.fromisoformat(corte)
        except ValueError:
            raise PeticionNoValida(f'«{corte}» no es una fecha que exista.') from None

    def _variables_al_vuelo(self, con, cliente_id, corte):
        """Ejecuta 02_poblar_fs.sql para UN cliente en `corte`, con MASTER (+ demo_compras) como vistas temporales."""
        cid = int(cliente_id)             # entero comprobado: se escribe en la vista (una vista no admite parámetros)
        demo = self.demo
        facturas = ('SELECT factura_id, cliente_id, fecha_factura, pais, es_cancelacion FROM main.master_facturas '
                    f'WHERE cliente_id = {cid}')
        lineas = ('SELECT factura_id, codigo_producto, cantidad, monto_linea, es_venta_valida FROM main.master_lineas '
                  f'WHERE factura_id IN (SELECT factura_id FROM main.master_facturas WHERE cliente_id = {cid})')
        if demo:
            facturas += (f" UNION ALL SELECT 'DEMO-' || compra_id, cliente_id, fecha, pais, 0 FROM main.demo_compras WHERE cliente_id = {cid}")
            lineas += (f" UNION ALL SELECT 'DEMO-' || compra_id, producto, unidades, importe, 1 FROM main.demo_compras WHERE cliente_id = {cid}")
        con.execute('DROP VIEW IF EXISTS temp.master_facturas')
        con.execute('DROP VIEW IF EXISTS temp.master_lineas')
        con.execute('DROP TABLE IF EXISTS temp.fs_cliente_corte')
        try:
            con.execute('CREATE TEMP TABLE fs_cliente_corte AS SELECT * FROM main.fs_cliente_corte WHERE 0')
            con.execute(f'CREATE TEMP VIEW master_facturas AS {facturas}')
            con.execute(f'CREATE TEMP VIEW master_lineas AS {lineas}')
            db.ejecutar_sentencia(con, config.SQL / 'fs' / '02_poblar_fs.sql', {'corte': corte})
            return pd.read_sql('SELECT * FROM temp.fs_cliente_corte', con)
        finally:
            con.execute('DROP VIEW IF EXISTS temp.master_facturas')
            con.execute('DROP VIEW IF EXISTS temp.master_lineas')
            con.execute('DROP TABLE IF EXISTS temp.fs_cliente_corte')

    def online(self, cliente_id, corte=None):
        t0 = time.perf_counter()
        ids = leer_ids([cliente_id])
        con = self._con()
        try:
            if not self._existe(con, 'fs_cliente_corte'):
                raise RuntimeError('No existe la capa FS: ejecuta antes  python -m ia_mlops.pipeline')
            ahora = self.ahora(con)
            if corte:
                primero, _ = self.c.limites_de_corte(con)
                self._validar_fecha(corte)
                if not primero <= corte <= ahora:
                    raise PeticionNoValida(f'El corte debe estar entre {primero} y {ahora} («ahora»).')
            else:
                corte = ahora
            df = self._variables_al_vuelo(con, ids[0], corte)
        finally:
            con.close()
        if df.empty:
            raise NoEncontrado(f'El cliente {ids[0]} no tiene compras válidas antes de {corte}: no hay variables con las que predecir.')
        probs, avisos = self.c._puntuar(ex._filas(df))
        fila = df.iloc[0]
        ms = round((time.perf_counter() - t0) * 1000, 2)
        return {**self._resultado('online', ids[0], fila, probs[0], avisos[0], corte, {'ahora': ahora}), **self._cabecera(), 'ms': ms}

    # --- modo demo ----------------------------------------------------------------------------------------------------------------
    def _exigir_demo(self):
        if not self.demo:
            raise NoEncontrado('El modo demo está apagado (arranca la interfaz con CURSO_DEMO=1): no hay compras simuladas.')

    def compra(self, cliente_id, importe, unidades=1, producto=None):
        self._exigir_demo()
        cid = leer_ids([cliente_id])[0]
        if not importe or importe <= 0 or unidades <= 0:
            raise PeticionNoValida('El importe y las unidades de la compra deben ser positivos.')
        con = db.conectar(self.c.ruta_db, solo_lectura=False)     # la COPIA de demo: la única base en la que esta interfaz escribe
        try:
            fila = con.execute('SELECT pais FROM master_clientes WHERE cliente_id = ?', [cid]).fetchone()
            if fila is None:
                raise NoEncontrado(f'El cliente {cid} no existe en MASTER.')
            ultimo_dia = db.escalar(con, 'SELECT date(MAX(fecha_factura)) FROM master_facturas')
            fecha = f'{ultimo_dia} {FECHA_HORA_DEMO}'
            cur = con.execute('INSERT INTO demo_compras (cliente_id, fecha, importe, unidades, producto, pais) VALUES (?, ?, ?, ?, ?, ?)',
                              [cid, fecha, float(importe), int(unidades), (producto or PRODUCTO_DEMO).strip().upper(), fila[0]])
            con.commit()
            total = db.escalar(con, 'SELECT COUNT(*) FROM demo_compras WHERE cliente_id = ?', [cid])
            return {'compra_id': cur.lastrowid, 'cliente_id': cid, 'fecha': fecha, 'importe': float(importe), 'unidades': int(unidades),
                    'compras_demo_del_cliente': total,
                    'aviso': 'Solo el modo online la ve; bajo demanda y lote no cambian hasta recalcular fs_produccion.'}
        finally:
            con.close()

    def reiniciar(self):
        self._exigir_demo()
        con = db.conectar(self.c.ruta_db, solo_lectura=False)
        try:
            n = con.execute('DELETE FROM demo_compras').rowcount
            con.commit()
        finally:
            con.close()
        return {'compras_borradas': n}
