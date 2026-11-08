# Proyecto base: estructura propuesta

Raw: archivos originales en data/raw.
Master, fs y ml: tablas SQLite con prefijos.
Artefactos fuera de SQLite: modelo, preprocesamiento, métricas y metadatos.
La API carga artefactos; no reconstruye el pipeline completo en cada predicción.
Los workflows de GitHub Actions irán en `.github/workflows/` (raíz del repositorio).
Implementación pendiente; directorios vacíos deliberados.
