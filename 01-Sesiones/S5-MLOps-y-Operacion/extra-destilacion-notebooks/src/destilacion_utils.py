"""Utilidades compartidas de los cuadernos de destilación de conocimiento.

Este módulo centraliza lo que se reutiliza entre cuadernos: localización de la
raíz del proyecto, comprobación del entorno, configuración de proxy y Hugging
Face, softmax con temperatura, la pérdida de destilación, modelos pequeños,
evaluación y persistencia de artefactos en modelos/ y resultados/.
"""

from __future__ import annotations

import json
import os
import random
import time
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

import numpy as np

SEMILLA_DEFECTO = 42
NOMBRE_UTILS = "destilacion_utils.py"


# ---------------------------------------------------------------------------
# Rutas, semilla y dispositivo
# ---------------------------------------------------------------------------

def encontrar_raiz(partida: Optional[Path] = None) -> Path:
    """Devuelve la raíz del proyecto (la carpeta que contiene src/ y notebooks/)."""
    partida = Path(partida or Path.cwd()).resolve()
    candidatos = [partida, *partida.parents]
    # También probar hermanos habituales si se ejecuta desde un subdirectorio.
    for cand in candidatos:
        if (cand / "src" / NOMBRE_UTILS).exists() and (cand / "notebooks").is_dir():
            return cand
    raise FileNotFoundError(
        "No encuentro la raíz del proyecto de destilación "
        f"(buscaba src/{NOMBRE_UTILS} y notebooks/). "
        "Abre el cuaderno desde extra-destilacion-notebooks/ o extra-destilacion-notebooks/notebooks/."
    )


def preparar_rutas(raiz: Optional[Path] = None) -> dict[str, Path]:
    """Crea las carpetas de trabajo y devuelve un diccionario de rutas."""
    raiz = encontrar_raiz(raiz) if raiz is None or not (Path(raiz) / "src" / NOMBRE_UTILS).exists() else Path(raiz).resolve()
    rutas = {
        "raiz": raiz,
        "src": raiz / "src",
        "notebooks": raiz / "notebooks",
        "modelos": raiz / "modelos",
        "resultados": raiz / "resultados",
        "datos": raiz / "datos",
        "cache_hf": raiz / "cache-hf",
    }
    for clave in ("modelos", "resultados", "datos", "cache_hf"):
        rutas[clave].mkdir(parents=True, exist_ok=True)
    return rutas


def fijar_semilla(semilla: int = SEMILLA_DEFECTO) -> int:
    """Fija semillas de Python, NumPy y PyTorch para que los resultados se puedan repetir."""
    os.environ["PYTHONHASHSEED"] = str(semilla)
    random.seed(semilla)
    np.random.seed(semilla)
    try:
        import torch

        torch.manual_seed(semilla)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(semilla)
        # Determinismo razonable en CPU. No forzamos benchmark/cudnn aquí.
        torch.use_deterministic_algorithms(False)
    except ImportError:
        pass
    return semilla


def dispositivo() -> "torch.device":
    """Elige CUDA si hay GPU usable; si no, CPU. El curso se puede completar en CPU."""
    import torch

    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


# ---------------------------------------------------------------------------
# Proxy corporativo y Hugging Face
# ---------------------------------------------------------------------------

_VARS_PROXY = ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "NO_PROXY", "no_proxy")
_VARS_SSL = ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE")
_VARS_HF = (
    "HF_HOME",
    "HF_HUB_CACHE",
    "HF_DATASETS_CACHE",
    "HF_TOKEN",
    "HUGGING_FACE_HUB_TOKEN",
    "HF_HUB_OFFLINE",
    "TRANSFORMERS_OFFLINE",
    "HF_HUB_DISABLE_TELEMETRY",
    "HF_ENDPOINT",
)


def _presente_no_vacio(nombre: str) -> bool:
    valor = os.environ.get(nombre)
    return bool(valor) and valor.strip() != ""


