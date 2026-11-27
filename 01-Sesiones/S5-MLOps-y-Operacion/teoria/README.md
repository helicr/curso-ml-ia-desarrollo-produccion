# S5 · Teoría: operar lo que ya está en producción

Material de lectura para la última sesión. Acompaña a la [guía de laboratorios](../practica/guia-laboratorio.md) y a los laboratorios: el de agentes ([`laboratorio-agentes/guia.md`](../laboratorio-agentes/guia.md)) y el de MLOps clásico (`laboratorio-mlops/`: ver su guía cuando esté publicada).

> **Cómo leerlo.** Los ejemplos son del caso Retail (retención a 90 días, Online Retail II, `04-Proyecto-Base`) porque ahí hay algo que ya está en producción desde S4. Cada afirmación factual lleva la ruta donde se comprueba; si no la hay, dice **sin dato** o **convención** (una costumbre del oficio, no una ley). Tu caso propio (Bank Marketing) usa las mismas ideas; la [tarea](../tarea/README.md) te pide aplicarlas.

> **Estado.** Lo de GitHub Actions y los agentes se ejecutó de verdad (runs del 22 y 23/11/2026, cuenta del profesor). Lo de Google Cloud se explica de palabra o con lo practicado en S4; aquí no se da ninguna cifra de precios, cuotas ni créditos (**sin verificar**: consulta la página oficial).

## 0. La idea en una frase

Poner un modelo en producción no es el final: es el principio de un trabajo distinto. Hay que poder responder, en cualquier momento, cinco preguntas: **¿qué está sirviendo? ¿con qué datos y qué código se hizo? ¿sigue funcionando bien? ¿cómo lo cambio con seguridad? ¿cómo lo deshago?** Esta sesión es el mapa de esas respuestas.

| Pregunta | Dónde se contesta | Apartado |
|---|---|---|
| ¿Qué está sirviendo? | La ficha `models/referencia.json` y la imagen con su etiqueta | 1 |
| ¿Está sano el servicio, y es bueno el modelo? | Métricas del servicio **y** métricas de calidad: no son lo mismo | 2 |
| ¿Han cambiado los datos o el rendimiento? | Deriva | 3 |
| ¿Qué pasó y quién tiene que enterarse? | Registros y alertas | 4 |
| ¿Es seguro y se puede mantener? | Seguridad y mantenimiento | 5 |
| ¿Cómo lo cambio y lo deshago? | Puerta de calidad, aprobación, alias y rollback | 6 |
| ¿Cuánto cuesta y cómo evito sorpresas? | Costes | 7 |
| ¿Y si lo que sirvo es un agente? | Lo mismo: es software | 8 |

---

## 1. Qué se versiona y cómo se enlaza

«Versionar» es poder decir **cuál era exactamente** cada pieza cuando pasó algo. En el caso hay cinco piezas, y ninguna basta sola:

| Pieza | Cómo se identifica | Dónde se comprueba |
|---|---|---|
| **Datos** | Una **huella** (`huella_datos`): resumen corto del contenido; los mismos datos dan la misma huella | `04-Proyecto-Base/models/metadatos.json` y parámetro en MLflow ([`de-notebook-a-python.md`](../../../04-Proyecto-Base/docs/de-notebook-a-python.md), apartado «Qué datos usó cada modelo») |
| **Variables** | El catálogo de FS (qué es cada variable, su fórmula y por qué se conoce antes de llamar) y el SQL de la capa FS en git | Capa FS del proyecto (`sql/`); el catálogo es una tabla (`fs_catalogo`) |
| **Modelo** | Una **versión** (`version`) del modelo con su métrica de test; opcionalmente un **alias** en el registro de MLflow | [`models/referencia.json`](../../../04-Proyecto-Base/models/referencia.json) y [`models/historial_versiones.json`](../../../04-Proyecto-Base/models/historial_versiones.json) |
| **Código** | El *commit* de git | El repositorio |
| **Imagen** | La etiqueta `retencion-api:v<N>-<huella>` en GHCR | El campo `etiqueta_imagen` de la ficha |

