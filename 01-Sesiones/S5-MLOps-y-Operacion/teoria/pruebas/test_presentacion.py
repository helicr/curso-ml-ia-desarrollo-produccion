"""Pruebas de la presentación «MLOps y operación» (teoría de S5, index.html).

Se ejecutan solo con esta carpeta:  python -m pytest pruebas -q
No necesitan red ni navegador: comprueban el HTML generado, que los enlaces locales existen, que cada orden copiable y cada cifra salen de
archivos reales del repositorio (se leen aquí), y que los números de la ilustración coinciden con su cálculo (recalculado por su cuenta).
"""
import html as htmllib
import importlib.util
import json
import math
import re
from pathlib import Path

import pytest

TEORIA = Path(__file__).resolve().parents[1]
S5 = TEORIA.parent
CURSO = S5.parent.parent
BASE = CURSO / '04-Proyecto-Base'
INDEX = TEORIA / 'index.html'
GENERAR = TEORIA / 'generar.py'


def leer(p):
    return Path(p).read_bytes().decode('utf-8')


@pytest.fixture(scope='module')
def doc():
    return leer(INDEX)


@pytest.fixture(scope='module')
def gen():
    spec = importlib.util.spec_from_file_location('generar_teoria_s5', GENERAR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope='module')
def slides(doc):
    res = []
    for m in re.finditer(r'<section class="slide"([^>]*)>(.*?)</section>', doc, re.S):
        attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', m.group(1)))
        res.append(({k: htmllib.unescape(v) for k, v in attrs.items()}, m.group(2)))
    return res


def texto(cuerpo):
    return htmllib.unescape(re.sub(r'<[^>]+>', ' ', cuerpo))


def por_titulo(slides, titulo):
    return next(c for a, c in slides if a['data-title'] == titulo)


# Fuentes del repositorio que se leen para comprobar órdenes y cifras
GUIA_A = leer(S5 / 'laboratorio-mlops' / 'guia.md')
GUIA_B = leer(S5 / 'laboratorio-agentes' / 'guia.md')
MLOPS_DOC = leer(BASE / 'docs' / 'mlops-clasico.md')
API_DOC = leer(BASE / 'docs' / 'api-y-contenedor.md')
README_TEORIA = leer(TEORIA / 'README.md')
TAREA = leer(S5 / 'tarea' / 'README.md')
README_S5 = leer(S5 / 'README.md')
GUION = leer(S5 / 'guion.md')
S4_GUIA = leer(CURSO / '01-Sesiones' / 'S4-Orquestacion-y-CI-CD' / 'laboratorio-produccion-e2e' / 'guia.md')
CONFIG_REPO = leer(S5 / 'laboratorio-agentes' / 'CONFIGURAR-REPOSITORIO.md')
PREPARAR = leer(BASE / 'deploy' / 'gcp' / 'preparar_proyecto.sh')
REFERENCIA = json.loads(leer(BASE / 'models' / 'referencia.json'))
HISTORIAL = json.loads(leer(BASE / 'models' / 'historial_versiones.json'))


# ---------------------------------------------------------------- estructura
def test_numero_de_diapositivas(slides):
    assert 20 <= len(slides) <= 26, len(slides)


def test_cada_diapositiva_tiene_parte_titulo_y_minutos(slides, gen):
    for a, _ in slides:
        assert a['data-part'] in gen.PARTES
        assert a['data-title'].strip()
        assert a['data-min'].isdigit()


def test_una_sola_h1_y_pocas_palabras(slides):
    for a, cuerpo in slides:
        assert cuerpo.count('<h1>') == 1
        assert len(texto(cuerpo).split()) < 330, (a['data-title'], len(texto(cuerpo).split()))


def test_minutos_20_a_30(slides):
    total = sum(int(a['data-min']) for a, _ in slides)
    assert 20 <= total <= 30, total


def test_barra_de_secciones_y_enlace_de_regreso(doc, gen):
    assert re.search(r'<a id="bhome" href="\.\./index\.html"', doc)
    assert (S5 / 'index.html').is_file()
    assert len(re.findall(r'class="part" data-p="', doc)) == len(gen.PARTES)
    for k in gen.PARTES:
        assert f'data-part="{k}"' in doc
    assert '<html lang="es">' in doc


