# Datos del caso de los alumnos

Copia de dos datasets del UCI Machine Learning Repository, ambos con licencia **CC BY 4.0** (leída en las fichas oficiales el 09/11/2026).

| Carpeta | Papel en el curso | Para qué |
|---|---|---|
| `bank-marketing/` | **El caso de los alumnos** (confirmado el 10/11/2026) | Lo desarrollan de S1 a S5: RAW → MASTER → FS → ML, modelo, API, GCP, workflow y operación |
| `default-credit-card/` | **Referencia para investigar por su cuenta** | Misma estructura de problema (clasificación binaria sobre datos tabulares) con otras trampas: encabezado doble, formato ancho, sin dimensión temporal |

## Qué contiene cada carpeta
**`bank-marketing/`** (Moro, Cortez y Rita; banco portugués, llamadas de venta de un depósito a plazo, mayo de 2008 a noviembre de 2010)
- `bank-additional-full.csv`: 41 188 filas, 20 variables más el objetivo `y`, separador `;`, **ordenado por fecha**. Es el único archivo que usa el caso.
- `bank-additional-names.txt`: la documentación original del autor. Léela entera: explica las variables y advierte de que `duration` no se conoce antes de llamar.

**`default-credit-card/`** (I-Cheng Yeh; clientes de tarjeta de crédito en Taiwán, abril a septiembre de 2005)
- `default_of_credit_card_clients.xls`: el original, 30 000 filas, **dos filas de encabezado** (códigos `X1..X23` y nombres `ID, LIMIT_BAL...`).
  Se renombró (el original se llama `default of credit card clients.xls`); el contenido es idéntico byte a byte.
- `default_of_credit_card_clients.csv`: **derivado** del anterior, con un único encabezado (el de nombres). No cambia ningún valor; `convertir_xls_a_csv.py` lo regenera.
  Hace falta `xlrd` para leer el `.xls`, y el entorno `env-ia-mlops` no lo trae: por eso se entrega el CSV.

No se incluyen `bank-additional.csv` (muestra del 10 % de lo anterior) ni la versión antigua `bank-full.csv`, para que nadie dude de qué archivo usar.

## Atribución (obligatoria por la licencia CC BY 4.0)
- Moro, S., Rita, P., & Cortez, P. (2014). *Bank Marketing* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5K306
  La documentación del autor pide además citar: S. Moro, P. Cortez y P. Rita, *A Data-Driven Approach to Predict the Success of Bank Telemarketing*, Decision Support Systems (2014), doi:10.1016/j.dss.2014.03.001.
- Yeh, I. (2009). *Default of Credit Card Clients* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C55S3H
- Licencia: https://creativecommons.org/licenses/by/4.0/
- Cambios hechos aquí: solo los descritos arriba para Default (renombrar el `.xls` y derivar el CSV). `bank-marketing/` es copia sin cambios.

## Verificar que tienes los archivos originales
`SHA256SUMS` fija la huella de cada archivo. Git está configurado (`.gitattributes`) para no modificar ni un byte de esta carpeta, así que la huella debe coincidir también en Windows.
```text
cd 02-Proyecto-Transversal/datos
sha256sum -c SHA256SUMS                                     # Linux, macOS, Git Bash, Codespaces
```
En PowerShell: `Get-FileHash -Algorithm SHA256 bank-marketing\bank-additional-full.csv` y compara con la línea de `SHA256SUMS`.
UCI no publica una huella oficial: estas son las de los archivos que descargó el instructor, y coinciden con los tamaños de las fichas.

## Antes de modelar (no son sugerencias)
- **No uses `duration`** como variable del modelo: es la duración de la llamada, que solo se conoce después de llamar.
- **No hay identificador de cliente** en Bank Marketing: la unidad es la llamada.
- No reordenes las filas de `bank-additional-full.csv`: el orden es la única información temporal fiable.
- Los números del perfilado están en `../verificacion-datos-tarea/`.
