# S4: Orquestación y CI/CD con GitHub Actions

Duración propuesta: 4 horas.

## Contenido
Workflows, jobs, steps, runners y disparadores. Secretos, variables y entornos; autenticación con GCP
sin claves en el repositorio (Workload Identity Federation). Caché, artefactos y matrices. CI frente a CD y aprobaciones.

## Práctica
Pruebas y calidad; ejecutar raw → master → fs → ml → modelo → métricas en el workflow; registrar el modelo y sus métricas en MLflow; construir y publicar la imagen
en Artifact Registry; desplegar en Cloud Run con aprobación manual; leer registros y depurar.

## Tarea
Orquestar con un workflow el pipeline del caso propio y documentar etapas y fallos encontrados.

## Evidencia
Avance en S5: workflow funcionando, historial de ejecuciones y explicación de una decisión.

## Materiales (estado a 27/11/2026)
Sesión impartida el miércoles 25 de noviembre (10:00–14:00, hora de Perú); la entrega del avance 4 vence el viernes 27 de noviembre a las 10:00. El guion y la agenda están en [`guion.md`](guion.md) (propuesta; el recorte de la parte de Google Cloud es decisión del profesor).

| Carpeta o archivo | Qué es | Estado |
|---|---|---|
| `teoria/`, `practica/`, `tarea/`, `evidencias/`, `guion.md`, `checklist.md` | Los siete documentos de la sesión (tarea = avance 4, rúbrica, plantilla de evidencia) | Escritos; los pesos de la rúbrica por decidir |
| `clase-onpremise-a-nube/` | De on-premise a la nube: 29 diapositivas y guía con fuentes | Preparada |
| `laboratorio-produccion-e2e/` | Producción de punta a punta del caso Retail: lote, panel, versión nueva con puerta de calidad y aprobación, rollback | Ensayado en GitHub Actions el 22/11/2026 |
| `laboratorio-cloud-journey/` | La API en Cloud Run desde Actions sin claves (WIF), modelo en Vertex AI y borrado | Ejecutado en la cuenta del curso el 25/11/2026 y borrado |
| `practicas-gcp/` | Cinco prácticas crear → probar → borrar (Cloud Run, GKE, Dataproc, Vertex, Gemini) | Ejecutadas y borradas el 25/11/2026 |
| `extra-estilo-llm/` | Extra: un LLM que copia el estilo de color (LoRA) orquestado en Actions | Ejecutado el 21/11/2026 |

**Dockerfiles multi-etapa (fusionado en `develop` el 27/11/2026):** el código de la imagen se clona del commit exacto (`FUENTE=git` por defecto; `REF=${GITHUB_SHA}` en Actions) y el modelo de la API entra aparte con `--build-context modelo=...`; los compose usan `FUENTE=contexto` para el desarrollo. Las pruebas locales pasan, pero **ningún `docker build` se ha ejecutado de verdad ni se ha ensayado en Actions**: el primer ensayo (empezando por `validar-dos-contenedores` en una rama `lab/...`) debe comprobar el clon por *sha*, `--secret id=git_token,env=GIT_TOKEN` y `additional_contexts` de compose. Detalle en `C:\bk\HC-Cursos\traspaso-dockerfile-clon.md` (fuera del repositorio) y en `04-Proyecto-Base/docs/api-y-contenedor.md`.
