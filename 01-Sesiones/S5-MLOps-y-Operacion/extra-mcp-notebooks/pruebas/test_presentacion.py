"""Pruebas de la presentación del «Extra de S5: MCP en notebooks» (sin navegador).

Qué vigilan: que index.html está al día con generar.py; la estructura (entre 22 y 28 diapositivas con título, parte, minutos y notas,
60-75 min); que el visor es el del laboratorio de agentes (solo cambia el pie); que el fondo es blanco y nada se mueve al pasar el
ratón; que cada orden tiene su botón de copiar; que las capturas existen, salen una vez y no hay ninguna pendiente; que TODO lo que se
enseña como «salida guardada» o «código del notebook» está de verdad en los notebooks (que se leen aquí, no se copian) y que las cifras
clave de la presentación coinciden con las de los notebooks; que lo «sin verificar» está donde toca (y no en lo verificado); que no hay
mojibake, rutas personales ni secretos; y que cada diapositiva lleva una sola idea (un título, pocas palabras).
"""
import html as htmllib
import importlib.util
import json
import re
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parents[1]
SESION = AQUI.parent

_spec = importlib.util.spec_from_file_location('generar_extra_mcp', AQUI / 'generar.py')
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


# ---- los notebooks (se leen aquí: la fuente de las cifras) -------------------------------------------------------------------
def celdas(n):
    return json.loads(leer(AQUI / G.NOTEBOOKS[n]))['cells']


def src(n, i):
    s = celdas(n)[i]['source']
    return ''.join(s) if isinstance(s, list) else s


def salidas(n):
    """Todo lo que imprimieron las celdas de código de un notebook, junto."""
    partes = []
    for c in celdas(n):
        for o in c.get('outputs', []):
            t = o.get('text') or o.get('data', {}).get('text/plain') or ''
            partes.append(''.join(t) if isinstance(t, list) else t)
    return '\n'.join(partes)


def fuentes(n):
    return '\n'.join(''.join(c['source']) if isinstance(c['source'], list) else c['source'] for c in celdas(n))


def coma(x):
    return str(x).replace('.', ',')


def sin_comentario(linea):
    return re.sub(r'\s{2,}#.*$', '', linea).rstrip()


# ----------------------------------------------------------------------------------------------------------------------
# Estructura
# ----------------------------------------------------------------------------------------------------------------------
def test_esta_al_dia_con_el_generador(html):
    assert html == G.html_completo(), 'index.html no coincide con generar.py: ejecuta  python generar.py'


def test_entre_22_y_28_diapositivas_cada_una_con_titulo_parte_minutos_y_notas(html):
    s = secciones(html)
    assert 22 <= len(s) <= 28, len(s)
    for attrs, cuerpo in s:
        assert re.search(r'data-part="[A-E]"', attrs), attrs
        m = re.search(r'data-min="(\d+)"', attrs)
        assert m and int(m.group(1)) > 0, attrs
        assert titulo(attrs).strip()
        n = re.search(r'data-notes="([^"]*)"', attrs)
        assert n and len(n.group(1)) > 80, f'notas demasiado cortas en {titulo(attrs)}'
        assert cuerpo.count('<h1>') == 1


def test_minutos_entre_60_y_75_y_la_portada_dice_el_total(html):
    total = sum(int(m) for m in re.findall(r'data-min="(\d+)"', html))
    assert 60 <= total <= 75, total
    assert total == G.TOTAL_MIN
    assert f'{total} min' in secciones(html)[0][1] or f'{total} min' in todo_el_texto(html)


def test_titulos_sin_repetir_y_antetitulos_numerados_por_partes(html):
    s = secciones(html)
    titulos = [titulo(a) for a, _ in s]
    assert len(titulos) == len(set(titulos))
    letras = list(G.PARTES)
    for attrs, cuerpo in s:
        parte = re.search(r'data-part="([A-E])"', attrs).group(1)
        kick = re.search(r'<p class="kick">(.*?)</p>', cuerpo).group(1)
        assert kick.startswith(f'{letras.index(parte) + 1} · '), kick
    orden = [re.search(r'data-part="([A-E])"', a).group(1) for a, _ in s]
    assert orden == sorted(orden) and set(orden) == set(G.PARTES)


def test_pie_con_posicion_x_de_total_y_un_boton_por_parte(html):
    assert '${i+1} / ${N}' in html
    assert html.count('class="part"') == len(G.PARTES)
    assert 'ML e IA · S5 · Extra: MCP en notebooks' in html and 'Laboratorio de agentes</span>' not in html