def configurar_proxy_y_hf(
    raiz: Optional[Path] = None,
    *,
    verbose: bool = True,
) -> dict[str, Any]:
    """Prepara un entorno razonable detrás de un proxy corporativo y para Hugging Face.

    No inventa credenciales ni las imprime. Si ya existen HTTP(S)_PROXY, certificados
    o HF_TOKEN en el entorno, solo informa de que están definidos. Si HF_HOME no está
    definido, lo apunta a cache-hf/ dentro del proyecto (así el caché no se mezcla
    con el del usuario y sobrevive mejor entre sesiones).
    """
    rutas = preparar_rutas(raiz)
    cambios: list[str] = []

    if not _presente_no_vacio("HF_HOME"):
        os.environ["HF_HOME"] = str(rutas["cache_hf"])
        cambios.append(f"HF_HOME={rutas['cache_hf']}")
    if not _presente_no_vacio("HF_HUB_DISABLE_TELEMETRY"):
        os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
        cambios.append("HF_HUB_DISABLE_TELEMETRY=1")
    if not _presente_no_vacio("TOKENIZERS_PARALLELISM"):
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        cambios.append("TOKENIZERS_PARALLELISM=false")

    # Si hay un certificado corporativo habitual, avisar (no lo adivinamos).
    informe = {
        "proxy_http": _presente_no_vacio("HTTP_PROXY") or _presente_no_vacio("http_proxy"),
        "proxy_https": _presente_no_vacio("HTTPS_PROXY") or _presente_no_vacio("https_proxy"),
        "no_proxy": _presente_no_vacio("NO_PROXY") or _presente_no_vacio("no_proxy"),
        "certificado_ssl": any(_presente_no_vacio(v) for v in _VARS_SSL),
        "token_hf": _presente_no_vacio("HF_TOKEN") or _presente_no_vacio("HUGGING_FACE_HUB_TOKEN"),
        "hf_home": os.environ.get("HF_HOME"),
        "hf_offline": os.environ.get("HF_HUB_OFFLINE") == "1" or os.environ.get("TRANSFORMERS_OFFLINE") == "1",
        "cambios": cambios,
    }
    if verbose:
        print("Configuración de red y Hugging Face")
        print(f"  HTTP_PROXY definido:  {informe['proxy_http']}")
        print(f"  HTTPS_PROXY definido: {informe['proxy_https']}")
        print(f"  NO_PROXY definido:    {informe['no_proxy']}")
        print(f"  Certificado SSL (SSL_CERT_FILE / REQUESTS_CA_BUNDLE): {informe['certificado_ssl']}")
        print(f"  Token de Hugging Face presente: {informe['token_hf']} (no se muestra el valor)")
        print(f"  HF_HOME: {informe['hf_home']}")
        print(f"  Modo offline HF: {informe['hf_offline']}")
        if cambios:
            print("  Ajustes aplicados en esta sesión:")
            for c in cambios:
                print(f"    - {c}")
        else:
            print("  No hizo falta ajustar variables: ya estaban definidas.")
    return informe


def texto_ayuda_proxy() -> str:
    return (
        "Si estás detrás de un proxy corporativo, define las variables antes de\n"
        "abrir Jupyter o al principio del cuaderno 00, por ejemplo:\n\n"
        '  os.environ["HTTP_PROXY"]  = "http://usuario:contraseña@proxy.empresa:8080"\n'
        '  os.environ["HTTPS_PROXY"] = os.environ["HTTP_PROXY"]\n'
        '  os.environ["NO_PROXY"]    = "localhost,127.0.0.1,.empresa.com"\n\n'
        "Si el proxy inspecciona HTTPS, apunta al certificado corporativo:\n\n"
        '  os.environ["SSL_CERT_FILE"]      = "/ruta/al/certificado-corporativo.pem"\n'
        '  os.environ["REQUESTS_CA_BUNDLE"] = os.environ["SSL_CERT_FILE"]\n\n'
        "Hugging Face:\n"
        '  os.environ["HF_TOKEN"] = "..."          # o: huggingface-cli login\n'
        '  os.environ["HF_HUB_OFFLINE"] = "1"      # si el modelo ya está en cache-hf/\n'
    )


