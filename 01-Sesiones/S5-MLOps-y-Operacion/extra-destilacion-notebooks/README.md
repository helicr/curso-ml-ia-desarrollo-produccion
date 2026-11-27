# Destilación de conocimiento: de la intuición a un estudiante en producción

Extra opcional de la sesión 5 del curso *ML e IA: de desarrollo a producción* (UNTRM). La carpeta en el repositorio es `01-Sesiones/S5-MLOps-y-Operacion/extra-destilacion-notebooks/`. No entra en la tarea ni en la rúbrica.

Material práctico (cuadernos de Jupyter) para entender y aplicar **destilación de conocimiento** (*knowledge distillation*): un modelo **profesor**, ya entrenado, transfiere lo que sabe a un modelo **estudiante** más pequeño, mediante etiquetas blandas (distribuciones), no solo con las etiquetas duras 0/1.

Está pensado para ejecutarse **en CPU**, en Linux, macOS o Windows. Una GPU acelera el cuaderno 03, pero no es necesaria.

Los `.ipynb` de esta carpeta **ya incluyen salidas** de una ejecución en CPU (Python 3.12, PyTorch solo CPU). Puedes leerlos sin volver a entrenar. Si los reejecutas, se regeneran `modelos/` y `resultados/`. Algunas salidas guardadas muestran rutas absolutas de la máquina donde se ejecutaron (`/workspace/destilacion/...`); al reejecutar verás la ruta de tu carpeta. Eso no cambia las métricas ni las figuras.

## Índice y orden de ejecución

Hay que seguir el orden. El cuaderno 04 lee artefactos que generan el 02 y el 03. El 05 se puede abrir después del 01; varios ejercicios usan resultados del 02 y del 03. La **v2** (cuadernos 06 y 07) no sustituye a la v1: parte de ella y construye un estudiante de sentimiento que sí cumple las puertas de promoción del ejercicio 5. El 07 necesita el 03 y el 06.

| # | Cuaderno | Qué hace | Tiempo orientativo (CPU) |
|---|---|---|---|
| 00 | [notebooks/00-introduccion-y-setup.ipynb](notebooks/00-introduccion-y-setup.ipynb) | Intuición, comprobación del entorno, proxy y Hugging Face | 1-2 min |
| 01 | [notebooks/01-teoria-softmax-temperatura.ipynb](notebooks/01-teoria-softmax-temperatura.ipynb) | Softmax, temperatura, «conocimiento oscuro», pérdida de destilación y figuras | 1-2 min |
| 02 | [notebooks/02-destilacion-mnist-mlp.ipynb](notebooks/02-destilacion-mnist-mlp.ipynb) | Calentamiento: MLP profesor (30 000 imágenes) y estudiante pequeño (400 etiquetas) | 1-3 min |
| 03 | [notebooks/03-destilacion-bert-sentimiento.ipynb](notebooks/03-destilacion-bert-sentimiento.ipynb) | Profesor de Hugging Face (DistilBERT, SST-2) hacia un estudiante diminuto | 2-15 min (la primera vez descarga el modelo, unos 250 MB) |
| 04 | [notebooks/04-comparativa-y-produccion.ipynb](notebooks/04-comparativa-y-produccion.ipynb) | Exactitud, tamaño, latencia y conclusiones de MLOps | 1-3 min |
| 05 | [notebooks/05-ejercicios.ipynb](notebooks/05-ejercicios.ipynb) | Ejercicios (con soluciones al final). La v1 de sentimiento no promociona | 2-10 min |
| 06 | [notebooks/06-destilacion-v2-sentimiento.ipynb](notebooks/06-destilacion-v2-sentimiento.ipynb) | v2: TinyBERT + más datos + logits cacheados + int8. `MODO_RAPIDO` por defecto | 10-20 min (menos si los logits ya están en `modelos/`) |
| 07 | [notebooks/07-comparativa-v1-vs-v2.ipynb](notebooks/07-comparativa-v1-vs-v2.ipynb) | Ablación v1 frente a v2 y decisión de promoción | 1-3 min |

Para volver a ejecutarlos todos, desde la raíz del proyecto y con el entorno activado:

```bash
bash scripts/ejecutar_cuadernos.sh
```

En Windows (PowerShell), con el entorno activado:

