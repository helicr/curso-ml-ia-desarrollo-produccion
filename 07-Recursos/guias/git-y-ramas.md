# Git y GitHub: guía y chuleta

**Se usa en:** S0 (instalar, configurar, clonar) y en todas las entregas: la tarea de S1 se entrega en una rama `tarea-s1` de tu repositorio personal.
**Terminal:** CMD, PowerShell, Git Bash o la terminal de VS Code. Los comandos son los mismos.

## Para qué sirve
Git guarda la **historia** de tu proyecto como una cadena de fotografías (*commits*). Permite volver atrás, probar ideas en **ramas** sin romper lo que funciona y trabajar con otras personas.
**GitHub** es el sitio donde vive la copia compartida (el *remoto*). Git funciona sin GitHub; GitHub sin Git no.

```
 tu carpeta de trabajo  --git add-->  área de preparación  --git commit-->  repositorio local  --git push-->  GitHub (origin)
        (working tree)                    (stage)                              (historia)         <--git pull--
```
Palabras que se repiten:
- **Commit:** una fotografía con mensaje. **Rama (*branch*):** una línea de commits con nombre. **HEAD:** dónde estás ahora.
- **origin:** el nombre habitual del remoto. **main** / **develop:** ramas del repositorio del curso.

## Configuración inicial (checklist 1 de S0)
```text
git --version
git config --global user.name "Tu Nombre"
git config --global user.email "tu_correo@ejemplo.com"
git config --global init.defaultBranch main
git config --global --list
```
Usa el mismo correo que en tu cuenta de GitHub. **Autenticación en Windows:** Git para Windows trae el *Git Credential Manager*; el primer `git push` abre el navegador para iniciar sesión en GitHub.
No escribas contraseñas ni pegues *tokens* en archivos, capturas o chats.

## Clonar el repositorio del curso
```text
git clone https://github.com/helicr/curso-ml-ia-desarrollo-produccion.git
cd curso-ml-ia-desarrollo-produccion
code .
```
**Hasta que `develop` se fusione en `main`,** el contenido del curso está en la rama `develop` (`main` está casi vacía). Clona directamente esa rama:
```text
git clone --branch develop https://github.com/helicr/curso-ml-ia-desarrollo-produccion.git
```
o, si ya clonaste, `git switch develop`. Cuando el instructor fusione, esta nota ya no hará falta.

## El ciclo diario
```text
git status                 # ¿qué ha cambiado?
git add archivo.py         # prepara un archivo   (git add .  prepara todo lo cambiado)
git commit -m "Añadir variable monto_180d"
git push                   # sube tus commits a GitHub
git pull                   # baja los de otros (o los tuyos desde otro equipo)
```
Buenos mensajes de commit: en imperativo y concretos (*«Corregir fecha de corte»*, no *«cambios»*). Haz commits pequeños y frecuentes.
Antes de `git add .`, mira `git status`: así no subes archivos que no querías.

## Ramas
Una rama te deja trabajar sin tocar lo que ya funciona.
| Quiero... | Comando |
|---|---|
| Ver mis ramas (la actual lleva `*`) | `git branch` · con remotas: `git branch -a` |
| Crear una rama y pasar a ella | `git switch -c tarea-s1` |
| Cambiar de rama | `git switch main` |
| Fusionar otra rama en la actual | `git merge tarea-s1` |
| Fusionar dejando constancia en la historia | `git merge --no-ff tarea-s1` |
| Borrar una rama ya fusionada | `git branch -d tarea-s1` |
| Subir una rama nueva por primera vez | `git push -u origin tarea-s1` |
| Borrar una rama en GitHub | `git push origin --delete tarea-s1` |

Pasar de rama con cambios sin guardar puede fallar: haz commit o usa `git stash` (más abajo).
Para fusionar: ponte en la rama que **recibe** (`git switch main`) y ejecuta `git merge la-que-aporta`.

## Remotos: qué hace cada comando
| Comando | Qué hace |
|---|---|
| `git remote -v` | Muestra a qué URL apunta `origin` |
| `git fetch` | Baja novedades **sin tocar tu trabajo**. Después, `git status` te dice si vas por detrás |
| `git pull` | `fetch` + fusionar en tu rama actual |
| `git push` | Sube tus commits. La primera vez en una rama: `git push -u origin nombre-de-rama` |
| `git clone URL` | Copia un repositorio completo a tu equipo |

## Entrega de la tarea (propuesta, confirma con el instructor)
La tarea de S1 pide un **repositorio personal con la rama `tarea-s1`**. Una forma de hacerlo:
1. En GitHub, crea un repositorio nuevo **vacío** (sin README) con tu nombre.
2. En tu copia del curso:
```text
git switch -c tarea-s1
git remote rename origin curso
git remote add origin https://github.com/TU_USUARIO/TU_REPOSITORIO.git
git push -u origin tarea-s1
```
3. Trabaja con commits normales y `git push` cuando quieras entregar un avance.
`curso` queda apuntando al repositorio original, así que `git pull curso develop` trae las novedades del instructor.
Alternativa: el botón **Fork** de GitHub hace una copia a tu cuenta y conserva el vínculo.

