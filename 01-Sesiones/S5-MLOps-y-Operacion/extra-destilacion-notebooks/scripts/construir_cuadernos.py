#!/usr/bin/env python3
"""Genera los cuadernos v1 de extra-destilacion-notebooks/notebooks/."""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

RAIZ = Path(__file__).resolve().parents[1]
OUT = RAIZ / "notebooks"

BOOTSTRAP = """\
from pathlib import Path
import os, sys, json, time, gc

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def _raiz():
    aqui = Path.cwd().resolve()
    for cand in [aqui, *aqui.parents]:
        if (cand / "src" / "destilacion_utils.py").exists() and (cand / "notebooks").is_dir():
            return cand
    raise FileNotFoundError(
        "No encuentro la raiz del proyecto de destilacion "
        "(src/destilacion_utils.py + notebooks/)."
    )

RAIZ = _raiz()
sys.path.insert(0, str(RAIZ / "src"))

from destilacion_utils import (
    preparar_rutas,
    fijar_semilla,
    dispositivo,
    configurar_proxy_y_hf,
    comprobar_entorno,
    probar_conexion_hf,
    texto_ayuda_proxy,
    softmax_temperatura,
    divergencia_kl,
    perdida_destilacion,
    construir_mlp,
    construir_estudiante_sentimiento,
    contar_parametros,
    tamano_archivo_mb,
    guardar_json,
    cargar_json,
    guardar_checkpoint,
    cargar_checkpoint,
    evaluar_loader,
    medir_latencia_ms,
    entrenar_epoca,
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
print(f"Raiz:        {RAIZ}")
print(f"Dispositivo: {DEVICE}")
print(f"Semilla:     {SEMILLA}")
"""


def md(texto: str):
    return new_markdown_cell(texto.strip() + "\n")


def code(texto: str):
    return new_code_cell(texto.strip() + "\n")


def write_nb(nombre: str, celdas, kernelspec_display="Python (destilacion)"):
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

**Objetivo de este cuaderno:** entender la idea de la destilación de conocimiento (*knowledge distillation*) y dejar el entorno listo para el resto de la serie: paquetes, dispositivo (CPU o GPU), proxy corporativo y Hugging Face.

No se entrena ningún modelo aquí. Si esta comprobación termina bien, puedes pasar al cuaderno 01.

## La idea, en una frase

Un modelo **profesor** (grande o, simplemente, ya entrenado y competente) transfiere lo que sabe a un modelo **estudiante** más pequeño. La transferencia no se hace solo con las etiquetas duras (la clase correcta: un 3, un «positivo»), sino con las **etiquetas blandas**: la distribución de probabilidad que el profesor asigna a *todas* las clases.

Esa distribución es un señal más rica. Si el profesor, ante un dígito 3, da algo de probabilidad también al 8 y al 5, y casi nada al 0, el estudiante aprende que «un 3 se parece más a un 8 que a un 0». A esa información, que no está en la etiqueta dura, se la llama a veces **conocimiento oscuro** (*dark knowledge*).

## Por qué importa en producción

En un servicio, el modelo que responde a cada petición paga en **latencia**, **memoria** y **coste**. Un profesor puede ser excelente y, a la vez, demasiado lento o demasiado grande para el camino de la petición. Destilarlo a un estudiante es una forma de conservar buena parte de su calidad con un coste de inferencia menor. El profesor puede seguir usándose fuera de la petición (por lotes, para etiquetar, para auditar).

## Recorrido de la serie

| Cuaderno | Contenido | Depende de |
|---|---|---|
| **00** (este) | Intuición, entorno, proxy y Hugging Face | — |
| **01** | Softmax, temperatura, pérdida de destilación y figuras | 00 |
| **02** | Calentamiento: MLP profesor y estudiante en MNIST | 01 |
| **03** | Profesor de Hugging Face (sentimiento) → estudiante diminuto | 01 |
| **04** | Comparativa (exactitud, tamaño, latencia) y conclusiones de MLOps | 02 y 03 |
| **05** | Ejercicios | 01; varios usan 02 y 03 |

Los artefactos de 02 y 03 se guardan en `modelos/` y `resultados/`. El 04 los lee; no vuelve a entrenar.
"""),
        md("""\
## 1. Localizar el proyecto y el módulo compartido

Los cuadernos viven en `notebooks/` y las funciones comunes en `src/destilacion_utils.py`. La celda siguiente localiza la raíz aunque el directorio de trabajo sea `notebooks/`, añade `src/` al `sys.path` y deja creadas las carpetas `modelos/`, `resultados/`, `datos/` y `cache-hf/`.
"""),
        code(BOOTSTRAP),
        md("""\
## 2. Comprobación del entorno

Se listan las versiones de los paquetes que usa la serie. Todo debe aparecer como **disponible**. El curso se puede completar en **CPU**; si hay GPU, se usará, pero no es un requisito.

Si falta algún paquete, instálalo en el entorno del kernel (en la raíz del proyecto: `pip install -r requisitos-extra-destilacion.txt`) y vuelve a ejecutar esta celda.
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
    "Activa el entorno del proyecto e instala requisitos-extra-destilacion.txt."
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

Si estás en una red de empresa, las descargas de MNIST o de Hugging Face pueden fallar por el **proxy** o por un **certificado corporativo** que intercepta HTTPS. Esta serie no adivina tu proxy ni imprime contraseñas ni tokens.

La función `configurar_proxy_y_hf` (ya ejecutada arriba) hace tres cosas conservadoras:

1. Informa de si `HTTP_PROXY` / `HTTPS_PROXY` / `NO_PROXY` están definidos.
2. Informa de si hay un certificado (`SSL_CERT_FILE` o `REQUESTS_CA_BUNDLE`) y de si hay un `HF_TOKEN` (solo sí o no).
3. Si `HF_HOME` no estaba definido, lo apunta a `cache-hf/` dentro del proyecto, para que el caché de modelos y datos quede con el material y no se mezcle con el del usuario.

Para **definir** un proxy, descomenta y adapta la celda siguiente *antes* de descargar nada (cuadernos 02 y 03), o exporta las variables en la terminal y vuelve a abrir Jupyter.
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
Comprobación opcional de red: un `HEAD` a Hugging Face, sin descargar modelos. Si falla, el cuaderno 01 y el 02 (con MNIST, que usa otro origen) todavía se pueden cursar; el 03 necesitará red la primera vez, o un caché previo y `HF_HUB_OFFLINE=1`.
"""),
        code("""\
conexion_hf = probar_conexion_hf()
print(conexion_hf)
if conexion_hf["ok"]:
    print("Hugging Face es alcanzable. El cuaderno 03 podrá descargar el profesor si no está en el caché.")
else:
    print(
        "No se ha podido alcanzar Hugging Face:",
        conexion_hf.get("error"),
        "\\nSi el profesor ya está en cache-hf/, define HF_HUB_OFFLINE=1. "
        "Si estás detrás de un proxy, revisa la celda anterior.",
    )
"""),
        md("""\
## 4. Carpetas de artefactos

Los cuadernos 02 y 03 escribirán pesos en `modelos/` y métricas en `resultados/`. El 04 las leerá. Esta celda solo confirma que existen.
"""),
        code("""\
resumen_rutas = pd.DataFrame(
    [
        {"carpeta": k, "ruta": str(v), "existe": Path(v).exists()}
        for k, v in RUTAS.items()
    ]
)
resumen_rutas
"""),
        md("""\
## Cierre

Para seguir adelante hace falta:

- Que no falte ningún paquete obligatorio.
- Tener claro si vas a trabajar en CPU o en GPU (ambos valen).
- Si estás en una red corporativa, dejar resuelto el proxy *antes* del cuaderno 03.

Siguiente cuaderno: `01-teoria-softmax-temperatura.ipynb`.
"""),
    ]


# ---------------------------------------------------------------------------
# 01
# ---------------------------------------------------------------------------

def nb01():
    return [
        md("""\
# 01 · Teoría: softmax y temperatura

**Objetivo de este cuaderno:** entender el softmax, el papel de la **temperatura** \\(T\\), el «conocimiento oscuro» del profesor y la **pérdida de destilación**, con figuras y un ejemplo numérico pequeño. Aquí no se entrenan redes: solo se fija el lenguaje que usan los cuadernos 02 y 03.

## Softmax

Un clasificador no produce directamente una clase: produce un vector de **logits** \\(z\\) (números reales, uno por clase). El softmax los convierte en una distribución de probabilidad:

$$
p_i = \\mathrm{softmax}(z)_i = \\frac{e^{z_i}}{\\sum_j e^{z_j}}.
$$

La clase predicha es \\(\\arg\\max_i p_i\\) (equivale a \\(\\arg\\max_i z_i\\)). Lo que cambia, y lo que el estudiante va a copiar, es *cómo se reparte* la probabilidad entre las clases no ganadoras.
"""),
        code(BOOTSTRAP),
        md("""\
## 1. Softmax a mano, y de forma numéricamente estable

Restar el máximo de los logits antes de exponentiar no cambia el resultado (el factor se cancela) y evita desbordar `exp` cuando los logits son grandes. `softmax_temperatura` del módulo compartido hace exactamente eso. Lo comprobamos con un vector pequeño.
"""),
        code("""\
logits = np.array([2.0, 1.0, 0.1])

def softmax_ingenua(z):
    e = np.exp(z)
    return e / e.sum()

def softmax_estable(z):
    z = z - z.max()
    e = np.exp(z)
    return e / e.sum()

p_ingenua = softmax_ingenua(logits)
p_estable = softmax_estable(logits)
p_util = softmax_temperatura(logits, temperature=1.0)

tabla = pd.DataFrame(
    {"clase": [0, 1, 2], "logit": logits, "ingenua": p_ingenua, "estable": p_estable, "util": p_util}
)
print(tabla.to_string(index=False))
print("sumas:", p_ingenua.sum(), p_estable.sum(), p_util.sum())
np.testing.assert_allclose(p_ingenua, p_estable)
np.testing.assert_allclose(p_estable, p_util)
print("Las tres implementaciones coinciden (T = 1).")
"""),
        md("""\
## 2. La temperatura \\(T\\)

En destilación se usa un softmax **con temperatura**:

$$
p_i^{(T)} = \\mathrm{softmax}(z / T)_i = \\frac{e^{z_i / T}}{\\sum_j e^{z_j / T}}.
$$

- \\(T = 1\\): el softmax habitual.
- \\(T > 1\\): se suaviza la distribución. Las clases no ganadoras reciben más masa. Ahí es donde aparece el conocimiento oscuro.
- \\(T \\to 0\\): la distribución se acerca a un vector *one-hot* (todo a la clase de mayor logit).
- \\(T \\to \\infty\\): se acerca a la uniforme.

La celda siguiente toma un mismo vector de logits (el de un «profesor» que está muy seguro de la clase 3, pero ve cierto parecido con la 8 y la 5) y lo muestra a varias temperaturas.
"""),
        code("""\
