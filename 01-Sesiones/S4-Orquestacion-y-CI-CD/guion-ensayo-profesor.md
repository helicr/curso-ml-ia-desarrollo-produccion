# Guion de ensayo del profesor · S4 (recrear el laboratorio antes de repetirlo con el alumnado)

Preparado el 27/11/2026. Es para ti: sirve para **practicar** S4 de principio a fin, en tu *fork*, antes de volver a hacerlo con el grupo. Las duraciones son estimaciones tomadas del [`guion.md`](guion.md) de la clase del 25/11 y de las ejecuciones reales de esos días; **no están medidas en un ensayo posterior**. Los comandos son los de las guías (no hay ninguno nuevo): si una guía cambia, manda la guía.

## 1. Qué cambió desde la clase del 25/11

| Qué | Dónde | Por qué te afecta al repetirlo |
|---|---|---|
| El script de preparación entiende un *pool* o proveedor de WIF **borrado** (los de Google se conservan 30 días) y los **restaura** (`undelete`); además fija la condición `assertion.repository==…` del proveedor | [`laboratorio-cloud-journey/preparar-gcp-s4.sh`](laboratorio-cloud-journey/preparar-gcp-s4.sh) y su guía (párrafo «Si lo repites un día después de borrarlo») | Si repites el laboratorio tras haberlo borrado, antes fallaba con `NOT_FOUND` al crear el proveedor. Ahora debe continuar. **Sin volver a ejecutar** tras el arreglo en una cuenta limpia |
| `borrar.sh` de Dataproc borra también los dos *buckets* que Dataproc crea solo (`dataproc-staging-…`, `dataproc-temp-…`), solo si ya no quedan lotes ni clústeres | [`practicas-gcp/03-dataproc-spark/`](practicas-gcp/03-dataproc-spark/borrar.sh) | Tras la práctica 03 quedaban *buckets* huérfanos (lo vimos el 26/11) |
| El README de la práctica 04 (Vertex) dice «comprobado» sobre la **clase** frente a la probabilidad | [`practicas-gcp/04-vertex-modelo/README.md`](practicas-gcp/04-vertex-modelo/README.md) | El contenedor prediseñado devuelve 0 o 1, no la probabilidad |
| Laboratorio e2e: fork **sin** «Copy the main branch only», error *non-fast-forward*, el *environment* se llama `produccion` (sin tilde), `curl` en cmd y PowerShell | [`laboratorio-produccion-e2e/`](laboratorio-produccion-e2e/guia.md) (`guia.md`, `CONFIGURAR-REPOSITORIO.md`, `CODESPACE.md`) | Son las trampas en las que cayó el grupo |
| Extra del LLM: apartado «Si falla» de `torch` y del `ConnectError` de HuggingFace | [`extra-estilo-llm/`](extra-estilo-llm/README.md) | Solo si lo ofreces |
| Documentos de la sesión que **no existían**: teoría, hoja de ruta de laboratorios, tarea (avance 4), rúbrica, plantilla de evidencia, guion y checklist | [`teoria/`](teoria/README.md), [`practica/`](practica/guia-laboratorio.md), [`tarea/`](tarea/README.md), [`evidencias/`](evidencias/plantilla-avance-4.md) | El guion está fechado el 25/11: **cambia la fecha** si lo reutilizas |
| La guía de Docker y kind del Codespace (secuencia nueva, «mirar dentro de la imagen», tabla de fallos; 43 diapositivas) | [`03-Entorno/guia-docker-kubernetes-gke/`](../../03-Entorno/guia-docker-kubernetes-gke/index.html) | La usas en el bloque 4 del e2e (Codespace) |

## 2. Qué sigue pendiente (no lo des por hecho al ensayar)

