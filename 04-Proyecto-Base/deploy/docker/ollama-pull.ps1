# Descarga el modelo del asistente DENTRO del contenedor de Ollama (compose-agente.yaml, perfil «ollama»). Una vez; queda en el volumen.
# El nombre hf.co/... baja por el proxy de la oficina; el corto «qwen2.5:3b» no. Desde 04-Proyecto-Base:   .\deploy\docker\ollama-pull.ps1
param([string]$Modelo = 'hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF:Q4_K_M')
$ErrorActionPreference = 'Stop'
$compose = 'deploy/docker/compose-agente.yaml'
docker compose -f $compose --profile ollama up -d ollama
docker compose -f $compose --profile ollama exec ollama ollama pull $Modelo
docker compose -f $compose --profile ollama exec ollama ollama list
