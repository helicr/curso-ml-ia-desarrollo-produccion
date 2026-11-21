# Extra de S4: un LLM de visión que copia el estilo de color de una foto

> **Borrador: en preparación.** Esta carpeta es un esqueleto. Los notebooks, las cifras y las instrucciones se completan tras el estudio técnico. No es material final para alumnos.

## Qué es

- El alumno da una **foto de referencia** (el estilo, por ejemplo un atardecer cálido) y una **foto de contenido**.
- Un **LLM de visión** pequeño, ajustado con **LoRA**, «lee» el estilo de la referencia y lo escribe como un JSON de ajustes de color (temperatura, saturación, contraste…).
- Esos ajustes se aplican a la foto de contenido.
- El resultado se compara con tres alternativas (el mismo modelo sin ajustar, una red pequeña y un método clásico sin aprendizaje) para decidir con datos si hace falta un LLM.
- Es un extra de S4: no es obligatorio y no entra en la tarea ni en la rúbrica. Los mismos notebooks se orquestan como pipeline en GitHub Actions.

## Notebooks

Cuatro notebooks cortos, ejecutados con sus salidas, y un quinto opcional.

| # | Notebook | Qué hace | Duración en clase |
|---|---|---|---|
| 0 | `00_preparar_entorno.ipynb` | Comprueba versiones, descarga el modelo y las fotos, comprueba memoria e hilos | [se completa tras el estudio técnico] |
| 1 | `01_datos_fabricados.ipynb` | Define los ajustes, aplica ajustes aleatorios conocidos, enseña antes y después, reparte train, val y test | [se completa tras el estudio técnico] |
| 2 | `02_zero_shot.ipynb` | Versión A: prompt al VLM, lectura del JSON y medida del error; respuestas reales buenas y malas | [se completa tras el estudio técnico] |
| 3 | `03_fine_tuning_lora.ipynb` | Versión B: LoRA, curva de pérdida, error en test, tamaño del adaptador, registro en MLflow | [se completa tras el estudio técnico] |
| 4 | `04_comparar_y_transferir.ipynb` | Versiones C y D, tabla comparativa, panel de transferencia de estilo, conclusiones | [se completa tras el estudio técnico] |
| 5 | `05_prueba_tu_foto.ipynb` (opcional) | Subir dos fotos propias y ver el resultado | [se completa tras el estudio técnico] |

Qué se hace en vivo y qué se lleva hecho lo decide el estudio técnico. Por defecto, el notebook 03 se lleva ejecutado y en clase solo se recorre.

## Cómo seguirlo: con y sin ejecutar

**Sin ejecutar.** Los notebooks se entregan con sus salidas guardadas. Se pueden leer en el navegador sin instalar nada.

**Ejecutando en local o en Codespace.**

- Hardware mínimo previsto: CPU, sin GPU (portátil propio o Codespace de 2 núcleos y 8 GB). Memoria máxima medida: [se completa tras el estudio técnico].
- Versiones: Python 3.11 (el del curso), `torch` y `torchvision` en CPU, `transformers`, `peft`, `accelerate`, `pillow`, `numpy`, `scikit-image`, `mlflow` 3.18, `jupyter`, `matplotlib`. El fichero `requisitos-extra-estilo.txt` con las versiones fijadas está pendiente.
- Orden: 00, 01, 02, 03, 04. Cada notebook explica qué debe ver el alumno y qué hacer si falla.
- Las descargas (modelo y fotos) van a una caché fuera del repositorio. No se suben al repositorio.

**Si el Codespace se detiene** (por cuota, al entrenar), sigue leyendo los notebooks ejecutados o ejecuta en local. El extra se puede seguir sin ejecutar.

## Orquestado en GitHub Actions

Los mismos notebooks se ejecutan como pipeline: cada notebook es un job, los jobs se encadenan con `needs:` y pasan su salida como artefacto. En la pestaña Actions se ve el grafo del experimento, y el adaptador, la tabla y el panel se descargan como artefactos.

```
preparar (00) ─► datos (01) ─┬─► zero-shot (02, versión A) ─────────┐
                             ├─► fine-tuning LoRA (03, versión B) ──┼─► comparar (04: tabla + panel) ─► resumen
                             └─► línea base (C) y Reinhard (D) ─────┘
```

- Archivo del workflow: `.github/workflows/extra-estilo-llm.yml` (pendiente).
- Disparadores: `push` a `lab/**` y `workflow_dispatch` con entradas para cambiar parámetros pequeños (N_EJEMPLOS, EPOCAS).
- Ejecución de notebooks con `papermill` o `jupyter nbconvert --execute`. Cada notebook ejecutado se sube como artefacto para verlo con sus salidas. La elección queda pendiente.
- Caché de pip y de la descarga del modelo.
- Resumen en el panel de la ejecución: tabla A/B/C/D y enlaces a los artefactos.
- Límites del runner de GitHub (memoria, núcleos, tiempo por job, tamaño de artefactos): sin verificar; se medirán con un run real.

## Licencias y citas

- **Oxford-IIIT Pet** (fotos base): licencia CC BY-SA 4.0, verificada el 15/11/2026. Cita: Parkhi, O. M., Vedaldi, A., Zisserman, A. y Jawahar, C. V., «Cats and Dogs», CVPR 2012. Origen: Universidad de Oxford (VGG).
- **Modelo de visión** (candidato SmolVLM-256M-Instruct; alternativas pendientes): licencia por confirmar.
- **MobileNetV3-small** preentrenada (línea base C, pesos de torchvision): licencia sin verificar.
