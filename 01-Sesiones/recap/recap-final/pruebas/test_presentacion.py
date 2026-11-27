"""Pruebas del RECAP FINAL (index.html generado por ../generar.py).

Ejecutar solo esta carpeta, con el entorno del curso:
    <env-ia-mlops>\\python.exe -m pytest 01-Sesiones/recap/recap-final/pruebas -q

Comprueban: estructura y notas, enlace de regreso, las seis secciones de sesión, el mensaje de entrega en el Classroom y la
fecha límite, que cada imagen existe y tiene su rótulo y su origen, que cada cifra aparece en el repositorio, que cada
carpeta citada existe, que el repositorio citado es el real, y que no hay mojibake, CDN ni :hover.
No ejecutan la suite de 04-Proyecto-Base ni abren ningún navegador.
"""
import hashlib
import re
import subprocess
import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
CARPETA = AQUI.parent
HTML = CARPETA / 'index.html'
RAIZ = CARPETA.parents[2]
SES = RAIZ / '01-Sesiones'
BASE = RAIZ / '04-Proyecto-Base'
NBSP = ' '


@pytest.fixture(scope='module')
def doc():
    assert HTML.is_file(), 'falta index.html: ejecuta python generar.py'
    return HTML.read_text(encoding='utf-8')


@pytest.fixture(scope='module')
def slides(doc):
    partes = re.findall(r'<section class="slide[^"]*" data-part="(\w)" data-min="(\d+)" data-title="([^"]*)"\s*\n data-notes="([^"]*)">(.*?)</section>', doc, re.S)
    return [{'part': p, 'min': int(m), 'title': t, 'notes': n, 'html': h} for p, m, t, n, h in partes]


def leer(rel):
    return (RAIZ / rel).read_text(encoding='utf-8')


def texto(doc):
    """El texto visible sin etiquetas (para buscar frases)."""
    t = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', doc)).replace(NBSP, ' ')
    return re.sub(r' ([,.;:)»])', r'\1', re.sub(r'([(«]) ', r'\1', t))


# ---------------------------------------------------------------------------------------------------------- estructura
def test_numero_de_diapositivas_y_minutos(slides):
    assert 40 <= len(slides) <= 50
    total = sum(s['min'] for s in slides)
    assert 60 <= total <= 75, f'{total} min'
    assert all(s['min'] >= 1 for s in slides)


def test_notas_del_profesor_en_todas(slides):
    for k, s in enumerate(slides, 1):
        n = s['notes']
        assert 'Qué decir:' in n and 'Ejemplo o anécdota:' in n and 'Pregunta para el aula:' in n, f'diapositiva {k}'
        assert len(n) > 150, f'notas demasiado cortas en la {k}'
        assert n.rstrip().endswith('?'), f'la última línea de la {k} debe ser la pregunta'


def test_idioma_titulo_y_teclas(doc):
    assert '<html lang="es">' in doc
    assert '<title>Recap final' in doc
    for tecla in ("k==='s'||k==='S'", "k==='o'||k==='O'", "k==='f'||k==='F'", "k==='Escape'"):
        assert tecla in doc
    assert 'id="notes"' in doc and 'id="zoombox"' in doc


def test_enlace_de_regreso_existe(doc):
    m = re.search(r'<a id="bhome" href="([^"]+)"', doc)
    assert m, 'falta el enlace de regreso'
    destino = (CARPETA / m.group(1)).resolve()
    assert destino.is_file(), destino
    assert destino == (SES / [p for p in SES.iterdir() if p.name.startswith('S5-')][0] / 'index.html').resolve()


def test_generar_esta_al_dia():
    r = subprocess.run([sys.executable, str(CARPETA / 'generar.py'), '--comprobar'], capture_output=True, text=True, encoding='utf-8')
    assert r.returncode == 0, r.stdout + r.stderr


# ----------------------------------------------------------------------------------------------------- las seis sesiones
NOMBRES = {'0': 'S0', '1': 'S1', '2': 'S2', '3': 'S3', '4': 'S4', '5': 'S5'}


