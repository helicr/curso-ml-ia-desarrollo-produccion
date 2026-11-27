"""Utilidades compartidas de los cuadernos de RAG (Retrieval-Augmented Generation).

Centraliza lo que se reutiliza entre cuadernos: raíz del proyecto, entorno, proxy
y Hugging Face, carga del corpus, estrategias de *chunking*, embeddings,
índices (NumPy y FAISS), BM25, fusión híbrida, métricas, un generador local y
el *pipeline* de extremo a extremo.
"""

from __future__ import annotations

import json
import os
import random
import re
import time
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Sequence, Union

import numpy as np

SEMILLA_DEFECTO = 42
NOMBRE_UTILS = "rag_utils.py"

# Modelos por defecto: caben en un portátil con CPU y cubren español.
MODELO_EMBEDDINGS_DEFECTO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
MODELO_RERANKER_DEFECTO = "cross-encoder/ms-marco-MiniLM-L-6-v2"
MODELO_LLM_DEFECTO = "Qwen/Qwen2.5-0.5B-Instruct"
MODELO_LLM_RESERVA = "HuggingFaceTB/SmolLM2-135M-Instruct"

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


# ---------------------------------------------------------------------------
# Rutas, semilla, dispositivo y modo rápido
# ---------------------------------------------------------------------------

def encontrar_raiz(partida: Optional[Path] = None) -> Path:
    """Devuelve la raíz del proyecto (la carpeta que contiene src/ y notebooks/)."""
    partida = Path(partida or Path.cwd()).resolve()
    for cand in [partida, *partida.parents]:
        if (cand / "src" / NOMBRE_UTILS).exists() and (cand / "notebooks").is_dir():
            return cand
    raise FileNotFoundError(
        "No encuentro la raíz del proyecto de RAG "
        f"(buscaba src/{NOMBRE_UTILS} y notebooks/). "
        "Abre el cuaderno desde extra-rag-notebooks/ o extra-rag-notebooks/notebooks/."
    )


def preparar_rutas(raiz: Optional[Path] = None) -> dict[str, Path]:
    """Crea las carpetas de trabajo y devuelve un diccionario de rutas."""
    if raiz is None or not (Path(raiz) / "src" / NOMBRE_UTILS).exists():
        raiz_p = encontrar_raiz(raiz)
    else:
        raiz_p = Path(raiz).resolve()
    rutas = {
        "raiz": raiz_p,
        "src": raiz_p / "src",
        "notebooks": raiz_p / "notebooks",
        "modelos": raiz_p / "modelos",
        "resultados": raiz_p / "resultados",
        "datos": raiz_p / "datos",
        "corpus": raiz_p / "datos" / "corpus",
        "cache_hf": raiz_p / "cache-hf",
    }
    for clave in ("modelos", "resultados", "datos", "corpus", "cache_hf"):
        rutas[clave].mkdir(parents=True, exist_ok=True)
    return rutas


def fijar_semilla(semilla: int = SEMILLA_DEFECTO) -> int:
    """Fija semillas de Python, NumPy y PyTorch para poder repetir resultados."""
    os.environ["PYTHONHASHSEED"] = str(semilla)
    random.seed(semilla)
    np.random.seed(semilla)
    try:
        import torch

        torch.manual_seed(semilla)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(semilla)
        torch.use_deterministic_algorithms(False)
    except ImportError:
        pass
    return semilla


def dispositivo() -> "torch.device":
    """Elige CUDA si hay GPU usable; si no, CPU. El curso se completa en CPU."""
    import torch

    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def modo_rapido(valor_por_defecto: bool = True) -> bool:
    """Lee RAG_MODO_RAPIDO (1/0, true/false). Por defecto está activo.

    En modo rápido se reducen el número de preguntas generadas, los tokens
    nuevos del LLM y algún gráfico auxiliar. La recuperación y las métricas
    del conjunto hecho a mano se calculan igual.
    """
    crudo = os.environ.get("RAG_MODO_RAPIDO")
    if crudo is None or crudo.strip() == "":
        return valor_por_defecto
    return crudo.strip().lower() not in {"0", "false", "no", "off"}


# ---------------------------------------------------------------------------
# Proxy corporativo y Hugging Face
# ---------------------------------------------------------------------------

def _presente_no_vacio(nombre: str) -> bool:
    valor = os.environ.get(nombre)
    return bool(valor) and valor.strip() != ""


