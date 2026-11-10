# PDF del curso

PDF de las sesiones S0, S1 y S2 de «ML e IA: de desarrollo a producción». Los exige la institución. Se generan desde las fuentes (presentaciones HTML y documentos Markdown): **no los edites a mano**, cambia la fuente y vuelve a generar.

## Cómo se regeneran

```text
pip install playwright pypdf pygments     # y tener Google Chrome y pandoc
python 00-Planificacion/pdfs/generar_pdfs.py             # todos
python 00-Planificacion/pdfs/generar_pdfs.py --sesion S1 # una sesión
python 00-Planificacion/pdfs/generar_pdfs.py --comprobar # revisa los PDF existentes
```

El contenido de esta carpeta sale de `00-Planificacion/pdfs/contenido_pdfs.py`.

## Qué se pierde en las presentaciones

Se pierden las animaciones, los botones, los contadores en vivo y las notas del orador. Cada diapositiva sale con todos sus pasos ya revelados y los valores finales de los contadores.
Las interactivas (encuesta, simuladores, cronómetro) quedan como una imagen fija de su estado final. Para eso, y para las notas del orador, usa la presentación HTML.

Los enlaces entre archivos del repositorio apuntan a la rama `develop` en GitHub.

## S0 · Presentación y entorno (2 h)

### Presentaciones

| PDF | Contenido | Páginas | Tamaño |
|---|---|---|---|
| [`01-presentacion-principal.pdf`](S0-Presentacion-y-Entorno/01-presentaciones/01-presentacion-principal.pdf) | Presentación principal de S0 | 29 | 6.3 MB |
| [`02-tu-equipo-listo-para-s1.pdf`](S0-Presentacion-y-Entorno/01-presentaciones/02-tu-equipo-listo-para-s1.pdf) | Tu equipo listo para S1 | 27 | 3.0 MB |

### Material del alumno

| PDF | Contenido | Páginas | Tamaño |
|---|---|---|---|
| [`01-guia-rapida-del-entorno.pdf`](S0-Presentacion-y-Entorno/02-alumno/01-guia-rapida-del-entorno.pdf) | Guía rápida del entorno (S0 → S1) | 13 | 410 KB |
| [`02-checklist.pdf`](S0-Presentacion-y-Entorno/02-alumno/02-checklist.pdf) | Checklist de 12 comprobaciones | 1 | 100 KB |
| [`03-requisitos-del-entorno.pdf`](S0-Presentacion-y-Entorno/02-alumno/03-requisitos-del-entorno.pdf) | Requisitos del entorno | 1 | 104 KB |
| [`04-preparacion-paso-a-paso.pdf`](S0-Presentacion-y-Entorno/02-alumno/04-preparacion-paso-a-paso.pdf) | Preparación paso a paso (Windows) | 2 | 132 KB |

### Material del instructor

| PDF | Contenido | Páginas | Tamaño |
|---|---|---|---|
| [`01-readme-s0.pdf`](S0-Presentacion-y-Entorno/03-instructor/01-readme-s0.pdf) | README de S0 | 1 | 100 KB |
| [`02-guion-s0.pdf`](S0-Presentacion-y-Entorno/03-instructor/02-guion-s0.pdf) | Guion con tiempos de S0 | 3 | 133 KB |
| [`03-plan-docente.pdf`](S0-Presentacion-y-Entorno/03-instructor/03-plan-docente.pdf) | Plan docente (una página) | 1 | 59 KB |


## S1 · Datos y entrenamiento (4 h)

### Presentaciones

| PDF | Contenido | Páginas | Tamaño |
|---|---|---|---|
| [`01-presentacion-s1.pdf`](S1-Datos-y-Entrenamiento/01-presentaciones/01-presentacion-s1.pdf) | Presentación de S1 | 20 | 3.6 MB |

### Material del alumno

