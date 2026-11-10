"""Genera los PDF de las sesiones en `pdfs/` a partir de `contenido_pdfs.py`.

Uso (desde la raíz del repositorio):
    python 00-Planificacion/pdfs/generar_pdfs.py                 # todo
    python 00-Planificacion/pdfs/generar_pdfs.py --sesion S1     # una sesión
    python 00-Planificacion/pdfs/generar_pdfs.py --solo 01-presentacion-s1.pdf
    python 00-Planificacion/pdfs/generar_pdfs.py --comprobar     # revisa los PDF existentes, sin generar

Necesita: Python con `playwright` y `pypdf` y `pygments`; Google Chrome; `pandoc`.
    pip install playwright pypdf pygments
Chrome: se usa el de la variable PDF_CHROME, o `google-chrome`/`chromium` del PATH, o el Chrome instalado
(playwright `channel="chrome"`).

Los PDF se sobrescriben: no los edites a mano. Cámbialos en la fuente y vuelve a generar.

Cómo se hace cada tipo:
 - Presentación: se abre el HTML en 1280 × 720 y se va diapositiva por diapositiva con el índice y el teclado (así
   se ejecutan los contadores y las barras animadas y se revelan todos los pasos), se pulsan las demos de terminal,
   se espera a que acaben las animaciones y se imprime solo esa diapositiva. Después se unen las páginas y se
   añade un marcador por diapositiva. Los únicos retoques son los de CSS_PRESENTACION y RETOQUES_TEXTO (frases que
   mandan pulsar un botón que en el PDF no existe).
 - Documento (Markdown): pandoc (GFM) → HTML con el estilo de `estilo-documento.css` → A4 con pie de página.
"""
import argparse
import html
import io
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(AQUI))
import contenido_pdfs as C  # noqa: E402

ANCHO_PRESENTACION, ALTO_PRESENTACION = 1280, 720
PALABRA_INTERNA = 'guia' + 'burros'  # nombre interno: no debe aparecer en ningún PDF (en dos trozos para no escribirla aquí)

# Se aplica solo al imprimir las presentaciones (con RETOQUES_TEXTO, los únicos cambios sobre ellas, y solo en el PDF):
#  - una diapositiva visible a la vez;
#  - sin botones de control (no hacen nada en papel);
#  - el título con degradado (background-clip:text) se pinta como un rectángulo en algunos visores de PDF:
#    se sustituye por un color liso.
CSS_PRESENTACION = """
@media print{
  .slide:not(.pdf-solo){display:none!important}
  button.btn,.cmdbtns,.poll-nav,#bprev,#bnext,.cp,.cpall,.hecho-btn{display:none!important}
  h1{background:none!important;-webkit-text-fill-color:#eef7ff!important;color:#eef7ff!important}
  h1 .tag{-webkit-text-fill-color:initial!important}
  *{animation:none!important}
}
"""

# Frases que mandan pulsar o hacer clic en algo que en el PDF no existe. Se sustituyen solo en el PDF (en HTML, la fuente
# no se toca). Cada par es (HTML de antes, HTML de después); se aplica a los <p>, <li> y <span class="small"> de cada diapositiva ya mostrada.
RETOQUES_TEXTO = [
    ('; pulsa la opción para contarla', ''),
    (' Haz clic en cada nivel.', ''),
    (' Haz clic en una capa o pulsa ▶ para el recorrido completo.', ''),
    (' Hacer clic en una capa.', ''),
    ('Haz clic en un tramo para saltar a ese bloque. ', ''),
    ('El contador solo arranca al pulsar «Iniciar pausa».', 'Pausa de 15 minutos.'),
    ('Clic: ✓ · 2 clics: ✗ · 3: pendiente', '✓ correcto · ✗ fallo'),
    ('Se guarda en este navegador.', 'Lista en el checklist.'),
    ('Pulsa <b>⧉</b> junto a cada línea para copiarla y pégala con Ctrl+V en la terminal que indica la diapositiva. '
     '<b>← →</b> navegan · <b>C</b> copia todo el bloque · <b>O</b> índice · <b>F</b> pantalla completa. ',
     'Copia cada línea y pégala en la terminal que indica la diapositiva. '),
    ('Cópialas una a una (⧉)', 'Cópialas una a una'),
    ('Copia con <b>⧉</b> y pega con <b>Ctrl+V</b>', 'Copia cada línea y pégala con <b>Ctrl+V</b>'),
]