def test_visor_con_teclas_pantalla_completa_y_zoom(doc):
    assert "k==='s'||k==='S'" in doc
    assert "k==='f'||k==='F'" in doc and 'requestFullscreen' in doc
    assert 'id="zoombox"' in doc and 'class="zsv lupa"' in doc
    assert re.search(r"if\(k==='Escape'\)\{zoom\(false\)", doc)


def test_notas_del_profesor_en_todas(slides):
    for a, _ in slides:
        n = a['data-notes']
        assert 'Qué decir:' in n and 'Ejemplo:' in n and 'Pregunta para el aula:' in n, a['data-title']
        assert len(n) > 250, a['data-title']
    assert 'id="notes"' in leer(INDEX) and 'Notas del profesor' in leer(INDEX)


def test_index_al_dia(gen, doc):
    assert gen.html_completo() == doc, 'ejecuta python generar.py'


def test_las_cinco_preguntas_y_ocho_mensajes(slides):
    t = texto(por_titulo(slides, 'Cinco preguntas'))
    for q in ('¿Qué está', '¿Con qué se', '¿Sigue', '¿Cómo lo', 'cambio', 'deshago'):
        assert q in t
    assert por_titulo(slides, 'Resumen').count('class="card kpi"') == 8


# ---------------------------------------------------------------- aspecto
def test_fondo_blanco(doc):
    assert '--fondo:#ffffff' in doc
    assert re.search(r'#stage\{[^}]*background:var\(--fondo\)', doc)
    assert re.search(r'\.slide\{[^}]*background:var\(--fondo\)', doc)


def test_sin_hover_ni_animaciones(doc):
    css = re.search(r'<style>(.*?)</style>', doc, re.S).group(1)
    assert ':hover' not in css and '@keyframes' not in css and 'animation:' not in css and 'transition' not in css


def test_ids_unicos(doc):
    ids = re.findall(r'\sid="([^"]+)"', doc)
    assert not {i for i in ids if ids.count(i) > 1}


# ---------------------------------------------------------------- higiene
def test_sin_mojibake_cdn_rutas_personales_proxies_ni_identificadores(doc):
    assert not re.search('[ÃÂ�]|â€', doc)
    assert 'http://' not in doc.replace('http://127.0.0.1:8080/listo', '') and 'https://' not in doc
    assert not re.search(r'<script[^>]+src=|<link[^>]+href=|@import|cdn\.', doc)
    assert not re.search(r'[A-Za-z]:\\|/Users/|/home/|BK70827|helicr', doc)
    assert not re.search(r'proxy|:3128|:8080/(?!listo)|zscaler', doc, re.I)
    assert not re.search(r'[\w.+-]+@[\w-]+\.[a-z]{2,}', doc)                       # correos
    assert not re.search(r'[0-9A-F]{6}-[0-9A-F]{6}-[0-9A-F]{6}', doc)               # cuenta de facturación
    assert not re.search(r'\b(gho|ghp|github_pat)_\w+', doc)                         # tokens
    for h in set(re.findall(r'\b[0-9a-f]{16}\b', doc)):                               # huellas permitidas (las de los archivos)
        assert h in GUIA_A + GUIA_B + json.dumps(REFERENCIA), h


def test_enlaces_locales_existen(doc):
    hrefs = re.findall(r'href="([^"]+)"', doc)
    locales = [h for h in hrefs if not h.startswith('#')]
    assert locales
    for h in locales:
        assert not re.match(r'[a-z]+:', h), h
        assert (TEORIA / h.split('#')[0]).resolve().is_file(), h
    for h in ('../laboratorio-mlops/index.html', '../laboratorio-agentes/index.html', '../clase-fundamentos-ia-agentes/index.html', '../index.html'):
        assert h in hrefs or h in doc


# ---------------------------------------------------------------- órdenes copiables salen de archivos reales
def test_cada_orden_copiable_esta_en_el_repositorio(doc):
    ordenes = [htmllib.unescape(t) for t in re.findall(r'class="cp" data-t="([^"]+)"', doc)]
    assert len(ordenes) >= 9
    corpus = GUIA_A + GUIA_B + MLOPS_DOC + API_DOC
    for o in ordenes:
        assert o in corpus, o
    assert doc.count('title="Copiar esta orden">COPIAR<') == len(ordenes)


