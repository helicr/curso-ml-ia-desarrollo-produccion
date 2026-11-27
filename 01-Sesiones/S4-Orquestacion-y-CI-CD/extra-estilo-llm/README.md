# Extra de S4: un LLM y el estilo de color

> **Antes de afinar un LLM, mide una línea base barata.** Este extra lo demuestra con un caso real: un LLM de visión pequeño intenta leer el estilo de color de una foto, y una regresión que entrena en segundos le gana. Después, el mismo LLM sí funciona donde le toca: explicando con palabras. Es opcional: no entra en la tarea ni en la rúbrica.

## Qué es

Los datos se **fabrican**: se toma una foto, se le aplican cinco ajustes de color conocidos (exposición, temperatura, tinte, contraste, saturación) y así las etiquetas salen exactas y gratis. Con esos datos se cuentan tres actos:

| Acto | Pregunta | Resultado | Notebooks |
|---|---|---|---|
| **1. El LLM intenta leer el estilo** | ¿Puede SmolVLM-256M escribir los 5 ajustes como JSON? | Sin entrenar (A): 55 % de JSON válido. Con LoRA (B): 100 % de JSON válido, pero **aprende el formato, no la tarea**: su error es peor que contestar siempre la media | 02, 03 |
| **2. Una línea base barata** | ¿Y si no usamos un LLM? | Una regresión sobre 27 estadísticas de color (C_color) entrena en segundos y es la mejor | 04 |
| **3. El LLM explica en español** | ¿Y si le damos una tarea de lenguaje? | Con LoRA, el LLM sí funciona (100 % de sentido correcto), aunque «fluido» no es «correcto» | 05 |

### Glosario mínimo (cada notebook vuelve a explicar lo suyo)

| Término | Qué significa aquí |
|---|---|
| **LLM** / **VLM** | Un LLM es un modelo de lenguaje grande: escribe texto palabra a palabra. Un VLM (*vision-language model*, «LLM de visión») además puede mirar una imagen. SmolVLM-256M es un VLM pequeño (256 millones de parámetros, los números que el modelo ha aprendido) |
| **Zero-shot** / **one-shot** | Preguntar al modelo sin enseñarle ningún ejemplo (zero-shot) o dándole uno solo en la pregunta (one-shot). No se entrena nada |
| **Fine-tuning** y **LoRA** | Fine-tuning (afinar) es seguir entrenando un modelo ya entrenado con nuestros datos. LoRA es una forma barata de hacerlo: se congela el modelo y solo se entrenan unas matrices pequeñas añadidas a su lado |
| **Adaptador** | El archivo con esas matrices pequeñas (7 MB); se guarda aparte del modelo base (494 MB) |
| **JSON** | Texto con pares «nombre: valor», por ejemplo `{"exposicion": 0.3}`; es lo que el modelo debe escribir |
| **MAE normalizado** | Error medio absoluto entre el ajuste predicho y el real, dividido por el ancho del rango del ajuste; 0 es perfecto y se promedian los cinco ajustes |
| **Ridge** | Una regresión lineal con una penalización que evita coeficientes exagerados; entrena en segundos |
| **ΔE, SSIM** | Medidas de imagen del notebook 04: ΔE es la diferencia de color con el resultado ideal (menor es mejor); SSIM, cuánto se conserva la estructura de la foto (1 es idéntica) |
| **Alucinación** | Que el modelo afirme algo que no está en la entrada; en el acto 3, mencionar un ajuste que no se tocó |
| **Artefacto** | Un archivo que un job de GitHub Actions guarda al terminar para que lo use otro job o lo descargues |
| **papermill** | Herramienta que ejecuta un notebook desde la terminal, cambiándole parámetros, y guarda una copia ya ejecutada |

**Mensaje global.** Usa cada herramienta para lo que sirve. Un LLM pequeño con LoRA aprende un formato de salida y una tarea de lenguaje; para **medir** un color, unas estadísticas y una regresión lineal son más baratas y más exactas. Y siempre: mide primero la línea base («contestar la media»), porque si tu modelo no la mejora, no ha aprendido nada de la foto.

## Para quién

Para quien ha seguido S3 y S4 y quiere ver un experimento de ML completo, incluido el fracaso honesto de un modelo grande frente a uno simple, y cómo se orquesta en GitHub Actions.

## Cómo seguirlo

**Sin ejecutar (lo recomendado).** Los notebooks se entregan con sus salidas guardadas. Se leen en el navegador sin instalar nada. Orden: 00, 01, 02, 03, 04, 05.

**Ejecutando en local.** Con CPU, sin GPU:

```bash
pip install -r requisitos-extra-estilo.txt
```

Cada notebook explica qué debes ver y qué hacer si falla. Las descargas (modelo y fotos) van a una caché fuera del repositorio.

