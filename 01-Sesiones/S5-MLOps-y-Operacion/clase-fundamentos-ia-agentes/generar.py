"""Genera la clase «Fundamentos de la IA, los LLM, los RAG y los agentes» (index.html y glosario.md, junto a este archivo).

Clase teórica de S5 del curso «ML e IA: de desarrollo a producción» (alumnado técnico de un banco), de una hora:
de lo general (IA, ML, aprendizaje profundo) a lo concreto (LLM, embeddings, RAG, herramientas y MCP, agentes) y su
sitio en Google Cloud. Mismo manejo que las otras presentaciones del curso (← → · O índice · S notas · F pantalla
completa · Esc · lupa para ampliar capturas), fondo blanco y nada que se mueva al pasar el ratón.

Reglas del contenido: cada cifra lleva su fuente; lo que no se pudo comprobar se dice «sin verificar»; los esquemas son
SVG o HTML+CSS escritos aquí (sin imágenes ni recursos externos salvo las capturas reales de la consola, en img/).
Los cálculos de los ejemplos (softmax de la temperatura, coseno) se hacen en este archivo y se enseñan tal cual.

Uso:  python generar.py              escribe index.html y glosario.md
      python generar.py --comprobar  no escribe; sale con 1 si alguno no está al día
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
SALIDA_GLOSARIO = AQUI / 'glosario.md'
CONSULTA = '26/11/2026'

# ----------------------------------------------------------------------------------------------------------------------
# Fuentes (todas consultadas el 26/11/2026). Clave -> (nombre corto, dirección)
# ----------------------------------------------------------------------------------------------------------------------
FUENTES = {
    'dartmouth': ('Dartmouth · El proyecto de verano de 1956', 'https://home.dartmouth.edu/about/artificial-intelligence-ai-coined-dartmouth'),
    'transformer': ('Vaswani et al. · Attention Is All You Need (arXiv, jun 2017)', 'https://arxiv.org/abs/1706.03762'),
    'rag': ('Lewis et al. · Retrieval-Augmented Generation (arXiv, may 2020)', 'https://arxiv.org/abs/2005.11401'),
    'lora': ('Hu et al. · LoRA (arXiv, jun 2021)', 'https://arxiv.org/abs/2106.09685'),
    'rlhf': ('Ouyang et al. · Training language models to follow instructions with human feedback (arXiv, mar 2022)', 'https://arxiv.org/abs/2203.02155'),
    'react': ('Yao et al. · ReAct (arXiv, oct 2022)', 'https://arxiv.org/abs/2210.03629'),
    'mcp_anuncio': ('Anthropic · Introducing the Model Context Protocol (25/11/2024)', 'https://www.anthropic.com/news/model-context-protocol'),
    'mcp_intro': ('Model Context Protocol · What is MCP?', 'https://modelcontextprotocol.io/docs/getting-started/intro'),
    'mcp_arq': ('Model Context Protocol · Architecture overview', 'https://modelcontextprotocol.io/docs/learn/architecture'),
    'agentes': ('Anthropic · Building effective agents', 'https://www.anthropic.com/engineering/building-effective-agents'),
    'plataforma': ('Google Cloud · Gemini Enterprise Agent Platform overview', 'https://docs.cloud.google.com/gemini-enterprise-agent-platform/overview'),
    'garden': ('Google Cloud · Model Garden: explorar modelos', 'https://docs.cloud.google.com/vertex-ai/generative-ai/docs/model-garden/explore-models'),
    'studio': ('Google Cloud · Agent Studio', 'https://docs.cloud.google.com/gemini-enterprise-agent-platform/agent-studio'),
    'embed': ('Google Cloud · Text embeddings', 'https://docs.cloud.google.com/vertex-ai/generative-ai/docs/embeddings/get-text-embeddings'),
    'vs': ('Google Cloud · Vector Search overview', 'https://docs.cloud.google.com/vertex-ai/docs/vector-search/overview'),
    'ragengine': ('Google Cloud · RAG Engine overview', 'https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-overview'),
    'bqvs': ('Google Cloud · BigQuery vector search', 'https://docs.cloud.google.com/bigquery/docs/vector-search-intro'),
    'bqemb': ('Google Cloud · BigQuery: generar embeddings de texto', 'https://docs.cloud.google.com/bigquery/docs/generate-text-embedding'),
    'bqref': ('Google Cloud · BigQuery ML.GENERATE_EMBEDDING (referencia)', 'https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-generate-embedding'),
    'runtime': ('Google Cloud · Agent Runtime (escalar agentes)', 'https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale'),
    'adk': ('Google Cloud · Agent Development Kit (ADK)', 'https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/adk'),
    'obs': ('Google Cloud · Observabilidad de agentes', 'https://docs.cloud.google.com/gemini-enterprise-agent-platform/optimize/observability/overview'),
    'run': ('Google Cloud · ¿Qué es Cloud Run?', 'https://docs.cloud.google.com/run/docs/overview/what-is-cloud-run'),
    'runmcp': ('Google Cloud · Cloud Run: alojar servidores MCP', 'https://docs.cloud.google.com/run/docs/host-mcp-servers'),
    'secretos': ('Google Cloud · Secret Manager overview', 'https://docs.cloud.google.com/secret-manager/docs/overview'),
    'wif': ('Google Cloud · Workload Identity Federation', 'https://docs.cloud.google.com/iam/docs/workload-identity-federation'),
    'logging': ('Google Cloud · Cloud Logging overview', 'https://docs.cloud.google.com/logging/docs/overview'),
}
# Fuentes locales del repositorio del curso (rutas relativas a 01-Sesiones)
LOCALES = {
    'nb02': 'S5-MLOps-y-Operacion/extra-mcp-notebooks/02_mcp_modelo_prediccion.ipynb',
    'nb01': 'S5-MLOps-y-Operacion/extra-mcp-notebooks/01_mcp_datos_sqlite_y_bigquery.ipynb',
    'readme_extra': 'S5-MLOps-y-Operacion/extra-mcp-notebooks/README.md',
    'lab': 'S5-MLOps-y-Operacion/laboratorio-agentes/guia.md',
    'base': 'S1/S2 del curso, 04-Proyecto-Base (modelo de retención a 90 días)',
}


def urls(*claves):
    return '; '.join(f'{FUENTES[c][0]}, {FUENTES[c][1]}' for c in claves)


def nota(decir, ejemplo, pregunta, fuentes=''):
    """Notas del profesor: qué decir (~1 min), un ejemplo y una pregunta para el aula; fuentes con su URL."""
    t = f'Qué decir: {decir}\nEjemplo: {ejemplo}\nPregunta para el aula: {pregunta}'
    if fuentes:
        t += f'\nFuentes (consultadas el {CONSULTA}): {fuentes}'
    return t


PARTES = {'1': 'Mapa', '2': 'ML', '3': 'Redes', '4': 'LLM', '5': 'Vectores', '6': 'RAG', '7': 'Contexto', '8': 'Herram.', '9': 'Agentes', '10': 'GCP', '11': 'Cierre'}
NOMBRES_PARTE = {'1': 'El mapa', '2': 'Datos y ML clásico', '3': 'Aprendizaje profundo y transformers', '4': 'Los LLM', '5': 'Embeddings y búsqueda semántica',
                 '6': 'RAG', '7': 'Dato y contexto', '8': 'Herramientas y MCP', '9': 'Agentes y sistemas agénticos', '10': 'En producción y en Google Cloud', '11': 'Cierre'}


# ----------------------------------------------------------------------------------------------------------------------
# Utilidades de HTML
# ----------------------------------------------------------------------------------------------------------------------
def esc(t):
    return html.escape(t, quote=True)


def md(t):
    """`código`, **negrita** y *cursiva* a HTML (sobre texto ya seguro)."""
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
    """Una celda que empieza por «!» se inserta como HTML tal cual."""
    def celda(c):
        return c[1:] if c.startswith('!') else md(c)
    th = ''.join(f'<th>{md(c)}</th>' for c in cab)
    tr = ''.join('<tr>' + ''.join(f'<td>{celda(c)}</td>' for c in f) + '</tr>' for f in filas)
    return f'<table class="tbl {clase}"><tr>{th}</tr>{tr}</table>'


def kpi(valor, texto, color=''):
    return f'<div class="card kpi"><b class="n {color}">{esc(valor)}</b><p class="small">{md(texto)}</p></div>'


def tag(txt, clase=''):
    return f'<span class="tag {clase}">{esc(txt)}</span>'


def codigo(texto, titulo=''):
    cab = f'<div class="bar"><em>{esc(titulo)}</em></div>' if titulo else ''
    return f'<div class="term">{cab}<pre class="src">{esc(texto.rstrip())}</pre></div>'


def grid(n, *celdas, clase=''):
    return f'<div class="grid{n} {clase}">' + ''.join(celdas) + '</div>'


# ----------------------------------------------------------------------------------------------------------------------
# Capturas reales de la consola (img/). Rótulo = exactamente lo que se ve.
# ----------------------------------------------------------------------------------------------------------------------
LUPA = ('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round">'
        '<circle cx="10" cy="10" r="6.5"/><path d="M15 15l6 6"/></svg>')
CAPTURAS = {
    'gcp-plataforma.webp': 'Consola de Google Cloud (en español): «Plataforma de Gemini», pantalla «Descripción general» (menú: Studio, Modelos, Agentes, Notebooks)',
    'gcp-model-garden.webp': 'Model Garden: colecciones «Modelos de Google», «Modelos de socios» y «Modelos de socios con autoimplementación», y tareas como «Embeddings de textos»',
    'gcp-agent-studio.webp': 'Agent Studio: «Comienza a crear con Agent Studio»; menú «Agentes», «Creador de apps» y «Galería»',
    'gcp-busqueda-vectores.webp': 'Búsqueda de vectores › Índices (región us-central1): «Aún no tienes índices en esta región»',
    'gcp-rag-engine.webp': 'RAG Engine (región us-central1): «No hay corpus de RAG»',
    'gcp-bigquery.webp': 'BigQuery Studio: explorador con conjuntos de datos, conexiones, agentes y notebooks; «Recientes» sin filas (la búsqueda vectorial es SQL, no tiene pantalla propia aquí)',
    'gcp-agent-runtime.webp': 'Implementaciones en Agent Runtime: «No hay instancias de agente»; menú con ADK, Memory Bank, Sesiones y Evaluación',
    'gcp-cloud-run.webp': 'Cloud Run › Descripción general: «Implementa un contenedor», «Crea un trabajo» (aún sin servicios desplegados en la cuenta del curso)',
    'gcp-secret-manager.webp': 'Secret Manager › Secretos: «Este proyecto no contiene secretos»',
    'gcp-iam.webp': 'IAM › Permitir: permisos del proyecto por entidad y rol (correos y nombres difuminados)',
    'gcp-logging.webp': 'Explorador de registros (Cloud Logging): «0 resultados» en los últimos 5 minutos',
    'gcp-trace.webp': 'Explorador de seguimiento (Trace): aviso «El almacenamiento de seguimiento no se inicializó para este proyecto»; sin intervalos',
}
RUTAS_MENU = {
    'gcp-plataforma.webp': 'Plataforma de Gemini › Descripción general', 'gcp-model-garden.webp': 'Plataforma de Gemini › Modelos › Model Garden',
    'gcp-agent-studio.webp': 'Plataforma de Gemini › Studio', 'gcp-busqueda-vectores.webp': 'Plataforma de Gemini › Agentes › Búsqueda de vectores',
    'gcp-rag-engine.webp': 'Plataforma de Gemini › Agentes › RAG Engine', 'gcp-bigquery.webp': 'BigQuery › Studio',
    'gcp-agent-runtime.webp': 'Plataforma de Gemini › Agentes › Implementaciones', 'gcp-cloud-run.webp': 'Cloud Run › Descripción general',
    'gcp-secret-manager.webp': 'Seguridad › Secret Manager › Secretos', 'gcp-iam.webp': 'IAM y administración › IAM',
    'gcp-logging.webp': 'Logging › Explorador de registros', 'gcp-trace.webp': 'Observabilidad › Trace › Explorador de seguimiento',
}
CAPTURAS_PENDIENTES = set()     # nombres que aún no se pudieron capturar: se pintan como recuadro «Captura pendiente»


def cap(nombre, extra=''):
    """Una captura (clic o lupa = ampliar, Esc cierra) o, si falta, el recuadro «Captura pendiente»."""
    alt = CAPTURAS[nombre]
    extra = extra + f'<br><span class="menu">Menú: {esc(RUTAS_MENU[nombre])}</span>' if nombre in RUTAS_MENU else extra
    if (AQUI / 'img' / nombre).is_file() and nombre not in CAPTURAS_PENDIENTES:
        return (f'<figure class="cap" data-img="{nombre}"><button class="zoom" data-src="img/{nombre}" data-alt="{esc(alt)}" title="Ampliar (Esc cierra)">'
                f'<img src="img/{nombre}" alt="{esc(alt)}"><span class="lupa">{LUPA} Ampliar</span></button>'
                f'<figcaption><span class="tag ok">Captura real</span> {esc(alt)}{extra}</figcaption></figure>')
    return (f'<figure class="cap" data-img="{nombre}"><div class="pend"><b>Captura pendiente</b><span class="mono">img/{nombre}</span>'
            f'<span>{esc(alt)}</span></div><figcaption><span class="tag warn">Pendiente</span> {esc(alt)}{extra}</figcaption></figure>')


# ----------------------------------------------------------------------------------------------------------------------
# Diapositivas
# ----------------------------------------------------------------------------------------------------------------------
SLIDES = []
_N = {}
GRANDES_NO = set()


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
# Utilidades de SVG: mismas formas en todos los diagramas
#   usuario = persona · modelo = rectángulo azul con doble borde · datos = cilindro · herramienta = hexágono ámbar
#   agente/aplicación = rectángulo redondeado · observabilidad = recuadro de trazo discontinuo
# ----------------------------------------------------------------------------------------------------------------------
LH = {'t0': 28, 't1': 22, 't2': 19, 't3': 17}


def svg(w, h, cuerpo, etiqueta, idp='a'):
    marcas = ''.join(f'<marker id="{idp}{s}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto">'
                     f'<path d="M0 0 L10 5 L0 10 z" fill="{c}"/></marker>' for s, c in (('', '#0b5cad'), ('g', '#7b8794'), ('r', '#b91c1c')))
    return f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{esc(etiqueta)}"><defs>{marcas}</defs>{cuerpo}</svg>'


def tx(x, y, s, cls='t2', lh=None):
    """Texto (varias líneas con \\n) con la primera línea en y."""
    lh = lh or LH.get(cls.split()[0], 19)
    partes = s.split('\n')
    if len(partes) == 1:
        return f'<text x="{x:g}" y="{y:g}" class="{cls}">{esc(s)}</text>'
    ts = ''.join(f'<tspan x="{x:g}" dy="{0 if i == 0 else lh}">{esc(p)}</tspan>' for i, p in enumerate(partes))
    return f'<text x="{x:g}" y="{y:g}" class="{cls}">{ts}</text>'


def centrado(x, y, w, h, lineas):
    """Líneas [(texto, clase)] centradas en un rectángulo."""
    n = sum(len(t.split('\n')) for t, _ in lineas)
    alto = sum(LH.get(c.split()[0], 19) * len(t.split('\n')) for t, c in lineas)
    yy = y + h / 2 - alto / 2 + 15
    out = []
    for t, c in lineas:
        out.append(tx(x + w / 2, yy, t, c))
        yy += LH.get(c.split()[0], 19) * len(t.split('\n'))
    return ''.join(out)


def nodo(x, y, w, h, t1, t2='', cls='nodo', t3='', c2='t2', c3='t2'):
    ls = [(t1, 't1')] + ([(t2, c2)] if t2 else []) + ([(t3, c3)] if t3 else [])
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" class="{cls}"/>' + centrado(x, y, w, h, ls)


def sh_modelo(x, y, w, h, t1, t2='', t3='', c2='t2', c3='t2'):
    ls = [(t1, 't1')] + ([(t2, c2)] if t2 else []) + ([(t3, c3)] if t3 else [])
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" class="modelo"/>'
            f'<rect x="{x + 5}" y="{y + 5}" width="{w - 10}" height="{h - 10}" rx="10" class="modelo2"/>' + centrado(x, y, w, h, ls))


def sh_datos(x, y, w, h, t1, t2='', t3='', c2='t2', c3='t2'):
    ry = 11
    ls = [(t1, 't1')] + ([(t2, c2)] if t2 else []) + ([(t3, c3)] if t3 else [])
    d = f'M{x} {y + ry} A{w / 2} {ry} 0 0 1 {x + w} {y + ry} V{y + h - ry} A{w / 2} {ry} 0 0 1 {x} {y + h - ry} Z'
    tapa = f'M{x} {y + ry} A{w / 2} {ry} 0 0 0 {x + w} {y + ry}'
    return f'<path d="{d}" class="datos"/><path d="{tapa}" class="datos2"/>' + centrado(x, y + ry, w, h - ry, ls)


def sh_herr(x, y, w, h, t1, t2='', t3='', c2='t2', c3='t2'):
    c = 18
    pts = f'{x + c},{y} {x + w - c},{y} {x + w},{y + h / 2} {x + w - c},{y + h} {x + c},{y + h} {x},{y + h / 2}'
    ls = [(t1, 't1')] + ([(t2, c2)] if t2 else []) + ([(t3, c3)] if t3 else [])
    return f'<polygon points="{pts}" class="herr"/>' + centrado(x, y, w, h, ls)


def sh_usuario(cx, cy, etiqueta='Usuario', s=1.0):
    r = 11 * s
    cuerpo = (f'<circle cx="{cx}" cy="{cy - 16 * s:g}" r="{r:g}" class="user"/>'
              f'<path d="M{cx - 21 * s:g} {cy + 22 * s:g} Q{cx - 21 * s:g} {cy + 1 * s:g} {cx} {cy + 1 * s:g} Q{cx + 21 * s:g} {cy + 1 * s:g} {cx + 21 * s:g} {cy + 22 * s:g} Z" class="user"/>')
    return cuerpo + tx(cx, cy + 22 * s + 20, etiqueta, 't1')


def sh_obs(x, y, w, h, t1, t2=''):
    ls = [(t1, 't1')] + ([(t2, 't2')] if t2 else [])
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" class="obs"/>' + centrado(x, y, w, h, ls)


def zona(x, y, w, h, titulo, cls='zona'):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" class="{cls}"/>' + tx(x + 16, y + 26, titulo, 't1 izq')


def flecha(idp, *pts, kind='', suf=''):
    d = 'M' + ' L'.join(f'{x:g} {y:g}' for x, y in pts)
    return f'<path d="{d}" class="fl {kind}" marker-end="url(#{idp}{suf})"/>'


def fl_g(idp, *pts):
    return flecha(idp, *pts, kind='g', suf='g')


def fl_r(idp, *pts):
    return flecha(idp, *pts, kind='r', suf='r')


def num(cx, cy, n, cls='num'):
    return f'<circle cx="{cx}" cy="{cy}" r="13" class="{cls}"/><text x="{cx}" y="{cy + 5.5}" class="numt">{n}</text>'


def dg(s, clase=''):
    return f'<div class="dg {clase}">{s}</div>'


def leyenda(x, y, idp):
    """Leyenda de formas (la misma en todos los diagramas)."""
    it = [('usuario', 'u'), ('modelo (LLM)', 'm'), ('datos', 'd'), ('herramienta', 'h'), ('agente / app', 'a')]
    out, cx = [], x
    for nombre, k in it:
        if k == 'u':
            out.append(f'<circle cx="{cx + 9}" cy="{y + 7}" r="6" class="user"/><path d="M{cx} {y + 22} Q{cx} {y + 12} {cx + 9} {y + 12} Q{cx + 18} {y + 12} {cx + 18} {y + 22} Z" class="user"/>')
        elif k == 'm':
            out.append(f'<rect x="{cx}" y="{y + 2}" width="22" height="18" rx="5" class="modelo"/><rect x="{cx + 3}" y="{y + 5}" width="16" height="12" rx="3" class="modelo2"/>')
        elif k == 'd':
            out.append(f'<path d="M{cx} {y + 6} A11 4 0 0 1 {cx + 22} {y + 6} V{y + 17} A11 4 0 0 1 {cx} {y + 17} Z" class="datos"/><path d="M{cx} {y + 6} A11 4 0 0 0 {cx + 22} {y + 6}" class="datos2"/>')
        elif k == 'h':
            out.append(f'<polygon points="{cx + 5},{y + 2} {cx + 17},{y + 2} {cx + 22},{y + 11} {cx + 17},{y + 20} {cx + 5},{y + 20} {cx},{y + 11}" class="herr"/>')
        else:
            out.append(f'<rect x="{cx}" y="{y + 2}" width="22" height="18" rx="5" class="nodo"/>')
        out.append(tx(cx + 30, y + 16, nombre, 't3 izq'))
        cx += 30 + len(nombre) * 8.6 + 30
    return ''.join(out)


LH.update({'tc': 17, 'tg': 17, 'tw': 22})


# ----------------------------------------------------------------------------------------------------------------------
# Cálculos de los ejemplos (se enseñan tal cual; las pruebas los recalculan por su cuenta)
# ----------------------------------------------------------------------------------------------------------------------
def es(x, d=3):
    return f'{x:.{d}f}'.replace('.', ',')


LOGITS = [('comprar', 3.0), ('visitar', 2.0), ('llamar', 1.2), ('reclamar', 0.4), ('cancelar', -0.4)]
TEMPS = [(0.5, 'baja'), (1.0, 'media'), (2.0, 'alta')]


def softmax(logits, t):
    e = [math.exp(v / t) for v in logits]
    s = sum(e)
    return [x / s for x in e]


def pct(t):
    return [round(p * 100) for p in softmax([v for _, v in LOGITS], t)]


VQ = (4, 3, 0)
DOCS = [('Retención a 90 días: qué es', (5, 2, 1)), ('Política de devoluciones', (1, 4, 2)), ('Receta de paella', (0, 1, 6))]


def punto(a, b):
    return sum(x * y for x, y in zip(a, b))


def norma(a):
    return math.sqrt(sum(x * x for x in a))


def coseno(a, b):
    return punto(a, b) / (norma(a) * norma(b))


# Datos reales del curso (se leen de los notebooks en las pruebas): extra-mcp-notebooks/02_mcp_modelo_prediccion.ipynb
CLIENTE = {'id': 12369, 'prob': '0.3035', 'tramo': 'baja', 'version': 6, 'valid_auc': '0.6982', 'test_auc': '0.7471',
           'recencia': 413, 'frecuencia': 3, 'monto': '1511.15', 'pais': 'Austria', 'facturas': 3}


# ----------------------------------------------------------------------------------------------------------------------
# 1 · El mapa
# ----------------------------------------------------------------------------------------------------------------------
def svg_munecas():
    rs = [255, 208, 161, 114, 67]
    cols = ['#f6f9fd', '#e6f0fb', '#cfe2f7', '#a9ccf0', '#6fa8e0']
    nombres = ['Inteligencia artificial', 'Aprendizaje automático', 'Aprendizaje profundo', 'IA generativa', 'LLM']
    cx, base = 290, 512
    c = [f'<circle cx="{cx}" cy="{base - r}" r="{r}" fill="{col}" stroke="#0b5cad" stroke-width="2"/>' for r, col in zip(rs, cols)]
    for i, (r, n) in enumerate(zip(rs, nombres)):
        c.append(tx(cx, base - 2 * r + (41 if i < 4 else 44), n, 't1'))
    return svg(580, 520, ''.join(c), 'Cinco círculos anidados: IA contiene aprendizaje automático, que contiene aprendizaje profundo, que contiene IA generativa, que contiene los LLM', 'm1')


MUNECAS_FILAS = [
    ('IA', 'Que una máquina haga tareas que exigen «inteligencia»', 'Un sistema de **reglas** que decide si un pedido se revisa (IA sin ML)'),
    ('Aprendizaje automático', 'Aprender patrones **de los datos**, sin escribir las reglas', 'Nuestro modelo: ¿volverá a comprar en 90 días?'),
    ('Aprendizaje profundo', 'Aprender con **redes de muchas capas** cuando los datos son complejos', 'Reconocer un producto en una foto'),
    ('IA generativa', '**Crear** contenido nuevo: texto, imagen, código', 'Redactar el borrador de un correo'),
    ('LLM', 'Generar y entender **lenguaje** a gran escala, token a token', 'Un asistente que explica la recomendación a un gestor'),
]


def html_munecas_filas():
    cols = ['#f6f9fd', '#e6f0fb', '#cfe2f7', '#a9ccf0', '#6fa8e0']
    filas = ''.join(f'<div class="mrow"><span class="dot" style="background:{c}"></span><div><b>{esc(n)}</b>'
                    f'<p><span class="lb">Resuelve</span> {md(r)}</p><p><span class="lb">Ejemplo</span> {md(e)}</p></div></div>'
                    for c, (n, r, e) in zip(cols, MUNECAS_FILAS))
    return f'<div class="mfilas">{filas}</div>'


HITOS = [
    ('1956', 'Dartmouth', 'Proyecto de verano: se propone que una máquina pueda simular el aprendizaje', 'dartmouth', 'el origen del campo'),
    ('2017', 'Transformer', '«Attention Is All You Need»: una arquitectura basada solo en atención', 'transformer', 'base de todo LLM actual'),
    ('2020', 'RAG', 'Modelo generador + índice de documentos: «Retrieval-Augmented Generation»', 'rag', 'hoy: bloque 6 de esta clase'),
    ('2021', 'LoRA', 'Ajustar un modelo entrenando solo unas pocas matrices pequeñas', 'lora', 'ajuste fino barato'),
    ('2022', 'Instrucciones', 'InstructGPT: ajustar con valoraciones humanas (RLHF) para que siga instrucciones', 'rlhf', 'por qué un LLM «sigue órdenes»'),
    ('2022', 'ReAct', 'Razonar y actuar: alternar pensamientos y acciones', 'react', 'el bucle del agente de S5'),
    ('2024', 'MCP', 'Anthropic presenta el Model Context Protocol (25 de noviembre)', 'mcp_anuncio', 'el extra de S5'),
]


def html_hitos():
    ev = ''.join(f'<div class="ev"><b class="yr">{y}</b><i class="pt"></i><h4>{esc(t)}</h4><p>{esc(d)}</p>'
                 f'<span class="cur">En el curso: {esc(c)}</span><small>{esc(FUENTES[k][1].replace("https://", ""))}</small></div>' for y, t, d, k, c in HITOS)
    return f'<div class="tl">{ev}</div>'

# ----------------------------------------------------------------------------------------------------------------------
# 2 · Datos y ML clásico
# ----------------------------------------------------------------------------------------------------------------------
def svg_flujo_ml():
    c = [sh_datos(10, 70, 210, 140, 'Datos', 'compras de clientes', '(Online Retail II)'),
         '<rect x="300" y="50" width="280" height="180" rx="12" class="nodo"/>',
         tx(440, 84, 'Variables (features)', 't1'),
         tx(440, 122, 'recencia_dias · frecuencia', 't2'), tx(440, 146, 'monto_total · ticket_medio', 't2'),
         tx(440, 170, 'frecuencia_180d · devoluciones', 't2'), tx(440, 200, '… 13 en total', 't2'),
         sh_modelo(660, 70, 230, 140, 'Modelo', 'regresión logística', 'retencion-90d @champion'),
         '<rect x="960" y="50" width="206" height="180" rx="12" class="nodo ok"/>',
         tx(1063, 90, 'Predicción', 't1'), tx(1063, 142, es(float(CLIENTE['prob']), 4), 't0'),
         tx(1063, 176, 'prob. de volver a comprar', 't2'), tx(1063, 200, f'tramo «{CLIENTE["tramo"]}»', 't2'),
         flecha('f1', (222, 140), (296, 140)), flecha('f1', (582, 140), (656, 140)), flecha('f1', (892, 140), (956, 140)),
         num(30, 40, 1), num(320, 40, 2), num(680, 40, 3), num(980, 30, 4)]
    return svg(1176, 250, ''.join(c), 'Cuatro pasos: datos de compras, variables, modelo de regresión logística y predicción de probabilidad', 'f1')


def svg_sup():
    A = [(250, 50), (285, 92), (305, 55), (240, 122), (312, 125), (272, 152)]
    B = [(60, 58), (92, 112), (38, 132), (112, 62), (80, 152), (128, 100)]
    c = ['<path d="M190 14 L152 178" class="fl g" stroke-dasharray="6 4"/>']
    c += [f'<circle cx="{x}" cy="{y}" r="9" fill="#0b5cad"/>' for x, y in A]
    c += [f'<circle cx="{x}" cy="{y}" r="8" fill="#fff" stroke="#6b7a8c" stroke-width="2.5"/>' for x, y in B]
    c += [tx(95, 196, '○ no vuelve', 't2'), tx(280, 196, '● vuelve', 't2')]
    return svg(360, 210, ''.join(c), 'Puntos de dos clases separados por una línea: aprendizaje supervisado', 's1')


def svg_nosup():
    import random
    rnd = random.Random(7)
    c = []
    for cx, cy in [(80, 62), (270, 52), (175, 128)]:
        c.append(f'<ellipse cx="{cx}" cy="{cy}" rx="58" ry="38" class="zona"/>')
        c += [f'<circle cx="{cx + rnd.randint(-38, 38)}" cy="{cy + rnd.randint(-22, 22)}" r="7.5" fill="#8a97a8"/>' for _ in range(6)]
    c.append(tx(180, 196, 'sin etiquetas: el algoritmo agrupa', 't2'))
    return svg(360, 210, ''.join(c), 'Puntos agrupados en tres grupos sin etiquetas: aprendizaje no supervisado', 's2')


def svg_refuerzo():
    c = [nodo(20, 60, 120, 70, 'Agente'), nodo(220, 60, 120, 70, 'Entorno'),
         flecha('s3', (140, 82), (216, 82)), flecha('s3', (216, 112), (144, 112)),
         tx(180, 72, 'acción', 't3'), tx(180, 134, 'recompensa', 't3'),
         tx(180, 188, 'prueba y error con premio', 't2')]
    return svg(360, 210, ''.join(c), 'Un agente actúa sobre un entorno y recibe una recompensa: aprendizaje por refuerzo', 's3')


def svg_sobreajuste():
    c = ['<path d="M60 30 L60 290 L540 290" class="eje"/>',
         '<path d="M60 70 C 180 175, 330 250, 530 270" class="curva g"/>',
         '<path d="M60 84 C 150 150, 220 188, 290 188 S 440 150, 530 100" class="curva"/>',
         '<line x1="290" y1="40" x2="290" y2="290" class="fl g" stroke-dasharray="5 4"/>',
         '<circle cx="290" cy="188" r="7" fill="#0b5cad"/>',
         tx(300, 62, 'punto dulce', 't1 izq'),
         tx(150, 322, 'modelo simple', 't2'), tx(440, 322, 'modelo muy complejo', 't2'),
         tx(300, 346, 'complejidad del modelo →', 't2'),
         '<text x="22" y="170" class="t2" transform="rotate(-90 22 170)">error</text>',
         '<path d="M70 372 L110 372" class="curva g"/>', tx(118, 378, 'entrenamiento: sigue bajando', 't2 izq'), '<path d="M340 372 L380 372" class="curva"/>', tx(388, 378, 'validación: vuelve a subir', 't2 izq'),
         tx(120, 52, 'infraajuste', 't2 mal'), tx(470, 52, 'sobreajuste', 't2 mal')]
    return svg(580, 392, ''.join(c), 'Gráfica ilustrativa: el error de entrenamiento baja siempre; el de validación baja y luego sube (sobreajuste)', 'o1')


def html_split():
    return ('<div class="split3"><div class="b1"><b>Entrenamiento</b><span>el modelo aprende aquí</span></div>'
            '<div class="b2"><b>Validación</b><span>elegir y ajustar</span></div>'
            '<div class="b3"><b>Test</b><span>la nota final, una vez</span></div></div>')


def svg_funcion():
    c = [sh_modelo(10, 160, 150, 90, 'LLM', 'pide, no ejecuta'),
         zona(200, 50, 700, 340, 'Servidor MCP «mcp-modelo-retencion»'),
         sh_herr(230, 150, 230, 110, 'predecir_cliente', '(cliente_id=12369)'),
         sh_datos(620, 70, 230, 120, 'fs_produccion', '13 variables', '(solo lectura)'),
         sh_modelo(620, 245, 230, 120, 'Modelo', 'retencion-90d', '@champion · v6'),
         nodo(930, 160, 236, 100, 'Respuesta JSON', f'probabilidad {es(float(CLIENTE["prob"]), 4)}', 'nodo ok', f'tramo «{CLIENTE["tramo"]}» · v{CLIENTE["version"]}'),
         flecha('g1', (162, 205), (226, 205)),
         flecha('g1', (462, 175), (616, 135)), flecha('g1', (462, 235), (616, 300)),
         flecha('g1', (850, 300), (900, 300), (900, 215), (926, 215)),
         flecha('g1', (1048, 262), (1048, 424), (85, 424), (85, 254)),
         num(540, 138, 1), num(540, 270, 2), tx(1060, 330, 'resultado al LLM', 't2 izq'),
         tx(470, 120, 'lee las variables', 't3 izq'), tx(470, 300, 'puntúa', 't3 izq')]
    return svg(1176, 450, ''.join(c), 'Un LLM llama a la herramienta predecir_cliente de un servidor MCP, que lee variables y usa el modelo champion y devuelve un JSON', 'g1')


# ----------------------------------------------------------------------------------------------------------------------
# 3 · Aprendizaje profundo y transformers
# ----------------------------------------------------------------------------------------------------------------------
def svg_neurona_red():
    c = [tx(280, 36, 'Una neurona', 't1')]
    ys = [120, 220, 320]
    for i, y in enumerate(ys):
        c.append(f'<circle cx="60" cy="{y}" r="26" class="nodo"/>' + tx(60, y + 6, f'x{i + 1}', 't1'))
        c.append(flecha('n1', (88, y), (282, 220 + (y - 220) * 0.2)))
        c.append(tx(165, y + (-8 if y < 220 else (14 if y > 220 else -10)) + (0 if y != 220 else -6), f'peso w{i + 1}', 't3'))
    c += ['<circle cx="330" cy="220" r="46" class="nodo"/>' + tx(330, 228, 'Σ + b', 't1'),
          flecha('n1', (378, 220), (418, 220)), nodo(420, 190, 70, 60, 'f'),
          flecha('n1', (492, 220), (532, 220)), f'<circle cx="556" cy="220" r="24" class="nodo ok"/>' + tx(556, 226, 'y', 't1'),
          tx(60, 372, 'variables', 't2'), tx(330, 290, 'suma ponderada', 't2'), tx(455, 272, 'activación', 't2'),
          tx(290, 420, 'y = f( w1·x1 + w2·x2 + w3·x3 + b )', 't1')]
    xs = [700, 830, 960, 1090]
    sizes = [3, 4, 4, 2]
    pos = [[235 + (j - (n - 1) / 2) * 66 for j in range(n)] for n in sizes]
    for a in range(3):
        for ya in pos[a]:
            for yb in pos[a + 1]:
                c.append(f'<line x1="{xs[a]}" y1="{ya:g}" x2="{xs[a + 1]}" y2="{yb:g}" class="red"/>')
    for k, (x, ps) in enumerate(zip(xs, pos)):
        for y in ps:
            c.append(f'<circle cx="{x}" cy="{y:g}" r="17" class="{"nodo ok" if k == 3 else "nodo"}"/>')
    c += [tx(895, 36, 'Una red: neuronas en capas', 't1'), tx(700, 372, 'entrada', 't2'), tx(895, 372, 'capas ocultas', 't2'),
          tx(1090, 372, 'salida', 't2'), tx(895, 420, 'profundo = muchas capas ocultas', 't1')]
    return svg(1176, 450, ''.join(c), 'Una neurona suma entradas por pesos y aplica una activación; una red une neuronas en capas', 'n1')


TOKS = ['La', 'clienta', 'devolvió', 'el', 'pedido', 'porque', 'estaba', 'roto', '.']


def svg_tokens():
    ws = [22 + len(t) * 12 for t in TOKS]
    gap = 10
    total = sum(ws) + gap * (len(ws) - 1)
    x0 = 232
    xs, x = [], x0
    for w in ws:
        xs.append(x)
        x += w + gap
    cx = [a + w / 2 for a, w in zip(xs, ws)]
    y0 = 330
    c = []
    # arcos de atención desde «estaba» (índice 6)
    pesos = {4: (7.5, 1.0), 7: (4.5, .85), 1: (2.6, .7), 2: (1.6, .45), 0: (1.1, .3), 3: (1.1, .3), 5: (1.1, .3)}
    for j, (g, op) in pesos.items():
        d = abs(cx[6] - cx[j])
        c.append(f'<path d="M{cx[6]:g} {y0} Q{(cx[6] + cx[j]) / 2:g} {y0 - 40 - d * 0.55:g} {cx[j]:g} {y0 - 2}" fill="none" stroke="#0b5cad" '
                 f'stroke-width="{g}" stroke-opacity="{op}" stroke-linecap="round"/>')
    for t, a, w in zip(TOKS, xs, ws):
        c.append(f'<rect x="{a:g}" y="{y0}" width="{w}" height="48" rx="10" class="{"nodo puerta" if t == "estaba" else "nodo"}"/>' + tx(a + w / 2, y0 + 31, t, 't1'))
        c.append(f'<rect x="{a:g}" y="{y0 + 86}" width="{w}" height="38" rx="8" class="datos"/>' + tx(a + w / 2, y0 + 111, 'nº', 't2'))
        c.append(flecha('t1', (a + w / 2, y0 + 52), (a + w / 2, y0 + 82), kind='g', suf='g'))
    c += [tx(20, y0 + 30, 'tokens', 't1 izq'), tx(20, y0 + 111, 'ids (números)', 't2 izq'),
          tx(588, 36, '«La clienta devolvió el pedido porque estaba roto.»', 't1'),
          tx(588, 62, 'Texto → tokens → números. Después, cada token pasa a ser un vector (embedding).', 't2'),
          tx(cx[4], 126, '¿qué estaba roto?', 't2 azul'), tx(cx[4], 148, '«estaba» mira sobre todo a «pedido»', 't2 azul'),
          tx(20, 100, 'Grosor del arco = atención', 't2 izq'), tx(20, 122, '(ilustración: pesos inventados)', 't3 izq')]
    return svg(1176, 470, ''.join(c), 'Oración dividida en tokens; la palabra estaba tiene un arco grueso hacia pedido, que indica atención', 't1')


def html_etapas():
    et = [('1 · Preentrenamiento', 'Leer una enorme cantidad de texto y predecir el **siguiente token**',
           'Lo hacen pocas organizaciones: es lo más caro', 'Sale un modelo base que «sabe lenguaje»'),
          ('2 · Ajuste fino (fine-tuning)', 'Seguir entrenando con **ejemplos de tu tarea**',
           '**LoRA**: entrena unas pocas matrices pequeñas y deja fijo el resto', 'Formato, tono o tarea concretos'),
          ('3 · Alineación', 'Ajustar con **preferencias humanas** (RLHF) para que siga instrucciones',
           'Personas ordenan respuestas; el modelo aprende cuál se prefiere', 'Sale un modelo «de chat» útil y más seguro')]
    cs = ''
    for i, (t, a, b, c) in enumerate(et):
        cs += f'<div class="etapa"><h3>{esc(t)}</h3><p>{md(a)}</p><p class="s">{md(b)}</p><p class="r">{md(c)}</p></div>'
        if i < 2:
            cs += '<div class="flechaH">➜</div>'
    return f'<div class="etapas">{cs}</div>'


# ----------------------------------------------------------------------------------------------------------------------
# 4 · LLM
# ----------------------------------------------------------------------------------------------------------------------
def svg_temperatura():
    c = [nodo(300, 8, 576, 54, 'Prompt: «El cliente volverá a ___»', '', 'nodo puerta')]
    nombres = {0.5: 'Temperatura baja (0,5)', 1.0: 'Temperatura media (1,0)', 2.0: 'Temperatura alta (2,0)'}
    notas_t = {0.5: 'casi siempre la misma palabra', 1.0: 'reparto equilibrado', 2.0: 'más variedad… y más disparates'}
    for k, (t, _) in enumerate(TEMPS):
        x0 = k * 396
        c.append(f'<rect x="{x0 + 4}" y="86" width="372" height="330" rx="14" class="zona"/>')
        c.append(tx(x0 + 190, 118, nombres[t], 't1'))
        for i, ((pal, _), p) in enumerate(zip(LOGITS, pct(t))):
            y = 150 + i * 46
            c.append(tx(x0 + 20, y + 22, pal, 't2 izq'))
            c.append(f'<rect x="{x0 + 110}" y="{y}" width="{max(p, 1) * 2.1:g}" height="30" rx="5" fill="{"#0b5cad" if i == 0 else "#a9c6e8"}"/>')
            c.append(tx(x0 + 116 + max(p, 1) * 2.1, y + 22, f'{p} %', 't2 izq'))
        c.append(tx(x0 + 190, 402, notas_t[t], 't2'))
    c.append(tx(588, 450, 'Ilustración: las puntuaciones de las cinco palabras son inventadas; el cálculo (softmax con T) es real.', 't3'))
    return svg(1176, 470, ''.join(c), 'Tres gráficas de barras con la probabilidad de cinco palabras siguientes según la temperatura', 'te')


def svg_sabe():
    p = es(float(CLIENTE['prob']), 4)
    c = [tx(10, 52, 'LLM solo', 't1 mal izq'), tx(10, 76, 'sin datos ni modelo', 't2 izq'),
         nodo(190, 22, 250, 80, '«¿Probabilidad del', 'cliente 12369?»'), sh_modelo(500, 22, 150, 80, 'LLM'),
         nodo(720, 12, 330, 100, 'Una cifra plausible… inventada', '(alucinación)', 'nodo mal'),
         flecha('sb', (442, 62), (496, 62)), flecha('sb', (652, 62), (716, 62)),
         tx(10, 192, 'LLM + herramienta', 't1 okk izq'), tx(10, 216, 'el sistema ejecuta', 't2 izq'),
         nodo(190, 162, 250, 80, '«¿Probabilidad del', 'cliente 12369?»'), sh_modelo(500, 162, 130, 80, 'LLM'),
         sh_herr(680, 152, 250, 100, 'predecir_cliente', '(12369)'), nodo(980, 152, 190, 100, p, f'tramo «{CLIENTE["tramo"]}»', 'nodo ok', f'versión {CLIENTE["version"]}'),
         flecha('sb', (442, 202), (496, 202)), flecha('sb', (632, 202), (676, 202)), flecha('sb', (932, 202), (976, 202))]
    return svg(1176, 262, ''.join(c), 'Comparación: un LLM solo inventa la probabilidad; con la herramienta predecir_cliente devuelve 0,3035', 'sb')


def svg_triangulo():
    c = ['<path d="M270 36 L480 380 L60 380 Z" fill="#eef5fc" stroke="#0b5cad" stroke-width="2.5"/>',
         tx(270, 24, 'Calidad', 't1'), tx(60, 410, 'Velocidad', 't1'), tx(480, 410, 'Coste', 't1'),
         tx(270, 230, 'Se negocian:', 't1'), tx(270, 256, 'rara vez se gana en los tres', 't2'),
         tx(270, 282, 'a la vez', 't2')]
    return svg(540, 430, ''.join(c), 'Triángulo de compromiso entre calidad, velocidad y coste', 'tr')


# ----------------------------------------------------------------------------------------------------------------------
# 5 · Embeddings
# ----------------------------------------------------------------------------------------------------------------------
def svg_texto_vector():
    tex = ['¿Volverá a comprar?', 'Retención a 90 días', 'Devolver un pedido']
    c = []
    for i, t in enumerate(tex):
        y = 80 + i * 100
        c.append(nodo(10, y, 230, 56, t, '', 'nodo'))
        c.append(flecha('v1', (242, y + 28), (300, 222)))
        for j in range(8):
            sombra = ['#dbeafe', '#a9cdf0', '#6fa8e0', '#3a7fc9', '#0b5cad'][(i * 3 + j * 2) % 5]
            c.append(f'<rect x="{560 + j * 26}" y="{y + 14}" width="22" height="28" rx="4" fill="{sombra}" stroke="#8fb2d6"/>')
        c.append(tx(780, y + 34, '…', 't1 izq'))
    c += [sh_modelo(300, 170, 200, 104, 'Modelo de', 'embeddings'), flecha('v1', (502, 222), (556, 130)), flecha('v1', (502, 222), (556, 222)), flecha('v1', (502, 222), (556, 322)),
          tx(10, 44, 'Texto', 't1 izq'), tx(560, 44, 'Vector (muchos números)', 't1 izq'),
          tx(10, 410, 'Cada texto pasa a ser una lista de números:', 't2 izq'), tx(10, 434, 'significados parecidos → vectores parecidos.', 't2 izq')]
    c.append('<rect x="830" y="20" width="340" height="430" rx="14" class="zona"/>')
    c.append(tx(1000, 50, 'Mapa 2D (ilustración)', 't1'))
    grupos = [((930, 130), 'recompra y retención', 'recompra y retención', '#0b5cad', [(0, 0), (22, -14), (-20, 12), (14, 24), (-14, -22), (30, 10)], 232),
              ((1080, 190), 'devoluciones', 'devoluciones', '#c58a12', [(0, 0), (20, 16), (-22, -8), (12, -24), (-14, 22)], 252),
              ((960, 318), 'envíos y logística', 'envíos y logística', '#0e7490', [(0, 0), (24, 10), (-18, 18), (10, -22), (-26, -6), (28, -14)], 374)]
    for (gx, gy), nom, _, col, pts, ly in grupos:
        for dx, dy in pts:
            c.append(f'<circle cx="{gx + dx}" cy="{gy + dy}" r="8" fill="{col}"/>')
        c.append(tx(gx, ly, nom, 't2'))
    c += ['<circle cx="936" cy="136" r="64" fill="none" stroke="#0b5cad" stroke-dasharray="5 4" stroke-width="2"/>',
          '<path d="M910 100 L915 114 L930 114 L918 123 L923 138 L910 129 L897 138 L902 123 L890 114 L905 114 Z" fill="#b91c1c" stroke="#fff" stroke-width="1.2"/>',
          tx(1000, 418, '★ pregunta: sus vecinos son los trozos relevantes', 't3'),
          tx(1000, 438, 'los ejes no significan nada por sí solos', 't3')]
    return svg(1176, 460, ''.join(c), 'Tres textos pasan por un modelo de embeddings y se convierten en vectores; un mapa 2D agrupa los significados parecidos', 'v1')


def svg_coseno():
    ox, oy = 190, 330
    def pt(ang, ln):
        a = math.radians(ang)
        return ox + ln * math.cos(a), oy - ln * math.sin(a)
    vec = [(38, 270, '#0b5cad', 'pregunta', 4), (24, 255, '#6b7a8c', 'A: retención', 2.5), (66, 235, '#6b7a8c', 'B: devoluciones', 2.5), (96, 225, '#6b7a8c', 'C: paella', 2.5)]
    c = []
    for ang, ln, col, nom, w in vec:
        x, y = pt(ang, ln)
        c.append(f'<line x1="{ox}" y1="{oy}" x2="{x:g}" y2="{y:g}" stroke="{col}" stroke-width="{w}" marker-end="url(#co{"" if col == "#0b5cad" else "g"})"/>')
        c.append(tx(x + (8 if ang < 80 else -6), y - 8, nom, 't2 izq' if ang < 80 else 't2 izq'))
    xa, ya = pt(38, 80)
    xb, yb = pt(24, 80)
    c.append(f'<path d="M{xb:g} {yb:g} A80 80 0 0 0 {xa:g} {ya:g}" fill="none" stroke="#b91c1c" stroke-width="2"/>')
    c += [tx(300, 296, 'θ pequeño', 't3 mal izq'), tx(ox, 372, 'origen', 't3'),
          tx(190, 410, 'cos θ = (a · b) / (|a| · |b|)', 't1'), tx(190, 436, 'mide el ÁNGULO, no la longitud', 't2')]
    return svg(560, 450, ''.join(c), 'Cuatro vectores desde un origen: la pregunta forma un ángulo pequeño con A y casi recto con C', 'co')


def html_coseno_tabla():
    q = VQ
    filas = []
    for nombre, d in DOCS:
        filas.append([nombre, f'{d}', str(punto(q, d)), es(norma(d)), f'<b>{es(coseno(q, d))}</b>'.join(['!', ''])])
    return filas


def svg_chunks_indice():
    c = [tx(290, 34, '1 · Trocear el documento (chunking)', 't1'),
         '<rect x="20" y="60" width="540" height="56" rx="8" class="datos"/>', tx(290, 94, 'documento largo', 't2'),
         '<rect x="20" y="150" width="220" height="62" rx="8" fill="#dbeafe" stroke="#0b5cad" stroke-width="2"/>', tx(130, 188, 'trozo 1', 't1'),
         '<rect x="190" y="230" width="220" height="62" rx="8" fill="#e8f3ff" stroke="#0b5cad" stroke-width="2"/>', tx(300, 268, 'trozo 2', 't1'),
         '<rect x="360" y="310" width="200" height="62" rx="8" fill="#dbeafe" stroke="#0b5cad" stroke-width="2"/>', tx(460, 348, 'trozo 3', 't1'),
         '<rect x="190" y="150" width="50" height="142" fill="#fde9c8" opacity=".75"/>', '<rect x="360" y="230" width="50" height="142" fill="#fde9c8" opacity=".75"/>',
         tx(215, 322, 'solapamiento', 't3 izq'), tx(20, 404, 'Pequeños: precisos, pero sin contexto.', 't2 izq'), tx(20, 430, 'Grandes: con contexto, pero con ruido.', 't2 izq'),
         tx(880, 34, '2 · Guardar y buscar vectores', 't1'),
         sh_datos(700, 70, 300, 150, 'Índice vectorial', 'un vector por trozo + el texto', ''),
         nodo(620, 290, 190, 70, '«¿Cuándo vuelve', 'a comprar?»'), flecha('ci', (760, 288), (760, 224)),
         nodo(930, 290, 220, 70, 'Top-k vecinos', 'los k trozos más parecidos', 'nodo ok'), flecha('ci', (960, 224), (960, 286)),
         tx(770, 262, 'buscar', 't3 izq'), tx(970, 262, 'k más cercanos', 't3 izq'),
         tx(880, 400, 'Búsqueda aproximada (ANN): más rápida', 't2'), tx(880, 424, 'que comparar con todos; puede perder algún vecino real', 't2')]
    return svg(1176, 450, ''.join(c), 'Un documento se trocea con solapamiento; los vectores de los trozos se guardan en un índice que devuelve los k más parecidos a la pregunta', 'ci')


# ----------------------------------------------------------------------------------------------------------------------
# 6 · RAG
# ----------------------------------------------------------------------------------------------------------------------
def svg_rag():
    w, g = 140, 30
    xs = [8 + i * (w + g) for i in range(7)]
    c = [zona(0, 4, 1176, 200, 'A · Ingesta (se hace antes, y al actualizar los documentos)'),
         sh_datos(xs[0], 56, w, 130, 'Documentos', 'guías del curso'),
         nodo(xs[1], 76, w, 90, 'Trocear', '(chunks)'), sh_modelo(xs[2], 66, w, 110, 'Embeber', 'cada trozo'),
         sh_datos(xs[3], 56, w, 130, 'Índice', 'vectorial'),
         flecha('r1', (xs[0] + w + 2, 121), (xs[1] - 2, 121)), flecha('r1', (xs[1] + w + 2, 121), (xs[2] - 2, 121)), flecha('r1', (xs[2] + w + 2, 121), (xs[3] - 2, 121)),
         zona(0, 236, 1176, 276, 'B · Consulta (en cada pregunta)'),
         sh_usuario(xs[0] + w / 2, 340, 'Pregunta'),
         sh_modelo(xs[1], 330, w, 96, 'Embeber', 'la pregunta'), nodo(xs[2], 330, w, 96, 'Recuperar', 'top-k trozos', 'nodo'),
         nodo(xs[3], 330, w, 96, 'Reordenar', '(opcional)', 'nodo puerta'), nodo(xs[4], 330, w, 96, 'Construir', 'el prompt'),
         sh_modelo(xs[5], 330, w, 96, 'LLM', 'genera'), nodo(xs[6], 330, w, 96, 'Respuesta', 'con citas', 'nodo ok'),
         flecha('r1', (xs[0] + w - 24, 340), (xs[1] - 2, 378)), flecha('r1', (xs[1] + w + 2, 378), (xs[2] - 2, 378)),
         flecha('r1', (xs[2] + w + 2, 378), (xs[3] - 2, 378)), flecha('r1', (xs[3] + w + 2, 378), (xs[4] - 2, 378)),
         flecha('r1', (xs[4] + w + 2, 378), (xs[5] - 2, 378)), flecha('r1', (xs[5] + w + 2, 378), (xs[6] - 2, 378)),
         flecha('r1', (xs[3] + w / 2, 188), (xs[3] + w / 2, 222), (xs[2] + w / 2, 222), (xs[2] + w / 2, 326), kind='g', suf='g'),
         tx(xs[3] + w / 2 + 10, 216, 'busca aquí', 't3 izq'),
         tx(588, 470, 'Ejemplo (ilustrativo, no construido en el curso): «¿Cómo hago el rollback del agente?» → cita laboratorio-agentes/guia.md', 't2'),
         tx(588, 494, 'El LLM responde con lo recuperado y dice de dónde sale.', 't2')]
    return svg(1176, 520, ''.join(c), 'Dos tuberías: ingesta de documentos (trocear, embeber, indexar) y consulta (embeber la pregunta, recuperar, reordenar, construir el prompt, generar y citar)', 'r1')


def html_rag_tabla():
    return tabla(['', 'RAG', 'Ajuste fino', 'Contexto largo'],
                 [['**Sirve para**', 'Conocimiento que **cambia** y que hay que **citar**', 'Estilo, formato o una tarea **fija**', 'Pocos documentos que **caben** enteros'],
                  ['**Actualizar**', 'Re-indexar el documento', 'Volver a entrenar', 'Cambiar el texto del prompt'],
                  ['**Citar la fuente**', 'Natural: sabes qué trozo usó', 'No: el saber queda en los pesos', 'Posible, a mano'],
                  ['**Coste de montaje**', 'Medio: trocear, indexar, evaluar', 'Alto: datos buenos y entrenamiento', 'Bajo'],
                  ['**Riesgo principal**', 'Recuperar mal', 'Memorizar datos obsoletos', 'Más caro y lento en cada llamada'],
                  ['**Cuándo NO**', 'Si el saber cabe en el prompt', 'Si los datos cambian a diario', 'Si hay muchos documentos']], 'comp')


def html_fallos():
    fs = [('1', 'Recuperación mala', 'Trae trozos que no responden la pregunta (embedding flojo, k mal puesto)'),
          ('2', 'Troceado malo', 'Corta una tabla o una idea por la mitad: el trozo pierde sentido'),
          ('3', 'Datos obsoletos', 'El índice no se actualizó: responde con la versión antigua'),
          ('4', 'Inyección de instrucciones', 'Un documento dice «ignora lo anterior…» y el modelo lo obedece')]
    return ''.join(f'<div class="falla"><b class="n">{n}</b><h3>{esc(t)}</h3><p>{esc(d)}</p></div>' for n, t, d in fs)


# ----------------------------------------------------------------------------------------------------------------------
# 7 · Dato y contexto
# ----------------------------------------------------------------------------------------------------------------------
def svg_ventana():
    bl = [('Instrucciones del sistema', 44), ('Historial de la conversación', 60), ('Memoria (corta y larga)', 48),
          ('Conocimiento recuperado (RAG)', 72), ('Resultados de herramientas', 60), ('Estado y plan', 40)]
    c = ['<rect x="350" y="20" width="440" height="470" rx="18" fill="#f8fbff" stroke="#0b5cad" stroke-width="3"/>',
         tx(570, 52, 'Ventana de contexto', 't1'), tx(570, 74, '(lo que el modelo ve en esta llamada)', 't3')]
    y = 92
    pos = {}
    for i, (n, h) in enumerate(bl):
        c.append(f'<rect x="372" y="{y}" width="396" height="{h}" rx="9" fill="{["#dbeafe", "#e8f3ff", "#e4f3ee", "#dbeafe", "#fff4dc", "#eef2f6"][i]}" stroke="#8fb2d6"/>')
        c.append(tx(570, y + h / 2 + 6, n, 't2'))
        pos[i] = y + h / 2
        y += h + 9
    c += [sh_usuario(70, 150, 'Tú y la app'), sh_datos(10, 232, 180, 80, 'Memoria', 'larga (externa)'), sh_datos(10, 330, 180, 80, 'Índice RAG', ''),
          sh_herr(10, 424, 180, 70, 'Herramientas', ''),
          flecha('w1', (130, 190), (346, 108)), flecha('w1', (192, 272), (346, 236)), flecha('w1', (192, 370), (346, 312)), flecha('w1', (192, 459), (346, 388)),
          tx(830, 120, 'Escasa', 't1 izq'), tx(830, 144, 'es finita: lo que no cabe, no existe', 't2 izq'),
          tx(830, 210, 'Cara', 't1 izq'), tx(830, 234, 'cada token cuesta tiempo y dinero', 't2 izq'),
          tx(830, 300, 'Se diseña', 't1 izq'), tx(830, 324, 'qué entra, en qué orden', 't2 izq'), tx(830, 346, 'y qué se resume o se recorta', 't2 izq')]
    return svg(1176, 510, ''.join(c), 'Una ventana de contexto con seis bloques (instrucciones, historial, memoria, conocimiento recuperado, resultados de herramientas y estado) alimentados desde fuera', 'w1')


def svg_gobierno():
    c = [f'<rect x="10" y="40" width="660" height="340" rx="18" class="zona" stroke="#0b5cad"/>', tx(30, 366, 'Perímetro del banco (o de tu portátil)', 't1 izq'),
         sh_usuario(80, 150, 'Usuario'), nodo(170, 120, 150, 80, 'Aplicación', '/ agente', 'nodo'),
         sh_datos(400, 90, 230, 110, 'Datos del banco', 'permisos por rol'), sh_modelo(400, 245, 230, 90, 'LLM local', 'el dato no sale'),
         flecha('gv', (112, 156), (166, 160)), flecha('gv', (322, 150), (396, 145)), flecha('gv', (260, 202), (260, 290), (396, 290)),
         sh_herr(700, 128, 160, 100, 'Puerta de salida', 'política'),
         sh_modelo(940, 130, 220, 100, 'LLM en la nube', '(API de un proveedor)'),
         flecha('gv', (245, 118), (245, 62), (690, 62), (690, 160), (696, 160), kind='r', suf='r'),
         flecha('gv', (862, 178), (936, 178)), tx(705, 112, '¿qué datos viajan?', 't2 mal izq')]
    return svg(1176, 396, ''.join(c), 'Un perímetro contiene usuario, aplicación, datos y un LLM local; una puerta de salida controla lo que viaja a un LLM en la nube', 'gv')


# ----------------------------------------------------------------------------------------------------------------------
# 8 · Herramientas y MCP
# ----------------------------------------------------------------------------------------------------------------------
def svg_secuencia():
    xs = [130, 430, 730, 1030]
    c = [sh_usuario(xs[0], 40, 'Usuario'), nodo(xs[1] - 80, 12, 160, 56, 'Aplicación', '(agente)'), sh_modelo(xs[2] - 70, 8, 140, 64, 'LLM'),
         sh_herr(xs[3] - 90, 8, 180, 64, 'Herramienta', '(servidor MCP)')]
    for x in xs:
        c.append(f'<line x1="{x}" y1="96" x2="{x}" y2="490" class="vida"/>')
    msgs = [(0, 1, 'Pregunta: «¿Probabilidad del cliente 12369?»', ''),
            (1, 2, 'Pregunta + catálogo de herramientas (nombre, descripción, argumentos)', ''),
            (2, 1, 'Pide: predecir_cliente(cliente_id=12369) · ¡no la ejecuta!', 'r'),
            (1, 3, 'La aplicación ejecuta la función', ''),
            (3, 1, f'Resultado: {{probabilidad: {es(float(CLIENTE["prob"]), 4)}, tramo: «{CLIENTE["tramo"]}»}}', ''),
            (1, 2, 'Le devuelve el resultado de la herramienta', ''),
            (2, 1, 'Redacta la respuesta final', ''),
            (1, 0, 'Respuesta al usuario', '')]
    for i, (a, b, t, k) in enumerate(msgs):
        y = 124 + i * 47
        xa, xb = xs[a], xs[b]
        d = 1 if xb > xa else -1
        izq = min(xa, xb)
        c.append(flecha('sq', (xa + 4 * d, y), (xb - 4 * d, y), kind='r' if k else '', suf='r' if k else ''))
        c.append(num(izq + 22, y - 16, i + 1, 'num'))
        c.append(tx(izq + 44, y - 10, t, 't2 izq lbl' + (' mal' if k else '')))
    return svg(1176, 505, ''.join(c), 'Diagrama de secuencia de una llamada a función: el LLM pide la herramienta, la aplicación la ejecuta y devuelve el resultado', 'sq')


def svg_mcp():
    c = [zona(10, 10, 380, 320, 'Host (IDE, agente, aplicación)'),
         nodo(40, 60, 320, 100, 'Cliente MCP 1', 'una conexión por servidor'), nodo(40, 200, 320, 100, 'Cliente MCP 2', 'una conexión por servidor'),
         zona(520, 10, 450, 150, 'Servidor «mcp-datos-master»'), zona(520, 180, 450, 150, 'Servidor «mcp-modelo-retencion»'),
         sh_herr(545, 50, 250, 100, 'consulta_sql', 'resumen_cliente', '(y 5 más)'), sh_herr(545, 220, 250, 100, 'predecir_cliente', 'por_que', '(y 2 más)'),
         sh_datos(820, 48, 130, 104, 'SQLite', 'o BigQuery'), sh_modelo(820, 218, 130, 104, 'Modelo', '@champion'),
         flecha('mc', (362, 110), (516, 100)), flecha('mc', (362, 250), (516, 250)),
         tx(440, 92, 'stdio', 't3'), tx(440, 242, 'stdio', 't3'),
         flecha('mc', (797, 100), (816, 100)), flecha('mc', (797, 270), (816, 270)),
         tx(1070, 130, 'Un estándar abierto:', 't1'), tx(1070, 156, '«como un USB-C', 't2'), tx(1070, 180, 'para aplicaciones de IA»', 't2')]
    return svg(1176, 340, ''.join(c), 'Un host con dos clientes MCP conectados a dos servidores, cada uno con herramientas y su origen de datos o modelo', 'mc')


def svg_capas_sql():
    caps = [('1 · Descripción clara', 'cuándo usar la herramienta y cuándo no'),
            ('2 · Validar los argumentos', 'tipos, nombres y rangos antes de ejecutar'),
            ('3 · Vigilar el SQL', 'solo SELECT; lo demás se rechaza (13 entradas rechazadas en las pruebas)'),
            ('4 · Conexión de solo lectura', 'aunque algo se cuele, no puede escribir ni borrar'),
            ('5 · Topes', 'filas devueltas y bytes facturados (maximum_bytes_billed en BigQuery)'),
            ('6 · Registro', 'cada llamada queda en una traza')]
    c = []
    for i, (t, d) in enumerate(caps):
        w = 820 - i * 44
        x = 20 + i * 22
        y = 14 + i * 64
        c.append(f'<rect x="{x}" y="{y}" width="{w}" height="54" rx="10" fill="{["#e8f3ff", "#e2eefb", "#dbeafe", "#d2e5f8", "#c9dff5", "#c0daf2"][i]}" stroke="#0b5cad"/>')
        c.append(tx(x + 14, y + 23, t, 't1 izq'))
        c.append(tx(x + 14, y + 44, d, 't3 izq'))
    c += [flecha('cs', (430, 400), (430, 436)), sh_datos(310, 440, 240, 60, 'Los datos', ''),
          tx(880, 60, 'Mínimo privilegio', 't1 izq'), tx(880, 84, 'solo lo imprescindible', 't2 izq'),
          tx(880, 140, 'Solo lectura', 't1 izq'), tx(880, 164, 'por defecto', 't2 izq'),
          tx(880, 220, 'Humano aprueba', 't1 izq'), tx(880, 244, 'lo que escribe o gasta', 't2 izq'),
          '<rect x="870" y="290" width="296" height="130" rx="10" fill="#fdf6e9" stroke="#c9a65e"/>',
          tx(884, 318, 'Una expresión regular no es', 't2 izq mal'), tx(884, 340, 'un analizador de SQL: por eso', 't2 izq mal'), tx(884, 362, 'hay varias capas, no una', 't2 izq mal'),
          tx(884, 392, 'sin garantía (README del extra)', 't3 izq')]
    return svg(1176, 510, ''.join(c), 'Seis capas de defensa entre una petición de SQL del LLM y los datos', 'cs')


# ----------------------------------------------------------------------------------------------------------------------
# 9 · Agentes
# ----------------------------------------------------------------------------------------------------------------------
def html_espectro():
    pasos = [('LLM suelto', 'Responde con lo que sabe', 'Explica qué es el AUC', 'lleva poca autonomía'),
             ('RAG', 'Busca antes de responder', '«¿Cómo hago el rollback?» y cita la guía', ''),
             ('Workflow con LLM', 'Pasos fijos escritos en código', 'Cada lunes: lista del día → redactar mensajes', ''),
             ('Agente', 'El LLM **decide** los pasos y las herramientas', '«¿A quién llamo hoy y qué le digo?» (laboratorio de S5)', ''),
             ('Multiagente', 'Varios agentes con roles', 'Solo **planteado** en el curso: no está implementado', '')]
    cs = ''
    for i, (t, a, e, _) in enumerate(pasos):
        cs += (f'<div class="paso"><span class="nv">{i + 1}</span><h3>{esc(t)}</h3>'
               f'<p>{md(a)}</p><p class="eg"><span class="lb">Caso</span> {md(e)}</p></div>')
    return f'<div class="espectro">{cs}</div>'


def svg_react():
    c = [nodo(140, 20, 190, 76, 'Pensar', '¿qué me falta?', 'nodo'), nodo(262, 190, 200, 76, 'Actuar', 'llamar a la herramienta', 'nodo puerta'),
         nodo(8, 190, 200, 76, 'Observar', 'leer el resultado', 'nodo ok'),
         flecha('re', (300, 98), (362, 186)), flecha('re', (260, 228), (212, 228)), flecha('re', (100, 186), (172, 100)),
         nodo(140, 316, 190, 58, 'Responder', '', 'nodo ok'), flecha('re', (108, 268), (170, 312), kind='g', suf='g'),
         tx(235, 394, 'se repite hasta tener lo necesario', 't2')]
    return svg(470, 404, ''.join(c), 'Bucle de tres pasos: pensar, actuar, observar; cuando basta, responder', 're')


def html_traza_react():
    f = CLIENTE
    filas = [('Pregunta', 'p', '«¿Qué probabilidad tiene el cliente 12369 de volver a comprar y cuánto ha comprado?»'),
             ('1 Pensar', 'pn', 'Necesito los datos del cliente y su probabilidad. Primero, los datos.'),
             ('1 Actuar', 'ac', 'mcp-datos-master → resumen_cliente(cliente_id=12369)'),
             ('1 Observar', 'ob', f'{f["pais"]}, {f["facturas"]} facturas, monto_ventas {es(float(f["monto"]), 2)}'),
             ('2 Pensar', 'pn', 'Ahora la probabilidad: eso lo da el modelo, no yo.'),
             ('2 Actuar', 'ac', 'mcp-modelo-retencion → predecir_cliente(cliente_id=12369)'),
             ('2 Observar', 'ob', f'probabilidad {es(float(f["prob"]), 4)} · tramo «{f["tramo"]}» · versión {f["version"]}'),
             ('3 Responder', 'rs', f'«Es poco probable que vuelva a comprar en 90 días ({es(float(f["prob"]), 4)}, tramo baja). Ha comprado {es(float(f["monto"]), 2)} en {f["facturas"]} facturas.»')]
    return '<div class="traza">' + ''.join(f'<div class="tr {k}"><span class="tg">{esc(a)}</span><span class="tc">{esc(b)}</span></div>' for a, k, b in filas) + '</div>'


def svg_guardrails():
    c = [sh_usuario(60, 90, 'Usuario'),
         nodo(150, 40, 160, 100, 'Entrada', 'filtrar y validar', 'nodo puerta'),
         nodo(350, 40, 140, 100, 'Agente', '', 'nodo'),
         nodo(530, 40, 190, 100, 'Acciones', 'permisos + OK humano', 'nodo puerta'),
         sh_herr(760, 36, 190, 108, 'Herramientas', 'solo lectura'),
         nodo(990, 40, 180, 100, 'Salida', 'revisar antes de mostrar', 'nodo puerta'),
         flecha('gr', (100, 92), (146, 92)), flecha('gr', (312, 90), (346, 90)), flecha('gr', (492, 90), (526, 90)),
         flecha('gr', (722, 90), (756, 90)), flecha('gr', (952, 90), (986, 90)),
         tx(588, 188, 'Guardrails (barreras): reglas fuera del modelo que limitan lo que puede entrar, hacer y salir', 't2')]
    return svg(1176, 210, ''.join(c), 'Cadena usuario, filtro de entrada, agente, control de acciones con aprobación humana, herramientas de solo lectura y revisión de salida', 'gr')


def html_riesgos():
    rs = [('Inyección de prompt', 'Un texto (o un documento) intenta dar órdenes al agente', 'Separar datos de instrucciones; no fiarse del contenido recuperado'),
          ('Permisos excesivos', 'El agente puede más de lo que necesita', 'Mínimo privilegio y solo lectura'),
          ('Bucles', 'Repite la misma herramienta sin fin', 'Tope de pasos y de tiempo'),
          ('Coste', 'Más pasos y más contexto = más tokens', 'Presupuesto por conversación y alertas')]
    return ''.join(f'<div class="riesgo"><h3>{esc(t)}</h3><p>{esc(a)}</p><p class="ctl"><span class="lb">Control</span> {esc(b)}</p></div>' for t, a, b in rs)


def svg_traza_eval():
    spans = [('agente (conversación completa)', 0, 100, '#0b5cad'), ('LLM: decide la herramienta', 2, 18, '#6fa8e0'), ('herramienta: resumen_cliente', 20, 12, '#c58a12'),
             ('LLM: decide otra', 33, 14, '#6fa8e0'), ('herramienta: predecir_cliente', 49, 14, '#c58a12'), ('LLM: redacta', 65, 33, '#6fa8e0')]
    c = [tx(280, 26, 'Una traza = una conversación paso a paso', 't1')]
    for i, (n, a, d, col) in enumerate(spans):
        y = 50 + i * 40
        c.append(tx(10, y + 20, n, 't2 izq'))
        c.append(f'<rect x="{290 + a * 2.5:g}" y="{y + 4}" width="{d * 2.5:g}" height="22" rx="4" fill="{col}"/>')
    c.append(tx(420, 306, 'tiempo →   (ilustración: duraciones inventadas)', 't3'))
    return svg(580, 320, ''.join(c), 'Cronograma de una traza: el agente llama al LLM, a una herramienta, otra vez al LLM, a otra herramienta y redacta', 'tz')


# ----------------------------------------------------------------------------------------------------------------------
# 10 · En producción y en Google Cloud
# ----------------------------------------------------------------------------------------------------------------------
def svg_arq():
    c = [sh_usuario(60, 150, 'Usuario'),
         nodo(130, 80, 200, 130, 'Aplicación', 'Curso: interfaz del agente', 'nodo', 'GCP: Cloud Run', c2='tc', c3='tg'),
         zona(360, 14, 804, 346, 'Sistema agéntico'),
         nodo(380, 56, 220, 126, 'Agente', 'Curso: bucle en Python (L3)', 'nodo', 'GCP: ADK en Agent Runtime', c2='tc', c3='tg'),
         sh_modelo(620, 50, 255, 132, 'Modelo (LLM)', 'Curso: Ollama (Qwen2.5)', 'GCP: Model Garden · Gemini', c2='tc', c3='tg'),
         sh_herr(895, 48, 255, 136, 'Herramientas (MCP)', 'Curso: notebooks y laboratorio', 'GCP: MCP en Cloud Run', c2='tc', c3='tg'),
         sh_datos(620, 206, 255, 140, 'Conocimiento (RAG)', 'Curso: sin construir', 'GCP: RAG Engine · Vector Search', c2='tc', c3='tg'),
         sh_datos(895, 206, 255, 140, 'Datos y modelo de ML', 'Curso: SQLite + MLflow', 'GCP: BigQuery', c2='tc', c3='tg'),
         flecha('aq', (100, 150), (126, 150)), flecha('aq', (332, 145), (376, 120)), flecha('aq', (602, 110), (616, 110)), flecha('aq', (877, 110), (891, 110)),
         flecha('aq', (500, 184), (500, 276), (616, 276)), flecha('aq', (1020, 186), (1020, 202)),
         sh_obs(30, 372, 1130, 56, '', ''), sh_obs(30, 440, 1130, 60, '', ''),
         tx(50, 407, 'Secretos e identidad', 't1 izq'), tx(300, 407, 'Curso: GitHub Actions + WIF, sin claves', 'tc izq'), tx(700, 407, 'GCP: Secret Manager · IAM · Workload Identity Federation', 'tg izq'),
         tx(50, 476, 'Observabilidad', 't1 izq'), tx(300, 476, 'Curso: trazas en MLflow', 'tc izq'), tx(700, 476, 'GCP: Cloud Logging · Trace · Monitoring', 'tg izq')]
    return svg(1176, 516, ''.join(c), 'Arquitectura de referencia de un sistema agéntico con el equivalente en el curso y en Google Cloud para cada pieza', 'aq')


def svg_llmops():
    nodos = [('Versionar', 'prompts, skills y agente', 'git + prompts en MLflow'), ('Evaluar', 'antes de desplegar', '25 preguntas de oro'),
             ('Aprobar', 'una persona decide', 'environment con aprobación'), ('Desplegar', 'la nueva versión', 'workflow agente-nueva-version'),
             ('Observar', 'trazas, coste, calidad', 'trazas en MLflow'), ('Revertir', 'volver a la anterior', 'workflow agente-rollback')]
    pos = [(30, 30), (420, 30), (810, 30), (810, 250), (420, 250), (30, 250)]
    w, h = 336, 120
    c = []
    for k in range(6):
        x, y = pos[k]
        c.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" class="nodo"/>')
        t, d, cu = nodos[k]
        c.append(tx(x + w / 2, y + 36, f'{k + 1} · {t}', 't1'))
        c.append(tx(x + w / 2, y + 66, d, 't2'))
        c.append(tx(x + w / 2, y + 96, 'Curso: ' + cu, 'tc'))
    c += [flecha('lm', (368, 90), (416, 90)), flecha('lm', (758, 90), (806, 90)), flecha('lm', (978, 152), (978, 246)),
          flecha('lm', (806, 310), (758, 310)), flecha('lm', (416, 310), (368, 310)), flecha('lm', (198, 246), (198, 152)),
          tx(588, 196, 'LLMOps / AgentOps', 't1'), tx(588, 220, 'el mismo ciclo que el modelo de S4', 't2')]
    return svg(1176, 396, ''.join(c), 'Ciclo de seis pasos: versionar, evaluar, aprobar, desplegar, observar y revertir', 'lm')


# ----------------------------------------------------------------------------------------------------------------------
# 11 · Cierre
# ----------------------------------------------------------------------------------------------------------------------
def svg_mapa_mental():
    ramas = [('Datos y ML', 'variables · modelo · AUC · sobreajuste'), ('Redes', 'neurona · transformer · atención · token'),
             ('LLM', 'prompt · temperatura · alucinación · coste'), ('Conocimiento', 'embedding · coseno · RAG · chunk'),
             ('Contexto y herramientas', 'ventana · function calling · MCP · skill'), ('Agentes', 'ReAct · planificar · multiagente · guardrails'),
             ('Operación', 'evaluación · trazas · LLMOps · GCP')]
    cx, cy = 588, 264
    c = []
    pts = []
    for k in range(7):
        a = math.radians(-90 + k * 360 / 7)
        pts.append((cx + 440 * math.cos(a), cy + 200 * math.sin(a)))
    for p in pts:
        c.append(f'<line x1="{cx}" y1="{cy}" x2="{p[0]:g}" y2="{p[1]:g}" stroke="#9fb7d4" stroke-width="2.5"/>')
    c.append(f'<circle cx="{cx}" cy="{cy}" r="74" class="modelo"/><circle cx="{cx}" cy="{cy}" r="66" class="modelo2"/>' + tx(cx, cy - 4, 'Sistema', 't1') + tx(cx, cy + 20, 'agéntico', 't1'))
    for (x, y), (t, h) in zip(pts, ramas):
        partes = h.split(' · ')
        c.append(f'<rect x="{x - 125:g}" y="{y - 48:g}" width="250" height="96" rx="12" class="nodo"/>')
        c.append(tx(x, y - 20, t, 't1'))
        c.append(tx(x, y + 4, ' · '.join(partes[:2]), 't2'))
        c.append(tx(x, y + 26, ' · '.join(partes[2:]), 't2'))
    return svg(1176, 530, ''.join(c), 'Mapa mental: un sistema agéntico en el centro con siete ramas de conceptos', 'mm')


# ======================================================================================================================
# Las diapositivas
# ======================================================================================================================
def construir_1():
    KPI_AUC = grid(2, kpi('0,6982', 'AUC en **validación** (versión 6)'), kpi('0,7471', 'AUC en **test** (versión 6)'))
    # ---- 1 · El mapa (la portada se añade al final, con su agenda calculada) ----
    slide('1', 2, 'Las muñecas rusas de la IA', 'Qué es qué', 'La IA es una muñeca rusa: cada capa vive dentro de la anterior',
          f'<div class="muneca"><div class="dg">{svg_munecas()}</div>{html_munecas_filas()}</div>',
          nota('Empieza por el vocabulario: IA, aprendizaje automático, aprendizaje profundo, IA generativa y LLM no son sinónimos, son círculos anidados. Cada capa resuelve un problema distinto: la IA automatiza decisiones, el ML aprende de los datos, el profundo maneja datos complejos (imagen, texto), la generativa crea contenido y el LLM lo hace con lenguaje. Insiste en que hay IA sin ML (un sistema de reglas).',
               'Nuestro modelo de retención a 90 días está en el círculo del aprendizaje automático, pero NO es un LLM. El LLM del laboratorio de agentes (Qwen2.5 en Ollama) sí lo es.',
               '¿En qué círculo está la recomendación «llamar a este cliente»: en el modelo que calcula la probabilidad o en el LLM que la redacta?',
               urls('dartmouth')))
    slide('1', 1, 'Siete hitos con fuente', 'Línea de tiempo', 'Siete hitos, cada uno con su fuente',
          html_hitos() + callout('Hay muchos más hitos. Aquí están **solo los que hemos comprobado** en la fuente original (en las notas, con su dirección).'),
          nota('No es historia por la historia: cada hito explica una pieza de lo que veremos. Dartmouth 1956 es el origen del campo; el Transformer (2017) hace posibles los LLM; RAG (2020) los conecta a documentos; LoRA (2021) abarata el ajuste; InstructGPT (2022) populariza alinear con valoraciones humanas; ReAct (2022) es el bucle de los agentes; MCP (2024) estandariza las herramientas.',
               'Los dos hitos de 2022 son de los que más se citan: sin InstructGPT no hay chat útil, y sin ReAct no hay agentes que usen herramientas.',
               'Si tuvieras que borrar un hito de la línea, ¿cuál echaría más en falta un agente de producción?',
               urls('dartmouth', 'transformer', 'rag', 'lora', 'rlhf', 'react', 'mcp_anuncio') + '. Fechas: v1 de cada artículo en arXiv; MCP, 25/11/2024. Dartmouth: la página confirma 1956 y la propuesta de simular «cada aspecto del aprendizaje».'))

    # ---- 2 · Datos y ML clásico ----
    slide('2', 2, 'De los datos a la predicción', 'Nuestro caso', 'Datos → variables → modelo → predicción',
          dg(svg_flujo_ml()) + grid(3,
              card('La pregunta', ['«¿Volverá a comprar en los próximos **90 días**?»', 'Alta = **buena noticia**: no es un riesgo de abandono']),
              card('Un cliente: el 12369', [f'**{CLIENTE["recencia"]}** días desde su última compra', f'**{CLIENTE["frecuencia"]}** compras en total y 0 en los últimos 180 días']),
              kpi('AUC 0,70 · 0,75', 'validación · test (0,5 = azar, 1 = perfecto). Fuente: S1/S2 del curso, 04-Proyecto-Base (notebook 02, versión 6: 0,6982 · 0,7471)')),
          nota('Este es nuestro caso, que acompañará toda la clase: a partir de las compras de cada cliente se construyen 13 variables (recencia, frecuencia, importe…), un modelo de regresión logística las convierte en una probabilidad, y una regla de negocio la traduce en tramo (alta, media, baja). El AUC resume qué tan bien ordena el modelo a quien vuelve frente a quien no.',
               f'Cliente {CLIENTE["id"]}: 413 días sin comprar, 3 compras, ninguna en 180 días. El modelo da {es(float(CLIENTE["prob"]), 4)}: tramo «baja». Ojo con la lectura: es probabilidad de VOLVER a comprar.',
               '¿Qué decisión de negocio cambia si leemos esa probabilidad al revés, como riesgo de abandono?',
               'Cifras: notebook 02 del extra de S5 (extra-mcp-notebooks/02_mcp_modelo_prediccion.ipynb), salida guardada «v6 · valid_auc 0.6982 · test_auc 0.7471» y cliente 12369 con probabilidad 0.3035, tramo baja. Origen: S1/S2 del curso, 04-Proyecto-Base.'))
    slide('2', 1, 'Tres formas de aprender', 'Tipos de aprendizaje', 'Tres formas de aprender: con respuesta, sin respuesta y por premio',
          grid(3,
               card('Supervisado', cuerpo=dg(svg_sup()) + '<p class="small"><span class="lb">Nuestro caso</span> aprende de clientes que **sí** y **no** volvieron</p>'),
               card('No supervisado', cuerpo=dg(svg_nosup()) + '<p class="small"><span class="lb">Ejemplo posible</span> segmentar clientes por parecido</p>'),
               card('Por refuerzo', cuerpo=dg(svg_refuerzo()) + '<p class="small"><span class="lb">Dónde aparece</span> en el ajuste de los LLM con preferencias</p>')) +
          callout('En el curso solo **entrenamos** modelos supervisados (retención). El LLM del laboratorio llega ya preentrenado y alineado.'),
          nota('Tres formas de aprender. Supervisado: cada ejemplo trae su respuesta correcta (volvió o no volvió); es el nuestro. No supervisado: no hay respuesta, el algoritmo agrupa por parecido (segmentación). Por refuerzo: un agente prueba acciones y recibe un premio; es la idea detrás de alinear modelos con preferencias.',
               'Retención a 90 días: la etiqueta «volvió a comprar» existe porque esperamos 90 días y miramos. Eso es supervisado.',
               '¿Por qué un modelo supervisado necesita que pase el tiempo antes de poder entrenarse con la etiqueta?'))
    slide('2', 2, 'Entrenar, validar y probar', 'Sobreajuste', 'Un modelo debe funcionar con datos que no ha visto',
          f'<div class="split2"><div class="col">{html_split()}{lista(["El modelo **aprende** con el entrenamiento", "La validación sirve para **elegir y ajustar**", "El test es la **nota final**: se mira una vez", "Sobreajuste = memorizar en vez de aprender"])}{KPI_AUC}<p class="fte">Fuente: S1/S2 del curso, notebook 02 del extra de S5.</p></div>'
          f'<div class="card">{dg(svg_sobreajuste())}<p class="small centro">Ilustración conceptual: no son datos reales</p></div></div>',
          nota('El modelo no se evalúa con los datos con que aprendió. Se separan tres bloques: entrenamiento (aprende), validación (comparar y ajustar) y test (la nota final, una vez). Si el modelo es demasiado complejo, el error de entrenamiento sigue bajando pero el de validación vuelve a subir: eso es sobreajuste, memorizar.',
               f'En nuestro modelo, la validación dio 0,6982 y el test 0,7471; no se alejan mucho, pero con pocos datos esa diferencia puede ser ruido (no está comprobado). Fuente: notebook 02, versión 6.',
               '¿Qué pasaría si usáramos el test para elegir entre modelos y luego presumiéramos de su AUC?',
               'Cifras del notebook 02 (extra-mcp-notebooks/02_mcp_modelo_prediccion.ipynb). El gráfico es una ilustración sin datos.'))
    slide('2', 1, 'El modelo es una función', 'Del modelo a la herramienta', 'En ML clásico, el modelo es una función',
          dg(svg_funcion()) + msg('variables del cliente → **función** → probabilidad. Un servidor MCP la publica como **herramienta**.'),
          nota('Un modelo clásico entrenado es, para quien lo usa, una función: entra una lista de variables, sale un número. Eso es exactamente lo que necesita un LLM para usarlo: una herramienta con contrato. En el extra de S5, el servidor MCP carga models:/retencion-90d@champion, lee las 13 variables del cliente en solo lectura y devuelve JSON. El LLM no ve ni el modelo ni la base de datos.',
               f'predecir_cliente(cliente_id={CLIENTE["id"]}) devuelve probabilidad {CLIENTE["prob"]}, tramo «{CLIENTE["tramo"]}», versión {CLIENTE["version"]}. Y como carga el alias, un rollback cambia lo que responde sin reiniciar nada.',
               '¿Qué ventaja tiene que el MCP cargue el alias @champion en vez de un archivo fijo?',
               'Notebook 02 del extra de S5 (extra-mcp-notebooks/02_mcp_modelo_prediccion.ipynb) y README del extra.'))


def construir_2():
    # ---- 3 · Aprendizaje profundo y transformers ----
    slide('3', 1, 'Neurona y red', 'Aprendizaje profundo', 'Una red neuronal son muchas neuronas simples en capas',
          dg(svg_neurona_red()) + callout('Nuestra regresión logística es, en el fondo, **una sola neurona** con función sigmoide. «Profundo» = muchas capas.'),
          nota('Una neurona artificial suma sus entradas multiplicadas por pesos, añade un sesgo y aplica una función de activación. Una red une muchas en capas: la salida de una capa es la entrada de la siguiente. «Profundo» significa que hay varias capas ocultas. Entrenar es ajustar los pesos para reducir el error.',
               'Con una sola neurona y activación sigmoide, tenemos una regresión logística: justo el modelo de retención. Un LLM es lo mismo llevado a una escala enorme y con una arquitectura distinta.',
               '¿Qué le falta a una sola neurona para entender una frase completa?'))
    slide('3', 2, 'Tokens y atención', 'Transformers', 'Un transformer lee tokens y decide a cuáles mirar',
          dg(svg_tokens()) + '<div class="chips"><span class="chip">Token ≈ trozo de palabra o de signo</span><span class="chip">Atención: cada token elige a cuáles mirar</span><span class="chip">El troceado real depende de cada modelo</span></div>',
          nota('Un LLM no lee letras ni palabras: lee tokens, trozos de texto que se convierten en números y luego en vectores. La arquitectura Transformer añade la atención: cada token calcula cuánto debe fijarse en los demás para entender su significado en este contexto. Así resuelve referencias: en esa frase, «estaba» se refiere al pedido.',
               'Ilustración: pesos de atención inventados para explicar la idea; los reales son matrices con muchas cabezas y capas. Y el troceado real de tokens varía por modelo.',
               '¿Qué pasaría con la frase «la clienta devolvió el pedido porque estaba cansada»? ¿A quién mira ahora «estaba»?',
               urls('transformer')))
    slide('3', 2, 'Preentrenar, ajustar, alinear', 'Cómo se forma un LLM', 'Tres etapas: preentrenar, ajustar y alinear',
          html_etapas() + grid(2,
              card('Parámetros', ['Los números que el modelo aprendió: su «saber» estable', 'No cambian mientras lo usas']),
              card('Ventana de contexto', ['Lo que puede leer **a la vez**: su «mesa de trabajo»', 'Lo que no cabe, no existe para él'])) +
          '<p class="fte">Cifras con fuente: LoRA reduce unas 10 000 veces los parámetros entrenables y unas 3 veces la memoria de GPU frente al ajuste completo de GPT-3 175B (arXiv 2106.09685). En InstructGPT, evaluadores prefirieron un modelo de 1,3B ajustado con valoraciones humanas a GPT-3 de 175B (arXiv 2203.02155).</p>',
          nota('Un LLM se forma en tres pasos. 1) Preentrenamiento: leer muchísimo texto prediciendo el siguiente token; es carísimo y lo hacen pocas organizaciones. 2) Ajuste fino: seguir entrenando con ejemplos de tu tarea; LoRA lo abarata entrenando solo matrices pequeñas. 3) Alineación: valoraciones humanas (RLHF) para que siga instrucciones. Parámetros y ventana de contexto: lo aprendido frente a lo que cabe en la llamada, sin cifras sueltas porque cambian cada trimestre.',
               'El LLM de nuestro laboratorio (Qwen2.5 3B Instruct) ya viene preentrenado y alineado para chat: nosotros no lo entrenamos, solo lo usamos y le damos herramientas.',
               '¿Para qué tarea de nuestro caso consideraríais un ajuste fino y para cuál bastaría con un buen prompt?',
               urls('lora', 'rlhf')))

    # ---- 4 · LLM ----
    slide('4', 2, 'Genera token a token', 'Cómo genera', 'Un LLM predice el siguiente token y lo repite',
          dg(svg_temperatura()) + '<div class="ruta"><span class="st">elige un token</span><span class="fl2">➜</span><span class="st">lo añade al texto</span><span class="fl2">➜</span><span class="st">vuelve a empezar</span><span class="fl2">➜</span><span class="st">hasta el final</span></div>',
          nota('Un LLM no «piensa la respuesta entera»: calcula una distribución de probabilidad sobre el siguiente token, elige uno, lo añade y repite. La temperatura controla cuánto se arriesga: baja, casi siempre el más probable; alta, más variedad y más disparates. Por eso la misma pregunta puede dar respuestas distintas.',
               'Con «El cliente volverá a ___», T baja casi siempre elige «comprar»; T alta reparte más. Las puntuaciones son inventadas; el cálculo softmax con temperatura es real y está en generar.py.',
               'Para extraer datos de un formulario, ¿temperatura alta o baja? ¿Y para proponer nombres de campañas?'))
    slide('4', 2, 'Qué sabe y qué no', 'Límites', 'Sabe lenguaje; no sabe lo tuyo ni lo posterior',
          grid(3, card('Sabe', ['Lenguaje y patrones', 'Conocimiento general hasta su **fecha de corte**']),
               card('NO sabe', ['Lo posterior al corte', '**Tus datos** y tu modelo', 'Cuándo se equivoca']),
               card('Y entonces…', ['Puede **alucinar**: inventa con aplomo', 'Se arregla dándole contexto y herramientas'])) +
          dg(svg_sabe()) + callout(f'Caso real del laboratorio de S5: un LLM de 3B contestó «el cliente 12670 sigue en riesgo» siendo su probabilidad **alta**: confundió el sentido. Por eso medimos (guia.md).'),
          nota('Sabe lenguaje y lo que vio al entrenarse hasta una fecha de corte. No sabe lo posterior, no conoce tus datos privados y no sabe que no sabe: ante una pregunta que no puede responder, produce algo plausible. Eso es una alucinación. El remedio no es «pedirle que no alucine», sino darle datos (RAG) y herramientas, y evaluar.',
               f'«¿Probabilidad del cliente {CLIENTE["id"]}?»: solo, inventa una cifra verosímil; con la herramienta predecir_cliente devuelve {es(float(CLIENTE["prob"]), 4)}, tramo baja, versión {CLIENTE["version"]}. La respuesta «inventada» del esquema es una ilustración: no la hemos medido.',
               'Si el LLM contesta con mucha seguridad, ¿cómo comprobáis que la cifra viene de una herramienta y no de su imaginación?',
               'Caso del 12670: laboratorio-agentes/guia.md (prueba de humo con el 3B). Cliente 12369: notebook 02 del extra de S5.'))
    slide('4', 1, 'El prompt', 'Instrucciones', 'El prompt: sistema, ejemplos, contexto y pregunta',
          '<div class="split2"><div class="col"><div class="capa sis"><b>Sistema</b><span>«Predices si un cliente volverá a comprar en 90 días. Alta = buena noticia. Si una herramienta devuelve error, díselo al usuario y no inventes cifras.»</span></div>'
          '<div class="capa eje"><b>Ejemplos</b><span>Pregunta → herramienta → respuesta corta (few-shot)</span></div>'
          '<div class="capa ctx"><b>Contexto</b><span>Documentos recuperados y resultados de herramientas</span></div>'
          '<div class="capa usr"><b>Usuario</b><span>«¿Qué probabilidad tiene el cliente 12369?»</span></div></div>'
          '<div class="col">' + codigo('{\n  "cliente_id": 12369,\n  "probabilidad": 0.3035,\n  "tramo": "baja",\n  "version_modelo": 6\n}', 'Salida estructurada (JSON): se valida con código') +
          card('Razonamiento', ['El modelo escribe **pasos intermedios** antes de responder', 'Suele ayudar en problemas de varios pasos, a cambio de **más tokens, tiempo y coste**']) + '</div></div>',
          nota('El prompt tiene capas: instrucciones del sistema (rol y reglas), ejemplos (few-shot), contexto (documentos, resultados de herramientas) y la pregunta del usuario. Pide la salida estructurada (JSON con un esquema) cuando otro programa va a leerla: se valida con código, no con fe. Los modelos de razonamiento escriben pasos antes de contestar: mejoran casos de varios pasos pero cuestan más tokens y tiempo.',
               'El texto del sistema está adaptado de las instrucciones reales del servidor mcp-modelo-retencion: «La probabilidad es de VOLVER A COMPRAR… no inventes cifras». El JSON es la salida real de predecir_cliente (campos abreviados).',
               '¿Por qué conviene que el sistema diga explícitamente «no inventes cifras» si ya tiene una herramienta?',
               'Instrucciones y salida: notebook 02 del extra de S5.'))
    slide('4', 1, 'Tokens, coste y latencia', 'Conceptos de operación', 'Calidad, velocidad y coste se negocian',
          '<div class="split2"><div class="card">' + dg(svg_triangulo()) + '</div><div class="col">' +
          card('Se paga y se espera por…', ['**Tokens de entrada**: prompt, historial, documentos', '**Tokens de salida**: se generan **uno a uno** (de ahí la latencia)', 'Cada **paso de agente** es otra llamada']) +
          card('Local o API', ['Local (Ollama): sin coste por llamada, pero con **tu hardware** y sus límites', 'API: pagas por token y dependes del proveedor']) + '</div></div>',
          nota('Dos ideas de operación. Coste: lo que entra y lo que sale se mide en tokens; contextos largos y respuestas largas cuestan. Latencia: la salida se genera token a token, así que respuestas largas o razonamiento tardan. Un agente multiplica ambos porque hace varias llamadas. Calidad, velocidad y coste se negocian: se mide, no se supone.',
               'En el laboratorio de S5 comparamos tres modelos Qwen2.5 locales: los tiempos son de un portátil sin GPU, no los de vuestra máquina; por eso no ponemos cifras sueltas aquí.',
               '¿Qué reduciríais primero para abaratar un agente que tarda y cuesta demasiado?',
               'Laboratorio de agentes de S5 (laboratorio-agentes/guia.md): local frente a API, latencias del portátil del profesor.'))


def construir_3():
    # ---- 5 · Embeddings ----
    slide('5', 2, 'De texto a vector', 'Embeddings', 'Un embedding convierte un texto en números que guardan su significado',
          dg(svg_texto_vector()) + '<p class="fte">Fuente: los modelos de embeddings de Google Cloud dan vectores densos «que representan mejor el significado»; el gemini-embedding-001 llega a 3072 dimensiones y los vectores van normalizados (docs.cloud.google.com, Text embeddings).</p>',
          nota('Un modelo de embeddings convierte un texto en un vector de cientos o miles de números. La propiedad clave: textos con significado parecido dan vectores cercanos, aunque no compartan palabras. A la derecha, un mapa 2D ilustrativo: las preguntas sobre recompra caen cerca de los textos de retención. Los ejes no significan nada por sí solos.',
               '«¿Volverá a comprar?» y «Retención a 90 días» no comparten palabras y deberían quedar cerca; «Devolver un pedido» queda en otro grupo. Es una búsqueda semántica, no por palabra clave.',
               '¿Qué fallaría si buscáramos solo por palabras clave la pregunta «¿cuándo vuelve un cliente?» en nuestros documentos?',
               urls('embed')))
    slide('5', 1, 'Similitud del coseno', 'Medir parecido', 'La similitud se mide con el ángulo entre vectores',
          '<div class="split2"><div class="card">' + dg(svg_coseno()) + '</div><div class="col">' +
          tabla(['Texto', 'Vector', 'a·b', '|b|', 'coseno'], html_coseno_tabla(), 'cos') +
          card('Cálculo con A', [f'a = pregunta = {VQ}, |a| = {es(norma(VQ), 0)}', f'a·b = 4·5 + 3·2 + 0·1 = {punto(VQ, DOCS[0][1])}', f'|b| = √30 = {es(norma(DOCS[0][1]))}', f'coseno = {punto(VQ, DOCS[0][1])} / ({es(norma(VQ), 0)} · {es(norma(DOCS[0][1]))}) = **{es(coseno(VQ, DOCS[0][1]))}**']) + '</div></div>'
          '<p class="fte">Vectores de 3 números inventados para poder hacer la cuenta a mano: los reales tienen cientos o miles. Cálculo hecho en generar.py.</p>',
          nota('El coseno mide el ángulo entre dos vectores, no su longitud: 1 es la misma dirección, 0 casi sin relación. Con la pregunta (4, 3, 0) y tres textos de juguete: el de retención sale 0,949, el de devoluciones 0,698 y la receta de paella 0,099. Se recuperan los más parecidos. En los embeddings de Google los vectores vienen normalizados, así que coseno, producto escalar y distancia euclídea dan el mismo orden.',
               f'a·b = 4·5 + 3·2 + 0·1 = 26; |a| = 5; |b| = √30 = 5,477; coseno = 26 / 27,386 = {es(coseno(VQ, DOCS[0][1]))}. Los vectores son inventados, de 3 números.',
               '¿Por qué nos importa el ángulo y no la longitud del vector?',
               urls('embed')))
    slide('5', 2, 'Bases vectoriales y troceado', 'Dónde se guardan', 'Se trocea, se guarda un vector por trozo y se buscan los más cercanos',
          dg(svg_chunks_indice()) + '<p class="fte">En Google Cloud: Vector Search (algoritmo ScaNN) o la búsqueda vectorial de BigQuery (VECTOR_SEARCH). Los índices aproximados aceleran la consulta y miden su «recall» (docs.cloud.google.com).</p>',
          nota('Dos decisiones prácticas. Troceado (chunking): los documentos largos se parten en trozos; pequeños son precisos pero pierden contexto, grandes conservan contexto pero meten ruido; el solapamiento evita cortar una idea por la mitad. Índice vectorial: guarda un vector por trozo y devuelve los k más parecidos a la pregunta; la búsqueda aproximada (ANN) es más rápida que comparar con todos, a cambio de poder perder algún vecino real (recall).',
               'Una guía del curso en trozos de un apartado cada uno, con solapamiento de un par de frases, es un buen punto de partida; se ajusta midiendo.',
               '¿Qué le pasaría a una tabla de comandos si el troceado la partiera por la mitad?',
               urls('vs', 'bqvs')))

    # ---- 6 · RAG ----
    slide('6', 2, 'RAG: dos tuberías', 'Retrieval-Augmented Generation', 'RAG: primero se buscan los trozos, luego se genera con ellos',
          dg(svg_rag()),
          nota('RAG son dos tuberías. La de ingesta (se hace antes y al actualizar): trocear los documentos, embeber cada trozo e indexarlo. La de consulta (en cada pregunta): embeber la pregunta, recuperar los k trozos más parecidos, reordenarlos si hace falta, construir el prompt con ellos, generar y citar de dónde sale. El modelo no «sabe» los documentos: se los das en el prompt.',
               'Si indexáramos las guías del curso, la pregunta «¿cómo hago el rollback del agente?» recuperaría el apartado L6 de laboratorio-agentes/guia.md. Es un ejemplo ilustrativo: no lo hemos construido en el curso.',
               '¿Qué parte de la tubería de consulta añade más latencia y cuál más coste?',
               urls('rag', 'ragengine')))
    slide('6', 2, 'RAG, ajuste fino o contexto largo', 'Cuándo usar cada uno', 'No hay una opción mejor: depende del problema',
          html_rag_tabla() + callout('**No son excluyentes**: se combinan, p. ej. RAG para los hechos y ajuste fino para el tono.'),
          nota('Tabla honesta, sin ganador. RAG: conocimiento que cambia y hay que citar; el riesgo es recuperar mal. Ajuste fino: estilo, formato o tarea fija; no se actualiza fácilmente y puede memorizar datos obsoletos. Contexto largo: pocos documentos que caben enteros; es lo más simple, pero cada llamada es más cara y lenta. Se decide con el tipo de dato y cómo cambia.',
               'Normas internas que cambian cada trimestre: RAG. Un formato de salida muy estricto: ajuste fino o salida estructurada. Un contrato de 20 páginas que consultamos una vez: contexto largo.',
               '¿Qué elegiríais para un asistente que responde sobre el reglamento interno de un banco que se actualiza cada mes?'))
    slide('6', 1, 'Cómo falla un RAG y cómo se evalúa', 'Fallos y evaluación', 'Un RAG falla en cuatro sitios y se evalúa en dos',
          '<div class="cadena"><span>Documentos</span><b class="m m3">3</b>➜<span>Trocear</span><b class="m m2">2</b>➜<span>Indexar</span>➜<span>Recuperar</span><b class="m m1">1</b>➜<span>Prompt</span><b class="m m4">4</b>➜<span>Generar</span></div>'
          + grid(4, html_fallos()) +
          grid(2, card('Se evalúa la recuperación', ['¿Trajo los trozos correctos? Con **preguntas de oro** con su documento esperado']),
               card('Se evalúa la respuesta', ['¿Es **fiel** a lo recuperado? ¿**Cita** y se puede comprobar?'])),
          nota('Cuatro fallos típicos y dónde se ven. 1) Recuperación mala: trae trozos que no responden. 2) Troceado malo: corta ideas. 3) Datos obsoletos: el índice no se actualizó. 4) Inyección de instrucciones: un documento contiene órdenes que el modelo obedece; hay que tratar lo recuperado como datos, no como instrucciones. Se evalúa en dos partes: la recuperación (¿trajo lo correcto?) y la generación (¿es fiel y cita?).',
               'Una pregunta de oro: «¿Cómo vuelvo a la versión anterior del agente?» con su documento esperado (guia.md, L6). Si la recuperación no lo trae, el fallo es de búsqueda, no del LLM.',
               'Si el RAG responde mal, ¿cómo averiguáis si falló la búsqueda o la generación?',
               urls('rag', 'ragengine')))

    # ---- 7 · Dato y contexto ----
    slide('7', 2, 'Ingeniería de contexto', 'Qué entra en la ventana', 'El contexto es un recurso escaso y caro: hay que diseñarlo',
          dg(svg_ventana()),
          nota('Ingeniería de contexto es decidir qué entra en la ventana en cada llamada: instrucciones, historial, memoria corta y larga, conocimiento recuperado, resultados de herramientas y estado o plan. Es escaso (la ventana es finita) y caro (cada token cuesta tiempo y dinero). Técnicas: resumir el historial, recuperar solo lo necesario, pedir a las herramientas respuestas cortas y recortar lo antiguo.',
               'predecir_cliente devuelve un JSON pequeño (probabilidad, tramo, versión) en vez de volcar tablas enteras al contexto: es ingeniería de contexto (notebook 02 del extra de S5).',
               '¿Qué quitaríais primero del contexto si la conversación se hace demasiado larga?'))
    slide('7', 2, 'Gobierno del dato', 'Qué sale del banco', 'Antes de enviar nada fuera: qué dato, a quién y con qué permiso',
          dg(svg_gobierno()) + grid(3, card('Qué sale', ['Prompt y contexto **viajan** al proveedor del modelo']),
                                    card('Quién ve qué', ['El agente debe tener **los permisos del usuario**, no más']),
                                    card('Datos personales', ['Mínimo necesario, enmascarar y **preguntar a Cumplimiento**'])),
          nota('Gobierno del dato con una regla simple: cada vez que se envía un texto a un modelo externo, viaja dato. Hay que saber qué dato, a quién, con qué permiso y bajo qué política del banco. No inventamos normativa: la política concreta la dicta el banco y su equipo de Cumplimiento. Buenas prácticas: mínimo necesario, enmascarar datos personales, permisos del usuario y no del agente, y un modelo local cuando el dato no puede salir.',
               'En el curso usamos el conjunto de datos Online Retail II y un LLM local con Ollama: no hay claves ni dato que salga del portátil (laboratorio de agentes de S5).',
               '¿Quién en vuestro equipo decide hoy qué datos pueden enviarse a un modelo externo?',
               'Laboratorio de agentes de S5: «sin claves, sin coste por llamada y sin Google Cloud» (laboratorio-agentes/guia.md).'))

    # ---- 8 · Herramientas y MCP ----
    slide('8', 1, 'Function calling', 'Llamar a funciones', 'El LLM no ejecuta nada: pide que se ejecute una función',
          dg(svg_secuencia()),
          nota('Llamada a funciones: la aplicación da al modelo un catálogo de herramientas (nombre, descripción y argumentos). El modelo, en lugar de contestar, devuelve «quiero llamar a predecir_cliente con cliente_id=12369». La aplicación la ejecuta, devuelve el resultado y el modelo redacta la respuesta. El LLM nunca ejecuta código ni toca datos: lo hace tu sistema, con tus permisos y tus validaciones.',
               f'El resultado real de la herramienta: probabilidad {es(float(CLIENTE["prob"]), 4)}, tramo baja. Si el LLM «redacta» otra cifra, lo detectamos con una pregunta de oro.',
               '¿Dónde pondríais la validación de argumentos: en el LLM, en la aplicación o en la herramienta?',
               urls('react', 'mcp_arq')))
    slide('8', 2, 'MCP y skills', 'Un estándar para herramientas', 'MCP: un estándar abierto para conectar herramientas a la IA',
          dg(svg_mcp()) + grid(3, card('Un servidor ofrece', ['**Herramientas**: acciones', '**Recursos**: datos de contexto', '**Prompts**: plantillas']),
                                  card('Cómo se conecta', ['**stdio**: servidor local', '**HTTP en streaming**: servidor remoto']),
                                  card('Skill', ['Una carpeta con `SKILL.md`: cuándo usarla y cómo', 'Se carga **solo cuando hace falta**'])) +
          '<div class="ruta"><span class="st">En el curso</span><span class="st">Extra de S5: dos servidores MCP solo con notebooks</span><span class="st">Laboratorio de agentes: mcp-retencion y skills</span></div>',
          nota('MCP (Model Context Protocol) es un estándar abierto, presentado en noviembre de 2024, para conectar aplicaciones de IA con herramientas y datos: «como un USB-C para la IA». Un host (IDE, agente) crea un cliente por cada servidor. El servidor ofrece herramientas, recursos y prompts; se conecta por stdio (local) o HTTP en streaming (remoto). Una skill es otra cosa: instrucciones empaquetadas que el agente carga solo cuando hacen falta.',
               'Nuestro extra de S5 construye dos servidores MCP solo con notebooks: mcp-datos-master (SQL vigilado sobre SQLite o BigQuery) y mcp-modelo-retencion (el modelo @champion). El laboratorio de agentes los usa desde un agente con skills.',
               '¿Qué ventaja tiene un estándar frente a que cada aplicación escriba sus propias integraciones?',
               urls('mcp_anuncio', 'mcp_intro', 'mcp_arq') + '. Extra de S5: extra-mcp-notebooks/README.md; laboratorio: laboratorio-agentes/guia.md.'))
    slide('8', 2, 'Seguridad de las herramientas', 'Lo que construimos', 'Una herramienta con acceso a datos se protege en capas',
          dg(svg_capas_sql()),
          nota('Una herramienta que acepta SQL libre es una puerta a los datos: se protege en capas. Descripción clara, validación de argumentos, vigilancia del SQL (solo SELECT), conexión de solo lectura, topes (filas y bytes facturados) y registro de cada llamada. Ninguna capa vale sola: una expresión regular no es un analizador de SQL. Principios: mínimo privilegio, solo lectura por defecto y aprobación humana para lo que escribe o gasta.',
               'En BigQuery, con maximum_bytes_billed=1 el servicio rechaza la consulta (Query exceeded limit for bytes billed): es un tope real que probamos en el extra de S5. Pruebas: 38 pruebas, 13 entradas SQL rechazadas.',
               '¿Qué capa seguiría protegiendo los datos si el LLM fuese engañado por una inyección de prompt?',
               'Extra de S5: extra-mcp-notebooks/README.md (38 pruebas, 13 entradas rechazadas, prueba de BigQuery) y notebook 01.'))


def construir_4():
    # ---- 9 · Agentes y sistemas agénticos ----
    slide('9', 1, 'Del chatbot al agente', 'Espectro de autonomía', 'Del LLM suelto al multiagente: más autonomía, menos control',
          html_espectro() + '<div class="barra"><span>← más control del código, más predecible</span><span>más autonomía del modelo, más coste y riesgo →</span></div>',
          nota('Un espectro, no una etiqueta. LLM suelto: contesta con lo que sabe. RAG: busca antes de contestar. Workflow con LLM: los pasos los escribes tú en código. Agente: el LLM decide los pasos y las herramientas. Multiagente: varios agentes con roles. La definición que usamos es la de Anthropic: workflows son caminos predefinidos en código; agentes son sistemas donde el LLM dirige dinámicamente su proceso. Empieza siempre por lo más simple que resuelva el problema.',
               'Nuestro caso: «¿qué es el AUC?» es un LLM suelto; «¿cómo hago el rollback?» sería RAG; «cada lunes, lista del día y redactar mensajes» es un workflow; «¿a quién llamo hoy y qué le digo?» es el agente del laboratorio de S5. El multiagente solo está planteado, no implementado.',
               '¿Qué problema de vuestro día a día se resolvería con un workflow y no necesita un agente?',
               urls('agentes') + '. Laboratorio: laboratorio-agentes/guia.md (el extra de dos agentes aparece como «solo planteado: no implementado»).'))
    slide('9', 3, 'El bucle ReAct con nuestro caso', 'Percibir, razonar, actuar', 'El agente piensa, actúa, observa… y responde',
          '<div class="split3b"><div class="card">' + dg(svg_react()) + '</div>' + html_traza_react() + '</div>'
          '<p class="fte">Traza ilustrada con los resultados reales de los notebooks del extra de S5 (resumen_cliente y predecir_cliente), no es la salida de un LLM: que un LLM elija bien la herramienta está sin verificar en el curso.</p>',
          nota('ReAct (Reason + Act) alterna pensamiento y acción: el modelo razona qué le falta, llama a una herramienta, lee el resultado y repite hasta poder responder. Es el bucle de casi todos los agentes. Mira el ejemplo: primero pide los datos del cliente al servidor de datos, después la probabilidad al servidor del modelo, y solo entonces redacta; las cifras vienen de las herramientas, no del modelo.',
               f'Pregunta: «¿qué probabilidad tiene el cliente 12369 y cuánto ha comprado?». resumen_cliente: Austria, 3 facturas, 1511,15. predecir_cliente: {es(float(CLIENTE["prob"]), 4)}, tramo baja, versión 6. Respuesta con ambas cifras. La traza es ilustrada; que un LLM real elija bien la herramienta está sin verificar (README del extra).',
               '¿Qué haría el agente si resumen_cliente devolviera «el cliente no existe»? ¿Qué querríais que hiciera?',
               urls('react') + '. Cifras: notebooks 01 y 02 del extra de S5.'))
    slide('9', 1, 'Planificar, recordar, reflexionar y repartir', 'Capacidades y multiagente', 'Un agente planifica, recuerda y se revisa; varios agentes, solo si compensa',
          grid(2,
               card('Un agente capaz', cuerpo='<div class="cap3"><p><b>Planificar</b> dividir la tarea en pasos y rehacer el plan si falla</p>'
                                           '<p><b>Recordar</b> corta = la ventana · larga = un almacén externo</p>'
                                           '<p><b>Reflexionar</b> revisar su propio resultado antes de darlo por bueno</p></div>'),
               '<div class="card"><h3>Multiagente: ¿cuándo?</h3><div class="sino"><div class="si"><b>SÍ</b>' + lista(['Tareas que se **reparten** en paralelo', 'Contextos que no caben juntos', 'Roles con permisos distintos']) +
               '</div><div class="no"><b>NO</b>' + lista(['La tarea cabe en **un** agente', 'Cada agente multiplica coste y latencia', 'Los errores se propagan y cuesta depurar']) + '</div></div></div>') +
          callout('En el curso, el extra de **dos agentes** está solo planteado (no implementado): se medirá antes de adoptarlo.'),
          nota('Tres capacidades que hacen a un agente útil: planificar (descomponer la tarea y rehacer el plan), memoria (corta, la propia ventana; larga, un almacén externo) y reflexión (revisar su resultado, como el patrón evaluador-optimizador). El multiagente suena atractivo pero cada agente multiplica llamadas, coste y puntos de fallo: solo compensa si la tarea se reparte, si los contextos no caben juntos o si los permisos deben separarse.',
               'En el curso no hay multiagente: el laboratorio de S5 lo deja planteado y dice que «más agentes no es mejor por defecto: se mide».',
               '¿Qué tarea de vuestro equipo se repartiría de verdad entre dos agentes con permisos distintos?',
               urls('agentes') + '. Laboratorio: laboratorio-agentes/guia.md (extra de dos agentes: solo planteado).'))
    slide('9', 1, 'Barreras y riesgos', 'Guardrails y humano en el bucle', 'Barreras fuera del modelo: limitan lo que entra, lo que hace y lo que sale',
          dg(svg_guardrails()) + f'<div class="grid4">{html_riesgos()}</div>',
          nota('Los guardrails son reglas fuera del modelo, en código: filtran la entrada, limitan las acciones (permisos y aprobación humana para lo que escribe o gasta) y revisan la salida antes de mostrarla. Riesgos principales: inyección de prompt (un texto o documento que da órdenes), permisos excesivos, bucles sin fin y coste que se dispara. Controles: separar datos de instrucciones, mínimo privilegio y solo lectura, tope de pasos y tiempo, y presupuesto por conversación.',
               'La puerta de calidad de nuestro laboratorio es un guardrail de despliegue: un agente nuevo no pasa a producción si empeora al actual, y siempre hay aprobación humana.',
               '¿Qué acción de un agente en vuestro trabajo exigiría siempre un humano en el bucle?',
               urls('agentes') + '. Laboratorio: laboratorio-agentes/guia.md (puerta de calidad: igual, rechazada, aceptada).'))
    slide('9', 2, 'Evaluar y trazar', 'Preguntas de oro y trazas', 'Un agente se evalúa con datos, no con impresiones',
          '<div class="split2"><div class="col">' + ''.join(f'<div class="paso2"><b>{i}</b><span>{md(t)}</span></div>' for i, t in enumerate([
              '**25 preguntas de oro**: herramienta esperada y dato comprobable', 'Ejecutar el agente y guardar la **traza** de cada conversación',
              'Puntuar: ¿herramienta correcta? ¿cifra correcta? ¿**sentido** correcto?', '**Puerta de calidad**: igual · rechazada · aceptada', 'Solo entonces se promueve'], 1)) +
          '</div><div class="card">' + dg(svg_traza_eval()) + '</div></div>',
          nota('Un agente se evalúa como cualquier software: con un conjunto de preguntas de oro, cada una con la herramienta esperada y un dato comprobable. Cada ejecución deja una traza (los pasos, las llamadas y los tiempos) que sirve para depurar y para comparar versiones. La puerta de calidad compara el agente nuevo con el de producción: igual, rechazada o aceptada. Hay una categoría específica que vigila el sentido de la probabilidad.',
               'Nuestro laboratorio: 25 preguntas de oro, trazas en MLflow, puerta de calidad y una categoría «sentido» porque un LLM de 3B confundió volver a comprar con riesgo de abandono.',
               '¿Qué pregunta de oro añadiríais para vigilar que el agente nunca invente una cifra?',
               'Laboratorio de agentes de S5: laboratorio-agentes/guia.md (piezas, preguntas de oro, trazas en MLflow, puerta de calidad).'))

    # ---- 10 · En producción y en Google Cloud ----
    slide('10', 2, 'Arquitectura de referencia', 'Curso frente a Google Cloud', 'Sistema agéntico: el curso frente a Google Cloud',
          dg(svg_arq()) + svg(1176, 34, leyenda(250, 6, 'lg'), 'Leyenda de las formas', 'lg'),
          nota('La misma arquitectura en dos mundos. Un usuario habla con una aplicación; detrás hay un agente que orquesta un modelo, herramientas MCP, conocimiento (RAG) y datos, y todo alrededor lleva secretos, identidad y observabilidad. En el curso usamos Ollama, un bucle en Python, servidores MCP en notebooks, SQLite y MLflow, y GitHub Actions con identidad federada. En Google Cloud, cada pieza tiene un servicio: Model Garden, ADK sobre Agent Runtime, MCP en Cloud Run, RAG Engine o Búsqueda de vectores, BigQuery, Secret Manager, IAM y Cloud Logging, Trace y Monitoring.',
               'El RAG del curso aún no está construido («sin construir»); los demás componentes del lado «Curso» son los de los laboratorios y el extra de S5. Los nombres del lado GCP son los de la documentación y la consola actuales; la correspondencia con nombres anteriores (Vertex AI, Agent Engine) está sin verificar.',
               '¿Qué pieza del lado Google Cloud sería la primera que tendríais que pedir a vuestro equipo de plataforma?',
               urls('plataforma', 'adk', 'runtime', 'runmcp', 'ragengine', 'vs', 'bqvs', 'secretos', 'wif', 'obs')))
    slide('10', 2, 'LLMOps y AgentOps', 'Operar un agente', 'Operar un agente es el mismo ciclo que operar un modelo',
          dg(svg_llmops()),
          nota('LLMOps o AgentOps es aplicar a prompts, skills y agentes lo que ya hacemos con el modelo de ML: versionar, evaluar antes de desplegar, aprobar con una persona, desplegar, observar y poder volver atrás. Los costes se vigilan en la observación: tokens, pasos y latencia. En el curso es literalmente el mismo ciclo de S4 con otros workflows.',
               'Nuestro laboratorio tiene cuatro workflows de GitHub Actions: agente-ci, agente-evaluar, agente-nueva-version y agente-rollback; el alias champion de MLflow marca qué agente manda.',
               '¿Qué dato mínimo guardaríais de cada ejecución para poder explicar una respuesta dentro de seis meses?',
               'Laboratorio de agentes de S5: laboratorio-agentes/guia.md y los cuatro workflows agente-*.yml.'))
    slide('10', 1, 'GCP: modelos y Studio', 'Dónde vive cada cosa (1)', 'En Google Cloud: los modelos viven en la plataforma de Gemini',
          callout('La consola en español muestra **«Plataforma de Gemini»**; la documentación la llama «Gemini Enterprise Agent Platform», **«una evolución de Vertex AI»**. Los nombres cambian: se confirman siempre en la consola.') +
          '<div class="grid3">' + cap('gcp-plataforma.webp') + cap('gcp-model-garden.webp') + cap('gcp-agent-studio.webp') + '</div>',
          nota('Primero, la advertencia de nombres: Google ha ido renombrando sus servicios de IA. La documentación actual presenta la «Gemini Enterprise Agent Platform» como una evolución de Vertex AI, y la consola en español muestra «Plataforma de Gemini». Model Garden es la biblioteca para descubrir, probar, personalizar y desplegar modelos de Google y de socios; Agent Studio es el espacio para elegir modelos y refinar instrucciones y prompts. Que Agent Studio sea el antiguo Vertex AI Studio y Agent Runtime el antiguo Agent Engine: sin verificar (la documentación consultada no lo dice).',
               'Las tres capturas son reales, de la cuenta del curso el 26/11/2026, y no hemos lanzado ningún prompt ni habilitado nada. En Model Garden se ve la tarea «Embeddings de textos» entre las categorías.',
               '¿Dónde miraríais primero qué modelos están disponibles en vuestra región?',
               urls('plataforma', 'garden', 'studio')))
    slide('10', 2, 'GCP: datos y búsqueda', 'Dónde vive cada cosa (2)', 'Los embeddings y la búsqueda semántica viven en tres sitios',
          '<div class="grid3">' + cap('gcp-busqueda-vectores.webp') + cap('gcp-rag-engine.webp') + cap('gcp-bigquery.webp') + '</div>'
          '<div class="ruta"><span class="st">Búsqueda de vectores: índices ANN (ScaNN)</span><span class="st">RAG Engine: corpus gestionado de extremo a extremo</span><span class="st">BigQuery: AI.GENERATE_EMBEDDING + VECTOR_SEARCH en SQL</span></div>',
          nota('Tres formas de montar la búsqueda semántica en Google Cloud. Búsqueda de vectores (Vector Search): un motor de búsqueda vectorial basado en ScaNN, con índices y extremos de índice. RAG Engine: un componente gestionado que cubre ingesta, transformación (trocear), embedding, indexación, recuperación y generación. BigQuery: genera embeddings con SQL (AI.GENERATE_EMBEDDING, la función recomendada para consultas nuevas; ML.GENERATE_EMBEDDING también está documentada) y busca con VECTOR_SEARCH; es lo natural si los datos ya están allí.',
               'En las capturas, la cuenta del curso no tiene ni índices ni corpus de RAG: son las pantallas de lista vacía, no hemos creado nada. En BigQuery no hay pantalla de búsqueda vectorial: es una función SQL.',
               '¿Qué opción elegiríais si vuestros documentos ya están en BigQuery y no queréis mover datos?',
               urls('vs', 'ragengine', 'bqvs', 'bqemb', 'bqref', 'embed')))
    slide('10', 1, 'GCP: agentes y alojamiento', 'Dónde vive cada cosa (3)', 'Los agentes se hacen con ADK y corren en Agent Runtime o Cloud Run',
          '<div class="grid2">' + cap('gcp-agent-runtime.webp') + cap('gcp-cloud-run.webp') + '</div>'
          '<div class="ruta"><span class="st">ADK: marco de código abierto para agentes</span><span class="st">Agent Runtime: entorno gestionado</span><span class="st">Cloud Run: contenedores, también servidores MCP por HTTP</span></div>',
          nota('El Agent Development Kit (ADK) es un marco de código abierto para construir agentes en Python, TypeScript, Go y Java, y se despliega en Agent Runtime, Cloud Run o GKE. Agent Runtime es el entorno gestionado para desplegar y escalar agentes, con soporte para ADK, LangChain, LangGraph, LlamaIndex, AG2, A2A y agentes propios. Cloud Run es una plataforma gestionada de contenedores y también puede alojar servidores MCP que usen HTTP en streaming, pero no los de stdio. Es importante: nuestros servidores del extra usan stdio y habría que cambiarlos de transporte.',
               'Capturas reales del 26/11/2026: «No hay instancias de agente» en Agent Runtime y la portada de Cloud Run sin servicios. No hemos desplegado nada.',
               '¿Qué cambiaría en nuestro servidor mcp-modelo-retencion para alojarlo en Cloud Run?',
               urls('adk', 'runtime', 'run', 'runmcp')))
    slide('10', 1, 'GCP: secretos e identidad', 'Dónde vive cada cosa (4)', 'Los secretos y la identidad tienen su propio sitio',
          '<div class="grid2 caps2">' + cap('gcp-secret-manager.webp') + cap('gcp-iam.webp') + '</div>'
          '<div class="ruta"><span class="st">Secret Manager: claves y credenciales fuera del código</span><span class="st">IAM y Workload Identity Federation: identidad sin claves de larga vida</span></div>',
          nota('Dos piezas transversales. Secret Manager guarda secretos y credenciales (claves de API, contraseñas) fuera del código. IAM define quién puede qué; Workload Identity Federation permite que cargas externas (por ejemplo GitHub Actions) accedan a Google Cloud con identidades federadas en lugar de claves de cuentas de servicio: es lo que usamos en S4.',
               'En las capturas: sin secretos todavía y los permisos del proyecto (correos difuminados). No hemos creado nada.',
               '¿Qué secreto tiene hoy alguien de vuestro equipo en un archivo de configuración que debería estar en un gestor de secretos?',
               urls('secretos', 'wif')))
    slide('10', 1, 'GCP: registros y trazas', 'Dónde vive cada cosa (5)', 'Los registros y las trazas dicen qué hizo el agente',
          '<div class="grid2 caps2">' + cap('gcp-logging.webp') + cap('gcp-trace.webp') + '</div>'
          '<div class="ruta"><span class="st">Logging: registros de cada ejecución</span><span class="st">Trace: la traza de cada llamada</span><span class="st">Monitoring: métricas y alertas</span></div>',
          nota('Cloud Logging es un sistema de gestión de registros en tiempo real; la documentación de agentes describe trazas en Cloud Trace, registros en Cloud Logging y métricas en Cloud Monitoring, con formato OpenTelemetry. Es el equivalente de lo que vimos con MLflow tracing y la traza MCP de la interfaz.',
               'En las capturas: registros vacíos (0 resultados en los últimos 5 minutos) y, en Trace, el aviso «El almacenamiento de seguimiento no se inicializó para este proyecto». Esa pantalla pide habilitar algo y NO lo hemos hecho.',
               '¿Cómo sabríais hoy, paso a paso, qué hizo un agente cuando da una respuesta equivocada?',
               urls('logging', 'obs')))
    # ---- 11 · Cierre ----
    slide('11', 2, 'Mapa mental', 'Todo en una página', 'Todo en una página: de los datos al sistema agéntico',
          dg(svg_mapa_mental()),
          nota('Recapitulación en una página, de lo general a lo concreto: datos y ML clásico (variables, modelo, AUC); redes y transformers (neurona, atención, token); LLM (prompt, temperatura, alucinación, coste); conocimiento (embeddings, coseno, RAG, chunk); contexto y herramientas (ventana, function calling, MCP, skill); agentes (ReAct, planificar, multiagente, guardrails); y la operación (evaluación, trazas, LLMOps, Google Cloud). El hilo común: el LLM razona y redacta; las herramientas y los datos aportan los hechos; la evaluación y la operación lo hacen fiable.',
               f'Todo cabe en una frase de nuestro caso: pregunto por el cliente {CLIENTE["id"]}, el agente consulta datos y modelo, y responde {es(float(CLIENTE["prob"]), 4)} con su tramo y su fuente.',
               '¿Qué rama del mapa sentís más débil y qué os gustaría ver en el laboratorio?'))
    slide('11', 1, 'Glosario', 'Los términos clave', f'{sum(1 for x in GLOSARIO if x["chip"])} términos clave (glosario completo, con {len(GLOSARIO)}, en glosario.md)',
          html_glosario_rejilla(),
          nota('Esta rejilla recoge los términos que se han usado hoy; el archivo glosario.md de esta carpeta los ordena de lo general a lo concreto, con una definición corta y un ejemplo de nuestro caso. Úsalo como repaso o como material para el alumnado. Términos del glosario completo: ' + ', '.join(t['busca'] for t in GLOSARIO) + '.',
               'Cada término del glosario lleva, cuando existe, un ejemplo de nuestro caso: el cliente 12369, el modelo retencion-90d@champion o el servidor mcp-modelo-retencion.',
               '¿Qué término os resulta hoy más confuso y cuál explicaríais a un compañero con vuestras palabras?'))
    slide('11', 2, 'Autoevaluación', 'Cinco preguntas', 'Cinco preguntas: piensa la respuesta y pulsa «ver respuesta»',
          html_autoevaluacion(),
          nota('Haz las preguntas en voz alta, deja pensar medio minuto y revela la respuesta. Sirven de cierre y de comprobación de lo esencial: herramientas frente a conocimiento del modelo, workflow frente a agente, RAG, contexto y seguridad de las herramientas.',
               'Si el aula se anima, pide que alguien responda la 1 con el ejemplo del cliente 12369 y la 5 con los controles que añadiría a un agente con acceso a SQL.',
               '¿Cuál de las cinco preguntas os costaría más responder sin la presentación?'))
    slide('11', 1, 'Fuentes', 'Referencias', 'Fuentes consultadas el 26/11/2026',
          html_fuentes(),
          nota('Todas las direcciones se consultaron el 26/11/2026. Las cifras y fechas de la clase salen de ellas o de los notebooks del curso. Lo que no pudimos comprobar se dice «sin verificar»: la equivalencia entre nombres anteriores y actuales de los servicios de Google Cloud (Vertex AI Studio y Agent Studio, Agent Engine y Agent Runtime), que un LLM de tamaño pequeño elija bien la herramienta, y los precios y límites de cualquier servicio, que no se citan.',
               'Para revisar un dato, abre la fuente y compara con la diapositiva; los nombres de productos de Google Cloud cambian a menudo.',
               '¿Qué fuente os gustaría tener a mano durante el laboratorio?'))


def construir():
    construir_1()
    construir_2()
    construir_3()
    construir_4()
    # La portada se añade la última (necesita los minutos por parte) y se coloca al principio.
    mins = {'1': 1}      # la portada (1 min) aún no está en SLIDES
    for s in SLIDES:
        p = re.search(r'data-part="(\d+)" data-min="(\d+)"', s)
        mins[p.group(1)] = mins.get(p.group(1), 0) + int(p.group(2))
    total = sum(mins.values())
    ag = ''.join(f'<tr><td class="np">{i}</td><td>{esc(NOMBRES_PARTE[k])}</td><td class="mn">{mins[k]} min</td></tr>' for i, k in enumerate(PARTES, 1))
    cuerpo = ('<div class="cover"><div class="portada-izq"><p class="sub">De los datos al agente, y dónde vive cada cosa en Google Cloud</p>'
              '<div class="objetivo"><b>Al terminar podrás…</b>' + lista(['Situar cada pieza: **IA, ML, LLM, RAG, agente**', 'Explicar por qué un LLM **necesita herramientas y datos**', 'Saber **dónde vive** cada pieza en Google Cloud']) + '</div>'
              '<div class="chips"><span class="chip">Un solo caso: ¿volverá a comprar en 90 días?</span><span class="chip">Capturas reales de la consola</span></div></div>'
              f'<table class="tbl agenda"><tr><th>#</th><th>Agenda propuesta</th><th>Minutos</th></tr>{ag}<tr class="tot"><td></td><td>Total propuesto</td><td class="mn">{total} min</td></tr></table></div>')
    slide('1', 1, 'Fundamentos de la IA, los LLM, los RAG y los agentes', 'Portada y agenda', 'Fundamentos de la IA, los LLM, los RAG y los agentes',
          cuerpo,
          nota('Presenta el objetivo: al terminar, el alumnado sabe situar cada pieza, entiende por qué un LLM necesita herramientas y datos, y sabe dónde vive cada cosa en Google Cloud. Enseña la agenda y recuerda que hay un único caso a lo largo de la clase: ¿volverá a comprar un cliente en 90 días? La barra inferior permite saltar de sección; S abre estas notas, O el índice, F la pantalla completa.',
               'Hilo de la clase: cliente 12369 → datos → modelo → LLM → herramienta → agente → Google Cloud.',
               '¿Quién ha usado ya un LLM con herramientas, y para qué?'))
    SLIDES.insert(0, SLIDES.pop())      # la portada, la primera
    return total


# ======================================================================================================================
# Glosario (de lo general a lo concreto). chip = frase corta para la rejilla de la diapositiva (None = solo en glosario.md)
# ======================================================================================================================
def g(nivel, term, busca, definicion, ejemplo='', chip=None):
    return {'nivel': nivel, 'term': term, 'busca': busca, 'def': definicion, 'ejemplo': ejemplo, 'chip': chip}


NIVELES = ['Lo general', 'Datos y aprendizaje automático', 'Redes y modelos de lenguaje', 'Búsqueda y RAG', 'Contexto, herramientas y agentes',
           'Evaluar y operar', 'Google Cloud']
GLOSARIO = [
    g(0, 'Inteligencia artificial (IA)', 'Inteligencia artificial', 'Sistemas que hacen tareas que normalmente exigen inteligencia humana: percibir, decidir, generar lenguaje.',
      'Un sistema de reglas que marca los pedidos que hay que revisar es IA aunque no aprenda de datos.', 'máquinas que hacen tareas «inteligentes»'),
    g(0, 'Aprendizaje automático (ML)', 'Aprendizaje automático', 'Sistemas que aprenden patrones a partir de los datos en lugar de seguir reglas escritas a mano.',
      'El modelo retencion-90d aprende de las compras pasadas de los clientes.', 'aprender patrones de los datos'),
    g(0, 'Aprendizaje profundo (DL)', 'Aprendizaje profundo', 'Aprendizaje automático con redes neuronales de muchas capas; brilla con imágenes, audio y texto.',
      'Reconocer un producto en una foto; un LLM es una red profunda.', 'redes neuronales de muchas capas'),
    g(0, 'IA generativa', 'IA generativa', 'Modelos que crean contenido nuevo: texto, imágenes, código.', 'Redactar el borrador de la recomendación para un gestor.', 'crea contenido nuevo'),
    g(1, 'Variable (feature)', 'feature', 'Una característica medible del caso que el modelo recibe como entrada.',
      'recencia_dias = 413 y frecuencia_180d = 0 del cliente 12369; el modelo usa 13 variables.', 'entrada medible del modelo'),
    g(1, 'Modelo', 'Modelo', 'Función aprendida de los datos que convierte variables en una predicción.',
      'retencion-90d@champion devuelve 0,3035 para el cliente 12369.', 'función: variables → predicción'),
    g(1, 'AUC', 'AUC', 'Medida de cuán bien un modelo ordena a los positivos por delante de los negativos: 0,5 es azar y 1 es perfecto.',
      'Versión 6 del modelo: 0,6982 en validación y 0,7471 en test.', '0,5 = azar · 1 = perfecto'),
    g(1, 'Sobreajuste', 'Sobreajuste', 'Memorizar los datos de entrenamiento y fallar con datos nuevos; se detecta con validación y test.',
      'El error de entrenamiento baja pero el de validación vuelve a subir.', 'memorizar en vez de aprender'),
    g(2, 'Red neuronal', 'Red neuronal', 'Neuronas artificiales (suma ponderada + activación) conectadas en capas.',
      'Nuestra regresión logística equivale a una sola neurona con sigmoide.', 'neuronas conectadas en capas'),
    g(2, 'Transformer', 'Transformer', 'Arquitectura de red basada en atención; es la base de los LLM actuales (Vaswani et al., 2017).', '', 'arquitectura basada en atención'),
    g(2, 'Atención', 'Atención', 'Mecanismo por el que cada token pondera a los demás para interpretar su significado en contexto.',
      'En «el pedido… estaba roto», «estaba» mira sobre todo a «pedido».', None),
    g(2, 'Token', 'Token', 'Pieza de texto (trozo de palabra, signo) que el modelo procesa; coste y límites se miden en tokens.', 'El troceado real depende del modelo.', 'pieza de texto que lee el modelo'),
    g(2, 'Parámetros', 'Parámetros', 'Los números que el modelo aprende en el entrenamiento; son su «saber» estable.', '', None),
    g(2, 'Ventana de contexto', 'Ventana de contexto', 'La cantidad de tokens que el modelo puede considerar a la vez en una llamada.', 'Si algo no cabe en la ventana, para el modelo no existe.', 'lo que cabe en una llamada'),
    g(2, 'LLM (modelo de lenguaje grande)', 'LLM', 'Red transformer entrenada para predecir el siguiente token; genera y entiende lenguaje.', 'Qwen2.5 en Ollama, en el laboratorio de agentes de S5.', 'predice el siguiente token'),
    g(2, 'Preentrenamiento', 'Preentrenamiento', 'Fase inicial: leer muchísimo texto prediciendo el siguiente token.', '', None),
    g(2, 'Ajuste fino (fine-tuning)', 'fine-tuning', 'Seguir entrenando un modelo con ejemplos de tu tarea.', '', 'entrenar con ejemplos de tu tarea'),
    g(2, 'LoRA', 'LoRA', 'Ajuste fino que entrena solo unas matrices pequeñas añadidas y deja fijo el resto (Hu et al., 2021).', '', 'ajuste fino barato'),
    g(2, 'RLHF (valoraciones humanas)', 'RLHF', 'Alineación: ajustar el modelo con preferencias humanas para que siga instrucciones.', '', 'alinear con preferencias humanas'),
    g(2, 'Prompt', 'Prompt', 'El texto de entrada: instrucciones del sistema, ejemplos, contexto y pregunta.', '«¿Qué probabilidad tiene el cliente 12369?»', 'instrucciones + contexto + pregunta'),
    g(2, 'Temperatura', 'Temperatura', 'Parámetro que controla cuánto se arriesga al elegir el siguiente token: baja = predecible, alta = variada.', '', 'cuánto arriesga al elegir'),
    g(2, 'Alucinación', 'Alucinación', 'Contenido plausible pero inventado, dicho con aplomo.', 'Una probabilidad del cliente 12369 «de memoria» en vez de la de la herramienta.', 'inventar con aplomo'),
    g(2, 'Salida estructurada', 'Salida estructurada', 'Respuesta en un formato fijo (por ejemplo JSON) que el código puede validar.', 'La respuesta de predecir_cliente: probabilidad, tramo y versión.', None),
    g(2, 'Razonamiento', 'Razonamiento', 'Pasos intermedios que el modelo escribe antes de responder; mejora problemas de varios pasos a cambio de más tokens.', '', None),
    g(3, 'Embedding', 'Embedding', 'Vector de números que representa el significado de un texto (o imagen).', '«¿Volverá a comprar?» queda cerca de «Retención a 90 días».', 'texto convertido en vector'),
    g(3, 'Vector', 'Vector', 'Lista ordenada de números.', 'Los embeddings reales tienen cientos o miles; el ejemplo de la clase usa 3.', None),
    g(3, 'Similitud (coseno)', 'coseno', 'Medida de parecido entre vectores por el ángulo que forman: 1 misma dirección, 0 sin relación.', 'En la clase: 0,949 para el texto de retención y 0,099 para la paella.', 'ángulo entre dos vectores'),
    g(3, 'Base vectorial (índice vectorial)', 'vectorial', 'Almacén que guarda vectores y devuelve los k más parecidos a una consulta, normalmente de forma aproximada.', '', 'busca los vectores más cercanos'),
    g(3, 'Chunk (trozo)', 'chunk', 'Fragmento de un documento que se indexa y se recupera por separado.', 'Un apartado de una guía del curso.', 'trozo de un documento'),
    g(3, 'RAG (generación aumentada por recuperación)', 'RAG', 'Buscar trozos relevantes y dárselos al LLM en el prompt para que responda con ellos y cite.', 'Recuperar el apartado L6 de la guía para responder cómo hacer un rollback.', 'buscar primero, generar después'),
    g(3, 'Reranker', 'Reranker', 'Segundo paso que reordena los trozos recuperados por relevancia antes de construir el prompt.', '', 'reordena lo recuperado'),
    g(4, 'Ingeniería de contexto', 'Ingeniería de contexto', 'Diseñar qué entra en la ventana (instrucciones, historial, memoria, conocimiento, resultados, estado) en cada llamada.', '', 'decidir qué entra en la ventana'),
    g(4, 'Function calling (llamada a funciones)', 'Function calling', 'El modelo devuelve «quiero llamar a esta función con estos argumentos»; la aplicación la ejecuta.',
      'predecir_cliente(cliente_id=12369).', 'el modelo pide, tu sistema ejecuta'),
    g(4, 'Herramienta', 'Herramienta', 'Función con contrato (nombre, descripción, argumentos) que un agente puede invocar.', 'resumen_cliente, predecir_cliente, por_que.', 'función con contrato'),
    g(4, 'MCP (Model Context Protocol)', 'MCP', 'Estándar abierto para conectar aplicaciones de IA con herramientas, recursos y prompts de servidores.', 'mcp-datos-master y mcp-modelo-retencion, del extra de S5.', 'estándar para conectar herramientas'),
    g(4, 'Skill', 'Skill', 'Carpeta con un SKILL.md: instrucciones que el agente carga solo cuando hacen falta.', 'Las skills del laboratorio de agentes de S5.', 'saber hacer cargado a demanda'),
    g(4, 'Workflow', 'Workflow', 'Sistema donde LLM y herramientas siguen caminos predefinidos en código.', 'Cada lunes: lista del día y redactar mensajes.', 'pasos fijos escritos en código'),
    g(4, 'Agente', 'Agente', 'Sistema donde el LLM dirige dinámicamente sus pasos y el uso de herramientas.', '«¿A quién llamo hoy y qué le digo?»', 'el LLM decide los pasos'),
    g(4, 'ReAct', 'ReAct', 'Patrón que alterna razonar y actuar: pensar, llamar a una herramienta, observar y repetir (Yao et al., 2022).', 'Datos del cliente → probabilidad → respuesta.', 'pensar → actuar → observar'),
    g(4, 'Multiagente', 'Multiagente', 'Varios agentes con roles distintos que se reparten una tarea.', 'En el curso: solo planteado, no implementado.', 'varios agentes con roles'),
    g(5, 'Guardrail (barrera)', 'Guardrail', 'Regla fuera del modelo, en código, que limita lo que entra, lo que hace o lo que sale.', 'Un tope de pasos; solo lectura en la base de datos.', 'regla fuera del modelo'),
    g(5, 'Humano en el bucle', 'Humano en el bucle', 'Una persona aprueba las acciones sensibles antes de que se ejecuten.', 'La aprobación de un environment antes de desplegar un agente.', 'una persona aprueba'),
    g(5, 'Inyección de prompt', 'Inyección de prompt', 'Texto (o documento) que intenta dar órdenes al agente para que se salte sus reglas.', '', 'texto que da órdenes al agente'),
    g(5, 'Evaluación (preguntas de oro)', 'preguntas de oro', 'Conjunto de preguntas con la herramienta esperada y un dato comprobable para medir un agente.', '25 preguntas de oro en el laboratorio de agentes de S5.', 'preguntas con respuesta comprobable'),
    g(5, 'Traza', 'Traza', 'Registro paso a paso de una conversación: llamadas al LLM, a herramientas y tiempos.', 'Las trazas del laboratorio se guardan en MLflow.', 'registro paso a paso'),
    g(5, 'LLMOps / AgentOps', 'LLMOps', 'Versionar, evaluar, aprobar, desplegar, observar y revertir prompts, skills y agentes, como se hace con un modelo.', 'Los workflows agente-ci, agente-evaluar, agente-nueva-version y agente-rollback.', 'el ciclo de vida de un agente'),
    g(5, 'Alias / champion', 'champion', 'Puntero con nombre a una versión de un modelo (o agente) en el registro: «la que manda ahora».', '@champion apunta a la versión 6 de retencion-90d.', 'la versión que manda ahora'),
    g(6, 'Plataforma de Gemini (antes Vertex AI)', 'Plataforma de Gemini', 'Nombre en la consola en español de la «Gemini Enterprise Agent Platform», que la documentación presenta como una evolución de Vertex AI.', '', None),
    g(6, 'Model Garden', 'Model Garden', 'Biblioteca para descubrir, probar, personalizar y desplegar modelos de Google y de socios.', '', None),
    g(6, 'Agent Studio', 'Agent Studio', 'Espacio para elegir modelos, refinar instrucciones y optimizar prompts.', '', None),
    g(6, 'RAG Engine', 'RAG Engine', 'Componente gestionado de la plataforma para montar RAG: ingesta, trocear, embeber, indexar, recuperar y generar.', '', None),
    g(6, 'Búsqueda de vectores (Vector Search)', 'Búsqueda de vectores', 'Motor de búsqueda vectorial de Google basado en ScaNN, con índices y extremos de índice.', '', None),
    g(6, 'ADK (Agent Development Kit)', 'ADK', 'Marco de código abierto para construir agentes (Python, TypeScript, Go y Java).', '', None),
    g(6, 'Agent Runtime', 'Agent Runtime', 'Entorno gestionado para desplegar y escalar agentes.', '', None),
    g(6, 'Cloud Run', 'Cloud Run', 'Plataforma gestionada para ejecutar contenedores; puede alojar servidores MCP con HTTP en streaming.', '', None),
    g(6, 'Secret Manager', 'Secret Manager', 'Servicio para guardar y controlar secretos y credenciales.', '', None),
    g(6, 'Workload Identity Federation (WIF)', 'Workload Identity Federation', 'Permite que cargas externas accedan a Google Cloud con identidades federadas, sin claves de cuenta de servicio.', 'GitHub Actions con WIF en S4.', None),
]


def html_glosario_rejilla():
    items = [t for t in GLOSARIO if t['chip']]
    return '<div class="gls">' + ''.join(f'<div class="gl"><b>{esc(t["term"].split(" (")[0])}</b><span>{esc(t["chip"])}</span></div>' for t in items) + '</div>'


AUTOEVAL = [
    ('¿Por qué un LLM solo no puede darte la probabilidad del cliente 12369, y qué hay que darle para que lo haga?',
     f'No tiene tus datos ni tu modelo; si responde, inventa (alucina). Hay que darle una **herramienta** (llamada a funciones o MCP) que ejecute el modelo: predecir_cliente({CLIENTE["id"]}) devuelve {es(float(CLIENTE["prob"]), 4)}, tramo «{CLIENTE["tramo"]}».'),
    ('¿Qué diferencia hay entre un workflow con LLM y un agente?',
     'En un **workflow** los pasos están predefinidos en código; en un **agente** el LLM decide dinámicamente los pasos y las herramientas (definición de Anthropic).'),
    ('Un RAG responde mal: ¿dónde miras primero?',
     'En la **recuperación** (¿trajo los trozos correctos? troceado, embeddings, k, datos obsoletos) y, después, en la **generación** (¿es fiel a lo recuperado y cita?).'),
    ('¿Por qué decimos que el contexto es un recurso escaso y caro?',
     'La ventana es finita y cada token cuesta tiempo y dinero: hay que decidir qué entra (instrucciones, historial, memoria, conocimiento, resultados de herramientas), qué se resume y qué se recorta.'),
    ('Nombra tres controles antes de dar a un agente acceso a una base de datos.',
     '**Mínimo privilegio y solo lectura**, vigilancia del SQL y topes (filas, bytes), aprobación humana para lo que escribe o gasta, y trazas de cada llamada. Ninguno vale solo.'),
]


def html_autoevaluacion():
    out = []
    for i, (q, a) in enumerate(AUTOEVAL, 1):
        out.append(f'<div class="qa"><div class="q"><b class="qn">{i}</b><span>{esc(q)}</span><button class="rev" data-i="{i}" aria-expanded="false">ver respuesta</button></div>'
                   f'<div class="ans" hidden>{md(a)}</div></div>')
    return '<div class="qas">' + ''.join(out) + '</div>'


def html_fuentes():
    grupos = [('Historia y modelos', ['dartmouth', 'transformer', 'lora', 'rlhf', 'rag', 'react']),
              ('MCP y agentes', ['mcp_anuncio', 'mcp_intro', 'mcp_arq', 'agentes']),
              ('Google Cloud · plataforma, datos y búsqueda', ['plataforma', 'garden', 'studio', 'embed', 'vs', 'ragengine', 'bqvs', 'bqemb', 'bqref']),
              ('Google Cloud · agentes, alojar, proteger y observar', ['adk', 'runtime', 'run', 'runmcp', 'secretos', 'wif', 'logging', 'obs'])]
    cols = []
    for tit, ks in grupos:
        li = ''.join(f'<li><span>{esc(FUENTES[k][0])}</span><a href="{FUENTES[k][1]}" target="_blank" rel="noopener">{FUENTES[k][1]}</a></li>' for k in ks)
        cols.append(f'<div class="fgrp"><h3>{esc(tit)}</h3><ul>{li}</ul></div>')
    loc = ''.join(f'<li>{esc(v)}</li>' for v in LOCALES.values())
    cols.append(f'<div class="fgrp"><h3>Del curso (01-Sesiones)</h3><ul class="loc">{loc}</ul></div>')
    sv = ('<div class="sv"><b>Sin verificar:</b> la equivalencia entre nombres anteriores y actuales (Vertex AI Studio ↔ Agent Studio, Agent Engine ↔ Agent Runtime) · '
          'que un LLM pequeño elija bien la herramienta · precios y límites de los servicios (no se citan).</div>')
    return f'<div class="fuentes">{"".join(cols)}</div>{sv}'


def glosario_md():
    out = ['# Glosario: fundamentos de la IA, los LLM, los RAG y los agentes', '',
           'De lo más general a lo más concreto. Cada término lleva una definición corta y, cuando existe, un ejemplo de **nuestro caso** del curso '
           '(¿volverá a comprar un cliente en los próximos 90 días?: cliente 12369, modelo `retencion-90d@champion`, servidores MCP del extra de S5).', '',
           f'Generado por `generar.py` (consulta de fuentes: {CONSULTA}). Las fuentes están en la última diapositiva de `index.html`.', '']
    for n, nombre in enumerate(NIVELES):
        out += [f'## {n + 1}. {nombre}', '']
        for t in GLOSARIO:
            if t['nivel'] == n:
                out += [f'### {t["term"]}', '', t['def'], '']
                if t['ejemplo']:
                    out += [f'*En nuestro caso:* {t["ejemplo"]}', '']
    out += ['## Fuentes', ''] + [f'- {n_}: <{u}>' for n_, u in FUENTES.values()] + ['']
    return '\n'.join(out)


# ======================================================================================================================
# Marco: CSS (fondo blanco, sin movimiento al pasar el ratón) y JavaScript del visor
# ======================================================================================================================
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
.sub{font-size:25px;line-height:1.35;color:var(--suave);max-width:640px}
.chips{display:flex;gap:8px;flex-wrap:wrap}
.chip{display:inline-block;font-size:17px;padding:6px 15px;border-radius:999px;border:1px solid #bcd3ec;background:#eef5fc;color:var(--acento);font-weight:600}
.tag{display:inline-block;font-size:12px;padding:1px 9px;border-radius:999px;border:1px solid var(--linea);background:var(--gris);color:var(--tinta)}
.tag.ok{border-color:#86c79c;background:#ecf8f0;color:var(--ok)}.tag.warn{border-color:#e2b56b;background:#fdf6e9;color:var(--aviso)}
.card{border:1px solid var(--linea);border-radius:12px;padding:14px 18px;background:#fff;min-width:0}
.callout{border-left:5px solid var(--acento);background:#eef5fc;padding:11px 18px;border-radius:0 10px 10px 0;font-size:20px;line-height:1.4}
.msg{font-size:24px;line-height:1.3;font-weight:600;border-left:6px solid var(--acento);padding:10px 20px;background:#eef5fc;border-radius:0 12px 12px 0}
.small{font-size:18px;line-height:1.42}.centro{text-align:center}
.fte{font-size:12.5px;line-height:1.4;color:var(--suave)}
.mono{font-family:var(--mono);font-size:.92em;background:var(--gris);padding:0 4px;border-radius:4px}
.lb{display:inline-block;font-weight:700;font-size:11.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--suave);margin-right:4px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.split2{display:grid;grid-template-columns:1fr 1fr;gap:18px;min-height:0}.split2b{display:grid;grid-template-columns:1.45fr 1fr;gap:16px}.split3b{display:grid;grid-template-columns:470px 1fr;gap:16px}
.col{display:flex;flex-direction:column;gap:10px;min-width:0}
.list{list-style:none;display:flex;flex-direction:column;gap:5px}.list li{font-size:19.5px;line-height:1.38;padding-left:17px;position:relative}
.list li::before{content:"";position:absolute;left:2px;top:9px;width:7px;height:7px;border-radius:50%;background:var(--acento)}
.dg svg{display:block;width:100%;height:auto}
.card .dg svg{max-width:100%}
.tbl{width:100%;border-collapse:collapse;font-size:18px}.tbl th{text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--suave);border-bottom:2px solid var(--linea);padding:6px 9px}
.tbl td{border-bottom:1px solid var(--linea);padding:13px 12px;line-height:1.35;vertical-align:top}
.tbl.comp td:first-child{white-space:nowrap}.tbl.comp td:nth-child(2){background:#eef5fc}
.tbl.cos td{font-size:15px;padding:7px 8px}.tbl.cos td:last-child{background:#eef5fc;font-size:17px}
.term{border:1px solid var(--linea);border-radius:10px;background:var(--gris);overflow:hidden}
.term .bar{padding:5px 10px;border-bottom:1px solid var(--linea);background:#eaeef3;font-size:12.5px;color:var(--suave)}.term .bar em{font-style:normal}
.src{font-family:var(--mono);font-size:17px;line-height:1.5;padding:8px 12px;white-space:pre-wrap}
.kpi .n{display:block;font-size:32px;line-height:1.15;color:var(--acento);margin-bottom:4px}
/* portada */
.cover{display:grid;grid-template-columns:1fr 470px;gap:30px;align-items:start;margin-top:6px}
.portada-izq{display:flex;flex-direction:column;gap:20px;padding-top:24px}
.objetivo{border:1px solid var(--linea);border-radius:12px;padding:12px 18px;background:#fff}.objetivo b{display:block;font-size:17px;margin-bottom:6px;color:var(--acento)}
.agenda td{padding:5px 9px;font-size:15px}.agenda .np{color:var(--acento);font-weight:700;width:30px}.agenda .mn{text-align:right;white-space:nowrap;color:var(--suave)}.agenda .tot td{font-weight:700;border-top:2px solid var(--linea)}
/* muñecas y línea de tiempo */
.muneca{display:grid;grid-template-columns:580px 1fr;gap:22px;align-items:center}
.mfilas{display:flex;flex-direction:column;gap:9px}.mrow{display:flex;gap:12px;align-items:flex-start;border:1px solid var(--linea);border-radius:10px;padding:8px 12px}
.mrow b{font-size:20px}.mrow p{font-size:15.5px;line-height:1.35;color:var(--tinta)}.dot{flex:none;width:20px;height:20px;border-radius:50%;border:2px solid var(--acento);margin-top:3px}
.tl{position:relative;display:grid;grid-template-columns:repeat(7,1fr);gap:10px;margin-top:30px}
.tl::before{content:"";position:absolute;left:0;right:0;top:58px;height:4px;background:var(--acento);border-radius:2px}
.ev{text-align:center;display:flex;flex-direction:column;align-items:center;gap:6px}.ev .yr{font-size:36px;color:var(--acento)}.ev .pt{width:16px;height:16px;border-radius:50%;background:#fff;border:4px solid var(--acento);margin:2px 0 6px;position:relative;z-index:1}
.ev h4{font-size:21px}.ev p{font-size:16.5px;line-height:1.35;color:var(--tinta)}.cur{font-size:14px;color:var(--acento);font-weight:600;background:#eef5fc;border-radius:8px;padding:4px 8px}.ev small{font-size:12px;color:var(--suave);font-family:var(--mono);overflow-wrap:anywhere}
/* etapas */
.etapas{display:flex;align-items:stretch;gap:8px}.etapa{flex:1;border:1px solid var(--linea);border-top:5px solid var(--acento);border-radius:12px;padding:11px 14px;display:flex;flex-direction:column;gap:6px}
.etapa h3{font-size:23px}.etapa p{font-size:19px;line-height:1.4}.etapa .s{color:var(--suave);font-size:17px}.etapa .r{font-weight:600;color:var(--acento);font-size:18px}
.flechaH{align-self:center;font-size:28px;color:var(--acento)}
/* prompt */
.capa{border:1px solid var(--linea);border-left:7px solid var(--acento);border-radius:8px;padding:8px 13px;display:flex;flex-direction:column;gap:2px}
.capa b{font-size:15px;text-transform:uppercase;letter-spacing:.06em;color:var(--acento)}.capa span{font-size:18px;line-height:1.4}
.capa.eje{border-left-color:#7b8794}.capa.ctx{border-left-color:#c58a12}.capa.usr{border-left-color:var(--ok)}
.ruta{display:flex;gap:8px;flex-wrap:wrap;align-items:center}.st{background:#eef5fc;border:1px solid #bcd3ec;border-radius:999px;padding:7px 17px;font-size:18px;color:var(--acento);font-weight:600}.fl2{color:var(--acento);font-size:20px}
/* muestras */
.split3{display:flex;height:64px;border-radius:10px;overflow:hidden;border:1px solid var(--linea)}.split3 div{display:flex;flex-direction:column;justify-content:center;padding:0 12px}
.split3 b{font-size:16px}.split3 span{font-size:13px;color:var(--suave)}.split3 .b1{flex:6;background:#dbeafe}.split3 .b2{flex:2;background:#eef5fc}.split3 .b3{flex:2;background:#fde9c8}
/* RAG: fallos */
.cadena{display:flex;align-items:center;gap:7px;font-size:17px;flex-wrap:wrap;color:var(--acento)}.cadena span{background:#eef5fc;border:1px solid #bcd3ec;border-radius:8px;padding:5px 11px;color:var(--tinta)}
.m{display:inline-block;width:24px;height:24px;border-radius:50%;background:var(--mal);color:#fff;text-align:center;line-height:24px;font-size:14px;margin-left:-4px}
.falla{border:1px solid #e0a3a3;background:#fdf3f3;border-radius:12px;padding:10px 13px}.falla .n{display:inline-block;width:26px;height:26px;border-radius:50%;background:var(--mal);color:#fff;text-align:center;line-height:26px;font-size:15px;margin-bottom:4px}
.falla h3{font-size:20px}.falla p{font-size:17.5px;line-height:1.4}
.riesgo{border:1px solid var(--linea);border-top:4px solid var(--mal);border-radius:12px;padding:10px 13px}.riesgo h3{font-size:20px}.riesgo p{font-size:17px;line-height:1.4;margin-bottom:6px}.riesgo .ctl{color:var(--ok);font-weight:600}
/* espectro */
.espectro{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;align-items:end;min-height:430px}
.espectro .paso{border:1px solid var(--linea);border-top:5px solid var(--acento);border-radius:12px;padding:10px 13px;min-height:var(--h);display:flex;flex-direction:column;gap:6px;background:#fff}
.espectro .paso:nth-child(1){--h:250px;border-top-color:#9fb7d4}.espectro .paso:nth-child(2){--h:295px}.espectro .paso:nth-child(3){--h:340px}.espectro .paso:nth-child(4){--h:385px}.espectro .paso:nth-child(5){--h:430px;border-top-color:#073d73}
.espectro h3{font-size:22px}.espectro p{font-size:17.5px;line-height:1.4}.espectro .eg{margin-top:auto;font-size:16px;color:var(--suave)}.nv{display:inline-block;width:26px;height:26px;border-radius:50%;background:var(--acento);color:#fff;text-align:center;line-height:26px;font-size:15px}
.barra{display:flex;justify-content:space-between;font-size:15px;color:var(--suave);border-top:3px solid var(--acento);padding-top:6px}
/* traza ReAct */
.traza{display:flex;flex-direction:column;gap:5px}.tr{display:flex;gap:10px;align-items:flex-start;border-radius:8px;padding:8px 11px;font-size:17px;line-height:1.35;background:var(--gris)}
.tr .tg{flex:none;width:112px;font-weight:700;font-size:14px;text-transform:uppercase;letter-spacing:.04em;padding-top:2px}.tr .tc{flex:1}
.tr.p{background:#eef5fc}.tr.pn .tc{font-style:italic;color:var(--suave)}.tr.ac{background:#fff4dc}.tr.ac .tc{font-family:var(--mono);font-size:15.5px}.tr.ob{background:#ecf8f0}.tr.ob .tc{font-family:var(--mono);font-size:15.5px}.tr.rs{background:#dbeafe;font-weight:600}
.paso2{display:flex;gap:12px;align-items:center;border:1px solid var(--linea);border-radius:10px;padding:12px 15px;font-size:19.5px}.paso2>b{flex:none;width:28px;height:28px;border-radius:50%;background:var(--acento);color:#fff;text-align:center;line-height:28px}
.cap3 p{font-size:20px;line-height:1.45;margin-bottom:12px}.cap3 b{color:var(--acento)}
.sino{display:grid;grid-template-columns:1fr 1fr;gap:10px}.sino>div{border-radius:10px;padding:9px 12px}.sino .si{background:#ecf8f0}.sino .no{background:#fdf3f3}.sino b{font-size:18px}.sino .si b{color:var(--ok)}.sino .no b{color:var(--mal)}.sino .list li{font-size:17.5px}
/* capturas */
.cap{display:flex;flex-direction:column;gap:5px;min-width:0}
.cap figcaption{font-size:13.5px;line-height:1.35;color:var(--suave)}.menu{font-family:var(--mono);font-size:12px;color:var(--acento)}
.zoom{display:block;position:relative;cursor:zoom-in;text-align:left;width:100%}
.zoom img{display:block;width:100%;height:auto;border:1px solid var(--linea);border-radius:8px}
.lupa{position:absolute;right:6px;bottom:6px;font-size:12px;background:rgba(255,255,255,.94);border:1px solid var(--linea);border-radius:6px;padding:2px 7px;display:flex;align-items:center;gap:4px;color:var(--suave)}
.pend{border:2px dashed #c9a65e;background:#fdf9f0;border-radius:10px;min-height:150px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;padding:10px;text-align:center;font-size:13.5px;color:var(--aviso)}.pend b{font-size:16px}
.caps4 .cap figcaption{font-size:11.5px}
.caps2 .zoom img{width:auto;max-width:100%;max-height:285px;margin:0 auto;object-fit:contain;background:#f6f9fd}.caps2 .cap figcaption{font-size:12.5px}
/* glosario, autoevaluación, fuentes */
.gls{display:grid;grid-template-columns:repeat(6,1fr);gap:6px}.gl{border:1px solid var(--linea);border-radius:10px;padding:5px 9px;display:flex;flex-direction:column;gap:1px}
.gl b{font-size:16.5px;color:var(--acento)}.gl span{font-size:13.5px;line-height:1.25;color:var(--tinta)}
.qas{display:flex;flex-direction:column;gap:9px}.qa{border:1px solid var(--linea);border-radius:12px;padding:12px 16px}
.q{display:flex;gap:12px;align-items:center;font-size:20px;line-height:1.35}.q span{flex:1}.qn{flex:none;width:30px;height:30px;border-radius:50%;background:var(--acento);color:#fff;text-align:center;line-height:30px;font-size:16px}
.rev{flex:none;border:1px solid var(--acento);color:var(--acento);border-radius:8px;padding:5px 14px;font-size:14px;background:#fff}.rev[aria-expanded="true"]{background:var(--acento);color:#fff}
.ans{margin-top:7px;padding:8px 12px;background:#ecf8f0;border-left:5px solid var(--ok);border-radius:0 8px 8px 0;font-size:18px;line-height:1.4}.ans[hidden]{display:none}
.fuentes{column-count:2;column-gap:24px}.fgrp{break-inside:avoid;margin-bottom:3px}.fgrp h3{font-size:12.5px;color:var(--acento);margin-bottom:0}.fgrp ul{list-style:none}.fgrp li{font-size:10px;line-height:1.16;margin-bottom:0}
.fgrp li span{display:block;font-weight:600;color:var(--tinta)}.fgrp li a{color:var(--acento);overflow-wrap:anywhere;text-decoration:none}.fgrp ul.loc li{font-size:10px}
.sv{border-left:5px solid #c9a65e;background:#fdf9f0;padding:4px 12px;font-size:12px;border-radius:0 8px 8px 0}
/* svg */
svg .nodo{fill:#f4f8fc;stroke:#8fb2d6;stroke-width:1.6}svg .nodo.puerta{fill:#fdf6e9;stroke:#c9a65e;stroke-dasharray:6 4}svg .nodo.ok{fill:#ecf8f0;stroke:var(--ok)}svg .nodo.mal{fill:#fdeeee;stroke:var(--mal)}
svg .modelo{fill:#dbeafe;stroke:#0b5cad;stroke-width:2.4}svg .modelo2{fill:none;stroke:#0b5cad;stroke-width:1}
svg .datos{fill:#eef2f6;stroke:#6b7a8c;stroke-width:1.8}svg .datos2{fill:none;stroke:#6b7a8c;stroke-width:1.8}
svg .herr{fill:#fff4dc;stroke:#c58a12;stroke-width:2}svg .user{fill:#f1f3f6;stroke:#6b7280;stroke-width:2}
svg .obs{fill:#fbfcfe;stroke:#7b8794;stroke-dasharray:7 5;stroke-width:1.6}svg .zona{fill:#fbfcfe;stroke:#8fb2d6;stroke-dasharray:6 4;stroke-width:1.6}
svg .fl{stroke:var(--acento);stroke-width:2.2;fill:none}svg .fl.g{stroke:#7b8794}svg .fl.r{stroke:var(--mal)}
svg .eje{stroke:#8a94a3;stroke-width:1.6;fill:none}svg .curva{stroke:var(--acento);stroke-width:3.4;fill:none}svg .curva.g{stroke:#8a94a3}svg .red{stroke:#b9c4d2;stroke-width:1.2}svg .vida{stroke:#b9c4d2;stroke-width:1.5;stroke-dasharray:5 5}
svg .num{fill:var(--acento)}svg .numt{font:700 14px var(--sans);fill:#fff;text-anchor:middle}
svg .t0{font:700 28px var(--sans);fill:var(--tinta);text-anchor:middle}svg .t1{font:700 18px var(--sans);fill:var(--tinta);text-anchor:middle}
svg .t2{font:16px var(--sans);fill:#4b5563;text-anchor:middle}svg .t3{font:14.5px var(--sans);fill:#4b5563;text-anchor:middle}
svg .tc{font:14.5px var(--sans);fill:#5b6472;text-anchor:middle}svg .tg{font:700 14.5px var(--sans);fill:var(--acento);text-anchor:middle}
svg .lbl{paint-order:stroke;stroke:#fff;stroke-width:7px;stroke-linejoin:round}svg .izq{text-anchor:start}svg .mal{fill:var(--mal);font-weight:700}svg .okk{fill:var(--ok)}svg .azul{fill:var(--acento);font-weight:700}svg .gris{fill:#6b7280}
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
#zoombox.on{display:flex}#zoombox img{max-width:100%;max-height:100%;background:#fff;border-radius:6px}
#zoombox p{position:fixed;top:8px;left:0;right:0;text-align:center;color:#fff;font-size:13px}
@media print{#bar,#notes,#index,#prog{display:none!important}}
"""