def comprobar_entorno() -> "pd.DataFrame":
    """Tabla de versiones y disponibilidad de paquetes necesarios."""
    import platform
    import importlib

    import pandas as pd

    filas = []

    def _add(nombre, ok, detalle="", obligatorio=False):
        filas.append(
            {
                "componente": nombre,
                "disponible": ok,
                "obligatorio": obligatorio,
                "detalle": detalle,
            }
        )

    _add("Python", True, platform.python_version() + " · " + platform.platform(), obligatorio=True)

    for paquete, atributo in [
        ("numpy", "__version__"),
        ("pandas", "__version__"),
        ("matplotlib", "__version__"),
        ("sklearn", "__version__"),
        ("tqdm", "__version__"),
        ("torch", "__version__"),
        ("torchvision", "__version__"),
        ("transformers", "__version__"),
        ("datasets", "__version__"),
        ("accelerate", "__version__"),
    ]:
        try:
            mod = importlib.import_module(paquete)
            ver = getattr(mod, atributo, "?")
            extra = ""
            if paquete == "torch":
                cuda = bool(getattr(mod, "cuda") and mod.cuda.is_available())
                extra = f" · dispositivo: {'cuda' if cuda else 'cpu'}"
                if cuda:
                    extra += f" ({mod.cuda.get_device_name(0)})"
            _add(paquete, True, str(ver) + extra, obligatorio=True)
        except Exception as exc:  # noqa: BLE001
            _add(paquete, False, f"no importable: {exc}", obligatorio=True)

    try:
        import torch

        _add("CUDA compilado en torch", bool(torch.backends.cuda.is_built()), torch.version.cuda or "cpu-only")
    except Exception:
        pass

    informe = configurar_proxy_y_hf(verbose=False)
    _add("Proxy HTTP(S)", informe["proxy_http"] or informe["proxy_https"], "definido" if (informe["proxy_http"] or informe["proxy_https"]) else "no definido (salida directa)")
    _add("Token Hugging Face", informe["token_hf"], "presente" if informe["token_hf"] else "no presente (los modelos públicos no lo necesitan)")
    _add("HF_HOME", True, str(informe["hf_home"]))
    return pd.DataFrame(filas)


def probar_conexion_hf(timeout: float = 8.0) -> dict[str, Any]:
    """Comprueba si se puede alcanzar el Hub de Hugging Face. No descarga modelos."""
    import urllib.request
    import urllib.error
    import ssl

    url = os.environ.get("HF_ENDPOINT", "https://huggingface.co")
    resultado: dict[str, Any] = {"url": url, "ok": False, "estado": None, "error": None}
    try:
        ctx = ssl.create_default_context()
        cert = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
        if cert and Path(cert).exists():
            ctx = ssl.create_default_context(cafile=cert)
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "destilacion-cuadernos/1.0"})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            resultado["ok"] = 200 <= getattr(resp, "status", 200) < 400
            resultado["estado"] = getattr(resp, "status", None)
    except Exception as exc:  # noqa: BLE001
        resultado["error"] = f"{type(exc).__name__}: {exc}"
    return resultado


# ---------------------------------------------------------------------------
# Softmax, temperatura y pérdida de destilación
# ---------------------------------------------------------------------------

def softmax_temperatura(logits: np.ndarray, temperature: float = 1.0, eje: int = -1) -> np.ndarray:
    """Softmax numéricamente estable: softmax(z / T).

    T = 1 es el softmax habitual. T > 1 suaviza la distribución (más masa en
    las clases no ganadoras: el «conocimiento oscuro» del profesor). T → 0
    se acerca a un vector one-hot.
    """
    if temperature <= 0:
        raise ValueError("La temperatura debe ser un número positivo.")
    z = np.asarray(logits, dtype=np.float64) / float(temperature)
    z = z - np.max(z, axis=eje, keepdims=True)
    exp = np.exp(z)
    return exp / np.sum(exp, axis=eje, keepdims=True)


def divergencia_kl(p: np.ndarray, q: np.ndarray, eje: int = -1, eps: float = 1e-12) -> np.ndarray:
    """KL(p || q) = sum p log(p/q), reducida en el eje de las clases."""
    p = np.clip(np.asarray(p, dtype=np.float64), eps, 1.0)
    q = np.clip(np.asarray(q, dtype=np.float64), eps, 1.0)
    p = p / p.sum(axis=eje, keepdims=True)
    q = q / q.sum(axis=eje, keepdims=True)
    return np.sum(p * (np.log(p) - np.log(q)), axis=eje)