```powershell
$env:HF_HOME = "$PWD\cache-hf"
$env:TOKENIZERS_PARALLELISM = "false"
foreach ($nb in @(
  "notebooks\00-introduccion-y-setup.ipynb",
  "notebooks\01-teoria-softmax-temperatura.ipynb",
  "notebooks\02-destilacion-mnist-mlp.ipynb",
  "notebooks\03-destilacion-bert-sentimiento.ipynb",
  "notebooks\04-comparativa-y-produccion.ipynb",
  "notebooks\05-ejercicios.ipynb",
  "notebooks\06-destilacion-v2-sentimiento.ipynb",
  "notebooks\07-comparativa-v1-vs-v2.ipynb"
)) {
  python -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout 1800 $nb
}
```

## Requisitos

- El entorno del curso `env-ia-mlops` (véase `03-Entorno/`), o Python 3.12 (recomendado) / 3.11 en un entorno nuevo
- Las librerías de [`requisitos-extra-destilacion.txt`](requisitos-extra-destilacion.txt) (PyTorch solo CPU, transformers, datasets, etc.), **aparte** de las del proyecto base
- Unos 3 GB de disco para el entorno, el caché de Hugging Face y MNIST
- Salida a Internet la primera vez (MNIST y el profesor de sentimiento). Si estás detrás de un proxy corporativo, configura el proxy *antes* de abrir el cuaderno 03 o el 06 (o empieza por el 00)

## Entorno recomendado: el del curso (`env-ia-mlops`)

Este extra necesita paquetes que **no** vienen en `env-ia-mlops`. Activa el entorno del curso e instala encima los requisitos del extra, con el mismo Python que use el kernel:

```bash
conda activate env-ia-mlops
pip install -r requisitos-extra-destilacion.txt
```

En Windows (PowerShell), si tu red sale por un proxy corporativo, defínelo **en esta misma sesión** antes de instalar (ajusta el host si el tuyo es otro; en un aula o un PC de casa, sin proxy, omite estas tres líneas y el `--proxy`):

```powershell
conda activate env-ia-mlops
$env:HTTP_PROXY  = "http://proxy.empresa:8080"
$env:HTTPS_PROXY = $env:HTTP_PROXY
$env:NO_PROXY    = "localhost,127.0.0.1"
pip install --proxy $env:HTTP_PROXY -r requisitos-extra-destilacion.txt
```

El archivo de requisitos ya incluye `--extra-index-url` para las ruedas CPU de PyTorch. Si no tienes el entorno del curso, puedes crear uno nuevo (apartados siguientes).

## Preparar un entorno nuevo (CPU, Linux o macOS)

```bash
python3.12 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requisitos-extra-destilacion.txt --extra-index-url https://download.pytorch.org/whl/cpu
python -m ipykernel install --user --name destilacion --display-name "Python (destilacion)"
jupyter notebook notebooks/00-introduccion-y-setup.ipynb
```

`requisitos-extra-destilacion.txt` fija `torch==...+cpu`. El `--extra-index-url` es necesario para que pip encuentre esa rueda y no intente instalar una variante con CUDA.

## Preparar un entorno nuevo (CPU, Windows)

