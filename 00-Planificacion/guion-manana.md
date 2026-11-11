# Guion de mañana: S0 + S1 (6 horas)

S0 (120 min) y S1 (240 min), seguidas. Detalle minuto a minuto en `01-Sesiones/S0-Presentacion-y-Entorno/guion.md` y `01-Sesiones/S1-Datos-y-Entrenamiento/guion.md`.

## Rutas
- Presentación S0: `01-Sesiones/S0-Presentacion-y-Entorno/slides/index.html`
- Equipo listo para S1 (copiar y pegar): `01-Sesiones/S0-Presentacion-y-Entorno/slides/instalacion/index.html`
- Presentación S1: `01-Sesiones/S1-Datos-y-Entrenamiento/slides/index.html`
- PDF: `pdfs/S0-Presentacion-y-Entorno/` y `pdfs/S1-Datos-y-Entrenamiento/`
- Enunciado del caso de los alumnos: `02-Proyecto-Transversal/enunciado/README.md`

## Línea de tiempo (minutos acumulados)
| Min | Bloque |
|---|---|
| 0–25 | S0 · Parte A (diapositivas 1–11) |
| 25–40 | S0 · Pausa (diapositiva 12) |
| 40–110 | S0 · Parte B, entorno (diapositivas 13–27) |
| 110–120 | S0 · Cierre (diapositivas 28–31) |
| 120–… | Descanso entre sesiones, a criterio del profesor (no entra en el cómputo) |
| +0–30 | S1 · Revisión de entorno (diapositivas 1–3) |
| +30–90 | S1 · Teoría (diapositivas 4–16) |
| +90–225 | S1 · Práctica, cuatro cuadernos con pausa de 10 min (diapositiva 17) |
| +225–240 | S1 · Entrega y cierre (diapositivas 18–20) |

## S0 · qué explicar primero
- **Parte A (1–11):** empieza por la 2 (pregunta de arranque, 3 min), la 3 (núcleo obligatorio frente a opcional) y la 4 (del notebook al servicio). Sigue con la 7 (capas raw → ml), la 9 (método) y la 10 (cadena de entregas).
- **Pausa (12):** 15 min.
- **Parte B (13–27):** la 15 y la 16 explican qué software se usa en cada sesión y para qué. Después, los pasos con comandos (19–25) y el diagnóstico (27, 10 min).
- **Cierre (28–31):** las diapositivas 28 y 29 presentan cada caso (qué se hará, qué hay en el archivo y dónde está el CSV); las 30 y 31 cierran la sesión. Revela los dos casos. El del instructor es Online Retail II y se trabaja en S1. El de los alumnos es Bank Marketing. Encarga leer el enunciado y `bank-additional-names.txt`, y comprobar la huella del archivo.
- Las que más pesan: la 10 y la 28.
- Si vas justo de tiempo: resume en una frase la 5 (estadísticas) y la 8 (equivalencias con GCP).

## S1 · qué explicar primero
- **Revisión (1–3):** cada alumno ejecuta la prueba de humo y `pytest`; esperado `34 passed`. S0 ya hizo el diagnóstico, así que se puede reducir a 10–15 min. Quien no pase: Codespaces o pareja, sin detener la sesión.
- **Teoría (4–16):** no saltes la 10 (regla de oro de FS, 8 min), la 13 (partición temporal frente a aleatoria), la 14 (sobreajuste) ni la 15 (MLflow). Si hay que recortar, quita la 11 y la 16.
- **Práctica (17):** `01-Sesiones/S1-Datos-y-Entrenamiento/practica/guia-laboratorio.md`. Ritmo: 10 preparar · 30 cuaderno 01 · 25 cuaderno 02 · 10 pausa · 25 cuaderno 03 · 25 cuaderno 04 · 10 `.py` y pruebas.
- **Cierre (18–20):** recuerda los dos entregables: (1) la tarea de la variable nueva, sobre Online Retail II; (2) el avance en S2 sobre Bank Marketing (RAW → MASTER → FS → ML, entrenamiento y métricas, en cuadernos). `duration` se excluye y las filas de `bank-additional-full.csv` no se reordenan.

## Antes de mañana
- `main` sigue vacía: las diapositivas y guías usan `git clone --branch develop`.
- El Codespace del curso no está publicado: las diapositivas 23, 25 y 27 de S0 lo marcan como pendiente.
- Las cifras y tarifas externas no están reverificadas.
- Nada se ha probado en Windows real (scripts de instalación y entorno).
- Probar las presentaciones en la plataforma de la clase (Google Meet) y en otros navegadores.
- Enviar a los alumnos la guía de instalación para Windows (`03-Entorno/guia-instalacion/index.html`) antes de S0.
