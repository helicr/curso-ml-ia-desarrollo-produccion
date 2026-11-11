# Guion del docente · S1 (240 min)

**Presentación:** `01-Sesiones/S1-Datos-y-Entrenamiento/slides/index.html`

Las diapositivas tienen notas del ponente (tecla **S**). Este guion añade el ritmo y qué comprobar.

## 0:00–0:30 · Revisión de entorno (diap. 1–3)
- Abrir, comprobar audio. Mostrar agenda (diap. 2) en 1 minuto.
- Diap. 3: cada persona ejecuta `conda activate env-ia-mlops`, `python ../03-Entorno/conda/prueba_de_humo.py` y `python -m pytest -q` dentro de `04-Proyecto-Base`. Esperado: `44 passed`.
- Anotar quién no pasa y el mensaje de error (checklist). Quien falle: Codespaces o pareja. **No se detiene la sesión.**
- Si pasan los 30 min y hay más de un tercio sin entorno: recortar teoría (diap. 11 y 16), no práctica.

## 0:30–1:30 · Teoría (diap. 4–16)
| Min | Diap. | Mensaje clave | Pregunta a la audiencia |
|---|---|---|---|
| 3 | 4 | Una pregunta de negocio, no de estadística. | ¿Quién decide a quién se le escribe? |
| 6 | 5 | El operacional (la fuente, solo se lee) y cuatro capas, cada una regenerable. Clic en cada capa. | ¿Por qué FS va antes que ML? |
| 4 | 6 | El dato real viene sucio; los contadores justifican MASTER. | ¿Cuál de estos problemas rompería un promedio? |
| 4 | 7 | RAW copia el sistema operacional (`retail.db`); el linaje (`linea_id`, `_carga_id`) permite volver a la línea de origen. | ¿Qué pasa si limpiamos sobre RAW? |
| 4 | 8 | Nada se pierde: 1 033 036 + 34 335 = 1 067 371. | ¿Qué haría el pipeline si no cuadra? |
| 3 | 9 | Reglas duras, alertas e informativas. | ¿Una alerta detiene el pipeline? |
| 8 | 10 | **Regla de oro.** Mover el deslizador y ver qué se usa. | ¿Dónde estaría la fuga si usáramos la factura roja? |
| 3 | 11 | 13 variables, 5 familias, documentadas. | ¿Qué variable añadirías? |
| 6 | 12 | Objetivo hacia el futuro, partición temporal. Mostrar 48→35→38 %. | ¿Por qué baja la tasa? |
| 5 | 13 | **Honestidad:** aquí la aleatoria dio *menos* AUC. La razón para la temporal es el uso real. | ¿Qué otra razón hay? |
| 5 | 14 | Referencia, sobreajuste (0,842 en train vs 0,781 en test). | ¿Qué modelo desplegarías y por qué? |
| 5 | 15 | MLflow: parámetros, métricas, firma, huella. | ¿Cómo sabes que dos ejecuciones son comparables? |
| 4 | 16 | Cuaderno = fuente; paquete = traducción; prueba de equivalencia. | ¿Qué demuestra que la traducción es fiel? |

## 1:30–3:45 · Práctica (diap. 17 → `practica/guia-laboratorio.md`)
Ritmo: 10 preparar · 30 cuaderno 01 · 25 cuaderno 02 · **10 pausa** · 25 cuaderno 03 · 25 cuaderno 04 · 10 `.py` y pruebas.
- Recorrer el chat/pantallas a los 15 min de cada bloque.
- Quien termine antes: empezar la tarea (variable nueva).

## 3:45–4:00 · Entrega y cierre (diap. 18–20)
- Tarea y rúbrica (diap. 18), errores frecuentes (19), avance de S2 (20).
- Recordar los **dos entregables**: (1) la tarea de la variable nueva, sobre Online Retail II; (2) el **avance en S2** sobre su caso, Bank Marketing: RAW → MASTER → FS → ML, entrenamiento y métricas, como cuadernos (ver `02-Proyecto-Transversal/enunciado/README.md`). Recordar: `duration` se excluye y las filas de `bank-additional-full.csv` no se reordenan.
- Recordar: evidencia = decisión escrita + comparación de dos ejecuciones + traducción a `.py`.

## Si algo falla en directo
| Síntoma | Respuesta |
|---|---|
| El cuaderno 02 falla | Falta el 01: ejecutar desde el 01 (`Run All`). |
| Kernel sin paquetes | Seleccionar `env-ia-mlops` (esquina superior derecha). |
| MLflow UI no abre | `mlflow ui --backend-store-uri sqlite:///models/mlflow.db` desde `04-Proyecto-Base`. |
| Números distintos a la diapositiva | Esperado: la muestra da valores menores que el dato completo. |
