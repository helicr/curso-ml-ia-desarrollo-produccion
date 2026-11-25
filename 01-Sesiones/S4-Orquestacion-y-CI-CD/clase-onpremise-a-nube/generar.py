"""Genera la clase «De on-premise a la nube» (index.html y guia.md, junto a este archivo).

Clase de apoyo del curso «ML e IA: de desarrollo a producción»: por qué la nube, los tres grandes proveedores, Google Cloud, los
servicios que nos competen, nuestro Cloud Journey (de lo que hay hoy a lo que sería en GCP), costes y buenas prácticas.

Mismo manejo que las otras presentaciones del curso (← → · O índice · S notas · F pantalla completa · Esc), fondo blanco y nada
que se mueva al pasar el ratón. Los esquemas son SVG o HTML+CSS en línea (sin imágenes ni recursos externos). Cada cifra lleva su
fuente en la nota del ponente; lo que no se comprobó se dice «sin dato». La guía (guia.md) se genera del mismo contenido.

Uso:  python generar.py              escribe index.html y guia.md
      python generar.py --comprobar  no escribe; sale con 1 si alguno no está al día
"""
import argparse
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / 'index.html'
SALIDA_GUIA = AQUI / 'guia.md'
CONSULTA = '25/11/2026'
REGION = 'southamerica-west1'
REGION_ALT = 'southamerica-east1'

# Fuentes públicas consultadas (todas el 25/11/2026). Clave -> (nombre corto, dirección)
FUENTES = {
    'locs': ('Google Cloud · Cloud locations', 'https://cloud.google.com/about/locations'),
    'vertex': ('Vertex AI · Locations', 'https://docs.cloud.google.com/vertex-ai/docs/general/locations'),
    'gemini': ('Gemini en Vertex AI · Locations', 'https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/locations'),
    'run': ('Cloud Run · Locations', 'https://docs.cloud.google.com/run/docs/locations'),
    'bq': ('BigQuery · Locations', 'https://docs.cloud.google.com/bigquery/docs/locations'),
    'ar': ('Artifact Registry · Repository locations', 'https://docs.cloud.google.com/artifact-registry/docs/repositories/repo-locations'),
    'gcs': ('Cloud Storage · Locations', 'https://docs.cloud.google.com/storage/docs/locations'),
    'sm': ('Secret Manager · Locations', 'https://docs.cloud.google.com/secret-manager/docs/locations'),
    'ce': ('Compute Engine · Regions and zones', 'https://docs.cloud.google.com/compute/docs/regions-zones'),
    'dataproc': ('Dataproc · Regional endpoints', 'https://docs.cloud.google.com/dataproc/docs/concepts/regional-endpoints'),
    'free': ('Google Cloud · Free cloud features', 'https://docs.cloud.google.com/free/docs/free-cloud-features'),
    'budgets': ('Cloud Billing · Budgets', 'https://docs.cloud.google.com/billing/docs/how-to/budgets'),
    'jerarquia': ('Resource Manager · Resource hierarchy', 'https://docs.cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy'),
    'wif': ('IAM · Workload Identity Federation', 'https://docs.cloud.google.com/iam/docs/workload-identity-federation'),
    'aws7r': ('AWS Prescriptive Guidance · Migration strategies', 'https://docs.aws.amazon.com/prescriptive-guidance/latest/large-migration-guide/migration-strategies.html'),
    'sagemaker': ('AWS · What is Amazon SageMaker AI', 'https://docs.aws.amazon.com/sagemaker/latest/dg/whatis.html'),
    'foundry': ('Microsoft Learn · Foundry Models sold by Azure', 'https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure'),
    'synapse': ('Microsoft Learn · What is Azure Synapse Analytics', 'https://learn.microsoft.com/en-us/azure/synapse-analytics/overview-what-is'),
}


def fte(*claves):
    """Texto de fuentes para una nota del ponente."""
    return 'Fuente' + ('s' if len(claves) > 1 else '') + f' (consultadas el {CONSULTA}): ' + '; '.join(
        f'{FUENTES[c][0]}, {FUENTES[c][1]}' for c in claves) + '.'


# Órdenes de gcloud que se copian (clave -> orden). Placeholders en MAYÚSCULAS. La guía las repite tal cual.
O = {
    'login': 'gcloud auth login',
    'proyecto': 'gcloud config set project ID_PROYECTO',
    'region': f'gcloud config set run/region {REGION}',
    'factura': 'gcloud billing projects link ID_PROYECTO --billing-account=ID_FACTURACION',
    'apis': ('gcloud services enable run.googleapis.com artifactregistry.googleapis.com storage.googleapis.com '
             'bigquery.googleapis.com secretmanager.googleapis.com aiplatform.googleapis.com'),
    'borrar_run': f'gcloud run services delete retencion-api --region={REGION}',
    'borrar_ar': f'gcloud artifacts repositories delete REPOSITORIO --location={REGION}',
    'borrar_gcs': 'gcloud storage rm --recursive gs://NOMBRE_DEL_BUCKET',
    'borrar_bq': 'bq rm --recursive --force --dataset ID_PROYECTO:NOMBRE_DEL_DATASET',
    'borrar_proyecto': 'gcloud projects delete ID_PROYECTO',
}

PARTES = {'A': 'La nube', 'B': 'Proveedores', 'C': 'Google Cloud', 'D': 'Servicios', 'E': 'Cloud Journey', 'F': 'Costes', 'G': 'Cierre'}
NOMBRES_PARTE = {'A': 'Por qué la nube', 'B': 'Los tres grandes', 'C': 'Orientado a Google Cloud', 'D': 'Los servicios que nos competen',
                 'E': 'Nuestro Cloud Journey', 'F': 'Costes y buenas prácticas', 'G': 'Cierre'}


def esc(t):
    return html.escape(t, quote=True)


def md(t):
    """`código`, **negrita** y *cursiva* a HTML (sobre texto ya seguro)."""
    t = esc(t)
    t = re.sub(r'`([^`]+)`', r'<span class="mono">\1</span>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', t)
    return re.sub(r'(?<![\w*])\*([^*\s][^*]*)\*(?![\w*])', r'<i>\1</i>', t)


def term(titulo, lineas):
    """Terminal con una orden por línea y su botón ⧉. Las líneas que empiezan por # son comentarios (no se copian)."""
    filas = []
    for l in lineas:
        if l.startswith('#'):
            filas.append(f'<div class="tln c">{esc(l)}</div>')
        else:
            filas.append(f'<div class="tln"><span class="ps">$</span> <code>{esc(l)}</code><button class="cp" data-t="{esc(l)}" title="Copiar">⧉</button></div>')
    todo = '\n'.join(l for l in lineas if not l.startswith('#'))
    return (f'<div class="term"><div class="bar"><em>{esc(titulo)}</em><button class="cp cpall" data-t="{esc(todo)}">Copiar todo</button></div>'
            f'<div class="tls">{"".join(filas)}</div></div>')


def lista(items):
    return '<ul class="list">' + ''.join(f'<li>{md(i)}</li>' for i in items) + '</ul>'


def card(titulo, items, clase=''):
    return f'<div class="card {clase}"><h3>{esc(titulo)}</h3>{lista(items)}</div>'


def callout(texto):
    return f'<div class="callout">{md(texto)}</div>'


def tabla(cab, filas, clase=''):
    """Una celda que empieza por «!» se inserta como HTML tal cual."""
    def celda(c):
        return c[1:] if c.startswith('!') else md(c)
    th = ''.join(f'<th>{md(c)}</th>' for c in cab)
    tr = ''.join('<tr>' + ''.join(f'<td>{celda(c)}</td>' for c in f) + '</tr>' for f in filas)
    return f'<table class="tbl {clase}"><tr>{th}</tr>{tr}</table>'


def kpi(valor, texto, color=''):
    return f'<div class="card kpi"><b class="n {color}">{esc(valor)}</b><p class="small">{md(texto)}</p></div>'


def nivel(txt):
    clase = {'bajo': 'ok', 'medio': 'warn', 'alto': 'mal'}[txt]
    return f'!<span class="tag {clase}">{txt}</span>'


def ficha(color, nombre, que, curso, hoy=None):
    filas = f'<div class="fr"><span class="lb">Qué es</span> {md(que)}</div><div class="fr"><span class="lb">En el curso</span> {md(curso)}</div>'
    if hoy:
        filas += f'<div class="fr"><span class="lb">Hoy (local)</span> {md(hoy)}</div>'
    return f'<div class="card ficha {color}"><h3>{esc(nombre)}</h3>{filas}</div>'


SLIDES = []
_N = {}
GUIA = []   # (parte, título, h1, cuerpo, notas)
DENSOS = {'Qué se mueve y con qué esfuerzo', 'La región: Santiago', 'Servicios equivalentes (1)',
          'Servicios equivalentes (2)', 'TO-BE: cómo sería en Google Cloud', 'AS-IS: lo que hay hoy', 'Vertex AI y los modelos', 'Entrega, secretos y operación'}


def slide(parte, minutos, titulo, kick, h1, cuerpo, notas):
    cuerpo = re.sub(r'\*\*([^*<>]+)\*\*', r'<b>\1</b>', cuerpo)      # negrita y código escritos a mano en HTML
    cuerpo = re.sub(r'`([^`<>]+)`', r'<span class="mono">\1</span>', cuerpo)
    n = list(PARTES).index(parte) + 1
    _N[parte] = _N.get(parte, 0) + 1
    antetitulo = f'{n} · {NOMBRES_PARTE[parte]} · {kick}'
    attrs = f' data-part="{parte}" data-min="{minutos}" data-title="{esc(titulo)}"'
    clase = '' if titulo in DENSOS else ' grande'
    SLIDES.append(f'<section class="slide{clase}"{attrs}\n data-notes="{esc(notas)}">\n'
                  f'<p class="kick">{esc(antetitulo)}</p><h1>{md(h1)}</h1>\n{cuerpo}\n</section>')
    GUIA.append((parte, titulo, h1, cuerpo, notas))


# ======================================================================================================================
# Utilidades de SVG
# ======================================================================================================================
def svg(w, h, cuerpo, etiqueta, idp):
    marca = (f'<defs><marker id="{idp}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
             '<path d="M0 0 L10 5 L0 10 z" fill="#0b5cad"/></marker></defs>')
    return f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{esc(etiqueta)}">{marca}{cuerpo}</svg>'


def box(x, y, w, h, t1, t2='', cls='nodo', t3=''):
    lineas = [(t1, 't1')] + ([(t2, 't2')] if t2 else []) + ([(t3, 't2')] if t3 else [])
    y0 = y + h / 2 - (len(lineas) - 1) * 9 + 5
    textos = ''.join(f'<text x="{x + w / 2:g}" y="{y0 + i * 18:g}" class="{c}">{esc(t)}</text>' for i, (t, c) in enumerate(lineas))
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" class="{cls}"/>{textos}'


def flecha(idp, *pts, dis=False):
    d = 'M' + ' L'.join(f'{x} {y}' for x, y in pts)
    return f'<path d="{d}" class="fl{" dis" if dis else ""}" marker-end="url(#{idp})"/>'


def txt(x, y, s, cls='t2', izq=False):
    return f'<text x="{x}" y="{y}" class="{cls}{" izq" if izq else ""}">{esc(s)}</text>'


def zona(x, y, w, h, titulo):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" class="zona"/>' + txt(x + 14, y + 22, titulo, 't1 izq', True)


def svg_demanda():
    """Capacidad fija (on-premise) frente a capacidad que sigue la demanda (nube). Ilustración sin datos."""
    curva = 'M60 220 C110 220 130 130 180 130 S240 205 290 205 S360 80 420 80 S480 170 520 170'
    c = [f'<rect x="60" y="64" width="460" height="186" class="ocio"/>',
         f'<path d="{curva} L520 250 L60 250 Z" class="area"/>',
         f'<path d="{curva}" class="curva"/>',
         '<path d="M50 64 L530 64" class="fl cap"/>',
         '<path d="M60 40 L60 252 L530 252" class="eje"/>',
         txt(300, 36, 'On-premise: capacidad comprada para el pico (CAPEX)', 't1'),
         txt(300, 272, 'tiempo', 't2'),
         '<text x="22" y="150" class="t2" transform="rotate(-90 22 150)">demanda y capacidad</text>',
         txt(405, 150, 'demanda real', 't2'),
         txt(255, 112, 'capacidad ociosa: se paga sin usarla', 't2 mal'),
         txt(300, 292, 'En la nube la capacidad sigue a la curva y se paga lo consumido (OPEX).', 't3'),
         txt(300, 312, 'Ilustración conceptual: no son datos reales.', 't3')]
    return svg(560, 322, ''.join(c), 'Gráfica conceptual: la capacidad fija on-premise queda por encima de la demanda casi todo el tiempo; en la nube se paga solo la curva de demanda', 'a1')


