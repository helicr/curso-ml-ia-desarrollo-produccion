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
RAMA = 'main'

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
            deck('Anexos de consulta', f'{S0}/slides/anexos/index.html', 'Anexos A–F: estadísticas, herramientas, calculadora de coste de Cloud Run y fuentes. Consulta; no suman a las dos horas de S0.'),
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
        nota='El caso propio de los alumnos (Bank Marketing) empieza aquí y sigue hasta S5: ver 02-Proyecto-Transversal/alumno/tu-caso-bank-marketing.md.',
        enlaces=[
            deck('Presentación de S1', f'{S1}/slides/index.html', 'Revisión del entorno, teoría, práctica, entrega y cierre.', volver=True),
            deck('Tu caso de S1 a S5 (Bank Marketing)', f'{S1}/slides/caso-propio/index.html', 'El caso propio del alumnado: la pregunta, el dato, las trampas, la partición y los cuatro avances.', volver=True),
            alumno('Teoría y glosario', f'{S1}/teoria/README.md'),
            alumno('Guía de laboratorio', f'{S1}/practica/guia-laboratorio.md', 'Paso a paso con presupuesto de tiempo.'),
            alumno('Tarea', f'{S1}/tarea/README.md'),
            alumno('Rúbrica', f'{S1}/tarea/rubrica.md', '20 % reproducibilidad · 40 % técnica · 40 % análisis y decisión.'),
            alumno('Plantilla de la decisión', f'{S1}/evidencias/plantilla-decision.md', 'La evidencia que se entrega.'),
            alumno('Checklist', f'{S1}/checklist.md'),
            alumno('Proyecto base (Online Retail II)', '04-Proyecto-Base/README.md', 'Cuadernos, paquete ia_mlops, pruebas y Makefile.'),
            alumno('Tu caso: Bank Marketing', '02-Proyecto-Transversal/alumno/tu-caso-bank-marketing.md', 'La hoja del caso propio: pregunta, dato, cifras para comprobar tu carga, decisiones tuyas y entregas.'),
            alumno('Plantilla de cada avance', '02-Proyecto-Transversal/alumno/plantilla-avance.md', 'Lo que se entrega en cada uno de los cuatro avances del caso propio.'),
            alumno('Rúbrica de cada avance', '02-Proyecto-Transversal/alumno/rubrica-avance.md', '20 % reproducibilidad · 40 % técnica · 40 % análisis y decisión.'),
            instructor('README de S1', f'{S1}/README.md', 'Agenda por minutos y qué está validado.'),
            instructor('Guion', f'{S1}/guion.md'),
        ],
    ),
    dict(
        id='S2', titulo='API y Docker', horas='4 h', carpeta=S2, estado=PREPARADO, esperados=TODOS,
        resumen='Del modelo guardado a un servicio: API con FastAPI cuyo contrato sale de la firma del modelo, errores 422/503/500, registros JSON, imagen Docker mínima, '
                'comparación de predicciones por todos los caminos y primer workflow de GitHub Actions. Tarea: llevar el modelo propio al mismo punto.',
        nota='Probado en Linux y en GitHub Actions. Sin probar: el Codespace del curso (.devcontainer), Docker en un equipo propio y Windows. '
             'Los ejemplos de contenedores se ejecutaron con Docker real en GitHub Actions, no en un Codespace; lo que dicen de Cloud Run es solo la documentación de Google.',
        enlaces=[
            deck('Presentación de S2', f'{S2}/slides/index.html', 'Revisión del entorno, teoría, laboratorio de códigos, práctica, entrega y cierre.', volver=True),
            alumno('Teoría y glosario', f'{S2}/teoria/README.md'),
            alumno('Guía de laboratorio', f'{S2}/practica/guia-laboratorio.md', 'Paso a paso con presupuesto de tiempo y salidas esperadas.'),
            alumno('Tarea', f'{S2}/tarea/README.md'),
            alumno('Rúbrica', f'{S2}/tarea/rubrica.md', '20 % reproducibilidad · 40 % técnica · 40 % análisis y decisión.'),
            alumno('Plantilla de la evidencia', f'{S2}/evidencias/plantilla-api-y-contenedor.md', 'La evidencia que se entrega.'),
            alumno('Checklist', f'{S2}/checklist.md'),
            alumno('La API y el contenedor', '04-Proyecto-Base/docs/api-y-contenedor.md', 'Contrato, errores, registros, imagen, workflow y qué se probó.'),
            deck('Codespaces: tu laboratorio de Docker en la nube', f'{ENTORNO}/guia-codespaces/index.html',
                 'Guía en diapositivas: abrir el Codespace (navegador o VS Code), el bloque 4 paso a paso y la cuota.', volver=True),
            alumno('Guía de Codespaces (versión en texto)', f'{ENTORNO}/guias/codespaces-para-el-alumnado.md', 'El mismo contenido, para leer sin diapositivas.'),
            deck('Contenedores 1: el modelo mental', f'{S2}/contenedores/modelo-mental/index.html',
                 'Antes de S2: imagen y contenedor, ciclo de vida, lo que se pierde al borrar, puertos y volúmenes. Cuatro prácticas con salidas reales.', volver=True),
            deck('Contenedores 2: del Dockerfile a producción', f'{S2}/contenedores/del-dockerfile-a-produccion/index.html',
                 'Antes de S2: capas y caché, .dockerignore, secretos, usuario sin privilegios, healthcheck. Cinco prácticas con salidas reales.', volver=True),
            alumno('Contenedores: guía práctica con nueve ejemplos', f'{S2}/contenedores/guia-practica.md',
                   'Los mismos ejemplos de las dos presentaciones, para hacer en el Codespace (unos 60 min los seis primeros, 97 min todos; estimado).'),
            alumno('Contenedores: laboratorio «romperlo a propósito»', f'{S2}/contenedores/laboratorio-romper.md',
                   'Cinco fallos que provocas, diagnosticas y arreglas (unos 34 min; estimado).'),
            alumno('Docker y Kubernetes sin instalación local', f'{ENTORNO}/guias/docker-y-kubernetes-sin-instalacion-local.md', 'Cómo trabajar con Docker en Codespaces.'),
            instructor('README de S2', f'{S2}/README.md', 'Agenda por minutos y qué está validado.'),
            instructor('Guion', f'{S2}/guion.md'),
            instructor('Contenedores: cómo se generó y cómo regenerarlo', f'{S2}/contenedores/README.md', 'Una sola fuente de comandos, salidas reales de Docker, pruebas y comprobación de diseño.'),
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
