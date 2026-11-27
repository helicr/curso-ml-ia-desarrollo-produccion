"""Genera la presentación «Laboratorio de cierre de S4: producción e2e del caso Retail» (index.html, junto a este archivo).

En su fork y su Codespace, cada persona lleva a producción el modelo de retención a 90 días del caso Online Retail II:
configura el repositorio una vez, ve los tres modos de explotación (lote, bajo demanda y online), entrena una versión nueva
con puerta de calidad y aprobación humana, la publica en GHCR, abre el pull request de la referencia y ensaya el rollback.

Mismo manejo que las presentaciones de S3 (← → · O índice · S notas · F pantalla completa · Esc), con fondo blanco y nada
que se mueva al pasar el ratón. Cada orden lleva ⧉ para copiarla. Las capturas se leen de img/ con los nombres de CAPTURAS;
si falta alguna, se dibuja un recuadro «Captura pendiente» (no falla).

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
FECHA = '22/11/2026'
USUARIO = 'helicr'
CARPETA = '01-Sesiones/S4-Orquestacion-y-CI-CD/laboratorio-produccion-e2e'
RAMA_BASE = 'lab/produccion-e2e'
WORKFLOWS = ['puntuar-lote.yml', 'validar-produccion.yml', 'nueva-version.yml', 'rollback.yml']
RUNS = 'https://github.com/helicr/curso-ml-ia-desarrollo-produccion/actions/runs/'

# Runs reales de la cuenta del profesor (22/11/2026): nombre -> número de run
RUN = {'lote': '45026646958', 'validar': '45026646944', 'igual': '45027468464', 'rechazo': '45027468487',
       'completo': '45030152194', 'rollback_rojo': '45041023548', 'rollback_verde': '45041634741'}

# Capturas reales (webp). Nombre -> qué se ve de verdad (texto alternativo y pie).
CAPTURAS = {
    'cfg-01-environments.webp': 'Settings > Environments del fork: el environment «produccion» con «1 protection rule» y el botón New environment',
    'cfg-02-environment-revisores.webp': 'Configure produccion: Required reviewers marcado con helicr como revisor y el botón verde Save protection rules',
    'cfg-03-actions-permisos.webp': 'Settings > Actions > General: seleccionada la opción «Allow all actions and reusable workflows» (Actions activado)',
    'cfg-04-workflow-permissions.webp': 'Workflow permissions: marcada la casilla «Allow GitHub Actions to create and approve pull requests»',
    'gh-01-esperando-aprobacion.webp': 'Run en espera: aviso amarillo «helicr requested your review to deploy to produccion» con el botón Review deployments; trabajos 1 y 2 en verde y el 3 esperando',
    'gh-02-run-publicado.webp': 'Run terminado con éxito: los cuatro trabajos en verde (3 m 11 s, 2 m 18 s, 17 s y 14 s) y el resumen «ACEPTADA»',
    'gh-03-pr-referencia.webp': 'Pull request nº 2 «Referencia del modelo: v2-3521a0421905ba28», abierto por github-actions[bot], con la tabla v1 frente a v2',
    'gh-04-pr-cambios.webp': 'Archivos cambiados del PR nº 2: en historial_versiones.json se añade la versión 2 y la 1 pasa a «anterior»',
    'gh-05-rollback-parado.webp': 'Rollback en rojo (10 s): «La imagen no está en GHCR. No se encuentra ghcr.io/helicr/retencion-api:v1-35a94deb4e04ab4a…»',
    'gh-06-rollback-pr.webp': 'Rollback en verde (16 s): resumen «Rollback · de v2 a v1» con el enlace al pull request nº 3',
    'gh-07-pr-rollback.webp': 'Pull request nº 3 «Rollback del modelo: v2 a v1», abierto por github-actions[bot]: devuelve referencia.json a la versión 1',
    'gh-08-pr-rollback-cambios.webp': 'Archivos cambiados del PR nº 3: en el historial la 1 pasa de «anterior» a «produccion» y la 2 de «produccion» a «retirada»',
    'gh-10-run-lote.webp': 'Puntuar por lotes en verde (2 m 55 s): trabajos de 55 s, 1 min 51 s y 4 s; resumen con corte 2011-12-10 y 148 clientes puntuados',
    'gh-11-run-validar.webp': 'Validar la producción completa en verde (2 m 16 s): un trabajo de 2 m 13 s; resumen con la campaña de 148 clientes y la versión v1',
    'gh-12-nueva-igual.webp': 'Nueva versión con la rama …/muestra: trabajo 1 en verde (1 m 4 s), los otros tres omitidos y «IGUAL · nada que publicar»',
    'gh-13-nueva-rechazada.webp': 'Nueva versión con …/completo-rechazo: trabajo 1 en rojo (2 m 43 s), los demás omitidos y «RECHAZADA · no se publica» con tolerancia -0.1',
    'panel-1-lote.webp': 'Panel de producción, pestaña Lote: corte 2011-12-10, 148 clientes puntuados, 15 en la campaña y los 20 primeros clientes con su probabilidad',
    'panel-2-bajo-demanda.webp': 'Pestaña Bajo demanda: el cliente 12670 con probabilidad 79,9 %, tramo alta y corte 2011-12-10',
    'panel-3-online-antes.webp': 'Pestaña Online antes de la compra: lote, bajo demanda y online dan 79,9 % para el cliente 12670',
    'panel-4-online-despues.webp': 'Pestaña Online tras «Simular una compra nueva»: online pasa a 76,2 % y lote y bajo demanda siguen en 79,9 %',
    'panel-5-versiones.webp': 'Pestaña Versiones: en producción v1 (retencion-api:v1-35a94deb4e04ab4a, AUC 0,747), coincide con el modelo que sirve, sin historial guardado',
}

# Órdenes que se copian (clave -> orden). La guía las repite tal cual y las pruebas lo comprueban.
O = {
    'switch_develop': 'git switch develop',
    'pull': 'git pull',
    'rama': f'git switch -c {RAMA_BASE}',
    'mkdir': 'mkdir -p .github/workflows',
    'cp': f'cp {CARPETA}/{{puntuar-lote,validar-produccion,nueva-version,rollback}}.yml .github/workflows/',
    'add': 'git add .github/workflows',
    'commit': 'git commit -m "Laboratorio de cierre de S4: workflows de producción"',
    'push': f'git push -u origin {RAMA_BASE}',
    'volver_base': f'git switch {RAMA_BASE}',
    'muestra_rama': 'git switch -c lab/nueva-version/muestra',
    'muestra_push': 'git push -u origin lab/nueva-version/muestra',
    'rechazo_rama': f'git switch {RAMA_BASE} && git switch -c lab/nueva-version/completo-rechazo',
    'rechazo_push': 'git push -u origin lab/nueva-version/completo-rechazo',
    'completo_rama': f'git switch {RAMA_BASE} && git switch -c lab/nueva-version/completo',
    'completo_push': 'git push -u origin lab/nueva-version/completo',
    'rb_fetch': 'git fetch origin',
    'rb_base': 'git switch lab/nueva-version/completo',
    'rb_pull': 'git pull',
    'rb1_rama': 'git switch -c lab/rollback/v1',
    'rb1_push': 'git push -u origin lab/rollback/v1',
    'rb2_rama': 'git switch -c lab/rollback/v1-sin-comprobar',
    'rb2_push': 'git push -u origin lab/rollback/v1-sin-comprobar',
    'cd': 'cd 04-Proyecto-Base',
    'operacional': 'python -m ia_mlops.operacional',
    'pipeline': 'python -m ia_mlops.pipeline',
    'explotacion': 'python -m ia_mlops.explotacion',
    'compose_up': 'docker compose -f deploy/docker/compose-produccion.yaml up --build -d',
    'compose_ps': 'docker compose -f deploy/docker/compose-produccion.yaml ps',
    'listo': 'curl -fsS http://127.0.0.1:8090/listo',
    'id': 'ID=12670',
    'bajo': 'curl -s http://127.0.0.1:8090/bajo-demanda/$ID',
    'online': 'curl -s http://127.0.0.1:8090/online/$ID',
    'compra': ('curl -s -X POST http://127.0.0.1:8090/demo/compra -H \'content-type: application/json\' '
               '-d "{\\"cliente_id\\": $ID, \\"importe\\": 120.5, \\"unidades\\": 3}"'),
    'reiniciar': 'curl -s -X POST http://127.0.0.1:8090/demo/reiniciar',
    'down': 'docker compose -f deploy/docker/compose-produccion.yaml down',
}

NOTA_GH13 = ('Esta captura se hizo antes de corregir el texto del motivo: pone «empeora más que la tolerancia de -0.1» con una '
             'diferencia de +0.0485, que no tiene sentido. El texto actual del código, para una tolerancia negativa, dice «no '
             'mejora lo exigido (al menos +0.1, tolerancia de -0.1). No se publica.». La decisión (rechazada) es la misma.')

PARTES = {'A': 'Plan', 'B': 'Preparar', 'C': 'Lote', 'D': 'Panel', 'E': 'Versión', 'F': 'Rollback', 'G': 'Cierre'}
NOMBRES_PARTE = {'A': 'Qué vamos a hacer', 'B': 'Preparar el repositorio', 'C': 'Modo 1 · lote',
                 'D': 'Modos 2 y 3 y el panel', 'E': 'Una versión nueva', 'F': 'Volver atrás', 'G': 'Problemas y cierre'}


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


def cap(nombre, alto=None, nota=None):
    """Una captura (clic = ampliar) o, si aún no está en img/, el recuadro «Captura pendiente»."""
    alt = CAPTURAS[nombre]
    estilo = f' style="max-height:{alto}px"' if alto else ''
    extra = f'<br><span class="nota">{md(nota)}</span>' if nota else ''
    if (AQUI / 'img' / nombre).is_file():
        return (f'<figure class="cap" data-img="{nombre}"><button class="zoom" data-src="img/{nombre}" data-alt="{esc(alt)}" title="Ampliar (Esc cierra)">'
                f'<img src="img/{nombre}" alt="{esc(alt)}"{estilo}><span class="lupa">{LUPA} Ampliar</span></button>'
                f'<figcaption><span class="tag ok">Captura real</span> {esc(alt)}{extra}</figcaption></figure>')
    alto_p = f' style="min-height:{min(alto or 200, 260)}px"' if alto else ''
    return (f'<figure class="cap" data-img="{nombre}"><div class="pend"{alto_p}><b>Captura pendiente</b><span class="mono">img/{nombre}</span>'
            f'<span>{esc(alt)}</span></div><figcaption><span class="tag warn">Pendiente</span> {esc(alt)}</figcaption></figure>')


def rotulo_capturas(nombres):
    hay = [n for n in nombres if (AQUI / 'img' / n).is_file()]
    if len(hay) == len(nombres):
        return f'<p class="small rot"><span class="tag ok">Capturas reales</span> cuenta del profesor (<span class="mono">{USUARIO}</span>) · {FECHA}</p>'
    return '<p class="small rot"><span class="tag warn">Captura pendiente</span> las capturas reales de este paso se añaden en <span class="mono">img/</span></p>'


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


SLIDES = []
_N = {}
GRANDES = {'El plan', 'Los tres modos', 'Siglas y palabras', 'Fork, Codespace y rama', 'Configurar el repositorio', 'Puntuar por lotes',
           'Levantar el panel', 'Bajo demanda y online con curl', 'Ramas de ensayo', 'Puerta de calidad y los cuatro trabajos',
           'Escenario igual', 'Lanzar el rollback', 'Aceptada: espera la aprobación', 'Fusionar el PR', 'Si algo falla', 'Qué está verificado', 'Autoevaluación', 'Cierre'}


def slide(parte, minutos, titulo, kick, h1, cuerpo, notas):
    n = list(PARTES).index(parte) + 1
    _N[parte] = _N.get(parte, 0) + 1
    antetitulo = f'{n} · {NOMBRES_PARTE[parte]} · {kick}'
    attrs = f' data-part="{parte}" data-min="{minutos}" data-title="{esc(titulo)}"'
    clase = ' grande' if titulo in GRANDES else ''
    SLIDES.append(f'<section class="slide{clase}"{attrs}\n data-notes="{esc(notas)}">\n'
                  f'<p class="kick">{esc(antetitulo)}</p><h1>{md(h1)}</h1>\n{cuerpo}\n</section>')


def svg_grafo():
    """Los cuatro trabajos de nueva-version.yml, con la puerta de calidad y la aprobación."""
    cajas = [('1 · Entrenar y comparar', 'con la versión en producción'),
             ('2 · Construir la imagen', 'probarla; campeón frente a candidata'),
             ('3 · Publicar en GHCR', 'espera la aprobación de una persona'),
             ('4 · Abrir el PR', 'que actualiza models/referencia.json')]
    g = ['<defs><marker id="fg" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#0b5cad"/></marker></defs>']
    for i, (t, s) in enumerate(cajas):
        x = 6 + i * 275
        clase = 'nodo puerta' if i == 2 else 'nodo'
        g.append(f'<rect x="{x}" y="20" width="238" height="84" rx="12" class="{clase}"/><text x="{x + 119}" y="55" class="t1">{esc(t)}</text><text x="{x + 119}" y="80" class="t2">{esc(s)}</text>')
        if i:
            g.append(f'<path d="M{x - 34} 62 L{x - 3} 62" class="fl" marker-end="url(#fg)"/>')
    g.append('<path d="M125 106 L125 124 L675 124" class="fl dis"/><path d="M400 124 L400 138" class="fl dis"/><path d="M675 124 L675 138" class="fl dis"/>')
    g.append('<path d="M125 106 L125 138" class="fl" marker-end="url(#fg)"/>')
    g.append('<rect x="6" y="142" width="238" height="52" rx="10" class="nodo ok"/><text x="125" y="165" class="t1 tok">aceptada</text><text x="125" y="184" class="t2">sigue con los trabajos 2 a 4</text>')
    g.append('<rect x="281" y="142" width="238" height="52" rx="10" class="nodo"/><text x="400" y="165" class="t1">igual</text><text x="400" y="184" class="t2">misma huella: 2 a 4 omitidos</text>')
    g.append('<rect x="556" y="142" width="238" height="52" rx="10" class="nodo mal"/><text x="675" y="165" class="t1 tmal">rechazada</text><text x="675" y="184" class="t2">el trabajo 1 sale en rojo</text>')
    return f'<svg viewBox="0 0 1100 205" role="img" aria-label="Los cuatro trabajos de nueva-version.yml y las tres decisiones posibles del primero">{"".join(g)}</svg>'


# =====================================================================================================================================
# Contenido
# =====================================================================================================================================
def construir():
    SLIDES.clear()
    _N.clear()

    # ---------------------------------------------------------------- A · Qué vamos a hacer
    slide('A', 3, 'Portada', 'ML e IA: de desarrollo a producción · S4', 'Laboratorio de cierre: producción de punta a punta del caso Retail', f'''
<div class="cover">
 <p class="sub">El mismo modelo de retención a 90 días, explotado de <b>tres maneras</b>; y cómo entra en producción una <b>versión nueva</b> con puerta de calidad, aprobación humana y vuelta atrás. Todo en tu fork y tu Codespace, sin Google Cloud.</p>
 <div class="chips"><span class="tag">Caso Online Retail II</span><span class="tag">GitHub Actions</span><span class="tag">GHCR</span><span class="tag">Codespace</span><span class="tag">sin GCP</span></div>
 <div class="card" style="margin-top:22px"><h3>Cómo seguirla</h3><p class="small">Cada orden lleva <b>⧉</b> para copiarla en la terminal del Codespace. <b>← →</b> avanzan · <b>O</b> índice · <b>S</b> notas · <b>F</b> pantalla completa · clic en una captura para ampliarla y <b>Esc</b> para cerrarla. Todo está también en texto en <span class="mono">guia.md</span>, junto a esta presentación. Las capturas son reales ({FECHA}, cuenta del profesor).</p></div>
</div>''',
          'Cierre de la puesta en producción (laboratorio final de S4): el modelo ya está entrenado y desplegado en S3, hoy se ve cómo se explota y cómo se cambia con control. Que cada persona tenga abierto su fork y su Codespace. Todo lo que se enseña pasó de verdad en la cuenta del profesor el 22 de noviembre; las cifras salen de los runs y de las capturas, no están inventadas. No se usa Google Cloud.')

    slide('A', 4, 'El plan', 'Lo que vas a hacer', 'Siete pasos: de configurar a volver atrás', '''
<div class="grid2">
 <div class="card"><h3>Los pasos</h3><ol class="ol">
  <li>Preparar la rama y copiar los cuatro workflows</li>
  <li>Configurar el repositorio <b>una vez</b> (environment y permiso de PR)</li>
  <li>Modo 1: <b>puntuación por lotes</b> con Actions</li>
  <li>Modos 2 y 3 y el <b>panel</b> en el Codespace</li>
  <li><b>Nueva versión</b>: igual, rechazada, aceptada, aprobada y publicada</li>
  <li><b>Fusionar</b> el pull request de la referencia</li>
  <li><b>Rollback</b> a la versión anterior</li></ol></div>
 <div class="col">
  <div class="card"><h3>Al terminar sabrás</h3>''' + lista([
        'Cuándo conviene **lote**, **bajo demanda** u **online**, y por qué dan lo mismo hasta que llegan datos nuevos.',
        'Qué es «el modelo en producción»: **una imagen** con etiqueta y **una ficha** en el repositorio.',
        'Cómo una **puerta de calidad** y una **aprobación** protegen la publicación.',
        'Cómo **volver atrás** sin borrar nada.']) + '''</div>
  <div class="callout">Nada se empuja a <span class="mono">develop</span> ni a <span class="mono">main</span>: se ensaya en ramas <span class="mono">lab/…</span> y los cambios entran por pull request.</div>
 </div></div>''',
          'Mapa completo antes de empezar. Los pasos 1 y 2 se hacen una vez. El 3 y el 4 enseñan los tres modos. Del 5 al 7 es el ciclo de una versión nueva: entrar, fusionar y volver atrás. Insista en la regla de oro: las ramas de ensayo empiezan por lab/, así no se toca develop ni main.')

    slide('A', 6, 'Los tres modos', 'Concepto · una pregunta, un modo', 'Tres modos de explotación del mismo modelo', '''
<div class="card">''' + tabla(['Modo', 'La pregunta del negocio', 'De dónde salen las 13 variables', 'Cuándo se calcula', 'Dónde corre aquí'], [
        ['**1 · Lote** (*batch*)', '«¿A quién llamo hoy?» Se puntúa a **todos** y se ordena', 'del pipeline, en el corte del día', 'una vez al día: `schedule` 05:17 UTC y **Run workflow**', 'GitHub Actions: `puntuar-lote.yml`'],
        ['**2 · Bajo demanda**', '«¿Qué probabilidad tiene el cliente 12670?»', '**leídas** de la tabla `fs_produccion` (ya calculadas, las de ayer)', 'al preguntar, sin cálculo de variables', 'API + interfaz: `GET /bajo-demanda/{id}` y `POST /bajo-demanda`'],
        ['**3 · Online**', '«Acaba de comprar: ¿qué le ofrezco **ahora**?»', '**calculadas al vuelo** con el SQL de la capa FS, hasta el instante de la petición', 'al preguntar, con los datos frescos', 'API + interfaz: `GET /online/{id}?corte=`']]) + '''</div>
<div class="grid3" style="margin-top:12px">
 <div class="card"><h3>Lote</h3><p class="small">Barato y programado: <b>una vez al día</b>, para todos los clientes a la vez.</p></div>
 <div class="card"><h3>Bajo demanda</h3><p class="small">Rápido: consulta por clave de variables <b>ya calculadas</b>. No ve lo que pasó hoy.</p></div>
 <div class="card"><h3>Online</h3><p class="small">Rápido y con datos frescos, pero hay que calcular las variables al vuelo <b>sin fuga</b>: solo datos anteriores a la petición.</p></div>
</div>
<div class="grid2" style="margin-top:12px">
 <div class="callout">Los tres usan <b>la misma versión</b> del modelo y, mientras no llegan datos nuevos, dan <b>la misma probabilidad</b> para el mismo cliente y corte.</div>
 <div class="callout">La demo lo hace visible: una <b>compra simulada</b> cambia la probabilidad <b>online</b> y no la del lote ni la de bajo demanda.</div>
</div>''',
          'Esta tabla es la columna vertebral del laboratorio. Pregunte al grupo qué modo usarían para: la campaña de la mañana (lote), un agente de call center que consulta a un cliente concreto (bajo demanda) y una web que reacciona a una compra que acaba de ocurrir (online). La diferencia está en de dónde salen las variables: leídas o calculadas ahora. Lo veremos medido: online cuesta algo más de tiempo pero ve la compra nueva.')

    slide('A', 4, 'Siglas y palabras', 'Vocabulario · antes de empezar', 'Siglas y palabras que van a aparecer', '<div class="card">' + tabla(['Palabra', 'Qué es'], [
        ['**GHCR**', '*GitHub Container Registry*: el almacén de imágenes de contenedor de GitHub (`ghcr.io`). Aquí guarda `retencion-api`, la API con el modelo dentro'],
        ['**PR** (*pull request*)', 'una propuesta de cambio entre dos ramas, con revisión y fusión (*merge*) a mano. Nuestros workflows **nunca** empujan a `develop` ni a `main`: abren un PR'],
        ['***environment***', 'un «entorno» de GitHub con reglas de protección. El nuestro se llama `produccion` y exige que una persona **revise y apruebe** antes de publicar'],
        ['**huella** (de datos)', 'resumen corto de los datos de entrenamiento: los mismos datos dan la misma huella. Va en la etiqueta de la imagen: `retencion-api:v1-35a94deb4e04ab4a`'],
        ['**AUC**', 'área bajo la curva ROC: **0,5** es el azar y **1** es acertar siempre. Es la métrica de la puerta de calidad'],
        ['**tolerancia**', 'cuánto puede **empeorar** el AUC de test la versión nueva sin ser rechazada (por defecto **0,02**)'],
        ['**campeón / candidata**', 'el campeón es el modelo en producción; la candidata, la versión nueva que aspira a sustituirlo'],
        ['`referencia.json`', 'la ficha de la versión en producción en el repositorio: versión, huella, imagen y métricas de test']]) + '</div>',
          'Vocabulario mínimo para no perderse. Insista en tres: environment, que es lo que hace que la publicación espere a una persona; huella, que es lo que permite decir que no hay nada nuevo; y tolerancia, que es la puerta de calidad. AUC se explicó en el curso: 0,5 es el azar. GHCR y PR no se habían usado antes en el curso.')

    # ---------------------------------------------------------------- B · Preparar el repositorio
    slide('B', 7, 'Fork, Codespace y rama', 'paso 1, rama y workflows', 'Rama de trabajo y los cuatro workflows', f'''
<div class="split" style="grid-template-columns:1.05fr .95fr">
 <div class="col">''' + term('Terminal del Codespace · en la raíz del repositorio', [
        O['switch_develop'], O['pull'], O['rama'], O['mkdir'], O['cp'], O['add'], O['commit']]) + f'''
  <div class="callout">En un <b>fork</b>, antes: pestaña <b>Actions</b> y aceptar el aviso para activar los workflows. Aún <b>no hagas push</b>: primero se configura el repositorio.</div>
 </div>
 <div class="col">''' + mira([
        '`On branch lab/produccion-e2e` y `.github/workflows/` con **cuatro** archivos nuevos.',
        'Los cuatro: `puntuar-lote.yml`, `validar-produccion.yml`, `nueva-version.yml` y `rollback.yml`.',
        'El `cp` copia los cuatro de una vez (llaves de bash); en otra terminal, cópialos uno a uno.']) + si_falla([
        '`cp: cannot stat …`: tu fork no tiene la carpeta del laboratorio; haz **Sync fork** o copia cada YAML con «Copiar el archivo».',
        'Sin Actions activado en el fork no aparecerá ningún run: pestaña Actions del fork.',
        'El fork debe hacerse con «Copy the `main` branch only» **desmarcado**: si no, no tiene `develop` y fallan «Create codespace on develop» y `git switch develop`.',
        'Un Codespace no se actualiza solo: `git fetch origin`, `git status -sb` (debe decir «behind N») y `git pull origin develop`.']) + '''
 </div></div>''',
          'Preparación. Dos formas de tener los cuatro YAML: copiarlos de la carpeta del laboratorio, o abrir cada uno y pegarlo. El push se deja para después de configurar el repositorio: así el primer push lanza el lote y la validación y ya hay environment. Que nadie trabaje en el repositorio del curso: tiene que ser su fork, o no podrán subir.')

    slide('B', 8, 'Configurar el repositorio', 'una sola vez, en Settings de GitHub', 'Configurar el repositorio: environment y permiso de PR', f'''
<div class="split" style="grid-template-columns:.9fr 1.1fr">
 <div class="col">
  <div class="card"><h3>A · El environment <span class="mono">produccion</span></h3><ol class="ol sm">
   <li><b>Settings</b> › <b>Environments</b> › <b>New environment</b></li>
   <li>Nombre exacto: <span class="mono">produccion</span> (sin tilde; no <span class="mono">prod</span>)</li>
   <li>Marca <b>Required reviewers</b> y añádete a ti mismo</li>
   <li><b>Save protection rules</b></li></ol></div>
  <div class="card"><h3>B · Permiso para abrir PR</h3><ol class="ol sm">
   <li><b>Settings</b> › <b>Actions</b> › <b>General</b> › <b>Workflow permissions</b></li>
   <li>Marca <b>Allow GitHub Actions to create and approve pull requests</b></li>
   <li><b>Save</b></li></ol></div>
  <div class="callout">Sin A (o con otro nombre), la publicación <b>no espera</b> a nadie. Sin B, el último paso falla.</div>
 </div>
 <div class="capcol">{rotulo_capturas(['cfg-01-environments.webp', 'cfg-02-environment-revisores.webp', 'cfg-03-actions-permisos.webp', 'cfg-04-workflow-permissions.webp'])}
  <div class="thumbs t2">{cap('cfg-01-environments.webp', 175)}{cap('cfg-02-environment-revisores.webp', 175)}{cap('cfg-03-actions-permisos.webp', 175)}{cap('cfg-04-workflow-permissions.webp', 175)}</div>
 </div>
</div>''',
          'El paso más importante de la preparación y el que más se olvida. Primera captura: la lista de environments con produccion y una regla de protección. Segunda: Required reviewers con el propio usuario y Save protection rules; en la captura también está marcado Allow administrators to bypass, que es lo que GitHub propone por defecto. Tercera: Actions habilitado. Cuarta: la casilla del permiso de PR, en Workflow permissions; el permiso del token puede seguir en solo lectura porque cada trabajo pide los suyos.')

    # ---------------------------------------------------------------- C · Modo 1 · lote
    slide('C', 6, 'Puntuar por lotes', 'cuándo y qué hace', 'Puntuación por lotes: todos los clientes, cada día', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">
  <div class="card"><h3>Cuándo se ejecuta</h3>''' + tabla(['Disparador', 'Detalle'], [
        ['`schedule`', '**todos los días a las 05:17 UTC** (`cron: \'17 5 * * *\'`); un minuto «raro» a propósito, porque a las horas en punto GitHub va cargado'],
        ['`workflow_dispatch`', '**Run workflow** a mano, con tres entradas: `capacidad` (0.10 = el 10 %), `corte` e `imagen` (construir o ghcr)'],
        ['`push` a `lab/**`', 'solo si cambia el workflow o `explotacion.py`: así se prueba sin esperar al día siguiente']]) + '''</div>
  <div class="callout">El push arranca <b>dos</b> runs: «Puntuar por lotes» (3 cajas) y «Validar la producción completa» (1 caja). No es un error. Si el push se rechaza con <b>non-fast-forward</b>, la rama ya existe en ese repositorio: no hagas <span class="mono">git pull</span> ni <span class="mono">--force</span>; renómbrala con <span class="mono">git branch -m lab/produccion-e2e lab/produccion-e2e-2</span>.</div>
  <div class="callout"><b>En un fork, el <span class="mono">schedule</span> viene desactivado</b>. Se lanza con Run workflow; y Run workflow solo aparece si el workflow está en la rama por defecto: por eso en el laboratorio se dispara con el <b>push</b>.</div>
 </div>
 <div class="col">
  <div class="card"><h3>Qué hace: tres trabajos</h3>''' + lista([
        '**1 · Preparar datos** (operacional + pipeline).',
        '**2 · Puntuar a todos los clientes**: levanta la API en un contenedor y ejecuta `explotacion --url`.',
        '**3 · Resumen**: corte, clientes puntuados, campaña, probabilidad media, versión y huella del modelo.']) + '''</div>
  <div class="card"><h3>Qué deja</h3>''' + lista([
        'Artefacto **campana**: `campana_<corte>.csv` y `.json` (todos los clientes, ordenados).',
        'Artefacto **base-fs-produccion**: la base con la tabla `fs_produccion` (las 13 variables del corte), la que lee «bajo demanda».']) + '''</div>
  ''' + term('Terminal · tras configurar el repositorio: este push lanza el lote y la validación', [O['push']]) + '''
 </div></div>''',
          'El lote responde a ¿a quién llamo hoy? No se pregunta por nadie: se puntúa a todos y se ordena por probabilidad. El cron es 17 5: cinco y diecisiete UTC. GitHub puede retrasar un schedule varios minutos. En un fork el schedule viene desactivado, y Run workflow solo aparece si el archivo está en la rama por defecto; en el laboratorio, el primer push a lab/produccion-e2e lo lanza porque cambia el propio workflow. Los artefactos se pueden descargar desde la página del run.')

    slide('C', 5, 'Lote y validación en Actions', 'los runs reales', 'El lote y la validación de la producción, en verde', f'''
{rotulo_capturas(['gh-10-run-lote.webp', 'gh-11-run-validar.webp'])}
<div class="grid2">{cap('gh-10-run-lote.webp', 300)}{cap('gh-11-run-validar.webp', 300)}</div>
<div class="grid2" style="margin-top:8px">
 {mira(['**Puntuar por lotes**, run nº ' + RUN['lote'] + ': trabajos de **55 s**, **111 s** y **4 s**; total 2 m 55 s.', 'Resumen: corte **2011-12-10**, **148** clientes puntuados; en la campaña, el 10 % (15 clientes en el panel).'], 'Lote')}
 {mira(['**Validar la producción completa**, run nº ' + RUN['validar'] + ': un trabajo de **133 s**; total 2 m 16 s.', 'Levanta API + interfaz con docker compose y comprueba los tres modos con `curl`.'], 'Validación')}
</div>''',
          'Los dos workflows se lanzaron con el mismo push a lab/produccion-e2e. El lote tarda unos tres minutos: el trabajo de puntuar es el más largo porque construye y levanta la API. El segundo es la prueba de humo de la producción completa: comprueba en Actions, con Docker real, lo mismo que el alumno hará a mano en el Codespace. Cada persona verá sus propios números de run; los de aquí son los del profesor.')

    # ---------------------------------------------------------------- D · Modos 2 y 3 y el panel
    slide('D', 6, 'Levantar el panel', 'preparar y levantar', 'Datos, modelo y panel en el Codespace', '''
<div class="split" style="grid-template-columns:1.1fr .9fr">
 <div class="col">''' + term('Terminal del Codespace', [
        O['cd'], '# 1) deja los datos, el modelo y el lote (el compose no los crea)', O['operacional'], O['pipeline'], O['explotacion'],
        '# 2) levanta la API y la interfaz con el panel', O['compose_up'], O['compose_ps'], O['listo']]) + '''
 </div>
 <div class="col">''' + mira([
        '`ps`: dos servicios, `api` e `interfaz`; la `api` pasa a **healthy**. La primera vez tarda unos minutos (construye dos imágenes).',
        '`/listo` responde con `"estado": "listo"`.',
        'En la pestaña **Puertos** abre el **8090** y añade `/panel` a la dirección.']) + si_falla([
        '`No existe …`: te saltaste una de las tres órdenes de Python; ejecútalas en ese orden.',
        '`curl` da 503: la API aún no está sana; mira `docker compose … logs api interfaz`.']) + '''
  <div class="callout"><b>Sin verificar en Codespace.</b> Estas órdenes se probaron en local y en Actions (<span class="mono">validar-produccion.yml</span>); en un Codespace todavía no se han ejecutado.</div>
 </div></div>''',
          'Orden de las tres órdenes de Python: primero la base operacional, luego el pipeline que entrena y crea la base analítica, y por último el lote, que escribe la campaña y la tabla fs_produccion. Sin ellas el compose arranca pero el panel sale vacío. Cuota de Codespaces: si se detiene, el panel también se puede abrir en local. Honestidad: el compose no se ha ejecutado todavía en un Codespace; sí en Actions y en local.')

    slide('D', 6, 'Bajo demanda y online con curl', 'lo mismo, dos caminos', 'Mismo cliente, dos caminos: leer o calcular', '''
<div class="split" style="grid-template-columns:1.1fr .9fr">
 <div class="col">''' + term('Terminal del Codespace · el cliente 12670 es de la campaña del lote', [
        O['id'], O['bajo'], O['online'], '# llega una compra nueva y se vuelve a preguntar', O['compra'], O['bajo'], O['online'],
        '# dejar la demo como al principio', O['reiniciar'], '# al terminar: parar el panel', O['down']]) + '''
 </div>
 <div class="col">''' + mira([
        'Antes de la compra, **bajo demanda y online dan la misma** `probabilidad` y el mismo `corte`.',
        'Después: **bajo demanda no cambia** (lee la tabla de ayer) y **online cambia** (suma la compra).',
        'La compra se guarda en una **copia** de la base dentro del contenedor, nunca en la del proyecto.']) + si_falla([
        '`404` «no está en fs_produccion»: ese cliente no tiene compras válidas antes del corte; elige otro de la pestaña Lote.',
        '`404` «El modo demo está apagado»: usa `compose-produccion.yaml`, no `compose.yaml`.']) + '''
  <div class="card"><h3>Tiempos medidos</h3><p class="small">Latencia p50 con <span class="mono">TestClient</span> (local, <b>no en red</b>): bajo demanda <b>26,8 ms</b>, online <b>33,5 ms</b>.</p></div>
 </div></div>''',
          'La demostración conceptual más importante del día. Bajo demanda hace una consulta por clave a fs_produccion y llama a la API: rápido y barato. Online calcula las trece variables con el SQL de la capa FS hasta el instante de la petición: más caro pero ve lo último. Las latencias son de una medición local con TestClient, sin red: sirven para comparar, no como promesa de producción. El id 12670 es del lote del 2011-12-10 que se ve en las capturas.')

    slide('D', 4, 'Pestañas del panel', 'cuatro pestañas', 'El panel: Lote, Bajo demanda, Online y Versiones', f'''
{rotulo_capturas(['panel-1-lote.webp', 'panel-2-bajo-demanda.webp', 'panel-5-versiones.webp'])}
<div class="grid3">{cap('panel-1-lote.webp', 250)}{cap('panel-2-bajo-demanda.webp', 250)}{cap('panel-5-versiones.webp', 250)}</div>
<div class="grid3" style="margin-top:8px">
 {mira(['Corte **2011-12-10**, **148** clientes puntuados, **15** en la campaña (el 10 %), probabilidad media **48,6 %**.', 'Los 20 primeros, con su probabilidad y avisos.'], 'Lote')}
 {mira(['El cliente **12670**: **79,9 %**, tramo **alta**, corte 2011-12-10.', 'Dice que «las variables son las de ayer».'], 'Bajo demanda')}
 {mira(['En producción **v1** (AUC test **0,747**) y el modelo que sirve coincide. El historial sale vacío: aún no hay versión 2.'], 'Versiones')}
</div>''',
          'Cuatro pestañas, tres capturas aquí y la cuarta, Online, en la siguiente diapositiva. Lote: la última campaña con enlace al CSV. Bajo demanda: el id y la recomendación; la primera consulta tardó casi seis segundos en la captura porque el modelo estaba frío, por eso las latencias se miden con p50 y no con una sola llamada. Versiones: compara la ficha referencia.json con el modelo que sirve; el historial aparece después de fusionar el primer PR.')

    slide('D', 5, 'La compra simulada', 'la pestaña Online', 'Una compra simulada: solo cambia el modo online', f'''
{rotulo_capturas(['panel-3-online-antes.webp', 'panel-4-online-despues.webp'])}
<div class="grid2">{cap('panel-3-online-antes.webp', 290)}{cap('panel-4-online-despues.webp', 290)}</div>
<div class="grid3" style="margin-top:8px">
 {kpi('79,9 %', '**antes**: lote, bajo demanda y online dan lo mismo para el cliente 12670', 'okc')}
 {kpi('76,2 %', '**online después** de «Simular una compra nueva» (120,5 en 3 unidades)', '')}
 {kpi('79,9 %', '**lote y bajo demanda siguen igual** hasta que se recalcule `fs_produccion`', 'okc')}
</div>''',
          'Es la imagen que resume los tres modos. Antes de pulsar el botón, los tres cuadros dicen 79,9 por ciento. Se simula una compra de 120,5 en tres unidades; online baja a 76,2 por ciento porque la recencia y la frecuencia cambian, y lote y bajo demanda no se mueven hasta el siguiente run diario. En producción real esa compra llegaría por una cola o un feature store online; aquí se simula sobre una copia de la base.')

    # ---------------------------------------------------------------- E · Una versión nueva
    slide('E', 8, 'Ramas de ensayo', 'cómo se ensaya', 'El nombre de la rama elige el escenario', f'''
<div class="split" style="grid-template-columns:1.05fr .95fr">
 <div class="col">
  <div class="card">''' + tabla(['Rama de ensayo (`lab/nueva-version/…`)', 'Escenario', 'Resultado esperado'], [
        ['`muestra`', 'datos de la muestra del repositorio (la fuente de la v1)', '**IGUAL**: misma huella; trabajos 2 a 4 omitidos'],
        ['`completo-rechazo`', 'Excel completo y **tolerancia -0,10** (se exige mejorar 0,10)', '**RECHAZADA**: el trabajo 1 sale en rojo'],
        ['`completo`', 'Excel completo con la tolerancia por defecto (0,02)', '**ACEPTADA**: construye, espera aprobación, publica y abre el PR']]) + '''</div>
  <div class="callout"><b>Por qué ramas:</b> <span class="mono">Run workflow</span> solo aparece si el workflow está en la rama por defecto. Un <b>push</b> a una rama <span class="mono">lab/nueva-version/…</span> lo lanza igual y el nombre decide los datos y la tolerancia. Hazlo en este orden: <b>completo</b> el último.</div>
 </div>
 <div class="col">''' + term('Terminal · una orden por escenario', [
        O['volver_base'], O['muestra_rama'], O['muestra_push'], '# cuando acabe: el rechazo', O['rechazo_rama'], O['rechazo_push'], '# el último: el completo (espera aprobación)', O['completo_rama'], O['completo_push']]) + '''
 </div></div>''',
          'Lo que hace posible ensayar sin tocar la rama principal. Dos reglas: el nombre de la rama elige el escenario (muestra, completo, completo-rechazo) y los runs del mismo grupo de concurrency esperan en cola, por eso se lanza el completo el último: se quedará esperando a que alguien lo apruebe. La rama nueva apunta al mismo commit que la de base, pero crear una rama es un push y dispara el workflow. La tolerancia negativa es una exigencia de mejora, útil para ensayar un rechazo con datos reales, porque con el Excel completo el modelo nuevo no empeora.')

    slide('E', 6, 'Puerta de calidad y los cuatro trabajos', 'el pipeline', 'Cuatro trabajos y una puerta de calidad', f'''
<div class="card">{svg_grafo()}</div>
<div class="grid3" style="margin-top:12px">
 <div class="card"><h3>La puerta</h3><p class="small">{md("Compara el **AUC de test** con el de `models/referencia.json` y una **tolerancia de 0,02**: misma huella → **igual**; el AUC cae más que la tolerancia → **rechazada**; en otro caso → **aceptada**.")}</p></div>
 <div class="card"><h3>La aprobación</h3><p class="small">{md("El trabajo 3 usa el *environment* `produccion`: se queda **esperando** hasta que un revisor aprueba. Es el único con permiso para escribir paquetes.")}</p></div>
 <div class="card"><h3>«En producción» es…</h3><p class="small">{md("la imagen `retencion-api:v<N>-<huella>` en GHCR **más** `referencia.json` y `historial_versiones.json` (la pestaña Versiones). Pasa a ser la de producción al **fusionar el PR**.")}</p></div>
</div>''',
          'El dibujo es el grafo real de nueva-version.yml. Tres decisiones en el primer trabajo: igual, rechazada y aceptada. Si es igual, los trabajos 2 a 4 se omiten y aparecen en gris. Si es rechazada, el trabajo 1 sale en rojo y no se construye nada. Solo aceptada sigue. El trabajo 2 construye la imagen, la prueba y compara campeón y candidata: cuántos clientes cambian de tramo puntuando las mismas filas de test. El 3 espera a una persona. El 4 abre un PR, nunca hace push directo.')

    slide('E', 4, 'Escenario igual', 'escenario 1', 'Sin datos nuevos: «igual · nada que publicar»', f'''
<div class="split" style="grid-template-columns:1.15fr .85fr">
 <div class="capcol">{rotulo_capturas(['gh-12-nueva-igual.webp'])}{cap('gh-12-nueva-igual.webp', 400)}</div>
 <div class="col">''' + mira([
        'Rama `lab/nueva-version/muestra`, run nº ' + RUN['igual'] + ', **en verde**.',
        'El trabajo 1 (entrenar y comparar) tarda **64 s**.',
        'Los trabajos 2, 3 y 4 salen **omitidos** (gris con un círculo tachado).',
        'El resumen dice: «los datos son los mismos que los de la versión 1 (huella 35a94deb4e04ab4a): no hay nada que publicar».']) + '''
  <div class="callout">Entrenar con los mismos datos da el mismo modelo: no se publica nada. Es la <b>idempotencia por huella</b>.</div>
 </div></div>''',
          'Primer escenario: no llegan datos nuevos. El pipeline recalcula la huella de los datos, la compara con la de referencia.json y, al coincidir, se detiene con éxito. Es lo correcto: un run verde que no publica nada. Los grises no son un error. Pregunte al grupo por qué es útil: porque se puede programar el reentrenamiento todos los días sin llenar GHCR de imágenes idénticas.')

    slide('E', 5, 'Escenario rechazada', 'escenario 2', 'Una versión que no pasa la puerta: rechazada', f'''
<div class="split" style="grid-template-columns:1.15fr .85fr">
 <div class="capcol">{rotulo_capturas(['gh-13-nueva-rechazada.webp'])}{cap('gh-13-nueva-rechazada.webp', 330, NOTA_GH13)}</div>
 <div class="col">''' + mira([
        'Rama `lab/nueva-version/completo-rechazo`, run nº ' + RUN['rechazo'] + ', **en rojo** en el trabajo 1 («Rechazar la versión si empeora más que la tolerancia»); total 3 m 53 s.',
        'Los trabajos 2, 3 y 4 **no se ejecutan**: no se construye ni se publica nada.',
        'AUC de test **0,7956** frente a **0,7471**: la versión nueva **mejora** +0,0485.']) + '''
  <div class="callout">Se ensaya con <b>tolerancia -0,10</b>: «tienes que mejorar 0,10». Mejoró 0,0485, así que <b>no basta</b> y se rechaza.</div>
 </div></div>''',
          'Esta captura se hizo antes de corregir el texto del motivo, y por eso es importante leerla con el pie. Con una tolerancia negativa la regla es una exigencia de mejora: la versión nueva tiene que mejorar al menos 0,10, y mejoró 0,0485. El código actual lo dice bien: no mejora lo exigido, al menos más 0,1, tolerancia de menos 0,1. No se publica. Con la tolerancia por defecto, esta misma versión sale aceptada: es la siguiente diapositiva.')

    slide('E', 7, 'Aceptada: espera la aprobación', 'escenario 3', 'Aceptada, construida… y esperando a una persona', f'''
<div class="split" style="grid-template-columns:1.1fr .9fr">
 <div class="capcol">{rotulo_capturas(['gh-01-esperando-aprobacion.webp'])}{cap('gh-01-esperando-aprobacion.webp', 420, 'Es el run nº 3 de este mismo escenario (rama `lab/nueva-version/completo`); el que acabó publicando fue el nº 5. El paso de espera es idéntico.')}</div>
 <div class="col">
  <div class="card"><h3>Aprobar el despliegue</h3><ol class="ol sm">
   <li>Abre el run: estado <b>Waiting</b> y el aviso amarillo</li>
   <li>Pulsa <b>Review deployments</b></li>
   <li>Marca <b>produccion</b></li>
   <li>Pulsa <b>Approve and deploy</b></li></ol></div>''' + mira([
        'Texto del aviso: «**helicr requested your review to deploy to produccion**».',
        'Trabajos 1 y 2 en verde; el 3, «waiting for review».',
        'Resumen del trabajo 1: **ACEPTADA**, AUC de test **0,7956** frente a **0,7471** (diferencia **+0,0485**) dentro de la tolerancia de 0,02.']) + si_falla([
        'Pasa sin pedir aprobación: el *environment* no existe o no tiene revisores (paso de configuración A).']) + '''
 </div></div>''',
          'El momento humano del pipeline. Sin esta aprobación, un pipeline automático publicaría cualquier versión que supere la puerta. El aviso amarillo dice quién pidió la revisión; con un solo usuario, uno se aprueba a sí mismo, que es lo que se hace en el laboratorio. La captura es de un run anterior del mismo escenario; el definitivo fue el número 5, cuyas cifras se ven en la diapositiva siguiente.')

    slide('E', 7, 'Publicada y PR abierto', 'tras aprobar', 'Publicada en GHCR y PR de la referencia abierto', f'''
{rotulo_capturas(['gh-02-run-publicado.webp', 'gh-03-pr-referencia.webp', 'gh-04-pr-cambios.webp'])}
<div class="grid3">{cap('gh-02-run-publicado.webp', 215)}{cap('gh-03-pr-referencia.webp', 215)}{cap('gh-04-pr-cambios.webp', 215)}</div>
<div class="grid3" style="margin-top:8px">
 {mira(['Run nº ' + RUN['completo'] + ' en verde: entrenar **191 s**, construir **138 s**, publicar **17 s** tras aprobar, referencia **14 s**.', 'Imagen: `ghcr.io/helicr/retencion-api:v2-3521a0421905ba28`.'], 'El run')}
 {mira(['PR **nº 2** «Referencia del modelo: v2-3521a0421905ba28», abierto por `github-actions[bot]` desde `referencia/v2-45030152194`.', 'Tabla v1 → v2: AUC **0,7471 → 0,7956**.'], 'El PR')}
 {mira(['Cambia `referencia.json` e `historial_versiones.json`.', 'En el historial: la v2 queda **produccion** y la v1, **anterior**.'], 'Los archivos')}
</div>''',
          'Tras aprobar, el trabajo 3 sube la imagen ya probada a GHCR con la etiqueta v2 guion huella; solo tarda 17 segundos porque la imagen se construyó en el trabajo anterior. El trabajo 4 abre un pull request desde una rama nueva con el nombre referencia barra v2 guion número de ejecución. El tiempo total del run en la captura, 1 h 19 min, incluye la espera hasta aprobar; el trabajo real suma unos seis minutos. El PR va contra la rama de ensayo, no contra develop.')

    slide('E', 5, 'Fusionar el PR', 'la v2 pasa a ser la de producción', 'Fusionar el PR: ahora sí es la de producción', '''
<div class="split" style="grid-template-columns:.9fr 1.1fr">
 <div class="col">
  <div class="card"><h3>Fusionar</h3><ol class="ol sm">
   <li>Abre el PR nº 2 (pestaña <b>Pull requests</b>)</li>
   <li>Revisa <b>Files changed</b>: dos archivos</li>
   <li><b>Merge pull request</b></li>
   <li><b>Confirm merge</b></li></ol></div>
  <div class="callout">Hasta fusionar, la v2 existe en GHCR pero <b>no está en producción</b>: la ficha sigue diciendo v1. El siguiente lote usará la v2 cuando el PR esté fusionado.</div>
  <div class="card"><h3>Qué no hace</h3>''' + lista([
        'No empuja a `develop` ni a `main`: aquí el PR va contra la rama de ensayo.',
        'Un PR creado con el `GITHUB_TOKEN` **no lanza otros workflows** (regla de GitHub).']) + '''</div>
 </div>
 <div class="col">
  <div class="card"><h3>Qué cambia al fusionar</h3>''' + tabla(['', 'Antes (v1)', 'Después (v2)'], [
        ['`etiqueta_imagen`', '`retencion-api:v1-35a94deb4e04ab4a`', '`retencion-api:v2-3521a0421905ba28`'],
        ['fuente de los datos', 'muestra', 'completo'],
        ['AUC de test', '0,7471', '0,7956'],
        ['historial', 'v1 · producción', 'v1 · anterior; v2 · producción']]) + '''</div>
  <div class="realbox"><div class="rk">Captura real del diff · historial_versiones.json (PR nº 2)</div><pre>+    "estado": "anterior"      (la v1)
+    "version": 2, "fuente_datos": "completo"
+    "etiqueta_imagen": "retencion-api:v2-3521a0421905ba28"
+    "estado": "produccion"    (la v2)</pre></div>
 </div></div>''',
          'Fusionar es el acto que cambia qué versión está en producción. Mientras el PR esté abierto, la ficha referencia.json sigue apuntando a la v1. Los textos de los botones son los de GitHub en inglés: Merge pull request y Confirm merge. En este ensayo el PR se fusiona en la rama lab/nueva-version/completo. El bloque verde es lo que se lee en el diff de la captura del PR nº 2.')

    # ---------------------------------------------------------------- F · Volver atrás
    slide('F', 5, 'Lanzar el rollback', 'cómo se lanza', 'Lanzar el rollback desde una rama con la v2 fusionada', '''
<div class="split" style="grid-template-columns:1.1fr .9fr">
 <div class="col">''' + term('Terminal · tras fusionar el PR nº 2', [
        O['rb_fetch'], O['rb_base'], O['rb_pull'], '# 1) con comprobación: se parará, a propósito', O['rb1_rama'], O['rb1_push'],
        '# 2) sin comprobar la imagen: abre el PR', O['rb2_rama'], O['rb2_push']]) + '''
 </div>
 <div class="col">''' + mira([
        'El rollback **no reentrena ni reconstruye**: busca en el historial de git la ficha de la versión pedida (por defecto, la anterior a la actual).',
        'Por defecto **comprueba que su imagen exista en GHCR**; con «sin-comprobar» en el nombre de la rama, no.',
        'Abre un PR y **no borra nada**.'], 'Cómo funciona') + si_falla([
        'El run no arranca: puede haber otro run del grupo `nueva-version-modelo` esperando aprobación; cancélalo o apruébalo.',
        'Hay que salir de una rama que **ya tenga la v2 fusionada**: si no, no hay una versión anterior que restaurar.']) + '''
 </div></div>''',
          'El rollback se lanza igual que la nueva versión: con un push a una rama cuyo nombre empieza por lab/rollback. Sale de la rama donde se fusionó el PR de la v2, porque necesita ver en el historial de git la ficha anterior. Primero se hace con la comprobación de la imagen, que se parará; después se repite con sin-comprobar en el nombre para ver el mecanismo completo.')

    slide('F', 6, 'Rollback: dos intentos', 'volver a la v1', 'Rollback: primero se para, a propósito', f'''
{rotulo_capturas(['gh-05-rollback-parado.webp', 'gh-06-rollback-pr.webp'])}
<div class="grid2">
 <div class="col">
  {cap('gh-05-rollback-parado.webp', 270)}
  {mira(['Rama `lab/rollback/v1`, run nº ' + RUN['rollback_rojo'] + ', **rojo** en **10 s**.', '«La imagen no está en GHCR: No se encuentra ghcr.io/helicr/retencion-api:v1-35a94deb4e04ab4a…».', 'Es **a propósito**: la v1 se entrenó en local y **nunca se publicó**.'], '1 · Con comprobación')}
 </div>
 <div class="col">
  {cap('gh-06-rollback-pr.webp', 270)}
  {mira(['Rama `lab/rollback/v1-sin-comprobar` (con «sin-comprobar» en el nombre no se comprueba la imagen), run nº ' + RUN['rollback_verde'] + ', **verde** en **16 s**.', 'Resumen «Rollback · de v2 a v1» y enlace al **PR nº 3**.'], '2 · Sin comprobar')}
 </div>
</div>''',
          'El rollback no reentrena ni reconstruye: devuelve la ficha a una versión anterior. Por defecto comprueba que la imagen de esa versión exista en GHCR, porque si no, la ficha apuntaría a algo que no se puede descargar. La v1 nunca se publicó, así que el primer intento se detiene con un mensaje claro; es una lección: lo que no está publicado no se puede restaurar. En el segundo se salta la comprobación con una rama cuyo nombre lleva sin-comprobar, solo para ensayar el mecanismo. No se borra nada en GHCR.')

    slide('F', 5, 'El PR del rollback', 'lo que cambia', 'El PR nº 3 restaura la ficha y no borra nada', f'''
<div class="grid2">{cap('gh-07-pr-rollback.webp', 270)}{cap('gh-08-pr-rollback-cambios.webp', 270)}</div>
<div class="grid2" style="margin-top:8px">
 {mira(['**Restaura** `referencia.json` tal cual estaba en el commit anterior (la v1).', 'En el historial: la v1 vuelve a **produccion** y la v2 pasa a **retirada**.', 'Al fusionarlo, el siguiente lote vuelve a usar la imagen de la v1.'], 'Qué hace')}
 {mira(['**No se borra nada**: la imagen de la v2 sigue en GHCR y el historial se conserva.', 'Volver a avanzar es lanzar «Nueva versión del modelo» otra vez.', 'Alternativa: el botón **Revert** del PR de referencia que se fusionó.'], 'Qué no hace')}
</div>''',
          'El PR nº 3 es la prueba de que se puede volver atrás con control: queda revisado y fusionado como cualquier cambio, con rastro. Fíjese en la segunda captura: en historial_versiones.json la 1 pasa de anterior a produccion y la 2 de produccion a retirada. Lo retirado no se elimina. En el día a día, el rollback va con la imagen ya publicada, así que se hace en segundos; aquí la v1 no estaba publicada y por eso hubo que saltarse la comprobación.')

    # ---------------------------------------------------------------- G · Problemas y cierre
    slide('G', 6, 'Si algo falla', 'casos reales que pasaron', 'Si algo falla: cuatro casos reales', '<div class="card">' + tabla(['Síntoma', 'Causa', 'Qué hacer'], [
        ['El run nuevo **no arranca**: se queda en cola («Pending»)', 'Un run **esperando aprobación bloquea** al siguiente del mismo grupo de *concurrency* (`nueva-version-modelo`, compartido con `rollback`)', '**Cancela** el run viejo (Cancel workflow) o **apruébalo**'],
        ['El trabajo «Publicar» falla con «No such file or directory»', 'Un trabajo **sin checkout** hereda `defaults.run.working-directory: 04-Proyecto-Base`, que no existe en ese trabajo', 'Se arregló con `working-directory: .` en el trabajo `publicar` (una prueba lo vigila)'],
        ['Publica **sin esperar** aprobación', 'El *environment* `produccion` **no existía** (GitHub lo crea solo, **sin revisores**) o sin Required reviewers', 'Repite la configuración A y vuelve a lanzar'],
        ['El último paso (abrir el PR) falla', 'Falta **Allow GitHub Actions to create and approve pull requests**', 'Repite la configuración B y relanza el trabajo 4 (Re-run)'],
        ['No aparece ningún run', 'Actions sin activar en el fork, o la rama no empieza por `lab/…`', 'Pestaña Actions del fork; revisa el nombre de la rama']]) + '</div>',
          'Los cuatro primeros pasaron de verdad durante los ensayos. El primero es el más engañoso: parece que GitHub no hace nada, pero hay un run anterior esperando aprobación en el mismo grupo. El segundo es un detalle de YAML: los defaults se heredan a todos los trabajos, y un trabajo que no hace checkout no tiene la carpeta. El tercero y el cuarto son, otra vez, la configuración del repositorio. El quinto es el de siempre en un fork.')

    slide('G', 5, 'Qué está verificado', 'qué se comprobó y qué no', 'Qué se comprobó de verdad y qué falta', f'''
<div class="grid2">
 <div class="card"><h3 class="okc">Comprobado en runs reales ({FECHA})</h3>''' + lista([
        'Lote nº ' + RUN['lote'] + ' y validación nº ' + RUN['validar'] + ' en verde.',
        'Nueva versión: igual (nº ' + RUN['igual'] + '), rechazada (nº ' + RUN['rechazo'] + ') y aceptada con aprobación, publicación y PR (nº ' + RUN['completo'] + ').',
        'Rollback: parado (nº ' + RUN['rollback_rojo'] + ') y con PR nº 3 (nº ' + RUN['rollback_verde'] + ').',
        'Configuración del repositorio (cuatro capturas) y panel con los tres modos y la compra simulada.']) + '''</div>
 <div class="card"><h3 class="malc">Sin verificar o sin dato</h3>''' + lista([
        'El compose del panel **en un Codespace**: se probó en local y en Actions.',
        'El `schedule` de las 05:17 UTC **corriendo solo**: se lanzó por push.',
        'Descargar la imagen con `docker pull` desde un Codespace.',
        'Tamaño de la imagen `retencion-api`: **sin dato**.',
        'Las latencias son locales (`TestClient`), no en red.',
        'Duración total del laboratorio para un grupo: **sin dato**.']) + '''</div>
</div>
<div class="callout" style="margin-top:12px">Cada run se puede abrir con <span class="mono">https://github.com/helicr/curso-ml-ia-desarrollo-produccion/actions/runs/&lt;nº&gt;</span>.</div>''',
          'Diapositiva de honestidad: lo comprobado y lo que no. Los números de run permiten abrir cada ejecución en la cuenta del profesor. Lo no verificado es sobre todo el entorno Codespace para el compose y la ejecución programada real; ambos se anotan como pendientes en CODESPACE.md. Si algún alumno los comprueba, que lo cuente para completar la guía.')

    slide('G', 5, 'Autoevaluación', 'Comprueba que lo tienes', 'Seis preguntas', '<div class="grid3">' + ''.join(
        f'<div class="card"><h3>{i}. {md(p)}</h3><p class="small">{md(r)}</p></div>' for i, (p, r) in enumerate([
            ('¿Qué modo usarías para la campaña de cada mañana y cuál para una compra que acaba de ocurrir?', 'Lote para la campaña (puntúa a todos); **online** para lo que acaba de ocurrir (variables calculadas al vuelo).'),
            ('¿Por qué «bajo demanda» no cambia tras la compra simulada?', 'Lee las variables ya calculadas de `fs_produccion`, las de ayer; solo online las recalcula.'),
            ('¿Qué decide la puerta de calidad?', 'Compara el **AUC de test** con `referencia.json` y la tolerancia: igual, rechazada o aceptada.'),
            ('¿Qué hace el *environment* `produccion`?', 'Obliga a que un revisor apruebe antes de publicar en GHCR.'),
            ('¿Por qué el primer rollback se para y qué no borra ninguno?', 'La imagen de la v1 nunca se publicó. Ninguno borra imágenes ni el historial: se restaura la ficha.'),
            ('¿Dónde ves qué versión está en producción?', 'En `models/referencia.json` (y su historial) y en la pestaña **Versiones** del panel.')], 1)) + '</div>',
          'Lea cada pregunta y deje que respondan antes de leer la respuesta. La tercera enlaza con la diapositiva de la puerta; la quinta con el rollback: la comprobación de la imagen es una protección, no un fallo. Cierre con la idea del día en la diapositiva siguiente.')

    slide('G', 4, 'Cierre', 'El mensaje', 'Producción no es subir un modelo: es poder cambiarlo con control y volver atrás', f'''
<div class="msg">Un modelo en producción se <b>mide</b>, se <b>aprueba</b>, se <b>versiona</b> y se puede <b>deshacer</b>.</div>
<div class="grid4" style="margin-top:18px">
 {kpi('0,7471 → 0,7956', 'AUC de test de la v1 a la v2: **+0,0485**, dentro de la tolerancia de 0,02', '')}
 {kpi('79,9 % → 76,2 %', 'probabilidad **online** del cliente 12670 tras una compra simulada; lote y bajo demanda siguen en 79,9 %', '')}
 {kpi('6 min', 'de trabajo de la v2: 191 s + 138 s + 17 s + 14 s, sin contar la espera de la aprobación', '')}
 {kpi('16 s', 'el rollback a la v1: un PR, y **ninguna** imagen borrada de GHCR', '')}
</div>
<div style="text-align:center;margin-top:44px;font-size:44px;font-weight:700;color:var(--acento)">¿Preguntas?</div>''',
          'Cierre con un único mensaje. Las cuatro cifras son reales: el AUC de test del run nº 45030152194, la probabilidad online del panel, la suma de los tiempos de los cuatro trabajos del mismo run (191, 138, 17 y 14 segundos, que dan 360) y el rollback del run nº 45041634741. Este laboratorio no usa Google Cloud; la operación del modelo (deriva, monitoreo, alertas) sigue en S5.')


# =====================================================================================================================================
# Marco: CSS (fondo blanco, sin movimiento al pasar el ratón) y JavaScript del visor
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
  f.innerHTML=`<span>ML e IA · S4 · Laboratorio de producción e2e</span><span><b>${esc(PARTES[s.dataset.part]||'')}</b> · ${i+1} / ${N}</span>`;s.appendChild(f)});
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
    construir()
    js = JS.replace('__PARTES__', json.dumps(PARTES, ensure_ascii=False))
    partes = ''.join(f'<button class="part" data-p="{k}">{esc(v)}</button>' for k, v in PARTES.items())
    return ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>Laboratorio de cierre de S4: producción e2e del caso Retail · ML e IA: de desarrollo a producción</title>\n'
            f'<!-- Generado por generar.py: no se edita a mano. -->\n<style>{CSS}</style>\n</head>\n<body>\n'
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
            '<noscript>Esta presentación necesita JavaScript. El mismo contenido está en guia.md, en esta carpeta.</noscript>\n\n'
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
