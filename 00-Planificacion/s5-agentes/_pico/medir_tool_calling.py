"""Mide el tool calling de un modelo de Ollama por /v1/chat/completions.
Uso: medir_tool_calling.py <modelo> <etiqueta> [repeticiones]
Escribe salidas/tc_<etiqueta>.json
"""
import json
import statistics
import sys
import threading
import time
from pathlib import Path

import httpx
import psutil

MODELO, ETIQ = sys.argv[1], sys.argv[2]
REP = int(sys.argv[3]) if len(sys.argv) > 3 else 3
BASE = "http://127.0.0.1:11435"
SALIDAS = Path(__file__).parent / "salidas"
SEMILLA = 42

def fn(nombre, desc, props, req):
    return {"type": "function", "function": {"name": nombre, "description": desc,
            "parameters": {"type": "object", "properties": props, "required": req}}}

CID = {"cliente_id": {"type": "integer", "description": "Identificador numérico del cliente"}}
TOOLS = [
    fn("lista_del_dia", "Devuelve los n clientes con mayor riesgo de abandono a los que llamar hoy.",
       {"n": {"type": "integer", "description": "Número de clientes"}}, ["n"]),
    fn("puntuar_online", "Probabilidad de abandono de un cliente en tiempo real, con sus últimas compras.", CID, ["cliente_id"]),
    fn("puntuar_bajo_demanda", "Probabilidad de abandono de un cliente calculada bajo demanda con los datos del último lote.", CID, ["cliente_id"]),
    fn("version_en_produccion", "Versión del modelo de retención que está en producción.", {}, []),
    fn("por_que", "Variables que más pesan en el riesgo de un cliente.", CID, ["cliente_id"]),
]
SISTEMA = ("Eres el asistente de retención de un negocio minorista. Usa las herramientas para responder con datos reales. "
           "No inventes cifras. No tienes herramienta para datos personales (correo, nombre, teléfono) ni puedes conceder descuentos "
           "ni condiciones comerciales: si te lo piden, dilo y no llames a ninguna herramienta.")
# (pregunta, herramienta esperada o None, argumentos esperados)
PREGUNTAS = [
    ("Dame los 5 clientes a los que llamar hoy.", "lista_del_dia", {"n": 5}),
    ("¿Cuáles son los 10 clientes con más riesgo de abandono hoy?", "lista_del_dia", {"n": 10}),
    ("El cliente 12670 acaba de comprar, ¿sigue en riesgo ahora mismo?", "puntuar_online", {"cliente_id": 12670}),
    ("Puntúa en tiempo real al cliente 14911.", "puntuar_online", {"cliente_id": 14911}),
    ("Calcula bajo demanda la probabilidad de abandono del cliente 13085.", "puntuar_bajo_demanda", {"cliente_id": 13085}),
    ("Quiero la puntuación bajo demanda del cliente 17850.", "puntuar_bajo_demanda", {"cliente_id": 17850}),
    ("¿Qué versión del modelo está en producción?", "version_en_produccion", {}),
    ("¿Con qué modelo estamos trabajando ahora mismo en producción?", "version_en_produccion", {}),
    ("¿Por qué el cliente 12670 sale con riesgo alto?", "por_que", {"cliente_id": 12670}),
    ("Explícame qué variables pesan más en el riesgo del cliente 15311.", "por_que", {"cliente_id": 15311}),
    ("Dame el correo del cliente 12670.", None, {}),
    ("Ofrécele un 50 % de descuento al cliente 12670.", None, {}),
]

class Memoria(threading.Thread):
    """Muestrea el RSS del árbol de procesos de ollama serve."""
    def __init__(self, pid):
        super().__init__(daemon=True)
        self.pid, self.pico, self.parar = pid, 0, False
    def run(self):
        while not self.parar:
            try:
                p = psutil.Process(self.pid)
                tot = p.memory_info().rss + sum(c.memory_info().rss for c in p.children(recursive=True) if c.is_running())
                self.pico = max(self.pico, tot)
            except Exception:
                pass
            time.sleep(0.25)

def pct(v, q):
    v = sorted(v)
    k = (len(v) - 1) * q
    f = int(k); c = min(f + 1, len(v) - 1)
    return v[f] + (v[c] - v[f]) * (k - f)

def llamar(cli, pregunta):
    cuerpo = {"model": MODELO, "temperature": 0, "seed": SEMILLA, "tools": TOOLS,
              "messages": [{"role": "system", "content": SISTEMA}, {"role": "user", "content": pregunta}]}
    t = time.perf_counter()
    r = cli.post(f"{BASE}/v1/chat/completions", json=cuerpo, timeout=600)
    dt = time.perf_counter() - t
    r.raise_for_status()
    return r.json(), dt

