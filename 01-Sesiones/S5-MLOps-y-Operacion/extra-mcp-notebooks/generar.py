"""Genera la presentación «Extra de S5: MCP en notebooks» (index.html, junto a este archivo).

Qué cuenta: cómo se construyen y se vigilan dos servidores MCP desde notebooks: «mcp-datos-master» (consulta la capa master del caso Retail
en SQLite o en BigQuery, con defensa en cuatro capas) y «mcp-modelo-retencion» (lleva el modelo embebido y sigue el alias @champion de
MLflow). Mensaje: un MCP seguro no se fía de una sola capa, y uno de ML sigue al alias, no a un archivo.

TODAS las salidas y el código que se enseñan se LEEN de los notebooks de esta carpeta (00, 01 y 02), que se ejecutaron en local con
sus salidas guardadas: así la presentación no puede contar otra cosa que lo que se ejecutó. La excepción es BigQuery: las celdas de
BigQuery del notebook 01 salen «saltada» (no había credenciales); lo de BigQuery se probó el 26/11/2026 en Cloud Shell y de ello solo
hay las capturas de img/ (recortes de una captura del profesor), rotuladas con lo que muestran.

El visor (CSS y JavaScript: ← → · O índice · S notas · F pantalla completa · Esc · botón ⧉ «Copiar todo» · lupa con zoom al clic ·
pie «x / total») es el MISMO que el del laboratorio de agentes de S5, copiado aquí (no se importa); solo cambia el rótulo del pie.

Uso:  python generar.py              escribe index.html
      python generar.py --comprobar  no escribe; sale con 1 si index.html no está al día
"""
import argparse
import ast
import html
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / 'index.html'

FECHA_BQ = '26/11/2026'
TOTAL_MIN = 72
NOTEBOOKS = {'00': '00_preparar_entorno.ipynb', '01': '01_mcp_datos_sqlite_y_bigquery.ipynb', '02': '02_mcp_modelo_prediccion.ipynb'}

# Capturas (webp, recortes de la prueba real de BigQuery en Cloud Shell) -> lo que muestran de verdad (alt y pie).
CAPTURAS = {
    'bq-01-paridad.webp': 'Terminal de Cloud Shell (recorte): aparecen subidas las tablas master_facturas (1430 filas), master_lineas (22117) y master_productos (3077), y después las siete llamadas del notebook 01, cada una con «motor=bigquery IGUAL»',
    'bq-02-tope.webp': 'Terminal de Cloud Shell (recorte): la respuesta de resumen_cliente en BigQuery para el cliente 12369, la línea «con tope de 1 byte» con el error «Query exceeded limit for bytes billed: 1. 20971520 or higher required.» y la línea «RESULTADO: LOS DOS CONECTORES RESPONDEN LO MISMO»',
    'bq-03-borrado.webp': 'Terminal de Cloud Shell (recorte): la línea «dataset borrado: curso_master_prueba | quedan: []», con la que la prueba comprobó que no quedó nada en el proyecto (el notebook crea y borra el dataset curso_master; este nombre era el de la prueba)',
}
CAPTURAS_PENDIENTES = []

PARTES = {'A': 'Plan', 'B': 'Servidor de datos', 'C': 'BigQuery', 'D': 'Servidor del modelo', 'E': 'Límites y cierre'}
NOMBRES_PARTE = {'A': 'Qué vamos a hacer', 'B': 'Un MCP que consulta los datos', 'C': 'El segundo conector: BigQuery',
                 'D': 'Un MCP con el modelo dentro', 'E': 'Juntos, límites y cierre'}


# ------------------------------------------------------------------------------------------------------------------------
# Lectura de los notebooks (única fuente de código y de salidas)
# ------------------------------------------------------------------------------------------------------------------------
_CACHE = {}


def _celdas(n):
    if n not in _CACHE:
        _CACHE[n] = json.loads((AQUI / NOTEBOOKS[n]).read_text(encoding='utf-8'))['cells']
    return _CACHE[n]


def _txt(x):
    return ''.join(x) if isinstance(x, list) else x


def fuente_celda(n, i):
    return _txt(_celdas(n)[i]['source'])


def salida_celda(n, i):
    partes = []
    for o in _celdas(n)[i].get('outputs', []):
        partes.append(_txt(o['text']) if 'text' in o else _txt(o.get('data', {}).get('text/plain', '')))
    return ''.join(partes).strip('\n')


def trozo(texto, desde, hasta=None):
    """Líneas desde la primera que contiene `desde` hasta la anterior a la primera posterior que contiene `hasta` (o el final)."""
    lineas = texto.split('\n')
    ini = next(k for k, l in enumerate(lineas) if desde in l)
    fin = len(lineas)
    if hasta is not None:
        fin = next(k for k in range(ini + 1, len(lineas)) if hasta in lineas[k])
    return '\n'.join(lineas[ini:fin]).rstrip()


def quitar_comentarios(texto):
    return '\n'.join(re.sub(r'\s{2,}#.*$', '', l) for l in texto.split('\n'))


def bloques_json(n, i):
    return [json.loads(b) for b in re.findall(r'```json\n(.*?)```', fuente_celda(n, i), re.S)]


def ejercicios(n, i):
    t = fuente_celda(n, i).split('## Ejercicios', 1)[1]
    return [re.sub(r'^\d+\.\s*', '', l).strip() for l in t.splitlines() if re.match(r'\d+\.\s', l)]


# ------------------------------------------------------------------------------------------------------------------------
# Piezas del visor (copiadas del laboratorio de agentes de S5) y propias
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
    return (f'<div class="term"><div class="bar"><em>{esc(titulo)}</em><button class="cp cpall" data-t="{esc(texto)}">Copiar todo</button></div>'
            f'<pre class="src">{esc(texto.rstrip())}</pre></div>')


def cap(nombre, alto=None, nota=None):
    """Una captura (clic = ampliar) o, si aún no está en img/, el recuadro «Captura pendiente»."""
    alt = CAPTURAS[nombre]
    estilo = f' style="max-height:{alto}px"' if alto else ''
    extra = f'<br><span class="nota">{md(nota)}</span>' if nota else ''
    if (AQUI / 'img' / nombre).is_file() and nombre not in CAPTURAS_PENDIENTES:
        return (f'<figure class="cap" data-img="{nombre}"><button class="zoom" data-src="img/{nombre}" data-alt="{esc(alt)}" title="Ampliar (Esc cierra)">'
                f'<img src="img/{nombre}" alt="{esc(alt)}"{estilo}><span class="lupa">{LUPA} Ampliar</span></button>'
                f'<figcaption><span class="tag ok">Captura real</span> {esc(alt)}{extra}</figcaption></figure>')
    alto_p = f' style="min-height:{min(alto or 200, 260)}px"' if alto else ''
    return (f'<figure class="cap" data-img="{nombre}"><div class="pend"{alto_p}><b>Captura pendiente</b><span class="mono">img/{nombre}</span>'
            f'<span>{esc(alt)}</span></div><figcaption><span class="tag warn">Pendiente</span> {esc(alt)}{extra}</figcaption></figure>')


def lista(items):
    return '<ul class="list">' + ''.join(f'<li>{md(i)}</li>' for i in items) + '</ul>'


def mira(items, titulo='Qué debes ver'):
    return f'<div class="card mira"><h3>{esc(titulo)}</h3>{lista(items)}</div>'


def si_falla(items):
    return f'<div class="card falla"><h3>Si falla</h3>{lista(items)}</div>'


