"""Genera la presentación «Del ordenador al servicio» (index.html, junto a este archivo).

Es la versión en diapositivas de 04-Proyecto-Base/docs/del-ordenador-al-servicio.md: la que el docente proyecta en S2
y el alumnado sigue en su Codespace (cada orden se copia con ⧉). Reutiliza el estilo de la presentación de S2
(slides/index.html): mismo CSS, mismas teclas (← → · O índice · S notas · F pantalla completa) y notas del ponente.

Las salidas que se muestran son REALES: las del workflow «Validar API e interfaz en dos contenedores» (GitHub Actions,
14/11/2026) y las de la interfaz en Windows. Si cambian, se actualizan en SALIDAS y se regenera.

Uso:  python generar.py              escribe index.html
      python generar.py --comprobar  no escribe; sale con 1 si index.html no está al día
"""
import argparse
import html
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
S2 = AQUI.parent
SALIDA = AQUI / 'index.html'
FECHA = '14/11/2026'

# --- Salidas reales (workflow validar-dos-contenedores.yml, ejecución del 14/11/2026, y la interfaz en Windows) -------------------
SALIDAS = {
    'imagenes': 'retencion-interfaz:local  423MB\nretencion-api:local  826MB',
    'app': '/app/requirements-api.lock\n/app/requirements-interfaz.txt\n/app/sql/fs/02_poblar_fs.sql',
    'sin_sklearn': "ModuleNotFoundError: No module named 'sklearn'",
    'listo': '{"estado":"listo","datos":"ok","modelo":"http://api:8080"}',
    'recomendar': 'origen http://api:8080 | corte 2011-12-10\n13599 0.9977 alta puesto 1\n18108 0.4159 media puesto 75\n13306 0.128 baja puesto 148\n99999 no existe en MASTER',
    'docker_ps': 'NAMES      STATUS                   PORTS\ninterfaz   Up 6 seconds (healthy)   0.0.0.0:8090->8090/tcp\napi        Up 6 seconds (healthy)   8080/tcp',
    'url_127': '{"detalle":"La API del modelo en http://127.0.0.1:8080 no responde ([Errno 111] Connection refused). ¿Está arrancada y /listo responde?"}',
    'solo_lectura': 'sh: 1: cannot create /datos/intruso: Read-only file system',
    'api_equipo': 'curl: (7) Failed to connect to 127.0.0.1 port 8080 after 0 ms: Could not connect to server',
    'api_interfaz': "b'{\"estado\":\"listo\"}'",
    'sin_volumen': '{"detalle":"No existe la base /datos/curso.db. ¿Has montado el volumen con los datos? (-v .../data/processed:/datos:ro)"}',
    'api_parada': '{"detalle":"La API del modelo en http://api:8080 no responde ([Errno -3] Temporary failure in name resolution). ¿Está arrancada y /listo responde?"}',
    'compose_ps': 'SERVICE    STATUS                    PORTS\napi        Up 11 seconds (healthy)   8080/tcp\ninterfaz   Up 5 seconds (healthy)    0.0.0.0:8090->8090/tcp',
    'local_listo': '{"estado":"listo","datos":"ok","modelo":"http://127.0.0.1:8080"}',
    'local_sin_api': '{"detalle":"La API del modelo en http://127.0.0.1:8080 no responde (…). ¿Está arrancada y /listo responde?"}',
}
REAL_GHA = f'Salida real · GitHub Actions · {FECHA}'
REAL_WIN = f'Salida real · Windows · {FECHA}'


def esc(t):
    return html.escape(t, quote=True)


def md(t):
    """`código` y **negrita** a HTML (sobre texto ya seguro)."""
    t = esc(t)
    t = re.sub(r'`([^`]+)`', r'<span class="mono">\1</span>', t)
    return re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', t)


def term(titulo, lineas, alto=None):
    """Terminal con una orden por línea; cada una con su botón ⧉ (clase .cp: el PDF la oculta). Las líneas que empiezan por # son comentarios."""
    filas = []
    for l in lineas:
        if l.startswith('#'):
            filas.append(f'<div class="tln c">{esc(l)}</div>')
        else:
            filas.append(f'<div class="tln"><span class="ps">$</span> <code>{esc(l)}</code><button class="cp" data-t="{esc(l)}" title="Copiar">⧉</button></div>')
    todo = '\n'.join(l for l in lineas if not l.startswith('#'))
    estilo = f' style="min-height:{alto}px"' if alto else ''
    return (f'<div class="term t2"><div class="bar"><i></i><i></i><i></i><em>{esc(titulo)}</em>'
            f'<button class="cp cpall" data-t="{esc(todo)}">Copiar todo</button></div><div class="tls"{estilo}>{"".join(filas)}</div></div>')


def real(clave, fuente=REAL_GHA, clase=''):
    return f'<div class="realbox {clase}"><div class="rk">{esc(fuente)}</div><pre>{esc(SALIDAS[clave])}</pre></div>'


def lista(items):
    return '<ul class="list">' + ''.join(f'<li><span>{md(i)}</span></li>' for i in items) + '</ul>'


def tabla(cab, filas, clase='tbl dens2'):
    th = ''.join(f'<th>{md(c)}</th>' for c in cab)
    tr = ''.join('<tr>' + ''.join(f'<td>{md(c)}</td>' for c in f) + '</tr>' for f in filas)
    return f'<table class="{clase}"><tr>{th}</tr>{tr}</table>'


SLIDES = []


def slide(parte, minutos, titulo, kick, h1, cuerpo, notas, enter=None, sid=None):
    # ids de los marcadores SVG únicos por diapositiva: si se repiten, el navegador usa el de una diapositiva oculta y no pinta la punta
    cuerpo = re.sub(r'(id="|url\(#)(f[a-z0-9]{1,2})(?=["\)])', lambda m: f'{m.group(1)}{m.group(2)}-s{len(SLIDES)}', cuerpo)
    attrs = f' data-part="{parte}" data-min="{minutos}" data-title="{esc(titulo)}"' + (f' data-enter="{enter}"' if enter else '') + (f' id="{sid}"' if sid else '')
    SLIDES.append(f'<section class="slide"{attrs}\n data-notes="{esc(notas)}">\n'
                  f'<p class="kick st">{esc(kick)}</p><h1 class="st">{md(h1)}</h1>\n{cuerpo}\n</section>')


# =====================================================================================================================================
# Diagramas (SVG en línea, colores del tema)
# =====================================================================================================================================
def svg_escalones():
    pasos = [('1', 'Mi ordenador', 'procesos'), ('2', 'API en imagen', 'bloque 4'), ('3', 'Interfaz en imagen', 'sin modelo ni datos'),
             ('4', 'Dos contenedores', 'red + volumen'), ('5', 'Compose', 'un archivo'), ('6', 'Producción', 'S3 · S4 · S5')]
    g = []
    for i, (n, t, s) in enumerate(pasos):
        x, y = 10 + i * 78, 300 - i * 50
        clase = 'hnode' if i < 5 else 'hnode prod'
        g.append(f'<rect class="{clase}" x="{x}" y="{y}" width="150" height="44" rx="10"/>'
                 f'<text class="htxt" x="{x + 75}" y="{y + 20}" style="font-size:15px">{n} · {esc(t)}</text>'
                 f'<text class="htxt2" x="{x + 75}" y="{y + 37}">{esc(s)}</text>')
        if i:
            g.append(f'<path class="flowpath" d="M{x - 3} {y + 50} L{x + 12} {y + 44}"/>')
    return f'<svg viewBox="0 0 560 360" role="img" aria-label="Los seis escalones">{"".join(g)}</svg>'


def svg_piezas():
    return '''<svg viewBox="0 0 1140 250" role="img" aria-label="Las cuatro piezas">
<defs><marker id="fl" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#fcd34d"/></marker></defs>
<rect class="hnode" x="10" y="85" width="150" height="80" rx="14"/><text class="htxt" x="85" y="120">Persona</text><text class="htxt2" x="85" y="142">conoce el id</text>
<rect class="hnode gold" x="250" y="70" width="230" height="110" rx="14"/><text class="htxt" x="365" y="108">INTERFAZ</text><text class="htxt2" x="365" y="132">ids → variables →</text><text class="htxt2" x="365" y="152">recomendación</text>
<rect class="hnode" x="600" y="10" width="230" height="80" rx="14"/><text class="htxt" x="715" y="45">Datos + SQL de FS</text><text class="htxt2" x="715" y="68">curso.db · 02_poblar_fs.sql</text>
<rect class="hnode" x="600" y="160" width="230" height="80" rx="14"/><text class="htxt" x="715" y="195">API del modelo</text><text class="htxt2" x="715" y="218">13 variables → probabilidad</text>
<rect class="hnode" x="930" y="160" width="200" height="80" rx="14"/><text class="htxt" x="1030" y="195">Modelo</text><text class="htxt2" x="1030" y="218">models/modelo_mlflow</text>
<path class="flowpath" d="M160 125 L246 125" marker-end="url(#fl)"/>
<path class="flowpath" d="M480 105 L596 55" marker-end="url(#fl)"/><text class="htxt3" x="520" y="62">(1) variables</text>
<path class="flowpath" d="M480 150 L596 195" marker-end="url(#fl)"/><text class="htxt3" x="520" y="200">(2) HTTP</text>
<path class="flowpath" d="M830 200 L926 200" marker-end="url(#fl)"/>
</svg>'''


def svg_hosts():
    return '''<svg viewBox="0 0 560 300" role="img" aria-label="127.0.0.1 frente a 0.0.0.0">
<defs><marker id="fh" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#fcd34d"/></marker></defs>
<rect x="150" y="20" width="390" height="260" rx="18" fill="none" stroke="#2bb3ff" stroke-dasharray="8 6" stroke-width="2"/>
<text class="htxt3" x="345" y="44">TU EQUIPO</text>
<rect class="hnode" x="200" y="70" width="290" height="60" rx="12"/><text class="htxt" x="345" y="96">uvicorn --host 127.0.0.1</text><text class="htxt2" x="345" y="117">solo atiende al propio equipo</text>
<rect class="hnode gold" x="200" y="190" width="290" height="60" rx="12"/><text class="htxt" x="345" y="216">uvicorn --host 0.0.0.0</text><text class="htxt2" x="345" y="237">atiende también desde fuera</text>
<rect class="hnode" x="10" y="125" width="110" height="60" rx="12"/><text class="htxt" x="65" y="152">otro</text><text class="htxt2" x="65" y="172">equipo</text>
<path class="flowpath bad" d="M120 145 L196 105"/><text x="150" y="112" fill="#fb7185" font-size="26" font-weight="800">✗</text>
<path class="flowpath" d="M120 165 L196 215" marker-end="url(#fh)"/><text x="145" y="222" fill="#34d399" font-size="22" font-weight="800">✓</text>
</svg>'''


