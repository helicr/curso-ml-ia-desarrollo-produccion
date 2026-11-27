# Laboratorio de cierre de S4: producción de punta a punta del caso Retail

En tu copia del repositorio del curso (tu *fork*) y desde tu Codespace vas a llevar a producción el modelo «retención a 90 días» del caso Online Retail II:

1. **configurar** el repositorio una vez (un *environment* con revisores y un permiso);
2. ver los **tres modos de explotación** del mismo modelo: **lote**, **bajo demanda** y **online**, y el **panel** que los reúne;
3. entrenar una **versión nueva** con **puerta de calidad**, **aprobación humana**, publicación en **GHCR** y **pull request** de la referencia;
4. **volver atrás** (rollback) sin borrar nada.

No se usa Google Cloud. Presentación: [`index.html`](index.html) (cada orden se copia con **⧉**). Workflows listos para copiar: [`puntuar-lote.yml`](puntuar-lote.yml), [`validar-produccion.yml`](validar-produccion.yml), [`nueva-version.yml`](nueva-version.yml) y [`rollback.yml`](rollback.yml). Complementos: [`CONFIGURAR-REPOSITORIO.md`](CONFIGURAR-REPOSITORIO.md) (los ajustes de GitHub, con capturas) y [`CODESPACE.md`](CODESPACE.md) (levantar el panel).

> **Estado de validación.** Todos los runs de esta guía se ejecutaron de verdad el 22/11/2026 en la cuenta del profesor (`helicr`) y las capturas son de esos runs. **Sin verificar:** el *compose* del panel dentro de un **Codespace** (se probó en local y en Actions con `validar-produccion.yml`), el `schedule` de las 05:17 UTC corriendo solo (se lanzó con un push), descargar la imagen con `docker pull` desde un Codespace, el tamaño de la imagen (**sin dato**) y la duración total del laboratorio para un grupo (**sin dato**). Las latencias son locales (`TestClient`), no en red.

Los números de run de los ejemplos se abren con `https://github.com/helicr/curso-ml-ia-desarrollo-produccion/actions/runs/<nº>`. Los tuyos serán otros.

---

## 0. Los tres modos y las palabras que vas a oír

| Modo | La pregunta del negocio | De dónde salen las 13 variables | Cuándo se calcula | Dónde corre aquí |
|---|---|---|---|---|
| **1 · Lote** (*batch*) | «¿A quién llamo hoy?» Se puntúa a **todos** y se ordena | del pipeline, en el corte del día | una vez al día: `schedule` 05:17 UTC y **Run workflow** | GitHub Actions: `puntuar-lote.yml` |
| **2 · Bajo demanda** | «¿Qué probabilidad tiene el cliente 12670?» | **leídas** de la tabla `fs_produccion` (ya calculadas, las de ayer) | al preguntar, sin calcular variables | API + interfaz: `GET /bajo-demanda/{id}` y `POST /bajo-demanda` |
| **3 · Online** | «Acaba de comprar: ¿qué le ofrezco **ahora**?» | **calculadas al vuelo** con el SQL de la capa FS, hasta el instante de la petición | al preguntar, con datos frescos | API + interfaz: `GET /online/{id}?corte=` |

Los tres usan **la misma versión** del modelo y, mientras no llegan datos nuevos, dan **la misma probabilidad** para el mismo cliente y corte.

| Palabra | Qué es |
|---|---|
| **GHCR** | *GitHub Container Registry* (`ghcr.io`): el almacén de imágenes de contenedor de GitHub. Aquí guarda `retencion-api`, la API con el modelo dentro |
| **PR** (*pull request*) | una propuesta de cambio entre dos ramas, con revisión y fusión (*merge*) a mano. Nuestros workflows **nunca** empujan a `develop` ni a `main`: abren un PR |
| ***environment*** | un «entorno» de GitHub con reglas de protección. El nuestro se llama `produccion` y exige que una persona **revise y apruebe** antes de publicar |
| **huella** (de datos) | resumen corto de los datos de entrenamiento: los mismos datos dan la misma huella. Va en la etiqueta de la imagen: `retencion-api:v1-35a94deb4e04ab4a` |
| **AUC** | área bajo la curva ROC: **0,5** es el azar y **1** es acertar siempre. Es la métrica de la puerta de calidad |
| **tolerancia** | cuánto puede **empeorar** el AUC de test la versión nueva sin ser rechazada (por defecto **0,02**) |
| **campeón / candidata** | el campeón es el modelo en producción; la candidata, la versión nueva que aspira a sustituirlo |
| `referencia.json` | la ficha de la versión en producción en el repositorio: versión, huella, imagen y métricas de test |

