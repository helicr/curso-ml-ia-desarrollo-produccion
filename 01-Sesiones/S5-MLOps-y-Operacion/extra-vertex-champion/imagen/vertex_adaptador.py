"""Adaptador de Vertex AI: sirve el modelo champion de MLflow con el contrato de un contenedor propio de predicción.

QUÉ ES
    Vertex AI llama a un contenedor propio con un contrato muy simple (documentación oficial, «Custom container requirements for
    inference», https://docs.cloud.google.com/vertex-ai/docs/predictions/custom-container-requirements):
        · el servidor escucha en 0.0.0.0 en el puerto de la variable AIP_HTTP_PORT (8080 si no existe);
        · una ruta de SALUD (AIP_HEALTH_ROUTE) que responde 200 cuando el contenedor está listo;
        · una ruta de PREDICCIÓN (AIP_PREDICT_ROUTE) que recibe  {"instances": [...]}  y devuelve  {"predictions": [...]}
          con UNA predicción por instancia.
    Este módulo cumple ese contrato con el modelo que lleva DENTRO de la imagen (no descarga nada de Cloud Storage), así que
    devuelve la PROBABILIDAD (predict_proba), no la clase: es lo que no puede hacer el contenedor pre-construido de scikit-learn
    de la práctica 04 de S4 (que llama a predict()).

ENTRADA  (cada instancia es una LISTA de 13 números en el orden de ia_mlops.config.FEATURES, no un diccionario)
    {"instances": [[35, 6, 1250.4, 208.4, 410, 38, 310, 2, 380.5, 4, 55.0, 1, 1]]}
    · `dias_medios_entre_compras` (posición 11) admite null: es el único campo opcional (clientes de una sola factura).
    · Se aplican las MISMAS reglas que en la API de S2 (ia_mlops.api.esquemas.Cliente): rangos, coherencia entre variables, etc.
SALIDA
    {"predictions": [{"probabilidad": 0.8279, "clase": 1, "tramo": "alta", "version_mlflow": 6}]}
    · clase = 1 si probabilidad >= 0.5 (lo que hace predict() de la regresión logística); tramo = segmento de negocio de
      config.SEGMENTOS_RECOMPRA (alta, media, baja).
    · La versión de MLflow va en cada predicción para saber QUÉ versión contestó cuando hay dos desplegadas con tráfico dividido.
ERRORES
    422 con {"error": ..., "errores": [{"instancia": i, "campo": ..., "mensaje": ...}]} si el cuerpo no cumple el contrato;
    503 si el modelo no se cargó (la ruta de salud también devuelve 503: Vertex no enviará tráfico a un contenedor así);
    500 sin detalles internos. NUNCA se registran los valores de las instancias: solo cuántas, el código y el tiempo.

ARRANQUE
    python vertex_adaptador.py                      (en la imagen)
    CURSO_MODELO_DIR  carpeta con modelo_mlflow/ y vertex-manifiesto.json (por defecto ./modelo junto a este archivo)
"""
import json
import math
import os
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from ia_mlops import config
from ia_mlops.api import esquemas

UMBRAL_CLASE = 0.5
MAX_INSTANCIAS = 1000
MAX_ERRORES = 20
OPCIONALES = ('dias_medios_entre_compras',)         # el único campo que admite null (esquemas.Cliente)
RUTA_SALUD_POR_DEFECTO = '/salud'
RUTA_PREDICT_POR_DEFECTO = '/predict'
NOMBRE_MANIFIESTO = 'vertex-manifiesto.json'
CAMPOS_INFO = ('modelo', 'alias', 'mlflow_version', 'run_id', 'huella_datos', 'valid_auc', 'test_auc', 'version_anterior', 'etiqueta_imagen')


class ModeloNoDisponible(RuntimeError):
    pass


def registrar(nivel, mensaje, **campos):
    """Una línea JSON por stdout (Cloud Logging la entiende: `severity` y `message`). Nunca datos de clientes."""
    print(json.dumps({'severity': nivel, 'message': mensaje, **campos}, ensure_ascii=False), flush=True)


def carpeta_modelo():
    return Path(os.environ.get('CURSO_MODELO_DIR') or Path(__file__).resolve().parent / 'modelo')


