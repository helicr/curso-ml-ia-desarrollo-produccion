# Guion S0 (120 min)

Referencia: las diapositivas (notas del ponente con la tecla S). Tiempos tomados de la propia presentación.
Cada diapositiva muestra su tiempo previsto en el índice (tecla O) y la barra inferior indica el minuto acumulado.

## Parte A · 25 min + pausa de 15 min
| Slide | Tema | Min | Qué se mueve |
|---|---|---|---|
| 1 | Portada | 1 | |
| 2 | Pregunta de arranque (3 preguntas; clave B en la 2.ª) | 3 | Contador de respuestas por opción |
| 3 | Objetivo: núcleo obligatorio frente a opcional | 2 | Aparece paso a paso (→) |
| 4 | Del notebook al servicio (7 pasos) | 3 | Se revela con → |
| 5 | El modelo es la parte pequeña: sistema de ML, 45 % del tiempo en datos y niveles de madurez de MLOps | 2 | Contador; clic en cada nivel |
| 6 | Programa S0–S5 y tres hilos (MLflow, Actions, local → GCP) | 2 | Clic en cada sesión |
| 7 | Capas raw → master → fs → ml → … | 3 | Clic o ▶ Recorrer capas |
| 8 | De local a GCP: equivalencias y estrategia | 2 | Filas con → |
| 9 | Método ver → ejecutar → adaptar → explicar | 2 | Pasos con → y barra del ritmo |
| 10 | Cadena de entregas | 3 | Cadena con → |
| 11 | Evaluación 20/40/40 | 2 | Contadores y barra |
| 12 | **Pausa de 15 min** | 15 | Cuenta atrás; «Ir a la Parte B» |

Consejo: recorrer 1–11 (25 min) y hacer la pausa al terminar la Parte A.
No atravesar estadísticas detalladas para llegar a la instalación.

## Parte B · 70 min (obligatoria)
Cada paso: para qué, qué ejecutar, qué esperar y qué revisar si falla. En las diapositivas con comandos,
«▶ Ver demo» simula la salida esperada (ilustrativa) y «Copiar comandos» deja los comandos en el portapapeles.

| Slide | Tema | Min |
|---|---|---|
| 13 | Preparación del entorno: barra de presupuesto de tiempo (clic para saltar) | 2 |
| 14 | Dónde corre cada pieza: equipo, Codespaces, Actions, GCP | 4 |
| 15 | Herramientas (filtros: equipo / Codespaces / nube) | 7 |
| 16 | Clonar y abrir | 5 |
| 17 | Miniconda (solo comprobar; no crear entorno aún) | 7 |
| 18 | VS Code y notebooks (mismo intérprete en script y notebook) | 6 |
| 19 | SQLite: comprobar ejecución | 6 |
| 20 | Docker en Codespaces | 8 |
| 21 | Google Cloud: autenticar, no gastar | 7 |
| 22 | Codespaces: docker, kind, kubectl | 6 |
| 23 | Ruta opcional red neuronal / LLM | 2 |
| 24 | Diagnóstico interactivo (12 comprobaciones; informe de incidencias) | 10 |

La slide 23 es opcional: dedicarle 1–2 min. El diagnóstico se guarda en el navegador de cada participante.

## Cierre · 10 min
Slides 25–26: completar diagnóstico, comunicar bloqueos, leer el caso cuando se publique, no improvisar el entorno.

## Consulta (fuera del cómputo)
`slides/anexos/index.html`: material de la edición anterior; los anexos A–F (estadísticas, costes, calculadora de Cloud Run
y fuentes) siguen siendo de consulta. El resto de ese archivo está desactualizado respecto a la presentación principal.

## Teclas
→ / espacio: avanzar (revela pasos) · ←: retroceder · O: índice · S: notas del ponente · F: pantalla completa · Inicio / Fin.

## Antes de impartir
- Fusionar `develop` en `main` (hoy `main` está vacía) o indicar la rama a clonar.
- Publicar `environment.yml` y el Codespace del curso, o ajustar las slides 17, 22 y 24.
- Revisar precios y cifras externas (sección de fuentes).
- Enviar la guía interactiva `03-Entorno/guia-instalacion/index.html` (solo Windows) antes de S0, para que la Parte B sea de comprobación y no de instalación.
- Probar `instalar_entorno.ps1` en un equipo Windows limpio: no se ha probado.
