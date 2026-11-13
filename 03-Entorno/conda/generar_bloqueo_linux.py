"""Genera env-ia-mlops-linux-64.txt: la lista EXPLÍCITA de paquetes del entorno para el Codespace del curso (linux-64).

Por qué: en el Codespace de 2 núcleos (8 GB), `conda env create -f environment.yml` resuelve 480 paquetes y el sistema
termina el proceso hacia los 7 GB de memoria (probado el 12/11/2026). Con la lista explícita, `conda create --file` instala
sin resolver nada: unos 2 minutos y 4,3 GB.

Se ejecuta en cualquier equipo con conda (Windows, Linux o macOS) y conexión; resuelve para linux-64 sin instalar nada:
    python 03-Entorno/conda/generar_bloqueo_linux.py
Regenerarla cada vez que cambie environment.yml (una prueba lo vigila: pruebas/test_bloqueo_linux.py).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ENTORNO = AQUI / 'environment.yml'
SALIDA = AQUI / 'env-ia-mlops-linux-64.txt'
CANAL = 'conda-forge'
GLIBC = '2.41'   # la de Debian 13 (trixie), base de mcr.microsoft.com/devcontainers/miniconda:3 en noviembre de 2026


def fijados(texto=None):
    """Paquetes fijados en environment.yml: {'python': '3.11', 'pandas': '2.3.3', ...}."""
    texto = texto if texto is not None else ENTORNO.read_text(encoding='utf-8')
    return dict(re.findall(r'^\s+- ([a-z0-9_.-]+)=([0-9][^\s#]*)', texto, flags=re.M))


def resolver():
    conda = os.environ.get('CONDA_EXE') or shutil.which('conda') or shutil.which('conda.bat')
    if not conda:
        sys.exit('No encuentro conda (CONDA_EXE o en el PATH).')
    specs = [f'{n}={v}' for n, v in fijados().items()]
    entorno = dict(os.environ, CONDA_SUBDIR='linux-64', CONDA_OVERRIDE_GLIBC=GLIBC, CONDA_OVERRIDE_LINUX='6.8')
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / 'specs.txt'
        f.write_text('\n'.join(specs) + '\n', encoding='utf-8')
        r = subprocess.run([conda, 'create', '-n', 'bloqueo-linux', '--dry-run', '--json', '--override-channels',
                            '-c', CANAL, '--file', str(f)], capture_output=True, text=True, env=entorno)
    datos = json.loads(r.stdout)
    if not datos.get('success'):
        sys.exit('No resuelve para linux-64:\n' + str(datos.get('error', r.stderr))[:3000])
    return datos['actions']['LINK']


def existe(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method='HEAD'), timeout=30) as r:
            return r.status == 200
    except Exception:
        return False


def url_de(p):
    base = f"{p['base_url']}/{p['platform']}/{p['dist_name']}"
    return next((base + ext for ext in ('.conda', '.tar.bz2') if existe(base + ext)), None)


def main():
    paquetes = sorted(resolver(), key=lambda p: p['name'])
    with ThreadPoolExecutor(16) as ex:
        urls = list(ex.map(url_de, paquetes))
    faltan = [p['dist_name'] for p, u in zip(paquetes, urls) if not u]
    if faltan:
        sys.exit('Sin archivo en el canal: ' + ', '.join(faltan))
    cabecera = [
        '# Entorno env-ia-mlops para el Codespace del curso (linux-64), sin resolver dependencias:',
        '#   conda create -n env-ia-mlops --file 03-Entorno/conda/env-ia-mlops-linux-64.txt',
        '# Generado desde 03-Entorno/conda/environment.yml con generar_bloqueo_linux.py (solo conda-forge). No editar a mano.',
        '# platform: linux-64',
        '@EXPLICIT',
    ]
    SALIDA.write_text('\n'.join(cabecera + urls) + '\n', encoding='utf-8', newline='\n')
    print(f'{SALIDA.name}: {len(urls)} paquetes')


if __name__ == '__main__':
    main()
