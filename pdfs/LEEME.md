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

Los enlaces entre archivos del repositorio apuntan a la rama `main` en GitHub.

## S0 · Presentación y entorno (2 h)

### Presentaciones

| PDF | Contenido | Páginas | Tamaño |
|---|---|---|---|
| [`01-presentacion-principal.pdf`](S0-Presentacion-y-Entorno/01-presentaciones/01-presentacion-principal.pdf) | Presentación principal de S0 | 31 | 5.6 MB |
| [`02-tu-equipo-listo-para-s1.pdf`](S0-Presentacion-y-Entorno/01-presentaciones/02-tu-equipo-listo-para-s1.pdf) | Tu equipo listo para S1 | 27 | 2.3 MB |

### Material del alumno

| PDF | Contenido | Páginas | Tamaño |
|---|---|---|---|
| [`01-guia-rapida-del-entorno.pdf`](S0-Presentacion-y-Entorno/02-alumno/01-guia-rapida-del-entorno.pdf) | Guía rápida del entorno (S0 → S1) | 13 | 371 KB |
| [`02-checklist.pdf`](S0-Presentacion-y-Entorno/02-alumno/02-checklist.pdf) | Checklist de 12 comprobaciones | 1 | 81 KB |
| [`03-requisitos-del-entorno.pdf`](S0-Presentacion-y-Entorno/02-alumno/03-requisitos-del-entorno.pdf) | Requisitos del entorno | 1 | 80 KB |
| [`04-preparacion-paso-a-paso.pdf`](S0-Presentacion-y-Entorno/02-alumno/04-preparacion-paso-a-paso.pdf) | Preparación paso a paso (Windows) | 2 | 102 KB |

### Material del instructor

| PDF | Contenido | Páginas | Tamaño |
|---|---|---|---|
| [`01-readme-s0.pdf`](S0-Presentacion-y-Entorno/03-instructor/01-readme-s0.pdf) | README de S0 | 1 | 79 KB |
| [`02-guion-s0.pdf`](S0-Presentacion-y-Entorno/03-instructor/02-guion-s0.pdf) | Guion con tiempos de S0 | 3 | 114 KB |
| [`03-plan-docente.pdf`](S0-Presentacion-y-Entorno/03-instructor/03-plan-docente.pdf) | Plan docente (una página) | 1 | 31 KB |


## S1 · Datos y entrenamiento (4 h)

### Presentaciones

| PDF | Contenido | Páginas | Tamaño |
|---|---|---|---|
| [`01-presentacion-s1.pdf`](S1-Datos-y-Entrenamiento/01-presentaciones/01-presentacion-s1.pdf) | Presentación de S1 | 20 | 3.1 MB |
| [`02-tu-caso-de-s1-a-s5.pdf`](S1-Datos-y-Entrenamiento/01-presentaciones/02-tu-caso-de-s1-a-s5.pdf) | Tu caso de S1 a S5 (Bank Marketing) | 12 | 987 KB |

### Material del alumno

| PDF | Contenido | Páginas | Tamaño |
|---|---|---|---|
| [`01-teoria-y-glosario.pdf`](S1-Datos-y-Entrenamiento/02-alumno/01-teoria-y-glosario.pdf) | Teoría y glosario de S1 | 2 | 91 KB |
| [`02-guia-de-laboratorio.pdf`](S1-Datos-y-Entrenamiento/02-alumno/02-guia-de-laboratorio.pdf) | Guía de laboratorio de S1 | 3 | 183 KB |
| [`03-tarea.pdf`](S1-Datos-y-Entrenamiento/02-alumno/03-tarea.pdf) | Tarea de S1 | 2 | 127 KB |
| [`04-rubrica.pdf`](S1-Datos-y-Entrenamiento/02-alumno/04-rubrica.pdf) | Rúbrica de S1 | 1 | 55 KB |
| [`05-plantilla-de-la-decision.pdf`](S1-Datos-y-Entrenamiento/02-alumno/05-plantilla-de-la-decision.pdf) | Plantilla de la decisión (evidencia) | 2 | 67 KB |
| [`06-checklist.pdf`](S1-Datos-y-Entrenamiento/02-alumno/06-checklist.pdf) | Checklist de S1 | 1 | 85 KB |
| [`07-proyecto-base.pdf`](S1-Datos-y-Entrenamiento/02-alumno/07-proyecto-base.pdf) | Proyecto base (Online Retail II) | 4 | 340 KB |
| [`08-tu-caso-bank-marketing.pdf`](S1-Datos-y-Entrenamiento/02-alumno/08-tu-caso-bank-marketing.pdf) | Tu caso: Bank Marketing | 6 | 255 KB |
| [`09-plantilla-de-avance.pdf`](S1-Datos-y-Entrenamiento/02-alumno/09-plantilla-de-avance.pdf) | Plantilla de cada avance del caso propio | 3 | 106 KB |
| [`10-rubrica-de-avance.pdf`](S1-Datos-y-Entrenamiento/02-alumno/10-rubrica-de-avance.pdf) | Rúbrica de cada avance del caso propio | 2 | 100 KB |

