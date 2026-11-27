"""Genera la presentación «Laboratorio de MLOps clásico de S5: deriva, alias y alertas» (index.html, junto a este archivo).

Sobre el caso Retail del curso (retención a 90 días, Online Retail II), cada persona vigila el modelo que ya está en producción:
mide la deriva de los datos (PSI y KS) y la del rendimiento (AUC por corte), versiona el modelo con un alias de MLflow y vuelve
atrás con un solo comando, y deja un workflow de GitHub Actions que avisa con un issue y un run en rojo. Mensaje: un modelo en
producción se vigila, se versiona y se puede deshacer.

El visor (CSS y JavaScript: ← → · O índice · S notas · F pantalla completa · Esc · botón ⧉ «Copiar todo» · lupa con zoom al clic ·
pie «x / total» · recuadro «Captura pendiente» si falta una imagen) es EL MISMO que el del laboratorio de agentes de S5: se importa
de ../laboratorio-agentes/generar.py para que no se desvíen; aquí solo cambia el rótulo del pie. Las capturas se leen de img/ (webp).

Todas las salidas que se enseñan («Qué debes ver») son REALES: se ejecutaron el 26/11/2026 sobre la copia de ensayo del proyecto
(Windows, Python 3.11, muestra de 150 clientes). Las capturas de GitHub Actions están PENDIENTES: las hará el profesor al lanzar
los ensayos; hasta entonces se dibuja el recuadro «Captura pendiente».

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
JS = _AG.JS.replace(_PIE_ORIGINAL, 'ML e IA · S5 · Laboratorio de MLOps clásico')

FECHA = '26/11/2026'
USUARIO = 'helicr'
CARPETA = '01-Sesiones/S5-MLOps-y-Operacion/laboratorio-mlops'
RAMA_BASE = 'lab/mlops-s5'
RAMA_ESTABLE = 'lab/monitoreo/estable'
RAMA_DERIVA = 'lab/monitoreo/deriva'
WORKFLOWS = ['monitoreo.yml']

# Capturas (webp) -> qué se ve de verdad (texto alternativo y pie). Todas son de GitHub Actions y están PENDIENTES: las hará el profesor.
CAPTURAS = {
    'm-01-estable-verde.webp': 'Run de «Monitoreo del modelo» en la rama lab/monitoreo/estable: los trabajos «1 · Preparar datos y modelo» y «2 · Deriva de datos y de rendimiento» en verde y «3 · Alerta» omitido (gris), con el aviso de que el workflow no abrió ningún issue',
    'm-02-resumen-estable.webp': 'Resumen del run de la rama lab/monitoreo/estable: «Sin alerta», la tabla de PSI y KS por variable con antiguedad_dias en 0.410 (moderada con el umbral de 0.50) y la tabla de AUC por corte (0.6982, 0.7534 y 0.7423)',
    'm-03-deriva-rojo.webp': 'Run de «Monitoreo del modelo» en la rama lab/monitoreo/deriva: los trabajos 1 y 2 en verde y «3 · Alerta» en ROJO, con la anotación «Alerta de deriva» y el enlace al issue abierto',
    'm-04-resumen-deriva.webp': 'Resumen del run de la rama lab/monitoreo/deriva: «ALERTA», la tabla de PSI con las cinco variables marcadas como «supera el umbral» (antiguedad_dias 2.830, recencia_dias 0.437, frecuencia_180d 0.400, monto_90d 0.293, frecuencia_90d 0.276)',
    'm-05-issue-alerta.webp': 'Issue abierto por el workflow con la etiqueta alerta-deriva: título «Alerta de deriva: 5 variables superan el PSI 0.25 (referencia 2010-12-01, actual 2011-12-10)», la tabla de variables y el enlace al run',
    'm-06-segunda-alerta.webp': 'El mismo issue tras repetir el run: en lugar de un segundo issue, un comentario «Nueva medición con deriva» con el enlace al nuevo run; el issue sigue siendo el mismo (#6)',
}
CAPTURAS_PENDIENTES = []                    # las seis ya están capturadas de ensayos reales en Actions (26/11)

# ------------------------------------------------------------------------------------------------------------------------
# Salidas REALES (copia de ensayo del 26/11/2026). Se enseñan tal cual salen.
# ------------------------------------------------------------------------------------------------------------------------
S_CORTES = '''Cortes guardados en fs_cliente_corte (10):
  2010-06-01     69 clientes  partición train  etiqueta a 90 días: sí
  2010-07-01     80 clientes  partición train  etiqueta a 90 días: sí
  2010-08-01     84 clientes  partición train  etiqueta a 90 días: sí
  2010-09-01     88 clientes  partición train  etiqueta a 90 días: sí
  2010-10-01     93 clientes  partición train  etiqueta a 90 días: sí
  2010-11-01    103 clientes  partición train  etiqueta a 90 días: sí
  2010-12-01    109 clientes  partición train  etiqueta a 90 días: sí
  2011-03-01    114 clientes  partición valid  etiqueta a 90 días: sí
  2011-06-01    119 clientes  partición test   etiqueta a 90 días: sí
  2011-09-01    131 clientes  partición test   etiqueta a 90 días: sí
Corte «ahora» (día siguiente a la última factura): 2011-12-10'''

S_DATOS = '''Deriva de datos: referencia 2010-12-01 (109 clientes, fs_cliente_corte) frente a actual 2011-12-10 (148 clientes, calculado al vuelo)
PSI con 10 intervalos por cuantiles de la referencia (suelo 0.0001); umbral de alarma 0.25.

variable                        PSI      KS  estado
antiguedad_dias               2.830   0.736  deriva  <-- supera el umbral
recencia_dias                 0.437   0.259  deriva  <-- supera el umbral
frecuencia_180d               0.400   0.240  deriva  <-- supera el umbral
monto_90d                     0.293   0.213  deriva  <-- supera el umbral
frecuencia_90d                0.276   0.213  deriva  <-- supera el umbral
unidades_total                0.147   0.122  moderada
frecuencia                    0.137   0.145  moderada
dias_medios_entre_compras     0.115   0.128  moderada
productos_distintos           0.107   0.124  moderada
monto_total                   0.097   0.138  estable
devoluciones                  0.018   0.064  estable
ticket_medio                  0.012   0.064  estable
es_reino_unido                0.000   0.010  estable

DERIVA: 5 de 13 variables superan el umbral (antiguedad_dias, recencia_dias, frecuencia_180d, monto_90d, frecuencia_90d).
Ojo: con 109 clientes el PSI oscila por azar; es un aviso, no una sentencia.
salida: 1'''

S_PAR = '''variable                        PSI      KS  estado
antiguedad_dias               0.410   0.261  deriva  <-- supera el umbral
recencia_dias                 0.228   0.175  moderada
monto_90d                     0.092   0.106  estable
...
DERIVA: 1 de 13 variables superan el umbral (antiguedad_dias).
salida: 1'''

S_PAR_UMBRAL = '''umbral de alarma 0.5.
variable                        PSI      KS  estado
antiguedad_dias               0.410   0.261  moderada
recencia_dias                 0.228   0.175  moderada
...
Sin deriva relevante: ninguna variable supera el umbral.
salida: 0'''

S_REND = '''corte       uso                        clientes positivos      AUC    caída
2011-03-01  validación                      114        52   0.6982  +0.0000
2011-06-01  prueba                          119        46   0.7534  -0.0552
2011-09-01  prueba                          131        55   0.7423  -0.0441

AVISO: El corte 2011-03-01 es de entrenamiento o validación: el modelo se ajustó o se eligió con él y el AUC ahí SOBREESTIMA. Para una medida honesta usa cortes de prueba o posteriores al entrenamiento.
Sin deriva de rendimiento relevante.
salida: 0'''

S_REND_ENT = '''corte       uso                        clientes positivos      AUC    caída
2010-12-01  entrenamiento                   109        41   0.8497  +0.0000
2011-03-01  validación                      114        52   0.6982  +0.1515
2011-06-01  prueba                          119        46   0.7534  +0.0963
2011-09-01  prueba                          131        55   0.7423  +0.1074

AVISO: Los cortes 2010-12-01, 2011-03-01 son de entrenamiento o validación: el modelo se ajustó o se eligió con ellos y el AUC ahí SOBREESTIMA. [...]
AVISO: El AUC cae 0.1515 respecto al primer corte medido (2010-12-01), más que la tolerancia de 0.05. Si ese primer corte es de entrenamiento, parte de la caída es sobreajuste y no deriva.
DERIVA DE RENDIMIENTO: sí.
salida: 1'''

S_MOSTRAR1 = '''Modelo registrado «retencion-90d»: 1 versiones
  v1   alias: -            valid_auc 0.6982 · test_auc 0.7471
Alias: ninguno'''

S_PROMOVER1 = '@champion -> v1 (no había champion anterior: no se guardó a dónde volver).'

S_CARGAR1 = '''Cargado models:/retencion-90d@champion -> versión 1
Probabilidad de comprar en 90 días del cliente de cliente_ejemplo.json: 0.8279'''

S_PIPE_COMPLETO = '''  OPERACIONAL: clientes             5,942 filas
  OPERACIONAL: lineas_factura   1,067,371 filas
  ...
  ML: train  23,760 filas | tasa de recompra 48.1 %
  ML: valid   4,512 filas | tasa de recompra 35.1 %
  ML: test   10,132 filas | tasa de recompra 38.0 %
  regresion_logistica        AUC valid 0.786 | test 0.796 | precision media test 0.735
  ...
  Registrado en MLflow como «retencion-90d», version 2.'''

S_MOSTRAR2 = '''Modelo registrado «retencion-90d»: 2 versiones
  v1   alias: @champion    valid_auc 0.6982 · test_auc 0.7471
  v2   alias: -            valid_auc 0.7855 · test_auc 0.7956
Alias: @champion -> v1'''

S_PROMOVER2 = '@champion: v1 -> v2. La v2 recuerda a la v1: para volver, `volver`. No se ha borrado nada.'

S_CARGAR2 = '''Cargado models:/retencion-90d@champion -> versión 2
Probabilidad de comprar en 90 días del cliente de cliente_ejemplo.json: 0.7245'''

S_VOLVER = 'Rollback: @champion: v2 -> v1. La v2 sigue registrada; no se ha borrado nada.'

S_VOLVER_SIN = '''Error: La versión 1, que es @champion, no guardó una versión anterior: no hay a dónde volver. Si sabes cuál quieres, usa  promover --version N
salida: 2'''

# ------------------------------------------------------------------------------------------------------------------------
# Órdenes que se copian (clave -> orden). Todas, en bash (Codespace) y, salvo las de git, desde 04-Proyecto-Base.
# ------------------------------------------------------------------------------------------------------------------------
O = {
    'cd': 'cd 04-Proyecto-Base',
    'pip': 'python -m pip install -r requirements-dev.txt',
    'operacional': 'python -m ia_mlops.operacional',
    'pipeline': 'python -m ia_mlops.pipeline',
    'cortes': 'python -m ia_mlops.deriva cortes',
    'datos': 'python -m ia_mlops.deriva datos --referencia 2010-12-01 --actual 2011-12-10',
    'salida': 'echo "salida: $?"',
    'datos_json': 'python -m ia_mlops.deriva datos --referencia 2010-12-01 --actual 2011-12-10 --json reports/datos.json',
    'leer_json': "python -c \"import json; d = json.load(open('reports/datos.json', encoding='utf-8')); print(d['hay_deriva'], d['superan_umbral'])\"",
    'psi_ejemplo': 'python -c "from ia_mlops import deriva; print(round(deriva.psi_detalle([1, 2, 3, 4], [1, 1, 1, 4], intervalos=2)[\'psi\'], 4))"',
    'par': 'python -m ia_mlops.deriva datos --referencia 2010-08-01 --actual 2010-09-01',
    'par_umbral': 'python -m ia_mlops.deriva datos --referencia 2010-08-01 --actual 2010-09-01 --umbral-psi 0.5',
    'rend': 'python -m ia_mlops.deriva rendimiento --cortes 2011-03-01 2011-06-01 2011-09-01',
    'rend_ent': 'python -m ia_mlops.deriva rendimiento --cortes 2010-12-01 2011-03-01 2011-06-01 2011-09-01',
    'mostrar': 'python -m ia_mlops.alias_modelo mostrar',
    'promover1': 'python -m ia_mlops.alias_modelo promover --version 1',
    'cargar': 'python -m ia_mlops.alias_modelo cargar',
    'descargar': 'python -m ia_mlops.dataset descargar',
    'pipe_completo': 'python -m ia_mlops.pipeline --fuente completo',
    'promover2': 'python -m ia_mlops.alias_modelo promover --version 2',
    'volver': 'python -m ia_mlops.alias_modelo volver',
    'borrar_db': 'rm data/processed/curso.db',
    'pipe_muestra': 'python -m ia_mlops.pipeline --fuente muestra',
    'cd_raiz': 'cd ..',
    'switch_develop': 'git switch develop',
    'pull': 'git pull',
    'rama': f'git switch -c {RAMA_BASE}',
    'mkdir': 'mkdir -p .github/workflows',
    'cp': f'cp {CARPETA}/monitoreo.yml .github/workflows/',
    'add': 'git add .github/workflows',
    'commit': 'git commit -m "Laboratorio de MLOps clásico de S5: workflow de monitoreo"',
    'push': f'git push -u origin {RAMA_BASE}',
    'estable_rama': f'git switch -c {RAMA_ESTABLE}',
    'estable_push': f'git push -u origin {RAMA_ESTABLE}',
    'volver_base': f'git switch {RAMA_BASE}',
    'deriva_rama': f'git switch -c {RAMA_DERIVA}',
    'deriva_push': f'git push -u origin {RAMA_DERIVA}',
    'borrar_rama_estable': f'git push origin --delete {RAMA_ESTABLE}',
    'borrar_rama_deriva': f'git push origin --delete {RAMA_DERIVA}',
}

PARTES = {'A': 'Plan', 'B': 'L1 · Datos', 'C': 'L2 · Rendimiento', 'D': 'L3 · Alias', 'E': 'L4 · Alertas', 'F': 'L5 · Costes', 'G': 'Cierre'}
NOMBRES_PARTE = {'A': 'Qué vamos a hacer', 'B': 'L1 · Deriva de datos', 'C': 'L2 · Deriva de rendimiento',
                 'D': 'L3 · Versionar y volver atrás con alias', 'E': 'L4 · Alertas con GitHub Actions',
                 'F': 'L5 · Costes y orden', 'G': 'Verificación y cierre'}


# ------------------------------------------------------------------------------------------------------------------------
# Piezas propias (las que dependen de esta carpeta o no existen en el laboratorio de agentes)
# ------------------------------------------------------------------------------------------------------------------------
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


def salida(titulo, texto):
    return f'<div class="realbox"><div class="rk">{esc(titulo)}</div><pre>{esc(texto)}</pre></div>'


def callout(texto, estilo=''):
    return f'<div class="callout"{(" style=" + chr(34) + estilo + chr(34)) if estilo else ""}>{md(texto)}</div>'


def card(titulo, items):
    return f'<div class="card"><h3>{esc(titulo)}</h3>{lista(items)}</div>'


def dos_columnas(izq, der, proporcion='.9fr 1.1fr', mira_a_la_derecha=False):
    if mira_a_la_derecha:      # la tarjeta «Qué debes ver» pasa debajo de la salida: las dos columnas quedan equilibradas
        m = re.search(r'<div class="card mira">.*?</ul></div>', izq, re.S)
        if m:
            izq = izq.replace(m.group(0), '', 1)
            der = der + m.group(0)
    return (f'<div class="split" style="grid-template-columns:{proporcion}"><div class="col">{izq}</div>'
            f'<div class="capcol">{der}</div></div>')


SLIDES = []
_N = {}
GRANDES = {'El plan', 'Siglas y palabras', 'Costes y orden', 'Si algo falla', 'Qué se comprobó de verdad', 'Cierre'}


def slide(parte, minutos, titulo, kick, h1, cuerpo, notas):
    n = list(PARTES).index(parte) + 1
    _N[parte] = _N.get(parte, 0) + 1
    antetitulo = f'{n} · {NOMBRES_PARTE[parte]} · {kick}'
    attrs = f' data-part="{parte}" data-min="{minutos}" data-title="{esc(titulo)}"'
    clase = ' grande' if titulo in GRANDES else ''
    SLIDES.append(f'<section class="slide{clase}"{attrs}\n data-notes="{esc(notas)}">\n'
                  f'<p class="kick">{esc(antetitulo)}</p><h1>{md(h1)}</h1>\n{cuerpo}\n</section>')


NOTA_WINDOWS = ('Si usas **Windows** (cmd o PowerShell 5.1) en vez del Codespace: no existe `&&`; en lugar de `echo "salida: $?"` usa '
                '`echo $LASTEXITCODE` (PowerShell) o `echo %ERRORLEVEL%` (cmd); `rm` es `del`, `cp` es `copy` y `mkdir -p` es `mkdir`.')


# ------------------------------------------------------------------------------------------------------------------------
# Contenido
# ------------------------------------------------------------------------------------------------------------------------
def construir():
    SLIDES.clear()
    _N.clear()

    # ------------------------------------------------------------------ A · Qué vamos a hacer
    slide('A', 3, 'Portada', 'ML e IA: de desarrollo a producción · S5', 'Laboratorio de MLOps clásico: vigilar, versionar y avisar', f'''
<div class="cover">
 <p class="sub">El modelo de <b>retención a 90 días</b> ya está en producción desde S4. Ahora toca lo que hace un equipo de MLOps cada día: <b>medir si los datos o el modelo han cambiado</b>, <b>cambiar de versión y volver atrás sin miedo</b> y <b>dejar que GitHub avise</b> cuando algo se mueve.</p>
 <div class="chips"><span class="tag">Caso Online Retail II</span><span class="tag">PSI y KS</span><span class="tag">AUC por corte</span><span class="tag">Alias de MLflow</span><span class="tag">GitHub Actions</span><span class="tag">Issues</span></div>
 <div class="card" style="margin-top:22px"><h3>Cómo seguirlo</h3><p class="small">Cada orden lleva <b>⧉</b> para copiarla. Se pega <b>en la terminal bash del Codespace</b>, siempre <b>desde la carpeta <span class="mono">04-Proyecto-Base</span></b>, salvo las de git (L4), que van en la raíz del repositorio y lo dicen. En cada paso hay <b>qué debes ver</b> (salida real) y <b>si falla</b>. <b>← →</b> avanzan · <b>O</b> índice · <b>S</b> notas · <b>F</b> pantalla completa · clic en una captura para ampliarla y <b>Esc</b> para cerrarla.</p></div>
 {callout('**No cuesta dinero:** todo corre en tu Codespace y en los minutos de GitHub Actions. En L5 se enlaza lo de Google Cloud (presupuesto y borrado) de S4.', 'margin-top:12px')}
</div>''',
          f'Presentación para el alumno del laboratorio de MLOps clásico de la sesión 5. Todas las salidas del terminal son reales, ejecutadas el {FECHA} sobre una copia de ensayo del proyecto con la muestra de 150 clientes. Las capturas de GitHub Actions están pendientes: se hacen cuando el profesor lance los dos ensayos. Insista desde el principio en el mensaje: un modelo en producción se vigila, se versiona y se puede deshacer.')

    slide('A', 4, 'El plan', 'cinco laboratorios', 'Cinco laboratorios para un modelo que ya está en producción', f'''
<div class="card">''' + tabla(['#', 'Laboratorio', 'Qué haces', 'Qué te llevas'], [
        ['**L1**', 'Deriva de datos', '`deriva cortes` y `deriva datos`: PSI y KS de las 13 variables', 'El modelo **no avisa solo** de que los datos han cambiado'],
        ['**L2**', 'Deriva de rendimiento', '`deriva rendimiento`: el AUC por corte', 'Se mide **tarde**, y **medir con datos de entrenamiento engaña**'],
        ['**L3**', 'Versionar y volver atrás', '`alias_modelo`: una v2 distinta, `promover` y `volver`', 'Un alias es un **puntero**: deshacer es moverlo'],
        ['**L4**', 'Alertas con GitHub Actions', 'El workflow `monitoreo.yml` y dos ramas de ensayo', 'La alerta **es el rojo** y un issue'],
        ['**L5**', 'Costes y orden', 'Lo de S4: presupuesto y borrado', 'Avisar no es cortar; lo que creas, lo borras']]) + '''</div>
<div class="grid3" style="margin-top:12px">
 ''' + card('Dónde', ['**Codespace** (terminal bash) para L1 a L3, desde `04-Proyecto-Base`.', '**Terminal en la raíz** y la web de **GitHub** (pestañas Actions e Issues) para L4.']) + card('Orden', ['**L1 y L2 antes que L3:** L3 cambia los datos a los completos y los números de L1 y L2 dejan de ser los de la muestra.', 'Al final de L3 se explica cómo volver a la muestra.']) + card('Sin claves', ['Ningún secreto: el workflow usa solo el `GITHUB_TOKEN` de cada run.', 'Ni Google Cloud ni LLM.']) + '''
</div>''',
          'Mapa de los cinco laboratorios. L1 y L2 miden, L3 versiona y deshace, L4 automatiza el aviso y L5 recuerda los costes de S4 sin repetirlos. El orden importa por una razón práctica: L3 entrena una versión 2 con los datos completos del Excel y eso cambia la base analítica local, así que L1 y L2 se hacen antes. Todo lo que se enseña se ejecutó de verdad en una copia de ensayo; lo de GitHub Actions lo ensaya el profesor.')

    slide('A', 4, 'Siglas y palabras', 'vocabulario', 'Las palabras que vamos a usar', '<div class="card">' + tabla(['Palabra', 'Qué significa aquí'], [
        ['**Corte**', 'Una fecha para la que se calculan las 13 variables de cada cliente («la foto de ese día»). El **«ahora»** es el día siguiente a la última factura: 2011-12-10'],
        ['**Deriva de datos**', 'Los clientes de hoy ya no se parecen a los de entrenamiento. Se mide **sin etiqueta**, solo con los datos'],
        ['**Deriva de rendimiento**', 'El modelo acierta menos que antes (el **AUC** cae). Necesita la **etiqueta**, que llega 90 días tarde'],
        ['**PSI**', '*Population Stability Index*: cuánto cambia el reparto de una variable. Menos de 0,10 «estable», de 0,10 a 0,25 «moderado», más de 0,25 «cambio importante»: una **convención del oficio, no una ley**'],
        ['**KS**', 'Estadístico de Kolmogórov y Smirnov: distancia máxima entre dos distribuciones (0 = iguales, 1 = totalmente separadas)'],
        ['**Alias** `champion`', 'Un puntero con nombre a una **versión** del modelo en MLflow: «la que manda». Cambiar de modelo es mover el puntero'],
        ['**Issue**', 'Una incidencia abierta en el repositorio de GitHub (pestaña **Issues**): aquí, el aviso de la alerta'],
        ['**schedule**', 'El disparador de GitHub Actions que lanza un workflow a una hora fija (cron). En un *fork* viene **desactivado**']]) + '</div>',
          'Diapositiva de vocabulario. Insista en dos ideas: el umbral de PSI es una convención del oficio, no una ley, y se puede cambiar con una opción; y la deriva de datos avisa pronto pero puede dar falsas alarmas, mientras que la de rendimiento es la verdad pero llega tarde. Se miran las dos. Después de esta diapositiva todo es práctico.')

    slide('A', 8, 'Preparar el entorno', 'paso 0 · Codespace', 'Deja la base de datos y el modelo listos (una vez)', f'''
<div class="split" style="grid-template-columns:1.05fr .95fr">
 <div class="col">''' + term('Codespace · terminal bash · una orden cada vez', [
        '# 1) entra en la carpeta del proyecto', O['cd'],
        '# 2) las dependencias (si tu Codespace ya las trae, no hace nada)', O['pip'],
        '# 3) la base operacional (la fuente) y el pipeline que entrena el modelo', O['operacional'], O['pipeline']]) + '''
  ''' + callout('El pipeline **registra la versión 1** de `retencion-90d` en MLflow. Con un Codespace nuevo verás «versión 1»; si ya habías ejecutado el pipeline con `--forzar`, tendrás más versiones: usa **tus** números.') + '''
 </div>
 <div class="col">
  ''' + mira([
        '`OPERACIONAL: clientes 150 filas` … `lineas_factura 23,070 filas`.',
        'Los cuatro pipelines con su tiempo y, al final, `regresion_logistica   AUC valid 0.698 | test 0.747`.',
        '`Registrado en MLflow como «retencion-90d», version 1.` (~30 s en un portátil).']) + si_falla([
        '`No module named ia_mlops`: no estás en `04-Proyecto-Base` (`pwd`).',
        '`0xc06d007f` al importar `scikit-learn` en Windows con conda: falta `<entorno>\\Library\\bin` en el `PATH`; activa el entorno con `conda activate`.']) + f'''
  <p class="small">{md(NOTA_WINDOWS)}</p>
 </div>
</div>''',
          'Preparación. Las dos primeras órdenes dejan la base operacional y el pipeline entrena el modelo y registra la versión uno en MLflow. En el ensayo tardó unos treinta segundos. Las salidas de esta presentación vienen de un portátil con Windows; en un Codespace con Linux no se han comprobado: los números deberían coincidir, pero está sin verificar. La línea de la ruta del almacén de MLflow será la del alumno.')

    # ------------------------------------------------------------------ B · L1
    slide('B', 5, 'La deriva de datos', 'qué es y por qué no avisa sola', 'El modelo sigue funcionando… pero ya no ve a los clientes con los que aprendió', '''
<div class="grid2">
 ''' + card('Qué pasa', [
        'Un modelo **no se rompe**: sigue devolviendo una probabilidad para cualquier entrada. **No avisa** de que sus entradas ya no se parecen a las del entrenamiento.',
        'Los clientes de hoy compran menos veces al trimestre, o hace más tiempo que no compran: el modelo **extrapola**.',
        'Por eso alguien tiene que **medirlo**: comparar los datos de hoy con los de referencia.']) + card('Cómo se mide', [
        'Se elige un **corte de referencia** (el último de entrenamiento) y un **corte actual**.',
        'Para cada una de las 13 variables: **PSI** (cuánto cambia el reparto) y **KS** (distancia entre distribuciones).',
        'No hace falta la etiqueta: se puede hacer **hoy**, sin esperar 90 días.']) + '''
</div>
''' + callout('**Lo que avisa pronto puede dar falsas alarmas** (los datos cambian y el modelo sigue bien). **Lo que dice la verdad llega tarde** (L2). Se miran las dos.', 'margin-top:12px') + '''
<div class="grid3" style="margin-top:12px">
 ''' + card('Datos de hoy', ['Se calculan al vuelo con el **mismo SQL** de la capa FS que usó el entrenamiento: así la comparación es justa.']) + card('Pocos clientes', ['Con 109 y 148 clientes el PSI **oscila por azar**: es un aviso, no una sentencia.']) + card('Solo lectura', ['`deriva` no escribe nada en la base ni en el registro: lo puedes lanzar sin miedo.']) + '''
</div>''',
          'Primera idea del laboratorio: el modelo no avisa de que los datos han cambiado, porque siempre devuelve una probabilidad. Hay que medirlo comparando un corte de referencia con otro actual, variable a variable, con PSI y KS. Esto no necesita la etiqueta, por eso se puede hacer cada día. Advierta que con pocos clientes el PSI oscila por azar y que el comando solo lee, no cambia nada.')

    slide('B', 5, 'Los cortes guardados', 'paso 1 · cortes', 'Primero, qué fechas hay: `deriva cortes`', f'''
''' + dos_columnas(term('Codespace · desde 04-Proyecto-Base', [O['cortes']]) + mira([
        'Diez cortes guardados, de **69** a **131** clientes por corte.',
        'Los siete primeros son de **entrenamiento** (`train`), 2011-03-01 es de **validación** y los dos últimos de **prueba** (`test`).',
        'El «ahora» de los datos es **2011-12-10**. Se puede pedir cualquier fecha: se calcula al vuelo.']) + si_falla([
        'Sale 2 y un mensaje de error: falta ejecutar el pipeline (paso 0).']), salida('Qué debes ver · salida 0', S_CORTES), '.8fr 1.2fr'),
          'Los cortes guardados salen de la tabla fs_cliente_corte. Fíjese en la columna partición: los cortes de entrenamiento, el de validación y los de prueba. Esa columna será importante en L2, cuando midamos el rendimiento. El ahora es el día siguiente a la última factura. Cualquier otra fecha se puede pedir y se calcula al vuelo.')

    slide('B', 6, 'Deriva de datos con datos reales', 'paso 2 · datos', 'La orden: `deriva datos` entre el último corte de entrenamiento y el «ahora»', f'''
''' + dos_columnas(term('Codespace · desde 04-Proyecto-Base', [O['datos'], O['salida']]) + mira([
        '**Salida 1**: hay deriva (salida 0 = sin deriva, 2 = error). Un workflow puede decidir con ese número.',
        '**5 de 13** variables superan 0,25; las mayores: `antiguedad_dias` (PSI **2,830**, KS 0,736) y `recencia_dias` (0,437).',
        'Las más bajas: `es_reino_unido` 0,000, `ticket_medio` 0,012 y `devoluciones` 0,018.']) + callout('**Lectura honesta:** `antiguedad_dias` crece para todos con solo **dejar pasar un año**: su PSI enorme es esperable y no pide por sí solo reentrenar. Las de actividad reciente (`recencia_dias`, `frecuencia_90d`, `frecuencia_180d`, `monto_90d`) sí dicen que el comportamiento cambió.'), salida('Qué debes ver', S_DATOS), '.8fr 1.2fr'),
          'Esta es la orden central de L1. La salida real: cinco de trece variables superan el umbral de 0,25. La más grande, la antigüedad, es esperable: todos los clientes envejecen un año. Las que realmente importan son las de actividad reciente. Esto es lo que hay que enseñar a leer: no toda deriva pide reentrenar. El número de salida, uno, es lo que usará el workflow para decidir.')

    slide('B', 5, 'Cómo leer PSI y KS', 'el cálculo con cuatro clientes', 'El PSI con un ejemplo que cabe en la mano', f'''
<div class="grid2" style="grid-template-columns:1.05fr .95fr">
 <div class="col">
  <div class="card"><h3><span class="mono">PSI = suma de (q − p) · ln(q / p)</span></h3><p class="small">Con <b>p</b> = fracción de clientes de la referencia en cada intervalo y <b>q</b> = la del corte actual. Los intervalos salen de los <b>cuantiles de la referencia</b>.</p>''' + tabla(['intervalo', 'referencia (p)', 'actual (q)', 'aporte'], [
        ['hasta 2,5', '0,50', '0,75', '0,1014'], ['más de 2,5', '0,50', '0,25', '0,1733'], ['nulo', '0,0001', '0,0001', '0,0000'], ['**PSI**', '', '', '**0,2747**']]) + '''</div>
  ''' + term('Codespace · desde 04-Proyecto-Base', ['# la referencia es [1, 2, 3, 4] y el corte actual [1, 1, 1, 4]', O['psi_ejemplo']]) + '''
  <p class="small">Qué debes ver: <b>0.2747</b>. Con la misma muestra en los dos lados, el PSI es exactamente <b>0</b>.</p>
 </div>
 <div class="col">
  ''' + card('Las tres franjas (una convención)', ['Menos de **0,10**: estable.', 'De **0,10 a 0,25**: moderado.', 'Más de **0,25**: cambio importante.', 'Es la regla del oficio, **no una ley**: por eso `--umbral-psi` la deja cambiar.']) + card('El suelo anti-cero', ['`ln(q / p)` no existe si un intervalo está vacío: las fracciones menores que **0,0001** se suben a 0,0001. Es un parche numérico, no una teoría.']) + card('El KS', ['Mira la distancia máxima entre las dos distribuciones **acumuladas**: 0 iguales, 1 separadas del todo. Es un segundo punto de vista sobre lo mismo.']) + '''
 </div>
</div>''',
          'El ejemplo pequeño de la documentación del proyecto: cuatro clientes y dos intervalos. La mediana de la referencia, dos coma cinco, separa los intervalos; el PSI da cero coma dos siete cuatro siete. Los umbrales de cero coma diez y cero coma veinticinco son una convención del oficio. El suelo de cero coma cero cero cero uno evita el logaritmo de cero. Con pocos clientes, el PSI oscila por azar.')

    slide('B', 6, 'Ejercicio de deriva de datos', 'ejercicio · otro par y otro umbral', 'Ahora tú: otro par de cortes y otro umbral', f'''
''' + dos_columnas(term('Codespace · desde 04-Proyecto-Base', [
        '# 1) dos cortes de entrenamiento consecutivos', O['par'], O['salida'],
        '# 2) la misma pareja, con otro umbral de alarma', O['par_umbral'], O['salida'],
        '# 3) y el resultado en JSON (lo que lee un workflow)', O['datos_json'], O['leer_json']]) + mira([
        'Con el umbral por defecto la pareja agosto→septiembre de 2010 **también da salida 1**: `antiguedad_dias` llega a **0,410**.',
        'Con `--umbral-psi 0.5` la **misma medición** da salida **0**: la variable pasa a «moderada». Cambió la convención, no los datos.',
        'En esta muestra **ninguna pareja de cortes da salida 0** con el umbral 0,25 (se probaron las 45): siempre hay alguna variable, casi siempre `antiguedad_dias`, que supera 0,25.',
        "El JSON dice `True ['antiguedad_dias', 'recencia_dias', 'frecuencia_180d', 'monto_90d', 'frecuencia_90d']`."]), salida('Qué debes ver (recortado)', S_PAR + '\n\n--umbral-psi 0.5:\n' + S_PAR_UMBRAL), '.95fr 1.05fr', mira_a_la_derecha=True),
          'Ejercicio. Primero un par distinto: agosto y septiembre de dos mil diez. Con el umbral por defecto da salida uno por la antigüedad, que vale cero coma cuatro uno cero. Con el umbral en cero coma cinco la misma medición da cero. Es una decisión de convención, no de datos. Conviene decir con honestidad que en esta muestra de ciento cincuenta clientes ninguna de las cuarenta y cinco parejas de cortes da cero con el umbral de cero coma veinticinco. Esa pareja y ese umbral son los del escenario estable del workflow.')

    # ------------------------------------------------------------------ C · L2
    slide('C', 4, 'Por qué se mide tarde', 'la etiqueta llega 90 días después', 'La deriva de rendimiento es la verdad… que llega 90 días tarde', f'''
<div class="grid2">
 ''' + card('Qué se predice', ['La probabilidad de que el cliente **vuelva a comprar en los próximos 90 días**.', 'La **etiqueta** («¿compró?») solo se conoce **cuando pasan esos 90 días**.', 'El corte 2011-12-10 aparece como «sin etiqueta»: el corte + 90 días se sale de los datos.']) + card('Qué se mide', ['El **AUC** del modelo en producción en cada corte con etiqueta: cómo ordena a los que compran por delante de los que no.', 'Se compara con el **primer corte medido**: la **caída** de AUC.', 'La **tolerancia** por defecto (0,05) es **provisional**: no sale de ninguna medición.']) + '''
</div>
<div class="card" style="margin-top:12px"><h3>Línea de tiempo (un corte cualquiera)</h3>''' + tabla(['Día 0 (corte)', 'Día 0 a 90', 'Día 90'], [
        ['Se calculan las 13 variables y se **puntúa**', 'Nadie sabe todavía quién comprará: **solo** se puede mirar la deriva de datos (L1)', 'Llega la etiqueta: ya se puede calcular el **AUC** de ese corte']]) + '''</div>
''' + callout('Por eso se **miran las dos**: la de datos avisa **pronto** (pero puede ser falsa alarma) y la de rendimiento confirma **tarde**.', 'margin-top:12px'),
          'Segunda idea: la deriva de rendimiento es la verdad, pero necesita la etiqueta, y en nuestro caso la etiqueta llega noventa días después del corte. Mientras tanto solo podemos mirar la deriva de datos. La tolerancia de cero coma cero cinco es provisional: no sale de ninguna medición. Es una decisión que debe tomar el negocio.')

    slide('C', 5, 'Rendimiento por corte', 'paso 3 · rendimiento', 'La orden: `deriva rendimiento` con los cortes de validación y de prueba', f'''
''' + dos_columnas(term('Codespace · desde 04-Proyecto-Base', [O['rend'], O['salida']]) + mira([
        '**Salida 0**: la caída máxima no supera la tolerancia (0,05).',
        'AUC **0,6982** (validación, 114 clientes), **0,7534** (prueba, 119) y **0,7423** (prueba, 131).',
        'Caída **negativa** = el AUC **mejora** frente al primer corte; la orden no se alarma.',
        'El AVISO dice que 2011-03-01 es de validación: ahí el AUC **sobreestima**.']) + si_falla([
        'Sale 2 y un mensaje de error: falta el modelo; ejecuta `python -m ia_mlops.pipeline` (paso 0).']), salida('Qué debes ver', S_REND), '.8fr 1.2fr'),
          'La orden de rendimiento calcula el AUC del modelo en producción para cada corte con etiqueta. En el ensayo da cero coma seis nueve ocho dos en validación, cero coma siete cinco tres cuatro y cero coma siete cuatro dos tres en prueba. La salida es cero. Fíjese en el aviso: el primer corte medido es de validación y por tanto sobreestima.')

    slide('C', 5, 'La lección del corte de entrenamiento', 'medir con datos de entrenamiento engaña', 'Si el primer corte es de entrenamiento, el modelo parece haber «caído» sin haber cambiado', f'''
''' + dos_columnas(term('Codespace · desde 04-Proyecto-Base', ['# el mismo modelo, pero empezando por un corte de ENTRENAMIENTO', O['rend_ent'], O['salida']]) + mira([
        '**Salida 1** y «DERIVA DE RENDIMIENTO: sí»: la caída máxima es **0,1515**, mayor que 0,05.',
        'El AUC en entrenamiento (2010-12-01) es **0,8497**; en validación, **0,6982**: **el modelo no ha cambiado**, solo lo medimos con datos que ya había visto.',
        'La orden **avisa**: parte de la caída es **sobreajuste** y no deriva.']) + callout('**La lección importante:** medir el rendimiento con datos de entrenamiento **engaña**. Para una medida honesta, usa cortes de **prueba** o posteriores al entrenamiento.'), salida('Qué debes ver (recortado)', S_REND_ENT), '.8fr 1.2fr'),
          'Esta es la lección importante de la práctica. Si empezamos por un corte de entrenamiento, el AUC vale cero coma ocho cuatro nueve siete, y el de validación cero coma seis nueve ocho dos: la caída es de cero coma uno cinco uno cinco y la orden sale con uno. Pero el modelo no ha cambiado: solo estamos midiendo con datos que ya vio. La propia orden lo avisa. Medir en datos de entrenamiento engaña.')

    # ------------------------------------------------------------------ D · L3
    slide('D', 5, 'Un alias es un puntero', 'paso 1 · mostrar, promover y cargar', 'Un alias es un puntero a una versión: nada se copia ni se borra', f'''
''' + dos_columnas(term('Codespace · desde 04-Proyecto-Base', [O['mostrar'], O['promover1'], O['cargar']]) + mira([
        '`mostrar`: **una** versión (v1) y «Alias: ninguno».',
        '`promover --version 1`: `@champion -> v1` y el aviso de que **no había anterior**.',
        '`cargar`: carga `models:/retencion-90d@champion` y puntúa al cliente de ejemplo: **0.8279**.']) + si_falla([
        'Si te salen más versiones que en la pantalla, usa **tus** números (`mostrar` te dice cuáles hay).',
        '«No existe la versión 9 de «retencion-90d»…»: pediste una que no está; mira `mostrar`.']), salida('Qué debes ver (la línea «Almacén de MLflow: …» será tu ruta)', S_MOSTRAR1 + '\n\n' + S_PROMOVER1 + '\n\n' + S_CARGAR1), '.85fr 1.15fr'),
          'Primer paso de L3. El registro de MLflow tiene una versión del modelo de retención. Promover la versión uno pone el alias champion en ella. Cargar por alias carga lo que apunta champion y puntúa al cliente de ejemplo: cero coma ocho dos siete nueve. Con tres versiones idénticas el cambio de alias no se nota en la probabilidad, por eso en el siguiente paso entrenamos una versión distinta.')

    slide('D', 8, 'Una v2 distinta', 'paso 2 · datos completos', 'Entrena una v2 que sea de verdad otra: los datos completos del Excel', f'''
''' + dos_columnas(term('Codespace · desde 04-Proyecto-Base', [
        '# 1) baja el Excel completo de UCI y comprueba su huella sha256 (unos 45 MB)', O['descargar'],
        '# 2) rehace la base con 1,07 millones de filas, reentrena y registra la v2', O['pipe_completo']]) + callout('**Paciencia:** el segundo comando tardó **437 s** (algo más de 7 minutos) en el portátil del ensayo. En un Codespace: **sin verificar**. Después de esto, tus cortes y tu modelo local **ya no son los de la muestra** (al final de L3 se explica cómo volver).') + mira([
        '`descargar`: «sha256: 572e3627…» y «Listo: …/online_retail_II.xlsx».',
        'El pipeline: clientes **5,942**, líneas **1,067,371**, `regresion_logistica   AUC valid 0.786 | test 0.796` y «version 2».',
        'La v2 tiene otra huella de datos (**3521a0421905ba28**) que la v1 (**35a94deb4e04ab4a**).']), salida('Qué debes ver (recortado)', S_PIPE_COMPLETO + '\n\n' + S_MOSTRAR2), '.9fr 1.1fr'),
          'Para que el cambio de alias se note hay que tener dos versiones distintas. La segunda se entrena con los datos completos del Excel de Online Retail II, que no está en el repositorio: se baja con el comando descargar, que verifica la huella. El pipeline completo tardó cuatrocientos treinta y siete segundos en el portátil del ensayo, más de siete minutos; en un Codespace no se ha medido. La versión dos tiene AUC de test cero coma siete nueve cinco seis frente a cero coma siete cuatro siete uno de la uno.')

    slide('D', 5, 'Mover el puntero', 'paso 3 · promover 2 y cargar', 'Promover la v2: mismo comando, otro modelo', f'''
''' + dos_columnas(term('Codespace · desde 04-Proyecto-Base', [O['promover2'], O['cargar']]) + mira([
        '`promover`: «@champion: v1 -> v2. La v2 recuerda a la v1» y **«No se ha borrado nada»**.',
        '`cargar` ahora carga la **versión 2** y la probabilidad del cliente de ejemplo es **0.7245**.',
        'Antes (v1) era **0.8279**: el alias decide qué modelo se sirve, y ahora **se nota**.']) + callout('`promover` guarda en la v2 una etiqueta **`champion_anterior = 1`**: es lo que luego lee `volver`.'), salida('Qué debes ver', S_PROMOVER2 + '\n\n' + S_CARGAR2), '.85fr 1.15fr'),
          'Promover la versión dos mueve el puntero y deja anotado en la versión dos cuál era la anterior, con la etiqueta champion_anterior. Al cargar por alias ahora se carga la versión dos y la probabilidad del cliente de ejemplo es cero coma siete dos cuatro cinco, frente a cero coma ocho dos siete nueve de la versión uno. El mismo comando, otro modelo.')

    slide('D', 5, 'Volver atrás', 'paso 4 · rollback', 'Deshacer es mover el puntero: `volver`', f'''
''' + dos_columnas(term('Codespace · desde 04-Proyecto-Base', [O['volver'], O['cargar'], O['mostrar']]) + mira([
        '`volver`: «Rollback: @champion: v2 -> v1. La v2 **sigue registrada**».',
        '`cargar` otra vez da **0.8279** y **versión 1**: el mismo modelo de antes.',
        '`mostrar` enseña **las dos versiones** y la v2 con «(champion anterior: v1)».']) + si_falla([
        'Si repites `volver`: «La versión 1, que es @champion, no guardó una versión anterior: no hay a dónde volver» (salida **2**). Para ir a otra, `promover --version N`.']), salida('Qué debes ver', S_VOLVER + '\n\n(cargar)\nCargado models:/retencion-90d@champion -> versión 1\nProbabilidad de comprar en 90 días del cliente de cliente_ejemplo.json: 0.8279\n\n(mostrar)\n' + '''Modelo registrado «retencion-90d»: 2 versiones
  v1   alias: @champion    valid_auc 0.6982 · test_auc 0.7471
  v2   alias: -            valid_auc 0.7855 · test_auc 0.7956  (champion anterior: v1)
Alias: @champion -> v1

(volver otra vez)
''' + S_VOLVER_SIN), '.85fr 1.15fr'),
          'El rollback es mover el puntero hacia atrás. Después de volver, el alias apunta de nuevo a la versión uno y la probabilidad vuelve a ser cero coma ocho dos siete nueve. La versión dos sigue registrada, con sus métricas y su modelo: no se ha borrado nada. Si se repite volver y no hay versión anterior, falla con un mensaje claro y salida dos.')

    slide('D', 5, 'Lo que el alias gobierna', 'limitación honesta', 'Mover el alias no cambia la API que ya está desplegada', f'''
<div class="grid2">
 ''' + card('Qué gobierna el alias', ['El **registro** de MLflow y **cualquiera que cargue** `models:/retencion-90d@champion`.', '`cargar` y las pruebas de este laboratorio.']) + card('Qué NO gobierna', ['La **imagen Docker de la API** copia `models/modelo_mlflow` al construirse y **no lee el registro**.', 'Mover `champion` **no cambia** lo que responde la API ya desplegada.']) + '''
</div>
<div class="card" style="margin-top:12px"><h3>Cómo se uniría en un sistema real (tres líneas; aquí no se implementa)</h3><ol class="ol sm">
 <li>Al mover el alias, un paso del workflow <b>exporta la versión champion</b> a <span class="mono">models/modelo_mlflow</span>.</li>
 <li>Construye y publica la imagen con <b>la versión en su etiqueta</b>.</li>
 <li>La despliega (o hace que la API <b>cargue por alias al arrancar</b>).</li></ol></div>
<div class="grid2" style="margin-top:12px">
 ''' + card('Volver a la muestra (si quieres repetir L1 y L2)', ['Tras L3 la base local es la completa. Bórrala y rehaz la de la muestra: **en este orden**.', 'Registrará una **v3** (igual que la v1) y **el alias no se mueve**.']) + term('Codespace · desde 04-Proyecto-Base', [O['borrar_db'], O['pipe_muestra']]) + '''
</div>''' + callout('**Sin verificar:** repetirlo en un Codespace. Si lanzas `--fuente muestra` **sin** borrar antes `curso.db`, falla con «R03_integridad_referencial: Violaciones de claves foráneas» (visto en el ensayo).', 'margin-top:10px'),
          'Honestidad sobre el alcance del alias: gobierna el registro y a quien cargue por alias, no la imagen Docker de la API, que copia el modelo al construirse. Un sistema real lo uniría exportando la versión champion, construyendo y publicando la imagen con la versión en su etiqueta y desplegándola. Aquí no se implementa. A la derecha, cómo volver a los datos de la muestra: hay que borrar la base analítica antes, porque si no el pipeline falla por integridad referencial; es un comportamiento del proyecto que se anota en el informe.')

    # ------------------------------------------------------------------ E · L4
    slide('E', 5, 'El workflow de monitoreo', 'qué hace monitoreo.yml', 'El mismo `deriva`, pero cada día y sin que nadie mire', f'''
<div class="grid3">
 ''' + card('1 · Datos y modelo', ['Reconstruye la **base operacional** y entrena el modelo desde la muestra (`operacional` + `pipeline`), como `puntuar-lote.yml` de S4.', 'Sube **models/** y **curso.db** como artefacto.']) + card('2 · Deriva', ['**Elige el escenario** (por la rama, por las entradas o por defecto).', 'Lanza `deriva datos` y `deriva rendimiento` con `--json`.', 'Escribe el **resumen** con la tabla de PSI y sube los JSON.']) + card('3 · Alerta', ['Solo si algún código de salida fue **1**.', '**Abre un issue** (o comenta el que ya hay) con la etiqueta `alerta-deriva` y **termina el run en ROJO**.']) + '''
</div>
<div class="card" style="margin-top:10px">''' + tabla(['Disparador', 'Cuándo', 'Qué mide'], [
        ['`schedule`', 'cada día a las **05:23 UTC** (un minuto «raro»: a las horas en punto GitHub va cargado)', 'referencia 2010-12-01 frente al «ahora». En un *fork* viene **desactivado**'],
        ['`workflow_dispatch`', 'a mano, con `referencia`, `actual` y `umbral_psi`', 'lo que escribas'],
        ['`push` a `lab/monitoreo/**`', 'el **nombre de la rama** elige el escenario', f'`{RAMA_ESTABLE}` y `{RAMA_DERIVA}`']]) + '''</div>
<div class="grid3" style="margin-top:10px">
 ''' + card('Permisos mínimos', ['`contents: read` en todo; **`issues: write` solo** en el trabajo de alerta.']) + card('Sin secretos', ['Solo el `GITHUB_TOKEN` de cada run.']) + card('Un detalle', ['El trabajo de alerta **no hace checkout**: lleva `working-directory: .` (lección real de S4).']) + '''
</div>''',
          'El workflow tiene tres trabajos: preparar datos y modelo, medir la deriva de datos y la de rendimiento, y la alerta, que solo se ejecuta si algún código de salida fue uno. La alerta abre un issue con la etiqueta alerta-deriva, o comenta el que ya hay, y termina el run en rojo. El nombre de la rama elige el escenario, igual que en S4. El schedule diario no corre en un fork salvo que se active; como los datos están congelados siempre daría alerta, así que hay que desactivarlo al terminar.')

    slide('E', 6, 'Copiar y subir el workflow', 'paso 1 · en la raíz del repositorio', 'Copia `monitoreo.yml` a `.github/workflows` en una rama base', f'''
''' + dos_columnas(term('Codespace · terminal bash · RAÍZ del repositorio', [
        '# sal de 04-Proyecto-Base (si estás dentro)', O['cd_raiz'],
        O['switch_develop'], O['pull'], O['rama'], O['mkdir'], O['cp'], O['add'], O['commit'], O['push']]) + callout('Este push **no lanza el workflow**: `lab/mlops-s5` no es una rama de ensayo. **`Run workflow` solo aparece si el archivo está en la rama por defecto**; por eso los ensayos usan ramas.'), mira([
        'En la pestaña **Actions** de tu *fork*, a la izquierda, **«Monitoreo del modelo»**. Si es un *fork*, acepta antes el aviso para **activar las Actions**.',
        'Configuración del repositorio: lo mismo que en S4 (`CONFIGURAR-REPOSITORIO.md`). Aquí **no** hace falta el *environment* `produccion`: no hay despliegue.']) + si_falla([
        '`git push` da 403: el gestor de credenciales tiene otra cuenta (`git-credential-manager github login`).',
        'No aparece el workflow: comprueba que el archivo está en `.github/workflows/` de la rama y que activaste las Actions.']), '1.05fr .95fr'),
          'Se copia el workflow a la carpeta de workflows en una rama base. El push a la rama base no lanza nada porque no coincide con el patrón de las ramas de ensayo. Las ramas de ensayo se crean después a partir de esta. Recuerde que aquí no hace falta el environment de producción de S4 porque este workflow no despliega nada, solo mide y avisa. Las órdenes de git se ejecutan en la raíz del repositorio, no en cero cuatro guion proyecto base.')

    slide('E', 6, 'Escenario estable', 'ensayo 1 · rama lab/monitoreo/estable', 'Primer ensayo: nada que avisar, el run termina en verde', f'''
''' + dos_columnas(term('Terminal bash · raíz del repositorio', [O['volver_base'], O['estable_rama'], O['estable_push']]) + mira([
        '**Qué verás** (ensayado en Actions el 26/11): los trabajos 1 y 2 en **verde** y el 3 **omitido**.',
        'Mide la pareja **2010-08-01 → 2010-09-01** con umbral **0,50**: `antiguedad_dias` 0,410 queda «moderada» y la salida es **0** (comprobado en local).',
        'El resumen dice **«Sin alerta»** y el AUC por corte: 0.6982, 0.7534 y 0.7423.',
        '**No se abre ningún issue.**']) + callout('**Honestidad:** «estable» **no** es «sin cambios»: es un par de cortes cercano **y un umbral más laxo**. Con 0,25 también habría alertado (L1).'), cap('m-01-estable-verde.webp', 160) + cap('m-02-resumen-estable.webp', 160), '.85fr 1.15fr'),
          'Primer ensayo: la rama estable. El nombre de la rama elige el escenario: referencia agosto de dos mil diez, actual septiembre, umbral cero coma cinco. Con ese umbral la salida es cero y el workflow acaba en verde, con el trabajo de alerta omitido. Las capturas están pendientes: las hará el profesor al lanzar el ensayo. Lo que sí está comprobado es el código de salida de la orden, ejecutada en local sobre los mismos datos.')

    slide('E', 6, 'Escenario deriva: el rojo', 'ensayo 2 · rama lab/monitoreo/deriva', 'Segundo ensayo: la deriva real, y el run en rojo', f'''
''' + dos_columnas(term('Terminal bash · raíz del repositorio', [O['volver_base'], O['deriva_rama'], O['deriva_push']]) + mira([
        '**Qué verás** (ensayado en Actions el 26/11): los trabajos 1 y 2 en **verde** y el **3 · Alerta en ROJO**.',
        'Mide **2010-12-01 frente a 2011-12-10** con umbral **0,25**: la misma medición de L1, **salida 1**, **5 de 13** variables.',
        'El resumen dice **«ALERTA»** y marca las cinco variables con **supera el umbral**.',
        '**La alerta es el rojo**: sin él, nadie se entera de que ha pasado algo.']) + si_falla([
        '«Rama de ensayo desconocida»: el nombre no es `…/estable` ni `…/deriva`; el workflow lo rechaza a propósito.']), cap('m-03-deriva-rojo.webp', 160) + cap('m-04-resumen-deriva.webp', 160), '.85fr 1.15fr'),
          'Segundo ensayo: la rama deriva. Mide la misma pareja que L1, el último corte de entrenamiento frente al ahora de los datos, con el umbral por defecto. La salida es uno, cinco de trece variables, y el workflow termina en rojo a propósito. El rojo es la alerta: si el workflow acabara en verde, nadie se enteraría. Las capturas están pendientes.')

    slide('E', 5, 'El issue de alerta', 'qué abre el workflow', 'El aviso de verdad: un issue con las variables y el enlace al run', f'''
''' + dos_columnas(mira([
        'En la pestaña **Issues** hay **uno nuevo**, con la etiqueta **`alerta-deriva`** (se crea sola si no existe).',
        'Título: **«Alerta de deriva: 5 variables superan el PSI 0.25 (referencia 2010-12-01, actual 2011-12-10)»**.',
        'Cuerpo: la tabla de las **cinco variables** que superan el umbral con su PSI y su KS, el **enlace al run** y qué hacer.']) + callout('**Qué hacer con la alerta:** abre el run, lee el resumen y decide si la deriva es **esperable** (`antiguedad_dias`) o **de comportamiento** (`recencia_dias`, `frecuencia_90d`…). Si el AUC de cortes de **prueba** cae, reentrena y promueve la versión nueva con alias (L3); si sale mal, `volver`.') + '''
  <p class="small"><b>Verificado en Actions (26/11):</b> <span class="mono">gh issue create</span> funciona con solo <span class="mono">issues: write</span>, y un segundo run comenta en el mismo issue.</p>''', cap('m-05-issue-alerta.webp', 330), '.9fr 1.1fr'),
          'El aviso de verdad es el issue. El workflow lo abre con el título y la tabla de variables, y pone la etiqueta alerta-deriva, que crea si no existe. El trabajo de alerta es el único con permiso de escritura, y solo sobre issues. Esto se ensayó de verdad en Actions el veintiséis de noviembre y funcionó con solo ese permiso.')

    slide('E', 6, 'Otra alerta, ningún issue nuevo', 'repetir y limpiar', 'Si repites el run, no se abre un segundo issue', f'''
''' + dos_columnas(mira([
        'En la página del run, **Re-run all jobs**: vuelve a medir y a dar rojo.',
        '**Qué verás** (ensayado en Actions el 26/11): el trabajo 3 **comenta** en el issue que ya está abierto («Nueva medición con deriva») y **no abre otro**.',
        'Así una deriva que sigue ahí no llena la lista de issues: **una alerta abierta** hasta que alguien la cierre.']) + si_falla([
        '`gh: Resource not accessible by integration`: faltan permisos de escritura de issues; en *Settings › Actions › General*, comprueba que el workflow puede escribir.',
        'El issue no se crea: mira el paso «Abrir el issue» del trabajo 3.']) + card('Al terminar, limpia', ['**Cierra** el issue (botón *Close issue*).', 'Borra las dos ramas de ensayo (órdenes de abajo).', '**Desactiva el workflow** en Actions («···» › *Disable workflow*): con datos congelados, el schedule diario avisaría **siempre**.']) + term('Terminal bash · raíz del repositorio', [O['borrar_rama_estable'], O['borrar_rama_deriva']]), cap('m-06-segunda-alerta.webp', 330), '.9fr 1.1fr'),
          'Si se repite el run, el trabajo de alerta busca primero si hay un issue abierto con la etiqueta alerta-deriva. Si lo hay, añade un comentario en lugar de abrir otro. Al terminar el laboratorio conviene cerrar el issue, borrar las dos ramas y desactivar el workflow, porque con los datos congelados el schedule diario daría alerta todos los días. El mensaje de error de permisos es una conjetura habitual y no se ha provocado.')

    # ------------------------------------------------------------------ F · L5
    slide('F', 4, 'Costes y orden', 'sin repetir S4', 'Este laboratorio no usa la nube de pago; lo de S4 sigue valiendo', f'''
<div class="grid2">
 <div class="card"><h3>Lo de este laboratorio</h3>''' + lista([
        'L1 a L3: tu **Codespace** (lo que ya tengas incluido en tu cuenta de GitHub).',
        'L4: **minutos de GitHub Actions** (gratis en repositorios públicos; en uno privado cuentan contra tu cuota). Minutos exactos del workflow: **sin dato** hasta el ensayo del profesor.',
        'Lo que crea y **se borra**: las ramas `lab/monitoreo/*`, el issue y la etiqueta `alerta-deriva`; y el workflow, desactivado.']) + '''</div>
 <div class="card"><h3>Lo de Google Cloud (S4), sin repetirlo</h3>''' + lista([
        'Un **presupuesto** con alertas (en S4, 20 € al 50, 90 y 100 %): **avisa, no corta nada**.',
        'Lo que más cobra si se olvida es lo que **sigue encendido** (un clúster, un endpoint): se **borra** con los scripts de borrado, siempre.',
        'Guía completa: [Laboratorio Cloud Journey](../../S4-Orquestacion-y-CI-CD/laboratorio-cloud-journey/guia.md) (`01-Sesiones/S4-Orquestacion-y-CI-CD/laboratorio-cloud-journey/guia.md`).']) + '''</div>
</div>
''' + callout('**Dos reglas del oficio:** un aviso que nadie lee **no protege** (por eso la alerta es un rojo y un issue), y **lo que creas, lo borras**.', 'margin-top:14px'),
          'Cierre de costes sin repetir S4: este laboratorio no usa la nube de pago. Se recuerdan las dos ideas de S4: el presupuesto con alertas avisa pero no corta, y lo que se crea se borra. Se enlaza la guía de Cloud Journey de S4. Los minutos exactos de Actions del workflow están sin dato hasta que el profesor lo ensaye.')

    # ------------------------------------------------------------------ G · Cierre
    slide('G', 5, 'Si algo falla', 'casos y qué hacer', 'Si algo falla: casos y qué hacer', '<div class="card">' + tabla(['Síntoma', 'Causa', 'Qué hacer', '¿Visto?'], [
        ['`No module named ia_mlops`', 'No estás en `04-Proyecto-Base`', '`cd 04-Proyecto-Base`', 'previsto'],
        ['`Error: La referencia «2010-12-1» no tiene la forma AAAA-MM-DD`', 'Fecha sin ceros (salida 2)', 'Escribe `2010-12-01`', 'sí (26/11)'],
        ['`deriva` sale 1 con casi cualquier pareja de cortes', '`antiguedad_dias` siempre crece con el tiempo', 'Léela como esperable; compara con `--umbral-psi`', 'sí (26/11)'],
        ['`rendimiento` con un corte de entrenamiento da **salida 1**', 'El AUC en entrenamiento sobreestima', 'Empieza por un corte de **prueba** (L2)', 'sí (26/11)'],
        ['`volver`: «no hay a dónde volver» (2)', 'Esa versión no guardó anterior', '`promover --version N`', 'sí (26/11)'],
        ['`--fuente muestra` falla con `R03_integridad_referencial`', 'Quedan tablas de los datos completos', '`rm data/processed/curso.db` y repetir', 'sí (26/11)'],
        ['`gh: Resource not accessible by integration` en la alerta', 'Falta permiso de escritura de issues', 'Revisa los permisos del workflow y de Actions', 'sin verificar'],
        ['El schedule no corre', 'En un *fork* viene desactivado y solo corre en la rama por defecto', 'Actívalo en Actions o usa `workflow_dispatch`', 'previsto']]) + '</div>',
          'Los casos marcados con sí se vieron de verdad el veintiséis de noviembre en la copia de ensayo. Los marcados previsto vienen de la documentación o de la práctica de S4. El de permisos de issues no se ha provocado: con el permiso del workflow, la alerta funcionó. Si un alumno encuentra otro, que lo cuente para completar el material.')

    slide('G', 5, 'Qué se comprobó de verdad', 'qué se comprobó y qué no', 'Qué se comprobó de verdad y qué falta', f'''
<div class="grid2">
 <div class="card"><h3 class="okc">Comprobado el {FECHA} (copia de ensayo, Windows)</h3>''' + lista([
        '**L1 y L2:** `cortes`, `datos` (salida 1, 5 de 13), `rendimiento` (salidas 0 y 1) con las cifras de esta presentación.',
        '**L3:** v2 con datos completos (AUC de test **0.7956** frente a **0.7471**), `promover`, `cargar` (**0.7245** y **0.8279**) y `volver`.',
        '**Workflow:** YAML válido, permisos, órdenes y opciones que existen, `bash -n` de cada paso, y los dos escenarios **ejecutados en local sobre los datos reales** (estable → 0, deriva → 1).',
        'El **resumen** y el **cuerpo del issue** se generan bien a partir de los JSON reales.']) + '''</div>
 <div class="card"><h3 class="malc">Sin verificar o sin dato</h3>''' + lista([
        '**Todo lo de GitHub Actions**: los dos runs, el issue, el comentario del segundo run y los permisos (`issues: write`). Las capturas están **pendientes**.',
        'Las órdenes **en un Codespace** (Linux): se ejecutaron en Windows.',
        'El tiempo de `--fuente completo` en un Codespace (**437 s** en el ensayo) y los minutos de Actions: **sin dato**.',
        'Un **umbral de PSI** o una **tolerancia de AUC** razonables para el negocio: son convenciones, no salen de ninguna medición.']) + '''</div>
</div>''',
          'Diapositiva de honestidad. Lo comprobado es todo lo que se ejecutó en local, con sus cifras. Lo no comprobado es todo lo de GitHub Actions: se ensayará con el profesor y se insertarán entonces las capturas. Tampoco se probó en un Codespace con Linux ni se midieron los minutos de Actions.')

    slide('G', 4, 'Cierre', 'El mensaje', 'Un modelo en producción se vigila, se versiona y se puede deshacer', '''
<div class="msg">La <b>deriva</b> se mide, el <b>alias</b> es un puntero que se mueve y se vuelve a mover, y la <b>alerta es el rojo</b>: sin él, nadie se entera.</div>
<div class="grid4" style="margin-top:18px">
 ''' + kpi('5 de 13', 'variables con PSI por encima de 0,25 entre 2010-12-01 y 2011-12-10: `deriva datos` sale **1**', '') + kpi('0,8497 → 0,6982', 'AUC en un corte de **entrenamiento** y en el de validación: **medir con datos de entrenamiento engaña**', '') + kpi('0,8279 → 0,7245', 'probabilidad del cliente de ejemplo con la **v1** y la **v2**: el alias se nota; `volver` la devuelve', '') + kpi('0 · 1 · 2', 'códigos de salida de `deriva`: **sin deriva · deriva · error**; un workflow decide con ellos', '') + '''
</div>
<div style="text-align:center;margin-top:44px;font-size:44px;font-weight:700;color:var(--acento)">¿Preguntas?</div>''',
          'Cierre con un único mensaje: un modelo en producción se vigila, se versiona y se puede deshacer. Las cuatro cifras son reales: cinco de trece variables con deriva, el AUC de entrenamiento frente al de validación, la probabilidad con la versión uno y la dos, y los códigos de salida de la orden. La operación de agentes, y la tarea de la sesión, siguen en el resto de S5.')


def html_completo():
    construir()
    js = JS.replace('__PARTES__', json.dumps(PARTES, ensure_ascii=False))
    partes = ''.join(f'<button class="part" data-p="{k}">{esc(v)}</button>' for k, v in PARTES.items())
    return ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>Laboratorio de MLOps clásico de S5: deriva, alias y alertas · ML e IA: de desarrollo a producción</title>\n'
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
