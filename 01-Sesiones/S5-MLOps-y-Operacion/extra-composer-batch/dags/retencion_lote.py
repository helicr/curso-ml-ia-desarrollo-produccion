"""DAG «retencion_lote»: el lote de puntuación de clientes (ia_mlops.explotacion) orquestado con Airflow.

    comprobar ──► ejecutar_lote ──► validar ──► resumir

  comprobar      arranca la imagen y lee qué modelo lleva (models/metadatos.json): modelo, huella de datos, fecha de entrenamiento.
  ejecutar_lote  en esa MISMA imagen: python -m ia_mlops.explotacion --corte … --capacidad … --sin-guardar-fs, y reduce la salida a un JSON.
  validar        en el worker de Airflow: filas, probabilidades en [0, 1], tramos, deciles, campaña y que el modelo es el de «comprobar».
  resumir        deja el resultado en el registro de la tarea.

SIN SCHEDULE: se lanza a mano, por la API o por Actions. Parámetros (Trigger DAG w/ config, o --conf '{"corte": "2011-12-10"}'):
    corte           AAAA-MM-DD; vacío = el día siguiente a la última factura de MASTER
    imagen          registro/ruta:etiqueta de la imagen del lote (vacío = variable de entorno LOTE_IMAGEN_DEFECTO)
    capacidad       fracción de clientes a los que llega la campaña (0.10 = el 10 %)
    huella_esperada opcional: si se rellena, el lote falla si el modelo de la imagen tiene otra huella de datos

DOS VARIANTES del operador, elegidas por LOTE_MODO (variable de entorno o Variable de Airflow; por defecto «kubernetes»):
    kubernetes   KubernetesPodOperator: en Cloud Composer, la imagen sale de Artifact Registry.
    docker       DockerOperator: en local (Airflow en Docker), con el socket de Docker montado.
Si falta el proveedor de la variante elegida, el DAG SE IMPORTA igualmente y la tarea falla con un mensaje que dice qué instalar.

La imagen del lote es la imagen de la API más el SQL y la base de muestra (lote.Dockerfile): sirve igual con el Dockerfile de
develop (COPY del modelo) y con el multi-etapa (--build-context modelo=…), porque parte de la imagen ya construida.
ESTE DAG NO SE HA EJECUTADO EN UN AIRFLOW REAL (sin verificar): lo que sí se probó está en pruebas/.
"""
import inspect
import json
import os
from datetime import datetime

try:                                                      # Airflow 3
    from airflow.sdk import DAG, Param
except ImportError:                                       # Airflow 2
    from airflow import DAG
    from airflow.models.param import Param

try:
    from airflow.providers.standard.operators.python import PythonOperator          # Airflow 3
except ImportError:
    from airflow.operators.python import PythonOperator                              # Airflow 2

from airflow.exceptions import AirflowFailException

from lote_logica import ErrorSalida, resumen_markdown, resumir_salida, validar_entradas, validar_salida

DAG_ID = 'retencion_lote'
MODOS = ('kubernetes', 'docker')


def leer_ajuste(nombre, defecto=''):
    """Variable de entorno primero; si no está, Variable de Airflow (consulta la base al analizar el DAG: por eso va la primera)."""
    valor = os.environ.get(nombre)
    if valor is not None:
        return valor
    try:
        from airflow.models import Variable
        return Variable.get(nombre, default=defecto) if _variable_acepta_default() else Variable.get(nombre, default_var=defecto)
    except Exception:                                      # noqa: BLE001 - sin base disponible al importar: se usa el valor por defecto
        return defecto


def _variable_acepta_default():
    from airflow.models import Variable
    return 'default' in inspect.signature(Variable.get).parameters


MODO = leer_ajuste('LOTE_MODO', 'kubernetes').strip().lower()
NAMESPACE = leer_ajuste('LOTE_K8S_NAMESPACE', 'composer-user-workloads')       # en Composer los pods siempre corren aquí
IMAGEN_DEFECTO = leer_ajuste('LOTE_IMAGEN_DEFECTO', '')

# Lo que ejecuta el contenedor. Los valores entran como ARGUMENTOS posicionales ($1, $2), nunca pegados dentro del script.
ORDEN_LOTE = (
    'set -eu; CORTE="$1"; CAP="$2"; '
    'if [ -n "$CORTE" ]; then python -m ia_mlops.explotacion --corte "$CORTE" --capacidad "$CAP" --sin-guardar-fs; '
    'else python -m ia_mlops.explotacion --capacidad "$CAP" --sin-guardar-fs; fi; '
    'python -c "$RESUMEN_PY"'
)
RESUMEN_PY = (
    inspect.getsource(resumir_salida)
    + "\nimport json, os\nr = resumir_salida()\n"
      "if os.path.isdir('/airflow/xcom'):\n"
      "    json.dump(r, open('/airflow/xcom/return.json', 'w'))\n"
      "print(json.dumps(r))\n"                            # la ÚLTIMA línea de salida: es lo que recoge DockerOperator como XCom
)
ORDEN_COMPROBAR = (
    "import json, os; m = json.load(open(os.path.join(os.environ.get('CURSO_MODELOS', 'models'), 'metadatos.json'), encoding='utf-8')); "
    "r = {k: m.get(k) for k in ('modelo', 'huella_datos', 'entrenado_en')}; "
    "os.path.isdir('/airflow/xcom') and json.dump(r, open('/airflow/xcom/return.json', 'w')); print(json.dumps(r))"
)
ENTORNO_LOTE = {'RESUMEN_PY': RESUMEN_PY, 'CURSO_REPORTES': '/tmp/reports'}


