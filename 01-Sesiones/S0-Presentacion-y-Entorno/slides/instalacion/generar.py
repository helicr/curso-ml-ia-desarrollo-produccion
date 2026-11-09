"""Genera, a partir de contenido.py y salidas-reales.json:
    - slides/instalacion/index.html                      (diapositivas «Tu equipo listo para S1», con botones de copiar)
    - practica/guia-rapida-entorno-s0-s1.md              (la misma informacion en texto, para leer o imprimir)

Uso (desde cualquier carpeta):   python generar.py
No edites a mano esos dos archivos: cambia contenido.py (textos y comandos) y vuelve a ejecutar. Para renovar las salidas reales: capturar.py.
"""
import html
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import contenido as C  # noqa: E402

SESION = AQUI.parents[1]                       # 01-Sesiones/S0-Presentacion-y-Entorno
RAIZ = AQUI.parents[3]
SALIDA_HTML = AQUI / 'index.html'
SALIDA_MD = SESION / 'practica' / 'guia-rapida-entorno-s0-s1.md'
TITULO = 'Tu equipo listo para S1'
TITULO_GUIA = 'Guía rápida del entorno (S0 → S1)'


def cargar_salidas():
    ruta = AQUI / 'salidas-reales.json'
    datos = json.loads(ruta.read_text(encoding='utf-8'))
    return datos['salidas'], datos['meta']


def esc(t):
    return html.escape(t, quote=True)


def nota_real(p, salidas):
    """real_nota con {clave} sustituido por los segundos medidos en la captura (p. ej. {crear_entorno})."""
    return p['real_nota'].format(**{k: f'{v["segundos"]:.0f}' for k, v in salidas.items()})


def cmds_planos(paso, extras=False):
    grupos = [paso['cmds']] + ([e['cmds'] for e in paso.get('extra', [])] if extras else [])
    return [c['c'] for g in grupos for c in g]


def md(t):
    """Convierte el HTML minimo de los textos (<code>, <b>, <br>) a Markdown."""
    t = re.sub(r'<code>(.*?)</code>', lambda m: '`' + m.group(1) + '`', t)
    t = re.sub(r'<b>(.*?)</b>', r'**\1**', t)
    t = t.replace('<br>', '  \n')
    return html.unescape(t)


def numero_de_paquetes():
    n = 0
    for linea in (RAIZ / '03-Entorno' / 'conda' / 'environment.yml').read_text(encoding='utf-8').splitlines():
        if re.match(r'^\s*-\s*[A-Za-z0-9_.\-]+=[^=]', linea.split('#')[0]) and not linea.strip().startswith('- python='):
            n += 1
    return n


