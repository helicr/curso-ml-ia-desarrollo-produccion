# Laboratorios S4 · Hoja de ruta: qué se hace, en qué orden y dónde está cada guía

Esta hoja **no repite** los laboratorios: te dice **qué piezas hay en S4, qué hace cada una, dónde están su guía y sus diapositivas, y qué es obligatorio, opcional o para casa**. Los pasos detallados, con las órdenes y las capturas, están en la guía de cada pieza. Teoría y glosario: [`../teoria/README.md`](../teoria/README.md). Tarea: [`../tarea/README.md`](../tarea/README.md).

> **Estado de validación (de las guías de cada pieza).** Los laboratorios se ensayaron de verdad entre el 22 y el 25/11/2026, en la cuenta del profesor y en la cuenta de Google del curso. Referencias medidas: el lote diario tardó unos **3 min**, «Validar la producción completa» unos **2 min** y la API desplegada en Cloud Run predijo **0,828** para el cliente de ejemplo, igual que en local. **Sin verificar:** clonar en Cloud Shell el *fork* de otra persona, las órdenes de Windows PowerShell y el panel dentro de un Codespace. **Sin dato:** costes de uso, duración total para un grupo y duración de cada pieza en clase.

> **Los laboratorios usan el caso Online Retail II** (el del docente). **Tu tarea usa tu caso propio** (Bank Marketing): lo que haces en clase es el modelo a imitar, no lo que entregas.

## 1. Las piezas de S4

| # | Pieza | Qué hace | Guía | Diapositivas | Dónde se ejecuta |
|---|---|---|---|---|---|
| A | **Clase «De on-premise a la nube»** | El mapa de la nube: AWS, Azure y Google Cloud, los servicios que nos competen y «nuestro Cloud Journey» (qué pieza del curso iría a qué servicio, con qué esfuerzo y con qué cuidado de costes). Nada se ejecuta | [`guia.md`](../clase-onpremise-a-nube/guia.md) | [`index.html`](../clase-onpremise-a-nube/index.html) (29) | Solo se mira y se comenta |
| B | **Laboratorio de producción de punta a punta** | Configurar el repositorio (*environment* `produccion` con revisores y permiso de PR); **lote diario**, **bajo demanda** y **online** del mismo modelo; **versión nueva** con puerta de calidad, aprobación humana, publicación en GHCR y PR de la referencia; **rollback**. **No usa Google Cloud** | [`guia.md`](../laboratorio-produccion-e2e/guia.md) · [`CONFIGURAR-REPOSITORIO.md`](../laboratorio-produccion-e2e/CONFIGURAR-REPOSITORIO.md) · [`CODESPACE.md`](../laboratorio-produccion-e2e/CODESPACE.md) | [`index.html`](../laboratorio-produccion-e2e/index.html) (26) | Tu *fork* y tu Codespace; GitHub Actions |
| C | **Laboratorio Cloud Journey** | La API de retención desde GitHub Actions a **Artifact Registry** y **Cloud Run**, entrando **sin claves (WIF)** y con **una persona que aprueba**; probar la URL pública; ver el modelo en Vertex AI; **borrar todo** | [`guia.md`](../laboratorio-cloud-journey/guia.md) · [`CONFIGURAR-GCP.md`](../laboratorio-cloud-journey/CONFIGURAR-GCP.md) | [`index.html`](../laboratorio-cloud-journey/index.html) (29) | Cloud Shell, tu terminal o Codespace, la web de GitHub y la consola de Google Cloud |
| D | **Prácticas en Google Cloud** (cinco) | **Crea → prueba → borra**: 01 Docker + Artifact Registry + Cloud Run · 02 Kubernetes (GKE Autopilot) · 03 Dataproc/Spark · 04 el modelo en Vertex AI · 05 Gemini explica la predicción | [`README.md`](../practicas-gcp/README.md) y el de cada carpeta | [`index.html`](../practicas-gcp/index.html) | Cloud Shell |
| E | **Extra: un LLM y el estilo de color** | Un LLM de visión intenta leer el estilo de color de una foto y una regresión barata le gana; orquestado en Actions. **No entra en la tarea ni en la rúbrica** | [`README.md`](../extra-estilo-llm/README.md) · [`guia-pipeline.md`](../extra-estilo-llm/guia-pipeline.md) | [`index.html`](../extra-estilo-llm/index.html) | Codespace y Actions |

Scripts de las piezas C y D: [`preparar-gcp-s4.sh`](../laboratorio-cloud-journey/preparar-gcp-s4.sh) y [`borrar-gcp-s4.sh`](../laboratorio-cloud-journey/borrar-gcp-s4.sh) (C); `crear.sh`, `probar.sh` y `borrar.sh` en cada carpeta de D, y [`borrar-todo.sh`](../practicas-gcp/borrar-todo.sh) para limpiarlo todo.

## 2. Qué es obligatorio, qué opcional y qué puede quedar para casa

Esta clasificación es una **propuesta** (el profesor la confirma; ver «Decisiones del profesor»).

| Pieza | Propuesta | Por qué |
|---|---|---|
| **B · producción de punta a punta** | **Obligatoria** (al menos configurar el repositorio, el lote y la versión nueva con aprobación) | Es la que enseña workflows, jobs, artefactos, `needs`, `concurrency`, permisos y aprobación, **sin riesgo de coste**. Es la base de la tarea |
| **A · clase de la nube** | **Obligatoria, como lectura o versión corta** | Pone el contexto de por qué y a dónde se va; no hay nada que ejecutar |
| **C · Cloud Journey** | **Obligatoria como recorrido**; la ejecución por cada persona depende de tener cuenta de Google con Google Cloud y facturación activos | Es la pieza de WIF y de CD con aprobación. Quien no pueda, sigue la demostración del profesor y **lo declara** (no resta; fingirlo, sí) |
| **D · prácticas de GCP** | **Opcional / para casa**, salvo la 04 que ya se ve dentro de C (paso 9) | Cada una crea recursos que cuestan si se olvidan |
| **E · extra del LLM** | **Opcional / para casa** | No entra en la tarea ni en la rúbrica |