JS = r"""
(function(){
'use strict';
const $=(s,r)=>(r||document).querySelector(s), $$=(s,r)=>[...(r||document).querySelectorAll(s)];
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const PARTES=__PARTES__, NOMBRES=__NOMBRES__;
const slides=$$('.slide'), N=slides.length; let cur=0;
slides.forEach((s,i)=>{const f=document.createElement('div');f.className='foot';
  f.innerHTML=`<span>ML e IA · S5 · Fundamentos de la IA y los agentes</span><span><b>${esc(NOMBRES[s.dataset.part]||'')}</b> · ${i+1} / ${N}</span>`;s.appendChild(f)});
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
function zoom(on,src,alt){const z=$('#zoombox');if(on){$('#zoomimg').src=src;$('#zoomimg').alt=alt||'';}z.classList.toggle('on',!!on)}
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
document.addEventListener('click',e=>{
  const z=e.target.closest('.zoom'); if(z){e.stopPropagation();zoom(true,z.dataset.src,z.dataset.alt);return}
  const r=e.target.closest('.rev'); if(r){e.stopPropagation();const a=r.closest('.qa').querySelector('.ans');const abierto=!a.hidden;a.hidden=abierto;r.setAttribute('aria-expanded',String(!abierto));r.textContent=abierto?'ver respuesta':'ocultar';}
});
fit();
const h=parseInt((location.hash||'').slice(1),10); go(isNaN(h)?0:h-1);
addEventListener('hashchange',()=>{const n=parseInt((location.hash||'').slice(1),10);if(!isNaN(n)&&n-1!==cur)go(n-1)});
})();
"""


