"""Fuente del índice de cada sesión (`01-Sesiones/Sx-.../index.html`).

`generar_indices.py` crea un `index.html` dentro de cada carpeta de sesión con:
  - sus presentaciones y documentos (los de esta lista, con su descripción);
  - cualquier otro .html o .md que haya en la carpeta y no esté aquí: aparece solo, con el título que tenga el archivo;
  - qué componentes de la sesión existen y cuáles faltan (presentación, guion, teoría, práctica, tarea…).

Para describir un archivo nuevo o cambiar un texto: edita este archivo y ejecuta
`python 00-Planificacion/indices-de-sesion/generar_indices.py`. Si solo añades un archivo a la carpeta, basta con ejecutar el generador.
"""

CURSO = 'ML e IA: de desarrollo a producción'
SUBTITULO = 'Instructor: Helí Campos R · UNTRM · 2026-II'
REPO_GITHUB = 'https://github.com/helicr/curso-ml-ia-desarrollo-produccion'
RAMA = 'develop'

CARPETA_SESIONES = '01-Sesiones'
ENTORNO = '03-Entorno'

# Grupos de enlaces dentro de la página de una sesión
PRESENTACIONES, ALUMNO, INSTRUCTOR = 'presentaciones', 'alumno', 'instructor'
GRUPOS = [(PRESENTACIONES, 'Presentaciones'), (ALUMNO, 'Para el alumno'), (INSTRUCTOR, 'Para el instructor')]


def deck(titulo, ruta, desc='', volver=False):
    """Presentación o página HTML (se abre siempre desde el disco). `volver`: lleva un enlace de regreso al índice de su sesión."""
    return dict(tipo='deck', grupo=PRESENTACIONES, titulo=titulo, ruta=ruta, desc=desc, volver=volver)


def doc(grupo, titulo, ruta, desc=''):
    """Documento (.md, .py, .yml): según el interruptor de la página se abre en GitHub o desde la carpeta local."""
    return dict(tipo='doc', grupo=grupo, titulo=titulo, ruta=ruta, desc=desc)


def alumno(titulo, ruta, desc=''):
    return doc(ALUMNO, titulo, ruta, desc)


def instructor(titulo, ruta, desc=''):
    return doc(INSTRUCTOR, titulo, ruta, desc)


# Componentes que se espera encontrar en una sesión y cómo se detectan (patrones relativos a la carpeta de la sesión)
COMPONENTES = {
    'presentacion': ('Presentación', ['slides/index.html']),
    'guion': ('Guion', ['guion.md']),
    'checklist': ('Checklist', ['checklist.md']),
    'teoria': ('Teoría', ['teoria/*.md']),
    'practica': ('Práctica', ['practica/*.md']),
    'tarea': ('Tarea', ['tarea/README.md']),
    'rubrica': ('Rúbrica', ['tarea/rubrica.md']),
    'evidencia': ('Plantilla de la evidencia', ['evidencias/*.md']),
}
TODOS = list(COMPONENTES)

# Estados de una sesión
PREPARADO = 'preparado'      # hay material de clase (lo probado y lo no probado está en ESTADO-DEL-PAQUETE.md)
SOLO_README = 'solo_readme'  # la carpeta solo tiene README.md
ESTADOS = {PREPARADO: ('Material preparado', 'ok'), SOLO_README: ('Solo README', 'warn')}

S0, S1, S2, S3, S4, S5 = (f'{CARPETA_SESIONES}/{n}' for n in (
    'S0-Presentacion-y-Entorno', 'S1-Datos-y-Entrenamiento', 'S2-API-y-Docker',
    'S3-Despliegue-y-Redes-Neuronales', 'S4-Orquestacion-y-CI-CD', 'S5-MLOps-y-Operacion'))