**Qué es «el modelo en producción»:** la imagen `ghcr.io/<propietario>/retencion-api:v<N>-<huella>` **más** `04-Proyecto-Base/models/referencia.json` **más** `models/historial_versiones.json` (la pestaña **Versiones** del panel). Una versión pasa a ser «la de producción» cuando **se fusiona** el PR que actualiza esos archivos.

---

## 1. Preparar la rama y los cuatro workflows

En tu fork, abre un Codespace **desde tu fork**, en `develop`. En un fork, entra antes en la pestaña **Actions** y acepta el aviso para activar los workflows (el texto exacto puede cambiar).

> **Al hacer el fork, desmarca «Copy the `main` branch only».** Todo el material de este laboratorio está en la rama `develop`. Si dejas esa casilla marcada, tu fork solo tendrá `main`: no existirá `develop` y fallarán «Create codespace on develop» y `git switch develop`.

```bash
git switch develop
git pull
git switch -c lab/produccion-e2e
mkdir -p .github/workflows
cp 01-Sesiones/S4-Orquestacion-y-CI-CD/laboratorio-produccion-e2e/{puntuar-lote,validar-produccion,nueva-version,rollback}.yml .github/workflows/
git add .github/workflows
git commit -m "Laboratorio de cierre de S4: workflows de producción"
```

**Aún no hagas `git push`:** primero se configura el repositorio (paso 2), para que el *environment* ya exista.

**Qué debes ver.** `git status` limpio tras el commit, en `lab/produccion-e2e`, con `.github/workflows/` y cuatro archivos nuevos: `puntuar-lote.yml`, `validar-produccion.yml`, `nueva-version.yml` y `rollback.yml`.

**Si falla.**
- `cp: cannot stat …`: tu fork no tiene la carpeta del laboratorio. Haz **Sync fork** en GitHub y `git pull`, o abre cada YAML y pega su contenido.
- Si tu terminal no entiende las llaves `{a,b}`, copia los cuatro archivos de uno en uno.
- `git switch develop` dice `invalid reference: develop`, o «Create codespace on develop» no ofrece esa rama: tu fork se hizo con «Copy the `main` branch only» y no tiene `develop`. Dos soluciones:
  1. **Traer `develop` al fork que ya tienes:** en GitHub, en tu fork, pestaña **Code** › desplegable de ramas › **View all branches**. Si `develop` no está, pulsa **Sync fork** › **Update branch** en `main`; si sigue sin aparecer, usa la solución 2. (Sin dato: no se ha probado en este laboratorio qué opción de GitHub crea `develop` en un fork ya hecho.)
  2. **Rehacer el fork:** **Settings** › al final, **Delete this repository** (solo si no tiene nada tuyo que quieras conservar) y vuelve a hacer el fork con «Copy the `main` branch only» **desmarcado**.
- **Un Codespace no se actualiza solo.** Si el profesor ha publicado cambios en `develop` después de crear tu Codespace, no los verás hasta que los traigas:
  ```bash
  git fetch origin
  git status -sb          # debe decir «behind N» (N commits por detrás)
  git pull origin develop
  ```
  En un fork, antes haz **Sync fork** en GitHub si `origin/develop` no avanza.
- `&&` no existe en **Windows PowerShell 5.1**: encadena con `;` o lanza las órdenes una a una. Y las llaves `{a,b}` del `cp` son de bash: en PowerShell o `cmd`, copia los archivos de uno en uno.

---

## 2. Configurar el repositorio (una sola vez)

Detalle y capturas en [`CONFIGURAR-REPOSITORIO.md`](CONFIGURAR-REPOSITORIO.md). Resumen:

1. **Settings** › **Environments** › **New environment** › nombre exacto `produccion` (sin tilde) › marca **Required reviewers** y añádete a ti mismo › **Save protection rules**.
2. **Settings** › **Actions** › **General** › **Workflow permissions** › marca **Allow GitHub Actions to create and approve pull requests** › **Save**.

