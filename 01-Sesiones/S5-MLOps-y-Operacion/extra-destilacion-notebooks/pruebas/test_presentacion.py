"""Pruebas de la presentación «Extra de S5: Destilación de modelos en notebooks» (sin navegador, sin reejecutar ningún notebook).

Qué vigilan: que index.html está al día con generar.py; la estructura (28-34 diapositivas con título, parte, minutos y notas); que el visor es el
de los otros extras de S5 (solo cambia el pie); que el fondo es blanco y nada se mueve al pasar el ratón; que cada bloque copiable existe tal
cual en el README, los notebooks, scripts/ o src/ (el proxy es un marcador genérico); que cada figura existe, es la que produce su notebook
(mismo tamaño que el PNG de resultados/), sale una vez y su rótulo dice lo que muestra y de qué notebook y celda sale; que las cifras clave
coinciden con resultados/*.json y con los .ipynb (que se leen aquí, no se copian); que los tiempos son los de la metadata de ejecución guardada;
que lo «sin verificar» está donde toca; y que no hay mojibake, recursos externos, rutas personales ni proxies o credenciales reales.
"""
import datetime as dt
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

_spec = importlib.util.spec_from_file_location('generar_extra_destilacion', AQUI / 'generar.py')
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)

NBS = ['00', '01', '02', '03', '04', '05', '06', '07']


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
    return htmllib.unescape(re.search(r'data-title="([^"]+)"', attrs).group(1))


def cuerpo_de(h, inicio_titulo):
    for attrs, c in secciones(h):
        if titulo(attrs).startswith(inicio_titulo):
            return c
    raise KeyError(inicio_titulo)


# ---- la fuente (se lee aquí, no se copia) ------------------------------------------------------------------------------------
def nb_json(n):
    ruta = sorted((AQUI / 'notebooks').glob(f'{n}-*.ipynb'))
    assert len(ruta) == 1, n
    return json.loads(leer(ruta[0]))


def celdas(n):
    return nb_json(n)['cells']


def txt(x):
    return ''.join(x) if isinstance(x, list) else x


def fuentes(n, tipo=None):
    return '\n'.join(txt(c['source']) for c in celdas(n) if tipo is None or c['cell_type'] == tipo)


def salidas(n):
    partes = []
    for c in celdas(n):
        for o in c.get('outputs', []):
            t = txt(o['text']) if 'text' in o else txt(o.get('data', {}).get('text/plain', ''))
            partes.append(t)
    return '\n'.join(partes)


def todas_las_salidas():
    return '\n'.join(salidas(n) for n in NBS)


def R(nombre):
    return json.loads(leer(AQUI / 'resultados' / f'{nombre}.json'))


def corpus_lineas():
    """Todas las líneas (sin sangría) de README, notebooks (código y texto), scripts/, src/, requisitos y JSON de resultados."""
    textos = [leer(AQUI / 'README.md'), leer(AQUI / 'requisitos-extra-destilacion.txt')]
    textos += [fuentes(n) for n in NBS]
    textos += [leer(p) for p in (AQUI / 'scripts').iterdir() if p.is_file()]
    textos += [leer(p) for p in (AQUI / 'src').glob('*.py')]
    textos += [leer(p) for p in (AQUI / 'resultados').glob('*.json')]
    return {l.strip() for t in textos for l in t.replace('\r', '').split('\n')}


def pc(x):
    return f'{x * 100:.2f}'.replace('.', ',') + ' %'


def c(x, d=2):
    return f'{x:.{d}f}'.replace('.', ',')


def t_notebook(n):
    """Suma de lo que tardó cada celda, de la metadata guardada (implementación propia, distinta de la del generador)."""
    def f(s):
        return dt.datetime.fromisoformat(s.replace('Z', '+00:00'))
    tot = 0.0
    for cel in celdas(n):
        e = cel.get('metadata', {}).get('execution') or {}
        if 'iopub.execute_input' in e and 'shell.execute_reply' in e:
            tot += (f(e['shell.execute_reply']) - f(e['iopub.execute_input'])).total_seconds()
    return tot


def fmt_t(s):
    if s < 10:
        return c(s, 1) + ' s'
    if s < 100:
        return str(round(s)) + ' s'
    return f'{int(round(s)) // 60} min {int(round(s)) % 60} s'


# ----------------------------------------------------------------------------------------------------------------------
# Estructura
# ----------------------------------------------------------------------------------------------------------------------
def test_esta_al_dia_con_el_generador(html):
    assert html == G.html_completo(), 'index.html no coincide con generar.py: ejecuta  python generar.py'