1. **Dockerfiles multi-etapa** (rama `feat/dockerfile-clon`, **ya fusionada en `develop`**): el código se clona del commit exacto y el modelo entra con `--build-context modelo`; cambia la línea de `docker build` de los workflows, de los compose (modo desarrollo `FUENTE=contexto`) y de las guías. **«Validar API e interfaz en dos contenedores» ya pasó en verde en Actions sobre `f7bb7a0`** (27/11/2026, run 46003093657: clon por *sha*, `--secret env=` y compose con `FUENTE=git`). **Sin ensayar todavía** el build nuevo en `puntuar-lote`, `nueva-version`, `desplegar-gcp`, los workflows del agente y `ci.yml`: el **ensayo A** de abajo es esa primera prueba. Si algo falla, anótalo: las guías ya describen el comando nuevo. Faltan además los PDF y las capturas antiguas con el comando anterior.
2. **Decisiones tuyas**: el recorte de Google Cloud en 4 h (la hoja de ruta de [`practica/guia-laboratorio.md`](practica/guia-laboratorio.md) lo deja abierto), los pesos de la rúbrica y qué se entrega por qué canal.
3. **Sin verificar**: clonar el *fork* de un alumno en Cloud Shell, y el coste y el tiempo exacto del endpoint de Vertex (**sin dato**).

## 3. Por dónde empezar: te recomiendo la práctica sin coste, con 10 minutos de teoría delante

Orden de los tres ensayos, de menos a más riesgo:

| Ensayo | Qué es | Coste | Tiempo estimado |
|---|---|---|---|
| **A** | Teoría breve de Actions + **configurar el repositorio** + **laboratorio B (producción e2e)** | Ninguno (solo Actions) | ~2 h |
| **B** | **Cloud Journey** (WIF sin claves → Cloud Run) + Vertex (opcional) + **borrar todo** | **Sí, mientras haya recursos**: Vertex cobra con el endpoint desplegado, GKE mientras exista el clúster | ~1,5 h + borrado |
| **C** | Prácticas de GCP (Dataproc, GKE, Gemini…) y extra del LLM | Sí (cada una con su `borrar.sh`) | opcional, para casa |

**Por qué empezar por A:** no cuesta nada, no depende de la nube, y lo que configuras (el *environment* `produccion`, los permisos de Actions, la rama de ensayo) lo reutiliza B. **Empieza por la teoría de 10 minutos** (no 30): la de la clase quedó larga; basta con tres ideas, y el resto se explica **con los YAML abiertos** mientras corren.

## 4. Antes de empezar (una vez)

- **Ramas que ya existen en tu repositorio** (`lab/produccion-e2e`, `lab/nueva-version/*`, `lab/rollback/*`, `lab/cloud-journey/despliegue`, `lab/cloud-journey/despliegue-2`, `lab/monitoreo/*`, `lab/agente-*`…): **un `git push -u origin lab/produccion-e2e` sería rechazado** (*non-fast-forward*) porque ya existe con otra historia. Dos salidas: usa un **sufijo** (`lab/produccion-e2e-ens2`, `lab/nueva-version/muestra-ens2`…) o **bórralas antes** (decisión tuya; son del ensayo del 22–26/11): `git push origin --delete <rama>`. Las `referencia/*` y `main` **no se tocan**.
- **Trabaja en un *fork* o en una copia de prueba**, no en `develop`: los workflows se copian a `.github/workflows/` **de la rama de ensayo**, nunca a `develop`.
- **Python/Git en este portátil** (por si lo haces desde aquí): el `git` del entorno y el *bundle* de certificados; ver tu nota de «git push a GitHub» (Zscaler).

## 5. Guion del ensayo A (sin coste)

> «**Di:**» es lo que explicas; «**Haz:**» lo que tecleas o pulsas; «**Debes ver:**» lo que confirma que va bien.

### A.0 · Teoría de 10 minutos (con los YAML abiertos)
- **Di:** un *workflow* es un archivo YAML en `.github/workflows/`; tiene *jobs*, cada job *steps*, y corre en un *runner*. Se dispara por un evento (`push`, `workflow_dispatch`, `schedule`). Un *environment* con revisores es una **puerta**: el job espera hasta que una persona aprueba.
- **Di (la trampa):** «Run workflow» **no aparece** si el workflow no está en la rama por defecto: por eso lo ensayamos **por rama** (`lab/…`), empujando una rama que dispara el workflow.
- **Haz:** abre [`puntuar-lote.yml`](laboratorio-produccion-e2e/puntuar-lote.yml) y [`nueva-version.yml`](laboratorio-produccion-e2e/nueva-version.yml). Señala `on:`, `permissions:`, `environment:` y `concurrency:`.
- **Pregunta al aula:** «¿qué pasa si el *environment* se llama distinto?» → **no pide aprobación** (por eso el nombre exacto: `produccion`).

