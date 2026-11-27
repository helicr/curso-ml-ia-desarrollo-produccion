"""Servidor MCP «mcp-modelo-retencion»: el modelo de retención embebido; le pasas un cliente y devuelve la predicción.

IDEA
    Un modelo es una función: variables del cliente -> probabilidad. Un MCP la publica como HERRAMIENTA para que un LLM la llame.
    El LLM no ve el modelo ni los datos: pide `predecir_cliente(12369)` y recibe un JSON con la probabilidad, el tramo y la versión.

QUÉ MODELO USA (y por qué eso es MLOps)
    No carga un archivo fijo: carga `models:/retencion-90d@champion`, es decir, «la versión que MANDA ahora» en el registro de MLflow.
    En cada llamada pregunta a qué versión apunta el alias y, si ha cambiado, recarga. Así un rollback (mover `champion` a la versión
    anterior) cambia lo que responde el MCP SIN reiniciarlo y sin tocar el código.

QUÉ PREDICE
    La probabilidad de que el cliente VUELVA A COMPRAR en los próximos 90 días. Alta = buena noticia; no es un riesgo de abandono.

HERRAMIENTAS
    predecir_cliente(cliente_id)     probabilidad con las variables del cliente en fs_produccion (las del último lote)
    predecir_variables(variables)    «¿y si...?»: la probabilidad de un cliente inventado, con sus 13 variables (o las que tengas)
    por_que(cliente_id, n)           las variables que más empujan esa probabilidad (exacto: es una regresión logística)
    modelo_en_uso()                  versión del alias, AUC con que se registró y cuántas versiones hay

ENTORNO: MCP_PROYECTO (carpeta 04-Proyecto-Base), CURSO_DB (curso.db), CURSO_MLFLOW_URI (por defecto models/mlflow.db), MCP_ALIAS (champion).
"""
import math
import os
import sqlite3
import sys
from pathlib import Path

os.environ.setdefault('MLFLOW_DISABLE_AGENT_HINT', '1')
sys.path.insert(0, os.environ['MCP_PROYECTO'])                       # para importar ia_mlops.config (variables, nombre del modelo, tramos)

import pandas as pd                                                  # noqa: E402
from mcp.server.fastmcp import FastMCP                               # noqa: E402

from ia_mlops import config                                          # noqa: E402

NOMBRE = 'mcp-modelo-retencion'
ALIAS = os.environ.get('MCP_ALIAS', 'champion')
URI = os.environ.get('CURSO_MLFLOW_URI') or 'sqlite:///' + (config.MODELOS / 'mlflow.db').as_posix()
BD = Path(os.environ.get('CURSO_DB', config.RAIZ / 'data' / 'processed' / 'curso.db'))
FEATURES = list(config.FEATURES)

servidor = FastMCP(NOMBRE, instructions=(
    'Predice si un cliente del caso Retail volverá a comprar en los próximos 90 días. La probabilidad es de VOLVER A COMPRAR: alta = buena noticia, '
    'no es un riesgo de abandono. Responde con lo que devuelvan las herramientas; si devuelven «error», díselo al usuario y no inventes cifras.'))
_cache = {'version': None, 'modelo': None, 'metricas': {}}


def _cliente_mlflow():
    import mlflow
    mlflow.set_tracking_uri(URI)
    return mlflow.MlflowClient()


def modelo_champion():
    """(modelo, versión, métricas) de lo que apunte el alias AHORA. Solo recarga si la versión cambió."""
    c = _cliente_mlflow()
    try:
        mv = c.get_model_version_by_alias(config.MODELO_REGISTRADO, ALIAS)
    except Exception as e:                                           # noqa: BLE001 - MLflow lanza varios tipos
        raise LookupError(f'«{config.MODELO_REGISTRADO}» no tiene el alias @{ALIAS}: asígnalo (python -m ia_mlops.alias_modelo promover --version N)') from e
    version = int(mv.version)
    if _cache['version'] != version:
        import mlflow.sklearn
        _cache.update(version=version, modelo=mlflow.sklearn.load_model(f'models:/{config.MODELO_REGISTRADO}/{version}'),
                      metricas=c.get_run(mv.run_id).data.metrics if mv.run_id else {})
    return _cache['modelo'], version, _cache['metricas']


