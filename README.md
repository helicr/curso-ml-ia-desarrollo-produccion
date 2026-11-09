# ML e IA: de desarrollo a producción

Instructor: Helí Campos R  
BigData, Analytics & AI Architect.

Objetivo: llevar un modelo de ML clásico desde el dato hasta un servicio que otra persona
pueda usar, documentar y operar. IA generativa (red neuronal, LLM, RAG, agentes) es opcional.

## Contenido del paquete
- Programa S0–S5: 22 horas síncronas propuestas.
- S0: presentación HTML, guion, preparación y checklist de 12 comprobaciones; diapositivas y guía rápida para dejar el equipo listo para S1.
- S1: presentación HTML, teoría, laboratorio, tarea con rúbrica y proyecto base con pruebas.
- `pdfs/`: versión en PDF de las presentaciones y los documentos de S0 y S1 (una diapositiva por página; ver `pdfs/LEEME.md`).
- Caso transversal y entregas.
- Estructura del proyecto con SQLite.
- Guías de entorno: Docker y Kubernetes en Codespaces, pipelines con GitHub Actions.
- Referencias y decisiones de alcance.

## Por dónde empezar
Cada sesión tiene su propio índice: abre `01-Sesiones/Sx-.../index.html` en un navegador (la primera, `01-Sesiones/S0-Presentacion-y-Entorno/index.html`).
Enlaza las presentaciones y los documentos de esa sesión y dice qué le falta; cada presentación lleva un enlace «⌂ Índice» para volver.
La presentación de S0 distingue Parte A, Parte B obligatoria y Consulta opcional.

## Estado
S0 y S1 están implementadas y validadas en Linux (entorno `env-ia-mlops`, datos del caso, cuadernos y pruebas); nada se ha probado en Windows real.
S2–S5 solo tienen README. APIs, workflows, Codespace del curso y laboratorios de S2 a S5 están pendientes de desarrollo y prueba, así que no es un curso completamente implementado.
Trabajo en la rama `develop`; `main` está vacía hasta fusionar. Ver `00-Planificacion/decisiones-y-pendientes.md`.