JS_RETOQUES = """
(pares) => {
  document.querySelectorAll('p, li, span.small').forEach(el => {
    let h = el.innerHTML;
    for (const [antes, despues] of pares) h = h.split(antes).join(despues);
    if (h !== el.innerHTML) el.innerHTML = h;
  });
}
"""

# Reescribe los enlaces relativos (que en el PDF apuntarían a file:///...) hacia el repositorio en GitHub.
JS_ENLACES = """
([raiz, repo, rama]) => {
  document.querySelectorAll('a[href]').forEach(a => {
    const h = a.getAttribute('href');
    if (/^(https?:|mailto:|#|javascript:)/i.test(h)) return;
    const u = new URL(h, location.href);
    if (u.protocol !== 'file:') return;
    const p = decodeURIComponent(u.pathname);
    if (!p.startsWith(raiz)) { a.removeAttribute('href'); return; }
    const rel = p.slice(raiz.length);
    a.setAttribute('href', repo + '/' + (rel.endsWith('/') ? 'tree/' : 'blob/') + rama + '/' + rel + u.hash);
  });
}
"""


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def esc(t):
    return html.escape(t, quote=True)


def ruta_pdf(sesion, elemento):
    return RAIZ / C.CARPETA_SALIDA / sesion['carpeta'] / C.GRUPOS[elemento['grupo']][1] / elemento['archivo']


def url_repo(ruta_repo, es_carpeta=False):
    modo = 'tree' if es_carpeta else 'blob'
    return f"{C.REPOSITORIO}/{modo}/{C.RAMA}/{ruta_repo}"


def elementos(filtro_sesion=None, filtro_archivo=None):
    for s in C.SESIONES:
        if filtro_sesion and s['id'].lower() != filtro_sesion.lower():
            continue
        for e in s['elementos']:
            if filtro_archivo and e['archivo'] != filtro_archivo:
                continue
            yield s, e


def buscar_chrome():
    """Devuelve (ruta, None) si hay un Chrome/Chromium localizable, o (None, 'chrome') para usar el canal de playwright."""
    ruta = os.environ.get('PDF_CHROME')
    if ruta:
        return ruta, None
    for nombre in ('google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser', 'chrome'):
        r = shutil.which(nombre)
        if r:
            return r, None
    return None, 'chrome'


def lanzar(p):
    ruta, canal = buscar_chrome()
    args = ['--no-sandbox'] if hasattr(os, 'geteuid') and os.geteuid() == 0 else []
    if ruta:
        return p.chromium.launch(executable_path=ruta, args=args)
    return p.chromium.launch(channel=canal, args=args)


# ---------------------------------------------------------------------------
# Presentaciones
# ---------------------------------------------------------------------------
INDICE_ACTIVA = "[...document.querySelectorAll('section.slide')].findIndex(s => s.classList.contains('active'))"


def mostrar_diapositiva(pagina, i, n):
    """Lleva la presentación a la diapositiva i con todos sus pasos revelados, como lo haría quien la presenta.

    Las presentaciones guardan su código en una función anónima, así que no se puede llamar a `go()` desde fuera:
    se abre la diapositiva desde el índice (O) y se avanza con la flecha derecha hasta pasar a la siguiente; entonces se
    vuelve atrás con la flecha izquierda, que deja la diapositiva con todos los pasos visibles y vuelve a ejecutar sus
    contadores y barras. En la última diapositiva basta con la tecla Fin.
    """
    abierta = pagina.evaluate(
        "(i) => { const b = document.querySelector('#idxgrid button[data-i=\"' + i + '\"]'); "
        "if (!b) return false; b.click(); return true; }", i)
    if not abierta:
        raise RuntimeError(f'no se pudo abrir la diapositiva {i + 1}: la presentación no tiene #idxgrid')
    pagina.wait_for_timeout(150)
    if pagina.evaluate(INDICE_ACTIVA) != i:
        raise RuntimeError(f'no se pudo abrir la diapositiva {i + 1}')
    if i == n - 1:
        pagina.keyboard.press('End')
        return
    for _ in range(60):
        pagina.keyboard.press('ArrowRight')
        if pagina.evaluate(INDICE_ACTIVA) != i:
            pagina.keyboard.press('ArrowLeft')
            break
    else:
        raise RuntimeError(f'la diapositiva {i + 1} tiene más de 60 pasos o no avanza')
    if pagina.evaluate(INDICE_ACTIVA) != i:
        raise RuntimeError(f'al volver a la diapositiva {i + 1} se llegó a otra')



