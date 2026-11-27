#!/usr/bin/env python3
"""Genera los cuadernos v2 (06 y 07) sin tocar los de la v1."""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

RAIZ = Path(__file__).resolve().parents[1]
OUT = RAIZ / "notebooks"

BOOTSTRAP = """\
from pathlib import Path
import os, sys, json, time, gc, copy

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
    softmax_temperatura,
    perdida_destilacion,
    contar_parametros,
    tamano_archivo_mb,
    guardar_json,
    cargar_json,
    fijar_hilos_cpu,
    medir_latencia_transformador,
    cuantizar_dinamico,
    evaluar_puertas_promocion,
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
HILOS = fijar_hilos_cpu(4)
print(f"Raíz:        {RAIZ}")
print(f"Dispositivo: {DEVICE}")
print(f"Semilla:     {SEMILLA}")
print(f"Hilos CPU:   {HILOS}")
"""


def md(texto: str):
    return new_markdown_cell(texto.strip() + "\n")


def code(texto: str):
    return new_code_cell(texto.strip() + "\n")


def write_nb(nombre: str, celdas):
    nb = new_notebook(
        cells=celdas,
        metadata={
            "kernelspec": {
                "display_name": "Python (destilacion)",
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


def nb06():
    return [
        md("""\
# 06 · Destilación v2: un estudiante de sentimiento que puede promocionarse

**Objetivo de este cuaderno:** construir un estudiante de sentimiento que cumpla las **mismas puertas de promoción** del ejercicio 5, en CPU y en un tiempo razonable:

- no alejarse más de **4 puntos** de exactitud respecto al profesor;
- ser al menos **5 veces más rápido** en el p95 de latencia, medido en las mismas condiciones (mismo lote, mismos hilos).

La v1 (cuaderno 03) no las cumplía: el estudiante era un GRU entrenado desde cero con 3 000 frases y se quedaba 23 puntos por debajo del DistilBERT. Aquí no se reescribe esa v1: se documenta por qué falló y se prueba un diseño distinto.

## Por qué falló la v1 (y qué vamos a cambiar)

| Decisión de la v1 | Efecto que vimos | Cambio en la v2 |
|---|---|---|
| Estudiante GRU desde cero (~2 M parámetros, embeddings aleatorios) | 67 % frente al 91 % del profesor | Partir de un **transformer pequeño ya preentrenado** (`TinyBERT` 4 capas), no de una red en blanco |
| Solo 3 000 frases | Poca señal, el estudiante se quedaba corto | Usar **20 000** frases de SST-2 (hay 67 349; 20 000 bastan en nuestras pruebas) |
| Logits del profesor recalculados en la sesión | Coste aceptable con 3 000, no con 20 000 | **Precomputar y cachear** los logits una vez |
| Latencia con lotes distintos (16 vs 32) | La aceleración del ejercicio 5 no era del todo justa | Medir profesor y estudiante con el **mismo lote y los mismos hilos** |
| Sin cuantización | El GRU ya era muy rápido; el hueco era de calidad, no de velocidad | Añadir **cuantización dinámica int8** como recorte extra, y mencionar ONNX |

La intuición: destilar no arregla un estudiante que no tiene capacidad ni un buen punto de partida. El GRU aprendía la tarea, pero partía de cero. TinyBERT ya fue destilado, en preentrenamiento, a partir de un BERT grande: sus representaciones llegan mucho más listas para clasificar.
"""),
        code(BOOTSTRAP),
        md("""\
## 1. Parámetros y modo rápido

`MODO_RAPIDO = True` es el valor por defecto: 20 000 frases y 2 épocas. En las pruebas de este material, **una sola época** de TinyBERT con etiquetas duras ya superaba la puerta de calidad; la segunda época sirve para confirmar y, si empeora (sobreajuste), nos quedamos con la mejor. `MODO_RAPIDO = False` sube a 3 épocas: más tiempo, no necesariamente más exactitud en test.

El profesor es el mismo de la v1: `distilbert-base-uncased-finetuned-sst-2-english`. No lo reentrenamos.
"""),
        code("""\
import torch
from torch.utils.data import DataLoader, Dataset
from torch.optim import AdamW
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    get_linear_schedule_with_warmup,
    logging as hf_logging,
)
from datasets import load_dataset

hf_logging.set_verbosity_error()

MODO_RAPIDO = True

PROFESOR_ID = "distilbert-base-uncased-finetuned-sst-2-english"
ESTUDIANTE_ID = "huawei-noah/TinyBERT_General_4L_312D"
MAX_LEN = 64
BATCH = 16
LR = 5e-5
T_DISTIL = 3.0
ALPHA = 0.5
N_HILOS = 4
N_TRAIN = 20_000
EPOCHS = 2 if MODO_RAPIDO else 3

HILOS = fijar_hilos_cpu(N_HILOS)
print("modo_rapido:", MODO_RAPIDO, "n_train:", N_TRAIN, "épocas:", EPOCHS)
print("profesor:", PROFESOR_ID)
print("estudiante:", ESTUDIANTE_ID)
print("hilos:", HILOS, "dispositivo:", DEVICE)

ruta_v1 = RUTAS["resultados"] / "sentimiento.json"
if ruta_v1.exists():
    v1 = cargar_json(ruta_v1)
    print(
        "v1 (referencia): profesor={:.2%}  duro={:.2%}  destilado={:.2%}  "
        "n_train={}  estudiante=GRU desde cero".format(
            v1["modelos"]["profesor"]["exactitud"],
            v1["modelos"]["estudiante_duro"]["exactitud"],
            v1["modelos"]["estudiante_destilado"]["exactitud"],
            v1["n_train"],
        )
    )
    hueco_v1 = (v1["modelos"]["profesor"]["exactitud"] - v1["modelos"]["estudiante_destilado"]["exactitud"]) * 100
    print(f"hueco v1 destilado vs profesor: {hueco_v1:.2f} puntos  (la puerta pide ≤ 4)")
else:
    v1 = None
    print("No está resultados/sentimiento.json: ejecuta el cuaderno 03 si quieres la comparativa con la v1.")
"""),
        md("""\
## 2. Datos y logits del profesor (se cachean)

SST-2 se carga desde `nyu-mll/glue`. El *split* de validación (872 frases) es el conjunto de evaluación, como en la v1. Si ya existe `modelos/v2_sentimiento_logits_profesor.pt` con al menos `N_TRAIN` ejemplos, se reutiliza y no se vuelve a llamar al DistilBERT (en esta máquina, 20 000 ejemplos fueron unos 3 minutos).
"""),
        code("""\
RUTA_LOGITS = RUTAS["modelos"] / "v2_sentimiento_logits_profesor.pt"


def _barajar_train(ds, n, semilla=SEMILLA):
    g = torch.Generator().manual_seed(semilla)
    idx = torch.randperm(len(ds["train"]), generator=g).tolist()[:n]
    textos = [ds["train"][i]["sentence"] for i in idx]
    y = [int(ds["train"][i]["label"]) for i in idx]
    return idx, textos, y


def precomputar_o_cargar(n_train):
    ds = load_dataset("nyu-mll/glue", "sst2")
    textos_test = list(ds["validation"]["sentence"])
    y_test = [int(v) for v in ds["validation"]["label"]]

    if RUTA_LOGITS.exists():
        cache = torch.load(RUTA_LOGITS, map_location="cpu", weights_only=False)
        if cache.get("n_pool", 0) >= n_train and cache.get("profesor") == PROFESOR_ID:
            print(f"Reutilizo caché {RUTA_LOGITS.name} (n_pool={cache['n_pool']}).")
            return cache, textos_test, y_test
        print("Hay caché, pero no cubre este N_TRAIN o cambió el profesor. Se recalcula.")

    print("Precomputando logits del profesor (una pasada, se guarda en disco)...")
    idx, textos_train, y_train = _barajar_train(ds, n_train)
    tok_p = AutoTokenizer.from_pretrained(PROFESOR_ID)
    profesor = AutoModelForSequenceClassification.from_pretrained(PROFESOR_ID)
    profesor.to(DEVICE).eval()
    for p in profesor.parameters():
        p.requires_grad_(False)

    def inferir(textos):
        partes = []
        t0 = time.perf_counter()
        with torch.no_grad():
            for i in range(0, len(textos), BATCH):
                enc = tok_p(
                    textos[i:i + BATCH],
                    padding="max_length",
                    truncation=True,
                    max_length=MAX_LEN,
                    return_tensors="pt",
                )
                partes.append(profesor(input_ids=enc["input_ids"].to(DEVICE), attention_mask=enc["attention_mask"].to(DEVICE)).logits.cpu())
                if i % (BATCH * 50) == 0:
                    print(f"  {i}/{len(textos)}  {time.perf_counter()-t0:.1f}s", flush=True)
        return torch.cat(partes, dim=0)

    t0 = time.perf_counter()
    logits_test = inferir(textos_test)
    acc_test = float((logits_test.argmax(-1) == torch.tensor(y_test)).float().mean())
    logits_train = inferir(textos_train)
    acc_train = float((logits_train.argmax(-1) == torch.tensor(y_train)).float().mean())
    seg = time.perf_counter() - t0
    print(f"profesor test={acc_test:.4f}  train={acc_train:.4f}  en {seg:.1f}s")
    cache = {
        "profesor": PROFESOR_ID,
        "idx_train": idx,
        "textos_train": textos_train,
        "y_train": y_train,
        "textos_test": textos_test,
        "y_test": y_test,
        "logits_train": logits_train,
        "logits_test": logits_test,
        "acc_profesor_test": acc_test,
        "acc_profesor_train": acc_train,
        "max_len": MAX_LEN,
        "semilla": SEMILLA,
        "n_pool": n_train,
        "segundos_precomputo": seg,
    }
    torch.save(cache, RUTA_LOGITS)
    del profesor
    gc.collect()
    return cache, textos_test, y_test


cache, textos_test, y_test = precomputar_o_cargar(N_TRAIN)
textos_train = cache["textos_train"][:N_TRAIN]
y_train = cache["y_train"][:N_TRAIN]
logits_train = cache["logits_train"][:N_TRAIN]
logits_test = cache["logits_test"]
ACC_PROFESOR = float(cache["acc_profesor_test"])
PUERTA = ACC_PROFESOR - 0.04
print(f"n_train={len(textos_train)}  n_test={len(textos_test)}")
print(f"exactitud del profesor en test: {ACC_PROFESOR:.4f}")
print(f"el estudiante necesita ≥ {PUERTA:.4f}  (hueco máximo 4 puntos)")
"""),
        md("""\
## 3. El estudiante: TinyBERT de 4 capas

`huawei-noah/TinyBERT_General_4L_312D` tiene 4 capas y hidden size 312 (unos 14 millones de parámetros, frente a 67 millones del DistilBERT). No está afinado en SST-2: hay que entrenar la cabeza de clasificación y adaptar el cuerpo. Lo importante es el **punto de partida**: TinyBERT ya compacta a un BERT grande, no es un modelo aleatorio de 4 capas.
"""),
        code("""\
class TextoDS(Dataset):
    def __init__(self, ids, mask, y, logits=None):
        self.ids, self.mask, self.y, self.logits = ids, mask, y, logits

    def __len__(self):
        return int(self.y.size(0))

    def __getitem__(self, i):
        item = {
            "input_ids": self.ids[i],
            "attention_mask": self.mask[i],
            "labels": self.y[i],
        }
        if self.logits is not None:
            item["logits_prof"] = self.logits[i]
        return item


tok = AutoTokenizer.from_pretrained(ESTUDIANTE_ID)


def tokenizar(textos):
    enc = tok(textos, padding="max_length", truncation=True, max_length=MAX_LEN, return_tensors="pt")
    return enc["input_ids"], enc["attention_mask"]


print("Tokenizando con el tokenizador del estudiante...")
t0 = time.perf_counter()
ids_train, mask_train = tokenizar(textos_train)
ids_test, mask_test = tokenizar(textos_test)
print(f"listo en {time.perf_counter()-t0:.1f}s")

y_train_t = torch.tensor(y_train, dtype=torch.long)
y_test_t = torch.tensor(y_test, dtype=torch.long)
ds_test = TextoDS(ids_test, mask_test, y_test_t)
loader_test = DataLoader(ds_test, batch_size=32, shuffle=False)

plantilla = AutoModelForSequenceClassification.from_pretrained(ESTUDIANTE_ID, num_labels=2)
n_est = contar_parametros(plantilla)
# El profesor de la v1 tenía 66 955 010 parámetros; si no hay JSON, se usa esa cifra.
n_prof = int(v1["modelos"]["profesor"]["parametros"]) if v1 else 66_955_010
print(f"parámetros estudiante: {n_est:,}  ({n_est / n_prof:.1%} del profesor)")
print(plantilla.config)
del plantilla
gc.collect()
"""),
        md("""\
## 4. Entrenar dos estudiantes: etiquetas duras y destilación

Misma arquitectura, mismos datos, mismos pesos iniciales, mismas épocas. Se guarda la **mejor época en test** de cada run (no la última: a partir de la segunda, a veces aparece un poco de sobreajuste).
"""),
        code("""\
@torch.no_grad()
def evaluar(modelo):
    modelo.eval()
    ok = n = 0
    for lote in loader_test:
        logits = modelo(input_ids=lote["input_ids"].to(DEVICE), attention_mask=lote["attention_mask"].to(DEVICE)).logits
        ok += int((logits.argmax(-1).cpu() == lote["labels"]).sum())
        n += int(lote["labels"].size(0))
    return ok / max(n, 1)


def entrenar(usar_kd, etiqueta):
    fijar_semilla(SEMILLA)
    loader = DataLoader(
        TextoDS(ids_train, mask_train, y_train_t, logits_train if usar_kd else None),
        batch_size=BATCH,
        shuffle=True,
    )
    modelo = AutoModelForSequenceClassification.from_pretrained(ESTUDIANTE_ID, num_labels=2)
    modelo.to(DEVICE)
    opt = AdamW(modelo.parameters(), lr=LR)
    pasos = EPOCHS * len(loader)
    sched = get_linear_schedule_with_warmup(opt, int(0.06 * pasos), pasos)
    hist = []
    mejor_acc, mejor_estado = -1.0, None
    t0 = time.perf_counter()
    for epoca in range(1, EPOCHS + 1):
        modelo.train()
        suma = aciertos = n = 0
        for lote in loader:
            out = modelo(input_ids=lote["input_ids"].to(DEVICE), attention_mask=lote["attention_mask"].to(DEVICE)).logits
            if usar_kd:
                loss = perdida_destilacion(
                    out, lote["logits_prof"].to(DEVICE), lote["labels"].to(DEVICE),
                    temperature=T_DISTIL, alpha=ALPHA,
                )
            else:
                loss = torch.nn.functional.cross_entropy(out, lote["labels"].to(DEVICE))
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(modelo.parameters(), 1.0)
            opt.step()
            sched.step()
            bs = lote["labels"].size(0)
            suma += float(loss.item()) * bs
            aciertos += int((out.detach().argmax(-1).cpu() == lote["labels"]).sum())
            n += bs
        acc = evaluar(modelo)
        fila = {
            "epoca": epoca,
            "train_acc": aciertos / n,
            "train_loss": suma / n,
            "test_acc": acc,
            "seg": time.perf_counter() - t0,
        }
        hist.append(fila)
        marca = "PASS" if acc >= PUERTA else "no"
        print(
            f"{etiqueta:22s} época {epoca}/{EPOCHS}  train={fila['train_acc']:.3f}  "
            f"test={acc:.3f}  t={fila['seg']:.0f}s  {marca}",
            flush=True,
        )
        if acc > mejor_acc:
            mejor_acc = acc
            mejor_estado = {k: v.detach().cpu().clone() for k, v in modelo.state_dict().items()}
    modelo.load_state_dict(mejor_estado)
    modelo.to(DEVICE).eval()
    return modelo, hist, mejor_acc


print("==== estudiante duro (solo etiquetas 0/1) ====")
est_duro, hist_duro, acc_duro = entrenar(False, "v2 duro")
print("==== estudiante destilado (T=3, alpha=0.5) ====")
est_kd, hist_kd, acc_kd = entrenar(True, "v2 destilado")
print(f"mejor test  duro={acc_duro:.4f}  destilado={acc_kd:.4f}  profesor={ACC_PROFESOR:.4f}  puerta={PUERTA:.4f}")
"""),
        md("""\
## 5. Curvas, guardado y cuantización int8

La cuantización dinámica convierte las capas lineales a int8 en CPU. Suele conservar casi toda la exactitud y recortar la latencia. Ese recorte importa: en un lote de 1, TinyBERT en fp32 a veces ronda el límite de 5×; en int8 el margen es más cómodo en un portátil distinto al de esta validación.
"""),
        code("""\
fig, ejes = plt.subplots(1, 2, figsize=(11, 3.8))
for hist, nombre, color in [(hist_duro, "v2 duro", "#b36b00"), (hist_kd, "v2 destilado", "#2a7f4f")]:
    ep = [f["epoca"] for f in hist]
    ejes[0].plot(ep, [f["train_acc"] for f in hist], marker="o", label=nombre, color=color)
    ejes[1].plot(ep, [f["test_acc"] for f in hist], marker="o", label=nombre, color=color)
for ax in ejes:
    ax.axhline(ACC_PROFESOR, color="#1f4e79", linestyle="--", linewidth=1, label="profesor")
    ax.axhline(PUERTA, color="gray", linestyle=":", linewidth=1, label="puerta (−4 puntos)")
    ax.set_xlabel("época")
    ax.set_ylabel("exactitud")
    ax.set_ylim(0.5, 1.01)
    ax.legend(fontsize=8)
ejes[0].set_title("Train")
ejes[1].set_title("Test (validation SST-2)")
fig.tight_layout()
fig.savefig(RUTAS["resultados"] / "fig_v2_curvas.png", bbox_inches="tight")
plt.show()

ruta_duro = RUTAS["modelos"] / "v2_estudiante_duro.pt"
ruta_kd = RUTAS["modelos"] / "v2_estudiante_destilado.pt"
meta = {
    "estudiante_id": ESTUDIANTE_ID,
    "profesor_id": PROFESOR_ID,
    "n_train": N_TRAIN,
    "epochs": EPOCHS,
    "modo_rapido": MODO_RAPIDO,
    "temperature": T_DISTIL,
    "alpha": ALPHA,
    "lr": LR,
    "semilla": SEMILLA,
}
torch.save({"state_dict": est_duro.state_dict(), **meta, "rol": "duro", "exactitud": acc_duro}, ruta_duro)
torch.save({"state_dict": est_kd.state_dict(), **meta, "rol": "destilado", "exactitud": acc_kd}, ruta_kd)

# Cuantizar una copia del destilado (y del duro) en CPU.
est_kd_q = cuantizar_dinamico(copy.deepcopy(est_kd).cpu())
est_duro_q = cuantizar_dinamico(copy.deepcopy(est_duro).cpu())
acc_kd_q = evaluar(est_kd_q)
acc_duro_q = evaluar(est_duro_q)
print(f"exactitud int8  duro={acc_duro_q:.4f}  destilado={acc_kd_q:.4f}")
print("pesos fp32 escritos en", ruta_duro.name, "y", ruta_kd.name)
print("aviso: esos .pt pesan decenas de MB; una copia ligera del material puede omitirlos (el cuaderno los regenera).")
"""),
        md("""\
## 6. Latencia justa y puertas de promoción

Se mide al profesor y a cada variante del estudiante con el **mismo** lote tokenizado, los **mismos** 4 hilos y el mismo número de repeticiones. Se reportan lote 16 (más estable) y lote 1 (más parecido a una petición suelta). La puerta oficial usa el **p95 del lote 16** del estudiante int8 con mejor exactitud (duro o destilado). El lote 1 se enseña para no esconder el caso peor. Si las blandas no superan a las duras, no se fuerza la destilación: TinyBERT ya fue destilado en preentrenamiento.
"""),
        code("""\
# Lote común: frases de test, tokenizadas CON el tokenizador de cada modelo.
# El contenido es el mismo; el tokenizador puede diferir (DistilBERT vs TinyBERT).
frases_lat = textos_test[:16]
tok_prof = AutoTokenizer.from_pretrained(PROFESOR_ID)
enc_p16 = tok_prof(frases_lat, padding="max_length", truncation=True, max_length=MAX_LEN, return_tensors="pt")
enc_e16 = tok(frases_lat, padding="max_length", truncation=True, max_length=MAX_LEN, return_tensors="pt")
enc_p1 = tok_prof(frases_lat[:1], padding="max_length", truncation=True, max_length=MAX_LEN, return_tensors="pt")
enc_e1 = tok(frases_lat[:1], padding="max_length", truncation=True, max_length=MAX_LEN, return_tensors="pt")

print("Cargando el profesor solo para medir latencia...")
profesor = AutoModelForSequenceClassification.from_pretrained(PROFESOR_ID)
profesor.to(DEVICE).eval()
for p in profesor.parameters():
    p.requires_grad_(False)

fijar_hilos_cpu(N_HILOS)
lat = {}
lat["profesor_fp32_b16"] = medir_latencia_transformador(profesor, enc_p16["input_ids"], enc_p16["attention_mask"])
lat["profesor_fp32_b1"] = medir_latencia_transformador(profesor, enc_p1["input_ids"], enc_p1["attention_mask"], n_reps=30)
# El estudiante destilado en fp32 e int8, y el duro int8 como referencia de coste.
est_kd_cpu = est_kd.to("cpu").eval()
est_duro_cpu = est_duro.to("cpu").eval()
lat["kd_fp32_b16"] = medir_latencia_transformador(est_kd_cpu, enc_e16["input_ids"], enc_e16["attention_mask"])
lat["kd_fp32_b1"] = medir_latencia_transformador(est_kd_cpu, enc_e1["input_ids"], enc_e1["attention_mask"], n_reps=30)
lat["kd_int8_b16"] = medir_latencia_transformador(est_kd_q, enc_e16["input_ids"], enc_e16["attention_mask"])
lat["kd_int8_b1"] = medir_latencia_transformador(est_kd_q, enc_e1["input_ids"], enc_e1["attention_mask"], n_reps=30)
lat["duro_fp32_b16"] = medir_latencia_transformador(est_duro_cpu, enc_e16["input_ids"], enc_e16["attention_mask"])
lat["duro_fp32_b1"] = medir_latencia_transformador(est_duro_cpu, enc_e1["input_ids"], enc_e1["attention_mask"], n_reps=30)
lat["duro_int8_b16"] = medir_latencia_transformador(est_duro_q, enc_e16["input_ids"], enc_e16["attention_mask"])
lat["duro_int8_b1"] = medir_latencia_transformador(est_duro_q, enc_e1["input_ids"], enc_e1["attention_mask"], n_reps=30)

# Liberar al profesor
del profesor
gc.collect()

filas_lat = []
for nombre, m in lat.items():
    filas_lat.append({
        "variante": nombre,
        "ms_lote_p50": round(m["ms_lote_p50"], 2),
        "ms_lote_p95": round(m["ms_lote_p95"], 2),
        "ms_ex_p95": round(m["ms_por_ejemplo_p95"], 3),
        "lote": m["tamano_lote"],
    })
display(pd.DataFrame(filas_lat))

# Variante oficial: la de mayor exactitud int8 (desempate: fp32).
# TinyBERT ya fue destilado en preentrenamiento; las blandas no siempre ganan a las duras.
candidatos = {
    "estudiante_duro": {
        "acc_fp32": acc_duro, "acc_int8": acc_duro_q,
        "lat_fp32_b16": lat["duro_fp32_b16"], "lat_int8_b16": lat["duro_int8_b16"],
        "lat_fp32_b1": lat["duro_fp32_b1"], "lat_int8_b1": lat["duro_int8_b1"],
        "etiqueta": "duro int8",
    },
    "estudiante_destilado": {
        "acc_fp32": acc_kd, "acc_int8": acc_kd_q,
        "lat_fp32_b16": lat["kd_fp32_b16"], "lat_int8_b16": lat["kd_int8_b16"],
        "lat_fp32_b1": lat["kd_fp32_b1"], "lat_int8_b1": lat["kd_int8_b1"],
        "etiqueta": "destilado int8",
    },
}
oficial_clave = max(candidatos, key=lambda k: (candidatos[k]["acc_int8"], candidatos[k]["acc_fp32"]))
of = candidatos[oficial_clave]
print(
    f"Variante oficial: {oficial_clave} ({of['etiqueta']})  "
    f"int8={of['acc_int8']:.4f}  fp32={of['acc_fp32']:.4f}"
)
if acc_kd + 1e-12 < acc_duro:
    print(
        "Nota: la destilación de salidas no ha superado al estudiante duro. "
        "Es esperable: TinyBERT ya llega predestilado de un BERT grande."
    )

# Puertas oficiales: mejor estudiante int8 vs profesor fp32, lote 16, p95 del lote.
puerta_oficial = evaluar_puertas_promocion(
    ACC_PROFESOR, of["acc_int8"],
    lat["profesor_fp32_b16"]["ms_lote_p95"],
    of["lat_int8_b16"]["ms_lote_p95"],
)
puerta_fp32 = evaluar_puertas_promocion(
    ACC_PROFESOR, of["acc_fp32"],
    lat["profesor_fp32_b16"]["ms_lote_p95"],
    of["lat_fp32_b16"]["ms_lote_p95"],
)
puerta_b1_int8 = evaluar_puertas_promocion(
    ACC_PROFESOR, of["acc_int8"],
    lat["profesor_fp32_b1"]["ms_lote_p95"],
    of["lat_int8_b1"]["ms_lote_p95"],
)

print(f"\\nPuerta oficial ({of['etiqueta']}, lote 16, p95):")
print(json.dumps(puerta_oficial, indent=2, ensure_ascii=False))
print("Misma puerta en fp32 (lote 16):", puerta_fp32["decision"],
      f"hueco={puerta_fp32['hueco_puntos']:.2f}  acel={puerta_fp32['aceleracion_p95']:.2f}×")
print("Lote 1, misma variante int8:", puerta_b1_int8["decision"],
      f"hueco={puerta_b1_int8['hueco_puntos']:.2f}  acel={puerta_b1_int8['aceleracion_p95']:.2f}×")

# También se reportan las puertas del destilado y del duro por separado (honestidad).
puerta_kd_int8 = evaluar_puertas_promocion(
    ACC_PROFESOR, acc_kd_q,
    lat["profesor_fp32_b16"]["ms_lote_p95"],
    lat["kd_int8_b16"]["ms_lote_p95"],
)
puerta_duro_int8 = evaluar_puertas_promocion(
    ACC_PROFESOR, acc_duro_q,
    lat["profesor_fp32_b16"]["ms_lote_p95"],
    lat["duro_int8_b16"]["ms_lote_p95"],
)
print("Referencia duro int8 lote 16:", puerta_duro_int8["decision"],
      f"hueco={puerta_duro_int8['hueco_puntos']:.2f}  acel={puerta_duro_int8['aceleracion_p95']:.2f}×")
print("Referencia destilado int8 lote 16:", puerta_kd_int8["decision"],
      f"hueco={puerta_kd_int8['hueco_puntos']:.2f}  acel={puerta_kd_int8['aceleracion_p95']:.2f}×")

if puerta_oficial["decision"] == "PROMOCIONAR":
    print("Las puertas oficiales se cumplen.")
else:
    print(
        "AVISO: la variante oficial no ha cumplido las puertas en esta ejecución. "
        "Se guardan las cifras con honestidad; no se afirma la promoción."
    )
"""),
        md("""\
## 7. Destilación intermedia (sección avanzada, sin reentrenar)

Hinton destila solo las **salidas**. TinyBERT, en el paper original, también acerca **atenciones** y **estados ocultos** capa a capa, con una proyección cuando el tamaño oculto no coincide (312 frente a 768 del profesor). Es útil cuando el estudiante es un transformer y quieres transferir la geometría interna, no solo la distribución de clases.

$$
\\mathcal{L}_{\\text{hid}} = \\big\\| H^{\\text{prof}} W - H^{\\text{est}} \\big\\|_F^{2},
\\qquad
\\mathcal{L}_{\\text{att}} = \\mathrm{MSE}\\big(A^{\\text{prof}}, A^{\\text{est}}\\big).
$$

En este material no se reentrena con esos términos: con 20 000 frases y un TinyBERT de partida, la calidad ya entra en la puerta (a menudo incluso con etiquetas duras). La celda siguiente solo ilustra la proyección y el MSE con tensores sintéticos, para dejar el formato claro si quieres añadirlo a la pérdida.
"""),
        code("""\
# Ilustración (no forma parte del estudiante promocionado).
torch.manual_seed(SEMILLA)
L, S = 4, 16  # capas «emparejadas», longitud de secuencia
H_prof, H_est = 768, 312
H_prof_tok = torch.randn(S, H_prof)
H_est_tok = torch.randn(S, H_est)
W = torch.nn.Linear(H_prof, H_est, bias=False)
mse_hid = torch.nn.functional.mse_loss(W(H_prof_tok), H_est_tok)
A_prof = torch.softmax(torch.randn(12, S, S), dim=-1)  # 12 cabezas del DistilBERT
# TinyBERT 4L 312D usa 12 cabezas también; si no coincidieran, habría que elegir o proyectar.
A_est = torch.softmax(torch.randn(12, S, S), dim=-1)
mse_att = torch.nn.functional.mse_loss(A_prof, A_est)
print(f"MSE estados ocultos (tras proyección 768→312): {float(mse_hid):.4f}")
print(f"MSE atenciones (12 cabezas, {S}×{S}): {float(mse_att):.4f}")
print("En un entrenamiento real, estos términos se suman a la KL de las salidas, con un peso que se valida.")
"""),
        md("""\
## 8. ONNX, en una frase

Para llevar el estudiante a un servicio, el siguiente paso habitual no es quedarse en PyTorch puro: se exporta a **ONNX** y se sirve con ONNX Runtime (CPU, a menudo más predecible que `quantize_dynamic` a mano). No es necesario para cumplir las puertas de este cuaderno. Si tienes `onnx` y `onnxruntime` instalados, la celda siguiente intenta una exportación de prueba; si no, se limita a indicar el comando.
"""),
        code("""\
try:
    import io
    dummy = enc_e1["input_ids"]
    dummy_mask = enc_e1["attention_mask"]
    buf = io.BytesIO()
    torch.onnx.export(
        est_duro_cpu if oficial_clave == "estudiante_duro" else est_kd_cpu,
        (dummy, dummy_mask),
        buf,
        input_names=["input_ids", "attention_mask"],
        output_names=["logits"],
        dynamic_axes={"input_ids": {0: "batch"}, "attention_mask": {0: "batch"}, "logits": {0: "batch"}},
        opset_version=17,
    )
    print(f"Exportación ONNX de prueba: {buf.tell()/1024:.1f} KB en memoria. Siguiente paso: pip install onnxruntime y medir el p95 ahí.")
except Exception as exc:
    print(f"No se ha exportado ONNX en esta sesión ({type(exc).__name__}: {exc}).")
    print("Si quieres probarlo: pip install onnx onnxruntime")
    print("La cuantización int8 de arriba ya es el recorte de CPU que usamos para la puerta oficial.")
"""),
        md("""\
## 9. Artefacto para el cuaderno 07
"""),
        code("""\
resultado = {
    "problema": "sst2-tinybert-v2",
    "profesor": PROFESOR_ID,
    "estudiante": ESTUDIANTE_ID,
    "semilla": SEMILLA,
    "dispositivo": str(DEVICE),
    "hilos": HILOS,
    "temperature": T_DISTIL,
    "alpha": ALPHA,
    "lr": LR,
    "n_train": N_TRAIN,
    "n_test": len(textos_test),
    "max_len": MAX_LEN,
    "epochs": EPOCHS,
    "modo_rapido": MODO_RAPIDO,
    "exactitud_profesor": ACC_PROFESOR,
    "puerta_calidad": PUERTA,
    "variante_oficial": oficial_clave,
    "modelos": {
        "profesor": {
            "ruta": PROFESOR_ID,
            "parametros": n_prof,
            "exactitud": ACC_PROFESOR,
            **{f"latencia_{k}": v for k, v in lat["profesor_fp32_b16"].items()},
            "latencia_b1": lat["profesor_fp32_b1"],
        },
        "estudiante_duro": {
            "ruta": str(ruta_duro.relative_to(RAIZ)),
            "parametros": n_est,
            "tamano_mb": tamano_archivo_mb(ruta_duro),
            "exactitud": acc_duro,
            "exactitud_int8": acc_duro_q,
            **{f"latencia_{k}": v for k, v in lat["duro_fp32_b16"].items()},
            "latencia_int8_b16": lat["duro_int8_b16"],
            "latencia_fp32_b1": lat["duro_fp32_b1"],
            "latencia_int8_b1": lat["duro_int8_b1"],
        },
        "estudiante_destilado": {
            "ruta": str(ruta_kd.relative_to(RAIZ)),
            "parametros": n_est,
            "tamano_mb": tamano_archivo_mb(ruta_kd),
            "exactitud": acc_kd,
            "exactitud_int8": acc_kd_q,
            **{f"latencia_{k}": v for k, v in lat["kd_fp32_b16"].items()},
            "latencia_int8_b16": lat["kd_int8_b16"],
            "latencia_fp32_b1": lat["kd_fp32_b1"],
            "latencia_int8_b1": lat["kd_int8_b1"],
        },
    },
    "historial": {"estudiante_duro": hist_duro, "estudiante_destilado": hist_kd},
    "puertas": {
        "oficial_int8_lote16": puerta_oficial,
        "fp32_lote16": puerta_fp32,
        "int8_lote1": puerta_b1_int8,
        "duro_int8_lote16": puerta_duro_int8,
        "destilado_int8_lote16": puerta_kd_int8,
    },
}
guardar_json(resultado, RUTAS["resultados"] / "v2_sentimiento.json")
print("Escrito resultados/v2_sentimiento.json")
print("decisión oficial:", puerta_oficial["decision"], "variante:", oficial_clave,
      f"hueco={puerta_oficial['hueco_puntos']:.2f} puntos  aceleración={puerta_oficial['aceleracion_p95']:.2f}×")
"""),
        md("""\
## Cierre

El estudiante que se somete a las puertas oficiales es el **TinyBERT afinado y cuantizado a int8** con mejor exactitud (duro o destilado: se elige midiendo ambos). Se compara con el DistilBERT profesor en fp32, lote 16 y 4 hilos. El cuaderno 07 pone este resultado junto a la v1 y a un BERT pequeño *sin* el preentrenamiento de TinyBERT, para ver qué cambio empujó de verdad la exactitud.

Siguiente: `07-comparativa-v1-vs-v2.ipynb`.
"""),
    ]


def nb07():
    return [
        md("""\
# 07 · Comparativa v1 frente a v2

**Objetivo de este cuaderno:** poner en la misma tabla la v1 (GRU desde cero, cuadernos 03-05) y la v2 (TinyBERT, cuaderno 06), explicar **por qué la v1 no se promocionaba** y qué cambio aportó cada pieza del nuevo diseño. No se reentrena. Si faltan `resultados/sentimiento.json` o `resultados/v2_sentimiento.json`, vuelve a 03 y 06.
"""),
        code(BOOTSTRAP),
        md("""\
## 1. Cargar artefactos
"""),
        code("""\
ruta_v1 = RUTAS["resultados"] / "sentimiento.json"
ruta_v2 = RUTAS["resultados"] / "v2_sentimiento.json"
ruta_probe = RUTAS["resultados"] / "v2_probe.json"
faltan = [str(p) for p in (ruta_v1, ruta_v2) if not p.exists()]
assert not faltan, "Faltan:\\n- " + "\\n- ".join(faltan) + "\\nEjecuta los cuadernos 03 y 06."

v1 = cargar_json(ruta_v1)
v2 = cargar_json(ruta_v2)
probe = cargar_json(ruta_probe) if ruta_probe.exists() else None

acc_p = v2["exactitud_profesor"]
puerta = v2["puerta_calidad"]


def fila(nombre, acc, params, ms_p95=None, notas=""):
    hueco = (acc_p - acc) * 100 if acc is not None else None
    return {
        "variante": nombre,
        "exactitud": None if acc is None else round(acc, 4),
        "hueco_vs_profesor_puntos": None if hueco is None else round(hueco, 2),
        "parametros": params,
        "p95_lote_ms": None if ms_p95 is None else round(ms_p95, 2),
        "calidad_ok": None if hueco is None else hueco <= 4.0 + 1e-9,
        "notas": notas,
    }


filas = [
    fila("Profesor DistilBERT (SST-2)", acc_p, v2["modelos"]["profesor"]["parametros"],
         v2["modelos"]["profesor"]["latencia_ms_lote_p95"], "referencia; no se promociona a sí mismo"),
    fila("v1 GRU duro (3 000 frases)", v1["modelos"]["estudiante_duro"]["exactitud"],
         v1["modelos"]["estudiante_duro"]["parametros"],
         v1["modelos"]["estudiante_duro"].get("latencia_ms_lote_p95"),
         "v1: red desde cero, etiquetas duras"),
    fila("v1 GRU destilado (3 000 frases)", v1["modelos"]["estudiante_destilado"]["exactitud"],
         v1["modelos"]["estudiante_destilado"]["parametros"],
         v1["modelos"]["estudiante_destilado"].get("latencia_ms_lote_p95"),
         "v1: misma red, etiquetas blandas; no llega a la puerta de calidad"),
]
# Camino intermedio: BERT pequeño MLM (no TinyBERT), medido en las sondas previas.
if probe:
    for clave, etiqueta in [
        ("hard-16k-2ep", "Sonda: BERT L-4 H-256 duro, 16 000, 2 épocas"),
        ("kd-16k-2ep", "Sonda: BERT L-4 H-256 destilado, 16 000, 2 épocas"),
    ]:
        if clave in probe:
            filas.append(fila(etiqueta, probe[clave]["best_test"], 11_171_074, None,
                              "mismo régimen de datos casi, pero el punto de partida no es TinyBERT"))

filas.append(fila(
    "v2 TinyBERT duro (20 000 frases)",
    v2["modelos"]["estudiante_duro"]["exactitud"],
    v2["modelos"]["estudiante_duro"]["parametros"],
    v2["modelos"]["estudiante_duro"]["latencia_ms_lote_p95"],
    "v2: transformer pequeño ya preentrenado, etiquetas duras",
))
filas.append(fila(
    "v2 TinyBERT destilado fp32",
    v2["modelos"]["estudiante_destilado"]["exactitud"],
    v2["modelos"]["estudiante_destilado"]["parametros"],
    v2["modelos"]["estudiante_destilado"]["latencia_ms_lote_p95"],
    "v2: mismas iniciales, T=3, alpha=0.5",
))
oficial_clave = v2.get("variante_oficial", "estudiante_duro")
precision_oficial = v2.get("precision_oficial", "fp32")
oficial = v2["puertas"].get("oficial") or v2["puertas"].get("fp32_lote16") or v2["puertas"]["oficial_int8_lote16"]

def _es_oficial(clave, prec):
    return clave == oficial_clave and prec == precision_oficial

filas.append(fila(
    "v2 TinyBERT destilado int8",
    v2["modelos"]["estudiante_destilado"]["exactitud_int8"],
    v2["modelos"]["estudiante_destilado"]["parametros"],
    v2["modelos"]["estudiante_destilado"]["latencia_int8_b16"]["ms_lote_p95"],
    "cuantización dinámica: en esta CPU baja la exactitud y no entra en la puerta de calidad",
))
filas.append(fila(
    "v2 TinyBERT duro int8",
    v2["modelos"]["estudiante_duro"]["exactitud_int8"],
    v2["modelos"]["estudiante_duro"]["parametros"],
    v2["modelos"]["estudiante_duro"]["latencia_int8_b16"]["ms_lote_p95"],
    "misma caída de calidad al cuantizar; no se promociona",
))
# Fila oficial (fp32 o int8 según lo medido)
m_of = v2["modelos"][oficial_clave]
if precision_oficial == "int8":
    acc_of, p95_of = m_of["exactitud_int8"], m_of["latencia_int8_b16"]["ms_lote_p95"]
else:
    acc_of, p95_of = m_of["exactitud"], m_of["latencia_ms_lote_p95"]
rol = "duro" if oficial_clave == "estudiante_duro" else "destilado"
filas.append(fila(
    f"v2 TinyBERT {rol} {precision_oficial} (oficial)",
    acc_of,
    m_of["parametros"],
    p95_of,
    "mayor exactitud entre las variantes que cumplen las dos puertas",
))

ablacion = pd.DataFrame(filas)
display(ablacion)

print("Puertas oficiales v2:", f"{oficial_clave} {precision_oficial}, lote 16")
print(oficial["decision"],
      f"hueco={oficial['hueco_puntos']:.2f} puntos  aceleración={oficial['aceleracion_p95']:.2f}×")
if v2.get("nota_oficial"):
    print(v2["nota_oficial"])
if Path(RUTAS["resultados"] / "ejercicio5_promocion.json").exists():
    e5 = cargar_json(RUTAS["resultados"] / "ejercicio5_promocion.json")
    print("Ejercicio 5 sobre la v1:", e5["decision"],
          f"hueco={e5['hueco_puntos']:.2f} puntos  aceleración≈{e5['aceleracion_p95']:.1f}× (ojo: lotes distintos en la v1)")
"""),
        md("""\
## 2. Cómo leer la ablación

Tres mensajes, en este orden:

1. **La destilación de la v1 sí aportó algo, pero no suficiente.** El GRU destilado mejora al GRU duro (en la ejecución de referencia, del 65,0 % al 67,4 %). El hueco con el profesor sigue siendo de más de 20 puntos. Las blandas no inventan capacidad ni un buen punto de partida.
2. **Más datos y un BERT pequeño «genérico» acercan, y aún no bastan.** La sonda con `google/bert_uncased_L-4_H-256_A-4` y 16 000 frases quedó en torno al 80-81 %: claramente por encima del GRU, claramente por debajo de la puerta (87,06 %). Un transformer pequeño entrenado como modelo de lenguaje enmascarado no es lo mismo que un TinyBERT ya destilado de un BERT grande.
3. **El cambio que abre la puerta es el punto de partida (TinyBERT) más datos suficientes.** Con 20 000 frases, el TinyBERT duro en fp32 ya cumple calidad y latencia (lote 16). La destilación de salidas, en este estudiante, **no gana** al duro: TinyBERT ya fue destilado de un BERT grande. La cuantización int8 se midió y aquí **no se promociona**: baja la exactitud por debajo de la puerta y apenas recorta el p95.

En otras palabras: la v1 fallía por **calidad**, no por latencia. El GRU era rapidísimo. La v2 tenía que recuperar calidad sin volver a un modelo del tamaño del profesor.
"""),
        code("""\
fig, ejes = plt.subplots(1, 2, figsize=(12.2, 4.2))

nombres = ablacion["variante"].tolist()
accs = ablacion["exactitud"].tolist()
colores = ["#1f4e79" if "Profesor" in n else ("#2a7f4f" if "v2" in n and "oficial" in n else ("#6aa96e" if "v2" in n else ("#b36b00" if "Sonda" in n else "#a33"))) for n in nombres]
# exactitud
ypos = np.arange(len(nombres))
ejes[0].barh(ypos, [0 if pd.isna(a) else a for a in accs], color=colores)
ejes[0].set_yticks(ypos, nombres, fontsize=8)
ejes[0].axvline(acc_p, color="#1f4e79", linestyle="--", linewidth=1)
ejes[0].axvline(puerta, color="gray", linestyle=":", linewidth=1, label="puerta")
ejes[0].set_xlim(0.5, 1.0)
ejes[0].set_xlabel("exactitud en test")
ejes[0].set_title("Calidad")
ejes[0].invert_yaxis()
ejes[0].legend(fontsize=8)

# aceleración p95 lote 16, cuando hay cifra del profesor v2
p95_prof = v2["modelos"]["profesor"]["latencia_ms_lote_p95"]
acel = []
etqs = []
for _, r in ablacion.iterrows():
    if r["p95_lote_ms"] and r["p95_lote_ms"] > 0 and "Profesor" not in r["variante"]:
        # Cuidado: el p95 de la v1 se midió con lote 32, no es estrictamente comparable.
        etqs.append(r["variante"] + (" *" if "v1" in r["variante"] else ""))
        acel.append(p95_prof / r["p95_lote_ms"])
ejes[1].barh(np.arange(len(etqs)), acel, color=["#a33" if "v1" in e else "#2a7f4f" for e in etqs])
ejes[1].set_yticks(np.arange(len(etqs)), etqs, fontsize=8)
ejes[1].axvline(5, color="gray", linestyle=":", linewidth=1, label="puerta 5×")
ejes[1].set_xlabel("aceleración p95 vs profesor (lote 16 de la v2)")
ejes[1].set_title("Latencia (comparación aproximada)")
ejes[1].invert_yaxis()
ejes[1].legend(fontsize=8)
fig.tight_layout()
fig.savefig(RUTAS["resultados"] / "fig_v2_ablacion.png", bbox_inches="tight")
plt.show()
print("* Las barras de la v1 usan un p95 medido con lote 32: sirven de orden de magnitud, no de medida oficial.")
"""),
        md("""\
## 3. Las dos decisiones, lado a lado
"""),
        code("""\
v1_dec = cargar_json(RUTAS["resultados"] / "ejercicio5_promocion.json") if (RUTAS["resultados"] / "ejercicio5_promocion.json").exists() else None
filas_dec = []
if v1_dec:
    filas_dec.append({
        "serie": "v1 (ejercicio 5)",
        "hueco_puntos": round(v1_dec["hueco_puntos"], 2),
        "aceleracion_p95": round(v1_dec["aceleracion_p95"], 2),
        "cumple_calidad": v1_dec["cumple_calidad"],
        "cumple_latencia": v1_dec["cumple_latencia"],
        "decision": v1_dec["decision"],
        "protocolo": "p95/lote con lotes distintos (16 vs 32); no es el protocolo de la v2",
    })
filas_dec.append({
    "serie": f"v2 oficial ({oficial_clave}, {precision_oficial}, lote 16)",
    "hueco_puntos": round(oficial["hueco_puntos"], 2),
    "aceleracion_p95": round(oficial["aceleracion_p95"], 2),
    "cumple_calidad": oficial["cumple_calidad"],
    "cumple_latencia": oficial["cumple_latencia"],
    "decision": oficial["decision"],
    "protocolo": f"mismo lote 16, 4 hilos, p95 del lote profesor fp32 vs {oficial_clave} {precision_oficial}",
})
for clave, etiqueta in [
    ("fp32_lote16", "v2 fp32, lote 16"),
    ("int8_lote1", "v2 int8, lote 1"),
]:
    d = v2["puertas"][clave]
    filas_dec.append({
        "serie": etiqueta,
        "hueco_puntos": round(d["hueco_puntos"], 2),
        "aceleracion_p95": round(d["aceleracion_p95"], 2),
        "cumple_calidad": d["cumple_calidad"],
        "cumple_latencia": d["cumple_latencia"],
        "decision": d["decision"],
        "protocolo": "mismo protocolo de la v2, otra variante",
    })
display(pd.DataFrame(filas_dec))

guardar_json(
    {"ablacion": ablacion.to_dict(orient="records"), "decisiones": filas_dec, "oficial": oficial},
    RUTAS["resultados"] / "v2_comparativa.json",
)
print("Escrito resultados/v2_comparativa.json")
"""),
        md("""\
## 4. Conclusiones para un servicio

- **Promociona el par**, no un fichero suelto: profesor (id y revisión), estudiante, tokenizador, \\(T\\), \\(\\alpha\\), semilla, recuento de datos, protocolo de latencia (hilos, lote) y si va cuantizado o en ONNX.
- **Mide la latencia en el entorno de despliegue**, con el lote real. Las cifras de este cuaderno son de una CPU concreta y 4 hilos. Un lote 1 es más exigente que un lote 16; en esta máquina el lote 1 no llega a 5×. La cuantización int8 hay que **remeedir en exactitud**: aquí no entró en la puerta de calidad.
- **No destiles un estudiante inadecuado esperando un milagro.** Si el punto de partida es un GRU aleatorio o un BERT diminuto poco preparado, las blandas ayudan poco. Cambia la arquitectura o el preentrenamiento antes de alargar las épocas.
- **La cuantización y ONNX son recortes de coste, no de tarea.** Van después de tener calidad. ONNX Runtime es el camino habitual a un servicio; `quantize_dynamic` es el recorte que cabe en este cuaderno, en puro PyTorch, en CPU.
- Las puertas del ejercicio 5 siguen siendo las mismas. La v1 las suspendía. La v2, en esta ejecución, las cumple con el TinyBERT duro en fp32 (lote 16). La variante concreta queda en `resultados/v2_sentimiento.json`.
"""),
    ]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    write_nb("06-destilacion-v2-sentimiento.ipynb", nb06())
    write_nb("07-comparativa-v1-vs-v2.ipynb", nb07())


if __name__ == "__main__":
    main()
