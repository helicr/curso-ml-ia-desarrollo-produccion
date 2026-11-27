'use strict';
/* Interfaz del extra de S5. Vanilla JS, sin librerías ni CDNs: funciona sin Internet.
   Todo el texto que llega del servidor se pinta con textContent (nunca innerHTML). */

// ------------------------------------------------------------------------------------------------ utilidades
const $ = (s, r = document) => r.querySelector(s);
const SVGNS = 'http://www.w3.org/2000/svg';

function poner(el, attrs) {
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === false || v == null) continue;
    if (k === 'class') el.setAttribute('class', v);
    else if (k === 'text') el.textContent = v;
    else if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? '' : v);
  }
}
function anadir(el, hijos) {
  for (const c of hijos.flat(Infinity)) {
    if (c == null || c === false) continue;
    el.appendChild(typeof c === 'object' ? c : document.createTextNode(String(c)));
  }
  return el;
}
const h = (tag, attrs, ...hijos) => { const el = document.createElement(tag); poner(el, attrs); return anadir(el, hijos); };
const s = (tag, attrs, ...hijos) => { const el = document.createElementNS(SVGNS, tag); poner(el, attrs); return anadir(el, hijos); };
const vaciar = (el) => { while (el.firstChild) el.removeChild(el.firstChild); return el; };
const json = (o) => JSON.stringify(o, null, 2);
const esperar = (ms) => new Promise((r) => setTimeout(r, ms));

const nf = (d = 0) => new Intl.NumberFormat('es-ES', { maximumFractionDigits: d, minimumFractionDigits: 0 });
const pct = (p) => (p == null ? '—' : (p * 100).toLocaleString('es-ES', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + ' %');
const num = (v, d = 2) => (v == null ? '—' : typeof v === 'number' ? nf(d).format(v) : String(v));
const auc = (v) => (v == null ? '—' : v.toLocaleString('es-ES', { minimumFractionDigits: 4, maximumFractionDigits: 4 }));

async function api(ruta, opciones) {
  let r;
  try { r = await fetch(ruta, opciones); } catch (e) { throw new Error('No se pudo contactar con la aplicación (¿sigue en marcha?).'); }
  let datos = null;
  try { datos = await r.json(); } catch (e) { /* sin cuerpo */ }
  if (!r.ok) throw new Error((datos && (datos.error || (Array.isArray(datos.detail) ? datos.detail.map((d) => d.msg).join('; ') : datos.detail))) || `Error HTTP ${r.status}`);
  return datos;
}
const post = (ruta, cuerpo) => api(ruta, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(cuerpo || {}) });
const llamar = (herramienta, argumentos) => post('/api/herramienta', { herramienta, argumentos: argumentos || {} });

const NOMBRE_SRV = { datos: 'mcp-datos-master', modelo: 'mcp-modelo-retencion' };
const ETIQ = {
  recencia_dias: 'Días desde la última compra', frecuencia: 'Compras (frecuencia)', monto_total: 'Gasto total', ticket_medio: 'Ticket medio',
  unidades_total: 'Unidades compradas', productos_distintos: 'Productos distintos', antiguedad_dias: 'Antigüedad (días)',
  frecuencia_90d: 'Compras en 90 días', monto_90d: 'Gasto en 90 días', frecuencia_180d: 'Compras en 180 días',
  dias_medios_entre_compras: 'Días medios entre compras', devoluciones: 'Devoluciones', es_reino_unido: 'Cliente de Reino Unido (0/1)',
};
const PASO = { dias_medios_entre_compras: 0.1, monto_total: 1, monto_90d: 1, ticket_medio: 1 };
const COLOR_TRAMO = { alta: '#2f9e62', media: '#e0a021', baja: '#d4584d' };

function etiquetaOrigen(servidor, herramienta) {
  return h('span', { class: 'etiqueta-origen ' + servidor, title: `Lo produjo la herramienta ${herramienta} de ${NOMBRE_SRV[servidor]}` }, `${NOMBRE_SRV[servidor]} · ${herramienta}`);
}
const tramoChip = (t) => h('span', { class: 'tramo ' + t }, t ? `Probabilidad ${t}` : '—');
function errorCaja(msg) { return h('p', { class: 'nota roja', role: 'alert' }, msg); }

// ------------------------------------------------------------------------------------------------ estado global
const S = {
  estado: null, clientes: [], rangos: {}, versionClientes: null, errorClientes: null, cid: null, detalle: null, filtro: '', tramo: 'todos', orden: 'id',
  trazaUltimo: 0, hist: [], ocupado: false, cambioModelo: null, herr: null, ysi: null,
};

// ------------------------------------------------------------------------------------------------ diálogo propio (nada de confirm/alert del navegador)
const dlg = $('#dialogo');
function dialogo({ titulo, cuerpo, ok = 'Aceptar', cancelar = 'Cancelar', peligro = false, alAceptar = null, soloInfo = false }) {
  return new Promise((resolver) => {
    $('#dlg-titulo').textContent = titulo;
    const caja = vaciar($('#dlg-cuerpo'));
    anadir(caja, [cuerpo]);
    const error = h('p', { class: 'error-dlg', role: 'alert', hidden: true });
    caja.appendChild(error);
    const bOk = $('#dlg-ok'), bNo = $('#dlg-cancelar');
    bOk.textContent = ok; bNo.textContent = cancelar; bNo.hidden = soloInfo;
    bOk.className = 'boton ' + (peligro ? 'peligro' : 'primario');
    bOk.disabled = bNo.disabled = false;
    let cerrado = false;
    const cerrar = (v) => { if (cerrado) return; cerrado = true; limpiar(); if (dlg.open) dlg.close(); resolver(v); };
    const limpiar = () => { bOk.onclick = bNo.onclick = null; dlg.oncancel = null; };
    bNo.onclick = () => cerrar(false);
    dlg.oncancel = (ev) => { ev.preventDefault(); if (!bOk.disabled) cerrar(false); };
    bOk.onclick = async () => {
      if (alAceptar) {
        bOk.disabled = bNo.disabled = true; error.hidden = true;
        const previo = bOk.textContent; bOk.textContent = 'Trabajando…';
        try { await alAceptar(); } catch (e) {
          error.textContent = e.message; error.hidden = false; bOk.textContent = previo; bOk.disabled = bNo.disabled = false; return;
        }
        bOk.textContent = previo;
      }
      cerrar(true);
    };
    dlg.showModal();
    (soloInfo ? bOk : bNo).focus();
  });
}
const queSi = (titulo, ...items) => h('div', { class: 'que si' }, h('b', {}, titulo), h('ul', {}, items.map((i) => h('li', {}, i))));
const queNo = (titulo, ...items) => h('div', { class: 'que no' }, h('b', {}, titulo), h('ul', {}, items.map((i) => h('li', {}, i))));

// ------------------------------------------------------------------------------------------------ cabecera: píldoras, avisos, backend
function pildora(clase, nombre, valor, detalle) {
  return h('span', { class: 'pildora ' + clase, title: detalle || '' }, h('i', { class: 'punto', 'aria-hidden': 'true' }), h('b', {}, nombre), ' ', valor);
}
function pintarCabecera() {
  const e = S.estado; if (!e) return;
  const p = vaciar($('#pildoras'));
  const d = e.servidores.datos, m = e.servidores.modelo, mo = e.modelo, l = e.llm;
  p.appendChild(d.vivo ? pildora('ok', 'MCP datos', `· motor ${e.backend}`, `${d.herramientas.length} herramientas`) : pildora('mal', 'MCP datos', '· caído', d.error));
  if (!m.vivo) p.appendChild(pildora('mal', 'MCP modelo', '· caído', m.error));
  else if (mo.sin_alias) p.appendChild(pildora('aviso', 'MCP modelo', '· sin alias champion', 'Hay que promover una versión'));
  else if (mo.error) p.appendChild(pildora('mal', 'MCP modelo', '· con error', mo.error));
  else p.appendChild(pildora('ok', 'MCP modelo', `· v${mo.version}@${mo.alias}`, `${mo.versiones_registradas} versiones registradas`));
  p.appendChild(l.ok ? pildora('ok', 'LLM', `· ${l.modelo} · responde`, l.url) : pildora('mal', 'LLM', `· ${l.modelo} · ${l.detalle}`, l.ayuda));
  const bq = e.backend === 'bigquery';
  $('#b-sqlite').setAttribute('aria-pressed', String(!bq));
  $('#b-bigquery').setAttribute('aria-pressed', String(bq));
}
function pintarAvisos() {
  const e = S.estado, caja = vaciar($('#avisos')); if (!e) return;
  for (const [k, sv] of Object.entries(e.servidores)) {
    if (!sv.vivo) caja.appendChild(h('div', { class: 'aviso error', role: 'alert' }, h('span', { class: 'texto' }, `El servidor ${sv.nombre} no está en marcha: ${sv.error}`)));
  }
  if (!e.proyecto_ok) caja.appendChild(h('div', { class: 'aviso warn' }, h('span', { class: 'texto' }, 'No se encuentran 04-Proyecto-Base o curso.db. Define MCP_PROYECTO y CURSO_DB (consulta el README) y reinicia la aplicación.')));
  if (e.modelo.sin_alias && e.servidores.modelo.vivo) {
    const v = e.modelo.ultima_version;
    caja.appendChild(h('div', { class: 'aviso warn', role: 'status' },
      h('span', { class: 'texto' }, h('b', {}, 'El modelo no tiene alias champion. '), 'El MCP del modelo carga «lo que mande champion»: sin alias no puede predecir. Ninguna versión se promueve sola.'),
      h('button', { class: 'boton primario', type: 'button', onclick: () => promover(v) }, `Promover la v${v} a champion`)));
  }
}

async function refrescarEstado() {
  try { S.estado = await api('/api/estado'); } catch (e) { return; }
  pintarCabecera(); pintarAvisos();
  if (S.tab === 'modelo') pintarModelo();
  if (S.tab === 'pregunta') pintarEstadoChat();
  if (!S.herr) construirExplorador();
}

