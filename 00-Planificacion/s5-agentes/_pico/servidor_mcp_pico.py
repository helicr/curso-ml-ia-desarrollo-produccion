"""Servidor MCP mínimo. Uso: servidor_mcp_pico.py v1|v2 (v1 = FastMCP de mcp<2; v2 = MCPServer de mcp>=2)."""
import sys

if sys.argv[1] == "v1":
    from mcp.server.fastmcp import FastMCP as Server
else:
    from mcp.server.mcpserver import MCPServer as Server

mcp = Server("mcp-retencion-pico")


@mcp.tool()
def lista_del_dia(n: int = 5) -> list[dict]:
    """Devuelve los n clientes con mayor riesgo de abandono hoy."""
    return [{"cliente_id": 12670 + i, "prob": round(0.9 - 0.05 * i, 3)} for i in range(n)]


@mcp.tool()
def version_en_produccion() -> str:
    """Versión del modelo en producción."""
    return "retencion-v7"


@mcp.resource("referencia://modelo")
def referencia() -> str:
    """Ficha del modelo de referencia."""
    return '{"modelo": "retencion", "auc": 0.77}'


if __name__ == "__main__":
    mcp.run(transport="stdio")