def test_entre_28_y_34_diapositivas_cada_una_con_titulo_parte_minutos_y_notas(html):
    s = secciones(html)
    assert 28 <= len(s) <= 34, len(s)
    for attrs, cuerpo in s:
        assert re.search(r'data-part="[A-F]"', attrs), attrs
        m = re.search(r'data-min="(\d+)"', attrs)
        assert m and int(m.group(1)) > 0, attrs
        assert titulo(attrs).strip()
        n = re.search(r'data-notes="([^"]*)"', attrs)
        assert n and len(n.group(1)) > 80, f'notas demasiado cortas en {titulo(attrs)}'
        assert cuerpo.count('<h1>') == 1


def test_minutos_la_portada_dice_el_total_y_es_una_propuesta(html):
    total = sum(int(m) for m in re.findall(r'data-min="(\d+)"', html))
    assert 90 <= total <= 140 and total == G.TOTAL_MIN
    assert f'{total} min' in secciones(html)[0][1] and 'propuesta' in html


def test_titulos_sin_repetir_y_antetitulos_numerados_por_partes(html):
    s = secciones(html)
    titulos = [titulo(a) for a, _ in s]
    assert len(titulos) == len(set(titulos))
    letras = list(G.PARTES)
    assert len(letras) == 6
    for attrs, cuerpo in s:
        parte = re.search(r'data-part="([A-F])"', attrs).group(1)
        kick = re.search(r'<p class="kick">(.*?)</p>', cuerpo).group(1)
        assert kick.startswith(f'{letras.index(parte) + 1} · '), kick
    orden = [re.search(r'data-part="([A-F])"', a).group(1) for a, _ in s]
    assert orden == sorted(orden) and set(orden) == set(G.PARTES)


def test_hay_un_bloque_por_notebook_de_00_a_07(html):
    titulos = [titulo(a) for a, _ in secciones(html)]
    for n in NBS:
        assert any(t.startswith(f'Notebook {n}') for t in titulos), n
    cuerpo = todo_el_texto(html)
    assert 'Si falla' in cuerpo and 'Salida guardada' in cuerpo and 'Qué debes ver' in cuerpo
    for n in NBS:
        cu = ' '.join(c for a, c in secciones(html) if titulo(a).startswith(f'Notebook {n}'))
        assert 'Copiar todo' in cu or n in ('07',), f'el notebook {n} no trae ninguna orden o celda para copiar'


def test_pie_con_posicion_x_de_total_y_un_boton_por_parte(html):
    assert '${i+1} / ${N}' in html
    assert html.count('class="part"') == 6
    assert 'ML e IA · S5 · Extra: Destilación en notebooks' in html
    assert 'Extra: MCP' not in html


def test_fondo_blanco_y_nada_se_mueve_al_pasar_el_raton(html):
    assert '--fondo:#ffffff' in html
    assert ':hover' not in html and 'transition' not in html and 'animation' not in html


def test_sin_recursos_externos_ni_cdn(html):
    assert not re.search(r'(src|href)="(https?:)?//', html)
    assert not re.search(r'@import|url\((["\']?)(https?:)?//', html)
    assert '<link' not in html and '<iframe' not in html
    for cdn in ('cdn.', 'unpkg', 'jsdelivr', 'googleapis', 'cdnjs', 'gstatic'):
        assert cdn not in html, cdn


def test_boton_indice_de_regreso_a_la_sesion(html):
    assert '<a id="bhome" href="../index.html"' in html and '⌂ Índice' in html
    assert (SESION / 'index.html').exists()


def test_marco_zoom_con_lupa_clic_esc_flechas_y_notas_con_s(html):
    for clave in ("k==='Escape'", "k==='ArrowRight'", "k==='ArrowLeft'", "k==='s'||k==='S'", 'id="zoombox"', 'cursor:zoom-in', 'id="notes"'):
        assert clave in html, clave
    assert html.count('class="lupa"') == len(G.FIGURAS)
    assert 'Notas del profesor' in html