$('#b-sqlite').onclick = () => cambiarBackend('sqlite');
$('#b-bigquery').onclick = () => cambiarBackend('bigquery');
async function cambiarBackend(destino) {
  if (!S.estado || S.estado.backend === destino) return;
  const proyecto = h('input', { type: 'text', id: 'bq-proyecto', placeholder: 'id-de-tu-proyecto', autocomplete: 'off', spellcheck: 'false' });
  const dataset = h('input', { type: 'text', id: 'bq-dataset', value: 'curso_master', autocomplete: 'off', spellcheck: 'false' });
  const cuerpo = destino === 'sqlite'
    ? h('div', {}, h('p', {}, 'Se reinicia solo el servidor MCP de datos para que lea de nuevo curso.db (SQLite, solo lectura). El servidor del modelo no se toca.'))
    : h('div', { class: 'rejilla' },
      h('p', {}, 'Se reinicia solo el servidor MCP de datos para que lea de BigQuery. Exige ',
        h('code', {}, 'GCP_PROJECT'), ' y credenciales de Google en este equipo (', h('code', {}, 'gcloud auth application-default login'), '). Si faltan, verás el motivo y todo sigue en SQLite.'),
      queNo('Antes de usarlo', '«Sin verificar» en esta interfaz con un proyecto real: aquí solo se ha probado con un conector falso.',
        'Usa un proyecto de pruebas tuyo, nunca el de tu trabajo. Cada consulta tiene un tope de 100 MB facturables.'),
      h('label', {}, 'Proyecto de Google Cloud', proyecto), h('label', {}, 'Dataset', dataset));
  const hecho = await dialogo({
    titulo: destino === 'sqlite' ? 'Volver a SQLite' : 'Cambiar a BigQuery', cuerpo, ok: destino === 'sqlite' ? 'Volver a SQLite' : 'Intentar cambiar a BigQuery',
    alAceptar: () => post('/api/backend', { backend: destino, proyecto: proyecto.value.trim() || null, dataset: dataset.value.trim() || null }),
  });
  if (hecho) { await refrescarEstado(); await cargarClientes(true); }
}

// ------------------------------------------------------------------------------------------------ pestañas
const TABS = ['cliente', 'ysi', 'pregunta', 'explorador', 'modelo', 'lote'];
function irA(tab, foco) {
  S.tab = tab;
  for (const t of TABS) {
    const sel = t === tab;
    const b = $('#t-' + t); b.setAttribute('aria-selected', String(sel)); b.tabIndex = sel ? 0 : -1;
    $('#p-' + t).hidden = !sel;
    if (sel && foco) b.focus();
  }
  if (tab === 'ysi') pintarYsi();
  if (tab === 'modelo') pintarModelo();
  if (tab === 'pregunta') pintarEstadoChat();
  if (tab === 'explorador') construirExplorador();
  if (tab === 'lote') abrirLote();
  else pararSondeoLote();
}
for (const t of TABS) {
  const b = $('#t-' + t);
  b.onclick = () => irA(t);
  b.onkeydown = (ev) => {
    const i = TABS.indexOf(t);
    if (ev.key === 'ArrowRight') { ev.preventDefault(); irA(TABS[(i + 1) % TABS.length], true); }
    if (ev.key === 'ArrowLeft') { ev.preventDefault(); irA(TABS[(i + TABS.length - 1) % TABS.length], true); }
  };
}

// ------------------------------------------------------------------------------------------------ gráficos SVG
function medidor(p, { ghost = null, tramo = null, ancho = 260 } = {}) {
  const cx = 130, cy = 128, r = 98;
  const pt = (q, rr = r) => { const a = Math.PI * (1 - q); return [cx + rr * Math.cos(a), cy - rr * Math.sin(a)]; };
  const arco = (q0, q1, rr = r) => { const [x0, y0] = pt(q0, rr), [x1, y1] = pt(q1, rr); return `M${x0.toFixed(2)} ${y0.toFixed(2)} A${rr} ${rr} 0 0 1 ${x1.toFixed(2)} ${y1.toFixed(2)}`; };
  const t = tramo || (p >= 0.7 ? 'alta' : p >= 0.4 ? 'media' : 'baja');
  const svg = s('svg', { viewBox: '0 -10 260 160', role: 'img', 'aria-label': `Medidor: probabilidad de volver a comprar ${pct(p)}, tramo ${t}` });
  svg.appendChild(s('path', { d: arco(0.0005, 0.9995), fill: 'none', stroke: '#e6ebf2', 'stroke-width': 18, 'stroke-linecap': 'round' }));
  for (const [a, b, c] of [[0, 0.4, '#f3c4bf'], [0.4, 0.7, '#f6dca5'], [0.7, 1, '#b9e0c9']]) {
    svg.appendChild(s('path', { d: arco(Math.max(a, 0.002), Math.min(b, 0.998), r + 15), fill: 'none', stroke: c, 'stroke-width': 6 }));
  }
  svg.appendChild(s('path', { d: arco(0.0005, Math.max(0.002, Math.min(p, 0.9995))), fill: 'none', stroke: COLOR_TRAMO[t], 'stroke-width': 18, 'stroke-linecap': 'round' }));
  for (const q of [0.4, 0.7]) {
    const [x0, y0] = pt(q, r - 12), [x1, y1] = pt(q, r + 20);
    svg.appendChild(s('line', { x1: x0, y1: y0, x2: x1, y2: y1, stroke: '#566274', 'stroke-width': 1.2 }));
    const [tx, ty] = pt(q, r + 31);
    svg.appendChild(s('text', { x: tx, y: ty, 'text-anchor': 'middle', 'font-size': 10, fill: '#566274' }, `${q * 100}`));
  }
  if (ghost != null) {
    const [x0, y0] = pt(ghost, r - 14), [x1, y1] = pt(ghost, r + 12);
    svg.appendChild(s('line', { x1: x0, y1: y0, x2: x1, y2: y1, stroke: '#1a2332', 'stroke-width': 3, 'stroke-dasharray': '2 2' }));
    const [tx, ty] = pt(ghost, r - 26);
    svg.appendChild(s('text', { x: tx, y: ty, 'text-anchor': 'middle', 'font-size': 9.5, fill: '#1a2332' }, 'original'));
  }
  svg.appendChild(s('text', { x: cx, y: cy - 14, 'text-anchor': 'middle', 'font-size': 34, 'font-weight': 700, fill: '#1a2332' }, pct(p)));
  svg.appendChild(s('text', { x: cx, y: cy + 8, 'text-anchor': 'middle', 'font-size': 11, fill: '#566274' }, 'de volver a comprar en 90 días'));
  return svg;
}

function barrasPorQue(filas, contenedor) {
  vaciar(contenedor);
  const W = Math.max(280, contenedor.clientWidth || 520);
  const L = Math.min(190, Math.round(W * 0.42)), margen = 46, fila = 30;
  const x0 = L + 8, x1 = W - margen, mid = (x0 + x1) / 2, mitad = (x1 - x0) / 2;
  const max = Math.max(0.0001, ...filas.map((f) => Math.abs(f.peso_logit)));
  const svg = s('svg', { viewBox: `0 0 ${W} ${filas.length * fila + 8}`, role: 'img', 'aria-label': 'Barras horizontales con el peso de cada variable en la probabilidad: azul sube, naranja baja' });
  svg.appendChild(s('line', { x1: mid, y1: 0, x2: mid, y2: filas.length * fila + 4, stroke: '#9aa6b8', 'stroke-width': 1 }));
  filas.forEach((f, i) => {
    const y = i * fila + 4, w = (Math.abs(f.peso_logit) / max) * (mitad - 40), sube = f.peso_logit >= 0;
    const etiqueta = (ETIQ[f.variable] || f.variable);
    const txt = s('text', { x: L, y: y + 14, 'text-anchor': 'end', 'font-size': 12.5, fill: '#1a2332' }, etiqueta.length > 26 && L < 170 ? etiqueta.slice(0, 25) + '…' : etiqueta);
    txt.appendChild(s('title', {}, `${f.variable} = ${f.valor}`));
    svg.appendChild(txt);
    svg.appendChild(s('text', { x: L, y: y + 26, 'text-anchor': 'end', 'font-size': 10.5, fill: '#566274' }, `valor ${num(f.valor, 2)}`));
    svg.appendChild(s('rect', { x: sube ? mid : mid - w, y: y + 3, width: Math.max(w, 1.5), height: 17, rx: 3, fill: sube ? '#1f5fbf' : '#d9731a' }));
    const tx = sube ? mid + w + 5 : mid - w - 5;
    svg.appendChild(s('text', { x: tx, y: y + 16, 'text-anchor': sube ? 'start' : 'end', 'font-size': 11.5, fill: '#1a2332', 'font-variant-numeric': 'tabular-nums' },
      `${f.peso_logit > 0 ? '+' : ''}${f.peso_logit.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`));
  });
  contenedor.appendChild(svg);
}

