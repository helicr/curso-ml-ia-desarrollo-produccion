"""El alias `champion` del modelo de retención en el registro de MLflow: promover una versión y volver atrás (rollback).

IDEA
    Cada entrenamiento registra una VERSIÓN nueva de «retencion-90d» (1, 2, 3...). Un ALIAS es un puntero con nombre a
    una versión: `champion` = «la versión que manda». Cambiar de versión es mover el puntero; deshacer es volver a moverlo.
    NO SE BORRA NADA: las versiones siguen ahí, con sus métricas y su modelo.

    Para poder volver, `promover` anota en la versión que pasa a ser champion una etiqueta (tag) `champion_anterior` con
    el número de la versión que lo era antes. `volver` lee esa etiqueta y mueve el puntero allí. Con varias promociones
    seguidas queda una cadena: v3 recuerda a v2, v2 recuerda a v1.

NOTA HONESTA: LO QUE ESTE ALIAS GOBIERNA Y LO QUE NO
    La imagen Docker de la API copia `models/modelo_mlflow` al construirse y NO lee este registro: mover `champion`
    gobierna el registro y a cualquier cliente que cargue `models:/retencion-90d@champion`, pero no cambia por sí solo
    lo que responde la API ya desplegada. Un sistema real lo uniría así: (1) al mover el alias, un paso del workflow
    exporta esa versión a `models/modelo_mlflow`; (2) construye y publica la imagen con ese modelo (etiqueta con la
    versión); (3) despliega la imagen, o hace que la API cargue por alias al arrancar. Aquí no se implementa.

CLI (desde 04-Proyecto-Base):
    python -m ia_mlops.alias_modelo mostrar [--json RUTA]               # versiones, AUC y a qué apunta cada alias
    python -m ia_mlops.alias_modelo promover --version 2                # `champion` pasa a la versión 2 (recuerda la anterior)
    python -m ia_mlops.alias_modelo volver                              # rollback: `champion` vuelve a la versión anterior
    python -m ia_mlops.alias_modelo cargar --alias champion             # carga models:/retencion-90d@champion y puntúa un cliente de ejemplo
    python -m ia_mlops.alias_modelo cargar --cliente otro.json          # (--json RUTA también guarda el resultado)
Opción común: --uri (por defecto CURSO_MLFLOW_URI o models/mlflow.db). Código de salida: 0 bien · 2 error (versión inexistente,
no hay versión anterior, registro vacío...).
"""
import argparse
import json
import os
import sys
from pathlib import Path

os.environ.setdefault('MLFLOW_DISABLE_AGENT_HINT', '1')

from . import config  # noqa: E402

ALIAS = 'champion'
ETIQUETA_ANTERIOR = 'champion_anterior'
CLIENTE_EJEMPLO = config.RAIZ / 'tests' / 'datos' / 'cliente_ejemplo.json'


class ErrorAlias(RuntimeError):
    """El registro no tiene lo que se pide. El mensaje dice qué hacer."""


# ------------------------------------------------------------------------------------------------ conexión
def uri_por_defecto():
    return os.environ.get('CURSO_MLFLOW_URI') or 'sqlite:///' + (config.MODELOS / 'mlflow.db').as_posix()


def conectar(uri=None):
    """Apunta MLflow al almacén del curso (o al indicado), devuelve (URI, cliente)."""
    import mlflow
    uri = uri or uri_por_defecto()
    mlflow.set_tracking_uri(uri)
    return uri, mlflow.MlflowClient()


def _alias_de(cliente, nombre):
    """{alias: versión (int)} del modelo registrado; ErrorAlias si el modelo no está registrado."""
    try:
        return {a: int(v) for a, v in (cliente.get_registered_model(nombre).aliases or {}).items()}
    except Exception as e:                                                  # noqa: BLE001 - MLflow lanza varios tipos
        raise ErrorAlias(f'«{nombre}» no está en el registro: entrena antes con python -m ia_mlops.pipeline ({e})') from e


def _version(cliente, nombre, version):
    try:
        return cliente.get_model_version(nombre, str(int(version)))
    except Exception as e:                                                  # noqa: BLE001
        raise ErrorAlias(f'No existe la versión {version} de «{nombre}»: mira cuáles hay con  python -m ia_mlops.alias_modelo mostrar') from e


