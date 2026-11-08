# Decisiones y pendientes

## Acordado
- Proyecto transversal desde S1 con avances en la siguiente sesión.
- Scripts y notebooks base para ejecutar y adaptar, no programar todo desde cero.
- Capas: raw → master → fs → ml → entrenamiento → artefactos.
- SQLite local; prefijos master_, fs_, ml_. Originales conservados.
- FS didáctica, no plataforma completa de feature store.
- ML clásico end-to-end como núcleo obligatorio.
- Preparación de entorno obligatoria en Parte B de S0, no en anexos.
- Estadísticas y costes ampliados en consulta opcional.
- No depender de GPU ni asumir disponibilidad en la prueba cloud.

## Ajustes del 08/11/2026
- **Alcance:** IA generativa y relacionado pasa a **opcional**: red neuronal, LLM abierto, RAG,
  LLMOps/IAOps/AgentOps. MCP y agentes siguen fuera del curso.
- **Docker y Kubernetes sin instalación local:** se trabajan en Codespaces (docker, kind, kubectl).
  Docker Desktop local es opcional. GKE no es requisito (ver `03-Entorno/guias/docker-y-kubernetes-sin-instalacion-local.md`).
- **Orquestación con GitHub Actions** como hilo didáctico: primer workflow en S2 (construir imagen),
  pipeline completo en S5 (pruebas, construcción, publicación y despliegue).
- **S0:** Parte A 25 min, pausa 15, Parte B 70, cierre 10 (las slides son la referencia).

## Pendiente
1. Seleccionar y licenciar dataset y caso definitivo.
2. Fijar calendario y fechas; resolver incoherencias del sílabo original.
3. Elegir versiones y probar instalaciones por sistema operativo (local: Git, VS Code, Miniconda, SQLite, gcloud).
4. Implementar scripts, entornos, notebooks, API, workflows y pruebas.
5. **Decidir qué se hace con S4 y con la parte neuronal de S3**, ahora opcionales. Propuesta:
   S4 pasa a «Orquestación y CI/CD con GitHub Actions» (núcleo) y el LLM queda como sesión extra opcional.
6. Crear y validar el Codespace del curso (docker, kind, kubectl); revisar cuota gratuita vigente.
7. Definir autenticación de GitHub Actions con GCP (Workload Identity Federation, sin claves en el repo).
8. Validar cloud, accesos, costes y limpieza.
9. **Fusionar `develop` en `main` antes de S0**: hoy `main` está vacía y las slides indican clonar el repo.
10. Revisar visualmente el HTML en navegador antes de impartir (revisadas S0 en Chromium sin errores).
11. Rúbrica y formato de la evaluación final (`08-Evaluacion-Final` está vacío).
12. Estructura duplicada: `05-Modulo-Redes-Neuronales` y `06-Modulo-LLMs` en la raíz vs carpetas de S3/S4.

## Evaluación propuesta
Conservar 20 % conocimiento, 40 % desempeño y 40 % producto por unidad,
sujeto a validación institucional. Los avances alimentan las evidencias acumulativas.