**Cómo se enlazan.** La **ficha** `referencia.json` es el eslabón: dice la versión (`version`: 1), la huella de los datos (`35a94deb4e04ab4a`), la etiqueta de la imagen (`retencion-api:v1-35a94deb4e04ab4a`), el tipo de modelo, las métricas de valid y de test y cuándo se entrenó y se aprobó. La **etiqueta de la imagen lleva la huella**: de la imagen se llega a los datos, y de la ficha, a la imagen. El **historial** (`historial_versiones.json`) guarda todas las versiones con su `estado` (hoy solo hay una: `produccion`).

**«En producción» no es «está en GHCR».** En el laboratorio de S4, el modelo en producción es *la imagen* **más** la ficha **más** el historial, y una versión pasa a serlo cuando **se fusiona el PR** que los actualiza ([guía de S4](../../S4-Orquestacion-y-CI-CD/laboratorio-produccion-e2e/guia.md), apartado 0). Una imagen publicada y sin fusionar es una candidata, no la de producción.

**Ejemplo para romperte la cabeza.** Dos entrenamientos con los mismos datos y el mismo código dan la misma huella y las mismas métricas «hasta el último decimal» (comprobado con la muestra del proyecto, [`de-notebook-a-python.md`](../../../04-Proyecto-Base/docs/de-notebook-a-python.md)). Si la huella cambia, **han cambiado los datos**: comparar dos ejecuciones con huellas distintas sin decirlo es un error de método (lo penaliza la [rúbrica de avances](../../../02-Proyecto-Transversal/alumno/rubrica-avance.md)).

**Qué no se versiona en git.** Los datos grandes y los pesos de un LLM no van en git; se identifican por huella y se guardan donde ya estaban (la caché de Ollama no se sube: [guía de agentes](../laboratorio-agentes/guia.md), apartado «Qué va en MLflow y qué va fuera»).

> Para pensar: tu repositorio, ¿puede contestar «con qué datos y qué código se entrenó el modelo que sirve hoy» en menos de un minuto?

---

## 2. Métricas del servicio frente a calidad del modelo

Son dos preguntas distintas y **una no contesta a la otra**.

| | Métricas del **servicio** | Métricas de **calidad del modelo** |
|---|---|---|
| Pregunta | ¿La API responde, rápido y sin errores? | ¿Las respuestas son buenas? |
| Ejemplos | **Latencia** (mediana, p95), **tasa de errores**, **disponibilidad** (¿responde `/listo`?) | **AUC** y precisión media del modelo (0,747 de AUC de test en la ficha de la versión 1); en el agente, **acierto de herramienta** (80 % en la referencia v1) |
| Cuándo se sabe | En el momento de la petición | A menudo **tarde**: hace falta la etiqueta real (apartado 3) |
| Un fallo se ve como | Un 5xx, un tiempo excesivo, la API caída | Nada: la API devuelve 200 con una probabilidad equivocada |

**La trampa.** Un servicio puede estar perfecto (200 en 20 ms) y servir un modelo que ya no acierta. Y al revés: un modelo excelente detrás de una API que se cae. Por eso la API del curso **distingue** los fallos: 422 (la petición no cumple el contrato), 503 (no hay modelo cargado), 500 (error nuestro). Distinguirlos es lo que permite medir cada cosa por separado (ver la rúbrica de [avances](../../../02-Proyecto-Transversal/alumno/rubrica-avance.md), avance 2).

**En el agente**, el servicio es la latencia (mediana de 19,2 s y p95 de 104,9 s en un portátil de 14 hilos sin GPU, **no en tu máquina**) y la calidad es la evaluación con las 25 preguntas de oro: herramienta, argumentos, «sin inventar» y trampas superadas ([guía de agentes](../laboratorio-agentes/guia.md), apartados 6.3 a 6.5). Los dos grupos se miran juntos y se deciden por separado.

**Un evaluador también se prueba.** En la primera pasada de la evaluación del agente, el «sin inventar» salió en un 64 %; tras corregir la regla del evaluador (contaba fechas y nombres de variable como cifras inventadas) salió 96 %. Si una métrica te sorprende, revisa primero la regla que la mide (apartado 6.6 de la guía).

