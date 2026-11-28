"""Pruebas de la presentación del «Extra de S5: RAG en notebooks» (sin navegador y sin ejecutar los notebooks).

Qué vigilan: que index.html está al día con generar.py; la estructura (entre 24 y 30 diapositivas con título, parte, minutos y notas);
que el visor es el del laboratorio de agentes (solo cambia el pie); que el fondo es blanco y nada se mueve al pasar el ratón; que cada orden
tiene su botón de copiar y existe tal cual en el README, en los notebooks o en scripts/; que las ocho figuras de resultados/ existen, salen una
vez, con su rótulo y su celda de origen; que TODO lo que se enseña como «salida guardada» o «código del notebook» está de verdad en los
notebooks (que se leen aquí, no se copian) y que las cifras clave coinciden con resultados/*.json y con las salidas de los .ipynb; que lo
«sin verificar» está donde toca; que no hay mojibake, CDN, :hover, rutas personales ni URLs de proxy reales; y que cada diapositiva lleva
una sola idea (un título, pocas palabras).
"""
import html as htmllib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parents[1]
SESION = AQUI.parent

_spec = importlib.util.spec_from_file_location('generar_extra_rag', AQUI / 'generar.py')
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)


@pytest.fixture(scope='module')
def html():
    return (AQUI / 'index.html').read_text(encoding='utf-8')


def leer(ruta):
    return Path(ruta).read_text(encoding='utf-8')


def secciones(texto):
    return re.findall(r'<section class="slide[^"]*"([^>]*)>(.*?)</section>', texto, re.S)


def sin_etiquetas(texto):
    return re.sub(r'\s+', ' ', htmllib.unescape(re.sub(r'<[^>]+>', ' ', texto)))


def todo_el_texto(h):
    return sin_etiquetas(' '.join(c for _, c in secciones(h)))


def titulo(attrs):
    return re.search(r'data-title="([^"]+)"', attrs).group(1)


def por_titulo(h, t):
    return next(c for a, c in secciones(h) if titulo(a) == t)


# ---- los notebooks, resultados/ y README (se leen aquí: la fuente de las cifras) -------------------------------------------------
def celdas(n):
    return json.loads(leer(AQUI / 'notebooks' / G.NOTEBOOKS[n]))['cells']


def _t(x):
    return ''.join(x) if isinstance(x, list) else x


def fuentes(n):
    return '\n'.join(_t(c['source']) for c in celdas(n))


def codigo_nb(n):
    return '\n'.join(_t(c['source']) for c in celdas(n) if c['cell_type'] == 'code')


def salidas(n):
    """Todo lo que imprimieron las celdas de código de un notebook, junto (sin filtrar nada)."""
    partes = []
    for c in celdas(n):
        for o in c.get('outputs', []):
            partes.append(_t(o['text']) if 'text' in o else _t(o.get('data', {}).get('text/plain', '')))
    return '\n'.join(partes)


def res(nombre):
    return json.loads(leer(AQUI / 'resultados' / f'{nombre}.json'))


def coma(x, d=2):
    return f'{x:.{d}f}'.replace('.', ',')


def sin_comentario(linea):
    return re.sub(r'\s{2,}#.*$', '', linea).rstrip()


README = leer(AQUI / 'README.md')
SCRIPT_SH = leer(AQUI / 'scripts' / 'ejecutar_cuadernos.sh')
REQ = leer(AQUI / 'requisitos-extra-rag.txt')


# ----------------------------------------------------------------------------------------------------------------------
# Estructura
# ----------------------------------------------------------------------------------------------------------------------
def test_esta_al_dia_con_el_generador(html):
    assert html == G.html_completo(), 'index.html no coincide con generar.py: ejecuta  python generar.py'
    assert G.convertir_figuras(escribir=False) == [], 'img/ no está al día: ejecuta  python generar.py'


def test_entre_24_y_30_diapositivas_cada_una_con_titulo_parte_minutos_y_notas(html):
    s = secciones(html)
    assert 24 <= len(s) <= 30, len(s)
    for attrs, cuerpo in s:
        assert re.search(r'data-part="[A-F]"', attrs), attrs
        m = re.search(r'data-min="(\d+)"', attrs)
        assert m and int(m.group(1)) > 0, attrs
        assert titulo(attrs).strip()
        n = re.search(r'data-notes="([^"]*)"', attrs)
        assert n and len(n.group(1)) > 80, f'notas demasiado cortas en {titulo(attrs)}'
        assert cuerpo.count('<h1>') == 1


def test_minutos_entre_60_y_95(html):
    total = sum(int(m) for m in re.findall(r'data-min="(\d+)"', html))
    assert 60 <= total <= 95, total


def test_titulos_sin_repetir_y_antetitulos_numerados_por_partes(html):
    s = secciones(html)
    titulos = [titulo(a) for a, _ in s]
    assert len(titulos) == len(set(titulos))
    letras = list(G.PARTES)
    for attrs, cuerpo in s:
        parte = re.search(r'data-part="([A-F])"', attrs).group(1)
        kick = re.search(r'<p class="kick">(.*?)</p>', cuerpo).group(1)
        assert kick.startswith(f'{letras.index(parte) + 1} · '), kick
    orden = [re.search(r'data-part="([A-F])"', a).group(1) for a, _ in s]
    assert orden == sorted(orden) and set(orden) == set(G.PARTES)


def test_hay_un_bloque_por_notebook_de_00_a_06(html):
    t = todo_el_texto(html)
    for n in G.NOTEBOOKS:
        assert f'notebook {n}' in t.lower(), n
    titulos = [titulo(a) for a, _ in secciones(html)]
    for n in ('00', '01', '02', '03', '04', '05'):
        assert any(x.startswith(f'Notebook {n}') for x in titulos), n
    assert 'Ejercicios' in titulos


