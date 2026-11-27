#!/usr/bin/env bash
# Ejecuta los siete cuadernos en orden y deja las salidas guardadas en los .ipynb.
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
export RAG_MODO_RAPIDO="${RAG_MODO_RAPIDO:-1}"
TIMEOUT_LARGO="${TIMEOUT_LARGO:-2400}"
for nb in \
  notebooks/00-introduccion-y-setup.ipynb \
  notebooks/01-embeddings-y-similitud.ipynb \
  notebooks/02-chunking-e-indexado.ipynb \
  notebooks/03-recuperacion-y-busqueda.ipynb \
  notebooks/04-generacion-con-llm-local.ipynb \
  notebooks/05-pipeline-completo-y-evaluacion.ipynb \
  notebooks/06-ejercicios.ipynb
do
  echo "=== $nb ==="
  "$PY" -m jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout="$TIMEOUT_LARGO" \
    --ExecutePreprocessor.kernel_name=python3 \
    "$nb"
done
echo "Listo."
