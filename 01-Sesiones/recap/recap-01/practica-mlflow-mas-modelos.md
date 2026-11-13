# Práctica guiada: añadir dos modelos y compararlos en MLflow

**Duración:** 30–40 minutos. **Requisito:** haber hecho [MLflow paso a paso](mlflow-paso-a-paso.md) (pasos 1 a 4): entorno activado, estás en
`04-Proyecto-Base` y `python -m ia_mlops.mlflow_ui --comprobar` muestra al menos 4 ejecuciones.

**Qué vas a aprender:** dónde se decide qué modelos se comparan, cómo añadir uno sin romper el preprocesamiento, por qué el pipeline sí vuelve a
entrenar cuando cambias el código, y cómo leer la comparación en MLflow sin hacer trampa con test.

> **Probado en Windows 11 el 13/11/2026** con la muestra del curso, en una carpeta temporal (variables `CURSO_*`). Todas las salidas y cifras de esta
> práctica son de esa ejecución. Con el dato completo de UCI las cifras serán otras.

---

## Paso 1 · Encuentra la lista de modelos (3 min)

Los modelos que se comparan están en **una sola función**, `modelos()`, que devuelve un diccionario `{nombre: modelo sin entrenar}`:

| Si entrenas con… | Dónde está `modelos()` |
|---|---|
| El pipeline (`python -m ia_mlops.pipeline_train`) | `ia_mlops/modeling/train.py`, líneas 76–84 |
| El cuaderno 04 | Apartado *2. Los modelos y la evaluación*, la celda de código que empieza por `from sklearn.dummy import DummyClassifier` |

Ábrela. Hoy hay tres: `referencia_sin_aprender`, `regresion_logistica` (dentro de un `Pipeline` con imputar, `log1p` y escalar) y `gradient_boosting`.
Todo lo demás (entrenar, medir en train/valid/test, registrar en MLflow, elegir con valid) recorre ese diccionario: **si añades una entrada, el resto
del código la trata igual que a las otras.**

## Paso 2 · Elige los dos modelos nuevos (5 min)

Proponemos dos modelos de árboles, para comparar con lo que ya hay:

| Nombre | Modelo | Por qué este |
|---|---|---|
| `bosque_aleatorio` | `RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=0)` | Muchos árboles **en paralelo**, cada uno con una muestra distinta de filas y variables; se promedian. Es la otra gran familia de árboles junto al gradient boosting (que los pone **en secuencia**). `min_samples_leaf=5` evita hojas de una sola fila, para que memorice menos |
| `arbol_decision` | `DecisionTreeClassifier(max_depth=4, min_samples_leaf=20, random_state=0)` | **Un solo árbol** poco profundo: se puede dibujar y explicar a negocio («si la recencia es menor que X y…»). Sirve para ver cuánto aportan 300 árboles frente a uno |

`random_state=0` hace que el resultado sea **reproducible**: misma semilla, mismos árboles, mismas métricas.

**¿Y los nulos?** `dias_medios_entre_compras` es nula cuando el cliente solo compró una vez (con la muestra: 241 filas de 626 en train, 37 de 114 en
valid, 69 de 250 en test). La regresión logística los rellena con `SimpleImputer` dentro de su `Pipeline`. Haremos lo mismo con los dos modelos nuevos:
- scikit-learn 1.9 (la del curso) ya admite nulos en estos árboles (lo comprobamos: `RandomForestClassifier` entrena sin imputar). Aun así los metemos en
  un `Pipeline` con `SimpleImputer(strategy='median')`: así el tratamiento de nulos queda **escrito y dentro del modelo**, igual que en la regresión
  logística, y la API de S2 aplicará exactamente lo mismo.
- No hace falta escalar: a un árbol le da igual la escala de las variables.

## Paso 3 · Haz el cambio (5 min)

En `ia_mlops/modeling/train.py`:

**3a.** Cambia la línea de import del ensemble y añade la del árbol (líneas 54 y siguiente):
```python
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
```

**3b.** Añade dos entradas al final del diccionario de `modelos()`, después de `gradient_boosting`:
```python
        'gradient_boosting': HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, random_state=0),
        'bosque_aleatorio': Pipeline([('imputar', SimpleImputer(strategy='median')),
                                      ('modelo', RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=0))]),
        'arbol_decision': Pipeline([('imputar', SimpleImputer(strategy='median')),
                                    ('modelo', DecisionTreeClassifier(max_depth=4, min_samples_leaf=20, random_state=0))]),
    }
```

