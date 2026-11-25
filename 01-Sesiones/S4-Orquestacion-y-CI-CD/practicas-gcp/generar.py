"""Genera la presentación «Prácticas en Google Cloud: del contenedor al LLM, paso a paso» (index.html, junto a este archivo).

Son las cinco prácticas de S4 del curso «ML e IA: de desarrollo a producción» (carpetas 01 a 05 de esta misma carpeta), contadas
para el ALUMNO paso a paso: qué se aprende, qué crea, las órdenes para copiar y pegar (todas en Cloud Shell, desde la carpeta de
la práctica), qué debes ver (con la salida y la captura reales del 25/11/2026), qué hacer si falla (con los fallos que de verdad
tuvimos) y cómo borrarlo todo.

El visor (CSS y JavaScript: ← → · O índice · S notas · F pantalla completa · Esc · botón ⧉ «Copiar todo» · lupa con zoom al clic ·
pie «x / total» · recuadro «Captura pendiente» si falta una imagen) es EL MISMO que el del laboratorio Cloud Journey: se importa
de ../laboratorio-cloud-journey/generar.py para que no se desvíen. Las capturas se leen de img/ (webp).

Uso:  python generar.py              escribe index.html
      python generar.py --comprobar  no escribe; sale con 1 si index.html no está al día
"""
import argparse
import html
import importlib.util
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / 'index.html'

_spec = importlib.util.spec_from_file_location('generar_cloud_journey_visor', AQUI.parent / 'laboratorio-cloud-journey' / 'generar.py')
_CJ = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_CJ)
CSS, EXTRA_CSS, LUPA = _CJ.CSS, _CJ.EXTRA_CSS, _CJ.LUPA
_PIE_ORIGINAL = 'ML e IA · S4 · Laboratorio Cloud Journey'
assert _PIE_ORIGINAL in _CJ.JS, 'el visor del Cloud Journey ha cambiado: revisa el pie'
JS = _CJ.JS.replace(_PIE_ORIGINAL, 'ML e IA · S4 · Prácticas en Google Cloud')

FECHA = '25/11/2026'
USUARIO = 'helicr'
REPO = 'curso-ml-ia-desarrollo-produccion'
CARPETA = '01-Sesiones/S4-Orquestacion-y-CI-CD/practicas-gcp'
PROYECTO = 'project-curso-ml-ia'
REGION = 'southamerica-west1'
FUENTE_CREDITO = 'https://docs.cloud.google.com/free/docs/free-cloud-features'
PRACTICAS = ['01-docker-artifact-registry', '02-kubernetes-gke', '03-dataproc-spark', '04-vertex-modelo', '05-vertex-llm']

# Capturas (webp) -> qué se ve de verdad (texto alternativo y pie).
CAPTURAS = {
    'gcp-30-clonar.webp': 'Cloud Shell con el proyecto project-curso-ml-ia: la orden «git clone -q --depth 1 -b lab/practicas-gcp» del repositorio helicr/curso-ml-ia-desarrollo-produccion y el listado de la carpeta practicas-gcp (01-docker-artifact-registry, 02-kubernetes-gke, 03-dataproc-spark, 04-vertex-modelo, 05-vertex-llm, borrar-todo.sh, clientes_ejemplo.json, comun.sh, pruebas y README.md), seguido de «Python 3.12.3»',
    'gcp-p01-crear.webp': 'Final de «bash crear.sh» de la práctica 01: las capas de la imagen en «Pushed», «v1: digest: sha256:9d6cea90… size: 856», «Deploying container to Cloud Run service [retencion-api-practica] … region [southamerica-west1]», «has been deployed and is serving 100 percent of traffic», «Service URL: https://retencion-api-practica-61343545797.southamerica-west1.run.app» y «Listo. Ahora: ./probar.sh»',
    'gcp-p01-probar.webp': 'Salida de «bash probar.sh» de la práctica 01: /salud {"estado":"ok"}, /listo {"estado":"listo"}, la ficha de /modelo (regresion_logistica, huella_datos 35a94deb4e04ab4a, scikit-learn 1.9.1), POST /predecir con probabilidad 0.8278889191932244 y «OK: probabilidad de recompra a 90 dias = 0.828», código 422 con un campo inventado, código 403 sin token («OK: privado») y las últimas líneas del registro',
    'gcp-p01-borrado.webp': 'Final de «bash borrar.sh» de la práctica 01, ejecutado desde la carpeta de la 02: el único repositorio de Artifact Registry que queda es «curso» (el del Cloud Journey: 174.801 MB, creado el 2026-11-25), no el de la práctica; la descripción «Imgenes del curso ML e IA» enseña las tildes que se perdieron al teclear',
    'gcp-p02-crear2.webp': 'Final de «bash crear.sh» de la práctica 02 tras el arreglo: clúster en STATUS RUNNING (versión 1.36.4-gke.2377000), «kubeconfig entry generated for curso-ml-gke», namespace, deployment y service «created», «deployment "retencion-api" successfully rolled out», un pod 1/1 Running y el servicio de tipo ClusterIP con EXTERNAL-IP <none>',
    'gcp-p02-probar.webp': 'Salida de «bash probar.sh» de la práctica 02: /listo {"estado":"listo"}, probabilidad 0.8278889191932244 («OK … 0.828»), «deployment.apps/retencion-api scaled» con dos pods 1/1 Running, un pod borrado y de nuevo dos pods Running («OK: 2 replicas listas otra vez.») y las líneas JSON del registro de un pod',
    'gcp-p02-borrado.webp': 'Final de «bash borrar.sh» de la práctica 02: «Deleted [… clusters/curso-ml-gke]», quitados los roles roles/container.defaultNodeServiceAccount y roles/artifactregistry.reader, «deleted service account [sa-gke-nodos@project-curso-ml-ia.iam.gserviceaccount.com]» y, en «Lo que queda», «Listed 0 items.» dos veces',
    'gcp-p03-crear2.webp': 'Final de «bash crear.sh» de la práctica 03 (se lanzó con «sleep 120;» delante: la espera que ahora hace el propio script): cinco filas del RFM que imprime Spark, «Batch [curso-ventas-20261125-021646] finished.», sus metadatos (southamerica-west1, etiqueta curso: ml-ia) y «Listo (lote curso-ventas-20261125-021646)»',
    'gcp-p03-probar.webp': 'Final de «bash probar.sh» de la práctica 03: tres filas del RFM, «== Paridad: Spark frente a un calculo local con Python estandar» y «OK: 9 paises; facturas, clientes y monto coinciden con el calculo local.»',
    'gcp-p03-borrado.webp': 'Salida de «bash borrar.sh» de la práctica 03: se borran del bucket salida/por_pais (el CSV y _SUCCESS) y job/analisis_ventas.py, «Removing buckets», «Quitado roles/dataproc.worker» a la cuenta de Compute, «Listed 0 items.» y «(ningun bucket project-curso-ml-ia-curso-ml-dataproc)»',
    'gcp-p04-crear.webp': 'Salida de «bash crear.sh» de la práctica 04: «AUC valid del modelo del proyecto (scikit-learn 1.9.1): 0.6982», las 13 variables en orden, activo con probabilidad local 0.8279 y clase 1, dormido con 0.2760 y clase 0, el bucket y model.joblib, «Created Vertex AI endpoint … retencion-90d-endpoint», «Deployed a model to the endpoint» y «Listo. Ahora: ./probar.sh y, SIN DEJARLO PARA DESPUES: ./borrar.sh»',
    'gcp-p04-probar.webp': 'Salida de «bash probar.sh» de la práctica 04: la petición {"instances": [[13 números], [13 números]]}, la respuesta de «gcloud ai endpoints predict» con "predictions": [1, 0], modelo retencion-90d-sklearn, y la comparación «activo Vertex (clase) = 1 | local: probabilidad 0.8279, clase 1 -> OK» y «dormido Vertex (clase) = 0 | local: probabilidad 0.2760, clase 0 -> OK», con la nota de que el contenedor devuelve la CLASE',
    'gcp-p04-borrado.webp': 'Salida de «bash borrar.sh» de la práctica 04: se borra model.joblib y el bucket gs://project-curso-ml-ia-curso-ml-vertex, se quita el entorno scikit-learn 1.6 y, en «Lo que queda», «Listed 0 items.» dos veces (endpoints y modelos) y «(ningun bucket project-curso-ml-ia-curso-ml-vertex)»',
    'cj-06-vertex-modelo.webp': 'Consola de Google Cloud, Plataforma de Gemini › Modelos › Registro de modelos, región southamerica-west1 (Santiago): un modelo cuyo nombre se corta en «retencion-» (es retencion-90d-sklearn), versión predeterminada 1, estado Implementado, tipo Importado y origen Entrenamiento personalizado',
    'cj-07-vertex-endpoint.webp': 'Consola de Google Cloud, Plataforma de Gemini › Modelos › Extremos (los endpoints), región southamerica-west1 (Santiago): el extremo retencion-90d-endpoint en estado Activo, con 1 modelo y supervisión Inhabilitada',
    'gcp-p05-probar.webp': 'Salida de crear.sh y probar.sh de la práctica 05: «google-genai 3.6.1», los hechos del modelo (monto_total 1250.4 sube 0.19, frecuencia_90d 2 sube 0.105, antiguedad_dias 310 baja -0.085), «Llamando a gemini-3.1-flash-lite en Vertex AI (ubicación: global)», la explicación de Gemini («probabilidad del 82.79% … tramo de probabilidad alta»), «Tokens: entrada=388 salida=171» y el AVISO falso de que el texto no cita el 82.8 %',
}

