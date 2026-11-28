# PDF del curso

PDF de las sesiones S0 a S5 de «ML e IA: de desarrollo a producción». Los exige la institución. Se generan desde las fuentes (presentaciones HTML y documentos Markdown): **no los edites a mano**, cambia la fuente y vuelve a generar.

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
| [`03-tarea.pdf`](S1-Datos-y-Entrenamiento/02-alumno/03-tarea.pdf) | Tarea de S1 | 2 | 132 KB |
| [`04-rubrica.pdf`](S1-Datos-y-Entrenamiento/02-alumno/04-rubrica.pdf) | Rúbrica de S1 | 1 | 55 KB |
| [`05-plantilla-de-la-decision.pdf`](S1-Datos-y-Entrenamiento/02-alumno/05-plantilla-de-la-decision.pdf) | Plantilla de la decisión (evidencia) | 2 | 67 KB |
| [`06-checklist.pdf`](S1-Datos-y-Entrenamiento/02-alumno/06-checklist.pdf) | Checklist de S1 | 1 | 85 KB |
| [`07-proyecto-base.pdf`](S1-Datos-y-Entrenamiento/02-alumno/07-proyecto-base.pdf) | Proyecto base (Online Retail II) | 5 | 349 KB |
| [`08-tu-caso-bank-marketing.pdf`](S1-Datos-y-Entrenamiento/02-alumno/08-tu-caso-bank-marketing.pdf) | Tu caso: Bank Marketing | 6 | 255 KB |
| [`09-plantilla-de-avance.pdf`](S1-Datos-y-Entrenamiento/02-alumno/09-plantilla-de-avance.pdf) | Plantilla de cada avance del caso propio | 3 | 128 KB |
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
| [`01-presentacion-s2.pdf`](S2-API-y-Docker/01-presentaciones/01-presentacion-s2.pdf) | Presentación de S2 | 22 | 3.7 MB |
| [`02-guia-de-codespaces.pdf`](S2-API-y-Docker/01-presentaciones/02-guia-de-codespaces.pdf) | Codespaces: tu laboratorio de Docker en la nube | 38 | 5.3 MB |
| [`03-contenedores-el-modelo-mental.pdf`](S2-API-y-Docker/01-presentaciones/03-contenedores-el-modelo-mental.pdf) | Contenedores: el modelo mental | 16 | 1.7 MB |
| [`04-del-dockerfile-a-produccion.pdf`](S2-API-y-Docker/01-presentaciones/04-del-dockerfile-a-produccion.pdf) | Contenedores: del Dockerfile a producción | 17 | 1.7 MB |
| [`05-del-ordenador-al-servicio.pdf`](S2-API-y-Docker/01-presentaciones/05-del-ordenador-al-servicio.pdf) | Del ordenador al servicio | 36 | 9.2 MB |

### Material del alumno

| PDF | Contenido | Páginas | Tamaño |
|---|---|---|---|
| [`01-teoria-y-glosario.pdf`](S2-API-y-Docker/02-alumno/01-teoria-y-glosario.pdf) | Teoría y glosario de S2 | 3 | 159 KB |
| [`02-guia-de-laboratorio.pdf`](S2-API-y-Docker/02-alumno/02-guia-de-laboratorio.pdf) | Guía de laboratorio de S2 | 6 | 262 KB |
| [`03-tarea.pdf`](S2-API-y-Docker/02-alumno/03-tarea.pdf) | Tarea de S2 | 2 | 125 KB |
| [`04-rubrica.pdf`](S2-API-y-Docker/02-alumno/04-rubrica.pdf) | Rúbrica de S2 | 2 | 71 KB |
| [`05-plantilla-de-la-evidencia.pdf`](S2-API-y-Docker/02-alumno/05-plantilla-de-la-evidencia.pdf) | Plantilla de la evidencia (API y contenedor) | 2 | 83 KB |
| [`06-checklist.pdf`](S2-API-y-Docker/02-alumno/06-checklist.pdf) | Checklist de S2 | 2 | 107 KB |
| [`07-la-api-y-el-contenedor.pdf`](S2-API-y-Docker/02-alumno/07-la-api-y-el-contenedor.pdf) | La API y el contenedor (proyecto base) | 6 | 263 KB |
| [`08-guia-practica-de-contenedores.pdf`](S2-API-y-Docker/02-alumno/08-guia-practica-de-contenedores.pdf) | Contenedores: guía práctica con nueve ejemplos | 23 | 577 KB |
| [`09-laboratorio-romper-a-proposito.pdf`](S2-API-y-Docker/02-alumno/09-laboratorio-romper-a-proposito.pdf) | Contenedores: laboratorio «romperlo a propósito» | 7 | 224 KB |
| [`10-laboratorio-extra-de-punta-a-punta.pdf`](S2-API-y-Docker/02-alumno/10-laboratorio-extra-de-punta-a-punta.pdf) | Laboratorio extra: de la ingesta a la explotación | 6 | 262 KB |