def svg_local():
    return '''<svg viewBox="0 0 600 300" role="img" aria-label="Escalón 1: todo en mi ordenador">
<defs><marker id="f1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#fcd34d"/></marker></defs>
<rect x="5" y="5" width="590" height="290" rx="18" fill="rgba(43,179,255,.06)" stroke="#2bb3ff" stroke-width="2"/>
<text class="htxt3" x="300" y="30">TU ORDENADOR · conda env-ia-mlops · tu clon · tus archivos</text>
<rect class="hnode" x="25" y="60" width="120" height="56" rx="12"/><text class="htxt" x="85" y="93">navegador</text>
<rect class="hnode gold" x="200" y="50" width="180" height="76" rx="12"/><text class="htxt" x="290" y="80">interfaz</text><text class="htxt2" x="290" y="102">127.0.0.1:8090</text>
<rect class="hnode" x="430" y="50" width="150" height="76" rx="12"/><text class="htxt" x="505" y="80">API</text><text class="htxt2" x="505" y="102">127.0.0.1:8080</text>
<rect class="hnode" x="200" y="190" width="180" height="70" rx="12"/><text class="htxt" x="290" y="220">data/processed/</text><text class="htxt2" x="290" y="242">curso.db (lectura y escritura)</text>
<rect class="hnode" x="430" y="190" width="150" height="70" rx="12"/><text class="htxt" x="505" y="220">models/</text><text class="htxt2" x="505" y="242">el modelo</text>
<path class="flowpath" d="M145 88 L196 88" marker-end="url(#f1)"/><path class="flowpath" d="M380 88 L426 88" marker-end="url(#f1)"/>
<path class="flowpath" d="M290 126 L290 186" marker-end="url(#f1)"/><path class="flowpath" d="M505 126 L505 186" marker-end="url(#f1)"/>
</svg>'''


def svg_dos_contenedores(destacar=''):
    mal = destacar == 'mal'
    extra = ''
    ancho, cx, sufijo = (140, 400, '-mal') if mal else (230, 445, '')
    llamada = '' if mal else ('<path class="flowpath" d="M560 150 L816 150" marker-end="url(#f2)"/>'
                              '<text class="htxt3" x="688" y="138">http://api:8080</text>')
    if mal:
        extra = ('<path d="M470 150 C 560 110, 560 230, 470 200" fill="none" stroke="#fb7185" stroke-width="3" stroke-dasharray="6 6" marker-end="url(#f2b)"/>'
                 '<text x="560" y="128" fill="#fb7185" font-size="15" font-weight="700">127.0.0.1:8080</text>'
                 '<text x="560" y="148" fill="#fb7185" font-size="14">= él mismo: nadie escucha</text>')
    return f'''<svg viewBox="0 0 1140 330" role="img" aria-label="Dos contenedores en una red">
<defs><marker id="f2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#fcd34d"/></marker>
<marker id="f2b" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#fb7185"/></marker></defs>
<rect x="5" y="5" width="1130" height="320" rx="18" fill="rgba(43,179,255,.05)" stroke="#2bb3ff" stroke-width="2"/>
<text class="htxt3" x="24" y="30" text-anchor="start">EQUIPO (el Codespace)</text>
<rect x="290" y="45" width="830" height="190" rx="16" fill="rgba(252,211,77,.05)" stroke="#fcd34d" stroke-dasharray="8 6" stroke-width="2"/>
<text class="htxt3" x="705" y="68" fill="#fcd34d">red «retencion» · los contenedores se encuentran por su nombre</text>
<rect class="hnode" x="25" y="100" width="150" height="64" rx="12"/><text class="htxt" x="100" y="128">navegador</text><text class="htxt2" x="100" y="150">:8090</text>
<rect class="hnode gold" x="330" y="90" width="{ancho}" height="120" rx="14"/>
<text class="htxt" x="{cx}" y="122">interfaz{sufijo}</text><text class="htxt2" x="{cx}" y="146">usuario 10001</text><text class="htxt2" x="{cx}" y="166">sin modelo</text><text class="htxt2" x="{cx}" y="186">sin datos dentro</text>
<rect class="hnode" x="820" y="90" width="270" height="120" rx="14"/><text class="htxt" x="955" y="122">api</text><text class="htxt2" x="955" y="146">usuario 10001 · con el modelo</text><text class="htxt2" x="955" y="166">escucha en :8080 dentro de la red</text><text class="htxt2" x="955" y="186">sin -p: no se publica</text>
<path class="flowpath" d="M175 132 L326 132" marker-end="url(#f2)"/><text class="htxt3" x="250" y="120">-p 8090:8090</text>
{llamada}
<rect class="hnode" x="330" y="262" width="300" height="50" rx="12"/><text class="htxt" x="480" y="285">data/processed/</text><text class="htxt2" x="480" y="304">en tu carpeta, fuera de la imagen</text>
<path class="flowpath" d="M445 258 L445 214" marker-end="url(#f2)"/><text class="htxt3" x="560" y="250" text-anchor="start">-v …:/datos:ro (solo lectura)</text>
{extra}
</svg>'''


ARQ_HOY = dict(
    banda1='CONSTRUCCIÓN · una vez por versión del modelo', banda2='EJECUCIÓN · cada consulta',
    a=('Operacional', 'retail.db'), b=('Pipelines', 'RAW → MASTER → FS → ML'), c=('Entrenar', 'MLflow · retencion-90d'),
    d=('Modelo + firma', 'models/modelo_mlflow'), e=('Imagen API', 'retencion-api'), g=('Imagen interfaz', 'código + SQL de FS'),
    red='red «retencion» (Docker)', inter=('Contenedor interfaz', ':8090 · publicado con -p'), api=('Contenedor API', ':8080 · sin -p'),
    db=('curso.db', 'volumen de solo lectura'), ops=('Operación', '/salud · /listo · HEALTHCHECK', 'registros JSON por stdout', 'sin datos de clientes'),
    run='docker run')
ARQ_PROD = dict(
    banda1='CONSTRUCCIÓN · automática en el CI (S4)', banda2='EJECUCIÓN · servicios gestionados (S3)',
    a=('Sistemas de origen', 'ventas, CRM…'), b=('Pipelines orquestados', 'workflow de S4'), c=('Registro de modelos', 'MLflow · alias (S5)'),
    d=('Modelo aprobado', 'versión + firma'), e=('Artifact Registry', 'imagen API versionada'), g=('Artifact Registry', 'imagen interfaz'),
    red='red privada · IAM entre servicios', inter=('Cloud Run · interfaz', 'HTTPS · usuarios autenticados'), api=('Cloud Run · API', 'privada: solo la interfaz'),
    db=('BigQuery', 'tablas FS con permisos'), ops=('Operación', 'salud y reinicio automáticos', 'registros centralizados', 'métricas, alertas, deriva (S5)'),
    run='despliegue')


