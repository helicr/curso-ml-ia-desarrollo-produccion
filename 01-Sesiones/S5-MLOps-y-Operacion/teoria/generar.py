"""Genera la presentación «MLOps y operación» (teoría de S5, index.html junto a este archivo).

Teoría corta (unos 25 min hablados, minutado PROPUESTO) que se da ANTES del laboratorio A (MLOps clásico) y del B (agentes) del curso
«ML e IA: de desarrollo a producción». Fuente de contenido: teoria/README.md y las guías de los dos laboratorios. Caso Retail
(retención a 90 días, Online Retail II) con lo que ya está en 04-Proyecto-Base.

Reglas del contenido: cada cifra sale de un archivo del repositorio (las pruebas lo comprueban); la única cifra calculada aquí
es la de la diapositiva «Ilustración» (PSI y KS de un ejemplo pequeño, rotulado como ilustración); lo no probado se dice «sin verificar»,
lo que decide otra persona, «por confirmar» y lo que no existe, «sin dato». Sin imágenes ni recursos externos: todo son SVG y HTML+CSS.
El visor es el de las otras presentaciones del curso (← → · O índice · S notas · F pantalla completa · Esc · lupa para ampliar un
diagrama · botón COPIAR en cada orden), fondo blanco y nada que se mueva al pasar el ratón.

Uso:  python generar.py              escribe index.html
      python generar.py --comprobar  no escribe; sale con 1 si index.html no está al día
"""
import argparse
import html
import json
import math
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / 'index.html'

# ----------------------------------------------------------------------------------------------------------------------
# Cifras REALES: cada una con el archivo del repositorio donde se comprueba (las pruebas lo leen).
# ----------------------------------------------------------------------------------------------------------------------
HUELLA = '35a94deb4e04ab4a'                       # 04-Proyecto-Base/models/referencia.json
ETIQUETA = f'retencion-api:v1-{HUELLA}'
AUC_TEST = 0.747092830088378                      # referencia.json, metricas_test.auc
ENTRENADO = '2026-11-13T17:04:12'
APROBADO = '2026-11-22T13:26:32'
HUELLA_V2 = '3521a0421905ba28'                    # laboratorio-mlops/guia.md, 4.2

PSI_REALES = [('antiguedad_dias', '2,830', '0,736'), ('recencia_dias', '0,437', '0,259'), ('frecuencia_180d', '0,400', '0,240'),
              ('monto_90d', '0,293', '0,213'), ('frecuencia_90d', '0,276', '0,213')]       # laboratorio-mlops/guia.md, 2.3
AUC_CORTES = [('2010-12-01', 'entrenamiento', 0.8497), ('2011-03-01', 'validación', 0.6982), ('2011-06-01', 'prueba', 0.7534),
              ('2011-09-01', 'prueba', 0.7423)]                                             # laboratorio-mlops/guia.md, 3.2 y 3.3
EVAL_PRIMERA = [('Herramienta', 76), ('Sin inventar', 64), ('Trampas', 50), ('Respuestas\ncorrectas', 44)]   # laboratorio-agentes/guia.md, 6.6
EVAL_CORREGIDA = [80, 96, 86, 76]                                                            # laboratorio-agentes/guia.md, 6.5 y 6.6
PREGUNTAS_ORO = [('normales', 11), ('trampas', 6), ('seguridad', 5), ('sentido', 3)]        # laboratorio-agentes/guia.md, 6.2
HUELLA_AGENTE = 'e90daa8a20bef846'                                                          # laboratorio-agentes/guia.md, 4.4
RUN_RECHAZO, RUN_ROLLBACK_PARADO, RUN_ROLLBACK_ENSAYO = '45067472249', '45277896553', '45278456252'

# Ilustración (números de ejemplo; el PSI y el KS se CALCULAN aquí; la prueba los recalcula por su cuenta)
ILU_REF = [0.20, 0.20, 0.20, 0.20, 0.20]
ILU_ACT = [0.10, 0.15, 0.20, 0.25, 0.30]


def psi(p, q):
    return sum((b - a) * math.log(b / a) for a, b in zip(p, q))


def ks(p, q):
    ca = cb = m = 0.0
    for a, b in zip(p, q):
        ca += a
        cb += b
        m = max(m, abs(ca - cb))
    return m


def es(x, d=3):
    return f'{x:.{d}f}'.replace('.', ',')


# ----------------------------------------------------------------------------------------------------------------------
# Fuentes locales (rutas relativas a esta carpeta: cada una debe existir)
# ----------------------------------------------------------------------------------------------------------------------
RAIZ = '../../../'
FUENTES_LOCALES = [
    ('Contenido de esta teoría', [('README.md', 'teoria/README.md (apartados 0 a 9)')]),
    ('Laboratorio A · MLOps clásico', [('../laboratorio-mlops/guia.md', 'laboratorio-mlops/guia.md (L1 a L5)'),
                                       ('../laboratorio-mlops/monitoreo.yml', 'laboratorio-mlops/monitoreo.yml (workflow de monitoreo)'),
                                       ('../laboratorio-mlops/index.html', 'laboratorio-mlops/index.html (presentación)')]),
    ('Laboratorio B · Agentes', [('../laboratorio-agentes/guia.md', 'laboratorio-agentes/guia.md (apartados 4.4, 6 y 7)'),
                                 ('../laboratorio-agentes/CONFIGURAR-REPOSITORIO.md', 'laboratorio-agentes/CONFIGURAR-REPOSITORIO.md'),
                                 ('../laboratorio-agentes/index.html', 'laboratorio-agentes/index.html (presentación)')]),
    ('Caso Retail · 04-Proyecto-Base', [(RAIZ + '04-Proyecto-Base/models/referencia.json', 'models/referencia.json (la ficha)'),
                                        (RAIZ + '04-Proyecto-Base/models/historial_versiones.json', 'models/historial_versiones.json'),
                                        (RAIZ + '04-Proyecto-Base/docs/mlops-clasico.md', 'docs/mlops-clasico.md'),
                                        (RAIZ + '04-Proyecto-Base/docs/donde-se-usa-el-modelo.md', 'docs/donde-se-usa-el-modelo.md'),
                                        (RAIZ + '04-Proyecto-Base/docs/api-y-contenedor.md', 'docs/api-y-contenedor.md'),
                                        (RAIZ + '04-Proyecto-Base/deploy/gcp/preparar_proyecto.sh', 'deploy/gcp/preparar_proyecto.sh (presupuesto)')]),
    ('Sesión y curso', [('../tarea/README.md', 'tarea/README.md (la tarea)'),
                        ('../README.md', 'S5/README.md (fechas)'),
                        ('../clase-fundamentos-ia-agentes/index.html', 'clase-fundamentos-ia-agentes/index.html'),
                        (RAIZ + '01-Sesiones/S4-Orquestacion-y-CI-CD/laboratorio-produccion-e2e/guia.md', 'S4 · laboratorio-produccion-e2e/guia.md (puerta con 0,02)')]),
]
CONSULTA = '28/11/2026'


def nota(decir, ejemplo, pregunta, fuentes=''):
    """Notas del profesor: qué decir, un ejemplo y una pregunta para el aula (~1 min por diapositiva)."""
    t = f'Qué decir: {decir}\nEjemplo: {ejemplo}\nPregunta para el aula: {pregunta}'
    if fuentes:
        t += f'\nFuentes: {fuentes}'
    return t


PARTES = {'A': 'Inicio', 'B': 'Preguntas', 'C': 'Medir', 'D': 'Cambiar', 'E': 'Avisar', 'F': 'Agentes', 'G': 'Cierre'}
NOMBRES_PARTE = {'A': 'Qué se hace hoy', 'B': 'Las cinco preguntas', 'C': 'Medir: servicio, calidad y deriva', 'D': 'Cambiar y deshacer',
                 'E': 'Avisar y mantener el orden', 'F': 'Los agentes también se operan', 'G': 'Cierre y tarea'}


# ----------------------------------------------------------------------------------------------------------------------
# Utilidades de HTML
# ----------------------------------------------------------------------------------------------------------------------
def esc(t):
    return html.escape(t, quote=True)


def md(t):
    """`código`, **negrita** y *cursiva* a HTML (sobre texto seguro)."""
    t = esc(t)
    t = re.sub(r'`([^`]+)`', r'<span class="mono">\1</span>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', t)
    return re.sub(r'(?<![\w*])\*([^*\s][^*]*)\*(?![\w*])', r'<i>\1</i>', t)


def lista(items, clase=''):
    return f'<ul class="list {clase}">' + ''.join(f'<li>{md(i)}</li>' for i in items) + '</ul>'


def card(titulo, items=None, clase='', cuerpo=''):
    inner = (lista(items) if items else '') + cuerpo
    return f'<div class="card {clase}"><h3>{md(titulo)}</h3>{inner}</div>'


def callout(texto, clase=''):
    return f'<div class="callout {clase}">{md(texto)}</div>'


def msg(texto):
    return f'<div class="msg">{md(texto)}</div>'


def tabla(cab, filas, clase=''):
    def celda(c):
        return c[1:] if c.startswith('!') else md(c)
    th = ''.join(f'<th>{md(c)}</th>' for c in cab)
    tr = ''.join('<tr>' + ''.join(f'<td>{celda(c)}</td>' for c in f) + '</tr>' for f in filas)
    return f'<table class="tbl {clase}"><tr>{th}</tr>{tr}</table>'


def tag(txt, clase=''):
    return f'<span class="tag {clase}">{esc(txt)}</span>'


def grid(n, *celdas, clase=''):
    return f'<div class="grid{n} {clase}">' + ''.join(celdas) + '</div>'


def term(titulo, lineas):
    """Terminal con una orden por línea y su botón COPIAR. Las líneas que empiezan por # son comentarios (no se copian)."""
    filas = []
    for l in lineas:
        if l.startswith('#'):
            filas.append(f'<div class="tln c">{esc(l)}</div>')
        else:
            filas.append(f'<div class="tln"><span class="ps">$</span> <code>{esc(l)}</code>'
                         f'<button class="cp" data-t="{esc(l)}" title="Copiar esta orden">COPIAR</button></div>')
    return f'<div class="term"><div class="bar"><em>{esc(titulo)}</em></div><div class="tls">{"".join(filas)}</div></div>'


def enlace(href, texto):
    return f'<a class="btn" href="{esc(href)}">{esc(texto)}</a>'


LUPA = ('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round">'
        '<circle cx="10" cy="10" r="6.5"/><path d="M15 15l6 6"/></svg>')


def dg(s, zoom=True):
    """Diagrama SVG; con lupa para ampliarlo (Esc cierra)."""
    boton = f'<button class="zsv lupa" type="button" title="Ampliar el diagrama (Esc cierra)">{LUPA} Ampliar</button>' if zoom else ''
    return f'<div class="dg dgz">{s}{boton}</div>'


# ----------------------------------------------------------------------------------------------------------------------
# Diapositivas
# ----------------------------------------------------------------------------------------------------------------------
SLIDES = []
_N = {}


def slide(parte, minutos, titulo, kick, h1, cuerpo, notas):
    cuerpo = re.sub(r'\*\*([^*<>]+)\*\*', r'<b>\1</b>', cuerpo)
    cuerpo = re.sub(r'`([^`<>]+)`', r'<span class="mono">\1</span>', cuerpo)
    n = list(PARTES).index(parte) + 1
    _N[parte] = _N.get(parte, 0) + 1
    antetitulo = f'{n} · {NOMBRES_PARTE[parte]} · {kick}'
    attrs = f' data-part="{parte}" data-min="{minutos}" data-title="{esc(titulo)}"'
    SLIDES.append(f'<section class="slide"{attrs}\n data-notes="{esc(notas)}">\n'
                  f'<p class="kick">{esc(antetitulo)}</p><h1>{md(h1)}</h1>\n<div class="bd">{cuerpo}</div>\n</section>')


# ----------------------------------------------------------------------------------------------------------------------
# SVG: mismas formas y paleta que los otros decks (modelo = rectángulo azul de doble borde, datos = cilindro, herramienta = hexágono
# ámbar, aplicación = rectángulo redondeado, puerta = trazo discontinuo ámbar)
# ----------------------------------------------------------------------------------------------------------------------
LH = {'t0': 28, 't1': 22, 't2': 19, 't3': 17}


def svg(w, h, cuerpo, etiqueta, idp='a'):
    marcas = ''.join(f'<marker id="{idp}{s}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto">'
                     f'<path d="M0 0 L10 5 L0 10 z" fill="{c}"/></marker>' for s, c in (('', '#0b5cad'), ('g', '#7b8794'), ('r', '#b91c1c'), ('v', '#15803d')))
    return f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{esc(etiqueta)}"><defs>{marcas}</defs>{cuerpo}</svg>'


