# Estado de la entrega

La S0 es una edición reconstruida con la organización Parte A / Parte B / consulta, y ajustada el 08/11/2026:
núcleo = ML clásico a producción; IA generativa y relacionado = opcional; Docker y Kubernetes en Codespaces;
orquestación con GitHub Actions. No es una copia visual exacta de los HTML exploratorios anteriores.

No incluye el PDF original ni las versiones anteriores alternativas.
S0 y S1 están completas (presentaciones, documentos, laboratorio, tarea, rúbrica, proyecto base y entorno) y validadas en Linux; nada se ha probado en Windows real.
S2–S5 solo tienen README; el Codespace del curso y los workflows de GitHub Actions no están implementados.
Los scripts `instalar_entorno.*` instalan programas con winget y nunca se ejecutaron en Windows real.

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

Cada sesión (`01-Sesiones/S0-...` a `S5-...`) tiene un `index.html` con sus presentaciones, sus documentos y lo que falta (presentación, guion, teoría, práctica, tarea…).
Se genera con `00-Planificacion/indices-de-sesion/generar_indices.py`: un archivo nuevo en la carpeta de una sesión aparece al volver a ejecutarlo, y las presentaciones de S0 y S1 llevan un enlace «⌂ Índice» de vuelta.
Comprobado en Chrome (6 índices en 4 tamaños, enlaces entre sesiones y regreso desde las tres presentaciones de clase) y con 68 pruebas automáticas en `00-Planificacion/indices-de-sesion/pruebas/`.
No se probó el modo «Esta carpeta» para abrir los `.md` (el navegador puede descargarlos en lugar de mostrarlos) ni en Windows real.

La institución exige PDF: `pdfs/` tiene los de S0 y S1 (19 archivos: 3 presentaciones, 15 documentos y el plan docente), organizados por sesión y por quién los usa
(presentaciones · alumno · instructor); `pdfs/LEEME.md` los lista. Se generan con `00-Planificacion/pdfs/generar_pdfs.py` (Chrome + pandoc) y los índices de
sesión los enlazan con un botón «PDF». Una página por diapositiva (1280 × 720) con marcadores, todos los pasos revelados, contadores en su valor final y las demos
de terminal con su salida de ejemplo; los documentos salen en A4 con pie «Página n de N». **Se pierden** las animaciones, los botones, los contadores en vivo y las
notas del orador; las piezas interactivas (encuesta, simuladores, cronómetro) quedan como imagen fija. Solo en el PDF se reescribieron las frases que mandan pulsar
botones que en papel no existen (lista en `RETOQUES_TEXTO`); las fuentes no cambian. La tipografía va incrustada como Type 3 (el texto se puede buscar y copiar,
pero `pdftoppm` avisa de «Bad bounding box»; no afecta a la lectura). Comprobado: 19 PDF abiertos y revisados a mano en hojas de contacto, `--comprobar` limpio
(tamaño, número de páginas = diapositivas, sin `file:///`, sin palabras internas) y 75 pruebas automáticas en `00-Planificacion/pdfs/pruebas/`. No se abrieron en
otros visores que Chrome y poppler (no en Acrobat ni en el visor de Windows) y no se ha comprobado la impresión en papel. Excluidos a propósito: la guía interactiva
de Windows (`03-Entorno/guia-instalacion/`, ya cubierta por «Preparación paso a paso» y «Tu equipo listo para S1»), los anexos antiguos y `verificar_s1.py`.

Las cifras y tarifas externas (McKinsey, FinOps, Stack Overflow, Cloud Run) no se han reverificado
tras el ajuste: revisarlas antes de impartir. Las salidas de las demos de terminal son ilustrativas, no capturas reales.