clases = np.arange(10)
# Logits inventados de un profesor ante un dígito que es un 3.
# El 3 gana; el 8 y el 5 se le parecen; el 0 y el 1 casi no.
logits_profesor = np.array([0.2, -1.0, 0.4, 5.0, 0.1, 2.2, -0.4, 0.3, 3.1, 0.0])

temperaturas = [0.5, 1, 2, 5, 10]
probs = {T: softmax_temperatura(logits_profesor, temperature=T) for T in temperaturas}

fig, ejes = plt.subplots(1, len(temperaturas), figsize=(14, 3.4), sharey=True)
for ax, T in zip(ejes, temperaturas):
    ax.bar(clases, probs[T], color="#1f4e79")
    ax.set_title(f"T = {T}")
    ax.set_xticks(clases)
    ax.set_xlabel("clase")
    ax.set_ylim(0, 1)
ejes[0].set_ylabel("probabilidad")
fig.suptitle("El mismo vector de logits, suavizado con distintas temperaturas", y=1.03)
fig.tight_layout()
fig.savefig(RUTAS["resultados"] / "fig_softmax_temperatura.png", bbox_inches="tight")
plt.show()

pd.DataFrame(probs, index=[f"clase {i}" for i in clases]).round(3)
"""),
        md("""\
### Cómo leer la figura

Con \\(T = 0.5\\) casi toda la masa está en el 3: la señal se parece a una etiqueta dura. Con \\(T = 5\\) o \\(T = 10\\) el 3 sigue ganando, pero el 8 y el 5 son claramente más probables que el 0 o el 1. Esa es la información que queremos que el estudiante reciba.

Una forma compacta de medir el suavizado es la **entropía** \\(H(p) = -\\sum_i p_i \\log p_i\\): crece con \\(T\\) y se satura cerca de \\(\\log 10\\) (uniforme en 10 clases).
"""),
        code("""\
def entropia(p, eps=1e-12):
    p = np.clip(p, eps, 1.0)
    p = p / p.sum()
    return float(-(p * np.log(p)).sum())

Ts = np.linspace(0.25, 15, 80)
H = [entropia(softmax_temperatura(logits_profesor, temperature=T)) for T in Ts]

fig, ax = plt.subplots(figsize=(7, 3.6))
ax.plot(Ts, H, color="#1f4e79")
ax.axhline(np.log(10), color="gray", linestyle="--", linewidth=1, label="uniforme (log 10)")
for T in temperaturas:
    ax.scatter([T], [entropia(probs[T])], zorder=3)
    ax.annotate(f"T={T}", (T, entropia(probs[T])), textcoords="offset points", xytext=(4, 6))
ax.set_xlabel("temperatura T")
ax.set_ylabel("entropía (nats)")
ax.set_title("A mayor T, más se acerca la distribución a la uniforme")
ax.legend()
fig.tight_layout()
fig.savefig(RUTAS["resultados"] / "fig_entropia_temperatura.png", bbox_inches="tight")
plt.show()
"""),
        md("""\
## 3. La pérdida de destilación

Hinton, Vinyals y Dean (2015) combinan dos términos:

$$
\\mathcal{L} = \\alpha \\, T^{2} \\, \\mathrm{KL}\\big( p^{\\text{prof}}_{(T)} \\,\\big\\|\\, p^{\\text{est}}_{(T)} \\big) + (1-\\alpha)\\, \\mathrm{CE}\\big(z^{\\text{est}}, y\\big).
$$

- **KL** (divergencia de Kullback-Leibler): obliga al estudiante a copiar la distribución suave del profesor. Se calcula a temperatura \\(T\\).
- **CE** (entropía cruzada): el estudiante también ve la etiqueta dura \\(y\\), la del dataset.
- **\\(\\alpha\\)**: mezcla. \\(\\alpha = 1\\) es solo destilación; \\(\\alpha = 0\\) es el entrenamiento supervisado habitual.
- **\\(T^2\\)**: al subir \\(T\\), las probabilidades se aplanan y el gradiente de la KL se encoge (del orden de \\(1/T^2\\)). Multiplicar por \\(T^2\\) compensa ese efecto y deja el peso relativo de los dos términos más estable cuando cambias \\(T\\).

En el módulo compartido esto es `perdida_destilacion(...)`.
"""),
        code("""\
import torch

# Profesor: seguro del 3, con masa residual en 8 y 5 (el mismo vector de arriba).
z_prof = torch.tensor(logits_profesor, dtype=torch.float32).unsqueeze(0)
# Estudiante A: ya se parece al profesor. Estudiante B: se equivoca y apuesta por el 8.
z_est_a = torch.tensor([0.1, -0.8, 0.2, 4.2, 0.0, 1.8, -0.3, 0.2, 2.6, 0.0]).unsqueeze(0)
z_est_b = torch.tensor([0.3, 0.0, 0.2, 1.0, 0.1, 0.8, 0.0, 0.2, 4.8, 0.2]).unsqueeze(0)
y = torch.tensor([3])

filas = []
for nombre, z_est in [("estudiante cercano", z_est_a), ("estudiante que apuesta al 8", z_est_b)]:
    for T in [1.0, 3.0, 5.0]:
        for alpha in [0.0, 0.7, 1.0]:
            loss = perdida_destilacion(z_est, z_prof, y, temperature=T, alpha=alpha)
            filas.append(
                {"caso": nombre, "T": T, "alpha": alpha, "perdida": float(loss)}
            )

tabla_perdida = pd.DataFrame(filas).pivot_table(
    index=["caso", "T"], columns="alpha", values="perdida"
)
tabla_perdida.round(3)
"""),
        md("""\
### Cómo leer la tabla

- Con \\(\\alpha = 0\\) solo cuenta la etiqueta dura. Si ambos estudiantes aciertan el 3 como clase más probable, esta pérdida no distingue bien *cómo* reparte cada uno el resto de la masa.
- Con \\(\\alpha = 0.7\\) o \\(1\\), el estudiante que se parece al profesor tiene pérdida claramente menor que el que se empeña en el 8: la KL ve la forma de la distribución, no solo el ganador.

Eso es exactamente lo que queremos transferir en los cuadernos 02 y 03.
"""),
        code("""\
# KL entre el profesor y un estudiante, a varias T, para el caso "cercano" y el "equivocado".
filas_kl = []
for nombre, z_est in [("cercano", z_est_a), ("apuesta al 8", z_est_b)]:
    for T in [1, 2, 3, 5, 8]:
        p = softmax_temperatura(z_prof.numpy().ravel(), temperature=T)
        q = softmax_temperatura(z_est.numpy().ravel(), temperature=T)
        filas_kl.append({"T": T, "estudiante": nombre, "KL(prof || est)": float(divergencia_kl(p, q))})

tabla_kl = pd.DataFrame(filas_kl).pivot(index="T", columns="estudiante", values="KL(prof || est)")
ax = tabla_kl.plot(marker="o", figsize=(7, 3.6), title="KL entre profesor y estudiante a distintas T")
ax.set_ylabel("KL (nats)")
ax.set_xlabel("temperatura T")
fig = ax.get_figure()
fig.tight_layout()
fig.savefig(RUTAS["resultados"] / "fig_kl_temperatura.png", bbox_inches="tight")
plt.show()
tabla_kl.round(3)
"""),
        md("""\
## Qué retener

1. El softmax convierte logits en una distribución. La temperatura \\(T\\) controla cuánto se suaviza.
2. El valor de destilar está en las **clases no ganadoras**: el estudiante copia similitudes que la etiqueta dura no contiene.
3. La pérdida mezcla esa KL (con el factor \\(T^2\\)) y, si quieres, la entropía cruzada con \\(y\\). \\(T\\) y \\(\\alpha\\) son hiperparámetros: se eligen con un conjunto de validación, no a ojo en test.
4. En 02 y 03 usaremos, salvo que se indique otra cosa, \\(T = 3\\) y \\(\\alpha = 0.7\\), valores de partida razonables, no un óptimo universal.

Siguiente cuaderno: `02-destilacion-mnist-mlp.ipynb` (calentamiento en visión, un MLP). El 03 hace lo mismo con un profesor de Hugging Face. Los dos pueden cursarse en ese orden; el 04 los necesita a ambos.
"""),
    ]


# ---------------------------------------------------------------------------
# 02 MNIST
# ---------------------------------------------------------------------------

def nb02():
    return [
        md("""\
# 02 · Calentamiento: destilación de un MLP en MNIST

**Objetivo de este cuaderno:** ver la destilación de conocimiento en un problema pequeño y medible, de punta a punta. Se entrena un **profesor** MLP, se entrena un **estudiante** mucho más pequeño con etiquetas duras y se entrena *el mismo* estudiante copiando las etiquetas blandas del profesor. Al final se comparan exactitud, tamaño y latencia, y se guardan artefactos para el cuaderno 04.

MNIST no es un problema difícil: un MLP pequeño, con suficientes etiquetas duras, ya acierta mucho y la destilación apenas se nota. El experimento se diseña a propósito con **pocas etiquetas para el estudiante** (400 imágenes). Con tan pocos ejemplos, el estudiante duro tiende a memorizar el train; el destilado recibe, en cada imagen, una distribución rica del profesor (entrenado con 30 000) y suele generalizar mejor. Ese es un caso realista: el profesor se entrenó cuando había más datos o más cómputo; el estudiante tiene que arreglárselas con un subconjunto.

## Diseño del experimento

| Pieza | Qué es | Datos |
|---|---|---|
| Profesor | MLP `[784, 256, 128, 10]` | 30 000 imágenes de train |
| Estudiante duro | MLP `[784, 32, 10]`, solo etiquetas 0/1 | 400 imágenes de train |
| Estudiante destilado | La misma arquitectura y los mismos pesos iniciales, con \\(T=4\\), \\(\\alpha=0.5\\) | Las mismas 400, más las blandas del profesor |
| Test | No se usa para elegir nada | 5 000 imágenes del test oficial |

Los dos estudiantes arrancan del **mismo estado inicial**. Si no, una diferencia de exactitud podría deberse a la suerte de la inicialización, no a la destilación.
"""),
        code(BOOTSTRAP),
        md("""\
## 1. Parámetros

Como en el resto del curso, los parámetros van al principio y no se editan a ciegas a mitad del cuaderno. Si quieres experimentar, cámbialos aquí y vuelve a ejecutar desde esta celda. El cuaderno 05 propone variaciones sistemáticas de \\(T\\) y \\(\\alpha\\).
"""),
        code("""\
import torch
from torch import optim
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms

N_TRAIN_PROFESOR = 30_000
N_TRAIN_ESTUDIANTE = 400
N_TEST = 5_000
EPOCHS_PROFESOR = 4
EPOCHS_ESTUDIANTE = 25
BATCH = 64
LR_PROFESOR = 1e-3
LR_ESTUDIANTE = 1e-3
ANCHOS_PROFESOR = [784, 256, 128, 10]
ANCHOS_ESTUDIANTE = [784, 32, 10]
T_DISTIL = 4.0
ALPHA = 0.5
DROP_PROFESOR = 0.2
DROP_ESTUDIANTE = 0.0

