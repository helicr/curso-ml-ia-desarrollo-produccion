"""Genera la presentación «Extra de S5: Destilación de modelos en notebooks» (index.html, junto a este archivo).

Qué cuenta: un laboratorio para replicar paso a paso. Un modelo profesor, ya entrenado, enseña a un estudiante más pequeño con etiquetas
blandas (distribuciones con temperatura). Ocho notebooks en CPU: la v1 (00-05: MNIST y sentimiento con DistilBERT como profesor) y la v2
(06-07: TinyBERT como estudiante, y la decisión de promoción). Mensaje: destilar ayuda cuando el profesor merece copiarse y el estudiante
parte de un buen punto de partida; lo decide medir calidad y latencia a la vez, no solo la exactitud.

TODO lo que se enseña se LEE de esta carpeta, nada se transcribe a mano: el código y las salidas, de los .ipynb (que se ejecutaron una vez
en CPU, con sus salidas guardadas; aquí NO se vuelven a ejecutar); las cifras, de resultados/*.json; las órdenes, del README y de scripts/;
los tiempos, de la metadata de ejecución de cada celda guardada en los .ipynb; y las figuras, de resultados/*.png (capturas reales de lo que
producen los notebooks), convertidas a img/*.webp con Pillow.

El visor (CSS y JavaScript: ← → · O índice · S notas · F pantalla completa · Esc · botón ⧉ «Copiar todo» · lupa con zoom al clic ·
pie «x / total») es el MISMO que el de los otros extras de S5, copiado aquí (no se importa); solo cambia el rótulo del pie.

Uso:  python generar.py              escribe index.html (y convierte las figuras a img/ si faltan)
      python generar.py --comprobar  no escribe; sale con 1 si index.html no está al día
"""
import argparse
import datetime as dt
import html
import json
import re
import sys
import textwrap
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / 'index.html'
NB_DIR = AQUI / 'notebooks'
RES = AQUI / 'resultados'
IMG = AQUI / 'img'

TOTAL_MIN = 124
PROXY_EJEMPLO = 'http://proxy.miempresa.example:8080'     # marcador genérico: el README usa otro nombre de ejemplo, aquí se sustituye
PROXY_README = 'http://proxy.empresa:8080'

PARTES = {'A': 'La idea', 'B': 'Preparación', 'C': 'v1 · 00-05', 'D': 'v2 · 06-07', 'E': 'Producción', 'F': 'Límites'}
NOMBRES_PARTE = {'A': 'Qué es destilar', 'B': 'Requisitos y preparación', 'C': 'v1: MNIST y sentimiento (notebooks 00-05)',
                 'D': 'v2: TinyBERT (notebooks 06-07)', 'E': 'De los notebooks a producción', 'F': 'Límites y cierre'}


# ------------------------------------------------------------------------------------------------------------------------
# Lectura de la fuente (notebooks, resultados, README, scripts): única fuente de código, salidas y cifras
# ------------------------------------------------------------------------------------------------------------------------
_CACHE = {}


def _ruta_nb(n):
    r = sorted(NB_DIR.glob(f'{n}-*.ipynb'))
    assert len(r) == 1, f'no encuentro el notebook {n}'
    return r[0]


def _nb_json(n):
    if n not in _CACHE:
        _CACHE[n] = json.loads(_ruta_nb(n).read_text(encoding='utf-8'))
    return _CACHE[n]


def _celdas(n):
    return _nb_json(n)['cells']


def _txt(x):
    return ''.join(x) if isinstance(x, list) else x


def fuente_celda(n, i):
    return _txt(_celdas(n)[i]['source'])


def salida_celda(n, i):
    partes = []
    for o in _celdas(n)[i].get('outputs', []):
        t = _txt(o['text']) if 'text' in o else _txt(o.get('data', {}).get('text/plain', ''))
        partes.append(t if t.endswith('\n') else t + '\n')
    return ''.join(partes).strip('\n')


def buscar(n, marca, tipo='code'):
    """Índice de la primera celda del notebook n cuyo texto contiene `marca` (así no se fijan números de celda a mano)."""
    for i, c in enumerate(_celdas(n)):
        if c['cell_type'] == tipo and marca in _txt(c['source']):
            return i
    raise KeyError(f'{n}: no hay celda {tipo} con «{marca}»')


def cod(n, marca):
    return fuente_celda(n, buscar(n, marca))


def sal(n, marca):
    return salida_celda(n, buscar(n, marca))


def trozo(texto, desde, hasta=None):
    """Líneas desde la primera que contiene `desde` hasta la anterior a la primera posterior que contiene `hasta` (o el final)."""
    lineas = texto.split('\n')
    ini = next(k for k, l in enumerate(lineas) if desde in l)
    fin = len(lineas)
    if hasta is not None:
        fin = next(k for k in range(ini + 1, len(lineas)) if hasta in lineas[k])
    return textwrap.dedent('\n'.join(lineas[ini:fin])).rstrip()


def lineas_con(texto, patron):
    return '\n'.join(l.rstrip() for l in texto.split('\n') if re.search(patron, l))


def quitar_comentarios(texto):
    return '\n'.join(re.sub(r'\s{2,}#.*$', '', l) for l in texto.split('\n'))


def R(nombre):
    return json.loads((RES / f'{nombre}.json').read_text(encoding='utf-8'))


def readme():
    return (AQUI / 'README.md').read_text(encoding='utf-8')


def bloque_readme(titulo_antes, lenguaje, ocurrencia=0):
    """Contenido del bloque ```lenguaje que sigue (la `ocurrencia`-ésima vez) al texto `titulo_antes` del README."""
    t = readme()
    ini = t.index(titulo_antes)
    bloques = re.findall(r'```' + lenguaje + r'\n(.*?)```', t[ini:], re.S)
    return bloques[ocurrencia].rstrip('\n')


def lineas_cmd(texto):
    return [l for l in texto.split('\n')]


PAQUETES_VERSIONES = [('numpy', 'numpy'), ('pandas', 'pandas'), ('scikit-learn', 'sklearn'), ('torch', 'torch'), ('torchvision', 'torchvision'),
                      ('transformers', 'transformers'), ('datasets', 'datasets'), ('accelerate', 'accelerate')]


def versiones_nb00(reqs):
    """Filas (paquete, versión pinada, versión que imprimió el notebook 00, coincide) leídas de la tabla guardada del notebook 00."""
    texto = sal('00', 'tabla_entorno = comprobar_entorno()')
    nombres, detalles, en_detalle = {}, {}, False
    for l in texto.split('\n'):
        if l.strip() == 'detalle':
            en_detalle = True
            continue
        if not en_detalle:
            m = re.match(r'^\s*(\d+)\s{2,}(\S.*?)\s{2,}(True|False)\s+(True|False)', l)
            if m:
                nombres[m.group(1)] = m.group(2)
        else:
            m = re.match(r'^\s*(\d+)\s{2,}(\S.*)$', l)
            if m:
                detalles[m.group(1)] = m.group(2)
    por_nombre = {nombres[i]: detalles[i] for i in nombres if i in detalles}
    filas = []
    for pin, nb in PAQUETES_VERSIONES:
        req = re.search(rf'^{re.escape(pin)}==(\S+)$', reqs, re.M).group(1)
        vis = por_nombre[nb].split()[0]
        filas.append([f'`{pin}`', req, vis, '✓' if req == vis else '✗'])
    return filas


def tabla_md(texto):
    filas = [[c.strip() for c in l.strip().strip('|').split('|')] for l in texto.split('\n') if l.strip().startswith('|')]
    return filas[0], filas[2:]


def tiempo_nb(n):
    """Segundos de ejecución que guardó el propio notebook: suma, celda a celda, de execute_input -> shell.execute_reply."""
    def p(s):
        return dt.datetime.fromisoformat(s.replace('Z', '+00:00'))
    total = 0.0
    for c in _celdas(n):
        e = c.get('metadata', {}).get('execution')
        if e and 'iopub.execute_input' in e and 'shell.execute_reply' in e:
            total += (p(e['shell.execute_reply']) - p(e['iopub.execute_input'])).total_seconds()
    return total


def dur(s):
    if s < 10:
        return f'{s:.1f}'.replace('.', ',') + ' s'
    if s < 100:
        return f'{s:.0f} s'
    m, seg = divmod(round(s), 60)
    return f'{m} min {seg} s'


def pc(x, d=2):
    return f'{x * 100:.{d}f}'.replace('.', ',') + ' %'


def num(x, d=2):
    return f'{x:.{d}f}'.replace('.', ',')


def miles(n):
    return f'{int(n):,}'.replace(',', ' ')


# ------------------------------------------------------------------------------------------------------------------------
# Piezas del visor (copiadas de los otros extras de S5) y propias
# ------------------------------------------------------------------------------------------------------------------------
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


def codigo(titulo, texto):
    """Un fragmento de código que se copia entero con «Copiar todo»."""
    return (f'<div class="term"><div class="bar"><em>{esc(titulo)}</em><button class="cp cpall" data-t="{esc(texto.rstrip())}">Copiar todo</button></div>'
            f'<pre class="src">{esc(texto.rstrip())}</pre></div>')


# ---- figuras: PNG de resultados/ (lo que producen los notebooks) -> WEBP en img/ ----------------------------------------------
FIGURAS = {
    'fig_softmax_temperatura': 'Cinco paneles de barras (T = 0.5 · 1 · 2 · 5 · 10) con las probabilidades de las 10 clases para el mismo vector de logits de un profesor; título de la figura «El mismo vector de logits, suavizado con distintas temperaturas»',
    'fig_entropia_temperatura': 'Curva de la entropía (nats) frente a la temperatura T, con puntos rotulados T=0.5 · T=1 · T=2 · T=5 · T=10 y una línea discontinua en la entropía uniforme (log 10); título «A mayor T, más se acerca la distribución a la uniforme»',
    'fig_kl_temperatura': 'Dos líneas con la KL (nats) entre profesor y estudiante para T = 1 · 2 · 3 · 5 · 8, una para el estudiante «cercano» y otra para el que «apuesta al 8»; título «KL entre profesor y estudiante a distintas T»',
    'fig_mnist_curvas': 'Dos paneles, «Exactitud en train» y «Exactitud en test», con una línea por época para el profesor, el estudiante duro y el estudiante destilado de MNIST',
    'fig_mnist_blandas': 'Seis dígitos de test y, debajo de cada uno, barras con las etiquetas blandas del profesor a T = 4; título «Etiquetas blandas del profesor (la masa residual es el conocimiento oscuro)»',
    'fig_sentimiento_curvas': 'Dos paneles, «Exactitud en train» y «Exactitud en test (validation SST-2)», con las épocas del GRU duro y del GRU destilado y una línea discontinua con la exactitud del profesor DistilBERT',
    'fig_comparativa_global': 'Tres paneles, «Calidad», «Tamaño» (parámetros, escala log) y «Latencia (esta máquina)», con barras de profesor, estudiante duro y estudiante destilado para MNIST y para SST-2',
    'fig_comparativa_pareto': 'Gráfico de puntos con los parámetros (escala log) frente a la exactitud en test de los seis modelos de MNIST y SST-2; título «Frente calidad / tamaño»',
    'fig_ejercicio2_blandas_mnist': 'Ocho dígitos de test y, debajo, las probabilidades del profesor de MNIST a T = 1 y a T = 5; título «Profesor de MNIST: la misma predicción, dos temperaturas»',
    'fig_v2_curvas': 'Dos paneles, «Train» y «Test (validation SST-2)», con las épocas del TinyBERT duro y del TinyBERT destilado, la línea del profesor y la línea de la puerta (−4 puntos)',
    'fig_v2_ablacion': 'Dos paneles de barras horizontales: «Calidad» (exactitud en test de cada variante, con las líneas del profesor y de la puerta) y «Latencia (comparación aproximada)» (aceleración del p95 frente al profesor, con la línea de 5×)',
}