def test_cada_bloque_de_ordenes_tiene_boton_copiar(doc):
    for m in re.finditer(r'<div class="tln">(.*?)</div>', doc, re.S):
        assert 'class="cp"' in m.group(1)


# ---------------------------------------------------------------- cifras reales y su fuente
CIFRAS = [
    # (texto en la presentación, archivo con el dato, texto en ese archivo)
    ('35a94deb4e04ab4a', 'referencia.json', '"huella_datos": "35a94deb4e04ab4a"'),
    ('retencion-api:v1-', 'referencia.json', '"etiqueta_imagen": "retencion-api:v1-35a94deb4e04ab4a"'),
    ('0,747', 'referencia.json', '0.747092830088378'),
    ('2026-11-13T17:04:12', 'referencia.json', '2026-11-13T17:04:12'),
    ('2026-11-22T13:26:32', 'referencia.json', '2026-11-22T13:26:32'),
    ('produccion', 'historial', '"estado": "produccion"'),
    ('0,8497', 'guia_a', '0.8497'), ('0,6982', 'guia_a', '0.6982'), ('0,7534', 'guia_a', '0.7534'), ('0,7423', 'guia_a', '0.7423'),
    ('0,1515', 'guia_a', '0.1515'), ('0,05', 'guia_a', 'tolerancia 0.05'),
    ('2,830', 'guia_a', '2.830'), ('0,736', 'guia_a', '0.736'), ('0,437', 'guia_a', '0.437'), ('0,259', 'guia_a', '0.259'),
    ('0,400', 'guia_a', '0.400'), ('0,240', 'guia_a', '0.240'), ('0,293', 'guia_a', '0.293'), ('0,213', 'guia_a', '0.213'),
    ('0,276', 'guia_a', '0.276'), ('0,010', 'guia_a', '0.010'),
    ('5 de 13', 'guia_a', '5 de 13'), ('109 clientes', 'guia_a', '109 clientes'), ('148 clientes', 'guia_a', '148 clientes'),
    ('0,7855', 'guia_a', '0.7855'), ('0,7956', 'guia_a', '0.7956'), ('0,7471', 'guia_a', '0.7471'),
    ('3521a0421905ba28', 'guia_a', '3521a0421905ba28'), ('0,8279', 'guia_a', '0.8279'), ('0,7245', 'guia_a', '0.7245'),
    ('0,0001', 'guia_a', '0.0001'), ('0,10', 'guia_a', '0,10'), ('0,25', 'guia_a', '0,25'),
    ('0,02', 's4', '0,02'), ('2,1 GB', 'guia_b', '2,1 GB'),
    ('e90daa8a20bef846', 'guia_b', 'e90daa8a20bef846'),
    ('64 %', 'guia_b', '**64 %**'), ('96 %', 'guia_b', '**96 %**'), ('76 %', 'guia_b', '76 %'), ('50 %', 'guia_b', '**50 %**'), ('44 %', 'guia_b', '44 %'),
    ('80 %', 'guia_b', '**80 %**'), ('86 %', 'guia_b', '**86 %**'),
    ('45067472249', 'guia_b', '45067472249'), ('45277896553', 'guia_b', '45277896553'), ('45278456252', 'guia_b', '45278456252'),
    ('0,10', 'guia_b', '0,10'), ('13 min 37 s', 'guia_b', '13 min 37 s'),
    ('11 de diciembre', 'tarea', '11 de diciembre'), ('10:00', 'tarea', '10:00'),
    ('~50 min', 'guion', '| 50 |'), ('~110 min', 'guion', '| 10 |'),
]
FUENTE_CIFRA = {'referencia.json': json.dumps(REFERENCIA, indent=2) + leer(BASE / 'models' / 'referencia.json'), 'historial': leer(BASE / 'models' / 'historial_versiones.json'),
                'guia_a': GUIA_A, 'guia_b': GUIA_B, 's4': S4_GUIA, 'tarea': TAREA, 'guion': GUION}