1. Instala Python 3.12 desde [python.org](https://www.python.org/downloads/) o con `winget install Python.Python.3.12`. Durante la instalación, marca «Add python.exe to PATH».
2. Abre PowerShell en esta carpeta (`extra-destilacion-notebooks`).

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
```

Si Windows bloquea la activación (`execution policy`), ejecuta una vez, solo para tu usuario:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Instala PyTorch **solo CPU** y el resto de dependencias:

```powershell
python -m pip install --upgrade pip
pip install -r requisitos-extra-destilacion.txt --extra-index-url https://download.pytorch.org/whl/cpu
python -m ipykernel install --user --name destilacion --display-name "Python (destilacion)"
jupyter notebook notebooks\00-introduccion-y-setup.ipynb
```

También puedes abrir los cuadernos en Visual Studio Code (extensión Jupyter) y elegir el kernel `Python (destilacion)` o el intérprete `venv\Scripts\python.exe`.

Los cuadernos añaden `src/` al `sys.path` y localizan la raíz del proyecto aunque el directorio de trabajo sea `notebooks/`.

## Proxy corporativo y Hugging Face

El cuaderno 00 detecta si ya existen `HTTP_PROXY`, `HTTPS_PROXY`, el certificado corporativo (`SSL_CERT_FILE` / `REQUESTS_CA_BUNDLE`) y un `HF_TOKEN`. No imprime secretos. Define las variables **en la misma terminal** (o como variables de usuario) *antes* de abrir Jupyter, o descomenta el bloque de ayuda al principio del cuaderno 00.

Linux o macOS:

```bash
export HTTP_PROXY="http://usuario:contraseña@proxy.empresa:8080"
export HTTPS_PROXY="$HTTP_PROXY"
export NO_PROXY="localhost,127.0.0.1,.empresa.com"
# Si el proxy inspecciona HTTPS:
export SSL_CERT_FILE="/ruta/al/certificado-corporativo.pem"
export REQUESTS_CA_BUNDLE="$SSL_CERT_FILE"
# Opcional, si un modelo del Hub es privado o hay límite de tasa:
export HF_TOKEN="hf_..."
```

Windows (PowerShell, solo esta sesión):

```powershell
$env:HTTP_PROXY  = "http://usuario:contraseña@proxy.empresa:8080"
$env:HTTPS_PROXY = $env:HTTP_PROXY
$env:NO_PROXY    = "localhost,127.0.0.1,.empresa.com"
$env:SSL_CERT_FILE      = "C:\ruta\certificado-corporativo.pem"
$env:REQUESTS_CA_BUNDLE = $env:SSL_CERT_FILE
$env:HF_TOKEN = "hf_..."
```

Para dejarlas fijas en el usuario de Windows: «Configuración → Sistema → Acerca de → Configuración avanzada del sistema → Variables de entorno», o `setx` (hace falta cerrar y abrir la terminal).

Si `pip` también necesita el proxy:

```powershell
pip install --proxy $env:HTTP_PROXY -r requisitos-extra-destilacion.txt --extra-index-url https://download.pytorch.org/whl/cpu
```

Si el profesor de sentimiento ya está en `cache-hf/`, puedes trabajar sin red:

```bash
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
```

```powershell
$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"
```

El conjunto SST-2 se carga desde `nyu-mll/glue` (el identificador antiguo `glue` ya no es válido en el Hub).

## Qué hay en cada carpeta

```
extra-destilacion-notebooks/
  notebooks/               # los ocho cuadernos (v1: 00-05; v2: 06-07), con salidas
  src/destilacion_utils.py # funciones y modelos compartidos
  modelos/                 # pesos ligeros de MNIST y logits; los de TinyBERT y la GRU no van en el repo
  resultados/              # métricas en JSON y figuras
  datos/                   # MNIST (se crea al ejecutar el 02; no se incluye en el repo)
  cache-hf/                # caché de Hugging Face del proyecto (si no hay HF_HOME previo; no se incluye)
  scripts/                 # regenerar cuadernos y reejecutarlos
  requisitos-extra-destilacion.txt
```

Los cuadernos 02, 03 y 06 escriben en `modelos/` y `resultados/`. El 04 lee la v1; el 07 lee la v1 y la v2. Ninguno de los dos vuelve a entrenar.

Una copia empaquetada para compartir puede omitir `venv/`, `cache-hf/`, `datos/`, `__pycache__/` y los checkpoints de 5 MB o más (GRU de la v1 y TinyBERT de la v2; se regeneran ejecutando los cuadernos 03 y 06). Las métricas de los cuadernos 04 y 07 están en los JSON y no dependen de esos pesos. El caché de logits `modelos/v2_sentimiento_logits_profesor.pt` es pequeño y conviene incluirlo.

## Serie v2 (sentimiento que sí promociona)

La v1 del cuaderno 03 usa un GRU entrenado desde cero con 3 000 frases. Es didáctica y rápida, pero se queda más de 20 puntos por debajo del profesor: **no supera las puertas del ejercicio 5**.

La v2 no borra esa lección. Cambia el diseño:

- Estudiante: `huawei-noah/TinyBERT_General_4L_312D` (4 capas, ya preentrenado por destilación a partir de un BERT grande).
- 20 000 frases de SST-2 y logits del profesor **cacheados** en `modelos/v2_sentimiento_logits_profesor.pt`.
- Medición de latencia justa (mismo lote, mismos 4 hilos). Se mide también la **cuantización dinámica int8**; en la ejecución de referencia no entra en la puerta de calidad (baja la exactitud más de lo admisible y apenas recorta el p95), así que la variante oficial es el TinyBERT duro en **fp32**, lote 16.
- En el cuaderno 06, `MODO_RAPIDO = True` (2 épocas) es el valor por defecto. Ponerlo a `False` sube a 3 épocas; no siempre mejora el test.

Los pesos finos de TinyBERT pesan decenas de megas: una copia ligera del material puede omitirlos. El cuaderno 06 los vuelve a generar. El caché de logits sí es pequeño y conviene dejarlo.

## Convención


- Semilla por defecto: 42
- El dispositivo se elige solo: CUDA si hay GPU usable, si no CPU
- Las métricas que alimentan el cuaderno 04 están en `resultados/mnist.json` y `resultados/sentimiento.json`. Las de la v2, en `resultados/v2_sentimiento.json` y `resultados/v2_comparativa.json`