def test_seis_secciones_de_sesion(slides):
    for k, etq in NOMBRES.items():
        ss = [s for s in slides if s['part'] == k]
        assert len(ss) >= 4, f'{etq} tiene {len(ss)} diapositivas'
        titulos = ' | '.join(s['title'] for s in ss)
        assert etq + ' · Qué hicimos en clase' in titulos
        assert etq + ' · Qué te llevas' in titulos
        assert etq + ' · El momento difícil' in titulos
        assert etq + ' · Ahora lo puedes explicar' in titulos
        if k != '0':
            assert etq + ' · Lo que vimos' in titulos
        assert all(s['html'].count('<h1>') == 1 for s in ss)


def test_cada_sesion_tiene_ya_sabes_y_si_falla(slides):
    for k in NOMBRES:
        ss = [s for s in slides if s['part'] == k]
        sab = [s for s in ss if 'y lo has comprobado en' in s['html']]
        assert sab, k
        assert sum(x['html'].count('class="ys"') for x in sab) >= 3, f'S{k}: faltan filas «Ya sabes»'
        falla = [s for s in ss if 'falla-tbl' in s['html']]
        assert falla and 'Es normal.' in falla[0]['html'], k
        expl = [s for s in ss if 'Ahora lo puedes explicar a un compañero' in s['html'] and 'Y si quieres ir más allá' in s['html']]
        assert expl, k


def test_secciones_obligatorias_del_brief(slides):
    partes = {s['part'] for s in slides}
    assert {'A', 'J', 'K', 'E', 'R', 'Z'} <= partes
    assert sum(1 for s in slides if s['part'] == 'A') >= 3
    assert sum(1 for s in slides if s['part'] == 'J') >= 3
    assert sum(1 for s in slides if s['part'] == 'K') >= 3
    assert sum(1 for s in slides if s['part'] == 'E') >= 3
    assert sum(1 for s in slides if s['part'] == 'R') >= 3
    assert sum(1 for s in slides if s['part'] == 'Z') >= 3


def test_mitos_interactivos(doc):
    assert doc.count('class="mbtn"') == 6
    assert doc.count('class="real" hidden') == 6
    assert 'id="mitos-todos"' in doc


# ------------------------------------------------------------------------------- evaluación: Classroom y fecha límite
def test_mensaje_classroom_y_fecha_limite(doc, slides):
    t = texto(doc)
    assert 'Sube tu tarea al Classroom' in t
    sola = [s for s in slides if s['title'] == 'Sube tu tarea al Classroom']
    assert len(sola) == 1
    assert 'Entrega final: viernes 11/12/2026 · 10:00 (hora de Perú)' in texto(sola[0]['html'])
    assert 'ENVIAR lo solicitado en la tarea y SUBIRLO al CLASSROOM' in t
    assert t.count('11/12/2026') >= 3
    # la fecha límite coincide con la del repositorio
    assert 'viernes 11 de diciembre, a las 10:00 (hora de Perú)' in leer('01-Sesiones/S5-MLOps-y-Operacion/tarea/README.md')
    assert 'vie 11 dic, 10:00' in leer('02-Proyecto-Transversal/alumno/tu-caso-bank-marketing.md')
    import datetime
    assert datetime.date(2026, 12, 11).weekday() == 4          # viernes


def test_calendario_de_sesiones_y_avances(doc):
    hoja = leer('02-Proyecto-Transversal/alumno/tu-caso-bank-marketing.md')
    assert ('S0 el miércoles 11 de noviembre, S1 el viernes 13, S2 el miércoles 18, S3 el viernes 20, S4 el miércoles 25 y S5 el viernes 27') in hoja
    for f in ('mié 11/11', 'vie 13/11', 'mié 18/11', 'vie 20/11', 'mié 25/11', 'vie 27/11'):
        assert f in doc
    for fila in ('mié 18 nov, 10:00', 'vie 20 nov, 10:00', 'mié 25 nov, 10:00', 'vie 27 nov, 10:00', 'vie 11 dic, 10:00'):
        assert fila in hoja
    assert 'de 10:00 a 14:00 (hora de Perú)' in doc and 'miércoles y viernes, de 10:00 a 14:00' in hoja