## Deshacer sin miedo
| Situación | Comando |
|---|---|
| Descartar los cambios de un archivo (**irrecuperable**) | `git restore archivo` |
| Sacar un archivo del área de preparación | `git restore --staged archivo` |
| Corregir el mensaje o añadir algo al **último** commit (si aún no lo subiste) | `git commit --amend -m "mensaje nuevo"` |
| Deshacer un commit **ya subido**, creando otro que lo revierte | `git revert HEAD` |
| Guardar a un lado lo que tienes a medias | `git stash push -m "a medias"` |
| Recuperarlo | `git stash pop` · ver la lista: `git stash list` |
| Deshacer el último commit pero conservar los cambios | `git reset --soft HEAD~1` |

`git reset --hard` y `git push --force` **destruyen trabajo**: no los uses sin saber exactamente qué borran.
Un commit ya subido y compartido se deshace con `revert`, no con `reset`.

## Conflictos
Aparecen al fusionar cuando dos ramas cambiaron las mismas líneas. Git se detiene y marca el archivo:
```text
<<<<<<< HEAD
tu versión
=======
la versión que llega
>>>>>>> tarea-s1
```
1. `git status` muestra los archivos en conflicto (`both modified`).
2. Edita el archivo: deja el texto final y **borra las tres líneas de marcas**. VS Code ofrece botones *Accept Current / Incoming / Both* sobre cada conflicto.
3. `git add archivo` y `git commit` (sin `-m`, Git propone el mensaje).
4. Si te pierdes: `git merge --abort` vuelve al estado anterior.

## Mirar la historia
| Quiero... | Comando |
|---|---|
| Resumen de commits | `git log --oneline -10` |
| Ramas dibujadas | `git log --oneline --graph --all` |
| Qué he cambiado (sin preparar) | `git diff` · preparado: `git diff --staged` |
| Qué cambió un commit | `git show abc1234` |
| Marcar una versión | `git tag -a v0.1 -m "primera versión"` · `git push origin --tags` |

## `.gitignore` y secretos
`.gitignore` lista lo que Git no debe seguir: entornos virtuales, `__pycache__/`, bases `.db`, modelos generados y, sobre todo, **`.env`** (donde van contraseñas y claves).
El repositorio ya trae uno en la raíz y otro en `04-Proyecto-Base/`. Para comprobar que un archivo se ignora: `git check-ignore -v .env`.
Si subiste un secreto por error, **borrarlo del repositorio no basta**: considera la clave comprometida y cámbiala. Un `.gitignore` no afecta a archivos que Git ya seguía (`git rm --cached archivo`).

## Avisos que verás y no son errores
- `warning: in the working copy of 'x', LF will be replaced by CRLF...` En Windows, Git convierte los saltos de línea al guardar. Es normal; el repositorio lo controla con `.gitattributes`.
- `Your branch is behind 'origin/main' by 1 commit`: alguien subió algo. Haz `git pull`.
- `You are in 'detached HEAD' state`: miras un commit suelto. Vuelve con `git switch -` o `git switch main`.

## Errores frecuentes
| Síntoma | Qué hacer |
|---|---|
| `fatal: not a git repository` | Estás fuera de la carpeta del proyecto. `cd` hasta ella. |
| `Author identity unknown` | Faltan `user.name` y `user.email`. Ejecuta los dos `git config` de arriba. |
| `rejected ... non-fast-forward` al hacer `push` | Hay commits en GitHub que no tienes. `git pull`, resuelve si hay conflicto y vuelve a `git push`. |
| `Please commit your changes or stash them before you switch branches` | Tienes cambios sin guardar. `git commit` o `git stash push`. |
| `shallow update not allowed` al hacer `push` a otro repositorio | Clonaste con `--depth 1` (clon superficial). Haz un clon completo (sin `--depth`) o `git fetch --unshallow`. |
| `Permission denied` / `Authentication failed` | Sesión de GitHub caducada o sin permiso en ese repositorio. Reinicia sesión; comprueba que la URL de `origin` es tuya. |
| Subí un archivo que no quería | Si no hiciste `push`: `git reset --soft HEAD~1`. Si ya lo subiste y es sensible, trátalo como filtrado. |

## Qué se probó y qué no
Los comandos de esta guía se ejecutaron (09/11/2026) con **Git 2.43 en Linux**: configuración, `init`, `add`, `commit`, `switch -c`, `merge --no-ff`, un conflicto provocado y resuelto,
`merge --abort`, `restore`, `restore --staged`, `stash`, `amend`, `revert`, `reset --soft`, `diff`, `tag`, `push -u`, borrado de rama remota, `fetch`, `pull` y `switch` a una rama remota, contra un remoto local.
Contra GitHub se probó `git clone --branch develop` del repositorio del curso (clon completo) y, con repositorios locales, la receta de entrega con dos remotos (`remote rename`, `remote add`, `push -u`, `fetch curso`).
No se probó en Windows (Credential Manager, avisos de CRLF) ni un `push` a GitHub con autenticación. La receta de entrega es una propuesta que el instructor debe confirmar.