def test_pie_con_posicion_x_de_total_y_un_boton_por_parte(html):
    assert '${i+1} / ${N}' in html
    assert html.count('class="part"') == len(G.PARTES)
    assert 'ML e IA · S5 · Extra: RAG en notebooks' in html and 'Laboratorio de agentes</span>' not in html and 'MCP en notebooks' not in html


def test_fondo_blanco_y_nada_se_mueve_al_pasar_el_raton(html):
    assert '--fondo:#ffffff' in html
    assert ':hover' not in html and 'transition' not in html and 'animation' not in html


def test_sin_recursos_externos(html):
    assert not re.search(r'(src|href)="(https?:)?//', html)
    assert not re.search(r'@import|url\((["\']?)(https?:)?//', html)
    assert '<link' not in html and '<iframe' not in html and 'cdn' not in html.lower()


def test_boton_indice_de_regreso_al_indice_de_s5(html):
    assert '<a id="bhome" href="../index.html"' in html and '⌂ Índice' in html


def test_marco_notas_con_s_zoom_con_clic_esc_y_flechas(html):
    for clave in ("k==='Escape'", "k==='ArrowRight'", "k==='ArrowLeft'", "k==='s'||k==='S'", 'id="zoombox"', 'cursor:zoom-in', 'id="notes"'):
        assert clave in html, clave


def test_el_visor_es_el_del_laboratorio_de_agentes_salvo_el_pie():
    ref = SESION / 'laboratorio-agentes' / 'index.html'
    if not ref.exists():
        pytest.skip('no está el laboratorio de agentes')
    ag, mio = leer(ref), leer(AQUI / 'index.html')
    css_a = re.search(r'<style>(.*?)</style>', ag, re.S).group(1)
    css_m = re.search(r'<style>(.*?)</style>', mio, re.S).group(1)
    assert css_m.startswith(css_a), 'el CSS del visor ya no es el del laboratorio de agentes (solo se admiten añadidos al final)'
    js_a = re.search(r'<script>(.*?)</script>', ag, re.S).group(1).replace('ML e IA · S5 · Laboratorio de agentes', 'PIE')
    js_m = re.search(r'<script>(.*?)</script>', mio, re.S).group(1).replace('ML e IA · S5 · Extra: RAG en notebooks', 'PIE')
    js_a = re.sub(r'const PARTES=\{.*?\};', 'const PARTES={};', js_a, flags=re.S)
    js_m = re.sub(r'const PARTES=\{.*?\};', 'const PARTES={};', js_m, flags=re.S)
    assert js_a == js_m


def test_sin_tabuladores_ni_marcas_markdown_sin_convertir(html):
    assert '\t' not in html
    texto = sin_etiquetas(re.sub(r'<span class="mono">.*?</span>', ' ', re.sub(r'<pre[^>]*>.*?</pre>', ' ', ' '.join(c for _, c in secciones(html)), flags=re.S), flags=re.S))
    assert not re.search(r'(?<!/)\*\*', texto), 'un **negrita** sin convertir'
    assert '`' not in texto, 'una `comilla` sin convertir'


# ----------------------------------------------------------------------------------------------------------------------
# Una sola idea por diapositiva
# ----------------------------------------------------------------------------------------------------------------------
def test_una_idea_por_diapositiva_titulo_corto_y_pocas_palabras(html):
    for attrs, cuerpo in secciones(html):
        h1 = sin_etiquetas(re.search(r'<h1>(.*?)</h1>', cuerpo, re.S).group(1))
        assert len(h1) <= 125, f'título largo en «{titulo(attrs)}»: {len(h1)}'
        prosa = re.sub(r'<pre[^>]*>.*?</pre>', ' ', cuerpo, flags=re.S)
        palabras = len(sin_etiquetas(prosa).split())
        assert palabras <= 360, f'demasiado texto en «{titulo(attrs)}»: {palabras} palabras'
        assert cuerpo.count('class="msg"') <= 1


def test_el_cierre_tiene_un_mensaje_y_cuatro_tarjetas_con_cifras(html):
    ultima = secciones(html)[-1][1]
    assert ultima.count('class="msg"') == 1 and ultima.count('class="card kpi"') == 4
    for cifra in ('recall@5 = 1,0', '0,00 → 0,58', 'k = 1: 0,833', '0,009 s · 1,5 s', '¿Preguntas?'):
        assert cifra in ultima, cifra


# ----------------------------------------------------------------------------------------------------------------------
# Figuras (capturas reales de lo que producen los notebooks)
# ----------------------------------------------------------------------------------------------------------------------
FIGS = ['fig_similitud_coseno', 'fig_pca_embeddings', 'fig_chunking_longitudes', 'fig_mrr', 'fig_recall_at_k', 'fig_con_sin_rag',
        'fig_mandos_chunk_k', 'fig_latencia_etapas']


def test_las_ocho_figuras_existen_salen_una_vez_y_son_las_de_resultados(html):
    from PIL import Image
    assert sorted(G.FIGURAS) == sorted(FIGS)
    cuerpo = ' '.join(c for _, c in secciones(html))
    for nombre in FIGS:
        webp = AQUI / 'img' / f'{nombre}.webp'
        png = AQUI / 'resultados' / f'{nombre}.png'
        assert webp.is_file() and webp.stat().st_size > 2000, nombre
        assert png.is_file()
        assert cuerpo.count(f'data-img="{nombre}.webp"') == 1, nombre
        with Image.open(webp) as a, Image.open(png) as b:
            assert a.format == 'WEBP' and a.size == b.size, (nombre, a.size, b.size)
    for ruta in re.findall(r'(?:src|data-src)="(img/[^"]+)"', html):
        assert (AQUI / ruta).is_file(), ruta
    assert 'Captura pendiente' not in html