print("dispositivo:", DEVICE)
print("profesor:", ANCHOS_PROFESOR, "épocas", EPOCHS_PROFESOR, "datos", N_TRAIN_PROFESOR)
print("estudiante:", ANCHOS_ESTUDIANTE, "épocas", EPOCHS_ESTUDIANTE, "datos", N_TRAIN_ESTUDIANTE)
print(f"destilación: T={T_DISTIL}, alpha={ALPHA}")
"""),
        md("""\
## 2. Datos

MNIST se descarga una vez a `datos/mnist/`. Las imágenes se normalizan con la media y la desviación habituales del conjunto y se aplanan a un vector de 784. Las particiones del estudiante son un **subconjunto** de las del profesor (mismas primeras 400, tras un barajado con la semilla del proyecto). Test no se mezcla con train.
"""),
        code("""\
transform = transforms.Compose(
    [
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,)),
        transforms.Lambda(lambda t: t.reshape(-1)),
    ]
)

train_full = datasets.MNIST(RUTAS["datos"] / "mnist", train=True, download=True, transform=transform)
test_full = datasets.MNIST(RUTAS["datos"] / "mnist", train=False, download=True, transform=transform)

g = torch.Generator().manual_seed(SEMILLA)
idx_train = torch.randperm(len(train_full), generator=g).tolist()
idx_test = torch.randperm(len(test_full), generator=g).tolist()

ds_profesor = Subset(train_full, idx_train[:N_TRAIN_PROFESOR])
ds_estudiante = Subset(train_full, idx_train[:N_TRAIN_ESTUDIANTE])
ds_test = Subset(test_full, idx_test[:N_TEST])

# Para visualizar, una copia sin normalizar ni aplanar.
raw_train = datasets.MNIST(RUTAS["datos"] / "mnist", train=True, download=False, transform=transforms.ToTensor())


def hacer_loader(ds, shuffle, batch=BATCH):
    return DataLoader(ds, batch_size=batch, shuffle=shuffle, num_workers=0)


loader_prof = hacer_loader(ds_profesor, shuffle=True)
loader_est = hacer_loader(ds_estudiante, shuffle=True)
loader_test = hacer_loader(ds_test, shuffle=False)

print(
    f"train profesor={len(ds_profesor)}, train estudiante={len(ds_estudiante)}, "
    f"test={len(ds_test)} (MNIST train completo={len(train_full)}, test completo={len(test_full)})"
)

# Un vistazo a dígitos del subconjunto del estudiante.
fig, ejes = plt.subplots(1, 8, figsize=(12, 2))
for ax, i in zip(ejes, idx_train[:8]):
    img, y = raw_train[i]
    ax.imshow(img.squeeze(), cmap="gray")
    ax.set_title(str(int(y)))
    ax.axis("off")
fig.suptitle("Ocho imágenes del subconjunto con el que aprenderá el estudiante", y=1.08)
fig.tight_layout()
plt.show()
"""),
        md("""\
## 3. Modelos: cuánto más pequeño es el estudiante
"""),
        code("""\
profesor = construir_mlp(ANCHOS_PROFESOR, dropout=DROP_PROFESOR).to(DEVICE)
estudiante_plantilla = construir_mlp(ANCHOS_ESTUDIANTE, dropout=DROP_ESTUDIANTE).to(DEVICE)

tabla_tam = pd.DataFrame(
    [
        {
            "modelo": "profesor",
            "anchos": str(ANCHOS_PROFESOR),
            "parametros": contar_parametros(profesor),
        },
        {
            "modelo": "estudiante",
            "anchos": str(ANCHOS_ESTUDIANTE),
            "parametros": contar_parametros(estudiante_plantilla),
        },
    ]
)
tabla_tam["ratio_respecto_profesor"] = tabla_tam["parametros"] / tabla_tam.loc[0, "parametros"]
display(tabla_tam)

n_prof = contar_parametros(profesor)
n_est = contar_parametros(estudiante_plantilla)
print(f"El estudiante tiene {n_est / n_prof:.1%} de los parámetros del profesor.")
"""),
        md("""\
## 4. Entrenar al profesor

El profesor se entrena de forma habitual: entropía cruzada con etiquetas duras, en las 30 000 imágenes. Después se deja en modo `eval` y ya no se mueve: es la fuente de las etiquetas blandas.
"""),
        code("""\
def entrenar(
    modelo,
    loader,
    epocas,
    lr,
    *,
    profesor_fijo=None,
    temperature=T_DISTIL,
    alpha=ALPHA,
    etiqueta="",
):
    opt = optim.Adam(modelo.parameters(), lr=lr)
    historial = []
    for epoca in range(1, epocas + 1):
        tr = entrenar_epoca(
            modelo,
            loader,
            opt,
            DEVICE,
            profesor=profesor_fijo,
            temperature=temperature,
            alpha=alpha if profesor_fijo is not None else 0.0,
        )
        ev = evaluar_loader(modelo, loader_test, DEVICE)
        fila = {
            "epoca": epoca,
            "train_perdida": tr["perdida"],
            "train_exactitud": tr["exactitud"],
            "test_exactitud": ev["exactitud"],
            "test_perdida": ev["perdida_ce"],
        }
        historial.append(fila)
        print(
            f"{etiqueta:22s} época {epoca:2d}/{epocas}  "
            f"train acc={tr['exactitud']:.3f}  test acc={ev['exactitud']:.3f}  "
            f"pérdida={tr['perdida']:.3f}"
        )
    return historial


hist_profesor = entrenar(
    profesor, loader_prof, EPOCHS_PROFESOR, LR_PROFESOR, etiqueta="profesor"
)
profesor.eval()
for p in profesor.parameters():
    p.requires_grad_(False)

metricas_profesor = evaluar_loader(profesor, loader_test, DEVICE)
print("profesor en test:", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in metricas_profesor.items()})
assert metricas_profesor["exactitud"] > 0.90, (
    "El profesor debería superar el 90 % en test de MNIST. Revisa el entorno o aumenta las épocas."
)
"""),
        md("""\
## 5. Dos estudiantes, misma salida

Se clona el estado inicial. El primero ve solo etiquetas duras (`alpha = 0`, sin profesor). El segundo destila al profesor. Misma arquitectura, mismos datos, mismas épocas, mismo optimizador.
"""),
        code("""\
# Estado inicial común (la plantilla aún no se ha entrenado).
estado_inicial = {k: v.detach().cpu().clone() for k, v in estudiante_plantilla.state_dict().items()}

estudiante_duro = construir_mlp(ANCHOS_ESTUDIANTE, dropout=DROP_ESTUDIANTE).to(DEVICE)
estudiante_duro.load_state_dict(estado_inicial)
hist_duro = entrenar(
    estudiante_duro, loader_est, EPOCHS_ESTUDIANTE, LR_ESTUDIANTE, etiqueta="estudiante duro"
)

estudiante_kd = construir_mlp(ANCHOS_ESTUDIANTE, dropout=DROP_ESTUDIANTE).to(DEVICE)
estudiante_kd.load_state_dict(estado_inicial)
hist_kd = entrenar(
    estudiante_kd,
    loader_est,
    EPOCHS_ESTUDIANTE,
    LR_ESTUDIANTE,
    profesor_fijo=profesor,
    temperature=T_DISTIL,
    alpha=ALPHA,
    etiqueta="estudiante destilado",
)

metricas_duro = evaluar_loader(estudiante_duro, loader_test, DEVICE)
metricas_kd = evaluar_loader(estudiante_kd, loader_test, DEVICE)
"""),
        md("""\
## 6. Curvas y comparación

En train, el estudiante duro puede llegar a acertar casi todo: con 400 ejemplos, memorizar es fácil. La cifra que importa está en **test**. El destilado suele quedar por encima del duro ahí, porque las blandas del profesor actúan como una señal más rica (y, de paso, como regularizador). Si en tu ejecución la diferencia fuera pequeña o del otro signo, no la fuerces: anótala y el cuaderno 05 pregunta cuándo merece la pena destilar.
"""),
        code("""\
fig, ejes = plt.subplots(1, 2, figsize=(11, 3.8))
for hist, nombre, color in [
    (hist_profesor, "profesor", "#1f4e79"),
    (hist_duro, "estudiante duro", "#b36b00"),
    (hist_kd, "estudiante destilado", "#2a7f4f"),
]:
    ep = [f["epoca"] for f in hist]
    ejes[0].plot(ep, [f["train_exactitud"] for f in hist], marker="o", label=nombre, color=color)
    ejes[1].plot(ep, [f["test_exactitud"] for f in hist], marker="o", label=nombre, color=color)
ejes[0].set_title("Exactitud en train")
ejes[1].set_title("Exactitud en test")
for ax in ejes:
    ax.set_xlabel("época")
    ax.set_ylabel("exactitud")
    ax.set_ylim(0.5, 1.01)
    ax.legend()
fig.tight_layout()
fig.savefig(RUTAS["resultados"] / "fig_mnist_curvas.png", bbox_inches="tight")
plt.show()

# Un lote de test: el profesor "explica" un dígito a T=1 y a T=3.
estudiante_kd.eval()
x_vis, y_vis = next(iter(loader_test))
x_vis, y_vis = x_vis.to(DEVICE), y_vis.to(DEVICE)
with torch.no_grad():
    logits_p = profesor(x_vis[:6])

fig, ejes = plt.subplots(2, 6, figsize=(12, 4.2))
# Reconstruir una imagen aproximada deshaciendo la normalización solo para verla.
for i in range(6):
    img = x_vis[i].detach().cpu().reshape(28, 28) * 0.3081 + 0.1307
    ejes[0, i].imshow(img.numpy(), cmap="gray")
    ejes[0, i].set_title(f"y = {int(y_vis[i])}")
    ejes[0, i].axis("off")
    p3 = softmax_temperatura(logits_p[i].cpu().numpy(), temperature=T_DISTIL)
    ejes[1, i].bar(range(10), p3, color="#1f4e79")
    ejes[1, i].set_xticks(range(10))
    ejes[1, i].set_ylim(0, 1)
    ejes[1, i].set_title(f"prof T={int(T_DISTIL)}")
ejes[1, 0].set_ylabel("probabilidad")
fig.suptitle("Etiquetas blandas del profesor (la masa residual es el conocimiento oscuro)")
fig.tight_layout()
fig.savefig(RUTAS["resultados"] / "fig_mnist_blandas.png", bbox_inches="tight")
plt.show()
"""),
        md("""\
## 7. Tamaño, latencia y artefactos

Se mide la latencia de un lote de 64 en el dispositivo actual (casi seguro CPU). El 04 volverá a leer estas cifras y, si los pesos siguen ahí, puede remedirlas.
"""),
        code("""\
lote_latencia = next(iter(loader_test))[0][:64].to(DEVICE)
lat_prof = medir_latencia_ms(profesor, lote_latencia, device=DEVICE)
lat_duro = medir_latencia_ms(estudiante_duro, lote_latencia, device=DEVICE)
lat_kd = medir_latencia_ms(estudiante_kd, lote_latencia, device=DEVICE)

