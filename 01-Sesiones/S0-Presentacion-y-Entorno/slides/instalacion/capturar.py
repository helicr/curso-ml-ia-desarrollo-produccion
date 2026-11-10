"""Ejecuta de verdad (en Linux o macOS) los comandos de contenido.py que llevan clave `k` y guarda sus salidas reales en salidas-reales.json.

Para que sirve: las diapositivas y la guia rapida muestran esas salidas como «Debe salir asi». Asi lo que ves en pantalla no esta escrito a mano:
es lo que dio el comando la ultima vez que se capturo, con el entorno hecho desde environment.yml. Vuelve a capturar cada vez que cambies
environment.yml, los scripts de 03-Entorno/conda o el proyecto base, y despues ejecuta generar.py.

Uso (desde cualquier carpeta; necesita conda para --crear y git para copiar el repositorio):
    python capturar.py --entorno /ruta/a/envs/env-ia-mlops --conda /ruta/a/conda --crear     # crea el entorno desde cero y captura todo
    python capturar.py --entorno /ruta/a/envs/env-ia-mlops --conda /ruta/a/conda             # usa un entorno ya creado
El nombre de la carpeta del entorno debe ser env-ia-mlops. Los comandos se ejecutan sobre una COPIA temporal del repositorio (lo versionado y lo nuevo
sin ignorar), en un HOME temporal: no se ensucia el repositorio ni tu configuracion de Jupyter.
Solo para Linux/macOS: la captura de Windows no se puede hacer aqui (ver «Qué no se probó» en la guia).
"""
import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[3]
sys.path.insert(0, str(AQUI))
import contenido as C  # noqa: E402

RUIDO = re.compile(r'(INFO mlflow|INFO alembic|Downloading artifacts|StarletteDeprecation|from starlette|UserWarning|warnings\.warn|WARNING mlflow|'
                   r'\[IPKernelApp\]|Registry store URI|Updating database tables|Creating initial MLflow)')
PASAN_DEL_ENTORNO = ('HTTP_PROXY', 'HTTPS_PROXY', 'NO_PROXY', 'http_proxy', 'https_proxy', 'no_proxy', 'SSL_CERT_FILE', 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE', 'GIT_SSL_CAINFO')
RECORTES = {   # clave -> (lineas del principio, lineas del final) si la salida es mas larga
    'humo': (3, 8), 'crear_entorno': (0, 16), 'pytest_rapido': (0, 3), 'pytest_total': (0, 3), 'verificar': (0, 40),
}


def copiar_repositorio(destino):
    archivos = subprocess.run(['git', '-C', str(RAIZ), 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], capture_output=True, check=True).stdout.decode().split('\0')
    for a in filter(None, archivos):
        origen = RAIZ / a
        if origen.is_file():
            (destino / a).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origen, destino / a)


def enmascarar(texto, entorno, copia, casa):
    for real, falso in ((str(copia), '<repositorio>'), (str(entorno), f'<conda>/envs/{C.ENTORNO}'), (str(entorno.parent), '<conda>/envs'), (str(casa), '~'),
                        (str(Path.home()), '~')):
        texto = texto.replace(real, falso)
    return texto


def limpiar(texto, clave, entorno, copia, casa):
    texto = enmascarar(texto, entorno, copia, casa)
    lineas = []
    for linea in texto.replace('\r\n', '\n').split('\n'):
        linea = linea.split('\r')[-1].rstrip()            # barras de progreso: solo el ultimo estado
        if RUIDO.search(linea):
            continue
        lineas.append(linea)
    while lineas and not lineas[-1].strip():
        lineas.pop()
    lineas = [re.sub(r'conda activate <conda>/envs/' + re.escape(C.ENTORNO), 'conda activate ' + C.ENTORNO, x) for x in lineas]   # ver nota en main()
    principio, final = RECORTES.get(clave, (0, 0))
    if (principio or final) and len(lineas) > principio + final:
        lineas = lineas[:principio] + ['…'] + lineas[-final:] if principio else lineas[-final:]
    return '\n'.join(lineas)


def cwd_tras_cd(cwd, comando, copia, fuera):
    destino = comando[3:].strip().replace('\\', '/')
    if destino.lower().startswith('c:/cursos/' + C.CARPETA_REPO.lower()):
        return copia
    if destino.lower().rstrip('/') == 'c:/cursos':
        return fuera
    return (cwd / destino).resolve()


def correr(comando_linux, cwd, env, tiempo=1800):
    t0 = time.monotonic()
    p = subprocess.run(['bash', '-c', comando_linux], cwd=cwd, env=env, capture_output=True, text=True, timeout=tiempo)
    return p.returncode, (p.stdout or '') + (p.stderr or ''), time.monotonic() - t0


