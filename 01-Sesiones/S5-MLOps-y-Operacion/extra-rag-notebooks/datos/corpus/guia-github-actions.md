# GitHub Actions en el curso (CI de la API de retención)

Este documento fija el convenio de integración continua del taller. Es un texto
original. El objetivo es que cada *push* a la rama de trabajo ejecute pruebas y mida
cobertura sin que nadie tenga que acordarse de correrlas a mano.

## El workflow

El archivo se llama **`ci-retencion.yml`** y vive en `.github/workflows/`. El
nombre del workflow (campo `name`) es `CI retención`. Corre en **`ubuntu-latest`**.

Disparadores:

- `push` a las ramas `develop` y `main` del *fork* del equipo.
- `pull_request` hacia `develop`.

No disparamos despliegue automático a producción en este curso. CI valida; el
despliegue se discute aparte y, si existe, es otro workflow.

## Trabajos

El workflow tiene un único trabajo llamado `test-and-lint` que, en este orden:

1. Reserva el repositorio (`actions/checkout`).
2. Instala Python 3.12.
3. Instala dependencias desde el archivo de bloqueo del proyecto.
4. Ejecuta el linter acordado en clase (Ruff).
5. Ejecuta la batería de pruebas con `pytest`.
6. Calcula cobertura. El umbral mínimo es **80 %**. Por debajo, el trabajo falla.

No se construye la imagen Docker en cada *push* en la versión básica del laboratorio,
para no alargar la cola ni exigir un registro. Quien quiera añadir un trabajo
`build-image` puede hacerlo como extra, no es obligatorio para el Avance 3.

## Secretos

El workflow de CI del laboratorio no necesita secretos de nube. Si más adelante se
añade un despliegue, los secretos viven en la configuración del repositorio, nunca
en el YAML. Un token pegado en `ci-retencion.yml` es un fallo grave de la rúbrica.

## Cómo se evidencia en el Avance 3

En el PDF se incluye una captura de una ejecución en verde del workflow `CI retención`
sobre el commit evaluado, y se indica la cobertura obtenida (número concreto, no un
«pasó»). Si la primera ejecución falló, se documenta la causa y la ejecución
posterior en verde. Eso suma; esconder el fallo no.

## Relación con Codespaces y el portátil

Las mismas pruebas deben poder correrse en local (`pytest` con cobertura) y en
Codespaces. CI no es un entorno mágico distinto: si solo pasa en la máquina de un
integrante, el workflow lo delatará. Esa es precisamente su utilidad.
