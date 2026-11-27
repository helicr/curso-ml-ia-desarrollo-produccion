# Tarea S4 · Orquesta el pipeline de tu caso con GitHub Actions

**Esta tarea es el avance 4 de tu caso propio (Bank Marketing).** No hay un ejercicio aparte sobre Online Retail II: lo que ves en los laboratorios de S4 es el modelo a imitar; lo que entregas es **tu** pipeline.

**Entrega:** a las 10:00 (hora de Perú) del **viernes 27 de noviembre**, antes de que empiece S5 (es la fecha que figura en la hoja del caso, [`tu-caso-bank-marketing.md`](../../../02-Proyecto-Transversal/alumno/tu-caso-bank-marketing.md)) · repositorio personal de tu caso con la rama `avance-4` (o carpeta comprimida si no hay repositorio, aunque entonces no se puede demostrar el workflow: ver «Honestidad»). Se entrega con el **formulario de Google del curso** (el instructor da el enlace en clase): tu nombre, el número de avance (4), el enlace a tu rama o carpeta y «qué no pude ejecutar». Si tu repositorio es privado, añade al instructor como colaborador (su usuario lo indica en clase). Para ramas: [`git-y-ramas.md`](../../../07-Recursos/guias/git-y-ramas.md).

> **Qué se evalúa:** que tu pipeline **se ejecute de verdad en un workflow**, con sus etapas explicadas, con el historial de lo que falló y por qué, y con una decisión argumentada. La nube es **opcional**: no tenerla no resta; fingirla, sí.

## Qué se pide
La parte (a) es obligatoria y es la que más pesa. (b) y (c) son opcionales.

**(a) Un workflow de GitHub Actions que orquesta el pipeline de tu caso**, en el repositorio de tu caso:

1. **Etapas.** El workflow ejecuta, **en este orden y como trabajos o pasos distintos**, estas etapas (adapta los nombres a tu proyecto):
   1. **Datos:** deja los datos y las capas listas (raw → master → fs → ml, o lo que tu repositorio tenga).
   2. **Entrenamiento:** entrena tu modelo.
   3. **Métricas:** calcula y deja visibles las métricas (por ejemplo, AUC en validación y prueba) en el resumen de la ejecución.
   4. **Artefacto:** guarda con `upload-artifact` el modelo y las métricas, para poder descargarlos.
2. **Al menos dos trabajos** unidos por `needs:` (por ejemplo, «calidad» → «pipeline»), de modo que si el primero falla el segundo no corre. Y **algo se pasa entre trabajos o se guarda como artefacto** (el runner se destruye al acabar).
3. **Disparadores:** `push` a la rama `avance-4`, y `workflow_dispatch` si quieres poder lanzarlo a mano (recuerda que «Run workflow» solo sale si el workflow está en la rama principal; por eso se ensaya con el `push` a una rama con nombre).
4. **Pruebas dentro del workflow:** el trabajo de calidad ejecuta tus pruebas (`python -m pytest`, o lo que uses) **antes** de entrenar.
5. **Permisos mínimos y sin secretos:** `permissions: contents: read` por defecto (amplía solo en el trabajo que lo necesite y dilo), `timeout-minutes` en cada trabajo y **ningún secreto** (el pipeline de tu caso no necesita ninguno). Ni claves, ni tokens, ni `.env` en el repositorio. Recomendado: `concurrency` y caché de dependencias, cada uno con su porqué.
6. **El historial rojo → verde, demostrado.** Una ejecución en **rojo** y la ejecución en **verde** del commit que lo arregla, con **enlaces** a las dos y a sus commits. **El rojo debe venir de una comprobación del pipeline** (una prueba que protege una regla de tu caso, o una puerta de calidad que rechaza un modelo peor), **no** de un error de sintaxis del YAML ni de una dependencia que no se instala (esos también se anotan, pero no sustituyen). El arreglo es un cambio de código o de datos; **no** vale borrar o saltar la comprobación.
7. **El workflow en verde al entregar:** la última ejecución de `avance-4` es verde.
8. **Registrar en MLflow (recomendado):** si tu pipeline ya usa MLflow, registra el modelo y sus métricas durante la ejecución. Como el runner se destruye, **sube la carpeta de MLflow como artefacto**; si no, el registro se pierde.

**(b) Una aprobación con *environment* (opcional).** Un trabajo final de «publicación» (aunque solo escriba un mensaje o suba un archivo) protegido por `environment: produccion` con revisores, como en el laboratorio. Para sumar, **comprueba y documenta** que de verdad espera: el nombre exacto importa; si el *environment* no existe, GitHub lo crea sin revisores y **no pide aprobación**. Captura del aviso «Review deployments» con tu correo tapado.