Guarda. `git diff --stat` debe decir `1 file changed, 6 insertions(+), 1 deletion(-)`.

**Si lo haces en el cuaderno 04** (en lugar de, o además de, `train.py`): el mismo cambio en su celda de modelos **y** añade los dos nombres al
diccionario `COLOR_MODELO` de la celda de gráficas del apartado 4, por ejemplo:
```python
COLOR_MODELO = {'referencia_sin_aprender': '#9ca3af', 'regresion_logistica': '#2563eb', 'gradient_boosting': '#f59e0b',
                'bosque_aleatorio': '#10b981', 'arbol_decision': '#a855f7'}
```
Si no, el cuaderno se para en esa celda con `KeyError: 'bosque_aleatorio'` (comprobado). Con los colores añadidos, el cuaderno entero se ejecutó en 32 s
y dio las mismas cifras que el pipeline.

## Paso 4 · Vuelve a entrenar. ¿Hace falta `--forzar`? (8 min)

Los pipelines son **idempotentes**: antes de trabajar calculan una *huella de entrada* y, si coincide con la de la última ejecución correcta, dicen
«sin cambios» y no hacen nada (`ia_mlops/control.py`, función `ejecutar`, líneas 100–112). La clave es **qué entra en esa huella**. En
`ia_mlops/pipeline_train.py`, líneas 29–32:

```python
def huella_entrada(con, usar_mlflow):
    datos = train.huella_datos(pd.read_sql('SELECT * FROM ml_dataset', con))
    return control.huella(datos, config.FEATURES, config.OBJETIVO, config.CORTES, config.VENTANA_OBJETIVO_DIAS,
                          control.huella_codigo(train), usar_mlflow), datos
```

`control.huella_codigo(train)` es el **código fuente completo de `train.py`** (`inspect.getsource`, `control.py` línea 49). Al editar `modelos()`
cambia el texto de `train.py`, cambia la huella y **el pipeline vuelve a entrenar solo, sin `--forzar`**.

```
python -m ia_mlops.pipeline_train
```

Salida real (26,5 s):
```
[pipeline_train] ejecutando (huella de entrada 2e2ec74b00bf)
  referencia_sin_aprender    AUC valid 0.500 | test 0.500 | precision media test 0.404
  regresion_logistica        AUC valid 0.698 | test 0.747 | precision media test 0.659
  gradient_boosting          AUC valid 0.663 | test 0.735 | precision media test 0.648
  bosque_aleatorio           AUC valid 0.703 | test 0.783 | precision media test 0.741
  arbol_decision             AUC valid 0.668 | test 0.701 | precision media test 0.622
  Mejor modelo: bosque_aleatorio. Guardado en …\models\modelo.joblib
  Registrado en MLflow como «retencion-90d», version 2. Para verlo: python -m ia_mlops.mlflow_ui
```
La huella de antes era `7108eeb2fa32`; ahora es `2e2ec74b00bf`. Ejecútalo **otra vez** sin cambiar nada:
```
[pipeline_train] sin cambios: la entrada es la misma que en la ultima ejecucion (2e2ec74b00bf). Usa --forzar para rehacerlo.
```

**Cuándo sí hace falta `--forzar`:**
- Si cambias código que **no** está en `train.py` ni en la configuración que entra en la huella (por ejemplo, una librería que actualizas): la huella no cambia.
- Si quieres repetir el mismo entrenamiento a propósito (por ejemplo, para ver que da lo mismo).
- El **cuaderno** no tiene control de huella: cada vez que lo ejecutas entrena y añade ejecuciones a MLflow.

`python -m ia_mlops.mlflow_ui --comprobar` dice ahora:
```
  Experimento «retencion-90d»: 10 ejecuciones · modelo registrado «retencion-90d»: 2 versiones
```
4 del primer entrenamiento + 6 de este (5 modelos + `MEJOR-bosque_aleatorio`).

## Paso 5 · Compara en MLflow (10 min)

`python -m ia_mlops.mlflow_ui` → **Model training** → **Experiments** → `retencion-90d` → **Runs**. Si la interfaz ya estaba abierta, las ejecuciones
nuevas aparecen solas en unos segundos; si no, recarga (F5). Con **Columns** añade `train_auc`, `valid_auc`, `test_auc` y `huella_datos`.

Lo que se ve (salida real de MLflow, último entrenamiento; métricas redondeadas a 3 decimales):

