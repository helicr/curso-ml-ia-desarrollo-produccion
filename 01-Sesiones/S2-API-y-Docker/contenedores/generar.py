"""Genera todo el material de contenedores a partir de ejemplos.py + salidas-reales.json:

    guia-practica.md                         guía en texto (9 ejemplos)
    laboratorio-romper.md                    laboratorio de 5 roturas
    modelo-mental/index.html                 presentación 1 «Contenedores: el modelo mental»
    del-dockerfile-a-produccion/index.html   presentación 2 «Del Dockerfile a producción»

Uso:  python generar.py            escribe los archivos
      python generar.py --comprobar  no escribe; sale con 1 si algún archivo no está al día
"""
import argparse
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
if str(AQUI) not in sys.path:
    sys.path.insert(0, str(AQUI))

import datos  # noqa: E402,F401  (comprueba la coherencia comandos <-> salidas)
import presentaciones  # noqa: E402
import textos  # noqa: E402


def contenidos():
    return {
        AQUI / 'guia-practica.md': textos.guia_md(),
        AQUI / 'laboratorio-romper.md': textos.laboratorio_md(),
        AQUI / 'modelo-mental' / 'index.html': presentaciones.modelo_mental().html(),
        AQUI / 'del-dockerfile-a-produccion' / 'index.html': presentaciones.dockerfile_a_produccion().html(),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--comprobar', action='store_true', help='no escribe: comprueba que los archivos generados estan al dia')
    a = ap.parse_args()
    desfasados = []
    for ruta, texto in contenidos().items():
        actual = ruta.read_text(encoding='utf-8') if ruta.exists() else None
        if actual != texto:
            desfasados.append(ruta)
            if not a.comprobar:
                ruta.parent.mkdir(parents=True, exist_ok=True)
                ruta.write_text(texto, encoding='utf-8')
                print('escrito', ruta.relative_to(AQUI))
    if a.comprobar:
        if desfasados:
            print('DESFASADOS (ejecuta python generar.py):', *[str(r.relative_to(AQUI)) for r in desfasados], sep='\n  ')
            sys.exit(1)
        print('todo al dia')
    elif not desfasados:
        print('sin cambios')


if __name__ == '__main__':
    main()
