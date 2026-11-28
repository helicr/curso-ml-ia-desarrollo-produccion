"""Qué PDF se generan y dónde quedan. Es la única fuente de verdad: `generar_pdfs.py` solo lo ejecuta.

Estructura de salida (carpeta `pdfs/` en la raíz del repositorio):

    pdfs/
      LEEME.md                         (lo genera el script)
      S0-Presentacion-y-Entorno/
        01-presentaciones/             una diapositiva por página, 1280 × 720 px
        02-alumno/                     documentos en A4
        03-instructor/                 documentos en A4
      S1-Datos-y-Entrenamiento/
        ...

Cada elemento:
  origen   ruta del archivo fuente, desde la raíz del repositorio
  tipo     'presentacion' (HTML con section.slide), 'pagina' (HTML normal, sin diapositivas) o 'documento' (Markdown)
  grupo    'presentaciones' | 'alumno' | 'instructor'
  titulo   título que se muestra en el PDF y en el LEEME
  archivo  nombre del PDF (minúsculas, sin acentos, con número de orden)
  nota     (opcional) lo que se pierde o conviene saber de ese PDF
  espera_ms (opcional, solo presentaciones) pausa tras cambiar de diapositiva, para que acaben las animaciones
"""

CARPETA_SALIDA = 'pdfs'

REPOSITORIO = 'https://github.com/helicr/curso-ml-ia-desarrollo-produccion'
RAMA = 'main'

CURSO = 'ML e IA: de desarrollo a producción'
INSTITUCION = 'UNTRM · INCID · FIZBAC · 2026-II'
AUTOR = 'Helí Campos R.'

GRUPOS = {
    'presentaciones': ('Presentaciones', '01-presentaciones'),
    'alumno': ('Material del alumno', '02-alumno'),
    'instructor': ('Material del instructor', '03-instructor'),
}

PERDIDO_EN_PRESENTACIONES = (
    'Se pierden las animaciones, los botones, los contadores en vivo y las notas del orador. '
    'Cada diapositiva sale con todos sus pasos ya revelados y los valores finales de los contadores.'
)