ruta_prof = RUTAS["modelos"] / "mnist_profesor.pt"
ruta_duro = RUTAS["modelos"] / "mnist_estudiante_duro.pt"
ruta_kd = RUTAS["modelos"] / "mnist_estudiante_destilado.pt"

meta_base = {
    "anchos_profesor": ANCHOS_PROFESOR,
    "anchos_estudiante": ANCHOS_ESTUDIANTE,
    "n_train_profesor": N_TRAIN_PROFESOR,
    "n_train_estudiante": N_TRAIN_ESTUDIANTE,
    "n_test": N_TEST,
    "epochs_profesor": EPOCHS_PROFESOR,
    "epochs_estudiante": EPOCHS_ESTUDIANTE,
    "temperature": T_DISTIL,
    "alpha": ALPHA,
    "semilla": SEMILLA,
    "dispositivo": str(DEVICE),
    "dropout_profesor": DROP_PROFESOR,
    "dropout_estudiante": DROP_ESTUDIANTE,
}

guardar_checkpoint(profesor, ruta_prof, {**meta_base, "rol": "profesor", **metricas_profesor})
guardar_checkpoint(estudiante_duro, ruta_duro, {**meta_base, "rol": "estudiante_duro", **metricas_duro})
guardar_checkpoint(estudiante_kd, ruta_kd, {**meta_base, "rol": "estudiante_destilado", **metricas_kd})

resultado = {
    "problema": "mnist-mlp",
    "semilla": SEMILLA,
    "dispositivo": str(DEVICE),
    "temperature": T_DISTIL,
    "alpha": ALPHA,
    "dropout_profesor": DROP_PROFESOR,
    "dropout_estudiante": DROP_ESTUDIANTE,
    "n_train_profesor": N_TRAIN_PROFESOR,
    "n_train_estudiante": N_TRAIN_ESTUDIANTE,
    "n_test": N_TEST,
    "modelos": {
        "profesor": {
            "ruta": str(ruta_prof.relative_to(RAIZ)),
            "anchos": ANCHOS_PROFESOR,
            "parametros": contar_parametros(profesor),
            "tamano_mb": tamano_archivo_mb(ruta_prof),
            **metricas_profesor,
            **{f"latencia_{k}": v for k, v in lat_prof.items()},
        },
        "estudiante_duro": {
            "ruta": str(ruta_duro.relative_to(RAIZ)),
            "anchos": ANCHOS_ESTUDIANTE,
            "parametros": contar_parametros(estudiante_duro),
            "tamano_mb": tamano_archivo_mb(ruta_duro),
            **metricas_duro,
            **{f"latencia_{k}": v for k, v in lat_duro.items()},
        },
        "estudiante_destilado": {
            "ruta": str(ruta_kd.relative_to(RAIZ)),
            "anchos": ANCHOS_ESTUDIANTE,
            "parametros": contar_parametros(estudiante_kd),
            "tamano_mb": tamano_archivo_mb(ruta_kd),
            **metricas_kd,
            **{f"latencia_{k}": v for k, v in lat_kd.items()},
        },
    },
    "historial": {
        "profesor": hist_profesor,
        "estudiante_duro": hist_duro,
        "estudiante_destilado": hist_kd,
    },
}
guardar_json(resultado, RUTAS["resultados"] / "mnist.json")

comp = pd.DataFrame(
    [
        {
            "modelo": nombre,
            "parametros": datos["parametros"],
            "tamano_mb": round(datos["tamano_mb"], 3),
            "exactitud_test": round(datos["exactitud"], 4),
            "ms_por_ejemplo": round(datos["latencia_ms_por_ejemplo_media"], 4),
        }
        for nombre, datos in resultado["modelos"].items()
    ]
)
display(comp)
print("Artefactos escritos en modelos/ y resultados/mnist.json")
"""),
        md("""\
## Interpretación y cierre

- El profesor es la referencia de calidad. El estudiante destilado no tiene por qué igualarlo: tiene menos capacidad y dos órdenes de magnitud menos de datos. El éxito es **generalizar mejor que el estudiante duro** (mismo modelo, mismos 400 ejemplos, mismos pesos iniciales) y acercarse al profesor más de lo que las etiquetas duras solas permiten.
- La latencia, en un MLP de este tamaño, es muy baja en CPU. El contraste de coste se verá mejor en el cuaderno 03, con un DistilBERT de decenas de millones de parámetros frente a un GRU diminuto.
- Estos resultados son la entrada del cuaderno 04. No borres `modelos/` ni `resultados/mnist.json` si quieres la comparativa completa.

Siguiente: `03-destilacion-bert-sentimiento.ipynb`.
"""),
    ]


# ---------------------------------------------------------------------------
# 03 sentimiento
# ---------------------------------------------------------------------------

def nb03():
    return [
        md("""\
# 03 · Destilación: de un profesor de Hugging Face a un estudiante diminuto (sentimiento)

**Objetivo de este cuaderno:** repetir la destilación en un problema de lenguaje, con un profesor **ya entrenado** que no vamos a retocar. El profesor es un DistilBERT público, afinado en SST-2 (frases en inglés, positivo / negativo). El estudiante es un GRU bidireccional muy pequeño, con la misma tokenización que el profesor, que cabe y entrena en CPU.

Este es el patrón habitual en producción: el profesor es un modelo de Hugging Face (o uno propio, ya validado); el estudiante es lo que se desplegará en el camino de la petición.

## Diseño

| Pieza | Qué es |
|---|---|
| Profesor | `distilbert-base-uncased-finetuned-sst-2-english` (solo inferencia) |
| Datos | SST-2 (GLUE): 3 000 frases de train y el validation oficial (872) como test |
| Estudiante duro | Embedding + GRU bidireccional + lineal, etiquetas 0/1 |
| Estudiante destilado | La misma arquitectura y los mismos pesos iniciales, \\(T=3\\), \\(\\alpha=0.7\\) |

Para no tener el DistilBERT en memoria durante el entrenamiento del estudiante, se **precomputan** sus logits, se guardan en disco y se libera el profesor. El estudiante, más adelante, solo alinea esos logits por el índice del ejemplo.
"""),
        code(BOOTSTRAP),
        md("""\
## 1. Parámetros
"""),
        code("""\
import torch
from torch import optim
from torch.utils.data import DataLoader, Dataset
from datasets import load_dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODELO_PROFESOR = "distilbert-base-uncased-finetuned-sst-2-english"
N_TRAIN = 3_000
MAX_LEN = 64
BATCH_PROFESOR = 16
BATCH_ESTUDIANTE = 32
EPOCHS_ESTUDIANTE = 5
T_DISTIL = 3.0
ALPHA = 0.7
LR_ESTUDIANTE = 1e-3
DIM_EMB = 64
DIM_OCULTA = 64
N_CAPAS = 1

print("dispositivo:", DEVICE)
print("profesor:", MODELO_PROFESOR)
print(f"datos: train={N_TRAIN}, max_len={MAX_LEN}")
print(f"estudiante: emb={DIM_EMB}, hidden={DIM_OCULTA}, épocas={EPOCHS_ESTUDIANTE}")
print(f"destilación: T={T_DISTIL}, alpha={ALPHA}")
"""),
        md("""\
## 2. Datos SST-2 y tokenizador del profesor

SST-2 es binario (0 = negativo, 1 = positivo). El conjunto se carga desde `nyu-mll/glue` (el identificador antiguo `glue` ya no es válido en el Hub). El *split* de test oficial de GLUE no trae etiquetas públicas, así que usamos el **validation** como conjunto de evaluación (872 frases). No se toca para elegir hiperparámetros: en este cuaderno no hay búsqueda, solo una comparación honesta entre dos estudiantes.

El estudiante reutiliza el **mismo tokenizador** que el profesor. Así, lo que ve el profesor y lo que ve el estudiante es la misma secuencia de identificadores. En producción, ese tokenizador tiene que viajar con el estudiante (es parte del preprocesamiento).
"""),
        code("""\
# Caché del proyecto (HF_HOME ya apunta a cache-hf/ si no había otro).
ds = load_dataset("nyu-mll/glue", "sst2")

g = torch.Generator().manual_seed(SEMILLA)
idx = torch.randperm(len(ds["train"]), generator=g).tolist()[:N_TRAIN]
textos_train = [ds["train"][i]["sentence"] for i in idx]
y_train = [int(ds["train"][i]["label"]) for i in idx]
textos_test = list(ds["validation"]["sentence"])
y_test = [int(v) for v in ds["validation"]["label"]]

print(f"train={len(textos_train)}  test={len(textos_test)}")
print("ejemplo train:", textos_train[0], "→", y_train[0])
print("clases train:  neg=", sum(v == 0 for v in y_train), " pos=", sum(v == 1 for v in y_train))
print("clases test:   neg=", sum(v == 0 for v in y_test), " pos=", sum(v == 1 for v in y_test))

tokenizer = AutoTokenizer.from_pretrained(MODELO_PROFESOR)


def tokenizar(textos):
    enc = tokenizer(
        textos,
        padding="max_length",
        truncation=True,
        max_length=MAX_LEN,
        return_tensors="pt",
    )
    return {"input_ids": enc["input_ids"], "attention_mask": enc["attention_mask"]}


enc_train = tokenizar(textos_train)
enc_test = tokenizar(textos_test)


class SentimientoDS(Dataset):
    def __init__(self, enc, etiquetas):
        self.input_ids = enc["input_ids"]
        self.attention_mask = enc["attention_mask"]
        self.labels = torch.tensor(etiquetas, dtype=torch.long)

    def __len__(self):
        return int(self.labels.size(0))

    def __getitem__(self, i):
        return {
            "input_ids": self.input_ids[i],
            "attention_mask": self.attention_mask[i],
            "labels": self.labels[i],
            "idx": i,
        }


ds_train = SentimientoDS(enc_train, y_train)
ds_test = SentimientoDS(enc_test, y_test)
loader_train = DataLoader(ds_train, batch_size=BATCH_ESTUDIANTE, shuffle=True, num_workers=0)
loader_test = DataLoader(ds_test, batch_size=BATCH_ESTUDIANTE, shuffle=False, num_workers=0)
loader_train_ordenado = DataLoader(ds_train, batch_size=BATCH_PROFESOR, shuffle=False, num_workers=0)
loader_test_prof = DataLoader(ds_test, batch_size=BATCH_PROFESOR, shuffle=False, num_workers=0)
"""),
        md("""\
## 3. Profesor: cargar, evaluar y precomputar logits

La primera ejecución descarga el modelo al caché del proyecto (del orden de 250 MB). Después se reutiliza, incluso sin red si defines `HF_HUB_OFFLINE=1`.
"""),
        code("""\
profesor = AutoModelForSequenceClassification.from_pretrained(MODELO_PROFESOR)
profesor.to(DEVICE)
profesor.eval()
for p in profesor.parameters():
    p.requires_grad_(False)

n_prof = contar_parametros(profesor)
print(f"parámetros del profesor: {n_prof:,}")
print("etiquetas:", profesor.config.id2label)