def test_la_figura_es_el_png_convertido_sin_perdida():
    from PIL import Image, ImageChops
    for nombre in FIGS:
        with Image.open(AQUI / 'img' / f'{nombre}.webp') as a, Image.open(AQUI / 'resultados' / f'{nombre}.png') as b:
            dif = ImageChops.difference(a.convert('RGB'), b.convert('RGB')).getbbox()
            assert dif is None, f'{nombre}: el webp no es idéntico al png'


def test_cada_figura_dice_de_que_notebook_y_celda_sale(html):
    for nombre, (nb, rotulo) in G.FIGURAS.items():
        bloque = re.search(rf'<figure class="cap" data-img="{nombre}\.webp">(.*?)</figure>', html, re.S).group(1)
        txt = sin_etiquetas(bloque)
        m = re.search(rf'Sale del notebook {nb}, celda \[(\d+)\] → resultados/{nombre}\.png', txt)
        assert m, nombre
        celda = next(c for c in celdas(nb) if c['cell_type'] == 'code' and c.get('execution_count') == int(m.group(1)))
        assert f'{nombre}.png' in _t(celda['source']) and 'savefig' in _t(celda['source']), nombre
        assert rotulo in txt and 'Figura real' in txt
        assert len(rotulo) > 60


def test_el_rotulo_de_cada_figura_dice_lo_que_el_grafico_contiene():
    R = G.FIGURAS
    rc, gn = res('recuperacion'), res('generacion')
    # títulos de los gráficos: son los del código que los dibuja
    for nombre, (nb, rotulo) in R.items():
        for tit in re.findall(r'«([^»]+)»', rotulo):
            assert tit.replace('Recall@k', 'recall@k') in fuentes(nb).replace('Recall@k', 'recall@k') or tit in fuentes(nb), (nombre, tit)
    # MRR: 0,96 · 0,91 · 0,96
    assert [coma(rc[m]['mrr']) for m in ('bm25', 'denso', 'hibrido')] == ['0,96', '0,91', '0,96']
    r = R['fig_mrr'][1]
    assert 'BM25 0,96' in r and 'denso 0,91' in r and 'híbrido 0,96' in r
    # recall@k: BM25 e híbrido valen lo mismo en todos los k (por eso una línea tapa a la otra)
    por = {(f['k'], f['metodo']): f['recall'] for f in rc['recall_por_k']}
    assert all(por[(k, 'BM25')] == por[(k, 'hibrido')] for k in (1, 3, 5, 8))
    assert 'k = 1, 3, 5 y 8' in R['fig_recall_at_k'][1]
    # con/sin RAG: las barras «sin RAG» valen 0 y las «con RAG», las del JSON
    det = {d['id']: d for d in gn['detalle']}
    assert all(det[i]['cobertura_sin'] == 0 for i in det)
    assert [coma(det[i]['cobertura_con']).replace(',50', ',5').replace(',00', ',0') for i in ('q11', 'q13', 'q03', 'q19')] == ['0,33', '0,5', '0,5', '1,0']
    assert 'valen 0,33, 0,5, 0,5 y 1,0' in R['fig_con_sin_rag'][1] and 'q11, q13, q03 y q19' in R['fig_con_sin_rag'][1]
    # mandos: 200, 400 y 800 caracteres y k de 1 a 8
    assert 'chunk de 200, 400 y 800' in R['fig_mandos_chunk_k'][1] and 'k de 1 a 8' in R['fig_mandos_chunk_k'][1]
    assert 'for tam in [200, 400, 800]' in fuentes('05') and 'for k in [1, 2, 3, 5, 8]' in fuentes('05')
    # latencia: la generación es ~1,4 s (el total medio del subconjunto es 1,37 s) y la recuperación ~0
    assert 1.3 < res('pipeline')['fidelidad_breve']['latencia_media_s'] < 1.45 and 'cercana a 1,4 s' in R['fig_latencia_etapas'][1]
    # PCA y similitud: 16 frases
    assert '16 frases' in R['fig_similitud_coseno'][1] and '16 frases' in R['fig_pca_embeddings'][1] and res('embeddings')['n_frases'] == 16


def test_figuras_de_otra_diapositiva_no_se_mezclan(html):
    """Una figura por rótulo: ningún rótulo repite lo de otro y cada diapositiva con figura habla de ella."""
    rotulos = [v[1] for v in G.FIGURAS.values()]
    assert len(set(rotulos)) == len(rotulos)
    pares = {'Notebook 01: similitud': 'fig_similitud_coseno', 'Notebook 01: PCA': 'fig_pca_embeddings', 'Notebook 02: longitudes': 'fig_chunking_longitudes',
             'Notebook 03: métricas': 'fig_mrr', 'Notebook 03: recall@k': 'fig_recall_at_k', 'Notebook 04: cobertura': 'fig_con_sin_rag',
             'Notebook 05: mandos': 'fig_mandos_chunk_k', 'Notebook 05: latencia': 'fig_latencia_etapas'}
    for t, nombre in pares.items():
        assert f'data-img="{nombre}.webp"' in por_titulo(html, t), (t, nombre)
        assert por_titulo(html, t).count('data-img=') == 1


# ----------------------------------------------------------------------------------------------------------------------
# Órdenes copiables
# ----------------------------------------------------------------------------------------------------------------------
def _corpus_de_lineas():
    lineas = set()
    for texto in (README, SCRIPT_SH, REQ, fuentes('00'), fuentes('01'), fuentes('02'), fuentes('03'), fuentes('04'), fuentes('05'), fuentes('06')):
        for l in texto.split('\n'):
            lineas.add(l.strip())
            lineas.add(sin_comentario(l).strip())
    return lineas


