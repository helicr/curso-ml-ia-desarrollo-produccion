# RAG: de la pregunta al documento, y del documento a la respuesta

Extra opcional de la sesión 5 del curso *ML e IA: de desarrollo a producción* (UNTRM).
La carpeta en el repositorio es `01-Sesiones/S5-MLOps-y-Operacion/extra-rag-notebooks/`.
No entra en la tarea ni en la rúbrica.

Material práctico (cuadernos de Jupyter) para entender y aplicar **RAG**
(*Retrieval-Augmented Generation*, generación aumentada con recuperación):
ante una pregunta, el sistema **recupera** trozos de un corpus que tú controlas
y **después** le pide a un modelo de lenguaje que redacte la respuesta **con
ese contexto**, citando fuentes.

Está pensado para ejecutarse **en CPU**, en Windows, Linux o macOS. Una GPU
acelera el cuaderno 04, pero no es necesaria. No hace falta ninguna API de pago.

Los `.ipynb` de esta carpeta **ya incluyen salidas** de una ejecución en CPU
(Python 3.12, PyTorch solo CPU, modo rápido). Puedes leerlos sin volver a
descargar modelos. Si los reejecutas, se regeneran `modelos/` y `resultados/`.
Algunas salidas guardadas muestran rutas absolutas de la máquina donde se
ejecutaron (`/workspace/rag/...`); al reejecutar verás la ruta de tu carpeta.
Eso no cambia las métricas ni las figuras.

El corpus de `datos/corpus/` es **original de este taller**: convenios del curso
*De Modelo a Producción* (UNTRM) redactados como material didáctico, y una
empresa **ficticia** (NubeAndina) con políticas inventadas. No hay texto con
copyright de terceros. Las cifras están puestas a propósito para pillar
alucinaciones.

## Índice y orden de ejecución

Hay que seguir el orden. El cuaderno 03 lee el índice que genera el 02. El 04 y
el 05 usan ese índice y un LLM local. El 06 se puede abrir después del 02; varias
soluciones reutilizan el índice.

| # | Cuaderno | Qué hace | Tiempo orientativo (CPU) |
|---|---|---|---|
| 00 | [notebooks/00-introduccion-y-setup.ipynb](notebooks/00-introduccion-y-setup.ipynb) | Qué es RAG, por qué (alucinaciones, conocimiento fresco o privado), entorno, proxy y Hugging Face | 1 min |
| 01 | [notebooks/01-embeddings-y-similitud.ipynb](notebooks/01-embeddings-y-similitud.ipynb) | Embeddings, similitud coseno y PCA en 2-D, con frases en español | 1–5 min (la primera vez descarga el modelo, unos 500 MB) |
| 02 | [notebooks/02-chunking-e-indexado.ipynb](notebooks/02-chunking-e-indexado.ipynb) | Corpus, estrategias de *chunking*, índice NumPy y FAISS | 1–2 min |
| 03 | [notebooks/03-recuperacion-y-busqueda.ipynb](notebooks/03-recuperacion-y-busqueda.ipynb) | BM25, búsqueda densa, híbrida (RRF), *recall@k* y MRR | 2–5 min |
| 04 | [notebooks/04-generacion-con-llm-local.ipynb](notebooks/04-generacion-con-llm-local.ipynb) | LLM local: la misma pregunta **sin RAG** y **con RAG** | 5–15 min (la primera vez descarga el LLM, unos 1 GB) |
| 05 | [notebooks/05-pipeline-completo-y-evaluacion.ipynb](notebooks/05-pipeline-completo-y-evaluacion.ipynb) | *Pipeline* de extremo a extremo, mandos (*chunk*, *k*), notas de MLOps | 2–8 min |
| 06 | [notebooks/06-ejercicios.ipynb](notebooks/06-ejercicios.ipynb) | Ejercicios (con soluciones al final) | 1–3 min |

Validación de esta copia, en CPU, con los modelos ya en `cache-hf/` y
`RAG_MODO_RAPIDO=1`: 00 ≈ 10 s, 01 ≈ 15 s, 02 ≈ 19 s, 03 ≈ 4 min, 04 ≈ 5,5 min,
05 ≈ 17 s, 06 ≈ 9 s. En un portátil en frío, o la primera vez que se descargan
los modelos, súmale la red y espera del orden de 15–30 min para la serie
completa.

Para volver a ejecutarlos todos, desde la raíz del proyecto y con el entorno
activado:

```bash
bash scripts/ejecutar_cuadernos.sh
```

En Windows (PowerShell), con el entorno activado:

