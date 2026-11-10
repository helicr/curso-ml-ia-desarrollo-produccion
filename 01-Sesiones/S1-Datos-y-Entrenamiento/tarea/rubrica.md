# Rúbrica de la tarea S1 (100 puntos)

| Criterio | Peso | Qué se observa |
|---|---|---|
| **Reproducibilidad** | 20 | Otra persona clona, ejecuta los comandos indicados y obtiene tus resultados. Pasos documentados, versiones, semilla. |
| **Técnica** | 40 | Variable sin fuga (prueba `-k futuro` en verde); catálogo actualizado; ML reconstruido; traducción a `.py` y prueba de equivalencia; dos ejecuciones en MLflow comparables. |
| **Análisis y decisión** | 40 | Comparación honesta (huella del dato, métricas valid y test), decisión argumentada, límites y riesgos reconocidos. |

## Niveles por criterio
| Nivel | Reproducibilidad (20) | Técnica (40) | Análisis (40) |
|---|---|---|---|
| Sobresaliente | 18–20 · un tercero reproduce sin ayuda | 36–40 · todo en verde y justificado | 36–40 · decisión clara, riesgos y alternativas |
| Logrado | 14–17 | 28–35 | 28–35 |
| En proceso | 8–13 · faltan pasos o versiones | 16–27 · fuga no probada o sin traducción | 16–27 · métricas sin interpretar |
| Insuficiente | 0–7 | 0–15 | 0–15 |

## Descuentos y alertas
- Variable que usa datos posteriores al corte: la técnica no supera 15 aunque mejore la métrica.
- Comparar ejecuciones con huellas de datos distintas sin decirlo: el análisis no supera 20.
- Presentar solo capturas, sin código ni pruebas ejecutables: la reproducibilidad no supera 8.