# Órdenes que se copian (clave -> orden). Todas, en Cloud Shell.
O = {
    'usuario_gh': 'USUARIO_GH=tu-usuario-de-github',
    'cd_home': 'cd ~',
    'clonar': f'git clone -q --depth 1 -b develop https://github.com/$USUARIO_GH/{REPO}.git curso',
    'cd_practicas': f'cd ~/curso/{CARPETA}',
    'ls': 'ls',
    'proyecto': f'gcloud config set project {PROYECTO}',
    'cd_01': f'cd ~/curso/{CARPETA}/{PRACTICAS[0]}',
    'cd_02': f'cd ~/curso/{CARPETA}/{PRACTICAS[1]}',
    'cd_03': f'cd ~/curso/{CARPETA}/{PRACTICAS[2]}',
    'cd_04': f'cd ~/curso/{CARPETA}/{PRACTICAS[3]}',
    'cd_05': f'cd ~/curso/{CARPETA}/{PRACTICAS[4]}',
    'crear': 'bash crear.sh',
    'probar': 'bash probar.sh',
    'borrar': 'bash borrar.sh',
    'k_ver': 'kubectl -n curso get deployment,pods,svc',
    'cd_01_desde_02': f'cd ../{PRACTICAS[0]}',
    'borrar_todo': 'bash borrar-todo.sh',
}

PARTES = {'A': 'Preparar', 'B': 'Práctica 1', 'C': 'Práctica 2', 'D': 'Práctica 3', 'E': 'Práctica 4', 'F': 'Práctica 5', 'G': 'Cierre'}
NOMBRES_PARTE = {'A': 'Antes de empezar', 'B': 'Práctica 1: Docker, Artifact Registry y Cloud Run', 'C': 'Práctica 2: Kubernetes en GKE Autopilot',
                 'D': 'Práctica 3: PySpark con Dataproc sin servidor', 'E': 'Práctica 4: el modelo en Vertex AI',
                 'F': 'Práctica 5: Gemini explica la predicción', 'G': 'Borrar, costes y cierre'}


def esc(t):
    return html.escape(t, quote=True)


def md(t):
    """`código` y **negrita** a HTML (sobre texto ya seguro)."""
    t = esc(t)
    t = re.sub(r'`([^`]+)`', r'<span class="mono">\1</span>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', t)
    return re.sub(r'(?<![\w*])\*([^*\s][^*]*)\*(?![\w*])', r'<i>\1</i>', t)


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


def cap(nombre, alto=None, nota=None, titulo=None):
    """Una captura (clic = ampliar) o, si aún no está en img/, el recuadro «Captura pendiente»."""
    if not nombre.endswith('.webp'):
        nombre += '.webp'
    alt = CAPTURAS[nombre]
    estilo = f' style="max-height:{alto}px"' if alto else ''
    extra = f'<br><span class="nota">{md(nota)}</span>' if nota else ''
    if (AQUI / 'img' / nombre).is_file():
        return (f'<figure class="cap" data-img="{nombre}"><button class="zoom" data-src="img/{nombre}" data-alt="{esc(alt)}" title="Ampliar (Esc cierra)">'
                f'<img src="img/{nombre}" alt="{esc(alt)}"{estilo}><span class="lupa">{LUPA} Ampliar</span></button>'
                f'<figcaption><span class="tag ok">Captura real</span> {md(titulo) if titulo else esc(alt)}{extra}</figcaption></figure>')
    alto_p = f' style="min-height:{min(alto or 200, 260)}px"' if alto else ''
    return (f'<figure class="cap" data-img="{nombre}"><div class="pend"{alto_p}><b>Captura pendiente</b><span class="mono">img/{nombre}</span>'
            f'<span>{esc(alt)}</span></div><figcaption><span class="tag warn">Pendiente</span> {esc(alt)}</figcaption></figure>')


def lista(items):
    return '<ul class="list">' + ''.join(f'<li>{md(i)}</li>' for i in items) + '</ul>'


def card(titulo, items):
    return f'<div class="card"><h3>{esc(titulo)}</h3>{lista(items)}</div>'


def mira(items, titulo='Qué debes ver'):
    return f'<div class="card mira"><h3>{esc(titulo)}</h3>{lista(items)}</div>'


def si_falla(items, titulo='Si falla'):
    return f'<div class="card falla"><h3>{esc(titulo)}</h3>{lista(items)}</div>'


def tabla(cab, filas, clase=''):
    th = ''.join(f'<th>{md(c)}</th>' for c in cab)
    tr = ''.join('<tr>' + ''.join(f'<td>{md(c)}</td>' for c in f) + '</tr>' for f in filas)
    return f'<table class="tbl {clase}"><tr>{th}</tr>{tr}</table>'


def kpi(valor, texto, color=''):
    return f'<div class="card kpi"><b class="n {color}">{esc(valor)}</b><p class="small">{md(texto)}</p></div>'


def salida(titulo, texto):
    return f'<div class="realbox"><div class="rk">{esc(titulo)}</div><pre>{esc(texto)}</pre></div>'


def callout(texto, estilo=''):
    return f'<div class="callout"{(" style=" + chr(34) + estilo + chr(34)) if estilo else ""}>{md(texto)}</div>'


SLIDES = []
_N = {}
GRANDES = {'Costes y lecciones', 'Cierre'}


def slide(parte, minutos, titulo, kick, h1, cuerpo, notas):
    n = list(PARTES).index(parte) + 1
    _N[parte] = _N.get(parte, 0) + 1
    antetitulo = f'{n} · {NOMBRES_PARTE[parte]} · {kick}'
    attrs = f' data-part="{parte}" data-min="{minutos}" data-title="{esc(titulo)}"'
    clase = ' grande' if titulo in GRANDES else ''
    SLIDES.append(f'<section class="slide{clase}"{attrs}\n data-notes="{esc(notas)}">\n'
                  f'<p class="kick">{esc(antetitulo)}</p><h1>{md(h1)}</h1>\n{cuerpo}\n</section>')


def pasos(items):
    """Tres tarjetas «1 · Crear / 2 · Probar / 3 · Borrar» con lo que hace cada script de la práctica."""
    return '<div class="grid3" style="margin-top:10px">' + ''.join(
        f'<div class="card"><h3>{esc(t)}</h3><p class="small">{md(c)}</p></div>' for t, c in items) + '</div>'


def dos_columnas(izq, der, proporcion='.75fr 1.25fr'):
    """Dos columnas: órdenes y avisos a la izquierda; la captura a la derecha, con la tarjeta «Qué debes ver» debajo de ella
    (así las dos columnas quedan equilibradas y la salida real se lee junto a la captura)."""
    m = re.search(r'<div class="card mira">.*?</ul></div>', izq, re.S)
    if m:
        izq = izq.replace(m.group(0), '', 1)
        der = der + m.group(0)
    return (f'<div class="split" style="grid-template-columns:{proporcion}"><div class="col">{izq}</div>'
            f'<div class="capcol">{der}</div></div>')


