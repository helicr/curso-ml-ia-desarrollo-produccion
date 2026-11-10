"""Pruebas de la herramienta que compara probabilidades entre el paquete, joblib, MLflow y la API (S2)."""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from ia_mlops import config
from ia_mlops.modeling import comparar, predict


def test_sin_api_compara_paquete_joblib_y_mlflow(carpeta_modelo, ruta_db):
    filas, n, tol = comparar.comparar(n=50, carpeta=carpeta_modelo, ruta_db=ruta_db)
    assert n == 50
    assert [f['camino'] for f in filas] == ['paquete (referencia)', 'joblib', 'MLflow']
    assert all(f['coincide'] and f['filas'] == 50 for f in filas)
    assert max(f['diferencia_maxima'] for f in filas) <= tol


def test_con_la_api_real_en_otro_proceso_tambien_coincide(carpeta_modelo, ruta_db, arrancar_servidor):
    puerto, _ = arrancar_servidor(carpeta_modelo)
    filas, n, _ = comparar.comparar(n=120, url=f'http://127.0.0.1:{puerto}', carpeta=carpeta_modelo, ruta_db=ruta_db)
    assert n == 120 and len(filas) == 4
    assert filas[3]['camino'].startswith('API http://127.0.0.1:')
    assert filas[3]['filas'] == 120 and filas[3]['coincide'], filas[3]


def test_main_devuelve_0_y_lo_cuenta_en_pantalla(carpeta_modelo, ruta_db, monkeypatch, capsys):
    monkeypatch.setattr(config, 'DB', ruta_db)
    assert comparar.main(['--n', '20']) == 0
    salida = capsys.readouterr().out
    assert '20 filas reales' in salida and 'coincide' in salida and 'DIFIERE' not in salida


class _ApiQueMiente(BaseHTTPRequestHandler):
    """Imita /predecir/lote pero suma una pequena diferencia: simula un servicio distinto del modelo entrenado."""
    delta = 1e-6

    def do_POST(self):      # noqa: N802 - nombre fijado por http.server
        cuerpo = json.loads(self.rfile.read(int(self.headers['content-length'])))
        n = len(cuerpo['clientes'])
        # las probabilidades correctas se calculan con el mismo paquete que usa la herramienta
        import pandas as pd
        df = pd.DataFrame(cuerpo['clientes'])
        p = predict.predecir_probabilidad(df, ruta=self.server.carpeta)
        respuesta = json.dumps({'predicciones': [{'probabilidad': min(1.0, x + self.delta), 'modelo': 'x', 'huella_datos': 'x', 'advertencias': []}
                                                 for x in p[:n]]}).encode()
        self.send_response(200)
        self.send_header('content-type', 'application/json')
        self.end_headers()
        self.wfile.write(respuesta)

    def log_message(self, *a):
        pass


def test_detecta_una_api_que_no_da_la_misma_probabilidad(carpeta_modelo, ruta_db, monkeypatch, capsys):
    servidor = HTTPServer(('127.0.0.1', 0), _ApiQueMiente)
    servidor.carpeta = carpeta_modelo
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    try:
        monkeypatch.setattr(config, 'DB', ruta_db)
        codigo = comparar.main(['--n', '30', '--url', f'http://127.0.0.1:{servidor.server_port}'])
    finally:
        servidor.shutdown()
    salida = capsys.readouterr().out
    assert codigo == 1
    assert 'DIFIERE' in salida and 'HAY DIFERENCIAS' in salida


def test_sin_modelo_sin_base_o_con_la_api_apagada_el_codigo_es_2(carpeta_modelo, ruta_db, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(config, 'DB', ruta_db)
    monkeypatch.setattr(config, 'MODELOS', tmp_path / 'no_hay_modelo')
    assert comparar.main([]) == 2
    assert 'No hay modelo' in capsys.readouterr().err
    monkeypatch.setattr(config, 'MODELOS', carpeta_modelo)
    monkeypatch.setattr(config, 'DB', tmp_path / 'no_hay_base.db')
    assert comparar.main([]) == 2
    assert 'No existe la base' in capsys.readouterr().err
    assert not (tmp_path / 'no_hay_base.db').exists()           # y no deja una base vacia como efecto secundario
    monkeypatch.setattr(config, 'DB', ruta_db)
    assert comparar.main(['--url', 'http://127.0.0.1:9']) == 2     # puerto 9 (discard): nadie escucha
    assert 'No se pudo hablar con la API' in capsys.readouterr().err
