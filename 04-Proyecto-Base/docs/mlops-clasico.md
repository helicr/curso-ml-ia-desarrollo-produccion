# MLOps clásico: deriva, alias y vuelta atrás (S5)

Un modelo en producción no se «termina»: el mundo cambia y el modelo no. Este documento reúne las tres herramientas del proyecto para **vigilar** un modelo y **cambiarlo sin miedo**:

```
 datos de hoy ──▶ deriva de datos (PSI) ──┐
 aciertos reales ▶ deriva de rendimiento ─┼─▶ ¿reentrenar? ─▶ versión nueva en el registro ─▶ alias @champion ─▶ (si falla) volver
                                          └─ ia_mlops/deriva.py                          └─ ia_mlops/alias_modelo.py
```

## Qué es la deriva

- **Deriva de datos:** los clientes de hoy ya no se parecen a los de entrenamiento (por ejemplo, ahora compran menos veces al trimestre). El modelo sigue funcionando, pero extrapola. Se mide **sin necesitar la etiqueta**: basta con los datos de hoy.
- **Deriva de rendimiento:** el modelo acierta menos que antes. Se mide con el **AUC** y **necesita la etiqueta**, que en este caso llega 90 días tarde (hay que esperar a ver si el cliente compró).

Lo primero avisa pronto pero puede dar falsas alarmas (los datos cambian y el modelo sigue bien); lo segundo es la verdad, pero llega tarde. Se miran las dos.

## PSI en un ejemplo pequeño

El **PSI** (*Population Stability Index*) divide cada variable en intervalos con los cuantiles de la referencia y compara qué fracción de clientes cae en cada uno:

`PSI = suma de (q - p) · ln(q / p)`, con `p` = fracción en la referencia y `q` = fracción en el corte actual.

Ejemplo con cuatro clientes y dos intervalos (los calcula `deriva.psi_detalle([1, 2, 3, 4], [1, 1, 1, 4], intervalos=2)`). La mediana de la referencia (2,5) separa los intervalos:

| intervalo | referencia (p) | actual (q) | aporte `(q - p) · ln(q / p)` |
|---|---|---|---|
| hasta 2,5 | 0,50 | 0,75 | 0,1014 |
| más de 2,5 | 0,50 | 0,25 | 0,1733 |
| nulo | 0,0001 | 0,0001 | 0,0000 |
| **PSI** | | | **0,2747** |

- Con la misma muestra en los dos lados el PSI es exactamente 0.
- El intervalo «nulo» existe para que cambie el PSI si de repente faltan más datos; aquí está vacío en los dos lados.
- **Suelo anti-cero:** `ln(q / p)` no existe si un intervalo está vacío, así que las fracciones menores que 0,0001 se suben a 0,0001. Es un parche numérico, no una teoría.
- **Los umbrales son una convención de la industria, no una ley:** menos de 0,10 «estable», de 0,10 a 0,25 «moderado», más de 0,25 «cambio importante». El comando deja cambiar el de alarma con `--umbral-psi`.
- Con pocos clientes (aquí, 109 y 148) el PSI oscila por azar: es un aviso, no una sentencia.

Junto al PSI se muestra el estadístico **KS** (0 = distribuciones iguales, 1 = totalmente separadas), que mira la distancia máxima entre las dos distribuciones acumuladas.

## Los comandos de deriva (solo lectura)

Desde `04-Proyecto-Base`, con la base y el modelo ya creados (`python -m ia_mlops.pipeline`):

```text
python -m ia_mlops.deriva cortes
python -m ia_mlops.deriva datos --referencia 2010-12-01 --actual 2011-12-10 [--umbral-psi 0.25] [--intervalos 10] [--json datos.json]
python -m ia_mlops.deriva rendimiento --cortes 2011-03-01 2011-06-01 2011-09-01 [--tolerancia 0.05] [--json rendimiento.json]
```

Código de salida de `datos` y `rendimiento`: **0** sin deriva relevante · **1** hay deriva (alguna variable supera el umbral, o el AUC cae más que la tolerancia) · **2** error. Así un workflow puede decidir con el código de salida.