# =====================================================================================================================================
# Contenido
# =====================================================================================================================================
def construir():
    SLIDES.clear()
    _N.clear()

    # ---------------------------------------------------------------- A · Antes de empezar
    slide('A', 3, 'Portada', 'ML e IA: de desarrollo a producción · S4', 'Prácticas en Google Cloud: del contenedor al LLM, paso a paso', f'''
<div class="cover">
 <p class="sub">Cinco prácticas con nuestro caso (la <b>probabilidad de recompra a 90 días</b>): un <b>contenedor en Cloud Run</b>, <b>Kubernetes</b>, <b>Spark sin servidor</b>, <b>el modelo en Vertex AI</b> y <b>Gemini</b>. En todas: <b>crear → probar → borrar</b>.</p>
 <div class="chips"><span class="tag">Caso Online Retail II</span><span class="tag">Cloud Shell</span><span class="tag">Cloud Run</span><span class="tag">GKE Autopilot</span><span class="tag">Dataproc</span><span class="tag">Vertex AI</span><span class="tag">Gemini</span></div>
 <div class="card" style="margin-top:22px"><h3>Cómo seguirlas</h3><p class="small">Cada orden lleva <b>⧉</b> para copiarla y la pegas <b>en Cloud Shell</b>, siempre <b>desde la carpeta de la práctica</b>. Cada práctica se cuenta en cuatro pasos: <b>qué aprendes y qué crea</b>, <b>crear</b>, <b>probar</b> y <b>borrar</b>, con la salida y la captura reales ({FECHA}, cuenta de Google del curso). <b>← →</b> avanzan · <b>O</b> índice · <b>S</b> notas · <b>F</b> pantalla completa · clic en una captura para ampliarla y <b>Esc</b> para cerrarla.</p></div>
 {callout('**Estas prácticas usan tu cuenta de Google Cloud y pueden costar dinero.** Lo que más cobra si se olvida es el **clúster de la práctica 2** y el **endpoint de la práctica 4**: borra cada práctica en cuanto la termines.', 'margin-top:12px')}
</div>''',
          'Presentación para el alumno de las cinco prácticas de Google Cloud de la sesión 4. Todo lo que se enseña se ejecutó de verdad el 25 de noviembre de 2026 en la cuenta de Google del curso, con el proyecto project-curso-ml-ia y la región de Santiago. Lo que no se pudo comprobar se marca como sin verificar. Insista desde el principio en que cuesta dinero si no se borra, y en que el borrado de cada práctica no es opcional.')

    slide('A', 4, 'El plan', 'lo que vas a hacer', 'Cinco prácticas y una regla: crea, prueba y borra', f'''
<div class="grid2" style="grid-template-columns:1.35fr .65fr">
 <div class="card">''' + tabla(['#', 'Práctica', 'Qué aprendes', 'Qué crea (y se borra)'], [
        ['**1**', 'Docker, Artifact Registry y Cloud Run', 'de la imagen a una **URL privada**', 'repositorio `curso-ml-imagenes`, imagen `retencion-api:v1`, servicio `retencion-api-practica`'],
        ['**2**', 'Kubernetes en GKE Autopilot', '**Pod, Deployment y Service**', 'clúster `curso-ml-gke` y la cuenta `sa-gke-nodos`'],
        ['**3**', 'PySpark con Dataproc sin servidor', 'Spark sobre **nuestras ventas**', 'un bucket, un lote y un rol temporal'],
        ['**4**', 'El modelo en Vertex AI', '**registro, endpoint** y predicción online', 'bucket, modelo `retencion-90d-sklearn`, endpoint `retencion-90d-endpoint`'],
        ['**5**', 'Gemini explica la predicción', 'un LLM gestionado que **solo redacta**', 'nada en la nube (solo el SDK en Cloud Shell)']]) + '''</div>
 <div class="col">
  <div class="card"><h3>El orden</h3><ol class="ol sm">
   <li><b>1</b>: crear y probar</li>
   <li><b>2</b>: crear, probar y <b>borrar</b></li>
   <li><b>1</b>: ahora sí, borrar</li>
   <li><b>3</b>, <b>4</b> y <b>5</b>: cada una entera</li></ol></div>
  ''' + callout('La **2** descarga la imagen que sube la **1**: por eso la 1 se borra **después** de la 2.') + '''
 </div>
</div>
<div class="grid3" style="margin-top:10px">
 ''' + card('Dónde', ['Todo en **Cloud Shell** (la terminal de Google en el navegador).', f'Proyecto `{PROYECTO}`, región `{REGION}` (Santiago).']) + card('Sin claves', ['Ninguna clave de cuenta de servicio: la organización lo prohíbe y se usa la **sesión de Cloud Shell**.']) + card('Cada práctica', ['Tres scripts: `crear.sh`, `probar.sh` y `borrar.sh`, que se ejecutan con `bash`.', 'Las APIs activadas **no** se desactivan: no cuestan.']) + '''
</div>''',
          'Mapa de las cinco prácticas. La regla es crear, probar y borrar. La práctica 2 necesita la imagen de la 1, así que el orden recomendado para pagar lo mínimo es: 1 crear y probar, 2 crear probar y borrar, 1 borrar, y después 3, 4 y 5 cada una entera. Si algo se queda sin borrar, existe el script borrar-todo.sh, que se ve al final. No se usan claves de cuentas de servicio.')

    slide('A', 5, 'Abrir Cloud Shell y clonar', 'paso 0 · en la consola y en Cloud Shell', 'Abre Cloud Shell y trae las prácticas a tu carpeta personal', f'''
<div class="split" style="grid-template-columns:1.05fr .95fr">
 <div class="col">''' + term('Cloud Shell · una orden cada vez', [
        '# 1) tu usuario de GitHub (el de tu fork del curso)', O['usuario_gh'], O['cd_home'], O['clonar'],
        '# 2) entra en la carpeta de las prácticas y mira qué hay', O['cd_practicas'], O['ls'],
        '# solo si el prompt no muestra tu proyecto entre paréntesis', O['proyecto']]) + '''
 </div>
 <div class="col">
  <div class="card"><h3>Dónde: la consola de Google Cloud</h3><ol class="ol sm">
   <li>Entra con la cuenta de Google del curso y comprueba arriba tu <b>proyecto</b></li>
   <li>Pulsa el icono <b>&gt;_</b> (Activar Cloud Shell), arriba a la derecha</li>
   <li>Espera al prompt y pega las órdenes de la izquierda</li></ol></div>
  ''' + mira([
        '`ls` enseña `01-docker-artifact-registry` … `05-vertex-llm`, `borrar-todo.sh`, `clientes_ejemplo.json`, `comun.sh`, `pruebas` y `README.md`.',
        'El prompt lleva tu proyecto entre paréntesis y en amarillo.']) + si_falla([
        '`Remote branch develop not found` o `Repository not found`: tu fork no tiene `develop` o escribiste mal el usuario.',
        '`destination path \'curso\' already exists`: ya lo clonaste; haz `cd ~/curso` y `git pull`.']) + f'''
 </div>
</div>
{cap('gcp-30-clonar', 70, 'Es la captura del profesor: clonó la rama `lab/practicas-gcp` y tú clonas `develop` (con un fork propio: **sin verificar**). El «__FIN_…» del final lo añadió la herramienta que tecleó la orden; tú no lo verás.', 'La orden de clonado y el listado de la carpeta de las prácticas (Cloud Shell trae Python 3.12.3: hace falta 3.11 o superior)')}''',
          'Cada alumno abre Cloud Shell desde la consola de Google Cloud y clona su fork del curso en la rama develop. La captura es la del profesor, que clonó la rama de trabajo de las prácticas; con un fork de alumno no se ha probado y se dice con claridad. Cloud Shell trae Python 3.12.3, y los scripts piden 3.11 o superior. Los scripts de cada práctica fijan el proyecto, así que la orden de gcloud config solo hace falta si el prompt no lo muestra.')

    # ---------------------------------------------------------------- B · Práctica 1
    slide('B', 4, 'Práctica 1: qué aprendes', 'qué aprendes y qué crea', 'De una imagen Docker a una URL privada en Cloud Run', '''
<div class="grid2">
 <div class="col">''' + card('Qué aprendes', [
        '**Imagen frente a contenedor**: la imagen es la receta; el contenedor, la receta en marcha.',
        'Un **registro de imágenes** (Artifact Registry) es el almacén de Google, el equivalente de GHCR.',
        'Una **etiqueta fija** (`v1`), nunca `latest`: así sabes qué versión corre.',
        'Un servicio **privado**: solo entra quien demuestra su identidad, sin claves.',
        'Cloud Run **escala a cero**: sin llamadas, no hay nada encendido.']) + callout('Es la **misma imagen** de la API de retención de S2: aquí solo cambia **dónde corre**.') + '''
 </div>
 <div class="col">
  <div class="card"><h3>Qué crea</h3>''' + tabla(['Recurso', 'Nombre'], [
        ['Repositorio Docker de Artifact Registry', '`curso-ml-imagenes`'],
        ['Imagen', f'`{REGION}-docker.pkg.dev/{PROYECTO}/curso-ml-imagenes/retencion-api:v1`'],
        ['Servicio de Cloud Run (privado, 0 a 1 instancias, 1 GiB)', '`retencion-api-practica`']]) + '''</div>
  ''' + card('Antes de empezar', [
        'Tiempo estimado **20-30 min** (estimado, sin medir): el `docker push` de la imagen es lo más lento.',
        'Coste: **sin dato**. Con 0 instancias en reposo no hay instancia cobrando; sí hay almacenamiento de la imagen mientras exista.',
        'Se llama `retencion-api-practica` y no `retencion-api` para **no pisar** el servicio del Cloud Journey.']) + '''
 </div>
</div>''' + pasos([
        ('1 · Crear', '`bash crear.sh`: construye la imagen, la sube a Artifact Registry y despliega el servicio privado.'),
        ('2 · Probar', '`bash probar.sh`: llama a la API con tu identidad y comprueba los códigos 200, 422 y 403.'),
        ('3 · Borrar', '`bash borrar.sh`, pero **después de la práctica 2**, que descarga esta imagen.')]),
          'Primera práctica: llevar la API de retención, con la misma imagen del Dockerfile del proyecto, a Artifact Registry y a Cloud Run como servicio privado. Se construye en Cloud Shell, se sube con la etiqueta fija v1 y se despliega con cero instancias en reposo y una como máximo. El servicio se llama retencion-api-practica para no pisar el del laboratorio Cloud Journey. El tiempo es una estimación y el coste no se ha medido.')

    slide('B', 7, 'Práctica 1: crear', 'paso 1 · en Cloud Shell', 'Crea el repositorio, sube la imagen y despliega el servicio', dos_columnas(
        term('Cloud Shell · carpeta de la práctica 1', [O['cd_01'], O['crear']]) + mira([
            'Habilita las APIs, **genera el modelo** si falta (la primera vez tarda), construye la imagen con `docker build`, la **sube** (`docker push`) y despliega.',
            'Las líneas «**Pushed**» y un `v1: digest: sha256:… size: 856`.',
            'Al final: «**Service URL: https://retencion-api-practica-…run.app**» y «Listo. Ahora: ./probar.sh».']) + si_falla([
            '**Visto:** al teclear la descripción del repositorio desde otra herramienta se perdieron las tildes («Imgenes»). Escribe las descripciones de `gcloud` **sin tildes**.',
            '**Posible, sin verificar:** `docker: command not found` (reinicia Cloud Shell) o `denied: Permission … uploadArtifacts` (pide `roles/artifactregistry.writer`).']),
        cap('gcp-p01-crear', 400, None, 'El final de `crear.sh`: capas subidas, URL del servicio y «Listo»')),
          'Un solo script hace tres cosas: crea el repositorio de Artifact Registry, construye y sube la imagen con la etiqueta fija v1 y despliega el servicio privado en Cloud Run. Lo más lento es el docker push. En la captura se ve el resumen de capas subidas, la confirmación de que la revisión sirve el cien por cien del tráfico y la URL. Fallo visto de verdad: las tildes se pierden al teclear en Cloud Shell desde fuera; los otros dos fallos de la tarjeta son posibles y no se han provocado.')

    slide('B', 7, 'Práctica 1: probar', 'paso 2 · en Cloud Shell', 'Prueba la API privada con tu identidad, sin claves', dos_columnas(
        term('Cloud Shell · misma carpeta de la práctica 1', [O['probar']]) + mira([
            '`/salud` → `{"estado":"ok"}` y `/listo` → `{"estado":"listo"}`; `/modelo` → la ficha del modelo.',
            '`POST /predecir` con el cliente `activo` → **probabilidad 0.828** y «OK: probabilidad de recompra a 90 dias = 0.828».',
            'Un campo que no existe → **422** (contrato estricto). Sin token → **403** y «**OK: privado**».']) + callout('**No ejecutes aún `borrar.sh`**: la práctica 2 usa esta imagen. Se borra después de la 2.') + si_falla([
            '**Posible, sin verificar:** `403` incluso con token: tu usuario no tiene `roles/run.invoker`; se añade con `gcloud run services add-iam-policy-binding retencion-api-practica --region southamerica-west1 --member=user:TU_CORREO --role=roles/run.invoker`.']),
          cap('gcp-p01-probar', 410, None, 'Las cinco comprobaciones de `probar.sh`: 200, 200, 200, 422 y 403')),
          'El servicio es privado, así que probar.sh obtiene un token de identidad de la sesión de Cloud Shell con gcloud auth print-identity-token y lo manda en la cabecera. Se comprueba la salud, que el modelo está cargado, una predicción, que la API rechaza un campo inventado con 422 y que sin token responde 403. La probabilidad, 0,828, es la misma que en local. Importante: todavía no se borra, porque la práctica 2 descarga esta imagen.')

    # ---------------------------------------------------------------- C · Práctica 2
    slide('C', 4, 'Práctica 2: qué aprendes', 'qué aprendes y qué crea', 'Kubernetes: Pod, Deployment y Service con la misma imagen', '''
<div class="grid2">
 <div class="col">
  <div class="card"><h3>Los tres objetos básicos</h3>''' + tabla(['Objeto', 'En una frase'], [
        ['**Pod**', 'la unidad mínima: uno o más contenedores que viven juntos. **Nace y muere**'],
        ['**Deployment**', '«quiero **N pods** de esta imagen y siempre N»: repone los que caen'],
        ['**Service**', 'un **nombre y una IP estables** delante de los pods; reparte entre los que están *listos*']]) + '''</div>
  ''' + callout('Además: `readinessProbe` (`/listo`), `livenessProbe` (`/salud`), **escalado** a 2 réplicas y **autorreparación** al borrar un pod.') + '''
 </div>
 <div class="col">''' + card('Qué crea', [
        f'Clúster **GKE Autopilot** `curso-ml-gke` en `{REGION}`.',
        'Una cuenta de servicio propia para los nodos, `sa-gke-nodos`, con dos roles (ver «Si falla»).',
        'Dentro: namespace `curso`, Deployment `retencion-api` (1 réplica; 2 tras probar) y Service `retencion-api` de tipo `ClusterIP`: **sin IP pública** ni balanceador de pago.']) + card('Antes de empezar', [
        '**Requisito:** haber hecho `crear.sh` de la práctica 1 (la imagen `v1` debe estar en Artifact Registry).',
        'Tiempo estimado **25-35 min** (sin medir); crear el clúster es lo más lento.',
        'El clúster **cobra mientras exista** (coste: **sin dato**): bórralo al acabar.']) + '''
 </div>
</div>''' + pasos([
        ('1 · Crear', '`bash crear.sh`: cuenta de los nodos, clúster Autopilot y `kubectl apply` de los tres YAML.'),
        ('2 · Probar', '`bash probar.sh`: predicción por el Service, 2 réplicas y autorreparación.'),
        ('3 · Borrar', '`bash borrar.sh` y, justo después, el `borrar.sh` de la práctica 1.')]),
          'Segunda práctica: los tres objetos básicos de Kubernetes con la misma imagen de la práctica 1. El Pod es la unidad mínima, el Deployment mantiene el número de pods que pedimos y el Service da un nombre y una dirección estables. Se usa GKE Autopilot, donde Google gestiona los nodos. El clúster cobra mientras exista y el importe no se ha medido. Requisito: la imagen de la práctica 1 tiene que estar subida y sin borrar.')

    slide('C', 8, 'Práctica 2: crear', 'paso 1 · en Cloud Shell', 'Crea el clúster y despliega la API con kubectl', dos_columnas(
        term('Cloud Shell · carpeta de la práctica 2', [O['cd_02'], O['crear']]) + mira([
            'Crea la cuenta `sa-gke-nodos`, le da dos roles y crea el clúster **con ella** (varios minutos, sin medir).',
            'Después `kubectl apply` de los tres YAML. Final: «**deployment "retencion-api" successfully rolled out**», un pod **1/1 Running** y el Service `ClusterIP`.']) + si_falla([
            '**Visto (25/11):** el primer clúster quedó en estado **ERROR** y `kubectl` daba «Unable to connect to the server: dial tcp …:443: **i/o timeout**».',
            '**Causa:** en una organización nueva la cuenta de servicio de Compute **no tiene roles**: los nodos no pueden descargar imágenes ni enviar registros.',
            '**Arreglo (ya en `crear.sh`):** cuenta propia `sa-gke-nodos` con `roles/container.defaultNodeServiceAccount` y `roles/artifactregistry.reader`, y `--service-account` en `create-auto`.']),
        cap('gcp-p02-crear2', 330, 'Es la captura **tras el arreglo**; la del clúster en ERROR no se incluye.', 'Clúster RUNNING, manifiestos aplicados y el pod 1/1 Running')),
          'El script crea primero una cuenta de servicio para los nodos con dos roles, y luego el clúster Autopilot usando esa cuenta. Es la lección de esta práctica: la primera vez usamos la cuenta de Compute por defecto y, en una organización nueva, no tiene ningún rol, así que los nodos no podían bajar la imagen ni enviar registros y el clúster acabó en estado de error, con kubectl dando un tiempo de espera agotado. La captura es del intento correcto.')

    slide('C', 7, 'Práctica 2: probar', 'paso 2 · en Cloud Shell', 'Prueba la API, escala a 2 réplicas y borra un pod', dos_columnas(
        term('Cloud Shell · misma carpeta de la práctica 2', [O['probar'], '# opcional: mira los objetos a mano', O['k_ver']]) + mira([
            'Por `kubectl port-forward` al Service: `{"estado":"listo"}` y la **probabilidad 0.828**.',
            '`deployment.apps/retencion-api scaled` → **2 pods** `1/1 Running`.',
            'Borra uno de los pods y Kubernetes **crea otro**: «**OK: 2 replicas listas otra vez.**» (autorreparación).']) + si_falla([
            '**Posible, sin verificar:** un pod en `Pending` mucho rato es Autopilot creando el nodo: espera unos minutos y mira `kubectl -n curso describe pod …`.',
            '**Posible, sin verificar:** `ImagePullBackOff` si la imagen de la práctica 1 ya no está.']),
          cap('gcp-p02-probar', 400, None, 'Predicción por el Service, escalado a 2 réplicas y autorreparación')),
          'Se prueba la API a través del Service con port-forward, sin exponer nada a Internet. Después se escala el Deployment a dos réplicas y se borra un pod a propósito: el Deployment crea otro para mantener dos, que es la autorreparación. Con eso se ve la diferencia entre un pod, que nace y muere, y un Deployment, que mantiene el estado deseado. La probabilidad vuelve a ser 0,828, la misma que en local y en Cloud Run.')

    slide('C', 5, 'Borrar la 2 y luego la 1', 'paso 3 · en Cloud Shell', 'Borra la práctica 2 y, ahora sí, la práctica 1', f'''
<div class="grid2">
 {term('Cloud Shell · carpeta de la práctica 2', [O['borrar']])}
 {term('Cloud Shell · pasas a la carpeta de la práctica 1', [O['cd_01_desde_02'], O['borrar']])}
</div>
<div class="grid2" style="margin-top:6px">
 {mira(['Borra el clúster, quita los **dos roles** y borra la cuenta `sa-gke-nodos`.', 'Al final «**Listed 0 items.**» (el aviso «filter keys … name» es normal).'], 'Práctica 2')}
 {mira(['Borra el servicio de Cloud Run, el repositorio `curso-ml-imagenes` (con su imagen) y la imagen local.', 'En esta captura el único repositorio que queda es `curso`: **es el del Cloud Journey**, no el de la práctica.'], 'Práctica 1')}
</div>
<div class="grid2" style="margin-top:6px">
 {cap('gcp-p02-borrado', 150, None, 'Práctica 2 borrada: clúster, roles y cuenta')}
 {cap('gcp-p01-borrado', 150, 'La captura recorta con `tail` las líneas anteriores.', 'Práctica 1 borrada: solo queda el repositorio `curso` del Cloud Journey')}
</div>''',
          'El borrado de la práctica 2 elimina el clúster, que borra todo lo de dentro, y después quita los dos roles y borra la cuenta de servicio de los nodos. Solo cuando la 2 está borrada se pasa a la carpeta de la 1 y se ejecuta su borrar.sh. En la captura de la práctica 1 el único repositorio que queda se llama curso y es el del laboratorio Cloud Journey, no el de esta práctica; las líneas anteriores no se ven porque la captura corta con tail. Comprobar siempre que los listados finales salen vacíos.')

    # ---------------------------------------------------------------- D · Práctica 3
    slide('D', 4, 'Práctica 3: qué aprendes', 'qué aprendes y qué crea', 'PySpark sobre nuestras ventas, sin montar un clúster', '''
<div class="grid2">
 <div class="col">''' + card('Qué aprendes', [
        'Un **lote (batch) de Dataproc sin servidor** ejecuta un job de **PySpark** sin que montes ni borres un clúster: desaparece solo al terminar.',
        'Los datos viajan por **Cloud Storage**: entrada, job y salida en un bucket.',
        'Se calcula `por_pais` (facturas, clientes distintos, monto y ticket medio) y `rfm` (recencia, frecuencia y monto por cliente).',
        'Después, **paridad**: Spark debe dar lo mismo que un cálculo local en Python.']) + callout('Funcionó en **Santiago**: el lote corrió en `southamerica-west1` (la documentación no lo listaba, por eso lo comprobamos).') + '''
 </div>
 <div class="col">
  <div class="card"><h3>Qué crea</h3>''' + tabla(['Recurso', 'Nombre'], [
        ['Bucket de Cloud Storage (sin acceso público)', f'`{PROYECTO}-curso-ml-dataproc`'],
        ['Lote de Dataproc sin servidor (etiqueta `curso=ml-ia`)', '`curso-ventas-AAAAMMDD-HHMMSS`'],
        ['Rol `roles/dataproc.worker` a la cuenta de Compute', 'solo si no lo tenía; `borrar.sh` lo quita']]) + '</div>' + card('Antes de empezar', [
        'Tiempo estimado **15-25 min** (sin medir). Coste: **sin dato**.',
        'Datos: **22 117 líneas** de venta exportadas de `curso.db`. Runtime de Spark **2.3**.']) + '''
 </div>
</div>''' + pasos([
        ('1 · Crear', '`bash crear.sh`: exporta los datos, crea el bucket, espera 120 s al permiso y lanza el lote.'),
        ('2 · Probar', '`bash probar.sh`: estado del lote, tabla por país y paridad con Python.'),
        ('3 · Borrar', '`bash borrar.sh`: registro de lotes, bucket y rol temporal.')]),
          'Tercera práctica: un lote de Dataproc sin servidor ejecuta un job de PySpark sobre las líneas de venta del caso, exportadas de la base del proyecto a un CSV en Cloud Storage. Se calculan los agregados por país y la tabla RFM de recencia, frecuencia y monto por cliente. Al final se comprueba la paridad con un cálculo local. En Santiago funcionó: el lote se ejecutó en southamerica-west1, algo que la documentación no listaba y que ahora está comprobado.')

    slide('D', 8, 'Práctica 3: crear', 'paso 1 · en Cloud Shell', 'Exporta los datos, crea el bucket y lanza el lote', dos_columnas(
        term('Cloud Shell · carpeta de la práctica 3', [O['cd_03'], O['crear']]) + mira([
            '«22117 lineas exportadas», el bucket y la subida de datos y job.',
            'Concede `roles/dataproc.worker` y **espera 120 s**: es normal, no se ha colgado.',
            'Al final «**Batch [curso-ventas-…] finished.**» y «Listo (lote curso-ventas-…)».']) + si_falla([
            '**Visto (25/11):** «**Permission \'dataproc.autoscalingPolicies.use\' denied**» justo después de conceder `roles/dataproc.worker`: **IAM tarda en propagarse**. Por eso `crear.sh` espera ahora 120 s; con dos minutos, el mismo lote terminó bien.',
            'Si te pasa con una copia antigua: espera dos minutos y repite `bash crear.sh`.']),
          cap('gcp-p03-crear2', 360, 'Se lanzó con `sleep 120;` delante, que es la espera que ahora hace el propio script.', 'El final de `crear.sh`: filas del RFM, lote terminado y «Listo»')),
          'El script exporta las líneas de venta del caso a un CSV, crea el bucket sin acceso público, sube los datos y el job, concede el rol de trabajador de Dataproc a la cuenta de Compute si no lo tenía, espera dos minutos y lanza el lote. La espera existe por un fallo real: la primera vez, justo después de conceder el rol, el lote falló con un permiso denegado de autoscalingPolicies.use; dos minutos después, el mismo lote terminó bien. La captura se hizo con un sleep delante, que es lo que el script hace ahora.')

    slide('D', 7, 'Práctica 3: probar', 'paso 2 · en Cloud Shell', 'Comprueba que Spark da lo mismo que Python', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">''' + term('Cloud Shell · misma carpeta de la práctica 3', [O['probar']]) + '''
  <div class="card"><h3>Tabla por país (salida real; 9 países en total)</h3>''' + tabla(['País', 'Facturas', 'Clientes', 'Monto total'], [
        ['United Kingdom', '1140', '133', '344244.74'], ['France', '47', '5', '18857.36'], ['Portugal', '14', '3', '10780.8']]) + '''</div>
  ''' + si_falla([
        '**Visto y corregido:** `probar.sh` decía «no hay lotes» aunque el lote estaba `SUCCEEDED`: `value(name)` devuelve el **nombre corto**. Si te pasa, `git pull`.',
        '**Lección:** la paridad daba **1 cliente de más** en EIRE y Reino Unido: el comprobador contaba las compras **sin cliente** y `countDistinct` de Spark, como `COUNT(DISTINCT)` en SQL, **ignora los nulos**. Ya está corregido.']) + f'''
 </div>
 <div class="capcol">{cap('gcp-p03-probar', 200, None, 'Fin de `probar.sh`: filas del RFM y la paridad')}
  ''' + mira([
        '`estado: SUCCEEDED`; ficheros `part-….csv` y `_SUCCESS` en `salida/por_pais/` y `salida/rfm/`.',
        'La última línea: «**OK: 9 paises; facturas, clientes y monto coinciden con el calculo local.**»']) + '''
  <div class="card"><h3>RFM: los 5 clientes con más monto (salida real de crear.sh)</h3>''' + tabla(['cliente_id', 'recencia_dias', 'frecuencia', 'monto'], [
        ['13093', '275', '55', '54144.25'], ['13001', '4', '33', '24042.65'], ['17243', '1', '69', '20184.68'],
        ['13488', '17', '23', '14205.96'], ['18225', '3', '26', '13014.8']]) + '''</div>
 </div>
</div>''',
          'Probar comprueba el estado del último lote, descarga el resultado de Cloud Storage, enseña la tabla por país y compara con un cálculo local de Python. La tabla muestra tres de los nueve países con cifras reales: Reino Unido, Francia y Portugal. Dos fallos reales: el grep sobre el nombre del lote, que devolvía el nombre corto, y la paridad, que daba un cliente de más porque había compras sin cliente y countDistinct, igual que COUNT DISTINCT en SQL, ignora los nulos. Ambos están corregidos.')

    slide('D', 4, 'Práctica 3: borrar', 'paso 3 · en Cloud Shell', 'Borra el bucket, los lotes y el rol temporal', dos_columnas(
        term('Cloud Shell · carpeta de la práctica 3', [O['borrar']]) + mira([
            'Borra el registro de los lotes, el **bucket con todo lo que contiene** y quita `roles/dataproc.worker` (solo si lo concedió `crear.sh`).',
            'Al final: «**Listed 0 items.**» y «(ningun bucket project-curso-ml-ia-curso-ml-dataproc)».']) + callout('Los lotes no cuestan en reposo, pero el **bucket** sí guarda datos: bórralo.'),
          cap('gcp-p03-borrado', 340, None, 'Bucket borrado, rol quitado y listados vacíos')),
          'El borrado elimina el registro de los lotes, el bucket con todo su contenido y el rol que concedió el script de creación, solo si lo concedió él. Al final lista lo que queda, que debe estar vacío. No hay ningún clúster que borrar: el lote desaparece solo al terminar.')

    # ---------------------------------------------------------------- E · Práctica 4
    slide('E', 6, 'Práctica 4: qué aprendes', 'qué aprendes y qué crea', 'Nuestro modelo en Vertex AI: registro, endpoint y predicción online', '''
<div class="grid2">
 <div class="col">''' + card('Qué aprendes', [
        'Registrar el modelo en el **Model Registry**, desplegarlo en un **endpoint** (un servicio HTTPS gestionado) y pedirle una **predicción online**.',
        'Deshacerlo todo en orden: **undeploy → endpoint → modelo → bucket**.']) + '''
  <div class="card"><h3>Un detalle de versiones</h3><p class="small">El proyecto usa <b>scikit-learn 1.9.1</b> y los contenedores pre-construidos de Vertex solo llegan a la <b>1.6</b>. Un modelo guardado con una versión no debe abrirse con otra, así que <span class="mono">crear.sh</span> <b>reentrena el mismo modelo</b> (misma regresión logística, mismos datos y 13 variables) con <b>scikit-learn 1.6.1</b> y compara su AUC con el del proyecto (0.6982): deben ser casi iguales.</p></div>
 </div>
 <div class="col">
  <div class="card"><h3>Qué crea</h3>''' + tabla(['Recurso', 'Nombre'], [
        ['Bucket (sin acceso público) con `modelo/model.joblib`', f'`{PROYECTO}-curso-ml-vertex`'],
        ['Modelo en el Model Registry', '`retencion-90d-sklearn`'],
        ['Endpoint (1 réplica `e2-standard-2`)', '`retencion-90d-endpoint`']]) + '''</div>
  <div class="card"><h3>La petición: una lista, no un diccionario</h3><p class="small"><span class="mono">{"instances": [[13 números]]}</span>, con las variables <b>en el orden del modelo</b>: <span class="mono">recencia_dias, frecuencia, monto_total, ticket_medio, unidades_total, productos_distintos, antiguedad_dias, frecuencia_90d, monto_90d, frecuencia_180d, dias_medios_entre_compras, devoluciones, es_reino_unido</span>. Si cambias el orden, el modelo <b>no avisa</b>: devuelve otra cosa.</p></div>
 </div>
</div>''' + pasos([
        ('1 · Crear', '`bash crear.sh`: reentrena con scikit-learn 1.6.1, registra el modelo, crea el endpoint y despliega (10-15 min).'),
        ('2 · Probar', '`bash probar.sh`: predicción online de dos clientes y comparación con el modelo local.'),
        ('3 · Borrar, ya', '`bash borrar.sh` **enseguida**: el endpoint cobra mientras exista.')]),
          'Cuarta práctica: registrar y servir nuestro modelo en Vertex AI. Detalle importante de versiones: el proyecto usa scikit-learn 1.9.1 y los contenedores pre-construidos de Vertex llegan solo a la 1.6, así que el script reentrena el mismo modelo con la 1.6.1 y compara el AUC con el del proyecto. La petición es una lista de trece números en el orden del modelo, no un diccionario, y el modelo no avisa si el orden es otro. Santiago admite Model Registry y predicción online de modelos propios.')

    slide('E', 9, 'Práctica 4: crear', 'paso 1 · en Cloud Shell', 'Reentrena, registra el modelo, crea el endpoint y despliega', dos_columnas(
        term('Cloud Shell · carpeta de la práctica 4', [O['cd_04'], O['crear']]) + mira([
            '`AUC valid` con scikit-learn 1.6.1 y el del proyecto (**0.6982**): casi iguales. `activo` → **0.8279**, clase 1; `dormido` → **0.2760**, clase 0.',
            'Bucket y `model.joblib`, «**Created Vertex AI endpoint**» y «**Deployed a model to the endpoint**».',
            'El despliegue tardó del orden de **10 a 15 min** (sin medir con exactitud).']) + callout('**Desde que termina el despliegue, el endpoint cobra.** No lo dejes para después: pasa a «probar» y «borrar» seguidos.') + si_falla([
            '**Posibles, sin verificar:** `Quota` o «insufficient resources» (cuota de CPU), `PERMISSION_DENIED` (falta `roles/aiplatform.user`) o un error de versión de scikit-learn en los registros del endpoint.']),
          cap('gcp-p04-crear', 470, None, 'Reentrenado, bucket, modelo registrado, endpoint creado y modelo desplegado')),
          'El script reentrena el modelo con scikit-learn 1.6.1 en un entorno aparte, lo sube a un bucket, lo registra en el Model Registry con el contenedor pre-construido, crea el endpoint y despliega el modelo en una máquina e2-standard-2 con una réplica. El despliegue tardó del orden de diez a quince minutos, sin medir con exactitud. En cuanto el modelo está desplegado, el endpoint cobra aunque nadie lo llame. Los fallos de la tarjeta son los más probables según la documentación y no se han provocado.')

    slide('E', 7, 'Práctica 4: probar', 'paso 2 · en Cloud Shell', 'Pide una predicción online y compárala con el modelo local', dos_columnas(
        term('Cloud Shell · misma carpeta de la práctica 4', [O['probar']]) + mira([
            'La respuesta de Vertex: `"predictions": [1, 0]`.',
            '«**activo Vertex (clase) = 1 | local: probabilidad 0.8279, clase 1 -> OK**» y «**dormido … 0.2760, clase 0 -> OK**».']) + callout('**Lección:** el contenedor pre-construido llama a `predict()` y devuelve la **clase**, no la probabilidad. Para servir la probabilidad haría falta un contenedor propio.') + callout('**Ahora, `borrar.sh`**: el endpoint cobra mientras esté desplegado.'),
          cap('gcp-p04-probar', 440, None, 'Petición de 2 clientes, `predictions: [1, 0]` y la comparación con el modelo local')),
          'La petición lleva dos clientes de ejemplo, el activo y el dormido, como listas de trece números. Vertex responde con la clase de cada uno, uno y cero, y el script la compara con la clase y la probabilidad del mismo modelo en local. La lección real de esta práctica: el contenedor pre-construido de scikit-learn llama a predict y devuelve la clase, no la probabilidad; la probabilidad de la API de S2 exigiría un contenedor propio con una rutina de predicción personalizada, que no se hace aquí.')

    slide('E', 4, 'Práctica 4: en la consola', 'paso 2 · la consola de Google Cloud', 'Míralo también en la consola de Google Cloud', f'''
<div class="grid2">{cap('cj-06-vertex-modelo', 330, None, 'Registro de modelos: el modelo importado, versión 1, Implementado')}{cap('cj-07-vertex-endpoint', 330, None, 'Extremos: el endpoint `retencion-90d-endpoint`, Activo, con 1 modelo')}</div>
<div class="grid2" style="margin-top:8px">
 {mira(['Dónde: la consola de Google Cloud, menú ☰ › **Plataforma de Gemini** (Vertex AI) › **Modelos** › **Registro de modelos**.', f'Elige la región **`{REGION}` (Santiago)**: si miras otra región, la lista sale **vacía**.'], 'El modelo')}
 {mira(['Dónde: el mismo menú › **Extremos** (los *endpoints*).', 'Estado **Activo** y **1** modelo: mientras sea así, **cobra**. Tras `borrar.sh` la lista queda vacía.'], 'El endpoint')}
</div>''',
          'Las dos capturas son de la consola de Google Cloud, con el banner del crédito recortado. En la consola, el menú de Vertex AI aparece como Plataforma de Gemini y los endpoints como Extremos. Hay que elegir la región de Santiago; en otra región la lista sale vacía. El nombre del modelo se corta en la tabla, pero es retencion-90d-sklearn, como se ve en la salida de probar.sh.')

    slide('E', 5, 'Práctica 4: borrar', 'paso 3 · en Cloud Shell, ya', 'Borra el endpoint, el modelo y el bucket, sin esperar', dos_columnas(
        term('Cloud Shell · carpeta de la práctica 4', [O['borrar']]) + mira([
            'En este orden: **undeploy** del modelo, **endpoint**, **modelo**, **bucket** y el entorno scikit-learn 1.6.',
            'Al final «**Listed 0 items.**» dos veces (endpoints y modelos) y «(ningun bucket …)».']) + callout(f'**Por qué ya:** el endpoint cobra mientras exista, y **el crédito de prueba no cubre la plataforma Gemini/Vertex en cuentas dadas de alta desde el 16/11/2026** (fuente: `{FUENTE_CREDITO}`). Cuánto cobra: **sin dato**.') + si_falla([
            '**Posible, sin verificar:** `borrar.sh` no puede borrar el endpoint porque aún tiene un modelo desplegado: repite `bash borrar.sh`, o en la consola entra al extremo y pulsa «Deshacer despliegue».']),
          cap('gcp-p04-borrado', 380, None, 'Bucket y entorno borrados; endpoints y modelos: «Listed 0 items»')),
          'Orden obligatorio: primero se deshace el despliegue del modelo, luego se borra el endpoint, después el modelo del registro y por último el bucket. Es la práctica que más importa borrar enseguida: el endpoint cobra por tiempo mientras tenga un modelo desplegado, y el crédito de la prueba gratuita no cubre la plataforma Gemini y Vertex en las cuentas dadas de alta desde el 16 de noviembre de 2026, según la página de la propia Google. El importe exacto no está medido.')

    # ---------------------------------------------------------------- F · Práctica 5
    slide('F', 4, 'Práctica 5: qué aprendes', 'qué aprendes y qué crea', 'Gemini explica la predicción: el modelo calcula, el LLM solo redacta', '''
<div class="grid4" style="margin-bottom:6px">
 <div class="card"><h3>1 · El cliente</h3><p class="small">Sus 13 variables (el cliente <span class="mono">activo</span> o <span class="mono">dormido</span> de <span class="mono">clientes_ejemplo.json</span>).</p></div>
 <div class="card"><h3>2 · El modelo</h3><p class="small">La regresión logística calcula la <b>probabilidad</b> y el <b>peso exacto</b> de cada variable.</p></div>
 <div class="card"><h3>3 · Gemini</h3><p class="small"><b>Solo redacta</b> en español con esos números; no calcula nada.</p></div>
 <div class="card"><h3>4 · La comprobación</h3><p class="small">El script mira que el texto <b>cite la probabilidad</b> del modelo.</p></div>
</div>
<div class="grid2">
 <div class="col">''' + card('Qué aprendes', [
        'Un **LLM gestionado** por Google, **sin claves**: se usa la autenticación de Cloud Shell.',
        'El LLM **no inventa**: se le entrega todo calculado y una instrucción de usar **solo** esos datos.',
        'El peso por variable es exacto porque el modelo es una **regresión logística**; el script lo comprueba con una aserción.']) + '''
 </div>
 <div class="col">''' + card('Qué crea', [
        '**Ningún recurso en la nube**: habilita la API de Vertex AI e instala `google-genai` en tu entorno de Cloud Shell.',
        'Modelo: `gemini-3.1-flash-lite`. Ubicación: **`global`**: Gemini **no** está en Santiago y `global` no garantiza dónde se procesa la petición (aquí solo viajan variables de un cliente de ejemplo).',
        'Tiempo estimado **10-15 min** (sin medir). Coste de cada llamada: **sin dato**.']) + '''
 </div>
</div>''' + pasos([
        ('1 · Crear', '`bash crear.sh`: instala `google-genai` en tu entorno de Cloud Shell (no crea nada en la nube).'),
        ('2 · Probar', '`bash probar.sh`: explica los clientes `activo` y `dormido` con Gemini.'),
        ('3 · Borrar', '`bash borrar.sh`: desinstala el SDK y lista los endpoints por si hiciste algo a mano.')]),
          'Quinta práctica: lo mismo que el agente de la sesión 5 pero con un modelo de lenguaje alojado por Google. El modelo de retención calcula la probabilidad y cuánto pesa cada variable, con cálculo exacto porque es una regresión logística; Gemini solo redacta la explicación en español a partir de esos números. No crea recursos que cobren en reposo. Gemini no está en Santiago, así que se usa la ubicación global; solo viajan variables agregadas de un cliente de ejemplo.')

    slide('F', 7, 'Práctica 5: crear y probar', 'pasos 1 y 2 · en Cloud Shell', 'Instala el SDK y pide la explicación de dos clientes', dos_columnas(
        term('Cloud Shell · carpeta de la práctica 5', [O['cd_05'], O['crear'], O['probar']]) + mira([
            '`crear.sh` imprime «**google-genai 3.6.1**» (la versión que se instaló ese día).',
            '`probar.sh`: los **hechos del modelo** en JSON (variables que más pesan, con «sube» o «baja»), «Llamando a gemini-3.1-flash-lite … (ubicación: global)» y un **párrafo en español**.',
            '«Tokens: entrada=388 salida=171».']) + si_falla([
            '**Posibles, sin verificar:** `404 … model not found` (otro `CURSO_REGION_GEMINI`), `403 PERMISSION_DENIED` (falta `roles/aiplatform.user`) o `DefaultCredentialsError` (`gcloud auth application-default login`).']),
          cap('gcp-p05-probar', 470, 'En la captura sale un «AVISO» falso: se explica en la diapositiva siguiente.', 'Hechos del modelo, la explicación de Gemini y los tokens')),
          'Crear instala el SDK de IA generativa de Google en el entorno de Cloud Shell. Probar calcula, para dos clientes de ejemplo, la probabilidad y los pesos con el modelo, se los entrega a Gemini con la instrucción de usar solo esos datos y muestra el texto. Con temperatura cero las respuestas son parecidas entre ejecuciones, pero no se garantiza que sean idénticas. En la captura se ve el aviso falso que se explica a continuación.')

    slide('F', 6, 'Práctica 5: la cifra y borrar', 'paso 3 · en Cloud Shell', 'Un aviso que era falso y cómo cerrar la práctica', f'''
<div class="split" style="grid-template-columns:1.05fr .95fr">
 <div class="col">
  <div class="card"><h3>Lo que escribió Gemini</h3><p class="small">«Este cliente tiene una probabilidad del <b>82.79%</b> de realizar una compra en los próximos 90 días, situándose en un tramo de probabilidad alta.»</p></div>
  {si_falla([
        '**Visto (25/11):** el script avisó «el texto no cita el 82.8 %» aunque Gemini sí escribió «82.79%». Era un **falso positivo**: solo buscaba «83» y «82.8».',
        '**Arreglo:** `explicar_prediccion.py` acepta la cifra con **1 o 2 decimales, coma o punto** (82,8 · 82.8 · 82,79 · 82.79); tiene su prueba. No se repitió la llamada real en Cloud Shell: **sin verificar** allí.'], 'El aviso de la captura')}
  {callout('**Lección:** los números los pone el modelo; el LLM solo los cuenta. Comprobar que cita la cifra es buena idea, pero la comprobación también puede equivocarse: **revisa** el texto.')}
 </div>
 <div class="col">
  {term('Cloud Shell · misma carpeta de la práctica 5', [O['borrar']])}
  {mira(['Desinstala `google-genai` del entorno y lista los endpoints por si hiciste algo a mano.', 'No hay **ningún recurso en la nube** que borrar: no se ha hecho captura de este paso.'], 'Borrar')}
  {card('Nota: Model Garden', ['Es la biblioteca de modelos de Vertex AI. Para modelos abiertos se paga **el cómputo del endpoint** (normalmente con GPU), por tiempo.', 'Por eso **no se despliega nada** en el curso: solo se explica. Coste: **sin dato**.'])}
 </div>
</div>''',
          'El aviso de la captura es un falso positivo real: Gemini escribió ochenta y dos coma setenta y nueve por ciento y el script buscaba solo ochenta y tres o ochenta y dos coma ocho. Ya se acepta la cifra con uno o dos decimales, con coma o con punto, y hay una prueba que lo comprueba; en Cloud Shell no se ha repetido la llamada real. La lección es doble: el modelo calcula y el LLM cuenta, y también las comprobaciones automáticas pueden fallar. Esta práctica no crea nada en la nube, así que su borrado solo desinstala el SDK.')

    # ---------------------------------------------------------------- G · Cierre
    slide('G', 4, 'Borrar todo de golpe', 'si algo se quedó sin borrar', 'Un solo script borra las cinco prácticas y repasa lo que queda', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">''' + term('Cloud Shell · carpeta practicas-gcp', [O['cd_practicas'], O['borrar_todo']]) + mira([
        'Ejecuta el `borrar.sh` de las cinco, **de la 5 a la 1** (la 1 la última, porque la 2 usa su imagen).',
        'Al final lista Cloud Run, clústeres, repositorios, lotes, endpoints, modelos y buckets: **todo debe salir vacío**.',
        'Si alguno falla, lo dice («han fallado estos borrar.sh») y sigue; repítelos uno a uno y lee el error.']) + '''
 </div>
 <div class="col">
  ''' + callout('**Sin verificar:** `borrar-todo.sh` no se ha ejecutado entero; sí se ejecutó cada `borrar.sh` por separado (capturas de las prácticas 1 a 4).') + card('Después de borrar', [
        'Las **APIs** habilitadas **se quedan** (no cuestan nada).',
        'Mira la consola: Cloud Run, Kubernetes Engine, Artifact Registry, Dataproc, Vertex AI y Cloud Storage deben estar **sin recursos de las prácticas**.',
        'Si el panel de **Facturación** enseña gasto, anota qué servicio es antes de cerrar.']) + '''
 </div>
</div>
<div class="card" style="margin-top:10px"><h3>Lista de comprobación en la consola (menú ☰)</h3>''' + tabla(['Servicio', 'Dónde mirar', 'Debe salir'], [
        ['**Cloud Run**', 'Cloud Run › Servicios', 'sin `retencion-api-practica` (el `retencion-api` es del Cloud Journey)'],
        ['**GKE**', 'Kubernetes Engine › Clústeres', 'sin `curso-ml-gke`'],
        ['**Artifact Registry**', 'Artifact Registry › Repositorios', 'sin `curso-ml-imagenes`'],
        ['**Dataproc** y **Cloud Storage**', 'Dataproc › Lotes · Cloud Storage › Buckets', 'sin lotes `curso-ventas-…` ni buckets `…-curso-ml-dataproc` / `…-curso-ml-vertex`'],
        ['**Vertex AI**', f'Registro de modelos y Extremos, región `{REGION}`', 'listas vacías']]) + '''</div>''',
          'Si al terminar el día algo se quedó sin borrar, el script borrar-todo.sh ejecuta los cinco borrados en orden inverso y repasa los listados. No se ha ejecutado entero todavía; lo que sí se ejecutó de verdad es cada borrar.sh por separado. Las APIs activadas no se desactivan porque no cuestan nada. Conviene mirar siempre la consola y el panel de facturación al terminar.')

    slide('G', 6, 'Costes y lecciones', 'lo que aprendimos de verdad', 'Costes y lecciones reales', '<div class="grid3">' + ''.join(
        f'<div class="card"><h3>{esc(t)}</h3><p class="small">{md(c)}</p></div>' for t, c in [
            ('El endpoint cobra encendido', 'Vertex cobra **mientras tenga un modelo desplegado**, aunque no reciba peticiones. El clúster de GKE, igual. Importe: **sin dato**.'),
            ('El crédito no lo cubre todo', 'La prueba gratuita **no cubre** la plataforma Gemini/Vertex en cuentas dadas de alta **desde el 16/11/2026**: borra enseguida.'),
            ('Cuenta de Compute, sin roles', 'En una organización nueva **no tiene ningún rol**: el clúster de GKE quedó en **ERROR**. Solución: `sa-gke-nodos`.'),
            ('IAM tarda en propagarse', 'Un rol recién concedido puede no valer aún: `dataproc.autoscalingPolicies.use denied`. Se **esperan 120 s**.'),
            ('Spark ignora los nulos', '`countDistinct` no cuenta los nulos, como `COUNT(DISTINCT)`: las compras **sin cliente** no suman clientes.'),
            ('Vertex devuelve la clase', 'El contenedor pre-construido llama a `predict()`: **1 o 0**, no la probabilidad. Tildes: en `gcloud`, **sin tildes**.')]) + '</div>'
          + '<div class="card" style="margin-top:12px"><h3>Qué sigue cobrando si lo dejas (importes: sin dato)</h3>' + tabla(['Recurso', 'Práctica', 'Cuándo cobra'], [
              ['**Endpoint con un modelo desplegado**', '4', 'por tiempo, **mientras exista**, aunque nadie lo llame'],
              ['**Clúster de GKE Autopilot**', '2', 'por los recursos de los pods y una cuota de clúster, **mientras exista**'],
              ['Repositorio de imágenes y buckets', '1, 3 y 4', 'por el almacenamiento de lo que guardan'],
              ['Servicio de Cloud Run', '1', 'con 0 instancias en reposo no hay instancia cobrando; la imagen sí ocupa espacio']]) + '</div>',
          'Seis lecciones reales de la jornada del 25 de noviembre. El endpoint de Vertex y el clúster de GKE cobran mientras existan. El crédito de prueba no cubre la plataforma Gemini y Vertex en las cuentas nuevas. La cuenta de Compute sin roles rompió el clúster. IAM tarda en propagarse. Spark ignora los nulos al contar distintos. Y el contenedor de scikit-learn de Vertex devuelve la clase y no la probabilidad. Las tildes también se pierden al teclear en Cloud Shell desde fuera.')

    slide('G', 6, 'Si algo falla', 'casos y su causa', 'Si algo falla: casos y qué hacer', '<div class="card">' + tabla(['Síntoma', 'Causa', 'Qué hacer', '¿Visto?'], [
        ['Clúster en **ERROR**; `kubectl`: «dial tcp …:443: i/o timeout» (2)', 'Los nodos usan la cuenta de Compute, **sin roles**', 'Usar el `crear.sh` actual (`sa-gke-nodos`); `bash borrar.sh` y repetir', 'sí (25/11)'],
        ['«Permission \'dataproc.autoscalingPolicies.use\' denied» (3)', '**IAM tarda** en propagar el rol recién concedido', 'Esperar 2 min y repetir; el script ya espera 120 s', 'sí (25/11)'],
        ['`probar.sh` dice «no hay lotes» (3)', '`value(name)` devuelve el nombre **corto**', '`git pull`: ya está corregido', 'sí (25/11)'],
        ['La paridad da **1 cliente de más** (3)', 'Compras **sin cliente**; `countDistinct` ignora los nulos', 'Comprobador corregido (ya cuenta como Spark)', 'sí (25/11)'],
        ['`predictions: [1, 0]` en vez de probabilidades (4)', 'El contenedor llama a `predict()`', 'Es lo esperado; la probabilidad es la del modelo local', 'sí (25/11)'],
        ['«El texto no cita el 82.8 %» y sí lo cita (5)', 'Falso positivo: «82.79%»', 'Corregido: acepta 1 o 2 decimales, coma o punto', 'sí (25/11)'],
        ['«Imgenes» en una descripción de `gcloud` (1)', 'Se pierden las **tildes** al teclear en Cloud Shell', 'Escribir las descripciones sin tildes', 'sí (25/11)'],
        ['`docker` no arranca, `uploadArtifacts` denegado, `403` con token, cuota, `PERMISSION_DENIED` en Vertex', 'Cloud Shell sin Docker, falta de un rol o de cuota', 'Ver «Si falla» del README de cada práctica', 'sin verificar']]) + '</div>',
          'Los siete primeros casos pasaron de verdad el 25 de noviembre y están corregidos o explicados. El último agrupa los fallos más probables según la documentación y el README de cada práctica, que no se provocaron a propósito: se marcan sin verificar y no se citan mensajes literales. Si un alumno encuentra uno con un mensaje distinto, que lo cuente para completar el material. El número entre paréntesis es la práctica.')

    slide('G', 5, 'Qué está verificado', 'qué se comprobó y qué no', 'Qué se comprobó de verdad y qué falta', f'''
<div class="grid2">
 <div class="card"><h3 class="okc">Comprobado el {FECHA} en la cuenta del curso</h3>''' + lista([
        '**1:** imagen en Artifact Registry y servicio privado en Cloud Run; `/salud`, `/listo`, `/modelo`, `/predecir` (**0.828**), 422 y 403 sin token.',
        '**2:** GKE Autopilot con pod 1/1 Running, predicción **0.828**, escalado a 2 réplicas y autorreparación; borrado con «Listed 0 items».',
        '**3:** lote de Dataproc en Santiago; «OK: 9 paises; facturas, clientes y monto coinciden con el calculo local».',
        '**4:** modelo en el Registro y endpoint **Activo** en Santiago; predicción `[1, 0]`; borrado con listados vacíos.',
        '**5:** explicación de Gemini con google-genai 3.6.1 (entrada 388, salida 171 tokens).']) + '''</div>
 <div class="card"><h3 class="malc">Sin verificar o sin dato</h3>''' + lista([
        'Coste de cada práctica y tiempo **exacto** del despliegue del endpoint (del orden de 10-15 min).',
        '`borrar-todo.sh` entero, y el borrado de la práctica 5 (no tiene recursos; sin captura).',
        'El aviso corregido de la práctica 5 **repetido en Cloud Shell**: solo se probó con la prueba automática.',
        'Clonar el **fork de un alumno** y los fallos «posibles» de cada README.',
        'Qué versión de Python trae Cloud Shell **mañana**: ese día, 3.12.3.']) + '''</div>
</div>
<div class="card" style="margin-top:10px"><h3>Las cifras reales del día (para comparar con las tuyas)</h3>''' + tabla(['Práctica', 'Qué midió', 'Cifra'], [
        ['**1** y **2**', 'probabilidad del cliente `activo` (API en Cloud Run y en GKE)', '**0.828** (0.8278889191932244)'],
        ['**3**', 'líneas exportadas · países · Reino Unido (facturas, clientes, monto)', '22 117 · 9 · 1140, 133, 344244.74'],
        ['**4**', 'AUC del modelo del proyecto · `activo` y `dormido` (local) · respuesta de Vertex', '0.6982 · 0.8279 y 0.2760 · `[1, 0]`'],
        ['**5**', 'tokens de la llamada a Gemini (`gemini-3.1-flash-lite`)', 'entrada 388 · salida 171']]) + '''</div>''',
          'Diapositiva de honestidad. Lo comprobado es todo lo que se ejecutó el veinticinco de noviembre en la cuenta del curso, con sus capturas. Lo que no: el coste de cada práctica, el tiempo exacto del despliegue del endpoint, el script de borrado total entero, el borrado de la práctica cinco que no tiene recursos ni captura, la repetición real del aviso corregido y el clonado desde el fork de un alumno.')

    slide('G', 4, 'Cierre', 'El mensaje', 'Del contenedor al LLM, y siempre: crea, prueba y borra', '''
<div class="msg">Cinco servicios de Google Cloud con <b>nuestro modelo</b>, <b>una misma probabilidad</b> y, al terminar cada uno, <b>todo borrado</b>.</div>
<div class="grid4" style="margin-top:18px">
 ''' + kpi('0.828', 'la **misma** probabilidad en local, Cloud Run y GKE', '') + kpi('[1, 0]', 'lo que devuelve Vertex: la **clase**, no la probabilidad', '') + kpi('120 s', 'de espera para que **IAM** propague un permiso', '') + kpi('0 claves', 'ni una clave JSON: la **sesión de Cloud Shell**', '') + '''
</div>
<div style="text-align:center;margin-top:44px;font-size:44px;font-weight:700;color:var(--acento)">¿Preguntas?</div>''',
          'Cierre con un único mensaje. Las cuatro cifras son reales: la probabilidad idéntica en local, Cloud Run y GKE; la respuesta de Vertex, que es la clase; los ciento veinte segundos de espera por la propagación de permisos y la ausencia de claves. La operación del modelo en producción continúa en la sesión 5.')