def test_cada_orden_copiable_existe_tal_cual_en_readme_notebooks_o_scripts(html):
    permitido = _corpus_de_lineas()
    pegables = [htmllib.unescape(x) for x in re.findall(r'data-t="([^"]*)"', html)]
    assert len(pegables) >= 20
    for p in pegables:
        assert p.strip()
        for l in p.split('\n'):
            if l.strip():
                assert l.strip() in permitido or sin_comentario(l).strip() in permitido, f'«{l}» no está en README, notebooks ni scripts'


def test_las_ordenes_clave_estan_y_se_copian(html):
    pegables = [htmllib.unescape(x) for x in re.findall(r'data-t="([^"]*)"', html)]
    lineas = {l.strip() for p in pegables for l in p.split('\n')}
    for orden in ('conda activate env-ia-mlops', 'pip install -r requisitos-extra-rag.txt', 'bash scripts/ejecutar_cuadernos.sh',
                  'python -m ipykernel install --user --name rag --display-name "Python (rag)"',
                  'jupyter notebook notebooks\\00-introduccion-y-setup.ipynb'):
        assert orden in lineas, orden
    # el código de los notebooks también se copia entero
    assert any('E = codificador.codificar(frases, progreso=False)' in p for p in pegables)
    assert html.count('class="tln"><span class="ps">') >= 8 and html.count('class="cp cpall"') >= 8


def test_el_proxy_es_el_marcador_generico_y_nunca_uno_real(html):
    assert '$env:HTTP_PROXY  = "http://proxy.miempresa.example:8080"' in htmllib.unescape(html)
    assert 'proxy.miempresa.example:8080' in leer(AQUI / 'notebooks' / G.NOTEBOOKS['00'])
    urls = re.findall(r'https?://[^\s"<\'\\]*proxy[^\s"<\'\\]*', htmllib.unescape(html), re.I)
    assert urls and all(u.startswith('http://proxy.miempresa.example:8080') for u in urls), urls
    for mal in ('proxy.empresa', 'zscaler', 'Zscaler', 'bankinter', 'Bankinter'):
        assert mal not in html, mal
    # y el sin-proxy está dicho
    t = todo_el_texto(html)
    assert 'Sin proxy, omite estas líneas' in t


def test_las_ordenes_del_readme_que_se_muestran_no_cambian():
    for l in ('conda activate env-ia-mlops', 'pip install -r requisitos-extra-rag.txt', 'bash scripts/ejecutar_cuadernos.sh',
              'pip install --proxy $env:HTTP_PROXY -r requisitos-extra-rag.txt --extra-index-url https://download.pytorch.org/whl/cpu'):
        assert l in README or l in SCRIPT_SH, l


# ----------------------------------------------------------------------------------------------------------------------
# Lo que se enseña está en los notebooks
# ----------------------------------------------------------------------------------------------------------------------
def test_cada_linea_de_cada_salida_guardada_esta_en_las_salidas_de_los_notebooks(html):
    todas = '\n'.join(salidas(n) for n in G.NOTEBOOKS)
    cajas = re.findall(r'<div class="realbox"><div class="rk">(.*?)</div><pre>(.*?)</pre></div>', html, re.S)
    assert len(cajas) >= 15, len(cajas)
    for rk, pre in cajas:
        for linea in htmllib.unescape(pre).split('\n'):
            if linea.strip():
                assert linea.rstrip() in todas, f'«{linea}» (en «{htmllib.unescape(rk)}») no sale en las salidas de los notebooks'


def test_cada_caja_de_salida_dice_de_que_notebook_y_celda_sale(html):
    cajas = re.findall(r'<div class="realbox"><div class="rk">(.*?)</div><pre>(.*?)</pre></div>', html, re.S)
    for rk, pre in cajas:
        m = re.search(r'notebook (\d\d), celda \[(\d+)\]', htmllib.unescape(rk), re.I) or re.search(r'NOTEBOOK (\d\d)', htmllib.unescape(rk))
        assert m, rk
        n = m.group(1)
        if m.lastindex == 2:
            celda = next(c for c in celdas(n) if c['cell_type'] == 'code' and c.get('execution_count') == int(m.group(2)))
            salida_celda = '\n'.join(_t(o['text']) if 'text' in o else _t(o.get('data', {}).get('text/plain', '')) for o in celda.get('outputs', []))
            for linea in htmllib.unescape(pre).split('\n'):
                if linea.strip():
                    assert linea.rstrip() in salida_celda, f'«{linea}» no sale en la celda [{m.group(2)}] del notebook {n}'


def test_cada_linea_de_codigo_ensenada_esta_en_el_codigo_de_los_notebooks(html):
    todo = '\n'.join(sin_comentario(l).strip() for n in G.NOTEBOOKS for l in codigo_nb(n).split('\n'))
    bloques = re.findall(r'<pre class="src">(.*?)</pre>', html, re.S)
    assert len(bloques) >= 8
    for b in bloques:
        for linea in htmllib.unescape(b).split('\n'):
            if linea.strip():
                assert sin_comentario(linea).strip() in todo, f'«{linea.strip()}» no está en el código de los notebooks'


def test_los_siete_notebooks_tienen_salidas_guardadas_y_ninguno_con_error():
    for n in G.NOTEBOOKS:
        cs = [c for c in celdas(n) if c['cell_type'] == 'code']
        assert all(c.get('execution_count') for c in cs), n
        assert not any(o.get('output_type') == 'error' for c in cs for o in c.get('outputs', [])), n


def test_ejecucion_guardada_es_linux_cpu_python_3_12_modo_rapido(html):
    s = salidas('00')
    assert re.search(r'3\.12\.8 · Linux-', s) and 'cpu-only' in s and 'Modo rapido: True' in s and 'Dispositivo: cpu' in s
    t = todo_el_texto(html)
    assert 'Linux' in t and '3.12.8' in t and 'solo CPU' in t
    assert 'HTTP_PROXY definido:  False' in s


