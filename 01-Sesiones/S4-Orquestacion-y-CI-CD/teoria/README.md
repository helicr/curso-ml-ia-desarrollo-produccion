# S4 · Teoría y glosario: orquestar con GitHub Actions y llevarlo a la nube

Material de lectura de la sesión «Orquestación y CI/CD con GitHub Actions». Acompaña a los laboratorios de la sesión (reparto en la [guía de laboratorios](../practica/guia-laboratorio.md)) y a la [tarea](../tarea/README.md). Cada concepto va con un ejemplo **real** de los laboratorios de S4, para que puedas abrir el archivo y verlo escrito.

> **Qué está comprobado y qué no.** Los laboratorios se ensayaron de verdad entre el 22 y el 25/11/2026: el lote diario tardó unos 3 minutos, «Validar la producción completa» unos 2 minutos y la API desplegada en Cloud Run predijo **0,828** para el cliente de ejemplo, igual que en local. Todo lo que no se pudo comprobar dice «sin verificar» o «sin dato». Este documento **no da precios, cuotas ni créditos de Google Cloud**: cambian; consulta la página oficial el día que lo hagas.

## 1. De dónde partimos y adónde vamos

Hasta S3 tu pipeline (raw → master → fs → ml → modelo → métricas) lo ejecutabas **tú**, a mano, en tu equipo o en el Codespace. En S3 aprendiste que un workflow puede ejecutar tus pruebas en cada `push`. En S4 damos el paso siguiente: que **el workflow ejecute el pipeline completo**, deje sus resultados guardados y, cuando toca publicar, **espere a que una persona lo apruebe**.

| Antes (a mano) | Con un workflow |
|---|---|
| «Lo ejecuté en mi equipo y funcionó» | Se ejecuta en una máquina limpia, siempre igual, y queda el historial |
| Un modelo en una carpeta local | Un **artefacto** descargable por cada ejecución |
| Publicar = copiar algo a algún sitio | Publicar = un trabajo que **espera aprobación** y deja rastro de quién aprobó |
| Claves guardadas «por si acaso» | **Sin claves**: la identidad se demuestra en cada ejecución (WIF, apartado 5) |

## 2. Workflows, jobs, steps y runners

| Palabra | Qué es | Ejemplo real |
|---|---|---|
| **Workflow** | Un archivo YAML en `.github/workflows/` que describe qué se automatiza | [`puntuar-lote.yml`](../laboratorio-produccion-e2e/puntuar-lote.yml) |
| **Evento / disparador** (`on:`) | Lo que lo pone en marcha | `push`, `workflow_dispatch`, `schedule` (apartado 3) |
| **Job** (trabajo) | Un grupo de pasos que corre en **una** máquina; los jobs corren en paralelo salvo que uno **necesite** a otro (`needs:`) | En `desplegar-gcp.yml`: «1 · Construir y probar la imagen» y «2 · Publicar … y desplegar» |
| **Step** (paso) | Una orden (`run:`) o una *action* ya hecha (`uses:`) | `uses: actions/checkout@v4`, o `run: python -m pytest -q` |
| **Runner** | La máquina que ejecuta un job. `runs-on: ubuntu-latest` es una máquina virtual de GitHub, **nueva en cada ejecución** y que se destruye al acabar | Todos los workflows del curso |
| **Action** | Un paso reutilizable publicado por alguien (GitHub, Google…) | `google-github-actions/auth@v2` |

Tres consecuencias que importan al orquestar un pipeline:
1. **El runner empieza vacío.** No tiene tu código (hay que hacer `checkout`), ni tus dependencias, ni tus datos, ni el modelo de ayer. Todo lo que el pipeline necesita debe llegar por el repositorio, por la instalación o por un artefacto.
2. **El runner desaparece al acabar.** Un modelo o una base que no se guarda como artefacto **se pierde**.
3. **Cada job es una máquina distinta.** Lo que un job deja en su disco no lo ve el siguiente: se pasa con artefactos (apartado 6).

Una trampa real: los `defaults.run.working-directory` de un workflow se **heredan** en todos los jobs. En `desplegar-gcp.yml` el segundo job **no hace checkout** y no existe la carpeta `04-Proyecto-Base`; por eso ese job fija `working-directory: .`. Sin ello falla con «No such file or directory».

## 3. Disparadores: push, workflow_dispatch y schedule

