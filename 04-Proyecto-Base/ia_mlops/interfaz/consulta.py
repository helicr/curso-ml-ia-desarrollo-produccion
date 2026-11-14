"""Lógica de la interfaz de consulta: de unos ids de cliente a su probabilidad y su recomendación. No sabe nada de HTTP.

POR QUÉ HACE FALTA
    La API del modelo (ia_mlops/api) pide las 13 variables de cada cliente: es el contrato del modelo. Quien hace la campaña no
    conoce esas variables; conoce el id del cliente. Esta capa hace de puente, como un «feature store en línea»:

        id(s) de cliente ──► variables en el corte (mismo SQL de FS) ──► API del modelo (/predecir/lote) ──► regla de negocio
                                                                                                          (config.SEGMENTOS_RECOMPRA)

CÓMO SE CALCULAN LAS VARIABLES
    Con ia_mlops.explotacion.variables_en_corte: ejecuta sql/fs/02_poblar_fs.sql para la fecha de corte pedida sobre una tabla
    TEMPORAL. Son exactamente las variables con las que se entrenó (la prueba lo compara con la capa FS) y solo usan datos
    anteriores al corte. La capa FS del proyecto no se toca.

    Se puntúa a TODOS los clientes del corte (no solo a los pedidos) para poder decir el puesto y el decil de cada uno; el
    resultado se guarda en memoria por (corte, huella del modelo): la segunda consulta del mismo corte es inmediata.

LA RECOMENDACIÓN
    El modelo da una probabilidad. Convertirla en una acción es una decisión de negocio: tramos y textos en config.SEGMENTOS_RECOMPRA.
    Si el modelo avisa de valores que no vio al entrenar, el cliente se marca «revisar»: la probabilidad no tiene respaldo ahí.
"""
import re
import threading
from datetime import date

import pandas as pd

from .. import config, db, explotacion as ex
from ..api.servicio import Servicio

MAXIMO_IDS = 1000
_FECHA = re.compile(r'^\d{4}-\d{2}-\d{2}$')


class PeticionNoValida(ValueError):
    """La petición no tiene sentido (fecha mal escrita o fuera del dato, demasiados ids...): 422."""


def segmento_de(probabilidad, segmentos=None):
    """El primer tramo de config.SEGMENTOS_RECOMPRA cuyo «desde» no supera la probabilidad."""
    for s in (segmentos or config.SEGMENTOS_RECOMPRA):
        if probabilidad >= s['desde']:
            return s
    return (segmentos or config.SEGMENTOS_RECOMPRA)[-1]


def leer_ids(valores):
    """Normaliza la lista de ids: enteros positivos, sin repetir, en el orden recibido."""
    vistos, ids = set(), []
    for v in valores:
        try:
            n = int(str(v).strip())
        except ValueError:
            raise PeticionNoValida(f'«{v}» no es un id de cliente (debe ser un número entero).') from None
        if n <= 0:
            raise PeticionNoValida(f'{n} no es un id de cliente válido.')
        if n not in vistos:
            vistos.add(n)
            ids.append(n)
    if not ids:
        raise PeticionNoValida('No hay ningún id de cliente.')
    if len(ids) > MAXIMO_IDS:
        raise PeticionNoValida(f'Como mucho {MAXIMO_IDS} clientes por consulta (llegaron {len(ids)}). Para todos, usa  python -m ia_mlops.explotacion')
    return ids


