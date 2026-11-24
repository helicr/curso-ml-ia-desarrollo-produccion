"""Cliente MCP por stdio. Uso: cliente_mcp_pico.py v1|v2"""
import asyncio
import sys
import time
import importlib.metadata as md

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

modo = sys.argv[1]
ruta = r"C:\bk\HC-Cursos\curso-ml-ia-desarrollo-produccion\00-Planificacion\s5-agentes\_pico\servidor_mcp_pico.py"


async def main():
    t0 = time.perf_counter()
    params = StdioServerParameters(command=sys.executable, args=["-I", ruta, modo])
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            t_init = time.perf_counter() - t0
            tools = await s.list_tools()
            print("mcp", md.version("mcp"), "modo", modo)
            print("arranque+initialize_s", round(t_init, 2))
            print("herramientas", [t.name for t in tools.tools])
            t0_ = tools.tools[0]
            print("schema lista_del_dia", getattr(t0_, "inputSchema", None) or getattr(t0_, "input_schema", None))
            t1 = time.perf_counter()
            res = await s.call_tool("lista_del_dia", {"n": 2})
            print("call_tool_s", round(time.perf_counter() - t1, 3))
            print("resultado", [c.text for c in res.content], "structured:", getattr(res, "structuredContent", None) or getattr(res, "structured_content", None))
            res = await s.call_tool("version_en_produccion", {})
            print("version", [c.text for c in res.content])
            rs = await s.list_resources()
            print("recursos", [str(x.uri) for x in rs.resources])
            rec = await s.read_resource("referencia://modelo")
            print("recurso", rec.contents[0].text)


asyncio.run(main())