def perdida_destilacion(
    logits_estudiante: "torch.Tensor",
    logits_profesor: "torch.Tensor",
    etiquetas: Optional["torch.Tensor"] = None,
    temperature: float = 3.0,
    alpha: float = 0.7,
) -> "torch.Tensor":
    """Pérdida clásica de destilación (Hinton et al., 2015).

    L = alpha * T^2 * KL( softmax(z_p / T) || softmax(z_e / T) )
      + (1 - alpha) * CE(z_e, y)

    El factor T^2 compensa que el gradiente de la KL se encoge como 1/T^2
    al suavizar las distribuciones. alpha = 1 usa solo las etiquetas blandas
    del profesor; alpha = 0 es entrenamiento supervisado habitual.
    """
    import torch
    import torch.nn.functional as F

    if temperature <= 0:
        raise ValueError("La temperatura debe ser un número positivo.")
    if not 0.0 <= alpha <= 1.0:
        raise ValueError("alpha debe estar en [0, 1].")

    log_p_est = F.log_softmax(logits_estudiante / temperature, dim=-1)
    p_prof = F.softmax(logits_profesor / temperature, dim=-1)
    kl = F.kl_div(log_p_est, p_prof, reduction="batchmean") * (temperature ** 2)

    if alpha >= 1.0 or etiquetas is None:
        return kl

    ce = F.cross_entropy(logits_estudiante, etiquetas)
    return alpha * kl + (1.0 - alpha) * ce


# ---------------------------------------------------------------------------
# Modelos y métricas
# ---------------------------------------------------------------------------

def contar_parametros(modelo: "torch.nn.Module", solo_entrenables: bool = False) -> int:
    params = modelo.parameters() if not solo_entrenables else (p for p in modelo.parameters() if p.requires_grad)
    return int(sum(p.numel() for p in params))


def tamano_archivo_mb(ruta: Path) -> float:
    ruta = Path(ruta)
    if not ruta.exists():
        return float("nan")
    return ruta.stat().st_size / (1024 * 1024)


def guardar_json(obj: Any, ruta: Path) -> Path:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    def _default(o):
        if isinstance(o, Path):
            return str(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        raise TypeError(f"No se puede serializar {type(o)}")

    ruta.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=_default), encoding="utf-8")
    return ruta


def cargar_json(ruta: Path) -> Any:
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


def guardar_checkpoint(modelo: "torch.nn.Module", ruta: Path, metadatos: Optional[dict] = None) -> Path:
    import torch

    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    payload = {"state_dict": modelo.state_dict(), "metadatos": metadatos or {}}
    torch.save(payload, ruta)
    return ruta


def cargar_checkpoint(modelo: "torch.nn.Module", ruta: Path, map_location=None) -> dict:
    import torch

    payload = torch.load(Path(ruta), map_location=map_location or "cpu", weights_only=False)
    modelo.load_state_dict(payload["state_dict"])
    return payload.get("metadatos", {})


class MLP(torch.nn.Module if False else object):
    """Definida de forma perezosa para poder importar este módulo sin torch.

    En la práctica se crea con construir_mlp().
    """


def construir_mlp(anchos: Iterable[int], dropout: float = 0.2) -> "torch.nn.Module":
    """MLP genérico: Linear-ReLU-Dropout en capas ocultas y Linear al final.

    Ejemplo: construir_mlp([784, 256, 128, 10]) para MNIST.
    """
    import torch
    from torch import nn

    anchos = list(anchos)
    if len(anchos) < 2:
        raise ValueError("Haz falta al menos dimensión de entrada y de salida.")

    capas: list[nn.Module] = []
    for i, (a, b) in enumerate(zip(anchos[:-1], anchos[1:])):
        es_ultima = i == len(anchos) - 2
        capas.append(nn.Linear(a, b))
        if not es_ultima:
            capas.append(nn.ReLU())
            if dropout and dropout > 0:
                capas.append(nn.Dropout(dropout))
    modelo = nn.Sequential(*capas)
    modelo.anchos = anchos  # type: ignore[attr-defined]
    return modelo


class EstudianteTinySentiment:
    """Marcador de posición: la clase real se define en construir_estudiante_sentimiento."""


