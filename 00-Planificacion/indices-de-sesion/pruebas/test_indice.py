"""Pruebas de los índices de sesión (`01-Sesiones/Sx-.../index.html`).

Qué vigilan:
  - que cada índice está al día respecto de contenido_indices.py y de lo que hay en la carpeta (si añades un archivo y no ejecutas el generador, falla);
  - que todos los enlaces apuntan a archivos que existen;
  - que todo .html y .md de una sesión está enlazado;
  - que el estado «solo README» es verdad;
  - que las presentaciones con «volver» tienen su enlace de regreso al índice de su sesión;
  - que no hay recursos externos ni la palabra que no debe aparecer en títulos o nombres.
"""
import re
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlparse

import pytest

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(AQUI.parent))
import contenido_indices as C  # noqa: E402
import generar_indices as G  # noqa: E402
import contenido_pdfs as P  # noqa: E402  (la lista de PDF vive en 00-Planificacion/pdfs/)

SESIONES = list(enumerate(C.SESIONES))
IDS = [s['id'] for s in C.SESIONES]
PROHIBIDA = 'guia' + 'burros'  # nombre interno que no debe aparecer en títulos, nombres de archivo ni contenido


def pagina(i):
    return (RAIZ / C.SESIONES[i]['carpeta'] / 'index.html').read_text(encoding='utf-8')


def hrefs(texto):
    return re.findall(r'<a\b[^>]*?\bhref="([^"]+)"', texto)


def enlaces_de(texto, clase):
    return re.findall(rf'<a\b[^>]*class="{clase}"[^>]*?\bhref="([^"]+)"', texto)


@pytest.mark.parametrize('i,s', SESIONES, ids=IDS)
def test_el_indice_esta_al_dia(i, s):
    esperado = G.construir(i)
    assert pagina(i) == esperado, f'{s["id"]}: el index.html no coincide con lo generado. Ejecuta: python 00-Planificacion/indices-de-sesion/generar_indices.py'


@pytest.mark.parametrize('i,s', SESIONES, ids=IDS)
def test_todos_los_enlaces_existen(i, s):
    texto = pagina(i)
    carpeta = RAIZ / s['carpeta']
    for h in hrefs(texto):
        if h.startswith(('http://', 'https://', '#')):
            continue
        destino = (carpeta / unquote(urlparse(h).path)).resolve()
        if h.endswith('/'):
            assert destino.is_dir(), f'{s["id"]}: el enlace {h} apunta a una carpeta que no existe'
        else:
            assert destino.is_file(), f'{s["id"]}: el enlace {h} apunta a un archivo que no existe'
    for ruta in re.findall(r'data-path="([^"]+)"', texto):
        assert (RAIZ / ruta).is_file(), f'{s["id"]}: data-path {ruta} no existe (la versión de GitHub fallaría)'


@pytest.mark.parametrize('i,s', SESIONES, ids=IDS)
def test_todo_archivo_html_o_md_de_la_sesion_esta_enlazado(i, s):
    texto = pagina(i)
    carpeta = RAIZ / s['carpeta']
    enlazados = {(carpeta / unquote(urlparse(h).path)).resolve() for h in hrefs(texto) if not h.startswith(('http', '#'))}
    for p in sorted(carpeta.rglob('*')):
        partes = set(p.relative_to(carpeta).parts)
        if p.suffix not in ('.html', '.md') or partes & G.IGNORAR or any(x.startswith('.') for x in partes) or p == carpeta / 'index.html':
            continue
        assert p.resolve() in enlazados, f'{s["id"]}: {p.relative_to(RAIZ)} no está enlazado en el índice'


@pytest.mark.parametrize('i,s', SESIONES, ids=IDS)
def test_estado_solo_readme_es_verdad(i, s):
    carpeta = RAIZ / s['carpeta']
    archivos = {p.relative_to(carpeta).as_posix() for p in carpeta.rglob('*') if p.is_file() and not p.name.startswith('.') and p.name != 'index.html'}
    if s['estado'] == C.SOLO_README:
        assert archivos == {'README.md'}, f'{s["id"]} está marcada «Solo README» pero tiene {sorted(archivos)}: cambia su estado en contenido_indices.py'
    else:
        assert len(archivos) > 1, f'{s["id"]} está marcada «preparada» pero solo tiene README'


