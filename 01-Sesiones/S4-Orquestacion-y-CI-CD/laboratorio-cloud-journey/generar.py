"""Genera la presentación «Laboratorio Cloud Journey: la API en Google Cloud sin claves» (index.html, junto a este archivo).

Práctica de S4 del curso «ML e IA: de desarrollo a producción»: se lleva la API de retención desde GitHub Actions y GHCR hasta
Artifact Registry y Cloud Run, entrando en Google Cloud SIN CLAVES (Workload Identity Federation) y con aprobación humana; se
prueba la URL pública, se enlaza el modelo en Vertex AI (práctica 04) y se BORRA todo al terminar.

Mismo manejo que los demás laboratorios (← → · O índice · S notas · F pantalla completa · Esc), con fondo blanco y nada que
se mueva al pasar el ratón. Cada orden lleva ⧉ para copiarla. Las capturas se leen de img/ con los nombres de CAPTURAS; si
falta alguna, se dibuja un recuadro «Captura pendiente» (no falla).

Uso:  python generar.py              escribe index.html
      python generar.py --comprobar  no escribe; sale con 1 si index.html no está al día
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / 'index.html'
FECHA = '25/11/2026'
USUARIO = 'helicr'
REPO = 'curso-ml-ia-desarrollo-produccion'
CARPETA = '01-Sesiones/S4-Orquestacion-y-CI-CD/laboratorio-cloud-journey'
RAMA = 'lab/cloud-journey/despliegue'
RUN = '45519881368'
RUN_URL = f'https://github.com/{USUARIO}/{REPO}/actions/runs/{RUN}'
PROYECTO = 'project-curso-ml-ia'
REGION = 'southamerica-west1'
NUMERO = '61343545797'
WIF = f'projects/{NUMERO}/locations/global/workloadIdentityPools/github/providers/github'
SA_DESPLIEGUE = f'sa-github-despliegue@{PROYECTO}.iam.gserviceaccount.com'
SA_SERVICIO = f'sa-cloudrun-retencion@{PROYECTO}.iam.gserviceaccount.com'
VARIABLES = [('GCP_PROYECTO', PROYECTO), ('GCP_REGION', REGION), ('GCP_PROVEEDOR_WIF', WIF),
             ('GCP_CUENTA_DESPLIEGUE', SA_DESPLIEGUE), ('GCP_CUENTA_SERVICIO', SA_SERVICIO)]
PENDIENTES = []     # ya están todas las capturas; si falta alguna en img/, la diapositiva dibuja «Captura pendiente»

# Capturas (webp). Nombre -> qué se ve de verdad (texto alternativo y pie).
CAPTURAS = {
    'gcp-01-proyectos.webp': 'Consola de Google Cloud, «Administra recursos»: la organización del curso con tres proyectos, entre ellos project-curso-ml-ia, y los botones Crear proyecto y Crear carpeta',
    'gcp-02-facturacion.webp': 'Administración de la cuenta de facturación: una cuenta «Mi cuenta de facturación», de tipo Directa, estado Activo y gasto de los últimos 30 días de 0 euros',
    'gcp-03-facturacion-proyecto.webp': 'Facturación del proyecto project-curso-ml-ia: «Este proyecto no tiene cuenta de facturación» y los botones «Vincular una cuenta de facturación» y «Administrar cuentas de facturación»',
    'gcp-20-cloudshell.webp': 'Cloud Shell abierto: «Your Cloud Platform project in this session is set to project-curso-ml-ia» y el prompt con el proyecto entre paréntesis',
    'gcp-23-preparar.webp': 'Salida real de preparar-gcp-s4.sh en Cloud Shell: los pasos 1 a 7, las cinco variables GCP_ y al final «FIN · todo listo»',
    'gcp-12-politica-claves.webp': 'Política de la organización «Inhabilitar la creación de claves de cuentas de servicio» (iam.disableServiceAccountKeyCreation): heredada, estado Aplicada',
    'gcp-09-cuentas-servicio.webp': 'IAM > Cuentas de servicio del proyecto, antes del script: solo sa-curso-ml-ia, habilitada y con «No hay claves» en la columna ID de clave',
    'gcp-11-wif.webp': 'IAM > Grupos de Workload Identity, antes del script: la pantalla de bienvenida con los cuatro pasos y el botón Comenzar (aún no hay ningún pool)',
    'gcp-24-ar-y-politicas.webp': 'Cloud Shell: «Created repository [curso]», la política que permite allUsers (allValues: ALLOW) y Vertex AI respondiendo en southamerica-west1 («Listed 0 items»)',
    'cj-01-variables-github.webp': 'GitHub, Settings > Secrets and variables > Actions > pestaña Variables: las Repository variables GCP_CUENTA_DESPLIEGUE, GCP_CUENTA_SERVICIO, GCP_PROVEEDOR_WIF y GCP_PROYECTO',
    'gh-01-esperando-aprobacion.webp': 'Run en espera: aviso amarillo «helicr requested your review to deploy to produccion» con el botón Review deployments; trabajos 1 y 2 en verde y el 3 esperando',
    'cj-02-run-desplegado.webp': 'Run «Ensayo Cloud Journey» en verde: éxito, duración total 8 m 32 s, rama lab/cloud-journey/despliegue; trabajo 1 de 1 min 49 s y trabajo 2 de 1 min 16 s',
    'cj-03-resumen-cloudrun.webp': 'Resumen del trabajo 2: imagen en southamerica-west1-docker.pkg.dev/project-curso-ml-ia/curso/retencion-api, la URL de run.app, la cuenta de servicio sin permisos y la entrada sin claves',
    'cj-04-cloudrun-consola.webp': 'Consola de Google Cloud, Cloud Run › Detalles del servicio: retencion-api con la marca verde, su URL pública https://retencion-api-61343545797.southamerica-west1.run.app, la región southamerica-west1 y la pestaña Observabilidad con las métricas (recuento de solicitudes con respuestas 2xx, latencias)',
    'cj-05-artifact-registry.webp': 'Consola de Google Cloud, Artifact Registry › repositorio curso › paquete retencion-api (southamerica-west1): tres versiones creadas hace 1 hora, una con una etiqueta hexadecimal de 40 caracteres (la del commit), otra de 174.8 MB y otra de 1.4 KB',
    'cj-06-vertex-modelo.webp': 'Consola de Google Cloud, Plataforma de Gemini › Modelos › Registro de modelos, región southamerica-west1 (Santiago): un modelo cuyo nombre se corta en «retencion-» (es retencion-90d-sklearn), versión 1, estado Implementado, tipo Importado, origen Entrenamiento personalizado',
    'cj-07-vertex-endpoint.webp': 'Consola de Google Cloud, Plataforma de Gemini › Modelos › Extremos (los endpoints), región southamerica-west1 (Santiago): el extremo retencion-90d-endpoint en estado Activo, con 1 modelo y supervisión Inhabilitada',
    'cj-08-borrado.webp': 'Cloud Shell, final de borrar-gcp-s4.sh: proveedor y pool de WIF borrados, presupuesto «Curso ML e IA» borrado, «Se deja vinculada» la facturación, Cloud Run y Artifact Registry con «Listed 0 items», solo sa-curso-ml-ia y la cuenta de Compute por defecto entre las cuentas de servicio, y «FIN · borrado terminado»',
}

# Órdenes que se copian (clave -> orden). La guía las repite tal cual y las pruebas lo comprueban.
O = {
    # Cloud Shell
    'usuario_gh': 'USUARIO_GH=tu-usuario-de-github',
    'clonar': f'git clone -q --depth 1 -b develop https://github.com/$USUARIO_GH/{REPO}.git curso',
    'cd_lab': f'cd ~/curso/{CARPETA}',
    'cuentas_fact': 'gcloud billing accounts list',
    'editar': 'nano preparar-gcp-s4.sh',
    'ver_valores': "grep -nE '^(PROYECTO|FACTURACION|REPO_GITHUB)=' preparar-gcp-s4.sh",
    'preparar': 'bash preparar-gcp-s4.sh',
    'crear_ar': f'gcloud artifacts repositories create curso --repository-format=docker --location={REGION} --description="Imagenes del curso"',
    'listar_ar': f'gcloud artifacts repositories list --location={REGION}',
    'politica_allusers': f'gcloud resource-manager org-policies describe iam.allowedPolicyMemberDomains --project={PROYECTO} --effective',
    # tu terminal o Codespace (bash)
    'switch_develop': 'git switch develop',
    'pull': 'git pull',
    'rama': f'git switch -c {RAMA}',
    'mkdir': 'mkdir -p .github/workflows',
    'cp': f'cp {CARPETA}/desplegar-gcp.yml .github/workflows/',
    'add': 'git add .github/workflows/desplegar-gcp.yml',
    'commit': 'git commit -m "Ensayo Cloud Journey: desplegar la API en Cloud Run con WIF"',
    'push': f'git push -u origin {RAMA}',
    # Windows PowerShell 5.1
    'ps_mkdir': 'New-Item -ItemType Directory -Force .github/workflows',
    'ps_cp': f'Copy-Item {CARPETA}/desplegar-gcp.yml .github/workflows/',
    # probar
    'url': f"URL=$(gcloud run services describe retencion-api --region={REGION} --format='value(status.url)')",
    'cd_base': 'cd ~/curso/04-Proyecto-Base',
    'salud': 'curl -fsS "$URL/salud"',
    'listo': 'curl -fsS "$URL/listo"',
    'predecir': "curl -fsS -X POST \"$URL/predecir\" -H 'content-type: application/json' -d @tests/datos/cliente_ejemplo.json",
    'ps_url': '$URL = "https://retencion-api-XXXX.a.run.app"',
    'ps_salud': 'Invoke-WebRequest -UseBasicParsing "$URL/salud" | Select-Object -ExpandProperty Content',
    'ps_listo': 'Invoke-WebRequest -UseBasicParsing "$URL/listo" | Select-Object -ExpandProperty Content',
    'ps_predecir': ('Invoke-WebRequest -UseBasicParsing -Method Post -Uri "$URL/predecir" -ContentType "application/json" '
                    '-InFile 04-Proyecto-Base/tests/datos/cliente_ejemplo.json | Select-Object -ExpandProperty Content'),
    # Vertex AI (práctica 04)
    'cd_vertex': 'cd ~/curso/01-Sesiones/S4-Orquestacion-y-CI-CD/practicas-gcp/04-vertex-modelo',
    'vertex_crear': 'bash crear.sh',
    'vertex_probar': 'bash probar.sh',
    'vertex_borrar': 'bash borrar.sh',
    # borrar
    'borrar': 'bash borrar-gcp-s4.sh',
    'borrar_desv': 'DESVINCULAR_FACTURACION=si bash borrar-gcp-s4.sh',
}

PARTES = {'A': 'Plan', 'B': 'Google Cloud', 'C': 'GitHub', 'D': 'Desplegar', 'E': 'Probar', 'F': 'Vertex AI', 'G': 'Borrar y cierre'}
NOMBRES_PARTE = {'A': 'De dónde partimos y adónde vamos', 'B': 'Preparar Google Cloud', 'C': 'Preparar GitHub',
                 'D': 'Desplegar con aprobación', 'E': 'Probar la API', 'F': 'El modelo en Vertex AI', 'G': 'Borrar y cerrar'}


def esc(t):
    return html.escape(t, quote=True)


def md(t):
    """`código` y **negrita** a HTML (sobre texto ya seguro)."""
    t = esc(t)
    t = re.sub(r'`([^`]+)`', r'<span class="mono">\1</span>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', t)
    return re.sub(r'(?<![\w*])\*([^*\s][^*]*)\*(?![\w*])', r'<i>\1</i>', t)


LUPA = '<svg viewBox="0 0 20 20" width="14" height="14" aria-hidden="true"><circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12.5 12.5 L18 18" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>'


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


def cap(nombre, alto=None, nota=None, titulo=None):
    """Una captura (clic = ampliar) o, si aún no está en img/, el recuadro «Captura pendiente».
    El pie es el texto alternativo salvo que se dé un `titulo` más corto (el texto alternativo se conserva entero)."""
    alt = CAPTURAS[nombre]
    estilo = f' style="max-height:{alto}px"' if alto else ''
    extra = f'<br><span class="nota">{md(nota)}</span>' if nota else ''
    if (AQUI / 'img' / nombre).is_file():
        return (f'<figure class="cap" data-img="{nombre}"><button class="zoom" data-src="img/{nombre}" data-alt="{esc(alt)}" title="Ampliar (Esc cierra)">'
                f'<img src="img/{nombre}" alt="{esc(alt)}"{estilo}><span class="lupa">{LUPA} Ampliar</span></button>'
                f'<figcaption><span class="tag ok">Captura real</span> {md(titulo) if titulo else esc(alt)}{extra}</figcaption></figure>')
    alto_p = f' style="min-height:{min(alto or 200, 260)}px"' if alto else ''
    return (f'<figure class="cap" data-img="{nombre}"><div class="pend"{alto_p}><b>Captura pendiente</b><span class="mono">img/{nombre}</span>'
            f'<span>{esc(alt)}</span></div><figcaption><span class="tag warn">Pendiente</span> {esc(alt)}</figcaption></figure>')


def rotulo_capturas(nombres):
    hay = [n for n in nombres if (AQUI / 'img' / n).is_file()]
    if len(hay) == len(nombres):
        return f'<p class="small rot"><span class="tag ok">Capturas reales</span> cuenta de Google del curso y cuenta del profesor en GitHub (<span class="mono">{USUARIO}</span>) · {FECHA}</p>'
    return '<p class="small rot"><span class="tag warn">Captura pendiente</span> las capturas reales de este paso se añaden en <span class="mono">img/</span></p>'


def lista(items):
    return '<ul class="list">' + ''.join(f'<li>{md(i)}</li>' for i in items) + '</ul>'


def mira(items, titulo='Qué debes ver'):
    return f'<div class="card mira"><h3>{esc(titulo)}</h3>{lista(items)}</div>'


def si_falla(items):
    return f'<div class="card falla"><h3>Si falla</h3>{lista(items)}</div>'


def tabla(cab, filas, clase=''):
    th = ''.join(f'<th>{md(c)}</th>' for c in cab)
    tr = ''.join('<tr>' + ''.join(f'<td>{md(c)}</td>' for c in f) + '</tr>' for f in filas)
    return f'<table class="tbl {clase}"><tr>{th}</tr>{tr}</table>'


def kpi(valor, texto, color=''):
    return f'<div class="card kpi"><b class="n {color}">{esc(valor)}</b><p class="small">{md(texto)}</p></div>'


SLIDES = []
_N = {}
GRANDES = {'El plan', 'Abrir Cloud Shell', 'Ejecutar el script', 'Aprobar el despliegue', 'Probar la API', 'Borrar todo',
           'Costes y lecciones', 'Si algo falla', 'Qué está verificado', 'Cierre'}


def slide(parte, minutos, titulo, kick, h1, cuerpo, notas):
    n = list(PARTES).index(parte) + 1
    _N[parte] = _N.get(parte, 0) + 1
    antetitulo = f'{n} · {NOMBRES_PARTE[parte]} · {kick}'
    attrs = f' data-part="{parte}" data-min="{minutos}" data-title="{esc(titulo)}"'
    clase = ' grande' if titulo in GRANDES else ''
    SLIDES.append(f'<section class="slide{clase}"{attrs}\n data-notes="{esc(notas)}">\n'
                  f'<p class="kick">{esc(antetitulo)}</p><h1>{md(h1)}</h1>\n{cuerpo}\n</section>')


# ======================================================================================================================
# Diagramas (SVG propio, mismo estilo que la clase «De on-premise a la nube»)
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


def svg_asis():
    """Cómo está hoy el caso: todo local o en GitHub; nada en Google Cloud."""
    c = [zona(10, 10, 640, 290, 'Tu equipo o el Codespace'),
         zona(670, 10, 500, 290, 'GitHub'),
         box(30, 60, 180, 76, 'Datos y pipeline', 'Python → SQLite', 'nodo'),
         box(240, 60, 190, 76, 'MLflow y modelo', 'SQLite + carpeta local', 'nodo'),
         box(450, 60, 180, 76, 'Imagen Docker', 'con el modelo dentro', 'nodo'),
         box(450, 190, 180, 76, 'API FastAPI', 'local o Codespace', 'nodo'),
         box(690, 60, 220, 76, 'GitHub Actions', 'construye y prueba', 'nodo'),
         box(930, 60, 220, 76, 'GHCR', 'ghcr.io: las imágenes', 'nodo'),
         box(690, 190, 220, 76, 'Environment «produccion»', 'una persona aprueba', 'nodo puerta'),
         box(930, 190, 220, 76, 'referencia.json', 'versión en producción', 'nodo'),
         flecha('a1', (210, 98), (240, 98)), flecha('a1', (430, 98), (450, 98)), flecha('a1', (540, 136), (540, 190)),
         flecha('a1', (910, 98), (930, 98)), flecha('a1', (800, 190), (800, 136), dis=True), flecha('a1', (910, 228), (930, 228), dis=True),
         txt(590, 328, 'Hoy no hay nada en Google Cloud: todo cabe en una máquina o en GitHub.', 't3')]
    return svg(1180, 346, ''.join(c), 'Arquitectura de hoy: pipeline, SQLite, MLflow, imagen Docker y API en local o Codespace; GitHub Actions publica en GHCR con aprobación; nada en Google Cloud', 'a1')


def svg_tobe():
    """Cómo queda en Google Cloud con la práctica de hoy y con el modelo en Vertex AI."""
    c = [box(10, 70, 200, 70, 'GitHub Actions', 'construye y prueba', 'nodo'),
         box(10, 190, 200, 70, 'Aprobación', 'environment «produccion»', 'nodo puerta'),
         zona(250, 10, 920, 400, f'Proyecto {PROYECTO} · región {REGION} (Santiago)'),
         box(280, 60, 200, 70, 'Cloud Storage', 'bucket del modelo y datos', 'nodo puerta'),
         box(530, 60, 200, 70, 'Vertex AI', 'Model Registry', 'nodo puerta'),
         box(780, 60, 200, 70, 'Vertex AI', 'endpoint online', 'nodo puerta'),
         box(280, 170, 200, 76, 'Artifact Registry', 'repositorio «curso»', 'nodo gcp'),
         box(530, 170, 200, 76, 'Cloud Run', 'retencion-api · mín. 0', 'nodo gcp'),
         box(780, 170, 200, 76, 'Cuenta de servicio', 'sa-cloudrun-retencion', 'nodo ok', 'sin permisos'),
         box(280, 300, 450, 66, 'Workload Identity Federation', 'GitHub entra con su identidad: sin claves', 'nodo ok', 'sa-github-despliegue · permisos mínimos'),
         box(780, 300, 200, 66, 'Presupuesto', '20 € con alertas', 'nodo ok'),
         flecha('b1', (110, 140), (110, 190)), flecha('b1', (380, 300), (380, 246)), flecha('b1', (630, 300), (630, 246)),
         flecha('b1', (480, 208), (530, 208)), flecha('b1', (780, 208), (730, 208)),
         flecha('b1', (210, 225), (230, 225), (230, 333), (280, 333)),
         flecha('b1', (480, 95), (530, 95), dis=True), flecha('b1', (730, 95), (780, 95), dis=True),
         txt(1075, 100, 'práctica 04', 't2'), txt(1075, 118, '(aparte)', 't2'),
         txt(10, 372, 'Azul continuo: este laboratorio.', 't3', True), txt(10, 394, 'Ámbar discontinuo: práctica 04.', 't3', True)]
    return svg(1180, 424, ''.join(c), 'Arquitectura en Google Cloud: GitHub Actions entra con identidad federada, sube la imagen a Artifact Registry y despliega en Cloud Run con una cuenta sin permisos; el modelo en Vertex AI es la práctica 04', 'b1')


def svg_wif():
    c = [box(10, 70, 190, 90, 'GitHub Actions', 'el trabajo 2 del workflow', 'nodo', 'tiene identidad propia'),
         box(250, 20, 210, 70, '1 · Token de GitHub', 'OIDC: dice quién es', 'nodo puerta'),
         box(250, 140, 210, 80, '2 · Google (STS)', 'pool «github» y proveedor', 'nodo gcp', 'solo tu repositorio'),
         box(520, 140, 210, 80, '3 · sa-github-despliegue', 'se suplanta con permiso', 'nodo ok', 'y vale unos minutos'),
         box(790, 20, 200, 60, 'Artifact Registry', 'subir la imagen', 'nodo'), box(790, 100, 200, 60, 'Cloud Run', 'desplegar la API', 'nodo'),
         box(790, 180, 200, 60, 'Servir como…', 'sa-cloudrun-retencion', 'nodo'),
         flecha('w1', (200, 100), (250, 60)), flecha('w1', (355, 90), (355, 140)),
         flecha('w1', (460, 180), (520, 180)), flecha('w1', (730, 160), (790, 55), dis=True),
         flecha('w1', (730, 180), (790, 130), dis=True), flecha('w1', (730, 200), (790, 210), dis=True),
         txt(10, 262, 'No se guarda ninguna clave JSON en GitHub: el token vale minutos y no se reutiliza.', 't3', True),
         txt(10, 284, 'OIDC = OpenID Connect: la forma estándar de que un servicio demuestre quién es con un token firmado.', 't3', True)]
    return svg(1000, 300, ''.join(c), 'Cómo entra GitHub Actions en Google Cloud sin claves: presenta su token OIDC, Google lo cambia por acceso temporal de la cuenta sa-github-despliegue, que solo puede subir la imagen y desplegar', 'w1')


def svg_trabajos():
    """Los dos trabajos de desplegar-gcp.yml y la aprobación entre ellos."""
    c = [box(10, 20, 340, 150, '1 · Construir y probar la imagen', 'entrena con la muestra, construye', 'nodo', 'y prueba /salud, /listo y /predecir'),
         box(400, 40, 190, 110, 'Aprobación', 'environment «produccion»', 'nodo puerta', 'Review deployments'),
         box(640, 20, 480, 150, '2 · Publicar en Artifact Registry y desplegar', 'entrar sin claves → docker push', 'nodo gcp', 'gcloud run deploy → probar la URL'),
         flecha('j1', (350, 95), (400, 95)), flecha('j1', (590, 95), (640, 95)),
         txt(180, 200, 'real: 1 min 49 s', 't2 ok'), txt(880, 200, 'real: 1 min 16 s', 't2 ok'),
         txt(495, 200, 'la espera cuenta', 't2'),
         txt(10, 236, 'La misma imagen que se probó en el trabajo 1 es la que sube y se despliega (viaja como artefacto), no otra parecida.', 't3', True)]
    return svg(1130, 256, ''.join(c), 'Los dos trabajos de desplegar-gcp.yml: construir y probar la imagen, la aprobación humana y publicar en Artifact Registry y desplegar en Cloud Run', 'j1')


# =====================================================================================================================================
# Contenido
# =====================================================================================================================================
def construir():
    SLIDES.clear()
    _N.clear()

    # ---------------------------------------------------------------- A · De dónde partimos y adónde vamos
    slide('A', 3, 'Portada', 'ML e IA: de desarrollo a producción · S4', 'Laboratorio Cloud Journey: la API en Google Cloud, sin claves', f'''
<div class="cover">
 <p class="sub">Llevamos la API de retención desde GitHub Actions y GHCR hasta <b>Artifact Registry</b> y <b>Cloud Run</b>, entrando en Google Cloud <b>sin una sola clave</b> y con una persona que aprueba. Al final, <b>borramos todo</b>.</p>
 <div class="chips"><span class="tag">Caso Online Retail II</span><span class="tag">Google Cloud</span><span class="tag">Cloud Run</span><span class="tag">Workload Identity Federation</span><span class="tag">GitHub Actions</span></div>
 <div class="card" style="margin-top:22px"><h3>Cómo seguirla</h3><p class="small">Cada orden lleva <b>⧉</b> para copiarla y dice <b>dónde</b> se ejecuta: «Cloud Shell», «tu terminal», «la web de GitHub» o «la consola de Google Cloud». <b>← →</b> avanzan · <b>O</b> índice · <b>S</b> notas · <b>F</b> pantalla completa · clic en una captura para ampliarla y <b>Esc</b> para cerrarla. Todo está también en texto en <span class="mono">guia.md</span>. Las capturas son reales ({FECHA}, cuenta de Google del curso).</p></div>
 <div class="callout" style="margin-top:12px"><b>Esta práctica usa tu cuenta de Google Cloud y puede costar dinero.</b> Sigue el paso de borrado al final: sin él, lo creado seguiría ahí.</div>
</div>''',
          'Laboratorio práctico de Cloud Journey: la teoría está en la clase «De on-premise a la nube». Aquí cada alumno hace lo mismo que se hizo el 25 de noviembre de 2026 en la cuenta de Google del curso. Todo lo que se enseña pasó de verdad; lo que no se pudo comprobar se marca como sin verificar. Insista desde el principio en que cuesta dinero si no se borra y en que el último paso no es opcional.')

    slide('A', 4, 'El plan', 'Lo que vas a hacer', 'Diez pasos: de preparar Google Cloud a borrarlo todo', '''
<div class="grid2">
 <div class="card"><h3>Los pasos</h3><ol class="ol sm">
  <li><b>Requisitos</b>: cuenta de Google, proyecto, facturación y región</li>
  <li>Abrir <b>Cloud Shell</b></li>
  <li>Ejecutar <span class="mono">preparar-gcp-s4.sh</span>: APIs, cuentas, <b>WIF</b> y presupuesto</li>
  <li>Crear el repositorio de <b>Artifact Registry</b></li>
  <li>Crear las <b>5 variables</b> en GitHub</li>
  <li>Copiar <span class="mono">desplegar-gcp.yml</span> y lanzar el ensayo</li>
  <li><b>Aprobar</b> el despliegue</li>
  <li><b>Probar</b> la API en su URL pública</li>
  <li>El modelo en <b>Vertex AI</b> (práctica 04)</li>
  <li><b>Borrar</b> todo</li></ol></div>
 <div class="col">
  <div class="card"><h3>Al terminar sabrás</h3>''' + lista([
        'Qué piezas de Google Cloud necesita una API en producción y **cuánto cuesta dejarlas encendidas**.',
        'Por qué **no hay claves**: GitHub entra con su identidad (**WIF**).',
        'Cómo la **misma aprobación** de S4 protege también el despliegue en la nube.',
        'Cómo **dejarlo todo limpio**.']) + '''</div>
  <div class="callout">No se toca <span class="mono">develop</span> ni <span class="mono">main</span>: el ensayo corre en una rama <span class="mono">lab/cloud-journey/…</span>.</div>
 </div></div>''',
          'Mapa completo. Los pasos 1 a 4 son en Google Cloud, el 5 y el 6 en GitHub, el 7 y el 8 son el despliegue y la prueba, el 9 es el enlace con la práctica 04 de Vertex AI y el 10 es el borrado. Subraye el último: los recursos que se crean cobran por uso o por tenerlos encendidos, así que se borra siempre.')

    slide('A', 4, 'AS-IS: hoy', 'el punto de partida de nuestro caso', 'AS-IS: lo que hay hoy', '<div class="card">' + svg_asis() + '</div>' +
          '<div class="grid3" style="margin-top:12px">' + f'''
 <div class="card"><h3>Qué funciona</h3>{lista(['La API se **construye y prueba** en GitHub Actions y se publica en **GHCR**.', 'La publicación **espera la aprobación** del environment `produccion`.'])}</div>
 <div class="card"><h3>Qué limita</h3>{lista(['La API se ejecuta en **tu equipo o el Codespace**: no hay URL pública estable.', 'MLflow y SQLite son **locales**.'])}</div>
 <div class="card"><h3>Qué ya es «de nube»</h3>{lista(['**GitHub Actions** y **GHCR** corren en la nube de GitHub.', 'La imagen Docker es **portable**: por eso el salto es corto.'])}</div>
</div>''',
          'AS-IS es cómo está hoy el caso del curso, el mismo de la clase de on-premise a la nube pero más sencillo. Todo lo que ya hicimos en S2, S3 y el laboratorio de producción e2e: el pipeline sobre SQLite, MLflow local, la imagen con el modelo dentro, la API, y GitHub Actions con GHCR y la aprobación del environment produccion. Nada de eso está todavía en Google Cloud.')

    slide('A', 5, 'TO-BE: mañana', 'el destino', 'TO-BE: la API en Cloud Run y el modelo en Vertex AI', '<div class="card">' + svg_tobe() + '</div>' +
          '<div class="callout" style="margin-top:10px">Cambia <b>dónde viven la imagen, la API y el modelo</b>. No cambia el código ni la <b>aprobación humana</b>: solo cambia <b>cómo entra</b> GitHub en la nube.</div>',
          f'TO-BE es cómo queda. Todo vive en un solo proyecto, {PROYECTO}, y en una sola región, {REGION} (Santiago), la más cercana a Perú. En azul continuo está lo que hacemos hoy: Artifact Registry, Cloud Run, la cuenta de servicio sin permisos, la federación de identidades y el presupuesto. En ámbar discontinuo está el modelo en Vertex AI, que es la práctica 04 y se hace aparte. Dibujo propio, sin cifras de coste.')

    slide('A', 5, 'Pieza, hoy, mañana', 'tabla de equivalencias', 'Qué se mueve y a qué servicio', '<div class="card">' + tabla(['Pieza', 'Hoy', 'Mañana', 'Servicio'], [
        ['Imagen de la API', 'GHCR (`ghcr.io`)', 'repositorio `curso`', '**Artifact Registry**'],
        ['La API', 'tu equipo o el Codespace', 'URL pública que **escala a cero**', '**Cloud Run**'],
        ['Entrada de GitHub a la nube', 'no existe todavía', 'identidad federada, **sin claves**', '**Workload Identity Federation** + cuenta de servicio'],
        ['Quién ejecuta el servicio', 'tu usuario', 'cuenta `sa-cloudrun-retencion`, **sin roles**', '**IAM** (cuentas de servicio)'],
        ['Publicación', 'Actions + aprobación', 'igual: **la misma aprobación**', 'GitHub Actions (environment `produccion`)'],
        ['Modelo registrado y servido', 'MLflow local y la imagen', 'Model Registry + endpoint', '**Vertex AI** (práctica 04)'],
        ['Datos y archivos', '`data/` y SQLite locales', 'un bucket (el del modelo, en la práctica 04)', '**Cloud Storage**'],
        ['Control del gasto', 'nada que controlar', 'presupuesto de **20 €** con alertas', '**Presupuestos de facturación**']]) + '</div>',
          'Tabla de la pieza, lo de hoy, lo de mañana y el servicio. Lo importante: la columna de hoy no tiene entrada a la nube y la de mañana la resuelve con federación de identidades, no con claves. La fila de datos se menciona: en este laboratorio solo se usa un bucket para el modelo en la práctica 04. No se dan cifras de coste porque no las hemos medido.')

    slide('A', 4, 'Siglas y palabras', 'Vocabulario · antes de empezar', 'Siglas y palabras que van a aparecer', '<div class="card">' + tabla(['Palabra', 'Qué es'], [
        ['**Cloud Shell**', 'una terminal de Linux que Google te da **en el navegador**, ya con `gcloud` y con tu proyecto elegido'],
        ['**`gcloud`**', 'la orden para manejar Google Cloud desde una terminal'],
        ['**Artifact Registry**', 'el almacén de imágenes de contenedor de Google Cloud (el equivalente de GHCR)'],
        ['**Cloud Run**', 'ejecuta un contenedor y le da una **URL pública**; con `min-instances=0` no hay nada encendido cuando nadie lo llama'],
        ['**Cuenta de servicio**', 'la «identidad» de un programa. Aquí hay dos: una que **despliega** (la usa GitHub) y otra con la que **corre** la API, sin ningún permiso'],
        ['**WIF** (*Workload Identity Federation*)', 'deja que GitHub demuestre quién es con un token de corta vida y reciba acceso temporal, **sin guardar claves**'],
        ['**OIDC**', '*OpenID Connect*: la forma estándar de demostrar quién eres con un token firmado'],
        ['**Región**', f'dónde están físicamente los recursos: `{REGION}` es Santiago, la más cercana a Perú'],
        ['**Vertex AI**', 'la plataforma de IA de Google Cloud: aquí, el **Model Registry** (registro de modelos) y el **endpoint** (el modelo servido)']]) + '</div>',
          'Vocabulario mínimo. Dos que conviene decir despacio: cuenta de servicio, que es la identidad de un programa y no de una persona, y WIF, que es la razón por la que no hay ninguna clave en GitHub. Cloud Run con mínimo de cero instancias significa que no hay nada en marcha cuando nadie llama; la primera llamada tarda más porque arranca desde cero.')

    # ---------------------------------------------------------------- B · Preparar Google Cloud
    slide('B', 6, 'Requisitos y facturación', 'paso 1 · lo que necesitas antes', 'Requisitos: cuenta, proyecto, región y facturación', f'''
{rotulo_capturas(['gcp-01-proyectos.webp', 'gcp-02-facturacion.webp', 'gcp-03-facturacion-proyecto.webp'])}
<div class="grid3">{cap('gcp-01-proyectos.webp', 235)}{cap('gcp-02-facturacion.webp', 235)}{cap('gcp-03-facturacion-proyecto.webp', 235)}</div>
<div class="grid3" style="margin-top:8px">
 {mira(['Una **cuenta de Google** con Google Cloud activado (**prueba gratuita**): consola de Google Cloud.', f'Un **proyecto**: el del curso es `{PROYECTO}`. El tuyo puede tener **otro ID**: úsalo donde aquí aparezca el del profesor.', f'La región **`{REGION}`** (Santiago).'], '1 · Proyecto y región')}
 {mira(['Menú ☰ > **Facturación**: una cuenta **Activa**. Apunta su **ID** (tiene la forma `XXXXXX-XXXXXX-XXXXXX`).', 'Importe y duración de la prueba gratuita: **sin verificar**, consúltalo en la oferta vigente.'], '2 · La cuenta de facturación')}
 {mira(['Un proyecto recién creado **no tiene facturación**: «Este proyecto no tiene cuenta de facturación».', 'No hace falta vincularla a mano: **el script del paso 3 lo hace**.'], '3 · El proyecto, sin vincular')}
</div>''',
          'Requisitos. Primera captura: la lista de recursos, con la organización del curso y el proyecto project-curso-ml-ia; los otros dos proyectos son los que Google crea por defecto, no se usan. Segunda: la cuenta de facturación, activa y con gasto cero. Tercera: el proyecto aún sin cuenta vinculada; por eso el primer paso del script la vincula. El importe del crédito de la prueba gratuita no se muestra aquí: no está comprobado.')

    slide('B', 3, 'Abrir Cloud Shell', 'paso 2 · en la consola de Google Cloud', 'Abre Cloud Shell: la terminal de Google en el navegador', f'''
<div class="split" style="grid-template-columns:.85fr 1.15fr">
 <div class="col">
  <div class="card"><h3>Dónde: la consola de Google Cloud</h3><ol class="ol sm">
   <li>Entra con la cuenta de Google del curso y comprueba arriba que está elegido tu <b>proyecto</b></li>
   <li>Pulsa el icono <b>&gt;_</b> (Activar Cloud Shell), arriba a la derecha</li>
   <li>Espera a que salga el prompt: ya puedes escribir</li></ol></div>''' + mira([
        'El mensaje «**Your Cloud Platform project in this session is set to** {}».'.format(PROYECTO),
        'El prompt con el proyecto entre paréntesis y en amarillo.']) + si_falla([
        'El proyecto que sale **no es el tuyo**: `gcloud config set project <tu-ID-de-proyecto>`.']) + f'''
 </div>
 <div class="capcol">{rotulo_capturas(['gcp-20-cloudshell.webp'])}{cap('gcp-20-cloudshell.webp', 400)}</div>
</div>''',
          'Cloud Shell es una terminal de Linux en el navegador, con gcloud y git ya instalados y con una sesión ya autenticada con la cuenta de Google; por eso no hace falta instalar nada ni descargar claves. En la captura se lee el aviso del proyecto elegido. Si el proyecto no es el del curso, se cambia con gcloud config set project.')

    slide('B', 6, 'Traer y editar el script', 'paso 3 · en Cloud Shell', 'Trae el script y pon tus tres valores', f'''
<div class="split" style="grid-template-columns:1.12fr .88fr">
 <div class="col">''' + term('Cloud Shell · una orden cada vez', [
        '# 1) tu usuario de GitHub (lo único que cambias en esta línea)', O['usuario_gh'], O['clonar'], O['cd_lab'],
        '# 2) apunta el ID de tu cuenta de facturación (columna ACCOUNT_ID)', O['cuentas_fact'],
        '# 3) edita las tres líneas de arriba (Ctrl+O, Intro, Ctrl+X para guardar y salir)', O['editar'],
        '# 4) comprueba el resultado', O['ver_valores']]) + '''
 </div>
 <div class="col">
  <div class="card"><h3>Las tres líneas que cambias</h3>''' + tabla(['Línea', 'Pon'], [
        ['`PROYECTO=`', 'el **ID** de tu proyecto'],
        ['`FACTURACION=`', 'el **ACCOUNT_ID** que imprime `gcloud billing accounts list`'],
        ['`REPO_GITHUB=`', f'`tu-usuario/{REPO}`']]) + '''</div>''' + mira([
        'La orden `grep` enseña **solo esas tres líneas**, ya con tus valores.',
        'El resto del script (región, nombres de las cuentas, pool) **no se toca**.']) + si_falla([
        '`Remote branch develop not found` o `Repository not found`: tu fork no tiene `develop` o escribiste mal el usuario.',
        '`destination path \'curso\' already exists`: ya lo clonaste; haz `cd ~/curso` y `git pull`.']) + '''
 </div></div>''',
          'El script está en la carpeta del laboratorio. En Cloud Shell se clona el fork del alumno, en la rama develop. Solo hay que cambiar tres valores: el proyecto, el identificador de la cuenta de facturación y el repositorio de GitHub; este último es el que el script usa para limitar la federación de identidades a tu repositorio y a ningún otro. Clonar el fork de un alumno desde Cloud Shell: sin verificar con un fork distinto del del profesor.')

    slide('B', 7, 'Ejecutar el script', 'paso 3 · en Cloud Shell', 'Ejecuta el script: siete pasos y las cinco variables', f'''
<div class="split" style="grid-template-columns:.8fr 1.2fr">
 <div class="col">''' + term('Cloud Shell', [O['preparar']]) + mira([
        'Siete bloques «=== n · …» y al final **«FIN · todo listo»**.',
        'Antes del final, **cinco líneas `GCP_…=`**: son tus variables de GitHub. **Cópialas**.',
        'Puedes repetirlo: lo que ya existe **no se vuelve a crear**.']) + si_falla([
        '`PERMISSION_DENIED` al vincular la facturación: tu cuenta no administra esa cuenta de facturación.',
        'Un error en un bloque **detiene** el script: corrige y vuelve a ejecutarlo.']) + f'''
 </div>
 <div class="capcol">{rotulo_capturas(['gcp-23-preparar.webp'])}{cap('gcp-23-preparar.webp', 470, 'La captura se tomó con un marcador de fin añadido por la herramienta que tecleó la orden (`__FIN_… 0`): tú solo verás «FIN · todo listo».')}</div>
</div>''',
          'Ejecución real del script. Los siete bloques son: proyecto activo, facturación, APIs, cuentas de servicio, permisos mínimos, federación de identidades, presupuesto y, al final, la lista de variables. El número de proyecto que ve en la captura, 61343545797, es el del proyecto del profesor; el vuestro será distinto. Si se repite, el script comprueba antes de crear cada cosa.')

    slide('B', 6, 'Qué hace el script', 'paso 3 · lo que dejó hecho', 'Qué dejó hecho el script y por qué cada cosa', '<div class="card">' + tabla(['Bloque', 'Qué hace', 'Por qué'], [
        ['**1 · Facturación**', 'vincula la cuenta de facturación al proyecto', 'sin ella no se pueden activar las APIs de pago'],
        ['**2 · APIs**', 'activa Artifact Registry, Cloud Run, IAM, credenciales, STS, Resource Manager y Presupuestos', 'cada servicio hay que activarlo una vez por proyecto'],
        ['**3 · Cuentas**', '`sa-github-despliegue` (la usa GitHub) y `sa-cloudrun-retencion` (con la que corre la API)', 'separar quien **despliega** de quien **ejecuta**'],
        ['**4 · Permisos mínimos**', 'al desplegador: `artifactregistry.writer`, `run.admin` y `serviceAccountUser` **solo sobre** `sa-cloudrun-retencion`', 'puede subir imágenes y desplegar, nada más; la cuenta del servicio **no tiene ningún rol**'],
        ['**5 · Federación (WIF)**', 'pool `github`, proveedor `github` y una **condición** que limita a tu repositorio', 'cualquier otro repositorio de GitHub quedaría **rechazado**'],
        ['**6 · Presupuesto**', 'alerta de **20 €** al 50, 90 y 100 %', 'avisa por correo; **no corta** nada'],
        ['**7 · Variables**', 'imprime las cinco `GCP_…`', 'son lo que necesita el workflow']]) + '</div>',
          'Esto es lo que el script deja hecho. Insista en dos decisiones de diseño: la cuenta que despliega tiene permisos mínimos y la cuenta con la que corre el servicio no tiene ningún rol, de modo que si alguien consiguiera ejecutar código dentro del servicio no podría tocar nada más en el proyecto. Y la condición del proveedor: solo tu repositorio puede actuar como la cuenta de despliegue. El presupuesto avisa, no corta: eso hay que decirlo.')

    slide('B', 5, 'Cómo entra GitHub sin claves', 'paso 3 · el mecanismo', 'WIF: GitHub demuestra quién es y recibe acceso temporal', '<div class="card">' + svg_wif() + '</div>' + '''
<div class="grid3" style="margin-top:10px">
 <div class="card"><h3>1 · El token</h3><p class="small">Cada ejecución de Actions puede pedir a GitHub un token OIDC que dice <b>qué repositorio</b> es. Necesita el permiso <span class="mono">id-token: write</span>.</p></div>
 <div class="card"><h3>2 · El cambio</h3><p class="small">Google comprueba el token contra el <b>pool y el proveedor</b> y la condición del repositorio. Solo si cuadra, lo cambia por acceso temporal.</p></div>
 <div class="card"><h3>3 · El permiso</h3><p class="small">El acceso es el de <b>una cuenta de servicio con permisos mínimos</b>: subir la imagen y desplegar. Caduca en minutos.</p></div>
</div>''',
          'Este es el dibujo de la clase, ahora aplicado a nuestro caso. GitHub emite un token firmado que dice a qué repositorio pertenece la ejecución. Google lo valida contra el proveedor que creó el script y su condición. Si todo cuadra, entrega acceso temporal como la cuenta sa-github-despliegue. No hay ninguna clave que se pueda filtrar, copiar o caducar sin avisar.')

    slide('B', 5, 'Por qué sin claves', 'paso 3 · lo que vimos en la organización', 'Por qué sin claves: la organización lo prohíbe', f'''
{rotulo_capturas(['gcp-12-politica-claves.webp', 'gcp-09-cuentas-servicio.webp', 'gcp-11-wif.webp'])}
<div class="grid3">{cap('gcp-12-politica-claves.webp', 245)}{cap('gcp-09-cuentas-servicio.webp', 245)}{cap('gcp-11-wif.webp', 245)}</div>
<div class="grid3" style="margin-top:8px">
 {mira(['La política `iam.disableServiceAccountKeyCreation` está **Aplicada** y la **hereda** el proyecto de la organización.', 'Crear una clave JSON de una cuenta de servicio **no es posible** aquí.'], '1 · La política')}
 {mira(['La única cuenta que había, `sa-curso-ml-ia`, muestra «**No hay claves**».', 'Esta captura es **de antes** de ejecutar el script.'], '2 · Las cuentas')}
 {mira(['Pantalla de bienvenida de Workload Identity, **sin ningún pool** todavía (antes del script).', 'El script hace por ti sus **cuatro pasos**.'], '3 · Workload Identity')}
</div>''',
          'Por qué no usamos claves. En esta organización, una política heredada impide crear claves de cuentas de servicio. Es una buena práctica general: una clave JSON es una contraseña eterna que alguien acabará pegando donde no debe. La federación evita la clave. Las dos últimas capturas son de antes de ejecutar el script: la lista de cuentas solo tiene la del curso y no hay ningún pool de identidades.')

    slide('B', 5, 'Crear el repositorio de imágenes', 'paso 4 · en Cloud Shell', 'Crea el repositorio «curso» de Artifact Registry', f'''
<div class="split" style="grid-template-columns:.95fr 1.05fr">
 <div class="col">''' + term('Cloud Shell', [O['crear_ar'], O['listar_ar'], '# opcional: ¿la organización deja una URL pública sin login?', O['politica_allusers']]) + mira([
        '`Created repository [curso].`',
        'La segunda orden lista el repositorio `curso` en `southamerica-west1`.',
        'La política dice **`allValues: ALLOW`**: Cloud Run podrá publicar la API con `--allow-unauthenticated`.']) + si_falla([
        '**Escribe la descripción sin tildes** (`Imagenes`): al teclear en Cloud Shell desde otra herramienta se perdieron («Imgenes», se ve en la captura).',
        'Si la política **no** permite `allUsers`, el despliegue con `--allow-unauthenticated` puede fallar o la URL no ser pública (**sin verificar**: aquí sí lo permite).']) + f'''
 </div>
 <div class="capcol">{rotulo_capturas(['gcp-24-ar-y-politicas.webp'])}{cap('gcp-24-ar-y-politicas.webp', 400, 'Lo que se tecleó en la captura es una sola línea que además comprueba la política y que Vertex AI responde en Santiago («Listed 0 items»: aún no hay endpoints).')}</div>
</div>''',
          'El script no crea el repositorio de imágenes: se hace a mano, con una sola orden. La captura reúne tres comprobaciones en una línea: se creó el repositorio, la política de la organización deja usar allUsers, y Vertex AI contesta en Santiago con cero endpoints. Anécdota real y útil: al teclear la orden desde otra herramienta se perdieron las tildes de la descripción, así que se recomienda no usarlas en las descripciones de gcloud.')

    # ---------------------------------------------------------------- C · Preparar GitHub
    slide('C', 5, 'Variables de GitHub', 'paso 5 · en la web de GitHub', 'Crea las cinco variables del repositorio (no son secretos)', f'''
<div class="split" style="grid-template-columns:1.05fr .95fr">
 <div class="col">
  <div class="card"><h3>Dónde: la web de GitHub, en tu fork</h3><ol class="ol sm">
   <li><b>Settings</b> › <b>Secrets and variables</b> › <b>Actions</b></li>
   <li>Pestaña <b>Variables</b> › <b>New repository variable</b></li>
   <li>Escribe <b>Name</b> y <b>Value</b> › <b>Add variable</b>; repite 5 veces</li></ol></div>
  <div class="card">''' + tabla(['Name', 'Value (las del profesor)'], [[f'`{n}`', f'`{v}`'] for n, v in VARIABLES], 'vars') + '''</div>
  <div class="callout">Tus valores son <b>los que imprimió tu script</b>, líneas <span class="mono">GCP_…=</span>. Son <b>Repository variables</b> (no «Environment variables», ni secretos): no hay nada secreto.</div>
 </div>
 <div class="capcol">''' + rotulo_capturas(['cj-01-variables-github.webp']) + cap('cj-01-variables-github.webp', 400) + '''</div>
</div>''',
          'En GitHub se crean cinco variables de repositorio, no secretos, porque ninguna lo es: son nombres de proyecto, de región y de cuentas. Si el entorno de GitHub se llamase igual que una variable de entorno, sería otra cosa: aquí van en Repository variables. Los valores de la tabla son los del profesor; cada alumno copia los suyos de la salida del script. El número 61343545797 es el número del proyecto del profesor.')

    slide('C', 5, 'Los dos trabajos', 'paso 6 · el workflow', 'desplegar-gcp.yml: dos trabajos y una aprobación', '<div class="card">' + svg_trabajos() + '''</div>
<div class="grid3" style="margin-top:12px">
 <div class="card"><h3>Trabajo 1 · construir y probar</h3><p class="small">Entrena el modelo con la <b>muestra del repositorio</b>, construye la imagen y la <b>prueba</b> en el runner: <span class="mono">/salud</span>, <span class="mono">/listo</span>, <span class="mono">/modelo</span> y una predicción. Si algo falla, <b>no se publica nada</b>.</p></div>
 <div class="card"><h3>La aprobación</h3><p class="small">El trabajo 2 usa el <i>environment</i> <span class="mono">produccion</span>: se queda <b>esperando</b> hasta que una persona apruebe. Es el mismo del laboratorio anterior.</p></div>
 <div class="card"><h3>Trabajo 2 · publicar y desplegar</h3><p class="small">Entra en Google Cloud <b>sin claves</b>, sube la imagen a Artifact Registry, la despliega en Cloud Run y <b>prueba la URL pública</b>. Deja un resumen con la imagen y la URL.</p></div>
</div>''',
          'El workflow tiene dos trabajos. El primero construye y prueba la imagen en el runner y la guarda como artefacto; si falla no se publica nada. Entre los dos está la aprobación del environment produccion, el mismo que se configuró en el laboratorio anterior. El segundo trabajo carga esa misma imagen, entra en Google Cloud sin claves, la sube y la despliega. Los tiempos reales son 1 minuto 49 y 1 minuto 16.')

    slide('C', 6, 'Las líneas clave del YAML', 'paso 6 · qué hace cada línea', 'Las líneas que importan de desplegar-gcp.yml', '<div class="card">' + tabla(['Línea', 'Qué hace'], [
        ["`on: push: branches: ['lab/cloud-journey/**']`", 'un push a una rama **`lab/cloud-journey/…`** lo lanza: ensayo **sin tocar** `develop` ni `main` (también hay `workflow_dispatch`)'],
        ['`permissions: id-token: write` (trabajo 2)', 'deja que GitHub emita el **token OIDC**; sin él no hay WIF'],
        ['`environment: produccion`', 'el trabajo **espera** a que una persona apruebe'],
        ['`google-github-actions/auth@v2` con `workload_identity_provider` y `service_account`', 'cambia el token de GitHub por **acceso temporal** como `sa-github-despliegue`'],
        ['`google-github-actions/setup-gcloud@v2`', 'instala `gcloud` en el runner'],
        ['`gcloud auth configure-docker …-docker.pkg.dev` y `docker push`', 'Docker entra en Artifact Registry con ese acceso y **sube la imagen**'],
        ['`gcloud run deploy … --service-account=…`', 'el servicio **corre con la cuenta sin permisos**'],
        ['`--min-instances=0 --max-instances=1 --allow-unauthenticated`', 'escala a **cero** y a **uno** como máximo; URL **pública**'],
        ['`defaults.run.working-directory: .` (trabajo 2)', 'ese trabajo **no hace checkout** y no puede heredar `04-Proyecto-Base` (lección de S4)']]) + '</div>',
          'Las líneas que importan. id-token write es lo que permite pedir el token a GitHub. La acción auth de Google hace el intercambio con el proveedor de identidad y la cuenta de despliegue. Las tres opciones de Cloud Run son decisiones de coste y de seguridad: cero instancias en reposo, un máximo de una para que no se dispare el gasto, y acceso público porque es una demostración con datos de ejemplo. La última es la lección de S4: un trabajo sin checkout no tiene la carpeta 04-Proyecto-Base.')

    # ---------------------------------------------------------------- D · Desplegar con aprobación
    slide('D', 6, 'Copiar y lanzar el ensayo', 'paso 6 · en tu terminal o el Codespace', 'Copia el workflow y lanza el ensayo con un push', f'''
<div class="split" style="grid-template-columns:1.1fr .9fr">
 <div class="col">''' + term('Tu terminal (bash) o la del Codespace · en la raíz del repositorio', [
        O['switch_develop'], O['pull'], O['rama'], O['mkdir'], O['cp'], O['add'], O['commit'], O['push']]) + term('Windows PowerShell 5.1 · en lugar de «mkdir» y «cp» (sin verificar)', [O['ps_mkdir'], O['ps_cp']]) + '''
 </div>
 <div class="col">''' + mira([
        '`Switched to a new branch \'lab/cloud-journey/despliegue\'`; el `push` enseña una línea `[new branch]`.',
        'En la pestaña **Actions** de GitHub sale un run nuevo: **Cloud Journey · desplegar la API en Google Cloud**.',
        'Antes de este paso deben existir las **5 variables** y el environment `produccion` con revisores.']) + si_falla([
        'No aparece ningún run: Actions sin activar en el fork, o la rama **no empieza por** `lab/cloud-journey/`.',
        'En Windows PowerShell 5.1, **una orden por línea**: `&&` no existe.']) + '''
 </div></div>''',
          'Estas órdenes son de git, en el Codespace o en una terminal bash. Se hacen en órdenes sueltas, no encadenadas, porque en Windows PowerShell 5.1 el doble ampersand no existe. Las dos órdenes de PowerShell sustituyen a mkdir con la opción p y a cp; están sin verificar porque el ensayo se hizo desde bash. El push a una rama que empieza por lab barra cloud-journey barra lanza el workflow, sin tocar develop ni main.')

    slide('D', 5, 'Aprobar el despliegue', 'paso 7 · en la web de GitHub', 'El trabajo 2 se para y espera tu aprobación', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">
  <div class="card"><h3>Dónde: la web de GitHub › Actions</h3><ol class="ol sm">
   <li>Abre el run y espera: el trabajo 1 en verde y el 2 en <b>Waiting</b></li>
   <li>Pulsa <b>Review deployments</b> (aviso amarillo)</li>
   <li>Marca <b>produccion</b></li>
   <li>Pulsa <b>Approve and deploy</b></li></ol></div>''' + mira([
        'El aviso: «**helicr requested your review to deploy to produccion**» (con tu usuario).',
        'Tras aprobar, el trabajo 2 arranca y **tarda poco más de un minuto**.']) + si_falla([
        'Pasa **sin pedir aprobación**: el environment `produccion` no existe o no tiene revisores. Mira `CONFIGURAR-REPOSITORIO.md` del laboratorio anterior.']) + f'''
 </div>
 <div class="capcol">{rotulo_capturas(['gh-01-esperando-aprobacion.webp'])}{cap('gh-01-esperando-aprobacion.webp', 400, 'Es del laboratorio anterior (otro workflow, el de nueva versión); el aviso y el botón son los mismos que verás aquí.')}</div>
</div>''',
          'La aprobación es la misma del laboratorio de producción e2e: el trabajo 2 usa el environment produccion con revisores, así que se detiene hasta que una persona lo aprueba. La captura es del workflow del laboratorio anterior, que usa el mismo environment; no se tomó una específica de este run. Con un solo usuario, uno se aprueba a sí mismo. Si no pide aprobación, el environment no está bien configurado.')

    slide('D', 6, 'El run en verde', 'paso 7 · el resultado', 'Desplegada: dos trabajos en verde y un resumen con la URL', f'''
{rotulo_capturas(['cj-02-run-desplegado.webp', 'cj-03-resumen-cloudrun.webp'])}
<div class="split" style="grid-template-columns:1.1fr .9fr;gap:14px">
 <div class="capcol">{cap('cj-02-run-desplegado.webp', 330)}</div>
 <div class="capcol">{cap('cj-03-resumen-cloudrun.webp', 230)}
  <div class="grid3">{kpi('8 min 32 s', 'total, **con** la espera', 'okc')}{kpi('1 min 49 s', 'trabajo 1', '')}{kpi('1 min 16 s', 'trabajo 2', '')}</div></div>
</div>
<div class="small" style="margin-top:2px">Run nº {RUN} (<span class="mono">{RUN_URL}</span>). El total incluye la espera de la aprobación y es mayor que la suma de los dos trabajos. El resumen muestra la imagen <span class="mono">…/curso/retencion-api:&lt;commit&gt;</span>, la URL, la cuenta del servicio «sin permisos» y la entrada «sin claves».</div>''',
          'Resultado real del ensayo del 25 de noviembre de 2026: éxito en 8 minutos 32 segundos en total, que incluyen la espera de la aprobación; el trabajo 1 duró 1 minuto 49 y el trabajo 2, 1 minuto 16. El resumen del trabajo 2 lo escribe el propio workflow: imagen con la etiqueta del commit, URL pública, cuenta de servicio sin permisos y entrada sin claves. Cada persona verá su run, su URL y sus tiempos.')

    # ---------------------------------------------------------------- E · Probar la API
    slide('E', 7, 'Probar la API', 'paso 8 · desde cualquier sitio', 'Prueba la API en su URL pública', f'''
<div class="split" style="grid-template-columns:1.12fr .88fr">
 <div class="col">''' + term('Cloud Shell · saca tu URL y entra en la carpeta del proyecto', [O['url'], O['cd_base']]) + term('Cloud Shell, bash o tu terminal · con la variable URL puesta', [O['salud'], O['listo'], O['predecir']]) + term('Windows PowerShell 5.1 · en la raíz del repositorio (sin verificar)', [O['ps_url'], O['ps_salud'], O['ps_listo'], O['ps_predecir']]) + f'''
 </div>
 <div class="col">''' + mira([
        '`/salud` → `{"estado":"ok"}`',
        '`/listo` → `{"estado":"listo"}`',
        '`/predecir` → `probabilidad` **0,8278889191932133**, `modelo` `regresion_logistica`, `huella_datos` `35a94deb4e04ab4a` y `advertencias` vacío.',
        'Es **la misma probabilidad que en local** (0,828), con la misma huella de datos.']) + si_falla([
        'La **primera llamada tarda más**: el servicio arranca desde cero (`min-instances=0`). Reintenta; cuánto tarda: **sin dato**.',
        '`403`: posiblemente la organización no permite `allUsers` (paso 4; **sin verificar**).',
        'En PowerShell cambia `XXXX` por tu URL (sale en el resumen del run).']) + '''
 </div></div>''',
          'Se prueba la API desplegada con curl. En Cloud Shell, la URL se obtiene con la misma orden que usa el workflow. Desde otra terminal se copia del resumen del run. La respuesta de predecir da exactamente la misma probabilidad que la API en local, 0,828, con la misma huella de datos 35a94deb4e04ab4a: el código y el modelo son los mismos, solo cambia dónde corre. Las órdenes de PowerShell no se han ejecutado: sin verificar.')

    slide('E', 4, 'En la consola', 'paso 8 · la consola de Google Cloud', 'Míralo también en la consola de Google Cloud', f'''
{rotulo_capturas(['cj-04-cloudrun-consola.webp', 'cj-05-artifact-registry.webp'])}
<div class="grid2">{cap('cj-04-cloudrun-consola.webp', 300)}{cap('cj-05-artifact-registry.webp', 300)}</div>
<div class="grid2" style="margin-top:8px">
 {mira(['Dónde: la consola de Google Cloud, menú ☰ › **Cloud Run** › `retencion-api`.', 'Sale en `southamerica-west1`, con la marca verde, su **URL** y, en **Observabilidad**, las métricas de tus llamadas.'], 'Cloud Run')}
 {mira(['Dónde: menú ☰ › **Artifact Registry** › `curso` › `retencion-api`.', 'Salen **tres versiones**: una con la **etiqueta del commit** y otra de **174,8 MB** (tamaño virtual de la imagen).'], 'Artifact Registry')}
</div>''',
          'Las dos capturas son de la consola de Google Cloud del 25 de noviembre, con el aviso del crédito recortado. Cloud Run: el servicio retencion-api en la región de Santiago, con su URL y las métricas de la pestaña Observabilidad. Artifact Registry: el repositorio curso, paquete retencion-api, con tres versiones, una de ellas con la etiqueta del commit del run y otra de 174,8 MB de tamaño virtual. La guía indica el camino por el menú.')

    # ---------------------------------------------------------------- F · El modelo en Vertex AI
    slide('F', 6, 'El modelo en Vertex AI', 'paso 9 · práctica 04, en Cloud Shell', 'TO-BE del modelo: registrado y servido en Vertex AI', f'''
<div class="split" style="grid-template-columns:1.05fr .95fr">
 <div class="col">''' + term('Cloud Shell · práctica 04 (tarda; se hace aparte)', [O['cd_vertex'], O['vertex_crear'], O['vertex_probar'], '# en cuanto acabes (el endpoint cobra mientras esté desplegado)', O['vertex_borrar']]) + '''
  <div class="callout">Todo el detalle, las trampas y las fuentes están en <span class="mono">../practicas-gcp/04-vertex-modelo/README.md</span>.</div>
 </div>
 <div class="col">''' + mira([
        '`crear.sh` **reentrena el mismo modelo** con scikit-learn 1.6.1: los contenedores de Vertex solo llegan a la **1.6** y el proyecto usa la **1.9.1**.',
        'Crea un bucket, registra **`retencion-90d-sklearn`** en el Model Registry y despliega el endpoint **`retencion-90d-endpoint`**.',
        'La petición es `{"instances": [[13 números]]}`: **una lista en el orden del modelo**, no un diccionario.'], 'Qué hace') + si_falla([
        'El endpoint **cobra mientras tenga un modelo desplegado**, aunque no reciba peticiones: ejecuta `borrar.sh` en cuanto acabes. Coste: **sin dato**.',
        'Comprobado el 25/11/2026: el contenedor devuelve la **clase** (1 o 0), no la probabilidad. Tardó del orden de 10-15 min en desplegar (**sin medir** con exactitud).']) + '''
 </div></div>''',
          'El modelo en Vertex AI es la práctica 04 de las prácticas de Google Cloud; aquí solo se resume y se enlaza. Se registra el modelo de retención en el Model Registry y se despliega en un endpoint. Hay un detalle de versiones: el contenedor pre-construido solo llega a scikit-learn 1.6 y el proyecto usa la 1.9.1, así que crear.sh reentrena el mismo modelo con la 1.6.1. Importante: el endpoint cobra mientras tenga un modelo desplegado, y el coste exacto no lo tenemos.')

    slide('F', 4, 'Qué debes ver en Vertex AI', 'paso 9 · la consola de Google Cloud', 'Qué debes ver en Vertex AI', f'''
{rotulo_capturas(['cj-06-vertex-modelo.webp', 'cj-07-vertex-endpoint.webp'])}
<div class="grid2">{cap('cj-06-vertex-modelo.webp', 300)}{cap('cj-07-vertex-endpoint.webp', 300)}</div>
<div class="grid2" style="margin-top:8px">
 {mira(['Dónde: la consola de Google Cloud, menú ☰ › **Plataforma de Gemini** (Vertex AI) › **Modelos** › **Registro de modelos**.', f'Elige la región **`{REGION}` (Santiago)**: en otra región la lista sale **vacía**. El modelo es `retencion-90d-sklearn` (el nombre se corta en la tabla).'], 'El modelo en el Registro')}
 {mira(['Dónde: el mismo menú › **Extremos** (los *endpoints*).', 'El endpoint `retencion-90d-endpoint` en estado **Activo**, con **1** modelo: mientras sea así, **cobra**. Se deshace con `bash borrar.sh`.'], 'El endpoint')}
</div>''',
          'Las dos capturas son de la consola de Google Cloud del 25 de noviembre, con el aviso del crédito recortado y las dos en la región de Santiago. La primera es el registro de modelos, con el modelo importado, versión uno, implementado; en la consola el menú de Vertex AI se llama Plataforma de Gemini. La segunda son los endpoints, que la consola llama Extremos: retencion-90d-endpoint, activo, con un modelo. Hay que elegir la región de Santiago, porque en otra la lista sale vacía. Para cualquier detalle, el README de la práctica 04 es la fuente.')

    # ---------------------------------------------------------------- G · Borrar y cerrar
    slide('G', 7, 'Borrar todo', 'paso 10 · en Cloud Shell', 'Borra todo al terminar: sin esto, sigue cobrando', f'''
<div class="split" style="grid-template-columns:1.05fr .95fr">
 <div class="col">''' + term('Cloud Shell · primero la práctica 04 (si la hiciste)', [O['cd_vertex'], O['vertex_borrar']]) + term('Cloud Shell · en la carpeta del laboratorio', [O['cd_lab'], O['borrar'], '# opcional: además, desvincula la facturación del proyecto', O['borrar_desv']]) + '''
  <div class="card"><h3>Lo que borra</h3><ul class="list"><li><b>Cloud Run</b> (<span class="mono">retencion-api</span>), el repositorio <b>curso</b> con sus imágenes, los <b>permisos</b> y las <b>dos cuentas</b> del laboratorio, el <b>pool y proveedor</b> de WIF y el <b>presupuesto</b>.</li><li><b>No</b> borra el proyecto ni <span class="mono">sa-curso-ml-ia</span>.</li><li>Las <b>5 variables de GitHub</b> se borran <b>a mano</b>: Settings › Secrets and variables › Actions › Variables.</li></ul></div>
 </div>
 <div class="col">''' + mira([
        'Cada bloque dice qué borra o «No existe (nada que borrar)»; **se puede repetir**.',
        'Al final, listados **vacíos** (Cloud Run, Artifact Registry, WIF, presupuestos) y solo queda `sa-curso-ml-ia`.',
        'La última línea: **«FIN · borrado terminado»**.']) + si_falla([
        'Google guarda un pool de WIF borrado unos **30 días** y no deja reutilizar el nombre (según su documentación, **sin verificar aquí**); para recuperarlo: `gcloud iam workload-identity-pools undelete github --location=global`.']) + f'''
  {cap('cj-08-borrado.webp', 140, 'Se ven solo los pasos 5 a 8: la captura recorta los anteriores con `tail`.', 'El final de `borrar-gcp-s4.sh`: WIF y presupuesto borrados, listados vacíos y «FIN · borrado terminado»')}
 </div></div>''',
          'El borrado es parte del laboratorio. El script borrar-gcp-s4.sh es idempotente: comprueba si cada recurso existe antes de borrarlo y al final lista lo que queda. No borra el proyecto ni la cuenta de servicio que ya existía. Se ejecutó de verdad el 25 de noviembre: en la captura se ve el proveedor y el pool de WIF borrados, el presupuesto borrado, la facturación vinculada a propósito, los listados de Cloud Run y de Artifact Registry vacíos y, entre las cuentas de servicio, solo sa-curso-ml-ia y la cuenta de Compute por defecto, que no es nuestra. La captura corta con tail los primeros pasos.')

    slide('G', 6, 'Costes y lecciones', 'lo que aprendimos de verdad', 'Costes y lecciones reales', '<div class="grid3">' + ''.join(
        f'<div class="card"><h3>{esc(t)}</h3><p class="small">{md(c)}</p></div>' for t, c in [
            ('0 instancias en reposo', 'Con `--min-instances=0` **no hay nada encendido** cuando nadie llama. `--max-instances=1` pone un tope. Importe del uso: **sin dato**.'),
            ('Presupuesto con alertas', 'El de **20 €** avisa al 50, 90 y 100 %, pero **no corta nada**: sigues siendo tú quien borra.'),
            ('Sin claves, por política', 'La organización prohíbe crear claves de cuentas de servicio: **WIF** no es un capricho: es la vía que queda.'),
            ('La cuenta de Compute, sin roles', 'En una organización nueva, la cuenta de servicio de Compute **no tiene ningún rol**. Con ella **GKE se rompió** (práctica 02).'),
            ('Gemini no está en Santiago', 'Para Gemini se usa la ubicación `global` (práctica 05). El resto del laboratorio va en `southamerica-west1`.'),
            ('Tildes en Cloud Shell', 'Al teclear desde otra herramienta se **perdieron** («Imgenes»): descripciones de `gcloud` **sin tildes**.')]) + '</div>',
          'Seis lecciones reales. Cero instancias en reposo y un máximo de una son las dos decisiones de coste del servicio. El presupuesto avisa, no corta. La política de la organización impone la federación. La cuenta de servicio de Compute sin roles es lo que rompió el clúster de GKE de la práctica 02. Gemini no figura para Santiago, por eso la práctica 05 usa la ubicación global. Y las tildes que se perdieron al teclear en Cloud Shell.')

    slide('G', 6, 'Si algo falla', 'casos y su causa', 'Si algo falla: casos y qué hacer', '<div class="card">' + tabla(['Síntoma', 'Causa', 'Qué hacer', '¿Visto?'], [
        ['Aparece «Imgenes» en la descripción', 'Se pierden las **tildes** al teclear en Cloud Shell', 'Escribir sin tildes', 'sí (25/11)'],
        ['El trabajo 2 falla con «No such file or directory»', 'Un trabajo **sin checkout** hereda `working-directory: 04-Proyecto-Base`', '`working-directory: .` en ese trabajo (ya está)', 'sí (S4)'],
        ['El trabajo 2 pasa **sin esperar**', 'El environment `produccion` no existe o **sin revisores**', 'Configurarlo (laboratorio anterior)', 'sí (S4)'],
        ['No aparece ningún run', 'Actions sin activar en el fork, o rama que **no empieza por** `lab/cloud-journey/`', 'Pestaña Actions; revisar el nombre de la rama', 'sin verificar'],
        ['Falla el paso «Entrar en Google Cloud sin claves»', '**Variables** mal copiadas, o `REPO_GITHUB` del script **distinto** de tu repositorio', 'Repasar las 5 variables y la condición del proveedor', 'sin verificar'],
        ['Falla `docker push` o `gcloud run deploy`', 'Falta el repositorio `curso` (paso 4), una API o un permiso', 'Repetir el paso 4; volver a ejecutar el script', 'sin verificar'],
        ['La URL responde `403`', 'Posible: la organización no permite `allUsers`', 'La orden de política del paso 4', 'sin verificar']]) + '</div>',
          'Los tres primeros casos pasaron de verdad: las tildes en Cloud Shell, el directorio de trabajo heredado y el environment sin revisores. Los demás son los fallos más probables según cómo está construido el workflow, pero no se han provocado a propósito, así que se marcan sin verificar y no se citan mensajes literales. Si algún alumno los encuentra con un mensaje distinto, que lo cuente para completar la guía.')

    slide('G', 5, 'Qué está verificado', 'qué se comprobó y qué no', 'Qué se comprobó de verdad y qué falta', f'''
<div class="grid2">
 <div class="card"><h3 class="okc">Comprobado el {FECHA} en la cuenta del curso</h3>''' + lista([
        f'Run nº {RUN} en verde: **8 min 32 s** en total, trabajos de **1 min 49 s** y **1 min 16 s**.',
        'La API en **Cloud Run**: `/salud`, `/listo` y `/predecir` con **0,8278889191932133**, igual que en local.',
        'El script `preparar-gcp-s4.sh` de principio a fin («FIN · todo listo») y el repositorio `curso`.',
        'Las cinco variables en GitHub y la entrada **sin claves**.',
        '`borrar-gcp-s4.sh` **ejecutado**: WIF y presupuesto borrados, listados vacíos y solo `sa-curso-ml-ia` y la cuenta de Compute por defecto (captura `cj-08`).',
        'La práctica 04 (Vertex AI): modelo en el Registro y endpoint **Activo** en Santiago (capturas `cj-06` y `cj-07`); el contenedor devuelve la **clase**.']) + '''</div>
 <div class="card"><h3 class="malc">Sin verificar o sin dato</h3>''' + lista([
        'Clonar un **fork de alumno** en Cloud Shell y las órdenes de **PowerShell**.',
        'Coste del uso, tiempo de la primera llamada en frío, tiempo exacto del despliegue del endpoint y límites de la prueba gratuita: **sin dato**.']) + '''</div>
</div>
<div class="callout" style="margin-top:12px">El run se puede abrir en <span class="mono">''' + RUN_URL + '</span>.</div>',
          'Diapositiva de honestidad. Lo comprobado es todo lo del run real y las capturas de la cuenta del curso. Lo comprobado incluye ya el script de borrado, que se ejecutó de verdad, y la práctica 04 con sus dos capturas de la consola. Lo que no: el clonado desde el fork de un alumno; las órdenes de PowerShell; y las cifras de coste y el tiempo exacto del despliegue del endpoint, que no tenemos.')

    slide('G', 4, 'Cierre', 'El mensaje', 'Una API en la nube sin una sola clave, aprobada por una persona y borrable', f'''
<div class="msg">GitHub <b>demuestra quién es</b>, una persona <b>aprueba</b>, la API <b>corre</b> en Cloud Run y, cuando acabas, <b>lo borras todo</b>.</div>
<div class="grid4" style="margin-top:18px">
 {kpi('8 min 32 s', 'el run en verde, **con** la espera de la aprobación: 1 min 49 s + 1 min 16 s de trabajo', '')}
 {kpi('0,828', 'la **misma** probabilidad en local y en Cloud Run, con la huella `35a94deb4e04ab4a`', '')}
 {kpi('0 claves', 'ni una clave JSON ni un secreto: **5 variables** públicas y WIF', '')}
 {kpi('20 €', 'de presupuesto con alertas, y `min-instances=0`: nada encendido sin uso', '')}
</div>
<div style="text-align:center;margin-top:44px;font-size:44px;font-weight:700;color:var(--acento)">¿Preguntas?</div>''',
          'Cierre con un único mensaje. Las cuatro cifras son reales: el run del 25 de noviembre, la probabilidad idéntica en local y en la nube, la ausencia de claves y el presupuesto de veinte euros con cero instancias en reposo. Lo que no se ha comprobado, con honestidad, está en la diapositiva anterior: el clonado desde el fork de un alumno, las órdenes de PowerShell y las cifras de coste. La operación del modelo en producción continúa en S5.')



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
.cover{display:flex;flex-direction:column;justify-content:flex-start;padding-top:70px;flex:1}
.chips{display:flex;gap:8px;margin-top:18px;flex-wrap:wrap}
.tag{display:inline-block;font-size:13px;padding:3px 10px;border-radius:999px;border:1px solid var(--linea);background:var(--gris);color:var(--tinta)}
.tag.ok{border-color:#86c79c;background:#ecf8f0;color:var(--ok)}.tag.warn{border-color:#e2b56b;background:#fdf6e9;color:var(--aviso)}
.card{border:1px solid var(--linea);border-radius:12px;padding:10px 14px;background:#fff}
.callout{border-left:4px solid var(--acento);background:#eef5fc;padding:9px 14px;border-radius:0 10px 10px 0;font-size:15.5px;line-height:1.4}
.small{font-size:15px;line-height:1.42}
.mono{font-family:var(--mono);font-size:.92em;background:var(--gris);padding:0 4px;border-radius:4px}
.okc{color:var(--ok)}.malc{color:var(--mal)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.thumbs{display:grid;gap:8px}.thumbs.t2{grid-template-columns:1fr 1fr}
.split{display:grid;gap:18px;min-height:0}.col,.capcol{display:flex;flex-direction:column;gap:9px;min-width:0}
.list{list-style:none;display:flex;flex-direction:column;gap:4px}.list li{font-size:15px;line-height:1.38;padding-left:16px;position:relative}
.list li::before{content:"";position:absolute;left:2px;top:8px;width:6px;height:6px;border-radius:50%;background:var(--acento)}
.ol{padding-left:24px;display:flex;flex-direction:column;gap:5px;font-size:17px}.ol.sm{font-size:15px;gap:3px}
.mira h3{color:var(--acento);font-size:15.5px}.mira .list li{font-size:14.5px}
.falla{border-color:#e2b56b;background:#fffaf0}.falla h3{color:var(--aviso);font-size:15.5px}.falla .list li{font-size:14.5px}.falla .list li::before{background:var(--aviso)}
.tbl{width:100%;border-collapse:collapse;font-size:14.5px}.tbl th{text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--suave);border-bottom:2px solid var(--linea);padding:5px 8px}
.tbl td{border-bottom:1px solid var(--linea);padding:6px 8px;line-height:1.35;vertical-align:top}
.term{border:1px solid var(--linea);border-radius:10px;background:var(--gris);overflow:hidden}
.term .bar{display:flex;align-items:center;gap:8px;padding:5px 10px;border-bottom:1px solid var(--linea);background:#eaeef3}
.term .bar em{flex:1;font-style:normal;font-size:12.5px;color:var(--suave)}
.tls{padding:6px 8px;font-family:var(--mono);font-size:13px;line-height:1.42}
.tln{display:flex;align-items:flex-start;gap:6px;padding:2px 4px}
.tln code{flex:1;white-space:pre-wrap;overflow-wrap:anywhere;font-family:var(--mono)}
.tln.c{color:var(--suave);font-style:italic}
.ps{color:var(--ok);font-weight:700}
.cp{flex:none;min-width:26px;height:24px;border-radius:6px;border:1px solid #b9c3cf;background:#fff;font-size:13px;color:var(--suave)}
.cp.ok{border-color:var(--ok);color:var(--ok)}.cpall{padding:0 10px;font-size:12px;font-family:var(--sans)}
.realbox{border:1px solid #86c79c;background:#f3fbf5;border-radius:10px;padding:8px 12px}
.realbox .rk{font-size:11.5px;letter-spacing:.07em;text-transform:uppercase;color:var(--ok);font-weight:700;margin-bottom:3px}
.realbox pre{font-family:var(--mono);font-size:12.5px;line-height:1.4;white-space:pre-wrap;overflow-wrap:anywhere}
.rot{margin:-4px 0 0}
.cap{display:flex;flex-direction:column;gap:4px;min-width:0}
.cap figcaption{font-size:12px;line-height:1.35;color:var(--suave)}
.cap .nota{color:var(--aviso)}
.zoom{display:block;position:relative;cursor:zoom-in;text-align:left}
.zoom img{display:block;max-width:100%;height:auto;border:1px solid var(--linea);border-radius:8px}
.lupa{position:absolute;right:6px;bottom:6px;font-size:11.5px;background:rgba(255,255,255,.92);border:1px solid var(--linea);border-radius:6px;padding:1px 6px;display:flex;align-items:center;gap:4px;color:var(--suave)}
.pend{border:2px dashed #c9a65e;background:#fdf9f0;border-radius:10px;min-height:150px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;padding:10px;text-align:center;font-size:13.5px;color:var(--aviso)}
.pend b{font-size:16px}
.grande .small{font-size:17.5px}.grande .list li{font-size:17px}.grande .mira .list li,.grande .falla .list li{font-size:16.5px}.grande .tbl{font-size:16.5px}.grande .tbl td{padding:8px 10px}
.grande .tls{font-size:14.5px;line-height:1.5}.grande .callout{font-size:18px}.grande .ol{font-size:19px}.grande .ol.sm{font-size:17px}.grande h3{font-size:19px}.grande .mira h3,.grande .falla h3{font-size:17px}
.grande .card{padding:13px 17px}.grande .grid4 .kpi{min-height:250px;padding-top:20px}.grande .grid4 .kpi .small{font-size:19px}.grande .grid4{margin-top:36px!important}.grande .kpi .n{font-size:30px}.grande .msg{font-size:32px}
.kpi .n{display:block;font-size:27px;line-height:1.15;color:var(--acento);margin-bottom:4px}.kpi .n.okc{color:var(--ok)}
.msg{font-size:27px;line-height:1.3;font-weight:600;border-left:6px solid var(--acento);padding:12px 20px;background:#eef5fc;border-radius:0 12px 12px 0}
svg .nodo{fill:#f4f8fc;stroke:#8fb2d6;stroke-width:1.5}svg .nodo.puerta{fill:#fdf6e9;stroke:#c9a65e}svg .nodo.ok{fill:#ecf8f0;stroke:var(--ok)}svg .nodo.mal{fill:#fdeeee;stroke:var(--mal)}
svg .fl{stroke:var(--acento);stroke-width:2;fill:none}svg .fl.dis{stroke-dasharray:5 4;stroke:#8fb2d6}
svg .t1{font:700 15px var(--sans);fill:var(--tinta);text-anchor:middle}svg .t2{font:13px var(--sans);fill:var(--suave);text-anchor:middle}
svg .tok{fill:var(--ok)}svg .tmal{fill:var(--mal)}
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
#zoombox{position:fixed;inset:0;background:rgba(20,26,34,.86);display:none;z-index:9;align-items:center;justify-content:center;padding:24px;cursor:zoom-out}
#zoombox.on{display:flex}#zoombox img{max-width:100%;max-height:100%;background:#fff;border-radius:6px}
#zoombox p{position:fixed;top:10px;left:0;right:0;text-align:center;color:#fff;font-size:13px}
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
  f.innerHTML=`<span>ML e IA · S4 · Laboratorio Cloud Journey</span><span><b>${esc(PARTES[s.dataset.part]||'')}</b> · ${i+1} / ${N}</span>`;s.appendChild(f)});
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
function zoom(on,src,alt){const z=$('#zoombox');if(on){$('#zoomimg').src=src;$('#zoomimg').alt=alt||'';}z.classList.toggle('on',!!on)}
$('#zoombox').onclick=()=>zoom(false);
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
document.addEventListener('click',async e=>{
  const z=e.target.closest('.zoom'); if(z){e.stopPropagation();zoom(true,z.dataset.src,z.dataset.alt);return}
  const b=e.target.closest('.cp'); if(!b) return; e.stopPropagation();
  const ok=await copyText(b.dataset.t); const t=b.textContent; b.classList.add('ok'); b.textContent=ok?'✓':'✗'; setTimeout(()=>{b.classList.remove('ok');b.textContent=t},1200)});
fit();
const h=parseInt((location.hash||'').slice(1),10); go(isNaN(h)?0:h-1);
addEventListener('hashchange',()=>{const n=parseInt((location.hash||'').slice(1),10);if(!isNaN(n)&&n-1!==cur)go(n-1)});
})();
"""


