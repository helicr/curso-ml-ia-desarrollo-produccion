"""Pruebas del material de contenedores (guía práctica, laboratorio de roturas y dos presentaciones).

Ejecutar:  python -m pytest 01-Sesiones/S2-API-y-Docker/contenedores/pruebas -q
No necesitan Internet ni Docker: comprueban que lo escrito sale de ejemplos.py y de las salidas reales guardadas, que las salidas reales cumplen
lo que cada paso espera, que los archivos generados están al día y que lo que no se ha probado se dice.
"""
import html as hlib
import re
import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AQUI))
import datos  # noqa: E402
import deck_b  # noqa: E402
import generar as G  # noqa: E402
import textos  # noqa: E402
from datos import E  # noqa: E402

RAIZ = AQUI.parents[2]
S2 = AQUI.parent
PALABRA_PROHIBIDA = re.compile(r'gu[ií]a[\s_-]*burros?', re.I)
GUIA = AQUI / 'guia-practica.md'
LAB = AQUI / 'laboratorio-romper.md'
DECKS = {'modelo-mental': AQUI / 'modelo-mental' / 'index.html', 'del-dockerfile-a-produccion': AQUI / 'del-dockerfile-a-produccion' / 'index.html'}
PREPARACION = {datos.CARPETA_LIBRE} | {datos.preparar_carpeta(x) for x in E.TODOS}
COMANDOS = {p['cmd'] for x in E.TODOS for p in datos.pasos_de(x)}


def leer(p):
    return p.read_text(encoding='utf-8')


def rc_ok(esperado, rc):
    if esperado == 'distinto':
        return rc != 0
    if isinstance(esperado, (list, tuple)):
        return rc in esperado
    return rc == esperado


# ------------------------------------------------------------------------------------------------ fuente y salidas reales
def test_hay_9_ejemplos_y_5_roturas_con_sus_pasos_ejecutados():
    assert [x['id'] for x in E.EJEMPLOS] == [f'e{i}' for i in range(1, 10)]
    assert [x['id'] for x in E.ROTURAS] == [f'r{i}' for i in range(1, 6)]
    for x in E.TODOS:
        assert len(datos.SALIDAS['ejemplos'][x['id']]) == len(datos.pasos_de(x))


def test_cada_paso_ejecutado_cumple_lo_que_ejemplos_py_esperaba():
    for x in E.TODOS:
        for k, p in enumerate(datos.pasos_de(x)):
            reg = datos.registro(x['id'], k)
            donde = f'{x["id"]} paso {k + 1}: {p["cmd"]}'
            assert rc_ok(p['rc'], reg['rc']), f'{donde}: código {reg["rc"]}, se esperaba {p["rc"]}'
            if p['espera']:
                assert re.search(p['espera'], reg['salida'], re.M), f'{donde}: la salida no contiene /{p["espera"]}/'
            if p['no_espera']:
                assert not re.search(p['no_espera'], reg['salida'], re.M), f'{donde}: la salida contiene /{p["no_espera"]}/'


def test_las_salidas_no_llevan_datos_que_cambian_en_cada_ejecucion():
    for x in E.TODOS:
        for k, p in enumerate(datos.pasos_de(x)):
            s = datos.mostrado(p, datos.registro(x['id'], k))
            assert not re.search(r'[0-9a-f]{64}', s), f'{x["id"]} paso {k + 1}: identificador largo sin acortar'
            assert not re.search(r'"ts": [0-9]', s), f'{x["id"]} paso {k + 1}: marca de tiempo sin sustituir'
            assert '\x1b[' not in s, f'{x["id"]} paso {k + 1}: códigos de color'


def test_la_caché_se_ve_en_las_salidas_reales():
    malo = datos.salida('e5', 2)
    bueno = datos.salida('e5', 5)
    assert re.search(r'RUN pip install[^\n]*$', malo) and not re.search(r'RUN pip install[^\n]*\n#\d+ CACHED', malo)
    assert re.search(r'RUN pip install[^\n]*\n#\d+ CACHED', bueno)
    assert datos.segundos('e5', 5) < datos.segundos('e5', 2)


def test_las_cifras_de_contexto_y_tamano_son_las_medidas():
    g = deck_b.dockerfile_a_produccion().html()
    ctx_malo = deck_b._ultimo(r'transferring context: ([0-9.]+[kMG]?B)', datos.salida('e8', 1))
    ctx_bueno = deck_b._ultimo(r'transferring context: ([0-9.]+[kMG]?B)', datos.salida('e8', 4))
    assert ctx_malo in g and ctx_bueno in g
    assert deck_b._tam_disco('e8', 2) in g and deck_b._tam_disco('e8', 5) in g