**Orquestado en GitHub Actions.** Desde la web de GitHub, sin ejecutar nada en tu ordenador: ver [`guia-pipeline.md`](guia-pipeline.md).

## Notebooks

Los tiempos son de los notebooks ejecutados con la configuración de clase (300 fotos: 210 de entrenamiento, 30 de validación y 60 de test), en CPU, portátil de 12 núcleos, sin GPU. Cada notebook empieza con «Qué vas a aprender» y termina con «Qué te llevas» y dos preguntas; el hilo de uno al siguiente está en su apartado «Dónde estamos».

| # | Notebook | Qué hace | Tiempo en CPU |
|---|---|---|---|
| 0 | `00_preparar_entorno.ipynb` | Comprueba versiones, licencia, descarga el modelo y la red pequeña, comprueba memoria y disco | 13 s (prueba tipo CI del estudio previo); la descarga del modelo, 51,7 s la primera vez |
| 1 | `01_datos_fabricados.ipynb` | Define los ajustes, fabrica las parejas y reparte train, val y test | 12–15 s |
| 2 | `02_zero_shot.ipynb` | Versión A: el modelo sin entrenar; respuestas reales buenas y malas | 320 s (estudio previo, 60 fotos de test) |
| 3 | `03_fine_tuning_lora.ipynb` | Versión B: LoRA, curva de pérdida, error, tamaño del adaptador, MLflow | 1456 s (24 min) |
| 4 | `04_comparar_y_transferir.ipynb` | Versiones C, C_color y D, tabla comparativa, panel de transferencia | ≈40 s |
| 5 | `05_explicar_estilo.ipynb` | Acto 3: el LLM explica los ajustes en español, con LoRA | 1397 s (23 min), medido el 21/11/2026 |

Fuente: `INFORME.md` del estudio técnico (tabla «Tiempos, tamaños y memoria») y los avisos de tiempo de los propios notebooks. En clase se llevan ejecutados el 03 y el 05 y solo se recorren.

**Orden obligatorio:** el 04 lee las predicciones del 02 y del 03 (y busca el run `B_lora` en MLflow) en la **misma carpeta de trabajo** (`ESTILO_TRABAJO`): ejecuta antes el 01, el 02 y el 03. El 05 solo necesita el 01. Las **diapositivas** del extra están en [`index.html`](index.html) (26 diapositivas, 60 min, órdenes para copiar y capturas de las salidas reales).

## Requisitos

- **Hardware:** CPU, sin GPU. Memoria pico medida: 2747 MB en el 03 y 2887 MB en el 05 (con 500 frases). Se recomiendan unos 8 GB de RAM (mínimo previsto, sin verificar) y ~2 GB de disco para las descargas.
- **Software:** Python 3.11 y las versiones fijadas en [`requisitos-extra-estilo.txt`](requisitos-extra-estilo.txt) (`torch`/`torchvision` en CPU, `transformers`, `peft`, `accelerate`, `mlflow`, `scikit-learn`, `scikit-image`…). Van aparte de los requisitos del proyecto base.
- **Descargas:** el modelo SmolVLM-256M-Instruct (493,9 MB), MobileNetV3-small (9,8 MB) y las fotos de Oxford-IIIT Pet (~792 MB).

## Si falla (al ejecutar los notebooks en tu ordenador o en un Codespace)

**`ModuleNotFoundError: No module named 'torch'` en el notebook 00.** El kernel que usa el notebook no tiene las librerías del extra: van **aparte** de las del proyecto base y no se instalan con ellas. Instálalas con **el mismo Python que usa el kernel**:

```bash
python -m pip install -r requisitos-extra-estilo.txt
```

Para saber qué Python es, ejecuta en una celda `import sys; print(sys.executable)` y usa esa ruta en lugar de `python`. Después **reinicia el kernel** y comprueba, en una celda:

```python
import torch; print(torch.__version__)
```

Debe imprimir `2.15.0+cpu`. En un portátil con proxy corporativo, `pip` puede rechazar el certificado: añade `--cert <ruta-del-bundle-de-certificados>` a la orden de `pip`.

**`ConnectError` al bajar el modelo de Hugging Face.** En una red corporativa con proxy, la descarga del modelo falla. Usa un **Codespace** (sin proxy). En su terminal:

```bash
conda activate env-ia-mlops
python -m pip install -r requisitos-extra-estilo.txt
```

y elige como kernel del notebook `env-ia-mlops` (`/opt/conda/envs/env-ia-mlops/bin/python`).