def construir_estudiante_sentimiento(
    vocab_size: int,
    n_clases: int = 2,
    dim_emb: int = 64,
    dim_oculta: int = 64,
    n_capas: int = 1,
    pad_id: int = 0,
    dropout: float = 0.2,
) -> "torch.nn.Module":
    """Estudiante muy pequeño para sentimiento: embedding + GRU bidireccional + lineal.

    No es un transformer. Cabe en CPU y entrena en minutos (o menos) sobre unos
    pocos miles de frases. El profesor de Hugging Face aporta las etiquetas blandas.
    """
    import torch
    from torch import nn

    class _Estudiante(nn.Module):
        def __init__(self):
            super().__init__()
            self.pad_id = pad_id
            self.emb = nn.Embedding(vocab_size, dim_emb, padding_idx=pad_id)
            self.gru = nn.GRU(
                dim_emb,
                dim_oculta,
                num_layers=n_capas,
                batch_first=True,
                bidirectional=True,
                dropout=dropout if n_capas > 1 else 0.0,
            )
            self.dropout = nn.Dropout(dropout)
            self.fc = nn.Linear(dim_oculta * 2, n_clases)
            self.config = {
                "vocab_size": vocab_size,
                "n_clases": n_clases,
                "dim_emb": dim_emb,
                "dim_oculta": dim_oculta,
                "n_capas": n_capas,
                "pad_id": pad_id,
                "dropout": dropout,
                "arquitectura": "embedding-gru-bidireccional",
            }

        def forward(self, input_ids, attention_mask=None):
            x = self.emb(input_ids)
            if attention_mask is None:
                attention_mask = (input_ids != self.pad_id).long()
            longitudes = attention_mask.sum(dim=1).clamp(min=1)
            empaquetado = nn.utils.rnn.pack_padded_sequence(
                x, longitudes.cpu(), batch_first=True, enforce_sorted=False
            )
            _, h = self.gru(empaquetado)
            # h: (num_capas * 2, batch, hidden) → última capa, concat direcciones
            h_last = torch.cat((h[-2], h[-1]), dim=-1)
            return self.fc(self.dropout(h_last))

    return _Estudiante()


@torch.no_grad() if False else (lambda f: f)
def exactitud_loader(modelo, loader, device, logits_extra=None) -> float:
    """Exactitud media de un DataLoader de (x, y) o de un dict estilo Hugging Face."""
    import torch

    modelo.eval()
    aciertos = 0
    total = 0
    for lote in loader:
        if isinstance(lote, dict):
            y = lote["labels" if "labels" in lote else "y"].to(device)
            if "input_ids" in lote:
                mask = lote.get("attention_mask")
                logits = modelo(
                    lote["input_ids"].to(device),
                    attention_mask=None if mask is None else mask.to(device),
                )
            else:
                logits = modelo(lote["x"].to(device))
        else:
            x, y = lote[0].to(device), lote[1].to(device)
            logits = modelo(x)
        pred = logits.argmax(dim=-1)
        aciertos += int((pred == y).sum().item())
        total += int(y.size(0))
    return aciertos / max(total, 1)


def evaluar_loader(modelo, loader, device) -> dict[str, float]:
    """Exactitud y pérdida de entropía cruzada media."""
    import torch
    import torch.nn.functional as F

    modelo.eval()
    aciertos = 0
    total = 0
    perdida = 0.0
    with torch.no_grad():
        for lote in loader:
            if isinstance(lote, dict):
                y = lote["labels" if "labels" in lote else "y"].to(device)
                if "input_ids" in lote:
                    mask = lote.get("attention_mask")
                    logits = modelo(
                        lote["input_ids"].to(device),
                        attention_mask=None if mask is None else mask.to(device),
                    )
                else:
                    logits = modelo(lote["x"].to(device))
            else:
                x, y = lote[0].to(device), lote[1].to(device)
                logits = modelo(x)
            perdida += float(F.cross_entropy(logits, y, reduction="sum").item())
            aciertos += int((logits.argmax(dim=-1) == y).sum().item())
            total += int(y.size(0))
    return {
        "exactitud": aciertos / max(total, 1),
        "perdida_ce": perdida / max(total, 1),
        "n": total,
    }


def medir_latencia_ms(
    modelo,
    lote_ejemplo,
    device=None,
    n_calentamiento: int = 8,
    n_reps: int = 40,
) -> dict[str, float]:
    """Latencia de inferencia en milisegundos (una pasada hacia delante, modo eval)."""
    import torch

    modelo.eval()
    if device is None:
        device = next(modelo.parameters()).device

    def _paso():
        with torch.no_grad():
            if isinstance(lote_ejemplo, dict):
                mask = lote_ejemplo.get("attention_mask")
                return modelo(
                    lote_ejemplo["input_ids"].to(device),
                    attention_mask=None if mask is None else mask.to(device),
                )
            x = lote_ejemplo.to(device)
            return modelo(x)

    for _ in range(n_calentamiento):
        _paso()
    if device.type == "cuda":
        torch.cuda.synchronize()

    tiempos = []
    for _ in range(n_reps):
        t0 = time.perf_counter()
        _paso()
        if device.type == "cuda":
            torch.cuda.synchronize()
        tiempos.append((time.perf_counter() - t0) * 1000.0)

    arr = np.asarray(tiempos, dtype=np.float64)
    n_muestras = int(lote_ejemplo["input_ids"].shape[0]) if isinstance(lote_ejemplo, dict) else int(lote_ejemplo.shape[0])
    return {
        "ms_lote_media": float(arr.mean()),
        "ms_lote_p50": float(np.percentile(arr, 50)),
        "ms_lote_p95": float(np.percentile(arr, 95)),
        "ms_por_ejemplo_media": float(arr.mean() / max(n_muestras, 1)),
        "n_reps": n_reps,
        "tamano_lote": n_muestras,
    }


