#!/usr/bin/env python3
"""Ejecuta con Docker de verdad todos los pasos de `ejemplos.py` y guarda la salida real en `salidas-reales.json`.

Pensado para GitHub Actions (Ubuntu con Docker), pero vale en cualquier Linux con Docker:

    python3 ejecutar.py                       # todo
    python3 ejecutar.py --solo e3,e5,r2       # solo esos
    python3 ejecutar.py --salida otra.json

Cada ejemplo se ejecuta en una copia temporal de su carpeta (los archivos del repositorio no se tocan) y, antes de cada
uno, se borran los contenedores y el volumen `datos` que hubiera. Cada paso comprueba su código de salida y lo que la
salida debe (o no debe) contener. Si algo no se cumple, el programa termina con error, pero antes escribe el JSON
para poder ver qué pasó. Al final imprime el JSON por trozos entre marcas (para recuperarlo de un registro de Actions).
"""
import argparse
import base64
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zlib
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import ejemplos as E  # noqa: E402

CARPETA_EJEMPLOS = AQUI / 'ejemplos'
TIEMPO_MAXIMO = 600


def ejecutar(cmd, cwd):
    t0 = time.time()
    try:
        r = subprocess.run(['bash', '-c', cmd], cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=TIEMPO_MAXIMO)
        salida, rc = r.stdout.decode('utf-8', 'replace'), r.returncode
    except subprocess.TimeoutExpired as e:
        salida, rc = (e.stdout or b'').decode('utf-8', 'replace') + '\n[TIEMPO AGOTADO]', 124
    return rc, salida.replace('\r', ''), round(time.time() - t0, 1)


def normalizar(salida, reglas):
    for patron, repl in reglas:
        salida = re.sub(patron, repl, salida)
    return salida.rstrip('\n')


def rc_ok(esperado, rc):
    if esperado == 'distinto':
        return rc != 0
    if isinstance(esperado, (list, tuple)):
        return rc in esperado
    return rc == esperado


def limpiar():
    ejecutar('docker ps -aq | xargs -r docker rm -f; docker volume rm -f datos', '/')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--solo', help='ids separados por comas, p. ej. e3,e5,r2')
    ap.add_argument('--salida', default=str(AQUI / 'salidas-reales.json'))
    a = ap.parse_args()
    ids = set(a.solo.split(',')) if a.solo else None

    _, version, _ = ejecutar("docker version --format '{{.Server.Version}}'", '/')
    _, sistema, _ = ejecutar('. /etc/os-release && echo "$PRETTY_NAME"', '/')
    resultado = dict(meta=dict(fecha=time.strftime('%Y-%m-%d'), docker=version.strip(), sistema=sistema.strip(),
                               kernel=platform.release(), nota='Ejecutado con Docker en GitHub Actions (Ubuntu).'),
                     ejemplos={})
    fallos = []

    for ej in E.TODOS:
        if ids and ej['id'] not in ids:
            continue
        limpiar()
        tmp = Path(tempfile.mkdtemp(prefix=f'{ej["id"]}-'))
        if ej['carpeta']:
            shutil.copytree(CARPETA_EJEMPLOS / ej['carpeta'], tmp, dirs_exist_ok=True)
        pasos = [('paso', p) for p in ej['pasos']] + [('arreglo', p) for p in ej.get('arreglo', [])]
        filas = []
        print(f'\n=== {ej["id"]} · {ej["titulo"]}', flush=True)
        for fase, p in pasos:
            if p['pausa']:
                time.sleep(p['pausa'])
            rc, salida, seg = ejecutar(p['cmd'], tmp)
            salida = normalizar(salida, p['norm'])
            problemas = []
            if not rc_ok(p['rc'], rc):
                problemas.append(f'código de salida {rc}, se esperaba {p["rc"]}')
            if p['espera'] and not re.search(p['espera'], salida, re.M):
                problemas.append(f'la salida no contiene /{p["espera"]}/')
            if p['no_espera'] and re.search(p['no_espera'], salida, re.M):
                problemas.append(f'la salida contiene lo que no debía: /{p["no_espera"]}/')
            marca = 'OK ' if not problemas else 'MAL'
            print(f'  [{marca}] ({fase}) {p["cmd"][:100]}  rc={rc}  {seg}s', flush=True)
            for linea in salida.split('\n')[:6]:
                print(f'        | {linea[:160]}', flush=True)
            for pr in problemas:
                print(f'        !! {pr}', flush=True)
                fallos.append(f'{ej["id"]}: {p["cmd"][:80]} -> {pr}')
            filas.append(dict(fase=fase, cmd=p['cmd'], rc=rc, segundos=seg, salida=salida))
        resultado['ejemplos'][ej['id']] = filas
        shutil.rmtree(tmp, ignore_errors=True)
    limpiar()

    Path(a.salida).write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding='utf-8')
    paquete = base64.b64encode(zlib.compress(json.dumps(resultado, ensure_ascii=False).encode('utf-8'), 9)).decode('ascii')
    print('\nJSON-BEGIN')
    for i in range(0, len(paquete), 3000):
        print('J|' + paquete[i:i + 3000])
    print('JSON-END')
    if fallos:
        print('\nFALLOS:')
        for f in fallos:
            print(' -', f)
        sys.exit(1)
    print('\nTODO OK')


if __name__ == '__main__':
    main()