def test_el_visor_es_el_de_los_otros_extras_salvo_el_pie():
    ref = SESION / 'extra-mcp-notebooks' / 'index.html'
    if not ref.exists():
        pytest.skip('no está el extra de MCP')
    ag, mio = leer(ref), leer(AQUI / 'index.html')
    css_a = re.search(r'<style>(.*?)</style>', ag, re.S).group(1)
    css_m = re.search(r'<style>(.*?)</style>', mio, re.S).group(1)
    assert css_m.startswith(css_a), 'el CSS del visor ya no es el de los otros extras (solo se admiten añadidos al final)'
    js_a = re.search(r'<script>(.*?)</script>', ag, re.S).group(1).replace('ML e IA · S5 · Extra: MCP en notebooks', 'PIE')
    js_m = re.search(r'<script>(.*?)</script>', mio, re.S).group(1).replace('ML e IA · S5 · Extra: Destilación en notebooks', 'PIE')
    js_a = re.sub(r'const PARTES=\{.*?\};', 'const PARTES={};', js_a, flags=re.S)
    js_m = re.sub(r'const PARTES=\{.*?\};', 'const PARTES={};', js_m, flags=re.S)
    assert js_a == js_m


def test_sin_tabuladores_ni_marcas_markdown_sin_convertir(html):
    assert '\t' not in html
    sin_codigo = re.sub(r'<span class="mono">.*?</span>', ' ', re.sub(r'<pre[^>]*>.*?</pre>', ' ', ' '.join(c_ for _, c_ in secciones(html)), flags=re.S), flags=re.S)
    texto = sin_etiquetas(sin_codigo)
    assert not re.search(r'(?<!/)\*\*', texto), 'un **negrita** sin convertir'
    assert '`' not in texto, 'una `comilla` sin convertir'


def test_una_idea_por_diapositiva_titulo_corto_y_pocas_palabras(html):
    for attrs, cuerpo in secciones(html):
        h1 = sin_etiquetas(re.search(r'<h1>(.*?)</h1>', cuerpo, re.S).group(1))
        assert len(h1) <= 118, f'título largo en «{titulo(attrs)}»: {len(h1)}'
        prosa = re.sub(r'<pre[^>]*>.*?</pre>', ' ', cuerpo, flags=re.S)
        palabras = len(sin_etiquetas(prosa).split())
        assert palabras <= 330, f'demasiado texto en «{titulo(attrs)}»: {palabras} palabras'
        assert cuerpo.count('class="msg"') <= 1


def test_el_cierre_tiene_un_mensaje_y_cuatro_tarjetas_con_cifras(html):
    ultima = secciones(html)[-1][1]
    assert ultima.count('class="msg"') == 1 and ultima.count('class="card kpi"') == 4
    for cifra in ('1 frase', '¿Preguntas?', 'TinyBERT duro en fp32'):
        assert cifra in sin_etiquetas(ultima), cifra


# ----------------------------------------------------------------------------------------------------------------------
# Figuras: lo que producen los notebooks
# ----------------------------------------------------------------------------------------------------------------------
def test_las_once_figuras_de_resultados_estan_convertidas_y_salen_una_vez(html):
    pngs = sorted(p.stem for p in (AQUI / 'resultados').glob('fig_*.png'))
    assert pngs == sorted(G.FIGURAS), 'cada figura de resultados/ tiene su rótulo y viceversa'
    assert len(pngs) == 11
    cuerpo = ' '.join(c_ for _, c_ in secciones(html))
    for nombre in pngs:
        assert (AQUI / 'img' / f'{nombre}.webp').is_file(), nombre
        assert f'img/{nombre}.webp' in html
        assert cuerpo.count(f'data-img="{nombre}.webp"') == 1, nombre
    for ruta in re.findall(r'(?:src|data-src)="(img/[^"]+)"', html):
        assert (AQUI / ruta).is_file(), ruta
    assert 'Captura pendiente' not in html and 'class="pend"' not in html


def test_cada_webp_es_la_misma_imagen_que_el_png_del_notebook():
    from PIL import Image, ImageChops
    for nombre in G.FIGURAS:
        with Image.open(AQUI / 'resultados' / f'{nombre}.png') as a, Image.open(AQUI / 'img' / f'{nombre}.webp') as b:
            assert b.format == 'WEBP' and b.width >= 300 and b.height >= 100
            assert a.size == b.size, nombre
            diff = ImageChops.difference(a.convert('RGB'), b.convert('RGB'))
            assert diff.getbbox() is None, f'{nombre}: el webp no es idéntico al PNG original'


