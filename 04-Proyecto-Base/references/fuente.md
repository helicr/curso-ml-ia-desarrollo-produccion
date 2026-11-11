# Fuente del dato

**Online Retail II** · UCI Machine Learning Repository
- Ficha oficial: https://archive.ics.uci.edu/dataset/502/online+retail+ii
- DOI: https://doi.org/10.24432/C5CG6D
- Autor: Daqing Chen. Donado el 20/09/2019.
- **Licencia: Creative Commons Attribution 4.0 (CC BY 4.0).** Permite compartir y adaptar para cualquier fin, citando la fuente. Verificada en la ficha oficial el 09/11/2026.
- Contenido: transacciones de una tienda online del Reino Unido, 01/12/2009 a 09/12/2011. **1 067 371 filas** en dos hojas de un Excel (≈ 45 MB).
- Huella sha256 del zip descargado: `572e36277c2390fbfde10664750731e0a86f55e33470d91919085f0408e67bfb`

Cita sugerida: Chen, D. (2012). *Online Retail II* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5CG6D

## Qué se incluye en este repositorio
- `data/raw/muestra_online_retail_ii.csv`: **muestra de 23 070 filas** (150 clientes elegidos al azar con semilla 42 y 300 líneas sin cliente), con las mismas columnas del original.
  Se redistribuye bajo CC BY 4.0, citando la fuente. Conserva la suciedad del original (cancelaciones, duplicados, códigos que no son productos, clientes nulos).
  Se regenera con `python -m ia_mlops.dataset muestra` (necesita el Excel completo descargado); la muestra regenerada tiene la misma huella sha256.
- A partir del archivo, el cuaderno `00_pipeline_operacional.ipynb` construye la base operacional simulada `data/external/retail.db`, que es la fuente del pipeline.
- El archivo original **no** se incluye: se descarga con `python -m ia_mlops.dataset descargar`, que verifica la huella.

## Suciedad real del dato (medida sobre el archivo completo)
| Hallazgo | Valor |
|---|---|
| `Invoice` mezcla números y texto (`C489449`) | 1 047 871 números · 19 500 textos |
| `StockCode` mezcla enteros y texto | 932 385 enteros · 134 986 textos |
| Duplicados exactos | 34 335 (3,2 %) |
| Líneas sin Customer ID | 22,76 % |
| Líneas con precio ≤ 0 | 6 019 |
| Códigos que no son productos | 61 |
| Líneas que son ventas válidas | 97,11 % de las que pasan a MASTER |

## Ética y privacidad
El dato no contiene nombres ni contacto: `Customer ID` es un número interno. Aun así, no se debe intentar reidentificar a los clientes.
