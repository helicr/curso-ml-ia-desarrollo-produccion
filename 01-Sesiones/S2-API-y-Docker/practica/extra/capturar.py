"""Ejecuta el laboratorio extra de S2 de punta a punta y guarda sus salidas REALES en salidas-reales.json.

Lo hace en una carpeta temporal (variables CURSO_*), así no toca los datos ni los modelos de tu proyecto:
    operacional (muestra) → los cuatro pipelines uno a uno → otra vez (idempotencia) → registro de control → MLflow
    → API con uvicorn → /listo y /modelo → explotación por la API y en local → datos nuevos (--fuente completo)
    → la versión 2 del modelo → API reiniciada → nueva campaña comparada con la primera.

Uso (desde la raíz del repositorio, con el entorno env-ia-mlops activado):
    python 01-Sesiones/S2-API-y-Docker/practica/extra/capturar.py [--sin-completo] [--puerto 8090]
--sin-completo se salta el paso de datos nuevos (necesita el Excel de UCI: python -m ia_mlops.dataset descargar).
"""
import argparse
import json
import os
import platform
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import date
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[3]
PROYECTO = RAIZ / '04-Proyecto-Base'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--puerto', type=int, default=8090)
    ap.add_argument('--sin-completo', action='store_true')
    a = ap.parse_args()
    url = f'http://127.0.0.1:{a.puerto}'
    tmp = Path(tempfile.mkdtemp(prefix='lab-extra-'))
    entorno = dict(os.environ, CURSO_DB_OPERACIONAL=str(tmp / 'retail.db'), CURSO_DB=str(tmp / 'curso.db'),
                   CURSO_MODELOS=str(tmp / 'models'), CURSO_REPORTES=str(tmp / 'reports'), PYTHONIOENCODING='utf-8',
                   NO_PROXY='127.0.0.1,localhost', no_proxy='127.0.0.1,localhost', MLFLOW_DISABLE_AGENT_HINT='1')
    # el Excel completo se lee de su sitio (data/raw/online_retail_ii/); solo las bases, modelos y reportes van a la carpeta temporal
    salidas = {}

    def paso(clave, *args, limite=1800):
        t0 = time.time()
        r = subprocess.run([sys.executable, '-m', *args], cwd=PROYECTO, env=entorno, capture_output=True, text=True,
                           encoding='utf-8', timeout=limite)
        seg = round(time.time() - t0, 1)
        lineas = [l.replace(str(tmp), '…') for l in r.stdout.splitlines() if l.strip()]
        comando = ('python -m ' + ' '.join(args)).replace(str(tmp), '…')         # la carpeta temporal lleva el usuario de Windows
        salidas[clave] = {'comando': comando, 'codigo': r.returncode, 'segundos': seg, 'salida': lineas}
        print(f'[{r.returncode}] {seg:7.1f} s  python -m {" ".join(args)}')
        if r.returncode:
            print(r.stdout[-2000:], r.stderr[-3000:])
            sys.exit(f'falló: {clave}')
        return lineas

    def control():
        con = sqlite3.connect(tmp / 'curso.db')
        filas = con.execute('SELECT pipeline, substr(huella_entrada,1,12), ejecutado_en FROM control_pipelines ORDER BY ejecutado_en').fetchall()
        con.close()
        return [list(f) for f in filas]

    def api():
        log = open(tmp / f'uvicorn-{time.time():.0f}.log', 'w')
        p = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'ia_mlops.api.app:app', '--host', '127.0.0.1', '--port', str(a.puerto)],
                             cwd=PROYECTO, env=entorno, stdout=log, stderr=subprocess.STDOUT)
        for _ in range(120):
            try:
                urllib.request.urlopen(f'{url}/listo', timeout=2).read()
                return p, log
            except Exception:       # noqa: BLE001
                time.sleep(0.5)
        sys.exit('la API no arrancó')

    def get(ruta):
        return json.loads(urllib.request.urlopen(f'{url}{ruta}', timeout=10).read().decode('utf-8'))

    try:
        paso('operacional', 'ia_mlops.operacional')
        for nombre in ('pipeline_ingesta_raw', 'pipeline_ingesta_master', 'pipeline_ml', 'pipeline_train'):
            paso(nombre, f'ia_mlops.{nombre}')
        paso('pipeline_otra_vez', 'ia_mlops.pipeline')
        salidas['control_tras_muestra'] = control()
        paso('mlflow_v1', 'ia_mlops.mlflow_ui', '--comprobar')

        p, log = api()
        salidas['listo_v1'] = get('/listo')
        m = get('/modelo')
        salidas['modelo_v1'] = {k: m[k] for k in ('modelo', 'huella_datos', 'entrenado_en', 'filas')}
        paso('explotacion_api_v1', 'ia_mlops.explotacion', '--url', url)
        p.terminate(); p.wait(timeout=10); log.close()
        paso('explotacion_local_v1', 'ia_mlops.explotacion', '--top', '5')
        corte_v1 = json.loads(next((tmp / 'reports' / 'campana').glob('campana_*.json')).read_text(encoding='utf-8'))['corte']
        copia_v1 = tmp / f'campana_{corte_v1}_v1.csv'
        shutil.copy(tmp / 'reports' / 'campana' / f'campana_{corte_v1}.csv', copia_v1)

        if not a.sin_completo:
            paso('datos_nuevos', 'ia_mlops.pipeline', '--fuente', 'completo')
            salidas['control_tras_completo'] = control()
            paso('mlflow_v2', 'ia_mlops.mlflow_ui', '--comprobar')
            p, log = api()
            m = get('/modelo')
            salidas['modelo_v2'] = {k: m[k] for k in ('modelo', 'huella_datos', 'entrenado_en', 'filas')}
            paso('explotacion_api_v2', 'ia_mlops.explotacion', '--url', url, '--comparar-con', str(copia_v1))
            p.terminate(); p.wait(timeout=10); log.close()
    finally:
        meta = {'fecha': date.today().isoformat(), 'sistema': platform.platform(), 'python': platform.python_version(),
                'nota': 'Carpeta temporal con CURSO_*; API con uvicorn (sin contenedor).'}
        (AQUI / 'salidas-reales.json').write_text(json.dumps({'meta': meta, 'salidas': salidas}, ensure_ascii=False, indent=1), encoding='utf-8')
        print('salidas en', AQUI / 'salidas-reales.json', '· temporal', tmp)


if __name__ == '__main__':
    main()
