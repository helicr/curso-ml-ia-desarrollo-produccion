"""Genera la presentación «Extra de S5: del alias champion de MLflow a un endpoint de Vertex AI, desplegado desde GitHub Actions» (index.html, junto a este archivo).

Sobre el caso Retail del curso (retención a 90 días, Online Retail II): el modelo que manda en MLflow (alias `champion`) llega a un endpoint de
Vertex AI dentro de una imagen de predicción PROPIA que devuelve la probabilidad; se despliega en canario, se prueba, se promueve, se deshace y se
borra, a mano (Cloud Shell) y con tres workflows de GitHub Actions (identidad federada, sin claves, con aprobación). Mensaje: el alias decide
qué modelo manda; el tráfico del endpoint decide qué modelo responde; y lo que cobra es lo que está desplegado.

El visor (CSS y JavaScript: ← → · O índice · S notas · F pantalla completa · botón ⧉ «Copiar todo» · lupa con zoom al clic · pie «x / total» ·
recuadro «Captura pendiente» si falta una imagen) es EL MISMO que el del laboratorio de agentes de S5: se importa de ../laboratorio-agentes/generar.py
para que no se desvíen; aquí solo cambia el rótulo del pie.

HONESTIDAD: las salidas que se enseñan («Qué debes ver») son REALES y están en salidas/ (ejecutadas el 27/11/2026; las de scripts/ contra un gcloud
SIMULADO, y así se rotulan). Las capturas de la consola de Google Cloud y de GitHub son reales y de solo lectura; lo que requiere ejecutar el extra de
verdad (Actions, Vertex) lleva el recuadro «Captura pendiente» y su receta en capturas-pendientes.md. Nunca hay una imagen inventada.

Uso:  python generar.py              escribe index.html
      python generar.py --comprobar  no escribe; sale con 1 si index.html no está al día
"""
import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / 'index.html'

_spec = importlib.util.spec_from_file_location('generar_laboratorio_agentes_visor', AQUI.parent / 'laboratorio-agentes' / 'generar.py')
_AG = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_AG)
CSS, LUPA = _AG.CSS, _AG.LUPA
esc, md, term, codigo, lista, mira, si_falla, tabla, kpi = (_AG.esc, _AG.md, _AG.term, _AG.codigo, _AG.lista, _AG.mira, _AG.si_falla,
                                                          _AG.tabla, _AG.kpi)
_PIE_ORIGINAL = 'ML e IA · S5 · Laboratorio de agentes'
assert _PIE_ORIGINAL in _AG.JS, 'el visor del laboratorio de agentes ha cambiado: revisa el pie'
JS = _AG.JS.replace(_PIE_ORIGINAL, 'ML e IA · S5 · Extra: del champion de MLflow a Vertex AI')

FECHA = '27/11/2026'
CARPETA = '01-Sesiones/S5-MLOps-y-Operacion/extra-vertex-champion'
RAMA = 'lab/vertex-champion/ensayo'
WORKFLOWS = ['vertex-desplegar.yml', 'vertex-rollback.yml', 'vertex-borrar.yml']


def S(nombre, desde=0, hasta=None):
    """Líneas de una salida REAL guardada en salidas/ (la presentación no escribe a mano ninguna salida)."""
    return '\n'.join((AQUI / 'salidas' / nombre).read_text(encoding='utf-8').splitlines()[desde:hasta])


def S_entre(nombre, inicio, fin):
    """Las líneas de una salida real desde la que empieza por inicio hasta la que empieza por in (incluida)."""
    lineas = (AQUI / 'salidas' / nombre).read_text(encoding='utf-8').splitlines()
    i = next(n for n, l in enumerate(lineas) if l.startswith(inicio))
    j = next(n for n, l in enumerate(lineas) if n >= i and l.startswith(fin))
    return '\n'.join(lineas[i:j + 1])


def fuente_adaptador(inicio, fin):
    """Un trozo literal de imagen/vertex_adaptador.py: desde la línea que empieza por `inicio` hasta antes de la que empieza por `fin`."""
    lineas = (AQUI / 'imagen' / 'vertex_adaptador.py').read_text(encoding='utf-8').splitlines()
    i = next(n for n, l in enumerate(lineas) if l.startswith(inicio))
    j = next(n for n, l in enumerate(lineas) if n > i and l.startswith(fin))
    return '\n'.join(lineas[i:j]).rstrip()


def instrucciones_dockerfile():
    return '\n'.join(l for l in (AQUI / 'imagen' / 'Dockerfile.vertex').read_text(encoding='utf-8').splitlines() if l.strip() and not l.startswith('#'))


# ------------------------------------------------------------------------------------------------------------------------
# Capturas (webp). Las reales están en img/; las «pend-*» NO existen y salen como recuadro «Captura pendiente» (ver capturas-pendientes.md).
# ------------------------------------------------------------------------------------------------------------------------
CAPTURAS = {
    'vx-01-registro-modelos.webp': 'Consola de Google Cloud, Vertex AI, Registro de modelos del proyecto del curso (27/11/2026): la lista está vacía («No hay filas para mostrar»). El selector de región enseña us-central1 (Iowa) porque no se cambió; en el laboratorio se elige southamerica-west1 (Santiago)',
    'vx-02-endpoints.webp': 'Consola de Google Cloud, Vertex AI, Extremos (27/11/2026): la lista está vacía; el selector de región enseña us-central1 (Iowa), en el laboratorio se elige southamerica-west1 (Santiago)',
    'vx-03-artifact-registry.webp': 'Consola de Google Cloud, Artifact Registry, Repositorios (27/11/2026): no hay ninguno, porque el repositorio curso de S4 se borró; scripts/preparar_gcp.sh lo vuelve a crear',
    'vx-04-iam.webp': 'Consola de Google Cloud, IAM del proyecto (27/11/2026), con los correos y el nombre del proyecto difuminados: solo están las entidades del propietario; no existe la cuenta sa-github-despliegue de S4 (se borró), así que hay que recrearla antes del ensayo',
    'vx-05-gh-actions.webp': 'GitHub, pestaña Actions del repositorio del curso (27/11/2026): la lista de workflows y de runs de S4 y S5; los tres workflows del extra aparecerán aquí al copiarlos al fork',
    'vx-06-gh-variables.webp': 'GitHub, Settings, Secrets and variables, Actions, Variables (27/11/2026): las cinco variables GCP_* de S4 con los valores difuminados salvo la región; falta GCP_REPO_AR, nueva de este extra',
    'vx-07-gh-environments.webp': 'GitHub, Settings, Environments (27/11/2026): el environment produccion con una regla de protección, los revisores que aprueban cada despliegue',
    's4-aprobacion-environment.webp': 'Captura de S4 de OTRO workflow (nueva-version.yml): un run en espera, «helicr requested your review to deploy to produccion» y el botón Review deployments; el de este extra se verá igual',
    's4-job-summary.webp': 'Captura de S4 de OTRO workflow (desplegar-gcp.yml): un Job Summary «Desplegada en Cloud Run» con imagen, URL y «Entrada en Google Cloud sin claves»; el de este extra lleva la tabla MLflow y Vertex AI',
    't-01-manifiesto.webp': 'Salida real dibujada como imagen: python manifiesto_champion.py generar sobre una copia del registro de MLflow, con el champion en la versión 6 y la 5 como anterior; AUC valid 0.6982, test 0.7471 y las etiquetas de Vertex',
    't-02-prediccion.webp': 'Salida real dibujada como imagen: la respuesta del adaptador arrancado de verdad con las variables AIP_*, con tres clientes: 0.8279 (alta), 0.2760 (baja) y 0.2852 (baja), cada una con clase, tramo y version_mlflow 6',
    't-03-paridad.webp': 'Salida real dibujada como imagen: comparar_paridad.py con la respuesta del adaptador y el modelo cargado a mano: diferencia 0.00e+00 en los tres clientes y «PARIDAD: las predicciones del endpoint y las del modelo local coinciden»',
    't-04-canario.webp': 'Salida real dibujada como imagen, contra un gcloud SIMULADO: desplegar.sh --canario 10 reparte 0=10 y 90 a la anterior, y probar.sh reintenta una vez porque la primera respuesta es de la versión anterior',
    't-05-rollback.webp': 'Salida real dibujada como imagen, contra un gcloud SIMULADO: volver.sh --sin-mlflow lee la versión anterior de las etiquetas y mueve el tráfico de mlflow-v6 a mlflow-v5',
    't-06-pruebas.webp': 'Salida real dibujada como imagen: el resumen de pytest sobre las pruebas de esta carpeta (adaptador, manifiesto, ayudante, scripts, workflows y presentación)',
    'pend-01-form-run-workflow.webp': 'GitHub, Actions, «Vertex AI · desplegar el champion de MLflow», desplegable Run workflow con las nueve entradas (sin lanzarlo)',
    'pend-02-run-esperando-aprobacion.webp': 'Run de «Vertex AI · desplegar el champion de MLflow» tras el push a la rama de ensayo: el trabajo 1 en verde y el 2 esperando la aprobación del environment produccion (Review deployments)',
    'pend-03-resumen-modelo.webp': 'Resumen del trabajo 1 del run («Champion listo para Vertex AI»): versión de MLflow, imagen probada en el runner y la tabla de paridad',
    'pend-04-resumen-desplegado.webp': 'Resumen del trabajo 2 del run («Desplegado en Vertex AI»): la tabla MLflow y Vertex AI con la versión, la huella de datos y el AUC, y la salida de paridad',
    'pend-05-ar-imagen.webp': 'Consola de Google Cloud, Artifact Registry, repositorio curso, paquete retencion-vertex, con la etiqueta v<N>-<huella> de la imagen subida',
    'pend-06-registro-versiones.webp': 'Consola de Google Cloud, Vertex AI, Registro de modelos en Santiago, retencion-90d-champion, pestaña Versiones: dos versiones con sus alias (champion, mlflow-vN) y etiquetas',
    'pend-07-endpoint-canario.webp': 'Consola de Google Cloud, Vertex AI, Extremos en Santiago, retencion-90d-champion-ep con los dos modelos desplegados en 90 % y 10 %',
    'pend-08-cloudshell-subir.webp': 'Cloud Shell: el final de bash scripts/subir_modelo.sh («Listo: MLflow v… -> retencion-90d-champion versión …»)',
    'pend-09-cloudshell-probar.webp': 'Cloud Shell: bash scripts/probar.sh con el canario activo, con los reintentos y «PARIDAD: las predicciones del endpoint y las del modelo local coinciden»',
    'pend-10-rollback-run.webp': 'Run de «Vertex AI · volver a la versión anterior» con su resumen y el reparto de tráfico resultante',
    'pend-11-borrar-confirmacion.webp': 'Formulario Run workflow de «Vertex AI · borrar todo» con BORRAR escrito en la confirmación (antes de pulsar el botón)',
    'pend-12-vacio-final.webp': 'Consola de Google Cloud tras el borrado: Registro de modelos y Extremos de Santiago vacíos, y gcloud ai endpoints list y gcloud ai models list sin filas',
    'pend-13-variables-gcp-repo-ar.webp': 'GitHub, Variables de Actions con GCP_REPO_AR ya añadida a las cinco GCP_* de S4',
}
CAPTURAS_PENDIENTES = [n for n in CAPTURAS if n.startswith('pend-')]