| El environment con su regla | Revisores y «Save protection rules» |
|---|---|
| ![El environment produccion con una regla de protección](img/cfg-01-environments.webp) | ![Required reviewers con helicr](img/cfg-02-environment-revisores.webp) |
| **Actions habilitado** | **Permiso para abrir PR** |
| ![Allow all actions and reusable workflows](img/cfg-03-actions-permisos.webp) | ![Casilla Allow GitHub Actions to create and approve pull requests](img/cfg-04-workflow-permissions.webp) |

**Qué debes ver.** En **Settings › Environments**, `produccion` con «1 protection rule»; en **Workflow permissions**, la casilla marcada.

> **El nombre es exactamente `produccion`**, en minúsculas y sin tilde: no vale `prod`, `Produccion` ni `producción`. El workflow pide un *environment* con ese nombre; si no lo encuentra, GitHub **crea uno nuevo sin revisores** y el despliegue **no pide aprobación**: publica directamente.

**Si falla (casos que pasaron en los ensayos).**
- Si el *environment* **no existe**, se llama de otra forma (por ejemplo `prod`) o no tiene revisores, GitHub lo crea solo **sin revisores** y el trabajo de publicación **no espera**: publica directamente. Vuelve a este paso, comprueba el nombre en **Settings › Environments** y corrígelo o créalo con el nombre exacto.
- Sin el permiso de PR, el **último paso** (abrir el pull request) **falla**.

---

## 3. Modo 1 · puntuación por lotes (`puntuar-lote.yml`)

**Cuándo se ejecuta.**
- `schedule`: **todos los días a las 05:17 UTC** (`cron: '17 5 * * *'`). El minuto 17 es «raro» a propósito: a las horas en punto GitHub va cargado y puede retrasar un `schedule` varios minutos.
- `workflow_dispatch` (**Run workflow**), con tres entradas: `capacidad` (0.10 = el 10 %), `corte` (AAAA-MM-DD) e `imagen` (`construir` o `ghcr`).
- `push` a una rama `lab/**`, solo si cambia el workflow o `explotacion.py`.

**En un fork el `schedule` viene desactivado**, y **Run workflow** solo aparece si el workflow está en la rama por defecto. Por eso en el laboratorio se dispara con el **push**:

```bash
git push -u origin lab/produccion-e2e
```

Este push lanza **dos** workflows: **Puntuar por lotes** y **Validar la producción completa** (también cambia su YAML). Mírales en la pestaña **Actions**. Al subir los cuatro workflows arrancan solos **dos runs**: «Puntuar por lotes» con **3 cajas** (trabajos) y «Validar la producción completa» con **1 caja**. No es un error: son dos workflows distintos y el segundo hace todo en un solo trabajo.

![Puntuar por lotes en verde](img/gh-10-run-lote.webp)

**Qué hace.** Tres trabajos: **1 · Preparar datos** (operacional + pipeline), **2 · Puntuar a todos los clientes** (levanta la API en un contenedor y ejecuta `explotacion --url`) y **3 · Resumen**. Deja dos artefactos: **campana** (`campana_<corte>.csv` y `.json`, todos los clientes ordenados) y **base-fs-produccion** (la base con la tabla `fs_produccion`, la que lee «bajo demanda»).

**Qué debes ver (ejemplo real).** Run nº 45026646958 en verde, 2 m 55 s: trabajos de **55 s**, **111 s** y **4 s**. El resumen enseña el corte **2011-12-10** y **148** clientes puntuados.

![Validar la producción completa en verde](img/gh-11-run-validar.webp)

Run nº 45026646944 de **Validar la producción completa**: verde, un trabajo de **133 s** (total 2 m 16 s). Levanta API + interfaz con `docker compose` en Actions y comprueba los tres modos con `curl`.

