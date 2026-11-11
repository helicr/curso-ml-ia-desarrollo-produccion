"""Genera el `index.html` de cada sesión (`01-Sesiones/Sx-.../index.html`) desde `contenido_indices.py`.

Uso:  python 00-Planificacion/indices-de-sesion/generar_indices.py
Los `index.html` de las sesiones se sobrescriben: no los edites a mano.
"""
import html
import json
import os
import re
import sys
from pathlib import Path, PurePosixPath

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(AQUI))
import contenido_indices as C  # noqa: E402
sys.path.insert(0, str(RAIZ / '00-Planificacion' / 'pdfs'))
import contenido_pdfs as P  # noqa: E402

IGNORAR = {'__pycache__', 'node_modules', '.git'}


def esc(t):
    return html.escape(t, quote=True)


def relativa(ruta, carpeta):
    """Ruta (desde la raíz del repositorio) vista desde la carpeta de la sesión, con barras /."""
    # os.path.relpath usa «\» en Windows: se pasa a «/» para que los enlaces sean iguales en cualquier sistema.
    return os.path.relpath(RAIZ / ruta, RAIZ / carpeta).replace(os.sep, '/')


def contar_diapositivas(ruta):
    """Número de diapositivas de una presentación (secciones con class="slide"); 0 si la página no es una presentación."""
    texto = (RAIZ / ruta).read_text(encoding='utf-8', errors='replace')
    return len(re.findall(r'<section\b[^>]*\bclass="slide', texto))


def titulo_de_archivo(ruta):
    """Título que tiene el propio archivo: <title> en HTML, primer encabezado en Markdown, y si no, su nombre."""
    texto = (RAIZ / ruta).read_text(encoding='utf-8', errors='replace')
    if ruta.endswith('.html'):
        m = re.search(r'<title>(.*?)</title>', texto, re.S)
        if m and m.group(1).strip():
            return html.unescape(m.group(1).strip())
    else:
        for linea in texto.splitlines():
            if linea.startswith('# '):
                return linea[2:].strip()
    return PurePosixPath(ruta).name


def descubrir(s):
    """.html y .md de la carpeta de la sesión que no están en contenido_indices.py: aparecen solos, con el título del archivo."""
    conocidos = {e['ruta'] for e in s['enlaces']}
    base = RAIZ / s['carpeta']
    nuevos = []
    for p in sorted(base.rglob('*')):
        rel = p.relative_to(RAIZ).as_posix()
        partes = set(p.relative_to(base).parts)
        if p.suffix not in ('.html', '.md') or partes & IGNORAR or any(x.startswith('.') for x in partes):
            continue
        if p == base / 'index.html' or rel in conocidos:
            continue
        if p.suffix == '.html':
            nuevos.append(dict(tipo='deck', grupo=C.PRESENTACIONES, titulo=titulo_de_archivo(rel), ruta=rel, desc='', volver=False, auto=True))
        else:
            grupo = C.INSTRUCTOR if p.name in ('README.md', 'guion.md') else C.ALUMNO
            nuevos.append(dict(tipo='doc', grupo=grupo, titulo=titulo_de_archivo(rel), ruta=rel, desc='', auto=True))
    return nuevos


def enlaces_de(s):
    for e in s['enlaces']:
        if not (RAIZ / e['ruta']).is_file():
            raise SystemExit(f'{s["id"]}: el archivo enlazado en contenido_indices.py no existe: {e["ruta"]}')
    return s['enlaces'] + descubrir(s)


def componentes(s):
    """[(etiqueta, hay)] de los componentes que se esperan en la sesión."""
    base = RAIZ / s['carpeta']
    salida = []
    for clave in s['esperados']:
        etiqueta, patrones = C.COMPONENTES[clave]
        salida.append((etiqueta, any(any(base.glob(p)) for p in patrones)))
    return salida


def ruta_pdf_de(ruta):
    """Ruta (desde la raíz del repositorio) del PDF generado para un archivo fuente, o None si no hay o aún no se generó."""
    for s in P.SESIONES:
        for e in s['elementos']:
            if e['origen'] == ruta:
                pdf = f"{P.CARPETA_SALIDA}/{s['carpeta']}/{P.GRUPOS[e['grupo']][1]}/{e['archivo']}"
                return pdf if (RAIZ / pdf).is_file() else None
    return None


