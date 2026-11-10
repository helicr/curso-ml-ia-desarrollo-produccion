"""Comprueba en un Chrome real los índices de sesión: diseño sin desbordes, interruptor GitHub/local, enlaces entre sesiones,
que cada presentación enlazada carga y que su enlace de regreso lleva de vuelta al índice de su sesión.
Requiere playwright y Chrome.

Uso:  python 00-Planificacion/indices-de-sesion/comprobar_diseno.py [--capturas CARPETA]
Sale con código 1 si algo falla.
"""
import argparse
import sys
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(AQUI))
import contenido_indices as C  # noqa: E402

CHROME = '/usr/bin/google-chrome'
ANCHOS = [(1280, 800), (1024, 768), (800, 600), (390, 844)]
BASE = f'{C.REPO_GITHUB}/blob/{C.RAMA}/'

fallos = []


def comprobar(cond, msg):
    if not cond:
        fallos.append(msg)
        print('  FALLA:', msg)


def indice_de(s):
    return RAIZ / s['carpeta'] / 'index.html'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--capturas', help='carpeta donde guardar capturas de pantalla')
    args = ap.parse_args()
    capturas = Path(args.capturas) if args.capturas else None
    if capturas:
        capturas.mkdir(parents=True, exist_ok=True)
    visitadas = 0

    with sync_playwright() as p:
        nav = p.chromium.launch(executable_path=CHROME, headless=True, args=['--no-sandbox'])

        for i, s in enumerate(C.SESIONES):
            url = indice_de(s).as_uri()
            # ---- diseño por tamaño
            for ancho, alto in ANCHOS:
                ctx = nav.new_context(viewport={'width': ancho, 'height': alto})
                pg = ctx.new_page()
                errores, externas = [], []
                pg.on('console', lambda m: errores.append(m.text) if m.type == 'error' else None)
                pg.on('pageerror', lambda e: errores.append(str(e)))
                pg.on('request', lambda r: externas.append(r.url) if not r.url.startswith('file://') else None)
                pg.goto(url)
                pg.wait_for_load_state('load')
                sw = pg.evaluate('document.documentElement.scrollWidth')
                comprobar(sw <= ancho, f'{s["id"]} {ancho}px: desborde horizontal (scrollWidth {sw})')
                comprobar(not errores, f'{s["id"]} {ancho}px: errores de consola {errores}')
                comprobar(not externas, f'{s["id"]} {ancho}px: peticiones externas {externas}')
                cortes = pg.evaluate("""() => [...document.querySelectorAll('a.deck,.falta,.col,header.top')]
                    .filter(e => e.scrollWidth > e.clientWidth + 1).map(e => e.className + ':' + e.scrollWidth + '>' + e.clientWidth)""")
                comprobar(not cortes, f'{s["id"]} {ancho}px: contenido que no cabe en su caja {cortes}')
                if capturas and ancho in (1280, 390):
                    pg.screenshot(path=str(capturas / f'{s["id"]}-{ancho}.png'), full_page=True)
                ctx.close()

            # ---- comportamiento (1280)
            ctx = nav.new_context(viewport={'width': 1280, 'height': 800})
            pg = ctx.new_page()
            pg.goto(url)
            titulo = pg.title()
            comprobar(titulo.startswith(s['id']), f'{s["id"]}: el título de la página es «{titulo}»')

            docs = pg.locator('a.doc')
            if docs.count():
                ruta = docs.first.get_attribute('data-path')
                comprobar(docs.first.get_attribute('href') == BASE + ruta, f'{s["id"]}: por defecto los documentos deben abrir en GitHub')
                pg.check('input[value=local]')
                href_local = docs.first.evaluate('a => a.href')
                comprobar(href_local == (RAIZ / ruta).as_uri(), f'{s["id"]} modo local: href {href_local}')
                pg.reload()
                comprobar(pg.is_checked('input[value=local]'), f'{s["id"]}: el modo elegido no se recuerda al recargar')
                pg.check('input[value=github]')

            # enlaces a la sesión anterior y a la siguiente
            esperadas = (['← ' + C.SESIONES[i - 1]['id']] if i > 0 else []) + ([C.SESIONES[i + 1]['id'] + ' →'] if i < len(C.SESIONES) - 1 else [])
            textos = [t.strip() for t in pg.locator('nav.vecinas a').all_inner_texts()]
            comprobar(textos == esperadas, f'{s["id"]}: enlaces a otras sesiones {textos}, esperados {esperadas}')
            for k in range(len(textos)):
                destino = pg.locator('nav.vecinas a').nth(k).evaluate('a => a.href')
                comprobar(Path(urlparse(destino).path).is_file(), f'{s["id"]}: el enlace «{textos[k]}» apunta a un archivo que no existe')

            # cada presentación enlazada carga; las que llevan «volver» devuelven a este índice
            hrefs = pg.evaluate("[...document.querySelectorAll('a.deck')].map(a => a.href)")
            volver = {(RAIZ / e['ruta']).as_uri() for e in C.SESIONES[i]['enlaces'] if e['tipo'] == 'deck' and e['volver']}
            for h in hrefs:
                pg2 = ctx.new_page()
                pg2.goto(h)
                pg2.wait_for_load_state('load')
                visitadas += 1
                comprobar(bool(pg2.title().strip()), f'{s["id"]}: {h} no tiene título')
                if h in volver:
                    for ancho, alto in ANCHOS[:3]:
                        pg2.set_viewport_size({'width': ancho, 'height': alto})
                        ok_barra = pg2.evaluate("(() => { const b = document.getElementById('bar'); return !b || b.scrollWidth <= b.clientWidth + 1 })()")
                        comprobar(ok_barra, f'{s["id"]}: la barra de {Path(urlparse(h).path).relative_to(RAIZ)} se desborda a {ancho}px')
                    enlace = pg2.locator('a#bhome')
                    comprobar(enlace.count() == 1, f'{s["id"]}: {h} no tiene el enlace «⌂ Índice» en su barra')
                    if enlace.count() == 1:
                        enlace.click()
                        pg2.wait_for_load_state('load')
                        comprobar(urlparse(pg2.url).path == str(indice_de(s)), f'{s["id"]}: el enlace de regreso de {h} lleva a {pg2.url}')
                pg2.close()
            ctx.close()
            print(f'  {s["id"]}: página, interruptor, sesiones vecinas y {len(hrefs)} presentaciones/páginas enlazadas revisadas')

        nav.close()

    if fallos:
        print(f'\n{len(fallos)} problema(s).')
        sys.exit(1)
    print(f'\nDISENO OK: {len(C.SESIONES)} índices en {len(ANCHOS)} tamaños sin desbordes; {visitadas} enlaces a presentaciones abiertos')


if __name__ == '__main__':
    main()
