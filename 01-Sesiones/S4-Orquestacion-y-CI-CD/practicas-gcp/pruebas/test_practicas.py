"""Pruebas de las practicas de GCP (S4). No necesitan Google Cloud: revisan los ficheros.

Ejecutar desde practicas-gcp:   python -m pytest -q pruebas -p no:cacheprovider
"""
import json
import os
import py_compile
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

BASE = Path(__file__).resolve().parents[1]
PROYECTO_BASE = BASE.parents[2] / '04-Proyecto-Base'
PRACTICAS = ['01-docker-artifact-registry', '02-kubernetes-gke', '03-dataproc-spark', '04-vertex-modelo', '05-vertex-llm']
SCRIPTS_PRACTICA = ['crear.sh', 'probar.sh', 'borrar.sh', 'variables.sh']
REGIONES_PERMITIDAS = {'southamerica-west1', 'southamerica-east1'}     # la segunda solo como alternativa citada en comentarios y READMEs
RE_REGION = re.compile(r'\b(?:southamerica|northamerica|us|europe|asia|me|africa|australia)-[a-z]+\d+\b')

# (orden que crea algo en crear.sh, lo que debe aparecer en borrar.sh para deshacerlo)
CREA_Y_BORRA = [
    ('artifacts repositories create', 'artifacts repositories delete'),
    ('run deploy', 'run services delete'),
    ('container clusters create-auto', 'container clusters delete'),
    ('storage buckets create', 'storage rm'),
    ('dataproc batches submit', 'dataproc batches delete'),
    ('add-iam-policy-binding', 'remove-iam-policy-binding'),
    ('ai models upload', 'ai models delete'),
    ('ai endpoints create', 'ai endpoints delete'),
    ('ai endpoints deploy-model', 'ai endpoints undeploy-model'),
]
SOLO_VISUAL = {'NOMBRE_DESPLIEGUE'}      # nombre visible que se pone al desplegar; no es un recurso que haya que borrar aparte


def _texto(ruta):
    return Path(ruta).read_text(encoding='utf-8')


def _ordenes(sh):
    """Las ordenes del script con las lineas continuadas con \\ unidas en una sola, sin comentarios."""
    sh = re.sub(r'\\\n\s*', ' ', sh)
    return [l.strip() for l in sh.splitlines() if l.strip() and not l.strip().startswith('#')]


def _todos_los_scripts():
    return sorted(p for p in BASE.rglob('*') if p.suffix in ('.sh', '.py', '.yaml') and 'pruebas' not in p.parts and '__pycache__' not in p.parts)


def _bash():
    for c in (os.environ.get('CURSO_BASH'), r'C:\bk\software\git\bin\bash.exe', shutil.which('bash')):
        if c and Path(c).exists():
            return c
    return None


# ------------------------------------------------------------------------------------------------------ estructura
@pytest.mark.parametrize('practica', PRACTICAS)
def test_cada_practica_tiene_readme_y_scripts(practica):
    carpeta = BASE / practica
    assert (carpeta / 'README.md').is_file()
    for s in SCRIPTS_PRACTICA:
        assert (carpeta / s).is_file(), f'{practica}/{s}'


@pytest.mark.parametrize('practica', PRACTICAS)
def test_readme_tiene_las_secciones_pedidas(practica):
    t = _texto(BASE / practica / 'README.md').lower()
    for clave in ('objetivo', 'tiempo estimado', 'coste aproximado', '## pasos', 'qué debes ver', 'si falla'):
        assert clave in t, f'{practica}: falta «{clave}»'


def test_readme_general_y_borrar_todo():
    t = _texto(BASE / 'README.md')
    for p in PRACTICAS:
        assert p in t
    assert 'CREA → PRUEBA → BORRA' in t
    todo = _texto(BASE / 'borrar-todo.sh')
    for p in PRACTICAS:
        assert p in todo, f'borrar-todo.sh no incluye {p}'
    assert todo.index('01-docker-artifact-registry') > todo.index('02-kubernetes-gke'), 'la 01 debe borrarse despues de la 02'


