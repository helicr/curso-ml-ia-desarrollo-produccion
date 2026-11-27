# Modelos

Los cuadernos 02, 03 y 06 escriben aquí los pesos.

## v1 (cuadernos 02 y 03)

- `mnist_profesor.pt`, `mnist_estudiante_duro.pt`, `mnist_estudiante_destilado.pt`: caben en una copia ligera del material (< 1 MB cada uno).
- `sentimiento_logits_profesor.pt`: logits precomputados del profesor de SST-2 sobre el subconjunto pequeño de la v1.
- `sentimiento_estudiante_duro.pt` y `sentimiento_estudiante_destilado.pt`: unos 7,6 MB cada uno. Si no están en esta carpeta, se regeneran ejecutando `notebooks/03-destilacion-bert-sentimiento.ipynb`. Las métricas del cuaderno 04 están en `resultados/sentimiento.json` y no necesitan esos pesos.

## v2 (cuaderno 06)

- `v2_sentimiento_logits_profesor.pt`: logits del profesor sobre 20 000 frases de entrenamiento y el test de SST-2 (alrededor de 1,6 MB). Conviene dejarlo: evita recomputar al profesor (~3 min en CPU).
- `v2_estudiante_duro.pt` y `v2_estudiante_destilado.pt`: pesos de TinyBERT afinado (decenas de MB). Una copia ligera del material puede omitirlos; el cuaderno 06 los vuelve a generar. Las métricas del cuaderno 07 están en `resultados/v2_sentimiento.json`.
