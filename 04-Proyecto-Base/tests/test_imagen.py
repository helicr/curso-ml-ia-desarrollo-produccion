"""Pruebas de la imagen Docker SIN Docker: lo que se puede comprobar leyendo el Dockerfile, el .dockerignore y las dependencias.

Que NO prueban: que `docker build` y `docker run` funcionen. Eso solo lo demuestra ejecutarlos (en Codespaces o en GitHub Actions: ver
deploy/github-actions/ci.yml). Lo que si evitan es llegar al `docker build` con errores que se ven a simple vista.

El Dockerfile es multi-etapa: el código sale de la etapa «fuente-git» (el repositorio clonado en el commit pedido, por defecto) o de
«fuente-contexto» (la carpeta de trabajo, con --build-arg FUENTE=contexto); el modelo entra por el contexto con nombre «modelo»
(--build-context modelo=models). Las pruebas leen la etapa FINAL (la imagen que se sirve) y comprueban que las dos fuentes dejan lo mismo.
"""
import json
import re
import shutil
import urllib.request
from pathlib import Path

import pytest

from ia_mlops import config
from ia_mlops.modeling import train

RAIZ = config.RAIZ
DOCKERFILE = RAIZ / 'deploy' / 'docker' / 'Dockerfile'


def _instrucciones(texto):
    """Instrucciones del Dockerfile (une las lineas que terminan en «\\» y descarta comentarios)."""
    unido = re.sub(r'\\\s*\n', ' ', texto)
    lineas = [l.strip() for l in unido.splitlines() if l.strip() and not l.strip().startswith('#')]
    return [(l.split(None, 1)[0].upper(), l.split(None, 1)[1] if ' ' in l else '') for l in lineas]


def _etapas(texto):
    """[(nombre o None, imagen base, [instrucciones de la etapa])], en orden. Lo que va antes del primer FROM (ARG globales) no cuenta."""
    etapas = []
    for inst, resto in _instrucciones(texto):
        if inst == 'FROM':
            partes = resto.split()
            nombre = partes[2] if len(partes) >= 3 and partes[1].upper() == 'AS' else None
            etapas.append((nombre, partes[0], []))
        elif etapas:
            etapas[-1][2].append((inst, resto))
    return etapas


def _globales(texto):
    """Instrucciones antes del primer FROM (solo puede haber ARG)."""
    salida = []
    for inst, resto in _instrucciones(texto):
        if inst == 'FROM':
            break
        salida.append((inst, resto))
    return salida


def _final(texto):
    """Instrucciones de la ÚLTIMA etapa: la imagen que se construye y se sirve."""
    return _etapas(texto)[-1][2]


def _etapa(texto, nombre):
    return next(ins for n, _, ins in _etapas(texto) if n == nombre)


def _copy(resto):
    """(etapa o contexto de --from, [orígenes], destino) de un COPY."""
    partes = resto.split()
    desde = next((p.split('=', 1)[1] for p in partes if p.startswith('--from=')), None)
    sin_opciones = [p for p in partes if not p.startswith('--')]
    return desde, sin_opciones[:-1], sin_opciones[-1]


def _copias(ins):
    return [_copy(r) for i, r in ins if i == 'COPY']


def _destino(origen, destino, es_carpeta):
    """Dónde queda «origen» al copiarlo a «destino» (COPY y cp -r): una carpeta deja su contenido; un archivo a «x/» (o a «.») queda en «x/nombre»."""
    carpeta = '' if destino in ('.', './') else destino.rstrip('/')
    if es_carpeta:
        return carpeta or '.'
    if destino.endswith('/') or destino == '.':
        nombre = Path(origen.rstrip('/')).name
        return f'{carpeta}/{nombre}' if carpeta else nombre
    return destino


def _src_del_contexto(texto):
    """{ruta en /src: ruta en la carpeta del proyecto} de la etapa «fuente-contexto» (FUENTE=contexto)."""
    salida = {}
    for desde, origenes, destino in _copias(_etapa(texto, 'fuente-contexto')):
        assert desde is None, 'fuente-contexto copia de la carpeta del proyecto, no de otra etapa'
        for o in origenes:
            salida[_destino(o, destino, (RAIZ / o).is_dir())] = o.rstrip('/')
    return salida