// ------------------------------------------------------------------------------------------------ pestaña 1: Cliente
const pCliente = $('#p-cliente');
function construirCliente() {
  vaciar(pCliente);
  const buscar = h('input', { type: 'search', id: 'buscar', placeholder: 'Buscar por nº de cliente…', 'aria-label': 'Buscar cliente por número', autocomplete: 'off', oninput: (ev) => { S.filtro = ev.target.value.trim(); pintarLista(); } });
  const orden = h('select', { 'aria-label': 'Ordenar clientes', onchange: (ev) => { S.orden = ev.target.value; pintarLista(); } },
    h('option', { value: 'id' }, 'Orden: nº de cliente'), h('option', { value: 'pdesc' }, 'Orden: probabilidad ↓'), h('option', { value: 'pasc' }, 'Orden: probabilidad ↑'));
  const filtros = h('div', { class: 'filtros', role: 'group', 'aria-label': 'Filtrar por tramo' },
    ['todos', 'alta', 'media', 'baja'].map((t) => h('button', { type: 'button', class: 'chip-filtro', 'data-t': t, 'aria-pressed': String(S.tramo === t), onclick: () => { S.tramo = t; for (const b of filtros.children) b.setAttribute('aria-pressed', String(b.dataset.t === t)); pintarLista(); } }, t === 'todos' ? 'Todos' : t[0].toUpperCase() + t.slice(1))));
  pCliente.appendChild(h('div', { class: 'cliente-grid' },
    h('div', { class: 'tarjeta lista-clientes' },
      h('header', {}, h('h2', {}, 'Clientes'), h('span', { class: 'peq tenue', id: 'cli-n' })),
      h('div', { class: 'controles' }, buscar, orden, filtros),
      h('ul', { class: 'clientes', id: 'lista-clientes', 'aria-label': 'Lista de clientes' }),
      h('p', { class: 'peq tenue', id: 'cli-origen' })),
    h('div', { class: 'col', id: 'cli-detalle' })));
}
function pintarLista() {
  const ul = $('#lista-clientes'); if (!ul) return; vaciar(ul);
  const nota = $('#cli-origen');
  if (S.errorClientes) {
    ul.appendChild(h('li', {}, h('p', { class: 'vacio' }, S.errorClientes)));
    $('#cli-n').textContent = ''; nota.textContent = ''; return;
  }
  let lista = S.clientes.filter((c) => (!S.filtro || String(c.cliente_id).includes(S.filtro)) && (S.tramo === 'todos' || c.tramo === S.tramo));
  lista = lista.slice().sort((a, b) => S.orden === 'pdesc' ? b.probabilidad - a.probabilidad : S.orden === 'pasc' ? a.probabilidad - b.probabilidad : a.cliente_id - b.cliente_id);
  $('#cli-n').textContent = `${lista.length} de ${S.clientes.length}`;
  nota.textContent = S.clientes.length ? `Probabilidades de volver a comprar con la v${S.versionClientes ?? '?'} (predecir_cliente de mcp-modelo-retencion).` : '';
  if (!lista.length) ul.appendChild(h('li', {}, h('p', { class: 'vacio' }, S.clientes.length ? 'Ningún cliente coincide con el filtro.' : 'Cargando clientes…')));
  for (const c of lista) {
    ul.appendChild(h('li', {}, h('button', { type: 'button', class: 'cli-item', 'aria-pressed': String(c.cliente_id === S.cid), onclick: () => elegirCliente(c.cliente_id), 'aria-label': `Cliente ${c.cliente_id}, probabilidad ${pct(c.probabilidad)}, tramo ${c.tramo}` },
      h('span', { class: 'mono' }, String(c.cliente_id)),
      h('span', { class: 'cli-barra', 'aria-hidden': 'true' }, h('i', { class: 'c-' + c.tramo, style: `width:${(c.probabilidad * 100).toFixed(1)}%` })),
      h('span', { class: 'cli-p' }, pct(c.probabilidad)))));
  }
}
async function cargarClientes(forzar) {
  if (forzar) { S.clientes = []; S.errorClientes = null; pintarLista(); }
  try {
    const d = await api('/api/clientes');
    S.errorClientes = d.error ? (d.sin_alias ? 'El modelo no tiene alias champion: promueve una versión (aviso superior o pestaña Modelo) para ver las probabilidades.' : d.error) : null;
    S.clientes = d.clientes || []; S.rangos = d.rangos || {}; S.versionClientes = d.version;
  } catch (e) { S.errorClientes = e.message; S.clientes = []; }
  pintarLista();
  if (S.cid != null && S.clientes.some((c) => c.cliente_id === S.cid)) return elegirCliente(S.cid, true);
  if (S.cid == null) pintarDetalleVacio();
}
function pintarDetalleVacio() {
  const d = vaciar($('#cli-detalle'));
  d.appendChild(h('div', { class: 'vacio' }, S.errorClientes ? 'Sin clientes que mostrar todavía.' : 'Elige un cliente de la lista para ver su probabilidad, qué la empuja y su ficha de datos.'));
}
let tokenCliente = 0;
async function elegirCliente(id, recarga) {
  S.cid = id; pintarLista();
  const yo = ++tokenCliente, d = vaciar($('#cli-detalle'));
  d.appendChild(h('div', { class: 'vacio', role: 'status' }, `Cargando el cliente ${id}…`));
  const [pred, porque, resumen, facturas] = await Promise.all([
    llamar('predecir_cliente', { cliente_id: id }), llamar('por_que', { cliente_id: id, n: 13 }),
    llamar('resumen_cliente', { cliente_id: id }), llamar('ultimas_facturas', { cliente_id: id, n: 5 }),
  ].map((p) => p.catch((e) => ({ ok: false, resultado: { error: e.message } }))));
  if (yo !== tokenCliente) return;
  S.detalle = { id, pred, porque, resumen, facturas };
  vaciar(d);
  const R = pred.resultado;
  d.appendChild(h('div', { class: 'tarjeta' },
    h('header', {}, h('h2', {}, `Cliente ${id}`), etiquetaOrigen('modelo', 'predecir_cliente')),
    pred.ok ? h('div', { class: 'medidor-caja' }, medidor(R.probabilidad, { tramo: R.tramo }),
      h('div', { class: 'reco' }, tramoChip(R.tramo), h('p', { style: 'margin-top:8px' }, h('strong', {}, 'Recomendación de negocio'), R.recomendacion),
        h('p', { class: 'peq tenue', style: 'margin-top:8px' }, `Modelo v${R.version_modelo}@${R.alias} · variables del lote del ${R.corte_de_las_variables}. La probabilidad es la de VOLVER A COMPRAR: alta = buena noticia.`)))
      : errorCaja(R.error || 'No se pudo predecir.')));
  const barras = h('div', { class: 'barras', id: 'barras' });
  d.appendChild(h('div', { class: 'tarjeta' },
    h('header', {}, h('h3', {}, 'Qué empuja la cifra'), etiquetaOrigen('modelo', 'por_que')),
    porque.ok && porque.resultado.variables_que_mas_pesan ? h('div', {},
      h('div', { class: 'leyenda' }, h('span', {}, h('i', { style: 'background:#1f5fbf' }), 'sube la probabilidad'), h('span', {}, h('i', { style: 'background:#d9731a' }), 'baja la probabilidad'), h('span', {}, 'pesos en escala logit')),
      barras, h('p', { class: 'peq tenue', style: 'margin-top:8px' }, porque.resultado.nota + ` Intercepto ${num(porque.resultado.intercepto_logit, 2)} + suma de pesos = logit ${num(porque.resultado.logit_total, 2)}.`))
      : errorCaja(porque.resultado.error || porque.resultado.nota || 'No hay descomposición para este modelo.')));
  if (porque.ok && porque.resultado.variables_que_mas_pesan) { S.barras = porque.resultado.variables_que_mas_pesan; barrasPorQue(S.barras, barras); }
  const ficha = h('div', { class: 'tarjeta' }, h('header', {}, h('h3', {}, 'Ficha de datos'), etiquetaOrigen('datos', 'resumen_cliente'), etiquetaOrigen('datos', 'ultimas_facturas')));
  if (resumen.ok) {
    const r = resumen.resultado, campos = [['País', r.pais], ['Primer movimiento', (r.primer_movimiento || '').slice(0, 10)], ['Último movimiento', (r.ultimo_movimiento || '').slice(0, 10)],
      ['Facturas', num(r.facturas, 0)], ['Cancelaciones', num(r.cancelaciones, 0)], ['Monto de ventas válidas', num(r.monto_ventas, 2)]];
    ficha.appendChild(h('dl', { class: 'ficha' }, campos.map(([k, v]) => h('div', {}, h('dt', {}, k), h('dd', {}, v ?? '—')))));
  } else ficha.appendChild(errorCaja(resumen.resultado.error || 'No hay resumen de este cliente en la capa master.'));
  if (facturas.ok) {
    const filas = facturas.resultado.filas || [];
    ficha.appendChild(filas.length ? h('div', { class: 'tabla-scroll' }, h('table', {}, h('thead', {}, h('tr', {}, ['Factura', 'Fecha', 'País', 'Cancelación', 'Total'].map((t, i) => h('th', { class: i === 4 ? 'num' : '' }, t)))),
      h('tbody', {}, filas.map((f) => h('tr', {}, h('td', { class: 'mono' }, f.factura_id), h('td', {}, String(f.fecha_factura || '').slice(0, 10)), h('td', {}, f.pais), h('td', {}, f.es_cancelacion ? 'Sí' : 'No'), h('td', { class: 'num' }, num(f.total, 2))))))) : h('p', { class: 'tenue' }, 'Sin facturas.'));
  } else ficha.appendChild(errorCaja(facturas.resultado.error || 'No se pudieron leer las facturas.'));
  d.appendChild(ficha);
  if (S.tab === 'ysi') pintarYsi();
}
window.addEventListener('resize', () => { const b = $('#barras'); if (b && S.barras) barrasPorQue(S.barras, b); });