SESIONES = [
    dict(
        id='S0', titulo='Presentación y entorno', horas='2 h', carpeta=S0, estado=PREPARADO, esperados=['presentacion', 'guion', 'checklist', 'practica'],
        resumen='Parte A (curso, caso y entregas, 25 min), pausa de 15, Parte B (software local, repositorio, Codespaces, nube y diagnóstico, 70 min) y cierre de 10. '
                'Tarea: completar la preparación y leer el caso. Evidencia: entorno comprobado antes de S1.',
        nota='No tiene teoría ni tarea en archivos propios: la tarea es completar la preparación.',
        enlaces=[
            deck('Presentación principal', f'{S0}/slides/index.html', 'Parte A, pausa, Parte B y cierre. Teclas: ← → avanzar, O índice, S notas, F pantalla completa.', volver=True),
            deck('Tu equipo listo para S1', f'{S0}/slides/instalacion/index.html', 'Para copiar y pegar: instalación en orden, entorno desde environment.yml, pruebas y verificador.', volver=True),
            deck('Anexos de consulta', f'{S0}/slides/anexos/index.html', 'Edición anterior (con React y ECharts). Los anexos A–F siguen vigentes; el resto está desactualizado.'),
            deck('Plan docente', f'{S0}/slides/fuentes/plan-docente.html', 'Una página: programa, ritmo, reparto de S0 y cautelas.'),
            alumno('Guía rápida del entorno (S0 → S1)', f'{S0}/practica/guia-rapida-entorno-s0-s1.md', 'Lo mismo que «Tu equipo listo para S1», en texto.'),
            deck('Guía de instalación para Windows', f'{ENTORNO}/guia-instalacion/index.html', 'Interactiva: elige ruta y terminal, copia los comandos y marca tu progreso.'),
            alumno('Checklist de 12 comprobaciones', f'{S0}/checklist.md', 'Diagnóstico del entorno.'),
            alumno('Requisitos del entorno', f'{ENTORNO}/guias/requisitos.md', 'Qué se instala en tu equipo, qué se usa en la nube y qué versiones.'),
            alumno('Preparación paso a paso (Windows)', f'{ENTORNO}/guias/preparacion-paso-a-paso.md', 'Todo en uno con script o paso a paso; ruta sin instalación.'),
            alumno('Verificador para S1', f'{ENTORNO}/conda/verificar_s1.py', 'Termina en LISTO PARA S1; con --informe guarda verificacion-s1.txt.'),
            instructor('README de S0', f'{S0}/README.md'),
            instructor('Guion con tiempos', f'{S0}/guion.md', 'Minuto a minuto, diapositiva por diapositiva.'),
        ],
    ),
    dict(
        id='S1', titulo='Datos y entrenamiento', horas='4 h', carpeta=S1, estado=PREPARADO, esperados=TODOS,
        resumen='OPERACIONAL → RAW → MASTER → FS → ML con un cuaderno por capa, partición temporal, tres modelos comparados y seguimiento con MLflow. '
                'Tarea: añadir una variable a la capa FS del caso del instructor (Online Retail II) y decidir con evidencia.',
        nota='El caso propio de los alumnos (Bank Marketing) empieza aquí y sigue hasta S5: ver 02-Proyecto-Transversal/enunciado/README.md.',
        enlaces=[
            deck('Presentación de S1', f'{S1}/slides/index.html', 'Revisión del entorno, teoría, práctica, entrega y cierre.', volver=True),
            alumno('Teoría y glosario', f'{S1}/teoria/README.md'),
            alumno('Guía de laboratorio', f'{S1}/practica/guia-laboratorio.md', 'Paso a paso con presupuesto de tiempo.'),
            alumno('Tarea', f'{S1}/tarea/README.md'),
            alumno('Rúbrica', f'{S1}/tarea/rubrica.md', '20 % conocimiento · 40 % desempeño · 40 % producto.'),
            alumno('Plantilla de la decisión', f'{S1}/evidencias/plantilla-decision.md', 'La evidencia que se entrega.'),
            alumno('Checklist', f'{S1}/checklist.md'),
            alumno('Proyecto base (Online Retail II)', '04-Proyecto-Base/README.md', 'Cuadernos, paquete ia_mlops, pruebas y Makefile.'),
            instructor('README de S1', f'{S1}/README.md', 'Agenda por minutos y qué está validado.'),
            instructor('Guion', f'{S1}/guion.md'),
        ],
    ),
    dict(
        id='S2', titulo='API y Docker', horas='4 h', carpeta=S2, estado=SOLO_README, esperados=TODOS,
        resumen='Carga del modelo desde MLflow, FastAPI, validación, Dockerfile e imagen (en Codespaces) y primer workflow de GitHub Actions.',
        enlaces=[
            alumno('Docker y Kubernetes sin instalación local', f'{ENTORNO}/guias/docker-y-kubernetes-sin-instalacion-local.md', 'Ya escrita: cómo trabajar con Docker en Codespaces.'),
            instructor('README de S2', f'{S2}/README.md'),
        ],
    ),
    dict(
        id='S3', titulo='Despliegue en la nube (red neuronal opcional)', horas='4 h', carpeta=S3, estado=SOLO_README, esperados=TODOS,
        resumen='Migrar de local a GCP: Cloud Storage, BigQuery, Secret Manager, Artifact Registry y Cloud Run. Kubernetes en Codespaces si hay tiempo.',
        enlaces=[
            alumno('Guía de migración de local a GCP', f'{ENTORNO}/guias/migracion-on-premise-a-gcp.md', 'Ya escrita; es el hilo de S3.'),
            instructor('README de S3', f'{S3}/README.md'),
        ],
    ),
    dict(
        id='S4', titulo='Orquestación y CI/CD con GitHub Actions', horas='4 h', carpeta=S4, estado=SOLO_README, esperados=TODOS,
        resumen='Workflows y disparadores, secretos y autenticación con GCP sin claves, pruebas, registro del modelo, imagen y despliegue con aprobación.',
        enlaces=[instructor('README de S4', f'{S4}/README.md')],
    ),
    dict(
        id='S5', titulo='MLOps y operación', horas='4 h', carpeta=S5, estado=SOLO_README, esperados=TODOS,
        resumen='Versionado con alias de MLflow, deriva, monitoreo, registros y alertas, seguridad, rollback y costes. Tarea: repositorio, informe y demostración.',
        enlaces=[instructor('README de S5', f'{S5}/README.md')],
    ),
]

LEYENDA = ('«Material preparado» significa que el material existe, no que esté probado en Windows ni en el proyector: '
           'eso se detalla en ESTADO-DEL-PAQUETE.md y en 03-Entorno/VALIDACION.md.')