def svg_jerarquia():
    c = [box(150, 10, 230, 56, 'Organización', 'la empresa (raíz)', 'nodo gcp'),
         box(40, 100, 200, 52, 'Carpeta «Datos»', 'departamentos, equipos', 'nodo'),
         box(290, 100, 200, 52, 'Carpeta «Pruebas»', 'se pueden anidar', 'nodo'),
         box(10, 192, 140, 56, 'Proyecto', 'ml-curso-prod', 'nodo ok'), box(165, 192, 140, 56, 'Proyecto', 'ml-curso-dev', 'nodo ok'),
         box(340, 192, 160, 56, 'Proyecto', 'sandbox-alumno', 'nodo ok'),
         box(10, 290, 140, 70, 'Recursos', 'bucket, tabla,', 'nodo', 'servicio Cloud Run'), box(165, 290, 140, 70, 'Recursos', 'VM, secreto,', 'nodo', 'repositorio'),
         box(340, 290, 160, 70, 'Recursos', 'los que crees', 'nodo', 'y luego borres'),
         flecha('j1', (265, 66), (140, 100)), flecha('j1', (265, 66), (390, 100)),
         flecha('j1', (140, 152), (80, 192)), flecha('j1', (140, 152), (235, 192)), flecha('j1', (390, 152), (420, 192)),
         flecha('j1', (80, 248), (80, 290)), flecha('j1', (235, 248), (235, 290)), flecha('j1', (420, 248), (420, 290)),
         '<path d="M545 30 L545 350" class="fl" marker-end="url(#j1)"/>',
         '<text x="565" y="190" class="t2" transform="rotate(90 565 190)">IAM y políticas se heredan hacia abajo</text>']
    return svg(600, 372, ''.join(c), 'Jerarquía de recursos de Google Cloud: organización, carpetas, proyectos y recursos; los permisos se heredan hacia abajo', 'j1')


def svg_wif():
    c = [box(10, 70, 190, 90, 'GitHub Actions', 'un workflow en marcha', 'nodo', 'tiene identidad propia'),
         box(250, 20, 210, 70, '1 · Token de GitHub', 'OIDC: dice quién es', 'nodo puerta'),
         box(250, 140, 210, 80, '2 · Google STS', 'servicio de tokens + pool', 'nodo gcp', 'y proveedor de identidad'),
         box(520, 140, 200, 80, '3 · Cuenta de servicio', 'se suplanta con permiso', 'nodo ok', 'mínimo y sin claves'),
         box(780, 20, 200, 60, 'Artifact Registry', 'subir la imagen', 'nodo'), box(780, 100, 200, 60, 'Cloud Run', 'desplegar la API', 'nodo'),
         box(780, 180, 200, 60, 'Cloud Storage', 'leer o escribir datos', 'nodo'),
         flecha('w1', (200, 100), (250, 60)), flecha('w1', (355, 90), (355, 140)),
         flecha('w1', (460, 180), (520, 180)), flecha('w1', (720, 160), (780, 55), dis=True),
         flecha('w1', (720, 180), (780, 130), dis=True), flecha('w1', (720, 200), (780, 210), dis=True),
         txt(10, 220, 'No se guarda ninguna clave JSON en GitHub: el token vale minutos y no se reutiliza.', 't3', True),
         txt(10, 242, 'OIDC = OpenID Connect: la forma estándar de que un servicio demuestre quién es con un token firmado.', 't3', True)]
    return svg(1000, 256, ''.join(c), 'Workload Identity Federation: GitHub Actions presenta su token OIDC a Google STS, que lo cambia por acceso temporal de una cuenta de servicio con permisos mínimos sobre Artifact Registry, Cloud Run y Cloud Storage', 'w1')


def svg_asis():
    c = [zona(10, 10, 780, 360, 'Tu equipo o el Codespace (el «on-premise» simulado)'),
         zona(810, 10, 360, 360, 'GitHub'),
         box(30, 60, 140, 76, 'Archivos', 'data/raw', 'nodo'), box(200, 60, 160, 76, 'Pipeline Python', 'raw → master → fs → ml', 'nodo'),
         box(390, 60, 140, 76, 'SQLite', 'las cuatro capas', 'nodo'), box(560, 60, 210, 76, 'Entrenamiento', 'y MLflow local', 'nodo', '(SQLite + carpeta)'),
         box(560, 230, 210, 76, 'Imagen Docker', 'con el modelo dentro', 'nodo'), box(390, 230, 140, 76, 'API FastAPI', 'uvicorn o docker run', 'nodo'),
         box(160, 230, 200, 76, 'Interfaz', 'lee SQLite (solo lectura)', 'nodo'),
         box(830, 60, 320, 76, 'GitHub Actions', 'lote, validación, nueva versión', 'nodo', 'y rollback'),
         box(830, 160, 320, 66, 'GHCR', 'ghcr.io: almacén de imágenes', 'nodo'),
         box(830, 250, 320, 70, 'Environment «produccion»', 'una persona aprueba', 'nodo puerta', 'antes de publicar'),
         flecha('s1', (170, 98), (200, 98)), flecha('s1', (360, 98), (390, 98)), flecha('s1', (530, 98), (560, 98)),
         flecha('s1', (665, 136), (665, 230)), flecha('s1', (560, 268), (530, 268)),
         flecha('s1', (440, 136), (290, 230), dis=True), flecha('s1', (360, 268), (390, 268)),
         flecha('s1', (990, 136), (990, 160)), flecha('s1', (990, 226), (990, 250)),
         txt(400, 346, 'Todo cabe en una máquina; no hay coste por uso ni elasticidad.', 't3')]
    return svg(1180, 380, ''.join(c), 'Arquitectura actual: pipeline, SQLite, MLflow, imagen Docker, API e interfaz en local, y GitHub Actions con GHCR y aprobación en GitHub', 's1')


def svg_tobe():
    c = [box(10, 60, 220, 70, 'Código en GitHub', 'repositorio y pruebas', 'nodo'),
         box(10, 190, 220, 80, 'GitHub Actions', 'construye, prueba, despliega', 'nodo', 'con aprobación'),
         flecha('t1', (120, 130), (120, 190)),
         zona(260, 10, 910, 400, f'Proyecto de Google Cloud · región {REGION} (Santiago)'),
         box(290, 60, 190, 76, 'Cloud Storage', 'archivos y Parquet', 'nodo gcp'), box(510, 60, 190, 76, 'BigQuery', 'capas master, fs y ml', 'nodo gcp'),
         box(740, 60, 190, 76, 'Vertex AI', 'Model Registry', 'nodo', 'práctica 04'), box(960, 60, 190, 76, 'Vertex AI', 'endpoint online', 'nodo', 'práctica 04'),
         box(290, 190, 190, 80, 'Artifact Registry', 'imagen retencion-api', 'nodo gcp'), box(510, 190, 190, 80, 'Cloud Run', 'la API (privada al inicio)', 'nodo gcp'),
         box(740, 190, 190, 80, 'Secret Manager', 'configuración sensible', 'nodo gcp'), box(960, 190, 190, 80, 'Logging y Monitoring', 'registros y alertas', 'nodo gcp'),
         box(290, 320, 860, 62, 'Presupuesto y alertas de facturación', 'creados antes que cualquier recurso', 'nodo ok'),
         flecha('t1', (480, 98), (510, 98)), flecha('t1', (700, 98), (740, 98), dis=True), flecha('t1', (930, 98), (960, 98), dis=True),
         flecha('t1', (480, 230), (510, 230)), flecha('t1', (740, 230), (700, 230)), flecha('t1', (605, 270), (605, 296), (1055, 296), (1055, 270), dis=True),
         flecha('t1', (230, 230), (290, 230)),
         txt(236, 214, 'WIF', 't2 ok'),
         txt(10, 330, 'Trazo continuo: se practica en el curso.', 't3', True), txt(10, 352, 'Ámbar y discontinuo: solo se menciona.', 't3', True)]
    return svg(1180, 420, ''.join(c), 'Arquitectura en Google Cloud: GitHub Actions despliega con identidad federada la imagen en Artifact Registry y Cloud Run; los datos van a Cloud Storage y BigQuery; el modelo, registrado y servido en Vertex AI (práctica 04)', 't1')


def svg_ruta():
    pasos = [('0 · Evaluar', 'inventario y dependencias', 'nodo'), ('1 · Base', 'proyecto, facturación, presupuesto, IAM', 'nodo'),
             ('2 · Datos', 'Cloud Storage y BigQuery, y validar', 'nodo gcp'), ('3 · Servicio', 'Artifact Registry, Cloud Run y WIF', 'nodo gcp'),
             ('4 · Modelo', 'Model Registry y endpoint', 'nodo puerta'), ('5 · Operar', 'registros, alertas y borrar', 'nodo ok')]
    c = []
    for i, (t, s, cl) in enumerate(pasos):
        x = 8 + i * 188
        c.append(f'<rect x="{x}" y="30" width="172" height="110" rx="10" class="{cl}"/>')
        c.append(txt(x + 86, 58, t, 't1'))
        c.append(f'<foreignObject x="{x + 8}" y="68" width="156" height="68"><div xmlns="http://www.w3.org/1999/xhtml" class="fo">{esc(s)}</div></foreignObject>')
        if i:
            c.append(flecha('r1', (x - 16, 85), (x, 85)))
    c.append(txt(8, 170, 'Oleadas 1 a 3: se practican en el curso (S4, según el plan). Oleada 4: solo se menciona. Oleada 0: el inventario ya existe en el curso.', 't3', True))
    c.append(txt(8, 192, 'El orden importa: primero el presupuesto, después los datos, después el servicio; lo que cambia el modelo viene al final.', 't3', True))
    return svg(1140, 206, ''.join(c), 'Hoja de ruta en seis oleadas: evaluar, base, datos, servicio, modelo y operar', 'r1')


def svg_ciclo():
    c = [box(10, 20, 130, 60, '1 · Crear', 'con etiquetas', 'nodo'), box(190, 20, 130, 60, '2 · Usar', 'tamaños mínimos', 'nodo gcp'),
         box(370, 20, 130, 60, '3 · Apagar', 'al terminar', 'nodo puerta'), box(550, 20, 130, 60, '4 · Borrar', 'y comprobar', 'nodo mal'),
         flecha('c1', (140, 50), (190, 50)), flecha('c1', (320, 50), (370, 50)), flecha('c1', (500, 50), (550, 50)),
         txt(345, 112, 'Apagar no es borrar: un bucket, una tabla o una imagen siguen cobrando almacenamiento.', 't3')]
    return svg(690, 130, ''.join(c), 'Ciclo de vida de un recurso en la nube: crear con etiquetas, usar, apagar y borrar', 'c1')


