"""La versión en producción: qué modelo está publicado, con qué datos se entrenó y cómo se decide si una versión nueva lo sustituye.

QUÉ ES «LA VERSIÓN EN PRODUCCIÓN»
    Es el modelo que hoy responde a las peticiones y puntúa los lotes. Para poder hablar de él con precisión hace falta
    saber cuál es: qué versión, entrenada con qué datos, con qué resultado y empaquetada en qué imagen. Eso es lo que
    guarda `models/referencia.json`.

POR QUÉ UN ARCHIVO EN EL REPOSITORIO Y UNA IMAGEN VERSIONADA
    * La IMAGEN (`retencion-api:v<N>-<huella>`) es el modelo ya empaquetado con su API: inmutable, se puede descargar y
      ejecutar donde sea, y las versiones anteriores siguen disponibles, así que volver atrás (rollback) es volver a usar
      una etiqueta antigua.
    * El ARCHIVO `models/referencia.json` es la ficha de esa imagen: dice cuál es la vigente y con qué cifras se aprobó.
      Vive en el repositorio, no en `models/` generado, para que cambiarlo sea un cambio revisable (un pull request),
      con historial, y para que cualquier ejecución (tu portátil, un workflow, un contenedor) lea la misma verdad.
      Nadie lo edita a mano: lo escribe `python -m ia_mlops.produccion crear` tras aprobar una versión.

CÓMO SE DECIDE SI UNA VERSIÓN NUEVA ENTRA (comparar_con_referencia)
    1. Misma huella de datos que la de producción: «igual». Entrenar con los mismos datos da el mismo modelo; no hay nada
       que publicar (idempotencia).
    2. Si no, se compara la métrica principal (config.METRICA_COMPARACION, el AUC) medida en TEST, en los mismos cortes
       en las dos versiones, de modo que las cifras son comparables. Si la nueva empeora MÁS que config.TOLERANCIA_COMPARACION:
       «rechazada». En otro caso: «aceptada» (todavía falta la aprobación humana antes de publicar).

ESQUEMA DE models/referencia.json (todas las claves son obligatorias salvo mlflow_version_registrada, que puede ser null)
    esquema                  1, versión del formato de este archivo
    version                  entero >= 1: la versión de producción (v1, v2...)
    etiqueta_imagen          retencion-api:v<version>-<huella_datos>
    huella_datos             huella de los datos de entrenamiento (la de models/metadatos.json)
    modelo                   tipo de modelo elegido (p. ej. regresion_logistica)
    metrica_principal        nombre de la métrica con la que se compara (config.METRICA_COMPARACION)
    metricas_test            métricas medidas en test (las que calcula modeling/train.py: auc, precision_media...)
    metricas_valid           las mismas en valid (con la que se eligió el modelo)
    cortes_test              fechas de corte de test: la ventana en la que se mide, igual para todas las versiones
    entrenado_en             fecha y hora del entrenamiento (de metadatos.json)
    aprobado_en              fecha y hora en que se aprobó la versión
    mlflow_version_registrada  versión del modelo en el registro de MLflow, si se conoce (o null)

Uso (desde 04-Proyecto-Base, con el modelo ya entrenado: python -m ia_mlops.pipeline):
    python -m ia_mlops.produccion mostrar                      # la versión en producción
    python -m ia_mlops.produccion crear --version 1            # fija el modelo actual como versión 1
    python -m ia_mlops.produccion comparar                     # el modelo recién entrenado frente a la referencia
    python -m ia_mlops.produccion comparar --metricas candidata.json
    python -m ia_mlops.produccion comparar --json decision.json      # además guarda la decisión y las métricas de las dos versiones
    python -m ia_mlops.produccion crear --version 2 --fuente completo   # anota la fuente de datos (opcional; sin ella se entiende «muestra»)
    python -m ia_mlops.produccion historial [--retira ficha.json --estado-retirada anterior|retirada]   # models/historial_versiones.json
    python -m ia_mlops.produccion exportar-test --salida test.csv       # filas de test de ml_dataset
    python -m ia_mlops.produccion comparar-tramos --referencia <models/ de producción> --datos test.csv   # cuántos clientes cambian de tramo
Código de salida de `comparar`: 0 igual o aceptada · 1 rechazada · 2 no se pudo comparar.
"""
import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from . import config