def test_fondo_blanco_y_nada_se_mueve_al_pasar_el_raton(html):
    assert '--fondo:#ffffff' in html
    assert ':hover' not in html and 'transition' not in html and 'animation' not in html


def test_sin_recursos_externos(html):
    assert not re.search(r'(src|href)="(https?:)?//', html)
    assert not re.search(r'@import|url\((["\']?)(https?:)?//', html)
    assert '<link' not in html and '<iframe' not in html


def test_boton_indice_de_regreso_a_la_sesion(html):
    assert '<a id="bhome" href="../index.html"' in html and '⌂ Índice' in html
    assert (SESION / 'index.html').exists()


def test_marco_zoom_con_clic_esc_y_flechas(html):
    for clave in ("k==='Escape'", "k==='ArrowRight'", "k==='ArrowLeft'", 'id="zoombox"', 'cursor:zoom-in'):
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
    js_m = re.search(r'<script>(.*?)</script>', mio, re.S).group(1).replace('ML e IA · S5 · Extra: MCP en notebooks', 'PIE')
    js_a = re.sub(r'const PARTES=\{.*?\};', 'const PARTES={};', js_a, flags=re.S)
    js_m = re.sub(r'const PARTES=\{.*?\};', 'const PARTES={};', js_m, flags=re.S)
    assert js_a == js_m


def test_sin_tabuladores_ni_marcas_markdown_sin_convertir(html):
    assert '\t' not in html
    texto = sin_etiquetas(re.sub(r'<span class="mono">.*?</span>', ' ', re.sub(r'<pre[^>]*>.*?</pre>', ' ', ' '.join(c for _, c in secciones(html)), flags=re.S), flags=re.S))
    assert not re.search(r'(?<!/)\*\*', texto), 'un **negrita** sin convertir'
    assert not re.search(r'(?<!\w)`', texto) and '`' not in texto, 'una `comilla` sin convertir'


# ----------------------------------------------------------------------------------------------------------------------
# Una sola idea por diapositiva
# ----------------------------------------------------------------------------------------------------------------------
def test_una_idea_por_diapositiva_titulo_corto_y_pocas_palabras(html):
    for attrs, cuerpo in secciones(html):
        h1 = sin_etiquetas(re.search(r'<h1>(.*?)</h1>', cuerpo, re.S).group(1))
        assert len(h1) <= 112, f'título largo en «{titulo(attrs)}»: {len(h1)}'
        prosa = re.sub(r'<pre[^>]*>.*?</pre>', ' ', cuerpo, flags=re.S)
        palabras = len(sin_etiquetas(prosa).split())
        assert palabras <= 330, f'demasiado texto en «{titulo(attrs)}»: {palabras} palabras'
        assert cuerpo.count('class="msg"') <= 1


def test_el_cierre_tiene_un_mensaje_y_cuatro_tarjetas_con_cifras(html):
    ultima = secciones(html)[-1][1]
    assert ultima.count('class="msg"') == 1 and ultima.count('class="card kpi"') == 4
    for cifra in ('4 capas', '7 de 7 IGUAL', '0,0', 'v6 → v1 → v6', '¿Preguntas?'):
        assert cifra in ultima, cifra


# ----------------------------------------------------------------------------------------------------------------------
# Capturas
# ----------------------------------------------------------------------------------------------------------------------
def test_las_tres_capturas_existen_salen_una_vez_y_ninguna_esta_pendiente(html):
    assert sorted(G.CAPTURAS) == ['bq-01-paridad.webp', 'bq-02-tope.webp', 'bq-03-borrado.webp']
    assert G.CAPTURAS_PENDIENTES == [] and 'Captura pendiente' not in html and 'class="pend"' not in html
    cuerpo = ' '.join(c for _, c in secciones(html))
    for nombre, alt in G.CAPTURAS.items():
        ruta = AQUI / 'img' / nombre
        assert ruta.is_file() and ruta.stat().st_size > 500, nombre
        assert f'img/{nombre}' in html
        assert len(alt) > 60 and cuerpo.count(f'data-img="{nombre}"') == 1, nombre
    assert re.findall(r'img/([\w.-]+)', html).__len__() >= 3
    for ruta in re.findall(r'(?:src|data-src)="(img/[^"]+)"', html):
        assert (AQUI / ruta).is_file(), ruta


