# Ejercicios S1 · La tarea resuelta: añadir una variable y decidir con evidencia

Solución del profesor de la [tarea de S1](../../S1-Datos-y-Entrenamiento/tarea/README.md), para explicarla en clase **después de la entrega** (mié 18/11, 10:00 hora de Perú). Variable elegida: **`ratio_devoluciones`** (devoluciones por cada factura con venta). Se eligió esta y no `monto_180d` porque el enunciado ya da el resultado de `monto_180d` como referencia.

**Todo lo que sigue es una ejecución real** en Windows 11 el 13/11/2026, con la muestra del curso (150 clientes), en una copia aparte del repositorio y con las bases y MLflow en una carpeta temporal. Las salidas completas están en [`salidas/`](salidas/).

| Archivo | Qué es |
|---|---|
| [`decision-ratio-devoluciones.md`](decision-ratio-devoluciones.md) | La plantilla de decisión de la tarea, rellenada: lo que entregaría un alumno |
| [`solucion-ratio-devoluciones.patch`](solucion-ratio-devoluciones.patch) | Los cambios exactos en los seis sitios de la receta (`git apply`) |
| [`traduccion/04_entrenamiento_y_seguimiento.py`](traduccion/04_entrenamiento_y_seguimiento.py) | El cuaderno 04 modificado, traducido con `jupytext` (paso 6 de la tarea) |
| [`scripts/comparar_en_mlflow.py`](scripts/comparar_en_mlflow.py) | Tabla de las ejecuciones de MLflow (antes y después) y descripción de la variable |
| [`scripts/bootstrap_auc.py`](scripts/bootstrap_auc.py) | ¿La mejora es mayor que el ruido? Compara las versiones 1 y 2 del modelo registrado |
| [`salidas/`](salidas/) | Las salidas reales: pipeline antes y después, comparación, *bootstrap* y pruebas |

---

## 1. La variable (5 min en clase)
- **Nombre:** `ratio_devoluciones`.
- **Fórmula:** facturas de cancelación antes del corte ÷ facturas con venta antes del corte = `devoluciones / frecuencia`.
- **Sin fuga:** las dos partes ya existen en FS y ya cumplen la regla de oro (`fecha_factura < :corte`). Como `frecuencia ≥ 1` (sin historia no hay fila en FS), no hay división por cero.
- **Por qué podría ayudar:** `devoluciones` es un número absoluto: un cliente con 50 facturas y 2 devoluciones no es como uno con 2 facturas y 2 devoluciones. La ratio mide la **proporción** de compras que acaban en devolución, que podría indicar insatisfacción.
- **Ojo, puede pasar de 1:** en train el máximo es **2,0**. Un cliente puede tener más facturas de cancelación que de venta (por ejemplo, cancela varias veces partes de una misma compra). No es un error del cálculo; conviene decirlo en el catálogo.

## 2. Dónde se toca: los seis sitios (10 min, con el parche abierto)
Exactamente la receta de la tarea. En total, 12 líneas añadidas y 7 cambiadas:

| Archivo | Cambio |
|---|---|
| `sql/fs/01_crear_fs.sql` | fila en `fs_catalogo` (`'ratio_devoluciones'`, descripción, `'devoluciones / frecuencia'`, `'devoluciones por factura'`) y columna `ratio_devoluciones REAL` en `fs_cliente_corte` |
| `sql/fs/02_poblar_fs.sql` | columna en el `INSERT` y, en el `SELECT`, `ROUND(COALESCE(d.devoluciones, 0) * 1.0 / p.frecuencia, 4)` |
| `sql/ml/01_crear_ml.sql` | columna `ratio_devoluciones REAL` en `ml_dataset` |
| `sql/ml/02_poblar_ml.sql` | columna en el `INSERT` y `fs.ratio_devoluciones` en el `SELECT` |
| `ia_mlops/config.py` | `'ratio_devoluciones'` al final de `FEATURES` |
| `notebooks/04_entrenamiento_y_seguimiento.ipynb` | lo mismo en la lista `FEATURES` de la celda de parámetros |