# ------------------------------------------------------------------------------------------------------ sintaxis
def test_sh_con_lf_sin_bom_y_con_shebang():
    for p in BASE.rglob('*.sh'):
        b = p.read_bytes()
        assert b'\r' not in b, f'{p.name}: CRLF'
        assert not b.startswith(b'\xef\xbb\xbf'), f'{p.name}: BOM'
        assert b.startswith(b'#!/usr/bin/env bash'), f'{p.name}: sin shebang'


def test_bash_n_pasa():
    bash = _bash()
    if not bash:
        pytest.skip('no hay bash')
    for p in sorted(BASE.rglob('*.sh')):
        r = subprocess.run([bash, '-n', p.as_posix()], capture_output=True, text=True)
        assert r.returncode == 0, f'{p}: {r.stderr}'


def test_los_scripts_de_practica_usan_set_euo_pipefail():
    for practica in PRACTICAS:
        for s in ('crear.sh', 'probar.sh', 'borrar.sh'):
            assert 'set -euo pipefail' in _texto(BASE / practica / s), f'{practica}/{s}'
        for s in ('crear.sh', 'probar.sh', 'borrar.sh'):
            assert 'source "$DIR/variables.sh"' in _texto(BASE / practica / s), f'{practica}/{s} no carga variables.sh'
    assert 'set -uo pipefail' in _texto(BASE / 'borrar-todo.sh')    # sigue aunque una practica falle (lo avisa al final)


def test_los_python_compilan(tmp_path):
    for p in BASE.rglob('*.py'):
        py_compile.compile(str(p), cfile=str(tmp_path / (p.name + 'c')), doraise=True)


def test_yaml_valido_y_con_lo_esperado():
    docs = {}
    for p in sorted((BASE / '02-kubernetes-gke' / 'manifiestos').glob('*.yaml')):
        docs[p.name] = yaml.safe_load(p.read_text(encoding='utf-8'))
    assert {d['kind'] for d in docs.values()} == {'Namespace', 'Deployment', 'Service'}
    dep = docs['deployment.yaml']
    assert dep['metadata']['namespace'] == docs['service.yaml']['metadata']['namespace'] == docs['namespace.yaml']['metadata']['name']
    c = dep['spec']['template']['spec']['containers'][0]
    assert c['image'] == '__IMAGEN__'
    assert c['readinessProbe']['httpGet']['path'] == '/listo' and c['livenessProbe']['httpGet']['path'] == '/salud'
    assert c['resources']['requests'] == c['resources']['limits']              # Autopilot iguala los limites a lo pedido
    assert dep['spec']['template']['spec']['securityContext']['runAsNonRoot'] is True
    assert docs['service.yaml']['spec']['type'] == 'ClusterIP'                  # nada de IP publica de pago
    assert dep['spec']['selector']['matchLabels'] == docs['service.yaml']['spec']['selector']
    assert '__IMAGEN__' in _texto(BASE / '02-kubernetes-gke' / 'crear.sh')       # crear.sh sustituye el marcador


# ------------------------------------------------------------------------------------------------------ seguridad
def test_ningun_script_crea_claves():
    prohibido = re.compile(r'service-accounts\s+keys\s+create|iam\s+service-accounts\s+keys|GOOGLE_APPLICATION_CREDENTIALS|private_key|--key-file|allUsers|--allow-unauthenticated', re.I)
    for p in _todos_los_scripts():
        for n, linea in enumerate(_texto(p).splitlines(), 1):
            if prohibido.search(linea) and not linea.lstrip().startswith('#'):
                pytest.fail(f'{p.relative_to(BASE)}:{n}: {linea.strip()}')
    assert '--no-allow-unauthenticated' in _texto(BASE / '01-docker-artifact-registry' / 'crear.sh')


def test_ninguna_etiqueta_latest_en_nuestras_imagenes():
    comun = _texto(BASE / 'comun.sh')
    assert 'ETIQUETA_IMAGEN="v1"' in comun
    for p in BASE.rglob('*.sh'):
        for linea in _ordenes(_texto(p)):
            if 'IMAGEN_COMPLETA' in linea:
                assert ':latest' not in linea


