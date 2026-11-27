"""Recorre la interfaz con Playwright (Edge/Chromium propio, headless) y guarda capturas. No es una prueba de pytest.

    python pruebas/capturar.py [URL] [CARPETA] [--promover]

Con --promover acepta el diálogo de promover y de volver (ESCRIBE en el registro de MLflow: úsalo solo con una copia o restaura después).
Usa un navegador PROPIO de Playwright: nunca se conecta a un Chrome abierto por el usuario.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

args = [a for a in sys.argv[1:] if not a.startswith('--')]
URL = args[0] if args else 'http://127.0.0.1:8095/'
OUT = Path(args[1] if len(args) > 1 else 'capturas')
PROMOVER = '--promover' in sys.argv
OUT.mkdir(parents=True, exist_ok=True)
errores = []


def lanzar(p):
    try:
        return p.chromium.launch(headless=True)
    except Exception:                                    # noqa: BLE001 - sin Chromium descargado: Edge del sistema, también propio y sin perfil
        return p.chromium.launch(headless=True, channel='msedge')


def recorrer(pagina, sufijo):
    pagina.on('console', lambda m: errores.append(f'[{sufijo}] consola {m.type}: {m.text}') if m.type in ('error', 'warning') else None)
    pagina.on('pageerror', lambda e: errores.append(f'[{sufijo}] excepción: {e}'))
    pagina.goto(URL)
    try:
        pagina.wait_for_selector('.cli-item', timeout=45000)      # sin alias champion no hay clientes: se sigue igualmente
    except Exception:                                    # noqa: BLE001
        pass
    pagina.wait_for_timeout(800)
    pagina.screenshot(path=str(OUT / f'01-cliente-vacio-{sufijo}.png'), full_page=True)
    if pagina.locator('.cli-item').count():
        pagina.locator('.cli-item').first.click()
        pagina.wait_for_selector('.medidor-caja svg', timeout=30000)
        pagina.wait_for_timeout(600)
        pagina.screenshot(path=str(OUT / f'02-cliente-{sufijo}.png'), full_page=True)
        pagina.click('#t-ysi')
        pagina.wait_for_selector('#ysi-res svg', timeout=30000)
        pagina.fill('#n-recencia_dias', '30')
        pagina.wait_for_timeout(1200)
        pagina.screenshot(path=str(OUT / f'03-ysi-{sufijo}.png'), full_page=True)
    pagina.click('#t-pregunta')
    pagina.wait_for_timeout(500)
    pagina.screenshot(path=str(OUT / f'04-pregunta-{sufijo}.png'), full_page=True)
    pagina.click('#t-explorador')
    pagina.wait_for_selector('.herr')
    pagina.locator('.ataque', has_text='UPDATE').click()
    pagina.wait_for_selector('.veredicto')
    pagina.wait_for_timeout(400)
    pagina.screenshot(path=str(OUT / f'05-explorador-{sufijo}.png'), full_page=True)
    pagina.click('#t-modelo')
    pagina.wait_for_timeout(600)
    pagina.screenshot(path=str(OUT / f'06-modelo-{sufijo}.png'), full_page=True)
    boton = pagina.locator('button.boton', has_text='Promover').first
    boton.click()
    pagina.wait_for_selector('dialog[open]')
    pagina.wait_for_timeout(300)
    pagina.screenshot(path=str(OUT / f'07-dialogo-promover-{sufijo}.png'))
    if PROMOVER and sufijo == 'escritorio':
        pagina.click('#dlg-ok')
        pagina.wait_for_selector('.antes-despues', timeout=60000)
        pagina.wait_for_timeout(800)
        pagina.screenshot(path=str(OUT / f'08-modelo-tras-promover-{sufijo}.png'), full_page=True)
    else:
        pagina.click('#dlg-cancelar')
    pagina.click('#b-traza') if pagina.locator('#traza').is_hidden() else None
    pagina.wait_for_timeout(500)
    pagina.screenshot(path=str(OUT / f'09-traza-{sufijo}.png'))


with sync_playwright() as p:
    b = lanzar(p)
    for sufijo, vp in (('escritorio', {'width': 1440, 'height': 900}), ('movil', {'width': 390, 'height': 844})):
        ctx = b.new_context(viewport=vp, locale='es-ES')
        recorrer(ctx.new_page(), sufijo)
        ctx.close()
    b.close()
print('\n'.join(errores) or 'Sin errores ni avisos en la consola.')
