# Informe de validación del entorno

Fecha: 09/11/2026. Todo se probó en un contenedor Linux (Ubuntu 24.04, kernel 6.18, 4 CPU, 15 GB). **Nada se probó en Windows real.**
Cualquiera puede repetir estas pruebas con los comandos de la columna «Cómo repetirla».

## Resumen
| Qué | Resultado | Dónde se probó | Cómo repetirla |
|---|---|---|---|
| Script `instalar_entorno.ps1`: sintaxis y lógica | 20 de 20 correctas | PowerShell 7.6.9 en Linux, `winget` falso | `03-Entorno/scripts/pruebas/probar_ps1.sh` |
| Script `instalar_entorno.cmd`: lógica | 26 de 26 correctas | `cmd.exe` de Wine 9, ejecutables falsos | `03-Entorno/scripts/pruebas/probar_cmd.sh` |
| Guía de instalación interactiva | 20 de 20 correctas | Chromium sin conexión | abrir `03-Entorno/guia-instalacion/index.html` |
| Presentación S0 | 22 interacciones correctas, 26 slides sin desbordes | Chromium sin conexión | abrir `01-Sesiones/S0-Presentacion-y-Entorno/slides/index.html` |
| Miniconda real (26.9.4) | instalado y funcionando | Linux | `bash Miniconda3-latest-Linux-x86_64.sh` |
| `environment.yml` (`env-ia-mlops`) | se crea en 1 min 16 s | Linux, solo canal conda-forge | `conda env create -f 03-Entorno/conda/environment.yml` |
| Prueba de humo del entorno | `HUMO OK` | Linux | `python 03-Entorno/conda/prueba_de_humo.py` |
| Resolución del entorno para Windows (`win-64`) | resuelve | `CONDA_SUBDIR=win-64 conda env create --dry-run` | igual |
| Docker (motor) | funciona; descarga `hello-world` y una imagen de Microsoft | Linux | `docker run hello-world` |

## Lo que encontraron las pruebas (errores que habrían aparecido en clase)
1. **Miniconda se niega a crear el entorno** aunque el `environment.yml` use solo conda-forge. Mensaje real:
   `CondaToSNonInteractiveError: Terms of Service have not been accepted for the following channels … repo.anaconda.com/pkgs/main … pkgs/r`.
   `conda env create` no admite `--override-channels`. Receta verificada desde una configuración limpia (4 comandos):
   ```text
   conda config --add channels conda-forge
   conda config --remove channels defaults
   conda config --set channel_priority strict
   conda config --add default_channels https://conda.anaconda.org/conda-forge
   ```
   Con eso, `conda env create` resuelve sin aceptar los términos. Decisión pendiente: usar esta receta, aceptar los términos de Anaconda
   (revisar si tu organización necesita licencia) o cambiar a Miniforge.
2. **MLflow 3.18 + scikit-learn 1.9: `log_model` de un `RandomForest` falla por defecto** con `UntrustedTypesFoundException … sklearn.tree._tree.Tree`.
   `LogisticRegression` sí funciona. Dos soluciones comprobadas: `skops_trusted_types=['sklearn.tree._tree.Tree']` o `serialization_format='cloudpickle'`.
   Esto afecta a S1 (seguimiento con MLflow) y hay que decidir cuál enseñar.
3. **CMD:** la variable de bucle `%%I` chocaba con variables que empiezan por `I` (`ID_3` salía como `3D_3`).
4. **PowerShell:** `-like '[OK]*'` trata los corchetes como un conjunto de caracteres, no como texto.
5. **Slide 15:** el aviso nuevo se montaba sobre el pie de página.

## Versiones resueltas y fijadas
python 3.11.18 · pandas 2.3.3 · numpy 2.4.6 · pyarrow 26.0.1 · scikit-learn 1.9.1 · joblib 1.6.0 · matplotlib 3.11.2 · jupyterlab 4.6.6 ·
ipykernel 7.4.0 · mlflow 3.18.0 · fastapi 0.162.2 · uvicorn 0.54.0 · pydantic 2.14.3 · httpx 0.28.1 · requests 2.34.2 · pytest 9.2.0 ·
google-cloud-storage 3.17.0 · google-cloud-bigquery 3.47.0 · db-dtypes 1.9.0 · pyyaml 6.0.3.

## Salida de la prueba de humo (resumen)
```text
python 3.11.18
  ok    pandas 2.3.3 … (19 librerías importadas)
  sqlite: tablas ['fs_cliente', 'master_ventas', 'ml_dataset', 'raw_ventas']
  mlflow: ejecucion f98ff997 | auc 0.701
  api: respuesta {'clase': 0}
  api: entrada invalida rechazada (422)
HUMO OK
```

## Verificación para S1 (09/11/2026, Linux)
Entorno creado **desde cero** con `environment.yml` (conda 26.9.4, solo conda-forge; de 49 a 82 s en cuatro creaciones), sin instalar nada más.
Todo lo de esta tabla se ejecutó de verdad; las salidas que muestran las diapositivas son las capturadas en esa ejecución (`01-Sesiones/S0-Presentacion-y-Entorno/slides/instalacion/salidas-reales.json`).