# ================================================================== HTML
CSS = r"""
:root{--bg:#031a33;--bg2:#062a4d;--panel:#0a3560;--panel2:#0e4378;--line:#1a5fa3;--blue:#2bb3ff;--gold:#fcd34d;--text:#eef6ff;--muted:#a9c8ea;
--ok:#34d399;--warn:#fbbf24;--bad:#fb7185;--r:14px;
--mono:ui-monospace,"Cascadia Code","SFMono-Regular",Consolas,Menlo,monospace;--sans:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:var(--sans);overflow:hidden}
button{font:inherit;color:inherit;cursor:pointer;background:none;border:0}
a{color:var(--blue)}
code{font-family:var(--mono);background:rgba(43,179,255,.14);padding:1px 6px;border-radius:6px;font-size:.92em;color:#d9efff}
:focus-visible{outline:3px solid var(--gold);outline-offset:2px}
#viewport{position:fixed;inset:0 0 46px 0;overflow:hidden;background:radial-gradient(1200px 700px at 20% 0%,#07305a 0%,var(--bg) 70%)}
#stage{position:absolute;left:50%;top:50%;width:1280px;height:720px;transform:translate(-50%,-50%) scale(var(--s,1));transform-origin:center center}
.slide{position:absolute;inset:0;padding:40px 60px 52px;opacity:0;visibility:hidden;transform:translateX(24px);transition:opacity .35s ease,transform .35s ease,visibility 0s .35s;overflow:hidden}
.slide.active{opacity:1;visibility:visible;transform:none;transition:opacity .35s ease,transform .35s ease}
.slide::before{content:"";position:absolute;inset:0 0 auto 0;height:4px;background:linear-gradient(90deg,var(--blue),var(--gold))}
.foot{position:absolute;left:60px;right:60px;bottom:14px;display:flex;justify-content:space-between;font-size:12px;letter-spacing:.08em;color:var(--muted);text-transform:uppercase}
.kick{font-size:14px;letter-spacing:.18em;text-transform:uppercase;color:var(--gold);font-weight:700;margin-bottom:6px;display:flex;gap:14px;align-items:center}
h1{font-size:34px;line-height:1.1;letter-spacing:-.01em;margin-bottom:8px;font-weight:800}
h2{font-size:22px;margin-bottom:8px}
h3{font-size:16px;margin-bottom:6px;color:var(--gold);letter-spacing:.04em;text-transform:uppercase}
p{font-size:18px;line-height:1.45}
.muted{color:var(--muted)} .small{font-size:14px;line-height:1.4;color:var(--muted)}
.card{background:linear-gradient(180deg,var(--panel),#082d54);border:1px solid var(--line);border-radius:var(--r);padding:14px 18px}
.card.ok{border-color:rgba(52,211,153,.55)} .card.bad{border-color:rgba(251,113,133,.5)}
.tag{display:inline-block;font-size:12px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;padding:3px 10px;border-radius:999px;border:1px solid var(--line);color:var(--muted)}
.tag.linux{color:#032b1c;background:var(--ok);border-color:var(--ok)} .tag.mixto{color:#2b2100;background:var(--gold);border-color:var(--gold)} .tag.sin{color:var(--warn);border-color:var(--warn)}
.chip{display:inline-block;font-size:14px;font-weight:700;padding:3px 12px;border-radius:999px;background:var(--blue);color:#04213f}
.where{display:flex;gap:10px;align-items:center;margin-bottom:10px;font-size:15px;color:var(--muted)}
.cols{display:grid;grid-template-columns:1.2fr .8fr;gap:20px;align-items:start}
.term{background:#02101f;border:1px solid var(--line);border-radius:12px;overflow:hidden;margin:10px 0 8px}
.term .bar{display:flex;gap:6px;align-items:center;padding:6px 12px;background:#0a2a4a;font-size:12px;color:var(--muted);letter-spacing:.06em;text-transform:uppercase}
.term .bar i{width:10px;height:10px;border-radius:50%;background:#2a5d92;display:inline-block}
.term .bar em{margin-left:8px;font-style:normal}
.cmd{display:flex;gap:10px;align-items:flex-start;padding:4px 10px;border-top:1px solid rgba(26,95,163,.35)}
.cmd:first-of-type{border-top:0}
.cmd .cp{flex:none;width:28px;height:28px;border-radius:8px;border:1px solid var(--line);background:var(--panel);font-size:15px;line-height:1;display:grid;place-items:center}
.cmd .cp:hover{background:var(--blue);color:#04213f}.cmd .cp.hecho{background:var(--ok);color:#032b1c;border-color:var(--ok)}
.cmd .tx{flex:1;min-width:0}
.cmd code.l{display:block;background:none;padding:2px 0;font-size:15px;color:#fff;white-space:pre-wrap;overflow-wrap:anywhere;user-select:all}
.cmd code.l::before{content:"> ";color:var(--gold)}
.cmd .nota{display:block;font-size:12.5px;color:var(--muted)}
.sub{padding:5px 12px;font-size:12.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--gold);background:rgba(252,211,77,.07);border-top:1px solid rgba(26,95,163,.35)}
.btns{display:flex;gap:10px;margin-top:6px;align-items:center}
.btn{padding:7px 14px;border-radius:10px;border:1px solid var(--line);background:var(--panel);font-weight:700;font-size:14px}
.btn:hover{background:var(--panel2)} .btn.primary{background:var(--blue);color:#04213f;border-color:var(--blue)}
.btn.on{background:var(--ok);color:#032b1c;border-color:var(--ok)}
ol.ui{list-style:none;counter-reset:u;display:flex;flex-direction:column;gap:5px;margin:6px 0}
ol.ui li{counter-increment:u;display:flex;gap:10px;font-size:15px;line-height:1.32}
ol.ui li span{flex:1;min-width:0}
ol.ui li::before{content:counter(u);flex:none;width:24px;height:24px;border-radius:50%;background:var(--blue);color:#04213f;font-weight:800;font-size:14px;display:grid;place-items:center;margin-top:1px}
pre.real.larga{font-size:12px;line-height:1.25}
pre.real{font-family:var(--mono);font-size:12.5px;line-height:1.32;background:#02101f;border:1px solid var(--line);border-radius:10px;padding:8px 10px;margin-top:8px;white-space:pre-wrap;word-break:break-word;color:#cfe8ff}
.rn{font-size:12px;color:var(--muted);margin-top:4px}
.side{display:flex;flex-direction:column;gap:10px}
.full .term{margin-top:6px}
ul.f{list-style:none;display:flex;flex-direction:column;gap:6px}
ul.f li{font-size:14.5px;line-height:1.38;padding-left:16px;position:relative}
ul.f li::before{content:"›";position:absolute;left:2px;color:var(--bad);font-weight:800}
.vn{font-size:12.5px;color:var(--muted);margin-top:6px}
table{width:100%;border-collapse:collapse;font-size:15px}
th{font-size:12.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--gold);text-align:left;padding:6px 10px;border-bottom:2px solid var(--line)}
td{padding:7px 10px;border-bottom:1px solid rgba(26,95,163,.45);vertical-align:top;line-height:1.35}
.map{display:grid;grid-template-columns:repeat(6,1fr);gap:14px;margin:14px 0 16px}
.blk{position:relative;background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:12px 12px 14px;min-height:150px}
.blk .L{width:38px;height:38px;border-radius:50%;background:var(--gold);color:#2b2100;font-weight:800;font-size:20px;display:grid;place-items:center;margin-bottom:8px}
.blk b{display:block;font-size:17px;margin-bottom:3px}.blk span{display:block;font-size:13.5px;color:var(--muted);line-height:1.3}
.blk em{display:block;font-style:normal;margin-top:8px;font-size:12px;color:var(--blue);font-weight:700}
.blk:not(:last-child)::after{content:"→";position:absolute;right:-16px;top:38px;font-size:22px;color:var(--blue);z-index:2}
.blk.f{border-style:dashed}
.two{display:grid;grid-template-columns:1fr 1fr;gap:18px}
ul.p{list-style:none;display:flex;flex-direction:column;gap:7px}
ul.p li{font-size:16.5px;line-height:1.4;padding-left:18px;position:relative}
ul.p li::before{content:"";position:absolute;left:0;top:9px;width:8px;height:8px;border-radius:3px;background:var(--blue)}
.cover{display:flex;flex-direction:column;justify-content:center;height:100%;padding-bottom:20px}
.cover h1{font-size:62px;line-height:1.04;margin:6px 0 14px}.cover .sub2{font-size:24px;color:var(--muted);margin-bottom:22px;max-width:900px}
.chips{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:20px}
.check{display:flex;flex-direction:column;gap:8px}
.check label{display:flex;gap:12px;align-items:flex-start;font-size:17px;line-height:1.35;padding:8px 12px;background:var(--panel);border:1px solid var(--line);border-radius:12px;cursor:pointer}
.check input{width:20px;height:20px;margin-top:2px;accent-color:var(--ok)}
.check .ref{margin-left:auto;font-size:12.5px;color:var(--muted);white-space:nowrap;padding-left:10px}
#bar{position:fixed;left:0;right:0;bottom:0;height:46px;display:flex;gap:10px;align-items:center;padding:0 14px;background:#02101f;border-top:1px solid var(--line);font-size:14px}
#bar button{padding:6px 12px;border-radius:8px;border:1px solid var(--line);background:var(--panel)}
#bar .sp{flex:1}
#prog{position:fixed;left:0;bottom:46px;height:3px;background:var(--gold);width:0;transition:width .3s}
#index{position:fixed;inset:0 0 46px 0;background:rgba(2,16,31,.97);padding:26px 40px;overflow:auto;display:none;z-index:20}
#index.on{display:block}#index h2{font-size:26px;margin-bottom:14px}
#idxgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:10px}
#idxgrid button{text-align:left;padding:10px 14px;border-radius:10px;border:1px solid var(--line);background:var(--panel);font-size:15px}
#idxgrid button small{display:block;color:var(--gold);font-size:11.5px;letter-spacing:.1em;text-transform:uppercase}
#idxgrid button.cur{border-color:var(--gold)}#idxgrid button.hecho::after{content:" ✓";color:var(--ok);font-weight:800}
@media (prefers-reduced-motion:reduce){.slide,.slide.active{transition:none}}
@media print{html,body{overflow:visible;height:auto}#bar,#prog,#index{display:none}#viewport{position:static}#stage{position:static;transform:none;width:auto;height:auto}
.slide{position:relative;opacity:1;visibility:visible;transform:none;page-break-after:always;height:720px;width:1280px}}
"""