**Sin dato en este repositorio:** un panel de métricas de servicio en vivo (latencia, errores, disponibilidad) para la API del curso. Lo que sí hay son los códigos distinguibles, `/listo` y los registros. Si en tu caso añades un panel, es una mejora tuya.

---

## 3. Deriva: de datos y de rendimiento

**Deriva** es que el mundo cambia y el modelo no se entera. Hay dos clases, y se miden de forma muy distinta.

### 3.1 Deriva de datos (se ve enseguida)

Compara **lo que entra ahora** con **lo que entró al entrenar**, sin necesitar la respuesta correcta.

Una medida muy usada es el **PSI** (*Population Stability Index*, índice de estabilidad de la población). Se parte la variable en tramos y se compara la proporción de filas de cada tramo entre un periodo de referencia (`p_ref`) y el actual (`p_act`):

```
PSI = suma sobre los tramos de (p_act − p_ref) · ln(p_act / p_ref)
```

- Es 0 si las dos distribuciones coinciden y crece cuanto más se separan.
- **El umbral es una convención.** Es habitual leer «menos de 0,1: estable; de 0,1 a 0,25: vigilar; más de 0,25: cambio importante», pero esos números son una costumbre del oficio, **no una ley** y **sin fuente en este repositorio**: el laboratorio de MLOps usa el suyo (ver su guía) y tú debes poder justificar el tuyo (por ejemplo, ¿con qué umbral te habrías enterado de un cambio que de verdad importó?).
- Cuidado con los tramos vacíos (el logaritmo de 0): hay que decidir qué hacer y dejarlo escrito.
- **Entre qué cortes se compara** es la decisión importante. En Retail, la ficha dice que el test usa los cortes `2011-06-01` y `2011-09-01` (`cortes_test` en [`referencia.json`](../../../04-Proyecto-Base/models/referencia.json)); un corte posterior es «datos de otro periodo».

### 3.2 Deriva de rendimiento (se ve tarde)

Es que el modelo **acierta menos**. Medirla exige la **etiqueta real**, y la etiqueta del caso es «¿compró en los **90 días siguientes**?»: la respuesta correcta de una predicción de hoy **llega dentro de 90 días**. No hay atajo: hasta entonces solo puedes mirar la deriva de datos y las probabilidades que salen (¿se aplanan? ¿se vacía el tramo alto?).

Consecuencias prácticas:
- La deriva de datos es una **alerta temprana**, no una prueba de que el modelo falla (los datos pueden cambiar y el modelo seguir bien, o al revés).
- La deriva de rendimiento es la **confirmación**, con retraso. El diseño del monitoreo debe decir con qué desfase se calcula.
- En tu caso propio hay una versión más cruda de lo mismo: la **evaluación por orden de filas** (las primeras filas para entrenar, las últimas para probar) frente a la partición aleatoria. La diferencia entre las dos es la deriva que la partición aleatoria te escondía: antes de explicarla, mira qué proporción de síes hay en cada tramo ([hoja del caso](../../../02-Proyecto-Transversal/alumno/tu-caso-bank-marketing.md), apartado 8).

### 3.3 Qué se hace al detectarla

Nada automático y a ciegas. Un camino razonable: **investigar** (¿es un error de datos o un cambio real?), **decidir** (¿reentrenar?, ¿esperar?) y, si se reentrena, pasar por la **puerta de calidad** y la **aprobación** (apartado 6). Una alerta de deriva que reentrena y publica sola es una puerta sin cerradura.

---

## 4. Registros y alertas

**Registro** (*log*): lo que el sistema cuenta de sí mismo. **Alerta**: un aviso que le llega a una persona cuando algo cruza un límite.

**Qué se registra.** Un evento por petición, en líneas JSON por la salida estándar (como la API de S2): qué ruta, qué código de respuesta, cuánto tardó, qué versión del modelo y qué huella de datos. Con eso se reconstruye qué pasó sin guardar nada del cliente.

**Qué NUNCA se registra.** Los **datos del cliente**: nombres, correos, teléfonos ni el contenido de la petición completa. En el caso Retail solo existe el número de cliente y su país, y las herramientas del agente no devuelven nombres, correos ni teléfonos ([guía de agentes](../laboratorio-agentes/guia.md), L1). La rúbrica de S2 exige «registro sin datos del cliente». Un registro es una copia de los datos que nadie protege como protege la base: lo que no se escribe no se puede filtrar. Tampoco se registran claves ni tokens.

