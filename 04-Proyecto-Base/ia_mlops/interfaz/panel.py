"""Panel de producción (GET /panel): cuatro pestañas para ver, de punta a punta, qué hay en producción.

  Lote          la última campaña (reports/campana/ o CURSO_CAMPANA): corte, clientes, campaña, versión del modelo, 20 primeros, descarga
  Bajo demanda  variables leídas de fs_produccion (las de ayer) -> probabilidad
  Online        variables calculadas ahora; con el modo demo, «Simular una compra nueva» y la comparación con bajo demanda y lote
  Versiones     la versión en producción (models/referencia.json) frente al modelo que sirve ahora, y el historial si existe

Endpoints auxiliares (JSON; el resto de datos salen de /bajo-demanda, /online, /modos y /demo/*):
  GET /panel/lote                  resumen de la última campaña y sus 20 primeros clientes   ({"disponible": false, ...} si no hay)
  GET /panel/lote/cliente/{id}     la fila de ese cliente en la última campaña (404 si no está o no hay campaña)
  GET /panel/lote.csv              descarga el CSV de la última campaña
  GET /panel/versiones             versión en producción, modelo que sirve ahora, aviso si no coinciden e historial

La página es un solo HTML sin recursos externos.
"""
import json
import os
from pathlib import Path

import pandas as pd
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from .. import config, produccion
from .consulta import segmento_de

PRIMEROS = 20
HISTORIAL = 'historial_versiones.json'      # models/historial_versiones.json (opcional): lista de versiones o {"versiones": [...]}

FLUJO_NUEVA_VERSION = ['Entrenar', 'Comparar con la versión en producción', 'Aprobar', 'Publicar la imagen', 'Pull request con la nueva referencia']


# ------------------------------------------------------------------------------------------------------------------ datos
def _carpeta_campana():
    return Path(os.environ.get('CURSO_CAMPANA') or (Path(config.REPORTES) / 'campana'))


def ultima_campana():
    """(ruta_csv, ruta_json) de la campaña más reciente (por el corte del nombre), o None. CURSO_CAMPANA: carpeta o un archivo campana_<corte>.*"""
    origen = _carpeta_campana()
    if origen.is_file():
        csv = origen.with_suffix('.csv')
        return (csv, origen.with_suffix('.json')) if csv.exists() else None
    if not origen.is_dir():
        return None
    csvs = sorted(origen.glob('campana_*.csv'), key=lambda p: p.stem)      # AAAA-MM-DD ordena como texto
    if not csvs:
        return None
    return csvs[-1], csvs[-1].with_suffix('.json')


def _limpio(v):
    """Valores aptos para JSON (sin NaN)."""
    if isinstance(v, float) and v != v:
        return None
    return v.item() if hasattr(v, 'item') else v