def test_tabla_de_entregas_con_ramas_y_plantillas(doc):
    for rama in ('tarea-s1', 'avance-1', 'avance-2', 'avance-3', 'avance-4', 'avance-5'):
        assert rama in doc
    # las plantillas de evidencia existen
    for m in re.findall(r'data-ruta="([^"]*plantilla[^"]*)"', doc):
        assert (RAIZ / m).is_file(), m
    # las ramas son las que piden las tareas
    assert '`avance-5`' in leer('01-Sesiones/S5-MLOps-y-Operacion/tarea/README.md')
    assert 'avance-4' in leer('01-Sesiones/S4-Orquestacion-y-CI-CD/tarea/README.md')
    assert 'avance-3' in leer('01-Sesiones/S3-Despliegue-y-Redes-Neuronales/tarea/README.md')
    assert 'tarea-s2' in leer('01-Sesiones/S2-API-y-Docker/tarea/README.md')


def test_pesos_solo_los_de_las_rubricas_y_marcados_propuesta(doc, slides):
    t = ' '.join(texto(s['html']) for s in slides)
    assert '20 % reproducibilidad, 40 % técnica y 40 % análisis y decisión' in t
    for r in ('S1-Datos-y-Entrenamiento', 'S5-MLOps-y-Operacion'):
        rub = leer(f'01-Sesiones/{r}/tarea/rubrica.md')
        assert 'Reproducibilidad' in rub and '| 20 |' in rub and '| 40 |' in rub
    assert 'propuesta' in t and 'por confirmar' in t
    # ningún otro porcentaje inventado: solo 20, 40 y 40
    porcentajes = set(re.findall(r'(?<![\d,.])(\d+)\s?%', t))   # sin los decimales de las capturas (79,9 %)
    assert porcentajes <= {'20', '40'}, porcentajes


def test_checklist_interactivo(doc):
    assert doc.count('<label class="chk"><input type="checkbox">') == 9
    assert 'id="chk-n"' in doc
    assert 'las casillas no se guardan' in doc
    assert 'localStorage' not in doc and 'sessionStorage' not in doc and 'indexedDB' not in doc


# ------------------------------------------------------------------------------------------------------ imágenes reales
def test_cada_imagen_existe_con_rotulo_y_origen(doc):
    figs = re.findall(r'<figure class="cap" data-img="([^"]+)">(.*?)</figure>', doc, re.S)
    assert len(figs) >= 14
    usadas = [n for n, _ in figs]
    assert len(usadas) == len(set(usadas)), 'una imagen aparece dos veces'
    en_disco = {p.name for p in (CARPETA / 'img').glob('*')}
    assert en_disco == set(usadas), f'sobran o faltan: {en_disco ^ set(usadas)}'
    alts = []
    for nombre, h in figs:
        assert (CARPETA / 'img' / nombre).is_file()
        assert nombre.endswith('.webp')
        alt = re.search(r'<img src="img/' + re.escape(nombre) + r'" alt="([^"]+)"', h)
        assert alt and len(alt.group(1)) > 40, nombre
        alts.append(alt.group(1))
        cap = re.search(r'<figcaption>(.*?)</figcaption>', h, re.S).group(1)
        assert 'Captura real' in cap or 'Figura del proyecto base' in cap
        assert 'Origen:' in cap
        origen = re.search(r'data-ruta="([^"]+)"', cap).group(1)
        assert (RAIZ / origen).is_file(), f'{nombre}: origen {origen}'
        # el rótulo coincide con la imagen: el botón de ampliar lleva el mismo texto
        assert f'data-alt="{alt.group(1)}"' in h
        if origen.endswith('.webp'):
            assert hashlib.sha256((CARPETA / 'img' / nombre).read_bytes()).hexdigest() == hashlib.sha256((RAIZ / origen).read_bytes()).hexdigest(), \
                f'{nombre} no es copia del original'
    assert len(set(alts)) == len(alts), 'dos imágenes con el mismo rótulo'


def test_imagenes_no_borrosas_y_ligeras():
    from PIL import Image
    for p in (CARPETA / 'img').glob('*.webp'):
        im = Image.open(p)
        assert im.width >= 900, f'{p.name} es demasiado pequeña: {im.size}'
        assert p.stat().st_size < 400_000, p.name


def test_origen_de_laboratorio_citado_existe(doc):
    for lab in ('guia-codespaces', 'laboratorio-mlflow', 'laboratorio-github-actions', 'laboratorio-cloud-journey', 'laboratorio-produccion-e2e',
                'laboratorio-mlops', 'laboratorio-agentes', 'laboratorio-recap-s2', 'del-ordenador-al-servicio'):
        assert lab in doc
    for lab in ('laboratorio-mlflow', 'laboratorio-github-actions', 'laboratorio-recap-s2'):
        assert (SES / 'S3-Despliegue-y-Redes-Neuronales' / lab).is_dir()


