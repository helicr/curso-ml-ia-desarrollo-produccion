# Extra de S5 · Del alias `champion` de MLflow a un endpoint de Vertex AI, desplegado desde GitHub Actions

Laboratorio extra de la sesión 5 del curso «ML e IA: de desarrollo a producción» (caso Retail, retención a 90 días). Lleva **el modelo que manda en MLflow** (alias `champion`) hasta un **endpoint de Vertex AI**, con una imagen de predicción **propia** que devuelve la **probabilidad**, y lo despliega, lo prueba, lo deshace y lo borra con tres workflows de GitHub Actions (identidad federada, sin claves; con aprobación humana).

- **Presentación:** [`index.html`](index.html) (autocontenida; `⌂ Índice` vuelve a [S5](../index.html); `S` abre las notas del profesor). Se regenera con `python generar.py`.
- **Guía paso a paso:** [`guia.md`](guia.md) (cada orden con «qué debes ver», «si falla», qué cuesta y cómo no dejarlo encendido).
- **Capturas que faltan y cómo hacerlas:** [`capturas-pendientes.md`](capturas-pendientes.md).

## Qué está probado y qué NO

| | Estado |
|---|---|
| Adaptador de Vertex (contrato, probabilidad, errores 422, arranque real, paridad exacta con `alias_modelo` y con el modelo cargado a mano) | **Ejecutado** (pytest, 27/11/2026) |
| Manifiesto, etiquetas de Google Cloud, puerta de calidad, `anotar` en MLflow, contexto de la imagen | **Ejecutado** sobre una **copia** del registro de MLflow del proyecto |
| Los siete scripts de `scripts/` (subir, desplegar con canario, probar con reintento, promover, volver con y sin la anterior desplegada, borrar) | **Ejecutados con bash** contra un `gcloud` y un `docker` **simulados** (`pruebas/gcloud_simulado.py`): prueban la lógica, **no** Google Cloud |
| Los tres workflows | YAML, permisos mínimos, WIF sin claves, `environment`, sin secretos, entradas no interpoladas, `bash -n` de cada paso, órdenes que existen: **ejecutado**. En GitHub Actions: **sin verificar** |
| `docker build` / `push` de `Dockerfile.vertex` | **Sin verificar** (este portátil no tiene Docker) |
| Vertex AI real (subir versión con `--parent-model`, canario, `endpoints update`, rollback), Artifact Registry real, WIF real | **Sin verificar**: no se ha creado ningún recurso en Google Cloud para esta entrega |
| Precios y tiempos de despliegue | **Sin dato** |

La lista detallada de lo «sin verificar» (nombres de campo JSON de `gcloud`, sintaxis `--model <id>@<versión>`, permisos de `roles/aiplatform.user`...) está en `guia.md`, apartado 10, y la receta del ensayo real con borrado inmediato, en el apartado 9.

## Qué hay aquí

```
extra-vertex-champion/
├── README.md · guia.md · capturas-pendientes.md · index.html · generar.py
├── imagen/vertex_adaptador.py        el contrato de Vertex (FastAPI): salud, predicción, 13 números -> probabilidad, clase y tramo
├── imagen/Dockerfile.vertex          la imagen con el modelo dentro (sin variables AIP_*, sin latest, sin root)
├── manifiesto_champion.py            MLflow -> vertex-manifiesto.json + etiquetas; puerta de calidad; MLflow <- Vertex (anotar)
├── preparar_contexto.py              build/vertex/: lo que necesita docker build (no depende de cómo se construya la API)
├── instancias.py · clientes_ejemplo.json · comparar_paridad.py · vertex_ayuda.py
├── scripts/                          preparar_gcp · subir_modelo · desplegar · probar · promover · volver · borrar (+ variables.sh)
├── vertex-desplegar.yml · vertex-rollback.yml · vertex-borrar.yml     para copiar a .github/workflows de TU fork
├── salidas/                          las salidas REALES que enseñan las diapositivas
├── pruebas/                          pytest (adaptador, manifiesto, ayudante, scripts, workflows, presentación)
├── img/                              capturas reales (GCP y GitHub en solo lectura) y salidas de terminal dibujadas
└── requirements-extra.txt            -> requirements-dev.txt del proyecto (no añade nada)
```

## Cómo se ejecutan las pruebas

Desde esta carpeta, con el entorno del curso (Python 3.11, `requirements-dev.txt`) y **con el proyecto entrenado** (`python -m ia_mlops.pipeline` en `04-Proyecto-Base`; sin `models/mlflow.db` las pruebas que lo necesitan se omiten con el aviso):

```bash
python -m pytest -q -p no:cacheprovider pruebas
```

Las pruebas trabajan sobre una **copia** del registro de MLflow (nunca lo cambian: una prueba comprueba la huella SHA-256 del original antes y después, y si **otro proceso** lo ha escrito durante la sesión lo avisa con un skip explícito). Las de los scripts necesitan un `bash` (el de Git); sin él se omiten. **No** ejecutan la suite completa de `04-Proyecto-Base`.

## Reglas que se han respetado

- No se ha tocado `04-Proyecto-Base` (ni un archivo) ni ningún workflow instalado en `.github/workflows`.
- Ningún recurso creado en Google Cloud; ninguna credencial usada.
- La documentación oficial manda sobre el diseño inicial; las diferencias están dichas en `guia.md` (apartado 11).