**Alertas útiles.** Una alerta buena es **accionable** (dice qué mirar), **rara** (si salta cada día se ignora) y **tiene dueño** (alguien sabe que es suyo). Ejemplos del caso: el workflow de monitoreo se pone en rojo si el PSI supera el umbral (laboratorio de MLOps: ver su guía); un `/listo` que deja de responder; la puerta de calidad del agente que **rechaza** una versión (rojo y los trabajos siguientes omitidos: run 45067472249, [guía de agentes](../laboratorio-agentes/guia.md), 7.5).

**En GitHub Actions**, una «alerta» es un workflow que falla o que abre un aviso; el correo o la notificación los gestiona GitHub. Alertas de Google Cloud (Cloud Monitoring): **sin verificar en el curso** (en S4 solo se practicó el presupuesto con alertas).

---

## 5. Seguridad y mantenimiento

Lo que ya está hecho en el caso, para que lo reconozcas:

| Medida | Qué evita | Dónde se ve |
|---|---|---|
| **Sin claves en el repositorio** | Que quien lea el código o el registro de un workflow tenga acceso | Los workflows del agente no usan ningún secreto (LLM local); el resto usa el `GITHUB_TOKEN` de cada ejecución ([`CONFIGURAR-REPOSITORIO.md`](../laboratorio-agentes/CONFIGURAR-REPOSITORIO.md), punto 2) |
| **Identidad federada (WIF)** | Guardar una clave de Google en GitHub: GitHub pide un token de corta vida con su identidad OIDC (`id-token: write`) | [`desplegar-gcp.yml`](../../S4-Orquestacion-y-CI-CD/laboratorio-cloud-journey/desplegar-gcp.yml) |
| **Usuario sin privilegios** (`USER 10001`, no root) | Que un fallo de la API dé administración del contenedor | [`api-y-contenedor.md`](../../../04-Proyecto-Base/docs/api-y-contenedor.md) |
| **Contrato de entrada estricto** | Datos imposibles o campos inesperados: la API responde 422 y no los pasa al modelo | Contrato en `esquemas.py`, vigilado contra la firma del modelo al arrancar |
| **Dependencias fijadas** | Que una versión nueva rompa algo sin avisar | `mcp==1.30.0` en `requirements-agente.txt` (la 2.x quitó `FastMCP`: [guía de agentes](../laboratorio-agentes/guia.md), apartado 1) |
| **Permisos mínimos y aprobación humana** | Publicar sin que nadie lo vea | `permissions:` en los workflows y el *environment* `produccion` con revisores |
| **Reglas que no se negocian** | Que el agente prometa descuentos o dé datos personales | Skill `cumplimiento` y preguntas críticas de la puerta de calidad (se rechaza **siempre**, sin tolerancia) |

**La cadena de confianza del modelo.** El modelo del caso está guardado en un formato (`cloudpickle`) que **puede ejecutar código al cargarse**. Aquí es aceptable **porque el artefacto lo construye nuestro propio pipeline**; nunca se debe cargar un modelo de origen desconocido ([`api-y-contenedor.md`](../../../04-Proyecto-Base/docs/api-y-contenedor.md)). Lo que mantiene la cadena: el código en git, la imagen etiquetada con la huella, la ficha aprobada por una persona.

**Mantenimiento.** Es un trabajo, no un incidente: actualizar dependencias con prueba verde, caducar cachés y artefactos, retirar versiones viejas del historial (marcándolas, no borrándolas), revisar permisos y borrar lo que ya no se usa. Una versión fijada que no se actualiza nunca también es un riesgo (vulnerabilidades sin parchear): fijar no es olvidar. Con qué frecuencia: **decisión de tu equipo**, sin dato en el curso.

---

## 6. Actualización y rollback

**Actualizar con seguridad = candidata, puerta, aprobación, publicación.** El ciclo de S4 y de S5:

