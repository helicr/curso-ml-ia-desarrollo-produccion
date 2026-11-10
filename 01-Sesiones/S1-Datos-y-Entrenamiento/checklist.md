# Checklist S1

## Antes de la sesión (docente)
- [ ] Rama `develop` actualizada y proyecto base clonado en tu máquina.
- [ ] `conda activate env-ia-mlops` y `python -m pytest -q` en `04-Proyecto-Base`: **34 passed**.
- [ ] `slides/index.html` abre sin conexión; probar las diapositivas 5, 10, 13 y 17 (interactivas).
- [ ] Probar `mlflow ui` con el backend SQLite y verificar que se ven las ejecuciones.
- [ ] Confirmar la lista de quién no pasó la verificación de entorno en S0.

## Durante la sesión (alumnado)
- [ ] Entorno verificado (`prueba_de_humo.py` y `pytest` en verde).
- [ ] Cuaderno 01 ejecutado: conciliación `raw = master + descartes` cuadra y `master_calidad` sin reglas duras fallidas.
- [ ] Cuaderno 02 ejecutado: prueba de no-fuga en verde (`pytest tests -k futuro`).
- [ ] Cuaderno 03 ejecutado: tasa de recompra por partición revisada.
- [ ] Cuaderno 04 ejecutado: tres ejecuciones visibles en MLflow UI.
- [ ] Traducción a `.py` (`jupytext`) y `python -m ia_mlops.pipeline` ejecutados.
- [ ] Tarea entendida (variable nueva) y plantilla de evidencia descargada.

## Registro de incidencias
Paso / esperado / obtenido / mensaje / acción. Sin credenciales.