def tx(x, y, s, cls='t2', lh=None):
    lh = lh or LH.get(cls.split()[0], 19)
    partes = s.split('\n')
    if len(partes) == 1:
        return f'<text x="{x:g}" y="{y:g}" class="{cls}">{esc(s)}</text>'
    ts = ''.join(f'<tspan x="{x:g}" dy="{0 if i == 0 else lh}">{esc(p)}</tspan>' for i, p in enumerate(partes))
    return f'<text x="{x:g}" y="{y:g}" class="{cls}">{ts}</text>'


def centrado(x, y, w, h, lineas):
    alto = sum(LH.get(c.split()[0], 19) * len(t.split('\n')) for t, c in lineas)
    yy = y + h / 2 - alto / 2 + 15
    out = []
    for t, c in lineas:
        out.append(tx(x + w / 2, yy, t, c))
        yy += LH.get(c.split()[0], 19) * len(t.split('\n'))
    return ''.join(out)


def _ls(t1, t2, t3, c2='t2', c3='t2'):
    return [(t1, 't1')] + ([(t2, c2)] if t2 else []) + ([(t3, c3)] if t3 else [])


def nodo(x, y, w, h, t1, t2='', t3='', cls='nodo', c2='t2', c3='t2'):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" class="{cls}"/>' + centrado(x, y, w, h, _ls(t1, t2, t3, c2, c3))


def sh_modelo(x, y, w, h, t1, t2='', t3='', c2='t2', c3='t2'):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" class="modelo"/>'
            f'<rect x="{x + 5}" y="{y + 5}" width="{w - 10}" height="{h - 10}" rx="10" class="modelo2"/>' + centrado(x, y, w, h, _ls(t1, t2, t3, c2, c3)))


def sh_datos(x, y, w, h, t1, t2='', t3='', c2='t2', c3='t2'):
    ry = 11
    d = f'M{x} {y + ry} A{w / 2} {ry} 0 0 1 {x + w} {y + ry} V{y + h - ry} A{w / 2} {ry} 0 0 1 {x} {y + h - ry} Z'
    tapa = f'M{x} {y + ry} A{w / 2} {ry} 0 0 0 {x + w} {y + ry}'
    return f'<path d="{d}" class="datos"/><path d="{tapa}" class="datos2"/>' + centrado(x, y + ry, w, h - ry, _ls(t1, t2, t3, c2, c3))


def sh_herr(x, y, w, h, t1, t2='', t3='', c2='t2', c3='t2'):
    c = 18
    pts = f'{x + c},{y} {x + w - c},{y} {x + w},{y + h / 2} {x + w - c},{y + h} {x + c},{y + h} {x},{y + h / 2}'
    return f'<polygon points="{pts}" class="herr"/>' + centrado(x, y, w, h, _ls(t1, t2, t3, c2, c3))


def flecha(idp, *pts, kind='', suf=''):
    d = 'M' + ' L'.join(f'{x:g} {y:g}' for x, y in pts)
    return f'<path d="{d}" class="fl {kind}" marker-end="url(#{idp}{suf})"/>'


def fl_g(idp, *pts):
    return flecha(idp, *pts, kind='g', suf='g')


def fl_r(idp, *pts):
    return flecha(idp, *pts, kind='r', suf='r')


def fl_v(idp, *pts):
    return flecha(idp, *pts, kind='v', suf='v')


def num(cx, cy, n):
    return f'<circle cx="{cx}" cy="{cy}" r="14" class="num"/><text x="{cx}" y="{cy + 5.5}" class="numt">{n}</text>'


