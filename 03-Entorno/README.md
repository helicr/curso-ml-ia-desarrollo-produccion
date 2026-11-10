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
| `guia-codespaces/index.html` | Guía en diapositivas de Codespaces para el alumnado: abrirlo en el navegador o desde tu VS Code, el bloque 4 de S2 paso a paso (entrenar, construir la imagen, arrancar el contenedor, comparar), cuota y qué hacer si falla. También en PDF (`pdfs/S2-API-y-Docker/01-presentaciones/02-guia-de-codespaces.pdf`). |
| `guia-codespaces/generar.py`, `capturar.py`, `comprobar_diseno.py` y `pruebas/` | `generar.py` produce las diapositivas y la versión en texto a partir de una sola fuente; `capturar.py` renueva las salidas reales (`salidas-reales.json`); `comprobar_diseno.py` revisa en Chrome que nada se desborde; `pruebas/` vigila que los comandos coincidan con la guía de laboratorio y el `devcontainer`. Ver `guia-codespaces/README.md`. |
| `../01-Sesiones/S2-API-y-Docker/contenedores/` | Autoestudio de contenedores antes de S2, para hacer en el Codespace: dos presentaciones («el modelo mental» y «del Dockerfile a producción»), una guía práctica con nueve ejemplos y un laboratorio de cinco fallos provocados. Comandos y salidas reales de Docker (ejecutados en GitHub Actions; **sin probar todavía en un Codespace del curso**). También en PDF (`pdfs/S2-API-y-Docker/`). |
| `guias/codespaces-para-el-alumnado.md` | La misma guía de Codespaces en texto (se genera con `guia-codespaces/generar.py`; no editar a mano). |
| `guias/docker-y-kubernetes-sin-instalacion-local.md` | Cómo trabajar Docker y Kubernetes sin instalarlos. |
| `guias/migracion-on-premise-a-gcp.md` | Hilo de migración de local a GCP. |
| `conda/environment.yml` | Entorno `env-ia-mlops` (ML clásico, MLflow, FastAPI, pruebas, GCP), 23 paquetes con versión fijada. Probado en Linux. |
| `conda/prueba_de_humo.py` | Comprueba el entorno: debe terminar con `HUMO OK`. |
| `conda/verificar_s1.py` y `conda/pruebas/` | Verificador para S1: versiones frente a `environment.yml`, kernel, Git, dato, puerto, pruebas del proyecto base. Termina en `LISTO PARA S1`. `--informe` guarda `verificacion-s1.txt` para el instructor. |
| `VALIDACION.md` | Qué se probó, con qué resultado y qué no. |

Solo Windows 10 (1809 o superior) y Windows 11. macOS y Linux no tienen guía en esta edición.

Estado de los scripts: la lógica se probó con un `winget` falso; **no se han probado en Windows real**.