JS = r"""
(function(){
'use strict';
const $=(s,r)=>(r||document).querySelector(s), $$=(s,r)=>[...(r||document).querySelectorAll(s)];
function store(k,v){try{if(v===undefined){return JSON.parse(localStorage.getItem(k))}localStorage.setItem(k,JSON.stringify(v))}catch(e){return null}}
async function copyText(t){try{await navigator.clipboard.writeText(t);return true}catch(e){try{const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();const ok=document.execCommand('copy');a.remove();return ok}catch(e2){return false}}}
const slides=$$('.slide'), N=slides.length; let cur=0;
let hecho=store('s0-inst-hecho')||{};
function fit(){const v=$('#viewport');$('#stage').style.setProperty('--s',Math.min(v.clientWidth/1280,v.clientHeight/720).toFixed(4))}
addEventListener('resize',fit);
function go(i){cur=Math.max(0,Math.min(N-1,i));slides.forEach((s,k)=>s.classList.toggle('active',k===cur));
  $('#count').textContent=(cur+1)+' / '+N;$('#prog').style.width=((cur+1)/N*100)+'%';
  $$('#idxgrid button').forEach((b,k)=>b.classList.toggle('cur',k===cur)); location.hash='#'+(cur+1);}
function marcar(){$$('.slide[data-id]').forEach(s=>{const id=s.dataset.id,b=$('.hecho-btn',s);if(b){b.classList.toggle('on',!!hecho[id]);b.textContent=hecho[id]?'✓ Hecho':'Marcar como hecho'}});
  $$('#idxgrid button').forEach(b=>b.classList.toggle('hecho',!!hecho[b.dataset.id]));
  const ids=[...new Set($$('.slide[data-id]').map(s=>s.dataset.id))], total=ids.length, n=ids.filter(id=>hecho[id]).length;const c=$('#cuenta');if(c)c.textContent=n+' de '+total+' pasos marcados como hechos en este navegador'}
$('#idxgrid').innerHTML=slides.map((s,i)=>`<button data-i="${i}" data-id="${s.dataset.id||''}"><small>${s.dataset.bloque||''}</small>${i+1}. ${s.dataset.title}</button>`).join('');
$('#idxgrid').addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;$('#index').classList.remove('on');go(+b.dataset.i)});
document.addEventListener('click',async e=>{
  const cp=e.target.closest('.cp');
  if(cp){const ok=await copyText(cp.dataset.t);cp.classList.toggle('hecho',ok);cp.textContent=ok?'✓':'!';setTimeout(()=>{cp.classList.remove('hecho');cp.textContent='⧉'},1300);return}
  const all=e.target.closest('.cpall');
  if(all){const ok=await copyText(all.dataset.t);const t=all.textContent;all.textContent=ok?'Copiado ✓':'No se pudo copiar';setTimeout(()=>{all.textContent=t},1500);return}
  const hb=e.target.closest('.hecho-btn');
  if(hb){const id=hb.closest('[data-id]').dataset.id;hecho[id]=!hecho[id];store('s0-inst-hecho',hecho);marcar();return}
});
document.addEventListener('change',e=>{const c=e.target.closest('.check input');if(c){hecho['lista-'+c.dataset.k]=c.checked;store('s0-inst-hecho',hecho)}});
$('#bprev').onclick=()=>go(cur-1);$('#bnext').onclick=()=>go(cur+1);$('#bidx').onclick=()=>$('#index').classList.toggle('on');
$('#bfull').onclick=()=>{if(document.fullscreenElement)document.exitFullscreen();else document.documentElement.requestFullscreen&&document.documentElement.requestFullscreen()};
addEventListener('keydown',e=>{if(e.ctrlKey||e.metaKey||e.altKey)return;const k=e.key;
  if(k==='ArrowRight'||k==='PageDown'){e.preventDefault();go(cur+1)}else if(k==='ArrowLeft'||k==='PageUp'){e.preventDefault();go(cur-1)}
  else if(k==='Home'){go(0)}else if(k==='End'){go(N-1)}else if(k==='o'||k==='O'){$('#index').classList.toggle('on')}
  else if(k==='f'||k==='F'){$('#bfull').click()}else if(k==='Escape'){$('#index').classList.remove('on')}
  else if(k==='c'||k==='C'){const b=$('.cpall',slides[cur]);if(b)b.click()}});
$$('.check input').forEach(c=>{c.checked=!!hecho['lista-'+c.dataset.k]});
fit();marcar();const h=parseInt((location.hash||'').slice(1),10);go(h>0?h-1:0);
})();
"""


