"""Genera el RECAP FINAL del curso «ML e IA: de desarrollo a producción» (index.html, junto a este archivo).

«Lo que ya sabes hacer»: la presentación de cierre, sesión por sesión (S0 a S5), para el alumnado técnico de un banco.
Mismo manejo que las otras presentaciones del curso (← → · O índice · S notas del profesor · F pantalla completa · Esc ·
lupa para ampliar capturas), fondo blanco y nada que se mueva al pasar el ratón.

Reglas del contenido (las vigilan las pruebas de `pruebas/test_presentacion.py`):
  - cada cifra tiene su fuente en el repositorio o se cuenta aquí mismo con glob (sesiones, presentaciones, guías...);
  - lo no probado o no decidido se rotula «sin verificar» o «por confirmar»; nada de pesos de rúbrica inventados;
  - los esquemas son SVG escritos aquí; las capturas son reales y se copiaron de los laboratorios (img/), con su origen;
  - cada carpeta o archivo que se cita (`ruta()`) existe en el repositorio.

Uso:  python generar.py              escribe index.html
      python generar.py --comprobar  no escribe; sale con 1 si no está al día
"""
import argparse
import html
import json
import re
import sys
import textwrap
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / 'index.html'
RAIZ = AQUI.parents[2]                      # curso-ml-ia-desarrollo-produccion
SES = RAIZ / '01-Sesiones'
BASE = RAIZ / '04-Proyecto-Base'
REPO_URL = 'https://github.com/helicr/curso-ml-ia-desarrollo-produccion'
ENTREGA_FINAL = 'viernes 11/12/2026, 10:00 (hora de Perú)'
EXCLUIR = {'_trabajo', '__pycache__', 'mlruns', 'node_modules', '.pytest_cache', '.ipynb_checkpoints'}

# ----------------------------------------------------------------------------------------------------------------------
# Recuentos reales del repositorio (se cuentan con glob; las pruebas los recalculan por su cuenta)
# ----------------------------------------------------------------------------------------------------------------------


def _fich(base, patron):
    return [p for p in base.rglob(patron) if not (EXCLUIR & set(p.relative_to(base).parts))]


def carpetas_sesion():
    return sorted(p for p in SES.iterdir() if p.is_dir() and re.match(r'S\d-', p.name))


def _prof(p):
    return len(p.relative_to(SES).parts)


def decks_de(carpeta):
    """Presentaciones HTML: index.html por debajo de la carpeta de la sesión (sin la interfaz web `ui` ni el índice de la sesión)."""
    return [p for p in _fich(carpeta, 'index.html') if p.parent != carpeta and 'ui' not in p.relative_to(carpeta).parts]


def guias_de(carpeta):
    return [p for p in _fich(carpeta, 'guia*.md')]


def yml_de(carpeta):
    return _fich(carpeta, '*.yml')


def nb_de(carpeta):
    return _fich(carpeta, '*.ipynb')


def contar():
    ss = carpetas_sesion()
    por = {}
    for c in ss:
        k = c.name.split('-')[0]
        por[k] = {'decks': len(decks_de(c)), 'guias': len(guias_de(c)), 'yml': len(yml_de(c)), 'nb': len(nb_de(c)),
                  'lista': sorted(p.parent.relative_to(c).as_posix() for p in decks_de(c))}
    t = {'sesiones': len(ss),
         'decks': sum(v['decks'] for v in por.values()),
         'guias': sum(v['guias'] for v in por.values()),
         'yml_ses': sum(v['yml'] for v in por.values()),
         'nb_ses': sum(v['nb'] for v in por.values()),
         'nb_base': len(list((BASE / 'notebooks').glob('*.ipynb'))),
         'yml_base': len(list((BASE / 'deploy' / 'github-actions').glob('*.yml'))),
         'yml_gh': len(list((RAIZ / '.github' / 'workflows').glob('*.yml'))),
         'tests_arch': len(list((BASE / 'tests').glob('test_*.py'))),
         'tests_def': sum(len(re.findall(r'^\s*def test_', p.read_text(encoding='utf-8'), re.M)) for p in (BASE / 'tests').glob('*.py')),
         'tareas': sum(1 for c in ss if (c / 'tarea' / 'README.md').is_file()),
         'guias_entorno': len(list((RAIZ / '03-Entorno' / 'guias').glob('*.md'))),
         'guias_recursos': len([p for p in (RAIZ / '07-Recursos' / 'guias').glob('*.md') if p.name != 'README.md'])}
    t['nb'] = t['nb_ses'] + t['nb_base']
    t['yml'] = t['yml_ses'] + t['yml_base'] + t['yml_gh']
    return t, por


N, POR = contar()


def n(x):
    """Entero con separador de millares a la española (365 → «365»; 1067371 → «1 067 371»)."""
    return f'{x:,}'.replace(',', ' ')


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


def tag(txt, clase=''):
    return f'<span class="tag {clase}">{esc(txt)}</span>'


def grid(k, *celdas, clase=''):
    return f'<div class="grid{k} {clase}">' + ''.join(celdas) + '</div>'


def ruta(p, texto=None):
    """Una ruta del repositorio (relativa a la raíz del curso). Las pruebas comprueban que existe."""
    return f'<span class="mono ruta" data-ruta="{esc(p)}">{esc(texto or p).replace("/", "/<wbr>")}</span>'


def tabla(cab, filas, clase=''):
    """Una celda que empieza por «!» se inserta como HTML tal cual."""
    def celda(c):
        return c[1:] if c.startswith('!') else md(c)
    th = ''.join(f'<th>{md(c)}</th>' for c in cab)
    tr = ''.join('<tr>' + ''.join(f'<td>{celda(c)}</td>' for c in f) + '</tr>' for f in filas)
    return f'<table class="tbl {clase}"><tr>{th}</tr>{tr}</table>'


def kpi(valor, texto, fuente='', color=''):
    f = f'<span class="fte">Fuente: {esc(fuente)}</span>' if fuente else ''
    return f'<div class="card kpi"><b class="n {color}">{esc(str(valor))}</b><p class="small">{md(texto)}</p>{f}</div>'


def nota(decir, ejemplo, pregunta):
    """Notas del profesor: qué decir (~1 min), anécdota o ejemplo y pregunta para el aula."""
    return f'Qué decir: {decir}\nEjemplo o anécdota: {ejemplo}\nPregunta para el aula: {pregunta}'


# ----------------------------------------------------------------------------------------------------------------------
# Partes (barra inferior) y diapositivas
# ----------------------------------------------------------------------------------------------------------------------
PARTES = {'A': 'Inicio', '0': 'S0', '1': 'S1', '2': 'S2', '3': 'S3', '4': 'S4', '5': 'S5', 'J': 'Salto', 'K': 'Consejos', 'E': 'Entrega', 'R': 'Repo', 'Z': 'Cierre'}
NOMBRES_PARTE = {'A': 'Apertura', '0': 'S0 · Presentación y entorno', '1': 'S1 · Datos y entrenamiento', '2': 'S2 · API y Docker',
                 '3': 'S3 · Despliegue y redes neuronales', '4': 'S4 · Orquestación y CI/CD con la nube', '5': 'S5 · MLOps y agentes',
                 'J': 'El salto completo', 'K': 'Consejos prácticos', 'E': 'Qué hacer ahora y evaluación', 'R': 'Te llevas un repositorio', 'Z': 'Cierre'}
SLIDES = []


def slide(parte, minutos, titulo, kick, h1, cuerpo, notas, clase=''):
    cuerpo = re.sub(r'\*\*([^*<>]+)\*\*', r'<b>\1</b>', cuerpo)
    cuerpo = re.sub(r'`([^`<>]+)`', r'<span class="mono">\1</span>', cuerpo)
    antetitulo = f'{NOMBRES_PARTE[parte]} · {kick}' if kick else NOMBRES_PARTE[parte]
    attrs = f' data-part="{parte}" data-min="{minutos}" data-title="{esc(titulo)}"'
    SLIDES.append(f'<section class="slide {clase}"{attrs}\n data-notes="{esc(notas)}">\n'
                  f'<p class="kick">{esc(antetitulo)}</p><h1>{md(h1)}</h1>\n<div class="bd">{cuerpo}</div>\n</section>')


# ----------------------------------------------------------------------------------------------------------------------
# Imágenes reales (img/). Rótulo = exactamente lo que se ve; origen = el laboratorio del que se copió.
# ----------------------------------------------------------------------------------------------------------------------
LUPA = ('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true">'
        '<circle cx="10" cy="10" r="6.5"/><path d="M15 15l6 6"/></svg>')
IMAGENES = {
    's0-codespaces-pestana.webp': ('Captura real',
        'GitHub, rama develop del repositorio: botón Code › pestaña Codespaces con «No codespaces» y el botón «Create codespace on develop»; al pie, quién paga el uso',
        '03-Entorno/guia-codespaces/capturas/01-pestana-codespaces.webp'),
    's1-recorrido.webp': ('Figura del proyecto base',
        '«Del dato del negocio al modelo en producción: qué construye cada cuaderno» (archivo, operacional, RAW, MASTER, FS, ML, MLflow, modelo y API)',
        '04-Proyecto-Base/docs/img/recorrido.png'),
    's1-particiones.webp': ('Figura del proyecto base',
        '«Train, validación y test: se reparten por FECHA DE CORTE, no al azar»: siete cortes de train, uno de valid y dos de test',
        '04-Proyecto-Base/docs/img/particiones.png'),
    's1-mlflow.webp': ('Figura del proyecto base',
        '«MLflow: el cuaderno de laboratorio de los entrenamientos»: el experimento retencion-90d con sus ejecuciones, mlflow.db y mlartifacts',
        '04-Proyecto-Base/docs/img/mlflow.png'),
    's2-tres-terminales.webp': ('Captura real',
        'Tres terminales de un Codespace: la API en el puerto 8080, la interfaz en el 8090 y los curl a /salud y /listo con «ok» y «listo»',
        '01-Sesiones/S2-API-y-Docker/del-ordenador-al-servicio/img/cs-03-tres-terminales.webp'),
    's2-interfaz-contenedor.webp': ('Captura real',
        'La interfaz «¿Volverá a comprar en 90 días?» servida por el contenedor, con predicciones desde http://api:8080: tramos alta, media y baja y la recomendación del cliente 13599',
        '01-Sesiones/S2-API-y-Docker/del-ordenador-al-servicio/img/cs-10-interfaz-contenedor.webp'),
    's2-api-docs.webp': ('Captura real',
        'Página /docs de la API (FastAPI): GET /salud, /listo y /modelo, y POST /predecir con su ejemplo de variables',
        '01-Sesiones/S3-Despliegue-y-Redes-Neuronales/laboratorio-recap-s2/img/r05-docs.webp'),
    's3-mlflow-comparar.webp': ('Captura real',
        'MLflow, experimento retencion-90d: «Comparing 2 Runs from 1 Experiment» (gradient_boosting y regresion_logistica) con el gráfico de coordenadas paralelas de train_auc',
        '01-Sesiones/S3-Despliegue-y-Redes-Neuronales/laboratorio-mlflow/img/m06-comparar.webp'),
    's3-actions-historial.webp': ('Captura real',
        'Pestaña Actions, workflow «Pruebas del proyecto», rama lab/actions-s3: verde (#1), rojo «Rotura a propósito: el tramo alta empieza en 0,75» (#2) y verde «Revert» (#3)',
        '01-Sesiones/S3-Despliegue-y-Redes-Neuronales/laboratorio-github-actions/img/a12-historial.webp'),
    's4-cloudrun.webp': ('Captura real',
        'Consola de Google Cloud, Cloud Run › Detalles del servicio: retencion-api con la marca verde, región southamerica-west1 y las métricas de Observabilidad',
        '01-Sesiones/S4-Orquestacion-y-CI-CD/laboratorio-cloud-journey/img/cj-04-cloudrun-consola.webp'),
    's4-artifact-registry.webp': ('Captura real',
        'Consola de Google Cloud, Artifact Registry › repositorio curso › paquete retencion-api (southamerica-west1): tres versiones creadas hace 1 hora',
        '01-Sesiones/S4-Orquestacion-y-CI-CD/laboratorio-cloud-journey/img/cj-05-artifact-registry.webp'),
    's4-aprobacion.webp': ('Captura real',
        'Run en espera de «Nueva versión del modelo»: aviso amarillo «helicr requested your review to deploy to produccion» con Review deployments; trabajos 1 y 2 en verde y el 3 esperando',
        '01-Sesiones/S4-Orquestacion-y-CI-CD/laboratorio-produccion-e2e/img/gh-01-esperando-aprobacion.webp'),
    's5-deriva-rojo.webp': ('Captura real',
        'Run «Ensayo S5: monitoreo del modelo (deriva)» en la rama lab/monitoreo/deriva: trabajos 1 y 2 en verde y «3 · Alerta» en rojo, con «ALERTA · deriva de datos: sí»',
        '01-Sesiones/S5-MLOps-y-Operacion/laboratorio-mlops/img/m-03-deriva-rojo.webp'),
    's5-issue-alerta.webp': ('Captura real',
        'Issue abierto por github-actions con la etiqueta alerta-deriva: «5 variables superan el PSI 0.25», con la tabla de PSI y KS por variable',
        '01-Sesiones/S5-MLOps-y-Operacion/laboratorio-mlops/img/m-05-issue-alerta.webp'),
    's5-panel-asistente.webp': ('Captura real',
        'Panel de producción, pestaña Asistente (LLM falso): pregunta por el cliente 12670, respuesta con 79,9 % de VOLVER A COMPRAR y las dos herramientas usadas',
        '01-Sesiones/S5-MLOps-y-Operacion/laboratorio-agentes/img/s5-12-panel-asistente.webp'),
}


def cap(nombre, alto=None, extra=''):
    """Una imagen real (clic o lupa = ampliar, Esc cierra) con su rótulo y su origen."""
    etiqueta, alt, origen = IMAGENES[nombre]
    estilo = f' style="max-height:{alto}px"' if alto else ''
    return (f'<figure class="cap" data-img="{nombre}"><button class="zoom" data-src="img/{nombre}" data-alt="{esc(alt)}" title="Ampliar (Esc cierra)" aria-label="Ampliar: {esc(alt)}">'
            f'<img src="img/{nombre}" alt="{esc(alt)}"{estilo}><span class="lupa">{LUPA} Ampliar</span></button>'
            f'<figcaption><span class="tag ok">{etiqueta}</span> {esc(alt)}{extra}<br><span class="orig">Origen: {ruta(origen)}</span></figcaption></figure>')


# ----------------------------------------------------------------------------------------------------------------------
# Utilidades de SVG: mismas formas en todos los diagramas
#   usuario = persona · modelo = rectángulo azul con doble borde · datos = cilindro · herramienta = hexágono ámbar
#   aplicación / paso = rectángulo redondeado · observabilidad = recuadro discontinuo · lo has hecho tú = círculo verde con ✓
# ----------------------------------------------------------------------------------------------------------------------
LH = {'t0': 28, 't1': 22, 't2': 19, 't3': 17, 'tc': 17}


def svg(w, h, cuerpo, etiqueta, idp='a'):
    marcas = ''.join(f'<marker id="{idp}{s}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto">'
                     f'<path d="M0 0 L10 5 L0 10 z" fill="{c}"/></marker>' for s, c in (('', '#0b5cad'), ('g', '#7b8794'), ('r', '#b91c1c'), ('o', '#15803d')))
    return f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{esc(etiqueta)}"><defs>{marcas}</defs>{cuerpo}</svg>'


def tx(x, y, s, cls='t2', lh=None):
    lh = lh or LH.get(cls.split()[0], 19)
    partes = s.split('\n')
    if len(partes) == 1:
        return f'<text x="{x:g}" y="{y:g}" class="{cls}">{esc(s)}</text>'
    ts = ''.join(f'<tspan x="{x:g}" dy="{0 if i == 0 else lh}">{esc(p)}</tspan>' for i, p in enumerate(partes))
    return f'<text x="{x:g}" y="{y:g}" class="{cls}">{ts}</text>'


def wrap(s, ancho):
    return '\n'.join(textwrap.wrap(s, ancho))


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


def nodo(x, y, w, h, t1, t2='', cls='nodo', t3='', c2='t2', c3='t2'):
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


def sh_usuario(cx, cy, etiqueta='Persona', s=1.0):
    r = 11 * s
    cuerpo = (f'<circle cx="{cx}" cy="{cy - 16 * s:g}" r="{r:g}" class="user"/>'
              f'<path d="M{cx - 21 * s:g} {cy + 22 * s:g} Q{cx - 21 * s:g} {cy + 1 * s:g} {cx} {cy + 1 * s:g} Q{cx + 21 * s:g} {cy + 1 * s:g} {cx + 21 * s:g} {cy + 22 * s:g} Z" class="user"/>')
    return cuerpo + (tx(cx, cy + 22 * s + 20, etiqueta, 't1') if etiqueta else '')


