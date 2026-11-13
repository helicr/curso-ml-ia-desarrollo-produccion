"""Genera 01-Sesiones/D01-Guion-Alumno.html y D01-Guion-Profesor.html (día 1 = S0 + S1).

Uso (desde la raíz del repositorio):  python 00-Planificacion/guion-d01/generar.py
El contenido es común; lo marcado como `prof` solo aparece en la versión del profesor.
Los HTML son autónomos: sin librerías ni recursos externos.
"""
import html
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parents[2]
S0 = "S0-Presentacion-y-Entorno"
S1 = "S1-Datos-y-Entrenamiento"

# (sesión, min_inicio, duración, título, diapositivas, texto para el alumno, extras del profesor)
BLOQUES = [
    ("S0", 0, 25, "Parte A · Por qué y cómo", "S0 · 1–11",
     "Objetivos del curso, el recorrido del notebook al servicio, las capas raw → master → fs → ml, el método (ver, ejecutar, adaptar, explicar), la cadena de entregas y la evaluación 20/40/40.",
     dict(mensaje="Empieza por la 2 (pregunta de arranque), la 3 (núcleo obligatorio frente a opcional) y la 4 (del notebook al servicio). Después la 7 (capas), la 9 (método) y la 10 (cadena de entregas: el primer avance es sobre Bank Marketing).",
          preguntas=["¿Qué parte del camino te preocupa más hoy? (diapositiva 2, contador en vivo)"],
          ojo="Si vas justo: la 5 (estadísticas) y la 8 (equivalencias con GCP) se resumen en una frase cada una. Las cifras de la 5 son históricas (Anaconda 2020): preséntalas como contexto.")),
    ("S0", 25, 15, "Pausa", "S0 · 12", "Descanso de 15 minutos.",
     dict(mensaje="El contador solo arranca al pulsar «Iniciar pausa». «Ir a la Parte B» sigue a la diapositiva 13.", preguntas=[],
          ojo="Aprovecha para pegar en el chat la ruta del repositorio y la rama `develop`.")),
    ("S0", 40, 70, "Parte B · Entorno (obligatorio)", "S0 · 13–27",
     "Qué software necesita cada sesión y para qué; clonar el repositorio; Miniconda y el entorno `env-ia-mlops`; VS Code y notebooks; SQLite; Docker y Kubernetes en Codespaces; Google Cloud (autenticar, no gastar); diagnóstico de 12 comprobaciones.",
     dict(mensaje="Cada paso responde cuatro preguntas: para qué sirve, qué ejecuto, qué debo ver, qué reviso si falla. No se improvisa en silencio: se anota el comando y la salida.",
          preguntas=["¿Qué ves en pantalla? ¿Coincide con «lo esperado»? (en cada paso)"],
          ojo="Los pasos con comandos (19–25) conservan sus tiempos; el diagnóstico (27) son 10 min. Las diapositivas 15 y 16 (qué se necesita en cada sesión) van antes de instalar. Equipo listo para S1 con copiar y pegar: `01-Sesiones/%s/slides/instalacion/index.html`." % S0)),
    ("S0", 110, 10, "Cierre de S0 y presentación de los dos casos", "S0 · 28–31",
     "Completar el diagnóstico, comunicar bloqueos, leer el caso de Bank Marketing (el tuyo) y no improvisar el entorno. En S1 se trabaja el caso del instructor, Online Retail II.",
     dict(mensaje="Las diapositivas 28 y 29 presentan cada caso con su pregunta, el contenido del archivo y la ruta del CSV. Aquí se revelan los dos casos: el del instructor (Online Retail II, en S1) y el de ellos (Bank Marketing, UCI, ya en el repositorio). La tarea: leer el enunciado y `bank-additional-names.txt` y comprobar la huella del archivo.",
          preguntas=[], ojo="No adelantes el entrenamiento. Recalca: `duration` no se usa como variable y las filas del CSV no se reordenan.")),
    ("S1", 0, 30, "Revisión de entorno", "S1 · 1–3",
     "Cada persona comprueba que su entorno funciona: activar `env-ia-mlops`, ejecutar la prueba de humo y las pruebas del proyecto base (esperado: 131 passed).",
     dict(mensaje="Agenda en 1 minuto (diapositiva 2). Después, a ejecutar la diapositiva 3 («Copiar comandos»).", preguntas=[],
          ojo="S0 ya hizo el diagnóstico: si casi todos pasan, reduce a 10–15 min. Anota quién no pasa y el error exacto; esas personas siguen con Codespaces o en pareja. No se detiene la sesión. Si pasados 30 min más de un tercio no tiene entorno, recorta teoría (diap. 11 y 16), no práctica.")),
    ("S1", 30, 60, "Teoría: de los datos al modelo", "S1 · 4–16",
     "El caso Online Retail II y su pregunta; la base operacional (la fuente) y las capas RAW, MASTER, FS y ML; calidad; la regla de oro de FS (sin información del futuro); partición temporal; entrenamiento y comparación de modelos; seguimiento con MLflow; del cuaderno al paquete Python.",
     dict(mensaje="Imprescindibles: la 10 (regla de oro de FS, 8 min), la 13 (temporal frente a aleatoria: aquí la aleatoria dio MENOS AUC; la razón de la temporal es el uso real), la 14 (sobreajuste: 0,842 en train frente a 0,781 en test) y la 15 (MLflow).",
          preguntas=["¿Quién decide a quién se le escribe? (4)", "¿Por qué FS va antes que ML? (5)", "¿Qué pasa si limpiamos sobre RAW? (7)",
                     "¿Dónde estaría la fuga si usáramos la factura roja? (10)", "¿Qué modelo desplegarías y por qué? (14)", "¿Cómo sabes que dos ejecuciones son comparables? (15)"],
          ojo="Recorte si hace falta: diapositiva 11 (catálogo de variables) y 16 (cuaderno a paquete). Las cifras son del dato completo; con la muestra del curso los valores son menores (esperado).")),
    ("S1", 90, 135, "Práctica guiada: los cinco cuadernos", "S1 · 17",
     "Cuaderno 00 (base operacional), 01 (operacional→RAW→MASTER), 02 (MASTER→FS), 03 (FS→ML) y 04 (entrenamiento y MLflow); traducción a `.py` y pruebas. Pausa de 10 minutos. Guía: `01-Sesiones/%s/practica/guia-laboratorio.md`." % S1,
     dict(mensaje="Ritmo: 10 preparar · 30 cuadernos 00 y 01 · 25 cuaderno 02 · 10 pausa · 25 cuaderno 03 · 25 cuaderno 04 · 10 `.py` y pruebas.", preguntas=[],
          ojo="Recorre el chat o las pantallas a los 15 min de cada bloque. Quien termine antes empieza la tarea (variable nueva). Si el 01 falla: falta el 00; si falla el 02, falta el 01: ejecutar desde el primero que falte. Kernel: `env-ia-mlops`. MLflow UI: `mlflow ui --backend-store-uri sqlite:///models/mlflow.db` desde `04-Proyecto-Base`.")),
    ("S1", 225, 15, "Entrega y cierre", "S1 · 18–20",
     "La tarea (añadir una variable a FS en Online Retail II y decidir con evidencia), errores frecuentes, y el avance en S2 sobre tu caso, Bank Marketing.",
     dict(mensaje="Dos entregables: (1) la tarea de la variable nueva, sobre Online Retail II; (2) el avance en S2 sobre Bank Marketing: RAW → MASTER → FS → ML, entrenamiento y métricas, como cuadernos. Evidencia: decisión escrita + comparación de dos ejecuciones en MLflow + traducción a `.py`.",
          preguntas=[], ojo="Anuncia qué trae S2: cargar el modelo desde MLflow, API con FastAPI, imagen Docker y primer workflow de GitHub Actions.")),
]