@pytest.mark.parametrize('en_deck,fuente,en_fuente', CIFRAS)
def test_cada_cifra_sale_de_su_archivo(doc, slides, en_deck, fuente, en_fuente):
    cuerpo = ' '.join(texto(c) for _, c in slides) + ' ' + ' '.join(a['data-notes'] for a, _ in slides)
    assert en_deck in cuerpo or en_deck in doc, f'{en_deck} no está en la presentación'
    assert en_fuente in FUENTE_CIFRA[fuente], f'{en_fuente} no está en {fuente}'


def test_composicion_de_las_25_preguntas_de_oro(doc, gen):
    assert sum(n for _, n in gen.PREGUNTAS_ORO) == 25
    assert '`n01`…`n11`' in GUIA_B and '`t01`…`t06`' in GUIA_B and '`s01`…`s05`' in GUIA_B and '`m01`…`m03`' in GUIA_B
    assert '11 **normales**' in GUIA_B and '6 **trampas**' in GUIA_B and '5 de **seguridad**' in GUIA_B and '3 de **sentido**' in GUIA_B
    assert 'aria-label="25 preguntas de oro: 11 normales, 6 trampas, 5 de seguridad y 3 de sentido"' in doc


def test_la_ficha_y_el_historial_coinciden_con_la_diapositiva(slides, gen):
    assert REFERENCIA['huella_datos'] == gen.HUELLA == '35a94deb4e04ab4a'
    assert REFERENCIA['etiqueta_imagen'] == gen.ETIQUETA
    assert REFERENCIA['version'] == 1 and HISTORIAL['versiones'][0]['estado'] == 'produccion'
    assert abs(REFERENCIA['metricas_test']['auc'] - gen.AUC_TEST) < 1e-12
    assert REFERENCIA['entrenado_en'] == gen.ENTRENADO and REFERENCIA['aprobado_en'] == gen.APROBADO
    t = texto(por_titulo(slides, 'De la imagen a la ficha'))
    assert gen.ETIQUETA.split(':')[0] in t and REFERENCIA['huella_datos'] in t


def test_cifras_de_los_graficos_coinciden_con_la_guia(gen):
    for corte, uso, auc in gen.AUC_CORTES:
        assert f'{corte}  ' in GUIA_A and f'{auc:.4f}' in GUIA_A
    for v, p, k in gen.PSI_REALES:
        assert re.search(rf'{v}\s+{p.replace(",", ".")}\s+{k.replace(",", ".")}', GUIA_A), v
    assert dict((n.replace('\n', ' '), v) for n, v in gen.EVAL_PRIMERA) == {'Herramienta': 76, 'Sin inventar': 64, 'Trampas': 50, 'Respuestas correctas': 44}
    assert gen.EVAL_CORREGIDA == [80, 96, 86, 76]
    assert 'La primera dio 76 % de herramienta, **64 %** sin inventar, **50 %** de trampas y 44 % de respuestas correctas' in GUIA_B
    assert 'Tras corregirlo: 80 % de herramienta, 96 % sin inventar, 86 % de trampas y 76 % de respuestas correctas' in GUIA_B


def test_la_teoria_original_sigue_diciendo_lo_mismo():
    for frase in ('0,747', '`35a94deb4e04ab4a`', '`e90daa8a20bef846`', 'sin dato', 'convención'):
        assert frase in README_TEORIA


# ---------------------------------------------------------------- ilustración: números = cálculo independiente
def test_ilustracion_coincide_con_su_calculo(slides, gen):
    p = [0.20] * 5
    q = [0.10, 0.15, 0.20, 0.25, 0.30]
    aportes = [(b - a) * math.log(b / a) for a, b in zip(p, q)]
    psi = sum(aportes)
    cp = cq = ks = 0.0
    for a, b in zip(p, q):
        cp += a
        cq += b
        ks = max(ks, abs(cp - cq))
    assert gen.ILU_REF == p and gen.ILU_ACT == q
    assert abs(gen.psi(p, q) - psi) < 1e-12 and abs(gen.ks(p, q) - ks) < 1e-12
    cuerpo = por_titulo(slides, 'Ilustración PSI')
    t = texto(cuerpo)
    for a in aportes:
        assert f'{a:.4f}'.replace('.', ',') in t
    assert f'{psi:.4f}'.replace('.', ',') in t and f'{psi:.3f}'.replace('.', ',') in t and f'{ks:.2f}'.replace('.', ',') in t
    assert 'ILUSTRACIÓN' in cuerpo and 'no son datos del curso' in cuerpo
    assert 0.10 <= psi < 0.25 and '«vigilar»' in t