def carpeta_pdf_de(sesion_id):
    """Carpeta de PDF de una sesión (desde la raíz del repositorio), o None si la sesión no tiene PDF."""
    for s in P.SESIONES:
        if s['id'] == sesion_id and (RAIZ / P.CARPETA_SALIDA / s['carpeta']).is_dir():
            return f"{P.CARPETA_SALIDA}/{s['carpeta']}"
    return None


def enlace_pdf(e, carpeta):
    pdf = ruta_pdf_de(e['ruta'])
    if not pdf:
        return ''
    return f'<a class="pdf" href="{esc(relativa(pdf, carpeta))}" title="Versión en PDF: {esc(pdf)}">PDF</a>'


def item(e, carpeta):
    local = relativa(e['ruta'], carpeta)
    sin = ' <span class="auto">(sin descripción: añádela en contenido_indices.py)</span>' if e.get('auto') else ''
    desc = f'<span class="d">{esc(e["desc"])}{sin}</span>' if (e['desc'] or sin) else ''
    if e['tipo'] == 'deck':
        n = contar_diapositivas(e['ruta'])
        badge = f'<span class="n">{n} diap.</span>' if n else ''
        return (f'<li><a class="deck" href="{esc(local)}"><span class="t">{esc(e["titulo"])}</span>{badge}{desc}'
                f'<span class="r">{esc(e["ruta"])}</span></a>{enlace_pdf(e, carpeta)}</li>')
    return (f'<li><a class="doc" href="{esc(local)}" data-local="{esc(local)}" data-path="{esc(e["ruta"])}" title="{esc(e["ruta"])}">{esc(e["titulo"])}</a>'
            f'{enlace_pdf(e, carpeta)}{desc}</li>')


def seccion(clave, titulo, enlaces, carpeta, vacio=''):
    sel = [e for e in enlaces if e['grupo'] == clave]
    if not sel:
        return f'<div class="col"><h2>{esc(titulo)}</h2><p class="vacio">{esc(vacio)}</p></div>' if vacio else ''
    return f'<div class="col"><h2>{esc(titulo)}</h2><ul>{"".join(item(e, carpeta) for e in sel)}</ul></div>'


def linea_pdf(sesion_id):
    carpeta = carpeta_pdf_de(sesion_id)
    if not carpeta:
        return ''
    sesion = next(s for s in C.SESIONES if s['id'] == sesion_id)
    origen = sesion['carpeta']
    return (f'<p class="modo">PDF de esta sesión (los exige la institución): '
            f'<a href="{esc(relativa(carpeta, origen))}/">carpeta {esc(carpeta)}</a> · '
            f'<a href="{esc(relativa(P.CARPETA_SALIDA + "/LEEME.md", origen))}">qué contiene y qué se pierde</a></p>')


def vecinas(i):
    def enlace(j, flecha_izq):
        o = C.SESIONES[j]
        rel = relativa(o['carpeta'] + '/index.html', C.SESIONES[i]['carpeta'])
        txt = f'← {o["id"]}' if flecha_izq else f'{o["id"]} →'
        return f'<a href="{esc(rel)}" title="{esc(o["titulo"])}">{esc(txt)}</a>'
    partes = []
    if i > 0:
        partes.append(enlace(i - 1, True))
    if i < len(C.SESIONES) - 1:
        partes.append(enlace(i + 1, False))
    return f'<nav class="vecinas" aria-label="Otras sesiones">{"".join(partes)}</nav>'