**Los notebooks 03 y 05 tardan mucho.** El 03 (LoRA) tarda unos 24 min y el 05 unos 23 min, en un portátil de 12 núcleos; en un Codespace de 2 núcleos pesan aún más (sin dato de cuánto). No hace falta ejecutarlos: **se pueden leer sin ejecutar**, porque se entregan con sus salidas guardadas. Si quieres ver que funcionan, la alternativa es el **pipeline de GitHub Actions** ([`guia-pipeline.md`](guia-pipeline.md)), que los ejecuta con parámetros pequeños.

## Orquestación en GitHub Actions

Los mismos notebooks se ejecutan como pipeline: cada notebook es un job, con `needs:`, artefactos y caché. La guía [`guia-pipeline.md`](guia-pipeline.md) explica el grafo, el guion de clase y los pasos del alumno; el control previo está en [`checklist-actions.md`](checklist-actions.md) y el workflow en [`extra-estilo-llm.yml`](extra-estilo-llm.yml).

**Run real (21/11/2026):** [44854247545](https://github.com/helicr/curso-ml-ia-desarrollo-produccion/actions/runs/44854247545), rama `lab/extra-estilo-llm`: **Success, 14 min 10 s, 13 artefactos**. Se ejecuta con parámetros de CI pequeños (60 fotos, 2 épocas; 100 frases y 1 época en el acto 3) para comprobar que el pipeline funciona. Sus cifras (por ejemplo, 13 fotos de test) **no** se comparan con las de la tabla de abajo: las conclusiones se sacan solo con la configuración de clase. Las cifras del run están en la guía.

![Grafo del run en Actions: Success, 14 m 10 s, 13 artefactos](img/x01-grafo-actions.webp)

## Resultados clave (configuración de clase, 300 fotos, 60 de test)

Error al leer los ajustes: MAE normalizado, 0 = perfecto.

| Versión | Qué es | MAE normalizado |
|---|---|---|
| Media | Contestar siempre la media del entrenamiento | 0,259 |
| A | SmolVLM-256M sin entrenar (55 % de JSON válido) | 0,433 |
| B | SmolVLM-256M con LoRA (100 % de JSON válido; adaptador 7,06 MB, 0,71 % de los parámetros) | 0,310 |
| 2c | Estadísticas en el prompt + LoRA | 0,244 |
| C | MobileNetV3-small + Ridge | 0,229 |
| **C_color** | **27 estadísticas de color + Ridge (segundos)** | **0,151** |
| D | Reinhard (sin aprendizaje) | no aplica (no predice ajustes) |

C_color se registra en MLflow como `estilo-color-ridge` con el alias `produccion`; el adaptador LoRA, como `estilo-lora-adaptador` con el alias `descartado`.

Acto 3 (el LLM explica el JSON de ajustes; frases de test):

| Versión | Sentido correcto | Frases con alucinación | Frases perfectas |
|---|---|---|---|
| A3, sin entrenar | 40,7 % | 58,3 % | 0 % |
| B3, LoRA (500 frases, 2 épocas) | 100 % | 18,3 % (10,0 % y 15,0 % en otras ejecuciones, ver notebook 05) | 81,7 % |

Aquí el fine-tuning **sí** funciona, porque la tarea es de lenguaje. Pero el modelo aún se inventa algún adjetivo en ajustes casi nulos: fluido no es igual a correcto.

Fuentes: `INFORME.md` del estudio técnico (rondas 1 a 4, ejecución de referencia con 300 fotos) y las tablas de los notebooks 04 y 05.

## Licencias y citas

- **SmolVLM-256M-Instruct** (Hugging Face, HuggingFaceTB): licencia `apache-2.0`, leída de la ficha del modelo.
- **Oxford-IIIT Pet** (fotos base): licencia CC BY-SA 4.0. Cita: Parkhi, O. M., Vedaldi, A., Zisserman, A. y Jawahar, C. V., «Cats and Dogs», CVPR 2012. Los paneles derivados de las fotos heredan CC BY-SA 4.0.
- **MobileNetV3-small** (línea base C, pesos de torchvision): el código de torchvision es BSD-3-Clause; la licencia de los **pesos**: sin verificar.
- Reinhard, E. et al., «Color Transfer between Images», IEEE Computer Graphics and Applications, 2001 (método).

## Qué no se ha verificado

- **SmolVLM-500M**, Moondream u otros modelos de visión: no se probaron.
- **Más épocas, más datos u otras variantes de LoRA** (MLP, conector, otra tasa de aprendizaje): no se probaron; podrían cambiar el resultado de B.
- **Otras semillas:** una sola semilla y un solo reparto; con 60 fotos de test, diferencias pequeñas pueden no ser significativas.
- **Un fork de otra cuenta** ejecutando el workflow (por ejemplo, el aviso para activar Actions): sin verificar.
- **Licencia de los pesos de MobileNetV3** de torchvision.
