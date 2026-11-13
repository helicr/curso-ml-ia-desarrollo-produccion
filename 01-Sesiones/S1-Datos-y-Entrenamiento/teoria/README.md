# Teoría S1 (60 min) · resumen y glosario

Corresponde a las diapositivas 4–16.

## 1. El caso
Online Retail II (UCI, CC BY 4.0): 1 067 371 líneas de factura de una tienda online británica, 01/12/2009–09/12/2011. Pregunta: dado un cliente y una fecha de corte, ¿comprará en los 90 días siguientes?

## 2. Las capas
| Capa | Qué es | Regla |
|---|---|---|
| OPERACIONAL | `retail.db`: el sistema de ventas simulado, normalizado (clientes, productos, facturas, líneas) | El pipeline lo lee, nunca escribe en él |
| RAW | Copia fiel de cada tabla del operacional + linaje (`_carga_id`, clave de origen) y huella en `raw_carga` | No se edita |
| MASTER | Dato depurado y relacional (clientes, productos, facturas, líneas) | Todo lo descartado queda en `master_descartes` con su motivo; `raw = master + descartes` |
| FS | Variables por cliente y corte (`fs_cliente_corte`) + `fs_catalogo` | Solo datos **anteriores** al corte |
| ML | Variables + objetivo `y` + partición | Ventanas de objetivo que no se solapan |

Cada capa se puede borrar y regenerar desde la anterior.

## 3. Calidad
Reglas duras (detienen el pipeline), alertas (se revisan) e informativas (se vigilan). Resultado en `master_calidad`.

## 4. Sin fuga de información
La **fuga** ocurre cuando una variable usa información que no existiría al momento de predecir. Protección: todos los filtros de FS usan `fecha_factura < :corte` y una prueba borra el futuro y comprueba que las variables no cambian.

## 5. Partición temporal
Train 2010-06…2010-12 (mensual), valid 2011-03, test 2011-06 y 2011-09. Imita el uso real: entrenar con el pasado y predecir el futuro.
**Honestidad:** en este caso una partición aleatoria dio un AUC *más bajo* (media 0,766) que la temporal (0,796); no inflaba la métrica. La temporal se elige por fidelidad al uso real y porque la tasa de recompra cambia (48 % → 35 % → 38 %).

## 6. Entrenamiento
Referencia sin aprender (AUC 0,5), regresión logística y gradient boosting. En el dato completo: logística valid 0,786 · test 0,796; gradient boosting 0,761 · 0,781 (train 0,842: sobreajuste). Se elige con valid y se informa test una sola vez.

## 7. MLflow (tracking)
Parámetros, métricas, modelo con firma y huella del dato. Comparar ejecuciones solo si la huella coincide.

## 8. Del cuaderno al paquete
Los cuadernos son el pipeline; `ia_mlops` es su traducción y se prueba que dan resultados idénticos.

## Glosario
- **AUC:** probabilidad de que un cliente que recompra tenga mayor puntuación que uno que no. 0,5 = azar.
- **Corte:** fecha desde la que se predice.
- **Huella de datos:** sha256 del dataset de entrenamiento.
- **Ingesta:** copia de los datos del sistema de origen a RAW.
- **Linaje:** camino que permite volver a la fila original.
- **Sistema operacional (OLTP):** la base con la que funciona el negocio; el pipeline la lee y no escribe en ella.
- **Fuga:** uso de información que no existiría al predecir.
- **Sobreajuste:** buen resultado en train, peor en datos nuevos.