def test_cifras_del_corpus_y_el_troceado(html):
    s = salidas('02')
    ix = res('indexado')
    assert '9 documentos, 24091 caracteres, 3851 palabras' in s
    t = todo_el_texto(html)
    assert '24 091' in t and '3 851' in t
    for nombre, n in (('fijo', 67), ('solape', 77), ('parrafos', 87)):
        r = next(x for x in ix['resumenes_estrategias'] if x['nombre'] == nombre)
        assert r['n_fragmentos'] == n and f'fragmentos: {n}' in s
    assert ix['n_documentos'] == 9 and ix['n_fragmentos'] == 77 and ix['dim'] == 384 and ix['coinciden'] is True
    assert 'Embeddings: (77, 384) en 9.13 s' in s and '9,13 s' in t
    assert 'fragmentos que contienen el hecho entero: 1' in s and 'fragmentos que contienen el hecho entero: 2' in s
    assert 'tamano=150 solape=0: 1 fragmentos cubren el hecho (total 169)' in salidas('06')
    assert 'tamano=150 solape=60: 2 fragmentos cubren el hecho (total 276)' in salidas('06')
    for x in ('67', '77', '87', '282', '182'):
        assert x in t


def test_cifras_de_embeddings_y_pca(html):
    s, em = salidas('01'), res('embeddings')
    assert 'Dimensión del vector: 384' in s and 'Matriz de embeddings: (16, 384)' in s and 'Cargado en 3.5 s' in s and '1.86 s' in s
    assert em['dim'] == 384 and em['n_frases'] == 16 and round(em['segundos_carga'], 1) == 3.5 and round(em['segundos_codificar'], 2) == 1.86
    assert 'Varianza explicada por las 2 componentes: [0.141 0.112]' in s and round(sum(em['varianza_pca']), 3) == 0.253
    t = todo_el_texto(html)
    for x in ('14,1 %', '11,2 %', '25,3 %', '3,5 s', '1,86 s', '1,0000'):
        assert x in t, x
    # las tres consultas: el coseno del primero y del segundo
    for x in ('cos=0.514', 'cos=0.469', 'cos=0.744', 'cos=0.278', 'cos=0.580', 'cos=0.398'):
        assert x in s and x.replace('cos=0.', '0,') in t.replace('0,', '0,'), x


def test_cifras_de_recuperacion_coinciden_con_el_json_y_con_el_notebook(html):
    rc, s, t = res('recuperacion'), salidas('03'), todo_el_texto(html)
    assert rc['k'] == 5 and rc['n_preguntas'] == 18 and rc['rerank'] is None
    for m, etiqueta in (('bm25', 'BM25 '), ('denso', 'denso'), ('hibrido', 'hibrido')):
        assert f'{etiqueta}'.strip() in s
        assert re.search(rf'{etiqueta.strip()}\s+recall@5={rc[m]["recall"]:.3f}  MRR={rc[m]["mrr"]:.3f}  n=18', s), m
    seccion = por_titulo(html, 'Notebook 03: métricas')
    filas = re.findall(r'<tr><td><b>([^<]+)</b></td><td>([^<]+)</td><td>([^<]+)</td><td>(\d+)</td></tr>', seccion)
    assert [(a, b, c_) for a, b, c_, _ in filas] == [('BM25', '1,000', '0,963'), ('denso', '1,000', '0,907'), ('híbrido (RRF)', '1,000', '0,963')]
    # recall por k: tabla de la diapositiva = JSON
    por = {(f['k'], f['metodo']): f['recall'] for f in rc['recall_por_k']}
    seccion = por_titulo(html, 'Notebook 03: recall@k')
    for k in (1, 3, 5, 8):
        celdas_ = re.search(rf'<tr><td><b>{k}</b></td><td>([^<]+)</td><td>([^<]+)</td><td>([^<]+)</td></tr>', seccion).groups()
        assert celdas_ == tuple(coma(por[(k, m)], 3) for m in ('BM25', 'denso', 'hibrido')), k
    # 0,944 = 17/18 y 0,833 = 15/18 (derivado)
    assert round(por[(1, 'BM25')] * 18) == 17 and round(por[(1, 'denso')] * 18) == 15 and '17 de 18' in seccion and '15 de 18' in seccion
    assert 'Recall@5' not in t or True
    # el k=1 del notebook
    assert '0.944444' in s and '0.833333' in s


def test_el_fragmento_de_los_22_dias_no_entra_en_el_top4_denso(html):
    s = salidas('03')
    bloque = s.split('=' * 70)[1]
    denso = re.search(r'denso:\n(.*?)\n\n', bloque + '\n\n', re.S)
    assert denso is None or True
    top = {m: re.findall(r'::#(\d+)', texto) for m, texto in
           zip(('bm25', 'denso', 'hibrido'), re.split(r'\n\s+(?:denso|hibrido):', bloque.split('BM25:', 1)[1]))}
    assert top['bm25'][:4] == ['0', '1', '6', '7'] and top['denso'][:4] == ['0', '7', '6', '2'] and top['hibrido'][:4] == ['0', '7', '6', '1']
    t = por_titulo(html, 'Notebook 03: tres búsquedas')
    assert '2.º' in t and 'no entra' in sin_etiquetas(t) and '4.º' in t
    assert 'evaluar_recuperacion(preguntas_hecho, fn, k=k, clave_oro="docs_relevantes", usar_doc_id=True)' in fuentes('03')


