"""Comprueba en un navegador real (guía de Codespaces) que ninguna diapositiva de index.html se desborda ni tapa su pie, y que los botones funcionan.

Necesita Playwright y un Chrome/Chromium (no forma parte de las pruebas automaticas del curso porque no todos los equipos los tienen):
    python comprobar_diseno.py [--chrome /usr/bin/google-chrome] [--capturas carpeta]
Revisa en 1280x766 (pantalla de proyector), 1024x640 y 800x600:
  - el contenido de cada diapositiva cabe en el escenario de 1280x720 y no pisa el pie;
  - la diapositiva activa es la que marca el hash y todas se pueden visitar con el teclado;
  - «Copiar» deja en el portapapeles exactamente el comando; «Copiar todo» deja todos los del paso; «Marcar como hecho» se recuerda al recargar.
Termina con codigo 0 solo si todo esta bien.
"""
import argparse
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
TAMANOS = [(1280, 766), (1024, 640), (800, 600)]

MEDIR = """
() => {
  const out = [];
  const stage = document.querySelector('#stage');
  const s = parseFloat(getComputedStyle(stage).getPropertyValue('--s')) || 1;
  for (const [i, sl] of [...document.querySelectorAll('.slide')].entries()) {
    const r0 = sl.getBoundingClientRect();
    const foot = sl.querySelector('.foot').getBoundingClientRect();
    let maxB = 0, maxR = 0, culpable = '';
    for (const el of sl.querySelectorAll('*')) {
      if (el.closest('.foot') || el.closest('.term .bar')) continue;
      const r = el.getBoundingClientRect();
      if (r.width === 0 && r.height === 0) continue;
      const b = (r.bottom - r0.top) / s, d = (r.right - r0.left) / s;
      if (b > maxB) { maxB = b; culpable = el.tagName.toLowerCase() + '.' + el.className + ' ' + (el.textContent || '').slice(0, 40).replace(/\\s+/g, ' '); }
      if (d > maxR) maxR = d;
    }
    out.push({i: i + 1, titulo: sl.dataset.title, contenido_abajo: Math.round(maxB), pie_arriba: Math.round((foot.top - r0.top) / s),
              contenido_derecha: Math.round(maxR), scrollH: sl.scrollHeight, clientH: sl.clientHeight, scrollW: sl.scrollWidth, clientW: sl.clientWidth, culpable});
  }
  return out;
}
"""


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
                    Path(a.capturas).mkdir(parents=True, exist_ok=True)
                    pag.wait_for_timeout(450)                    # que termine la transicion
                    pag.screenshot(path=str(Path(a.capturas) / f'{i:02d}.png'))
            if errores:
                problemas.append(f'{ancho}x{alto}: errores en la consola: {errores[:3]}')
            # medidas: se hacen una vez por tamano con todas las diapositivas visibles (visibility no afecta a getBoundingClientRect)
            for m in pag.evaluate(MEDIR):
                if m['contenido_abajo'] > m['pie_arriba'] - 4:
                    problemas.append(f'{ancho}x{alto}: diapositiva {m["i"]} «{m["titulo"]}»: el contenido llega a {m["contenido_abajo"]} y el pie empieza en {m["pie_arriba"]} ({m["culpable"]})')
                if m['contenido_derecha'] > 1280 - 20:
                    problemas.append(f'{ancho}x{alto}: diapositiva {m["i"]} «{m["titulo"]}»: el contenido llega a x={m["contenido_derecha"]} de 1280')
                if m['scrollH'] > m['clientH'] + 52 + 1 or m['scrollW'] > m['clientW'] + 1:      # 52 px = relleno inferior reservado al pie
                    problemas.append(f'{ancho}x{alto}: diapositiva {m["i"]} «{m["titulo"]}»: desborda (scroll {m["scrollW"]}x{m["scrollH"]} > {m["clientW"]}x{m["clientH"]})')
            ctx.close()

        # --- comportamiento (una vez, a 1280x766)
        ctx = nav.new_context(viewport={'width': 1280, 'height': 766}, permissions=['clipboard-read', 'clipboard-write'])
        pag = ctx.new_page()
        pag.goto(url)
        pag.wait_for_selector('.slide.active')
        n = pag.locator('.slide').count()
        for _ in range(n - 1):
            pag.keyboard.press('ArrowRight')
        if pag.evaluate("document.querySelector('#count').textContent") != f'{n} / {n}':
            problemas.append('el teclado no llega a la ultima diapositiva')
        pag.keyboard.press('Home')
        # un paso con varias lineas y «Copiar todo»: B1
        pag.evaluate("location.hash = '#' + ([...document.querySelectorAll('.slide')].findIndex(s => s.dataset.id === 'orientar') + 1)")
        pag.reload()
        pag.wait_for_selector('.slide.active')
        activa = pag.locator('.slide.active')
        botones = activa.locator('.cp')
        for k in range(botones.count()):
            esperado = botones.nth(k).get_attribute('data-t')
            botones.nth(k).click()
            if pag.evaluate('navigator.clipboard.readText()') != esperado:
                problemas.append(f'copiar linea {k + 1} de «orientar» no deja el comando exacto')
        activa.locator('.cpall').click()
        todo = activa.locator('.cpall').get_attribute('data-t')
        if pag.evaluate('navigator.clipboard.readText()') != todo or todo.count('\n') + 1 != botones.count():
            problemas.append('«Copiar todo» no copia todas las lineas del paso')
        activa.locator('.hecho-btn').click()
        pag.reload()
        pag.wait_for_selector('.slide.active')
        if 'on' not in (pag.locator('.slide.active .hecho-btn').get_attribute('class') or ''):
            problemas.append('«Marcar como hecho» no se recuerda al recargar')
        # lista final: marcas
        pag.evaluate("location.hash = '#' + ([...document.querySelectorAll('.slide')].findIndex(s => s.dataset.title === 'Listo para S2') + 1)")
        pag.reload()
        pag.wait_for_selector('.slide.active')
        pag.locator('.slide.active .check input').first.check()
        pag.reload()
        pag.wait_for_selector('.slide.active')
        if not pag.locator('.slide.active .check input').first.is_checked():
            problemas.append('la lista final no recuerda las marcas')
        pag.keyboard.press('o')
        if not pag.locator('#index.on').count():
            problemas.append('la tecla O no abre el indice')
        ctx.close()
        nav.close()

    if problemas:
        print('PROBLEMAS DE DISENO:')
        for p in problemas:
            print(' -', p)
        sys.exit(1)
    print(f'DISENO OK: {n} diapositivas sin desbordes en {len(TAMANOS)} tamanos; copiar, copiar todo, hecho, lista y teclado funcionan')


if __name__ == '__main__':
    main()
