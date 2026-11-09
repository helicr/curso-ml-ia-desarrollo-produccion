# De cuaderno a Python: cómo y por qué

Un cuaderno es ideal para **explorar, explicar y construir** un pipeline. Un servicio en producción necesita **código que se pueda importar, probar,
empaquetar y automatizar**. En este proyecto los cuadernos son los pipelines y el paquete `ia_mlops` es su traducción.

## Los dos caminos
| | Traducción literal | Refactorización |
|---|---|---|
| Herramienta | `jupytext --to py:percent` | A mano, con criterio |
| Resultado | Un `.py` por cuaderno, celda a celda | Funciones con nombre en módulos (`dataset.py`, `features.py`…) |
| Para qué sirve | Ejecutar un cuaderno sin Jupyter; revisar cambios en Git | Reutilizar, probar, importar desde la API, empaquetar |
| Rutas y parámetros | Variables de entorno (`CURSO_DB`, `CURSO_MODELOS`…) | `config.py` y argumentos de línea de comandos |
| Limitación | Sigue siendo un script lineal | Hay que mantenerlo sincronizado con el cuaderno |

```text
make traducir          # o:  jupytext --to py:percent notebooks/01_pipeline_raw_a_master.ipynb -o scripts_desde_notebooks/01.py
```

## Equivalencia: lo que no se puede romper
Si el cuaderno y el paquete dan resultados distintos, uno de los dos está mal. `tests/test_notebooks.py` lo verifica:
1. Ejecuta los cuatro cuadernos con **papermill** sobre una base temporal.
2. Compara **todas las tablas** (RAW, MASTER, FS y ML) con las que construye el paquete.
3. Compara las **métricas** (AUC, precisión media…) y la **huella** de los datos de entrenamiento.
4. Traduce los cuadernos con **jupytext**, ejecuta los `.py` resultantes y vuelve a comparar.

Esta prueba ya detectó una deriva real: las descripciones de las reglas de calidad tenían tildes en el cuaderno y no en el paquete.
Con el dato completo (1 067 371 filas) las nueve tablas son idénticas y los AUC coinciden hasta el último decimal.

## Qué cambia al traducir un cuaderno a módulos
| En el cuaderno | En el paquete |
|---|---|
| Celda de parámetros (`FUENTE`, `RUTA_DB`…) | `config.py`, variables de entorno y argumentos (`--fuente completo`) |
| Celdas sueltas con funciones auxiliares | Funciones públicas con docstring (`cargar_raw`, `construir_master`…) |
| `print` y tablas de `pandas` para mirar | `print` informativo (`verbose`) y datos devueltos para probar |
| Gráficos que se ven en pantalla | Figuras guardadas en `reports/figures/` |
| `assert` sueltos como controles | Reglas de calidad en `calidad.py` y pruebas en `tests/` |
| Ejecución manual celda a celda | `python -m ia_mlops.pipeline`; luego GitHub Actions (S4) |

## Reglas para que un cuaderno se pueda traducir bien
- Una celda de **parámetros** al inicio (con la etiqueta `parameters`), con los comentarios en líneas aparte.
- Nada de rutas escritas a mano: todo parte de la carpeta del proyecto.
- Sin `display()` ni comandos mágicos (`%`): el último valor de una celda se ve en el cuaderno y no estorba en un script.
- Cada cuaderno **empieza y termina** de forma explícita: crea sus tablas, comprueba y cierra la conexión.
- Los cuadernos se guardan **sin salidas** en Git, para que los cambios sean legibles.

## Ejercicio de S1
Elige la función de `ia_mlops/features.py`, léela junto a la celda de `02_pipeline_master_a_fs.ipynb` y señala **tres cosas** que cambiaron al traducirla.