def mlflow_ui(cwd, env, entorno, copia, casa):
    """Arranca `mlflow ui` como lo haria el alumno, espera a que responda y lo detiene. Devuelve (codigo, salida, segundos hasta estar listo)."""
    log = Path(tempfile.mkdtemp(prefix='mlui-')) / 'ui.log'
    t0 = time.monotonic()
    with open(log, 'w') as f:
        p = subprocess.Popen(['bash', '-c', 'mlflow ui --backend-store-uri sqlite:///mlflow.db'], cwd=cwd, env=env, stdout=f, stderr=subprocess.STDOUT, start_new_session=True)
        listo = None
        try:
            while time.monotonic() - t0 < 120:
                try:
                    if urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=2).status == 200:
                        listo = time.monotonic() - t0
                        break
                except Exception:  # noqa: BLE001 - mientras arranca no responde
                    time.sleep(1)
        finally:
            os.killpg(p.pid, signal.SIGTERM)
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(p.pid, signal.SIGKILL)
    lineas = [re.sub(r'^\d{4}/\d\d/\d\d \d\d:\d\d:\d\d ', '', x) for x in log.read_text().splitlines() if 'Uvicorn running' in x]
    return (0 if listo is not None else 1), '\n'.join(lineas), (listo if listo is not None else time.monotonic() - t0)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--entorno', required=True, help='ruta del entorno (la carpeta debe llamarse env-ia-mlops)')
    ap.add_argument('--conda', help='ruta del ejecutable de conda (hace falta para --crear y para `conda --version`)')
    ap.add_argument('--crear', action='store_true', help='borra y crea el entorno desde environment.yml antes de capturar')
    ap.add_argument('--salida', default=str(AQUI / 'salidas-reales.json'))
    a = ap.parse_args()
    entorno = Path(a.entorno).resolve()
    if entorno.name != C.ENTORNO:
        sys.exit(f'La carpeta del entorno debe llamarse {C.ENTORNO}, y es {entorno.name}')
    base = Path(tempfile.mkdtemp(prefix='captura-s0-'))
    copia, fuera, casa = base / C.CARPETA_REPO, base / 'fuera', base / 'casa'      # la copia se llama como la carpeta que clona el alumno: asi lo ve en «Repositorio: …»
    fuera.mkdir()
    casa.mkdir()
    copiar_repositorio(copia)
    path = [str(entorno / 'bin')] + ([str(Path(a.conda).parent)] if a.conda else []) + ['/usr/bin', '/bin']
    env = {'PATH': os.pathsep.join(path), 'HOME': str(casa), 'CONDA_PREFIX': str(entorno), 'LANG': 'C.UTF-8', 'PYTHONUNBUFFERED': '1'}
    for nombre in PASAN_DEL_ENTORNO:                       # sin esto, conda no llega a Internet detras de un proxy
        if nombre in os.environ:
            env[nombre] = os.environ[nombre]
    salidas, meta = {}, {'fecha': time.strftime('%Y-%m-%d'), 'sistema': f'{os.uname().sysname} {os.uname().release}', 'nota': 'Salidas reales; rutas y usuario sustituidos. Unica normalizacion: en crear_entorno, «conda activate <ruta>» se muestra como «conda activate env-ia-mlops» porque el entorno se creo con -p.'}

    if a.crear:
        if not a.conda:
            sys.exit('--crear necesita --conda')
        shutil.rmtree(entorno, ignore_errors=True)
        # Se crea con -p porque por nombre conda se negaria si ya existe un env-ia-mlops en su carpeta de entornos. Con -p el mensaje final dice
        # «conda activate <ruta>»; mas abajo se sustituye la ruta por el nombre (unica normalizacion de esa salida), que es lo que vera el alumno.
        print('Creando el entorno desde environment.yml ...', flush=True)
        codigo, texto, seg = correr(f'{a.conda} env create -f 03-Entorno/conda/environment.yml -p {entorno}', copia, env)
        salidas['crear_entorno'] = dict(cmd='conda env create -f 03-Entorno/conda/environment.yml', codigo=codigo, segundos=round(seg), salida=limpiar(texto, 'crear_entorno', entorno, copia, casa))
        if codigo != 0:
            print(texto[-2000:])
            sys.exit('La creacion del entorno fallo')
    if not (entorno / 'bin' / 'python').exists():
        sys.exit(f'No existe {entorno}/bin/python (usa --crear o apunta a un entorno ya hecho)')

    for paso in C.PASOS:
        cwd = {'entorno': copia, 'conda_repo': copia}.get(paso['donde'], fuera)
        for grupo in [paso['cmds']] + [e['cmds'] for e in paso.get('extra', [])]:
            for cmd in grupo:
                texto_cmd = cmd['c']
                if texto_cmd.startswith('cd '):
                    cwd = cwd_tras_cd(cwd, texto_cmd, copia, fuera)
                    continue
                clave = cmd.get('k')
                if not clave and texto_cmd.startswith('git config --global '):
                    # Deja el equipo como lo deja el paso A1 (con la identidad puesta); estos comandos no imprimen nada que mostrar.
                    codigo, texto, _ = correr(texto_cmd, cwd, env)
                    if codigo != 0:
                        sys.exit(f'Fallo {texto_cmd}: {texto}')
                    continue
                if not clave or clave == 'crear_entorno':
                    continue
                linux = texto_cmd.replace('\\', '/')
                print(f'[{clave}] {linux[:90]}', flush=True)
                if clave == 'mlflow_ui':
                    codigo, texto, seg = mlflow_ui(cwd, env, entorno, copia, casa)
                else:
                    codigo, texto, seg = correr(linux, cwd, env)
                salidas[clave] = dict(cmd=linux, codigo=codigo, segundos=round(seg, 1), salida=limpiar(texto, clave, entorno, copia, casa))
                print(f'    -> codigo {codigo}, {seg:.1f} s', flush=True)
    meta['python'] = salidas.get('py_version', {}).get('salida', '')
    fallos = [k for k, v in salidas.items() if v['codigo'] != 0]
    Path(a.salida).write_text(json.dumps({'meta': meta, 'salidas': salidas}, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    shutil.rmtree(base, ignore_errors=True)
    print(f'\n{len(salidas)} salidas guardadas en {a.salida}')
    if fallos:
        sys.exit('Comandos con codigo de salida distinto de 0: ' + ', '.join(fallos))


if __name__ == '__main__':
    main()
