"""Genera la guía del alumnado «Codespaces: tu laboratorio de Docker en la nube»:
    - 03-Entorno/guia-codespaces/index.html            (diapositivas, con botones de copiar)
    - 03-Entorno/guias/codespaces-para-el-alumnado.md  (la misma guía en texto, para leer o imprimir)

Uso (desde cualquier carpeta):   python generar.py
No edites a mano esos dos archivos: cambia este script y vuelve a ejecutarlo.
Las salidas que muestra la guía salen de salidas-reales.json (capturar.py las renueva).

Origen de los datos:
  - Comandos del laboratorio: 01-Sesiones/S2-API-y-Docker/practica/guia-laboratorio.md, bloque 4 (una prueba lo vigila).
  - Configuración del Codespace: .devcontainer/devcontainer.json de la raíz del repositorio (una prueba lo vigila).
  - Cuotas, tiempos de inactividad y retención, VS Code, puertos y fork: documentación oficial de GitHub (ver FUENTES, 10/11/2026).
  - Capturas (capturas/*.webp) y tiempos del Codespace: un Codespace real del curso abierto el 12/11/2026 (2 núcleos, rama develop),
    con salidas-codespace.json. Las salidas en texto de los pasos siguen saliendo de salidas-reales.json (Linux, capturar.py).
"""
import base64
import html
import json
import re
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
SALIDA_HTML = AQUI / 'index.html'
SALIDA_MD = RAIZ / '03-Entorno' / 'guias' / 'codespaces-para-el-alumnado.md'
TITULO = 'Codespaces: tu laboratorio de Docker en la nube'
FECHA = '10/11/2026'
FECHA_PRUEBA = '12/11/2026'          # primer Codespace real del curso
CAPTURAS = AQUI / 'capturas'
REPO = 'helicr/curso-ml-ia-desarrollo-produccion'
PROYECTO = '04-Proyecto-Base'
STORE = 'codespaces-guia-hecho'

# Comandos del laboratorio (bloque 4 de S2): deben coincidir con practica/guia-laboratorio.md
CMD_ENTRAR = 'cd 04-Proyecto-Base'
CMD_PIPELINE = 'python -m ia_mlops.pipeline'
CMD_BUILD = 'docker build -f deploy/docker/Dockerfile -t retencion-api:local .'
CMD_LS = 'docker image ls retencion-api:local'
CMD_RUN = 'docker run -d --name api -p 8080:8080 retencion-api:local'
CMD_LISTO = 'curl http://127.0.0.1:8080/listo'
CMD_COMPARAR = 'python -m ia_mlops.modeling.comparar --url http://127.0.0.1:8080'
CMD_LOGS = 'docker logs api'
CMD_ID = 'docker exec api id -u'
CMD_RM = 'docker rm -f api'
COMANDOS_LAB = [CMD_ENTRAR, 'docker version', CMD_PIPELINE, CMD_BUILD, CMD_LS, CMD_RUN, CMD_LISTO, CMD_COMPARAR, CMD_LOGS, CMD_ID, CMD_RM]

# (clase de la etiqueta, texto)
VAL = {
    'probado': ('ok', 'Probado en un Codespace real · ' + FECHA_PRUEBA),
    'lab': ('mixto', 'Probado en Linux y Actions · Codespace sin probar'),
    'docs': ('sin', 'Según la doc. de GitHub · sin probar en un Codespace'),
    'cifras': ('mixto', 'Cifras leídas en la doc. de GitHub el ' + FECHA + ' · pueden cambiar'),
}

FUENTES = [
    ('Cuotas y precios de Codespaces', 'https://docs.github.com/en/billing/concepts/product-billing/github-codespaces'),
    ('Aprovechar el uso incluido (almacenamiento, tiempo de inactividad, retención)', 'https://docs.github.com/en/codespaces/troubleshooting/troubleshooting-included-usage'),
    ('Ciclo de vida de un Codespace (30 min de inactividad, borrado automático)', 'https://docs.github.com/en/codespaces/about-codespaces/understanding-the-codespace-lifecycle'),
    ('Borrado automático y periodo de retención (0–30 días)', 'https://docs.github.com/en/codespaces/setting-your-user-preferences/configuring-automatic-deletion-of-your-codespaces'),
    ('Tiempo de inactividad configurable (de 5 min a 4 h)', 'https://github.blog/changelog/codespaces-now-have-a-configurable-idle-timeout'),
    ('Crear un Codespace para un repositorio (rama, configuración, máquina)', 'https://docs.github.com/en/codespaces/developing-in-a-codespace/creating-a-codespace-for-a-repository'),
    ('Máquinas disponibles (de 2 núcleos, 8 GB, 32 GB en adelante)', 'https://docs.github.com/en/codespaces/about-codespaces/what-are-codespaces'),
    ('Usar Codespaces en Visual Studio Code', 'https://docs.github.com/en/codespaces/developing-in-a-codespace/using-github-codespaces-in-visual-studio-code'),
    ('Reabrir un Codespace (navegador, VS Code, gh codespace code)', 'https://docs.github.com/en/codespaces/developing-in-a-codespace/opening-an-existing-codespace'),
    ('Reenviar puertos', 'https://docs.github.com/en/codespaces/developing-in-a-codespace/forwarding-ports-in-your-codespace'),
    ('Control de versiones y fork automático', 'https://docs.github.com/en/codespaces/developing-in-a-codespace/using-source-control-in-your-codespace'),
    ('Exportar cambios a una rama sin abrir el Codespace', 'https://docs.github.com/en/codespaces/troubleshooting/exporting-changes-to-a-branch'),
    ('Reconstruir el contenedor y modo recuperación', 'https://docs.github.com/en/codespaces/developing-in-a-codespace/rebuilding-the-container-in-a-codespace'),
    ('Student Developer Pack (180 horas y 20 GB de Codespaces)', 'https://github.com/education/students'),
    ('Función docker-in-docker de los contenedores de desarrollo', 'https://github.com/devcontainers/features/tree/main/src/docker-in-docker'),
]


def esc(t):
    return html.escape(t, quote=True)


def md(t):
    """Convierte el HTML mínimo de los textos (<code>, <b>, <br>, <a>) a Markdown."""
    t = re.sub(r'<code>(.*?)</code>', lambda m: '`' + m.group(1) + '`', t)
    t = re.sub(r'<b>(.*?)</b>', r'**\1**', t)
    t = re.sub(r'<a href="([^"]+)"[^>]*>(.*?)</a>', r'[\2](\1)', t)
    t = t.replace('<br>', '  \n')
    t = re.sub(r'</?(span|em|small)[^>]*>', '', t)
    return html.unescape(t)


def cargar_salidas():
    return json.loads((AQUI / 'salidas-reales.json').read_text(encoding='utf-8'))


def cargar_codespace():
    return json.loads((AQUI / 'salidas-codespace.json').read_text(encoding='utf-8'))


def captura(nombre, pie, alto=None):
    """Captura real embebida (data URI): el HTML sigue abriéndose con doble clic, sin archivos aparte."""
    datos = base64.b64encode((CAPTURAS / f'{nombre}.webp').read_bytes()).decode('ascii')
    estilo = f' style="max-height:{alto}px;width:auto;max-width:100%;margin:0 auto"' if alto else ''
    return (f'<figure class="shot"><img src="data:image/webp;base64,{datos}" alt="{esc(pie)}"{estilo}>'
            f'<figcaption>{esc(pie)}</figcaption></figure>')


def captura_md(nombre, pie):
    """La misma captura en la versión en texto (03-Entorno/guias/), enlazada como archivo."""
    return f'![{pie}](../guia-codespaces/capturas/{nombre}.webp)'


