"""Lógica del lote SIN Airflow: lo que se puede probar en cualquier ordenador, con Python y nada más.

El DAG (retencion_lote.py) solo orquesta; las decisiones están aquí para poder ensayarlas sobre la salida REAL de
`python -m ia_mlops.explotacion` sin instalar Airflow. Contenido:

  * resumir_salida()   se EJECUTA DENTRO del contenedor del lote (el DAG envía su código fuente a `python -c`): lee lo que
                       dejó explotacion en reports/campana y lo reduce a un JSON pequeño (filas, probabilidades, tramos).
                       Por eso solo usa la biblioteca estándar: la imagen de la API no tiene nada más garantizado.
  * validar_salida()   se ejecuta en el worker de Airflow: comprueba ese JSON y falla con un mensaje claro.
  * resumen_markdown() el texto final que queda en el registro de la tarea «resumir».
"""
import math
import re

# Misma regla de negocio que ia_mlops/config.py (SEGMENTOS_RECOMPRA). Una prueba comprueba que no se han separado.
TRAMOS = (('alta', 0.70), ('media', 0.40), ('baja', 0.0))

CORTE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
# Una imagen: registro/ruta:etiqueta o @sha256:…  Solo caracteres de una referencia de imagen (nada de espacios ni «;»).
IMAGEN_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._\-/:@]{2,300}$')
CAPACIDAD_RE = re.compile(r'^(0(\.\d{1,3})?|1(\.0{1,3})?)$')


class ErrorSalida(Exception):
    """La salida del lote no cumple lo que se espera. El mensaje dice qué y cuánto."""


def validar_entradas(corte, imagen, capacidad):
    """Valida lo que escribe una persona antes de que llegue a un contenedor. Devuelve (corte, imagen, capacidad) limpios."""
    corte, imagen, capacidad = (corte or '').strip(), (imagen or '').strip(), str(capacidad if capacidad is not None else '0.10').strip()
    if corte and not CORTE_RE.match(corte):
        raise ErrorSalida(f'corte no válido: «{corte}» (se espera AAAA-MM-DD o vacío)')
    if not imagen:
        raise ErrorSalida('falta la imagen del lote: indica el parámetro «imagen» (registro/ruta:etiqueta) o la variable LOTE_IMAGEN_DEFECTO')
    if not IMAGEN_RE.match(imagen):
        raise ErrorSalida(f'imagen no válida: «{imagen}»')
    if not CAPACIDAD_RE.match(capacidad) or float(capacidad) <= 0:
        raise ErrorSalida(f'capacidad no válida: «{capacidad}» (fracción entre 0 y 1, por ejemplo 0.10)')
    return corte, imagen, capacidad


def tramo_de(probabilidad):
    for nombre, desde in TRAMOS:
        if probabilidad >= desde:
            return nombre
    return TRAMOS[-1][0]


def resumir_salida(carpeta_reportes=None):
    """DENTRO DEL CONTENEDOR. Lee la última campaña de <reportes>/campana y devuelve un diccionario pequeño.

    Solo biblioteca estándar. Lo que devuelve es lo que luego comprueba validar_salida().
    """
    import csv
    import glob
    import json
    import os
    base = carpeta_reportes or os.environ.get('CURSO_REPORTES') or 'reports'
    rutas = sorted(glob.glob(os.path.join(base, 'campana', 'campana_*.json')), key=os.path.getmtime)
    if not rutas:
        raise SystemExit(f'No hay ningún campana_*.json en {base}/campana: el lote no dejó salida.')
    r = json.load(open(rutas[-1], encoding='utf-8'))
    filas = list(csv.DictReader(open(rutas[-1][:-5] + '.csv', encoding='utf-8')))
    tramos = {'alta': 0, 'media': 0, 'baja': 0}
    probs, deciles, nulos, en_campana = [], set(), 0, 0
    for f in filas:
        try:
            p = float(f['probabilidad'])
        except (TypeError, ValueError):
            nulos += 1
            continue
        if p != p:
            nulos += 1
            continue
        probs.append(p)
        tramos['alta' if p >= 0.70 else 'media' if p >= 0.40 else 'baja'] += 1
        deciles.add(int(f['decil']))
        en_campana += str(f['en_campana']).lower() == 'true'
    return {
        'corte': r['corte'], 'modelo': r['modelo'], 'huella_datos': r['huella_datos'], 'entrenado_en': r['entrenado_en'],
        'origen': r['origen'], 'capacidad': r['capacidad'], 'clientes_puntuados': r['clientes_puntuados'],
        'filas': len(filas), 'nulos': nulos, 'prob_min': min(probs) if probs else None, 'prob_max': max(probs) if probs else None,
        'prob_media': round(sum(probs) / len(probs), 4) if probs else None, 'tramos': tramos, 'deciles': sorted(deciles),
        'en_campana': en_campana, 'clientes_en_campana': r['clientes_en_campana'],
        'con_advertencias': r['clientes_con_advertencias'],
    }