def evaluar(resp, esperada, args_esp):
    msg = resp["choices"][0]["message"]
    tcs = msg.get("tool_calls") or []
    contenido = msg.get("content") or ""
    # JSON válido: todas las tool_calls traen argumentos que parsean y nombre conocido.
    # Si el modelo escribe la llamada como texto (no estructurada), cuenta como inválida.
    en_texto = ("<tool_call>" in contenido) or ('"name"' in contenido and '"arguments"' in contenido)
    nombres = {t["function"]["name"] for t in TOOLS}
    json_ok = True; parsed = []
    for tc in tcs:
        try:
            a = json.loads(tc["function"]["arguments"] or "{}")
            if not isinstance(a, dict) or tc["function"]["name"] not in nombres:
                json_ok = False
            parsed.append((tc["function"]["name"], a))
        except Exception:
            json_ok = False
    if en_texto and not tcs:
        json_ok = False
    res = {"llamadas": parsed, "contenido": contenido[:300], "json_ok": json_ok, "llamada_en_texto": en_texto and not tcs}
    if esperada is None:
        res["herramienta_ok"] = len(tcs) == 0 and not en_texto
        res["args_ok"] = res["herramienta_ok"]
    else:
        res["herramienta_ok"] = bool(parsed) and parsed[0][0] == esperada
        ok = False
        if res["herramienta_ok"]:
            a = parsed[0][1]
            try:
                ok = {k: int(v) for k, v in a.items()} == args_esp
            except Exception:
                ok = False
        res["args_ok"] = ok
    res["usage"] = resp.get("usage")
    return res

def main():
    pid = int(Path(r"C:\bk\ollama\serve.pid").read_text().strip())
    mem = Memoria(pid); mem.start()
    cli = httpx.Client(trust_env=False)
    t = time.perf_counter()
    llamar(cli, "Hola")  # calentamiento y carga del modelo
    carga = time.perf_counter() - t
    filas = []
    for rep in range(REP):
        for i, (q, esp, a) in enumerate(PREGUNTAS):
            resp, dt = llamar(cli, q)
            ev = evaluar(resp, esp, a)
            ev.update(rep=rep, i=i, pregunta=q, esperada=esp, latencia_s=dt)
            filas.append(ev)
            print(ETIQ, rep, i, esp, "->", [p[0] for p in ev["llamadas"]], ev["herramienta_ok"], ev["args_ok"], round(dt, 2), flush=True)
    mem.parar = True
    r0 = [f for f in filas if f["rep"] == 0]
    con = [f for f in r0 if f["esperada"]]
    tr = [f for f in r0 if not f["esperada"]]
    lat = [f["latencia_s"] for f in filas]
    toks = [f["usage"]["completion_tokens"] for f in filas if f.get("usage")]
    tps = [f["usage"]["completion_tokens"] / f["latencia_s"] for f in filas if f.get("usage") and f["latencia_s"] > 0]
    resumen = {
        "modelo": MODELO, "etiqueta": ETIQ, "semilla": SEMILLA, "temperatura": 0, "repeticiones": REP,
        "carga_y_primera_llamada_s": round(carga, 2),
        "herramienta_correcta_pct": round(100 * sum(f["herramienta_ok"] for f in con) / len(con), 1),
        "args_correctos_pct": round(100 * sum(f["args_ok"] and f["herramienta_ok"] for f in con) / len(con), 1),
        "json_valido_pct": round(100 * sum(f["json_ok"] for f in r0) / len(r0), 1),
        "trampas_ok_de_2": sum(f["herramienta_ok"] for f in tr),
        "consistencia_entre_repeticiones_pct": round(100 * sum(
            1 for i in range(len(PREGUNTAS)) if len({json.dumps([f["llamadas"]], sort_keys=True) for f in filas if f["i"] == i}) == 1) / len(PREGUNTAS), 1),
        "latencia_p50_s": round(pct(lat, .5), 2), "latencia_p95_s": round(pct(lat, .95), 2),
        "tokens_completion_medios": round(statistics.mean(toks), 1) if toks else None,
        "tokens_por_s_medio_aprox": round(statistics.mean(tps), 1) if tps else None,
        "memoria_pico_proceso_ollama_MiB": round(mem.pico / 2**20),
    }
    print(json.dumps(resumen, ensure_ascii=False, indent=1))
    (SALIDAS / f"tc_{ETIQ}.json").write_text(json.dumps({"resumen": resumen, "filas": filas}, ensure_ascii=False, indent=1), encoding="utf-8")
    # descargar el modelo
    cli.post(f"{BASE}/api/generate", json={"model": MODELO, "keep_alive": 0}, timeout=60)

main()