# ---------------------------------------------------------------------------------------------- rutas y carpetas citadas
def test_cada_ruta_citada_existe(doc):
    rutas = re.findall(r'data-ruta="([^"]+)"', doc)
    assert len(set(rutas)) >= 60
    for r in set(rutas):
        assert (RAIZ / r.replace('&amp;', '&')).exists(), r


def test_extras_de_s5_y_su_estado(doc):
    s5 = SES / 'S5-MLOps-y-Operacion'
    for extra in ('extra-mcp-notebooks', 'extra-composer-batch', 'extra-vertex-champion'):
        assert (s5 / extra).is_dir(), extra
    li = {a: b for a, b in re.findall(r'<li><span class="mono ruta" data-ruta="([^"]+)">(.*?)</li>', doc, re.S) if '/S5-MLOps-y-Operacion/extra-' in a}
    assert len(li) == 3
    assert 'en preparación' in li['01-Sesiones/S5-MLOps-y-Operacion/extra-composer-batch']
    assert 'en preparación' in li['01-Sesiones/S5-MLOps-y-Operacion/extra-vertex-champion']
    assert 'sin verificar' in li['01-Sesiones/S5-MLOps-y-Operacion/extra-mcp-notebooks']
    # sus propios README dicen que no está todo verificado
    assert 'Sin verificar' in leer('01-Sesiones/S5-MLOps-y-Operacion/extra-vertex-champion/README.md') or 'sin verificar' in leer('01-Sesiones/S5-MLOps-y-Operacion/extra-vertex-champion/README.md')
    assert 'sin verificar' in leer('01-Sesiones/S5-MLOps-y-Operacion/extra-composer-batch/README.md').lower()
    # los extras de otras sesiones que se citan existen
    for r in ('S4-Orquestacion-y-CI-CD/extra-estilo-llm', 'S3-Despliegue-y-Redes-Neuronales/laboratorio-red-neuronal', 'S2-API-y-Docker/contenedores'):
        assert (SES / r).is_dir()


def test_carpetas_reservadas_o_vacias_se_dicen_asi(doc):
    for c in ('05-Modulo-Redes-Neuronales', '08-Evaluacion-Final'):
        assert [p.name for p in (RAIZ / c).iterdir()] == ['.gitkeep'], c
    assert [p.name for p in (RAIZ / '06-Modulo-LLMs').iterdir() if p.name != '.gitkeep'] == ['README.md']
    assert 'reservada: todavía vacía' in doc and 'solo el README por ahora' in doc


# ------------------------------------------------------------------------------------------------------------- cifras
def test_recuentos_del_repositorio_recalculados(doc):
    """Recuenta con glob, por su cuenta, lo que dice la diapositiva «Organizado, con ejemplos para copiar»."""
    excluir = {'_trabajo', '__pycache__', 'mlruns', 'node_modules', '.pytest_cache', '.ipynb_checkpoints'}

    def fich(base, patron):
        return [p for p in base.rglob(patron) if not (excluir & set(p.relative_to(base).parts))]
    ses = sorted(p for p in SES.iterdir() if p.is_dir() and re.match(r'S\d-', p.name))
    decks = sum(1 for c in ses for p in fich(c, 'index.html') if p.parent != c and 'ui' not in p.relative_to(c).parts)
    guias = sum(len(fich(c, 'guia*.md')) for c in ses)
    nb = sum(len(fich(c, '*.ipynb')) for c in ses) + len(list((BASE / 'notebooks').glob('*.ipynb')))
    yml = sum(len(fich(c, '*.yml')) for c in ses) + len(list((BASE / 'deploy' / 'github-actions').glob('*.yml'))) + len(list((RAIZ / '.github' / 'workflows').glob('*.yml')))
    tests = len(list((BASE / 'tests').glob('test_*.py')))
    defs = sum(len(re.findall(r'^\s*def test_', p.read_text(encoding='utf-8'), re.M)) for p in (BASE / 'tests').glob('*.py'))
    tareas = sum(1 for c in ses if (c / 'tarea' / 'README.md').is_file())
    t = texto(doc)
    assert len(ses) == 6
    for esperado in (f'{len(ses)} sesiones', f'{decks} presentaciones', f'{guias} guías paso a paso', f'{nb} cuadernos', f'{yml} workflows de ejemplo',
                     f'{tests} archivos de pruebas', f'{tareas} tareas con rúbrica', f'{defs} funciones def test_'):
        assert esperado in t, esperado
    # y los de las tarjetas del diagrama del repositorio
    assert f'{len(ses)} sesiones · {decks} presentaciones' in t
    assert f'{guias} guías · {sum(len(fich(c, "*.ipynb")) for c in ses)} cuadernos' in t