def svg_arquitectura(L, pasos=True):
    """Arquitectura de la exposición del modelo: arriba se construye, abajo se usa. L: textos (ARQ_HOY o ARQ_PROD)."""
    def caja(x, y, w, h, t, s, clase='hnode', extra=''):
        return (f'<rect class="{clase}" x="{x}" y="{y}" width="{w}" height="{h}" rx="12"/>'
                f'<text class="htxt" x="{x + w / 2:g}" y="{y + h / 2 - 3:g}" style="font-size:15px">{esc(t)}</text>'
                f'<text class="htxt2" x="{x + w / 2:g}" y="{y + h / 2 + 15:g}">{esc(s)}</text>{extra}')

    def paso(n, x, y):
        return f'<circle cx="{x}" cy="{y}" r="12" fill="#fcd34d"/><text x="{x}" y="{y + 5}" text-anchor="middle" font-size="14" font-weight="800" fill="#2b2100">{n}</text>'

    f = ' class="f"' if pasos else ''
    o = []
    o.append('<defs><marker id="fa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#fcd34d"/></marker>'
             '<marker id="fb" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#a9c8ea"/></marker></defs>')
    # franja de construcción
    o.append(f'<rect x="2" y="2" width="1136" height="140" rx="14" fill="rgba(179,156,255,.06)" stroke="#b39cff" stroke-dasharray="6 6"/>'
             f'<text class="htxt3" x="14" y="22" text-anchor="start" fill="#b39cff">{esc(L["banda1"])}</text>')
    xs = [(12, 150, 'a'), (182, 180, 'b'), (384, 170, 'c'), (576, 170, 'd'), (768, 170, 'e'), (962, 168, 'g')]
    for x, w, k in xs:
        o.append(caja(x, 40, w, 76, *L[k]))
    for (x1, w1, _), (x2, _, k2) in zip(xs[:4], xs[1:5]):
        o.append(f'<path class="flowpath" d="M{x1 + w1} 78 L{x2 - 4} 78" marker-end="url(#fa)"/>')
    # franja de ejecución
    o.append(f'<rect x="2" y="158" width="1136" height="330" rx="14" fill="rgba(43,179,255,.05)" stroke="#2bb3ff" stroke-width="2"/>'
             f'<text class="htxt3" x="14" y="178" text-anchor="start">{esc(L["banda2"])}</text>')
    o.append(f'<rect x="196" y="196" width="636" height="198" rx="16" fill="rgba(252,211,77,.05)" stroke="#fcd34d" stroke-dasharray="8 6" stroke-width="2"/>'
             f'<text class="htxt3" x="600" y="388">{esc(L["red"])}</text>')
    o.append(caja(14, 262, 130, 76, 'Persona', 'conoce el id'))
    o.append(f'<rect class="hnode gold" x="216" y="226" width="250" height="146" rx="14"/>'
             f'<text class="htxt" x="341" y="252" style="font-size:16px">{esc(L["inter"][0])}</text><text class="htxt2" x="341" y="270">{esc(L["inter"][1])}</text>'
             '<text class="htxt2" x="341" y="300" style="fill:#eef6ff">ids → 13 variables (SQL de FS)</text>'
             '<text class="htxt2" x="341" y="322" style="fill:#eef6ff">probabilidad → tramo (regla)</text>'
             '<text class="htxt2" x="341" y="344" style="fill:#eef6ff">página web · /recomendar</text>')
    o.append(f'<rect class="hnode" x="566" y="226" width="250" height="146" rx="14"/>'
             f'<text class="htxt" x="691" y="252" style="font-size:16px">{esc(L["api"][0])}</text><text class="htxt2" x="691" y="270">{esc(L["api"][1])}</text>'
             '<text class="htxt2" x="691" y="300" style="fill:#eef6ff">contrato = firma del modelo (422)</text>'
             '<text class="htxt2" x="691" y="322" style="fill:#eef6ff">modelo en memoria: predict_proba</text>'
             '<text class="htxt2" x="691" y="344" style="fill:#eef6ff">/predecir · /predecir/lote</text>')
    o.append(caja(216, 412, 250, 60, *L['db']))
    o.append(f'<rect class="hnode" x="880" y="226" width="246" height="146" rx="14"/>'
             f'<text class="htxt" x="1003" y="256" style="font-size:16px">{esc(L["ops"][0])}</text>'
             + ''.join(f'<text class="htxt2" x="1003" y="{284 + 24 * i}" style="fill:#eef6ff">{esc(t)}</text>' for i, t in enumerate(L['ops'][1:])))
    # de la construcción a la ejecución
    o.append(f'<path d="M853 116 L853 150 L691 150 L691 222" fill="none" stroke="#a9c8ea" stroke-width="2" stroke-dasharray="5 5" marker-end="url(#fb)"/>'
             f'<path d="M1046 116 L1046 186 L420 186 L420 222" fill="none" stroke="#a9c8ea" stroke-width="2" stroke-dasharray="5 5" marker-end="url(#fb)"/>'
             f'<text class="htxt2" x="770" y="145" style="fill:#a9c8ea">{esc(L["run"])}</text><text class="htxt2" x="1090" y="160" style="fill:#a9c8ea">{esc(L["run"])}</text>'
             '<path d="M272 116 L272 132 L160 132 L160 442 L212 442" fill="none" stroke="#a9c8ea" stroke-width="2" stroke-dasharray="5 5" marker-end="url(#fb)"/>'
             '<text class="htxt2" x="120" y="400" style="fill:#a9c8ea">FS escrita</text><text class="htxt2" x="120" y="416" style="fill:#a9c8ea">por los pipelines</text>')
    # los pasos de una consulta
    o.append(f'<g{f}><path class="flowpath" d="M144 286 L212 286" marker-end="url(#fa)"/>{paso(1, 178, 272)}<text class="htxt2" x="178" y="305">ids</text></g>')
    o.append(f'<g{f}><path class="flowpath" d="M341 372 L341 408" marker-end="url(#fa)"/>{paso(2, 318, 390)}<text class="htxt2" x="356" y="395" text-anchor="start">variables en el corte</text></g>')
    o.append(f'<g{f}><path class="flowpath" d="M466 272 L562 272" marker-end="url(#fa)"/>{paso(3, 514, 256)}<text class="htxt2" x="514" y="292">POST 13 variables</text></g>')
    o.append(f'<g{f}><path class="flowpath" d="M562 330 L470 330" marker-end="url(#fa)"/>{paso(4, 514, 314)}<text class="htxt2" x="514" y="350">probabilidad + avisos</text></g>')
    o.append(f'<g{f}><path class="flowpath" d="M212 318 L148 318" marker-end="url(#fa)"/>{paso(5, 178, 334)}<text class="htxt2" x="178" y="362">recomendación</text></g>')
    o.append(f'<g{f}><path d="M816 300 L876 300" fill="none" stroke="#34d399" stroke-width="2" stroke-dasharray="4 4"/><path d="M836 240 L876 240" fill="none" stroke="#34d399" stroke-width="2" stroke-dasharray="4 4"/>'
             '<text class="htxt2" x="1003" y="400" style="fill:#34d399">cada servicio dice si está vivo y listo,</text><text class="htxt2" x="1003" y="418" style="fill:#34d399">y deja una línea por petición</text></g>')
    return f'<svg viewBox="0 0 1140 490" role="img" aria-label="Arquitectura de la exposición del modelo">{"".join(o)}</svg>'


