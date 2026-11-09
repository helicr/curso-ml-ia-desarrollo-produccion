"""Genera index.html a partir de index.template.html e inserta el texto de los dos scripts.

Ejecutar desde cualquier carpeta:  python generar.py
Vuelve a ejecutarlo cada vez que cambies ../scripts/instalar_entorno.ps1 o ../scripts/instalar_entorno.cmd,
para que la guía y los scripts no se desincronicen.
"""
import html
from pathlib import Path

aqui = Path(__file__).resolve().parent
plantilla = (aqui / 'index.template.html').read_text(encoding='utf-8')
scripts = aqui.parent / 'scripts'

salida = plantilla
for marcador, nombre in (('@@SCRIPT_PS@@', 'instalar_entorno.ps1'), ('@@SCRIPT_CMD@@', 'instalar_entorno.cmd')):
    assert plantilla.count(marcador) == 1, f'La plantilla debe contener exactamente un marcador {marcador}'
    texto = (scripts / nombre).read_text(encoding='utf-8')  # normaliza CRLF a LF
    salida = salida.replace(marcador, html.escape(texto, quote=False))

(aqui / 'index.html').write_text(salida, encoding='utf-8')
print('index.html generado:', len(salida), 'caracteres')