EXTRA_CSS = r"""
svg .nodo.gcp{fill:#e4effb;stroke:#0b5cad}svg .nodo.puerta{stroke-dasharray:6 4}
svg .zona{fill:#fbfcfe;stroke:#8fb2d6;stroke-dasharray:6 4;stroke-width:1.5}
svg .t3{font:13px var(--sans);fill:var(--suave);text-anchor:middle}svg .izq{text-anchor:start}
svg .t2.ok{fill:var(--ok);font-weight:700}svg .t2.mal{fill:var(--mal);font-weight:700}
.kpi .n.malc{color:var(--mal)}.tbl .mono{font-size:.86em}
.tbl.vars td{overflow-wrap:anywhere;word-break:break-all;font-size:13px}.tbl.vars td:first-child{word-break:normal;white-space:nowrap}
"""


def html_completo():
    construir()
    js = JS.replace('__PARTES__', json.dumps(PARTES, ensure_ascii=False))
    partes = ''.join(f'<button class="part" data-p="{k}">{esc(v)}</button>' for k, v in PARTES.items())
    return ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>Laboratorio Cloud Journey: la API en Google Cloud sin claves · ML e IA: de desarrollo a producción</title>\n'
            f'<!-- Generado por generar.py: no se edita a mano. -->\n<style>{CSS}{EXTRA_CSS}</style>\n</head>\n<body>\n'
            '<div id="prog"></div>\n<div id="viewport"><div id="stage">\n\n' + '\n\n'.join(SLIDES) + '\n\n</div></div>\n\n'
            '<aside id="notes" aria-label="Notas del ponente"><h3>Notas del ponente</h3><div id="notetext"></div><p class="small" id="notemin"></p></aside>\n'
            '<div id="index" aria-label="Índice"><h2>Índice</h2><div class="grid" id="idxgrid"></div></div>\n'
            '<div id="zoombox" aria-label="Captura ampliada"><p>Esc o clic para cerrar</p><img id="zoomimg" alt=""></div>\n'
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
    actual = SALIDA.read_text(encoding='utf-8') if SALIDA.exists() else None
    pendientes = [n for n in CAPTURAS if not (AQUI / 'img' / n).is_file()]
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
        minutos = sum(int(m) for m in re.findall(r'data-min="(\d+)"', nuevo))
        print(f'escrito {SALIDA.name}: {len(SLIDES)} diapositivas, {minutos} min')
    if pendientes:
        print(f'capturas pendientes ({len(pendientes)}): ' + ', '.join(pendientes))


if __name__ == '__main__':
    main()
