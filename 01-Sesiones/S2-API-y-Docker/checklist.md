# Checklist S2

## Antes de la sesión (docente)
- [ ] Rama `develop` actualizada y proyecto base clonado en tu máquina.
- [ ] `conda activate env-ia-mlops` y, en `04-Proyecto-Base`, `python -m ia_mlops.pipeline` y `python -m pytest -q -m "not lento"`: **108 passed, 4 deselected**.
- [ ] `slides/index.html` abre sin conexión; probar las diapositivas 7, 8 (laboratorio de códigos), 11, 15, 17 y 18 (interactivas).
- [ ] **Probar el Codespace del curso** (el `.devcontainer` no se ha abierto nunca): crear uno desde `develop`, esperar a que termine la instalación y ejecutar `docker version`, `cd 04-Proyecto-Base`, `python -m ia_mlops.pipeline` y `docker build -f deploy/docker/Dockerfile -t retencion-api:local .`. Si falla, anotar el mensaje y preparar el plan B: el workflow construye la imagen.
- [ ] Preparar un repositorio personal de prueba y comprobar que `deploy/github-actions/ci.yml` copiado a `.github/workflows/` se ejecuta en verde (con `PROYECTO: "04-Proyecto-Base"` si es un clon del curso).
- [ ] Revisar la cuota gratuita de horas de Codespaces del grupo (pendiente de S0).
- [ ] Confirmar la lista de quién no pasó la verificación de entorno en S0 y quién tiene Codespace.
- [ ] Probar los diez casos de `tests/datos/casos/` con `curl` (la prueba `tests/test_casos_laboratorio.py` ya lo hace con `TestClient`).

## Durante la sesión (alumnado)
- [ ] Entorno verificado: pipeline ejecutado y `108 passed` en las pruebas rápidas; existe `models/modelo_mlflow/`.
- [ ] La API arranca y `/salud`, `/listo`, `/modelo` y `/predecir` responden; el ejemplo da `0.8278889…`.
- [ ] Los diez casos probados con el código esperado **apuntado antes**; se entiende por qué 08 y 09 dan 200 con advertencia.
- [ ] 503 sin modelo, 503 con el contrato roto y 503 con el esquema desactualizado vistos y entendidos; `git restore` hecho.
- [ ] Una petición seguida por el registro con su `X-Request-ID`.
- [ ] `comparar` ejecutado sin y con `--url`: todos los caminos coinciden.
- [ ] Una regla del esquema rota y la prueba que falla anotada.
- [ ] Imagen construida y contenedor probado en el Codespace (o plan B: CI), `id -u` = `10001`.
- [ ] Workflow ejecutado en GitHub (o entendido) y el paso «Probar el contenedor» leído.
- [ ] Tarea entendida (ruta A o B) y plantilla de evidencia descargada.

## Registro de incidencias
Paso / esperado / obtenido / mensaje / acción. Sin credenciales. Prestar especial atención a lo que falle con **Codespaces, Docker y Windows**: es lo que no se pudo probar al preparar la sesión.