def validar_salida(resumen, comprobar=None, huella_esperada=None):
    """En el WORKER. Comprueba el resumen del lote. Devuelve la lista de avisos (no graves); lanza ErrorSalida si algo falla.

    resumen          lo que devolvió resumir_salida() dentro del contenedor
    comprobar        lo que dijo la tarea «comprobar» (modelo y huella que lleva la imagen); si se da, deben coincidir
    huella_esperada  huella de datos que se exige a la imagen (parámetro opcional del DAG)
    """
    fallos, avisos = [], []
    if not isinstance(resumen, dict):
        raise ErrorSalida(f'la tarea del lote no devolvió un resumen (llegó {type(resumen).__name__}); mira el registro del contenedor')
    filas = resumen.get('filas') or 0
    if filas <= 0:
        fallos.append('el lote no puntuó a ningún cliente (0 filas)')
    if resumen.get('clientes_puntuados') != filas:
        fallos.append(f'filas del CSV ({filas}) distintas de clientes_puntuados del JSON ({resumen.get("clientes_puntuados")})')
    if resumen.get('nulos'):
        fallos.append(f'{resumen["nulos"]} probabilidades vacías o no numéricas')
    lo, hi = resumen.get('prob_min'), resumen.get('prob_max')
    if filas and (lo is None or hi is None or not (0.0 <= lo <= hi <= 1.0)):
        fallos.append(f'probabilidades fuera de [0, 1]: mínima {lo}, máxima {hi}')
    tramos = resumen.get('tramos') or {}
    if set(tramos) != {n for n, _ in TRAMOS}:
        fallos.append(f'tramos inesperados: {sorted(tramos)}')
    elif sum(tramos.values()) != filas - (resumen.get('nulos') or 0):
        fallos.append(f'los tramos suman {sum(tramos.values())} y no {filas}')
    if filas >= 10 and resumen.get('deciles') != list(range(1, 11)):
        fallos.append(f'deciles inesperados: {resumen.get("deciles")} (se esperaba 1..10)')
    esperados = max(1, math.ceil(float(resumen.get('capacidad') or 0) * filas)) if filas else 0
    if resumen.get('en_campana') != esperados:
        fallos.append(f'la campaña tiene {resumen.get("en_campana")} clientes y por la capacidad {resumen.get("capacidad")} deberían ser {esperados}')
    if comprobar:
        if comprobar.get('huella_datos') != resumen.get('huella_datos'):
            fallos.append(f'el modelo que puntuó (huella {resumen.get("huella_datos")}) no es el que declaraba la imagen en «comprobar» ({comprobar.get("huella_datos")})')
    if huella_esperada and resumen.get('huella_datos') != huella_esperada:
        fallos.append(f'la huella del modelo es {resumen.get("huella_datos")} y se exigía {huella_esperada}')
    if resumen.get('con_advertencias'):
        avisos.append(f'{resumen["con_advertencias"]} clientes con valores fuera del rango de entrenamiento (primera señal de que conviene reentrenar)')
    if fallos:
        raise ErrorSalida('; '.join(fallos))
    return avisos


def resumen_markdown(resumen, avisos=()):
    t = resumen['tramos']
    lineas = [
        f'## Lote de retención · corte {resumen["corte"]}',
        '',
        f'- Clientes puntuados: **{resumen["filas"]}** · campaña: **{resumen["en_campana"]}** (capacidad {resumen["capacidad"]})',
        f'- Probabilidad: mínima {resumen["prob_min"]:.3f} · media {resumen["prob_media"]:.3f} · máxima {resumen["prob_max"]:.3f}',
        f'- Tramos de negocio: alta {t["alta"]} · media {t["media"]} · baja {t["baja"]}',
        f'- Modelo: {resumen["modelo"]} · huella de datos `{resumen["huella_datos"]}` · entrenado {resumen["entrenado_en"]}',
        f'- Origen de las predicciones: {resumen["origen"]}',
    ]
    lineas += [f'- Aviso: {a}' for a in avisos]
    return '\n'.join(lineas)
