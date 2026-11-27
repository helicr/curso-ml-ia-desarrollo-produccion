"""Pruebas de la clase «Fundamentos de la IA, los LLM, los RAG y los agentes» (index.html y glosario.md).

Se ejecutan solo con esta carpeta:  python -m pytest pruebas -q
No necesitan red ni navegador: comprueban el HTML generado, los cálculos de los ejemplos (recalculados aquí por su cuenta) y que
las cifras coinciden con los notebooks y guías del repositorio del curso.
"""
import html as htmllib
import importlib.util
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import pytest

CLASE = Path(__file__).resolve().parents[1]
S5 = CLASE.parent
EXTRA = S5 / 'extra-mcp-notebooks'
LAB = S5 / 'laboratorio-agentes'
INDEX = CLASE / 'index.html'
GLOSARIO_MD = CLASE / 'glosario.md'
GENERAR = CLASE / 'generar.py'


@pytest.fixture(scope='module')
def doc():
    return INDEX.read_bytes().decode('utf-8')


@pytest.fixture(scope='module')
def gen():
    spec = importlib.util.spec_from_file_location('generar_clase', GENERAR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope='module')
def slides(doc):
    """[(atributos, cuerpo_html)] de cada <section class="slide">."""
    res = []
    for m in re.finditer(r'<section class="slide"([^>]*)>(.*?)</section>', doc, re.S):
        attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', m.group(1)))
        res.append(({k: htmllib.unescape(v) for k, v in attrs.items()}, m.group(2)))
    return res


def texto(cuerpo):
    return htmllib.unescape(re.sub(r'<[^>]+>', ' ', cuerpo))


# ---------------------------------------------------------------- estructura
def test_numero_de_diapositivas(slides):
    assert 34 <= len(slides) <= 42, len(slides)


def test_cada_diapositiva_tiene_parte_titulo_y_minutos(slides, gen):
    for a, _ in slides:
        assert a['data-part'] in gen.PARTES
        assert a['data-title'].strip()
        assert a['data-min'].isdigit()


def test_barra_de_secciones_y_enlace_de_regreso(doc, gen):
    assert re.search(r'<a id="bhome" href="\.\./index\.html"', doc)
    assert len(re.findall(r'class="part" data-p="', doc)) == len(gen.PARTES)
    for k in gen.PARTES:                                   # cada sección tiene al menos una diapositiva
        assert f'data-part="{k}"' in doc
    assert '<html lang="es">' in doc


def test_visor_con_teclas_pantalla_completa_y_zoom(doc):
    assert "k==='s'||k==='S'" in doc          # notas con S
    assert "k==='f'||k==='F'" in doc          # pantalla completa
    assert 'requestFullscreen' in doc
    assert 'id="zoombox"' in doc and 'class="lupa"' in doc
    assert re.search(r"if\(k==='Escape'\)\{zoom\(false\)", doc)     # Esc cierra el zoom


def test_notas_del_profesor_en_todas(slides):
    for a, _ in slides:
        n = a['data-notes']
        assert 'Qué decir:' in n and 'Ejemplo:' in n and 'Pregunta para el aula:' in n, a['data-title']
        assert len(n) > 250, a['data-title']


def test_minutos_suman_60_65(slides):
    total = sum(int(a['data-min']) for a, _ in slides)
    assert 60 <= total <= 65, total


def test_agenda_de_la_portada_suma_lo_mismo(slides, gen):
    total = sum(int(a['data-min']) for a, _ in slides)
    portada = texto(slides[0][1])
    assert f'{total} min' in portada
    for k, nombre in gen.NOMBRES_PARTE.items():
        suma = sum(int(a['data-min']) for a, _ in slides if a['data-part'] == k)
        assert nombre in portada and f'{suma} min' in portada


def test_una_sola_h1_por_diapositiva_y_pocas_palabras(slides):
    for a, cuerpo in slides:
        assert cuerpo.count('<h1>') == 1
    # «pocas palabras»: ninguna diapositiva se acerca a una pared de texto (las fuentes son la excepción de listado)
    for a, cuerpo in slides:
        if a['data-title'] == 'Fuentes':
            continue
        assert len(texto(cuerpo).split()) < 330, (a['data-title'], len(texto(cuerpo).split()))


# ---------------------------------------------------------------- aspecto
def test_fondo_blanco(doc):
    assert '--fondo:#ffffff' in doc
    assert re.search(r'#stage\{[^}]*background:var\(--fondo\)', doc)
    assert re.search(r'\.slide\{[^}]*background:var\(--fondo\)', doc)