def test_el_rotulo_de_cada_captura_dice_lo_que_muestra():
    """Lo que dice el rótulo tiene que ser lo que el recorte contiene (cifras y palabras de la captura original)."""
    a1, a2, a3 = (G.CAPTURAS[n] for n in ('bq-01-paridad.webp', 'bq-02-tope.webp', 'bq-03-borrado.webp'))
    for clave in ('1430', '22117', '3077', 'motor=bigquery IGUAL', 'siete'):
        assert clave in a1, clave
    assert 'master_clientes' not in a1, 'el recorte no enseña la línea de master_clientes: no puede decir que sí'
    for clave in ('12369', 'con tope de 1 byte', 'Query exceeded limit for bytes billed: 1. 20971520 or higher required.',
                  'RESULTADO: LOS DOS CONECTORES RESPONDEN LO MISMO'):
        assert clave in a2, clave
    assert 'dataset borrado: curso_master_prueba | quedan: []' in a3
    assert all('recorte' in a for a in (a1, a2, a3))
    # los números del rótulo 1 son los de las tablas de los notebooks (150/1430/22117/3077)
    s = salidas('00')
    for t in ('1430', '22117', '3077'):
        assert t in s


def test_la_captura_del_tope_no_afirma_que_consulta_se_uso(html):
    t = todo_el_texto(html)
    assert 'no enseña qué consulta se usó' in t and 'top_productos' in t
    assert 'con n=7' in t or 'n=7' in t


def test_las_imagenes_son_recortes_legibles():
    from PIL import Image
    for nombre in G.CAPTURAS:
        with Image.open(AQUI / 'img' / nombre) as im:
            assert im.format == 'WEBP' and im.width >= 300 and im.height >= 15, (nombre, im.size)


# ----------------------------------------------------------------------------------------------------------------------
# Órdenes copiables
# ----------------------------------------------------------------------------------------------------------------------
def test_cada_orden_tiene_su_boton_de_copiar(html):
    pegables = [htmllib.unescape(x) for x in re.findall(r'data-t="([^"]*)"', html)]
    assert len(pegables) >= 12
    for orden in ('gcloud auth application-default login', 'gcloud config set project TU_PROYECTO', 'export GCP_PROJECT=TU_PROYECTO',
                  'set GCP_PROJECT=TU_PROYECTO', 'python -m ia_mlops.alias_modelo promover --version 1', 'python -m ia_mlops.alias_modelo volver'):
        assert orden in pegables, orden
    # cada línea de las terminales tiene su botón y no hay botón sin texto
    assert html.count('class="tln"><span class="ps">$</span>') >= 6
    assert all(p.strip() for p in pegables)


def test_las_ordenes_de_bigquery_son_las_del_notebook_00():
    md = src('00', 6)
    for orden in ('gcloud auth application-default login', 'gcloud config set project TU_PROYECTO', 'export GCP_PROJECT=TU_PROYECTO',
                  'set GCP_PROJECT=TU_PROYECTO'):
        assert orden in md, orden


def test_las_ordenes_de_rollback_son_las_del_modulo_que_usa_el_notebook(html):
    assert 'from ia_mlops import alias_modelo as A' in fuentes('02') and 'A.promover(' in fuentes('02') and 'A.volver(' in fuentes('02')
    raiz = SESION.parents[1]
    proyecto = raiz / '04-Proyecto-Base' / 'ia_mlops' / 'alias_modelo.py'
    if proyecto.exists():
        t = leer(proyecto)
        assert "add_parser('promover'" in t and "add_parser('volver'" in t and "'--version'" in t


def test_el_json_de_vscode_une_los_dos_de_los_notebooks_y_se_copia(html):
    a = json.loads(re.search(r'```json\n(.*?)```', src('01', 24), re.S).group(1))['servers']
    b = json.loads(re.search(r'```json\n(.*?)```', src('02', 22), re.S).group(1))['servers']
    copiables = [htmllib.unescape(x) for x in re.findall(r'data-t="([^"]*)"', html)]
    unido = next(json.loads(c) for c in copiables if c.lstrip().startswith('{') and '"servers"' in c)
    assert unido == {'servers': {**a, **b}}
    assert set(unido['servers']) == {'datos-master', 'modelo-retencion'}


