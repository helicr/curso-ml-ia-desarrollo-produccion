"""Las herramientas del agente de retención: funciones puras en Python que devuelven diccionarios serializables a JSON.

QUÉ ES UNA HERRAMIENTA
    Una función con un CONTRATO claro: argumentos sencillos (un id, un número) y un diccionario como respuesta. El LLM no ve la base
    de datos ni el modelo: solo pide «dame la lista del día» o «puntúa al cliente 12670» y lee el diccionario que vuelve. El servidor
    MCP (servidor_mcp.py) no añade lógica: solo publica estas funciones con una descripción para el LLM.

    función                      qué responde                                              de dónde sale
    lista_del_dia(n)             los n clientes con más probabilidad de la última campaña  reports/campana/ (lote diario, panel.py)
    puntuar_bajo_demanda(id)     probabilidad con las variables LEÍDAS de fs_produccion    GET /bajo-demanda/{id} (interfaz/modos.py)
    puntuar_online(id, corte)    probabilidad con las variables CALCULADAS ahora           GET /online/{id}      (interfaz/modos.py)
    version_en_produccion()      qué modelo está publicado, desde cuándo y su historial    models/referencia.json (produccion.py)
    por_que(id, n)               qué variables empujan más la probabilidad de ese cliente  el propio modelo (regresión logística)
    referencia_del_modelo()      la ficha completa del modelo (el recurso referencia://modelo)

PARIDAD CON LA API DE S4
    puntuar_bajo_demanda y puntuar_online devuelven EXACTAMENTE lo que devuelven los endpoints de la interfaz (es el mismo código:
    la clase Modos). Una prueba lo comprueba. Por eso no hay aquí ningún cálculo nuevo de probabilidades.

ERRORES: LA HERRAMIENTA NUNCA LANZA
    Un cliente que no existe, una fecha mal escrita o una base que falta devuelven {'error': '...'} con el motivo en claro. Así el
    agente puede leerlo y contestar «no tengo datos de ese cliente» en vez de caerse. Los mensajes no llevan rutas de tu equipo.

DATOS PERSONALES
    El caso (Online Retail II) solo conoce un número de cliente y su país: no hay nombres, correos ni teléfonos, y ninguna herramienta
    los devuelve. Una prueba vigila que ninguna respuesta lleve claves de ese tipo.

DÓNDE LEE
    Por defecto, lo mismo que el resto del proyecto (config.py: CURSO_DB, CURSO_MODELOS, CURSO_REFERENCIA, CURSO_CAMPANA,
    CURSO_URL_API). En las pruebas se puede apuntar a otra base y otro modelo con configurar(...).
"""
import functools
import json
import math
import threading
from pathlib import Path

import pandas as pd

from .. import config, produccion
from ..interfaz import panel
from ..interfaz.consulta import Consulta, PeticionNoValida, leer_ids, segmento_de
from ..interfaz.modos import Modos, NoEncontrado

MAXIMO_LISTA = 100            # tope de clientes por lista: el LLM es pequeño y no necesita más
MAXIMO_VARIABLES = len(config.FEATURES)
_RESUMEN_PUBLICO = ('corte', 'clientes_puntuados', 'clientes_en_campana', 'probabilidad_media', 'probabilidad_media_campana',
                    'modelo', 'huella_datos', 'generado_en')      # del JSON de la campaña: sin rutas ni nada más

_cerrojo = threading.Lock()
_contexto = {'ruta_db': None, 'carpeta_modelo': None, 'url_api': None}
_modos = None


# --------------------------------------------------------------------------------------------------------- configuración
def configurar(ruta_db=None, carpeta_modelo=None, url_api=None):
    """Fija de dónde leen las herramientas (útil en pruebas). Sin argumentos vuelve a los valores de config.py.

    `url_api=''` fuerza el modelo local aunque CURSO_URL_API esté definida; `None` usa config.URL_API.
    """
    global _modos
    with _cerrojo:
        _contexto.update(ruta_db=ruta_db, carpeta_modelo=carpeta_modelo, url_api=url_api)
        _modos = None


def _servicio_modos():
    """Un único objeto Modos (y su modelo cargado) para todas las llamadas: cargar el modelo cuesta, no se repite."""
    global _modos
    with _cerrojo:
        if _modos is None:
            url = _contexto['url_api'] if _contexto['url_api'] is not None else config.URL_API
            consulta = Consulta(ruta_db=_contexto['ruta_db'], url_api=url, carpeta_modelo=_contexto['carpeta_modelo'])
            _modos = Modos(consulta, demo=False)         # el agente nunca simula compras: demo apagado
        return _modos


