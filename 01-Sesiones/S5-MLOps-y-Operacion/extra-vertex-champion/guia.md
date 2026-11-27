# Extra de S5 · Del alias `champion` de MLflow a un endpoint de Vertex AI, desplegado desde GitHub Actions

Guía paso a paso. Cada orden se copia y se pega; después de cada una hay **qué debes ver** (las salidas marcadas «real» son de una ejecución del 27/11/2026 en este equipo, ver [`salidas/`](salidas)) y **si falla**. La presentación es [`index.html`](index.html) (⌂ Índice vuelve a [S5](../index.html)).

> **Qué está probado y qué no, en una frase.** Está **ejecutado de verdad** todo lo que corre en un portátil sin nube: el adaptador (contrato de Vertex, paridad exacta con el modelo de MLflow, errores), el manifiesto y las etiquetas, el contexto de la imagen, los scripts de `scripts/` (contra un `gcloud` **simulado**) y los tres workflows (YAML, permisos, órdenes). **No se ha ejecutado** — está **sin verificar** — nada en Google Cloud real (Vertex AI, Artifact Registry, WIF), ni en GitHub Actions, ni con Docker (este portátil no tiene). El ensayo real, con borrado inmediato, está descrito al final (apartado 9) y en [`capturas-pendientes.md`](capturas-pendientes.md).

## 0. La idea en un minuto

| En MLflow (S5 · MLOps clásico) | En Vertex AI | Cómo se enlazan |
|---|---|---|
| Modelo registrado `retencion-90d` | **Modelo** `retencion-90d-champion` en el Model Registry | mismo nombre de negocio; etiqueta `mlflow_modelo` |
| **Versión** 6 | **Versión** (1, 2, 3…) del mismo modelo | alias de Vertex `mlflow-v6` y etiqueta `mlflow_version=6` |
| Alias `champion` | alias `champion` de la versión de Vertex + el **tráfico** del endpoint | el alias de Vertex sigue a MLflow; lo que sirve es el reparto de tráfico |
| `promover` / `volver` | `desplegar` + `promover` / `volver` (mover el tráfico) | `scripts/volver.sh` hace las dos cosas |
| Huella de los datos y AUC | etiquetas `huella_datos`, `auc_valid`, `auc_test` | `manifiesto_champion.py` |
| — | **Endpoint**: el servicio HTTPS; **cobra mientras tenga un modelo desplegado** | `scripts/borrar.sh` |

**La diferencia con la práctica 04 de S4:** allí el modelo se reentrenó con scikit-learn 1.6 para usar el contenedor **pre-construido** de Vertex, que llama a `predict()` y devuelve la **clase** (0 o 1). Aquí la imagen es **propia**: lleva el modelo del champion con **scikit-learn 1.9.1** (el del proyecto) y devuelve la **probabilidad**, la clase y el tramo de negocio.

```
MLflow  (alias champion → versión N)
   │  manifiesto_champion.py generar          →  vertex-manifiesto.json  (versión, AUC, huella, etiquetas)
   │  preparar_contexto.py                    →  build/vertex/  (adaptador + modelo EXACTO de la versión N)
   ▼
imagen retencion-vertex:vN-<huella>  ──►  Artifact Registry (regional, misma región que el endpoint)
   ▼
Model Registry: NUEVA VERSIÓN del modelo (--parent-model, alias champion y mlflow-vN, etiquetas)
   ▼
Endpoint: deploy-model en CANARIO (10 %) ─► probar (paridad) ─► promover (100 %) ─► [volver = mover el tráfico atrás]
```

## 1. Qué hace cada pieza

