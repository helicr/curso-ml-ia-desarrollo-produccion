"""Utilidades de las pruebas: el Airflow FALSO en un hilo, sobre un puerto libre."""
import socket
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path

import pytest

EXTRA = Path(__file__).resolve().parents[1]
for ruta in (EXTRA, EXTRA / 'dags', EXTRA / 'pruebas'):
    if str(ruta) not in sys.path:
        sys.path.insert(0, str(ruta))


def puerto_libre():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


@contextmanager
def airflow_falso(**opciones):
    """Arranca el Airflow falso y da (url, app). Se para al salir."""
    import uvicorn
    from airflow_falso import crear_app
    app = crear_app(**opciones)
    puerto = puerto_libre()
    servidor = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=puerto, log_level='error'))
    hilo = threading.Thread(target=servidor.run, daemon=True)
    hilo.start()
    for _ in range(100):
        if servidor.started:
            break
        time.sleep(0.05)
    assert servidor.started, 'el Airflow falso no arrancó'
    try:
        yield f'http://127.0.0.1:{puerto}', app
    finally:
        servidor.should_exit = True
        hilo.join(timeout=5)


@pytest.fixture
def falso():
    return airflow_falso
