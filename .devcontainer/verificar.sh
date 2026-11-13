#!/usr/bin/env bash
# Comprobación del Codespace del curso. Ejecutar: bash .devcontainer/verificar.sh
fallos=0
comprobar() { # nombre, comando...
  local n="$1"; shift
  if salida="$("$@" 2>&1)"; then printf '[OK   ] %-12s %s\n' "$n" "$(echo "$salida" | head -1)"
  else printf '[FALLA] %-12s %s\n' "$n" "$(echo "$salida" | head -1)"; fallos=$((fallos+1)); fi
}
comprobar docker   docker version --format 'cliente {{.Client.Version}} · servidor {{.Server.Version}}'
comprobar hello    docker run --rm hello-world
comprobar kind     kind version
comprobar kubectl  kubectl version --client
comprobar python   conda run -n env-ia-mlops python --version
echo "Fallos: $fallos"
exit $fallos