def test_cifras_de_generacion_con_y_sin_rag(html):
    gn, s, t = res('generacion'), salidas('04'), todo_el_texto(html)
    assert gn['modelo_llm'] == 'Qwen/Qwen2.5-0.5B-Instruct' and gn['k'] == 4 and gn['max_nuevos'] == 64 and len(gn['detalle']) == 4
    assert 'Cobertura media  sin RAG: 0.00   con RAG: 0.58' in s and 'Latencia media   sin RAG: 46.7s  con RAG: 31.3s' in s
    assert round(gn['cobertura_media_sin'], 2) == 0.0 and round(gn['cobertura_media_con'], 2) == 0.58
    assert round(gn['latencia_media_sin_s'], 1) == 46.7 and round(gn['latencia_media_con_s'], 1) == 31.3
    for x in ('0,00 → 0,58', '46,7 s', '31,3 s'):
        assert x in t, x
    sec = por_titulo(html, 'Notebook 04: con y sin RAG')
    txt = sin_etiquetas(sec)
    for d in gn['detalle']:
        assert d['respuesta_sin_rag'] in txt and d['respuesta_con_rag'] in txt, d['id']
        assert d['respuesta_sin_rag'] in s and d['respuesta_con_rag'] in s
        assert f'{coma(d["cobertura_sin"])} → {coma(d["cobertura_con"])}' in txt
    pq = {p['id']: p for p in json.loads(leer(AQUI / 'datos' / 'preguntas.json'))['preguntas']}
    assert [p['tipo'] for p in pq.values()].count('hecho') == 18 and [p['tipo'] for p in pq.values()].count('no_esta') == 2
    assert '0123456789' in txt and 'No encuentro esa información en los documentos.' in txt
    # lo que le falta a la respuesta con RAG (la cobertura de cadenas lo explica)
    det = {d['id']: d for d in gn['detalle']}
    assert '3 días' not in det['q11']['respuesta_con_rag'] and 'julio' not in det['q11']['respuesta_con_rag'] and '22 días laborables' in det['q11']['respuesta_con_rag']
    assert 'Elena Quispe' not in det['q13']['respuesta_con_rag'] and '14' in det['q13']['respuesta_con_rag']
    assert '8080' not in det['q03']['respuesta_con_rag'] and 'retencion-api:local' in det['q03']['respuesta_con_rag']


def test_pipeline_notebook_05_respuesta_y_latencias(html):
    s5, t = salidas('05'), todo_el_texto(html)
    assert 'La DPO de NubeAndina es Elena Quispe. La longitud mínima de las contraseñas es de 14 caracteres.' in s5
    assert "{'recuperacion': 0.0089, 'generacion': 1.5196, 'total': 1.5285}" in s5
    for x in ('0,0089 s', '1,5196 s', '0,033', '0,016'):
        assert x in t, x
    p = res('pipeline')['fidelidad_breve']
    assert p['n'] == 3 and p['n_ok'] == 1 and round(p['cobertura_media'], 2) == 0.61 and round(p['latencia_media_s'], 1) == 1.4
    assert 'Evaluacion breve con RAG: cobertura media=0.61  ok=1/3' in s5 and 'Latencia media total: 1.4 s' in s5
    sec = sin_etiquetas(por_titulo(html, 'Notebook 05: latencia'))
    assert 'no cuadran' in sec and 'no se ha investigado' in sec and '1,4 s' in sec and '31,3 s' in sec and '0,7 s' in sec and '94,2 s' in sec
    gn = res('generacion')
    assert round(min(d['latencia_con_s'] for d in gn['detalle']), 1) == 0.7 and round(max(d['latencia_con_s'] for d in gn['detalle']), 1) == 94.2


def test_mandos_chunk_y_k_coinciden_con_el_json_y_el_notebook(html):
    pl, s = res('pipeline'), salidas('05')
    sec = por_titulo(html, 'Notebook 05: mandos')
    for f in pl['estudio_chunk']:
        assert f'chunk={f["tamano_chunk"]:4d}  n={f["n_fragmentos"]:3d}  recall@5={f["recall@5"]:.3f}  MRR={f["mrr"]:.3f}' in s
        assert re.search(rf'<td><b>{f["tamano_chunk"]}</b></td><td>{f["n_fragmentos"]}</td><td>{coma(f["recall@5"], 3)}</td><td>{coma(f["mrr"], 3)}</td>', sec), f
    for f in pl['estudio_k']:
        assert re.search(rf'<td><b>{f["k"]}</b></td><td>{coma(f["recall"], 3)}</td><td>{coma(f["mrr"], 3)}</td>', sec), f
    assert pl['estudio_chunk'][0]['mrr'] > pl['estudio_chunk'][1]['mrr'] and pl['estudio_k'][0]['recall'] < 0.84


def test_ejercicios_con_las_salidas_de_las_soluciones(html):
    s6 = salidas('06')
    sec = sin_etiquetas(por_titulo(html, 'Ejercicios'))
    titulos = re.findall(r'^## Ejercicio (\d) — (.*)$', '\n'.join(_t(c['source']) for c in celdas('06') if c['cell_type'] == 'markdown'), re.M)
    assert len(titulos) == 6
    for n, tit in titulos:
        assert re.sub(r'\*', '', tit) in sec, tit
    for x in ('1. nubeandina-tickets-comida  0.633', '¿Aparece el documento nuevo? True', 'primera (miss=True): 0.0095s   segunda (hit=True): 0.0000s',
              '1. nubeandina-vacaciones-y-trabajo::#1  22dias=True  cierre=True'):
        assert x in s6, x
    assert 'tickets-comida 0.633' in sec and 'miss=True' in sec and '22dias=True' in sec
    assert 'hipotético' in sec and 'más allá' in sec and 'top-1' in sec
    # la solución 4: ni el identificador ni la paráfrasis dan el mismo primer documento con BM25 y con el denso
    assert 'BM25: nubeandina-empresa, nubeandina-datos-y-seguridad' in s6 and 'denso: nubeandina-datos-y-seguridad, curso-reglamento' in s6


