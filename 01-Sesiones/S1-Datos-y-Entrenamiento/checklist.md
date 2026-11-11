# Checklist S1

## Antes de la sesión (docente)
- [ ] Rama `develop` actualizada y proyecto base clonado en tu máquina.
- [ ] `conda activate env-ia-mlops` y `python -m pytest -q` en `04-Proyecto-Base`: **123 passed** (completas). Las rápidas, `python -m pytest -q -m "not lento"` (las de la guía de laboratorio), dan **119 passed, 4 deselected**.
- [ ] `slides/index.html` abre sin conexión; probar las diapositivas 5, 10, 13 y 17 (interactivas).
- [ ] Probar `mlflow ui` con el backend SQLite y verificar que se ven las ejecuciones.
- [ ] Confirmar la lista de quién no pasó la verificación de entorno en S0.
- [ ] Crear el formulario de Google de entregas (nombre, avance o tarea de S1, enlace a la rama o carpeta comprimida, «qué no pude ejecutar») con la hoja de respuestas en hora de Lima, y tener el enlace listo para dar en S1.

## Durante la sesión (alumnado)
- [ ] Entorno verificado (`prueba_de_humo.py` y `pytest` en verde).
- [ ] Cuaderno 00 ejecutado: `retail.db` creada, claves foráneas sin errores y las 23 070 líneas reconstruidas.
- [ ] Cuaderno 01 ejecutado: conciliación `raw = master + descartes` cuadra y `master_calidad` sin reglas duras fallidas.
- [ ] Cuaderno 02 ejecutado: prueba de no-fuga en verde (`pytest tests -k futuro`).
- [ ] Cuaderno 03 ejecutado: tasa de recompra por partición revisada.
- [ ] Cuaderno 04 ejecutado: tres ejecuciones visibles en MLflow UI.
- [ ] Traducción a `.py` (`jupytext`) y `python -m ia_mlops.pipeline` ejecutados.
- [ ] Tarea entendida (variable nueva) y plantilla de evidencia descargada.
- [ ] Leída la hoja de mi caso propio ([Bank Marketing](../../02-Proyecto-Transversal/alumno/tu-caso-bank-marketing.md)) y comprobada la huella de mi copia del CSV. Es otro trabajo distinto de la tarea de arriba.

## Registro de incidencias
Paso / esperado / obtenido / mensaje / acción. Sin credenciales.
