"""python -m ia_mlops.interfaz [--url http://127.0.0.1:8080] [--puerto 8090] [--host 127.0.0.1]"""
import argparse

import uvicorn

from .. import config
from .app import crear_app


def main(argv=None):
    ap = argparse.ArgumentParser(description='Interfaz web: ids de cliente -> probabilidad de recompra y recomendación.')
    ap.add_argument('--url', default=config.URL_API,
                    help='URL de la API del modelo (p. ej. http://127.0.0.1:8080). Sin ella, usa el modelo de models/ directamente.')
    ap.add_argument('--puerto', type=int, default=8090)
    ap.add_argument('--host', default='127.0.0.1', help='0.0.0.0 para abrirla desde fuera (contenedor o Codespace)')
    a = ap.parse_args(argv)
    print(f'Interfaz en http://{a.host}:{a.puerto} · predicciones: {a.url or "modelo local (models/)"}')
    uvicorn.run(crear_app(url_api=a.url or ''), host=a.host, port=a.puerto)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
