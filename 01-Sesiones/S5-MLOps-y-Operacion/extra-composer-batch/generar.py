"""Genera la presentación del extra «Ejecución batch del modelo orquestada con Airflow (Cloud Composer)» (index.html, junto a este archivo).

Qué cuenta: por qué orquestar el lote de puntuación, qué son Airflow, DAG, tarea, operador y Cloud Composer, y el laboratorio PASO A PASO:
el lote a mano, la imagen, el DAG, Airflow en local, el cliente REST, la pestaña «Lote» de la interfaz, Composer y GitHub Actions.
Mensaje: un orquestador no cambia lo que hace el lote; añade dependencias, reintentos, historial y un botón. Y lo que no se ejecutó, se dice.

TODO el código y todas las salidas que se enseñan se LEEN de los archivos de esta carpeta (dags/, comandos.md, workflows, salidas/), de modo
que la presentación no puede contar otra cosa que lo que hay. Las capturas de img/ son reales: salidas de terminal que se ejecutaron,
la pestaña Lote contra un servidor Airflow DE PRUEBA (no es Airflow) y dos pantallas de la consola de Google Cloud en solo lectura.
Lo que falta (Airflow real, Composer, GitHub Actions) sale como recuadro «Captura pendiente» con la receta para hacerla.

El visor (CSS y JavaScript) es el MISMO que el del extra MCP y el laboratorio de agentes de S5, copiado aquí (no se importa).

Uso:  python generar.py              escribe index.html
      python generar.py --comprobar  no escribe; sale con 1 si index.html no está al día
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / 'index.html'
FECHA = '27/11/2026'
TOTAL_MIN = 120

PARTES = {'A': 'Plan', 'B': 'El lote y el DAG', 'C': 'Airflow en local', 'D': 'Lanzarlo', 'E': 'Cloud Composer', 'F': 'GitHub Actions', 'G': 'Cierre'}
NOMBRES_PARTE = {'A': 'Por qué y qué', 'B': 'Preparar el lote y escribir el DAG', 'C': 'Airflow en tu ordenador', 'D': 'Lanzarlo desde fuera: cliente REST e interfaz',
                 'E': 'Cloud Composer', 'F': 'Automatizarlo con GitHub Actions', 'G': 'Lo probado, lo que falta y los costes'}

# Capturas (webp) -> lo que muestran de verdad (alt y pie). Si el archivo no está en img/, sale el recuadro «Captura pendiente».
CAPTURAS = {
    'term-01-explotacion.webp': 'Terminal: salida REAL de «python -m ia_mlops.explotacion --corte 2011-12-10 --capacidad 0.1 --sin-guardar-fs» sobre una copia de curso.db',
    'term-02-resumir-y-validar.webp': 'Terminal: salida REAL de resumir_salida(), validar_salida() y resumen_markdown() sobre esa salida',
    'term-03-lanzar-lote.webp': 'Terminal: salida REAL de lanzar_lote.py contra el servidor Airflow DE PRUEBA (no es Airflow): un run correcto (código 0), uno fallido (código 1) y sin servidor (código 3)',
    'term-04-simular-url.webp': 'Terminal: salida REAL de lanzar_lote.py con --simular-url (no llama a nadie)',
    'term-05-pytest-extra.webp': 'Terminal: salida REAL de las pruebas de extra-composer-batch',
    'term-06-pytest-ui.webp': 'Terminal: salida REAL de las pruebas de la interfaz (las 46 de antes y las nuevas de la pestaña Lote)',
    'ui-01-sin-airflow.webp': 'Pestaña Lote de la interfaz arrancada SIN AIRFLOW_URL: dice «Sin conexión», cómo arrancar Airflow, y el botón «Lanzar el lote» desactivado. No simula nada',
    'ui-02-conectado.webp': 'Pestaña Lote conectada a un servidor Airflow DE PRUEBA (no es Airflow real): configuración leída del entorno, sin secretos, y el formulario',
    'ui-03-dialogo.webp': 'Diálogo propio de confirmación de la pestaña Lote: «Esto lanza» y «Esto no hace»',
    'ui-04-en-curso.webp': 'Run en curso contra el servidor Airflow DE PRUEBA: entradas y comprobar correctas, ejecutar_lote en curso, el resto pendiente',
    'ui-05-terminado.webp': 'Run terminado contra el servidor Airflow DE PRUEBA, con el registro de la tarea «resumir» (texto simulado del servidor de prueba) y el historial',
    'ui-06-fallo.webp': 'Run fallido contra el servidor Airflow DE PRUEBA (imagen «…:falla»): ejecutar_lote falla, las demás no llegan a ejecutarse, y su registro',
    'ui-07-movil.webp': 'La pestaña Lote en un móvil (390 px), contra el servidor Airflow DE PRUEBA',
    'gcp-01-composer-api.webp': 'Consola de Google Cloud, solo lectura: la entrada de Cloud Composer en el proyecto del curso. La API está sin habilitar (botón «Habilitar» sin pulsar): no hay entorno que enseñar sin crear uno (nombre del proyecto y cuenta difuminados)',
    'gcp-02-artifact-registry.webp': 'Consola de Google Cloud, solo lectura: Artifact Registry del proyecto del curso, sin repositorios todavía: aquí se subirá la imagen del lote (nombre del proyecto y cuenta difuminados)',
    'gh-01-actions-lista.webp': 'GitHub, solo lectura: la pestaña Actions del repositorio del curso con los workflows YA existentes (puntuar-lote, nueva-version…). El workflow nuevo de este extra todavía NO está en el repositorio',
    'gh-02-nueva-version-runs.webp': 'GitHub, solo lectura: ejecuciones de «Nueva versión del modelo», un workflow que YA existe (otro, no el de este extra), para ver cómo luce una lista de runs. No hay botón «Run workflow» porque los workflows de ensayo viven en ramas lab/, no en la rama por defecto',
    'gh-03-puntuar-lote-resumen.webp': 'GitHub, solo lectura: un run YA terminado de «Puntuar por lotes» (otro workflow, de S4) con sus tres trabajos y su Job Summary «Puntuación por lotes»: así lucirá el resumen del lote en Composer',
    'gh-04-environments.webp': 'GitHub, solo lectura: Settings › Environments del repositorio: el environment «produccion» con 1 regla de protección (el de la aprobación), que usarán los workflows nuevos',
    'gh-05-variables.webp': 'GitHub, solo lectura: Settings › Secrets and variables › Actions › Variables: las GCP_* de S4 (valores difuminados). Las del extra (COMPOSER_ENV, COMPOSER_REGION, COMPOSER_CUENTA…) habría que añadirlas',
    # Pendientes: no existen aún
    'airflow-01-dag-en-la-lista.webp': 'Interfaz de Airflow (local): la lista de DAGs con retencion_lote',
    'airflow-02-grid-run-ok.webp': 'Interfaz de Airflow: vista Grid del run con las cinco tareas en verde',
    'airflow-03-registro-resumir.webp': 'Interfaz de Airflow: registro de la tarea «resumir» con el resumen del lote',
    'composer-01-entornos.webp': 'Consola de Google Cloud: lista de entornos de Composer con el entorno en RUNNING',
    'composer-02-bucket-dags.webp': 'Carpeta /dags del bucket del entorno con retencion_lote.py y lote_logica.py',
    'composer-03-run.webp': 'Interfaz de Airflow del entorno de Composer: el run en verde',
    'gcp-iam-roles.webp': 'Consola de IAM: roles de la cuenta de servicio del entorno y de la de GitHub Actions',
    'actions-01-run-workflow.webp': 'GitHub Actions: formulario «Run workflow» de «Lote en Cloud Composer» con corte, imagen y capacidad',
    'actions-02-aprobacion.webp': 'GitHub Actions: el run esperando la aprobación del environment «produccion» (Review deployments)',
    'actions-03-job-summary.webp': 'GitHub Actions: la página del run con el Job Summary (tabla de tareas y registro de resumir)',
    'actions-04-ensayo-airflow.webp': 'GitHub Actions: el resumen del ensayo «airflow dags test» en el runner',
}
RECETAS = {
    'airflow-01-dag-en-la-lista.webp': ['`docker compose -f docker-compose-airflow.yaml up -d` en la carpeta del extra.', 'Abre http://localhost:8080 (airflow / airflow).', 'Captura la lista de DAGs.'],
    'airflow-02-grid-run-ok.webp': ['Lanza el DAG con `airflow dags trigger …` (paso siguiente).', 'Abre el DAG y su vista Grid.', 'Captura con las cinco tareas en verde.'],
    'airflow-03-registro-resumir.webp': ['En el run, pulsa la tarea «resumir» y la pestaña Logs.', 'Captura el resumen «Lote de retención».'],
    'composer-01-entornos.webp': ['(Cuesta dinero) crea el entorno con el comando del paso.', 'Consola → Cloud Composer → Entornos.', 'Captura con el entorno en RUNNING y bórralo después.'],
    'composer-02-bucket-dags.webp': ['Tras `dags import`, abre «Abrir carpeta DAGs» del entorno.', 'Captura los dos archivos.'],
    'composer-03-run.webp': ['Lanza el DAG con `gcloud composer environments run …`.', 'Abre la interfaz de Airflow del entorno, vista Grid.', 'Captura el run.'],
    'gcp-iam-roles.webp': ['Consola → IAM.', 'Filtra por la cuenta de servicio del entorno y la de Actions.', 'Captura y difumina el proyecto.'],
    'actions-01-run-workflow.webp': ['Copia `lote-composer.yml` a `.github/workflows/` de la rama por defecto (el botón «Run workflow» solo aparece así).', 'Actions → «Lote en Cloud Composer» → Run workflow.', 'Captura el formulario SIN pulsar Run.'],
    'actions-02-aprobacion.webp': ['Lanza el workflow.', 'Cuando espere en «produccion», captura «Review deployments».'],
    'actions-03-job-summary.webp': ['Con el run terminado, abre su página.', 'Captura el Job Summary.'],
    'actions-04-ensayo-airflow.webp': ['Sigue la receta «Ensayo en Actions» del README.', 'Captura el resumen del job.'],
}


# ------------------------------------------------------------------------------------------------------------------------
# Lectura de los archivos reales (única fuente de código y de salidas)
# ------------------------------------------------------------------------------------------------------------------------
def leer(rel):
    return (AQUI / rel).read_text(encoding='utf-8')


def salida_txt(nombre):
    return leer('salidas/' + nombre).rstrip('\n')


def trozo(texto, desde, hasta=None):
    """Líneas desde la primera que contiene `desde` hasta la anterior a la primera posterior que contiene `hasta` (o el final)."""
    lineas = texto.split('\n')
    ini = next(k for k, l in enumerate(lineas) if desde in l)
    fin = len(lineas)
    if hasta is not None:
        fin = next(k for k in range(ini + 1, len(lineas)) if hasta in lineas[k])
    return '\n'.join(lineas[ini:fin]).rstrip()


def bloque(desde):
    """El bloque de código de comandos.md que contiene `desde`, tal cual."""
    for b in re.findall(r'```\w*\n(.*?)```', leer('comandos.md'), re.S):
        if desde in b:
            return b.rstrip('\n')
    raise KeyError(desde)



# ----------------------------------------------------------------------------------------------------------------------
# Piezas del visor (copiadas del extra MCP de S5)
# ----------------------------------------------------------------------------------------------------------------------
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





def cap(nombre, alto=None, nota=None):
    """Una captura real (clic = ampliar) o, si aún no está en img/, el recuadro «Captura pendiente» con la receta para hacerla."""
    alt = CAPTURAS[nombre]
    estilo = f' style="max-height:{alto}px"' if alto else ''
    extra = f'<br><span class="nota">{md(nota)}</span>' if nota else ''
    if (AQUI / 'img' / nombre).is_file():
        return (f'<figure class="cap" data-img="{nombre}"><button class="zoom" data-src="img/{nombre}" data-alt="{esc(alt)}" title="Ampliar (Esc cierra)">'
                f'<img src="img/{nombre}" alt="{esc(alt)}"{estilo}><span class="lupa">{LUPA} Ampliar</span></button>'
                f'<figcaption><span class="tag ok">Captura real</span> {esc(alt)}{extra}</figcaption></figure>')
    receta = '<ol class="small">' + ''.join(f'<li>{md(p)}</li>' for p in RECETAS.get(nombre, [])) + '</ol>'
    return (f'<figure class="cap" data-img="{nombre}"><div class="pend"><b>Captura pendiente</b><span class="mono">img/{nombre}</span>'
            f'<span>{esc(alt)}</span><span class="small"><b>Cómo hacer esta captura</b></span>{receta}</div>'
            f'<figcaption><span class="tag warn">Pendiente</span> {esc(alt)}{extra}</figcaption></figure>')


def svg_arquitectura():
    g = ['<defs><marker id="fa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#0b5cad"/></marker></defs>']
    xs = [6, 226, 446, 666, 886]
    g.append(_caja(xs[0], 30, 190, ['Imagen del lote', 'API + modelo + SQL + datos', 'Artifact Registry'], 'nodo', 96))
    g.append(_caja(xs[1], 30, 190, ['Airflow / Composer', 'el DAG retencion_lote', 'lo lanzas con --conf'], 'nodo puerta', 96))
    g.append(_caja(xs[2], 30, 190, ['Pod o contenedor', 'python -m ia_mlops.', 'explotacion'], 'nodo puerta', 96))
    g.append(_caja(xs[3], 30, 190, ['Salida', 'campana_<corte>.csv', 'y .json'], 'nodo', 96))
    g.append(_caja(xs[4], 30, 190, ['Validación y resumen', 'filas · prob. en [0,1]', 'tramos · deciles'], 'nodo ok', 96))
    for k in range(4):
        g.append(f'<path d="M{xs[k] + 190} 78 L{xs[k + 1] - 3} 78" class="fl" marker-end="url(#fa)"/>')
    g.append('<text x="550" y="160" class="t2">comprobar → ejecutar_lote → validar → resumir: si una falla, las siguientes no corren y el run queda en rojo</text>')
    return ('<svg viewBox="0 0 1100 175" role="img" aria-label="La imagen del lote se ejecuta como pod o contenedor lanzado por el DAG; deja la campaña en CSV y JSON; '
            'una tarea valida la salida y otra la resume">' + ''.join(g) + '</svg>')


# ------------------------------------------------------------------------------------------------------------------------
# Contenido
# ------------------------------------------------------------------------------------------------------------------------
def construir():
    SLIDES.clear()
    _N.clear()
    dag = leer('dags/retencion_lote.py')
    logica = leer('dags/lote_logica.py')
    wf = leer('lote-composer.yml')
    wd = leer('dags-composer.yml')
    we = leer('ensayo-airflow.yml')

    # ---------------------------------------------------------------- A · Plan
    slide('A', 3, 'Portada', 'ML e IA: de desarrollo a producción · S5 · extra', 'El lote del modelo, orquestado con Airflow en Cloud Composer', f'''
<div class="cover">
 <p class="sub">Cada día hay que puntuar a <b>todos</b> los clientes. Ya lo hace GitHub Actions (S4). Aquí lo hace <b>Airflow</b>, el orquestador, en su versión gestionada de Google Cloud: <b>Cloud Composer</b>. Un <b>DAG</b> de cuatro pasos, una <b>interfaz</b> con un botón y los <b>workflows</b> de Actions que lo lanzan con aprobación.</p>
 <div class="chips"><span class="tag">DAG retencion_lote</span><span class="tag">KubernetesPodOperator</span><span class="tag">DockerOperator</span><span class="tag">API REST</span><span class="tag">pestaña Lote</span><span class="tag">WIF sin claves</span></div>
 <div class="grid3" style="margin-top:20px">
  {card('Lo que te llevas', ['El **DAG** y los **comandos** para lanzarlo a mano.', 'Una **interfaz** para lanzarlo y verlo.', 'Los **workflows** de GitHub Actions.'])}
  {card('Cómo se usa', ['Cada paso trae su **orden con ⧉** para copiar y pegar.', 'Cada paso trae **qué debes ver** y **si falla**.', '**← →** avanzan · **O** índice · **S** notas · **F** pantalla completa.'])}
  {card('Honestidad desde el principio', [f'Ejecutado el **{FECHA}**: el lote real, la validación, el cliente REST y la interfaz (contra un **Airflow de prueba**).', '**Sin verificar:** el DAG en un Airflow real, Composer, Docker y los workflows en Actions. Se marca en cada diapositiva.'])}
 </div>
</div>''',
          'Portada del extra. El profesor decidió Cloud Composer, el Airflow gestionado de Google Cloud. Este extra tiene tres piezas: el DAG con los comandos manuales, una interfaz para lanzarlo y los workflows de GitHub Actions. Diga desde el principio lo que se ejecutó de verdad y lo que no: el DAG no se ha ejecutado en un Airflow real, ni nada en Composer, ni Docker. Cada diapositiva lo marca.')

    slide('A', 4, 'Por qué orquestar un lote', 'del cron al orquestador', '¿Por qué no basta un cron o un workflow? Porque un lote real tiene pasos, dependencias y fallos', f'''
<div class="grid2">
 {card('Lo que ya hace puntuar-lote.yml (S4)', ['Un workflow de Actions con `schedule` entrena, construye la API y puntúa a todos los clientes.', 'Funciona y es **barato**: para un lote diario aislado, **puede ser suficiente**.'])}
 {card('Lo que añade un orquestador', ['**Dependencias:** validar solo si el lote terminó; resumir solo si validó.', '**Reintentos y estado por tarea:** ves *qué* tarea falló y la repites sola.', '**Historial y botón:** cada ejecución queda guardada y se lanza con parámetros.', '**Un sitio donde coordinar muchos flujos** (ingesta, lote, monitoreo…).'])}
</div>
{callout('**Decisión del profesor: Cloud Composer.** Se justifica cuando hay **muchos** flujos que coordinar. Para uno solo, Cloud Run Jobs o el propio Actions cuestan mucho menos: el README lo dice sin cifras inventadas.')}''' + fuente('`puntuar-lote.yml` de S4 y README de este extra.'),
          'Por qué orquestar. Ya hay un lote diario en GitHub Actions, el workflow puntuar lote de S4, y funciona. Un orquestador añade dependencias entre pasos, reintentos, el estado de cada tarea, historial y un botón con parámetros. La decisión del profesor es Cloud Composer; sea honesto: para un solo lote es más caro que Actions o que un Cloud Run Job.')

    slide('A', 4, 'Airflow en cinco palabras', 'vocabulario', 'DAG, tarea, operador, ejecución y Composer: el vocabulario que necesitas', '<div class="card">' + tabla(['Palabra', 'Qué es', 'En este extra'], [
        ['**DAG**', 'Un grafo de tareas **sin ciclos**, escrito en Python', '`retencion_lote`: `entradas → comprobar → ejecutar_lote → validar → resumir`'],
        ['**Tarea**', 'Un paso del grafo', 'Cinco tareas'],
        ['**Operador**', 'La plantilla de una tarea (qué sabe hacer)', '`KubernetesPodOperator`, `DockerOperator`, `PythonOperator`'],
        ['**Run (ejecución)**', 'Una pasada completa del DAG, con su estado', '`success` o `failed`; lleva su `conf` (corte, imagen)'],
        ['**Cloud Composer**', 'Airflow **gestionado** en Google Cloud', 'Composer 3 ofrece Airflow 2 y Airflow 3; subes los DAG a `/dags` de un bucket']]) + '</div>' + fuente('<https://docs.cloud.google.com/composer/docs/composer-versioning-overview> y <https://docs.cloud.google.com/composer/docs/composer-3/manage-dags>.'),
          'El vocabulario. Un DAG es un grafo de tareas sin ciclos, escrito en Python. Una tarea es un paso; un operador es la plantilla de una tarea; un run es una pasada completa. Cloud Composer es Airflow gestionado: Composer tres ofrece Airflow dos y Airflow tres según su documentación de versiones.')

    slide('A', 4, 'Arquitectura', 'imagen → pod → salida → validación', 'La imagen lleva el modelo; el DAG la ejecuta, valida la salida y la resume', f'''
<div class="card">{svg_arquitectura()}</div>
<div class="grid3" style="margin-top:12px">
 {card('La imagen', ['La imagen de la API lleva el modelo, pero **no el SQL ni los datos** (su `.dockerignore` los excluye).', '`lote.Dockerfile` parte de ella y los añade: sirve con el Dockerfile de develop **y** con el multi-etapa (`--build-context modelo=…`).'])}
 {card('Dos operadores', ['**Composer:** `KubernetesPodOperator` con la imagen de Artifact Registry.', '**Local:** `DockerOperator` con el socket de Docker.', 'Se elige con `LOTE_MODO`; si falta el proveedor, el DAG **se importa igual**.'])}
 {card('La salida', ['`explotacion` escribe `campana_<corte>.csv` y `.json` en `/tmp/reports` del contenedor.', 'El pod devuelve un **resumen pequeño** por XCom; no se guarda la lista de clientes fuera.'])}
</div>''' + sin_verificar('El DAG no se ha ejecutado en un Airflow real: ni con Docker ni en Composer.'),
          'La arquitectura. La imagen de la API lleva el modelo pero no el SQL ni los datos, porque su dockerignore los excluye; por eso lote punto Dockerfile parte de esa imagen y añade el SQL de la capa FS y la base de muestra. Como parte de la imagen ya construida, vale con el Dockerfile actual de develop y con el multi etapa que usa build context modelo. El DAG tiene dos variantes de operador; el pod devuelve un resumen pequeño por XCom y una tarea del worker lo valida.')

    # ---------------------------------------------------------------- B · Lote y DAG
    b0 = bloque('python -m ia_mlops.explotacion --corte 2011-12-10 --capacidad 0.1 --sin-guardar-fs\n')
    slide('B', 6, 'Paso 1 · El lote a mano', 'ejecutado', 'Paso 1 · Antes de orquestar nada, el lote tiene que funcionar a mano', dos_columnas(
        codigo('comandos.md · paso 0 (copia y pega)', b0) + mira(['`Clientes puntuados: 148` y `Campaña: 15 clientes`.', 'Los 10 primeros con su decil y los avisos (132 clientes con valores fuera de rango).', 'Código de salida 0.']) + si_falla(['`MASTER está vacío` / `No existe la capa FS` → falta `python -m ia_mlops.pipeline`.', 'Con `CURSO_DB` y `CURSO_REPORTES` en una carpeta temporal no se toca el proyecto: así se probó.']),
        cap('term-01-explotacion.webp', 440), '.85fr 1.15fr') + '<p class="small"><span class="tag ok">Ejecutado</span> sobre una copia de curso.db; el repositorio no cambió (comprobado con hashes).</p>',
          'Paso uno. Antes de orquestar, el lote debe funcionar a mano. Estos son los comandos del paso cero de comandos punto md. La captura es la salida real: ciento cuarenta y ocho clientes, quince en campaña. Se ejecutó sobre una copia de curso punto db para no tocar el proyecto.')

    b1 = bloque('docker build -f ../$EXTRA/lote.Dockerfile')
    slide('B', 5, 'Paso 2 · La imagen del lote', 'sin verificar', 'Paso 2 · La imagen del lote: la de la API más el SQL y los datos', dos_columnas(
        codigo('lote.Dockerfile', trozo(leer('lote.Dockerfile'), 'ARG IMAGEN_API')) + codigo('comandos.md · paso 1 (copia y pega)', b1),
        mira(['`retencion-lote:local` aparece en `docker image ls`.', 'El último comando repite la salida del paso 1.']) + si_falla(['`Cannot connect to the Docker daemon` → Docker no está en marcha.', '`COPY failed … curso.db` → falta `python -m ia_mlops.pipeline`.']) + sin_verificar('No hay Docker en el ordenador donde se escribió: **no se ha construido** esta imagen. Los datos van dentro porque el curso los congela; en una empresa se leerían de BigQuery o de un volumen.'), '1.1fr .9fr'),
          'Paso dos. La imagen del lote. El código es el del lote punto Dockerfile y los comandos son los del paso uno de comandos punto md. No se ha construido: no hay Docker aquí. Los datos van dentro de la imagen solo porque el curso los congela.')

    slide('B', 5, 'El DAG', 'dags/retencion_lote.py', 'El DAG: cinco tareas encadenadas, sin schedule y con cuatro parámetros', dos_columnas(
        codigo('dags/retencion_lote.py · la definición', trozo(dag, 'with DAG(', None)),
        mira(['**Sin `schedule`**: se lanza a mano, por la API o por Actions.', '`max_active_runs=1`: dos lotes a la vez no tienen sentido.', 'Cuatro `params`: `corte`, `imagen`, `capacidad`, `huella_esperada`; el formulario de Airflow los valida.']) + card('Las cinco tareas', ['`entradas`: valida lo que escribió una persona **antes** de lanzar nada.', '`comprobar`: qué modelo lleva la imagen.', '`ejecutar_lote`: `python -m ia_mlops.explotacion`.', '`validar` y `resumir` corren en el worker.']), '1.1fr .9fr'),
          'El DAG. Sin schedule, un solo run a la vez y cuatro parámetros. La primera tarea valida las entradas antes de lanzar ningún contenedor. Comprobar lee qué modelo lleva la imagen. Ejecutar lote corre explotacion. Validar y resumir corren en el worker de Airflow.')

    slide('B', 5, 'Dos operadores', 'KubernetesPodOperator y DockerOperator', 'Dos variantes del operador, elegidas por LOTE_MODO, sin que el DAG deje de importarse', dos_columnas(
        codigo('Composer · KubernetesPodOperator', trozo(dag, 'def pod(', '# ---- VARIANTE 2')) + codigo('Local · DockerOperator', trozo(dag, 'def contenedor(', 'def operador')),
        card('Lo que dice la documentación', ['En Composer 3 los pods corren siempre en **`composer-user-workloads`**; `config_file` es `/home/airflow/composer_kube_config`.', 'XCom del pod: el contenido de `/airflow/xcom/return.json`.', '`DockerOperator` es del paquete `apache-airflow-providers-docker`; sin XCom completo recoge la **última línea** de salida.']) + fuente('<https://docs.cloud.google.com/composer/docs/composer-3/use-kubernetes-pod-operator> y la documentación del proveedor Docker.') + sin_verificar('Los argumentos están escritos de la documentación y probados con un Airflow *de cartón*; no se han ejecutado en Airflow.'), '1.2fr .8fr'),
          'Las dos variantes. En Composer, KubernetesPodOperator con el espacio de nombres composer user workloads y el archivo de configuración que indica la documentación. En local, DockerOperator con el socket de Docker. Si falta el proveedor, la tarea falla con un mensaje que dice qué instalar, pero el DAG se importa. Esto está probado con módulos falsos, no con Airflow.')

    slide('B', 5, 'Validar la salida', 'filas, probabilidades, tramos', 'La tarea «validar» no se fía: filas, probabilidades en [0,1], tramos y modelo', dos_columnas(
        codigo('dags/lote_logica.py · validar_salida (extracto)', trozo(logica, 'def validar_salida', '    if comprobar:')),
        cap('term-02-resumir-y-validar.webp', 420) + '<p class="small"><span class="tag ok">Ejecutado</span> sobre la salida real del paso 1; las pruebas corrompen cada dato y comprueban que se detecta.</p>', '1.05fr .95fr'),
          'La validación. Comprueba que hay filas, que las probabilidades están entre cero y uno, que los tramos suman las filas, que hay diez deciles, que la campaña tiene el tamaño que dice la capacidad y que el modelo que puntuó es el que declaraba la imagen. Se probó sobre la salida real y las pruebas rompen cada dato para ver que se detecta. Los tramos alta, media y baja son los de la configuración del proyecto; una prueba comprueba que no se separan.')

    # ---------------------------------------------------------------- C · Local
    b2 = bloque('docker compose -f docker-compose-airflow.yaml up -d\n')
    slide('C', 6, 'Paso 3 · Airflow en local', 'sin verificar', 'Paso 3 · Airflow en tu ordenador con Docker (compose mínimo)', dos_columnas(
        codigo('comandos.md · paso 2', b2) + codigo('docker-compose-airflow.yaml (extracto)', trozo(leer('docker-compose-airflow.yaml'), 'services:', '    command:')),
        mira(['Tras 1-2 minutos, http://localhost:8080 pide usuario `airflow` y contraseña `airflow`.', '`airflow dags list` incluye `retencion_lote`; `list-import-errors` no da nada.']) + si_falla(['`docker compose logs airflow`.', '`permission denied` sobre el socket de Docker → `DOCKER_GID` (ver el compose).']) + sin_verificar('Escrito desde la guía oficial, **sin ejecutar**. La guía oficial avisa de que su compose no es para producción.') + cap('airflow-01-dag-en-la-lista.webp'), '1fr 1fr'),
          'Paso tres. Airflow en local con un compose mínimo basado en la guía oficial: un solo contenedor con SQLite. No se ha ejecutado. La captura de la lista de DAGs queda pendiente con su receta.')

    b3 = bloque("airflow dags test retencion_lote")
    b3b = bloque('airflow dags trigger retencion_lote')
    slide('C', 6, 'Paso 4 · dags test, trigger y estados', 'sin verificar', 'Paso 4 · Probar el DAG entero, lanzarlo y mirar sus tareas', dos_columnas(
        codigo('comandos.md · dags test', b3) + codigo('comandos.md · trigger, list-runs y states-for-dag-run', b3b),
        mira(['Las cinco tareas en `success`.', 'En el registro de `resumir`, «Lote de retención · corte 2011-12-10».']) + si_falla(['`ImagePullBackOff` / `pull access denied` → la imagen no existe en el Docker del equipo (paso 2).', 'En Airflow 3, `list-runs` recibe el DAG como argumento.']) + sin_verificar('Opciones de la CLI contrastadas con la referencia de Airflow, **no ejecutadas**.') + cap('airflow-02-grid-run-ok.webp'), '1.05fr .95fr'),
          'Paso cuatro. Dags test ejecuta el DAG entero en el mismo proceso, trigger crea un run de verdad y states for dag run enseña el estado de cada tarea. Ninguno se ha ejecutado aquí; las opciones están contrastadas con la referencia de la CLI de Airflow.')

    # ---------------------------------------------------------------- D · Lanzar
    b4 = bloque('export AIRFLOW_USUARIO=airflow')
    slide('D', 6, 'Paso 5 · lanzar_lote.py', 'cliente de la API REST', 'Paso 5 · Lanzarlo por la API REST: un cliente sin dependencias que devuelve un código de salida', dos_columnas(
        codigo('comandos.md · paso 3 (copia y pega)', b4) + mira(['Una línea por cambio de estado de cada tarea y `Run …: success`.', 'Código 0 correcto · 1 el DAG falló · 2 se agotó la espera · 3 sin conexión o credenciales · 4 DAG en pausa.']) + si_falla(['`401` credenciales · `404` nombre del DAG o versión de la API · conexión rechazada: Airflow no está en marcha.']),
        cap('term-03-lanzar-lote.webp', 470) + sin_verificar('Probado contra un servidor Airflow **de prueba** (`pruebas/airflow_falso.py`), no contra Airflow real. Airflow 2 usa `/api/v1` y Airflow 3 `/api/v2` (con JWT local); en Composer, un token de Google.'), '.9fr 1.1fr'),
          'Paso cinco. El cliente de la API REST. Usa solo la biblioteca estándar, detecta si el servidor habla la versión uno o la dos de la API y devuelve un código de salida: cero si el run acaba bien, uno si falla, dos si se agota la espera, tres si no hay conexión y cuatro si el DAG está en pausa. La captura es contra el servidor de prueba, no contra Airflow real. La documentación de Composer autentica con un token de acceso de Google; el script lo saca de gcloud.')

    slide('D', 4, 'Paso 6 · La interfaz: sin Airflow', 'pestaña Lote', 'Paso 6 · La pestaña «Lote»: si Airflow no responde, lo dice y no simula nada', dos_columnas(
        codigo('Arrancar la interfaz (extra-mcp-notebooks/ui)', 'cd 01-Sesiones/S5-MLOps-y-Operacion/extra-mcp-notebooks/ui\npython app.py') + mira(['Una pestaña nueva, «Lote», junto a «Modelo».', 'Con `AIRFLOW_URL` sin definir: «Sin conexión», cómo arrancar Airflow y el botón desactivado.']) + callout('Los secretos (`AIRFLOW_USUARIO`, `AIRFLOW_CLAVE`, `AIRFLOW_TOKEN`) solo se **leen** del entorno: la página no los pide, no los guarda ni los muestra.'),
        cap('ui-01-sin-airflow.webp', 560), '.8fr 1.2fr'),
          'Paso seis. La pestaña Lote de la interfaz del extra MCP. Si Airflow no responde lo dice claro, explica cómo arrancarlo y no simula ninguna ejecución. Los secretos solo se leen de variables de entorno.')

    slide('D', 4, 'La interfaz: configurar y confirmar', 'AIRFLOW_URL y diálogo propio', 'Conectada: configuración sin secretos, formulario y un diálogo que explica qué lanza y qué no', dos_columnas(
        codigo('Variables (Airflow local)', 'AIRFLOW_URL=http://localhost:8080 AIRFLOW_AUTH=basic AIRFLOW_USUARIO=airflow AIRFLOW_CLAVE=airflow') + mira(['«Conectado · API v1» (o v2) y el nombre del DAG.', 'El formulario: corte, imagen, capacidad y huella opcional.', 'Al pulsar «Lanzar el lote», un **diálogo propio** (nunca `confirm()`): *Esto lanza* y *Esto no hace*.']) + sin_verificar('Las capturas son contra un servidor Airflow **de prueba**, no contra Airflow real.'),
        cap('ui-02-conectado.webp', 330) + cap('ui-03-dialogo.webp', 330), '.8fr 1.2fr'),
          'La interfaz conectada. La configuración se lee del entorno sin mostrar secretos. El botón abre un diálogo propio, nunca confirm del navegador, que explica qué lanza: un run del DAG y un contenedor que puntúa a todos los clientes, y qué no hace: no entrena, no mueve el alias champion, no toca la referencia de producción y no escribe fs produccion.')

    slide('D', 4, 'La interfaz: el run en vivo', 'estado de cada tarea', 'El run en vivo: cada tarea con su estado, el registro y el historial', dos_columnas(
        cap('ui-04-en-curso.webp', 380) , cap('ui-05-terminado.webp', 380), '1fr 1fr') + mira(['Sondeo cada 1,5 s del run y de cada tarea; enlace a Airflow para los registros completos.', 'Al terminar: historial de ejecuciones y, si el lote corrió **en este equipo**, el último `campana_*.json` (clientes y tramos). Si corrió en Composer, esa salida no está aquí: se lee en el registro de `resumir`.']),
          'El run en vivo. La interfaz sondea el run y cada tarea cada segundo y medio. El registro que se ve aquí es texto simulado del servidor de prueba. Al terminar se actualiza el historial y el resultado del lote, que solo se lee si el lote corrió en este equipo.')

    slide('D', 4, 'La interfaz: fallo y móvil', 'cuando algo sale mal', 'Cuando falla, lo ves: la tarea en rojo, las demás sin ejecutar y su registro', dos_columnas(
        cap('ui-06-fallo.webp', 400), cap('ui-07-movil.webp', 400), '1.4fr .6fr') + callout('Todo con `playwright` (Chromium propio, 1440×900 y 390×844) contra el servidor de prueba. **Las pruebas de la interfaz** (`ui/pruebas`) cubren lanzar, seguir, fallo, pausa, autenticación, secretos y confirmación obligatoria.'),
          'Un run fallido y la versión móvil. El servidor de prueba falla en ejecutar lote cuando la imagen se llama dos puntos falla; las tareas siguientes quedan como no llegó a ejecutarse. En móvil no hay desplazamiento horizontal.')

    # ---------------------------------------------------------------- E · Composer
    slide('E', 5, 'Paso 7 · Composer en la consola', 'solo lectura', 'Paso 7 · Así se ve Cloud Composer por dentro de la consola: sin API no hay entornos que ver', dos_columnas(
        cap('gcp-01-composer-api.webp', 360), cap('gcp-02-artifact-registry.webp', 360), '1fr 1fr') + mira(['Cloud Composer pide **habilitar su API** antes de enseñar nada: aquí **no se habilitó** (no hace falta para entender el flujo).', 'Artifact Registry está **vacío**: ahí se subirá `retencion-lote`.']) + callout('Solo lectura: se visitaron las dos pantallas y **no se creó ni se habilitó nada**. La lista de entornos solo se ve completa creando uno (cuesta dinero), por eso está como captura pendiente.'),
          'Las dos pantallas de la consola de Google Cloud, en solo lectura. Cloud Composer pide habilitar su API antes de enseñar nada y no se habilitó. Artifact Registry está vacío todavía. No se creó ni se habilitó ningún recurso.')

    b5 = bloque('gcloud composer environments create')
    b5b = bloque('gcloud composer environments storage dags import --environment $ENTORNO --location $REGION --source=$EXTRA/dags/lote_logica.py')
    b5c = bloque('gcloud auth configure-docker')
    slide('E', 6, 'Paso 8 · Entorno, DAG e imagen', 'sin verificar', 'Paso 8 · Crear el entorno, subir el DAG y subir la imagen a Artifact Registry', dos_columnas(
        codigo('comandos.md · crear el entorno', b5) + codigo('comandos.md · subir los DAG a /dags', b5b) + codigo('comandos.md · la imagen a Artifact Registry', b5c),
        mira(['`gcloud composer environments list --locations $REGION` muestra el entorno en `RUNNING` (~25 minutos).', '`dags list` incluye `retencion_lote` (Airflow tarda 1-2 minutos en verlo).']) + si_falla(['`PERMISSION_DENIED` → faltan roles; `API not enabled` → el primer comando.', 'Si el DAG no aparece, mira los errores de importación en la interfaz de Airflow.']) + sin_verificar('**Crear un entorno cuesta dinero** y no se creó ninguno. Tiempo: «aproximadamente 25 minutos» según la documentación; coste: sin dato aquí.') + cap('composer-01-entornos.webp'), '1.05fr .95fr'),
          'Paso ocho. Crear el entorno, subir los dos archivos del DAG a la carpeta dags del bucket y subir la imagen a Artifact Registry. Nada de esto se ha ejecutado: crear un entorno cuesta dinero, tarda unos veinticinco minutos según la documentación y aquí no se cita ninguna cifra de coste. Acuérdese de borrarlo al terminar.')

    b6 = bloque('gcloud composer environments run $ENTORNO --location $REGION dags trigger')
    b6b = bloque('export AIRFLOW_URL=')
    slide('E', 6, 'Paso 9 · Lanzarlo en Composer', 'sin verificar', 'Paso 9 · Lanzar el DAG en Composer: con gcloud o por la API REST', dos_columnas(
        codigo('comandos.md · gcloud composer environments run', b6) + codigo('comandos.md · la API REST', b6b) + codigo('comandos.md · borrar el entorno', bloque('gcloud composer environments delete')),
        mira(['`trigger` devuelve el run; `list-runs` pasa de `running` a `success`; `states-for-dag-run` lista las cinco tareas.', 'Con la API: lo mismo que en el paso 5.']) + si_falla(['`ImagePullBackOff` en `ejecutar_lote` → la cuenta de servicio del entorno no lee Artifact Registry o la etiqueta no existe.', '`403` → falta rol de Airflow/IAM.']) + sin_verificar('Patrón de `gcloud composer environments run … -- …` y URL con `config.airflowUri` tomados de la documentación de Composer, **no ejecutados**.') + cap('composer-03-run.webp'), '1.05fr .95fr'),
          'Paso nueve. Lanzar el DAG en Composer con gcloud composer environments run, donde los argumentos del DAG van después de los dos guiones, o con la API REST usando la URL que devuelve config punto airflowUri. Está sin verificar. Al final, borre el entorno.')

    # ---------------------------------------------------------------- F · Actions
    slide('F', 4, 'La propuesta de Actions', 'tres workflows', 'GitHub Actions: lanzar con aprobación, subir el DAG tras las pruebas y ensayar sin Composer', '<div class="card">' + tabla(['Workflow', 'Qué hace', 'Estado'], [
        ['`lote-composer.yml`', 'Formulario (corte, imagen, capacidad) → **aprobación** en `produccion` → WIF sin claves → URL de Airflow → `lanzar_lote.py --auth google` → resumen; **falla si el DAG falla**', 'Sin ensayar'],
        ['`dags-composer.yml`', 'Al cambiar `dags/**`: pruebas → (con aprobación) sube a `/dags` y espera a que Airflow vea el DAG', 'Sin ensayar'],
        ['`ensayo-airflow.yml`', 'Sin Composer: construye las imágenes en el runner, instala Airflow con las restricciones oficiales y ejecuta `airflow dags test`', 'Sin ensayar']]) + '</div>' + dos_columnas(
        card('Variables de GitHub (no secretos)', ['`GCP_PROYECTO`, `GCP_PROVEEDOR_WIF`, `COMPOSER_CUENTA`', '`COMPOSER_ENV`, `COMPOSER_REGION`, y `LOTE_IMAGEN` (opcional)', 'Environment `produccion` con revisores, como en S4.']),
        card('Lo que comparten con S4', ['`permissions: contents: read`; `id-token: write` solo en el job que entra en Google.', '`concurrency` propio y las entradas validadas a mano antes de usarlas.', 'No se instalan en `.github/workflows/` de este repo: se **copian** al fork.']), '1fr 1fr') + sin_verificar('Los tres están escritos y probados como **texto** (YAML, permisos, WIF, entradas). **Ninguno se ha ejecutado en Actions.**'),
          'La propuesta de GitHub Actions. Tres workflows: lote composer, con formulario y aprobación del environment produccion, que entra en Google Cloud sin claves y lanza el DAG por la API; dags composer, que sube el DAG tras pasar las pruebas; y ensayo airflow, que ejecuta el DAG con airflow dags test en el runner para poder ensayar sin pagar un entorno. Los tres se probaron como texto; ninguno se ejecutó en Actions.')

    slide('F', 5, 'Así luce Actions hoy', 'capturas de OTROS workflows', 'Cómo lucen en GitHub los workflows que ya existen: lista, un run terminado con su resumen', dos_columnas(
        cap('gh-01-actions-lista.webp', 330) + cap('gh-03-puntuar-lote-resumen.webp', 330),
        cap('gh-02-nueva-version-runs.webp', 330) + callout('Todo **solo lectura**, de workflows de **S4**: `lote-composer.yml` aún no está en el repositorio. No se pulsó Run, Approve, Merge ni Delete. Los workflows de ensayo viven en ramas `lab/`, por eso la rama por defecto no ofrece el botón «Run workflow».'), '1fr 1fr'),
          'Capturas de GitHub en solo lectura, de otros workflows que ya existen: la lista de Actions, una lista de runs y un run terminado de puntuar lote con su Job Summary. El workflow de este extra todavía no está en el repositorio. No hay botón Run workflow porque los workflows de ensayo están en ramas lab y no en la rama por defecto.')

    slide('F', 4, 'Aprobación y variables', 'environment y variables de Actions', 'Lo que ya está configurado: el environment «produccion» y las variables GCP_*', dos_columnas(
        cap('gh-04-environments.webp', 330), cap('gh-05-variables.webp', 330), '1fr 1fr') + mira(['El environment `produccion` ya existe con una regla de protección: los dos workflows nuevos lo reutilizan para **esperar aprobación**.', 'Las variables `GCP_PROYECTO`, `GCP_PROVEEDOR_WIF`… ya están (valores difuminados). **Hay que añadir** `COMPOSER_ENV`, `COMPOSER_REGION` y `COMPOSER_CUENTA` (y `LOTE_IMAGEN` si quieres).']),
          'El environment produccion y las variables de GCP ya existen del laboratorio de S4. Para los workflows de este extra hay que añadir las variables de Composer. Capturas de solo lectura, con los valores difuminados.')

    slide('F', 5, 'lote-composer.yml', 'el workflow que lo lanza', 'lote-composer.yml: aprobación, entrada sin claves y falla si el DAG falla', dos_columnas(
        codigo('lote-composer.yml · el trabajo «lanzar»', trozo(wf, '  lanzar:', None)),
        mira(['Run workflow pide corte, imagen y capacidad; el job «lanzar» **espera la aprobación**.', 'La página del run trae la tabla de tareas y el registro de `resumir`.']) + si_falla(['`::error::El entorno no devolvió config.airflowUri` → no existe o no está en marcha.', 'Run en rojo con `failed` → mira el registro de la tarea que imprime el propio script.']) + cap('actions-01-run-workflow.webp', 240), '1.1fr .9fr'),
          'El workflow que lanza el lote. El job lanzar para en el environment produccion hasta que un revisor lo aprueba, entra en Google Cloud con Workload Identity Federation, pregunta a Composer la URL de su Airflow y ejecuta lanzar lote punto py, que escribe el resumen en la página del run y sale con código distinto de cero si el DAG falla. Sin ensayar.')

    slide('F', 5, 'dags-composer.yml y ensayo', 'subir el DAG y ensayar sin Composer', 'Subir el DAG tras las pruebas, y un ensayo honesto sin Composer', dos_columnas(
        codigo('dags-composer.yml · subir', trozo(wd, '      - name: Subir los DAG', '      - name: Esperar')) + codigo('ensayo-airflow.yml · airflow dags test', trozo(we, '      - name: Ejecutar el DAG entero', None)),
        card('El ensayo sin Composer', ['Rama `lab/composer/…` que cambie el DAG, o Run workflow.', 'Receta exacta en el README: «Ensayo en Actions».', 'Debes ver `list-import-errors` sin errores y las tareas en `success`.']) + sin_verificar('**Sin ensayar.** Se espera hasta que el profesor autorice el push a una rama `lab/`.') + cap('actions-04-ensayo-airflow.webp', 200), '1.1fr .9fr'),
          'Subir el DAG y ensayar sin Composer. Dags composer sube los dos archivos con gcloud y espera con reintentos a que Airflow vea el DAG. Ensayo airflow ejecuta airflow dags test en el runner con DockerOperator. Los dos están sin ensayar; la receta para ensayarlos en una rama lab está en el README.')

    # ---------------------------------------------------------------- G · Cierre
    slide('G', 5, 'Qué quedó sin verificar', 'honestidad', 'Qué se ejecutó de verdad y qué quedó sin verificar', dos_columnas(
        '<div class="card">' + tabla(['Ejecutado', 'Cómo'], [
            ['El lote real y su validación', 'Copia de `curso.db`; repositorio intacto (hashes)'],
            ['El DAG: AST y estructura', 'Airflow *de cartón* (2 y 3) en las pruebas'],
            ['`lanzar_lote.py` y la pestaña Lote', 'Servidor Airflow **falso**'],
            ['Los YAML', 'Pruebas de texto: permisos, WIF, entradas']]) + '</div>' + cap('term-05-pytest-extra.webp', 200),
        '<div class="card">' + tabla(['Sin verificar', 'Para hacerlo'], [
            ['El DAG en Airflow real', 'Pasos 3-4 (Docker) o Actions «ensayo»'],
            ['`lote.Dockerfile`, el compose', 'Paso 2-3 con Docker'],
            ['Composer, Artifact Registry, IAM', 'Pasos 7-9 (cuesta dinero)'],
            ['Los workflows en Actions', 'Rama `lab/`, con autorización']]) + '</div>' + cap('term-06-pytest-ui.webp', 200), '1fr 1fr'),
          'Qué se ejecutó y qué no. Lo ejecutado: el lote real, el DAG como estructura, el cliente y la interfaz contra un Airflow de prueba, los YAML como texto. Sin verificar: el DAG en un Airflow real, las imágenes, Composer y los workflows en Actions. Las capturas pendientes están listadas en capturas pendientes punto md.')

    slide('G', 4, 'Costes y limpieza', 'sin cifras inventadas', 'Costes: un entorno de Composer cuesta mientras exista, y esto no creó ninguno', f'''
<div class="grid2">
 {card('Lo que dice la documentación', ['Crear un entorno: «aproximadamente 25 minutos».', 'Precio: sin dato en esta presentación; **consulta la página de precios** de Composer.', 'Los DAG tardan 1-2 minutos en aparecer tras subirlos.'])}
 {card('Antes de crear nada', ['Avisa al profesor: **cuesta dinero** y la cuenta del curso tiene presupuesto.', 'Bórralo al terminar: `gcloud composer environments delete`.', '¿Un único lote diario? Un Cloud Run Job o `puntuar-lote.yml` salen mucho más baratos.'])}
</div>
{callout('**En este extra no se creó ningún recurso en Google Cloud y no se habilitó ninguna API**: las dos capturas de la consola son de solo lectura.')}''' + fuente('<https://docs.cloud.google.com/composer/docs/composer-3/create-environments>.'),
          'Costes. Un entorno de Composer cuesta mientras exista y tarda unos veinticinco minutos en crearse según la documentación. No se cita ninguna cifra porque la documentación consultada no la daba en esa página. En este extra no se creó ningún recurso ni se habilitó ninguna API.')

    slide('G', 4, 'Resumen', 'lo que debes recordar', 'Resumen: el orquestador no cambia el lote; lo hace repetible, visible y con botón', f'''
<div class="grid3">
 {card('Lo que construiste', ['Un **DAG** de cinco tareas con dos operadores.', 'Un **cliente REST** y una **pestaña Lote**.', 'Tres **workflows** copiables.'])}
 {card('Lo que debes recordar', ['La imagen de la API **no** puede correr el lote sola: lleva el modelo, no los datos.', 'Valida la salida **dentro del DAG**; un run en verde con datos malos no sirve.', 'Aprobación en `produccion` antes de tocar la nube.'])}
 {card('Lo que falta', ['Ejecutarlo en un **Airflow real**.', 'Hacer las **capturas pendientes** (`capturas-pendientes.md`).', 'Ensayar los workflows en una rama `lab/`.'])}
</div>''' + fuente('README.md y comandos.md de este extra.'),
          'Resumen. El orquestador no cambia lo que hace el lote, lo hace repetible, visible y con un botón. Recuerde que la imagen de la API no puede correr el lote sola, que hay que validar la salida dentro del DAG y que la nube se toca solo tras una aprobación. Lo que falta: ejecutarlo en un Airflow real y hacer las capturas pendientes.')



# ==================================================================================================================================
# Marco: CSS y JavaScript del visor, copiados del extra MCP de S5
# ==================================================================================================================================
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
  f.innerHTML=`<span>ML e IA · S5 · Extra: lote con Airflow / Composer</span><span><b>${esc(PARTES[s.dataset.part]||'')}</b> · ${i+1} / ${N}</span>`;s.appendChild(f)});
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
.pend ol{text-align:left;margin:4px 0 0;padding-left:22px}
"""
CSS = CSS + EXTRA_CSS


def html_completo():
    construir()
    js = JS.replace('__PARTES__', json.dumps(PARTES, ensure_ascii=False))
    partes = ''.join(f'<button class="part" data-p="{k}">{esc(v)}</button>' for k, v in PARTES.items())
    return ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>Extra de S5: lote con Airflow en Cloud Composer · ML e IA: de desarrollo a producción</title>\n'
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
            '<noscript>Esta presentación necesita JavaScript. El mismo contenido está en README.md y comandos.md de esta carpeta.</noscript>\n\n'
            f'<script>{js}</script>\n</body>\n</html>\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--comprobar', action='store_true')
    a = ap.parse_args()
    nuevo = html_completo()
    actual = SALIDA.read_text(encoding='utf-8') if SALIDA.exists() else None
    pendientes = [n for n in CAPTURAS if not (AQUI / 'img' / n).is_file()]
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
