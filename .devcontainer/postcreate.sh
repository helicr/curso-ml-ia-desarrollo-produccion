#!/usr/bin/env bash
# Prepara el Codespace del curso: kind, entorno env-ia-mlops y verificación.
# Estado: escrito el 10/11/2026 y NO probado todavía en un Codespace real (ver 03-Entorno/VALIDACION.md).
set -euo pipefail

KIND_VERSION="${KIND_VERSION:-v0.27.0}"   # cambiar con: KIND_VERSION=vX.Y.Z (comprobar que existe en github.com/kubernetes-sigs/kind/releases)

# 1) kind
arq="$(uname -m)"; case "$arq" in x86_64) arq=amd64;; aarch64|arm64) arq=arm64;; esac
if ! command -v kind >/dev/null 2>&1; then
  curl -fsSL -o /tmp/kind "https://github.com/kubernetes-sigs/kind/releases/download/${KIND_VERSION}/kind-linux-${arq}"
  sudo install -m 0755 /tmp/kind /usr/local/bin/kind
fi

# 2) entorno del curso (solo conda-forge, sin términos de servicio de Anaconda)
if ! conda env list | grep -q '^env-ia-mlops '; then
  conda env create --override-channels -c conda-forge -f 03-Entorno/conda/environment.yml
fi
conda init bash >/dev/null 2>&1 || true
grep -q 'conda activate env-ia-mlops' ~/.bashrc || echo 'conda activate env-ia-mlops' >> ~/.bashrc

# 3) verificación (no falla la creación del Codespace si algo falta: la verificación lo cuenta)
bash .devcontainer/verificar.sh || true
