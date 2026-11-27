# S3 · Laboratorios: el servicio de S2, MLflow, GitHub Actions y una red neuronal (4 horas) · GCP en vivo pasa a S4

Viernes 20 de noviembre, de 10:00 a 14:00 (hora de Perú).

> **Cambio de plan (20/11/2026).** La S3 ya **no** es «migración a GCP en vivo»: la migración y el despliegue en GCP **pasan a S4** (miércoles 25 de noviembre). Hoy se repasa S2 con un laboratorio, se hace un laboratorio de GitHub Actions y GCP se explica de palabra para que cada persona llegue a S4 con su cuenta preparada. La planificación de [`00-Planificacion/s3/`](../../00-Planificacion/s3/PLANIFICACION-S3.md) era el **plan previo** (migración en vivo): se conserva como referencia para S4. El nombre de la carpeta («Despliegue y redes neuronales») también es del plan anterior.

## Objetivo
Al terminar, la persona asistente puede:
1. Recorrer de nuevo el camino de S2: la interfaz de consulta llama a la API, la API sirve el modelo y las variables de FS que faltan se calculan al vuelo con la misma lógica que al entrenar.
2. Leer un workflow de GitHub Actions que ejecuta pruebas, provocar un rojo con una prueba, leer el registro y devolverlo al verde con un arreglo (no borrando la prueba).
3. Saber qué preparar en Google Cloud antes de S4 (proyecto desechable, presupuesto con alertas antes de nada, nada creado todavía, `gcloud` en el Codespace) y que la ruta sin facturación es válida.

## Agenda (240 min)

| Hora (Perú) | Min | Bloque | Material |
|---|---|---|---|
| 10:00–10:10 | 10 | Bienvenida y plan del día | [`guion.md`](guion.md) |
| 10:10–11:20 | 70 | 1 · Laboratorio-recap de S2 (el servicio): interfaz, inferencia con la API y cálculo al vuelo de las variables de FS | [`laboratorio-recap-s2/index.html`](laboratorio-recap-s2/index.html) · [`laboratorio-recap-s2/guia.md`](laboratorio-recap-s2/guia.md) |
| 11:20–11:55 | 35 | 2 · Laboratorio de MLflow (de dónde sale el modelo): runs, comparación, firma y versiones del registro | [`laboratorio-mlflow/index.html`](laboratorio-mlflow/index.html) · [`laboratorio-mlflow/guia.md`](laboratorio-mlflow/guia.md) |
| 11:55–12:10 | 15 | Pausa | — |
| 12:10–13:20 | 70 | 3 · Laboratorio de GitHub Actions: romper y arreglar un workflow de pruebas en la rama `lab/actions-s3` de tu *fork* | [`laboratorio-github-actions/index.html`](laboratorio-github-actions/index.html) · [`laboratorio-github-actions/guia.md`](laboratorio-github-actions/guia.md) · [`laboratorio-github-actions/pruebas-proyecto.yml`](laboratorio-github-actions/pruebas-proyecto.yml) |
| 13:20–13:40 | 20 | 4 · Extra: red neuronal, ¿perro o gato? (con capturas; replicarlo es autoestudio) | [`laboratorio-red-neuronal/index.html`](laboratorio-red-neuronal/index.html) · [`laboratorio-red-neuronal/guia.md`](laboratorio-red-neuronal/guia.md) |
| 13:40–14:00 | 20 | GCP de palabra (Google Cloud activado para S4), tarea (avance 3) y cierre | [`preparar-gcp-para-s4.md`](preparar-gcp-para-s4.md) · [`tarea/README.md`](tarea/README.md) · [`tarea/rubrica.md`](tarea/rubrica.md) |

## Qué hay en esta carpeta, en el orden en que se usa
1. [`checklist.md`](checklist.md): comprobaciones del docente y del alumnado (antes, durante y después).
2. [`guion.md`](guion.md): guion del docente por bloques, con «si algo falla en directo».
3. [`laboratorio-recap-s2/`](laboratorio-recap-s2/index.html): laboratorio de repaso de S2 (`index.html` y `guia.md`).
4. [`laboratorio-github-actions/`](laboratorio-github-actions/index.html): laboratorio de GitHub Actions (`index.html`, `guia.md` y el workflow `pruebas-proyecto.yml`).
5. [`laboratorio-mlflow/`](laboratorio-mlflow/index.html): laboratorio de MLflow, 45 min (`index.html` y `guia.md`): la base del proyecto, la interfaz en el puerto 5000, runs y métricas, comparar modelos, la firma, versiones del modelo registrado y cargarlo desde Python. Capturas reales del Codespace (20/11/2026).
6. [`laboratorio-red-neuronal/`](laboratorio-red-neuronal/index.html): laboratorio de red neuronal, 30 min (`index.html`, `guia.md`, `red_gato_perro.py`): ¿perro o gato? con transferencia (MobileNetV3-small congelada + regresión logística), registro en MLflow y predicción de una foto. Instalación y datos capturados en el Codespace; entrenar, MLflow y predecir, en local (el Codespace se detuvo durante el entrenamiento).
7. [`preparar-gcp-para-s4.md`](preparar-gcp-para-s4.md): hoja corta para activar Google Cloud (lo único obligatorio del avance 3) y, si quieres, adelantar el proyecto para S4 sin crear recursos.
8. [`tarea/README.md`](tarea/README.md) y [`tarea/rubrica.md`](tarea/rubrica.md): tarea = **avance 3** del caso propio y su rúbrica (20/40/40). Entrega: **miércoles 25 de noviembre a las 10:00** (hora de Perú), con el formulario de Google del curso.
9. [`evidencias/plantilla-avance-3.md`](evidencias/plantilla-avance-3.md): plantilla de la evidencia del avance 3.
10. `tarea/pruebas/`: pruebas que comprueban la coherencia de la tarea, la rúbrica, la evidencia y el guion (pesos 20/40/40, fecha de entrega en miércoles, 240 min). Ejecutar: `python -m pytest 01-Sesiones/S3-Despliegue-y-Redes-Neuronales/tarea/pruebas -q`.

## Material del plan previo (se reutiliza en S4)
- `practica/guia-laboratorio.md` y `practica/ensayo-local/`: guía de la migración y salidas reales del ensayo local de la migración (sin GCP).
- `teoria/README.md` y `slides/`: borradores de teoría y presentación de la migración.
- `index.html`: índice de la sesión, generado con `00-Planificacion/indices-de-sesion/generar_indices.py` (regenerado el 27/11/2026 con el contenido actual).
- Guía de referencia: [`03-Entorno/guias/migracion-on-premise-a-gcp.md`](../../03-Entorno/guias/migracion-on-premise-a-gcp.md).

## Qué está validado y qué no
- **Validado:** las pruebas de coherencia de `tarea/pruebas/` (pesos, fechas, minutos y enlaces).
- **Sin verificar en el curso:** todo lo de GCP (órdenes de `gcloud`, pantallas de la consola, comportamiento de los presupuestos y alertas, precios, créditos y cuotas). La guía del SDK es un borrador.
- Los dos laboratorios tienen su propio estado de validación en su carpeta.