| Evento | Cuándo corre | En el curso |
|---|---|---|
| `push` (con `branches:`) | Cada vez que subes un commit (o creas una rama) que coincide | `lab/cloud-journey/**`, `lab/nueva-version/**`, `lab/**` |
| `workflow_dispatch` | A mano, con el botón **Run workflow**, y con entradas (`inputs`) opcionales | `puntuar-lote.yml`: `capacidad`, `corte`, `imagen` |
| `schedule` | A una hora fija (formato cron, en UTC) | `puntuar-lote.yml`: `cron: '17 5 * * *'`, todos los días a las 05:17 UTC |

Tres cosas que sorprenden y que pasaron en los ensayos:

1. **«Run workflow» solo aparece si el workflow está en la rama principal** (la rama por defecto del repositorio). Por eso los laboratorios no usan el botón: **se ensayan con un `push` a una rama con nombre**, y el nombre de la rama puede incluso **elegir el escenario** (`lab/nueva-version/muestra`, `…/completo-rechazo`, `…/completo`). Crear una rama nueva también es un push y dispara el workflow.
2. **El `schedule` solo corre desde la rama por defecto y en un *fork* viene desactivado.** Hay que activarlo en la pestaña **Actions**. Además GitHub puede **retrasar** un `schedule` varios minutos cuando hay carga: no es un reloj exacto. El minuto 17 es «raro» a propósito: a las horas en punto hay más carga.
3. **Un workflow solo se lanza si el evento coincide con sus filtros.** `puntuar-lote.yml` se dispara con un push solo si ese push cambia el propio workflow (o `explotacion.py`). Si no aparece ninguna ejecución: ¿está Actions activado en tu *fork*?, ¿la rama coincide con `branches:`?, ¿el push cambió algún archivo de los filtrados?

## 4. Secretos, variables y *environments*

| Qué | Para qué | Cómo se lee | Se ve en el registro |
|---|---|---|---|
| **Variable** (`vars`) | Configuración **no secreta** (región, nombre del proyecto, identificadores públicos) | `${{ vars.GCP_REGION }}` | Sí |
| **Secreto** (`secrets`) | Un valor que **no debe verse** | `${{ secrets.NOMBRE }}` | GitHub lo oculta (`***`), pero no es infalible |
| ***Environment*** | Un «entorno» con reglas de protección (revisores, rama permitida) y sus propias variables y secretos | `environment: produccion` en el job | — |

En el laboratorio Cloud Journey **no hay ningún secreto**: son cinco **variables** (`GCP_PROYECTO`, `GCP_REGION`, `GCP_PROVEEDOR_WIF`, `GCP_CUENTA_DESPLIEGUE`, `GCP_CUENTA_SERVICIO`). Ninguna sirve para entrar sola a nada: son nombres, no llaves. La entrada la da WIF.

**El *environment* `produccion` y por qué el nombre exacto importa.** Un job con `environment: produccion` **se detiene** hasta que un revisor lo aprueba (**Review deployments** › marcar `produccion` › **Approve and deploy**). Pero:

> Si el *environment* **no existe** (o está escrito distinto: `produccion` sin tilde, minúsculas), GitHub **lo crea solo y sin revisores**, y el job **no espera: publica directamente**. No hay error ni aviso. Es el fallo más peligroso de la sesión porque «parece que funciona».

Comprobación: **Settings › Environments** muestra `produccion` con «1 protection rule». Los pasos con capturas están en [`CONFIGURAR-REPOSITORIO.md`](../laboratorio-produccion-e2e/CONFIGURAR-REPOSITORIO.md).

Reglas de higiene:
- Nada de claves, tokens ni `.env` en el repositorio. Un secreto en el repositorio o en el registro de un workflow da acceso a quien lo lea, **para siempre** (el historial de git no se olvida).
- Un valor que viene de fuera (una entrada de `workflow_dispatch`, el nombre de una rama) **no se pega dentro de la orden**; se pasa por variable de entorno. `puntuar-lote.yml` lo hace así.

## 5. Entrar en Google Cloud sin claves: Workload Identity Federation (WIF)

**El problema.** Para que un workflow suba una imagen a Google Cloud necesita una identidad. La solución clásica es una clave JSON de una cuenta de servicio guardada como secreto: **una contraseña que no caduca**. En la organización del curso ni siquiera se puede: la política `iam.disableServiceAccountKeyCreation` **prohíbe crear claves** de cuentas de servicio. WIF es la vía que queda, y es la buena práctica de todas formas.

**La idea, paso a paso (conceptual):**