ENTREGABLES = [
    ("Antes de S2", "Tarea S1: añade una variable nueva a FS (Online Retail II), reconstruye ML, reentrena, compara dos ejecuciones en MLflow y decide si se queda. Entrega también la traducción a `.py`.",
     "01-Sesiones/%s/tarea/README.md" % S1),
    ("Avance en S2", "Tu caso, Bank Marketing: capas RAW → MASTER → FS → ML, entrenamiento y métricas, como cuadernos. `duration` no se usa; no reordenes las filas del CSV.",
     "02-Proyecto-Transversal/enunciado/README.md"),
]
AYUDA = [
    ("El entorno no se crea o `conda` pide aceptar términos", "Usa la receta de 4 comandos de la guía de preparación (canal conda-forge)."),
    ("El cuaderno 02 falla", "Falta ejecutar el 01: lanza «Run All» desde el 01."),
    ("El cuaderno no encuentra paquetes", "Elige el kernel `env-ia-mlops` (esquina superior derecha de VS Code)."),
    ("`mlflow ui` no abre", "Desde `04-Proyecto-Base`: `mlflow ui --backend-store-uri sqlite:///models/mlflow.db`."),
    ("Mis números no coinciden con la diapositiva", "Es normal: la muestra del curso da valores menores que el dato completo."),
    ("Docker o Kubernetes no funcionan", "No se instalan en tu equipo: se usan en el Codespace del curso. Si no puedes abrirlo, avisa y trabaja en pareja."),
]
PREVIO = [
    "Presentaciones abiertas sin conexión y probadas: `01-Sesiones/%s/slides/index.html` y `01-Sesiones/%s/slides/index.html`." % (S0, S1),
    "Probar la plataforma de la clase (Google Meet): compartir pantalla, audio y el chat.",
    "Repositorio: `main` sigue sin fusionar; los comandos de clonado usan `git clone --branch develop`.",
    "Codespace del curso: está escrito (`.devcontainer/`) pero NO probado en un Codespace real. Ábrelo una vez o ejecuta el workflow «Validar Codespace del curso» antes de clase.",
    "Windows real: los scripts de instalación y el entorno no se han probado en Windows real; ten a mano la guía rápida (`practica/guia-rapida-entorno-s0-s1.md`) y las diapositivas de copiar y pegar.",
    "Cifras y tarifas externas: no reverificadas. Presenta las de la diapositiva 5 como contexto histórico y no cites tarifas.",
    "Enviar a los alumnos la guía de instalación para Windows (`03-Entorno/guia-instalacion/index.html`) antes de empezar.",
    "Tener a mano los PDF de las presentaciones (`pdfs/`) por si falla el proyector o la conexión.",
]
FALLOS_PROF = [
    ("Más de un tercio sin entorno al minuto 30 de S1", "Recorta teoría (11 y 16), no práctica; esas personas, a Codespaces o en pareja."),
    ("Se agota el tiempo en S0 Parte B", "Deja el diagnóstico (27) como tarea; el resto del entorno puede cerrarse antes de S1 con la guía rápida."),
    ("La presentación no abre o va lenta", "Usa el PDF de `pdfs/`; pierde animaciones pero conserva todo el contenido."),
    ("Preguntas sobre cifras o tarifas", "«Es un dato de contexto; las tarifas cambian y se revisan en S3.»"),
    ("«¿Por qué dos casos?»", "El del instructor se explica con detalle en S1; el vuestro, Bank Marketing, repite la receta como avance en S2."),
]