def ejecutar_demo(pagina, i):
    """Si la diapositiva tiene un terminal con «▶ Ver demo», se ejecuta y se espera a que termine, para que en el PDF
    aparezca la salida de ejemplo que en pantalla solo se ve al pulsar el botón."""
    hay = pagina.evaluate(
        "(i) => { const b = document.querySelectorAll('section.slide')[i].querySelector('button.run'); "
        "if (!b) return false; b.click(); return true; }", i)
    if hay:
        pagina.wait_for_function(
            "(i) => { const b = document.querySelectorAll('section.slide')[i].querySelector('button.run'); "
            "return b && /Repetir/.test(b.textContent); }", arg=i, timeout=30000)


def generar_presentacion(navegador, sesion, e, destino):
    from pypdf import PdfReader, PdfWriter

    fuente = RAIZ / e['origen']
    espera = e.get('espera_ms', 1500)
    pagina = navegador.new_page(viewport={'width': ANCHO_PRESENTACION, 'height': ALTO_PRESENTACION})
    try:
        pagina.goto(fuente.as_uri(), wait_until='load')
        pagina.wait_for_timeout(800)
        pagina.add_style_tag(content=CSS_PRESENTACION)
        raiz_url = urlsplit(RAIZ.as_uri()).path.rstrip('/') + '/'
        pagina.evaluate(JS_ENLACES, [unquote(raiz_url), C.REPOSITORIO, C.RAMA])
        n = pagina.evaluate("document.querySelectorAll('section.slide').length")
        if n == 0:
            raise RuntimeError(f'{e["origen"]}: no se encontraron diapositivas (section.slide)')
        titulos = pagina.evaluate(
            "[...document.querySelectorAll('section.slide')].map(s => s.dataset.title || "
            "(s.querySelector('h1,h2')||{}).textContent || '')")
        escritor = PdfWriter()
        desbordan = []
        for i in range(n):
            mostrar_diapositiva(pagina, i, n)
            ejecutar_demo(pagina, i)
            pagina.evaluate(JS_RETOQUES, RETOQUES_TEXTO)
            pagina.evaluate(
                "(i) => document.querySelectorAll('section.slide').forEach((s, k) => s.classList.toggle('pdf-solo', k === i))", i)
            pagina.wait_for_timeout(espera)
            datos = pagina.pdf(width=f'{ANCHO_PRESENTACION}px', height=f'{ALTO_PRESENTACION}px',
                               print_background=True, margin={'top': '0', 'right': '0', 'bottom': '0', 'left': '0'})
            lector = PdfReader(io.BytesIO(datos))
            if len(lector.pages) != 1:
                desbordan.append((i + 1, len(lector.pages)))
            escritor.add_page(lector.pages[0])
        if desbordan:
            raise RuntimeError(f'{e["origen"]}: diapositivas que ocupan más de una página al imprimir: {desbordan}')
        for i, t in enumerate(titulos):
            limpio = ' '.join(t.split())
            escritor.add_outline_item(f'{i + 1}. {limpio}', i)
        poner_metadatos(escritor, sesion, e)
        escritor.page_mode = '/UseOutlines'
        destino.parent.mkdir(parents=True, exist_ok=True)
        with open(destino, 'wb') as f:
            escritor.write(f)
        return n
    finally:
        pagina.close()


# ---------------------------------------------------------------------------
# Documentos (Markdown)
# ---------------------------------------------------------------------------
RE_TAREA_NUMERADA = re.compile(r'^(\s*[-*+] \[[ xX]\] +)(\d+)([.)])(?= )', re.M)


def proteger_numeros_en_tareas(texto):
    """`- [ ] 1. texto`: pandoc lo lee como una lista numerada dentro de la casilla y la separa en dos líneas
    (GitHub no). Se escapa el punto (`1\\.`) para que el número siga siendo texto de la casilla."""
    return RE_TAREA_NUMERADA.sub(lambda m: f'{m.group(1)}{m.group(2)}\\{m.group(3)}', texto)


