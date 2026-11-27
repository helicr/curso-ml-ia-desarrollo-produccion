# Guion del docente · S4 (240 min) · PROPUESTA

Miércoles 25 de noviembre, de 10:00 a 14:00 (hora de Perú), según el calendario del repositorio. Sesión «Orquestación y CI/CD con GitHub Actions». Hoja de ruta de las piezas: [`practica/guia-laboratorio.md`](practica/guia-laboratorio.md). Teoría: [`teoria/README.md`](teoria/README.md). Tarea: [`tarea/README.md`](tarea/README.md).

> **Esto es una propuesta.** Las duraciones son un **reparto propuesto**, no tiempos medidos en clase. Lo único medido son las ejecuciones: el lote diario tardó unos 3 min y «Validar la producción completa» unos 2 min. Las piezas de Google Cloud (clase, Cloud Journey y prácticas) **no caben juntas** en 4 h; el recorte de abajo es una **decisión del profesor**.

Lo que se dice en el aula separa lo **comprobado** (ensayado entre el 22 y el 25/11/2026) de lo **sin verificar** o **sin dato**. Sin precios, cuotas ni créditos: «consulta la página oficial».

## Bloques

| Hora (Perú) | Min | Qué se hace | Material | En vivo / capturas |
|---|---|---|---|---|
| 10:00–10:10 | 10 | **Bienvenida.** Qué se entregó (avance 3: rojo → verde) y qué vamos a hacer hoy: que el pipeline lo ejecute un workflow, que una persona apruebe, y llevarlo a la nube sin claves. | Este guion · [`README.md`](README.md) | En vivo |
| 10:10–10:40 | 30 | **Teoría de Actions con los YAML reales abiertos.** Workflow, job, step, runner; disparadores y por qué «Run workflow» no sale (ensayo por rama); variables, secretos y *environment* (el nombre exacto); caché, artefactos, `needs`, `concurrency`, permisos; CI frente a CD. | [`teoria/README.md`](teoria/README.md), apartados 2 a 8 · [`puntuar-lote.yml`](laboratorio-produccion-e2e/puntuar-lote.yml) · [`nueva-version.yml`](laboratorio-produccion-e2e/nueva-version.yml) | En vivo en el editor |
| 10:40–10:55 | 15 | **Clase «De on-premise a la nube», versión corta.** Solo el hilo: por qué la nube, Google Cloud en una diapositiva, qué pieza nuestra iría a qué servicio y costes. El resto, como lectura. | [`clase-onpremise-a-nube/index.html`](clase-onpremise-a-nube/index.html) (29 diap.) · [`guia.md`](clase-onpremise-a-nube/guia.md) | Diapositivas |
| 10:55–11:05 | 10 | **Configurar el repositorio** (una vez): *environment* `produccion` con revisores y permiso para que Actions abra PR. Enseñar la trampa: sin el *environment* correcto, no pide aprobación. | [`laboratorio-produccion-e2e/CONFIGURAR-REPOSITORIO.md`](laboratorio-produccion-e2e/CONFIGURAR-REPOSITORIO.md) · [`guia.md`](laboratorio-produccion-e2e/guia.md), paso 2 | En vivo en el *fork* del docente; capturas de respaldo |
| 11:05–11:50 | 45 | **Laboratorio B: producción de punta a punta.** Lote (`puntuar-lote.yml`, unos 3 min), validar (unos 2 min), y **versión nueva** con los tres escenarios: igual, rechazada y aceptada (que espere la aprobación y se apruebe). Mientras corre, leer el registro. Rollback solo si hay margen. | [`laboratorio-produccion-e2e/guia.md`](laboratorio-produccion-e2e/guia.md) · [`index.html`](laboratorio-produccion-e2e/index.html) (26 diap.) | En vivo; lanzar los escenarios por rama (`lab/nueva-version/…`); capturas de respaldo |
| 11:50–12:05 | 15 | **Pausa.** Pedir que, durante la pausa, cada persona compruebe que su cuenta de Google tiene Google Cloud activado y que quien no lo tenga lo diga (seguirá C como observador). | — | — |
| 12:05–12:20 | 15 | **WIF sin claves**: el problema de la clave JSON, la política que la prohíbe en la organización del curso y los seis pasos de WIF. | [`teoria/README.md`](teoria/README.md), apartado 5 · [`laboratorio-cloud-journey/guia.md`](laboratorio-cloud-journey/guia.md), 3.4 | Diapositivas y YAML |
| 12:20–13:20 | 60 | **Laboratorio C: Cloud Journey**, dirigido. Preparar con el script, las cinco variables, push a `lab/cloud-journey/…`, **aprobar**, probar la URL pública (0,828 como en local), ver el modelo en Vertex AI y **borrar todo**. | [`laboratorio-cloud-journey/guia.md`](laboratorio-cloud-journey/guia.md) · [`index.html`](laboratorio-cloud-journey/index.html) (29 diap.) · [`preparar-gcp-s4.sh`](laboratorio-cloud-journey/preparar-gcp-s4.sh) · [`borrar-gcp-s4.sh`](laboratorio-cloud-journey/borrar-gcp-s4.sh) | En vivo en la cuenta del curso; capturas de respaldo |
| 13:20–13:30 | 10 | **Prácticas de GCP: qué hay y qué queda para casa.** La 04 ya se vio en C. Mostrar el patrón crear → probar → borrar y `borrar-todo.sh`; avisar de lo que más cobra si se olvida (endpoint de Vertex AI y clúster de GKE) y del crédito (Vertex y Gemini). | [`practicas-gcp/README.md`](practicas-gcp/README.md) | Solo se explica |
| 13:30–13:50 | 20 | **Tarea (avance 4).** Qué se pide, qué es opcional, el rojo debe venir de una comprobación, y cómo entregar. Entrega a las 10:00 del viernes 27 de noviembre, con el formulario. | [`tarea/README.md`](tarea/README.md) · [`tarea/rubrica.md`](tarea/rubrica.md) · [`evidencias/plantilla-avance-4.md`](evidencias/plantilla-avance-4.md) | En vivo |
| 13:50–14:00 | 10 | **Borrar y cerrar.** Recordar: `borrar-gcp-s4.sh`, `borrar-todo.sh`, borrar el Codespace y revisar la factura. Preguntas. | [`checklist.md`](checklist.md) | En vivo |