| Qué | Resultado | Cómo repetirla |
|---|---|---|
| Versiones instaladas frente a las fijadas | 23 de 23 | `python 03-Entorno/conda/verificar_s1.py` |
| Prueba de humo | `HUMO OK` | `python 03-Entorno/conda/prueba_de_humo.py` |
| Pruebas del proyecto base, sin `pip install` | 30 passed, 4 deselected (rápidas) · 34 passed (completas, unos 50 s) | desde `04-Proyecto-Base`: `python -m pytest -q -m "not lento"` · `python -m pytest -q` |
| Verificador completo | `LISTO PARA S1` (14 OK, 0 AVISO, 0 FALLA), unos 17 s con pruebas | `python 03-Entorno/conda/verificar_s1.py --con-pruebas --informe` |
| Pruebas del verificador | 27 correctas | `python -m pytest 03-Entorno/conda/pruebas -q` |
| Contenido de las diapositivas «Tu equipo listo para S1» | 26 pruebas correctas (comandos, rutas, cifras frente a las salidas reales, sin el nombre interno prohibido) | `python -m pytest 01-Sesiones/S0-Presentacion-y-Entorno/slides/instalacion/pruebas -q` |
| Diseño de las diapositivas | 27 diapositivas sin desbordes en 3 tamaños (1280×766, 1024×640, 800×600); copiar, copiar todo, «hecho», lista y teclado | `python 01-Sesiones/S0-Presentacion-y-Entorno/slides/instalacion/comprobar_diseno.py` (necesita Playwright y Chrome) |
| `git clone --branch develop` contra GitHub | trae `develop` con las carpetas del curso (clon superficial) | `git clone --branch develop --depth 1 URL` |
| Cuaderno de prueba | `NOTEBOOK OK` con `jupyter nbconvert` | ver la guía interactiva, paso «Abre el cuaderno de prueba» |

**Qué encontraron estas pruebas (y qué se hizo):**
1. `git clone` a secas deja en `main`, que está casi vacía → los comandos llevan `--branch develop` (diapositiva 19 de S0, guía interactiva, guía paso a paso, diapositivas y guía rápida).
2. `pytest` no mostraba la línea «30 passed» porque `pyproject.toml` ya llevaba `-q` y el comando del alumno añadía otro → se quitó `addopts = "-q"` de `04-Proyecto-Base/pyproject.toml`.
3. `conda env update --prune` **repone un paquete que falta** (se quitó `jupytext` y lo repuso) pero **no devuelve a su versión** uno cambiado con `pip` (`requests` 2.31.0 siguió igual). Lo que sí lo arregla es `conda install --force-reinstall requests=2.34.2` (probado con `-c conda-forge`). El verificador ya propone esa línea.
4. El verificador daba un falso «puerto 5000 ocupado» justo después de cerrar `mlflow ui` (probaba con `bind`, y el puerto queda en `TIME_WAIT`) → ahora comprueba si algo escucha. Prueba de regresión incluida.
5. **Sin resolver:** `pip check` en el entorno recién creado avisa de que `databricks-sdk 0.73.0` (dependencia de `mlflow`) pide `protobuf<7` y hay `protobuf 7.35.1`. No afecta a las pruebas ni a MLflow en S1; si se quiere evitar el aviso, habría que fijar `protobuf` en `environment.yml` y repetir esta validación.
6. **Aviso para S3 y S4:** `duckdb` y `sqlglot` no están en `environment.yml`; el caso de referencia los pide en su propio `requirements-dev.txt` (simulación de BigQuery en las pruebas).

## Primera prueba en un Windows real (10/11/2026, equipo corporativo)
Hallazgos de la primera ejecución de la guía en un equipo real (Windows 11 corporativo, con MKS Toolkit y varias copias de Git en el `PATH`):
- `winget --version` → v1.29.380; `winget install --id Git.Git -e` instaló Git 2.56.0.4 (descarga, hash y permiso de administrador correctos).
- **Quedó activo otro Git:** justo después, `git --version` seguía diciendo 2.47.1. Hay varias copias en el `PATH` (la del propio equipo va antes) y la terminal abierta no ve la nueva. Comprobar con `where git` y abrir una terminal nueva.
- **`git config --global` falla** con `could not lock config file M:C:/Users/<usuario>/OneDrive - …/.gitconfig: Invalid argument`: la variable `HOME` está mal formada (`M:C:/…`, la deja MKS Toolkit). Solución sin tocar `HOME`: `setx GIT_CONFIG_GLOBAL "%USERPROFILE%\.gitconfig"` y abrir una terminal nueva (vale desde Git 2.32). Pendiente de confirmar en ese equipo y de añadir a «Si falla» de la guía.

## Lo que NO se validó
- **Windows real**, Windows PowerShell 5.1 y el `winget` real: los identificadores de paquete (`Git.Git`, `Anaconda.Miniconda3`, `DBBrowserForSQLite.DBBrowserForSQLite`,
  `Google.CloudSDK`, `Microsoft.VisualStudioCode`) y los de las extensiones de VS Code son de memoria.
- La creación del entorno en Windows: solo se comprobó que **resuelve** (`--dry-run`), no que se instale ni funcione.
- macOS: no resuelve con estas versiones (no es objetivo del curso).
- Limitaciones de Wine: su `where.exe` no funciona, su `&&` falla y su `set /p` lee toda la entrada de una vez; se usaron sustitutos para probar la lógica.
- Codespace del curso, `kind` y `kubectl`: pendientes.
- De las diapositivas «Tu equipo listo para S1»: `winget`, «Anaconda Prompt», `code`, `Get-FileHash` y los clics en VS Code y en el navegador (Windows real); los tiempos son de Linux con buena conexión.
- Google Cloud (autenticación, BigQuery, Cloud Run): no se probó contra la nube real.
