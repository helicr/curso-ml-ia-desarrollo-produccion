"""Compara la respuesta del endpoint de Vertex AI con lo que da el mismo modelo en local (esperado_local.json).

El contenedor pre-construido de scikit-learn llama a predict(): lo normal es que devuelva la CLASE (0 o 1). Si devolviera probabilidades
(entre 0 y 1) tambien se acepta y se compara con tolerancia. Acepta la salida de `gcloud ai endpoints predict --format=json`
(un dict con "predictions" o directamente la lista).

Uso:  python3 comparar_respuesta.py --respuesta /tmp/respuesta.json --esperado /tmp/curso-vertex/esperado_local.json
"""
import argparse
import json


def predicciones(texto):
    d = json.loads(texto)
    if isinstance(d, dict):
        d = d.get('predictions', d)
    return [float(x[0] if isinstance(x, list) else x) for x in d]


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--respuesta', required=True)
    ap.add_argument('--esperado', required=True)
    a = ap.parse_args()
    obtenido = predicciones(open(a.respuesta, encoding='utf-8').read())
    esperado = json.load(open(a.esperado, encoding='utf-8'))
    if len(obtenido) != len(esperado):
        raise SystemExit(f'ERROR: {len(obtenido)} predicciones y se esperaban {len(esperado)}')
    mal = 0
    for o, e in zip(obtenido, esperado):
        es_clase = o in (0.0, 1.0)
        ok = (int(o) == e['clase']) if es_clase else abs(o - e['probabilidad']) < 1e-6
        tipo = 'clase' if es_clase else 'probabilidad'
        print(f'{e["cliente"]:8s} Vertex ({tipo}) = {o:g} | local: probabilidad {e["probabilidad"]:.4f}, clase {e["clase"]} -> {"OK" if ok else "DIFERENTE"}')
        mal += 0 if ok else 1
    raise SystemExit(1 if mal else 0)
