# Tareas · Puesta en producción de punta a punta

Plan: [`PLANIFICACION.md`](PLANIFICACION.md). Estado: **22/11/2026, decisiones tomadas** (D4: laboratorio de cierre de S4 en `01-Sesiones/S4-Orquestacion-y-CI-CD/laboratorio-produccion-e2e/`; D5: lote diario; D1–D3 por la recomendación). Tareas en marcha desde P01/P02.
**Modelo:** **Haiku** para lo mecánico (pruebas estáticas, índices, comprobaciones, checklist); **Sonnet** para diseño, código, workflows, interfaz y guías; **Opus** coordina, revisa y ejecuta lo que toca GitHub (push a ramas `lab/`, seguimiento de runs) con la orden del instructor.
**Prioridad:** P1 imprescindible · P2 deseable · P3 opcional.

| # | Tarea | Entregables | Prueba de aceptación | Depende | Modelo | Prior. |
|---|---|---|---|---|---|---|
| P00 | Decisiones D1–D5 | Respuestas anotadas | — | — | instructor | P1 |
| P01 | Inventario de lo que existe | Nota corta: qué hace hoy `explotacion`, la API, la interfaz, `comparar`, los workflows del curso y `nueva-version.yml` del taller; qué falta | Cada afirmación con su archivo | — | Haiku | P1 |
| P02 | `models/referencia.json` y su lectura | Esquema (versión, huella de datos, métricas de test, fecha, etiqueta de imagen), función que la lee y la compara; versión 1 creada con el modelo actual | Pruebas: lee, valida esquema, compara con tolerancia | P00 | Sonnet | P1 |
| P03 | Modo 1 · `puntuar-lote.yml` | Workflow `schedule` + `workflow_dispatch`: datos → puntuar con la imagen de producción → resumen → artefacto campaña | Prueba estática (disparadores, permisos, `needs:`, artefactos); run real en verde | P02 | Sonnet | P1 |
| P04 | Modo 2 · bajo demanda | `GET /bajo-demanda/{id}`: variables **leídas** de `fs_cliente_corte` (último corte) → `/predecir`; latencia p50/p95 | Pruebas del endpoint (cliente presente/ausente); latencias medidas | P02 | Sonnet | P1 |
| P05 | Modo 3 · online (features al vuelo) | `GET /online/{id}` con corte = instante de la petición; `POST /demo/compra` sobre copia de la base; pruebas de **paridad** (mismo corte → misma probabilidad en lote, bajo demanda y online), **frescura** (tras una compra, online cambia; los otros no) y **sin fuga**; latencia de punta a punta | Las tres pruebas en verde; latencias medidas | P02 | Sonnet | P1 |
| P06 | **Panel de producción** | Ampliar la interfaz: pestañas Lote · Bajo demanda · En línea · Versiones; endpoints que necesite; sin librerías externas | Pruebas de endpoints; revisión visual con capturas | P02 P03 | Sonnet | P1 |
| P07 | **`nueva-version.yml`** | Adaptar el del taller al caso Retail: entrenar → comparar con `referencia.json` → construir y probar → comparar predicciones campeón/candidato → aprobar (`environment: produccion`) → publicar en GHCR → PR de `referencia.json` | Prueba estática; los tres escenarios (P08) | P02 [D1 D2] | Sonnet | P1 |
| P08 | **Ensayo real de los escenarios** | Runs reales: (a) sin datos nuevos; (b) versión peor → rechazada; (c) aceptable → aprobada, publicada, PR; (d) rollback; enlaces, tiempos y capturas | Los cuatro con su run y su resultado esperado | P03 P07 + config. P09 | Opus + instructor | P1 |
| P09 | Configuración del repositorio | Guía con capturas: *environment* `produccion` con revisores, permiso de PR para Actions, visibilidad de GHCR | Hecho por el instructor; comprobado en P08 | P07 | Haiku (guía) + instructor | P1 |
| P10 | Compose de demo | `compose.yaml` (API de producción + interfaz con panel) que descarga la imagen de GHCR; órdenes para Codespace | Arranca en Codespace o en Actions; `/listo` en verde | P06 [D1] | Sonnet | P1 |
| P11 | Guía y diapositivas | Guía paso a paso y presentación (marco de los laboratorios de S3: ⧉, capturas reales): los tres modos, el panel, la versión nueva, el rollback | Cada orden existe; cada cifra de un run o medida | P08 P10 | Sonnet | P1 |
| P12 | Pruebas de los workflows | Pruebas estáticas de `puntuar-lote.yml` y `nueva-version.yml` (como `test_workflow.py` del extra de S4) | En verde | P03 P07 | Haiku | P1 |
| P13 | Revisión didáctica y comprobaciones | Lectura como alumno; rutas, correos, tokens; tamaños; índice de la sesión | Sin hallazgos | P11 | Sonnet + Haiku | P1 |
| P14 | Subida | Commit y push a `develop` con la orden del instructor | — | todo | Opus | P1 |

## Orden y paralelismo
1. P00 (instructor) y P01 (Haiku) a la vez.
2. P02 (Sonnet) → en paralelo P03, P05, P07 (tres agentes Sonnet) y P04 (P2).
3. P06 (Sonnet) cuando P03 deje una campaña; P10 (Sonnet) tras P06.
4. P09 (instructor) → P08 (Opus + instructor): los cuatro escenarios con runs reales.
5. P11 (Sonnet) y P12 (Haiku) → P13 → P14.

## Brief común para los agentes
Repo `C:\bk\HC-Cursos\curso-ml-ia-desarrollo-produccion`, `develop`; sin commit ni push (lo hace Opus con la orden del instructor); crear/editar con Write/Edit; no inventar cifras; sin secretos propios ni rutas personales; tono de los laboratorios de S3; probar en local antes de entregar y decir qué no se pudo probar.
