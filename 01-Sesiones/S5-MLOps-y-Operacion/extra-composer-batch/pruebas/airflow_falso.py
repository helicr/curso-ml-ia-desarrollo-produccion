"""SERVIDOR AIRFLOW FALSO, solo para pruebas. NO ejecuta nada: imita los endpoints de la API REST que usan lanzar_lote.py y la interfaz.

    python pruebas/airflow_falso.py --puerto 8099 [--api v1|v2] [--auth ninguna|basic|bearer] [--pausado] [--seg-por-paso 2]

  * Cada run avanza por las tareas del DAG (entradas, comprobar, ejecutar_lote, validar, resumir): un paso por consulta del run
    (o uno cada --seg-por-paso segundos). Si la «imagen» del run contiene la palabra «falla», ejecutar_lote termina en failed.
  * Los registros que devuelve son un texto fijo que lo dice: «servidor de prueba».
  * Rutas, nombres de estados y forma de las respuestas siguen la referencia de la API de Airflow, pero solo en lo que se usa
    aquí; que este servidor acepte una llamada NO demuestra que un Airflow real la acepte (sin verificar contra un Airflow real).
"""
import argparse
import base64
import itertools
import time
from datetime import datetime, timezone

from fastapi import Body, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

TAREAS = ['entradas', 'comprobar', 'ejecutar_lote', 'validar', 'resumir']
USUARIO, CLAVE, JWT = 'airflow', 'airflow', 'jwt-de-prueba'


def _iso():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00')