### Qué sale (ensayo real con la muestra del repositorio)

`datos` con la referencia en el último corte de entrenamiento y el «ahora» de los datos (2011-12-10, calculado al vuelo con el mismo SQL de la capa FS):

| variable | PSI | KS | estado |
|---|---|---|---|
| antiguedad_dias | 2,830 | 0,736 | deriva |
| recencia_dias | 0,437 | 0,259 | deriva |
| frecuencia_180d | 0,400 | 0,240 | deriva |
| monto_90d | 0,293 | 0,213 | deriva |
| frecuencia_90d | 0,276 | 0,213 | deriva |
| unidades_total | 0,147 | 0,122 | moderada |

(y siete variables más por debajo; `es_reino_unido` queda en 0,000). Salida del comando: código 1, cinco de trece variables por encima de 0,25. Una lectura razonable: `antiguedad_dias` crece para todos los clientes con solo dejar pasar un año, así que su PSI enorme es en parte esperable y no pide por sí solo reentrenar; las variables de actividad reciente (`recencia_dias`, `frecuencia_90d`, `frecuencia_180d`, `monto_90d`) son las que dicen que el comportamiento ha cambiado.

`rendimiento` sobre los cortes con etiqueta:

| corte | uso | AUC |
|---|---|---|
| 2011-03-01 | validación | 0,6982 |
| 2011-06-01 | prueba | 0,7534 |
| 2011-09-01 | prueba | 0,7423 |

Con el primer corte medido como base, el AUC no cae más que la tolerancia (código de salida 0).

**Honestidad al medir:** el modelo se ajustó con los cortes de entrenamiento y se eligió con el de validación; el AUC ahí **sobreestima** (en el último corte de entrenamiento, 2010-12-01, es 0,8497). La orden marca el uso de cada corte (entrenamiento, validación o prueba, leído de `models/metadatos.json` y de `models/referencia.json`) y avisa. La tolerancia de 0,05 es **provisional**: no sale de ninguna medición. Un corte cuya ventana de 90 días no cabe en los datos (como el «ahora») se lista como «sin etiqueta».

## Alias y vuelta atrás

Cada entrenamiento registra una **versión** nueva de `retencion-90d` en MLflow. Un **alias** es un puntero con nombre a una versión: `champion` = «la que manda». **Cambiar de modelo es mover el puntero; deshacer es volver a moverlo. No se borra nada.**

```text
python -m ia_mlops.alias_modelo mostrar                 # versiones, AUC y a qué apunta cada alias
python -m ia_mlops.alias_modelo promover --version 2    # @champion pasa a la v2 y la v2 recuerda cuál era la anterior
python -m ia_mlops.alias_modelo volver                  # rollback: @champion vuelve a la versión anterior
python -m ia_mlops.alias_modelo cargar --alias champion # carga models:/retencion-90d@champion y puntúa un cliente de ejemplo
```

`promover` guarda en la versión nueva la etiqueta `champion_anterior`; `volver` la lee. Varias promociones seguidas dejan una cadena (v3 recuerda a v2, v2 recuerda a v1). Si no hay versión anterior, `volver` falla con un mensaje claro (código de salida 2). El almacén es `models/mlflow.db`, o el de `CURSO_MLFLOW_URI`, o `--uri`.

`cargar` demuestra que **el alias es lo que decide qué modelo se sirve**: el mismo comando carga la v3 o la v2 según dónde esté el puntero.

**Lo que el alias gobierna y lo que no.** La imagen Docker de la API copia `models/modelo_mlflow` y **no lee el registro**: mover `champion` cambia el registro y a quien cargue por alias, no la API ya desplegada. Un sistema real los uniría exportando la versión champion a `models/modelo_mlflow` en el workflow, construyendo y publicando la imagen con esa versión en su etiqueta y desplegándola (o haciendo que la API cargue por alias al arrancar). Aquí no se implementa.