# ------------------------------------------------------------------------------------------------ modelo
class Servicio:
    """El modelo cargado, su contrato y los datos de versión del manifiesto."""

    def __init__(self, modelo, variables, manifiesto):
        self.modelo = modelo
        self.variables = variables
        self.manifiesto = manifiesto

    @property
    def version(self):
        return self.manifiesto.get('mlflow_version')

    @classmethod
    def cargar(cls, carpeta):
        carpeta = Path(carpeta)
        ruta = carpeta / config.CARPETA_MODELO_MLFLOW
        if not (ruta / 'MLmodel').exists():
            raise ModeloNoDisponible(f'No hay modelo MLflow en {ruta}.')
        import mlflow.models
        import mlflow.sklearn
        firma = mlflow.models.Model.load(str(ruta)).signature
        if firma is None:
            raise ModeloNoDisponible('El modelo no tiene firma: no se puede comprobar el contrato.')
        variables = [c.name for c in firma.inputs.inputs]
        if variables != list(config.FEATURES) or variables != list(esquemas.Cliente.model_fields):
            raise ModeloNoDisponible(f'La firma del modelo {variables} no coincide con config.FEATURES ni con el esquema de la API.')
        archivo = carpeta / NOMBRE_MANIFIESTO
        manifiesto = json.loads(archivo.read_text(encoding='utf-8')) if archivo.exists() else {}
        return cls(mlflow.sklearn.load_model(str(ruta)), variables, manifiesto)

    def predecir(self, filas):
        """filas: lista de diccionarios ya validados. Devuelve una lista de dicts de predicción (uno por fila)."""
        import pandas as pd
        df = pd.DataFrame(filas)[self.variables]
        df['dias_medios_entre_compras'] = pd.to_numeric(df['dias_medios_entre_compras'], errors='coerce').astype('float64')
        prob = self.modelo.predict_proba(df)[:, 1]
        return [{'probabilidad': float(p), 'clase': int(p >= UMBRAL_CLASE), 'tramo': tramo(float(p)), 'version_mlflow': self.version}
                for p in prob]

    def info(self):
        return {'variables': self.variables, 'umbral_clase': UMBRAL_CLASE, **{k: self.manifiesto.get(k) for k in CAMPOS_INFO}}


def tramo(probabilidad):
    """Segmento de negocio (config.SEGMENTOS_RECOMPRA): el primero cuyo «desde» no supera la probabilidad."""
    for s in config.SEGMENTOS_RECOMPRA:
        if probabilidad >= s['desde']:
            return s['segmento']
    return config.SEGMENTOS_RECOMPRA[-1]['segmento']