class Consulta:
    """ruta_db: base analítica (MASTER y FS) · url_api: la API del modelo; sin ella, el modelo de `carpeta_modelo` (o models/)."""

    def __init__(self, ruta_db=None, url_api=None, carpeta_modelo=None):
        self.ruta_db = ruta_db
        self.url_api = (url_api or '').rstrip('/') or None
        self.carpeta_modelo = carpeta_modelo
        self._servicio = None
        self._cache = {}
        self._cerrojo = threading.Lock()

    # --- el modelo: por la API o en local -------------------------------------------------------------------------------------
    @property
    def origen(self):
        return self.url_api or 'modelo local (models/)'

    def _servicio_local(self):
        if self._servicio is None:
            self._servicio = Servicio.cargar(self.carpeta_modelo)
        return self._servicio

    def info_modelo(self):
        if self.url_api:
            i = ex._pedir(f'{self.url_api}/modelo', timeout=10)
        else:
            i = self._servicio_local().meta
        return {'modelo': i['modelo'], 'huella_datos': i['huella_datos'], 'entrenado_en': i['entrenado_en']}

    def _puntuar(self, filas):
        if self.url_api:
            probs, avisos, _ = ex.puntuar_api(filas, self.url_api)
            return probs, avisos
        resultado = self._servicio_local().predecir(filas)
        return [p for p, _ in resultado], [a for _, a in resultado]

    # --- el dato ---------------------------------------------------------------------------------------------------------------
    def limites_de_corte(self, con):
        """(primer corte con historia, corte por defecto = el «hoy» del dato)."""
        primero = db.escalar(con, "SELECT date(MIN(fecha_factura), '+1 day') FROM master_facturas")
        return primero, ex.corte_por_defecto(con)

    def validar_corte(self, con, corte):
        primero, ultimo = self.limites_de_corte(con)
        if not corte:
            return ultimo
        if not _FECHA.match(str(corte)):
            raise PeticionNoValida(f'La fecha de corte «{corte}» debe tener la forma AAAA-MM-DD.')
        try:
            date.fromisoformat(corte)
        except ValueError:
            raise PeticionNoValida(f'«{corte}» no es una fecha que exista.') from None
        if not primero <= corte <= ultimo:
            raise PeticionNoValida(f'El corte debe estar entre {primero} y {ultimo} (el dato no tiene facturas fuera de ese tramo).')
        return corte

    def puntuacion_del_corte(self, con, corte):
        """Todos los clientes del corte con sus variables, probabilidad, advertencias, puesto y decil (en memoria por corte y modelo)."""
        huella = self.info_modelo()['huella_datos']
        clave = (str(self.ruta_db), corte, huella)
        with self._cerrojo:
            if clave in self._cache:
                return self._cache[clave]
        df = ex.variables_en_corte(con, corte)
        if df.empty:
            raise PeticionNoValida(f'Ningún cliente tiene compras antes de {corte}.')
        probs, avisos = self._puntuar(ex._filas(df))
        df = df.assign(probabilidad=probs, advertencias=avisos)
        df = df.sort_values(['probabilidad', 'cliente_id'], ascending=[False, True]).reset_index(drop=True)
        df['puesto'] = range(1, len(df) + 1)
        df['decil'] = (df.index * 10 // len(df) + 1).astype(int)
        df['cliente_id'] = df['cliente_id'].astype(int)
        with self._cerrojo:
            self._cache = {k: v for k, v in self._cache.items() if k[0] == clave[0] and k[2] == huella}   # si cambia el modelo, fuera lo viejo
            self._cache[clave] = df
        return df

    # --- lo que se pide --------------------------------------------------------------------------------------------------------
    def comprobar(self):
        """¿Puede atender? Llega a los datos (MASTER y FS) y al modelo (la API responde /listo, o el modelo local carga).

        Devuelve lo comprobado; lanza RuntimeError (sin datos), urllib.error.URLError (sin API) o ModeloNoDisponible (sin modelo local).
        """
        con = db.conectar(self.ruta_db)
        try:
            ex.corte_por_defecto(con)
            if not db.escalar(con, "SELECT COUNT(*) FROM sqlite_master WHERE name = 'fs_cliente_corte'"):
                raise RuntimeError('No existe la capa FS: ejecuta antes  python -m ia_mlops.pipeline')
        finally:
            con.close()
        if self.url_api:
            ex._pedir(f'{self.url_api}/listo', timeout=5)
        else:
            self._servicio_local()
        return {'datos': 'ok', 'modelo': self.origen}

    def estado(self):
        con = db.conectar(self.ruta_db)
        try:
            primero, ultimo = self.limites_de_corte(con)
            todos = self.puntuacion_del_corte(con, ultimo)
            # ejemplos repartidos por el ranking (el primero, el último y tres intermedios): se ven todos los tramos
            n = len(todos)
            ejemplos = list(dict.fromkeys(int(todos['cliente_id'].iloc[min(n - 1, round(q * (n - 1)))]) for q in (0, 0.25, 0.5, 0.75, 1)))
        finally:
            con.close()
        return {'corte_por_defecto': ultimo, 'primer_corte': primero, 'origen': self.origen, **self.info_modelo(),
                'segmentos': config.SEGMENTOS_RECOMPRA, 'maximo_ids': MAXIMO_IDS, 'ejemplos': ejemplos}

    def recomendar(self, ids, corte=None):
        ids = leer_ids(ids)
        con = db.conectar(self.ruta_db)
        try:
            corte = self.validar_corte(con, corte)
            todos = self.puntuacion_del_corte(con, corte)
            encontrados = todos[todos['cliente_id'].isin(ids)]
            faltan = [i for i in ids if i not in set(encontrados['cliente_id'])]
            en_master = {r[0] for r in con.execute(
                f'SELECT cliente_id FROM master_clientes WHERE cliente_id IN ({",".join("?" * len(faltan))})', faltan)} if faltan else set()
        finally:
            con.close()

        resultados = []
        for r in encontrados.to_dict(orient='records'):     # ya vienen de mayor a menor probabilidad
            s = segmento_de(r['probabilidad'])
            variables = {k: (None if pd.isna(r[k]) else (float(r[k]) if isinstance(r[k], float) else int(r[k]))) for k in config.FEATURES}
            resultados.append({
                'cliente_id': r['cliente_id'], 'probabilidad': round(float(r['probabilidad']), 4),
                'segmento': s['segmento'], 'recomendacion': s['recomendacion'], 'revisar': bool(r['advertencias']),
                'puesto': int(r['puesto']), 'decil': int(r['decil']), 'advertencias': list(r['advertencias']), 'variables': variables,
            })
        no_encontrados = [{'cliente_id': i, 'motivo': 'sin compras válidas antes del corte: no hay variables con las que predecir'
                           if i in en_master else 'no existe en MASTER'} for i in faltan]
        por_segmento = {s['segmento']: sum(1 for x in resultados if x['segmento'] == s['segmento']) for s in config.SEGMENTOS_RECOMPRA}
        return {'corte': corte, 'origen': self.origen, **self.info_modelo(), 'clientes_en_el_corte': int(len(todos)),
                'pedidos': len(ids), 'encontrados': len(resultados), 'por_segmento': por_segmento,
                'resultados': resultados, 'no_encontrados': no_encontrados}
