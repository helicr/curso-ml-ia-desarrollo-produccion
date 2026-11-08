# Docker, Kubernetes y pipelines sin instalar nada en local

Estado: propuesta de diseño del 08/11/2026. Ninguna de estas piezas está implementada ni probada todavía.
Las cuotas y precios cambian: verificarlos antes de impartir.

## Idea
Todo lo que necesita Docker o Kubernetes se hace en la nube, y el portátil solo edita y ejecuta Python.

| Necesidad | Dónde se hace | Instalación local |
|---|---|---|
| Construir y ejecutar imágenes (S2) | Codespace del curso (Docker) | Ninguna |
| Laboratorio de Kubernetes (S3) | Codespace con `kind` y `kubectl` | Ninguna |
| Orquestar el pipeline, construir y publicar imagen (S2, S4) | GitHub Actions | Ninguna |
| Desplegar el servicio (S3) | Cloud Run (no requiere Kubernetes) | `gcloud` o Cloud Shell |

## Opciones, en orden de preferencia
1. **GitHub Codespaces (recomendada).** Entorno en el navegador o VS Code, con Docker, `kind` y `kubectl`
   preconfigurados mediante `devcontainer.json`. El repo ya está en GitHub, así que es el camino natural.
   Pendiente: crear y probar el `devcontainer`, y revisar la cuota gratuita mensual vigente de horas de Codespaces.
2. **GitHub Actions.** Los runners de GitHub traen Docker. Sirve para construir la imagen, ejecutar pruebas y orquestar
   el pipeline completo sin tocar el equipo del alumno. Los repositorios públicos tienen minutos gratuitos; revisar el límite
   si el repo del alumno es privado.
3. **Google Cloud Shell (respaldo).** Terminal en el navegador con `gcloud`, `kubectl` y Docker disponibles, y un directorio
   personal persistente. Tiene cuotas de uso: verificar. Si `kind` funciona bien allí, está por probar.
4. **Cloud Build.** Construye imágenes en GCP sin Docker local: `gcloud builds submit`. Alternativa a Actions si el
   alumno ya trabaja con `gcloud`.
5. **Docker Desktop local.** Opcional; solo para quien pueda y quiera instalarlo.

## ¿Y GKE?
No es requisito. Exige facturación y genera coste. Para enseñar Kubernetes basta `kind` en Codespaces; el despliegue real
del curso va a Cloud Run. Si se quiere mostrar GKE, que sea una demo del instructor, con presupuesto y alertas.

## Orquestación de pipelines con GitHub Actions (propuesta didáctica)
Workflow en `.github/workflows/` con disparadores `push`, `pull_request` y `workflow_dispatch`:

1. Pruebas y calidad: `pytest`, lint.
2. Pipeline de datos y entrenamiento: raw → master → fs → ml → modelo, sobre un dataset pequeño.
3. Publicar métricas y artefactos como artefactos del workflow.
4. Construir la imagen Docker.
5. Publicar en Artifact Registry.
6. Desplegar en Cloud Run (con aprobación manual mediante *environments* si se desea).

Progresión sugerida: S2 construye la imagen (pasos 1 y 4); S4 completa el pipeline (2, 3, 5, 6); S5 practica versionado, deriva y rollback.
Autenticación con GCP: Workload Identity Federation, sin claves JSON ni secretos en el repositorio.

## Pendiente
- Crear y probar `.devcontainer/devcontainer.json` (Docker, kind, kubectl).
- Probar `kind` dentro de Codespaces y, como respaldo, en Cloud Shell.
- Escribir y probar el workflow base y la configuración de Workload Identity Federation.
- Verificar cuotas de Codespaces, Actions y Cloud Shell, y los costes de Cloud Run y Artifact Registry.