def convertir_figuras():
    """resultados/fig_*.png -> img/fig_*.webp (sin pérdida). Solo si falta o el PNG es más nuevo."""
    from PIL import Image
    IMG.mkdir(exist_ok=True)
    for nombre in FIGURAS:
        png = RES / f'{nombre}.png'
        destino = IMG / f'{nombre}.webp'
        if not png.is_file():
            raise FileNotFoundError(png)
        if not destino.is_file() or destino.stat().st_mtime < png.stat().st_mtime:
            with Image.open(png) as im:
                im.save(destino, 'WEBP', lossless=True, quality=100, method=6)


def origen_figura(nombre):
    """(notebook, celda) donde se guarda resultados/<nombre>.png: se busca en el código, no se apunta a mano."""
    for n in ('00', '01', '02', '03', '04', '05', '06', '07'):
        for i, c in enumerate(_celdas(n)):
            if c['cell_type'] == 'code' and f'{nombre}.png' in _txt(c['source']):
                return n, i
    raise KeyError(nombre)


def cap(nombre, alto=None):
    """Una figura real (clic = ampliar) con su rótulo exacto y de qué notebook y celda sale."""
    alt = FIGURAS[nombre]
    n, i = origen_figura(nombre)
    estilo = f' style="max-height:{alto}px"' if alto else ''
    pie = f'Sale de: notebook {n}, celda {i} → <span class="mono">resultados/{nombre}.png</span>'
    return (f'<figure class="cap" data-img="{nombre}.webp"><button class="zoom" data-src="img/{nombre}.webp" data-alt="{esc(alt)}" title="Ampliar (Esc cierra)">'
            f'<img src="img/{nombre}.webp" alt="{esc(alt)}"{estilo}><span class="lupa">{LUPA} Ampliar</span></button>'
            f'<figcaption><span class="tag ok">Figura real</span> {esc(alt)}<br><span class="orig">{pie}</span></figcaption></figure>')


def lista(items):
    return '<ul class="list">' + ''.join(f'<li>{md(i)}</li>' for i in items) + '</ul>'


def mira(items, titulo='Qué debes ver'):
    return f'<div class="card mira"><h3>{esc(titulo)}</h3>{lista(items)}</div>'


def si_falla(items):
    return f'<div class="card falla"><h3>Si falla</h3>{lista(items)}</div>'


def tabla(cab, filas, clase=''):
    def celda(c):
        return c if c.startswith('<span class="dec ') else md(c)
    th = ''.join(f'<th>{md(c)}</th>' for c in cab)
    tr = ''.join('<tr>' + ''.join(f'<td>{celda(c)}</td>' for c in f) + '</tr>' for f in filas)
    return f'<table class="tbl {clase}"><tr>{th}</tr>{tr}</table>'


def kpi(valor, texto, color=''):
    return f'<div class="card kpi"><b class="n {color}">{esc(valor)}</b><p class="small">{md(texto)}</p></div>'


def salida(titulo, texto):
    return f'<div class="realbox"><div class="rk">{esc(titulo)}</div><pre>{esc(texto.strip(chr(10)))}</pre></div>'


def callout(texto, estilo=''):
    return f'<div class="callout"{(" style=" + chr(34) + estilo + chr(34)) if estilo else ""}>{md(texto)}</div>'


def card(titulo, items):
    return f'<div class="card"><h3>{esc(titulo)}</h3>{lista(items)}</div>'


def fuente(texto):
    return f'<p class="fuente">Fuente: {md(texto)}</p>'


def sin_verificar(texto):
    return f'<p class="small"><span class="tag warn">Sin verificar</span> {md(texto)}</p>'


def dos_columnas(izq, der, proporcion='.9fr 1.1fr'):
    return (f'<div class="split" style="grid-template-columns:{proporcion}"><div class="col">{izq}</div>'
            f'<div class="capcol">{der}</div></div>')


def decision(texto):
    clase = 'ok' if texto == 'PROMOCIONAR' else 'mal'
    return f'<span class="dec {clase}">{texto}</span>'


SLIDES = []
_N = {}
GRANDES = {'Qué quedó sin verificar', 'Resumen'}


def slide(parte, minutos, titulo, kick, h1, cuerpo, notas):
    n = list(PARTES).index(parte) + 1
    _N[parte] = _N.get(parte, 0) + 1
    antetitulo = f'{n} · {NOMBRES_PARTE[parte]} · {kick}'
    attrs = f' data-part="{parte}" data-min="{minutos}" data-title="{esc(titulo)}"'
    clase = ' grande' if titulo in GRANDES else ''
    SLIDES.append(f'<section class="slide{clase}"{attrs}\n data-notes="{esc(notas)}">\n'
                  f'<p class="kick">{esc(antetitulo)}</p><h1>{md(h1)}</h1>\n{cuerpo}\n</section>')


def _caja(x, y, w, lineas, clase='nodo', h=96):
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" class="{clase}"/>'
    for k, t in enumerate(lineas):
        s += f'<text x="{x + w // 2}" y="{y + 27 + k * 20}" class="{"t1" if k == 0 else "t2"}">{esc(t)}</text>'
    return s


def svg_profesor_estudiante(p_neg, p_pos, n_prof, n_est, T, y_dura):
    """Qué es destilar: el estudiante aprende de la etiqueta dura Y de la blanda del profesor."""
    g = ['<defs><marker id="fa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#0b5cad"/></marker></defs>']
    g.append(_caja(6, 62, 170, ['Una frase', 'de SST-2', 'entra en los dos'], 'nodo', 96))
    g.append(_caja(236, 6, 270, ['Profesor', f'DistilBERT · {miles(n_prof)} parámetros', 'ya entrenado: no se toca'], 'nodo puerta', 96))
    g.append(_caja(566, 6, 270, [f'Etiqueta blanda (T = {num(T, 0)})', f'negativo {num(p_neg, 3)} · positivo {num(p_pos, 3)}', 'toda la distribución'], 'nodo ok', 96))
    g.append(_caja(566, 138, 270, ['Etiqueta dura del dataset', f'{y_dura} (positivo)', 'solo la clase correcta'], 'nodo', 90))
    g.append(_caja(896, 62, 198, ['Estudiante', f'GRU · {miles(n_est)}', 'parámetros: aprende de las dos'], 'nodo puerta', 96))
    g.append('<path d="M179 96 L233 54" class="fl" marker-end="url(#fa)"/>')
    g.append('<path d="M509 54 L563 54" class="fl" marker-end="url(#fa)"/>')
    g.append('<path d="M839 54 L893 90" class="fl" marker-end="url(#fa)"/><text x="900" y="40" class="t2">α · T² · KL</text>')
    g.append('<path d="M179 132 L563 182" class="fl dis" marker-end="url(#fa)"/>')
    g.append('<path d="M839 182 L893 140" class="fl" marker-end="url(#fa)"/><text x="900" y="198" class="t2">(1 − α) · CE</text>')
    return ('<svg viewBox="0 0 1100 236" role="img" aria-label="El profesor produce una etiqueta blanda con toda la distribución; el dataset aporta la etiqueta dura; el estudiante '
            'aprende de las dos con una pérdida que mezcla KL a temperatura T y entropía cruzada">' + ''.join(g) + '</svg>')


def svg_flujo(titulos):
    """Los ocho notebooks en orden y quién lee los artefactos de quién."""
    g = ['<defs><marker id="fb" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#0b5cad"/></marker></defs>']
    xs = [6 + k * 136 for k in range(8)]
    lee = {4: 'lee lo de 02 y 03', 7: 'lee lo de 03 y 06'}
    for k, x in enumerate(xs):
        clase = 'nodo' if k < 6 else 'nodo ok'
        g.append(f'<rect x="{x}" y="10" width="116" height="84" rx="10" class="{clase}"/><text x="{x + 58}" y="38" class="t1">{k:02d}</text>'
                 f'<text x="{x + 58}" y="58" class="t2">{esc(titulos[k])}</text>')
        if k in lee:
            g.append(f'<text x="{x + 58}" y="80" class="t2" style="fill:#0b5cad;font-weight:700">{lee[k]}</text>')
        if k < 7:
            g.append(f'<path d="M{x + 118} 52 L{x + 134} 52" class="fl" marker-end="url(#fb)"/>')
    g.append('<text x="6" y="116" class="t2" style="text-anchor:start">azul: v1 (notebooks 00-05) · verde: v2 (06-07) · el 04 y el 07 no entrenan: leen resultados/</text>')
    return ('<svg viewBox="0 0 1100 124" role="img" aria-label="Los ocho notebooks en orden; el 04 lee los resultados del 02 y del 03, y el 07 los del 03 y del 06">'
            + ''.join(g) + '</svg>')