### Material del instructor

| PDF | Contenido | Páginas | Tamaño |
|---|---|---|---|
| [`01-readme-s2.pdf`](S2-API-y-Docker/03-instructor/01-readme-s2.pdf) | README de S2 | 3 | 154 KB |
| [`02-guion-s2.pdf`](S2-API-y-Docker/03-instructor/02-guion-s2.pdf) | Guion de S2 | 3 | 171 KB |


## S3 · Laboratorios: el servicio de S2, MLflow, GitHub Actions y una red neuronal (4 h)

### Presentaciones

| PDF | Contenido | Páginas | Tamaño |
|---|---|---|---|
| [`01-laboratorio-recap-de-s2.pdf`](S3-Despliegue-y-Redes-Neuronales/01-presentaciones/01-laboratorio-recap-de-s2.pdf) | Laboratorio-recap de S2: el servicio | 20 | 7.2 MB |
| [`02-laboratorio-de-mlflow.pdf`](S3-Despliegue-y-Redes-Neuronales/01-presentaciones/02-laboratorio-de-mlflow.pdf) | Laboratorio de MLflow | 17 | 3.9 MB |
| [`03-laboratorio-de-github-actions.pdf`](S3-Despliegue-y-Redes-Neuronales/01-presentaciones/03-laboratorio-de-github-actions.pdf) | Laboratorio de GitHub Actions | 21 | 6.3 MB |
| [`04-laboratorio-de-red-neuronal.pdf`](S3-Despliegue-y-Redes-Neuronales/01-presentaciones/04-laboratorio-de-red-neuronal.pdf) | Laboratorio de red neuronal: ¿perro o gato? | 12 | 1.7 MB |

### Material del alumno

| PDF | Contenido | Páginas | Tamaño |
|---|---|---|---|
| [`01-guia-recap-de-s2.pdf`](S3-Despliegue-y-Redes-Neuronales/02-alumno/01-guia-recap-de-s2.pdf) | Guía del laboratorio-recap de S2 | 9 | 282 KB |
| [`02-guia-de-mlflow.pdf`](S3-Despliegue-y-Redes-Neuronales/02-alumno/02-guia-de-mlflow.pdf) | Guía del laboratorio de MLflow | 6 | 279 KB |
| [`03-guia-de-github-actions.pdf`](S3-Despliegue-y-Redes-Neuronales/02-alumno/03-guia-de-github-actions.pdf) | Guía del laboratorio de GitHub Actions | 6 | 268 KB |
| [`04-guia-de-red-neuronal.pdf`](S3-Despliegue-y-Redes-Neuronales/02-alumno/04-guia-de-red-neuronal.pdf) | Guía del laboratorio de red neuronal | 6 | 1.1 MB |
| [`05-activa-google-cloud-para-s4.pdf`](S3-Despliegue-y-Redes-Neuronales/02-alumno/05-activa-google-cloud-para-s4.pdf) | Activa Google Cloud para S4 | 2 | 108 KB |
| [`06-tarea.pdf`](S3-Despliegue-y-Redes-Neuronales/02-alumno/06-tarea.pdf) | Tarea de S3 (avance 3) | 3 | 124 KB |
| [`07-rubrica.pdf`](S3-Despliegue-y-Redes-Neuronales/02-alumno/07-rubrica.pdf) | Rúbrica de S3 | 2 | 90 KB |
| [`08-plantilla-de-la-evidencia.pdf`](S3-Despliegue-y-Redes-Neuronales/02-alumno/08-plantilla-de-la-evidencia.pdf) | Plantilla de la evidencia del avance 3 | 2 | 100 KB |
| [`09-checklist.pdf`](S3-Despliegue-y-Redes-Neuronales/02-alumno/09-checklist.pdf) | Checklist de S3 | 2 | 117 KB |

### Material del instructor

| PDF | Contenido | Páginas | Tamaño |
|---|---|---|---|
| [`01-readme-s3.pdf`](S3-Despliegue-y-Redes-Neuronales/03-instructor/01-readme-s3.pdf) | README de S3 | 3 | 134 KB |
| [`02-guion-s3.pdf`](S3-Despliegue-y-Redes-Neuronales/03-instructor/02-guion-s3.pdf) | Guion de S3 | 3 | 141 KB |


