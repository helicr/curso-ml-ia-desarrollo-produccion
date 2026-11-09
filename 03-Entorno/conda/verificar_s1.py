"""Verificador de la sesion S0 -> S1: comprueba que tu equipo esta listo para empezar la S1.

Complementa a prueba_de_humo.py (que importa las librerias y recorre un mini ciclo de ML): este programa mira el resto de lo que hace falta
para S1 y te dice, para cada cosa que falla, que hacer.

Uso (con el entorno activo, desde cualquier carpeta del repositorio):
    conda activate env-ia-mlops
    python 03-Entorno/conda/verificar_s1.py                  # comprobaciones rapidas (unos segundos)
    python 03-Entorno/conda/verificar_s1.py --con-pruebas    # ademas ejecuta las pruebas del proyecto base (1-2 minutos)
    python 03-Entorno/conda/verificar_s1.py --informe        # ademas guarda verificacion-s1.txt para enviarlo al instructor
    python 03-Entorno/conda/verificar_s1.py --sin-conda      # si usas pip + venv (Codespaces): no exige el nombre del entorno

Resultado de cada linea:  OK = bien · AVISO = revisalo, pero no te bloquea · FALLA = arreglalo antes de S1.
Termina con «LISTO PARA S1» (codigo de salida 0) o «NO LISTO PARA S1» (codigo 1).

No necesita Internet ni cuentas. Escribe solo en una carpeta temporal (y en verificacion-s1.txt si usas --informe).
El informe NO incluye tu nombre de usuario (las rutas de tu carpeta personal se sustituyen por «~») ni tu correo de Git.
Los textos no llevan tildes a proposito: algunas consolas de Windows las muestran mal.
"""
import argparse
import hashlib
import importlib
import importlib.metadata as metadatos
import logging
import os
import platform
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]            # <repo>/03-Entorno/conda/verificar_s1.py
ENTORNO = 'env-ia-mlops'
PYTHON_ESPERADO = (3, 11)
OK, AVISO, FALLA = 'OK', 'AVISO', 'FALLA'
SQLITE_MINIMA = (3, 25, 0)                            # funciones de ventana (row_number() over ...) que usa el caso
DISCO_AVISO_GB, DISCO_FALLA_GB = 3.0, 1.0
MODULOS_CLAVE = ['numpy', 'pandas', 'sklearn', 'pyarrow', 'matplotlib', 'mlflow', 'papermill', 'jupytext', 'nbformat', 'nbclient',
                 'fastapi', 'pytest']
# Nombre del paquete de conda -> nombre con el que lo ve Python (solo los que difieren o hay que traducir).
NOMBRE_EN_PYTHON = {'pyyaml': 'PyYAML'}
SIN_VERSION_EN_PYTHON = {'python'}                    # lo fija conda, no es un paquete de Python


# ------------------------------------------------------------------ piezas puras (se prueban en pruebas/test_verificar_s1.py)
def leer_versiones_fijadas(texto):
    """Lee las lineas «  - paquete=version» de un environment.yml. Devuelve {paquete: version}. Ignora comentarios y lo que no fija version."""
    fijadas = {}
    for linea in texto.splitlines():
        linea = linea.split('#', 1)[0].rstrip()
        m = re.match(r'^\s*-\s*([A-Za-z0-9_.\-]+)\s*={1,2}\s*([A-Za-z0-9_.\-+!]+)\s*$', linea)
        if m and m.group(1).lower() not in SIN_VERSION_EN_PYTHON:
            fijadas[m.group(1)] = m.group(2)
    return fijadas


def comparar_versiones(fijadas, version_de):
    """version_de(nombre) -> version instalada o None. Devuelve (faltan, distintas): listas de nombres y de (nombre, instalada, esperada)."""
    faltan, distintas = [], []
    for nombre, esperada in sorted(fijadas.items()):
        instalada = version_de(NOMBRE_EN_PYTHON.get(nombre.lower(), nombre))
        if instalada is None:
            faltan.append(nombre)
        elif instalada != esperada:
            distintas.append((nombre, instalada, esperada))
    return faltan, distintas


def version_instalada(nombre):
    try:
        return metadatos.version(nombre)
    except metadatos.PackageNotFoundError:
        return None