```powershell
$env:HF_HOME = "$PWD\cache-hf"
$env:TOKENIZERS_PARALLELISM = "false"
$env:RAG_MODO_RAPIDO = "1"
foreach ($nb in @(
  "notebooks\00-introduccion-y-setup.ipynb",
  "notebooks\01-embeddings-y-similitud.ipynb",
  "notebooks\02-chunking-e-indexado.ipynb",
  "notebooks\03-recuperacion-y-busqueda.ipynb",
  "notebooks\04-generacion-con-llm-local.ipynb",
  "notebooks\05-pipeline-completo-y-evaluacion.ipynb",
  "notebooks\06-ejercicios.ipynb"
)) {
  python -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout 2400 $nb
}
```

## Requisitos

- El entorno del curso `env-ia-mlops` (véase `03-Entorno/`), o Python 3.12
  (recomendado) / 3.11 en un entorno nuevo
- Las librerías de [`requisitos-extra-rag.txt`](requisitos-extra-rag.txt)
  (PyTorch solo CPU, sentence-transformers, faiss-cpu, etc.), **aparte** de las
  del proyecto base
- Unos 4 GB de disco para el entorno, el caché de Hugging Face y los índices
- Unos 4 GB de RAM libres para cargar el LLM de 0,5B en CPU (si no cabe, el
  código intenta un modelo de reserva más pequeño)
- Salida a Internet la primera vez (embeddings y LLM). Si estás detrás de un
  proxy corporativo, configúralo *antes* de abrir el cuaderno 01 (o empieza por
  el 00). En un aula o un PC de casa, sin proxy, no hace falta.

## Entorno recomendado: el del curso (`env-ia-mlops`)

Este extra necesita paquetes que **no** vienen en `env-ia-mlops`. Activa el
entorno del curso e instala encima los requisitos del extra, con el mismo
Python que use el kernel:

```bash
conda activate env-ia-mlops
pip install -r requisitos-extra-rag.txt
```

En Windows (PowerShell), si tu red sale por un proxy corporativo, defínelo
**en esta misma sesión** antes de instalar (ajusta el host si el tuyo es otro;
sin proxy, omite estas tres líneas y el `--proxy`):

```powershell
conda activate env-ia-mlops
$env:HTTP_PROXY  = "http://proxy.empresa:8080"
$env:HTTPS_PROXY = $env:HTTP_PROXY
$env:NO_PROXY    = "localhost,127.0.0.1"
pip install --proxy $env:HTTP_PROXY -r requisitos-extra-rag.txt
```

El archivo de requisitos ya incluye `--extra-index-url` para las ruedas CPU de
PyTorch. Si no tienes el entorno del curso, puedes crear uno nuevo (apartados
siguientes).

## Preparar un entorno nuevo (CPU, Linux o macOS)

```bash
python3.12 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requisitos-extra-rag.txt --extra-index-url https://download.pytorch.org/whl/cpu
python -m ipykernel install --user --name rag --display-name "Python (rag)"
jupyter notebook notebooks/00-introduccion-y-setup.ipynb
```

`requisitos-extra-rag.txt` fija `torch==...+cpu`. El `--extra-index-url` es necesario
para que pip encuentre esa rueda y no intente instalar una variante con CUDA.

## Preparar un entorno nuevo (CPU, Windows)

En un PC corporativo sin permisos de administrador, lo habitual es
**Miniforge/conda** (instalación solo para el usuario) o el Python de
`python.org` si ya lo tienes en el PATH.

### Con conda / Miniforge (recomendado en el PC del curso)

Abre **PowerShell** en esta carpeta (`extra-rag-notebooks`).

```powershell
conda create -n rag python=3.12 -y
conda activate rag
```

Si tu red sale por un proxy corporativo, defínelo **en esta misma sesión**
antes de instalar nada (ejemplo del aula; adapta el host si el tuyo es otro):

```powershell
$env:HTTP_PROXY  = "http://proxy.empresa:8080"  # ejemplo; en un PC corporativo pon el tuyo
$env:HTTPS_PROXY = $env:HTTP_PROXY
$env:NO_PROXY    = "localhost,127.0.0.1"
```

Instala PyTorch **solo CPU** y el resto de dependencias:

```powershell
python -m pip install --upgrade pip
pip install --proxy $env:HTTP_PROXY -r requisitos-extra-rag.txt --extra-index-url https://download.pytorch.org/whl/cpu
python -m ipykernel install --user --name rag --display-name "Python (rag)"
jupyter notebook notebooks\00-introduccion-y-setup.ipynb
```

Si prefieres instalar torch por separado:

```powershell
pip install --proxy $env:HTTP_PROXY torch --index-url https://download.pytorch.org/whl/cpu
# Comenta la línea torch==...+cpu de requisitos-extra-rag.txt y luego:
pip install --proxy $env:HTTP_PROXY -r requisitos-extra-rag.txt
```