SESIONES = [
    {
        'id': 'S0',
        'carpeta': 'S0-Presentacion-y-Entorno',
        'titulo': 'Presentación y entorno',
        'horas': '2 h',
        'elementos': [
            {
                'origen': '01-Sesiones/S0-Presentacion-y-Entorno/slides/index.html',
                'tipo': 'presentacion', 'grupo': 'presentaciones',
                'titulo': 'Presentación principal de S0',
                'archivo': '01-presentacion-principal.pdf',
                'espera_ms': 2400,
                'nota': PERDIDO_EN_PRESENTACIONES,
            },
            {
                'origen': '01-Sesiones/S0-Presentacion-y-Entorno/slides/instalacion/index.html',
                'tipo': 'presentacion', 'grupo': 'presentaciones',
                'titulo': 'Tu equipo listo para S1',
                'archivo': '02-tu-equipo-listo-para-s1.pdf',
                'espera_ms': 700,
                'nota': PERDIDO_EN_PRESENTACIONES,
            },
            {
                'origen': '01-Sesiones/S0-Presentacion-y-Entorno/practica/guia-rapida-entorno-s0-s1.md',
                'tipo': 'documento', 'grupo': 'alumno',
                'titulo': 'Guía rápida del entorno (S0 → S1)',
                'archivo': '01-guia-rapida-del-entorno.pdf',
            },
            {
                'origen': '01-Sesiones/S0-Presentacion-y-Entorno/checklist.md',
                'tipo': 'documento', 'grupo': 'alumno',
                'titulo': 'Checklist de 12 comprobaciones',
                'archivo': '02-checklist.pdf',
            },
            {
                'origen': '03-Entorno/guias/requisitos.md',
                'tipo': 'documento', 'grupo': 'alumno',
                'titulo': 'Requisitos del entorno',
                'archivo': '03-requisitos-del-entorno.pdf',
            },
            {
                'origen': '03-Entorno/guias/preparacion-paso-a-paso.md',
                'tipo': 'documento', 'grupo': 'alumno',
                'titulo': 'Preparación paso a paso (Windows)',
                'archivo': '04-preparacion-paso-a-paso.pdf',
            },
            {
                'origen': '01-Sesiones/S0-Presentacion-y-Entorno/README.md',
                'tipo': 'documento', 'grupo': 'instructor',
                'titulo': 'README de S0',
                'archivo': '01-readme-s0.pdf',
            },
            {
                'origen': '01-Sesiones/S0-Presentacion-y-Entorno/guion.md',
                'tipo': 'documento', 'grupo': 'instructor',
                'titulo': 'Guion con tiempos de S0',
                'archivo': '02-guion-s0.pdf',
            },
            {
                'origen': '01-Sesiones/S0-Presentacion-y-Entorno/slides/fuentes/plan-docente.html',
                'tipo': 'pagina', 'grupo': 'instructor',
                'titulo': 'Plan docente (una página)',
                'archivo': '03-plan-docente.pdf',
            },
        ],
    },
    {
        'id': 'S1',
        'carpeta': 'S1-Datos-y-Entrenamiento',
        'titulo': 'Datos y entrenamiento',
        'horas': '4 h',
        'elementos': [
            {
                'origen': '01-Sesiones/S1-Datos-y-Entrenamiento/slides/index.html',
                'tipo': 'presentacion', 'grupo': 'presentaciones',
                'titulo': 'Presentación de S1',
                'archivo': '01-presentacion-s1.pdf',
                'espera_ms': 2400,
                'nota': PERDIDO_EN_PRESENTACIONES,
            },
            {
                'origen': '01-Sesiones/S1-Datos-y-Entrenamiento/slides/caso-propio/index.html',
                'tipo': 'presentacion', 'grupo': 'presentaciones',
                'titulo': 'Tu caso de S1 a S5 (Bank Marketing)',
                'archivo': '02-tu-caso-de-s1-a-s5.pdf',
                'espera_ms': 2400,
                'nota': PERDIDO_EN_PRESENTACIONES,
            },
            {
                'origen': '01-Sesiones/S1-Datos-y-Entrenamiento/teoria/README.md',
                'tipo': 'documento', 'grupo': 'alumno',
                'titulo': 'Teoría y glosario de S1',
                'archivo': '01-teoria-y-glosario.pdf',
            },
            {
                'origen': '01-Sesiones/S1-Datos-y-Entrenamiento/practica/guia-laboratorio.md',
                'tipo': 'documento', 'grupo': 'alumno',
                'titulo': 'Guía de laboratorio de S1',
                'archivo': '02-guia-de-laboratorio.pdf',
            },
            {
                'origen': '01-Sesiones/S1-Datos-y-Entrenamiento/tarea/README.md',
                'tipo': 'documento', 'grupo': 'alumno',
                'titulo': 'Tarea de S1',
                'archivo': '03-tarea.pdf',
            },
            {
                'origen': '01-Sesiones/S1-Datos-y-Entrenamiento/tarea/rubrica.md',
                'tipo': 'documento', 'grupo': 'alumno',
                'titulo': 'Rúbrica de S1',
                'archivo': '04-rubrica.pdf',
            },
            {
                'origen': '01-Sesiones/S1-Datos-y-Entrenamiento/evidencias/plantilla-decision.md',
                'tipo': 'documento', 'grupo': 'alumno',
                'titulo': 'Plantilla de la decisión (evidencia)',
                'archivo': '05-plantilla-de-la-decision.pdf',
            },
            {
                'origen': '01-Sesiones/S1-Datos-y-Entrenamiento/checklist.md',
                'tipo': 'documento', 'grupo': 'alumno',
                'titulo': 'Checklist de S1',
                'archivo': '06-checklist.pdf',
            },
            {
                'origen': '04-Proyecto-Base/README.md',
                'tipo': 'documento', 'grupo': 'alumno',
                'titulo': 'Proyecto base (Online Retail II)',
                'archivo': '07-proyecto-base.pdf',
            },
            {
                'origen': '02-Proyecto-Transversal/alumno/tu-caso-bank-marketing.md',
                'tipo': 'documento', 'grupo': 'alumno',
                'titulo': 'Tu caso: Bank Marketing',
                'archivo': '08-tu-caso-bank-marketing.pdf',
            },
            {
                'origen': '02-Proyecto-Transversal/alumno/plantilla-avance.md',
                'tipo': 'documento', 'grupo': 'alumno',
                'titulo': 'Plantilla de cada avance del caso propio',
                'archivo': '09-plantilla-de-avance.pdf',
            },
            {
                'origen': '02-Proyecto-Transversal/alumno/rubrica-avance.md',
                'tipo': 'documento', 'grupo': 'alumno',
                'titulo': 'Rúbrica de cada avance del caso propio',
                'archivo': '10-rubrica-de-avance.pdf',
            },
            {
                'origen': '01-Sesiones/S1-Datos-y-Entrenamiento/README.md',
                'tipo': 'documento', 'grupo': 'instructor',
                'titulo': 'README de S1',
                'archivo': '01-readme-s1.pdf',
            },
            {
                'origen': '01-Sesiones/S1-Datos-y-Entrenamiento/guion.md',
                'tipo': 'documento', 'grupo': 'instructor',
                'titulo': 'Guion de S1',
                'archivo': '02-guion-s1.pdf',
            },
        ],
    },
    {
        'id': 'S2',
        'carpeta': 'S2-API-y-Docker',
        'titulo': 'API y Docker',
        'horas': '4 h',
        'elementos': [
            {
                'origen': '01-Sesiones/S2-API-y-Docker/slides/index.html',
                'tipo': 'presentacion', 'grupo': 'presentaciones',
                'titulo': 'Presentación de S2',
                'archivo': '01-presentacion-s2.pdf',
                'espera_ms': 2400,
                'nota': PERDIDO_EN_PRESENTACIONES,
            },
            {
                'origen': '03-Entorno/guia-codespaces/index.html',
                'tipo': 'presentacion', 'grupo': 'presentaciones',
                'titulo': 'Codespaces: tu laboratorio de Docker en la nube',
                'archivo': '02-guia-de-codespaces.pdf',
                'espera_ms': 700,
                'nota': PERDIDO_EN_PRESENTACIONES + ' Los pasos se explican igual en la versión de texto, '
                        '`03-Entorno/guias/codespaces-para-el-alumnado.md`.',
            },
            {
                'origen': '01-Sesiones/S2-API-y-Docker/contenedores/modelo-mental/index.html',
                'tipo': 'presentacion', 'grupo': 'presentaciones',
                'titulo': 'Contenedores: el modelo mental',
                'archivo': '03-contenedores-el-modelo-mental.pdf',
                'espera_ms': 700,
                'nota': PERDIDO_EN_PRESENTACIONES + ' Los mismos ejemplos están en la guía práctica '
                        '(`01-Sesiones/S2-API-y-Docker/contenedores/guia-practica.md`).',
            },
            {
                'origen': '01-Sesiones/S2-API-y-Docker/contenedores/del-dockerfile-a-produccion/index.html',
                'tipo': 'presentacion', 'grupo': 'presentaciones',
                'titulo': 'Contenedores: del Dockerfile a producción',
                'archivo': '04-del-dockerfile-a-produccion.pdf',
                'espera_ms': 700,
                'nota': PERDIDO_EN_PRESENTACIONES + ' Los mismos ejemplos están en la guía práctica '
                        '(`01-Sesiones/S2-API-y-Docker/contenedores/guia-practica.md`).',
            },
            {
                'origen': '01-Sesiones/S2-API-y-Docker/del-ordenador-al-servicio/index.html',
                'tipo': 'presentacion', 'grupo': 'presentaciones',
                'titulo': 'Del ordenador al servicio',
                'archivo': '05-del-ordenador-al-servicio.pdf',
                'espera_ms': 900,
                'nota': PERDIDO_EN_PRESENTACIONES + ' Las dos diapositivas interactivas (la receta del Dockerfile y «Romper a propósito») '
                        'muestran en el PDF un solo caso; todos están en `04-Proyecto-Base/docs/del-ordenador-al-servicio.md`.',
            },
            {
                'origen': '01-Sesiones/S2-API-y-Docker/teoria/README.md',
                'tipo': 'documento', 'grupo': 'alumno',
                'titulo': 'Teoría y glosario de S2',
                'archivo': '01-teoria-y-glosario.pdf',
            },
            {
                'origen': '01-Sesiones/S2-API-y-Docker/practica/guia-laboratorio.md',
                'tipo': 'documento', 'grupo': 'alumno',
                'titulo': 'Guía de laboratorio de S2',
                'archivo': '02-guia-de-laboratorio.pdf',
            },
            {
                'origen': '01-Sesiones/S2-API-y-Docker/tarea/README.md',
                'tipo': 'documento', 'grupo': 'alumno',
                'titulo': 'Tarea de S2',
                'archivo': '03-tarea.pdf',
            },
            {
                'origen': '01-Sesiones/S2-API-y-Docker/tarea/rubrica.md',
                'tipo': 'documento', 'grupo': 'alumno',
                'titulo': 'Rúbrica de S2',
                'archivo': '04-rubrica.pdf',
            },
            {
                'origen': '01-Sesiones/S2-API-y-Docker/evidencias/plantilla-api-y-contenedor.md',
                'tipo': 'documento', 'grupo': 'alumno',
                'titulo': 'Plantilla de la evidencia (API y contenedor)',
                'archivo': '05-plantilla-de-la-evidencia.pdf',
            },
            {
                'origen': '01-Sesiones/S2-API-y-Docker/checklist.md',
                'tipo': 'documento', 'grupo': 'alumno',
                'titulo': 'Checklist de S2',
                'archivo': '06-checklist.pdf',
            },
            {
                'origen': '04-Proyecto-Base/docs/api-y-contenedor.md',
                'tipo': 'documento', 'grupo': 'alumno',
                'titulo': 'La API y el contenedor (proyecto base)',
                'archivo': '07-la-api-y-el-contenedor.pdf',
            },
            {
                'origen': '01-Sesiones/S2-API-y-Docker/contenedores/guia-practica.md',
                'tipo': 'documento', 'grupo': 'alumno',
                'titulo': 'Contenedores: guía práctica con nueve ejemplos',
                'archivo': '08-guia-practica-de-contenedores.pdf',
            },
            {
                'origen': '01-Sesiones/S2-API-y-Docker/contenedores/laboratorio-romper.md',
                'tipo': 'documento', 'grupo': 'alumno',
                'titulo': 'Contenedores: laboratorio «romperlo a propósito»',
                'archivo': '09-laboratorio-romper-a-proposito.pdf',
            },
            {
                'origen': '01-Sesiones/S2-API-y-Docker/practica/laboratorio-extra-de-punta-a-punta.md',
                'tipo': 'documento', 'grupo': 'alumno',
                'titulo': 'Laboratorio extra: de la ingesta a la explotación',
                'archivo': '10-laboratorio-extra-de-punta-a-punta.pdf',
            },
            {
                'origen': '01-Sesiones/S2-API-y-Docker/README.md',
                'tipo': 'documento', 'grupo': 'instructor',
                'titulo': 'README de S2',
                'archivo': '01-readme-s2.pdf',
            },
            {
                'origen': '01-Sesiones/S2-API-y-Docker/guion.md',
                'tipo': 'documento', 'grupo': 'instructor',
                'titulo': 'Guion de S2',
                'archivo': '02-guion-s2.pdf',
            },
        ],
    },
]


