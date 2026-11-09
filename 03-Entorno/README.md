# Entorno del curso (Windows)

| Carpeta o archivo | Para qué sirve |
|---|---|
| `guia-instalacion/index.html` | Guía interactiva: elige ruta, modo y terminal (CMD o PowerShell), copia los comandos y marca tu progreso. |
| `guia-instalacion/index.template.html` y `generar.py` | Plantilla y generador de la guía. Ejecuta `python generar.py` tras cambiar un script. |
| `scripts/instalar_entorno.cmd` | Instala con winget lo que falte y verifica (`verificar`), desde CMD. |
| `scripts/instalar_entorno.ps1` | Lo mismo desde PowerShell (`-Verificar`). |
| `scripts/pruebas/` | Pruebas de la lógica de ambos scripts en Linux. Ver su README. |
| `guias/requisitos.md` | Qué va en tu equipo y qué va en la nube. |
| `guias/preparacion-paso-a-paso.md` | Los mismos pasos en texto. |
| `guias/docker-y-kubernetes-sin-instalacion-local.md` | Cómo trabajar Docker y Kubernetes sin instalarlos. |
| `guias/migracion-on-premise-a-gcp.md` | Hilo de migración de local a GCP. |
| `conda/` | `environment.yml`: pendiente de publicar. |

Solo Windows 10 (1809 o superior) y Windows 11. macOS y Linux no tienen guía en esta edición.

Estado de los scripts: la lógica se probó con un `winget` falso; **no se han probado en Windows real**.
