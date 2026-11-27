"""El DAG y su lógica. NADA de esto es Airflow real: no hay Airflow instalado.

  * AST del DAG: sintaxis, un DAG «retencion_lote», sin schedule, parámetros y cuatro tareas encadenadas.
  * Importación con un Airflow DE CARTÓN (módulos falsos): se comprueba la estructura de tareas, la elección de variante por
    LOTE_MODO, que falte un proveedor no rompe la importación, y que los argumentos del contenedor son los de comandos.md.
  * La lógica de validación sobre la salida REAL de `python -m ia_mlops.explotacion` (sobre una COPIA de curso.db en una carpeta
    temporal; se comprueba que la base y el modelo del repositorio no cambian).
"""
import ast
import hashlib
import importlib
import json
import os
import re
import subprocess
import sys
import types
from pathlib import Path

import pytest

EXTRA = Path(__file__).resolve().parents[1]
DAGS = EXTRA / 'dags'
PROYECTO = EXTRA.parents[2] / '04-Proyecto-Base'
DAG_PY = DAGS / 'retencion_lote.py'

import lote_logica as L  # noqa: E402


# ------------------------------------------------------------------------------------------------ AST
def test_el_dag_es_python_valido_y_sin_secretos():
    texto = DAG_PY.read_text(encoding='utf-8')
    ast.parse(texto)
    assert not re.search(r'(password|token|secret)\s*=\s*[\'"][^\'"]+[\'"]', texto, re.I)
    assert "schedule=None" in texto and "dag_id=DAG_ID" in texto and "DAG_ID = 'retencion_lote'" in texto


def test_los_parametros_estan_declarados():
    texto = DAG_PY.read_text(encoding='utf-8')
    for p in ('corte', 'imagen', 'capacidad', 'huella_esperada'):
        assert f"'{p}': Param(" in texto


# ------------------------------------------------------------------------------------------------ un Airflow de cartón
class _Tarea:
    def __init__(self, task_id, **kw):
        self.task_id, self.kw, self.aguas_abajo = task_id, kw, []
        DAG_ACTUAL[-1].tareas[task_id] = self

    def __rshift__(self, otra):
        self.aguas_abajo.append(otra.task_id)
        return otra


DAG_ACTUAL = []


class _DAG:
    def __init__(self, **kw):
        self.kw, self.tareas = kw, {}

    def __enter__(self):
        DAG_ACTUAL.append(self)
        return self

    def __exit__(self, *a):
        DAG_ACTUAL.pop()


class _Param:
    def __init__(self, defecto, **kw):
        self.defecto, self.kw = defecto, kw


def _modulo(nombre, **attrs):
    m = types.ModuleType(nombre)
    m.__dict__.update(attrs)
    return m


class _Fail(Exception):
    pass


