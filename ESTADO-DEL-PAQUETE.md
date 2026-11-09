# Estado de la entrega

La S0 es una edición reconstruida con la organización Parte A / Parte B / consulta, y ajustada el 08/11/2026:
núcleo = ML clásico a producción; IA generativa y relacionado = opcional; Docker y Kubernetes en Codespaces;
orquestación con GitHub Actions. No es una copia visual exacta de los HTML exploratorios anteriores.

No incluye el PDF original ni las versiones anteriores alternativas.
Los scripts de instalación, datasets, notebooks, workflows, Codespace y laboratorios no están
implementados. Los comandos y guías incluidos no se presentan como un instalador.

La presentación principal (`slides/index.html`) se rehízo el 08/11/2026 (26 diapositivas; el 09/11/2026 pasó a 29, ver más abajo): diapositivas interactivas en un solo archivo
(HTML, CSS y JavaScript propios, sin librerías ni recursos externos) con animaciones, pasos progresivos, encuesta, mapa del curso,
capas animadas, temporizador de pausa y diagnóstico con informe de incidencias. Las imágenes están en `slides/media/`.
Funciona sin conexión.

Comprobado en Chromium (sin conexión): sin errores de consola, 22 interacciones probadas de forma automática, impresión a PDF
(26 páginas) y las 26 diapositivas revisadas con sus pasos revelados. Falta probarla en la plataforma de la clase (Google Meet),
en otros navegadores y en el proyector.

El 09/11/2026 se añadieron tres diapositivas a la Parte B para explicar, antes de los pasos de instalación, qué software se necesita en cada sesión y para qué:
la 15 (matriz herramienta × sesión, con «para qué sirve» y la guía de uso de cada una), la 16 (qué estrena cada sesión y qué debe estar listo antes) y la 18
(una guía de uso por herramienta). La Parte B sigue sumando 70 min. Comprobado en Chrome sin conexión: 29 diapositivas recorridas con →, sin errores de
consola ni peticiones externas, barra de tiempo con salto correcto e impresión a PDF de 29 páginas. Las comprobaciones de arriba (PDF de 26 páginas, 22 interacciones)
corresponden a la versión de 26 diapositivas. Las marcas de la matriz siguen `00-Planificacion/programa.md` y son orientativas; no se ha revisado la presentación en un proyector.

`slides/anexos/index.html` conserva la edición anterior (con React y ECharts, licencias en `slides/anexos/licencias/`) solo como
material de consulta: sus anexos A–F siguen vigentes; el resto está desactualizado.

La guía de instalación para Windows (`03-Entorno/guia-instalacion/`) se probó en Chromium (interacciones, copia, progreso y móvil). Los dos scripts
(`instalar_entorno.cmd` y `.ps1`) se probaron con un `winget` falso: PowerShell 7 en Linux (20 comprobaciones) y `cmd.exe` de Wine (26),
con las pruebas en `03-Entorno/scripts/pruebas/`. **Nunca se ejecutaron en Windows real** ni con `winget` real; esas pruebas encontraron
y corrigieron dos errores, pero no sustituyen una prueba en un equipo limpio.

El entorno `env-ia-mlops` (`03-Entorno/conda/environment.yml`) se creó con Miniconda real en Linux y pasó su prueba de humo (`HUMO OK`); para
Windows solo se comprobó que resuelve. Ver `03-Entorno/VALIDACION.md`.

Para dejar el equipo listo para S1 hay unas diapositivas de copiar y pegar (`01-Sesiones/S0-Presentacion-y-Entorno/slides/instalacion/`), una guía rápida en texto (`practica/guia-rapida-entorno-s0-s1.md`) y un verificador (`03-Entorno/conda/verificar_s1.py`). Los comandos de Python, conda, pytest, SQLite y MLflow se ejecutaron en Linux en un entorno creado desde cero y las diapositivas muestran esas salidas reales; **nada de eso se ejecutó en Windows real**. El detalle, los hallazgos (clonado de `develop`, resumen de `pytest`, `conda env update` frente a `pip`, aviso de `protobuf` sin resolver) y cómo repetirlo están en `03-Entorno/VALIDACION.md`.

Las cifras y tarifas externas (McKinsey, FinOps, Stack Overflow, Cloud Run) no se han reverificado
tras el ajuste: revisarlas antes de impartir. Las salidas de las demos de terminal son ilustrativas, no capturas reales.