def test_nada_con_hover_que_mueva(doc):
    css = re.search(r'<style>(.*?)</style>', doc, re.S).group(1)
    for regla in re.findall(r'([^{}]*:hover[^{}]*)\{([^}]*)\}', css):
        assert not re.search(r'transform|translate|scale|margin|padding|width|height|top|left|animation|transition', regla[1]), regla
    assert ':hover' not in css                 # en esta clase no hay ninguna
    assert '@keyframes' not in css and 'animation:' not in css


def test_ids_unicos(doc):
    ids = re.findall(r'\sid="([^"]+)"', doc)
    repetidos = {i for i in ids if ids.count(i) > 1}
    assert not repetidos, repetidos             # los marcadores de flecha de cada SVG no se pisan entre diapositivas


def test_utf8_sin_mojibake():
    for p in (INDEX, GLOSARIO_MD, GENERAR):
        t = p.read_bytes().decode('utf-8')      # falla si no es UTF-8
        for malo in ('Ã', 'â€', '�', 'Â«', 'Â»'):
            assert malo not in t, (p.name, malo)
        assert 'ó' in t and 'ñ' in t or p == GENERAR


def test_sin_cdn_ni_recursos_externos(doc):
    assert not re.search(r'<script[^>]+src=', doc)
    assert not re.search(r'<link[^>]+href=', doc)
    assert not re.search(r'<img[^>]+src="https?:', doc)
    assert not re.search(r'@import|url\(\s*["\']?https?:', doc)


def test_html_actualizado_con_generar():
    r = subprocess.run([sys.executable, str(GENERAR), '--comprobar'], capture_output=True, text=True, encoding='utf-8')
    assert r.returncode == 0, r.stdout + r.stderr


# ---------------------------------------------------------------- glosario
def test_cada_termino_del_glosario_aparece_en_la_clase(doc, gen):
    bajo = doc.lower()
    faltan = [t['busca'] for t in gen.GLOSARIO if t['busca'].lower() not in bajo]
    assert not faltan, faltan


def test_glosario_md_completo_y_ordenado(gen):
    md = GLOSARIO_MD.read_bytes().decode('utf-8')
    for t in gen.GLOSARIO:
        assert f'### {t["term"]}' in md, t['term']
    niveles = [int(n) for n in re.findall(r'^## (\d+)\. ', md, re.M)]
    assert niveles == sorted(niveles) and niveles[0] == 1                       # de lo general a lo concreto
    assert [t['nivel'] for t in gen.GLOSARIO] == sorted(t['nivel'] for t in gen.GLOSARIO)
    for obligado in ['IA', 'ML', 'DL', 'red neuronal', 'transformer', 'token', 'embedding', 'vector', 'similitud', 'ventana de contexto', 'prompt',
                     'temperatura', 'alucinación', 'fine-tuning', 'LoRA', 'RAG', 'chunk', 'reranker', 'base vectorial', 'function calling',
                     'herramienta', 'MCP', 'skill', 'agente', 'ReAct', 'workflow', 'multiagente', 'guardrail', 'humano en el bucle',
                     'inyección de prompt', 'evaluación', 'traza', 'LLMOps', 'champion']:
        assert obligado.lower() in md.lower(), obligado
    assert 'En nuestro caso' in md and '12369' in md


# ---------------------------------------------------------------- capturas
def test_cada_captura_tiene_rotulo_y_archivo_o_es_pendiente(doc, gen):
    figs = re.findall(r'<figure class="cap" data-img="([^"]+)">(.*?)</figure>', doc, re.S)
    assert figs, 'no hay capturas'
    usadas = set()
    for nombre, cuerpo in figs:
        usadas.add(nombre)
        rotulo = gen.CAPTURAS[nombre]
        assert htmllib.escape(rotulo, quote=True) in cuerpo                       # el rótulo es el de la tabla, exacto
        if 'class="zoom"' in cuerpo:                                              # real
            assert (CLASE / 'img' / nombre).is_file(), nombre
            assert 'Captura real' in cuerpo and 'Pendiente' not in cuerpo
            assert f'src="img/{nombre}"' in cuerpo
        else:                                                                     # pendiente
            assert 'class="pend"' in cuerpo and 'Captura pendiente' in cuerpo and 'class="tag warn">Pendiente' in cuerpo
            assert 'Captura real' not in cuerpo
    assert usadas == set(gen.CAPTURAS), set(gen.CAPTURAS) - usadas


