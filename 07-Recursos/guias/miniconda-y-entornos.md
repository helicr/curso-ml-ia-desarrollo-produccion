# Miniconda y entornos de conda: guía y chuleta

**Se usa en:** S0 (instalar y comprobar) y en todas las sesiones, porque cada comando de Python se ejecuta dentro del entorno del curso.
**Entorno del curso:** `env-ia-mlops` (receta: `03-Entorno/conda/environment.yml`).

## Para qué sirve
Miniconda instala `conda`, un gestor de **paquetes** y de **entornos**. Un entorno es una carpeta aislada con su propia versión de Python y de librerías.
Sirve para dos cosas: que un proyecto no rompa a otro, y que todo el grupo tenga **las mismas versiones** (las fija `environment.yml`).

Cuatro ideas que bastan:
- `base` es el entorno que trae Miniconda. **No instales nada en `base`.**
- Se trabaja con **un entorno por proyecto**. En este curso: `env-ia-mlops`.
- Un entorno se **activa** en la terminal. Mientras está activo, `python`, `pip` y `jupyter` son los suyos y el prompt muestra `(env-ia-mlops)`.
- `environment.yml` es la receta para crearlo de nuevo en cualquier equipo.

## Qué terminal usar en Windows
| Terminal | ¿Reconoce `conda`? |
|---|---|
| **Anaconda Prompt** (Menú Inicio) | Sí, siempre. Es la recomendada en S0. |
| Terminal de VS Code | Sí, si conda está inicializado (`conda init`) o si VS Code activa el entorno por ti (ver `vscode.md`). |
| CMD o PowerShell normales | Solo después de inicializar conda y volver a abrir la terminal. |