D0 = "%s/slides/index.html" % S0
D1 = "%s/slides/index.html" % S1


def _d(deck, ini, fin):
    """Un solo enlace por bloque: abre la presentación en la diapositiva `ini` y se sigue con → (no hace falta empezar en la 1)."""
    rango = "%d" % ini if ini == fin else "%d–%d" % (ini, fin)
    return [("Presentación: abre en la diap. %d y sigue con → (bloque: %s)" % (ini, rango), "%s#%d" % (deck, ini))]


# Qué abrir en cada bloque: (texto, enlace relativo a 01-Sesiones/). Los enlaces `#N` abren la diapositiva N.
ABRIR_ALUMNO = [
    _d(D0, 1, 11),
    _d(D0, 12, 12),
    _d(D0, 13, 27) + [
        ("Equipo listo para S1 (copiar y pegar)", "%s/slides/instalacion/index.html" % S0),
        ("Guía rápida del entorno", "%s/practica/guia-rapida-entorno-s0-s1.md" % S0),
        ("Guía de instalación para Windows", "../03-Entorno/guia-instalacion/index.html")],
    [("Diap. 28 · Caso 1: Online Retail II", D0 + "#28"), ("Diap. 29 · Caso 2: Bank Marketing", D0 + "#29"), ("Diap. 30 · Antes de S1", D0 + "#30")] + [("Enunciado del caso", "../02-Proyecto-Transversal/enunciado/README.md"),
                      ("Datos de Bank Marketing", "../02-Proyecto-Transversal/datos/LEEME.md"),
                      ("Documentación del dato", "../02-Proyecto-Transversal/datos/bank-marketing/bank-additional-names.txt")],
    _d(D1, 1, 3) + [("Prueba de humo", "../03-Entorno/conda/prueba_de_humo.py"), ("Proyecto base", "../04-Proyecto-Base/README.md")],
    _d(D1, 4, 16) + [("Resumen de teoría", "%s/teoria/README.md" % S1)],
    _d(D1, 17, 17) + [("Guía del laboratorio", "%s/practica/guia-laboratorio.md" % S1),
                  ("Cuaderno 01", "../04-Proyecto-Base/notebooks/01_pipeline_raw_a_master.ipynb"),
                  ("Cuaderno 02", "../04-Proyecto-Base/notebooks/02_pipeline_master_a_fs.ipynb"),
                  ("Cuaderno 03", "../04-Proyecto-Base/notebooks/03_pipeline_fs_a_ml.ipynb"),
                  ("Cuaderno 04", "../04-Proyecto-Base/notebooks/04_entrenamiento_y_seguimiento.ipynb")],
    _d(D1, 18, 20) + [("Tarea de S1", "%s/tarea/README.md" % S1), ("Rúbrica", "%s/tarea/rubrica.md" % S1),
                          ("Plantilla de la decisión", "%s/evidencias/plantilla-decision.md" % S1),
                          ("Enunciado del avance (Bank Marketing)", "../02-Proyecto-Transversal/enunciado/README.md")],
]
ABRIR_PROFESOR = [
    [("Guion de S0", "%s/guion.md" % S0), ("Checklist de S0", "%s/checklist.md" % S0)],
    [],
    [("Presupuesto de tiempo: clic en la barra de la diap. 13", D0 + "#13"), ("Diagnóstico de 12 comprobaciones (diap. 27)", D0 + "#27"),
     ("Guía de uso por herramienta", "../07-Recursos/guias/README.md"), ("Validación del entorno", "../03-Entorno/VALIDACION.md")],
    [("Notas del orador: tecla S en cada diapositiva", D0 + "#28")],
    [("Guion de S1", "%s/guion.md" % S1), ("Checklist de S1", "%s/checklist.md" % S1), ("Probar en Windows", "../03-Entorno/PRUEBA-EN-WINDOWS.md")],
    [("Interactiva: regla de oro (diap. 10)", D1 + "#10"), ("Interactiva: capas (diap. 5)", D1 + "#5")],
    [("Si algo falla en la práctica: tabla del guion de S1", "%s/guion.md" % S1)],
    [("Checklist de entrega", "%s/checklist.md" % S1), ("Si el alumno pregunta por el avance: dataset-candidatos", "../02-Proyecto-Transversal/dataset-candidatos.md")],
]

