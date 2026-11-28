# Cierre de `develop` y paso a `main` · estado a 28/11/2026

Revisión hecha el 28/11/2026 sobre `develop` = `11cb2b8` y `main` = `6f33465`. Es una lista de comprobación: lo marcado **[hecho]** está hecho; el resto, pendiente o por decidir.

## 1. Estado de la fusión (comprobado, sin ejecutarla)
- `develop` lleva **26 commits** que `main` no tiene; `main` lleva 9 **fusiones previas** de `develop` (sin contenido propio).
- Cambio de `main` a `develop`: **844 archivos, +125 608 / −170 líneas** (S5: 321, S4: 182, S3: 89, proyecto base `ia_mlops`: 34, S2: 31…).
- Simulación de la fusión (`git merge-tree`): **0 conflictos**.
- `main` hoy solo tiene los workflows `validar-codespace.yml` y `validar-windows.yml`; la fusión añade `validar-dos-contenedores.yml` (se dispara con *push* a `develop`, así que en `main` no corre solo).

## 2. Pruebas (26 carpetas, sin la suite grande)
- **22 en verde.** Cuatro carpetas con fallos:
  1. `00-Planificacion/pdfs`: falta `pypdf` en el entorno (los PDF se generan al final de la última sesión).
  2. `S1/slides/caso-propio`: «la presentación está al día» (**ya fallaba antes**; desfasada).
  3. `S4/laboratorio-cloud-journey`: `desplegar-gcp.yml` con CRLF **en el árbol de trabajo de Windows** (`core.autocrlf=true`); el archivo en el repositorio es LF. No afecta a GitHub.
  4. `S5/extra-vertex-champion`: una prueba que miraba el texto del Dockerfile antiguo **[hecho: arreglada el 28/11]**.
- **No ejecutadas** (a propósito): la suite de `04-Proyecto-Base/tests` (≈ 13 min, consume memoria) y `extra-mcp-notebooks/ui/pruebas` (toca el registro de MLflow y lo restaura). **Pásalas antes de fusionar.**

## 3. Limpieza antes de que sea la rama «de cara al alumnado»
- [ ] **Identificador de facturación** de la cuenta del curso (`010A93-…`) escrito en `preparar-gcp-s4.sh` y `borrar-gcp-s4.sh`. Propuesta: valor por defecto genérico (`TU-ID-DE-FACTURACION`) o variable de entorno. **Decisión tuya** (cambia lo que tecleas en el laboratorio).
- [ ] **Historial con el proxy corporativo** (`proxysscc…`): ya no está en `HEAD` **[hecho]**, pero sigue en el commit `1a1d0b2`. Quitarlo exige reescribir historia (`force push`): **decisión tuya**.
- [ ] **Correo de la cuenta del curso** (`cursomlops@gmail.com`) en `00-Planificacion/classroom/` y `validar-antes-de-subir.md`; **rutas locales** (`C:\bk\…`) en notebooks del proyecto base y en informes de `00-Planificacion/*/_pico`. Decidir si `00-Planificacion` (notas internas del profesor) viaja a `main` o se queda en `develop`.
- [ ] **Identificadores de la cuenta del curso** (proyecto `project-curso-ml-ia`, nº de proyecto, proveedor WIF) en las guías de Google Cloud: son los valores del profesor para el laboratorio; no son secretos, pero conviene decidir si se publican.
- [ ] **`04-Proyecto-Base/comparar_fs.py`**: sin versionar; borrar.

## 4. Contenido que falta o está a medias
- [ ] **Presentaciones** de los extras de **destilación** y **RAG** (tienen README y notebooks ejecutados en CPU, sin diapositivas).
- [ ] **Deck de teoría de S5** (hoy: `teoria/README.md` y las primeras diapositivas del laboratorio A).
- [ ] **PDF de S3, S4 y S5** (al final de la última sesión; instalar `pypdf`).
- [ ] **Capturas pendientes** de Composer (11) y Vertex (13), con su receta en `capturas-pendientes.md`.
- [ ] **READMEs desfasados:** el de la raíz y los de S0, S3 y S4 ya están al día **[hecho el 27/11]**; revisa S1 y S2.
- [ ] `07-Recursos`: guías que citan la rama `develop` (ver el punto 6).

## 5. Ensayos reales que siguen sin hacerse (no se presentan como probados)
- [ ] Build de los Dockerfiles nuevos en `puntuar-lote`, `nueva-version`, `desplegar-gcp`, los workflows del agente y `ci.yml` (**«Validar API e interfaz en dos contenedores» sí pasó en verde**, run 46003093657).
- [ ] Airflow/Composer y Vertex con recursos reales (cuestan; con tu OK y borrado inmediato).
- [ ] Notebooks MCP, destilación y RAG en un **Codespace**; interfaz web con BigQuery real y con un LLM mayor.
- [ ] `preparar-gcp-s4.sh` en una cuenta con el *pool* de WIF borrado (el arreglo no se ha vuelto a ejecutar).

## 6. Decisiones del profesor (abiertas)
1. **Canal de entrega:** Classroom o formulario de Google (las tareas dicen «formulario»; el recap, «Classroom»).
2. **Hora de la entrega final** (11/12/2026): las 10:00 (Perú) no están confirmadas.
3. **Rama del avance 2:** `tarea-s2` o `avance-2`.
4. **Pesos de las rúbricas** de S4 y S5 y la **rúbrica de la entrega final**.
5. **Demostración final:** vídeo o en vivo.
6. **Recorte de Google Cloud en S4** (4 h) y **Airflow 2 o 3** para el laboratorio local de Composer.
7. **Qué rama usa el alumnado:** hoy las guías mandan clonar/cambiar a `develop` (≈ 90 referencias en 44 archivos). Al fusionar, la rama por defecto de un *fork* pasa a tener todo el material: se podría **simplificar a `main`** (y desaparecen «Copy the main branch only» y el botón «Run workflow» ausente), o mantener `develop`. Es una pasada de documentación.

## 7. Orden propuesto para pasar a `main`
1. Cerrar los puntos de la sección 3 que decidas y pasar la suite grande (`04-Proyecto-Base/tests`) y la de la interfaz.
2. Regenerar índices (`python 00-Planificacion/indices-de-sesion/generar_indices.py`) y comprobar los 69 tests de índices.
3. Fusionar `develop` en `main` con **commit de fusión** (como las anteriores: «Fusiona develop en main: …»), sin reescribir historia.
4. Comprobar en GitHub que los workflows de `main` (`validar-codespace`, `validar-windows`) siguen en verde.
5. Decidir el punto 7 de la sección 6 y, si procede, hacer la pasada de documentación (`develop` → `main`) y volver a fusionar.
6. Opcional: una **etiqueta** (`git tag`) en la fusión como foto del curso entregado.

Respaldo: las ramas `lab/*` y `referencia*` borradas el 27/11 están en `C:\bk\HC-Cursos\respaldo-ramas-lab-27-11-2026.bundle` (fuera del repositorio).