def datos_lote():
    ruta = ultima_campana()
    if ruta is None:
        return {'disponible': False, 'mensaje': 'Todavía no hay campaña: ejecuta el lote (python -m ia_mlops.explotacion).'}
    csv, js = ruta
    resumen = {}
    if js.exists():
        try:
            resumen = json.loads(js.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            resumen = {}
    tabla = pd.read_csv(csv)
    primeros = [{k: _limpio(v) for k, v in fila.items()} for fila in tabla.head(PRIMEROS).to_dict('records')]
    resumen = {k: v for k, v in resumen.items() if k != 'archivos'}        # nada de rutas de quien lo ejecutó
    return {'disponible': True, 'archivo': csv.name, 'resumen': resumen, 'primeros': primeros, 'filas': int(len(tabla))}


def datos_versiones(consulta):
    try:
        ref = produccion.leer_referencia()
        error_ref = None
    except produccion.ErrorReferencia as e:
        ref, error_ref = None, str(e).replace(str(config.RAIZ), '.')
    try:
        sirve = {**consulta.info_modelo(), 'origen': consulta.origen}
        error_sirve = None
    except Exception as e:                          # sin modelo o API caída: el panel lo cuenta, no se rompe
        sirve, error_sirve = None, str(e)
    aviso = None
    if ref and sirve:
        if ref['huella_datos'] != sirve['huella_datos']:
            aviso = (f'El modelo que sirve ahora (huella {sirve["huella_datos"]}) no es el de la versión en producción '
                     f'(huella {ref["huella_datos"]}, v{ref["version"]}).')
    elif ref and not sirve:
        aviso = 'No se puede comprobar qué modelo sirve ahora.'
    historial = None
    ruta = Path(config.MODELOS) / HISTORIAL
    if ruta.exists():
        try:
            h = json.loads(ruta.read_text(encoding='utf-8'))
            historial = h.get('versiones', []) if isinstance(h, dict) else h
        except json.JSONDecodeError:
            historial = None
    return {'produccion': ref, 'error_produccion': error_ref, 'sirviendo': sirve, 'error_sirviendo': error_sirve,
            'coinciden': (ref['huella_datos'] == sirve['huella_datos']) if ref and sirve else None, 'aviso': aviso,
            'historial': historial, 'flujo_nueva_version': FLUJO_NUEVA_VERSION}


# ------------------------------------------------------------------------------------------------------------------ rutas
def registrar_panel(app: FastAPI, consulta):
    @app.get('/panel', response_class=HTMLResponse)
    def panel():
        return HTML

    @app.get('/panel/lote')
    def panel_lote():
        return datos_lote()

    @app.get('/panel/lote/cliente/{cliente_id}')
    def panel_lote_cliente(cliente_id: int):
        ruta = ultima_campana()
        if ruta is None:
            return JSONResponse(status_code=404, content={'detalle': 'Todavía no hay campaña.'})
        tabla = pd.read_csv(ruta[0])
        fila = tabla[tabla['cliente_id'] == cliente_id]
        if fila.empty:
            return JSONResponse(status_code=404, content={'detalle': f'El cliente {cliente_id} no está en la última campaña.'})
        r = {k: _limpio(v) for k, v in fila.iloc[0].to_dict().items()}
        corte = None
        if ruta[1].exists():
            try:
                corte = json.loads(ruta[1].read_text(encoding='utf-8')).get('corte')
            except json.JSONDecodeError:
                pass
        s = segmento_de(float(r['probabilidad']))
        return {**r, 'corte': corte, 'segmento': s['segmento'], 'recomendacion': s['recomendacion']}

    @app.get('/panel/lote.csv')
    def panel_lote_csv():
        ruta = ultima_campana()
        if ruta is None:
            return JSONResponse(status_code=404, content={'detalle': 'Todavía no hay campaña.'})
        return FileResponse(ruta[0], media_type='text/csv', filename=ruta[0].name)

    @app.get('/panel/versiones')
    def panel_versiones():
        return datos_versiones(consulta)


HTML = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Panel de producción</title>
<link rel="icon" href="data:,">
<style>
:root{--texto:#1d2330;--suave:#5b6474;--borde:#dde1e7;--fondo-suave:#f6f7f9;--acento:#2457c5;
--alta:#1f7a4d;--alta-f:#e3f4ea;--media:#9a6400;--media-f:#fdf1d8;--baja:#b3261e;--baja-f:#fbe5e3}
*{box-sizing:border-box}
body{margin:0;background:#fff;color:var(--texto);font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:1100px;margin:0 auto;padding:24px 16px 48px}
h1{font-size:1.45rem;margin:0 0 4px}
h2{font-size:1.05rem;margin:18px 0 6px}
.sub{color:var(--suave);margin:0 0 16px}
nav{display:flex;gap:4px;border-bottom:1px solid var(--borde);margin-bottom:16px}
nav button{border:1px solid transparent;border-bottom:none;background:none;padding:8px 16px;font:inherit;color:var(--suave);cursor:pointer;border-radius:6px 6px 0 0;margin-bottom:-1px}
nav button[aria-selected=true]{color:var(--acento);font-weight:600;border-color:var(--borde);background:#fff;border-bottom:1px solid #fff}
section.pestana{display:none}section.pestana.activa{display:block}
.nota{background:var(--fondo-suave);border:1px solid var(--borde);border-radius:8px;padding:10px 12px;color:var(--suave);margin:0 0 14px}
.aviso{background:var(--media-f);color:var(--media);border:1px solid var(--media);border-radius:8px;padding:10px 12px;margin:0 0 14px}
.error{background:var(--baja-f);color:var(--baja);border:1px solid var(--baja);border-radius:8px;padding:10px 12px;margin:0 0 14px}
.ok{background:var(--alta-f);color:var(--alta);border:1px solid var(--alta);border-radius:8px;padding:10px 12px;margin:0 0 14px}
.tarjetas{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-bottom:14px}
.tarjeta{border:1px solid var(--borde);border-radius:8px;padding:10px 12px}
.tarjeta b{font-size:1.4rem;display:block;font-variant-numeric:tabular-nums}
.tarjeta span{color:var(--suave);font-size:.86rem}
.fila{display:flex;flex-wrap:wrap;gap:10px;align-items:flex-end;margin-bottom:12px}
label{font-weight:600;display:block;margin-bottom:4px}
input[type=text],input[type=number]{font:inherit;padding:7px 8px;border:1px solid var(--borde);border-radius:6px;background:#fff;color:var(--texto)}
input.ids{width:340px;max-width:100%}
input.corto{width:100px}
button.b{font:inherit;border-radius:6px;border:1px solid var(--borde);background:#fff;color:var(--texto);padding:7px 14px;cursor:pointer}
button.principal{background:var(--acento);color:#fff;border-color:var(--acento);font-weight:600}
button:disabled{opacity:.55;cursor:wait}
table{border-collapse:collapse;width:100%;font-size:.92rem}
th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--borde);vertical-align:top}
th{color:var(--suave);font-weight:600;white-space:nowrap}
td.num{font-variant-numeric:tabular-nums;white-space:nowrap}
.tabla{overflow-x:auto}
.chip{display:inline-block;border-radius:999px;padding:1px 9px;font-size:.82rem;font-weight:600}
.alta{background:var(--alta-f);color:var(--alta)}.media{background:var(--media-f);color:var(--media)}.baja{background:var(--baja-f);color:var(--baja)}
.tres{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px}
.col{border:1px solid var(--borde);border-radius:8px;padding:12px}
.col h3{margin:0 0 2px;font-size:1rem}
.col .que{color:var(--suave);font-size:.84rem;margin-bottom:8px}
.col .prob{font-size:1.8rem;font-weight:700;font-variant-numeric:tabular-nums}
.col dl{display:grid;grid-template-columns:auto 1fr;gap:2px 10px;margin:8px 0 0;font-size:.86rem}
dt{color:var(--suave)}dd{margin:0}
.col.vivo{border-color:var(--acento)}
ol{margin:6px 0 0;padding-left:22px}
code{font-family:ui-monospace,Consolas,monospace;font-size:.9em}
.pie{color:var(--suave);font-size:.84rem;margin-top:12px}
</style>
</head>
<body>
<main>
<h1>Panel de producción</h1>
<p class="sub">Los tres modos de inferencia y la versión del modelo, en un solo sitio. Caso Online Retail II: ¿volverá a comprar en 90 días?</p>

<nav role="tablist" aria-label="Secciones">
  <button role="tab" id="t-lote" data-p="lote" aria-selected="true">Lote</button>
  <button role="tab" id="t-demanda" data-p="demanda" aria-selected="false">Bajo demanda</button>
  <button role="tab" id="t-online" data-p="online" aria-selected="false">Online</button>
  <button role="tab" id="t-versiones" data-p="versiones" aria-selected="false">Versiones</button>
</nav>

<section class="pestana activa" id="p-lote" role="tabpanel">
  <p class="nota">El lote se calcula <b>una vez al día en GitHub Actions</b>: puntúa a todos los clientes con las variables del corte, guarda la campaña (CSV y JSON) y deja esas variables en <code>fs_produccion</code>. Aquí se lee la última.</p>
  <div id="lote-contenido">Cargando…</div>
</section>

<section class="pestana" id="p-demanda" role="tabpanel">
  <p class="nota">Bajo demanda: las variables se <b>leen</b> del último corte de <code>fs_produccion</code> (<b>las variables son las de ayer</b>) y el modelo puntúa al momento.</p>
  <div class="fila">
    <div><label for="d-ids">Id(s) de cliente</label><input type="text" id="d-ids" class="ids" placeholder="12346, 12347"></div>
    <button class="b principal" id="d-ir">Consultar</button>
  </div>
  <div id="d-msg"></div>
  <div class="tabla" id="d-tabla"></div>
</section>

<section class="pestana" id="p-online" role="tabpanel">
  <p class="nota">Online: las variables se <b>calculan ahora</b> con el SQL de la capa FS (corte «ahora»). Solo este modo ve una compra que acaba de ocurrir.</p>
  <div class="fila">
    <div><label for="o-id">Id de cliente</label><input type="text" id="o-id" class="ids" placeholder="12346"></div>
    <button class="b principal" id="o-ir">Consultar</button>
  </div>
  <div class="fila" id="o-demo" hidden>
    <div><label for="o-imp">Importe</label><input type="number" id="o-imp" class="corto" value="120.5" min="0.01" step="0.01"></div>
    <div><label for="o-uni">Unidades</label><input type="number" id="o-uni" class="corto" value="3" min="1" step="1"></div>
    <button class="b principal" id="o-compra">Simular una compra nueva</button>
    <button class="b" id="o-reset">Reiniciar demo</button>
  </div>
  <div id="o-msg"></div>
  <div class="tres" id="o-tres"></div>
</section>

<section class="pestana" id="p-versiones" role="tabpanel">
  <div id="v-contenido">Cargando…</div>
</section>

<p class="pie">Panel sin recursos externos. Los datos salen de la propia interfaz: <code>/panel/lote</code>, <code>/panel/versiones</code>, <code>/bajo-demanda</code>, <code>/online</code>, <code>/modos</code>.</p>
</main>
<script>
const $ = id => document.getElementById(id);
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pct = p => p == null ? '—' : (p * 100).toFixed(1) + ' %';
const dec = (p, n) => p == null ? '—' : Number(p).toFixed(n == null ? 3 : n);
const chip = s => s ? `<span class="chip ${esc(s)}">${esc(s)}</span>` : '—';
let MODOS = null;

async function pedir(url, cuerpo) {
  const r = await fetch(url, cuerpo ? {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(cuerpo)} : {});
  let j = null; try { j = await r.json(); } catch (e) {}
  if (!r.ok) { const e = new Error((j && (j.detalle || JSON.stringify(j))) || ('Error ' + r.status)); e.estado = r.status; throw e; }
  return j;
}
const ids = t => [...new Set(String(t).split(/[\s,;]+/).filter(Boolean).map(Number))].filter(n => Number.isInteger(n) && n > 0);

// ---- pestañas
const cargadas = {};
function abrir(p) {
  document.querySelectorAll('nav button').forEach(b => b.setAttribute('aria-selected', b.dataset.p === p ? 'true' : 'false'));
  document.querySelectorAll('section.pestana').forEach(s => s.classList.toggle('activa', s.id === 'p-' + p));
  if (p === 'lote' && !cargadas.lote) cargarLote();
  if (p === 'versiones' && !cargadas.versiones) cargarVersiones();
  if (history.replaceState) history.replaceState(null, '', '#' + p);
}
document.querySelectorAll('nav button').forEach(b => b.addEventListener('click', () => abrir(b.dataset.p)));

// ---- lote
async function cargarLote() {
  const c = $('lote-contenido');
  try {
    const d = await pedir('/panel/lote'); cargadas.lote = true;
    if (!d.disponible) { c.innerHTML = `<div class="aviso">${esc(d.mensaje)}</div>`; return; }
    const r = d.resumen || {};
    const t = (v, e) => `<div class="tarjeta"><b>${v}</b><span>${e}</span></div>`;
    const pctCamp = r.clientes_puntuados ? ((r.clientes_en_campana / r.clientes_puntuados) * 100).toFixed(0) + ' % de los puntuados' : '';
    let h = '<div class="tarjetas">' +
      t(esc(r.corte || '—'), 'Corte') + t(r.clientes_puntuados == null ? '—' : r.clientes_puntuados, 'Clientes puntuados') +
      t(r.clientes_en_campana == null ? '—' : r.clientes_en_campana, 'En la campaña · ' + esc(pctCamp)) +
      t(pct(r.probabilidad_media), 'Probabilidad media') + t(pct(r.probabilidad_media_campana), 'Probabilidad media en campaña') + '</div>';
    h += `<p>Puntuado con el modelo <b>${esc(r.modelo || '—')}</b>, huella <code>${esc(r.huella_datos || '—')}</code>` +
         (r.referencia ? `, versión en producción <b>v${esc(r.referencia.version)}</b> (<code>${esc(r.referencia.etiqueta_imagen)}</code>)` : '') +
         `. Generado: ${esc(r.generado_en || '—')} · origen: ${esc(r.origen || '—')}.</p>`;
    h += `<h2>Los ${d.primeros.length} primeros de ${d.filas}</h2><div class="tabla"><table><thead><tr><th>Puesto</th><th>Cliente</th><th>Probabilidad</th><th>Decil</th><th>En campaña</th><th>Avisos</th></tr></thead><tbody>` +
      d.primeros.map(x => `<tr><td class="num">${esc(x.puesto)}</td><td class="num">${esc(x.cliente_id)}</td><td class="num">${pct(x.probabilidad)}</td><td class="num">${esc(x.decil)}</td><td>${x.en_campana ? 'sí' : 'no'}</td><td>${x.advertencias ? `<details><summary>${esc(x.n_advertencias)} aviso(s)</summary>${esc(x.advertencias).split(' | ').join('<br>')}</details>` : '—'}</td></tr>`).join('') +
      '</tbody></table></div><p><a href="/panel/lote.csv" download id="descarga">Descargar el CSV completo (' + esc(d.archivo) + ')</a></p>';
    c.innerHTML = h;
  } catch (e) { c.innerHTML = `<div class="error">${esc(e.message)}</div>`; }
}

// ---- bajo demanda
async function demanda() {
  const lista = ids($('d-ids').value), m = $('d-msg'), t = $('d-tabla');
  m.innerHTML = ''; t.innerHTML = '';
  if (!lista.length) { m.innerHTML = '<div class="aviso">Escribe al menos un id de cliente.</div>'; return; }
  $('d-ir').disabled = true;
  try {
    const r = await pedir('/bajo-demanda', {cliente_ids: lista});
    let h = `<p>Corte usado: <b>${esc(r.corte)}</b> — las variables son las de ayer, no las de ahora. Modelo ${esc(r.modelo)}, huella <code>${esc(r.huella_datos)}</code>` +
      (r.ms != null ? `, ${esc(dec(r.ms, 1))} ms` : '') + '.</p>';
    if (r.no_encontrados && r.no_encontrados.length) h += `<div class="aviso">Sin datos en fs_produccion: ${esc(r.no_encontrados.join(', '))}.</div>`;
    h += '<table><thead><tr><th>Cliente</th><th>Probabilidad</th><th>Tramo</th><th>Recomendación</th><th>Corte</th></tr></thead><tbody>' +
      (r.resultados || []).map(x => `<tr><td class="num">${esc(x.cliente_id)}</td><td class="num">${pct(x.probabilidad)}</td><td>${chip(x.segmento)}</td><td>${esc(x.recomendacion)}${x.revisar ? ' <i>(revisar)</i>' : ''}</td><td class="num">${esc(x.corte || r.corte)}</td></tr>`).join('') + '</tbody></table>';
    t.innerHTML = h;
  } catch (e) { m.innerHTML = `<div class="error">${esc(e.message)}</div>`; }
  $('d-ir').disabled = false;
}
$('d-ir').addEventListener('click', demanda);
$('d-ids').addEventListener('keydown', e => { if (e.key === 'Enter') demanda(); });

// ---- online
let ANTES = {};
function col(titulo, que, r, vivo) {
  if (!r) return `<div class="col"><h3>${esc(titulo)}</h3><div class="que">${esc(que)}</div><p class="que">Sin dato para este cliente.</p></div>`;
  return `<div class="col${vivo ? ' vivo' : ''}"><h3>${esc(titulo)}</h3><div class="que">${esc(que)}</div>` +
    `<div class="prob">${pct(r.probabilidad)}</div>${r.segmento ? chip(r.segmento) : ''}` +
    `<dl><dt>Corte</dt><dd>${esc(r.corte || '—')}</dd>` + (r.recomendacion ? `<dt>Recomendación</dt><dd>${esc(r.recomendacion)}</dd>` : '') +
    (r.ms != null ? `<dt>Tiempo</dt><dd>${esc(dec(r.ms, 1))} ms</dd>` : '') + (r.huella_datos ? `<dt>Modelo</dt><dd><code>${esc(r.huella_datos)}</code></dd>` : '') + '</dl></div>';
}
async function opcional(url) { try { return await pedir(url); } catch (e) { if (e.estado === 404) return null; throw e; } }
async function online(nota) {
  const lista = ids($('o-id').value), m = $('o-msg');
  m.innerHTML = nota || '';
  if (lista.length !== 1) { $('o-tres').innerHTML = ''; m.innerHTML = '<div class="aviso">Escribe un id de cliente.</div>'; return; }
  const id = lista[0]; $('o-ir').disabled = true;
  try {
    const [on, bd, lo] = await Promise.all([pedir('/online/' + id), opcional('/bajo-demanda/' + id), opcional('/panel/lote/cliente/' + id)]);
    let delta = '';
    if (ANTES[id] != null && nota) delta = `<div class="ok">Online pasó de ${pct(ANTES[id])} a <b>${pct(on.probabilidad)}</b>; bajo demanda y lote siguen igual hasta que se recalcule <code>fs_produccion</code>.</div>`;
    ANTES[id] = on.probabilidad;
    m.innerHTML = (nota || '') + delta;
    $('o-tres').innerHTML =
      col('Lote', 'Calculado en el último lote (corte ' + (lo && lo.corte || '—') + ')', lo, false) +
      col('Bajo demanda', 'Variables de fs_produccion (las de ayer)', bd, false) +
      col('Online', 'Variables calculadas ahora (corte «ahora»)', on, true);
  } catch (e) { m.innerHTML = `<div class="error">${esc(e.message)}</div>`; $('o-tres').innerHTML = ''; }
  $('o-ir').disabled = false;
}
$('o-ir').addEventListener('click', () => online());
$('o-id').addEventListener('keydown', e => { if (e.key === 'Enter') online(); });
$('o-compra').addEventListener('click', async () => {
  const lista = ids($('o-id').value);
  if (lista.length !== 1) { $('o-msg').innerHTML = '<div class="aviso">Escribe primero el id de un cliente.</div>'; return; }
  $('o-compra').disabled = true;
  try {
    if (ANTES[lista[0]] == null) { const p = await pedir('/online/' + lista[0]); ANTES[lista[0]] = p.probabilidad; }
    const c = await pedir('/demo/compra', {cliente_id: lista[0], importe: Number($('o-imp').value), unidades: Number($('o-uni').value)});
    await online(`<div class="nota">Compra simulada: ${esc(c.importe)} en ${esc(c.unidades)} unidad(es), fecha ${esc(c.fecha)}.</div>`);
  } catch (e) { $('o-msg').innerHTML = `<div class="error">${esc(e.message)}</div>`; }
  $('o-compra').disabled = false;
});
$('o-reset').addEventListener('click', async () => {
  try {
    const r = await pedir('/demo/reiniciar', {}); ANTES = {};
    const lista = ids($('o-id').value);
    if (lista.length === 1) await online(`<div class="nota">Demo reiniciada: ${esc(r.compras_borradas)} compra(s) simulada(s) borrada(s).</div>`);
    else $('o-msg').innerHTML = `<div class="nota">Demo reiniciada: ${esc(r.compras_borradas)} compra(s) simulada(s) borrada(s).</div>`;
  } catch (e) { $('o-msg').innerHTML = `<div class="error">${esc(e.message)}</div>`; }
});

// ---- versiones
function met(m) {
  if (!m) return '—';
  return Object.entries(m).map(([k, v]) => `${esc(k.replace(/_/g, ' '))}: <b>${dec(v)}</b>`).join(' · ');
}
async function cargarVersiones() {
  const c = $('v-contenido');
  try {
    const d = await pedir('/panel/versiones'); cargadas.versiones = true;
    let h = '';
    if (d.aviso) h += `<div class="aviso">${esc(d.aviso)}</div>`;
    else if (d.coinciden) h += '<div class="ok">Coinciden: el modelo que sirve ahora es el de la versión en producción.</div>';
    const p = d.produccion, s = d.sirviendo;
    h += '<div class="tres">';
    if (p) h += `<div class="col"><h3>En producción (referencia.json)</h3><div class="que">La versión aprobada y publicada</div><div class="prob">v${esc(p.version)}</div>
      <dl><dt>Imagen</dt><dd><code>${esc(p.etiqueta_imagen)}</code></dd><dt>Modelo</dt><dd>${esc(p.modelo)}</dd><dt>Huella</dt><dd><code>${esc(p.huella_datos)}</code></dd>
      <dt>Métricas test</dt><dd>${met(p.metricas_test)}</dd><dt>Entrenado</dt><dd>${esc(p.entrenado_en || '—')}</dd><dt>Aprobado</dt><dd>${esc(p.aprobado_en || '—')}</dd></dl></div>`;
    else h += `<div class="col"><h3>En producción</h3><div class="error">${esc(d.error_produccion || 'Sin referencia.')}</div></div>`;
    if (s) h += `<div class="col"><h3>Sirviendo ahora</h3><div class="que">Origen: ${esc(s.origen || '—')}</div><div class="prob">${esc(s.modelo)}</div>
      <dl><dt>Huella</dt><dd><code>${esc(s.huella_datos)}</code></dd><dt>Entrenado</dt><dd>${esc(s.entrenado_en || '—')}</dd></dl></div>`;
    else h += `<div class="col"><h3>Sirviendo ahora</h3><div class="error">${esc(d.error_sirviendo || 'Sin modelo.')}</div></div>`;
    h += '</div><h2>Historial de versiones</h2>';
    if (d.historial && d.historial.length) {
      const cols = [...new Set(d.historial.flatMap(x => Object.keys(x)).filter(k => typeof (d.historial[0] || {})[k] !== 'object'))];
      h += '<div class="tabla"><table><thead><tr>' + cols.map(k => `<th>${esc(k.replace(/_/g, ' '))}</th>`).join('') + '</tr></thead><tbody>' +
        d.historial.map(x => '<tr>' + cols.map(k => `<td>${esc(x[k])}</td>`).join('') + '</tr>').join('') + '</tbody></table></div>';
    } else h += '<p class="que">No hay historial guardado: solo se muestra la versión actual.</p>';
    h += '<h2>Cómo entra una versión nueva</h2><p>Con el workflow «Nueva versión» de GitHub Actions:</p><ol>' + d.flujo_nueva_version.map(x => `<li>${esc(x)}</li>`).join('') + '</ol>';
    c.innerHTML = h;
  } catch (e) { c.innerHTML = `<div class="error">${esc(e.message)}</div>`; }
}

// ---- arranque: el botón de demo solo existe si /modos dice demo=true
(async () => {
  try { MODOS = await pedir('/modos'); $('o-demo').hidden = !MODOS.demo; } catch (e) { $('o-demo').hidden = true; }
  const p = (location.hash || '#lote').slice(1);
  abrir(['lote', 'demanda', 'online', 'versiones'].includes(p) ? p : 'lote');
})();
</script>
</body>
</html>
"""