def precargar():
    """Carga el modelo y hace una puntuación de prueba ANTES de atender peticiones. Devuelve None si todo va bien, o el motivo si no.

    Para qué: en Windows, importar las librerías científicas (scipy, scikit-learn) por primera vez mientras el servidor MCP ya lee su
    entrada estándar (stdio) deja el proceso colgado. Cargando todo antes de abrir el canal, la primera consulta responde al momento y
    sin ese riesgo. Si no hay modelo o base, no es un fallo del arranque: cada herramienta lo explicará cuando la llamen.
    """
    try:
        servicio = _servicio_modos().c._servicio_local()
        medio = {v: (lo + hi) / 2 for v, (lo, hi) in servicio.meta['rangos_entrenamiento'].items()}
        servicio.predecir([medio])
        _pesos_exactos(servicio.modelo, servicio.variables, medio)
        return None
    except Exception as e:                                   # noqa: BLE001 - sin modelo todavía: las herramientas lo dirán
        return _sin_rutas(f'{type(e).__name__}: {e}')


def _modos_con_base():
    """Como _servicio_modos, pero sin base no la crea vacía (SQLite lo haría al abrirla): dice qué falta."""
    if not Path(_contexto['ruta_db'] or config.DB).is_file():
        raise NoEncontrado('No existe la base de datos del caso: hay que ejecutar antes el pipeline (python -m ia_mlops.pipeline).')
    return _servicio_modos()


# --------------------------------------------------------------------------------------------------------- utilidades
def _serializable(d):
    """Pasa por JSON para garantizar que todo es serializable (los tipos de numpy y pandas se convierten a Python)."""
    def por_defecto(o):
        if hasattr(o, 'item'):
            return o.item()
        return str(o)
    return json.loads(json.dumps(d, default=por_defecto, ensure_ascii=False))


def _sin_rutas(texto):
    """Quita del mensaje la ruta de quien lo ejecuta (la raíz del proyecto pasa a «.»)."""
    return str(texto).replace(str(config.RAIZ), '.')


def _herramienta(f):
    """Convierte cualquier fallo en {'error': ...}: una herramienta no lanza excepciones al agente."""
    @functools.wraps(f)
    def interior(*args, **kwargs):
        try:
            return _serializable(f(*args, **kwargs))
        except NoEncontrado as e:
            return {'error': _sin_rutas(e), 'tipo': 'sin_datos'}
        except PeticionNoValida as e:
            return {'error': _sin_rutas(e), 'tipo': 'peticion_no_valida'}
        except produccion.ErrorReferencia as e:
            return {'error': _sin_rutas(e), 'tipo': 'sin_referencia'}
        except Exception as e:                                   # noqa: BLE001 - el agente debe poder seguir
            return {'error': f'No se pudo completar la consulta ({type(e).__name__}): {_sin_rutas(e)}', 'tipo': 'fallo_interno'}
    return interior


def _a_entero(n, nombre, minimo=1):
    try:
        if isinstance(n, bool) or (isinstance(n, float) and not n.is_integer()):
            raise ValueError
        n = int(n) if isinstance(n, (int, float)) else int(str(n).strip())
    except ValueError:
        raise PeticionNoValida(f'«{nombre}» debe ser un número entero (llegó {n!r}).') from None
    if n < minimo:
        raise PeticionNoValida(f'«{nombre}» debe ser como mínimo {minimo} (llegó {n}).')
    return n