# ----------------------------------------------------------------------------------------------------------------------
# Lo que se enseña está en los notebooks
# ----------------------------------------------------------------------------------------------------------------------
def test_cada_linea_de_cada_salida_guardada_esta_en_las_salidas_de_los_notebooks(html):
    todas = '\n'.join(salidas(n) for n in ('00', '01', '02'))
    cajas = re.findall(r'<div class="realbox"><div class="rk">(.*?)</div><pre>(.*?)</pre></div>', html, re.S)
    assert len(cajas) >= 9
    for rk, pre in cajas:
        for linea in htmllib.unescape(pre).split('\n'):
            if linea.strip():
                assert linea.rstrip() in todas, f'«{linea}» (en «{htmllib.unescape(rk)}») no sale en las salidas de los notebooks'


def test_cada_linea_de_codigo_enseñada_esta_en_el_codigo_de_los_notebooks(html):
    todo = '\n'.join(sin_comentario(l) for n in ('01', '02') for l in fuentes(n).split('\n'))
    bloques = re.findall(r'<pre class="src">(.*?)</pre>', html, re.S)
    assert len(bloques) >= 6
    for b in bloques:
        texto = htmllib.unescape(b)
        if texto.lstrip().startswith('{') and '"servers"' in texto:
            continue                         # el JSON unido se comprueba aparte
        for linea in texto.split('\n'):
            if linea.strip():
                assert sin_comentario(linea) in todo, f'«{linea.strip()}» no está en el código de los notebooks'


def test_los_servidores_de_fuentes_son_los_del_notebook():
    for nb, celda, arch in (('01', 3, 'mcp_datos.py'), ('02', 5, 'mcp_modelo.py')):
        codigo = src(nb, celda).split('\n', 1)[1].strip()
        ref = leer(AQUI / 'fuentes' / arch).replace('\r\n', '\n').strip()
        assert codigo == ref, arch


def test_la_tabla_de_ataques_sale_de_la_salida_y_son_ocho(html):
    out = salidas('01')
    rechazos = re.findall(r'→ RECHAZADA: (.*)', out)
    assert len(rechazos) == 8
    ataques = re.search(r'ATAQUES = (\{.*?\n\})', src('01', 11), re.S).group(1)
    assert ataques.count("':") == 8 or len(re.findall(r"^\s+'[^']+':", ataques, re.M)) == 8
    t = todo_el_texto(html)
    for r in rechazos:
        assert r.split('. Tablas:')[0] in t, r
    assert 'Ocho ataques' in t and 'los ocho los frena' in t
    assert 'SELECT * de 22 117 líneas → devuelve 50 filas (truncado: True)' in out and '22 117' in t and '50 filas' in t


def test_cifras_del_notebook_00(html):
    s = salidas('00')
    t = todo_el_texto(html)
    for n in ('150', '1430', '22117', '3077', '148', '6 versiones', 'mcp                      1.30.0', 'TODO LISTO'):
        assert n in s, n
    for esperado in ('150 clientes', '22 117', '3077', '148', '6 versiones', '1.30.0', '0,6982', '0,7471'):
        assert esperado in t, esperado
    assert len(re.findall(r'valid_auc 0\.6982 · test_auc 0\.7471', s)) >= 6


def test_las_siete_herramientas_de_datos_y_las_cuatro_del_modelo(html):
    d = [l[2:] for l in salidas('01').split('\n') if l.startswith('• ')]
    m = [l[2:] for l in salidas('02').split('\n') if l.startswith('• ')]
    assert d == ['listar_tablas', 'describir_tabla', 'resumen_cliente', 'ultimas_facturas', 'ventas_por_pais', 'top_productos', 'consulta_sql']
    assert m == ['predecir_cliente', 'predecir_variables', 'por_que', 'modelo_en_uso']
    t = todo_el_texto(html)
    for h in d + m:
        assert h in t, h


def test_cifras_de_las_siete_llamadas_sqlite(html):
    out = salidas('01')
    t = todo_el_texto(html).replace('\u202f', ' ')
    for texto in ('"facturas": 3', '"cancelaciones": 0', '"monto_ventas": 1511.15'):
        assert texto in out
    for cifra in ('1511,15', '183,35', '1259,48', '344 244,74', '18 857,36', '10 780,8', '2720', '2712', '2244', '528576', '522773'):
        assert cifra in t, cifra
    for crudo in ('344244.74', '18857.36', '10780.8', '183.35', '1259.48', '528576', '522773'):
        assert crudo in out, crudo
    assert re.search(r'United Kingdom\s*\*{0,2}\s*135', t) and '"clientes": 135' in out


