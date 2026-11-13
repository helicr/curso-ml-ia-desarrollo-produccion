# Subida a Google Classroom: organización propuesta

Estado (11/11/2026): **propuesta local, sin subir nada.** No se ha visto lo que la institución definió en Classroom (el acceso automático fue rechazado por Google); adaptar los nombres de tema y de tarea cuando se vea.
Solo se suben los materiales **del alumno**. Los del instructor (guiones, README de instructor y plan docente) se quedan fuera.

## Estructura sugerida
Un **tema** por sesión. Dentro: materiales (PDF) y, en S1, la tarea con su rúbrica. Orden de lectura = orden de la lista.

### Tema «S0 · Presentación y entorno»
| Tipo | Título en Classroom | Archivo |
|---|---|---|
| Material | S0 · Presentación principal | `pdfs/S0-Presentacion-y-Entorno/01-presentaciones/01-presentacion-principal.pdf` |
| Material | S0 · Tu equipo listo para S1 (copiar y pegar) | `pdfs/S0-Presentacion-y-Entorno/01-presentaciones/02-tu-equipo-listo-para-s1.pdf` |
| Material | S0 · Guía rápida del entorno | `pdfs/S0-Presentacion-y-Entorno/02-alumno/01-guia-rapida-del-entorno.pdf` |
| Material | S0 · Checklist de diagnóstico | `pdfs/S0-Presentacion-y-Entorno/02-alumno/02-checklist.pdf` |
| Material | S0 · Requisitos del entorno | `pdfs/S0-Presentacion-y-Entorno/02-alumno/03-requisitos-del-entorno.pdf` |
| Material | S0 · Preparación paso a paso | `pdfs/S0-Presentacion-y-Entorno/02-alumno/04-preparacion-paso-a-paso.pdf` |
| Tarea (sin entrega o con confirmación) | S0 · Completa la preparación y lee el caso de Bank Marketing | texto: ver «Descripciones» |

### Tema «S1 · De los datos al modelo»
| Tipo | Título en Classroom | Archivo |
|---|---|---|
| Material | S1 · Presentación | `pdfs/S1-Datos-y-Entrenamiento/01-presentaciones/01-presentacion-s1.pdf` |
| Material | S1 · Teoría y glosario | `pdfs/S1-Datos-y-Entrenamiento/02-alumno/01-teoria-y-glosario.pdf` |
| Material | S1 · Guía del laboratorio | `pdfs/S1-Datos-y-Entrenamiento/02-alumno/02-guia-de-laboratorio.pdf` |
| Material | S1 · Proyecto base | `pdfs/S1-Datos-y-Entrenamiento/02-alumno/07-proyecto-base.pdf` |
| Material | S1 · Checklist | `pdfs/S1-Datos-y-Entrenamiento/02-alumno/06-checklist.pdf` |
| Tarea | S1 · Adapta una variable y decide | `.../02-alumno/03-tarea.pdf` + rúbrica `.../04-rubrica.pdf` + plantilla `.../05-plantilla-de-la-decision.pdf` |
| Tarea | Avance en S2 · Bank Marketing (caso propio) | `02-Proyecto-Transversal/enunciado/README.md` (no está en PDF todavía) |

### Temas S2 a S5
Sin materiales todavía (solo README). Crear los temas vacíos para fijar el orden.

## Descripciones sugeridas
- **S0 · tarea:** «Completa el diagnóstico de 12 comprobaciones, comunica los bloqueos con el comando y la salida, y lee el enunciado del caso de Bank Marketing (`02-Proyecto-Transversal/enunciado/README.md`) y `bank-additional-names.txt`. Comprueba la huella del archivo. No adelantes el entrenamiento.»
- **S1 · tarea:** «Añade una variable nueva a la capa FS (Online Retail II), reconstruye ML, reentrena, compara dos ejecuciones en MLflow y decide con evidencia si se queda. Entrega la decisión escrita, la comparación y la traducción a `.py`. Rúbrica: 20 % reproducibilidad, 40 % técnica, 40 % análisis y decisión.»
- **Avance en S2:** «Sobre Bank Marketing: capas RAW → MASTER → FS → ML, entrenamiento y métricas, como cuadernos. No uses `duration`; no reordenes las filas.»

## Antes de subir
1. Validar lo de `validar-antes-de-subir.md`.
2. Subir desde la cuenta de Classroom del curso, a mano o con un script propio (la API de Classroom necesita su propio permiso OAuth y un cliente creado por el titular de la cuenta).
3. No subir datos ni contraseñas: los CSV están en el repositorio y se clonan; no hace falta adjuntarlos.