# ----------------------------------------------------------------------------------------------------------------------
# Contenido
# ----------------------------------------------------------------------------------------------------------------------
def construir():
    SLIDES.clear()
    _N.clear()

    # ------------------------------------------------------------------------------------------------ A · Qué se hace hoy
    slide('A', 0, 'Portada', 'ML e IA · S5', 'MLOps y operación: lo que pasa después de «ponerlo en producción»', f'''
<div class="cover">
 <p class="sub">El modelo de **retención a 90 días** ya está en producción desde S4. Esta teoría corta explica **cómo se opera**: saber qué está sirviendo, vigilar si sigue bien, cambiarlo con seguridad y poder deshacerlo.</p>
 <div class="chips"><span class="chip">Caso Retail</span><span class="chip">Huella y ficha</span><span class="chip">PSI y KS</span><span class="chip">Alias y rollback</span><span class="chip">Alertas</span><span class="chip">Agentes como software</span></div>
 {grid(3, card('Se vigila', ['Servicio sano **no** es modelo bueno', 'La deriva avisa; el rendimiento confirma, tarde']),
       card('Se versiona', ['Huella de datos, ficha, imagen', 'Un alias es un puntero a una versión']),
       card('Se deshace', ['Volver atrás sin borrar nada', 'Un agente es software más']), clase='tres')}
 <p class="fte">Teclas: <b>← →</b> avanzan · <b>O</b> índice · <b>S</b> notas del profesor · <b>F</b> pantalla completa · <b>lupa</b> para ampliar un diagrama y <b>Esc</b> para cerrar · <b>COPIAR</b> en cada orden.</p>
</div>''',
          nota('Es la teoría corta de la sesión: unos 25 minutos (propuesta) antes de los dos laboratorios. Nada de lo que se ve hoy es nuevo en herramientas: es la disciplina de operar lo que ya existe desde S4. Anticipe los tres verbos: se vigila, se versiona, se deshace.',
               'Un modelo no se rompe como una API: sigue devolviendo una probabilidad aunque ya no acierte.',
               '¿Quién ha tenido que volver atrás un cambio en producción alguna vez? ¿Cuánto tardó?',
               'teoria/README.md, apartado 0; guion.md, «Mensajes que no deben perderse».'))

    plano = svg(1176, 238, ''.join([
        nodo(0, 20, 270, 170, 'Teoría', 'esta presentación', 'unos 25 min (propuesta)'),
        nodo(302, 20, 270, 170, 'Laboratorio A', 'MLOps clásico', 'deriva · alias · alertas'),
        nodo(604, 20, 270, 170, 'Laboratorio B', 'Agentes', 'MCP · LLM local · evaluación'),
        nodo(906, 20, 270, 170, 'Tarea', 'repositorio, informe, demo', 'entrega 11/12, 10:00 (hora de Perú)', cls='nodo puerta'),
        fl_g('p1', (271, 105), (301, 105)), fl_g('p1', (573, 105), (603, 105)), fl_g('p1', (875, 105), (905, 105)),
        tx(437, 218, 'propuesta del guion: ~50 min', 't3'), tx(739, 218, 'propuesta del guion: ~110 min', 't3'),
    ]), 'Cuatro estaciones: teoría, laboratorio A, laboratorio B y tarea', 'p1')
    slide('A', 1, 'Qué se hace hoy', 'el plan', 'Hoy: teoría, dos laboratorios y la tarea', f'''
{dg(plano)}
<div class="botones">{enlace('../laboratorio-mlops/index.html', 'Laboratorio A · presentación')} {enlace('../laboratorio-agentes/index.html', 'Laboratorio B · presentación')} {enlace('../tarea/README.md', 'Tarea (README)')} {enlace('../clase-fundamentos-ia-agentes/index.html', 'Clase de fundamentos')}</div>
{grid(2, card('Laboratorio A · MLOps clásico', ['Medir la deriva (PSI y KS) y el AUC por corte', 'Mover el alias `champion` y volver atrás', 'Un workflow de monitoreo que avisa con un issue']),
       card('Laboratorio B · Agentes', ['Un servidor MCP, un LLM local y un agente', 'Skills, 25 preguntas de oro y puerta de calidad', 'Despliegue con aprobación y rollback']))}''',
          nota('Dibuje el día: teoría ahora, laboratorio A de MLOps clásico (propuesta de 50 minutos en el guion), laboratorio B de agentes (unos 110 minutos repartidos en seis bloques) y la tarea, que se entrega el 11 de diciembre a las 10:00, hora de Perú. Los minutos son una propuesta, no una medición.',
               'La tarea aplica a SU caso (Bank Marketing) lo que aquí se ve con el caso Retail.',
               '¿Quién tiene ya su fork con la rama develop, Actions activado y el environment produccion?',
               'guion.md (minuto a minuto); S5/README.md (fecha de entrega); tarea/README.md.'))

    # ------------------------------------------------------------------------------------------------ B · Las cinco preguntas
    preguntas = [('1', '¿Qué está\nsirviendo?', 'La ficha\nreferencia.json y\nla etiqueta de imagen'),
                 ('2', '¿Con qué se\nhizo?', 'La huella de los\ndatos y el commit\nde git'),
                 ('3', '¿Sigue\nfuncionando?', 'Deriva de datos y\nde rendimiento\n(PSI, AUC por corte)'),
                 ('4', '¿Cómo lo\ncambio?', 'Puerta de calidad,\naprobación humana\ny PR'),
                 ('5', '¿Cómo lo\ndeshago?', 'Mover el alias o\nrestaurar la ficha\nanterior: sin borrar')]
    cs = []
    for i, (n, q, r) in enumerate(preguntas):
        x = i * 238
        cs.append(f'<rect x="{x}" y="6" width="224" height="278" rx="14" class="nodo"/><rect x="{x}" y="6" width="224" height="8" rx="4" class="modelo"/>')
        cs.append(num(x + 112, 50, n))
        cs.append(tx(x + 112, 94, q, 't1'))
        cs.append(f'<line x1="{x + 24}" y1="152" x2="{x + 200}" y2="152" class="vida"/>')
        cs.append(tx(x + 112, 182, 'se contesta con', 'tg'))
        cs.append(tx(x + 112, 212, r, 't3'))
    cinco = svg(1176, 292, ''.join(cs), 'Las cinco preguntas de operar: qué sirve, con qué se hizo, si funciona, cómo lo cambio y cómo lo deshago', 'q1')
    slide('B', 2, 'Cinco preguntas', 'operar no es el final', 'Operar no es una tarea al final: son cinco preguntas', f'''
{dg(cinco)}
{msg('Si no puedes contestarlas en un minuto, el modelo está **en producción**, pero no está **operado**.')}''',
          nota('Es el hilo de toda la sesión: cada diapositiva siguiente contesta una de estas cinco preguntas. Poner un modelo en producción no es el final, es el principio de un trabajo distinto. Pida que las apunten: al final del día deben poder señalar dónde se responde cada una.',
               'Si mañana alguien pregunta «¿con qué datos se entrenó el modelo que sirve la API?», la respuesta debería estar en un archivo, no en la memoria de una persona.',
               'En tu repositorio, ¿puedes contestar la pregunta 2 en menos de un minuto?',
               'teoria/README.md, apartado 0; guion.md, mensaje 1.'))

    cadena = svg(1176, 330, ''.join([
        sh_datos(0, 30, 240, 150, 'Datos', 'huella_datos', HUELLA, c3='t2 mono'),
        sh_modelo(312, 30, 240, 150, 'Ficha del modelo', 'models/referencia.json', f'version 1 · AUC test {es(AUC_TEST)}'),
        nodo(624, 30, 240, 150, 'Imagen', 'retencion-api:v1-', HUELLA, c3='t2 mono'),
        nodo(936, 30, 240, 150, 'Estado', 'historial_versiones.json', 'estado: produccion', cls='nodo ok'),
        fl_g('c1', (241, 105), (310, 105)), fl_g('c1', (553, 105), (622, 105)), fl_g('c1', (865, 105), (934, 105)),
        tx(276, 92, 'alimenta', 'tc'), tx(588, 92, 'etiqueta', 'tc'), tx(900, 92, 'aprobada', 'tc'),
        fl_r('c1', (744, 196), (744, 236), (120, 236), (120, 192)),
        tx(432, 266, 'la etiqueta lleva la huella: de la imagen se llega a los datos', 'tg'),
        tx(588, 318, f'Otros campos de la ficha: entrenado_en {ENTRENADO} · aprobado_en {APROBADO}', 't3'),
    ]), 'La huella de los datos va a la ficha, la ficha a la etiqueta de la imagen y el historial guarda el estado', 'c1')
    slide('B', 2, 'De la imagen a la ficha', 'versionar y enlazar', 'Una huella enlaza datos, ficha, imagen y estado', f'''
{dg(cadena)}
{grid(3, card('Código', ['El **commit** de git; los datos grandes no van en git, se identifican por huella']),
      card('«En producción»', ['Es la imagen **más** la ficha **más** el historial: se fusiona un PR para cambiarlo']),
      card('Misma huella', ['Mismos datos y mismo código dan la misma huella y las mismas métricas']))}''',
          nota('Versionar es poder decir cuál era exactamente cada pieza cuando pasó algo. La ficha referencia.json es el eslabón: dice la versión, la huella de los datos, la etiqueta de la imagen y las métricas; la etiqueta de la imagen lleva la huella, así que de la imagen se llega a los datos. El historial guarda el estado de cada versión (hoy solo la 1, en producción).',
               f'Abrir models/referencia.json: huella_datos {HUELLA}, etiqueta_imagen {ETIQUETA}. Si la huella cambia, han cambiado los datos: comparar dos ejecuciones con huellas distintas sin decirlo es un error de método.',
               '¿Qué dos archivos y qué etiqueta necesitas para saber con qué datos se hizo el modelo que sirve la API?',
               '04-Proyecto-Base/models/referencia.json y historial_versiones.json; docs/donde-se-usa-el-modelo.md; S4 laboratorio-produccion-e2e/guia.md (apartado 0).'))

    # ------------------------------------------------------------------------------------------------ C · Medir
    slide('C', 1, 'Servicio y modelo', 'dos preguntas distintas', 'Un servicio sano no es un modelo bueno', f'''
{grid(2, card('Métricas del servicio', ['¿Responde, rápido y sin errores?', '**Latencia** (mediana y p95), **tasa de errores**, **disponibilidad**', 'Un fallo se ve: un 5xx, un tiempo excesivo, la API caída'], clase='verde'),
       card('Calidad del modelo', [f'¿Las respuestas son buenas? **AUC** de test {es(AUC_TEST)} (ficha v1)', 'En el agente: acierto de herramienta, 80 % (referencia v1)', 'Un fallo **no se ve**: 200 con una probabilidad equivocada y la etiqueta llega tarde'], clase='azul'))}
{callout('**La trampa:** la API responde 200 en milisegundos y el modelo ya no acierta. Por eso la API distingue **422** (contrato), **503** (sin modelo) y **500** (error nuestro).', 'rojo')}
<div class="split2">{term('Terminal bash · API en marcha', ['curl http://127.0.0.1:8080/listo'])}<p class="small"><b>Sin dato:</b> un panel de métricas de servicio en vivo para la API del curso. Hay códigos distinguibles, <span class="mono">/listo</span> y registros.</p></div>''',
          nota('Son dos preguntas distintas y una no contesta a la otra. El servicio se mide en el momento de la petición; la calidad exige la etiqueta real y a menudo llega tarde. Por eso la API del curso distingue los fallos: 422 si la petición no cumple el contrato, 503 si no hay modelo cargado, 500 si el error es nuestro.',
               'GET /listo responde 503 y dice qué ejecutar si falta el modelo; /salud y /listo son cosas distintas: vivo no es lo mismo que listo. En el agente, la latencia es una cosa y las 25 preguntas de oro son otra.',
               'Tu API responde 200 en 15 ms y el AUC cae: ¿qué métricas lo muestran y cuáles no?',
               'teoria/README.md, apartado 2; 04-Proyecto-Base/docs/api-y-contenedor.md; models/referencia.json; laboratorio-agentes/guia.md, 6.5.'))

    tl = svg(1176, 340, ''.join([
        '<line x1="70" y1="170" x2="1106" y2="170" class="eje"/>',
        '<circle cx="120" cy="170" r="11" fill="#fff" stroke="#0b5cad" stroke-width="4"/><circle cx="1010" cy="170" r="11" fill="#fff" stroke="#0b5cad" stroke-width="4"/>',
        tx(120, 212, 'Día 0', 't1'), tx(120, 236, 'el modelo predice', 't3'),
        tx(1010, 78, 'Día 90', 't1'), tx(1010, 102, 'llega la etiqueta:', 't3'), tx(1010, 120, '¿compró de verdad?', 't3'),
        nodo(150, 24, 780, 92, 'Deriva de datos: se mide ya', 'compara lo que entra ahora con lo que entró al entrenar', 'no necesita la etiqueta · avisa pronto, pero puede ser falsa alarma', cls='nodo ok', c2='t2', c3='t3'),
        fl_v('t1', (120, 120), (120, 152)),
        nodo(150, 262, 960, 66, 'Deriva de rendimiento: hay que esperar', 'el AUC solo se puede calcular cuando llega la etiqueta · confirma, con retraso', cls='nodo puerta'),
        fl_g('t1', (1010, 260), (1010, 190)),
    ]), 'Línea de tiempo de 90 días: la deriva de datos se ve el día 0 y la de rendimiento solo el día 90', 't1')
    slide('C', 2, 'Dos derivas', 'la etiqueta tarda 90 días', 'La deriva de datos avisa; la de rendimiento confirma, tarde', f'''
{dg(tl)}
{msg('La etiqueta del caso es «¿compró en los **90 días siguientes**?»: no hay atajo hasta entonces.')}''',
          nota('Deriva es que el mundo cambia y el modelo no se entera. La de datos se ve enseguida porque compara lo que entra con lo que entró al entrenar, sin respuesta correcta. La de rendimiento exige la etiqueta, y la del caso llega 90 días después de la predicción. Por eso la primera es una alerta temprana, no una prueba, y la segunda es la confirmación con retraso.',
               'Una predicción de hoy solo se puede corregir dentro de 90 días. Mientras tanto se mira la deriva de datos y las probabilidades que salen (¿se aplanan? ¿se vacía el tramo alto?).',
               'En tu caso propio, ¿con qué retraso llega la etiqueta? ¿Se puede medir el rendimiento o no?',
               'teoria/README.md, apartado 3; laboratorio-mlops/guia.md, 0 y 3.1; 04-Proyecto-Base/docs/mlops-clasico.md.'))

    umbrales = svg(560, 150, ''.join([
        '<rect x="10" y="40" width="130" height="34" class="bd1"/><rect x="140" y="40" width="190" height="34" class="bd2"/><rect x="330" y="40" width="220" height="34" class="bd3"/>',
        tx(75, 62, 'estable', 't3'), tx(235, 62, 'vigilar', 't3'), tx(440, 62, 'cambio importante', 't3'),
        tx(10, 100, '0', 'tg izq'), tx(140, 100, '0,10', 'tg'), tx(330, 100, '0,25', 'tg'), tx(552, 100, 'PSI →', 'tg fin'),
        tx(280, 24, 'CONVENCIÓN del oficio, no una ley', 't1'),
    ]), 'Escala del PSI con los umbrales 0,10 y 0,25 como convención', 'u1')
    slide('C', 1, 'PSI y KS', 'qué miden', 'PSI y KS miden cuánto se parecen dos distribuciones', f'''
<div class="split2b">
 <div class="col">{card('PSI · índice de estabilidad', ['Parte la variable en **tramos** (cuantiles de la referencia)', 'Compara la fracción de filas de cada tramo: `p` en la referencia, `q` ahora', '**Suma** de `(q - p) · ln(q / p)`: 0 si coinciden, crece al separarse'])}
 {card('KS · Kolmogórov y Smirnov', ['Distancia **máxima** entre las dos distribuciones acumuladas', '0 = iguales; 1 = totalmente separadas'])}</div>
 <div class="col">{card('Umbrales', cuerpo=dg(umbrales))}
 {callout('Los umbrales 0,10 y 0,25 son una **convención**, **sin fuente** en este repositorio. Tú debes poder justificar el tuyo. Un tramo vacío da `ln(0)`: suelo de 0,0001.')}</div>
</div>''',
          nota('El PSI compara, tramo a tramo, qué fracción de clientes cae en cada intervalo antes y ahora. El KS mira la distancia máxima entre las distribuciones acumuladas. Lo importante es la honestidad con los umbrales: 0,10 y 0,25 son una costumbre del oficio, no una ley, y no tienen fuente en este repositorio. El laboratorio A permite cambiar el umbral de alarma.',
               'Un tramo vacío rompe el logaritmo; el laboratorio sube las fracciones menores que 0,0001 a 0,0001. Es un parche numérico, no una teoría.',
               '¿Con qué umbral te habrías enterado de un cambio que de verdad importó? ¿Cómo lo justificarías?',
               'teoria/README.md, apartado 3.1; laboratorio-mlops/guia.md, 0 y 2.4; 04-Proyecto-Base/docs/mlops-clasico.md.'))

    # --- Ilustración: números de ejemplo, calculados aquí
    p_ilu = psi(ILU_REF, ILU_ACT)
    k_ilu = ks(ILU_REF, ILU_ACT)
    estado_ilu = 'estable' if p_ilu < 0.10 else ('vigilar' if p_ilu < 0.25 else 'cambio importante')
    ejeY0 = 250
    barras = []
    for i, (a, b) in enumerate(zip(ILU_REF, ILU_ACT)):
        x = 50 + i * 100
        ha, hb = a * 560, b * 560
        barras.append(f'<rect x="{x}" y="{ejeY0 - ha:g}" width="36" height="{ha:g}" class="bg"/><rect x="{x + 38}" y="{ejeY0 - hb:g}" width="36" height="{hb:g}" class="b1"/>')
        barras.append(tx(x + 18, ejeY0 - ha - 6, es(a, 2), 't3'))
        barras.append(tx(x + 56, ejeY0 - hb - 6, es(b, 2), 't3'))
        barras.append(tx(x + 37, ejeY0 + 22, f'tramo {i + 1}', 't3'))
    ilu = svg(580, 300, '<line x1="40" y1="250" x2="560" y2="250" class="eje"/>' + ''.join(barras) +
              '<rect x="60" y="6" width="14" height="14" class="bg"/>' + tx(80, 18, 'referencia (p)', 't3 izq') +
              '<rect x="220" y="6" width="14" height="14" class="b1"/>' + tx(240, 18, 'actual (q)', 't3 izq'), 'Barras de la fracción de filas por tramo en la referencia y en el corte actual (ilustración)', 'i1')
    filas = [[f'tramo {i + 1}', es(a, 2), es(b, 2), es((b - a) * math.log(b / a), 4)] for i, (a, b) in enumerate(zip(ILU_REF, ILU_ACT))]
    filas.append(['**PSI**', '', '', f'**{es(p_ilu, 4)}**'])
    slide('C', 1, 'Ilustración PSI', 'ejemplo calculado', 'Ilustración: así sale un PSI con cinco tramos', f'''
<div class="split2">
 <div class="col"><span class="tag warn">ILUSTRACIÓN · números de ejemplo, no son datos del curso</span>{dg(ilu)}</div>
 <div class="col">{tabla(['Tramo', 'p', 'q', '(q − p) · ln(q / p)'], filas, 'cos')}
 {callout(f'PSI = **{es(p_ilu, 3)}** → «{estado_ilu}» con la convención. KS (con estos cinco tramos) = **{es(k_ilu, 2)}**. Calculado en `generar.py`.')}</div>
</div>''',
          nota(f'Es una ilustración con números que elegimos para que se vea el mecanismo: la referencia reparte el 20 % en cada uno de cinco tramos y ahora el reparto se inclina hacia el último. El PSI sale {es(p_ilu, 4)} y el KS, sobre estos cinco tramos, {es(k_ilu, 2)}. No son datos del curso: las cifras reales del caso vienen en la diapositiva siguiente.',
               'Con la misma muestra en los dos lados el PSI es exactamente 0. Cada tramo aporta un término positivo: da igual el sentido del cambio, importa cuánto se mueve.',
               '¿Qué pasaría con el PSI si un tramo se quedara vacío en el corte actual?',
               'Cálculo hecho en teoria/generar.py (funciones psi y ks); la fórmula es la de laboratorio-mlops/guia.md, 2.4.'))

    # --- Cifras reales del laboratorio A
    f_real = [[f'`{v}`', p, k, '**deriva**'] for v, p, k in PSI_REALES] + [['`es_reino_unido`', '0,000', '0,010', 'estable']]
    slide('C', 1, 'Cifras del laboratorio A', 'datos reales', 'Con datos reales: 5 de 13 variables superan 0,25', f'''
<div class="split2b">
 <div class="col">{tabla(['Variable', 'PSI', 'KS', 'Estado'], f_real, 'cos')}
 <p class="fte">Referencia 2010-12-01 (109 clientes) frente a 2011-12-10 (148 clientes). Fuente: laboratorio-mlops/guia.md, apartado 2.3 (ensayo del 26/11/2026, muestra de 150 clientes).</p></div>
 <div class="col">{callout('**Lectura honesta:** `antiguedad_dias` crece para todos con solo dejar pasar un año: es **esperable**. Las de actividad reciente sí dicen que el comportamiento cambió.')}
 {term('Terminal bash · desde 04-Proyecto-Base', ['python -m ia_mlops.deriva datos --referencia 2010-12-01 --actual 2011-12-10', 'python -m ia_mlops.deriva datos --referencia 2010-08-01 --actual 2010-09-01 --umbral-psi 0.5'])}
 <p class="small">Salida **1** = hay deriva, **0** = no, **2** = error. Con 0,25 el par agosto→septiembre de 2010 da 1 y con 0,5 da 0: cambió la **convención**, no los datos.</p></div>
</div>''',
          nota('Estas son las cifras reales del laboratorio A, ya guardadas en su guía: cinco de trece variables superan 0,25; la mayor es antiguedad_dias con PSI 2,830. La lectura honesta: antiguedad_dias crece para todos los clientes con solo dejar pasar un año, así que su PSI enorme es esperable y no pide por sí solo reentrenar. Con 109 clientes el PSI oscila por azar: es un aviso, no una sentencia.',
               'La misma medición da salida 1 con el umbral 0,25 y salida 0 con 0,5 en el par agosto-septiembre de 2010: el código de salida es lo que un workflow lee para decidir.',
               '¿Reentrenarías por esta alerta? ¿Qué mirarías antes de decidir?',
               'laboratorio-mlops/guia.md, apartados 2.3 y 2.5; 04-Proyecto-Base/docs/mlops-clasico.md.'))

    # --- AUC con datos de entrenamiento
    alto = 260
    bar = []
    for i, (corte, uso, auc) in enumerate(AUC_CORTES):
        x = 60 + i * 120
        h = auc * alto
        clase = 'br' if uso == 'entrenamiento' else 'b1'
        bar.append(f'<rect x="{x}" y="{300 - h:g}" width="80" height="{h:g}" class="{clase}"/>')
        bar.append(tx(x + 40, 300 - h - 8, es(auc, 4), 't1'))
        bar.append(tx(x + 40, 322, corte, 't3'))
        bar.append(tx(x + 40, 340, uso, 't3'))
    grafico = svg(600, 360, '<line x1="40" y1="300" x2="590" y2="300" class="eje"/>' + ''.join(bar) +
                  f'<line x1="40" y1="{300 - 0.5 * alto:g}" x2="590" y2="{300 - 0.5 * alto:g}" class="vida"/>' + tx(588, 300 - 0.5 * alto - 6, 'azar: 0,5', 't3 fin'),
                  'AUC por corte: 0,8497 en entrenamiento, 0,6982 en validación, 0,7534 y 0,7423 en prueba', 'a1')
    slide('C', 1, 'AUC engaña', 'medir con datos de entrenamiento', 'Medir con datos de entrenamiento engaña', f'''
<div class="split2">
 <div class="col">{dg(grafico)}</div>
 <div class="col">{callout('El AUC en **entrenamiento** (0,8497) es mucho mayor que en validación (0,6982): la «caída» de **0,1515** es en parte **sobreajuste**. **El modelo no ha cambiado**: solo lo medimos con datos que ya había visto.')}
 {term('Terminal bash · desde 04-Proyecto-Base', ['python -m ia_mlops.deriva rendimiento --cortes 2011-03-01 2011-06-01 2011-09-01', 'python -m ia_mlops.deriva rendimiento --cortes 2010-12-01 2011-03-01 2011-06-01 2011-09-01'])}
 <p class="small">Para una medida honesta: cortes de **prueba** o posteriores. Tolerancia de 0,05 **provisional**: no sale de ninguna medición.</p></div>
</div>''',
          nota('El AUC por corte lo calcula el laboratorio A. En el último corte de entrenamiento sale 0,8497 y en validación 0,6982: la caída de 0,1515 parece deriva, pero es sobreajuste, porque el modelo se ajustó con esos datos. En los cortes de prueba, 0,7534 y 0,7423, no hay caída: el AUC incluso mejora frente al primer corte medido.',
               'La orden marca el uso de cada corte (entrenamiento, validación o prueba) y avisa. La primera orden da salida 0 y la segunda salida 1; la diferencia es solo qué cortes se miran.',
               '¿Cómo habrías interpretado una caída de 0,15 si nadie te hubiera dicho qué cortes eran de entrenamiento?',
               'laboratorio-mlops/guia.md, apartados 3.2 y 3.3; 04-Proyecto-Base/docs/mlops-clasico.md.'))

    # ------------------------------------------------------------------------------------------------ D · Cambiar y deshacer
    vers = svg(1176, 330, ''.join([
        nodo(40, 30, 220, 50, '@champion', cls='nodo puerta'),
        sh_modelo(40, 170, 330, 140, 'Versión 1', 'valid_auc 0,6982 · test_auc 0,7471', f'huella {HUELLA}'),
        sh_modelo(500, 170, 330, 140, 'Versión 2', 'valid_auc 0,7855 · test_auc 0,7956', f'huella {HUELLA_V2}'),
        fl_v('v1', (150, 82), (150, 168)),
        flecha('v1', (260, 55), (665, 55), (665, 168), kind='g', suf='g'),
        tx(470, 46, 'promover --version 2', 'tg'), tx(166, 128, 'ahora', 'tc izq'),
        fl_g('v1', (498, 250), (372, 250)), tx(435, 242, 'volver', 'tg'),
        tx(1003, 40, 'Mismo cliente, mismo comando', 't1'), tx(1003, 62, 'cargar', 't3'),
        nodo(880, 90, 120, 80, 'con v1', '0,8279', cls='nodo ok'), nodo(1016, 90, 120, 80, 'con v2', '0,7245', cls='nodo ok'),
        tx(1003, 215, 'El alias decide qué', 't2'), tx(1003, 237, 'modelo se sirve y,', 't2'), tx(1003, 259, 'esta vez, se nota.', 't2'),
    ]), 'Un alias @champion apunta a la versión 1; promover lo mueve a la versión 2 y volver lo devuelve', 'v1')
    slide('D', 2, 'Versiones y alias', 'un puntero con nombre', 'Un alias es un puntero: cambiar es moverlo, deshacer es volver a moverlo', f'''
{dg(vers)}
{term('Terminal bash · desde 04-Proyecto-Base (L3 del laboratorio A)', ['python -m ia_mlops.alias_modelo mostrar', 'python -m ia_mlops.alias_modelo promover --version 2', 'python -m ia_mlops.alias_modelo volver'])}''',
          nota('Cada entrenamiento registra una versión nueva de retencion-90d en MLflow. Un alias, por ejemplo champion, es un nombre que apunta a una versión. Cambiar de modelo es mover el puntero y deshacer es volver a moverlo: no se borra nada, y por eso el rollback es rápido. La v2 se entrena con los datos completos para que sea de verdad otra: su AUC de test es 0,7956 frente a 0,7471.',
               'Con la v1 el comando cargar da 0,8279 para el cliente de ejemplo; con la v2, 0,7245. Con tres versiones idénticas el cambio de alias no se notaría, por eso la v2 es distinta.',
               '¿Qué ventaja tiene mover un puntero frente a copiar archivos de modelo a mano?',
               'laboratorio-mlops/guia.md, apartados 4.1 a 4.4; 04-Proyecto-Base/docs/mlops-clasico.md (alias y vuelta atrás).'))

    gob = svg(1176, 340, ''.join([
        '<rect x="0" y="6" width="560" height="236" rx="16" class="zona"/>', tx(18, 32, 'Registro de MLflow', 't1 izq'),
        sh_modelo(24, 52, 150, 90, 'v1'), sh_modelo(200, 52, 150, 90, 'v2'), nodo(384, 62, 160, 70, '@champion', cls='nodo puerta'),
        fl_v('g1', (383, 97), (352, 97)),
        nodo(24, 166, 520, 56, 'Quien carga models:/retencion-90d@champion', 'recibe la versión a la que apunte el alias', cls='nodo ok', c2='t3'),
        '<rect x="660" y="6" width="516" height="236" rx="16" class="zona"/>', tx(678, 32, 'Despliegue de la API', 't1 izq'),
        nodo(684, 64, 220, 80, 'Imagen Docker', 'copia models/modelo_mlflow', 'al construirse', c2='t3', c3='t3'),
        nodo(940, 64, 210, 80, 'API en marcha', 'sirve lo que copió', cls='nodo mal', c2='t3'),
        fl_g('g1', (905, 104), (938, 104)),
        fl_r('g1', (561, 104), (682, 104)),
        tx(612, 78, 'no lee el', 'tc mal'), tx(612, 96, 'registro', 'tc mal'),
        tx(930, 200, 'Mover el alias no cambia', 't2'), tx(930, 222, 'lo que responde la API ya desplegada', 't2'),
        nodo(0, 262, 380, 70, '1 · Exportar champion', 'a models/modelo_mlflow', c2='t3'), nodo(398, 262, 380, 70, '2 · Construir y publicar', 'la imagen con la versión en su etiqueta', c2='t3'),
        nodo(796, 262, 380, 70, '3 · Desplegar', 'o cargar por alias al arrancar', c2='t3'),
        fl_g('g1', (381, 297), (396, 297)), fl_g('g1', (779, 297), (794, 297)),
    ]), 'El alias gobierna el registro de MLflow, pero la imagen Docker de la API copia el modelo al construirse y no lee el registro', 'g1')
    slide('D', 1, 'Qué gobierna el alias', 'y qué no', 'El alias gobierna el registro, no la API ya desplegada', f'''
{dg(gob)}
<p class="fte">Abajo, lo que unirá las dos cosas en un sistema real: **aquí no se implementa** (laboratorio-mlops/guia.md, apartado 4.5).</p>''',
          nota('El alias gobierna el registro de MLflow y a cualquiera que cargue models:/retencion-90d@champion. No gobierna la imagen Docker de la API: esa imagen copia models/modelo_mlflow al construirse y no lee el registro. Mover champion cambia el registro, no lo que responde la API ya desplegada. Un sistema real los uniría con tres pasos, que aquí no se implementan.',
               'Es la diferencia entre «he movido el puntero» y «el cliente ya recibe el modelo nuevo»: hace falta exportar, construir con la versión en la etiqueta y desplegar.',
               '¿Qué pasaría en producción si alguien mueve champion y nadie reconstruye la imagen?',
               'laboratorio-mlops/guia.md, apartado 4.5; 04-Proyecto-Base/docs/mlops-clasico.md, «Lo que el alias gobierna y lo que no».'))

    flujo = svg(1176, 200, ''.join([
        nodo(0, 40, 200, 110, 'Candidata', 'otros datos o', 'otro prompt'),
        nodo(236, 40, 230, 110, 'Puerta de calidad', 'regla escrita antes', 'AUC test: tolerancia 0,02', cls='nodo puerta', c3='t3'),
        nodo(502, 40, 210, 110, 'Aprobación', 'una persona', 'environment produccion'),
        nodo(748, 40, 210, 110, 'Publicar + PR', 'imagen en GHCR y', 'PR de ficha e historial'),
        nodo(994, 40, 182, 110, 'Fusionar', 'el PR: ahora sí', 'es producción', cls='nodo ok'),
        fl_g('f1', (201, 95), (234, 95)), fl_g('f1', (467, 95), (500, 95)), fl_g('f1', (713, 95), (746, 95)), fl_g('f1', (959, 95), (992, 95)),
        fl_r('f1', (350, 152), (350, 186)), tx(350, 198, 'rechazada: no se construye ni se publica nada', 'tc'),
    ]), 'Candidata, puerta de calidad, aprobación, publicación con PR y fusión del PR', 'f1')
    slide('D', 1, 'Puerta y aprobación', 'actualizar con seguridad', 'Actualizar: candidata, puerta, aprobación y PR fusionado', f'''
{dg(flujo)}
{grid(3, card('Aceptada no es «mejor»', ['La puerta comprueba que **no empeora** lo medido; una persona decide si merece la pena']),
      card('Rechazada es válida', ['Es un resultado correcto de la puerta, bien explicado con cifras']),
      card('Antes del PR, no es producción', ['Una imagen publicada y sin fusionar es una **candidata**']))}''',
          nota('El ciclo es siempre el mismo: una candidata se evalúa, una puerta con reglas escritas antes la compara con la de producción, una persona aprueba y se publica la imagen y se abre un PR que cambia la ficha y el historial. Hasta fusionar el PR, la candidata no es la de producción. En el modelo del caso, el AUC de test no puede empeorar más que una tolerancia, por defecto 0,02.',
               'En S4, la v2 con datos completos existía en GHCR pero la ficha seguía diciendo v1 hasta fusionar el PR. En el agente, un prompt nuevo con tolerancia -0,10 se rechazó y no se construyó ni se publicó nada.',
               '¿Quién debería poder aprobar en tu equipo, y quién no?',
               'S4 laboratorio-produccion-e2e/guia.md (apartado 0 y 5.7); laboratorio-agentes/guia.md, 7.5 y 7.6; teoria/README.md, apartado 6.'))

    des = ''.join([
        card('1 · No reevalúa ni reconstruye', ['Restaura la **ficha** de una versión anterior desde el historial de git y abre un PR', 'No borra imágenes ni historial']),
        card('2 · Solo se vuelve a lo publicado', [f'El rollback a la v1 del agente **se paró** (run {RUN_ROLLBACK_PARADO}): esa imagen nunca estuvo en GHCR', 'Publica siempre la primera versión']),
        card('3 · Git y MLflow son dos sitios', [f'El PR cambia git; los alias viven en el servidor de MLflow', f'En el laboratorio ese servidor es efímero: el rollback **no mueve MLflow** de verdad (run {RUN_ROLLBACK_ENSAYO})'])])
    slide('D', 1, 'Deshacer', 'tres límites', 'Deshacer: tres cosas que enseñó el laboratorio', f'''
{grid(3, des)}
{msg('Volver atrás es rápido **porque no se borró nada**.')}''',
          nota('El rollback del laboratorio de agentes enseñó tres límites. Primero, no reevalúa ni reconstruye: restaura la ficha anterior desde git y abre un PR. Segundo, solo se vuelve a lo que se publicó: el rollback a la v1 se paró a propósito porque esa imagen nunca estuvo en GHCR. Tercero, git y MLflow son dos sitios, y el servidor de MLflow del laboratorio es efímero.',
               f'Run {RUN_ROLLBACK_PARADO} (parado a propósito) y run {RUN_ROLLBACK_ENSAYO} (la variante que ensaya el mecanismo completo). Con un servidor de MLflow permanente haría falta además mover el alias allí.',
               '¿Qué versión de tu proyecto no podrías restaurar hoy porque nunca se publicó?',
               'teoria/README.md, apartado 6; laboratorio-agentes/guia.md, 7.8 y 10.'))

    # ------------------------------------------------------------------------------------------------ E · Avisar y mantener el orden
    mon = svg(1176, 290, ''.join([
        nodo(0, 30, 300, 100, '1 · Preparar datos y modelo', 'base y modelo desde la muestra', c2='t3'),
        nodo(340, 30, 360, 100, '2 · Deriva de datos y de rendimiento', 'salida 0 · 1 · 2', 'un 1 es un resultado, un 2 es un error', c2='t2', c3='t3'),
        nodo(740, 30, 436, 100, '3 · Alerta (solo si hubo un 1)', 'abre un issue «alerta-deriva»', 'o comenta el que ya hay · run en ROJO', cls='nodo mal', c3='t3'),
        fl_g('m1', (301, 80), (338, 80)), fl_g('m1', (701, 80), (738, 80)),
        nodo(0, 170, 380, 96, 'Disparadores', 'cada día · a mano · ramas lab/monitoreo/*', c2='t3'),
        nodo(420, 170, 380, 96, 'Una alerta buena', 'accionable · rara · con dueño', c2='t3'),
        nodo(840, 170, 336, 96, 'Sin duplicados', 'repetir el run añade un comentario', cls='nodo ok', c2='t3'),
    ]), 'Workflow de monitoreo: preparar, medir deriva y, si hay deriva, abrir un issue y terminar en rojo', 'm1')
    slide('E', 1, 'Alertas', 'el rojo y un issue', 'Una alerta es un run en rojo y un issue, sin duplicados', f'''
{dg(mon)}
<p class="fte"><b>Sin verificar</b> en esta teoría: el permiso `issues: write` con `gh issue create` y los minutos de Actions del workflow (<b>sin dato</b>). El README de S5 recoge el ensayo del 26/11/2026; la guía del laboratorio A conserva esos avisos. Alertas de Cloud Monitoring: sin verificar en el curso.</p>''',
          nota('Una alerta, en GitHub Actions, es un workflow que falla o que abre un aviso. El workflow de monitoreo hace lo mismo que las órdenes de deriva, pero cada día y sin que nadie mire; si alguna medición da salida 1, abre un issue con la etiqueta alerta-deriva o comenta el que ya está abierto, y termina el run en rojo. Una alerta buena es accionable, rara y con dueño.',
               'Un aviso que nadie lee no protege. Con los datos congelados del curso, el schedule diario avisaría siempre: por eso al terminar el laboratorio se desactiva el workflow y se borran las ramas de ensayo.',
               '¿Quién recibiría la alerta en tu equipo y qué haría en los primeros diez minutos?',
               'laboratorio-mlops/guia.md, apartado 5 y 8; laboratorio-mlops/monitoreo.yml; S5/README.md (estado del laboratorio A).'))

    coste = svg(1176, 190, ''.join([
        nodo(0, 40, 270, 100, 'Presupuesto', 'con alertas, antes de todo', cls='nodo puerta', c2='t3'),
        nodo(308, 40, 200, 100, 'CREA'), nodo(546, 40, 200, 100, 'PRUEBA'), nodo(784, 40, 200, 100, 'BORRA'),
        nodo(1022, 40, 154, 100, 'Comprueba', 'que no queda nada', c2='t3', cls='nodo ok'),
        fl_g('k1', (271, 90), (306, 90)), fl_g('k1', (509, 90), (544, 90)), fl_g('k1', (747, 90), (782, 90)), fl_g('k1', (985, 90), (1020, 90)),
        tx(135, 170, 'avisa, NO corta el gasto', 'tg mal'),
    ]), 'Presupuesto con alertas antes de crear nada; después crear, probar, borrar y comprobar', 'k1')
    slide('E', 1, 'Costes y orden', 'avisar no es cortar', 'Un presupuesto avisa, no corta: crea antes y borra lo creado', f'''
{dg(coste)}
{grid(3, card('Mientras existe, cuesta', ['Un recurso olvidado sigue cobrando, lo uses o no']),
      card('Actions y LLM local', ['Repositorio público: minutos gratis; privado: cuentan contra tu cuota', 'Un LLM local no cobra por llamada, pero ocupa **2,1 GB** de disco']),
      card('Google Cloud', ['Precios, créditos y cuotas: **sin verificar**. Consulta la página oficial y anota la fecha', 'Sin cifras de precio en este curso']))}''',
          nota('Cada recurso en la nube cuesta mientras existe. Un presupuesto con alertas avisa pero no corta el gasto: el propio script del curso lo dice y manda comprobarlo en la documentación vigente. Se crea antes que cualquier recurso. La regla de S4 es CREA, PRUEBA, BORRA: lo que creas, lo borras y lo compruebas.',
               'En este laboratorio no se usa la nube de pago: L1 a L3 corren en el Codespace y L4 en minutos de Actions. Lo que se borra al terminar: las ramas lab/monitoreo/*, el issue, la etiqueta alerta-deriva y el workflow, desactivado.',
               'Tu presupuesto llega al 100 %: ¿se ha detenido el gasto? ¿Qué haces?',
               '04-Proyecto-Base/deploy/gcp/preparar_proyecto.sh; laboratorio-mlops/guia.md, apartado 6; laboratorio-agentes/CONFIGURAR-REPOSITORIO.md, punto 3; laboratorio-agentes/guia.md (apartado 3.3, 2,1 GB).'))

    slide('E', 1, 'Seguridad y registros', 'nada del cliente, nada de claves', 'Un registro no lleva datos del cliente ni claves', f'''
<div class="sino">
 <div class="si"><b>Sí se registra</b>{lista(['La ruta y el código de respuesta', 'Cuánto tardó', 'La versión del modelo y la huella de los datos', 'Un evento por petición, en líneas JSON'])}</div>
 <div class="no"><b>Nunca se registra</b>{lista(['Nombres, correos ni teléfonos', 'El contenido de la petición completa', 'Claves ni tokens'])}</div>
</div>
{callout('Un registro es una copia de los datos que **nadie protege como protege la base**: lo que no se escribe no se puede filtrar.')}
{grid(3, card('Sin claves en el repo', ['Los workflows del agente no usan secretos; el resto, el `GITHUB_TOKEN` de cada run']),
      card('Contrato estricto', ['422 si la petición no cumple el contrato: no llega al modelo']),
      card('Permisos mínimos', ['`permissions:` en cada workflow y aprobación humana en `produccion`']))}''',
          nota('Un registro es lo que el sistema cuenta de sí mismo y es una copia de los datos que nadie protege como la base. Por eso se registra qué ruta, qué código, cuánto tardó, qué versión del modelo y qué huella de datos, y nunca nombres, correos, teléfonos, el contenido de la petición completa ni claves o tokens. En el caso Retail solo existe el número de cliente y su país.',
               'Las herramientas del agente tampoco devuelven nombres, correos ni teléfonos. La rúbrica de S2 exige «registro sin datos del cliente».',
               'Escribe tres campos que nunca irían a un registro y di por qué.',
               'teoria/README.md, apartados 4 y 5; 02-Proyecto-Transversal/alumno/rubrica-avance.md (avance 2); laboratorio-agentes/guia.md (L1).'))

    # ------------------------------------------------------------------------------------------------ F · Agentes
    verbos = [('Se prueba', 'seis niveles; el bucle\ncon un LLM falso'), ('Se evalúa', '25 preguntas de oro'),
              ('Se versiona', f'huella del agente\n{HUELLA_AGENTE}'), ('Se aprueba', 'puerta + environment\nproduccion + PR'),
              ('Se deshace', 'workflow de rollback\ny alias de MLflow')]
    ag = []
    for i, (v, a) in enumerate(verbos):
        x = i * 240
        ag.append(nodo(x, 10, 216, 150, v, a, c2='t3'))
        if i < 4:
            ag.append(fl_g('s1', (x + 217, 85), (x + 238, 85)))
    ag.append(sh_modelo(100, 200, 360, 100, 'Modelo de ML', 'decide: la probabilidad', 'de volver a comprar'))
    ag.append(nodo(560, 200, 360, 100, 'LLM', 'orquesta y redacta', 'no decide'))
    ag.append(fl_g('s1', (461, 250), (558, 250)))
    ag.append(tx(1050, 250, 'El agente llama al', 'tc')); ag.append(tx(1050, 268, 'modelo mediante herramientas', 'tc'))
    agente = svg(1176, 318, ''.join(ag), 'Un agente es software: se prueba, se evalúa, se versiona, se aprueba y se deshace; el modelo de ML decide y el LLM orquesta', 's1')
    slide('F', 1, 'Agente es software', 'lo mismo que el modelo', 'Un agente es un sistema de software más', f'''
{dg(agente)}
{msg('El modelo de ML **decide**; el LLM solo **orquesta y redacta**.')}''',
          nota('El mensaje del laboratorio de agentes cierra el curso: un agente es un sistema de software más, y se opera como cualquier otro. Se prueba, se evalúa, se versiona con una huella (prompt, modelo y skills: una coma de una skill es otra versión), se aprueba y se puede deshacer. El modelo de ML sigue decidiendo; el LLM solo orquesta y redacta.',
               f'La huella del agente de la v1 es {HUELLA_AGENTE}. Dos avisos honestos: un LLM no es determinista (por eso se compara con tolerancia y no a igualdad) y que una skill se cargue no garantiza que se use bien.',
               '¿Qué parte de tu agente cambia sin que cambie una sola línea de código?',
               'teoria/README.md, apartado 8; laboratorio-agentes/guia.md, 4.4 y 6.'))

    niveles = [['1', 'Herramientas', 'ninguno'], ['2', 'Protocolo MCP', 'ninguno'], ['3', 'Agente con **LLM falso**', 'falso'],
               ['4', 'Evaluación con LLM real', 'local'], ['5', 'Seguridad', 'local'], ['6', 'Humo del despliegue', 'falso']]
    total_oro = sum(n for _, n in PREGUNTAS_ORO)
    segs, x0 = [], 0
    cols = ['b1', 'bam', 'br', 'b2']
    for (nombre, n), c in zip(PREGUNTAS_ORO, cols):
        w = n / total_oro * 560
        segs.append(f'<rect x="{x0:g}" y="30" width="{w:g}" height="50" class="{c}"/>' + tx(x0 + w / 2, 62, str(n), 't1'))
        segs.append(tx(x0 + w / 2, 104, nombre, 't3'))
        x0 += w
    oro = svg(560, 120, ''.join(segs) + tx(0, 18, f'{total_oro} preguntas de oro', 't1 izq'), '25 preguntas de oro: 11 normales, 6 trampas, 5 de seguridad y 3 de sentido', 'o1')
    slide('F', 1, 'Pruebas y evaluación', 'seis niveles y 25 preguntas', 'Se prueba con un LLM falso y se evalúa con 25 preguntas de oro', f'''
<div class="split2">
 <div class="col">{tabla(['Nivel', 'Qué prueba', 'LLM'], niveles, 'cos')}
 {callout('El LLM falso **sabe la solución**: prueba el **sistema**, no el LLM. Si no da 100 %, falla tu montaje.')}</div>
 <div class="col">{dg(oro)}
 <p class="small">Las cifras esperadas se **calculan** con las herramientas, no se escriben a mano.</p>
 {term('Terminal bash · desde 04-Proyecto-Base (L5 del laboratorio B)', ['python -m ia_mlops.agente.evaluacion evaluar --llm falso'])}</div>
</div>''',
          nota('Un agente se prueba en seis niveles: herramientas, protocolo MCP, el bucle con un LLM falso (rápido y siempre igual), evaluación con el LLM real, seguridad y el humo del despliegue. Y se evalúa con 25 preguntas de oro: 11 normales, 6 trampas, 5 de seguridad y 3 de sentido. Las cifras esperadas se calculan llamando a las herramientas sobre tus datos, así que las preguntas siguen valiendo si cambian los datos.',
               'El LLM falso es un oráculo: con él se espera 100 % en todo; si no da 100 %, falla el montaje y no el LLM. Con el LLM falso la comparación puede decir «aceptada»: no vale para publicar nada.',
               '¿Qué te dice un 100 % con el LLM falso, y qué NO te dice?',
               'laboratorio-agentes/guia.md, apartados 6.1, 6.2 y 6.4.'))

    ejeb = 270
    gb = []
    for i, ((nombre, v1), v2) in enumerate(zip(EVAL_PRIMERA, EVAL_CORREGIDA)):
        x = 50 + i * 130
        gb.append(f'<rect x="{x}" y="{ejeb - v1 * 2.2:g}" width="48" height="{v1 * 2.2:g}" class="bg"/><rect x="{x + 52}" y="{ejeb - v2 * 2.2:g}" width="48" height="{v2 * 2.2:g}" class="b1"/>')
        gb.append(tx(x + 24, ejeb - v1 * 2.2 - 6, f'{v1} %', 't3')); gb.append(tx(x + 76, ejeb - v2 * 2.2 - 6, f'{v2} %', 't1'))
        gb.append(tx(x + 50, ejeb + 22, nombre, 't3'))
    gev = svg(600, 330, '<line x1="40" y1="270" x2="590" y2="270" class="eje"/>' + ''.join(gb) +
              '<rect x="40" y="2" width="14" height="14" class="bg"/>' + tx(60, 14, 'primera pasada', 't3 izq') +
              '<rect x="220" y="2" width="14" height="14" class="b1"/>' + tx(240, 14, 'regla del evaluador corregida', 't3 izq'), 'Primera pasada del evaluador frente a la corregida: 64 % a 96 % en sin inventar', 'e1')
    slide('F', 1, 'El evaluador se prueba', 'una métrica que sorprende', 'El evaluador también se prueba: 64 % pasó a 96 %', f'''
<div class="split2">
 <div class="col">{dg(gev)}</div>
 <div class="col">{callout('En la primera pasada, el «sin inventar» salió **64 %**. Muchos «fallos» eran **del evaluador**: contaba como cifras inventadas las **fechas**, los números **dentro de nombres de variable** (`frecuencia_180d`) y el «100 %».')}
 {msg('Si una métrica te sorprende, revisa **primero la regla que la mide**.')}</div>
</div>''',
          nota('Lección del laboratorio de agentes: las reglas del evaluador se corrigieron tras ver la primera pasada. La primera dio 76 % de herramienta, 64 % de sin inventar, 50 % de trampas y 44 % de respuestas correctas; muchos fallos eran del evaluador. Tras corregirlo: 80, 96, 86 y 76 por ciento. Es honesto decirlo: las reglas se corrigieron DESPUÉS de ver el resultado, y eso se declara.',
               'Contaba como cifras inventadas las fechas, los números dentro de nombres de variable como frecuencia_180d y el «100 %». Un evaluador sin pruebas puede aprobar o rechazar por razones equivocadas.',
               '¿Cómo probarías que tu evaluador no se equivoca? ¿Qué casos le pondrías?',
               'laboratorio-agentes/guia.md, apartados 6.5 y 6.6.'))

    reglas = [('1', 'Rechazada', 'si falla alguna pregunta **crítica**: siempre, sin tolerancia'), ('2', 'Error', 'si las preguntas no son las de la referencia'),
              ('3', 'Igual', 'si la huella del agente es la de la referencia'), ('4', 'Rechazada', 'si herramienta o «sin inventar» caen más que la tolerancia (0,10, provisional)'),
              ('5', 'Aceptada', 'en otro caso, y falta la aprobación humana')]
    escalera = ''.join(f'<div class="paso2"><b>{n}</b><span><b class="r">{esc(r)}</b> {md(t)}</span></div>' for n, r, t in reglas)
    slide('F', 1, 'Puerta del agente', 'escrita antes', 'Una puerta escrita después de ver el resultado no es una puerta', f'''
<div class="split2">
 <div class="col"><div class="ladder">{escalera}</div>
 {term('Terminal bash · desde 04-Proyecto-Base', ['python -m ia_mlops.agente.evaluacion comparar --resultados evaluacion.json --json decision.json'])}</div>
 <div class="col">{callout(f'Ejemplo real: con tolerancia **-0,10** (se exige **mejorar** 0,10) un prompt nuevo fue **rechazado** (run {RUN_RECHAZO}): «sin inventar» ya estaba en 0,96 y no podía subir tanto. No se construyó ni se publicó nada.')}
 {msg('Tolerancia y reglas se acuerdan **antes** de ver el resultado.')}
 <p class="small">La tolerancia de 0,10 es **provisional**. Una tolerancia negativa es una exigencia de mejora. **Declarar lo no hecho no resta; fingirlo, sí.**</p></div>
</div>''',
          nota('La puerta de calidad compara tu evaluación con la referencia del agente, en este orden: rechazada si falla una pregunta crítica, error si las preguntas no son comparables, igual si la huella es la misma, rechazada si herramienta o sin inventar caen más que la tolerancia, y aceptada en otro caso. El orden importa, y las reglas se escriben antes de ver el resultado: una puerta escrita después de ver el resultado no es una puerta.',
               f'El run {RUN_RECHAZO} terminó en rojo a los 13 min 37 s y los trabajos siguientes se omitieron: es un resultado válido, no un fallo del sistema. Con 25 preguntas, cada una vale 4 puntos, así que 0,10 deja pasar dos fallos de más.',
               'Si la tolerancia la fijas después de ver el AUC de tu candidata, ¿qué estás midiendo realmente?',
               'laboratorio-agentes/guia.md, apartados 6.7 y 7.5; tarea/README.md, (c) 1.'))

    # ------------------------------------------------------------------------------------------------ G · Cierre y tarea
    mapa = [['Huella → ficha → imagen; versionar', 'Laboratorio B · 4.4 (prompt y agente versionados) y 7.6 (PR)', '!<a href="../laboratorio-agentes/guia.md">guía B</a>'],
            ['Servicio frente a calidad', 'Laboratorio B · 6.3 a 6.5 (métricas)', '!<a href="../laboratorio-agentes/guia.md">guía B</a>'],
            ['Deriva de datos: PSI y KS', 'Laboratorio A · L1', '!<a href="../laboratorio-mlops/index.html">presentación A</a>'],
            ['Deriva de rendimiento: AUC por corte', 'Laboratorio A · L2', '!<a href="../laboratorio-mlops/guia.md">guía A</a>'],
            ['Alias `champion`, promover y volver', 'Laboratorio A · L3', '!<a href="../laboratorio-mlops/index.html">presentación A</a>'],
            ['Alertas con Actions', 'Laboratorio A · L4', '!<a href="../laboratorio-mlops/monitoreo.yml">monitoreo.yml</a>'],
            ['Costes y orden', 'Laboratorio A · L5', '!<a href="../laboratorio-mlops/guia.md">guía A</a>'],
            ['Registros sin datos del cliente', 'Laboratorio B · L1 y nivel 5 de pruebas', '!<a href="../laboratorio-agentes/index.html">presentación B</a>'],
            ['Agente: pruebas, evaluación, puerta, aprobación y rollback', 'Laboratorio B · L5 y L6 (6 y 7)', '!<a href="../laboratorio-agentes/guia.md">guía B</a>']]
    slide('G', 1, 'Mapa de prácticas', 'idea y laboratorio', 'Cada idea, en el laboratorio donde se practica', f'''
{tabla(['Idea de esta teoría', 'Dónde se practica', 'Enlace'], mapa, 'cos')}
<div class="botones">{enlace('../laboratorio-mlops/index.html', 'Laboratorio A')} {enlace('../laboratorio-agentes/index.html', 'Laboratorio B')} {enlace('../clase-fundamentos-ia-agentes/index.html', 'Clase de fundamentos')}</div>''',
          nota('Es el mapa para que, en cada laboratorio, el alumnado sepa qué idea de esta teoría está practicando. El laboratorio A cubre deriva, alias, alertas y costes. El B cubre cómo se opera un agente: pruebas, evaluación, puerta, aprobación y rollback. La clase de fundamentos explica qué es cada pieza (LLM, RAG, agentes) si alguien necesita el contexto.',
               'Cuando en L3 del laboratorio A muevan el alias, que lo conecten con la diapositiva «Un alias es un puntero» y con la limitación: la API ya desplegada no se mueve sola.',
               '¿Qué idea de las anteriores te parece que se va a atascar en el laboratorio y por qué?',
               'laboratorio-mlops/guia.md (tabla inicial); laboratorio-agentes/guia.md (apartados 4 a 7); guion.md.'))

    slide('G', 1, 'Tarea y evidencia', 'entrega final', 'La tarea: aplicar todo esto a tu caso propio', f'''
<div class="split2b">
 <div class="col">{tabla(['', 'Qué se pide'], [
     ['**(a)**', 'Repositorio consolidado con README reproducible y **sin secretos**'], ['**(b)**', 'Workflows de Actions en verde, con **enlace a cada ejecución**'],
     ['**(c)**', 'Nueva versión con **puerta** escrita antes, aprobación humana, **rollback** y una decisión explicada'],
     ['**(d)**', 'Comprobación de deriva (orden de filas o PSI) con umbral justificado y alerta'], ['**(e)**', 'Informe corto: limitaciones, costes y lo que no pudiste ejecutar'],
     ['**(f)**', 'Demostración: **la que indique el instructor** (por confirmar)']], 'cos')}</div>
 <div class="col">{card('Entrega', ['**11 de diciembre, 10:00** (hora de Perú), rama `avance-5`', 'Con el formulario del curso'])}
 {card('Por confirmar', ['Cómo y dónde es la demostración (vídeo o en vivo)', 'Pesos de la rúbrica: 20 % / 40 % / 40 % son una **propuesta**'], clase='aviso')}
 {callout('Evidencia mínima: workflows con sus enlaces, ficha e historial **antes y después**, decisión de la puerta, PRs y la comprobación de deriva.')}</div>
</div>''',
          nota('La tarea es la entrega final de su caso propio (Bank Marketing): seis partes, y la (b) y la (c) son las que más pesan. Se entrega el viernes 11 de diciembre a las 10:00, hora de Perú, en la rama avance-5. Dos cosas siguen por confirmar: cómo y dónde se hace la demostración (la que indique el instructor) y los pesos de la rúbrica (propuesta: 20 % reproducibilidad, 40 % técnica, 40 % análisis y decisión).',
               'Una puerta rechazada bien explicada vale tanto como una aceptada. No se pegan claves, tokens, el ID del proyecto, el correo ni el identificador de facturación: se tapan también las capturas.',
               '¿Qué parte de la tarea te preocupa más y qué necesitas hoy para desbloquearla?',
               'tarea/README.md y tarea/rubrica.md; S5/README.md (fecha de entrega).'))

    mensajes = [('1', 'Operar es una disciplina', 'no una tarea al final'), ('2', 'Servicio sano ≠ modelo bueno', 'se miden por separado'),
                ('3', 'La deriva de datos avisa', 'la de rendimiento confirma, tarde (90 días)'), ('4', 'Un registro no lleva', 'datos del cliente ni claves'),
                ('5', 'Un presupuesto avisa', 'no corta; crea antes y borra lo creado'), ('6', 'Un agente es software', 'se prueba, evalúa, versiona, aprueba y deshace'),
                ('7', 'Una puerta escrita después', 'de ver el resultado no es una puerta'), ('8', 'Declarar lo no hecho', 'no resta; fingirlo, sí')]
    cel = ''.join(f'<div class="card kpi"><span class="nv">{n}</span><b class="n">{esc(a)}</b><p class="small">{esc(b)}</p></div>' for n, a, b in mensajes)
    slide('G', 1, 'Resumen', 'ocho mensajes', 'Lo que no debe perderse', f'''
<div class="grid4">{cel}</div>''',
          nota('Cierre con los ocho mensajes. Si solo se llevan uno: un modelo en producción se vigila, se versiona y se puede deshacer, y un agente se opera igual. La puerta de calidad se escribe antes de ver el resultado y lo no hecho se declara.',
               'Cada mensaje tiene su diapositiva y su práctica: 1 y 2 en las cinco preguntas y el servicio; 3 en la deriva; 4 y 5 en registros y costes; 6 y 7 en agentes; 8 en la tarea.',
               '¿Cuál de los ocho te parece más fácil de olvidar con prisa?',
               'guion.md, «Mensajes que no deben perderse»; teoria/README.md.'))

    qs = [('¿Qué dos archivos y qué etiqueta necesitas para saber con qué datos se hizo el modelo que sirve la API?',
           'La ficha `models/referencia.json` (con `huella_datos`) y `historial_versiones.json` (el estado). La etiqueta de la imagen, `retencion-api:v<N>-<huella>`, lleva la huella: de la imagen se llega a los datos.'),
          ('Tu API responde 200 en 15 ms y el AUC cae. ¿Qué métricas lo muestran y cuáles no?',
           'Lo muestran las de **calidad** (AUC, y en el agente el acierto de herramienta). No lo muestran las del servicio (latencia, errores, disponibilidad): la API sigue devolviendo 200.'),
          ('¿Por qué la deriva de rendimiento del caso Retail solo se puede medir con 90 días de retraso?',
           'Porque la etiqueta es «¿compró en los 90 días siguientes?»: la respuesta correcta de una predicción de hoy llega dentro de 90 días. Hasta entonces solo se mira la deriva de datos.'),
          ('Escribe tres campos que nunca irían a un registro, y por qué.',
           'Por ejemplo nombre, correo y teléfono (o el contenido completo de la petición, o una clave). Un registro es una copia de los datos que nadie protege como la base: lo que no se escribe no se filtra.'),
          ('¿Por qué un rollback a una versión que nunca se publicó falla, y qué harías para que no pase?',
           f'Porque el rollback restaura la ficha desde git y su imagen tiene que existir en GHCR: lo que no está publicado no se restaura (run {RUN_ROLLBACK_PARADO}). Publicar siempre la primera versión.')]
    qa = ''.join(f'<div class="qa"><div class="q"><span class="qn">{i + 1}</span><span>{esc(q)}</span><button class="rev" type="button" aria-expanded="false">ver respuesta</button></div>'
                 f'<div class="ans" hidden>{md(a)}</div></div>' for i, (q, a) in enumerate(qs))
    slide('G', 1, 'Autoevaluación', '5 preguntas', 'Cinco preguntas para comprobar que lo entiendes', f'<div class="qas">{qa}</div>',
          nota('Deje un minuto para que respondan por su cuenta y después pulse «ver respuesta» de cada una. Las respuestas están ocultas hasta pulsar, sin librerías: un botón que muestra u oculta el párrafo. Es autoevaluación, no examen.',
               'Si una respuesta del aula se aparta de la de la diapositiva, vuelva a la diapositiva de origen: la 1 a la de la huella, la 2 a servicio y modelo, la 3 a las dos derivas, la 4 a registros y la 5 a deshacer.',
               '¿Cuál de las cinco preguntas has contestado distinto de lo que pone aquí, y por qué?',
               'teoria/README.md, apartado 11 (las seis preguntas originales; aquí, cinco).'))

    grupos = ''.join(f'<div class="fgrp"><h3>{esc(g)}</h3><ul>' + ''.join(f'<li><a href="{esc(h)}">{esc(t)}</a></li>' for h, t in items) + '</ul></div>'
                     for g, items in FUENTES_LOCALES)
    slide('G', 0, 'Fuentes', 'archivos del repositorio', 'Fuentes: archivos del repositorio del curso', f'''
<div class="fuentes">{grupos}</div>
<p class="sv"><b>Sin verificar:</b> no se cita documentación externa (MLflow, Google Cloud ni GitHub): no se comprobó en esta presentación. Precios, créditos y cuotas de Google Cloud, sin cifra. Estado de las ejecuciones en Actions: el que recogen las guías, con fecha.</p>
<p class="fte">Cada cifra de la presentación se comprueba contra estos archivos en pruebas/test_presentacion.py. La única cifra calculada aquí es la de la diapositiva «Ilustración PSI».</p>''',
          nota('Todo lo que se ha dicho sale de archivos del repositorio del curso, que son enlaces. La documentación oficial externa no se cita: no se ha comprobado en esta presentación y por eso se dice. Las cifras tienen su fuente en la guía de cada laboratorio; las pruebas de la carpeta pruebas/ las comprueban.',
               'Si alguien quiere una cifra que no está aquí (precios de Google Cloud, minutos de Actions del workflow de monitoreo), la respuesta es «sin dato» o «sin verificar»: consulta la página oficial y anota la fecha.',
               '¿Qué fuente te falta para defender tu umbral de PSI?',
               'Todos los archivos listados en esta diapositiva.'))