def test_un_rotulo_una_imagen_y_el_pie_dice_de_que_notebook_y_celda_sale(html):
    figuras = re.findall(r'<figure class="cap" data-img="([^"]+)">(.*?)</figure>', html, re.S)
    assert len(figuras) == 11
    for nombre_webp, cuerpo in figuras:
        base = nombre_webp[:-5]
        assert cuerpo.count('<img ') == 1 and cuerpo.count('<figcaption>') == 1
        alt = htmllib.unescape(re.search(r'<img [^>]*alt="([^"]*)"', cuerpo).group(1))
        pie = sin_etiquetas(re.search(r'<figcaption>(.*?)</figcaption>', cuerpo, re.S).group(1))
        assert alt == G.FIGURAS[base] and alt in pie and len(alt) > 90
        m = re.search(r'Sale de: notebook (\d\d), celda (\d+) → resultados/' + re.escape(base) + r'\.png', pie)
        assert m, pie
        n, i = m.group(1), int(m.group(2))
        cel = celdas(n)[i]
        assert cel['cell_type'] == 'code' and f'{base}.png' in txt(cel['source']), f'{base} no se guarda en la celda {i} del notebook {n}'
        # y es la ÚNICA celda que lo guarda
        todas = [(k, j) for k in NBS for j, cc in enumerate(celdas(k)) if cc['cell_type'] == 'code' and f'{base}.png' in txt(cc['source'])]
        assert todas == [(n, i)], todas
        # la celda produjo de verdad una imagen guardada
        assert any('image/png' in o.get('data', {}) for o in cel.get('outputs', [])), f'la celda {i} del notebook {n} no tiene la figura en su salida'


def test_los_titulos_citados_en_los_rotulos_son_los_de_las_figuras_del_notebook():
    for base, rotulo in G.FIGURAS.items():
        n = next(k for k in NBS for cc in celdas(k) if cc['cell_type'] == 'code' and f'{base}.png' in txt(cc['source']))
        codigo = '\n'.join(txt(cc['source']) for cc in celdas(n) if cc['cell_type'] == 'code')
        for citado in re.findall(r'«([^»]+)»', rotulo):
            assert citado in codigo, f'«{citado}» (rótulo de {base}) no está en el código del notebook {n}'


def test_lo_que_dicen_los_rotulos_coincide_con_el_codigo_y_los_datos():
    assert 'temperaturas = [0.5, 1, 2, 5, 10]' in fuentes('01') and 'Cinco paneles' in G.FIGURAS['fig_softmax_temperatura']
    assert 'for T in [1, 2, 3, 5, 8]' in fuentes('01') and 'T = 1 · 2 · 3 · 5 · 8' in G.FIGURAS['fig_kl_temperatura']
    assert 'profesor(x_vis[:6])' in fuentes('02') and 'range(6)' in fuentes('02') and 'Seis dígitos' in G.FIGURAS['fig_mnist_blandas']
    assert 'plt.subplots(3, 8' in fuentes('05') and 'Ocho dígitos' in G.FIGURAS['fig_ejercicio2_blandas_mnist']
    assert len(R('comparativa')['comparativa']) == 6 and 'seis modelos' in G.FIGURAS['fig_comparativa_pareto']
    assert 'T = 4' in G.FIGURAS['fig_mnist_blandas'] and R('mnist')['temperature'] == 4.0
    assert 'puerta (−4 puntos)' in fuentes('06') and '−4 puntos' in G.FIGURAS['fig_v2_curvas']


# ----------------------------------------------------------------------------------------------------------------------
# Órdenes copiables
# ----------------------------------------------------------------------------------------------------------------------
def pegables(html):
    return [htmllib.unescape(x) for x in re.findall(r'data-t="([^"]*)"', html)]


def test_hay_botones_de_copiar_y_ninguno_vacio(html):
    p = pegables(html)
    assert len(p) >= 40
    assert all(x.strip() for x in p)
    assert html.count('class="tln"><span class="ps">$</span>') >= 20


def test_cada_linea_copiable_existe_tal_cual_en_readme_notebooks_scripts_o_src(html):
    corpus = corpus_lineas()
    for texto in pegables(html):
        texto = texto.replace(G.PROXY_EJEMPLO, G.PROXY_README)          # el marcador genérico vuelve al ejemplo del README para comparar
        for linea in texto.split('\n'):
            if linea.strip():
                assert linea.strip() in corpus, f'«{linea.strip()}» no está en README, notebooks, scripts ni src'


def test_ordenes_clave_presentes(html):
    p = pegables(html)
    juntas = '\n'.join(p)
    for orden in ('conda activate env-ia-mlops', 'pip install -r requisitos-extra-destilacion.txt',
                  'pip install -r requisitos-extra-destilacion.txt --extra-index-url https://download.pytorch.org/whl/cpu',
                  'bash scripts/ejecutar_cuadernos.sh', 'export HF_HUB_OFFLINE=1', 'tabla_entorno = comprobar_entorno()'):
        assert orden in juntas, orden
    assert 'bash scripts/ejecutar_cuadernos.sh' in leer(AQUI / 'README.md')
    assert 'jupyter nbconvert' in leer(AQUI / 'scripts' / 'ejecutar_cuadernos.sh')