def pandoc_html(texto):
    texto = proteger_numeros_en_tareas(texto)
    if not shutil.which('pandoc'):
        raise RuntimeError('Falta pandoc (https://pandoc.org/installing.html)')
    r = subprocess.run(['pandoc', '-f', 'gfm', '-t', 'html5', '--no-highlight', '--wrap=none'],
                       input=texto.encode('utf-8'), capture_output=True, check=True)
    return r.stdout.decode('utf-8')


def resaltar(cuerpo):
    """Sintaxis coloreada en los bloques de código (pygments)."""
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import TextLexer, get_lexer_by_name
    from pygments.util import ClassNotFound

    formateador = HtmlFormatter(nowrap=True, classprefix='h-')

    def cambiar(m):
        lenguaje = m.group(1) or ''
        codigo = html.unescape(m.group(2))
        try:
            lexer = get_lexer_by_name(lenguaje) if lenguaje and lenguaje != 'text' else TextLexer()
        except ClassNotFound:
            lexer = TextLexer()
        resultado = highlight(codigo.rstrip('\n'), lexer, formateador).rstrip('\n')
        largo = ' larga' if codigo.count('\n') > 38 else ''
        return f'<pre class="codigo{largo}"><code>{resultado}</code></pre>'

    return re.sub(r'<pre(?: class="([^"]*)")?><code>(.*?)</code></pre>', cambiar, cuerpo, flags=re.S)


def estilo_resaltado():
    from pygments.formatter import Formatter  # noqa: F401
    from pygments.formatters import HtmlFormatter
    css = HtmlFormatter(style='tango', classprefix='h-').get_style_defs('pre.codigo')
    # No se usa el fondo ni el borde del estilo: ya los pone estilo-documento.css.
    return re.sub(r'pre\.codigo \{[^}]*\}', '', css)


def enlaces_al_repositorio(cuerpo, origen):
    """Los enlaces relativos entre archivos del repositorio se convierten en enlaces a GitHub (en papel o en PDF no existen las rutas)."""
    base = PurePosixPath(origen).parent

    def cambiar(m):
        h = html.unescape(m.group(1))
        if re.match(r'^(https?:|mailto:|#)', h, re.I):
            return m.group(0)
        partes = urlsplit(h)
        ruta = os.path.normpath((base / unquote(partes.path)).as_posix()).replace('\\', '/')
        es_carpeta = partes.path.endswith('/') or (RAIZ / ruta).is_dir()
        destino = url_repo(ruta, es_carpeta) + (f'#{partes.fragment}' if partes.fragment else '')
        return f'<a href="{esc(destino)}"'

    return re.sub(r'<a href="([^"]*)"', cambiar, cuerpo)


def pagina_documento(sesion, e):
    texto = (RAIZ / e['origen']).read_text(encoding='utf-8')
    cuerpo = pandoc_html(texto)
    cuerpo = resaltar(cuerpo)
    cuerpo = enlaces_al_repositorio(cuerpo, e['origen'])
    css = (AQUI / 'estilo-documento.css').read_text(encoding='utf-8') + '\n' + estilo_resaltado()
    grupo = C.GRUPOS[e['grupo']][0]
    cabecera = (f'<div class="cabecera"><div class="curso">{esc(C.CURSO)} · {esc(C.INSTITUCION)}</div>'
                f'<div class="sesion">{esc(sesion["id"])} · {esc(sesion["titulo"])} · {esc(grupo)}</div></div>')
    return (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>{esc(e["titulo"])}</title>'
            f'<style>{css}</style></head><body><main>{cabecera}{cuerpo}</main></body></html>')


def pie(sesion, e):
    estilo = ("font-family:Inter,'Segoe UI',Arial,sans-serif;font-size:7.4pt;color:#566677;width:100%;"
              "padding:0 17mm;display:flex;justify-content:space-between;-webkit-print-color-adjust:exact")
    return (f'<div style="{estilo}"><span>{esc(sesion["id"])} · {esc(e["titulo"])}</span>'
            f'<span>Página <span class="pageNumber"></span> de <span class="totalPages"></span></span></div>')