def entrenar_epoca(
    modelo,
    loader,
    optimizer,
    device,
    *,
    profesor=None,
    logits_profesor: Optional["torch.Tensor"] = None,
    temperature: float = 3.0,
    alpha: float = 0.7,
    indices_en_lote: bool = False,
) -> dict[str, float]:
    """Una época de entrenamiento, con o sin destilación.

    Tres modos:
    - Sin profesor ni logits_profesor: entropía cruzada con etiquetas duras.
    - Con profesor (módulo en eval): el profesor genera logits por lote.
    - Con logits_profesor (tensor [N, C] alineado al índice del dataset):
      el DataLoader debe devolver también el índice (indices_en_lote=True)
      o el lote debe ser (x, y, idx).
    """
    import torch

    modelo.train()
    if profesor is not None:
        profesor.eval()

    suma_perdida = 0.0
    aciertos = 0
    total = 0

    for lote in loader:
        idx = None
        if isinstance(lote, dict):
            y = lote["labels" if "labels" in lote else "y"].to(device)
            if "input_ids" in lote:
                mask = lote.get("attention_mask")
                x_kwargs = {
                    "input_ids": lote["input_ids"].to(device),
                    "attention_mask": None if mask is None else mask.to(device),
                }
                logits_e = modelo(**x_kwargs)
            else:
                x_kwargs = None
                logits_e = modelo(lote["x"].to(device))
            if "idx" in lote:
                idx = lote["idx"]
        else:
            if len(lote) == 3:
                x, y, idx = lote
                y = y.to(device)
                logits_e = modelo(x.to(device))
                x_kwargs = None
            else:
                x, y = lote[0], lote[1]
                y = y.to(device)
                logits_e = modelo(x.to(device))
                x_kwargs = None

        if profesor is not None:
            with torch.no_grad():
                if x_kwargs is not None:
                    logits_p = profesor(**x_kwargs)
                    # El profesor de HF suele devolver un objeto con .logits
                    if hasattr(logits_p, "logits"):
                        logits_p = logits_p.logits
                else:
                    logits_p = profesor(x.to(device))
                    if hasattr(logits_p, "logits"):
                        logits_p = logits_p.logits
            perdida = perdida_destilacion(logits_e, logits_p, y, temperature=temperature, alpha=alpha)
        elif logits_profesor is not None:
            if idx is None:
                raise ValueError("Hacen falta índices del lote para alinear logits_profesor.")
            logits_p = logits_profesor[idx].to(device)
            perdida = perdida_destilacion(logits_e, logits_p, y, temperature=temperature, alpha=alpha)
        else:
            import torch.nn.functional as F

            perdida = F.cross_entropy(logits_e, y)

        optimizer.zero_grad(set_to_none=True)
        perdida.backward()
        optimizer.step()

        suma_perdida += float(perdida.item()) * int(y.size(0))
        aciertos += int((logits_e.argmax(dim=-1) == y).sum().item())
        total += int(y.size(0))

    return {
        "perdida": suma_perdida / max(total, 1),
        "exactitud": aciertos / max(total, 1),
        "n": total,
    }


def historial_a_dict(historial: list[dict]) -> dict:
    """Convierte una lista de registros por época en columnas."""
    if not historial:
        return {}
    claves = sorted({k for fila in historial for k in fila})
    return {k: [fila.get(k) for fila in historial] for k in claves}



# ---------------------------------------------------------------------------
# v2: hilos CPU, latencia justa de transformers, cuantización y puertas
# ---------------------------------------------------------------------------

