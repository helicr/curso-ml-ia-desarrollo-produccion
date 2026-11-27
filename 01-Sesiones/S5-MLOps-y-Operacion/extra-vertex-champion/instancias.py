"""Convierte los clientes de ejemplo (clientes_ejemplo.json, con nombres de variable) en el cuerpo que espera Vertex.

Vertex recibe cada cliente como una LISTA de 13 números EN EL ORDEN de ia_mlops.config.FEATURES, no como un diccionario:
    {"instances": [[35, 6, 1250.4, 208.4, 410, 38, 310, 2, 380.5, 4, 55.0, 1, 1], ...]}
Si cambias el orden el modelo no avisa: contesta otra cosa. Por eso esto se genera, no se escribe a mano.

Uso (desde esta carpeta):
    python instancias.py [--clientes clientes_ejemplo.json] [--salida instancias.json]
"""
import argparse
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import manifiesto_champion  # noqa: E402,F401  (fija el sys.path del proyecto)


def a_instancias(clientes):
    """{'activo': {...}, ...} -> {'instances': [[13 números], ...], 'nombres': ['activo', ...]}; falla si falta alguna variable."""
    from ia_mlops import config
    filas, nombres = [], []
    for nombre, c in clientes.items():
        faltan = [v for v in config.FEATURES if v not in c]
        if faltan:
            raise ValueError(f'Al cliente «{nombre}» le faltan variables: {faltan}')
        filas.append([c[v] for v in config.FEATURES])
        nombres.append(nombre)
    return {'instances': filas, 'nombres': nombres}


def main(argv=None):
    ap = argparse.ArgumentParser(description='Crea instancias.json para Vertex a partir de clientes_ejemplo.json')
    ap.add_argument('--clientes', default=str(AQUI / 'clientes_ejemplo.json'))
    ap.add_argument('--salida', default='instancias.json')
    a = ap.parse_args(argv)
    try:
        cuerpo = a_instancias(json.loads(Path(a.clientes).read_text(encoding='utf-8')))
    except (OSError, ValueError) as e:
        print(f'Error: {e}', file=sys.stderr)
        return 2
    Path(a.salida).write_text(json.dumps({'instances': cuerpo['instances']}), encoding='utf-8')
    print(f'Escrito {a.salida}: {len(cuerpo["instances"])} instancias ({", ".join(cuerpo["nombres"])}), 13 números cada una')
    return 0


if __name__ == '__main__':
    sys.exit(main())