def terminal(titulo_barra, grupos):
    """grupos: lista de (subtitulo|None, [cmd...]). Cada comando lleva su boton de copiar."""
    filas = []
    for sub, cmds in grupos:
        if sub:
            filas.append(f'<div class="sub">{sub}</div>')
        for c in cmds:
            nota = f'<span class="nota">{c["nota"]}</span>' if c.get('nota') else ''
            filas.append(f'<div class="cmd"><button class="cp" data-t="{esc(c["c"])}" title="Copiar esta línea" aria-label="Copiar: {esc(c["c"])}">⧉</button>'
                         f'<div class="tx"><code class="l">{esc(c["c"])}</code>{nota}</div></div>')
    return f'<div class="term"><div class="bar"><i></i><i></i><i></i><em>{esc(titulo_barra)}</em></div>{"".join(filas)}</div>'


def slide(titulo, cuerpo, bloque='', id_=None, kick='', pie=''):
    attrs = f' data-title="{esc(titulo)}" data-bloque="{esc(bloque)}"' + (f' data-id="{id_}"' if id_ else '')
    return f'<section class="slide"{attrs}>{cuerpo}<div class="foot"><span>{esc(TITULO)}</span><span>{esc(pie)}</span></div></section>'


def _val(p):
    return f'<span class="tag {p["val"]}">{C.VAL_TEXTO[p["val"]]}</span>'


def _cabecera(p, n, total, fase=''):
    b = C.BLOQUES[p['bloque']]
    return (f'<div class="kick"><span>Bloque {b[0]} · {esc(b[1])} · paso {n} de {total}{(" · " + fase) if fase else ""}</span>{_val(p)}</div>'
            f'<h1>{esc(p["titulo"])}</h1>')


def _donde(p):
    return f'<div class="where">En: <span class="chip">{esc(C.DONDE[p["donde"]])}</span></div>'


def _comandos(p, con_hecho):
    grupos = [(None, p['cmds'])] + [(e['titulo'], e['cmds']) for e in p.get('extra', [])]
    todos = '\n'.join(cmds_planos(p))
    notas = ''.join(f'<p class="small" style="margin-top:6px">{e["nota"]}</p>' for e in p.get('extra', []) if e.get('nota'))
    hecho = '<button class="btn hecho-btn">Marcar como hecho</button>' if con_hecho else ''
    hay_aparte = any(c.get('aparte') for c in p['cmds'])
    if len(p['cmds']) > 1 and not hay_aparte:
        copiar = f'<button class="btn primary cpall" data-t="{esc(todos)}">Copiar todo (C)</button>'
    else:
        copiar = '<span class="small">Cópialas una a una (⧉)' + (': algunas van en otra terminal o llevan tus datos.' if hay_aparte else '.') + '</span>'
    return (f'{terminal("Terminal", grupos)}{notas}<div class="btns">{copiar}{hecho}</div>')


def _ui(p):
    return ('<ol class="ui">' + ''.join(f'<li><span>{t}</span></li>' for t in p['ui']) + '</ol>') if p.get('ui') else ''


def _esperado(p, salidas):
    reales = ''.join(f'<pre class="real{" larga" if salidas[k]["salida"].count(chr(10)) > 12 else ""}">{esc(salidas[k]["salida"])}</pre>' for k in p.get('real', []))
    nota = f'<p class="rn">{nota_real(p, salidas)}</p>' if p.get('real') and p.get('real_nota') else ''
    return f'<div class="card ok"><h3>Debe salir</h3><p style="font-size:15.5px;line-height:1.4">{p["esperado"]}</p>{reales}{nota}</div>'


def _falla(p, con_hecho=False):
    falla = ''.join(f'<li>{t}</li>' for t in p['si_falla'])
    vn = f'<p class="vn">{p["val_nota"]}</p>' if p.get('val_nota') else ''
    hecho = '<div class="btns"><button class="btn hecho-btn">Marcar como hecho</button></div>' if con_hecho else ''
    return f'<div class="card bad"><h3 style="color:var(--bad)">Si falla</h3><ul class="f">{falla}</ul></div>{vn}{hecho}'


def slides_paso(p, n, total, salidas):
    """Un paso = una diapositiva; si lleva dividir=True, dos («Hazlo» y «Comprueba»)."""
    b = C.BLOQUES[p['bloque']]
    bloque = f'Bloque {b[0]} · {b[1]}'
    por_que = f'<p class="muted" style="font-size:16px">{p["por_que"]}</p>'
    if not p.get('dividir'):
        antes, despues = ('', _ui(p)) if p.get('ui_despues') else (_ui(p), '')
        cuerpo = (f'{_cabecera(p, n, total)}{_donde(p)}<div class="cols"><div>{por_que}{antes}{_comandos(p, True)}{despues}</div>'
                  f'<div class="side">{_esperado(p, salidas)}{_falla(p)}</div></div>')
        return [slide(p['titulo'], cuerpo, bloque=bloque, id_=p['id'], pie=bloque)]
    antes, despues = ('', _ui(p)) if p.get('ui_despues') else (_ui(p), '')
    hazlo = f'{_cabecera(p, n, total, "Hazlo")}{_donde(p)}<div class="full">{por_que}{antes}{_comandos(p, False)}{despues}</div>'
    comprueba = (f'{_cabecera(p, n, total, "Comprueba")}<div class="cols" style="grid-template-columns:1.25fr .75fr">'
                 f'<div>{_esperado(p, salidas)}</div><div class="side">{_falla(p, True)}</div></div>')
    return [slide(p['titulo'] + ' · Hazlo', hazlo, bloque=bloque, id_=p['id'], pie=bloque + ' · Hazlo'),
            slide(p['titulo'] + ' · Comprueba', comprueba, bloque=bloque, id_=p['id'], pie=bloque + ' · Comprueba')]


