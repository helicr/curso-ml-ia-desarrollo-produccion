# S0: Presentación y entorno

Duración: 2 horas (25 min Parte A, 15 min pausa, 70 min Parte B, 10 min cierre).

## Contenido
Parte A: objetivos, recorrido, caso y entregas. Parte B: Git, VS Code, Miniconda, SQLite, repositorio,
Docker y Kubernetes en Codespaces (sin instalación local), Google Cloud y diagnóstico.
Red neuronal y LLM: ruta opcional, sin instalar nada en S0.

## Tarea
Completar preparación y leer el caso.

## Evidencia
Entorno comprobado antes de S1.

## Materiales
- `index.html`: índice de la sesión (presentaciones, documentos y qué falta). Se genera con `00-Planificacion/indices-de-sesion/generar_indices.py`.
- `slides/index.html`: presentación interactiva (29 diapositivas, un solo archivo sin dependencias externas; imágenes en `slides/media/`).
  Teclas: → avanzar, ← retroceder, O índice, S notas, F pantalla completa. Se imprime a PDF con una diapositiva por página.
- `slides/anexos/index.html`: material de la edición anterior (anexos A–F de consulta).
- PDF de las presentaciones y de los documentos (los exige la institución): `pdfs/S0-Presentacion-y-Entorno/` en la raíz del repositorio; ver `pdfs/LEEME.md` (qué se pierde respecto a la versión HTML).
- `guion.md`: guion con tiempos por diapositiva.
- `checklist.md`: diagnóstico de 12 comprobaciones.
- Instalación previa (solo Windows): `03-Entorno/guia-instalacion/index.html` y `03-Entorno/scripts/instalar_entorno.ps1`.
- Equipo listo para S1, para copiar y pegar: `slides/instalacion/index.html` (27 diapositivas: instalación en orden, entorno desde `environment.yml`, pruebas y verificador, con las salidas reales) y su versión en texto `practica/guia-rapida-entorno-s0-s1.md`. Se generan desde `slides/instalacion/contenido.py` con `generar.py`; `capturar.py` renueva las salidas reales y `comprobar_diseno.py` revisa el diseño.

Laboratorio y materiales completos de las demás sesiones: pendientes de implementación y validación.
