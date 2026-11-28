"""Genera la presentación «Extra de S5: RAG en notebooks» (index.html, junto a este archivo), tipo laboratorio.

Qué cuenta: cómo se monta un RAG completo en CPU, paso a paso, con los siete cuadernos de esta carpeta (00 a 06): preparar el entorno,
vectores y similitud, troceado e índice, recuperación (BM25, densa, híbrida), generación con un LLM pequeño local con y sin recuperación,
el pipeline y su evaluación, y los ejercicios. Mensaje: un RAG se mide en dos sitios (¿llegó el contexto? ¿lo usó el modelo?) y con un
corpus pequeño y un LLM de 0,5B las cifras son una brújula, no un benchmark.

TODO lo que se enseña como código, salida o cifra se LEE de esta carpeta (los .ipynb con sus salidas guardadas, resultados/*.json,
README.md, requisitos-extra-rag.txt y scripts/): la presentación no ejecuta los notebooks ni descarga modelos y no puede contar otra cosa
que lo que se ejecutó. Las figuras de resultados/ (capturas reales de lo que producen los notebooks) se convierten a WebP en img/.

El visor (CSS y JavaScript: ← → · O índice · S notas · F pantalla completa · botones «Copiar» · lupa con zoom al clic · pie «x / total»)
es el MISMO que el del laboratorio de agentes de S5 y el del extra de MCP, copiado aquí (no se importa); solo cambia el rótulo del pie.

Uso:  python generar.py              escribe index.html (y convierte las figuras a img/*.webp si faltan o están viejas)
      python generar.py --comprobar  no escribe; sale con 1 si index.html o img/ no están al día
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / 'index.html'
IMG = AQUI / 'img'
RESULTADOS = AQUI / 'resultados'

NOTEBOOKS = {
    '00': '00-introduccion-y-setup.ipynb',
    '01': '01-embeddings-y-similitud.ipynb',
    '02': '02-chunking-e-indexado.ipynb',
    '03': '03-recuperacion-y-busqueda.ipynb',
    '04': '04-generacion-con-llm-local.ipynb',
    '05': '05-pipeline-completo-y-evaluacion.ipynb',
    '06': '06-ejercicios.ipynb',
}
PARTES = {'A': 'Idea', 'B': 'Preparar', 'C': 'Indexar', 'D': 'Recuperar', 'E': 'Generar', 'F': 'Límites'}
NOMBRES_PARTE = {'A': 'Qué es RAG y por qué', 'B': 'Preparar el entorno', 'C': 'Ingesta: vectores e índice',
                 'D': 'Consulta: recuperar', 'E': 'Generar y evaluar', 'F': 'Practicar, fallos y límites'}
PIE = 'ML e IA · S5 · Extra: RAG en notebooks'

# Figuras de resultados/ -> (notebook que las dibuja, rótulo EXACTO de lo que muestra). Un rótulo = una imagen.
FIGURAS = {
    'fig_similitud_coseno': ('01', 'Mapa de calor «Similitud coseno entre frases de ejemplo»: 16 frases (01 a 16) en filas y columnas, rotuladas por tema '
                                   '(Docker, Kubernetes, MLflow/CI, Curso, NubeAndina); la diagonal es amarilla (coseno 1) y la barra de color va de 0 a 1'),
    'fig_pca_embeddings': ('01', 'Dispersión «Frases de ejemplo proyectadas con PCA (2-D)»: las mismas 16 frases, numeradas y con un color por tema, '
                                 'sobre los ejes PCA 1 y PCA 2'),
    'fig_chunking_longitudes': ('02', 'Histograma «Distribución de longitudes según la estrategia»: longitud del fragmento (de 0 a 400 caracteres) frente a '
                                      'frecuencia, con tres series superpuestas: fijo, solape y parrafos'),
    'fig_mrr': ('03', 'Barras «MRR (primer documento relevante)»: BM25 0,96, denso 0,91 e híbrido 0,96'),
    'fig_recall_at_k': ('03', 'Líneas «Recall@k según el método de recuperación» para k = 1, 3, 5 y 8 con BM25, denso e híbrido; la línea de BM25 queda '
                              'tapada por la del híbrido porque valen lo mismo'),
    'fig_con_sin_rag': ('04', 'Barras «Misma pregunta, con y sin RAG»: cobertura de hechos (o abstención) en q11, q13, q03 y q19; las barras «sin RAG» '
                              '(rojas) valen 0 y no se ven; las «con RAG» (verdes) valen 0,33, 0,5, 0,5 y 1,0'),
    'fig_mandos_chunk_k': ('05', 'Dos paneles: «Efecto del tamaño de fragmento» (chunk de 200, 400 y 800 caracteres, con recall@5 y MRR) y '
                                 '«Efecto de k (índice por defecto)» (k de 1 a 8, con recall@k y MRR)'),
    'fig_latencia_etapas': ('05', 'Barras «Latencia por etapa (CPU, LLM local)»: segundos de media en recuperación (barra casi invisible) y en '
                                  'generación (barra cercana a 1,4 s)'),
}


# ------------------------------------------------------------------------------------------------------------------------
# Lectura de los notebooks, de resultados/, del README y de los requisitos (única fuente de código, salidas y cifras)
# ------------------------------------------------------------------------------------------------------------------------
_CACHE = {}


def _txt(x):
    return ''.join(x) if isinstance(x, list) else x


def _nb(n):
    if n not in _CACHE:
        _CACHE[n] = json.loads((AQUI / 'notebooks' / NOTEBOOKS[n]).read_text(encoding='utf-8'))['cells']
    return _CACHE[n]


def celda(n, clave, tipo='code'):
    """Índice de la primera celda del tipo dado cuyo código (o texto) contiene `clave`."""
    for i, c in enumerate(_nb(n)):
        if c['cell_type'] == tipo and clave in _txt(c['source']):
            return i
    raise KeyError(f'notebook {n}: ninguna celda {tipo} contiene «{clave}»')


def fuente_celda(n, i):
    return _txt(_nb(n)[i]['source'])


def ec(n, i):
    """Número que ve el alumnado en Jupyter: In [n]."""
    return _nb(n)[i].get('execution_count')


def ref(n, clave):
    return f'notebook {n}, celda [{ec(n, celda(n, clave))}]'


_RUIDO = re.compile(r'^(Loading weights|Batches:|<Figure size)|FutureWarning|^\s+self\.dim = |^Warning: You are sending')


def limpia(texto):
    lineas = [l for l in texto.split('\n') if not _RUIDO.search(l)]
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(lineas)).strip('\n')


def salida_celda(n, i):
    partes = []
    for o in _nb(n)[i].get('outputs', []):
        t = _txt(o['text']) if 'text' in o else _txt(o.get('data', {}).get('text/plain', ''))
        partes.append(t if t.endswith('\n') else t + '\n')      # una barra de progreso sin salto no debe tragarse la línea siguiente
    return limpia(''.join(partes))


def salida(n, clave):
    return salida_celda(n, celda(n, clave))


def trozo(texto, desde, hasta=None):
    """Líneas desde la primera que contiene `desde` hasta la anterior a la primera posterior que contiene `hasta` (o el final)."""
    lineas = texto.split('\n')
    ini = next(k for k, l in enumerate(lineas) if desde in l)
    fin = len(lineas)
    if hasta is not None:
        fin = next(k for k in range(ini + 1, len(lineas)) if hasta in lineas[k])
    return '\n'.join(lineas[ini:fin]).rstrip()


def lineas_con(texto, *prefijos):
    return '\n'.join(l for l in texto.split('\n') if l.startswith(prefijos))


def quitar_comentarios(texto):
    return '\n'.join(re.sub(r'\s{2,}#.*$', '', l) for l in texto.split('\n'))


def res(nombre):
    return json.loads((RESULTADOS / f'{nombre}.json').read_text(encoding='utf-8'))


README = (AQUI / 'README.md').read_text(encoding='utf-8')
REQUISITOS = (AQUI / 'requisitos-extra-rag.txt').read_text(encoding='utf-8')


def linea_readme(prefijo):
    for l in README.split('\n'):
        if l.strip().startswith(prefijo):
            return l.strip()
    raise KeyError(f'README: ninguna línea empieza por «{prefijo}»')


def tabla_readme(encabezado):
    """Filas (listas de celdas) de la primera tabla Markdown que sigue a `encabezado`."""
    resto = README.split(encabezado, 1)[1]
    filas = []
    for l in resto.split('\n'):
        if l.startswith('|'):
            celdas_ = [c.strip() for c in l.strip().strip('|').split('|')]
            if not set(''.join(celdas_)) <= set('-: '):
                filas.append(celdas_)
        elif filas:
            break
    return filas


def paquetes():
    return {l.split('==')[0]: l.split('==')[1] for l in REQUISITOS.split('\n') if '==' in l and not l.startswith('#')}


def c(x, d=2):
    """Número con coma decimal."""
    return f'{x:.{d}f}'.replace('.', ',')


def miles(x):
    return f'{x:,}'.replace(',', ' ')


# ------------------------------------------------------------------------------------------------------------------------
# Piezas del visor (copiadas del extra de MCP, que las copió del laboratorio de agentes de S5) y propias
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


def term(titulo, lineas, prompt='$'):
    """Terminal con una orden por línea y su botón ⧉. Las líneas que empiezan por # son comentarios (no se copian)."""
    filas = []
    for l in lineas:
        if l.startswith('#'):
            filas.append(f'<div class="tln c">{esc(l)}</div>')
        else:
            filas.append(f'<div class="tln"><span class="ps">{esc(prompt)}</span> <code>{esc(l)}</code><button class="cp" data-t="{esc(l)}" title="Copiar">⧉</button></div>')
    todo = '\n'.join(l for l in lineas if not l.startswith('#'))
    return (f'<div class="term"><div class="bar"><em>{esc(titulo)}</em><button class="cp cpall" data-t="{esc(todo)}">Copiar todo</button></div>'
            f'<div class="tls">{"".join(filas)}</div></div>')


def codigo(titulo, texto):
    """Un fragmento de código que se copia entero con «Copiar todo»."""
    return (f'<div class="term"><div class="bar"><em>{esc(titulo)}</em><button class="cp cpall" data-t="{esc(texto)}">Copiar todo</button></div>'
            f'<pre class="src">{esc(texto.rstrip())}</pre></div>')


def fig(nombre, alto=None):
    """Una figura real de resultados/ (clic = ampliar) con su rótulo exacto y el notebook y la celda de los que sale."""
    nb, rotulo = FIGURAS[nombre]
    celda_ = celda(nb, nombre + '.png')
    origen = f'notebook {nb}, celda [{ec(nb, celda_)}] → resultados/{nombre}.png'
    estilo = f' style="max-height:{alto}px"' if alto else ''
    return (f'<figure class="cap" data-img="{nombre}.webp"><button class="zoom" data-src="img/{nombre}.webp" data-alt="{esc(rotulo)}" title="Ampliar (Esc cierra)">'
            f'<img src="img/{nombre}.webp" alt="{esc(rotulo)}"{estilo}><span class="lupa">{LUPA} Ampliar</span></button>'
            f'<figcaption><span class="tag ok">Figura real</span> {esc(rotulo)}. <span class="origen">Sale del {esc(origen)}.</span></figcaption></figure>')


