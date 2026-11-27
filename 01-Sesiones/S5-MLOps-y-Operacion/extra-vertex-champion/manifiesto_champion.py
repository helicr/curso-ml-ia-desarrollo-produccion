"""Manifiesto del champion: el enlace MLflow <-> Vertex AI en las DOS direcciones.

IDA (MLflow -> Vertex)       generar
    Lee el registro de MLflow: a qué versión apunta el alias `champion`, su run_id, el AUC de validación y de prueba, la huella de
    los datos y la versión que era champion antes. Escribe `vertex-manifiesto.json` y las ETIQUETAS (labels) que se pondrán al
    modelo en el Model Registry de Vertex (`--labels`), para que desde la consola de Google se sepa de qué versión de MLflow viene.
VUELTA (Vertex -> MLflow)    anotar
    Tras desplegar, escribe en la versión de MLflow las etiquetas `vertex_model_version`, `vertex_endpoint`... para que desde
    MLflow se sepa dónde está desplegada. Con un registro local de MLflow (el del curso) esas etiquetas viven en TU registro.
LEER                         leer
    Imprime un campo del manifiesto (lo usan los scripts de Cloud Shell y los workflows en lugar de `jq`).

Reglas de las etiquetas de Google Cloud (https://docs.cloud.google.com/resource-manager/docs/labels-overview): hasta 64 por recurso;
clave de 1 a 63 caracteres que empieza por letra minúscula; valor de 0 a 63; solo minúsculas, números, guion bajo y guion.
Por eso el AUC 0.6982 se escribe `0_6982` y todo se pasa a minúsculas. (La referencia de `gcloud ai models upload --labels` dice
«64 caracteres»; se aplica el límite menor, 63, que es el seguro.)

CLI (desde esta carpeta; la carpeta del proyecto se busca en ../../../04-Proyecto-Base o en CURSO_DIR_PROYECTO):
    python manifiesto_champion.py generar [--uri URI] [--alias champion] [--version N] [--salida vertex-manifiesto.json] [--simular]
    python manifiesto_champion.py anotar  --manifiesto vertex-manifiesto.json --vertex-version 3 --endpoint ID [--deployed-model-id ID]
                                          [--region R] [--vertex-modelo ID] [--uri URI] [--simular]
    python manifiesto_champion.py puerta  --manifiesto vertex-manifiesto.json [--auc-minimo 0.65]   (sale con 2 si no debe publicarse)
    python manifiesto_champion.py leer    --manifiesto vertex-manifiesto.json CAMPO        (CAMPO puede ser a.b)
Código de salida: 0 bien · 2 error (sin alias, versión inexistente, manifiesto ausente...).
`--simular` NO abre MLflow: usa unos datos de ejemplo (los de la versión 6 del registro del curso) y marca `"simulado": true`.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PROYECTO = Path(os.environ.get('CURSO_DIR_PROYECTO') or AQUI.parents[2] / '04-Proyecto-Base')
if str(PROYECTO) not in sys.path:
    sys.path.insert(0, str(PROYECTO))

NOMBRE_MANIFIESTO = 'vertex-manifiesto.json'
ESQUEMA = 1
MAX_ETIQUETAS = 64
MAX_LONGITUD = 63
ETIQUETAS_VERTEX_MLFLOW = ('vertex_model_version', 'vertex_endpoint', 'vertex_deployed_model_id', 'vertex_region', 'vertex_modelo')
SIMULADO = {                                    # lo que hay en el registro del curso (copia de ensayo del 27/11/2026): v6 champion, v5 anterior
    'mlflow_version': 6, 'run_id': 'ddd3b315513e4a3b9b79ae3e80cf1cb7', 'valid_auc': 0.6982009925558312, 'test_auc': 0.747092830088378,
    'huella_datos': '35a94deb4e04ab4a', 'version_anterior': 5,
}


class ErrorManifiesto(RuntimeError):
    """Lo que se pide no está en el registro o en el manifiesto. El mensaje dice qué hacer."""


# ------------------------------------------------------------------------------------------------ etiquetas de Google Cloud
def sanear(texto):
    """Pasa un texto a lo que admite una etiqueta de GCP: minúsculas, números, `_` y `-`; máximo 63 caracteres."""
    t = re.sub(r'[^a-z0-9_-]', '_', str(texto).lower())
    return t[:MAX_LONGITUD]


def numero_a_etiqueta(x, decimales=4):
    """0.6982009 -> '0_6982' (el punto no es válido en una etiqueta)."""
    return sanear(f'{float(x):.{decimales}f}'.replace('.', '_'))


def etiqueta_valida(clave, valor):
    """True si (clave, valor) cumple las reglas de etiquetas de Google Cloud."""
    return bool(re.fullmatch(r'[a-z][a-z0-9_-]{0,62}', clave)) and bool(re.fullmatch(r'[a-z0-9_-]{0,63}', valor))


def etiquetas_vertex(m):
    """Etiquetas para el modelo de Vertex a partir de los datos del manifiesto (solo las que tienen valor)."""
    candidatas = {
        'curso': 'ml-ia', 'mlflow_modelo': m['modelo'], 'mlflow_alias': m['alias'], 'mlflow_version': m['mlflow_version'],
        'mlflow_run': m.get('run_id'), 'huella_datos': m.get('huella_datos'),
        'auc_valid': None if m.get('valid_auc') is None else numero_a_etiqueta(m['valid_auc']),
        'auc_test': None if m.get('test_auc') is None else numero_a_etiqueta(m['test_auc']),
        'mlflow_version_anterior': m.get('version_anterior'),
    }
    et = {k: sanear(v) for k, v in candidatas.items() if v not in (None, '')}
    malas = [k for k, v in et.items() if not etiqueta_valida(k, v)]
    if malas or len(et) > MAX_ETIQUETAS:
        raise ErrorManifiesto(f'Etiquetas no válidas para Google Cloud: {malas}')
    return et


def etiquetas_a_gcloud(et):
    """{'a': '1', 'b': '2'} -> 'a=1,b=2' (el formato de --labels)."""
    return ','.join(f'{k}={v}' for k, v in et.items())


# ------------------------------------------------------------------------------------------------ manifiesto
def construir(datos, nombre, alias, simulado=False):
    """Manifiesto a partir de los datos leídos de MLflow (o simulados)."""
    from ia_mlops import config
    huella = datos.get('huella_datos')
    version = int(datos['mlflow_version'])
    m = {
        'esquema': ESQUEMA, 'simulado': bool(simulado), 'modelo': nombre, 'alias': alias, 'mlflow_version': version,
        'run_id': datos.get('run_id'), 'valid_auc': datos.get('valid_auc'), 'test_auc': datos.get('test_auc'),
        'huella_datos': huella, 'version_anterior': None if datos.get('version_anterior') in (None, '') else int(datos['version_anterior']),
        'variables': list(config.FEATURES),
        'etiqueta_imagen': f'v{version}-{huella}' if huella else f'v{version}',
        'alias_vertex': f'mlflow-v{version}',
    }
    m['etiquetas'] = etiquetas_vertex(m)
    m['etiquetas_gcloud'] = etiquetas_a_gcloud(m['etiquetas'])
    return m


def leer_de_mlflow(cliente, nombre, alias, version=None):
    """Datos de la versión (la del alias, o la indicada) desde el registro de MLflow."""
    from ia_mlops import alias_modelo
    try:
        alias_a_version = alias_modelo._alias_de(cliente, nombre)
    except alias_modelo.ErrorAlias as e:
        raise ErrorManifiesto(str(e)) from e
    if version is None:
        if alias not in alias_a_version:
            raise ErrorManifiesto(f'«{nombre}» no tiene el alias @{alias}: promueve una versión con  python -m ia_mlops.alias_modelo promover --version N')
        version = alias_a_version[alias]
    try:
        v = alias_modelo._version(cliente, nombre, version)
    except alias_modelo.ErrorAlias as e:
        raise ErrorManifiesto(str(e)) from e
    metricas = cliente.get_run(v.run_id).data.metrics if v.run_id else {}
    tags = v.tags or {}
    return {'mlflow_version': int(v.version), 'run_id': v.run_id, 'valid_auc': metricas.get('valid_auc'), 'test_auc': metricas.get('test_auc'),
            'huella_datos': tags.get('huella_datos'), 'version_anterior': tags.get(alias_modelo.ETIQUETA_ANTERIOR)}


def generar(uri=None, alias=None, version=None, simular=False):
    from ia_mlops import alias_modelo, config
    alias = alias or alias_modelo.ALIAS
    nombre = config.MODELO_REGISTRADO
    if simular:
        return construir(SIMULADO, nombre, alias, simulado=True)
    _, cliente = alias_modelo.conectar(uri)
    return construir(leer_de_mlflow(cliente, nombre, alias, version), nombre, alias)


def anotar(manifiesto, vertex_version, endpoint, deployed_model_id=None, region=None, uri=None, simular=False, vertex_modelo=None):
    """Escribe en la versión de MLflow dónde está en Vertex. Devuelve las etiquetas escritas (o que se escribirían con --simular)."""
    from ia_mlops import alias_modelo
    etiquetas = {'vertex_modelo': vertex_modelo or manifiesto['modelo'], 'vertex_model_version': str(vertex_version),
                 'vertex_endpoint': str(endpoint)}
    if deployed_model_id:
        etiquetas['vertex_deployed_model_id'] = str(deployed_model_id)
    if region:
        etiquetas['vertex_region'] = str(region)
    if simular:
        return etiquetas
    _, cliente = alias_modelo.conectar(uri)
    nombre, version = manifiesto['modelo'], manifiesto['mlflow_version']
    try:
        alias_modelo._version(cliente, nombre, version)
    except alias_modelo.ErrorAlias as e:
        raise ErrorManifiesto(str(e)) from e
    for k, v in etiquetas.items():
        cliente.set_model_version_tag(nombre, str(version), k, v)
    return etiquetas


AUC_MINIMO = 0.65         # PROVISIONAL: no sale de ninguna medición; con 114 y 250 clientes de valid y test el AUC oscila más que eso por azar. Se acuerda con negocio.


def puerta(m, auc_minimo=AUC_MINIMO):
    """Puerta de calidad ANTES de publicar: lista de motivos por los que el champion NO debe ir a Vertex (vacía = puede ir)."""
    fallos = []
    for k in ('valid_auc', 'test_auc'):
        if m.get(k) is None:
            fallos.append(f'{k} no está en el registro de MLflow.')
        elif m[k] < auc_minimo:
            fallos.append(f'{k} = {m[k]:.4f} es menor que el mínimo {auc_minimo:g}.')
    if not m.get('huella_datos'):
        fallos.append('La versión no tiene huella de los datos (etiqueta huella_datos): no se sabe con qué datos se entrenó.')
    if m.get('simulado'):
        fallos.append('El manifiesto es SIMULADO: no se publica.')
    return fallos


def cargar(ruta):
    ruta = Path(ruta)
    if not ruta.exists():
        raise ErrorManifiesto(f'No existe {ruta}: genéralo con  python manifiesto_champion.py generar')
    return json.loads(ruta.read_text(encoding='utf-8'))


def campo(manifiesto, ruta):
    """manifiesto['a']['b'] a partir de 'a.b'; ErrorManifiesto si no está."""
    valor = manifiesto
    for p in ruta.split('.'):
        if not isinstance(valor, dict) or p not in valor:
            raise ErrorManifiesto(f'El manifiesto no tiene el campo «{ruta}».')
        valor = valor[p]
    return valor


# ------------------------------------------------------------------------------------------------ CLI
def main(argv=None):
    ap = argparse.ArgumentParser(prog='python manifiesto_champion.py', description='Manifiesto del champion de MLflow para Vertex AI')
    sub = ap.add_subparsers(dest='orden', required=True)
    g = sub.add_parser('generar', help='lee el registro de MLflow y escribe vertex-manifiesto.json y las etiquetas')
    g.add_argument('--uri', help='almacén de MLflow (por defecto CURSO_MLFLOW_URI o models/mlflow.db)')
    g.add_argument('--alias', default='champion')
    g.add_argument('--version', type=int, help='una versión concreta en lugar de la del alias')
    g.add_argument('--salida', default=NOMBRE_MANIFIESTO)
    g.add_argument('--simular', action='store_true', help='no abre MLflow: usa datos de ejemplo y marca simulado=true')
    a = sub.add_parser('anotar', help='escribe en la versión de MLflow dónde está desplegada en Vertex')
    a.add_argument('--manifiesto', default=NOMBRE_MANIFIESTO)
    a.add_argument('--vertex-version', required=True)
    a.add_argument('--endpoint', required=True)
    a.add_argument('--deployed-model-id')
    a.add_argument('--region')
    a.add_argument('--vertex-modelo', help='ID del modelo en el Model Registry de Vertex (por defecto el nombre del modelo de MLflow)')
    a.add_argument('--uri')
    a.add_argument('--simular', action='store_true', help='no escribe en MLflow: solo enseña las etiquetas que escribiría')
    pu = sub.add_parser('puerta', help='puerta de calidad: sale con 2 si el champion no debe publicarse')
    pu.add_argument('--manifiesto', default=NOMBRE_MANIFIESTO)
    pu.add_argument('--auc-minimo', type=float, default=AUC_MINIMO)
    le = sub.add_parser('leer', help='imprime un campo del manifiesto')
    le.add_argument('--manifiesto', default=NOMBRE_MANIFIESTO)
    le.add_argument('campo')
    p = ap.parse_args(argv)
    try:
        if p.orden == 'generar':
            m = generar(p.uri, p.alias, p.version, p.simular)
            Path(p.salida).write_text(json.dumps(m, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            print(f'{"SIMULADO: " if m["simulado"] else ""}«{m["modelo"]}» @{m["alias"]} -> versión {m["mlflow_version"]} de MLflow'
                  f' (anterior: {m["version_anterior"] if m["version_anterior"] is not None else "ninguna"})')
            print(f'  AUC valid {m["valid_auc"]:.4f} · test {m["test_auc"]:.4f} · huella de datos {m["huella_datos"]}')
            print(f'  imagen: <registro>/retencion-vertex:{m["etiqueta_imagen"]}   alias en Vertex: {m["alias_vertex"]}')
            print(f'  etiquetas de Vertex: {m["etiquetas_gcloud"]}')
            print(f'Escrito {p.salida}')
        elif p.orden == 'anotar':
            m = cargar(p.manifiesto)
            et = anotar(m, p.vertex_version, p.endpoint, p.deployed_model_id, p.region, p.uri, p.simular, p.vertex_modelo)
            print(('SIMULADO (no se escribe nada). Se escribirían' if p.simular else 'Escritas') + f' en la versión {m["mlflow_version"]} de «{m["modelo"]}» en MLflow:')
            for k, v in et.items():
                print(f'  {k} = {v}')
        elif p.orden == 'puerta':
            m = cargar(p.manifiesto)
            fallos = puerta(m, p.auc_minimo)
            if fallos:
                raise ErrorManifiesto('Puerta de calidad CERRADA: ' + ' '.join(fallos))
            print(f'Puerta de calidad abierta: la versión {m["mlflow_version"]} tiene AUC valid {m["valid_auc"]:.4f} y test {m["test_auc"]:.4f} (mínimo {p.auc_minimo:g}) y huella {m["huella_datos"]}.')
        else:
            valor = campo(cargar(p.manifiesto), p.campo)
            print(json.dumps(valor, ensure_ascii=False) if isinstance(valor, (dict, list)) else ('' if valor is None else valor))
        return 0
    except ErrorManifiesto as e:
        print(f'Error: {e}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