BASE_ALUMNO = "C:/cursos/curso-ml-ia-desarrollo-produccion"   # donde la guía manda clonar (cd C:\cursos)
BASE_PROFESOR = RAIZ.as_posix()

# Prácticas que se abren en VS Code, por bloque: (texto, ruta dentro del repositorio). Solo si el repositorio está clonado en BASE_*.
VSCODE = {
    2: [("Carpeta del curso", ""), ("Cuaderno de prueba del kernel", "03-Entorno/conda/prueba_notebook.ipynb")],
    4: [("Carpeta del proyecto base", "04-Proyecto-Base")],
    6: [("Carpeta del proyecto base", "04-Proyecto-Base"), ("Guía del laboratorio", "01-Sesiones/%s/practica/guia-laboratorio.md" % S1),
        ("Cuaderno 01", "04-Proyecto-Base/notebooks/01_pipeline_raw_a_master.ipynb"), ("Cuaderno 02", "04-Proyecto-Base/notebooks/02_pipeline_master_a_fs.ipynb"),
        ("Cuaderno 03", "04-Proyecto-Base/notebooks/03_pipeline_fs_a_ml.ipynb"), ("Cuaderno 04", "04-Proyecto-Base/notebooks/04_entrenamiento_y_seguimiento.ipynb")],
    7: [("Plantilla de la decisión", "01-Sesiones/%s/evidencias/plantilla-decision.md" % S1)],
}