def _cargar_dag(monkeypatch, modo, airflow3=True, k8s=True, docker=True):
    DAG_ACTUAL.clear()
    mods = {
        'airflow': _modulo('airflow', DAG=_DAG),
        'airflow.exceptions': _modulo('airflow.exceptions', AirflowFailException=_Fail),
        'airflow.models': _modulo('airflow.models', Variable=types.SimpleNamespace(get=lambda k, default=None: default)),
        'airflow.models.param': _modulo('airflow.models.param', Param=_Param),
        'airflow.operators': _modulo('airflow.operators'),
        'airflow.operators.python': _modulo('airflow.operators.python', PythonOperator=type('PythonOperator', (_Tarea,), {})),
        'airflow.providers': _modulo('airflow.providers'),
    }
    if airflow3:
        mods['airflow.sdk'] = _modulo('airflow.sdk', DAG=_DAG, Param=_Param)
        mods['airflow.providers.standard'] = _modulo('airflow.providers.standard')
        mods['airflow.providers.standard.operators'] = _modulo('airflow.providers.standard.operators')
        mods['airflow.providers.standard.operators.python'] = _modulo('x', PythonOperator=mods['airflow.operators.python'].PythonOperator)
    if k8s:
        mods['airflow.providers.cncf'] = _modulo('c')
        mods['airflow.providers.cncf.kubernetes'] = _modulo('k')
        mods['airflow.providers.cncf.kubernetes.operators'] = _modulo('o')
        mods['airflow.providers.cncf.kubernetes.operators.pod'] = _modulo('p', KubernetesPodOperator=type('KubernetesPodOperator', (_Tarea,), {}))
    if docker:
        mods['airflow.providers.docker'] = _modulo('d')
        mods['airflow.providers.docker.operators'] = _modulo('o')
        mods['airflow.providers.docker.operators.docker'] = _modulo('dd', DockerOperator=type('DockerOperator', (_Tarea,), {}))
    for k in [k for k in sys.modules if k == 'retencion_lote' or k.startswith('airflow')]:
        monkeypatch.delitem(sys.modules, k)
    for k, v in mods.items():
        monkeypatch.setitem(sys.modules, k, v)
    monkeypatch.setenv('LOTE_MODO', modo)
    monkeypatch.setenv('LOTE_IMAGEN_DEFECTO', 'europe-west1-docker.pkg.dev/proy/curso/retencion-lote:v1')
    monkeypatch.syspath_prepend(str(DAGS))
    monkeypatch.delitem(sys.modules, 'retencion_lote', raising=False)
    modulo = importlib.import_module('retencion_lote')
    return modulo, DAG_ACTUAL[-1] if DAG_ACTUAL else None


def _dag_de(modulo):
    return modulo.dag


@pytest.mark.parametrize('airflow3', [True, False])
def test_estructura_de_tareas_en_las_dos_versiones_de_airflow(monkeypatch, airflow3):
    m, _ = _cargar_dag(monkeypatch, 'kubernetes', airflow3=airflow3)
    d = _dag_de(m)
    assert d.kw['dag_id'] == 'retencion_lote' and d.kw['schedule'] is None and d.kw['catchup'] is False and d.kw['max_active_runs'] == 1
    assert list(d.tareas) == ['entradas', 'comprobar', 'ejecutar_lote', 'validar', 'resumir']
    cadena = [t for t in d.tareas]
    for a, b in zip(cadena, cadena[1:]):
        assert d.tareas[a].aguas_abajo == [b]
    assert set(d.kw['params']) == {'corte', 'imagen', 'capacidad', 'huella_esperada'}
    assert d.kw['params']['capacidad'].defecto == 0.10


def test_variante_kubernetes(monkeypatch):
    m, _ = _cargar_dag(monkeypatch, 'kubernetes')
    t = _dag_de(m).tareas['ejecutar_lote']
    assert type(t).__name__ == 'KubernetesPodOperator'
    assert t.kw['namespace'] == 'composer-user-workloads' and t.kw['do_xcom_push'] is True
    assert t.kw['cmds'] == ['sh', '-c'] and t.kw['arguments'][1:] == ['lote', '{{ params.corte }}', '{{ params.capacidad }}']
    assert 'params.imagen' in t.kw['image'] and 'retencion-lote:v1' in t.kw['image']
    assert t.kw['config_file'] == '/home/airflow/composer_kube_config'


def test_variante_docker(monkeypatch):
    m, _ = _cargar_dag(monkeypatch, 'docker')
    t = _dag_de(m).tareas['ejecutar_lote']
    assert type(t).__name__ == 'DockerOperator'
    assert t.kw['command'][:2] == ['sh', '-c'] and t.kw['docker_url'].startswith('unix://')
    assert 'ia_mlops.explotacion' in t.kw['command'][2]


@pytest.mark.parametrize('modo,falta', [('kubernetes', 'k8s'), ('docker', 'docker')])
def test_si_falta_el_proveedor_el_dag_se_importa_y_la_tarea_explica(monkeypatch, modo, falta):
    m, _ = _cargar_dag(monkeypatch, modo, **{falta: False})
    t = _dag_de(m).tareas['ejecutar_lote']
    assert type(t).__name__ == 'PythonOperator'
    with pytest.raises(_Fail, match='apache-airflow-providers'):
        t.kw['python_callable']()