Dos detalles que explicar:
- **`* 1.0`**: en SQLite, entero entre entero es división entera (`1 / 3 = 0`). Sin él, casi todas las ratios saldrían 0.
- **`COALESCE(d.devoluciones, 0)`**: la CTE `devoluciones` solo tiene a los clientes con alguna cancelación; el resto llega como NULL por el `LEFT JOIN`.

Para aplicarlo en tu copia: `git apply 01-Sesiones/ejercicios/ejercicios-s1/solucion-ratio-devoluciones.patch` (desde la raíz del repositorio).

## 3. Reconstruir y reentrenar (5 min)
```bash
cd 04-Proyecto-Base
python -m ia_mlops.pipeline
```
```text
[pipeline_ingesta_raw] sin cambios: la entrada es la misma que en la ultima ejecucion (a3e0551c3461). Usa --forzar para rehacerlo.
[pipeline_ingesta_master] sin cambios: la entrada es la misma que en la ultima ejecucion (d31efa33ae66). Usa --forzar para rehacerlo.
[pipeline_ml] ejecutando (huella de entrada d278a74b9437)
[pipeline_train] ejecutando (huella de entrada 1d00448ff637)
  regresion_logistica        AUC valid 0.699 | test 0.748 | precision media test 0.659
  gradient_boosting          AUC valid 0.665 | test 0.731 | precision media test 0.641
  Mejor modelo: regresion_logistica. Guardado en …\models\modelo.joblib
  Registrado en MLflow como «retencion-90d», version 2.
```
**Lo que hay que señalar:** RAW y MASTER dicen «sin cambios», porque su entrada no cambió. FS → ML y el entrenamiento se rehacen **solos**, sin `--forzar`, porque cambió su código (los SQL y `config.py` entran en la huella).

## 4. Comparar en MLflow (10 min)
Las dos ejecuciones `MEJOR-regresion_logistica` (antes y después), leídas de MLflow (`scripts/comparar_en_mlflow.py`):

| | Sin la variable (versión 1) | Con la variable (versión 2) |
|---|---|---|
| `huella_datos` | `35a94deb4e04ab4a` | `2befaf80246b5f98` (**cambió**: los datos tienen una columna más) |
| Variables | 13 | 14 |
| AUC train | 0,8033 | 0,8029 |
| **AUC valid** | **0,6982** | **0,6991** (+0,0009) |
| AUC test | 0,7471 | 0,7477 (+0,0006) |
| Precisión media test | 0,6589 | 0,6594 |
| Aciertos en el 10 % mejor (test) | 0,88 | 0,88 |

El gradient boosting se mueve en direcciones opuestas: valid de 0,6628 a 0,6647 y test de 0,7354 a 0,7313.

**¿Son comparables?** Sí. Mismas particiones (626 / 114 / 250 filas), mismos cortes, mismos modelos y misma semilla; solo cambia la variable. La huella distinta es la esperada: es justo lo que cambiamos. La rúbrica pide decirlo.

## 5. ¿La mejora es real? (10 min: la parte más importante)
**Sola, la variable es muy informativa.** En train, los clientes con alguna devolución recompran el **79 %** de las veces, frente al **35 %** de los que no tienen ninguna (`salidas/comparacion.txt`).

**Pero el modelo casi no la usa.** Su coeficiente en la regresión logística, con las variables escaladas, es **0,035**, frente a **0,768** el de `devoluciones`. La información ya estaba: `ratio_devoluciones` se calcula con `devoluciones` y `frecuencia`, que el modelo ya tenía (la correlación con `devoluciones` en train es 0,495). Quien devuelve es, sobre todo, quien compra mucho.

**Y la mejora no se distingue del ruido.** *Bootstrap* pareado de 2 000 remuestreos sobre las filas de valid y test (`scripts/bootstrap_auc.py`):

| | Diferencia de AUC | Intervalo del 95 % | Remuestreos en los que mejora |
|---|---|---|---|
| valid (114 filas) | +0,0009 | [−0,0000, +0,0031] | 81 % |
| test (250 filas) | +0,0006 | [−0,0009, +0,0024] | 76 % |

El intervalo llega a 0: con 114 filas de valid, una milésima es indistinguible de la casualidad. (Test se mira **una sola vez**, al final, para informar; la decisión se toma con valid.)

