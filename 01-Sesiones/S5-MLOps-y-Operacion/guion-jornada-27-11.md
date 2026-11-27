# Guion de la jornada · viernes 27/11/2026 · «el maratón»

Cierre de S4 + recap de S4 + S5. **El tiempo no es la restricción hoy**: aquí no recorto nada; solo marco los **puntos de pausa** naturales y qué se enseña con runs de referencia si algo tarda. Todo el minutado es orientativo y **no está medido en clase** (lo medido son los tiempos de Actions que se citan).

Orden de la jornada:

| Parte | Qué | Dónde está el material |
|---|---|---|
| **0** | Arranque y **replicar los repositorios** (fork, `develop`, Actions, *environment*) | [`laboratorio-produccion-e2e/CONFIGURAR-REPOSITORIO.md`](../S4-Orquestacion-y-CI-CD/laboratorio-produccion-e2e/CONFIGURAR-REPOSITORIO.md) · [`checklist.md`](checklist.md) |
| **1A** | **Laboratorio de los Dockerfiles** (lo que modificamos) | [guía de Docker y kind](../../03-Entorno/guia-docker-kubernetes-gke/index.html) · [`04-Proyecto-Base/docs/api-y-contenedor.md`](../../04-Proyecto-Base/docs/api-y-contenedor.md) |
| **1B** | **Lo que quedó a medias de GitHub Actions** (producción e2e) | [`laboratorio-produccion-e2e/guia.md`](../S4-Orquestacion-y-CI-CD/laboratorio-produccion-e2e/guia.md) |
| **2** | **Recap de S4** | [`recap-final`](../recap/recap-final/index.html), pestaña **S4** |
| **3** | **S5**: teoría corta → laboratorio A (MLOps clásico) → laboratorio B (agentes) → tarea y cierre | [`teoria/`](teoria/README.md) · [`laboratorio-mlops/`](laboratorio-mlops/index.html) · [`laboratorio-agentes/`](laboratorio-agentes/index.html) |
| **4** | (Aparte) **Sesión de cierre**: fundamentos de IA y agentes + recap final | [`clase-fundamentos-ia-agentes/`](clase-fundamentos-ia-agentes/index.html) · [`recap-final`](../recap/recap-final/index.html) |

**Hoy a las 10:00 vence el avance 4** (fecha del calendario del repositorio): pregunta al empezar quién lo tiene entregado y por qué canal.

## Antes de empezar (esta mañana, 30 minutos)

- [ ] **Tu Codespace/entorno** al día: `git pull origin develop` (debes estar en `f7bb7a0` o posterior) y `bash .devcontainer/verificar.sh` (cinco `[OK   ]` y «Fallos: 0»).
- [ ] **Modelo y datos de la muestra:** `cd 04-Proyecto-Base`, `python -m ia_mlops.operacional`, `python -m ia_mlops.pipeline` (unos 30 s) y `ls models/modelo_mlflow models/metadatos.json`.
- [ ] **El laboratorio A necesita los datos completos para la «v2 de verdad»:** `python -m ia_mlops.dataset descargar` y `python -m ia_mlops.pipeline --fuente completo` tardó **437 s** en el ensayo (≈7 min). Déjalo para **después** de L1 y L2 (esos usan la muestra) o lánzalo en una segunda terminal mientras hablas. **Cuidado:** tras `--fuente completo`, volver a `--fuente muestra` falla con R03 si no borras antes `data/processed/curso.db` (guía del laboratorio, apartado 4.6).
- [ ] **El registro de MLflow sin alias `champion`** (es el estado de partida del laboratorio A): comprueba con `python -m ia_mlops.alias_modelo mostrar` («Alias: ninguno»).
- [ ] **Ollama con el Qwen 3B** servido (`ollama list`) si vas a mostrar L2 del laboratorio de agentes; si no, sigues con el LLM falso.
- [ ] **Docker en tu Codespace** (`docker version`) y, para el laboratorio de Docker, `kind` y `kubectl` (`bash .devcontainer/verificar.sh` lo comprueba).
- [ ] **Tu fork** con Actions habilitado, el *environment* `produccion` con revisores y «Allow GitHub Actions to create and approve pull requests» (ver la parte 0).
- [ ] **Limpieza de ramas de ensayo:** el remoto ya no tiene las `lab/*` viejas (borradas hoy); los nombres de rama de las guías vuelven a estar libres.