def lista(items):
    return '<ul class="list">' + ''.join(f'<li>{md(i)}</li>' for i in items) + '</ul>'


def mira(items, titulo='Qué debes ver'):
    return f'<div class="card mira"><h3>{esc(titulo)}</h3>{lista(items)}</div>'


def si_falla(items):
    return f'<div class="card falla"><h3>Si falla</h3>{lista(items)}</div>'


def tabla(cab, filas):
    th = ''.join(f'<th>{md(x)}</th>' for x in cab)
    tr = ''.join('<tr>' + ''.join(f'<td>{md(x)}</td>' for x in f) + '</tr>' for f in filas)
    return f'<table class="tbl"><tr>{th}</tr>{tr}</table>'


def kpi(valor, texto, color=''):
    return f'<div class="card kpi"><b class="n {color}">{esc(valor)}</b><p class="small">{md(texto)}</p></div>'


def real(titulo, texto):
    """Salida guardada de un notebook (caja verde)."""
    return f'<div class="realbox"><div class="rk">{esc(titulo)}</div><pre>{esc(texto)}</pre></div>'


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


SLIDES = []
_N = {}
GRANDES = {'Qué no está verificado', 'Resumen'}


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


def _marca(idf):
    return (f'<defs><marker id="{idf}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
            f'<path d="M0 0 L10 5 L0 10 z" fill="#0b5cad"/></marker></defs>')


def svg_ingesta():
    """Tubería de ingesta: documentos -> trozos -> vectores -> índice (cifras de resultados/indexado.json)."""
    ix = res('indexado')
    g = [_marca('fi')]
    xs = [6, 296, 586, 876]
    y = 40
    g.append(_caja(xs[0], y, 218, ['Documentos', f'{ix["n_documentos"]} archivos .md', 'datos/corpus/'], 'nodo', 96))
    g.append(_caja(xs[1], y, 218, ['Trocear (chunking)', f'{ix["tamano"]} caracteres', f'solape de {ix["solape"]}'], 'nodo puerta', 96))
    g.append(_caja(xs[2], y, 218, ['Embeddings', 'MiniLM multilingüe', f'{ix["dim"]} números por trozo'], 'nodo puerta', 96))
    g.append(_caja(xs[3], y, 218, ['Índice vectorial', 'FAISS y NumPy', f'{ix["n_fragmentos"]} fragmentos'], 'nodo ok', 96))
    for k in range(3):
        g.append(f'<path d="M{xs[k] + 218} {y + 48} L{xs[k + 1] - 3} {y + 48}" class="fl" marker-end="url(#fi)"/>')
    for x, t in zip(xs, ['antes de todo', 'notebook 02', 'notebooks 01 y 02', 'notebook 02: modelos/']):
        g.append(f'<text x="{x + 109}" y="{y + 126}" class="t2">{esc(t)}</text>')
    g.append('<text x="550" y="14" class="t2">INGESTA: se hace una vez, y de nuevo cuando cambian los documentos</text>')
    return ('<svg viewBox="0 0 1100 190" role="img" aria-label="Tubería de ingesta: los documentos se trocean, cada trozo se convierte en un vector y los '
            'vectores se guardan en un índice">' + ''.join(g) + '</svg>')


def svg_consulta():
    """Tubería de consulta, con el desvío «sin RAG» que se compara en el notebook 04."""
    g = [_marca('fc')]
    xs = [6, 226, 446, 666, 886]
    y = 24
    g.append(_caja(xs[0], y, 190, ['Pregunta', 'en lenguaje natural', ''], 'nodo', 96))
    g.append(_caja(xs[1], y, 190, ['Recuperar top-k', 'BM25 + vectores', 'fusión RRF'], 'nodo puerta', 96))
    g.append(_caja(xs[2], y, 190, ['Prompt', 'reglas + fragmentos', '+ pregunta'], 'nodo puerta', 96))
    g.append(_caja(xs[3], y, 190, ['LLM local', 'Qwen2.5-0.5B-Instruct', 'en CPU'], 'nodo', 96))
    g.append(_caja(xs[4], y, 190, ['Respuesta', 'con citas', '[doc::#n]'], 'nodo ok', 96))
    for k in range(4):
        g.append(f'<path d="M{xs[k] + 190} {y + 48} L{xs[k + 1] - 3} {y + 48}" class="fl" marker-end="url(#fc)"/>')
    g.append(_caja(226, 150, 190, ['Índice de la ingesta', '', ''], 'nodo ok', 40))
    g.append(f'<path d="M321 150 L321 {y + 98}" class="fl dis" marker-end="url(#fc)"/>')
    g.append(f'<path d="M101 {y + 98} L101 232 L761 232 L761 {y + 100}" class="fl dis" marker-end="url(#fc)"/>')
    g.append('<text x="430" y="226" class="t2">SIN RAG: la pregunta va directa al LLM y responde de memoria (la prueba de control)</text>')
    return ('<svg viewBox="0 0 1100 245" role="img" aria-label="Tubería de consulta: la pregunta recupera fragmentos del índice, se arma un prompt con ellos, '
            'el LLM local redacta la respuesta con citas; el desvío sin RAG envía la pregunta directa al LLM">' + ''.join(g) + '</svg>')