1. **Se prepara una vez, en Google Cloud** (lo hace `preparar-gcp-s4.sh`): un *pool* de identidades externas, un *proveedor* que dice «confío en los tokens de GitHub» y una **condición** que limita el acceso a **tu repositorio**. Además, una cuenta de servicio de despliegue (`sa-github-despliegue`) con los permisos justos.
2. **En cada ejecución**, el job pide a GitHub un **token OIDC**: un documento firmado, de corta vida, que dice «soy una ejecución de *este* repositorio». Para poder pedirlo, el job necesita el permiso `id-token: write`.
3. La action `google-github-actions/auth@v2` presenta ese token a Google, indicando el proveedor (`GCP_PROVEEDOR_WIF`) y la cuenta de despliegue (`GCP_CUENTA_DESPLIEGUE`).
4. Google comprueba la firma, el pool, el proveedor **y la condición del repositorio**. Si todo cuadra, entrega acceso **temporal** como `sa-github-despliegue`.
5. Con ese acceso temporal, `docker push` y `gcloud run deploy` funcionan. Cuando el job acaba, el acceso caduca. **No hay nada que robar ni que rotar.**
6. La API desplegada **corre con otra cuenta** (`sa-cloudrun-retencion`) que no tiene **ningún rol**: quien despliega no es quien ejecuta, y el servicio no puede hacer nada en tu proyecto.

Ejemplo real, de [`desplegar-gcp.yml`](../laboratorio-cloud-journey/desplegar-gcp.yml): el permiso `id-token: write` está **solo en el job de despliegue**, no en el de construir. Eso es mínimo privilegio (apartado 7).

Un detalle operativo que pasó el 26/11/2026: al borrar un pool de identidades, Google **no lo elimina del todo**; lo guarda **30 días** como `DELETED` y no deja reutilizar el nombre. `preparar-gcp-s4.sh` ya lo detecta y lo restaura; con una copia antigua del script, el paso falla con `NOT_FOUND`.

## 6. Caché, artefactos, `needs` y matrices

- **Caché** (`cache: pip` en `actions/setup-python`): guarda las dependencias descargadas **entre ejecuciones** para no volver a bajarlas. Es un acelerador: si no está, el workflow funciona igual, más lento. La clave de la caché depende de los archivos de dependencias (`cache-dependency-path`).
- **Artefacto** (`actions/upload-artifact` / `download-artifact`): un archivo que un job **guarda** para que lo use otro job o para que **tú lo descargues** después. Es la forma de pasar cosas entre jobs, y de no perder lo que el runner se llevaría al desaparecer. Dos ejemplos reales:
  - `puntuar-lote.yml` deja dos artefactos: **campana** (`campana_<corte>.csv`, todos los clientes ordenados) y **base-fs-produccion** (la base con la tabla `fs_produccion`).
  - `desplegar-gcp.yml` **pasa la imagen entre jobs**: el job 1 construye y **prueba** la imagen, la guarda con `docker save` como artefacto (`retention-days: 1`) y el job 2 la carga con `docker load`. Así se publica **la misma imagen que se probó**, no otra parecida reconstruida.
- **`needs:`** ordena los jobs: `needs: construir` hace que el job 2 espere al 1 **y no corra si el 1 falla**. En `nueva-version.yml` hay cuatro jobs encadenados (entrenar y comparar → construir y probar → publicar → abrir PR); si la puerta de calidad rechaza, los tres siguientes **ni se ejecutan** (salen omitidos).
- **Matrices** (`strategy.matrix`): ejecutar el **mismo job** con varios valores (por ejemplo, varias versiones de Python). **No se usan en los laboratorios.** Ejemplo **ilustrativo**, no ejecutado en el curso:

```yaml
jobs:
  pruebas:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
```

## 7. `concurrency`, permisos mínimos y límites de tiempo

- **`concurrency`** evita que dos ejecuciones del mismo grupo corran a la vez. En el curso: `group: gcp-despliegue` (dos despliegues al mismo servicio a la vez no tienen sentido), `puntuar-lote`, y **`nueva-version-modelo` compartido por `nueva-version.yml` y `rollback.yml`** (no se publica y se vuelve atrás a la vez), todos con `cancel-in-progress: false` (la ejecución en curso no se cancela; la nueva espera).
  > **Trampa real:** un run que está **esperando aprobación bloquea al siguiente del mismo grupo**. Si lanzas otra ejecución y se queda «en cola» sin motivo aparente, mira si hay una anterior esperando: **apruébala o cancélala** (**Cancel workflow**).