## 6. La decisión: **no se queda**
- **Métricas:** +0,0009 en valid, dentro del ruido; el modelo apenas la usa.
- **Coste:** una columna más en seis archivos y en el contrato de la API (ver el punto 7). Cada variable es código que hay que mantener, documentar y vigilar.
- **Riesgo:** ninguno de fuga (la prueba lo confirma), pero la ratio puede pasar de 1 y habría que documentarlo.
- **Qué haría con más tiempo:** repetirlo con el **dato completo** (4 512 filas de valid en vez de 114: ahí una milésima sí sería medible) y probar una variable que aporte algo nuevo, por ejemplo `dias_desde_ultima_devolucion` (*cuándo*, no *cuánto*).

> **El mensaje de la clase:** una variable puede estar muy relacionada con el objetivo y aun así **no aportar nada al modelo**, porque lo que dice ya lo dicen otras. Por eso se decide con la comparación del modelo entero, no con la tabla de la variable sola. Un «no» bien argumentado vale tanto como un «sí».

## 7. Las pruebas: lo que va a ver el alumnado
```bash
python -m pytest tests -k futuro -q     # 2 passed: no hay fuga
python -m pytest -q                     # 22 failed, 109 passed
```
**Los 22 fallos son todos de la API**: 15 de `test_api.py`, 4 de los casos del laboratorio, 1 de `comparar`, 1 de la explotación y 1 de la imagen. Ni uno de datos o de entrenamiento: la prueba de equivalencia de los cuadernos pasa. El modelo nuevo tiene 14 variables y el contrato de la API, 13, así que `/listo` responde **503** con:
```text
El esquema de la API no coincide con la firma del modelo. Faltan en la API: ['ratio_devoluciones']. Sobran en la API: []
```
Es la protección de S2 funcionando: mejor no arrancar «listo» que predecir con las columnas equivocadas. **Hacer entrar la variable en la API es la tarea de S2 (ruta A).** Para S1 basta con entregar la salida y explicarla. El enunciado de la tarea de S1 se escribió antes de que el proyecto incluyera la API; ahora lo dice.

## 8. Deshacer
Como la decisión es «no», se vuelve atrás:
```bash
git restore 04-Proyecto-Base/sql 04-Proyecto-Base/ia_mlops/config.py 04-Proyecto-Base/notebooks/04_entrenamiento_y_seguimiento.ipynb
python -m ia_mlops.pipeline            # vuelve a 13 variables: ML y el entrenamiento se rehacen solos (versión 3 en MLflow)
python -m pytest -q -m "not lento"     # 127 passed, 4 deselected
```

## Preguntas para la clase
1. ¿Por qué RAW y MASTER dicen «sin cambios» y FS sí se rehace?
2. ¿Por qué hace falta `* 1.0` en SQLite? ¿Qué saldría sin él?
3. La variable separa muy bien recompra / no recompra por sí sola (79 % frente a 35 %). ¿Por qué el modelo no mejora?
4. La huella del dato cambió. ¿Invalida eso la comparación? ¿Cuándo sí la invalidaría?
5. ¿Qué cambiaría en la conclusión con el dato completo?
6. ¿Por qué fallan 22 pruebas que no tienen nada que ver con la variable, y por qué es bueno que fallen?

## Cómo se puntuaría con la rúbrica
- **Reproducibilidad (20):** parche, comandos en orden y salidas → reproducible por un tercero.
- **Técnica (40):** sin fuga (`-k futuro` en verde), catálogo actualizado, ML reconstruido, traducción con `jupytext`, equivalencia en verde y dos ejecuciones comparables. Los 22 fallos de la API, explicados, no restan: son esperables.
- **Análisis (40):** dice que la huella cambió y por qué; mira valid y test; mide el ruido; decide «no» con razones, coste y alternativa.

## Qué se probó
- **Ejecutado** (Windows 11, 13/11/2026, muestra): los pasos 2 a 8, el parche (`git apply --check` sobre `develop`), `jupytext`, `pytest -k futuro` (2 passed) y `pytest -q` con la variable (22 failed, 109 passed, todos los fallos en la API) y los dos scripts.
- **Sin probar:** la misma variable con el dato completo.
