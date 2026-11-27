"""Pruebas de las diapositivas de la interfaz web (ui/index_slides.html), sin navegador y sin arrancar la aplicación.

Qué vigilan: que index_slides.html está al día con generar_slides.py; la estructura (entre 22 y 26 diapositivas con título, parte, minutos y
notas; 45-60 min); el enlace de regreso al índice de S5; que el visor es el de los otros extras (CSS y JS copiados) y no hay :hover; que cada
orden copiable existe de verdad en README.md, app.py, app.js o los README del extra; que cada captura existe, es webp, sale una vez y tiene su
rótulo y su «cómo se produce»; que los 8 ataques y las 11 herramientas que se enseñan son los reales; que «sin verificar» está donde toca;
que no hay mojibake, CDN, rutas personales ni secretos; y que cada diapositiva lleva una sola idea.
"""
import html as htmllib
import importlib.util
import re
from pathlib import Path

import pytest

UI = Path(__file__).resolve().parents[1]
EXTRA = UI.parent
SESION = EXTRA.parent


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


G = _cargar('generar_slides_ui', UI / 'generar_slides.py')
PADRE = _cargar('generar_extra_mcp_padre', EXTRA / 'generar.py')


def leer(ruta):
    return Path(ruta).read_text(encoding='utf-8')


@pytest.fixture(scope='module')
def html():
    return leer(UI / 'index_slides.html')


@pytest.fixture(scope='module')
def fuentes():
    """Los textos contra los que se comprueban las órdenes y los datos que se enseñan."""
    trozos = [leer(UI / 'README.md'), leer(UI / 'app.py'), leer(UI / 'estatico' / 'app.js'), leer(EXTRA / 'README.md'), leer(EXTRA / 'requisitos-extra-mcp.txt')]
    return '\n'.join(trozos)


def secciones(texto):
    return re.findall(r'<section class="slide[^"]*"([^>]*)>(.*?)</section>', texto, re.S)


def sin_etiquetas(texto):
    return re.sub(r'\s+', ' ', htmllib.unescape(re.sub(r'<[^>]+>', ' ', texto)))


def atributo(attrs, nombre):
    return htmllib.unescape(re.search(rf'{nombre}="([^"]*)"', attrs).group(1))


# ---- estructura ------------------------------------------------------------------------------------------------------------------
def test_esta_al_dia_con_el_generador(html):
    assert G.html_completo() == html, 'index_slides.html está desfasado: ejecuta python generar_slides.py'


def test_numero_de_diapositivas_minutos_y_notas(html):
    s = secciones(html)
    assert 22 <= len(s) <= 26, len(s)
    titulos = [atributo(a, 'data-title') for a, _ in s]
    assert len(set(titulos)) == len(titulos), 'títulos repetidos'
    for a, cuerpo in s:
        assert atributo(a, 'data-part') in G.PARTES
        assert int(atributo(a, 'data-min')) >= 1
        notas = atributo(a, 'data-notes')
        assert len(notas) >= 200, f'notas del profesor demasiado cortas en «{atributo(a, "data-title")}»'
        assert '<h1>' in cuerpo and 'class="kick"' in cuerpo
    total = sum(int(atributo(a, 'data-min')) for a, _ in s)
    assert 45 <= total <= 60, total
    assert [atributo(a, 'data-part') for a, _ in s] == sorted(atributo(a, 'data-part') for a, _ in s), 'las partes deben ir en orden'


def test_cada_diapositiva_con_cifras_o_capturas_tiene_fuente(html):
    for a, cuerpo in secciones(html):
        if atributo(a, 'data-title') == 'Portada':
            continue
        assert 'class="fuente"' in cuerpo, f'sin «Fuente:» en «{atributo(a, "data-title")}»'


def test_una_idea_por_diapositiva(html):
    for a, cuerpo in secciones(html):
        t = atributo(a, 'data-title')
        h1 = sin_etiquetas(re.search(r'<h1>(.*?)</h1>', cuerpo, re.S).group(1))
        assert len(h1) <= 150, f'título largo en «{t}»'
        sin_notas = re.sub(r'data-notes="[^"]*"', '', cuerpo)
        palabras = len(sin_etiquetas(sin_notas).split())
        assert palabras <= 400, f'«{t}» tiene {palabras} palabras'


# ---- visor y enlace de regreso ---------------------------------------------------------------------------------------------------
def test_enlace_de_regreso_al_indice_de_la_sesion(html):
    assert 'id="bhome" href="../../index.html"' in html
    assert (UI / '..' / '..' / 'index.html').resolve().is_file(), 'el índice de S5 no existe en esa ruta'
    assert 'index_slides.html' in leer(UI / 'README.md'), 'el README de ui no enlaza a las diapositivas'