# ------------------------------------------------------------------------------------------------ contrato de entrada
def _numero(x):
    """True si x es un número JSON finito (int o float; un bool NO cuenta)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def validar_cuerpo(cuerpo, variables):
    """Devuelve (filas, errores). `filas` = lista de diccionarios {variable: valor}; `errores` = lista de {instancia, campo, mensaje}.

    Si hay errores, `filas` no se debe usar. No lanza excepciones por datos mal formados: los describe.
    """
    if not isinstance(cuerpo, dict) or 'instances' not in cuerpo:
        return [], [{'instancia': None, 'campo': 'instances', 'mensaje': 'El cuerpo debe ser un objeto JSON con la clave "instances".'}]
    instancias = cuerpo['instances']
    if not isinstance(instancias, list) or not instancias:
        return [], [{'instancia': None, 'campo': 'instances', 'mensaje': '"instances" debe ser una lista con al menos una instancia.'}]
    if len(instancias) > MAX_INSTANCIAS:
        return [], [{'instancia': None, 'campo': 'instances', 'mensaje': f'Como máximo {MAX_INSTANCIAS} instancias por petición.'}]
    filas, errores = [], []
    for i, inst in enumerate(instancias):
        if isinstance(inst, dict):
            errores.append({'instancia': i, 'campo': None, 'mensaje': f'Cada instancia debe ser una LISTA de {len(variables)} números en este orden: {", ".join(variables)}. No un diccionario.'})
            continue
        if not isinstance(inst, list) or len(inst) != len(variables):
            errores.append({'instancia': i, 'campo': None, 'mensaje': f'Cada instancia debe ser una lista de {len(variables)} números; esta tiene {len(inst) if isinstance(inst, list) else "otro tipo"}.'})
            continue
        fila, malo = {}, False
        for nombre, valor in zip(variables, inst):
            if valor is None and nombre in OPCIONALES:
                fila[nombre] = None
            elif not _numero(valor):
                errores.append({'instancia': i, 'campo': nombre, 'mensaje': 'Debe ser un número finito' + (' (o null)' if nombre in OPCIONALES else '') + '.'})
                malo = True
            else:
                fila[nombre] = valor
        if malo:
            continue
        try:
            esquemas.Cliente(**fila)
        except ValidationError as e:
            for d in e.errors():
                errores.append({'instancia': i, 'campo': '.'.join(str(p) for p in d['loc']) or None, 'mensaje': d['msg']})
            continue
        filas.append(fila)
    return (filas if not errores else []), errores[:MAX_ERRORES]


# ------------------------------------------------------------------------------------------------ aplicación
def crear_app(carpeta=None, ruta_salud=None, ruta_predict=None):
    """Fábrica. Las rutas salen de AIP_HEALTH_ROUTE y AIP_PREDICT_ROUTE (las pone Vertex según --container-health-route y
    --container-predict-route al subir el modelo); sin ellas se usan /salud y /predict. `carpeta` la cambian las pruebas."""
    ruta_salud = ruta_salud or os.environ.get('AIP_HEALTH_ROUTE') or RUTA_SALUD_POR_DEFECTO
    ruta_predict = ruta_predict or os.environ.get('AIP_PREDICT_ROUTE') or RUTA_PREDICT_POR_DEFECTO
    carpeta = Path(carpeta) if carpeta else carpeta_modelo()

    @asynccontextmanager
    async def ciclo(app):
        app.state.servicio, app.state.error = None, None
        try:
            app.state.servicio = Servicio.cargar(carpeta)
            registrar('INFO', 'modelo cargado', evento='modelo_cargado', mlflow_version=app.state.servicio.version,
                      huella_datos=app.state.servicio.manifiesto.get('huella_datos'))
        except Exception as e:                                              # noqa: BLE001 - el proceso sigue vivo y la salud dice 503
            app.state.error = str(e)
            registrar('ERROR', 'modelo no cargado', evento='modelo_no_cargado', motivo=str(e))
        yield

    app = FastAPI(title='Retención 90 días · adaptador de Vertex AI', version='0.1.0', lifespan=ciclo,
                  description='Contenedor propio de predicción para Vertex AI: sirve el modelo champion de MLflow (probabilidad, clase y tramo).')

    def sin_modelo(request):
        return JSONResponse(status_code=503, content={'error': 'Modelo no disponible', 'detalle': request.app.state.error})

    @app.get(ruta_salud)
    def salud(request: Request):
        if request.app.state.servicio is None:
            return sin_modelo(request)
        return {'estado': 'ok'}

    if ruta_salud != RUTA_SALUD_POR_DEFECTO:        # la de siempre sigue disponible para probar a mano
        app.add_api_route(RUTA_SALUD_POR_DEFECTO, salud, methods=['GET'])

    @app.get('/modelo')
    def modelo(request: Request):
        if request.app.state.servicio is None:
            return sin_modelo(request)
        return request.app.state.servicio.info()

    @app.post(ruta_predict)
    async def predict(request: Request):
        t0 = time.perf_counter()
        servicio = request.app.state.servicio
        if servicio is None:
            return sin_modelo(request)
        try:
            cuerpo = json.loads(await request.body())
        except ValueError:
            registrar('WARNING', 'cuerpo no válido', evento='peticion', codigo=422)
            return JSONResponse(status_code=422, content={'error': 'El cuerpo no es JSON válido.', 'errores': []})
        filas, errores = validar_cuerpo(cuerpo, servicio.variables)
        if errores:
            registrar('WARNING', 'instancias no válidas', evento='peticion', codigo=422, errores=len(errores))
            return JSONResponse(status_code=422, content={'error': 'El cuerpo no cumple el contrato de entrada.', 'errores': errores})
        predicciones = servicio.predecir(filas)
        registrar('INFO', 'predicción', evento='peticion', codigo=200, instancias=len(filas), ms=round(1000 * (time.perf_counter() - t0), 1))
        return {'predictions': predicciones}

    @app.exception_handler(Exception)
    async def error_interno(request: Request, exc: Exception):
        registrar('ERROR', 'error no controlado', evento='error_no_controlado', tipo=type(exc).__name__)
        return JSONResponse(status_code=500, content={'error': 'Error interno'})

    return app


app = crear_app()


def main():
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=int(os.environ.get('AIP_HTTP_PORT') or 8080), log_level='warning')


if __name__ == '__main__':
    sys.exit(main())
