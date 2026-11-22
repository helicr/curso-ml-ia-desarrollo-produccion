"""Pruebas de la presentación «Un LLM y el estilo de color» (sin navegador).

Qué vigilan: que index.html está al día con generar.py; 60 minutos en total (A 5 · B 25 · C 20 · D 10); título, parte, minutos
y notas en cada diapositiva; que las órdenes citadas usan archivos, notebooks y parámetros que existen (y los mismos que el
workflow); que las salidas «reales» están de verdad en los notebooks; que todas las imágenes citadas existen; sin recursos
externos; el botón «⌂ S4»; y que las cifras clave coinciden con README.md y guia-pipeline.md.
El archivo se llama test_presentacion.py para no chocar con otros laboratorios (test_laboratorio.py).
"""
import importlib.util
import json
import re
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parents[1]
RAIZ = AQUI.parents[2]
README = AQUI / 'README.md'
GUIA = AQUI / 'guia-pipeline.md'
YML = AQUI / 'extra-estilo-llm.yml'

_spec = importlib.util.spec_from_file_location('generar_extra_estilo', AQUI / 'generar.py')
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)

NOTEBOOKS = ['00_preparar_entorno', '01_datos_fabricados', '02_zero_shot', '03_fine_tuning_lora',
             '04_comparar_y_transferir', '05_explicar_estilo']


@pytest.fixture(scope='module')
def html():
    return (AQUI / 'index.html').read_text(encoding='utf-8')


@pytest.fixture(scope='module')
def blob_notebooks():
    """Todo el texto de los notebooks: celdas de código y de texto y sus salidas de texto."""
    trozos = []
    for nb in NOTEBOOKS:
        datos = json.loads((AQUI / f'{nb}.ipynb').read_text(encoding='utf-8'))
        for celda in datos['cells']:
            trozos.append(''.join(celda['source']))
            for sal in celda.get('outputs', []):
                if 'text' in sal:
                    trozos.append(''.join(sal['text']))
                elif 'data' in sal and 'text/plain' in sal['data']:
                    trozos.append(''.join(sal['data']['text/plain']))
    return '\n'.join(trozos)


def secciones(texto):
    return re.findall(r'<section class="slide"([^>]*)>(.*?)</section>', texto, re.S)


def test_esta_al_dia_con_el_generador(html):
    assert html == G.html_completo(), 'index.html no coincide con generar.py: ejecuta  python generar.py'


def test_minutos_suman_60_y_cada_diapositiva_tiene_titulo_parte_minutos_y_notas(html):
    s = secciones(html)
    assert 22 <= len(s) <= 28
    total = 0
    for attrs, cuerpo in s:
        assert re.search(r'data-part="[A-D]"', attrs), attrs
        m = re.search(r'data-min="(\d+)"', attrs)
        assert m and int(m.group(1)) > 0, attrs
        total += int(m.group(1))
        t = re.search(r'data-title="([^"]+)"', attrs)
        assert t and t.group(1).strip(), attrs
        n = re.search(r'data-notes="([^"]*)"', attrs)
        assert n and len(n.group(1)) > 80, f'notas demasiado cortas en {t.group(1)}'
        assert cuerpo.count('<h1>') == 1
    assert total == 60 == G.DURACION


def test_minutos_por_parte():
    G.construir()
    por_parte = {}
    for s in G.SLIDES:
        por_parte[s['parte']] = por_parte.get(s['parte'], 0) + s['min']
    assert por_parte == {'A': 5, 'B': 25, 'C': 20, 'D': 10}


def test_hay_una_diapositiva_por_notebook_en_la_parte_b():
    G.construir()
    titulos = [s['titulo'] for s in G.SLIDES if s['parte'] == 'B']
    for n in range(6):
        assert f'Notebook 0{n}' in titulos, n


def test_sin_recursos_externos(html):
    assert not re.search(r'(src|href)="(https?:)?//', html)
    assert not re.search(r'@import|url\((["\']?)(https?:)?//', html)
    assert '<link' not in html and '<iframe' not in html
    for ruta in re.findall(r'(?:src|href|data-src)="([^"#]+)"', html):
        assert not ruta.startswith(('http', '//')), ruta


def test_boton_s4_al_indice_de_la_sesion(html):
    assert '<a id="bhome" href="../index.html"' in html and '⌂ S4' in html
    assert (AQUI.parent / 'index.html').exists()


def test_nada_se_mueve_al_pasar_el_raton(html):
    assert ':hover' not in html and 'transition' not in html and 'animation' not in html