# ======================================================================================================================
# Contenido
# ======================================================================================================================
def construir():
    SLIDES.clear()
    _N.clear()
    GUIA.clear()

    # ---------------------------------------------------------------- A · Por qué la nube
    slide('A', 3, 'Portada', 'ML e IA: de desarrollo a producción · clase de apoyo', 'De on-premise a la nube', f'''
<div class="cover">
 <p class="sub">Qué es la nube y por qué se usa, quiénes son los tres grandes proveedores, cómo se organiza <b>Google Cloud</b> y qué pasaría con lo que hemos construido en el curso si lo lleváramos allí: <b>nuestro Cloud Journey</b>.</p>
 <div class="chips"><span class="tag">Nube pública</span><span class="tag">AWS · Azure · Google Cloud</span><span class="tag">Cloud Run · BigQuery · Vertex AI</span><span class="tag">Costes</span></div>
 <div class="card" style="margin-top:22px"><h3>Cómo seguirla</h3><p class="small"><b>← →</b> avanzan · <b>O</b> índice · <b>S</b> notas del ponente (con las fuentes) · <b>F</b> pantalla completa. Todo está también en texto en <span class="mono">guia.md</span>. Las cifras y nombres de Google Cloud se consultaron en su documentación pública el {CONSULTA}; lo que no se pudo comprobar dice «sin dato».</p></div>
</div>''',
          'Clase de apoyo, orientada a lo que se ha visto en el curso: pipeline raw, master, fs y ml, API con FastAPI, imagen Docker, MLflow y SQLite en local, y GitHub Actions con GHCR en la nube de GitHub. Objetivo: que cada persona entienda el mapa de la nube y pueda decir qué pieza de nuestro caso iría a qué servicio, con qué esfuerzo y con qué cuidado de costes. No se ha ejecutado nada en Google Cloud para preparar esta clase: todo lo de la nube viene de documentación pública, citada en las notas.')

    slide('A', 3, 'Lo que ya construimos', 'punto de partida', 'Lo que ya tenemos es nuestro «on-premise» simulado', '''
<div class="grid4">
 <div class="card"><h3>Datos</h3><p class="small">Archivos en <span class="mono">data/raw</span> y la base <b>SQLite</b> con las capas <span class="mono">raw_</span>, <span class="mono">master_</span>, <span class="mono">fs_</span> y <span class="mono">ml_</span>.</p></div>
 <div class="card"><h3>Modelo</h3><p class="small">Entrenamiento con scikit-learn y seguimiento en <b>MLflow</b> con SQLite y una carpeta local.</p></div>
 <div class="card"><h3>Servicio</h3><p class="small">API <b>FastAPI</b> en una imagen <b>Docker</b>, e interfaz que lee la base en solo lectura.</p></div>
 <div class="card"><h3>Entrega</h3><p class="small"><b>GitHub Actions</b> publica la imagen en <b>GHCR</b>, con un <i>environment</i> que exige aprobación.</p></div>
</div>
<div class="grid2" style="margin-top:14px">
 <div class="callout"><b>On-premise</b> significa «en instalaciones propias»: servidores que compras, instalas y mantienes tú. Nuestro portátil o Codespace hace de ese entorno.</div>
 <div class="callout"><b>La pregunta de la clase:</b> si mañana hubiera que llevar esto a producción real en una empresa, ¿qué se movería a la nube, a qué servicio y con qué cuidado?</div>
</div>
<div class="card" style="margin-top:14px"><h3>Cómo está organizada la clase</h3>
 <div class="ruta"><span class="paso">1 · Por qué la nube</span><span class="paso">2 · Los tres grandes</span><span class="paso">3 · Google Cloud</span><span class="paso">4 · Servicios</span><span class="paso">5 · Cloud Journey</span><span class="paso">6 · Costes</span></div></div>''',
          'Recapitulación de lo construido, para anclar la clase en el caso conocido. La interfaz abre la SQLite en solo lectura; la API no lee datos: el modelo va dentro de la imagen (así se describe en la teoría de S3). Esto es lo que llamamos on-premise simulado: la situación de partida de muchos equipos, que ya tienen cosas funcionando y se preguntan cómo llevarlas a la nube sin romperlas. Sin cifras en esta diapositiva.')

    slide('A', 6, 'On-premise frente a nube', 'comparación', 'On-premise frente a nube: de comprar capacidad a pagar por uso', '''
<div class="split" style="grid-template-columns:.95fr 1.05fr">
 <div class="col">
  <div class="card">''' + tabla(['', 'On-premise', 'Nube pública'], [
        ['**Dinero**', '**CAPEX**: inversión inicial en equipos', '**OPEX**: gasto corriente por uso'],
        ['**Capacidad**', 'se compra para el pico y se queda fija', '**elástica**: sube y baja con la demanda'],
        ['**Plazo**', 'semanas o meses hasta tener el equipo', 'minutos para crear un recurso'],
        ['**Mantenimiento**', 'tuyo: hardware, parches, centro de datos', 'el proveedor se ocupa de la infraestructura'],
        ['**Servicios**', 'los instalas y operas tú', '**gestionados**: bases de datos, ML, colas…'],
        ['**Riesgo**', 'quedarse corto o pagar capacidad sin usar', 'olvidar apagar y que el gasto crezca']]) + '''</div>
  <div class="callout"><b>Elasticidad</b> es poder aumentar o reducir recursos casi al instante. Es la ventaja principal; el riesgo asociado son los costes, por eso hay una parte entera sobre ellos.</div>
 </div>
 <div class="card">''' + svg_demanda() + '''</div>
</div>''',
          'CAPEX (capital expenditure) es la inversión inicial en activos, como comprar servidores; OPEX (operating expenditure) es el gasto corriente, como pagar por lo consumido cada mes. La gráfica es una ilustración conceptual construida a mano para este curso: no representa datos reales ni mide ahorros; no se afirma que la nube sea siempre más barata (depende de cuánto se use y de cómo se opere). Concepto general, sin fuente numérica.')

    slide('A', 6, 'Modelos de servicio', 'IaaS, PaaS, serverless y SaaS', 'Cuanto más gestionado el servicio, menos te toca administrar', '''
<div class="split" style="grid-template-columns:1.25fr .75fr">
 <div class="card">
  <table class="tbl capas"><tr><th>Capa</th><th>On-premise</th><th>IaaS</th><th>PaaS</th><th>Serverless</th><th>SaaS</th></tr>
   <tr><td>Aplicación</td><td class="tu">tú</td><td class="tu">tú</td><td class="tu">tú</td><td class="tu">tú (tu código o imagen)</td><td class="pv">proveedor</td></tr>
   <tr><td>Datos</td><td class="tu">tú</td><td class="tu">tú</td><td class="tu">tú</td><td class="tu">tú</td><td class="tu">tú (tu contenido)</td></tr>
   <tr><td>Entorno de ejecución</td><td class="tu">tú</td><td class="tu">tú</td><td class="pv">proveedor</td><td class="pv">proveedor</td><td class="pv">proveedor</td></tr>
   <tr><td>Sistema operativo</td><td class="tu">tú</td><td class="tu">tú</td><td class="pv">proveedor</td><td class="pv">proveedor</td><td class="pv">proveedor</td></tr>
   <tr><td>Servidores y virtualización</td><td class="tu">tú</td><td class="pv">proveedor</td><td class="pv">proveedor</td><td class="pv">proveedor</td><td class="pv">proveedor</td></tr>
   <tr><td>Red, almacenamiento y centro de datos</td><td class="tu">tú</td><td class="pv">proveedor</td><td class="pv">proveedor</td><td class="pv">proveedor</td><td class="pv">proveedor</td></tr>
   <tr class="ej"><td>Ejemplos</td><td>tu sala de servidores</td><td>Compute Engine, Amazon EC2, Azure Virtual Machines</td><td>Cloud SQL, App Engine</td><td>Cloud Run, AWS Lambda, Azure Functions</td><td>Google Workspace, Microsoft 365</td></tr>
  </table>
  <p class="small" style="margin-top:6px"><span class="lg tu"></span> lo gestionas tú &nbsp; <span class="lg pv"></span> lo gestiona el proveedor</p>
 </div>
 <div class="col">
  <div class="card"><h3>Responsabilidad compartida</h3><p class="small">{}</p></div>
  <div class="callout">En el curso usaremos sobre todo <b>serverless con contenedores</b> (Cloud Run) y servicios <b>gestionados</b> (BigQuery, Cloud Storage), no máquinas virtuales.</div>
 </div>
</div>'''.replace('{}', md('El proveedor protege **la nube** (instalaciones, hardware, red base); tú proteges **lo que pones en ella**: identidades, permisos, datos y configuración. Cuanto más a la derecha, más cosas hace el proveedor, pero **tus datos y tus accesos siguen siendo tuyos**.')),
          'La tabla simplifica: en la práctica hay matices (un servicio PaaS permite configurar parte del entorno de ejecución, y serverless suma escalado automático, incluso a cero, y pago por uso). IaaS es infraestructura como servicio, PaaS plataforma como servicio, SaaS software como servicio. El modelo de responsabilidad compartida es un concepto general de todos los proveedores; no se cita una fuente numérica. Los ejemplos son nombres de producto reales de cada proveedor.')

    slide('A', 4, 'Siglas y palabras', 'vocabulario · antes de seguir', 'Siglas y palabras que van a aparecer', '<div class="card">' + tabla(['Palabra', 'Qué es'], [
        ['**CAPEX / OPEX**', '*Capital expenditure*: inversión inicial. *Operating expenditure*: gasto corriente por uso'],
        ['**IaaS / PaaS / SaaS**', 'Infraestructura, plataforma o software **como servicio**: cuánto gestiona el proveedor'],
        ['**región y zona**', 'una región es una zona geográfica con centros de datos; una zona es una parte aislada dentro de ella. Se elige dónde viven tus recursos'],
        ['**SLA**', '*Service Level Agreement*: compromiso escrito del proveedor sobre la disponibilidad de un servicio'],
        ['**IAM**', '*Identity and Access Management*: quién (identidad) puede hacer qué (rol) sobre qué recurso'],
        ['**cuenta de servicio**', 'identidad para un programa, no para una persona; se le dan solo los permisos que necesita'],
        ['**WIF**', '*Workload Identity Federation*: un programa de fuera de Google Cloud (como GitHub Actions) entra **sin claves guardadas**'],
        ['**API (de un servicio)**', 'además de «nuestra API», cada servicio de Google Cloud se activa y se maneja por una API que hay que **habilitar**'],
        ['**FinOps**', 'práctica de vigilar y optimizar el gasto en la nube entre técnica y finanzas']]) + '</div>',
          'Vocabulario mínimo. Insistir en tres: región y zona, porque de ahí sale el coste y la latencia; IAM y cuenta de servicio, porque la seguridad en la nube es sobre todo identidad; y WIF, que veremos con GitHub Actions. FinOps se menciona solo como idea. Definiciones generales, sin cifras.')

    # ---------------------------------------------------------------- B · Proveedores
    slide('B', 5, 'Los hiperescalares', 'quiénes son', 'Tres hiperescalares y algunos más', '''
<div class="grid3">
 <div class="card prov"><h3>Amazon Web Services</h3><p class="small"><b>AWS</b>, de Amazon. Infraestructura, datos e IA como servicio, con presencia en todo el mundo.</p><p class="small">ML: <b>Amazon SageMaker</b> · LLMs: <b>Amazon Bedrock</b></p></div>
 <div class="card prov"><h3>Microsoft Azure</h3><p class="small"><b>Azure</b>, de Microsoft. Se integra con Microsoft 365 y con el directorio de identidades <b>Microsoft Entra ID</b>.</p><p class="small">ML: <b>Azure Machine Learning</b> · LLMs: <b>Azure OpenAI</b></p></div>
 <div class="card prov"><h3>Google Cloud</h3><p class="small"><b>GCP</b>, de Google. Destaca en datos (<b>BigQuery</b>), contenedores (<b>Kubernetes</b> lo creó Google) e IA.</p><p class="small">ML: <b>Vertex AI</b> · LLMs: <b>Gemini</b></p></div>
</div>
<div class="grid2" style="margin-top:12px">
 <div class="card"><h3>Qué es un hiperescalar</h3><p class="small">Un proveedor con centros de datos repartidos por el mundo en <b>regiones</b>, un catálogo muy amplio de servicios, pago por uso y todo accesible por API. Hay otros: <b>Oracle Cloud Infrastructure</b>, <b>IBM Cloud</b> y <b>Alibaba Cloud</b>.</p></div>
 <div class="card"><h3>Cuál elegir</h3><p class="small">No hay una respuesta única: depende de <b>dónde están ya los datos y la identidad de la empresa</b>, de los servicios que se necesitan, del coste y de la región. Muchas empresas usan **más de una** (multinube). Cuota de mercado: <b>sin dato</b> verificado aquí; cambia cada trimestre y hay que citar un informe con fecha.</p></div>
</div>''',
          'Los tres nombres y sus servicios de ML y LLMs son los de la tabla de la diapositiva siguiente. Sobre Kubernetes: lo creó Google y hoy es un proyecto abierto; Google Kubernetes Engine es su servicio gestionado. Cuotas de mercado, número de regiones y precios: no se citan porque no se han verificado en esta preparación; si alguien las pregunta, remitir a un informe de analistas con fecha o a la página de ubicaciones de cada proveedor. Nombres de producto: Amazon SageMaker AI (renombrado de SageMaker el 3/12/2024) y Azure OpenAI en Microsoft Foundry; para abreviar usamos los nombres cortos. ' + fte('sagemaker', 'foundry'))

    filas_a = [
        ['**Máquina virtual**', 'tu equipo', 'Amazon EC2', 'Azure Virtual Machines', 'Compute Engine'],
        ['**Contenedores sin servidores**', '`docker run`', 'AWS App Runner, Amazon ECS con AWS Fargate', 'Azure Container Apps', '**Cloud Run**'],
        ['**Kubernetes gestionado**', 'solo demo del instructor', 'Amazon EKS', 'Azure Kubernetes Service (AKS)', 'Google Kubernetes Engine (GKE)'],
        ['**Registro de imágenes**', 'GHCR', 'Amazon ECR', 'Azure Container Registry', '**Artifact Registry**'],
        ['**Almacenamiento de objetos**', 'carpeta `data/raw`', 'Amazon S3', 'Azure Blob Storage', '**Cloud Storage**'],
        ['**Base de datos relacional**', 'SQLite', 'Amazon RDS', 'Azure SQL Database', 'Cloud SQL'],
        ['**Data warehouse**', 'SQLite (capas)', 'Amazon Redshift', 'Azure Synapse Analytics', '**BigQuery**']]
    filas_b = [
        ['**Spark gestionado**', 'no se usa (solo mención)', 'Amazon EMR', 'Azure Databricks', 'Dataproc'],
        ['**Plataforma de ML**', 'MLflow local', 'Amazon SageMaker', 'Azure Machine Learning', '**Vertex AI**'],
        ['**LLMs gestionados**', 'fuera del curso base', 'Amazon Bedrock', 'Azure OpenAI', 'Gemini en Vertex AI'],
        ['**CI/CD**', 'GitHub Actions', 'AWS CodePipeline y CodeBuild', 'Azure DevOps Pipelines', 'Cloud Build (o GitHub Actions)'],
        ['**Identidad y permisos**', 'tu usuario', 'AWS IAM', 'Microsoft Entra ID y Azure RBAC', '**Cloud IAM**'],
        ['**Secretos**', 'archivo `.env`', 'AWS Secrets Manager', 'Azure Key Vault', '**Secret Manager**'],
        ['**Monitorización y registros**', 'logs en la salida estándar', 'Amazon CloudWatch', 'Azure Monitor', '**Cloud Logging y Monitoring**']]
    cab = ['Necesidad en nuestro caso', 'Hoy en el curso', 'AWS', 'Azure', 'Google Cloud']
    slide('B', 5, 'Servicios equivalentes (1)', 'tabla comparativa 1 de 2', 'Servicios equivalentes: cómputo, imágenes, datos', '<div class="card">' + tabla(cab, filas_a, 'eq') + '</div>' +
          '<div class="callout" style="margin-top:10px">En <b>negrita</b> los servicios de Google Cloud que usaría nuestro Cloud Journey. «Equivalente» no es «idéntico»: cambian límites, precios y detalles de manejo.</div>',
          'Primera mitad de la tabla de equivalencias. Los nombres de AWS y Azure son nombres de producto reales; se escribieron los nombres cortos habituales. Azure Synapse Analytics sigue descrito como servicio en su documentación (versión de 2025), aunque Microsoft también ofrece Microsoft Fabric para analítica; no se compara aquí. Para Spark gestionado en Azure se cita Azure Databricks; Synapse también ofrece Spark. No se comparan precios ni rendimiento. ' + fte('synapse'))
    slide('B', 5, 'Servicios equivalentes (2)', 'tabla comparativa 2 de 2', 'Servicios equivalentes: ML, LLMs, entrega y operación', '<div class="card">' + tabla(cab, filas_b, 'eq') + '</div>' +
          '<div class="callout" style="margin-top:10px">Fíjate en la columna «Hoy en el curso»: casi todo lo que usamos tiene su equivalente gestionado. Lo que no se usa (Spark, LLMs) se queda en una mención.</div>',
          'Segunda mitad de la tabla. La plataforma de ML de AWS se llama hoy Amazon SageMaker AI (era Amazon SageMaker hasta el 3 de diciembre de 2024); Bedrock aparece dentro de la familia Amazon SageMaker según su documentación. La oferta de LLMs de Azure se documenta hoy como Azure OpenAI en Microsoft Foundry. En Google Cloud, Gemini se usa a través de Vertex AI. ' + fte('sagemaker', 'foundry'))

    # ---------------------------------------------------------------- C · Google Cloud
    slide('C', 6, 'Cómo se organiza Google Cloud', 'jerarquía, regiones y zonas', 'Organización, carpetas, proyectos y recursos', '''
<div class="split" style="grid-template-columns:1.05fr .95fr">
 <div class="card">''' + svg_jerarquia() + '''</div>
 <div class="col">
  <div class="card"><h3>El proyecto es la unidad de trabajo</h3>''' + lista([
        'Todo recurso vive en **un proyecto**; sin proyecto no hay servicios, ni APIs, ni facturación.',
        'Un proyecto tiene un **ID único**, un nombre y **etiquetas** (*labels*) para filtrar.',
        'Los permisos y las políticas se **heredan** de arriba abajo.',
        'La **organización** requiere Google Workspace o Cloud Identity; una cuenta personal de prueba puede tener proyectos sin organización.']) + '''</div>
  <div class="card"><h3>Región y zonas</h3><div class="regionbox"><b>southamerica-west1</b> · Santiago, Chile<div class="zonas"><span>-a</span><span>-b</span><span>-c</span></div></div><p class="small">Una **región** son varias **zonas** aisladas. Compute Engine lista tres zonas en Santiago.</p></div>
 </div></div>''',
          'La jerarquía es la de la documentación de Resource Manager: organización, carpetas (opcionales), proyectos y recursos; las políticas de permisos se heredan hacia abajo. Los nombres de carpetas y proyectos del dibujo son inventados como ejemplo. La organización requiere una cuenta de Google Workspace o de Cloud Identity; los usuarios de prueba gratuita o de nivel gratuito pueden tener proyectos sin padre. Las zonas de southamerica-west1 son a, b y c según la tabla de regiones y zonas de Compute Engine. ' + fte('jerarquia', 'ce'))

    slide('C', 6, 'Identidad en Google Cloud', 'IAM, cuentas de servicio y WIF', 'Identidad: quién puede hacer qué, y sin claves guardadas', '''
<div class="card">''' + svg_wif() + '''</div>
<div class="grid3" style="margin-top:12px">
 <div class="card"><h3>IAM</h3><p class="small">''' + md('Una **identidad** (persona, grupo o cuenta de servicio) recibe un **rol** (conjunto de permisos) **sobre un recurso**. Regla de oro: el **mínimo privilegio**.') + '''</p></div>
 <div class="card"><h3>Cuenta de servicio</h3><p class="small">''' + md('La identidad de **un programa**: la API en Cloud Run se ejecuta con una cuenta de servicio que solo puede leer lo que necesita.') + '''</p></div>
 <div class="card"><h3>Workload Identity Federation</h3><p class="small">''' + md('GitHub Actions presenta su propio token a Google, que lo cambia por **acceso temporal**. Se evitan las **claves de cuenta de servicio**, que son credenciales potentes y un riesgo si se guardan mal.') + '''</p></div>
</div>''',
          'WIF permite que cargas de trabajo de fuera de Google Cloud, entre ellas pipelines de CI/CD como GitHub, accedan con identidades de un proveedor externo en lugar de claves de cuenta de servicio; el intercambio sigue el estándar OAuth 2.0 token exchange, mediante pools de identidades y proveedores (GitHub figura entre los admitidos). La documentación recomienda dar acceso directamente sobre recursos o suplantar una cuenta de servicio con un token de corta vida. El dibujo es un esquema simplificado hecho para esta clase. En el curso, esto es el paso de «tu usuario y una clave» a «cuenta de servicio sin claves» (refactor). ' + fte('wif'))

    slide('C', 6, 'Qué hace falta para empezar', 'la lista de la compra', 'Qué hace falta para empezar en Google Cloud', '''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">
  <div class="card"><h3>Los cinco pasos</h3><ol class="ol">
   <li><b>Cuenta de Google</b> (personal o de empresa)</li>
   <li><b>Proyecto</b>, mejor desechable para aprender</li>
   <li><b>Facturación</b>: cuenta de facturación vinculada (la prueba gratuita pide un medio de pago)</li>
   <li><b>Habilitar las APIs</b> de los servicios que vas a usar</li>
   <li><b>Herramienta</b>: <span class="mono">gcloud</span> en tu equipo o <b>Cloud Shell</b> en el navegador</li></ol></div>
  <div class="callout"><b>Antes de crear nada:</b> un presupuesto con alertas. Se explica en la parte de costes.</div>
 </div>
 <div class="col">''' + term('Terminal · plantilla (cambia los valores en MAYÚSCULAS; sin ejecutar en esta clase)', [
        O['login'], O['proyecto'], O['region'], O['factura'], O['apis']]) + '''
  <div class="card"><h3>Habilitar una API</h3><p class="small">Cada servicio llega por una API que se <b>habilita por proyecto</b>: un servicio sin habilitar da error de permiso aunque tengas el rol correcto.</p></div>
 </div></div>''',
          'Los cinco pasos son el flujo habitual; los comandos de gcloud son los de uso corriente (auth login, config set project, billing projects link, services enable) con valores de ejemplo en mayúsculas: no se han ejecutado para preparar esta clase. La documentación pública de la prueba gratuita indica que se crea una cuenta de facturación y un proyecto de ejemplo, y que se exige tarjeta u otro medio de pago válido durante la prueba. Cloud Shell figura entre los productos globales de la página de ubicaciones. Los nombres de las APIs (run, artifactregistry, storage, bigquery, secretmanager, aiplatform) siguen el patrón servicio.googleapis.com. ' + fte('free', 'locs'))

    # ---------------------------------------------------------------- D · Servicios
    slide('D', 5, 'Mapa de servicios', 'el panorama', 'Los servicios que nos competen, en un mapa', '''
<div class="mapa">
 <div class="gr g1"><h4>Datos</h4><div class="t">Cloud Storage<small>archivos y Parquet</small></div><div class="t">BigQuery<small>analítica con SQL</small></div></div>
 <div class="gr g2"><h4>Cómputo y contenedores</h4><div class="t">Artifact Registry<small>imágenes</small></div><div class="t">Cloud Run<small>la API</small></div><div class="t">GKE<small>Kubernetes</small></div><div class="t">Dataproc<small>Spark</small></div></div>
 <div class="gr g3"><h4>ML e IA</h4><div class="t">Vertex AI<small>Model Registry</small></div><div class="t">Vertex AI<small>endpoints y pipelines</small></div><div class="t">Model Garden<small>y Gemini</small></div></div>
 <div class="gr g4"><h4>Entrega y seguridad</h4><div class="t">GitHub Actions<small>con WIF</small></div><div class="t">Cloud Build<small>CI/CD de GCP</small></div><div class="t">Secret Manager<small>secretos</small></div><div class="t">Cloud IAM<small>permisos</small></div></div>
 <div class="gr g5"><h4>Operación y costes</h4><div class="t">Cloud Logging<small>registros</small></div><div class="t">Cloud Monitoring<small>métricas y alertas</small></div><div class="t">Presupuestos<small>y alertas de gasto</small></div></div>
</div>
<div class="callout" style="margin-top:12px">Son <b>dieciséis</b> recuadros, pero para nuestro caso solo hacen falta siete para empezar: <b>Cloud Storage, BigQuery, Artifact Registry, Cloud Run, Secret Manager, IAM y presupuestos</b>. El resto se suma después.</div>''',
          'Mapa agrupado por función. Sirve de índice de las cuatro diapositivas siguientes. Para empezar en el caso del curso bastan siete servicios: lo mismo que se practica con los scripts de la teoría de S3 (archivos a Cloud Storage, tablas a BigQuery, imagen a Artifact Registry, servicio en Cloud Run, secreto en Secret Manager, cuenta de servicio y presupuesto). Sin cifras externas. El conteo «dieciséis» es el número de recuadros del mapa (Vertex AI aparece dos veces).')

    slide('D', 6, 'Datos y contenedores', 'Cloud Storage, BigQuery y Artifact Registry', 'Datos y contenedores: para qué sirve cada uno en el curso', '''
<div class="grid3">''' + ficha('c1', 'Cloud Storage', 'Almacenamiento de **objetos** en *buckets*: archivos de cualquier tipo, sin límite práctico de tamaño total.', 'Los archivos originales y los **Parquet** exportados de las tablas, con su huella SHA-256.', 'carpeta `data/raw`') +
          ficha('c1', 'BigQuery', 'Almacén de datos **analítico** sin servidores: se consulta con **SQL** y se paga por almacenamiento y consultas.', 'Las capas `master_`, `fs_` y `ml_` como **copia analítica validada** de la SQLite.', 'SQLite') +
          ficha('c2', 'Artifact Registry', 'Repositorio de **imágenes de contenedor** y paquetes dentro de tu proyecto, con permisos IAM.', 'La imagen `retencion-api` que hoy se publica en GHCR.', 'GHCR (`ghcr.io`)') + '''</div>
<div class="callout" style="margin-top:12px"><b>Importante:</b> desplegar la API en la nube <b>no hace que lea BigQuery</b>. En el curso la API lleva el modelo dentro de la imagen; BigQuery recibe una copia analítica. Que el servicio consulte BigQuery sería un cambio de diseño (refactor).</div>
<div class="card" style="margin-top:12px"><h3>Cómo se sabe que los datos llegaron bien</h3><p class="small">''' + md('No basta con subirlos: se **valida** (mismos conteos, esquemas y agregados que en origen) y se comprueba la integridad. Cloud Storage informa de **MD5 y CRC32C**, no de SHA-256: por eso la huella SHA-256 se calcula en origen y se comprueba **descargando y recalculando**. *Sin verificar hoy en la documentación vigente.*') + '''</p></div>''',
          'Las tres fichas siguen el mapa de equivalencias de la teoría de S3 (Cloud Storage para archivos, BigQuery para las capas, Artifact Registry para la imagen). La aclaración sobre la API que no lee BigQuery es la del propio material del curso. La afirmación de que Cloud Storage informa de MD5 y CRC32C pero no de SHA-256 está marcada en el material de S3 como sin verificar; aquí se mantiene esa marca. Las regiones donde existen estos servicios se tratan en la parte de costes.')

    slide('D', 6, 'Ejecutar: Cloud Run, GKE y Dataproc', 'dónde corre el código', 'Ejecutar el código: Cloud Run, GKE y Dataproc', '''
<div class="grid3">''' + ficha('c2', 'Cloud Run', 'Ejecuta **contenedores** sin gestionar servidores: escala con las peticiones y puede **bajar a cero** instancias.', 'La **API FastAPI** (privada al principio), desplegada desde Artifact Registry.', '`uvicorn` o `docker run`') +
          ficha('c2', 'GKE', '**Kubernetes** gestionado: tú decides más cosas (redes, nodos, versiones) y ganas control a cambio de operar más.', 'Alternativa a Cloud Run; en el curso solo hay una **demo del instructor**, sin ejecutar.') +
          ficha('c2', 'Dataproc', 'Clústeres de **Hadoop y Spark** gestionados para procesar volúmenes que no caben en una sola máquina.', 'Solo se **menciona**: nuestro conjunto de datos cabe en una máquina.') + '''</div>
<div class="card" style="margin-top:12px"><h3>¿Cloud Run o GKE?</h3>''' + tabla(['', 'Cloud Run', 'GKE'], [
        ['**Qué gestionas**', 'la imagen y su configuración', 'además, el clúster y sus nodos (según el modo)'],
        ['**Cuándo**', 'una API o un trabajo en contenedor, sin demasiadas piezas', 'muchos servicios que se hablan entre sí, necesidades de red o de nodo especiales'],
        ['**Para nuestro caso**', '**la opción de partida**', 'solo si el crecimiento lo pide']]) + '''</div>''',
          'Cloud Run: contenedores sin servidores, con escalado automático; puede reducirse el mínimo de instancias a cero (así lo recomienda el material de S3 para no pagar sin uso). GKE y Dataproc se practican en las prácticas 02 y 03 (ejecutadas y borradas en Santiago el 25/11/2026). La comparación Cloud Run frente a GKE es una orientación general de la clase, no una recomendación oficial ni una medida.')

    slide('D', 7, 'Vertex AI y los modelos', 'plataforma de ML', 'Vertex AI: de registrar un modelo a servirlo', '''
<div class="grid3">''' + ficha('c3', 'Model Registry', 'Catálogo de **versiones de modelos** con sus metadatos.', 'Sustituiría al registro de **MLflow** local, o convivirían.', 'MLflow con SQLite y carpeta') +
          ficha('c3', 'Endpoints', 'Despliegue **gestionado** de un modelo para pedirle predicciones por red (en línea) o en lote.', 'El modo **online** de la clase de producción, como alternativa a Cloud Run.') +
          ficha('c3', 'Pipelines', 'Orquestación de pasos de entrenamiento y despliegue como flujo.', 'En el curso orquesta **GitHub Actions**; esto sería la otra vía.') + '''</div>
<div class="grid2" style="margin-top:12px">''' + ficha('c3', 'Model Garden', 'Catálogo para descubrir y usar modelos, propios de Google, abiertos y de terceros.', 'Solo se menciona.') +
          ficha('c3', 'Gemini en Vertex AI', 'Modelos de lenguaje de Google accesibles por API desde la plataforma.', 'Fuera del caso base (el modelo de retención no es un LLM); útil para explicar resultados o agentes.') + '''</div>
<div class="callout" style="margin-top:12px">Nuestra pieza central, el <b>modelo de retención</b>, es un modelo clásico de scikit-learn: puede servirse en <b>Cloud Run</b> dentro de la imagen o desde un <b>endpoint de Vertex AI</b>. Elegir entre ambos es una decisión de diseño de la siguiente diapositiva.</div>''',
          'Vertex AI agrupa varios servicios de ML. La documentación de ubicaciones lista Model Registry, predicción en línea y por lotes de modelos personalizados, entrenamiento y Pipelines entre las funciones disponibles en Santiago (diapositiva de regiones). La documentación actual presenta estas páginas bajo el nombre «Gemini Enterprise Agent Platform» aunque el producto y el SDK siguen llamándose Vertex AI; para esta clase se usa el nombre Vertex AI, que sigue vigente en las URL y en las funciones. Equivalencias con MLflow y GitHub Actions: las de la teoría de S3. ' + fte('vertex', 'gemini'))

    slide('D', 6, 'Dos maneras de servir el modelo', 'decisión de diseño', 'Servir el modelo: Cloud Run o endpoint de Vertex AI', '<div class="card">' + tabla(['', 'API en Cloud Run (lo que hace el curso)', 'Endpoint de Vertex AI'], [
        ['**Qué despliegas**', 'una **imagen** con el modelo dentro y tu código de API', 'un **modelo registrado** en Model Registry, con su contenedor de servicio'],
        ['**Quién controla el contrato**', 'tú: rutas, validación y formato propios', 'más estándar y menos flexible: sigue el formato de predicción de la plataforma'],
        ['**Versionado**', 'la etiqueta de la imagen (`v2-<huella>`)', 'las versiones del modelo en el registro'],
        ['**Pipeline de entrega**', 'GitHub Actions construye, prueba y despliega', 'GitHub Actions o Vertex AI Pipelines registran y despliegan'],
        ['**Coste base**', 'puede bajar a cero cuando no hay tráfico', '**sin dato** aquí: depende de la configuración del endpoint'],
        ['**Encaja si**', 'la API tiene lógica propia (nuestra interfaz, tres modos de explotación)', 'se quiere una solución gestionada para el modelo y su monitoreo']]) + '</div>' +
          '<div class="callout" style="margin-top:12px"><b>Para el curso:</b> Cloud Run primero (rehost de lo que ya funciona); el endpoint de Vertex AI cuando se quiera registro gestionado (lo hace la práctica 04: ojo, cobra mientras existe).</div>',
          'Comparación orientativa hecha para esta clase a partir de la arquitectura del curso; no son medidas ni una recomendación oficial. El coste de un endpoint de Vertex AI no se ha consultado: se deja «sin dato». La ventaja de Cloud Run de poder bajar a cero instancias es la del material de S3. Si alguien pregunta por el monitoreo de modelos, recordar que la lista de funciones de Vertex AI en Santiago no incluye Model Monitoring (ver diapositiva de regiones). ' + fte('vertex'))

    slide('D', 7, 'Entrega, secretos y operación', 'lo que rodea al modelo', 'Entrega, secretos y operación: lo que rodea al código', '''
<div class="grid3">''' + ficha('c4', 'GitHub Actions + WIF', 'El flujo de entrega del curso, que se **autentica sin claves** contra Google Cloud.', 'Publica la imagen y despliega; el *environment* `produccion` exige aprobación.') +
          ficha('c4', 'Cloud Build', 'Servicio de CI/CD de Google Cloud: construye imágenes y ejecuta pasos en la nube.', 'Alternativa a GitHub Actions; en el curso orquesta GitHub Actions.') +
          ficha('c4', 'Secret Manager', 'Guarda secretos con **versiones** y permisos; un servicio los monta o los lee.', 'Sustituye al archivo `.env`. En la demo, un valor de ejemplo que el servicio no consume.', 'archivo `.env`') + '''</div>
<div class="grid3" style="margin-top:12px">''' + ficha('c5', 'Cloud Logging', 'Reúne los **registros** de los servicios, con búsqueda.', 'El registro JSON de la API ya sirve sin cambiar el código.', 'líneas JSON por la salida estándar') +
          ficha('c5', 'Cloud Monitoring', '**Métricas y alertas** sobre el estado de los servicios.', 'Avisar si la API falla; la deriva del modelo se vería en S5.') +
          ficha('c5', 'Presupuestos y alertas', 'Límites de **aviso** de gasto sobre una cuenta de facturación.', 'Se crean **antes** que cualquier recurso.', 'hardware fijo') + '''</div>''',
          'Cloud Build figura entre los productos globales (sin dependencia de ubicación) de la página de ubicaciones de Google Cloud. Cloud Monitoring también aparece como producto global, con escenarios regionales en su documentación. El tratamiento de Secret Manager con un valor de ejemplo y el registro JSON que ya sirve para Cloud Logging son los del material de S3. Un presupuesto de alertas no corta el gasto: ver la diapositiva de presupuestos. ' + fte('locs'))

    # ---------------------------------------------------------------- E · Cloud Journey
    slide('E', 5, 'AS-IS: lo que hay hoy', 'el punto de partida', 'AS-IS: lo que hay hoy', '<div class="card">' + svg_asis() + '</div>' +
          '<div class="grid3" style="margin-top:12px">' + card('Qué funciona', ['Todo el flujo de datos, entrenamiento, API y entrega.', 'La entrega ya es **automática y con aprobación**.']) +
          card('Qué limita', ['Todo en **una máquina**: sin escalado ni disponibilidad.', 'SQLite y MLflow locales no se comparten en equipo.']) +
          card('Qué ya es «de nube»', ['**GitHub Actions** y **GHCR** ya corren en la nube de GitHub.', 'La imagen Docker es **portable**: base del rehost.']) + '</div>',
          'AS-IS es «como está hoy». El dibujo recoge el caso real del curso: pipeline raw, master, fs y ml sobre SQLite; MLflow local; imagen Docker con el modelo dentro; API FastAPI; interfaz que lee la base en solo lectura; GitHub Actions publicando en GHCR con aprobación en el environment produccion. Dibujo propio hecho para esta clase, sin cifras.')

    slide('E', 6, 'TO-BE: cómo sería en Google Cloud', 'el destino', 'TO-BE: cómo sería en Google Cloud', '<div class="card">' + svg_tobe() + '</div>' +
          '<div class="callout" style="margin-top:12px">Qué cambia: <b>dónde viven los datos, la imagen y el servicio</b>. Qué <b>no</b> cambia: el código del pipeline, la API y el flujo de entrega en GitHub Actions; solo se autentica con WIF.</div>',
          f'TO-BE es «como sería». Todo el proyecto queda en una sola región, {REGION} (Santiago), por cercanía a los alumnos, pero ver en la diapositiva de regiones qué partes de Vertex AI están disponibles allí. Los datos van a Cloud Storage y BigQuery; la imagen a Artifact Registry y se despliega en Cloud Run; GitHub Actions entra con identidad federada. Model Registry y el endpoint de Vertex AI se practican en la práctica 04 (ejecutada y borrada el 25/11/2026). Dibujo propio, sin cifras.')

    slide('E', 7, 'Qué se mueve y con qué esfuerzo', 'plan por pieza', 'Qué se mueve, a qué servicio y con qué esfuerzo', '<div class="card">' + tabla(['Pieza', 'Hoy', 'En Google Cloud', 'Estrategia', 'Esfuerzo'], [
        ['Archivos originales', '`data/raw`', 'Cloud Storage', 'Replatform', nivel('bajo')],
        ['Capas master, fs y ml', 'SQLite', 'BigQuery (vía Parquet) y validación', 'Replatform', nivel('medio')],
        ['Imagen de la API', 'GHCR', 'Artifact Registry', 'Rehost', nivel('bajo')],
        ['Servicio de la API', '`uvicorn` o `docker run`', 'Cloud Run', 'Rehost', nivel('bajo')],
        ['Configuración sensible', 'archivo `.env`', 'Secret Manager', 'Replatform', nivel('bajo')],
        ['Identidad de la entrega', 'usuario y claves', 'cuenta de servicio + WIF', 'Refactor', nivel('medio')],
        ['Registros', 'salida estándar', 'Cloud Logging', 'Replatform', nivel('bajo')],
        ['Seguimiento y registro de modelos', 'MLflow local', 'Vertex AI Model Registry', 'Replatform o refactor', nivel('alto')],
        ['Servir el modelo online', 'API en Docker', 'endpoint de Vertex AI (opcional)', 'Refactor', nivel('alto')],
        ['Orquestación', 'GitHub Actions', 'se mantiene (o Cloud Build / Vertex AI Pipelines)', 'Retener', nivel('bajo')]]) + '</div>' +
          '<p class="small" style="margin-top:6px"><b>Esfuerzo</b>: valoración cualitativa del profesor para este caso, <b>sin medir</b>. Vale como orden de magnitud para priorizar, no como estimación de proyecto.</p>',
          'Las filas y las estrategias vienen del mapa de equivalencias de la teoría de S3 y de la guía de migración del curso; se añaden el servicio de modelos de Vertex AI y la fila de orquestación. La columna de esfuerzo es una valoración cualitativa hecha para esta clase: bajo cuando no se toca el código, medio cuando hay que validar datos o cambiar la forma de autenticarse, alto cuando cambia la forma de registrar o servir el modelo. No hay cifras de horas ni de coste: sin dato.')

    slide('E', 6, 'Las R de la migración', 'estrategias por pieza', 'Las «R» de la migración y cuál aplica a cada pieza', '''
<div class="rgrid">
 <div class="r r1"><h3>Rehost</h3><p class="small"><i>Lift and shift</i>: mover tal cual.</p><p class="small"><b>Nosotros:</b> la imagen Docker y la API en Cloud Run.</p></div>
 <div class="r r2"><h3>Replatform</h3><p class="small">Mover con ajustes mínimos a un servicio gestionado.</p><p class="small"><b>Nosotros:</b> SQLite a BigQuery, archivos a Cloud Storage, `.env` a Secret Manager.</p></div>
 <div class="r r3"><h3>Refactor</h3><p class="small">Rediseñar para aprovechar la nube.</p><p class="small"><b>Nosotros:</b> claves a identidad federada; servir el modelo desde Vertex AI.</p></div>
 <div class="r r4"><h3>Repurchase</h3><p class="small">Recomprar: sustituir por un producto de terceros.</p><p class="small"><b>Nosotros:</b> ninguna pieza hoy; sería cambiar un componente propio por un servicio de pago.</p></div>
 <div class="r r5"><h3>Retire</h3><p class="small">Retirar: apagar lo que ya no aporta.</p><p class="small"><b>Nosotros:</b> la SQLite como fuente, cuando BigQuery esté validado; recursos de ensayo al terminar.</p></div>
 <div class="r r6"><h3>Retain</h3><p class="small">Retener: dejarlo donde está.</p><p class="small"><b>Nosotros:</b> el repositorio y GitHub Actions; los datos personales o sensibles no suben.</p></div>
</div>
<div class="callout" style="margin-top:12px">Las listas de «R» <b>varían según la fuente</b>: AWS documenta <b>siete</b> (añade <i>Relocate</i>, mover a la versión en nube de la misma plataforma). Lo que importa: <b>elegir una estrategia por pieza</b>, no una para todo.</div>''',
          'AWS Prescriptive Guidance documenta siete estrategias («7 Rs»): Retire, Retain, Rehost, Relocate, Repurchase, Replatform y Refactor o re-architect; también indica que Refactor es la más compleja y costosa. El material del curso usa seis (rehost, replatform y refactor se practican; retener, retirar y recomprar solo se mencionan). Cuál lista usa hoy Google Cloud: sin verificar. Los ejemplos de «Nosotros» son los de la teoría de S3 y de la guía de migración, salvo Retire y Retain, que se plantean para esta clase. ' + fte('aws7r'))

    slide('E', 5, 'Hoja de ruta', 'por oleadas', 'Una hoja de ruta de seis oleadas', '<div class="card">' + svg_ruta() + '</div>' +
          '<div class="grid3" style="margin-top:12px">' + card('Antes de mover nada', ['**Inventario**: qué hay, cuánto ocupa y de qué depende.', '**Plan de vuelta atrás** escrito antes de crear nada.']) +
          card('Mientras se mueve', ['**Validar** cada paso: conteos, esquemas y agregados.', 'Datos y servicio se migran **por separado**.']) +
          card('Después', ['**Medir el gasto** y ajustar tamaños.', '**Borrar** lo que ya no sirve: forma parte de la migración.']) + '</div>',
          'Las fases (evaluar, planificar, ejecutar y optimizar) son las del material del curso, que advierte que sus nombres no se han contrastado con la documentación vigente de Google Cloud; aquí se reparten en oleadas por pieza. Qué se practica en el curso: las oleadas 1 a 3, según el plan de S4; la 4 solo se menciona. Hoja de ruta propuesta para esta clase, sin plazos ni cifras.')

    # ---------------------------------------------------------------- F · Costes y buenas prácticas
    slide('F', 7, 'Cómo se paga y qué es gratis', 'prueba gratuita y nivel gratuito', 'Cómo se paga y qué es gratis', '''
<div class="grid2">
 <div class="card"><h3>Prueba gratuita (<i>Free Trial</i>)</h3>''' + lista([
        'Programa público: **$300** de crédito de bienvenida **válido 90 días**.',
        'Pide un **medio de pago válido**; no se cobra durante la prueba.',
        'No cubre **GPUs**, Marketplace ni aumentos de cuota; tampoco la **API de Gemini en AI Studio** ni modelos de terceros.',
        'Al terminar sin actualizar: la cuenta se cierra y los **datos se marcan para borrado**, con 30 días de gracia.']) + '''</div>
 <div class="card"><h3>Nivel gratuito mensual (<i>Free Tier</i>)</h3>''' + lista([
        '**Cloud Run**: 2 millones de peticiones al mes.',
        '**BigQuery**: 1 TiB de consultas y 10 GiB de almacenamiento al mes.',
        '**Cloud Storage**: 5 GB-mes, pero **solo** en `us-east1`, `us-west1` y `us-central1`.',
        'Lo que pase del límite se factura (o se descuenta del crédito).']) + '''</div>
</div>
<div class="grid3" style="margin-top:12px">
 ''' + kpi('$300 · 90 días', 'crédito y plazo del programa de prueba (cifra pública del programa; **no** el saldo de ninguna cuenta concreta)') +
          kpi('0 GB gratis', 'en `southamerica-west1`: el nivel gratuito de Cloud Storage **no** cubre Santiago; ahí el almacenamiento se factura (o sale del crédito de la prueba)', 'malc') +
          kpi('Pago por uso', 'cómputo, almacenamiento, consultas y salida de red: **se factura lo que consumes**') + '''
</div>''',
          'Cifras y condiciones de la documentación pública de Google Cloud sobre prueba gratuita y nivel gratuito, consultada el 25/11/2026: 300 dólares de crédito válidos 90 días; medio de pago obligatorio; restricciones (sin GPUs, Marketplace ni aumentos de cuota; el crédito no cubre Gemini API en AI Studio ni modelos de socios, ni, para altas desde el 16/11/2026, los servicios de la plataforma Gemini); cierre de cuenta y 30 días de gracia; límites mensuales de Cloud Run, BigQuery y Cloud Storage. La cuenta de curso del profesor está en prueba gratuita: no se cita su saldo. Las condiciones cambian: comprobar antes de impartir. ' + fte('free'))

    slide('F', 7, 'Presupuestos, alertas y limpieza', 'controlar y borrar', 'Presupuestos con alertas, y apagar no es borrar', '''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">
  <div class="card"><h3>Presupuesto con alertas</h3>''' + lista([
        'Se crea **antes** que cualquier recurso, sobre la cuenta de facturación.',
        'Umbrales por defecto: **50 %, 90 % y 100 %** del importe, sobre gasto real.',
        'Puede avisar también por **previsión** de gasto.']) + '''</div>
  <div class="callout" style="border-left-color:#b91c1c;background:#fdeeee"><b>Un presupuesto de alertas no corta el gasto:</b> «Setting an alerts-only budget doesn't automatically cap Google Cloud … usage or spending». Solo avisa; alguien tiene que actuar.</div>
  <div class="card"><h3>Etiquetas y tamaños</h3>''' + lista([
        '**Etiqueta todo**: `curso`, `responsable`, `caduca`. Así se sabe qué es de quién.',
        'Cloud Run con **mínimo de instancias 0** y tamaños pequeños.',
        'Tablas con **caducidad** en las zonas de prueba.']) + '''</div>
 </div>
 <div class="col">
  <div class="card">''' + svg_ciclo() + '''</div>
  ''' + term('Terminal · limpieza al terminar (plantilla; sin ejecutar en esta clase)', [
        O['borrar_run'], O['borrar_ar'], O['borrar_gcs'], O['borrar_bq'], '# o, si el proyecto era desechable, de una vez', O['borrar_proyecto']]) + '''
 </div></div>''',
          'Umbrales por defecto de los presupuestos de Cloud Billing: 50, 90 y 100 por ciento del importe, calculados sobre el gasto real; pueden cambiarse y añadirse previsiones. La documentación advierte textualmente de que un presupuesto solo de alertas no limita el uso ni el gasto; hay presupuestos con tope de gasto, solo para servicios compatibles y a nivel de proyecto (no se detalla aquí). Los comandos de limpieza son plantillas con valores en mayúsculas: no se han ejecutado. Antes de borrar un proyecto, comprobar que no hay nada que conservar. ' + fte('budgets'))

    slide('F', 7, 'La región: Santiago', 'qué hay y qué no', 'La región del curso: qué hay en Santiago', '<div class="card">' + tabla(['Servicio', f'{REGION} (Santiago)', f'{REGION_ALT} (São Paulo)'], [
        ['**Cloud Storage**', '!<span class="tag ok">sí</span> región', '!<span class="tag ok">sí</span> región'],
        ['**BigQuery**', '!<span class="tag ok">sí</span>', '!<span class="tag ok">sí</span>'],
        ['**Artifact Registry**', '!<span class="tag ok">sí</span>', '!<span class="tag ok">sí</span>'],
        ['**Cloud Run**', '!<span class="tag ok">sí</span> (nivel de precio 2)', '!<span class="tag ok">sí</span> (nivel de precio 2)'],
        ['**Secret Manager**', '!<span class="tag ok">sí</span> secretos regionales', '!<span class="tag ok">sí</span> secretos regionales'],
        ['**GKE y Dataproc**', '!<span class="tag ok">sí</span> comprobado: GKE Autopilot y Dataproc sin servidor funcionaron en Santiago (prácticas 02 y 03, 25/11/2026)', '!<span class="tag">sin dato</span>'],
        ['**Vertex AI: modelos propios**', '!<span class="tag ok">sí</span> entrenamiento, predicción en línea y por lotes, Model Registry, Pipelines', '!<span class="tag ok">sí</span> y además Model Monitoring, Experiments y Explainable AI'],
        ['**Gemini en Vertex AI**', '!<span class="tag warn">no listada</span> usar el endpoint global', '!<span class="tag">sin dato</span> aparece como región; sin detalle de modelos']]) + '</div>' +
          '<div class="callout" style="margin-top:10px"><b>Conclusión:</b> en Santiago caben nuestras piezas de partida y el Model Registry y los endpoints de Vertex AI. Si se necesita <b>Model Monitoring</b>, <b>Experiments</b> o <b>Explainable AI</b> de Vertex AI, la alternativa documentada es <b>' + REGION_ALT + ' (São Paulo)</b>. El nivel gratuito de Cloud Storage no cubre ninguna de las dos.</div>',
          f'Disponibilidad según la documentación oficial, consultada el {CONSULTA}. Vertex AI en {REGION}: AutoML tabular y de series temporales, inferencia por lotes y en línea y entrenamiento de modelos personalizados, Model Registry, Vector Search, Pipelines, TensorBoard y Vizier; no figuran Model Monitoring, Experiments, Explainable AI, etiquetado de datos ni Workbench. En {REGION_ALT} figuran además Model Monitoring, Experiments y Explainable AI, y Workbench. Gemini: la página de regiones de Gemini no lista Santiago; São Paulo aparece como región pero las celdas de disponibilidad salieron vacías en la copia consultada, así que no se sabe qué modelos; existe endpoint global. Cloud Run: ambas regiones en nivel de precio 2. BigQuery, Artifact Registry y Cloud Storage: Santiago y São Paulo aparecen en sus listas de regiones. Secret Manager: ambas admiten secretos regionales; también existe replicación automática. Dataproc: la página no enumera regiones y remite a las de Compute Engine. GKE: la página consultada no nombra la región: sin dato. Nota de nombre: las páginas actuales de Vertex AI hablan de «Gemini Enterprise Agent Platform». ' + fte('vertex', 'gemini', 'run', 'bq', 'ar', 'gcs', 'sm', 'ce', 'dataproc'))

    slide('F', 6, 'Buenas prácticas', 'seis reglas', 'Seis reglas para no arrepentirse', '''
<div class="grid3">
 <div class="card regla"><h3><span class="num">1</span> Proyecto desechable</h3><p class="small">Un proyecto solo para aprender, que se **borra entero** al acabar.</p></div>
 <div class="card regla"><h3><span class="num">2</span> Presupuesto primero</h3><p class="small">Antes de crear el primer recurso, con alertas a **varios umbrales**.</p></div>
 <div class="card regla"><h3><span class="num">3</span> Una sola región</h3><p class="small">Cerca de los usuarios (aquí, Santiago). Mover datos entre regiones suma complejidad y coste de red.</p></div>
 <div class="card regla"><h3><span class="num">4</span> Sin claves</h3><p class="small">**Workload Identity Federation** en lugar de claves JSON; ningún secreto en el repositorio.</p></div>
 <div class="card regla"><h3><span class="num">5</span> Mínimo privilegio</h3><p class="small">Una **cuenta de servicio por función** con un solo rol; secretos en **Secret Manager**.</p></div>
 <div class="card regla"><h3><span class="num">6</span> Etiquetar y borrar</h3><p class="small">Todo con etiqueta y fecha de caducidad; **validar** antes de borrar el origen.</p></div>
</div>
<div class="callout" style="margin-top:14px"><b>Datos del curso:</b> ningún dato sensible ni personal en la nube del curso, y comprobar la licencia del conjunto de datos antes de subirlo.</div>''',
          'Las seis reglas resumen el material del curso (proyecto desechable, presupuesto antes que cualquier recurso, una sola región, identidad sin claves, mínimo privilegio y limpieza) y las recomendaciones de la documentación citada en las diapositivas anteriores: WIF evita las claves de cuenta de servicio, que son credenciales potentes con riesgo si se gestionan mal; los presupuestos no cortan el gasto. La regla de datos es la de la guía de migración del curso. Sin cifras.')

    # ---------------------------------------------------------------- G · Cierre
    slide('G', 5, 'Qué está verificado', 'qué se comprobó y qué no', 'Qué se comprobó de verdad y qué falta', f'''
<div class="grid2">
 <div class="card"><h3 class="okc">Comprobado en la documentación oficial ({CONSULTA})</h3>''' + lista([
        'Disponibilidad en Santiago y São Paulo de Cloud Storage, BigQuery, Artifact Registry, Cloud Run y Secret Manager.',
        'Funciones de Vertex AI en Santiago y en São Paulo; Gemini sin Santiago.',
        'Prueba gratuita ($300, 90 días) y límites mensuales; el de Cloud Storage solo en tres regiones de EE. UU.',
        'Presupuestos: umbrales 50, 90 y 100 %; no cortan el gasto.',
        'Jerarquía de recursos, WIF, y las siete «R» de AWS.']) + '''</div>
 <div class="card"><h3 class="malc">Sin verificar o sin dato</h3>''' + lista([
        '**Sin ejecutar** en Google Cloud: ninguna orden de esta clase (hay plantillas).',
        'Cuota de mercado, número de regiones y precios de los proveedores: **sin dato**.',
        'GKE y Dataproc en São Paulo, y Cloud Logging: **sin dato** (en Santiago se comprobaron el 25/11/2026).',
        'Modelos de Gemini disponibles en São Paulo: **sin dato**.',
        'Coste de un endpoint de Vertex AI y horas de cada migración: **sin dato**.',
        'Nombres de producto de AWS y Azure: de sus documentaciones, pero no se comprobó cada fila.']) + '''</div>
</div>
<div class="callout" style="margin-top:12px">Los servicios, las regiones y las condiciones de la nube <b>cambian</b>. Antes de impartir o de decidir: volver a mirar las páginas citadas en las notas del ponente (tecla <b>S</b>).</div>''',
          'Diapositiva de honestidad. La lista de lo comprobado corresponde a páginas de documentación oficial leídas el 25/11/2026; ninguna orden se ejecutó contra Google Cloud para preparar esta clase. Lo no comprobado se dice sin dato. Las fuentes con dirección están en las notas de cada diapositiva y reunidas en guia.md.')

    slide('G', 5, 'Autoevaluación', 'comprueba que lo tienes', 'Seis preguntas', '<div class="grid3">' + ''.join(
        f'<div class="card"><h3>{i}. {md(p)}</h3><p class="small">{md(r)}</p></div>' for i, (p, r) in enumerate([
            ('¿Qué diferencia hay entre CAPEX y OPEX?', 'CAPEX es la inversión inicial en equipos (on-premise); OPEX, el gasto corriente por uso (nube).'),
            ('¿Por qué Cloud Run es «serverless»?', 'No gestionas servidores: subes una imagen, escala con las peticiones y puede bajar a cero.'),
            ('¿Qué cambia al pasar de claves a WIF?', 'Ya no hay claves guardadas: GitHub presenta un token temporal y Google lo cambia por acceso de una cuenta de servicio.'),
            ('¿Qué estrategia aplica a la imagen de la API y cuál a SQLite?', '**Rehost** para la imagen (se mueve tal cual); **replatform** para SQLite a BigQuery.'),
            ('¿Un presupuesto con alertas evita pasarse de gasto?', 'No: solo avisa. Hay que actuar, y apagar no es borrar.'),
            ('¿Qué falta en Santiago respecto a São Paulo en Vertex AI?', 'Model Monitoring, Experiments y Explainable AI no figuran en Santiago; Gemini no se lista allí.')], 1)) + '</div>',
          'Lea cada pregunta y deje que respondan antes de leer la respuesta. La sexta se contesta con la diapositiva de regiones, cuya fuente es la documentación de ubicaciones de Vertex AI y de Gemini consultada el 25/11/2026. La tercera enlaza con la diapositiva de identidad y la quinta con la de presupuestos.')

    slide('G', 4, 'Cierre', 'el mensaje', 'A la nube se llega pieza a pieza, con presupuesto y borrando al final', '''
<div class="msg">Mover algo a la nube <b>no es copiarlo</b>: es elegir, <b>pieza a pieza</b>, qué servicio la sustituye, cómo se valida y cuánto cuesta, y <b>borrar</b> al final lo que ya no sirve.</div>
<div class="grid4" style="margin-top:18px">
 ''' + kpi('3 zonas', 'tiene la región `southamerica-west1` (Santiago): `-a`, `-b` y `-c`') +
          kpi('90 días', 'de validez del crédito de la prueba gratuita pública de Google Cloud') +
          kpi('0 claves', 'guardadas en GitHub si se entra con **Workload Identity Federation**') +
          kpi('50 · 90 · 100 %', 'umbrales por defecto de un presupuesto con alertas: avisan, **no cortan**') + '''
</div>
<div style="text-align:center;margin-top:44px;font-size:44px;font-weight:700;color:var(--acento)">¿Preguntas?</div>''',
          'Cierre con un único mensaje. Las cuatro tarjetas son comprobables: las tres zonas de southamerica-west1 vienen de la tabla de regiones y zonas de Compute Engine; los 90 días, de la documentación pública de la prueba gratuita; las cero claves, de la descripción de Workload Identity Federation; y los umbrales 50, 90 y 100 por ciento, de la documentación de presupuestos. ' + fte('ce', 'free', 'wif', 'budgets') + ' Siguiente paso en el curso: la práctica guiada de S4 y la operación del modelo en S5.')