def sh_obs(x, y, w, h, t1, t2=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" class="obs"/>' + centrado(x, y, w, h, _ls(t1, t2, ''))


def zona(x, y, w, h, titulo, cls='zona'):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" class="{cls}"/>' + tx(x + 16, y + 26, titulo, 't1 izq')


def nube(x, y, w, h, cls='nube'):
    """Silueta de nube (hiperescalar) dentro de la caja x,y,w,h."""
    sx, sy = w / 100, h / 60
    d = (f'M{x + 22 * sx:g} {y + 55 * sy:g} C{x + 6 * sx:g} {y + 55 * sy:g} {x + 2 * sx:g} {y + 34 * sy:g} {x + 20 * sx:g} {y + 30 * sy:g} '
         f'C{x + 20 * sx:g} {y + 10 * sy:g} {x + 48 * sx:g} {y + 4 * sy:g} {x + 58 * sx:g} {y + 20 * sy:g} C{x + 78 * sx:g} {y + 10 * sy:g} {x + 96 * sx:g} {y + 30 * sy:g} '
         f'{x + 82 * sx:g} {y + 40 * sy:g} C{x + 100 * sx:g} {y + 44 * sy:g} {x + 94 * sx:g} {y + 55 * sy:g} {x + 80 * sx:g} {y + 55 * sy:g} Z')
    return f'<path d="{d}" class="{cls}"/>'


def flecha(idp, *pts, kind='', suf=''):
    d = 'M' + ' L'.join(f'{x:g} {y:g}' for x, y in pts)
    return f'<path d="{d}" class="fl {kind}" marker-end="url(#{idp}{suf})"/>'


def fl_g(idp, *pts):
    return flecha(idp, *pts, kind='g', suf='g')


def fl_r(idp, *pts):
    return flecha(idp, *pts, kind='r', suf='r')


def num(cx, cy, k, cls='num'):
    return f'<circle cx="{cx}" cy="{cy}" r="13" class="{cls}"/><text x="{cx}" y="{cy + 5.5}" class="numt">{k}</text>'


def visto(cx, cy, medio=False):
    """Insignia «lo has tocado tú» (✓ verde) o «con tu cuenta o en demostración» (◐ ámbar)."""
    if medio:
        return f'<circle cx="{cx}" cy="{cy}" r="14" class="vmedio"/><path d="M{cx} {cy - 14} A14 14 0 0 1 {cx} {cy + 14} Z" class="vmedio2"/>'
    return f'<circle cx="{cx}" cy="{cy}" r="14" class="visto"/><path d="M{cx - 6} {cy} L{cx - 1.5} {cy + 5} L{cx + 7} {cy - 5}" class="vtick"/>'


def dg(s, clase=''):
    return f'<div class="dg {clase}">{s}</div>'


def leyenda(x, y):
    it = [('persona', 'u'), ('modelo', 'm'), ('datos', 'd'), ('herramienta / paso de CI', 'h'), ('aplicación', 'a')]
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
        cx += 30 + len(nombre) * 8.2 + 26
    return ''.join(out)


# ----------------------------------------------------------------------------------------------------------------------
# Diagramas SVG propios (todos con las mismas formas y la misma paleta azul)
# ----------------------------------------------------------------------------------------------------------------------
def svg_portada():
    i = 'p'
    c = nube(250, 10, 210, 126) + tx(355, 78, 'Google Cloud', 't1') + tx(355, 100, 'hiperescalar', 't3')
    c += sh_datos(10, 210, 92, 86, 'Datos') + sh_modelo(128, 210, 100, 86, 'Modelo') + nodo(254, 210, 100, 86, 'API', 'y contenedor')
    c += flecha(i, (104, 253), (126, 253)) + flecha(i, (230, 253), (252, 253)) + flecha(i, (330, 208), (360, 142))
    c += sh_herr(380, 210, 82, 86, 'CI/CD')
    c += flecha(i, (356, 253), (378, 253))
    c += tx(235, 336, 'De tu portátil a producción', 't1')
    return dg(svg(470, 350, c, 'Un camino de los datos al modelo, la API, el contenedor y la nube de Google Cloud', i), 'portada-dg')


def svg_viaje():
    i = 'v'
    W, H = 1160, 372
    est = [('S0', 'mié 11/11', 'Presentación\ny entorno', 'Un entorno que\nfunciona en\ncualquier equipo', 'lap'),
           ('S1', 'vie 13/11', 'Datos y\nentrenamiento', 'De la tabla al\nmodelo, con\nMLflow', 'dat'),
           ('S2', 'mié 18/11', 'API y\nDocker', 'El modelo se\nconvierte en un\nservicio', 'mod'),
           ('S3', 'vie 20/11', 'Despliegue y\nredes neuronales', 'Pruebas que se\nponen rojas y\nvuelven al verde', 'her'),
           ('S4', 'mié 25/11', 'Orquestación y\nCI/CD en la nube', 'Del repositorio a\nCloud Run, sin\nclaves', 'nub'),
           ('S5', 'vie 27/11', 'MLOps\ny agentes', 'Vigilar, versionar,\ndeshacer y dar\nherramientas', 'obs')]
    c = f'<path d="M20 52 L1140 52" class="fl" marker-end="url(#{i})"/>'
    for k, (s, fecha, tit, frase, ico) in enumerate(est):
        x = 10 + k * 192
        cx = x + 90
        c += f'<circle cx="{cx}" cy="52" r="20" class="num"/><text x="{cx}" y="58" class="numt" style="font-size:16px">{s}</text>'
        c += f'<rect x="{x}" y="92" width="180" height="262" rx="14" class="nodo"/>'
        c += tx(cx, 120, fecha, 'tg')
        if ico == 'lap':
            c += f'<rect x="{cx - 30}" y="140" width="60" height="38" rx="5" class="nodo"/><path d="M{cx - 40} {186} L{cx + 40} {186}" class="eje" style="stroke-width:4"/>'
        elif ico == 'dat':
            c += sh_datos(cx - 28, 138, 56, 54, '')
        elif ico == 'mod':
            c += sh_modelo(cx - 34, 140, 68, 50, 'API')
        elif ico == 'her':
            c += sh_herr(cx - 36, 140, 72, 50, '')
        elif ico == 'nub':
            c += nube(cx - 46, 134, 92, 58)
        else:
            c += sh_obs(cx - 36, 140, 72, 50, '') + f'<path d="M{cx - 26} {176} L{cx - 10} {160} L{cx + 2} {170} L{cx + 24} {148}" class="curva" style="stroke-width:2.6"/>'
        c += tx(cx, 222, tit, 't1') + tx(cx, 282, frase, 't3')
    return dg(svg(W, H, c, 'Línea de seis sesiones, de S0 a S5, con su fecha, su tema y un dibujo', i))


def svg_s0():
    i = 's0'
    W, H = 1160, 372
    c = zona(10, 10, 590, 300, 'Tu equipo')
    c += nodo(30, 50, 265, 72, 'Git', 'versiona el trabajo') + nodo(310, 50, 270, 72, 'VS Code', '7 extensiones')
    c += nodo(30, 138, 265, 72, 'Miniconda', 'entorno env-ia-mlops') + nodo(310, 138, 270, 72, 'SQLite', 'la base del curso')
    c += nodo(30, 228, 550, 66, 'Diagnóstico: 12 comprobaciones', 'verificar_s1.py termina en «LISTO PARA S1»', cls='nodo ok')
    c += sh_datos(650, 100, 120, 112, 'Repositorio', 'en GitHub')
    c += flecha(i, (648, 146), (604, 146)) + tx(626, 134, 'clonar', 'tc')
    c += flecha(i, (772, 146), (828, 146)) + tx(800, 134, 'abrir', 'tc')
    c += zona(830, 10, 320, 300, 'Codespaces: sin instalar nada')
    c += nodo(850, 50, 280, 72, 'Docker', 'imágenes y contenedores') + nodo(850, 138, 280, 72, 'kind + kubectl', 'Kubernetes de ensayo')
    c += nodo(850, 228, 280, 66, 'Puertos', 'la API se ve desde tu navegador')
    c += leyenda(10, 336)
    return dg(svg(W, H, c, 'Tu equipo con Git, VS Code, Miniconda y SQLite, el repositorio en GitHub y un Codespace con Docker y kind', i))


def svg_s1():
    i = 's1'
    W, H = 1160, 350
    c = zona(282, 4, 584, 166, 'curso.db · la base analítica')
    cajas = [('Archivo', 'Online\nRetail II', 'd'), ('Operacional', 'sistema\nde ventas', 'd'), ('RAW', 'copia fiel', 'n'), ('MASTER', 'depurado y\ncon reglas', 'n'),
             ('FS', 'solo mira\nal pasado', 'n'), ('ML', 'variables,\nobjetivo y\npartición', 'n'), ('Modelo', 'tres\ncomparados', 'm'), ('MLflow', 'runs y\nregistro', 'o')]
    preg = ['¿De dónde\nviene?', '¿Cómo lo guarda\nel negocio?', '¿Qué llegó,\ntal cual?', '¿Qué es correcto\ny se puede usar?', '¿Qué sabemos\nde cada cliente?', '¿Qué queremos\npredecir?', '¿Cuál\nelegimos?', '¿Qué probamos\ny cuándo?']
    for k, (t1, t2, f) in enumerate(cajas):
        x = 10 + k * 144
        if f == 'd':
            c += sh_datos(x, 40, 118, 100, t1, t2, c2='t3')
        elif f == 'm':
            c += sh_modelo(x, 44, 118, 96, t1, t2, c2='t3')
        elif f == 'o':
            c += sh_obs(x, 44, 118, 96, t1, t2)
        else:
            c += nodo(x, 44, 118, 96, t1, t2, c2='t3')
        c += tx(x + 59, 196, preg[k], 'tg2')
        if k < 7:
            c += flecha(i, (x + 120, 92), (x + 142, 92))
    c += tx(10, 262, 'Partición por fecha de corte, no al azar', 't1 izq')
    for (x0, w, cl, t) in ((10, 420, 'b1', 'TRAIN · 7 cortes'), (430, 60, 'b2', 'VALID'), (490, 120, 'b3', 'TEST · 2')):
        c += f'<rect x="{x0}" y="276" width="{w}" height="40" class="{cl}"/>' + tx(x0 + w / 2, 301, t, 't3')
    c += tx(640, 296, 'El modelo se elige con VALID y se mide en TEST una sola vez.', 't2 izq')
    return dg(svg(W, H, c, 'Del archivo del negocio al modelo: operacional, RAW, MASTER, FS, ML, entrenamiento y MLflow, con la partición por fecha de corte', i))


def svg_s2():
    i = 's2'
    W, H = 1160, 372
    c = sh_modelo(10, 60, 150, 104, 'Modelo', '+ firma', '+ metadatos') + nodo(200, 60, 150, 104, 'Contrato', 'esquemas.py', t3='sale de la firma', c3='t3')
    c += nodo(390, 60, 170, 104, 'API FastAPI', '/salud · /listo', t3='/predecir', c2='t3', c3='t3')
    c += nodo(600, 60, 150, 104, 'Imagen Docker', 'sin root', t3='usuario 10001', c2='t3', c3='t3')
    c += nodo(790, 60, 150, 104, 'Contenedor', '-p · -v · -e', c2='t3')
    c += sh_usuario(1040, 100, 'Tú o tu programa')
    for a, b in ((162, 198), (352, 388), (562, 598), (752, 788), (942, 1000)):
        c += flecha(i, (a, 112), (b, 112))
    c += tx(280, 48, 'se comparan al arrancar', 'tg2')
    c += tx(475, 196, 'Cuatro respuestas, cuatro significados', 't1')
    for k, (cod, t, cl) in enumerate((('200', 'todo bien', 'ok'), ('422', 'se equivocó\nquien llama', 'aviso'), ('503', 'el servicio\nno está listo', 'aviso'), ('500', 'se equivocó\nel servicio', 'mal'))):
        x = 190 + k * 150
        c += nodo(x, 212, 140, 74, cod, t, cls=f'nodo {cl}', c2='t3')
    c += nodo(10, 306, 1140, 54, 'Comparar todos los caminos: el paquete, el joblib, el formato MLflow, la API y el contenedor', 'la diferencia debe ser cero', cls='nodo ok', c2='t3')
    return dg(svg(W, H, c, 'Del modelo guardado al servicio: contrato, API, imagen, contenedor y persona que consulta, con los códigos 200, 422, 503 y 500', i))


def svg_s3():
    i = 's3'
    W, H = 1160, 396
    c = zona(10, 4, 1140, 118, '1 · MLflow: de dónde sale el modelo (35 min)')
    fila = [(30, 190, 'Dos runs', 'regresión y boosting'), (270, 190, 'Comparar', 'coordenadas paralelas'), (770, 170, 'Firma', 'el contrato'), (980, 150, 'Cargar', 'desde Python')]
    for x, w, t1, t2 in fila:
        c += nodo(x, 50, w, 58, t1, t2, c2='t3')
    c += sh_modelo(510, 48, 220, 62, 'Modelo registrado', 'retencion-90d · versiones', c2='t3')
    for a, b in ((222, 268), (462, 508), (732, 768), (942, 978)):
        c += flecha(i, (a, 79), (b, 79))
    c += zona(10, 132, 1140, 118, '2 · GitHub Actions: romper y arreglar (70 min)')
    seq = [(30, 170, 'nodo', 'push', 'rama lab/actions-s3'), (236, 176, 'herr', 'Workflow', 'ejecuta pruebas'), (440, 110, 'nodo ok', 'Verde', 'la base'),
           (590, 150, 'nodo mal', 'Rojo', 'una prueba falla'), (790, 180, 'nodo', 'Leer el registro', 'primera caja roja'), (1000, 130, 'nodo ok', 'Verde', 'con arreglo')]
    for x, w, cl, t1, t2 in seq:
        c += (sh_herr(x, 178, w, 58, t1, t2, c2='t3') if cl == 'herr' else nodo(x, 178, w, 58, t1, t2, cls=cl, c2='t3'))
    for a, b in ((202, 234), (414, 438), (552, 588), (742, 788), (972, 998)):
        c += flecha(i, (a, 207), (b, 207))
    c += zona(10, 260, 1140, 128, '3 · Extra: red neuronal «¿perro o gato?» (20 min)')
    c += sh_datos(34, 296, 110, 82, 'Fotos') + sh_modelo(190, 300, 250, 70, 'MobileNetV3-small', 'congelada', c2='t3')
    c += nodo(486, 300, 220, 70, 'Regresión logística', 'se entrena encima', c2='t3') + nodo(752, 300, 180, 70, 'Runs en MLflow', c2='t3')
    c += nodo(978, 300, 150, 70, 'Predecir', 'una foto', c2='t3')
    for a, b in ((146, 188), (442, 484), (708, 750), (934, 976)):
        c += flecha(i, (a, 335), (b, 335))
    return dg(svg(W, H, c, 'Tres bloques de S3: MLflow, GitHub Actions con rojo y verde, y la red neuronal con transferencia', i))


def svg_s4():
    i = 's4'
    W, H = 1160, 412
    c = zona(10, 6, 500, 300, 'GitHub Actions') + visto(480, 28)
    c += nodo(28, 56, 130, 62, 'Pruebas', c2='t3') + nodo(176, 56, 130, 62, 'Imagen', 'se prueba', c2='t3') + sh_herr(324, 52, 166, 70, 'Aprobación', 'environment', c2='t3')
    c += flecha(i, (160, 87), (174, 87)) + flecha(i, (308, 87), (322, 87))
    c += sh_usuario(407, 178, 'Una persona revisa') + flecha(i, (407, 148), (407, 126))
    c += nodo(28, 236, 462, 62, 'Permisos mínimos y sin secretos', 'timeout en cada trabajo', cls='nodo puerta', c2='t3')
    c += nodo(540, 90, 130, 112, 'WIF', 'token OIDC', t3='sin claves', cls='nodo puerta', c2='t3', c3='t3')
    c += zona(700, 6, 450, 300, 'Google Cloud · southamerica-west1') + visto(1120, 28, medio=True)
    c += flecha(i, (492, 146), (538, 146)) + flecha(i, (672, 146), (718, 146))
    c += nodo(720, 56, 190, 74, 'Artifact Registry', 'la imagen', c2='t3') + nodo(940, 56, 190, 74, 'Cloud Run', 'URL pública', c2='t3')
    c += flecha(i, (912, 93), (938, 93))
    c += nodo(720, 160, 190, 66, 'Cuenta de servicio', 'la que despliega', c2='t3') + nodo(940, 160, 190, 66, 'Cuenta de servicio', 'la que ejecuta, sin roles', c2='t3')
    c += nodo(720, 240, 410, 52, 'Presupuesto con alertas: avisa, pero no corta', cls='nodo puerta', c2='t3')
    c += sh_obs(10, 326, 1140, 62, 'CREA → PRUEBA → BORRA', 'lo que creas, lo borras: pool de WIF, presupuesto, Cloud Run y Artifact Registry')
    return dg(svg(W, H, c, 'GitHub Actions entra en Google Cloud sin claves por federación de identidad, publica la imagen en Artifact Registry y despliega en Cloud Run con aprobación humana', i))


def svg_s5():
    i = 's5'
    W, H = 1160, 412
    c = zona(10, 6, 560, 398, 'Modelo en producción: se vigila y se deshace')
    c += sh_datos(30, 56, 120, 86, 'Datos', 'nuevos') + nodo(190, 56, 170, 86, 'PSI y KS', 'umbral 0,25', c2='t3') + nodo(400, 56, 150, 86, 'Alerta', 'run rojo + issue', cls='nodo mal', c2='t3')
    c += flecha(i, (152, 99), (188, 99)) + flecha(i, (362, 99), (398, 99))
    c += sh_modelo(30, 190, 150, 84, 'champion', 'alias → v1', c2='t3') + sh_modelo(262, 190, 140, 84, 'v2', 'candidata', c2='t3')
    c += nodo(442, 190, 108, 84, 'Puerta', 'de calidad', cls='nodo puerta', c2='t3')
    c += flecha(i, (404, 232), (440, 232)) + fl_g(i, (260, 262), (182, 262)) + tx(221, 288, 'volver', 'tc')
    c += fl_g(i, (182, 222), (260, 222)) + tx(221, 212, 'promover', 'tc')
    c += sh_obs(30, 330, 520, 60, 'El AUC se mide tarde', 'con datos de entrenamiento engaña')
    c += zona(600, 6, 550, 398, 'Agente: un LLM con herramientas')
    c += sh_usuario(662, 110, 'Pregunta') + sh_modelo(722, 58, 130, 88, 'LLM local', 'Ollama', c2='t3')
    c += flecha(i, (688, 100), (720, 100))
    c += sh_herr(890, 44, 240, 48, 'lista_del_dia', c2='t3') + sh_herr(890, 102, 240, 48, 'puntuar_online', c2='t3') + sh_herr(890, 160, 240, 48, 'version_en_produccion', c2='t3')
    c += flecha(i, (852, 102), (888, 70)) + flecha(i, (852, 102), (888, 126)) + flecha(i, (852, 102), (888, 184))
    c += sh_modelo(890, 232, 240, 72, 'Modelo de ML', '@champion decide', c2='t3')
    c += flecha(i, (1010, 210), (1010, 230))
    c += sh_obs(620, 232, 240, 72, 'Trazas en MLflow', '25 preguntas de oro')
    c += nodo(620, 326, 510, 64, 'El LLM orquesta y redacta; el modelo de ML decide', cls='nodo ok', c2='t3')
    return dg(svg(W, H, c, 'Monitoreo con PSI y alerta, alias champion con rollback, y un agente que usa herramientas MCP sobre el modelo', i))


def svg_salto():
    i = 'j'
    W, H = 1160, 470
    c = zona(10, 6, 1140, 192, 'En tu portátil o en tu Codespace') + zona(10, 214, 1140, 192, 'GitHub y la nube')
    fila1 = [('Datos', 'capas RAW → ML', 'S1', 'd'), ('Modelo', 'entrenado y registrado', 'S1', 'm'), ('API', 'FastAPI y contrato', 'S2', 'n'), ('Contenedor', 'imagen Docker,\nsin root', 'S2', 'n')]
    fila2 = [('CI/CD', 'pruebas, workflow\ny aprobación', 'S3 · S4', 'h'), ('Nube', 'Artifact Registry\ny Cloud Run', 'S4', 'c'), ('Monitoreo', 'deriva, alias\ny rollback', 'S5', 'o'), ('Agentes', 'LLM, herramientas\nMCP y evaluación', 'S5', 'm')]
    for fila, y in ((fila1, 44), (fila2, 252)):
        for k, (t1, t2, s, f) in enumerate(fila):
            x = 30 + k * 285
            t2w = t2
            if f == 'd':
                c += sh_datos(x, y, 220, 118, t1, t2w, c2='t3')
            elif f == 'm':
                c += sh_modelo(x, y, 220, 118, t1, t2w, c2='t3')
            elif f == 'h':
                c += sh_herr(x, y, 220, 118, t1, t2w, c2='t3')
            elif f == 'o':
                c += sh_obs(x, y, 220, 118, t1, t2w)
            elif f == 'c':
                c += nube(x - 6, y - 4, 232, 128) + centrado(x, y + 34, 220, 80, [(t1, 't1'), (t2w, 't3')])
            else:
                c += nodo(x, y, 220, 118, t1, t2w, c2='t3')
            c += (visto(x + 210, y + 4, medio=True) if t1 == 'Nube' else visto(x + 220, y + 6)) + tx(x + 110, y + 138, s, 'tg')
            if k < 3:
                c += flecha(i, (x + 224, y + 59), (x + 281, y + 59))
    c += f'<path d="M1077 103 L1118 103 L1118 205 L235 205 L235 248" class="fl" marker-end="url(#{i})"/>'
    c += sh_obs(10, 420, 1140, 40, 'Por debajo, siempre: Git · pruebas · MLflow · identidad sin claves · borrar lo creado')
    return dg(svg(W, H, c, 'De tu portátil a producción: datos, modelo, API, contenedor, CI/CD, nube, monitoreo y agentes, marcando qué has tocado tú', i))


def svg_entregas():
    i = 'e'
    W, H = 1160, 236
    xs = [110, 330, 550, 770, 1030]
    c = f'<path d="M20 52 L1140 52" class="fl" marker-end="url(#{i})"/>'
    c += f'<path d="M770 52 L1030 52" class="fl g" stroke-dasharray="3 7"/>' + tx(900, 40, '2 semanas', 'tg2')
    datos = [('mié 18/11', 'Tarea de S1\n+ Avance 1'), ('vie 20/11', 'Avance 2\n(Ruta B de S2)'), ('mié 25/11', 'Avance 3\n(tarea de S3)'), ('vie 27/11', 'Avance 4\n(tarea de S4)'), ('vie 11/12', 'ENTREGA FINAL\n(tarea de S5)')]
    for k, (cx, (f, t)) in enumerate(zip(xs, datos)):
        ult = k == 4
        c += f'<circle cx="{cx}" cy="52" r="{15 if ult else 11}" class="{"puntoo" if ult else "num"}"/>'
        c += f'<rect x="{cx - 104}" y="88" width="208" height="128" rx="14" class="{"nodo oro" if ult else "nodo"}"/>'
        c += tx(cx, 124, f, 't1') + tx(cx, 158, t, 't2')
        if ult:
            c += tx(cx, 202, '10:00 · hora de Perú', 'tg')
    return dg(svg(W, H, c, 'Línea de entregas: cuatro avances los días 18, 20, 25 y 27 de noviembre y la entrega final el 11 de diciembre a las 10:00 hora de Perú', i))


def svg_repo():
    i = 'r'
    W, H = 1160, 466
    c = tx(10, 28, f'{REPO_URL.split("/")[-1]}/', 't1 izq')
    cajas = [('00-Planificacion', 'programa, calendario,\ndecisiones y generadores', '', False),
             ('01-Sesiones', f'{N["sesiones"]} sesiones · {N["decks"]} presentaciones\n{N["guias"]} guías · {N["nb_ses"]} cuadernos', 'lo que has usado', False),
             ('02-Proyecto-Transversal', 'caso Bank Marketing: datos,\nhoja, plantilla y rúbrica de avance', '', False),
             ('03-Entorno', f'{N["guias_entorno"]} guías, Codespaces,\ninstalación y scripts', '', False),
             ('04-Proyecto-Base', f'paquete ia_mlops · {N["nb_base"]} cuadernos\n{N["tests_arch"]} archivos de pruebas', 'código para copiar', False),
             ('05-Modulo-Redes-Neuronales', 'reservada: todavía vacía', 'próximamente', True),
             ('06-Modulo-LLMs', 'módulo opcional:\nsolo el README por ahora', 'en preparación', True),
             ('07-Recursos', f'{N["guias_recursos"]} guías (Git, Miniconda,\nSQLite, VS Code) y fuentes', '', False),
             ('08-Evaluacion-Final', 'reservada: todavía vacía', 'por confirmar', True)]
    for k, (nom, desc, etq, vacia) in enumerate(cajas):
        x = 10 + (k % 3) * 384
        y = 44 + (k // 3) * 140
        c += f'<rect x="{x}" y="{y}" width="372" height="126" rx="14" class="{"nodo puerta" if vacia else "nodo"}"/>'
        c += f'<path d="M{x + 16} {y + 22} h18 l5 6 h20 v18 h-43 z" class="herr" style="stroke-width:1.4"/>'
        c += tx(x + 74, y + 40, nom, 't1 izq') + tx(x + 20, y + 76, desc, 't2 izq')
        if etq:
            c += tx(x + 356, y + 112, etq, 'tg3')
    return dg(svg(W, H, c, 'Estructura del repositorio: nueve carpetas, de la planificación a la evaluación final, con lo que hay en cada una', i))


def svg_escalera():
    i = 'z'
    W, H = 1160, 420
    pasos = [('1 · Entorno', 'Un entorno\nque se reproduce'), ('2 · Datos y modelo', 'Capas, variables\ny partición por tiempo'), ('3 · Servicio', 'API con contrato\ny contenedor'),
             ('4 · Automatización', 'Workflows:\nrojo → verde'), ('5 · Nube', 'Despliegue sin claves\ny borrar lo creado'), ('6 · Operación', 'Vigilar, versionar,\ndeshacer y agentes')]
    c = ''
    for k, (t, d) in enumerate(pasos):
        x = 10 + k * 190
        h = 110 + k * 46
        y = 390 - h
        c += f'<rect x="{x}" y="{y}" width="180" height="{h}" rx="10" class="esc esc{k}"/>'
        w = ' w' if k == 5 else ''
        c += tx(x + 90, y + 28, t, 'te1' + w) + tx(x + 90, y + 56, d, 'te3' + w)
    c += f'<path d="M1050 56 L1050 20 L1100 32 L1050 44" class="herr" style="stroke-width:2"/>' + tx(1050, 10, 'hoy', 'tg')
    return dg(svg(W, H, c, 'Escalera de seis peldaños, del entorno a la operación, con una bandera en el último', i))


# ----------------------------------------------------------------------------------------------------------------------
# Piezas de contenido reutilizables
# ----------------------------------------------------------------------------------------------------------------------
S0, S1, S2, S3, S4, S5 = [f'01-Sesiones/{c.name}' for c in carpetas_sesion()]
EN_PREPARACION = {'extra-composer-batch', 'extra-vertex-champion'}
CAL = {'S0': 'mié 11/11', 'S1': 'vie 13/11', 'S2': 'mié 18/11', 'S3': 'vie 20/11', 'S4': 'mié 25/11', 'S5': 'vie 27/11'}


def ya_sabes(filas):
    """Filas «Ya sabes: … → y lo has comprobado en: …» (el segundo elemento es HTML con las rutas)."""
    out = ''.join(f'<div class="ys"><div class="ys1"><span class="lb">Ya sabes</span><span class="yt">{md(a)}</span></div><div class="ysf" aria-hidden="true">→</div>'
                  f'<div class="ys2"><span class="lb">y lo has comprobado en</span>{b}</div></div>' for a, b in filas)
    return f'<div class="yss">{out}</div>'


def si_falla(filas, anecdota=''):
    t = tabla(['Lo que ves', 'Por qué pasa', 'Qué se hizo'], filas, 'falla-tbl')
    return t + f'<div class="calma"><b>Es normal.</b> {md(anecdota)}</div>'


def explicar(frase, extras):
    """Columna izquierda «ahora lo puedes explicar» y derecha «si quieres ir más allá»."""
    li = ''
    for r, estado, desc in extras:
        et = '' if estado == 'ok' else ' ' + tag(estado, 'warn')
        li += f'<li>{ruta(r)}{et}<span class="small"> {md(desc)}</span></li>'
    return (f'<div class="split2b2"><div class="col"><div class="explica"><span class="lb">Ahora lo puedes explicar a un compañero</span><p>{md(frase)}</p></div></div>'
            f'<div class="col"><h3>Y si quieres ir más allá</h3><ul class="mas">{li}</ul></div></div>')


# ----------------------------------------------------------------------------------------------------------------------
# 1 · Apertura
# ----------------------------------------------------------------------------------------------------------------------
def construir_apertura():
    cuerpo = ('<div class="cover"><div class="portada-izq"><p class="sub">De los datos al modelo, del modelo al servicio y del servicio a la nube. '
              'Seis sesiones, de S0 a S5, en una sola mirada.</p>'
              '<div class="chips">'
              f'<span class="chip">{N["sesiones"]} sesiones</span><span class="chip">22 h síncronas propuestas</span>'
              '<span class="chip">Un caso: ¿volverá a comprar en 90 días?</span><span class="chip">Capturas reales de tus laboratorios</span></div>'
              + msg('No es un examen: es un espejo. Mira todo lo que **ya sabes hacer**.') + '</div>' + svg_portada() + '</div>')
    slide('A', 1, 'Lo que ya sabes hacer', 'Recap final · ML e IA: de desarrollo a producción', 'Lo que ya sabes hacer', cuerpo,
          nota('Da la bienvenida y fija el tono: esto no es un examen, es un espejo. En una hora recorremos las seis sesiones, vemos lo que ya sabéis hacer y dejamos claro qué falta entregar y dónde queda todo el material.',
               'Al empezar, producción parecía otro mundo; en S3 pusisteis un workflow en rojo a propósito y lo devolvisteis al verde.',
               '¿Qué fue lo que más os sorprendió que fuera «normal» y no magia?'), 'portada')

    slide('A', 2, 'El viaje de un vistazo', 'Seis sesiones', 'El viaje de un vistazo: seis sesiones, un solo camino',
          svg_viaje() + '<p class="fte centro">Sesiones los miércoles y viernes, de 10:00 a 14:00 (hora de Perú). Fuente: 02-Proyecto-Transversal/alumno/tu-caso-bank-marketing.md, apartado 9.</p>',
          nota('Recorre la línea de izquierda a derecha con una frase por sesión: entorno, datos y modelo, servicio, pruebas que se ponen rojas y vuelven al verde, nube sin claves, y vigilancia con agentes. Es un único camino, no seis cursos.',
               'El caso de hilo es el mismo desde S1: ¿volverá este cliente a comprar en los próximos 90 días? Del cuaderno al contenedor, a la nube y a un agente que lo consulta.',
               '¿En qué sesión sentisteis que «ya no había vuelta atrás»?'))

    mitos = [('Un modelo es magia', 'Es una función que aprende de datos y variables. Tú construiste las capas RAW → ML y viste salir el modelo de las 13 variables.', 'S1'),
             ('Producción es otro mundo', 'Es el mismo código con pruebas, imagen, workflow y aprobación: lo montaste de S2 a S4.', 'S2 · S3 · S4'),
             ('Un LLM lo sabe todo, hasta mis datos', 'No sabe tus datos: se los das con herramientas (MCP). El modelo de ML sigue decidiendo.', 'S5'),
             ('La nube es una caja negra', 'Son piezas que se despliegan y se borran con un script: Artifact Registry, Cloud Run, identidad federada.', 'S4'),
             ('Si el pipeline se pone rojo, algo va mal conmigo', 'El rojo es información. En S3 rompiste una regla a propósito y la devolviste al verde sin borrar la prueba.', 'S3'),
             ('Desplegar es irreversible', 'Deshacer es mover un alias o restaurar una ficha: rollback sin borrar nada.', 'S4 · S5')]
    tarj = ''.join(f'<div class="mito"><button class="mbtn" aria-expanded="false"><span class="lb">Mito {k}</span><span class="mq">«{esc(m)}»</span><span class="pista">Pulsa para ver la realidad</span></button>'
                   f'<div class="real" hidden><span class="lb ok">Realidad</span><p>{md(r)}</p><span class="fte">Lo viste en {esc(s)}</span></div></div>' for k, (m, r, s) in enumerate(mitos, 1))
    slide('A', 2, 'Los mitos que hemos desmontado', 'Mito → realidad', 'Los mitos que hemos desmontado',
          f'<div class="mitos">{tarj}</div><div class="centro"><button class="btn" id="mitos-todos" aria-pressed="false">Mostrar todas las realidades</button></div>',
          nota('Pulsa cada tarjeta y pide al aula que adivine la realidad antes de mostrarla. Son solo los mitos que de verdad se trabajaron en el curso, cada uno con su sesión.',
               'Mito 5: en S3 el workflow se puso rojo con «Rotura a propósito: el tramo alta empieza en 0,75» y volvió al verde con un «Revert». El rojo no era un fallo vuestro: era el sistema funcionando.',
               '¿Qué otro mito tenías tú al empezar y ya no tienes?'))


# ----------------------------------------------------------------------------------------------------------------------
# 2 · Una sección por sesión
# ----------------------------------------------------------------------------------------------------------------------
def construir_s0():
    slide('0', 2, 'S0 · Qué hicimos en clase', 'Qué hicimos en clase', 'S0 · Un entorno que funciona en cualquier equipo',
          svg_s0() + '<p class="fte centro">S0, mié 11/11 (2 horas): Parte A de 25 min (objetivos, recorrido, caso y entregas), pausa de 15, Parte B de 70 (entorno) y cierre de 10. Fuente: 01-Sesiones/S0-Presentacion-y-Entorno/README.md.</p>',
          nota('S0 fue la sesión de «dejar el equipo listo»: Git, VS Code, Miniconda, SQLite, el repositorio, y un Codespace con Docker y kind para no instalar nada pesado en local. Cerró con un diagnóstico de 12 comprobaciones.',
               'Quien no pudo instalar algo en su equipo corporativo tenía la ruta del Codespace: el diagnóstico existía precisamente para detectarlo el primer día y no en S2.',
               '¿Qué fue lo que más costó instalar, y qué hiciste al final?'))
    slide('0', 1, 'S0 · Qué te llevas', 'Qué te llevas', 'S0 · Qué te llevas',
          '<div class="split2c"><div class="col">' + ya_sabes([
              ('Montar un **entorno reproducible** desde una receta (`environment.yml`).', ruta(f'{S0}/slides/instalacion', 'S0 · Tu equipo listo para S1')),
              ('Clonar un repositorio y **trabajar con ramas**.', ruta('07-Recursos/guias/git-y-ramas.md')),
              ('Abrir un **Codespace** con Docker sin instalar nada.', ruta('03-Entorno/guia-codespaces')),
              ('**Pedir ayuda bien**: comando, error completo y `verificacion-s1.txt`.', ruta(f'{S0}/practica/guia-rapida-entorno-s0-s1.md'))]) + '</div>'
          + cap('s0-codespaces-pestana.webp', 260) + '</div>',
          nota('Cuatro cosas que ya sabéis hacer sin pensar: montar el entorno desde una receta, clonar y usar ramas, abrir un Codespace y pedir ayuda con la información que de verdad hace falta (comando, error completo y el informe de verificación).',
               'La captura es la pestaña Codespaces del repositorio: la cuota de uso la paga quien lo crea, por eso la guía explica cómo parar y borrar el Codespace.',
               '¿Quién ha abierto un Codespace por su cuenta después de la clase?'))
    slide('0', 1, 'S0 · El momento difícil', 'El momento difícil y cómo se superó', 'S0 · El primer día, el entorno siempre rompe algo',
          si_falla([('`conda` no se reconoce', 'Terminal equivocada', 'Usar «Anaconda Prompt (Miniconda3)»'),
                    ('`ModuleNotFoundError`', 'Entorno o kernel equivocado', 'El prompt debe empezar por (env-ia-mlops); en un cuaderno, elegir ese kernel'),
                    ('Faltan carpetas del curso', 'Se clonó `main`', '`git fetch origin` y `git switch develop`')],
                   'Por eso existe el diagnóstico de 12 comprobaciones: encontrar el problema el primer día, con el mensaje exacto, y no en mitad de S2.'),
          nota('Normaliza el tropiezo: casi todos los errores del primer día son de terminal, entorno o rama, no de capacidad. La tabla sale de la guía rápida del entorno.',
               'Faltan carpetas del curso: pasó por clonar la rama principal, que no trae todo el material; la solución son dos comandos.',
               '¿Qué error del entorno te hizo perder más tiempo y cómo lo resolviste?'))
    slide('0', 1, 'S0 · Ahora lo puedes explicar', 'Ahora lo puedes explicar · ir más allá', 'S0 · Ahora lo puedes explicar',
          explicar('Un entorno es una receta que cualquiera puede reproducir; un Codespace es un ordenador de usar y tirar que ya trae Docker.',
                   [('03-Entorno/guia-codespaces', 'ok', 'guía con capturas reales: crear, parar y borrar'), ('03-Entorno/guia-instalacion', 'ok', 'instalación en Windows, con comandos para copiar'),
                    ('03-Entorno/guia-docker-kubernetes-gke', 'ok', 'Docker y Kubernetes sin instalación local'), (f'{S0}/slides/anexos', 'ok', 'anexos de consulta (estadísticas, herramientas, costes)')]),
          nota('Pide a alguien que lo cuente con sus palabras en diez segundos: «un entorno es una receta; un Codespace es un ordenador desechable». Luego enseña dónde están las guías por si hay que repetirlo en otro equipo.',
               'La guía de Codespaces se hizo con capturas reales del propio proceso: crear, esperar a que construya, abrir los puertos, parar.',
               '¿Qué le explicarías a un compañero nuevo que va a empezar el curso mañana?'))


def construir_s1():
    slide('1', 2, 'S1 · Qué hicimos en clase', 'Qué hicimos en clase', 'S1 · De los datos al modelo, capa a capa',
          svg_s1() + f'<p class="fte centro">Caso del instructor: Online Retail II ({n(1067371)} líneas de una tienda online, 2009–2011): ¿volverá este cliente a comprar en los próximos 90 días? Fuente: 04-Proyecto-Base/README.md.</p>',
          nota('S1 fue de los datos al modelo: una base operacional simulada, las capas RAW, MASTER, FS y ML (un cuaderno por capa y su traducción a .py), tres modelos comparados y MLflow para guardar cada intento.',
               'FS va antes que ML, y todos los filtros usan fecha_factura < :corte: así el modelo no ve el futuro. Hay una prueba, `pytest tests -k futuro`, que lo vigila.',
               '¿Por qué partimos por fecha de corte y no al azar?'))
    slide('1', 1, 'S1 · Lo que vimos', 'Lo que vimos en pantalla', 'S1 · El recorrido y la partición por tiempo',
          '<div class="caps2">' + cap('s1-recorrido.webp') + cap('s1-particiones.webp', 340) + '</div>',
          nota('Estas dos figuras son del proyecto base y las usasteis en el laboratorio: la primera es el recorrido completo; la segunda, cómo se reparten train, validación y test por fecha de corte.',
               'Siete cortes mensuales para entrenar, uno para comparar modelos y dos para el examen final: el modelo elegido se mide en test una sola vez.',
               '¿Qué pasaría si repartiéramos las filas al azar en lugar de por fecha?'))
    slide('1', 2, 'S1 · Qué te llevas', 'Qué te llevas', 'S1 · Qué te llevas',
          '<div class="split2c"><div class="col">' + ya_sabes([
              ('Reconstruir las **capas** con un cuaderno por capa y su traducción a `.py`.', ruta(f'{S1}/practica/guia-laboratorio.md') + ' ' + ruta('04-Proyecto-Base/notebooks')),
              ('**Evitar la fuga**: ningún filtro mira después del corte, y una prueba lo vigila.', ruta(f'{S1}/tarea/README.md')),
              ('**Partir por tiempo**, elegir con VALID y medir TEST una sola vez.', ruta('04-Proyecto-Base/ia_mlops/config.py')),
              ('**Registrar y comparar** ejecuciones en MLflow.', ruta(f'{S1}/practica/guia-laboratorio.md'))]) + '</div>'
          + cap('s1-mlflow.webp', 330) + '</div>',
          nota('Cuatro habilidades: capas con cuadernos y .py equivalentes, evitar la fuga con una prueba, partir por tiempo y registrar los intentos en MLflow. Y una más de la hoja del caso propio: en Bank Marketing, `duration` queda fuera del modelo.',
               f'En el caso propio (Bank Marketing, 41 188 filas y 21 columnas) la partición aleatoria es optimista y se dice así; en S5 el mismo modelo se evalúa por orden de filas.',
               '¿Cuál es la diferencia entre elegir un modelo con VALID y medirlo con TEST?'))
    slide('1', 1, 'S1 · El momento difícil', 'El momento difícil y cómo se superó', 'S1 · Un MLflow vacío no es un MLflow roto',
          si_falla([('MLflow abre, pero no hay ejecuciones', 'Abre en la vista GenAI (Traces, Prompts) o aún no se ejecutó el cuaderno 04 con `USAR_MLFLOW = True`', 'Elegir **Model training** y comprobar con `python -m ia_mlops.mlflow_ui --comprobar`'),
                    ('`No module named ia_mlops`', 'No estás en `04-Proyecto-Base`', '`cd 04-Proyecto-Base` y repetir'),
                    ('La prueba de equivalencia falla', 'Cuaderno y paquete difieren', 'Anotar el mensaje en las evidencias; no ocultarlo')],
                   'Pasó al preparar S1: la interfaz arrancaba sin ejecuciones ni modelos porque una ruta relativa creaba una base vacía en otro sitio.'),
          nota('Tranquiliza: un MLflow vacío casi siempre es un problema de dónde lo lanzas, no de lo que has hecho. La tabla es la de la guía del laboratorio de S1.',
               'Lo más honesto del curso: este fallo salió de verdad al preparar S1, y hoy el comando de la interfaz ya evita la ruta relativa.',
               '¿Qué mensaje de error te enseñó más de lo que esperabas?'))
    slide('1', 1, 'S1 · Ahora lo puedes explicar', 'Ahora lo puedes explicar · ir más allá', 'S1 · Ahora lo puedes explicar',
          explicar('Un modelo es una función que aprende de ejemplos del pasado; si le dejas ver el futuro al entrenar, el examen es una trampa.',
                   [('01-Sesiones/ejercicios/ejercicios-s1', 'ok', 'ejercicios con su solución y su traducción'), (f'{S1}/slides/caso-propio', 'ok', '«Tu caso de S1 a S5»: la hoja y las entregas'),
                    ('01-Sesiones/recap/recap-01', 'ok', 'recap de S1 y MLflow paso a paso'), ('02-Proyecto-Transversal/alumno/tu-caso-bank-marketing.md', 'ok', 'tu caso propio, con sus reglas')]),
          nota('La frase para contarlo: un modelo aprende del pasado; si ve el futuro al entrenar, la métrica miente. Es la trampa de datos más importante de todo el curso.',
               'En Bank Marketing la variable `duration` se conoce después de la llamada: usarla da un AUC precioso y un modelo inútil. Por eso queda fuera.',
               '¿Qué variable de tu trabajo diario «sabría» algo que en realidad aún no ha pasado?'))


def construir_s2():
    slide('2', 2, 'S2 · Qué hicimos en clase', 'Qué hicimos en clase', 'S2 · Del modelo guardado al servicio',
          svg_s2() + '<p class="fte centro">S2, mié 18/11. Fuente: 01-Sesiones/S2-API-y-Docker/README.md y 04-Proyecto-Base/docs/api-y-contenedor.md.</p>',
          nota('S2 convirtió el modelo guardado en un servicio: el contrato sale de la firma del modelo, la API distingue 200, 422, 503 y 500, la imagen corre sin root y se comparan las predicciones por todos los caminos.',
               'Un ticket medio de 5 000 libras cuando el modelo solo vio hasta 1 295 no se rechaza: se avisa, porque es posible pero no tiene respaldo.',
               '¿Por qué un 503 al arrancar es una buena noticia?'))
    slide('2', 1, 'S2 · Lo que vimos', 'Lo que vimos en pantalla', 'S2 · La API y la interfaz, vivas',
          '<div class="caps2s2">' + cap('s2-tres-terminales.webp') + cap('s2-interfaz-contenedor.webp', 380) + '</div>',
          nota('Aquí está todo funcionando: tres terminales con la API, la interfaz y los curl, y la interfaz servida por un contenedor que llama a la API por su nombre.',
               'La interfaz marca el aviso «antiguedad_dias fuera del rango visto al entrenar»: la predicción se da, pero sin respaldo.',
               '¿Qué diferencia hay entre /salud y /listo?'))
    slide('2', 2, 'S2 · Qué te llevas', 'Qué te llevas', 'S2 · Qué te llevas',
          '<div class="split2c"><div class="col">' + ya_sabes([
              ('Servir un modelo con **FastAPI** y un contrato de **13 variables** que sale de la firma.', ruta('04-Proyecto-Base/docs/api-y-contenedor.md')),
              ('Distinguir **200, 422, 503 y 500**; rechazar frente a avisar.', ruta(f'{S2}/teoria/README.md')),
              ('Construir una **imagen Docker** (826 MB en GitHub Actions) con usuario 10001, sin root.', ruta('04-Proyecto-Base/deploy/docker/Dockerfile')),
              ('**Comparar** las predicciones del paquete, el joblib, MLflow, la API y el contenedor.', ruta(f'{S2}/practica/guia-laboratorio.md'))]) + '</div>'
          + cap('s2-api-docs.webp', 330) + '</div>',
          nota('Cuatro habilidades de servicio: el contrato, los códigos de estado, la imagen mínima sin root y la comparación de caminos. La captura es la documentación automática de FastAPI.',
               'La imagen ocupa 826 MB en disco porque pesan pandas, scipy y scikit-learn; la cifra es de GitHub Actions, no de un Codespace.',
               '¿Por qué importa que el contenedor no corra como root?'))
    slide('2', 1, 'S2 · El momento difícil', 'El momento difícil y cómo se superó', 'S2 · Un 503 es la API diciendo la verdad',
          si_falla([('`/listo` da 503', 'El esquema o los metadatos no coinciden con la firma', 'Leer el `detalle`: es el diseño, no un fallo'),
                    ('`COPY failed … models/modelo_mlflow`', 'Falta entrenar antes de construir', '`python -m ia_mlops.pipeline` y luego `docker build`'),
                    ('El navegador no llega al contenedor', 'Falta `-p 8080:8080` o la API escucha en 127.0.0.1', 'Publicar el puerto; escuchar en 0.0.0.0')],
                   'La API no se cae ni da 500 cuando el contrato no cuadra: lo dice con el motivo exacto. Eso es lo que queremos en producción.'),
          nota('El 503 es un diseño: si el modelo y el contrato no coinciden, el servicio no finge estar listo. La tabla es la de la guía del laboratorio de S2.',
               'Al reentrenar con una variable nueva y no tocar la API, /listo responde 503 con «Faltan en la API: […]». Es lo esperado y es de lo que trataba la tarea.',
               '¿Preferirías un servicio que da 500 o uno que dice «no estoy listo y por qué»?'))
    slide('2', 1, 'S2 · Ahora lo puedes explicar', 'Ahora lo puedes explicar · ir más allá', 'S2 · Ahora lo puedes explicar',
          explicar('Una API es un contrato: dice qué acepta, qué rechaza y quién se equivocó.',
                   [(f'{S2}/contenedores', 'ok', 'dos presentaciones, guía práctica y laboratorio de roturas'), (f'{S2}/del-ordenador-al-servicio', 'ok', 'exponer el servicio: interfaz y dos contenedores'),
                    (f'{S2}/practica/laboratorio-extra-de-punta-a-punta.md', 'ok', 'de la ingesta a la explotación'), ('01-Sesiones/recap/recap-02', 'ok', 'recap de S2: del modelo guardado al servicio')]),
          nota('La frase: una API es un contrato con tres respuestas claras: acepto, rechazo porque te equivocaste, o no estoy listo. Todo lo demás es plomería.',
               'El laboratorio de roturas de contenedores y el extra de punta a punta están ahí para repetir con calma lo que fue denso.',
               '¿Qué endpoint de tu trabajo debería responder 422 en lugar de aceptar datos raros?'))


def construir_s3():
    slide('3', 2, 'S3 · Qué hicimos en clase', 'Qué hicimos en clase', 'S3 · Pruebas que se ponen rojas y vuelven al verde',
          svg_s3() + '<p class="fte centro">S3, vie 20/11: repaso del servicio de S2 (70 min), MLflow (35), GitHub Actions (70) y red neuronal (20). Fuente: 01-Sesiones/S3-Despliegue-y-Redes-Neuronales/README.md.</p>',
          nota('S3 cambió de plan el mismo día: la migración a GCP pasó a S4 y S3 se dedicó a tres laboratorios: MLflow (de dónde sale el modelo), GitHub Actions (romper y arreglar un workflow) y un extra con una red neuronal.',
               'El rojo del laboratorio de Actions no es un accidente: se rompe a propósito una prueba, se lee el registro y se arregla sin borrar la prueba.',
               '¿Qué os enseñó más: el verde del principio o el rojo del medio?'))
    slide('3', 1, 'S3 · Lo que vimos', 'Lo que vimos en pantalla', 'S3 · MLflow y el historial verde, rojo, verde',
          '<div class="caps2">' + cap('s3-mlflow-comparar.webp') + cap('s3-actions-historial.webp') + '</div>',
          nota('A la izquierda, la comparación de dos ejecuciones en MLflow; a la derecha, el historial de un workflow con tres runs: verde, rojo por una rotura a propósito y verde con un Revert.',
               'Fijaos en los tiempos: el rojo duró 51 segundos y el verde de después 1 minuto y 6 segundos. Un fallo tiene registro, causa y arreglo.',
               '¿Cómo reconoces la primera caja roja en un grafo con varios trabajos?'))
    slide('3', 2, 'S3 · Qué te llevas', 'Qué te llevas', 'S3 · Qué te llevas',
          ya_sabes([
              ('**Comparar ejecuciones** en MLflow y leer la firma y las versiones del modelo registrado.', ruta(f'{S3}/laboratorio-mlflow')),
              ('Leer un **workflow**, provocar un rojo con una prueba y devolver el verde **arreglando**, no borrando.', ruta(f'{S3}/laboratorio-github-actions')),
              ('Recorrer **interfaz → API → modelo** con las variables de FS calculadas al vuelo.', ruta(f'{S3}/laboratorio-recap-s2')),
              ('Explicar la **transferencia**: MobileNetV3-small congelada y una regresión logística encima.', ruta(f'{S3}/laboratorio-red-neuronal'))])
          + callout('**Cambio de plan, dicho claro.** La migración a GCP pasó a S4; en S3 solo se explicó de palabra y la tarea fue el avance 3: pruebas en Actions y la cuenta de Google Cloud activada.'),
          nota('Cuatro habilidades concretas, cada una con su laboratorio. Dilo con claridad: la migración a GCP no se hizo en S3, se hizo en S4.',
               'La red neuronal fue un extra: el entrenamiento y la predicción se hicieron en local; replicarlo es autoestudio.',
               '¿Qué parte del laboratorio de Actions volverías a hacer en tu repositorio?'))
    slide('3', 1, 'S3 · El momento difícil', 'El momento difícil y cómo se superó', 'S3 · «No aparece ningún run» le pasa a todo el mundo',
          si_falla([('No aparece ningún run', 'El archivo no está en `.github/workflows/`, la rama no empieza por `lab/` o Actions está desactivado en tu fork', 'Revisar ruta, rama y la pestaña Actions'),
                    ('El run falla sin llegar a los jobs', 'YAML mal sangrado (o con tabuladores)', 'Dos espacios por nivel; copiar desde la URL *raw*'),
                    ('Un job falla y los siguientes salen en gris', 'Con `needs:`, si uno falla, los que dependen de él no se ejecutan', 'Buscar la primera caja roja: ahí está el error')],
                   'El gris no es un error: es el sistema diciendo «no corro porque mi dependencia falló».'),
          nota('Tres tropiezos clásicos de Actions. La tabla es la del laboratorio: el 90 % de los «no pasa nada» es de ruta, rama o sangrado.',
               'En un fork, Actions suele venir desactivado: hay que activarlo desde la pestaña Actions.',
               '¿Qué te dijo el registro del paso rojo la primera vez que lo leíste?'))
    slide('3', 1, 'S3 · Ahora lo puedes explicar', 'Ahora lo puedes explicar · ir más allá', 'S3 · Ahora lo puedes explicar',
          explicar('Un workflow es una receta que GitHub ejecuta en una máquina nueva cada vez: si se pone rojo, es información, no un castigo.',
                   [(f'{S3}/laboratorio-red-neuronal', 'ok', 'extra: ¿perro o gato? con capturas; replicarlo es autoestudio'), (f'{S3}/laboratorio-github-actions/guia-pipeline-e2e.md', 'ok', 'el pipeline de punta a punta en Actions'),
                    (f'{S3}/preparar-gcp-para-s4.md', 'ok', 'activar Google Cloud con presupuesto y alertas'), (f'{S3}/practica/ensayo-local', 'ok', 'ensayo local de la migración (sin GCP)')]),
          nota('La frase: un workflow es una receta que corre en una máquina nueva; el rojo es información. Con esa idea, depurar deja de dar miedo.',
               'La hoja «preparar GCP para S4» insiste en crear antes un presupuesto con alertas: avisa, pero no corta el gasto.',
               '¿Qué pruebas de tu proyecto protegerían una regla que no debe romperse?'))


def construir_s4():
    slide('4', 2, 'S4 · Qué hicimos en clase', 'Qué hicimos en clase', 'S4 · Del repositorio a Google Cloud, sin una sola clave',
          svg_s4() + '<p class="fte centro">S4, mié 25/11. Cloud Journey se recorrió de verdad el 25/11/2026 con la cuenta del curso (fuente: 01-Sesiones/S4-Orquestacion-y-CI-CD/laboratorio-cloud-journey/guia.md). ◐ = con tu cuenta de Google Cloud o en demostración.</p>',
          nota('S4 unió dos mundos: el workflow de GitHub entra en Google Cloud con identidad federada, publica la imagen en Artifact Registry y despliega en Cloud Run con una persona que aprueba. Y al final todo se borra.',
               'Dos cuentas de servicio: una despliega (la usa GitHub) y otra ejecuta la API sin ningún permiso. Quien despliega no es quien ejecuta.',
               '¿Por qué es mejor un token de corta vida que una clave guardada?'))
    slide('4', 1, 'S4 · Lo que vimos', 'Lo que vimos en pantalla', 'S4 · La API ya vive en Cloud Run',
          '<div class="caps2">' + cap('s4-cloudrun.webp', 360) + cap('s4-artifact-registry.webp') + '</div>',
          nota('Dos pantallas de la consola de Google Cloud del recorrido real: el servicio en Cloud Run con sus métricas y la imagen en Artifact Registry.',
               'La región es southamerica-west1 (Santiago), la más cercana a Perú; las cuentas y el proyecto son de la cuenta del curso.',
               '¿Qué pieza del mapa de la nube os resulta ahora menos misteriosa?'))
    slide('4', 2, 'S4 · Qué te llevas', 'Qué te llevas', 'S4 · Qué te llevas',
          '<div class="split2c"><div class="col">' + ya_sabes([
              ('Orquestar un pipeline en **Actions**: trabajos con `needs:`, artefactos y permisos mínimos.', ruta(f'{S4}/laboratorio-produccion-e2e')),
              ('Entrar en Google Cloud **sin claves** (WIF), con tokens de corta vida.', ruta(f'{S4}/laboratorio-cloud-journey')),
              ('Publicar en **Artifact Registry** y desplegar en **Cloud Run** con aprobación humana.', ruta(f'{S4}/laboratorio-cloud-journey/desplegar-gcp.yml')),
              ('Sacar una **nueva versión con puerta de calidad** y volver atrás.', ruta(f'{S4}/laboratorio-produccion-e2e/nueva-version.yml'))]) + '</div>'
          + cap('s4-aprobacion.webp', 380) + '</div>',
          nota('Cuatro habilidades de entrega: orquestar, entrar sin claves, publicar con aprobación y versionar con puerta de calidad. La captura es el momento en que el run espera a una persona.',
               'El laboratorio de producción no usa Google Cloud: lo hicimos con GitHub y GHCR y lo comprobamos de verdad el 22/11/2026. Cloud Journey lo llevó a Google Cloud el 25/11.',
               '¿Qué cambia, para quien aprueba, entre confiar en un workflow y mirar antes de pulsar «Review deployments»?'))
    slide('4', 1, 'S4 · El momento difícil', 'El momento difícil y cómo se superó', 'S4 · «Publica sin pedir aprobación»',
          si_falla([('El job de publicar no espera aprobación', 'El *environment* no existe o no tiene revisores: GitHub lo crea sin revisores', 'Crearlo con el nombre exacto y con revisores'),
                    ('«Run workflow» no aparece', 'El workflow no está en la rama principal', 'Ensayar con un push a una rama `lab/…`'),
                    ('El run nuevo se queda en cola', 'Otro run del mismo grupo `concurrency` espera aprobación', 'Aprobar o cancelar el anterior')],
                   'Son «errores que pasaron de verdad» al preparar la sesión; por eso están escritos y por eso ahora los reconoces.'),
          nota('La tabla es la sección «Errores que pasaron de verdad» de la teoría de S4. La más importante: si el environment no existe, GitHub lo crea sin revisores y publica sin pedir permiso.',
               'Otro pequeño: un pool de identidad federada borrado se queda 30 días en estado DELETED y el script nuevo lo restaura.',
               '¿Qué comprobarías antes de confiar en que una aprobación realmente bloquea?'))
    slide('4', 1, 'S4 · Ahora lo puedes explicar', 'Ahora lo puedes explicar · ir más allá', 'S4 · Ahora lo puedes explicar',
          explicar('Un pipeline en producción es el mismo código con pruebas, imagen, workflow y una persona que aprueba: en la nube cambia dónde corre, no cómo se hace.',
                   [(f'{S4}/practicas-gcp', 'ok', 'cinco prácticas con CREA → PRUEBA → BORRA (Cloud Run, GKE, Dataproc, Vertex y Gemini)'), (f'{S4}/clase-onpremise-a-nube', 'ok', 'clase de apoyo: del on-premise a la nube'),
                    (f'{S4}/extra-estilo-llm', 'ok', 'extra opcional: un LLM que copia el estilo de color'), (f'{S4}/laboratorio-produccion-e2e', 'ok', 'lote, bajo demanda, online y rollback')]),
          nota('La frase: es el mismo código; cambia dónde corre. Y una regla de oro de la nube: lo que creas, lo borras.',
               'Las prácticas de GCP siguen CREA → PRUEBA → BORRA y avisan de qué cobra más si se olvida: el endpoint de Vertex y el clúster de GKE cobran por tiempo.',
               '¿Qué recurso de la nube olvidarías borrar con más facilidad?'))


def construir_s5():
    slide('5', 2, 'S5 · Qué hicimos en clase', 'Qué hicimos en clase', 'S5 · Un modelo en producción se vigila, se versiona y se deshace',
          svg_s5() + '<p class="fte centro">S5, vie 27/11. Fuente: 01-Sesiones/S5-MLOps-y-Operacion/laboratorio-mlops/guia.md y laboratorio-agentes/guia.md. El umbral de PSI 0,25 es una convención del oficio, no una ley.</p>',
          nota('S5 tiene dos mitades: MLOps clásico (deriva con PSI y KS, AUC por corte, alias champion, rollback y un workflow de monitoreo con alerta) y agentes (un LLM que usa herramientas MCP sobre el modelo en producción).',
               'El mensaje: la alerta es el rojo de un run y un issue. Sin él, nadie se entera de que los datos han cambiado.',
               '¿Qué te inquieta más de un modelo en producción: que se degrade o que nadie se entere?'))
    slide('5', 1, 'S5 · Lo que vimos', 'Lo que vimos en pantalla', 'S5 · La alerta de deriva, de verdad',
          '<div class="caps2">' + cap('s5-deriva-rojo.webp') + cap('s5-issue-alerta.webp') + '</div>',
          nota('Un run de monitoreo con dos trabajos en verde y la alerta en rojo, y el issue que abre el propio workflow con la tabla de variables que superan el umbral.',
               'El issue lo abrió github-actions con la etiqueta alerta-deriva; el ensayo se hizo en Actions el 26/11/2026 con una rama de ensayo.',
               '¿Quién debería enterarse de esta alerta en tu equipo, y por qué canal?'))
    slide('5', 2, 'S5 · Qué te llevas', 'Qué te llevas', 'S5 · Qué te llevas',
          '<div class="split2c"><div class="col">' + ya_sabes([
              ('Medir **deriva** (PSI y KS) y saber que el **rendimiento se mide tarde**.', ruta(f'{S5}/laboratorio-mlops')),
              ('**Versionar con un alias** (`champion`) y volver atrás moviéndolo.', ruta(f'{S5}/laboratorio-mlops/monitoreo.yml')),
              ('Explicar un **agente**: un LLM con herramientas MCP en un bucle.', ruta(f'{S5}/laboratorio-agentes')),
              ('**Evaluar** con 25 preguntas de oro, trazas y una puerta de calidad.', ruta(f'{S5}/laboratorio-agentes/guia.md'))]) + '</div>'
          + cap('s5-panel-asistente.webp', 440) + '</div>',
          nota('Cuatro habilidades: medir deriva, versionar con alias, explicar un agente y evaluarlo con datos. La captura es el panel con el LLM falso: enseña qué herramientas se llamaron y qué devolvieron, sin redactar.',
               'Cuidado con el sentido de la probabilidad: es la de VOLVER A COMPRAR en 90 días, no la de abandono. Un 80 % es un cliente que probablemente vuelva.',
               '¿Por qué evaluamos con preguntas de oro y no con la impresión de «parece que responde bien»?'))
    slide('5', 1, 'S5 · El momento difícil', 'El momento difícil y cómo se superó', 'S5 · Un número raro no siempre es un fallo',
          si_falla([('La deriva sale 1 con casi cualquier pareja de cortes', '`antiguedad_dias` siempre crece con el tiempo', 'Leerla como esperable; comparar con `--umbral-psi`'),
                    ('El LLM pequeño dice «sigue en riesgo»', 'Confunde recompra con abandono', 'El prompt y las descripciones de las herramientas importan; preguntas de prueba `m01`–`m03`'),
                    ('Publica sin pedir aprobación', 'El *environment* `produccion` no tiene revisores', 'Repetir la configuración del repositorio')],
                   'Interpretar es parte del trabajo: una alerta se lee con criterio, no se obedece a ciegas.'),
          nota('Tres casos reales de las guías de S5: una deriva «esperable», un LLM pequeño que confunde el sentido de la probabilidad y una aprobación que no bloqueaba.',
               'La antigüedad en días crece sola con el tiempo: por eso aparece en la tabla con un PSI muy alto y no significa que el negocio haya cambiado.',
               '¿Cómo distinguirías una deriva esperable de una deriva de comportamiento?'))
    slide('5', 1, 'S5 · Ahora lo puedes explicar', 'Ahora lo puedes explicar · ir más allá', 'S5 · Ahora lo puedes explicar',
          explicar('Un modelo en producción se vigila, se versiona y se puede deshacer; un agente es un sistema más: se prueba, se evalúa y se aprueba.',
                   [(f'{S5}/extra-mcp-notebooks', 'sin verificar', 'dos servidores MCP con notebooks; ejecutados en Windows, sin probar en Codespace ni con un LLM real'),
                    (f'{S5}/extra-destilacion-notebooks', 'sin verificar', 'destilación v1 y v2 en notebooks; ejecutados en CPU, sin probar en Windows ni en un Codespace'),
                    (f'{S5}/extra-rag-notebooks', 'sin verificar', 'RAG en notebooks con LLM local; ejecutados en CPU, sin probar en Windows ni en un Codespace'),
                    (f'{S5}/extra-composer-batch', 'en preparación', 'lote con Airflow en Cloud Composer; sin verificar en Google Cloud'),
                    (f'{S5}/extra-vertex-champion', 'en preparación', 'del alias champion a un endpoint de Vertex AI; sin verificar en Google Cloud'),
                    (f'{S5}/clase-fundamentos-ia-agentes', 'ok', '41 diapositivas con 12 capturas de la consola y un glosario')]),
          nota('La frase de cierre técnico: vigilar, versionar y poder deshacer. Y los extras: MCP, destilación y RAG ya disponibles aunque con partes sin verificar, dos en preparación (Composer y Vertex), y la clase de fundamentos de IA y agentes.',
               'Destilación y RAG se ejecutaron en CPU con las salidas guardadas; falta probarlos en Windows y en un Codespace. Composer y Vertex se probaron con simulaciones: lo dice su README. Hasta probarlos en Google Cloud real, están «en preparación».',
               '¿Qué extra te gustaría ver terminado primero?'))
# ----------------------------------------------------------------------------------------------------------------------
# 3 · El salto completo
# ----------------------------------------------------------------------------------------------------------------------
def construir_salto():
    slide('J', 3, 'De tu portátil a producción', 'El mapa completo', 'De tu portátil a producción: lo que has tocado tú',
          svg_salto() + '<p class="fte centro"><b>✓</b> lo has hecho en clase · <b>◐</b> con tu cuenta de Google Cloud o en demostración. Cada pieza tiene su sesión debajo.</p>',
          nota('Este es el dibujo que te llevas: ocho piezas, de los datos a los agentes. Las cuatro primeras viven en tu portátil o en un Codespace; las otras cuatro, en GitHub y en la nube. Lo que hay por debajo es lo que lo sostiene todo: Git, pruebas, MLflow, identidad sin claves y borrar lo creado.',
               'La nube lleva media marca a propósito: Cloud Journey se hizo con la cuenta del curso, y quien activó su cuenta (avance 3) pudo repetirlo por su cuenta.',
               '¿Qué pieza de este mapa te gustaría poder explicar con un dibujo en una pizarra?'))
    filas = [('«Producción» es un sitio aparte', 'Es un contenedor con tu modelo dentro: la misma imagen que probaste', f'S2 · {ruta("04-Proyecto-Base/deploy/docker/Dockerfile")}'),
             ('«Desplegar» es subir un archivo', 'Es un workflow con pruebas y una persona que aprueba', f'S4 · {ruta(S4 + "/laboratorio-produccion-e2e")}'),
             ('«Acceder a la nube» es pedir una clave', 'Es identidad federada: un token de corta vida, sin claves guardadas', f'S4 · {ruta(S4 + "/laboratorio-cloud-journey")}'),
             ('Un fallo es un desastre', 'Es un run rojo con registro, causa y arreglo', f'S3 · {ruta(S3 + "/laboratorio-github-actions")}'),
             ('Un modelo en producción se queda como está', 'Se vigila, se versiona con un alias y se puede deshacer', f'S5 · {ruta(S5 + "/laboratorio-mlops")}'),
             ('Un LLM en la empresa es una caja que responde', 'Es un sistema con herramientas, trazas y preguntas de oro', f'S5 · {ruta(S5 + "/laboratorio-agentes")}')]
    slide('J', 2, 'De desarrollo a producción', 'Lo que antes parecía otro mundo', 'De desarrollo a producción: lo que antes parecía otro mundo',
          tabla(['Antes parecía…', 'Ahora sabes que…', 'Lo comprobaste en'], [[f'!<span class="tachado">{esc(a)}</span>', f'!<b>{esc(b)}</b>', f'!{c}'] for a, b, c in filas], 'antes'),
          nota('Seis frases que cambian de significado. Antes eran «cosas de otro equipo»; ahora son una imagen, un workflow, un token, un registro, un alias y un conjunto de preguntas de oro.',
               'Un detalle que lo resume: nadie guardó una clave en el repositorio para llegar a Google Cloud, y aun así el despliegue funcionó.',
               '¿Cuál de estas seis frases le cambiarías hoy a un compañero que aún cree la de la izquierda?'))
    eq = [('Imagen en GHCR (`ghcr.io`)', 'Artifact Registry', tag('hecho en S4', 'ok') + ' <span class="small">Cloud Journey, 25/11/2026</span>'),
          ('La API en tu equipo o en el Codespace', 'Cloud Run (URL pública)', tag('hecho en S4', 'ok') + ' <span class="small">Cloud Journey, 25/11/2026</span>'),
          ('Una clave JSON de cuenta de servicio', 'Workload Identity Federation: sin claves', tag('hecho en S4', 'ok') + ' <span class="small">la organización del curso las prohíbe</span>'),
          ('`data/` en disco', 'Cloud Storage', tag('probado', 'ok') + ' <span class="small">práctica 03 de S4 (el bucket de Dataproc)</span>'),
          ('Spark o pandas en local', 'Dataproc sin servidor', tag('probado', 'ok') + ' <span class="small">práctica 03; probado el 25/11/2026 en Santiago</span>'),
          ('MLflow local y el modelo en una carpeta', 'Vertex AI: registro y endpoint', tag('comprobado', 'ok') + ' <span class="small">el contenedor predefinido devuelve la clase, no la probabilidad</span>'),
          ('Docker y kind en el Codespace', 'GKE Autopilot', tag('sin verificar', 'warn') + ' <span class="small">región de Santiago sin verificar</span>'),
          ('SQLite con las capas raw, master, fs y ml', 'BigQuery', tag('explicado', 'warn') + ' <span class="small">probado en Cloud Shell en el extra de MCP</span>')]
    slide('J', 2, 'Llevar a un hiperescalar', 'On-premise → Google Cloud', 'Llevar a un hiperescalar: tu equivalencia on-premise → GCP',
          tabla(['En el curso (on-premise simulado)', 'En Google Cloud', 'Estado'], [[a, f'!<b>{esc(b)}</b>', f'!{c}'] for a, b, c in eq], 'equiv')
          + '<p class="fte">Fuentes: 01-Sesiones/S4-Orquestacion-y-CI-CD/laboratorio-cloud-journey/guia.md y practicas-gcp/README.md. No se citan precios ni cuotas: «consulta la página oficial».</p>',
          nota('Una tabla corta y veraz: cada pieza que construisteis en local tiene su equivalente en Google Cloud. Lo marcado como hecho se ejecutó de verdad; lo marcado como sin verificar o explicado, no.',
               'En Cloud Journey el contenedor ya traía el modelo dentro; en Vertex, el contenedor predefinido devuelve la clase y no la probabilidad, así que comparamos distinto.',
               'Si mañana tuvieras que llevar un servicio tuyo a un hiperescalar, ¿por cuál de estas filas empezarías?'))


# ----------------------------------------------------------------------------------------------------------------------
# 4 · Consejos prácticos
# ----------------------------------------------------------------------------------------------------------------------
def consejo(titulo, texto, visto):
    return f'<div class="card cons"><h3>{md(titulo)}</h3><p class="small">{md(texto)}</p><span class="fte">Lo viste en: {esc(visto)}</span></div>'


def construir_consejos():
    slide('K', 1, 'Hábitos de ingeniería', 'Para empezar a trabajar de verdad', 'Seis hábitos de ingeniería que ya practicaste',
          grid(3, consejo('Versiona todo', 'Código, datos con su huella, modelo e imagen: lo que no está versionado no se puede reproducir ni deshacer.', 'S1 (huellas) y S5 (alias)'),
               consejo('Empieza pequeño y automatiza', 'Una muestra, una prueba y un workflow antes que la gran arquitectura.', 'S3'),
               consejo('Mide antes de desplegar', 'Escribe la puerta de calidad antes de ver el resultado, y mide en prueba, no en entrenamiento.', 'S4 y S5'),
               consejo('Ten siempre un rollback', 'Un alias o una ficha se mueve; no se borra nada. Si no puedes deshacerlo, no lo despliegues.', 'S4 y S5'),
               consejo('Documenta y deja evidencias', 'Enlaces a ejecuciones, no solo capturas: otra persona debe poder reproducirlo.', 'las tareas de S3 a S5'),
               consejo('Pide revisión', 'Pull request y aprobación humana antes de producción: dos pares de ojos.', 'S4'))
          + callout('**Sin sermones:** son los mismos pasos que ya diste. La diferencia es hacerlos a propósito.'),
          nota('Seis hábitos, todos ya practicados. No son reglas nuevas: son lo que hicisteis en los laboratorios, dicho como costumbre.',
               'En la tarea de S3, el rojo debía venir de una prueba que falla, no de un error de YAML: medir antes de desplegar empieza por una prueba que proteja una regla.',
               '¿Cuál de estos hábitos aplicarías mañana en tu equipo, sin pedir permiso a nadie?'))
    slide('K', 1, 'Seguridad, coste y criterio', 'Para empezar a trabajar de verdad', 'Seis hábitos de seguridad, coste y criterio',
          grid(3, consejo('No copies claves', 'Identidad federada: tokens de corta vida en lugar de claves guardadas. Ni claves, ni tokens, ni .env en el repositorio.', 'S4 (WIF)'),
               consejo('Vigila los costes', 'Presupuesto con alertas antes de crear nada: avisa, pero no corta. Y lo que creas, lo borras.', 'S4 y S5'),
               consejo('Pregunta antes de sacar datos', 'Consulta a seguridad y cumplimiento antes de mover datos del banco; nada de datos de clientes en registros ni capturas.', 'la rúbrica de S5'),
               consejo('Los LLM se evalúan', 'Preguntas de oro, trazas y una puerta de calidad: se evalúa con datos, no con impresiones.', 'S5'),
               consejo('Di lo que no pudiste', 'Con el error exacto. Declararlo no resta; fingirlo, sí.', 'las tareas'),
               consejo('Mide con honestidad', 'Partición por tiempo, sin variables que miran al futuro, y di cuándo una cifra es optimista.', 'S1 y la hoja del caso'))
          + callout('**La realidad no es un laboratorio ordenado:** por eso conviene entrar con costumbres seguras y reversibles.'),
          nota('Seis hábitos de criterio: seguridad, coste, datos y honestidad. Los dos más importantes en un banco: no mover datos sin preguntar y no guardar claves.',
               'La rúbrica de S5 limita la nota si hay datos de clientes en los registros o recursos de nube sin borrar y sin presupuesto previo: lo propone el profesor y está por confirmar.',
               '¿Qué dato de tu trabajo nunca pondrías en una captura de pantalla?'))
    recursos = [('07-Recursos/guias', 'Git y ramas, Miniconda, SQLite y VS Code'), ('03-Entorno/guias', 'Codespaces, Docker y Kubernetes, SDK de Google Cloud (borrador)'),
                ('04-Proyecto-Base/docs', 'del cuaderno a Python, API y contenedor, MLOps clásico, modelo de datos'), (f'{S4}/practicas-gcp', 'cinco prácticas con crear, probar y borrar'),
                (f'{S5}/clase-fundamentos-ia-agentes', 'IA, LLM, RAG y agentes, con glosario.md'), ('01-Sesiones/recap', 'recap-01 y recap-02, como este')]
    li = ''.join(f'<li>{ruta(r)}<span class="small"> {md(d)}</span></li>' for r, d in recursos)
    slide('K', 2, 'Cómo seguir aprendiendo', 'Con lo que ya tienes en el repositorio', 'Cómo seguir aprendiendo',
          f'<div class="split2b2"><div class="col"><h3>En el repositorio</h3><ul class="mas">{li}</ul></div>'
          '<div class="col"><h3>Una ruta de tres pasos</h3>'
          '<div class="paso2"><b>1</b><span>Haz un **fork** y rehaz el caso con una variable tuya.</span></div>'
          '<div class="paso2"><b>2</b><span>**Cambia una sola cosa y mide** con una puerta de calidad.</span></div>'
          '<div class="paso2"><b>3</b><span>Lleva tu caso a un **workflow** y, si puedes, a la nube… y **bórralo**.</span></div></div></div>',
          nota('El repositorio es tu biblioteca: guías de entorno, documentos del proyecto base, prácticas de GCP y la clase de fundamentos de IA y agentes con su glosario. Y una ruta de tres pasos para no perderse.',
               'El fork es tuyo: ahí Actions suele venir desactivado y hay que activarlo; es un buen primer paso para aprender.',
               '¿Cuál de los tres pasos darías esta semana?'))


# ----------------------------------------------------------------------------------------------------------------------
# 5 · Qué hacer ahora y evaluación (lo más importante)
# ----------------------------------------------------------------------------------------------------------------------
def construir_entrega():
    slide('E', 2, 'Qué hacer ahora', 'Lo que cuenta para tu nota', 'Qué hacer ahora: enviar y subir',
          '<div class="bandera"><b>Para la nota final del curso hay que ENVIAR lo solicitado en la tarea y SUBIRLO al CLASSROOM.</b></div>'
          + svg_entregas()
          + '<p class="fte centro">Fechas del calendario del repositorio; los avances se entregan a las 10:00 (hora de Perú) del día de la sesión en que se presentan. Fuente: 02-Proyecto-Transversal/alumno/tu-caso-bank-marketing.md, apartado 9.</p>',
          nota('Este es el mensaje que no puede perderse: para la nota final hay que enviar lo que pide cada tarea y subirlo al Classroom. La línea muestra las fechas: cuatro avances y la entrega final del viernes 11 de diciembre a las 10:00, hora de Perú.',
               'Entre S2 y S3 y entre S4 y S5 solo hay dos días: por eso los avances 2 y 4 conviene empezarlos en cuanto termina la sesión.',
               '¿Qué avance tienes ya entregado y cuál te falta?'))
    filas = [('Tarea de S1 (Online Retail II)', '`tarea-s1`', 'una variable nueva en FS, comparación de dos ejecuciones en MLflow, decisión escrita y la traducción a `.py`', 'plantilla-decision.md', f'{S1}/evidencias/plantilla-decision.md'),
             ('Avance 1 (Bank Marketing)', '`avance-1`', 'capas RAW → MASTER → FS → ML, entrenamiento y métricas, como cuadernos', 'plantilla-avance.md', '02-Proyecto-Transversal/alumno/plantilla-avance.md'),
             ('Avance 2 (= Ruta B de la tarea de S2)', '`avance-2` (la tarea de S2 dice `tarea-s2`)', 'pipeline en Python, API, contenedor y pruebas', 'plantilla-api-y-contenedor.md', f'{S2}/evidencias/plantilla-api-y-contenedor.md'),
             ('Avance 3 (= tarea de S3)', '`avance-3`', 'workflow que ejecuta tus pruebas, rojo → verde con enlaces, y cuenta de Google Cloud activada', 'plantilla-avance-3.md', f'{S3}/evidencias/plantilla-avance-3.md'),
             ('Avance 4 (= tarea de S4)', '`avance-4`', 'pipeline orquestado en Actions: etapas, al menos dos trabajos con `needs:`, historial y una decisión', 'plantilla-avance-4.md', f'{S4}/evidencias/plantilla-avance-4.md'),
             ('ENTREGA FINAL (= tarea de S5)', '`avance-5`', 'repositorio consolidado, workflows en verde con enlaces, nueva versión con puerta, aprobación y rollback, deriva o monitoreo, informe de 3 a 5 páginas y demostración', 'plantilla-avance-5.md', f'{S5}/evidencias/plantilla-avance-5.md')]
    cuerpo = tabla(['Entrega', 'Rama', 'Qué lleva', 'Plantilla de evidencia'],
                   [[a, b, c, f'!{ruta(r, d)}'] for a, b, c, d, r in filas], 'entr')
    cuerpo += (f'<div class="calma"><b>Cada entrega se evalúa con su rúbrica</b> ({ruta(S1 + "/tarea/rubrica.md", "tarea/rubrica.md")} de cada sesión): 20 % reproducibilidad, 40 % técnica y 40 % análisis y decisión '
               + tag('propuesta', 'warn') + '. El peso de cada avance en la nota final y la rúbrica de la entrega final están ' + tag('por confirmar', 'warn') + '.</div>')
    slide('E', 2, 'Qué se entrega, tarea a tarea', 'Lo que pide cada tarea', 'Qué se entrega, tarea a tarea', cuerpo,
          nota('Una fila por entrega: la rama, lo que lleva y la plantilla de evidencia que hay que completar. No inventamos pesos: las rúbricas proponen 20/40/40 y el peso de cada avance en la nota final está por confirmar.',
               'La tarea de S2 dice rama `tarea-s2` y la hoja del caso dice `avance-2`: es una incoherencia del repositorio que el profesor debe aclarar.',
               '¿Qué plantilla te ha costado más rellenar y por qué?'))
    casillas = ['Mi rama `avance-5` está subida y la última ejecución es verde.',
                'El README permite reproducirlo desde una copia limpia: pregunta, estructura, versiones y comandos en orden.',
                'Cité la fuente del dato (Moro, Rita y Cortez, 2014; CC BY 4.0) y `duration` queda fuera del modelo.',
                'Cada ejecución que cito lleva su enlace: una captura sin enlace no la demuestra.',
                'Hay una nueva versión con puerta de calidad escrita antes del resultado, aprobación humana y rollback.',
                'Añadí la comprobación de deriva o de monitoreo, con un umbral que justifico.',
                'Sin secretos: ni claves, ni tokens, ni `.env`, ni mi correo, ni el ID de mi proyecto.',
                'Borré lo creado en la nube (o escribí «ninguno») y anoté lo que no pude ejecutar, con el error exacto.',
                'Lo subí al Classroom antes del viernes 11/12/2026, 10:00 (hora de Perú).']
    chk = ''.join(f'<label class="chk"><input type="checkbox"><span class="caja" aria-hidden="true"></span><span>{md(c)}</span></label>' for c in casillas)
    slide('E', 2, 'Checklist de entrega', 'Antes de pulsar «entregar»', 'Checklist de la entrega final',
          '<div class="split2d"><div class="col"><div class="chks" role="group" aria-label="Checklist de entrega">' + chk + '</div>'
          f'<p class="small cuenta"><b id="chk-n">0</b> de {len(casillas)} marcadas · las casillas no se guardan</p></div>'
          '<div class="col"><div class="pendiente"><h3>Por confirmar por el profesor</h3>' + lista([
              'El peso de cada avance en la nota final y la rúbrica de la entrega final.',
              'Dónde y cómo se hace la demostración: vídeo corto (orientativo, unos 5 minutos) o sesión en vivo.',
              'El canal exacto de entrega: el Classroom (como se pide aquí) o el formulario de Google del curso que citan las tareas.']) + '</div>'
          + callout('Si algo no lo pudiste hacer, **cuéntalo con el error exacto**: declararlo no resta; fingirlo, sí.') + '</div></div>',
          nota('Usad la lista para repasar en voz alta: no se guarda nada, es para vosotros. Las nueve casillas salen de la tarea y de la rúbrica de la entrega final.',
               'Una captura sin enlace no demuestra una ejecución: por eso cada ejecución citada lleva su enlace. Y «ninguno» es una respuesta válida para los recursos de nube.',
               '¿Qué casilla sueles dejar para el último minuto?'))
    slide('E', 1, 'Sube tu tarea al Classroom', 'El mensaje', 'Sube tu tarea al Classroom',
          '<div class="solo"><p class="solo1">Sube tu tarea al <span>Classroom</span></p>'
          '<p class="solo2">Para la nota final del curso hay que <b>enviar lo solicitado en la tarea</b> y <b>subirlo al Classroom</b>.</p>'
          '<p class="solo3"><span class="chip grande">Entrega final: viernes 11/12/2026 · 10:00 (hora de Perú)</span></p></div>',
          nota('Una sola idea, repetida despacio: enviar lo que pide la tarea y subirlo al Classroom. La entrega final es el viernes 11 de diciembre de 2026 a las 10:00, hora de Perú.',
               'El rojo, el error exacto y lo que no pudiste hacer también se entregan: no restan, y suman honestidad.',
               '¿Alguien tiene alguna duda sobre dónde o cómo subir su entrega?'), 'slide-solo')


# ----------------------------------------------------------------------------------------------------------------------
# 6 · Te llevas un repositorio
# ----------------------------------------------------------------------------------------------------------------------
def tabs_sesiones():
    nombres = {'S0': 'Presentación y entorno', 'S1': 'Datos y entrenamiento', 'S2': 'API y Docker', 'S3': 'Despliegue y redes neuronales', 'S4': 'Orquestación y CI/CD', 'S5': 'MLOps y operación'}
    bt, pn = '', ''
    for k, c in enumerate(carpetas_sesion()):
        s = c.name.split('-')[0]
        d = POR[s]
        chips = ''.join(f'<span class="chip peq">{esc(x)}</span>' + (' ' + tag('en preparación', 'warn') if x in EN_PREPARACION else '') for x in d['lista'])
        bt += f'<button role="tab" id="tab-{s}" class="tab" aria-selected="{"true" if k == 0 else "false"}" aria-controls="pan-{s}" tabindex="{0 if k == 0 else -1}">{s}</button>'
        pn += (f'<div role="tabpanel" id="pan-{s}" class="tpan" aria-labelledby="tab-{s}"{"" if k == 0 else " hidden"}>'
               f'<h3>{s} · {nombres[s]} <span class="small">({CAL[s]})</span></h3>'
               f'<div class="mini"><div><b>{d["decks"]}</b>presentaciones</div><div><b>{d["guias"]}</b>guías</div><div><b>{d["yml"]}</b>workflows</div><div><b>{d["nb"]}</b>cuadernos</div></div>'
               f'<p class="small">Presentaciones HTML de la sesión (carpeta dentro de {S0.split("/")[0]}/{c.name}):</p><div class="chips">{chips}</div></div>')
    return f'<div class="tabs" role="tablist" aria-label="Sesiones">{bt}</div>{pn}'


def construir_repo():
    slide('R', 1, 'Te llevas un repositorio', 'Estructura real', 'Te llevas un repositorio completo',
          svg_repo() + '<p class="fte centro">Recuentos hechos con glob sobre el repositorio al generar esta presentación. Las carpetas de trazo discontinuo están reservadas o en preparación.</p>',
          nota('El repositorio tiene nueve carpetas con un orden: planificación, sesiones, proyecto transversal, entorno, proyecto base, dos módulos opcionales, recursos y evaluación final. Las que están a trazos todavía no tienen contenido y lo decimos tal cual.',
               'La carpeta 04 es la que más vas a copiar: es un paquete Python con cuadernos, pruebas, Dockerfile y plantilla de CI.',
               '¿Qué carpeta abrirías primero si empezaras un proyecto tuyo mañana?'))
    t = N
    chips = ''.join(f'<span class="chip">{b} {a}</span>' for a, b in (('sesiones', t['sesiones']), ('presentaciones', t['decks']), ('guías paso a paso', t['guias']), ('cuadernos', t['nb']),
                                                                    ('workflows de ejemplo', t['yml']), ('archivos de pruebas', t['tests_arch']), ('tareas con rúbrica', t['tareas'])))
    slide('R', 1, 'Organizado, con ejemplos para copiar', 'Un repositorio hecho para reproducir', 'Organizado, con ejemplos para copiar y reproducir',
          f'<div class="chips grande">{chips}</div>' + tabs_sesiones()
          + f'<p class="fte">Contados con glob: presentaciones = index.html dentro de cada sesión (sin la interfaz web); guías = archivos guia*.md; cuadernos = *.ipynb de 01-Sesiones y de 04-Proyecto-Base; '
            f'workflows = *.yml de 01-Sesiones, de 04-Proyecto-Base/deploy/github-actions y de .github/workflows; pruebas = test_*.py de 04-Proyecto-Base/tests ({t["tests_def"]} funciones <span class="mono">def test_</span>, sin ejecutar).</p>',
          nota('Los números son recuentos reales, no estimaciones: cada pestaña enseña lo que hay en cada sesión. Algunas presentaciones son de extras que aún están en preparación y se marcan así.',
               'No ejecutamos la suite entera para esta presentación: las pruebas se cuentan por archivo y por función, no por resultado.',
               '¿En qué sesión crees que hay más material para repetir por tu cuenta?'))
    slide('R', 1, 'Un repositorio vivo', 'El compromiso y cómo enterarte', 'Un repositorio vivo, y tuyo',
          msg('El repositorio se mantiene **actualizado constantemente**, con **más tareas y más extras** en cada tema.')
          + '<div class="split2b2"><div class="col"><h3>Cómo enterarte de las novedades</h3>'
            f'<div class="term"><div class="bar"><em>Terminal</em></div><pre class="src">git clone {REPO_URL}.git\ngit switch develop\ngit pull</pre></div>'
            + lista(['`git pull` trae lo nuevo; `git switch develop` es la rama con todo el material, según la guía de S0.', 'El **índice de cada sesión** (`index.html`) dice qué hay y qué falta.']) + '</div>'
            '<div class="col"><h3>Tu repo es tuyo</h3>' + lista(['**Haz un fork** y practica sin miedo a romper nada.', 'Rehaz un laboratorio cambiando **una sola cosa**.', 'Sigue con tu caso: pruebas, workflow y, si puedes, la nube.'])
            + f'<p class="small">Repositorio del curso: <a href="{REPO_URL}" target="_blank" rel="noopener">{REPO_URL}</a></p></div></div>',
          nota('El compromiso del profesor: el repositorio se mantiene actualizado constantemente, con más tareas y más extras en cada tema. Para enterarte: git pull y el índice de cada sesión, que dice qué hay y qué falta.',
               'Hoy ya hay extras en preparación (Composer y Vertex): irán llegando. Y cuando una guía cambie, el índice y las pruebas lo reflejan.',
               '¿Qué tema te gustaría que tuviera más ejercicios?'))


# ----------------------------------------------------------------------------------------------------------------------
# 7 · Cierre
# ----------------------------------------------------------------------------------------------------------------------
def construir_cierre():
    slide('Z', 2, 'De dónde partías y dónde estás', 'Seis peldaños', 'De dónde partías y dónde estás',
          svg_escalera() + '<p class="fte centro">Niveles cualitativos, sin puntuaciones: cada peldaño es algo que hiciste en un laboratorio.</p>',
          nota('Una escalera, no un examen: seis peldaños que son seis cosas que ya sabes hacer. No hay números porque no los hemos medido; hay laboratorios que lo demuestran.',
               'Arriba del todo, la bandera: operar es cuidar lo que ya está en producción, no solo construir.',
               '¿En qué peldaño te sientes más seguro y en cuál todavía tienes dudas?'))
    parrafos = ['Empezaste con una pregunta sencilla, «¿volverá este cliente a comprar en 90 días?», y la llevaste por un camino que casi nadie ve entero: capas de datos, un modelo, una API, un contenedor, un workflow, la nube y un agente.',
                'Nada de eso era magia. Era oficio: pasos pequeños, probados, reversibles y con evidencias.',
                'La realidad no se parece a un laboratorio ordenado, y está bien. Ahora tienes un repositorio, un vocabulario común y la certeza de que un rojo se lee, se arregla y vuelve a verde.',
                'No tengas miedo de empezar pequeño. Estas seis sesiones son la base: lo demás se aprende trabajando.']
    slide('Z', 2, 'Un mensaje final', 'Del profesor', 'Un mensaje final',
          '<div class="carta">' + ''.join(f'<p>{esc(p)}</p>' for p in parrafos) + '<p class="firma">Tu profesor</p></div>',
          nota('Léelo despacio o dilo con tus palabras. La idea: el miedo a la realidad se quita haciendo cosas pequeñas, probadas y reversibles, y eso es lo que habéis hecho durante seis sesiones.',
               'Cierra con algo personal tuyo: una vez que algo te salió mal en producción y qué hiciste después.',
               '¿Qué vas a hacer esta semana, en una hora, que antes te parecía de otro mundo?'))
    nom = {'S0': 'Presentación y entorno', 'S1': 'Datos y entrenamiento', 'S2': 'API y Docker', 'S3': 'Despliegue y redes neuronales', 'S4': 'Orquestación y CI/CD', 'S5': 'MLOps y operación'}
    enl = ''.join(f'<a class="enl" href="../../{c.name}/index.html">{c.name.split("-")[0]} · {nom[c.name.split("-")[0]]}</a>' for c in carpetas_sesion())
    slide('Z', 1, 'Gracias', 'Y ahora, a trabajar', 'Y ahora, a trabajar',
          '<div class="gracias"><p class="g1">Gracias por estas seis sesiones.</p>'
          '<div class="split2b2"><div class="col"><h3>Índices de cada sesión</h3><div class="enls">' + enl + '</div></div>'
          f'<div class="col"><h3>El repositorio</h3><a class="enl grande" href="{REPO_URL}" target="_blank" rel="noopener">{REPO_URL.replace("https://", "")}</a>'
          '<p class="small">Y recuerda: <b>sube tu tarea al Classroom</b> antes del viernes 11/12/2026, 10:00 (hora de Perú).</p></div></div></div>',
          nota('Agradece y deja los dos enlaces: los índices de cada sesión y el repositorio. Recuerda por última vez lo de subir la tarea al Classroom.',
               'Quien quiera repasar algo, que empiece por el índice de la sesión: dice qué hay y qué falta.',
               '¿Qué se llevan hoy que no tenían hace seis sesiones?'))


# ======================================================================================================================
# Marco: CSS (fondo blanco, sin ningún efecto al pasar el ratón) y JavaScript del visor
# ======================================================================================================================
CSS = r"""
:root{--tinta:#1f2937;--suave:#5b6472;--linea:#d6dde6;--fondo:#ffffff;--gris:#f4f6f9;--acento:#0b5cad;--acento2:#073d73;--ok:#15803d;--mal:#b91c1c;--aviso:#92400e;--oro:#c58a12;
 --mono:Consolas,"Cascadia Mono","DejaVu Sans Mono",Menlo,monospace;--sans:"Segoe UI",system-ui,-apple-system,Arial,sans-serif}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:#e8ecf1;color:var(--tinta);font-family:var(--sans)}
button{font:inherit;color:inherit;background:none;border:0;cursor:pointer}
a{color:var(--acento)}
:focus-visible{outline:3px solid var(--acento);outline-offset:2px;border-radius:6px}
#viewport{position:fixed;inset:0 0 48px 0;display:flex;align-items:center;justify-content:center;overflow:hidden}
#stage{width:1280px;height:720px;flex:none;position:relative;transform:scale(var(--s,1));background:var(--fondo);box-shadow:0 2px 14px rgba(0,0,0,.12)}
.slide{position:absolute;inset:0;padding:22px 52px 44px;display:none;flex-direction:column;gap:8px;overflow:hidden;background:var(--fondo)}
.slide.active{display:flex}
.bd{flex:1;display:flex;flex-direction:column;justify-content:center;gap:12px;min-height:0}
.kick{font-size:13px;letter-spacing:.09em;text-transform:uppercase;color:var(--acento);font-weight:700}
h1{font-size:30px;line-height:1.15;font-weight:700;margin-bottom:2px}
h3{font-size:20px;margin-bottom:6px}
.sub{font-size:25px;line-height:1.35;color:var(--suave);max-width:640px}
.chips{display:flex;gap:8px;flex-wrap:wrap}
.chip{display:inline-block;font-size:17px;padding:6px 15px;border-radius:999px;border:1px solid #bcd3ec;background:#eef5fc;color:var(--acento);font-weight:600}
.chip.peq{font-size:14px;padding:3px 11px;font-family:var(--mono)}
.chips.grande{justify-content:center}.chips.grande .chip{font-size:19px;padding:7px 18px}
.chip.grande{font-size:24px;padding:10px 26px;background:#fff7e0;border-color:#e2b56b;color:#7a4b06}
.tag{display:inline-block;font-size:12px;padding:1px 9px;border-radius:999px;border:1px solid var(--linea);background:var(--gris);color:var(--tinta);font-family:var(--sans);font-weight:600}
.tag.ok{border-color:#86c79c;background:#ecf8f0;color:var(--ok)}.tag.warn{border-color:#e2b56b;background:#fdf6e9;color:var(--aviso)}
.card{border:1px solid var(--linea);border-radius:12px;padding:14px 18px;background:#fff;min-width:0}
.callout{border-left:5px solid var(--acento);background:#eef5fc;padding:10px 18px;border-radius:0 10px 10px 0;font-size:19px;line-height:1.4}
.msg{font-size:24px;line-height:1.3;font-weight:600;border-left:6px solid var(--acento);padding:10px 20px;background:#eef5fc;border-radius:0 12px 12px 0}
.small{font-size:17px;line-height:1.42}.centro{text-align:center}
.fte{font-size:12.5px;line-height:1.4;color:var(--suave)}
.mono{font-family:var(--mono);font-size:.92em;background:var(--gris);padding:0 4px;border-radius:4px}
.ruta{background:#eef5fc;color:var(--acento2);font-size:14px;overflow-wrap:break-word}
.lb{display:inline-block;font-weight:700;font-size:11.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--suave);margin-right:6px}.lb.ok{color:var(--ok)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.split2c{display:grid;grid-template-columns:1fr 440px;gap:22px;align-items:center}
.split2b2{display:grid;grid-template-columns:1.1fr 1fr;gap:26px;align-items:start}
.split2d{display:grid;grid-template-columns:1.25fr 1fr;gap:26px;align-items:start}
.col{display:flex;flex-direction:column;gap:10px;min-width:0}
.list{list-style:none;display:flex;flex-direction:column;gap:5px}.list li{font-size:18px;line-height:1.38;padding-left:17px;position:relative}
.list li::before{content:"";position:absolute;left:2px;top:9px;width:7px;height:7px;border-radius:50%;background:var(--acento)}
.dg svg{display:block;width:100%;height:auto}
.tbl{width:100%;border-collapse:collapse;font-size:18px}.tbl th{text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--suave);border-bottom:2px solid var(--linea);padding:6px 9px}
.tbl td{border-bottom:1px solid var(--linea);padding:10px 12px;line-height:1.35;vertical-align:top}
.tbl.antes td:nth-child(2){background:#eef5fc}.tachado{color:var(--suave);text-decoration:line-through;text-decoration-color:#b9c4d2}
.tbl.antes td{font-size:19px;padding:13px 12px}
.tbl.equiv td{font-size:16.5px;padding:8px 12px}.tbl.equiv td:nth-child(2){background:#eef5fc}
.tbl.entr td{font-size:15.5px;padding:8px 10px}.tbl.entr td:first-child{font-weight:700;white-space:nowrap}.tbl.entr tr:last-child td{background:#fff7e0}
.tbl.falla-tbl td{font-size:20px;padding:18px 14px}.tbl.falla-tbl th{font-size:13px}.tbl.falla-tbl td:first-child{font-weight:600}
.calma{border-left:5px solid var(--ok);background:#ecf8f0;padding:14px 20px;border-radius:0 10px 10px 0;font-size:20px;line-height:1.4;margin-top:10px}
.term{border:1px solid var(--linea);border-radius:10px;background:var(--gris);overflow:hidden}
.term .bar{padding:5px 10px;border-bottom:1px solid var(--linea);background:#eaeef3;font-size:12.5px;color:var(--suave)}.term .bar em{font-style:normal}
.src{font-family:var(--mono);font-size:16px;line-height:1.5;padding:8px 12px;white-space:pre-wrap}
.kpi .n{display:block;font-size:30px;line-height:1.15;color:var(--acento);margin-bottom:4px}
/* portada */
.cover{display:grid;grid-template-columns:1fr 470px;gap:30px;align-items:center}
.portada-izq{display:flex;flex-direction:column;gap:22px}
.slide.portada{background:linear-gradient(160deg,#f3f8fe 0,#ffffff 55%)}
.slide.portada h1{font-size:52px;line-height:1.05;color:var(--acento2)}
/* mitos */
.mitos{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.mito{border:1px solid var(--linea);border-radius:14px;background:#fff;display:flex;flex-direction:column;min-height:196px;overflow:hidden}
.mbtn{display:flex;flex-direction:column;gap:6px;text-align:left;padding:14px 16px;width:100%;flex:1}
.mq{font-size:21px;line-height:1.28;font-weight:700;color:var(--acento2)}
.pista{font-size:13px;color:var(--suave);margin-top:auto}
.mbtn[aria-expanded="true"] .pista{display:none}
.real{padding:10px 16px 12px;background:#ecf8f0;border-top:1px solid #bfe3cc}.real p{font-size:17px;line-height:1.38;margin:2px 0 4px}
.real[hidden]{display:none}
.btn{border:2px solid var(--acento);color:var(--acento);border-radius:10px;padding:8px 20px;font-size:16px;font-weight:600;background:#fff}
.btn[aria-pressed="true"]{background:var(--acento);color:#fff}
/* ya sabes */
.yss{display:flex;flex-direction:column;gap:9px}
.ys{display:grid;grid-template-columns:1fr 22px 1fr;gap:6px;align-items:stretch}
.yt{display:block}.ys1,.ys2{border:1px solid var(--linea);border-radius:10px;padding:9px 13px;font-size:17px;line-height:1.35;display:flex;flex-direction:column;gap:3px;justify-content:center}
.ys1{background:#eef5fc;border-color:#bcd3ec;font-weight:600}.ys2{background:#fff}
.ysf{align-self:center;color:var(--acento);font-size:22px;text-align:center}
.split2c .ys{grid-template-columns:1fr 18px 1fr}.split2c .ys1,.split2c .ys2{font-size:16px;padding:8px 11px}
.explica{border:2px solid var(--acento);border-radius:16px;padding:20px 24px;background:#eef5fc}
.explica p{font-size:30px;line-height:1.35;font-weight:600;color:var(--acento2);margin-top:8px}
.mas{list-style:none;display:flex;flex-direction:column;gap:9px}.mas li{display:flex;flex-direction:column;gap:2px;border:1px solid var(--linea);border-radius:10px;padding:10px 14px}.mas .small{font-size:18px}
/* capturas */
.cap{display:flex;flex-direction:column;gap:5px;min-width:0}
.cap figcaption{font-size:12.5px;line-height:1.35;color:var(--suave)}.orig{font-size:11.5px}
.zoom{display:block;position:relative;cursor:zoom-in;text-align:left;width:100%}
.zoom img{display:block;max-width:100%;width:auto;height:auto;margin:0 auto;border:1px solid var(--linea);border-radius:8px;object-fit:contain;background:#f6f9fd}
.lupa{position:absolute;right:6px;bottom:6px;font-size:12px;background:rgba(255,255,255,.94);border:1px solid var(--linea);border-radius:6px;padding:2px 7px;display:flex;align-items:center;gap:4px;color:var(--suave)}
.caps2{display:grid;grid-template-columns:1fr 1fr;gap:18px;align-items:start}
.caps2s2{display:grid;grid-template-columns:1.25fr 1fr;gap:18px;align-items:start}
/* consejos */
.cons h3{font-size:19px;color:var(--acento2)}.cons p{margin-bottom:6px}
.paso2{display:flex;gap:12px;align-items:center;border:1px solid var(--linea);border-radius:10px;padding:12px 15px;font-size:19px;line-height:1.35}
.paso2>b{flex:none;width:30px;height:30px;border-radius:50%;background:var(--acento);color:#fff;text-align:center;line-height:30px}
/* entrega */
.bandera{background:var(--acento);color:#fff;border-radius:14px;padding:16px 26px;font-size:28px;line-height:1.25;text-align:center;border:4px solid var(--oro)}
.bandera b{font-weight:800}
.chks{display:flex;flex-direction:column;gap:7px}
.chk{display:flex;gap:12px;align-items:flex-start;border:1px solid var(--linea);border-radius:10px;padding:7px 12px;font-size:16px;line-height:1.35;cursor:pointer;background:#fff}
.chk input{position:absolute;opacity:0;width:1px;height:1px}
.caja{flex:none;width:24px;height:24px;border:2px solid var(--acento);border-radius:6px;background:#fff;position:relative;margin-top:1px}
.chk input:checked+.caja{background:var(--ok);border-color:var(--ok)}
.chk input:checked+.caja::after{content:"";position:absolute;left:6px;top:1px;width:7px;height:13px;border:solid #fff;border-width:0 3px 3px 0;transform:rotate(45deg)}
.chk input:focus-visible+.caja{outline:3px solid var(--acento);outline-offset:2px}
.chk:has(input:checked){background:#ecf8f0;border-color:#86c79c}
.cuenta{color:var(--suave)}.cuenta b{color:var(--acento);font-size:22px}
.pendiente{border:2px dashed #c9a65e;background:#fdf9f0;border-radius:12px;padding:12px 16px}.pendiente h3{color:var(--aviso)}
.slide.slide-solo{background:linear-gradient(160deg,#eaf3fc 0,#ffffff 70%)}
.slide.slide-solo .bd{justify-content:center}
.solo{display:flex;flex-direction:column;gap:30px;align-items:center;text-align:center}
.solo1{font-size:78px;line-height:1.05;font-weight:800;color:var(--acento2)}.solo1 span{color:var(--acento);border-bottom:8px solid var(--oro)}
.solo2{font-size:30px;line-height:1.35;max-width:900px}.solo2 b{color:var(--acento)}
/* pestañas */
.tabs{display:flex;gap:6px}.tab{border:1px solid var(--linea);border-radius:10px 10px 0 0;padding:6px 22px;font-size:17px;font-weight:700;background:#fff;color:var(--suave)}
.tab[aria-selected="true"]{background:var(--acento);color:#fff;border-color:var(--acento)}
.tpan{border:1px solid var(--linea);border-radius:0 12px 12px 12px;padding:12px 18px;margin-top:-1px;display:flex;flex-direction:column;gap:8px;min-height:226px}
.tpan[hidden]{display:none}
.mini{display:flex;gap:12px}.mini div{border:1px solid var(--linea);border-radius:10px;padding:6px 18px;font-size:14px;color:var(--suave);text-align:center}.mini b{display:block;font-size:26px;color:var(--acento)}
/* cierre */
.carta{max-width:920px;margin:0 auto;border-left:6px solid var(--oro);padding:8px 28px;display:flex;flex-direction:column;gap:14px}
.carta p{font-size:23px;line-height:1.42}.carta .firma{font-weight:700;color:var(--acento);text-align:right;font-size:20px}
.gracias{display:flex;flex-direction:column;gap:18px}.g1{font-size:44px;font-weight:800;color:var(--acento2)}
.enls{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.enl{display:block;border:1px solid #bcd3ec;background:#eef5fc;border-radius:10px;padding:9px 12px;font-size:16px;font-weight:600;text-decoration:none;color:var(--acento2)}
.enl.grande{font-size:17px;word-break:break-all}
/* svg */
svg .nodo{fill:#f4f8fc;stroke:#8fb2d6;stroke-width:1.6}svg .nodo.puerta{fill:#fdf6e9;stroke:#c9a65e;stroke-dasharray:6 4}svg .nodo.ok{fill:#ecf8f0;stroke:var(--ok)}svg .nodo.mal{fill:#fdeeee;stroke:var(--mal)}
svg .nodo.aviso{fill:#fdf6e9;stroke:#c9a65e}svg .nodo.oro{fill:#fff7e0;stroke:var(--oro);stroke-width:3}
svg .modelo{fill:#dbeafe;stroke:#0b5cad;stroke-width:2.4}svg .modelo2{fill:none;stroke:#0b5cad;stroke-width:1}
svg .datos{fill:#eef2f6;stroke:#6b7a8c;stroke-width:1.8}svg .datos2{fill:none;stroke:#6b7a8c;stroke-width:1.8}
svg .herr{fill:#fff4dc;stroke:#c58a12;stroke-width:2}svg .user{fill:#f1f3f6;stroke:#6b7280;stroke-width:2}
svg .obs{fill:#fbfcfe;stroke:#7b8794;stroke-dasharray:7 5;stroke-width:1.6}svg .zona{fill:#fbfcfe;stroke:#8fb2d6;stroke-dasharray:6 4;stroke-width:1.6}
svg .nube{fill:#eaf3fc;stroke:#0b5cad;stroke-width:2}
svg .fl{stroke:var(--acento);stroke-width:2.2;fill:none}svg .fl.g{stroke:#7b8794}svg .fl.r{stroke:var(--mal)}
svg .eje{stroke:#8a94a3;stroke-width:1.6;fill:none}svg .curva{stroke:var(--acento);stroke-width:3.4;fill:none}
svg .num{fill:var(--acento)}svg .numt{font:700 14px var(--sans);fill:#fff;text-anchor:middle}svg .puntoo{fill:var(--oro);stroke:#fff;stroke-width:3}
svg .visto{fill:var(--ok);stroke:#fff;stroke-width:2}svg .vtick{stroke:#fff;stroke-width:3;fill:none;stroke-linecap:round;stroke-linejoin:round}
svg .vmedio{fill:#fff;stroke:#c58a12;stroke-width:3}svg .vmedio2{fill:#c58a12}
svg .b1{fill:#9fc3ee;stroke:#0b5cad}svg .b2{fill:#fcd77a;stroke:#c58a12}svg .b3{fill:#8fd7ac;stroke:#15803d}
svg .esc{stroke:#073d73;stroke-width:1.4}svg .esc0{fill:#eaf3fc}svg .esc1{fill:#d3e5f9}svg .esc2{fill:#b9d5f3}svg .esc3{fill:#8fbbe8}svg .esc4{fill:#5b97d4}svg .esc5{fill:#0b5cad}
svg .te1.w,svg .te3.w{fill:#fff}
svg .t0{font:700 28px var(--sans);fill:var(--tinta);text-anchor:middle}svg .t1{font:700 18px var(--sans);fill:var(--tinta);text-anchor:middle}
svg .t2{font:16px var(--sans);fill:#374151;text-anchor:middle}svg .t3{font:15px var(--sans);fill:#374151;text-anchor:middle}
svg .tc{font:14.5px var(--sans);fill:#5b6472;text-anchor:middle}svg .tg{font:700 15px var(--sans);fill:var(--acento);text-anchor:middle}
svg .tg2{font:italic 14.5px var(--sans);fill:#4b5563;text-anchor:middle}svg .tg3{font:700 14px var(--sans);fill:var(--aviso);text-anchor:end}
svg .te1{font:700 17px var(--sans);fill:var(--tinta);text-anchor:middle}svg .te3{font:15px var(--sans);fill:var(--tinta);text-anchor:middle}
svg .izq{text-anchor:start}
.foot{position:absolute;left:52px;right:52px;bottom:12px;display:flex;justify-content:space-between;font-size:12px;color:var(--suave);border-top:1px solid var(--linea);padding-top:5px}
#prog{position:fixed;left:0;top:0;height:3px;background:var(--acento);z-index:5}
#bar{position:fixed;left:0;right:0;bottom:0;height:48px;display:flex;align-items:center;gap:5px;padding:0 10px;background:#fff;border-top:1px solid var(--linea);font-size:13px;z-index:6;overflow-x:auto}
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
const NOMBRES=__NOMBRES__;
const slides=$$('.slide'), N=slides.length; let cur=0;
slides.forEach((s,i)=>{const f=document.createElement('div');f.className='foot';
  f.innerHTML=`<span>ML e IA: de desarrollo a producción · Recap final</span><span><b>${esc(NOMBRES[s.dataset.part]||'')}</b> · ${i+1} / ${N}</span>`;s.appendChild(f)});
const cum=[];(()=>{let t=0;slides.forEach(s=>{cum.push(t);t+=+s.dataset.min||0})})();
const TOTAL=cum[N-1]+(+slides[N-1].dataset.min||0);
function go(i){i=Math.max(0,Math.min(N-1,i));cur=i;slides.forEach((s,k)=>s.classList.toggle('active',k===i));chrome();try{history.replaceState(null,'','#'+(i+1))}catch(e){}}
function chrome(){const s=slides[cur];
  $('#count').textContent=(cur+1)+' / '+N; $('#clockref').textContent='min '+cum[cur]+' de '+TOTAL;
  $('#prog').style.width=((cur+1)/N*100)+'%';
  $$('#bar .part').forEach(b=>b.classList.toggle('on',b.dataset.p===s.dataset.part));
  $('#notetext').innerHTML=(s.dataset.notes||'').split('\n').map(p=>{const m=p.match(/^([^:]{3,40}):\s?(.*)$/);return '<p>'+(m?'<b>'+esc(m[1])+':</b> '+esc(m[2]):esc(p))+'</p>'}).join('');
  $('#notemin').textContent='Tiempo previsto (propuesta): ~'+(s.dataset.min||0)+' min · acumulado '+cum[cur]+' min de '+TOTAL;
  $$('#idxgrid button').forEach((b,k)=>b.classList.toggle('cur',k===cur));}
function fit(){const v=$('#viewport');$('#stage').style.setProperty('--s',Math.min(v.clientWidth/1280,v.clientHeight/720).toFixed(4))}
addEventListener('resize',fit);
$('#idxgrid').innerHTML=slides.map((s,i)=>`<button data-i="${i}"><small>${esc(NOMBRES[s.dataset.part]||'')} · ~${s.dataset.min||0} min</small>${i+1}. ${esc(s.dataset.title||'')}</button>`).join('');
$('#idxgrid').addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;toggle('#index',false);go(+b.dataset.i)});
function toggle(sel,force){$(sel).classList.toggle('on',force)}
function zoom(on,src,alt){const z=$('#zoombox');if(on){$('#zoomimg').src=src;$('#zoomimg').alt=alt||'';}z.classList.toggle('on',!!on)}
$('#zoombox').onclick=()=>zoom(false);
$('#bprev').onclick=()=>go(cur-1); $('#bnext').onclick=()=>go(cur+1);
$('#bidx').onclick=()=>toggle('#index'); $('#bnotes').onclick=()=>toggle('#notes');
$('#bfull').onclick=()=>{if(document.fullscreenElement)document.exitFullscreen();else document.documentElement.requestFullscreen&&document.documentElement.requestFullscreen()};
$$('#bar .part').forEach(b=>b.onclick=()=>go(slides.findIndex(s=>s.dataset.part===b.dataset.p)));
function selTab(t){const g=t.closest('.slide');$$('[role=tab]',g).forEach(x=>{const on=x===t;x.setAttribute('aria-selected',String(on));x.tabIndex=on?0:-1;const p=$('#'+x.getAttribute('aria-controls'),g);if(p)p.hidden=!on});t.focus()}
addEventListener('keydown',e=>{
  const t=e.target; if(t&&/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)) return;
  if(e.ctrlKey||e.metaKey||e.altKey) return;
  const k=e.key;
  if(t&&t.getAttribute&&t.getAttribute('role')==='tab'&&(k==='ArrowRight'||k==='ArrowLeft')){e.preventDefault();const ts=$$('[role=tab]',t.closest('.slide'));const j=(ts.indexOf(t)+(k==='ArrowRight'?1:-1)+ts.length)%ts.length;selTab(ts[j]);return}
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
function mito(b,abrir){const r=b.parentElement.querySelector('.real');r.hidden=!abrir;b.setAttribute('aria-expanded',String(abrir))}
document.addEventListener('click',e=>{
  const z=e.target.closest('.zoom'); if(z){e.stopPropagation();zoom(true,z.dataset.src,z.dataset.alt);return}
  const m=e.target.closest('.mbtn'); if(m){e.stopPropagation();mito(m,m.getAttribute('aria-expanded')!=='true');return}
  const a=e.target.closest('#mitos-todos'); if(a){e.stopPropagation();const on=a.getAttribute('aria-pressed')!=='true';a.setAttribute('aria-pressed',String(on));a.textContent=on?'Ocultar las realidades':'Mostrar todas las realidades';$$('.mbtn').forEach(b=>mito(b,on));return}
  const t=e.target.closest('[role=tab]'); if(t){e.stopPropagation();selTab(t);return}
});
document.addEventListener('change',e=>{if(e.target.closest('.chk')){const g=e.target.closest('.slide');$('#chk-n',g).textContent=$$('.chk input:checked',g).length}});
fit();
const h=parseInt((location.hash||'').slice(1),10); go(isNaN(h)?0:h-1);
addEventListener('hashchange',()=>{const n=parseInt((location.hash||'').slice(1),10);if(!isNaN(n)&&n-1!==cur)go(n-1)});
})();
"""

VOLVER = '../../S5-MLOps-y-Operacion/index.html'


def html_completo():
    SLIDES.clear()
    construir_apertura()
    construir_s0()
    construir_s1()
    construir_s2()
    construir_s3()
    construir_s4()
    construir_s5()
    construir_salto()
    construir_consejos()
    construir_entrega()
    construir_repo()
    construir_cierre()
    js = JS.replace('__NOMBRES__', json.dumps(NOMBRES_PARTE, ensure_ascii=False))
    partes = ''.join(f'<button class="part" data-p="{k}" title="{esc(NOMBRES_PARTE[k])}">{esc(v)}</button>' for k, v in PARTES.items())
    return ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>Recap final: lo que ya sabes hacer · ML e IA: de desarrollo a producción</title>\n'
            f'<!-- Generado por generar.py: no se edita a mano. -->\n<style>{CSS}</style>\n</head>\n<body>\n'
            '<div id="prog"></div>\n<div id="viewport"><div id="stage">\n\n' + '\n\n'.join(SLIDES) + '\n\n</div></div>\n\n'
            '<aside id="notes" aria-label="Notas del profesor"><h3>Notas del profesor</h3><div id="notetext"></div><p class="small" id="notemin"></p></aside>\n'
            '<div id="index" aria-label="Índice"><h2>Índice</h2><div class="grid" id="idxgrid"></div></div>\n'
            '<div id="zoombox" aria-label="Captura ampliada"><p>Esc o clic para cerrar</p><img id="zoomimg" alt=""></div>\n'
            '<nav id="bar" aria-label="Controles">\n'
            '  <button id="bprev" aria-label="Anterior">←</button><button id="bnext" aria-label="Siguiente">→</button>\n'
            f'  <span id="count">1 / 1</span><span id="clockref" title="Minuto planificado acumulado (propuesta)"></span>\n  {partes}\n'
            '  <span class="sp"></span>\n'
            f'  <a id="bhome" href="{VOLVER}" title="Volver al índice de la sesión S5, la de cierre del curso">⌂ Índice</a><button id="bidx">Índice (O)</button><button id="bnotes">Notas (S)</button><button id="bfull">Pantalla completa (F)</button>\n'
            '</nav>\n'
            '<noscript>Esta presentación necesita JavaScript.</noscript>\n\n'
            f'<script>{js}</script>\n</body>\n</html>\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--comprobar', action='store_true')
    a = ap.parse_args()
    nuevo = html_completo()
    if a.comprobar:
        if not SALIDA.exists() or SALIDA.read_text(encoding='utf-8') != nuevo:
            print('DESFASADO: ejecuta python generar.py')
            sys.exit(1)
        print('al día')
        return
    actual = SALIDA.read_text(encoding='utf-8') if SALIDA.exists() else None
    if actual == nuevo:
        print('index.html: sin cambios')
    else:
        SALIDA.write_bytes(nuevo.encode('utf-8'))      # LF también en Windows
        print('escrito index.html')
    minutos = sum(int(m) for m in re.findall(r'data-min="(\d+)"', nuevo))
    print(f'{len(SLIDES)} diapositivas, {minutos} min propuestos')


if __name__ == '__main__':
    main()