# ------------------------------------------------------------------------------------------------------------------------
# Contenido
# ------------------------------------------------------------------------------------------------------------------------
def construir():
    SLIDES.clear()
    _N.clear()
    mn, se, v2 = R('mnist'), R('sentimiento'), R('v2_sentimiento')
    v2c, cmp_, e4, e5, probe = R('v2_comparativa'), R('comparativa'), R('ejercicio4_registro_run'), R('ejercicio5_promocion'), R('v2_probe')
    M, S, V = mn['modelos'], se['modelos'], v2['modelos']
    acc_p = S['profesor']['exactitud']

    py_so = re.search(r'(\d+\.\d+\.\d+) · (Linux-\S+)', sal('00', 'comprobar_entorno()'))
    PY, SO = py_so.group(1), py_so.group(2)
    t_nb = {n: tiempo_nb(n) for n in ('00', '01', '02', '03', '04', '05', '06', '07')}
    t_total = sum(t_nb.values())
    reqs = (AQUI / 'requisitos-extra-destilacion.txt').read_text(encoding='utf-8')
    torch_pin = re.search(r'^torch==(\S+)$', reqs, re.M).group(1)

    # ---------------------------------------------------------------- A · La idea
    out_ej = sal('03', 'n_show = 6')
    p_neg, p_pos = re.search(r'^\s*0\s+([\d.]+)\s+([\d.]+)\s*$', out_ej, re.M).groups()
    slide('A', 3, 'Portada', 'ML e IA: de desarrollo a producción · S5 · extra', 'Destilación de modelos en notebooks: que un modelo pequeño aprenda de uno grande', f'''
<div class="cover">
 <p class="sub">Un laboratorio para <b>replicar paso a paso</b>: un modelo <b>profesor</b>, ya entrenado, enseña a un <b>estudiante</b> más pequeño con <b>etiquetas blandas</b>. Ocho notebooks en CPU: la <b>v1</b> (00-05) con MNIST y con sentimiento, y la <b>v2</b> (06-07) con TinyBERT.</p>
 <div class="chips"><span class="tag">8 notebooks</span><span class="tag">v1 y v2</span><span class="tag">Solo CPU</span><span class="tag">Profesor DistilBERT</span><span class="tag">Estudiantes GRU y TinyBERT</span><span class="tag">Puertas de promoción</span></div>
 <div class="grid3" style="margin-top:20px">
  {card('Objetivos', ['Entender **etiquetas blandas**, temperatura y la pérdida de destilación.', 'Ejecutar los ocho notebooks **en orden** y leer sus salidas.', 'Decidir si un estudiante **se promociona**: calidad y latencia a la vez.'])}
  {card('Cómo se usa', [f'**{TOTAL_MIN} min** propuestos en seis partes (minuto en la barra inferior).', 'Cada orden con **⧉** para copiarla; las salidas son las **guardadas** en los notebooks.', '**← →** avanzan · **O** índice · **S** notas · **F** pantalla completa.'])}
  {card('Honestidad desde el principio', [f'Todo se ejecutó **una vez**, en CPU, con Python **{PY}** en **Linux**; aquí no se reejecuta nada.', '**Sin verificar:** Windows, Codespace, alumnado y GPU.'])}
 </div>
</div>''',
          'Portada del extra de la sesión 5. Son ocho notebooks que se hacen en CPU: la versión uno, del cero al cinco, con MNIST y con sentimiento, y la versión dos, el seis y el siete, con TinyBERT. Diga desde el principio lo que se probó y lo que no: la ejecución guardada es una sola, en Linux con Python tres doce; Windows, Codespace, alumnado y GPU están sin verificar. Las cifras de toda la presentación salen de los notebooks y de la carpeta de resultados, no de memoria.')

    slide('A', 4, 'Qué es destilar', 'profesor, estudiante y etiquetas blandas', 'Destilar es que un profesor ya entrenado enseñe a un estudiante pequeño con algo más que la etiqueta', f'''
<div class="card">{svg_profesor_estudiante(float(p_neg), float(p_pos), S['profesor']['parametros'], S['estudiante_destilado']['parametros'], se['temperature'], 1)}</div>
<div class="grid3" style="margin-top:12px">
 {card('Etiqueta dura', ['La clase correcta: un 3, un «positivo».', 'Es lo único que ve un estudiante «duro».'])}
 {card('Etiqueta blanda', ['La **distribución** que el profesor da a *todas* las clases.', 'Si ante un 3 da algo al 8 y al 5 y casi nada al 0, el estudiante aprende esa semejanza: el **conocimiento oscuro**.'])}
 {card('Por qué en producción', ['En el camino de la petición pesan **latencia, memoria y coste**.', 'El profesor puede quedar **fuera** de la petición: por lotes, para etiquetar o para auditar.'])}
</div>''' + fuente('notebook 00, apartados «La idea, en una frase» y «Por qué importa en producción»; las cifras del diagrama, notebook 03 (salida de la celda de ejemplos) y resultados/sentimiento.json.'),
          'Qué es destilar, con un ejemplo real del notebook tres. Una frase entra en dos sitios: en el profesor, que es DistilBERT con casi sesenta y siete millones de parámetros y no se toca, y en el dataset, que da la etiqueta dura. El profesor devuelve una etiqueta blanda, la distribución entera: aquí cero coma cero cuarenta y siete negativo y cero coma novecientos cincuenta y tres positivo a temperatura tres. El estudiante, un GRU de dos millones de parámetros, aprende de las dos con una pérdida que mezcla una divergencia KL y la entropía cruzada. La utilidad en producción es mover el coste de la petición.')

    sm = sal('01', 'fig_softmax_temperatura.png')
    filas_t = {m.group(1): m.groups()[1:] for m in re.finditer(r'^clase (\d)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)$', sm, re.M)}
    c3, c8 = filas_t['3'], filas_t['8']
    slide('A', 3, 'La temperatura', 'softmax con T', 'La temperatura T suaviza el softmax: ahí aparece lo que el profesor sabe de las clases perdedoras', f'''
{cap('fig_softmax_temperatura', 250)}
<div class="grid3" style="margin-top:8px">
 {card('Qué hace T', ['`softmax(z / T)`. Con **T = 1** es el softmax de siempre.', 'Con **T > 1** las clases no ganadoras reciben más masa.'])}
 {card('Lo que dicen las cifras', [f'Clase 3: **{num(float(c3[0]), 3)}** a T = 0,5 y **{num(float(c3[3]), 3)}** a T = 5.', f'Clase 8 (se parece al 3): **{num(float(c8[0]), 3)}** a T = 0,5 y **{num(float(c8[3]), 3)}** a T = 5.'])}
 {callout('Los logits son **inventados** a propósito: un profesor muy seguro del 3 que ve algún parecido con el 8 y el 5. Sirven para fijar la idea, no son un modelo real.')}
</div>''' + fuente('notebook 01, apartado 2: celda que guarda `resultados/fig_softmax_temperatura.png`; la tabla de probabilidades, salida de esa celda.'),
          'La temperatura. El softmax convierte logits en probabilidades; con la temperatura se divide cada logit por T antes. Con T igual a cero coma cinco casi toda la masa está en la clase tres, casi una etiqueta dura. Con T igual a cinco el tres sigue ganando pero el ocho y el cinco son claramente más probables que el cero o el uno: esa es la información que queremos que el estudiante reciba. Aviso: los logits de este ejemplo están inventados a propósito en el notebook, para fijar la idea.')

    kl = sal('01', 'fig_kl_temperatura.png')
    kl_fil = {m.group(1): (m.group(2), m.group(3)) for m in re.finditer(r'^(\d)\s+([\d.]+)\s+([\d.]+)$', kl, re.M)}
    slide('A', 3, 'Entropía y KL', 'más T, distribución más plana', 'A más temperatura sube la entropía y baja la KL entre profesor y estudiante', f'''
<div class="thumbs t2">{cap('fig_entropia_temperatura', 230)}{cap('fig_kl_temperatura', 230)}</div>
<div class="grid2" style="margin-top:10px">
 {mira(['La **entropía** crece con T y se satura cerca de log 10 (uniforme en 10 clases).', 'La **KL** del estudiante que apuesta mal baja de **' + num(float(kl_fil['1'][0]), 3) + '** (T = 1) a **' + num(float(kl_fil['8'][0]), 3) + '** (T = 8); la del cercano, de **' + num(float(kl_fil['1'][1]), 3) + '** a **' + num(float(kl_fil['8'][1]), 3) + '**.'])}
 {callout('Con T = 1 la KL **separa muy bien** al estudiante cercano del que apuesta al 8; con T alta casi no los distingue. **T y α se eligen con validación**, no a ojo en test.')}
</div>''' + fuente('notebook 01, apartados 2 y 3: celdas que guardan las dos figuras; la tabla de KL, salida de la segunda.'),
          'Dos medidas de lo mismo. A la izquierda, la entropía de la distribución frente a la temperatura: sube con T y se acerca al límite de la distribución uniforme, que es el logaritmo de diez. A la derecha, la KL entre profesor y estudiante: con T igual a uno el estudiante que apuesta por el ocho tiene una KL de dos coma siete, y el cercano de cero coma cero dos; al subir T las dos bajan mucho. Por eso T y alfa son hiperparámetros que se eligen con un conjunto de validación.')

    slide('A', 3, 'La pérdida de destilación', 'KL a temperatura T más entropía cruzada', 'La pérdida mezcla copiar al profesor (KL a temperatura T) y acertar la etiqueta (entropía cruzada)', f'''
''' + dos_columnas(callout('`L = α · T² · KL( p_prof(T) ‖ p_est(T) ) + (1 − α) · CE(z_est, y)`  (Hinton, Vinyals y Dean, 2015)') + codigo('perdida_destilacion · src/destilacion_utils.py (núcleo)', trozo(_src_utils(), 'log_p_est = F.log_softmax', '# ----')) + lista(['**α = 1**: solo destilación. **α = 0**: entrenamiento supervisado de siempre.', '**T²** compensa que el gradiente de la KL se encoge como 1/T² al suavizar.']),
                    tabla(['Notebook', 'T', 'Alfa', 'Estudiante'], [
                        ['02 · MNIST', num(mn['temperature'], 0), num(mn['alpha'], 1), 'MLP de 400 etiquetas'],
                        ['03 · sentimiento v1', num(se['temperature'], 0), num(se['alpha'], 1), 'GRU, 3 000 frases'],
                        ['06 · sentimiento v2', num(v2['temperature'], 0), num(v2['alpha'], 1), 'TinyBERT, 20 000 frases']]) + salida('Salida guardada · notebook 01 · la pérdida de dos estudiantes', sal('01', 'z_est_a = torch.tensor')) + callout('En el 01, **T = 3 y α = 0,7** son «valores de partida razonables, no un óptimo universal».') + fuente('notebook 01, apartado 3; `src/destilacion_utils.py`; T y α de cada notebook, de resultados/mnist.json, sentimiento.json y v2_sentimiento.json.'), '1.05fr .95fr'),
          'La pérdida de destilación de Hinton y compañía. Dos términos: la divergencia KL entre la distribución suave del profesor y la del estudiante, a temperatura T, y la entropía cruzada con la etiqueta dura. Alfa mezcla los dos: con alfa uno solo se destila y con alfa cero es el entrenamiento supervisado habitual. El factor T al cuadrado compensa que el gradiente se encoge al suavizar. En la tabla se ven los valores que usa cada notebook; en el uno se dice que tres y cero coma siete son valores de partida, no un óptimo.')

    # ---------------------------------------------------------------- B · Preparación
    hdr, filas_readme = tabla_md(trozo(readme(), '| # | Cuaderno', '## Requisitos'))
    tit_nb = {}
    for n in t_nb:
        tit_nb[n] = _txt(_celdas(n)[0]['source']).split('\n')[0].split('·', 1)[1].strip()
    cortos = {'00': 'Intro y setup', '01': 'Teoría', '02': 'MNIST', '03': 'Sentimiento', '04': 'Comparativa', '05': 'Ejercicios', '06': 'v2 TinyBERT', '07': 'v1 vs v2'}
    filas_mapa = []
    for f in filas_readme:
        n = f[0]
        filas_mapa.append([f'**{n}**', f[2], dur(t_nb[n]), f[3]])
    slide('B', 4, 'Mapa y tiempos', 'ocho notebooks, un orden', 'Ocho notebooks que se siguen en orden: el 04 y el 07 leen lo que dejan los anteriores', f'''
<div class="card">{svg_flujo([cortos[n] for n in sorted(cortos)])}</div>
<div style="margin-top:8px" class="card">{tabla(['Nº', 'Qué hace (README)', 'Tiempo guardado', 'Orientativo (README)'], filas_mapa, 'sm')}</div>
<p class="fuente">Tiempo guardado = suma de lo que tardó cada celda, según la metadata de ejecución de cada .ipynb (total: <b>{dur(t_total)}</b>; el 06 usó los logits ya en caché). Fuente: README (tabla) y los ocho notebooks.</p>''',
          f'Mapa del extra. Los ocho notebooks se siguen en orden porque el cuatro lee lo que dejan el dos y el tres, y el siete lee lo del tres y el seis. La columna de tiempo guardado no es una estimación: es la suma de lo que tardó cada celda en la ejecución que quedó guardada en el propio notebook, en total unos {dur(t_total)}, y casi todo es el notebook seis, que tardó {dur(t_nb["06"])} con los logits del profesor ya en caché. La columna orientativa es la del README y es para CPU.')

    slide('B', 3, 'Entorno', 'el del curso, más los requisitos del extra', 'Un solo entorno: el del curso, y encima los requisitos del extra', '''
''' + dos_columnas(term('Terminal · desde la carpeta del extra · una orden cada vez', [
        '# entorno del curso (véase 03-Entorno/)'] + lineas_cmd(bloque_readme('## Entorno recomendado', 'bash'))) + fuente('README, «Entorno recomendado: el del curso (`env-ia-mlops`)».') + callout(f'El archivo fija **torch=={torch_pin}** y ya incluye el `--extra-index-url` de las ruedas CPU: sin él, pip no encuentra esa rueda.'),
                    mira([f'**Python 3.12** (recomendado) o 3.11; la ejecución guardada fue con **{PY}**.', 'Unos **3 GB** de disco: entorno, caché de Hugging Face y MNIST.', 'Salida a Internet **la primera vez**: MNIST y el profesor de sentimiento.']) + '<div class="card"><h3>Versiones: requisitos frente a notebook 00</h3>' + tabla(['Paquete', 'requisitos', 'notebook 00', ''], versiones_nb00(reqs), 'sm') + '</div>' + si_falla(['`pip` no encuentra `torch`: falta el `--extra-index-url` (el archivo ya lo lleva).', 'Falta algún paquete: el notebook 00 lo dice y pide `pip install -r requisitos-extra-destilacion.txt` con el **mismo Python que el kernel**.']), '1fr 1fr'),
          'Preparar el entorno. Lo recomendado es reutilizar el entorno del curso, que se llama env guion ia guion mlops, y encima instalar los requisitos del extra, porque el extra necesita paquetes que ese entorno no trae: PyTorch solo CPU, transformers, datasets. El archivo de requisitos fija la versión de torch y trae el índice extra para las ruedas de CPU. Necesita unos tres gigas de disco y salida a Internet la primera vez. Lo único que garantiza que funciona es que las versiones que imprime el notebook cero coinciden con las del archivo; instalar desde cero en una máquina limpia no se presenció aquí.')

    sh_nuevo = bloque_readme('## Preparar un entorno nuevo (CPU, Linux o macOS)', 'bash')
    ps_nuevo = bloque_readme('## Preparar un entorno nuevo (CPU, Windows)', 'powershell', 0) + '\n' + bloque_readme('## Preparar un entorno nuevo (CPU, Windows)', 'powershell', 2)
    slide('B', 3, 'Entorno nuevo', 'si no tienes el del curso', 'Si no tienes el entorno del curso, crea uno nuevo: Linux o macOS por un lado, Windows por otro', '''
<div class="grid2">
 <div class="col">''' + term('Linux o macOS · una orden cada vez', lineas_cmd(sh_nuevo)) + '''</div>
 <div class="col">''' + term('Windows (PowerShell) · una orden cada vez', [l for l in lineas_cmd(ps_nuevo) if l.strip()]) + sin_verificar('**Windows**: las órdenes salen del README, pero la ejecución guardada fue en **Linux** (' + SO + '). Nadie las ha probado en Windows aquí.') + '''</div>
</div>
<div style="margin-top:10px">''' + callout('Si Windows bloquea la activación del entorno, `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` (solo para tu usuario). Los notebooks localizan la raíz del proyecto aunque el directorio de trabajo sea `notebooks/`.') + '''</div>''' + fuente('README, «Preparar un entorno nuevo» (Linux o macOS y Windows).'),
          'Si no se dispone del entorno del curso, se crea uno nuevo con Python tres doce. A la izquierda, Linux o macOS, que es donde se ejecutó el material; a la derecha, Windows con PowerShell, que está en el README pero sin verificar: no se probó en Windows. En Windows, si la política de ejecución bloquea la activación, se cambia una vez para el usuario actual. Una nota práctica: los notebooks buscan la raíz del proyecto, así que da igual desde qué carpeta se abran.')

    px = [l.replace(PROXY_README, PROXY_EJEMPLO) for l in bloque_readme('En Windows (PowerShell), si tu red sale', 'powershell').split('\n')]
    slide('B', 3, 'Proxy y Hugging Face', 'solo si tu red lo exige', 'Detrás de un proxy corporativo, defínelo antes de descargar nada: MNIST y el profesor vienen de Internet', '''
''' + dos_columnas(term('PowerShell · solo esta sesión · cambia el proxy por el tuyo', [
        '# ejemplo con un proxy genérico: no es el de ninguna empresa real'] + px) + term('Si el profesor ya está en cache-hf/ · sin red', ['# bash', 'export HF_HUB_OFFLINE=1', 'export TRANSFORMERS_OFFLINE=1']) + fuente('README, «Proxy corporativo y Hugging Face».') + sin_verificar('**proxy corporativo**: la ejecución guardada fue **sin proxy**, sin certificado y sin token (notebook 00).'),
                    mira(['El notebook 00 **solo informa** de si hay proxy, certificado y token (sí o no); no imprime secretos.', 'Si `HF_HOME` no estaba definido, lo apunta a `cache-hf/` dentro del proyecto.', 'La conexión a Hugging Face se prueba con un `HEAD` (sin descargar): salió **200**.', 'El profesor `distilbert-base-uncased-finetuned-sst-2-english` se descarga **una vez**; el conjunto SST-2 viene de `nyu-mll/glue`.']) + si_falla(['Hugging Face no se alcanza: define el proxy, o `HF_HUB_OFFLINE=1` si el profesor **ya** está en `cache-hf/`.', 'Un proxy que inspecciona HTTPS necesita el certificado: `SSL_CERT_FILE` y `REQUESTS_CA_BUNDLE` (README).']), '1fr 1fr'),
          'Proxy y Hugging Face. Solo hace falta si la red lo exige. El proxy que se ve es un nombre de ejemplo genérico, no el de ninguna empresa: cada uno pone el suyo. El notebook cero solo informa de si hay proxy, certificado y token, sin imprimir ningún secreto, y prueba la conexión con una petición HEAD. En la ejecución guardada no había proxy ni certificado ni token, así que el camino con proxy corporativo está sin verificar. Si el profesor ya está en la caché local, las variables de modo offline permiten trabajar sin red.')

    ps_loop = bloque_readme('Para volver a ejecutarlos todos', 'powershell')
    slide('B', 3, 'Ejecutar los ocho', 'o leerlos sin reentrenar', 'Los notebooks ya traen salidas: léelos sin reentrenar, o reejecútalos todos en orden', '''
''' + dos_columnas(term('Linux o macOS · desde la raíz del extra, con el entorno activado', [l for l in bloque_readme('Para volver a ejecutarlos todos', 'bash').split('\n')]) + fuente('README y scripts/ejecutar_cuadernos.sh.') + callout(f'**Reejecutar tarda**: la ejecución guardada sumó **{dur(t_total)}** y casi todo es el notebook 06 (**{dur(t_nb["06"])}**, con los logits ya en caché). En esta preparación **no se reejecutó nada**: se usan las salidas guardadas.'),
                    codigo('Windows (PowerShell) · bucle del README, con el entorno activado', ps_loop) + sin_verificar('el bucle de **PowerShell** no se ha ejecutado aquí (solo la versión `.sh`, en Linux).'), '.8fr 1.2fr'),
          'Se pueden leer los notebooks sin reentrenar, porque ya incluyen las salidas de una ejecución en CPU, o reejecutarlos todos en orden con el script de bash. Reejecutar regenera las carpetas de modelos y resultados. Avise de que el notebook seis es el que más tarda: más de doce minutos en la ejecución guardada, y eso con los logits del profesor ya calculados. El bucle de PowerShell del README está sin verificar. En esta preparación no se volvió a ejecutar ningún notebook: todo lo que se enseña es lo guardado.')

    # ---------------------------------------------------------------- C · v1 (00-05)
    c4 = salida_celda('00', buscar('00', 'faltan = tabla_entorno'))
    cx = salida_celda('00', buscar('00', 'conexion_hf = probar_conexion_hf()'))
    slide('C', 4, 'Notebook 00', 'comprobar el entorno', 'Notebook 00: solo comprueba el entorno, no entrena nada', f'''
''' + dos_columnas(codigo('Celda · comprobar el entorno', cod('00', 'tabla_entorno = comprobar_entorno()')) + codigo('Celda · alcanzar Hugging Face (un HEAD)', cod('00', 'conexion_hf = probar_conexion_hf()').split('\n')[0]) + fuente('notebook 00, apartados 2 y 3.'),
                    salida('Salida guardada · notebook 00', c4.split('\n')[0] + '\n' + cx.split('\n')[0] + '\n' + cx.split('\n')[1]) + mira([f'Python **{PY}** sobre **Linux**; torch **{torch_pin}**, dispositivo **cpu**.', 'CUDA «cpu-only», proxy y token: **no** (informativos, no bloquean).', 'Hugging Face responde con estado **200**.']) + si_falla(['«Faltan paquetes»: instala `requisitos-extra-destilacion.txt` en el entorno del kernel.', 'No se alcanza Hugging Face: proxy o `HF_HUB_OFFLINE=1` (diapositiva del proxy).']), '1fr 1fr'),
          'El notebook cero no entrena nada. Primero comprueba que están los paquetes obligatorios y deja una tabla con las versiones; si falta alguno, la celda siguiente se para con un mensaje que dice qué instalar. Después prueba que Hugging Face se alcanza con una petición HEAD, sin descargar. En la ejecución guardada todo está disponible, no hay GPU, proxy ni token, y Hugging Face responde doscientos. Si estas dos celdas pasan, se puede seguir con el notebook uno.')

    slide('C', 4, 'Notebook 01', 'softmax a mano', 'Notebook 01: tres softmax que coinciden, la base de la temperatura y de la pérdida', f'''
''' + dos_columnas(codigo('Celda · softmax ingenuo, estable y del módulo', cod('01', 'def softmax_ingenua')) + fuente('notebook 01, apartado 1.'),
                    salida('Salida guardada · notebook 01', sal('01', 'def softmax_ingenua')) + mira(['Restar el máximo antes de exponenciar **no cambia** el resultado y evita desbordar `exp`.', 'Las tres versiones **coinciden** con T = 1 (el `assert_allclose` lo exige).', 'El resto del notebook son las figuras y la pérdida de las diapositivas de teoría; **no necesita red**.']), '1fr 1fr'),
          'El notebook uno es teoría ejecutable y no necesita red ni datos. Se calcula el softmax de tres formas: una ingenua, una estable que resta el máximo y la del módulo compartido, y se comprueba que coinciden. La ventaja de restar el máximo es no desbordar la exponencial con logits grandes. Las figuras de temperatura, entropía y KL, y la tabla de pérdidas, son las de las diapositivas anteriores.')

    out2_7 = sal('02', 'tabla_tam = pd.DataFrame')
    out2_9 = sal('02', 'hist_profesor = entrenar')
    slide('C', 5, 'Notebook 02 · el profesor', 'calentamiento en MNIST', 'Notebook 02: un profesor MLP con 30 000 imágenes y un estudiante con solo 400', f'''
''' + dos_columnas(codigo('Celda · parámetros del experimento', trozo(cod('02', 'N_TRAIN_PROFESOR = 30_000'), 'N_TRAIN_PROFESOR', 'print("dispositivo')) + fuente('notebook 02, apartados 1 a 4.'),
                    salida('Salida guardada · notebook 02', trozo(out2_7, 'modelo', 'El estudiante tiene') + '\n' + lineas_con(out2_7, 'El estudiante tiene') + '\n' + lineas_con(out2_9, r'época  4/4|profesor en test')) + mira(['Profesor **[784, 256, 128, 10]**; estudiante **[784, 32, 10]**: el **10,8 %** de los parámetros.', 'Se **diseña a propósito** con pocas etiquetas para el estudiante (400).', 'Los dos estudiantes arrancan del **mismo estado inicial**.']) + si_falla(['«El profesor debería superar el 90 % en test de MNIST. Revisa el entorno o aumenta las épocas.»', 'MNIST se descarga una vez a `datos/mnist/`: la primera vez hace falta red.']), '1fr 1fr'),
          'El notebook dos es el calentamiento en visión. Un profesor MLP con doscientos treinta y cinco mil parámetros se entrena con treinta mil imágenes; el estudiante es un MLP diez veces más pequeño que ve solo cuatrocientas. A propósito: con pocas etiquetas el estudiante duro tiende a memorizar, y el destilado recibe en cada imagen una distribución rica. Los dos estudiantes arrancan del mismo estado inicial, para que la diferencia no sea suerte de la inicialización. El profesor llega a casi noventa y siete por ciento en test, y el notebook tiene una aserción que exige más de noventa.')

    out2_11 = sal('02', 'estudiante_duro = construir_mlp')
    d_m, k_m = M['estudiante_duro']['exactitud'], M['estudiante_destilado']['exactitud']
    slide('C', 5, 'Notebook 02 · los estudiantes', 'duro frente a destilado', f'Notebook 02: con los mismos 400 ejemplos, el destilado acierta {pc(k_m)} y el duro {pc(d_m)}', f'''
''' + dos_columnas(codigo('Celda · dos estudiantes, mismo estado inicial', trozo(cod('02', 'estudiante_duro = construir_mlp'), 'estudiante_duro = construir_mlp', 'metricas_duro')) + salida('Salida guardada · notebook 02 (última época)', lineas_con(out2_11, r'época 25/25')) + fuente('notebook 02, apartados 5 y 6; resultados/mnist.json.'),
                    cap('fig_mnist_curvas', 190) + mira([f'En **train** el duro llega a casi todo (memoriza 400 ejemplos); lo que cuenta es **test**.', f'Destilado frente a duro: **+{num((k_m - d_m) * 100)} puntos** ({pc(d_m)} → {pc(k_m)}), con 5 000 imágenes de test.', 'El profesor sigue en **' + pc(M['profesor']['exactitud']) + '**: el destilado no lo iguala.']), '1.05fr .95fr'),
          'El experimento central del notebook dos. Dos estudiantes con la misma arquitectura, los mismos cuatrocientos ejemplos y los mismos pesos iniciales: uno aprende solo de etiquetas duras y el otro copia las blandas del profesor con temperatura cuatro y alfa cero coma cinco. En train el duro llega a casi cien por cien, que es memorizar; en test el destilado queda por encima, unos dos puntos y cuarto. No lo venda como milagro: es una sola ejecución con una semilla, y el propio notebook dice que si la diferencia fuera pequeña o de otro signo no se fuerce.')

    slide('C', 3, 'Conocimiento oscuro', 'las blandas del profesor de MNIST', 'La masa residual de las etiquetas blandas es el conocimiento oscuro que recibe el estudiante', f'''
{cap('fig_mnist_blandas', 290)}
<div class="grid2" style="margin-top:8px">
 {mira(['Las barras son la distribución del profesor a **T = 4** sobre seis dígitos de test.', 'La clase ganadora domina, pero **queda masa** en otras clases: eso es lo que la etiqueta dura no contiene.'])}
 {callout('El notebook lo advierte: el destilado «suele quedar por encima del duro» en test porque las blandas son «una señal más rica (y, de paso, como regularizador)»; si en tu ejecución no ocurre, **anótalo y no lo fuerces**.')}
</div>''' + fuente('notebook 02, apartado 6.'),
          'Aquí se ve el conocimiento oscuro. Son seis dígitos de test y, debajo, las barras del profesor a temperatura cuatro. La clase correcta domina, pero queda masa repartida en otras clases, y esa masa es información que la etiqueta dura no contiene. El notebook explica que el destilado suele quedar por encima del duro en test porque la señal es más rica y de paso regulariza, y pide anotar el resultado aunque salga distinto en otra ejecución.')

    out3_5 = sal('03', 'ds = load_dataset')
    out3_7 = sal('03', 'profesor = AutoModelForSequenceClassification')
    slide('C', 5, 'Notebook 03 · el profesor', 'DistilBERT, logits precalculados', 'Notebook 03: DistilBERT enseña; sus logits se calculan una vez y el profesor se libera de la memoria', f'''
''' + dos_columnas(codigo('Celda · parámetros del experimento', trozo(cod('03', 'MODELO_PROFESOR ='), 'MODELO_PROFESOR', 'print("dispositivo')) + fuente('notebook 03, apartados 1 a 3.'),
                    salida('Salida guardada · notebook 03', lineas_con(out3_5, r'^(train=|ejemplo|clases)') + '\n' + lineas_con(out3_7, r'parámetros del profesor|etiquetas:|listo en|latencia profesor')) + mira(['**3 000** frases de train y el **validation** de SST-2 (**872**) como test: no se usa para elegir nada.', 'El estudiante usa el **mismo tokenizador**; en producción debe viajar con él.']) + si_falla(['La primera vez **descarga** el profesor (la barra marca **268 MB**; el README dice «unos 250 MB»).', 'Sin red: proxy, o `HF_HUB_OFFLINE=1` con el modelo ya en `cache-hf/`.']), '1fr 1fr'),
          'El notebook tres repite la idea con lenguaje. El profesor es DistilBERT ya afinado en SST-2, y no se retoca. Para no tenerlo en memoria mientras se entrena el estudiante, se calculan una sola vez sus logits, se guardan en disco y se libera el modelo. Se usan tres mil frases de train y las ochocientas setenta y dos de validación como test. Un detalle de producción que repite el notebook: el tokenizador es parte del artefacto. La primera ejecución descarga el modelo, que es de unos doscientos sesenta megas.')

    out3_9 = sal('03', 'def entrenar_estudiante')
    slide('C', 5, 'Notebook 03 · el estudiante', 'un GRU diminuto', f'Notebook 03: el GRU destilado mejora al duro ({pc(S["estudiante_duro"]["exactitud"], 1)} → {pc(S["estudiante_destilado"]["exactitud"], 1)}), pero queda lejos del profesor', f'''
''' + dos_columnas(codigo('Celda · dos estudiantes, mismo estado inicial', trozo(cod('03', 'def entrenar_estudiante'), 'estudiante_duro = construir_estudiante_sentimiento', 'metricas_duro')) + salida('Salida guardada · notebook 03', lineas_con(out3_9, r'parámetros del estudiante|época  5/5|^test ')) + fuente('notebook 03, apartados 4 y 5; resultados/sentimiento.json.'),
                    cap('fig_sentimiento_curvas', 175) + mira([f'GRU de **{miles(S["estudiante_destilado"]["parametros"])}** parámetros: el **3,0 %** del profesor.', f'Hueco con el profesor: **{num((acc_p - S["estudiante_destilado"]["exactitud"]) * 100)} puntos**. El notebook dice que el éxito aquí es **acercarse más que el duro**, no igualarlo.']), '1.05fr .95fr'),
          'El estudiante del notebook tres es un GRU bidireccional con un embedding: dos millones de parámetros, un tres por ciento de los del profesor. Entrena cinco épocas con tres mil frases. El destilado mejora al duro unos dos puntos y medio, pero se queda más de veintitrés puntos por debajo de DistilBERT. Es el motivo de la versión dos: no es un problema de velocidad, es de calidad.')

    fila = lambda nom, b: [nom, pc(b['modelos']['profesor']['exactitud']), pc(b['modelos']['estudiante_duro']['exactitud']), pc(b['modelos']['estudiante_destilado']['exactitud']),
                           f"{num((b['modelos']['estudiante_destilado']['exactitud'] - b['modelos']['profesor']['exactitud']) * 100)}",
                           f"+{num((b['modelos']['estudiante_destilado']['exactitud'] - b['modelos']['estudiante_duro']['exactitud']) * 100)}",
                           f"{num(b['modelos']['profesor']['latencia_ms_por_ejemplo_media'] / b['modelos']['estudiante_destilado']['latencia_ms_por_ejemplo_media'])}×"]
    slide('C', 4, 'Notebook 04', 'comparar sin reentrenar', 'Notebook 04: lee los JSON y calcula hueco, mejora y aceleración; no vuelve a entrenar', f'''
''' + dos_columnas(codigo('Celda · el resumen (extracto)', trozo(cod('04', 'resumen = []'), '    resumen.append(', 'tabla_resumen')) + fuente('notebook 04, apartado 2; cifras de resultados/mnist.json y resultados/sentimiento.json (idénticas a la salida guardada del notebook).') + si_falla(['«Faltan resultados de cuadernos anteriores»: ejecuta el 02 y el 03 en ese orden.']),
                    '<div class="card">' + tabla(['Problema', 'Profesor', 'Duro', 'Destilado', 'Hueco (puntos)', 'Mejora vs duro', 'Aceleración'], [
                        fila('MNIST / MLP', mn), fila('SST-2 / DistilBERT→GRU', se)], 'sm nw') + '</div>' + mira(['**Hueco**: destilado menos profesor. **Mejora**: destilado menos duro, la parte atribuible a destilar.', f'**Aceleración** = latencia por ejemplo del profesor / la del destilado, en esta CPU (lote 64 en MNIST, 16 y 32 en sentimiento).']), '.8fr 1.2fr'),
          'El notebook cuatro no entrena: lee los dos archivos de resultados y calcula tres cosas. El hueco, que es la exactitud del destilado menos la del profesor. La mejora respecto al duro, que es lo que se puede atribuir a destilar, porque los dos estudiantes son el mismo modelo con los mismos pesos iniciales. Y la aceleración de latencia. En sentimiento sale una aceleración de unas cien veces, pero ojo con la lectura: profesor y estudiante se midieron con lotes distintos, así que es un orden de magnitud y no una medida oficial; la versión dos corrige eso.')

    slide('C', 3, 'Calidad, tamaño y latencia', 'figuras del notebook 04', 'En sentimiento el ahorro de tamaño y latencia es enorme y el precio es el hueco de calidad', f'''
<div class="split" style="grid-template-columns:1.5fr 1fr"><div class="col">{cap('fig_comparativa_global')}</div><div class="col">{cap('fig_comparativa_pareto', 250)}</div></div>
<div class="grid2" style="margin-top:10px">
 {mira(['En MNIST el contraste de latencia es pequeño: son MLP diminutos. El valor está en la **calidad con pocos datos**.', 'En sentimiento cuentan **tamaño y latencia**; el hueco de exactitud es el precio.'])}
 {callout('La latencia es de **esta máquina**, no un SLO de producción: sirve para comparar modelos entre sí en las mismas condiciones.')}
</div>''' + fuente('notebook 04, apartado 2 («Cómo leerlo»); las dos figuras salen de la celda de resumen.'),
          'Las dos figuras del notebook cuatro. A la izquierda, calidad, tamaño en escala logarítmica y latencia para los tres modelos de cada problema. A la derecha, el frente de calidad contra tamaño. En MNIST la latencia casi no importa porque son redes diminutas: el valor del experimento es la calidad con pocos datos. En sentimiento el ahorro de parámetros y de milisegundos es enorme y el precio es el hueco de exactitud. Y recuerde que la latencia es de esta máquina concreta.')

    o5 = salida_celda('05', buscar('05', 'def mi_softmax'))
    o5_2 = salida_celda('05', buscar('05', 'fig_ejercicio2_blandas_mnist.png'))
    o5_3 = salida_celda('05', buscar('05', 'class ProfesorRuido'))
    o5_5 = salida_celda('05', buscar('05', 'cumple_calidad = hueco_puntos'))
    slide('C', 5, 'Notebook 05 · ejercicios', 'cinco ejercicios con soluciones', 'Notebook 05: el ejercicio 3 enseña que destilar un profesor inútil arrastra al estudiante', f'''
''' + dos_columnas(codigo('Ejercicio 3 · un profesor de ruido', trozo(cod('05', 'class ProfesorRuido'), 'class ProfesorRuido', 'ruido = ProfesorRuido')) + salida('Salida guardada · notebook 05 (ejercicios 1, 2, 3 y 5)', o5.strip() + '\n' + lineas_con(o5_2, 'Predicción dura') + '\n' + lineas_con(o5_3, 'destilado de un profesor') + '\n' + o5_5.strip()) + fuente('notebook 05, ejercicios 1 a 5; el 4 está en la diapositiva «Qué registrar».') + mira(['**1** softmax estable a mano · **2** leer blandas reales · **3** profesor inútil · **4** qué registrar en un run · **5** un criterio de promoción.']),
                    cap('fig_ejercicio2_blandas_mnist', 250) + callout('Con α = 1 el estudiante **solo copia**: un profesor de ruido deja la exactitud cerca de la de un clasificador aleatorio (en torno a 0,10 en diez clases). **No destiles un profesor que no hayas evaluado.**'), '1.05fr .95fr'),
          'El notebook cinco tiene cinco ejercicios con soluciones al final. El uno, el softmax estable a mano. El dos, leer las etiquetas blandas del profesor de MNIST, que es la figura de la derecha. El tres es el más instructivo: se destila una época con alfa uno a partir de un profesor real y de un profesor de ruido, y el de ruido arrastra al estudiante a un once por ciento. El cuatro registra un run y el cinco aplica las puertas de promoción a la versión uno, y la respuesta es no promocionar.')

    # ---------------------------------------------------------------- D · v2 (06-07)
    cab6, filas6 = tabla_md(fuente_celda('06', 0))
    intuicion = fuente_celda('06', 0).split('La intuición: ')[1].split('. ')[0] + '.'
    n_sst2 = re.search(r'hay ([\d ]+);', fuente_celda('06', 0)).group(1)
    slide('D', 4, 'Por qué falló la v1', 'qué cambia la v2', 'La v1 falló por calidad, no por velocidad: la v2 cambia el punto de partida, los datos y la medida', f'''
<div class="card">{tabla(cab6, filas6, 'sm')}</div>
<div style="margin-top:10px">{callout('**La intuición:** ' + intuicion + ' TinyBERT ya fue destilado, en preentrenamiento, a partir de un BERT grande.')}</div>
<div class="grid3" style="margin-top:12px">
 {kpi(pc(S['estudiante_destilado']['exactitud']) + ' frente a ' + pc(acc_p), 'v1: el GRU destilado y el profesor (resultados/sentimiento.json)')}
 {kpi(num(e5['hueco_puntos']) + ' puntos', 'hueco de la v1: la puerta de calidad admite **4** (resultados/ejercicio5_promocion.json)')}
 {kpi(miles(se['n_train']) + ' → ' + miles(v2['n_train']), 'frases de entrenamiento de la v1 a la v2 (SST-2 tiene ' + n_sst2 + ', según el notebook 06)')}
</div>''' + fuente('notebook 06, apartado «Por qué falló la v1 (y qué vamos a cambiar)»; las cifras de la v1, de resultados/sentimiento.json.'),
          'La versión dos nace de reconocer por qué falló la uno. El estudiante era un GRU desde cero con tres mil frases y quedaba a veintitrés puntos del profesor. Los cambios, uno por uno: un transformer pequeño ya preentrenado, que es TinyBERT de cuatro capas; veinte mil frases en lugar de tres mil; los logits del profesor cacheados; la latencia medida con el mismo lote y los mismos hilos; y la cuantización a int8 como recorte extra. La idea de fondo: destilar no arregla un estudiante sin capacidad ni buen punto de partida.')

    o6_3 = sal('06', 'MODO_RAPIDO = True')
    o6_5 = sal('06', 'def precomputar_o_cargar')
    o6_7 = sal('06', 'class TextoDS')
    slide('D', 5, 'Notebook 06 · preparar', 'TinyBERT, 20 000 frases y logits en caché', 'Notebook 06: TinyBERT de 4 capas como estudiante, 20 000 frases y los logits del profesor en caché', f'''
''' + dos_columnas(codigo('Celda · parámetros y modo rápido', trozo(cod('06', 'MODO_RAPIDO = True'), 'MODO_RAPIDO = True', 'HILOS = fijar_hilos_cpu')) + salida('Salida guardada · notebook 06', lineas_con(o6_3, r'^(modo_rapido|profesor:|estudiante:)') + '\n' + lineas_con(o6_5, r'Reutilizo|^n_train|exactitud del profesor|necesita') + '\n' + lineas_con(o6_7, 'parámetros estudiante')) + fuente('notebook 06, apartados 1 a 3.'),
                    mira([f'`MODO_RAPIDO = True` es el valor por defecto: **2 épocas**. A `False` sube a 3 épocas: «no necesariamente más exactitud en test».', f'El estudiante necesita **≥ {pc(v2["puerta_calidad"])}** (profesor menos 4 puntos).', f'TinyBERT: **{miles(V["estudiante_duro"]["parametros"])}** parámetros, el **21,4 %** del profesor.', 'Los logits se **cachean** en `modelos/v2_sentimiento_logits_profesor.pt`.']) + si_falla(['Sin la caché, el notebook **recalcula** los logits: «en esta máquina, 20 000 ejemplos fueron unos 3 minutos».', 'Sin red la primera vez: mismo proxy o modo offline que en el 03.']), '1fr 1fr'),
          'El notebook seis prepara la versión dos. El modo rápido es el valor por defecto, con dos épocas, y subirlo a tres épocas no mejora necesariamente el test. El estudiante necesita ochenta y siete coma cero seis por ciento de exactitud, que es la del profesor menos cuatro puntos. TinyBERT tiene catorce millones de parámetros, un veintiuno por ciento de los del profesor, y no está afinado en SST-2, así que hay que entrenarlo. Los logits del profesor se cachean en disco: si no estuvieran, el notebook los recalcularía y serían unos tres minutos.')

    o6_9 = sal('06', 'def entrenar(usar_kd')
    slide('D', 5, 'Notebook 06 · entrenar', 'duro frente a destilado', f'Notebook 06: duro y destilado empatan ({pc(V["estudiante_duro"]["exactitud"])} y {pc(V["estudiante_destilado"]["exactitud"])}): las blandas no ganan al duro', f'''
''' + dos_columnas(codigo('Celda · la pérdida según el modo (extracto de «entrenar»)', trozo(cod('06', 'def entrenar(usar_kd'), 'if usar_kd:', 'opt.zero_grad')) + salida('Salida guardada · notebook 06', lineas_con(o6_9, r'^v2 (duro|destilado)\s+época|^mejor test')) + fuente('notebook 06, apartado 4; resultados/v2_sentimiento.json.'),
                    cap('fig_v2_curvas', 190) + mira([f'Mejor época: duro **{pc(V["estudiante_duro"]["exactitud"])}**, destilado **{pc(V["estudiante_destilado"]["exactitud"])}**, profesor **{pc(v2["exactitud_profesor"])}**.', 'El notebook lo explica: «TinyBERT ya llega predestilado de un BERT grande».', f'Cada época tardó unos **187 s** en CPU.']), '1.05fr .95fr'),
          'El entrenamiento de la versión dos. Dos estudiantes con la misma arquitectura, los mismos datos y los mismos pesos iniciales: uno con entropía cruzada y otro con la pérdida de destilación a temperatura tres y alfa cero coma cinco. Los dos superan la puerta de calidad. Y aquí viene un resultado honesto que hay que contar tal cual: la destilación no gana al duro. El notebook lo explica: TinyBERT ya llegó predestilado de un BERT grande. Cada época tarda unos tres minutos en CPU.')

    o6_13 = sal('06', 'frases_lat = textos_test')
    o6_21 = sal('06', 'candidatos_oficiales = []')
    slide('D', 6, 'Notebook 06 · latencia y puertas', 'mismo lote, mismos hilos', 'Latencia justa: mismo lote y 4 hilos; el fp32 pasa las dos puertas y el int8 suspende en calidad', f'''
''' + dos_columnas(salida('Salida guardada · notebook 06 · latencias (ms)', trozo(o6_13, 'variante', 'Variante oficial')) + salida('Salida guardada · notebook 06 · puertas', lineas_con(o6_21, r'acc=|^OFICIAL')),
                    mira([f'Profesor lote 16: p95 **{num(V["profesor"]["latencia_ms_lote_p95"])} ms**; TinyBERT duro fp32: **{num(V["estudiante_duro"]["latencia_ms_lote_p95"])} ms**.', f'**int8** baja la exactitud de {pc(V["estudiante_duro"]["exactitud"])} a {pc(V["estudiante_duro"]["exactitud_int8"])} y apenas recorta el p95: **no se promociona**.', f'**Lote 1**: ni fp32 ni int8 llegan a 5× en esta máquina; por eso el protocolo oficial es el lote 16.', 'ONNX **no se exportó**: «No module named \'onnxscript\'».']) + mira(['La primera decisión del notebook (variante int8) fue «NO PROMOCIONAR»; el apartado 10 la **recalcula** con las cifras medidas y elige el duro fp32.', 'Lo que manda es lo **guardado y medido**, no la primera impresión.'], 'Ojo: la decisión cambió') + fuente('notebook 06, apartados 6 y 10; src/destilacion_utils.py (`evaluar_puertas_promocion`).'), '1.15fr .85fr'),
          'Latencia y puertas, que es lo más delicado del notebook seis. Se mide al profesor y a cada variante con el mismo lote, los mismos cuatro hilos y las mismas repeticiones. Con lote dieciséis el profesor tarda unos ciento veintisiete milisegundos en el p95 y el TinyBERT en fp32 unos dieciséis y medio: casi ocho veces menos. La cuantización a int8 recorta poco y cuesta dos puntos y medio de exactitud, por debajo de la puerta. Con lote uno no se llega a cinco veces. Un detalle de honestidad: la primera decisión del notebook, con int8, era no promocionar; el apartado diez la corrige con las cifras medidas. ONNX no se llegó a exportar porque faltaba un paquete.')

    slide('D', 4, 'Notebook 07 · ablación', 'qué cambió de verdad', 'Notebook 07: lo que abre la puerta es el punto de partida y los datos, no las etiquetas blandas', f'''
{cap('fig_v2_ablacion', 245)}
<div class="grid2" style="margin-top:8px">
 {mira(['**1.** La destilación de la v1 **sí aportó algo**, pero no bastó.', '**2.** Un BERT pequeño genérico con 16 000 frases se queda en el **80-81 %**: por debajo de la puerta.', '**3.** TinyBERT + 20 000 frases abre la puerta; **la destilación de salidas no gana al duro**.'])}
 {callout('En otras palabras (notebook 07): la v1 fallaba por **calidad**, no por latencia; el GRU era rapidísimo.')}
</div>''' + fuente('notebook 07, apartado 2 («Cómo leer la ablación»); la sonda, de resultados/v2_probe.json.'),
          'El notebook siete pone todo junto. La figura tiene dos paneles: a la izquierda la calidad de cada variante con las líneas del profesor y de la puerta, y a la derecha una aceleración aproximada. Tres mensajes, en orden: la destilación de la versión uno sí aportó algo pero no bastó; un BERT pequeño genérico con más datos queda en torno al ochenta por ciento, todavía por debajo de la puerta; y lo que abre la puerta es el punto de partida, TinyBERT, más datos suficientes, no las etiquetas blandas. Las barras de latencia de la versión uno se midieron con otro lote, así que son orden de magnitud.')

    ab = v2c['ablacion']
    filas_ab = [[f'{r["variante"]}', pc(r['exactitud']), num(r['hueco_vs_profesor_puntos']), miles(r['parametros']),
                 ('—' if (r['p95_lote_ms'] is None or r['p95_lote_ms'] != r['p95_lote_ms']) else num(r['p95_lote_ms'])), ('sí' if r['calidad_ok'] else 'no')] for r in ab]
    slide('D', 3, 'Notebook 07 · tabla', 'diez variantes', 'Diez variantes en una tabla: solo las de TinyBERT en fp32 cumplen la calidad entre los estudiantes', f'''
<div class="card">{tabla(['Variante', 'Exactitud', 'Hueco (puntos)', 'Parámetros', 'p95 lote (ms)', 'Calidad ≤ 4'], filas_ab, 'sm')}</div>
<div class="grid2" style="margin-top:10px">
 {callout('Las filas «Sonda» salen de **resultados/v2_probe.json** (otro BERT pequeño, 11 171 074 parámetros): se midieron antes, **sin latencia**.')}
 {callout('El p95 de la v1 se midió con **lote 32** y el de la v2 con **lote 16**: no son comparables entre sí.')}
</div>''' + fuente('resultados/v2_comparativa.json (campo «ablacion»), que escribe el notebook 07.'),
          'La tabla de ablación del notebook siete, tal cual está guardada en el archivo de comparativa. Diez variantes: el profesor de referencia, los dos GRU de la versión uno, las dos sondas con un BERT pequeño genérico, y las variantes de TinyBERT duro y destilado en fp32 e int8, más la fila oficial, que es el duro en fp32 repetido. Solo cumplen la calidad, entre los estudiantes, las de fp32 de TinyBERT. Las sondas no tienen latencia porque se midieron antes, y el p95 de la versión uno es de otro lote.')

    # ---------------------------------------------------------------- E · Producción
    def puerta(acc, p95_est, p95_prof):
        return (acc_p - acc) * 100, p95_prof / p95_est
    p95p = V['profesor']['latencia_ms_lote_p95']
    pu = v2['puertas']
    filas_pu = [
        ['v1 · GRU destilado (ejercicio 5)', num(e5['hueco_puntos']), num(e5['aceleracion_p95'], 1) + '× †', 'no', 'sí', decision(e5['decision'])],
        ['v2 · TinyBERT **duro fp32**, lote 16 (oficial)', num(pu['oficial']['hueco_puntos']), num(pu['oficial']['aceleracion_p95']) + '×', 'sí', 'sí', decision(pu['oficial']['decision'])],
        ['v2 · TinyBERT destilado fp32, lote 16', num(puerta(V['estudiante_destilado']['exactitud'], V['estudiante_destilado']['latencia_ms_lote_p95'], p95p)[0]), num(puerta(V['estudiante_destilado']['exactitud'], V['estudiante_destilado']['latencia_ms_lote_p95'], p95p)[1]) + '×', 'sí', 'sí', decision('PROMOCIONAR')],
        ['v2 · TinyBERT int8, lote 16', num(pu['duro_int8_lote16']['hueco_puntos']), num(pu['duro_int8_lote16']['aceleracion_p95']) + '×', 'no', 'sí', decision(pu['duro_int8_lote16']['decision'])],
        ['v2 · TinyBERT int8, lote 1', num(pu['int8_lote1']['hueco_puntos']), num(pu['int8_lote1']['aceleracion_p95']) + '×', 'no', 'no', decision(pu['int8_lote1']['decision'])]]
    slide('E', 4, 'Cómo se promociona', 'dos puertas a la vez', 'Un estudiante se promociona si cumple a la vez calidad (≤ 4 puntos) y latencia (≥ 5×), no solo exactitud', f'''
<div class="card">{tabla(['Candidato', 'Hueco (puntos)', 'Aceleración p95', 'Calidad', 'Latencia', 'Decisión'], filas_pu, 'sm')}</div>
<div class="grid2" style="margin-top:10px">
 {callout('**† La v1 no es comparable**: p95 con lotes distintos (16 y 32). Suspende en calidad con cualquier protocolo: **' + num(e5['hueco_puntos']) + ' puntos** frente a 4.')}
 {mira(['Solo exactitud: el profesor siempre gana y **no se despliega nada más barato**.', 'Solo latencia: se promociona un modelo que **incumple el acuerdo de calidad**.', 'Entre los que cumplen, el oficial es el de **mayor exactitud**: el duro fp32.'], 'Por qué las dos')}
</div>''' + fuente('resultados/ejercicio5_promocion.json (v1) y resultados/v2_sentimiento.json (v2); las filas del destilado fp32 coinciden con la salida del notebook 06, apartado 10.'),
          'Cómo se promociona un estudiante, con las cifras guardadas. La regla del ejercicio cinco: no alejarse más de cuatro puntos del profesor y ser al menos cinco veces más rápido en el p95. La versión uno suspende en calidad, con más de veintitrés puntos; su aceleración de ciento sesenta y siete veces lleva una daga porque se midió con lotes distintos. En la versión dos se promociona el TinyBERT duro en fp32, con dos coma seis puntos y siete coma siete veces. El destilado en fp32 también cumpliría; el int8 no cumple calidad, y con lote uno no cumple ni la latencia. El criterio es siempre las dos puertas.')

    claves = [l[2:] for l in trozo(fuente_celda('04', buscar('04', '## 4. Conclusiones de MLOps', 'markdown')), 'No basta con', '### Criterio').split('\n') if l.startswith('- ')]
    slide('E', 4, 'Qué registrar', 'el estudiante y el profesor, juntos', 'Se promociona la pareja: profesor y estudiante, con tokenizador, T, α, semilla y protocolo de latencia', f'''
''' + dos_columnas(lista([c.replace('\\(T\\)', 'T').replace('\\(\\alpha\\)', 'α') for c in claves]) + fuente('notebook 04, apartado 4 («Qué registrar junto al estudiante»); el ejemplo, el ejercicio 4 del notebook 05.'),
                    codigo('resultados/ejercicio4_registro_run.json · lo que escribe el ejercicio 4', (RES / 'ejercicio4_registro_run.json').read_text(encoding='utf-8')), '.9fr 1.1fr'),
          'Qué debe quedar registrado junto al estudiante, según el notebook cuatro: la identidad del profesor, con su revisión; la del estudiante, con su arquitectura; los datos, con su semilla; los hiperparámetros de destilación; las métricas de los tres roles y la latencia en un hardware descrito; y el tokenizador, que es parte del modelo. A la derecha está lo que escribe el ejercicio cuatro con las cifras reales de la versión uno. El profesor y el estudiante se promocionan como pareja.')

    slide('E', 4, 'Relación con S5', 'MLflow, alias y producción', 'En S5 esto es un run de MLflow y un alias que se mueve; aquí son un JSON y un archivo', f'''
''' + dos_columnas(tabla(['En este extra', 'En producción (propuesta del notebook 04)'], [
        ['`resultados/*.json` con parámetros y métricas', 'Parámetros, métricas y artefactos de **un mismo run** en MLflow'],
        ['`modelos/*.pt` y el tokenizador', 'Artefactos del run; el profesor y el estudiante **como pareja**'],
        ['Decisión PROMOCIONAR / NO PROMOCIONAR', 'Mover el **alias** del registro (y el rollback, moverlo de vuelta)'],
        ['Latencia medida en esta CPU', 'Volver a medir en el **contenedor real**, con el lote real, en caliente']]) + sin_verificar('**MLflow y alias**: son la propuesta del notebook 04. **Este extra no los usa**: no registra ningún run ni mueve ningún alias.'),
                    mira(['El profesor puede actuar de **sombra** sobre una muestra del tráfico: su desacuerdo con el estudiante es señal de **deriva**.', 'Si **actualizas al profesor**, hay que redestilar, evaluar y promover otra vez.', 'El estudiante **hereda sesgos** y errores del profesor.']) + callout('Para ver un servicio que sigue un alias en producción, ver el extra de **MCP en notebooks** (modelo `retencion-90d` y `@champion`).') + fuente('notebook 04, apartado 4; notebook 07, apartado 4.'), '1.1fr .9fr'),
          'La relación con el resto de la sesión cinco. El notebook cuatro propone que lo que aquí es un JSON con parámetros y métricas sea, en producción, un run de MLflow, y que la promoción sea mover un alias del registro, con el rollback como moverlo de vuelta. Es una propuesta del notebook: este extra no usa MLflow ni mueve ningún alias, y eso está sin verificar. Tres ideas de producción del notebook: el profesor como sombra sobre una muestra del tráfico para detectar deriva, redestilar si cambia el profesor, y recordar que el estudiante hereda los sesgos del profesor. Para ver un alias funcionando, está el extra de MCP en notebooks.')

    # ---------------------------------------------------------------- F · Límites y cierre
    slide('F', 3, 'Qué quedó sin verificar', 'qué se comprobó y qué no', 'Qué se comprobó de verdad y qué quedó sin verificar', f'''
<div class="grid2">
 <div class="card"><h3 class="okc">Comprobado</h3>''' + lista([
        f'Los **ocho notebooks** se ejecutaron **una vez**, en **CPU**, con Python **{PY}** en **Linux**; las salidas y los JSON de las diapositivas son esas.',
        'Las **versiones** que imprime el notebook 00 coinciden con las del archivo de requisitos.',
        'Cada figura es **la que produce su notebook**; cada cifra, la de su JSON o su salida.']) + '''</div>
 <div class="card"><h3 class="malc">Sin verificar</h3>''' + lista([
        '**Windows** (PowerShell, venv, el bucle de ejecución): solo está en el README.',
        '**Codespace** y cualquier otro entorno remoto: no se probó.',
        '**Alumnado**: nadie del curso lo ha hecho; los tiempos son de **una** CPU y pueden variar mucho.',
        '**GPU**: el notebook 00 salió «cpu-only»; que acelere el 03 es lo que dice el README, no algo medido.',
        '**Proxy corporativo**, **instalar desde cero** con el archivo de requisitos, **ONNX** y **MLflow/alias**: sin comprobar.']) + '''</div>
</div>''',
          'Diapositiva de honestidad. Lo comprobado: los ocho notebooks se ejecutaron una sola vez, en CPU, con Python tres doce en Linux; las versiones que imprime el notebook cero coinciden con las del archivo de requisitos; y cada figura y cada cifra de esta presentación sale del notebook o del archivo de resultados que la produjo. Lo no comprobado: Windows, Codespace, alumnado, GPU, proxy corporativo, la instalación desde cero, la exportación a ONNX y el uso de MLflow con alias. Los tiempos son de una máquina.')

    n_test = v2['n_test']
    una_frase = 100 / n_test
    dif_v2 = (V['estudiante_duro']['exactitud'] - V['estudiante_destilado']['exactitud']) * 100
    assert round(dif_v2 / una_frase) == 1, 'la diferencia duro-destilado de la v2 ya no es de una frase: revisa el texto'
    slide('F', 4, 'Límites honestos', 'qué no prueban estas cifras', 'Estas cifras son una sola ejecución en CPU con muestras pequeñas: sirven para entender, no para concluir', f'''
<div class="grid2">
 {card('Una ejecución, una semilla', [f'Semilla **42**, sin repeticiones ni barras de error.', f'Con **{n_test}** frases de test, **una** frase son **{num(una_frase, 3)} puntos**; duro y destilado de la v2 distan **{num(dif_v2, 3)} puntos**: una frase.'])}
 {card('Mejor época en test', ['El notebook 06 guarda «la mejor época en test» de cada run, no la última: la cifra es algo **optimista**.', 'Un conjunto de validación aparte lo evitaría.'])}
 {card('CPU y latencia', ['Latencia de **una** CPU con **4 hilos**; en producción hay que **remedirla**.', 'Con **lote 1** no se llega a 5×.', '**GPU**: sin verificar; el 03 no se midió con GPU.'])}
 {card('Casos acotados', ['MNIST con **400 etiquetas** es un montaje didáctico, a propósito.', 'Solo **SST-2** (inglés, binario), con **un** profesor y **dos** estudiantes.', 'T y α **no se afinaron**: son valores de partida.'])}
</div>''' + fuente('resultados/*.json; notebook 06 (apartado 4: «Se guarda la mejor época en test»); notebook 01 («valores de partida razonables»).'),
          'Los límites, dichos sin adorno. Es una sola ejecución con una semilla, sin barras de error. Con ochocientas setenta y dos frases de test, una frase vale poco más de once centésimas de punto, y la diferencia entre el duro y el destilado de la versión dos es exactamente una frase: no se puede decir que uno gane al otro. El notebook seis guarda la mejor época mirando el test, lo que hace la cifra algo optimista. La latencia es de una CPU con cuatro hilos. Y los casos son acotados: MNIST con cuatrocientas etiquetas es un montaje didáctico y la temperatura y el alfa no se afinaron.')

    slide('F', 3, 'Resumen', 'el mensaje', 'Destilar ayuda si el profesor merece copiarse y el estudiante parte bien; lo decide la medida', f'''
<div class="msg">Un estudiante <b>se promociona</b> cuando cumple <b>calidad y latencia a la vez</b>: en esta ejecución lo hace <b>TinyBERT duro en fp32</b>, no el GRU de la v1.</div>
<div class="grid4" style="margin-top:18px">
 ''' + kpi(f'{pc(S["estudiante_duro"]["exactitud"], 1)} → {pc(S["estudiante_destilado"]["exactitud"], 1)}', f'v1: el GRU **duro** frente al **destilado**; el profesor, {pc(acc_p, 1)} (resultados/sentimiento.json)') + kpi(pc(V['estudiante_duro']['exactitud']), f'v2: **TinyBERT duro fp32**; el profesor, {pc(v2["exactitud_profesor"])} (resultados/v2_sentimiento.json)') + kpi(f'{num(pu["oficial"]["hueco_puntos"])} pts · {num(pu["oficial"]["aceleracion_p95"])}×', 'hueco y aceleración p95 del oficial frente a las puertas: **≤ 4 puntos** y **≥ 5×**') + kpi('1 frase', f'es la diferencia entre el duro y el destilado de la v2 (**{n_test}** frases de test): la destilación no gana') + '''
</div>
<div style="text-align:center;margin-top:44px;font-size:44px;font-weight:700;color:var(--acento)">¿Preguntas?</div>''',
          'Cierre con un único mensaje: un estudiante se promociona cuando cumple calidad y latencia a la vez, y en esta ejecución lo hace el TinyBERT duro en fp32, no el GRU de la versión uno. Las cuatro cifras: el GRU de la versión uno pasa de sesenta y cinco a sesenta y siete por ciento con destilación, lejos del noventa y uno del profesor; el TinyBERT duro llega a ochenta y ocho coma cuatro; el oficial cumple las dos puertas con dos coma seis puntos y siete coma siete veces; y la destilación no gana al duro en la versión dos, porque la diferencia es una frase de ochocientas setenta y dos.')

    suma = sum(int(m) for m in re.findall(r'data-min="(\d+)"', ''.join(SLIDES)))
    assert suma == TOTAL_MIN, f'TOTAL_MIN ({TOTAL_MIN}) no coincide con la suma de minutos ({suma})'