def html_completo():
    construir()
    js = JS.replace('__PARTES__', json.dumps(PARTES, ensure_ascii=False))
    partes = ''.join(f'<button class="part" data-p="{k}">{esc(v)}</button>' for k, v in PARTES.items())
    extra = '.zoom{width:fit-content;max-width:100%}.cap .zoom img{width:auto}'
    return ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>Prácticas en Google Cloud: del contenedor al LLM · ML e IA: de desarrollo a producción</title>\n'
            f'<!-- Generado por generar.py: no se edita a mano. -->\n<style>{CSS}{EXTRA_CSS}{extra}</style>\n</head>\n<body>\n'
            '<div id="prog"></div>\n<div id="viewport"><div id="stage">\n\n' + '\n\n'.join(SLIDES) + '\n\n</div></div>\n\n'
            '<aside id="notes" aria-label="Notas del ponente"><h3>Notas del ponente</h3><div id="notetext"></div><p class="small" id="notemin"></p></aside>\n'
            '<div id="index" aria-label="Índice"><h2>Índice</h2><div class="grid" id="idxgrid"></div></div>\n'
            '<div id="zoombox" aria-label="Captura ampliada"><p>Esc o clic para cerrar</p><img id="zoomimg" alt=""></div>\n'
            '<nav id="bar" aria-label="Controles">\n'
            '  <button id="bprev" aria-label="Anterior">←</button><button id="bnext" aria-label="Siguiente">→</button>\n'
            f'  <span id="count">1 / 1</span><span id="clockref" title="Minuto planificado acumulado (propuesta)"></span>\n  {partes}\n'
            '  <span class="sp"></span>\n'
            '  <a id="bhome" href="../index.html" title="Volver al índice de la sesión S4">⌂ S4</a><button id="bidx">Índice (O)</button><button id="bnotes">Notas (S)</button><button id="bfull">Pantalla completa (F)</button>\n'
            '</nav>\n'
            '<noscript>Esta presentación necesita JavaScript. El mismo contenido está en el README.md de cada práctica, en esta carpeta.</noscript>\n\n'
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