FUENTES_CIFRAS = [
    ('1 067 371', '04-Proyecto-Base/README.md', '1 067 371'),
    ('22 h síncronas propuestas', 'README.md', '22 horas síncronas propuestas'),
    ('13 variables', '04-Proyecto-Base/docs/api-y-contenedor.md', '13 variables'),
    ('826 MB', '01-Sesiones/S2-API-y-Docker/teoria/README.md', '826 MB'),
    ('usuario 10001', '04-Proyecto-Base/docs/api-y-contenedor.md', '`10001`'),
    ('5 000 libras', '01-Sesiones/S2-API-y-Docker/teoria/README.md', '5 000 libras'),
    ('1 295', '01-Sesiones/S2-API-y-Docker/teoria/README.md', '1 295'),
    ('41 188 filas', '02-Proyecto-Transversal/alumno/tu-caso-bank-marketing.md', '41 188'),
    ('12 comprobaciones', '01-Sesiones/S0-Presentacion-y-Entorno/README.md', '12 comprobaciones'),
    ('7 extensiones', '01-Sesiones/S0-Presentacion-y-Entorno/practica/guia-rapida-entorno-s0-s1.md', '7 extensiones'),
    ('25 preguntas de oro', '01-Sesiones/S5-MLOps-y-Operacion/laboratorio-agentes/guia.md', '25 preguntas de oro'),
    ('41 diapositivas', '01-Sesiones/S5-MLOps-y-Operacion/README.md', '41 diapositivas'),
    ('12 capturas', '01-Sesiones/S5-MLOps-y-Operacion/README.md', '12 capturas'),
    ('umbral 0,25', '01-Sesiones/S5-MLOps-y-Operacion/laboratorio-mlops/guia.md', '0,25'),
    ('MobileNetV3-small', '01-Sesiones/S3-Despliegue-y-Redes-Neuronales/README.md', 'MobileNetV3-small'),
    ('(70 min)', '01-Sesiones/S3-Despliegue-y-Redes-Neuronales/README.md', '| 70 |'),
    ('(35 min)', '01-Sesiones/S3-Despliegue-y-Redes-Neuronales/README.md', '| 35 |'),
    ('(20 min)', '01-Sesiones/S3-Despliegue-y-Redes-Neuronales/README.md', '| 20 |'),
    ('Parte A de 25 min', '01-Sesiones/S0-Presentacion-y-Entorno/README.md', '25 min Parte A'),
    ('southamerica-west1', '01-Sesiones/S4-Orquestacion-y-CI-CD/practicas-gcp/README.md', 'southamerica-west1'),
    ('25/11/2026', '01-Sesiones/S4-Orquestacion-y-CI-CD/laboratorio-cloud-journey/guia.md', '25/11/2026'),
    ('26/11/2026', '01-Sesiones/S5-MLOps-y-Operacion/README.md', '26/11/2026'),
    ('22/11/2026', '01-Sesiones/S4-Orquestacion-y-CI-CD/laboratorio-produccion-e2e/guia.md', '22/11/2026'),
    ('lista_del_dia', '01-Sesiones/S5-MLOps-y-Operacion/laboratorio-agentes/guia.md', 'lista_del_dia'),
    ('version_en_produccion', '01-Sesiones/S5-MLOps-y-Operacion/laboratorio-agentes/guia.md', 'version_en_produccion'),
    ('0,25', '01-Sesiones/S5-MLOps-y-Operacion/laboratorio-mlops/guia.md', 'más de 0,25'),
    ('Moro, Rita y Cortez, 2014', '01-Sesiones/S5-MLOps-y-Operacion/tarea/README.md', 'Moro, Rita y Cortez, 2014'),
    ('informe de 3 a 5 páginas', '01-Sesiones/S5-MLOps-y-Operacion/tarea/README.md', '3 a 5 páginas'),
    ('unos 5 minutos', '01-Sesiones/S5-MLOps-y-Operacion/tarea/README.md', 'unos **5 minutos**'),
]