1. Una **versión candidata** (modelo con otros datos, o agente con otro prompt) se evalúa.
2. La **puerta de calidad** la compara con la de producción **con reglas escritas antes**. En el modelo, el AUC de test no puede empeorar más que una tolerancia (por defecto 0,02, [guía de S4](../../S4-Orquestacion-y-CI-CD/laboratorio-produccion-e2e/guia.md), apartado 0). En el agente, por orden: rechazada si falla una pregunta crítica; error si las preguntas no son comparables; **igual** si la huella es la misma; rechazada si herramienta o «sin inventar» caen más que la tolerancia (0,10, provisional); aceptada en otro caso ([guía de agentes](../laboratorio-agentes/guia.md), 6.7).
3. Una **persona aprueba** (*environment* `produccion`).
4. Se **publica** la imagen en GHCR y se abre un **PR** que cambia la ficha y el historial. Hasta fusionarlo, la candidata no es la de producción.

**Aceptada no es «mejor».** La puerta comprueba que no empeora lo medido; una humana decide si merece la pena. Y **rechazada es un resultado válido**: en el laboratorio, un prompt nuevo con tolerancia -0,10 se rechazó porque «sin inventar» ya estaba en 0,96 y no podía subir 0,10; no se construyó ni se publicó nada.

**Alias como puntero.** En el registro de MLflow, un **alias** (por ejemplo `champion`) es un nombre que apunta a **una versión**. Cambiar de versión es mover el puntero; **deshacer es volver a moverlo**. No se borra nada, y por eso el rollback es rápido. El laboratorio de MLOps clásico practica esto con el modelo de retención (ver su guía); el agente tiene el suyo (`agente-retencion` con `@champion`, apartado 4.4 de la guía de agentes).

**Rollback: tres cosas que enseñó el laboratorio de agentes.**
- **No reevalúa ni reconstruye**: restaura la ficha de una versión anterior desde el historial de git y abre un PR. No borra imágenes ni historial.
- **Solo se puede volver a lo que se publicó.** El rollback a la v1 del agente se paró (run 45277896553) porque esa imagen nunca estuvo en GHCR: lo que no está publicado no se restaura. Por eso la primera versión de cualquier cosa debería publicarse.
- **Git y MLflow son dos sitios.** El PR cambia lo que está en git; los alias viven en el servidor de MLflow donde se registraron. En el laboratorio ese servidor es efímero (del runner), así que el rollback **no mueve MLflow de verdad** (run 45278456252): con un servidor permanente haría falta además mover el alias allí.

---

## 7. Costes

- **Cada recurso en la nube cuesta mientras existe**, lo uses o no. Un recurso olvidado sigue cobrando.
- **Un presupuesto con alertas avisa, pero no corta el gasto** (el código del curso lo dice así y lo manda comprobar en la documentación vigente: [`preparar_proyecto.sh`](../../../04-Proyecto-Base/deploy/gcp/preparar_proyecto.sh)). Se crea **antes** que cualquier recurso.
- **Regla de S4: CREA → PRUEBA → BORRA.** Cada práctica de GCP tiene su `borrar.sh` ([`practicas-gcp/README.md`](../../S4-Orquestacion-y-CI-CD/practicas-gcp/README.md)). Lo que creas, lo borras y lo compruebas.
- **GitHub Actions también tiene coste de minutos**: en un repositorio público los minutos son gratuitos y en uno privado cuentan contra tu cuota ([`CONFIGURAR-REPOSITORIO.md`](../laboratorio-agentes/CONFIGURAR-REPOSITORIO.md), punto 3). Medidas: evaluar el agente en el runner tardó 780 s (run 45067018776), un lote unos 3 minutos y una nueva versión completa unos 10 minutos más la aprobación (guías de S4 y S5).
- **Un LLM local no cobra por llamada**, pero cuesta en disco (2,1 GB el modelo del curso), memoria y tiempo (apartado 3.3 de la guía de agentes).
- **Precios, créditos y cuotas de Google Cloud: sin verificar.** Consulta la página oficial y anota lo que veas con su fecha. La clase [«De on-premise a la nube»](../../S4-Orquestacion-y-CI-CD/clase-onpremise-a-nube/guia.md) y el [Cloud Journey](../../S4-Orquestacion-y-CI-CD/laboratorio-cloud-journey/guia.md) explican cómo se pensó el control del gasto en el curso.