def leer_sumas(texto):
    """Lee un SHA256SUMS («huella  ruta»). Devuelve {ruta: huella}."""
    sumas = {}
    for linea in texto.splitlines():
        partes = linea.strip().split(None, 1)
        if len(partes) == 2 and re.fullmatch(r'[0-9a-f]{64}', partes[0]):
            sumas[partes[1].lstrip('*').replace('\\', '/')] = partes[0]
    return sumas


def huella(ruta):
    h = hashlib.sha256()
    with open(ruta, 'rb') as f:
        for bloque in iter(lambda: f.read(1 << 20), b''):
            h.update(bloque)
    return h.hexdigest()


def enmascarar(texto, casa=None):
    """Sustituye la carpeta personal por «~» para no dar el nombre de usuario en el informe."""
    casa = str(casa or Path.home())
    for variante in {casa, casa.replace('\\', '/'), casa.replace('/', '\\')}:
        if variante and variante not in ('/', '\\'):
            texto = texto.replace(variante, '~')
    return texto


def veredicto(resultados):
    n = {OK: 0, AVISO: 0, FALLA: 0}
    for estado, *_ in resultados:
        n[estado] += 1
    listo = n[FALLA] == 0
    return listo, f"Resultado: {'LISTO PARA S1' if listo else 'NO LISTO PARA S1'}  ({n[OK]} OK, {n[AVISO]} AVISO, {n[FALLA]} FALLA)"


# ------------------------------------------------------------------ comprobaciones: cada una devuelve [(estado, titulo, detalle, que_hacer)]
def c_python(_):
    v = sys.version_info[:2]
    if v == PYTHON_ESPERADO:
        return [(OK, 'python', platform.python_version(), '')]
    return [(FALLA, 'python', f'es {platform.python_version()} y el curso usa {PYTHON_ESPERADO[0]}.{PYTHON_ESPERADO[1]}',
             f'Activa el entorno del curso:  conda activate {ENTORNO}   (y mira que el prompt empiece por ({ENTORNO}))')]


def c_entorno(args):
    nombre = Path(sys.prefix).name
    if nombre == ENTORNO:
        return [(OK, 'entorno', ENTORNO, '')]
    ayuda = (f'Activa el entorno:  conda activate {ENTORNO}.  Si aun no existe:  conda env create -f 03-Entorno\\conda\\environment.yml')
    if args.sin_conda:
        return [(AVISO, 'entorno', f'usas «{nombre}» (se omite la exigencia por --sin-conda)', '')]
    return [(FALLA, 'entorno', f'estas en «{nombre}», no en {ENTORNO}', ayuda)]


def c_paquetes(_):
    yml = RAIZ / '03-Entorno' / 'conda' / 'environment.yml'
    if not yml.exists():
        return [(FALLA, 'paquetes', 'no encuentro 03-Entorno/conda/environment.yml', 'Ejecuta este programa dentro del repositorio del curso (ver «repositorio»)')]
    fijadas = leer_versiones_fijadas(yml.read_text(encoding='utf-8'))
    faltan, distintas = comparar_versiones(fijadas, version_instalada)
    resultados = []
    if faltan:
        resultados.append((FALLA, 'paquetes', f'faltan {len(faltan)} de {len(fijadas)}: ' + ', '.join(faltan),
                           'El entorno quedo incompleto. Prueba:  conda env update -f 03-Entorno\\conda\\environment.yml --prune   '
                           'Si sigue igual, rehazlo:  conda deactivate,  conda env remove -n env-ia-mlops -y,  conda env create -f 03-Entorno\\conda\\environment.yml'))
    if distintas:
        det = '; '.join(f'{n} {i} (esperada {e})' for n, i, e in distintas[:6]) + (' ...' if len(distintas) > 6 else '')
        # `conda env update --prune` NO revierte lo que cambio pip (comprobado): hace falta reinstalar ese paquete con conda.
        orden = 'conda install --force-reinstall ' + ' '.join(f'{n}={e}' for n, _, e in distintas[:6]) + (' ...' if len(distintas) > 6 else '')
        resultados.append((AVISO, 'paquetes', f'{len(distintas)} con otra version: {det}',
                           f'Puede ser un pip install posterior. Para volver a lo fijado:  {orden}   (o rehaz el entorno: ver «paquetes» cuando faltan)'))
    if not faltan and not distintas:
        resultados.append((OK, 'paquetes', f'{len(fijadas)} paquetes con la version fijada en environment.yml', ''))
    return resultados