def test_las_capturas_son_imagenes_validas_y_sin_correo():
    from PIL import Image
    for p in (CLASE / 'img').glob('*.webp'):
        with Image.open(p) as im:
            assert im.format == 'WEBP' and im.size[0] >= 800 and im.size[1] >= 500, p.name
    for p in (CLASE / 'img').iterdir():
        assert p.suffix == '.webp', p.name


def test_las_capturas_reales_no_enseñan_correo_ni_proyecto_en_el_texto(doc):
    cuerpo = re.sub(r'<script>.*?</script>', '', doc, flags=re.S)
    assert '@gmail.com' not in cuerpo and 'project-curso-ml-ia' not in cuerpo
    assert not re.search(r'[\w.]+@[\w.]+\.(com|es)', cuerpo)


# ---------------------------------------------------------------- «sin verificar» y fuentes
PERMITIDAS_SIN_VERIFICAR = {'El bucle ReAct con nuestro caso', 'Arquitectura de referencia', 'GCP: modelos y Studio', 'Fuentes'}


def test_sin_verificar_solo_donde_toca(slides):
    donde = {a['data-title'] for a, c in slides if 'sin verificar' in (texto(c) + a['data-notes']).lower()}
    assert donde, 'debe constar lo que no se pudo comprobar'
    assert donde <= PERMITIDAS_SIN_VERIFICAR, donde - PERMITIDAS_SIN_VERIFICAR


def test_cada_url_de_fuentes_aparece_y_las_de_las_notas_estan_en_fuentes(doc, slides, gen):
    fuentes = next(c for a, c in slides if a['data-title'] == 'Fuentes')
    urls_fuentes = set(re.findall(r'href="(https?://[^"]+)"', fuentes))
    assert len(urls_fuentes) >= 25
    assert urls_fuentes == {u for _, u in gen.FUENTES.values()}
    for u in urls_fuentes:
        assert u in doc
        assert u.startswith('https://')
    for a, c in slides:
        if a['data-title'] == 'Fuentes':
            continue
        for u in re.findall(r'https?://[^\s;,)<"]+', a['data-notes'] + texto(c)):
            u = u.rstrip('.')
            assert u in urls_fuentes, (a['data-title'], u)


def test_afirmaciones_de_google_cloud_llevan_su_url_en_las_notas(slides):
    for a, c in slides:
        if a['data-title'].startswith('GCP:'):
            assert 'https://docs.cloud.google.com/' in a['data-notes'], a['data-title']


def test_hitos_de_la_linea_de_tiempo_tienen_fuente(slides, gen):
    c = next(c for a, c in slides if a['data-title'] == 'Siete hitos con fuente')
    for y, _, _, k, _ in gen.HITOS:
        assert y in c
        assert FUENTE_VISIBLE(gen, k) in c


def FUENTE_VISIBLE(gen, k):
    return gen.FUENTES[k][1].replace('https://', '')


# ---------------------------------------------------------------- cifras de los ejemplos
def coseno(a, b):
    return sum(x * y for x, y in zip(a, b)) / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


def coma(x, d):
    return f'{x:.{d}f}'.replace('.', ',')


def test_similitud_coseno_recalculada(slides):
    c = texto(next(c for a, c in slides if a['data-title'] == 'Similitud del coseno'))
    q = (4, 3, 0)
    esperado = {'Retención a 90 días: qué es': (5, 2, 1), 'Política de devoluciones': (1, 4, 2), 'Receta de paella': (0, 1, 6)}
    for nombre, v in esperado.items():
        assert nombre in c
        assert coma(coseno(q, v), 3) in c, (nombre, coseno(q, v))
    assert (coma(coseno(q, (5, 2, 1)), 3), coma(coseno(q, (1, 4, 2)), 3), coma(coseno(q, (0, 1, 6)), 3)) == ('0,949', '0,698', '0,099')
    # la cuenta paso a paso
    assert 'a·b = 4·5 + 3·2 + 0·1 = 26' in c and '√30 = 5,477' in c


def test_temperatura_softmax_recalculada(slides):
    c = texto(next(c for a, c in slides if a['data-title'] == 'Genera token a token'))
    logits = [3.0, 2.0, 1.2, 0.4, -0.4]
    for t in (0.5, 1.0, 2.0):
        e = [math.exp(v / t) for v in logits]
        p = [round(100 * x / sum(e)) for x in e]
        assert abs(sum(p) - 100) <= 2
        for k, valor in enumerate(p):
            assert f'{valor} %' in c, (t, k, valor)
    assert 'Ilustración' in c and 'inventadas' in c