Para inicializar (una sola vez, cierra y abre la terminal después):
```text
conda init cmd.exe
conda init powershell
```
Si PowerShell responde que la ejecución de scripts está deshabilitada, la opción habitual es `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
Cambia una política de tu usuario: en un equipo corporativo, consúltalo antes. Los scripts del curso no tocan esa política.

## Comprobación de S0 (checklist 3, 5 y 6)
```text
conda --version
conda env list
conda env create -f 03-Entorno\conda\environment.yml
conda activate env-ia-mlops
python 03-Entorno\conda\prueba_de_humo.py
```
La prueba debe terminar con `HUMO OK`. Crear el entorno descarga cientos de MB (en mi prueba, unos 480 MB de paquetes): con buena conexión (Linux) tardó 1 min 20 s;
en clase puede tardar bastante más. Lánzalo antes de la sesión, no durante.

## Antes de crear el entorno: canales y términos de servicio
El Miniconda de Anaconda puede negarse a crear entornos hasta aceptar los términos de sus canales por defecto
(`CondaToSNonInteractiveError`), aunque el entorno use solo conda-forge. La configuración que lo evita deja a conda-forge como único canal:
```text
conda config --add channels conda-forge
conda config --remove channels defaults
conda config --set channel_priority strict
conda config --add default_channels https://conda.anaconda.org/conda-forge
```
Comprobar: `conda config --show channels default_channels`. Debe quedar solo conda-forge en `default_channels`.

**Si el segundo comando da `CondaKeyError: 'channels': value 'defaults' not present in config`, no pasa nada:** significa que `defaults` ya no estaba. Sigue con el tercero y el cuarto.
Alternativas: aceptar los términos de Anaconda (revisa si tu organización necesita licencia) o usar Miniforge, que ya viene con conda-forge. La decisión sobre cuál usa el curso sigue abierta en `00-Planificacion/decisiones-y-pendientes.md`.

## Chuleta de comandos

### Entornos
| Quiero... | Comando |
|---|---|
| Ver los entornos (el activo lleva `*`) | `conda env list` |
| Crear uno vacío con Python 3.11 | `conda create -n mi-entorno python=3.11` |
| Crearlo desde un archivo | `conda env create -f environment.yml` |
| Activarlo | `conda activate env-ia-mlops` |
| Desactivarlo | `conda deactivate` |
| Ejecutar algo sin activarlo | `conda run -n env-ia-mlops python script.py` |
| Duplicarlo | `conda create -n copia --clone env-ia-mlops` |
| Cambiarle el nombre | `conda rename -n viejo nuevo` |
| Borrarlo | `conda env remove -n nombre` |

### Paquetes (con el entorno activo, o añade `-n nombre`)
| Quiero... | Comando |
|---|---|
| Listar lo instalado | `conda list` · filtrar: `conda list pandas` |
| Buscar un paquete | `conda search -c conda-forge nombre` |
| Instalar | `conda install -c conda-forge nombre` |
| Instalar una versión exacta | `conda install nombre=2.3.3` |
| Actualizar uno | `conda update nombre` |
| Quitar | `conda remove nombre` |

### Reproducibilidad
| Quiero... | Comando |
|---|---|
| Guardar la receta de lo que **instalé yo** | `conda env export --from-history > environment.yml` |
| Guardar todo, con versiones exactas (no vale entre sistemas operativos) | `conda env export > entorno-completo.yml` |
| Actualizar el entorno tras cambiar el `.yml` | `conda env update -f environment.yml --prune` |
| Rehacerlo desde cero | `conda env remove -n env-ia-mlops` y luego `conda env create -f environment.yml` |

`--prune` elimina del entorno lo que ya no aparece en el archivo. Si el entorno tiene paquetes instalados con `pip`, `conda env export` avisa de que no puede fijarlos.

### Diagnóstico y mantenimiento
| Quiero... | Comando |
|---|---|
| Ver versión, rutas y canales | `conda info` |
| Ver de dónde sale cada ajuste | `conda config --show-sources` |
| Saber cuánto espacio se libera | `conda clean --all --dry-run` |
| Liberar caché de descargas | `conda clean --all` |

## `conda` o `pip`
- Instala con **conda** (`-c conda-forge`) todo lo que esté disponible.
- Usa **pip** solo para lo que conda no tenga, siempre con el entorno activo y comprobando antes con `where python` (Windows) que es el del entorno.
- `pip install -e .` dentro de `04-Proyecto-Base` instala el paquete del curso (`ia_mlops`) en modo editable. Es lo esperado.
- Mezclar los dos para el mismo paquete es la causa habitual de entornos rotos.

## El flujo del curso
```text
conda activate env-ia-mlops
cd 04-Proyecto-Base
pip install -e .
python -m ia_mlops.operacional     # una vez: simula la base de ventas (data/external/retail.db)
python -m ia_mlops.pipeline        # los cuatro pipelines; los que no tienen cambios no hacen nada
python -m pytest -q
```
Los cuadernos usan el kernel `env-ia-mlops`: se elige en VS Code (ver `vscode.md`). Si no aparece:
```text
python -m ipykernel install --user --name env-ia-mlops --display-name "env-ia-mlops"
```
`env-ia-opcional` (red neuronal y LLM) todavía no existe.

## Errores frecuentes
| Síntoma | Causa y solución |
|---|---|
| `conda no se reconoce como un comando` | Estás en una terminal sin inicializar. Usa Anaconda Prompt, o `conda init` y reabre la terminal. |
| `CondaToSNonInteractiveError` | Términos de servicio sin aceptar. Aplica la receta de canales de arriba. |
| `CondaValueError: prefix already exists` | El entorno ya existe. Usa `conda env update ... --prune`, o bórralo y créalo de nuevo. |
| `ModuleNotFoundError` al ejecutar | Entorno equivocado. Mira el prompt, `conda env list` y `where python`. En un cuaderno, es el kernel. |
| La creación tarda mucho o falla a mitad | Mala conexión o disco lleno. Repite el comando; `conda clean --all` libera espacio. |
| Conflictos al resolver (`UnsatisfiableError`) | Has pedido versiones incompatibles. Quita el paquete que añadiste o crea el entorno limpio desde el `.yml`. |

## Qué se probó y qué no
Comandos ejecutados con **conda 26.9.4 sobre Linux** (09/11/2026): crear `env-ia-mlops` desde el `environment.yml` del repositorio, `HUMO OK`, los 34 tests del proyecto base,
`env list`, `activate`, `deactivate`, `run`, `list`, `export --from-history`, `create`, `install`, `remove`, `rename`, `env remove`, `env update --prune`, `clean --dry-run`, `info` y `config --show-sources`.
Ese conda se instaló desde conda-forge (el instalador de Anaconda no era accesible desde esa red), así que **no reproduce** el aviso de términos de servicio ni el comando `conda tos`,
que menciona `03-Entorno/guias/preparacion-paso-a-paso.md`. No se probaron `conda init`, la política de PowerShell ni Anaconda Prompt: **nada se ejecutó en Windows real**.
`conda create --clone` y `conda env export` completo son sintaxis estándar de conda, no ejecutadas aquí.