# =====================================================================================================================================
# Contenido
# =====================================================================================================================================
def construir():
    SLIDES.clear()

    # ---------------------------------------------------------------- A · Por qué
    slide('A', 1, 'Portada', 'S2 · ML e IA: de desarrollo a producción', 'Del ordenador al servicio', f'''
<div class="cover" style="height:470px"><div>
 <p class="sub st">La API y la interfaz, paso a paso: de dos procesos en tu portátil a dos contenedores que se hablan, y lo que falta para producción.</p>
 <div class="chips st"><span class="tag core">6 escalones</span><span class="tag">unos 60 min</span><span class="tag">Codespace</span><span class="tag ok">Probado con Docker real</span></div>
 <div class="card st" style="margin-top:22px"><h3>Cómo seguirla</h3><p class="small">Cada orden lleva <b>⧉</b> para copiarla en la terminal de tu Codespace, de una en una. <b>← →</b> avanzan · <b>O</b> índice · <b>F</b> pantalla completa.
 Las salidas que ves son <b>reales</b> (GitHub Actions y Windows, {FECHA}). Todo está explicado en texto en <span class="mono">04-Proyecto-Base/docs/del-ordenador-al-servicio.md</span>.</p></div>
</div><div class="hero st">{svg_escalones()}</div></div>''',
          'Esta presentación responde a lo que preguntó el grupo: ya tenemos el modelo en una API, pero ¿dónde llama el usuario?, ¿cómo pone un id o una lista y recibe una recomendación?, ¿qué diferencia hay entre tenerlo en mi ordenador y tenerlo como servicio? Vamos en seis escalones; cada uno añade una sola idea y se puede ejecutar. Que cada persona tenga el Codespace abierto con la imagen de la API del bloque 4.')

    slide('A', 2, 'La pregunta y el plan', 'Lo que nos preguntaron', 'Ya tengo la API… ¿y ahora quién la usa?', '''
<div class="split" style="grid-template-columns:1.05fr 1fr">
 <div class="card st"><h3>La API pide esto</h3><pre class="pre" style="font-size:14px">{"recencia_dias": 35, "frecuencia": 6, "monto_total": 1250.4,
 "ticket_medio": 208.4, "unidades_total": 410,
 "productos_distintos": 38, "antiguedad_dias": 310,
 "frecuencia_90d": 2, "monto_90d": 380.5,
 "frecuencia_180d": 4, "dias_medios_entre_compras": 55.0,
 "devoluciones": 1, "es_reino_unido": 1}</pre>
 <p class="small" style="margin-top:8px">Trece variables. Nadie de negocio las conoce.</p></div>
 <div class="col">
  <div class="card f"><h3>Quien hace la campaña tiene esto</h3><p class="mono" style="font-size:26px;color:var(--gold)">13599, 18108, 13306</p><p class="small">…y quiere saber <b>qué hacer</b> con cada uno.</p></div>
  <div class="card f"><h3>Hoy, en cuatro partes</h3><ul class="list"><li><span><b>A</b> · ¿por qué llevar un modelo a producción?</span></li><li><span><b>B</b> · todo en mi ordenador</span></li><li><span><b>C</b> · dos contenedores que se hablan</span></li><li><span><b>D</b> · ¿esto ya es producción?</span></li></ul></div>
 </div></div>''',
          'Muestre el JSON de la API: trece variables. Pregunte quién en marketing sabría rellenarlas. Nadie. La persona de negocio tiene ids y quiere una acción. Ese hueco es lo que llenamos hoy: una interfaz que traduce ids a variables, llama a la API y devuelve una recomendación. Y la llevamos de mi portátil a un servicio.')

    slide('A', 3, 'Modelos que no salen del portátil', 'Antes de construir · pros y contras', 'El modelo que se queda en el portátil', '''
<div class="grid2" style="gap:16px">
 <div class="card f" style="border-color:rgba(52,211,153,.6)"><h3 style="color:var(--ok)">Lo bueno (y es legítimo)</h3>''' + lista([
        '**Rápido y barato** para explorar: sin infraestructura ni permisos.',
        '**Libertad** para cambiarlo todo mientras aún no sabes qué funciona.',
        'Suficiente para un **análisis puntual**: una decisión, un informe.',
        'Sirve para **validar la idea** antes de invertir en llevarla a producción.']) + '''</div>
 <div class="card f" style="border-color:rgba(251,113,133,.6)"><h3 style="color:var(--bad)">Lo que cuesta no llevarlo</h3>''' + lista([
        '**Nadie más lo usa**: el valor se queda en una presentación.',
        '«**En mi máquina funciona**»: otra persona no obtiene lo mismo.',
        'Depende de **una persona**: si se va o se enferma, se va el modelo.',
        'Se ejecuta **a mano**: pasos olvidados, versiones distintas.',
        '**Nadie vigila** si se degrada con datos nuevos.',
        '**Datos de clientes en portátiles** y sin rastro de qué modelo decidió qué.']) + '''</div>
</div>''',
          'No demonice el cuaderno: para explorar es lo correcto. Pero un modelo que solo vive en un portátil no genera valor de forma repetida. Recorra los contras uno a uno con ejemplos del aula: ¿quién ha tenido que rehacer un análisis porque no sabía con qué versión se hizo? El de «nadie vigila» lo vamos a ver hoy con un dato real: 132 de 148 clientes salen marcados «revisar».')

    slide('A', 3, 'Producción tampoco es gratis', 'El otro lado', 'Producción tampoco es gratis: ¿cuándo merece la pena?', '''
<div class="split" style="grid-template-columns:.9fr 1.1fr">
 <div class="card f"><h3>Lo que añade producción</h3>''' + lista([
        'Infraestructura que se **paga** cada mes.',
        '**Mantenimiento**: dependencias, parches de seguridad, versiones.',
        '**Vigilancia**: registros, métricas, alertas y alguien que responda.',
        '**Disciplina**: pruebas, revisiones y despliegues controlados; cambiar es más lento.']) + '''</div>
 <div class="card f"><h3>Merece la pena si respondes «sí» a alguna</h3>''' + tabla(['Pregunta', 'Si es «sí»…'], [
        ['¿Lo usarán **otras personas o sistemas**?', 'necesita una forma de llamarlo'],
        ['¿Se decide con él **a menudo** (cada día, cada semana)?', 'no puede depender de alguien a mano'],
        ['¿Los **datos cambian** y hay que volver a puntuar?', 'necesita un proceso repetible'],
        ['¿Hay que poder **explicar qué modelo decidió qué**?', 'necesita versiones y trazas'],
        ['¿Un fallo **cuesta dinero** o clientes?', 'necesita vigilancia']]) + '''
 <p class="small" style="margin-top:8px">«Producción» no siempre es una API: a veces es un <b>proceso por lotes</b> que deja la lista de la campaña cada lunes (el laboratorio extra, <span class="mono">python -m ia_mlops.explotacion</span>).</p></div>
</div>''',
          'Equilibre el mensaje: producción tiene coste. La regla práctica es la tabla de la derecha. Si todo es «no», un cuaderno bien documentado basta. Si hay algún «sí», hay que salir del portátil. Mencione que producción puede ser por lotes: el laboratorio extra hace exactamente eso, puntuar a todos y dejar un CSV. Hoy hacemos la versión en línea: alguien pregunta por unos ids y recibe respuesta al momento.')

    slide('A', 2, 'Las cuatro piezas', 'El mapa', 'Cuatro piezas y quién usa cada una', f'''
<div class="card st" style="padding:14px 18px">{svg_piezas()}</div>
<div class="grid2" style="gap:14px;margin-top:14px">
 <div class="callout f">La <b>API no sabe qué es un id</b>: solo sabe de variables. La <b>persona no sabe qué son las variables</b>: solo conoce el id.</div>
 <div class="callout f">La <b>interfaz traduce</b>: (1) calcula las 13 variables con el SQL de FS, (2) llama a la API, (3) aplica la regla de negocio de tramos.</div>
</div>''',
          'Este es el mapa de todo lo que sigue. Insista en la frase del primer recuadro: es la razón de que existan dos servicios. La recomendación no sale del modelo: es una regla de negocio en config.SEGMENTOS_RECOMPRA, con tramos 70 y 40 por ciento que se acuerdan con quien hace la campaña.')

    slide('A', 4, 'Arquitectura de la exposición', 'La arquitectura · lo que montamos hoy', 'Cómo funciona la exposición del modelo', f'''
<div class="card st arq" style="padding:8px 10px">{svg_arquitectura(ARQ_HOY)}</div>''',
          'Diapositiva clave: vuelva a ella al final de cada escalón. Arriba, la franja morada es la CONSTRUCCIÓN, que ocurre una vez por versión del modelo: los datos operacionales pasan por los pipelines RAW, MASTER, FS y ML; se entrena y se registra en MLflow; sale el modelo con su firma; y se construyen dos imágenes, la de la API con el modelo dentro y la de la interfaz con el código y el SQL de FS, sin modelo ni datos. Abajo, la franja azul es la EJECUCIÓN de cada consulta, en cinco pasos que se revelan con la flecha: 1, la persona escribe ids en la página de la interfaz; 2, la interfaz calcula las 13 variables con el mismo SQL de FS sobre curso.db, montada en solo lectura; 3, envía las variables a la API por la red, que las valida contra la firma; 4, la API devuelve probabilidad y avisos; 5, la interfaz aplica la regla de tramos y devuelve la recomendación. A la derecha, operación: cada servicio dice si está vivo y listo y deja una línea de registro por petición, sin datos de clientes. La línea discontinua de la izquierda recuerda que curso.db la escriben los pipelines: la interfaz solo la lee.')

    # ---------------------------------------------------------------- B · Mi ordenador
    slide('B', 2, 'Proceso, puerto y dirección', 'Conceptos · 1', 'Proceso, puerto y **quién puede llamar**', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">
  <div class="card f"><h3>Proceso y puerto</h3><p class="small">Un <b>proceso</b> es un programa en marcha. Un servidor se queda <b>escuchando</b> en un <b>puerto</b>, una «puerta» numerada del equipo: la API en el <span class="mono">8080</span>, la interfaz en el <span class="mono">8090</span>. Dos procesos no comparten puerto: <span class="mono">address already in use</span>.</p></div>
  <div class="card f"><h3>Cliente y servidor</h3><p class="small">El <b>cliente</b> pide (navegador, <span class="mono">curl</span>), el <b>servidor</b> responde. Hablan <b>HTTP</b> con <b>JSON</b> y un código: <b>200</b> bien, <b>422</b> petición sin sentido, <b>503</b> ahora no puedo. La interfaz es servidor para ti y <b>cliente</b> de la API.</p></div>
 </div>
 <div class="card st" style="padding:10px">{svg_hosts()}</div>
</div>''',
          'Dibuje la analogía: el equipo es un edificio y los puertos son puertas numeradas. 127.0.0.1 es «solo atiendo a quien está dentro del edificio»; 0.0.0.0 es «atiendo en todas las puertas que den a la calle». Por eso make api usa 127.0.0.1 y las imágenes usan 0.0.0.0: dentro de un contenedor, toda llamada llega desde fuera.')

    slide('B', 2, 'Dependencias, configuración y salud', 'Conceptos · 2', 'Lo que el código no lleva dentro', '''
<div class="grid2" style="gap:16px">
 <div class="card f"><h3>Dependencias</h3><p class="small">Todo lo que el programa necesita y <b>no está en su código</b>: Python 3.11, fastapi y pandas, <span class="mono">curso.db</span>, el SQL de FS… y <b>otro servicio</b>, la API. En tu portátil «está ahí» porque lo instalaste tú. <b>Esa es la trampa.</b></p></div>
 <div class="card f"><h3>Configuración por variables de entorno</h3>''' + tabla(['Variable', 'Mi ordenador', 'Contenedor'], [
        ['`CURSO_URL_API`', '`http://127.0.0.1:8080`', '`http://api:8080`'],
        ['`CURSO_DB`', '`data/processed/curso.db`', '`/datos/curso.db`'],
        ['`CURSO_DB_SOLO_LECTURA`', '(vacía)', '`1`']]) + '''<p class="small" style="margin-top:6px">El mismo código; cambia solo lo que se le pasa desde fuera.</p></div>
 <div class="card f" style="grid-column:1/3"><h3>Vivo no es lo mismo que listo</h3><div class="grid2" style="gap:14px">
  <p class="small"><span class="badge2 c200" style="font-size:16px;min-width:0">/salud</span> ¿El proceso <b>responde</b>? Si no, se reinicia. Es lo que pregunta el <span class="mono">HEALTHCHECK</span>.</p>
  <p class="small"><span class="badge2 c503" style="font-size:16px;min-width:0">/listo</span> ¿Tiene lo que necesita (la base y la API)? Si no, <b>reiniciar no sirve</b>: el 503 dice qué falta.</p></div></div>
</div>''',
          'Tres ideas que vuelven en cada escalón. La tabla del centro es la clave del paso a contenedores: el código no cambia, cambia la configuración. Y vivo frente a listo: la interfaz puede estar viva sin poder atender porque la API se cayó; reiniciarla no arregla nada.')

    t1 = term('Dos terminales · con conda activate env-ia-mlops · desde 04-Proyecto-Base', [
        '# terminal 1: la API del modelo',
        'python -m uvicorn ia_mlops.api.app:app --host 127.0.0.1 --port 8080',
        '# terminal 2: la interfaz, que llama a esa API',
        'python -m ia_mlops.interfaz --url http://127.0.0.1:8080'])
    t2 = term('Comprobar', ['curl http://127.0.0.1:8090/salud', 'curl http://127.0.0.1:8090/listo'])
    slide('B', 3, 'Escalón 1: todo en mi ordenador', 'Escalón 1 · práctica', 'Todo en mi ordenador', f'''
<div class="split" style="grid-template-columns:1fr 1.05fr;gap:20px">
 <div class="card st" style="padding:10px">{svg_local()}</div>
 <div class="col">
  {t1}
  {t2}
  {real('local_listo', REAL_WIN)}
 </div></div>''',
          'Que todos lo arranquen. En el Codespace también funciona así, con el entorno conda. La segunda terminal imprime «Interfaz en http://127.0.0.1:8090». /listo debe decir datos ok y la URL de la API. Si alguien tiene el 8080 ocupado por el contenedor del bloque 4, que lo pare antes con docker rm -f.')

    slide('B', 3, 'La interfaz en acción', 'Escalón 1 · práctica', 'La interfaz: ids → probabilidad → recomendación', '''
<div class="split" style="grid-template-columns:1.25fr .75fr;gap:18px">
 <div class="card st" style="padding:8px;overflow:hidden"><img src="img/interfaz-consulta.png" alt="La interfaz con cuatro clientes: tres tramos y uno sin predicción" style="width:100%;height:440px;object-fit:cover;object-position:top;border-radius:10px"></div>
 <div class="col">
  <div class="card f mini2"><h3>Prueba en la página</h3>''' + lista([
        '`13599` → 99,8 %, `alta`, puesto 1 de 148',
        '**Ejemplo**: tres tramos y un id que no existe',
        'Carga un **CSV** con columna `cliente_id`',
        'Corte `2011-03-01`: ¿por qué cambian las variables?']) + '''</div>
  <div class="card f mini2"><h3>Para pensar</h3><p class="small">Casi todos salen <b>⚠ Revisar</b>: <span class="mono">antiguedad_dias=738</span> fuera de lo visto al entrenar <span class="mono">[1, 364]</span>. El modelo se entrenó con cortes de 2010. <b>Así se ve un modelo que nadie vigila</b> (deriva, S5).</p></div>
 </div></div>''',
          'Abra http://127.0.0.1:8090. La captura es real, de la interfaz con la muestra. Recorra la tabla: puesto y decil son entre los 148 clientes del corte; el tramo y la recomendación salen de la regla de negocio. El aviso «revisar» enlaza con la diapositiva de pros y contras: sin vigilancia, un modelo se queda viejo sin que nadie lo note. La pregunta de los tramos: ¿a quién va el incentivo, al medio o al de más probabilidad como en el laboratorio extra? Depende del objetivo de negocio.')

    slide('B', 2, 'Por qué no se puede sacar', 'Escalón 1 · conclusión', '«En mi máquina funciona»… y solo ahí', '''
<div class="split" style="grid-template-columns:1.2fr .8fr">
 <div class="card st">''' + tabla(['Depende de…', '¿Qué pasa en otro equipo?'], [
        ['Tu **entorno conda** y sus versiones', 'Otras versiones, otras probabilidades… o no arranca'],
        ['Tus **archivos** (`models/`, `curso.db`)', 'Si no ejecutó el pipeline, no existen'],
        ['Tu **sistema operativo**', 'Cambian comandos y comillas (PowerShell o bash)'],
        ['Tu **sesión abierta**', 'Cierras el portátil y el servicio desaparece'],
        ['`127.0.0.1`', 'Nadie más puede llamarlo']]) + '''</div>
 <div class="col">
  <div class="card f"><h3>Prueba vivo frente a listo</h3><p class="small">Para la API (Ctrl+C en la terminal 1): <span class="mono">/salud</span> sigue en 200 y <span class="mono">/listo</span>:</p>''' + real('local_sin_api', REAL_WIN) + '''</div>
  <div class="callout f" style="font-size:18px">Sirve para <b>desarrollar</b> y <b>demostrar</b>. No es un servicio: nadie puede depender de él.</div>
 </div></div>''',
          'Esta diapositiva es la que pidieron explicar: por qué lo de mi ordenador no se puede sacar. No es que esté mal hecho; es que depende de cosas que solo existen en ese equipo. Haga que paren la API y vean el 503: la interfaz está viva pero no lista. Luego que la vuelvan a arrancar o la paren del todo, porque en la parte C usaremos el puerto 8080 dentro de Docker.')

    # ---------------------------------------------------------------- C · Contenedores
    slide('C', 1, 'Conceptos de contenedores', 'Conceptos · 3 · repaso', 'Lo mínimo de contenedores para seguir', '''
<div class="grid3">
''' + ''.join(f'<div class="card f mini2"><h3>{md(t)}</h3><p class="small">{md(d)}</p></div>' for t, d in [
        ('Imagen', 'Plantilla congelada: base, Python, paquetes y código. No cambia.'),
        ('Contenedor', 'Una imagen **en ejecución**. Al borrarlo se pierde lo que escribió dentro.'),
        ('Contexto y `.dockerignore`', 'Lo que se envía a Docker al construir, y lo que **no**.'),
        ('`-p equipo:contenedor`', 'Abre una puerta del equipo hacia el contenedor. Sin `-p`, no se llega.'),
        ('`-v origen:destino:ro`', 'Monta una carpeta del equipo dentro, en **solo lectura**. Los datos quedan fuera de la imagen.'),
        ('Red', 'Los contenedores de una red se encuentran **por su nombre**: Docker hace de guía telefónica.'),
        ('`-e` / `ENV`', 'La configuración, desde fuera.'),
        ('`USER 10001`', 'Sin privilegios: si alguien lo ataca, puede hacer menos.'),
        ('`HEALTHCHECK`', 'Docker pregunta «¿estás vivo?» y `docker ps` muestra `(healthy)`.')]) + '</div>',
          'Repaso rápido de las presentaciones de contenedores 1 y 2, que eran obligatorias antes de S2. Pase deprisa; vuelva sobre red y volumen, que son nuevas en la práctica de hoy.')

    slide('C', 1, 'Escalón 2: la API en su imagen', 'Escalón 2 · repaso del bloque 4', 'La API ya vive en una imagen', '''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">''' + term('Lo que hiciste en el bloque 4', ['docker build -f deploy/docker/Dockerfile -t retencion-api:local .']) + '''
  <div class="card f"><h3>Lleva</h3><p class="small">Python 3.11, versiones exactas (<span class="mono">requirements-api.lock</span>), <span class="mono">ia_mlops/</span> y <b>el modelo</b>.</p></div>
  <div class="card f"><h3>No lleva</h3><p class="small">Datos de clientes, cuadernos, pruebas ni SQL (<span class="mono">.dockerignore</span> de la raíz).</p></div></div>
 <div class="col">
  <div class="card f" style="border-color:rgba(52,211,153,.6)"><h3 style="color:var(--ok)">Qué ganamos</h3><p class="small">Ya no depende de tu conda ni de tu sistema operativo: cualquier equipo con Docker obtiene <b>lo mismo</b>, hasta el último decimal (lo comprobaste con <span class="mono">comparar</span>).</p></div>
  <div class="card f" style="border-color:rgba(251,191,36,.6)"><h3 style="color:var(--warn)">Qué falta</h3><p class="small">Sigue pidiendo <b>13 variables</b>. Falta la pieza para personas: la interfaz, en su propia imagen.</p></div></div>
</div>''',
          'Si alguien no tiene la imagen de la API, que la construya ahora: tarda un par de minutos la primera vez. Mientras, explique que el escalón 2 resuelve la mitad del problema de «en mi máquina funciona», pero solo para la API.')

    slide('C', 1, 'Escalón 3: ¿por qué otra imagen?', 'Escalón 3 · diseño', '¿Por qué una imagen aparte para la interfaz?', '''
<div class="loop" style="grid-template-columns:repeat(3,1fr)">
 <div class="lstep f"><div class="n">1</div><b>Sin datos de clientes en la imagen del modelo</b><p>Si la API buscara las variables por id, <span class="mono">curso.db</span> viajaría dentro y cualquiera con la imagen tendría los datos.</p></div>
 <div class="lstep f"><div class="n">2</div><b>Cada pieza cambia por un motivo</b><p>Reentrenas el modelo sin tocar la interfaz; cambias la página o los tramos sin reconstruir el modelo.</p></div>
 <div class="lstep f"><div class="n">3</div><b>Cada pieza escala por separado</b><p>En producción puede haber diez copias de la API y una sola interfaz.</p></div>
</div>''',
          'Pregunte antes de mostrar: ¿por qué no meter la interfaz en la imagen de la API? Recoja respuestas y luego revele las tres. La primera es la de más peso: seguridad y privacidad de los datos.')

    slide('C', 2, 'La receta de la interfaz', 'Escalón 3 · interfaz.Dockerfile', 'La receta, línea a línea', '''
<div class="split" style="grid-template-columns:1fr 1fr;gap:20px">
 <div class="col" id="dklines" style="gap:7px"></div>
 <div class="card" id="dkdet" style="min-height:420px"></div>
</div>''',
          'Pulse cada bloque. Tres decisiones a destacar. Uno: -c requirements-api.lock es un archivo de restricciones; no instala nada por sí mismo, solo fija versiones, y así las dos imágenes usan las mismas. Dos: no se copia ni models ni data. Tres: HEALTHCHECK pregunta a /salud y no a /listo.', enter='dock')

    t3 = term('Terminal del Codespace · desde 04-Proyecto-Base', [
        'docker build -f deploy/docker/interfaz.Dockerfile -t retencion-interfaz:local .',
        "docker image ls 'retencion-*'",
        'docker run --rm --entrypoint sh retencion-interfaz:local -c \'find /app -type f -not -path "*/ia_mlops/*"\'',
        'docker run --rm --entrypoint python retencion-interfaz:local -c "import sklearn"'])
    ancho_interfaz = f'{423 / 826 * 100:.0f}'
    slide('C', 3, 'Construir y mirar dentro', 'Escalón 3 · práctica', 'Construir y comprobar que no lleva nada de más', f'''
<div class="split" style="grid-template-columns:1.1fr .9fr;gap:18px">
 <div class="col">
  {t3}
  <div class="card f mini2"><h3>Cada imagen, su lista de exclusiones</h3><p class="small"><span class="mono">interfaz.Dockerfile.dockerignore</span>: Docker la usa en lugar de la de la raíz. Estrategia: <b>excluir todo</b> (<span class="mono">*</span>) y dejar pasar solo lo que se copia (<span class="mono">!ia_mlops</span>, <span class="mono">!sql/fs/02_poblar_fs.sql</span>…).</p></div>
 </div>
 <div class="col">
  <div class="card f mini2"><h3>Tamaño</h3>
   <div class="szrow"><span class="mono">interfaz</span><div class="szbar" style="width:{ancho_interfaz}%"><b>423 MB</b></div></div>
   <div class="szrow"><span class="mono">api</span><div class="szbar api" style="width:100%"><b>826 MB</b></div></div>
   <p class="small" style="margin-top:6px">La mitad: sin scikit-learn, scipy ni mlflow.</p></div>
  {real('app', clase='f')}
  {real('sin_sklearn', clase='f')}
 </div></div>''',
          'Que construyan la imagen. La primera vez descarga paquetes: un par de minutos. Las salidas de la derecha son las del workflow real. Fuera de ia_mlops solo hay tres archivos: ni modelo ni datos. Y el import de sklearn falla, como debe: esta imagen no ejecuta el modelo.')

    slide('C', 2, 'Escalón 4: el diagrama', 'Escalón 4 · el servicio', 'Dos contenedores que se hablan', f'''
<div class="card st" style="padding:12px 14px">{svg_dos_contenedores()}</div>
<div class="grid3" style="margin-top:12px">
 <div class="callout f" style="font-size:17px"><b>Red</b>: la interfaz llama a <span class="mono">http://api:8080</span>, por <b>nombre</b>.</div>
 <div class="callout f" style="font-size:17px"><b>Puertos</b>: solo la interfaz tiene <span class="mono">-p</span>. La API no se publica.</div>
 <div class="callout f" style="font-size:17px"><b>Datos</b>: un volumen <span class="mono">:ro</span>. Se leen; no se pueden tocar.</div>
</div>''',
          'Esta es la diapositiva central. Recorra el dibujo de izquierda a derecha: el navegador entra por la única puerta abierta, -p 8090; la interfaz llama a la API por su nombre dentro de la red; la API no tiene puerta al exterior; los datos están en tu carpeta y entran en solo lectura. Principio: exponer lo mínimo.')

    t4 = term('Terminal del Codespace · desde 04-Proyecto-Base', [
        '# 1. la red',
        'docker network create retencion',
        '# 2. la API: sin -p, no se publica',
        'docker run -d --name api --network retencion retencion-api:local',
        'docker ps',
        '# 3. la interfaz: su puerto, sus datos en solo lectura',
        'docker run -d --name interfaz --network retencion -p 8090:8090 -v "$PWD/data/processed:/datos:ro" retencion-interfaz:local',
        '# 4. comprobar',
        'curl http://127.0.0.1:8090/listo'])
    ps_vol = esc('-v "${PWD}\\data\\processed:/datos:ro"')
    slide('C', 4, 'Paso a paso', 'Escalón 4 · práctica', 'Paso a paso: red, API e interfaz', f'''
<div class="split" style="grid-template-columns:1.15fr .85fr;gap:18px">
 <div class="col">
  {t4}
  <p class="small">Espera a que <span class="mono">docker ps</span> muestre <span class="mono">(healthy)</span> en la API. En PowerShell (Docker Desktop, sin probar): <span class="mono">{ps_vol}</span>.</p>
 </div>
 <div class="col">
  {real('listo', clase='f')}
  {real('docker_ps', clase='f')}
  <div class="card f mini2"><p class="small">Fíjate en los puertos: la interfaz tiene <span class="mono">0.0.0.0:8090->8090</span> (publicado); la API solo <span class="mono">8080/tcp</span>: escucha en su red, sin puerta al equipo.</p></div>
 </div></div>''',
          'Dicte despacio, de una en una. El error más común aquí es lanzar la interfaz antes de que la API esté sana: no pasa nada, /listo dará 503 unos segundos. /listo debe mostrar «modelo»: «http://api:8080»; eso prueba que llegó por nombre. Lea con el grupo la columna PORTS de docker ps.')

    t5 = term('Terminal del Codespace', ['curl -X POST http://127.0.0.1:8090/recomendar -H "Content-Type: application/json" -d \'{"cliente_ids": [13599, 18108, 13306, 99999]}\''])
    slide('C', 2, 'El mismo resultado', 'Escalón 4 · comprobación', 'Mismos números, otro sitio', f'''
<div class="split" style="grid-template-columns:1fr 1fr;gap:18px">
 <div class="col">
  {t5}
  {real('recomendar', clase='f')}
 </div>
 <div class="col">
  <div class="card f"><h3>Igual que en tu Windows</h3>''' + tabla(['Cliente', 'Escalón 1 (Windows)', 'Escalón 4 (contenedores)'], [
        ['13599', '0,9977 · alta', '0,9977 · alta'], ['18108', '0,4159 · media', '0,4159 · media'], ['13306', '0,128 · baja', '0,128 · baja']]) + '''
   <p class="small" style="margin-top:8px">El modelo y los datos son los mismos: solo cambió <b>dónde corren</b>.</p></div>
  <div class="callout f" style="font-size:18px">Abre la página: pestaña <b>Puertos</b> del Codespace → <b>8090</b>.</div>
 </div></div>''',
          'Compare con lo que vieron en el escalón 1. Si los números no coinciden, algo está mal: otra base o otro modelo. En el Codespace la página se abre desde la pestaña Puertos; GitHub la reenvía de forma privada, solo para la cuenta de cada persona.')

    t6 = term('Pruébalo', [
        'docker run -d --name interfaz-mal --network retencion -p 8091:8090 -e CURSO_URL_API=http://127.0.0.1:8080 -v "$PWD/data/processed:/datos:ro" retencion-interfaz:local',
        'curl http://127.0.0.1:8091/listo',
        'docker rm -f interfaz-mal'])
    slide('C', 2, 'El error clásico', 'Escalón 4 · el error más frecuente', '`127.0.0.1` dentro de un contenedor es **él mismo**', f'''
<div class="card st arq pq" style="padding:6px 10px">{svg_dos_contenedores('mal')}</div>
<div class="split" style="grid-template-columns:1.1fr .9fr;gap:16px;margin-top:10px">
 {t6}
 {real('url_127', clase='f')}
</div>''',
          'El error que más se repite al pasar de procesos a contenedores. En el escalón 1 la API estaba en 127.0.0.1 porque las dos piezas compartían equipo. En un contenedor, 127.0.0.1 es el propio contenedor y allí no escucha nadie en el 8080. El 503 de /listo lo dice sin adivinar: Connection refused.')

    slide('C', 4, 'Romper a propósito', 'Escalón 4 · laboratorio', 'Romper a propósito: ¿qué esperas?', '''
<div class="split" style="grid-template-columns:.8fr 1.2fr;gap:18px">
 <div class="col" id="rbtns" style="gap:7px"></div>
 <div class="card" id="rdet" style="min-height:440px"></div>
</div>''',
          'Que cada persona apunte lo que espera antes de pulsar. Las salidas son las del workflow real. La de «parar la API» es la más rica: el motivo no es connection refused sino name resolution, porque al parar el contenedor su nombre desaparece de la red. Vivo no es listo: /salud sigue en 200. Al terminar: docker rm -f api interfaz y docker network rm retencion.', enter='romper')

    t7 = term('Terminal del Codespace · desde 04-Proyecto-Base', [
        'docker rm -f api interfaz; docker network rm retencion',
        'docker compose -f deploy/docker/compose.yaml up --build -d',
        'docker compose -f deploy/docker/compose.yaml ps',
        'docker compose -f deploy/docker/compose.yaml logs -f interfaz',
        'docker compose -f deploy/docker/compose.yaml down'])
    slide('C', 3, 'Escalón 5: Compose', 'Escalón 5 · un archivo', 'Lo mismo, escrito una vez: Docker Compose', f'''
<div class="split" style="grid-template-columns:1fr 1fr;gap:18px">
 <div class="col">
  {t7}
  {real('compose_ps', clase='f')}
  <p class="small f">La interfaz arrancó <b>6 s después</b>: Compose esperó a que la API estuviera sana (<span class="mono">depends_on: service_healthy</span>).</p>
 </div>
 <div class="card f">''' + tabla(['A mano', 'En compose.yaml'], [
        ['`docker network create retencion`', 'automática (`name: retencion`)'],
        ['`--name api`', '`services: api:`'],
        ['`docker build -f …`', '`build: {context, dockerfile}`'],
        ['`-p 8090:8090`', '`ports: ["8090:8090"]`'],
        ['`-v …/data/processed:/datos:ro`', '`volumes: ["../../data/processed:/datos:ro"]`'],
        ['`-e CURSO_URL_API=…`', '`environment:`'],
        ['mirar `docker ps` hasta `(healthy)`', '`depends_on: condition: service_healthy`']]) + '''
  <p class="small" style="margin-top:8px">Compose sirve para <b>un equipo</b>. Para muchos, lo hacen plataformas como Cloud Run o Kubernetes (S3 y S4).</p></div>
</div>''',
          'Cuatro órdenes largas con banderas no se repiten igual cada vez: Compose las escribe una vez y además documenta. Abra deploy/docker/compose.yaml y lea la tabla con el archivo al lado. Las rutas del archivo se resuelven desde deploy/docker, por eso el contexto es ../..')

    # ---------------------------------------------------------------- D · Producción
    slide('D', 3, '¿Ya es producción?', 'Escalón 6 · honestidad', 'Ya tienes el artefacto. El Codespace **no** es producción', '''
<div class="card st" style="padding:12px 18px">''' + tabla(['Aspecto', 'En el Codespace (hoy)', 'En producción', 'En el curso'], [
        ['**Dónde corre**', 'una máquina tuya que se apaga', 'plataforma gestionada que lo mantiene y reinicia', 'S3 · Cloud Run'],
        ['**Quién llega**', 'solo tú (puerto privado)', 'usuarios autenticados; la API solo desde servicios autorizados', 'S3 · IAM'],
        ['**Imágenes**', 'construidas a mano', 'construidas en el CI, versionadas en un registro', 'S3–S4 · Artifact Registry'],
        ['**Datos**', 'SQLite montado como volumen', 'almacén gestionado, con permisos y copias', 'S3 · BigQuery'],
        ['**Secretos**', 'no hay', 'en un gestor de secretos, nunca en la imagen', 'S3 · Secret Manager'],
        ['**Despliegue**', '`docker compose up`', 'automático, con pruebas y aprobación', 'S4 · CI/CD'],
        ['**Vigilancia**', '`docker logs`', 'registros, métricas y alertas', 'S3 y S5'],
        ['**Calidad del modelo**', 'el aviso «revisar»', 'deriva, reentrenamiento y vuelta atrás', 'S5']], clase='tbl dens2 big') + '''</div>
<div class="callout f" style="margin-top:12px">Pasar a producción <b>no cambia el código ni las imágenes</b>: cambia <b>dónde</b> corren y <b>lo que las rodea</b>. Por eso hoy separamos las piezas, sacamos los datos y pusimos la configuración fuera.</div>''',
          'Sea honesto: lo de hoy es el artefacto que iría a producción, pero no es producción. Recorra la tabla fila a fila y diga en qué sesión se ve cada cosa. La última frase es la idea que deben llevarse: todo lo que hicimos hoy, separar, sacar datos, configurar por entorno, es lo que hace que el salto a producción no obligue a reescribir nada.')

    slide('D', 2, 'La misma arquitectura en producción', 'Escalón 6 · el mapa a producción', 'La misma arquitectura, en producción', f'''
<div class="card st arq" style="padding:8px 10px">{svg_arquitectura(ARQ_PROD, pasos=False)}</div>''',
          'Ponga esta diapositiva al lado de la de arquitectura del principio: las cajas y las flechas son las mismas. Cambia en qué se convierte cada pieza. Las imágenes se guardan versionadas en Artifact Registry. Los dos contenedores pasan a dos servicios de Cloud Run: la interfaz con HTTPS y usuarios autenticados, y la API privada, que solo puede llamar la interfaz (IAM). curso.db pasa a tablas en BigQuery con permisos. La construcción la hace el workflow de S4, con pruebas y aprobación. El registro de modelos y la vuelta atrás con un alias son de S5, igual que métricas, alertas y deriva. Esto es el mapa de lo que viene: hoy no se despliega nada en GCP.')

    slide('D', 1, 'Los escalones en una tabla', 'Resumen', 'Los escalones, de un vistazo', '''
<div class="card st" style="padding:12px 18px">''' + tabla(['', 'Qué corre', 'Depende de', 'Quién llega', 'Datos'], [
        ['**1 · Mi ordenador**', 'dos procesos Python', 'tu conda, tus archivos, tu sesión', 'solo tú (`127.0.0.1`)', 'tu carpeta, con escritura'],
        ['**2 · API en imagen**', 'un contenedor', 'solo la imagen', 'tú, por `-p 8080`', 'no usa'],
        ['**3–4 · Dos contenedores**', 'dos contenedores en una red', 'solo las imágenes', 'tú, solo a la interfaz', 'volumen `:ro`'],
        ['**5 · Compose**', 'lo mismo, en un archivo', 'el archivo y las imágenes', 'igual', 'igual'],
        ['**6 · Producción**', 'las mismas imágenes', 'la plataforma', 'usuarios autenticados', 'almacén gestionado']], clase='tbl dens2 big') + '''</div>
<div class="grid2" style="margin-top:12px;gap:14px">
 <div class="callout f" style="font-size:18px">Del 1 al 2: <b>reproducible</b>. Del 2 al 4: <b>separado y protegido</b>.</div>
 <div class="callout f" style="font-size:18px">Del 4 al 5: <b>documentado</b>. Del 5 al 6: <b>gestionado y vigilado</b>.</div>
</div>''',
          'Repase la tabla de arriba abajo con una sola palabra por salto: reproducible, separado, documentado, gestionado. Si queda tiempo, pida a alguien que explique con sus palabras un salto.')

    slide('D', 2, 'Autoevaluación', 'Comprueba que lo tienes', 'Seis preguntas', '''
<div class="grid2" style="gap:12px">
''' + ''.join(f'<div class="card mini2"><h3>{i}. {md(p)}</h3><p class="small f">{md(r)}</p></div>' for i, (p, r) in enumerate([
        ('¿Por qué la interfaz llama a `http://api:8080` y no a `127.0.0.1`?', 'Dentro de un contenedor, `127.0.0.1` es él mismo. En la red, Docker resuelve `api` al contenedor de la API.'),
        ('¿Por qué la API no lleva `-p`?', 'Nadie de fuera necesita hablarle: solo la interfaz, dentro de la red. Exponer lo mínimo.'),
        ('¿Por qué los datos van en un volumen?', 'La imagen se copia y se comparte: no debe llevar datos de clientes. Con `:ro`, no se pueden estropear.'),
        ('La API se cae: ¿qué dan `/salud` y `/listo`?', '`/salud` 200 y `/listo` 503. Si el `HEALTHCHECK` mirara `/listo`, Docker reiniciaría la interfaz sin arreglar nada.'),
        ('¿Qué cambia en el código del escalón 1 al 4? ¿Y al 6?', 'Nada. Cambian la configuración y dónde corren las piezas.'),
        ('¿Cuándo NO merece la pena llevar un modelo a producción?', 'Cuando es un análisis puntual o un prototipo que nadie más usará ni repetirá.')], 1)) + '</div>',
          'Lea cada pregunta, deje unos segundos y revele la respuesta con la flecha. Las respuestas aparecen de una en una. Si hay tiempo, use la sexta para volver al principio: pros y contras.')

    slide('D', 1, 'Cierre', 'Cierre', 'Qué te llevas', '''
<div class="grid2">
 <div class="card f"><h3>Hoy</h3>''' + lista([
        'Por qué (y cuándo) sacar un modelo del **portátil**',
        'Una **interfaz** que convierte ids en recomendaciones',
        '**Dos imágenes**: la del modelo y la de la interfaz, sin datos',
        '**Red, puertos, volumen `:ro`** y vivo frente a listo',
        '**Compose** y lo que falta para producción']) + '''</div>
 <div class="card f"><h3>Para seguir</h3>''' + lista([
        'Guía completa: `docs/del-ordenador-al-servicio.md`',
        'Recorrido de clase: `practica/interfaz-de-consulta.md`',
        'Al acabar: `docker compose -f deploy/docker/compose.yaml down`',
        'S3: esta imagen, en **Cloud Run**']) + '''</div>
</div>
<p class="small" style="margin-top:10px">Probado con Docker real en GitHub Actions (''' + FECHA + '''). Aún sin recorrer a mano en un Codespace: anota lo que te salga distinto.</p>''',
          'Cierre recordando la pregunta inicial: dónde y cómo llama el usuario al modelo. Respuesta: a una interfaz que conoce los datos, que llama a una API que conoce el modelo, cada una en su contenedor. Pida que anoten cualquier diferencia que vean en su Codespace: el material se probó en GitHub Actions y todavía no se ha recorrido a mano en un Codespace.')


# =====================================================================================================================================
# Datos de las diapositivas interactivas
# =====================================================================================================================================
DOCKERFILE = [
    ('FROM python:3.11-slim', 'Base', 'La misma base que la API: el mismo Python que el entorno del curso.', 'Menos sistema, menos que mantener y vigilar.'),
    ('ENV CURSO_DB=/datos/curso.db \\\n    CURSO_DB_SOLO_LECTURA=1 \\\n    CURSO_URL_API=http://api:8080', 'Configuración', 'Valores por defecto. Se cambian al arrancar con -e, sin reconstruir la imagen.', 'Dónde están los datos y la API no es cosa del código.'),
    ('COPY requirements-api.lock requirements-interfaz.txt ./\nRUN pip install -c requirements-api.lock \\\n    -r requirements-interfaz.txt', 'Dependencias', 'Solo fastapi, uvicorn, pydantic, pandas y numpy. -c es un archivo de RESTRICCIONES: no instala nada por sí mismo, fija la versión de lo que se instala. Las dos imágenes usan las mismas versiones.', 'Sin scikit-learn ni mlflow: la interfaz no ejecuta el modelo.'),
    ('COPY ia_mlops/ ia_mlops/\nCOPY sql/fs/02_poblar_fs.sql sql/fs/…', 'Código y SQL', 'El paquete y el SQL con el que se calculan las variables. Nada de models/ ni de data/.', 'Lo que no está en la imagen no se puede filtrar desde la imagen.'),
    ('RUN useradd --uid 10001 … && mkdir /datos\nUSER 10001', 'Sin root', 'Un usuario sin privilegios y el punto de montaje de los datos.', 'Mismo criterio que la API: docker exec interfaz id -u da 10001.'),
    ('EXPOSE 8090\nHEALTHCHECK … /salud', 'Puerto y salud', 'EXPOSE documenta el puerto (no lo publica: eso es -p). Docker pregunta a /salud cada 30 s.', '/salud y no /listo: si la API cae, reiniciar la interfaz no arregla nada.'),
    ('CMD ["uvicorn", "ia_mlops.interfaz.app:app",\n     "--host", "0.0.0.0", "--port", "8090"]', 'Arranque', '0.0.0.0: dentro de un contenedor, las llamadas siempre llegan «desde fuera».', 'Con 127.0.0.1 nadie podría llegar, ni con -p.'),
]

ROTURAS = [
    ('Escribir en los datos', "docker exec interfaz sh -c 'echo x > /datos/intruso'", 'falla', 'solo_lectura', ':ro protege el dato aunque el código tenga un error.'),
    ('La API desde el equipo', 'curl http://127.0.0.1:8080/salud', 'no conecta', 'api_equipo', 'Sin -p no hay puerta.'),
    ('La API desde la interfaz', "docker exec interfaz python -c \"import urllib.request; print(urllib.request.urlopen('http://api:8080/listo').read())\"", '200', 'api_interfaz', 'Dentro de la red, por nombre, sí.'),
    ('Interfaz sin volumen', 'docker run -d --name sin-datos --network retencion -p 8092:8090 retencion-interfaz:local\ncurl http://127.0.0.1:8092/listo', '503', 'sin_volumen', 'Los datos no están en la imagen: hay que montarlos.'),
    ('Parar la API', 'docker stop api\ncurl http://127.0.0.1:8090/salud     # 200\ncurl http://127.0.0.1:8090/listo', '503', 'api_parada', 'Vivo no es listo. Y el motivo: al parar el contenedor, el nombre «api» desaparece de la red.'),
]


def js_datos():
    import json
    dk = [dict(l=l, t=t, d=d, r=r) for l, t, d, r in DOCKERFILE]
    ro = [dict(t=t, c=c, e=e, s=SALIDAS[k], l=l) for t, c, e, k, l in ROTURAS]
    return f'const DK={json.dumps(dk, ensure_ascii=False)};\nconst RO={json.dumps(ro, ensure_ascii=False)};\nconst FUENTE={json.dumps(REAL_GHA, ensure_ascii=False)};'


# =====================================================================================================================================
# Marco: CSS de la presentación de S2 + lo propio; JavaScript del visor (mismo comportamiento y teclas)
# =====================================================================================================================================
CSS_EXTRA = r"""
/* ---------- Del ordenador al servicio ---------- */
.hero svg{width:100%;height:100%}
.hnode.gold{stroke:var(--gold)} .hnode.prod{stroke:var(--ok);stroke-width:2.5}
.htxt2{fill:var(--muted);font-size:13px;text-anchor:middle;font-family:var(--sans)}
.htxt3{fill:var(--gold);font-size:13px;font-weight:700;letter-spacing:.06em;text-anchor:middle;font-family:var(--sans)}
.flowpath.bad{stroke:var(--bad)}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.mini2{padding:12px 16px!important}.mini2 h3{font-size:17px;margin-bottom:4px}.mini2 .small{font-size:15px;line-height:1.4}
.mini2 .list li{font-size:16px}.mini2 .list li::before{margin-top:6px}
.t2 .bar{justify-content:flex-start}.t2 .bar em{flex:1}
.t2 .tls{padding:8px 10px 10px;font-family:var(--mono);font-size:14px;line-height:1.45}
.t2 .tln{display:flex;align-items:flex-start;gap:6px;padding:2px 4px;border-radius:6px}
.t2 .tln:hover{background:rgba(255,255,255,.05)}
.t2 .tln code{flex:1;white-space:pre-wrap;overflow-wrap:anywhere;color:#d6e9ff}
.t2 .tln.c{color:var(--muted);font-style:italic;padding-top:5px}
.t2 .ps{color:var(--ok)}
.cp{flex:none;width:26px;height:24px;border-radius:6px;border:1px solid rgba(255,255,255,.2);font-size:13px;color:var(--muted)}
.cp:hover{border-color:var(--blue);color:var(--text)}
.cp.ok{border-color:var(--ok);color:var(--ok)}
.cpall{width:auto;padding:0 10px;font-family:var(--sans);font-size:12px}
.realbox{background:#021326;border:1px solid rgba(52,211,153,.45);border-radius:12px;padding:8px 12px}
.realbox .rk{font-size:11.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--ok);font-weight:700;margin-bottom:3px}
.realbox pre{font-family:var(--mono);font-size:13px;line-height:1.4;white-space:pre-wrap;overflow-wrap:anywhere;color:#d6e9ff}
.tbl.dens2{font-size:15px}.tbl.dens2 td{font-family:var(--sans);font-size:14.5px;padding:5px 9px;line-height:1.3}.tbl.dens2 th{padding:5px 9px;font-size:12px}
.tbl.dens2 td .mono{font-size:13.5px}
.tbl.big td{font-size:16px;padding:6px 10px}
.szrow{display:flex;align-items:center;gap:10px;margin:6px 0}.szrow>span{width:70px;font-size:14px}
.szbar{height:26px;border-radius:7px;background:linear-gradient(90deg,var(--ok),#1b9e73);display:flex;align-items:center;padding:0 8px;color:#032b1c;font-size:13px}
.szbar.api{background:linear-gradient(90deg,var(--blue),#1d8fdc);color:#031a33}
.rbtn{display:block;width:100%;text-align:left;padding:10px 14px;border-radius:11px;border:1px solid rgba(255,255,255,.14);
  background:linear-gradient(180deg,rgba(255,255,255,.085),rgba(255,255,255,.035));font-size:16px;transition:.2s}
.rbtn:hover{border-color:var(--blue)}.rbtn.sel{background:linear-gradient(180deg,rgba(43,179,255,.30),rgba(43,179,255,.12));border-color:var(--blue)}
.rbtn small{display:block;color:var(--muted);font-size:13px}
#rdet pre.pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:14px}
.reveal{margin-top:10px}
.arq svg{display:block;width:100%;max-height:462px}
.arq.pq svg{max-height:240px}
.htxt2[text-anchor="start"],.htxt3[text-anchor="start"]{text-anchor:start}
.arq .f{transform:none}
"""

JS = r"""
(function(){
'use strict';
const $=(s,r)=> (r||document).querySelector(s), $$=(s,r)=>[...(r||document).querySelectorAll(s)];
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
async function copyText(t){try{await navigator.clipboard.writeText(t);return true}catch(e){try{const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();document.execCommand('copy');a.remove();return true}catch(e2){return false}}}
__DATOS__

const slides=$$('.slide'); const N=slides.length;
const state=slides.map(()=>({r:0,frags:[]}));
let cur=0;
function partName(p){return p==='A'?'Por qué':p==='B'?'Mi ordenador':p==='C'?'Contenedores':'Producción'}
slides.forEach((s,i)=>{
  s.dataset.i=i; state[i].frags=$$('.f',s);
  const f=document.createElement('div'); f.className='foot';
  f.innerHTML=`<span>ML e IA · S2 · Del ordenador al servicio</span><span><b>${esc(partName(s.dataset.part))}</b> · ${i+1} / ${N}</span>`;
  s.appendChild(f);
});
const cum=[];(()=>{let t=0;slides.forEach(s=>{cum.push(t);t+=+s.dataset.min||0})})();
const TOTAL=cum[N-1]+(+slides[N-1].dataset.min||0);
function applyFrags(i){const st=state[i]; st.frags.forEach((el,k)=>el.classList.toggle('on',k<st.r))}
slides.forEach(s=>$$('.st',s).forEach((e,k)=>{if(!e.style.getPropertyValue('--d')) e.style.setProperty('--d',k)}));
const hooks={};
function go(i,full){
  i=Math.max(0,Math.min(N-1,i)); cur=i;
  slides.forEach((s,k)=>{s.classList.toggle('active',k===i);s.classList.toggle('past',k<i)});
  if(full!==undefined){state[i].r=full?state[i].frags.length:0}
  applyFrags(i); chrome();
  const e=slides[i].dataset.enter; if(e&&hooks[e]) hooks[e](slides[i]);
  try{history.replaceState(null,'','#'+(i+1))}catch(e){}
}
function next(){const st=state[cur]; if(st.r<st.frags.length){st.r++;applyFrags(cur);return} if(cur<N-1) go(cur+1,false)}
function prev(){const st=state[cur]; if(st.r>0){st.r--;applyFrags(cur);return} if(cur>0) go(cur-1,true)}
function chrome(){
  const s=slides[cur];
  $('#count').textContent=(cur+1)+' / '+N;
  $('#clockref').textContent='min '+cum[cur]+' de '+TOTAL;
  $('#prog').style.width=((cur+1)/N*100)+'%';
  $$('#bar .part').forEach(b=>b.classList.toggle('on',b.dataset.p===s.dataset.part));
  $('#notetext').innerHTML='<p>'+esc(s.dataset.notes||'')+'</p>';
  $('#notemin').textContent='Tiempo previsto: '+(s.dataset.min||0)+' min · acumulado '+cum[cur]+' min de '+TOTAL;
  $$('#idxgrid button').forEach((b,k)=>b.classList.toggle('cur',k===cur));
}
function fit(){const v=$('#viewport'); const sc=Math.min(v.clientWidth/1280,v.clientHeight/720); $('#stage').style.setProperty('--s',sc.toFixed(4))}
addEventListener('resize',fit);
$('#idxgrid').innerHTML=slides.map((s,i)=>`<button data-i="${i}"><small>${esc(partName(s.dataset.part))} · ${s.dataset.min||0} min</small>${i+1}. ${esc(s.dataset.title||'')}</button>`).join('');
$('#idxgrid').addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;toggle('#index',false);go(+b.dataset.i,false)});
function toggle(sel,force){$(sel).classList.toggle('on',force)}
$('#bprev').onclick=prev; $('#bnext').onclick=next;
$('#bidx').onclick=()=>toggle('#index'); $('#bnotes').onclick=()=>toggle('#notes');
$('#bfull').onclick=()=>{ if(document.fullscreenElement) document.exitFullscreen(); else document.documentElement.requestFullscreen&&document.documentElement.requestFullscreen() };
$$('#bar .part').forEach(b=>b.onclick=()=>{const k=slides.findIndex(s=>s.dataset.part===b.dataset.p);go(k,false)});
addEventListener('keydown',e=>{
  const t=e.target; if(t&&/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)) return;
  if(e.ctrlKey||e.metaKey||e.altKey) return;
  const k=e.key;
  if(k==='ArrowRight'||k==='PageDown'||(k===' '&&!/^(BUTTON|A)$/.test(t.tagName))){e.preventDefault();next()}
  else if(k==='ArrowLeft'||k==='PageUp'){e.preventDefault();prev()}
  else if(k==='Home'){e.preventDefault();go(0,false)}
  else if(k==='End'){e.preventDefault();go(N-1,true)}
  else if(k==='o'||k==='O'){toggle('#index')}
  else if(k==='s'||k==='S'){toggle('#notes')}
  else if(k==='f'||k==='F'){$('#bfull').click()}
  else if(k==='Escape'){toggle('#index',false);toggle('#notes',false)}
});
let tx=null;
addEventListener('touchstart',e=>{tx=e.touches[0].clientX},{passive:true});
addEventListener('touchend',e=>{if(tx===null)return;const dx=e.changedTouches[0].clientX-tx;tx=null;if(Math.abs(dx)>60){dx<0?next():prev()}},{passive:true});

/* Copiar órdenes */
document.addEventListener('click',async e=>{const b=e.target.closest('.cp'); if(!b) return; e.stopPropagation();
  const ok=await copyText(b.dataset.t); const t=b.textContent; b.classList.add('ok'); b.textContent=ok?'✓':'✗'; setTimeout(()=>{b.classList.remove('ok');b.textContent=t},1200)});

/* Dockerfile de la interfaz */
hooks.dock=()=>{ const box=$('#dklines'); if(box._ok) return; box._ok=1;
  box.innerHTML=DK.map((x,i)=>`<button class="dkl" data-i="${i}"><span class="mono">${esc(x.l)}</span></button>`).join('');
  function show(i){ const x=DK[i]; $$('.dkl',box).forEach((b,k)=>b.classList.toggle('sel',k===i));
    $('#dkdet').innerHTML=`<h2>${i+1}. ${esc(x.t)}</h2><p style="margin-top:6px;font-size:19px">${esc(x.d)}</p><div class="callout" style="margin-top:14px;font-size:18px">${esc(x.r)}</div>`; }
  box.addEventListener('click',e=>{const b=e.target.closest('.dkl'); if(b) show(+b.dataset.i)});
  show(2); };

/* Romper a propósito */
hooks.romper=()=>{ const box=$('#rbtns'); if(box._ok) return; box._ok=1;
  box.innerHTML=RO.map((x,i)=>`<button class="rbtn" data-i="${i}"><b>${esc(x.t)}</b><small>esperado: ${esc(x.e)}</small></button>`).join('');
  function show(i){ const x=RO[i]; $$('.rbtn',box).forEach((b,k)=>b.classList.toggle('sel',k===i));
    $('#rdet').innerHTML=`<h2>${esc(x.t)}</h2><pre class="pre" style="margin-top:8px">${esc(x.c)}</pre>`+
      `<div class="realbox reveal"><div class="rk">${esc(FUENTE)}</div><pre>${esc(x.s)}</pre></div>`+
      `<div class="callout" style="margin-top:12px;font-size:18px">${esc(x.l)}</div>`; }
  box.addEventListener('click',e=>{const b=e.target.closest('.rbtn'); if(b) show(+b.dataset.i)});
  show(4); };

fit();
const h=parseInt((location.hash||'').slice(1),10);
go(isNaN(h)?0:h-1,false);
addEventListener('hashchange',()=>{const n=parseInt((location.hash||'').slice(1),10);if(!isNaN(n)&&n-1!==cur)go(n-1,false)});
})();
"""


def css_base():
    texto = (S2 / 'slides' / 'index.html').read_text(encoding='utf-8')
    m = re.search(r'<style>(.*?)</style>', texto, re.S)
    if not m:
        raise SystemExit('no encuentro el <style> de slides/index.html')
    return m.group(1)


def html_completo():
    construir()
    js = JS.replace('__DATOS__', js_datos())
    return ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>Del ordenador al servicio · S2 · ML e IA: de desarrollo a producción</title>\n'
            f'<!-- Generado por generar.py: no se edita a mano. -->\n<style>{css_base()}{CSS_EXTRA}</style>\n</head>\n<body>\n'
            '<div id="prog"></div>\n<div id="viewport"><div id="stage">\n\n' + '\n\n'.join(SLIDES) + '\n\n</div></div>\n\n'
            '<aside id="notes" aria-label="Notas del ponente"><h3>Notas del ponente</h3><div id="notetext"></div><p class="small" id="notemin"></p></aside>\n'
            '<div id="index" aria-label="Índice"><h2>Índice</h2><div class="grid" id="idxgrid"></div></div>\n'
            '<nav id="bar" aria-label="Controles">\n'
            '  <button id="bprev" aria-label="Anterior">←</button><button id="bnext" aria-label="Siguiente">→</button>\n'
            '  <span id="count">1 / 1</span><span id="clockref" title="Minuto planificado acumulado"></span>\n'
            '  <button class="part" data-p="A">Por qué</button><button class="part" data-p="B">Mi ordenador</button><button class="part" data-p="C">Contenedores</button><button class="part" data-p="D">Producción</button>\n'
            '  <span class="sp"></span>\n'
            '  <a id="bhome" href="../index.html" title="Volver al índice de la sesión S2">⌂ <span class="tx">Índice de </span>S2</a><button id="bidx">Índice (O)</button><button id="bnotes">Notas (S)</button><button id="bfull">Pantalla completa (F)</button>\n'
            '</nav>\n'
            '<noscript>Esta presentación necesita JavaScript. El mismo contenido está en 04-Proyecto-Base/docs/del-ordenador-al-servicio.md.</noscript>\n\n'
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
        SALIDA.write_text(nuevo, encoding='utf-8')
        minutos = sum(int(m) for m in re.findall(r'data-min="(\d+)"', nuevo))
        print(f'escrito {SALIDA.name}: {len(SLIDES)} diapositivas, {minutos} min')


if __name__ == '__main__':
    main()