def tabla(cab, filas):
    th = ''.join(f'<th>{md(c)}</th>' for c in cab)
    tr = ''.join('<tr>' + ''.join(f'<td>{md(c)}</td>' for c in f) + '</tr>' for f in filas)
    return f'<table class="tbl"><tr>{th}</tr>{tr}</table>'


def kpi(valor, texto, color=''):
    return f'<div class="card kpi"><b class="n {color}">{esc(valor)}</b><p class="small">{md(texto)}</p></div>'


def salida(titulo, texto):
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


def svg_capas():
    """El camino de una pregunta: LLM -> herramientas -> vigilancia -> conexión -> motor, y el tope de filas a la vuelta."""
    g = ['<defs><marker id="fa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#0b5cad"/></marker></defs>']
    y = 40
    xs = [6, 226, 446, 666, 886]
    g.append(_caja(xs[0], y, 190, ['El LLM', 'lee las descripciones', 'y pide una herramienta'], 'nodo', 96))
    g.append(_caja(xs[1], y, 190, ['Capa 1', 'herramientas con nombre', 'el LLM da un número'], 'nodo puerta', 96))
    g.append(_caja(xs[2], y, 190, ['Capa 2 · validar_sql', 'solo para consulta_sql:', 'SELECT, 1 sentencia, master_*'], 'nodo puerta', 96))
    g.append(_caja(xs[3], y, 190, ['Capa 3', 'la conexión solo lee', 'mode=ro · bytes facturables'], 'nodo puerta', 96))
    g.append(_caja(xs[4], y, 190, ['El motor', 'SQLite o BigQuery', 'detrás de un conector'], 'nodo ok', 96))
    for k in range(4):
        g.append(f'<path d="M{xs[k] + 190} {y + 48} L{xs[k + 1] - 3} {y + 48}" class="fl" marker-end="url(#fa)"/>')
    g.append(f'<path d="M{xs[1] + 95} {y - 2} L{xs[1] + 95} 14 L{xs[3] + 95} 14 L{xs[3] + 95} {y - 3}" class="fl dis" marker-end="url(#fa)"/>')
    g.append('<text x="556" y="10" class="t2">las 6 herramientas con nombre van directas al conector</text>')
    g.append(f'<path d="M{xs[4] + 95} {y + 98} L{xs[4] + 95} 168 L{xs[0] + 95} 168 L{xs[0] + 95} {y + 100}" class="fl dis" marker-end="url(#fa)"/>')
    g.append('<rect x="400" y="148" width="300" height="40" rx="10" class="nodo puerta"/><text x="550" y="173" class="t1">Capa 4 · tope de 50 filas (MAX_FILAS)</text>')
    return ('<svg viewBox="0 0 1100 200" role="img" aria-label="El camino de una consulta: el LLM llama a una herramienta con nombre (capa 1), si es consulta_sql '
            'pasa por validar_sql (capa 2), la conexión solo lee (capa 3) y el motor responde; a la vuelta, un tope de 50 filas (capa 4)">' + ''.join(g) + '</svg>')


def svg_mcp():
    """Cliente, servidor y herramientas."""
    g = ['<defs><marker id="fm" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#0b5cad"/></marker></defs>']
    g.append(_caja(6, 20, 250, ['Cliente MCP', 'VS Code, un agente,', 'o tu ClienteMCP de 30 líneas'], 'nodo', 96))
    g.append(_caja(425, 20, 250, ['Servidor MCP', 'un proceso Python tuyo', 'FastMCP, transporte stdio'], 'nodo puerta', 96))
    g.append(_caja(844, 20, 250, ['Herramientas', 'nombre + argumentos', '+ descripción'], 'nodo ok', 96))
    g.append('<path d="M259 58 L420 58" class="fl" marker-end="url(#fm)"/><text x="340" y="48" class="t2">list_tools</text>')
    g.append('<path d="M420 84 L259 84" class="fl dis" marker-end="url(#fm)"/><text x="340" y="104" class="t2">las descripciones</text>')
    g.append('<path d="M678 58 L840 58" class="fl" marker-end="url(#fm)"/><text x="760" y="48" class="t2">las publica</text>')
    g.append('<text x="550" y="150" class="t2">call_tool(nombre, argumentos) → el servidor ejecuta → devuelve un resultado (JSON)</text>')
    return ('<svg viewBox="0 0 1100 170" role="img" aria-label="Un cliente MCP pide al servidor sus herramientas y recibe sus descripciones; después llama a una por nombre con argumentos">'
            + ''.join(g) + '</svg>')


