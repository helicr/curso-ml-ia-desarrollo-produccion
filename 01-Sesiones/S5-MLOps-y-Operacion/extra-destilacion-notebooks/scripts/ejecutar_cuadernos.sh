#!/usr/bin/env bash
# Ejecuta los cuadernos de la serie (v1 y v2) en orden y deja las salidas guardadas en los .ipynb.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -x "$ROOT/venv/bin/python" ]]; then
  PY="$ROOT/venv/bin/python"
else
  PY="${PYTHON:-python3}"
fi
export HF_HOME="${HF_HOME:-$ROOT/cache-hf}"
export TOKENIZERS_PARALLELISM=false
export HF_HUB_DISABLE_TELEMETRY=1
TIMEOUT_LARGO="${TIMEOUT_LARGO:-1800}"
for nb in \
  notebooks/00-introduccion-y-setup.ipynb \
  notebooks/01-teoria-softmax-temperatura.ipynb \
  notebooks/02-destilacion-mnist-mlp.ipynb \
  notebooks/03-destilacion-bert-sentimiento.ipynb \
  notebooks/04-comparativa-y-produccion.ipynb \
  notebooks/05-ejercicios.ipynb \
  notebooks/06-destilacion-v2-sentimiento.ipynb \
  notebooks/07-comparativa-v1-vs-v2.ipynb
do
  echo "=== $nb ==="
  "$PY" -m jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout="$TIMEOUT_LARGO" \
    --ExecutePreprocessor.kernel_name=python3 \
    "$nb"
done
echo "Listo."