# ------------------------------------------------------------------------------------------------------ crear <-> borrar
@pytest.mark.parametrize('practica', PRACTICAS)
def test_borrar_deshace_lo_que_crea(practica):
    crear = _ordenes(_texto(BASE / practica / 'crear.sh'))
    borrar_txt = _texto(BASE / practica / 'borrar.sh')
    for crea, borra in CREA_Y_BORRA:
        for orden in (o for o in crear if crea in o):
            assert borra in borrar_txt, f'{practica}: crear.sh hace «{crea}» pero borrar.sh no hace «{borra}»'
            if crea != 'add-iam-policy-binding':
                for nombre in set(re.findall(r'\$\{?(NOMBRE_[A-Z_]+)', orden)) - SOLO_VISUAL:
                    assert nombre in borrar_txt, f'{practica}: «{crea}» usa {nombre} y borrar.sh no lo menciona'
    if any(re.search(r'pip"? install', o) and 'VENV16' in o for o in crear):      # 04: entorno propio
        assert 'rm -rf "$VENV16"' in borrar_txt
    if practica == '05-vertex-llm':
        assert re.search(r'pip"? uninstall', borrar_txt)


@pytest.mark.parametrize('practica', PRACTICAS)
def test_los_nombres_de_recursos_se_definen_una_sola_vez_en_variables(practica):
    var = _texto(BASE / practica / 'variables.sh')
    for s in ('crear.sh', 'borrar.sh', 'probar.sh'):
        for linea in _ordenes(_texto(BASE / practica / s)):
            assert not re.match(r'NOMBRE_[A-Z_]+=', linea), f'{practica}/{s} redefine un nombre de recurso: {linea}'
    for nombre in re.findall(r'^(NOMBRE_[A-Z_]+)=', var, re.M):
        assert nombre  # definidos aqui; las comprobaciones de uso estan en test_borrar_deshace_lo_que_crea


@pytest.mark.parametrize('practica', PRACTICAS)
def test_probar_no_crea_recursos_en_gcp(practica):
    for linea in _ordenes(_texto(BASE / practica / 'probar.sh')):
        assert not re.search(r'gcloud .*\b(create|create-auto|deploy|upload|deploy-model|submit)\b', linea), linea
        assert 'add-iam-policy-binding' not in linea


@pytest.mark.parametrize('practica', PRACTICAS)
def test_borrar_lista_lo_que_queda(practica):
    t = _texto(BASE / practica / 'borrar.sh')
    assert 'Lo que queda' in t


# ------------------------------------------------------------------------------------------------------ regiones
def test_regiones_son_las_declaradas():
    comun = _texto(BASE / 'comun.sh')
    assert 'REGION="${CURSO_REGION:-southamerica-west1}"' in comun
    assert 'REGION_VERTEX="${CURSO_REGION_VERTEX:-$REGION}"' in comun
    assert 'REGION_GEMINI="${CURSO_REGION_GEMINI:-global}"' in comun
    assert 'PROYECTO="${CURSO_PROYECTO:-project-curso-ml-ia}"' in comun
    for p in _todos_los_scripts():
        for region in RE_REGION.findall(_texto(p)):
            assert region in REGIONES_PERMITIDAS, f'{p.relative_to(BASE)}: region no declarada {region}'
        for orden in _ordenes(_texto(p)) if p.suffix == '.sh' else []:
            assert not re.search(r'--(region|location)[= ]+"?(southamerica|us|europe)', orden), f'{p.relative_to(BASE)}: region fija en una orden: {orden}'
    # la unica region literal ejecutable esta en comun.sh
    for p in BASE.rglob('*.sh'):
        if p.name == 'comun.sh':
            continue
        for orden in _ordenes(_texto(p)):
            assert 'southamerica-west1' not in orden, f'{p.relative_to(BASE)}: {orden}'


def test_el_contenedor_de_vertex_es_de_scikit_learn_1_6_y_con_latest():
    v = _texto(BASE / '04-vertex-modelo' / 'variables.sh')
    assert 'sklearn-cpu.1-6:latest' in v
    assert 'VERSION_SKLEARN="1.6.' in v


# ------------------------------------------------------------------------------------------------------ coherencia con el proyecto
def _cargar_proyecto():
    if not (PROYECTO_BASE / 'ia_mlops').is_dir():
        pytest.skip('no esta 04-Proyecto-Base')
    sys.path.insert(0, str(PROYECTO_BASE))
    from ia_mlops import config
    return config