## Parte 0 · Arranque y replicar los repositorios

**Objetivo:** que **cada persona** tenga su propio repositorio listo para trabajar: un *fork* con la rama `develop`, Actions habilitado y el *environment* `produccion`.

1. **Di:** «Trabajáis en vuestro *fork*, no en el mío. Todo lo que lancemos hoy corre en vuestro GitHub, con vuestros minutos de Actions».
2. **Haz** (quien no tenga fork): en `https://github.com/helicr/curso-ml-ia-desarrollo-produccion` → **Fork** → **desmarca «Copy the main branch only»** (si no, no trae `develop`) → **Create fork**.
3. **Haz** (quien ya tiene fork, para ponerlo al día): botón **Sync fork** en su página de GitHub, rama `develop`; o en la terminal `git remote add upstream https://github.com/helicr/curso-ml-ia-desarrollo-produccion.git`, `git fetch upstream` y `git switch develop && git merge --ff-only upstream/develop`.
4. **Haz:** abrir un Codespace del fork (rama `develop`) o clonar: `git clone https://github.com/<usuario>/curso-ml-ia-desarrollo-produccion.git` y `git switch develop`.
5. **Haz** (configurar el repositorio, **una vez**): **Settings › Actions › General** → permitir acciones y, en **Workflow permissions**, marcar **Allow GitHub Actions to create and approve pull requests**; **Settings › Environments › New environment** → `produccion` (sin tilde) → **Required reviewers** (tú mismo) → **Save protection rules**. Capturas en [`CONFIGURAR-REPOSITORIO.md`](../S4-Orquestacion-y-CI-CD/laboratorio-produccion-e2e/CONFIGURAR-REPOSITORIO.md).
6. **Debes ver:** en **Settings › Environments**, `produccion` con «1 protection rule»; en la pestaña **Actions**, los workflows listados.
7. **Si falla:** el fork no trae `develop` → rehacerlo con la casilla desmarcada; Actions desactivado en el fork → aceptar el aviso de la pestaña **Actions**; `git push` da 403 → otra cuenta en el gestor de credenciales (`git-credential-manager github login --username <usuario> --device`).

**Punto de control:** pasa lista: ¿todos con fork, `develop` y `produccion`? No sigas hasta que lo estén.

## Parte 1A · Laboratorio de los Dockerfiles (lo que modificamos)

**Lo que cambió** (cuéntalo con un dibujo en la pizarra): antes la imagen **copiaba tu carpeta**; ahora, por defecto, **clona el repositorio en el commit exacto** (`FUENTE=git`, `REF=${GITHUB_SHA}` en Actions) dentro de una etapa que se **descarta** (no queda `git` ni el clon en la imagen final). El **modelo** entra **aparte** (`--build-context modelo=...`) porque la API **no entrena**: lleva el que validó la puerta de calidad. El token de un fork privado va como **secreto de BuildKit**, nunca como `ARG` ni `ENV`. En desarrollo (Codespace/compose) se usa `FUENTE=contexto`.

**Ya está ensayado:** el workflow **«Validar API e interfaz en dos contenedores»** pasó en verde sobre `f7bb7a0` (27/11/2026, run 46003093657) con las imágenes **construidas por clon del commit**, el secreto de BuildKit y los dos compose con `FUENTE=git`. **Sin ensayar todavía:** el resto de workflows que cambiaron la línea del build (`puntuar-lote`, `nueva-version`, `desplegar-gcp`, los del agente y `ci.yml`).

### 1A.1 · La imagen en tu Codespace (modo desarrollo)
- **Di:** «Una imagen es una receta congelada: código + dependencias + modelo. Aquí construimos desde nuestra carpeta; en Actions se construirá desde el commit».
- **Haz** (guía de Docker y kind, secuencia completa; desde `04-Proyecto-Base`):
  ```
  docker build -f deploy/docker/Dockerfile --build-arg FUENTE=contexto --build-context modelo=models -t retencion-api:local .
  docker image ls retencion-api
  ```
- **Debes ver:** la imagen `retencion-api:local` en la lista. El punto final es el **contexto**: sin él, `docker buildx build requires 1 argument`.
- **Si falla:** sin `models/` no hay contexto `modelo` → `python -m ia_mlops.pipeline`. (El texto exacto de ese error con el Dockerfile nuevo está **sin verificar**: anótalo si lo ves.)