def _salida_notebook(ruta):
    nb = json.loads(ruta.read_text(encoding='utf-8'))
    out = []
    for celda in nb['cells']:
        for o in celda.get('outputs', []):
            out.append(''.join(o.get('text', [])) if 'text' in o else json.dumps(o.get('data', {}), ensure_ascii=False))
    return '\n'.join(out)


def test_cifras_del_cliente_12369_y_del_auc_coinciden_con_el_notebook_02(doc, gen):
    salida = _salida_notebook(EXTRA / '02_mcp_modelo_prediccion.ipynb')
    c = gen.CLIENTE
    assert f'valid_auc {c["valid_auc"]}' in salida and f'test_auc {c["test_auc"]}' in salida
    assert '@champion' in salida and 'v6' in salida
    assert f'"cliente_id": {c["id"]}' in salida and f'"probabilidad": {c["prob"]}' in salida and f'"tramo": "{c["tramo"]}"' in salida
    assert f'recencia_dias\': {c["recencia"]}' in salida and f"'frecuencia': {c['frecuencia']}" in salida
    # el logit total del notebook reproduce la probabilidad
    logit = float(re.search(r'logit total ([+-][\d.]+)', salida).group(1))
    assert abs(1 / (1 + math.exp(-logit)) - float(c['prob'])) < 5e-4
    # en la clase
    assert coma(float(c['prob']), 4) in doc and coma(float(c['valid_auc']), 4) in doc and coma(float(c['test_auc']), 4) in doc
    assert f'"probabilidad": {c["prob"]}' in htmllib.unescape(doc)                       # el JSON de la diapositiva del prompt
    # AUC 0,70 / 0,75 solo como redondeo de las cifras reales y citando S1/S2
    assert coma(round(float(c['valid_auc']), 2), 2) == '0,70' and coma(round(float(c['test_auc']), 2), 2) == '0,75'
    assert 'AUC 0,70 · 0,75' in doc and 'S1/S2 del curso, 04-Proyecto-Base' in doc


def test_traza_react_coincide_con_el_notebook_01(doc, gen):
    salida = _salida_notebook(EXTRA / '01_mcp_datos_sqlite_y_bigquery.ipynb')
    c = gen.CLIENTE
    assert '"cliente_id": 12369' in salida and f'"pais": "{c["pais"]}"' in salida
    assert f'"facturas": {c["facturas"]}' in salida and f'"monto_ventas": {c["monto"]}' in salida
    assert f'{c["pais"]}, {c["facturas"]} facturas, monto_ventas {coma(float(c["monto"]), 2)}' in doc


def test_nombres_de_herramientas_existen_en_los_servidores():
    datos = (EXTRA / 'fuentes' / 'mcp_datos.py').read_text(encoding='utf-8')
    modelo = (EXTRA / 'fuentes' / 'mcp_modelo.py').read_text(encoding='utf-8')
    for h in ('resumen_cliente', 'consulta_sql'):
        assert f"name='{h}'" in datos
    for h in ('predecir_cliente', 'por_que'):
        assert f"name='{h}'" in modelo


def test_afirmaciones_sobre_el_curso_estan_en_la_documentacion_del_repositorio():
    guia = (LAB / 'guia.md').read_bytes().decode('utf-8')
    readme = (EXTRA / 'README.md').read_bytes().decode('utf-8')
    assert '25 preguntas de oro' in guia and '12670' in guia and 'Sin claves, sin coste por llamada' in guia
    assert 'puerta de calidad' in guia.lower() and '**igual**' in guia and '**rechazada**' in guia and '**aceptada**' in guia
    assert '38 pruebas' in readme and '13 entradas rechazadas' in readme and 'maximum_bytes_billed' in readme
    assert 'no es un analizador de SQL' in readme.replace('Una expresión regular **no es un analizador de SQL**', 'no es un analizador de SQL')
    for wf in ('agente-ci.yml', 'agente-evaluar.yml', 'agente-nueva-version.yml', 'agente-rollback.yml'):
        assert (LAB / wf).is_file(), wf


# ---------------------------------------------------------------- autoevaluación
def test_autoevaluacion_con_respuestas_ocultas_y_sin_librerias(doc):
    assert doc.count('class="rev"') == 5
    assert len(re.findall(r'<div class="ans" hidden>', doc)) == 5
    assert 'ver respuesta' in doc
    assert not re.search(r'<script[^>]+src=', doc)


def test_notas_se_ven_con_la_tecla_s_y_hay_botones_de_copiar_no_necesarios(doc):
    assert 'id="notes"' in doc and 'id="bnotes"' in doc