def test_psi_de_la_guia_con_la_misma_formula():
    # el ejemplo de la guía del laboratorio A: referencia [1, 2, 3, 4], actual [1, 1, 1, 4], dos intervalos y suelo 0,0001
    suelo = 1e-4
    p = [0.5, 0.5, suelo]
    q = [0.75, 0.25, suelo]
    assert round(sum((b - a) * math.log(b / a) for a, b in zip(p, q)), 4) == 0.2747
    assert '0.2747' in GUIA_A and '0,2747' in GUIA_A


# ---------------------------------------------------------------- «sin verificar», «por confirmar», «sin dato»: solo donde toca
def test_marcadores_solo_donde_toca(slides):
    permitido = {'sin verificar': {'Alertas', 'Costes y orden', 'Fuentes'}, 'sin dato': {'Servicio y modelo', 'Alertas'}, 'por confirmar': {'Tarea y evidencia'},
                 'sin fuente': {'PSI y KS'}}
    for a, cuerpo in slides:
        t = texto(cuerpo).lower()
        for marca, donde in permitido.items():
            if re.search(re.escape(marca) + (r'(?!s)' if marca == 'sin dato' else ''), t):
                assert a['data-title'] in donde, (marca, a['data-title'])
    for marca, donde in permitido.items():
        for titulo in donde:
            assert re.search(re.escape(marca) + (r'(?!s)' if marca == 'sin dato' else ''), texto(por_titulo(slides, titulo)).lower()), (marca, titulo)


def test_los_marcadores_tienen_base_en_las_fuentes():
    assert 'sin verificar' in README_TEORIA.lower() and 'sin dato' in README_TEORIA.lower()
    assert 'sin dato' in GUIA_A and 'issues: write' in GUIA_A
    assert 'por decidir' in README_S5 or 'por confirmar' in README_S5.lower() or 'la que indique el instructor' in TAREA
    assert 'propuesta' in TAREA and '20 % reproducibilidad, 40 % técnica, 40 % análisis y decisión' in TAREA
    assert 'Una alerta AVISA, no corta el gasto' in PREPARAR
    assert 'avisa, no corta' in GUIA_A.lower()


def test_fechas_de_la_entrega_y_la_sesion(slides):
    assert 'viernes 11 de diciembre, a las 10:00 (hora de Perú)' in TAREA and 'viernes 11 de diciembre, a las 10:00 (hora de Perú)' in README_S5
    t = texto(por_titulo(slides, 'Tarea y evidencia'))
    assert '11 de diciembre' in t and '10:00' in t and 'hora de Perú' in t and 'avance-5' in TAREA and 'avance-5' in t
    assert 'viernes 27 de noviembre' in GUION


def test_minuto_a_minuto_de_la_portada_de_hoy(slides):
    t = texto(por_titulo(slides, 'Qué se hace hoy'))
    assert 'propuesta' in t and '~50 min' in t and '~110 min' in t
    assert (10 + 15 + 15 + 10 + 25 + 35) == 110                      # L1..L6 del guion (minutos propuestos)


# ---------------------------------------------------------------- autoevaluación sin librerías
def test_autoevaluacion_con_respuesta_oculta(slides, doc):
    c = por_titulo(slides, 'Autoevaluación')
    assert c.count('class="qa"') == 5 and c.count('hidden>') == 5 and c.count('class="rev"') == 5
    assert 'aria-expanded="false"' in c
    assert '.ans[hidden]{display:none}' in doc


def test_fuentes_listan_archivos_del_repositorio(slides, gen):
    c = por_titulo(slides, 'Fuentes')
    n = 0
    for _, items in gen.FUENTES_LOCALES:
        for h, _t in items:
            assert (TEORIA / h).resolve().is_file(), h
            assert f'href="{h}"' in c
            n += 1
    assert n >= 15
    assert 'http' not in c