**(c) Google Cloud (opcional, solo si pudiste).** Si tienes cuenta de Google con Google Cloud activado y quieres llevar algo allí (por ejemplo, subir tu imagen a Artifact Registry o desplegar en Cloud Run), hazlo **sin claves** con WIF, como en el laboratorio Cloud Journey, y **bórralo todo al terminar**. **Si no pudiste, declara el motivo exacto** (por ejemplo, «el alta pidió una cuenta de facturación y no la activé» o el mensaje de error). No restas por no hacerlo.

## Dónde se hace
- En el repositorio de **tu caso**, con la misma mecánica del laboratorio de S3 y de los de S4. Puedes partir de [`puntuar-lote.yml`](../laboratorio-produccion-e2e/puntuar-lote.yml), [`nueva-version.yml`](../laboratorio-produccion-e2e/nueva-version.yml), [`desplegar-gcp.yml`](../laboratorio-cloud-journey/desplegar-gcp.yml) o del workflow de pruebas de S3 ([`pruebas-proyecto.yml`](../../S3-Despliegue-y-Redes-Neuronales/laboratorio-github-actions/pruebas-proyecto.yml)). **Lo que copies y lo que cambies, anótalo.**
- Los datos: decide cómo llegan al runner (el CSV en el repositorio con la cita de la fuente que exige su licencia, datos generados en el propio workflow, o una muestra pequeña de prueba) y **explícalo en la decisión**. Ninguna es la «correcta»; se evalúa que funcione y que lo justifiques.

## Pasos
1. Crea la rama `avance-4` desde tu rama del avance 3 (o la que tengas al día) y súbela.
2. Escribe el workflow con las etapas y pruébalo. Mira la pestaña **Actions**. Si no aparece ninguna ejecución: ¿Actions activado en tu repositorio?, ¿la rama coincide con `on: push: branches`?
3. Anota **cada fallo** que te dé (síntoma, línea del registro, causa, arreglo). Son la materia prima de la sección «Fallos encontrados».
4. Provoca (o aprovecha) el **rojo** con una comprobación del pipeline y copia el enlace de la ejecución.
5. Sube el arreglo y copia el enlace de la ejecución **en verde**.
6. (Opcional) Añade el *environment* con revisores y comprueba que espera. (Opcional) Si hiciste lo de Google Cloud, **bórralo todo** y revisa la facturación.
7. Completa [`evidencias/plantilla-avance-4.md`](../evidencias/plantilla-avance-4.md) (cópiala a tu repositorio) y la sección «Avance 4» de [`plantilla-avance.md`](../../../02-Proyecto-Transversal/alumno/plantilla-avance.md).
8. Comprueba que la última ejecución de `avance-4` está en verde y entrega con el formulario.

## Evidencia mínima
- El archivo del workflow en tu rama `avance-4`.
- **Tabla de etapas**: qué hace cada una, qué entra, qué sale y en qué trabajo corre.
- **Enlace a la ejecución en rojo** (y su commit), con la comprobación que falló y la línea del registro; **enlace a la ejecución en verde** del arreglo; y enlace a la **última ejecución en verde** al entregar. Una captura sin enlace no cuenta.
- **Fallos encontrados**: al menos **dos**, con síntoma, línea del registro, causa y arreglo (el rojo provocado cuenta como uno).
- Qué **artefactos** deja cada ejecución y cómo los descargas.
- **Permisos y secretos**: qué `permissions:` usa cada trabajo y confirmación de que no hay secretos.
- **Una decisión** explicada (por ejemplo, cómo llegan los datos al runner, qué corre en cada `push`, qué tolerancia usas en la puerta de calidad, o por qué separas o no los trabajos).
- Si hiciste (b): captura del *environment* esperando aprobación. Si hiciste (c): cómo entraste (WIF) y la prueba de que **borraste** lo creado. Si no pudiste (c): el motivo exacto.
- `evidencias/plantilla-avance-4.md` y la sección del avance 4 de `plantilla-avance.md` completadas.

## Rúbrica
Ver [`rubrica.md`](rubrica.md): 20 % reproducibilidad, 40 % técnica, 40 % análisis y decisión.

## Honestidad
No se evalúa solo por capturas: una captura de una ejecución verde **sin enlace** a la ejecución no la demuestra. Si algo no lo pudiste hacer (Actions desactivado, sin repositorio en GitHub, sin cuenta de Google Cloud, un paso que no logras), escríbelo con el **error exacto**: declararlo es parte de lo que se evalúa. **Declara lo que no ejecutaste** y no presentes como hecho lo que no lo está. No pegues en el repositorio ni en la evidencia claves, tokens, códigos de verificación, el ID de tu proyecto, tu correo ni el identificador de tu cuenta de facturación (**tapa también las capturas**). **Cita la ayuda que recibiste** (personas, documentación y herramientas, **incluidas las de IA**) y para qué.