def test_modo_invalido_falla_en_la_tarea_no_al_importar(monkeypatch):
    m, _ = _cargar_dag(monkeypatch, 'nube')
    with pytest.raises(_Fail, match='no es válido'):
        _dag_de(m).tareas['ejecutar_lote'].kw['python_callable']()


def test_el_script_del_contenedor_no_tiene_plantillas_jinja_accidentales(monkeypatch):
    m, _ = _cargar_dag(monkeypatch, 'kubernetes')
    for texto in (m.RESUMEN_PY, m.ORDEN_LOTE, m.ORDEN_COMPROBAR):
        assert not any(x in texto for x in ('{{', '{%', '{#')), 'Jinja lo interpretaría'
    ast.parse(m.RESUMEN_PY)
    ast.parse(m.ORDEN_COMPROBAR)


def test_los_valores_entran_como_argumentos_no_dentro_del_script(monkeypatch):
    m, _ = _cargar_dag(monkeypatch, 'kubernetes')
    assert 'params' not in m.ORDEN_LOTE and '"$CORTE"' in m.ORDEN_LOTE and '"$CAP"' in m.ORDEN_LOTE


def test_xcom_como_diccionario_o_como_ultima_linea(monkeypatch):
    m, _ = _cargar_dag(monkeypatch, 'docker')
    assert m._como_dict({'a': 1}) == {'a': 1}
    assert m._como_dict('basura\n{"a": 2}\n') == {'a': 2}
    assert m._como_dict(b'{"a": 3}') == {'a': 3}


# ------------------------------------------------------------------------------------------------ entradas
def test_validar_entradas():
    assert L.validar_entradas('2011-12-10', 'europe-west1-docker.pkg.dev/p/curso/retencion-lote:v1', '0.10')[0] == '2011-12-10'
    assert L.validar_entradas('', 'retencion-lote:local', 0.1)[0] == ''
    for corte, imagen, cap in [('10/12/2011', 'a:b', '0.1'), ('', '', '0.1'), ('', 'a b; rm -rf /', '0.1'), ('', 'abc:1', '2'), ('', 'abc:1', '0'), ('', 'abc:1', '$(x)')]:
        with pytest.raises(L.ErrorSalida):
            L.validar_entradas(corte, imagen, cap)


def test_los_tramos_son_los_de_la_configuracion_del_proyecto():
    sys.path.insert(0, str(PROYECTO))
    try:
        from ia_mlops import config
    finally:
        sys.path.remove(str(PROYECTO))
    assert [(s['segmento'], s['desde']) for s in config.SEGMENTOS_RECOMPRA] == list(L.TRAMOS)