def logits_de(loader, modelo):
    partes = []
    aciertos = 0
    total = 0
    with torch.no_grad():
        for lote in loader:
            ids = lote["input_ids"].to(DEVICE)
            mask = lote["attention_mask"].to(DEVICE)
            y = lote["labels"].to(DEVICE)
            logits = modelo(input_ids=ids, attention_mask=mask).logits
            partes.append(logits.cpu())
            aciertos += int((logits.argmax(dim=-1) == y).sum().item())
            total += int(y.size(0))
    return torch.cat(partes, dim=0), aciertos / max(total, 1)


print("Inferencia del profesor (una pasada por train y test)...")
t0 = time.perf_counter()
logits_train, acc_prof_train = logits_de(loader_train_ordenado, profesor)
logits_test, acc_prof_test = logits_de(loader_test_prof, profesor)
seg = time.perf_counter() - t0
print(f"listo en {seg:.1f} s  exactitud profesor: train={acc_prof_train:.3f}  test={acc_prof_test:.3f}")

ruta_logits = RUTAS["modelos"] / "sentimiento_logits_profesor.pt"
torch.save(
    {
        "train": logits_train,
        "test": logits_test,
        "modelo": MODELO_PROFESOR,
        "idx_train": idx,
        "semilla": SEMILLA,
    },
    ruta_logits,
)

# Latencia del profesor (lote de 16) antes de liberarlo.
lote_ej = next(iter(loader_test_prof))
# medir_latencia_ms espera un dict con input_ids; el wrapper del profesor de HF
# no es el mismo que el del estudiante. Medimos a mano.


def latencia_hf(modelo, lote, n_cal=5, n_reps=20):
    modelo.eval()
    ids = lote["input_ids"][:16].to(DEVICE)
    mask = lote["attention_mask"][:16].to(DEVICE)
    with torch.no_grad():
        for _ in range(n_cal):
            modelo(input_ids=ids, attention_mask=mask)
        if DEVICE.type == "cuda":
            torch.cuda.synchronize()
        tiempos = []
        for _ in range(n_reps):
            t1 = time.perf_counter()
            modelo(input_ids=ids, attention_mask=mask)
            if DEVICE.type == "cuda":
                torch.cuda.synchronize()
            tiempos.append((time.perf_counter() - t1) * 1000.0)
    arr = np.asarray(tiempos)
    return {
        "ms_lote_media": float(arr.mean()),
        "ms_lote_p50": float(np.percentile(arr, 50)),
        "ms_lote_p95": float(np.percentile(arr, 95)),
        "ms_por_ejemplo_media": float(arr.mean() / ids.size(0)),
        "n_reps": n_reps,
        "tamano_lote": int(ids.size(0)),
    }


lat_prof = latencia_hf(profesor, lote_ej)
print("latencia profesor:", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in lat_prof.items()})

# Liberar memoria: a partir de aquí solo viven los logits.
del profesor
gc.collect()
if DEVICE.type == "cuda":
    torch.cuda.empty_cache()
print("Profesor liberado de memoria. Logits guardados en", ruta_logits)
"""),
        md("""\
## 4. Estudiante diminuto

El estudiante no es un transformer: es un embedding + GRU bidireccional + una capa lineal. El vocabulario es el del profesor (unos 30 000 tokens), así que casi todos sus parámetros están en la matriz de embeddings. Aun así, queda en torno a **2 millones** de parámetros frente a los **66 millones** del DistilBERT: un orden de magnitud menor, y mucho más barato de ejecutar.
"""),
        code("""\
pad_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else 0
vocab = len(tokenizer)

fijar_semilla(SEMILLA)
plantilla = construir_estudiante_sentimiento(
    vocab_size=vocab,
    n_clases=2,
    dim_emb=DIM_EMB,
    dim_oculta=DIM_OCULTA,
    n_capas=N_CAPAS,
    pad_id=pad_id,
).to(DEVICE)
estado_inicial = {k: v.detach().cpu().clone() for k, v in plantilla.state_dict().items()}
n_est = contar_parametros(plantilla)
print(f"parámetros del estudiante: {n_est:,}  ({n_est / n_prof:.1%} del profesor)")
print("config:", plantilla.config)


def entrenar_estudiante(modelo, usar_destilacion, etiqueta):
    opt = optim.Adam(modelo.parameters(), lr=LR_ESTUDIANTE)
    historial = []
    for epoca in range(1, EPOCHS_ESTUDIANTE + 1):
        tr = entrenar_epoca(
            modelo,
            loader_train,
            opt,
            DEVICE,
            logits_profesor=logits_train if usar_destilacion else None,
            temperature=T_DISTIL,
            alpha=ALPHA if usar_destilacion else 0.0,
            indices_en_lote=True,
        )
        ev = evaluar_loader(modelo, loader_test, DEVICE)
        fila = {
            "epoca": epoca,
            "train_perdida": tr["perdida"],
            "train_exactitud": tr["exactitud"],
            "test_exactitud": ev["exactitud"],
            "test_perdida": ev["perdida_ce"],
        }
        historial.append(fila)
        print(
            f"{etiqueta:22s} época {epoca:2d}/{EPOCHS_ESTUDIANTE}  "
            f"train acc={tr['exactitud']:.3f}  test acc={ev['exactitud']:.3f}  "
            f"pérdida={tr['perdida']:.3f}"
        )
    return historial


estudiante_duro = construir_estudiante_sentimiento(
    vocab_size=vocab, n_clases=2, dim_emb=DIM_EMB, dim_oculta=DIM_OCULTA,
    n_capas=N_CAPAS, pad_id=pad_id,
).to(DEVICE)
estudiante_duro.load_state_dict(estado_inicial)
hist_duro = entrenar_estudiante(estudiante_duro, usar_destilacion=False, etiqueta="estudiante duro")

estudiante_kd = construir_estudiante_sentimiento(
    vocab_size=vocab, n_clases=2, dim_emb=DIM_EMB, dim_oculta=DIM_OCULTA,
    n_capas=N_CAPAS, pad_id=pad_id,
).to(DEVICE)
estudiante_kd.load_state_dict(estado_inicial)
hist_kd = entrenar_estudiante(estudiante_kd, usar_destilacion=True, etiqueta="estudiante destilado")

metricas_duro = evaluar_loader(estudiante_duro, loader_test, DEVICE)
metricas_kd = evaluar_loader(estudiante_kd, loader_test, DEVICE)
print("test duro:", metricas_duro)
print("test destilado:", metricas_kd)
print("test profesor:", acc_prof_test)
"""),
        md("""\
## 5. Curvas, ejemplos y artefactos
"""),
        code("""\
fig, ejes = plt.subplots(1, 2, figsize=(11, 3.8))
for hist, nombre, color in [
    (hist_duro, "estudiante duro", "#b36b00"),
    (hist_kd, "estudiante destilado", "#2a7f4f"),
]:
    ep = [f["epoca"] for f in hist]
    ejes[0].plot(ep, [f["train_exactitud"] for f in hist], marker="o", label=nombre, color=color)
    ejes[1].plot(ep, [f["test_exactitud"] for f in hist], marker="o", label=nombre, color=color)
for ax in ejes:
    ax.axhline(acc_prof_test, color="#1f4e79", linestyle="--", linewidth=1, label="profesor (test)")
    ax.set_xlabel("época")
    ax.set_ylabel("exactitud")
    ax.set_ylim(0.45, 1.01)
    ax.legend()
ejes[0].set_title("Exactitud en train")
ejes[1].set_title("Exactitud en test (validation SST-2)")
fig.tight_layout()
fig.savefig(RUTAS["resultados"] / "fig_sentimiento_curvas.png", bbox_inches="tight")
plt.show()

# Algunas frases: etiqueta real, predicción del estudiante destilado, y blandas del profesor.
estudiante_kd.eval()
n_show = 6
with torch.no_grad():
    lote = {k: v[:n_show] if torch.is_tensor(v) else v for k, v in next(iter(loader_test)).items()}
    pred = estudiante_kd(lote["input_ids"].to(DEVICE), lote["attention_mask"].to(DEVICE)).argmax(dim=-1).cpu()
    blandas = softmax_temperatura(logits_test[:n_show].numpy(), temperature=T_DISTIL)

filas = []
for i in range(n_show):
    filas.append(
        {
            "frase": textos_test[int(lote["idx"][i])][:80],
            "y": int(lote["labels"][i]),
            "pred_estudiante": int(pred[i]),
            "p_neg_profesor_T": round(float(blandas[i, 0]), 3),
            "p_pos_profesor_T": round(float(blandas[i, 1]), 3),
        }
    )
display(pd.DataFrame(filas))
"""),
        code("""\
lote_lat = next(iter(loader_test))
lat_duro = medir_latencia_ms(estudiante_duro, lote_lat, device=DEVICE)
lat_kd = medir_latencia_ms(estudiante_kd, lote_lat, device=DEVICE)

ruta_duro = RUTAS["modelos"] / "sentimiento_estudiante_duro.pt"
ruta_kd = RUTAS["modelos"] / "sentimiento_estudiante_destilado.pt"
meta = {
    "profesor": MODELO_PROFESOR,
    "n_train": N_TRAIN,
    "n_test": len(ds_test),
    "max_len": MAX_LEN,
    "temperature": T_DISTIL,
    "alpha": ALPHA,
    "semilla": SEMILLA,
    "dispositivo": str(DEVICE),
    "arquitectura_estudiante": plantilla.config,
}
guardar_checkpoint(estudiante_duro, ruta_duro, {**meta, "rol": "estudiante_duro", **metricas_duro})
guardar_checkpoint(estudiante_kd, ruta_kd, {**meta, "rol": "estudiante_destilado", **metricas_kd})

resultado = {
    "problema": "sst2-distilbert-a-gru",
    "profesor": MODELO_PROFESOR,
    "semilla": SEMILLA,
    "dispositivo": str(DEVICE),
    "temperature": T_DISTIL,
    "alpha": ALPHA,
    "n_train": N_TRAIN,
    "n_test": len(ds_test),
    "max_len": MAX_LEN,
    "modelos": {
        "profesor": {
            "ruta": MODELO_PROFESOR,
            "parametros": int(n_prof),
            "tamano_mb": None,
            "exactitud": acc_prof_test,
            "exactitud_train": acc_prof_train,
            "n": len(ds_test),
            **{f"latencia_{k}": v for k, v in lat_prof.items()},
        },
        "estudiante_duro": {
            "ruta": str(ruta_duro.relative_to(RAIZ)),
            "parametros": int(n_est),
            "tamano_mb": tamano_archivo_mb(ruta_duro),
            **metricas_duro,
            **{f"latencia_{k}": v for k, v in lat_duro.items()},
        },
        "estudiante_destilado": {
            "ruta": str(ruta_kd.relative_to(RAIZ)),
            "parametros": int(n_est),
            "tamano_mb": tamano_archivo_mb(ruta_kd),
            **metricas_kd,
            **{f"latencia_{k}": v for k, v in lat_kd.items()},
        },
    },
    "historial": {"estudiante_duro": hist_duro, "estudiante_destilado": hist_kd},
}
guardar_json(resultado, RUTAS["resultados"] / "sentimiento.json")