def c_importaciones(_):
    fallan = []
    t0 = time.monotonic()
    for nombre in MODULOS_CLAVE:
        try:
            importlib.import_module(nombre)
        except Exception as error:  # noqa: BLE001 - cualquier fallo al importar es informacion util
            fallan.append(f'{nombre} ({type(error).__name__}: {str(error)[:60]})')
    if fallan:
        return [(FALLA, 'importaciones', 'no se pueden importar: ' + '; '.join(fallan), 'Rehaz el entorno (ver «paquetes») y vuelve a probar')]
    return [(OK, 'importaciones', f'{len(MODULOS_CLAVE)} librerias clave se importan ({time.monotonic() - t0:.1f} s)', '')]


def c_sqlite(_):
    version = sqlite3.sqlite_version
    partes = tuple(int(x) for x in version.split('.')[:3])
    try:
        con = sqlite3.connect(':memory:')
        filas = con.execute('select x, row_number() over (order by x) from (select 3 as x union select 1 union select 2)').fetchall()
        con.close()
        ok_ventana = filas == [(1, 1), (2, 2), (3, 3)]
    except sqlite3.Error as error:
        return [(FALLA, 'sqlite', f'version {version}; falla una consulta con funciones de ventana: {error}', 'Rehaz el entorno: trae su propio SQLite')]
    if partes < SQLITE_MINIMA or not ok_ventana:
        return [(FALLA, 'sqlite', f'version {version} (hace falta 3.25 o mas)', 'Rehaz el entorno: trae su propio SQLite')]
    return [(OK, 'sqlite', f'version {version}; consultas con funciones de ventana correctas', '')]


def c_mlflow(_):
    try:
        import mlflow
        from mlflow.tracking import MlflowClient
        logging.getLogger('mlflow').setLevel(logging.WARNING)      # sin los INFO de creacion de tablas
        logging.getLogger('alembic').setLevel(logging.WARNING)
        with tempfile.TemporaryDirectory(prefix='verif-mlflow-', ignore_cleanup_errors=True) as carpeta:   # Windows no borra una base abierta
            uri = 'sqlite:///' + (Path(carpeta) / 'mlflow.db').as_posix()
            mlflow.set_tracking_uri(uri)
            exp = mlflow.set_experiment('verificar-s1')
            with mlflow.start_run() as run:
                mlflow.log_param('p', 1)
                mlflow.log_metric('m', 0.5)
            leida = MlflowClient(tracking_uri=uri).get_run(run.info.run_id)
            ok = leida.data.params == {'p': '1'} and leida.data.metrics.get('m') == 0.5 and exp.name == 'verificar-s1'
        if not ok:
            return [(FALLA, 'mlflow', 'se guardo una ejecucion pero lo leido no coincide', 'Rehaz el entorno')]
        return [(OK, 'mlflow', f'version {mlflow.__version__}; guarda y lee una ejecucion en SQLite', '')]
    except Exception as error:  # noqa: BLE001
        return [(FALLA, 'mlflow', f'{type(error).__name__}: {str(error)[:100]}', 'Copia el mensaje completo y envialo al instructor')]


def c_kernel(_):
    try:
        from jupyter_client.kernelspec import KernelSpecManager
        specs = KernelSpecManager().find_kernel_specs()
    except Exception as error:  # noqa: BLE001
        return [(FALLA, 'kernel', f'no se pudo consultar Jupyter: {type(error).__name__}', 'Rehaz el entorno')]
    if ENTORNO in specs:
        return [(OK, 'kernel', f'kernel «{ENTORNO}» registrado', '')]
    propio = [n for n, ruta in specs.items() if Path(ruta).resolve().is_relative_to(Path(sys.prefix).resolve())]
    if propio:
        return [(OK, 'kernel', f'el entorno trae su kernel «{propio[0]}» (VS Code lo encuentra al elegir el entorno)', '')]
    return [(AVISO, 'kernel', f'no hay un kernel «{ENTORNO}» registrado',
             f'Si VS Code no lista el entorno al elegir kernel:  python -m ipykernel install --user --name {ENTORNO} --display-name {ENTORNO}')]


def _git(*argumentos):
    return subprocess.run(['git', *argumentos], capture_output=True, text=True, timeout=30)