CSS = r"""
:root{--bg:#031a33;--panel:#0a3560;--panel2:#0e4378;--line:#1a5fa3;--blue:#2bb3ff;--gold:#fcd34d;--text:#eef6ff;--muted:#a9c8ea;--ok:#34d399;--warn:#fbbf24;--r:16px;
--mono:ui-monospace,"Cascadia Code","SFMono-Regular",Consolas,Menlo,monospace;--sans:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
*{box-sizing:border-box;margin:0;padding:0}
[hidden]{display:none!important}
html{background:var(--bg)}
body{background:radial-gradient(1100px 600px at 15% -5%,#07305a 0%,transparent 62%) no-repeat;color:var(--text);font:16px/1.5 var(--sans);min-height:100vh}
a{color:var(--blue)}
code{font-family:var(--mono);background:rgba(43,179,255,.14);padding:1px 6px;border-radius:6px;font-size:.88em;color:#d9efff;overflow-wrap:anywhere}
:focus-visible{outline:3px solid var(--gold);outline-offset:2px}
.sr{position:absolute;left:-9999px}
.wrap{max-width:1100px;margin:0 auto;padding:0 24px}
header.top{padding-top:30px;padding-bottom:6px;position:relative}
.kick{color:var(--gold);letter-spacing:.14em;text-transform:uppercase;font-size:13px;font-weight:700}
h1{display:flex;gap:16px;align-items:baseline;font-size:clamp(24px,4vw,36px);line-height:1.2;margin:6px 0 6px}
h1 .num{font-family:var(--mono);color:var(--gold)}
.meta{color:var(--muted);font-size:14px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.chip{font-size:12px;font-weight:700;border-radius:999px;padding:2px 12px;border:1px solid;white-space:nowrap}
.chip.ok{color:var(--ok);border-color:var(--ok)}
.chip.warn{color:var(--warn);border-color:var(--warn)}
.res{margin-top:12px;color:#dcebfb;max-width:900px}
.nota{margin-top:6px;font-size:14px;color:var(--muted);max-width:900px}
.vecinas{position:absolute;right:24px;top:30px;display:flex;gap:8px}
.vecinas a{text-decoration:none;color:var(--text);border:1px solid var(--line);border-radius:999px;padding:3px 12px;font-size:14px;font-weight:600}
.vecinas a:hover{border-color:var(--gold)}
.modo{display:flex;gap:16px;align-items:center;flex-wrap:wrap;font-size:14px;color:var(--muted);margin-top:14px}
.modo label{color:var(--text);cursor:pointer}
.modo fieldset{border:0;display:flex;gap:14px;align-items:center;flex-wrap:wrap}
main.wrap{padding-bottom:10px}
.cols{display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:22px;margin-top:22px}
.col h2{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--gold);margin-bottom:10px}
ul{list-style:none}
.col li+li{margin-top:10px}
a.deck{display:block;padding:12px 14px;border-radius:12px;background:var(--panel2);border:1px solid var(--line);text-decoration:none;color:var(--text)}
a.deck:hover{border-color:var(--gold)}
a.deck .t{font-weight:700;margin-right:8px}
a.deck .n{font-size:12px;color:#031a33;background:var(--blue);border-radius:999px;padding:1px 9px;font-weight:700;white-space:nowrap}
a.deck .d{display:block;font-size:13px;color:var(--muted);margin-top:3px}
a.deck .r{display:block;font:11.5px var(--mono);color:#7fa6cf;margin-top:4px;overflow-wrap:anywhere}
a.doc{font-weight:600}
a.pdf{display:inline-block;margin:6px 0 0 2px;font-size:12px;font-weight:700;letter-spacing:.04em;text-decoration:none;color:var(--gold);border:1px solid rgba(252,211,77,.6);border-radius:999px;padding:1px 11px}
a.pdf:hover{background:rgba(252,211,77,.16)}
a.doc+a.pdf{margin:0 0 0 10px}
li .d{display:block;font-size:13px;color:var(--muted)}
.auto{color:var(--warn)}
.vacio{font-size:14px;color:var(--warn)}
.falta{margin-top:26px;background:rgba(10,53,96,.45);border:1px solid var(--line);border-radius:var(--r);padding:14px 18px}
.falta h2{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--gold);margin-bottom:8px}
.falta ul{display:flex;gap:8px;flex-wrap:wrap}
.falta li{font-size:14px;border-radius:999px;padding:3px 12px;border:1px solid}
.falta li.si{color:var(--ok);border-color:rgba(52,211,153,.55)}
.falta li.no{color:var(--warn);border-color:var(--warn);background:rgba(251,191,36,.08)}
.falta p{font-size:14px;color:var(--muted);margin-top:8px}
footer.pie{margin:30px auto 40px;padding-top:14px;border-top:1px solid var(--line);font-size:13px;color:var(--muted)}
footer.pie p+p{margin-top:6px}
@media(max-width:900px){.cols{grid-template-columns:1fr}}
@media(max-width:560px){.wrap{padding:0 14px}.vecinas{position:static;margin-top:10px}}
@media print{body{background:#fff;color:#000}.modo,.vecinas{display:none}a.deck,.falta{border-color:#999;background:#fff;color:#000}
a,a.deck .t,a.pdf{color:#000}.chip,.num{color:#000;border-color:#000}a.deck .d,.meta,.nota,li .d{color:#333}}
"""