CSS = r"""
:root{--tinta:#1f2937;--suave:#5b6472;--linea:#d6dde6;--fondo:#ffffff;--gris:#f4f6f9;--acento:#0b5cad;--ok:#15803d;--mal:#b91c1c;--aviso:#92400e;
 --mono:Consolas,"Cascadia Mono","DejaVu Sans Mono",Menlo,monospace;--sans:"Segoe UI",system-ui,-apple-system,Arial,sans-serif}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:#e8ecf1;color:var(--tinta);font-family:var(--sans)}
button{font:inherit;color:inherit;background:none;border:0;cursor:pointer}
#viewport{position:fixed;inset:0 0 48px 0;display:flex;align-items:center;justify-content:center;overflow:hidden}
#stage{width:1280px;height:720px;flex:none;position:relative;transform:scale(var(--s,1));background:var(--fondo);box-shadow:0 2px 14px rgba(0,0,0,.12)}
.slide{position:absolute;inset:0;padding:24px 52px 44px;display:none;flex-direction:column;gap:12px;overflow:hidden;background:var(--fondo)}
.slide.active{display:flex}
.bd{flex:1;display:flex;flex-direction:column;justify-content:center;gap:14px;min-height:0}
.kick{font-size:13px;letter-spacing:.09em;text-transform:uppercase;color:var(--acento);font-weight:700}
h1{font-size:30px;line-height:1.15;font-weight:700;margin-bottom:2px}
h3{font-size:21px;margin-bottom:6px}
.sub{font-size:25px;line-height:1.35;color:var(--suave)}
.chips{display:flex;gap:8px;flex-wrap:wrap}
.chip{display:inline-block;font-size:17px;padding:6px 15px;border-radius:999px;border:1px solid #bcd3ec;background:#eef5fc;color:var(--acento);font-weight:600}
.tag{display:inline-block;font-size:12px;padding:1px 9px;border-radius:999px;border:1px solid var(--linea);background:var(--gris);color:var(--tinta);align-self:flex-start}
.tag.ok{border-color:#86c79c;background:#ecf8f0;color:var(--ok)}.tag.warn{border-color:#e2b56b;background:#fdf6e9;color:var(--aviso);font-size:13px;font-weight:700;padding:3px 11px}
.card{border:1px solid var(--linea);border-radius:12px;padding:14px 18px;background:#fff;min-width:0}
.card.verde{border-top:5px solid var(--ok)}.card.azul{border-top:5px solid var(--acento)}.card.aviso{border-top:5px solid #c9a65e;background:#fdf9f0}
.callout{border-left:5px solid var(--acento);background:#eef5fc;padding:11px 18px;border-radius:0 10px 10px 0;font-size:19.5px;line-height:1.4}
.callout.rojo{border-left-color:var(--mal);background:#fdf3f3}
.msg{font-size:24px;line-height:1.3;font-weight:600;border-left:6px solid var(--acento);padding:10px 20px;background:#eef5fc;border-radius:0 12px 12px 0}
.small{font-size:17.5px;line-height:1.42}
.fte{font-size:13px;line-height:1.4;color:var(--suave)}
.mono{font-family:var(--mono);font-size:.92em;background:var(--gris);padding:0 4px;border-radius:4px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
.split2{display:grid;grid-template-columns:1fr 1fr;gap:18px;min-height:0;align-items:center}.split2b{display:grid;grid-template-columns:1.2fr 1fr;gap:18px;align-items:center}
.col{display:flex;flex-direction:column;gap:12px;min-width:0}
.list{list-style:none;display:flex;flex-direction:column;gap:5px}.list li{font-size:18.5px;line-height:1.38;padding-left:17px;position:relative}
.list li::before{content:"";position:absolute;left:2px;top:9px;width:7px;height:7px;border-radius:50%;background:var(--acento)}
.dg{position:relative}.dg svg{display:block;width:100%;height:auto}
.tbl{width:100%;border-collapse:collapse;font-size:18px}.tbl th{text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--suave);border-bottom:2px solid var(--linea);padding:6px 9px}
.tbl td{border-bottom:1px solid var(--linea);padding:9px 10px;line-height:1.3;vertical-align:top}
.tbl.cos td{font-size:16.5px;padding:7px 9px}.tbl.cos th{text-transform:none;font-size:14px;letter-spacing:0}.tbl a{color:var(--acento)}
.botones{display:flex;gap:10px;flex-wrap:wrap}
.btn{display:inline-block;border:1px solid var(--acento);color:var(--acento);border-radius:8px;padding:7px 16px;font-size:16px;font-weight:600;text-decoration:none;background:#fff}
.cover{display:flex;flex-direction:column;gap:20px}.cover .sub{max-width:980px}
.kpi .n{display:block;font-size:20px;line-height:1.2;color:var(--acento);margin:6px 0 4px}
.nv{display:inline-block;width:26px;height:26px;border-radius:50%;background:var(--acento);color:#fff;text-align:center;line-height:26px;font-size:15px;font-weight:700}
/* terminal con COPIAR */
.term{border:1px solid var(--linea);border-radius:10px;background:var(--gris);overflow:hidden}
.term .bar{padding:5px 10px;border-bottom:1px solid var(--linea);background:#eaeef3;font-size:12.5px;color:var(--suave)}.term .bar em{font-style:normal}
.tls{padding:6px 8px;font-family:var(--mono);font-size:13.5px;line-height:1.42}
.tln{display:flex;align-items:flex-start;gap:6px;padding:3px 4px}
.tln code{flex:1;white-space:pre-wrap;overflow-wrap:anywhere;font-family:var(--mono)}
.tln.c{color:var(--suave);font-style:italic}.ps{color:var(--ok);font-weight:700}
.cp{flex:none;min-width:64px;height:24px;border-radius:6px;border:1px solid #b9c3cf;background:#fff;font-size:11.5px;font-weight:700;letter-spacing:.05em;color:var(--suave);padding:0 8px}
.cp.ok{border-color:var(--ok);color:var(--ok)}
/* autoevaluación */
.qas{display:flex;flex-direction:column;gap:9px}.qa{border:1px solid var(--linea);border-radius:12px;padding:10px 16px}
.q{display:flex;gap:12px;align-items:center;font-size:19.5px;line-height:1.3}.q span:nth-child(2){flex:1}.qn{flex:none;width:30px;height:30px;border-radius:50%;background:var(--acento);color:#fff;text-align:center;line-height:30px;font-size:16px}
.rev{flex:none;border:1px solid var(--acento);color:var(--acento);border-radius:8px;padding:5px 14px;font-size:14px;background:#fff}.rev[aria-expanded="true"]{background:var(--acento);color:#fff}
.ans{margin-top:7px;padding:8px 12px;background:#ecf8f0;border-left:5px solid var(--ok);border-radius:0 8px 8px 0;font-size:17px;line-height:1.38}.ans[hidden]{display:none}
/* puerta del agente, tres columnas, sí/no */
.ladder{display:flex;flex-direction:column;gap:7px}.paso2{display:flex;gap:12px;align-items:center;border:1px solid var(--linea);border-radius:10px;padding:8px 13px;font-size:17.5px;line-height:1.3}
.paso2>b{flex:none;width:28px;height:28px;border-radius:50%;background:var(--acento);color:#fff;text-align:center;line-height:28px}.paso2 .r{color:var(--acento)}
.sino{display:grid;grid-template-columns:1fr 1fr;gap:14px}.sino>div{border-radius:12px;padding:12px 16px}.sino .si{background:#ecf8f0}.sino .no{background:#fdf3f3}
.sino>div>b{font-size:20px}.sino .si>b{color:var(--ok)}.sino .no>b{color:var(--mal)}
/* fuentes */
.fuentes{column-count:2;column-gap:26px}.fgrp{break-inside:avoid;margin-bottom:8px}.fgrp h3{font-size:15px;color:var(--acento);margin-bottom:2px}.fgrp ul{list-style:none}
.fgrp li{font-size:13.5px;line-height:1.35}.fgrp li a{color:var(--acento);overflow-wrap:anywhere;text-decoration:none}
.sv{border-left:5px solid #c9a65e;background:#fdf9f0;padding:6px 12px;font-size:14px;border-radius:0 8px 8px 0}
/* svg */
svg .nodo{fill:#f4f8fc;stroke:#8fb2d6;stroke-width:1.6}svg .nodo.puerta{fill:#fdf6e9;stroke:#c9a65e;stroke-dasharray:6 4}svg .nodo.ok{fill:#ecf8f0;stroke:var(--ok)}svg .nodo.mal{fill:#fdeeee;stroke:var(--mal)}
svg .modelo{fill:#dbeafe;stroke:#0b5cad;stroke-width:2.4}svg .modelo2{fill:none;stroke:#0b5cad;stroke-width:1}
svg .datos{fill:#eef2f6;stroke:#6b7a8c;stroke-width:1.8}svg .datos2{fill:none;stroke:#6b7a8c;stroke-width:1.8}
svg .herr{fill:#fff4dc;stroke:#c58a12;stroke-width:2}
svg .zona{fill:#fbfcfe;stroke:#8fb2d6;stroke-dasharray:6 4;stroke-width:1.6}
svg .fl{stroke:var(--acento);stroke-width:2.2;fill:none}svg .fl.g{stroke:#7b8794}svg .fl.r{stroke:var(--mal)}svg .fl.v{stroke:var(--ok)}
svg .eje{stroke:#8a94a3;stroke-width:1.6;fill:none}svg .vida{stroke:#b9c4d2;stroke-width:1.5;stroke-dasharray:5 5}
svg .num{fill:var(--acento)}svg .numt{font:700 15px var(--sans);fill:#fff;text-anchor:middle}
svg .b1{fill:#0b5cad}svg .b2{fill:#a9ccf0}svg .bg{fill:#b9c4d2}svg .br{fill:#e4a3a3}svg .bam{fill:#f0cf8a}
svg .bd1{fill:#cdeed9}svg .bd2{fill:#fbe9b8}svg .bd3{fill:#f6c9c9}
svg .t0{font:700 28px var(--sans);fill:var(--tinta);text-anchor:middle}svg .t1{font:700 18px var(--sans);fill:var(--tinta);text-anchor:middle}
svg .t2{font:16px var(--sans);fill:#4b5563;text-anchor:middle}svg .t3{font:14.5px var(--sans);fill:#4b5563;text-anchor:middle}
svg .tc{font:14.5px var(--sans);fill:#5b6472;text-anchor:middle}svg .tg{font:700 14.5px var(--sans);fill:var(--acento);text-anchor:middle}
svg .mono{font-family:var(--mono);background:none;padding:0}
svg .izq{text-anchor:start}svg .fin{text-anchor:end}svg text.mal{fill:var(--mal);font-weight:700}
.dgz{display:flex;flex-direction:column;align-items:stretch;gap:2px}.dgz .lupa{align-self:flex-end}
.lupa{font-size:12px;background:rgba(255,255,255,.94);border:1px solid var(--linea);border-radius:6px;padding:2px 7px;display:flex;align-items:center;gap:4px;color:var(--suave)}
.foot{position:absolute;left:52px;right:52px;bottom:12px;display:flex;justify-content:space-between;font-size:12px;color:var(--suave);border-top:1px solid var(--linea);padding-top:5px}
#prog{position:fixed;left:0;top:0;height:3px;background:var(--acento);z-index:5}
#bar{position:fixed;left:0;right:0;bottom:0;height:48px;display:flex;align-items:center;gap:5px;padding:0 10px;background:#fff;border-top:1px solid var(--linea);font-size:13px;z-index:6}
#bar button,#bar a{border:1px solid var(--linea);border-radius:8px;padding:4px 9px;background:#fff;color:var(--tinta);text-decoration:none;font-size:13px;white-space:nowrap}
#bar .part.on{border-color:var(--acento);color:var(--acento);font-weight:700}
#bar .sp{flex:1}#count,#clockref{color:var(--suave);padding:0 5px;white-space:nowrap}
#notes{position:fixed;right:0;top:0;bottom:48px;width:420px;background:#fff;border-left:1px solid var(--linea);padding:18px;overflow:auto;display:none;z-index:7;font-size:15px;line-height:1.5}
#notes.on{display:block}#notes h3{margin-bottom:8px}#notes p{margin-bottom:9px}
#index{position:fixed;inset:0 0 48px 0;background:rgba(255,255,255,.98);display:none;z-index:8;padding:28px;overflow:auto}
#index.on{display:block}#index .grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:12px}
#index button{border:1px solid var(--linea);border-radius:10px;padding:10px;text-align:left;font-size:14px;background:#fff}
#index button small{display:block;color:var(--suave);font-size:12px}#index button.cur{border-color:var(--acento)}
#zoombox{position:fixed;inset:0;background:rgba(20,26,34,.88);display:none;z-index:9;align-items:center;justify-content:center;padding:34px;cursor:zoom-out}
#zoombox.on{display:flex}#zoombox svg{width:100%;max-height:100%;background:#fff;border-radius:6px;padding:12px}
#zoombox p{position:fixed;top:8px;left:0;right:0;text-align:center;color:#fff;font-size:13px}
@media print{#bar,#notes,#index,#prog{display:none!important}}
"""