def test_paridad_del_modelo_12_clientes_diferencia_cero(html):
    out = salidas('02')
    filas = re.findall(r'^\s+(\d{5})\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)$', out, re.M)
    assert len(filas) == 12 and all(a == b and float(d) == 0.0 for _, a, b, d in filas)
    assert 'la diferencia máxima es 0.0' in out
    t = todo_el_texto(html)
    assert '12 clientes' in t and 'diferencia máxima 0,0' in t
    for cid, a, _, _ in filas:
        assert f'{cid}' in t and a in t, cid


def test_cliente_12369_y_por_que(html):
    out = salidas('02')
    for x in ('"probabilidad": 0.3035', '"tramo": "baja"', '"version_modelo": 6', '"corte_de_las_variables": "2011-12-10"',
              'intercepto +0.225  logit total -0.831  →  probabilidad 0.3035', 'frecuencia_180d    valor 0        peso -1.339',
              'recencia_dias      valor 413      peso +0.583'):
        assert x in out, x
    t = todo_el_texto(html)
    for x in ('0,3035', '0,225', '0,831', '1,339', '0,583', '413 días', 'v6', 'baja'):
        assert x in t, x


def test_tabla_y_si_con_la_sorpresa(html):
    out = salidas('02')
    filas = re.findall(r'^\d\s+(\d+)\s+([\d.]+)\s+(\w+)$', out, re.M)
    assert [f[0] for f in filas] == ['5', '35', '90', '180', '365']
    probs = [float(f[1]) for f in filas]
    assert probs == sorted(probs) and probs[0] == 0.7533 and probs[-1] == 0.8965       # SUBE con la recencia
    t = todo_el_texto(html)
    for _, p, _ in filas:
        assert coma(p) in t, p
    assert 'SUBE' in t and 'no es una relación causal' in t and 'no ha investigado por qué ocurre' in t
    assert 'Con solo una variable: 0.2395' in out and '0.2395' in t
    assert '0,8279' in t and '"recencia_dias": 35' in leer(SESION.parents[1] / '04-Proyecto-Base' / 'tests' / 'datos' / 'cliente_ejemplo.json').replace('\r', '') if (SESION.parents[1] / '04-Proyecto-Base' / 'tests' / 'datos' / 'cliente_ejemplo.json').exists() else True


def test_rollback_v6_v1_v6_sin_reiniciar_y_misma_probabilidad(html):
    out = salidas('02')
    assert '1. el MCP responde con la v6: probabilidad 0.3035' in out
    assert '2. promovemos @champion a la v1, SIN reiniciar el MCP → responde la v1: probabilidad 0.3035' in out
    assert '3. rollback (volver) → responde la v6: probabilidad 0.3035' in out
    t = todo_el_texto(html)
    assert 'v6 → v1 → v6' in t and 'sin reiniciar' in t.lower() and 'mismos datos' in t
    assert 'no una mejora' in t


def test_errores_del_modelo_salen_de_la_salida(html):
    out = salidas('02')
    for x in ('El cliente 1 no está en fs_produccion', 'Variables que el modelo no conoce', '«frecuencia» debe ser un número, no «muchas».'):
        assert x in out and x.split('.')[0] in todo_el_texto(html), x


# ----------------------------------------------------------------------------------------------------------------------
# BigQuery: lo probado, lo no probado
# ----------------------------------------------------------------------------------------------------------------------
def test_el_notebook_01_se_ejecuto_sin_bigquery_y_la_presentacion_lo_dice(html):
    out = salidas('01')
    assert 'BigQuery SALTADO' in out and out.count('saltada') >= 3 and 'Nada que borrar' in out
    t = todo_el_texto(html)
    assert 'sin BigQuery' in t and 'saltada' in t and 'BigQuery SALTADO' in t
    assert 'no el notebook en Jupyter' in t and 'script' in t
    assert G.FECHA_BQ == '26/11/2026' and '26/11/2026' in t and 'Cloud Shell' in t


def test_tope_de_bytes_y_nota_de_la_cache_coinciden_con_el_notebook(html):
    md = src('01', 20)
    assert '20 971 520' in md and 'caché' in md and 'top_productos' in md and 'n=7' in md and 'no se factura' in md
    t = todo_el_texto(html)
    for x in ('20 971 520', 'caché', 'no se factura', 'n=7', '1 byte', 'cobra por mínimos'):
        assert x in t, x
    assert 'maximum_bytes_billed' in fuentes('01') and 'MCP_BQ_MAX_BYTES' in fuentes('01') and '100_000_000' in fuentes('01')