ESQUEMA = 1
PREFIJO_IMAGEN = 'retencion-api'
_ETIQUETA = re.compile(rf'^{PREFIJO_IMAGEN}:v(\d+)-([0-9a-f]+)$')
_CLAVES = ('esquema', 'version', 'etiqueta_imagen', 'huella_datos', 'modelo', 'metrica_principal', 'metricas_test',
           'metricas_valid', 'cortes_test', 'entrenado_en', 'aprobado_en')
_EPSILON = 1e-12    # la tolerancia es «empeora MÁS que»: los flotantes no deben decidir un caso justo en el límite


class ErrorReferencia(RuntimeError):
    """La referencia no existe, está rota o no se puede comparar. El mensaje dice qué hacer."""


# ----------------------------------------------------------------------------------------------------------- lectura
def etiqueta_imagen(version, huella):
    """Etiqueta de la imagen de la API: retencion-api:v<N>-<huella>."""
    return f'{PREFIJO_IMAGEN}:v{int(version)}-{huella}'


def validar_referencia(d):
    """Comprueba el esquema de la referencia. Devuelve `d` si es correcta; si no, ErrorReferencia con todos los fallos."""
    if not isinstance(d, dict):
        raise ErrorReferencia('La referencia debe ser un objeto JSON (un diccionario).')
    fallos = [f'falta la clave «{k}»' for k in _CLAVES if k not in d]
    if not fallos:
        if d['esquema'] != ESQUEMA:
            fallos.append(f'esquema {d["esquema"]!r}: este código entiende el {ESQUEMA}')
        if not isinstance(d['version'], int) or isinstance(d['version'], bool) or d['version'] < 1:
            fallos.append('«version» debe ser un entero mayor o igual que 1')
        if not isinstance(d['huella_datos'], str) or not d['huella_datos']:
            fallos.append('«huella_datos» debe ser un texto no vacío')
        coincide = _ETIQUETA.match(str(d['etiqueta_imagen']))
        if not coincide:
            fallos.append(f'«etiqueta_imagen» {d["etiqueta_imagen"]!r} no tiene la forma {PREFIJO_IMAGEN}:v<N>-<huella>')
        elif int(coincide.group(1)) != d['version'] or coincide.group(2) != d['huella_datos']:
            fallos.append('«etiqueta_imagen» no coincide con «version» y «huella_datos»')
        for clave in ('metricas_test', 'metricas_valid'):
            if not isinstance(d[clave], dict) or not d[clave]:
                fallos.append(f'«{clave}» debe ser un diccionario de métricas')
        if isinstance(d['metricas_test'], dict) and d['metrica_principal'] not in d['metricas_test']:
            fallos.append(f'«metricas_test» no contiene la métrica principal «{d["metrica_principal"]}»')
        if not isinstance(d['cortes_test'], list) or not d['cortes_test']:
            fallos.append('«cortes_test» debe ser una lista de fechas no vacía')
        if 'mlflow_version_registrada' in d and d['mlflow_version_registrada'] is not None \
                and not isinstance(d['mlflow_version_registrada'], int):
            fallos.append('«mlflow_version_registrada» debe ser un entero o null')
        if 'fuente_datos' in d and d['fuente_datos'] not in config.FUENTES:
            fallos.append(f'«fuente_datos» debe ser una de {list(config.FUENTES)} (es {d["fuente_datos"]!r})')
    if fallos:
        raise ErrorReferencia('La referencia no es válida: ' + '; '.join(fallos) + '. Se regenera con: python -m ia_mlops.produccion crear --version N')
    return d