JS = r"""
(function(){
'use strict';
const $=(s,r)=>(r||document).querySelector(s), $$=(s,r)=>[...(r||document).querySelectorAll(s)];
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const NOMBRES=__NOMBRES__;
const slides=$$('.slide'), N=slides.length; let cur=0;
slides.forEach((s,i)=>{const f=document.createElement('div');f.className='foot';
  f.innerHTML=`<span>ML e IA · S5 · MLOps y operación (teoría)</span><span><b>${esc(NOMBRES[s.dataset.part]||'')}</b> · ${i+1} / ${N}</span>`;s.appendChild(f)});
const cum=[];(()=>{let t=0;slides.forEach(s=>{cum.push(t);t+=+s.dataset.min||0})})();
const TOTAL=cum[N-1]+(+slides[N-1].dataset.min||0);
function go(i){i=Math.max(0,Math.min(N-1,i));cur=i;slides.forEach((s,k)=>s.classList.toggle('active',k===i));chrome();try{history.replaceState(null,'','#'+(i+1))}catch(e){}}
function chrome(){const s=slides[cur];
  $('#count').textContent=(cur+1)+' / '+N; $('#clockref').textContent='min '+cum[cur]+' de '+TOTAL;
  $('#prog').style.width=((cur+1)/N*100)+'%';
  $$('#bar .part').forEach(b=>b.classList.toggle('on',b.dataset.p===s.dataset.part));
  $('#notetext').innerHTML=(s.dataset.notes||'').split('\n').map(p=>{const m=p.match(/^([^:]{3,40}):\s?(.*)$/);return '<p>'+(m?'<b>'+esc(m[1])+':</b> '+esc(m[2]):esc(p))+'</p>'}).join('');
  $('#notemin').textContent='Tiempo previsto (propuesta): '+(s.dataset.min||0)+' min · acumulado '+cum[cur]+' min de '+TOTAL;
  $$('#idxgrid button').forEach((b,k)=>b.classList.toggle('cur',k===cur));}
function fit(){const v=$('#viewport');$('#stage').style.setProperty('--s',Math.min(v.clientWidth/1280,v.clientHeight/720).toFixed(4))}
addEventListener('resize',fit);
$('#idxgrid').innerHTML=slides.map((s,i)=>`<button data-i="${i}"><small>${esc(NOMBRES[s.dataset.part]||'')} · ${s.dataset.min||0} min</small>${i+1}. ${esc(s.dataset.title||'')}</button>`).join('');
$('#idxgrid').addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;toggle('#index',false);go(+b.dataset.i)});
function toggle(sel,force){$(sel).classList.toggle('on',force)}
function zoom(on,svg){const z=$('#zoombox');$('#zoomsvg').innerHTML=on&&svg?svg.outerHTML:'';z.classList.toggle('on',!!on)}
$('#zoombox').onclick=()=>zoom(false);
$('#bprev').onclick=()=>go(cur-1); $('#bnext').onclick=()=>go(cur+1);
$('#bidx').onclick=()=>toggle('#index'); $('#bnotes').onclick=()=>toggle('#notes');
$('#bfull').onclick=()=>{if(document.fullscreenElement)document.exitFullscreen();else document.documentElement.requestFullscreen&&document.documentElement.requestFullscreen()};
$$('#bar .part').forEach(b=>b.onclick=()=>go(slides.findIndex(s=>s.dataset.part===b.dataset.p)));
addEventListener('keydown',e=>{
  const t=e.target; if(t&&/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)) return;
  if(e.ctrlKey||e.metaKey||e.altKey) return;
  const k=e.key;
  if(k==='Escape'){zoom(false);toggle('#index',false);toggle('#notes',false);return}
  if($('#zoombox').classList.contains('on')) return;
  if(k==='ArrowRight'||k==='PageDown'||(k===' '&&!/^(BUTTON|A)$/.test(t.tagName))){e.preventDefault();go(cur+1)}
  else if(k==='ArrowLeft'||k==='PageUp'){e.preventDefault();go(cur-1)}
  else if(k==='Home'){e.preventDefault();go(0)} else if(k==='End'){e.preventDefault();go(N-1)}
  else if(k==='o'||k==='O'){toggle('#index')} else if(k==='s'||k==='S'){toggle('#notes')} else if(k==='f'||k==='F'){$('#bfull').click()}
});
let tx=null;
addEventListener('touchstart',e=>{tx=e.touches[0].clientX},{passive:true});
addEventListener('touchend',e=>{if(tx===null)return;const dx=e.changedTouches[0].clientX-tx;tx=null;if(Math.abs(dx)>60){dx<0?go(cur+1):go(cur-1)}},{passive:true});
async function copyText(t){try{await navigator.clipboard.writeText(t);return true}catch(e){try{const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();document.execCommand('copy');a.remove();return true}catch(e2){return false}}}
document.addEventListener('click',async e=>{
  const z=e.target.closest('.zsv'); if(z){e.stopPropagation();zoom(true,z.closest('.dgz').querySelector('svg'));return}
  const r=e.target.closest('.rev'); if(r){e.stopPropagation();const a=r.closest('.qa').querySelector('.ans');const abierto=!a.hidden;a.hidden=abierto;r.setAttribute('aria-expanded',String(!abierto));r.textContent=abierto?'ver respuesta':'ocultar';return}
  const b=e.target.closest('.cp'); if(!b) return; e.stopPropagation();
  const ok=await copyText(b.dataset.t); const t=b.textContent; b.classList.add('ok'); b.textContent=ok?'✓ copiado':'✗'; setTimeout(()=>{b.classList.remove('ok');b.textContent=t},1200)});
fit();
const h=parseInt((location.hash||'').slice(1),10); go(isNaN(h)?0:h-1);
addEventListener('hashchange',()=>{const n=parseInt((location.hash||'').slice(1),10);if(!isNaN(n)&&n-1!==cur)go(n-1)});
})();
"""


