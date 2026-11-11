"""Captura las salidas REALES que muestra la guía de Codespaces y las guarda en salidas-reales.json.

Ejecuta, en una carpeta temporal y con el Python del entorno del curso:
    python -m ia_mlops.pipeline                                (entrena con la muestra)
    uvicorn ia_mlops.api.app:app                               (la API, en el puerto 8080)
    curl http://127.0.0.1:8080/listo
    python -m ia_mlops.modeling.comparar --url http://127.0.0.1:8080

OJO: es la API ejecutada directamente en Linux, NO el contenedor. Lo que la guía dice del contenedor (docker build, run, logs, id -u)
no se captura aquí: se verificó en GitHub Actions y nadie ha abierto todavía un Codespace.

Uso:  python capturar.py [--python /ruta/al/python] [--puerto 8080]
"""
import argparse
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import date
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PROYECTO = AQUI.parents[1] / '04-Proyecto-Base'


def ejecutar(cmd, entorno, limite=300):
    t0 = time.time()
    r = subprocess.run(cmd, cwd=PROYECTO, env=entorno, capture_output=True, text=True, timeout=limite)
    return r, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--python', default=sys.executable)
    ap.add_argument('--puerto', type=int, default=8080)
    a = ap.parse_args()
    url = f'http://127.0.0.1:{a.puerto}'
    with tempfile.TemporaryDirectory() as tmp:
        entorno = dict(os.environ, CURSO_DB=f'{tmp}/curso.db', CURSO_MODELOS=f'{tmp}/models', CURSO_REPORTES=f'{tmp}/reports',
                       MLFLOW_TRACKING_URI=f'sqlite:///{tmp}/mlflow.db', NO_PROXY='127.0.0.1,localhost', no_proxy='127.0.0.1,localhost')
        salidas = {}
        r, seg = ejecutar([a.python, '-m', 'ia_mlops.pipeline'], entorno)
        if r.returncode:
            sys.exit('El pipeline falló:\n' + r.stdout[-1500:] + r.stderr[-1500:])
        lineas = [l.replace(tmp, '…') for l in r.stdout.splitlines() if l.strip()]      # la carpeta temporal no dice nada al lector
        salidas['pipeline'] = {'comando': 'python -m ia_mlops.pipeline', 'segundos': round(seg, 1), 'ultimas_lineas': lineas[-8:],
                               'carpetas': sorted(p.name for p in Path(entorno['CURSO_MODELOS']).iterdir())}
        srv = subprocess.Popen([a.python, '-m', 'uvicorn', 'ia_mlops.api.app:app', '--host', '127.0.0.1', '--port', str(a.puerto)],
                               cwd=PROYECTO, env=entorno, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            for _ in range(60):
                try:
                    urllib.request.urlopen(f'{url}/salud', timeout=2).read()
                    break
                except Exception:
                    time.sleep(1)
            else:
                sys.exit('La API no arrancó')
            r, _ = ejecutar(['curl', '-s', f'{url}/listo'], entorno)
            salidas['listo'] = {'comando': f'curl {url}/listo', 'salida': r.stdout.strip()}
            r, seg = ejecutar([a.python, '-m', 'ia_mlops.modeling.comparar', '--url', url], entorno)
            if r.returncode:
                sys.exit('comparar falló:\n' + r.stdout + r.stderr)
            salidas['comparar'] = {'comando': f'python -m ia_mlops.modeling.comparar --url {url}', 'segundos': round(seg, 1),
                                   'salida': r.stdout.strip(), 'aviso_stderr': bool(r.stderr.strip())}
        finally:
            srv.terminate()
            srv.wait(timeout=10)
    meta = {'fecha': date.today().isoformat(), 'sistema': platform.platform(), 'python': platform.python_version(),
            'nota': 'API ejecutada directamente con uvicorn en Linux; no es el contenedor.'}
    (AQUI / 'salidas-reales.json').write_text(json.dumps({'meta': meta, 'salidas': salidas}, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps(salidas, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