def slide_portada():
    cuerpo = (f'<div class="cover"><div class="kick">S0 · ML e IA: de desarrollo a producción</div><h1>{esc(TITULO)}</h1>'
              '<p class="sub2">Instalar, crear el entorno y comprobarlo: todo para copiar y pegar, en el orden correcto y con una comprobación al final de cada paso.</p>'
              '<div class="chips"><span class="chip">Windows 10 (1809+) o 11</span><span class="chip">Entorno env-ia-mlops</span><span class="chip">Caso: Bank Marketing</span></div>'
              '<div class="card" style="max-width:980px"><h3>Cómo usar estas diapositivas</h3>'
              '<p style="font-size:16.5px">Pulsa <b>⧉</b> junto a cada línea para copiarla y pégala con Ctrl+V en la terminal que indica la diapositiva. '
              '<b>← →</b> navegan · <b>C</b> copia todo el bloque · <b>O</b> índice · <b>F</b> pantalla completa. '
              'No pases al siguiente paso si lo que ves no coincide con «Debe salir».</p>'
              '<p class="small" style="margin-top:8px">Los comandos de Python, conda, pytest, SQLite y MLflow se ejecutaron el ' + C.FECHA + ' en Linux, en un entorno recién creado con el '
              '<code>environment.yml</code> actual; las salidas que ves son las reales. <b>Nada se probó en un Windows real</b>: cada diapositiva lo indica en su etiqueta.</p></div></div>')
    return slide('Portada', cuerpo, bloque='Inicio', pie='')


def slide_mapa():
    bl = ''.join(f'<div class="blk{" f" if k == "F" else ""}"><div class="L">{v[0]}</div><b>{esc(v[1])}</b><span>{esc(v[2])}</span><em>{esc(v[3])}</em></div>' for k, v in C.BLOQUES.items())
    cuerpo = ('<div class="kick">El orden lógico</div><h1>Seis bloques, siempre en este orden</h1>'
              f'<div class="map">{bl}</div>'
              '<div class="two"><div class="card"><h3>Por qué este orden</h3><ul class="p">'
              '<li><b>Git antes de clonar</b>, y <b>Miniconda antes de crear el entorno</b>.</li>'
              '<li><b>Los canales de conda antes de crear</b>: si no, conda puede negarse por los términos de servicio.</li>'
              '<li><b>El repositorio antes que el entorno</b>: la receta (<code>environment.yml</code>) está dentro.</li>'
              '<li><b>El entorno antes de las pruebas</b>: todas usan su Python.</li></ul></div>'
              '<div class="card ok"><h3>La regla</h3><p style="font-size:17px">Cada paso termina con una comprobación (<b>Debe salir</b>). '
              'Si no sale igual, <b>para</b>: lee «Si falla». Seguir con un paso roto solo produce errores más raros después.</p>'
              '<p class="small" style="margin-top:8px">El bloque F (nube) no bloquea S1: puede esperar.</p></div></div>')
    return slide('El orden lógico', cuerpo, bloque='Inicio', pie='Mapa')


def slide_antes():
    cuerpo = ('<div class="kick">Antes de empezar</div><h1>Lo que necesitas y qué terminal usar</h1>'
              '<div class="two"><div class="card"><h3>Requisitos</h3><ul class="p">'
              '<li>Windows 10 (1809 o superior) o Windows 11. Esta edición no tiene guía para macOS ni Linux.</li>'
              '<li>Reserva unos <b>6 GB libres</b> (estimación): el entorno ocupa unos 2,5 GB (medido en Linux) y hay que sumar la caché de descargas de conda y los programas.</li>'
              '<li>Conexión estable: se descargan cientos de MB.</li>'
              '<li>Una cuenta de GitHub.</li>'
              '<li>No hace falta ser administrador: winget pedirá permiso cuando haga falta.</li>'
              '<li>Si tu equipo no te deja instalar programas, usa Codespaces (diapositiva «Si algo falla y cómo pedir ayuda»).</li></ul></div>'
              '<div><div class="card"><h3>Qué terminal para qué</h3><table><tr><th>Terminal</th><th>Para</th></tr>'
              '<tr><td><b>CMD</b> o <b>PowerShell</b></td><td>winget, Git, VS Code, clonar (bloques A y C)</td></tr>'
              '<tr><td><b>Anaconda Prompt</b> (Miniconda3)</td><td>conda y Python (B, D y E)</td></tr>'
              '<tr><td>Terminal de <b>VS Code</b></td><td>lo mismo que Anaconda Prompt, si el entorno está activo</td></tr></table>'
              f'<p style="font-size:16px;margin-top:10px">Sabrás que el entorno está activo porque el prompt empieza por <b>({C.ENTORNO})</b>.</p></div>'
              '<div class="card" style="margin-top:12px"><h3>Dos hábitos que evitan la mitad de los errores</h3><ul class="p">'
              '<li>Tras instalar un programa, <b>cierra y abre la terminal</b>.</li>'
              '<li>Copia con <b>⧉</b> y pega con <b>Ctrl+V</b>: no escribas los comandos a mano.</li></ul></div></div></div>')
    return slide('Antes de empezar', cuerpo, bloque='Inicio', pie='Requisitos')


