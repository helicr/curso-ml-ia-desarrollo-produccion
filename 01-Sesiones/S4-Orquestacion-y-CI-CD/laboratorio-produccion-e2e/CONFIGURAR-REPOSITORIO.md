# Configurar el repositorio (lo hace quien lo administra, una sola vez)

Sin estos ajustes, `nueva-version.yml` falla o, peor, publica sin que nadie lo apruebe. No son código: se hacen en la web de GitHub, en el repositorio donde van a correr los workflows (en el curso, tu *fork*). Los nombres de menús y botones son los **documentados en el taller de la sesión anterior** (`taller-ml-ia-dev-production`, guía detallada, pasos 17, 19, 21 y 22, y la cabecera de su `nueva-version.yml`), donde se ejecutaron el 14/11/2026. GitHub cambia su interfaz de vez en cuando: si un texto no coincide, busca el equivalente y avisa.

Antes de nada, copia a tu repositorio los workflows de este laboratorio (no hace falta tocarlos):

| Archivo de esta carpeta | Dónde va en tu repositorio |
|---|---|
| `nueva-version.yml` | `.github/workflows/nueva-version.yml` |
| `rollback.yml` | `.github/workflows/rollback.yml` |

## 0. Activar las Actions (solo en un *fork*)

Los workflows de un fork **vienen desactivados**. En la pestaña **Actions** de tu fork pulsa el botón verde **«I understand my workflows, go ahead and enable them»** (el texto exacto puede cambiar). Los `schedule` (la puntuación diaria por lotes) tampoco corren solos en un fork: se lanzan a mano con **Run workflow**.

## 1. El *environment* `produccion`, con revisores

Es lo que hace que la publicación **espere a una persona**.

1. **Settings** > **Environments** > **New environment**.
2. Nombre exactamente `produccion` (sin tilde, en minúsculas) > **Configure environment**.
3. Marca **Required reviewers** y añade a quien deba aprobar (en tu fork, **tú mismo**).
4. Guarda con **Save protection rules**.

**Qué debes ver:** en **Settings > Environments**, `produccion` con «Required reviewers» y el usuario.

**Si no lo haces bien:** si el *environment* no existe, GitHub lo crea solo **sin revisores**, y entonces el trabajo `publicar` **no se queda esperando**: publica directamente. Si el trabajo de publicación pasa sin pedirte aprobación, vuelve a este paso.

**Cómo se aprueba en cada ejecución:** cuando `publicar` queda en espera, GitHub suele mostrar «Waiting for review» y un botón **Review deployments**; se marca `produccion` y se pulsa **Approve and deploy**. Esos textos exactos están **sin verificar** (así lo decía el taller).

## 2. Permiso para que las Actions abran *pull requests*

El último trabajo (`referencia`) y el de `rollback.yml` abren un pull request.

1. **Settings** > **Actions** > **General** > **Workflow permissions**.
2. Marca **«Allow GitHub Actions to create and approve pull requests»** y guarda.

Los permisos por defecto del token pueden seguir en «solo lectura»: cada trabajo del workflow pide los suyos (por eso `nueva-version.yml` declara `permissions:` en cada uno).

**Si no lo haces:** el paso de abrir el pull request falla con un error de permisos (el taller lo describe como «not permitted to create or approve pull requests»; el texto exacto no se ha vuelto a ver con este laboratorio).

## 3. Visibilidad del paquete en GHCR

`nueva-version.yml` publica la imagen en `ghcr.io/<propietario>/retencion-api:v<N>-<huella>` (el propietario va en minúsculas) con el `GITHUB_TOKEN` de la ejecución, **sin ningún secreto propio**. La primera publicación **crea** el paquete `retencion-api`.

- Si el repositorio es **público**, en el taller los paquetes figuraron como **públicos** (heredan la visibilidad del repositorio) y su manifiesto se descargó sin sesión (comprobado el 14/11/2026).
- Si el paquete aparece **privado**, para poder descargarlo sin iniciar sesión (por ejemplo, desde el lote o desde un Codespace): **Packages** > el paquete > **Package settings** > **Change visibility** > **Public**. Si el repositorio es de una organización, puede que haya que permitir antes los paquetes públicos en la organización.
- Descargar la imagen con `docker pull` desde un Codespace **no se ha probado** (sin verificar).

## 4. Qué NO hace falta

- Ningún secreto ni token personal: solo el `GITHUB_TOKEN` que GitHub crea en cada ejecución.
- Ninguna protección de rama especial: los workflows **nunca** hacen push a `develop` ni a `main`; abren una rama nueva (`referencia/v<N>-<n.º de ejecución>`) y un pull request. Si tu repositorio ya protege `develop`, el pull request lo respeta tal cual.

## 5. Cosas que conviene saber (no son fallos)

- Un pull request creado con el `GITHUB_TOKEN` **no lanza otros workflows** por sí solo (regla de GitHub): el CI (`ci.yml` o `Validar`) no se ejecuta solo sobre el PR de la referencia. Se puede lanzar a mano sobre su rama o cerrar y reabrir el pull request.
- Lo que se crea en GitHub es **borrable**: los paquetes (Packages > el paquete > Package settings), el *environment* (Settings > Environments) y las ramas `referencia/...` tras cerrar su PR. Nada de esto afecta a tu código.
- La imagen `retencion-api` pesa unos cientos de MB (en el taller, la imagen análoga `cafe-api` midió 826 MB descomprimida y 183 MB comprimida; la de este caso no se ha medido todavía).

## Comprobación de que todo está listo

| Comprobación | Debes ver |
|---|---|
| Actions habilitadas | Los workflows «Nueva versión del modelo» y «Rollback de la versión del modelo» aparecen a la izquierda en la pestaña **Actions** |
| *Environment* | **Settings > Environments** lista `produccion` con revisores |
| Permiso de PR | **Settings > Actions > General** tiene marcada la casilla «Allow GitHub Actions to create and approve pull requests» |
| Primera ejecución | Con `fuente = muestra`, el resumen debe decir **IGUAL · nada que publicar** y los trabajos 2 a 4 salen en gris (omitidos). Esto **no se ha verificado todavía en Actions**: depende de que la huella de datos calculada en el runner (`pandas` de `requirements-dev.txt`) sea la de `models/referencia.json`; en un portátil con otro entorno sí coincidió |
