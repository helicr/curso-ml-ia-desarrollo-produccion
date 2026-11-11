"""Registro estructurado: una linea JSON por evento, por la salida estandar.

Por que asi: un contenedor (Cloud Run, Kubernetes, `docker logs`) recoge lo que sale por stdout/stderr, y Cloud Logging entiende una
linea JSON: usa `severity` como nivel de la entrada y `message` como texto, y deja el resto de claves como campos consultables.

Sin handler propio, uvicorn NO muestra los logs de la aplicacion (solo configura los suyos) y la raiz esta en WARNING: las lineas
`info` se pierden en silencio. Por eso hay una prueba que arranca uvicorn de verdad y mira su salida (tests/test_api.py).

Nunca se registran datos del cliente: solo metodo, ruta, codigo, duracion e identificador de la peticion.
"""
import json
import logging
import os
import sys

NOMBRE = 'ia_mlops.api'


class _Stdout(logging.StreamHandler):
    """Escribe en el `sys.stdout` del momento (no el del momento de crear el handler): asi funciona tambien con las capturas de pytest."""

    def __init__(self):
        super().__init__()
        self._marca_curso = True

    @property
    def stream(self):
        return sys.stdout

    @stream.setter
    def stream(self, _valor):
        pass


class FormatoJSON(logging.Formatter):
    def format(self, record):
        linea = {'severity': record.levelname, 'message': record.getMessage()}
        linea.update(getattr(record, 'campos', {}))
        if record.exc_info:
            linea['traceback'] = self.formatException(record.exc_info)
        return json.dumps(linea, ensure_ascii=False)


def configurar():
    """Idempotente: se puede llamar en cada `crear_app()` sin duplicar handlers."""
    logger = logging.getLogger(NOMBRE)
    if not any(getattr(h, '_marca_curso', False) for h in logger.handlers):
        handler = _Stdout()
        handler.setFormatter(FormatoJSON())
        logger.addHandler(handler)
    logger.setLevel(os.environ.get('CURSO_LOG_NIVEL', 'INFO').upper())
    return logger


def registrar(nivel, mensaje, exc_info=False, **campos):
    logging.getLogger(NOMBRE).log(nivel, mensaje, exc_info=exc_info, extra={'campos': campos})