### 1A.2 · Mirar dentro de la imagen (a los alumnos les gusta)
- **Haz:** `docker run --rm -it retencion-api:local bash` y dentro `pwd`, `ls -la`, `ls models`, `cat models/metadatos.json`, `id` (uid=10001, **no root**), `pip list | grep -i -E "fastapi|uvicorn|scikit-learn|pandas|mlflow"`, `exit`. Desde fuera: `docker history retencion-api:local` y `docker image inspect retencion-api:local --format '{{.Config.User}} · {{.Config.ExposedPorts}} · {{.Config.Cmd}} · {{.Size}}'`.
- **Pregunta al aula:** «¿hay `git` dentro?» (no: la etapa que clona se descarta) y «¿de dónde salió el modelo?» (del contexto `modelo`).

### 1A.3 · Lo mismo en Actions, con el commit exacto
- **Haz:** el workflow vive en `develop` (no en `main`, que es la rama por defecto de un *fork*), así que **el botón «Run workflow» no aparece**. Se dispara con un `push` a `develop` que toque `04-Proyecto-Base/deploy/docker/**` o el propio workflow. En tu fork, desde la raíz del repositorio: `echo "# ensayo" >> .github/workflows/validar-dos-contenedores.yml`, `git add .github/workflows/validar-dos-contenedores.yml`, `git commit -m "Ensayo: validar API e interfaz en dos contenedores"` y `git push origin develop`. Mientras corre, abre el YAML: señala `--build-arg REF="${GITHUB_SHA}"`, `--build-context modelo=models`, `--secret id=git_token,env=GIT_TOKEN` y, en el paso de compose, `FUENTE: git`.
- **Debes ver:** todos los pasos en verde (en el repositorio del profesor lo fue en `f7bb7a0`). El *Job Summary* resume lo comprobado.
- **Di (la lección):** «La imagen que se prueba es **el commit**, no “lo que tengo en mi carpeta”: reproducible y auditable».
- **Si falla:** lee el paso que falló; sospecha primero de la **red** (el clon) o de que `models/` no se generó en el job. Anótalo en el registro de incidencias.

## Parte 1B · Lo que quedó a medias de GitHub Actions (producción e2e)

> Marca con una ✓ lo que **ya** hicisteis el miércoles y haz solo lo que falte; el orden es el de la guía [`laboratorio-produccion-e2e/guia.md`](../S4-Orquestacion-y-CI-CD/laboratorio-produccion-e2e/guia.md).

- [ ] **Preparar la rama y los cuatro workflows** (apartado 1): `git switch -c lab/produccion-e2e`, copiar `puntuar-lote`, `validar-produccion`, `nueva-version` y `rollback` a `.github/workflows/`, commit.
- [ ] **Modo 1 · lote** (apartado 3): `git push -u origin lab/produccion-e2e` → run «Puntuar por lotes» en verde en **unos 3 min** y su *Job Summary*. **Di:** «el lote puntúa a todos y deja una lista priorizada».
- [ ] **Modos 2 y 3 y el panel en el Codespace** (apartado 4): `docker compose -f deploy/docker/compose-produccion.yaml up --build -d` (en desarrollo usa `FUENTE=contexto`), `curl` a `/bajo-demanda/$ID` y `/online/$ID`, compra simulada, y de nuevo las dos lecturas. **Debes ver:** el modo online cambia con la compra; el de bajo demanda, no.
- [ ] **Versión nueva con puerta y aprobación** (apartado 5): ramas `lab/nueva-version/muestra` («igual»: no publica), `…/completo-rechazo` (la puerta falla) y **`…/completo` el último** (queda en **Waiting**, tú aprobas con **Review deployments › Approve and deploy**, se publica y se abre el PR). Fusiona el PR (5.7).
- [ ] **Rollback** (apartado 6): `lab/rollback/v1` (y la variante `…/v1-sin-comprobar`). **Debes ver:** el workflow restaura la versión anterior.
- **Tiempos medidos (22/11):** lote ≈ 3 min; «validar la producción completa» ≈ 2 min. Los de «versión nueva» y rollback, **sin medir aquí**: míralos en tus runs.
- **Trampas conocidas:** *non-fast-forward* (la rama ya existe: hoy están borradas las `lab/*` viejas del remoto, pero **en tu fork** puede haberlas); el *environment* se llama `produccion` sin tilde; «Run workflow» no sale en los workflows que viven solo en ramas `lab/…` (por eso se ensayan **por rama**).