## S4 · Orquestación y CI/CD con GitHub Actions (4 h)

### Presentaciones

| PDF | Contenido | Páginas | Tamaño |
|---|---|---|---|
| [`01-clase-de-on-premise-a-la-nube.pdf`](S4-Orquestacion-y-CI-CD/01-presentaciones/01-clase-de-on-premise-a-la-nube.pdf) | Clase: de on-premise a la nube | 29 | 3.1 MB |
| [`02-laboratorio-de-produccion-e2e.pdf`](S4-Orquestacion-y-CI-CD/01-presentaciones/02-laboratorio-de-produccion-e2e.pdf) | Laboratorio de producción de punta a punta | 26 | 9.3 MB |
| [`03-laboratorio-cloud-journey.pdf`](S4-Orquestacion-y-CI-CD/01-presentaciones/03-laboratorio-cloud-journey.pdf) | Laboratorio Cloud Journey: la API en Google Cloud sin claves | 29 | 8.7 MB |
| [`04-practicas-en-google-cloud.pdf`](S4-Orquestacion-y-CI-CD/01-presentaciones/04-practicas-en-google-cloud.pdf) | Prácticas en Google Cloud, paso a paso | 27 | 8.2 MB |

### Material del alumno

| PDF | Contenido | Páginas | Tamaño |
|---|---|---|---|
| [`01-teoria.pdf`](S4-Orquestacion-y-CI-CD/02-alumno/01-teoria.pdf) | Teoría de S4 | 7 | 318 KB |
| [`02-hoja-de-ruta-de-laboratorios.pdf`](S4-Orquestacion-y-CI-CD/02-alumno/02-hoja-de-ruta-de-laboratorios.pdf) | Hoja de ruta de los laboratorios de S4 | 4 | 153 KB |
| [`03-clase-de-la-nube-en-texto.pdf`](S4-Orquestacion-y-CI-CD/02-alumno/03-clase-de-la-nube-en-texto.pdf) | Clase de on-premise a la nube (texto) | 21 | 305 KB |
| [`04-guia-de-produccion-e2e.pdf`](S4-Orquestacion-y-CI-CD/02-alumno/04-guia-de-produccion-e2e.pdf) | Guía del laboratorio de producción e2e | 16 | 6.8 MB |
| [`05-configurar-el-repositorio.pdf`](S4-Orquestacion-y-CI-CD/02-alumno/05-configurar-el-repositorio.pdf) | Configurar el repositorio (environment y permisos) | 5 | 1.3 MB |
| [`06-guia-de-cloud-journey.pdf`](S4-Orquestacion-y-CI-CD/02-alumno/06-guia-de-cloud-journey.pdf) | Guía del laboratorio Cloud Journey | 15 | 5.8 MB |
| [`07-configurar-google-cloud.pdf`](S4-Orquestacion-y-CI-CD/02-alumno/07-configurar-google-cloud.pdf) | Configurar Google Cloud para Cloud Journey | 3 | 180 KB |
| [`08-practicas-en-google-cloud-texto.pdf`](S4-Orquestacion-y-CI-CD/02-alumno/08-practicas-en-google-cloud-texto.pdf) | Prácticas en Google Cloud (crear, probar, borrar) | 3 | 165 KB |
| [`09-tarea.pdf`](S4-Orquestacion-y-CI-CD/02-alumno/09-tarea.pdf) | Tarea de S4 (avance 4) | 3 | 131 KB |
| [`10-rubrica.pdf`](S4-Orquestacion-y-CI-CD/02-alumno/10-rubrica.pdf) | Rúbrica de S4 | 3 | 111 KB |
| [`11-plantilla-de-la-evidencia.pdf`](S4-Orquestacion-y-CI-CD/02-alumno/11-plantilla-de-la-evidencia.pdf) | Plantilla de la evidencia del avance 4 | 3 | 122 KB |
| [`12-checklist.pdf`](S4-Orquestacion-y-CI-CD/02-alumno/12-checklist.pdf) | Checklist de S4 | 3 | 145 KB |

### Material del instructor