// ------------------------------------------------------------------------------------------------ pestaña 2: ¿Y si…?
const pYsi = $('#p-ysi');
let tokenYsi = 0, temporizadorYsi = null;
function pintarYsi() {
  vaciar(pYsi);
  const sel = h('select', { id: 'ysi-cliente', 'aria-label': 'Cliente de partida', onchange: (ev) => elegirCliente(Number(ev.target.value)) },
    h('option', { value: '' }, 'Elige un cliente…'), S.clientes.map((c) => h('option', { value: c.cliente_id, selected: c.cliente_id === S.cid }, `${c.cliente_id} · ${pct(c.probabilidad)}`)));
  const intro = h('div', { class: 'tarjeta' }, h('header', {}, h('h2', {}, '¿Y si…? Mover las variables de un cliente'), etiquetaOrigen('modelo', 'predecir_variables')),
    h('div', { class: 'nota' }, h('b', {}, 'Léelo con cuidado. '), 'Mover una sola variable no da un cliente real: en los datos las variables van juntas (si cambias las compras, el gasto cambiaría también). ',
      'Y la relación que aprendió el modelo es estadística, no causal: no dice qué pasaría si el cliente de verdad cambiara. ',
      'Ejemplo: en este modelo la probabilidad SUBE con la recencia (más días sin comprar, más probabilidad), contra la intuición; no se ha investigado por qué.'),
    h('div', { style: 'margin-top:12px; max-width:340px' }, h('label', { for: 'ysi-cliente', class: 'peq tenue' }, 'Cliente de partida'), sel));
  pYsi.appendChild(intro);
  const c = S.clientes.find((x) => x.cliente_id === S.cid);
  if (!c) { pYsi.appendChild(h('div', { class: 'vacio', style: 'margin-top:16px' }, S.errorClientes || 'Elige un cliente para empezar.')); return; }
  S.ysi = { orig: { ...c.variables }, vals: { ...c.variables }, p0: c.probabilidad };
  const filas = Object.keys(ETIQ).map((v) => {
    const o = c.variables[v], rg = S.rangos[v] || { min: 0, max: 1 }, esBin = v === 'es_reino_unido';
    const min = Math.min(rg.min, o), max = Math.max(rg.max, o), paso = PASO[v] || 1;
    const campo = h('input', { type: 'number', id: 'n-' + v, value: o, step: esBin ? 1 : paso, min: esBin ? 0 : undefined, 'aria-label': `${ETIQ[v]}, valor` });
    const rango = esBin ? h('input', { type: 'checkbox', id: 'r-' + v, checked: o === 1, 'aria-label': ETIQ[v] }) : h('input', { type: 'range', id: 'r-' + v, min, max, step: paso, value: o, 'aria-label': `${ETIQ[v]}, deslizador` });
    const fila = h('div', { class: 'var-fila', id: 'f-' + v },
      h('label', { for: 'n-' + v }, ETIQ[v], h('small', {}, v)), esBin ? h('div', {}, rango, ' Sí (1) / No (0)') : rango, campo,
      h('span', { class: 'orig' }, `Original: ${num(o, 2)}  ·  rango en los clientes: ${num(rg.min, 2)} a ${num(rg.max, 2)}`));
    const poner_ = (val, desde) => {
      const n = Number(val); if (!Number.isFinite(n)) return;
      S.ysi.vals[v] = n;
      if (desde !== 'campo') campo.value = n;
      if (desde !== 'rango') { if (esBin) rango.checked = n === 1; else rango.value = n; }
      fila.classList.toggle('cambiada', n !== o);
      programarYsi();
    };
    if (esBin) rango.onchange = () => poner_(rango.checked ? 1 : 0, 'rango'); else rango.oninput = () => poner_(rango.value, 'rango');
    campo.oninput = () => poner_(campo.value, 'campo');
    return fila;
  });
  const reset = h('button', { type: 'button', class: 'boton suave', onclick: () => pintarYsi() }, 'Volver a los valores originales');
  pYsi.appendChild(h('div', { class: 'ysi-grid', style: 'margin-top:16px' },
    h('div', { class: 'tarjeta' }, h('header', {}, h('h3', {}, `Las 13 variables del cliente ${c.cliente_id}`), reset), filas),
    h('div', { class: 'col sticky' }, h('div', { class: 'tarjeta', id: 'ysi-res' }, h('p', { class: 'tenue' }, 'Mueve una variable para ver la probabilidad.')))));
  programarYsi(0);
}
function programarYsi(ms = 250) { clearTimeout(temporizadorYsi); temporizadorYsi = setTimeout(predecirYsi, ms); }
async function predecirYsi() {
  const yo = ++tokenYsi, caja = $('#ysi-res'); if (!caja || !S.ysi) return;
  let r;
  try { r = await llamar('predecir_variables', { variables: S.ysi.vals }); } catch (e) { r = { ok: false, resultado: { error: e.message } }; }
  if (yo !== tokenYsi) return;
  vaciar(caja);
  caja.appendChild(h('header', {}, h('h3', {}, 'Probabilidad con tus cambios'), etiquetaOrigen('modelo', 'predecir_variables')));
  if (!r.ok) { caja.appendChild(errorCaja(r.resultado.error)); return; }
  const R = r.resultado, d = (R.probabilidad - S.ysi.p0) * 100;
  const clase = Math.abs(d) < 0.05 ? 'igual' : d > 0 ? 'sube' : 'baja';
  caja.appendChild(medidor(R.probabilidad, { ghost: S.ysi.p0, tramo: R.tramo }));
  caja.appendChild(h('p', {}, tramoChip(R.tramo), ' ', h('span', { class: 'peq tenue' }, `v${R.version_modelo}@${R.alias}`)));
  caja.appendChild(h('p', { style: 'margin-top:8px' }, h('span', { class: 'delta ' + clase }, `${d > 0 ? '+' : ''}${d.toLocaleString('es-ES', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} puntos`),
    h('span', { class: 'tenue' }, ` respecto al original (${pct(S.ysi.p0)})`)));
  caja.appendChild(h('p', { class: 'peq', style: 'margin-top:8px' }, R.recomendacion));
  if (R.aviso) caja.appendChild(h('p', { class: 'nota', style: 'margin-top:8px' }, R.aviso));
  caja.appendChild(h('p', { class: 'peq tenue', style: 'margin-top:10px' }, 'No es un cliente real y la relación no es causal.'));
}

// ------------------------------------------------------------------------------------------------ pestaña 3: Pregunta (chat)
const pPregunta = $('#p-pregunta');
const SUGERENCIAS = ['¿Qué país vende más?', '¿Qué probabilidad tiene el cliente 12369 y por qué?', 'Compara los clientes 12369 y 12425'];
function construirChat() {
  vaciar(pPregunta);
  const entrada = h('textarea', { id: 'chat-texto', rows: 1, placeholder: 'Escribe tu pregunta…', 'aria-label': 'Tu pregunta', onkeydown: (ev) => { if (ev.key === 'Enter' && !ev.shiftKey) { ev.preventDefault(); enviar(entrada.value); } } });
  pPregunta.appendChild(h('div', { class: 'tarjeta chat' },
    h('div', {},
      h('header', {}, h('h2', {}, 'Pregunta a los datos y al modelo'), h('span', { class: 'peq tenue', id: 'chat-llm' })),
      h('div', { class: 'nota', style: 'margin-top:4px' }, h('b', {}, 'Un modelo pequeño se equivoca. '), 'Los números salen de las herramientas MCP, no del LLM: comprueba siempre las llamadas que hay debajo de cada respuesta (máximo 5 pasos por pregunta).'),
      h('div', { id: 'chat-aviso', style: 'margin-top:8px' })),
    h('div', { class: 'mensajes', id: 'mensajes', role: 'log', 'aria-live': 'polite', 'aria-label': 'Conversación' }),
    h('div', { class: 'col', style: 'gap:10px' },
      h('div', { class: 'sugerencias', id: 'sugerencias' }, SUGERENCIAS.map((t) => h('button', { type: 'button', class: 'sugerencia', onclick: () => enviar(t) }, t))),
      h('div', { class: 'entrada' }, entrada, h('button', { type: 'button', class: 'boton primario', id: 'chat-enviar', onclick: () => enviar(entrada.value) }, 'Preguntar'),
        h('button', { type: 'button', class: 'boton suave', onclick: () => { S.hist = []; vaciar($('#mensajes')); bienvenida(); } }, 'Nueva conversación')))));
  bienvenida();
}
function bienvenida() {
  $('#mensajes').appendChild(h('div', { class: 'turno' }, h('div', { class: 'msg-asistente' }, 'Hola. Puedo consultar los datos de ventas (servidor mcp-datos-master) y el modelo de retención (mcp-modelo-retencion). Elige una sugerencia o escribe tu pregunta.')));
}
function pintarEstadoChat() {
  const e = S.estado, caja = $('#chat-aviso'); if (!e || !caja) return;
  vaciar(caja);
  $('#chat-llm').textContent = `LLM: ${e.llm.modelo} en ${e.llm.url}`;
  if (!e.llm.ok) {
    caja.appendChild(h('div', { class: 'nota roja', role: 'alert' }, h('b', {}, 'No hay LLM disponible. '), e.llm.ayuda, ' ',
      h('button', { type: 'button', class: 'boton peq', onclick: refrescarEstado }, 'Volver a comprobar'), ' ',
      h('button', { type: 'button', class: 'boton peq', onclick: abrirAjustes }, 'Cambiar ajustes')));
  }
  const nada = !e.llm.ok || S.ocupado;
  $('#chat-enviar').disabled = nada;
  for (const b of document.querySelectorAll('.sugerencia')) b.disabled = nada;
}
function chipLlamada(ev) {
  const resumenEl = h('summary', {}, h('span', { class: 'srv ' + (ev.servidor || 'sin') }, ev.servidor ? NOMBRE_SRV[ev.servidor] : 'herramienta desconocida'),
    h('span', { class: 'mono' }, ev.herramienta), h('span', { class: 'estado-llamada', 'data-e': '1' }, 'en curso…'));
  const cuerpo = h('div', { class: 'cuerpo-llamada' }, h('b', { class: 'peq' }, 'Argumentos'), h('pre', { class: 'json' }, typeof ev.argumentos === 'string' ? ev.argumentos : json(ev.argumentos)),
    h('b', { class: 'peq', 'data-r': '1' }, 'Resultado'), h('pre', { class: 'json', 'data-res': '1' }, 'Esperando…'));
  return h('details', { class: 'llamada' }, resumenEl, cuerpo);
}
async function enviar(texto) {
  texto = (texto || '').trim();
  if (!texto || S.ocupado) return;
  S.ocupado = true; pintarEstadoChat();
  $('#chat-texto').value = '';
  const caja = $('#mensajes');
  caja.appendChild(h('div', { class: 'msg-usuario' }, texto));
  const burbuja = h('div', { class: 'msg-asistente pendiente' }, 'Pensando…');
  const pasos = h('div', { class: 'pasos' });
  caja.appendChild(h('div', { class: 'turno' }, burbuja, pasos));
  caja.scrollTop = caja.scrollHeight;
  S.hist.push({ role: 'user', content: texto });
  const chips = {};
  let respondido = false;
  const final = (t, clase) => { burbuja.className = 'msg-asistente' + (clase ? ' ' + clase : ''); burbuja.textContent = t; };
  try {
    const r = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ mensajes: S.hist.slice(-12) }) });
    if (!r.ok) throw new Error(`La aplicación rechazó la pregunta (HTTP ${r.status}).`);
    const lector = r.body.getReader(), dec = new TextDecoder();
    let buf = '';
    for (;;) {
      const { value, done } = await lector.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      let i;
      while ((i = buf.indexOf('\n\n')) >= 0) {
        const bloque = buf.slice(0, i); buf = buf.slice(i + 2);
        if (!bloque.startsWith('data: ')) continue;
        const ev = JSON.parse(bloque.slice(6));
        if (ev.tipo === 'paso') burbuja.textContent = `Pensando… (paso ${ev.n} de ${ev.de})`;
        else if (ev.tipo === 'pensamiento') pasos.appendChild(h('div', { class: 'pensamiento' }, 'El modelo dice: ' + ev.texto));
        else if (ev.tipo === 'llamada') { chips[ev.id] = chipLlamada(ev); pasos.appendChild(chips[ev.id]); }
        else if (ev.tipo === 'resultado') {
          const c = chips[ev.id]; if (!c) continue;
          const e = $('[data-e]', c); e.textContent = `${ev.ok ? 'correcta' : 'con error'} · ${ev.ms} ms`; e.className = 'estado-llamada ' + (ev.ok ? 'ok' : 'mal');
          c.classList.toggle('mal', !ev.ok);
          $('[data-res]', c).textContent = json(ev.resultado) + (ev.avisos && ev.avisos.length ? '\n\nAviso: ' + ev.avisos.join(' ') : '');
          if (!ev.ok) c.open = true;
        } else if (ev.tipo === 'final') { final(ev.texto); S.hist.push({ role: 'assistant', content: ev.texto }); respondido = true; }
        else if (ev.tipo === 'limite') { final(ev.texto, 'error'); respondido = true; S.hist.push({ role: 'assistant', content: ev.texto }); }
        else if (ev.tipo === 'error_llm' || ev.tipo === 'error') { final(ev.texto, 'error'); respondido = true; S.hist.pop(); if (ev.tipo === 'error_llm') refrescarEstado(); }
        caja.scrollTop = caja.scrollHeight;
      }
    }
    if (!respondido) final('No llegó ninguna respuesta.', 'error');
  } catch (e) { final(e.message, 'error'); S.hist.pop(); }
  S.ocupado = false; pintarEstadoChat(); caja.scrollTop = caja.scrollHeight;
}
async function abrirAjustes() {
  let cfg = { url: '', modelo: '' };
  try { cfg = await api('/api/ajustes'); } catch (e) { /* se queda en blanco */ }
  const url = h('input', { type: 'text', id: 'aj-url', value: cfg.url, autocomplete: 'off', spellcheck: 'false' });
  const modelo = h('input', { type: 'text', id: 'aj-modelo', value: cfg.modelo, autocomplete: 'off', spellcheck: 'false' });
  const ok = await dialogo({
    titulo: 'Ajustes del LLM',
    cuerpo: h('div', { class: 'rejilla' }, h('p', {}, 'Cualquier servidor con el formato OpenAI «/v1/chat/completions» y herramientas: Ollama (por defecto, puerto 11434) o el Qwen2.5-3B-Instruct Q4 del curso (puerto 11435).'),
      h('label', {}, 'Dirección base', url), h('label', {}, 'Modelo', modelo),
      queNo('Qué no hace', 'No instala ni descarga nada. Se guarda solo mientras la aplicación esté en marcha; para dejarlo fijo usa CURSO_LLM_URL y CURSO_LLM_MODELO.')),
    ok: 'Guardar', alAceptar: () => post('/api/ajustes', { url: url.value.trim(), modelo: modelo.value.trim() }),
  });
  if (ok) await refrescarEstado();
}
$('#b-ajustes').onclick = abrirAjustes;