def test_todas_las_imagenes_citadas_existen_y_estan_previstas(html):
    citadas = set(re.findall(r'(?:src|data-src)="img/([^"]+)"', html))
    pendientes = set(re.findall(r'data-falta="([^"]+)"', html))
    assert not pendientes, f'capturas pendientes: {pendientes}'
    assert citadas == set(G.CAPTURAS), 'cada imagen prevista debe salir en alguna diapositiva y viceversa'
    for nombre in citadas:
        assert (AQUI / 'img' / nombre).exists(), nombre
        assert (AQUI / 'img' / nombre).stat().st_size > 1000, nombre
    assert 'Captura pendiente' not in html


def test_hay_capturas_nuevas_p_de_cada_notebook():
    p = {n for n in G.CAPTURAS if n.startswith('p')}
    for n in range(6):
        assert any(x.startswith(f'p0{n}-') for x in p), n
    assert {'x01-grafo-actions.webp', 'x02-resumen-actions.webp', '04_panel_transferencia.png'} <= set(G.CAPTURAS)


def test_cada_orden_de_terminal_tiene_su_boton_de_copiar(html):
    usadas = 0
    for clave, orden in G.O.items():
        if f'data-t="{G.esc(orden)}"' in html:
            usadas += 1
    assert usadas == len(G.O), 'alguna orden de O no sale en ninguna diapositiva'


def test_las_ordenes_citan_archivos_y_notebooks_que_existen():
    texto = '\n'.join(G.O.values())
    for nb in set(re.findall(r'\b(\d\d_[a-z_]+\.ipynb)', texto)):
        assert (AQUI / nb).exists(), nb
    assert (AQUI / 'requisitos-extra-estilo.txt').exists() and 'requisitos-extra-estilo.txt' in texto
    assert (AQUI / 'extra-estilo-llm.yml').exists()
    assert (RAIZ / G.CARPETA).is_dir() and G.CARPETA == AQUI.relative_to(RAIZ).as_posix()
    assert G.O['cp'] == ('mkdir -p .github/workflows && cp 01-Sesiones/S4-Orquestacion-y-CI-CD/extra-estilo-llm/'
                         'extra-estilo-llm.yml .github/workflows/')
    assert G.YML == '.github/workflows/extra-estilo-llm.yml'
    assert G.YML in G.O['add'] and G.YML in G.O['curl']
    assert 'git switch -c lab/extra-estilo-llm' == G.O['rama'] and G.O['push'].endswith('lab/extra-estilo-llm')
    assert (RAIZ / G.CARPETA / 'extra-estilo-llm.yml').exists()


def test_los_papermill_usan_los_mismos_parametros_que_el_workflow():
    yml = YML.read_text(encoding='utf-8').replace('\\\n', ' ')
    for clave, nb in (('pm00', '00_preparar_entorno'), ('pm01', '01_datos_fabricados'), ('pm02', '02_zero_shot'),
                      ('pm03', '03_fine_tuning_lora'), ('pm04', '04_comparar_y_transferir'), ('pm05', '05_explicar_estilo')):
        orden = G.O[clave]
        assert orden.startswith(f'papermill {nb}.ipynb '), clave
        nombres_mios = set(re.findall(r'-p (\w+)', orden))
        lineas = [l for l in yml.splitlines() if f'papermill {nb}.ipynb' in l]
        assert lineas, nb
        if nb == '04_comparar_y_transferir':
            lineas = [l for l in lineas if 'ETAPA completo' in l]
        assert nombres_mios == set(re.findall(r'-p (\w+)', lineas[0])), (clave, nombres_mios)
        # cada parámetro existe en la celda `parameters` del notebook o lo inyecta el workflow igual
        datos = json.loads((AQUI / f'{nb}.ipynb').read_text(encoding='utf-8'))
        celda = next(''.join(c['source']) for c in datos['cells'] if 'parameters' in c['metadata'].get('tags', []))
        for nombre in nombres_mios - {'N_EJEMPLOS', 'EPOCAS', 'RESOLUCION', 'MODELO'}:
            assert nombre in celda, (nb, nombre)
    assert 'ESTILO_TRABAJO' in yml and 'HF_HOME' in yml
    assert 'ESTILO_TRABAJO' in G.O['vars'] and 'HF_HOME' in G.O['vars']
    assert 'HuggingFaceTB/SmolVLM-256M-Instruct' in G.O['params'] and 'HuggingFaceTB/SmolVLM-256M-Instruct' in yml
    assert 'N_FRASES 500 -p EPOCAS 2 -p FORMATO facil' in G.O['pm05']


def test_las_variables_de_entorno_citadas_las_leen_los_notebooks(blob_notebooks):
    for v in ('ESTILO_TRABAJO', 'ESTILO_N_EJEMPLOS', 'ESTILO_EPOCAS', 'ESTILO_TAR', 'ESTILO_EXTRA', 'HF_HOME'):
        assert v in blob_notebooks or v in (AQUI / 'estilo' / 'datos.py').read_text(encoding='utf-8'), v


