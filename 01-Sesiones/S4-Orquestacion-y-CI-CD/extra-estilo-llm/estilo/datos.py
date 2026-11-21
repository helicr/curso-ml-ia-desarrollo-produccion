"""Carpetas, fotos y utilidades de los notebooks.

Nada de rutas fijas: la carpeta de trabajo sale de la variable de entorno
``ESTILO_TRABAJO`` (por defecto ``_trabajo`` en la carpeta actual) y la caché
de Hugging Face de ``HF_HOME`` (por defecto ``<trabajo>/hf``).
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import tarfile
import tempfile
import time
import urllib.request
import warnings
from pathlib import Path

from PIL import Image

warnings.filterwarnings("ignore", message="IProgress not found")
os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")


def carpeta_trabajo(valor: str | None = None) -> Path:
    """Carpeta donde cada notebook lee su entrada y deja su salida (se crea si no existe)."""
    ruta = Path(valor or os.environ.get("ESTILO_TRABAJO") or "_trabajo").resolve()
    ruta.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HOME", str(ruta / "hf"))
    # Pesos de torchvision junto a la caché de Hugging Face (fuera de los artefactos).
    os.environ.setdefault("TORCH_HOME", str(Path(os.environ["HF_HOME"]) / "torch"))
    return ruta


def limitar_hilos(n: int | None = None) -> int:
    """Fija los hilos de PyTorch (variable ESTILO_HILOS o todos los núcleos)."""
    import torch

    n = int(n or os.environ.get("ESTILO_HILOS") or os.cpu_count() or 1)
    torch.set_num_threads(n)
    return n


def mostrar_ruta(ruta: Path, base: Path) -> str:
    """Ruta relativa a la carpeta de trabajo, para no imprimir rutas personales."""
    try:
        return "<trabajo>/" + Path(ruta).resolve().relative_to(Path(base).resolve()).as_posix()
    except ValueError:
        return Path(ruta).name


# ---------------------------------------------------------------------------
# Fotos de Oxford-IIIT Pet (CC BY-SA 4.0, Parkhi et al., CVPR 2012)
# ---------------------------------------------------------------------------
URL_PETS = "https://thor.robots.ox.ac.uk/~vgg/data/pets/data/images.tar.gz"


def _recorte_cuadrado(img: Image.Image, lado: int) -> Image.Image:
    w, h = img.size
    m = min(w, h)
    img = img.crop(((w - m) // 2, (h - m) // 2, (w - m) // 2 + m, (h - m) // 2 + m))
    return img.resize((lado, lado), Image.BICUBIC)


def preparar_fotos(trabajo: Path, n_fotos: int, resolucion: int, tar: str | None = None) -> list[Path]:
    """Extrae ``n_fotos`` fotos (mitad gatos, mitad perros) a ``trabajo/fotos_<res>``.

    Lee el images.tar.gz original (variable ESTILO_TAR) o, si no está, lo
    descarga de la web oficial. La elección es determinista (hash del nombre).
    En Oxford-IIIT Pet las razas de gato empiezan por mayúscula.
    """
    destino = trabajo / f"fotos_{resolucion}"
    destino.mkdir(parents=True, exist_ok=True)

    def _equilibradas():
        # Mitad de cada clase aunque la carpeta tenga más fotos de las pedidas
        # (sin esto, el orden alfabético devolvería solo «gato_*»).
        por_clase = n_fotos // 2
        gatos = sorted(destino.glob("gato_*.png"))[:por_clase]
        perros = sorted(destino.glob("perro_*.png"))[:n_fotos - len(gatos)]
        return sorted(gatos + perros)

    hechas = _equilibradas()
    if len(hechas) >= n_fotos:
        return hechas
    tar = tar or os.environ.get("ESTILO_TAR")
    if not tar or not Path(tar).exists():
        # Fuera de la carpeta de trabajo, para que los ~800 MB no viajen en los artefactos.
        tar = str(Path(tempfile.gettempdir()) / "oxford_pets_images.tar.gz")
        if not Path(tar).exists():
            print("Descargando Oxford-IIIT Pet (~800 MB)...")
            t0 = time.perf_counter()
            # Con el agente por defecto de Python, la web de Oxford devolvió un error HTTP en GitHub Actions
            # (21/11/2026); con un agente de navegador y siguiendo redirecciones, como hace curl, se descarga.
            peticion = urllib.request.Request(URL_PETS, headers={"User-Agent": "Mozilla/5.0 (curso-ml-ia)"})
            with urllib.request.urlopen(peticion) as r, open(tar, "wb") as f:
                while bloque := r.read(1 << 20):
                    f.write(bloque)
            print(f"Descarga: {time.perf_counter() - t0:.0f} s")
    elegidas = {"gato": [], "perro": []}
    prob = min(1.0, 1.6 * n_fotos / 7390)  # ~7390 fotos en el archivo
    with tarfile.open(tar, "r|gz") as t:
        for m in t:
            nombre = Path(m.name).name
            if not (m.isfile() and nombre.endswith(".jpg")):
                continue
            h = int(hashlib.md5(nombre.encode()).hexdigest(), 16)
            if (h % 10000) / 10000 >= prob:
                continue
            try:
                img = Image.open(io.BytesIO(t.extractfile(m).read()))
                if img.mode != "RGB":  # descartamos grises, CMYK y RGBA raras
                    continue
                img.load()
            except Exception:
                continue
            clase = "gato" if nombre[0].isupper() else "perro"
            elegidas[clase].append((h, nombre, _recorte_cuadrado(img, resolucion)))
    por_clase = n_fotos // 2
    for clase, lista in elegidas.items():
        for _, nombre, img in sorted(lista)[:por_clase]:
            img.save(destino / f"{clase}_{Path(nombre).stem}.png")
    return _equilibradas()


# ---------------------------------------------------------------------------
# Parejas (original, editada, ajustes) guardadas en trabajo/parejas/parejas.jsonl
# ---------------------------------------------------------------------------
def leer_parejas(trabajo: Path, parte: str | None = None) -> list[dict]:
    """Filas de ``parejas.jsonl`` (id, parte, original, editada, ajustes), filtradas por parte si se indica."""
    texto = (Path(trabajo) / "parejas" / "parejas.jsonl").read_text(encoding="utf-8")
    filas = [json.loads(linea) for linea in texto.splitlines() if linea]
    return [f for f in filas if parte is None or f["parte"] == parte]


def abrir(trabajo: Path, relativa: str) -> Image.Image:
    """Abre una imagen de ``trabajo/parejas/`` por su ruta relativa."""
    return Image.open(Path(trabajo) / "parejas" / relativa).convert("RGB")


def parejas_transferencia(test: list[dict]) -> list[tuple[dict, dict]]:
    """Cada foto editada de test hace de referencia; el contenido es la foto original siguiente."""
    return [(test[i], test[(i + 1) % len(test)]) for i in range(len(test))]


# ---------------------------------------------------------------------------
# Utilidades de medida y registro
# ---------------------------------------------------------------------------
def guardar_figura(ruta, dpi: int = 55) -> None:
    """Guarda la figura actual de matplotlib como PNG ligero (paleta de 256 colores)."""
    import matplotlib.pyplot as plt

    buf = io.BytesIO()
    plt.savefig(buf, dpi=dpi, format="png")
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    Image.open(buf).convert("RGB").quantize(256).save(ruta, optimize=True)


class Cronometro:
    """``with Cronometro() as c: ...`` y después ``c.s`` son los segundos transcurridos."""

    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, *a):
        self.s = time.perf_counter() - self.t0


def memoria_mb() -> float:
    """Memoria residente máxima del proceso (pico) en MB, si psutil lo permite."""
    try:
        import psutil

        info = psutil.Process().memory_info()
        return round(getattr(info, "peak_wset", info.rss) / 2**20, 1)
    except Exception:
        return float("nan")


def tamano_mb(ruta: Path) -> float:
    """Tamaño en MB de un archivo o de todos los archivos de una carpeta."""
    ruta = Path(ruta)
    archivos = [ruta] if ruta.is_file() else [f for f in ruta.rglob("*") if f.is_file()]
    return round(sum(f.stat().st_size for f in archivos) / 2**20, 2)


def mlflow_local(trabajo: Path):
    """MLflow en una base temporal dentro de la carpeta de trabajo (nunca la del proyecto)."""
    import mlflow

    uri = os.environ.get("ESTILO_MLFLOW") or ("sqlite:///" + (Path(trabajo) / "mlflow.db").as_posix())
    mlflow.set_tracking_uri(uri)
    nombre = "pico-llm-estilo"
    if mlflow.get_experiment_by_name(nombre) is None:
        # Los artefactos también dentro de la carpeta de trabajo, no en el repo.
        mlflow.create_experiment(nombre, artifact_location=(Path(trabajo) / "mlartifacts").resolve().as_uri())
    mlflow.set_experiment(nombre)
    return mlflow