| PDF | Contenido | Páginas | Tamaño |
|---|---|---|---|
| [`01-readme-s4.pdf`](S4-Orquestacion-y-CI-CD/03-instructor/01-readme-s4.pdf) | README de S4 | 2 | 110 KB |
| [`02-guion-s4.pdf`](S4-Orquestacion-y-CI-CD/03-instructor/02-guion-s4.pdf) | Guion de S4 | 3 | 161 KB |
| [`03-guion-de-ensayo-del-profesor.pdf`](S4-Orquestacion-y-CI-CD/03-instructor/03-guion-de-ensayo-del-profesor.pdf) | Guion de ensayo del profesor (recrear S4) | 6 | 284 KB |


## S5 · MLOps y operación (4 h)

### Presentaciones

| PDF | Contenido | Páginas | Tamaño |
|---|---|---|---|
| [`01-teoria-de-s5.pdf`](S5-MLOps-y-Operacion/01-presentaciones/01-teoria-de-s5.pdf) | Teoría de S5: operar el modelo y el agente | 26 | 2.8 MB |
| [`02-laboratorio-mlops-clasico.pdf`](S5-MLOps-y-Operacion/01-presentaciones/02-laboratorio-mlops-clasico.pdf) | Laboratorio A: MLOps clásico | 27 | 4.9 MB |
| [`03-laboratorio-de-agentes.pdf`](S5-MLOps-y-Operacion/01-presentaciones/03-laboratorio-de-agentes.pdf) | Laboratorio B: agentes | 29 | 7.6 MB |
| [`04-clase-fundamentos-de-ia-y-agentes.pdf`](S5-MLOps-y-Operacion/01-presentaciones/04-clase-fundamentos-de-ia-y-agentes.pdf) | Clase de cierre: fundamentos de IA, LLM, RAG y agentes | 41 | 8.1 MB |
| [`05-recap-final-del-curso.pdf`](S5-MLOps-y-Operacion/01-presentaciones/05-recap-final-del-curso.pdf) | Recap final del curso | 48 | 10.4 MB |

### Material del alumno

| PDF | Contenido | Páginas | Tamaño |
|---|---|---|---|
| [`01-teoria.pdf`](S5-MLOps-y-Operacion/02-alumno/01-teoria.pdf) | Teoría de S5 | 8 | 219 KB |
| [`02-hoja-de-ruta-de-laboratorios.pdf`](S5-MLOps-y-Operacion/02-alumno/02-hoja-de-ruta-de-laboratorios.pdf) | Hoja de ruta de los laboratorios de S5 | 4 | 168 KB |
| [`03-guia-de-mlops-clasico.pdf`](S5-MLOps-y-Operacion/02-alumno/03-guia-de-mlops-clasico.pdf) | Guía del laboratorio de MLOps clásico | 12 | 416 KB |
| [`04-guia-de-agentes.pdf`](S5-MLOps-y-Operacion/02-alumno/04-guia-de-agentes.pdf) | Guía del laboratorio de agentes | 17 | 528 KB |
| [`05-configurar-el-repositorio.pdf`](S5-MLOps-y-Operacion/02-alumno/05-configurar-el-repositorio.pdf) | Configurar el repositorio para los workflows del agente | 2 | 154 KB |
| [`06-glosario.pdf`](S5-MLOps-y-Operacion/02-alumno/06-glosario.pdf) | Glosario de IA, LLM, RAG y agentes | 7 | 131 KB |
| [`07-tarea.pdf`](S5-MLOps-y-Operacion/02-alumno/07-tarea.pdf) | Tarea de S5 (avance 5) | 4 | 139 KB |
| [`08-rubrica.pdf`](S5-MLOps-y-Operacion/02-alumno/08-rubrica.pdf) | Rúbrica de S5 | 3 | 100 KB |
| [`09-plantilla-de-la-evidencia.pdf`](S5-MLOps-y-Operacion/02-alumno/09-plantilla-de-la-evidencia.pdf) | Plantilla de la evidencia del avance 5 | 3 | 114 KB |
| [`10-checklist.pdf`](S5-MLOps-y-Operacion/02-alumno/10-checklist.pdf) | Checklist de S5 | 3 | 157 KB |

### Material del instructor

| PDF | Contenido | Páginas | Tamaño |
|---|---|---|---|
| [`01-readme-s5.pdf`](S5-MLOps-y-Operacion/03-instructor/01-readme-s5.pdf) | README de S5 | 2 | 85 KB |
| [`02-guion-s5.pdf`](S5-MLOps-y-Operacion/03-instructor/02-guion-s5.pdf) | Guion de S5 | 4 | 151 KB |
| [`03-guion-de-la-jornada.pdf`](S5-MLOps-y-Operacion/03-instructor/03-guion-de-la-jornada.pdf) | Guion de la jornada del 27/11 | 6 | 313 KB |