# ======================================================================================================================
# Guía en prosa (se genera del mismo contenido que las diapositivas)
# ======================================================================================================================
class _AMd(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.linea = ''
        self.omitir = 0       # dentro de svg o de un botón
        self.celda = None
        self.fila = None
        self.filas = []
        self.en_code = False
        self.en_h3 = False
        self.paso = False

    def _flush(self):
        t = re.sub(r'\s+', ' ', self.linea).strip()
        if t:
            self.out.append(t)
        self.linea = ''

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'svg':
            self._flush()
            self.out.append('*Esquema: ' + a.get('aria-label', '') + '*')
            self.omitir += 1
            return
        if self.omitir:
            if tag in ('button', 'foreignobject'):
                self.omitir += 1
            return
        if tag == 'button':
            self.omitir += 1
        elif tag == 'table':
            self._flush()
            self.filas = []
        elif tag == 'tr':
            self.fila = []
        elif tag in ('td', 'th'):
            self.celda = ''
        elif tag in ('p', 'div', 'ul', 'ol', 'section', 'h4'):
            self._flush()
        elif tag == 'li' or (tag == 'span' and 'paso' in (a.get('class') or '')):
            self._flush()
            self.linea = '- '
            self.paso = tag == 'span'
        elif tag == 'h3':
            self._flush()
            self.en_h3 = True
            self.linea = '**'
        elif tag == 'code':
            self.en_code = True
            self.linea += '`'
        elif tag == 'b':
            self.linea += '**' if self.celda is None else ''
        elif tag == 'br':
            self._flush()

    def handle_endtag(self, tag):
        if tag in ('svg',):
            self.omitir -= 1
            return
        if self.omitir:
            if tag in ('button', 'foreignobject'):
                self.omitir -= 1
            return
        if tag in ('td', 'th'):
            if self.fila is not None:
                self.fila.append(re.sub(r'\s+', ' ', self.celda or '').strip().replace('|', '/'))
            self.celda = None
        elif tag == 'tr':
            if self.fila:
                self.filas.append(self.fila)
            self.fila = None
        elif tag == 'table':
            lineas = []
            for i, f in enumerate(self.filas):
                lineas.append('| ' + ' | '.join(f) + ' |')
                if i == 0:
                    lineas.append('|' + '---|' * len(f))
            self.out.append('\n'.join(lineas))
            self.filas = []
        elif tag == 'h3':
            self.linea += '**'
            self.en_h3 = False
            self._flush()
        elif tag == 'code':
            self.linea += '`'
            self.en_code = False
        elif tag == 'b':
            self.linea += '**' if self.celda is None else ''
        elif tag in ('p', 'div', 'ul', 'ol', 'li', 'section', 'h4'):
            self._flush()
        elif tag == 'span' and self.linea.startswith('- ') and self.celda is None:
            self._flush()

    def handle_data(self, data):
        if self.omitir:
            return
        if self.celda is not None:
            self.celda += data
        else:
            self.linea += data


def a_markdown(cuerpo):
    p = _AMd()
    p.feed(cuerpo)
    p._flush()
    return '\n\n'.join(p.out)


def guia_md():
    construir()
    ordenes = '\n'.join(f'    {v}' for v in O.values())
    partes = []
    cab = ['# De on-premise a la nube', '',
           'Guía en texto de la clase de apoyo «De on-premise a la nube» del curso «ML e IA: de desarrollo a producción». Es el mismo contenido que la presentación (`index.html`), con las notas del ponente al final de cada apartado. Los nombres, regiones y condiciones de Google Cloud se consultaron en su documentación pública el '
           + CONSULTA + '; lo que no se pudo comprobar dice «sin dato». **Nada de lo que aquí aparece se ha ejecutado en Google Cloud**: las órdenes son plantillas.', '']
    n = 0
    actual = None
    for parte, titulo, h1, cuerpo, notas in GUIA:
        n += 1
        if parte != actual:
            actual = parte
            partes.append(f'## {list(PARTES).index(parte) + 1}. {NOMBRES_PARTE[parte]}\n')
        partes.append(f'### {n}. {re.sub(r"[*`]", "", h1)}\n')
        partes.append(a_markdown(cuerpo) + '\n')
        partes.append('> **Para el ponente.** ' + notas + '\n')
    fin = ['## Fuentes consultadas (' + CONSULTA + ')', ''] + [f'- {n_}: <{u}>' for n_, u in FUENTES.values()]
    return '\n'.join(cab + partes + fin) + '\n'


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
.slide{position:absolute;inset:0;padding:30px 52px 46px;display:none;flex-direction:column;gap:10px;overflow:hidden}
.slide.active{display:flex}
.kick{font-size:13px;letter-spacing:.09em;text-transform:uppercase;color:var(--acento);font-weight:700}
h1{font-size:31px;line-height:1.15;font-weight:700;margin-bottom:4px}
h3{font-size:17px;margin-bottom:5px}
.sub{font-size:22px;line-height:1.4;color:var(--suave);max-width:1050px}
.cover{display:flex;flex-direction:column;justify-content:flex-start;padding-top:110px;flex:1}
.chips{display:flex;gap:8px;margin-top:18px;flex-wrap:wrap}
.tag{display:inline-block;font-size:13px;padding:2px 10px;border-radius:999px;border:1px solid var(--linea);background:var(--gris);color:var(--tinta)}
.tag.ok{border-color:#86c79c;background:#ecf8f0;color:var(--ok)}.tag.warn{border-color:#e2b56b;background:#fdf6e9;color:var(--aviso)}.tag.mal{border-color:#e0a3a3;background:#fdeeee;color:var(--mal)}
.card{border:1px solid var(--linea);border-radius:12px;padding:10px 14px;background:#fff}
.callout{border-left:4px solid var(--acento);background:#eef5fc;padding:9px 14px;border-radius:0 10px 10px 0;font-size:15.5px;line-height:1.4}
.small{font-size:15px;line-height:1.42}
.mono{font-family:var(--mono);font-size:.92em;background:var(--gris);padding:0 4px;border-radius:4px}
.okc{color:var(--ok)}.malc{color:var(--mal)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.split{display:grid;gap:18px;min-height:0}.col{display:flex;flex-direction:column;gap:9px;min-width:0}
.list{list-style:none;display:flex;flex-direction:column;gap:4px}.list li{font-size:15px;line-height:1.38;padding-left:16px;position:relative}
.list li::before{content:"";position:absolute;left:2px;top:8px;width:6px;height:6px;border-radius:50%;background:var(--acento)}
.ol{padding-left:24px;display:flex;flex-direction:column;gap:6px;font-size:17px}
.tbl{width:100%;border-collapse:collapse;font-size:14.5px}.tbl th{text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--suave);border-bottom:2px solid var(--linea);padding:5px 8px}
.tbl td{border-bottom:1px solid var(--linea);padding:6px 8px;line-height:1.35;vertical-align:top}
.tbl.eq td{padding:9px 8px;font-size:15.5px}.tbl.eq td:last-child{background:#eef5fc}
.tbl.capas td,.tbl.capas th{text-align:center;font-size:13.5px;padding:7px 5px}.tbl.capas td:first-child,.tbl.capas th:first-child{text-align:left}
.tbl.capas .tu{background:#dbeafe;color:#1e3a8a}.tbl.capas .pv{background:#eceff3;color:#4b5563}.tbl.capas tr.ej td{font-size:12px;color:var(--suave);vertical-align:top}
.lg{display:inline-block;width:14px;height:14px;border-radius:3px;vertical-align:-2px;border:1px solid var(--linea)}.lg.tu{background:#dbeafe}.lg.pv{background:#eceff3}
.term{border:1px solid var(--linea);border-radius:10px;background:var(--gris);overflow:hidden}
.term .bar{display:flex;align-items:center;gap:8px;padding:5px 10px;border-bottom:1px solid var(--linea);background:#eaeef3}
.term .bar em{flex:1;font-style:normal;font-size:12.5px;color:var(--suave)}
.tls{padding:6px 8px;font-family:var(--mono);font-size:12.5px;line-height:1.42}
.tln{display:flex;align-items:flex-start;gap:6px;padding:2px 4px}
.tln code{flex:1;white-space:pre-wrap;overflow-wrap:anywhere;font-family:var(--mono)}
.tln.c{color:var(--suave);font-style:italic}
.ps{color:var(--ok);font-weight:700}
.cp{flex:none;min-width:26px;height:24px;border-radius:6px;border:1px solid #b9c3cf;background:#fff;font-size:13px;color:var(--suave)}
.cp.ok{border-color:var(--ok);color:var(--ok)}.cpall{padding:0 10px;font-size:12px;font-family:var(--sans)}
.ficha{border-top:4px solid var(--acento);display:flex;flex-direction:column;gap:5px}.ficha h3{margin-bottom:2px;font-size:18px}
.ficha .fr{font-size:14.5px;line-height:1.38}.ficha .fr .lb{display:block;font-weight:700;font-size:11.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--suave)}
.ficha.c1{border-top-color:#0e7490}.ficha.c2{border-top-color:#0b5cad}.ficha.c3{border-top-color:#6d28d9}.ficha.c4{border-top-color:#15803d}.ficha.c5{border-top-color:#b45309}
.mapa{display:grid;grid-template-columns:1fr 1.15fr 1fr 1.05fr 1fr;gap:10px}
.mapa .gr{border:1px solid var(--linea);border-radius:12px;padding:10px;display:flex;flex-direction:column;gap:7px;border-top:5px solid var(--acento)}
.mapa .g1{border-top-color:#0e7490}.mapa .g2{border-top-color:#0b5cad}.mapa .g3{border-top-color:#6d28d9}.mapa .g4{border-top-color:#15803d}.mapa .g5{border-top-color:#b45309}
.mapa h4{font-size:14px;margin-bottom:2px}
.mapa .t{background:var(--gris);border-radius:8px;padding:8px 9px;font-weight:700;font-size:15px;line-height:1.2}.mapa .t small{display:block;font-weight:400;font-size:12.5px;color:var(--suave);margin-top:2px}
.ruta{display:flex;gap:8px;flex-wrap:wrap}.paso{background:#eef5fc;border:1px solid #bcd3ec;border-radius:999px;padding:5px 14px;font-size:15px;color:var(--acento);font-weight:600}
.prov{border-top:5px solid var(--acento)}.prov h3{font-size:19px}.prov p{margin-bottom:6px}
.regionbox{background:#eef5fc;border:1px solid #bcd3ec;border-radius:10px;padding:8px 12px;font-size:15px;margin-bottom:5px}
.zonas{display:flex;gap:8px;margin-top:6px}.zonas span{flex:1;text-align:center;background:#fff;border:1px solid #8fb2d6;border-radius:8px;padding:6px 0;font-family:var(--mono);font-size:14px}
.rgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.r{border:1px solid var(--linea);border-radius:12px;padding:10px 14px;border-left:6px solid var(--acento)}.r h3{font-size:18px}.r p{margin-bottom:4px}
.r1{border-left-color:#15803d}.r2{border-left-color:#0b5cad}.r3{border-left-color:#6d28d9}.r4,.r5,.r6x{border-left-color:#9aa5b4}.r.r6{border-left-color:#9aa5b4}
.regla h3{font-size:19px}.regla .num{display:inline-block;width:28px;height:28px;border-radius:50%;background:var(--acento);color:#fff;text-align:center;line-height:28px;font-size:16px;margin-right:6px}
.regla{min-height:175px}.regla .small{font-size:18px}.grande .regla .small{font-size:18px}
.grande .small{font-size:17px}.grande .list li{font-size:16.5px}.grande .tbl{font-size:16px}.grande .tbl td{padding:9px 10px}.grande .callout{font-size:17.5px}.grande .card{padding:13px 17px}.grande .ol{font-size:19px}.grande h3{font-size:19px}.grande .ficha .fr{font-size:15.5px}.grande .ficha h3{font-size:20px}.grande .mapa .t{font-size:16.5px;padding:10px}.grande .mapa .t small{font-size:13.5px}.grande .mapa h4{font-size:15.5px}.grande .tbl.capas td,.grande .tbl.capas th{font-size:14.5px;padding:10px 5px}.grande .tbl.capas tr.ej td{font-size:12.5px}.grande .tls{font-size:13.5px}.grande .term .bar em{font-size:13px}.grande .r p{font-size:16px}.grande .grid3,.grande .grid2{gap:14px}.grande .tbl.eq td{padding:12px 8px;font-size:16.5px}
.grande .grid4 .kpi{min-height:230px;padding-top:20px}.grande .grid4 .kpi .small{font-size:19px}.grande .grid4{margin-top:36px!important}.grande .kpi .n{font-size:30px}.grande .msg{font-size:30px}
.kpi .n{display:block;font-size:27px;line-height:1.15;color:var(--acento);margin-bottom:4px}.kpi .n.okc{color:var(--ok)}.kpi .n.malc{color:var(--mal)}
.msg{font-size:27px;line-height:1.3;font-weight:600;border-left:6px solid var(--acento);padding:12px 20px;background:#eef5fc;border-radius:0 12px 12px 0}
svg .nodo{fill:#f4f8fc;stroke:#8fb2d6;stroke-width:1.5}svg .nodo.puerta{fill:#fdf6e9;stroke:#c9a65e;stroke-dasharray:6 4}svg .nodo.ok{fill:#ecf8f0;stroke:var(--ok)}svg .nodo.mal{fill:#fdeeee;stroke:var(--mal)}svg .nodo.gcp{fill:#e4effb;stroke:#0b5cad}
svg .zona{fill:#fbfcfe;stroke:#8fb2d6;stroke-dasharray:6 4;stroke-width:1.5}
svg .fl{stroke:var(--acento);stroke-width:2;fill:none}svg .fl.dis{stroke-dasharray:5 4;stroke:#8fb2d6}svg .fl.cap{stroke:var(--mal);stroke-dasharray:7 4;stroke-width:2.2}
svg .eje{stroke:#8a94a3;stroke-width:1.5;fill:none}svg .curva{stroke:var(--acento);stroke-width:3;fill:none}svg .area{fill:#dbeafe}svg .ocio{fill:#fde6e6}
svg .t1{font:700 15px var(--sans);fill:var(--tinta);text-anchor:middle}svg .t2{font:13px var(--sans);fill:var(--suave);text-anchor:middle}svg .t3{font:13px var(--sans);fill:var(--suave);text-anchor:middle}
svg .izq{text-anchor:start}svg .t2.mal{fill:var(--mal);font-weight:700}svg .t2.ok{fill:var(--ok);font-weight:700}
svg .fo{font:13px var(--sans);color:var(--suave);text-align:center;line-height:1.25}
.card svg{display:block;width:100%;height:auto}
.foot{position:absolute;left:52px;right:52px;bottom:14px;display:flex;justify-content:space-between;font-size:12px;color:var(--suave);border-top:1px solid var(--linea);padding-top:6px}
#prog{position:fixed;left:0;top:0;height:3px;background:var(--acento);z-index:5}
#bar{position:fixed;left:0;right:0;bottom:0;height:48px;display:flex;align-items:center;gap:6px;padding:0 12px;background:#fff;border-top:1px solid var(--linea);font-size:13px;z-index:6}
#bar button,#bar a{border:1px solid var(--linea);border-radius:8px;padding:4px 10px;background:#fff;color:var(--tinta);text-decoration:none;font-size:13px}
#bar .part.on{border-color:var(--acento);color:var(--acento);font-weight:700}
#bar .sp{flex:1}#count,#clockref{color:var(--suave);padding:0 6px}
#notes{position:fixed;right:0;top:0;bottom:48px;width:400px;background:#fff;border-left:1px solid var(--linea);padding:18px;overflow:auto;display:none;z-index:7;font-size:15px;line-height:1.5}
#notes.on{display:block}#notes h3{margin-bottom:8px}
#index{position:fixed;inset:0 0 48px 0;background:rgba(255,255,255,.98);display:none;z-index:8;padding:28px;overflow:auto}
#index.on{display:block}#index .grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:12px}
#index button{border:1px solid var(--linea);border-radius:10px;padding:10px;text-align:left;font-size:14px;background:#fff}
#index button small{display:block;color:var(--suave);font-size:12px}#index button.cur{border-color:var(--acento)}
@media print{#bar,#notes,#index,#prog,.cp{display:none!important}}
"""

JS = r"""
(function(){
'use strict';
const $=(s,r)=>(r||document).querySelector(s), $$=(s,r)=>[...(r||document).querySelectorAll(s)];
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const PARTES=__PARTES__;
async function copyText(t){try{await navigator.clipboard.writeText(t);return true}catch(e){try{const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();document.execCommand('copy');a.remove();return true}catch(e2){return false}}}
const slides=$$('.slide'), N=slides.length; let cur=0;
slides.forEach((s,i)=>{const f=document.createElement('div');f.className='foot';
  f.innerHTML=`<span>ML e IA · S4 · De on-premise a la nube</span><span><b>${esc(PARTES[s.dataset.part]||'')}</b> · ${i+1} / ${N}</span>`;s.appendChild(f)});
const cum=[];(()=>{let t=0;slides.forEach(s=>{cum.push(t);t+=+s.dataset.min||0})})();
const TOTAL=cum[N-1]+(+slides[N-1].dataset.min||0);
function go(i){i=Math.max(0,Math.min(N-1,i));cur=i;slides.forEach((s,k)=>s.classList.toggle('active',k===i));chrome();try{history.replaceState(null,'','#'+(i+1))}catch(e){}}
function chrome(){const s=slides[cur];
  $('#count').textContent=(cur+1)+' / '+N; $('#clockref').textContent='min '+cum[cur]+' de '+TOTAL+' (propuesta)';
  $('#prog').style.width=((cur+1)/N*100)+'%';
  $$('#bar .part').forEach(b=>b.classList.toggle('on',b.dataset.p===s.dataset.part));
  $('#notetext').innerHTML='<p>'+esc(s.dataset.notes||'')+'</p>';
  $('#notemin').textContent='Tiempo previsto (propuesta): '+(s.dataset.min||0)+' min · acumulado '+cum[cur]+' min de '+TOTAL;
  $$('#idxgrid button').forEach((b,k)=>b.classList.toggle('cur',k===cur));}
function fit(){const v=$('#viewport');$('#stage').style.setProperty('--s',Math.min(v.clientWidth/1280,v.clientHeight/720).toFixed(4))}
addEventListener('resize',fit);
$('#idxgrid').innerHTML=slides.map((s,i)=>`<button data-i="${i}"><small>${esc(PARTES[s.dataset.part]||'')} · ${s.dataset.min||0} min</small>${i+1}. ${esc(s.dataset.title||'')}</button>`).join('');
$('#idxgrid').addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;toggle('#index',false);go(+b.dataset.i)});
function toggle(sel,force){$(sel).classList.toggle('on',force)}
$('#bprev').onclick=()=>go(cur-1); $('#bnext').onclick=()=>go(cur+1);
$('#bidx').onclick=()=>toggle('#index'); $('#bnotes').onclick=()=>toggle('#notes');
$('#bfull').onclick=()=>{if(document.fullscreenElement)document.exitFullscreen();else document.documentElement.requestFullscreen&&document.documentElement.requestFullscreen()};
$$('#bar .part').forEach(b=>b.onclick=()=>go(slides.findIndex(s=>s.dataset.part===b.dataset.p)));
addEventListener('keydown',e=>{
  const t=e.target; if(t&&/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)) return;
  if(e.ctrlKey||e.metaKey||e.altKey) return;
  const k=e.key;
  if(k==='Escape'){toggle('#index',false);toggle('#notes',false);return}
  if(k==='ArrowRight'||k==='PageDown'||(k===' '&&!/^(BUTTON|A)$/.test(t.tagName))){e.preventDefault();go(cur+1)}
  else if(k==='ArrowLeft'||k==='PageUp'){e.preventDefault();go(cur-1)}
  else if(k==='Home'){e.preventDefault();go(0)} else if(k==='End'){e.preventDefault();go(N-1)}
  else if(k==='o'||k==='O'){toggle('#index')} else if(k==='s'||k==='S'){toggle('#notes')} else if(k==='f'||k==='F'){$('#bfull').click()}
});
let tx=null;
addEventListener('touchstart',e=>{tx=e.touches[0].clientX},{passive:true});
addEventListener('touchend',e=>{if(tx===null)return;const dx=e.changedTouches[0].clientX-tx;tx=null;if(Math.abs(dx)>60){dx<0?go(cur+1):go(cur-1)}},{passive:true});
document.addEventListener('click',async e=>{
  const b=e.target.closest('.cp'); if(!b) return; e.stopPropagation();
  const ok=await copyText(b.dataset.t); const t=b.textContent; b.classList.add('ok'); b.textContent=ok?'✓':'✗'; setTimeout(()=>{b.classList.remove('ok');b.textContent=t},1200)});
fit();
const h=parseInt((location.hash||'').slice(1),10); go(isNaN(h)?0:h-1);
addEventListener('hashchange',()=>{const n=parseInt((location.hash||'').slice(1),10);if(!isNaN(n)&&n-1!==cur)go(n-1)});
})();
"""


def html_completo():
    construir()
    js = JS.replace('__PARTES__', json.dumps(PARTES, ensure_ascii=False))
    partes = ''.join(f'<button class="part" data-p="{k}">{esc(v)}</button>' for k, v in PARTES.items())
    return ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>De on-premise a la nube · ML e IA: de desarrollo a producción</title>\n'
            f'<!-- Generado por generar.py: no se edita a mano. -->\n<style>{CSS}</style>\n</head>\n<body>\n'
            '<div id="prog"></div>\n<div id="viewport"><div id="stage">\n\n' + '\n\n'.join(SLIDES) + '\n\n</div></div>\n\n'
            '<aside id="notes" aria-label="Notas del ponente"><h3>Notas del ponente</h3><div id="notetext"></div><p class="small" id="notemin"></p></aside>\n'
            '<div id="index" aria-label="Índice"><h2>Índice</h2><div class="grid" id="idxgrid"></div></div>\n'
            '<nav id="bar" aria-label="Controles">\n'
            '  <button id="bprev" aria-label="Anterior">←</button><button id="bnext" aria-label="Siguiente">→</button>\n'
            f'  <span id="count">1 / 1</span><span id="clockref" title="Minuto planificado acumulado (propuesta)"></span>\n  {partes}\n'
            '  <span class="sp"></span>\n'
            '  <a id="bhome" href="../index.html" title="Volver al índice de la sesión S4">⌂ S4</a><button id="bidx">Índice (O)</button><button id="bnotes">Notas (S)</button><button id="bfull">Pantalla completa (F)</button>\n'
            '</nav>\n'
            '<noscript>Esta presentación necesita JavaScript. El mismo contenido está en guia.md, en esta carpeta.</noscript>\n\n'
            f'<script>{js}</script>\n</body>\n</html>\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--comprobar', action='store_true')
    a = ap.parse_args()
    nuevo = html_completo()
    guia = guia_md()
    pares = [(SALIDA, nuevo), (SALIDA_GUIA, guia)]
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