def _src_del_clon(texto):
    """{ruta en /src: ruta en la carpeta del proyecto} de lo que copia la etapa «fuente-git» desde el clon (cp ... /tmp/repo/"$CARPETA"/x ... destino)."""
    salida = {}
    for inst, resto in _etapa(texto, 'fuente-git'):
        if inst != 'RUN':
            continue
        for orden in resto.split(';'):
            partes = orden.split()
            if not partes or partes[0] != 'cp':
                continue
            args = [p for p in partes[1:] if not p.startswith('-')]
            for o in args[:-1]:
                m = re.fullmatch(r'/tmp/repo/"\$CARPETA"/(\S+)', o)
                assert m, f'fuente-git copia algo que no es de la carpeta del proyecto en el clon: {o}'
                salida[_destino(m.group(1), args[-1], (RAIZ / m.group(1)).is_dir())] = m.group(1).rstrip('/')
    return salida


def _orden_del_clon(texto):
    """Las órdenes de shell del RUN que clona (el que usa el secreto git_token)."""
    run = next(r for i, r in _etapa(texto, 'fuente-git') if i == 'RUN' and 'git_token' in r)
    return [o.strip() for o in run.split(';') if o.strip()]


def _regex(patron):
    """Traduce un patron de .dockerignore a expresion regular: `*` no cruza «/», `**/` cruza carpetas, `?` es un caracter, `[abc]` es un conjunto."""
    p, salida, i = patron.rstrip('/'), '', 0
    while i < len(p):
        if p.startswith('**/', i):
            salida += '(?:.*/)?'
            i += 3
        elif p[i] == '*':
            salida += '[^/]*'
            i += 1
        elif p[i] == '?':
            salida += '[^/]'
            i += 1
        elif p[i] == '[':
            j = p.index(']', i)
            salida += p[i:j + 1]
            i = j + 1
        else:
            salida += re.escape(p[i])
            i += 1
    return re.compile(salida)


def _ignorado(ruta, patrones):
    """Reglas de .dockerignore: un patron se compara con la ruta (relativa al contexto) y con cada una de sus carpetas; si coincide una carpeta, se excluye todo lo que contiene.

    Ojo: `*.pyc` sin «**/» solo vale en la raiz del contexto; para cualquier carpeta hay que escribir `**/*.pyc`.
    """
    partes = ruta.split('/')
    prefijos = ['/'.join(partes[:k]) for k in range(1, len(partes) + 1)]
    return any(_regex(p).fullmatch(pre) for p in patrones for pre in prefijos)


def _patrones():
    return [l.strip() for l in (RAIZ / '.dockerignore').read_text(encoding='utf-8').splitlines() if l.strip() and not l.startswith('#')]


def _texto():
    return DOCKERFILE.read_text(encoding='utf-8')


# --- Dockerfile: la imagen que se sirve (etapa final) -----------------------------------------------------------------------------

def test_el_dockerfile_usa_la_misma_version_de_python_que_el_entorno():
    etapas = _etapas(_texto())
    assert etapas[-1][1] == 'python:3.11-slim'           # environment.yml fija python=3.11
    internas = {n for n, _, _ in etapas if n} | {'scratch'}
    imagenes = [b for _, b, _ in etapas if b not in internas and not b.startswith('fuente-')]
    assert imagenes and set(imagenes) == {'python:3.11-slim'}   # la etapa del clon parte de la misma base: una sola imagen que descargar


def test_las_dependencias_se_instalan_antes_de_copiar_el_codigo():
    """Si el codigo se copiara primero, cualquier cambio de una linea reinstalaria todas las dependencias."""
    orden = [(i, r) for i, r in _final(_texto()) if i in ('COPY', 'RUN')]
    instalar = next(k for k, (i, t) in enumerate(orden) if i == 'RUN' and 'pip install' in t)
    codigo = next(k for k, (i, t) in enumerate(orden) if i == 'COPY' and 'ia_mlops/' in t)
    assert instalar < codigo
    assert any(i == 'COPY' and 'requirements-api.lock' in t for i, t in orden[:instalar])
    assert 'requirements-api.lock' in [t for i, t in orden if i == 'RUN' and 'pip install' in t][0]


def test_no_se_ejecuta_como_root_y_tiene_comprobacion_de_salud():
    final = _final(_texto())
    usuario = [r for i, r in final if i == 'USER']
    assert usuario and usuario[-1] not in ('root', '0')
    salud = [r for i, r in final if i == 'HEALTHCHECK']
    assert salud and '/salud' in salud[0] and '8080' in salud[0]


