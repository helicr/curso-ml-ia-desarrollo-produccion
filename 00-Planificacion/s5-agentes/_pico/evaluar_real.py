"""Evaluación REAL del agente (no es pytest): Ollama portátil + Qwen2.5-3B + servidor MCP real + datos reales en SOLO LECTURA.
Lanza SOLO su Ollama y lo para por PID al terminar. Escribe el informe en _pico/salidas/evaluacion_3b.json."""
import hashlib
import os
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(r'C:\bk\HC-Cursos\curso-ml-ia-desarrollo-produccion\04-Proyecto-Base')
PICO = Path(r'C:\bk\HC-Cursos\curso-ml-ia-desarrollo-produccion\00-Planificacion\s5-agentes\_pico\salidas')
OLLAMA = Path(r'C:\bk\ollama')
HOST = '127.0.0.1:11435'
SALIDA = PICO / (sys.argv[1] if len(sys.argv) > 1 else 'evaluacion_3b.json')
PYTHON = r'C:\bk\HC-Cursos\.venv-s5-t01\Scripts\python.exe'

import urllib.request  # noqa: E402


def sha(ruta):
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()[:16]


def vivo():
    try:
        return urllib.request.urlopen(f'http://{HOST}/api/tags', timeout=3).status == 200
    except Exception:
        return False


def main():
    protegidos = [BASE / 'data' / 'processed' / 'curso.db', BASE / 'models' / 'referencia.json', BASE / 'models' / 'modelo.joblib']
    antes = {str(p): sha(p) for p in protegidos if p.exists()}
    if vivo():
        sys.exit('Ya hay un Ollama en el puerto: no se toca. Aborto.')
    env = {**os.environ, 'OLLAMA_MODELS': str(OLLAMA / 'modelos'), 'OLLAMA_HOST': HOST, 'OLLAMA_CONTEXT_LENGTH': '8192', 'NO_PROXY': '127.0.0.1,localhost'}
    for k in ('HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy'):
        env.pop(k, None)
    p = subprocess.Popen([str(OLLAMA / 'ollama.exe'), 'serve'], env=env, cwd=str(OLLAMA), stdout=open(OLLAMA / 'eval.out', 'w'), stderr=subprocess.STDOUT)
    print('Ollama lanzado, PID', p.pid, flush=True)
    codigo = 1
    try:
        for _ in range(90):
            if vivo():
                break
            time.sleep(1)
        entorno = {**env, 'CURSO_DB_SOLO_LECTURA': '1', 'PYTHONUTF8': '1', 'MLFLOW_DISABLE_AGENT_HINT': '1',
                   'CURSO_MLFLOW_URI': 'sqlite:///' + (PICO / 'mlflow_eval.db').as_posix()}
        r = subprocess.run([PYTHON, '-m', 'ia_mlops.agente.evaluacion', 'evaluar', '--llm', 'ollama', '--json', str(SALIDA)], cwd=str(BASE), env=entorno)
        codigo = r.returncode
    finally:
        subprocess.run(['taskkill', '/PID', str(p.pid), '/T', '/F'], capture_output=True)
        print('Ollama parado, PID', p.pid)
    despues = {str(q): sha(q) for q in protegidos if q.exists()}
    print('Datos reales intactos:', antes == despues, antes if antes != despues else '')
    sys.exit(codigo)


if __name__ == '__main__':
    main()
