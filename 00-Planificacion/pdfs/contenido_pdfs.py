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