def generar_documento(navegador, sesion, e, destino):
    from pypdf import PdfReader, PdfWriter

    pagina = navegador.new_page()
    try:
        pagina.set_content(pagina_documento(sesion, e), wait_until='load')
        datos = pagina.pdf(format='A4', print_background=True, display_header_footer=True,
                           header_template='<span></span>', footer_template=pie(sesion, e),
                           margin={'top': '16mm', 'bottom': '17mm', 'left': '17mm', 'right': '17mm'})
    finally:
        pagina.close()
    lector = PdfReader(io.BytesIO(datos))
    escritor = PdfWriter(clone_from=lector)
    poner_metadatos(escritor, sesion, e)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with open(destino, 'wb') as f:
        escritor.write(f)
    return len(lector.pages)


def generar_pagina(navegador, sesion, e, destino):
    """Página HTML normal (no presentación): se imprime tal cual en A4, con sus colores de fondo."""
    from pypdf import PdfReader, PdfWriter

    pagina = navegador.new_page(viewport={'width': 900, 'height': 1200})
    try:
        pagina.goto((RAIZ / e['origen']).as_uri(), wait_until='load')
        pagina.wait_for_timeout(500)
        raiz_url = urlsplit(RAIZ.as_uri()).path.rstrip('/') + '/'
        pagina.evaluate(JS_ENLACES, [unquote(raiz_url), C.REPOSITORIO, C.RAMA])
        datos = pagina.pdf(format='A4', print_background=True,
                           margin={'top': '0', 'right': '0', 'bottom': '0', 'left': '0'})
    finally:
        pagina.close()
    lector = PdfReader(io.BytesIO(datos))
    escritor = PdfWriter(clone_from=lector)
    poner_metadatos(escritor, sesion, e)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with open(destino, 'wb') as f:
        escritor.write(f)
    return len(lector.pages)


def poner_metadatos(escritor, sesion, e):
    escritor.add_metadata({
        '/Title': f'{e["titulo"]} · {sesion["id"]}',
        '/Author': C.AUTOR,
        '/Subject': f'{C.CURSO} · {C.INSTITUCION}',
        '/Keywords': f'{sesion["id"]}, {C.CURSO}',
        '/Creator': 'generar_pdfs.py (Chrome)',
    })


# ---------------------------------------------------------------------------
# LEEME y comprobación
# ---------------------------------------------------------------------------
def info_pdf(ruta):
    from pypdf import PdfReader
    lector = PdfReader(str(ruta))
    caja = lector.pages[0].mediabox
    return {'paginas': len(lector.pages), 'ancho': float(caja.width), 'alto': float(caja.height),
            'bytes': ruta.stat().st_size}


def tamano_legible(n):
    return f'{n / 1_000_000:.1f} MB' if n >= 1_000_000 else f'{max(1, round(n / 1000))} KB'


def texto_leeme():
    lineas = [
        '# PDF del curso',
        '',
        f'PDF de las sesiones S0, S1 y S2 de «{C.CURSO}». Los exige la institución. Se generan desde las fuentes '
        '(presentaciones HTML y documentos Markdown): **no los edites a mano**, cambia la fuente y vuelve a generar.',
        '',
        '## Cómo se regeneran',
        '',
        '```text',
        'pip install playwright pypdf pygments     # y tener Google Chrome y pandoc',
        'python 00-Planificacion/pdfs/generar_pdfs.py             # todos',
        'python 00-Planificacion/pdfs/generar_pdfs.py --sesion S1 # una sesión',
        'python 00-Planificacion/pdfs/generar_pdfs.py --comprobar # revisa los PDF existentes',
        '```',
        '',
        'El contenido de esta carpeta sale de `00-Planificacion/pdfs/contenido_pdfs.py`.',
        '',
        '## Qué se pierde en las presentaciones',
        '',
        C.PERDIDO_EN_PRESENTACIONES,
        'Las interactivas (encuesta, simuladores, cronómetro) quedan como una imagen fija de su estado final. '
        'Para eso, y para las notas del orador, usa la presentación HTML.',
        '',
        'Los enlaces entre archivos del repositorio apuntan a la rama `' + C.RAMA + '` en GitHub.',
    ]
    for s in C.SESIONES:
        lineas += ['', f'## {s["id"]} · {s["titulo"]} ({s["horas"]})', '']
        for clave, (nombre, carpeta) in C.GRUPOS.items():
            filas = [e for e in s['elementos'] if e['grupo'] == clave]
            if not filas:
                continue
            lineas += [f'### {nombre}', '', '| PDF | Contenido | Páginas | Tamaño |', '|---|---|---|---|']
            for e in filas:
                ruta = ruta_pdf(s, e)
                ruta_rel = f'{s["carpeta"]}/{carpeta}/{e["archivo"]}'
                if ruta.exists():
                    d = info_pdf(ruta)
                    paginas, tam = str(d['paginas']), tamano_legible(d['bytes'])
                else:
                    paginas, tam = '—', 'sin generar'
                lineas.append(f'| [`{e["archivo"]}`]({ruta_rel}) | {e["titulo"]} | {paginas} | {tam} |')
            lineas.append('')
    return '\n'.join(lineas).rstrip() + '\n'