# ------------------------------------------------------------------------------------------------------------------------
# Órdenes que se copian (clave -> orden). Todas están en guia.md.
# ------------------------------------------------------------------------------------------------------------------------
O = {
    'cd_proyecto': 'cd 04-Proyecto-Base',
    'mostrar': 'python -m ia_mlops.alias_modelo mostrar',
    'promover1': 'python -m ia_mlops.alias_modelo promover --version 1',
    'cd_extra': 'cd ../01-Sesiones/S5-MLOps-y-Operacion/extra-vertex-champion',
    'pip_extra': 'python -m pip install -r requirements-extra.txt',
    'manifiesto': 'python manifiesto_champion.py generar --salida vertex-manifiesto.json',
    'puerta': 'python manifiesto_champion.py puerta --manifiesto vertex-manifiesto.json',
    'puerta_cerrada': 'python manifiesto_champion.py puerta --manifiesto vertex-manifiesto.json --auc-minimo 0.99',
    'contexto': 'python preparar_contexto.py --manifiesto vertex-manifiesto.json --destino build/vertex',
    'instancias': 'python instancias.py --salida instancias.json',
    'cd_build': 'cd build/vertex',
    'arrancar': 'AIP_HTTP_PORT=8080 AIP_HEALTH_ROUTE=/salud AIP_PREDICT_ROUTE=/predict CURSO_MODELO_DIR=modelo python vertex_adaptador.py',
    'curl_salud': 'curl http://127.0.0.1:8080/salud',
    'curl_predict': 'curl -X POST http://127.0.0.1:8080/predict -H "content-type: application/json" -d @instancias.json',
    'curl_guardar': 'curl -X POST http://127.0.0.1:8080/predict -H "content-type: application/json" -d @instancias.json -o respuesta.json',
    'paridad': 'python comparar_paridad.py --respuesta respuesta.json --instancias instancias.json --modelo-dir build/vertex/modelo',
    'docker_build': 'docker build --platform linux/amd64 -f build/vertex/Dockerfile.vertex -t retencion-vertex:local build/vertex',
    'docker_run': 'docker run --rm -p 8080:8080 -e AIP_HTTP_PORT=8080 -e AIP_HEALTH_ROUTE=/salud -e AIP_PREDICT_ROUTE=/predict retencion-vertex:local',
    'preparar_gcp': 'bash scripts/preparar_gcp.sh --con-borrado',
    'clonar': 'git clone https://github.com/<tu-usuario>/curso-ml-ia-desarrollo-produccion.git',
    'export_python': 'export CURSO_PYTHON=~/.venv-curso-ml/bin/python',
    'subir': 'bash scripts/subir_modelo.sh',
    'desplegar': 'bash scripts/desplegar.sh',
    'desplegar_canario': 'bash scripts/desplegar.sh --canario 10',
    'probar': 'bash scripts/probar.sh',
    'promover': 'bash scripts/promover.sh',
    'promover_retirar': 'bash scripts/promover.sh --retirar-anterior',
    'volver': 'bash scripts/volver.sh',
    'volver_sin_mlflow': 'bash scripts/volver.sh --sin-mlflow',
    'borrar': 'bash scripts/borrar.sh',
    'mkdir': 'mkdir -p .github/workflows',
    'cp': f'cp {CARPETA}/vertex-*.yml .github/workflows/',
    'rama': f'git switch -c {RAMA}',
    'add': 'git add .github/workflows',
    'commit': 'git commit -m "Extra S5: workflows de Vertex AI"',
    'push': f'git push -u origin {RAMA}',
}

EJERCICIO_SPLIT = 'python vertex_ayuda.py split-nuevo --json ejemplos/endpoint-dos-modelos.json --porcentaje 50'

PARTES = {'A': 'Plan', 'B': 'L1 · Manifiesto', 'C': 'L2 · Imagen', 'D': 'L3 · Vertex AI', 'E': 'L4 · Rollback', 'F': 'L5 · Actions', 'G': 'L6 · Coste', 'H': 'Cierre'}
NOMBRES_PARTE = {'A': 'Qué vamos a hacer', 'B': 'L1 · Del registro de MLflow al manifiesto', 'C': 'L2 · El adaptador y la imagen', 'D': 'L3 · Subir, desplegar y probar en Vertex AI',
                 'E': 'L4 · Volver a la versión anterior', 'F': 'L5 · Los tres workflows de GitHub Actions', 'G': 'L6 · Coste y borrado', 'H': 'Verificación y cierre'}


# ------------------------------------------------------------------------------------------------------------------------
# Piezas propias
# ------------------------------------------------------------------------------------------------------------------------
def cap(nombre, alto=None, nota=None):
    """Una captura (clic = ampliar) o, si aún no existe en img/, el recuadro «Captura pendiente»."""
    alt = CAPTURAS[nombre]                 # el texto alternativo completo (lo que dice la imagen); el pie lleva solo el rótulo exacto de lo que se ve
    estilo = f' style="max-height:{alto}px"' if alto else ''
    extra = f'<br><span class="nota">{md(nota)}</span>' if nota else ''
    pie = alt if nombre.startswith('pend-') else alt.split(': ', 1)[1] if nombre.startswith('t-') else alt.split(': ', 1)[0]
    if (AQUI / 'img' / nombre).is_file() and nombre not in CAPTURAS_PENDIENTES:
        etiqueta = 'Salida real como imagen' if nombre.startswith('t-') else 'Captura real'
        return (f'<figure class="cap" data-img="{nombre}"><button class="zoom" data-src="img/{nombre}" data-alt="{esc(alt)}" title="Ampliar (Esc cierra)">'
                f'<img src="img/{nombre}" alt="{esc(alt)}"{estilo}><span class="lupa">{LUPA} Ampliar</span></button>'
                f'<figcaption><span class="tag ok">{etiqueta}</span> {esc(pie)}{extra}</figcaption></figure>')
    alto_p = f' style="min-height:{min(alto or 200, 260)}px"' if alto else ''
    return (f'<figure class="cap" data-img="{nombre}"><div class="pend"{alto_p}><b>Captura pendiente</b><span class="mono">img/{nombre}</span>'
            f'<span>Cómo hacerla: capturas-pendientes.md</span></div><figcaption><span class="tag warn">Pendiente</span> {esc(pie)}{extra}</figcaption></figure>')


def salida(titulo, texto):
    return f'<div class="realbox"><div class="rk">{esc(titulo)}</div><pre>{esc(texto)}</pre></div>'


def callout(texto, estilo=''):
    return f'<div class="callout"{(" style=" + chr(34) + estilo + chr(34)) if estilo else ""}>{md(texto)}</div>'


def card(titulo, items):
    return f'<div class="card"><h3>{esc(titulo)}</h3>{lista(items)}</div>'


def dos_columnas(izq, der, proporcion='.95fr 1.05fr'):
    return f'<div class="split" style="grid-template-columns:{proporcion}"><div class="col">{izq}</div><div class="capcol">{der}</div></div>'


SLIDES = []
_N = {}
GRANDES = {'Siglas y palabras', 'Cuánto cuesta y cómo no dejarlo encendido', 'Si algo falla', 'Qué se comprobó de verdad', 'Cierre'}


def slide(parte, minutos, titulo, kick, h1, cuerpo, notas):
    n = list(PARTES).index(parte) + 1
    _N[parte] = _N.get(parte, 0) + 1
    antetitulo = f'{n} · {NOMBRES_PARTE[parte]} · {kick}'
    attrs = f' data-part="{parte}" data-min="{minutos}" data-title="{esc(titulo)}"'
    clase = ' grande' if titulo in GRANDES else ''
    SLIDES.append(f'<section class="slide{clase}"{attrs}\n data-notes="{esc(notas)}">\n<p class="kick">{esc(antetitulo)}</p><h1>{md(h1)}</h1>\n{cuerpo}\n</section>')


def pruebas_ok():
    """Cuántas pruebas pasaron en la última ejecución (salidas/30-pruebas.txt, que se escribe a mano... no: con la salida de pytest)."""
    m = re.search(r'(\d+) passed', (AQUI / 'salidas' / '30-pruebas.txt').read_text(encoding='utf-8'))
    return m.group(1) if m else '?'