def test_las_13_variables_y_el_orden_del_modelo():
    config = _cargar_proyecto()
    assert len(config.FEATURES) == 13
    ejemplos = json.loads(_texto(BASE / 'clientes_ejemplo.json'))
    for nombre, c in ejemplos.items():
        assert list(c) == config.FEATURES, nombre
    readme = _texto(BASE / '04-vertex-modelo' / 'README.md')
    posiciones = [readme.index(f'`{v}`') for v in config.FEATURES]
    assert posiciones == sorted(posiciones), 'la tabla del README no sigue el orden del modelo'
    meta = PROYECTO_BASE / 'models' / 'metadatos.json'
    if meta.exists():
        assert json.loads(meta.read_text(encoding='utf-8'))['variables'] == config.FEATURES


def test_los_clientes_de_ejemplo_cumplen_el_contrato_de_la_api():
    _cargar_proyecto()
    pytest.importorskip('pydantic')
    from ia_mlops.api import esquemas
    for nombre, c in json.loads(_texto(BASE / 'clientes_ejemplo.json')).items():
        esquemas.Cliente(**c)


def test_exportar_datos_y_paridad_de_spark(tmp_path):
    base = PROYECTO_BASE / 'data' / 'processed' / 'curso.db'
    if not base.exists():
        pytest.skip('no esta curso.db')
    sys.path.insert(0, str(BASE / '03-dataproc-spark'))
    import comprobar_resultado
    import exportar_datos
    n, columnas = exportar_datos.exportar(base, tmp_path / 'ventas.csv')
    assert n > 0 and {'factura_id', 'cliente_id', 'pais', 'monto_linea', 'es_venta_valida'} <= set(columnas)
    por_pais = comprobar_resultado.calcular(tmp_path / 'ventas.csv')
    assert 'United Kingdom' in por_pais
    # el job de Spark usa las mismas columnas que exporta el script
    job = _texto(BASE / '03-dataproc-spark' / 'analisis_ventas.py')
    for c in ('es_venta_valida', 'factura_id', 'cliente_id', 'monto_linea', 'fecha_factura', 'pais'):
        assert c in job
    # simular la salida de Spark con el propio calculo y comprobar que comprobar_resultado la acepta (y rechaza una alterada)
    salida = tmp_path / 'por_pais'
    salida.mkdir()
    filas = ['pais,facturas,clientes,monto_total,ticket_medio'] + [f'{p},{f},{c},{m},0' for p, (f, c, m) in por_pais.items()]
    (salida / 'part-0000.csv').write_text('\n'.join(filas), encoding='utf-8')
    comando = [sys.executable, '-I', str(BASE / '03-dataproc-spark' / 'comprobar_resultado.py'), '--entrada', str(tmp_path / 'ventas.csv'), '--por-pais', str(salida)]
    assert subprocess.run(comando, capture_output=True).returncode == 0
    (salida / 'part-0000.csv').write_text('\n'.join(filas).replace(',', ',9', 1), encoding='utf-8')
    assert subprocess.run(comando, capture_output=True).returncode != 0


def test_comparar_respuesta_acepta_clase_y_probabilidad(tmp_path):
    sys.path.insert(0, str(BASE / '04-vertex-modelo'))
    import comparar_respuesta as c
    assert c.predicciones('{"predictions": [1.0, 0.0], "deployedModelId": "1"}') == [1.0, 0.0]
    assert c.predicciones('[[0.25], [0.75]]') == [0.25, 0.75]
    esperado = tmp_path / 'e.json'
    esperado.write_text(json.dumps([{'cliente': 'a', 'probabilidad': 0.8, 'clase': 1}, {'cliente': 'b', 'probabilidad': 0.2, 'clase': 0}]), encoding='utf-8')
    for cuerpo, codigo in (('[1, 0]', 0), ('[0, 0]', 1), ('[0.8, 0.2]', 0)):
        r = tmp_path / 'r.json'
        r.write_text(cuerpo, encoding='utf-8')
        res = subprocess.run([sys.executable, '-I', str(BASE / '04-vertex-modelo' / 'comparar_respuesta.py'), '--respuesta', str(r), '--esperado', str(esperado)], capture_output=True)
        assert res.returncode == codigo, (cuerpo, res.stdout)