| Ejecución | train_auc | valid_auc | test_auc | sobreajuste (train − valid) | aciertos en el 10 % mejor (test) |
|---|---|---|---|---|---|
| referencia_sin_aprender | 0,500 | 0,500 | 0,500 | 0,000 | 24 % |
| regresion_logistica | 0,803 | 0,698 | 0,747 | 0,105 | 88 % |
| gradient_boosting | 1,000 | 0,663 | 0,735 | 0,337 | 76 % |
| **bosque_aleatorio** | 0,976 | **0,703** | 0,783 | 0,273 | 88 % |
| arbol_decision | 0,835 | 0,668 | 0,701 | 0,167 | 84 % |

Las seis ejecuciones tienen la **misma `huella_datos`** (`35a94deb4e04ab4a`), igual que las del primer entrenamiento: se entrenaron con los mismos
datos, así que **la comparación es justa**. Tasa base en test: 40,4 %.

Ahora, en la interfaz:
1. Marca `bosque_aleatorio` y `regresion_logistica` → **Compare**. En *Parameters* solo cambia `modelo` (pulsa *Show diff only*): `huella_datos`,
   `n_variables` (13) y `ventana_objetivo_dias` (90) son iguales.
2. En *Metrics* busca `valid_auc`: 0,703 frente a 0,698.
3. **Model registry** → `retencion-90d`: *Version 2* tiene las etiquetas `modelo: bosque_aleatorio`, `huella_datos: 35a94deb4e04ab4a`,
   `valid_auc: 0.7029`; *Version 1*, `regresion_logistica` y `0.6982`. La versión 1 no se ha borrado.

**Qué versión se registra:** solo la del **ganador en valid** (aquí, el bosque aleatorio, versión 2). Los demás modelos quedan como ejecuciones con sus
métricas, pero no se registran.

**Por qué se elige con valid y no con test:** test es el examen sorpresa. Si mirásemos test para elegir, el modelo elegido sería «el que mejor salió en
ese examen» y su nota de test dejaría de ser una estimación honesta de cómo irá con datos nuevos. Aquí, además, test daría el mismo ganador, pero eso
no se sabe hasta que se mira, y la regla tiene que valer siempre.

## Paso 6 · Deshaz el cambio (3 min) — obligatorio

Las pruebas del proyecto esperan **los tres modelos originales**: por ejemplo, `test_entrena_y_guarda_los_artefactos` exige que el mejor sea
`regresion_logistica` o `gradient_boosting`, y `test_entrenar_otra_vez_sin_cambios_no_duplica_ejecuciones_en_mlflow` cuenta las ejecuciones de tres modelos.
Comprobado: con los dos modelos añadidos, `python -m pytest -q -m "not lento"` da **4 failed, 123 passed, 4 deselected** (falla también
`test_predice_una_probabilidad` de la API, porque el modelo servido pasa a ser el bosque). Deshaz el cambio con git, desde `04-Proyecto-Base`:

```
git restore ia_mlops/modeling/train.py
git status
```
`git status` ya no debe mostrar `train.py` como modificado. Si cambiaste el cuaderno: `git restore notebooks/04_entrenamiento_y_seguimiento.ipynb`
(pierdes también sus salidas nuevas, que es lo que queremos).

Después **vuelve a entrenar**, para que `models/modelo.joblib` y `models/modelo_mlflow/` vuelvan a ser la regresión logística:
```
python -m ia_mlops.pipeline_train
```
Salida real (19,7 s): la huella vuelve a ser la original, distinta de la última (`2e2ec74b00bf`), así que entrena sin `--forzar`:
```
[pipeline_train] ejecutando (huella de entrada 7108eeb2fa32)
  ...
  Mejor modelo: regresion_logistica. Guardado en …\models\modelo.joblib
  Registrado en MLflow como «retencion-90d», version 3. Para verlo: python -m ia_mlops.mlflow_ui
```
MLflow guarda la historia completa: versión 1 (regresión), 2 (bosque), 3 (regresión otra vez). Es exactamente lo que hará falta en S4–S5 para el rollback.

Por último, las pruebas:
```
python -m pytest -q -m "not lento"
```
**Debe salir:** `127 passed, 4 deselected`.

---

## Preguntas para el alumnado

