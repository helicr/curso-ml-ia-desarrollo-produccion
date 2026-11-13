# Guion S0 (120 min)

**Presentación:** `01-Sesiones/S0-Presentacion-y-Entorno/slides/index.html`  
**Equipo listo para S1 (copiar y pegar):** `01-Sesiones/S0-Presentacion-y-Entorno/slides/instalacion/index.html`

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
| 14 | Dónde corre cada pieza: equipo, Codespaces, Actions, GCP | 3 |
| 15 | **Software por sesión: qué y para qué.** Matriz herramienta × sesión; clic en una fila: para qué sirve, qué se hace con ella en cada sesión y si ya hay guía de uso | 3 |
| 16 | **Qué se estrena en cada sesión y qué debe estar listo antes.** Clic en S0–S5 | 2 |
| 17 | Herramientas: el kit base de hoy (filtros: equipo / Codespaces / nube) | 3 |
| 18 | **Una guía de uso por herramienta:** instalar, aprender lo mínimo, comprobar; qué guías hay y cuáles llegan después | 1 |
| 19 | Clonar y abrir | 5 |
| 20 | Miniconda: comprobar y crear el entorno `env-ia-mlops` desde `environment.yml` | 7 |
| 21 | VS Code y notebooks (mismo intérprete en script y notebook) | 6 |
| 22 | SQLite: comprobar ejecución | 6 |
| 23 | Docker en Codespaces | 8 |
| 24 | Google Cloud: autenticar, no gastar | 7 |
| 25 | Codespaces: docker, kind, kubectl | 6 |
| 26 | Ruta opcional red neuronal / LLM | 1 |
| 27 | Diagnóstico interactivo (12 comprobaciones; informe de incidencias) | 10 |

Las slides 15, 16 y 18 se añadieron el 09/11/2026 para explicar **qué software se necesita en cada sesión y para qué** antes de pasar a los
pasos de instalación y comprobación. Para hacer sitio se recortó la Parte B sin cambiar su total (70 min): Dónde corre cada pieza 4 → 3,
Herramientas 7 → 3 y Ruta opcional 2 → 1. Los pasos con comandos (19–25) conservan sus tiempos.
La slide 26 es opcional: dedicarle 1 min (hasta 2 si sobra tiempo). El diagnóstico se guarda en el navegador de cada participante.
Los datos de las slides 15 y 16 están en el propio `index.html` (constantes `SOFT` y `SW_SES`); las marcas siguen `00-Planificacion/programa.md` y son orientativas.

## Cierre · 10 min
| Slide | Tema | Min |
|---|---|---|
| 28 | **Caso 1 · Online Retail II**, el que desarrollamos: qué haremos, qué hay en el archivo y dónde está (`04-Proyecto-Base/data/raw/muestra_online_retail_ii.csv`) | 3 |
| 29 | **Caso 2 · Bank Marketing**, el de la tarea: qué harán, qué hay en el archivo y dónde está (`02-Proyecto-Transversal/datos/bank-marketing/bank-additional-full.csv`) | 3 |
| 30 | Antes de S1: completar el diagnóstico, comunicar bloqueos, leer el caso de Bank Marketing (enunciado en `02-Proyecto-Transversal/`), no improvisar el entorno | 3 |
| 31 | Nos vemos en S1 | 1 |

## Consulta (fuera del cómputo)
`slides/anexos/index.html`: anexos A–F (estadísticas, herramientas, calculadora de coste de Cloud Run y fuentes), solo de consulta.
No se presentan en clase ni suman a las dos horas; la sesión se imparte con `slides/index.html`.

## Teclas
→ / espacio: avanzar (revela pasos) · ←: retroceder · O: índice · S: notas del ponente · F: pantalla completa · Inicio / Fin.

## Antes de impartir
- Fusionar `develop` en `main` (hoy `main` está casi vacía). Mientras tanto, la slide 19, la guía interactiva y la guía rápida ya indican `git clone --branch develop`; tras fusionar bastará `git clone` a secas.
- `environment.yml` ya está publicado (probado en Linux; en Windows, sin probar) y las slides 20 y 27 lo reflejan. El Codespace del curso ya está escrito (`.devcontainer/`, con `verificar.sh`) y las slides 23, 25 y 27 lo reflejan, pero **no se ha probado en un Codespace real**: ejecuta antes el workflow «Validar Codespace del curso» (Actions) o ábrelo una vez.
- Revisar precios y cifras externas (sección de fuentes).
- Enviar la guía interactiva `03-Entorno/guia-instalacion/index.html` (solo Windows) antes de S0, para que la Parte B sea de comprobación y no de instalación.
- Material de copiar y pegar para dejar el equipo listo para S1 (instalación en orden, creación del entorno, pruebas y verificador): `slides/instalacion/index.html` y `practica/guia-rapida-entorno-s0-s1.md`. Es el soporte para quien no llegue con el entorno hecho; la slide 20 de la presentación principal remite a él.
- Probar `instalar_entorno.ps1` en un equipo Windows limpio: no se ha probado.