def test_el_puerto_y_el_comando_coinciden_con_la_aplicacion():
    ins = _final(_texto())
    assert [r for i, r in ins if i == 'EXPOSE'] == ['8080']
    cmd = json.loads([r for i, r in ins if i == 'CMD'][0])
    assert cmd[:2] == ['uvicorn', 'ia_mlops.api.app:app'] and cmd[cmd.index('--port') + 1] == '8080'
    from ia_mlops.api.app import app            # el objeto que nombra el CMD existe
    assert app.title


def test_el_dockerfile_dice_donde_estan_los_modelos():
    final = _final(_texto())
    env = ' '.join(r for i, r in final if i == 'ENV')
    assert 'CURSO_MODELOS=/app/models' in env
    # y el modelo se copia justo ahí: WORKDIR /app + destino models/...
    assert [r for i, r in final if i == 'WORKDIR'] == ['/app']
    destinos = [d for desde, _, d in _copias(final) if desde == 'modelo']
    assert destinos and all(d.startswith('models/') for d in destinos)


def test_el_dockerfile_no_copia_datos_ni_secretos():
    texto = _texto()
    del_proyecto = list(_src_del_contexto(texto).values()) + list(_src_del_clon(texto).values())
    del_proyecto += [o for desde, origenes, _ in _copias(_final(texto)) if desde is None for o in origenes]
    for origen in del_proyecto:
        assert not origen.startswith(('data', 'sql', 'tests', 'notebooks', '.env', '.git', 'models')) and '.db' not in origen, origen
    for desde, origenes, _ in _copias(_final(texto)):
        if desde == 'modelo':                   # del contexto «modelo», solo el modelo MLflow y sus metadatos
            assert set(origenes) <= {'modelo_mlflow/', 'metadatos.json'}, origenes


# --- De dónde sale el código: el clon del commit (o la carpeta, para desarrollar) ----------------------------------------------------

def test_el_codigo_sale_de_la_etapa_fuente_elegida_con_fuente_git_por_defecto():
    texto = _texto()
    assert ('ARG', 'FUENTE=git') in _globales(texto)
    nombres = {n: b for n, b, _ in _etapas(texto)}
    assert nombres.get('fuente') == 'fuente-${FUENTE}' and 'fuente-git' in nombres and nombres.get('fuente-contexto') == 'scratch'
    # La imagen final no copia nada de la carpeta: el código, de la etapa «fuente»; el modelo, del contexto «modelo».
    desdes = [desde for desde, _, _ in _copias(_final(texto))]
    assert desdes and set(desdes) == {'fuente', 'modelo'}, desdes
    src = _src_del_contexto(texto)
    for desde, origenes, _ in _copias(_final(texto)):
        if desde == 'fuente':
            for o in origenes:
                assert o.startswith('/src/') and o.rstrip('/') in src, o


def test_el_clon_y_la_carpeta_dejan_lo_mismo_en_src():
    """FUENTE=git y FUENTE=contexto deben dar la MISMA imagen (con el mismo código): si una copiara algo que la otra no, una de las dos fallaría."""
    texto = _texto()
    assert _src_del_clon(texto) == _src_del_contexto(texto)


def test_la_etapa_del_clon_clona_el_commit_pedido_y_borra_el_clon():
    texto = _texto()
    args = [r for i, r in _etapa(texto, 'fuente-git') if i == 'ARG']
    assert 'REF=develop' in args and 'CARPETA=04-Proyecto-Base' in args and any(a.startswith('REPO_URL=https://') for a in args)
    orden = _orden_del_clon(texto)
    fetch = next(o for o in orden if ' fetch ' in o)
    assert '--depth 1' in fetch and '"$REF"' in fetch and '/tmp/repo' in fetch
    assert orden[-1] == 'rm -rf /tmp/repo', 'el clon se borra al final del MISMO RUN: no queda en ninguna capa'


def test_la_imagen_final_no_instala_git():
    for inst, resto in _final(_texto()):
        if inst == 'RUN':
            assert not re.search(r'\bgit\b|apt-get|apk ', resto), resto


def test_el_token_va_como_secreto_y_nunca_como_arg_ni_env():
    texto = _texto()
    run = next(r for i, r in _etapa(texto, 'fuente-git') if i == 'RUN' and 'git_token' in r)
    assert run.startswith('--mount=type=secret,id=git_token')
    assert '/run/secrets/git_token' in run
    for inst, resto in _instrucciones(texto):
        if inst in ('ARG', 'ENV', 'LABEL'):
            assert 'token' not in resto.lower(), f'{inst} {resto}: el token quedaría en la imagen o en docker history'
    # el secreto solo se monta en la etapa del clon, que se tira
    for inst, resto in _final(texto):
        assert 'secret' not in resto, resto


