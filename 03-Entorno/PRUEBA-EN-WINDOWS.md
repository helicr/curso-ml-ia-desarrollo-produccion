# Protocolo de prueba en Windows

Objetivo: validar en un Windows real lo que hasta ahora solo se probó en Linux. Duración aproximada: 30–45 minutos en un equipo limpio
(una máquina virtual de Windows 10 u 11 sirve).

## Opción A · Automática (recomendada): GitHub Actions
1. Sube el repositorio con `.github/workflows/validar-windows.yml`.
2. En GitHub: pestaña **Actions** → **Validar entorno en Windows** → **Run workflow**. Marca «probar instalación» si quieres probar los scripts instalando.
3. Revisa cada paso (verde o rojo) en `windows-2022` y `windows-latest`, y descarga el artefacto `verificacion-entorno-…`.
4. Anota el resultado en la tabla de abajo y actualiza `03-Entorno/VALIDACION.md`.
Limitaciones: el runner es un Windows Server, no un Windows de escritorio; puede no traer winget; no prueba VS Code, DB Browser ni gcloud de forma interactiva.

## Opción B · Manual en un equipo limpio
Sigue `03-Entorno/guia-instalacion/index.html` paso a paso, una vez por terminal (CMD y PowerShell), y marca el resultado.

| # | Paso de la guía | Resultado esperado | ✔ / ✘ | Observaciones y mensaje de error |
|---|---|---|---|---|
| 1 | `winget --version` | un número de versión | | |
| 2 | Script CMD: instalar | `[instalando]` por programa y luego informe | | |
| 3 | Script CMD: verificar (terminal nueva) | todo `[OK]` | | |
| 4 | Script PowerShell: instalar | igual | | |
| 5 | Script PowerShell: verificar | todo `[OK]` | | |
| 6 | `git --version` | `git version 2.x.windows.1` | | |
| 7 | `code --version` | versión y hash | | |
| 8 | `code --list-extensions` | las 7 extensiones | | |
| 9 | `conda --version` (Anaconda Prompt) | `conda 2x.x.x` | | |
| 10 | Receta de términos de servicio (4 comandos) | sin errores | | |
| 11 | `conda env create -f 03-Entorno\conda\environment.yml` | termina con el mensaje de activación | | |
| 12 | `python 03-Entorno\conda\prueba_de_humo.py` | `HUMO OK` | | |
| 13 | Abrir `prueba_notebook.ipynb` en VS Code con el kernel `env-ia-mlops` | `NOTEBOOK OK` | | |
| 14 | DB Browser: `SELECT 1 AS entorno_listo;` | una fila con 1 | | |
| 15 | `gcloud --version` y `gcloud auth login` | versión y cuenta activa en `gcloud auth list` | | |
| 16 | `git clone` del repositorio | carpeta creada | | |

Equipo usado (Windows 10/11, edición, ¿administrador?, ¿red corporativa?): ________________
Fecha y quién probó: ________________

## Qué hacer con el resultado
- Si todo pasa: cambiar las etiquetas «Sin probar» de la guía a «Probado en Windows» y actualizar `VALIDACION.md`.
- Si algo falla: copiar el mensaje completo y corregir el comando o el script; los dos scripts tienen pruebas en `03-Entorno/scripts/pruebas/`.