Reglas que valen para todo lo de Google Cloud:
- **Una cuenta y un proyecto tuyos.** Nunca los de otra persona.
- **Crea → prueba → borra** el mismo día. Lo que más cobra si se olvida (por tiempo): el endpoint de Vertex AI (04) y el clúster de GKE (02).
- Un presupuesto con alertas **avisa, no corta** el gasto.
- Sin precios aquí: consulta la página oficial el día que lo hagas.
- El crédito de la prueba gratuita **no cubre Vertex AI ni Gemini** en cuentas dadas de alta desde el 16/11/2026: las prácticas 04 y 05 pueden **no ser posibles** con crédito en tu cuenta (es normal; decláralo si te pasa).
- Gemini **no está en la región de Santiago**: la práctica 05 usa la ubicación `global`.

## 3. Aviso: las piezas de Google Cloud no caben juntas en una sesión de 4 horas

La sesión de S4 dura **4 horas** (10:00–14:00, hora de Perú). Las tres piezas de Google Cloud —**A** (clase de la nube), **C** (Cloud Journey) y **D** (las cinco prácticas)— **juntas superan una sesión de 4 h**, y todavía falta la pieza **B**, la tarea y el cierre con el borrado. **No hay duraciones medidas en clase** para cada pieza (es **sin dato**), así que esta hoja no las inventa.

**Recorte propuesto (decisión del profesor, no una imposición):**
1. **B completa** en clase (es la base de la tarea y no cuesta dinero).
2. **A como lectura previa o versión corta** (unas pocas diapositivas clave).
3. **C completa pero dirigida por el profesor**: él ejecuta el script y el despliegue con aprobación; las personas con cuenta lista lo repiten a la vez, y el resto observa y sigue la guía. **Siempre se acaba con el paso 10, borrar todo.**
4. **D: solo la 04** (ya incluida en C, paso 9) en clase; **01, 02, 03 y 05 para casa** o como demostración del profesor.
5. **E, para casa.**

Alternativa si el grupo no tiene cuentas de Google Cloud listas: B completa + A + **C solo como demostración** + tarea con más tiempo.

## 4. Propuesta de reparto (sin duraciones)

Propuesta de **orden**; el minuto a minuto, también propuesto, está en [`../guion.md`](../guion.md).

1. **Entrada.** Repaso del avance 3 (rojo → verde) y del plan del día.
2. **Teoría breve** de Actions: [`../teoria/README.md`](../teoria/README.md), apartados 2 a 8, con los YAML reales abiertos.
3. **Pieza A**, en su versión corta.
4. **Pieza B, parte 1 (configurar el repositorio).** Primero, porque C y la tarea dependen de que el *environment* `produccion` exista con revisores.
5. **Pieza B, parte 2:** lote (`puntuar-lote.yml`), validación (`validar-produccion.yml`) y **versión nueva** con los tres escenarios: igual, rechazada y aceptada (esperando aprobación). El rollback, si hay margen.
6. **Pausa.**
7. **WIF**: teoría ([`../teoria/README.md`](../teoria/README.md), apartado 5) y qué hace `preparar-gcp-s4.sh`.
8. **Pieza C** (Cloud Journey), dirigida, **terminando en el borrado**.
9. **Pieza D (04)** si ya se vio dentro de C; el resto, para casa.
10. **Tarea** y cierre.

## 5. Qué debe quedarte de cada pieza (comprobaciones rápidas)

- **B.** Sabes decir por qué «Run workflow» no sale y cómo se lanza un ensayo por nombre de rama; has visto un run **esperando aprobación** y sabes qué pasa si el *environment* no existe; sabes qué decidió la puerta de calidad en cada escenario.
- **C.** Puedes explicar con tus palabras por qué no hay claves (WIF, apartado 5 de la teoría); has visto que se **aprueba** antes de publicar; la API respondió en su URL pública con **0,828** para el cliente de ejemplo; **lo borraste todo**.
- **D.** Si hiciste alguna, la ejecutaste de principio a fin: crear, probar **y borrar**. `./borrar-todo.sh` deja vacíos los listados.
- **Todas.** Cada vez que algo falló, lo anotaste con el **error exacto**: es material directo para tu tarea (la sección «Fallos encontrados»).

## 6. Cómo se conecta con tu tarea

Lo que ves en B y C es **el modelo a imitar** con tu caso: un workflow con trabajos encadenados que prepara datos, entrena, calcula métricas y deja un artefacto; con permisos mínimos, sin secretos y, si quieres, con una aprobación. Mira especialmente [`nueva-version.yml`](../laboratorio-produccion-e2e/nueva-version.yml) (trabajos encadenados, artefactos, puerta de calidad, `environment`) y [`puntuar-lote.yml`](../laboratorio-produccion-e2e/puntuar-lote.yml) (preparar datos y dejar artefactos). Google Cloud en la tarea es **opcional**.

## 7. Decisiones del profesor (abiertas)
1. **Clasificación** de obligatorio / opcional / casa (apartado 2).
2. **Recorte** de las piezas de Google Cloud (apartado 3) y cuáles de las prácticas D se hacen en clase.
3. **Orden B → C** (B primero porque configura el repositorio) frente a empezar por A.
4. **Quién ejecuta C**: demostración del profesor con repetición opcional, o todas las personas a la vez.
5. **Qué hacer** si alguien no puede activar Google Cloud o facturación: la propuesta es seguir C como demostración y declararlo.
