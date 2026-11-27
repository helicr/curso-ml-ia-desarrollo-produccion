#!/usr/bin/env python3
"""Lanza el DAG «retencion_lote» por la API REST de Airflow, espera a que termine y sale con un código que dice cómo acabó.

Solo biblioteca estándar (urllib): vale en un ordenador, en un runner de GitHub Actions o en Cloud Shell.

  python lanzar_lote.py --url https://<id>.composer.googleusercontent.com --auth google --corte 2011-12-10 \\
      --imagen europe-west1-docker.pkg.dev/<proyecto>/curso/retencion-lote:v1
  python lanzar_lote.py --url http://localhost:8080 --auth basic --corte 2011-12-10 --imagen retencion-lote:local    # Airflow local
  python lanzar_lote.py --url http://localhost:8080 --auth basic --simular-url                                      # no llama: enseña qué enviaría

AUTENTICACIÓN (--auth)
  google    Cloud Composer: un token de acceso de Google (alcance cloud-platform) en la cabecera Authorization: Bearer.
            Lo saca de  gcloud auth print-access-token  (con WIF en Actions, la sesión ya la dejó google-github-actions/auth);
            si no hay gcloud, de las credenciales por defecto de Google (google-auth, solo si está instalado). Variable AIRFLOW_TOKEN
            si ya tienes el token.
  basic     Airflow local: usuario y contraseña de las variables AIRFLOW_USUARIO y AIRFLOW_CLAVE (nunca por argumento: se verían
            en la lista de procesos). Con la API v2 (Airflow 3) se canjean por un JWT en POST /auth/token; con la v1, Basic.
  token     un token que ya tienes, en AIRFLOW_TOKEN.
  ninguna   sin cabecera (servidor de pruebas).

API (--api): auto (por defecto) prueba /api/v2/version y después /api/v1/version. Airflow 3 → v2; Airflow 2 → v1.

CÓDIGOS DE SALIDA
  0 el run terminó en success · 1 el run terminó en failed · 2 se agotó la espera (el run SIGUE en Airflow) ·
  3 no se pudo hablar con Airflow (red, autenticación, DAG inexistente) · 4 el DAG está en pausa (el run no empezaría nunca)
"""
import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

OK, FALLO, ESPERA, CONEXION, PAUSA = 0, 1, 2, 3, 4
ESTADOS_FINALES = {'success', 'failed'}


class ErrorAirflow(Exception):
    def __init__(self, mensaje, codigo=CONEXION):
        super().__init__(mensaje)
        self.codigo = codigo


def ahora():
    return datetime.now(timezone.utc)


def decir(texto):
    print(texto, flush=True)


# ------------------------------------------------------------------------------------------------ autenticación
def token_google():
    """Token de acceso de Google. Primero gcloud (sin dependencias), después google-auth si está instalado."""
    if os.environ.get('AIRFLOW_TOKEN'):
        return os.environ['AIRFLOW_TOKEN']
    gcloud = shutil.which('gcloud') or shutil.which('gcloud.cmd')
    if gcloud:
        r = subprocess.run([gcloud, 'auth', 'print-access-token'], capture_output=True, text=True, timeout=60)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
        motivo = (r.stderr or '').strip().splitlines()[-1:] or ['sin detalle']
        raise ErrorAirflow(f'gcloud no dio un token ({motivo[0]}). Ejecuta «gcloud auth login» o, en Actions, el paso de autenticación por WIF.')
    try:
        import google.auth
        import google.auth.transport.requests
        cred, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
        cred.refresh(google.auth.transport.requests.Request())
        return cred.token
    except ImportError:
        raise ErrorAirflow('No hay gcloud en el PATH ni la biblioteca google-auth. Instala el SDK de Google Cloud o exporta AIRFLOW_TOKEN.')
    except Exception as e:                               # noqa: BLE001
        raise ErrorAirflow(f'No se pudieron obtener credenciales de Google: {type(e).__name__}: {e}')