def fijar_hilos_cpu(n_hilos: int = 4) -> dict[str, int]:
    """Fija el número de hilos de PyTorch para medir latencia de forma comparable.

    Hay que llamarlo antes de medir al profesor y al estudiante, con el mismo
    valor. En un portátil, 4 es un compromiso razonable. `set_num_interop_threads`
    solo se puede fijar una vez por proceso: si ya estaba fijado, se ignora.
    """
    import torch

    n_hilos = int(max(1, n_hilos))
    torch.set_num_threads(n_hilos)
    interop = None
    try:
        torch.set_num_interop_threads(1)
        interop = 1
    except RuntimeError:
        try:
            interop = torch.get_num_interop_threads()
        except Exception:
            interop = None
    return {
        "intra_op": int(torch.get_num_threads()),
        "interop": -1 if interop is None else int(interop),
    }


def medir_latencia_transformador(
    modelo,
    input_ids,
    attention_mask=None,
    *,
    n_calentamiento: int = 10,
    n_reps: int = 40,
) -> dict[str, float]:
    """Latencia de un lote ya tokenizado, en milisegundos (modelo en eval, sin gradientes).

    El mismo lote, el mismo número de repeticiones y los mismos hilos se deben
    usar para el profesor y el estudiante. Se reportan p50 y p95 del *lote*
    y el equivalente por ejemplo (p95_lote / batch), que es una cota, no una
    medida request a request.
    """
    import time
    import numpy as np
    import torch

    modelo.eval()
    if attention_mask is None:
        attention_mask = torch.ones_like(input_ids)
    n_muestras = int(input_ids.shape[0])
    with torch.no_grad():
        for _ in range(n_calentamiento):
            out = modelo(input_ids=input_ids, attention_mask=attention_mask)
            if hasattr(out, "logits"):
                _ = out.logits
        tiempos = []
        for _ in range(n_reps):
            t0 = time.perf_counter()
            out = modelo(input_ids=input_ids, attention_mask=attention_mask)
            if hasattr(out, "logits"):
                _ = out.logits
            tiempos.append((time.perf_counter() - t0) * 1000.0)
    arr = np.asarray(tiempos, dtype=np.float64)
    return {
        "ms_lote_media": float(arr.mean()),
        "ms_lote_p50": float(np.percentile(arr, 50)),
        "ms_lote_p95": float(np.percentile(arr, 95)),
        "ms_por_ejemplo_media": float(arr.mean() / max(n_muestras, 1)),
        "ms_por_ejemplo_p95": float(np.percentile(arr, 95) / max(n_muestras, 1)),
        "n_reps": n_reps,
        "tamano_lote": n_muestras,
    }


def cuantizar_dinamico(modelo):
    """Cuantización dinámica int8 de las capas lineales (CPU).

    En PyTorch 2.x la API estable sigue siendo `torch.ao.quantization` (con
    aviso de migración a torchao). Para un clasificador, suele conservar casi
    toda la exactitud y recortar la latencia en CPU. El modelo de entrada debe
    estar en CPU y en modo eval.
    """
    import torch

    modelo = modelo.to("cpu").eval()
    return torch.ao.quantization.quantize_dynamic(
        modelo, {torch.nn.Linear}, dtype=torch.qint8
    )


def evaluar_puertas_promocion(
    acc_profesor: float,
    acc_estudiante: float,
    p95_profesor: float,
    p95_estudiante: float,
    *,
    max_hueco_puntos: float = 4.0,
    min_aceleracion: float = 5.0,
) -> dict:
    """Aplica las puertas del ejercicio 5: hueco de exactitud y aceleración p95.

    `p95_profesor` y `p95_estudiante` deben medirse en las mismas condiciones
    (mismo tamaño de lote, mismos hilos, mismo protocolo). La aceleración es
    p95_profesor / p95_estudiante.
    """
    hueco = (float(acc_profesor) - float(acc_estudiante)) * 100.0
    if p95_estudiante and p95_estudiante > 0:
        aceleracion = float(p95_profesor) / float(p95_estudiante)
    else:
        aceleracion = float("inf")
    cumple_calidad = hueco <= max_hueco_puntos + 1e-9
    cumple_latencia = aceleracion >= min_aceleracion
    return {
        "hueco_puntos": hueco,
        "aceleracion_p95": aceleracion,
        "max_hueco_puntos": max_hueco_puntos,
        "min_aceleracion": min_aceleracion,
        "cumple_calidad": bool(cumple_calidad),
        "cumple_latencia": bool(cumple_latencia),
        "decision": "PROMOCIONAR" if (cumple_calidad and cumple_latencia) else "NO PROMOCIONAR",
    }