def test_visor_igual_que_el_de_los_otros_extras(html):
    assert G.CSS.startswith(PADRE.CSS), 'el CSS del visor ya no es el del extra'
    assert G.JS == PADRE.JS.replace('ML e IA · S5 · Extra: MCP en notebooks', 'ML e IA · S5 · Interfaz web MCP y LLM')
    for pieza in ['id="bnotes"', 'id="zoombox"', 'cpall', "k==='s'", "k==='Escape'", 'class="lupa"', 'id="clockref"']:
        assert pieza in html, pieza


def test_fondo_blanco_y_nada_se_mueve_con_el_raton(html):
    assert '--fondo:#ffffff' in html
    css = re.search(r'<style>(.*?)</style>', html, re.S).group(1)
    assert ':hover' not in css and 'hover:' not in css.replace('hover:none', '')
    assert '@media (hover' not in css


# ---- órdenes copiables -----------------------------------------------------------------------------------------------------------
def test_cada_orden_copiable_existe_en_las_fuentes(html, fuentes):
    G.html_completo()
    copiables = {htmllib.unescape(t) for t in re.findall(r'data-t="([^"]*)"', html)}
    assert copiables, 'no hay botones de copiar'
    assert copiables == set(G.ORDENES), copiables ^ set(G.ORDENES)
    for texto, trozos in G.ORDENES.items():
        for trozo in trozos:
            assert trozo in fuentes, f'«{trozo}» (de «{texto}») no está en README.md, app.py, app.js ni en el README del extra'


def test_las_ordenes_clave_son_las_del_readme(html):
    copiables = {htmllib.unescape(t) for t in re.findall(r'data-t="([^"]*)"', html)}
    readme = leer(UI / 'README.md')
    assert 'python -m uvicorn app:app --port 8095' in copiables and 'python -m uvicorn app:app --port 8095' in readme
    assert 'cd 01-Sesiones\\S5-MLOps-y-Operacion\\extra-mcp-notebooks\\ui' in copiables
    assert 'export CURSO_UI_HOSTS="*.app.github.dev"' in copiables and 'export CURSO_UI_HOSTS="*.app.github.dev"' in readme
    assert 'python -m pytest ui/pruebas -q' in copiables and 'python -m pytest ui/pruebas -q' in readme
    assert 'ollama serve' in copiables and 'ollama pull qwen2.5:0.5b' in copiables
    # los valores por defecto de la tabla de variables son los de app.py
    app = leer(UI / 'app.py')
    assert "LLM_URL_DEFECTO = 'http://127.0.0.1:11434/v1'" in app and "LLM_MODELO_DEFECTO = 'qwen2.5:0.5b'" in app
    assert "'CURSO_UI_PUERTO', '8095'" in app and "'BQ_DATASET') or 'curso_master'" in app


def test_los_8_ataques_y_las_11_herramientas_son_los_reales(html, fuentes):
    js = leer(UI / 'estatico' / 'app.js')
    for nombre, sql, _ in G.ATAQUES:
        assert f"'{nombre}'" in js and sql in js, nombre
    assert len(G.ATAQUES) == 8
    codigo = leer(EXTRA / 'fuentes' / 'mcp_datos.py') + leer(EXTRA / 'fuentes' / 'mcp_modelo.py')
    herramientas = ['listar_tablas', 'describir_tabla', 'resumen_cliente', 'ultimas_facturas', 'ventas_por_pais', 'top_productos', 'consulta_sql',
                    'predecir_cliente', 'predecir_variables', 'por_que', 'modelo_en_uso']
    for h in herramientas:
        assert re.search(rf'def {h}\(', codigo), h
        assert h in html
    assert 'mcp-datos-master' in codigo and 'mcp-modelo-retencion' in codigo
    # cifras que vienen del modelo registrado: las mismas que el otro deck del extra
    otro = leer(EXTRA / 'index.html')
    assert '0,6982' in otro and '0,7471' in otro and '0,6982' in html and '0,7471' in html