def leer_referencia(ruta=None):
    """Lee y valida models/referencia.json (o la ruta indicada)."""
    ruta = Path(ruta or config.REFERENCIA)
    if not ruta.exists():
        raise ErrorReferencia(f'No existe {ruta}: todavía no hay versión en producción. Se crea con: python -m ia_mlops.produccion crear --version 1')
    try:
        d = json.loads(ruta.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        raise ErrorReferencia(f'{ruta} no es un JSON válido ({e}). No se edita a mano: se regenera con: python -m ia_mlops.produccion crear --version N') from e
    return validar_referencia(d)


# ----------------------------------------------------------------------------------------------------------- creación
def leer_candidata(carpeta=None, reportes=None):
    """El modelo recién entrenado, tal como lo dejó modeling/train.py: models/metadatos.json + reports/metricas.json.

    metadatos.json trae la huella, el modelo, la métrica de valid y las fechas de corte; las métricas de TEST las trae
    reports/metricas.json (la del modelo que train.py eligió). Devuelve un diccionario con `metricas_test` ya incorporada.
    """
    carpeta, reportes = Path(carpeta or config.MODELOS), Path(reportes or config.REPORTES)
    ruta_meta, ruta_metricas = carpeta / 'metadatos.json', reportes / 'metricas.json'
    for ruta in (ruta_meta, ruta_metricas):
        if not ruta.exists():
            raise ErrorReferencia(f'No existe {ruta}. Entrena antes el modelo: python -m ia_mlops.pipeline')
    meta = json.loads(ruta_meta.read_text(encoding='utf-8'))
    metricas = json.loads(ruta_metricas.read_text(encoding='utf-8'))
    if metricas.get('mejor') != meta.get('modelo'):
        raise ErrorReferencia(f'{ruta_metricas} es del modelo «{metricas.get("mejor")}» y {ruta_meta} del «{meta.get("modelo")}»: '
                              'no son del mismo entrenamiento. Vuelve a entrenar: python -m ia_mlops.pipeline')
    return {**meta, 'metricas_test': metricas['modelos'][meta['modelo']]['test']}


def fuente_de(referencia):
    """De qué fuente de datos salió la versión en producción (config.FUENTES). Las referencias anteriores a esta clave son de la muestra."""
    return referencia.get('fuente_datos') or 'muestra'


def crear_referencia(desde_metadatos, version, etiqueta=None, aprobado_en=None, mlflow_version=None, fuente=None):
    """Construye (sin escribir) el diccionario de referencia a partir de la candidata (ver leer_candidata).

    `desde_metadatos` es el contenido de metadatos.json con `metricas_test` añadida. `etiqueta` por defecto es
    retencion-api:v<version>-<huella>. `fuente` (opcional: 'muestra' o 'completo') anota con qué fuente de datos se entrenó,
    para poder reproducir la versión de producción más tarde (nueva-version.yml la reentrena para compararla con la candidata).
    Devuelve el diccionario ya validado.
    """
    for clave in ('modelo', 'huella_datos', 'metricas_valid', 'metricas_test', 'cortes', 'entrenado_en'):
        if clave not in desde_metadatos:
            raise ErrorReferencia(f'A los metadatos les falta «{clave}»: usa leer_candidata() o entrena de nuevo (python -m ia_mlops.pipeline).')
    d = {
        'esquema': ESQUEMA,
        'version': int(version),
        'etiqueta_imagen': etiqueta or etiqueta_imagen(version, desde_metadatos['huella_datos']),
        'huella_datos': desde_metadatos['huella_datos'],
        'modelo': desde_metadatos['modelo'],
        'metrica_principal': config.METRICA_COMPARACION,
        'metricas_test': desde_metadatos['metricas_test'],
        'metricas_valid': desde_metadatos['metricas_valid'],
        'cortes_test': list(desde_metadatos['cortes']['test']),
        'entrenado_en': desde_metadatos['entrenado_en'],
        'aprobado_en': aprobado_en or datetime.now().isoformat(timespec='seconds'),
        'mlflow_version_registrada': mlflow_version,
    }
    if fuente:
        d['fuente_datos'] = fuente
    return validar_referencia(d)


def escribir_referencia(d, ruta=None):
    """Valida y guarda la referencia en el repositorio (models/referencia.json)."""
    validar_referencia(d)
    ruta = Path(ruta or config.REFERENCIA)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(d, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return ruta


# ----------------------------------------------------------------------------------------------------------- comparación
@dataclass
class Decision:
    """Resultado de comparar una versión nueva con la de producción."""
    decision: str               # 'igual' | 'aceptada' | 'rechazada'
    motivo: str                 # frase legible: por qué
    metrica: str
    referencia: float | None    # métrica de la versión en producción (None si no se llegó a comparar)
    candidata: float | None
    diferencia: float | None    # candidata - referencia (negativa = empeora)
    tolerancia: float
    misma_huella_datos: bool

    def como_dict(self):
        return asdict(self)


def comparar_con_referencia(metricas_nuevas, referencia, tolerancia=None):
    """Decide qué hacer con la versión nueva. `metricas_nuevas` = {'huella_datos': ..., 'metricas_test': {...}, 'cortes': {...}}
    (lo que devuelve leer_candidata; `cortes` es opcional). `referencia` es el diccionario de leer_referencia.

    «igual»     la huella de datos coincide: mismos datos, nada que publicar.
    «rechazada» la métrica principal empeora más que la tolerancia (diferencia absoluta).
    «aceptada»  en otro caso (la métrica mejora, se mantiene o empeora menos que la tolerancia).
    """
    tolerancia = config.TOLERANCIA_COMPARACION if tolerancia is None else float(tolerancia)
    metrica = referencia['metrica_principal']
    huella = metricas_nuevas.get('huella_datos')
    if huella is not None and huella == referencia['huella_datos']:
        return Decision('igual', f'Los datos son los mismos que los de la versión {referencia["version"]} en producción '
                        f'(huella {huella}): no hay nada que publicar.', metrica, None, None, None, tolerancia, True)
    cortes = (metricas_nuevas.get('cortes') or {}).get('test')
    if cortes is not None and list(cortes) != list(referencia['cortes_test']):
        raise ErrorReferencia(f'La referencia se midió en los cortes de test {referencia["cortes_test"]} y la candidata en {list(cortes)}: '
                              'no son comparables. Fija una referencia nueva con los mismos cortes.')
    if metrica not in (metricas_nuevas.get('metricas_test') or {}):
        raise ErrorReferencia(f'A las métricas nuevas les falta «metricas_test.{metrica}», la métrica principal con la que se compara.')
    ref, cand = float(referencia['metricas_test'][metrica]), float(metricas_nuevas['metricas_test'][metrica])
    dif = cand - ref
    resumen = f'{metrica} de test {cand:.4f} frente a {ref:.4f} de la versión {referencia["version"]} (diferencia {dif:+.4f}'
    if dif < -tolerancia - _EPSILON:
        motivo = f'{resumen}): empeora más que la tolerancia de {tolerancia:g}. No se publica.'
        return Decision('rechazada', motivo, metrica, ref, cand, dif, tolerancia, False)
    motivo = f'{resumen}) dentro de la tolerancia de {tolerancia:g}: puede pasar a la aprobación.'
    return Decision('aceptada', motivo, metrica, ref, cand, dif, tolerancia, False)


# ----------------------------------------------------------------------------------------------------------- historial
# models/historial_versiones.json: la lista de versiones que han pasado por producción, para el panel (pestaña «Versiones»).
# Formato: {"versiones": [ {version, etiqueta_imagen, huella_datos, modelo, fuente_datos, auc_test, entrenado_en, aprobado_en, estado}, ... ]}
# con solo campos escalares (el panel los muestra como columnas). `estado`:
#   produccion  la versión vigente (solo una a la vez: la de models/referencia.json)
#   anterior    estuvo en producción y la sustituyó una versión más nueva
#   retirada    estuvo en producción y se retiró con un rollback
# Va en el MISMO pull request que referencia.json (nueva-version.yml y rollback.yml), así que cambia por revisión, nunca a mano.
ESTADOS_HISTORIAL = ('produccion', 'anterior', 'retirada')
_CAMPOS_HISTORIAL = ('version', 'etiqueta_imagen', 'huella_datos', 'modelo', 'fuente_datos', 'auc_test', 'entrenado_en', 'aprobado_en', 'estado')


def ruta_historial(ruta_referencia=None):
    """El historial vive junto a la referencia (models/historial_versiones.json), también cuando la referencia se desvía con CURSO_REFERENCIA."""
    return Path(ruta_referencia or config.REFERENCIA).with_name('historial_versiones.json')


def entrada_historial(referencia, estado):
    """Una fila del historial a partir de una referencia (la ficha de una versión) y su estado."""
    if estado not in ESTADOS_HISTORIAL:
        raise ErrorReferencia(f'Estado {estado!r} no válido: debe ser uno de {list(ESTADOS_HISTORIAL)}.')
    validar_referencia(referencia)
    return {'version': referencia['version'], 'etiqueta_imagen': referencia['etiqueta_imagen'], 'huella_datos': referencia['huella_datos'],
            'modelo': referencia['modelo'], 'fuente_datos': fuente_de(referencia),
            'auc_test': referencia['metricas_test'].get('auc'),
            'entrenado_en': referencia['entrenado_en'], 'aprobado_en': referencia['aprobado_en'], 'estado': estado}


def leer_historial(ruta=None):
    """Las versiones del historial (lista vacía si todavía no hay archivo)."""
    ruta = Path(ruta or ruta_historial())
    if not ruta.exists():
        return []
    try:
        d = json.loads(ruta.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        raise ErrorReferencia(f'{ruta} no es un JSON válido ({e}). No se edita a mano: lo escribe python -m ia_mlops.produccion historial.') from e
    if not isinstance(d, dict) or not isinstance(d.get('versiones'), list):
        raise ErrorReferencia(f'{ruta} debe ser un objeto con la lista «versiones».')
    return d['versiones']


def actualizar_historial(referencia, retira=None, estado_retirada='anterior', ruta=None):
    """Deja `referencia` como la versión en producción del historial y devuelve la lista nueva (la guarda en `ruta`).

    * La fila de `referencia` se añade (o se actualiza si ya estaba: se conserva su posición) con estado «produccion».
    * Cualquier otra fila que figurase en «produccion» pasa a `estado_retirada`: «anterior» si la sustituye una versión nueva,
      «retirada» si se vuelve atrás con un rollback.
    * `retira` (opcional): la ficha de la versión que deja de estar en producción. Si no estaba en el historial, se añade con
      `estado_retirada` (así el historial es completo aunque se creara después de esa versión).
    """
    if estado_retirada not in ESTADOS_HISTORIAL[1:]:
        raise ErrorReferencia(f'El estado de la versión que sale debe ser «anterior» o «retirada» (es {estado_retirada!r}).')
    nueva = entrada_historial(referencia, 'produccion')
    filas = [dict(f) for f in leer_historial(ruta)]
    for f in filas:
        if f.get('version') != nueva['version'] and f.get('estado') == 'produccion':
            f['estado'] = estado_retirada
    if retira is not None and retira['version'] != nueva['version']:
        saliente = entrada_historial(retira, estado_retirada)
        for f in filas:
            if f.get('version') == saliente['version']:
                f['estado'] = estado_retirada
                break
        else:
            filas.append(saliente)
    for i, f in enumerate(filas):
        if f.get('version') == nueva['version']:
            filas[i] = nueva
            break
    else:
        filas.append(nueva)
    destino = Path(ruta or ruta_historial())
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps({'versiones': filas}, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return filas


# ----------------------------------------------------------------------------------------------------------- campeón y candidata
def tramo(probabilidad):
    """El tramo de negocio (config.SEGMENTOS_RECOMPRA) al que pertenece una probabilidad: el primero cuyo «desde» no la supera."""
    for s in config.SEGMENTOS_RECOMPRA:
        if probabilidad >= s['desde']:
            return s['segmento']
    return config.SEGMENTOS_RECOMPRA[-1]['segmento']


def _probabilidades(carpeta, datos):
    import joblib
    ruta = Path(carpeta) / 'modelo.joblib'
    if not ruta.exists():
        raise ErrorReferencia(f'No existe {ruta}: es la carpeta de un modelo entrenado (la que deja python -m ia_mlops.pipeline en models/).')
    return joblib.load(ruta).predict_proba(datos[config.FEATURES].astype(float))[:, 1]


def comparar_tramos(carpeta_referencia, carpeta_candidata, datos):
    """Campeón frente a candidata sobre LOS MISMOS clientes y cortes: cuántos cambian de tramo de negocio.

    `carpeta_*`: carpeta `models/` de cada versión (con modelo.joblib). `datos`: DataFrame con cliente_id, fecha_corte, las variables
    de config.FEATURES y, si se quiere medir también el AUC, el objetivo `y` (p. ej. las filas de test de ml_dataset de la candidata).
    Las dos versiones puntúan exactamente las mismas filas, así que la diferencia es del modelo, no de los datos.
    """
    import numpy as np
    from sklearn.metrics import roc_auc_score
    if len(datos) == 0:
        raise ErrorReferencia('No hay filas con las que comparar las dos versiones.')
    datos = datos.reset_index(drop=True)
    p_ref, p_cand = _probabilidades(carpeta_referencia, datos), _probabilidades(carpeta_candidata, datos)
    tramos = [s['segmento'] for s in config.SEGMENTOS_RECOMPRA]          # de mayor a menor probabilidad
    t_ref, t_cand = [tramo(p) for p in p_ref], [tramo(p) for p in p_cand]
    orden = {t: i for i, t in enumerate(tramos)}
    matriz = {a: {b: 0 for b in tramos} for a in tramos}
    for a, b in zip(t_ref, t_cand):
        matriz[a][b] += 1
    cambian = sum(1 for a, b in zip(t_ref, t_cand) if a != b)
    suben = sum(1 for a, b in zip(t_ref, t_cand) if orden[b] < orden[a])      # a un tramo de probabilidad más alta
    por_corte = {}
    for corte, indices in datos.groupby('fecha_corte').groups.items():
        i = list(indices)
        n_cambian = sum(1 for k in i if t_ref[k] != t_cand[k])
        por_corte[str(corte)] = {'filas': len(i), 'cambian': n_cambian, 'pct_cambian': round(100.0 * n_cambian / len(i), 1)}
    r = {
        'filas': int(len(datos)), 'clientes': int(datos['cliente_id'].nunique()), 'cortes': sorted(por_corte),
        'tramos': tramos, 'matriz': matriz, 'cambian': cambian, 'pct_cambian': round(100.0 * cambian / len(datos), 1),
        'suben': suben, 'bajan': cambian - suben, 'por_corte': por_corte,
        'prob_media_referencia': round(float(np.mean(p_ref)), 4), 'prob_media_candidata': round(float(np.mean(p_cand)), 4),
        'dif_abs_media': round(float(np.mean(np.abs(p_cand - p_ref))), 4), 'dif_abs_max': round(float(np.max(np.abs(p_cand - p_ref))), 4),
        'auc_referencia': None, 'auc_candidata': None,
    }
    if config.OBJETIVO in datos.columns and datos[config.OBJETIVO].nunique() == 2:
        r['auc_referencia'] = round(float(roc_auc_score(datos[config.OBJETIVO], p_ref)), 4)
        r['auc_candidata'] = round(float(roc_auc_score(datos[config.OBJETIVO], p_cand)), 4)
    return r


def resumen_tramos_md(r, version_referencia=None, version_candidata=None):
    """La comparación campeón/candidata (resultado de comparar_tramos) en Markdown, para el resumen de GitHub Actions."""
    a = f'v{version_referencia}' if version_referencia else 'referencia'
    b = f'v{version_candidata}' if version_candidata else 'candidata'
    tramos = r['tramos']
    lineas = [f'Se puntúan las mismas {r["filas"]} filas ({r["clientes"]} clientes) de los cortes de test {", ".join(r["cortes"])} con las dos versiones.',
              '', f'**{r["cambian"]} de {r["filas"]} filas ({r["pct_cambian"]} %) cambian de tramo** ({r["suben"]} suben, {r["bajan"]} bajan).', '',
              f'| {a} \\ {b} | ' + ' | '.join(tramos) + ' |', '|---|' + '---|' * len(tramos)]
    for t in tramos:
        lineas.append(f'| **{t}** | ' + ' | '.join(str(r['matriz'][t][u]) for u in tramos) + ' |')
    lineas += ['', '| corte | filas | cambian de tramo |', '|---|---|---|']
    lineas += [f'| {c} | {v["filas"]} | {v["cambian"]} ({v["pct_cambian"]} %) |' for c, v in r['por_corte'].items()]
    lineas += ['', f'Probabilidad media: {r["prob_media_referencia"]:.4f} ({a}) frente a {r["prob_media_candidata"]:.4f} ({b}); '
               f'diferencia absoluta media {r["dif_abs_media"]:.4f}, máxima {r["dif_abs_max"]:.4f}.']
    if r['auc_referencia'] is not None:
        lineas.append(f'AUC sobre estas mismas filas: {r["auc_referencia"]:.4f} ({a}) frente a {r["auc_candidata"]:.4f} ({b}).')
    return '\n'.join(lineas) + '\n'


def exportar_test(salida, con=None):
    """Guarda en CSV las filas de test de ml_dataset (clientes, cortes, variables y objetivo): lo que comparar_tramos puntúa."""
    import pandas as pd
    from . import db
    cierre = con is None
    con = con or db.conectar()
    try:
        df = pd.read_sql("SELECT * FROM ml_dataset WHERE particion = 'test' ORDER BY cliente_id, fecha_corte", con)
    finally:
        if cierre:
            con.close()
    if df.empty:
        raise ErrorReferencia('ml_dataset no tiene filas de test: ejecuta antes python -m ia_mlops.pipeline.')
    salida = Path(salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(salida, index=False)
    return salida


# ----------------------------------------------------------------------------------------------------------- terminal
def _mostrar(d):
    print(f'Versión en producción: v{d["version"]}')
    print(f'  imagen         {d["etiqueta_imagen"]}')
    print(f'  modelo         {d["modelo"]}')
    print(f'  datos          huella {d["huella_datos"]} (fuente «{fuente_de(d)}»)')
    print(f'  test           ' + ' · '.join(f'{k} {v:.4f}' for k, v in d['metricas_test'].items()) + f'   (cortes {", ".join(d["cortes_test"])})')
    print(f'  métrica clave  {d["metrica_principal"]} de test = {d["metricas_test"][d["metrica_principal"]]:.4f}')
    print(f'  entrenada      {d["entrenado_en"]}')
    print(f'  aprobada       {d["aprobado_en"]}')
    if d.get('mlflow_version_registrada') is not None:
        print(f'  MLflow         «{config.MODELO_REGISTRADO}» versión {d["mlflow_version_registrada"]}')


def main(argv=None):
    ap = argparse.ArgumentParser(prog='python -m ia_mlops.produccion', description='La versión en producción: models/referencia.json')
    ap.add_argument('--ruta', help='archivo de referencia (por defecto config.REFERENCIA)')
    sub = ap.add_subparsers(dest='orden', required=True)
    sub.add_parser('mostrar', help='muestra la versión en producción')
    c = sub.add_parser('crear', help='fija el modelo entrenado (models/metadatos.json) como nueva versión en producción')
    c.add_argument('--version', type=int, required=True, help='número de versión (entero >= 1)')
    c.add_argument('--etiqueta', help='etiqueta de la imagen (por defecto retencion-api:v<N>-<huella>)')
    c.add_argument('--mlflow-version', type=int, help='versión registrada en MLflow, si se conoce')
    c.add_argument('--fuente', choices=list(config.FUENTES), help='fuente de datos con la que se entrenó (se anota en la referencia)')
    k = sub.add_parser('comparar', help='compara una versión nueva con la de producción')
    k.add_argument('--metricas', help='JSON con huella_datos y metricas_test de la candidata (por defecto, el modelo entrenado en local)')
    k.add_argument('--tolerancia', type=float, default=None, help=f'cuánto puede empeorar la métrica (por defecto {config.TOLERANCIA_COMPARACION:g})')
    k.add_argument('--json', help='guarda además la decisión (y las métricas de las dos versiones) en este archivo JSON')
    h = sub.add_parser('historial', help='deja la referencia actual como versión en producción en models/historial_versiones.json')
    h.add_argument('--retira', help='ficha (JSON) de la versión que deja de estar en producción: se añade al historial si no estaba')
    h.add_argument('--estado-retirada', choices=list(ESTADOS_HISTORIAL[1:]), default='anterior',
                   help='estado de la versión que sale: anterior (la sustituye una nueva, por defecto) o retirada (rollback)')
    t = sub.add_parser('exportar-test', help='guarda en CSV las filas de test de ml_dataset (entrada de comparar-tramos)')
    t.add_argument('--salida', required=True, help='archivo CSV de salida')
    m = sub.add_parser('comparar-tramos', help='campeón frente a candidata: cuántos clientes cambian de tramo en los mismos cortes')
    m.add_argument('--referencia', required=True, help='carpeta models/ de la versión en producción (con modelo.joblib)')
    m.add_argument('--candidata', default=None, help='carpeta models/ de la versión nueva (por defecto config.MODELOS)')
    m.add_argument('--datos', required=True, help='CSV de exportar-test (las filas de test de la candidata)')
    m.add_argument('--salida', help='guarda el resultado en este archivo JSON')
    m.add_argument('--markdown', help='guarda el resumen en este archivo Markdown (para el resumen de Actions)')
    a = ap.parse_args(argv)
    try:
        if a.orden == 'mostrar':
            _mostrar(leer_referencia(a.ruta))
            return 0
        if a.orden == 'crear':
            d = crear_referencia(leer_candidata(), a.version, a.etiqueta, mlflow_version=a.mlflow_version, fuente=a.fuente)
            ruta = escribir_referencia(d, a.ruta)
            print(f'Referencia guardada en {ruta}')
            _mostrar(d)
            return 0
        if a.orden == 'historial':
            retira = leer_referencia(a.retira) if a.retira else None
            filas = actualizar_historial(leer_referencia(a.ruta), retira, a.estado_retirada, ruta_historial(a.ruta))
            print(f'Historial guardado en {ruta_historial(a.ruta)}')
            for f in filas:
                print(f'  v{f["version"]:<3} {f["estado"]:<10} {f["etiqueta_imagen"]}')
            return 0
        if a.orden == 'exportar-test':
            print(f'Filas de test guardadas en {exportar_test(a.salida)}')
            return 0
        if a.orden == 'comparar-tramos':
            import pandas as pd
            ruta = Path(a.datos)
            if not ruta.exists():
                raise ErrorReferencia(f'No existe {ruta}. Se crea con: python -m ia_mlops.produccion exportar-test --salida {ruta}')
            r = comparar_tramos(a.referencia, a.candidata or config.MODELOS, pd.read_csv(ruta))
            md = resumen_tramos_md(r)
            print(md)
            if a.salida:
                Path(a.salida).write_text(json.dumps(r, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            if a.markdown:
                Path(a.markdown).write_text(md, encoding='utf-8')
            return 0
        if a.metricas:
            ruta = Path(a.metricas)
            if not ruta.exists():
                raise ErrorReferencia(f'No existe {ruta}.')
            nuevas = json.loads(ruta.read_text(encoding='utf-8'))
        else:
            nuevas = leer_candidata()
        ref = leer_referencia(a.ruta)
        r = comparar_con_referencia(nuevas, ref, a.tolerancia)
    except ErrorReferencia as e:
        print(f'Error: {e}', file=sys.stderr)
        return 2
    if a.json:
        Path(a.json).write_text(json.dumps({**r.como_dict(), 'version_referencia': ref['version'], 'fuente_referencia': fuente_de(ref),
                                            'huella_referencia': ref['huella_datos'], 'huella_candidata': nuevas.get('huella_datos'),
                                            'metricas_test_referencia': ref['metricas_test'],
                                            'metricas_test_candidata': nuevas.get('metricas_test')}, indent=2, ensure_ascii=False) + '\n',
                                encoding='utf-8')
    print(f'Decisión: {r.decision.upper()}')
    print(f'  {r.motivo}')
    return 1 if r.decision == 'rechazada' else 0


if __name__ == '__main__':
    sys.exit(main())