### Con venv (si tienes Python 3.12 en el PATH)

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
```

Si Windows bloquea la activación (`execution policy`), ejecuta una vez, solo
para tu usuario:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

A partir de ahí, los mismos `pip install` del apartado anterior (con o sin
`--proxy`, según tu red).

También puedes abrir los cuadernos en Visual Studio Code (extensión Jupyter) y
elegir el kernel `Python (rag)` o el intérprete del entorno.

Los cuadernos añaden `src/` al `sys.path` y localizan la raíz del proyecto
aunque el directorio de trabajo sea `notebooks/`.

## Proxy corporativo y Hugging Face

El cuaderno 00 detecta si ya existen `HTTP_PROXY`, `HTTPS_PROXY`, el certificado
corporativo (`SSL_CERT_FILE` / `REQUESTS_CA_BUNDLE`) y un `HF_TOKEN`. No imprime
secretos. Define las variables **en la misma terminal** (o como variables de
usuario) *antes* de abrir Jupyter, o descomenta el bloque de ayuda al principio
del cuaderno 00.

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
$env:HTTP_PROXY  = "http://proxy.empresa:8080"  # ejemplo; en un PC corporativo pon el tuyo
$env:HTTPS_PROXY = $env:HTTP_PROXY
$env:NO_PROXY    = "localhost,127.0.0.1"
# Si el proxy inspecciona HTTPS (por ejemplo Zscaler):
# $env:SSL_CERT_FILE      = "C:\ruta\certificado-corporativo.pem"
# $env:REQUESTS_CA_BUNDLE = $env:SSL_CERT_FILE
# $env:HF_TOKEN = "hf_..."
```

Para dejarlas fijas en el usuario de Windows: «Configuración → Sistema → Acerca
de → Configuración avanzada del sistema → Variables de entorno», o `setx` (hace
falta cerrar y abrir la terminal).

Si `pip` también necesita el proxy, añade `--proxy $env:HTTP_PROXY` como en los
ejemplos de arriba.

Si los modelos ya están en `cache-hf/`, puedes trabajar sin red:

```bash
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
```

```powershell
$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"
```

## Modelos que se descargan

| Uso | Identificador en el Hub | Tamaño aproximado |
|---|---|---|
| Embeddings (español, por defecto) | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | ~500 MB |
| LLM instructivo (cuadernos 04 y 05) | `Qwen/Qwen2.5-0.5B-Instruct` | ~1 GB |
| Reserva si el 0,5B no cabe | `HuggingFaceTB/SmolLM2-135M-Instruct` | más ligero, peor en español |
| *Reranker* opcional (se omite en modo rápido) | `cross-encoder/ms-marco-MiniLM-L-6-v2` | ~80 MB, entrenado en inglés |

El modo rápido (`RAG_MODO_RAPIDO=1`, activo por defecto) reduce el número de
preguntas que se generan con el LLM y el número de tokens nuevos. La
recuperación y las métricas del conjunto hecho a mano no se recortan.

Una API de pago (OpenAI, Gemini, Claude, un *endpoint* de empresa) es
**opcional** y no se usa en esta serie: el *pipeline* es el mismo, solo cambia
el paso de generación.

## Qué hay en cada carpeta

```
extra-rag-notebooks/
  notebooks/               # los siete cuadernos, en orden, con salidas
  src/rag_utils.py         # corpus, chunking, índices, métricas y pipeline
  datos/corpus/            # documentos originales (curso + NubeAndina)
  datos/preguntas.json     # conjunto pequeño, hecho a mano, para evaluar
  modelos/                 # índices NumPy/FAISS (sí van en el repo; no los pesos de Hugging Face)
  resultados/              # métricas en JSON y figuras
  cache-hf/                # caché de Hugging Face del proyecto (si no hay HF_HOME previo; no se incluye)
  scripts/                 # regenerar cuadernos y reejecutarlos
  requisitos-extra-rag.txt
```

Una copia empaquetada para compartir puede omitir `venv/` y `cache-hf/` (los
pesos se vuelven a descargar al ejecutar los cuadernos 01 y 04). Los índices
de `modelos/` son ligeros y sí se pueden incluir. Las métricas del 03 y del 04
están en los JSON y no dependen de los pesos.

## Convención

- Semilla por defecto: 42
- El dispositivo se elige solo: CUDA si hay GPU usable, si no CPU
- *Chunk* por defecto: 400 caracteres, con 80 de solape
- *k* por defecto en la generación: 4
- Las métricas de recuperación están en `resultados/recuperacion.json`; las de
  generación (con RAG y sin RAG), en `resultados/generacion.json`
