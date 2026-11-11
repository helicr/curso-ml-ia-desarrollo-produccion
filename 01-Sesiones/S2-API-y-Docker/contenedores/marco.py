"""Marco común de las presentaciones de contenedores: aspecto, comportamiento y ensamblado del HTML.

Reutiliza el CSS y el JavaScript de la guía de Codespaces (`03-Entorno/guia-codespaces/generar.py`) para que todas
las guías del curso se vean y se manejen igual, y añade lo que aquí hace falta (capas, flujos, comparaciones).
"""
import html
import importlib.util
import re
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]

_ruta = RAIZ / '03-Entorno' / 'guia-codespaces' / 'generar.py'
_spec = importlib.util.spec_from_file_location('guia_codespaces_generar', _ruta)
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

CSS_EXTRA = r"""
.stack{display:flex;flex-direction:column;gap:5px}
.stack .l{display:flex;justify-content:space-between;align-items:baseline;gap:14px;padding:8px 14px;border-radius:10px;border:1px solid var(--line);background:var(--panel);font-size:15px}
.stack .l code{background:none;padding:0;color:#fff}
.stack .l small{color:var(--muted);font-size:12.5px;white-space:nowrap}
.stack .l.mio{border-color:var(--gold);background:#3a3110;color:#fff4cf}
.stack .l.rw{border-color:var(--ok);background:#08352b;border-style:dashed}
.stack .l.base{background:#0b2644}
.flow{display:flex;align-items:stretch;gap:8px}
.flow .b{flex:1;padding:10px 12px;border-radius:12px;border:1px solid var(--line);background:var(--panel);text-align:center;font-size:15px;line-height:1.3}
.flow .b b{display:block;color:var(--gold);font-size:14px;letter-spacing:.04em;margin-bottom:3px}
.flow .b.ok{border-color:rgba(52,211,153,.6)} .flow .b.bad{border-color:rgba(251,113,133,.6)} .flow .b.warn{border-color:rgba(251,191,36,.6)}
.flow .a{align-self:center;color:var(--gold);font-weight:800;font-size:22px}
.num{font-size:34px;font-weight:800;color:var(--gold);line-height:1}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.pair .card{padding:10px 14px}
.k{font-size:13px;color:var(--muted)}
.lead{font-size:17px;line-height:1.4;color:var(--muted)}
pre.real.g{font-size:12px;line-height:1.28;padding:6px 9px;margin-top:6px}
.mt{margin-top:10px}
.row{display:flex;gap:12px;align-items:stretch}
.row>*{flex:1;min-width:0}
.mini{padding:7px 11px}
.mini .k{font-family:var(--mono);font-size:11.5px;color:var(--gold);margin-bottom:2px;overflow-wrap:anywhere;line-height:1.25}
.mini pre.real{margin-top:3px}
.wide .cmd{padding:2px 10px}
.wide .cmd .cp{width:24px;height:24px;font-size:13px}
.wide .cmd code.l{font-size:14px;padding:1px 0}
.piensa{font-size:14.5px;line-height:1.35;margin-top:8px}
.wide+.btns .btn{padding:4px 12px}
.zoom{transform-origin:0 0;transform:scale(var(--z,1));width:calc(100% / var(--z,1))}
.pdfonly{display:none}
"""


def esc(t):
    return html.escape(t, quote=True)


def fmt(t):
    """Texto corto con `código` y **negrita** a HTML."""
    t = esc(t)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', t)
    return t


def card(titulo, cuerpo, clase='', estilo=''):
    h = f'<h3>{titulo}</h3>' if titulo else ''
    return f'<div class="card {clase}" style="{estilo}">{h}{cuerpo}</div>'


def ul(items, pequena=False):
    return f'<ul class="p{" s" if pequena else ""}">' + ''.join(f'<li>{i}</li>' for i in items) + '</ul>'


def tabla(cabeceras, filas, densa=True):
    th = ''.join(f'<th>{c}</th>' for c in cabeceras)
    tr = ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in f) + '</tr>' for f in filas)
    return f'<table class="{"dens" if densa else ""}"><tr>{th}</tr>{tr}</table>'


def real(texto, pequena=True):
    return f'<pre class="real{" g" if pequena else ""}">{esc(texto)}</pre>'


def capas(filas):
    """filas: (clase, html_izquierda, nota)"""
    return '<div class="stack">' + ''.join(f'<div class="l {c}"><span>{t}</span><small>{n}</small></div>' for c, t, n in filas) + '</div>'


def flujo(cajas):
    """cajas: (titulo, texto, clase)"""
    partes = []
    for i, (t, x, c) in enumerate(cajas):
        if i:
            partes.append('<div class="a">→</div>')
        partes.append(f'<div class="b {c}"><b>{t}</b>{x}</div>')
    return '<div class="flow">' + ''.join(partes) + '</div>'