# ---- capturas --------------------------------------------------------------------------------------------------------------------
def test_cada_captura_existe_sale_una_vez_y_tiene_rotulo(html):
    assert 'Captura pendiente' not in html, 'hay capturas pendientes'
    rotulos = [r for r, _ in G.CAPTURAS.values()]
    assert len(set(rotulos)) == len(rotulos), 'un rótulo = una imagen: hay rótulos repetidos'
    en_disco = {p.name for p in (UI / 'img').iterdir()}
    assert en_disco == set(G.CAPTURAS), en_disco ^ set(G.CAPTURAS)
    for nombre, (rotulo, como) in G.CAPTURAS.items():
        ruta = UI / 'img' / nombre
        cab = ruta.read_bytes()[:12]
        assert cab[:4] == b'RIFF' and cab[8:12] == b'WEBP', f'{nombre} no es webp'
        assert ruta.stat().st_size > 5000
        assert html.count(f'data-img="{nombre}"') == 1, f'{nombre} debe salir exactamente una vez'
        assert html.count(f'<img src="img/{nombre}"') == 1
        assert len(rotulo) > 60 and len(como) > 30
        assert f'alt="{htmllib.escape(rotulo, quote=True)}"' in html
        assert 'Cómo se produce:' in html
    assert html.count('Cómo se produce:') == len(G.CAPTURAS)


def test_las_capturas_nombran_lo_que_muestran(html):
    """Los rótulos que dicen una cifra o un texto de la interfaz deben coincidir con lo que dicen las diapositivas de al lado."""
    r = {k: v[0] for k, v in G.CAPTURAS.items()}
    assert '30,3 %' in r['ui-04-cliente.webp'] and '18,4 %' in r['ui-06-ysi.webp'] and '-11,9' in r['ui-06-ysi.webp']
    assert 'sin ningún chip' in r['ui-07-pregunta-sin-herramientas.webp']
    assert '0.3035' in r['ui-10-pregunta-predecir.webp'] and '164 ms' in r['ui-10-pregunta-predecir.webp']
    assert '1140 facturas' in r['ui-08-pregunta-ventas.webp']
    assert 'capa 2' in r['ui-12-ataque-update.webp']
    assert 'Sin conexión' in r['ui-16-lote.webp']
    assert '390' in r['ui-17-movil.webp']
    # ... y las diapositivas repiten esas mismas cifras
    texto = sin_etiquetas(html)
    for cifra in ['30,3 %', '18,4 %', '11,9 puntos', '0,3035', '164 ms', '1140 facturas', '133 clientes']:
        assert cifra in texto or cifra.replace(',', '.') in texto, cifra


# ---- honestidad: «sin verificar» ---------------------------------------------------------------------------------------------------
def test_sin_verificar_solo_donde_toca(html):
    con = set()
    for a, cuerpo in secciones(html):
        t = atributo(a, 'data-title')
        if re.search(r'sin verificar', sin_etiquetas(cuerpo) + ' ' + atributo(a, 'data-notes'), re.I):
            con.add(t)
    assert con <= G.SIN_VERIFICAR_OK, f'«sin verificar» fuera de sitio: {con - G.SIN_VERIFICAR_OK}'
    for t in ['Arrancar en Codespace o Linux', 'Qué no está verificado', 'Pregunta: un LLM pequeño sin herramientas', 'Pestaña Lote', 'Variables de entorno']:
        assert t in con, f'falta «sin verificar» en «{t}»'
    # lo verificado (capturas reales, 8 ataques, promover y volver) no lleva la etiqueta
    for t in ['Promover la v6', 'Los 8 ataques SQL y la capa que los frena', 'Modelo: promover otra versión y volver', 'Pestaña Cliente', 'Cómo se prueba']:
        assert t not in con, t


def test_cifra_de_pruebas_real(html):
    assert G.PRUEBAS_VERDES.isdigit(), 'falta la cifra real de pruebas en verde (PRUEBAS_VERDES)'
    assert int(G.PRUEBAS_VERDES) >= 57
    assert html.count(f'{G.PRUEBAS_VERDES} pruebas') >= 2


# ---- limpieza --------------------------------------------------------------------------------------------------------------------
def test_sin_mojibake_cdn_rutas_personales_ni_secretos(html):
    for malo in ['Ã', 'Â', 'â€', '\ufffd', 'ðŸ', '&amp;amp;']:
        assert malo not in html, malo
    assert not re.search(r'https?://(?!127\.0\.0\.1|localhost)', html), 'enlace a Internet'
    assert not re.search(r'<script[^>]+src=|<link[^>]+href=|@import|cdn\.|cdnjs|jsdelivr|unpkg|googleapis', html, re.I), 'recurso externo'
    assert not re.search(r'C:\\Users|BK70827|/home/|AKIA|password\s*=|token\s*=', html, re.I)
    assert html.count('data-notes="') == len(secciones(html))
    assert '\r' not in html
    for palabra, correcta in [('pestana', 'pestaña'), ('informacion', 'información'), ('configuracion', 'configuración')]:
        assert palabra not in html.lower().replace('pestana_', ''), palabra