def html_completo():
    construir()
    js = JS.replace('__NOMBRES__', json.dumps(NOMBRES_PARTE, ensure_ascii=False))
    partes = ''.join(f'<button class="part" data-p="{k}" title="{esc(NOMBRES_PARTE[k])}">{esc(v)}</button>' for k, v in PARTES.items())
    return ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>MLOps y operación (teoría de S5) · ML e IA: de desarrollo a producción</title>\n'
            f'<!-- Generado por generar.py: no se edita a mano. -->\n<style>{CSS}</style>\n</head>\n<body>\n'
            '<div id="prog"></div>\n<div id="viewport"><div id="stage">\n\n' + '\n\n'.join(SLIDES) + '\n\n</div></div>\n\n'
            '<aside id="notes" aria-label="Notas del profesor"><h3>Notas del profesor</h3><div id="notetext"></div><p class="small" id="notemin"></p></aside>\n'
            '<div id="index" aria-label="Índice"><h2>Índice</h2><div class="grid" id="idxgrid"></div></div>\n'
            '<div id="zoombox" aria-label="Diagrama ampliado"><p>Esc o clic para cerrar</p><div id="zoomsvg"></div></div>\n'
            '<nav id="bar" aria-label="Controles">\n'
            '  <button id="bprev" aria-label="Anterior">←</button><button id="bnext" aria-label="Siguiente">→</button>\n'
            f'  <span id="count">1 / 1</span><span id="clockref" title="Minuto planificado acumulado (propuesta)"></span>\n  {partes}\n'
            '  <span class="sp"></span>\n'
            '  <a id="bhome" href="../index.html" title="Volver al índice de la sesión S5">⌂ Índice</a><button id="bidx">Índice (O)</button><button id="bnotes">Notas (S)</button><button id="bfull">Pantalla completa (F)</button>\n'
            '</nav>\n'
            '<noscript>Esta presentación necesita JavaScript. El mismo contenido está en README.md, en esta carpeta.</noscript>\n\n'
            f'<script>{js}</script>\n</body>\n</html>\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--comprobar', action='store_true')
    a = ap.parse_args()
    nuevo = html_completo()
    actual = SALIDA.read_text(encoding='utf-8') if SALIDA.exists() else None
    if a.comprobar:
        if actual != nuevo:
            print('DESFASADO: ejecuta python generar.py')
            sys.exit(1)
        print('al día')
        return
    if actual == nuevo:
        print('sin cambios')
    else:
        SALIDA.write_bytes(nuevo.encode('utf-8'))      # LF también en Windows
        print(f'escrito {SALIDA.name}')
    minutos = sum(int(m) for m in re.findall(r'data-min="(\d+)"', nuevo))
    print(f'{len(SLIDES)} diapositivas, {minutos} min')


if __name__ == '__main__':
    main()