# --------------------------------------------------------------------------------------------------------- lista del día
@_herramienta
def lista_del_dia(n=10):
    """Los `n` clientes con más probabilidad de la última campaña por lotes, de mayor a menor.

    Lee reports/campana/ (la que escribe `python -m ia_mlops.explotacion`). Devuelve el corte de la campaña, cuántos clientes
    se puntuaron y, de cada cliente: puesto, cliente_id, probabilidad, tramo (alta/media/baja), recomendación de negocio, decil,
    si está en la campaña y si hay que revisar la puntuación (el modelo avisó de valores que no vio al entrenar).
    """
    n = _a_entero(n, 'n')
    ruta = panel.ultima_campana()
    if ruta is None:
        return {'error': 'Todavía no hay campaña: hay que ejecutar antes el lote (python -m ia_mlops.explotacion).', 'tipo': 'sin_datos'}
    csv, js = ruta
    tabla = pd.read_csv(csv)
    faltan = [c for c in ('cliente_id', 'probabilidad') if c not in tabla.columns]
    if faltan:
        return {'error': f'La campaña {csv.name} no tiene las columnas {faltan}.', 'tipo': 'sin_datos'}
    if tabla.empty:
        return {'error': f'La campaña {csv.name} está vacía.', 'tipo': 'sin_datos'}
    resumen = {}
    if js.exists():
        try:
            resumen = {k: v for k, v in json.loads(js.read_text(encoding='utf-8')).items() if k in _RESUMEN_PUBLICO}
        except json.JSONDecodeError:
            resumen = {}
    aviso = None
    if n > MAXIMO_LISTA:
        aviso = f'Se pidieron {n} clientes; el máximo por lista es {MAXIMO_LISTA}.'
        n = MAXIMO_LISTA
    tabla = tabla.sort_values(['probabilidad', 'cliente_id'], ascending=[False, True], kind='stable').head(n)
    clientes = []
    for i, f in enumerate(tabla.to_dict('records'), start=1):
        s = segmento_de(float(f['probabilidad']))
        clientes.append({
            'puesto': int(f['puesto']) if pd.notna(f.get('puesto')) else i, 'cliente_id': int(f['cliente_id']),
            'probabilidad': round(float(f['probabilidad']), 4), 'tramo': s['segmento'], 'recomendacion': s['recomendacion'],
            'decil': int(f['decil']) if pd.notna(f.get('decil')) else None,
            'en_campana': bool(f['en_campana']) if 'en_campana' in f and pd.notna(f['en_campana']) else None,
            'revisar': bool(pd.notna(f.get('n_advertencias')) and int(f['n_advertencias']) > 0)})
    r = {'campana': csv.name, **resumen, 'pedidos': n, 'devueltos': len(clientes), 'clientes': clientes}
    if aviso:
        r['aviso'] = aviso
    return r


# --------------------------------------------------------------------------------------------------------- puntuar
@_herramienta
def puntuar_bajo_demanda(cliente_id):
    """Probabilidad de recompra a 90 días con las variables LEÍDAS de fs_produccion (las del último lote: «las de ayer»).

    Es lo mismo que devuelve GET /bajo-demanda/{id}. Error si el cliente no está en fs_produccion o la tabla no existe.
    """
    return _modos_con_base().bajo_demanda_uno(leer_ids([cliente_id])[0])


@_herramienta
def puntuar_online(cliente_id, corte=None):
    """Probabilidad de recompra a 90 días con las variables CALCULADAS AL VUELO («ahora»), con la última compra incluida.

    Es lo mismo que devuelve GET /online/{id}. `corte` (AAAA-MM-DD, opcional) solo sirve para comparar con otra fecha: por defecto
    es «ahora» (el día siguiente a la última factura conocida).
    """
    return _modos_con_base().online(leer_ids([cliente_id])[0], corte or None)


# --------------------------------------------------------------------------------------------------------- versión
@_herramienta
def version_en_produccion():
    """La versión del modelo que está en producción: cuál es, desde cuándo, con qué cifras se aprobó y qué versiones hubo antes.

    Sale de models/referencia.json (la ficha de la versión aprobada) y de models/historial_versiones.json (opcional).
    """
    ref = produccion.leer_referencia()
    r = {'version': ref['version'], 'en_produccion_desde': ref['aprobado_en'], 'etiqueta_imagen': ref['etiqueta_imagen'],
         'modelo': ref['modelo'], 'huella_datos': ref['huella_datos'], 'fuente_datos': produccion.fuente_de(ref),
         'metrica_principal': ref['metrica_principal'], 'metricas_test': ref['metricas_test'], 'entrenado_en': ref['entrenado_en']}
    try:
        r['historial'] = produccion.leer_historial()
    except produccion.ErrorReferencia as e:
        r['historial'] = None
        r['aviso'] = _sin_rutas(e)
    return r


@_herramienta
def referencia_del_modelo():
    """La ficha completa de la versión en producción (models/referencia.json), tal cual. Es el recurso referencia://modelo."""
    return produccion.leer_referencia()


