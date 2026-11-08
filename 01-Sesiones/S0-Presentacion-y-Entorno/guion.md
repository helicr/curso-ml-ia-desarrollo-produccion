# Guion S0 (120 min)

Referencia: las diapositivas (notas del ponente con la tecla S). Tiempos tomados del registro de slides.

## Parte A · 25 min + pausa de 15 min
| Slide | Tema | Min |
|---|---|---|
| 1 | Portada | 1 |
| 2 | Pregunta de arranque (3 preguntas, clave B en la 2.ª) | 3 |
| 3 | Objetivo: ML clásico a producción; IA generativa opcional | 1 |
| 4 | Del notebook al servicio (7 pasos) | 3 |
| 5 | Usar IA no es escalarla (McKinsey 2026) | 3 |
| 6 | Acuerdos de alcance | 2 |
| 7 | Programa S0–S5 | 2 |
| 8 | **Pausa de 15 min** (pulsar «Iniciar pausa»; al volver, «Ir a Parte B») | 15 |
| 9 | Estructura del caso (raw → master → fs → ml) | 3 |
| 10 | Método ver → ejecutar → adaptar → explicar | 2 |
| 11 | Cadena de entregas | 3 |
| 12 | Evaluación 20/40/40 | 2 |

Consejo: recorrer 1–7 y 9–12 (25 min) y hacer la pausa al terminar la Parte A.
No atravesar estadísticas detalladas para llegar a la instalación.

## Parte B · 70 min (obligatoria)
Cada paso: para qué, qué ejecutar, qué esperar y qué revisar si falla.

| Slide | Tema | Min |
|---|---|---|
| 13 | Preparación del entorno: orden del bloque | 2 |
| 14 | Local · Codespaces · nube: dónde corre cada pieza | 4 |
| 15 | Herramientas (local: Git, VS Code, Miniconda, SQLite, gcloud) | 7 |
| 16 | Clonar y abrir | 5 |
| 17 | Miniconda (solo comprobar; no crear entorno aún) | 7 |
| 18 | VS Code y notebooks (mismo intérprete en script y notebook) | 6 |
| 19 | SQLite: comprobar ejecución | 6 |
| 20 | Docker en Codespaces | 8 |
| 21 | Google Cloud: autenticar, no gastar | 7 |
| 22 | Codespaces: docker, kind, kubectl | 6 |
| 23 | Ruta opcional red neuronal / LLM | 5 |
| 24 | Diagnóstico (12 comprobaciones) | 7 |

Sugerencia: la slide 23 es opcional; dedicarle 1–2 min y reasignar el resto a Codespaces o diagnóstico.

## Cierre · 10 min
Slides 25–26: completar diagnóstico, comunicar bloqueos, leer el caso cuando se publique, no improvisar el entorno.

## Consulta (fuera del cómputo)
Anexos A–F: estadísticas, costes, calculadora Cloud Run y fuentes. No son requisitos de instalación.

## Antes de impartir
- Fusionar `develop` en `main` (hoy `main` está vacía) o indicar la rama a clonar.
- Publicar `environment.yml` y el Codespace del curso, o ajustar las slides 17, 22 y 24.
- Revisar precios y cifras externas (sección de fuentes).