PASOS_VSCODE = [
    ("Dónde", r"Se clona en `C:\cursos` (carpeta nueva). El proyecto queda en `C:\cursos\curso-ml-ia-desarrollo-produccion`."),
    ("Cómo", r"Terminal (CMD o PowerShell): `cd C:\cursos`, `git clone --branch develop https://github.com/helicr/curso-ml-ia-desarrollo-produccion.git`, `cd curso-ml-ia-desarrollo-produccion`, `git branch --show-current` (debe decir develop) y `code .`."),
    ("Abrir la carpeta", "Se abre la **carpeta** del repositorio, no un archivo suelto (Archivo → Abrir carpeta, o `code .`). Si VS Code pregunta si confías en los autores, acepta: la clonaste tú."),
    ("Intérprete", "`Ctrl+Mayús+P` → «Python: Select Interpreter» → `env-ia-mlops`. Debe verse en la barra inferior."),
    ("Terminal de VS Code", "`Ctrl+ñ` (o Terminal → Nueva terminal): `conda activate env-ia-mlops` y `cd 04-Proyecto-Base`. Con el Anaconda Prompt también vale."),
    ("Cuadernos", "Abre un `.ipynb` → «Seleccionar kernel» (arriba a la derecha) → Python Environments → `env-ia-mlops`."),
    ("Novedades", "Para traer cambios del repositorio: `git pull` desde la carpeta del curso."),
]

CASOS = [
    ("Caso 1 · Online Retail II", "El que desarrolla el profesor (S1)", "Una tienda online: ¿este cliente volverá a comprar en 90 días?",
     "Una fila = una línea de factura. 8 columnas: Invoice, StockCode, Description, Quantity, InvoiceDate, Price, Customer ID, Country.",
     "04-Proyecto-Base/data/raw/muestra_online_retail_ii.csv (muestra de 23 070 filas). Completo: `python -m ia_mlops.dataset descargar`.", "Diap. 28"),
    ("Caso 2 · Bank Marketing", "El de la tarea de los alumnos (S1–S5)", "Un banco que vende depósitos por teléfono: ¿este cliente lo contratará?",
     "Una fila = una llamada. 41 188 filas, 20 columnas y la respuesta `y` (sí/no), separador `;`. No usar `duration`; no reordenar las filas.",
     "02-Proyecto-Transversal/datos/bank-marketing/bank-additional-full.csv (columnas explicadas en bank-additional-names.txt).", "Diap. 29"),
]

