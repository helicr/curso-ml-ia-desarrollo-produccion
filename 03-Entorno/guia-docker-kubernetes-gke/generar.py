"""Genera index.html (la guía «Docker, Kubernetes y GKE» en diapositivas) a partir de plantilla.html.

Sustituye cada marca <!--CAPTURA nombre|pie--> por la captura capturas/nombre.webp embebida (data URI) con su pie,
así el HTML se abre con doble clic, sin archivos aparte. Edita plantilla.html, no index.html.

Uso (desde cualquier carpeta):  python generar.py
Las capturas son de la práctica de kind ejecutada en el Codespace del curso el 13/11/2026.
"""
import base64
import html
import re
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PLANTILLA = AQUI / 'plantilla.html'
SALIDA = AQUI / 'index.html'
CAPTURAS = AQUI / 'capturas'
MARCA = re.compile(r'<!--CAPTURA ([\w-]+)\|(.*?)-->')


def figura(m):
    nombre, pie = m.group(1), m.group(2)
    datos = base64.b64encode((CAPTURAS / f'{nombre}.webp').read_bytes()).decode('ascii')
    return (f'<figure class="shot"><img src="data:image/webp;base64,{datos}" alt="{html.escape(pie, quote=True)}">'
            f'<figcaption>{html.escape(pie)}</figcaption></figure>')


def construir():
    return MARCA.sub(figura, PLANTILLA.read_text(encoding='utf-8'))


def capturas_citadas():
    return [m.group(1) for m in MARCA.finditer(PLANTILLA.read_text(encoding='utf-8'))]


def main():
    SALIDA.write_text(construir(), encoding='utf-8', newline='\n')
    n = len(re.findall(r'<section class="slide"', SALIDA.read_text(encoding='utf-8')))
    print(f'{SALIDA.name}: {SALIDA.stat().st_size} bytes · {n} diapositivas · {len(capturas_citadas())} capturas')


if __name__ == '__main__':
    main()
