# Verificación de los datos de la tarea (09/11/2026)

Scripts y salidas con los que se perfilaron los dos datasets de la tarea (*Default of Credit Card Clients* y *Bank Marketing*, de UCI) y se entrenó un
**modelo base rápido**. Sirven para reproducir las cifras de `../enunciado/README.md`. **No son la base de referencia de la tarea**: no hay capas RAW → ML, cuadernos ni pruebas.

## Procedencia
Los archivos los descargó el instructor desde las fichas de UCI y los adjuntó a la sesión el 09/11/2026. Desde el entorno de trabajo no se pudieron descargar (el proxy bloquea `archive.ics.uci.edu`).
Los tamaños coinciden con los que anuncian las fichas (5,3 MB el `.xls`; 434,2 KB `bank-additional.zip`; 565,5 KB `bank.zip`), pero UCI no publica un hash, así que `sha256.txt` solo fija **qué archivos se usaron**, no que sean los originales.
**Los datos no están en el repositorio** (decisión pendiente, ver `00-Planificacion/decisiones-y-pendientes.md`, punto 15). `bank-additional.zip` trae basura de macOS (`__MACOSX`, `.DS_Store`) y un `.Rhistory`; `bank.zip` está limpio. La ingesta debe ignorar esos archivos.

## Cómo reproducir
1. Descomprimir cada zip **en su propia carpeta**. El zip de Bank Marketing contiene a su vez `bank.zip` y `bank-additional.zip`, que también se descomprimen, cada uno en su carpeta.
2. Ejecutar desde fuera de esas carpetas (hace falta `xlrd` para el `.xls`; **`env-ia-mlops` no lo trae**):

```
uv run --no-project --with pandas --with xlrd python -I perfil_default.py "<ruta>/default of credit card clients.xls"
uv run --no-project --with pandas python -I perfil_bank.py "<ruta>/bank-additional-full.csv" "<ruta>/bank-full.csv"
uv run --no-project --with pandas --with xlrd --with scikit-learn python -I modelo_base_tarea.py "<ruta>/default of credit card clients.xls" "<ruta>/bank-additional-full.csv"
```

Las salidas guardadas están en `salidas/`. Se ejecutaron dos veces con `uv` (09/11/2026) y las tres salidas fueron idénticas byte a byte. No se fijaron versiones de pandas, scikit-learn ni xlrd, así que otras versiones pueden variar en los decimales del modelo.

## Límites
- Una sola partición y una sola semilla (0); los modelos no están afinados. Son una referencia de orden de magnitud, no un resultado que los alumnos deban reproducir.
- El año de cada fila de Bank Marketing se **infirió** a partir del cambio de mes (el archivo no trae año).