### Material del instructor

| PDF | Contenido | Páginas | Tamaño |
|---|---|---|---|
| [`01-readme-s1.pdf`](S1-Datos-y-Entrenamiento/03-instructor/01-readme-s1.pdf) | README de S1 | 2 | 149 KB |
| [`02-guion-s1.pdf`](S1-Datos-y-Entrenamiento/03-instructor/02-guion-s1.pdf) | Guion de S1 | 3 | 129 KB |


## S2 · API y Docker (4 h)

### Presentaciones

| PDF | Contenido | Páginas | Tamaño |
|---|---|---|---|
| [`01-presentacion-s2.pdf`](S2-API-y-Docker/01-presentaciones/01-presentacion-s2.pdf) | Presentación de S2 | 21 | 3.4 MB |
| [`02-guia-de-codespaces.pdf`](S2-API-y-Docker/01-presentaciones/02-guia-de-codespaces.pdf) | Codespaces: tu laboratorio de Docker en la nube | 38 | 5.3 MB |
| [`03-contenedores-el-modelo-mental.pdf`](S2-API-y-Docker/01-presentaciones/03-contenedores-el-modelo-mental.pdf) | Contenedores: el modelo mental | 16 | 1.7 MB |
| [`04-del-dockerfile-a-produccion.pdf`](S2-API-y-Docker/01-presentaciones/04-del-dockerfile-a-produccion.pdf) | Contenedores: del Dockerfile a producción | 17 | 1.7 MB |

### Material del alumno

| PDF | Contenido | Páginas | Tamaño |
|---|---|---|---|
| [`01-teoria-y-glosario.pdf`](S2-API-y-Docker/02-alumno/01-teoria-y-glosario.pdf) | Teoría y glosario de S2 | 3 | 159 KB |
| [`02-guia-de-laboratorio.pdf`](S2-API-y-Docker/02-alumno/02-guia-de-laboratorio.pdf) | Guía de laboratorio de S2 | 6 | 255 KB |
| [`03-tarea.pdf`](S2-API-y-Docker/02-alumno/03-tarea.pdf) | Tarea de S2 | 2 | 125 KB |
| [`04-rubrica.pdf`](S2-API-y-Docker/02-alumno/04-rubrica.pdf) | Rúbrica de S2 | 2 | 71 KB |
| [`05-plantilla-de-la-evidencia.pdf`](S2-API-y-Docker/02-alumno/05-plantilla-de-la-evidencia.pdf) | Plantilla de la evidencia (API y contenedor) | 2 | 83 KB |
| [`06-checklist.pdf`](S2-API-y-Docker/02-alumno/06-checklist.pdf) | Checklist de S2 | 2 | 100 KB |
| [`07-la-api-y-el-contenedor.pdf`](S2-API-y-Docker/02-alumno/07-la-api-y-el-contenedor.pdf) | La API y el contenedor (proyecto base) | 5 | 243 KB |
| [`08-guia-practica-de-contenedores.pdf`](S2-API-y-Docker/02-alumno/08-guia-practica-de-contenedores.pdf) | Contenedores: guía práctica con nueve ejemplos | 23 | 576 KB |
| [`09-laboratorio-romper-a-proposito.pdf`](S2-API-y-Docker/02-alumno/09-laboratorio-romper-a-proposito.pdf) | Contenedores: laboratorio «romperlo a propósito» | 7 | 224 KB |
| [`10-laboratorio-extra-de-punta-a-punta.pdf`](S2-API-y-Docker/02-alumno/10-laboratorio-extra-de-punta-a-punta.pdf) | Laboratorio extra: de la ingesta a la explotación | 6 | 262 KB |

### Material del instructor

| PDF | Contenido | Páginas | Tamaño |
|---|---|---|---|
| [`01-readme-s2.pdf`](S2-API-y-Docker/03-instructor/01-readme-s2.pdf) | README de S2 | 3 | 148 KB |
| [`02-guion-s2.pdf`](S2-API-y-Docker/03-instructor/02-guion-s2.pdf) | Guion de S2 | 3 | 136 KB |
