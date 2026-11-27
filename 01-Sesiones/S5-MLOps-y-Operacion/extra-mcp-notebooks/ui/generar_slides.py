"""Genera las diapositivas «TIPO LABORATORIO» de la interfaz web del extra de S5 (index_slides.html, junto a este archivo).

Qué cuenta: cómo se prepara, se arranca y se recorre, paso a paso, la interfaz que une los dos servidores MCP (datos y modelo) con un LLM.
Mensaje: la interfaz no inventa nada; cada cifra sale de una herramienta MCP, y lo que un LLM pequeño dice encima hay que comprobarlo.

Las capturas de img/ son REALES: se hicieron con la aplicación en marcha (Windows, Playwright con Chromium propio, 1440 px de ancho, y 390 px
la móvil) y cada una lleva su rótulo y el clic o la entrada que la produce. Las órdenes que se copian se comprueban contra README.md, app.py y
estatico/app.js en pruebas/test_presentacion.py. Lo que no se pudo comprobar lleva la etiqueta «Sin verificar».

El visor (CSS y JavaScript: ← → · O índice · S notas · F pantalla completa · Esc · botón «Copiar todo» · lupa con zoom al clic · pie «x / total»)
es el MISMO que el de los otros extras de S5 (extra-mcp-notebooks/index.html), copiado aquí (no se importa); cambian el pie y el enlace «⌂ Índice».

Uso:  python generar_slides.py              escribe index_slides.html
      python generar_slides.py --comprobar  no escribe; sale con 1 si index_slides.html no está al día
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / 'index_slides.html'
FECHA = '27/11/2026'
PRUEBAS_VERDES = '72'          # nº de pruebas de ui/pruebas que salieron en verde (se rellena con la ejecución real)

PARTES = {'A': 'Qué y cómo', 'B': 'Arrancar', 'C': 'Recorrido', 'D': 'Ejercicios', 'E': 'Pruebas y límites'}
NOMBRES_PARTE = {'A': 'Qué construimos', 'B': 'Preparar y arrancar', 'C': 'Recorrido por la interfaz', 'D': 'Ejercicios guiados', 'E': 'Pruebas y límites'}

# Capturas reales (webp en img/): nombre -> (rótulo = lo que muestra, cómo se produce). UN RÓTULO = UNA IMAGEN.
CAPTURAS = {
    'ui-01-sin-champion.webp': (
        'Interfaz recién abierta con el registro sin alias: píldora ámbar «MCP modelo · sin alias champion», franja «El modelo no tiene alias champion» con el botón «Promover la v6 a champion» y la lista de clientes vacía',
        'Arranca la interfaz con el modelo sin alias champion y abre http://127.0.0.1:8095. No hay que pulsar nada.'),
    'ui-02-dialogo-promover.webp': (
        'Diálogo «Promover la v6 a champion (primer alias)» con dos bloques, «Qué pasa» y «Qué NO pasa», y los botones «Cancelar» y «Promover la v6»',
        'Pestaña Modelo, botón «Promover la v6 a champion» (el de la franja superior hace lo mismo). Todavía no se ha aceptado.'),
    'ui-03-modelo-tras-promover.webp': (
        'Pestaña Modelo tras aceptar: la v6 con la etiqueta @champion, y el cuadro «Qué cambió al mover el alias» con Antes «sin alias» y Ahora «v6» con 30,3 %',
        'En el diálogo anterior, pulsa «Promover la v6». Se espera 1-2 s a que el MCP del modelo cargue la versión.'),
    'ui-04-cliente.webp': (
        'Pestaña Cliente con el 12369: medidor de 30,3 % (tramo «Probabilidad baja»), recomendación de negocio y el gráfico «Qué empuja la cifra» con las 13 variables',
        'Pestaña Cliente, escribe 12369 en «Buscar por nº de cliente…» y pulsa la única fila que sale.'),
    'ui-05-ficha.webp': (
        'Tarjeta «Ficha de datos» del cliente 12369: país Austria, primer movimiento 2010-03-08, último 2010-10-22, 3 facturas, 0 cancelaciones, monto 1511,15 y la tabla de sus tres facturas',
        'Es la parte de abajo de la misma pestaña Cliente (con el 12369 elegido): desplázate hacia abajo.'),
    'ui-06-ysi.webp': (
        'Pestaña ¿Y si…? con el cliente 12369: «Días desde la última compra» cambiado de 413 a 30 y el medidor en 18,4 % con «-11,9 puntos respecto al original (30,3 %)»',
        'Pestaña ¿Y si…?, cliente de partida 12369, escribe 30 en la casilla de «Días desde la última compra» (recencia_dias) y espera un instante.'),
    'ui-07-pregunta-sin-herramientas.webp': (
        'Pestaña Pregunta con qwen2.5:0.5b: a «¿Qué país vende más?» y a «¿Qué probabilidad tiene el cliente 12369 y por qué?» responde pidiendo el ID del cliente, sin ningún chip de herramienta',
        'Pestaña Pregunta, botón de sugerencia «¿Qué país vende más?» y, a continuación, «¿Qué probabilidad tiene el cliente 12369 y por qué?» en la misma conversación.'),
    'ui-10-pregunta-predecir.webp': (
        'Pestaña Pregunta: tras «Usa la herramienta predecir_cliente con cliente_id 12369», la respuesta del LLM (con frases sin sentido como «Esta variable tiene un valor de 6») y, debajo, la llamada desplegada: predecir_cliente, correcta, 164 ms, probabilidad 0.3035',
        'Pestaña Pregunta, «Nueva conversación», escribe la orden de la diapositiva y pulsa «Preguntar»; despliega la tarjeta de la herramienta.'),
    'ui-08-pregunta-ventas.webp': (
        'Pestaña Pregunta: tras «Usa la herramienta ventas_por_pais y dime qué país vende más», el LLM dice Reino Unido «en los últimos 90 días»; debajo, la llamada ventas_por_pais con 1140 facturas y 133 clientes y sin ningún periodo',
        'Pestaña Pregunta, «Nueva conversación», escribe esa orden y pulsa «Preguntar»; despliega la tarjeta de la herramienta.'),
    'ui-09-pregunta-sql-rechazado.webp': (
        'Pestaña Pregunta: a «Compara los clientes 12369 y 12425» el LLM escribe un SELECT sobre la tabla «clientes», consulta_sql la rechaza («rechazada_por: vigilancia del SQL») y el LLM lo cuenta',
        'Pestaña Pregunta, «Nueva conversación» y sugerencia «Compara los clientes 12369 y 12425»; despliega la tarjeta de la herramienta.'),
    'ui-11-explorador-herramienta.webp': (
        'Pestaña Explorador MCP: lista de las 7 herramientas de mcp-datos-master y las 4 de mcp-modelo-retencion, y el formulario de resumen_cliente con cliente_id 12369 ya ejecutado («Correcta · 10 ms»)',
        'Pestaña Explorador MCP, herramienta resumen_cliente de la lista, deja cliente_id en 12369 y pulsa «Ejecutar».'),
    'ui-12-ataque-update.webp': (
        'Tarjeta «Qué capa lo frena» tras el ataque UPDATE: «Frenada por la capa 2: Vigilancia del SQL», con la capa 2 resaltada, las otras tres capas sin resaltar y el JSON de error con «rechazada_por»',
        'Pestaña Explorador MCP, en «Ataques de ejemplo» pulsa «UPDATE».'),
    'ui-13-modelo-promover-v5.webp': (
        'Pestaña Modelo tras promover la v5 con la v6 como champion anterior: Antes v6 (30,3 %), Ahora v5 (30,3 %), y el botón «Volver a la v6»',
        'Pestaña Modelo, con la v6 como champion: botón «Promover v5» de la fila v5 y «Promover la v5» en el diálogo.'),
    'ui-14-modelo-volver.webp': (
        'Pestaña Modelo tras «Volver a la v6»: @champion de nuevo en la v6, Antes v5 y Ahora v6, ambas con 30,3 %, y el botón «Volver a la anterior (no hay)» desactivado',
        'En la captura anterior, pulsa «Volver a la v6» y acepta el diálogo.'),
    'ui-15-traza.webp': (
        'Panel lateral «Traza MCP» (recorte de 360 px de ancho): una fila por llamada, con el servidor, la herramienta, los ms, «ok» o «error» y el principio del resultado',
        'Botón «Traza MCP» de la cabecera (se abre solo en pantallas anchas). La captura es tras pulsar los ataques de ejemplo: hay filas «error».'),
    'ui-16-lote.webp': (
        'Pestaña Lote sin Airflow: tarjeta «Airflow» con la etiqueta roja «Sin conexión», AIRFLOW_URL «(sin definir)», el aviso «No hay AIRFLOW_URL» y la explicación de cómo arrancar Airflow; a la derecha «Estado del run» vacío',
        'Pestaña Lote, sin definir AIRFLOW_URL antes de arrancar la interfaz.'),
    'ui-17-movil.webp': (
        'Vista de móvil (390 px de ancho): cabecera con las tres píldoras en columna, pestañas con desplazamiento lateral (la última se corta) y la lista de clientes con sus probabilidades (recorte de la parte alta; el cliente 12369 aparece seleccionado)',
        'Abre la interfaz con la ventana a 390 px (en el navegador: F12, vista de dispositivo) y pulsa el primer cliente de la lista.'),
}
SIN_VERIFICAR_OK = {'Portada', 'Variables de entorno', 'Arrancar en Codespace o Linux', 'Pregunta: un LLM pequeño sin herramientas', 'Pestaña Lote', 'Qué no está verificado'}


def esc(t):
    return html.escape(t, quote=True)


def md(t):
    """`código` y **negrita** a HTML (sobre texto ya seguro)."""
    t = esc(t)
    t = re.sub(r'`([^`]+)`', r'<span class="mono">\1</span>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', t)
    return re.sub(r'(?<![\w*])\*([^*\s][^*]*)\*(?![\w*])', r'<i>\1</i>', t)


LUPA = '<svg viewBox="0 0 20 20" width="14" height="14" aria-hidden="true"><circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12.5 12.5 L18 18" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>'

ORDENES = {}      # texto copiable -> lista de trozos que deben existir en README.md / app.py / app.js / README de la sesión (lo vigila la prueba)


def term(titulo, lineas, necesita=None, prompt=False):
    """Terminal con una orden por línea y su botón ⧉. Las líneas que empiezan por # son comentarios (no se copian).
    necesita: {línea: [trozos]} que deben aparecer en las fuentes; por defecto, la propia línea. prompt=True: texto que se escribe en la interfaz."""
    necesita = necesita or {}
    filas = []
    for l in lineas:
        if l.startswith('#'):
            filas.append(f'<div class="tln c">{esc(l)}</div>')
        else:
            ORDENES[l] = necesita.get(l, [l])
            sig = '›' if prompt else '$'
            filas.append(f'<div class="tln"><span class="ps">{sig}</span> <code>{esc(l)}</code><button class="cp" data-t="{esc(l)}" title="Copiar">⧉</button></div>')
    todo = '\n'.join(l for l in lineas if not l.startswith('#'))
    reales = [l for l in lineas if not l.startswith('#')]
    if len(reales) > 1:
        ORDENES[todo] = [t for l in reales for t in ORDENES[l]]
    return (f'<div class="term"><div class="bar"><em>{esc(titulo)}</em><button class="cp cpall" data-t="{esc(todo)}">Copiar todo</button></div>'
            f'<div class="tls">{"".join(filas)}</div></div>')


def salida(titulo, texto):
    return f'<div class="realbox"><div class="rk">{esc(titulo)}</div><pre>{esc(texto)}</pre></div>'


def cap(nombre, alto=None):
    """Una captura real (clic o lupa = ampliar) con su rótulo y cómo se produce, o el recuadro «Captura pendiente» si no está en img/."""
    rotulo, como = CAPTURAS[nombre]
    estilo = f' style="max-height:{alto}px"' if alto else ''
    extra = f'<br><span class="nota">Cómo se produce: {md(como)}</span>'
    if (AQUI / 'img' / nombre).is_file():
        return (f'<figure class="cap" data-img="{nombre}"><button class="zoom" data-src="img/{nombre}" data-alt="{esc(rotulo)}" title="Ampliar (Esc cierra)">'
                f'<img src="img/{nombre}" alt="{esc(rotulo)}"{estilo}><span class="lupa">{LUPA} Ampliar</span></button>'
                f'<figcaption><span class="tag ok">Captura real</span> {esc(rotulo)}{extra}</figcaption></figure>')
    return (f'<figure class="cap" data-img="{nombre}"><div class="pend"><b>Captura pendiente</b><span class="mono">img/{nombre}</span>'
            f'<span>{esc(rotulo)}</span></div><figcaption><span class="tag warn">Pendiente</span> {esc(rotulo)}{extra}</figcaption></figure>')


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
GRANDES = set()


def slide(parte, minutos, titulo, kick, h1, cuerpo, notas):
    _N[parte] = _N.get(parte, 0) + 1
    n = list(PARTES).index(parte) + 1
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


def svg_arquitectura():
    """Navegador - FastAPI - dos servidores MCP por stdio - SQLite/BigQuery y modelo; el LLM aparte."""
    g = ['<defs><marker id="fa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#0b5cad"/></marker></defs>']
    g.append(_caja(6, 96, 190, ['Navegador', 'http://127.0.0.1:8095', 'HTML y JS, sin CDN'], 'nodo', 96))
    g.append(_caja(300, 70, 230, ['FastAPI · app.py', 'uvicorn en el puerto 8095', 'puente MCP, traza y chat'], 'nodo puerta', 148))
    g.append(_caja(650, 6, 200, ['mcp-datos-master', '7 herramientas', 'proceso hijo, stdio'], 'nodo', 96))
    g.append(_caja(650, 150, 200, ['mcp-modelo-retencion', '4 herramientas', 'proceso hijo, stdio'], 'nodo', 96))
    g.append(_caja(900, 6, 196, ['SQLite curso.db', 'o BigQuery', '(solo lectura)'], 'nodo ok', 96))
    g.append(_caja(900, 150, 196, ['Modelo en MLflow', 'retencion-90d', 'alias @champion'], 'nodo ok', 96))
    g.append(_caja(300, 268, 230, ['LLM aparte', 'Ollama u otro servidor', 'en /v1/chat/completions'], 'nodo mal', 96))
    g.append('<path d="M199 144 L296 144" class="fl" marker-end="url(#fa)"/><path d="M296 160 L199 160" class="fl" marker-end="url(#fa)"/>')
    g.append('<text x="248" y="134" class="t2">HTTP</text>')
    g.append('<path d="M533 120 L646 56" class="fl" marker-end="url(#fa)"/><path d="M533 170 L646 196" class="fl" marker-end="url(#fa)"/>')
    g.append('<path d="M853 54 L896 54" class="fl" marker-end="url(#fa)"/><path d="M853 198 L896 198" class="fl" marker-end="url(#fa)"/>')
    g.append('<path d="M415 222 L415 264" class="fl dis" marker-end="url(#fa)"/><text x="520" y="248" class="t2">el LLM pide herramientas; las ejecuta FastAPI</text>')
    return ('<svg viewBox="0 0 1100 370" style="max-height:300px" role="img" aria-label="El navegador habla por HTTP con FastAPI (app.py). FastAPI lanza como procesos hijos, por stdio, '
            'los dos servidores MCP: el de datos, que lee SQLite o BigQuery, y el del modelo, que carga el alias champion de MLflow. El LLM es un servidor aparte al que FastAPI llama '
            'por /v1/chat/completions y cuyas peticiones de herramienta ejecuta FastAPI">' + ''.join(g) + '</svg>')


# ------------------------------------------------------------------------------------------------------------------------
# Contenido
# ------------------------------------------------------------------------------------------------------------------------
CD = r'cd 01-Sesiones\S5-MLOps-y-Operacion\extra-mcp-notebooks\ui'
UVI = 'python -m uvicorn app:app --port 8095'

ATAQUES = [
    ('DROP', 'DROP TABLE master_clientes', 'Solo se admiten consultas que empiecen por SELECT (o WITH).'),
    ('UPDATE', "UPDATE master_clientes SET pais = 'Nowhere'", 'Solo se admiten consultas que empiecen por SELECT (o WITH).'),
    ('Varias sentencias', 'SELECT 1; DELETE FROM master_clientes', 'Solo se admite una sentencia.'),
    ('Comentario', 'SELECT cliente_id FROM master_clientes -- ver todo', 'No se admiten comentarios en la consulta.'),
    ('Tabla fs_produccion', 'SELECT * FROM fs_produccion', 'La tabla «fs_produccion» no está permitida.'),
    ('sqlite_master', 'SELECT name FROM sqlite_master', 'La tabla «sqlite_master» no está permitida.'),
    ('Ruta completa', 'SELECT * FROM main.master_clientes', 'Escribe solo el nombre de la tabla, sin proyecto ni dataset.'),
    ('Coma entre tablas', 'SELECT a.cliente_id FROM master_clientes a, master_facturas b', 'No se admiten listas de tablas separadas por comas: usa JOIN.'),
]


def construir():
    SLIDES.clear()
    _N.clear()
    ORDENES.clear()

    # ---------------------------------------------------------------- A · Qué y cómo
    slide('A', 2, 'Portada', 'ML e IA: de desarrollo a producción · S5 · extra', 'Una interfaz web que une dos servidores MCP y un LLM', f'''
<div class="cover">
 <p class="sub">Laboratorio paso a paso: <b>preparas</b> el entorno, <b>arrancas</b> la interfaz (<span class="mono">http://127.0.0.1:8095</span>), la <b>recorres pestaña a pestaña</b> con capturas reales y la <b>pruebas</b>. Lo que ves sale de las herramientas MCP; el LLM solo conversa.</p>
 <div class="chips"><span class="tag">FastAPI</span><span class="tag">2 servidores MCP por stdio</span><span class="tag">SQLite o BigQuery</span><span class="tag">Modelo @champion</span><span class="tag">LLM aparte (Ollama)</span><span class="tag">6 pestañas</span></div>
 <div class="grid3" style="margin-top:20px">
  {card('Qué vas a hacer', ['Arrancarla en **Windows** (cmd y PowerShell) o en un **Codespace**.', 'Promover una versión del modelo y ver cómo cambia lo que responde.', 'Preguntar a un LLM pequeño y **comprobar** sus herramientas en la traza.'])}
  {card('Cómo se sigue', ['**← →** avanzan · **O** índice · **S** notas del profesor · **F** pantalla completa.', 'Cada orden tiene su botón **⧉**; cada captura se amplía con la **lupa** (Esc la cierra).', 'Cada captura dice qué clic o qué entrada la produce.'])}
  {card('Honestidad', ['Las capturas son **reales**, hechas en Windows con `qwen2.5:0.5b`.', 'Lo que no se pudo probar (Codespace, Linux, BigQuery desde la interfaz, un LLM mayor) lleva **«sin verificar»**.'])}
 </div>
</div>''',
          'Portada del laboratorio de la interfaz web del extra de la sesión 5. Es una página local que arranca los dos servidores MCP de la carpeta fuentes, el de datos y el del modelo, y los une con un LLM. El alumnado la replica paso a paso: prepara el entorno, la arranca, recorre cada pestaña y la prueba. Todas las capturas son reales y llevan escrito el clic que las produce. Lo que no se pudo probar está marcado como sin verificar.')

    slide('A', 2, 'Qué construimos y qué necesitas', 'requisitos', 'Una página local, dos servidores MCP y un modelo registrado: esto es lo que hace falta', '<div class="card">' + tabla(['Qué', 'Para qué', 'Cómo lo compruebas'], [
        ['**Entorno** `env-ia-mlops`', 'Trae `fastapi`, `uvicorn`, `httpx` y `mlflow`', 'Actívalo antes de arrancar (`python -m uvicorn` lo encuentra)'],
        ['**`curso.db`** de `04-Proyecto-Base`', 'Los datos que consulta el MCP de datos', '`python -m ia_mlops.pipeline` y `python -m ia_mlops.explotacion` (desde S1)'],
        ['**Modelo `retencion-90d`** registrado en MLflow', 'Lo carga el MCP del modelo por el alias `@champion`', 'Son 6 versiones; la interfaz avisa si no hay alias'],
        ['**`mcp` 1.30.0**', 'SDK de Model Context Protocol, fijado a la 1.x', '`mcp==1.30.0` en `requisitos-extra-mcp.txt`'],
        ['Un **Ollama** (opcional)', 'El LLM de la pestaña Pregunta', 'Sin él, solo esa pestaña avisa; el resto funciona']]) + '</div>'
          + '<div class="grid2" style="margin-top:12px">'
          + term('Solo si faltan los datos (desde 04-Proyecto-Base)', ['python -m ia_mlops.pipeline', 'python -m ia_mlops.explotacion'])
          + callout('La probabilidad es la de **volver a comprar en 90 días**: alta = buena noticia, no es riesgo de abandono.', 'align-self:center')
          + '</div>' + fuente('`ui/README.md` (Arrancar) y `README.md` del extra (Cómo se usa); `requisitos-extra-mcp.txt`.'),
          'Qué se necesita antes de empezar. El entorno del curso, env-ia-mlops, ya trae fastapi, uvicorn, httpx y mlflow. Hacen falta los datos de la sesión uno, el curso punto db y la tabla fs produccion, y el modelo retencion noventa d registrado en MLflow, con seis versiones. El SDK de MCP está fijado a la versión uno punto treinta. Un Ollama es opcional: sin él solo la pestaña Pregunta avisa. Recuerde que la probabilidad es la de volver a comprar: alta es buena noticia.')

    slide('A', 3, 'Arquitectura', 'quién habla con quién', 'El navegador solo habla con FastAPI; FastAPI lanza los dos servidores MCP y llama al LLM aparte', f'''
<div class="card">{svg_arquitectura()}</div>
<div class="grid3" style="margin-top:10px">
 {card('Un solo proceso web', ['`app.py` arranca los dos servidores de `fuentes/` como **procesos hijos** (stdio) y guarda **toda llamada** en una traza.', 'Solo escucha en `127.0.0.1`.'])}
 {card('Los datos y el modelo', ['`mcp-datos-master`: 7 herramientas, SQLite o BigQuery.', '`mcp-modelo-retencion`: 4 herramientas; carga lo que mande `@champion`.'])}
 {card('El LLM', ['Es **otro servidor** (`/v1/chat/completions`): la interfaz le ofrece las herramientas y **ejecuta** las que pide.', 'Sin LLM, el resto funciona.'])}
</div>''' + fuente('`ui/app.py` (docstring y clase `Puente`) y `ui/README.md`; recuento de herramientas: pestaña Explorador MCP (captura 11).'),
          'La arquitectura. El navegador solo habla por HTTP con FastAPI, el archivo app punto py. FastAPI arranca como procesos hijos los dos servidores MCP, por stdio: el de datos, con siete herramientas, que lee SQLite o BigQuery, y el del modelo, con cuatro, que carga el modelo registrado en MLflow por el alias champion. El LLM va aparte: es cualquier servidor con la API de chat completions; es FastAPI quien le ofrece las herramientas y quien las ejecuta cuando las pide. Toda llamada queda en una traza.')

    slide('A', 2, 'Qué hace cada pestaña', 'seis pestañas', 'Seis pestañas: cinco usan las herramientas MCP y una lanza el lote por Airflow', '<div class="card">' + tabla(['Pestaña', 'Qué hace', 'Qué herramientas MCP usa'], [
        ['**Cliente**', 'Lista, medidor, qué empuja la cifra y ficha de datos', '`predecir_cliente`, `por_que`, `resumen_cliente`, `ultimas_facturas`'],
        ['**¿Y si…?**', '13 deslizadores y la probabilidad en vivo', '`predecir_variables`'],
        ['**Pregunta**', 'Chat con el LLM (máximo 5 pasos por pregunta)', 'Las que pida el LLM'],
        ['**Explorador MCP**', 'Formulario por herramienta y «SQL con vigilancia»', 'Las 11, y `consulta_sql` con 8 ataques de ejemplo'],
        ['**Modelo**', 'Versiones, AUC, promover y volver', '`modelo_en_uso` y `predecir_cliente` (antes y después); el alias lo mueve `app.py` en MLflow'],
        ['**Lote**', 'Lanza el DAG `retencion_lote`', 'Ninguna: usa la API REST de Airflow (otro extra)']]) + '</div>'
          + '<div class="grid2" style="margin-top:12px">' + card('mcp-datos-master (7)', ['`listar_tablas`, `describir_tabla`, `resumen_cliente`, `ultimas_facturas`', '`ventas_por_pais`, `top_productos` y `consulta_sql` (SQL libre, vigilado)'])
          + card('mcp-modelo-retencion (4)', ['`predecir_cliente`, `predecir_variables`', '`por_que` (qué empuja la cifra) y `modelo_en_uso` (qué versión responde)']) + '</div>'
          + fuente('`ui/README.md` (tabla de pestañas), lista de herramientas de la captura 11 y trazas de las capturas 04, 06 y 13.'),
          'Qué hace cada pestaña y con qué herramientas MCP. Cliente usa predecir cliente, por que, resumen cliente y ultimas facturas; lo vimos en la traza. La pestaña Y si usa predecir variables. Pregunta usa las que pida el LLM, con un máximo de cinco pasos. El Explorador permite ejecutar cada una de las once a mano y probar ocho ataques de SQL. Modelo lee el registro y mueve el alias, que no es una herramienta MCP sino una operación de la aplicación sobre MLflow. Lote no usa MCP: lanza un DAG de Airflow y pertenece al otro extra.')

    # ---------------------------------------------------------------- B · Arrancar
    slide('B', 3, 'Arrancar en Windows', 'cmd y PowerShell', 'Dos órdenes: entrar en la carpeta ui y lanzar uvicorn', dos_columnas(
        term('Windows · cmd', [CD, UVI]) + term('Windows · PowerShell (igual)', [CD, UVI]) + term('Alternativa', ['python app.py']),
        salida('Salida esperada (uvicorn, la prueba se hizo en el puerto 8195)', 'INFO:     Started server process [29404]\nINFO:     Waiting for application startup.\nINFO:     Application startup complete.\nINFO:     Uvicorn running on http://127.0.0.1:8095 (Press CTRL+C to quit)')
        + mira(['Tarda **unos 10-20 s** en responder: arranca los dos servidores MCP.', 'Abre **http://127.0.0.1:8095**: sale la página «Retail · MCP y LLM» con tres píldoras de estado.', '**Ctrl+C** en la terminal la para.'])
        + si_falla(['«No module named …»: no tienes activado `env-ia-mlops`.', 'El puerto 8095 está ocupado por otro programa: cambia `--port` (o usa `CURSO_UI_PUERTO` con `python app.py`).']), '1fr 1fr')
          + fuente('`ui/README.md` (Arrancar) y salida real de uvicorn en la prueba del 27/11/2026.'),
          'Arrancar en Windows. En cmd y en PowerShell son las mismas dos órdenes: entrar en la carpeta ui del extra y lanzar uvicorn con la aplicación app en el puerto ocho mil noventa y cinco. También vale python app punto py. La salida de uvicorn es la que se ve; en la prueba se usó el puerto ocho mil ciento noventa y cinco, por eso el número del proceso es de esa ejecución. Tarda unos diez o veinte segundos porque arranca los dos servidores. Después se abre el navegador en ciento veintisiete punto cero punto cero punto uno.')

    slide('B', 2, 'Variables de entorno', 'todas opcionales', 'Todas las variables son opcionales: se ponen antes de arrancar, igual que en cualquier otra aplicación', dos_columnas(
        '<div class="card">' + tabla(['Variable', 'Para qué', 'Por defecto'], [
            ['`CURSO_LLM_URL`', 'Base del LLM (OpenAI-compatible)', '`http://127.0.0.1:11434/v1`'],
            ['`CURSO_LLM_MODELO`', 'Nombre del modelo', '`qwen2.5:0.5b`'],
            ['`CURSO_UI_HOSTS`', 'Hosts extra admitidos (Codespace)', 'solo local'],
            ['`CURSO_UI_PUERTO`', 'Puerto con `python app.py`', '`8095`'],
            ['`MCP_PROYECTO`, `CURSO_DB`, `CURSO_MLFLOW_URI`', 'Carpetas de datos y registro', 'las de `04-Proyecto-Base`'],
            ['`GCP_PROJECT`, `BQ_DATASET`', 'Solo modo BigQuery', '`curso_master` el dataset']]) + '</div>'
        + sin_verificar('BigQuery desde la interfaz solo se probó con un conector falso. `MCP_BACKEND` no se pone a mano: la interfaz la fija al pulsar SQLite o BigQuery.')
        + fuente('`ui/app.py` (docstring y líneas de `os.environ`) y `ui/README.md`.'),
        term('cmd', ['set CURSO_LLM_URL=http://127.0.0.1:11434/v1', 'set CURSO_LLM_MODELO=qwen2.5:0.5b'],
             {'set CURSO_LLM_URL=http://127.0.0.1:11434/v1': ['CURSO_LLM_URL', 'http://127.0.0.1:11434/v1'], 'set CURSO_LLM_MODELO=qwen2.5:0.5b': ['CURSO_LLM_MODELO', 'qwen2.5:0.5b']})
        + term('PowerShell', ['$env:CURSO_LLM_URL = "http://127.0.0.1:11434/v1"', '$env:CURSO_LLM_MODELO = "qwen2.5:0.5b"'],
               {'$env:CURSO_LLM_URL = "http://127.0.0.1:11434/v1"': ['CURSO_LLM_URL', 'http://127.0.0.1:11434/v1'], '$env:CURSO_LLM_MODELO = "qwen2.5:0.5b"': ['CURSO_LLM_MODELO', 'qwen2.5:0.5b']})
        + term('BigQuery (opcional; en cmd)', ['gcloud auth application-default login', 'set GCP_PROJECT=TU_PROYECTO'],
               {'set GCP_PROJECT=TU_PROYECTO': ['GCP_PROJECT', 'TU_PROYECTO']})
        + callout('Los valores de arriba son los **de por defecto**: ponerlos no cambia nada. Sirven de plantilla si tu Ollama está en otro puerto.', 'font-size:14px'), '1.15fr .85fr'),
          'Las variables de entorno. Todas son opcionales. Las del LLM son la dirección y el nombre del modelo; los valores que se muestran son los de por defecto, así que ponerlos no cambia nada, pero sirven de plantilla. Para Codespace hace falta CURSO UI HOSTS. Para BigQuery hacen falta GCP PROJECT y credenciales, y no se debe usar el proyecto del trabajo. La variable MCP BACKEND no se toca a mano: la interfaz la fija al pulsar SQLite o BigQuery. Sobre BigQuery desde la interfaz: sin verificar con un proyecto real.')

    slide('B', 2, 'El LLM: Ollama', 'opcional', 'El LLM es otro servidor: sin él solo la pestaña Pregunta avisa', dos_columnas(
        term('Arrancar Ollama y descargar el modelo', ['ollama serve', 'ollama pull qwen2.5:0.5b'])
        + term('Comprobar que responde (la interfaz hace esta misma consulta)', ['curl http://127.0.0.1:11434/v1/models'], {'curl http://127.0.0.1:11434/v1/models': ['http://127.0.0.1:11434/v1', '/models']})
        + callout('El curso usa **Qwen2.5-3B-Instruct Q4** en el puerto 11435: cámbialo en el botón «Ajustes del LLM» o con `CURSO_LLM_URL`.', 'font-size:14px'),
        salida('Respuesta real (recortada) de http://127.0.0.1:11434/v1/models', '{"object":"list","data":[{"id":"qwen2.5:0.5b","object":"model", ...}]}')
        + mira(['La píldora de la cabecera pone **«LLM · qwen2.5:0.5b · responde»** (verde).', '«no responde» (ámbar): falta `ollama serve`. «modelo no descargado»: falta `ollama pull`.'])
        + callout('`qwen2.5:0.5b` es **débil con herramientas**: se equivocará. Lo veremos en las capturas.', 'font-size:14px'), '1fr 1fr')
          + fuente('`ui/README.md` (LLM) y `ui/app.py` (`comprobar_llm`, `ayuda_llm`); respuesta de `/v1/models` en la prueba del 27/11/2026.'),
          'El LLM. Es cualquier servidor con la API de chat completions y herramientas. Con Ollama son dos órdenes: ollama serve y ollama pull del modelo. La interfaz consulta la lista de modelos y pinta la píldora: verde si responde, ámbar si no responde o si falta el modelo. El curso usa Qwen dos punto cinco de tres mil millones de parámetros en el puerto once mil cuatrocientos treinta y cinco, que se cambia en Ajustes. El modelo pequeño de quinientos millones de parámetros es muy débil con herramientas y se va a equivocar; es a propósito para enseñarlo.')

    slide('B', 2, 'Arrancar en Codespace o Linux', 'host extra', 'En un Codespace la página llega con otro nombre de host: hay que admitirlo antes de arrancar', dos_columnas(
        term('Codespace / Linux (bash), desde la carpeta ui', ['export CURSO_UI_HOSTS="*.app.github.dev"', UVI])
        + lista(['Lo mismo que en Windows, **desde la carpeta `ui`**.', 'Abre el puerto **8095** reenviado (pestaña «Puertos»).', 'Sin esa variable, la interfaz rechaza el host con **400** (protección contra «DNS rebinding»).'])
        + sin_verificar('Codespace y Linux **no se han probado**: solo Windows.'),
        card('Por qué hace falta', ['`app.py` solo atiende `127.0.0.1`, `localhost` y los hosts de `CURSO_UI_HOSTS`.', 'En Windows el 400 con otro host **sí está probado** (`test_solo_acepta_hosts_locales`).', 'Lo que no está probado es el reenvío del puerto en un Codespace.'])
        + si_falla(['La página no abre o da 400: revisa `CURSO_UI_HOSTS` y que el puerto 8095 esté reenviado.', 'Ollama no existe en un Codespace sin instalarlo: la pestaña Pregunta avisará y el resto funciona.']), '1fr 1fr')
          + fuente('`ui/README.md` (Codespace / Linux) y `ui/pruebas/test_interfaz.py`.'),
          'Codespace o Linux. Es lo mismo desde la carpeta ui, con una variable más: CURSO UI HOSTS con el patrón de hosts de GitHub. Sin ella la aplicación rechaza con un cuatrocientos las peticiones con otro nombre de host, que es una defensa contra el DNS rebinding; esa defensa sí está probada en Windows. Lo que no está probado es el uso real en un Codespace, ni en Linux. Si alguien lo prueba, que lo cuente.')

    slide('B', 2, 'Si falla al arrancar', 'síntoma, causa, solución', 'Cuatro fallos típicos y qué mira la propia interfaz', '<div class="card">' + tabla(['Qué ves', 'Causa', 'Qué haces'], [
        ['Píldora **«MCP modelo · sin alias champion»** y clientes vacíos', 'El registro no tiene `@champion`', 'Botón «Promover la v6 a champion» (diapositivas siguientes)'],
        ['Píldora **«LLM · no responde»**', 'No hay Ollama en `127.0.0.1:11434`', '`ollama serve` o cambia la URL en «Ajustes del LLM»'],
        ['Píldora **«LLM · modelo no descargado»**', 'Ollama responde, pero sin ese modelo', '`ollama pull qwen2.5:0.5b`'],
        ['La página no sale o la terminal da error', 'Falta `curso.db`, el modelo o un paquete', 'Repite los pasos de requisitos; mira la terminal donde corre uvicorn'],
        ['Error 400 en la página', 'Host no admitido', '`CURSO_UI_HOSTS` (Codespace)']]) + '</div>'
          + callout('Los avisos de la interfaz **dicen qué hacer**: léelos antes de buscar fuera. Sin LLM no hay reglas que finjan inteligencia: la pestaña Pregunta lo dice y no responde.')
          + fuente('`ui/app.py` (`ayuda_llm`, `comprobar_llm`, `estado_registro`) y `ui/README.md`.'),
          'Los fallos típicos. Los avisos de la propia interfaz dicen qué hacer: sin alias champion, el botón de promover; LLM que no responde, ollama serve; modelo no descargado, ollama pull. Si la página ni sale, hay que mirar la terminal donde corre uvicorn: lo más probable es que falte curso punto db, el modelo registrado o algún paquete. Un cuatrocientos es el host no admitido. No hay reglas que finjan inteligencia: sin LLM, la pestaña Pregunta lo dice.')

    # ---------------------------------------------------------------- C · Recorrido
    slide('C', 3, 'Primer arranque: sin alias champion', 'píldoras y aviso', 'Con el registro sin alias, la interfaz avisa y no promueve nada por su cuenta', dos_columnas(
        mira(['La píldora **«MCP modelo · sin alias champion»** es ámbar: el servidor vive, pero no puede predecir.', 'La franja amarilla lo explica y ofrece **«Promover la v6 a champion»**.', 'La lista de clientes dice «Sin clientes que mostrar todavía»: **no hay cifras sin modelo**.', '**«MCP datos · motor sqlite»** y **«LLM · responde»** salen en verde: lo demás funciona.'])
        + callout('Es **la situación de partida** del laboratorio: el registro del curso no trae alias. Ninguna versión se promueve sola.', 'font-size:14.5px'),
        cap('ui-01-sin-champion.webp', 400), '.75fr 1.25fr')
          + fuente('captura real de la interfaz y `ui/README.md` («Si el modelo no tiene alias `champion`…»).'),
          'Primera vista cuando el registro no tiene alias champion. La píldora del modelo sale en ámbar con el texto sin alias champion, y una franja amarilla explica que sin alias no se puede predecir y que ninguna versión se promueve sola. El botón ofrece promover la versión seis. La lista de clientes está vacía porque sin modelo no hay probabilidades. Los servidores de datos y el LLM están en verde.')

    slide('C', 3, 'Promover la v6', 'diálogo propio', 'Promover pide confirmación y dice qué pasa y, sobre todo, qué NO pasa', dos_columnas(
        cap('ui-02-dialogo-promover.webp', 330),
        cap('ui-03-modelo-tras-promover.webp', 330), '1fr 1fr')
          + '<div class="grid2">' + callout('**Qué pasa:** se crea `@champion` en la v6 y el MCP del modelo **recarga solo** en su siguiente llamada.', '') + '' + callout('**Qué NO pasa:** no se borra ni se reentrena nada, y la API Docker ya desplegada **no cambia**. **Esto escribe en el registro de MLflow.**', 'border-color:#c9a65e;background:#fdf6e9') + '</div>'
          + fuente('captura 02 (texto del diálogo) y captura 03 (cuadro «Qué cambió al mover el alias»).'),
          'Promover la versión seis. El diálogo es propio, no el nativo del navegador, y explica qué pasa y qué no pasa. Se crea el alias champion en la versión seis, el servidor del modelo lo detecta en su siguiente llamada y recarga solo, sin reiniciarse. No se borra ninguna versión, no se reentrena nada y la API de Docker que ya esté desplegada no cambia porque copió su modelo al construirse. Esto escribe en el registro de MLflow de cero cuatro proyecto base: quien lo haga en su máquina deja el alias puesto.')

    slide('C', 2, 'Pestaña Cliente', 'medidor, qué empuja la cifra y ficha', 'Cada bloque dice qué servidor y qué herramienta lo produjo', dos_columnas(
        mira(['El **medidor** da la probabilidad de volver a comprar: **30,3 %**, tramo «baja».', '**«Qué empuja la cifra»** (`por_que`): barras azules suben la probabilidad, naranjas la bajan.', '**«Ficha de datos»** (`resumen_cliente`, `ultimas_facturas`): país, fechas, facturas y monto.', 'Etiqueta sobre cada tarjeta: **`mcp-modelo-retencion · predecir_cliente`**, etc.'])
        + cap('ui-05-ficha.webp', 150), cap('ui-04-cliente.webp', 430), '.85fr 1.15fr')
          + fuente('capturas 04 y 05 (cliente 12369, modelo v6@champion).'),
          'La pestaña Cliente con el cliente doce mil trescientos sesenta y nueve. El medidor muestra treinta coma tres por ciento de probabilidad de volver a comprar en noventa días, tramo bajo. El gráfico que empuja la cifra sale de la herramienta por que, con los pesos en escala logit: azul sube, naranja baja. Dice qué empuja la cifra, no por qué compra el cliente: no es causal. La ficha de datos sale del servidor de datos. Cada tarjeta lleva una etiqueta con el servidor y la herramienta que la produjo, para no mezclar.')

    slide('C', 3, 'Pestaña ¿Y si…?', 'deslizadores y delta', 'Mover una variable da otra cifra, pero no un cliente real ni una causa', dos_columnas(
        mira(['**Cliente 12369**: «Días desde la última compra» baja de **413 a 30**.', 'La probabilidad pasa de **30,3 %** a **18,4 %**: **−11,9 puntos** respecto al original (la sombra del medidor).', 'Cada cambio llama a `predecir_variables`; el tramo y la recomendación se recalculan.'])
        + callout('**Advertencia honesta:** en este modelo la probabilidad **sube con la recencia** (más días sin comprar, más probabilidad), contra la intuición; **no se ha investigado por qué** y la relación no es causal. Las variables van juntas: una sola no es un cliente real.', 'font-size:14px'),
        cap('ui-06-ysi.webp', 430), '.8fr 1.2fr')
          + fuente('captura 06 (cuadro «Léelo con cuidado» de la propia pestaña) y `ui/README.md`.'),
          'La pestaña Y si. Se parte de un cliente real y se mueven las trece variables con deslizadores o casillas; la probabilidad se recalcula en vivo llamando a predecir variables. En la captura, el cliente doce mil trescientos sesenta y nueve baja la recencia de cuatrocientos trece a treinta días y la probabilidad cae de treinta coma tres a dieciocho coma cuatro: once coma nueve puntos menos. Ojo con la lectura: en este modelo la probabilidad sube con la recencia, lo contrario de la intuición, y no se ha investigado el motivo. Y la relación es estadística, no causal. La advertencia está escrita en la propia pestaña.')

    slide('C', 2, 'Pregunta: un LLM pequeño sin herramientas', 'qwen2.5:0.5b real', 'A veces el modelo pequeño ni llama a las herramientas: pide un dato que ya tiene', cap('ui-07-pregunta-sin-herramientas.webp', 280)
          + '<div class="grid2" style="margin-top:6px">' + mira(['Dos preguntas **seguidas**: ninguna llamada, **cero chips** de herramienta debajo de las respuestas.', 'Con la **conversación vacía**, la misma pregunta por el 12369 sí llamó a `predecir_cliente` (una ejecución previa, sin captura).'], 'Qué debes ver')
          + callout('El aviso de la pestaña lo dice: **«Un modelo pequeño se equivoca»**. Con un modelo mayor el comportamiento puede cambiar: **sin verificar**.', 'font-size:14.5px') + '</div>'
          + fuente('captura 07 (qwen2.5:0.5b por Ollama, 27/11/2026); la ejecución con herramienta se vio una vez y no se guardó.'),
          'La pestaña Pregunta con el modelo real de quinientos millones de parámetros. Se pulsan dos sugerencias seguidas: qué país vende más, y qué probabilidad tiene el cliente doce mil trescientos sesenta y nueve. El modelo responde las dos veces pidiendo el identificador del cliente, sin llamar a ninguna herramienta: no hay chips debajo. En otra ejecución previa, con la conversación vacía, la segunda pregunta sí llamó a predecir cliente, pero no quedó guardada la captura; el modelo no es fiable. Con un modelo mayor no se ha probado. Mensaje: por eso hay que mirar siempre las llamadas.')

    slide('C', 2, 'Pregunta: con herramienta y se equivoca al explicar', 'el dato es bueno, la glosa no', 'La herramienta devuelve 0,3035; el LLM lo envuelve con frases sin sentido', dos_columnas(
        mira(['La tarjeta de abajo es **la fuente**: `predecir_cliente` · correcta · 164 ms · `probabilidad: 0.3035`, versión 6, alias `champion`.', 'El LLM acierta la cifra, pero añade «**Esta variable tiene un valor de 6**» y mezcla variables: no es verdad.', 'La regla del curso: **los números salen de las herramientas, no del LLM**.'])
        + callout('Comprueba **siempre** la tarjeta desplegable, no el texto de arriba.', 'font-size:15px'),
        cap('ui-10-pregunta-predecir.webp', 440), '.8fr 1.2fr')
          + fuente('captura 10 (qwen2.5:0.5b, v6@champion, cliente 12369).'),
          'Aquí el modelo sí llama a la herramienta predecir cliente con el argumento correcto, y la herramienta devuelve cero coma tres mil treinta y cinco, tramo bajo, versión seis. La cifra del LLM es correcta, pero después añade frases sin sentido: dice que una variable tiene un valor de seis, mezcla la versión con una variable. Es el fallo típico de un modelo pequeño. La lección es que los números salen de las herramientas, y por eso cada respuesta lleva debajo la llamada desplegable, con argumentos y resultado.')

    slide('C', 3, 'Pregunta: la glosa de más y el SQL inventado', 'dos fallos más', 'Otras dos veces: una glosa que la herramienta no dice y un SQL que la vigilancia rechaza', dos_columnas(
        cap('ui-08-pregunta-ventas.webp', 300) , cap('ui-09-pregunta-sql-rechazado.webp', 300), '1fr 1fr')
          + '<div class="grid2">' + callout('**Izquierda:** el país (Reino Unido) y las cifras coinciden con la herramienta, pero «**en los últimos 90 días**» es **invención del LLM**: `ventas_por_pais` no filtra por periodo.', 'font-size:14px') + '' + callout('**Derecha:** el LLM inventó `SELECT * FROM clientes…`; la capa 2 lo **rechazó** y el LLM lo contó bien. Se ve que la vigilancia **no depende** de lo que escriba el LLM.', 'font-size:14px;border-color:#c9a65e;background:#fdf6e9') + '</div>'
          + fuente('capturas 08 y 09 (qwen2.5:0.5b, 27/11/2026).'),
          'Dos fallos más del modelo pequeño. A la izquierda llama bien a ventas por país y el país y las cifras coinciden, pero añade que son los últimos noventa días, algo que la herramienta no dice: no filtra por periodo. A la derecha, para comparar dos clientes, inventa una consulta SQL sobre una tabla llamada clientes; la vigilancia del SQL la rechaza porque solo admite las tablas master, y el modelo lo cuenta correctamente. Es un buen ejemplo de por qué la defensa no puede depender del LLM.')

    slide('C', 2, 'Explorador MCP: un formulario por herramienta', 'inputSchema', 'El Explorador genera el formulario de cada herramienta a partir de su esquema', dos_columnas(
        mira(['Dos grupos: **mcp-datos-master (7)** y **mcp-modelo-retencion (4)**.', 'Cada herramienta muestra su **descripción** (lo que lee el LLM) y un campo por argumento, marcando los obligatorios.', '«Ejecutar» llama de verdad y muestra **«Correcta · 10 ms»** y el JSON.', 'La llamada **también** aparece en la traza.'])
        + callout('Es la misma herramienta que usaría el LLM, pero **tú pones los argumentos**.', 'font-size:14.5px'),
        cap('ui-11-explorador-herramienta.webp', 400), '.8fr 1.2fr')
          + fuente('captura 11 (resumen_cliente, cliente 12369, SQLite).'),
          'El Explorador MCP. Se genera un formulario por herramienta a partir de su esquema de entrada: el nombre, la descripción, los argumentos y cuáles son obligatorios. Hay siete herramientas en el servidor de datos y cuatro en el del modelo. Al ejecutar se llama de verdad a la herramienta y se muestra si fue correcta, cuántos milisegundos tardó y el resultado. Es la forma de ver lo que ve el LLM sin tener LLM.')

    slide('C', 2, 'Los 8 ataques SQL y la capa que los frena', 'consulta_sql', 'Ocho ataques de ejemplo: la capa 2 los frena todos antes de llegar al motor', '<div class="split" style="grid-template-columns:1.25fr .75fr"><div class="col"><div class="card" style="padding:6px 10px">'
          + tabla(['Ataque (botón)', 'SQL que envía', 'Mensaje de la capa 2'], [[f'**{n}**', f'`{q}`', m] for n, q, m in ATAQUES])
          + '</div></div><div class="capcol">' + cap('ui-12-ataque-update.webp', 300) + '</div></div>'
          + '<div class="grid2" style="margin-top:2px">' + callout('La consulta legítima (`SELECT pais, COUNT(*) …`) sale **«Consulta aceptada · 5 filas»**.', 'font-size:14px')
          + callout('Las **capas 3 y 4** (solo lectura, 50 filas) **no se activaron**: no hizo falta. Se prueban en `test_servidores_y_notebooks.py`.', 'font-size:14px') + '</div>'
          + fuente('resultados reales de los 8 botones (27/11/2026), captura 12 de la pestaña Explorador; `ATAQUES` en `ui/estatico/app.js`.'),
          'Los ocho ataques de ejemplo del Explorador. Los ocho los frena la capa dos, la vigilancia del SQL, que es la primera línea: solo select, una sentencia, sin comentarios, solo tablas master y sin comas entre tablas. Las capas tres y cuatro, la conexión de solo lectura y el tope de cincuenta filas, no se activan con estos ataques porque la capa dos ya los ha parado; las pruebas del extra las cubren por separado. Una expresión regular no es un analizador de SQL, así que no es una garantía: por eso hay más capas. La consulta legítima devuelve cinco filas.')

    slide('C', 2, 'Modelo: promover otra versión y volver', 'sin reiniciar', 'Al mover el alias cambia la versión que responde, sin reiniciar ningún servidor', dos_columnas(
        cap('ui-13-modelo-promover-v5.webp', 250), cap('ui-14-modelo-volver.webp', 250), '1fr 1fr')
          + '<div class="grid2">' + callout('**Cambia la VERSIÓN** que responde (v6 → v5 → v6), no la cifra: las seis versiones tienen el **mismo AUC** (valid 0,6982 · test 0,7471) y daban **30,3 %** para el 12369.', 'font-size:14px') + '' + callout('**«Volver»** solo existe si la champion **recuerda** una anterior (columna «Recuerda a»); si no, sale desactivado. La interfaz no quita alias.', 'font-size:14px;border-color:#c9a65e;background:#fdf6e9') + '</div>'
          + fuente('capturas 13 y 14 (tabla de versiones de `retencion-90d`).'),
          'La pestaña Modelo. Se promueve la versión cinco y el cuadro dice que antes respondía la versión seis y ahora la cinco; después se vuelve a la seis, que es el rollback. Se ve que cambia la versión que responde y que el servidor del modelo no se reinicia. La cifra no cambia porque las seis versiones se entrenaron con los mismos datos y tienen el mismo AUC; la interfaz lo dice y avisa de que no se ha verificado versión a versión. El botón volver solo existe si la versión champion recuerda cuál fue la anterior. Esta interfaz no sabe quitar un alias.')

    slide('C', 2, 'La traza MCP lateral', 'todas las llamadas', 'La traza lista cada llamada, venga de un clic, del explorador o del LLM', dos_columnas(
        mira(['**Botón «Traza MCP»** de la cabecera, con un contador de llamadas.', 'Cada fila: servidor (`datos` o `modelo`), herramienta, **ms**, **ok o error** y el principio del resultado.', '**Pulsa una fila** para ver el JSON completo; «Vaciar» limpia la lista.', 'Es la prueba de **qué llamó el LLM** de verdad.'])
        + callout('Los errores de la captura son los **ataques SQL rechazados** (capa 2), no fallos del sistema.', 'font-size:14.5px'),
        cap('ui-15-traza.webp', 420), '1.3fr .7fr')
          + fuente('captura 15 (recorte lateral de la interfaz, 27/11/2026).'),
          'La traza MCP. Es el panel lateral que registra todas las llamadas a herramientas, vengan de un clic, del explorador o del LLM. Cada fila muestra el servidor, la herramienta, los milisegundos, si fue correcta o con error y el principio del resultado; al pulsarla se ve el JSON. En la captura se ven los ataques SQL rechazados como filas en rojo, y una consulta legítima correcta. Es la forma de comprobar qué herramientas llamó realmente el LLM.')

    slide('C', 2, 'Pestaña Lote', 'apunta al otro extra', 'La pestaña Lote lanza el DAG por Airflow: sin Airflow, lo dice y no simula nada', dos_columnas(
        mira(['Sin `AIRFLOW_URL`, sale **«Sin conexión»** y el botón «Lanzar el lote» está **desactivado**.', 'La interfaz **no simula** ninguna ejecución.', 'Las claves de Airflow solo se **leen del entorno**; no se guardan ni se muestran.', 'Es el **otro extra** (`extra-composer-batch`): allí se explica el DAG.'])
        + term('Arrancar Airflow en local (otro extra)', ['cd 01-Sesiones/S5-MLOps-y-Operacion/extra-composer-batch', 'docker compose -f docker-compose-airflow.yaml up -d'])
        + sin_verificar('Lanzar un lote real desde esta interfaz **no se ha ejecutado** en esta revisión; las pruebas usan un Airflow falso.'),
        cap('ui-16-lote.webp', 360), '.9fr 1.1fr')
          + fuente('captura 16, `ui/app.py` (`COMO_ARRANCAR`) y `ui/pruebas/test_lote.py`.'),
          'La pestaña Lote pertenece al otro extra, el del procesamiento por lotes con Airflow. Aquí se muestra el estado honesto cuando no hay Airflow: sin conexión, sin URL definida y el botón de lanzar desactivado. La interfaz no simula ninguna ejecución. Si se arranca Airflow en local con docker compose y se reinicia la interfaz con AIRFLOW URL, la pestaña lanza el DAG retención lote. Esa parte no se ha ejecutado de verdad en esta revisión; las pruebas de la carpeta usan un Airflow falso.')

    slide('C', 1, 'Vista móvil', '390 px', 'En una pantalla de móvil, las tarjetas pasan a una columna', dos_columnas(
        mira(['Cabecera con las **tres píldoras apiladas**.', 'Las pestañas se **desplazan** hacia un lado.', 'Debajo, la lista y después el medidor, el gráfico y la ficha, **una tarjeta debajo de otra** (la captura solo recoge la parte alta).', 'La traza es opcional (botón «Traza MCP»).'])
        + callout('Es la misma página, no una versión aparte: solo cambia la maqueta.', 'font-size:14.5px'),
        cap('ui-17-movil.webp', 420), '1.4fr .6fr')
          + fuente('captura 17 (390 × 844 px, recorte de la parte alta, 27/11/2026).'),
          'La vista móvil, con una ventana de trescientos noventa píxeles. Es la misma página: las tarjetas se apilan, la cabecera pone las píldoras en columna y las pestañas se desplazan. No es una aplicación aparte. La captura es un recorte de la parte alta para que se lea.')

    # ---------------------------------------------------------------- D · Ejercicios
    slide('D', 4, 'Ejercicios guiados', 'tres ejercicios', 'Tres ejercicios para repetir lo visto: cada uno acaba comprobando en la traza', '<div class="grid3">'
          + '<div class="card"><h3>1 · Pregunta y comprueba</h3>'
          + lista(['Pestaña **Pregunta** → «Nueva conversación».', 'Pega la pregunta y pulsa «Preguntar».', 'Despliega las tarjetas y abre **«Traza MCP»**.', '¿Qué herramientas llamó? ¿Coincide la cifra del texto con la de la traza? Si no hay llamadas, **anótalo** y repite.'])
          + term('Pregunta por el 12369', ['¿Qué probabilidad tiene el cliente 12369 y por qué?'], {'¿Qué probabilidad tiene el cliente 12369 y por qué?': ['¿Qué probabilidad tiene el cliente 12369 y por qué?']}, prompt=True) + '</div>'
          + '<div class="card"><h3>2 · Ataca la consulta_sql</h3>'
          + lista(['**Explorador MCP** → «SQL con vigilancia».', 'Pega este ataque, **predice la capa** que lo frena y pulsa «Ejecutar consulta».', 'Inventa **dos ataques propios** y anota capa y mensaje.', 'Comprueba en la traza que quedan como «error».'])
          + term('Ataque de ejemplo', ['SELECT * FROM main.master_clientes'], prompt=True) + '</div>'
          + '<div class="card"><h3>3 · Promueve otra versión y vuelve</h3>'
          + lista(['**Modelo** → «Promover v5» (acepta el diálogo).', 'Lee «Qué cambió al mover el alias».', 'Pulsa «Volver a la v6».', 'Abre la traza: busca `modelo_en_uso`. **Qué cambia y qué no.**'])
          + '<p class="small" style="margin-top:6px"><b>Cuidado:</b> escribe en el registro de MLflow. La interfaz no quita alias: avisa al profesor.</p></div></div>'
          + fuente('`ATAQUES` y `SUGERENCIAS` de `ui/estatico/app.js`; diálogos de la pestaña Modelo.'),
          'Tres ejercicios guiados. Uno: preguntar al LLM por el cliente doce mil trescientos sesenta y nueve y comprobar en la traza qué herramientas llamó; si no llamó ninguna, apuntarlo y repetir. Dos: atacar la consulta sql; antes de pulsar, predecir qué capa lo frena, e inventar dos ataques propios. Tres: promover otra versión y volver, y decir qué cambia, que es la versión, y qué no, que es la cifra. Aviso: el ejercicio tres escribe en el registro de MLflow del proyecto base y la interfaz no sabe quitar un alias.')

    # ---------------------------------------------------------------- E · Pruebas y límites
    slide('E', 2, 'Cómo se prueba', 'pytest', f'{PRUEBAS_VERDES} pruebas en verde con la aplicación y los servidores reales', dos_columnas(
        term('Desde extra-mcp-notebooks', ['python -m pytest ui/pruebas -q'])
        + mira([f'**{PRUEBAS_VERDES} pruebas** pasaron el {FECHA} (Windows, `env-ia-mlops`).', 'Usan **la aplicación y los dos servidores MCP reales**, un LLM de guion y, si responde, Ollama real sin exigir acierto.', 'Si no hay `champion`, lo ponen y **dejan el registro como lo encontraron**.', '`test_presentacion.py` vigila **estas diapositivas**.'])
        + fuente('ejecución real del 27/11/2026 y `ui/README.md` (Pruebas).'),
        card('Cobertura', ['`test_interfaz.py`: estado, herramientas, chat, hosts, promover y volver.', '`test_lote.py`: pestaña Lote con un Airflow falso.', '`test_presentacion.py`: estructura, órdenes copiables, capturas y rótulos.'])
        + callout('`ui/pruebas/capturar.py` repite el recorrido con Playwright y guarda capturas (`--promover` escribe en el registro).', 'font-size:14.5px'), '1.05fr .95fr'),
          'Cómo se prueba. Con python menos m pytest sobre la carpeta ui barras pruebas, desde el extra. Las pruebas usan la aplicación real, los dos servidores reales, un LLM de guion y, si responde, el Ollama real sin exigir que acierte. Si no hay alias champion lo ponen y al terminar dejan el registro como lo encontraron. Esta presentación tiene además su propia prueba, que comprueba que las órdenes copiables existen en el README o en el código, que cada captura existe y tiene su rótulo, y que no hay enlaces externos.')

    slide('E', 2, 'Qué no está verificado', 'límites', 'Lo que no se ha probado, dicho claro', '<div class="grid2">' + card('Sin verificar', [
        '**BigQuery real desde la interfaz**: solo con un conector falso.', '**Codespace** y **Linux**: solo se probó en Windows.', '**Un LLM mayor** (por ejemplo, Qwen2.5-3B del curso): solo se vio `qwen2.5:0.5b`.', 'Lanzar un **lote real** por Airflow desde la pestaña Lote.', 'Que las versiones del modelo den lo mismo **una a una** (la interfaz lo avisa).'])
          + card('Sí verificado', ['Arranque en Windows y recorrido de las **6 pestañas**, con capturas reales.', 'Los **8 ataques** rechazados por la capa 2 y la consulta legítima aceptada.', 'Promover y volver **sin reiniciar** el servidor del modelo.', f'**{PRUEBAS_VERDES} pruebas** automáticas en verde.'])
          + '</div>' + callout('**Hallazgo del modelo pequeño:** `qwen2.5:0.5b` falló de tres maneras distintas (no llamó herramientas, glosó de más, inventó una tabla). Ninguna cifra mala llegó a la pantalla: **las cifras vienen de las herramientas**.', 'margin-top:12px')
          + fuente('`ui/README.md` (BigQuery, Codespace), capturas 07 a 10 y ejecución de pruebas del 27/11/2026.'),
          'Cierre y límites. Sin verificar: BigQuery real desde la interfaz, porque solo se probó con un conector falso; Codespace y Linux; un modelo mayor que el de quinientos millones de parámetros; y lanzar un lote real desde la pestaña Lote. Verificado: el arranque en Windows, el recorrido de las seis pestañas con capturas reales, los ocho ataques rechazados, promover y volver sin reiniciar, y las pruebas automáticas. La lección final: el modelo pequeño falló de tres maneras y, aun así, las cifras que se ven vienen de las herramientas, que es el diseño.')



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

.fuente{font-size:12.5px;line-height:1.35;color:var(--suave);margin-top:2px}
.fuente .mono{font-size:.95em}
.tbl td .mono{font-size:12.5px}
.grid2>.callout{align-self:start}
.cover .grid3 .card .list li{font-size:14px}

.zoom img{width:auto}
.split>.col,.split>.capcol{min-width:0}
.cap figcaption{font-size:11.5px}
.cover .grid3 .card .list li{font-size:14px}
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
  f.innerHTML=`<span>ML e IA · S5 · Interfaz web MCP y LLM</span><span><b>${esc(PARTES[s.dataset.part]||'')}</b> · ${i+1} / ${N}</span>`;s.appendChild(f)});
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


def html_completo():
    ORDENES.clear()
    construir()
    js = JS.replace('__PARTES__', json.dumps(PARTES, ensure_ascii=False))
    partes = ''.join(f'<button class="part" data-p="{k}">{esc(v)}</button>' for k, v in PARTES.items())
    return ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>Interfaz web MCP y LLM · extra de S5 · ML e IA: de desarrollo a producción</title>\n'
            f'<!-- Generado por generar_slides.py: no se edita a mano. -->\n<style>{CSS}</style>\n</head>\n<body>\n'
            '<div id="prog"></div>\n<div id="viewport"><div id="stage">\n\n' + '\n\n'.join(SLIDES) + '\n\n</div></div>\n\n'
            '<aside id="notes" aria-label="Notas del ponente"><h3>Notas del ponente</h3><div id="notetext"></div><p class="small" id="notemin"></p></aside>\n'
            '<div id="index" aria-label="Índice"><h2>Índice</h2><div class="grid" id="idxgrid"></div></div>\n'
            '<div id="zoombox" aria-label="Captura ampliada"><p>Esc o clic para cerrar</p><img id="zoomimg" alt=""></div>\n'
            '<nav id="bar" aria-label="Controles">\n'
            '  <button id="bprev" aria-label="Anterior">←</button><button id="bnext" aria-label="Siguiente">→</button>\n'
            f'  <span id="count">1 / 1</span><span id="clockref" title="Minuto planificado acumulado (propuesta)"></span>\n  {partes}\n'
            '  <span class="sp"></span>\n'
            '  <a id="bhome" href="../../index.html" title="Volver al índice de la sesión S5">⌂ Índice</a><button id="bidx">Índice (O)</button><button id="bnotes">Notas (S)</button><button id="bfull">Pantalla completa (F)</button>\n'
            '</nav>\n'
            '<noscript>Esta presentación necesita JavaScript. El mismo contenido está en ui/README.md.</noscript>\n\n'
            f'<script>{js}</script>\n</body>\n</html>\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--comprobar', action='store_true')
    a = ap.parse_args()
    nuevo = html_completo()
    actual = SALIDA.read_bytes().decode('utf-8') if SALIDA.exists() else None
    pendientes = [n for n in CAPTURAS if not (AQUI / 'img' / n).is_file()]
    if a.comprobar:
        if actual != nuevo:
            print('DESFASADO: ejecuta python generar_slides.py')
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
