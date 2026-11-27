"""Dibuja como imagen (.webp) una salida REAL de terminal guardada en salidas/*.txt, para que se vea en las diapositivas con lupa.

NO es una captura de la ventana de un terminal: es el TEXTO de la ejecución real, dibujado con una fuente monoespaciada sobre fondo claro, con una
barra de título que lo dice. Las diapositivas lo rotulan así («Salida real dibujada como imagen»). Las rutas locales ya se sustituyeron por <trabajo>
al guardar las salidas.

Uso (desde esta carpeta):  python terminal_a_imagen.py            (regenera todas las imágenes t-*.webp de img/)
Necesita Pillow y la fuente Consolas (Windows) o DejaVu Sans Mono (Linux).
"""
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

AQUI = Path(__file__).resolve().parent
ANCHO_CARACTERES = 118
FUENTES = [r'C:\Windows\Fonts\consola.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf']

# nombre de imagen -> (título de la barra, [(archivo de salidas, línea inicial, línea final o None), ...])
IMAGENES = {
    't-01-manifiesto.webp': ('python manifiesto_champion.py generar --salida vertex-manifiesto.json', [('01-manifiesto.txt', 0, None)]),
    't-02-prediccion.webp': ('curl -X POST http://127.0.0.1:8080/predict … -d @instancias.json  (adaptador real)', [('10-adaptador-prediccion.txt', 0, 3), ('10-adaptador-prediccion.txt', 5, None)]),
    't-03-paridad.webp': ('python comparar_paridad.py --respuesta … --instancias … --modelo-dir build/vertex/modelo', [('13-paridad.txt', 0, None)]),
    't-04-canario.webp': ('bash scripts/desplegar.sh --canario 10  y  bash scripts/probar.sh  (gcloud SIMULADO)', [('22-desplegar-canario.txt', 0, 1), ('22-desplegar-canario.txt', 6, None), ('23-probar-canario.txt', 0, 1), ('23-probar-canario.txt', 6, None)]),
    't-05-rollback.webp': ('bash scripts/volver.sh --sin-mlflow  (gcloud SIMULADO)', [('25-volver.txt', 0, None)]),
    't-06-pruebas.webp': ('python -m pytest -q -p no:cacheprovider pruebas', [('30-pruebas.txt', 0, None)]),
}


def fuente(tam):
    for f in FUENTES:
        if Path(f).exists():
            return ImageFont.truetype(f, tam)
    raise SystemExit('No encuentro una fuente monoespaciada (Consolas o DejaVu Sans Mono).')


def lineas_de(spec):
    out = []
    for archivo, ini, fin in spec:
        t = (AQUI / 'salidas' / archivo).read_text(encoding='utf-8').splitlines()
        out += t[ini:fin]
    return out


def dibujar(titulo, lineas, destino):
    f, fb = fuente(17), fuente(15)
    envueltas = []
    for l in lineas:
        envueltas += textwrap.wrap(l, ANCHO_CARACTERES, subsequent_indent='    ', break_long_words=True, replace_whitespace=False, drop_whitespace=False) or ['']
    alto_l, margen, barra = 23, 18, 38
    w = 1420
    h = barra + 2 * margen + alto_l * len(envueltas) + 26
    im = Image.new('RGB', (w, h), '#ffffff')
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, barra], fill='#eef1f5')
    for i, c in enumerate(('#ff6159', '#ffbd2e', '#28c941')):
        d.ellipse([14 + i * 22, 12, 28 + i * 22, 26], fill=c)
    d.text((88, 10), 'Salida real · 27/11/2026 · ' + titulo, font=fb, fill='#445')
    y = barra + margen
    for l in envueltas:
        color = '#1a7f37' if l.startswith('$') else '#9a3412' if l.startswith(('AVISO', 'ERROR', 'Error')) else '#1f2933'
        d.text((margen, y), l, font=f, fill=color)
        y += alto_l
    d.text((margen, h - 24), 'texto de la ejecución real (salidas/), dibujado como imagen; no es una captura de pantalla de la ventana', font=fuente(12), fill='#8a94a0')
    im.save(destino, quality=88)
    return im.size


def main():
    for nombre, (titulo, spec) in IMAGENES.items():
        try:
            lineas = lineas_de(spec)
        except FileNotFoundError as e:
            print(f'omitida {nombre}: falta {Path(e.filename).name}')
            continue
        print(nombre, dibujar(titulo, lineas, AQUI / 'img' / nombre))


if __name__ == '__main__':
    sys.exit(main())
