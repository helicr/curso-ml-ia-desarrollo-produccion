"""La página de la interfaz (un solo HTML, sin recursos externos: funciona sin internet y dentro de un contenedor)."""

HTML = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Consulta de recompra</title>
<link rel="icon" href="data:,">
<style>
:root{--fondo:#f6f7f9;--panel:#fff;--texto:#1d2330;--suave:#5b6474;--borde:#dde1e7;--acento:#2457c5;--acento-t:#fff;
--alta:#1f7a4d;--alta-f:#e3f4ea;--media:#9a6400;--media-f:#fdf1d8;--baja:#b3261e;--baja-f:#fbe5e3;--aviso:#7a4b00;--barra:#c9d3e6}
@media (prefers-color-scheme:dark){:root{--fondo:#12151b;--panel:#1b2029;--texto:#e6e9ef;--suave:#9aa3b2;--borde:#2c3340;--acento:#7aa2ff;--acento-t:#0d1220;
--alta:#6fd19c;--alta-f:#173226;--media:#f0c060;--media-f:#352a12;--baja:#ff8a80;--baja-f:#3a1d1b;--aviso:#f0c060;--barra:#3a4558}}
*{box-sizing:border-box}
body{margin:0;background:var(--fondo);color:var(--texto);font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:1100px;margin:0 auto;padding:24px 16px 48px}
h1{font-size:1.45rem;margin:0 0 4px}
.sub{color:var(--suave);margin:0 0 20px}
.panel{background:var(--panel);border:1px solid var(--borde);border-radius:10px;padding:16px;margin-bottom:16px}
label{font-weight:600;display:block;margin-bottom:6px}
textarea{width:100%;min-height:92px;resize:vertical;font:14px ui-monospace,Consolas,monospace;padding:8px;border:1px solid var(--borde);border-radius:6px;background:var(--fondo);color:var(--texto)}
input[type=date]{padding:6px 8px;border:1px solid var(--borde);border-radius:6px;background:var(--fondo);color:var(--texto);font:inherit}
.fila{display:flex;flex-wrap:wrap;gap:12px;align-items:flex-end;margin-top:12px}
.fila>div{flex:0 1 auto}
.ayuda{color:var(--suave);font-size:.86rem;margin-top:4px}
button{font:inherit;border-radius:6px;border:1px solid var(--borde);background:var(--panel);color:var(--texto);padding:7px 14px;cursor:pointer}
button.principal{background:var(--acento);color:var(--acento-t);border-color:var(--acento);font-weight:600}
button:disabled{opacity:.55;cursor:wait}
.archivo{display:inline-block}
.estado{font-size:.86rem;color:var(--suave)}
.error{background:var(--baja-f);color:var(--baja);border:1px solid var(--baja);border-radius:8px;padding:10px 12px;margin-bottom:16px}
.tarjetas{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:12px}
.tarjeta{border-radius:8px;padding:10px 12px;border:1px solid var(--borde)}
.tarjeta b{font-size:1.5rem;display:block}
.alta{background:var(--alta-f);color:var(--alta)}.media{background:var(--media-f);color:var(--media)}.baja{background:var(--baja-f);color:var(--baja)}
.tabla{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:.92rem}
th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--borde);vertical-align:top}
th{color:var(--suave);font-weight:600;white-space:nowrap}
td.num{font-variant-numeric:tabular-nums;white-space:nowrap}
.chip{display:inline-block;border-radius:999px;padding:1px 9px;font-size:.82rem;font-weight:600}
.barra{display:inline-block;width:70px;height:7px;border-radius:4px;background:var(--barra);vertical-align:middle;margin-left:6px;overflow:hidden}
.barra i{display:block;height:100%;background:var(--acento)}
.revisar{color:var(--aviso);font-size:.84rem}
details summary{cursor:pointer;color:var(--acento);font-size:.85rem}
dl{display:grid;grid-template-columns:auto auto;gap:2px 12px;margin:6px 0 0;font-size:.84rem}
dt{color:var(--suave)}dd{margin:0;font-variant-numeric:tabular-nums}
.pie{color:var(--suave);font-size:.84rem;margin-top:12px}
code{font-family:ui-monospace,Consolas,monospace;font-size:.9em}
</style>
</head>
<body>
<main>
<h1>¿Volverá a comprar en 90 días?</h1>
<p class="sub">Escribe uno o varios ids de cliente, o carga una lista. Las variables se calculan desde el id con el mismo SQL de la capa FS; la probabilidad la da el modelo; la recomendación es una regla de negocio.</p>

<section class="panel" aria-label="Consulta">
  <label for="ids">Ids de cliente</label>
  <textarea id="ids" placeholder="12346&#10;12347, 12348 12349&#10;(separados por comas, espacios o saltos de línea)"></textarea>
  <div class="fila">
    <div class="archivo">
      <label for="fichero">…o una lista (CSV o TXT)</label>
      <input type="file" id="fichero" accept=".csv,.txt,text/csv,text/plain">
      <div class="ayuda">Si tiene cabecera, se usa la columna <code>cliente_id</code>; si no, la primera.</div>
    </div>
    <div>
      <label for="corte">Fecha de corte</label>
      <input type="date" id="corte">
      <div class="ayuda" id="ayuda-corte">El «hoy» del dato.</div>
    </div>
    <div>
      <button class="principal" id="predecir">Predecir</button>
      <button id="ejemplo">Ejemplo</button>
      <button id="limpiar">Limpiar</button>
    </div>
  </div>
  <p class="estado" id="estado">Cargando…</p>
</section>

<div id="error" class="error" hidden></div>

<section class="panel" id="resultado" hidden aria-live="polite">
  <div class="tarjetas" id="tarjetas"></div>
  <p class="estado" id="resumen"></p>
  <div class="tabla"><table>
    <thead><tr><th>Puesto</th><th>Cliente</th><th>Probabilidad</th><th>Tramo</th><th>Recomendación</th><th>Detalle</th></tr></thead>
    <tbody id="filas"></tbody>
  </table></div>
  <div id="faltan"></div>
  <p><button id="descargar">Descargar CSV</button></p>
  <p class="pie" id="pie"></p>
</section>
</main>

<script>
const $ = id => document.getElementById(id);
let ESTADO = null, ULTIMO = null;
const NOMBRES = {recencia_dias:'Días desde la última compra', frecuencia:'Facturas', monto_total:'Gasto total (£)', ticket_medio:'Ticket medio (£)',
  unidades_total:'Unidades', productos_distintos:'Productos distintos', antiguedad_dias:'Días desde la primera compra', frecuencia_90d:'Facturas en 90 días',
  monto_90d:'Gasto en 90 días (£)', frecuencia_180d:'Facturas en 180 días', dias_medios_entre_compras:'Días medios entre compras',
  devoluciones:'Devoluciones', es_reino_unido:'Reino Unido'};
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pct = p => (100 * p).toLocaleString('es', {maximumFractionDigits: 1}) + ' %';

function mostrarError(t){ const e = $('error'); e.textContent = t; e.hidden = !t; }

async function pedir(url, cuerpo){
  const r = await fetch(url, cuerpo ? {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(cuerpo)} : {});
  const datos = await r.json().catch(() => ({}));
  if (!r.ok){
    let d = datos.detalle || datos.detail || r.statusText;
    if (Array.isArray(d)) d = d.map(x => x.msg).join(' · ');
    throw new Error(`${r.status}: ${d}`);
  }
  return datos;
}

function idsDelTexto(t){ return (t.match(/\d+/g) || []).map(Number); }

function idsDelFichero(texto){
  const lineas = texto.split(/\r?\n/).filter(l => l.trim());
  if (!lineas.length) return [];
  const sep = lineas[0].includes(';') ? ';' : (lineas[0].includes('\t') ? '\t' : ',');
  const cab = lineas[0].split(sep).map(c => c.trim().replace(/^"|"$/g, '').toLowerCase());
  let col = cab.findIndex(c => ['cliente_id', 'customer id', 'customer_id', 'id'].includes(c));
  const conCabecera = col >= 0 || isNaN(Number(cab[0]));
  if (col < 0) col = 0;
  return lineas.slice(conCabecera ? 1 : 0).map(l => (l.split(sep)[col] || '').trim().replace(/^"|"$/g, ''))
               .filter(v => /^\d+(\.0+)?$/.test(v)).map(v => Math.trunc(Number(v)));
}

async function cargarEstado(){
  try {
    ESTADO = await pedir('estado');
    $('corte').value = ESTADO.corte_por_defecto; $('corte').min = ESTADO.primer_corte; $('corte').max = ESTADO.corte_por_defecto;
    $('ayuda-corte').textContent = `Por defecto ${ESTADO.corte_por_defecto}: el día siguiente a la última factura.`;
    $('estado').textContent = `Modelo ${ESTADO.modelo} (huella ${ESTADO.huella_datos}, entrenado ${ESTADO.entrenado_en}) · predicciones: ${ESTADO.origen}`;
  } catch (e) { $('estado').textContent = ''; mostrarError('No se pudo preparar la consulta. ' + e.message); }
}

async function predecir(){
  mostrarError('');
  const ids = [...new Set(idsDelTexto($('ids').value))];
  if (!ids.length){ mostrarError('Escribe al menos un id de cliente o carga una lista.'); return; }
  const max = ESTADO ? ESTADO.maximo_ids : 1000;
  if (ids.length > max){ mostrarError(`Como mucho ${max} clientes por consulta (hay ${ids.length}).`); return; }
  $('predecir').disabled = true; $('predecir').textContent = 'Calculando…';
  try {
    ULTIMO = await pedir('recomendar', {cliente_ids: ids, corte: $('corte').value || null});
    pintar(ULTIMO);
  } catch (e) { mostrarError(e.message); $('resultado').hidden = true; }
  finally { $('predecir').disabled = false; $('predecir').textContent = 'Predecir'; }
}

function pintar(r){
  const segs = ESTADO ? ESTADO.segmentos : [];
  $('tarjetas').innerHTML = segs.map((s, i) => {
    const tramo = !i ? `≥ ${pct(s.desde)}` : (s.desde > 0 ? `${pct(s.desde)} – ${pct(segs[i-1].desde)}` : `< ${pct(segs[i-1].desde)}`);
    return `<div class="tarjeta ${esc(s.segmento)}"><b>${r.por_segmento[s.segmento] || 0}</b>Tramo ${esc(s.segmento)} (${tramo})</div>`;
  }).join('');
  $('resumen').textContent = `Corte ${r.corte} · ${r.encontrados} de ${r.pedidos} clientes con predicción · puesto y decil entre los ${r.clientes_en_el_corte} clientes del corte.`;
  $('filas').innerHTML = r.resultados.map(x => {
    const vars = Object.entries(x.variables).map(([k, v]) => `<dt>${esc(NOMBRES[k] || k)}</dt><dd>${v === null ? '—' : esc(k === 'es_reino_unido' ? (v ? 'sí' : 'no') : v.toLocaleString('es'))}</dd>`).join('');
    const avisos = x.advertencias.length ? `<div class="revisar">⚠ Revisar: ${x.advertencias.map(esc).join(' ')}</div>` : '';
    return `<tr><td class="num">${x.puesto} <span class="estado">(decil ${x.decil})</span></td><td class="num"><b>${x.cliente_id}</b></td>
      <td class="num">${pct(x.probabilidad)}<span class="barra" aria-hidden="true"><i style="width:${(100*x.probabilidad).toFixed(1)}%"></i></span></td>
      <td><span class="chip ${esc(x.segmento)}">${esc(x.segmento)}</span></td><td>${esc(x.recomendacion)}${avisos}</td>
      <td><details><summary>Variables</summary><dl>${vars}</dl></details></td></tr>`;
  }).join('');
  $('faltan').innerHTML = r.no_encontrados.length ? `<p><b>Sin predicción (${r.no_encontrados.length}):</b></p><ul>` +
    r.no_encontrados.map(f => `<li><code>${f.cliente_id}</code>: ${esc(f.motivo)}</li>`).join('') + '</ul>' : '';
  $('pie').textContent = `Modelo ${r.modelo} · huella ${r.huella_datos} · entrenado ${r.entrenado_en} · predicciones: ${r.origen}. ` +
    'La probabilidad la calcula el modelo; el tramo y la recomendación son una regla de negocio (config.SEGMENTOS_RECOMPRA).';
  $('resultado').hidden = false;
}

function descargar(){
  if (!ULTIMO) return;
  const vars = Object.keys(NOMBRES);
  const cab = ['corte', 'cliente_id', 'probabilidad', 'segmento', 'recomendacion', 'revisar', 'puesto', 'decil', 'advertencias', ...vars];
  const q = v => { const s = v === null || v === undefined ? '' : String(v); return /[",;\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
  const filas = ULTIMO.resultados.map(x => [ULTIMO.corte, x.cliente_id, x.probabilidad, x.segmento, x.recomendacion, x.revisar, x.puesto, x.decil,
    x.advertencias.join(' | '), ...vars.map(k => x.variables[k])].map(q).join(','));
  const blob = new Blob(['﻿' + [cab.join(','), ...filas].join('\n')], {type: 'text/csv;charset=utf-8'});
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `recompra_${ULTIMO.corte}.csv`; a.click(); URL.revokeObjectURL(a.href);
}

$('predecir').onclick = predecir;
$('ids').addEventListener('keydown', e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) predecir(); });
$('ejemplo').onclick = () => { if (ESTADO) $('ids').value = ESTADO.ejemplos.join(', ') + ', 99999'; };
$('limpiar').onclick = () => { $('ids').value = ''; $('fichero').value = ''; $('resultado').hidden = true; mostrarError(''); };
$('descargar').onclick = descargar;
$('fichero').onchange = async e => {
  const f = e.target.files[0]; if (!f) return;
  const ids = idsDelFichero(await f.text());
  if (!ids.length){ mostrarError(`No encontré ids en ${f.name}.`); return; }
  mostrarError(''); $('ids').value = [...new Set(ids)].join('\n');
};
cargarEstado();
</script>
</body>
</html>
"""