---

## 8. Agentes como software

El mensaje del laboratorio de agentes es el cierre del curso: **un agente es un sistema de software más: se prueba, se evalúa, se versiona, se aprueba y se puede deshacer.** El modelo de ML sigue siendo el que decide; el LLM solo orquesta y redacta.

| Idea de este documento | En el agente |
|---|---|
| **Se prueba** (apartado 5) | Seis niveles: herramientas, protocolo MCP, bucle con LLM falso (rápido y siempre igual), evaluación con LLM real, seguridad y humo del despliegue |
| **Se evalúa** (apartado 2) | 25 preguntas de oro; las cifras esperadas se **calculan** con las herramientas, no se escriben a mano |
| **Se versiona** (apartado 1) | La **huella del agente** (prompt + modelo + skills): `e90daa8a20bef846` en la v1. Una coma de una skill es otra versión |
| **Se aprueba** (apartado 6) | Puerta de calidad + *environment* `produccion` + PR de `agentes/referencia-agente.json` |
| **Se puede deshacer** (apartado 6) | Workflow de rollback y alias de MLflow |

Dos avisos honestos: un LLM **no es determinista** (mismo modelo, otro resultado en el runner: por eso se compara con tolerancia y no a igualdad) y que una skill se cargue **no garantiza** que se use bien (el agente dio el mismo guion a cinco clientes).

---

## 9. Qué se comprobó y qué no

- **Comprobado en Actions** (22 y 23/11/2026): CI del agente, escenarios «igual», «rechazo» y «prompt-nuevo» (aceptada, aprobada, publicada, con PR), evaluación en el runner, rollback parado y rollback con PR. Los números de run están en la [guía de agentes](../laboratorio-agentes/guia.md), apartado 10.
- **Comprobado en S4** (22/11/2026): lote, bajo demanda, online, nueva versión con puerta y rollback ([guía](../../S4-Orquestacion-y-CI-CD/laboratorio-produccion-e2e/guia.md)).
- **Laboratorio de MLOps clásico** (`laboratorio-mlops/`: deriva por PSI, alias `champion` y monitoreo con alertas): lo implementa y valida otro equipo; su estado se lee **en su guía**, no aquí.
- **Sin verificar o sin dato:** panel de métricas de servicio en vivo, alertas de Cloud Monitoring, precios y cuotas de GCP, el agente en un Codespace, `@champion` del agente con el LLM real, el extra de dos agentes (no existe).

## 10. Glosario

| Término | Significado |
|---|---|
| **Huella** | Resumen corto del contenido de unos datos (o de un agente): lo mismo da lo mismo |
| **Ficha de referencia** | `referencia.json`: versión, huella, imagen y métricas de la versión en producción |
| **Alias** | Nombre que apunta a una versión en el registro de MLflow (`champion`) |
| **Deriva de datos / de rendimiento** | Cambio de lo que entra / pérdida de acierto |
| **PSI** | Índice que compara dos distribuciones por tramos; sus umbrales son convención |
| **Puerta de calidad** | Regla escrita que compara la candidata con la de producción |
| **Rollback** | Volver a una versión anterior sin borrar nada |
| **Registro (log)** | Lo que el sistema cuenta de sí mismo; sin datos del cliente |
| **WIF** | *Workload Identity Federation*: entrar en la nube sin claves guardadas |

## 11. Preguntas para comprobar que lo entiendes

1. ¿Qué dos archivos y qué etiqueta necesitas para saber con qué datos se hizo el modelo que sirve la API?
2. Tu API responde 200 en 15 ms y el AUC cae. ¿Qué métricas lo muestran y cuáles no?
3. ¿Por qué la deriva de rendimiento del caso Retail solo se puede medir con 90 días de retraso?
4. Escribe tres campos que **nunca** irían a un registro y por qué.
5. ¿Por qué un rollback a una versión que nunca se publicó falla, y qué harías para que no pase?
6. Un presupuesto con alertas llega al 100 %: ¿se ha detenido el gasto? ¿Qué haces?