def test_el_modelo_entra_por_el_contexto_modelo():
    copias = _copias(_final(_texto()))
    del_modelo = {(tuple(o), d) for desde, o, d in copias if desde == 'modelo'}
    assert del_modelo == {(('modelo_mlflow/',), 'models/modelo_mlflow/'), (('metadatos.json',), 'models/metadatos.json')}
    # y ningún COPY de ninguna etapa toma models/ de la carpeta
    for _, _, ins in _etapas(_texto()):
        for desde, origenes, _ in _copias(ins):
            assert not any(o.startswith('models') for o in origenes), origenes


def test_requiere_buildkit():
    assert _texto().splitlines()[0] == '# syntax=docker/dockerfile:1'     # RUN --mount y --build-context son de BuildKit


# --- .dockerignore: lo que se copia (con FUENTE=contexto) no puede estar excluido ----------------------------------------------------

def _archivos_de_la_imagen(carpeta_modelos):
    """(ruta en /app, archivo, ruta en el contexto del proyecto o None) de lo que lleva la imagen, tras entrenar.

    El código se resuelve a través de /src hasta la carpeta del proyecto (FUENTE=contexto: lo mismo que deja el clon, ver la prueba
    de paridad); el modelo recién entrenado está en una carpeta temporal (carpeta_modelos), que hace de contexto «modelo».
    """
    texto = _texto()
    src = _src_del_contexto(texto)
    rutas = []
    for desde, origenes, destino in _copias(_final(texto)):
        for origen in origenes:
            if desde == 'modelo':
                p, en_contexto = carpeta_modelos / origen.rstrip('/'), None
            else:
                en_contexto = src[origen.rstrip('/')]
                p = RAIZ / en_contexto
            dentro = _destino(origen, destino, p.is_dir())
            if p.is_dir():
                for f in sorted(p.rglob('*')):
                    if f.is_file():
                        rel = f.relative_to(p).as_posix()
                        rutas.append((f'{dentro}/{rel}', f, f'{en_contexto}/{rel}' if en_contexto else None))
            else:
                rutas.append((dentro, p, en_contexto))
    return rutas


@pytest.fixture(scope='module')
def modelo_entrenado(ruta_db, tmp_path_factory):
    destino = tmp_path_factory.mktemp('imagen')
    mp = pytest.MonkeyPatch()
    mp.setattr(config, 'MODELOS', destino / 'models')
    mp.setattr(config, 'REPORTES', destino / 'reports')
    from ia_mlops import db
    con = db.conectar(ruta_db)
    train.entrenar(con, usar_mlflow=False, verbose=False)
    con.close()
    yield destino / 'models'
    mp.undo()


def test_lo_que_el_dockerfile_copia_no_queda_excluido_por_dockerignore(modelo_entrenado):
    rutas = _archivos_de_la_imagen(modelo_entrenado)
    assert any(r.endswith('MLmodel') for r, _, _ in rutas) and any(r == 'models/metadatos.json' for r, _, _ in rutas)
    assert any(r.startswith('ia_mlops/api/') for r, _, _ in rutas)
    # el modelo de la imagen es el entrenado (el del contexto «modelo»), no uno de la carpeta del proyecto
    assert all(a.is_relative_to(modelo_entrenado) for r, a, _ in rutas if r.startswith('models/'))
    for ruta, archivo, en_contexto in rutas:
        if '__pycache__' in ruta or ruta.endswith('.pyc'):
            continue
        assert archivo.exists(), ruta
        if en_contexto:
            assert not _ignorado(en_contexto, _patrones()), f'{en_contexto} lo copia el Dockerfile (FUENTE=contexto) pero .dockerignore lo excluye'


def test_dockerignore_deja_fuera_datos_pruebas_y_artefactos_pesados():
    patrones = _patrones()
    for ruta in ['data/raw/muestra_online_retail_ii.csv', 'data/processed/curso.db', 'tests/test_api.py', 'notebooks/01_pipeline_raw_a_master.ipynb',
                 'models/mlflow.db', 'models/mlartifacts/0/x/model.pkl', 'models/modelo.joblib', '.git/config', '.env', 'ia_mlops/__pycache__/x.pyc']:
        assert _ignorado(ruta, patrones), ruta
    for ruta in ['models/modelo_mlflow/MLmodel', 'models/metadatos.json', 'ia_mlops/api/app.py', 'requirements-api.lock']:
        assert not _ignorado(ruta, patrones), ruta