def c_git(_):
    if shutil.which('git') is None:
        return [(FALLA, 'git', 'no se encuentra «git» en esta terminal', 'Instalalo (winget install --id Git.Git -e) y abre una terminal NUEVA')]
    resultados = [(OK, 'git', _git('--version').stdout.strip(), '')]
    faltan = [c for c, nombre in (('user.name', 'nombre'), ('user.email', 'correo')) if not _git('config', '--get', c).stdout.strip()]
    if faltan:
        resultados.append((AVISO, 'git: identidad', 'falta ' + ' y '.join(faltan),
                           'git config --global user.name "Tu Nombre"   y   git config --global user.email "tu@correo.com"'))
    else:
        resultados.append((OK, 'git: identidad', 'nombre y correo configurados (no se muestran)', ''))
    return resultados


def c_repositorio(_):
    marcas = ['03-Entorno/conda/environment.yml', '04-Proyecto-Base/pyproject.toml', '02-Proyecto-Transversal/datos/bank-marketing/bank-additional-full.csv']
    faltan = [m for m in marcas if not (RAIZ / m).exists()]
    resultados = []
    if faltan:
        resultados.append((FALLA, 'repositorio', 'faltan: ' + ', '.join(faltan),
                           'Clona el repositorio y usa la rama que tiene el material:  git clone --branch develop https://github.com/helicr/curso-ml-ia-desarrollo-produccion.git'))
    else:
        resultados.append((OK, 'repositorio', 'material del curso completo en la carpeta clonada', ''))
    ruta = str(RAIZ)
    if len(ruta) > 80 or ' ' in ruta or 'onedrive' in ruta.lower():
        resultados.append((AVISO, 'ruta del repositorio', 'es larga, tiene espacios o esta dentro de OneDrive',
                           'En Windows eso da errores de rutas largas. Clona en una carpeta corta, por ejemplo C:\\cursos'))
    return resultados


def c_dato(_):
    csv = RAIZ / '02-Proyecto-Transversal' / 'datos' / 'bank-marketing' / 'bank-additional-full.csv'
    sumas_ruta = RAIZ / '02-Proyecto-Transversal' / 'datos' / 'SHA256SUMS'
    if not csv.exists() or not sumas_ruta.exists():
        return [(FALLA, 'dato Bank Marketing', 'no encuentro el CSV o SHA256SUMS', 'Revisa la clonacion (ver «repositorio»)')]
    esperada = leer_sumas(sumas_ruta.read_text(encoding='utf-8')).get('bank-marketing/bank-additional-full.csv')
    obtenida = huella(csv)
    with open(csv, 'rb') as f:
        lineas = sum(bloque.count(b'\n') for bloque in iter(lambda: f.read(1 << 20), b''))
    if esperada is None:
        return [(FALLA, 'dato Bank Marketing', 'SHA256SUMS no trae la huella de este archivo', 'Avisa al instructor')]
    if obtenida != esperada:
        return [(FALLA, 'dato Bank Marketing', f'la huella no coincide ({lineas} saltos de linea): el archivo se ha modificado',
                 'Vuelve a descargarlo del repositorio:  git restore 02-Proyecto-Transversal/datos/bank-marketing/bank-additional-full.csv   (no lo abras y guardes con Excel)')]
    return [(OK, 'dato Bank Marketing', f'huella correcta; {lineas - 1} filas de datos (+ encabezado)', '')]


def c_disco(_):
    libre = shutil.disk_usage(RAIZ if RAIZ.exists() else Path.cwd()).free / 1e9
    if libre < DISCO_FALLA_GB:
        return [(FALLA, 'disco', f'{libre:.1f} GB libres', 'Libera espacio (conda clean --all) antes de continuar')]
    if libre < DISCO_AVISO_GB:
        return [(AVISO, 'disco', f'{libre:.1f} GB libres (recomendado: {DISCO_AVISO_GB:.0f} GB o mas)', 'Libera espacio:  conda clean --all')]
    return [(OK, 'disco', f'{libre:.0f} GB libres', '')]