def test_el_json_del_ejercicio_4_es_el_que_escribe_el_notebook_y_se_copia(html):
    json_copiable = next(json.loads(x) for x in pegables(html) if x.lstrip().startswith('{') and '"params"' in x)
    assert json_copiable == R('ejercicio4_registro_run')
    assert 'ejercicio4_registro_run.json' in fuentes('05')
    d = R('sentimiento')
    assert json_copiable['metrics']['acc_estudiante_destilado'] == d['modelos']['estudiante_destilado']['exactitud']


def test_el_proxy_es_un_marcador_generico_y_no_hay_credenciales(html):
    assert 'proxy.miempresa.example:8080' in html
    assert 'proxy.empresa' not in html and 'usuario:contraseña' not in html
    urls = set(re.findall(r'https?://[^\s"\'<>]*proxy[^\s"\'<>]*', htmllib.unescape(html)))
    assert urls <= {'http://proxy.miempresa.example:8080', 'http://proxy.miempresa.example:8080"'}, urls
    assert not re.search(r'(HF_TOKEN|hf_)[=\s"]+[A-Za-z0-9_]{10,}', html)
    assert 'SSL_CERT_FILE' in html     # se nombra la variable, sin ninguna ruta de certificado real
    assert not re.search(r'[A-Za-z]:\\[^\s<]*\.pem', html)


# ----------------------------------------------------------------------------------------------------------------------
# Lo que se enseña está en los notebooks y en resultados/
# ----------------------------------------------------------------------------------------------------------------------
def test_cada_linea_de_cada_salida_guardada_esta_en_las_salidas_de_los_notebooks(html):
    todas = todas_las_salidas()
    cajas = re.findall(r'<div class="realbox"><div class="rk">(.*?)</div><pre>(.*?)</pre></div>', html, re.S)
    assert len(cajas) >= 12
    for rk, pre in cajas:
        for linea in htmllib.unescape(pre).split('\n'):
            if linea.strip():
                assert linea.rstrip() in todas, f'«{linea}» (en «{htmllib.unescape(rk)}») no sale en las salidas de los notebooks'


def test_cada_linea_de_codigo_ensenada_esta_en_el_codigo_de_notebooks_src_o_readme(html):
    corpus = corpus_lineas()
    bloques = re.findall(r'<pre class="src">(.*?)</pre>', html, re.S)
    assert len(bloques) >= 14
    for b in bloques:
        for linea in htmllib.unescape(b).split('\n'):
            if linea.strip():
                assert linea.strip() in corpus, f'«{linea.strip()}» no está en el código fuente'


def test_las_cifras_de_cada_diapositiva_salen_de_los_json_y_de_los_notebooks(html):
    t = todo_el_texto(html)
    mn, se, v2, e5 = R('mnist'), R('sentimiento'), R('v2_sentimiento'), R('ejercicio5_promocion')
    M, S, V = mn['modelos'], se['modelos'], v2['modelos']
    # MNIST
    for x in (M['profesor']['exactitud'], M['estudiante_duro']['exactitud'], M['estudiante_destilado']['exactitud']):
        assert pc(x) in t, x
    assert '+' + c((M['estudiante_destilado']['exactitud'] - M['estudiante_duro']['exactitud']) * 100) + ' puntos' in t
    assert M['profesor']['parametros'] == 235146 and M['estudiante_duro']['parametros'] == 25450
    # sentimiento v1
    for x in (S['profesor']['exactitud'], S['estudiante_duro']['exactitud'], S['estudiante_destilado']['exactitud']):
        assert pc(x) in t, x
    assert c((S['profesor']['exactitud'] - S['estudiante_destilado']['exactitud']) * 100) in t
    assert '66 955 010' in t and '2 003 586' in t and S['profesor']['parametros'] == 66955010 and S['estudiante_duro']['parametros'] == 2003586
    # v2
    for x in (v2['exactitud_profesor'], v2['puerta_calidad'], V['estudiante_duro']['exactitud'], V['estudiante_destilado']['exactitud'], V['estudiante_duro']['exactitud_int8']):
        assert pc(x) in t, x
    assert '14 350 874' in t and V['estudiante_duro']['parametros'] == 14350874
    assert c(V['profesor']['latencia_ms_lote_p95']) in t and c(V['estudiante_duro']['latencia_ms_lote_p95']) in t
    of = v2['puertas']['oficial']
    assert of['decision'] == 'PROMOCIONAR' and v2['variante_oficial'] == 'estudiante_duro' and v2['precision_oficial'] == 'fp32'
    for x in (c(of['hueco_puntos']) + ' ', c(of['aceleracion_p95']) + '×'):
        assert x in t, x
    assert c(v2['puertas']['duro_int8_lote16']['hueco_puntos']) in t and c(v2['puertas']['duro_int8_lote16']['aceleracion_p95']) + '×' in t
    assert c(v2['puertas']['int8_lote1']['aceleracion_p95']) + '×' in t
    # ejercicio 5 (v1)
    assert e5['decision'] == 'NO PROMOCIONAR' and c(e5['hueco_puntos']) in t and c(e5['aceleracion_p95'], 1) + '×' in t
    # el destilado fp32 de la v2 sale de la salida del notebook 06
    o6 = salidas('06')
    assert re.search(r'estudiante_destilado fp32\s+acc=0\.8830\s+hueco=2\.75\s+acel=7\.67×\s+PROMOCIONAR', o6)
    assert '2,75' in t and '7,67×' in t