CSS = """
:root{--bg:#06182c;--panel:#0d2744;--line:#25476e;--text:#e8f1fb;--mut:#9db6d3;--blue:#2bb3ff;--gold:#fcd34d}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.55 "Segoe UI",system-ui,sans-serif}
main{max-width:1000px;margin:0 auto;padding:28px 22px 80px}
h1{font-size:30px;margin:.1em 0}h2{font-size:21px;margin:1.6em 0 .5em;border-bottom:1px solid var(--line);padding-bottom:6px}
.kick{color:var(--gold);font-weight:700;letter-spacing:.08em;font-size:13px;text-transform:uppercase}
.mut{color:var(--mut)}code{background:#021224;border:1px solid var(--line);padding:1px 6px;border-radius:5px;font-family:Consolas,monospace;font-size:.92em}
.blk{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 18px;margin:12px 0}
.blk h3{margin:0 0 4px;font-size:18px}.meta{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px}
.chip{background:#04213f;border:1px solid var(--blue);color:var(--blue);border-radius:99px;padding:1px 10px;font-size:13px;font-weight:600}
.chip.g{border-color:var(--gold);color:var(--gold)}
.prof{border-left:4px solid var(--gold);background:#2a2208;border-radius:8px;padding:8px 14px;margin:10px 0}
.prof b.t{color:var(--gold);display:block;font-size:13px;letter-spacing:.06em;text-transform:uppercase}
table{border-collapse:collapse;width:100%;margin:8px 0}th,td{border:1px solid var(--line);padding:6px 10px;text-align:left;vertical-align:top}th{background:#0a2240}
ul{margin:.3em 0 .3em 1.2em;padding:0}li{margin:.2em 0}
.bar{position:sticky;top:0;z-index:5;background:#04101e;border-bottom:1px solid var(--line);padding:8px 22px;display:flex;gap:16px;align-items:center;flex-wrap:wrap}
.bar label{color:var(--mut);font-size:14px}.bar input{background:#021224;color:var(--text);border:1px solid var(--line);border-radius:6px;padding:3px 6px}
.abrir{margin:8px 0;display:flex;flex-wrap:wrap;gap:6px;align-items:center}.abrir>b{color:var(--mut);font-size:14px;margin-right:4px}
a.ab{background:#04213f;border:1px solid var(--line);border-radius:7px;padding:2px 9px;font-size:14px;color:var(--blue);text-decoration:none}a.ab:hover{border-color:var(--blue)}
a.vs{border-color:#34d399;color:#34d399}
.pasos{margin:.4em 0 .4em 1.2em}
.chk{display:flex;gap:8px;align-items:flex-start;margin:4px 0}.chk input{margin-top:6px}
.done{opacity:.55;text-decoration:line-through}
@media print{a.ab{color:#000;border-color:#666}.bar{display:none}body{background:#fff;color:#000}.blk,.prof{background:#fff;border-color:#999}code{background:#eee;color:#000}.chip{color:#000;border-color:#666}th{background:#eee}h2{color:#000}.mut,.kick{color:#333}}
"""

SCRIPT = """<script>
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
function hhmm(m){m=((m%1440)+1440)%1440;return String(Math.floor(m/60)).padStart(2,'0')+':'+String(m%60).padStart(2,'0')}
function pintar(){const [h,mi]=$('#ini').value.split(':').map(Number);const d=+$('#desc').value||0;
 $$('.hora').forEach(e=>{const m=+e.dataset.m,base=h*60+mi+(e.dataset.s==='S0'?0:120+d);e.textContent=hhmm(base+m)})}
$('#ini').oninput=$('#desc').oninput=()=>{pintar();localStorage.setItem('d01-ini',$('#ini').value);localStorage.setItem('d01-desc',$('#desc').value)};
$('#ini').value=localStorage.getItem('d01-ini')||$('#ini').value;$('#desc').value=localStorage.getItem('d01-desc')||$('#desc').value;pintar();
$$('input[data-k]').forEach(c=>{c.checked=localStorage.getItem('d01-'+c.dataset.k)==='1';c.parentElement.classList.toggle('done',c.checked);
 c.onchange=()=>{localStorage.setItem('d01-'+c.dataset.k,c.checked?'1':'0');c.parentElement.classList.toggle('done',c.checked)}});
</script>"""