def _tarea_que_falla(task_id, motivo):
    def _falla(**_):
        raise AirflowFailException(motivo)
    return PythonOperator(task_id=task_id, python_callable=_falla)


# ---- VARIANTE 1 · KubernetesPodOperator (Cloud Composer) -------------------------------------------------------------
def pod(task_id, cmds, argumentos, entorno=None):
    try:
        from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
    except ImportError:
        return _tarea_que_falla(task_id, 'Falta apache-airflow-providers-cncf-kubernetes (viene con Cloud Composer). '
                                         'En local usa LOTE_MODO=docker.')
    comunes = dict(
        task_id=task_id, name=task_id.replace('_', '-'), namespace=NAMESPACE,
        image='{{ params.imagen or "' + IMAGEN_DEFECTO + '" }}',
        cmds=list(cmds), arguments=list(argumentos), env_vars=entorno or {},
        get_logs=True, do_xcom_push=True, startup_timeout_seconds=600,
        config_file='/home/airflow/composer_kube_config', kubernetes_conn_id='kubernetes_default',
    )
    try:
        return KubernetesPodOperator(on_finish_action='delete_pod', **comunes)          # proveedor reciente
    except TypeError:
        return KubernetesPodOperator(is_delete_operator_pod=True, **comunes)             # proveedor antiguo


# ---- VARIANTE 2 · DockerOperator (local) ------------------------------------------------------------------------------
def contenedor(task_id, cmds, argumentos, entorno=None):
    try:
        from airflow.providers.docker.operators.docker import DockerOperator
    except ImportError:
        return _tarea_que_falla(task_id, 'Falta apache-airflow-providers-docker. Instálalo (pip install apache-airflow-providers-docker) '
                                         'o usa LOTE_MODO=kubernetes en Cloud Composer.')
    return DockerOperator(
        task_id=task_id, image='{{ params.imagen or "' + IMAGEN_DEFECTO + '" }}',
        command=list(cmds) + list(argumentos), environment=entorno or {},        # la imagen de la API solo define CMD: command lo sustituye
        docker_url=leer_ajuste('LOTE_DOCKER_URL', 'unix://var/run/docker.sock'), auto_remove='success', mount_tmp_dir=False,
        tty=False, force_pull=False,
    )


def operador(task_id, cmds, argumentos, entorno=None):
    if MODO == 'kubernetes':
        return pod(task_id, cmds, argumentos, entorno)
    if MODO == 'docker':
        return contenedor(task_id, cmds, argumentos, entorno)
    return _tarea_que_falla(task_id, f'LOTE_MODO={MODO!r} no es válido: usa uno de {MODOS}.')


# ---- Tareas que corren en el worker ----------------------------------------------------------------------------------
def _como_dict(valor):
    """KubernetesPodOperator entrega el JSON ya leído; DockerOperator, la última línea de salida como texto."""
    if isinstance(valor, (bytes, bytearray)):
        valor = valor.decode('utf-8')
    if isinstance(valor, str):
        valor = json.loads(valor.strip().splitlines()[-1])
    return valor


def _validar_entradas_tarea(**contexto):
    p = contexto['params']
    try:
        validar_entradas(p.get('corte'), p.get('imagen') or IMAGEN_DEFECTO, p.get('capacidad'))
    except ErrorSalida as e:
        raise AirflowFailException(str(e)) from e


def _validar(**contexto):
    ti, p = contexto['ti'], contexto['params']
    try:
        resumen = _como_dict(ti.xcom_pull(task_ids='ejecutar_lote'))
        comprobar = _como_dict(ti.xcom_pull(task_ids='comprobar'))
        avisos = validar_salida(resumen, comprobar, (p.get('huella_esperada') or '').strip() or None)
    except (ErrorSalida, ValueError) as e:
        raise AirflowFailException(f'Salida del lote no válida: {e}') from e
    for a in avisos:
        print('AVISO:', a)
    return {'resumen': resumen, 'avisos': avisos}


def _resumir(**contexto):
    ti = contexto['ti']
    datos = ti.xcom_pull(task_ids='validar')
    texto = resumen_markdown(datos['resumen'], datos['avisos'])
    print(texto)
    return texto


with DAG(
    dag_id=DAG_ID,
    description='Puntuación por lotes de todos los clientes (ia_mlops.explotacion) en la imagen que lleva el modelo.',
    schedule=None, start_date=datetime(2026, 1, 1), catchup=False, max_active_runs=1,
    tags=['curso', 'retencion', 'lote'], doc_md=__doc__,
    params={
        'corte': Param('', type='string', pattern=r'^(\d{4}-\d{2}-\d{2})?$', description='AAAA-MM-DD; vacío = el día siguiente a la última factura'),
        'imagen': Param('', type='string', description='registro/ruta:etiqueta de la imagen del lote; vacío = LOTE_IMAGEN_DEFECTO'),
        'capacidad': Param(0.10, type='number', minimum=0.01, maximum=1, description='fracción de clientes a los que llega la campaña'),
        'huella_esperada': Param('', type='string', description='opcional: huella de datos que debe tener el modelo de la imagen'),
    },
) as dag:
    entradas = PythonOperator(task_id='entradas', python_callable=_validar_entradas_tarea)
    comprobar = operador('comprobar', ['python', '-c'], [ORDEN_COMPROBAR])
    ejecutar = operador('ejecutar_lote', ['sh', '-c'], [ORDEN_LOTE, 'lote', '{{ params.corte }}', '{{ params.capacidad }}'], ENTORNO_LOTE)
    validar = PythonOperator(task_id='validar', python_callable=_validar)
    resumir = PythonOperator(task_id='resumir', python_callable=_resumir)
    entradas >> comprobar >> ejecutar >> validar >> resumir