// ------------------------------------------------------------------------------------------------ pestaña 4: Explorador MCP
const pExpl = $('#p-explorador');
const ATAQUES = [
  ['DROP', 'DROP TABLE master_clientes'], ['UPDATE', "UPDATE master_clientes SET pais = 'Nowhere'"], ['Varias sentencias', 'SELECT 1; DELETE FROM master_clientes'],
  ['Comentario', 'SELECT cliente_id FROM master_clientes -- ver todo'], ['Tabla fs_produccion', 'SELECT * FROM fs_produccion'], ['sqlite_master', 'SELECT name FROM sqlite_master'],
  ['Ruta completa', 'SELECT * FROM main.master_clientes'], ['Coma entre tablas', 'SELECT a.cliente_id FROM master_clientes a, master_facturas b'],
];
const LEGIT = 'SELECT pais, COUNT(*) AS clientes FROM master_clientes GROUP BY pais ORDER BY clientes DESC LIMIT 5';
const CAPAS = [
  [1, 'Herramientas con nombre', 'Lo normal es no escribir SQL: resumen_cliente, ventas_por_pais… Esta herramienta libre es el último recurso.'],
  [2, 'Vigilancia del SQL', 'Solo SELECT, una sentencia, sin comentarios, solo tablas master_*, sin comas entre tablas.'],
  [3, 'Conexión de solo lectura', 'SQLite se abre en modo «ro»; BigQuery tiene un tope de bytes facturables. No depende de la vigilancia.'],
  [4, 'Tope de filas', 'Como máximo 50 filas devueltas. Tampoco depende de las capas anteriores.'],
];
function construirExplorador() {
  const e = S.estado; if (!e) return;
  const todas = Object.entries(e.servidores).flatMap(([k, sv]) => sv.herramientas.map((t) => ({ ...t, servidor: k })));
  if (S.herr && todas.some((t) => t.nombre === S.herr.nombre)) return;
  vaciar(pExpl);
  if (!todas.length) { pExpl.appendChild(h('div', { class: 'vacio' }, 'Ningún servidor MCP en marcha: no hay herramientas que explorar.')); return; }
  S.herr = todas[0];
  const lista = h('div', { class: 'tarjeta' }, h('header', {}, h('h2', {}, 'Herramientas')));
  const caja = h('div', { class: 'herr-lista' });
  for (const k of Object.keys(e.servidores)) {
    caja.appendChild(h('h3', {}, `${NOMBRE_SRV[k]} (${e.servidores[k].herramientas.length})`));
    for (const t of todas.filter((x) => x.servidor === k)) caja.appendChild(h('button', { type: 'button', class: 'herr', 'data-n': t.nombre, 'aria-pressed': String(t.nombre === S.herr.nombre), onclick: () => elegirHerramienta(t) }, t.nombre));
  }
  lista.appendChild(caja);
  pExpl.appendChild(h('div', { class: 'expl-grid' }, lista, h('div', { class: 'tarjeta', id: 'herr-detalle' })));
  pExpl.appendChild(construirSQL());
  elegirHerramienta(S.herr);
}
function valorPrevio(nombre, esquema) {
  if (nombre === 'cliente_id') return S.cid ?? (S.clientes[0] && S.clientes[0].cliente_id) ?? 12369;
  if (nombre === 'variables') { const c = S.clientes.find((x) => x.cliente_id === S.cid) || S.clientes[0]; return json(c ? c.variables : {}); }
  if (nombre === 'tabla') return 'master_clientes';
  return esquema.default;
}
function elegirHerramienta(t) {
  S.herr = t;
  for (const b of pExpl.querySelectorAll('.herr')) b.setAttribute('aria-pressed', String(b.dataset.n === t.nombre));
  const d = vaciar($('#herr-detalle')), props = t.inputSchema.properties || {}, req = t.inputSchema.required || [], campos = {};
  d.appendChild(h('header', {}, h('h2', { class: 'mono' }, t.nombre), h('span', { class: 'srv ' + t.servidor }, NOMBRE_SRV[t.servidor])));
  d.appendChild(h('p', {}, t.descripcion));
  const form = h('form', { class: 'form-herr', onsubmit: (ev) => { ev.preventDefault(); ejecutar(); } });
  const nombres = Object.keys(props);
  if (!nombres.length) form.appendChild(h('p', { class: 'tenue peq' }, 'Esta herramienta no necesita argumentos.'));
  for (const n of nombres) {
    const sc = props[n], previo = valorPrevio(n, sc), id = 'arg-' + n;
    let campo;
    if (sc.type === 'object' || sc.type === 'array') campo = h('textarea', { id, rows: 6 }, typeof previo === 'string' ? previo : json(previo ?? {}));
    else if (sc.type === 'boolean') campo = h('input', { type: 'checkbox', id, checked: !!previo });
    else if (sc.type === 'integer' || sc.type === 'number') campo = h('input', { type: 'number', id, step: sc.type === 'integer' ? 1 : 'any', value: previo ?? '' });
    else campo = h('input', { type: 'text', id, value: previo ?? '', autocomplete: 'off' });
    campos[n] = { campo, sc };
    form.appendChild(h('label', { for: id }, `${n}${req.includes(n) ? ' *' : ''}`, h('small', {}, `${sc.type || 'cualquiera'}${req.includes(n) ? ' · obligatorio' : ' · opcional'}${sc.default !== undefined ? ` · por defecto ${JSON.stringify(sc.default)}` : ''}`), campo));
  }
  form.appendChild(h('div', {}, h('button', { type: 'submit', class: 'boton primario', id: 'b-ejecutar' }, 'Ejecutar')));
  d.appendChild(form);
  d.appendChild(h('div', { id: 'herr-salida', 'aria-live': 'polite' }));
  async function ejecutar() {
    const args = {};
    try {
      for (const [n, { campo, sc }] of Object.entries(campos)) {
        if (sc.type === 'boolean') args[n] = campo.checked;
        else if (campo.value === '') { if (req.includes(n)) args[n] = ''; }
        else if (sc.type === 'integer') args[n] = Number.isInteger(Number(campo.value)) ? Number(campo.value) : campo.value;
        else if (sc.type === 'number') args[n] = Number(campo.value);
        else if (sc.type === 'object' || sc.type === 'array') args[n] = JSON.parse(campo.value);
        else args[n] = campo.value;
      }
    } catch (e) { vaciar($('#herr-salida')).appendChild(errorCaja('Un argumento no es JSON válido: ' + e.message)); return; }
    const out = vaciar($('#herr-salida')); out.appendChild(h('p', { class: 'tenue' }, 'Ejecutando…'));
    try {
      const r = await llamar(t.nombre, args);
      vaciar(out).appendChild(h('div', { class: 'col' }, h('p', { class: 'peq' }, h('span', { class: r.ok ? 'ok-i' : 'mal-i' }, r.ok ? 'Correcta' : 'Con error'), ` · ${r.ms} ms · ${NOMBRE_SRV[r.servidor] || ''}`), h('pre', { class: 'json' }, json(r.resultado))));
    } catch (e) { vaciar(out).appendChild(errorCaja(e.message)); }
  }
}
function construirSQL() {
  const area = h('textarea', { id: 'sql-texto', rows: 4, spellcheck: 'false', 'aria-label': 'Consulta SQL' }, LEGIT);
  const salida = h('div', { id: 'sql-salida', 'aria-live': 'polite' }, h('p', { class: 'tenue' }, 'Escribe una consulta o pulsa un ataque de ejemplo: verás qué capa lo frena y por qué.'));
  const lanzar = (sql) => { area.value = sql; ejecutarSQL(sql, salida); };
  return h('div', { class: 'sql-grid' },
    h('div', { class: 'tarjeta' }, h('header', {}, h('h2', {}, 'SQL con vigilancia'), etiquetaOrigen('datos', 'consulta_sql')),
      h('p', { class: 'peq tenue', style: 'margin-bottom:8px' }, 'Un LLM que escribe SQL libre es potente y peligroso. Pulsa un ataque y mira dónde se queda.'),
      area, h('div', { style: 'margin:8px 0' }, h('button', { type: 'button', class: 'boton primario', onclick: () => ejecutarSQL(area.value, salida) }, 'Ejecutar consulta')),
      h('p', { class: 'peq', style: 'margin:6px 0 4px' }, h('b', {}, 'Ataques de ejemplo')),
      h('div', { class: 'ataques' }, ATAQUES.map(([t, q]) => h('button', { type: 'button', class: 'ataque', title: q, onclick: () => lanzar(q) }, t)),
        h('button', { type: 'button', class: 'ataque legit', title: LEGIT, onclick: () => lanzar(LEGIT) }, 'Consulta legítima'))),
    h('div', { class: 'tarjeta' }, h('header', {}, h('h3', {}, 'Qué capa lo frena')), salida));
}
function capaDe(r) {
  const x = r.resultado || {};
  if (x.rechazada_por) return 2;
  if (x.error && /readonly|read-only|attempt to write|solo lectura/i.test(x.error)) return 3;
  if (r.ok && x.truncado) return 4;
  return 0;
}
async function ejecutarSQL(sql, salida) {
  vaciar(salida).appendChild(h('p', { class: 'tenue' }, 'Ejecutando…'));
  let r;
  try { r = await llamar('consulta_sql', { sql }); } catch (e) { vaciar(salida).appendChild(errorCaja(e.message)); return; }
  const capa = capaDe(r), x = r.resultado;
  vaciar(salida);
  if (capa) salida.appendChild(h('div', { class: 'veredicto frenado', role: 'status' }, h('b', {}, `Frenada por la capa ${capa}: ${CAPAS[capa - 1][1]}`), x.error || 'La consulta devolvió el tope de filas.'));
  else if (r.ok) salida.appendChild(h('div', { class: 'veredicto paso', role: 'status' }, h('b', {}, 'Consulta aceptada'), `Devolvió ${x.n} fila(s) del motor ${x.motor}. Solo lee tablas master_*.`));
  else salida.appendChild(h('div', { class: 'veredicto frenado', role: 'status' }, h('b', {}, 'El motor rechazó la consulta'), x.error));
  salida.appendChild(h('ol', { class: 'capas', style: 'margin-top:10px' }, CAPAS.map(([n, t, d]) => h('li', { class: n === capa ? 'activa' : '' }, h('span', { class: 'n' }, String(n)), h('span', {}, h('b', {}, t + '. '), d)))));
  salida.appendChild(h('pre', { class: 'json', style: 'margin-top:10px' }, json(x)));
}