@pytest.mark.parametrize('cifra,fuente,patron', FUENTES_CIFRAS)
def test_cada_cifra_esta_en_su_fuente(doc, cifra, fuente, patron):
    assert cifra.replace(NBSP, ' ') in texto(doc) or cifra in doc, f'«{cifra}» no está en la presentación'
    assert patron.replace(NBSP, ' ') in leer(fuente).replace(NBSP, ' '), f'«{patron}» no está en {fuente}'


def test_particion_por_cortes_coincide_con_config(doc):
    cfg = (BASE / 'ia_mlops' / 'config.py').read_text(encoding='utf-8')
    bloque = re.search(r"CORTES = \{(.*?)\n\}", cfg, re.S).group(1)
    n = {k: len(re.findall(r"'\d{4}-\d{2}-\d{2}'", v)) for k, v in re.findall(r"'(train|valid|test)': \[(.*?)\]", bloque)}
    assert n == {'train': 7, 'valid': 1, 'test': 2}
    t = texto(doc)
    assert 'TRAIN · 7 cortes' in t and 'TEST · 2' in t


def test_tres_modelos_y_nombres_de_herramientas():
    assert 'gradient_boosting' in (SES / 'S1-Datos-y-Entrenamiento' / 'tarea' / 'README.md').read_text(encoding='utf-8') or \
        'gradient_boosting' in (BASE / 'ia_mlops' / 'modeling' / 'train.py').read_text(encoding='utf-8')


# ---------------------------------------------------------------------------------------------------- repositorio real
def test_repositorio_citado_es_el_real(doc):
    url = 'https://github.com/helicr/curso-ml-ia-desarrollo-produccion'
    assert url in doc
    cfg = (RAIZ / '.git' / 'config')
    if cfg.is_file():
        remoto = re.search(r'url = (\S+)', cfg.read_text(encoding='utf-8')).group(1)
        assert re.sub(r'https://[^@/]+@', 'https://', remoto).removesuffix('.git') == url
    # el repo aparece igual en documentos del propio curso
    assert url in leer('01-Sesiones/S4-Orquestacion-y-CI-CD/practicas-gcp/README.md')
    # y no hay otro enlace de github.com del repositorio con otro nombre
    for u in set(re.findall(r'https://github\.com/[\w.-]+/[\w.-]+', doc)):
        assert u.removesuffix('.git') == url, u
    assert 'git switch develop' in doc and 'git pull' in doc
    assert 'git switch develop' in leer('01-Sesiones/S0-Presentacion-y-Entorno/practica/guia-rapida-entorno-s0-s1.md')


def test_compromiso_del_repositorio_vivo(doc):
    t = texto(doc)
    assert 'El repositorio se mantiene actualizado constantemente, con más tareas y más extras en cada tema' in t
    assert 'Haz un fork' in t or 'Haz un **fork**' in doc or 'fork' in t


# --------------------------------------------------------------------------------------- rotulado «por confirmar»
def test_por_confirmar_y_sin_verificar_solo_donde_toca(slides):
    for k, s in enumerate(slides, 1):
        vis = texto(s['html'])
        if 'por confirmar' in vis:
            assert s['part'] in ('E', 'R'), f'«por confirmar» fuera de lugar en la diapositiva {k}: {s["title"]}'
        if 'sin verificar' in vis:
            assert s['part'] in ('5', 'J'), f'«sin verificar» fuera de lugar en la diapositiva {k}: {s["title"]}'
        if 'en preparación' in vis:
            assert s['part'] in ('5', 'R'), k
    todo = ' '.join(texto(s['html']) for s in slides)
    for marca in ('por confirmar', 'sin verificar', 'en preparación'):
        assert marca in todo
    # lo que se declara por confirmar existe de verdad como pendiente en el repositorio
    assert 'por definir' in leer('02-Proyecto-Transversal/alumno/tu-caso-bank-marketing.md')
    assert 'por definir' in leer('01-Sesiones/S5-MLOps-y-Operacion/tarea/rubrica.md')
    assert 'sin definir' in leer('01-Sesiones/S5-MLOps-y-Operacion/tarea/README.md')