**Si falla.**
- **`git push` rechazado con `! [rejected] … (non-fast-forward)`** (o «fetch first»). *Non-fast-forward* significa que la rama del servidor tiene commits que la tuya no tiene (o historias distintas), así que Git no puede «avanzar» la rama remota sin pisarla. Pasa si empujas a un repositorio donde **ya existe una rama con ese nombre**: en el repositorio del profesor `lab/produccion-e2e` y `lab/cloud-journey/despliegue` ya existen (ramas de ensayo); en el **fork de un alumno** no existen, así que allí no debería pasar. **No hagas `git pull` ni `git push --force`:** el primero mezclaría el trabajo ajeno con el tuyo y el segundo borraría el del otro. La solución es **cambiar el nombre de tu rama** conservando el prefijo:
  ```bash
  git branch -m lab/produccion-e2e lab/produccion-e2e-2
  git push -u origin lab/produccion-e2e-2
  ```
  El prefijo importa porque los workflows solo arrancan con ciertos nombres: las ramas del laboratorio empiezan por `lab/` (`lab/produccion-e2e-2` vale); las de escenario, por `lab/nueva-version/` y `lab/rollback/`; las del Cloud Journey, por `lab/cloud-journey/`. Si renombras la rama base, usa el nombre nuevo donde la guía dice `lab/produccion-e2e` (por ejemplo en `git switch lab/produccion-e2e-2` del apartado 5.1). Y si te falla una rama de escenario, añade `-2` al final de su nombre (`lab/nueva-version/muestra-2`): conserva el nombre del escenario, que es lo que lee el workflow.
- No aparece ningún run: Actions sin activar en el fork, o la rama no empieza por `lab/`.
- «Puntuar por lotes» solo se lanza con el push si ese push cambia el workflow (o `explotacion.py`). Si ya lo habías subido, hazlo desde **Actions › Run workflow** (requiere el workflow en la rama por defecto) o cambia una línea del YAML.

---

## 4. Modos 2 y 3 y el panel, en el Codespace

> **Sin verificar en Codespace.** Estas órdenes se probaron en local y en Actions (`validar-produccion.yml`); en un Codespace todavía no se han ejecutado. Más detalle en [`CODESPACE.md`](CODESPACE.md).

Desde la carpeta del proyecto:

```bash
cd 04-Proyecto-Base
python -m ia_mlops.operacional
python -m ia_mlops.pipeline
python -m ia_mlops.explotacion
docker compose -f deploy/docker/compose-produccion.yaml up --build -d
docker compose -f deploy/docker/compose-produccion.yaml ps
curl -fsS http://127.0.0.1:8090/listo
```

Las tres órdenes de Python dejan los datos, el modelo y el lote (el *compose* no los crea). Después, en la pestaña **Puertos** del Codespace abre el puerto **8090** y añade `/panel` a la dirección.

**Qué debes ver.** `ps`: dos servicios, `api` e `interfaz`; la `api` pasa a *healthy*. `/listo` responde con `"estado": "listo"`. El panel tiene cuatro pestañas: **Lote**, **Bajo demanda**, **Online** y **Versiones**.

**Si falla.**
- `No existe …`: te saltaste una de las tres órdenes de Python; ejecútalas en ese orden.
- `curl` responde 503: la API aún no está sana. `docker compose -f deploy/docker/compose-produccion.yaml logs api interfaz`.
- Pestaña Lote vacía («Todavía no hay campaña»): `reports/campana` estaba vacía al levantar; repite las tres órdenes y reinicia con `down` y `up`.

### 4.1 Bajo demanda y online con `curl`

```bash
ID=12670
curl -s http://127.0.0.1:8090/bajo-demanda/$ID
curl -s http://127.0.0.1:8090/online/$ID
curl -s -X POST http://127.0.0.1:8090/demo/compra -H 'content-type: application/json' -d "{\"cliente_id\": $ID, \"importe\": 120.5, \"unidades\": 3}"
curl -s http://127.0.0.1:8090/bajo-demanda/$ID
curl -s http://127.0.0.1:8090/online/$ID
curl -s -X POST http://127.0.0.1:8090/demo/reiniciar
```

(El cliente 12670 es del lote del 2011-12-10 de las capturas; si el tuyo es otro, usa uno de la pestaña **Lote**.)

**Si tu terminal no es bash** (por ejemplo, el portátil con Windows, fuera del Codespace). Las órdenes de arriba usan sintaxis de bash: `ID=12670`, `$ID`, comillas simples y, en otras guías, `; echo`. No funcionan igual en `cmd` ni en PowerShell. Variantes equivalentes (con el cliente escrito a mano):