def escribir_leeme():
    (RAIZ / C.CARPETA_SALIDA).mkdir(exist_ok=True)
    (RAIZ / C.CARPETA_SALIDA / 'LEEME.md').write_text(texto_leeme(), encoding='utf-8')


def comprobar(filtro_sesion=None, filtro_archivo=None):
    """Revisa los PDF existentes: existen, tienen el tamaño de página esperado y, en presentaciones, una página por diapositiva."""
    from pypdf import PdfReader
    errores = []
    for s, e in elementos(filtro_sesion, filtro_archivo):
        ruta = ruta_pdf(s, e)
        if not ruta.exists():
            errores.append(f'falta {ruta.relative_to(RAIZ)}')
            continue
        d = info_pdf(ruta)
        if e['tipo'] == 'presentacion':
            esperado = len(re.findall(r'<section\b[^>]*\bclass="slide', (RAIZ / e['origen']).read_text(encoding='utf-8')))
            if d['paginas'] != esperado:
                errores.append(f'{ruta.name}: {d["paginas"]} páginas y la presentación tiene {esperado} diapositivas')
            if (round(d['ancho']), round(d['alto'])) != (960, 540):
                errores.append(f'{ruta.name}: tamaño {d["ancho"]:.0f}×{d["alto"]:.0f} pt (se esperaba 960×540)')
        elif abs(d['ancho'] - 595.3) > 2 or abs(d['alto'] - 841.9) > 2:  # A4; Chrome a veces redondea a 596 × 843
            errores.append(f'{ruta.name}: tamaño {d["ancho"]:.0f}×{d["alto"]:.0f} pt (se esperaba A4, 595×842)')
        texto = ' '.join((p.extract_text() or '') for p in PdfReader(str(ruta)).pages)
        if PALABRA_INTERNA in texto.lower():
            errores.append(f'{ruta.name}: contiene una palabra interna que no debe aparecer')
        if 'file:///' in ruta.read_bytes().decode('latin-1'):
            errores.append(f'{ruta.name}: tiene enlaces a file:///')
    return errores


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--sesion', help='solo esa sesión (S0, S1)')
    ap.add_argument('--solo', help='solo el PDF con ese nombre de archivo')
    ap.add_argument('--comprobar', action='store_true', help='revisa los PDF existentes y termina')
    a = ap.parse_args(argv)

    if a.comprobar:
        errores = comprobar(a.sesion, a.solo)
        for m in errores:
            print('ERROR', m)
        print('Comprobación:', 'correcta' if not errores else f'{len(errores)} problema(s)')
        return 1 if errores else 0

    from playwright.sync_api import sync_playwright
    cuantos = 0
    with sync_playwright() as p:
        navegador = lanzar(p)
        try:
            for s, e in elementos(a.sesion, a.solo):
                destino = ruta_pdf(s, e)
                if e['tipo'] == 'presentacion':
                    n = generar_presentacion(navegador, s, e, destino)
                    detalle = f'{n} diapositivas'
                elif e['tipo'] == 'documento':
                    n = generar_documento(navegador, s, e, destino)
                    detalle = f'{n} páginas'
                elif e['tipo'] == 'pagina':
                    n = generar_pagina(navegador, s, e, destino)
                    detalle = f'{n} páginas'
                else:
                    raise RuntimeError(f'tipo no admitido: {e["tipo"]}')
                print(f'{destino.relative_to(RAIZ)}  ({detalle}, {tamano_legible(destino.stat().st_size)})')
                cuantos += 1
        finally:
            navegador.close()
    if cuantos == 0:
        print('Nada que generar con ese filtro.')
        return 1
    escribir_leeme()
    errores = comprobar(a.sesion, a.solo)
    for m in errores:
        print('ERROR', m)
    return 1 if errores else 0


if __name__ == '__main__':
    sys.exit(main())