def test_ningun_comando_es_peligroso():
    malos = re.compile(r'\bsudo\b|--privileged|system prune|rm -rf /(\s|$)|rm -rf ~|chmod -R 777|curl [^|]*\|\s*(ba)?sh|docker rmi -f|docker volume prune|--net(work)?=?\s*host')
    for c in COMANDOS:
        assert not malos.search(c), c
    # los `rm -rf` solo borran carpetas de la práctica
    for c in COMANDOS:
        for m in re.finditer(r'rm -rf (\S+)', c):
            assert m.group(1) in ('modelo-demo', 'models'), c


# ------------------------------------------------------------------------------------------------ carpetas de ejemplo
def test_las_carpetas_de_ejemplo_existen_y_sus_dockerfiles_parten_de_la_imagen_base():
    for x in E.TODOS:
        if not x['carpeta']:
            continue
        base = AQUI / 'ejemplos' / x['carpeta']
        assert base.is_dir(), x['carpeta']
        for p in datos.pasos_de(x):
            for f in (re.findall(r'(?<![\w-])-f (\S+)', p['cmd']) if p['cmd'].startswith('docker build') else []):
                assert (base / f).exists() or f.startswith('Dockerfile.arreglado'), f'{x["id"]}: {f} no existe en {x["carpeta"]}'
        for df in base.glob('Dockerfile*'):
            assert re.search(rf'^FROM {re.escape(E.IMAGEN_BASE)}$', leer(df), re.M), df


def test_la_imagen_de_la_api_minima_hace_lo_que_dice_la_guia():
    t = leer(AQUI / 'ejemplos' / '09-api-minima' / 'Dockerfile')
    assert 'USER 10001' in t and 'HEALTHCHECK' in t and 'EXPOSE 8080' in t
    api = leer(AQUI / 'ejemplos' / '09-api-minima' / 'api.py')
    assert '0.0.0.0' in api and '/salud' in api


def test_el_unico_secreto_de_los_ejemplos_es_falso_y_esta_declarado():
    mal = leer(AQUI / 'ejemplos' / '06-entorno' / 'Dockerfile.mal')
    assert 'no-es-un-secreto-real-123' in mal
    assert 'mi.env' in leer(AQUI / 'ejemplos' / '06-entorno' / '.gitignore')


# ------------------------------------------------------------------------------------------------ generados al día
def test_los_archivos_generados_estan_al_dia():
    for ruta, texto in G.contenidos().items():
        assert ruta.exists(), f'falta {ruta}: ejecuta python generar.py'
        assert leer(ruta) == texto, f'{ruta.relative_to(AQUI)} está desfasado: ejecuta python generar.py'


# ------------------------------------------------------------------------------------------------ guía y laboratorio (texto)
def bloques(md, leng):
    return re.findall(rf'```{leng}\n(.*?)\n```', md, re.S)


@pytest.mark.parametrize('ruta', [GUIA, LAB])
def test_los_comandos_del_texto_son_los_de_ejemplos_py(ruta):
    md = leer(ruta)
    for b in bloques(md, 'bash'):
        for linea in b.split('\n'):
            assert linea in COMANDOS or linea in PREPARACION or linea == 'docker version', f'{ruta.name}: «{linea}» no viene de ejemplos.py'


@pytest.mark.parametrize('ruta,lista', [(GUIA, E.EJEMPLOS), (LAB, E.ROTURAS)])
def test_cada_comando_y_cada_salida_mostrada_estan_en_el_texto(ruta, lista):
    md = leer(ruta)
    for x in lista:
        for k, p in enumerate(datos.pasos_de(x)):
            assert p['cmd'] in md, f'{ruta.name}: falta el comando de {x["id"]} paso {k + 1}'
            s = datos.mostrado(p, datos.registro(x['id'], k))
            if s:
                assert s in md, f'{ruta.name}: la salida de {x["id"]} paso {k + 1} no coincide con la real'


def test_el_laboratorio_esconde_el_arreglo_en_un_desplegable():
    md = leer(LAB)
    assert md.count('<details>') == md.count('</details>') == len(E.ROTURAS)
    for x in E.ROTURAS:
        antes = md.split(f'## Rotura {x["num"]} ')[1].split('<details>')[0]
        for p in x['arreglo']:
            assert p['cmd'] not in antes or p['cmd'] in {q['cmd'] for q in x['pasos']}, f'el arreglo de {x["id"]} está a la vista antes del desplegable'
        assert x['leccion'] in md