### A.1 · Configurar el repositorio (una vez)
- **Haz:** **Settings › Environments › New environment** → `produccion` → **Required reviewers** (tú) → **Save protection rules**. Después **Settings › Actions › General › Workflow permissions** → marca **Allow GitHub Actions to create and approve pull requests** → **Save**.
- **Debes ver:** `produccion` con «1 protection rule» y la casilla marcada. Detalle y capturas: [`CONFIGURAR-REPOSITORIO.md`](laboratorio-produccion-e2e/CONFIGURAR-REPOSITORIO.md).

### A.2 · Preparar la rama y los cuatro workflows
- **Haz** (guía, apartado 1; cambia el nombre de la rama si ya existe):
  ```
  git switch develop
  git pull
  git switch -c lab/produccion-e2e
  mkdir -p .github/workflows
  cp 01-Sesiones/S4-Orquestacion-y-CI-CD/laboratorio-produccion-e2e/{puntuar-lote,validar-produccion,nueva-version,rollback}.yml .github/workflows/
  git add .github/workflows
  git commit -m "Laboratorio de cierre de S4: workflows de producción"
  ```

### A.3 · Modo 1: puntuación por lotes
- **Haz:** `git push -u origin lab/produccion-e2e`. **Debes ver** en la pestaña **Actions** el run «Puntuar por lotes» en verde en **unos 3 minutos** (medido el 22/11) y su **Job Summary**.
- **Di:** el lote puntúa a todos los clientes de una vez y deja una lista priorizada; es el modo «de ayer».

### A.4 · Modos 2 y 3 y el panel (Codespace)
- **Haz** (guía, apartado 4): `python -m ia_mlops.operacional`, `python -m ia_mlops.pipeline`, `python -m ia_mlops.explotacion` y `docker compose -f deploy/docker/compose-produccion.yaml up --build -d`; luego `curl -fsS http://127.0.0.1:8090/listo`.
- **Haz:** con `ID=12670`, compara `/bajo-demanda/$ID` y `/online/$ID`, simula una compra con `POST /demo/compra` y repite las dos lecturas. **Debes ver:** el modo online cambia con la compra nueva; el de bajo demanda **no** (usa el último lote).
- **En cmd/PowerShell de Windows**, `curl` no admite `; echo` ni comillas simples: usa las variantes de la guía.

### A.5 · Una versión nueva (el corazón del laboratorio)
- **Di:** una versión nueva **no se despliega porque sí**: pasa por una **puerta de calidad** (compara con la de producción) y por una **aprobación humana**.
- **Haz:** tres ramas, una por escenario (guía, apartado 5.1): `lab/nueva-version/muestra` (igual), `…/completo-rechazo` y `…/completo` (aceptada, **espera tu aprobación**).
- **Debes ver:** «igual» → no publica; «rechazada» → la puerta falla; «aceptada» → el job queda en **Waiting**; tú pulsas **Review deployments › Approve and deploy**; se publica y abre un PR.
- **Si hay margen:** rollback (`lab/rollback/v1`): mueve la versión anterior de vuelta, con y sin comprobación.

### A.6 · Cierre del ensayo A
- Borra las ramas de ensayo que crees (opcional) y **no** hay nada que borrar en Google Cloud.

## 6. Guion del ensayo B (con coste controlado): Cloud Journey

> **Antes de empezar:** abre **Facturación** y confirma que hay presupuesto con alertas. Regla de oro: **todo lo que crees, lo borras ese mismo día**.

### B.0 · Teoría de 15 minutos: WIF sin claves
- **Di:** una clave JSON de cuenta de servicio es una **llave que no caduca**; la organización del curso **prohíbe crearlas** (`iam.disableServiceAccountKeyCreation`). En su lugar, GitHub presenta un **token firmado** y Google lo cambia por credenciales de **corta vida**: *Workload Identity Federation*.
- **Di:** el proveedor solo acepta tokens **de tu repositorio** (la condición `assertion.repository==…` que ahora fija el script).

### B.1 · Preparar Google Cloud con el script (Cloud Shell)
- **Haz** (guía, apartado 3): clonar el repo en Cloud Shell, abrir `preparar-gcp-s4.sh`, poner tus **tres valores** (`PROYECTO`, `FACTURACION`, `REPO_GITHUB`) y ejecutar `bash preparar-gcp-s4.sh`.
- **Debes ver:** al final, las cinco líneas `GCP_…=` que luego pegas en GitHub.
- **Si falla con `NOT_FOUND`:** el *pool* o el proveedor estaban borrados. El script nuevo los restaura; si no, `gcloud iam workload-identity-pools undelete github --location=global` y `… providers undelete github --workload-identity-pool=github --location=global`.