NOTA_WINDOWS = ('Si usas **Windows**: los `bash scripts/...` y las variables en línea (`AIP_HTTP_PORT=8080 python ...`) van en **Git Bash**; en PowerShell 5.1 no existe `&&` '
                'y en vez de `echo "salida: $?"` se usa `echo $LASTEXITCODE`.')


# ------------------------------------------------------------------------------------------------------------------------
# Contenido
# ------------------------------------------------------------------------------------------------------------------------
def construir():
    SLIDES.clear()
    _N.clear()

    # ------------------------------------------------------------------ A · Plan
    slide('A', 3, 'Portada', 'ML e IA: de desarrollo a producción · S5 · extra', 'Del alias champion de MLflow a un endpoint de Vertex AI', f'''
<div class="cover">
 <p class="sub">En S5 aprendimos que <b>el alias champion decide qué modelo manda</b> en MLflow. Pero lo que responde a un cliente es <b>un servicio desplegado</b>. Este extra une las dos cosas: <b>el champion de MLflow dentro de una imagen propia, en un endpoint de Vertex AI</b>, desplegado y deshecho desde <b>GitHub Actions</b>.</p>
 <div class="chips"><span class="tag">Caso Online Retail II</span><span class="tag">Alias champion</span><span class="tag">Vertex AI</span><span class="tag">Artifact Registry</span><span class="tag">Canario</span><span class="tag">WIF sin claves</span><span class="tag">GitHub Actions</span></div>
 <div class="card" style="margin-top:22px"><h3>Cómo seguirlo</h3><p class="small">Cada orden lleva <b>⧉</b> para copiarla. Las de <b>L1 y L2</b> se pegan en una terminal bash en <span class="mono">extra-vertex-champion</span> y <b>no necesitan nube</b>; las de <b>L3 a L6</b> van en <b>Cloud Shell</b> y <b>cuestan dinero mientras haya algo desplegado</b>. En cada paso: <b>qué debes ver</b> (salida real), <b>si falla</b> y, cuando falta, un recuadro <b>«Captura pendiente»</b>. <b>← →</b> avanzan · <b>O</b> índice · <b>S</b> notas · <b>F</b> pantalla completa · clic en una captura para ampliarla y <b>Esc</b> para cerrarla.</p></div>
 {callout('**Honestidad:** todo lo que corre sin nube está ejecutado y probado. **Vertex AI, Artifact Registry, GitHub Actions y Docker no se han ejecutado todavía**: se marca «sin verificar» y se deja la receta del ensayo.', 'margin-top:12px')}
</div>''',
          f'Presentación del extra de la sesión 5. Las salidas del terminal son reales, ejecutadas el {FECHA}; las de los scripts de Cloud Shell son reales pero contra un gcloud simulado, y se rotulan así. Las capturas de la consola de Google Cloud y de GitHub son reales y de solo lectura. Lo que necesita Vertex o Actions de verdad aparece como captura pendiente. Insista desde el principio en el mensaje: el alias decide qué modelo manda, el tráfico decide cuál responde, y cobra lo que está desplegado.')

    slide('A', 4, 'Por qué llevar el champion a Vertex', 'el problema', 'Mover el alias no cambia lo que responde', f'''
<div class="split" style="grid-template-columns:1.1fr .9fr">
 <div class="col">
  <div class="msg">En MLflow, <b>@champion</b> es un puntero. La imagen de la API <b>no lee ese registro</b>: se construye con el modelo dentro.</div>
  {tabla(['Sin el enlace', 'Con el enlace de este extra'], [
      ['Cambias el alias y **nada** cambia en producción', 'La versión que manda es la que **se publica**: misma versión, misma huella, mismas métricas'],
      ['Nadie sabe qué versión de MLflow responde', 'Cada predicción lleva `version_mlflow`; cada versión de Vertex, sus **etiquetas** (huella, AUC)'],
      ['Volver atrás = reconstruir y desplegar a mano', '`volver.sh` mueve el **tráfico** y el alias a la vez'],
      ['El servicio de Vertex de S4 devolvía la **clase**', 'Una imagen **propia** devuelve la **probabilidad**, la clase y el tramo']])}
 </div>
 <div class="capcol">
  {card('Qué aporta Vertex AI', ['Un **Model Registry** con versiones, alias y etiquetas.', 'Un **endpoint** HTTPS gestionado, con **reparto de tráfico** entre versiones (el canario).', 'Escala y registros en Cloud Logging.'])}
  {card('Qué cuesta', ['Un endpoint **cobra mientras tenga un modelo desplegado**, aunque no reciba peticiones.', 'Precio: **sin dato** ([precios de Vertex AI](https://cloud.google.com/vertex-ai/pricing)).', 'Por eso hay un `borrar.sh` y un workflow para borrar.'])}
 </div>
</div>''',
          'Planteamiento del problema. La nota honesta ya la decía el módulo de alias de S5: la imagen de la API copia el modelo al construirse y no lee el registro, de modo que mover el alias gobierna el registro pero no lo que responde. Este extra implementa la pieza que allí se dejó fuera: llevar la versión champion a un servicio. Anticipe el coste desde el principio: el endpoint cobra mientras tenga algo desplegado.')

    slide('A', 4, 'El plan', 'seis laboratorios', 'Seis laboratorios, de la versión de MLflow al borrado', f'''
<div class="card">''' + tabla(['#', 'Laboratorio', 'Qué haces', 'Dónde', 'Nube'], [
        ['**L1**', 'Manifiesto', 'Leer el champion de MLflow y escribir `vertex-manifiesto.json`, las etiquetas y la puerta de calidad', 'tu terminal', 'no'],
        ['**L2**', 'Imagen', 'El adaptador de Vertex con el modelo dentro; paridad exacta con el modelo local', 'tu terminal', 'no'],
        ['**L3**', 'Vertex AI', 'Subir una versión nueva, desplegar en canario, probar, promover', 'Cloud Shell', '**sí, cobra**'],
        ['**L4**', 'Rollback', 'Mover el tráfico (y el alias) a la versión anterior', 'Cloud Shell', '**sí, cobra**'],
        ['**L5**', 'Actions', 'Lo mismo con tres workflows, WIF sin claves y aprobación', 'GitHub', '**sí, cobra**'],
        ['**L6**', 'Coste', 'Borrar todo y comprobar que no queda nada', 'Cloud Shell o Actions', 'deja de cobrar']]) + '''</div>
<div class="grid3" style="margin-top:12px">
 ''' + card('Orden', ['**L1 y L2 primero:** no necesitan nube y es donde está la lógica que se prueba.', 'L3 a L6 solo en el **ensayo del profesor**, con borrado inmediato.']) + card('Sin claves', ['Ningún secreto: la entrada a Google Cloud es WIF (token de corta vida).', 'Las variables de GitHub no son secretos.']) + card('Sin tocar nada ajeno', ['Los nombres no chocan con la práctica 04 de S4.', 'El registro de MLflow del proyecto no se modifica: se prueba sobre una copia.']) + '''
</div>''',
          'Mapa de los seis laboratorios. L1 y L2 se hacen en cualquier terminal y son los que se han ejecutado y probado aquí. L3 a L6 hablan con Google Cloud: están escritos, probados contra un gcloud simulado, y pendientes de un ensayo real con borrado inmediato. Aclare que los nombres de los recursos son distintos de los de la práctica 04, para poder tener las dos cosas a la vez.')

    slide('A', 4, 'Siglas y palabras', 'vocabulario', 'Las palabras de Vertex AI que vamos a usar', '<div class="card">' + tabla(['Palabra', 'Qué significa aquí'], [
        ['**Model Registry**', 'El catálogo de modelos de Vertex AI. Un **modelo** tiene **versiones** (1, 2, 3...). Es el equivalente del registro de MLflow'],
        ['**Versión y alias**', 'Cada subida con `--parent-model` es una versión nueva del mismo modelo. Un **alias** (`champion`, `mlflow-v6`) es un nombre para una versión'],
        ['**Endpoint**', 'El servicio HTTPS gestionado. Recibe peticiones y las reparte entre los modelos **desplegados** en él. **Cobra mientras tenga un modelo desplegado**'],
        ['**Modelo desplegado**', 'Una versión puesta en un endpoint, con su máquina (`e2-standard-2`) y sus réplicas. Tiene un **id** distinto del de la versión'],
        ['**Tráfico (traffic split)**', 'El reparto en % entre los modelos desplegados: `0=10,1000=90`. La clave **0** es el modelo que se despliega ahora. **Debe sumar 100**'],
        ['**Canario**', 'Desplegar la versión nueva con poco tráfico (10 %), probarla con peticiones reales y solo entonces darle el 100 %'],
        ['**Contenedor propio**', 'Una imagen tuya que cumple el contrato de Vertex (`AIP_HTTP_PORT`, ruta de salud, ruta de predicción). Frente al **pre-construido**, que solo devuelve la clase'],
        ['**Artifact Registry**', 'Donde se guarda la imagen. Debe ser **regional** y de la **misma región** que el endpoint (no multirregional)'],
        ['**WIF**', '*Workload Identity Federation*: GitHub pide a Google un token de corta vida con su identidad OIDC. **Sin claves**']]) + '</div>',
          'Vocabulario. Insista en tres: la clave cero del reparto de tráfico es el modelo que se está desplegando; el reparto debe sumar cien; y el endpoint cobra mientras tenga un modelo desplegado. Todo lo demás son nombres para algo que ya conocen de MLflow: versión, alias, registro.')

    # ------------------------------------------------------------------ B · L1
    slide('B', 4, 'Mapa MLflow y Vertex', 'equivalencias', 'Cada idea de MLflow tiene su pareja en Vertex', '<div class="card">' + tabla(['En MLflow (S5)', 'En Vertex AI', 'Cómo se enlazan'], [
        ['Modelo registrado `retencion-90d`', '**Modelo** `retencion-90d-champion` en el Model Registry', 'etiqueta `mlflow_modelo`'],
        ['**Versión** 6', '**Versión** del mismo modelo (con `--parent-model`)', 'alias `mlflow-v6` y etiqueta `mlflow_version=6`'],
        ['Alias `champion`', 'Alias `champion` de la versión + el **tráfico** del endpoint', 'el alias sigue a MLflow; el tráfico decide quién responde'],
        ['`champion_anterior` (la v5)', 'Etiqueta `mlflow_version_anterior=5`', '`volver.sh` la lee para saber a dónde volver'],
        ['Huella de datos y AUC', 'Etiquetas `huella_datos`, `auc_valid`, `auc_test`', 'se escriben al subir la versión'],
        ['`promover` / `volver`', '`desplegar` + `promover` / **mover el tráfico**', '`volver.sh` hace las dos cosas a la vez'],
        ['Etiquetas `vertex_*` en la versión', '(la vuelta) dónde está desplegada', '`manifiesto_champion.py anotar`']]) + '''</div>
<p class="small" style="margin-top:8px">Fuente de las versiones y los alias: <span class="mono">docs.cloud.google.com/vertex-ai/docs/model-registry/versioning</span> · de las etiquetas: <span class="mono">docs.cloud.google.com/resource-manager/docs/labels-overview</span>.</p>''',
          'La tabla de equivalencias es la clave del extra. Subraye la última fila: el enlace se cierra en las dos direcciones. De MLflow a Vertex con las etiquetas y los alias; de Vertex a MLflow con las etiquetas vertex_ que escribe el comando anotar. Con un registro local de MLflow esas etiquetas viven en el registro de quien lo ejecuta; con un servidor compartido las vería todo el equipo.')

    slide('B', 5, 'Pre-construido o propio', 'la diferencia con la práctica 04', 'Contenedor pre-construido que devuelve la clase, o propio que devuelve la probabilidad', f'''
<div class="grid2">
 <div class="card"><h3>Práctica 04 de S4 · pre-construido</h3>{lista([
     'Imagen de Vertex para **scikit-learn 1.6** (la más reciente de la tabla oficial el 25/11/2026).',
     'El proyecto usa **1.9.1**: hubo que **reentrenar** el mismo modelo con 1.6.1.',
     'Llama a `predict()`: devuelve la **clase** (0 o 1). **Comprobado el 25/11/2026.**',
     'No hay nada que construir ni subir; el modelo va en un bucket (`model.joblib`).'])}</div>
 <div class="card"><h3>Este extra · propio</h3>{lista([
     'Imagen **tuya** con el **mismo `requirements-api.lock`** que la API: scikit-learn **1.9.1**. No se reentrena nada.',
     'El adaptador llama a `predict_proba`: devuelve la **probabilidad**, la clase y el **tramo** de negocio.',
     'El modelo va **dentro de la imagen** (sin bucket, sin `--artifact-uri`).',
     'Hay que construir, subir a Artifact Registry y mantener un contrato.'])}</div>
</div>
<div style="margin-top:12px">{tabla(['', 'Pre-construido', 'Propio'], [
    ['Respuesta', 'clase (0 o 1)', '`probabilidad`, `clase`, `tramo`, `version_mlflow`'],
    ['Versión de scikit-learn', '1.6 (reentrenar)', '1.9.1 (la del proyecto)'],
    ['Validación de la entrada', 'ninguna propia', 'las mismas reglas que la API de S2 (422 con mensaje claro)'],
    ['Lo que hay que mantener', 'nada', 'el adaptador, el Dockerfile y la imagen'],
    ['Probado aquí', 'sí (25/11/2026, en Vertex real)', 'adaptador sí; la imagen en Vertex **sin verificar**']])}</div>''',
          'La diferencia con la práctica cuatro. El contenedor pre-construido ahorra trabajo pero obliga a reentrenar con una versión antigua de scikit-learn y devuelve la clase, no la probabilidad; con la clase no se pueden hacer los tramos de negocio. El contenedor propio cuesta más de mantener pero sirve exactamente el modelo del champion. Esa comparación de la clase frente a la probabilidad se comprobó en Vertex real el veinticinco de noviembre.')

    slide('B', 5, 'El manifiesto del champion', 'paso 1', 'Leer el champion de MLflow y escribir el manifiesto', dos_columnas(
        term('Terminal bash · en extra-vertex-champion · una orden cada vez', [
            '# 1) la carpeta del proyecto y tu registro (si no tienes champion, ponlo)', O['cd_proyecto'], O['mostrar'], O['promover1'],
            '# 2) la carpeta del extra', O['cd_extra'], O['pip_extra'],
            '# 3) el manifiesto', O['manifiesto']]) + mira([
            'La versión del alias: `@champion -> versión 6 de MLflow (anterior: 5)`.',
            '`AUC valid 0.6982 · test 0.7471` y la **huella de datos** `35a94deb4e04ab4a`.',
            'La **etiqueta de la imagen** `v6-35a94deb4e04ab4a` y el alias de Vertex `mlflow-v6`.',
            'Las **etiquetas** de Vertex ya con el formato válido (`auc_valid=0_6982`).']),
        cap('t-01-manifiesto.webp', 260, 'Registro de ensayo: una copia con el champion en la v6; el del proyecto no se toca.') + si_falla([
            '`no tiene el alias @champion`: `promover --version N` (la segunda orden de la izquierda).',
            '`No module named ia_mlops`: estás en la carpeta equivocada.']) + f'<p class="small">{md(NOTA_WINDOWS)}</p>'),
          'Primer paso: del registro de MLflow al manifiesto. La salida es real y se obtuvo sobre una copia del registro del proyecto con el champion puesto en la versión seis y la cinco como anterior; el registro original no tiene alias champion y no se ha tocado. El manifiesto es el único sitio donde se decide la etiqueta de la imagen, el alias de Vertex y las etiquetas; el resto de scripts solo lo leen.')

    slide('B', 5, 'Etiquetas y puerta de calidad', 'reglas de Google Cloud', 'Las etiquetas tienen reglas; la puerta decide si se publica', dos_columnas(
        tabla(['Regla de una etiqueta de GCP', 'Valor'], [
            ['Etiquetas por recurso', 'hasta **64**'], ['Clave', '1 a **63** caracteres, empieza por **letra minúscula**'], ['Valor', '0 a **63** caracteres'],
            ['Caracteres', 'minúsculas, números, `_` y `-`'], ['Por eso', 'el AUC `0.6982` se escribe `0_6982`']]) + callout('La referencia de `gcloud ai models upload --labels` dice «64 caracteres»; se aplica el límite menor, **63**, que es el seguro. Fuente: `docs.cloud.google.com/resource-manager/docs/labels-overview`.', 'margin-top:8px'),
        term('Terminal bash · puerta de calidad antes de publicar', [O['puerta'], O['puerta_cerrada']]) +
        salida('Real · salidas/03-puerta.txt y 04-puerta-cerrada.txt', S('03-puerta.txt') + '\n' + S('04-puerta-cerrada.txt')) + mira([
            'Con el mínimo por defecto la puerta se **abre**; con `--auc-minimo 0.99`, **«CERRADA»** y salida 2.',
            'Comprueba también la huella de datos y que el manifiesto **no sea simulado**.']) + callout('**El 0.65 es provisional**: no sale de ninguna medición (con 114 y 250 clientes el AUC oscila más por azar). Se acuerda con negocio.')),
          'Las etiquetas de Google Cloud tienen reglas estrictas; el punto de un número decimal no vale, por eso el AUC se escribe con guion bajo. Hay una pequeña contradicción en la documentación: la referencia de gcloud dice sesenta y cuatro caracteres y la de etiquetas de Resource Manager sesenta y tres; aplicamos el límite menor. La puerta de calidad es la misma idea que la de nueva-version.yml de S4: si no pasa, no se publica nada. El umbral de 0,65 es provisional y hay que decirlo así.')

    # ------------------------------------------------------------------ C · L2
    slide('C', 5, 'El contrato de Vertex', 'documentación oficial', 'Un contenedor propio tiene que cumplir cuatro cosas', f'''
<div class="split" style="grid-template-columns:1.05fr .95fr">
 <div class="col">{tabla(['Variable o ruta', 'Qué es'], [
     ['`AIP_HTTP_PORT`', 'el puerto (8080 si no existe); se toma de `--container-ports`. El servidor escucha en **0.0.0.0**'],
     ['`AIP_HEALTH_ROUTE`', 'ruta de **salud**: debe responder **200** en menos de 10 s (`--container-health-route`)'],
     ['`AIP_PREDICT_ROUTE`', 'ruta de **predicción** (`--container-predict-route`)'],
     ['`AIP_STORAGE_URI`', 'vacía si no hay `--artifact-uri`: **no hace falta** si el modelo va en la imagen'],
     ['Entrada', '`POST` con `{"instances": [...], "parameters": ...}`'],
     ['Salida', '`{"predictions": [...]}`, **una por instancia**']])}
 </div>
 <div class="capcol">
  {card('Lo que manda la documentación', ['**No definas** variables con el prefijo `AIP_` (las pone Vertex): el Dockerfile **no** lleva `ENV AIP_...`.', 'La imagen debe estar en **Artifact Registry regional**, de la misma región que el endpoint.', 'El agente de servicio de Vertex necesita `roles/artifactregistry.reader`: **automático** si la imagen es del mismo proyecto.', 'Límite de 1,5 MB por petición y respuesta en un endpoint público compartido.'])}
  <p class="small">Fuente: <span class="mono">docs.cloud.google.com/vertex-ai/docs/predictions/custom-container-requirements</span> (27/11/2026). La documentación no dice si se pueden añadir campos al nivel superior de la respuesta: la versión de MLflow va <b>dentro de cada predicción</b>.</p>
 </div>
</div>''',
          'El contrato oficial. Aquí la documentación manda sobre el diseño inicial: la propuesta hablaba de poner variables de entorno de Vertex en el Dockerfile, pero la documentación dice expresamente que no se definan variables con el prefijo AIP; las pone Vertex a partir de las rutas y el puerto que se declaran al subir el modelo. Por eso el adaptador lee esas variables con valores por defecto y el Dockerfile no las define. Tampoco hay bucket: con contenedor propio el artifact uri es opcional.')

    slide('C', 5, 'El adaptador por dentro', 'imagen/vertex_adaptador.py', 'Lo esencial del adaptador: validar, predecir, devolver', dos_columnas(
        codigo('imagen/vertex_adaptador.py (extracto: la predicción y el tramo)', fuente_adaptador('    def predecir(self, filas):', '    def info(self):') + '\n\n' + fuente_adaptador('def tramo(probabilidad):', '# ----')),
        card('Qué hace', ['Carga `modelo_mlflow/` de la imagen y **comprueba la firma** contra `config.FEATURES` y el esquema de la API: si no coincide, la salud da **503** (Vertex no envía tráfico).', 'Cada instancia es una **lista de 13 números en el orden de `FEATURES`**; solo `dias_medios_entre_compras` admite `null`.', 'Aplica las **mismas reglas que la API de S2** (`esquemas.Cliente`): rangos y coherencia.', '**Nunca registra** los valores recibidos: solo cuántas instancias, el código y el milisegundo.']) +
        card('Qué devuelve', ['`probabilidad` (predict_proba), `clase` (1 si ≥ 0,5), `tramo` (alta, media, baja de `config.SEGMENTOS_RECOMPRA`) y `version_mlflow`.']), '1.05fr .95fr'),
          'El adaptador es un módulo pequeño de FastAPI. Dos decisiones importan. Primera: reutiliza el esquema de la API de S2, de modo que la validación es la misma y un cliente imposible se rechaza igual en los dos servicios. Segunda: comprueba la firma del modelo contra la lista de variables; si alguien reentrena con una variable nueva y no actualiza el esquema, el servicio no arranca listo, y Vertex no le enviará tráfico. La versión de MLflow va en cada predicción para saber qué versión contestó cuando hay dos desplegadas.')

    slide('C', 6, 'Probar el adaptador sin Docker', 'paso 2', 'Arrancarlo como lo arranca Vertex y llamarlo con curl', dos_columnas(
        term('Terminal 1 · en extra-vertex-champion', ['# la carpeta de construcción y las instancias', O['contexto'], O['instancias'], '# arrancar el adaptador en la carpeta de la imagen', O['cd_build'], O['arrancar']]) +
        term('Terminal 2 · en extra-vertex-champion', [O['curl_salud'], O['curl_predict']]) + mira([
            '`{"estado":"ok"}` y tres predicciones: **0.8279** (alta), **0.2760** (baja) y **0.2852** (baja).',
            'Cada una con `clase`, `tramo` y `version_mlflow: 6`.',
            'En la terminal 1, **una línea JSON por petición** sin valores de clientes.']),
        cap('t-02-prediccion.webp', 300) + callout('Es la misma probabilidad que da `python -m ia_mlops.alias_modelo cargar`: **0.8279**.') + si_falla([
            '`Address already in use`: otro proceso en el 8080; usa `AIP_HTTP_PORT=8081`.', '`ModuleNotFoundError: ia_mlops`: arrancaste fuera de `build/vertex`.'])),
          'Sin Docker se puede probar casi todo. El adaptador se arranca en la carpeta que prepara el script, con las mismas variables que pondría Vertex, y se llama con curl. La salida es real. El cliente activo da cero coma ocho dos siete nueve, que es exactamente lo que da el comando cargar del módulo de alias; esa igualdad es la que comprueba la prueba de paridad. Con Docker el procedimiento es el mismo pero dentro de la imagen, y eso no se ha podido ejecutar aquí.')

    slide('C', 4, 'Errores claros, sin romper', 'el contrato también se prueba', 'Una petición mala devuelve 422 con el motivo, y el servicio sigue', dos_columnas(
        salida('Real · salidas/11-adaptador-errores.txt', S('11-adaptador-errores.txt')),
        mira(['**422** y un mensaje que dice la **instancia** y el **campo**.', 'Una instancia como diccionario: «debe ser una **LISTA** de 13 números… No un diccionario».', 'Una variable fuera de contrato (`es_reino_unido = 2`) se rechaza igual que en la API de S2.', 'El error **no repite** el valor recibido.']) +
        card('Lo que cubren las pruebas', ['Cuerpo vacío, JSON roto, `NaN`, más de 1000 instancias, booleanos, textos, longitudes distintas de 13.', 'Tras un error, `/salud` y la siguiente petición **siguen bien**.', 'Sin modelo, `/salud` y `/predict` dan **503**.'])),
          'Los errores se prueban igual que los aciertos. Hay pruebas para cuerpos vacíos, json roto, valores no finitos, más de mil instancias, booleanos y longitudes incorrectas. Un detalle de seguridad: el mensaje de error nunca repite el valor recibido, y el registro tampoco escribe valores de clientes; solo cuántas instancias, el código y el tiempo.')

    slide('C', 5, 'Paridad exacta', 'lo que contesta el servicio frente al modelo cargado a mano', 'La diferencia entre Vertex y el modelo local tiene que ser cero', dos_columnas(
        term('Terminal bash · en extra-vertex-champion', ['# guarda la respuesta del adaptador en un archivo', O['curl_guardar'], '# y compárala con el modelo cargado a mano', O['paridad']]) + mira([
            'Una tabla con la **diferencia `0.00e+00`** en las tres instancias.',
            '`PARIDAD: las predicciones del endpoint y las del modelo local coinciden.`',
            'Salida **0** si coinciden, **1** si hay diferencias, **3** si contestó **otra versión** (canario).']) + si_falla([
            '`PARIDAD ROTA`: la imagen no lleva el modelo del manifiesto; compara `version_mlflow` y la huella.']),
        cap('t-03-paridad.webp', 300) + callout('Las pruebas comprueban la **misma paridad por dos caminos**: contra `alias_modelo.cargar_y_puntuar` (carga por alias) y contra el modelo cargado a mano, con `predict()` para la clase.')),
          'La paridad es la prueba que da confianza: la probabilidad que sirve el adaptador es idéntica, hasta la última cifra, a la del modelo cargado a mano. Se comprueba por dos caminos, el del módulo de alias, que carga por alias del registro, y el modelo cargado directamente, y además la clase coincide con la que daría el contenedor pre-construido. Este mismo comparador es el que usa probar.sh contra el endpoint real.')

    slide('C', 5, 'El Dockerfile de Vertex', 'imagen/Dockerfile.vertex', 'La imagen: el mismo lock que la API, el modelo dentro, sin AIP_*', dos_columnas(
        codigo('imagen/Dockerfile.vertex (sin comentarios)', instrucciones_dockerfile()),
        mira(['**Sin variables** `AIP_*`, sin `:latest` y sin root (`USER 10001`).', '`--platform linux/amd64`: Vertex es amd64; en un Mac con chip ARM sin él la imagen no arrancaría.']) +
        callout('**Compatible con las dos formas de construir la API.** La de `develop` (`COPY models/modelo_mlflow`) y la multietapa (`--build-context modelo=models`): esta imagen no usa **ninguna**. `preparar_contexto.py` reúne el mismo `requirements-api.lock`, tres archivos de `ia_mlops` y el modelo exportado del registro, y **se niega** si el modelo y el lock tienen otro scikit-learn.') +
        term('Con Docker (Cloud Shell o tu equipo) · SIN VERIFICAR', [O['docker_build'], O['docker_run']]) + f'<p class="small">Este portátil no tiene Docker: {md("ni el `build` ni el `run` se han ejecutado")}.</p>'),
          'El Dockerfile es corto a propósito. Se apoya en el mismo archivo de versiones exactas que la API, de modo que el modelo se abre con la misma versión de scikit-learn con la que se guardó. No depende de cómo se construya la imagen de la API: ni de la de develop ni de la multietapa del otro trabajo, porque su contexto lo prepara un script aparte. Lo que no se ha podido ejecutar aquí es docker build y docker run: no hay Docker en este portátil.')

    # ------------------------------------------------------------------ D · L3
    slide('D', 6, 'Preparar Google Cloud y GitHub', 'una vez · quien administra el proyecto', 'La nube y GitHub tienen que estar listos antes de lanzar nada', dos_columnas(
        tabla(['Variable de GitHub', 'Valor'], [['`GCP_PROYECTO`', 'el proyecto del curso'], ['`GCP_REGION`', '`southamerica-west1` (Santiago)'], ['`GCP_PROVEEDOR_WIF`', 'el proveedor de identidad federada'],
                                              ['`GCP_CUENTA_DESPLIEGUE`', '`sa-github-despliegue@…`'], ['`GCP_REPO_AR`', 'opcional · por defecto `curso`'], ['`CURSO_MLFLOW_URI`', 'opcional · MLflow compartido']]) +
        term('Cloud Shell · la persona que administra el proyecto · SIN EJECUTAR todavía', [O['preparar_gcp']]) +
        callout('`preparar_gcp.sh` **no crea** modelos, endpoints ni cuentas: habilita las APIs, crea el repositorio de Artifact Registry y da a la cuenta de despliegue `roles/aiplatform.user` y `roles/artifactregistry.writer` (y `repoAdmin` solo en ese repositorio para el borrado). **Sin verificar** que `aiplatform.user` baste para todo.', 'margin-top:8px'),
        '<div class="grid2">' + cap('vx-06-gh-variables.webp', 170) + cap('vx-07-gh-environments.webp', 170) + '</div>' + cap('pend-13-variables-gcp-repo-ar.webp', 50) +
        callout('Hoy en GitHub: las cinco variables `GCP_*` de S4 (valores difuminados) y el environment `produccion` con **1 regla de protección**. Falta `GCP_REPO_AR`. En Google Cloud, la cuenta `sa-github-despliegue` de S4 **ya no existe** (captura de IAM en la siguiente diapositiva): hay que recrearla antes del ensayo.'),
        '.95fr 1.05fr'),
          'Antes del ensayo hay que preparar dos sitios. En Google Cloud, las APIs, el repositorio de Artifact Registry regional y los permisos de la cuenta de despliegue. En GitHub, las variables y el environment con revisores. Las capturas son reales y de solo lectura: muestran que las cinco variables de S4 siguen en GitHub, que falta la del repositorio de Artifact Registry, que el environment produccion tiene una regla de protección, y que en IAM ya no existe la cuenta de despliegue de S4, porque se borró al acabar. Hay que recrearla con el script de S4 antes del ensayo.')

    slide('D', 5, 'Lo que hay hoy en la consola', 'solo lectura · 27/11/2026', 'Tres listas vacías y un IAM sin la cuenta de S4: así empieza el ensayo', f'''
<div class="grid4">
 <div>{cap('vx-01-registro-modelos.webp', 160)}</div>
 <div>{cap('vx-02-endpoints.webp', 160)}</div>
 <div>{cap('vx-03-artifact-registry.webp', 160)}</div>
 <div>{cap('vx-04-iam.webp', 160)}</div>
</div>
<div class="grid2" style="margin-top:10px">
 {callout('El selector de región de las dos primeras enseña **us-central1**: no se cambió para no interactuar con la página (solo se abrió con la URL). En el laboratorio se elige **southamerica-west1 (Santiago)**, que admite Model Registry y predicción online de modelos propios (fuente: `docs.cloud.google.com/vertex-ai/docs/general/locations`).')}
 {callout('**Cuando acabe el ensayo, las tres listas tienen que volver a verse así.** Es la prueba visual del borrado (captura pendiente nº 12).')}
</div>''',
          'Estas capturas son reales, hechas en solo lectura el veintisiete de noviembre. No hay ningún modelo, ningún endpoint ni ningún repositorio de imágenes: la nube está limpia, y en IAM ya no existe la cuenta de despliegue de S4. Son también el criterio de cierre del ensayo: después de borrar, las tres listas tienen que volver a verse así. Sea honesto con el selector de región: muestra us-central1 porque no se pudo cambiar sin interactuar con la página; en la práctica de S4 sí se capturó con Santiago.')

    slide('D', 6, 'Subir el modelo', 'paso 3 · una versión NUEVA del mismo modelo', 'Una versión de MLflow es una versión de Vertex', dos_columnas(
        term('Cloud Shell · en extra-vertex-champion · CUESTA almacenamiento', ['# una vez: el proyecto entrenado y el champion en Cloud Shell', O['clonar'], O['export_python'], '# subir', O['subir']]) + mira([
            'El manifiesto, `Contexto listo` y el repositorio (o `Ya existe`).',
            '`docker build` y `docker push` de `retencion-vertex:v6-35a94deb4e04ab4a`.',
            '`gcloud ai models upload` con `--container-ports`, `--container-predict-route`, `--container-health-route`, `--labels` y, desde la segunda vez, **`--parent-model`** y `--version-aliases champion,mlflow-v6`.',
            '**Repetirlo no hace nada nuevo**: la imagen y la versión se reconocen.']) + si_falla([
            '`PERMISSION_DENIED`: falta `roles/aiplatform.user` o `artifactregistry.writer` (apartado 5 de la guía).', '`docker: command not found`: **sin verificar** que Cloud Shell traiga Docker; ver la guía.']),
        salida('Real · contra un gcloud SIMULADO · salidas/19-subir-anterior.txt', S_entre('19-subir-anterior.txt', '== 2.', 'Siguiente')) + cap('pend-08-cloudshell-subir.webp', 60) + '<div class=\"grid2\">' + cap('pend-06-registro-versiones.webp', 60) + cap('pend-05-ar-imagen.webp', 60) + '</div>'),
          'Subir el modelo es crear una versión nueva del mismo modelo del Model Registry, no un modelo nuevo; la primera vez se crea el modelo con model id, y las siguientes se usa parent model y alias. La salida de la izquierda es real pero contra un gcloud simulado: prueba la lógica del script, no Google Cloud. Las dos capturas pendientes se harán en el ensayo.')

    slide('D', 6, 'Desplegar en canario', 'paso 4 · ¡ESTO COBRA!', 'La versión nueva entra con el 10 % del tráfico', dos_columnas(
        term('Cloud Shell · en extra-vertex-champion · COBRA mientras esté desplegado', [O['desplegar'], '# la siguiente vez, con una versión ya desplegada, entra en canario', O['desplegar_canario']]) +
        tabla(['Situación', '`--traffic-split`'], [['Endpoint **vacío**', '`0=100`'], ['Ya hay otra (id 1000), canario 10', '`0=10,1000=90`'], ['Canario 0 (directo al 100 %)', '`0=100,1000=0`']]) + callout('La clave **`0`** es el modelo que se despliega ahora; el reparto **debe sumar 100** y nombrar a los ya desplegados (fuente: `docs.cloud.google.com/vertex-ai/docs/predictions/deploy-model-api`). Con dos versiones desplegadas hay **dos máquinas**. Tarda varios minutos: **sin medir**.', 'margin-top:8px') + si_falla([
            '`Quota` o «insufficient resources»: cuota de CPU de la región; otra máquina con `CURSO_MAQUINA`.', 'El `--model <id>@<versión>` **sin verificar** en `gcloud`: ver la guía (alternativa con la API REST).']),
        cap('t-04-canario.webp', 360) + cap('pend-07-endpoint-canario.webp', 130)),
          'El despliegue en canario es la parte delicada. Si el endpoint está vacío, la versión recibe todo. Si ya hay otra, la nueva entra con el diez por ciento y la anterior conserva el resto. El reparto debe sumar cien y nombrar a todos los modelos ya desplegados; el simulador de las pruebas lo exige igual que Vertex. Con dos versiones desplegadas el coste se duplica. Lo que se ve es real pero contra el gcloud simulado.')

    slide('D', 5, 'Probar y comparar', 'paso 5', 'Probar con el canario: reintenta hasta que conteste la versión nueva', dos_columnas(
        term('Cloud Shell · en extra-vertex-champion', [O['probar']]) + mira([
            'Envía los **tres clientes** de ejemplo y compara con el modelo local.',
            'Con canario, **la primera respuesta puede ser de la versión anterior**: `intento 1: contestó otra versión (tráfico dividido); reintento...`',
            'Termina con `PARIDAD: las predicciones del endpoint y las del modelo local coinciden.`']) + si_falla([
            '`PARIDAD ROTA`: la imagen no lleva el modelo del manifiesto.', 'Sale **3** tras 40 intentos: sube `--intentos` o el canario.']),
        salida('Real · contra un gcloud SIMULADO · salidas/23-probar-canario.txt', S_entre('23-probar-canario.txt', '== gcloud ai', 'PARIDAD')) + cap('pend-09-cloudshell-probar.webp', 150)),
          'Probar contra un endpoint con dos versiones tiene una trampa: no se sabe cuál contesta. Por eso cada predicción lleva la versión de MLflow y el script reintenta hasta que conteste la esperada. La salida es real, contra un gcloud simulado cuyo endpoint alterna entre las versiones con tráfico. En Vertex real el reparto es aleatorio, de modo que el número de reintentos varía.')

    slide('D', 5, 'Promover al 100 %', 'paso 6 · y retirar la anterior', 'Pasar el tráfico a la nueva no apaga la anterior', dos_columnas(
        term('Cloud Shell · en extra-vertex-champion', [O['promover'], '# espera 10 min y retira la anterior (deja de cobrar)', O['promover_retirar']]) + mira([
            '`Reparto: 1000=0,1001=100` y la tabla de tráfico.', 'Sin `--retirar-anterior`: «La versión anterior sigue desplegada con 0 % y **SIGUE COBRANDO**».']) + callout('La documentación recomienda esperar **10-15 minutos** tras mover el tráfico antes de hacer `undeploy` (para que terminen las peticiones en vuelo). Fuente: `docs.cloud.google.com/vertex-ai/docs/predictions/undeploy-model`.', 'margin-top:8px') + si_falla([
            'Un valor `0` en `endpoints update --traffic-split`: **sin verificar** que Vertex lo acepte tal cual.']),
        salida('Real · contra un gcloud SIMULADO · salidas/24-promover.txt', S('24-promover.txt'))),
          'Promover es mover el tráfico, no apagar nada. La versión anterior queda desplegada con cero por ciento, lo cual sirve para volver en segundos, pero sigue cobrando. Retirarla es una decisión: con la opción retirar anterior el script espera diez minutos, como recomienda la documentación, y hace undeploy. Que Vertex acepte un valor cero en el reparto de endpoints update es algo que no se ha podido verificar.')

    # ------------------------------------------------------------------ E · L4
    slide('E', 6, 'Volver a la versión anterior', 'rollback · mover el tráfico y el alias', 'Volver atrás son dos movimientos a la vez', dos_columnas(
        term('Cloud Shell · en extra-vertex-champion', [O['volver'], '# en un workflow (el registro de MLflow no es el tuyo): sin mover el alias', O['volver_sin_mlflow']]) + mira([
            '`Sirve ahora: mlflow-v6 … -> vuelve a: mlflow-v5` (la anterior sale de la etiqueta `mlflow_version_anterior`).',
            'Si la anterior **sigue desplegada** (0 %): solo se mueve el tráfico, **segundos**.',
            'Si ya se **retiró**: se vuelve a **desplegar** desde el Model Registry (minutos, **sin medir**).',
            'Y `Rollback: @champion: v6 -> v5. La v6 sigue registrada; no se ha borrado nada.`']) + si_falla([
            '`no guardó una versión anterior`: `bash scripts/volver.sh --a-version N`.']),
        cap('t-05-rollback.webp', 170) + salida('Real · gcloud SIMULADO · salidas/26-volver-con-redespliegue.txt (la anterior ya retirada)', S('26-volver-con-redespliegue.txt', 7, 14)) + cap('pend-10-rollback-run.webp', 60)),
          'El rollback mueve dos cosas a la vez: el tráfico del endpoint y el alias champion de MLflow. Nada se borra. Hay dos caminos según la versión anterior siga desplegada o no, y los dos están probados contra el gcloud simulado. La segunda salida es la del caso difícil: la versión anterior ya se retiró y hay que volver a desplegarla desde el Model Registry, que tarda minutos y cuesta máquina.')

    # ------------------------------------------------------------------ F · L5
    slide('F', 5, 'Los tres workflows', 'GitHub Actions', 'Desplegar, volver y borrar, con aprobación y sin claves', dos_columnas(
        tabla(['Workflow', 'Qué hace', 'Entradas'], [
            ['`vertex-desplegar.yml`', '1 · champion, **puerta de calidad** y prueba de la imagen. 2 · **aprobación** y despliegue', '`version_mlflow`, `dos_versiones`, `region`, `maquina`, `min_replicas`, `canario`, `auc_minimo`, `promover`, `retirar_anterior`'],
            ['`vertex-rollback.yml`', 'Mueve el tráfico a la versión anterior (aprobación)', '`a_version`, `region`, `retirar_actual`'],
            ['`vertex-borrar.yml`', '**Confirmación escrita** (`BORRAR`) y luego aprobación; undeploy, endpoint, modelo e imágenes', '`confirmacion`, `region`, `con_imagenes`']]) +
        callout('Permisos `contents: read` en todo y `id-token: write` **solo** donde se entra en Google Cloud. Sin secretos ni `credentials_json`. Las entradas pasan por `env:` y **nunca** se interpolan en el script. Un `concurrency` común: desplegar, volver y borrar no se pisan.', 'margin-top:8px'),
        term('Terminal en la raíz de TU fork · se copian, no están instalados en el curso', [O['mkdir'], O['cp'], O['rama'], O['add'], O['commit'], O['push']]) +
        cap('vx-05-gh-actions.webp', 120) + cap('pend-01-form-run-workflow.webp', 60), '1.1fr .9fr'),
          'Los tres workflows se copian al fork del alumno; no están instalados en el repositorio del curso. Un push a una rama lab barra vertex-champion lanza el de desplegar y se detiene en la aprobación. Los permisos son mínimos: id-token solo en los trabajos que entran en Google Cloud. El de borrar pide escribir la palabra BORRAR antes de entrar en la nube, y además espera la aprobación del environment. La captura de Actions es real y de solo lectura; el formulario Run workflow no se pudo capturar porque estos archivos aún no están en la rama por defecto.')

    slide('F', 6, 'El workflow de desplegar, por dentro', 'dos trabajos', 'Primero se prueba todo sin nube; luego se pide permiso', dos_columnas(
        tabla(['Trabajo 1 · modelo (sin nube)', 'Trabajo 2 · desplegar (aprobación + WIF)'], [
            ['Entrena y deja el `champion`', '**Espera la aprobación** (`environment: produccion`)'],
            ['**Puerta de calidad** (AUC, huella, pruebas del adaptador)', 'Entra en Google Cloud con WIF (`auth@v2`)'],
            ['Construye la imagen y **la arranca en el runner**', 'Sube **la misma imagen** a Artifact Registry'],
            ['Salud y **paridad** con el modelo local', '`subir_modelo.sh` → `desplegar.sh` → `probar.sh` → `promover.sh`'],
            ['Guarda la imagen y el contexto (artefactos)', 'Job Summary con la tabla MLflow y Vertex AI']]) + callout('Si el trabajo 1 falla, **no se entra en Google Cloud**: no se publica nada.', 'margin-top:8px'),
        cap('s4-aprobacion-environment.webp', 270) + cap('pend-02-run-esperando-aprobacion.webp', 110), '1.05fr .95fr'),
          'El workflow tiene dos trabajos con una frontera clara. El primero no toca la nube: entrena, pasa la puerta de calidad, construye la imagen y la arranca en el runner para comprobar la salud y la paridad. Solo si todo va bien el segundo pide la aprobación y entra con identidad federada. La imagen que se sube es exactamente la que se probó, como en el workflow de Cloud Run de S4. La captura de la aprobación es de otro workflow de S4: el mecanismo es idéntico; la de este extra queda pendiente.')

    slide('F', 5, 'El resumen y el enlace', 'Job Summary', 'El resumen deja el enlace MLflow ↔ Vertex a la vista de todos', dos_columnas(
        tabla(['MLflow', 'Vertex AI'], [['modelo «retencion-90d» @champion', 'modelo `retencion-90d-champion`'], ['versión **6**', 'versión **N** (alias `mlflow-v6`, `champion`)'], ['huella de datos `35a94deb4e04ab4a`', 'etiqueta `huella_datos`'], ['AUC valid 0.6982', 'etiqueta `auc_valid=0_6982`']]) +
        mira(['El endpoint, la región y la imagen.', '«Entrada en Google Cloud **sin claves**».', 'El aviso: **el endpoint COBRA** mientras tenga un modelo desplegado.', 'La salida de paridad.']),
        cap('s4-job-summary.webp', 180) + cap('pend-04-resumen-desplegado.webp', 150) + cap('pend-03-resumen-modelo.webp', 100)),
          'El Job Summary es lo primero que mira quien aprueba. Lleva la tabla que enlaza las dos cosas, el aviso de coste y la salida de paridad. La captura real que se ve es el resumen de otro workflow de S4, para que se vea cómo luce un resumen; los dos de este extra están pendientes del ensayo.')

    slide('F', 5, 'De dónde sale el champion en el runner', 'limitación honesta', 'El registro de MLflow del curso es local: el runner crea el suyo', f'''
<div class="grid2">
 <div class="card"><h3>Lo que hace el workflow hoy</h3>{lista([
     '`models/mlflow.db` **no está en git**. Como `nueva-version.yml` de S4, el runner **entrena** con la muestra y crea **su propio registro**.',
     'El champion de ese run **no es** «el de tu portátil»: es el de ese run.',
     'Con `dos_versiones` entrena dos veces y promueve en cadena (v1, luego v2) para que **exista una anterior** a la que volver.',
     'El alias de MLflow **no se mueve** desde el rollback del workflow: el registro del runner desaparece.'])}</div>
 <div class="card"><h3>Lo que haría una empresa</h3>{lista([
     'Un **servidor de MLflow compartido** (`CURSO_MLFLOW_URI`): el workflow leería **ese** champion.',
     'Las etiquetas `vertex_*` se escribirían ahí con `manifiesto_champion.py anotar` (paso condicional ya escrito).',
     '**Sin verificar**: nunca se ha ejecutado con un servidor compartido.'])}</div>
</div>
{callout('**Resumen:** el workflow demuestra el **mecanismo** (puerta, imagen, aprobación, canario, rollback). Con un registro local no demuestra «el champion de mi portátil». Está dicho en el propio workflow, en la guía y aquí.', 'margin-top:12px')}''',
          'La limitación más importante del extra, dicha sin rodeos. En el curso el registro de MLflow es un archivo local que no está en git; en un runner de GitHub no existe. El workflow hace lo mismo que nueva-version: reentrena con los datos de muestra y crea su propio registro. Demuestra el mecanismo completo, pero no el champion del portátil del alumno. En una empresa habría un servidor compartido, y el workflow tiene ya un paso condicional preparado para él, sin verificar.')

    # ------------------------------------------------------------------ G · L6
    slide('G', 5, 'Cuánto cuesta y cómo no dejarlo encendido', 'borrar', 'Lo que cobra es lo que está desplegado: bórralo', dos_columnas(
        card('Qué cobra y qué no', ['Un **endpoint** cobra **mientras tenga un modelo desplegado**, aunque no reciba peticiones.', 'Con dos versiones desplegadas: **dos máquinas** (`e2-standard-2` × 1 cada una).', 'Subir el modelo y la imagen: almacenamiento. Un modelo **sin desplegar** no usa máquinas.', 'Precio: **sin dato** ([precios de Vertex AI](https://cloud.google.com/vertex-ai/pricing)).']) +
        term('Cloud Shell · en extra-vertex-champion · deja todo a cero', [O['borrar']]) + callout('Orden obligatorio: **undeploy** de cada versión → **endpoint** → **modelo** (todas sus versiones) → **imágenes**. No toca el repositorio de Artifact Registry ni los recursos de la práctica 04. Es **idempotente**.'),
        salida('Real · gcloud SIMULADO · salidas/28-borrar.txt', S('28-borrar.txt', 3, 10)) + '<div class=\"grid2\">' + cap('pend-11-borrar-confirmacion.webp', 60) + cap('pend-12-vacio-final.webp', 60) + '</div>'),
          'Lo importante: el endpoint cobra mientras tenga algo desplegado. El script de borrado respeta el orden que exige Vertex, porque no se puede borrar un endpoint con modelos desplegados, y es idempotente. Hay también un workflow de borrado con confirmación escrita. El precio no está en la documentación enlazada: se dice sin dato. El enlace con el presupuesto y las alertas de S4 sigue siendo válido: avisa pero no corta.')

    slide('G', 5, 'Si algo falla', 'tabla de síntomas', 'Los fallos más probables y qué hacer', '<div class="card">' + tabla(['Síntoma', 'Causa probable', 'Qué hacer'], [
        ['`Puerta de calidad CERRADA`', 'AUC por debajo del mínimo, sin huella o manifiesto simulado', 'Mira el motivo; el 0.65 es provisional; reentrena o acuerda el umbral'],
        ['`modelo guardado con scikit-learn X y el lock instalaría la Y`', 'Se reentrenó con otro scikit-learn', '`make lock` o reentrena con el del lock'],
        ['`PERMISSION_DENIED` en `aiplatform` o `artifactregistry`', 'Faltan roles de la cuenta de despliegue', '`preparar_gcp.sh`; el mensaje dice el permiso'],
        ['El endpoint nunca queda listo', 'La salud no responde 200 en 10 s: el modelo no cargó (firma distinta)', 'Registros del endpoint (Cloud Logging); `docker run` en local'],
        ['`PARIDAD ROTA`', 'La imagen no lleva el modelo del manifiesto', 'Compara `version_mlflow` y la huella'],
        ['`no hay a dónde volver`', 'La versión no guardó `mlflow_version_anterior`', '`bash scripts/volver.sh --a-version N`'],
        ['`No se puede borrar el endpoint`', 'Aún tiene modelos desplegados', 'Repite `bash scripts/borrar.sh` (hace el undeploy)'],
        ['La imagen no se borra desde el workflow', 'Falta `roles/artifactregistry.repoAdmin`', 'Bórrala desde Cloud Shell con `bash scripts/borrar.sh`']]) + '</div>',
          'Tabla de síntomas. Los dos primeros se reproducen en local y tienen pruebas. Los de permisos y de endpoints solo se pueden confirmar en el ensayo real. Hay que insistir en que cuando falle algo en Google Cloud el mensaje de error de gcloud dice qué permiso falta.')

    # ------------------------------------------------------------------ H · Cierre
    slide('H', 5, 'Qué se comprobó de verdad', 'honestidad', 'Lo que está probado, lo que no, y lo que no tiene dato', f'''
<div class="grid3">
 <div class="card"><h3 class="okc">Ejecutado y probado</h3>{lista([
     f'**{pruebas_ok()} pruebas** de pytest pasan (adaptador, manifiesto, ayudante, scripts, workflows y esta presentación).',
     'El **adaptador** (contrato, 422, arranque real) con **paridad exacta** frente al modelo de MLflow.',
     'Los **siete scripts**, ejecutados con bash contra un **gcloud simulado**: subir, canario con reintento, promover, volver con y sin la anterior, borrar.',
     'Los **tres workflows**: YAML, permisos, WIF sin claves, entradas, `bash -n` de cada paso.',
     'El registro de MLflow del proyecto **no se tocó** (huella SHA-256 antes y después).'])}</div>
 <div class="card"><h3 class="malc">Sin verificar</h3>{lista([
     '**Vertex AI real**: `--parent-model`, canario, `endpoints update`, rollback.', '**Artifact Registry** y **WIF** reales.', '**GitHub Actions**: los tres workflows.', '**Docker** (no hay en este portátil).',
     'Los **nombres de campo JSON** de `gcloud ... describe` que usan los scripts.', 'La sintaxis `--model <id>@<versión>` de `deploy-model`.'])}</div>
 <div class="card"><h3 class="malc">Sin dato</h3>{lista([
     'El **precio** de Vertex AI y de Artifact Registry.', 'El **tiempo** de despliegue y de rollback.', 'Un **AUC mínimo** razonable (el 0.65 es provisional).'])}
  <p class="small" style="margin-top:8px"><b>Ningún recurso</b> se creó en Google Cloud para esta entrega. El ensayo real, con borrado inmediato, está en la guía (apartado 9).</p></div>
</div>
{cap('t-06-pruebas.webp', 100)}''',
          'Diapositiva de honestidad. Lo probado es todo lo que corre sin nube y la lógica de los scripts contra un gcloud simulado. Lo no probado es todo lo que requiere Vertex, Artifact Registry, Actions o Docker. Insista en que el simulador implementa las reglas de la documentación pero usa nombres de campo JSON que se suponen; si Google los llama de otra forma, las pruebas pasan y el script falla en la nube. Por eso el ensayo real es necesario.')

    slide('H', 6, 'Ejercicios', 'para hacer y para pensar', 'Cinco ejercicios', '<div class="card">' + tabla(['#', 'Ejercicio', 'Cómo se comprueba'], [
        ['**1**', 'Calcula a mano el `--traffic-split` de un canario del **50 %** con dos modelos ya desplegados; luego compruébalo con `' + EJERCICIO_SPLIT + '`', 'La suma da 100 y la clave `0` es el modelo nuevo'],
        ['**2**', 'Manda al adaptador una instancia como **diccionario** y otra con **12 números**; lee los dos mensajes', 'Dos errores 422 que dicen la instancia y qué esperaban'],
        ['**3**', 'Escribe a mano las etiquetas de un modelo con AUC de test **0.7471** y huella `35a94deb4e04ab4a` según las reglas de GCP', 'Valores en minúsculas, sin punto: `0_7471`'],
        ['**4**', 'Sube `--auc-minimo` a **0.80** y mira qué hace la puerta; ¿qué número pondrías tú y **de dónde sale**?', 'La puerta se cierra; el 0.65 es provisional y se acuerda con negocio'],
        ['**5**', '(Con el profesor, en el ensayo) Lanza `vertex-rollback.yml` y **cronometra** cuánto tarda con la anterior desplegada y con la anterior retirada', 'Hasta entonces el tiempo es **sin dato**']]) + '</div>',
          'Ejercicios. Los cuatro primeros se hacen sin nube. El primero usa un archivo de ejemplo con la forma supuesta del json de un endpoint. El quinto es solo para el ensayo del profesor y sirve para rellenar un dato que hoy no existe: el tiempo del rollback. Recuerde que cualquier cifra de tiempo o de coste que se obtenga debe anotarse con su fuente.')

    slide('H', 4, 'Cierre', 'El mensaje', 'El alias decide qué modelo manda; el tráfico decide cuál responde', '''
<div class="msg">Un <b>champion</b> que no llega a producción es solo una etiqueta. Con un <b>manifiesto</b>, una <b>imagen propia</b>, un <b>canario</b> y un <b>rollback</b> que mueve el tráfico, la versión que manda es la que responde, y todo lo demás se <b>borra</b>.</div>
<div class="grid4" style="margin-top:18px">
 ''' + kpi('0.8279', 'probabilidad del cliente «activo» desde el adaptador: **la misma** que `alias_modelo cargar` (diferencia `0.00e+00`)', '') + kpi('13 → 3', 'variables en una lista → probabilidad, **clase** y **tramo** (más la versión de MLflow)', '') + kpi('Suma 100', 'el reparto de tráfico siempre suma 100 y la clave `0` es el modelo nuevo: `0=10,1000=90`', '') + kpi('0 recursos', 'creados en Google Cloud para esta entrega: lo de la nube sigue **sin verificar**', '') + '''
</div>
<div style="text-align:center;margin-top:20px;font-size:40px;font-weight:700;color:var(--acento)">¿Preguntas?</div>''',
          'Cierre con un único mensaje: el alias decide qué modelo manda y el tráfico decide cuál responde. Las cuatro cifras son reales: la probabilidad del cliente de ejemplo, que coincide con el módulo de alias; la forma de la entrada y de la salida; la regla del reparto de tráfico; y que no se creó ningún recurso en Google Cloud. El siguiente paso es el ensayo real con borrado inmediato y las trece capturas pendientes.')


