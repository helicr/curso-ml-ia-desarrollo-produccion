# Práctica 4: nuestro modelo en Vertex AI (registro, endpoint, predicción online)

## Objetivo
Registrar el modelo de retención en el **Model Registry** de Vertex AI, desplegarlo en un **endpoint** (un servicio HTTPS gestionado), pedirle una predicción online y **deshacerlo todo** (undeploy → endpoint → modelo → bucket).

- **Tiempo estimado:** 30-45 min (estimado, sin medir; el despliegue del endpoint es lo más lento).
- **Coste aproximado:** sin dato ([precios de Vertex AI](https://cloud.google.com/vertex-ai/pricing)). Un endpoint cobra **mientras tenga un modelo desplegado**, aunque no reciba peticiones: ejecuta `borrar.sh` en cuanto acabes. Máquina mínima usada: `e2-standard-2`, 1 réplica.
- **Región:** `southamerica-west1` (Santiago admite Model Registry, entrenamiento y predicción online de modelos propios: [fuente](https://docs.cloud.google.com/vertex-ai/docs/general/locations)).

## Un detalle de versiones (importante)
El proyecto usa **scikit-learn 1.9.1**. Los contenedores pre-construidos de Vertex solo llegan a la **1.6** (tabla oficial el 25/11/2026: 1.6, 1.5 y 1.4 con imágenes; [fuente](https://docs.cloud.google.com/vertex-ai/docs/predictions/pre-built-containers)). Un modelo guardado con una versión no debe abrirse con otra, así que `crear.sh` **reentrena el mismo modelo** (misma regresión logística, mismo código `ia_mlops.modeling.train.modelos`, mismos datos, mismas 13 variables) con scikit-learn 1.6.1 en un entorno aparte, y imprime su AUC de validación junto al del modelo del proyecto: deben ser casi iguales. Que el parche 1.6.1 coincida con el del contenedor: **sin verificar**.

## Qué crea
| Recurso | Nombre |
|---|---|
| Bucket (sin acceso público) con `modelo/model.joblib` | `project-curso-ml-ia-curso-ml-vertex` |
| Modelo en el Model Registry (contenedor `us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-6:latest`) | `retencion-90d-sklearn` |
| Endpoint | `retencion-90d-endpoint` |
| Despliegue (1 réplica `e2-standard-2`) | `retencion-90d-v1` |

El contenedor lo sirve cualquier prefijo (`us`, `europe`, `asia`); la etiqueta debe ser `latest` (así lo exige la documentación). `model.joblib` es el nombre exacto que exige Vertex para scikit-learn.

## Formato de entrada
`{"instances": [ [13 números], … ]}`: cada instancia es una **lista de números en el orden del modelo** (el de `ia_mlops.config.FEATURES` y `models/metadatos.json`), no un diccionario:

| Posición | Variable | Ejemplo (cliente `activo`) |
|---|---|---|
| 1 | `recencia_dias` | 35 |
| 2 | `frecuencia` | 6 |
| 3 | `monto_total` | 1250.4 |
| 4 | `ticket_medio` | 208.4 |
| 5 | `unidades_total` | 410 |
| 6 | `productos_distintos` | 38 |
| 7 | `antiguedad_dias` | 310 |
| 8 | `frecuencia_90d` | 2 |
| 9 | `monto_90d` | 380.5 |
| 10 | `frecuencia_180d` | 4 |
| 11 | `dias_medios_entre_compras` | 55.0 |
| 12 | `devoluciones` | 1 |
| 13 | `es_reino_unido` | 1 |

Con el cliente `activo`, la petición es `{"instances": [[35.0, 6.0, 1250.4, 208.4, 410.0, 38.0, 310.0, 2.0, 380.5, 4.0, 55.0, 1.0, 1.0]]}` (la genera `crear.sh` en `/tmp/curso-vertex/instancias.json`). Si cambias el orden, el modelo no avisa: devuelve otra cosa. **Sin verificar:** cómo trata el contenedor un valor ausente en `dias_medios_entre_compras` (en la API de S2 va `null` para clientes de una sola factura; aquí los dos ejemplos tienen valor).

## Pasos
1. **Cloud Shell:** `./crear.sh` (reentrena, sube, registra, crea el endpoint y despliega).
2. **Cloud Shell:** `./probar.sh` (`gcloud ai endpoints predict` y comparación con el modelo en local). También puedes mirarlo en la **web de la consola:** menú ☰ > Vertex AI > Model Registry / Predicción en línea.
3. **Cloud Shell, sin dejarlo para después:** `./borrar.sh`.

## Qué debes ver
- `crear.sh`: `scikit-learn 1.6.1 … AUC valid = 0.69xx` junto al `AUC valid del modelo del proyecto … 0.6982` (casi iguales), `Created Vertex AI endpoint`, y al desplegar `Deployed a model to the endpoint`.
- `probar.sh`: una respuesta `predictions` con un valor por cliente. **Comprobado el 25/11/2026 (laboratorio Cloud Journey):** el contenedor pre-construido llama a `predict()` y devuelve la **clase** (0 o 1), no la probabilidad; `comparar_respuesta.py` la compara con la clase del modelo en local y muestra también su probabilidad. Si el contenedor devolviera probabilidades, también lo acepta. Para servir la probabilidad desde Vertex haría falta un contenedor propio (rutina de predicción personalizada); no se hace aquí.
- `borrar.sh`: `undeploy`, endpoint y modelo borrados, bucket fuera, y los listados `ai endpoints list` y `ai models list` vacíos.

## Si falla
| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| Error de versión o `InconsistentVersionWarning` en los registros del endpoint | El contenedor tiene otro parche de scikit-learn | Mira los registros: menú ☰ > Vertex AI > Predicción en línea > endpoint > Registros; cambia `VERSION_SKLEARN` en `variables.sh` y repite `crear.sh` tras `borrar.sh` |
| Fallo al cargar `model.joblib` por numpy | Pickle con numpy distinto al del contenedor | Se fija numpy 1.26.4; ajusta `VERSION_NUMPY` |
| `Quota` o «insufficient resources» al desplegar | Cuota de CPU del proyecto o de la región | Pedir cuota o probar otra máquina (`MAQUINA`) |
| `PERMISSION_DENIED` al registrar el modelo | Falta `roles/aiplatform.user` o acceso al bucket | Pedir el rol al administrador |
| `--endpoint-id` o `--model-id` desconocidos | `gcloud` antiguo | `gcloud components update`; en último caso sin esos flags y leyendo los IDs de la salida (**sin verificar**) |
| `borrar.sh` no puede borrar el endpoint | Aún tiene un modelo desplegado | Repite `./borrar.sh`; o consola: Predicción en línea > endpoint > Deshacer despliegue |

## Fuentes
- Contenedores pre-construidos (versiones y URI): https://docs.cloud.google.com/vertex-ai/docs/predictions/pre-built-containers
- Exportar el artefacto (`model.joblib`): https://docs.cloud.google.com/vertex-ai/docs/training/exporting-model-artifacts
- Formato de la petición y `gcloud ai endpoints predict --json-request`: https://docs.cloud.google.com/vertex-ai/docs/predictions/get-online-predictions
- `models upload`: https://docs.cloud.google.com/sdk/gcloud/reference/ai/models/upload · `endpoints deploy-model`: https://docs.cloud.google.com/sdk/gcloud/reference/ai/endpoints/deploy-model
- Tipos de máquina: https://docs.cloud.google.com/vertex-ai/docs/predictions/configure-compute
