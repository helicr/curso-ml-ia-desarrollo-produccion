#!/usr/bin/env python3
"""Genera los cuadernos de extra-rag-notebooks/notebooks/."""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

RAIZ = Path(__file__).resolve().parents[1]
OUT = RAIZ / "notebooks"

BOOTSTRAP = r'''from pathlib import Path
import os, sys, json, time, gc, textwrap

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def _raiz():
    aqui = Path.cwd().resolve()
    for cand in [aqui, *aqui.parents]:
        if (cand / "src" / "rag_utils.py").exists() and (cand / "notebooks").is_dir():
            return cand
    raise FileNotFoundError(
        "No encuentro la raiz del proyecto de RAG "
        "(src/rag_utils.py + notebooks/)."
    )

RAIZ = _raiz()
sys.path.insert(0, str(RAIZ / "src"))

from rag_utils import (
    preparar_rutas,
    fijar_semilla,
    dispositivo,
    configurar_proxy_y_hf,
    comprobar_entorno,
    probar_conexion_hf,
    texto_ayuda_proxy,
    modo_rapido,
    guardar_json,
    cargar_json,
    cargar_corpus,
    cargar_preguntas,
    fragmentar_documentos,
    resumen_fragmentos,
    Codificador,
    similitud_coseno,
    IndiceNumpy,
    IndiceFAISS,
    IndiceBM25,
    fusion_rrf,
    Reranker,
    evaluar_recuperacion,
    construir_mensajes,
    construir_contexto,
    GeneradorLocal,
    contiene_hechos,
    parece_abstencion,
    PipelineRAG,
    evaluar_fidelidad,
    MODELO_EMBEDDINGS_DEFECTO,
    MODELO_RERANKER_DEFECTO,
    MODELO_LLM_DEFECTO,
    MODELO_LLM_RESERVA,
)

try:
    get_ipython().run_line_magic("matplotlib", "inline")
except Exception:
    import matplotlib
    matplotlib.use("Agg")

plt.rcParams.update({
    "figure.figsize": (8, 4.2),
    "axes.grid": True,
    "grid.alpha": 0.3,
    "axes.titlesize": 12,
    "figure.dpi": 110,
})

RUTAS = preparar_rutas(RAIZ)
SEMILLA = fijar_semilla()
CFG_RED = configurar_proxy_y_hf(RAIZ, verbose=True)
DEVICE = dispositivo()
MODO_RAPIDO = modo_rapido(True)
print(f"Raiz:        {RAIZ}")
print(f"Dispositivo: {DEVICE}")
print(f"Semilla:     {SEMILLA}")
print(f"Modo rapido: {MODO_RAPIDO}")
'''


def md(texto: str):
    return new_markdown_cell(texto.strip() + "\n")


def code(texto: str):
    return new_code_cell(texto.strip() + "\n")