def html_completo():
    construir()
    js = JS.replace('__PARTES__', json.dumps(PARTES, ensure_ascii=False))
    partes = ''.join(f'<button class="part" data-p="{k}">{esc(v)}</button>' for k, v in PARTES.items())
    return ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>Extra de S5: del alias champion de MLflow a un endpoint de Vertex AI · ML e IA: de desarrollo a producción</title>\n'
            f'<!-- Generado por generar.py: no se edita a mano. -->\n<style>{CSS}</style>\n</head>\n<body>\n'
            '<div id="prog"></div>\n<div id="viewport"><div id="stage">\n\n' + '\n\n'.join(SLIDES) + '\n\n</div></div>\n\n'
            '<aside id="notes" aria-label="Notas del ponente"><h3>Notas del ponente</h3><div id="notetext"></div><p class="small" id="notemin"></p></aside>\n'
            '<div id="index" aria-label="Índice"><h2>Índice</h2><div class="grid" id="idxgrid"></div></div>\n'
            '<div id="zoombox" aria-label="Captura ampliada"><p>Esc o clic para cerrar</p><img id="zoomimg" alt=""></div>\n'
            '<nav id="bar" aria-label="Controles">\n'
            '  <button id="bprev" aria-label="Anterior">←</button><button id="bnext" aria-label="Siguiente">→</button>\n'
            f'  <span id="count">1 / 1</span><span id="clockref" title="Minuto planificado acumulado (propuesta)"></span>\n  {partes}\n'
            '  <span class="sp"></span>\n'
            '  <a id="bhome" href="../index.html" title="Volver al índice de la sesión S5">⌂ S5</a><button id="bidx">Índice (O)</button><button id="bnotes">Notas (S)</button><button id="bfull">Pantalla completa (F)</button>\n'
            '</nav>\n'
            '<noscript>Esta presentación necesita JavaScript. El mismo contenido está en guia.md, en esta carpeta.</noscript>\n\n'
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