def crear_app(api='v1', auth='ninguna', pausado=False, seg_por_paso=0.0, dag_id='retencion_lote'):
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.state.runs, app.state.llamadas = {}, []
    contador = itertools.count(1)
    otra = 'v2' if api == 'v1' else 'v1'

    def comprobar(authorization):
        if auth == 'ninguna':
            return
        if auth == 'basic' and authorization == 'Basic ' + base64.b64encode(f'{USUARIO}:{CLAVE}'.encode()).decode():
            return
        if auth == 'bearer' and authorization in (f'Bearer {JWT}', 'Bearer token-de-google-de-prueba'):
            return
        raise HTTPException(401, 'Unauthorized')

    def estado_run(run):
        if run['final']:
            return run
        paso = run['paso'] if not seg_por_paso else int((time.time() - run['t0']) / seg_por_paso) + 1
        run['paso'] = paso
        tareas = {}
        for i, t in enumerate(TAREAS):
            tareas[t] = 'success' if i < paso else 'running' if i == paso else None
        if 'falla' in (run['conf'].get('imagen') or '') and paso >= 2:
            tareas['ejecutar_lote'] = 'failed'
            for t in TAREAS[3:]:
                tareas[t] = 'upstream_failed'
            run['estado'], run['final'], run['fin'] = 'failed', True, _iso()
        elif paso >= len(TAREAS):
            run['estado'], run['final'], run['fin'] = 'success', True, _iso()
            tareas = {t: 'success' for t in TAREAS}
        else:
            run['estado'] = 'running'
        run['tareas'] = tareas
        return run

    def ver_run(run):
        return {'dag_id': dag_id, 'dag_run_id': run['id'], 'state': run['estado'], 'conf': run['conf'], 'start_date': run['inicio'],
                'end_date': run['fin'] if run['final'] else None, 'logical_date': run['inicio'], 'run_type': 'manual'}

    def registrar(request: Request):
        app.state.llamadas.append((request.method, request.url.path + (('?' + request.url.query) if request.url.query else '')))

    @app.middleware('http')
    async def anotar(request: Request, call_next):
        registrar(request)
        return await call_next(request)

    if auth in ('basic', 'bearer') and api == 'v2':
        @app.post('/auth/token')
        async def token(cuerpo: dict = Body(...)):
            if cuerpo.get('username') == USUARIO and cuerpo.get('password') == CLAVE:
                return {'access_token': JWT}
            raise HTTPException(401, 'Unauthorized')

    @app.get(f'/api/{api}/version')
    async def version():
        return {'version': '3.0.0-prueba' if api == 'v2' else '2.10.0-prueba'}

    @app.get(f'/api/{otra}/version')
    async def otra_version():
        raise HTTPException(404, 'Not Found')

    @app.get(f'/api/{api}/dags/{{dag}}')
    async def dag(dag: str, authorization: str = Header(default='')):
        comprobar(authorization)
        if dag != dag_id:
            raise HTTPException(404, f'DAG {dag} not found')
        return {'dag_id': dag_id, 'is_paused': pausado, 'is_active': True, 'description': 'Servidor de prueba'}

    @app.post(f'/api/{api}/dags/{{dag}}/dagRuns')
    async def lanzar(dag: str, cuerpo: dict = Body(...), authorization: str = Header(default='')):
        comprobar(authorization)
        if dag != dag_id:
            raise HTTPException(404, f'DAG {dag} not found')
        if api == 'v2' and 'logical_date' not in cuerpo:
            raise HTTPException(422, 'logical_date es obligatorio en la API v2')
        rid = cuerpo.get('dag_run_id') or f'manual__{next(contador)}'
        if rid in app.state.runs:
            raise HTTPException(409, 'DagRun ya existe')
        run = {'id': rid, 'conf': cuerpo.get('conf') or {}, 'paso': 0, 'estado': 'queued', 'final': False, 'inicio': _iso(), 'fin': _iso(), 't0': time.time(),
               'tareas': {t: None for t in TAREAS}}
        app.state.runs[rid] = run
        return JSONResponse(ver_run(run), status_code=200)

    @app.get(f'/api/{api}/dags/{{dag}}/dagRuns')
    async def historial(dag: str, authorization: str = Header(default='')):
        comprobar(authorization)
        return {'dag_runs': [ver_run(estado_run(r)) for r in reversed(list(app.state.runs.values()))][:10], 'total_entries': len(app.state.runs)}

    @app.get(f'/api/{api}/dags/{{dag}}/dagRuns/{{run}}')
    async def ver(dag: str, run: str, authorization: str = Header(default='')):
        comprobar(authorization)
        if run not in app.state.runs:
            raise HTTPException(404, 'DagRun no encontrado')
        r = app.state.runs[run]
        if not seg_por_paso and not r['final']:
            r['paso'] += 1                                   # un paso por consulta
        return ver_run(estado_run(r))
    @app.get(f'/api/{api}/dags/{{dag}}/dagRuns/{{run}}/taskInstances')
    async def tareas(dag: str, run: str, authorization: str = Header(default='')):
        comprobar(authorization)
        if run not in app.state.runs:
            raise HTTPException(404, 'DagRun no encontrado')
        r = app.state.runs[run]
        return {'task_instances': [{'task_id': t, 'state': r['tareas'].get(t), 'try_number': 1 if r['tareas'].get(t) else 0,
                                    'start_date': r['inicio'] if r['tareas'].get(t) else None,
                                    'end_date': r['fin'] if r['tareas'].get(t) not in (None, 'running') else None} for t in TAREAS],
                'total_entries': len(TAREAS)}

    @app.get(f'/api/{api}/dags/{{dag}}/dagRuns/{{run}}/taskInstances/{{tarea}}/logs/{{intento}}')
    async def log(dag: str, run: str, tarea: str, intento: int, authorization: str = Header(default='')):
        comprobar(authorization)
        if run not in app.state.runs or tarea not in TAREAS:
            raise HTTPException(404, 'No encontrado')
        falla = app.state.runs[run]['tareas'].get(tarea) == 'failed'
        texto = f'[servidor de prueba] Registro SIMULADO de {tarea} (intento {intento}). Aquí no se ha ejecutado ningún contenedor.\n'
        if falla:
            texto += '[servidor de prueba] ERROR simulado: la imagen no se pudo bajar (ImagePullBackOff).\n'
        return {'content': texto, 'continuation_token': None}

    return app


if __name__ == '__main__':
    import uvicorn
    ap = argparse.ArgumentParser()
    ap.add_argument('--puerto', type=int, default=8099)
    ap.add_argument('--api', choices=['v1', 'v2'], default='v1')
    ap.add_argument('--auth', choices=['ninguna', 'basic', 'bearer'], default='ninguna')
    ap.add_argument('--pausado', action='store_true')
    ap.add_argument('--seg-por-paso', type=float, default=0.0)
    a = ap.parse_args()
    uvicorn.run(crear_app(a.api, a.auth, a.pausado, a.seg_por_paso), host='127.0.0.1', port=a.puerto, log_level='warning')
