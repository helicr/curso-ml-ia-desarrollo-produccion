# Visual Studio Code: guía y atajos

**Se usa en:** S0 (instalar, extensiones, elegir intérprete) y en todas las sesiones: escribes código, ejecutas cuadernos, usas la terminal y haces commits desde aquí.

## Para qué sirve
VS Code es un editor de código con terminal, cuadernos Jupyter, control de versiones con Git y depurador integrados. No instala Python ni conda: **usa el que le indiques**.
El 90 % de los problemas de principiantes se resumen en una frase: *VS Code está usando un Python distinto al del entorno `env-ia-mlops`*. Esta guía te enseña a comprobarlo.

## Extensiones del curso
El script de instalación del curso añade estas siete (`03-Entorno/scripts/instalar_entorno.ps1`):
| Extensión | ID | Para qué |
|---|---|---|
| Python | `ms-python.python` | Ejecutar y depurar Python, elegir intérprete, pruebas |
| Pylance | `ms-python.vscode-pylance` | Autocompletado y avisos al escribir |
| Jupyter | `ms-toolsai.jupyter` | Abrir y ejecutar cuadernos `.ipynb` |
| Container Tools | `ms-azuretools.vscode-containers` | Ver imágenes y contenedores de Docker (S2) |
| Kubernetes | `ms-kubernetes-tools.vscode-kubernetes-tools` | Ver clústeres (laboratorio opcional de S3) |
| Dev Containers | `ms-vscode-remote.remote-containers` | Abrir el proyecto dentro de un contenedor |
| GitHub Codespaces | `GitHub.codespaces` | Abrir el Codespace del curso desde VS Code (cómo conectar: `03-Entorno/guias/codespaces-para-el-alumnado.md`) |

Desde la terminal:
```text
code --version
code --list-extensions
code --install-extension ms-python.python
```

## Primeros pasos
1. Abre la **carpeta** del proyecto, no un archivo suelto: desde la terminal, `cd` hasta el repositorio y `code .`; o *Archivo → Abrir carpeta*.
2. Cuando pregunte si **confías en los autores** de la carpeta, acepta solo si la clonaste tú desde el repositorio del curso (*Workspace Trust*). Sin confianza, VS Code funciona en modo restringido y no ejecuta código.
3. Barra lateral izquierda: **Explorador** (archivos), **Buscar**, **Control de código fuente** (Git), **Ejecutar y depurar**, **Extensiones**.
4. Barra inferior: a la izquierda, la **rama** de Git; a la derecha, el **intérprete de Python** (versión y entorno).

## Elegir el intérprete y el kernel (checklist 6 de S0)
Es el paso más importante. Hay que decirle dos veces a VS Code que use `env-ia-mlops`: una para los scripts y otra para los cuadernos.

**Scripts `.py`:** `Ctrl+Shift+P` → *Python: Select Interpreter* → elige el que diga `env-ia-mlops`. Debe mostrarse en la barra inferior.
**Cuadernos `.ipynb`:** botón *Select Kernel* (arriba a la derecha) → *Python Environments…* → `env-ia-mlops`.

Comprobación: ejecuta lo mismo en un script y en un cuaderno.
```python
import sys; print(sys.executable)
```
La ruta debe ser **la misma** y contener `env-ia-mlops`. Si no aparece el entorno en la lista:
- Cierra y abre VS Code, o `Ctrl+Shift+P` → *Developer: Reload Window*.
- *Select Interpreter → Enter interpreter path…* y apunta a `python.exe` dentro de la carpeta del entorno
  (por ejemplo `%USERPROFILE%\miniconda3\envs\env-ia-mlops\python.exe`; la ruta depende de dónde se instaló Miniconda; `conda env list` te la muestra).
- Registra el kernel a mano (ver `miniconda-y-entornos.md`).