- **Permisos mínimos** (`permissions:`): el token del workflow solo debería poder lo imprescindible. Patrón del curso: `contents: read` para todo el workflow y **ampliar solo en el job que lo necesita**: `packages: write` solo en el job que publica en GHCR; `contents: write` y `pull-requests: write` solo en el que abre el *pull request*; `id-token: write` solo en el que entra en Google Cloud. Si un job es comprometido, el daño queda acotado.
- **`timeout-minutes`**: un job colgado no debe consumir minutos indefinidamente. Los workflows del curso lo fijan en cada job.
- **Los workflows nunca empujan a `develop` ni a `main`**: cuando hay que cambiar una referencia (`models/referencia.json`), **abren un pull request** que alguien revisa y fusiona.

## 8. CI frente a CD, y las aprobaciones

| | **CI** (integración continua) | **CD** (entrega / despliegue continuo) |
|---|---|---|
| Pregunta | «¿Este cambio rompe algo?» | «¿Lo llevamos a producción?» |
| Qué hace | Instala, ejecuta pruebas y calidad, entrena, calcula métricas | Construye la imagen, la publica, la despliega |
| Quién decide | La máquina (verde o rojo) | La máquina **y, si hace falta, una persona** |
| Ejemplo real | `validar-produccion.yml`; el job «entrenar» de `nueva-version.yml` | `publicar` (GHCR) y `desplegar` (Cloud Run) |

**La puerta de calidad** es CI con consecuencias: en `nueva-version.yml` el AUC de test de la versión nueva se compara con el de `models/referencia.json` con una **tolerancia de 0,02**. Misma huella de datos → **igual** (nada que publicar). El AUC cae más que la tolerancia → **rechazada** (el job sale en rojo con el motivo). En otro caso → **aceptada** y sigue. Una tolerancia **negativa** es una exigencia de mejora (`-0.10`: «debe mejorar al menos 0,10») y sirve para ensayar el rechazo con datos reales.

**La aprobación manual** (`environment: produccion` con revisores) separa «las máquinas dicen que está bien» de «una persona autoriza publicar». Qué hay que tener claro:
- Solo se pide en el job que publica; construir y probar **no** necesita aprobación.
- Quien aprueba debe poder ver **qué** se va a publicar (el resumen del run lo dice: versión, AUC, imagen).
- Solo funciona si el *environment* existe con revisores (apartado 4).
- Un **rollback** también es una publicación controlada: `rollback.yml` abre un PR para volver a la versión anterior; no borra imágenes ni historial.

## 9. Costes y borrar lo creado

- **Actions** gasta minutos de ejecución (consulta los límites de tu cuenta en la documentación vigente: sin dato aquí).
- **Google Cloud** cobra por lo que **existe**, aunque no lo uses. Lo que más cobra si se olvida, por tiempo mientras existen: el **endpoint de Vertex AI** (práctica 04) y el **clúster de GKE** (práctica 02). Cloud Run con `--min-instances=0` no deja nada encendido cuando nadie llama, y `--max-instances=1` pone un tope.
- Un **presupuesto con alertas** (el del laboratorio: 20 € con avisos al 50, 90 y 100 %) **avisa, no corta el gasto**.
- Regla del curso: **crea → prueba → borra**. Se borra con `borrar-gcp-s4.sh` (Cloud Journey: pool WIF, proveedor, cuentas y presupuesto) y con `borrar-todo.sh` de [`practicas-gcp`](../practicas-gcp/borrar-todo.sh); se borra también el Codespace, y se revisa la factura al día siguiente. Las APIs habilitadas **no se deshabilitan** (no cuestan).
- Dos hechos sobre la cuenta del curso: el crédito de la prueba gratuita **no cubre Vertex AI ni Gemini** en cuentas dadas de alta desde el 16/11/2026, y **Gemini no está en la región de Santiago** (`southamerica-west1`); se usa la ubicación `global`.

## 10. Errores que pasaron de verdad