# ------------------------------------------------------------------------------------------------------------------------
# Contenido
# ------------------------------------------------------------------------------------------------------------------------
def construir():
    SLIDES.clear()
    _N.clear()

    ix = res('indexado')
    rc = res('recuperacion')
    pl = res('pipeline')
    gn = res('generacion')
    em = res('embeddings')
    pq = {p['id']: p for p in json.loads((AQUI / 'datos' / 'preguntas.json').read_text(encoding='utf-8'))['preguntas']}
    det = {d['id']: d for d in gn['detalle']}
    pk = paquetes()

    corpus_txt = salida('02', 'documentos = cargar_corpus')
    m_corpus = re.search(r'(\d+) documentos, (\d+) caracteres, (\d+) palabras', corpus_txt)
    n_docs, n_car, n_pal = (int(x) for x in m_corpus.groups())
    n_pregs = len(pq)
    n_hecho = sum(1 for p in pq.values() if p['tipo'] != 'no_esta')

    # ---------------------------------------------------------------- A · Qué es RAG y por qué
    slide('A', 3, 'Portada', 'ML e IA: de desarrollo a producción · S5 · extra', 'RAG en notebooks: que el LLM conteste con tus documentos y cite de dónde', f'''
<div class="cover">
 <p class="sub">Montas un <b>RAG completo en CPU</b>, sin API de pago: troceas y indexas un corpus en español, recuperas con <b>BM25, vectores y los dos juntos</b>, se lo das a un <b>LLM de 0,5B</b> y <b>mides</b> qué mejora (y qué no) con y sin recuperación.</p>
 <div class="chips"><span class="tag">7 notebooks (00-06)</span><span class="tag">{n_docs} documentos · {ix["n_fragmentos"]} fragmentos</span><span class="tag">BM25 · denso · híbrido</span><span class="tag">FAISS y NumPy</span><span class="tag">Con y sin RAG</span><span class="tag">Solo CPU</span></div>
 <div class="grid3" style="margin-top:20px">
  {card('Objetivos', ['Entender las **dos tuberías** de un RAG: ingesta y consulta.', 'Ejecutar y **leer** cada notebook: qué orden, qué salida, qué debes ver.', 'Medir **recuperación** (recall@k, MRR) y **generación** (cobertura de hechos) por separado.'])}
  {card('Cómo se usa', ['Cada bloque: la **orden o celda** (botón **⧉** para copiarla), la **salida guardada** y «si falla».', 'Las cifras salen de los notebooks y de `resultados/`; cada una **con su fuente**.', '**← →** avanzan · **O** índice · **S** notas · **F** pantalla completa.'])}
  {card('Honestidad desde el principio', ['Los notebooks se ejecutaron en **Linux, solo CPU, modo rápido** (salida del notebook 00).', 'Corpus de **9 documentos** y **18 preguntas** de recuperación: una **brújula**, no un benchmark.', '**Sin verificar:** Windows, Codespace, alumnado y un LLM mayor.'])}
 </div>
</div>''',
          'Portada del extra de la sesión 5. Es un laboratorio: el alumnado replica cada paso en su portátil. Se monta un RAG completo en CPU con siete notebooks: preparación, vectores, troceado e índice, recuperación, generación con un modelo pequeño, pipeline con evaluación y ejercicios. Diga desde el principio lo que se probó y lo que no: los notebooks se ejecutaron en Linux, solo CPU y en modo rápido, y las cifras de esta presentación son las guardadas en ellos. Windows, Codespace, el alumnado y un modelo mayor están sin verificar. Pulse S para ver estas notas en cada diapositiva.')

    d_q11, d_q19, d_q13 = det['q11'], det['q19'], det['q13']
    primera = lambda t: t.split('. ')[0].rstrip('.') + '.'
    slide('A', 2, 'Por qué RAG', 'el LLM no sabe tus datos', 'Un LLM no conoce tus documentos: sin ellos, inventa con total seguridad', f'''
<div class="grid3">
 {card('Alucinaciones', ['Afirma cifras, nombres o normas que **no existen**, con tono seguro.', 'Aquí se usa una empresa **ficticia** (NubeAndina): no puede haberla memorizado.'])}
 {card('Conocimiento que caduca', ['El modelo se entrenó con un **corte de fecha**.', 'El reglamento de *este* semestre o el alias del modelo campeón no están en sus pesos.'])}
 {card('Conocimiento privado', ['Políticas internas, entregas o experimentos **no deben** estar en un modelo público.', 'Van en un **corpus que tú indexas** y controlas.'])}
</div>
<div class="card" style="margin-top:10px"><h3>Lo que respondió el LLM de 0,5B SIN contexto (salida guardada)</h3>''' + tabla(['Pregunta', 'Sin RAG respondió', 'El corpus dice'], [
        ['**q11** · días de vacaciones de un empleado de NubeAndina', primera(d_q11['respuesta_sin_rag']), f'**{pq["q11"]["hechos"][0]}**'],
        ['**q13** · quién es la Delegada de Protección de Datos', primera(d_q13['respuesta_sin_rag']), f'**{pq["q13"]["hechos"][0]}**'],
        ['**q19** · teléfono de la cafetería de la sede', primera(d_q19['respuesta_sin_rag']), 'No está en el corpus: **debería abstenerse**']]) + '''</div>
<div style="margin-top:8px">''' + callout('RAG no es la única respuesta (también existen el ajuste fino, la destilación, las herramientas y los agentes), pero es la **más directa cuando la información vive en documentos y cambia más rápido que el modelo**.') + '</div>'
          + fuente(f'notebook 00 (apartado «Por qué hace falta»); respuestas sin RAG en `resultados/generacion.json` ({ref("04", "pipeline = PipelineRAG(")}).'),
          'Por qué hace falta RAG. Tres problemas: alucinaciones, conocimiento que caduca y conocimiento privado. La tabla es real: son las respuestas del modelo pequeño sin contexto, guardadas en el notebook 4. Cada respuesta suena segura y está mal: quince días en vez de veintidós, un nombre inventado para la delegada de datos y un teléfono inventado para una cafetería que no existe en el corpus. Ojo: es un modelo de 0,5B parámetros; los grandes aciertan más, pero el problema de fondo, no conocer tus datos, es el mismo. RAG no sustituye al ajuste fino ni a los agentes; es la opción más directa cuando el conocimiento está en documentos.')

    slide('A', 2, 'La tubería de ingesta', 'documentos → vectores → índice', 'Ingesta: se trocean los documentos y cada trozo pasa a ser un vector en un índice', f'''
<div class="card">{svg_ingesta()}</div>
<div class="grid3" style="margin-top:12px">
 {card('Qué es un trozo', ['Un *chunk* es la unidad que se **embebe y se recupera**: aquí, 400 caracteres con 80 de solape.', 'Muy grande: la pregunta encaja con una esquina. Muy pequeño: se **corta un hecho** por la mitad.'])}
 {card('Qué es un embedding', ['Un **vector de 384 números** que intenta capturar el significado de un texto corto.', 'Dos textos de significado parecido quedan **cerca**, aunque no compartan palabras.'])}
 {card('Qué es el índice', ['Una matriz de vectores + los textos: se busca por **similitud coseno**.', 'Se guarda en `modelos/` (FAISS y NumPy) y los notebooks siguientes lo **reutilizan**.'])}
</div>''' + fuente(f'`resultados/indexado.json` ({n_docs} documentos, {ix["n_fragmentos"]} fragmentos, dimensión {ix["dim"]}) y notebooks 01 y 02.'),
          'La primera tubería, la de ingesta. Se hace una vez y se repite cuando cambian los documentos. Los documentos markdown se trocean en fragmentos de cuatrocientos caracteres con ochenta de solape; cada fragmento se convierte en un vector de trescientos ochenta y cuatro números con un modelo multilingüe pequeño; y los vectores se guardan en un índice, con FAISS y también con NumPy, que aquí hacen lo mismo. Todo esto ocurre en los notebooks uno y dos, y el índice se guarda en la carpeta modelos para no repetirlo.')

    slide('A', 2, 'La tubería de consulta', 'recuperar → prompt → LLM', 'Consulta: la pregunta trae k fragmentos, y el LLM responde solo con ellos y los cita', f'''
<div class="card">{svg_consulta()}</div>
<div class="grid3" style="margin-top:12px">
 {card('Recuperar', ['**BM25** (palabras), **denso** (vectores) o **híbrido** (fusión RRF de las dos listas).', 'Se queda con los **k mejores** (en la generación, k = 4).'])}
 {card('El prompt', ['El sistema le **prohíbe inventar** y le pide citas `[doc::#n]`.', 'Si la respuesta no está, debe decir exactamente que **no la encuentra**.'])}
 {card('El control', ['Para saber qué aporta RAG hay que comparar con **la misma pregunta sin contexto**.', 'Lo hace el notebook 04, y mide la **cobertura de hechos**.'])}
</div>''' + fuente('notebook 00 (diagrama del pipeline) y notebook 04 (apartados 2 y 3).'),
          'La segunda tubería, la de consulta. La pregunta se usa para recuperar los k fragmentos más parecidos del índice, con BM25, con vectores o con las dos cosas fusionadas. Con ellos se arma un prompt: unas reglas de sistema que prohíben inventar y piden citar, los fragmentos y la pregunta. El modelo local redacta la respuesta y cita los fragmentos. La línea de puntos es el control: la misma pregunta enviada directamente al modelo, sin contexto. Comparar las dos es lo que enseña el cuaderno 4.')

    filas_mapa = [f for f in tabla_readme('## Índice y orden de ejecución') if f[0].isdigit()]
    produce = {'00': 'nada (solo comprueba)', '01': '`embeddings.json`, `fig_similitud_coseno`, `fig_pca_embeddings`', '02': '`indexado.json`, `modelos/indice_faiss`, `modelos/indice_numpy`, `fig_chunking_longitudes`',
               '03': '`recuperacion.json`, `fig_recall_at_k`, `fig_mrr`', '04': '`generacion.json`, `fig_con_sin_rag`', '05': '`pipeline.json`, `fig_mandos_chunk_k`, `fig_latencia_etapas`', '06': 'nada (ejercicios con soluciones)'}
    slide('A', 2, 'Mapa del extra', 'siete notebooks, en orden', 'Siete notebooks que se ejecutan en orden: cada uno deja algo que usa el siguiente', '<div class="card">' + tabla(['Notebook', 'Qué haces', 'Qué deja guardado'], [
        [f'**{f[0]}**', f[2], produce[f[0]]] for f in filas_mapa]) + '</div>' + callout('**El orden importa:** el 03 lee el índice que genera el 02; el 04 y el 05 usan ese índice y un LLM local; el 06 se puede abrir después del 02 (varias soluciones reutilizan el índice).', 'margin-top:10px')
          + fuente('README.md (tabla «Índice y orden de ejecución») y las celdas que guardan cada archivo (`guardar_json`, `savefig`).'),
          'Mapa de los siete notebooks. El cero comprueba el entorno; el uno enseña embeddings y similitud; el dos trocea el corpus y construye el índice; el tres compara las tres formas de recuperar y mide recall y MRR; el cuatro genera con y sin contexto; el cinco junta todo en un pipeline y mide los mandos de tamaño de trozo y k; el seis son ejercicios con soluciones. El orden importa porque el tres lee el índice del dos y el cuatro y el cinco usan ese índice. Cada notebook deja archivos en modelos y en resultados, que son los que aparecen en esta presentación.')

    # ---------------------------------------------------------------- B · Preparar
    fijos = [('torch', pk['torch']), ('faiss-cpu', pk['faiss-cpu']), ('sentence-transformers', pk['sentence-transformers']), ('transformers', pk['transformers']),
             ('rank-bm25', pk['rank-bm25']), ('scikit-learn', pk['scikit-learn'])]
    slide('B', 2, 'Requisitos e instalación', 'entorno del curso o uno nuevo', 'Primero el entorno: activas `env-ia-mlops` e instalas encima los requisitos del extra', f'''
''' + dos_columnas(term('Terminal · entorno del curso · desde la carpeta extra-rag-notebooks', [
        '# 1) activa el entorno del curso', 'conda activate env-ia-mlops', '# 2) instala los paquetes del extra (aparte del proyecto base)', 'pip install -r requisitos-extra-rag.txt']) +
                    '<div class="card"><h3>Paquetes clave del archivo de requisitos</h3>' + tabla(['Paquete', 'Versión fijada'], [[f'`{a}`', f'`{b}`'] for a, b in fijos]) + '</div>'
                    + fuente('README.md (apartado «Entorno recomendado») y `requisitos-extra-rag.txt`.'),
                    mira(['**Python 3.12** (recomendado) o 3.11; unos **4 GB** de disco y unos **4 GB de RAM** libres para el LLM de 0,5B.', 'El archivo ya trae `--extra-index-url` para las **ruedas CPU** de PyTorch.', 'Salida a Internet **la primera vez** (embeddings y LLM).', 'Estas son las versiones que mostró el notebook 00 en la ejecución guardada.'], 'Qué necesitas')
                    + si_falla(['Si pip no encuentra `torch==…+cpu`, falta el `--extra-index-url` (viene en el archivo) o pip no es el del kernel.', 'Sin el entorno del curso: entorno nuevo con Python 3.12 (README, «Preparar un entorno nuevo»).'])
                    + sin_verificar('que la instalación funcione en **Windows**: la ejecución guardada es de Linux.'), '1fr 1fr'),
          'El primer paso es el entorno. En el aula se activa el entorno del curso, env-ia-mlops, y se instalan encima los requisitos del extra, porque trae paquetes que el proyecto base no tiene: torch solo CPU, sentence-transformers, faiss, rank-bm25 y transformers. Las versiones del archivo son las que mostró el notebook cero en la ejecución guardada. Hacen falta unos cuatro gigas de disco y de memoria libre. Si no hay entorno del curso, el README explica cómo crear uno nuevo con Python 3.12. Todo esto se ejecutó en Linux; en Windows está sin verificar.')

    modelos = tabla_readme('## Modelos que se descargan')[1:]
    ps_proxy = re.search(r'```powershell\n(\$env:HTTP_PROXY.*?)```', fuente_celda('00', celda('00', 'proxy.miempresa.example', 'markdown')), re.S).group(1).strip().split('\n')
    pip_proxy = linea_readme('pip install --proxy $env:HTTP_PROXY -r requisitos-extra-rag.txt --extra-index-url')
    slide('B', 3, 'Proxy y modelos', 'solo si tu red lo exige', 'Detrás de un proxy defínelo antes de instalar; y se descargan cuatro modelos', f'''
''' + dos_columnas(term('PowerShell · solo si tu red sale por un proxy · sustituye el host por el tuyo', ['# en la misma sesión, ANTES de instalar o de abrir Jupyter'] + ps_proxy + ['# pip también necesita el proxy', pip_proxy], prompt='PS>')
                    + fuente('notebook 00, apartado 3 (marcador genérico `proxy.miempresa.example`) y README.md. **Sin proxy, omite estas líneas.**')
                    + sin_verificar('con un **proxy corporativo real**: en la ejecución guardada `HTTP_PROXY` estaba sin definir y el Hub respondió **200** directamente.'),
                    '<div class="card"><h3>Modelos que se descargan (la primera vez)</h3>' + tabla(['Uso', 'Identificador en el Hub', 'Tamaño'], [[m[0], m[1], m[2]] for m in modelos]) + '</div>'
                    + callout('Si ya están en `cache-hf/`, puedes **trabajar sin red** con `HF_HUB_OFFLINE=1`.') + callout('Una API de pago es **opcional** y no se usa: el pipeline es el mismo, solo cambia el paso de generación.')
                    + fuente('README.md (apartado «Modelos que se descargan»).'), '1.05fr .95fr'),
          'El proxy y los modelos. Si la red del alumno sale por un proxy corporativo, hay que definir las variables en la misma sesión antes de instalar y antes de abrir Jupyter. El host que aparece es un marcador genérico: cada uno pone el suyo. Sin proxy se omiten esas líneas. Se descargan cuatro modelos: el de embeddings, unos quinientos megas; el LLM de cero coma cinco B, alrededor de un giga; uno de reserva más pequeño, y un reranker opcional que en modo rápido se omite. En la ejecución guardada no había proxy, así que su funcionamiento con un proxy real está sin verificar.')

    val = dict(re.findall(r'(\d\d) ≈ ([\d,]+ (?:s|min))', README))
    medido = {
        '00': '—',
        '01': f'carga {c(em["segundos_carga"], 1)} s · 16 frases {c(em["segundos_codificar"])} s',
        '02': f'77 fragmentos en {c(ix["segundos_embeber"])} s',
        '03': '— (no guarda tiempos)',
        '04': f'LLM cargado en {c(gn["segundos_carga_llm"], 1)} s · {c(gn["latencia_media_con_s"], 1)} s de media por respuesta con RAG',
        '05': f'evaluación breve: {c(pl["fidelidad_breve"]["latencia_media_s"], 1)} s de media (3 preguntas)',
        '06': 'caché: la primera consulta tardó ' + re.search(r'primera \(miss=True\): ([\d.]+)s', salida('06', 'class CacheRecuperacion')).group(1).replace('.', ',') + ' s',
    }
    slide('B', 3, 'Orden y tiempos', 'cuánto tarda cada notebook', 'Siete notebooks en orden: el 04 es el lento (≈ 5,5 min en CPU, con los modelos ya descargados)', f'''
<div class="card">''' + tabla(['Notebook', 'Orientativo (README)', 'Validación de la copia (README)', 'Medido y guardado en el notebook'], [
        [f'**{f[0]}**', f[3], f'≈ {val[f[0]]}', medido[f[0]]] for f in filas_mapa]) + '''</div>
<div class="grid2" style="margin-top:10px">
 ''' + card('El modo rápido', ['`RAG_MODO_RAPIDO=1` (activo por defecto) reduce las preguntas que se generan y los tokens nuevos: **64** en lugar de 120, y **4** preguntas en el 04.', 'La recuperación y las métricas del conjunto a mano **no** se recortan; el *reranker* **se omite**.', 'La serie completa **en frío**: del orden de **15–30 min** (estimación del README).']) + term('Reejecutar todos (opcional) · Linux/macOS · desde la raíz', ['bash scripts/ejecutar_cuadernos.sh']) + '''
</div>''' + fuente('README.md (tabla y párrafo de validación); salidas y JSON guardados: ' + f'`embeddings.json`, `indexado.json`, `generacion.json`, `pipeline.json` y {ref("06", "cache = CacheRecuperacion")}.') + sin_verificar('**tiempos en un portátil del alumnado** o en Windows: los de esta tabla son de la ejecución guardada.'),
          'Orden y tiempos. Se ejecutan en orden. La columna del medio es la validación del README, en CPU con los modelos ya descargados: el cuatro es el lento, unos cinco minutos y medio, porque es el que genera texto con el modelo. Las cifras de la última columna son las que el propio notebook guardó. Tenga paciencia con la primera ejecución: descarga el modelo de embeddings y el LLM. El modo rápido está activo por defecto: menos preguntas generadas y menos tokens; para desactivarlo, la variable RAG modo rápido a cero. Los tiempos son de esta ejecución en Linux; los de un portátil del alumnado o de Windows están sin verificar.')

    cb00 = celda('00', 'CFG_RED = configurar_proxy_y_hf(RAIZ, verbose=True)')
    s_boot = salida_celda('00', cb00)
    s_ent = salida('00', 'faltan = tabla_entorno')
    s_hub = salida('00', 'conexion = probar_conexion_hf()')
    jup = linea_readme('jupyter notebook notebooks\\00-introduccion-y-setup.ipynb')
    kern = linea_readme('python -m ipykernel install --user --name rag')
    slide('B', 4, 'Notebook 00', 'comprobar antes de construir', 'Notebook 00: no construye nada, comprueba el entorno y que llegas a Hugging Face', f'''
''' + dos_columnas(term('Terminal · abrir el notebook (kernel «Python (rag)»)', [kern, jup]) + real(f'Salida guardada · {ref("00", "CFG_RED = configurar")} (últimas 4 líneas)', '\n'.join(s_boot.split('\n')[-4:]))
                    + real(f'Salida guardada · {ref("00", "faltan = tabla_entorno")} (2 líneas)', '\n'.join(s_ent.split('\n')[:2])) + real(f'Salida guardada · {ref("00", "conexion = probar_conexion_hf()")}', s_hub),
                    mira(['«**Entorno listo. Paquetes obligatorios disponibles.**»: puedes pasar al 01.', '`Dispositivo: cpu`, `Semilla: 42` y `Modo rapido: True`: es lo esperado.', 'El Hub responde **estado 200**; CUDA, proxy y token salen en `False` y **no bloquean**.', 'Los 9 documentos del corpus están en `datos/corpus/`.'])
                    + si_falla(['**Falta un paquete:** instálalo en el entorno del kernel (`pip install -r requisitos-extra-rag.txt`) y reejecuta la celda.', '**No llegas al Hub:** revisa el proxy y el certificado, o coloca los modelos en `cache-hf/` y activa `HF_HUB_OFFLINE=1`.'])
                    + fuente('notebook 00, apartados 1 a 4.'), '1fr 1fr'),
          'El notebook cero no construye nada: localiza la raíz del proyecto, comprueba que están los paquetes obligatorios y hace una petición ligera al Hub de Hugging Face. La salida guardada dice entorno listo, dispositivo CPU, semilla cuarenta y dos y modo rápido activo, y el Hub contesta con estado doscientos. Las filas de CUDA, proxy y token salen en falso, y es lo esperado en un portátil sin GPU y sin proxy. Si falta un paquete, el propio notebook dice qué instalar; si no se llega al Hub, hay que revisar proxy y certificado antes del notebook uno.')

    # ---------------------------------------------------------------- C · Indexar
    c_car = celda('01', 'codificador = Codificador(MODELO_EMB')
    s_car = salida_celda('01', c_car)
    s_enc = salida('01', 'E = codificador.codificar(frases')
    slide('C', 3, 'Notebook 01: vectores', 'cargar el modelo y codificar', 'Notebook 01: 16 frases pasan a ser 16 vectores de 384 números, normalizados', f'''
''' + dos_columnas(codigo(f'notebook 01 · celda [{ec("01", c_car)}] · cargar el modelo', quitar_comentarios(fuente_celda('01', c_car))) + codigo(f'notebook 01 · celda [{ec("01", celda("01", "E = codificador.codificar(frases"))}] · codificar (extracto)', 'E = codificador.codificar(frases, progreso=False)'),
                    real(f'Salida guardada · {ref("01", "codificador = Codificador(MODELO_EMB")}', s_car) + real(f'Salida guardada · {ref("01", "E = codificador.codificar(frases")}', s_enc) + mira(['**Dimensión 384**, dispositivo `cpu`; cargar el modelo tardó **3,5 s** (ya en caché) y codificar las 16 frases, **1,86 s**.', 'La **norma media es 1,0000**: con vectores normalizados, el coseno es el producto interno.'])
                    + si_falla(['La primera vez descarga **~500 MB**: tarda más y necesita red (o proxy).', 'Si cambias a `intfloat/multilingual-e5-small`, hay que usar los prefijos `query:` y `passage:` (MiniLM no los pide).']), '1fr 1fr')
          + fuente(f'notebook 01, apartados 3 y 4; `resultados/embeddings.json` (carga {c(em["segundos_carga"], 1)} s, codificar {c(em["segundos_codificar"])} s).'),
          'Notebook uno: del texto al vector. Se carga el modelo multilingüe de MiniLM, que ocupa unos quinientos megas la primera vez y luego queda en caché, y se codifican dieciséis frases en español de varios temas: Docker, Kubernetes, MLflow, el reglamento del curso y la empresa ficticia. El resultado es una matriz de dieciséis por trescientos ochenta y cuatro, con norma uno. Que la norma sea uno importa: así el coseno y el producto interno coinciden y el índice puede usar producto interno. Los tiempos son los guardados en el notebook; la primera vez, con descarga, será más.')

    s_cons = salida('01', 'consultas = [')
    top_filas = [l for l in s_cons.split('\n') if l.startswith('Consulta:') or l.startswith('  1. ') or l.startswith('  2. ')]
    slide('C', 3, 'Notebook 01: similitud', 'el coseno entre frases', 'La similitud coseno acierta el tema, pero no siempre la frase que contesta', f'''
''' + dos_columnas(fig('fig_similitud_coseno', 400), real(f'Salida guardada · {ref("01", "consultas = [")} · 2 primeros de cada consulta', '\n'.join(top_filas))
                    + mira(['**Vacaciones:** gana la frase correcta (**0,744**), y la 2.ª baja a **0,278**.', '**Puerto de la API:** gana «la imagen se llama…» (**0,514**), no la frase que dice el puerto 8080 (**0,469**).', '**Experimento de MLflow:** gana la del *tracking URI* (**0,580**), no la que nombra el experimento (**0,398**).'])
                    + callout('Dos de tres veces el vecino más cercano es **del tema correcto pero no la frase con el dato**: por eso se recuperan **k fragmentos**, no uno.') + fuente('notebook 01, apartados 5 y 6.'), '1fr 1fr'),
          'La similitud coseno entre frases. A la izquierda, la matriz real: la diagonal vale uno y los bloques por tema se ven algo más claros, aunque la cercanía dentro de un tema ronda cero coma tres a cero coma seis, no uno. A la derecha, tres consultas que no están en la lista. En la de vacaciones gana la frase correcta con cero coma setenta y cuatro. Pero en las otras dos gana una frase del tema correcto que no es la que contiene el dato: en el puerto gana la que nombra la imagen, y en MLflow, la del tracking URI. Esa es la razón de recuperar varios fragmentos y no solo el primero.')

    s_pca = salida('01', 'pca = PCA(')
    slide('C', 2, 'Notebook 01: PCA', 'una foto en 2-D', 'En 2-D los temas se agrupan a medias: dos componentes recogen solo el 25 % de la varianza', f'''
''' + dos_columnas(fig('fig_pca_embeddings', 420), real(f'Salida guardada · {ref("01", "pca = PCA(")}', s_pca) + mira([f'Varianza explicada: **{c(em["varianza_pca"][0] * 100, 1)} %** y **{c(em["varianza_pca"][1] * 100, 1)} %**; suma **{c(sum(em["varianza_pca"]) * 100, 1)} %**.', 'A la **izquierda** se juntan 1, 3, 5, 6 y 7 (Docker, Kubernetes, MLflow/CI); 2, 4 y 8 quedan más al centro; las de NubeAndina (12 a 16) están **dispersas**.', 'Los ejes no tienen nombre semántico: son las direcciones de mayor varianza.'])
                    + callout('Una PCA a 2-D **pierde ~75 % de la información**: sirve para *ver* cúmulos, no para medir distancias.') + fuente('notebook 01, apartado 7 y `resultados/embeddings.json` (`varianza_pca`).'), '1.05fr .95fr'),
          'La PCA a dos dimensiones. No es el espacio real, que tiene trescientas ochenta y cuatro dimensiones; perdemos información, y las dos componentes recogen solo el veinticinco por ciento de la varianza. Aun así se ve que Docker, Kubernetes y MLflow se juntan a la izquierda, mientras que las frases de NubeAndina, que hablan de cosas muy distintas, quedan más dispersas. Los ejes no tienen un nombre como eje Docker. Conviene no sacar conclusiones fuertes de esta figura; es una foto de intuición.')

    c_estr = celda('02', 'estrategias = {')
    s_estr = salida_celda('02', c_estr)
    slide('C', 3, 'Notebook 02: trocear', 'tres estrategias', 'Notebook 02: el mismo corpus, tres formas de trocear, de 67 a 87 fragmentos', f'''
''' + dos_columnas(codigo(f'notebook 02 · celda [{ec("02", celda("02", "TAMANO_CHUNK = 400"))}] · mandos', quitar_comentarios(trozo(fuente_celda('02', celda('02', 'TAMANO_CHUNK = 400')), 'TAMANO_CHUNK', 'print(')))
                    + codigo(f'notebook 02 · celda [{ec("02", c_estr)}] · tres estrategias', quitar_comentarios(trozo(fuente_celda('02', c_estr), 'estrategias = {', 'tabla_est'))),
                    real(f'Salida guardada · {ref("02", "documentos = cargar_corpus")}', corpus_txt.split('\n')[0]) + real(f'Salida guardada · notebook 02, celda [{ec("02", c_estr)}]', re.split(r'\n\s+nombre\s', s_estr)[0].strip())
                    + mira(['**fijo:** ventanas de 400 caracteres sin solape (67 fragmentos, el menor de **10** caracteres).', '**solape:** igual con 80 compartidos (**77**, ninguno por debajo de 182): la que se usa por defecto.', '**párrafos:** agrupa párrafos (**87**, media de **282**).', 'Se trocea por **caracteres**, no por tokens: más simple; en producción, por tokens.']), '1.05fr .95fr')
          + fuente(f'notebook 02, apartados 1 y 2; `resultados/indexado.json` (`resumenes_estrategias`); corpus de {n_docs} documentos, {miles(n_car)} caracteres, {miles(n_pal)} palabras.'),
          'Notebook dos: trocear. El corpus son nueve documentos cortos, unos veinticuatro mil caracteres. Se comparan tres estrategias con el mismo tamaño objetivo de cuatrocientos caracteres: fijo, sin solape; solape, con ochenta caracteres compartidos, que es la que se usa por defecto; y párrafos, que agrupa párrafos sin pasar del tamaño. Salen sesenta y siete, setenta y siete y ochenta y siete fragmentos. Un detalle: se trocea por caracteres y no por tokens, porque es más fácil de explicar; en producción es más honesto hacerlo por tokens.')

    s_hecho = salida('02', 'HECHO = "22 días laborables"')
    s_borde = salida('02', 'frags_fijo =')
    s_sol1 = salida('06', 'def n_cubren')
    l_sol1 = '\n'.join(l for l in s_sol1.split('\n') if l.startswith('tamano='))
    slide('C', 3, 'Notebook 02: el hecho partido', 'por qué el solape', 'El solape es un seguro barato: el hecho «22 días laborables» aparece entero en 2 fragmentos, no en 1', f'''
''' + dos_columnas(real(f'Salida guardada · {ref("02", "HECHO = ")}', s_hecho) + real(f'Salida guardada · {ref("02", "frags_fijo =")} (líneas seleccionadas: el corte y el solape)', lineas_con(s_borde, 'A ellos se', 'suman', '--- Con SOLAPE', 'final de A', 'inicio de B')),
                    real(f'Salida guardada · {ref("06", "def n_cubren")} · ejercicio 1 (tamaño 150)', l_sol1) + mira(['Sin solape, el corte cae justo en «**A ellos se | suman 3 días…**»: se parte la frase siguiente al hecho.', 'Con solape, el inicio de un fragmento **repite el final** del anterior y el hecho viaja en **dos**.', 'Con ventanas de 150 caracteres: **1** fragmento sin solape y **2** con solape de 60.'])
                    + callout('Un hecho corto cerca del borde de la ventana puede **partirse y desaparecer** de todos los fragmentos: el *recall* de esa pregunta cae aunque el documento correcto esté en el corpus.'), '1fr 1fr')
          + fuente('notebook 02, apartado 3; notebook 06, solución del ejercicio 1.'),
          'Qué pasa con un hecho concreto al trocear. Se busca la frase veintidós días laborables. Con ventanas fijas aparece entera en un solo fragmento; con solape, en dos; con párrafos, en uno. Más abajo se ve el corte real de las ventanas fijas: acaba en a ellos se y el siguiente empieza en suman tres días, así que se parte la frase de los tres días del cierre andino. Con solape, el inicio del segundo fragmento repite el final del primero. En el ejercicio uno, con ventanas de ciento cincuenta caracteres, se ve lo mismo: uno sin solape, dos con solape de sesenta.')

    r = {x['nombre']: x for x in ix['resumenes_estrategias']}
    slide('C', 2, 'Notebook 02: longitudes', 'el histograma', 'Párrafos da más fragmentos y más cortos; el solape evita los trozos minúsculos', f'''
''' + dos_columnas(fig('fig_chunking_longitudes', 330), '<div class="card">' + tabla(['Estrategia', 'Fragmentos', 'Media', 'Mínima', 'Máxima'], [
        [f'**{n}**', str(r[n]['n_fragmentos']), c(r[n]['longitud_media'], 0), str(r[n]['longitud_min']), str(r[n]['longitud_max'])] for n in ('fijo', 'solape', 'parrafos')]) + '</div>'
                    + mira(['**fijo** deja trozos de **10** caracteres: restos del final de un documento.', '**solape** no baja de **182** y casi todos están en 380-400.', '**párrafos** reparte casi todo entre ~100 y 400 (mínimo **32**): respeta la estructura, pero con **más** variación.'])
                    + fuente('`resultados/indexado.json` (`resumenes_estrategias`) y notebook 02, apartado 4.'), '1.1fr .9fr'),
          'El histograma de longitudes. La estrategia fija y la de solape se concentran en torno a cuatrocientos caracteres; la fija deja algún resto minúsculo, de diez caracteres, al final de un documento. La de párrafos produce más fragmentos y de longitud muy variable, porque respeta los párrafos. No hay una estrategia mejor en abstracto: se elige midiendo la recuperación, como se hace en el cuaderno cinco con el tamaño del trozo.')

    c_ind = celda('02', 'fragmentos = fragmentos_por[ESTRATEGIA_DEFECTO]')
    c_q = celda('02', 'consulta = "¿Cuántos días')
    s_ind = salida_celda('02', c_ind)
    s_q = salida_celda('02', c_q)
    slide('C', 3, 'Notebook 02: el índice', 'NumPy y FAISS', 'Notebook 02: se indexan 77 fragmentos y NumPy y FAISS devuelven lo mismo', f'''
''' + dos_columnas(codigo(f'notebook 02 · celda [{ec("02", c_ind)}] · embeber e indexar', quitar_comentarios('\n'.join(l for l in fuente_celda('02', c_ind).split('\n') if l.strip() and not l.startswith('print('))))
                    + codigo(f'notebook 02 · celda [{ec("02", c_q)}] · buscar (extracto)', 'top_np = indice_np.buscar(qv, k=4)\ntop_fa = indice_faiss.buscar(qv, k=4)'),
                    real(f'Salida guardada · notebook 02, celda [{ec("02", c_ind)}]', s_ind) + real(f'Salida guardada · notebook 02, celda [{ec("02", c_q)}] (última línea)', s_q.split('\n')[-1])
                    + mira([f'**{ix["n_fragmentos"]} fragmentos × {ix["dim"]}** dimensiones, embebidos en **{c(ix["segundos_embeber"])} s**.', 'Los dos índices dan los **mismos 4 identificadores en el mismo orden** (`coinciden: true`): ambos hacen búsqueda exacta por producto interno.', 'Quedan guardados en `modelos/indice_faiss` y `modelos/indice_numpy`.'])
                    + si_falla(['Si cambias el troceado, **regenera el índice**: los notebooks 03-05 leen el de `modelos/`.']), '1fr 1fr')
          + fuente(f'notebook 02, apartado 5; `resultados/indexado.json` (`coinciden`, `ids_numpy`, `ids_faiss`: **{ix["ids_faiss"][0]}** primero).'),
          'Embeber e indexar. Se codifican los setenta y siete fragmentos de la estrategia con solape y se construyen dos índices: uno de NumPy, que es una matriz de vectores y un producto interno, y otro de FAISS en modo exacto. Con un corpus tan pequeño no hay ganancia de tiempo; FAISS importa con cientos de miles de vectores o con índices aproximados. Lo que se comprueba es que los dos devuelven los mismos identificadores en el mismo orden. Los índices se guardan en la carpeta modelos para que los notebooks siguientes no tengan que volver a embeber el corpus.')

    # ---------------------------------------------------------------- D · Recuperar
    c_busq = celda('03', 'def buscar_denso')
    s_busq = salida_celda('03', celda('03', 'mostrar("¿Cuántos días de vacaciones'))
    q1 = s_busq.split('=' * 70)[1]
    q1_lineas = [l for l in q1.split('\n') if l.strip()]
    bm = [l for l in q1_lineas if l.startswith('    ')]
    slide('D', 4, 'Notebook 03: tres búsquedas', 'BM25, denso e híbrido', 'Para «vacaciones», BM25 trae el fragmento de los «22 días» 2.º; el denso ni lo trae en el top-4', f'''
''' + dos_columnas(codigo(f'notebook 03 · celda [{ec("03", c_busq)}] · las tres búsquedas', quitar_comentarios(trozo(fuente_celda('03', c_busq), 'def buscar_denso', 'def mostrar')))
                    + card('Cómo se combinan', ['**BM25** puntúa por palabras compartidas; el **denso**, por cercanía de significado.', '**RRF** suma `1/(k + rango)` de cada lista (aquí `k_rrf = 60`): no promedia puntuaciones.']),
                    real(f'Salida guardada · {ref("03", "mostrar(")} · pregunta de vacaciones · sin el extracto de texto · el fragmento con los 22 días es el #1', '\n'.join(re.sub(r'(::#\d+)\s+.*$', r'\1', l) for l in q1_lineas if re.match(r'\s+(BM25|denso|hibrido):|^\s+\d\.\s', l)))
                    + mira(['**BM25:** el fragmento `#1` («22 días laborables») es el **2.º**.', '**Denso:** trae `#0`, `#7`, `#6`, `#2`; **`#1` no entra** en el top-4.', '**Híbrido:** lo recupera, pero **4.º**.'])
                    + callout('El *recall* de este notebook se mide por **documento**: acertar el documento **no garantiza** que el fragmento con el dato viaje al LLM.'), '1fr 1fr')
          + fuente('notebook 03, apartados 1 y 2 (la salida completa, con los extractos de texto, está guardada en esa celda).'),
          'Las tres búsquedas sobre el mismo índice. A la izquierda el código: buscar con BM25, con vectores y con la fusión de las dos listas por rango recíproco, RRF. A la derecha, la pregunta de las vacaciones: los identificadores que devuelve cada método. BM25 pone en segundo lugar el fragmento número uno, que es el que contiene los veintidós días laborables. La búsqueda densa trae otros cuatro fragmentos del mismo documento y no incluye ese. El híbrido lo recupera en cuarto lugar. Lo importante: el recall del notebook se mide por documento, así que esa diferencia no se ve en las métricas.')

    slide('D', 3, 'Notebook 03: métricas', 'recall@5 y MRR', 'Con k = 5 los tres métodos aciertan el documento; solo el MRR los distingue: 0,96 · 0,91 · 0,96', f'''
''' + dos_columnas('<div class="card">' + tabla(['Método', f'recall@{rc["k"]}', 'MRR', 'Preguntas'], [
        ['**BM25**', c(rc['bm25']['recall'], 3), c(rc['bm25']['mrr'], 3), str(rc['n_preguntas'])], ['**denso**', c(rc['denso']['recall'], 3), c(rc['denso']['mrr'], 3), str(rc['n_preguntas'])],
        ['**híbrido (RRF)**', c(rc['hibrido']['recall'], 3), c(rc['hibrido']['mrr'], 3), str(rc['n_preguntas'])]]) + '</div>'
                    + mira(['*Recall@k*: vale 1 si **al menos un** documento de referencia está en los k primeros.', '**MRR**: media de 1/r, con r el rango del primer documento relevante: premia lo que queda **arriba**.', 'Son **18** preguntas de tipo «hecho»; las 2 «no está» no tienen documento de referencia.'])
                    + card('Qué no se midió', ['El *reranker*: en modo rápido se omite (`rerank: null` en el JSON).']) + fuente('`resultados/recuperacion.json` y notebook 03, apartado 3.'),
                    fig('fig_mrr', 330), '1fr 1fr'),
          'Las métricas de recuperación sobre las dieciocho preguntas hechas a mano. Con k igual a cinco los tres métodos tienen recall uno: siempre cae algún fragmento del documento correcto entre los cinco primeros. La diferencia aparece en el MRR: BM25 y el híbrido, cero coma noventa y seis; el denso, cero coma noventa y uno. Es una diferencia de una pregunta en el segundo puesto, no un benchmark. El conjunto es pequeño y hecho a mano; las cifras son una brújula para este laboratorio. El reranker no se midió porque el modo rápido lo omite.')

    kk = {(f['k'], f['metodo']): f for f in rc['recall_por_k']}
    slide('D', 3, 'Notebook 03: recall@k', 'qué pasa al cambiar k', 'Con k = 1 el denso falla 2 preguntas más que BM25 (0,833 frente a 0,944); desde k = 3, todos llegan a 1,0', f'''
''' + dos_columnas(fig('fig_recall_at_k', 340), '<div class="card">' + tabla(['k', 'BM25', 'denso', 'híbrido'], [
        [f'**{k}**'] + [c(kk[(k, m)]['recall'], 3) for m in ('BM25', 'denso', 'hibrido')] for k in (1, 3, 5, 8)]) + '</div>'
                    + mira(['0,944 son **17 de 18** preguntas; 0,833, **15 de 18** (derivado de la tabla).', 'BM25 y el híbrido valen **lo mismo** en todos los k: por eso en la figura se ve una sola línea.', 'Con 18 preguntas, **una** pregunta mueve el recall 0,056: no saques conclusiones finas.'])
                    + fuente('`resultados/recuperacion.json` (`recall_por_k`) y ' + f'{ref("03", "ks = [1, 3, 5, 8]")}.'), '1.1fr .9fr'),
          'Qué pasa al cambiar k. Con k igual a uno, BM25 y el híbrido aciertan diecisiete de las dieciocho preguntas y el denso, quince; son dos preguntas de diferencia. Desde k igual a tres, los tres métodos llegan a uno. En la figura solo se ve una línea para BM25 y el híbrido porque coinciden en todos los puntos y una tapa a la otra. La lección: con k pequeño el método importa; con k suficiente casi cualquier método cumple en este corpus tan pequeño, y eso no quiere decir que pase lo mismo con miles de documentos.')

    # ---------------------------------------------------------------- E · Generar y evaluar
    c_pr = celda('04', 'pregunta_ejemplo = demo[0]')
    s_pr = salida_celda('04', c_pr)
    l_pr = s_pr.split('\n')
    slide('E', 3, 'Notebook 04: el prompt', 'las reglas del sistema', 'Notebook 04: el prompt es parte del sistema: «responde SOLO con el contexto» y cita', f'''
''' + dos_columnas(codigo(f'notebook 04 · celda [{ec("04", c_pr)}] · prompt con y sin contexto (extracto)', quitar_comentarios(trozo(fuente_celda('04', c_pr), 'pregunta_ejemplo =', 'print('))) + mira(['Con RAG, el **sistema** prohíbe inventar y exige abstenerse con una **frase exacta**.', 'El **usuario** recibe el contexto (fragmentos con su id) y la pregunta.', 'Sin RAG solo va la pregunta: es el **control** de la comparación.']),
                    real(f'Salida guardada · notebook 04, celda [{ec("04", c_pr)}] (líneas seleccionadas)','\n'.join(l_pr[:2]) + '\n' + '\n'.join(l_pr[l_pr.index('===== USUARIO (sin RAG) =====') :])), '1.05fr .95fr')
          + fuente('notebook 04, apartado 2 (el contexto con los fragmentos está en la salida guardada completa).'),
          'El prompt. Con RAG, el mensaje de sistema le prohíbe inventar cifras, nombres, fechas y políticas, le pide citar el identificador del fragmento entre corchetes y le obliga a decir exactamente una frase si la respuesta no está en el contexto. El usuario recibe el contexto, con cada fragmento marcado con su id, y la pregunta. Sin RAG solo va la pregunta: es el control. Insista en que el prompt es parte del sistema: no es un adorno y se versiona y se prueba como el resto.')

    slide('E', 4, 'Notebook 04: con y sin RAG', 'cuatro preguntas', 'La misma pregunta, con y sin RAG: sin contexto inventa; con contexto cita… aunque a veces incompleto', f'''
<div class="card">''' + tabla(['Pregunta', 'Sin RAG', 'Con RAG', 'Cobertura'], [
        [f'**{i}** · {pq[i]["pregunta"]}', det[i]['respuesta_sin_rag'], det[i]['respuesta_con_rag'], f'{c(det[i]["cobertura_sin"])} → {c(det[i]["cobertura_con"])}'] for i in ('q11', 'q13', 'q03', 'q19')]) + '''</div>
<div class="grid2" style="margin-top:8px">
 ''' + callout('**Con RAG sigue incompleto:** q11 da los 22 días pero no los 3 días ni julio; q13, la contraseña (14) pero no a Elena Quispe; q03, la imagen pero no el puerto. Falla el **modelo pequeño**: las fuentes eran las correctas.')
          + callout('**q19** (una cafetería que no existe): sin RAG inventa **0123456789**; con RAG se abstiene, y su cobertura **1,00** significa **abstención**.') + '''
</div>''' + fuente(f'`resultados/generacion.json` (`detalle`) y {ref("04", "pipeline = PipelineRAG(")}; los hechos esperados salen de `datos/preguntas.json`.'),
          'La comparación con y sin RAG, con las respuestas reales guardadas. Sin contexto, el modelo inventa en las cuatro. Con contexto mejora, pero no es perfecto: en la primera da los veintidós días pero se deja los tres días del cierre andino y julio; en la segunda da la longitud de la contraseña pero no el nombre de la delegada; en la tercera da el nombre de la imagen y no el puerto. Las fuentes recuperadas eran las correctas, así que el fallo es del modelo pequeño al redactar. En la cuarta, que no está en el corpus, el éxito es abstenerse, y con RAG lo hace. Un modelo mayor con el mismo patrón de recuperación debería ir mejor, pero eso está sin medir.')

    slide('E', 3, 'Notebook 04: cobertura', 'la figura y las medias', 'Cobertura media de hechos: 0,00 sin RAG y 0,58 con RAG (4 preguntas, un LLM de 0,5B)', f'''
''' + dos_columnas(fig('fig_con_sin_rag', 330), '<div class="grid2">' + kpi(f'{c(gn["cobertura_media_sin"])} → {c(gn["cobertura_media_con"])}', 'cobertura media de hechos **sin RAG → con RAG** (4 preguntas)') + kpi(f'{c(gn["latencia_media_sin_s"], 1)} s · {c(gn["latencia_media_con_s"], 1)} s', 'latencia media por respuesta **sin RAG · con RAG** en CPU') + '</div>'
                    + mira(['Cobertura = fracción de **hechos esperados** que aparecen como texto en la respuesta (`contiene_hechos`): **no es un juez semántico**.', 'En q19 (no está en el corpus) mide si **se abstiene**.', 'Solo **4 preguntas** (modo rápido): una anécdota, no un benchmark.'])
                    + fuente(f'`resultados/generacion.json` ({gn["modelo_llm"]}, k = {gn["k"]}, {gn["max_nuevos"]} tokens nuevos) y {ref("04", "fig_con_sin_rag.png")}.'), '1fr 1fr'),
          'La figura y las medias. Las barras rojas, sin RAG, valen cero en las cuatro preguntas y por eso no se ven. Las verdes, con RAG, valen cero coma treinta y tres, cero coma cinco, cero coma cinco y uno; este último es la abstención de la pregunta que no está en el corpus. La media pasa de cero a cero coma cincuenta y ocho. Es una comprobación de cadenas, no un juez semántico, con cuatro preguntas y un modelo de cero coma cinco B. Sirve para ver la dirección, no para publicar una cifra. La latencia media por respuesta, en CPU, es de varios segundos; se discute en la diapositiva de latencia.')

    c_p5 = celda('05', 'pipeline = PipelineRAG(')
    c_o5 = celda('05', 'out = pipeline.preguntar(q_demo')
    s_p5 = salida_celda('05', c_p5)
    s_o5 = salida_celda('05', c_o5)
    slide('E', 4, 'Notebook 05: el pipeline', 'una función', 'Notebook 05: `PipelineRAG.preguntar()` es una función: pregunta → respuesta, fuentes y latencias', f'''
''' + dos_columnas(codigo(f'notebook 05 · celda [{ec("05", c_p5)}] · el pipeline (extracto)', quitar_comentarios(trozo(fuente_celda('05', c_p5), 'pipeline = PipelineRAG(', '# Recuperación suelta')) + '\n\nhits = pipeline.recuperar(q_demo, k=K)')
                    + codigo(f'notebook 05 · celda [{ec("05", c_o5)}]', quitar_comentarios(fuente_celda('05', c_o5).split('\nelse:')[0]).replace('if generador is not None:\n    ', '').replace('\n    ', '\n')),
                    real(f'Salida guardada · notebook 05, celda [{ec("05", c_p5)}]', lineas_con(s_p5, 'Pregunta:', '  ')) + real(f'Salida guardada · notebook 05, celda [{ec("05", c_o5)}]', s_o5)
                    + mira(['Los 4 fragmentos son de `nubeandina-datos-y-seguridad` y `curso-reglamento`; los números **0,033 y 0,016** son puntuaciones **RRF**, no cosenos.', 'Esta vez el LLM acierta **los dos hechos**: «Elena Quispe» y «14 caracteres».', 'Recuperar tardó **0,0089 s**; generar, **1,52 s**.']), '1.05fr .95fr')
          + fuente('notebook 05, apartado 1.'),
          'El pipeline como objeto. Una clase junta el codificador, el índice denso, el índice BM25 y el generador, con k igual a cuatro y el método híbrido. Su método preguntar hace la recuperación y la generación y devuelve la respuesta, las fuentes y las latencias por etapa; es la unidad que más adelante se envolvería en una ruta HTTP, por ejemplo la API del curso. La salida guardada: los cuatro fragmentos recuperados, con puntuaciones de fusión, que no son cosenos, y una respuesta que esta vez acierta los dos hechos, Elena Quispe y catorce caracteres. Recuperar tarda milisegundos; generar, algo más de un segundo.')

    cc = {f['tamano_chunk']: f for f in pl['estudio_chunk']}
    ck = {f['k']: f for f in pl['estudio_k']}
    slide('E', 3, 'Notebook 05: mandos', 'tamaño de chunk y k', 'Con chunk de 200 el MRR sube a 0,944; con k = 1 el recall cae a 0,833: los mandos se miden', f'''
''' + dos_columnas(fig('fig_mandos_chunk_k', 280) + '<div class="card">' + tabla(['Chunk', 'Fragmentos', 'recall@5', 'MRR'], [[f'**{t}**', str(cc[t]['n_fragmentos']), c(cc[t]['recall@5'], 3), c(cc[t]['mrr'], 3)] for t in (200, 400, 800)]) + '</div>',
                    '<div class="card">' + tabla(['k', 'recall', 'MRR'], [[f'**{k}**', c(ck[k]['recall'], 3), c(ck[k]['mrr'], 3)] for k in (1, 2, 3, 5, 8)]) + '</div>'
                    + mira(['Solo se mide la **recuperación** (denso, 18 preguntas): así no se paga la generación en cada punto.', 'Más chunks pequeños (**203** con 200 caracteres) no cambian el recall, pero **suben el MRR**.', 'Un *k* alto mete más contexto: más probabilidad de que el hecho viaje, pero también más **ruido** y **latencia**.'])
                    + fuente('`resultados/pipeline.json` (`estudio_chunk`, `estudio_k`) y ' + f'{ref("05", "def construir_indice")}.'), '1.2fr .8fr'),
          'Los dos mandos del RAG: el tamaño del trozo y k. A la izquierda, tres tamaños, doscientos, cuatrocientos y ochocientos caracteres, con ciento tres, setenta y siete y treinta y siete fragmentos. El recall a cinco es uno en los tres y el MRR sube a cero coma novecientos cuarenta y cuatro con trozos de doscientos. A la derecha, k de uno a ocho con el índice por defecto: con k igual a uno el recall es cero coma ochocientos treinta y tres y desde tres es uno. Aquí solo se mide recuperación. Con dieciocho preguntas, una pregunta mueve las cifras: son pistas para decidir qué probar, no un óptimo.')

    p05 = pl['fidelidad_breve']
    lat_o5 = re.search(r"'recuperacion': ([\d.]+), 'generacion': ([\d.]+), 'total': ([\d.]+)", s_o5).groups()
    slide('E', 3, 'Notebook 05: latencia', 'por etapa, en CPU', 'Recuperar tarda milisegundos y generar, segundos: la latencia está en el LLM', f'''
''' + dos_columnas(fig('fig_latencia_etapas', 300), '<div class="grid2">' + kpi(f'{lat_o5[0].replace(".", ",")} s', f'recuperación de una pregunta (notebook 05)') + kpi(f'{lat_o5[1].replace(".", ",")} s', 'generación de esa misma pregunta (notebook 05)') + '</div>'
                    + mira([f'Evaluación breve (q11, q13 y q19): **{c(p05["latencia_media_s"], 1)} s** de media total; cobertura media **{c(p05["cobertura_media"])}** y **{p05["n_ok"]} de {p05["n"]}** completas.', f'En el notebook 04 las mismas preguntas dieron **{c(gn["latencia_media_con_s"], 1)} s** de media con RAG (cuatro preguntas; de **{c(min(d_["latencia_con_s"] for d_ in gn["detalle"]), 1)} s** a **{c(max(d_["latencia_con_s"] for d_ in gn["detalle"]), 1)} s** según la pregunta).'])
                    + callout('**Las dos medidas no cuadran** y no se ha investigado por qué: las coberturas coinciden (media 0,61 = (0,33 + 0,50 + 1,00) / 3) y las latencias son de órdenes distintos. Mide **por etapa** en tu máquina antes de fiarte.') + fuente('`resultados/pipeline.json` (`fidelidad_breve`), `resultados/generacion.json` y ' + f'{ref("05", "ruta_gen =")}.'), '1fr 1fr'),
          'La latencia por etapa. En el notebook cinco, recuperar una pregunta tarda unos nueve milisegundos y generar la respuesta algo más de un segundo y medio. En la evaluación breve de tres preguntas, la media total es de un segundo y medio aproximadamente. Pero en el notebook cuatro las latencias fueron de varias decenas de segundos por respuesta, hasta noventa y cuatro en una. Las respuestas son del mismo estilo, así que la diferencia no se explica por el modelo, y no se ha investigado la causa: puede ser el calentamiento o la carga de la máquina, pero eso es una hipótesis. Lo que sí se puede decir es que la recuperación es barata y la generación en CPU es lo caro, y que cada uno debe medir en su equipo.')

    # ---------------------------------------------------------------- F · Límites y cierre
    titulos_ej = re.findall(r'^## Ejercicio (\d) — (.*)$', '\n'.join(fuente_celda('06', i) for i, cc_ in enumerate(_nb('06')) if cc_['cell_type'] == 'markdown'), re.M)
    s2 = salida('06', 'ruta_extra = RUTAS')
    s3 = salida('06', 'tiene_22 = ')
    s4 = salida('06', 'def ver(pregunta)')
    s6 = salida('06', 'class CacheRecuperacion')
    top1 = lambda ls: ls.split(': ', 1)[1].split(', ')[0]
    bloques4 = s4.split('=' * 60)
    def l4(q, m):
        return top1(next(l.strip() for l in bloques4[q].split('\n') if l.strip().startswith(m + ':')))
    sol = {
        '1': l_sol1.replace('\n', ' · '),
        '2': 'rango ' + next(l.strip() for l in s2.split('\n') if l.strip().startswith('1. ')) + ' · ' + next(l for l in s2.split('\n') if l.startswith('¿Aparece')),
        '3': 'rango ' + next(l for l in s3.split('\n') if l.startswith('1. ')),
        '4': f'«¿Qué es gke-prod-andina-01?» → BM25: {l4(1, "BM25")}; denso: {l4(1, "denso")}',
        '5': 'sin código: se razona sobre la tasa de abstención y la cobertura (cuaderno 04)',
        '6': next(l for l in s6.split('\n') if l.startswith('primera')),
    }
    slide('F', 5, 'Ejercicios', 'notebook 06', 'Seis ejercicios para hacer tú: pruébalos antes de bajar a las soluciones', '<div class="card">' + tabla(['#', 'Ejercicio', 'Qué salió en la solución guardada'], [
        [f'**{n}**', t, sol[n]] for n, t in titulos_ej]) + '</div>' + callout('**Nota de lectura:** en el ejercicio 3 el texto de la solución habla de un caso hipotético; en la salida real **el top-1 (`#1`) ya trae los dos hechos** (22 días y cierre andino). Y en el 4 la solución escrita (BM25 gana con identificadores, el denso con paráfrasis) va **más allá** de este único ejemplo.', 'margin-top:10px')
          + fuente('notebook 06 (enunciados y soluciones con salida guardada).'),
          'Los seis ejercicios del notebook seis, con las salidas de las soluciones. Primero se intentan y después se baja a las soluciones. Uno: un hecho frágil con ventanas de ciento cincuenta caracteres. Dos: añadir un documento nuevo y reindexar, y comprobar que sale en el top tres. Tres: k igual a uno frente a cinco. Cuatro: BM25 frente a denso con un identificador literal. Cinco: un prompt más estricto, que se razona sin ejecutar. Seis: una caché de consultas, con su clave. Dos avisos de lectura honestos: en el tres, la salida real muestra que el primer fragmento ya trae los dos hechos, y en el cuatro la conclusión escrita va más allá de un solo ejemplo. Conviene decirlo en clase.')

    slide('F', 4, 'Cómo falla un RAG', 'y qué falta en producción', 'Cómo falla un RAG: seis fallos, y el notebook donde se ve cada uno', '<div class="card">' + tabla(['Fallo', 'Dónde se ve en los notebooks', 'Qué lo frena'], [
        ['**Recuperación mala**', 'Notebook 03: con k = 1 el denso acierta 15 de 18; el fragmento de los «22 días» no entra en su top-4.', 'Híbrido, k ≥ 3, medir recall@k con un conjunto de preguntas.'],
        ['**Troceado que corta hechos**', 'Notebook 02: el corte cae en «A ellos se | suman 3 días».', 'Solape; trocear por tokens en producción.'],
        ['**El modelo ignora el contexto**', 'Notebook 04: con las fuentes correctas, cobertura 0,33 y 0,50.', 'Modelo más capaz con el mismo patrón; medir la fidelidad.'],
        ['**Falso «no lo encuentro»**', 'Notebook 06, ej. 5: un prompt muy estricto puede abstenerse aunque el dato esté.', 'Medir abstención y cobertura **a la vez**.'],
        ['**Datos obsoletos**', 'Notebook 05: «si el reglamento cambia el viernes, el índice del jueves está mal».', 'Versionar corpus e índice; reindexar; caché con la versión.'],
        ['**Inyección de instrucciones**', 'Notebook 05 (guardarraíles): obedecer órdenes escondidas **dentro de un documento**.', 'No obedecerlas, filtrar PII, registrar la fuente de cada afirmación.']]) + '</div>'
          + '<p class="small" style="margin-top:6px">' + md('Los dos últimos fallos **solo se mencionan** en las notas del notebook 05: ningún notebook los provoca ni los mide.') + '</p>'
          + sin_verificar('**inyección de instrucciones** y **datos obsoletos**: descritos, **no probados** con este corpus.') + fuente('notebooks 02 a 06 (en cada fila) y `resultados/`.'),
          'Cómo falla un RAG. Seis fallos y, en cada fila, el notebook donde se ve. La recuperación mala: con k igual a uno el denso acierta quince de dieciocho y el fragmento con los veintidós días no entra en su top cuatro. El troceado que corta hechos. El modelo que ignora el contexto aunque las fuentes sean las correctas. El falso no lo encuentro de un prompt demasiado estricto. Y dos que el notebook cinco solo menciona: los datos obsoletos, que exigen versionar y reindexar, y la inyección de instrucciones escondidas en un documento. Esos dos no se prueban en esta serie; no se han verificado con este corpus.')

    slide('F', 3, 'Relación con S5 y el curso', 'teoría, práctica y MLOps', 'Esta práctica ejecuta lo que la clase de fundamentos de S5 explica, con el corpus del propio curso', '''
<div class="grid3">
 ''' + card('Clase de fundamentos de S5 (teoría)', ['Diapositivas **«De texto a vector»**, **«Similitud del coseno»**, **«Bases vectoriales y troceado»** y **«RAG: dos tuberías»**: el qué y el porqué.', '**«Cómo falla un RAG y cómo se evalúa»**: el marco que aquí se **mide** con recall@k, MRR y cobertura.']) + card('Este extra (práctica)', ['Los mismos conceptos, **ejecutados** en CPU sobre un corpus pequeño que cabe en la cabeza.', 'El corpus mezcla guías del curso (Docker, Kubernetes, MLflow, GitHub Actions, Avance 3) con la empresa **ficticia** NubeAndina.']) + card('El resto del curso (MLOps)', ['El notebook 05 lo dice: RAG **convive** con el registro de modelos (alias `champion`), el contenedor, la CI y un despliegue reversible.', 'El recuperador y el generador **también son modelos**: se promocionan, se miden y se retiran como el resto.']) + '''
</div>
<div style="margin-top:12px">''' + callout('**Lo que no cambia con una API de pago:** recuperas aquí (CPU, FAISS, tu corpus) y solo cambias el paso de generación. El contexto y las citas **siguen siendo tuyos**; y los datos privados **no** deben salir a un proveedor no acordado.') + '</div>'
          + fuente('notebooks 04 (apartado 5) y 05 (apartado 4); títulos de las diapositivas de `clase-fundamentos-ia-agentes/index.html`. No se copia su contenido.'),
          'Relación con el resto de la sesión y del curso. La clase de fundamentos de la sesión cinco tiene las diapositivas de teoría: texto a vector, similitud del coseno, bases vectoriales y troceado, las dos tuberías del RAG y cómo falla y se evalúa. Aquí no se repite esa teoría: se ejecuta. El corpus mezcla guías del propio curso con una empresa ficticia, para poder comprobar si una respuesta está fundada. Y el notebook cinco recuerda que RAG no vive solo: convive con el registro de modelos, el contenedor y la integración continua, y el recuperador y el generador también son modelos que se miden y se retiran.')

    slide('F', 3, 'Qué no está verificado', 'qué se comprobó y qué no', 'Qué se comprobó de verdad y qué quedó sin verificar', f'''
<div class="grid2">
 <div class="card"><h3 class="okc">Comprobado (salidas guardadas)</h3>''' + lista([
        'Los **7 notebooks** se ejecutaron **en Linux, solo CPU, Python 3.12.8**, en modo rápido; la presentación lee esas salidas.',
        f'Índices FAISS y NumPy: **mismos 4 identificadores** (`coinciden: true`). Recuperación sobre **{rc["n_preguntas"]} preguntas**.',
        f'Generación con y sin RAG: **{len(det)} preguntas**, cobertura media **{c(gn["cobertura_media_sin"])} → {c(gn["cobertura_media_con"])}**.']) + '''</div>
 <div class="card"><h3 class="malc">Sin verificar o con límites</h3>''' + lista([
        '**Windows** (instalación con conda o venv, PowerShell), **Codespace** y **el alumnado**: tiempos, dificultades y dudas, sin dato.',
        '**Proxy corporativo real**, GPU, el **reranker** (se omitió) y el **modo completo** (`RAG_MODO_RAPIDO=0`).',
        '**Un LLM mayor o por API**: solo se probó un modelo de **0,5B**; qué ganaría, sin dato.',
        f'Corpus de **{n_docs} documentos**, {n_hecho} preguntas con hecho y 2 de abstención: una **brújula**. Cobertura = **cadenas**, no un juez; el recall es por **documento**.',
        'Las **latencias** de los notebooks 04 y 05 no cuadran y **no se ha investigado**.']) + '''</div>
</div>''' + fuente('salidas guardadas de los notebooks 00, 04 y 05; `resultados/*.json`; README.md.'),
          'Diapositiva de honestidad. Lo comprobado: los siete notebooks se ejecutaron en Linux, solo CPU, con Python tres doce, en modo rápido; los índices de FAISS y de NumPy devuelven lo mismo; la recuperación se midió sobre dieciocho preguntas y la generación sobre cuatro. Lo no comprobado: Windows, Codespace, el alumnado, un proxy corporativo real, la GPU, el reranker, el modo completo y cualquier modelo mayor o por API. Los límites: un corpus de nueve documentos, cobertura medida por cadenas y no por un juez, recall por documento, y latencias de dos notebooks que no cuadran y no se han investigado.')

    slide('F', 2, 'Resumen', 'el mensaje', 'Un RAG se mide dos veces: ¿llegó el contexto? ¿lo usó el modelo?', f'''
<div class="msg">RAG = <b>recuperar bien</b> (recall@k, MRR) y <b>redactar fiel</b> (cobertura de hechos, abstención): se evalúan <b>por separado</b>, con tus datos y en tu máquina.</div>
<div class="grid4" style="margin-top:18px">
 ''' + kpi('recall@5 = 1,0', f'los tres métodos aciertan el documento (**{rc["n_preguntas"]}** preguntas); el MRR los separa: **0,96 · 0,91 · 0,96** (`recuperacion.json`)') + kpi('0,00 → 0,58', 'cobertura media de hechos **sin → con RAG** con un LLM de 0,5B (4 preguntas; `generacion.json`)') + kpi('k = 1: 0,833', 'recall del denso con un solo fragmento; desde **k = 3**, 1,0 (`pipeline.json`)') + kpi(f'{c(float(lat_o5[0]), 3)} s · {c(float(lat_o5[1]), 1)} s', f'recuperar frente a generar una respuesta en CPU ({ref("05", "out = pipeline.preguntar(q_demo")})') + '''
</div>
<div style="text-align:center;margin-top:44px;font-size:44px;font-weight:700;color:var(--acento)">¿Preguntas?</div>''',
          'Cierre con un único mensaje: un RAG se mide dos veces, y por separado. Primero, si el contexto llegó, con recall y MRR; después, si el modelo lo usó, con la cobertura de hechos y la abstención. Las cuatro cifras: recall uno a cinco en los tres métodos, con MRR de cero coma noventa y seis, cero coma noventa y uno y cero coma noventa y seis; cobertura de cero a cero coma cincuenta y ocho con RAG, con cuatro preguntas; recall cero coma ochocientos treinta y tres con un solo fragmento; y recuperar en milisegundos frente a generar en segundos. Recuerde que todo es de una ejecución en Linux y que lo demás está sin verificar.')

    TOTAL = sum(int(m) for m in re.findall(r'data-min="(\d+)"', ''.join(SLIDES)))
    assert TOTAL == sum(int(m) for m in re.findall(r'data-min="(\d+)"', ''.join(SLIDES)))
    return TOTAL