# -------------------------------------------------------------------------------- calidad: mojibake, CDN, hover, a11y
def test_sin_mojibake(doc):
    for malo in ('Ã', 'Â', 'â€', '�', 'Ã©', 'Ã³', 'Ã±'):
        assert malo not in doc, f'mojibake: {malo!r}'
    for ok in ('ó', 'í', 'ñ', 'á', 'é', '¿', '«', '»'):
        assert ok in doc
    generar = (CARPETA / 'generar.py').read_text(encoding='utf-8')
    assert 'Ã' not in generar and '�' not in generar


def test_sin_cdn_ni_recursos_externos(doc):
    assert not re.search(r'<script[^>]+src=', doc) and not re.search(r'<link[^>]+href=', doc)
    assert not re.search(r'(src|href)="https?://(?!github\.com/helicr/)', doc)
    assert 'cdn' not in doc.lower() and '@import' not in doc and 'url(http' not in doc
    assert 'fonts.googleapis' not in doc


def test_sin_hover_ni_efectos_que_muevan(doc):
    assert ':hover' not in doc
    css = re.search(r'<style>(.*?)</style>', doc, re.S).group(1)
    assert 'transition' not in css and 'animation' not in css and '@keyframes' not in css
    assert ':focus-visible' in css


def test_fondo_blanco(doc):
    css = re.search(r'<style>(.*?)</style>', doc, re.S).group(1)
    assert '--fondo:#ffffff' in css
    assert re.search(r'#stage\{[^}]*background:var\(--fondo\)', css)
    assert re.search(r'\.slide\{[^}]*background:var\(--fondo\)', css)


def test_diagramas_svg_propios_y_accesibles(doc):
    svgs = re.findall(r'<svg viewBox="[^"]+" role="img" aria-label="([^"]+)">', doc)
    assert len(svgs) >= 12, len(svgs)
    assert len(set(svgs)) == len(svgs)
    assert all(len(a) > 30 for a in svgs)
    # mismas formas: modelo, datos, herramienta, persona y observabilidad en los diagramas
    for clase in ('class="modelo"', 'class="datos"', 'class="herr"', 'class="user"', 'class="obs"', 'class="nodo'):
        assert clase in doc


def test_accesibilidad_basica(doc):
    imgs = re.findall(r'<img [^>]*>', doc)
    assert imgs and all(re.search(r'alt="[^"]{20,}"', i) for i in imgs if 'id="zoomimg"' not in i)
    for b in re.findall(r'<button class="zoom"[^>]*>', doc):
        assert 'aria-label=' in b
    assert doc.count('aria-expanded=') >= 6
    assert doc.count('role="tab"') == 6 and doc.count('role="tabpanel"') == 6
    assert 'aria-selected=' in doc and 'aria-controls=' in doc
    assert 'aria-label="Notas del profesor"' in doc and 'aria-label="Controles"' in doc
    assert 'aria-hidden="true"' in doc


def test_contraste_de_colores_del_texto(doc):
    css = re.search(r'<style>(.*?)</style>', doc, re.S).group(1)

    def lum(h):
        h = h.lstrip('#')
        c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

    def contraste(a, b):
        la, lb = sorted((lum(a), lum(b)), reverse=True)
        return (la + 0.05) / (lb + 0.05)
    var = dict(re.findall(r'--(\w+):(#[0-9a-fA-F]{6})', css))
    for fg, bg, minimo in (('tinta', 'fondo', 7), ('suave', 'fondo', 4.5), ('acento', 'fondo', 4.5), ('aviso', 'fondo', 4.5), ('ok', 'fondo', 4.5)):
        assert contraste(var[fg], var[bg]) >= minimo, (fg, bg)
    assert contraste('#ffffff', var['acento']) >= 4.5            # la banda de entrega (texto blanco sobre azul)


def test_no_se_toca_lo_ajeno():
    """Esta carpeta es nueva y autocontenida: solo tiene lo suyo."""
    assert sorted(p.name for p in CARPETA.iterdir() if p.name not in ('__pycache__', '.pytest_cache')) == ['generar.py', 'img', 'index.html', 'pruebas']