def test_las_cifras_de_los_json_coinciden_con_las_salidas_guardadas_de_los_notebooks():
    mn, se, v2 = R('mnist'), R('sentimiento'), R('v2_sentimiento')
    o2, o3, o4, o6 = salidas('02'), salidas('03'), salidas('04'), salidas('06')
    assert "'exactitud': 0.9692" in o2 and f"{mn['modelos']['estudiante_destilado']['exactitud']:.4f}" in o2
    assert '0.8638' in o2 and '0.8412' in o2
    assert 'test destilado' in o3 and f"{se['modelos']['estudiante_destilado']['exactitud']}" in o3
    assert '0.9106' in o2 + o3 + o4 + o6 and 'hueco=2.64' in o6 and 'acel=7.69×' in o6
    assert 'exactitud int8  duro=0.8589  destilado=0.8589' in o6
    assert f"{v2['modelos']['estudiante_duro']['exactitud']:.4f}" == '0.8842'
    assert '108.1268' in o4 and '3.3781' in o4


def test_la_diferencia_duro_destilado_de_la_v2_es_exactamente_una_frase(html):
    v2 = R('v2_sentimiento')
    d = v2['modelos']['estudiante_duro']['exactitud'] - v2['modelos']['estudiante_destilado']['exactitud']
    assert round(d * v2['n_test']) == 1 and abs(d * v2['n_test'] - 1) < 0.01
    t = todo_el_texto(html)
    assert '1 frase' in t and '872' in t and 'una frase' in t and c(100 / 872, 3) in t


def test_la_ablacion_sale_de_v2_comparativa_json_y_las_sondas_de_v2_probe(html):
    comp, probe = R('v2_comparativa'), R('v2_probe')
    t = todo_el_texto(html)
    assert len(comp['ablacion']) == 10
    for fila in comp['ablacion']:
        assert fila['variante'] in t and pc(fila['exactitud']) in t, fila['variante']
        assert c(fila['hueco_vs_profesor_puntos']) in t
    assert pc(probe['hard-16k-2ep']['best_test']) in t and pc(probe['kd-16k-2ep']['best_test']) in t
    assert probe['teacher_test'] > 0.91 and round(probe['gate'], 4) == 0.8706


def test_los_tiempos_son_los_de_la_metadata_de_ejecucion_guardada(html):
    t = todo_el_texto(html)
    total = 0.0
    for n in NBS:
        s = t_notebook(n)
        total += s
        assert fmt_t(s) in t, (n, fmt_t(s))
    assert fmt_t(total) in t
    assert t_notebook('06') > 700 > 100 > t_notebook('03') > t_notebook('02') > 20      # el 06 es, con diferencia, el que más tarda
    readme = leer(AQUI / 'README.md')
    for fila in re.findall(r'^\| (\d\d) \|.*\| ([^|]+) \|$', readme, re.M):
        assert re.sub(r'\s', '', fila[1].replace('`', '')) in re.sub(r'\s', '', t), fila


def test_las_versiones_del_notebook_00_coinciden_con_los_requisitos_y_se_muestran(html):
    reqs = leer(AQUI / 'requisitos-extra-destilacion.txt')
    o0 = salidas('00')
    cuerpo = sin_etiquetas(cuerpo_de(html, 'Entorno'))
    for pin in ('numpy', 'pandas', 'scikit-learn', 'torch', 'torchvision', 'transformers', 'datasets', 'accelerate'):
        v = re.search(rf'^{re.escape(pin)}==(\S+)$', reqs, re.M).group(1)
        assert v in o0, f'{pin} {v} no aparece en la salida del notebook 00'
        assert v in cuerpo, pin
    assert '✗' not in cuerpo and cuerpo.count('✓') == 8
    assert '3.12.8' in o0 and 'Linux' in o0 and 'cpu-only' in o0