// ------------------------------------------------------------------------------------------------ pestaña 5: Modelo
const pModelo = $('#p-modelo');
function pintarModelo() {
  const e = S.estado; vaciar(pModelo); if (!e) return;
  const mo = e.modelo, reg = mo.registro;
  if (!reg) { pModelo.appendChild(errorCaja(mo.error || 'No se pudo leer el registro de MLflow.')); return; }
  const champ = mo.alias_champion;
  const actual = reg.versiones.find((v) => v.version === champ);
  const puedeVolver = !!(actual && actual.champion_anterior);
  const tabla = h('div', { class: 'tabla-scroll' }, h('table', {}, h('caption', { class: 'peq tenue', style: 'text-align:left;padding:6px 12px' }, `Modelo registrado «${reg.nombre}»: ${reg.versiones.length} versiones`),
    h('thead', {}, h('tr', {}, h('th', {}, 'Versión'), h('th', {}, 'Alias'), h('th', { class: 'num' }, 'AUC valid'), h('th', { class: 'num' }, 'AUC test'), h('th', {}, 'Recuerda a'), h('th', {}, 'Acción'))),
    h('tbody', {}, reg.versiones.map((v) => h('tr', {}, h('td', { class: 'mono' }, 'v' + v.version), h('td', {}, v.alias.length ? v.alias.map((a) => h('span', { class: 'badge-alias' }, '@' + a)) : h('span', { class: 'tenue' }, '—')),
      h('td', { class: 'num' }, auc(v.valid_auc)), h('td', { class: 'num' }, auc(v.test_auc)), h('td', {}, v.champion_anterior ? 'v' + v.champion_anterior : '—'),
      h('td', {}, h('button', { type: 'button', class: 'boton peq', disabled: v.version === champ, onclick: () => promover(v.version) }, v.version === champ ? 'Es champion' : `Promover v${v.version}`)))))));
  const cm = S.cambioModelo;
  const resultado = cm ? h('div', { class: 'tarjeta' }, h('header', {}, h('h3', {}, 'Qué cambió al mover el alias'), etiquetaOrigen('modelo', 'predecir_cliente')),
    h('p', { class: 'peq tenue', style: 'margin-bottom:8px' }, `${cm.titulo} · cliente ${cm.cliente}. Sin reiniciar ningún servidor.`),
    h('div', { class: 'antes-despues' },
      h('div', {}, h('div', { class: 'peq tenue' }, 'Antes'), h('div', { class: 'grande' }, cm.antes ? `v${cm.antes.version_modelo}` : 'sin alias'), h('div', {}, cm.antes ? pct(cm.antes.probabilidad) : '—')),
      h('div', {}, h('div', { class: 'peq tenue' }, 'Ahora'), h('div', { class: 'grande' }, cm.despues ? `v${cm.despues.version_modelo}` : '—'), h('div', {}, cm.despues ? pct(cm.despues.probabilidad) : '—'))),
    h('p', { class: 'nota azul', style: 'margin-top:10px' }, cm.antes && cm.despues
      ? (cm.antes.version_modelo !== cm.despues.version_modelo ? `Cambió la VERSIÓN que responde (v${cm.antes.version_modelo} → v${cm.despues.version_modelo}). ` : 'La versión que responde no cambió. ')
        + (cm.antes.probabilidad === cm.despues.probabilidad ? 'La probabilidad es idéntica: según el curso, las versiones se entrenaron con los mismos datos (sin verificar aquí versión a versión).' : 'La probabilidad es distinta.')
      : 'Ahora el modelo ya responde por el alias.'))
    : h('div', { class: 'tarjeta' }, h('header', {}, h('h3', {}, 'Qué cambia al mover el alias')),
      h('p', { class: 'tenue' }, 'Promueve o vuelve atrás y aquí verás qué versión responde antes y después, sin reiniciar el servidor MCP del modelo.'));
  pModelo.appendChild(h('div', { class: 'modelo-grid' },
    h('div', { class: 'col' }, h('div', { class: 'tarjeta' },
      h('header', {}, h('h2', {}, 'Versiones del modelo'), etiquetaOrigen('modelo', 'modelo_en_uso')),
      h('div', { class: 'nota azul', style: 'margin-bottom:10px' }, champ ? h('span', {}, 'El alias ', h('b', {}, '@champion'), ` apunta a la versión v${champ}. El servidor MCP del modelo pregunta al registro en cada llamada y recarga si cambió.`)
        : h('span', {}, h('b', {}, 'Sin alias champion: '), 'el MCP del modelo no puede predecir hasta que promuevas una versión.')),
      tabla,
      h('div', { style: 'display:flex;flex-wrap:wrap;gap:8px;margin-top:12px' },
        !champ ? h('button', { type: 'button', class: 'boton primario', onclick: () => promover(mo.ultima_version) }, `Promover la v${mo.ultima_version} a champion`) : null,
        h('button', { type: 'button', class: 'boton', disabled: !puedeVolver, title: puedeVolver ? '' : 'La versión champion no recuerda una anterior', onclick: volver }, puedeVolver ? `Volver a la v${actual.champion_anterior}` : 'Volver a la anterior (no hay)')))),
    h('div', { class: 'col' }, resultado, h('div', { class: 'tarjeta' }, h('h3', {}, 'Lo que el alias gobierna y lo que no'),
      h('p', { class: 'peq tenue', style: 'margin-top:6px' }, 'Mover @champion gobierna el registro y a quien cargue models:/retencion-90d@champion, como este MCP. No cambia por sí solo la API Docker ya desplegada: esa copió su modelo al construirse. No se borra nada: las versiones siguen registradas.')))));
}
async function referenciaPrediccion(ref) {
  try { const r = await llamar('predecir_cliente', { cliente_id: ref }); return r.ok ? r.resultado : null; } catch (e) { return null; }
}
function clienteRef() { return S.cid ?? (S.clientes[0] && S.clientes[0].cliente_id) ?? 12369; }
async function promover(version) {
  const e = S.estado, champ = e && e.modelo.alias_champion, ref = clienteRef();
  let respuestaApi;
  const hecho = await dialogo({
    titulo: champ ? `Promover la v${version} a champion` : `Promover la v${version} a champion (primer alias)`,
    cuerpo: h('div', { class: 'rejilla' },
      queSi('Qué pasa', champ ? `El alias @champion pasa de la v${champ} a la v${version} en el registro de MLflow.` : `Se crea el alias @champion apuntando a la v${version} (no había ninguno).`,
        'El servidor MCP del modelo lo detecta en su siguiente llamada y recarga solo, sin reiniciarse.', champ ? `La v${version} anota que antes mandaba la v${champ}, para poder volver.` : 'Como no había champion anterior, no se guarda a dónde volver.'),
      queNo('Qué NO pasa', 'No se borra ninguna versión ni se reentrena nada.', 'No cambia la API Docker ya desplegada (copió su modelo al construirse).', 'Esto escribe en el registro de MLflow de 04-Proyecto-Base.')),
    ok: `Promover la v${version}`,
    alAceptar: async () => { const antes = champ ? await referenciaPrediccion(ref) : null; respuestaApi = await post('/api/modelo/promover', { version }); const despues = await referenciaPrediccion(ref); S.cambioModelo = { titulo: `Promovida la v${version}`, cliente: ref, antes, despues }; },
  });
  if (hecho) await tras();
}
async function volver() {
  const e = S.estado, actual = e.modelo.registro.versiones.find((v) => v.version === e.modelo.alias_champion), ref = clienteRef();
  const hecho = await dialogo({
    titulo: `Volver a la v${actual.champion_anterior}`,
    cuerpo: h('div', { class: 'rejilla' },
      queSi('Qué pasa', `@champion vuelve de la v${actual.version} a la v${actual.champion_anterior} (rollback).`, 'El servidor MCP del modelo recarga solo en su siguiente llamada.'),
      queNo('Qué NO pasa', `La v${actual.version} no se borra: sigue registrada.`, 'No cambia la API Docker ya desplegada.')),
    ok: `Volver a la v${actual.champion_anterior}`,
    alAceptar: async () => { const antes = await referenciaPrediccion(ref); await post('/api/modelo/volver'); const despues = await referenciaPrediccion(ref); S.cambioModelo = { titulo: `Vuelta atrás a la v${actual.champion_anterior}`, cliente: ref, antes, despues }; },
  });
  if (hecho) await tras();
}
async function tras() {
  await refrescarEstado(); irA('modelo'); await cargarClientes(false);
}

