# Checklist S4

Plan (miércoles 25 de noviembre, 10:00–14:00, hora de Perú, según el calendario del repositorio): workflows y aprobación en GitHub Actions, Google Cloud sin claves y tarea del avance 4. Guion propuesto: [`guion.md`](guion.md). Hoja de ruta de laboratorios: [`practica/guia-laboratorio.md`](practica/guia-laboratorio.md).

## Antes de la sesión (docente)
- [ ] **Fork propio** del repositorio del curso **copiando `develop`**: al crearlo, **desmarcar «Copy the main branch only»** (si no, el fork no trae `develop`).
- [ ] **Actions activado** en el fork (pestaña Actions: aceptar el aviso).
- [ ] **Environment `produccion`** con **revisores** (nombre exacto, sin tilde): Settings › Environments. Comprobar «1 protection rule». Ver [`laboratorio-produccion-e2e/CONFIGURAR-REPOSITORIO.md`](laboratorio-produccion-e2e/CONFIGURAR-REPOSITORIO.md).
- [ ] **Permiso de PR**: Settings › Actions › General › Workflow permissions › «Allow GitHub Actions to create and approve pull requests».
- [ ] Ensayo previo hecho: al menos un run en verde de `puntuar-lote.yml`, uno de `nueva-version.yml` aceptado esperando aprobación y uno rechazado, para enseñarlos si los runners van lentos. **Ningún run antiguo esperando aprobación** (bloquearía los del mismo grupo `concurrency`).
- [ ] **Google Cloud**: cuenta de Google con Google Cloud activado según [`preparar-gcp-para-s4.md`](../S3-Despliegue-y-Redes-Neuronales/preparar-gcp-para-s4.md); proyecto del curso, facturación vinculada y región `southamerica-west1`. Preparado con [`preparar-gcp-s4.sh`](laboratorio-cloud-journey/preparar-gcp-s4.sh) y el repositorio `curso` de Artifact Registry ([`CONFIGURAR-GCP.md`](laboratorio-cloud-journey/CONFIGURAR-GCP.md)). Comprobar que no queda un pool WIF en estado `DELETED` sin restaurar (el script actual lo restaura).
- [ ] Las **cinco variables** `GCP_…` creadas en el fork (Repository variables, no secretos).
- [ ] **Codespace propio** listo desde `develop`, ya arrancado.
- [ ] **Capturas de respaldo abiertas** de las piezas B y C (están en las carpetas `img/` de cada laboratorio).
- [ ] Enlaces abiertos: [`teoria/README.md`](teoria/README.md), [`clase-onpremise-a-nube/index.html`](clase-onpremise-a-nube/index.html), [`laboratorio-produccion-e2e/index.html`](laboratorio-produccion-e2e/index.html), [`laboratorio-cloud-journey/index.html`](laboratorio-cloud-journey/index.html), [`tarea/README.md`](tarea/README.md) y [`guion.md`](guion.md).
- [ ] Repasar el bloque de Google Cloud sin cifras: nada de precios, créditos ni cuotas; «consulta la página oficial». Tener presente que el crédito de la prueba **no cubre Vertex AI ni Gemini** en cuentas dadas de alta desde el 16/11/2026 y que Gemini **no está en Santiago**.
- [ ] Tener a mano el enlace del formulario de Google del curso y el usuario de GitHub del instructor (para los repositorios privados).
- [ ] Decidir el recorte de las piezas de Google Cloud (ver la hoja de ruta, apartado 3).

## Antes de la sesión (alumnado)
- [ ] Avance 3 entregado (miércoles 25, 10:00, hora de Perú) con el formulario de Google del curso.
- [ ] Cuenta de GitHub con la sesión iniciada y un *fork* del repositorio del curso con **`develop`** (al crearlo, desmarcar «Copy the main branch only»), con **Actions activado**.
- [ ] Codespace del curso que arranca.
- [ ] Cuenta de Google con Google Cloud activado (según [`preparar-gcp-para-s4.md`](../S3-Despliegue-y-Redes-Neuronales/preparar-gcp-para-s4.md)); si no, lo dices y sigues como observador.
- [ ] El repositorio de tu caso propio en GitHub con tu workflow de pruebas de S3.

## Durante la sesión (alumnado)
- [ ] Sabes por qué «Run workflow» no sale y lanzas un ensayo por push a una rama con nombre.
- [ ] Tu *environment* `produccion` existe con revisores; has visto un run **esperando aprobación**.
- [ ] Puedes explicar la diferencia entre CI y CD y qué decidió la puerta de calidad en cada escenario.
- [ ] Puedes explicar con tus palabras por qué no hay claves (WIF) y qué cuenta despliega y cuál ejecuta.
- [ ] Si tienes cuenta de Google Cloud: la API respondió en Cloud Run y **lo borraste todo**.
- [ ] Anotas **cada fallo** con el error exacto (alimenta tu tarea).
- [ ] Tarea (avance 4) entendida y [`evidencias/plantilla-avance-4.md`](evidencias/plantilla-avance-4.md) descargada.

## Después de la sesión (docente)
- [ ] Borrar lo creado en Google Cloud con [`borrar-gcp-s4.sh`](laboratorio-cloud-journey/borrar-gcp-s4.sh) (Cloud Shell; opcionalmente `DESVINCULAR_FACTURACION=si`) y [`borrar-todo.sh`](practicas-gcp/borrar-todo.sh) (de la carpeta `practicas-gcp`). Los listados (Cloud Run, clústeres, repositorios, lotes de Dataproc, endpoints, modelos, buckets) deben salir **vacíos**.
- [ ] **Borrar el Codespace** (y parar los demás).
- [ ] **Revisar la factura** y los presupuestos con alertas (avisan, no cortan el gasto).
- [ ] Revisar y aprobar o cancelar runs que sigan esperando aprobación; borrar ramas `lab/…` y `referencia/…` si ya no hacen falta.
- [ ] Anotar incidencias del grupo.

## Después de la sesión (alumnado, antes del viernes 27 a las 10:00)
- [ ] Rama `avance-4` en el repositorio de tu caso, con el workflow que ejecuta las etapas (datos → entrenamiento → métricas → artefacto) en al menos dos trabajos con `needs:`.
- [ ] Enlaces a la ejecución en rojo (por una comprobación del pipeline), a la verde del arreglo y a la última de `avance-4` en verde.
- [ ] Al menos dos fallos documentados con síntoma, causa y arreglo.
- [ ] Permisos mínimos y ningún secreto, clave ni token en el repositorio ni en el registro; capturas con correo e identificadores tapados.
- [ ] (Opcional) *Environment* con aprobación comprobada. (Opcional) Si usaste Google Cloud: **borraste todo** con los scripts y revisaste la factura; si no pudiste, el motivo exacto.
- [ ] Evidencia y sección «Avance 4» de la plantilla del caso completadas; entrega con el formulario de Google del curso.
- [ ] **Codespace borrado o parado** al terminar.

## Registro de incidencias
Paso / esperado / obtenido / mensaje / acción. Sin credenciales ni identificadores. Prestar atención a lo que más puede variar entre personas: Actions en los *fork*, ejecuciones en cola por `concurrency`, el *environment* y la entrada a Google Cloud.