# ================================================================== CSS y JS (misma familia que «Tu equipo listo para S1»)
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
.card.ok{border-color:rgba(52,211,153,.55)} .card.bad{border-color:rgba(251,113,133,.5)} .card.warn{border-color:rgba(251,191,36,.6)}
.tag{display:inline-block;font-size:12px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;padding:3px 10px;border-radius:999px;border:1px solid var(--line);color:var(--muted)}
.tag.mixto{color:#2b2100;background:var(--gold);border-color:var(--gold)} .tag.sin{color:var(--warn);border-color:var(--warn)}
.tag.ok{color:#032b1c;background:var(--ok);border-color:var(--ok)}
figure.shot{margin:8px 0 0;border:1px solid var(--line);border-radius:10px;overflow:hidden;background:#02101f}
figure.shot img{display:block;width:100%;height:auto}
figure.shot figcaption{font-size:12.5px;color:var(--muted);padding:5px 10px;border-top:1px solid var(--line)}
.shots{display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:start}
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
.btns{display:flex;gap:10px;margin-top:6px;align-items:center}
.btn{padding:7px 14px;border-radius:10px;border:1px solid var(--line);background:var(--panel);font-weight:700;font-size:14px}
.btn:hover{background:var(--panel2)} .btn.primary{background:var(--blue);color:#04213f;border-color:var(--blue)}
.btn.on{background:var(--ok);color:#032b1c;border-color:var(--ok)}
ol.ui{list-style:none;counter-reset:u;display:flex;flex-direction:column;gap:6px;margin:6px 0}
ol.ui li{counter-increment:u;display:flex;gap:10px;font-size:15.5px;line-height:1.34}
ol.ui li span{flex:1;min-width:0}
ol.ui li::before{content:counter(u);flex:none;width:24px;height:24px;border-radius:50%;background:var(--blue);color:#04213f;font-weight:800;font-size:14px;display:grid;place-items:center;margin-top:1px}
pre.real{font-family:var(--mono);font-size:12.5px;line-height:1.32;background:#02101f;border:1px solid var(--line);border-radius:10px;padding:8px 10px;margin-top:8px;white-space:pre-wrap;word-break:break-word;color:#cfe8ff}
.rn{font-size:12px;color:var(--muted);margin-top:4px}
.side{display:flex;flex-direction:column;gap:10px}
ul.f{list-style:none;display:flex;flex-direction:column;gap:6px}
ul.f li{font-size:14.5px;line-height:1.38;padding-left:16px;position:relative}
ul.f li::before{content:"›";position:absolute;left:2px;color:var(--bad);font-weight:800}
.vn{font-size:12.5px;color:var(--muted);margin-top:6px}
table{width:100%;border-collapse:collapse;font-size:15px}
th{font-size:12.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--gold);text-align:left;padding:6px 10px;border-bottom:2px solid var(--line)}
td{padding:7px 10px;border-bottom:1px solid rgba(26,95,163,.45);vertical-align:top;line-height:1.35}
table.dens td{padding:5px 10px;font-size:14.5px;line-height:1.3}
.two{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.three{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
ul.p{list-style:none;display:flex;flex-direction:column;gap:7px}
ul.p li{font-size:16.5px;line-height:1.4;padding-left:18px;position:relative}
ul.p li::before{content:"";position:absolute;left:0;top:9px;width:8px;height:8px;border-radius:3px;background:var(--blue)}
ul.p.s li{font-size:15px;line-height:1.36;gap:0}
.cover{display:flex;flex-direction:column;justify-content:center;height:100%;padding-bottom:20px}
.cover h1{font-size:58px;line-height:1.04;margin:6px 0 14px}.cover .sub2{font-size:23px;color:var(--muted);margin-bottom:22px;max-width:940px}
.chips{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:20px}
.check{display:flex;flex-direction:column;gap:8px}
.check label{display:flex;gap:12px;align-items:flex-start;font-size:17px;line-height:1.35;padding:8px 12px;background:var(--panel);border:1px solid var(--line);border-radius:12px;cursor:pointer}
.check input{width:20px;height:20px;margin-top:2px;accent-color:var(--ok)}
.check .ref{margin-left:auto;font-size:12.5px;color:var(--muted);white-space:nowrap;padding-left:10px}
ul.src{list-style:none;columns:2;column-gap:28px}
ul.src li{break-inside:avoid;font-size:13px;line-height:1.3;margin-bottom:7px}
ul.src a{display:block;font-family:var(--mono);font-size:11px;word-break:break-all}
#bar{position:fixed;left:0;right:0;bottom:0;height:46px;display:flex;gap:10px;align-items:center;padding:0 14px;background:#02101f;border-top:1px solid var(--line);font-size:14px}
#bar button{padding:6px 12px;border-radius:8px;border:1px solid var(--line);background:var(--panel)}
#bar .sp{flex:1}
#bar a#bhome{padding:6px 12px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--text);text-decoration:none;white-space:nowrap}
#bar a#bhome:hover{border-color:var(--gold)}
@media(max-width:900px){#bar a#bhome .tx{display:none}}
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
let hecho=store('@@STORE@@')||{};
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
  if(hb){const id=hb.closest('[data-id]').dataset.id;hecho[id]=!hecho[id];store('@@STORE@@',hecho);marcar();return}
});
document.addEventListener('change',e=>{const c=e.target.closest('.check input');if(c){hecho['lista-'+c.dataset.k]=c.checked;store('@@STORE@@',hecho)}});
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
""".replace('@@STORE@@', STORE)


# ================================================================== piezas de diapositiva
DIAS = []          # cada elemento: dict(titulo, bloque, id, html, md)


def terminal(titulo_barra, cmds):
    filas = []
    for c in cmds:
        nota = f'<span class="nota">{c["nota"]}</span>' if c.get('nota') else ''
        filas.append(f'<div class="cmd"><button class="cp" data-t="{esc(c["c"])}" title="Copiar esta línea" aria-label="Copiar: {esc(c["c"])}">⧉</button>'
                     f'<div class="tx"><code class="l">{esc(c["c"])}</code>{nota}</div></div>')
    return f'<div class="term"><div class="bar"><i></i><i></i><i></i><em>{esc(titulo_barra)}</em></div>{"".join(filas)}</div>'


def agregar(titulo, bloque, cuerpo_html, cuerpo_md, id_=None, pie=None):
    DIAS.append(dict(titulo=titulo, bloque=bloque, id=id_, html=cuerpo_html, md=cuerpo_md, pie=pie or bloque))


def val_html(v):
    clase, texto = VAL[v]
    return f'<span class="tag {clase}">{esc(texto)}</span>'


def paso(id_, bloque, n_de, titulo, donde, por_que, cmds=None, ui=None, esperado='', real=None, real_nota='', si_falla=(), val='lab',
         terminal_titulo='Terminal del Codespace', ui_despues=False, hecho=True, extra_md='', dividir=False, capturas=()):
    """Una diapositiva de paso: qué hacer (izquierda) y «Debe salir» / «Si falla» (derecha).

    capturas: lista de grupos; cada grupo es una lista de (nombre, pie) y da una diapositiva «Así se ve» (una o dos imágenes).
    """
    cmds = cmds or []
    ui_html = ('<ol class="ui">' + ''.join(f'<li><span>{t}</span></li>' for t in ui) + '</ol>') if ui else ''
    term = terminal(terminal_titulo, cmds) if cmds else ''
    botones = ''
    if len(cmds) > 1:
        botones += f'<button class="btn primary cpall" data-t="{esc(chr(10).join(c["c"] for c in cmds))}">Copiar todo (C)</button>'
    if hecho:
        botones += '<button class="btn hecho-btn">Marcar como hecho</button>'
    botones = f'<div class="btns">{botones}</div>' if botones else ''
    antes, despues = ('', ui_html) if ui_despues else (ui_html, '')
    reales = ''.join(f'<pre class="real">{esc(r)}</pre>' for r in (real or []))
    rn = f'<p class="rn">{real_nota}</p>' if real_nota else ''
    falla = ''.join(f'<li>{t}</li>' for t in si_falla)
    kick = lambda fase: f'<div class="kick"><span>{esc(bloque)} · paso {n_de}{fase}</span>{val_html(val)}</div><h1>{esc(titulo)}</h1>'
    donde_html = f'<div class="where">En: <span class="chip">{esc(donde)}</span></div>'
    card_ok = f'<div class="card ok"><h3>Debe salir</h3><p style="font-size:15.5px;line-height:1.4">{esperado}</p>{reales}{rn}</div>'
    card_bad = f'<div class="card bad"><h3 style="color:var(--bad)">Si falla</h3><ul class="f">{falla}</ul></div>'
    if not dividir:
        cuerpo = (f'{kick("")}{donde_html}<div class="cols"><div><p class="muted" style="font-size:16px">{por_que}</p>{antes}{term}{botones}{despues}</div>'
                  f'<div class="side">{card_ok}{card_bad}</div></div>')
        paginas = [(titulo, cuerpo, id_ if hecho else None, '')]
    else:
        solo_copiar = botones.replace('<button class="btn hecho-btn">Marcar como hecho</button>', '')
        solo_copiar = solo_copiar if 'cpall' in solo_copiar else ''
        solo_copiar = f'<div class="btns">{solo_copiar}</div>' if solo_copiar else ''
        hazlo = f'{kick(" · Hazlo")}{donde_html}<div><p class="muted" style="font-size:16px">{por_que}</p>{antes}{term}{solo_copiar}{despues}</div>'
        boton_hecho = '<div class="btns"><button class="btn hecho-btn">Marcar como hecho</button></div>' if hecho else ''
        comprueba = (f'{kick(" · Comprueba")}<div class="cols" style="grid-template-columns:1.25fr .75fr"><div>{card_ok}</div>'
                     f'<div class="side">{card_bad}{boton_hecho}</div></div>')
        paginas = [(titulo + ' · Hazlo', hazlo, None, ' · Hazlo'), (titulo + ' · Comprueba', comprueba, id_ if hecho else None, ' · Comprueba')]
    # Markdown
    m = [f'## {titulo}', f'*{bloque} · paso {n_de} · {VAL[val][1]}*', '', f'**En:** {donde}', '', md(por_que), '']
    if ui:
        m += [f'{i}. {md(t)}' for i, t in enumerate(ui, 1)] + ['']
    if cmds:
        m += ['```bash'] + [c['c'] for c in cmds] + ['```', '']
    m += [f'**Debe salir.** {md(esperado)}', '']
    for r in (real or []):
        m += ['```text', r, '```']
    if real_nota:
        m += [f'*{md(real_nota)}*', '']
    m += ['**Si falla:**'] + [f'- {md(t)}' for t in si_falla]
    if extra_md:
        m += ['', extra_md]
    for g, grupo in enumerate(capturas, 1):
        n_imgs = len(grupo)
        alto = 540 if n_imgs == 1 else 500
        figuras = ''.join(captura(nombre, pie, alto=alto) for nombre, pie in grupo)
        cuerpo = (f'<div class="kick"><span>{esc(bloque)} · paso {n_de} · Así se ve</span>{val_html("probado")}</div><h1>{esc(titulo)}</h1>'
                  + (f'<div class="shots">{figuras}</div>' if n_imgs > 1 else figuras))
        sufijo = ' · Así se ve' + (f' ({g})' if len(capturas) > 1 else '')
        paginas.append((titulo + sufijo, cuerpo, None, sufijo))
        m += [''] + [captura_md(nombre, pie) for nombre, pie in grupo]
    for k, (tit, cuerpo, ident, sufijo) in enumerate(paginas):
        agregar(tit, bloque, cuerpo, '\n'.join(m) if k == 0 else '', id_=ident, pie=bloque + sufijo)


def libre(titulo, bloque, kick, h1, cuerpo_html, cuerpo_md, id_=None, pie=None):
    agregar(titulo, bloque, f'<div class="kick">{esc(kick)}</div><h1>{esc(h1)}</h1>{cuerpo_html}',
            f'## {h1}\n\n{cuerpo_md}', id_=id_, pie=pie)


# ================================================================== contenido
def construir_contenido():
    S = cargar_salidas()
    sal = S['salidas']
    CS = cargar_codespace()
    t = CS['tiempos_segundos']
    verificar = '\n'.join(CS['verificar_sh'])
    comparar = sal['comparar']['salida']
    pipeline_fin = '\n'.join(sal['pipeline']['ultimas_lineas'][-5:])
    listo = sal['listo']['salida']

    # ---- 1. portada
    portada = ('<div class="cover"><div class="kick">ML e IA: de desarrollo a producción · Guía de herramientas</div>'
               f'<h1>{esc(TITULO)}</h1>'
               '<p class="sub2">Qué es, cómo abrirlo (en el navegador o desde tu VS Code), qué haremos dentro en S2 y cómo cuidar tu cuota.</p>'
               '<div class="chips"><span class="chip">GitHub Codespaces</span><span class="chip">Docker sin instalar</span><span class="chip">VS Code</span><span class="chip">S2 · bloque 4</span></div>'
               '<div class="card" style="max-width:1010px"><h3>Cómo usar estas diapositivas</h3>'
               '<p style="font-size:16.5px">Pulsa <b>⧉</b> junto a cada línea para copiarla y pégala en la terminal del Codespace. '
               '<b>← →</b> navegan · <b>C</b> copia todo el bloque · <b>O</b> índice · <b>F</b> pantalla completa.</p>'
               f'<p class="small" style="margin-top:8px"><b>Las capturas son de un Codespace real del curso</b>, abierto el {FECHA_PRUEBA} con la máquina de 2 núcleos y la rama <code>develop</code>: '
               f'las diapositivas «Así se ve» enseñan lo que vas a encontrar. Lo que no se probó allí (VS Code de escritorio, cuotas) sale de la documentación de GitHub ({FECHA}) y lo dice su etiqueta. '
               'Si algo difiere, anota el mensaje exacto.</p></div></div>')
    agregar('Portada', 'Inicio', portada,
            f'# {TITULO}\n\nGuía del alumnado de «ML e IA: de desarrollo a producción». Qué es un Codespace, cómo abrirlo (en el navegador o desde tu VS Code), '
            f'qué haremos dentro en S2 (bloque 4) y cómo cuidar tu cuota.\n\n> **Estado.** Las capturas y los tiempos son de un Codespace real del curso, abierto el {FECHA_PRUEBA} '
            f'(2 núcleos, rama `develop`). Lo que no se probó allí (VS Code de escritorio, cuotas) sale de la documentación de GitHub ({FECHA}) y lo indica cada paso. '
            'Si algo difiere, anota el mensaje exacto del error y envíaselo al instructor.\n\nEl mismo contenido, en diapositivas con botones de copiar: `03-Entorno/guia-codespaces/index.html`.',
            pie='')

    # ---- 2. qué es
    libre('Qué es y por qué lo usamos', 'A · Antes de empezar', 'A · Antes de empezar', 'Qué es un Codespace y por qué lo usamos',
          '<div class="two"><div class="card"><h3>Qué es</h3><ul class="p">'
          '<li>Un <b>ordenador Linux que GitHub te presta en la nube</b>, con VS Code en el navegador o conectado a tu VS Code.</li>'
          '<li>Se crea a partir de <b>un repositorio</b> y de un archivo de configuración: <code>.devcontainer/devcontainer.json</code>.</li>'
          '<li>Trae <b>Docker ya funcionando</b> (un motor propio dentro del Codespace): no instalas Docker Desktop.</li>'
          '<li>Todos usamos el mismo Python 3.11 y los mismos comandos, también quien no puede instalar programas.</li></ul></div>'
          '<div><div class="card ok"><h3>Para qué lo usamos</h3><p style="font-size:16.5px">Para <b>lo que necesita Docker</b>: construir la imagen de la API y ejecutar el contenedor '
          '(S2, bloque 4, 25 min). Trae también <code>kind</code> y <code>kubectl</code> para un laboratorio de Kubernetes en S3 (el laboratorio está pendiente).</p></div>'
          '<div class="card warn" style="margin-top:12px"><h3 style="color:var(--warn)">Lo que conviene tener claro</h3><ul class="p s">'
          '<li><b>No sustituye a tu entorno local</b>: S1 y los bloques 1 a 3 de S2 siguen en tu equipo con <code>env-ia-mlops</code>.</li>'
          '<li>Es <b>temporal</b>: si lo borras, lo que no hayas subido a un repositorio desaparece.</li>'
          '<li>Tiene <b>cuota mensual</b> gratuita; hay que pararlo y borrarlo (diapositivas del final del curso de uso).</li></ul></div></div></div>',
          '**Qué es.** Un ordenador Linux que GitHub te presta en la nube, con VS Code en el navegador o conectado a tu VS Code. Se crea a partir de un repositorio y de '
          '`.devcontainer/devcontainer.json`. Trae Docker funcionando (un motor propio dentro del Codespace): no instalas Docker Desktop. Todos usamos el mismo Python 3.11 y los mismos comandos.\n\n'
          '**Para qué lo usamos.** Para lo que necesita Docker: construir la imagen de la API y ejecutar el contenedor (S2, bloque 4, 25 min). Trae también `kind` y `kubectl` '
          'para un laboratorio de Kubernetes en S3 (el laboratorio está pendiente).\n\n**Conviene tener claro:**\n- No sustituye a tu entorno local: S1 y los bloques 1 a 3 de S2 siguen en tu equipo con `env-ia-mlops`.\n'
          '- Es temporal: si lo borras, lo que no hayas subido a un repositorio desaparece.\n- Tiene cuota mensual gratuita: hay que pararlo y borrarlo.')

    # ---- 3. dónde se hace cada cosa
    filas = [
        ('Tu equipo', '<code>env-ia-mlops</code> (conda), VS Code, Git', 'S1 completa · S2 bloques 1 a 3: API, errores, comparar predicciones'),
        ('<b>Codespace</b>', 'El mismo <code>env-ia-mlops</code> (Python 3.11) + Docker + <code>kind</code> y <code>kubectl</code>', '<b>S2 bloque 4</b>: imagen y contenedor (S3: Kubernetes, pendiente)'),
        ('GitHub Actions', 'Un servidor de GitHub que ejecuta el workflow <code>ci.yml</code>', 'S2 bloque 5: el CI construye la imagen y prueba el contenedor'),
        ('Cloud Shell (respaldo)', 'Terminal de Google Cloud en el navegador', 'Solo si falla el Codespace; por verificar antes de impartir'),
    ]
    tabla = ''.join(f'<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>' for a, b, c in filas)
    libre('Qué se hace dónde', 'A · Antes de empezar', 'A · Antes de empezar', 'Qué se hace en cada sitio',
          f'<div class="card"><table><tr><th>Dónde</th><th>Qué hay</th><th>Qué haces ahí</th></tr>{tabla}</table></div>'
          '<div class="card ok" style="margin-top:14px"><h3>La idea</h3><p style="font-size:17px">Cada herramienta hace lo que mejor se le da: <b>tu equipo</b> para programar y entrenar, '
          'el <b>Codespace</b> para Docker, y <b>GitHub Actions</b> para comprobar en cada cambio que todo sigue funcionando. Si no puedes usar el Codespace, '
          'el bloque 5 (Actions) construye la imagen por ti.</p></div>',
          '| Dónde | Qué hay | Qué haces ahí |\n|---|---|---|\n' + '\n'.join(f'| {md(a)} | {md(b)} | {md(c)} |' for a, b, c in filas) +
          '\n\nSi no puedes usar el Codespace, el bloque 5 (GitHub Actions) construye la imagen por ti.')

    # ---- 4. antes de empezar (lista)
    previos = [
        ('Tengo una <b>cuenta personal</b> de GitHub (no la de mi empresa). Las cuentas de organización no incluyen horas gratuitas.', 'cuotas'),
        ('Puedo entrar en <code>github.com/codespaces</code> con mi cuenta sin que aparezca ningún bloqueo.', 'sin probar'),
        ('Sé que trabajo sobre la rama <code>develop</code> del repositorio del curso.', 'S2'),
        ('Tengo claro que <b>cerrar la pestaña no para el Codespace</b>: sigue gastando cuota hasta que se agota el tiempo de inactividad.', 'cuota'),
        ('(Opcional) Tengo VS Code con la extensión <b>GitHub Codespaces</b> (<code>GitHub.codespaces</code>), que ya estaba en la lista de S0.', 'VS Code'),
    ]
    items = ''.join(f'<label><input type="checkbox" data-k="p{i}"><span>{t}</span><span class="ref">{r}</span></label>' for i, (t, r) in enumerate(previos))
    libre('Antes de empezar', 'A · Antes de empezar', 'A · Antes de empezar', 'Antes de abrir tu primer Codespace',
          f'<div class="check">{items}</div><p class="small" style="margin-top:12px">Las marcas se guardan solo en este navegador. Si tu cuenta es de estudiante verificado '
          '(GitHub Student Developer Pack), tienes la cuota del plan Pro.</p>',
          '\n'.join(f'- [ ] {md(t)}' for t, _ in previos))

    # ---- 5. cuota
    libre('Cuánto es gratis', 'A · Antes de empezar', 'A · Antes de empezar', 'Cuánto es gratis y cómo se cuenta',
          '<div class="cols" style="grid-template-columns:1.05fr .95fr"><div><div class="card"><table class="dens"><tr><th>Cuenta</th><th>Horas de núcleo al mes</th><th>Disco al mes</th></tr>'
          '<tr><td>GitHub Free (personal)</td><td>120</td><td>15 GB-mes</td></tr>'
          '<tr><td>GitHub Pro</td><td>180</td><td>20 GB-mes</td></tr>'
          '<tr><td>Estudiante verificado (Student Developer Pack)</td><td>180</td><td>20 GB-mes</td></tr>'
          '<tr><td>Cuenta de organización o empresa</td><td>ninguna gratis</td><td>—</td></tr></table></div>'
          f'<p class="small" style="margin-top:10px">{val_html("cifras")}</p>'
          '<div class="card warn" style="margin-top:10px"><p style="font-size:15.5px">Si <b>se agota</b> el cómputo o el disco y no tienes método de pago, GitHub bloquea Codespaces hasta el ciclo mensual siguiente. '
          '<b>No hace falta añadir un método de pago</b> para seguir el curso.</p></div></div>'
          '<div class="card"><h3>Cómo se cuenta</h3><ul class="p s">'
          '<li><b>Hora de núcleo = horas de uso × núcleos.</b> La máquina más pequeña (2 núcleos, 8 GB de RAM, 32 GB de disco) gasta 2 por hora: 120 equivalen a <b>60 horas reales</b> (180, a 90).</li>'
          '<li>Una sesión de 4 h con el Codespace abierto todo el rato son 8 horas de núcleo (cálculo: 2 × 4), el 7 % de 120.</li>'
          '<li><b>Parado no gasta cómputo</b>, pero su disco cuenta mientras exista, aunque esté parado. Y borrarlo no devuelve el disco que ya contó este mes.</li>'
          '<li>GitHub avisa por correo al llegar al 75, 90 y 100 %.</li>'
          f'<li>Deja la máquina por defecto (la más pequeña, <b>2 núcleos</b>): el bloque 4 entero funcionó en ella el {FECHA_PRUEBA}.</li></ul></div></div>',
          '| Cuenta | Horas de núcleo al mes | Disco al mes |\n|---|---|---|\n| GitHub Free (personal) | 120 | 15 GB-mes |\n| GitHub Pro | 180 | 20 GB-mes |\n'
          '| Estudiante verificado (Student Developer Pack) | 180 | 20 GB-mes |\n| Cuenta de organización o empresa | ninguna gratis | — |\n\n'
          f'*Cifras leídas en la documentación de GitHub el {FECHA}; pueden cambiar.*\n\n'
          '- **Hora de núcleo = horas de uso × núcleos.** La máquina más pequeña (2 núcleos, 8 GB de RAM, 32 GB de disco) gasta 2 por hora: 120 equivalen a 60 horas reales (180, a 90).\n'
          '- Una sesión de 4 h con el Codespace abierto todo el rato son 8 horas de núcleo (cálculo: 2 × 4), el 7 % de 120.\n'
          '- Parado no gasta cómputo, pero su disco cuenta mientras exista. Borrarlo no devuelve el disco que ya contó este mes.\n'
          '- GitHub avisa por correo al llegar al 75, 90 y 100 %. Sin método de pago, al agotar una cuota se bloquea hasta el ciclo siguiente.\n'
          f'- Deja la máquina por defecto (la más pequeña, 2 núcleos): el bloque 4 entero funcionó en ella el {FECHA_PRUEBA}.')

    # ---- 6. crear el Codespace
    paso('crear', 'B · Abrir el Codespace', '1 de 8', 'Crear el Codespace del curso', 'tu navegador, con tu sesión de GitHub',
         'Se crea desde la página del repositorio, eligiendo la rama <code>develop</code>.',
         ui=[f'Abre <code>github.com/{REPO}</code> e inicia sesión con tu cuenta personal.',
             'En el desplegable de ramas elige <code>develop</code>.',
             'Pulsa el botón verde <b>Code</b> y la pestaña <b>Codespaces</b>: verás <b>Create codespace on develop</b>.',
             'Mejor por <b>⋯ → New with options…</b>: comprueba la rama (<code>develop</code>), la configuración (solo hay una: <i>Curso ML e IA: de desarrollo a producción</i>), '
             'la <b>región</b> (elige la más cercana: desde Perú, <i>US East</i>) y la máquina (<b>2-core</b>). Pulsa <b>Create codespace</b>.'],
         cmds=[dict(c='https://github.com/codespaces/new', nota='Atajo: elige repositorio y rama en esta página (también vale escribir codespace.new).')],
         terminal_titulo='Barra de direcciones del navegador',
         esperado=f'Se abre una pestaña nueva con <b>VS Code en el navegador</b>. La primera vez tarda unos <b>{round(t["crear_y_conectar_primera_vez"] / 60)} minutos</b> en construir el contenedor y conectar '
                  f'(abajo a la izquierda pone «Abriendo remoto…»), y después unos <b>{round(t["postcreate_kind_y_entorno"] / 60)} minutos</b> más en instalar <code>kind</code> y el entorno <code>env-ia-mlops</code>. '
                  'Al pie del menú de Codespaces, GitHub dice <b>qué cuenta paga</b>: debe ser la tuya.',
         si_falla=['No puedes crear uno o se bloquea: revisa tu uso y cuota (diapositiva «Cuánto es gratis») y que entras con tu cuenta personal.',
                   '«Maximum running codespaces reached»: ya tienes otro encendido. Páralo en <code>github.com/codespaces</code> (⋯ → <b>Stop codespace</b>) y repite.',
                   'Pide permiso para hacer un fork: el repositorio del curso es público; acepta. Solo tienes lectura, y el fork se crea cuando haces tu primer commit.',
                   'Aparece «modo recuperación»: ve a «Si algo falla».'],
         val='probado', hecho=True,
         capturas=[[('01-pestana-codespaces', 'Code → pestaña Codespaces en la rama develop. Al pie: quién paga el uso (aquí, la cuenta del instructor; en tu caso, la tuya).')],
                   [('02-nuevo-con-opciones', '⋯ → New with options: rama, la única configuración del curso, región y máquina de 2 núcleos.')]])

    # ---- 6b. mientras se crea y el aviso de confianza
    libre('Mientras se crea', 'B · Abrir el Codespace', 'B · Abrir el Codespace · paso 1 · lo que verás', 'Mientras se crea… y el primer aviso',
          '<div class="shots">'
          + captura('03-construyendo', f'Construyendo: «Abriendo remoto…» abajo a la izquierda. La primera vez, unos {round(t["crear_y_conectar_primera_vez"] / 60)} minutos.', alto=300)
          + captura('04-confiar', 'Al conectar: «¿Confía en los autores de los archivos de esta carpeta?» → Confiar en la carpeta y continuar.', alto=300)
          + '</div><div class="two" style="margin-top:12px"><div class="card"><p style="font-size:15.5px">No cierres la pestaña mientras se construye. Cuando conecta, abajo a la izquierda pasa a decir '
          '<b>Codespaces: &lt;nombre&gt;</b> y aparece el Explorador con las carpetas del curso.</p></div>'
          '<div class="card ok"><p style="font-size:15.5px">VS Code pregunta si <b>confías en los autores</b> de la carpeta. Es el repositorio del curso: pulsa <b>Confiar en la carpeta y continuar</b>. '
          'Sin eso, la terminal no se abre (modo restringido).</p>'
          f'<p class="small" style="margin-top:6px">{val_html("probado")}</p></div></div>',
          f'Mientras se construye, abajo a la izquierda pone «Abriendo remoto…» (la primera vez, unos {round(t["crear_y_conectar_primera_vez"] / 60)} minutos). No cierres la pestaña. '
          'Cuando conecta, pasa a decir «Codespaces: <nombre>» y aparece el Explorador con las carpetas del curso.\n\n'
          'VS Code pregunta **«¿Confía en los autores de los archivos de esta carpeta?»**. Es el repositorio del curso: pulsa **Confiar en la carpeta y continuar**. '
          'Sin eso, la terminal no se abre (modo restringido).\n\n'
          + captura_md('03-construyendo', 'Construyendo el Codespace') + '\n\n' + captura_md('04-confiar', 'Confiar en los autores de la carpeta'))

    # ---- 7. qué lleva el devcontainer
    libre('Qué lleva el .devcontainer', 'B · Abrir el Codespace', 'B · Abrir el Codespace · mientras se crea', 'Qué se prepara mientras esperas',
          '<div class="cols" style="grid-template-columns:1.25fr .75fr"><div class="card"><table class="dens"><tr><th>En <code>.devcontainer/</code></th><th>Qué consigue</th></tr>'
          '<tr><td><code>image: mcr.microsoft.com/devcontainers/miniconda:3</code></td><td>Linux con conda, como en tu equipo.</td></tr>'
          '<tr><td><code>docker-in-docker:2</code> con <code>"moby": false</code></td><td>Un motor Docker propio dentro del Codespace: <code>docker build</code> y <code>docker run</code> sin instalar nada.</td></tr>'
          '<tr><td><code>kubectl-helm-minikube:1</code></td><td><code>kubectl</code> (para S3).</td></tr>'
          '<tr><td><code>postcreate.sh</code></td><td>Instala <code>kind</code> y crea <code>env-ia-mlops</code> con las versiones del curso, y ejecuta <code>verificar.sh</code>.</td></tr>'
          '<tr><td><code>forwardPorts: [8080, 5000]</code></td><td>Reenvía la API («API ia-mlops (S2)») y MLflow («MLflow UI»).</td></tr>'
          '<tr><td><code>extensions</code></td><td>Python, Jupyter, Docker, Kubernetes, GitHub Actions y un visor de SQLite.</td></tr></table></div>'
          f'<div class="side"><div class="card ok"><h3>Lo que comprueba al terminar</h3><pre class="real">{esc(verificar)}</pre>'
          f'<p class="rn">Registro de creación real ({FECHA_PRUEBA}). «hello» muestra la primera línea de <code>docker run hello-world</code>: descarga la imagen y funciona.</p></div>'
          '<div class="card"><ul class="p s"><li>La terminal se abre en la <b>raíz del repositorio</b> y con <code>(env-ia-mlops)</code> activado: entra con <code>cd 04-Proyecto-Base</code>.</li>'
          '<li>Tú no editas estos archivos. Si fallan, GitHub abre el Codespace en <b>modo recuperación</b>.</li></ul></div></div></div>',
          '| En `.devcontainer/` | Qué consigue |\n|---|---|\n'
          '| `image: mcr.microsoft.com/devcontainers/miniconda:3` | Linux con conda, como en tu equipo. |\n'
          '| `docker-in-docker:2` con `"moby": false` | Un motor Docker propio dentro del Codespace: `docker build` y `docker run` sin instalar nada. |\n'
          '| `kubectl-helm-minikube:1` | `kubectl` (para S3). |\n'
          '| `postcreate.sh` | Instala `kind` y crea `env-ia-mlops` con las versiones del curso, y ejecuta `verificar.sh`. |\n'
          '| `forwardPorts: [8080, 5000]` | Reenvía la API («API ia-mlops (S2)») y MLflow («MLflow UI»). |\n'
          '| `extensions` | Python, Jupyter, Docker, Kubernetes, GitHub Actions y un visor de SQLite. |\n\n'
          f'**Lo que comprueba al terminar** (registro de creación real, {FECHA_PRUEBA}):\n\n```text\n{verificar}\n```\n\n'
          'La terminal se abre en la raíz del repositorio y con `(env-ia-mlops)` activado: entra con `cd 04-Proyecto-Base`. Tú no editas estos archivos. '
          'Si fallan, GitHub abre el Codespace en modo recuperación.')

    # ---- 8. orientarse y comprobar
    paso('orientar', 'B · Abrir el Codespace', '2 de 8', 'Orientarte y comprobar Docker', 'la terminal del Codespace',
         'Cuando termine de prepararse, abre una terminal y comprueba lo mínimo antes de seguir.',
         ui=['Abre la terminal: menú <b>☰ → Terminal → Nuevo terminal</b> (<i>New Terminal</i> si está en inglés). Los comandos se ejecutan <b>en el Codespace</b>, no en tu equipo.',
             'El indicador debe empezar por <code>(env-ia-mlops)</code>, como en tu equipo.',
             'Junto a la terminal verás la pestaña <b>Puertos</b> (<i>PORTS</i>): la usaremos después.'],
         cmds=[dict(c=CMD_ENTRAR), dict(c='python --version'), dict(c='docker version')],
         esperado=f'<code>Python {CS["versiones"]["python"]}</code>. <code>docker version</code> debe mostrar dos bloques: <b>Client</b> y <b>Server</b> '
                  f'(en el Codespace de prueba, Docker Engine Community {CS["versiones"]["docker"]}). Sin Server, Docker no ha arrancado.',
         si_falla=['El indicador dice <code>(base)</code> en vez de <code>(env-ia-mlops)</code>: <code>conda activate env-ia-mlops</code>.',
                   '<code>docker: command not found</code>: la configuración no se aplicó. Paleta de comandos (<b>F1</b>) → <b>Codespaces: Rebuild Container</b>.',
                   'Solo aparece Client o dice <code>Cannot connect to the Docker daemon</code>: repite al cabo de un minuto; si sigue, reconstruye el contenedor.',
                   'Sigue sin ir: usa el bloque 5 (Actions), que construye la imagen por ti, y <b>anota el mensaje exacto</b>.'],
         val='probado',
         capturas=[[('06-docker-version', 'docker version en el Codespace: Client y Server, y el indicador (env-ia-mlops) en la carpeta 04-Proyecto-Base.')]])

    # ---- 9. navegador o escritorio
    libre('Navegador o VS Code de escritorio', 'B · Abrir el Codespace', 'B · Abrir el Codespace', 'En el navegador o en tu VS Code: el mismo Codespace',
          '<div class="two"><div class="card"><h3>VS Code en el navegador</h3><ul class="p s">'
          '<li><b>Es lo que se abre por defecto</b> al crear un Codespace en GitHub.</li>'
          '<li>No instalas nada: sirve en un equipo donde no puedes instalar programas.</li>'
          '<li>Las extensiones de la configuración del curso ya vienen.</li>'
          '<li>Se reabre desde <code>github.com/codespaces</code>.</li></ul></div>'
          '<div class="card"><h3>VS Code de escritorio</h3><ul class="p s">'
          '<li>Tu VS Code, con tus ajustes y atajos, <b>conectado</b> al Codespace.</li>'
          '<li>Requiere VS Code 1.51 o posterior y la extensión <b>GitHub Codespaces</b>.</li>'
          '<li>El código <b>sigue ejecutándose en el Codespace</b> (Docker incluido), no en tu equipo.</li>'
          '<li>Puedes abrir el mismo Codespace desde cualquiera de los dos, y desde la línea de comandos con GitHub CLI.</li></ul></div></div>'
          '<div class="card ok" style="margin-top:14px"><h3>Cuál elegir</h3><p style="font-size:17px">Para S2 sirve cualquiera: <b>los comandos y la cuota son los mismos</b>. '
          'Si ya trabajas con VS Code (S0 lo instaló con sus extensiones), conectarlo te ahorra aprender otra interfaz. Si tu equipo no te deja instalar extensiones, usa el navegador.</p>'
          f'<p class="small" style="margin-top:6px">{val_html("docs")}</p></div>',
          '**VS Code en el navegador.** Es lo que se abre por defecto al crear un Codespace en GitHub. No instalas nada. Se reabre desde `github.com/codespaces`.\n\n'
          '**VS Code de escritorio.** Tu VS Code conectado al Codespace; requiere VS Code 1.51 o posterior y la extensión **GitHub Codespaces**. El código sigue ejecutándose en el Codespace (Docker incluido).\n\n'
          'Para S2 sirve cualquiera: los comandos y la cuota son los mismos. Puedes abrir el mismo Codespace desde cualquiera de los dos.')

    # ---- 10. conectar desde VS Code de escritorio
    paso('vscode', 'B · Abrir el Codespace', '3 de 8 · opcional', 'Conectar desde tu VS Code de escritorio', 'VS Code (instalado en tu equipo)',
         'Una sola vez: instalar la extensión e iniciar sesión. Después, cada Codespace aparece en una lista.',
         ui=['Extensiones (<b>Ctrl+Shift+X</b>) → busca e instala <b>GitHub Codespaces</b> (<code>GitHub.codespaces</code>).',
             'Pulsa el icono <b>Remote Explorer</b> de la barra de actividades e inicia sesión con GitHub: pulsa <b>Authorize</b> cuando se pida (y, si el navegador lo muestra, <i>Authorize Visual-Studio-Code</i>).',
             'En la lista aparecen tus Codespaces: sitúate sobre el del curso y pulsa el icono del enchufe (<i>Connect to Codespace</i>).',
             'Alternativa, desde <code>github.com/codespaces</code>: menú <b>⋯</b> del Codespace → abrir en <b>Visual Studio Code</b>.'],
         cmds=[dict(c='gh codespace code', nota='Opcional: si ya tienes GitHub CLI (gh) con sesión iniciada, abre el Codespace que elijas en tu VS Code.')],
         terminal_titulo='Terminal de tu equipo (opcional)',
         esperado='VS Code se reabre <b>conectado</b>: el Explorador muestra las carpetas del repositorio y la terminal integrada es la del Codespace (la ruta empieza por <code>/workspaces/</code>). '
                  'Todo lo demás de la guía es igual.',
         si_falla=['No aparece ningún Codespace: inicia sesión con <b>la misma cuenta</b> con la que lo creaste.',
                   'La extensión no se instala o VS Code es anterior a la 1.51: actualiza VS Code o trabaja en el navegador.',
                   'Equipo corporativo sin permiso para extensiones: usa el navegador, que no necesita nada.'],
         val='docs')

    # ---- 11. qué haremos dentro
    libre('Qué haremos dentro', 'C · Laboratorio de S2', 'C · Laboratorio de S2 · bloque 4 · 25 min', 'Qué haremos dentro del Codespace',
          '<div class="cols" style="grid-template-columns:1.1fr .9fr"><div class="card"><ol class="ui">'
          '<li><span><b>Comprobar Docker</b> (<code>docker version</code>): Client y Server.</span></li>'
          '<li><span><b>Entrenar</b> el modelo (<code>python -m ia_mlops.pipeline</code>): la imagen necesita <code>models/</code>.</span></li>'
          '<li><span><b>Construir la imagen</b> <code>retencion-api:local</code> con el Dockerfile del proyecto.</span></li>'
          '<li><span><b>Arrancar el contenedor</b> y preguntarle a <code>/listo</code>.</span></li>'
          '<li><span><b>Comparar</b> las predicciones del contenedor con las del paquete, joblib y MLflow.</span></li>'
          '<li><span><b>Inspeccionar</b>: registros (<code>docker logs</code>) y usuario (<code>id -u</code>, no root).</span></li>'
          '<li><span><b>Limpiar</b>: borrar el contenedor.</span></li></ol></div>'
          '<div class="side"><div class="card ok"><h3>Preguntas para pensar</h3><ul class="p s">'
          '<li>¿Cuánto ocupa la imagen?</li>'
          '<li>Si cambias una línea de <code>ia_mlops/</code> y vuelves a construir, ¿qué capas se reutilizan?</li>'
          '<li>¿Por qué el contenedor escucha en <code>0.0.0.0</code> y no en <code>127.0.0.1</code>?</li></ul></div>'
          f'<div class="card"><p class="small" style="font-size:14.5px">Es el bloque 4 de la guía de laboratorio de S2. Las diapositivas «Así se ve» son capturas del Codespace real ({FECHA_PRUEBA}); '
          'las salidas en texto de los pasos son las de Linux (las mismas cifras).</p></div></div></div>',
          '1. **Comprobar Docker** (`docker version`): Client y Server.\n2. **Entrenar** el modelo (`python -m ia_mlops.pipeline`): la imagen necesita `models/`.\n'
          '3. **Construir la imagen** `retencion-api:local` con el Dockerfile del proyecto.\n4. **Arrancar el contenedor** y preguntarle a `/listo`.\n'
          '5. **Comparar** las predicciones del contenedor con las del paquete, joblib y MLflow.\n6. **Inspeccionar**: registros (`docker logs`) y usuario (`id -u`, no root).\n7. **Limpiar**: borrar el contenedor.\n\n'
          '**Preguntas para pensar:** ¿cuánto ocupa la imagen? Si cambias una línea de `ia_mlops/` y vuelves a construir, ¿qué capas se reutilizan? ¿Por qué el contenedor escucha en `0.0.0.0` y no en `127.0.0.1`?')

    # ---- 12. entrenar
    paso('pipeline', 'C · Laboratorio de S2', '4 de 8', 'Entrenar el modelo en el Codespace', 'la terminal del Codespace, en 04-Proyecto-Base',
         'La imagen copia <code>models/modelo_mlflow/</code>, y esa carpeta no viaja con el repositorio: se genera. Por eso se entrena aquí antes de construir.',
         cmds=[dict(c=CMD_PIPELINE)],
         esperado='Termina sin error y deja en <code>models/</code> el modelo (<code>modelo_mlflow/</code>, <code>modelo.joblib</code>) y <code>metadatos.json</code>. '
                  f'En el Codespace tardó {t["pipeline"]} s. Últimas líneas:',
         real=[pipeline_fin],
         real_nota='Salida real en Linux (' + S['meta']['fecha'] + '), ruta recortada (…); en el Codespace, el mismo modelo. Los avisos WARNING de MLflow son normales.',
         si_falla=['<code>ModuleNotFoundError</code>: la terminal no está en el entorno del curso. <code>conda activate env-ia-mlops</code> y repite.',
                   '<code>No module named ia_mlops</code>: no estás en <code>04-Proyecto-Base</code> (<code>pwd</code>).'],
         val='probado', dividir=False,
         capturas=[[('07-pipeline', f'Final del pipeline en el Codespace: «Mejor modelo: regresion_logistica», en unos {t["pipeline"]} s.')]])

    # ---- 13. construir la imagen
    paso('build', 'C · Laboratorio de S2', '5 de 8', 'Construir la imagen', 'la terminal del Codespace, en 04-Proyecto-Base',
         'Docker lee el Dockerfile y crea la imagen <code>retencion-api:local</code>: Python 3.11, las dependencias fijadas, el paquete y el modelo, sin root.',
         cmds=[dict(c=CMD_BUILD), dict(c=CMD_LS)],
         esperado=f'El build termina con <code>FINISHED</code> (la primera vez, {t["docker_build_primera_vez"]} s en el Codespace; si repites, las capas sin cambios salen de la caché). '
                  f'<code>docker image ls</code> lista <code>retencion-api:local</code>: con Docker 29 las columnas son <b>DISK USAGE</b> ({CS["imagen"]["disk_usage"]}, lo que ocupa en disco, igual que en GitHub Actions) '
                  f'y <b>CONTENT SIZE</b> ({CS["imagen"]["content_size"]}, comprimida).',
         si_falla=['<code>COPY failed … models/modelo_mlflow</code>: falta entrenar. Ejecuta antes <code>python -m ia_mlops.pipeline</code>.',
                   '<code>docker: command not found</code> o no conecta con el daemon: vuelve a «Orientarte y comprobar Docker».',
                   'Un error al descargar la imagen base: repite; si persiste, anótalo y usa el bloque 5 (Actions).'],
         val='probado',
         capturas=[[('08-docker-build', 'docker build en el Codespace: 14 pasos FINISHED; la instalación de dependencias (paso 4/8) es lo que más tarda.')],
                   [('09-image-ls', f'docker image ls retencion-api:local: DISK USAGE {CS["imagen"]["disk_usage"]} · CONTENT SIZE {CS["imagen"]["content_size"]}.')]])

    # ---- 14. arrancar y probar
    paso('run', 'C · Laboratorio de S2', '6 de 8', 'Arrancar el contenedor y comparar', 'la terminal del Codespace, en 04-Proyecto-Base',
         '<code>-p 8080:8080</code> publica el puerto del contenedor en el Codespace. <code>-d</code> lo deja en segundo plano.',
         cmds=[dict(c=CMD_RUN), dict(c=CMD_LISTO, nota='Si da «Connection reset by peer» justo después del run, espera unos segundos y repite.'), dict(c=CMD_COMPARAR)],
         esperado=f'<code>curl</code> responde <code>{esc(listo)}</code>. La comparación termina con «Todos los caminos dan la misma probabilidad», y la última fila es <b>la API</b> (el contenedor):',
         real=[comparar],
         real_nota='Salida real en Linux con la API sin contenedor; en el Codespace, contra el contenedor, dio lo mismo (captura). Según la versión de MLflow puede aparecer antes una línea INFO: es informativa.',
         si_falla=['<code>port is already allocated</code> o <code>container name "/api" is already in use</code>: <code>docker rm -f api</code> y repite.',
                   '<code>/listo</code> da 503: lee el campo <code>detalle</code> (falta el modelo o el esquema no coincide).',
                   'La comparación dice <code>No se pudo comparar</code>: falta el modelo o la base; ejecuta el pipeline.'],
         val='probado', dividir=True,
         capturas=[[('10-run-listo', 'Justo después del run, el primer curl da «Connection reset by peer»; seis segundos después, {"estado":"listo"}.'),
                    ('13-comparar', f'comparar contra el contenedor: los cuatro caminos coinciden (diferencia 0), en {t["comparar"]} s.')]])

    # ---- 15. ver la API en el navegador
    paso('puertos', 'C · Laboratorio de S2', '7 de 8 · opcional', 'Ver la API en el navegador (puertos)', 'el Codespace, panel PORTS',
         'Con <code>curl</code> no necesitas esto: <code>127.0.0.1:8080</code> ya es el Codespace. Los puertos sirven para abrir <code>/docs</code> en tu navegador.',
         ui=['Abre el panel <b>Puertos</b> (<i>PORTS</i>), junto a la terminal. Con el contenedor en marcha lista el <b>8080</b> como «API ia-mlops (S2)» con un punto verde.',
             'Si no aparece: <b>Agregar puerto</b> (<i>Add port</i>) → <code>8080</code>.',
             'Abre la dirección reenviada (<code>https://&lt;tu-codespace&gt;-8080.app.github.dev</code>; icono del globo o clic derecho → abrir en el navegador) y añade <code>/docs</code>.',
             'Verás la página interactiva de la API: prueba <code>/salud</code>, <code>/listo</code>, <code>/modelo</code> y <code>/predecir</code>.'],
         esperado='La página de documentación de la API, servida <b>desde el contenedor</b>. La visibilidad del puerto debe ser <b>privada</b> (columna «Visibilidad»: <i>Private</i>): solo tu cuenta de GitHub puede abrirla. '
                  'Cada visita aparece después en <code>docker logs api</code>.',
         si_falla=['No carga: comprueba que el contenedor sigue vivo (<code>docker ps</code>) y que el puerto es el 8080.',
                   '<b>No pongas el puerto en «Public»</b>: cualquiera con la dirección llegaría a la API, que no tiene autenticación.'],
         val='probado',
         capturas=[[('11-puertos', 'Panel Puertos: el 8080 «API ia-mlops (S2)» reenviado y privado; el 5000 es el de MLflow.')],
                   [('12-api-docs', 'La dirección reenviada + /docs: la documentación interactiva de la API del contenedor.')]])

    # ---- 16. inspeccionar y limpiar
    paso('limpiar', 'C · Laboratorio de S2', '8 de 8', 'Inspeccionar el contenedor y limpiar', 'la terminal del Codespace',
         'Los registros salen por la salida estándar del contenedor; el usuario demuestra que no corre como root.',
         cmds=[dict(c=CMD_LOGS), dict(c=CMD_ID), dict(c=CMD_RM)],
         esperado='<code>docker logs</code>: una línea JSON por petición (método, ruta, código, milisegundos e id). <code>id -u</code> imprime <b>10001</b>, no 0. '
                  '<code>docker rm -f api</code> escribe <code>api</code> y libera el nombre y el puerto.',
         si_falla=['<code>container … is not running</code>: el contenedor murió. <code>docker logs api</code> dice por qué (p. ej., sin modelo).',
                   'Si quieres repetir desde cero: <code>docker rm -f api</code> y vuelve a «Arrancar el contenedor».',
                   'Para la tarea, pega estas salidas en la plantilla de evidencias de S2.'],
         val='probado',
         capturas=[[('14-logs', 'docker logs api: una línea JSON por petición, con su id; aparecen también las visitas a /docs desde el navegador.')],
                   [('15-id-rm', f'docker exec api id -u → {CS["id_u"]} (no es root); docker rm -f api → api.')]])

    # ---- 17. guardar el trabajo
    libre('Guardar tu trabajo', 'D · Cuidarlo', 'D · Cuidarlo', 'Guardar tu trabajo: el Codespace es temporal',
          '<div class="two"><div class="card"><h3>En S2, bloque 4</h3><p style="font-size:16px">No hay nada que guardar: son comandos que se ejecutan y se miran. '
          'Lo que sí te llevas son las <b>salidas</b>: cópialas a la plantilla de evidencias (<code>01-Sesiones/S2-API-y-Docker/evidencias/</code>).</p>'
          '<h3 style="margin-top:12px">Si cambias archivos</h3><ul class="p s">'
          '<li>El repositorio del curso es de solo lectura para ti. Al hacer tu <b>primer commit o push</b>, GitHub crea un <b>fork</b> en tu cuenta y enlaza el Codespace a él.</li>'
          '<li>Si borras ese fork, se borran los Codespaces enlazados.</li></ul></div>'
          '<div class="card"><h3>Si no puedes abrirlo</h3><ul class="p s">'
          '<li>Por ejemplo, porque se agotó la cuota: en <code>github.com/codespaces</code>, menú <b>⋯</b> del Codespace → <b>Export changes to a branch</b>. Sube tus cambios a una rama (o a un fork) sin abrirlo.</li></ul>'
          '<h3 style="margin-top:12px">Hábitos</h3><ul class="p s">'
          '<li>Activa <b>Auto Save</b> en VS Code.</li>'
          '<li>Haz commit y push de lo que importe <b>antes de borrar</b> el Codespace.</li>'
          '<li>Nunca guardes contraseñas ni tokens en el Codespace.</li></ul>'
          f'<p class="small" style="margin-top:8px">{val_html("docs")}</p></div></div>',
          'En S2, bloque 4, no hay nada que guardar: lo que te llevas son las salidas, que copias a la plantilla de evidencias (`01-Sesiones/S2-API-y-Docker/evidencias/`).\n\n'
          '- El repositorio del curso es de solo lectura para ti: al hacer tu primer commit o push, GitHub crea un **fork** en tu cuenta y enlaza el Codespace a él. Si borras ese fork, se borran los Codespaces enlazados.\n'
          '- Si no puedes abrir el Codespace (por ejemplo, cuota agotada): en `github.com/codespaces`, menú ⋯ del Codespace → **Export changes to a branch**.\n'
          '- Activa Auto Save, haz commit y push de lo que importe antes de borrar el Codespace y nunca guardes contraseñas ni tokens en él.')

    # ---- 18. cuidar la cuota
    libre('Cuidar tu cuota', 'D · Cuidarlo', 'D · Cuidarlo', 'Parar y borrar: cuida tu cuota',
          '<div class="three"><div class="card"><h3>1 · Párarlo</h3><ul class="p s">'
          '<li><b>Cerrar la pestaña no lo para</b>: sigue gastando hasta agotar el tiempo de inactividad.</li>'
          '<li>Paleta de comandos (<b>F1</b>) → <b>Codespaces: Stop</b>, o <code>gh codespace stop</code>, o ⋯ → Stop en <code>github.com/codespaces</code>.</li></ul></div>'
          '<div class="card"><h3>2 · Se para solo</h3><ul class="p s">'
          '<li>Sin actividad, se para a los <b>30 minutos</b> (por defecto).</li>'
          '<li>Lo puedes cambiar entre 5 minutos y 4 horas en <i>Settings → Codespaces → Default idle timeout</i> de tu cuenta de GitHub.</li>'
          '<li>Un tiempo corto ahorra cuota.</li></ul></div>'
          '<div class="card"><h3>3 · Bórralo</h3><ul class="p s">'
          '<li>Parado y sin usar, <b>se borra solo a los 30 días</b> (puedes fijar de 0 a 30).</li>'
          '<li><b>Con 0 se borra en cuanto se para</b>: pierdes lo no guardado.</li>'
          '<li>Cuando termines una práctica: ⋯ → <b>Delete</b> en <code>github.com/codespaces</code>.</li></ul></div></div>'
          '<div class="card warn" style="margin-top:14px"><p style="font-size:16px"><b>Recuerda:</b> el disco cuenta mientras el Codespace exista, aunque esté parado, y borrarlo no devuelve el disco que ya contó este mes. '
          f'Si se te olvida, el borrado automático lo recoge.</p><p class="small" style="margin-top:6px">{val_html("cifras")}</p></div>',
          '1. **Páralo.** Cerrar la pestaña no lo para: sigue gastando hasta agotar el tiempo de inactividad. Paleta de comandos (F1) → *Codespaces: Stop*, o `gh codespace stop`, o ⋯ → Stop en `github.com/codespaces`.\n'
          '2. **Se para solo.** Sin actividad, a los 30 minutos (por defecto); configurable de 5 minutos a 4 horas en *Settings → Codespaces → Default idle timeout*.\n'
          '3. **Bórralo.** Parado y sin usar se borra solo a los 30 días (configurable de 0 a 30; con 0 se borra en cuanto se para y pierdes lo no guardado). Al terminar una práctica: ⋯ → Delete en `github.com/codespaces`.\n\n'
          f'El disco cuenta mientras el Codespace exista, aunque esté parado, y borrarlo no devuelve el disco que ya contó este mes. *Cifras leídas en la documentación de GitHub el {FECHA}.*')

    # ---- 18b. parar desde la web (capturas)
    libre('Parar desde la web', 'D · Cuidarlo', 'D · Cuidarlo · así se ve', 'Parar (o borrar) desde github.com/codespaces',
          '<div class="shots">'
          + captura('16-menu-codespace', 'Menú ⋯ del Codespace: Stop codespace, Export changes to a branch, abrir en el navegador o en VS Code… (Delete está más abajo).', alto=330)
          + captura('17-parado', '«Codespace … stopped»: ya no gasta cómputo; su disco sigue contando hasta que lo borres.', alto=330)
          + f'</div><p class="small" style="margin-top:10px">{val_html("probado")} · Fíjate en <b>develop*</b> y «uncommitted changes»: el Codespace guarda tus cambios sin confirmar mientras exista.</p>',
          'En `github.com/codespaces`, menú ⋯ del Codespace: **Stop codespace**, **Export changes to a branch**, abrir en el navegador o en VS Code… (Delete está más abajo). '
          'Al pararlo aparece «Codespace … stopped»: ya no gasta cómputo, pero su disco sigue contando hasta que lo borres.\n\n'
          + captura_md('16-menu-codespace', 'Menú del Codespace en github.com/codespaces') + '\n\n' + captura_md('17-parado', 'Codespace parado'))

    # ---- 19. si algo falla
    fallos = [
        ('«This codespace is currently running in recovery mode…»', 'El contenedor no se pudo construir con la configuración.', '<b>View creation log</b> y anota el error; avisa al instructor. Tras corregirlo: <b>F1 → Codespaces: Rebuild Container</b>.'),
        ('«¿Confía en los autores de los archivos de esta carpeta?»', 'VS Code abre las carpetas nuevas en modo restringido.', 'Es el repositorio del curso: <b>Confiar en la carpeta y continuar</b>.'),
        ('El indicador dice <code>(base)</code>', 'La terminal no está en el entorno del curso.', '<code>conda activate env-ia-mlops</code>'),
        ('«Maximum running codespaces reached»', 'Tienes otro Codespace encendido.', 'Páralo en <code>github.com/codespaces</code> (⋯ → Stop codespace).'),
        ('<code>docker: command not found</code> / <code>Cannot connect to the Docker daemon</code>', 'Docker no está disponible o no ha arrancado.', 'Repite al cabo de un minuto; <i>Rebuild Container</i>; si no, bloque 5 (Actions).'),
        ('<code>COPY failed … models/modelo_mlflow</code>', 'Falta entrenar.', '<code>python -m ia_mlops.pipeline</code> y vuelve a construir.'),
        ('<code>Connection reset by peer</code> justo tras <code>docker run</code>', 'La API aún está arrancando.', 'Espera unos segundos y repite el <code>curl</code>.'),
        ('<code>port is already allocated</code> / <code>name "/api" is already in use</code>', 'Queda un contenedor anterior.', '<code>docker rm -f api</code>'),
        ('El Codespace aparece parado o la pestaña pide reconectar', 'Se agotó el tiempo de inactividad.', 'Reábrelo desde <code>github.com/codespaces</code>; si no lo has borrado, sigue ahí.'),
        ('No te deja crear uno', 'Cuota agotada, cuenta de organización o política.', 'Revisa tu uso; trabaja en pareja o usa el CI (bloque 5).'),
    ]
    libre('Si algo falla', 'D · Cuidarlo', 'D · Cuidarlo', 'Si algo falla',
          '<div class="card"><table class="dens"><tr><th>Lo que ves</th><th>Causa</th><th>Qué hacer</th></tr>' + ''.join(f'<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>' for a, b, c in fallos) + '</table></div>'
          '<p class="small" style="margin-top:10px">Siempre: copia el mensaje <b>completo</b> como texto y envíalo con el comando que ejecutaste. Nunca envíes contraseñas, tokens ni capturas con tu sesión abierta.</p>',
          '| Lo que ves | Causa | Qué hacer |\n|---|---|---|\n' + '\n'.join(f'| {md(a)} | {md(b)} | {md(c)} |' for a, b, c in fallos) +
          '\n\nSiempre: copia el mensaje completo como texto y envíalo con el comando que ejecutaste. Nunca envíes contraseñas, tokens ni capturas con tu sesión abierta.')

    # ---- 19b. el modo recuperación, visto
    libre('Así se ve el modo recuperación', 'D · Cuidarlo', 'D · Cuidarlo · así se ve', 'Así se ve el modo recuperación',
          '<div class="cols" style="grid-template-columns:1.2fr .8fr">'
          + captura('05-modo-recuperacion', 'El aviso y la terminal en modo recuperación: el contenedor del curso no se construyó.', alto=420)
          + '<div class="side"><div class="card"><p style="font-size:15.5px">Le pasó al propio curso la primera vez que se abrió (12/11/2026): la imagen base había cambiado y la '
          'configuración de Docker ya no servía. <b>Ya está corregido.</b></p></div>'
          '<div class="card ok"><h3>Qué haces tú</h3><ul class="p s"><li><b>View Creation Log</b> y copia las líneas con <code>ERROR</code>.</li>'
          '<li>Envíaselas al instructor con la hora.</li><li>Mientras tanto, plan B: el bloque 5 (GitHub Actions) construye la imagen por ti.</li></ul></div></div></div>',
          'Le pasó al propio curso la primera vez que se abrió (12/11/2026): la imagen base había cambiado y la configuración de Docker ya no servía. Ya está corregido. '
          'Si te ocurre: **View Creation Log**, copia las líneas con `ERROR` y envíaselas al instructor; mientras tanto, el bloque 5 (GitHub Actions) construye la imagen por ti.\n\n'
          + captura_md('05-modo-recuperacion', 'Modo recuperación'))

    # ---- 20. más allá y plan B
    libre('Más allá de S2 y plan B', 'E · Cierre', 'E · Cierre', 'Más allá de S2 y qué hacer si no puedes usarlo',
          '<div class="two"><div class="card"><h3>S3: Kubernetes (pendiente)</h3><p style="font-size:16px">El programa prevé, <b>si hay tiempo</b>, un laboratorio acotado de Kubernetes en el Codespace. '
          f'<b>Las herramientas ya vienen</b>: <code>kind</code> {CS["versiones"]["kind"]} y <code>kubectl</code> {CS["versiones"]["kubectl"]} (comprobadas el {FECHA_PRUEBA}). El laboratorio está por escribir y probar; no hay nada que preparar todavía.</p></div>'
          '<div class="card"><h3>Si no puedes usar Codespaces</h3><ul class="p s">'
          '<li><b>GitHub Actions</b> (bloque 5 de S2): el workflow construye la imagen y prueba el contenedor. Es el plan B principal y se verificó.</li>'
          '<li><b>En pareja</b>: se comparte un Codespace y se rotan las manos.</li>'
          '<li><b>Cloud Shell</b> de Google Cloud, como respaldo (por verificar).</li>'
          '<li><b>Docker Desktop</b> en tu equipo: opcional, no se exige.</li></ul></div></div>'
          '<div class="card ok" style="margin-top:14px"><p style="font-size:16.5px">Lo importante de S2 no es el lugar donde corre Docker, sino entender <b>qué hay dentro de la imagen y por qué el contenedor se comporta igual en cualquier sitio</b>. '
          'Si el Codespace falla, no pierdes el objetivo.</p></div>',
          f'**S3 (pendiente).** El programa prevé, si hay tiempo, un laboratorio acotado de Kubernetes en el Codespace. Las herramientas ya vienen: `kind` {CS["versiones"]["kind"]} y `kubectl` {CS["versiones"]["kubectl"]} (comprobadas el {FECHA_PRUEBA}). El laboratorio está por escribir y probar.\n\n'
          '**Si no puedes usar Codespaces:** GitHub Actions (bloque 5 de S2: el workflow construye la imagen y prueba el contenedor; se verificó), trabajar en pareja, Cloud Shell de Google Cloud como respaldo (por verificar) o Docker Desktop en tu equipo (opcional).')

    # ---- 21. verificado / sin probar
    libre('Qué está verificado', 'E · Cierre', 'E · Cierre · transparencia', 'Qué se verificó y qué no',
          '<div class="two"><div class="card ok"><h3>Verificado</h3><ul class="p s">'
          f'<li><b>Un Codespace real del curso</b> ({FECHA_PRUEBA}, 2 núcleos, rama <code>develop</code>): creación y conexión, <code>verificar.sh</code> sin fallos, el <b>bloque 4 entero</b> '
          f'(pipeline {t["pipeline"]} s, build {t["docker_build_primera_vez"]} s, <code>/listo</code>, comparación, logs, <code>id -u</code> = {CS["id_u"]}), el panel Puertos con <code>/docs</code>, '
          'el diálogo de confianza, el modo recuperación y parar desde la web.</li>'
          '<li><b>GitHub Actions</b>: <code>docker build</code> con el Dockerfile (826 MB), <code>docker run</code>, <code>/listo</code>, <code>/modelo</code>, predicción, 422 al enviar <code>y</code> y usuario no root.</li>'
          f'<li><b>Linux</b>: pipeline ({round(sal["pipeline"]["segundos"])} s con la muestra), API, <code>curl /listo</code> y la comparación entre caminos (las salidas en texto de esta guía).</li></ul></div>'
          '<div class="card bad"><h3 style="color:var(--bad)">Sin probar</h3><ul class="p s">'
          '<li>La conexión desde <b>VS Code de escritorio</b> (paso 3).</li>'
          f'<li>Las <b>cuotas</b> y los tiempos de inactividad y retención: salen de la documentación de GitHub ({FECHA}).</li>'
          '<li>Una cuenta de <b>estudiante</b> (región de EE. UU., cuota propia) y <b>Export changes to a branch</b>.</li>'
          '<li>Cloud Shell como respaldo y el laboratorio de Kubernetes de S3.</li></ul></div></div>'
          '<p class="small" style="margin-top:12px">Si ves algo distinto de lo que muestra esta guía, es información valiosa: envía el comando y el mensaje exacto.</p>',
          f'**Verificado.**\n- Un Codespace real del curso ({FECHA_PRUEBA}, 2 núcleos, rama `develop`): creación y conexión, `verificar.sh` sin fallos, el bloque 4 entero '
          f'(pipeline {t["pipeline"]} s, build {t["docker_build_primera_vez"]} s, `/listo`, comparación, logs, `id -u` = {CS["id_u"]}), el panel Puertos con `/docs`, el diálogo de confianza, '
          'el modo recuperación y parar desde la web.\n'
          '- GitHub Actions: `docker build` con el Dockerfile (826 MB), `docker run`, `/listo`, `/modelo`, predicción, 422 al enviar `y` y usuario no root.\n'
          f'- Linux: pipeline ({round(sal["pipeline"]["segundos"])} s con la muestra), API, `curl /listo` y la comparación entre caminos (las salidas en texto de esta guía).\n\n'
          '**Sin probar.**\n- La conexión desde VS Code de escritorio (paso 3).\n'
          f'- Las cuotas y los tiempos de inactividad y retención: salen de la documentación de GitHub ({FECHA}).\n'
          '- Una cuenta de estudiante (región de EE. UU., cuota propia) y Export changes to a branch.\n'
          '- Cloud Shell como respaldo y el laboratorio de Kubernetes de S3.\n\nSi ves algo distinto de lo que muestra esta guía, envía el comando y el mensaje exacto.')

    # ---- 22. fuentes
    li = ''.join(f'<li>{esc(t)}<a href="{esc(u)}" target="_blank" rel="noopener">{esc(u)}</a></li>' for t, u in FUENTES)
    libre('Fuentes', 'E · Cierre', 'E · Cierre', 'Fuentes',
          f'<ul class="src">{li}</ul><p class="small" style="margin-top:6px">Consultadas el {FECHA}. Las cuotas y los precios cambian: compruébalos en tu cuenta antes de la clase.</p>',
          '\n'.join(f'- {t}: <{u}>' for t, u in FUENTES) + f'\n\nConsultadas el {FECHA}. Las cuotas y los precios cambian: compruébalos en tu cuenta antes de la clase.')

    # ---- 23. lista final
    final = [
        ('Mi cuenta de GitHub es personal y sé cuánta cuota me queda.', 'cuota'),
        ('He abierto el Codespace del curso (rama <code>develop</code>) y <code>docker version</code> muestra <b>Client</b> y <b>Server</b>.', 'paso 2'),
        ('He entrenado con <code>python -m ia_mlops.pipeline</code> y he construido la imagen (o sé que usaré el CI).', 'bloque 4'),
        ('El contenedor responde en <code>/listo</code> y <code>id -u</code> da 10001.', 'bloque 4'),
        ('Sé parar el Codespace y borrarlo, y he revisado el tiempo de inactividad.', 'cuota'),
    ]
    items = ''.join(f'<label><input type="checkbox" data-k="f{i}"><span>{t}</span><span class="ref">{r}</span></label>' for i, (t, r) in enumerate(final))
    libre('Listo para S2', 'E · Cierre', 'Final', 'Listo para el bloque Docker de S2 cuando…',
          f'<div class="check">{items}</div><p class="small" style="margin-top:12px" id="cuenta">0 de {len({d["id"] for d in DIAS if d["id"]})} pasos marcados como hechos en este navegador</p>'
          '<p class="small" style="margin-top:4px">Las marcas se guardan solo en este navegador. Lo ideal es abrir el Codespace <b>antes de la clase</b>: así, si algo falla, lo sabemos con tiempo.</p>',
          '\n'.join(f'- [ ] {md(t)}' for t, _ in final) + '\n\nLo ideal es abrir el Codespace antes de la clase: así, si algo falla, lo sabemos con tiempo.')


# ================================================================== ensamblado
def construir_html():
    DIAS.clear()
    construir_contenido()
    secciones = []
    for d in DIAS:
        attrs = f' data-title="{esc(d["titulo"])}" data-bloque="{esc(d["bloque"])}"' + (f' data-id="{d["id"]}"' if d['id'] else '')
        secciones.append(f'<section class="slide"{attrs}>{d["html"]}<div class="foot"><span>{esc(TITULO)}</span><span>{esc(d["pie"])}</span></div></section>')
    cuerpo = '\n'.join(secciones)
    return (f'<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>{esc(TITULO)} · ML e IA: de desarrollo a producción</title>\n<style>{CSS}</style>\n</head>\n<body>\n'
            f'<div id="viewport"><div id="stage">\n{cuerpo}\n</div></div>\n<div id="prog"></div>\n'
            '<div id="index" aria-label="Índice"><h2>Índice</h2><div id="idxgrid"></div></div>\n'
            '<nav id="bar" aria-label="Controles"><button id="bprev" aria-label="Anterior">←</button><button id="bnext" aria-label="Siguiente">→</button>'
            '<span id="count">1</span><span class="sp"></span><a id="bhome" href="../../01-Sesiones/S2-API-y-Docker/index.html" title="Volver al índice de la sesión S2">⌂ <span class="tx">Índice de </span>S2</a>'
            '<button id="bidx">Índice (O)</button><button id="bfull">Pantalla completa (F)</button></nav>\n'
            '<noscript>Esta presentación necesita JavaScript. El contenido completo está en 03-Entorno/guias/codespaces-para-el-alumnado.md.</noscript>\n'
            f'<script>{JS}</script>\n</body>\n</html>\n')


def construir_md():
    DIAS.clear()
    construir_contenido()
    partes = [DIAS[0]['md']]
    bloque = None
    for d in DIAS[1:]:
        if not d['md']:
            continue
        if d['bloque'] != bloque:
            bloque = d['bloque']
            partes.append(f'\n# {bloque}\n')
        partes.append(d['md'] + '\n')
    pie = ('\n---\n*Este archivo lo genera `03-Entorno/guia-codespaces/generar.py`; no lo edites a mano.*\n')
    return '\n'.join(partes) + pie


def main():
    SALIDA_HTML.write_text(construir_html(), encoding='utf-8')
    SALIDA_MD.write_text(construir_md(), encoding='utf-8')
    print(f'{SALIDA_HTML.relative_to(RAIZ)}: {SALIDA_HTML.stat().st_size} bytes · {len(DIAS)} diapositivas')
    print(f'{SALIDA_MD.relative_to(RAIZ)}: {SALIDA_MD.stat().st_size} bytes')


if __name__ == '__main__':
    main()