# ------------------------------------------------------------------------------------------------------------------------
# Contenido
# ------------------------------------------------------------------------------------------------------------------------
def construir():
    SLIDES.clear()
    _N.clear()

    # ---------------------------------------------------------------- A · Plan
    slide('A', 3, 'Portada', 'ML e IA: de desarrollo a producción · S5 · extra', 'MCP en notebooks: que un LLM consulte tus datos y use tu modelo', f'''
<div class="cover">
 <p class="sub">Construyes <b>dos servidores MCP</b> sin salir de un notebook: uno que consulta la capa <i>master</i> del caso Retail (en <b>SQLite y en BigQuery</b>) y otro que lleva dentro <b>el modelo de retención a 90 días</b>. Y los <b>vigilas</b>: lo que importa de un MCP no es que funcione, sino que no pueda hacer daño.</p>
 <div class="chips"><span class="tag">3 notebooks</span><span class="tag">2 servidores MCP</span><span class="tag">SQLite y BigQuery</span><span class="tag">Defensa en 4 capas</span><span class="tag">Alias @champion</span><span class="tag">Paridad y rollback</span></div>
 <div class="grid3" style="margin-top:20px">
  {card('Objetivos', ['Publicar consultas y un modelo como **herramientas** que un LLM puede llamar.', 'Defender un «SQL libre» en **capas** que no dependen del LLM.', 'Comprobar que dos conectores **dan lo mismo** y que el MCP **no inventa** nada.'])}
  {card('Duración propuesta', [f'**{TOTAL_MIN} min** en cinco partes (minuto propuesto en la barra inferior).', 'Cada orden con **⧉** para copiarla; las salidas son las **guardadas** en los notebooks.', '**← →** avanzan · **O** índice · **S** notas · **F** pantalla completa.'])}
  {card('Honestidad desde el principio', [f'**BigQuery** se probó de verdad el **{FECHA_BQ}** en Cloud Shell; el notebook 01 se ejecutó **sin BigQuery** (esas celdas salen «saltada»).', '**Sin verificar:** conectar los servidores a VS Code/Copilot y ejecutar los notebooks en un Codespace.'])}
 </div>
</div>''',
          'Portada del extra de la sesión 5. Son tres notebooks y dos servidores MCP. Diga desde el principio lo que se probó y lo que no: los notebooks se ejecutaron en local con sus salidas guardadas y esas son las cifras de esta presentación; BigQuery se probó de verdad el veintiséis de noviembre en Cloud Shell, pero el notebook uno se ejecutó sin BigQuery, así que sus celdas de BigQuery salen saltada. Conectar los servidores a VS Code y ejecutar todo en un Codespace está sin verificar.')

    slide('A', 3, 'Qué es MCP', 'cliente, servidor y herramientas', 'Un MCP es un contrato: nombre, argumentos y una descripción que lee el LLM', f'''
<div class="card">{svg_mcp()}</div>
<div class="grid3" style="margin-top:12px">
 {card('Lo que el LLM ve', ['Una lista de herramientas con su **descripción**: es lo que lee para decidir cuál usar.', 'No ve tu código, ni la base de datos, ni el modelo.'])}
 {card('Lo que tú controlas', ['Qué herramientas existen, qué argumentos admiten y **qué devuelven**.', 'Qué pasa con un argumento mal escrito o un SQL que no debería ejecutarse.'])}
 {card('Dónde encaja en S5', ['En el laboratorio de agentes usaste `mcp-retencion` (`lista_del_dia`, `puntuar_online`, `puntuar_bajo_demanda`…) ya hecho.', 'Aquí construyes **dos desde cero**: datos y modelo.'])}
</div>''' + fuente('notebook 01 (introducción y apartado 3) y laboratorio de agentes de S5.'),
          'Qué es un MCP, sin entrar en el protocolo. Un cliente, que puede ser VS Code, un agente o la clase de treinta líneas del notebook, lanza el servidor como proceso y le pide la lista de herramientas. Cada herramienta tiene un nombre, unos argumentos y una descripción, y la descripción es lo que el LLM lee para decidir cuál usar. El LLM no ve el código ni los datos. En el laboratorio de agentes ya se usó mcp-retencion; aquí se construyen dos servidores desde cero.')

    slide('A', 2, 'Mapa del extra', 'tres notebooks, dos servidores', 'Tres notebooks y dos servidores: cada notebook escribe el suyo y lo prueba', '<div class="card">' + tabla(['Notebook', 'Qué haces', 'Qué aprendes', 'Se guarda en'], [
        ['**00** · Preparar el entorno', 'Compruebas paquetes, datos, modelo registrado y BigQuery (opcional)', 'Un «TODO LISTO» o la lista de lo que falta', '—'],
        ['**01** · Datos, SQLite y BigQuery', 'Escribes y pruebas **`mcp-datos-master`**: 6 herramientas con nombre y `consulta_sql` vigilada', 'Dos conectores con la misma interfaz y una defensa en 4 capas', '`_trabajo/mcp_datos.py`'],
        ['**02** · El modelo', 'Escribes y pruebas **`mcp-modelo-retencion`**: 4 herramientas', 'El alias `@champion` de MLflow en cada llamada', '`_trabajo/mcp_modelo.py`']]) + '''</div>
<div class="grid2" style="margin-top:12px">
 ''' + card('Cómo se escribe un servidor', ['La celda `%%writefile` guarda el servidor en `_trabajo/`: así lo lanza **un proceso aparte**, como hace cualquier cliente MCP.', 'Una copia de referencia de los dos está en `fuentes/`.']) + card('Qué hace falta', ['El proyecto del curso con `curso.db` y el modelo `retencion-90d` registrado en MLflow (S1 y S5).', 'SQLite funciona sin nada más; **BigQuery es opcional**.']) + '''
</div>''' + fuente('los tres notebooks.'),
          'Mapa del extra. Tres notebooks: el cero solo comprueba el entorno, el uno construye el servidor de datos y el dos construye el del modelo. Cada notebook escribe su servidor con la orden mágica writefile en la carpeta de trabajo, porque un cliente MCP lanza el servidor como proceso aparte. En la carpeta fuentes hay una copia de referencia de los dos servidores, idéntica al código de los notebooks salvo los finales de línea.')

    s00 = salida_celda('00', 5)
    slide('A', 2, 'Notebook 00', 'comprobar antes de construir', 'El notebook 00 solo comprueba: «TODO LISTO» o te dice qué falta', f'''
''' + dos_columnas(salida('Salida guardada · notebook 00 · apartado 2', s00) + fuente('notebook 00, apartados 1 a 3 (paquetes, datos y modelo, BigQuery).'),
                    mira(['**150 clientes** en `master_clientes`, **1430** facturas, **22 117** líneas y **3077** productos; `fs_produccion` con **148** filas.', 'El modelo `retencion-90d` tiene **6 versiones**, todas con AUC de validación **0,6982** y de test **0,7471**; aún sin alias.', '`mcp` en la **1.30.0**: el proyecto la fija a propósito (la 2.x quitó `FastMCP`).', 'BigQuery: «no configurado (el notebook 01 usará solo SQLite)».']) + callout('Si algo falta, el propio notebook dice la orden: por ejemplo, `python -m ia_mlops.pipeline` desde `04-Proyecto-Base` (unos 30 s con la muestra).'), '1fr 1fr'),
          'El notebook cero no construye nada. Comprueba que están los paquetes, que existe curso punto db con las cuatro tablas master y fs produccion, y que el modelo retencion noventa d está registrado en MLflow. La salida guardada dice todo listo. Hay seis versiones del modelo, todas con el mismo AUC porque se entrenaron con los mismos datos, y todavía ninguna tiene alias. El último apartado comprueba BigQuery: aquí no estaba configurado, y el notebook uno seguirá solo con SQLite.')

    # ---------------------------------------------------------------- B · Servidor de datos
    slide('B', 3, 'La defensa en cuatro capas', 'diseño de mcp-datos-master', 'Un LLM que escribe SQL es peligroso: cuatro capas, y las dos últimas no dependen de nadie', f'''
<div class="card">{svg_capas()}</div>
<div class="grid2" style="margin-top:12px">
 {card('Las capas', ['**1 ·** herramientas con nombre y argumentos tipados: el SQL lo escribes tú.', '**2 ·** `consulta_sql` es el último recurso y la vigila `validar_sql`.', '**3 ·** SQLite se abre en `mode=ro`; BigQuery lleva un tope de bytes (`maximum_bytes_billed`).', '**4 ·** nunca se devuelven más de 50 filas.'])}
 {callout('**Las capas 3 y 4 no dependen del LLM ni de la capa 2:** si la vigilancia falla, siguen protegiendo. Por eso `validar_sql` puede ser una expresión regular sin que sea «la» defensa.', 'align-self:center')}
</div>''' + fuente('notebook 01, apartado 1 (docstring del servidor) y código de `consulta_sql` y `_ejecutar`.'),
          'El diseño del servidor de datos. Un LLM puede equivocarse o ser engañado, por ejemplo por un texto malicioso dentro de un dato, así que no se le da un SQL libre sin más. Capa uno: herramientas con nombre, donde el SQL lo escribe el servidor y el LLM solo da un número. Capa dos: la herramienta consulta sql, último recurso, vigilada por validar sql. Capa tres: la conexión solo puede leer, SQLite abierto en modo solo lectura y BigQuery con un tope de bytes facturables. Capa cuatro: un tope de cincuenta filas. Las capas tres y cuatro no dependen de las anteriores.')

    src_bq = trozo(fuente_celda('01', 3), 'class ConectorBigQuery', 'def elegir_conector')
    ej_bq = trozo(src_bq, '    def ejecutar', '    def columnas')
    ej_sqlite = trozo(fuente_celda('01', 3), '    def _abrir', '    def columnas')
    slide('B', 3, 'Dos conectores, una interfaz', 'SQLite y BigQuery', 'Dos conectores con la misma interfaz: el servidor no sabe qué motor hay detrás', f'''
<div class="grid2">
 <div class="col">{codigo('ConectorSQLite · extracto del notebook 01 (sin comentarios)', quitar_comentarios(ej_sqlite))}</div>
 <div class="col">{codigo('ConectorBigQuery · extracto del notebook 01 (sin comentarios)', quitar_comentarios(ej_bq))}</div>
</div>
<div class="grid3" style="margin-top:12px">
 {card('La interfaz', ['Los dos ofrecen `tabla()`, `columnas()` y `ejecutar()`.', 'Las consultas usan parámetros `@nombre`: valen para los dos motores.'])}
 {card('Cómo se elige', ['Una variable de entorno: `MCP_BACKEND=sqlite` (por defecto) o `bigquery`.', 'Con BigQuery hacen falta `GCP_PROJECT` y, si no es `curso_master`, `BQ_DATASET`.'])}
 {card('Lo que cambia por motor', ['SQLite: abre la base en solo lectura (capa 3).', 'BigQuery: un tope de **100 MB** por consulta (`MCP_BQ_MAX_BYTES`); el dataset entero pesa unos 2 MB.'])}
</div>''' + fuente('notebook 01, apartado 1 (celda que escribe `mcp_datos.py`).'),
          'Los dos conectores. El servidor llama siempre a tabla, columnas y ejecutar y no sabe qué motor hay detrás. En SQLite, la conexión se abre con mode igual ro, solo lectura. En BigQuery, cada consulta lleva maximum bytes billed: si superase el tope, BigQuery ni la ejecuta. El tope por defecto es cien megabytes y el dataset entero pesa unos dos. La variable MCP BACKEND elige el conector al arrancar el servidor.')

    cliente = fuente_celda('01', 5)
    cliente_corto = trozo(cliente, 'class ClienteMCP')
    cliente_corto = re.sub(r'    """.*?"""\n\n', '', cliente_corto, flags=re.S)
    cliente_corto = quitar_comentarios(cliente_corto)
    slide('B', 3, 'El cliente de 30 líneas', 'lo que hace VS Code, en un notebook', 'Un cliente MCP son treinta líneas: lanza el servidor y le habla por stdio', f'''
''' + dos_columnas(codigo('ClienteMCP · notebook 01, apartado 2 (sin docstring ni comentarios)', cliente_corto),
                    mira(['El cliente **lanza el servidor como proceso hijo** y le habla por su entrada y salida estándar (transporte `stdio`).', '`herramientas()` pide la lista y `llamar(nombre, **args)` ejecuta una.', 'Si el propio protocolo rechaza los argumentos (un tipo mal puesto), `isError` lo recoge como `error_del_protocolo`.']) + callout('**Ojo en Jupyter:** `stdio_client` escribe el `stderr` del servidor en `sys.stderr`, y el de Jupyter no tiene `fileno`. Por eso se abre un **archivo** (`servidor.err`) y se pasa como `errlog`.') + callout('Y un servidor **nunca debe usar `print`** hacia la salida estándar: `stdout` es el canal del protocolo. Los avisos van por `stderr`.'), '1.05fr .95fr'),
          'El cliente en treinta líneas. Es lo mismo que hacen VS Code, Claude Desktop o un agente: lanzan el servidor como proceso hijo, le piden las herramientas y las llaman por nombre, hablando por la entrada y salida estándar. Dos detalles reales: en Jupyter el stderr no tiene fileno, así que se abre un archivo y se pasa como errlog; y el servidor no puede imprimir por stdout, porque ese es el canal del protocolo, por eso sus avisos van por stderr. Si el SDK rechaza los argumentos por su tipo, el resultado vuelve marcado como error.')

    slide('B', 3, 'Las siete llamadas', 'salida real con SQLite', 'Siete herramientas, siete llamadas: todas dicen qué motor las respondió', f'''
''' + dos_columnas('<div class="card">' + tabla(['Herramienta y argumentos', 'Qué devolvió (SQLite)'], [
        ['`listar_tablas`', '`master_clientes` **150** · `master_facturas` **1430** · `master_lineas` **22 117** · `master_productos` **3077**'],
        ['`describir_tabla` · `master_clientes`', '4 columnas: `cliente_id`, `pais`, `primer_movimiento`, `ultimo_movimiento`, y 3 filas de muestra'],
        ['`resumen_cliente` · 12369', 'Austria · **3** facturas · **0** cancelaciones · monto **1511,15**'],
        ['`ultimas_facturas` · 12369, n=2', 'facturas 528576 (**183,35**) y 522773 (**1259,48**)'],
        ['`ventas_por_pais` · n=3', 'United Kingdom **344 244,74** · France **18 857,36** · Portugal **10 780,8**'],
        ['`top_productos` · n=3', '84077 (**2720** uds) · 22178 (**2712**) · 85099B (**2244**)'],
        ['`consulta_sql` · clientes por país', 'United Kingdom **135** · France **5** · Germany **3**']]) + '</div>',
                    salida('Salida guardada · notebook 01 · apartado 4 · resumen_cliente', trozo(salida_celda('01', 9), '--- resumen_cliente', '--- ultimas_facturas')) + mira(['Cada respuesta lleva `"motor": "sqlite"`.', 'Las 7 se lanzan con `ejecutar_casos(...)`: el mismo código servirá para BigQuery.']) + fuente('notebook 01, apartado 4; la salida completa (7 llamadas) está guardada en esa celda.'), '1.2fr .8fr'),
          'Las siete llamadas, una por herramienta, con salida real guardada en el notebook. Se ve que cada respuesta dice qué motor la produjo. Un detalle para el aula: ventas por país da ciento treinta y tres clientes en el Reino Unido y la consulta libre da ciento treinta y cinco; no son la misma pregunta, porque la primera cuenta solo clientes con ventas válidas y la segunda cuenta todas las filas de master clientes. Estas mismas siete llamadas son las que se repiten con BigQuery.')

    ataques_src = fuente_celda('01', 11)
    ATAQUES = ast.literal_eval(re.search(r'ATAQUES = (\{.*?\n\})', ataques_src, re.S).group(1))
    resp = dict(re.findall(r'^(.*?)\s+→ RECHAZADA: (.*)$', salida_celda('01', 11), re.M))
    reglas = {'borrar una tabla': 'no empieza por SELECT ni WITH', 'modificar datos': 'no empieza por SELECT ni WITH', 'varias sentencias': 'un `;` en medio',
              'comentario para esconder algo': 'lleva `--`', 'otra tabla (variables del modelo)': 'tabla fuera de la lista `master_*`',
              'el catálogo del motor': 'tabla fuera de la lista `master_*`', 'tabla con ruta completa': 'un punto en el nombre de la tabla',
              'unir tablas con coma': 'tablas separadas por comas'}
    filas_ataque = []
    for nombre, sql in ATAQUES.items():
        corta = resp[nombre].split('. Tablas:')[0]
        filas_ataque.append([f'**{nombre}**', f'<SQL>{sql}</SQL>', corta, reglas[nombre]])
    t_ataques = tabla(['Intento', 'SQL', 'Respuesta real', 'Qué regla lo frena'], filas_ataque)
    t_ataques = re.sub(r'&lt;SQL&gt;(.*?)&lt;/SQL&gt;', lambda m: f'<span class="mono">{m.group(1)}</span>', t_ataques)
    slide('B', 4, 'Intentar romperlo', 'ocho consultas que nunca deben ejecutarse', 'Ocho ataques a `consulta_sql`: los ocho los frena `validar_sql`', f'''
<div class="card">{t_ataques}</div>
<div style="margin-top:10px">{callout('**No te fíes de una sola capa:** una expresión regular no es un analizador de SQL. Si una se colase, SQLite abierto en solo lectura (capa 3) frenaría un UPDATE; esa prueba **no** la hace el notebook: es el ejercicio 1.')}</div>''' + fuente('notebook 01, apartado 5 (la columna «Qué regla lo frena» resume el código de `validar_sql`).'),
          'Intentar romperlo. Son ocho consultas que nunca deben ejecutarse y las ocho las frena validar sql, la capa dos. Cada una por una regla distinta: la que no empieza por select, la de varias sentencias, la de los comentarios, las tablas que no son master y la de la ruta completa. Insista en que no hay que fiarse de una sola capa, porque una expresión regular no es un analizador de SQL: si una se colase, la capa tres, solo lectura, haría fallar un update. Esa prueba no está en el notebook y es el ejercicio uno.')

    slide('B', 2, 'Topes y protocolo', 'cincuenta filas y un tipo mal puesto', 'Dos defensas más: el tope de 50 filas y el rechazo de un tipo mal puesto', f'''
''' + dos_columnas(salida('Salida guardada · notebook 01 · apartado 5', trozo(salida_celda('01', 11), 'SELECT * de 22 117') ) + callout('**Capa 4:** el servidor pide a la base 51 filas (`fetchmany(MAX_FILAS + 1)`) y, si llegan 51, devuelve 50 y marca `truncado: True`. El LLM no necesita 22 117 líneas ni su ventana de contexto tampoco.'),
                    mira(['`cliente_id = "abc"` no llega a tu función: la herramienta declara `cliente_id: int` y **el SDK valida el tipo** antes de llamar.', 'La respuesta es un `error_del_protocolo` con el aviso de validación (arriba, tal cual salió).', 'En el modelo (notebook 02) el mismo `"abc"` da el mismo tipo de error.']) + fuente('notebook 01, apartado 5 y código de `_ejecutar`; notebook 02, apartado 9.'), '1.1fr .9fr'),
          'Dos defensas más. El tope de filas: el servidor pide cincuenta y una filas; si llegan cincuenta y una, devuelve cincuenta y marca truncado. Con select estrella sobre las veintidós mil ciento diecisiete líneas devuelve cincuenta. Y el error de protocolo: si el LLM manda abc donde se espera un entero, el SDK lo rechaza antes de llamar a la función, porque la herramienta declara el tipo. El texto del error es el que salió en la ejecución guardada.')

    # ---------------------------------------------------------------- C · BigQuery
    slide('C', 3, 'BigQuery: preparar el proyecto', 'opcional', 'BigQuery es opcional: tu proyecto, tus credenciales y nunca el del trabajo', f'''
''' + dos_columnas(term('Terminal · una orden cada vez · cambia TU_PROYECTO', [
        '# 1) credenciales de aplicación de Google', 'gcloud auth application-default login',
        '# 2) tu proyecto de pruebas, NO el del trabajo', 'gcloud config set project TU_PROYECTO',
        '# 3) díselo al notebook (bash) ANTES de abrirlo', 'export GCP_PROJECT=TU_PROYECTO',
        '# en Windows (cmd)', 'set GCP_PROJECT=TU_PROYECTO']) + fuente('notebook 00, apartado 3.') + sin_verificar('que estas órdenes funcionen en un **Codespace**: la prueba real fue en **Cloud Shell**.'),
                    mira(['El notebook crea y borra el dataset **`curso_master`**: unas **22 000 filas**, unos **2 MB**; con el nivel gratuito de BigQuery no cuesta nada, pero **es tu cuenta**.', 'Opcionales: `BQ_DATASET` (por defecto `curso_master`) y `BQ_LOCATION` (por defecto `US`).', 'Sin `GCP_PROJECT` ni credenciales, las celdas dicen **«saltada»** y el notebook sigue con SQLite.']) + callout('**Cómo se ejecutó este notebook:** sin BigQuery. Sus salidas guardadas dicen «BigQuery SALTADO» y «saltada». Lo de BigQuery de las diapositivas siguientes viene de **otra prueba** (Cloud Shell, ' + FECHA_BQ + ').'), '1fr 1fr'),
          'Preparar BigQuery, que es opcional. Hacen falta credenciales de aplicación, un proyecto propio donde se pueda crear un dataset y la variable GCP PROJECT definida antes de abrir el notebook. Insista: no se usa el proyecto del trabajo; el notebook crea y borra un dataset llamado curso master de unas veintidós mil filas y dos megas, que con el nivel gratuito no cuesta nada pero es la cuenta de cada uno. Aclare lo que se hizo: el notebook uno se ejecutó sin BigQuery y por eso esas celdas salen saltada; la prueba real de BigQuery se hizo aparte en Cloud Shell.')

    slide('C', 3, 'Mismas siete llamadas, mismo resultado', 'prueba real en Cloud Shell', 'El mismo servidor con otro motor: las siete llamadas dan IGUAL', f'''
''' + dos_columnas(cap('bq-01-paridad.webp', 260),
                    mira([f'Prueba real del **{FECHA_BQ}** en **Cloud Shell**, con la cuenta del curso y un **dataset temporal**, con un script que repite los pasos del notebook (no el notebook en Jupyter).', 'Cada línea compara la respuesta de BigQuery con la de SQLite **ignorando el campo motor**.']) + callout('**Dos conectores que dan respuestas distintas no son dos conectores, son dos bugs.** La comparación (igual) tolera 0,01 en los decimales (los motores suman en otro orden) y de las columnas compara solo los nombres (INTEGER frente a INT64).') + fuente('notebook 01, apartados 7 y 8 (texto y función igual); captura de Cloud Shell, ' + FECHA_BQ + '.'), '.8fr 1.2fr'),
          'La prueba de paridad de BigQuery. La captura es real, de Cloud Shell el veintiséis de noviembre con la cuenta del curso: aparecen las tablas subidas y, para cada una de las siete llamadas, la palabra igual, es decir, BigQuery respondió lo mismo que SQLite. Aclare que se hizo con un script que repite los pasos del notebook y no con el notebook en Jupyter. La comparación ignora el campo motor, tolera una centésima en los decimales y compara solo los nombres de las columnas porque los tipos se llaman distinto. En la captura se ven tres tablas subidas; la línea de master clientes no sale en el recorte.')

    slide('C', 3, 'El tope de bytes y la caché', 'prueba real en Cloud Shell', 'El tope de coste funciona: con 1 byte, BigQuery ni ejecuta la consulta', f'''
''' + cap('bq-02-tope.webp', 120) + '''
<div class="grid2" style="margin-top:8px">
 ''' + mira(['El tope se fija con `MCP_BQ_MAX_BYTES`; la prueba lo baja a **1 byte** y BigQuery responde «Query exceeded limit for bytes billed: 1. **20971520** or higher required».', 'BigQuery **cobra por mínimos** (unos 20 MB), no por bytes sueltos: por eso el mensaje pide 20 971 520.']) + callout('**Truco de la caché:** BigQuery guarda el resultado de una consulta repetida y esa respuesta **no se factura**, así que no pasaría por el tope. El notebook usa una consulta que no se había lanzado antes (`top_productos` con `n=7`). La captura **no** enseña qué consulta se usó en la prueba de Cloud Shell.') + '''
</div>''' + fuente('notebook 01, apartado 9 (texto y celda); captura de Cloud Shell, ' + FECHA_BQ + '.'),
          'El tope de coste. El servidor fija maximum bytes billed y, si una consulta lo supera, BigQuery ni la ejecuta. Se fuerza con un tope absurdo de un byte y BigQuery contesta que hacen falta al menos veinte megas, veinte millones novecientos setenta y un mil quinientos veinte bytes: cobra por mínimos. La nota importante es la caché: una consulta repetida sale de la caché y no se factura, así que no pasaría por el tope; por eso el notebook usa una consulta nueva, top productos con n igual a siete. La captura no muestra qué consulta se lanzó en Cloud Shell.')

    slide('C', 2, 'Borrar el dataset', 'que no quede nada a tu nombre', 'Al terminar, se borra el dataset: que no quede nada a tu nombre', f'''
''' + dos_columnas(codigo('Notebook 01 · apartado 10', trozo(fuente_celda('01', 23), 'BORRAR_DATASET')) + fuente('notebook 01, apartado 10; la salida guardada en local es «Nada que borrar» (no se creó nada).'),
                    cap('bq-03-borrado.webp', 60) + mira(['`delete_contents=True` borra las cuatro tablas con el dataset; `not_found_ok=True` evita el error si ya no estaba.', 'Si quieres conservarlo, pon `BORRAR_DATASET = False`.']), '1fr 1fr'),
          'Limpiar. Si se subieron las tablas a BigQuery, se borran: así no queda nada a nombre del alumno. La captura es del final de la prueba real en Cloud Shell: dataset borrado, y la lista de datasets que quedan, vacía. En la ejecución local del notebook la salida guardada es nada que borrar, porque no se creó nada.')

    # ---------------------------------------------------------------- D · Servidor del modelo
    slide('D', 2, 'Un modelo es una función', 'mcp-modelo-retencion', 'Un modelo es una función: variables del cliente → probabilidad; un MCP la publica', f'''
<div class="grid2">
 <div class="card">''' + tabla(['Herramienta', 'Para qué'], [
        ['`predecir_cliente(cliente_id)`', 'Probabilidad con las variables del último lote (`fs_produccion`)'],
        ['`predecir_variables(variables)`', '«¿Y si…?»: un cliente **inventado**'],
        ['`por_que(cliente_id, n)`', 'Qué variables empujan esa probabilidad (exacto)'],
        ['`modelo_en_uso()`', 'Versión del alias, AUC y cuántas versiones hay']]) + '''</div>
 <div class="col">''' + callout('**La probabilidad es de VOLVER A COMPRAR en 90 días.** Alta = **buena noticia**; no es un «riesgo de abandono». Está en las instrucciones del servidor para que el LLM no lo lea al revés.') + card('Dos cosas que no vienen del modelo', ['El **tramo** (alta, media, baja) y la recomendación son una **regla de negocio** de `config.py`: se acuerda con quien hace la campaña.', 'El LLM no ve el modelo ni los datos: pide `predecir_cliente(12369)` y recibe un JSON.']) + '''</div>
</div>''' + fuente('notebook 02, introducción y apartado 2 (docstring y `instructions` del servidor).'),
          'La idea del segundo servidor. Un modelo es una función: variables del cliente a probabilidad, y un MCP la publica como herramienta. Son cuatro herramientas. Una advertencia de lectura que está escrita en las instrucciones del servidor: la probabilidad es de volver a comprar, así que alta es buena noticia y no un riesgo de abandono. El tramo y la recomendación no salen del modelo: son una regla de negocio del proyecto.')

    mc = trozo(fuente_celda('02', 5), 'def modelo_champion', 'def tramo_de')
    slide('D', 3, 'El alias en cada llamada', 'qué modelo responde', 'No carga un archivo: pregunta al alias `@champion` en cada llamada', f'''
''' + dos_columnas(codigo('modelo_champion() · notebook 02, apartado 2 (sin comentarios)', quitar_comentarios(mc)),
                    mira(['En **cada llamada** pregunta a MLflow a qué versión apunta `models:/retencion-90d@champion`.', 'Solo **recarga si la versión cambió** (la carga es lo caro).', 'Si el alias no existe, devuelve un **error claro** con la orden para asignarlo, no un traceback.']) + callout('Así un **rollback** (mover el alias) cambia lo que responde el MCP **sin reiniciarlo y sin tocar el código**. Es la parte MLOps: lo que manda es el registro, no un archivo.') + fuente('notebook 02, apartado 2; estado inicial del registro en el apartado 1.'), '1.05fr .95fr'),
          'Qué modelo responde. El servidor no abre un archivo fijo: en cada llamada pregunta a MLflow a qué versión apunta el alias champion y solo recarga el modelo si la versión cambió, porque cargarlo es lo caro. Si el alias no existe, devuelve un error con la orden para asignarlo. Con esto un rollback, que es mover el alias, cambia lo que responde el MCP sin reiniciarlo.')

    out11 = salida_celda('02', 11)
    slide('D', 3, 'Predecir un cliente', 'predecir_cliente(12369)', 'El cliente 12369 tiene un 30 % de probabilidad de volver: tramo bajo', f'''
''' + dos_columnas(salida('Salida guardada · notebook 02 · apartado 5', trozo(out11, '{', '--- ¿por qué?').rstrip()) + fuente('notebook 02, apartado 5.'),
                    mira(['Probabilidad **0,3035**, tramo **baja**, modelo **v6** con el alias `champion`.', 'Las variables son las del **corte 2011-12-10** de `fs_produccion`: **413 días** sin comprar, 3 facturas, 0 compras en los últimos 180 días.', 'Mismo cliente 12369 que en el servidor de datos: **Austria**, monto **1511,15**.']) + callout('Los números son de **este cliente en esta versión**; el LLM debería contar el tramo y la recomendación, no inventar el motivo (para eso está `por_que`).'), '1.05fr .95fr'),
          'Predecir un cliente. El mismo cliente que en el servidor de datos, el doce mil trescientos sesenta y nueve, de Austria. El modelo da cero coma tres cero tres cinco, tramo baja, con la versión seis y el alias champion, con las variables del corte del diez de diciembre de dos mil once. Recuerde que alta es buena noticia: aquí es poco probable que vuelva a comprar en noventa días.')

    pq = trozo(out11, '--- ¿por qué?', '--- el modelo en uso')
    slide('D', 3, 'Por qué sale ese número', 'por_que(12369)', 'Por qué sale 0,3035: el modelo es una regresión logística y se reparte exacto', f'''
''' + dos_columnas(salida('Salida guardada · notebook 02 · apartado 5', pq) + fuente('notebook 02, apartado 5 (`por_que` con `n=4`).'),
                    mira(['Cada peso es **coeficiente × valor transformado**; intercepto **+0,225** más la suma de todos los pesos = **logit −0,831**.', 'La probabilidad es `1/(1+e^-logit)` = **0,3035**: la descomposición reproduce la cifra del modelo.', 'Sin actividad en 180 días **baja** (−1,339); devoluciones 0 **baja** (−0,516).']) + callout('**Dice qué empuja la cifra, no por qué compra el cliente.** Y fíjate: **413 días** sin comprar **sube** (+0,583). Eso se explora en la siguiente diapositiva.') + sin_verificar('que el reparto exacto valga para otro modelo: si no es una regresión logística, la herramienta devuelve una nota y **no** reparte.'), '1fr 1fr'),
          'Por qué sale ese número. Como el modelo es una regresión logística, la probabilidad se reparte de forma exacta: cada variable pesa coeficiente por valor transformado, y el intercepto más la suma de pesos da el logit, menos cero coma ocho tres uno, que equivale a cero coma tres cero tres cinco. Lo que dice la herramienta es qué empuja la cifra, no por qué compra el cliente. Llame la atención sobre la recencia: cuatrocientos trece días sin comprar suma, no resta. Es el hilo de la siguiente diapositiva. Si el modelo no fuera una regresión logística, la herramienta devuelve una nota y no reparte.')

    out13 = salida_celda('02', 13)
    filas_y = re.findall(r'^\d+\s+(\d+)\s+([\d.]+)\s+(\w+)$', out13, re.M)
    t_y = tabla(['recencia_dias', 'probabilidad', 'tramo'], [[f'**{d}**', p.replace('.', ','), t] for d, p, t in filas_y])
    parcial = salida_celda('02', 14)
    slide('D', 4, '¿Y si…?', 'predecir_variables', 'Con más días sin comprar, la probabilidad SUBE: al revés que la intuición', f'''
''' + dos_columnas('<div class="card">' + t_y + '</div>' + fuente('notebook 02, apartado 6: cliente de ejemplo (`cliente_ejemplo.json`) moviendo **solo** `recencia_dias`.') + salida('Salida guardada · con una sola variable', parcial),
                    callout('**Sorpresa:** es lo que el modelo aprendió con estos datos. **No es un fallo del MCP** (la paridad de la siguiente diapositiva lo comprueba) y **no es una relación causal**.') + mira(['Con 150 clientes y variables muy relacionadas (recencia, antigüedad, frecuencia), **un coeficiente suelto puede engañar**.', 'Mover **una** variable no equivale a un cliente real: en la realidad se mueven juntas.', 'El notebook **no ha investigado por qué ocurre**: es una buena pregunta para la tarea.']) + '<p class="small">' + md('Con **35 días** sale **0,8279**, la misma cifra que el cliente de ejemplo del laboratorio de MLOps (L3).') + '</p>', '.85fr 1.15fr'),
          'El que pasa si. Se parte del cliente de ejemplo del proyecto y se mueve una sola variable, la recencia. La intuición dice que cuanto más tiempo sin comprar, menos probable que vuelva, pero el modelo dice lo contrario: de cero coma siete cinco tres tres con cinco días a cero coma ocho nueve seis cinco con trescientos sesenta y cinco. No es un fallo del MCP, es lo que aprendió con estos datos, no es causal, y no se ha investigado por qué. Con solo una variable, el modelo imputa el resto con la mediana del entrenamiento y avisa; la probabilidad cambia a cero coma dos tres nueve cinco.')

    par = salida_celda('02', 17)
    slide('D', 2, 'Paridad con el modelo a mano', 'el MCP no inventa nada', 'El MCP da lo mismo que el modelo cargado a mano: diferencia máxima 0,0', f'''
''' + dos_columnas(salida('Salida guardada · notebook 02 · apartado 7 · 12 clientes', par), mira(['Se carga el modelo **a mano** (`models:/retencion-90d@champion`), sin MCP, y se puntúan los **mismos 12 clientes**.', 'Las dos columnas están redondeadas a 4 decimales; la prueba exige una diferencia **menor que 1e-4** y salió **0,0**.', 'Esto es lo que descarta que la sorpresa del «¿y si…?» sea un fallo del servidor.']) + fuente('notebook 02, apartado 7.'), '1fr 1fr'),
          'La paridad. Se carga el modelo a mano, sin MCP, y se puntúan los mismos doce clientes. Las probabilidades coinciden: la diferencia máxima es cero. Las dos columnas están redondeadas a cuatro decimales, y el notebook exige menos de uno por diez a la menos cuatro. Es la prueba de que el servidor no inventa nada y de que la sorpresa de la recencia viene del modelo.')

    rb = salida_celda('02', 19)
    slide('D', 3, 'Rollback sin reiniciar', 'v6 → v1 → v6', 'Con el servidor arrancado, mover el alias cambia la versión que responde', f'''
''' + dos_columnas(salida('Salida guardada · notebook 02 · apartado 8', rb) + term('Terminal · desde 04-Proyecto-Base · orden del laboratorio de MLOps', ['python -m ia_mlops.alias_modelo promover --version 1', 'python -m ia_mlops.alias_modelo volver']) + fuente('notebook 02, apartado 8 (usa las mismas funciones `promover` y `volver`); las órdenes son las del laboratorio de MLOps (L3).'),
                    mira(['El servidor lleva **una sola sesión abierta**: la misma conexión responde con la v6, luego con la v1 y otra vez con la v6.', '**Misma probabilidad (0,3035)** en las tres porque las 6 versiones se entrenaron con los mismos datos (AUC de validación **0,6982**, de test **0,7471**).']) + callout('**Honestidad:** lo que cambia es la **versión que responde**. Con modelos de verdad distintos cambiaría también la cifra. Esta prueba demuestra el mecanismo, no una mejora.'), '1fr 1fr'),
          'El rollback sin reiniciar. Con el cliente conectado al servidor, se promueve el alias champion a la versión uno y se vuelve a preguntar: responde la versión uno. Después se hace el rollback con volver y responde otra vez la seis. Todas dan la misma probabilidad porque las seis versiones se entrenaron con los mismos datos, con AUC de validación cero coma seis nueve ocho dos y de test cero coma siete cuatro siete uno. Lo que se demuestra es el mecanismo, no una mejora. Las dos órdenes de terminal son las del laboratorio de MLOps; el notebook usa las mismas funciones.')

    t_err = salida_celda('02', 21)
    slide('D', 2, 'Cuando algo sale mal', 'errores que el LLM puede contar', 'Un MCP bueno no se rompe: devuelve un error claro que el LLM puede contar', f'''
''' + dos_columnas(salida('Salida guardada · notebook 02 · apartado 9', t_err) + fuente('notebook 02, apartado 9 (los textos salen recortados a 110 caracteres en el propio notebook).'),
                    mira(['Un cliente que no existe, una variable que sobra o un texto en vez de número devuelven **`error`**, no una excepción.', 'Las **instrucciones** del servidor dicen: «si devuelven error, díselo al usuario y no inventes cifras».', 'El caso del tipo (`"abc"`) lo rechaza el **SDK** antes de llamar a la función.']) + callout('Un error con **la lista de valores válidos** (como el de `edad`) deja al LLM corregirse solo en la siguiente llamada.'), '1.1fr .9fr'),
          'Cuando algo sale mal. Cinco entradas malas: un cliente que no existe, un texto en vez de número, una variable que el modelo no conoce, un valor que no es un número y un objeto vacío. En todos los casos el servidor devuelve un mensaje claro en lugar de romperse; el del texto lo rechaza el SDK antes de llamar. Los textos salen recortados porque el propio notebook los recorta a ciento diez caracteres. Un error que incluye la lista de variables válidas permite al LLM corregirse en la siguiente llamada.')

    # ---------------------------------------------------------------- E · Juntos, límites y cierre
    j_datos = bloques_json('01', 24)[0]['servers']
    j_modelo = bloques_json('02', 22)[0]['servers']
    mcp_json = json.dumps({'servers': {**j_datos, **j_modelo}}, indent=2, ensure_ascii=False)
    slide('E', 3, 'Dos servidores juntos', 'qué preguntas responden', 'Con los dos servidores a la vez, un agente combina datos y modelo', f'''
''' + dos_columnas(codigo('.vscode/mcp.json · los dos servidores (cada uno, del notebook 01 y del 02)', mcp_json) + sin_verificar('**nunca se conectó a VS Code ni a Copilot**: el JSON es solo el ejemplo de los notebooks, unidos en un archivo.'),
                    card('Quién responde qué', ['«¿Cuál es el país con más ventas?» → **datos-master** (lo esperable: `ventas_por_pais`; **sin verificar** con un LLM real).', '«¿Cuánto ha comprado el 12369 y qué probabilidad tiene de volver?» → una llamada a **datos-master** (`resumen_cliente`) y otra a **modelo-retencion** (`predecir_cliente`).', '«¿Por qué sale tan baja?» → `por_que`.']) + mira(['Las rutas de `args` cuelgan de la **raíz del repositorio** y `_trabajo/` **solo existe tras ejecutar** los notebooks (`%%writefile`).', 'Para BigQuery: `MCP_BACKEND` a `bigquery` y añadir `GCP_PROJECT` y `BQ_DATASET`.']) + fuente('notebook 01, apartado 11, y notebook 02, apartado 10.'), '1fr 1fr'),
          'Con los dos servidores a la vez, un agente puede contestar preguntas que mezclan datos y modelo, por ejemplo cuánto ha comprado un cliente y qué probabilidad tiene de volver: una llamada a un servidor y otra al otro. El archivo es el ejemplo de los notebooks, con los dos servidores unidos en uno solo. Está sin verificar: no se conectó a VS Code ni a Copilot, y las rutas dependen de que se hayan ejecutado antes los notebooks, porque son ellos los que escriben la carpeta de trabajo.')

    ej1 = ejercicios('01', 24)
    ej2 = ejercicios('02', 22)
    slide('E', 3, 'Ejercicios', 'los de los notebooks', 'Seis ejercicios para hacer tú: tres por servidor', f'''
<div class="grid2">
 <div class="card"><h3>Notebook 01 · el servidor de datos</h3><ol class="ol sm">{''.join(f'<li>{md(e)}</li>' for e in ej1)}</ol></div>
 <div class="card"><h3>Notebook 02 · el servidor del modelo</h3><ol class="ol sm">{''.join(f'<li>{md(e)}</li>' for e in ej2)}</ol></div>
</div>
''' + callout('**El ejercicio 1 del notebook 01 demuestra la capa 3**, la que no depende de nadie: sin vigilancia, SQLite abierto en solo lectura sigue frenando un `UPDATE`. Es la prueba que el notebook **no** hace por ti.', 'margin-top:14px'),
          'Los seis ejercicios, tal cual están en los notebooks. Del servidor de datos: quitar una capa y ver que la siguiente aguanta, añadir una herramienta con parámetros sin pegar texto dentro del SQL, y cambiar el tope de filas. Del servidor del modelo: una herramienta nueva para comparar clientes, un límite para la recencia negativa y una pregunta de diseño sobre las variables al vuelo. Recomiende el primero porque es el que demuestra la defensa en capas.')

    slide('E', 3, 'Qué quedó sin verificar', 'qué se comprobó y qué no', 'Qué se comprobó de verdad y qué quedó sin verificar', f'''
<div class="grid2">
 <div class="card"><h3 class="okc">Comprobado</h3>''' + lista([
        'Los **tres notebooks** se ejecutaron **en local** con SQLite y MLflow; las salidas guardadas son las de estas diapositivas.',
        f'**BigQuery** se probó el **{FECHA_BQ}** en **Cloud Shell**, con la cuenta del curso y un dataset temporal (borrado después): siete llamadas **IGUAL** y el tope de 1 byte.',
        '**Paridad** del MCP del modelo con el modelo a mano (12 clientes, diferencia máxima 0,0) y **rollback** v6 → v1 → v6 sin reiniciar.']) + '''</div>
 <div class="card"><h3 class="malc">Sin verificar o con límites</h3>''' + lista([
        '**Las celdas de BigQuery del notebook 01** nunca se ejecutaron como notebook: salen «saltada». La prueba fue con un script equivalente.',
        '**Conectar los servidores a VS Code/Copilot** y **ejecutar los notebooks en un Codespace**: sin verificar.',
        '**Ningún LLM real** llamó a las herramientas: el cliente del notebook las llama a mano. Cómo elige un LLM, sin dato.',
        '`validar_sql` es una expresión regular, no un analizador. La **sorpresa de la recencia** no se ha investigado, y las 6 versiones **no** son modelos distintos.']) + '''</div>
</div>''',
          'Diapositiva de honestidad. Lo comprobado: los tres notebooks se ejecutaron en local con sus salidas guardadas; BigQuery se probó de verdad en Cloud Shell el veintiséis de noviembre con siete llamadas iguales y el tope de un byte; la paridad y el rollback del servidor del modelo. Lo no comprobado: las celdas de BigQuery como notebook, la conexión a VS Code y Copilot, un Codespace, y cualquier LLM real llamando a las herramientas. Los límites: validar sql es una expresión regular, la sorpresa de la recencia no está investigada y las seis versiones no son modelos distintos.')

    slide('E', 2, 'Resumen', 'el mensaje', 'Un MCP seguro no se fía de una capa; uno de ML sigue al alias, no al archivo', '''
<div class="msg">Un MCP es un <b>contrato vigilado</b>: pocas herramientas, <b>capas que no dependen del LLM</b> y, en el modelo, <b>el alias que manda en MLflow</b>.</div>
<div class="grid4" style="margin-top:18px">
 ''' + kpi('4 capas', '`validar_sql` frenó los **8** ataques; si fallara, **solo lectura** y **50 filas** siguen ahí por diseño (el ejercicio 1 lo prueba)', '') + kpi('7 de 7 IGUAL', 'las siete llamadas dan lo mismo en **SQLite y BigQuery** (prueba en Cloud Shell, ' + FECHA_BQ + ')', '') + kpi('0,0', 'diferencia máxima entre el MCP y el modelo a mano en **12 clientes** (notebook 02)', '') + kpi('v6 → v1 → v6', 'rollback **sin reiniciar** el servidor; misma probabilidad **0,3035** porque son los mismos datos (notebook 02)', '') + '''
</div>
<div style="text-align:center;margin-top:44px;font-size:44px;font-weight:700;color:var(--acento)">¿Preguntas?</div>''',
          'Cierre con un único mensaje: un MCP seguro no se fía de una sola capa y uno de ML sigue al alias y no a un archivo. Las cuatro cifras: cuatro capas de defensa con ocho ataques frenados por la vigilancia; siete de siete llamadas iguales en SQLite y BigQuery, de la prueba de Cloud Shell; diferencia máxima cero coma cero entre el MCP y el modelo a mano en doce clientes; y el rollback de la versión seis a la uno y de vuelta sin reiniciar el servidor.')

    assert sum(int(m) for m in re.findall(r'data-min="(\d+)"', ''.join(SLIDES))) == TOTAL_MIN, 'TOTAL_MIN no coincide con la suma de minutos'


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
  f.innerHTML=`<span>ML e IA · S5 · Extra: MCP en notebooks</span><span><b>${esc(PARTES[s.dataset.part]||'')}</b> · ${i+1} / ${N}</span>`;s.appendChild(f)});
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
CSS = CSS + EXTRA_CSS


def html_completo():
    construir()
    js = JS.replace('__PARTES__', json.dumps(PARTES, ensure_ascii=False))
    partes = ''.join(f'<button class="part" data-p="{k}">{esc(v)}</button>' for k, v in PARTES.items())
    return ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>Extra de S5: MCP en notebooks · ML e IA: de desarrollo a producción</title>\n'
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
            '<noscript>Esta presentación necesita JavaScript. El mismo contenido está en los tres notebooks de esta carpeta.</noscript>\n\n'
            f'<script>{js}</script>\n</body>\n</html>\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--comprobar', action='store_true')
    a = ap.parse_args()
    nuevo = html_completo()
    actual = SALIDA.read_text(encoding='utf-8') if SALIDA.exists() else None
    pendientes = [n for n in CAPTURAS if not (AQUI / 'img' / n).is_file() or n in CAPTURAS_PENDIENTES]
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
    if pendientes:
        print(f'capturas pendientes ({len(pendientes)}): ' + ', '.join(pendientes))


if __name__ == '__main__':
    main()