def slide_archivos():
    n = numero_de_paquetes()
    cuerpo = ('<div class="kick">Bloque D · Entorno</div><h1>¿Qué archivo de requisitos uso?</h1>'
              '<p class="muted" style="margin-bottom:10px">Hay tres listas y las tres fijan las <b>mismas versiones</b> (' + C.FECHA + '). Una prueba automática lo vigila. Para tu equipo, solo importa la primera.</p>'
              '<div class="card"><table><tr><th>Archivo (en <code>03-Entorno/conda/</code>)</th><th>Qué es</th><th>Quién lo usa</th><th>Comando</th></tr>'
              f'<tr><td><code>environment.yml</code></td><td>Receta de conda: Python 3.11 y <b>{n} paquetes</b> con versión fijada, solo de conda-forge.</td><td><b>Tu equipo</b> (obligatorio)</td><td><code>conda env create -f …</code></td></tr>'
              f'<tr><td><code>requirements-dev.txt</code></td><td>Los mismos {n} paquetes, para pip.</td><td>Codespaces y GitHub Actions; alternativa sin conda</td><td><code>pip install -r …</code></td></tr>'
              '<tr><td><code>requirements.txt</code></td><td>Solo lo mínimo para ejecutar la API y el modelo (7 paquetes).</td><td>La imagen Docker de S2</td><td><code>pip install -r …</code></td></tr></table></div>'
              '<div class="two" style="margin-top:14px"><div class="card ok"><h3>Regla para tu entorno</h3><p style="font-size:16.5px">No instales paquetes con <code>pip</code> dentro de <code>env-ia-mlops</code> salvo que se te pida. '
              'Si lo haces, <code>verificar_s1.py</code> lo avisa («con otra version») y te da la línea que lo arregla: <code>conda install --force-reinstall paquete=versión</code>. <code>conda env update</code> no revierte lo que cambió pip.</p></div>'
              '<div class="card"><h3>Y el proyecto base</h3><p style="font-size:16.5px">Para S1 trabajas con el entorno del curso, sin instalar nada más: '
              '<code>04-Proyecto-Base</code> se ejecuta desde su carpeta, <b>sin</b> <code>pip install</code>. Las pruebas pasan así (comprobado en un entorno recién creado).</p></div></div>')
    return slide('¿Qué archivo de requisitos uso?', cuerpo, bloque='Bloque D · Entorno', pie='Bloque D · Entorno')


def slide_errores():
    filas = ''.join(f'<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>' for a, b, c in C.ERRORES)
    cuerpo = ('<div class="kick">Si algo falla (1 de 2)</div><h1>Errores frecuentes</h1>'
              f'<div class="card"><table><tr><th>Lo que ves</th><th>Causa</th><th>Qué hacer</th></tr>{filas}</table></div>')
    return slide('Errores frecuentes', cuerpo, bloque='Ayuda', pie='Ayuda')


def slide_ayuda():
    cuerpo = ('<div class="kick">Si algo falla (2 de 2)</div><h1>Si algo falla y cómo pedir ayuda</h1>'
              '<div class="two"><div class="card"><h3>Qué enviar al instructor</h3><ul class="p">'
              '<li><b>El comando</b> que ejecutaste y <b>en qué terminal</b> (CMD, PowerShell, Anaconda Prompt, VS Code).</li>'
              '<li><b>El mensaje de error completo</b>, copiado como texto (no recortado).</li>'
              '<li>El archivo <code>verificacion-s1.txt</code> (lo crea <code>verificar_s1.py --informe</code>; no lleva tu usuario ni tu correo).</li></ul></div>'
              '<div class="card bad"><h3 style="color:var(--bad)">Qué NO enviar nunca</h3><ul class="p">'
              '<li>Contraseñas, tokens ni claves de ningún servicio.</li>'
              '<li>Capturas de pantalla con tu sesión de GitHub o de Google Cloud abierta.</li></ul></div></div>'
              '<div class="card" style="margin-top:14px"><h3>Si tu equipo no te deja instalar nada</h3>'
              '<p style="font-size:17px">Usa la <b>ruta sin instalación</b>: Codespaces y Cloud Shell desde el navegador. Está en la guía interactiva '
              '<code>03-Entorno/guia-instalacion/index.html</code> (sección «Ruta sin instalación: Codespaces») y en <code>03-Entorno/guias/docker-y-kubernetes-sin-instalacion-local.md</code>. Avisa antes de S1.</p></div>')
    return slide('Si algo falla y cómo pedir ayuda', cuerpo, bloque='Ayuda', pie='Ayuda')


def slide_lista():
    items = ''.join(f'<label><input type="checkbox" data-k="{i}"><span>{t}</span><span class="ref">{r}</span></label>' for i, (t, r) in enumerate(C.LISTA_FINAL))
    cuerpo = ('<div class="kick">Final</div><h1>Listo para S1 cuando…</h1>'
              f'<div class="check">{items}</div>'
              '<p class="small" style="margin-top:12px" id="cuenta"></p>'
              '<p class="small" style="margin-top:4px">Las marcas se guardan solo en este navegador. En S1 empezamos con <code>conda activate env-ia-mlops</code> y <code>cd 04-Proyecto-Base</code>.</p>')
    return slide('Listo para S1', cuerpo, bloque='Final', pie='Lista final')


