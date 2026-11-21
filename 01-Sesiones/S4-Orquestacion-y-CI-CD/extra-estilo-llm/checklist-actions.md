# Checklist de GitHub Actions del extra de estilo LLM

Workflow: `.github/workflows/extra-estilo-llm.yml`

## 1. La víspera (profesor)

- [ ] El workflow está en `.github/workflows/extra-estilo-llm.yml` (ruta exacta, con las barras y el punto inicial; no en la raíz del repositorio).
- [ ] La rama del ensayo empieza por `lab/` (el disparador es `lab/**`), o el run se lanza con «Run workflow» (`workflow_dispatch`).
- [ ] «Run workflow» solo aparece si el archivo está en la rama principal del repositorio; si no aparece, usar el disparador por rama `lab/**`.
- [ ] Hay un run de prueba en verde y su enlace está guardado como respaldo.
- [ ] Actions está activado en el repositorio.
- [ ] El YAML se copia con el botón Raw; no se teclea a mano (la sangría se rompe).

## 2. Al empezar la clase

- [ ] La pestaña Actions muestra el workflow del extra.
- [ ] El run verde de respaldo está abierto en otra pestaña.

## 3. Para cada alumno

- [ ] El fork está hecho.
- [ ] En el fork, Actions está activado: entrar en la pestaña Actions y activarlo con el botón que ofrece GitHub allí (en los forks puede venir desactivado).
- [ ] El archivo está en `.github/workflows/` con el nombre `extra-estilo-llm.yml`.
- [ ] La rama tiene el nombre correcto (empieza por `lab/`).
- [ ] Se hace un push nuevo después de activar Actions.

## 4. Si no aparece en Actions (diagnóstico)

- [ ] ¿Está el archivo en `.github/workflows/extra-estilo-llm.yml` (ruta exacta)?
- [ ] ¿El nombre de la rama empieza por `lab/`, como pide el disparador `lab/**`?
- [ ] ¿Actions está activado en el fork?
- [ ] ¿El YAML es válido? GitHub muestra el error de sintaxis.

## 5. Si falla un job

- [ ] Leer el paso en rojo: ahí está el error.
- [ ] Los jobs siguientes salen «skipped» (omitidos): no tienen nada que leer.
- [ ] El respaldo es el run verde del profesor.

---

Estas comprobaciones salen de lo que falló en la sesión del 20/11/2026.