comp = pd.DataFrame(
    [
        {
            "modelo": nombre,
            "parametros": datos["parametros"],
            "tamano_mb": (None if datos.get("tamano_mb") is None else round(datos["tamano_mb"], 3)),
            "exactitud_test": round(datos["exactitud"], 4),
            "ms_por_ejemplo": round(datos["latencia_ms_por_ejemplo_media"], 4),
        }
        for nombre, datos in resultado["modelos"].items()
    ]
)
display(comp)
print("Artefactos escritos en modelos/ y resultados/sentimiento.json")
"""),
        md("""\
## Interpretación y cierre

- El profesor de Hugging Face no se ha reentrenado. En un equipo real eso importa: el profesor puede ser un modelo ya validado, versionado y costoso de volver a mover.
- El estudiante no va a igualar a DistilBERT con 3 000 frases y un GRU de un par de millones de parámetros. El éxito es **acercarse** más que el estudiante duro, con una latencia mucho menor.
- El tokenizador es parte del artefacto. Si en producción alguien tokeniza distinto, el estudiante no está recibiendo lo que aprendió.
- `resultados/sentimiento.json` es la entrada del cuaderno 04, junto con `resultados/mnist.json`.

Siguiente: `04-comparativa-y-produccion.ipynb`.
"""),
    ]


# ---------------------------------------------------------------------------
# 04 comparativa y produccion
# ---------------------------------------------------------------------------

def nb04():
    return [
        md("""\
# 04 · Comparativa y producción

**Objetivo de este cuaderno:** leer los artefactos de los cuadernos 02 y 03, comparar **exactitud, tamaño y latencia**, y sacar conclusiones que se puedan llevar a un servicio real. Aquí no se reentrena. Si faltan `resultados/mnist.json` o `resultados/sentimiento.json`, vuelve atrás y ejecuta 02 y 03.

La pregunta que organiza esta comparativa no es «¿quién tiene más exactitud?». Es: **¿qué calidad conserva el estudiante, a qué coste de inferencia, y qué habría que registrar y vigilar si lo pusiéramos en producción?**
"""),
        code(BOOTSTRAP),
        md("""\
## 1. Cargar resultados de 02 y 03
"""),
        code("""\
ruta_mnist = RUTAS["resultados"] / "mnist.json"
ruta_sent = RUTAS["resultados"] / "sentimiento.json"
faltan = [str(p) for p in (ruta_mnist, ruta_sent) if not p.exists()]
assert not faltan, (
    "Faltan resultados de cuadernos anteriores:\\n- "
    + "\\n- ".join(faltan)
    + "\\nEjecuta 02-destilacion-mnist-mlp.ipynb y 03-destilacion-bert-sentimiento.ipynb en ese orden."
)

mnist = cargar_json(ruta_mnist)
sent = cargar_json(ruta_sent)

def filas_de(nombre_problema, bloque):
    out = []
    for rol, d in bloque["modelos"].items():
        out.append(
            {
                "problema": nombre_problema,
                "modelo": rol,
                "parametros": d.get("parametros"),
                "tamano_mb": d.get("tamano_mb"),
                "exactitud_test": d.get("exactitud"),
                "ms_por_ejemplo": d.get("latencia_ms_por_ejemplo_media"),
                "ms_lote_p95": d.get("latencia_ms_lote_p95"),
                "tamano_lote_latencia": d.get("latencia_tamano_lote"),
                "dispositivo": bloque.get("dispositivo"),
                "temperature": bloque.get("temperature"),
                "alpha": bloque.get("alpha"),
            }
        )
    return out

comparativa = pd.DataFrame(filas_de("MNIST / MLP", mnist) + filas_de("SST-2 / DistilBERT→GRU", sent))
comparativa
"""),
        md("""\
## 2. Lectura de las cifras

Tres ángulos, en los dos problemas:

1. **Calidad:** ¿cuánto se deja el estudiante destilado respecto al profesor? ¿Mejora al estudiante duro?
2. **Tamaño:** parámetros y, cuando hay fichero, megas en disco. En sentimiento el profesor es un identificador de Hugging Face, no un `.pt` nuestro; el dato útil es el recuento de parámetros.
3. **Latencia:** milisegundos por ejemplo en el dispositivo en el que se midió (queda anotado). Es una medida de *esta máquina*, no un SLO de producción. Sirve para comparar modelos entre sí en las mismas condiciones.
"""),
        code("""\
def hueco(bloque, rol_a, rol_b, campo="exactitud"):
    return bloque["modelos"][rol_a][campo] - bloque["modelos"][rol_b][campo]


resumen = []
for nombre, bloque in [("MNIST / MLP", mnist), ("SST-2 / DistilBERT→GRU", sent)]:
    m = bloque["modelos"]
    acc_p = m["profesor"]["exactitud"]
    acc_d = m["estudiante_duro"]["exactitud"]
    acc_k = m["estudiante_destilado"]["exactitud"]
    lat_p = m["profesor"]["latencia_ms_por_ejemplo_media"]
    lat_k = m["estudiante_destilado"]["latencia_ms_por_ejemplo_media"]
    par_p = m["profesor"]["parametros"]
    par_k = m["estudiante_destilado"]["parametros"]
    resumen.append(
        {
            "problema": nombre,
            "acc_profesor": acc_p,
            "acc_estudiante_duro": acc_d,
            "acc_estudiante_destilado": acc_k,
            "hueco_destilado_vs_profesor": acc_k - acc_p,
            "mejora_vs_duro": acc_k - acc_d,
            "params_profesor": par_p,
            "params_estudiante": par_k,
            "ratio_params_est/prof": par_k / par_p,
            "aceleracion_latencia_prof/est": lat_p / lat_k if lat_k else None,
        }
    )

tabla_resumen = pd.DataFrame(resumen)
display(tabla_resumen.round(4))

# Figuras.
fig, ejes = plt.subplots(1, 3, figsize=(13.5, 4.0))

# Exactitud
for i, (nombre, bloque, color_base) in enumerate(
    [("MNIST", mnist, 0), ("SST-2", sent, 1)]
):
    xs = np.arange(3)
    vals = [
        bloque["modelos"]["profesor"]["exactitud"],
        bloque["modelos"]["estudiante_duro"]["exactitud"],
        bloque["modelos"]["estudiante_destilado"]["exactitud"],
    ]
    ejes[0].bar(xs + i * 0.38 - 0.19, vals, width=0.36, label=nombre)
ejes[0].set_xticks([0, 1, 2])
ejes[0].set_xticklabels(["profesor", "est. duro", "est. destilado"], rotation=15)
ejes[0].set_ylim(0, 1.05)
ejes[0].set_ylabel("exactitud en test")
ejes[0].set_title("Calidad")
ejes[0].legend()

# Parámetros (log)
for i, (nombre, bloque) in enumerate([("MNIST", mnist), ("SST-2", sent)]):
    xs = np.arange(3)
    vals = [
        bloque["modelos"]["profesor"]["parametros"],
        bloque["modelos"]["estudiante_duro"]["parametros"],
        bloque["modelos"]["estudiante_destilado"]["parametros"],
    ]
    ejes[1].bar(xs + i * 0.38 - 0.19, vals, width=0.36, label=nombre)
ejes[1].set_xticks([0, 1, 2])
ejes[1].set_xticklabels(["profesor", "est. duro", "est. destilado"], rotation=15)
ejes[1].set_yscale("log")
ejes[1].set_ylabel("parámetros (escala log)")
ejes[1].set_title("Tamaño")
ejes[1].legend()

# Latencia
for i, (nombre, bloque) in enumerate([("MNIST", mnist), ("SST-2", sent)]):
    xs = np.arange(3)
    vals = [
        bloque["modelos"]["profesor"]["latencia_ms_por_ejemplo_media"],
        bloque["modelos"]["estudiante_duro"]["latencia_ms_por_ejemplo_media"],
        bloque["modelos"]["estudiante_destilado"]["latencia_ms_por_ejemplo_media"],
    ]
    ejes[2].bar(xs + i * 0.38 - 0.19, vals, width=0.36, label=nombre)
ejes[2].set_xticks([0, 1, 2])
ejes[2].set_xticklabels(["profesor", "est. duro", "est. destilado"], rotation=15)
ejes[2].set_ylabel("ms por ejemplo")
ejes[2].set_title("Latencia (esta máquina)")
ejes[2].legend()

fig.tight_layout()
fig.savefig(RUTAS["resultados"] / "fig_comparativa_global.png", bbox_inches="tight")
plt.show()

# Frente Pareto: tamaño vs exactitud.
fig, ax = plt.subplots(figsize=(7.2, 4.2))
marcas = {"profesor": "o", "estudiante_duro": "s", "estudiante_destilado": "D"}
colores = {"MNIST / MLP": "#1f4e79", "SST-2 / DistilBERT→GRU": "#2a7f4f"}
for _, fila in comparativa.iterrows():
    ax.scatter(
        fila["parametros"],
        fila["exactitud_test"],
        marker=marcas[fila["modelo"]],
        color=colores[fila["problema"]],
        s=80,
        label=f"{fila['problema'].split(' / ')[0]} · {fila['modelo']}",
    )
ax.set_xscale("log")
ax.set_xlabel("parámetros (log)")
ax.set_ylabel("exactitud en test")
ax.set_title("Frente calidad / tamaño")
ax.legend(fontsize=8, loc="lower right")
fig.tight_layout()
fig.savefig(RUTAS["resultados"] / "fig_comparativa_pareto.png", bbox_inches="tight")
plt.show()
"""),
        md("""\
### Cómo leerlo

- En MNIST el contraste de latencia es pequeño: ambos modelos son MLP diminutos para una CPU moderna. El valor del experimento está en la **calidad con pocos datos**, no en el ahorro de milisegundos.
- En sentimiento el contraste de tamaño y de latencia es el que importa en un servicio: el profesor es un transformer; el estudiante, un GRU con un embedding compacto. El hueco de exactitud es el precio. Si ese precio cabe en el acuerdo de calidad del servicio, el estudiante es el que debería ir en el camino de la petición.
- «Mejora vs duro» es la ganancia *atribuible a destilar*, no a la arquitectura. Los dos estudiantes son el mismo modelo, con los mismos pesos iniciales.
"""),
        md("""\
## 3. Remedir latencia (opcional)

Si los pesos siguen en `modelos/`, se vuelve a medir en esta máquina. No es obligatorio: las cifras de 02 y 03 ya están en el JSON. Sirve para comprobar que el artefacto se carga y que la medida no dependía de un estado transitorio (otros procesos, primera ejecución, etc.).
"""),
        code("""\
import torch
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms

remeidiciones = []