def test_las_instancias_de_vertex_son_listas_de_13_numeros():
    """Reentrena con la version local de scikit-learn (no con la 1.6) solo para comprobar el formato de salida de entrenar_sklearn16.py."""
    base = PROYECTO_BASE / 'data' / 'processed' / 'curso.db'
    if not base.exists():
        pytest.skip('no esta curso.db')
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        r = subprocess.run([sys.executable, '-I', str(BASE / '04-vertex-modelo' / 'entrenar_sklearn16.py'), '--proyecto', str(PROYECTO_BASE),
                            '--salida', d, '--clientes', str(BASE / 'clientes_ejemplo.json')], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        inst = json.loads((Path(d) / 'instancias.json').read_text(encoding='utf-8'))['instances']
        assert len(inst) == 2 and all(len(i) == 13 and all(isinstance(x, float) for x in i) for i in inst)
        esperado = json.loads((Path(d) / 'esperado_local.json').read_text(encoding='utf-8'))
        assert all(0 <= e['probabilidad'] <= 1 and e['clase'] == int(e['probabilidad'] >= 0.5) for e in esperado)
        assert (Path(d) / 'model.joblib').is_file()


def test_el_aviso_de_cifra_acepta_uno_o_dos_decimales_con_coma_o_punto():
    """Falso positivo real (25/11/2026): Gemini escribió «82.79%» y el script avisó de que no citaba el 82.8 %."""
    sys.path.insert(0, str(BASE / '05-vertex-llm'))
    import explicar_prediccion as e
    prob = 0.8279
    for texto in ('probabilidad del **82.79%** de comprar', 'un 82,79 % de probabilidad', 'un 82.8% de probabilidad',
                  'un 82,8 % de probabilidad', 'alrededor del 83 % de probabilidad'):
        assert e.cita_la_probabilidad(texto, prob), texto
    for texto in ('un 28.5% de probabilidad', 'gastó 1250.83 euros', 'la referencia 2083', 'sin ninguna cifra', 'un 82.7% de probabilidad'):
        assert not e.cita_la_probabilidad(texto, prob), texto
    assert e.cita_la_probabilidad('un 27,6 % de probabilidad', 0.2760) and not e.cita_la_probabilidad('un 82.8%', 0.2760)


def test_la_explicacion_del_llm_usa_pesos_exactos():
    _cargar_proyecto()
    modelo_ruta = PROYECTO_BASE / 'models' / 'modelo.joblib'
    if not modelo_ruta.exists():
        pytest.skip('no hay modelo entrenado')
    joblib = pytest.importorskip('joblib')
    import pandas as pd
    sys.path.insert(0, str(BASE / '05-vertex-llm'))
    import explicar_prediccion as e
    modelo = joblib.load(modelo_ruta)
    meta = json.loads((PROYECTO_BASE / 'models' / 'metadatos.json').read_text(encoding='utf-8'))
    for c in json.loads(_texto(BASE / 'clientes_ejemplo.json')).values():
        valores = [c[v] for v in meta['variables']]
        pesos, prob = e.pesos_exactos(modelo, meta['variables'], valores)
        real = float(modelo.predict_proba(pd.DataFrame([valores], columns=meta['variables']).astype(float))[0, 1])
        assert len(pesos) == 13 and abs(prob - real) < 1e-9

# ------------------------------------------------------------------------------------------------------ Dataproc: buckets propios
def test_borrar_de_dataproc_quita_los_buckets_que_crea_dataproc_solo_si_no_queda_nada():
    """Visto el 26/11/2026: Dataproc sin servidor crea dataproc-staging-… y dataproc-temp-… por su cuenta y borrar.sh no los quitaba.
    Son compartidos por todo el Dataproc del proyecto: solo se borran si ya no queda ningún lote ni clúster en la región."""
    sh = _texto(BASE / '03-dataproc-spark' / 'borrar.sh')
    assert 'dataproc-(staging|temp)-' in sh
    ordenes = ' '.join(_ordenes(sh))
    assert 'dataproc batches list' in ordenes and 'dataproc clusters list' in ordenes
    assert 'OTROS_LOTES" = "0"' in ordenes and 'CLUSTERES" = "0"' in ordenes     # la salvaguarda
    assert 'storage rm -r "gs://$B"' in ordenes
    readme = _texto(BASE / '03-dataproc-spark' / 'README.md')
    assert 'dataproc-staging' in readme and 'compartidos' in readme
