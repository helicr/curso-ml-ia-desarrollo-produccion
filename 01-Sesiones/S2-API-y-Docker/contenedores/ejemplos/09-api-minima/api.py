"""API minima con la biblioteca estandar: lo justo para ver healthcheck, logs y limites de un contenedor."""
import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

MODELO = os.environ.get("MODELO", "v1")


def log(**campos):
    print(json.dumps({"ts": round(time.time(), 3), **campos}, ensure_ascii=False), flush=True)


class Manejador(BaseHTTPRequestHandler):
    def _responder(self, codigo, cuerpo):
        datos = json.dumps(cuerpo).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)
        log(metodo=self.command, ruta=self.path, codigo=codigo)

    def do_GET(self):
        if self.path == "/salud":
            self._responder(200, {"estado": "vivo"})
        elif self.path == "/modelo":
            self._responder(200, {"modelo": MODELO})
        else:
            self._responder(404, {"detalle": "no existe"})

    def log_message(self, *args):  # el registro de acceso por defecto no es JSON: se usa log()
        pass


if __name__ == "__main__":
    puerto = int(os.environ.get("PUERTO", "8080"))
    log(evento="arranque", puerto=puerto, modelo=MODELO)
    HTTPServer(("0.0.0.0", puerto), Manejador).serve_forever()