@pytest.mark.parametrize('i,s', SESIONES, ids=IDS)
def test_los_componentes_marcados_concuerdan_con_el_disco(i, s):
    texto = pagina(i)
    pares = re.findall(r'<li class="(si|no)"><span aria-hidden="true">.</span> ([^<]+)<span', texto)
    marcados = {etiqueta: clase for clase, etiqueta in pares}
    esperados = {C.COMPONENTES[k][0] for k in s['esperados']}
    assert set(marcados) == esperados
    for etiqueta, hay in G.componentes(s):
        assert (marcados[etiqueta] == 'si') == hay


def test_s0_y_s1_no_tienen_faltas_y_s2_a_s5_si():
    for i, s in SESIONES:
        texto = pagina(i)
        if s['estado'] == C.PREPARADO:
            assert 'No falta ningún componente' in texto, s['id']
        else:
            assert 'presentación' in re.search(r'<p>Falta: ([^<]+)\.</p>', texto).group(1), s['id']


@pytest.mark.parametrize('i,s', SESIONES, ids=IDS)
def test_las_presentaciones_con_volver_enlazan_al_indice_de_su_sesion(i, s):
    indice = (RAIZ / s['carpeta'] / 'index.html').resolve()
    for e in s['enlaces']:
        if e['tipo'] != 'deck' or not e['volver']:
            continue
        deck = RAIZ / e['ruta']
        m = re.search(r'<a id="bhome" href="([^"]+)"', deck.read_text(encoding='utf-8'))
        assert m, f'{e["ruta"]}: falta el enlace «⌂ Índice» (a#bhome) en su barra'
        assert (deck.parent / m.group(1)).resolve() == indice, f'{e["ruta"]}: su enlace de regreso no lleva a {indice.relative_to(RAIZ)}'


def test_los_numeros_de_diapositivas_son_los_reales():
    cuentas = {'S0': {31, 27}, 'S1': {20, 12}, 'S2': {22, 16, 38, 17, 36}}   # S2: presentación (22, con la del laboratorio «exponer el servicio»), recap 01 (16), guía de Codespaces (38), contenedores 1 (16) y 2 (17), del ordenador al servicio (36, con 9 capturas del Codespace)
    for i, s in SESIONES:
        if s['id'] not in cuentas:
            continue
        mostrados = {int(n) for n in re.findall(r'<span class="n">(\d+) diap\.</span>', pagina(i))}
        assert mostrados == cuentas[s['id']], f'{s["id"]}: las diapositivas mostradas {mostrados} no son las reales'
        for e in s['enlaces']:
            if e['tipo'] == 'deck' and G.contar_diapositivas(e['ruta']):
                assert f'{G.contar_diapositivas(e["ruta"])} diap.' in pagina(i)


@pytest.mark.parametrize('i,s', SESIONES, ids=IDS)
def test_las_sesiones_vecinas_enlazan_a_su_indice(i, s):
    texto = pagina(i)
    carpeta = RAIZ / s['carpeta']
    vecinas = re.search(r'<nav class="vecinas".*?</nav>', texto, re.S)
    destinos = [(carpeta / h).resolve() for h in hrefs(vecinas.group(0))] if vecinas else []
    esperados = []
    if i > 0:
        esperados.append((RAIZ / C.SESIONES[i - 1]['carpeta'] / 'index.html').resolve())
    if i < len(C.SESIONES) - 1:
        esperados.append((RAIZ / C.SESIONES[i + 1]['carpeta'] / 'index.html').resolve())
    assert destinos == esperados


@pytest.mark.parametrize('i,s', SESIONES, ids=IDS)
def test_sin_recursos_externos_y_sin_el_nombre_prohibido(i, s):
    texto = pagina(i)
    assert not re.search(r'<(script|link|img|iframe)\b[^>]*\b(src|href)="https?://', texto), 'recurso externo'
    assert PROHIBIDA not in texto.lower()


def test_el_nombre_prohibido_no_aparece_en_las_fuentes_ni_en_nombres_de_archivo():
    for ruta in (AQUI.parent / 'contenido_indices.py', AQUI.parent / 'generar_indices.py', AQUI.parent / 'comprobar_diseno.py'):
        assert PROHIBIDA not in ruta.read_text(encoding='utf-8').lower(), ruta.name
    for p in RAIZ.rglob('*'):
        if '.git' in p.parts:
            continue
        assert PROHIBIDA not in p.name.lower(), p