def puerto_en_uso(puerto=5000):
    """True si algun programa esta escuchando en ese puerto de este equipo.
    Se prueba con una conexion y no con bind(): tras cerrar un programa, el sistema deja el puerto en TIME_WAIT unos segundos y bind() falla aunque nadie escuche (falso aviso)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(('127.0.0.1', puerto)) == 0


def c_puerto(_):
    if puerto_en_uso(5000):
        return [(AVISO, 'puerto 5000', 'ocupado (lo necesita «mlflow ui» por defecto)', 'Usa otro puerto:  mlflow ui --port 5001 --backend-store-uri sqlite:///mlflow.db')]
    return [(OK, 'puerto 5000', 'libre para «mlflow ui»', '')]


def c_pruebas(_):
    base = RAIZ / '04-Proyecto-Base'
    if not base.exists():
        return [(FALLA, 'pruebas del proyecto base', 'no existe 04-Proyecto-Base', 'Revisa la clonacion (ver «repositorio»)')]
    t0 = time.monotonic()
    p = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-m', 'not lento', '-p', 'no:cacheprovider'], cwd=base, capture_output=True, text=True, timeout=900)
    lineas = p.stdout.strip().splitlines()
    resumen = [x for x in lineas if re.search(r'\b\d+ (passed|failed|error)', x)]      # «30 passed, 4 deselected in 8.5s»
    ultima = (resumen or lineas or [''])[-1].strip('= ')
    if p.returncode == 0:
        return [(OK, 'pruebas del proyecto base', f'{ultima} ({time.monotonic() - t0:.0f} s)', '')]
    return [(FALLA, 'pruebas del proyecto base', ultima or 'no se ejecuto', 'Ejecuta  cd 04-Proyecto-Base  y  python -m pytest -q -m "not lento"  y envia el mensaje completo')]


COMPROBACIONES = [c_python, c_entorno, c_paquetes, c_importaciones, c_sqlite, c_mlflow, c_kernel, c_git, c_repositorio, c_dato, c_disco, c_puerto]


def ejecutar(args):
    resultados = []
    comprobaciones = COMPROBACIONES + ([c_pruebas] if args.con_pruebas else [])
    for comprobar in comprobaciones:
        try:
            resultados += comprobar(args)
        except Exception as error:  # noqa: BLE001 - una comprobacion rota no debe esconder las demas
            resultados.append((FALLA, comprobar.__name__[2:], f'la comprobacion fallo: {type(error).__name__}: {str(error)[:80]}', 'Envia este mensaje al instructor'))
    return resultados


def formatear(resultados, args):
    lineas = [f'Verificacion para S1 - {time.strftime("%Y-%m-%d %H:%M")} - {platform.system()} {platform.release()} - Python {platform.python_version()}',
              f'Entorno: {Path(sys.prefix).name}   Repositorio: {RAIZ.name}', '']
    for estado, titulo, detalle, que_hacer in resultados:
        lineas.append(f'  [{estado:<5}] {titulo:<26} {detalle}')
        if estado != OK and que_hacer:
            lineas.append(f'          -> que hacer: {que_hacer}')
    if {'python', 'entorno'} & {titulo for estado, titulo, *_ in resultados if estado == FALLA}:
        lineas += ['', 'Pista: empieza por arreglar «python» y «entorno» (activar env-ia-mlops). Casi todos los demas fallos son consecuencia de no estar en el entorno.']
    lineas += ['', veredicto(resultados)[1]]
    return enmascarar('\n'.join(lineas))


def main(argv=None):
    ap = argparse.ArgumentParser(description='Comprueba que tu equipo esta listo para la S1.')
    ap.add_argument('--con-pruebas', action='store_true', help='ejecuta tambien las pruebas rapidas del proyecto base (1-2 minutos)')
    ap.add_argument('--informe', action='store_true', help='guarda el resultado en verificacion-s1.txt (sin tu usuario ni tu correo)')
    ap.add_argument('--sin-conda', action='store_true', help='no exige que el entorno se llame env-ia-mlops (pip + venv, Codespaces)')
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(errors='replace')
    resultados = ejecutar(args)
    texto = formatear(resultados, args)
    print(texto)
    if args.informe:
        Path('verificacion-s1.txt').write_text(texto + '\n', encoding='utf-8')
        print('\nInforme guardado en verificacion-s1.txt (en la carpeta actual). Enviaselo al instructor si algo no se resuelve.')
    return 0 if veredicto(resultados)[0] else 1


if __name__ == '__main__':
    sys.exit(main())