// ------------------------------------------------------------------------------------------------ pestaña 6: Lote (Airflow / Cloud Composer)
// Lanza el DAG retencion_lote por la API REST de Airflow y sigue el run. No simula nada: si Airflow no responde, lo dice.
const pLote = $('#p-lote');
const LT = { cfg: null, estado: null, run: null, runId: null, log: null, historial: [], resultado: null, errorRun: null, timer: null, construido: false, form: { corte: '', imagen: '', capacidad: '0.10', huella: '' } };
const ESTADO_TXT = { success: 'Correcta', failed: 'Fallida', running: 'En curso', queued: 'En cola', upstream_failed: 'No llegó a ejecutarse', skipped: 'Saltada', null: 'Pendiente' };
const ESTADO_CLASE = { success: 'ok', failed: 'mal', upstream_failed: 'mal', running: 'curso', queued: 'curso', skipped: 'pend', null: 'pend' };
const chipEstado = (e) => h('span', { class: 'chip-estado ' + (ESTADO_CLASE[e] || 'pend') }, ESTADO_TXT[e] || String(e));

async function abrirLote() {
  if (!LT.construido) construirLote();
  await refrescarLote();
  if (LT.runId && !(LT.run && LT.run.final)) sondearRun();
}
function pararSondeoLote() { clearTimeout(LT.timer); LT.timer = null; }

async function refrescarLote() {
  const [cfg, est, hist, res] = await Promise.all([
    api('/api/lote/config').catch(() => null), api('/api/lote/estado').catch((e) => ({ ok: false, error: e.message })),
    api('/api/lote/historial').catch(() => ({ runs: [], error: true })), api('/api/lote/resultado').catch(() => null)]);
  LT.cfg = cfg; LT.estado = est; LT.historial = (hist && hist.runs) || []; LT.resultado = res;
  if (cfg && !LT.form.imagen && cfg.imagen_defecto) LT.form.imagen = cfg.imagen_defecto;
  pintarLoteConexion(); pintarLoteHistorial(); pintarLoteResultado(); pintarLoteRun();
  const imagen = $('#lote-imagen'); if (imagen && !imagen.value) imagen.value = LT.form.imagen;
}

function construirLote() {
  LT.construido = true; vaciar(pLote);
  const campo = (id, etiqueta, ayuda, attrs) => h('div', { class: 'campo' }, h('label', { for: id }, etiqueta), h('input', { id, class: 'entrada', autocomplete: 'off', spellcheck: 'false', ...attrs }), h('span', { class: 'peq tenue' }, ayuda));
  const form = h('form', { class: 'campos', id: 'lote-form', onsubmit: (ev) => { ev.preventDefault(); pedirLanzar(); } },
    campo('lote-corte', 'Fecha de corte', 'AAAA-MM-DD. Vacío = el día siguiente a la última factura.', { placeholder: '2011-12-10', inputmode: 'numeric', maxlength: '10' }),
    campo('lote-imagen', 'Imagen del lote', 'registro/ruta:etiqueta. Vacío = la que tenga el DAG por defecto.', { placeholder: 'retencion-lote:local' }),
    campo('lote-capacidad', 'Capacidad de la campaña', 'Fracción de clientes a los que llega (0,10 = el 10 %).', { type: 'number', min: '0.01', max: '1', step: '0.01', value: '0.10' }),
    campo('lote-huella', 'Huella de datos exigida (opcional)', 'Si la rellenas, el lote falla si el modelo de la imagen tiene otra.', { placeholder: '35a94deb4e04ab4a' }),
    h('div', { class: 'acciones-lote' }, h('button', { type: 'submit', class: 'boton primario', id: 'lote-lanzar' }, 'Lanzar el lote'), h('span', { class: 'peq tenue', id: 'lote-lanzar-nota' })));
  pLote.appendChild(h('div', { class: 'lote-grid' },
    h('div', { class: 'col' },
      h('div', { class: 'tarjeta', id: 'lote-conexion' }),
      h('div', { class: 'tarjeta' }, h('header', {}, h('h2', {}, 'Lanzar el lote')), form),
      h('div', { class: 'tarjeta', id: 'lote-resultado' })),
    h('div', { class: 'col' },
      h('div', { class: 'tarjeta', id: 'lote-run' }),
      h('div', { class: 'tarjeta', id: 'lote-historial' }))));
  for (const [id, k] of [['lote-corte', 'corte'], ['lote-imagen', 'imagen'], ['lote-capacidad', 'capacidad'], ['lote-huella', 'huella']]) $('#' + id).oninput = (ev) => { LT.form[k] = ev.target.value; };
}

function pintarLoteConexion() {
  const c = vaciar($('#lote-conexion')), cfg = LT.cfg, e = LT.estado || {};
  const ok = !!e.ok;
  c.appendChild(h('header', {}, h('h2', {}, 'Airflow'), h('span', { class: 'chip-estado ' + (ok ? 'ok' : 'mal') }, ok ? `Conectado · API ${e.api}` : 'Sin conexión'),
    h('button', { type: 'button', class: 'boton suave peq', onclick: refrescarLote }, 'Comprobar de nuevo')));
  const fila = (k, v) => h('div', { class: 'fila-cfg' }, h('span', { class: 'tenue' }, k), h('span', { class: 'mono' }, v));
  if (cfg) {
    const cred = cfg.credenciales;
    c.appendChild(h('div', { class: 'cfg' },
      fila('AIRFLOW_URL', cfg.url_definida ? cfg.url : '(sin definir)'),
      fila('AIRFLOW_AUTH', cfg.auth),
      fila('DAG', cfg.dag),
      fila('Credenciales en el entorno', cfg.auth === 'basic' ? `usuario ${cred.usuario ? 'sí' : 'NO'} · clave ${cred.clave ? 'sí' : 'NO'}` : cfg.auth === 'token' ? `token ${cred.token ? 'sí' : 'NO'}` : cfg.auth === 'google' ? 'las de gcloud / Google (no se guardan aquí)' : 'ninguna')));
    c.appendChild(h('p', { class: 'peq tenue', style: 'margin-top:8px' }, 'Los secretos se leen de variables de entorno del proceso: esta página no los pide, no los guarda y no los muestra.'));
  }
  if (!ok) {
    c.appendChild(h('p', { class: 'nota roja', role: 'alert', style: 'margin-top:10px' }, e.error || 'No se pudo hablar con Airflow.'));
    c.appendChild(h('p', { class: 'nota azul', style: 'margin-top:8px' }, (e.como_arrancarlo || (cfg && cfg.como_arrancarlo) || '')));
    c.appendChild(h('p', { class: 'peq tenue', style: 'margin-top:8px' }, 'No hay ninguna simulación: sin Airflow no se lanza nada.'));
  } else if (e.en_pausa) {
    c.appendChild(h('p', { class: 'nota', style: 'margin-top:10px' }, `El DAG «${e.dag}» está en pausa: un run nuevo se quedaría en cola. Reactívalo con «airflow dags unpause ${e.dag}».`));
  }
  const boton = $('#lote-lanzar'), nota = $('#lote-lanzar-nota');
  if (boton) { boton.disabled = !ok || !!e.en_pausa || !!LT.lanzando; nota.textContent = !ok ? 'Necesita un Airflow en marcha.' : e.en_pausa ? 'El DAG está en pausa.' : ''; }
}

function cuerpoLote() {
  return { corte: LT.form.corte.trim(), imagen: LT.form.imagen.trim(), capacidad: parseFloat(String(LT.form.capacidad).replace(',', '.')) || 0.1, huella_esperada: LT.form.huella.trim() };
}
function pedirLanzar() {
  const b = cuerpoLote(), cfg = LT.cfg || {};
  if (b.corte && !/^\d{4}-\d{2}-\d{2}$/.test(b.corte)) { LT.errorRun = 'La fecha de corte debe ser AAAA-MM-DD (o estar vacía).'; pintarLoteRun(); return; }
  LT.errorRun = null;
  const cuerpo = h('div', { class: 'dlg-lote' },
    h('p', {}, h('b', {}, `Corte ${b.corte || '(el día siguiente a la última factura)'}`), ' · ', `imagen ${b.imagen || '(la del DAG)'}`, ' · ', `capacidad ${b.capacidad}`),
    queSi('Esto lanza',
      `Un run del DAG «${cfg.dag}» en ${cfg.url || 'tu Airflow'} (se ve en su interfaz y queda en su historial).`,
      'Un contenedor con la imagen indicada que ejecuta  python -m ia_mlops.explotacion  y puntúa a TODOS los clientes (el uso de recursos y el coste son los de ese Airflow).',
      'Una validación de la salida (filas, probabilidades entre 0 y 1, tramos) y un resumen en el registro.'),
    queNo('Esto no hace',
      'No entrena ni cambia el modelo, ni mueve el alias @champion, ni toca models/referencia.json.',
      'No escribe fs_produccion (el DAG usa --sin-guardar-fs) ni despliega nada.',
      'No envía la lista de la campaña a nadie: el resultado se queda en el contenedor y en el registro de la tarea «resumir».'));
  dialogo({ titulo: '¿Lanzar el lote?', cuerpo, ok: 'Lanzar el lote', cancelar: 'Cancelar', alAceptar: async () => {
    const r = await post('/api/lote/lanzar', { ...b, confirmado: true });
    LT.runId = r.run_id; LT.run = null; LT.log = null; LT.errorRun = null;
  } }).then((si) => { if (si) { pintarLoteRun(); sondearRun(); } });
}