def md(t):
    """Convierte `código` en <code> y escapa el resto."""
    out = []
    for i, p in enumerate(html.escape(t).split("`")):
        out.append(("<code>%s</code>" % p) if i % 2 else p)
    return "".join(out)


def abrir(items, titulo):
    if not items:
        return ""
    lis = "".join("<a class='ab' href='%s' target='_blank' rel='noopener'>%s</a>" % (html.escape(u, quote=True), html.escape(t)) for t, u in items)
    return "<div class='abrir'><b>%s:</b> %s</div>" % (html.escape(titulo), lis)


def abrir_vscode(i, base):
    items = VSCODE.get(i)
    if not items:
        return ""
    lis = "".join("<a class='ab vs' href='vscode://file/%s'>%s</a>" % (html.escape(base + ("/" + r if r else ""), quote=True), html.escape(t)) for t, r in items)
    return "<div class='abrir'><b>Abrir en VS Code (si el repositorio está en <code>%s</code>):</b> %s</div>" % (html.escape(base.replace("/", "\\")), lis)


def generar(prof):
    titulo = "Día 1 · Guion del profesor" if prof else "Día 1 · Guion del alumno"
    h = ["<!doctype html><html lang='es'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
         "<title>%s</title><style>%s</style></head><body>" % (titulo, CSS)]
    if prof:
        h.append("<div class='bar'><b>Reloj de clase</b><label>Inicio de S0 <input type='time' id='ini' value='09:00'></label>"
                 "<label>Descanso entre S0 y S1 (min) <input type='number' id='desc' value='15' min='0' max='120' style='width:70px'></label>"
                 "<span class='mut'>Las horas de cada bloque se calculan con estos dos valores.</span></div>")
    h.append("<main><p class='kick'>ML e IA: de desarrollo a producción</p><h1>%s</h1>" % titulo)
    h.append("<p class='mut'>S0 (120 min) + S1 (240 min) = 6 horas de clase, más el descanso entre sesiones. "
             "Presentaciones: <code>01-Sesiones/%s/slides/index.html</code> y <code>01-Sesiones/%s/slides/index.html</code>.</p>" % (S0, S1))
    if prof:
        h.append("<h2>Antes de empezar (checklist del profesor)</h2>")
        for i, t in enumerate(PREVIO):
            h.append("<label class='chk'><input type='checkbox' data-k='previo%d'><span>%s</span></label>" % (i, md(t)))
    h.append("<h2>Resumen del día</h2><table><tr><th>Bloque</th><th>Duración</th><th>Diapositivas</th>%s</tr>" % ("<th>Hora</th>" if prof else ""))
    for s, ini, dur, tit, dia, *_ in BLOQUES:
        celda = ("<td class='hora' data-s='%s' data-m='%d'></td>" % (s, ini)) if prof else ""
        h.append("<tr><td>%s · %s</td><td>%d min</td><td>%s</td>%s</tr>" % (s, html.escape(tit), dur, html.escape(dia), celda))
    h.append("</table>")
    h.append("<h2>Cómo se abre el proyecto en VS Code</h2><table><tr><th>Paso</th><th>Qué hacer</th></tr>")
    for a, b in PASOS_VSCODE:
        h.append("<tr><td>%s</td><td>%s</td></tr>" % (html.escape(a), md(b).replace("**", "")))
    h.append("</table>")
    if prof:
        h.append("<p class='prof'><b class='t'>Para el profesor</b>Los botones verdes «Abrir en VS Code» usan <code>vscode://file/…</code> y solo funcionan si el repositorio está en la ruta indicada (tu copia: <code>%s</code>); los de la versión del alumno apuntan a <code>C:&#92;cursos&#92;curso-ml-ia-desarrollo-produccion</code>. Si VS Code no se abre, copia la ruta y usa Archivo → Abrir carpeta.</p>" % html.escape(BASE_PROFESOR.replace("/", "\\")))
    for sesion, titulo_s in (("S0", "S0 · Presentación y entorno (120 min)"), ("S1", "S1 · De los datos al modelo (240 min)")):
        h.append("<h2>%s</h2>" % titulo_s)
        for i, (s, ini, dur, tit, dia, alumno, p) in enumerate(BLOQUES):
            if s != sesion:
                continue
            hora = ("<span class='chip g hora' data-s='%s' data-m='%d'></span>" % (s, ini)) if prof else ""
            h.append("<div class='blk'><h3>%s</h3><div class='meta'><span class='chip'>%d min</span><span class='chip'>%s</span>%s</div><p>%s</p>"
                     % (html.escape(tit), dur, html.escape(dia), hora, md(alumno)))
            h.append(abrir(ABRIR_ALUMNO[i], "Abrir en este bloque"))
            h.append(abrir_vscode(i, BASE_PROFESOR if prof else BASE_ALUMNO))
            if i == 3:
                h.append("<table><tr><th>Caso</th><th>Quién lo desarrolla</th><th>Pregunta</th><th>Qué hay en el archivo</th><th>Dónde está el CSV</th><th>Slide</th></tr>")
                for c in CASOS:
                    h.append("<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % tuple(md(x) for x in c))
                h.append("</table>")
            if prof:
                h.append("<div class='prof'><b class='t'>Para el profesor</b><p><b>Mensaje clave.</b> %s</p>" % md(p["mensaje"]))
                if p["preguntas"]:
                    h.append("<p><b>Preguntas a la audiencia.</b></p><ul>%s</ul>" % "".join("<li>%s</li>" % md(q) for q in p["preguntas"]))
                h.append("<p><b>Ojo.</b> %s</p>" % md(p["ojo"]))
                h.append(abrir(ABRIR_PROFESOR[i], "Solo para ti"))
                h.append("</div>")
            h.append("</div>")
    h.append("<h2>Qué tienes que entregar</h2><table><tr><th>Cuándo</th><th>Qué</th><th>Dónde se explica</th></tr>")
    for c, q, r in ENTREGABLES:
        h.append("<tr><td>%s</td><td>%s</td><td><code>%s</code></td></tr>" % (html.escape(c), md(q), html.escape(r)))
    h.append("</table><h2>Si algo falla</h2><table><tr><th>Síntoma</th><th>Qué hacer</th></tr>")
    for a, b in AYUDA:
        h.append("<tr><td>%s</td><td>%s</td></tr>" % (md(a), md(b)))
    h.append("</table>")
    if prof:
        h.append("<h2>Si algo falla en directo (profesor)</h2><table><tr><th>Situación</th><th>Respuesta</th></tr>")
        for a, b in FALLOS_PROF:
            h.append("<tr><td>%s</td><td>%s</td></tr>" % (md(a), md(b)))
        h.append("</table><h2>Materiales de apoyo</h2><ul>"
                 "<li>Guion detallado: <code>01-Sesiones/%s/guion.md</code> y <code>01-Sesiones/%s/guion.md</code></li>"
                 "<li>Notas del orador en cada diapositiva: tecla <b>S</b>; índice: <b>O</b>; pantalla completa: <b>F</b></li>"
                 "<li>PDF de respaldo: <code>pdfs/%s/</code> y <code>pdfs/%s/</code></li>"
                 "<li>Checklist de S0: <code>01-Sesiones/%s/checklist.md</code>; de S1: <code>01-Sesiones/%s/checklist.md</code></li>"
                 "<li>Plan del día: <code>00-Planificacion/guion-manana.md</code></li></ul>" % (S0, S1, S0, S1, S0, S1))
        h.append(SCRIPT)
    h.append("</main></body></html>")
    return "".join(h)


if __name__ == "__main__":
    for prof, nombre in ((False, "D01-Guion-Alumno.html"), (True, "D01-Guion-Profesor.html")):
        destino = RAIZ / "01-Sesiones" / nombre
        destino.write_text(generar(prof), encoding="utf-8")
        print(destino.relative_to(RAIZ), destino.stat().st_size, "bytes")