def terminal(titulo_barra, cmds):
    return base.terminal(titulo_barra, [dict(c=c) if isinstance(c, str) else c for c in cmds])


def boton_copiar_todo(cmds):
    return f'<button class="btn primary cpall" data-t="{esc(chr(10).join(cmds))}">Copiar todo (C)</button>'


def check(items, prefijo):
    filas = ''.join(f'<label><input type="checkbox" data-k="{prefijo}{i}"><span>{t}</span><span class="ref">{r}</span></label>' for i, (t, r) in enumerate(items))
    return f'<div class="check">{filas}</div>'


AJUSTE_JS = r"""
(function(){
'use strict';
// Agranda el contenido de cada diapositiva (hasta data-max) mientras quepa encima del pie. Se repite al cargar las fuentes.
function ajustar(){
  document.querySelectorAll('.zoom').forEach(function(z){
    var tope=parseFloat(z.getAttribute('data-max')||'1.4'), lim=720-52-8, arriba=z.offsetTop, mejor=1;
    for(var v=tope; v>1.001; v-=0.05){
      z.style.setProperty('--z', v.toFixed(2));
      if(arriba + z.offsetHeight*v <= lim){ mejor=v; break; }
    }
    z.style.setProperty('--z', mejor.toFixed(2));
  });
}
ajustar(); addEventListener('load',ajustar);
if(document.fonts&&document.fonts.ready){document.fonts.ready.then(ajustar);}
})();
"""


class Presentacion:
    def __init__(self, titulo, store, carpeta_salida, noscript, home_href='../../index.html', home_sesion='S2'):
        """`home_href` y `home_sesion`: a dónde vuelve el botón «⌂ Índice» (por defecto, el índice de la sesión S2)."""
        self.titulo, self.store, self.salida, self.noscript = titulo, store, carpeta_salida, noscript
        self.home_href, self.home_sesion = home_href, home_sesion
        self.dias = []

    def agregar(self, titulo, bloque, cuerpo, id_=None, pie=None, cabecera='', zoom=None):
        """cabecera = lo que no se agranda (kicker y título); cuerpo = lo que se agranda hasta `zoom` si hay hueco."""
        if zoom:
            cuerpo = f'<div class="zoom" data-max="{zoom}">{cuerpo}</div>'
        self.dias.append(dict(titulo=titulo, bloque=bloque, html=cabecera + cuerpo, id=id_, pie=pie or bloque))

    def libre(self, titulo, bloque, kick, h1, cuerpo, id_=None, pie=None, zoom=1.4):
        self.agregar(titulo, bloque, cuerpo, id_, pie, cabecera=f'<div class="kick">{esc(kick)}</div><h1>{fmt(h1)}</h1>', zoom=zoom)

    def html(self):
        css = base.CSS + CSS_EXTRA
        js = base.JS.replace("'codespaces-guia-hecho'", f"'{self.store}'")
        assert self.store in js
        secs = []
        for d in self.dias:
            attrs = f' data-title="{esc(d["titulo"])}" data-bloque="{esc(d["bloque"])}"' + (f' data-id="{d["id"]}"' if d['id'] else '')
            secs.append(f'<section class="slide"{attrs}>{d["html"]}<div class="foot"><span>{esc(self.titulo)}</span><span>{esc(d["pie"])}</span></div></section>')
        return (f'<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
                f'<title>{esc(self.titulo)} · ML e IA: de desarrollo a producción</title>\n<style>{css}</style>\n</head>\n<body>\n'
                f'<div id="viewport"><div id="stage">\n{chr(10).join(secs)}\n</div></div>\n<div id="prog"></div>\n'
                '<div id="index" aria-label="Índice"><h2>Índice</h2><div id="idxgrid"></div></div>\n'
                '<nav id="bar" aria-label="Controles"><button id="bprev" aria-label="Anterior">←</button><button id="bnext" aria-label="Siguiente">→</button>'
                f'<span id="count">1</span><span class="sp"></span><a id="bhome" href="{esc(self.home_href)}" title="Volver al índice de la sesión {esc(self.home_sesion)}">⌂ <span class="tx">Índice de </span>{esc(self.home_sesion)}</a>'
                '<button id="bidx">Índice (O)</button><button id="bfull">Pantalla completa (F)</button></nav>\n'
                f'<noscript>Esta presentación necesita JavaScript. {esc(self.noscript)}</noscript>\n'
                f'<script>{js}</script>\n<script>{AJUSTE_JS}</script>\n</body>\n</html>\n')