# =====================================================================================================================================
# Marco: CSS (fondo blanco, sin movimiento al pasar el ratón) y JavaScript del visor, copiados del laboratorio de agentes de S5
# =====================================================================================================================================
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
  f.innerHTML=`<span>ML e IA · S5 · Extra: RAG en notebooks</span><span><b>${esc(PARTES[s.dataset.part]||'')}</b> · ${i+1} / ${N}</span>`;s.appendChild(f)});
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
.cap .origen{color:var(--suave);font-style:italic}
.cap img{max-width:100%}
.zoom{display:flex;flex-direction:column;align-items:flex-start}
.zoom .lupa{position:static;margin:3px 0 0 auto}
"""
CSS = CSS + EXTRA_CSS


def html_completo():
    construir()
    js = JS.replace('__PARTES__', json.dumps(PARTES, ensure_ascii=False))
    partes = ''.join(f'<button class="part" data-p="{k}">{esc(v)}</button>' for k, v in PARTES.items())
    return ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>Extra de S5: RAG en notebooks · ML e IA: de desarrollo a producción</title>\n'
            f'<!-- Generado por generar.py: no se edita a mano. -->\n<style>{CSS}</style>\n</head>\n<body>\n'
            '<div id="prog"></div>\n<div id="viewport"><div id="stage">\n\n' + '\n\n'.join(SLIDES) + '\n\n</div></div>\n\n'
            '<aside id="notes" aria-label="Notas del ponente"><h3>Notas del ponente</h3><div id="notetext"></div><p class="small" id="notemin"></p></aside>\n'
            '<div id="index" aria-label="Índice"><h2>Índice</h2><div class="grid" id="idxgrid"></div></div>\n'
            '<div id="zoombox" aria-label="Captura ampliada"><p>Esc o clic para cerrar</p><img id="zoomimg" alt=""></div>\n'
            '<nav id="bar" aria-label="Controles">\n'
            '  <button id="bprev" aria-label="Anterior">←</button><button id="bnext" aria-label="Siguiente">→</button>\n'
            f'  <span id="count">1 / 1</span><span id="clockref" title="Minuto planificado acumulado (propuesta)"></span>\n  {partes}\n'
            '  <span class="sp"></span>\n'
            '  <a id="bhome" href="../index.html" title="Volver al índice de la sesión S5">⌂ Índice</a><button id="bidx">Índice (O)</button><button id="bnotes">Notas (S)</button><button id="bfull">Pantalla completa (F)</button>\n'
            '</nav>\n'
            '<noscript>Esta presentación necesita JavaScript. El mismo contenido está en los siete notebooks de esta carpeta.</noscript>\n\n'
            f'<script>{js}</script>\n</body>\n</html>\n')




def convertir_figuras(escribir):
    """Convierte resultados/*.png a img/*.webp (sin pérdida). Devuelve las que faltan o están viejas."""
    from PIL import Image
    pendientes = []
    for nombre in FIGURAS:
        origen = RESULTADOS / f'{nombre}.png'
        destino = IMG / f'{nombre}.webp'
        if not origen.is_file():
            raise SystemExit(f'falta resultados/{nombre}.png')
        if not destino.is_file() or destino.stat().st_mtime < origen.stat().st_mtime:
            pendientes.append(nombre)
            if escribir:
                IMG.mkdir(exist_ok=True)
                with Image.open(origen) as im:
                    im.convert('RGB').save(destino, 'WEBP', lossless=True, method=6)
    return pendientes


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--comprobar', action='store_true')
    a = ap.parse_args()
    nuevo = html_completo()
    actual = SALIDA.read_text(encoding='utf-8') if SALIDA.exists() else None
    pendientes = convertir_figuras(escribir=not a.comprobar)
    if a.comprobar:
        if actual != nuevo or pendientes:
            print('DESFASADO: ejecuta python generar.py' + (f' (figuras: {", ".join(pendientes)})' if pendientes else ''))
            sys.exit(1)
        print('al día')
        return
    if pendientes:
        print(f'figuras convertidas a img/: {len(pendientes)}')
    if actual == nuevo:
        print('sin cambios')
    else:
        SALIDA.write_bytes(nuevo.encode('utf-8'))      # LF también en Windows
        minutos = sum(int(m) for m in re.findall(r'data-min="(\d+)"', nuevo))
        print(f'escrito {SALIDA.name}: {len(SLIDES)} diapositivas, {minutos} min')


if __name__ == '__main__':
    main()