class Cliente:
    def __init__(self, url, auth, api='auto', timeout=60):
        self.base = url.rstrip('/')
        self.auth, self.api, self.timeout = auth, api, timeout
        self.cabecera_auth = None

    # --- HTTP
    def _pedir(self, metodo, ruta, cuerpo=None, cabeceras=None, texto=False):
        datos = None if cuerpo is None else json.dumps(cuerpo).encode('utf-8')
        h = {'Accept': 'application/json'}
        if datos is not None:
            h['Content-Type'] = 'application/json'
        if self.cabecera_auth:
            h['Authorization'] = self.cabecera_auth
        h.update(cabeceras or {})
        req = urllib.request.Request(self.base + ruta, data=datos, headers=h, method=metodo)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                bruto = r.read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as e:
            detalle = e.read().decode('utf-8', 'replace')[:300].replace('\n', ' ')
            pista = {401: ' (no autenticado: revisa --auth y las credenciales)', 403: ' (sin permiso: falta el rol de Airflow o de IAM)',
                     404: ' (no existe: ¿el nombre del DAG? ¿la versión de la API?)'}.get(e.code, '')
            raise ErrorAirflow(f'{metodo} {ruta} -> HTTP {e.code}{pista}: {detalle}')
        except urllib.error.URLError as e:
            raise ErrorAirflow(f'No se pudo conectar con {self.base}: {e.reason}. ¿Está Airflow en marcha y es esa la URL?')
        except TimeoutError:
            raise ErrorAirflow(f'Tiempo agotado hablando con {self.base}.')
        if texto:
            return bruto
        try:
            return json.loads(bruto) if bruto.strip() else {}
        except json.JSONDecodeError:
            raise ErrorAirflow(f'{metodo} {ruta} no devolvió JSON (¿es la URL del servidor web de Airflow?): {bruto[:120]!r}')

    # --- preparación
    def preparar(self):
        if self.auth == 'google':
            self.cabecera_auth = 'Bearer ' + token_google()
        elif self.auth == 'token':
            if not os.environ.get('AIRFLOW_TOKEN'):
                raise ErrorAirflow('--auth token pide la variable de entorno AIRFLOW_TOKEN.')
            self.cabecera_auth = 'Bearer ' + os.environ['AIRFLOW_TOKEN']
        if self.api == 'auto':
            self.api = self.detectar()
        if self.auth == 'basic':
            usuario, clave = os.environ.get('AIRFLOW_USUARIO'), os.environ.get('AIRFLOW_CLAVE')
            if not usuario or clave is None:
                raise ErrorAirflow('--auth basic pide las variables de entorno AIRFLOW_USUARIO y AIRFLOW_CLAVE.')
            if self.api == 'v2':                          # Airflow 3: usuario y clave se canjean por un JWT
                t = self._pedir('POST', '/auth/token', {'username': usuario, 'password': clave})
                if not t.get('access_token'):
                    raise ErrorAirflow('POST /auth/token no devolvió access_token.')
                self.cabecera_auth = 'Bearer ' + t['access_token']
            else:
                self.cabecera_auth = 'Basic ' + base64.b64encode(f'{usuario}:{clave}'.encode()).decode()
        return self.api

    def detectar(self):
        errores = []
        for v in ('v2', 'v1'):
            try:
                self._pedir('GET', f'/api/{v}/version')
                return v
            except ErrorAirflow as e:
                errores.append(str(e))
        raise ErrorAirflow('No respondió ni /api/v2/version ni /api/v1/version: ' + errores[-1])

    def ruta(self, resto):
        return f'/api/{self.api}{resto}'

    # --- operaciones
    def dag(self, dag_id):
        return self._pedir('GET', self.ruta(f'/dags/{urllib.parse.quote(dag_id)}'))

    def lanzar(self, dag_id, conf, run_id):
        cuerpo = {'conf': conf, 'dag_run_id': run_id}
        if self.api == 'v2':                              # Airflow 3 pide logical_date (la doc de Composer lo envía)
            cuerpo['logical_date'] = ahora().strftime('%Y-%m-%dT%H:%M:%SZ')
        return self._pedir('POST', self.ruta(f'/dags/{urllib.parse.quote(dag_id)}/dagRuns'), cuerpo)

    def run(self, dag_id, run_id):
        return self._pedir('GET', self.ruta(f'/dags/{urllib.parse.quote(dag_id)}/dagRuns/{urllib.parse.quote(run_id)}'))

    def historial(self, dag_id, limite=10):
        r = self._pedir('GET', self.ruta(f'/dags/{urllib.parse.quote(dag_id)}/dagRuns?limit={int(limite)}&order_by=-start_date'))
        return r.get('dag_runs', [])

    def tareas(self, dag_id, run_id):
        r = self._pedir('GET', self.ruta(f'/dags/{urllib.parse.quote(dag_id)}/dagRuns/{urllib.parse.quote(run_id)}/taskInstances'))
        return r.get('task_instances', [])

    def log(self, dag_id, run_id, task_id, intento):
        ruta = self.ruta(f'/dags/{urllib.parse.quote(dag_id)}/dagRuns/{urllib.parse.quote(run_id)}/taskInstances/{urllib.parse.quote(task_id)}/logs/{intento}')
        r = self._pedir('GET', ruta)
        c = r.get('content', '')
        if isinstance(c, list):                           # Airflow 3 puede devolver líneas estructuradas
            c = '\n'.join(x.get('event', '') if isinstance(x, dict) else str(x) for x in c)
        return c