def slide_no_probado():
    li = ''.join(f'<li>{t}</li>' for t in C.NO_PROBADO)
    cuerpo = ('<div class="kick">Transparencia</div><h1>Qué se probó y qué no</h1>'
              '<div class="two"><div class="card ok"><h3>Probado ' + C.FECHA + ' (Linux)</h3><ul class="p">'
              '<li>Creación del entorno desde cero con <code>environment.yml</code>, y <b>HUMO OK</b>.</li>'
              '<li>Versiones instaladas = versiones fijadas (verificador).</li>'
              '<li>30 pruebas rápidas y 34 completas del proyecto base.</li>'
              '<li>SQLite, MLflow UI, lectura del CSV de Bank Marketing, registro del kernel y ejecución del cuaderno de prueba.</li>'
              '<li><code>git clone --branch develop</code> contra GitHub (clon superficial).</li></ul></div>'
              f'<div class="card bad"><h3 style="color:var(--bad)">Sin probar</h3><ul class="p">{li}</ul></div></div>'
              '<p class="small" style="margin-top:12px">Si algo de lo «sin probar» falla en tu equipo, es información valiosa: cuéntalo con el comando y el mensaje completo.</p>')
    return slide('Qué se probó y qué no', cuerpo, bloque='Final', pie='Transparencia')


def construir_html():
    salidas, meta = cargar_salidas()
    pasos = C.PASOS
    partes = [slide_portada(), slide_mapa(), slide_antes()]
    for i, p in enumerate(pasos, 1):
        if p['id'] == 'D1':
            partes.append(slide_archivos())                  # antes de crear el entorno: que archivo de requisitos usar
        partes += slides_paso(p, i, len(pasos), salidas)
    partes += [slide_errores(), slide_ayuda(), slide_lista(), slide_no_probado()]
    cuerpo = '\n'.join(partes)
    return (f'<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>{esc(TITULO)} · S0 · ML e IA: de desarrollo a producción</title>\n<style>{CSS}</style>\n</head>\n<body>\n'
            f'<div id="viewport"><div id="stage">\n{cuerpo}\n</div></div>\n<div id="prog"></div>\n'
            '<div id="index" aria-label="Índice"><h2>Índice</h2><div id="idxgrid"></div></div>\n'
            '<nav id="bar" aria-label="Controles"><button id="bprev" aria-label="Anterior">←</button><button id="bnext" aria-label="Siguiente">→</button>'
            '<span id="count">1</span><span class="sp"></span><button id="bidx">Índice (O)</button><button id="bfull">Pantalla completa (F)</button></nav>\n'
            '<noscript>Esta presentación necesita JavaScript. El contenido completo está en practica/guia-rapida-entorno-s0-s1.md.</noscript>\n'
            f'<script>{JS}</script>\n</body>\n</html>\n')


# ================================================================== Markdown
def bloque_codigo(lineas):
    return '```text\n' + '\n'.join(lineas) + '\n```\n'