def md_plain(t):
    return t


_UTILS = None


def _src_utils():
    global _UTILS
    if _UTILS is None:
        _UTILS = (AQUI / 'src' / 'destilacion_utils.py').read_text(encoding='utf-8')
    return _UTILS


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
.src{margin:0;padding:7px 11px;font-family:var(--mono);font-size:12px;line-height:1.38;white-space:pre-wrap;overflow-wrap:anywhere}
.grande .src{font-size:13.5px}
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
  f.innerHTML=`<span>ML e IA · S5 · Extra: Destilación en notebooks</span><span><b>${esc(PARTES[s.dataset.part]||'')}</b> · ${i+1} / ${N}</span>`;s.appendChild(f)});
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
.fuente{font-size:12.5px;line-height:1.35;color:var(--suave);margin-top:2px}
.fuente .mono{font-size:.95em}
.tbl td .mono{font-size:12.5px}
.grid2>.callout{align-self:start}
.cover .grid3 .card .list li{font-size:14px}
"""
EXTRA_CSS2 = r"""
.tbl.sm td{font-size:13.5px;padding:4px 8px}.tbl.sm th{font-size:11.5px}
.orig{color:#5b6472}.orig .mono{font-size:.95em}
.dec{display:inline-block;font-weight:700;font-size:12px;padding:1px 8px;border-radius:999px;border:1px solid}
.dec.ok{color:var(--ok);border-color:#86c79c;background:#ecf8f0}.dec.mal{color:var(--mal);border-color:#e5a3a3;background:#fdeeee}
.thumbs .cap img{width:100%;object-fit:contain}
.slide .small .tag{margin-right:4px}
.cap .zoom{display:inline-block;align-self:flex-start;max-width:100%}
.tbl.nw td{white-space:nowrap}.tbl.nw td:first-child{white-space:normal}
.grande .card .list li{font-size:19px;line-height:1.45}
"""
CSS = CSS + EXTRA_CSS + EXTRA_CSS2


def html_completo():
    convertir_figuras()
    construir()
    js = JS.replace('__PARTES__', json.dumps(PARTES, ensure_ascii=False))
    partes = ''.join(f'<button class="part" data-p="{k}">{esc(v)}</button>' for k, v in PARTES.items())
    return ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>Extra de S5: Destilación de modelos en notebooks · ML e IA: de desarrollo a producción</title>\n'
            f'<!-- Generado por generar.py: no se edita a mano. -->\n<style>{CSS}</style>\n</head>\n<body>\n'
            '<div id="prog"></div>\n<div id="viewport"><div id="stage">\n\n' + '\n\n'.join(SLIDES) + '\n\n</div></div>\n\n'
            '<aside id="notes" aria-label="Notas del profesor"><h3>Notas del profesor</h3><div id="notetext"></div><p class="small" id="notemin"></p></aside>\n'
            '<div id="index" aria-label="Índice"><h2>Índice</h2><div class="grid" id="idxgrid"></div></div>\n'
            '<div id="zoombox" aria-label="Figura ampliada"><p>Esc o clic para cerrar</p><img id="zoomimg" alt=""></div>\n'
            '<nav id="bar" aria-label="Controles">\n'
            '  <button id="bprev" aria-label="Anterior">←</button><button id="bnext" aria-label="Siguiente">→</button>\n'
            f'  <span id="count">1 / 1</span><span id="clockref" title="Minuto planificado acumulado (propuesta)"></span>\n  {partes}\n'
            '  <span class="sp"></span>\n'
            '  <a id="bhome" href="../index.html" title="Volver al índice de la sesión S5">⌂ Índice</a><button id="bidx">Índice (O)</button><button id="bnotes">Notas (S)</button><button id="bfull">Pantalla completa (F)</button>\n'
            '</nav>\n'
            '<noscript>Esta presentación necesita JavaScript. El mismo contenido está en los ocho notebooks de esta carpeta.</noscript>\n\n'
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
        SALIDA.write_bytes(nuevo.encode('utf-8'))      # LF también en Windows
        minutos = sum(int(m) for m in re.findall(r'data-min="(\d+)"', nuevo))
        print(f'escrito {SALIDA.name}: {len(SLIDES)} diapositivas, {minutos} min')


if __name__ == '__main__':
    main()
