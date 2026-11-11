# S1 · De los datos al modelo (4 horas)

Caso transversal: **Online Retail II** → *¿volverá este cliente a comprar en los próximos 90 días?*
Proyecto de trabajo: [`04-Proyecto-Base/`](../../04-Proyecto-Base/README.md).

**Dos casos (presentados en S0):** el del instructor, Online Retail II, es el de esta sesión y su tarea. El de los alumnos es **Bank Marketing** (`02-Proyecto-Transversal/datos/`): repiten la receta sobre él y lo presentan como **avance en S2**. Ver `02-Proyecto-Transversal/enunciado/README.md`.

## Objetivo
Al terminar, la persona asistente puede:
1. Explicar y reconstruir las capas **RAW → MASTER → FS → ML** con un cuaderno por capa.
2. Justificar por qué una variable no puede usar información posterior al corte y comprobarlo con una prueba.
3. Entrenar tres modelos con partición temporal, compararlos y registrar las ejecuciones en **MLflow**.
4. Traducir los cuadernos a Python y comprobar que el resultado es idéntico.

## Agenda
| Min | Bloque | Material |
|---|---|---|
| 0–30 | Revisión de entorno | `slides/` diap. 3 · `checklist.md` |
| 30–90 | Teoría | `slides/` diap. 4–16 · `teoria/README.md` |
| 90–225 | Práctica (135 min, pausa de 10) | `practica/guia-laboratorio.md` |
| 225–240 | Entrega y cierre (tarea y avance en Bank Marketing) | `tarea/README.md` · `slides/` diap. 18–20 |

## Contenido de esta carpeta
- `index.html`: índice de la sesión (presentaciones, documentos y qué falta). Se genera con `00-Planificacion/indices-de-sesion/generar_indices.py`.
- `slides/index.html`: presentación interactiva (20 diapositivas; flechas, **O** índice, **S** notas, **F** pantalla completa).
- `guion.md`: guion del docente minuto a minuto.
- `checklist.md`: comprobaciones del docente y del alumnado.
- `teoria/README.md`: resumen de teoría y glosario.
- `practica/guia-laboratorio.md`: laboratorio paso a paso con presupuesto de tiempo.
- `tarea/README.md` y `tarea/rubrica.md`: tarea y rúbrica (20/40/40).
- `evidencias/plantilla-decision.md`: plantilla de la evidencia entregable.
- PDF de la presentación y de los documentos (los exige la institución): `pdfs/S1-Datos-y-Entrenamiento/` en la raíz del repositorio; ver `pdfs/LEEME.md`.

## Qué está validado y qué no
- **Validado (Linux, entorno `env-ia-mlops`):** los cuatro cuadernos y el paquete `ia_mlops` con la muestra y con el dato completo (resultados idénticos), 34 pruebas en verde, y la receta de la tarea (añadir `monto_180d`: pipeline completo y 30 pruebas rápidas en verde).
- **No validado:** ejecución en Windows real (ver `03-Entorno/PRUEBA-EN-WINDOWS.md`); la tarea con un dataset distinto (por decidir).
- **Cifras de las diapositivas:** las del dato completo salen de `04-Proyecto-Base` ejecutado sobre el Excel de UCI; con la **muestra** del curso (23 070 filas) los modelos dan valores menores (regresión logística: valid 0,698 · test 0,747). Es esperado.

## MLflow en S1 (versión ligera)
Solo seguimiento: parámetros, métricas, firma del modelo y comparación de ejecuciones (`mlflow ui`). El registro de modelos y los alias llegan en S4 y S5.
Con MLflow 3 el proyecto guarda el modelo con cloudpickle (ver `03-Entorno/VALIDACION.md`).