- **Windows `cmd`:** sin `; echo`, sin comillas simples y con el JSON entre comillas dobles escapando las interiores con `\"`.

  ```bat
  curl -s http://127.0.0.1:8090/bajo-demanda/12670
  curl -s http://127.0.0.1:8090/online/12670
  curl -s -X POST http://127.0.0.1:8090/demo/compra -H "content-type: application/json" -d "{\"cliente_id\": 12670, \"importe\": 120.5, \"unidades\": 3}"
  curl -s -X POST http://127.0.0.1:8090/demo/reiniciar
  ```

- **Windows PowerShell 5.1:** escribe **`curl.exe`**, no `curl`: en 5.1 `curl` es un alias de `Invoke-WebRequest`, que tiene otros parámetros y falla con `-s` o `-X`. El JSON va entre comillas simples con `\"` por dentro (PowerShell 5.1 pasa las comillas dobles a los programas externos de forma poco fiable), y `$id` es una variable de PowerShell.

  ```powershell
  $id = 12670
  curl.exe -s http://127.0.0.1:8090/bajo-demanda/$id
  curl.exe -s http://127.0.0.1:8090/online/$id
  curl.exe -s -X POST http://127.0.0.1:8090/demo/compra -H "content-type: application/json" -d '{\"cliente_id\": 12670, \"importe\": 120.5, \"unidades\": 3}'
  curl.exe -s -X POST http://127.0.0.1:8090/demo/reiniciar
  ```

  En PowerShell 5.1 el operador `&&` **no existe** (es un error de sintaxis): usa `;` para encadenar, o una orden por línea.

*Sin verificar con `curl.exe` real:* el paso de las comillas en `cmd` y en PowerShell 5.1 se comprobó con un programa que imprime los argumentos recibidos, no contra el panel.

**Qué debes ver.** Antes de la compra, bajo demanda y online dan la **misma** `probabilidad` y el mismo `corte`. Después, **bajo demanda no cambia** (lee la tabla de ayer) y **online cambia** (suma la compra). La compra se guarda en una **copia** de la base dentro del contenedor, nunca en la del proyecto; el último `curl` deja la demo como al principio.

**Tiempos medidos** (p50, con `TestClient`, local, **no en red**): bajo demanda **26,8 ms**, online **33,5 ms**.

**Si falla.**
- `404` «no está en fs_produccion»: ese cliente no tiene compras válidas antes del corte; elige otro de la lista del lote.
- `404` «El modo demo está apagado»: usa `compose-produccion.yaml`, no `compose.yaml`.

### 4.2 El panel

| Lote | Bajo demanda | Versiones |
|---|---|---|
| ![Pestaña Lote](img/panel-1-lote.webp) | ![Pestaña Bajo demanda](img/panel-2-bajo-demanda.webp) | ![Pestaña Versiones](img/panel-5-versiones.webp) |

- **Lote:** corte 2011-12-10, 148 clientes puntuados, **15** en la campaña (el 10 %), probabilidad media **48,6 %**, y los 20 primeros clientes.
- **Bajo demanda:** el cliente 12670 con **79,9 %**, tramo **alta**; avisa de que «las variables son las de ayer».
- **Versiones:** en producción **v1** (AUC de test 0,747); coincide con el modelo que sirve. El historial sale vacío porque aún no hay versión 2.

### 4.3 La compra simulada (pestaña Online)

En **Online**, con el cliente 12670, importe 120,5 y 3 unidades, pulsa **Simular una compra nueva**.

| Antes | Después |
|---|---|
| ![Online antes: 79,9 % en los tres](img/panel-3-online-antes.webp) | ![Online después: 76,2 %](img/panel-4-online-despues.webp) |

**Qué debes ver.** Antes, **79,9 %** en lote, bajo demanda y online. Después, online pasa a **76,2 %** y lote y bajo demanda **siguen en 79,9 %** hasta que se recalcule `fs_produccion`.

Para parar el panel: `docker compose -f deploy/docker/compose-produccion.yaml down`.

---

## 5. Una versión nueva (`nueva-version.yml`)

### 5.1 Cómo se ensaya sin tocar la rama principal

**Run workflow** solo aparece si el workflow está en la rama por defecto. Por eso cada escenario se lanza con un **push** a una rama de ensayo `lab/nueva-version/<escenario>`, y **el nombre de la rama elige el escenario**:

| Rama | Escenario | Resultado esperado |
|---|---|---|
| `lab/nueva-version/muestra` | datos de la muestra (la fuente de la v1) | **IGUAL**: misma huella; trabajos 2 a 4 omitidos |
| `lab/nueva-version/completo-rechazo` | Excel completo y **tolerancia -0,10** (se exige mejorar 0,10) | **RECHAZADA**: el trabajo 1 sale en rojo |
| `lab/nueva-version/completo` | Excel completo, tolerancia por defecto (0,02) | **ACEPTADA**: construye, espera aprobación, publica y abre el PR |

Hazlos **en este orden** y deja `completo` el último (se queda esperando tu aprobación). Siempre desde la rama `lab/produccion-e2e`, que ya tiene los workflows:

```bash
git switch lab/produccion-e2e
git switch -c lab/nueva-version/muestra
git push -u origin lab/nueva-version/muestra
# cuando acabe, el rechazo
git switch lab/produccion-e2e && git switch -c lab/nueva-version/completo-rechazo
git push -u origin lab/nueva-version/completo-rechazo
# el último: el completo (espera aprobación)
git switch lab/produccion-e2e && git switch -c lab/nueva-version/completo
git push -u origin lab/nueva-version/completo
```

(Si en el apartado 3 tuviste que renombrar tu rama base, por ejemplo a `lab/produccion-e2e-2`, usa ese nombre en los `git switch`. Si algún `git push` de estas ramas se rechaza con `non-fast-forward`, es el mismo caso: la rama ya existe en ese repositorio; no hagas `git pull` ni `--force`, renómbrala añadiendo `-2` y conserva el prefijo `lab/nueva-version/` o `lab/rollback/`.)

(El `git switch lab/produccion-e2e` inicial deja claro desde qué rama sale cada una. Crear una rama es un push y dispara el workflow aunque apunte al mismo commit.)

### 5.2 Cómo se comporta el pipeline

Cuatro trabajos, cada uno necesita que el anterior haya ido bien:

1. **Entrenar y comparar con la versión en producción.** Entrena con la fuente pedida y **compara** con `models/referencia.json`: la **puerta de calidad** es el **AUC de test** frente al de la referencia, con una **tolerancia de 0,02** (`config.TOLERANCIA_COMPARACION`). **Misma huella de datos → igual** (nada que publicar; se omiten los trabajos 2 a 4). **El AUC cae más que la tolerancia → rechazada** (el trabajo falla en rojo con el motivo). **En otro caso → aceptada.**
2. **Construir la imagen, probarla y comparar campeón y candidata.** Construye la API con el modelo nuevo, la prueba (`/salud`, `/listo`, `/modelo` y una predicción) y compara cuántos clientes cambian de tramo (alta, media o baja) entre la versión en producción y la nueva, puntuando las **mismas** filas de test.
3. **Publicar en GHCR (con aprobación manual).** **Espera la aprobación** del *environment* `produccion`. Aprobada, sube la imagen ya probada a GHCR con la etiqueta `v<N+1>-<huella>`. Es el único trabajo con permiso para escribir paquetes.
4. **Abrir el PR que actualiza `models/referencia.json`.** Abre un PR desde la rama `referencia/v<N+1>-<nº de ejecución>` con la nueva ficha y el historial. **Nunca** hace push a `develop` ni a `main`.

Una **tolerancia negativa** es una **exigencia de mejora**: `-0.10` significa «la versión nueva debe mejorar al menos 0,10». Sirve para ensayar el rechazo con datos reales, porque con el Excel completo el modelo nuevo **no empeora**.

### 5.3 Escenario «igual»

![Nueva versión: igual · nada que publicar](img/gh-12-nueva-igual.webp)

**Qué debes ver (ejemplo real).** Rama `lab/nueva-version/muestra`, run nº 45027468464, **en verde**. El trabajo 1 tarda **64 s**; los trabajos 2, 3 y 4 salen **omitidos** (gris, con un círculo tachado). El resumen dice «Nueva versión del modelo · IGUAL · nada que publicar» y «los datos son los mismos que los de la versión 1 (huella 35a94deb4e04ab4a)».

### 5.4 Escenario «rechazada»

![Nueva versión: rechazada](img/gh-13-nueva-rechazada.webp)