def conf_desde(args):
    conf = {'corte': args.corte or '', 'imagen': args.imagen or '', 'capacidad': args.capacidad}
    if args.huella_esperada:
        conf['huella_esperada'] = args.huella_esperada
    return conf


def enlace_ui(url, dag_id, run_id, api):
    if api == 'v2':
        return f'{url.rstrip("/")}/dags/{dag_id}/runs/{urllib.parse.quote(run_id)}'
    return f'{url.rstrip("/")}/dags/{dag_id}/grid?dag_run_id={urllib.parse.quote(run_id)}'


def simular(args, run_id):
    """No llama a nadie: enseña qué enviaría. Sirve para comprobar los argumentos sin Airflow."""
    api = args.api if args.api != 'auto' else 'v2|v1 (se detectaría con /version)'
    decir(f'[simulado] URL base: {args.url.rstrip("/")} · autenticación: {args.auth} · API: {api}')
    decir(f'[simulado] 1. GET  /api/<v>/dags/{args.dag}            (¿existe y no está en pausa?)')
    decir(f'[simulado] 2. POST /api/<v>/dags/{args.dag}/dagRuns    cuerpo: ' + json.dumps({'conf': conf_desde(args), 'dag_run_id': run_id}, ensure_ascii=False))
    decir(f'[simulado] 3. GET  /api/<v>/dags/{args.dag}/dagRuns/{run_id}  cada {args.intervalo} s hasta success o failed (máximo {args.espera} s)')
    decir('[simulado] No se ha enviado nada.')
    return OK


def escribir_resumen(ruta, dag_id, run_id, estado, tareas, enlace, segundos):
    iconos = {'success': 'OK', 'failed': 'FALLO', 'upstream_failed': 'no llegó a ejecutarse', 'skipped': 'saltada', 'running': 'en curso', 'queued': 'en cola'}
    filas = ['## Lote orquestado con Airflow', '', '| Dato | Valor |', '|---|---|',
             f'| DAG | `{dag_id}` |', f'| Run | `{run_id}` |', f'| Estado | **{estado}** |', f'| Duración | {segundos:.0f} s |']
    if enlace:
        filas.append(f'| Airflow | {enlace} |')
    filas += ['', '| Tarea | Estado |', '|---|---|']
    filas += [f'| {t["task_id"]} | {t.get("state") or "sin estado"} ({iconos.get(t.get("state"), "")}) |' for t in tareas]
    with open(ruta, 'a', encoding='utf-8') as f:
        f.write('\n'.join(filas) + '\n')