# ------------------------------------------------------------------------------------------------ mostrar
def estado(cliente, nombre=None):
    """Versiones del modelo con sus métricas y alias: {'nombre', 'alias': {alias: versión}, 'versiones': [...]}."""
    nombre = nombre or config.MODELO_REGISTRADO
    alias = _alias_de(cliente, nombre)
    versiones = []
    for v in cliente.search_model_versions(f"name='{nombre}'"):
        metricas = cliente.get_run(v.run_id).data.metrics if v.run_id else {}
        versiones.append({'version': int(v.version), 'alias': sorted(a for a, n in alias.items() if n == int(v.version)),
                          'valid_auc': metricas.get('valid_auc'), 'test_auc': metricas.get('test_auc'),
                          'champion_anterior': (v.tags or {}).get(ETIQUETA_ANTERIOR), 'huella_datos': (v.tags or {}).get('huella_datos'),
                          'run_id': v.run_id})
    return {'nombre': nombre, 'alias': alias, 'versiones': sorted(versiones, key=lambda x: x['version'])}


def texto_estado(e):
    lineas = [f'Modelo registrado «{e["nombre"]}»: {len(e["versiones"])} versiones']
    for v in e['versiones']:
        auc = ' · '.join(f'{k} {v[k]:.4f}' for k in ('valid_auc', 'test_auc') if v[k] is not None) or 'sin métricas'
        extra = f'  (champion anterior: v{v["champion_anterior"]})' if v['champion_anterior'] else ''
        lineas.append(f'  v{v["version"]:<3} alias: {", ".join("@" + a for a in v["alias"]) or "-":<12} {auc}{extra}')
    lineas.append('Alias: ' + (', '.join(f'@{a} -> v{n}' for a, n in sorted(e['alias'].items())) or 'ninguno'))
    return '\n'.join(lineas)


# ------------------------------------------------------------------------------------------------ promover y volver
def promover(cliente, version, nombre=None, alias=ALIAS):
    """Pone `alias` (champion) en `version` y guarda en esa versión la etiqueta de cuál era champion antes. Devuelve un resumen.

    Si `version` ya es champion no hace nada (no pisa la etiqueta, para no perder la cadena de vuelta atrás).
    """
    nombre = nombre or config.MODELO_REGISTRADO
    version = int(version)
    _version(cliente, nombre, version)                                      # error claro si no existe
    anterior = _alias_de(cliente, nombre).get(alias)
    if anterior == version:
        return {'nombre': nombre, 'alias': alias, 'version': version, 'anterior': None, 'cambio': False}
    if anterior is not None:
        cliente.set_model_version_tag(nombre, str(version), ETIQUETA_ANTERIOR, str(anterior))
    cliente.set_registered_model_alias(nombre, alias, str(version))
    return {'nombre': nombre, 'alias': alias, 'version': version, 'anterior': anterior, 'cambio': True}


def volver(cliente, nombre=None, alias=ALIAS):
    """Rollback: mueve `alias` a la versión anterior que anotó `promover`. No borra nada; la versión que sale sigue registrada."""
    nombre = nombre or config.MODELO_REGISTRADO
    actual = _alias_de(cliente, nombre).get(alias)
    if actual is None:
        raise ErrorAlias(f'«{nombre}» no tiene el alias @{alias}: no hay a qué volver. Promueve una versión con  promover --version N')
    anterior = (_version(cliente, nombre, actual).tags or {}).get(ETIQUETA_ANTERIOR)
    if not anterior:
        raise ErrorAlias(f'La versión {actual}, que es @{alias}, no guardó una versión anterior: no hay a dónde volver. '
                         f'Si sabes cuál quieres, usa  promover --version N')
    _version(cliente, nombre, anterior)                                     # por si alguien borró esa versión a mano
    cliente.set_registered_model_alias(nombre, alias, str(int(anterior)))
    return {'nombre': nombre, 'alias': alias, 'version': int(anterior), 'retirada': actual}