def construir_md():
    salidas, meta = cargar_salidas()
    n = numero_de_paquetes()
    o = []
    a = o.append
    a(f'# {TITULO_GUIA}\n')
    a(f'> Generada desde `01-Sesiones/S0-Presentacion-y-Entorno/slides/instalacion/contenido.py` (la misma fuente que las diapositivas `slides/instalacion/index.html`). '
      'No la edites a mano: cambia `contenido.py` y ejecuta `python generar.py`.\n')
    a(f'**Para qué sirve:** dejar tu equipo listo para S1, en el orden correcto, con comandos para copiar y pegar y una comprobación al final de cada paso. '
      f'**Estado ({C.FECHA}):** los comandos de Python, conda, pytest, SQLite y MLflow están ejecutados en Linux en un entorno recién creado; '
      'lo de Windows (winget, Anaconda Prompt, VS Code) está **sin probar** y se indica en cada paso (ver el final).\n')
    a('## Las tres reglas\n')
    a('1. **Sigue el orden** (tabla de abajo) y **no pases al siguiente paso** si lo que ves no coincide con «Debe salir».\n'
      '2. **Cierra y abre la terminal** tras instalar un programa; si no, no lo reconoce.\n'
      f'3. **Mira el prompt**: para todo lo de Python debe empezar por `({C.ENTORNO})`.\n')
    a('## El orden\n')
    a('| Bloque | Qué | Terminal |\n|---|---|---|')
    for v in C.BLOQUES.values():
        a(f'| **{v[0]}** · {v[1]} | {v[2]} | {v[3]} |')
    a('')
    a('## Qué terminal usar\n')
    a('| Terminal | Para |\n|---|---|\n| **CMD** o **PowerShell** | winget, Git, VS Code, clonar (bloques A y C) |\n'
      '| **Anaconda Prompt (Miniconda3)** | conda y Python (B, D y E) |\n| Terminal de **VS Code** | lo mismo que Anaconda Prompt, si el entorno está activo |\n')
    a('Requisitos: Windows 10 (1809+) o 11; reserva unos 6 GB libres (estimación: el entorno ocupa unos 2,5 GB, medido en Linux, y hay que sumar la caché de descargas de conda y los programas); conexión estable; cuenta de GitHub; '
      'no hace falta ser administrador. Si tu equipo no te deja instalar programas, usa la ruta sin instalación (Codespaces): sección «Ruta sin instalación: Codespaces» de `03-Entorno/guia-instalacion/index.html`.\n')
    a('## ¿Qué archivo de requisitos uso?\n')
    a(f'| Archivo (`03-Entorno/conda/`) | Qué es | Quién lo usa | Comando |\n|---|---|---|---|\n'
      f'| `environment.yml` | Receta de conda: Python 3.11 y **{n} paquetes** con versión fijada (conda-forge) | **Tu equipo** (obligatorio) | `conda env create -f …` |\n'
      f'| `requirements-dev.txt` | Los mismos {n} paquetes, para pip | Codespaces, GitHub Actions; alternativa sin conda | `pip install -r …` |\n'
      '| `requirements.txt` | Lo mínimo para ejecutar la API y el modelo (7 paquetes) | La imagen Docker de S2 | `pip install -r …` |\n')
    a('Las tres listas fijan las mismas versiones (una prueba automática lo vigila). No instales paquetes con `pip` dentro de `env-ia-mlops` salvo que se te pida: '
      'el verificador lo avisa («con otra version») y te da la línea que lo arregla: `conda install --force-reinstall paquete=versión`. '
      '`conda env update` **no** revierte lo que cambió pip (comprobado); sí repone un paquete que falte.\n')
    a('## Paso a paso\n')
    for i, p in enumerate(C.PASOS, 1):
        b = C.BLOQUES[p['bloque']]
        a(f'### {p["id"]} · {p["titulo"]}\n')
        a(f'**Bloque {b[0]} ({b[1]}) · Terminal:** {C.DONDE[p["donde"]]} · **Validación:** {C.VAL_TEXTO[p["val"]]}\n')
        a(md(p['por_que']) + '\n')
        def pasos_ui():
            for j, t in enumerate(p.get('ui', []), 1):
                a(f'{j}. {md(t)}')
            if p.get('ui'):
                a('')
        if not p.get('ui_despues'):
            pasos_ui()
        lineas = []
        for c in p['cmds']:
            if c.get('nota'):
                lineas.append(f'# {md(c["nota"])}')
            lineas.append(c['c'])
        a(bloque_codigo(lineas))
        if p.get('ui_despues'):
            pasos_ui()
        for e in p.get('extra', []):
            a(f'**{e["titulo"]}:**\n')
            a(bloque_codigo([c['c'] for c in e['cmds']]))
            if e.get('nota'):
                a(md(e['nota']) + '\n')
        a(f'**Debe salir:** {md(p["esperado"])}\n')
        if p.get('real'):                                         # las salidas de un paso van seguidas, como en la terminal
            a(bloque_codigo([x for k in p['real'] for x in salidas[k]['salida'].split('\n')]))
        if p.get('real') and p.get('real_nota'):
            a(f'_{md(nota_real(p, salidas))}_\n')
        a('**Si falla:**\n')
        for t in p['si_falla']:
            a(f'- {md(t)}')
        if p.get('val_nota'):
            a(f'\n_Validación: {md(p["val_nota"])}_')
        a('')
    a('## Errores frecuentes\n')
    a('| Lo que ves | Causa | Qué hacer |\n|---|---|---|')
    for x, y, z in C.ERRORES:
        a(f'| {md(x)} | {md(y)} | {md(z)} |')
    a('')
    a('## Si algo falla y cómo pedir ayuda\n')
    a('Envía al instructor: (1) el comando que ejecutaste y en qué terminal; (2) el mensaje de error **completo**, como texto; (3) `verificacion-s1.txt` '
      '(lo crea `python 03-Entorno\\conda\\verificar_s1.py --informe`; no lleva tu usuario ni tu correo). **Nunca** envíes contraseñas, tokens ni claves.\n')
    a('## Listo para S1 cuando…\n')
    for t, r in C.LISTA_FINAL:
        a(f'- [ ] {md(t)} _({r})_')
    a('')
    a('## Comandos de todos los días\n')
    a('| Quiero… | Comando |\n|---|---|\n'
      '| Ver mis entornos (el activo lleva `*`) | `conda env list` |\n'
      f'| Activar / desactivar el entorno del curso | `conda activate {C.ENTORNO}` · `conda deactivate` |\n'
      '| Ver qué hay instalado | `conda list` |\n'
      '| Reponer un paquete que falta, o aplicar cambios del archivo | `conda env update -f 03-Entorno\\conda\\environment.yml --prune` |\n'
      '| Devolver un paquete a la versión fijada (lo cambió pip) | `conda install --force-reinstall paquete=versión` |\n'
      '| Saber en qué rama estoy / traer novedades | `git branch --show-current` · `git pull` |\n'
      '| Pruebas rápidas del proyecto base | `python -m pytest -q -m "not lento"` (desde `04-Proyecto-Base`) |\n'
      '| Pruebas cuyo nombre contiene «futuro» (S1) | `python -m pytest tests -k futuro -q` |\n'
      '| Abrir MLflow en S1 | `mlflow ui --backend-store-uri sqlite:///models/mlflow.db` (desde `04-Proyecto-Base`) |\n'
      '| Comprobar todo otra vez | `python 03-Entorno\\conda\\verificar_s1.py` |\n')
    a('Más detalle: `07-Recursos/guias/` (Miniconda, Git y ramas, VS Code, SQLite) y la guía interactiva `03-Entorno/guia-instalacion/index.html`.\n')
    a('## Qué se probó y qué no\n')
    a(f'**Probado el {C.FECHA} en Linux (kernel {meta.get("sistema", "").replace("Linux ", "")}), en un entorno creado desde cero con `environment.yml`:** creación del entorno, `HUMO OK`, '
      'versiones instaladas frente a las fijadas, 30 pruebas rápidas y 34 completas del proyecto base, SQLite, MLflow UI, lectura del CSV de Bank Marketing, '
      'registro del kernel, ejecución del cuaderno de prueba y `git clone --branch develop` contra GitHub (clon superficial). Las salidas que ves arriba son las reales de esa ejecución (`slides/instalacion/salidas-reales.json`).\n')
    a('**Sin probar:**\n')
    for t in C.NO_PROBADO:
        a(f'- {md(t)}')
    a('')
    return '\n'.join(o)


def main():
    SALIDA_HTML.write_text(construir_html(), encoding='utf-8')
    SALIDA_MD.write_text(construir_md(), encoding='utf-8')
    print(f'{SALIDA_HTML.relative_to(RAIZ)}: {SALIDA_HTML.stat().st_size} bytes')
    print(f'{SALIDA_MD.relative_to(RAIZ)}: {SALIDA_MD.stat().st_size} bytes')


if __name__ == '__main__':
    main()
