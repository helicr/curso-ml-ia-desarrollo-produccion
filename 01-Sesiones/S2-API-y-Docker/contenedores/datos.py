"""Une los comandos (ejemplos.py) con las salidas reales (salidas-reales.json) y comprueba que van a la par.

Lo usan generar.py (guía, laboratorio y presentaciones) y las pruebas. Si ejemplos.py cambia y no se vuelve a ejecutar
ejecutar.py, este módulo se niega a seguir: así nunca se publica una salida que no corresponde al comando.
"""
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
if str(AQUI) not in sys.path:
    sys.path.insert(0, str(AQUI))

import ejemplos as E  # noqa: E402

SALIDAS = json.loads((AQUI / 'salidas-reales.json').read_text(encoding='utf-8'))
META = SALIDAS['meta']
RAIZ_REPO_CMD = 'cd "$(git rev-parse --show-toplevel)"'
CARPETA_ABS = E.CARPETA                                   # relativa a la raíz del repositorio
CARPETA_LIBRE = 'mkdir -p ~/practica-docker && cd ~/practica-docker'
MINUTOS_MIN = None                                        # se calcula abajo


def todos():
    return E.TODOS


def por_id(i):
    return next(x for x in E.TODOS if x['id'] == i)


def pasos_de(x):
    """Pasos en el orden en que los ejecutó el ejecutor: primero `pasos`, luego `arreglo`."""
    return list(x['pasos']) + list(x.get('arreglo', []))


def comprobar_coherencia():
    for x in E.TODOS:
        regs = SALIDAS['ejemplos'].get(x['id'])
        if regs is None:
            raise SystemExit(f'salidas-reales.json no tiene {x["id"]}: vuelve a ejecutar ejecutar.py')
        ps = pasos_de(x)
        if len(ps) != len(regs):
            raise SystemExit(f'{x["id"]}: {len(ps)} pasos en ejemplos.py y {len(regs)} en salidas-reales.json')
        for k, (p, r) in enumerate(zip(ps, regs)):
            if p['cmd'] != r['cmd']:
                raise SystemExit(f'{x["id"]} paso {k + 1}: el comando de ejemplos.py ya no es el que se ejecutó\n  ejemplos.py: {p["cmd"]}\n  ejecutado:   {r["cmd"]}')
            fase = 'paso' if k < len(x['pasos']) else 'arreglo'
            if r['fase'] != fase:
                raise SystemExit(f'{x["id"]} paso {k + 1}: la fase ejecutada es {r["fase"]} y debería ser {fase}')


comprobar_coherencia()


def registro(i, k):
    """Registro ejecutado del paso k (0-based) del ejemplo i, contando pasos y luego arreglo."""
    return SALIDAS['ejemplos'][i][k]


def mostrado(p, reg):
    """La salida tal como se enseña: respeta `mostrar` del paso (todas / últimas n / primeras n / ocultar)."""
    s = (reg['salida'] or '').rstrip('\n')
    for patron, reemplazo in p['norm']:          # idempotente: ya se aplicó al ejecutar; recoge las reglas añadidas después
        s = re.sub(patron, reemplazo, s)
    m = p['mostrar']
    if m is None:
        return s
    modo, n = m
    if n == 0:
        return ''
    ls = s.split('\n')
    return '\n'.join(ls[-n:] if modo == 'ultimas' else ls[:n])


def salida(i, k):
    x = por_id(i)
    return mostrado(pasos_de(x)[k], registro(i, k))


def cmd(i, k):
    return pasos_de(por_id(i))[k]['cmd']


def segundos(i, k):
    return registro(i, k)['segundos']


def minutos_total(lista):
    return sum(x['minutos'] for x in lista)


def preparar_carpeta(x):
    """Comando (o comandos) con los que el alumno se coloca antes de empezar el ejemplo."""
    if x.get('carpeta'):
        return f'cd "$(git rev-parse --show-toplevel)/{CARPETA_ABS}/{x["carpeta"]}"'
    return CARPETA_LIBRE


def archivos_de(x):
    """(nombre, texto, lenguaje) de los archivos de la carpeta del ejemplo, Dockerfile primero. Sin .gitignore ni cachés."""
    if not x.get('carpeta'):
        return []
    base = AQUI / 'ejemplos' / x['carpeta']
    if not base.is_dir():
        raise SystemExit(f'no existe la carpeta {base}')
    nombres = sorted(p.name for p in base.iterdir() if p.is_file() and p.name not in ('.gitignore',))
    nombres.sort(key=lambda n: (not n.startswith('Dockerfile'), n))
    out = []
    for n in nombres:
        leng = 'dockerfile' if n.startswith('Dockerfile') else ('python' if n.endswith('.py') else 'text')
        out.append((n, (base / n).read_text(encoding='utf-8').rstrip('\n'), leng))
    return out
