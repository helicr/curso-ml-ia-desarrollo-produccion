#!/bin/sh
# Descarga el modelo del asistente DENTRO del contenedor de Ollama (compose-agente.yaml, perfil «ollama»). Una vez; queda en el volumen.
# El nombre hf.co/... baja por el proxy de la oficina; el corto «qwen2.5:3b» no. Desde 04-Proyecto-Base:   sh deploy/docker/ollama-pull.sh
set -e
MODELO="${1:-hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF:Q4_K_M}"
docker compose -f deploy/docker/compose-agente.yaml --profile ollama up -d ollama
docker compose -f deploy/docker/compose-agente.yaml --profile ollama exec ollama ollama pull "$MODELO"
docker compose -f deploy/docker/compose-agente.yaml --profile ollama exec ollama ollama list