1. ¿Qué modelo gana con valid? ¿Por cuánto?
2. El bosque aleatorio tiene 0,976 de AUC en train y 0,703 en valid. ¿Está sobreajustado? ¿Más o menos que el gradient boosting?
3. Valid tiene 114 filas. ¿Te fiarías de una diferencia de 0,005 de AUC para cambiar el modelo de producción?
4. Si eligieras con test, ¿qué modelo ganaría? ¿Por qué igualmente no se hace?
5. ¿Por qué no hizo falta `--forzar` después de editar `train.py`? Pon un ejemplo de cambio que sí lo necesitaría.
6. ¿Por qué conviene comprobar `huella_datos` antes de comparar dos ejecuciones?
7. El árbol de decisión pierde contra el bosque. ¿Para qué podría servir igualmente?
8. ¿Qué versión del modelo registrado quedó tras deshacer el cambio y volver a entrenar? ¿Se borraron las anteriores?

## Respuestas (para el profesor)

1. **El bosque aleatorio**: valid 0,703 frente a 0,698 de la regresión logística, una diferencia de **0,005**. Es el modelo registrado como versión 2.
2. **Sí**: 0,976 − 0,703 = 0,273 de diferencia. Menos que el gradient boosting (1,000 − 0,663 = 0,337), más que la regresión logística (0,105).
   `min_samples_leaf=5` lo suaviza, pero con 626 filas de train los árboles siguen memorizando mucho.
3. **No a ciegas.** Lo medimos: remuestreando valid al azar 2 000 veces (*bootstrap*), la diferencia bosque − regresión da de media 0,004, con un
   intervalo del 95 % de **−0,043 a +0,049**; el bosque gana en el 57 % de los remuestreos. Es decir, con 114 filas **no se puede distinguir** cuál es
   mejor. La regla «mayor AUC en valid» elige el bosque, pero un equipo prudente preferiría el modelo más simple y explicable mientras no haya más
   datos (con el dato completo de UCI, en S1, ganó la regresión logística). Buena ocasión para decir que la regla automática es un punto de partida, no
   la decisión de negocio.
4. Con test también ganaría el bosque (0,783 frente a 0,747). Pero no se elige con test porque entonces test deja de ser un examen sorpresa: el resultado
   de test del elegido ya no sería una estimación honesta. Que aquí coincidan es casualidad; no se sabe hasta mirar.
5. Porque la huella de entrada de `pipeline_train` incluye **el código de `train.py`** (`control.huella_codigo(train)`): al cambiar el texto del archivo,
   cambia la huella. Necesitaría `--forzar`, por ejemplo, actualizar scikit-learn sin tocar el código, o cambiar algo de otro módulo que no entra en la
   huella. También si se quiere repetir el mismo entrenamiento a propósito.
6. Porque si los datos de entrenamiento cambiaron, una diferencia de AUC puede deberse a los datos y no al modelo. Aquí todas tienen
   `35a94deb4e04ab4a`: la comparación es justa.
7. Para **explicar**: un árbol de profundidad 4 se puede dibujar y leer como reglas. Da 0,668 en valid (más que el gradient boosting, 0,663) con un
   sobreajuste moderado (0,167), y en test pone un 84 % de aciertos en el 10 % mejor. Sirve como modelo de referencia interpretable o para contar a negocio
   qué patrones hay.
8. La **versión 3** (regresión logística). No se borra nada: la 1 (regresión) y la 2 (bosque) siguen en el registro. MLflow guarda la historia; en S4–S5
   el alias de producción dirá cuál se sirve.

---

### Cómo se obtuvieron estas cifras (para el profesor)
- Carpeta temporal en `%TEMP%` con `CURSO_DB_OPERACIONAL`, `CURSO_DB`, `CURSO_MODELOS` y `CURSO_REPORTES` (como `S2-API-y-Docker/practica/extra/capturar.py`),
  así no se tocaron los datos ni el MLflow del proyecto. Secuencia: `python -m ia_mlops.operacional` → `python -m ia_mlops.pipeline` (30,1 s; 22,9 s el
  entrenamiento) → editar `train.py` → `python -m ia_mlops.pipeline_train` (26,5 s) → otra vez («sin cambios») → comparación leída de MLflow con
  `mlflow.search_runs` y en la interfaz (puerto 5001, Chrome) → `git restore` → `python -m ia_mlops.pipeline_train` (19,7 s, versión 3).
- El cuaderno 04 con el mismo cambio se ejecutó **en memoria** (sin modificar el archivo) contra la misma `curso.db`: sin `COLOR_MODELO` falla con
  `KeyError: 'bosque_aleatorio'`; con los colores, completo en 32,3 s y mismas cifras.
- El bootstrap de la respuesta 3 se calculó con las probabilidades de valid de ambos modelos, 2 000 remuestreos con semilla 0.
- Windows 11, Python 3.11.18, scikit-learn 1.9.1, MLflow 3.18.0, 13/11/2026. **No probado en el Codespace.**