# ------------------------------------------------------------------------------------------------ cargar por alias
def cargar_y_puntuar(cliente, ejemplo, nombre=None, alias=ALIAS):
    """Carga `models:/<nombre>@<alias>` y puntúa el cliente `ejemplo` (dict con las 13 variables). Devuelve versión y probabilidad."""
    import mlflow.sklearn
    import pandas as pd
    nombre = nombre or config.MODELO_REGISTRADO
    try:
        version = int(cliente.get_model_version_by_alias(nombre, alias).version)
    except Exception as e:                                                  # noqa: BLE001
        raise ErrorAlias(f'«{nombre}» no tiene el alias @{alias}: asígnalo con  promover --version N') from e
    modelo = mlflow.sklearn.load_model(f'models:/{nombre}@{alias}')       # el alias decide QUÉ modelo se carga
    faltan = [c for c in config.FEATURES if c not in ejemplo]
    if faltan:
        raise ErrorAlias(f'Al cliente de ejemplo le faltan variables: {faltan}')
    prob = float(modelo.predict_proba(pd.DataFrame([{c: float(ejemplo[c]) for c in config.FEATURES}]))[:, 1][0])
    return {'nombre': nombre, 'alias': alias, 'uri': f'models:/{nombre}@{alias}', 'version': version, 'probabilidad': prob}


# ------------------------------------------------------------------------------------------------ CLI
def main(argv=None):
    ap = argparse.ArgumentParser(prog='python -m ia_mlops.alias_modelo', description=f'Alias @{ALIAS} del modelo «{config.MODELO_REGISTRADO}» en MLflow')
    ap.add_argument('--uri', help='almacén de MLflow (por defecto CURSO_MLFLOW_URI o models/mlflow.db)')
    sub = ap.add_subparsers(dest='orden', required=True)
    m = sub.add_parser('mostrar', help='versiones, AUC y a qué versión apunta cada alias')
    p = sub.add_parser('promover', help=f'pone @{ALIAS} en una versión y anota cuál era la anterior')
    p.add_argument('--version', type=int, required=True)
    v = sub.add_parser('volver', help=f'rollback: @{ALIAS} vuelve a la versión anterior')
    c = sub.add_parser('cargar', help='carga el modelo por alias y puntúa un cliente de ejemplo')
    c.add_argument('--alias', default=ALIAS)
    c.add_argument('--cliente', default=str(CLIENTE_EJEMPLO), help='JSON con las 13 variables de un cliente (por defecto tests/datos/cliente_ejemplo.json)')
    for s in (m, p, v, c):
        s.add_argument('--json', help='guarda además el resultado en este archivo JSON')
    a = ap.parse_args(argv)
    try:
        uri, cliente = conectar(a.uri)
        print(f'Almacén de MLflow: {uri}')
        if a.orden == 'mostrar':
            res = estado(cliente)
            print(texto_estado(res))
        elif a.orden == 'promover':
            res = promover(cliente, a.version)
            if not res['cambio']:
                print(f'Sin cambios: @{res["alias"]} ya apunta a la versión {res["version"]}.')
            elif res['anterior'] is None:
                print(f'@{res["alias"]} -> v{res["version"]} (no había champion anterior: no se guardó a dónde volver).')
            else:
                print(f'@{res["alias"]}: v{res["anterior"]} -> v{res["version"]}. La v{res["version"]} recuerda a la v{res["anterior"]}: '
                      'para volver, `volver`. No se ha borrado nada.')
        elif a.orden == 'volver':
            res = volver(cliente)
            print(f'Rollback: @{res["alias"]}: v{res["retirada"]} -> v{res["version"]}. La v{res["retirada"]} sigue registrada; no se ha borrado nada.')
        else:
            ruta = Path(a.cliente)
            if not ruta.exists():
                raise ErrorAlias(f'No existe {ruta}.')
            res = cargar_y_puntuar(cliente, json.loads(ruta.read_text(encoding='utf-8')), alias=a.alias)
            print(f'Cargado {res["uri"]} -> versión {res["version"]}')
            print(f'Probabilidad de comprar en {config.VENTANA_OBJETIVO_DIAS} días del cliente de {ruta.name}: {res["probabilidad"]:.4f}')
        if a.json:
            Path(a.json).write_text(json.dumps(res, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        return 0
    except ErrorAlias as e:
        print(f'Error: {e}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
