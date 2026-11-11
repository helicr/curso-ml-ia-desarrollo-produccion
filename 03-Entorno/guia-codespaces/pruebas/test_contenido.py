"""Pruebas de la guía «Codespaces: tu laboratorio de Docker en la nube»: coherente con el laboratorio de S2, con el devcontainer, con las salidas reales y con lo generado.

Ejecutar:  python -m pytest 03-Entorno/guia-codespaces/pruebas -q
No necesitan Internet ni Docker: leen archivos del repositorio.
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import pytest

AQUI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AQUI))
import generar as G  # noqa: E402

RAIZ = AQUI.parents[1]
LAB = (RAIZ / '01-Sesiones' / 'S2-API-y-Docker' / 'practica' / 'guia-laboratorio.md').read_text(encoding='utf-8')
DEVC = (RAIZ / '.devcontainer' / 'devcontainer.json').read_text(encoding='utf-8')
SALIDAS = json.loads((AQUI / 'salidas-reales.json').read_text(encoding='utf-8'))['salidas']
PALABRA_PROHIBIDA = re.compile(r'gu[ií]a[\s_-]*burros?', re.I)      # nombre interno nuestro: no debe aparecer en nada que vea el alumno
COPIABLES_EXTRA = {'https://github.com/codespaces/new', 'python --version', 'gh codespace code'}


@pytest.fixture(scope='module')
def html():
    return G.construir_html()


@pytest.fixture(scope='module')
def markdown():
    return G.construir_md()


def bloque_4_del_laboratorio():
    ini = LAB.index('## 4. Docker en Codespaces')
    fin = LAB.index('## 5. ')
    return LAB[ini:fin]


def test_los_comandos_de_la_guia_estan_en_el_bloque_4_del_laboratorio():
    bloque = bloque_4_del_laboratorio()
    for c in G.COMANDOS_LAB:
        assert c in bloque, f'«{c}» no aparece en el bloque 4 de practica/guia-laboratorio.md: la guía y el laboratorio se han separado'


def test_todo_lo_copiable_es_un_comando_del_laboratorio_o_un_extra_declarado(html):
    copiables = set(re.findall(r'class="cp" data-t="([^"]+)"', html))
    import html as h
    copiables = {h.unescape(c) for c in copiables}
    assert copiables, 'no hay botones de copiar'
    desconocidos = copiables - set(G.COMANDOS_LAB) - COPIABLES_EXTRA
    assert not desconocidos, desconocidos


def test_el_devcontainer_del_curso_dice_lo_que_dice_la_guia():
    assert 'mcr.microsoft.com/devcontainers/python:1-3.11-bookworm' in DEVC
    assert 'ghcr.io/devcontainers/features/docker-in-docker:2' in DEVC
    assert 'pip install -r 04-Proyecto-Base/requirements-dev.txt' in DEVC
    assert '8080' in DEVC and 'API ia-mlops' in DEVC
    assert 'ms-python.python' in DEVC and 'ms-azuretools.vscode-docker' in DEVC


def test_la_guia_es_honesta_sobre_lo_que_no_se_ha_probado(html, markdown):
    for texto in (html, markdown):
        assert 'Todavía no se ha abierto ningún Codespace del curso' in texto
        assert re.search(r'sin probar', texto, re.I)
    assert 'Sin probar' in html and 'Verificado' in html


def test_la_guia_no_promete_lo_que_no_es_nuestro(html, markdown):
    """No debe afirmar que el instructor hará algo concreto, ni que kind/kubectl ya estén en el devcontainer."""
    for texto in (html, markdown):
        assert 'el instructor abrirá' not in texto
    assert 'kubectl' not in DEVC and '"kind' not in DEVC, 'el devcontainer ya trae kind/kubectl: actualiza la diapositiva «Más allá de S2»'


def test_cifras_de_cuota_y_tiempos_documentados(html):
    for cifra in ('120', '180', '15 GB-mes', '20 GB-mes', '30 minutos', '30 días', '60 horas reales'):
        assert cifra in html, cifra


def test_los_pasos_estan_numerados_de_forma_consecutiva(html):
    n = [int(x) for x in re.findall(r'paso (\d+) de 8', html)]
    assert sorted(set(n)) == list(range(1, 9)), n


def test_las_fuentes_son_https_y_de_dominios_esperados():
    for titulo, url in G.FUENTES:
        p = urlparse(url)
        assert p.scheme == 'https' and p.netloc in ('docs.github.com', 'github.com', 'github.blog'), url
        assert titulo.strip()


def test_las_salidas_reales_son_las_esperadas():
    assert SALIDAS['listo']['salida'] == '{"estado":"listo"}'
    assert 'Todos los caminos dan la misma probabilidad.' in SALIDAS['comparar']['salida']
    assert 'DIFIERE' not in SALIDAS['comparar']['salida']
    assert SALIDAS['pipeline']['carpetas'].count('modelo_mlflow') == 1 and 'metadatos.json' in SALIDAS['pipeline']['carpetas']
    assert not any('/tmp/' in l for l in SALIDAS['pipeline']['ultimas_lineas']), 'la ruta temporal no debe llegar a la guía'


def test_la_palabra_prohibida_no_aparece(html, markdown):
    assert not PALABRA_PROHIBIDA.search(html)
    assert not PALABRA_PROHIBIDA.search(markdown)


def test_lo_generado_esta_al_dia(html, markdown):
    assert (AQUI / 'index.html').read_text(encoding='utf-8') == html, 'index.html está desactualizado: ejecuta python generar.py'
    assert G.SALIDA_MD.read_text(encoding='utf-8') == markdown, 'la guía en Markdown está desactualizada: ejecuta python generar.py'


def test_hay_marcas_de_progreso_y_enlace_al_indice_de_s2(html):
    assert html.count('class="slide"') >= 20
    assert 'href="../../01-Sesiones/S2-API-y-Docker/index.html"' in html
    assert (RAIZ / '01-Sesiones' / 'S2-API-y-Docker' / 'index.html').exists()