def configurar_proxy_y_hf(
    raiz: Optional[Path] = None,
    *,
    verbose: bool = True,
) -> dict[str, Any]:
    """Prepara un entorno razonable detrás de un proxy y para Hugging Face.

    No inventa credenciales ni las imprime. Si HF_HOME no está definido, lo
    apunta a cache-hf/ dentro del proyecto.
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
    import importlib
    import platform

    import pandas as pd

    filas: list[dict[str, Any]] = []

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

    for paquete, atributo, obligatorio in [
        ("numpy", "__version__", True),
        ("pandas", "__version__", True),
        ("matplotlib", "__version__", True),
        ("sklearn", "__version__", True),
        ("tqdm", "__version__", True),
        ("torch", "__version__", True),
        ("transformers", "__version__", True),
        ("sentence_transformers", "__version__", True),
        ("faiss", "__version__", True),
        ("rank_bm25", None, True),
        ("accelerate", "__version__", False),
    ]:
        try:
            mod = importlib.import_module(paquete)
            if atributo:
                ver = str(getattr(mod, atributo, "?"))
            else:
                ver = getattr(mod, "__version__", "ok")
            extra = ""
            if paquete == "torch":
                cuda = bool(getattr(mod, "cuda") and mod.cuda.is_available())
                extra = f" · dispositivo: {'cuda' if cuda else 'cpu'}"
                if cuda:
                    extra += f" ({mod.cuda.get_device_name(0)})"
            _add(paquete, True, str(ver) + extra, obligatorio=obligatorio)
        except Exception as exc:  # noqa: BLE001
            _add(paquete, False, f"no importable: {exc}", obligatorio=obligatorio)

    try:
        import torch

        _add("CUDA compilado en torch", bool(torch.backends.cuda.is_built()), torch.version.cuda or "cpu-only")
    except Exception:
        pass

    informe = configurar_proxy_y_hf(verbose=False)
    _add(
        "Proxy HTTP(S)",
        informe["proxy_http"] or informe["proxy_https"],
        "definido" if (informe["proxy_http"] or informe["proxy_https"]) else "no definido (salida directa)",
    )
    _add(
        "Token Hugging Face",
        informe["token_hf"],
        "presente" if informe["token_hf"] else "no presente (los modelos públicos no lo necesitan)",
    )
    _add("HF_HOME", True, str(informe["hf_home"]))
    return pd.DataFrame(filas)


def probar_conexion_hf(timeout: float = 8.0) -> dict[str, Any]:
    """Comprueba si se puede alcanzar el Hub de Hugging Face. No descarga modelos."""
    import ssl
    import urllib.error
    import urllib.request

    url = os.environ.get("HF_ENDPOINT", "https://huggingface.co")
    resultado: dict[str, Any] = {"url": url, "ok": False, "estado": None, "error": None}
    try:
        ctx = ssl.create_default_context()
        cert = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
        if cert and Path(cert).exists():
            ctx = ssl.create_default_context(cafile=cert)
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "rag-cuadernos/1.0"})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            resultado["ok"] = 200 <= getattr(resp, "status", 200) < 400
            resultado["estado"] = getattr(resp, "status", None)
    except Exception as exc:  # noqa: BLE001
        resultado["error"] = f"{type(exc).__name__}: {exc}"
    return resultado


# ---------------------------------------------------------------------------
# Persistencia
# ---------------------------------------------------------------------------

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
        if dataclass_ok := getattr(o, "__dataclass_fields__", None):  # noqa: F841
            return asdict(o)
        raise TypeError(f"No se puede serializar {type(o)}")

    ruta.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=_default), encoding="utf-8")
    return ruta


def cargar_json(ruta: Path) -> Any:
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Corpus y *chunking*
# ---------------------------------------------------------------------------

@dataclass
class Documento:
    id: str
    titulo: str
    ruta: str
    texto: str
    n_caracteres: int = 0
    n_palabras: int = 0

    def __post_init__(self):
        if not self.n_caracteres:
            self.n_caracteres = len(self.texto)
        if not self.n_palabras:
            self.n_palabras = len(self.texto.split())


@dataclass
class Fragmento:
    id: str
    doc_id: str
    titulo: str
    texto: str
    orden: int
    inicio: int
    fin: int
    estrategia: str
    metadatos: dict = field(default_factory=dict)

    def a_dict(self) -> dict[str, Any]:
        return asdict(self)


def _titulo_de_markdown(texto: str, fallback: str) -> str:
    for linea in texto.splitlines():
        s = linea.strip()
        if s.startswith("# "):
            return s[2:].strip()
    return fallback


def cargar_corpus(carpeta: Optional[Path] = None) -> list[Documento]:
    """Carga todos los `.md` de datos/corpus/ (o de la carpeta indicada)."""
    if carpeta is None:
        carpeta = preparar_rutas()["corpus"]
    carpeta = Path(carpeta)
    docs: list[Documento] = []
    for p in sorted(carpeta.glob("*.md")):
        texto = p.read_text(encoding="utf-8").strip() + "\n"
        docs.append(
            Documento(
                id=p.stem,
                titulo=_titulo_de_markdown(texto, p.stem),
                ruta=str(p),
                texto=texto,
            )
        )
    if not docs:
        raise FileNotFoundError(f"No hay documentos .md en {carpeta}")
    return docs


def cargar_preguntas(ruta: Optional[Path] = None) -> list[dict[str, Any]]:
    if ruta is None:
        ruta = preparar_rutas()["datos"] / "preguntas.json"
    payload = cargar_json(Path(ruta))
    return list(payload["preguntas"])


def _cortar_en_limite_de_palabra(texto: str, objetivo: int) -> int:
    """Devuelve un índice ≤ objetivo que no parte una palabra, si es posible."""
    if objetivo >= len(texto):
        return len(texto)
    if objetivo <= 0:
        return 0
    if texto[objetivo].isspace() or texto[objetivo - 1].isspace():
        return objetivo
    anterior = texto.rfind(" ", 0, objetivo)
    if anterior >= max(0, objetivo - 40):
        return anterior + 1
    return objetivo


def fragmentar_fijo(
    texto: str,
    tamano: int = 400,
    solape: int = 0,
) -> list[tuple[int, int, str]]:
    """Particiones por caracteres, con solape opcional, evitando cortes a mitad de palabra."""
    if tamano <= 0:
        raise ValueError("tamano debe ser positivo.")
    if solape < 0 or solape >= tamano:
        raise ValueError("solape debe estar en [0, tamano).")
    texto = texto.strip()
    trozos: list[tuple[int, int, str]] = []
    i = 0
    n = len(texto)
    while i < n:
        fin = _cortar_en_limite_de_palabra(texto, min(n, i + tamano))
        if fin <= i:
            fin = min(n, i + tamano)
        trozo = texto[i:fin].strip()
        if trozo:
            # Recalcular fin efectivo sin espacios de más a la derecha del slice original.
            trozos.append((i, i + len(texto[i:fin].rstrip()), trozo))
        if fin >= n:
            break
        i = max(fin - solape, i + 1)
    return trozos


def fragmentar_parrafos(
    texto: str,
    tamano_max: int = 500,
    solape: int = 40,
) -> list[tuple[int, int, str]]:
    """Agrupa párrafos (separados por una línea en blanco) sin pasar de tamano_max.

    Un párrafo más largo que tamano_max se parte con fragmentar_fijo y solape.
    """
    partes = re.split(r"(\n\s*\n)", texto)
    # partes alterna texto y separador
    bloques: list[tuple[int, str]] = []
    cursor = 0
    buf = ""
    buf_inicio = 0
    for parte in partes:
        if re.fullmatch(r"\n\s*\n", parte or ""):
            cursor += len(parte)
            continue
        if not parte.strip():
            cursor += len(parte)
            continue
        candidato = (buf + "\n\n" + parte).strip() if buf else parte.strip()
        if buf and len(candidato) > tamano_max:
            bloques.append((buf_inicio, buf.strip()))
            buf = parte
            buf_inicio = cursor
        else:
            if not buf:
                buf_inicio = cursor
            buf = candidato
        cursor += len(parte)
    if buf.strip():
        bloques.append((buf_inicio, buf.strip()))

    trozos: list[tuple[int, int, str]] = []
    for inicio, bloque in bloques:
        if len(bloque) <= tamano_max:
            trozos.append((inicio, inicio + len(bloque), bloque))
        else:
            for i, f, t in fragmentar_fijo(bloque, tamano=tamano_max, solape=solape):
                trozos.append((inicio + i, inicio + f, t))
    return trozos


def fragmentar_documentos(
    documentos: Sequence[Documento],
    estrategia: str = "solape",
    tamano: int = 400,
    solape: int = 80,
) -> list[Fragmento]:
    """Aplica una estrategia de troceado a todos los documentos.

    estrategias: "fijo" (sin solape), "solape" (fijo con solape), "parrafos".
    """
    estrategia = estrategia.lower().strip()
    fragmentos: list[Fragmento] = []
    for doc in documentos:
        if estrategia == "fijo":
            pares = fragmentar_fijo(doc.texto, tamano=tamano, solape=0)
        elif estrategia in {"solape", "fijo_solape", "overlap"}:
            pares = fragmentar_fijo(doc.texto, tamano=tamano, solape=solape)
        elif estrategia in {"parrafos", "párrafos", "paragraph"}:
            pares = fragmentar_parrafos(doc.texto, tamano_max=tamano, solape=min(solape, max(0, tamano - 1)))
        else:
            raise ValueError(f"Estrategia desconocida: {estrategia}")
        for orden, (inicio, fin, texto) in enumerate(pares):
            fragmentos.append(
                Fragmento(
                    id=f"{doc.id}::#{orden}",
                    doc_id=doc.id,
                    titulo=doc.titulo,
                    texto=texto,
                    orden=orden,
                    inicio=inicio,
                    fin=fin,
                    estrategia=estrategia,
                    metadatos={"tamano": tamano, "solape": solape, "n_caracteres": len(texto)},
                )
            )
    return fragmentos


def resumen_fragmentos(fragmentos: Sequence[Fragmento]) -> dict[str, Any]:
    longitudes = [len(f.texto) for f in fragmentos]
    docs = {f.doc_id for f in fragmentos}
    return {
        "n_fragmentos": len(fragmentos),
        "n_documentos": len(docs),
        "estrategia": fragmentos[0].estrategia if fragmentos else None,
        "longitud_media": float(np.mean(longitudes)) if longitudes else 0.0,
        "longitud_mediana": float(np.median(longitudes)) if longitudes else 0.0,
        "longitud_min": int(min(longitudes) if longitudes else 0),
        "longitud_max": int(max(longitudes) if longitudes else 0),
        "por_documento": {
            doc: int(sum(1 for f in fragmentos if f.doc_id == doc))
            for doc in sorted(docs)
        },
    }


# ---------------------------------------------------------------------------
# Tokens simples, embeddings y similitud
# ---------------------------------------------------------------------------

def tokenizar(texto: str) -> list[str]:
    """Tokenización sencilla para BM25: minúsculas, sin acentos, palabras y números."""
    norm = unicodedata.normalize("NFD", texto.lower())
    sin_acentos = "".join(c for c in norm if unicodedata.category(c) != "Mn")
    return re.findall(r"[a-z0-9]+", sin_acentos)


def normalizar_vectores(vectores: np.ndarray) -> np.ndarray:
    v = np.asarray(vectores, dtype=np.float32)
    if v.ndim == 1:
        n = np.linalg.norm(v) + 1e-12
        return v / n
    n = np.linalg.norm(v, axis=1, keepdims=True) + 1e-12
    return v / n


def similitud_coseno(a: np.ndarray, b: np.ndarray) -> Union[float, np.ndarray]:
    """Similitud coseno. Si a y b son 1-D, devuelve un float; si no, una matriz."""
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    a1 = a.ndim == 1
    b1 = b.ndim == 1
    if a1:
        a = a.reshape(1, -1)
    if b1:
        b = b.reshape(1, -1)
    a = normalizar_vectores(a)
    b = normalizar_vectores(b)
    mat = a @ b.T
    if a1 and b1:
        return float(mat[0, 0])
    if a1:
        return mat.ravel() if b.shape[0] != 1 else float(mat[0, 0])
    if b1:
        return mat.ravel()
    return mat


class Codificador:
    """Envuelve un *sentence-transformers* para no repetir la carga en cada cuaderno."""

    def __init__(
        self,
        nombre: str = MODELO_EMBEDDINGS_DEFECTO,
        dispositivo_destino: Optional[str] = None,
    ):
        from sentence_transformers import SentenceTransformer

        self.nombre = nombre
        dev = dispositivo_destino or str(dispositivo())
        self.dispositivo = dev
        self.modelo = SentenceTransformer(nombre, device=dev)
        if hasattr(self.modelo, "get_embedding_dimension"):
            self.dim = int(self.modelo.get_embedding_dimension())
        else:
            self.dim = int(self.modelo.get_sentence_embedding_dimension())

    def codificar(
        self,
        textos: Sequence[str],
        *,
        lote: int = 32,
        normalizar: bool = True,
        progreso: Optional[bool] = None,
    ) -> np.ndarray:
        if isinstance(textos, str):
            textos = [textos]
        mostrar = len(textos) > 8 if progreso is None else progreso
        vec = self.modelo.encode(
            list(textos),
            batch_size=lote,
            convert_to_numpy=True,
            normalize_embeddings=normalizar,
            show_progress_bar=mostrar,
        )
        return np.asarray(vec, dtype=np.float32)


# ---------------------------------------------------------------------------
# Índices: NumPy, FAISS, BM25 e híbrido
# ---------------------------------------------------------------------------

@dataclass
class Resultado:
    fragmento: Fragmento
    puntuacion: float
    rango: int
    metodo: str

    def a_dict(self) -> dict[str, Any]:
        d = self.fragmento.a_dict()
        d["puntuacion"] = float(self.puntuacion)
        d["rango"] = int(self.rango)
        d["metodo"] = self.metodo
        return d


def _ordenar_y_empaquetar(
    puntuaciones: np.ndarray,
    fragmentos: Sequence[Fragmento],
    k: int,
    metodo: str,
) -> list[Resultado]:
    k = min(int(k), len(fragmentos))
    if k <= 0:
        return []
    idx = np.argsort(-puntuaciones)[:k]
    return [
        Resultado(fragmento=fragmentos[i], puntuacion=float(puntuaciones[i]), rango=r, metodo=metodo)
        for r, i in enumerate(idx, start=1)
    ]


class IndiceNumpy:
    """Búsqueda densa por producto interno (equivalente a coseno si está normalizado)."""

    def __init__(self, vectores: np.ndarray, fragmentos: Sequence[Fragmento], normalizar: bool = True):
        vec = np.asarray(vectores, dtype=np.float32)
        if vec.ndim != 2:
            raise ValueError("vectores debe ser una matriz (n_fragmentos, dim).")
        if len(fragmentos) != vec.shape[0]:
            raise ValueError("El número de vectores y de fragmentos no coincide.")
        self.vectores = normalizar_vectores(vec) if normalizar else vec
        self.fragmentos = list(fragmentos)
        self.dim = int(self.vectores.shape[1])

    def buscar(self, consulta: np.ndarray, k: int = 5) -> list[Resultado]:
        q = normalizar_vectores(np.asarray(consulta, dtype=np.float32).reshape(1, -1))[0]
        scores = self.vectores @ q
        return _ordenar_y_empaquetar(scores, self.fragmentos, k, metodo="denso-numpy")

    def guardar(self, carpeta: Path) -> Path:
        carpeta = Path(carpeta)
        carpeta.mkdir(parents=True, exist_ok=True)
        np.save(carpeta / "vectores.npy", self.vectores)
        guardar_json([f.a_dict() for f in self.fragmentos], carpeta / "fragmentos.json")
        guardar_json({"dim": self.dim, "n": len(self.fragmentos), "tipo": "numpy"}, carpeta / "meta.json")
        return carpeta

    @classmethod
    def cargar(cls, carpeta: Path) -> "IndiceNumpy":
        carpeta = Path(carpeta)
        vectores = np.load(carpeta / "vectores.npy")
        frags = [Fragmento(**{k: v for k, v in d.items() if k in Fragmento.__dataclass_fields__}) for d in cargar_json(carpeta / "fragmentos.json")]
        return cls(vectores, frags, normalizar=False)


class IndiceFAISS:
    """Índice FAISS de producto interno (IndexFlatIP) sobre vectores normalizados."""

    def __init__(self, vectores: np.ndarray, fragmentos: Sequence[Fragmento], normalizar: bool = True):
        import faiss

        vec = np.asarray(vectores, dtype=np.float32)
        if len(fragmentos) != vec.shape[0]:
            raise ValueError("El número de vectores y de fragmentos no coincide.")
        self.vectores = normalizar_vectores(vec) if normalizar else vec
        self.fragmentos = list(fragmentos)
        self.dim = int(self.vectores.shape[1])
        self.index = faiss.IndexFlatIP(self.dim)
        self.index.add(self.vectores)

    def buscar(self, consulta: np.ndarray, k: int = 5) -> list[Resultado]:
        q = normalizar_vectores(np.asarray(consulta, dtype=np.float32).reshape(1, -1))
        k = min(int(k), len(self.fragmentos))
        scores, idx = self.index.search(q, k)
        out: list[Resultado] = []
        for rango, (j, s) in enumerate(zip(idx[0], scores[0]), start=1):
            if j < 0:
                continue
            out.append(Resultado(fragmento=self.fragmentos[int(j)], puntuacion=float(s), rango=rango, metodo="denso-faiss"))
        return out

    def guardar(self, carpeta: Path) -> Path:
        import faiss

        carpeta = Path(carpeta)
        carpeta.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(carpeta / "indice.faiss"))
        np.save(carpeta / "vectores.npy", self.vectores)
        guardar_json([f.a_dict() for f in self.fragmentos], carpeta / "fragmentos.json")
        guardar_json({"dim": self.dim, "n": len(self.fragmentos), "tipo": "faiss"}, carpeta / "meta.json")
        return carpeta

    @classmethod
    def cargar(cls, carpeta: Path) -> "IndiceFAISS":
        carpeta = Path(carpeta)
        vectores = np.load(carpeta / "vectores.npy")
        frags = [Fragmento(**{k: v for k, v in d.items() if k in Fragmento.__dataclass_fields__}) for d in cargar_json(carpeta / "fragmentos.json")]
        return cls(vectores, frags, normalizar=False)


class IndiceBM25:
    """Búsqueda dispersa clásica (Okapi BM25) sobre los mismos fragmentos."""

    def __init__(self, fragmentos: Sequence[Fragmento]):
        from rank_bm25 import BM25Okapi

        self.fragmentos = list(fragmentos)
        self.corpus_tokens = [tokenizar(f.texto) for f in self.fragmentos]
        self.bm25 = BM25Okapi(self.corpus_tokens)

    def buscar(self, consulta: str, k: int = 5) -> list[Resultado]:
        scores = np.asarray(self.bm25.get_scores(tokenizar(consulta)), dtype=np.float64)
        return _ordenar_y_empaquetar(scores, self.fragmentos, k, metodo="bm25")


def fusion_rrf(
    listas: Sequence[Sequence[Resultado]],
    k: int = 5,
    k_rrf: int = 60,
) -> list[Resultado]:
    """Fusión por Reciprocal Rank Fusion: 1 / (k_rrf + rango), sumado entre listas."""
    acumulado: dict[str, float] = {}
    objetos: dict[str, Fragmento] = {}
    for lista in listas:
        for item in lista:
            fid = item.fragmento.id
            acumulado[fid] = acumulado.get(fid, 0.0) + 1.0 / (k_rrf + item.rango)
            objetos[fid] = item.fragmento
    orden = sorted(acumulado.items(), key=lambda kv: (-kv[1], kv[0]))[:k]
    return [
        Resultado(fragmento=objetos[fid], puntuacion=float(p), rango=r, metodo="hibrido-rrf")
        for r, (fid, p) in enumerate(orden, start=1)
    ]


class Reranker:
    """Reordenador opcional con un *cross-encoder*. Puede fallar al descargar: es opcional."""

    def __init__(self, nombre: str = MODELO_RERANKER_DEFECTO, dispositivo_destino: Optional[str] = None):
        from sentence_transformers import CrossEncoder

        self.nombre = nombre
        self.dispositivo = dispositivo_destino or str(dispositivo())
        self.modelo = CrossEncoder(nombre, device=self.dispositivo)

    def reordenar(self, consulta: str, candidatos: Sequence[Resultado], k: int = 5) -> list[Resultado]:
        if not candidatos:
            return []
        pares = [(consulta, c.fragmento.texto) for c in candidatos]
        scores = np.asarray(self.modelo.predict(pares), dtype=np.float64)
        orden = np.argsort(-scores)[: min(k, len(candidatos))]
        out: list[Resultado] = []
        for rango, i in enumerate(orden, start=1):
            c = candidatos[int(i)]
            out.append(Resultado(fragmento=c.fragmento, puntuacion=float(scores[int(i)]), rango=rango, metodo="rerank"))
        return out


# ---------------------------------------------------------------------------
# Métricas de recuperación
# ---------------------------------------------------------------------------

def _como_conjunto(valor: Union[str, Sequence[str], None]) -> set[str]:
    if valor is None:
        return set()
    if isinstance(valor, str):
        return {valor} if valor else set()
    return {v for v in valor if v}


def acierto_en_k(ids_predichos: Sequence[str], ids_oro: Sequence[str] | set[str], k: int) -> float:
    oro = _como_conjunto(ids_oro)
    if not oro:
        return float("nan")
    top = list(ids_predichos)[:k]
    return 1.0 if any(i in oro for i in top) else 0.0


def mrr_de_una(ids_predichos: Sequence[str], ids_oro: Sequence[str] | set[str]) -> float:
    oro = _como_conjunto(ids_oro)
    if not oro:
        return float("nan")
    for i, pred in enumerate(ids_predichos, start=1):
        if pred in oro:
            return 1.0 / i
    return 0.0


def evaluar_recuperacion(
    preguntas: Sequence[dict[str, Any]],
    funcion_buscar: Callable[[str, int], list[Resultado]],
    k: int = 5,
    clave_oro: str = "docs_relevantes",
    usar_doc_id: bool = True,
) -> dict[str, Any]:
    """Evalúa recall@k y MRR sobre preguntas con documentos (o fragmentos) de referencia.

    Las preguntas de tipo `no_esta` sin documentos de referencia se omiten del promedio
    de acierto (no hay un documento 'correcto' que recuperar).
    """
    filas = []
    for p in preguntas:
        oro = _como_conjunto(p.get(clave_oro))
        if p.get("tipo") == "no_esta" and not oro:
            continue
        resultados = funcion_buscar(p["pregunta"], k)
        ids = [r.fragmento.doc_id if usar_doc_id else r.fragmento.id for r in resultados]
        rec = acierto_en_k(ids, oro, k)
        mrr = mrr_de_una(ids, oro)
        filas.append(
            {
                "id": p.get("id"),
                "pregunta": p["pregunta"],
                "oro": sorted(oro),
                "recuperados": ids,
                f"recall@{k}": rec,
                "mrr": mrr,
            }
        )
    recalls = [f[f"recall@{k}"] for f in filas if f[f"recall@{k}"] == f[f"recall@{k}"]]
    mrrs = [f["mrr"] for f in filas if f["mrr"] == f["mrr"]]
    resumen = {
        "k": k,
        "n_evaluadas": len(filas),
        f"recall@{k}": float(np.mean(recalls)) if recalls else float("nan"),
        "mrr": float(np.mean(mrrs)) if mrrs else float("nan"),
        "detalle": filas,
    }
    return resumen


# ---------------------------------------------------------------------------
# Generación local y *prompts*
# ---------------------------------------------------------------------------

SISTEMA_CON_RAG = (
    "Eres un asistente del curso taller 'De Modelo a Producción' (UNTRM). "
    "Respondes SOLO con la información del contexto que se te proporciona. "
    "Si la respuesta no está en el contexto, di exactamente: "
    "'No encuentro esa información en los documentos.' "
    "Cita el identificador del fragmento entre corchetes, por ejemplo [guia-docker::#1]. "
    "No inventes cifras, nombres, fechas ni políticas. Sé breve (3 a 6 frases)."
)

SISTEMA_SIN_RAG = (
    "Eres un asistente general. Responde a la pregunta del usuario de forma breve. "
    "Si no estás seguro, puedes intentar una respuesta, pero indica si es una suposición."
)


def construir_contexto(fragmentos_o_resultados: Sequence[Union[Fragmento, Resultado]], max_caracteres: int = 2200) -> str:
    bloques = []
    usado = 0
    for item in fragmentos_o_resultados:
        frag = item.fragmento if isinstance(item, Resultado) else item
        pieza = f"[{frag.id}] {frag.titulo}\n{frag.texto.strip()}"
        if usado + len(pieza) > max_caracteres and bloques:
            break
        bloques.append(pieza)
        usado += len(pieza)
    return "\n\n".join(bloques)


def construir_mensajes(
    pregunta: str,
    resultados: Optional[Sequence[Union[Fragmento, Resultado]]] = None,
    *,
    con_rag: bool = True,
) -> list[dict[str, str]]:
    if con_rag:
        contexto = construir_contexto(resultados or [])
        usuario = (
            "Contexto:\n"
            f"{contexto if contexto else '(no hay fragmentos recuperados)'}\n\n"
            f"Pregunta: {pregunta}\n\n"
            "Respuesta fundada en el contexto:"
        )
        return [
            {"role": "system", "content": SISTEMA_CON_RAG},
            {"role": "user", "content": usuario},
        ]
    return [
        {"role": "system", "content": SISTEMA_SIN_RAG},
        {"role": "user", "content": pregunta},
    ]


class GeneradorLocal:
    """LLM instructivo pequeño, pensado para CPU. Intenta el modelo pedido y, si falla, uno de reserva."""

    def __init__(
        self,
        nombre: str = MODELO_LLM_DEFECTO,
        dispositivo_destino: Optional[str] = None,
        reserva: str = MODELO_LLM_RESERVA,
        dtype: Optional[str] = None,
    ):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.dispositivo = torch.device(dispositivo_destino or str(dispositivo()))
        self.nombre = nombre
        self.dtype_nombre = dtype
        candidatos = [nombre]
        if reserva and reserva != nombre:
            candidatos.append(reserva)

        ultimo_error: Optional[Exception] = None
        self.tokenizer = None
        self.modelo = None
        for cand in candidatos:
            try:
                tok = AutoTokenizer.from_pretrained(cand)
                if tok.pad_token_id is None and tok.eos_token_id is not None:
                    tok.pad_token = tok.eos_token
                tipo = None
                if dtype == "float16":
                    tipo = torch.float16
                elif dtype == "bfloat16":
                    tipo = torch.bfloat16
                elif dtype == "float32":
                    tipo = torch.float32
                elif self.dispositivo.type == "cpu":
                    # float16 en CPU de PyTorch es limitado; float32 es lo predecible.
                    tipo = torch.float32
                modelo = AutoModelForCausalLM.from_pretrained(
                    cand,
                    dtype=tipo if tipo is not None else "auto",
                    low_cpu_mem_usage=True,
                )
                modelo.to(self.dispositivo)
                modelo.eval()
                self.tokenizer = tok
                self.modelo = modelo
                self.nombre = cand
                self.dtype_nombre = str(next(modelo.parameters()).dtype)
                break
            except Exception as exc:  # noqa: BLE001
                ultimo_error = exc
                print(f"No se pudo cargar {cand}: {type(exc).__name__}: {exc}")
                continue
        if self.modelo is None:
            raise RuntimeError(f"No pude cargar ningún LLM local. Último error: {ultimo_error}")

    def generar(
        self,
        mensajes: Sequence[dict[str, str]],
        *,
        max_nuevos: int = 80,
        temperatura: float = 0.0,
    ) -> str:
        import torch

        tok = self.tokenizer
        if hasattr(tok, "apply_chat_template"):
            prompt = tok.apply_chat_template(list(mensajes), tokenize=False, add_generation_prompt=True)
        else:
            prompt = "\n".join(f"{m['role']}: {m['content']}" for m in mensajes) + "\nassistant:"
        entradas = tok(prompt, return_tensors="pt", truncation=True, max_length=2048)
        entradas = {k: v.to(self.dispositivo) for k, v in entradas.items()}
        n_in = int(entradas["input_ids"].shape[1])
        with torch.inference_mode():
            kwargs: dict[str, Any] = {
                "max_new_tokens": int(max_nuevos),
                "pad_token_id": tok.pad_token_id or tok.eos_token_id,
                "eos_token_id": tok.eos_token_id,
            }
            if temperatura and temperatura > 0:
                kwargs["do_sample"] = True
                kwargs["temperature"] = float(temperatura)
            else:
                kwargs["do_sample"] = False
            salidas = self.modelo.generate(**entradas, **kwargs)
        nuevos = salidas[0, n_in:]
        texto = tok.decode(nuevos, skip_special_tokens=True).strip()
        return texto


def _normalizar_para_hecho(texto: str) -> str:
    norm = unicodedata.normalize("NFD", texto.lower())
    sin = "".join(c for c in norm if unicodedata.category(c) != "Mn")
    sin = sin.replace("http://", "").replace("https://", "")
    return re.sub(r"\s+", " ", sin).strip()


def contiene_hechos(respuesta: str, hechos: Sequence[str]) -> dict[str, Any]:
    """Comprueba si cada hecho (cadena) aparece en la respuesta, con normalización suave."""
    resp = _normalizar_para_hecho(respuesta)
    detalle = []
    for h in hechos:
        hn = _normalizar_para_hecho(str(h))
        # Aceptar '1200' si el hecho es '1 200'
        variantes = {hn, hn.replace(" ", "")}
        ok = any(v and v in resp.replace(" ", "") if " " in hn else v in resp for v in variantes)
        # Más simple y predecible:
        ok = hn in resp or hn.replace(" ", "") in resp.replace(" ", "")
        detalle.append({"hecho": h, "presente": bool(ok)})
    n = len(detalle)
    n_ok = sum(1 for d in detalle if d["presente"])
    return {
        "n_hechos": n,
        "n_presentes": n_ok,
        "cobertura": (n_ok / n) if n else float("nan"),
        "detalle": detalle,
    }


def parece_abstencion(respuesta: str) -> bool:
    t = _normalizar_para_hecho(respuesta)
    claves = [
        "no encuentro esa informacion",
        "no esta en los documentos",
        "no aparece en el contexto",
        "no tengo esa informacion",
        "no se menciona",
        "no figura en",
    ]
    return any(c in t for c in claves)


# ---------------------------------------------------------------------------
# Pipeline de extremo a extremo
# ---------------------------------------------------------------------------

class PipelineRAG:
    """Recupera k fragmentos y genera una respuesta con un LLM local.

    Se puede instanciar con un índice denso, uno BM25 o ambos (fusión RRF).
    """

    def __init__(
        self,
        codificador: Codificador,
        indice_denso: Optional[Union[IndiceNumpy, IndiceFAISS]] = None,
        indice_bm25: Optional[IndiceBM25] = None,
        generador: Optional[GeneradorLocal] = None,
        reranker: Optional[Reranker] = None,
        k: int = 4,
        k_candidatos: int = 8,
        metodo: str = "denso",
    ):
        self.codificador = codificador
        self.indice_denso = indice_denso
        self.indice_bm25 = indice_bm25
        self.generador = generador
        self.reranker = reranker
        self.k = int(k)
        self.k_candidatos = int(k_candidatos)
        self.metodo = metodo

    def recuperar(self, pregunta: str, k: Optional[int] = None) -> list[Resultado]:
        k_final = int(k or self.k)
        k_cand = max(k_final, self.k_candidatos if self.reranker is not None else k_final)
        metodo = self.metodo
        denso: list[Resultado] = []
        lex: list[Resultado] = []
        if metodo in {"denso", "hibrido"} and self.indice_denso is not None:
            vec = self.codificador.codificar([pregunta], progreso=False)[0]
            denso = self.indice_denso.buscar(vec, k=k_cand)
        if metodo in {"bm25", "hibrido"} and self.indice_bm25 is not None:
            lex = self.indice_bm25.buscar(pregunta, k=k_cand)
        if metodo == "hibrido":
            candidatos = fusion_rrf([denso, lex], k=k_cand)
        elif metodo == "bm25":
            candidatos = lex
        else:
            candidatos = denso
        if self.reranker is not None and candidatos:
            return self.reranker.reordenar(pregunta, candidatos, k=k_final)
        return candidatos[:k_final]

    def preguntar(
        self,
        pregunta: str,
        *,
        con_rag: bool = True,
        k: Optional[int] = None,
        max_nuevos: int = 80,
    ) -> dict[str, Any]:
        if self.generador is None:
            raise RuntimeError("Este pipeline no tiene generador (LLM) cargado.")
        t0 = time.perf_counter()
        resultados: list[Resultado] = []
        t_rec = 0.0
        if con_rag:
            t_r0 = time.perf_counter()
            resultados = self.recuperar(pregunta, k=k)
            t_rec = time.perf_counter() - t_r0
        mensajes = construir_mensajes(pregunta, resultados, con_rag=con_rag)
        t_g0 = time.perf_counter()
        respuesta = self.generador.generar(mensajes, max_nuevos=max_nuevos)
        t_gen = time.perf_counter() - t_g0
        total = time.perf_counter() - t0
        return {
            "pregunta": pregunta,
            "respuesta": respuesta,
            "con_rag": con_rag,
            "fuentes": [r.a_dict() for r in resultados],
            "ids_fuentes": [r.fragmento.id for r in resultados],
            "docs_fuentes": [r.fragmento.doc_id for r in resultados],
            "latencias_s": {
                "recuperacion": round(t_rec, 4),
                "generacion": round(t_gen, 4),
                "total": round(total, 4),
            },
            "metodo": self.metodo if con_rag else "sin-rag",
            "modelo_llm": self.generador.nombre,
            "modelo_embeddings": self.codificador.nombre,
        }


def evaluar_fidelidad(
    preguntas: Sequence[dict[str, Any]],
    pipeline: PipelineRAG,
    *,
    con_rag: bool = True,
    max_nuevos: int = 80,
    k: Optional[int] = None,
) -> dict[str, Any]:
    """Genera respuestas y mide cobertura de hechos (y abstención en preguntas 'no_esta')."""
    filas = []
    for p in preguntas:
        out = pipeline.preguntar(p["pregunta"], con_rag=con_rag, k=k, max_nuevos=max_nuevos)
        hechos = p.get("hechos") or []
        tipo = p.get("tipo", "hecho")
        if tipo == "no_esta":
            ok = parece_abstencion(out["respuesta"])
            cob = float(ok)
            det = {"abstencion": ok}
        else:
            det = contiene_hechos(out["respuesta"], hechos)
            cob = det["cobertura"]
            ok = cob == 1.0 if hechos else False
        filas.append(
            {
                "id": p.get("id"),
                "tipo": tipo,
                "pregunta": p["pregunta"],
                "respuesta": out["respuesta"],
                "con_rag": con_rag,
                "cobertura_hechos": cob,
                "ok": ok,
                "detalle": det,
                "docs_fuentes": out["docs_fuentes"],
                "latencias_s": out["latencias_s"],
            }
        )
    coberturas = [f["cobertura_hechos"] for f in filas if f["cobertura_hechos"] == f["cobertura_hechos"]]
    return {
        "con_rag": con_rag,
        "n": len(filas),
        "cobertura_media": float(np.mean(coberturas)) if coberturas else float("nan"),
        "n_ok": int(sum(1 for f in filas if f["ok"])),
        "latencia_media_s": float(np.mean([f["latencias_s"]["total"] for f in filas])) if filas else float("nan"),
        "detalle": filas,
    }