def main(argv=None):
    ap = argparse.ArgumentParser(description='Lanza el DAG retencion_lote por la API REST de Airflow y espera el resultado.',
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__.split('AUTENTICACIÓN')[1] if 'AUTENTICACIÓN' in __doc__ else '')
    ap.add_argument('--url', default=os.environ.get('AIRFLOW_URL'), help='URL del servidor web de Airflow (o la variable AIRFLOW_URL)')
    ap.add_argument('--dag', default='retencion_lote')
    ap.add_argument('--auth', choices=['google', 'basic', 'token', 'ninguna'], default=os.environ.get('AIRFLOW_AUTH', 'ninguna'))
    ap.add_argument('--api', choices=['auto', 'v1', 'v2'], default='auto')
    ap.add_argument('--corte', default='', help='fecha de corte AAAA-MM-DD (vacío = el día siguiente a la última factura)')
    ap.add_argument('--imagen', default='', help='imagen del lote (vacío = la que tenga el DAG por defecto)')
    ap.add_argument('--capacidad', type=float, default=0.10)
    ap.add_argument('--huella-esperada', default='')
    ap.add_argument('--run-id', default='')
    ap.add_argument('--espera', type=int, default=3600, help='segundos máximos esperando (por defecto 3600)')
    ap.add_argument('--intervalo', type=int, default=10, help='segundos entre consultas (por defecto 10)')
    ap.add_argument('--resumen-md', default=os.environ.get('GITHUB_STEP_SUMMARY', ''), help='archivo al que añadir un resumen en Markdown (en Actions, GITHUB_STEP_SUMMARY)')
    ap.add_argument('--salida-json', default='', help='archivo donde dejar el resultado final en JSON')
    ap.add_argument('--log-final', default='resumir', help='tarea cuyo registro se muestra y se añade al resumen cuando el run acaba bien (por defecto resumir; vacío = ninguna)')
    ap.add_argument('--simular-url', action='store_true', help='no llama a Airflow: enseña las llamadas que haría y sale con 0')
    args = ap.parse_args(argv)
    if not args.url:
        ap.error('falta --url (o la variable AIRFLOW_URL)')
    run_id = args.run_id or 'lanzar-' + ahora().strftime('%Y%m%dT%H%M%S')
    if args.simular_url:
        return simular(args, run_id)

    c = Cliente(args.url, args.auth, args.api)
    inicio = time.time()
    try:
        api = c.preparar()
        decir(f'Airflow en {c.base} · API {api} · autenticación {args.auth}')
        d = c.dag(args.dag)
        if d.get('is_paused'):
            raise ErrorAirflow(f'El DAG «{args.dag}» está en pausa: un run nuevo se quedaría en cola para siempre. '
                               f'Reactívalo:  airflow dags unpause {args.dag}  (o el interruptor de la interfaz).', PAUSA)
        c.lanzar(args.dag, conf_desde(args), run_id)
        enlace = enlace_ui(c.base, args.dag, run_id, api)
        decir(f'Lanzado {args.dag} · run {run_id}\nSeguimiento: {enlace}')
        vistos, estado, tareas = {}, 'queued', []
        while True:
            estado = c.run(args.dag, run_id).get('state')
            tareas = c.tareas(args.dag, run_id)
            for t in tareas:
                if vistos.get(t['task_id']) != t.get('state'):
                    vistos[t['task_id']] = t.get('state')
                    decir(f'  tarea {t["task_id"]:<14} {t.get("state") or "sin estado"}')
            if estado in ESTADOS_FINALES:
                break
            if time.time() - inicio > args.espera:
                decir(f'Se agotó la espera ({args.espera} s) con el run en «{estado}». El run SIGUE en Airflow: {enlace}')
                return ESPERA
            time.sleep(args.intervalo)
        segundos = time.time() - inicio
        decir(f'Run {run_id}: {estado} en {segundos:.0f} s')
        if estado == 'failed':
            for t in tareas:
                if t.get('state') == 'failed':
                    decir(f'--- registro de la tarea que falló: {t["task_id"]} ---')
                    try:
                        decir('\n'.join(c.log(args.dag, run_id, t['task_id'], t.get('try_number') or 1).strip().splitlines()[-25:]))
                    except ErrorAirflow as e:
                        decir(f'(no se pudo leer el registro: {e})')
        final = ''
        if estado == 'success' and args.log_final:
            try:
                final = c.log(args.dag, run_id, args.log_final, 1).strip()
                decir(f'--- registro de {args.log_final} ---\n' + final)
            except ErrorAirflow as e:
                decir(f'(no se pudo leer el registro de {args.log_final}: {e})')
        if args.resumen_md:
            escribir_resumen(args.resumen_md, args.dag, run_id, estado, tareas, enlace, segundos)
            if final:
                with open(args.resumen_md, 'a', encoding='utf-8') as f:
                    f.write('\n<details><summary>Registro de ' + args.log_final + '</summary>\n\n```\n' + final[-3000:] + '\n```\n\n</details>\n')
        if args.salida_json:
            with open(args.salida_json, 'w', encoding='utf-8') as f:
                json.dump({'dag': args.dag, 'run_id': run_id, 'estado': estado, 'segundos': round(segundos), 'enlace': enlace,
                           'tareas': {t['task_id']: t.get('state') for t in tareas}}, f, ensure_ascii=False, indent=2)
        return OK if estado == 'success' else FALLO
    except ErrorAirflow as e:
        decir(f'ERROR: {e}')
        return e.codigo


if __name__ == '__main__':
    sys.exit(main())
