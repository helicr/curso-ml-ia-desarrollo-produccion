"""Genera la presentación «Tu caso de S1 a S5» (index.html de esta carpeta) a partir de deck.py y hechos.py.

Uso:  python generar.py              escribe index.html
      python generar.py --comprobar  no escribe; sale con 1 si index.html no está al día
"""
import argparse
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
if str(AQUI) not in sys.path:
    sys.path.insert(0, str(AQUI))

import deck  # noqa: E402


def contenidos():
    return {AQUI / 'index.html': deck.deck().html()}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--comprobar', action='store_true', help='no escribe: comprueba que index.html esta al dia')
    a = ap.parse_args()
    desfasados = []
    for ruta, texto in contenidos().items():
        actual = ruta.read_text(encoding='utf-8') if ruta.exists() else None
        if actual != texto:
            desfasados.append(ruta)
            if not a.comprobar:
                ruta.write_text(texto, encoding='utf-8')
                print('escrito', ruta.name)
    if a.comprobar:
        if desfasados:
            print('DESFASADO (ejecuta python generar.py):', *[r.name for r in desfasados])
            sys.exit(1)
        print('todo al dia')
    elif not desfasados:
        print('sin cambios')


if __name__ == '__main__':
    main()