def test_cada_sesion_de_01_sesiones_tiene_su_indice_en_contenido():
    # «recap» y «ejercicios» no son sesiones: repasos y tareas resueltas (se enlazan desde el índice de su sesión)
    carpetas = {f'01-Sesiones/{p.name}' for p in (RAIZ / '01-Sesiones').iterdir() if p.is_dir() and p.name not in ('recap', 'ejercicios')}
    assert carpetas == {s['carpeta'] for s in C.SESIONES}, 'hay una carpeta de sesión sin índice (o un índice sin carpeta)'


def test_los_archivos_enlazados_en_contenido_existen_y_no_se_repiten():
    for s in C.SESIONES:
        rutas = [e['ruta'] for e in s['enlaces']]
        assert len(rutas) == len(set(rutas)), f'{s["id"]}: ruta repetida'
        for r in rutas:
            assert (RAIZ / r).is_file(), f'{s["id"]}: {r} no existe'
            assert PurePosixPath(r).as_posix() == r


# ---------------------------------------------------------------------------
# Enlaces a los PDF (00-Planificacion/pdfs/contenido_pdfs.py)
# ---------------------------------------------------------------------------
def pdfs_esperados(s):
    """{ruta fuente: ruta del PDF} de los elementos de esta sesión que están en el manifiesto de PDF y cuyo PDF existe."""
    fuentes = {e['ruta'] for e in s['enlaces']}
    salida = {}
    for ps in P.SESIONES:
        for e in ps['elementos']:
            pdf = f"{P.CARPETA_SALIDA}/{ps['carpeta']}/{P.GRUPOS[e['grupo']][1]}/{e['archivo']}"
            if e['origen'] in fuentes and (RAIZ / pdf).is_file():
                salida[e['origen']] = pdf
    return salida


@pytest.mark.parametrize('i,s', SESIONES, ids=IDS)
def test_cada_elemento_con_pdf_lo_enlaza_y_solo_esos(i, s):
    esperados = pdfs_esperados(s)
    carpeta = RAIZ / s['carpeta']
    enlazados = {(carpeta / unquote(h)).resolve().relative_to(RAIZ).as_posix() for h in enlaces_de(pagina(i), 'pdf')}
    assert enlazados == set(esperados.values()), f'{s["id"]}: los PDF enlazados no son los que existen en el manifiesto'


def test_s0_y_s1_enlazan_todos_los_pdf_de_sus_materiales():
    for i, s in SESIONES:
        if s['id'] in ('S0', 'S1'):
            # Todo elemento del manifiesto cuya fuente aparece en el índice debe tener su botón PDF.
            fuentes = {e['ruta'] for e in s['enlaces']}
            pendientes = [e['origen'] for ps in P.SESIONES if ps['id'] == s['id'] for e in ps['elementos'] if e['origen'] not in fuentes]
            assert pendientes == [], f'{s["id"]}: tienen PDF pero no salen en el índice (añádelos a contenido_indices.py): {pendientes}'
            assert len(pdfs_esperados(s)) == sum(1 for ps in P.SESIONES if ps['id'] == s['id'] for _ in ps['elementos'])


@pytest.mark.parametrize('i,s', SESIONES, ids=IDS)
def test_la_linea_de_la_carpeta_de_pdf_solo_sale_donde_hay_pdf(i, s):
    texto = pagina(i)
    hay = (RAIZ / P.CARPETA_SALIDA / next((ps['carpeta'] for ps in P.SESIONES if ps['id'] == s['id']), '-')).is_dir()
    assert ('PDF de esta sesión' in texto) == hay
    if hay:
        assert 'pdfs/LEEME.md' in texto


def test_sin_el_archivo_pdf_no_se_muestra_el_boton(monkeypatch, tmp_path):
    ruta = '01-Sesiones/S1-Datos-y-Entrenamiento/tarea/rubrica.md'
    assert G.ruta_pdf_de(ruta) is not None
    monkeypatch.setattr(G, 'RAIZ', tmp_path)  # una raíz sin PDF
    assert G.ruta_pdf_de(ruta) is None
    assert G.enlace_pdf({'ruta': ruta}, '01-Sesiones/S1-Datos-y-Entrenamiento') == ''


def test_una_fuente_que_no_esta_en_el_manifiesto_no_tiene_pdf():
    assert G.ruta_pdf_de('03-Entorno/conda/verificar_s1.py') is None