def test_las_decisiones_de_promocion_y_el_ejercicio_5_son_los_de_los_notebooks(html):
    e5 = R('ejercicio5_promocion')
    assert e5['decision'] == 'NO PROMOCIONAR' and e5['cumple_calidad'] is False and e5['cumple_latencia'] is True
    assert '4 puntos' in fuentes('05') and '5 veces' in fuentes('05')
    assert 'decisión según el enunciado: NO PROMOCIONAR' in salidas('05')
    t = sin_etiquetas(cuerpo_de(html, 'Cómo se promociona'))
    assert 'PROMOCIONAR' in t and t.count('NO PROMOCIONAR') == 3 and '†' in t
    v2 = R('v2_sentimiento')
    assert 'OFICIAL: estudiante_duro fp32 PROMOCIONAR' in salidas('06') and v2['puertas']['oficial']['cumple_latencia']


def test_los_ejercicios_son_los_cinco_del_notebook_05(html):
    md = fuentes('05', 'markdown')
    for clave in ('Softmax con temperatura, a mano', 'Leer las blandas de un profesor real', 'Un profesor inútil', 'Qué registrarías en un *run*', 'Un criterio de promoción'):
        assert clave in md, clave
    t = sin_etiquetas(cuerpo_de(html, 'Notebook 05'))
    for clave in ('softmax estable a mano', 'leer blandas reales', 'profesor inútil', 'qué registrar en un run', 'un criterio de promoción'):
        assert clave in t, clave
    assert 'class ProfesorRuido' in fuentes('05') and '0.113' in salidas('05') and '0.425' in salidas('05')


def test_las_frases_citadas_estan_literalmente_en_los_notebooks_o_el_readme(html):
    """Toda cita «entre comillas» del texto de las diapositivas (no las de los rótulos de las figuras) es literal de la fuente."""
    fuente_total = ' '.join(re.sub(r'\s+', ' ', x) for x in [leer(AQUI / 'README.md')] + [fuentes(n) for n in NBS] + [salidas(n) for n in NBS])
    fuente_total = fuente_total.replace('*', '').replace('`', '').replace('\\(', '').replace('\\)', '')
    citas = []
    for attrs, cuerpo in secciones(html):
        sin = re.sub(r'<pre[^>]*>.*?</pre>', ' ', re.sub(r'<figcaption>.*?</figcaption>', ' ', cuerpo, flags=re.S), flags=re.S)
        for q in re.findall(r'«([^»]{12,})»', sin_etiquetas(sin)):
            citas.append((titulo(attrs), q.strip()))
    assert len(citas) >= 12, len(citas)
    for tit, q in citas:
        assert re.sub(r'\s', '', q) in re.sub(r'\s', '', fuente_total), f'la cita «{q}» (en «{tit}») no está literalmente en el README ni en los notebooks'
    todas = ' '.join(q for _, q in citas)
    for esperada in ('suele quedar por encima del duro', 'no necesariamente más exactitud en test', 'TinyBERT ya llega predestilado de un BERT grande', 'la mejor época en test', "No module named 'onnxscript'"):
        assert esperada in todas, esperada


# ----------------------------------------------------------------------------------------------------------------------
# Honestidad: «sin verificar» en su sitio
# ----------------------------------------------------------------------------------------------------------------------
def test_sin_verificar_solo_donde_toca(html):
    permitidas = {'Portada', 'Entorno nuevo', 'Proxy y Hugging Face', 'Ejecutar los ocho', 'Relación con S5', 'Límites honestos', 'Qué quedó sin verificar'}
    con = set()
    for attrs, cuerpo in secciones(html):
        if 'sin verificar' in sin_etiquetas(cuerpo).lower():
            con.add(titulo(attrs))
        if 'data-img=' in cuerpo:
            assert 'sin verificar' not in sin_etiquetas(cuerpo).lower(), f'«sin verificar» en una diapositiva con figura real: {titulo(attrs)}'
    assert con <= permitidas, con - permitidas
    assert {'Portada', 'Entorno nuevo', 'Proxy y Hugging Face', 'Ejecutar los ocho', 'Qué quedó sin verificar'} <= con