# ------------------------------------------------------------------------------------------------ salida REAL del lote
def _huella(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


@pytest.fixture(scope='module')
def lote_real(tmp_path_factory):
    db = PROYECTO / 'data' / 'processed' / 'curso.db'
    modelo = PROYECTO / 'models' / 'metadatos.json'
    if not (db.is_file() and modelo.is_file()):
        pytest.skip('Falta curso.db o models/ (ejecuta python -m ia_mlops.pipeline en 04-Proyecto-Base)')
    antes = (_huella(db), _huella(modelo), _huella(PROYECTO / 'models' / 'mlflow.db'))
    carpeta = tmp_path_factory.mktemp('lote')
    (carpeta / 'curso.db').write_bytes(db.read_bytes())
    env = dict(os.environ, CURSO_DB=str(carpeta / 'curso.db'), CURSO_REPORTES=str(carpeta / 'reports'), MLFLOW_DISABLE_AGENT_HINT='1')
    r = subprocess.run([sys.executable, '-m', 'ia_mlops.explotacion', '--corte', '2011-12-10', '--capacidad', '0.1', '--sin-guardar-fs'],
                       cwd=PROYECTO, env=env, capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stdout + r.stderr
    yield carpeta / 'reports', r.stdout
    assert (_huella(db), _huella(modelo), _huella(PROYECTO / 'models' / 'mlflow.db')) == antes, 'el lote de prueba tocó el proyecto'


def test_resumir_y_validar_sobre_la_salida_real(lote_real):
    reportes, _ = lote_real
    r = L.resumir_salida(str(reportes))
    assert r['filas'] == r['clientes_puntuados'] > 100 and r['nulos'] == 0
    assert 0 <= r['prob_min'] <= r['prob_max'] <= 1 and sum(r['tramos'].values()) == r['filas'] and r['deciles'] == list(range(1, 11))
    assert r['en_campana'] == r['clientes_en_campana'] == 15
    avisos = L.validar_salida(r, {'huella_datos': r['huella_datos']})
    assert any('fuera del rango' in a for a in avisos)
    assert 'Tramos de negocio' in L.resumen_markdown(r, avisos)
    json.dumps(r)


def test_la_funcion_enviada_al_contenedor_da_lo_mismo_que_la_local(lote_real, monkeypatch):
    """El DAG manda el código fuente de resumir_salida a `python -c`: se ejecuta tal cual y la última línea es el JSON."""
    reportes, _ = lote_real
    m, _ = _cargar_dag(monkeypatch, 'docker')
    env = dict(os.environ, CURSO_REPORTES=str(reportes))
    r = subprocess.run([sys.executable, '-c', m.RESUMEN_PY], env=env, capture_output=True, text=True, timeout=60, cwd=EXTRA)
    assert r.returncode == 0, r.stderr
    assert m._como_dict(r.stdout) == L.resumir_salida(str(reportes))


def _corromper(r, **cambios):
    return {**r, **cambios}


def test_la_validacion_detecta_cada_fallo(lote_real):
    reportes, _ = lote_real
    r = L.resumir_salida(str(reportes))
    casos = {
        'vacío': dict(filas=0, clientes_puntuados=0, prob_min=None, prob_max=None, tramos={'alta': 0, 'media': 0, 'baja': 0}, en_campana=0),
        'probabilidad > 1': dict(prob_max=1.2),
        'probabilidad < 0': dict(prob_min=-0.1),
        'nulos': dict(nulos=3),
        'filas distintas': dict(clientes_puntuados=r['filas'] + 1),
        'tramo desconocido': dict(tramos={'alta': 1, 'otro': r['filas'] - 1}),
        'tramos no suman': dict(tramos={'alta': 1, 'media': 1, 'baja': 1}),
        'deciles': dict(deciles=[1, 2, 3]),
        'campaña': dict(en_campana=r['en_campana'] + 5),
    }
    for nombre, cambio in casos.items():
        with pytest.raises(L.ErrorSalida):
            L.validar_salida(_corromper(r, **cambio))
    with pytest.raises(L.ErrorSalida, match='no es el que declaraba'):
        L.validar_salida(r, {'huella_datos': 'otra'})
    with pytest.raises(L.ErrorSalida, match='se exigía'):
        L.validar_salida(r, None, 'otra')
    with pytest.raises(L.ErrorSalida, match='no devolvió un resumen'):
        L.validar_salida(None)


def test_el_comando_del_dag_es_el_de_comandos_md():
    comandos = (EXTRA / 'comandos.md').read_text(encoding='utf-8')
    texto = DAG_PY.read_text(encoding='utf-8')
    for opcion in ('--corte', '--capacidad', '--sin-guardar-fs'):
        assert opcion in texto and opcion in comandos
    assert 'python -m ia_mlops.explotacion --corte' in comandos
    # esas opciones existen de verdad en explotacion.py
    fuente = (PROYECTO / 'ia_mlops' / 'explotacion.py').read_text(encoding='utf-8')
    for opcion in ('--corte', '--capacidad', '--sin-guardar-fs'):
        assert f"'{opcion}'" in fuente