| Archivo | Para qué |
|---|---|
| `imagen/vertex_adaptador.py` | FastAPI que cumple el contrato de Vertex: ruta de salud, ruta de predicción, `{"instances": [[13 números]]}` → `{"predictions": [{probabilidad, clase, tramo, version_mlflow}]}` |
| `imagen/Dockerfile.vertex` | La imagen: mismo `requirements-api.lock` que la API, el adaptador y el modelo dentro; sin variables `AIP_*` |
| `manifiesto_champion.py` | Lee el registro de MLflow, escribe `vertex-manifiesto.json` y las etiquetas; `puerta` (calidad); `anotar` escribe en MLflow dónde está en Vertex |
| `preparar_contexto.py` | Reúne en `build/vertex/` lo que necesita `docker build` (no depende de cómo se construya la API) |
| `instancias.py`, `comparar_paridad.py` | Las 13 variables en el orden del modelo; compara Vertex con el modelo local |
| `vertex_ayuda.py` | Lee el JSON de `gcloud` y calcula el reparto de tráfico (sin `jq`) |
| `scripts/*.sh` | `preparar_gcp`, `subir_modelo`, `desplegar`, `probar`, `promover`, `volver`, `borrar` (idempotentes) |
| `vertex-desplegar.yml`, `vertex-rollback.yml`, `vertex-borrar.yml` | Los tres workflows de GitHub Actions (se copian al fork; **no** están instalados en `.github/workflows` del curso) |
| `pruebas/` | pytest: adaptador, manifiesto, scripts, workflows, presentación |

## 2. Preparar el entorno (una vez)

Desde la raíz del repositorio, en una terminal bash (Codespace, Git Bash o Linux). **Windows:** usa Git Bash para los `bash scripts/...`; en PowerShell 5.1 no existe `&&` y en vez de `echo "salida: $?"` se usa `echo $LASTEXITCODE`.

```bash
cd 04-Proyecto-Base
python -m pip install -r requirements-dev.txt
python -m ia_mlops.operacional
python -m ia_mlops.pipeline
python -m ia_mlops.alias_modelo mostrar
```

**Qué debes ver** (con un registro nuevo): `Modelo registrado «retencion-90d»: 1 versiones` y `Alias: ninguno`. Con más ejecuciones del pipeline habrá más versiones: usa **tus** números.
**Si falla:** `No module named ia_mlops` → no estás en `04-Proyecto-Base`; `0xc06d007f` con conda en Windows → activa el entorno con `conda activate`.

Para tener un `champion` en **tu** registro local (esto mueve el alias de tu copia local, no borra nada):

```bash
python -m ia_mlops.alias_modelo promover --version 1
```

Y las dependencias del extra:

```bash
cd ../01-Sesiones/S5-MLOps-y-Operacion/extra-vertex-champion
python -m pip install -r requirements-extra.txt
```

## 3. L1 · Del registro de MLflow al manifiesto

```bash
python manifiesto_champion.py generar --salida vertex-manifiesto.json
```

**Qué debes ver** (real, registro de ensayo con champion = v6 y anterior = v5; ver [`salidas/01-manifiesto.txt`](salidas/01-manifiesto.txt)):

```
«retencion-90d» @champion -> versión 6 de MLflow (anterior: 5)
  AUC valid 0.6982 · test 0.7471 · huella de datos 35a94deb4e04ab4a
  imagen: <registro>/retencion-vertex:v6-35a94deb4e04ab4a   alias en Vertex: mlflow-v6
  etiquetas de Vertex: curso=ml-ia,mlflow_modelo=retencion-90d,mlflow_alias=champion,mlflow_version=6,mlflow_run=…,huella_datos=35a94deb4e04ab4a,auc_valid=0_6982,auc_test=0_7471,mlflow_version_anterior=5
```

Las **etiquetas** cumplen las reglas de Google Cloud (hasta 64 por recurso; clave de 1 a 63 caracteres que empieza por letra minúscula; valor de 0 a 63; solo minúsculas, números, `_` y `-`): por eso el AUC `0.6982` se escribe `0_6982`. Fuente: <https://docs.cloud.google.com/resource-manager/docs/labels-overview>. *La referencia de `gcloud ai models upload --labels` habla de «64 caracteres»; se aplica el límite menor, 63.*