Total: 10 + 30 + 15 + 10 + 45 + 15 + 15 + 60 + 10 + 20 + 10 = **240 min**.

**Por qué este orden:** primero lo que no cuesta dinero (Actions, aprobación, puerta de calidad) y que es la base de la tarea; después la nube, que añade WIF; y al final la limpieza, que no se salta.

## Mensajes que no deben perderse
- **Un workflow es un pipeline que no depende de tu equipo:** corre en una máquina vacía que desaparece; lo que importa se guarda como **artefacto**.
- **«Run workflow» solo sale en la rama principal:** por eso los ensayos se hacen por nombre de rama.
- **El nombre exacto del *environment* importa:** si no existe, se crea sin revisores y **no pide aprobación**.
- **Sin claves:** WIF da acceso temporal por ejecución; la organización del curso prohíbe las claves de cuentas de servicio.
- **Quien despliega no es quien ejecuta:** una cuenta despliega, otra (sin roles) ejecuta la API.
- **Crea → prueba → borra.** Un presupuesto avisa, no corta el gasto.
- **Un run esperando aprobación bloquea el siguiente** del mismo grupo `concurrency`.
- **Tarea:** el rojo viene de una comprobación, no de un error del YAML; una captura sin enlace no demuestra nada.

## Si el tiempo se descontrola
- Orden de recorte (propuesta): 1.º el rollback y el escenario «igual» de la pieza B; 2.º la clase de la nube pasa entera a lectura; 3.º el modelo en Vertex AI (paso 9 de C) pasa a la demostración con capturas. **No se recorta** la configuración del *environment*, la aprobación, el borrado final ni la tarea.
- Si la cuenta de Google Cloud de alguien no está lista: sigue C como demostración y lo **declara** en su evidencia.
- La aprobación es el momento didáctico: dejar un run **esperando** unos instantes y preguntar qué pasaría si el *environment* no existiera.

## Si algo falla en directo

| Síntoma | Respuesta |
|---|---|
| No aparece ningún run | Actions sin activar en el *fork* o rama que no coincide con el filtro (`lab/…`). Mirar la pestaña Actions y el nombre de la rama |
| «Run workflow» no aparece | Es lo esperado: el workflow no está en la rama principal. Lanzar por push a la rama de ensayo |
| El run nuevo se queda en cola | Hay otro del mismo grupo `concurrency` esperando aprobación: aprobarlo o cancelarlo |
| El job de publicar no pide aprobación | El *environment* no existe o no tiene revisores: corregirlo y repetir |
| Falla el último paso (PR) | Falta el permiso «Allow GitHub Actions to create and approve pull requests» |
| Falla la entrada a Google Cloud | Variables mal copiadas, o el repositorio del script no es el de la persona |
| `NOT_FOUND` al preparar WIF | Pool en estado `DELETED` 30 días: usar la versión actual del script |
| Alguien no puede activar Google Cloud o facturación | Sigue la demostración, lo declara; no resta |
| Se quedó algo sin borrar | `borrar-gcp-s4.sh` y `borrar-todo.sh`; revisar los listados |

## Después de la sesión
- Borrar con [`borrar-gcp-s4.sh`](laboratorio-cloud-journey/borrar-gcp-s4.sh) y [`borrar-todo.sh`](practicas-gcp/borrar-todo.sh), borrar el Codespace y revisar la factura (ver [`checklist.md`](checklist.md)).
- Anotar incidencias (paso / esperado / obtenido / mensaje / acción), sin credenciales ni identificadores.