def html_completo():
    construir()
    js = JS.replace('__PARTES__', json.dumps(PARTES, ensure_ascii=False)).replace('__NOMBRES__', json.dumps(NOMBRES_PARTE, ensure_ascii=False))
    partes = ''.join(f'<button class="part" data-p="{k}" title="{esc(NOMBRES_PARTE[k])}">{esc(v)}</button>' for k, v in PARTES.items())
    return ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>Fundamentos de la IA, los LLM, los RAG y los agentes · ML e IA: de desarrollo a producción</title>\n'
            f'<!-- Generado por generar.py: no se edita a mano. -->\n<style>{CSS}</style>\n</head>\n<body>\n'
            '<div id="prog"></div>\n<div id="viewport"><div id="stage">\n\n' + '\n\n'.join(SLIDES) + '\n\n</div></div>\n\n'
            '<aside id="notes" aria-label="Notas del profesor"><h3>Notas del profesor</h3><div id="notetext"></div><p class="small" id="notemin"></p></aside>\n'
            '<div id="index" aria-label="Índice"><h2>Índice</h2><div class="grid" id="idxgrid"></div></div>\n'
            '<div id="zoombox" aria-label="Captura ampliada"><p>Esc o clic para cerrar</p><img id="zoomimg" alt=""></div>\n'
            '<nav id="bar" aria-label="Controles">\n'
            '  <button id="bprev" aria-label="Anterior">←</button><button id="bnext" aria-label="Siguiente">→</button>\n'
            f'  <span id="count">1 / 1</span><span id="clockref" title="Minuto planificado acumulado (propuesta)"></span>\n  {partes}\n'
            '  <span class="sp"></span>\n'
            '  <a id="bhome" href="../index.html" title="Volver al índice de la sesión S5">⌂ Índice</a><button id="bidx">Índice (O)</button><button id="bnotes">Notas (S)</button><button id="bfull">Pantalla completa (F)</button>\n'
            '</nav>\n'
            '<noscript>Esta presentación necesita JavaScript. El glosario está en glosario.md, en esta carpeta.</noscript>\n\n'
            f'<script>{js}</script>\n</body>\n</html>\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--comprobar', action='store_true')
    a = ap.parse_args()
    nuevo = html_completo()
    glos = glosario_md()
    pares = [(SALIDA, nuevo), (SALIDA_GLOSARIO, glos)]
    if a.comprobar:
        mal = [p.name for p, t in pares if not p.exists() or p.read_text(encoding='utf-8') != t]
        if mal:
            print('DESFASADO: ' + ', '.join(mal) + ': ejecuta python generar.py')
            sys.exit(1)
        print('al día')
        return
    for p, t in pares:
        actual = p.read_text(encoding='utf-8') if p.exists() else None
        if actual == t:
            print(f'{p.name}: sin cambios')
        else:
            p.write_bytes(t.encode('utf-8'))      # LF también en Windows
            print(f'escrito {p.name}')
    minutos = sum(int(m) for m in re.findall(r'data-min="(\d+)"', nuevo))
    print(f'{len(SLIDES)} diapositivas, {minutos} min')


if __name__ == '__main__':
    main()