| PDF | Contenido | Páginas | Tamaño |
|---|---|---|---|
| [`01-teoria-y-glosario.pdf`](S1-Datos-y-Entrenamiento/02-alumno/01-teoria-y-glosario.pdf) | Teoría y glosario de S1 | 2 | 126 KB |
| [`02-guia-de-laboratorio.pdf`](S1-Datos-y-Entrenamiento/02-alumno/02-guia-de-laboratorio.pdf) | Guía de laboratorio de S1 | 3 | 167 KB |
| [`03-tarea.pdf`](S1-Datos-y-Entrenamiento/02-alumno/03-tarea.pdf) | Tarea de S1 | 2 | 140 KB |
| [`04-rubrica.pdf`](S1-Datos-y-Entrenamiento/02-alumno/04-rubrica.pdf) | Rúbrica de S1 | 1 | 93 KB |
| [`05-plantilla-de-la-decision.pdf`](S1-Datos-y-Entrenamiento/02-alumno/05-plantilla-de-la-decision.pdf) | Plantilla de la decisión (evidencia) | 2 | 99 KB |
| [`06-checklist.pdf`](S1-Datos-y-Entrenamiento/02-alumno/06-checklist.pdf) | Checklist de S1 | 1 | 97 KB |
| [`07-proyecto-base.pdf`](S1-Datos-y-Entrenamiento/02-alumno/07-proyecto-base.pdf) | Proyecto base (Online Retail II) | 3 | 164 KB |

### Material del instructor

| PDF | Contenido | Páginas | Tamaño |
|---|---|---|---|
| [`01-readme-s1.pdf`](S1-Datos-y-Entrenamiento/03-instructor/01-readme-s1.pdf) | README de S1 | 2 | 156 KB |
| [`02-guion-s1.pdf`](S1-Datos-y-Entrenamiento/03-instructor/02-guion-s1.pdf) | Guion de S1 | 2 | 135 KB |


## S2 · API y Docker (4 h)

### Presentaciones

| PDF | Contenido | Páginas | Tamaño |
|---|---|---|---|
| [`01-presentacion-s2.pdf`](S2-API-y-Docker/01-presentaciones/01-presentacion-s2.pdf) | Presentación de S2 | 21 | 4.0 MB |

### Material del alumno

| PDF | Contenido | Páginas | Tamaño |
|---|---|---|---|
| [`01-teoria-y-glosario.pdf`](S2-API-y-Docker/02-alumno/01-teoria-y-glosario.pdf) | Teoría y glosario de S2 | 3 | 196 KB |
| [`02-guia-de-laboratorio.pdf`](S2-API-y-Docker/02-alumno/02-guia-de-laboratorio.pdf) | Guía de laboratorio de S2 | 6 | 296 KB |
| [`03-tarea.pdf`](S2-API-y-Docker/02-alumno/03-tarea.pdf) | Tarea de S2 | 2 | 155 KB |
| [`04-rubrica.pdf`](S2-API-y-Docker/02-alumno/04-rubrica.pdf) | Rúbrica de S2 | 2 | 106 KB |
| [`05-plantilla-de-la-evidencia.pdf`](S2-API-y-Docker/02-alumno/05-plantilla-de-la-evidencia.pdf) | Plantilla de la evidencia (API y contenedor) | 2 | 117 KB |
| [`06-checklist.pdf`](S2-API-y-Docker/02-alumno/06-checklist.pdf) | Checklist de S2 | 1 | 123 KB |
| [`07-la-api-y-el-contenedor.pdf`](S2-API-y-Docker/02-alumno/07-la-api-y-el-contenedor.pdf) | La API y el contenedor (proyecto base) | 6 | 271 KB |

### Material del instructor

| PDF | Contenido | Páginas | Tamaño |
|---|---|---|---|
| [`01-readme-s2.pdf`](S2-API-y-Docker/03-instructor/01-readme-s2.pdf) | README de S2 | 2 | 169 KB |
| [`02-guion-s2.pdf`](S2-API-y-Docker/03-instructor/02-guion-s2.pdf) | Guion de S2 | 3 | 160 KB |
