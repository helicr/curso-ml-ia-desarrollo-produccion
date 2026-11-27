"""Pruebas de la presentación (index.html) y de los archivos del extra.

Lo importante: cada bloque de código que la presentación ofrece para copiar está TAL CUAL en un archivo del extra, y las capturas de img/ existen.
"""
import html
import re
import subprocess
import sys
from pathlib import Path

import pytest

EXTRA = Path(__file__).resolve().parents[1]
INDEX = (EXTRA / 'index.html').read_text(encoding='utf-8')
ARCHIVOS = [p for p in EXTRA.rglob('*') if p.is_file() and p.suffix in ('.py', '.md', '.yml', '.yaml', '.Dockerfile', '.dockerignore', '.txt')
            and 'pruebas' not in p.parts and p.name != 'index.html']
TEXTO = '\n'.join(p.read_text(encoding='utf-8') for p in ARCHIVOS)


def diapositivas():
    return re.findall(r'<section class="slide[^"]*".*?</section>', INDEX, re.S)


def test_generar_esta_al_dia():
    r = subprocess.run([sys.executable, str(EXTRA / 'generar.py'), '--comprobar'], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_numero_de_diapositivas_y_estructura():
    n = len(diapositivas())
    assert 20 <= n <= 28
    assert '<html lang="es">' in INDEX and 'href="../index.html"' in INDEX and '⌂ Índice' in INDEX
    assert INDEX.count('class="kick"') == n and INDEX.count('<h1>') == n          # un mensaje por diapositiva


def test_cada_bloque_para_copiar_esta_tal_cual_en_los_archivos():
    bloques = [html.unescape(b) for b in re.findall(r'class="cp[^"]*" data-t="([^"]*)"', INDEX)]
    assert len(bloques) >= 15
    sueltos = {'cd 01-Sesiones/S5-MLOps-y-Operacion/extra-mcp-notebooks/ui\npython app.py',
               'AIRFLOW_URL=http://localhost:8080 AIRFLOW_AUTH=basic AIRFLOW_USUARIO=airflow AIRFLOW_CLAVE=airflow'}      # variables y arranque de la UI: están en su README y app.py
    for b in bloques:
        if b in sueltos:
            continue
        assert b in TEXTO, f'este bloque no está tal cual en ningún archivo:\n{b[:200]}'
    ui = (EXTRA.parent / 'extra-mcp-notebooks' / 'ui' / 'app.py').read_text(encoding='utf-8')
    assert 'AIRFLOW_URL' in ui and 'AIRFLOW_AUTH' in ui and 'python app.py' in ui


def test_las_capturas_reales_existen_y_las_pendientes_estan_rotuladas():
    reales = set(re.findall(r'data-src="img/([^"]+)"', INDEX))
    assert {'ui-02-conectado.webp', 'gcp-01-composer-api.webp', 'term-03-lanzar-lote.webp'} <= reales
    for r in reales:
        assert (EXTRA / 'img' / r).is_file() and (EXTRA / 'img' / r).stat().st_size > 2000
    pendientes = re.findall(r'<div class="pend"><b>Captura pendiente</b><span class="mono">img/([^<]+)</span>', INDEX)
    assert pendientes, 'debe haber recuadros de captura pendiente'
    md = (EXTRA / 'capturas-pendientes.md').read_text(encoding='utf-8')
    for p in pendientes:
        assert p in md, f'{p} no está en capturas-pendientes.md'
        assert not (EXTRA / 'img' / p).exists(), f'{p} existe: debería mostrarse como captura real'
    assert INDEX.count('Cómo hacer esta captura') == len(pendientes)


def test_las_capturas_de_servidor_de_prueba_estan_rotuladas_asi():
    for nombre in ('ui-02-conectado', 'ui-04-en-curso', 'ui-05-terminado', 'ui-06-fallo', 'ui-07-movil'):
        m = re.search(rf'data-img="{nombre}.webp".*?</figure>', INDEX, re.S)
        assert m and 'DE PRUEBA' in m.group(0), nombre
    assert 'Airflow real' in INDEX and 'Sin verificar' in INDEX


def test_nada_se_presenta_como_probado_si_no_se_ejecuto():
    for texto in ('Sin ensayar', 'Sin verificar'):
        assert texto in INDEX
    assert 'cuesta dinero' in INDEX.lower() and 'sin dato' in INDEX.lower()
    assert 'no se habilitó ninguna API' in html.unescape(INDEX).replace('**', '') or 'no se habilitó' in html.unescape(INDEX)


def test_tildes_y_sin_marcas_rotas():
    assert 'Ã' not in INDEX and '�' not in INDEX
    for archivo in ('README.md', 'comandos.md', 'capturas-pendientes.md'):
        t = (EXTRA / archivo).read_text(encoding='utf-8')
        assert 'Ã' not in t and '�' not in t


def test_fondo_blanco():
    assert re.search(r'--bg:\s*#fff|background:\s*#fff', INDEX, re.I)


def test_lo_que_dice_el_readme_existe():
    readme = (EXTRA / 'README.md').read_text(encoding='utf-8')
    for archivo in re.findall(r'`((?:dags/|pruebas/)?[\w\-]+\.(?:py|yml|yaml|md|html|Dockerfile))`', readme):
        assert (EXTRA / archivo).exists() or (EXTRA / 'pruebas' / archivo).exists() or archivo in ('puntuar-lote.yml',), archivo


def test_capturas_de_github_son_de_otros_workflows_y_estan_rotuladas():
    for nombre in ('gh-01-actions-lista', 'gh-02-nueva-version-runs', 'gh-03-puntuar-lote-resumen', 'gh-04-environments', 'gh-05-variables'):
        assert (EXTRA / 'img' / (nombre + '.webp')).is_file()
        m = re.search(rf'data-img="{nombre}.webp".*?</figure>', INDEX, re.S)
        assert m and 'solo lectura' in m.group(0), nombre
    assert 'OTROS workflows' in INDEX and 'aún no está en el repositorio' in INDEX