# ----------------------------------------------------------------------------------------------------------------------
# S3, S4 y S5 (añadidas el 28/11/2026). Mismo formato que S0 a S2; solo cambia que se construyen con dos ayudantes.
# ----------------------------------------------------------------------------------------------------------------------
def _pres(origen, titulo, archivo, espera_ms=700):
    return {'origen': origen, 'tipo': 'presentacion', 'grupo': 'presentaciones', 'titulo': titulo, 'archivo': archivo,
            'espera_ms': espera_ms, 'nota': PERDIDO_EN_PRESENTACIONES}


def _doc(origen, grupo, titulo, archivo):
    return {'origen': origen, 'tipo': 'documento', 'grupo': grupo, 'titulo': titulo, 'archivo': archivo}


_S3 = '01-Sesiones/S3-Despliegue-y-Redes-Neuronales/'
_S4 = '01-Sesiones/S4-Orquestacion-y-CI-CD/'
_S5 = '01-Sesiones/S5-MLOps-y-Operacion/'

SESIONES += [
    {
        'id': 'S3',
        'carpeta': 'S3-Despliegue-y-Redes-Neuronales',
        'titulo': 'Laboratorios: el servicio de S2, MLflow, GitHub Actions y una red neuronal',
        'horas': '4 h',
        'elementos': [
            _pres(_S3 + 'laboratorio-recap-s2/index.html', 'Laboratorio-recap de S2: el servicio', '01-laboratorio-recap-de-s2.pdf'),
            _pres(_S3 + 'laboratorio-mlflow/index.html', 'Laboratorio de MLflow', '02-laboratorio-de-mlflow.pdf'),
            _pres(_S3 + 'laboratorio-github-actions/index.html', 'Laboratorio de GitHub Actions', '03-laboratorio-de-github-actions.pdf'),
            _pres(_S3 + 'laboratorio-red-neuronal/index.html', 'Laboratorio de red neuronal: ¿perro o gato?', '04-laboratorio-de-red-neuronal.pdf'),
            _doc(_S3 + 'laboratorio-recap-s2/guia.md', 'alumno', 'Guía del laboratorio-recap de S2', '01-guia-recap-de-s2.pdf'),
            _doc(_S3 + 'laboratorio-mlflow/guia.md', 'alumno', 'Guía del laboratorio de MLflow', '02-guia-de-mlflow.pdf'),
            _doc(_S3 + 'laboratorio-github-actions/guia.md', 'alumno', 'Guía del laboratorio de GitHub Actions', '03-guia-de-github-actions.pdf'),
            _doc(_S3 + 'laboratorio-red-neuronal/guia.md', 'alumno', 'Guía del laboratorio de red neuronal', '04-guia-de-red-neuronal.pdf'),
            _doc(_S3 + 'preparar-gcp-para-s4.md', 'alumno', 'Activa Google Cloud para S4', '05-activa-google-cloud-para-s4.pdf'),
            _doc(_S3 + 'tarea/README.md', 'alumno', 'Tarea de S3 (avance 3)', '06-tarea.pdf'),
            _doc(_S3 + 'tarea/rubrica.md', 'alumno', 'Rúbrica de S3', '07-rubrica.pdf'),
            _doc(_S3 + 'evidencias/plantilla-avance-3.md', 'alumno', 'Plantilla de la evidencia del avance 3', '08-plantilla-de-la-evidencia.pdf'),
            _doc(_S3 + 'checklist.md', 'alumno', 'Checklist de S3', '09-checklist.pdf'),
            _doc(_S3 + 'README.md', 'instructor', 'README de S3', '01-readme-s3.pdf'),
            _doc(_S3 + 'guion.md', 'instructor', 'Guion de S3', '02-guion-s3.pdf'),
        ],
    },
    {
        'id': 'S4',
        'carpeta': 'S4-Orquestacion-y-CI-CD',
        'titulo': 'Orquestación y CI/CD con GitHub Actions',
        'horas': '4 h',
        'elementos': [
            _pres(_S4 + 'clase-onpremise-a-nube/index.html', 'Clase: de on-premise a la nube', '01-clase-de-on-premise-a-la-nube.pdf'),
            _pres(_S4 + 'laboratorio-produccion-e2e/index.html', 'Laboratorio de producción de punta a punta', '02-laboratorio-de-produccion-e2e.pdf'),
            _pres(_S4 + 'laboratorio-cloud-journey/index.html', 'Laboratorio Cloud Journey: la API en Google Cloud sin claves', '03-laboratorio-cloud-journey.pdf'),
            _pres(_S4 + 'practicas-gcp/index.html', 'Prácticas en Google Cloud, paso a paso', '04-practicas-en-google-cloud.pdf'),
            _doc(_S4 + 'teoria/README.md', 'alumno', 'Teoría de S4', '01-teoria.pdf'),
            _doc(_S4 + 'practica/guia-laboratorio.md', 'alumno', 'Hoja de ruta de los laboratorios de S4', '02-hoja-de-ruta-de-laboratorios.pdf'),
            _doc(_S4 + 'clase-onpremise-a-nube/guia.md', 'alumno', 'Clase de on-premise a la nube (texto)', '03-clase-de-la-nube-en-texto.pdf'),
            _doc(_S4 + 'laboratorio-produccion-e2e/guia.md', 'alumno', 'Guía del laboratorio de producción e2e', '04-guia-de-produccion-e2e.pdf'),
            _doc(_S4 + 'laboratorio-produccion-e2e/CONFIGURAR-REPOSITORIO.md', 'alumno', 'Configurar el repositorio (environment y permisos)', '05-configurar-el-repositorio.pdf'),
            _doc(_S4 + 'laboratorio-cloud-journey/guia.md', 'alumno', 'Guía del laboratorio Cloud Journey', '06-guia-de-cloud-journey.pdf'),
            _doc(_S4 + 'laboratorio-cloud-journey/CONFIGURAR-GCP.md', 'alumno', 'Configurar Google Cloud para Cloud Journey', '07-configurar-google-cloud.pdf'),
            _doc(_S4 + 'practicas-gcp/README.md', 'alumno', 'Prácticas en Google Cloud (crear, probar, borrar)', '08-practicas-en-google-cloud-texto.pdf'),
            _doc(_S4 + 'tarea/README.md', 'alumno', 'Tarea de S4 (avance 4)', '09-tarea.pdf'),
            _doc(_S4 + 'tarea/rubrica.md', 'alumno', 'Rúbrica de S4', '10-rubrica.pdf'),
            _doc(_S4 + 'evidencias/plantilla-avance-4.md', 'alumno', 'Plantilla de la evidencia del avance 4', '11-plantilla-de-la-evidencia.pdf'),
            _doc(_S4 + 'checklist.md', 'alumno', 'Checklist de S4', '12-checklist.pdf'),
            _doc(_S4 + 'README.md', 'instructor', 'README de S4', '01-readme-s4.pdf'),
            _doc(_S4 + 'guion.md', 'instructor', 'Guion de S4', '02-guion-s4.pdf'),
            _doc(_S4 + 'guion-ensayo-profesor.md', 'instructor', 'Guion de ensayo del profesor (recrear S4)', '03-guion-de-ensayo-del-profesor.pdf'),
        ],
    },
    {
        'id': 'S5',
        'carpeta': 'S5-MLOps-y-Operacion',
        'titulo': 'MLOps y operación',
        'horas': '4 h',
        'elementos': [
            _pres(_S5 + 'teoria/index.html', 'Teoría de S5: operar el modelo y el agente', '01-teoria-de-s5.pdf'),
            _pres(_S5 + 'laboratorio-mlops/index.html', 'Laboratorio A: MLOps clásico', '02-laboratorio-mlops-clasico.pdf'),
            _pres(_S5 + 'laboratorio-agentes/index.html', 'Laboratorio B: agentes', '03-laboratorio-de-agentes.pdf'),
            _pres(_S5 + 'clase-fundamentos-ia-agentes/index.html', 'Clase de cierre: fundamentos de IA, LLM, RAG y agentes', '04-clase-fundamentos-de-ia-y-agentes.pdf'),
            _pres('01-Sesiones/recap/recap-final/index.html', 'Recap final del curso', '05-recap-final-del-curso.pdf', espera_ms=900),
            _doc(_S5 + 'teoria/README.md', 'alumno', 'Teoría de S5', '01-teoria.pdf'),
            _doc(_S5 + 'practica/guia-laboratorio.md', 'alumno', 'Hoja de ruta de los laboratorios de S5', '02-hoja-de-ruta-de-laboratorios.pdf'),
            _doc(_S5 + 'laboratorio-mlops/guia.md', 'alumno', 'Guía del laboratorio de MLOps clásico', '03-guia-de-mlops-clasico.pdf'),
            _doc(_S5 + 'laboratorio-agentes/guia.md', 'alumno', 'Guía del laboratorio de agentes', '04-guia-de-agentes.pdf'),
            _doc(_S5 + 'laboratorio-agentes/CONFIGURAR-REPOSITORIO.md', 'alumno', 'Configurar el repositorio para los workflows del agente', '05-configurar-el-repositorio.pdf'),
            _doc(_S5 + 'clase-fundamentos-ia-agentes/glosario.md', 'alumno', 'Glosario de IA, LLM, RAG y agentes', '06-glosario.pdf'),
            _doc(_S5 + 'tarea/README.md', 'alumno', 'Tarea de S5 (avance 5)', '07-tarea.pdf'),
            _doc(_S5 + 'tarea/rubrica.md', 'alumno', 'Rúbrica de S5', '08-rubrica.pdf'),
            _doc(_S5 + 'evidencias/plantilla-avance-5.md', 'alumno', 'Plantilla de la evidencia del avance 5', '09-plantilla-de-la-evidencia.pdf'),
            _doc(_S5 + 'checklist.md', 'alumno', 'Checklist de S5', '10-checklist.pdf'),
            _doc(_S5 + 'README.md', 'instructor', 'README de S5', '01-readme-s5.pdf'),
            _doc(_S5 + 'guion.md', 'instructor', 'Guion de S5', '02-guion-s5.pdf'),
            _doc(_S5 + 'guion-jornada-27-11.md', 'instructor', 'Guion de la jornada del 27/11', '03-guion-de-la-jornada.pdf'),
        ],
    },
]