**Punto de control:** ¿todos han visto un run en verde, uno rojo por la puerta y uno esperando aprobación?

## Pausa larga (30–45 min)

Pide que, en la pausa, cada persona deje lista la rama `lab/agente-s5` del laboratorio de agentes (apartado 7.1 de su guía: copia los workflows, **no lanza nada**).

## Parte 2 · Recap de S4 (con el recap final, pestaña S4)

Mensajes, en este orden (3–4 diapositivas del recap; el resto, tú):
1. **Qué hicimos:** orquestar el pipeline con Actions; de «lo corro yo» a «lo corre un workflow» con **puerta de calidad** y **aprobación humana**.
2. **Qué te llevas:** leer un workflow (`on`, `jobs`, `environment`, `concurrency`); **identidad sin claves (WIF)**; imagen reproducible por commit (hoy); desplegar en Cloud Run y **borrar lo creado**.
3. **El momento difícil:** el *environment* mal nombrado y las ramas que ya existen. Es normal.
4. **Tarea (avance 4):** vence **hoy a las 10:00**; qué se entrega y cómo (ver [`tarea/README.md`](../S4-Orquestacion-y-CI-CD/tarea/README.md)). Lo no confirmado (canal Classroom/formulario, pesos) lo decides tú.
5. **Puente a S5:** «ya sabéis desplegar; hoy aprendemos a **operar**: qué hay en producción, si sigue funcionando, cómo lo cambio y cómo lo deshago».

## Parte 3 · S5: por dónde empezar

**Empieza por la teoría corta y luego el laboratorio A (MLOps clásico); los agentes van después.** Motivo: el laboratorio A enseña **alias, rollback y alertas**, que el laboratorio B reutiliza (versionar y volver atrás un agente); y la teoría de S5 gira en torno a **cinco preguntas** que sirven para los dos. Los extras (MCP en notebooks, interfaz web, Composer, Vertex) **no se hacen hoy**: se mencionan como «para casa».

### 3.0 · Teoría corta (≈ 20 min)
- **Las cinco preguntas** (mensajes del [`guion.md`](guion.md) de S5): qué está sirviendo, con qué se hizo, si sigue funcionando, cómo lo cambio y cómo lo deshago.
- **Huella → ficha → imagen:** abre `04-Proyecto-Base/models/referencia.json` y `historial_versiones.json`.
- **Servicio sano ≠ modelo bueno.** **La deriva de datos avisa; la de rendimiento confirma, tarde** (la etiqueta del caso llega 90 días después). **PSI 0,10/0,25 = convención, no ley.**
- Teoría completa: [`teoria/README.md`](teoria/README.md).

### 3.1 · Laboratorio A · MLOps clásico ([guía](laboratorio-mlops/guia.md), 27 diapositivas)
Orden de la guía y qué debes ver (todas las salidas reales están en las diapositivas):
1. **L1 · Deriva de datos** (apartado 2): `python -m ia_mlops.deriva cortes` y `datos --referencia R --actual A`. **Debes ver:** PSI y KS por variable; el umbral 0,25. **Di:** el PSI es una convención; una cifra sin umbral no es una alerta.
2. **L2 · Deriva de rendimiento** (apartado 3): `deriva rendimiento --cortes …`. **Lección:** medir con datos de entrenamiento **engaña** (el AUC se sobreestima).
3. **L3 · Alias y rollback** (apartado 4): `alias_modelo mostrar`, `promover --version N`, `volver`. La **v2 «de verdad»** necesita los datos completos (≈ 437 s: lánzalo en segundo plano). **Di (honesto):** el alias gobierna el **registro**, no cambia solo la API ya desplegada.
4. **L4 · Alertas con Actions** (apartado 5): copia `monitoreo.yml`; ramas `lab/monitoreo/estable` (verde, «Sin alerta») y `lab/monitoreo/deriva` (el trabajo 3 en **rojo** y un *issue* `alerta-deriva`). **Repite el run:** debe **comentar** en el *issue*, no abrir otro. **Cierra el *issue*** al acabar.
5. **L5 · Costes y orden** (apartado 6): solo se explica; sin cifras de precio.
- **Si falla:** casos en el apartado 7 de la guía. **Al terminar, limpia** (5.7) y vuelve a la muestra (4.6) si alguien quiere repetir.

### Pausa (15–30 min)