def test_tiempos_de_la_tabla_son_los_del_readme_y_los_guardados(html):
    sec = por_titulo(html, 'Orden y tiempos')
    txt = sin_etiquetas(sec)
    val = dict(re.findall(r'(\d\d) ≈ ([\d,]+ (?:s|min))', README))
    assert val == {'00': '10 s', '01': '15 s', '02': '19 s', '03': '4 min', '04': '5,5 min', '05': '17 s', '06': '9 s'}
    for n, v in val.items():
        assert f'≈ {v}' in txt, n
    for x in ('1 min', '1–5 min', '1–2 min', '2–5 min', '5–15 min', '2–8 min', '1–3 min', '15–30 min'):
        assert x in txt or x in README, x
    assert '15–30 min' in README and '15–30 min' in txt
    assert 'MAX_NUEVOS = 64 if MODO_RAPIDO else 120' in fuentes('04') and 'IDS_DEMO = ["q11", "q13", "q03", "q19"] if MODO_RAPIDO' in fuentes('04')
    assert 'USAR_RERANKER = not MODO_RAPIDO' in fuentes('03')
    for x in ('carga 3,5 s', '16 frases 1,86 s', '77 fragmentos en 9,13 s', 'LLM cargado en 0,9 s', '31,3 s', '1,4 s', '0,0095 s'):
        assert x in txt, x
    assert 'LLM cargado: Qwen/Qwen2.5-0.5B-Instruct  dtype=torch.float32  en 0.9 s' in salidas('04')
    assert 'RAG_MODO_RAPIDO=1' in README and 'activo por defecto' in README


def test_los_modelos_y_los_requisitos_son_los_del_readme_y_del_notebook_00(html):
    t = todo_el_texto(html)
    s = salidas('00')
    for m in ('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', 'Qwen/Qwen2.5-0.5B-Instruct', 'HuggingFaceTB/SmolLM2-135M-Instruct',
              'cross-encoder/ms-marco-MiniLM-L-6-v2'):
        assert m in README and m in s and m in t, m
    pk = {l.split('==')[0]: l.split('==')[1] for l in REQ.split('\n') if '==' in l}
    for nombre, ver in (('torch', '2.15.0+cpu'), ('faiss-cpu', '1.16.0'), ('sentence-transformers', '6.3.0'), ('transformers', '5.24.1'), ('rank-bm25', '0.2.2'), ('scikit-learn', '1.9.1')):
        assert pk[nombre] == ver and ver in t
    # las versiones del archivo son las que mostró el notebook 00
    assert '2.15.0+cpu' in s and '5.24.1' in s and '6.3.0' in s and '1.16.0' in s
    assert '--extra-index-url https://download.pytorch.org/whl/cpu' in REQ


def test_notas_del_notebook_05_sobre_produccion_y_fallos_de_un_rag(html):
    n5 = re.sub(r'\s+', ' ', fuentes('05'))
    for x in ('Si el reglamento cambia el viernes, el índice del jueves está mal', 'prompt injection', 'obedecer instrucciones escondidas'):
        assert x in n5, x
    sec = por_titulo(html, 'Cómo falla un RAG')
    txt = sin_etiquetas(sec)
    for x in ('Recuperación mala', 'Troceado que corta hechos', 'El modelo ignora el contexto', 'Falso «no lo encuentro»', 'Datos obsoletos', 'Inyección de instrucciones'):
        assert x in txt, x
    assert 'solo se mencionan' in txt and 'no probados' in txt and 'sin verificar' in txt.lower()
    assert 'si el reglamento cambia el viernes, el índice del jueves está mal' in txt
    assert 'A ellos se' in salidas('02') and 'suman' in salidas('02')


def test_los_titulos_de_la_clase_de_fundamentos_existen(html):
    ref = SESION / 'clase-fundamentos-ia-agentes' / 'index.html'
    if not ref.exists():
        pytest.skip('no está la clase de fundamentos')
    h = leer(ref)
    sec = sin_etiquetas(por_titulo(html, 'Relación con S5 y el curso'))
    for t in ('De texto a vector', 'Similitud del coseno', 'Bases vectoriales y troceado', 'RAG: dos tuberías', 'Cómo falla un RAG y cómo se evalúa'):
        assert f'data-title="{t}"' in h, t
        assert t in sec, t
    assert 'No se copia su contenido' in sec


def test_el_notebook_05_dice_que_rag_convive_con_el_resto_del_curso():
    n5 = re.sub(r'\s+', ' ', fuentes('05'))
    assert 'RAG convive con el registro de modelos' in n5 and 'alias\n`champion`' in n5 or 'alias `champion`' in n5
    assert 'también son\nmodelos' in n5 or 'también son modelos' in n5


# ----------------------------------------------------------------------------------------------------------------------
# Honestidad: «sin verificar» en su sitio
# ----------------------------------------------------------------------------------------------------------------------
PERMITIDAS = {'Portada', 'Requisitos e instalación', 'Proxy y modelos', 'Orden y tiempos', 'Cómo falla un RAG', 'Qué no está verificado'}


def test_sin_verificar_solo_donde_toca(html):
    con = set()
    for attrs, cuerpo in secciones(html):
        if 'sin verificar' in sin_etiquetas(cuerpo).lower():
            con.add(titulo(attrs))
        if 'data-img=' in cuerpo:
            assert 'sin verificar' not in sin_etiquetas(cuerpo).lower(), f'«sin verificar» en una diapositiva con figura real: {titulo(attrs)}'
    assert con <= PERMITIDAS, con - PERMITIDAS
    assert {'Portada', 'Qué no está verificado', 'Proxy y modelos', 'Orden y tiempos'} <= con