async function sondearRun() {
  clearTimeout(LT.timer);
  if (!LT.runId || S.tab !== 'lote') return;
  try {
    LT.run = await api('/api/lote/run/' + encodeURIComponent(LT.runId)); LT.errorRun = null;
  } catch (e) { LT.errorRun = e.message; }
  pintarLoteRun();
  if (LT.run && LT.run.final) { refrescarLoteTrasFin(); return; }
  LT.timer = setTimeout(sondearRun, 1500);
}
async function refrescarLoteTrasFin() {
  const [hist, res] = await Promise.all([api('/api/lote/historial').catch(() => ({ runs: [] })), api('/api/lote/resultado').catch(() => null)]);
  LT.historial = hist.runs || []; LT.resultado = res; pintarLoteHistorial(); pintarLoteResultado();
}

function pintarLoteRun() {
  const c = vaciar($('#lote-run'));
  c.appendChild(h('header', {}, h('h2', {}, 'Estado del run'), LT.run ? chipEstado(LT.run.estado) : null));
  if (LT.errorRun) c.appendChild(h('p', { class: 'nota roja', role: 'alert', style: 'margin-bottom:10px' }, LT.errorRun));
  if (!LT.runId) { c.appendChild(h('p', { class: 'tenue' }, 'Todavía no has lanzado ningún lote desde esta página. Al lanzarlo verás aquí cada tarea del DAG según avanza.')); return; }
  const r = LT.run;
  c.appendChild(h('p', { class: 'peq' }, 'Run ', h('span', { class: 'mono' }, LT.runId), r && r.segundos != null ? ` · ${r.segundos} s` : '',
    r && r.enlace ? [' · ', h('a', { href: r.enlace, target: '_blank', rel: 'noopener noreferrer' }, 'Abrir en Airflow (registros completos)')] : ''));
  if (!r) { c.appendChild(h('p', { class: 'tenue', style: 'margin-top:8px' }, 'Esperando la primera respuesta de Airflow…')); return; }
  c.appendChild(h('ol', { class: 'tareas', 'aria-label': 'Tareas del DAG' }, r.tareas.map((t) => h('li', {}, h('span', { class: 'mono' }, t.tarea), chipEstado(t.estado),
    t.estado && t.estado !== 'upstream_failed' ? h('button', { type: 'button', class: 'boton suave peq', onclick: () => verLog(t.tarea, t.intento || 1) }, 'Ver registro') : null))));
  if (r.estado === 'failed') c.appendChild(h('p', { class: 'nota roja', style: 'margin-top:10px' }, 'El run falló. Abre el registro de la tarea en rojo: ahí está el motivo (imagen que no baja, salida no válida…).'));
  if (r.estado === 'success') c.appendChild(h('p', { class: 'nota azul', style: 'margin-top:10px' }, 'El run terminó bien. El resumen del lote está en el registro de la tarea «resumir».'));
  if (LT.log) c.appendChild(h('div', { style: 'margin-top:10px' }, h('b', { class: 'peq' }, `Registro de ${LT.log.tarea}`), h('pre', { class: 'log-lote', tabindex: '0' }, LT.log.texto || '(vacío)')));
}
async function verLog(tarea, intento) {
  try { LT.log = await api(`/api/lote/log/${encodeURIComponent(LT.runId)}/${encodeURIComponent(tarea)}?intento=${intento}`); LT.errorRun = null; } catch (e) { LT.errorRun = e.message; }
  pintarLoteRun();
}

function pintarLoteHistorial() {
  const c = vaciar($('#lote-historial'));
  c.appendChild(h('header', {}, h('h2', {}, 'Historial de ejecuciones'), h('span', { class: 'peq tenue' }, 'últimas 10, las que Airflow tiene')));
  if (!LT.historial.length) { c.appendChild(h('p', { class: 'tenue' }, LT.estado && LT.estado.ok ? 'Airflow no tiene ninguna ejecución de este DAG.' : 'Sin conexión con Airflow: no hay historial que mostrar.')); return; }
  c.appendChild(h('div', { class: 'tabla-scroll' }, h('table', {}, h('thead', {}, h('tr', {}, h('th', {}, 'Run'), h('th', {}, 'Corte'), h('th', {}, 'Estado'), h('th', { class: 'num' }, 'Duración'))),
    h('tbody', {}, LT.historial.map((r) => h('tr', {}, h('td', { class: 'mono' }, h('a', { href: r.enlace, target: '_blank', rel: 'noopener noreferrer' }, r.run_id)), h('td', {}, r.corte), h('td', {}, chipEstado(r.estado)), h('td', { class: 'num' }, r.segundos == null ? '—' : r.segundos + ' s')))))));
}

function pintarLoteResultado() {
  const c = vaciar($('#lote-resultado')), r = LT.resultado;
  c.appendChild(h('header', {}, h('h2', {}, 'Último lote en este equipo'), h('span', { class: 'peq tenue' }, 'lee reports/campana')));
  if (!r || !r.disponible) { c.appendChild(h('p', { class: 'tenue' }, (r && r.motivo) || 'No se pudo leer reports/campana.')); return; }
  const t = r.tramos;
  c.appendChild(h('div', { class: 'cifras' },
    h('div', {}, h('div', { class: 'peq tenue' }, 'Clientes puntuados'), h('div', { class: 'grande' }, num(r.clientes, 0))),
    h('div', {}, h('div', { class: 'peq tenue' }, 'En la campaña'), h('div', { class: 'grande' }, num(r.en_campana, 0))),
    h('div', {}, h('div', { class: 'peq tenue' }, 'Probabilidad media'), h('div', { class: 'grande' }, r.probabilidad_media == null ? '—' : num(r.probabilidad_media, 3)))));
  if (t) c.appendChild(h('p', { style: 'margin-top:10px' }, 'Tramos de negocio: ', h('span', { class: 'tramo alta' }, `alta ${t.alta}`), ' ', h('span', { class: 'tramo media' }, `media ${t.media}`), ' ', h('span', { class: 'tramo baja' }, `baja ${t.baja}`)));
  c.appendChild(h('p', { class: 'peq tenue', style: 'margin-top:8px' }, `Archivo ${r.archivo} · corte ${r.corte} · generado ${r.generado_en} · modelo ${r.modelo} (huella ${r.huella_datos}).`));
  c.appendChild(h('p', { class: 'nota azul', style: 'margin-top:8px' }, 'Es el último archivo que hay en esta carpeta, no necesariamente el de la ejecución de arriba: el lote de Composer o de Docker deja su salida dentro de su contenedor. Compara la fecha «generado» con la hora del run.'));
}

// ------------------------------------------------------------------------------------------------ traza lateral
const lista = $('#traza-lista'), vistos = new Set();
function filaTraza(t) {
  const mal = !t.ok;
  return h('li', {}, h('details', {},
    h('summary', {}, h('span', { class: 'hora' }, t.hora), h('span', { class: 'srv ' + (t.servidor === 'datos' ? 'datos' : t.servidor === 'modelo' ? '' : 'sin') }, t.servidor), h('span', { class: 'herr-n', title: t.herramienta }, t.herramienta),
      h('span', { class: 'ms' }, `${t.ms} ms `, h('span', { class: mal ? 'mal-i' : 'ok-i', 'aria-label': mal ? 'con error' : 'correcta' }, mal ? '✕ error' : '✓ ok')),
      h('span', { class: 'res' + (mal ? ' mal' : '') }, t.resumen)),
    h('div', { class: 'detalle' }, h('b', { class: 'peq' }, `Argumentos · origen: ${t.origen}`), h('pre', { class: 'json' }, json(t.argumentos)), h('b', { class: 'peq' }, 'Resultado'), h('pre', { class: 'json' }, json(t.resultado)))));
}
async function sondearTraza() {
  if (document.hidden) return;
  try {
    const d = await api('/api/traza?desde=' + S.trazaUltimo);
    if (d.ultimo_id < S.trazaUltimo) { vaciar(lista); vistos.clear(); S.trazaUltimo = 0; }
    for (const t of d.items) { if (vistos.has(t.id)) continue; vistos.add(t.id); lista.insertBefore(filaTraza(t), lista.firstChild); }
    if (d.items.length) S.trazaUltimo = d.ultimo_id;
    while (lista.children.length > 200) lista.removeChild(lista.lastChild);
    $('#n-traza').textContent = String(d.ultimo_id);
  } catch (e) { /* la app puede estar parada */ }
}
function trazaAbrir(si) {
  $('#traza').hidden = !si; $('#b-traza').setAttribute('aria-expanded', String(si));
  if (S.barras && $('#barras')) setTimeout(() => barrasPorQue(S.barras, $('#barras')), 50);
}
$('#b-traza').onclick = () => trazaAbrir($('#traza').hidden);
$('#traza-cerrar').onclick = () => { trazaAbrir(false); $('#b-traza').focus(); };
$('#traza-limpiar').onclick = async () => { await post('/api/traza/limpiar'); vaciar(lista); vistos.clear(); };

// ------------------------------------------------------------------------------------------------ arranque
async function iniciar() {
  construirCliente(); construirChat(); pintarDetalleVacio(); pintarLista();
  trazaAbrir(window.innerWidth >= 1280);
  await refrescarEstado();
  irA('cliente');
  cargarClientes(false);
  sondearTraza();
  setInterval(sondearTraza, 1500);
  setInterval(refrescarEstado, 20000);
}
iniciar();
