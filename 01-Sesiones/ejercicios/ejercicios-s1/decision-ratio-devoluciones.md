# Evidencia S1 · decisión sobre la variable nueva

**Nombre:** solución del profesor  **Fecha:** 13/11/2026  **Rama / carpeta:** copia aparte de `develop` (cambios en `solucion-ratio-devoluciones.patch`)

## 1. La variable
- Nombre: `ratio_devoluciones`
- Fórmula (solo con datos anteriores al corte): facturas de cancelación antes del corte ÷ facturas con venta antes del corte (`devoluciones / frecuencia`, con `frecuencia ≥ 1`). Puede pasar de 1 (en train, máximo 2,0).
- Por qué podría ayudar a predecir la compra en 90 días: `devoluciones` es un recuento absoluto; la proporción de compras que acaban en devolución podría reflejar insatisfacción, independientemente de cuánto compre el cliente.

## 2. Dónde la implementé
Archivos modificados: `sql/fs/01_crear_fs.sql` (catálogo y columna), `sql/fs/02_poblar_fs.sql` (cálculo), `sql/ml/01_crear_ml.sql`, `sql/ml/02_poblar_ml.sql`, `ia_mlops/config.py` (`FEATURES`) y `notebooks/04_entrenamiento_y_seguimiento.ipynb` (`FEATURES`). Traducción: `traduccion/04_entrenamiento_y_seguimiento.py` (`jupytext --to py:percent`).

## 3. Pruebas
```
python -m pytest tests -k futuro -q
2 passed, 129 deselected

python -m pytest -q
22 failed, 109 passed
(los 22 son de la API: el contrato tiene 13 variables y el modelo 14; /listo da 503 con
 «Faltan en la API: ['ratio_devoluciones']». La prueba de equivalencia de los cuadernos pasa.)
```

## 4. Comparación en MLflow
| | Sin la variable | Con la variable |
|---|---|---|
| Ejecución | `MEJOR-regresion_logistica` · versión 1 | `MEJOR-regresion_logistica` · versión 2 |
| `huella_datos` | `35a94deb4e04ab4a` | `2befaf80246b5f98` (sí cambió: una columna más) |
| AUC valid | 0,6982 | 0,6991 |
| AUC test | 0,7471 | 0,7477 |
| Precisión media test | 0,6589 | 0,6594 |

## 5. Decisión
¿La variable se queda? **No**
Razones:
- La mejora en valid es de +0,0009 y el intervalo del 95 % del *bootstrap* (2 000 remuestreos) va de −0,0000 a +0,0031: no se distingue del ruido con 114 filas.
- El modelo casi no la usa (coeficiente escalado 0,035, frente a 0,768 de `devoluciones`), porque repite información que ya dan `devoluciones` y `frecuencia`.
- Mantenerla cuesta: seis archivos, el catálogo y el contrato de la API.
- No hay riesgo de fuga: la prueba de `futuro` pasa.

## 6. Límites y riesgos
- Probado solo con la muestra (114 filas en valid). Con el dato completo (4 512) una diferencia de este tamaño sí podría medirse: es lo primero que repetiría.
- Si se conservara, habría que actualizar el contrato de la API (tarea de S2) y documentar que puede ser mayor que 1.
- Alternativa: una variable que aporte información nueva, como `dias_desde_ultima_devolucion` (cuándo, no cuánto).

## 7. Dificultades
- Con la API de S2 en el proyecto, `pytest -q` no queda en verde al añadir una variable: 22 pruebas de la API fallan a propósito. No es un error de la variable.
- La división en SQLite: sin `* 1.0`, `devoluciones / frecuencia` es división entera y casi todo sale 0.

## 8. Reproducir
1. `git apply 01-Sesiones/ejercicios/ejercicios-s1/solucion-ratio-devoluciones.patch` (desde la raíz del repositorio)
2. `cd 04-Proyecto-Base` y `python -m ia_mlops.pipeline` (antes conviene haber entrenado sin la variable, para tener la versión 1)
3. `python ../01-Sesiones/ejercicios/ejercicios-s1/scripts/comparar_en_mlflow.py`
4. `python ../01-Sesiones/ejercicios/ejercicios-s1/scripts/bootstrap_auc.py --antes 1 --despues 2`
5. `python -m pytest tests -k futuro -q` y `python -m pytest -q`
6. Deshacer: `git restore 04-Proyecto-Base/sql 04-Proyecto-Base/ia_mlops/config.py 04-Proyecto-Base/notebooks/04_entrenamiento_y_seguimiento.ipynb`

## 9. Ayuda recibida
Preparada por el profesor con ayuda de un asistente de IA (Claude) para la ejecución y la redacción.
