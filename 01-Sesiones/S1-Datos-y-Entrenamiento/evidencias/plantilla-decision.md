# Evidencia S1 · decisión sobre la variable nueva

**Nombre:** …  **Fecha:** …  **Rama / carpeta:** …

## 1. La variable
- Nombre: `…`
- Fórmula (solo con datos anteriores al corte): …
- Por qué podría ayudar a predecir la compra en 90 días: …

## 2. Dónde la implementé
Archivos modificados: …

## 3. Pruebas
```
(pega aquí la salida de:  python -m pytest -q  y  python -m pytest tests -k futuro -q)
```

## 4. Comparación en MLflow
| | Sin la variable | Con la variable |
|---|---|---|
| Ejecución | … | … |
| `huella_datos` | … | … (¿cambió?) |
| AUC valid | … | … |
| AUC test | … | … |
| Precisión media test | … | … |

## 5. Decisión
¿La variable se queda? **Sí / No**
Razones (métricas, estabilidad, costo de mantenerla, riesgo de fuga): …

## 6. Límites y riesgos
Qué no pude comprobar, qué podría fallar en producción, qué haría con más tiempo: …

## 7. Dificultades
Error exacto y cómo lo resolví (o por qué no): …

## 8. Reproducir
Comandos, en orden: …

## 9. Ayuda recibida
Personas o herramientas: …