# --------------------------------------------------------------------------------------------------------- por qué
def _pesos_exactos(modelo, variables, fila):
    """Si el modelo es regresión logística (con su preprocesado dentro de un Pipeline), descompone su logit en un peso por variable.

    logit = intercepto + Σ coeficiente_j × valor_j, donde valor_j es la variable YA transformada por el pipeline (imputar la mediana,
    log1p y estandarizar). Es exacto, no una aproximación: probabilidad = 1 / (1 + e^-logit). Devuelve None si el modelo no es de ese tipo.
    """
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    if not isinstance(modelo, Pipeline) or not isinstance(modelo.steps[-1][1], LogisticRegression):
        return None
    logistica = modelo.steps[-1][1]
    if logistica.coef_.shape[0] != 1:
        return None
    X = pd.DataFrame([fila])[variables].apply(pd.to_numeric, errors='coerce').astype('float64')
    Z = np.asarray(modelo[:-1].transform(X), dtype='float64')[0]
    coef = logistica.coef_[0]
    pesos = coef * Z
    intercepto = float(logistica.intercept_[0])
    logit = intercepto + float(pesos.sum())
    return {'pesos': [float(p) for p in pesos], 'estandarizados': [float(z) for z in Z], 'coeficientes': [float(c) for c in coef],
            'intercepto': intercepto, 'logit': logit, 'probabilidad': 1.0 / (1.0 + math.exp(-logit))}


@_herramienta
def por_que(cliente_id, n=5):
    """Las variables que más pesan en la probabilidad de un cliente (con las variables de «ahora», como puntuar_online).

    Con la regresión logística en producción el cálculo es EXACTO: el peso de cada variable es su coeficiente por su valor ya
    transformado (imputado, log1p y estandarizado), medido en logit; la suma de todos los pesos más el intercepto da la probabilidad
    que devuelve el modelo (se comprueba). Positivo = empuja la probabilidad hacia arriba; negativo = hacia abajo. Si el modelo no
    permite esa descomposición, se devuelven las 13 variables con su valor y una nota: no se inventan pesos.
    """
    n = min(_a_entero(n, 'n'), MAXIMO_VARIABLES)
    actual = puntuar_online(cliente_id)
    if 'error' in actual:
        return actual
    modos = _servicio_modos()
    base = {'cliente_id': actual['cliente_id'], 'corte': actual['corte'], 'probabilidad': actual['probabilidad'],
            'tramo': actual['segmento'], 'modelo': actual['modelo'], 'huella_datos': actual['huella_datos']}
    sin_peso = {**base, 'metodo': 'solo_valores', 'variables': actual['variables']}
    try:
        servicio = modos.c._servicio_local()          # el modelo de models/ (carpeta_modelo): el que se puede abrir y descomponer
    except Exception as e:                            # noqa: BLE001 - sin modelo local: solo los valores
        return {**sin_peso, 'nota': f'No hay un modelo local que descomponer ({_sin_rutas(e)}); se devuelven los valores sin pesos.'}
    if servicio.meta['huella_datos'] != actual['huella_datos']:
        return {**sin_peso, 'nota': 'El modelo local no es el que sirve la API (otra huella de datos): no se calculan pesos para no mezclar versiones.'}
    d = _pesos_exactos(servicio.modelo, servicio.variables, actual['variables'])
    if d is None:
        return {**sin_peso, 'nota': f'El modelo «{actual["modelo"]}» no es una regresión logística: no permite repartir la probabilidad '
                                    'por variable de forma exacta, así que solo se devuelven las 13 variables con su valor.'}
    if abs(d['probabilidad'] - actual['probabilidad']) > 1e-6:
        return {**sin_peso, 'nota': 'La descomposición no reproduce la probabilidad del modelo: no se devuelven pesos.'}
    filas = []
    for variable, peso, z, c in zip(servicio.variables, d['pesos'], d['estandarizados'], d['coeficientes']):
        valor = actual['variables'][variable]
        filas.append({'variable': variable, 'valor': valor, 'peso_logit': round(peso, 4), 'efecto': 'sube' if peso > 0 else 'baja' if peso < 0 else 'neutro',
                      'valor_estandarizado': round(z, 4), 'coeficiente': round(c, 4), 'imputada_con_la_mediana': valor is None})
    filas.sort(key=lambda f: (-abs(f['peso_logit']), f['variable']))
    return {**base, 'metodo': 'regresion_logistica_exacto', 'intercepto_logit': round(d['intercepto'], 4), 'logit_total': round(d['logit'], 4),
            'variables_que_mas_pesan': filas[:n], 'variables_totales': len(filas),
            'nota': 'peso_logit = coeficiente × valor transformado (imputar, log1p, estandarizar). Intercepto + suma de los pesos = logit; '
                    'probabilidad = 1 / (1 + e^-logit). Es el modelo, no una opinión: dice qué empuja la probabilidad, no por qué compra el cliente.'}