### 3.2 · Laboratorio B · Agentes ([guía](laboratorio-agentes/guia.md), 30 diapositivas)
Seguimos el orden de [`guion.md`](guion.md) de S5 (bloques 3 a 8), con estos lanzamientos de workflows (ver «Orden de lanzamiento» en ese guion):
- **L1 MCP:** `python mi_cliente_mcp.py` (guía, 2.1): una herramienta es una función con contrato; la **descripción** es lo que el LLM lee.
- **L2 LLM local:** tu Ollama ya servido (`ollama list`); la descarga de 2,1 GB **no** en directo. Usa el nombre `hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF:Q4_K_M`.
- **L3 Agente en 100 líneas:** `agente_falso.py` y la traza en MLflow. **Al empezar, lanza «CI»** (`lab/agente/ci`, ≈ 4 min).
- **L4 Skills:** `skills.activadas(...)`; una coma cambia la huella.
- **L5 E2E y evaluación:** 25 preguntas de oro; `evaluar --llm falso` (100 %); lanza «igual» (`lab/agente-version/igual`, 1 min 16 s, sin LLM). El **evaluador también se prueba**.
- **L6 Desplegar en GitHub:** «prompt-nuevo» **el último** (espera aprobación y bloquea a los siguientes del grupo), **Review deployments**, fusionar el PR, **rollback**. «Rechazo» (≈ 13 min 37 s en rojo): enseña el **run de referencia** (nº 45067472249), no lo lances por alumno.
- **Mensaje:** un agente es software más: se prueba, se evalúa, se versiona, se aprueba y se puede deshacer; el **modelo de ML decide**, el LLM solo orquesta y redacta.
- **Extras** (para casa, un minuto de menciones): dos MCP en notebooks con interfaz web, lote con Airflow/Composer y del champion a Vertex.

### 3.3 · Tarea (avance 5) y cierre
- **Qué se entrega:** repositorio, informe y demostración; entrega final **viernes 11/12 a las 10:00 (hora de Perú)** (la hora está **por confirmar**; lo anunció el asistente, no tú). Plantilla: [`evidencias/plantilla-avance-5.md`](evidencias/plantilla-avance-5.md); rúbrica: [`tarea/rubrica.md`](tarea/rubrica.md) (**pesos por decidir**).
- **Decide antes y dilo:** cómo y dónde es la **demostración** (vídeo o en vivo) y el **canal** (Classroom o formulario).
- **Costes y limpieza:** borrar lo creado, parar el Codespace, revisar la factura de Google Cloud (debe marcar 0 €).
- **Honestidad:** declarar lo no hecho no resta; fingirlo, sí.

## Parte 4 · Sesión de cierre (aparte)
Cuando decidas la fecha: [`clase-fundamentos-ia-agentes/`](clase-fundamentos-ia-agentes/index.html) (41 diapositivas, a tu ritmo) y el [`recap final`](../recap/recap-final/index.html) (48 diapositivas) con el mensaje **«Sube tu tarea al Classroom»** y el repositorio que se llevan.

## Si algo falla (resumen; el detalle está en el [guion de S5](guion.md))
| Síntoma | Respuesta |
|---|---|
| Un run espera «Pending» | Un `agente-version` espera aprobación y bloquea al siguiente: apruébalo o cancélalo |
| No pide aprobación | El *environment* no se llama `produccion` o no tiene revisores |
| No abre el PR | Falta «Allow GitHub Actions to create and approve pull requests» |
| No aparece ejecución en un fork | Actions desactivado o la rama no coincide con el disparador |
| `git push` rechazado (*non-fast-forward*) | La rama ya existe: sufijo nuevo o bórrala |
| `0xc06d007f` al importar scikit-learn (Windows con conda) | `conda activate` el entorno, no llamar a `python.exe` a pelo |
| El laboratorio A tarda (v2 con datos completos) | Muestra las salidas de las diapositivas y sigue; lánzalo en segundo plano |
| Preguntan por precios o créditos de GCP | «Sin verificar; consulta la página oficial y anota lo que veas con la fecha» |

## Registro de incidencias (rellénalo en directo)
Paso · esperado · obtenido · mensaje · acción. Sin credenciales ni identificadores. Presta atención a: Actions en los forks, ejecuciones en cola, el *environment* sin revisores, el Codespace y lo **primero que ejecutes con los Dockerfiles nuevos fuera de `validar-dos-contenedores`**.
