# Guía de Codespaces para el alumnado

Diapositivas (y su versión en texto) sobre GitHub Codespaces: qué es, cómo abrirlo en el navegador o desde el VS Code de escritorio, qué se hace dentro en S2 (bloque 4 de la guía de laboratorio), cómo cuidar la cuota y qué hacer si algo falla. Escrita el 10/11/2026. Para practicar Docker dentro del Codespace antes de S2: [`contenedores/`](../../01-Sesiones/S2-API-y-Docker/contenedores/README.md).

| Archivo | Qué es |
|---|---|
| `index.html` | Las diapositivas (24). Se abre con doble clic; no necesita servidor. Botones de copiar por línea, «Copiar todo» (tecla C), «Marcar como hecho» (se guarda en el navegador) y listas de comprobación. |
| `../guias/codespaces-para-el-alumnado.md` | El mismo contenido en texto. |
| `../../pdfs/S2-API-y-Docker/01-presentaciones/02-guia-de-codespaces.pdf` | PDF de las diapositivas (una por página; sin botones). |
| `generar.py` | **Única fuente** del HTML y del Markdown. Para cambiar algo, edita este archivo y ejecuta `python generar.py`. Después, `python 00-Planificacion/pdfs/generar_pdfs.py --solo 02-guia-de-codespaces.pdf`. |
| `capturar.py` | Ejecuta el pipeline, la API y la comparación en Linux y guarda las salidas reales en `salidas-reales.json` (`python capturar.py --puerto 8080`, con el entorno `env-ia-mlops`). |
| `comprobar_diseno.py` | Abre las diapositivas en Chrome en tres tamaños y avisa de desbordes; prueba copiar, «Copiar todo», «Marcar como hecho», las listas y el teclado. |
| `pruebas/test_contenido.py` | 12 pruebas: los comandos coinciden con la guía de laboratorio, la configuración descrita coincide con el `devcontainer.json`, las salidas son las capturadas, no queda ninguna palabra interna, la guía no promete lo que no es nuestro y declara lo que no se ha probado, y lo generado está al día. |

## Qué está verificado y qué no
- **Verificado en un Codespace real del curso (12/11/2026, 2 núcleos, rama `develop`):** creación y conexión, `verificar.sh` sin fallos (Docker 29.9.3, kind v0.27.0, kubectl v1.37.2, Python 3.11.18), el bloque 4 entero, el panel Puertos con `/docs`, el diálogo de confianza, el modo recuperación y parar desde la web. Las **capturas** (`capturas/*.webp`, embebidas en `index.html`) y los **tiempos** (`salidas-codespace.json`) salen de esa prueba. La primera vez el Codespace arrancó en modo recuperación: los arreglos están en `.devcontainer/` (ver `03-Entorno/VALIDACION.md`, «Codespace del curso»).
- **Verificado en Linux y en GitHub Actions:** los comandos del bloque 4 y sus salidas en texto (`salidas-reales.json`).
- **Según la documentación de GitHub (consultada el 10/11/2026), sin probar:** cuotas, tiempos de inactividad y retención, Export changes to a branch y la conexión desde VS Code de escritorio con la extensión `GitHub.codespaces`. Cada diapositiva lo indica en su etiqueta.
- Las cuotas cambian: revisarlas antes de impartir.

## Capturas
`capturas/` tiene 17 recortes en WebP de las pantallas del Codespace de prueba (cuenta del instructor). Se embeben en `index.html` al generar y la versión en texto las enlaza. Una prueba comprueba que cada captura citada existe, está embebida y que no sobra ninguna.

## Antes de la clase
1. Con una cuenta de **estudiante**, abrir un Codespace de la rama `develop` y comprobar la región y la cuota (no se ha probado con esa cuenta).
2. Si algo difiere de la guía, corregir `generar.py` (y `.devcontainer/`) y regenerar.
3. Para S3: escribir y probar el laboratorio de Kubernetes con `kind` y `kubectl` (ya instalados) y ampliar la guía.

## Pruebas
```text
env-ia-mlops/bin/python -m pytest 03-Entorno/guia-codespaces/pruebas -q
python 03-Entorno/guia-codespaces/comprobar_diseno.py          # necesita playwright y Chrome
```