def test_aviso_de_no_usar_el_proyecto_del_trabajo_y_borrar_el_dataset(html):
    md = src('00', 6)
    assert 'No uses el proyecto de tu trabajo' in md and 'curso_master' in md
    t = todo_el_texto(html)
    assert 'nunca el del trabajo' in t and 'curso_master' in t and 'es tu cuenta' in t
    assert 'delete_dataset' in fuentes('01') and 'delete_contents=True' in fuentes('01')
    assert 'dataset temporal' in t


# ----------------------------------------------------------------------------------------------------------------------
# Honestidad: «sin verificar» en su sitio
# ----------------------------------------------------------------------------------------------------------------------
def test_sin_verificar_solo_donde_toca(html):
    permitidas = {'Portada', 'BigQuery: preparar el proyecto', 'Por qué sale ese número', 'Dos servidores juntos', 'Qué quedó sin verificar'}
    con = set()
    for attrs, cuerpo in secciones(html):
        if 'sin verificar' in sin_etiquetas(cuerpo).lower():
            con.add(titulo(attrs))
        if 'data-img=' in cuerpo:
            assert 'sin verificar' not in sin_etiquetas(cuerpo).lower(), f'«sin verificar» en una diapositiva con captura real: {titulo(attrs)}'
    assert con <= permitidas, con - permitidas
    assert {'Portada', 'Dos servidores juntos', 'Qué quedó sin verificar'} <= con


def test_vscode_copilot_y_codespace_siempre_con_sin_verificar(html):
    for attrs, cuerpo in secciones(html):
        t = sin_etiquetas(cuerpo)
        if re.search(r'Copilot|Codespace', t):
            assert 'sin verificar' in t.lower(), f'«{titulo(attrs)}» habla de Copilot o Codespace sin decir que está sin verificar'
    t = todo_el_texto(html)
    assert 'nunca se conectó a VS Code ni a Copilot' in t and 'ejecutar los notebooks en un Codespace' in t


def test_limites_dichos(html):
    t = todo_el_texto(html)
    for x in ('expresión regular', 'no es un analizador', 'Ningún LLM real', 'no son modelos distintos', 'no se ha investigado',
              'los mismos datos', 'ejercicio 1', 'MCP_BACKEND'):
        assert x in t or x.lower() in t.lower(), x
    assert 'VOLVER A COMPRAR' in t and 'no es un «riesgo de abandono»' in t
    assert 'regla de negocio' in t


def test_el_servidor_de_datos_no_da_nombres_ni_el_modelo_es_riesgo_de_abandono(html):
    t = todo_el_texto(html).lower()
    assert 'riesgo de abandono' in t and 'alta = buena noticia' in t


# ----------------------------------------------------------------------------------------------------------------------
# Higiene
# ----------------------------------------------------------------------------------------------------------------------
def test_utf8_con_tildes_y_sin_mojibake(html):
    for mal in ('Ã', 'â€', 'Â', '\ufffd', 'Ã³'):
        assert mal not in html, repr(mal)
    t = sin_etiquetas(re.sub(r'<span class="mono">.*?</span>', ' ', re.sub(r'<pre[^>]*>.*?</pre>', ' ', ' '.join(c for _, c in secciones(html)), flags=re.S), flags=re.S))
    for palabra in ('producción', 'versión', 'defensa', 'conexión', 'herramientas', 'descripción', 'probabilidad', 'qué', 'más'):
        assert palabra in t.lower(), palabra
    for mal in (' esta ordenes', 'ejecucion', 'validacion de', 'descripcion', ' mas probable', 'version del modelo'):
        assert not re.search(r'(?<!\w)' + re.escape(mal.strip()) + r'(?!\w)', t.lower()), mal


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
    assert not re.search(r'[\w.]+@[\w-]+\.(com|es|org)', texto)
    assert not re.search(r'(token|password|contraseña)\s*[:=]\s*\S{6,}', texto, re.I)
    assert not re.search(r'ghp_|github_pat_', texto)
    assert 'project-curso-ml-ia' not in texto and 'cursomlops' not in texto


def test_el_generador_comprueba_su_propia_salida(tmp_path):
    import subprocess
    import sys
    r = subprocess.run([sys.executable, str(AQUI / 'generar.py'), '--comprobar'], capture_output=True, text=True, encoding='utf-8')
    assert r.returncode == 0 and 'al día' in r.stdout, r.stdout + r.stderr
