# Qué validar antes de subir a Classroom y de impartir (11/11/2026)

Marca cada punto cuando lo hayas comprobado tú. «Hecho» significa comprobado por mí en Linux o en Edge, no en tu equipo.

## Bloqueantes (afectan a lo que ven los alumnos)
- [ ] **Windows real:** probar la guía de instalación y `instalar_entorno.ps1` en un equipo limpio. Ya hay un hallazgo: en equipos con MKS Toolkit, `HOME` está mal formado y `git config --global` falla (solución: `setx GIT_CONFIG_GLOBAL "%USERPROFILE%\.gitconfig"`). Falta añadirlo al «Si falla» de la guía.
- [ ] **Entorno `env-ia-mlops` en Windows:** crearlo con `conda env create` y pasar `verificar_s1.py` (hoy solo se probó en Linux).
- [ ] **Términos de Anaconda (pendiente 11c):** decidir conda-forge, aceptar términos o Miniforge.
- [ ] **MLflow 3 con scikit-learn (pendiente 11d):** el proyecto usa cloudpickle; confirmar que es lo que se enseña.
- [ ] **`xlrd` (pendiente 18):** decidir si se añade al entorno (hoy se entrega el CSV de Default ya convertido).

## Codespace (escrito, no probado)
- [ ] Subir `.devcontainer/` y `.github/workflows/validar-codespace.yml` y ejecutar el workflow, o abrir un Codespace una vez.
- [ ] Confirmar la versión de `kind` (`KIND_VERSION` en `.devcontainer/postcreate.sh`, puesta de memoria: `v0.27.0`).
- [ ] Confirmar que la cuenta de los alumnos puede crear Codespaces (cuenta personal frente a empresa) y la cuota gratuita vigente.

## Contenido
- [ ] **Cifras y tarifas externas:** ninguna reverificada (la búsqueda web está bloqueada por la política de tu organización y los agentes no pudieron abrir las fuentes). Abrir a mano: Sculley 2015, Anaconda 2020, Google Cloud MLOps, McKinsey 2026, FinOps 2025, Stack Overflow 2025, y las tarifas de Codespaces, Actions, Cloud Shell, Cloud Run y Artifact Registry. Hasta entonces, presentarlas como contexto.
- [ ] **Diapositiva 2 (pregunta 2):** reiniciar el conteo; el texto «Una captura no es evidencia…» da la respuesta antes de votar y la opción B es la más larga.
- [ ] **Diapositivas 28 y 29 (dos casos):** revisar las cifras contra el enunciado (41 188 filas, 11 %, 23 070 filas de la muestra).
- [ ] **Diapositiva 6:** comprobar que la etiqueta «Opcional · LLM (extra)» se entiende.

## Material generado
- [ ] **PDF:** se generaron con Edge (no con Chrome) y `pandoc` instalado vía `pip`; el script los da por correctos. Abrir al menos la presentación de S0 (31 páginas) y la de S1 en un visor y mirar las diapositivas 28 y 29.
- [ ] **D01 (guion alumno y profesor):** abrir uno de los botones «Abrir en VS Code» y comprobar que VS Code se abre con el proyecto (solo funciona si el repositorio está en `C:\cursos\curso-ml-ia-desarrollo-produccion`).
- [ ] **D01:** los dos HTML no tienen PDF; decidir si se suben tal cual o convertidos.
- [ ] **S2 a S5:** solo README; no hay materiales que subir.

## Repositorio
- [ ] **Commit:** hay unos 50 archivos modificados sin commitear (texto, diapositivas, PDF, índices, Codespace, guiones). Decidir si se hace uno o varios commits.
- [ ] **Fusionar `develop` en `main` y subir** (pendiente 9). Hasta entonces los comandos de clonado usan `--branch develop`.
- [ ] **Credenciales:** has pegado una contraseña de `cursomlops@gmail.com` en este chat; cámbiala. Las credenciales de `gcloud` (ADC) que acabas de crear son de tu cuenta del banco y no tienen nada que ver con el curso.

## Classroom
- [ ] Ver qué definió la institución (temas, tareas, fechas, rúbricas) y adaptar `classroom-subida.md`.
- [ ] Decidir si se sube a mano o con un script propio con la API de Classroom.
