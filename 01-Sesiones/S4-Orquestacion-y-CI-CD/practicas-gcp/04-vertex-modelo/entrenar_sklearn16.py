"""Reentrena NUESTRO modelo de retencion (la misma regresion logistica de 04-Proyecto-Base) con la version de scikit-learn del contenedor de Vertex AI.

POR QUE: el proyecto usa scikit-learn 1.9.1, pero los contenedores pre-construidos de Vertex solo llegan a la 1.6. Un modelo guardado con una
version no se debe abrir con otra, asi que se entrena de nuevo, con el mismo codigo (ia_mlops.modeling.train.modelos), los mismos datos
(ml_dataset de curso.db), las mismas 13 variables y en el mismo orden (ia_mlops.config.FEATURES). No es otro modelo: es el mismo, empaquetado para Vertex.

SALIDAS en --salida:
  model.joblib        el artefacto que se sube a Cloud Storage (el nombre EXACTO lo exige Vertex AI para scikit-learn)
  instancias.json     {"instances": [[13 numeros], ...]}: el cuerpo de la peticion, variables en el orden del modelo
  esperado_local.json lo que da este mismo modelo en local (probabilidad y clase) para los mismos clientes

Uso:  python entrenar_sklearn16.py --proyecto RUTA/04-Proyecto-Base --salida /tmp/curso-vertex --clientes ../clientes_ejemplo.json
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

import joblib
import sklearn


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--proyecto', required=True)
    ap.add_argument('--salida', required=True)
    ap.add_argument('--clientes', required=True, help='JSON con clientes de ejemplo (clientes_ejemplo.json)')
    a = ap.parse_args()
    proyecto, salida = Path(a.proyecto).resolve(), Path(a.salida)
    salida.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(proyecto))
    import pandas as pd
    from ia_mlops import config
    from ia_mlops.modeling import train

    con = sqlite3.connect(f'{(proyecto / "data" / "processed" / "curso.db").as_uri()}?mode=ro', uri=True)
    partes, _ = train.cargar_datos(con)
    con.close()
    X = {k: v[config.FEATURES] for k, v in partes.items()}
    y = {k: v[config.OBJETIVO] for k, v in partes.items()}
    modelo = train.modelos()['regresion_logistica']
    modelo.fit(X['train'], y['train'])
    metricas = train.evaluar(modelo, X['valid'], y['valid'])
    print(f'scikit-learn {sklearn.__version__} | filas train/valid: {len(X["train"])}/{len(X["valid"])} | AUC valid = {metricas["auc"]:.4f}')

    meta = json.loads((proyecto / 'models' / 'metadatos.json').read_text(encoding='utf-8')) if (proyecto / 'models' / 'metadatos.json').exists() else {}
    if meta.get('metricas_valid'):
        print(f'AUC valid del modelo del proyecto (scikit-learn {meta["versiones"]["scikit-learn"]}): {meta["metricas_valid"]["auc"]:.4f}  (deben ser casi iguales)')

    joblib.dump(modelo, salida / 'model.joblib')

    clientes = json.loads(Path(a.clientes).read_text(encoding='utf-8'))
    nombres = list(clientes)
    filas = [[float(clientes[n][v]) for v in config.FEATURES] for n in nombres]      # orden = config.FEATURES = metadatos.json['variables']
    (salida / 'instancias.json').write_text(json.dumps({'instances': filas}), encoding='utf-8')
    probas = modelo.predict_proba(pd.DataFrame(filas, columns=config.FEATURES))[:, 1]
    esperado = [{'cliente': n, 'probabilidad': float(p), 'clase': int(p >= 0.5)} for n, p in zip(nombres, probas)]
    (salida / 'esperado_local.json').write_text(json.dumps(esperado, indent=2, ensure_ascii=False), encoding='utf-8')
    print('Variables, en este orden:', ', '.join(config.FEATURES))
    for e in esperado:
        print(f'  {e["cliente"]:8s} probabilidad local = {e["probabilidad"]:.4f} -> clase {e["clase"]}')


if __name__ == '__main__':
    main()