def tramo_de(p):
    for s in config.SEGMENTOS_RECOMPRA:                              # regla de negocio, no del modelo: se acuerda con quien hace la campaña
        if p >= s['desde']:
            return s['segmento'], s['recomendacion']


def _variables_de(cliente_id):
    """Las 13 variables del cliente en fs_produccion (último corte). Solo lectura."""
    con = sqlite3.connect(BD.resolve().as_uri() + '?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    try:
        f = con.execute('SELECT * FROM fs_produccion WHERE cliente_id = ? ORDER BY fecha_corte DESC LIMIT 1', (cliente_id,)).fetchone()
    finally:
        con.close()
    return None if f is None else dict(f)


def _puntuar(variables):
    modelo, version, metricas = modelo_champion()
    X = pd.DataFrame([{c: (float('nan') if variables.get(c) is None else float(variables[c])) for c in FEATURES}])
    p = float(modelo.predict_proba(X)[:, 1][0])
    tramo, recomendacion = tramo_de(p)
    return p, tramo, recomendacion, version, modelo


def _cid(valor):
    try:
        return int(valor), None
    except (TypeError, ValueError):
        return None, {'error': f'«cliente_id» debe ser un número entero, no «{valor}».'}


@servidor.tool(name='predecir_cliente', description=(
    'Probabilidad de que UN cliente vuelva a comprar en los próximos 90 días, con sus variables del último lote (fs_produccion), el tramo '
    '(alta/media/baja) y la recomendación de negocio. Úsala cuando pregunten por un cliente concreto. Argumento: cliente_id (número).'))
def predecir_cliente(cliente_id: int) -> dict:
    cid, error = _cid(cliente_id)
    if error:
        return error
    fila = _variables_de(cid)
    if fila is None:
        return {'error': f'El cliente {cid} no está en fs_produccion: no hay variables con las que puntuarlo.'}
    try:
        p, tramo, recomendacion, version, _ = _puntuar(fila)
    except LookupError as e:
        return {'error': str(e)}
    return {'cliente_id': cid, 'probabilidad': round(p, 4), 'tramo': tramo, 'recomendacion': recomendacion, 'version_modelo': version,
            'alias': ALIAS, 'corte_de_las_variables': fila['fecha_corte'], 'variables': {c: fila[c] for c in FEATURES}}


@servidor.tool(name='predecir_variables', description=(
    'Probabilidad de volver a comprar para un cliente HIPOTÉTICO, a partir de sus variables: «¿y si compró 3 veces más?». '
    f'Argumento: variables (objeto con {len(FEATURES)} números: {", ".join(FEATURES)}). Si falta alguna, el modelo usa la mediana de entrenamiento y se avisa.'))
def predecir_variables(variables: dict) -> dict:
    if not isinstance(variables, dict) or not variables:
        return {'error': f'Pasa un objeto con las variables: {", ".join(FEATURES)}.'}
    desconocidas = sorted(set(variables) - set(FEATURES))
    if desconocidas:
        return {'error': f'Variables que el modelo no conoce: {desconocidas}. Las válidas: {FEATURES}.'}
    for k, v in variables.items():
        if v is not None and (isinstance(v, bool) or not isinstance(v, (int, float))):
            return {'error': f'«{k}» debe ser un número, no «{v}».'}
        if isinstance(v, float) and not math.isfinite(v):
            return {'error': f'«{k}» no es un número finito.'}
    faltan = [c for c in FEATURES if variables.get(c) is None]
    try:
        p, tramo, recomendacion, version, _ = _puntuar(variables)
    except LookupError as e:
        return {'error': str(e)}
    r = {'probabilidad': round(p, 4), 'tramo': tramo, 'recomendacion': recomendacion, 'version_modelo': version, 'alias': ALIAS}
    if faltan:
        r['aviso'] = f'Faltaban {faltan}: el modelo las imputó con la mediana del entrenamiento.'
    return r


def _pesos(modelo, fila):
    """Regresión logística dentro de un Pipeline: logit = intercepto + Σ coeficiente × valor transformado. Exacto. None si no es de ese tipo."""
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    if not isinstance(modelo, Pipeline) or not isinstance(modelo.steps[-1][1], LogisticRegression):
        return None
    logistica = modelo.steps[-1][1]
    X = pd.DataFrame([{c: (float('nan') if fila.get(c) is None else float(fila[c])) for c in FEATURES}])
    Z = np.asarray(modelo[:-1].transform(X), dtype='float64')[0]
    pesos = logistica.coef_[0] * Z
    logit = float(logistica.intercept_[0]) + float(pesos.sum())
    return {'pesos': pesos, 'intercepto': float(logistica.intercept_[0]), 'logit': logit, 'probabilidad': 1.0 / (1.0 + math.exp(-logit))}


@servidor.tool(name='por_que', description=(
    'Las variables que más empujan la probabilidad de UN cliente, hacia arriba o hacia abajo. Úsala cuando pregunten por qué sale alto o bajo. '
    'Argumentos: cliente_id (número) y n (cuántas variables, por defecto 5).'))
def por_que(cliente_id: int, n: int = 5) -> dict:
    cid, error = _cid(cliente_id)
    if error:
        return error
    fila = _variables_de(cid)
    if fila is None:
        return {'error': f'El cliente {cid} no está en fs_produccion.'}
    try:
        p, tramo, _, version, modelo = _puntuar(fila)
    except LookupError as e:
        return {'error': str(e)}
    d = _pesos(modelo, fila)
    if d is None:
        return {'cliente_id': cid, 'probabilidad': round(p, 4), 'version_modelo': version,
                'nota': 'El modelo no es una regresión logística: no se puede repartir la probabilidad por variable de forma exacta.'}
    if abs(d['probabilidad'] - p) > 1e-6:
        return {'cliente_id': cid, 'probabilidad': round(p, 4), 'version_modelo': version, 'nota': 'La descomposición no reproduce la probabilidad: no se devuelven pesos.'}
    filas = sorted(({'variable': c, 'valor': fila[c], 'peso_logit': round(float(w), 4), 'efecto': 'sube' if w > 0 else 'baja' if w < 0 else 'neutro'}
                    for c, w in zip(FEATURES, d['pesos'])), key=lambda f: (-abs(f['peso_logit']), f['variable']))
    return {'cliente_id': cid, 'probabilidad': round(p, 4), 'tramo': tramo, 'version_modelo': version, 'intercepto_logit': round(d['intercepto'], 4),
            'logit_total': round(d['logit'], 4), 'variables_que_mas_pesan': filas[:max(1, min(int(n), len(FEATURES)))],
            'nota': 'Intercepto + suma de los pesos = logit; probabilidad = 1/(1+e^-logit). Dice qué empuja la cifra, no por qué compra el cliente.'}


@servidor.tool(name='modelo_en_uso', description='Qué versión del modelo responde ahora (a la que apunta el alias), con su AUC de validación y test y cuántas versiones hay. No necesita argumentos.')
def modelo_en_uso() -> dict:
    try:
        _, version, metricas = modelo_champion()
    except LookupError as e:
        return {'error': str(e)}
    versiones = len(_cliente_mlflow().search_model_versions(f"name='{config.MODELO_REGISTRADO}'"))
    return {'modelo': config.MODELO_REGISTRADO, 'alias': ALIAS, 'version': version, 'versiones_registradas': versiones,
            'valid_auc': metricas.get('valid_auc'), 'test_auc': metricas.get('test_auc')}


def main():
    print(f'{NOMBRE}: alias @{ALIAS} en {URI}', file=sys.stderr)      # por stderr: stdout es el canal del protocolo
    servidor.run(transport='stdio')


if __name__ == '__main__':
    main()
