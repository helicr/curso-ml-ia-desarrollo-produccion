# Práctica 3: PySpark con Dataproc sin servidor

## Objetivo
Ejecutar un job de **PySpark** sobre nuestros datos sin montar un clúster: se sube a Cloud Storage el CSV de líneas de venta que genera el pipeline del proyecto (`master_lineas` + `master_facturas` de `curso.db`), un **lote (batch) de Dataproc sin servidor** lo procesa y deja el resultado en Cloud Storage:

- `por_pais`: facturas, clientes distintos, monto total y ticket medio por país (solo ventas válidas).
- `rfm`: recencia, frecuencia y monto por cliente.

Después se comprueba que Spark da lo mismo que un cálculo local en Python (paridad).

- **Tiempo estimado:** 15-25 min (estimado, sin medir; un lote suele tardar minutos por arrancar y terminar).
- **Coste aproximado:** sin dato ([Dataproc sin servidor](https://cloud.google.com/dataproc-serverless/pricing) cobra por recursos y tiempo del lote; el dato es pequeño, 22 117 líneas).
- **Región:** `southamerica-west1` para el bucket y el lote. **Dataproc sin servidor funcionó en Santiago** (probado el 25/11/2026 en la cuenta del curso). Si en tu cuenta falla por región, `export CURSO_REGION_SPARK=southamerica-east1` y repite (el bucket se crea en esa región).
- **Runtime:** `2.3` (LTS, soporte hasta 2027/11/26, [tabla oficial](https://docs.cloud.google.com/dataproc-serverless/docs/concepts/versions/spark-runtime-versions)). El runtime por defecto es 2.2 y el más reciente es 4.0.

## Qué crea
| Recurso | Nombre |
|---|---|
| Bucket de Cloud Storage (sin acceso público) | `project-curso-ml-ia-curso-ml-dataproc` |
| Lote de Dataproc sin servidor | `curso-ventas-AAAAMMDD-HHMMSS` (etiqueta `curso=ml-ia`) |
| Rol `roles/dataproc.worker` a la cuenta de Compute por defecto | solo si no lo tenía; `borrar.sh` lo quita (marca local en `~/.curso-ml-gcp/`) |
| **Dos buckets que crea Dataproc él solo** | `dataproc-staging-<región>-<nº de proyecto>-…` y `dataproc-temp-…`: no los crea `crear.sh`, y quedan con restos del lote. `borrar.sh` los borra **solo si ya no queda ningún lote ni clúster de Dataproc en la región** (son compartidos por todo el Dataproc del proyecto) |

Red: el lote usa la subred `default` de la región; Dataproc sin servidor activa en ella el acceso privado a las APIs de Google ([documentación](https://docs.cloud.google.com/dataproc-serverless/docs/concepts/network)). Si la organización no tiene red `default`, ver «Si falla».

## Pasos
1. **Cloud Shell:** `./crear.sh` (exporta el CSV, crea el bucket, sube datos y `analisis_ventas.py`, lanza el lote y espera).
2. **Cloud Shell:** `./probar.sh` (estado `SUCCEEDED`, ficheros de salida, primeras filas y comprobación contra el cálculo local).
3. En la **web de la consola:** menú ☰ > Dataproc > Lotes (batches) para ver el lote y sus registros.
4. **Cloud Shell:** `./borrar.sh`.

## Qué debes ver
- `exportar_datos.py`: `22117 lineas exportadas` (con la muestra del repositorio; si ejecutas con otros datos, otra cifra).
- `probar.sh`: `estado: SUCCEEDED`; en `salida/por_pais/` y `salida/rfm/` un fichero `part-….csv` (+ `_SUCCESS`); la tabla de países ordenada por monto; y `OK: N paises; facturas, clientes y monto coinciden con el calculo local.`
- `borrar.sh`: sin lotes, sin el bucket de la práctica y sin los dos buckets `dataproc-staging-…` / `dataproc-temp-…` (la última lista debe decir «ningun bucket de la practica ni de Dataproc»). Si tu proyecto tiene otros lotes o clústeres de Dataproc, los deja y lo avisa.

## Si falla
| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| `INVALID_ARGUMENT` o «location not supported» | Dataproc sin servidor no disponible en Santiago | `export CURSO_REGION_SPARK=southamerica-east1` y repetir |
| Lote `FAILED` con error de permisos | Falta `roles/dataproc.worker` en la cuenta de Compute por defecto | Lo concede `crear.sh`; si la organización lo impide, pedirlo al administrador |
| Error de red / subred `default` inexistente | La organización no crea la red por defecto | Crear una subred con acceso privado a Google o indicar `--subnet` (editar `crear.sh`; sin verificar) |
| `ModuleNotFoundError: pyspark` en Cloud Shell | Normal si ejecutas `analisis_ventas.py` allí | El job corre dentro de Dataproc, no en Cloud Shell |
| El nombre del bucket ya existe | Los nombres son globales | Cambiar `NOMBRE_BUCKET` en `variables.sh` |
| El flag `--batch` o `--labels` no existe en tu `gcloud` | Versión distinta | `gcloud dataproc batches submit pyspark --help` y ajustar; **sin verificar** (la guía oficial solo muestra `submit spark`) |

## Fuentes
- Lotes: https://docs.cloud.google.com/dataproc-serverless/docs/quickstarts/spark-batch (muestra `submit spark` con `--region`, `--version`, `--deps-bucket`, `--subnet`; la variante `pyspark` y `--batch` **sin verificar** en esa página)
- Red: https://docs.cloud.google.com/dataproc-serverless/docs/concepts/network
