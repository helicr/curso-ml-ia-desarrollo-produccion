#!/usr/bin/env bash
# Prepara el Codespace del curso: kind, entorno env-ia-mlops y verificación.
# Probado en un Codespace real (2 núcleos, 8 GB) el 12/11/2026: ver 03-Entorno/VALIDACION.md, «Codespace del curso».
set -euo pipefail

KIND_VERSION="${KIND_VERSION:-v0.27.0}"   # cambiar con: KIND_VERSION=vX.Y.Z (comprobar que existe en github.com/kubernetes-sigs/kind/releases)

# 1) kind
arq="$(uname -m)"; case "$arq" in x86_64) arq=amd64;; aarch64|arm64) arq=arm64;; esac
if ! command -v kind >/dev/null 2>&1; then
  curl -fsSL -o /tmp/kind "https://github.com/kubernetes-sigs/kind/releases/download/${KIND_VERSION}/kind-linux-${arq}"
  sudo install -m 0755 /tmp/kind /usr/local/bin/kind
fi

# 2) solo conda-forge (sin términos de servicio de Anaconda), también para lo que el alumnado instale después
conda config --add channels conda-forge
conda config --remove channels defaults 2>/dev/null || true
conda config --set channel_priority strict
conda config --add default_channels https://conda.anaconda.org/conda-forge

# 3) entorno del curso desde la lista explícita de paquetes (sin resolver dependencias)
#    `conda env create -f environment.yml` resuelve 480 paquetes y supera la memoria de la máquina de 2 núcleos
#    (la terminan hacia los 7 GB). La lista se genera con 03-Entorno/conda/generar_bloqueo_linux.py.
if ! conda env list | grep -q '^env-ia-mlops '; then
  conda create -y -q -n env-ia-mlops --file 03-Entorno/conda/env-ia-mlops-linux-64.txt
fi
conda init bash >/dev/null 2>&1 || true
grep -q 'conda activate env-ia-mlops' ~/.bashrc || echo 'conda activate env-ia-mlops' >> ~/.bashrc

# 4) verificación (no falla la creación del Codespace si algo falta: la verificación lo cuenta)
bash .devcontainer/verificar.sh || true