def write_nb(nombre: str, celdas, kernelspec_display="Python (rag)"):
    nb = new_notebook(
        cells=celdas,
        metadata={
            "kernelspec": {
                "display_name": kernelspec_display,
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
    )
    ruta = OUT / nombre
    nbf.write(nb, ruta)
    print(f"escrito {ruta}")
    return ruta


# ---------------------------------------------------------------------------
# 00
# ---------------------------------------------------------------------------

def nb00():
    return [
        md("""\
# 00 · Introducción y preparación del entorno

**Objetivo de este cuaderno:** entender qué es RAG (*Retrieval-Augmented Generation*,
generación aumentada con recuperación) y dejar el entorno listo para el resto de
la serie: paquetes, dispositivo (CPU o GPU), proxy corporativo y Hugging Face.

No se descarga ningún modelo de lenguaje todavía. Si esta comprobación termina
bien, puedes pasar al cuaderno 01.

## La idea, en una frase

Un modelo de lenguaje **no tiene** (o no debería tener) todos los datos de tu
curso, de tu empresa o de esta mañana. RAG consiste en **recuperar** primero los
trozos de documento que importan para la pregunta y **después** pedirle al modelo
que redacte la respuesta **usando ese contexto**. El modelo deja de «inventárselo
de memoria» y pasa a apoyarse en fuentes que tú controlas.

## Por qué hace falta

Los LLM, incluso los buenos, tropiezan con tres problemas habituales en producción:

1. **Alucinaciones.** Afirman con seguridad cifras, nombres o normas que no existen.
   En este laboratorio usamos una empresa ficticia (NubeAndina) y convenios del
   curso precisamente para pillar esas invenciones: el modelo no puede «haberlas
   memorizado» en el preentrenamiento de forma fiable.
2. **Conocimiento que caduca.** Un modelo se entrenó con un corte de fecha. El
   reglamento de *este* semestre, el puerto de *esta* API o el alias del modelo
   campeón no tienen por qué estar en sus pesos.
3. **Conocimiento privado.** Políticas internas, entregas, manifiestos y
   experimentos del equipo no deben (ni pueden) estar en un modelo público. Van
   en un corpus que tú indexas.

RAG no es la única respuesta (también existen el *fine-tuning*, la destilación,
las herramientas y los agentes), pero es la más directa cuando la información
vive en documentos y cambia más rápido que el modelo.

## El diagrama del *pipeline*

Primero una versión en ASCII, que se ve en cualquier visor de cuadernos:

```
  Documentos (PDF, Markdown, wikis)
            |
            v
     Troceado (chunks)  ---->  Embeddings  ---->  Indice (NumPy / FAISS)
                                                      |
  Pregunta ----> (opcional: la misma red de embeddings)|
                      |                               v
                      |                        Recuperar top-k
                      |                               |
                      +-------> Prompt (pregunta + fragmentos + citas)
                                      |
                                      v
                                 LLM local
                                      |
                                      v
                         Respuesta fundada, con fuentes
```

Y el mismo flujo, en mermaid (VS Code, GitHub y JupyterLab suele renderizarlo):

```mermaid
flowchart LR
  D[Documentos] --> T[Chunking]
  T --> E[Embeddings]
  E --> I[Indice vectorial]
  P[Pregunta] --> R[Recuperador]
  I --> R
  R --> PR[Prompt con contexto y citas]
  P --> PR
  PR --> L[LLM local]
  L --> S[Respuesta fundada]
```

## Recorrido de la serie

| Cuaderno | Contenido | Depende de |
|---|---|---|
| **00** (este) | Intuición, entorno, proxy y Hugging Face | — |
| **01** | Embeddings, similitud coseno y una PCA en 2-D | 00 |
| **02** | Corpus, *chunking* e índice (NumPy y FAISS) | 01 |
| **03** | Recuperación: BM25, densa, híbrida y métricas | 02 |
| **04** | Generación con un LLM local: con RAG y sin RAG | 03 |
| **05** | *Pipeline* completo, evaluación y notas de producción | 04 |
| **06** | Ejercicios | 01; varios usan 02–05 |

Los artefactos (índices, métricas, figuras) se guardan en `modelos/` y `resultados/`.
"""),
        md("""\
## 1. Localizar el proyecto y el módulo compartido

Los cuadernos viven en `notebooks/` y las funciones comunes en `src/rag_utils.py`.
La celda siguiente localiza la raíz aunque el directorio de trabajo sea
`notebooks/`, añade `src/` al `sys.path` y deja creadas las carpetas `modelos/`,
`resultados/`, `datos/` y `cache-hf/`.
"""),
        code(BOOTSTRAP),
        md("""\
## 2. Comprobación del entorno

Se listan las versiones de los paquetes que usa la serie. Todo lo **obligatorio**
debe aparecer como disponible. El curso se puede completar en **CPU**; si hay
GPU, se usará, pero no es un requisito.

Si falta algún paquete, instálalo en el entorno del kernel (en la raíz del
proyecto: `pip install -r requisitos-extra-rag.txt`, y PyTorch CPU según el README) y
vuelve a ejecutar esta celda.
"""),
        code("""\
tabla_entorno = comprobar_entorno()
tabla_entorno
"""),
        code("""\
faltan = tabla_entorno.loc[
    tabla_entorno["obligatorio"] & ~tabla_entorno["disponible"], "componente"
].tolist()
assert not faltan, (
    "Faltan paquetes: " + ", ".join(faltan) + ". "
    "Activa el entorno del proyecto e instala requisitos-extra-rag.txt."
)
print("Entorno listo. Paquetes obligatorios disponibles.")
print(
    "Filas informativas (no bloquean): CUDA, proxy y token de Hugging Face. "
    "En CPU, sin proxy y sin token, es el resultado esperado."
)
print(texto_ayuda_proxy())
"""),
        md("""\
## 3. Proxy corporativo y Hugging Face

Si estás en una red de empresa, las descargas de Hugging Face pueden fallar por
el **proxy** o por un **certificado corporativo** que intercepta HTTPS. Esta
serie no adivina tu proxy ni imprime contraseñas ni tokens.

La función `configurar_proxy_y_hf` (ya ejecutada arriba) hace tres cosas conservadoras:

1. Informa de si `HTTP_PROXY` / `HTTPS_PROXY` / `NO_PROXY` están definidos.
2. Informa de si hay un certificado (`SSL_CERT_FILE` o `REQUESTS_CA_BUNDLE`) y de
   si hay un `HF_TOKEN` (solo sí o no).
3. Si `HF_HOME` no estaba definido, lo apunta a `cache-hf/` dentro del proyecto,
   para que el caché de modelos quede con el material y no se mezcle con el del usuario.

Para **definir** un proxy, descomenta y adapta la celda siguiente *antes* de
descargar nada (cuadernos 01 y 04), o exporta las variables en la terminal y
vuelve a abrir Jupyter.

En un PC corporativo típico (PowerShell), antes de abrir Jupyter:

```powershell
$env:HTTP_PROXY  = "http://proxysscc.bankinter.bk:8080"
$env:HTTPS_PROXY = $env:HTTP_PROXY
$env:NO_PROXY    = "localhost,127.0.0.1,.bankinter.bk"
```

Adapta el host si el tuyo es otro. Si hay usuario y contraseña, van en la URL
(`http://usuario:contraseña@host:puerto`) y **no** se suben al repositorio.
"""),
        code("""\
# Descomenta y adapta solo si tu red lo exige. No subas este cuaderno con credenciales.
# os.environ["HTTP_PROXY"]  = "http://usuario:contraseña@proxy.empresa:8080"
# os.environ["HTTPS_PROXY"] = os.environ["HTTP_PROXY"]
# os.environ["NO_PROXY"]    = "localhost,127.0.0.1,.empresa.com"
# os.environ["SSL_CERT_FILE"]      = "/ruta/al/certificado-corporativo.pem"
# os.environ["REQUESTS_CA_BUNDLE"] = os.environ["SSL_CERT_FILE"]
# os.environ["HF_TOKEN"] = "hf_..."  # o: huggingface-cli login
# Recargar la configuración después de editar:
# CFG_RED = configurar_proxy_y_hf(RAIZ, verbose=True)

CFG_RED
"""),
        md("""\
## 4. ¿Llegamos a Hugging Face?

La celda siguiente hace una petición `HEAD` a `https://huggingface.co`. No
descarga modelos. Si falla, revisa el proxy y el certificado *antes* del
cuaderno 01. Si ya tienes los modelos en `cache-hf/`, puedes trabajar sin red
con `HF_HUB_OFFLINE=1`.
"""),
        code("""\
conexion = probar_conexion_hf()
print(conexion)
if conexion["ok"]:
    print("Conexion al Hub correcta. El cuaderno 01 podra descargar el modelo de embeddings si no esta en cache.")
else:
    print(
        "No se alcanzo el Hub. Si es la primera ejecucion, las descargas fallaran. "
        "Configura el proxy o coloca los modelos en cache-hf/ y activa HF_HUB_OFFLINE=1."
    )
"""),
        md("""\
## 5. Modo rápido

En un portátil solo con CPU, generar texto con un LLM de 0,5B parámetros es
aceptable, pero no instantáneo. Por eso existe un **modo rápido**
(`RAG_MODO_RAPIDO`, activo por defecto): se generan menos preguntas en los
cuadernos 04 y 05 y se limita el número de tokens nuevos. La recuperación, las
métricas sobre el conjunto hecho a mano y las figuras de embeddings no se
recortan de forma agresiva: son baratas.

Para desactivarlo, en la terminal (`$env:RAG_MODO_RAPIDO = "0"` en PowerShell, o
`export RAG_MODO_RAPIDO=0` en bash) o en una celda, *antes* del *bootstrap* si
ya lo has cambiado a mano:

```python
os.environ["RAG_MODO_RAPIDO"] = "0"
```
"""),
        code("""\
print("Modo rapido activo:" , MODO_RAPIDO)
print("Modelos por defecto de la serie:")
print("  embeddings:", MODELO_EMBEDDINGS_DEFECTO)
print("  reranker (opcional):", MODELO_RERANKER_DEFECTO)
print("  LLM:", MODELO_LLM_DEFECTO)
print("  LLM de reserva:", MODELO_LLM_RESERVA)
print()
print("Corpus:", RUTAS["corpus"])
print("Documentos .md:", len(list(RUTAS["corpus"].glob("*.md"))))
"""),
        md("""\
## 6. Qué hay en cada carpeta

```
extra-rag-notebooks/
  notebooks/          # estos cuadernos, en orden
  src/rag_utils.py    # funciones e indices compartidos
  datos/corpus/       # documentos originales (curso + empresa ficticia)
  datos/preguntas.json
  modelos/            # indices guardados (no los pesos de Hugging Face)
  resultados/         # metricas JSON y figuras
  cache-hf/           # cache de modelos (no se reparte en el zip del aula)
  scripts/            # regenerar y reejecutar cuadernos
  requisitos-extra-rag.txt
```

Cuando esta comprobación termina sin errores, abre el
[01-embeddings-y-similitud.ipynb](01-embeddings-y-similitud.ipynb).
"""),
    ]


# ---------------------------------------------------------------------------
# 01
# ---------------------------------------------------------------------------

def nb01():
    return [
        md("""\
# 01 · Embeddings y similitud

**Objetivo:** entender qué es un *embedding* de frase, cómo se compara con la
**similitud coseno** y por qué dos textos «parecidos en significado» quedan cerca
en ese espacio, aunque no compartan las mismas palabras.

En este cuaderno se descarga (o se reutiliza desde `cache-hf/`) un modelo
multilingüe pequeño, apto para CPU y para español:

`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

No hay un LLM todavía: solo la red que convierte una frase en un vector.
"""),
        md("""\
## 1. Entorno y mandos

Los mandos de este cuaderno están en la celda siguiente, junto al *bootstrap*.
Cambia el nombre del modelo si quieres probar, por ejemplo,
`intfloat/multilingual-e5-small` (en ese caso las consultas suelen ir con el
prefijo `query:` y los documentos con `passage:`; MiniLM no lo necesita).
"""),
        code(BOOTSTRAP),
        code("""\
# --- Mandos de este cuaderno ---
MODELO_EMB = MODELO_EMBEDDINGS_DEFECTO
print("Modelo de embeddings:", MODELO_EMB)
print("Dispositivo:", DEVICE)
"""),
        md("""\
## 2. Qué es un embedding (y qué no)

Un *embedding* de frase es un vector de números (aquí, de unos pocos cientos de
dimensiones) que pretende capturar el **significado** de un texto corto. Si el
modelo es bueno, «¿en qué puerto escucha la API?» y «¿qué puerto expone el
contenedor de retención?» quedarán cerca, aunque no compartan el verbo.

Eso no convierte al vector en una base de datos ni en un razonador. Solo nos da
una forma de **medir cercanía**. La métrica habitual es la **similitud coseno**:
el coseno del ángulo entre dos vectores. Vale 1 si apuntan en la misma
dirección, 0 si son ortogonales y −1 si apuntan al contrario. Cuando
normalizamos los vectores a norma 1, el coseno coincide con el **producto interno**.

La recuperación densa del resto de la serie es, esencialmente: *embebe la
pregunta, embebe cada fragmento, ordena por coseno y quédate los k mejores*.
"""),
        md("""\
## 3. Cargar el modelo

La primera vez descarga del orden de 500 MB (queda en `cache-hf/`). En CPU
suele tardar unos segundos en cargar, más la descarga si no está en caché.
"""),
        code("""\
t0 = time.perf_counter()
codificador = Codificador(MODELO_EMB, dispositivo_destino=str(DEVICE))
t_carga = time.perf_counter() - t0
print(f"Cargado en {t_carga:.1f} s")
print(f"Dimensión del vector: {codificador.dim}")
print(f"Dispositivo del modelo: {codificador.dispositivo}")
"""),
        md("""\
## 4. Frases en español, de varios temas

Usamos frases cortas de los mismos mundos que el corpus (curso, Docker, MLflow,
NubeAndina). Así veremos, más abajo, **cúmulos** en la PCA: no estamos
clasificando a mano, el espacio las agrupa solo.
"""),
        code("""\
frases = [
    # Docker / API
    "La imagen Docker de la API se llama retencion-api:local.",
    "El contenedor expone el puerto 8080 y el healthcheck consulta /salud.",
    "Se construye la imagen con docker build desde la raiz del repositorio.",
    # Kubernetes
    "En Kubernetes la unidad minima de despliegue es el Pod.",
    "El Deployment de ejemplo de la API tiene 2 replicas en el namespace curso-mlops.",
    # MLflow / CI
    "El tracking URI de MLflow en el laboratorio es http://127.0.0.1:5000.",
    "El experimento se llama retencion-clientes y el alias del modelo es champion.",
    "El workflow de GitHub Actions es ci-retencion.yml y exige 80 % de cobertura.",
    # Reglamento del curso
    "La nota minima de aprobacion del curso es 11 sobre 20.",
    "La asistencia minima exigida es del 70 por ciento de las sesiones.",
    "El Avance 3 se entrega el viernes de la semana 4 en Classroom.",
    # NubeAndina
    "NubeAndina es una empresa ficticia fundada en Chachapoyas en 2019.",
    "Un empleado de NubeAndina tiene 22 dias laborables de vacaciones al año.",
    "La DPO de NubeAndina se llama Elena Quispe.",
    "Los datos de clientes no pueden salir de la region southamerica-west1.",
    "El cluster de produccion se llama gke-prod-andina-01.",
]

grupos = (
    ["Docker"] * 3
    + ["Kubernetes"] * 2
    + ["MLflow/CI"] * 3
    + ["Curso"] * 3
    + ["NubeAndina"] * 5
)
assert len(grupos) == len(frases)

t0 = time.perf_counter()
E = codificador.codificar(frases, progreso=False)
t_enc = time.perf_counter() - t0
print(f"Matriz de embeddings: {E.shape}  (codificadas en {t_enc:.2f} s)")
print(f"Norma media de los vectores (deberia ser ~1 si estan normalizados): {np.linalg.norm(E, axis=1).mean():.4f}")
"""),
        md("""\
## 5. Matriz de similitud coseno

Cada celda es el coseno entre la frase de la fila y la de la columna. La
diagonal es 1 (una frase consigo misma). Fíjate en que dos frases del mismo
tema puntúan alto aunque el vocabulario no sea idéntico, y en que un tema
lejos (vacaciones frente a Docker) queda cerca de 0.
"""),
        code("""\
S = similitud_coseno(E, E)
etiquetas = [f"{i+1:02d} {g}" for i, g in enumerate(grupos)]

fig, ax = plt.subplots(figsize=(8.5, 7.2))
im = ax.imshow(S, cmap="viridis", vmin=0, vmax=1)
ax.set_xticks(range(len(frases)))
ax.set_yticks(range(len(frases)))
ax.set_xticklabels(etiquetas, rotation=80, ha="right", fontsize=8)
ax.set_yticklabels(etiquetas, fontsize=8)
ax.set_title("Similitud coseno entre frases de ejemplo")
fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="coseno")
fig.tight_layout()
fig.savefig(RUTAS["resultados"] / "fig_similitud_coseno.png", dpi=130)
plt.show()
"""),
        md("""\
## 6. Una consulta: los vecinos más cercanos

Embebemos una pregunta que **no** está en la lista, palabra por palabra, y
ordenamos las frases por coseno. Debería ganar un vecino del tema correcto.
"""),
        code("""\
consultas = [
    "¿En qué puerto escucha la API del contenedor?",
    "¿Cuántos días de vacaciones tiene un trabajador de NubeAndina?",
    "¿Cómo se llama el experimento de MLflow del laboratorio?",
]

filas = []
for q in consultas:
    qv = codificador.codificar([q], progreso=False)[0]
    sims = similitud_coseno(qv, E)
    orden = np.argsort(-sims)
    print("=" * 70)
    print("Consulta:", q)
    for rango, i in enumerate(orden[:3], start=1):
        print(f"  {rango}. cos={sims[i]:.3f}  [{grupos[i]}] {frases[i]}")
        filas.append({"consulta": q, "rango": rango, "coseno": float(sims[i]), "grupo": grupos[i], "frase": frases[i]})

pd.DataFrame(filas)
"""),
        md("""\
## 7. Una foto en 2-D: PCA

Diez dimensiones no se dibujan. Una PCA a 2 componentes no es el espacio real
(perdemos información), pero suele bastar para *ver* que los temas forman
grupos. Los ejes no tienen un nombre semántico («eje Docker»): son las
direcciones de mayor varianza.
"""),
        code("""\
from sklearn.decomposition import PCA

pca = PCA(n_components=2, random_state=SEMILLA)
xy = pca.fit_transform(E)
print("Varianza explicada por las 2 componentes:", pca.explained_variance_ratio_.round(3))
print("Suma:", float(pca.explained_variance_ratio_.sum()))

colores = {
    "Docker": "#1f77b4",
    "Kubernetes": "#17becf",
    "MLflow/CI": "#2ca02c",
    "Curso": "#ff7f0e",
    "NubeAndina": "#d62728",
}

fig, ax = plt.subplots(figsize=(8.2, 6.2))
for g in colores:
    mask = np.array(grupos) == g
    ax.scatter(xy[mask, 0], xy[mask, 1], c=colores[g], s=70, label=g, edgecolors="k", linewidths=0.4)
    for i in np.where(mask)[0]:
        ax.annotate(str(i + 1), (xy[i, 0], xy[i, 1]), textcoords="offset points", xytext=(5, 4), fontsize=8)
ax.set_xlabel("PCA 1")
ax.set_ylabel("PCA 2")
ax.set_title("Frases de ejemplo proyectadas con PCA (2-D)")
ax.legend(frameon=True)
fig.tight_layout()
fig.savefig(RUTAS["resultados"] / "fig_pca_embeddings.png", dpi=130)
plt.show()
"""),
        md("""\
## 8. Una nota sobre otros modelos (E5)

Modelos como `intfloat/multilingual-e5-small` están entrenados con **prefijos**:
las consultas van como `query: ...` y los documentos como `passage: ...`. Si te
olvidas del prefijo, la similitud se degrada. MiniLM, el que usamos por defecto
en esta serie, no pide esos prefijos. Si cambias de modelo, lee su ficha en el
Hub antes de indexar el corpus entero.

## Recapitulando

- Un embedding es un vector; la similitud coseno mide cercanía semántica.
- Ese es el motor de la **búsqueda densa** que usaremos para recuperar fragmentos.
- En el cuaderno 02 troceamos documentos reales y construimos un índice (NumPy y FAISS).

Siguiente: [02-chunking-e-indexado.ipynb](02-chunking-e-indexado.ipynb).
"""),
        code("""\
guardar_json(
    {
        "modelo": MODELO_EMB,
        "dim": int(codificador.dim),
        "n_frases": len(frases),
        "segundos_carga": round(t_carga, 3),
        "segundos_codificar": round(t_enc, 3),
        "varianza_pca": [float(x) for x in pca.explained_variance_ratio_],
    },
    RUTAS["resultados"] / "embeddings.json",
)
print("Metricas escritas en resultados/embeddings.json")
"""),
    ]



# ---------------------------------------------------------------------------
# 02
# ---------------------------------------------------------------------------

def nb02():
    return [
        md("""\
# 02 · Chunking e indexado

**Objetivo:** trocear un corpus en español (documentos originales del curso y de
una empresa ficticia, NubeAndina), ver cómo la estrategia de *chunking* cambia
lo que se puede recuperar, y construir un índice: primero con **NumPy** (para
entenderlo) y después con **FAISS**.

El corpus vive en `datos/corpus/` y está escrito para este taller: no hay texto
con copyright de terceros. Las cifras son deliberadamente concretas (22 días de
vacaciones, puerto 8080, alias `champion`…) para poder evaluar si una respuesta
está fundada.
"""),
        code(BOOTSTRAP),
        code("""\
# --- Mandos de este cuaderno ---
MODELO_EMB = MODELO_EMBEDDINGS_DEFECTO
TAMANO_CHUNK = 400          # caracteres, no tokens
SOLAPE = 80                 # caracteres de solape en la estrategia por defecto
ESTRATEGIA_DEFECTO = "solape"
print(f"chunk={TAMANO_CHUNK}  solape={SOLAPE}  estrategia={ESTRATEGIA_DEFECTO}")
print(f"modelo={MODELO_EMB}")
"""),
        md("""\
## 1. El corpus

Son documentos Markdown cortos (unas pocas páginas en total). En un sistema real
habría cientos o miles; aquí caben en la cabeza, que es lo que queremos para
aprender. Cargamos, contamos y mostramos un extracto.
"""),
        code("""\
documentos = cargar_corpus(RUTAS["corpus"])
tabla_docs = pd.DataFrame([
    {
        "id": d.id,
        "titulo": d.titulo,
        "caracteres": d.n_caracteres,
        "palabras": d.n_palabras,
    }
    for d in documentos
])
print(f"{len(documentos)} documentos, {tabla_docs['caracteres'].sum()} caracteres, {tabla_docs['palabras'].sum()} palabras")
tabla_docs
"""),
        code("""\
# Un extracto del reglamento de vacaciones de NubeAndina (empresa ficticia)
doc_vac = next(d for d in documentos if d.id == "nubeandina-vacaciones-y-trabajo")
print(doc_vac.titulo)
print("-" * 60)
print(doc_vac.texto[:900])
print("...")
"""),
        md("""\
## 2. Tres maneras de trocear

Un *chunk* (fragmento) es la unidad que embebemos y recuperamos. Si es **demasiado
grande**, la pregunta solo encaja con una esquina y el resto es ruido para el
LLM. Si es **demasiado pequeño**, se corta un hecho por la mitad («22 días» en
un fragmento y «laborables de vacaciones» en el siguiente) y el recuperador puede
perderlo.

Comparamos tres estrategias, con el mismo tamaño objetivo de 400 caracteres:

- **fijo**: ventanas consecutivas, sin solape.
- **solape**: igual, pero las ventanas comparten caracteres (aquí, 80). Es la
  que usaremos por defecto: amortigua los cortes.
- **párrafos**: agrupa párrafos (separados por una línea en blanco) sin pasar
  del tamaño máximo; un párrafo demasiado largo se parte.

El troceado de esta serie es por **caracteres**, no por tokens del LLM. Es más
simple de explicar y suficiente en un corpus pequeño. En producción, trocear
por tokens del *tokenizer* del modelo de embeddings (o del LLM) es más honesto
con los límites reales.
"""),
        code("""\
estrategias = {
    "fijo": dict(estrategia="fijo", tamano=TAMANO_CHUNK, solape=0),
    "solape": dict(estrategia="solape", tamano=TAMANO_CHUNK, solape=SOLAPE),
    "parrafos": dict(estrategia="parrafos", tamano=TAMANO_CHUNK, solape=SOLAPE),
}

resumenes = []
fragmentos_por = {}
for nombre, kwargs in estrategias.items():
    frags = fragmentar_documentos(documentos, **kwargs)
    fragmentos_por[nombre] = frags
    r = resumen_fragmentos(frags)
    r["nombre"] = nombre
    resumenes.append(r)
    print(f"\\n=== {nombre} ===")
    print(f"  fragmentos: {r['n_fragmentos']}  media={r['longitud_media']:.0f}  min={r['longitud_min']}  max={r['longitud_max']}")

tabla_est = pd.DataFrame(resumenes)[
    ["nombre", "n_fragmentos", "longitud_media", "longitud_mediana", "longitud_min", "longitud_max"]
]
tabla_est
"""),
        md("""\
## 3. ¿Se parte un hecho por la mitad?

Buscamos la frase «22 días laborables» (un hecho que más adelante preguntaremos)
y vemos si queda **entera** en algún fragmento, y cómo se ven los bordes de dos
fragmentos consecutivos del mismo documento.
"""),
        code("""\
HECHO = "22 días laborables"

def cubre_hecho(frags, hecho=HECHO):
    hits = [f for f in frags if hecho.lower() in f.texto.lower()]
    return hits

for nombre, frags in fragmentos_por.items():
    hits = cubre_hecho(frags)
    print(f"{nombre:10s}  fragmentos que contienen el hecho entero: {len(hits)}")
    for h in hits:
        print(f"    {h.id}  ({len(h.texto)} caracteres)")
"""),
        code("""\
# Bordes de dos fragmentos consecutivos, estrategia FIJA (sin solape), en el doc de vacaciones
frags_fijo = [f for f in fragmentos_por["fijo"] if f.doc_id == "nubeandina-vacaciones-y-trabajo"]
print(f"Fragmentos fijos del documento de vacaciones: {len(frags_fijo)}")
if len(frags_fijo) >= 2:
    a, b = frags_fijo[0], frags_fijo[1]
    print(f"\\n--- final del {a.id} (ultimos 180 caracteres) ---")
    print(a.texto[-180:])
    print(f"\\n--- inicio del {b.id} (primeros 180 caracteres) ---")
    print(b.texto[:180:])

frags_sol = [f for f in fragmentos_por["solape"] if f.doc_id == "nubeandina-vacaciones-y-trabajo"]
if len(frags_sol) >= 2:
    a, b = frags_sol[0], frags_sol[1]
    print(f"\\n--- Con SOLAPE: el inicio de {b.id} repite el final de {a.id} ---")
    print("final de A:", repr(a.texto[-80:]))
    print("inicio de B:", repr(b.texto[:80]))
"""),
        md("""\
## 4. Visualizar el tamaño de los fragmentos

Un histograma ayuda a ver si la estrategia por párrafos produce colas raras
(un fragmento enorme o muchos minúsculos).
"""),
        code("""\
fig, ax = plt.subplots(figsize=(8, 4.2))
for nombre, frags in fragmentos_por.items():
    ax.hist([len(f.texto) for f in frags], bins=15, alpha=0.45, label=nombre)
ax.set_xlabel("Longitud del fragmento (caracteres)")
ax.set_ylabel("Frecuencia")
ax.set_title("Distribución de longitudes según la estrategia")
ax.legend()
fig.tight_layout()
fig.savefig(RUTAS["resultados"] / "fig_chunking_longitudes.png", dpi=130)
plt.show()
"""),
        md("""\
## 5. Embeber e indexar (NumPy, luego FAISS)

Usamos la estrategia **solape** por defecto. El índice NumPy es un producto
interno entre la consulta (normalizada) y la matriz de fragmentos: es la
similitud coseno, sin magia. FAISS hace lo mismo aquí (`IndexFlatIP`, búsqueda
exacta). En un corpus de decenas de fragmentos no hay ganancia de tiempo; FAISS
empieza a importar cuando hay cientos de miles o millones de vectores, o cuando
pasas a índices aproximados (IVF, HNSW). En este laboratorio nos basta ver que
**los resultados coinciden**.
"""),
        code("""\
fragmentos = fragmentos_por[ESTRATEGIA_DEFECTO]
print(f"Indexando {len(fragmentos)} fragmentos ({ESTRATEGIA_DEFECTO})")

codificador = Codificador(MODELO_EMB, dispositivo_destino=str(DEVICE))
t0 = time.perf_counter()
vectores = codificador.codificar([f.texto for f in fragmentos], lote=16, progreso=True)
t_emb = time.perf_counter() - t0
print(f"Embeddings: {vectores.shape} en {t_emb:.2f} s")

indice_np = IndiceNumpy(vectores, fragmentos)
indice_faiss = IndiceFAISS(vectores, fragmentos)
print("Indices listos (NumPy y FAISS).")
"""),
        code("""\
consulta = "¿Cuántos días de vacaciones tiene un empleado de NubeAndina?"
qv = codificador.codificar([consulta], progreso=False)[0]

top_np = indice_np.buscar(qv, k=4)
top_fa = indice_faiss.buscar(qv, k=4)

def tabla_hits(resultados):
    return pd.DataFrame([
        {
            "rango": r.rango,
            "puntuacion": round(r.puntuacion, 4),
            "id": r.fragmento.id,
            "doc": r.fragmento.doc_id,
            "extracto": r.fragmento.texto[:140].replace("\\n", " ") + "...",
        }
        for r in resultados
    ])

print("Consulta:", consulta)
print("\\nNumPy:")
display_np = tabla_hits(top_np)
print(display_np.to_string(index=False))
print("\\nFAISS:")
display_fa = tabla_hits(top_fa)
print(display_fa.to_string(index=False))

ids_np = [r.fragmento.id for r in top_np]
ids_fa = [r.fragmento.id for r in top_fa]
print("\\n¿Mismos identificadores, en el mismo orden?", ids_np == ids_fa)
"""),
        md("""\
Los dos índices deberían devolver los mismos fragmentos en el mismo orden (búsqueda
exacta, mismos vectores). Guardamos FAISS y la copia NumPy en `modelos/` para
no volver a embeber el corpus en los cuadernos siguientes, salvo que cambies
el troceado.
"""),
        code("""\
ruta_faiss = indice_faiss.guardar(RUTAS["modelos"] / "indice_faiss")
ruta_np = indice_np.guardar(RUTAS["modelos"] / "indice_numpy")
guardar_json(
    {
        "estrategia": ESTRATEGIA_DEFECTO,
        "tamano": TAMANO_CHUNK,
        "solape": SOLAPE,
        "modelo_embeddings": MODELO_EMB,
        "n_documentos": len(documentos),
        "n_fragmentos": len(fragmentos),
        "dim": int(vectores.shape[1]),
        "segundos_embeber": round(t_emb, 3),
        "resumenes_estrategias": resumenes,
        "consulta_demo": consulta,
        "ids_numpy": ids_np,
        "ids_faiss": ids_fa,
        "coinciden": ids_np == ids_fa,
    },
    RUTAS["resultados"] / "indexado.json",
)
print("Indices guardados en:")
print(" ", ruta_faiss)
print(" ", ruta_np)
print("Listo. Siguiente cuaderno: 03-recuperacion-y-busqueda.")
"""),
        md("""\
## Recapitulando

- El *chunking* no es un detalle: corta o preserva hechos.
- El solape es un seguro barato contra los cortes.
- Un índice denso, en su forma más simple, es «matriz de vectores + coseno».
- FAISS, en modo exacto, replica eso y escala mejor cuando el corpus crece.

Siguiente: [03-recuperacion-y-busqueda.ipynb](03-recuperacion-y-busqueda.ipynb).
"""),
    ]


# ---------------------------------------------------------------------------
# 03
# ---------------------------------------------------------------------------

def nb03():
    return [
        md("""\
# 03 · Recuperación y búsqueda

**Objetivo:** comparar tres maneras de recuperar fragmentos —**BM25** (léxica),
**densa** (embeddings + FAISS) e **híbrida** (fusión RRF)— sobre un conjunto
pequeño de preguntas hechas a mano. Medimos *recall@k* y MRR. Al final,
opcionalmente, un *cross-encoder* reordena los candidatos.

BM25 puntúa por solapamiento de términos (con un ajuste por longitud y por
rareza de la palabra). Es excelente cuando la pregunta trae un identificador
literal (`ci-retencion.yml`, `southamerica-west1`, `/salud`). La búsqueda densa
gana cuando la pregunta **parafrasea**. La híbrida intenta quedarse con lo mejor
de las dos, fusionando rangos (Reciprocal Rank Fusion), no puntuaciones crudas,
porque un 12 de BM25 y un 0,42 de coseno no están en la misma escala.
"""),
        code(BOOTSTRAP),
        code("""\
# --- Mandos de este cuaderno ---
MODELO_EMB = MODELO_EMBEDDINGS_DEFECTO
K = 5
K_RRF = 60          # constante típica de Reciprocal Rank Fusion
USAR_RERANKER = not MODO_RAPIDO   # el cross-encoder es opcional y está en inglés
print(f"k={K}  k_rrf={K_RRF}  reranker={USAR_RERANKER}")
"""),
        md("""\
## 1. Cargar el índice y las preguntas

Reutilizamos el índice del cuaderno 02. Si no estuviera, se puede reconstruir;
aquí lo damos por escrito en `modelos/`. El modelo de embeddings sí hay que
cargarlo: hace falta embeber **las preguntas**.
"""),
        code("""\
indice = IndiceFAISS.cargar(RUTAS["modelos"] / "indice_faiss")
fragmentos = indice.fragmentos
indice_bm25 = IndiceBM25(fragmentos)
codificador = Codificador(MODELO_EMB, dispositivo_destino=str(DEVICE))
preguntas = cargar_preguntas(RUTAS["datos"] / "preguntas.json")
preguntas_hecho = [p for p in preguntas if p.get("tipo") != "no_esta"]
print(f"Fragmentos: {len(fragmentos)}")
print(f"Preguntas: {len(preguntas)} (evaluables para recall: {len(preguntas_hecho)})")
pd.DataFrame(preguntas)[["id", "tipo", "pregunta"]].head(8)
"""),
        md("""\
## 2. Una pregunta, tres listas

Miramos de cerca una pregunta que se puede parafrasear y otra que trae un
identificador literal. Para cada una listamos el top-k de BM25, el denso y el
híbrido.
"""),
        code("""\
def buscar_denso(pregunta, k=K):
    qv = codificador.codificar([pregunta], progreso=False)[0]
    return indice.buscar(qv, k=k)

def buscar_bm25(pregunta, k=K):
    return indice_bm25.buscar(pregunta, k=k)

def buscar_hibrido(pregunta, k=K):
    # Un poco más de candidatos por lista, luego fusionamos.
    denso = buscar_denso(pregunta, k=max(k, 8))
    lex = buscar_bm25(pregunta, k=max(k, 8))
    return fusion_rrf([denso, lex], k=k, k_rrf=K_RRF)

def mostrar(pregunta, k=4):
    print("=" * 70)
    print(pregunta)
    for nombre, fn in [("BM25", buscar_bm25), ("denso", buscar_denso), ("hibrido", buscar_hibrido)]:
        hits = fn(pregunta, k=k)
        print(f"\\n  {nombre}:")
        for r in hits:
            extracto = r.fragmento.texto.replace("\\n", " ")[:110]
            print(f"    {r.rango}. {r.puntuacion:.3f}  {r.fragmento.id}  {extracto}...")

mostrar("¿Cuántos días de vacaciones tiene un empleado de NubeAndina?")
mostrar("¿Cómo se llama el archivo del workflow de GitHub Actions del curso?")
"""),
        md("""\
## 3. Métricas: *recall@k* y MRR

*Recall@k* (aquí, con un conjunto de documentos relevantes por pregunta): vale 1
si **al menos un** documento de referencia aparece en los k primeros, 0 si no.
Es una medida de «¿cayó lo que buscábamos en la ventana que le vamos a dar al
LLM?».

**MRR** (*mean reciprocal rank*) es la media de 1/r, donde r es el rango
del primer documento relevante (y 0 si no aparece). Premia que lo bueno quede
arriba, no solo «en algún sitio del top-k».

El conjunto es pequeño y está hecho a mano: las cifras no son un *benchmark*
publicado, son una brújula para este laboratorio.
"""),
        code("""\
def evaluar(fn, nombre, k=K):
    res = evaluar_recuperacion(preguntas_hecho, fn, k=k, clave_oro="docs_relevantes", usar_doc_id=True)
    print(f"{nombre:10s}  recall@{k}={res[f'recall@{k}']:.3f}  MRR={res['mrr']:.3f}  n={res['n_evaluadas']}")
    return res

eval_bm25 = evaluar(buscar_bm25, "BM25")
eval_denso = evaluar(buscar_denso, "denso")
eval_hib = evaluar(buscar_hibrido, "hibrido")

tabla_met = pd.DataFrame([
    {"metodo": "BM25", f"recall@{K}": eval_bm25[f"recall@{K}"], "MRR": eval_bm25["mrr"]},
    {"metodo": "denso", f"recall@{K}": eval_denso[f"recall@{K}"], "MRR": eval_denso["mrr"]},
    {"metodo": "hibrido", f"recall@{K}": eval_hib[f"recall@{K}"], "MRR": eval_hib["mrr"]},
])
tabla_met
"""),
        code("""\
# recall@k para varios k, misma comparación
ks = [1, 3, 5, 8]
filas_k = []
for k in ks:
    for nombre, fn in [("BM25", buscar_bm25), ("denso", buscar_denso), ("hibrido", buscar_hibrido)]:
        r = evaluar_recuperacion(preguntas_hecho, fn, k=k, clave_oro="docs_relevantes")
        filas_k.append({"k": k, "metodo": nombre, "recall": r[f"recall@{k}"], "mrr": r["mrr"]})
tabla_k = pd.DataFrame(filas_k)

fig, ax = plt.subplots(figsize=(7.5, 4.2))
for nombre, sub in tabla_k.groupby("metodo"):
    ax.plot(sub["k"], sub["recall"], marker="o", label=nombre)
ax.set_xlabel("k")
ax.set_ylabel("recall@k")
ax.set_title("Recall@k según el método de recuperación")
ax.set_xticks(ks)
ax.legend()
fig.tight_layout()
fig.savefig(RUTAS["resultados"] / "fig_recall_at_k.png", dpi=130)
plt.show()

fig, ax = plt.subplots(figsize=(6, 4.0))
mrrs = tabla_met.set_index("metodo")["MRR"]
ax.bar(mrrs.index, mrrs.values, color=["#1f77b4", "#2ca02c", "#ff7f0e"])
ax.set_ylim(0, 1.05)
ax.set_ylabel("MRR")
ax.set_title("MRR (primer documento relevante)")
for i, v in enumerate(mrrs.values):
    ax.text(i, v + 0.03, f"{v:.2f}", ha="center")
fig.tight_layout()
fig.savefig(RUTAS["resultados"] / "fig_mrr.png", dpi=130)
plt.show()
tabla_k
"""),
        md("""\
## 4. Reordenar con un *cross-encoder* (opcional)

Un *bi-encoder* (el de embeddings) codifica la pregunta y el fragmento **por
separado**, y por eso puede indexar el corpus de antemano. Un *cross-encoder*
lee el par (pregunta, fragmento) junto y suele ordenar mejor, pero no escala a
todo el corpus: se aplica solo a los k candidatos ya recuperados.

El modelo por defecto, `cross-encoder/ms-marco-MiniLM-L-6-v2`, está entrenado
sobre MS MARCO (**inglés**). En un corpus en español puede ayudar un poco o no
ayudar nada: lo medimos, no lo damos por sentado. En modo rápido esta celda se
salta la descarga.
"""),
        code("""\
eval_rerank = None
reranker = None
if USAR_RERANKER:
    try:
        t0 = time.perf_counter()
        reranker = Reranker(MODELO_RERANKER_DEFECTO, dispositivo_destino=str(DEVICE))
        print(f"Reranker cargado en {time.perf_counter() - t0:.1f} s: {reranker.nombre}")

        def buscar_rerank(pregunta, k=K):
            cand = buscar_hibrido(pregunta, k=max(8, k))
            return reranker.reordenar(pregunta, cand, k=k)

        eval_rerank = evaluar(buscar_rerank, "hibrido+rerank")
    except Exception as exc:
        print(f"Reranker no disponible ({type(exc).__name__}: {exc}). Seguimos sin el.")
        reranker = None
else:
    print("Modo rapido: se omite el cross-encoder (USAR_RERANKER=False).")
    print("Pon USAR_RERANKER = True y reejecuta si quieres medirlo.")
"""),
        md("""\
## 5. Dónde falla cada método

Una tabla con el primer documento recuperado ayuda a ver errores típicos: un
identificador literal que BM25 clava, o una paráfrasis que la densa entiende
mejor.
"""),
        code("""\
filas = []
for p in preguntas_hecho:
    oro = set(p.get("docs_relevantes") or [])
    recs = {
        "BM25": buscar_bm25(p["pregunta"], k=K),
        "denso": buscar_denso(p["pregunta"], k=K),
        "hibrido": buscar_hibrido(p["pregunta"], k=K),
    }
    fila = {"id": p["id"], "oro": ", ".join(sorted(oro)), "pregunta": p["pregunta"][:80]}
    for nombre, hits in recs.items():
        ids = [h.fragmento.doc_id for h in hits]
        fila[nombre + "_top"] = ids[0] if ids else ""
        fila[nombre + "_ok"] = any(i in oro for i in ids)
    filas.append(fila)
tabla_err = pd.DataFrame(filas)
# Preguntas donde los metodos no coinciden en el acierto
discrepan = tabla_err[
    tabla_err["BM25_ok"] != tabla_err["denso_ok"]
]
print("Preguntas en las que BM25 y la busqueda densa no coinciden en el acierto @k:")
if len(discrepan) == 0:
    print("  (ninguna en este conjunto; prueba a bajar k)")
else:
    print(discrepan[["id", "oro", "BM25_top", "BM25_ok", "denso_top", "denso_ok"]].to_string(index=False))
tabla_err[["id", "oro", "BM25_ok", "denso_ok", "hibrido_ok", "BM25_top", "denso_top"]]
"""),
        code("""\
payload = {
    "k": K,
    "n_preguntas": len(preguntas_hecho),
    "bm25": {"recall": eval_bm25[f"recall@{K}"], "mrr": eval_bm25["mrr"]},
    "denso": {"recall": eval_denso[f"recall@{K}"], "mrr": eval_denso["mrr"]},
    "hibrido": {"recall": eval_hib[f"recall@{K}"], "mrr": eval_hib["mrr"]},
    "rerank": (
        {"recall": eval_rerank[f"recall@{K}"], "mrr": eval_rerank["mrr"]}
        if eval_rerank is not None else None
    ),
    "recall_por_k": filas_k,
}
guardar_json(payload, RUTAS["resultados"] / "recuperacion.json")
print("Metricas escritas en resultados/recuperacion.json")
print("Siguiente cuaderno: 04-generacion-con-llm-local.")
"""),
        md("""\
## Recapitulando

- BM25 y la búsqueda densa se equivocan en sitios distintos: por eso se combinan.
- *Recall@k* responde «¿el contexto llegó al LLM?»; MRR, «¿qué tan arriba?».
- Un *reranker* es un lujo que se aplica a pocos candidatos, no al corpus entero.

Siguiente: [04-generacion-con-llm-local.ipynb](04-generacion-con-llm-local.ipynb).
"""),
    ]



# ---------------------------------------------------------------------------
# 04
# ---------------------------------------------------------------------------

def nb04():
    return [
        md("""\
# 04 · Generación con un LLM local: con RAG y sin RAG

**Objetivo:** cargar un modelo instructivo **pequeño**, pensado para CPU
(`Qwen/Qwen2.5-0.5B-Instruct`, unos 0,5B de parámetros), y comparar la misma
pregunta en dos condiciones:

- **Sin RAG:** el modelo responde «de memoria». Con una empresa ficticia y con
  convenios del curso, es fácil que **alucine** (invente 30 días de vacaciones,
  un puerto 8000, un nombre que no está en el corpus…).
- **Con RAG:** recuperamos k fragmentos, se los pasamos en el *prompt* y le
  pedimos que se atenga a ellos y cite fuentes. Si no está en el contexto, debe
  abstenerse.

Este modelo es didáctico, no es un LLM de producción. Se equivocará al redactar
incluso con buen contexto. Lo que nos importa es ver el contraste: sin fuentes,
inventa; con fuentes, se acerca a los hechos o se calla.

Si el 0,5B no cabe en memoria, `rag_utils` intenta un modelo de reserva
(`SmolLM2-135M-Instruct`), más pobre en español pero más ligero.
"""),
        code(BOOTSTRAP),
        code("""\
# --- Mandos de este cuaderno ---
MODELO_EMB = MODELO_EMBEDDINGS_DEFECTO
MODELO_LLM = MODELO_LLM_DEFECTO
K = 4
MAX_NUEVOS = 64 if MODO_RAPIDO else 120
# En modo rapido basta un puñado de preguntas representativas.
IDS_DEMO = ["q11", "q13", "q03", "q19"] if MODO_RAPIDO else ["q11", "q13", "q03", "q05", "q10", "q19", "q20"]
print(f"LLM={MODELO_LLM}  k={K}  max_nuevos={MAX_NUEVOS}")
print("Preguntas de esta demo:", IDS_DEMO)
"""),
        md("""\
## 1. Índice, embeddings y LLM

Cargamos el índice del cuaderno 02, el codificador y el LLM. La primera vez, el
LLM ocupa del orden de 1 GB en disco (más si hay varios archivos de pesos). En
CPU, cada respuesta puede tardar **varios segundos**. Es normal.
"""),
        code("""\
indice = IndiceFAISS.cargar(RUTAS["modelos"] / "indice_faiss")
indice_bm25 = IndiceBM25(indice.fragmentos)
codificador = Codificador(MODELO_EMB, dispositivo_destino=str(DEVICE))
preguntas = cargar_preguntas(RUTAS["datos"] / "preguntas.json")
por_id = {p["id"]: p for p in preguntas}
demo = [por_id[i] for i in IDS_DEMO if i in por_id]
print(f"Fragmentos indexados: {len(indice.fragmentos)}")
print(f"Preguntas en la demo: {len(demo)}")

t0 = time.perf_counter()
generador = GeneradorLocal(
    MODELO_LLM,
    dispositivo_destino=str(DEVICE),
    reserva=MODELO_LLM_RESERVA,
)
t_llm = time.perf_counter() - t0
print(f"LLM cargado: {generador.nombre}  dtype={generador.dtype_nombre}  en {t_llm:.1f} s")
"""),
        md("""\
## 2. La plantilla del *prompt*

Con RAG, el sistema le prohíbe inventar y le pide citas `[doc::#n]`. El usuario
recibe el contexto (fragmentos ya seleccionados) y la pregunta. Sin RAG, solo
va la pregunta: es el control de la comparación.
"""),
        code("""\
# Un ejemplo de prompt CON contexto, sin generar todavía
pregunta_ejemplo = demo[0]["pregunta"]
qv = codificador.codificar([pregunta_ejemplo], progreso=False)[0]
hits = indice.buscar(qv, k=K)
mensajes_con = construir_mensajes(pregunta_ejemplo, hits, con_rag=True)
mensajes_sin = construir_mensajes(pregunta_ejemplo, None, con_rag=False)

print("===== SISTEMA (con RAG) =====")
print(mensajes_con[0]["content"])
print("\\n===== USUARIO (con RAG, recortado a 1200 caracteres) =====")
print(mensajes_con[1]["content"][:1200])
print("\\n===== USUARIO (sin RAG) =====")
print(mensajes_sin[1]["content"])
"""),
        md("""\
## 3. La misma pregunta, con y sin RAG

Para cada pregunta de la demo generamos las dos respuestas. Debajo medimos si
los **hechos** de referencia aparecen en el texto (una comprobación simple, no
un juez semántico) y si, en las preguntas «no está en el corpus», el modelo se
abstiene.
"""),
        code("""\
pipeline = PipelineRAG(
    codificador=codificador,
    indice_denso=indice,
    indice_bm25=indice_bm25,
    generador=generador,
    k=K,
    metodo="hibrido",
)

filas = []
for p in demo:
    print("=" * 70)
    print(f"{p['id']}: {p['pregunta']}")
    sin = pipeline.preguntar(p["pregunta"], con_rag=False, max_nuevos=MAX_NUEVOS)
    con = pipeline.preguntar(p["pregunta"], con_rag=True, max_nuevos=MAX_NUEVOS)
    print("\\n--- SIN RAG ({:.1f} s) ---".format(sin["latencias_s"]["total"]))
    print(sin["respuesta"])
    print("\\n--- CON RAG ({:.1f} s, fuentes: {}) ---".format(
        con["latencias_s"]["total"], ", ".join(con["docs_fuentes"])
    ))
    print(con["respuesta"])
    if p.get("tipo") == "no_esta":
        cob_sin, cob_con = float(parece_abstencion(sin["respuesta"])), float(parece_abstencion(con["respuesta"]))
        det_sin = {"abstencion": bool(cob_sin)}
        det_con = {"abstencion": bool(cob_con)}
    else:
        det_sin = contiene_hechos(sin["respuesta"], p.get("hechos") or [])
        det_con = contiene_hechos(con["respuesta"], p.get("hechos") or [])
        cob_sin, cob_con = det_sin["cobertura"], det_con["cobertura"]
    print(f"\\nCobertura de hechos  sin RAG={cob_sin:.2f}  con RAG={cob_con:.2f}")
    filas.append({
        "id": p["id"],
        "tipo": p.get("tipo"),
        "pregunta": p["pregunta"],
        "respuesta_sin_rag": sin["respuesta"],
        "respuesta_con_rag": con["respuesta"],
        "fuentes": con["docs_fuentes"],
        "cobertura_sin": cob_sin,
        "cobertura_con": cob_con,
        "latencia_sin_s": sin["latencias_s"]["total"],
        "latencia_con_s": con["latencias_s"]["total"],
        "latencia_recuperacion_s": con["latencias_s"]["recuperacion"],
        "latencia_generacion_s": con["latencias_s"]["generacion"],
        "hechos": p.get("hechos") or [],
    })

tabla = pd.DataFrame(filas)
tabla[["id", "tipo", "cobertura_sin", "cobertura_con", "latencia_sin_s", "latencia_con_s", "fuentes"]]
"""),
        md("""\
## 4. Lectura de los resultados

En las preguntas de tipo «hecho», una cobertura más alta **con RAG** es la señal
que buscamos: el texto menciona las cifras o los nombres del corpus. En las de
tipo «no_esta» (teléfono de una cafetería que no existe en los documentos, o un
sueldo que no se publica), el éxito es **abstenerse**, no acertar un número.

El modelo de 0,5B a veces redacta torpe o se deja un hecho aunque el fragmento
esté en el *prompt*. Eso no anula la lección: el fallo pasa a ser de generación,
no de desconocimiento total. En producción se usaría un modelo más capaz, o una
API, **con el mismo patrón de recuperación**.
"""),
        code("""\
fig, ax = plt.subplots(figsize=(7.2, 4.0))
x = np.arange(len(tabla))
w = 0.35
ax.bar(x - w/2, tabla["cobertura_sin"].fillna(0), w, label="sin RAG", color="#d62728")
ax.bar(x + w/2, tabla["cobertura_con"].fillna(0), w, label="con RAG", color="#2ca02c")
ax.set_xticks(x)
ax.set_xticklabels(tabla["id"], rotation=0)
ax.set_ylim(0, 1.15)
ax.set_ylabel("Cobertura de hechos / abstención")
ax.set_title("Misma pregunta, con y sin RAG")
ax.legend()
fig.tight_layout()
fig.savefig(RUTAS["resultados"] / "fig_con_sin_rag.png", dpi=130)
plt.show()

print(
    "Cobertura media  sin RAG: {:.2f}   con RAG: {:.2f}".format(
        tabla["cobertura_sin"].mean(), tabla["cobertura_con"].mean()
    )
)
print(
    "Latencia media   sin RAG: {:.1f}s  con RAG: {:.1f}s (recup {:.2f}s + gen {:.1f}s)".format(
        tabla["latencia_sin_s"].mean(),
        tabla["latencia_con_s"].mean(),
        tabla["latencia_recuperacion_s"].mean(),
        tabla["latencia_generacion_s"].mean(),
    )
)
"""),
        md("""\
## 5. Alternativas por API (opcionales, de pago)

Esta serie **no exige ninguna API de pago**. Si en tu práctica o en un proyecto
real quieres un generador más capaz, el *pipeline* es el mismo: recuperas
fragmentos aquí (CPU, FAISS, tu corpus) y cambias solo el paso de generación
por un cliente de OpenAI, Gemini, Claude, o un *endpoint* de tu empresa. El
contexto y las citas siguen siendo tuyos. Cuida no enviar datos privados a un
proveedor que no esté acordado (en el corpus de NubeAndina, de hecho, está
prohibido).
"""),
        code("""\
guardar_json(
    {
        "modelo_llm": generador.nombre,
        "modelo_embeddings": MODELO_EMB,
        "k": K,
        "max_nuevos": MAX_NUEVOS,
        "segundos_carga_llm": round(t_llm, 3),
        "cobertura_media_sin": float(tabla["cobertura_sin"].mean()),
        "cobertura_media_con": float(tabla["cobertura_con"].mean()),
        "latencia_media_sin_s": float(tabla["latencia_sin_s"].mean()),
        "latencia_media_con_s": float(tabla["latencia_con_s"].mean()),
        "detalle": filas,
    },
    RUTAS["resultados"] / "generacion.json",
)
print("Resultados escritos en resultados/generacion.json")
print("Siguiente cuaderno: 05-pipeline-completo-y-evaluacion.")
"""),
        md("""\
## Recapitulando

- El *prompt* es parte del sistema: «responde solo con el contexto» no es un adorno.
- Sin RAG, un LLM pequeño (y muchos grandes) inventan políticas y cifras.
- Con RAG, la calidad depende de la recuperación **y** de que el modelo respete
  el contexto. Por eso evaluamos las dos cosas.

Siguiente: [05-pipeline-completo-y-evaluacion.ipynb](05-pipeline-completo-y-evaluacion.ipynb).
"""),
    ]


# ---------------------------------------------------------------------------
# 05
# ---------------------------------------------------------------------------

def nb05():
    return [
        md("""\
# 05 · Pipeline completo, evaluación y producción

**Objetivo:** dejar un objeto `PipelineRAG` reutilizable (el de `src/rag_utils.py`),
medir fidelidad y latencia por etapa, jugar con los **mandos** (tamaño de
*chunk*, *k*) y apuntar lo que cambia cuando esto sale del cuaderno y entra en
un servicio: base vectorial, caché, monitorización, evaluación continua y
guardarraíles.

Si ya ejecutaste el cuaderno 04, reutilizamos sus ejemplos de generación. La
búsqueda de hiperparámetros de recuperación **no necesita el LLM** y se puede
repetir barato.
"""),
        code(BOOTSTRAP),
        code("""\
# --- Mandos de este cuaderno ---
MODELO_EMB = MODELO_EMBEDDINGS_DEFECTO
K = 4
MAX_NUEVOS = 64 if MODO_RAPIDO else 120
CARGAR_LLM = True          # pon False si solo quieres el estudio de chunking / k
print(f"k={K}  max_nuevos={MAX_NUEVOS}  cargar_llm={CARGAR_LLM}")
"""),
        md("""\
## 1. El *pipeline* como un objeto

`PipelineRAG.preguntar(pregunta)` hace recuperación + generación y devuelve
respuesta, fuentes y latencias. Es la unidad que más adelante envolverías en
una ruta HTTP (por ejemplo, la misma API del curso).
"""),
        code("""\
documentos = cargar_corpus(RUTAS["corpus"])
preguntas = cargar_preguntas(RUTAS["datos"] / "preguntas.json")
preguntas_hecho = [p for p in preguntas if p.get("tipo") != "no_esta"]
codificador = Codificador(MODELO_EMB, dispositivo_destino=str(DEVICE))
indice = IndiceFAISS.cargar(RUTAS["modelos"] / "indice_faiss")
indice_bm25 = IndiceBM25(indice.fragmentos)

generador = None
if CARGAR_LLM:
    t0 = time.perf_counter()
    generador = GeneradorLocal(MODELO_LLM_DEFECTO, dispositivo_destino=str(DEVICE), reserva=MODELO_LLM_RESERVA)
    print(f"LLM: {generador.nombre}  carga {time.perf_counter()-t0:.1f}s")
else:
    print("LLM no cargado (CARGAR_LLM=False).")

pipeline = PipelineRAG(
    codificador=codificador,
    indice_denso=indice,
    indice_bm25=indice_bm25,
    generador=generador,
    k=K,
    metodo="hibrido",
)

# Recuperación suelta (sin generar): barata y suficiente para inspeccionar fuentes
q_demo = "¿Quién es la DPO de NubeAndina y cuál es la longitud mínima de las contraseñas?"
hits = pipeline.recuperar(q_demo, k=K)
print("Pregunta:", q_demo)
for r in hits:
    print(f"  {r.rango}. {r.puntuacion:.3f}  {r.fragmento.id}")
"""),
        code("""\
if generador is not None:
    out = pipeline.preguntar(q_demo, con_rag=True, max_nuevos=MAX_NUEVOS)
    print("Respuesta:")
    print(out["respuesta"])
    print("\\nLatencias (s):", out["latencias_s"])
else:
    print("Sin LLM: se omite la generacion de demostracion.")
    out = None
"""),
        md("""\
## 2. Mandos: tamaño de *chunk* y *k*

Cambiamos el troceado y el *k* midiendo solo **recuperación** (*recall@5* y MRR)
sobre el conjunto hecho a mano. Así se ve el recorte de un hecho o el ruido de
un *k* demasiado grande **sin** pagar la generación en cada punto.

Un *k* alto mete más contexto en el *prompt*: aumenta la probabilidad de que el
hecho viaje, pero también el ruido y la latencia del LLM (y, en modelos pequeños,
la distracción).
"""),
        code("""\
def construir_indice(tamano, solape=80, estrategia="solape"):
    frags = fragmentar_documentos(documentos, estrategia=estrategia, tamano=tamano, solape=solape)
    vec = codificador.codificar([f.texto for f in frags], lote=16, progreso=False)
    return IndiceFAISS(vec, frags), frags

filas_chunk = []
for tam in [200, 400, 800]:
    ind, frags = construir_indice(tam, solape=80)
    def _buscador(pregunta, k, _ind=ind):
        qv = codificador.codificar([pregunta], progreso=False)[0]
        return _ind.buscar(qv, k=k)
    ev = evaluar_recuperacion(preguntas_hecho, _buscador, k=5)
    filas_chunk.append({
        "tamano_chunk": tam,
        "n_fragmentos": len(frags),
        "recall@5": ev["recall@5"],
        "mrr": ev["mrr"],
    })
    print(f"chunk={tam:4d}  n={len(frags):3d}  recall@5={ev['recall@5']:.3f}  MRR={ev['mrr']:.3f}")

tabla_chunk = pd.DataFrame(filas_chunk)

# k, con el indice por defecto del cuaderno 02
filas_k = []
def buscador_default(pregunta, k):
    qv = codificador.codificar([pregunta], progreso=False)[0]
    return indice.buscar(qv, k=k)

for k in [1, 2, 3, 5, 8]:
    ev = evaluar_recuperacion(preguntas_hecho, buscador_default, k=k)
    filas_k.append({"k": k, "recall": ev[f"recall@{k}"], "mrr": ev["mrr"]})
tabla_k = pd.DataFrame(filas_k)

fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.8))
axes[0].plot(tabla_chunk["tamano_chunk"], tabla_chunk["recall@5"], marker="o", label="recall@5")
axes[0].plot(tabla_chunk["tamano_chunk"], tabla_chunk["mrr"], marker="s", label="MRR")
axes[0].set_xlabel("Tamaño de chunk (caracteres)")
axes[0].set_title("Efecto del tamaño de fragmento")
axes[0].legend()
axes[1].plot(tabla_k["k"], tabla_k["recall"], marker="o", label="recall@k")
axes[1].plot(tabla_k["k"], tabla_k["mrr"], marker="s", label="MRR")
axes[1].set_xlabel("k")
axes[1].set_title("Efecto de k (índice por defecto)")
axes[1].legend()
fig.tight_layout()
fig.savefig(RUTAS["resultados"] / "fig_mandos_chunk_k.png", dpi=130)
plt.show()
tabla_chunk
"""),
        md("""\
## 3. Fidelidad y latencia (si el LLM está cargado)

Releemos `resultados/generacion.json` si existe (cuaderno 04) y, si hay
generador, evaluamos un subconjunto breve para obtener latencias por etapa en
este proceso.
"""),
        code("""\
ruta_gen = RUTAS["resultados"] / "generacion.json"
previo = cargar_json(ruta_gen) if ruta_gen.exists() else None
if previo:
    print("Resultados del cuaderno 04:")
    print(f"  modelo: {previo['modelo_llm']}")
    print(f"  cobertura media sin RAG: {previo['cobertura_media_sin']:.2f}")
    print(f"  cobertura media con RAG: {previo['cobertura_media_con']:.2f}")
    print(f"  latencia media con RAG:  {previo['latencia_media_con_s']:.1f} s")

eval_fid = None
if generador is not None:
    ids_eval = ["q11", "q13", "q19"] if MODO_RAPIDO else ["q11", "q13", "q03", "q10", "q19"]
    sub = [p for p in preguntas if p["id"] in ids_eval]
    eval_fid = evaluar_fidelidad(sub, pipeline, con_rag=True, max_nuevos=MAX_NUEVOS, k=K)
    print(f"\\nEvaluacion breve con RAG: cobertura media={eval_fid['cobertura_media']:.2f}  ok={eval_fid['n_ok']}/{eval_fid['n']}")
    print(f"Latencia media total: {eval_fid['latencia_media_s']:.1f} s")
    lat_r = [d["latencias_s"]["recuperacion"] for d in eval_fid["detalle"]]
    lat_g = [d["latencias_s"]["generacion"] for d in eval_fid["detalle"]]
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    ax.bar(["recuperacion", "generacion"], [float(np.mean(lat_r)), float(np.mean(lat_g))], color=["#1f77b4", "#ff7f0e"])
    ax.set_ylabel("segundos (media)")
    ax.set_title("Latencia por etapa (CPU, LLM local)")
    fig.tight_layout()
    fig.savefig(RUTAS["resultados"] / "fig_latencia_etapas.png", dpi=130)
    plt.show()
else:
    print("Sin LLM: no se recalcula fidelidad. Usa los numeros del cuaderno 04.")
"""),
        md("""\
## 4. De este cuaderno a producción (notas de MLOps)

Lo que has montado es un RAG mínimo, reproducible en CPU. En un servicio real
cambian, sobre todo, el **sitio** donde vive cada pieza y la **disciplina** con
la que la mides.

**Almacén de vectores.** FAISS en un proceso (o NumPy, en el laboratorio) vale
para un corpus pequeño. Cuando hay muchos documentos, varios servicios y
actualizaciones, entra un almacén: `pgvector` en Postgres, Chroma, Qdrant,
Vertex AI Vector Search, OpenSearch, etc. El contrato no cambia: guardas
vectores + metadatos (identificador, documento, fechas, permisos) y preguntas
por los k más cercanos.

**Actualización del índice.** Si el reglamento cambia el viernes, el índice del
jueves está mal. Hace falta una tubería que detecte documentos nuevos o
editados, los vuelva a trocear y los upsert-e. Versiona el corpus y el índice
como versionas un modelo.

**Caché.** Las preguntas repetidas («¿cuál es el puerto de la API?») no deberían
volver a embeberse ni a llamarse al LLM cada vez. Se cachea el embedding de la
consulta, y a veces la respuesta, con una caducidad ligada a la versión del
índice.

**Evaluación continua.** El `preguntas.json` de este taller es un *golden set*
en miniatura. En producción se mantiene un conjunto vivo: *recall@k*, cobertura
de hechos, tasa de abstención, *feedback* de usuarios (pulgar abajo) y, si se
quiere, métricas tipo fidelidad/relevancia con un juez (otro modelo o un
humano). Un cambio de *chunk*, de *k* o de modelo se acepta o se rechaza con
esas cifras, no a ojo.

**Latencia y coste.** Recupera en milisegundos; genera en cientos de
milisegundos o en segundos (como has visto en CPU). Mide por etapa. Un modelo
por API será más capaz y más caro; el contexto que le envías sigue siendo tu
responsabilidad (y tu factura, porque pagas tokens de *prompt*).

**Guardarraíles.** «Responde solo con el contexto» es el primero. Otros: no
exfiltrar secretos, no obedecer instrucciones escondidas **dentro de un
documento** (*prompt injection*), filtrar PII, limitar temas, registrar la
fuente de cada afirmación. El corpus de NubeAndina prohíbe mandar datos reales
de cooperativas a una API pública: esa norma también es un guardarraíl de diseño.

**Observabilidad.** Logs con el identificador de la pregunta, los fragmentos
servidos, el modelo, las latencias y un hash del *prompt*. Sin eso, un fallo en
producción («desde el martes responde mal») no se diagnostica.

**No es la única pieza.** RAG convive con el registro de modelos (MLflow, alias
`champion`), con el contenedor (`retencion-api:local`), con CI y con un
despliegue que se pueda revertir. El recuperador y el generador también son
modelos: se promocionan, se miden y se retiran como el resto.
"""),
        code("""\
guardar_json(
    {
        "k": K,
        "estudio_chunk": filas_chunk,
        "estudio_k": filas_k,
        "generacion_previa": {
            "cobertura_media_sin": previo["cobertura_media_sin"] if previo else None,
            "cobertura_media_con": previo["cobertura_media_con"] if previo else None,
            "modelo_llm": previo["modelo_llm"] if previo else None,
        } if previo else None,
        "fidelidad_breve": (
            {
                "n": eval_fid["n"],
                "cobertura_media": eval_fid["cobertura_media"],
                "n_ok": eval_fid["n_ok"],
                "latencia_media_s": eval_fid["latencia_media_s"],
            }
            if eval_fid is not None else None
        ),
    },
    RUTAS["resultados"] / "pipeline.json",
)
print("Metricas escritas en resultados/pipeline.json")
print("Siguiente cuaderno: 06-ejercicios.")
"""),
        md("""\
## Recapitulando

- El *pipeline* es una función: pregunta entra, respuesta + fuentes + latencias salen.
- *Chunk* y *k* se afinan con un *golden set* de recuperación, no solo «a ojo».
- En producción, el problema deja de ser el cuaderno y pasa a ser el ciclo de
  vida: índice, evaluación, caché, guardarraíles y despliegue.

Siguiente: [06-ejercicios.ipynb](06-ejercicios.ipynb).
"""),
    ]


# ---------------------------------------------------------------------------
# 06
# ---------------------------------------------------------------------------

def nb06():
    return [
        md("""\
# 06 · Ejercicios

Seis ejercicios para fijar lo de los cuadernos 01 a 05. Cada uno tiene un
enunciado, una pista y, al final del cuaderno, una **solución**. Intenta
resolverlos antes de bajar. El *bootstrap* deja cargadas las utilidades; no
hace falta el LLM para los ejercicios 1–4 y 6. El 5 sí propone tocar el *prompt*,
y su solución se puede leer aunque no generes de nuevo.
"""),
        code(BOOTSTRAP),
        code("""\
# --- Mandos (comunes a los ejercicios) ---
MODELO_EMB = MODELO_EMBEDDINGS_DEFECTO
documentos = cargar_corpus(RUTAS["corpus"])
preguntas = cargar_preguntas(RUTAS["datos"] / "preguntas.json")
preguntas_hecho = [p for p in preguntas if p.get("tipo") != "no_esta"]
codificador = Codificador(MODELO_EMB, dispositivo_destino=str(DEVICE))
indice = IndiceFAISS.cargar(RUTAS["modelos"] / "indice_faiss")
print(f"docs={len(documentos)}  fragmentos={len(indice.fragmentos)}  preguntas hecho={len(preguntas_hecho)}")
"""),
        md("""\
## Ejercicio 1 — Tamaño de *chunk* y un hecho frágil

Elige un hecho corto y concreto, por ejemplo `22 días laborables` o
`ci-retencion.yml`. Trocea el corpus con `tamano=150` y `solape=0`, y otra vez
con `tamano=150` y `solape=60`. ¿En cuántos fragmentos aparece el hecho **entero**
en cada caso? ¿Qué implica eso para *recall* si la pregunta es precisamente
esa cifra?

**Pista:** `fragmentar_documentos` y una comprensión de listas sobre `f.texto`.
"""),
        code("""\
# Escribe tu código aquí (ejercicio 1)
HECHO = "22 días laborables"
# ...
"""),
        md("""\
## Ejercicio 2 — Añade un documento y reindexa

Inventa un documento Markdown breve (por ejemplo, la política de *tickets de
comida* de NubeAndina: 18 soles por día laborable, no acumulables) en
`datos/corpus/`, recárgalo, vuelve a trocear y a embeber, y formula una
pregunta nueva con su `docs_relevantes`. Comprueba que el denso o BM25 lo
recuperan en el top-3.

**Pista:** no hace falta tocar `preguntas.json` si construyes el diccionario de
la pregunta en el cuaderno. Al terminar, puedes borrar el archivo para dejar el
corpus como estaba.
"""),
        code("""\
# Escribe tu código aquí (ejercicio 2)
# ruta = RUTAS["corpus"] / "nubeandina-tickets-comida.md"
# ...
"""),
        md("""\
## Ejercicio 3 — *k* = 1 frente a *k* = 5

Toma la pregunta de las vacaciones de NubeAndina. Lista el top-5 denso. Si solo
le pasaras el primero al LLM, ¿viaja el hecho de los 22 días **y** el del cierre
andino? ¿Y con k=5? Comenta el riesgo de un *k* demasiado pequeño y el de uno
demasiado grande.
"""),
        code("""\
# Escribe tu código aquí (ejercicio 3)
pregunta = "¿Cuántos días laborables de vacaciones tiene un empleado de NubeAndina y qué es el cierre andino?"
# ...
"""),
        md("""\
## Ejercicio 4 — BM25 frente a denso en un identificador

Compara BM25 y la búsqueda densa en una pregunta que cite un identificador
literal (`gke-prod-andina-01` o `ci-retencion.yml`) y en una paráfrasis sin ese
token («¿cómo se llama el clúster donde NubeAndina sirve producción?»). ¿Quién
gana en cada una? ¿Qué haría la fusión RRF?

**Pista:** `IndiceBM25` sobre `indice.fragmentos` y `fusion_rrf`.
"""),
        code("""\
# Escribe tu código aquí (ejercicio 4)
# ...
"""),
        md("""\
## Ejercicio 5 — Un *prompt* más estricto

El *prompt* de `construir_mensajes` pide abstenerse si el dato no está. Redacta
una variante todavía más estricta (por ejemplo: «si no puedes citar un
identificador de fragmento, no respondas la cifra»). ¿En qué tipo de pregunta
ayudaría, y en cuál podría dar un falso «no lo encuentro» aunque el contexto
sí tenga el dato?

No es obligatorio ejecutar el LLM otra vez: razona con lo que viste en el
cuaderno 04.
"""),
        code("""\
# Opcional: reescribe el sistema y, si quieres, genera una pregunta no_esta.
# NUEVO_SISTEMA = \"\"\"...\"\"\"
"""),
        md("""\
## Ejercicio 6 — Una caché de consultas

Implementa un diccionario que, dada la pregunta exactamente igual, reutilice
los fragmentos ya recuperados (y, si te animas, la respuesta). Mide el tiempo
de la primera llamada y de la segunda. ¿Qué clave usarías en producción, más
allá del texto crudo? (Pista: la versión del índice y del modelo de embeddings.)
"""),
        code("""\
# Escribe tu código aquí (ejercicio 6)
# cache = {}
# ...
"""),
        md("""\
---

# Soluciones

Baja hasta aquí cuando hayas intentado cada ejercicio. El código de las
soluciones es deliberadamente corto; no es «la» implementación de producción.
"""),
        md("""\
### Solución 1
"""),
        code("""\
def n_cubren(tamano, solape, hecho="22 días laborables"):
    frags = fragmentar_documentos(documentos, estrategia="solape" if solape else "fijo", tamano=tamano, solape=solape)
    hits = [f for f in frags if hecho.lower() in f.texto.lower()]
    print(f"tamano={tamano} solape={solape}: {len(hits)} fragmentos cubren el hecho (total {len(frags)})")
    for h in hits:
        print("  ", h.id)
    return hits

n_cubren(150, 0)
n_cubren(150, 60)
print(
    "Sin solape, un hecho corto cerca del borde de la ventana puede partirse "
    "y desaparecer de todos los fragmentos. El recall de esa pregunta se cae "
    "aunque el documento 'correcto' esté en el corpus."
)
"""),
        md("""\
### Solución 2
"""),
        code("""\
ruta_extra = RUTAS["corpus"] / "nubeandina-tickets-comida.md"
ruta_extra.write_text(
    "# NubeAndina: tickets de comida\\n\\n"
    "Cada empleado de jornada completa recibe un ticket de comida de **18 soles** "
    "por día laborable presencial. Los tickets no son acumulables ni canjeables "
    "por dinero. El día de trabajo remoto no genera ticket. Esta política es "
    "ficticia y solo existe para el laboratorio de RAG.\\n",
    encoding="utf-8",
)
docs2 = cargar_corpus(RUTAS["corpus"])
frags2 = fragmentar_documentos(docs2, estrategia="solape", tamano=400, solape=80)
vec2 = codificador.codificar([f.texto for f in frags2], progreso=False)
ind2 = IndiceFAISS(vec2, frags2)
preg = "¿De cuántos soles es el ticket de comida de NubeAndina en un día presencial?"
qv = codificador.codificar([preg], progreso=False)[0]
hits = ind2.buscar(qv, k=3)
print("Top-3:")
for r in hits:
    print(f"  {r.rango}. {r.fragmento.doc_id}  {r.puntuacion:.3f}")
print("¿Aparece el documento nuevo?", any(r.fragmento.doc_id == "nubeandina-tickets-comida" for r in hits))
ruta_extra.unlink()
print("Documento temporal borrado; el corpus queda como al principio.")
"""),
        md("""\
### Solución 3
"""),
        code("""\
pregunta = "¿Cuántos días laborables de vacaciones tiene un empleado de NubeAndina y qué es el cierre andino?"
qv = codificador.codificar([pregunta], progreso=False)[0]
hits = indice.buscar(qv, k=5)
for r in hits:
    t = r.fragmento.texto.lower()
    tiene_22 = "22" in t and "vacacion" in t.replace("ó", "o")
    tiene_cierre = "cierre andino" in t
    print(f"{r.rango}. {r.fragmento.id}  22dias={tiene_22}  cierre={tiene_cierre}")
print(
    "Con k=1 solo viaja el primer fragmento: si el cierre andino quedó en el "
    "siguiente trozo, el LLM no lo verá. Con k=5 es más probable que viajen "
    "ambos hechos, a costa de más ruido y más tokens."
)
"""),
        md("""\
### Solución 4
"""),
        code("""\
bm25 = IndiceBM25(indice.fragmentos)

def ver(pregunta):
    qv = codificador.codificar([pregunta], progreso=False)[0]
    denso = indice.buscar(qv, k=3)
    lex = bm25.buscar(pregunta, k=3)
    hib = fusion_rrf([denso, lex], k=3)
    print("=" * 60)
    print(pregunta)
    for nombre, lista in ("BM25", lex), ("denso", denso), ("hibrido", hib):
        print(f"  {nombre}:", ", ".join(r.fragmento.doc_id for r in lista))

ver("¿Qué es gke-prod-andina-01?")
ver("¿Cómo se llama el clúster donde NubeAndina sirve producción?")
print(
    "El identificador literal favorece a BM25. La parafrasis favorece a la busqueda "
    "densa. RRF no 'promedia puntuaciones'; suma 1/(k+rango) y por eso puede "
    "conservar el acierto de cualquiera de las dos listas."
)
"""),
        md("""\
### Solución 5

Una variante más estricta del sistema podría decir:

> Responde únicamente si puedes apoyar cada cifra o nombre en una cita
> `[fragmento-id]`. Si no puedes citar, escribe exactamente
> «No encuentro esa información en los documentos.» No completes con conocimiento
> previo.

Ayudaría en las preguntas *no_esta* (teléfono, sueldo) y cuando el recuperador
trae documentos del tema pero **sin** la cifra pedida. El riesgo es el falso
negativo: un modelo pequeño, aunque tenga el hecho en el contexto, a veces no
genera la cita y, si obedece al pie de la letra, se abstiene. Por eso se miden
*a la vez* la tasa de abstención y la cobertura de hechos, no solo una de las dos.

En producción, este guardarraíl se combina con filtros (¿el fragmento es del
tenant correcto?) y con trazas (¿qué se le mostró realmente al modelo?).
"""),
        md("""\
### Solución 6
"""),
        code("""\
class CacheRecuperacion:
    def __init__(self, pipeline, version_indice="indice_faiss_v1"):
        self.pipeline = pipeline
        self.version = version_indice
        self.mem = {}

    def clave(self, pregunta, k):
        return (self.version, self.pipeline.codificador.nombre, k, pregunta.strip())

    def recuperar(self, pregunta, k=4):
        c = self.clave(pregunta, k)
        if c in self.mem:
            return self.mem[c], True
        hits = self.pipeline.recuperar(pregunta, k=k)
        self.mem[c] = hits
        return hits, False

pipe = PipelineRAG(codificador=codificador, indice_denso=indice, metodo="denso", k=4)
cache = CacheRecuperacion(pipe)
preg = "¿Cuál es el tracking URI por defecto de MLflow en el laboratorio?"
t0 = time.perf_counter()
_, hit1 = cache.recuperar(preg, k=4)
t1 = time.perf_counter() - t0
t0 = time.perf_counter()
_, hit2 = cache.recuperar(preg, k=4)
t2 = time.perf_counter() - t0
print(f"primera (miss={not hit1}): {t1:.4f}s   segunda (hit={hit2}): {t2:.4f}s")
print("Entradas en cache:", len(cache.mem))
print(
    "En produccion la clave deberia incluir la version del indice, el nombre "
    "(y hash) del modelo de embeddings, el k y una normalizacion de la pregunta. "
    "Si el reglamento cambia, sube la version y la cache antigua deja de usarse."
)
"""),
        md("""\
## Cierre de la serie

Has recorrido el camino completo: embeddings, troceado, índice, recuperación
(léxica, densa e híbrida), generación con y sin contexto, y las notas para
llevarlo a un servicio. El siguiente paso, en el marco del curso, es tratar
este *pipeline* como cualquier otro artefacto: medirlo, versionarlo y, cuando
toque, empaquetarlo.
"""),
    ]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    write_nb("00-introduccion-y-setup.ipynb", nb00())
    write_nb("01-embeddings-y-similitud.ipynb", nb01())
    write_nb("02-chunking-e-indexado.ipynb", nb02())
    write_nb("03-recuperacion-y-busqueda.ipynb", nb03())
    write_nb("04-generacion-con-llm-local.ipynb", nb04())
    write_nb("05-pipeline-completo-y-evaluacion.ipynb", nb05())
    write_nb("06-ejercicios.ipynb", nb06())


if __name__ == "__main__":
    main()