# MNIST: reconstruir un lote y los tres MLP.
ruta_p = RAIZ / mnist["modelos"]["profesor"]["ruta"]
ruta_d = RAIZ / mnist["modelos"]["estudiante_duro"]["ruta"]
ruta_k = RAIZ / mnist["modelos"]["estudiante_destilado"]["ruta"]
if all(p.exists() for p in (ruta_p, ruta_d, ruta_k)):
    tfm = transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Normalize((0.1307,), (0.3081,)),
            transforms.Lambda(lambda t: t.reshape(-1)),
        ]
    )
    test_full = datasets.MNIST(RUTAS["datos"] / "mnist", train=False, download=False, transform=tfm)
    lote = next(iter(DataLoader(test_full, batch_size=64, shuffle=False)))[0]
    drop_p = mnist.get("dropout_profesor", 0.2)
    drop_e = mnist.get("dropout_estudiante", 0.0)
    for rol, ruta, anchos, drop in [
        ("profesor", ruta_p, mnist["modelos"]["profesor"]["anchos"], drop_p),
        ("estudiante_duro", ruta_d, mnist["modelos"]["estudiante_duro"]["anchos"], drop_e),
        ("estudiante_destilado", ruta_k, mnist["modelos"]["estudiante_destilado"]["anchos"], drop_e),
    ]:
        modelo = construir_mlp(anchos, dropout=drop).to(DEVICE)
        cargar_checkpoint(modelo, ruta, map_location="cpu")
        modelo.to(DEVICE).eval()
        lat = medir_latencia_ms(modelo, lote, device=DEVICE)
        remeidiciones.append({"problema": "mnist", "modelo": rol, **lat})
        del modelo
else:
    print("No están los tres pesos de MNIST; se mantiene la latencia del JSON.")

display(pd.DataFrame(remeidiciones) if remeidiciones else "Sin remedición de MNIST.")
guardar_json(
    {"comparativa": comparativa.to_dict(orient="records"), "resumen": resumen, "remeidiciones": remeidiciones},
    RUTAS["resultados"] / "comparativa.json",
)
print("Escrito resultados/comparativa.json")
"""),
        md("""\
## 4. Conclusiones de MLOps

Estas son las que conviene llevarse, más allá de MNIST y SST-2.

### Qué registrar junto al estudiante

No basta con un `estudiante.pt` y una exactitud. Un experimento de destilación, para poder repetirlo y auditarlo, debería dejar constancia de:

- Identidad del **profesor**: nombre o ruta, revisión (`commit` del Hub o hash del fichero), número de parámetros.
- Identidad del **estudiante**: arquitectura, hiperparámetros, hash de pesos.
- **Datos:** origen, recuento, partición, semilla, identificador o hash del subconjunto.
- **Hiperparámetros de destilación:** \\(T\\), \\(\\alpha\\), épocas, lote, tasa de aprendizaje.
- **Métricas:** exactitud (o la métrica de negocio) del profesor, del estudiante duro y del destilado, en validación y en test; acuerdo profesor-estudiante; tamaño; latencia p50 y p95 en un hardware descrito.
- El **tokenizador** o el preprocesamiento, versionado con el estudiante. No es un detalle: es parte del modelo.

En MLflow (o el registro que use el curso) eso son parámetros, métricas y artefactos de un mismo *run*. El profesor y el estudiante se promocionan **como pareja**.

### Criterio de promoción, no solo «el más exacto»

Un estudiante entra en el camino de la petición si cumple *a la vez*:

- un suelo de calidad (por ejemplo, no alejarse más de X puntos del profesor en test, o de un mínimo de negocio);
- un techo de coste (p95 de latencia, memoria, tamaño de imagen).

Si solo se mira la exactitud, el profesor siempre gana y no se despliega nada más barato. Si solo se mira la latencia, se puede promocionar un modelo que no cumple el acuerdo de calidad.

### El profesor no vive en la petición (o no debería)

El patrón de este material es deliberado: el profesor etiqueta o genera blandas **fuera** del request (aquí, precomputadas; en un sistema, en un job). El estudiante responde a la petición. El profesor se puede usar, de vez en cuando, como **sombra** sobre una muestra del tráfico para medir el acuerdo con el estudiante. Esa divergencia es una señal de deriva: cambió el lenguaje de entrada, cambió el profesor, o el estudiante se quedó viejo.

### Si actualizas al profesor, redestila

Un profesor nuevo (reentrenado, otra revisión del Hub) no se «hereda» solo. El estudiante hay que volver a destilarlo, evaluarlo y promoverlo. El versionado tiene que dejar claro *con qué profesor* se destiló cada estudiante.

### Riesgos que no desaparecen al destilar

- El estudiante **hereda sesgos** y errores del profesor. Si el profesor está mal calibrado, las blandas copian esa calibración.
- Un profesor mediocre destilado con \\(\\alpha\\) alto puede ser peor que entrenar al estudiante solo con etiquetas duras de calidad (el cuaderno 05 incluye un ejercicio sobre un «profesor» aleatorio).
- La latencia medida en un portátil no es la del contenedor en producción: hay que volver a medirla en el entorno real, con el lote real, en caliente.

### Cuándo merece la pena destilar

Tiene sentido cuando hay un profesor claramente mejor (más datos, más capacidad, ya validado) y una restricción real de coste o de latencia en el camino de la petición. Tiene menos sentido cuando el estudiante, con las etiquetas duras y los datos disponibles, ya iguala al profesor, o cuando no hay forma de servir el preprocesamiento del profesor junto al estudiante.
"""),
        md("""\
## Cierre

`resultados/comparativa.json` resume las cifras de 02 y 03. El cuaderno 05 parte de esta interpretación y pide decidir hiperparámetros, un criterio de promoción y lo que registrarías en un *run*.

Siguiente: `05-ejercicios.ipynb`.
"""),
    ]


# ---------------------------------------------------------------------------
# 05 ejercicios
# ---------------------------------------------------------------------------

def nb05():
    return [
        md("""\
# 05 · Ejercicios

**Objetivo de este cuaderno:** practicar lo de 01 a 04 sin rehacer toda la serie. Hay ejercicios ejecutables (celdas que deben correr de principio a fin) y preguntas de criterio, pensadas para un contexto de producción. Las **soluciones** están al final; conviene intentar cada ejercicio antes de bajar a ellas.

Si no has ejecutado 02 y 03, los ejercicios 1 y 4 siguen siendo factibles. El 2, el 3 y el 5 usan artefactos de esos cuadernos.
"""),
        code(BOOTSTRAP),
        md("""\
## Ejercicio 1 · Softmax con temperatura, a mano

Implementa `mi_softmax(logits, T)` en NumPy, numéricamente estable, y comprueba que coincide con `softmax_temperatura` del módulo compartido en varios vectores y temperaturas. No uses `scipy` ni `torch.softmax` dentro de tu función.
"""),
        code("""\
def mi_softmax(logits, T=1.0):
    # TODO: reemplaza esta implementación si quieres escribirla tú.
    # La celda de comprobación de más abajo debe seguir pasando.
    logits = np.asarray(logits, dtype=np.float64)
    z = logits / float(T)
    z = z - np.max(z, axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


rng = np.random.default_rng(SEMILLA)
casos = [
    np.array([2.0, 1.0, 0.1]),
    np.array([50.0, 49.0, 10.0]),  # valores grandes: aquí falla una exp ingenua
    rng.normal(size=(4, 10)),
]
for z in casos:
    for T in (0.5, 1.0, 3.0, 8.0):
        np.testing.assert_allclose(
            mi_softmax(z, T), softmax_temperatura(z, temperature=T), rtol=1e-10, atol=1e-10
        )
print("Ejercicio 1: tu softmax coincide con el del módulo en todos los casos.")
"""),
        md("""\
## Ejercicio 2 · Leer las blandas de un profesor real (MNIST)

Si existe `modelos/mnist_profesor.pt`, carga el profesor, toma 8 imágenes de test y pinta, para cada una, las probabilidades a \\(T=1\\) y a \\(T=5\\). Contesta (en una celda markdown tuya, o en voz alta): ¿en qué dígitos se ve más el conocimiento oscuro? ¿A qué clase «se parece» un 3 o un 4 según el profesor?
"""),
        code("""\
import torch
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

ruta_prof = RUTAS["modelos"] / "mnist_profesor.pt"
if not ruta_prof.exists():
    print("No está modelos/mnist_profesor.pt. Ejecuta el cuaderno 02 y vuelve a esta celda.")
else:
    meta_mnist = cargar_json(RUTAS["resultados"] / "mnist.json") if (RUTAS["resultados"] / "mnist.json").exists() else None
    anchos = (meta_mnist["modelos"]["profesor"]["anchos"] if meta_mnist else [784, 256, 128, 10])
    drop_p = (meta_mnist.get("dropout_profesor", 0.2) if meta_mnist else 0.2)
    profesor = construir_mlp(anchos, dropout=drop_p)
    cargar_checkpoint(profesor, ruta_prof, map_location="cpu")
    profesor.to(DEVICE).eval()

    tfm = transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Normalize((0.1307,), (0.3081,)),
            transforms.Lambda(lambda t: t.reshape(-1)),
        ]
    )
    test = datasets.MNIST(RUTAS["datos"] / "mnist", train=False, download=False, transform=tfm)
    x, y = next(iter(DataLoader(test, batch_size=8, shuffle=False)))
    with torch.no_grad():
        logits = profesor(x.to(DEVICE)).cpu().numpy()

    fig, ejes = plt.subplots(3, 8, figsize=(14, 5.2))
    for i in range(8):
        img = x[i].reshape(28, 28) * 0.3081 + 0.1307
        ejes[0, i].imshow(img.numpy(), cmap="gray")
        ejes[0, i].set_title(f"y={int(y[i])}")
        ejes[0, i].axis("off")
        for fila, T, titulo in [(1, 1.0, "T=1"), (2, 5.0, "T=5")]:
            ejes[fila, i].bar(range(10), softmax_temperatura(logits[i], temperature=T), color="#1f4e79")
            ejes[fila, i].set_ylim(0, 1)
            ejes[fila, i].set_xticks(range(10))
            if i == 0:
                ejes[fila, i].set_ylabel(titulo)
    fig.suptitle("Profesor de MNIST: la misma predicción, dos temperaturas")
    fig.tight_layout()
    fig.savefig(RUTAS["resultados"] / "fig_ejercicio2_blandas_mnist.png", bbox_inches="tight")
    plt.show()
    print("Predicción dura:", logits.argmax(axis=1), "etiquetas:", y.numpy())
"""),
        md("""\
## Ejercicio 3 · Un profesor inútil

La destilación no es magia: copia al profesor, también cuando el profesor no merece ser copiado. En esta celda se entrena, sobre un subconjunto pequeño de MNIST y **una sola época**, un estudiante con:

- las blandas del profesor real (si está el checkpoint);
- unas «blandas» aleatorias (logits gaussianos, un profesor de ruido).

Compara las exactitudes en test. ¿Qué esperas antes de ejecutar? ¿Lo confirma el número?
"""),
        code("""\
import torch
from torch import optim
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms

ruta_prof = RUTAS["modelos"] / "mnist_profesor.pt"
if not ruta_prof.exists():
    print("No está el profesor de MNIST. Ejecuta el cuaderno 02 y vuelve.")