**Qué debes ver (ejemplo real).** Rama `lab/nueva-version/completo-rechazo`, run nº 45027468487, **en rojo** en el paso «Rechazar la versión si empeora más que la tolerancia» del trabajo 1; total 3 m 53 s. Los trabajos 2, 3 y 4 no se ejecutan. AUC de test **0,7956** frente a **0,7471**: la versión nueva **mejora** +0,0485, pero se exigía +0,10.

> **Nota honesta sobre esta captura.** Se hizo **antes de corregir el texto** del motivo: pone «empeora más que la tolerancia de -0.1» con una diferencia de +0.0485, lo que no tiene sentido. El texto actual del código, para una tolerancia negativa, dice: «no mejora lo exigido (al menos +0.1, tolerancia de -0.1). No se publica.». La decisión (rechazada) es la misma.

### 5.5 Escenario «aceptada»: espera tu aprobación

Con `lab/nueva-version/completo`, los trabajos 1 y 2 acaban bien y el 3 se queda en **Waiting**.

![Run esperando aprobación](img/gh-01-esperando-aprobacion.webp)

*Esta captura es del run nº 3 de este mismo escenario; el que acabó publicando fue el nº 5. El paso de espera es idéntico.*

**Qué debes ver.** Un aviso amarillo: «**helicr requested your review to deploy to produccion**» (con tu usuario) y el botón **Review deployments**. Resumen del trabajo 1: **ACEPTADA**, AUC de test 0,7956 frente a 0,7471 (diferencia +0,0485), dentro de la tolerancia de 0,02.

**Para aprobar:** **Review deployments** › marca `produccion` › **Approve and deploy**.

**Si falla (casos reales que pasaron).**
- **El run nuevo no arranca y se queda en cola.** Un run **esperando aprobación bloquea** al siguiente del **mismo grupo de *concurrency*** (`nueva-version-modelo`, compartido con `rollback.yml`). **Cancela** el run viejo (**Cancel workflow**) o **apruébalo**.
- **No te pide aprobación** y publica directamente: el *environment* `produccion` no existía o no tiene revisores (paso 2, «A»).
- **El trabajo «Publicar» falla con «No such file or directory».** Un trabajo **sin `checkout`** hereda `defaults.run.working-directory: 04-Proyecto-Base`, que no existe en ese trabajo. Se arregló con `working-directory: .` en el trabajo `publicar` (una prueba del repositorio lo vigila).
- **El último paso falla** al abrir el PR: te falta el permiso «Allow GitHub Actions to create and approve pull requests» (paso 2, «B»).

### 5.6 Publicada y con el PR abierto

| El run terminado | El PR nº 2 | Archivos cambiados |
|---|---|---|
| ![Run nº 5 en verde](img/gh-02-run-publicado.webp) | ![PR de la referencia](img/gh-03-pr-referencia.webp) | ![Cambios del PR](img/gh-04-pr-cambios.webp) |

**Qué debes ver (ejemplo real).** Run nº 45030152194 (nº 5) en verde: **entrenar 191 s**, **construir 138 s**, **publicar 17 s** tras aprobar, **referencia 14 s**. (La captura marca 1 h 19 min en total porque incluye la espera hasta aprobar.) La imagen publicada es `ghcr.io/helicr/retencion-api:v2-3521a0421905ba28`.

Y un PR: **nº 2 «Referencia del modelo: v2-3521a0421905ba28»**, abierto por `github-actions[bot]` desde la rama `referencia/v2-45030152194`, con la tabla v1 → v2 (AUC **0,7471 → 0,7956**). Cambia dos archivos: `models/referencia.json` y `models/historial_versiones.json` (la v2 queda «produccion» y la v1, «anterior»).

### 5.7 Fusionar el PR

Abre el PR (pestaña **Pull requests**), revisa **Files changed** y pulsa **Merge pull request** › **Confirm merge**.

**Qué cambia al fusionar.** `referencia.json` pasa de `retencion-api:v1-35a94deb4e04ab4a` a `retencion-api:v2-3521a0421905ba28` (fuente `completo`, AUC 0,7956) y el historial recoge las dos versiones. Hasta fusionar, la v2 **existe en GHCR pero no está en producción**: la ficha sigue diciendo v1. En este ensayo el PR va contra la rama de ensayo (`lab/nueva-version/completo`), no contra `develop`.

