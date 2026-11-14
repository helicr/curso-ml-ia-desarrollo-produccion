"""Interfaz web de consulta: escribir uno o varios ids de cliente (o cargar una lista) y ver probabilidad y recomendación.

Es OTRO servicio, distinto de la API del modelo: la API sirve el modelo (pide las 13 variables); la interfaz conoce el dato
(calcula las variables desde el id) y llama a la API. Así la imagen del modelo sigue sin datos de clientes.

Endpoints:
  GET  /                      la página (HTML sin recursos externos)
  GET  /salud                 ¿el proceso responde?  (liveness; el HEALTHCHECK de la imagen)
  GET  /listo                 ¿llega a los datos y a la API del modelo?  (readiness; 503 con el motivo si no)
  GET  /estado                corte por defecto, origen de las predicciones, modelo y tramos de la recomendación
  POST /recomendar            {"cliente_ids": [12346, 12347], "corte": "2011-12-10"}   (corte opcional; hasta 1000 ids)
  GET  /recomendar/{id}       lo mismo para un cliente  (?corte=AAAA-MM-DD opcional)

Errores: 422 si la petición no tiene sentido · 503 si no hay modelo, no responde la API o falta la base de datos.

Arranque (desde 04-Proyecto-Base, con la API en marcha en otra terminal):
    python -m ia_mlops.interfaz --url http://127.0.0.1:8080        # http://127.0.0.1:8090
    python -m ia_mlops.interfaz                                     # sin API: usa el modelo de models/
"""
import logging
import urllib.error
from typing import Optional

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from .. import config
from ..api.registro import configurar as configurar_registro, registrar
from ..api.servicio import ModeloNoDisponible
from . import pagina
from .consulta import MAXIMO_IDS, Consulta, PeticionNoValida


class Peticion(BaseModel):
    model_config = ConfigDict(extra='forbid', json_schema_extra={'examples': [{'cliente_ids': [12346, 12347, 12348], 'corte': None}]})
    cliente_ids: list[int] = Field(min_length=1, max_length=MAXIMO_IDS, description='Ids de cliente (Customer ID); los repetidos se cuentan una vez')
    corte: Optional[str] = Field(default=None, description='Fecha de corte AAAA-MM-DD; por defecto, el día siguiente a la última factura')


def crear_app(ruta_db=None, url_api=None, carpeta_modelo=None):
    """`url_api`: la API del modelo (por defecto CURSO_URL_API); sin ella, el modelo de `carpeta_modelo` (o models/)."""
    configurar_registro()
    consulta = Consulta(ruta_db=ruta_db, url_api=url_api if url_api is not None else config.URL_API, carpeta_modelo=carpeta_modelo)
    app = FastAPI(title='Interfaz de consulta · recompra a 90 días', version='0.1.0',
                  description='Escribe ids de cliente y obtén la probabilidad de recompra en 90 días y una recomendación. '
                              'Las variables se calculan desde el id con el SQL de la capa FS; la predicción la da la API del modelo.')
    app.state.consulta = consulta

    @app.exception_handler(PeticionNoValida)
    async def no_valida(request: Request, exc: PeticionNoValida):
        return JSONResponse(status_code=422, content={'detalle': str(exc)})

    @app.exception_handler(ModeloNoDisponible)
    async def sin_modelo(request: Request, exc: ModeloNoDisponible):
        return JSONResponse(status_code=503, content={'detalle': str(exc)})

    @app.exception_handler(urllib.error.URLError)
    async def sin_api(request: Request, exc: urllib.error.URLError):
        # HTTPError también es URLError: la API respondió con error (p. ej. 503 sin modelo) o no respondió.
        motivo = f'la API respondió {exc.code}' if isinstance(exc, urllib.error.HTTPError) else f'no responde ({exc.reason})'
        registrar(logging.ERROR, 'API del modelo no disponible', evento='api_no_disponible', motivo=motivo)
        return JSONResponse(status_code=503, content={'detalle': f'La API del modelo en {consulta.url_api} {motivo}. ¿Está arrancada y /listo responde?'})

    @app.exception_handler(RuntimeError)
    async def sin_datos(request: Request, exc: RuntimeError):
        # explotacion.py lanza RuntimeError si no existe la capa FS o MASTER está vacío
        return JSONResponse(status_code=503, content={'detalle': str(exc)})

    @app.get('/', response_class=HTMLResponse)
    def inicio():
        return pagina.HTML

    @app.get('/salud')
    def salud():
        """¿El proceso responde? (liveness; lo pregunta el HEALTHCHECK de la imagen). No mira ni los datos ni la API."""
        return {'estado': 'ok'}

    @app.get('/listo')
    def listo():
        """¿Puede atender? Llega a la base (volumen) y a la API del modelo (red). 503 con el motivo si no."""
        return {'estado': 'listo', **consulta.comprobar()}

    @app.get('/estado')
    def estado():
        return consulta.estado()

    @app.post('/recomendar')
    def recomendar(peticion: Peticion):
        r = consulta.recomendar(peticion.cliente_ids, peticion.corte)
        # el registro lleva cuántos, nunca qué clientes
        registrar(logging.INFO, 'consulta', evento='consulta', pedidos=r['pedidos'], encontrados=r['encontrados'], corte=r['corte'])
        return r

    @app.get('/recomendar/{cliente_id}')
    def recomendar_uno(cliente_id: int, corte: Optional[str] = Query(default=None, description='AAAA-MM-DD')):
        return consulta.recomendar([cliente_id], corte)

    return app


app = crear_app()