def test_la_imagen_simulada_arranca_solo_con_lo_que_el_dockerfile_copia(modelo_entrenado, arrancar_servidor, tmp_path):
    """Replica la disposicion de la imagen (/app/ia_mlops, /app/models/...) en una carpeta nueva, sin datos, SQL ni pruebas, y arranca uvicorn alli.

    Detecta dependencias ocultas del servicio (rutas relativas al proyecto, archivos de datos). NO prueba la imagen base ni `pip install`.
    """
    app = tmp_path / 'app'
    for ruta, archivo, en_contexto in _archivos_de_la_imagen(modelo_entrenado):
        if '__pycache__' in ruta or (en_contexto and _ignorado(en_contexto, _patrones())):
            continue
        destino = app / ruta
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(archivo, destino)
    assert sorted(p.name for p in app.iterdir()) == ['ia_mlops', 'models', 'requirements-api.lock']
    puerto, salida = arrancar_servidor(app / 'models', cwd=app)
    base = f'http://127.0.0.1:{puerto}'
    assert json.loads(urllib.request.urlopen(base + '/listo', timeout=5).read()) == {'estado': 'listo'}
    ejemplo = (RAIZ / 'tests' / 'datos' / 'cliente_ejemplo.json').read_bytes()
    pet = urllib.request.Request(base + '/predecir', data=ejemplo, headers={'content-type': 'application/json'})
    assert 0 <= json.loads(urllib.request.urlopen(pet, timeout=5).read())['probabilidad'] <= 1
    # Y que el codigo servido es el de la copia, no el del proyecto (el paquete esta instalado en modo editable en este entorno):
    # uvicorn arranca con la carpeta actual al principio de sys.path, igual que este comando.
    import subprocess
    import sys
    r = subprocess.run([sys.executable, '-c', 'import ia_mlops; print(ia_mlops.__file__)'], cwd=app, capture_output=True, text=True)
    assert Path(r.stdout.strip()).is_relative_to(app)


# --- dependencias de la imagen ----------------------------------------------------------------------------------------------------

def _versiones(ruta):
    out = {}
    for linea in ruta.read_text(encoding='utf-8').splitlines():
        linea = linea.strip()
        if linea and not linea.startswith('#') and '==' in linea:
            nombre, version = linea.split('==')
            out[nombre.strip().lower().replace('_', '-')] = version.strip()
    return out


def test_el_archivo_de_versiones_exactas_contiene_las_dependencias_directas():
    directas, exactas = _versiones(RAIZ / 'requirements-api.txt'), _versiones(RAIZ / 'requirements-api.lock')
    assert directas
    for nombre, version in directas.items():
        assert exactas.get(nombre) == version, nombre


def test_la_imagen_no_lleva_herramientas_de_desarrollo_ni_mlflow_completo():
    exactas = _versiones(RAIZ / 'requirements-api.lock')
    for ausente in ('pytest', 'jupyterlab', 'papermill', 'jupytext', 'matplotlib', 'mlflow', 'openpyxl', 'httpx', 'sqlalchemy'):
        assert ausente not in exactas, ausente
    assert 'mlflow-skinny' in exactas and 'fastapi' in exactas and 'uvicorn' in exactas


def test_las_versiones_directas_coinciden_con_el_entorno_del_curso():
    """Quien entrena (env-ia-mlops) y quien sirve (la imagen) deben usar las mismas versiones de lo que afecta al modelo."""
    import yaml
    ruta_entorno = RAIZ.parent / '03-Entorno' / 'conda' / 'environment.yml'
    if not ruta_entorno.exists():
        pytest.skip('environment.yml solo existe en el repositorio del curso; en tu repositorio (la raiz es el proyecto) no hay con que comparar')
    entorno = yaml.safe_load(ruta_entorno.read_text(encoding='utf-8'))
    del_entorno = {}
    for d in entorno['dependencies']:
        if isinstance(d, str) and '=' in d:
            n, v = d.split('=', 1)
            del_entorno[n.lower()] = v
    for nombre, version in _versiones(RAIZ / 'requirements-api.txt').items():
        if nombre in del_entorno:
            assert del_entorno[nombre] == version, nombre
    for nombre in ('numpy', 'pandas', 'scikit-learn', 'joblib', 'fastapi', 'uvicorn', 'pydantic'):
        assert nombre in del_entorno, nombre