Un PR creado con el `GITHUB_TOKEN` **no lanza otros workflows** (regla de GitHub): el CI no se ejecuta solo sobre él.

---

## 6. Rollback (`rollback.yml`)

El rollback **no reentrena ni reconstruye**: busca en el historial de git la ficha de la versión pedida (por defecto, la anterior a la actual), comprueba que su imagen existe en GHCR y abre un PR que la restaura. **No borra nada** en GHCR.

Se lanza con un push a `lab/rollback/<nombre>` **desde una rama que ya tenga la v2 fusionada**; con **«sin-comprobar»** en el nombre no se comprueba que la imagen exista.

```bash
git fetch origin
git switch lab/nueva-version/completo
git pull
git switch -c lab/rollback/v1
git push -u origin lab/rollback/v1
```

![Rollback parado](img/gh-05-rollback-parado.webp)

**Qué debes ver (primer intento).** Run nº 45041023548 **en rojo** en **10 s**: «La imagen no está en GHCR: No se encuentra ghcr.io/helicr/retencion-api:v1-35a94deb4e04ab4a…». **Es a propósito:** la v1 se entrenó en local y **nunca se publicó**.

Segundo intento, sin comprobar la imagen:

```bash
git switch -c lab/rollback/v1-sin-comprobar
git push -u origin lab/rollback/v1-sin-comprobar
```

![Rollback con PR](img/gh-06-rollback-pr.webp)

**Qué debes ver.** Run nº 45041634741 **en verde** en **16 s**, con el resumen «Rollback · de v2 a v1» y el enlace al **PR nº 3**.

| El PR nº 3 | Archivos cambiados |
|---|---|
| ![PR del rollback](img/gh-07-pr-rollback.webp) | ![Cambios del PR del rollback](img/gh-08-pr-rollback-cambios.webp) |

El PR nº 3 **«Rollback del modelo: v2 a v1»** restaura `referencia.json` del commit anterior y, en el historial, pone la v1 en **«produccion»** y la v2 en **«retirada»**. Al fusionarlo, el siguiente lote vuelve a usar la imagen de la v1. Volver a avanzar es lanzar «Nueva versión del modelo» otra vez. Alternativa sin este workflow: el botón **Revert** del PR de referencia que se fusionó.

**Si falla.** El run no arranca: puede haber otro run del grupo `nueva-version-modelo` esperando aprobación (cancélalo o apruébalo). Si el rollback a una versión se para con «La imagen no está en GHCR», esa versión nunca se publicó: es la protección, no un fallo.

---

## 7. Limpieza (opcional)

Las ramas `lab/…` y `referencia/…` se pueden borrar desde GitHub (**Branches**) o con `git push origin --delete <rama>`. Los paquetes (**Packages** › el paquete › **Package settings**) y el *environment* (**Settings › Environments**) también son borrables. Nada de esto toca tu código.

## 8. Autoevaluación

1. ¿Qué modo usarías para la campaña de cada mañana y cuál para una compra que acaba de ocurrir? *Lote y online.*
2. ¿Por qué «bajo demanda» no cambia tras la compra simulada? *Lee las variables ya calculadas de `fs_produccion`, las de ayer.*
3. ¿Qué decide la puerta de calidad? *El AUC de test frente a `referencia.json` y la tolerancia: igual, rechazada o aceptada.*
4. ¿Qué hace el *environment* `produccion`? *Obliga a que un revisor apruebe antes de publicar.*
5. ¿Por qué el primer rollback se para y qué no borra ninguno? *La imagen de la v1 nunca se publicó; ninguno borra imágenes ni el historial.*
6. ¿Dónde ves qué versión está en producción? *En `models/referencia.json` (y su historial) y en la pestaña Versiones del panel.*

## Cifras de cierre

| Cifra | Qué es |
|---|---|
| 0,7471 → 0,7956 | AUC de test de la v1 a la v2 (+0,0485), dentro de la tolerancia de 0,02 |
| 79,9 % → 76,2 % | probabilidad **online** del cliente 12670 tras la compra simulada; lote y bajo demanda siguen en 79,9 % |
| 6 min | trabajo de la v2: 191 s + 138 s + 17 s + 14 s, sin contar la espera de la aprobación |
| 16 s | el rollback a la v1: un PR y ninguna imagen borrada |
