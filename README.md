# ML e IA: de desarrollo a producción

Instructor: Helí Campos R  
BigData, Analytics & AI Architect.

Objetivo: llevar un modelo de ML clásico desde el dato hasta un servicio que otra persona
pueda usar, documentar y operar. IA generativa (red neuronal, LLM, RAG, agentes) es opcional.

## Contenido del paquete
- Programa S0–S5: 22 horas síncronas propuestas.
- S0: presentación HTML, guion, preparación y checklist de 12 comprobaciones; diapositivas y guía rápida para dejar el equipo listo para S1.
- S1: presentación HTML, teoría, laboratorio, tarea con rúbrica y proyecto base con pruebas.
- S2: presentación HTML, teoría, laboratorio, tarea con rúbrica, y en el proyecto base la API (FastAPI), el Dockerfile y un workflow de GitHub Actions.
- S3: cuatro laboratorios con diapositivas (repaso de S2, MLflow, GitHub Actions y una red neuronal), tarea (avance 3) y hoja para activar Google Cloud.
- S4: clase «De on-premise a la nube», laboratorio de producción de punta a punta, laboratorio Cloud Journey (GCP sin claves con Workload Identity Federation), cinco prácticas en Google Cloud y un extra de LLM; teoría, guion, tarea (avance 4) y rúbrica.
- S5: laboratorio de MLOps clásico (deriva, alias `champion`, alerta), laboratorio de agentes (MCP, LLM local, evaluación), clase de fundamentos de IA y agentes (sesión de cierre) y extras (dos MCP en notebooks con interfaz web, lote con Airflow/Cloud Composer, del champion de MLflow a Vertex AI); teoría, guion, tarea y rúbrica.
- Recap final del curso (`01-Sesiones/recap/recap-final/`): lo que se hizo en cada sesión y qué entregar.
- `pdfs/`: versión en PDF de las presentaciones y los documentos de S0, S1 y S2 (una diapositiva por página; ver `pdfs/LEEME.md`).
- Caso transversal y entregas.
- Estructura del proyecto con SQLite.
- Guías de entorno: Docker y Kubernetes en Codespaces, pipelines con GitHub Actions.
- Referencias y decisiones de alcance.

## Por dónde empezar
Cada sesión tiene su propio índice: abre `01-Sesiones/Sx-.../index.html` en un navegador (la primera, `01-Sesiones/S0-Presentacion-y-Entorno/index.html`).
Enlaza las presentaciones y los documentos de esa sesión y dice qué le falta; cada presentación lleva un enlace «⌂ Índice» para volver.
La presentación de S0 distingue Parte A, Parte B obligatoria y Consulta opcional.

## Estado
S0, S1 y S2 están implementadas y validadas en Linux (entorno `env-ia-mlops`, datos del caso, cuadernos y pruebas); S2 además se verificó en GitHub Actions (imagen Docker, contenedor y workflow). Nada se ha probado en Windows real.
S3, S4 y S5 tienen ya sus laboratorios, guías, diapositivas, tareas y rúbricas (cada sesión indica en su README qué se ensayó de verdad y qué sigue sin verificar). Ensayados en GitHub Actions y en la cuenta de Google Cloud del curso: los laboratorios de S3 y S4, el laboratorio de MLOps de S5 y los workflows del agente. **Sin verificar**: los extras de S5 de Airflow/Cloud Composer y de Vertex AI en entornos reales (solo con simulaciones), los notebooks MCP en un Codespace y Docker en este portátil. Los pesos de las rúbricas y la forma de la demostración final están por decidir. El contenido se amplía de forma continua con más tareas y extras.
`main` trae lo que ya puede usar el alumnado (S0, S1 y S2 con sus PDF); el trabajo en curso se hace en `develop` y se fusiona en `main` cuando está listo. Ver `00-Planificacion/decisiones-y-pendientes.md`.