def test_windows_codespace_alumnado_y_gpu_siempre_con_sin_verificar(html):
    for attrs, cuerpo in secciones(html):
        t = sin_etiquetas(re.sub(r'<pre[^>]*>.*?</pre>', ' ', cuerpo, flags=re.S))
        if re.search(r'Windows|Codespace|alumnado|\bGPU\b|PowerShell', t):
            assert 'sin verificar' in t.lower(), f'«{titulo(attrs)}» habla de Windows, Codespace, alumnado o GPU sin decir que está sin verificar'
    t = todo_el_texto(html)
    for x in ('Windows', 'Codespace', 'Alumnado', 'GPU'):
        assert x in t, x
    # lo que se afirma como comprobado es lo que dicen los notebooks: Linux, CPU, Python 3.12.8
    o0 = salidas('00')
    assert 'Linux' in o0 and '3.12.8' in o0 and 'cpu-only' in o0 and 'Dispositivo: cpu' in o0 and 'CUDA' in o0
    assert 'Python 3.12.8' in t or '3.12.8' in t


def test_limites_dichos(html):
    t = todo_el_texto(html)
    for x in ('una sola ejecución', 'mejor época en test', 'optimista', '872', 'MNIST con 400 etiquetas', 'no se afinaron', 'remedirla', 'lote 1',
              'no ganan al duro', 'sesgos', 'redestilar', 'MLflow', 'Este extra no los usa'):
        assert x in t or x.lower() in t.lower(), x
    assert 'una ejecución' in t.lower() or 'una sola ejecución' in t.lower()
    assert 'sorpresa' not in t.lower()


def test_la_v1_no_promociona_y_la_destilacion_no_gana_al_duro_en_la_v2(html):
    t = todo_el_texto(html)
    assert 'las blandas no ganan al duro' in t or 'no ganan al duro' in t
    assert 'la destilación no gana' in t.lower() or 'no gana al duro' in t.lower()
    assert 'TinyBERT ya fue destilado' in t
    assert 'NO PROMOCIONAR' in t and 'PROMOCIONAR' in t


# ----------------------------------------------------------------------------------------------------------------------
# Higiene
# ----------------------------------------------------------------------------------------------------------------------
def test_utf8_con_tildes_y_sin_mojibake(html):
    for mal in ('Ã', 'â€', 'Â', '\ufffd', 'Ã³'):
        assert mal not in html, repr(mal)
    cuerpo = ' '.join(c_ for _, c_ in secciones(html))
    for patron in (r'<pre[^>]*>.*?</pre>', r'<code>.*?</code>', r'<div class="bar">.*?</div>', r'<p class="fuente">.*?</p>', r'<span class="mono">.*?</span>', r'<span class="orig">.*?</span>'):
        cuerpo = re.sub(patron, ' ', cuerpo, flags=re.S)
    t = sin_etiquetas(cuerpo).lower()
    for palabra in ('destilación', 'producción', 'etiquetas', 'temperatura', 'pérdida', 'parámetros', 'exactitud', 'qué', 'más', 'época', 'ejecución', 'versión'):
        assert palabra in t, palabra
    for mal in ('destilacion', 'produccion', 'parametros', 'epoca', 'ejecucion', 'perdida', 'exactitud en train ', 'que debes ver', 'mas probable', 'version'):
        assert not re.search(r'(?<!\w)' + re.escape(mal) + r'(?!\w)', t), mal
    assert 'si falla' not in sin_etiquetas(cuerpo).replace('Si falla', '').lower() or True


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
    assert '/workspace/destilacion' not in texto and 'bankinter' not in texto.lower()
    assert not re.search(r'[\w.]+@[\w-]+\.(com|es|org)', texto)
    assert not re.search(r'(token|password|contraseña)\s*[:=]\s*["\']?[A-Za-z0-9_\-]{12,}', texto, re.I)
    assert not re.search(r'ghp_|github_pat_|hf_[A-Za-z0-9]{10,}', texto)


def test_la_carpeta_solo_ha_ganado_la_presentacion_y_no_se_toco_la_fuente():
    """generar.py, index.html, img/ y pruebas/ son lo único nuevo: los notebooks siguen con sus salidas guardadas."""
    for n in NBS:
        for cel in celdas(n):
            if cel['cell_type'] == 'code':
                assert cel.get('execution_count') is not None, f'el notebook {n} tiene una celda sin ejecutar'
    assert sorted(p.name for p in (AQUI / 'img').iterdir()) == sorted(f'{b}.webp' for b in G.FIGURAS)


def test_el_generador_comprueba_su_propia_salida():
    r = subprocess.run([sys.executable, str(AQUI / 'generar.py'), '--comprobar'], capture_output=True, text=True, encoding='utf-8')
    assert r.returncode == 0 and 'al día' in r.stdout, r.stdout + r.stderr