JS = r"""
(function(){'use strict';
var BASE=@@BASE@@,KEY='indice-curso-docs';
function $$(s){return Array.prototype.slice.call(document.querySelectorAll(s))}
function leer(){try{return localStorage.getItem(KEY)==='local'?'local':'github'}catch(e){return 'github'}}
function guardar(v){try{localStorage.setItem(KEY,v)}catch(e){}}
function aplicar(m){
  $$('a[data-path]').forEach(function(a){
    if(m==='github'){a.href=BASE+a.getAttribute('data-path');a.target='_blank';a.rel='noopener'}
    else{a.href=a.getAttribute('data-local');a.removeAttribute('target');a.removeAttribute('rel')}
  });
  $$('input[name=modo]').forEach(function(r){r.checked=(r.value===m)});
}
aplicar(leer());
$$('input[name=modo]').forEach(function(r){r.addEventListener('change',function(){if(r.checked){guardar(r.value);aplicar(r.value)}})});
})();
"""


def construir(i):
    s = C.SESIONES[i]
    carpeta = s['carpeta']
    etiqueta, clase = C.ESTADOS[s['estado']]
    enlaces = enlaces_de(s)
    comp = componentes(s)
    faltan = [e for e, hay in comp if not hay]
    chips = ''.join(f'<li class="{"si" if hay else "no"}"><span aria-hidden="true">{"✔" if hay else "✗"}</span> {esc(e)}'
                    f'<span class="sr"> ({"hay" if hay else "falta"})</span></li>' for e, hay in comp)
    resumen_falta = (f'<p>Falta: {esc(", ".join(f.lower() for f in faltan))}.</p>' if faltan
                     else '<p>No falta ningún componente de los esperados.</p>')
    nota = f'<p class="nota">{esc(s["nota"])}</p>' if s.get('nota') else ''
    base = f'{C.REPO_GITHUB}/blob/{C.RAMA}/'
    cols = (seccion(C.PRESENTACIONES, 'Presentaciones', enlaces, carpeta, 'Todavía no hay presentaciones.')
            + seccion(C.ALUMNO, 'Para el alumno', enlaces, carpeta, 'Todavía no hay material para el alumno.')
            + seccion(C.INSTRUCTOR, 'Para el instructor', enlaces, carpeta))
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(s['id'])} · {esc(s['titulo'])} · Índice de la sesión · {esc(C.CURSO)}</title>
<style>{CSS}</style>
</head>
<body>
<header class="top wrap">
  <p class="kick">Índice de la sesión · {esc(C.CURSO)}</p>
  <h1><span class="num">{esc(s['id'])}</span><span>{esc(s['titulo'])}</span></h1>
  <p class="meta">{esc(s['horas'])} · <code>{esc(carpeta)}</code> · <span class="chip {clase}">{esc(etiqueta)}</span></p>
  <p class="res">{esc(s['resumen'])}</p>{nota}
  <div class="modo"><fieldset><legend class="sr">Dónde abrir los documentos</legend>
    <span>Los documentos (.md, .py, .yml) se abren en:</span>
    <label><input type="radio" name="modo" value="github"> GitHub (con conexión)</label>
    <label><input type="radio" name="modo" value="local"> Esta carpeta (el navegador los muestra como texto o los descarga)</label></fieldset></div>
  {linea_pdf(s['id'])}
  {vecinas(i)}
</header>
<main class="wrap">
  <div class="cols">{cols}</div>
  <section class="falta"><h2>Qué hay y qué falta en esta sesión</h2><ul>{chips}</ul>{resumen_falta}</section>
</main>
<footer class="wrap pie">
  <p>{esc(C.LEYENDA)}</p>
  <p>Página generada desde <code>00-Planificacion/indices-de-sesion/contenido_indices.py</code> con <code>generar_indices.py</code>; no se edita a mano.
  Si añades un archivo a esta carpeta, ejecuta el generador y aparecerá aquí. Rama de GitHub: <code>{esc(C.RAMA)}</code>.</p>
</footer>
<script>{JS.replace('@@BASE@@', json.dumps(base))}</script>
</body>
</html>
"""


def ruta_salida(i):
    return RAIZ / C.SESIONES[i]['carpeta'] / 'index.html'


def main():
    for i, s in enumerate(C.SESIONES):
        contenido = construir(i)
        ruta_salida(i).write_text(contenido, encoding='utf-8')
        print(f'{ruta_salida(i).relative_to(RAIZ)}: {len(contenido.encode("utf-8"))} bytes')


if __name__ == '__main__':
    main()