Sin registro de MLflow (para enseñar el formato): `python manifiesto_champion.py generar --simular --salida vertex-manifiesto.json` marca `"simulado": true` y **no** pasa la puerta de calidad.

La **puerta de calidad** antes de publicar (AUC mínimo en valid y test, huella de datos presente):

```bash
python manifiesto_champion.py puerta --manifiesto vertex-manifiesto.json
```

**Qué debes ver:** `Puerta de calidad abierta: la versión 6 tiene AUC valid 0.6982 y test 0.7471 (mínimo 0.65) y huella 35a94deb4e04ab4a.` Para ver la puerta **cerrada**:

```bash
python manifiesto_champion.py puerta --manifiesto vertex-manifiesto.json --auc-minimo 0.99
```

Con `--auc-minimo 0.99` sale `Error: Puerta de calidad CERRADA: …` y código 2. **El 0.65 es provisional**: no sale de ninguna medición (con 114 y 250 clientes el AUC oscila más que eso por azar); se acuerda con negocio.
**Si falla:** `no tiene el alias @champion` → `python -m ia_mlops.alias_modelo promover --version N` (apartado 2).

## 4. L2 · El adaptador y la imagen

```bash
python preparar_contexto.py --manifiesto vertex-manifiesto.json --destino build/vertex
```

**Qué debes ver:** `Contexto listo en build/vertex: 16 archivos; modelo guardado con scikit-learn 1.9.1 (= el del lock).` El script **se niega** si el modelo y el `requirements-api.lock` tienen otro scikit-learn (un modelo guardado con una versión no debe abrirse con otra), y **no borra** una carpeta que no creó él.

Las 13 variables, **en el orden del modelo** (lista de números, no diccionario; si cambias el orden el modelo no avisa):

```bash
python instancias.py --salida instancias.json
```

Probar el adaptador **sin Docker** (en la carpeta de la imagen, con las variables que pone Vertex):

```bash
cd build/vertex
AIP_HTTP_PORT=8080 AIP_HEALTH_ROUTE=/salud AIP_PREDICT_ROUTE=/predict CURSO_MODELO_DIR=modelo python vertex_adaptador.py
```

En **otra terminal** (desde `extra-vertex-champion`):

```bash
curl http://127.0.0.1:8080/salud
curl -X POST http://127.0.0.1:8080/predict -H "content-type: application/json" -d @instancias.json
```

**Qué debes ver** (real, [`salidas/10-adaptador-prediccion.txt`](salidas/10-adaptador-prediccion.txt)): `{"estado":"ok"}` y tres predicciones con `probabilidad`, `clase`, `tramo` y `version_mlflow` (el cliente `activo` da **0.8279** y tramo `alta`; es la misma probabilidad que `alias_modelo cargar`).
**Si falla:** `Address already in use` → otro proceso usa el 8080 (`AIP_HTTP_PORT=8081`); `422` → el cuerpo no cumple el contrato (el mensaje dice la instancia y el campo; ver [`salidas/11-adaptador-errores.txt`](salidas/11-adaptador-errores.txt)).

Con Docker (en Cloud Shell o en tu equipo; **este portátil no tiene Docker: sin verificar**):

```bash
docker build --platform linux/amd64 -f build/vertex/Dockerfile.vertex -t retencion-vertex:local build/vertex
docker run --rm -p 8080:8080 -e AIP_HTTP_PORT=8080 -e AIP_HEALTH_ROUTE=/salud -e AIP_PREDICT_ROUTE=/predict retencion-vertex:local
```

