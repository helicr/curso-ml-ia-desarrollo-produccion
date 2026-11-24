"""Descarga el zip portátil de Ollama (sin proxy de entorno; GitHub falla con el proxy) y lo extrae en C:\bk\ollama."""
import time, zipfile, pathlib, requests

B = "C:/bk/cert/bk-bundle-full.crt"
URL = "https://github.com/ollama/ollama/releases/download/v0.40.17/ollama-windows-amd64.zip"
dest = pathlib.Path(r"C:\bk\ollama-descarga")
dest.mkdir(exist_ok=True)
z = dest / "ollama-windows-amd64.zip"
s = requests.Session(); s.trust_env = False
t0 = time.time()
with s.get(URL, verify=B, stream=True, timeout=60) as r:
    r.raise_for_status()
    with open(z, "wb") as f:
        for c in r.iter_content(1 << 20):
            f.write(c)
print("descarga_s", round(time.time() - t0, 1), "bytes", z.stat().st_size)
out = pathlib.Path(r"C:\bk\ollama"); out.mkdir(exist_ok=True)
with zipfile.ZipFile(z) as zf:
    zf.extractall(out)
print("extraido")