## La terminal integrada
`` Ctrl+` `` la abre dentro de VS Code, ya situada en la carpeta del proyecto. Con el menú desplegable (`˅`) eliges el tipo: *Command Prompt* o *PowerShell*.
Si seleccionaste el intérprete del entorno, VS Code intenta ejecutar `conda activate env-ia-mlops` al abrir una terminal nueva; lo sabrás porque el prompt empieza por `(env-ia-mlops)`.
Si no lo hace, lanza el comando a mano, o usa Anaconda Prompt. Comprobación rápida: `where python` (Windows) debe listar primero la ruta del entorno.

Comandos del flujo del curso, desde la terminal de VS Code:
```text
cd 04-Proyecto-Base
python -m ia_mlops.operacional
python -m ia_mlops.pipeline
python -m pytest -q -m "not lento"
```

## Cuadernos Jupyter
| Quiero... | Cómo |
|---|---|
| Ejecutar la celda | `Shift+Enter` (ejecuta y baja) · `Ctrl+Enter` (ejecuta y se queda) |
| Ejecutar todo | Botón *Run All* de la barra del cuaderno |
| Reiniciar el kernel y limpiar la memoria | *Restart* · *Restart and Run All* para comprobar que el cuaderno funciona de principio a fin |
| Ver las variables | *Variables* en la barra del cuaderno |
| Añadir celda de código o de texto | Botones *+ Code* / *+ Markdown*, o con la celda seleccionada: `B` (debajo), `A` (encima), `M` (a Markdown), `Y` (a código) |
| Borrar celda | Con la celda seleccionada (no editando), `D D` |

Los cuadernos del curso son pipelines: **ejecútalos en orden** (01 → 04). Si algo falla a medias, *Restart and Run All* y vuelve a empezar.
Ejecutarlos sin abrir VS Code: `papermill notebooks/01_pipeline_raw_a_master.ipynb salida01.ipynb -p FUENTE muestra`.

## Git dentro de VS Code
Panel *Control de código fuente* (`Ctrl+Shift+G`): ves los archivos cambiados, pulsas `+` para prepararlos, escribes el mensaje y confirmas con *Commit*; *Sync Changes* hace `pull` y `push`.
La rama actual está abajo a la izquierda: pulsa sobre ella para cambiar o crear ramas. Los conflictos se resuelven con los botones *Accept Current / Incoming / Both* que aparecen sobre las marcas.
Todo esto equivale a los comandos de `git-y-ramas.md`; usa lo que te resulte más cómodo, pero **no mezcles sin mirar `git status`**.

## Pruebas y depuración
- Las pruebas se lanzan más seguras desde la terminal: `python -m pytest tests -q` dentro de `04-Proyecto-Base`.
- El panel *Testing* (matraz) también las descubre: *Configure Python Tests* → pytest → carpeta `tests`. Funciona si abriste la carpeta `04-Proyecto-Base` o fijaste ese directorio.
- Depurar un script: pon un punto de parada (clic a la izquierda del número de línea) y pulsa `F5`. `F10` salta una línea, `F11` entra en la función, `Shift+F5` detiene.

## Ver bases SQLite
Para abrir `curso.db` desde VS Code hay extensiones opcionales (`qwtel.sqlite-viewer` para explorar tablas, `alexcvzz.vscode-sqlite` para lanzar consultas). Detalles y alternativas en `sqlite.md`.

## Atajos (Windows)
| Atajo | Qué hace |
|---|---|
| `Ctrl+Shift+P` | **Paleta de comandos**: escribe lo que quieras hacer |
| `Ctrl+P` | Abrir un archivo por nombre |
| `` Ctrl+` `` | Mostrar u ocultar la terminal |
| `Ctrl+B` | Mostrar u ocultar la barra lateral |
| `Ctrl+Shift+E` / `F` / `G` / `X` | Explorador / Buscar en todo el proyecto / Git / Extensiones |
| `Ctrl+S` | Guardar |
| `Ctrl+Z` / `Ctrl+Y` | Deshacer / rehacer |
| `Ctrl+/` | Comentar o descomentar la línea |
| `Alt+↑` / `Alt+↓` | Mover la línea |
| `Shift+Alt+↓` | Duplicar la línea |
| `Ctrl+D` | Seleccionar la siguiente coincidencia (edición múltiple) |
| `F2` | Renombrar un símbolo en todo el código |
| `F12` | Ir a la definición |
| `Shift+Alt+F` | Dar formato al documento |
| `Ctrl+,` | Ajustes |
| `F5` | Ejecutar con depurador |

## Ajustes útiles (`Ctrl+,`)
- *Files: Auto Save* → `afterDelay`: guarda solo. Evita ejecutar una versión sin guardar.
- *Python › Terminal: Activate Environment* → activado (viene así): activa el entorno al abrir la terminal.

## Errores frecuentes
| Síntoma | Causa y solución |
|---|---|
| `'code' no se reconoce como un comando` | Cierra y abre la terminal. Si sigue, reinstala marcando *Añadir al PATH*, o usa *Ctrl+Shift+P → Shell Command: Install 'code' command* (solo macOS/Linux). |
| Pylance subraya `import pandas` («no se pudo resolver») | Intérprete equivocado. Vuelve a *Select Interpreter*. |
| `ModuleNotFoundError` en un cuaderno | Kernel equivocado. *Select Kernel → env-ia-mlops*. |
| El cuaderno no encuentra el kernel o «Failed to start the Kernel» | Falta `ipykernel` en el entorno o el entorno no se creó. Ejecuta `conda list ipykernel` con el entorno activo; si falta, `conda install ipykernel`. |
| La terminal no muestra `(env-ia-mlops)` | Conda sin inicializar para ese tipo de terminal (`conda init`) o intérprete sin seleccionar. Activa a mano o usa Anaconda Prompt. |
| Las pruebas del panel *Testing* no aparecen | Abre la carpeta `04-Proyecto-Base` o ejecuta `pytest` desde la terminal. |
| «Restricted Mode» | Aún no has confiado en la carpeta (*Workspace Trust*). |

## Qué se probó y qué no
**Esta es la única guía de las cuatro que no se pudo contrastar con el programa real**: se redactó sin VS Code instalado.
Lo comprobado: el listado de extensiones coincide con el script de instalación del repositorio; los comandos de terminal se ejecutaron (ver `miniconda-y-entornos.md`).
Los nombres de menús, botones y atajos son los habituales de VS Code en Windows, pero **no se verificaron en una versión concreta**; las etiquetas pueden cambiar con la versión y con el idioma de la interfaz.
Conviene revisarla con VS Code abierto antes de entregarla a los alumnos.