`--platform linux/amd64` porque Vertex es amd64 (en un Mac con chip ARM sin él la imagen no arrancaría en Vertex). **No se definen variables `AIP_*` dentro del Dockerfile**: la documentación oficial lo prohíbe («don't set your own variables with the `AIP_` prefix»); las pone Vertex según las rutas y el puerto que se declaran al subir el modelo.

**Paridad** con el modelo cargado a mano: se guarda la respuesta del adaptador en `respuesta.json` y se compara.

```bash
curl -X POST http://127.0.0.1:8080/predict -H "content-type: application/json" -d @instancias.json -o respuesta.json
python comparar_paridad.py --respuesta respuesta.json --instancias instancias.json --modelo-dir build/vertex/modelo
```

**Qué debes ver** (real, [`salidas/13-paridad.txt`](salidas/13-paridad.txt)): una tabla con la diferencia `0.00e+00` en cada cliente y `PARIDAD: las predicciones del endpoint y las del modelo local coinciden.` Sale `0` si coinciden, `1` si hay diferencias, `3` si contestó otra versión (con tráfico dividido).

### ¿Y si la API se construye con el Dockerfile multietapa?

Hay dos formas de construir **la API**: la de `develop` (`COPY models/modelo_mlflow`) y la multietapa (`--build-context modelo=models`). `Dockerfile.vertex` **no depende de ninguna**: su contexto lo prepara `preparar_contexto.py` con el mismo `requirements-api.lock` y el modelo exportado del registro. Una prueba lo comprueba (`test_compatible_con_las_dos_formas_de_construir_la_api`).

## 5. Preparar Google Cloud y GitHub (una vez, quien administra el proyecto)

Requisitos previos del laboratorio Cloud Journey de S4: federación WIF con GitHub, cuenta `sa-github-despliegue`, environment `produccion` con revisores. **Hoy no existen en la cuenta del curso** (se borraron al acabar S4; ver las capturas del apartado 10): se recrean con [`preparar-gcp-s4.sh`](../../S4-Orquestacion-y-CI-CD/laboratorio-cloud-journey/preparar-gcp-s4.sh) y luego, para este extra, en Cloud Shell:

```bash
bash scripts/preparar_gcp.sh --con-borrado
```

Habilita las APIs, crea el repositorio de Artifact Registry **regional**, da a la cuenta de despliegue `roles/aiplatform.user` y `roles/artifactregistry.writer` (y, con `--con-borrado`, `roles/artifactregistry.repoAdmin` solo sobre ese repositorio) e imprime las **variables de GitHub** (Settings → Secrets and variables → Actions → **Variables**; no son secretos):

| Variable | Valor |
|---|---|
| `GCP_PROYECTO` | el proyecto del curso |
| `GCP_REGION` | `southamerica-west1` (Santiago admite Model Registry y predicción online de modelos propios: [fuente](https://docs.cloud.google.com/vertex-ai/docs/general/locations)) |
| `GCP_PROVEEDOR_WIF` | `projects/<número>/locations/global/workloadIdentityPools/github/providers/github` |
| `GCP_CUENTA_DESPLIEGUE` | `sa-github-despliegue@<proyecto>.iam.gserviceaccount.com` |
| `GCP_REPO_AR` | opcional; por defecto `curso` |
| `CURSO_MLFLOW_URI` | opcional: un servidor de MLflow **compartido**; sin él, el enlace MLflow ← Vertex no se escribe |

**Sin verificar:** que `roles/aiplatform.user` baste para subir, desplegar, hacer `undeploy` y borrar el endpoint (si falla con `PERMISSION_DENIED`, el mensaje dice qué permiso falta); que el agente de servicio de Vertex lea la imagen sin más (la documentación dice que es automático si la imagen es del mismo proyecto; si no, necesita `roles/artifactregistry.reader`).

## 6. L3 · Cloud Shell: subir, desplegar, probar, promover

> **¡CUESTA!** Subir el modelo y la imagen cuesta almacenamiento. **Desplegar** cobra **mientras haya un modelo desplegado**, aunque no reciba peticiones, y con dos versiones desplegadas son **dos máquinas** (`e2-standard-2` × 1 réplica cada una). Precio: **sin dato** (<https://cloud.google.com/vertex-ai/pricing>). Cuando acabes: `bash scripts/borrar.sh`.

En Cloud Shell, con el repositorio clonado y un entorno con el proyecto entrenado (como en las prácticas de S4):

```bash
git clone https://github.com/<tu-usuario>/curso-ml-ia-desarrollo-produccion.git
cd curso-ml-ia-desarrollo-produccion/04-Proyecto-Base
python3 -m venv ~/.venv-curso-ml && ~/.venv-curso-ml/bin/pip install -q -r requirements-dev.txt
~/.venv-curso-ml/bin/python -m ia_mlops.operacional && ~/.venv-curso-ml/bin/python -m ia_mlops.pipeline
~/.venv-curso-ml/bin/python -m ia_mlops.alias_modelo promover --version 1
cd ../01-Sesiones/S5-MLOps-y-Operacion/extra-vertex-champion
export CURSO_PYTHON=~/.venv-curso-ml/bin/python
```

```bash
bash scripts/subir_modelo.sh
```

**Qué debes ver** (esperado; la salida real contra el `gcloud` simulado está en [`salidas/20-subir-modelo.txt`](salidas/20-subir-modelo.txt)): el manifiesto, `Contexto listo`, la creación del repositorio (o `Ya existe`), `docker build`/`push`, el `gcloud ai models upload` y `Listo: MLflow v1 -> retencion-90d-champion versión 1 (alias mlflow-v1). Sin desplegar: no cobra máquinas.` **Repetirlo no hace nada nuevo** (`La imagen … ya está subida`, `La versión … ya está en el Model Registry`).

```bash
bash scripts/desplegar.sh
```

Cuando ya hay otra versión desplegada, la nueva entra en canario (el 10 % es el valor por defecto; se cambia con `--canario N`):

```bash
bash scripts/desplegar.sh --canario 10
```

Si el endpoint está vacío, la versión recibe el **100 %** (`--traffic-split 0=100`: la clave `0` es el modelo que se despliega, [fuente](https://docs.cloud.google.com/vertex-ai/docs/predictions/deploy-model-api)). Si ya hay otra, la nueva entra en **canario**: `--traffic-split 0=10,<id-anterior>=90`, y la suma tiene que dar 100 (el simulador de las pruebas lo exige como Vertex). Tarda varios minutos (**sin medir**).

```bash
bash scripts/probar.sh
```

Envía los tres clientes de ejemplo, **reintenta** hasta que conteste la versión nueva (con canario puede contestar la anterior: cada respuesta lleva `version_mlflow`) y compara con el modelo local. **Qué debes ver:** `PARIDAD: las predicciones del endpoint y las del modelo local coinciden.`
**Si falla:** `paridad rota` → la imagen no lleva el modelo que dice el manifiesto (compara `version_mlflow` y la huella); `no contesta la versión esperada` tras 40 intentos → sube `--intentos` o el canario.

```bash
bash scripts/promover.sh
```

Pasa la versión al **100 %** (`gcloud ai endpoints update --traffic-split <id-nueva>=100,<id-anterior>=0`; que un valor 0 sea válido ahí: **sin verificar**). La anterior **sigue desplegada y cobrando**; para retirarla (espera 600 s, la documentación recomienda 10-15 min tras mover el tráfico: [fuente](https://docs.cloud.google.com/vertex-ai/docs/predictions/undeploy-model)):

```bash
bash scripts/promover.sh --retirar-anterior
```

## 7. L4 · Rollback: volver a la versión anterior

```bash
bash scripts/volver.sh
```

Mueve el tráfico a la versión **anterior de MLflow** (la que anotó la etiqueta `mlflow_version_anterior` de la versión que sirve, o la que pidas con `--a-version N`) **y**, a la vez, ejecuta `python -m ia_mlops.alias_modelo volver`. Si la anterior sigue desplegada (con 0 %), son segundos; si ya se retiró, se **vuelve a desplegar** desde el Model Registry (minutos, **sin medir**). Nada se borra. `--sin-mlflow` no toca el alias (lo usa el workflow, donde el registro no es el tuyo) y `--retirar-actual` hace `undeploy` de la versión mala:

```bash
bash scripts/volver.sh --sin-mlflow
```
**Qué debes ver** (real contra el `gcloud` simulado, [`salidas/25-volver.txt`](salidas/25-volver.txt) y [`salidas/26-volver-con-redespliegue.txt`](salidas/26-volver-con-redespliegue.txt)): `Sirve ahora: mlflow-v6 … -> vuelve a: mlflow-v5`, el reparto nuevo y `Rollback: @champion: v6 -> v5. La v6 sigue registrada; no se ha borrado nada.`
**Si falla:** `no guardó una versión anterior` → `bash scripts/volver.sh --a-version N`.

## 8. L5 · Los tres workflows de GitHub Actions

Se **copian a tu fork** (no están en `.github/workflows` del curso). Para ensayar sin la rama principal, un `push` a `lab/vertex-champion/<lo-que-sea>` lanza el de desplegar (se detiene en la aprobación):

```bash
mkdir -p .github/workflows
cp 01-Sesiones/S5-MLOps-y-Operacion/extra-vertex-champion/vertex-*.yml .github/workflows/
git switch -c lab/vertex-champion/ensayo
git add .github/workflows
git commit -m "Extra S5: workflows de Vertex AI"
git push -u origin lab/vertex-champion/ensayo
```

| Workflow | Qué hace | Entradas |
|---|---|---|
| `vertex-desplegar.yml` | **1 · modelo** (sin nube): entrena, deja el champion, **puerta de calidad**, construye la imagen, la **arranca en el runner** y comprueba salud y paridad. **2 · desplegar** (con **aprobación** del environment `produccion`, **WIF sin claves**): sube la **misma** imagen, registra la versión (`--parent-model`), despliega en canario, prueba, promueve y escribe el **Job Summary** con la tabla MLflow ↔ Vertex | `version_mlflow`, `dos_versiones`, `region`, `maquina`, `min_replicas`, `canario`, `auc_minimo`, `promover`, `retirar_anterior` |
| `vertex-rollback.yml` | Mueve el tráfico a la versión anterior (aprobación) | `a_version`, `region`, `retirar_actual` |
| `vertex-borrar.yml` | Pide **confirmación escrita** (`BORRAR`) antes de entrar en Google Cloud; luego aprobación; undeploy, endpoint, modelo e imágenes | `confirmacion`, `region`, `con_imagenes` |

**De dónde sale el champion en el runner (limitación honesta).** El registro de MLflow del curso es **local** (`models/mlflow.db` no está en git). Como `nueva-version.yml`, el runner **entrena** con los datos de muestra y crea **su propio registro**: el champion de ese run no es «el de tu portátil». Con `dos_versiones` se entrena dos veces y se promueve en cadena (v1 y v2) para que haya una versión anterior a la que volver. En una empresa habría **un servidor de MLflow compartido** (variable `CURSO_MLFLOW_URI`) del que se leería el champion y en el que se escribirían las etiquetas `vertex_*`; aquí eso queda **sin verificar**. El alias de MLflow tampoco se mueve desde el rollback del workflow (el registro del runner desaparece): se mueve donde está el registro.

**Seguridad.** Permisos `contents: read` en todo y `id-token: write` solo en los trabajos que entran en Google Cloud; sin secretos, ni claves, ni `credentials_json`; las entradas **nunca** se interpolan dentro de los scripts (pasan por `env:`); `concurrency` común para que desplegar, volver y borrar no se pisen.

**Qué debes ver en Actions** (**sin verificar**: aún no se ha ejecutado; capturas pendientes en [`capturas-pendientes.md`](capturas-pendientes.md)): el run `Vertex AI · desplegar el champion de MLflow` con el trabajo 1 en verde y el 2 en espera de *Review deployments*; tras aprobar, el resumen con la tabla MLflow ↔ Vertex y la salida de paridad.
**Si falla:** `Error: ... workload_identity_provider` → falta la variable `GCP_PROVEEDOR_WIF`; `PERMISSION_DENIED` en `aiplatform` → falta el rol (apartado 5); `docker: command not found` no debería pasar en `ubuntu-latest`.

## 9. Ensayo real recomendado (rama `lab/vertex-champion/ensayo`, borrado inmediato)

1. Recrear WIF y la cuenta de despliegue (`preparar-gcp-s4.sh`) y `bash scripts/preparar_gcp.sh --con-borrado`; poner las variables de GitHub.
2. En Cloud Shell, **primero** a mano: `subir_modelo.sh` → `desplegar.sh` → `probar.sh` → `volver.sh`/`promover.sh` → `borrar.sh`. Comprobar en la consola: Registro de modelos (versiones y etiquetas), Extremos (reparto 90/10).
3. Después, en Actions: `push` a la rama de ensayo → aprobar → mirar el resumen → `Vertex AI · borrar todo` con `BORRAR`.
4. Comprobar que **todo** queda vacío: `gcloud ai endpoints list`, `gcloud ai models list`, `gcloud artifacts docker images list` y la consola.
5. Hacer las capturas de [`capturas-pendientes.md`](capturas-pendientes.md) y anotar lo que difiera de lo «sin verificar» de abajo.

## 10. Qué se comprobó de verdad

**Ejecutado aquí (27/11/2026, Windows, Python 3.11, Git Bash):** adaptador (contrato, paridad exacta con `alias_modelo.cargar_y_puntuar` y con el modelo cargado a mano, errores 422, arranque real como en la imagen), manifiesto y etiquetas contra el registro de MLflow (**una copia**; el registro del proyecto no se toca y una prueba comprueba su huella SHA-256 antes y después; si otro proceso lo escribe durante la sesión, la prueba lo avisa con un skip), puerta de calidad, `anotar`, contexto de la imagen, los siete scripts ejecutados de verdad contra un `gcloud` y un `docker` **simulados** (subir, repetir, desplegar, canario con reintento, promover, volver con y sin la anterior desplegada, borrar), los tres workflows (YAML, permisos, WIF, órdenes, `bash -n` de cada paso) y la presentación. Las cifras de las pruebas están en [`salidas/30-pruebas.txt`](salidas/30-pruebas.txt).

**Sin verificar (no se ha podido ejecutar):** Docker (`docker build`/`push`, `--platform linux/amd64`); Artifact Registry real; `gcloud ai models upload --parent-model --version-aliases` y que un alias `champion` se mueva de versión; `gcloud ai endpoints deploy-model --model <id>@<versión>` (la referencia de gcloud no documenta esa sintaxis; la de la API REST sí: `models/{model}@2`); los nombres de campo JSON de `gcloud ... describe` que usan los scripts (`deployedModels[].id/displayName`, `trafficSplit`, `versionAliases`, `labels`); que un valor `0` sea válido en `--traffic-split` de `endpoints update`; permisos de `roles/aiplatform.user`; tiempos de despliegue; coste; GitHub Actions entero (los tres workflows); la intercepción del tráfico del canario (aleatoria: `probar.sh` reintenta).

**Sin dato:** precios de Vertex AI y de Artifact Registry (la documentación enlazada no los da); tiempo de despliegue de un endpoint.

## 11. Fuentes (documentación oficial, consultada el 27/11/2026)

- Requisitos de un contenedor propio (`AIP_HTTP_PORT`, `AIP_HEALTH_ROUTE`, `AIP_PREDICT_ROUTE`, `{"instances": …}` / `{"predictions": …}`, Artifact Registry regional, agente de servicio): <https://docs.cloud.google.com/vertex-ai/docs/predictions/custom-container-requirements>
- `gcloud ai models upload` (`--container-ports`, `--container-predict-route`, `--container-health-route`, `--parent-model`, `--version-aliases`, `--labels`): <https://docs.cloud.google.com/sdk/gcloud/reference/ai/models/upload>
- `gcloud ai endpoints deploy-model`: <https://docs.cloud.google.com/sdk/gcloud/reference/ai/endpoints/deploy-model> · desplegar con `--traffic-split`: <https://docs.cloud.google.com/vertex-ai/docs/predictions/deploy-model-api> · `endpoints update`: <https://docs.cloud.google.com/sdk/gcloud/reference/ai/endpoints/update>
- `undeploy-model` y espera de 10-15 min: <https://docs.cloud.google.com/vertex-ai/docs/predictions/undeploy-model>
- Versiones de un modelo (`parentModel`): <https://docs.cloud.google.com/vertex-ai/docs/model-registry/versioning> · `DeployedModel.model` con `@versión` o `@alias`: <https://docs.cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.endpoints> · `models describe 123@2`: <https://docs.cloud.google.com/sdk/gcloud/reference/ai/models/describe>
- `list-version`: <https://docs.cloud.google.com/sdk/gcloud/reference/ai/models/list-version> · `models delete`: <https://docs.cloud.google.com/sdk/gcloud/reference/ai/models/delete> · borrar imágenes: <https://docs.cloud.google.com/sdk/gcloud/reference/artifacts/docker/images/delete>
- Etiquetas: <https://docs.cloud.google.com/resource-manager/docs/labels-overview> · Regiones: <https://docs.cloud.google.com/vertex-ai/docs/general/locations> · Máquinas: <https://docs.cloud.google.com/vertex-ai/docs/predictions/configure-compute>

**Dónde manda la documentación sobre el diseño inicial:** (1) el Dockerfile **no** define variables `AIP_*` (la documentación lo prohíbe) y las rutas y el puerto se declaran en `models upload`; (2) no hay **bucket**: el modelo va dentro de la imagen y `--artifact-uri` es opcional con un contenedor propio; (3) la referencia de `gcloud` nombra «Container Registry», pero la documentación del contenedor propio exige **Artifact Registry** regional: se usa Artifact Registry; (4) el valor de una etiqueta admite 63 caracteres (la referencia de `--labels` dice 64): se usa 63. En Santiago **no** figuran Model Monitoring, Experiments ni Vertex Explainable AI (la fila de la región solo lista Model Registry, predicción online y entrenamiento de modelos propios, entre otros): no se usan aquí.

## 12. Pruebas y ejercicios

Las pruebas de esta carpeta (desde `extra-vertex-champion`, con el proyecto entrenado; trabajan sobre una **copia** del registro de MLflow y **no** ejecutan la suite completa de `04-Proyecto-Base`):

```bash
python -m pytest -q -p no:cacheprovider pruebas
```

**Git Bash en Windows:** Git Bash convierte un argumento como `/predict` en una ruta de Windows al llamar a `gcloud`; `variables.sh` lo evita con `MSYS2_ARG_CONV_EXCL` (una prueba comprueba que las rutas llegan exactas). En Cloud Shell no pasa nada de esto.

Ejercicios (los cuatro primeros, sin nube):

1. Calcula a mano el `--traffic-split` de un canario del **50 %** con dos modelos ya desplegados y compruébalo con el ayudante (usa un JSON de ejemplo con la forma **supuesta** de `gcloud ai endpoints describe`):

   ```bash
   python vertex_ayuda.py split-nuevo --json ejemplos/endpoint-dos-modelos.json --porcentaje 50
   ```

   Debe salir `0=50,1000=50,1001=0` (la clave `0` es el modelo nuevo; el reparto suma 100).
2. Manda al adaptador una instancia como **diccionario** y otra con **12 números**; lee los dos mensajes de error (422).
3. Escribe a mano las etiquetas de un modelo con AUC de test **0.7471** y huella `35a94deb4e04ab4a` según las reglas de GCP (`auc_test=0_7471`) y compáralas con `salidas/01-manifiesto.txt`.
4. Sube `--auc-minimo` a **0.80** y mira qué hace la puerta. ¿Qué número pondrías tú y **de dónde sale**?
5. (Con el profesor, en el ensayo real) Lanza `vertex-rollback.yml` y **cronometra** el rollback con la anterior desplegada y con la anterior retirada: hoy ese tiempo es **sin dato**.
