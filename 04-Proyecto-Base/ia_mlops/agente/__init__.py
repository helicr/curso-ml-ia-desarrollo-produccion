"""Capa de agente del caso de retención (S5): herramientas puras y el servidor MCP que las expone.

    herramientas.py    funciones Python que devuelven diccionarios JSON (sin LLM, sin MCP): lo que el agente puede hacer
    servidor_mcp.py    el servidor MCP «mcp-retencion»: solo envuelve las funciones de herramientas.py

Para usar `herramientas` no hace falta instalar `mcp`; solo el servidor lo necesita (requirements-agente.txt).
"""
