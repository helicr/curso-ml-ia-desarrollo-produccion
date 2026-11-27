"""Ayudante de los scripts de Cloud Shell: lee el JSON de `gcloud` y calcula el reparto de tráfico (sin jq).

Lo usan desplegar.sh, promover.sh, volver.sh, borrar.sh y los workflows. No llama a Google Cloud: solo lee un archivo JSON que
guardó `gcloud ... --format json` y escribe en pantalla UNA cosa por orden, para capturarla en el script con $(...).

Forma del JSON que se espera (los nombres de campo son los de la API REST de Vertex AI; SIN VERIFICAR en una cuenta real):
    endpoint   gcloud ai endpoints describe ENDPOINT --format json
               {"deployedModels": [{"id": "123", "displayName": "mlflow-v5", ...}], "trafficSplit": {"123": 100}}
    versiones  gcloud ai models list-version MODELO --format json
               [{"versionId": "2", "versionAliases": ["champion", "mlflow-v5"], "labels": {...}}, ...]

Órdenes:
    version-modelo --json F --alias A        versionId de la versión que tiene el alias A (vacío si no hay)
    etiqueta-de    --json F --alias A --clave K   valor de la etiqueta K de la versión con el alias A (vacío si no hay)
    desplegado     --json F --nombre N       id del modelo desplegado con ese nombre visible (vacío si no hay)
    nombre-de      --json F --id ID          nombre visible del modelo desplegado con ese id
    actual         --json F                  id del modelo desplegado que más tráfico recibe (vacío si no hay ninguno)
    trafico        --json F                  una línea por modelo desplegado: id, nombre y porcentaje
    split-nuevo    --json F --porcentaje N   valor para --traffic-split al desplegar uno nuevo: 0=N,<el que más tráfico tenía>=100-N,...
    split-solo     --json F --id ID          valor para `endpoints update --traffic-split`: ID=100 y el resto a 0
    ids            --json F                  los ids de los modelos desplegados, separados por espacios
"""
import argparse
import json
import sys
from pathlib import Path


def _leer(ruta):
    return json.loads(Path(ruta).read_text(encoding='utf-8'))


def _desplegados(endpoint):
    reparto = endpoint.get('trafficSplit') or {}
    return [{'id': str(d['id']), 'nombre': d.get('displayName', ''), 'pct': int(reparto.get(str(d['id']), 0))} for d in endpoint.get('deployedModels') or []]


def version_modelo(versiones, alias):
    for v in versiones:
        if alias in (v.get('versionAliases') or []):
            return str(v['versionId'])
    return ''


def etiqueta_de(versiones, alias, clave):
    for v in versiones:
        if alias in (v.get('versionAliases') or []):
            return str((v.get('labels') or {}).get(clave, ''))
    return ''


def desplegado(endpoint, nombre):
    return next((d['id'] for d in _desplegados(endpoint) if d['nombre'] == nombre), '')


def nombre_de(endpoint, id_):
    return next((d['nombre'] for d in _desplegados(endpoint) if d['id'] == str(id_)), '')


def actual(endpoint):
    d = _desplegados(endpoint)
    return max(d, key=lambda x: x['pct'])['id'] if d else ''


def split_nuevo(endpoint, porcentaje):
    """Reparto al desplegar un modelo nuevo: «0» es el modelo que se despliega (documentación de Vertex). Suma 100."""
    porcentaje = int(porcentaje)
    if not 0 <= porcentaje <= 100:
        raise ValueError('El porcentaje debe estar entre 0 y 100.')
    previos = _desplegados(endpoint)
    if not previos:
        return '0=100'
    principal = actual(endpoint)
    partes = [f'0={porcentaje}'] + [f'{d["id"]}={100 - porcentaje if d["id"] == principal else 0}' for d in previos]
    return ','.join(partes)


def split_solo(endpoint, id_):
    ids = [d['id'] for d in _desplegados(endpoint)]
    if str(id_) not in ids:
        raise ValueError(f'El modelo desplegado {id_} no está en el endpoint (hay: {", ".join(ids) or "ninguno"}).')
    return ','.join(f'{i}={100 if i == str(id_) else 0}' for i in ids)


def main(argv=None):
    ap = argparse.ArgumentParser(description='Ayudante JSON de los scripts de Vertex AI')
    ap.add_argument('orden', choices=['version-modelo', 'etiqueta-de', 'desplegado', 'nombre-de', 'actual', 'trafico', 'split-nuevo', 'split-solo', 'ids'])
    ap.add_argument('--json', required=True)
    ap.add_argument('--alias')
    ap.add_argument('--clave')
    ap.add_argument('--nombre')
    ap.add_argument('--id')
    ap.add_argument('--porcentaje')
    a = ap.parse_args(argv)
    try:
        datos = _leer(a.json)
        if a.orden == 'version-modelo':
            print(version_modelo(datos, a.alias))
        elif a.orden == 'etiqueta-de':
            print(etiqueta_de(datos, a.alias, a.clave))
        elif a.orden == 'desplegado':
            print(desplegado(datos, a.nombre))
        elif a.orden == 'nombre-de':
            print(nombre_de(datos, a.id))
        elif a.orden == 'actual':
            print(actual(datos))
        elif a.orden == 'trafico':
            for d in _desplegados(datos):
                print(f'{d["id"]}\t{d["nombre"]}\t{d["pct"]}%')
        elif a.orden == 'split-nuevo':
            print(split_nuevo(datos, a.porcentaje))
        elif a.orden == 'split-solo':
            print(split_solo(datos, a.id))
        else:
            print(' '.join(d['id'] for d in _desplegados(datos)))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f'Error: {e}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
