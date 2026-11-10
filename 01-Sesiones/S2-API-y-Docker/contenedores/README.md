# Contenedores: material de autoestudio antes de S2

Paquete para que el alumnado entienda imagen, contenedor, puertos, volúmenes, Dockerfile y qué hace falta para producción **antes** de la sesión S2, trabajando en su Codespace. Todo parte de una sola fuente de comandos y de salidas reales de Docker.

## Qué hay

| Archivo | Para qué | Quién lo usa |
|---|---|---|
| `modelo-mental/index.html` | Presentación «Contenedores: el modelo mental» (16 diapositivas, cuatro prácticas) | Alumnado, antes de S2 |
| `del-dockerfile-a-produccion/index.html` | Presentación «Del Dockerfile a producción» (17 diapositivas, cinco prácticas) | Alumnado, después de la anterior |
| `guia-practica.md` | Nueve ejemplos sueltos para hacer en el Codespace, con la salida real de cada comando | Alumnado |
| `laboratorio-romper.md` | Cinco fallos que se provocan, se diagnostican y se arreglan | Alumnado |
| `ejemplos/` | Archivos que usan los ejemplos (Dockerfile, `.dockerignore`, `app.py`…) | Los ejemplos |

Tiempos estimados, **sin cronometrar con alumnado**: unos 60 min los ejemplos 1 a 6 (mínimo), unos 97 min los nueve y unos 34 min el laboratorio.

Los PDF de las dos presentaciones, de la guía y del laboratorio están en `pdfs/S2-API-y-Docker/`.

## Qué se probó y qué no

- **Probado con Docker real:** los 113 pasos de los nueve ejemplos y de las cinco roturas se ejecutaron en GitHub Actions (Docker 29.4.2, Ubuntu 26.04.1 LTS, 10/11/2026) y cada paso comprobó su código de salida y lo que la salida debe contener. Las salidas que se ven en las diapositivas y en los textos son esas, con los identificadores largos abreviados.
- **Sin probar:** nada de esto se ha ejecutado todavía **en un Codespace del curso**. La versión de Docker, las columnas de `docker image ls`, los tiempos y los identificadores pueden diferir. Está dicho en la portada de las presentaciones y en los dos documentos.
- **Cloud Run:** lo que dicen las diapositivas sobre escuchar en `0.0.0.0` y el puerto, la memoria y el sistema de archivos sale solo de la [documentación de Google](https://docs.cloud.google.com/run/docs/container-contract) (consultada el 10/11/2026) y está marcado «Documentación · sin probar aquí». No se ha desplegado nada; en S3 se comprueba de verdad.
- **Los tiempos de construcción** (por ejemplo, 8,0 s frente a 1,2 s en el ejemplo de la caché) son los de esa ejecución y dependen de la red y de la máquina.

## Cómo está hecho

```
ejemplos.py ──► ejecutar.py ──► salidas-reales.json ─┐
   (comandos)     (Docker real)    (lo que salió)      ├─► generar.py ──► guía, laboratorio y las dos presentaciones
                                                       ┘
```

- `ejemplos.py` es la **única fuente** de los comandos. Cada paso declara su código de salida esperado y lo que su salida debe contener o no.
- `ejecutar.py` ejecuta cada ejemplo con Docker en una copia temporal de su carpeta y escribe `salidas-reales.json`. Termina con error si algún paso no cumple lo declarado, pero antes escribe el JSON para poder ver qué pasó.
- `datos.py` comprueba al cargar que los comandos de `ejemplos.py` y los del JSON coinciden; si no, se niega a generar nada.
- `textos.py` (guía y laboratorio), `deck_a.py` y `deck_b.py` (presentaciones), `marco.py` y `diapos.py` (estructura y estilo de las diapositivas, reutilizando el de `03-Entorno/guia-codespaces/`) escriben los archivos.

Las salidas se normalizan al guardarlas (identificadores de 12 caracteres, marcas de tiempo, colores ANSI) con las reglas `norm` de cada paso, y otra vez al mostrarlas.

## Cómo regenerar

```bash
# 1. Si cambias un comando o un archivo de ejemplos/: ejecútalos con Docker (en un Codespace o cualquier Linux con Docker)
python3 ejecutar.py                       # todo; o --solo e3,e5,r2
python3 ejecutar.py --salida salidas-codespace.json   # para comparar con las del curso sin sobrescribirlas

# 2. Genera los archivos
python3 generar.py                        # escribe
python3 generar.py --comprobar            # no escribe; sale con 1 si algo no está al día

# 3. Comprueba
python3 -m pytest 01-Sesiones/S2-API-y-Docker/contenedores/pruebas -q
python3 comprobar_diseno.py               # en un navegador real, a tres tamaños (necesita Playwright y Chrome)

# 4. Si cambia el texto de las presentaciones o de los documentos, regenera los PDF
python3 00-Planificacion/pdfs/generar_pdfs.py --sesion S2
```

`ejecutar.py` necesita Docker y acceso a Docker Hub (las imágenes base salen de `python:3.11-slim`). Las salidas guardadas se obtuvieron en un workflow temporal de GitHub Actions, porque el entorno donde se preparó el material no llega a Docker Hub; ese workflow no forma parte del curso.

**Ejecutarlo en un Codespace de verdad quita la etiqueta «sin probar en un Codespace»:** si `salidas-codespace.json` coincide con `salidas-reales.json` (salvo versión, tiempos e identificadores), el cambio de redacción es solo esa frase.

## Qué comprueban las pruebas

`pruebas/test_contenedores.py` (28 pruebas) no necesita Internet ni Docker. Comprueba que los nueve ejemplos y las cinco roturas tienen sus pasos ejecutados y cumplen lo que cada uno esperaba, que las salidas guardadas no llevan datos que cambian en cada ejecución, que los archivos generados están al día, que cada comando y cada salida mostrada vienen de `ejemplos.py` y del JSON, que el laboratorio esconde el arreglo en un desplegable, que los minutos declarados son la suma de los ejemplos, que las presentaciones tienen las diapositivas y los `data-id` esperados, que su enlace de vuelta al índice y sus enlaces relativos resuelven, que dicen lo que no se ha probado, que sobre la nube solo afirman lo que dice la documentación consultada y que las citas del `Dockerfile` y del `.dockerignore` del curso son reales.