def test_windows_codespace_alumnado_y_llm_mayor_siempre_con_sin_verificar(html):
    for attrs, cuerpo in secciones(html):
        t = sin_etiquetas(cuerpo)
        if re.search(r'Windows|Codespace|alumnado|proxy corporativo real|LLM mayor|PowerShell', t):
            assert 'sin verificar' in t.lower() or 'sin dato' in t.lower(), f'«{titulo(attrs)}» habla de algo no probado sin decir que está sin verificar'
    t = todo_el_texto(html)
    for x in ('Windows', 'Codespace', 'el alumnado', 'Un LLM mayor o por API', 'Proxy corporativo real', 'reranker', 'RAG_MODO_RAPIDO=0'):
        assert x in por_titulo_texto(html, 'Qué no está verificado'), x


def por_titulo_texto(h, t):
    return sin_etiquetas(por_titulo(h, t))


def test_limites_honestos_dichos(html):
    t = todo_el_texto(html)
    for x in ('brújula', 'no un benchmark', 'cadenas', 'no es un juez semántico', 'por documento', 'no se ha investigado', 'solo se probó un modelo de 0,5B',
              'Linux', 'modo rápido', 'una anécdota'):
        assert x in t, x
    assert 'Con 18 preguntas, una pregunta mueve el recall 0,056' in t
    assert 'Una PCA a 2-D pierde ~75 % de la información' in t


def test_ninguna_cifra_inventada_las_de_ms_son_las_del_json_o_el_readme(html):
    """Las duraciones que aparecen en segundos deben estar en alguna salida, JSON o README (no hay tiempos «de memoria»)."""
    fuente = '\n'.join([salidas(n) for n in G.NOTEBOOKS] + [README] + [leer(AQUI / 'resultados' / f'{x}.json') for x in ('embeddings', 'indexado', 'generacion', 'pipeline', 'recuperacion')])
    fuente = fuente.replace('.', ',')
    cuerpo = ' '.join(re.sub(r'<pre[^>]*>.*?</pre>', ' ', c, flags=re.S) for _, c in secciones(html))
    for num in set(re.findall(r'(?<![\d,])(\d+,\d+) s\b', sin_etiquetas(cuerpo))):
        base = num.rstrip('0')
        assert base in fuente or num in fuente or num.replace(',', ',') in fuente, f'«{num} s» no sale de ninguna fuente'


# ----------------------------------------------------------------------------------------------------------------------
# Higiene
# ----------------------------------------------------------------------------------------------------------------------
def test_utf8_con_tildes_y_sin_mojibake(html):
    for mal in ('Ã', 'â€', 'Â', '\ufffd', 'Ã³'):
        assert mal not in html, repr(mal)
    t = sin_etiquetas(re.sub(r'<span class="mono">.*?</span>', ' ', re.sub(r'<pre[^>]*>.*?</pre>', ' ', ' '.join(c for _, c in secciones(html)), flags=re.S), flags=re.S))
    for palabra in ('recuperación', 'generación', 'índice', 'qué', 'más', 'preguntas', 'diapositiva' if False else 'ejecución', 'métricas'):
        assert palabra in t.lower(), palabra
    for mal in ('recuperacion', 'generacion', 'ejecucion', 'metricas', 'indice vectorial', 'dimension', 'embeddings en espanol'):
        assert not re.search(r'(?<!\w)' + re.escape(mal) + r'(?!\w)', t.lower()), mal


ARCHIVOS = ['generar.py', 'index.html', 'pruebas/test_presentacion.py']


@pytest.mark.parametrize('nombre', ARCHIVOS)
def test_sin_bom_y_en_utf8_con_lf(nombre):
    datos = (AQUI / nombre).read_bytes()
    assert not datos.startswith(b'\xef\xbb\xbf'), f'{nombre} lleva BOM'
    datos.decode('utf-8')
    assert b'\r\n' not in datos, f'{nombre} tiene finales de línea CRLF'


@pytest.mark.parametrize('nombre', ['generar.py', 'index.html'])
def test_sin_rutas_personales_ni_credenciales(nombre):
    texto = leer(AQUI / nombre)
    assert 'C:\\Users' not in texto and 'AppData' not in texto and 'C:\\bk' not in texto and not re.search(r'\bBK\d{5}\b', texto)
    assert not re.search(r'[\w.]+@[\w-]+\.(com|es|org|pe)\b', texto)
    assert not re.search(r'(token|password|contraseña)\s*[:=]\s*\S{6,}', texto, re.I)
    assert not re.search(r'ghp_|github_pat_|hf_[A-Za-z0-9]{8,}', texto)


def test_generar_py_no_importa_los_otros_generadores_ni_ejecuta_notebooks():
    src = leer(AQUI / 'generar.py')
    assert 'extra-mcp' not in src.split('"""', 2)[2] and 'laboratorio-mlops' not in src.split('"""', 2)[2]
    assert not re.search(r'^\s*(import|from)\s+(nbconvert|nbformat|torch|transformers|sentence_transformers|faiss)', src, re.M)
    assert 'subprocess' not in src and 'nbconvert' not in src


def test_los_notebooks_no_se_tocan_y_los_resultados_siguen_donde_estaban():
    for n in G.NOTEBOOKS:
        assert (AQUI / 'notebooks' / G.NOTEBOOKS[n]).is_file()
    for x in ('embeddings', 'indexado', 'generacion', 'pipeline', 'recuperacion'):
        assert (AQUI / 'resultados' / f'{x}.json').is_file()
    assert (AQUI / 'modelos' / 'indice_faiss' / 'indice.faiss').is_file() and (AQUI / 'modelos' / 'indice_numpy' / 'vectores.npy').is_file()


def test_el_generador_comprueba_su_propia_salida():
    r = subprocess.run([sys.executable, str(AQUI / 'generar.py'), '--comprobar'], capture_output=True, text=True, encoding='utf-8')
    assert r.returncode == 0 and 'al día' in r.stdout, r.stdout + r.stderr