else:
    meta = cargar_json(RUTAS["resultados"] / "mnist.json")
    anchos_p = meta["modelos"]["profesor"]["anchos"]
    anchos_e = meta["modelos"]["estudiante_duro"]["anchos"]
    drop_p = meta.get("dropout_profesor", 0.2)
    drop_e = meta.get("dropout_estudiante", 0.0)
    profesor = construir_mlp(anchos_p, dropout=drop_p)
    cargar_checkpoint(profesor, ruta_prof, map_location="cpu")
    profesor.to(DEVICE).eval()
    for p in profesor.parameters():
        p.requires_grad_(False)

    tfm = transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Normalize((0.1307,), (0.3081,)),
            transforms.Lambda(lambda t: t.reshape(-1)),
        ]
    )
    train_full = datasets.MNIST(RUTAS["datos"] / "mnist", train=True, download=False, transform=tfm)
    test_full = datasets.MNIST(RUTAS["datos"] / "mnist", train=False, download=False, transform=tfm)
    g = torch.Generator().manual_seed(SEMILLA)
    idx = torch.randperm(len(train_full), generator=g).tolist()[:2000]
    loader_mini = DataLoader(Subset(train_full, idx), batch_size=128, shuffle=True)
    loader_test = DataLoader(Subset(test_full, list(range(2000))), batch_size=256, shuffle=False)

    class ProfesorRuido(torch.nn.Module):
        def forward(self, x):
            return torch.randn(x.size(0), 10, device=x.device)

    ruido = ProfesorRuido().to(DEVICE)

    fijar_semilla(SEMILLA)
    est_real = construir_mlp(anchos_e, dropout=drop_e).to(DEVICE)
    estado = {k: v.detach().cpu().clone() for k, v in est_real.state_dict().items()}
    est_ruido = construir_mlp(anchos_e, dropout=drop_e).to(DEVICE)
    est_ruido.load_state_dict(estado)

    opt1 = optim.Adam(est_real.parameters(), lr=1e-3)
    opt2 = optim.Adam(est_ruido.parameters(), lr=1e-3)
    entrenar_epoca(est_real, loader_mini, opt1, DEVICE, profesor=profesor, temperature=3.0, alpha=1.0)
    entrenar_epoca(est_ruido, loader_mini, opt2, DEVICE, profesor=ruido, temperature=3.0, alpha=1.0)

    acc_real = evaluar_loader(est_real, loader_test, DEVICE)["exactitud"]
    acc_ruido = evaluar_loader(est_ruido, loader_test, DEVICE)["exactitud"]
    print(f"destilado de un profesor real (1 época, alpha=1): {acc_real:.3f}")
    print(f"destilado de un profesor de ruido (1 época, alpha=1): {acc_ruido:.3f}")
    print("Un profesor inútil, con alpha=1, arrastra al estudiante. Las blandas no son un atajo si la fuente es mala.")
"""),
        md("""\
## Ejercicio 4 · Qué registrarías en un *run*

Construye un diccionario `registro_run` (el equivalente a parámetros + métricas de MLflow) para el experimento de sentimiento del cuaderno 03. Debe incluir, como mínimo: identidad del profesor, arquitectura del estudiante, \\(T\\), \\(\\alpha\\), semilla, recuento de datos, exactitudes de los tres roles y una latencia. Si existe `resultados/sentimiento.json`, rellénalo con cifras reales. Si no, déjalo con el esquema y valores `None`.
"""),
        code("""\
ruta = RUTAS["resultados"] / "sentimiento.json"
datos = cargar_json(ruta) if ruta.exists() else None

registro_run = {
    "params": {
        "profesor_id": None,
        "estudiante_arquitectura": None,
        "temperature": None,
        "alpha": None,
        "semilla": None,
        "n_train": None,
        "n_test": None,
        "max_len": None,
        "dispositivo": None,
    },
    "metrics": {
        "acc_profesor": None,
        "acc_estudiante_duro": None,
        "acc_estudiante_destilado": None,
        "ms_por_ejemplo_profesor": None,
        "ms_por_ejemplo_estudiante_destilado": None,
        "params_profesor": None,
        "params_estudiante": None,
    },
}

if datos:
    registro_run["params"].update(
        {
            "profesor_id": datos["profesor"],
            "estudiante_arquitectura": "embedding-gru-bidireccional",
            "temperature": datos["temperature"],
            "alpha": datos["alpha"],
            "semilla": datos["semilla"],
            "n_train": datos["n_train"],
            "n_test": datos["n_test"],
            "max_len": datos["max_len"],
            "dispositivo": datos["dispositivo"],
        }
    )
    m = datos["modelos"]
    registro_run["metrics"].update(
        {
            "acc_profesor": m["profesor"]["exactitud"],
            "acc_estudiante_duro": m["estudiante_duro"]["exactitud"],
            "acc_estudiante_destilado": m["estudiante_destilado"]["exactitud"],
            "ms_por_ejemplo_profesor": m["profesor"]["latencia_ms_por_ejemplo_media"],
            "ms_por_ejemplo_estudiante_destilado": m["estudiante_destilado"]["latencia_ms_por_ejemplo_media"],
            "params_profesor": m["profesor"]["parametros"],
            "params_estudiante": m["estudiante_destilado"]["parametros"],
        }
    )

assert registro_run["params"].keys() >= {
    "profesor_id", "temperature", "alpha", "semilla", "n_train"
}
print(json.dumps(registro_run, ensure_ascii=False, indent=2))
guardar_json(registro_run, RUTAS["resultados"] / "ejercicio4_registro_run.json")
"""),
        md("""\
## Ejercicio 5 · Un criterio de promoción (pregunta de criterio)

Imagina un servicio de sentimiento con este acuerdo interno:

- la exactitud en el conjunto de evaluación no puede quedar a más de **4 puntos** del profesor;
- el p95 de latencia de un ejemplo en CPU tiene que ser **al menos 5 veces menor** que el del profesor, medido en la misma máquina.

Con las cifras de `resultados/sentimiento.json` (o de la comparativa del cuaderno 04), ¿promocionarías al estudiante destilado al camino de la petición? Escribe el cálculo y la decisión. Si el estudiante no cumple, ¿qué probarías antes de rendirte (más datos, otro \\(T\\), otra arquitectura, destilar un estudiante a medio camino entre los dos tamaños)?

No hay una única respuesta correcta: lo que se evalúa es que uses **los dos** criterios, no solo la exactitud.
"""),
        code("""\
ruta = RUTAS["resultados"] / "sentimiento.json"
if not ruta.exists():
    print("No está resultados/sentimiento.json. Ejecuta el cuaderno 03 (y, si puedes, el 04) y vuelve.")
else:
    d = cargar_json(ruta)["modelos"]
    acc_p = d["profesor"]["exactitud"]
    acc_k = d["estudiante_destilado"]["exactitud"]
    # En 03 medimos media, p50 y p95 por *lote*. Aproximamos el p95 por ejemplo
    # dividiendo el p95 del lote por el tamaño de lote (es una cota, no una medida por request).
    p95_p = d["profesor"]["latencia_ms_lote_p95"] / d["profesor"]["latencia_tamano_lote"]
    p95_k = d["estudiante_destilado"]["latencia_ms_lote_p95"] / d["estudiante_destilado"]["latencia_tamano_lote"]
    hueco_puntos = (acc_p - acc_k) * 100
    aceleracion = p95_p / p95_k if p95_k else float("inf")
    cumple_calidad = hueco_puntos <= 4.0 + 1e-9
    cumple_latencia = aceleracion >= 5.0
    decision = "PROMOCIONAR" if (cumple_calidad and cumple_latencia) else "NO PROMOCIONAR"
    print(f"hueco de exactitud: {hueco_puntos:.2f} puntos  (máx. admitido: 4)  → calidad ok={cumple_calidad}")
    print(f"aceleración p95 aprox.: {aceleracion:.1f}×  (mín. exigido: 5×)  → latencia ok={cumple_latencia}")
    print(f"decisión según el enunciado: {decision}")
    guardar_json(
        {
            "hueco_puntos": hueco_puntos,
            "aceleracion_p95": aceleracion,
            "cumple_calidad": cumple_calidad,
            "cumple_latencia": cumple_latencia,
            "decision": decision,
        },
        RUTAS["resultados"] / "ejercicio5_promocion.json",
    )
"""),
        md("""\
---

## Soluciones y comentarios

### Ejercicio 1

La implementación estable es: dividir por \\(T\\), restar el máximo del último eje, exponentiar y normalizar. Sin restar el máximo, el caso `[50, 49, 10]` puede desbordar. Si tu función coincide con `softmax_temperatura` en ese caso, está bien.

### Ejercicio 2

A \\(T=1\\) casi toda la masa cae en la clase ganadora y el conocimiento oscuro se ve poco. A \\(T=5\\) suelen aparecer masas residuales en dígitos **visualmente próximos**: 3 con 5 y 8, 4 con 9, 7 con 9, 0 con 6 u 8. Si en alguna imagen el profesor se equivoca, mira a qué clase «casi» iba: muchas veces es un confusor clásico de MNIST, no un dígito arbitrario.

### Ejercicio 3

Con \\(\\alpha = 1\\) el estudiante *solo* copia al profesor. Un profesor de ruido no tiene estructura que valga para clasificar dígitos: la exactitud del estudiante se queda cerca de la de un clasificador aleatorio (en torno a 0.10 en diez clases), mientras que el destilado del profesor real ya acierta bastante en una sola época. Conclusión operativa: no destiles un profesor que no hayas evaluado; un \\(\\alpha\\) alto amplifica al profesor, también cuando es malo. Si el profesor es dudoso, baja \\(\\alpha\\) o no destiles.

### Ejercicio 4

El diccionario de la celda es un esquema mínimo razonable. En un *run* real añadirías: revisión concreta del profesor en el Hub (`revision` / hash del snapshot), hash del subconjunto de train, el propio tokenizador como artefacto, y el acuerdo profesor-estudiante (porcentaje de coincidencia en test). El profesor y el estudiante se versionan juntos.

### Ejercicio 5

Hay que calcular las dos desigualdades, no elegir a ojo. El hueco es \\((acc_{prof} - acc_{est}) \\times 100\\) puntos. La aceleración se estima con el p95 del lote dividido por el tamaño de lote (en producción medirías request a request, o con el lote real del servicio). Si falla la calidad y cumple la latencia, un siguiente paso natural es un estudiante intermedio (más capacidad o más datos) o una búsqueda de \\(T\\) y \\(\\alpha\\) en validación. Si falla la latencia y cumple la calidad, hay que aligerar más (menos hidden, cuantización, otro lote) y volver a medir en el entorno de despliegue, no solo en este cuaderno.
"""),
    ]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    write_nb("00-introduccion-y-setup.ipynb", nb00())
    write_nb("01-teoria-softmax-temperatura.ipynb", nb01())
    write_nb("02-destilacion-mnist-mlp.ipynb", nb02())
    write_nb("03-destilacion-bert-sentimiento.ipynb", nb03())
    write_nb("04-comparativa-y-produccion.ipynb", nb04())
    write_nb("05-ejercicios.ipynb", nb05())


if __name__ == "__main__":
    main()
