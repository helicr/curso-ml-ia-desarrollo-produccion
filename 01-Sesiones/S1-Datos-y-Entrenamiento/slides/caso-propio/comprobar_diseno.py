"""Comprueba en un navegador real la presentación «Tu caso de S1 a S5»: nada se desborda ni tapa el pie y los controles funcionan.

Necesita Playwright y un Chrome/Chromium (no forma parte de las pruebas automáticas del curso porque no todos los equipos los tienen):
    python comprobar_diseno.py [--chrome /usr/bin/google-chrome] [--capturas carpeta]
Revisa en 1280x766 (proyector), 1024x640 y 800x600:
  - el contenido de cada diapositiva cabe en el escenario de 1280x720 y no pisa el pie;
  - la diapositiva activa es la que marca el hash y se llega a la última con el teclado;
  - «⧉» deja en el portapapeles exactamente el comando; la lista final recuerda las marcas al recargar; la tecla O abre el índice;
  - el botón «⌂ Índice de S1» apunta a un archivo que existe.
Termina con código 0 solo si todo está bien.
"""
import argparse
import importlib.util
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[3]
_spec = importlib.util.spec_from_file_location('comprobar_codespaces', RAIZ / '03-Entorno' / 'guia-codespaces' / 'comprobar_diseno.py')
_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base)
MEDIR, TAMANOS = _base.MEDIR, _base.TAMANOS
TITULO_FINAL = 'Lista final'
TITULO_COMANDOS = 'Dónde está y cómo leerlo'


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--chrome', default='/usr/bin/google-chrome')
    ap.add_argument('--capturas', help='carpeta donde guardar una captura por diapositiva (1280x766)')
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright

    url = (AQUI / 'index.html').as_uri()
    problemas = []
    with sync_playwright() as pw:
        nav = pw.chromium.launch(executable_path=a.chrome, headless=True, args=['--no-sandbox'])
        n = 0
        for ancho, alto in TAMANOS:
            ctx = nav.new_context(viewport={'width': ancho, 'height': alto}, permissions=['clipboard-read', 'clipboard-write'])
            pag = ctx.new_page()
            errores = []
            pag.on('pageerror', lambda e: errores.append(str(e)))
            pag.on('console', lambda m: errores.append(m.text) if m.type == 'error' else None)
            pag.goto(url)
            pag.wait_for_selector('.slide.active')
            n = pag.locator('.slide').count()
            for i in range(1, n + 1):
                pag.evaluate(f"location.hash = '#{i}'")
                pag.reload()
                pag.wait_for_selector('.slide.active')
                activa = pag.evaluate("[...document.querySelectorAll('.slide')].findIndex(s => s.classList.contains('active')) + 1")
                if activa != i:
                    problemas.append(f'{ancho}x{alto}: el hash #{i} activa la diapositiva {activa}')
                if a.capturas and (ancho, alto) == TAMANOS[0]:
                    d = Path(a.capturas)
                    d.mkdir(parents=True, exist_ok=True)
                    pag.wait_for_timeout(450)
                    pag.screenshot(path=str(d / f'{i:02d}.png'))
            if errores:
                problemas.append(f'{ancho}x{alto}: errores en la consola: {errores[:3]}')
            for m in pag.evaluate(MEDIR):
                if m['contenido_abajo'] > m['pie_arriba'] - 4:
                    problemas.append(f'{ancho}x{alto}: diapositiva {m["i"]} «{m["titulo"]}»: el contenido llega a {m["contenido_abajo"]} y el pie empieza en {m["pie_arriba"]} ({m["culpable"]})')
                if m['contenido_derecha'] > 1280 - 20:
                    problemas.append(f'{ancho}x{alto}: diapositiva {m["i"]} «{m["titulo"]}»: el contenido llega a x={m["contenido_derecha"]} de 1280')
                if m['scrollH'] > m['clientH'] + 52 + 1 or m['scrollW'] > m['clientW'] + 1:
                    problemas.append(f'{ancho}x{alto}: diapositiva {m["i"]} «{m["titulo"]}»: desborda (scroll {m["scrollW"]}x{m["scrollH"]} > {m["clientW"]}x{m["clientH"]})')
            ctx.close()

        # comportamiento (una vez, a 1280x766)
        ctx = nav.new_context(viewport={'width': 1280, 'height': 766}, permissions=['clipboard-read', 'clipboard-write'])
        pag = ctx.new_page()
        pag.goto(url)
        pag.wait_for_selector('.slide.active')
        for _ in range(n - 1):
            pag.keyboard.press('ArrowRight')
        if pag.evaluate("document.querySelector('#count').textContent") != f'{n} / {n}':
            problemas.append('el teclado no llega a la última diapositiva')
        href = pag.evaluate("document.querySelector('#bhome').getAttribute('href')")
        destino = (AQUI / href).resolve()
        if not destino.exists() or destino.parent.name != 'S1-Datos-y-Entrenamiento':
            problemas.append(f'«⌂ Índice de S1» apunta a {href}, que no es el índice de S1')
        pag.keyboard.press('Home')
        # copiar cada línea del terminal
        pag.evaluate(f"location.hash = '#' + ([...document.querySelectorAll('.slide')].findIndex(s => s.dataset.title === {TITULO_COMANDOS!r}) + 1)")
        pag.reload()
        pag.wait_for_selector('.slide.active')
        botones = pag.locator('.slide.active .cp')
        if botones.count() != 3:
            problemas.append(f'la diapositiva de comandos debería tener 3 líneas copiables y tiene {botones.count()}')
        for k in range(botones.count()):
            esperado = botones.nth(k).get_attribute('data-t')
            botones.nth(k).click()
            if pag.evaluate('navigator.clipboard.readText()') != esperado:
                problemas.append(f'copiar la línea {k + 1} no deja el comando exacto')
        # lista final
        pag.evaluate(f"location.hash = '#' + ([...document.querySelectorAll('.slide')].findIndex(s => s.dataset.title === {TITULO_FINAL!r}) + 1)")
        pag.reload()
        pag.wait_for_selector('.slide.active')
        pag.locator('.slide.active .check input').first.check()
        pag.reload()
        pag.wait_for_selector('.slide.active')
        if not pag.locator('.slide.active .check input').first.is_checked():
            problemas.append('la lista final no recuerda las marcas')
        pag.keyboard.press('o')
        if not pag.locator('#index.on').count():
            problemas.append('la tecla O no abre el índice')
        ctx.close()
        nav.close()
    if problemas:
        print('PROBLEMAS DE DISEÑO:')
        for p in problemas:
            print(' -', p)
        sys.exit(1)
    print(f'DISEÑO OK: {n} diapositivas sin desbordes en {len(TAMANOS)} tamaños; copiar, lista final, índice y enlace a S1 funcionan')


if __name__ == '__main__':
    main()