def test_los_minutos_declarados_son_la_suma_de_los_ejemplos():
    md = leer(GUIA)
    assert f'≈{textos.MIN_TOTAL} min' in md and f'≈{textos.MIN_BASICO} min' in md
    assert textos.MIN_TOTAL == sum(x['minutos'] for x in E.EJEMPLOS) and textos.MIN_LAB == sum(x['minutos'] for x in E.ROTURAS)
    assert f'≈{textos.MIN_LAB} min' in leer(LAB)


# ------------------------------------------------------------------------------------------------ presentaciones
@pytest.fixture(scope='module', params=list(DECKS))
def deck(request):
    return request.param, leer(DECKS[request.param])


def test_numero_de_diapositivas_y_ids(deck):
    nombre, h = deck
    n = len(re.findall(r'<section class="slide"', h))
    assert n == {'modelo-mental': 16, 'del-dockerfile-a-produccion': 17}[nombre]
    ids = re.findall(r'<section class="slide"[^>]*data-id="([^"]+)"', h)
    assert len(ids) == len(set(ids)) and ids, ids
    assert ids == (['pa', 'pb', 'pc', 'pd'] if nombre == 'modelo-mental' else ['pa', 'pb', 'pc', 'pd', 'pe'])


def test_todo_lo_copiable_viene_de_ejemplos_py(deck):
    nombre, h = deck
    copiables = [hlib.unescape(c) for c in re.findall(r'class="cp" data-t="([^"]+)"', h)]
    assert len(copiables) >= 20
    for c in copiables:
        assert c in COMANDOS or c in PREPARACION, f'{nombre}: «{c}» no viene de ejemplos.py'
    assert 'btn primary cpall' not in h, 'sin «Copiar todo»: varios pasos necesitan esperar y leer la salida antes del siguiente'


def test_la_vuelta_al_indice_y_los_enlaces_relativos_resuelven(deck):
    nombre, h = deck
    assert '<a id="bhome" href="../../index.html"' in h
    assert (S2 / 'index.html').exists()
    base = DECKS[nombre].parent
    for href in re.findall(r'href="([^"#:]+)"', h):
        assert (base / href).resolve().exists(), f'{nombre}: el enlace {href} no existe'


def test_las_presentaciones_dicen_lo_que_no_se_ha_probado(deck):
    nombre, h = deck
    assert 'Todavía no se han ejecutado en un Codespace del curso' in h
    if 'docs.cloud.google.com' in h:
        assert 'sin probar aquí' in h.lower() or 'Sin probar aquí' in h


def test_la_nube_solo_afirma_lo_que_dice_la_documentacion_consultada():
    h = leer(DECKS['del-dockerfile-a-produccion'])
    assert 'https://docs.cloud.google.com/run/docs/container-contract' in h
    assert 'No se ha desplegado nada en Cloud Run' in h
    for texto in ('0.0.0.0', '8080', 'PORT', 'persiste'):
        assert texto in h


def test_las_citas_del_dockerfile_y_dockerignore_del_curso_son_reales():
    df = leer(RAIZ / '04-Proyecto-Base' / 'deploy' / 'docker' / 'Dockerfile')
    di = leer(RAIZ / '04-Proyecto-Base' / '.dockerignore')
    for f in deck_b.FRAGMENTOS_DOCKERFILE_CURSO:
        assert f in df, f'«{f}» ya no está en el Dockerfile del proyecto'
    for f in deck_b.FRAGMENTOS_DOCKERIGNORE_CURSO:
        assert f in di, f'«{f}» ya no está en el .dockerignore del proyecto'
    assert deck_b.DOCKERFILE_CURSO == '04-Proyecto-Base/deploy/docker/Dockerfile' and (RAIZ / deck_b.DOCKERFILE_CURSO).exists()


def test_la_pregunta_de_s2_sobre_0_0_0_0_tiene_respuesta_en_el_dockerfile_del_curso():
    df = leer(RAIZ / '04-Proyecto-Base' / 'deploy' / 'docker' / 'Dockerfile')
    assert '"--host", "0.0.0.0"' in df


def test_nada_de_lo_generado_ni_de_los_ejemplos_lleva_la_palabra_prohibida():
    archivos = [GUIA, LAB, *DECKS.values(), AQUI / 'ejemplos.py', AQUI / 'textos.py', AQUI / 'deck_a.py', AQUI / 'deck_b.py', AQUI / 'diapos.py']
    archivos += [p for p in (AQUI / 'ejemplos').rglob('*') if p.is_file()]
    for p in archivos:
        assert not PALABRA_PROHIBIDA.search(leer(p)), p
