"""Aplicacion FastAPI.

Endpoints:
  GET  /salud            ¿el proceso responde?  (liveness; no mira el modelo)
  GET  /listo            ¿el modelo esta cargado? (readiness; 503 si no)
  GET  /modelo           que modelo es: huella de los datos, variables, metricas de validacion
  POST /predecir         probabilidad de UN cliente
  POST /predecir/lote    probabilidad de hasta 1000 clientes

Errores: 422 si el cuerpo no cumple el contrato · 503 si no hay modelo · 500 sin detalles internos (el traceback va al log, no al cliente).
Cada peticion lleva un X-Request-ID y deja una linea de log en JSON (por stdout, ver registro.py) con el tiempo y el codigo; NUNCA se registran los datos del cliente.

Arranque:  uvicorn ia_mlops.api.app:app --port 8080     (o:  make api)
"""
import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from . import esquemas
from .registro import configurar as configurar_registro, registrar
from .servicio import ContratoRoto, ModeloNoDisponible, Servicio


def crear_app(carpeta_modelo=None, campos_contrato=None):
    """Fabrica de la aplicacion. `carpeta_modelo` permite a las pruebas apuntar a un modelo temporal.

    `campos_contrato`: nombres de las variables que acepta la API (por defecto, los campos de esquemas.Cliente); solo lo cambian las pruebas.
    """
    campos = list(campos_contrato) if campos_contrato is not None else list(esquemas.Cliente.model_fields)
    configurar_registro()

    @asynccontextmanager
    async def ciclo(app):
        app.state.servicio, app.state.error_carga = None, None
        try:
            servicio = Servicio.cargar(carpeta_modelo)
            servicio.comprobar_esquema(campos)
            app.state.servicio = servicio
            registrar(logging.INFO, 'modelo cargado', evento='modelo_cargado', huella_datos=app.state.servicio.meta['huella_datos'])
        except (ModeloNoDisponible, ContratoRoto) as e:
            # El proceso sigue vivo: /salud responde y /listo explica por que no esta listo.
            app.state.error_carga = str(e)
            registrar(logging.ERROR, 'modelo no cargado', evento='modelo_no_cargado', motivo=str(e))
        yield

    app = FastAPI(title='Online Retail II · probabilidad de recompra a 90 dias', version='0.1.0', lifespan=ciclo,
                  description='Dado el estado de un cliente en una fecha de corte, ¿que probabilidad hay de que compre en los 90 dias siguientes? Sirve para elegir a quien enviar una campana de retencion.')

    @app.middleware('http')
    async def middleware_registro(request: Request, call_next):
        id_peticion = request.headers.get('x-request-id') or uuid.uuid4().hex[:12]
        request.state.id_peticion = id_peticion
        t0 = time.perf_counter()
        try:
            respuesta = await call_next(request)
        except Exception:      # noqa: BLE001 - ultima red de seguridad: el detalle va al log, no al cliente
            registrar(logging.ERROR, 'error no controlado', exc_info=True, evento='error_no_controlado', id=id_peticion)
            respuesta = JSONResponse(status_code=500, content={'detalle': 'Error interno', 'id_peticion': id_peticion})
        respuesta.headers['X-Request-ID'] = id_peticion
        registrar(logging.INFO, f'{request.method} {request.url.path} {respuesta.status_code}', evento='peticion', id=id_peticion,
                  metodo=request.method, ruta=request.url.path, codigo=respuesta.status_code, ms=round(1000 * (time.perf_counter() - t0), 1))
        return respuesta

    def servicio_listo(request: Request):
        s = request.app.state.servicio
        if s is None:
            raise ModeloNoDisponible(request.app.state.error_carga or 'El modelo no esta cargado')
        return s

    @app.exception_handler(ModeloNoDisponible)
    async def sin_modelo(request: Request, exc: ModeloNoDisponible):
        return JSONResponse(status_code=503, content={'detalle': str(exc), 'id_peticion': getattr(request.state, 'id_peticion', None)})

    @app.get('/salud')
    def salud():
        return {'estado': 'ok'}

    @app.get('/listo', responses={503: {'model': esquemas.Error}})
    def listo(request: Request):
        servicio_listo(request)
        return {'estado': 'listo'}

    @app.get('/modelo', response_model=esquemas.InfoModelo, responses={503: {'model': esquemas.Error}})
    def modelo(request: Request):
        return servicio_listo(request).info()

    def _prediccion(servicio, probabilidad, advertencias):
        return esquemas.Prediccion(probabilidad=probabilidad, modelo=servicio.meta['modelo'], huella_datos=servicio.meta['huella_datos'],
                                   advertencias=advertencias)

    @app.post('/predecir', response_model=esquemas.Prediccion, responses={503: {'model': esquemas.Error}})
    def predecir(cliente: esquemas.Cliente, request: Request):
        s = servicio_listo(request)
        (p, avisos), = s.predecir([cliente.model_dump()])
        return _prediccion(s, p, avisos)

    @app.post('/predecir/lote', response_model=esquemas.PrediccionLote, responses={503: {'model': esquemas.Error}})
    def predecir_lote(lote: esquemas.LoteClientes, request: Request):
        s = servicio_listo(request)
        return {'predicciones': [_prediccion(s, p, a) for p, a in s.predecir([c.model_dump() for c in lote.clientes])]}

    return app


app = crear_app()
