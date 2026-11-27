"""Deriva de DATOS y de RENDIMIENTO entre dos cortes: ¿el mundo ha cambiado desde que se entrenó el modelo?

POR QUÉ HACE FALTA
    Un modelo se entrena con el pasado y se usa en el futuro. Si los clientes de hoy ya no se parecen a los de entrenamiento
    (deriva de DATOS), o si el modelo acierta menos de lo que acertaba (deriva de RENDIMIENTO), conviene reentrenar. Esto
    no lo avisa nadie solo: hay que medirlo. Este módulo lo mide con dos órdenes y sin escribir nada en la base.

DERIVA DE DATOS: el PSI (Population Stability Index)
    Se divide cada variable en intervalos con los CUANTILES de la referencia (por defecto 10: cada intervalo contiene
    cerca del 10 % de los clientes de la referencia) y se compara qué fracción de clientes cae en cada intervalo en la
    referencia (p) y en el corte actual (q):
        PSI = suma sobre los intervalos de  (q - p) * ln(q / p)
    Es 0 si las dos muestras se reparten igual y crece cuanto más se separan. Detalles de esta implementación:
      * los valores NULOS forman su propio intervalo (que de repente falten más datos también es deriva);
      * los valores fuera del rango de la referencia caen en el primer o el último intervalo;
      * SUELO ANTI-CERO: ln(q / p) no existe si un intervalo está vacío. Las fracciones menores que 0,0001 se suben a 0,0001
        (una de cada 10 000). Es un parche numérico habitual, no una teoría: con él un intervalo vacío en un lado y lleno
        en el otro aporta mucho PSI, pero no infinito;
      * con pocos clientes (la muestra del repositorio tiene unos 150) el PSI oscila por puro azar: léelo como un aviso,
        no como una sentencia.
    UMBRALES: se suele decir «menos de 0,10 estable; entre 0,10 y 0,25 cambio moderado; más de 0,25 cambio importante».
    Es una CONVENCIÓN DE LA INDUSTRIA, no una ley: no sale de ninguna demostración. Por eso el umbral de alarma se
    puede cambiar (--umbral-psi) y esta salida lo repite cada vez.
    Además se calcula el estadístico KS de dos muestras (scipy), la mayor distancia entre las dos distribuciones
    acumuladas (0 = iguales, 1 = totalmente separadas). Si scipy no estuviera, se omite sin fallar.

DERIVA DE RENDIMIENTO: el AUC por corte
    Se puntúa con el modelo en producción (models/modelo_mlflow) a todos los clientes de cada corte y se compara con lo que
    pasó de verdad: ¿compraron en los 90 días siguientes? Esa etiqueta solo existe si el corte + 90 días cae dentro de los
    datos; si no, el corte se lista como «sin etiqueta». HONESTIDAD: el modelo ya vio los cortes de entrenamiento (y se
    eligió con los de validación), así que medir en ellos SOBREESTIMA; la salida marca qué cortes fueron de entrenamiento,
    de validación o de prueba, y avisa. El aviso de caída (0,05 por defecto, PROVISIONAL: no sale de ninguna medición) se
    compara con el primer corte con etiqueta de la lista.

Uso (desde 04-Proyecto-Base, con la base y el modelo ya creados: python -m ia_mlops.pipeline):
    python -m ia_mlops.deriva cortes [--json RUTA]
    python -m ia_mlops.deriva datos --referencia 2010-12-01 --actual 2011-12-10 [--umbral-psi 0.25] [--intervalos 10] [--json RUTA]
    python -m ia_mlops.deriva rendimiento --cortes 2011-03-01 2011-06-01 2011-09-01 [--tolerancia 0.05] [--json RUTA]
Código de salida de `datos` y `rendimiento`: 0 sin deriva relevante · 1 hay deriva (alguna variable supera el umbral / el AUC cae
más que la tolerancia) · 2 error (base o modelo que faltan, fecha mal escrita...). `cortes` devuelve 0 o 2.
Todo es SOLO LECTURA: la base se abre en modo solo lectura y no se escribe nada salvo el --json que pidas.
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from . import config, db, explotacion, produccion

UMBRAL_AVISO_PSI = 0.10      # convención de la industria: por debajo, estable
UMBRAL_PSI = 0.25            # convención de la industria: por encima, cambio importante (no es una ley)
INTERVALOS = 10
SUELO_PSI = 1e-4             # fracción mínima por intervalo para que ln(q/p) exista (ver «suelo anti-cero» arriba)
TOLERANCIA_AUC = 0.05        # PROVISIONAL: cuánto puede caer el AUC respecto al primer corte antes de avisar
_FECHA = re.compile(r'^\d{4}-\d{2}-\d{2}$')


class ErrorDeriva(RuntimeError):
    """Algo falta o está mal escrito. El mensaje dice qué hacer."""


# ----------------------------------------------------------------------------------------------------------- PSI y KS
def _como_numeros(valores):
    return pd.to_numeric(pd.Series(valores), errors='coerce').to_numpy(dtype=float)


def psi_detalle(referencia, actual, intervalos=INTERVALOS, suelo=SUELO_PSI):
    """PSI de una variable entre dos muestras, con el reparto por intervalo.

    Devuelve {'psi': float, 'intervalos': [{'intervalo', 'referencia', 'actual', 'aporte'}...]} (fracciones ya con el suelo aplicado).
    Los intervalos salen de los cuantiles de la REFERENCIA; el último es el de los valores nulos.
    """
    ref, act = _como_numeros(referencia), _como_numeros(actual)
    if len(ref) == 0 or len(act) == 0:
        raise ErrorDeriva('No hay filas en una de las dos muestras: no se puede calcular el PSI.')
    ref_ok = ref[~np.isnan(ref)]
    # puntos de corte interiores (los cuantiles 10 %, 20 %... 90 %); duplicados fuera: una variable casi constante tiene pocos intervalos
    cortes = np.unique(np.quantile(ref_ok, np.linspace(0, 1, intervalos + 1)[1:-1])) if ref_ok.size else np.array([])

    def reparto(x):
        nulos = np.isnan(x)
        cuentas = np.bincount(np.searchsorted(cortes, x[~nulos], side='left'), minlength=len(cortes) + 1)
        return np.append(cuentas, nulos.sum()) / len(x)

    p, q = np.maximum(reparto(ref), suelo), np.maximum(reparto(act), suelo)
    aportes = (q - p) * np.log(q / p)
    nombres = ([f'<= {cortes[0]:g}'] + [f'({a:g}, {b:g}]' for a, b in zip(cortes[:-1], cortes[1:])] + [f'> {cortes[-1]:g}']) if len(cortes) else ['todos']
    nombres.append('nulo')
    return {'psi': float(aportes.sum()),
            'intervalos': [{'intervalo': n, 'referencia': float(a), 'actual': float(b), 'aporte': float(c)}
                           for n, a, b, c in zip(nombres, p, q, aportes)]}


def psi(referencia, actual, intervalos=INTERVALOS, suelo=SUELO_PSI):
    """Solo el número: el PSI de una variable entre dos muestras (ver psi_detalle)."""
    return psi_detalle(referencia, actual, intervalos, suelo)['psi']


def ks(referencia, actual):
    """Estadístico KS de dos muestras (sin nulos), o None si scipy no está o falta alguna muestra. No es una dependencia nueva: scikit-learn ya la trae."""
    try:
        from scipy.stats import ks_2samp
    except ImportError:
        return None
    ref, act = _como_numeros(referencia), _como_numeros(actual)
    ref, act = ref[~np.isnan(ref)], act[~np.isnan(act)]
    if len(ref) == 0 or len(act) == 0:
        return None
    return float(ks_2samp(ref, act).statistic)


def estado_psi(valor, umbral=UMBRAL_PSI):
    """«deriva» si supera el umbral de alarma; «moderada» si supera 0,10; «estable» en otro caso."""
    if valor > umbral:
        return 'deriva'
    return 'moderada' if valor > UMBRAL_AVISO_PSI else 'estable'


# ----------------------------------------------------------------------------------------------------------- datos de un corte
def _fecha(texto, nombre='fecha'):
    if not _FECHA.match(str(texto)):
        raise ErrorDeriva(f'La {nombre} «{texto}» no tiene la forma AAAA-MM-DD (por ejemplo 2011-12-10).')
    try:
        datetime.strptime(texto, '%Y-%m-%d')
    except ValueError as e:
        raise ErrorDeriva(f'La {nombre} «{texto}» no es una fecha válida.') from e
    return texto


def cortes_guardados(con):
    """Los cortes que hay en fs_cliente_corte: [{'corte', 'clientes'}], del más antiguo al más reciente."""
    if not db.escalar(con, "SELECT COUNT(*) FROM sqlite_master WHERE name = 'fs_cliente_corte'"):
        raise ErrorDeriva('No existe la capa FS en la base: ejecuta antes  python -m ia_mlops.pipeline')
    filas = con.execute('SELECT fecha_corte, COUNT(*) FROM fs_cliente_corte GROUP BY fecha_corte ORDER BY fecha_corte').fetchall()
    return [{'corte': c, 'clientes': n} for c, n in filas]


def variables_del_corte(con, corte):
    """Las 13 variables de cada cliente en `corte`: de fs_cliente_corte si ese corte está guardado; si no, al vuelo (variables_en_corte)."""
    _fecha(corte)
    if corte in {c['corte'] for c in cortes_guardados(con)}:
        df = pd.read_sql('SELECT * FROM fs_cliente_corte WHERE fecha_corte = ? ORDER BY cliente_id', con, params=(corte,))
        origen = 'fs_cliente_corte'
    else:
        df = explotacion.variables_en_corte(con, corte)
        origen = 'calculado al vuelo'
    if df.empty:
        raise ErrorDeriva(f'Ningún cliente tiene compras antes de {corte}: no hay nada que comparar.')
    return df, origen


def _abrir():
    """La base del proyecto en SOLO LECTURA (los cálculos al vuelo usan tablas temporales, que no tocan el archivo)."""
    try:
        return db.conectar(solo_lectura=True)
    except RuntimeError as e:
        raise ErrorDeriva(str(e)) from e


# ----------------------------------------------------------------------------------------------------------- orden «cortes»
def listar_cortes(con):
    """Cortes guardados (con su partición y si tienen etiqueta a 90 días) y el corte «ahora»."""
    ahora = explotacion.corte_por_defecto(con)
    particion = {}
    if db.escalar(con, "SELECT COUNT(*) FROM sqlite_master WHERE name = 'ml_particiones'"):
        particion = dict(con.execute('SELECT fecha_corte, particion FROM ml_particiones').fetchall())
    cortes = [{**c, 'particion': particion.get(c['corte']), 'etiqueta': _hay_etiqueta(con, c['corte'], ahora)} for c in cortes_guardados(con)]
    return {'guardados': cortes, 'ahora': ahora}


def _hay_etiqueta(con, corte, ahora=None):
    """La etiqueta a 90 días existe si la ventana [corte, corte + 90 días) cabe en los datos (la última factura es la del día anterior a «ahora»)."""
    ahora = ahora or explotacion.corte_por_defecto(con)
    return db.escalar(con, "SELECT date(?, ?) <= ?", (corte, f'+{config.VENTANA_OBJETIVO_DIAS} day', ahora)) == 1


# ----------------------------------------------------------------------------------------------------------- orden «datos»
def deriva_de_datos(con, referencia, actual, umbral=UMBRAL_PSI, intervalos=INTERVALOS):
    """Compara las 13 variables entre el corte de referencia y el actual. Devuelve el resultado completo (ver el JSON de la orden `datos`)."""
    df_ref, origen_ref = variables_del_corte(con, referencia)
    df_act, origen_act = variables_del_corte(con, actual)
    variables = []
    for v in config.FEATURES:
        p = psi_detalle(df_ref[v], df_act[v], intervalos)
        variables.append({'variable': v, 'psi': p['psi'], 'ks': ks(df_ref[v], df_act[v]), 'estado': estado_psi(p['psi'], umbral),
                          'nulos_referencia': float(df_ref[v].isna().mean()), 'nulos_actual': float(df_act[v].isna().mean()),
                          'intervalos': p['intervalos']})
    variables.sort(key=lambda x: x['psi'], reverse=True)
    superan = [x['variable'] for x in variables if x['psi'] > umbral]
    return {'referencia': {'corte': referencia, 'filas': int(len(df_ref)), 'origen': origen_ref},
            'actual': {'corte': actual, 'filas': int(len(df_act)), 'origen': origen_act},
            'umbral_psi': umbral, 'umbral_aviso_psi': UMBRAL_AVISO_PSI, 'intervalos': intervalos, 'suelo': SUELO_PSI,
            'variables': variables, 'superan_umbral': superan, 'hay_deriva': bool(superan),
            'nota': 'Los umbrales de PSI (0,10 y 0,25) son una convención de la industria, no una ley.'}


def texto_datos(r):
    """La tabla legible de la orden `datos`."""
    rf, ac = r['referencia'], r['actual']
    lineas = [f'Deriva de datos: referencia {rf["corte"]} ({rf["filas"]} clientes, {rf["origen"]}) frente a actual {ac["corte"]} '
              f'({ac["filas"]} clientes, {ac["origen"]})',
              f'PSI con {r["intervalos"]} intervalos por cuantiles de la referencia (suelo {r["suelo"]:g}); umbral de alarma {r["umbral_psi"]:g}.',
              r['nota'], '', f'{"variable":<27}{"PSI":>8}{"KS":>8}  estado']
    for x in r['variables']:
        k = f'{x["ks"]:.3f}' if x['ks'] is not None else 'n/d'
        lineas.append(f'{x["variable"]:<27}{x["psi"]:>8.3f}{k:>8}  {x["estado"]}' + ('  <-- supera el umbral' if x['psi'] > r['umbral_psi'] else ''))
    lineas.append('')
    if r['hay_deriva']:
        lineas.append(f'DERIVA: {len(r["superan_umbral"])} de {len(r["variables"])} variables superan el umbral ({", ".join(r["superan_umbral"])}).')
    else:
        lineas.append('Sin deriva relevante: ninguna variable supera el umbral.')
    if min(rf['filas'], ac['filas']) < 500:
        lineas.append(f'Ojo: con {min(rf["filas"], ac["filas"])} clientes el PSI oscila por azar; es un aviso, no una sentencia.')
    return '\n'.join(lineas)


# ----------------------------------------------------------------------------------------------------------- orden «rendimiento»
def etiquetas_en_corte(con, corte):
    """Serie cliente_id -> y (1 si compró al menos una vez en los 90 días siguientes al corte). Misma regla que sql/ml/02_poblar_ml.sql."""
    compradores = {r[0] for r in con.execute(
        '''SELECT DISTINCT f.cliente_id FROM master_facturas f JOIN master_lineas l ON l.factura_id = f.factura_id
           WHERE l.es_venta_valida = 1 AND f.fecha_factura >= :c AND f.fecha_factura < date(:c, :v)''',
        {'c': corte, 'v': f'+{config.VENTANA_OBJETIVO_DIAS} day'})}
    return compradores


def uso_de_cada_corte():
    """{corte: 'entrenamiento' | 'validación' | 'prueba'} según la configuración con la que se entrenó (metadatos.json) y models/referencia.json."""
    cortes = config.CORTES
    ruta = Path(config.MODELOS) / 'metadatos.json'
    if ruta.exists():
        cortes = json.loads(ruta.read_text(encoding='utf-8')).get('cortes', cortes)
    prueba = list(cortes['test'])
    try:
        prueba = list(produccion.leer_referencia()['cortes_test'])
    except produccion.ErrorReferencia:
        pass
    uso = {c: 'entrenamiento' for c in cortes['train']}
    uso.update({c: 'validación' for c in cortes['valid']})
    uso.update({c: 'prueba' for c in prueba})
    return uso


def cargar_modelo(carpeta=None):
    """El modelo en producción: models/modelo_mlflow (el mismo que carga la API)."""
    ruta = Path(carpeta or config.MODELOS) / config.CARPETA_MODELO_MLFLOW
    if not (ruta / 'MLmodel').exists():
        raise ErrorDeriva(f'No hay modelo en {ruta}. Entrénalo antes: python -m ia_mlops.pipeline')
    import mlflow.sklearn
    return mlflow.sklearn.load_model(str(ruta))


def rendimiento_por_corte(con, cortes, modelo, tolerancia=TOLERANCIA_AUC):
    """AUC del modelo en cada corte con etiqueta. Devuelve {'cortes': [...], 'avisos': [...], 'caida_maxima', 'hay_alerta', ...}."""
    from sklearn.metrics import roc_auc_score
    ahora = explotacion.corte_por_defecto(con)
    uso = uso_de_cada_corte()
    filas, primero = [], None
    for corte in cortes:
        fila = {'corte': corte, 'uso': uso.get(_fecha(corte), 'fuera de la partición'),
                'clientes': None, 'positivos': None, 'auc': None, 'caida': None, 'motivo': None}
        if not _hay_etiqueta(con, corte, ahora):
            fila['motivo'] = f'sin etiqueta: el corte + {config.VENTANA_OBJETIVO_DIAS} días pasa de los datos (hasta {ahora})'
        else:
            df, _ = variables_del_corte(con, corte)
            compradores = etiquetas_en_corte(con, corte)
            y = df['cliente_id'].isin(compradores).astype(int)
            fila['clientes'], fila['positivos'] = int(len(df)), int(y.sum())
            if y.nunique() < 2:
                fila['motivo'] = 'todos los clientes tienen la misma etiqueta: el AUC no está definido'
            else:
                fila['auc'] = float(roc_auc_score(y, modelo.predict_proba(df[config.FEATURES].astype(float))[:, 1]))
                if primero is None:
                    primero = fila['auc']
                fila['caida'] = primero - fila['auc']
        filas.append(fila)
    medidos = [f for f in filas if f['auc'] is not None]
    if not medidos:
        raise ErrorDeriva('Ningún corte tiene etiqueta con AUC calculable: no hay nada que medir. Mira los cortes con: python -m ia_mlops.deriva cortes')
    avisos = []
    vistos = [f['corte'] for f in medidos if f['uso'] in ('entrenamiento', 'validación')]
    if vistos:
        plural = len(vistos) > 1
        avisos.append(f'{"Los cortes" if plural else "El corte"} {", ".join(vistos)} {"son" if plural else "es"} de entrenamiento o validación: '
                      f'el modelo se ajustó o se eligió con {"ellos" if plural else "él"} y el AUC ahí SOBREESTIMA. '
                      'Para una medida honesta usa cortes de prueba o posteriores al entrenamiento.')
    maxima = max(f['caida'] for f in medidos)
    alerta = maxima > tolerancia
    if alerta:
        avisos.append(f'El AUC cae {maxima:.4f} respecto al primer corte medido ({medidos[0]["corte"]}), más que la tolerancia de {tolerancia:g}. '
                      'Si ese primer corte es de entrenamiento, parte de la caída es sobreajuste y no deriva.')
    return {'cortes': filas, 'tolerancia': tolerancia, 'corte_base': medidos[0]['corte'], 'caida_maxima': float(maxima),
            'hay_alerta': bool(alerta), 'avisos': avisos,
            'nota': 'La tolerancia por defecto (0,05) es provisional: no sale de ninguna medición.'}


def texto_rendimiento(r):
    lineas = [f'AUC del modelo en producción por corte (caída = AUC del primer corte medido, {r["corte_base"]}, menos el de este corte; positiva = empeora; tolerancia {r["tolerancia"]:g}). {r["nota"]}', '',
              f'{"corte":<12}{"uso":<26}{"clientes":>9}{"positivos":>10}{"AUC":>9}{"caída":>9}']
    for f in r['cortes']:
        if f['auc'] is None:
            lineas.append(f'{f["corte"]:<12}{f["uso"]:<26}{"-":>9}{"-":>10}{"-":>9}{"-":>9}  {f["motivo"]}')
        else:
            lineas.append(f'{f["corte"]:<12}{f["uso"]:<26}{f["clientes"]:>9}{f["positivos"]:>10}{f["auc"]:>9.4f}{f["caida"]:>+9.4f}')
    lineas.append('')
    lineas += [f'AVISO: {a}' for a in r['avisos']] or ['Sin avisos.']
    lineas.append('DERIVA DE RENDIMIENTO: sí.' if r['hay_alerta'] else 'Sin deriva de rendimiento relevante.')
    return '\n'.join(lineas)


# ----------------------------------------------------------------------------------------------------------- terminal
def _guardar(ruta, d):
    Path(ruta).write_text(json.dumps(d, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def main(argv=None):
    ap = argparse.ArgumentParser(prog='python -m ia_mlops.deriva', description='Deriva de datos y de rendimiento entre cortes (solo lectura).')
    sub = ap.add_subparsers(dest='orden', required=True)
    c = sub.add_parser('cortes', help='lista los cortes guardados y el «ahora»')
    c.add_argument('--json', help='guarda además el resultado en este archivo JSON')
    d = sub.add_parser('datos', help='PSI y KS de las 13 variables entre dos cortes')
    d.add_argument('--referencia', required=True, help='corte de referencia AAAA-MM-DD (p. ej. el último de entrenamiento)')
    d.add_argument('--actual', required=True, help='corte actual AAAA-MM-DD (se calcula al vuelo)')
    d.add_argument('--umbral-psi', type=float, default=UMBRAL_PSI, help=f'PSI a partir del cual una variable «deriva» (por defecto {UMBRAL_PSI:g}, convención)')
    d.add_argument('--intervalos', type=int, default=INTERVALOS, help=f'intervalos por cuantiles (por defecto {INTERVALOS})')
    d.add_argument('--json', help='guarda además el resultado en este archivo JSON')
    r = sub.add_parser('rendimiento', help='AUC del modelo en producción en cada corte con etiqueta')
    r.add_argument('--cortes', nargs='+', required=True, help='cortes AAAA-MM-DD, del más antiguo al más reciente')
    r.add_argument('--tolerancia', type=float, default=TOLERANCIA_AUC, help=f'caída de AUC permitida respecto al primer corte (por defecto {TOLERANCIA_AUC:g}, provisional)')
    r.add_argument('--modelo', help='carpeta models/ con modelo_mlflow (por defecto config.MODELOS)')
    r.add_argument('--json', help='guarda además el resultado en este archivo JSON')
    a = ap.parse_args(argv)
    try:
        con = _abrir()
        try:
            if a.orden == 'cortes':
                res = listar_cortes(con)
                print(f'Cortes guardados en fs_cliente_corte ({len(res["guardados"])}):')
                for x in res['guardados']:
                    print(f'  {x["corte"]}  {x["clientes"]:>5} clientes  partición {x["particion"] or "-":<6} etiqueta a {config.VENTANA_OBJETIVO_DIAS} días: '
                          + ('sí' if x['etiqueta'] else 'no'))
                print(f'Corte «ahora» (día siguiente a la última factura): {res["ahora"]}')
                hay = False
            elif a.orden == 'datos':
                res = deriva_de_datos(con, _fecha(a.referencia, 'referencia'), _fecha(a.actual, 'fecha actual'), a.umbral_psi, a.intervalos)
                print(texto_datos(res))
                hay = res['hay_deriva']
            else:
                res = rendimiento_por_corte(con, a.cortes, cargar_modelo(a.modelo), a.tolerancia)
                print(texto_rendimiento(res))
                hay = res['hay_alerta']
        finally:
            con.close()
        if a.json:
            _guardar(a.json, res)
    except ErrorDeriva as e:
        print(f'Error: {e}', file=sys.stderr)
        return 2
    return 1 if hay else 0


if __name__ == '__main__':
    sys.exit(main())