### B.2 · Artifact Registry y variables de GitHub
- **Haz:** `gcloud artifacts repositories create curso --repository-format=docker --location=southamerica-west1 …` (guía, apartado 4). En tu *fork*: **Settings › Secrets and variables › Actions › Variables**: cinco variables `GCP_PROYECTO`, `GCP_REGION`, `GCP_PROVEEDOR_WIF`, `GCP_CUENTA_DESPLIEGUE`, `GCP_CUENTA_SERVICIO` (**con los valores que imprimió tu script**).
- **Debes ver:** las cinco en **Repository variables** (no en «Environment variables»).

### B.3 · Desplegar con aprobación
- **Haz** (guía, apartado 6.2): rama `lab/cloud-journey/despliegue` (**usa un sufijo si ya existe**), copia `desplegar-gcp.yml` a `.github/workflows/`, commit y `git push -u origin …`.
- **Debes ver:** el run espera en **Waiting**; apruebas; Cloud Run queda desplegado.

### B.4 · Probar la URL pública
- **Haz** (apartado 8): `URL=$(gcloud run services describe retencion-api --region=southamerica-west1 --format='value(status.url)')`, luego `curl -fsS "$URL/salud"`, `…/listo` y `POST /predecir` con `tests/datos/cliente_ejemplo.json`.
- **Debes ver:** `0,828` (la probabilidad del cliente de ejemplo, como en local; medido el 25/11).

### B.5 · Vertex AI (opcional y caro si se olvida)
- **Haz:** práctica 04: `bash crear.sh`, `bash probar.sh` y **`bash borrar.sh` en cuanto acabes**.
- **Di:** el endpoint **cobra mientras tenga un modelo desplegado**, aunque no reciba peticiones. El contenedor prediseñado devuelve la **clase**, no la probabilidad.

### B.6 · Borrar todo (obligatorio)
- **Haz** (apartado 10): `bash borrar.sh` de Vertex y `bash borrar-gcp-s4.sh`; si quieres desvincular la facturación, `DESVINCULAR_FACTURACION=si bash borrar-gcp-s4.sh`. Al final revisa la **factura** (debería marcar 0 €) y borra tu Codespace.
- **Comprueba:** `gcloud run services list`, `gcloud artifacts repositories list`, `gcloud ai endpoints list` y `gcloud storage buckets list` **vacíos** (o solo lo que ya tuvieras).

## 7. Tabla de «si falla» que ya conoces

| Síntoma | Causa | Qué hacer |
|---|---|---|
| `git push` rechazado (*non-fast-forward*) | La rama ya existe en el remoto | Sufijo nuevo o borrar la rama remota |
| El run no pide aprobación | El *environment* no se llama `produccion` (sin tilde) o no tiene revisores | Revisar el nombre y las reglas (A.1) |
| «Run workflow» no aparece | El workflow no está en la rama por defecto | Ensayar por rama `lab/…` |
| El fork no trae las ramas | Se marcó «Copy the main branch only» | Rehacer el *fork* sin marcarlo |
| `NOT_FOUND` al crear el proveedor WIF | *Pool* o proveedor borrados (se conservan 30 días) | El script nuevo los restaura, o `undelete` a mano |
| `curl` falla en cmd | `;`, `echo` y comillas simples son de bash | Variantes cmd/PowerShell de la guía |
| `docker build` falla por `models/` | No existe el modelo | Ejecutar antes `python -m ia_mlops.pipeline` |
| Imagen no encontrada en kind | Falta construirla o cargarla | `docker build …` y `kind load docker-image …` (guía de kind, orden: modelo → imagen → clúster → carga → `apply`) |

## 8. Qué anotar al ensayar (para cerrar los «sin verificar»)

- Tiempo real de cada bloque (cronómetro) y dónde te atascaste.
- Si `preparar-gcp-s4.sh` pasa en una cuenta con el *pool* borrado, y su salida.
- Cuánto tardó el despliegue de Vertex y qué coste aparece en la factura (**sin dato** hasta que lo mires).
- Cualquier orden de las guías que ya no funcione: dímelo y la corrijo con su prueba.