| Síntoma | Causa | Qué hacer |
|---|---|---|
| El job de publicar **no espera** aprobación | El *environment* no existe o no tiene revisores | Crearlo con el nombre exacto y revisores (apartado 4) |
| No aparece **ningún run** | Actions desactivado en el *fork*, o la rama/ruta no coincide con el filtro | Pestaña Actions; revisar `on:` |
| «Run workflow» **no aparece** | El workflow no está en la rama principal | Ensayar con un push a una rama `lab/…` |
| El run nuevo se queda **en cola** | Otro run del mismo grupo `concurrency` espera aprobación | Aprobar o cancelar el anterior |
| El último paso (abrir el PR) **falla** | Falta el permiso «Allow GitHub Actions to create and approve pull requests» | **Settings › Actions › General › Workflow permissions** |
| «No such file or directory» en un job sin `checkout` | Hereda un `working-directory` que no existe | `working-directory: .` en ese job |
| Falla el paso de entrada a Google Cloud | Variables mal copiadas, o el repositorio de la condición no es el tuyo | Repasar las cinco variables y el proveedor |
| `NOT_FOUND` al recrear el proveedor WIF | El pool está 30 días en estado `DELETED` | Usar el script actual (lo restaura) |
| Tildes que desaparecen en Cloud Shell | Se pierden al teclear desde otra herramienta | Descripciones de `gcloud` sin tildes |

## 11. Autoevaluación

1. ¿Por qué un modelo entrenado en un job no está en el siguiente si no lo guardas? *Cada job corre en un runner distinto y el runner se destruye.*
2. ¿Por qué ensayamos con ramas `lab/…` y no con «Run workflow»? *El botón solo aparece si el workflow está en la rama principal.*
3. ¿Qué pasa si el *environment* `produccion` no existe? *GitHub lo crea sin revisores y el job publica sin pedir aprobación.*
4. ¿Qué es lo que **no** hay en WIF? *Ninguna clave guardada; el acceso es temporal y se pide en cada ejecución.*
5. ¿Por qué `id-token: write` está solo en el job de despliegue? *Mínimo privilegio.*
6. ¿Por qué se pasa la imagen entre jobs como artefacto en vez de reconstruirla? *Para publicar la misma que se probó.*
7. ¿Qué bloquea a un run nuevo del mismo grupo `concurrency`? *Uno anterior esperando aprobación.*
8. ¿Qué cobra más si se olvida en la práctica de Vertex AI y en la de GKE? *El endpoint y el clúster, por tiempo.*

## 12. Glosario

| Término | Significado |
|---|---|
| **CI / CD** | Integración continua (probar cada cambio) / entrega o despliegue continuo (publicarlo) |
| **Workflow, job, step, runner** | Ver apartado 2 |
| **Evento, disparador** | Lo que inicia un workflow: `push`, `workflow_dispatch`, `schedule` |
| **Artefacto** | Archivo que un job guarda al terminar (para otro job o para descargarlo) |
| **Caché** | Copia de dependencias entre ejecuciones para acelerar; no sustituye a un artefacto |
| ***Environment*** | Entorno de GitHub con reglas (revisores) y sus variables; `produccion` en el curso |
| **Variable / secreto** | Configuración visible / valor oculto en el registro |
| **`concurrency`** | Grupo que impide ejecuciones simultáneas |
| **`needs`** | Orden entre jobs: el segundo espera (y depende) del primero |
| **OIDC** | *OpenID Connect*: forma estándar de demostrar quién eres con un token firmado |
| **WIF** | *Workload Identity Federation*: acceso temporal a Google Cloud a partir del token de GitHub, sin claves |
| **Cuenta de servicio** | Identidad de un programa, no de una persona; aquí hay una que despliega y otra con la que corre la API |
| **GHCR** | *GitHub Container Registry*: almacén de imágenes de GitHub |
| **Artifact Registry** | Almacén de imágenes de Google Cloud |
| **Cloud Run** | Ejecuta un contenedor con URL pública y escala a cero |
| **Puerta de calidad** | Comparación automática que rechaza una versión que empeora más que la tolerancia |
| **Rollback** | Volver a la versión anterior sin borrar nada |

## Dónde seguir
- Clase de apoyo: [`clase-onpremise-a-nube/guia.md`](../clase-onpremise-a-nube/guia.md) (29 diapositivas en [`index.html`](../clase-onpremise-a-nube/index.html)).
- Laboratorios: [`laboratorio-produccion-e2e/guia.md`](../laboratorio-produccion-e2e/guia.md) · [`laboratorio-cloud-journey/guia.md`](../laboratorio-cloud-journey/guia.md) · [`practicas-gcp/README.md`](../practicas-gcp/README.md) · extra opcional [`extra-estilo-llm/README.md`](../extra-estilo-llm/README.md).
- Ramas y git: [`git-y-ramas.md`](../../../07-Recursos/guias/git-y-ramas.md).