def test_las_salidas_reales_estan_en_los_notebooks(blob_notebooks):
    normal = re.sub(r'[ \t]+', ' ', blob_notebooks)
    for clave, texto in G.SALIDAS.items():
        for linea in texto.splitlines():
            linea = re.sub(r'[ \t]+', ' ', linea.strip())
            if not linea or '…' in linea:
                continue
            assert linea in normal, (clave, linea)
    # los fragmentos con «…» se comprueban por partes
    for parte in ('La referencia es más luminosa, más magenta, con menos contraste y más saturada: se sube bastante la '
                  'exposición, se lleva el tinte bastante hacia el magenta',
                  'Ejemplo: Cambios: exposicion: sube bastante'):
        assert parte in blob_notebooks


def test_el_notebook_03_no_esta_ejecutado_y_la_presentacion_lo_dice(html):
    datos = json.loads((AQUI / '03_fine_tuning_lora.ipynb').read_text(encoding='utf-8'))
    codigo = [c for c in datos['cells'] if c['cell_type'] == 'code']
    assert not any(c.get('outputs') for c in codigo)
    assert 'Salida del estudio técnico del 20/11/2026' in ''.join(''.join(c['source']) for c in datos['cells'])
    assert G.ESTUDIO in html


def test_las_cifras_clave_coinciden_con_el_readme_y_la_guia(blob_notebooks):
    readme = README.read_text(encoding='utf-8') + blob_notebooks   # 791,9 MB solo figura en el notebook 00
    guia = GUIA.read_text(encoding='utf-8')
    for cifra in ('0,259', '0,433', '0,310', '0,151', '0,244', '0,229', '40,7 %', '58,3 %', '81,7 %', '18,3 %',
                  '10,0 %', '15,0 %', '1456 s', '1397 s', '7,06 MB', '493,9', '9,8 MB', '791,9', '2747 MB', '2887 MB',
                  '102 s', '51,7 s', RAIZ and G.RUN):
        assert cifra in readme or cifra in guia, cifra
    # tiempos por job: los mismos que la guía
    for tiempo in ('31 s', '2 min 1 s', '2 min 45 s', '3 min 32 s', '5 min 52 s', '1 min 49 s', '5 min 23 s', '2 min 41 s',
                   '6 s', '14 min 10 s', '13 artefactos'):
        assert tiempo in guia, tiempo
    G.construir()
    todo = ' '.join(s['html'] for s in G.SLIDES)
    for tiempo in ('31 s', '2 min 1 s', '2 min 45 s', '3 min 32 s', '5 min 52 s', '1 min 49 s', '5 min 23 s', '2 min 41 s',
                   '14 min 10 s', G.RUN):
        assert tiempo in todo, tiempo


def test_los_artefactos_citados_son_los_del_workflow():
    yml = YML.read_text(encoding='utf-8')
    nombres = set(re.findall(r'name: ([\w-]+)', yml)) | set(re.findall(r'name: ([\w-]+),', yml))
    G.construir()
    todo = ' '.join(s['html'] for s in G.SLIDES)
    for a in ('nb-00-preparar', 'nb-01-datos', 'datos', 'nb-02-zero-shot', 'metricas-a', 'nb-03-lora', 'adaptador-lora',
              'nb-04-c-d', 'metricas-c-d', 'nb-05', 'explicacion', 'nb-04-comparar', 'comparacion'):
        assert a in nombres, a
        assert a in todo, a
    assert 'retention-days: 3' in yml and 'if: always()' in yml
    assert "branches: ['lab/**']" in yml


def test_checklist_de_actions_recogido():
    check = (AQUI / 'checklist-actions.md').read_text(encoding='utf-8')
    G.construir()
    todo = ' '.join(s['html'] for s in G.SLIDES if s['titulo'] == 'Si no aparece en Actions')
    for frase in ('.github/workflows/extra-estilo-llm.yml', 'lab/', 'Actions está activado', 'Raw'):
        assert frase in check and frase in todo, frase


def test_autoevaluacion_de_cuatro_preguntas(html):
    ultima = secciones(html)[-1][1]
    assert ultima.count('<details>') == 4


def test_sin_rutas_personales_ni_credenciales(html):
    for texto in (html, (AQUI / 'generar.py').read_text(encoding='utf-8')):
        assert 'C:\\Users' not in texto and 'AppData' not in texto and 'BK70827' not in texto
        assert not re.search(r'[\w.]+@[\w-]+\.(com|es|org)', texto)
        assert not re.search(r'(token|password|contraseña)\s*[:=]', texto, re.I)
        assert not re.search(r'ghp_|github_pat_', texto)
