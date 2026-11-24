"""Verifica las APIs de MLflow 3.18 para GenAI contra Ollama. Cada paso se anota como OK o FALLA con el error."""
import json
import os
import time
import traceback
from pathlib import Path

PICO = Path(__file__).parent
os.environ.setdefault("NO_PROXY", "127.0.0.1,localhost")
os.environ["MLFLOW_ENABLE_ASYNC_TRACE_LOGGING"] = "false"  # sin esto, get_trace devuelve None justo tras la llamada (envío asíncrono)
import mlflow
import openai

mlflow.set_tracking_uri(f"sqlite:///{(PICO / 'mlflow.db').as_posix()}")
os.environ["MLFLOW_TRACKING_URI"] = mlflow.get_tracking_uri()
mlflow.set_experiment("pico-s5")
print("mlflow", mlflow.__version__, "openai", openai.__version__)

MODELO = "hf.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF:Q4_K_M"
cli = openai.OpenAI(base_url="http://127.0.0.1:11435/v1", api_key="ollama")
R = {}


def paso(nombre):
    def deco(f):
        t = time.perf_counter()
        try:
            v = f()
            R[nombre] = {"ok": True, "detalle": v, "s": round(time.perf_counter() - t, 2)}
            print("OK   ", nombre, "->", str(v)[:300])
        except Exception as e:
            R[nombre] = {"ok": False, "error": f"{type(e).__name__}: {str(e)[:400]}", "s": round(time.perf_counter() - t, 2)}
            print("FALLA", nombre, "->", R[nombre]["error"])
            traceback.print_exc()
        return f
    return deco


@paso("1a trace manual: @mlflow.trace + mlflow.start_span")
def _():
    @mlflow.trace(name="agente", span_type="AGENT")
    def agente(q):
        with mlflow.start_span(name="herramienta_falsa", span_type="TOOL") as sp:
            sp.set_inputs({"n": 5})
            sp.set_outputs({"clientes": [1, 2]})
        return "ok " + q
    agente("hola")
    tr = mlflow.get_last_active_trace_id()
    t = mlflow.get_trace(tr)
    return {"trace_id": tr, "spans": [s.name for s in t.data.spans]}


@paso("1b autolog openai: mlflow.openai.autolog()")
def _():
    mlflow.openai.autolog()
    r = cli.chat.completions.create(model=MODELO, temperature=0, seed=42,
                                    messages=[{"role": "user", "content": "Di hola en una palabra."}])
    tid = mlflow.get_last_active_trace_id()
    t = mlflow.get_trace(tid)
    sp = t.data.spans[0]
    return {"respuesta": r.choices[0].message.content, "spans": [s.name for s in t.data.spans],
            "span_type": str(sp.span_type), "atributos": list(sp.attributes.keys())[:8]}


@paso("1c autolog openai con tool_calls (ver que la traza guarda tools)")
def _():
    tools = [{"type": "function", "function": {"name": "version_en_produccion", "description": "Versión en producción", "parameters": {"type": "object", "properties": {}}}}]
    r = cli.chat.completions.create(model=MODELO, temperature=0, seed=42, tools=tools,
                                    messages=[{"role": "user", "content": "¿Qué versión hay en producción?"}])
    tid = mlflow.get_last_active_trace_id()
    t = mlflow.get_trace(tid)
    return {"tool_calls": [c.function.name for c in (r.choices[0].message.tool_calls or [])], "n_spans": len(t.data.spans)}


@paso("1d buscar trazas: mlflow.search_traces")
def _():
    df = mlflow.search_traces(max_results=10)
    return {"filas": len(df), "columnas": list(df.columns)[:10]}


@paso("2a prompts: mlflow.genai.register_prompt")
def _():
    p = mlflow.genai.register_prompt(name="prompt-agente-retencion",
                                     template="Eres el asistente de retención. Pregunta: {{pregunta}}",
                                     commit_message="v1")
    p2 = mlflow.genai.register_prompt(name="prompt-agente-retencion",
                                      template="Eres el asistente de retención. Responde en una frase. Pregunta: {{pregunta}}",
                                      commit_message="v2")
    return {"v1": p.version, "v2": p2.version}


@paso("2b prompts: mlflow.genai.set_prompt_alias + load_prompt por alias")
def _():
    mlflow.genai.set_prompt_alias("prompt-agente-retencion", alias="produccion", version=1)
    p = mlflow.genai.load_prompt("prompts:/prompt-agente-retencion@produccion")
    a = (p.version, p.format(pregunta="¿hola?"))
    mlflow.genai.set_prompt_alias("prompt-agente-retencion", alias="produccion", version=2)  # «rollback/promoción» = mover alias
    p = mlflow.genai.load_prompt("prompts:/prompt-agente-retencion@produccion")
    return {"antes": a, "despues": (p.version, p.format(pregunta="¿hola?"))}


@paso("2c prompts: mlflow.genai.search_prompts / delete_prompt_alias")
def _():
    n = [x.name for x in mlflow.genai.search_prompts()]
    mlflow.genai.delete_prompt_alias("prompt-agente-retencion", alias="produccion")
    mlflow.genai.set_prompt_alias("prompt-agente-retencion", alias="produccion", version=2)
    return {"prompts": n}


@paso("3 evaluación: mlflow.genai.evaluate con @scorer propio")
def _():
    from mlflow.genai.scorers import scorer
    from mlflow.entities import Feedback

    @scorer
    def herramienta_correcta(outputs, expectations):
        return Feedback(value=outputs.get("herramienta") == expectations["herramienta"],
                        rationale=f"usó {outputs.get('herramienta')}")

    @scorer
    def sin_inventar(outputs):
        return not any(ch.isdigit() for ch in outputs.get("texto", ""))

    tools = [{"type": "function", "function": {"name": "version_en_produccion", "description": "Versión del modelo en producción", "parameters": {"type": "object", "properties": {}}}},
             {"type": "function", "function": {"name": "lista_del_dia", "description": "Clientes del día", "parameters": {"type": "object", "properties": {"n": {"type": "integer"}}, "required": ["n"]}}}]

    def predict_fn(pregunta):
        r = cli.chat.completions.create(model=MODELO, temperature=0, seed=42, tools=tools,
                                        messages=[{"role": "user", "content": pregunta}])
        m = r.choices[0].message
        return {"herramienta": m.tool_calls[0].function.name if m.tool_calls else None, "texto": m.content or ""}

    datos = [
        {"inputs": {"pregunta": "¿Qué versión del modelo hay en producción?"}, "expectations": {"herramienta": "version_en_produccion"}},
        {"inputs": {"pregunta": "Dame los 5 clientes a los que llamar hoy."}, "expectations": {"herramienta": "lista_del_dia"}},
    ]
    res = mlflow.genai.evaluate(data=datos, predict_fn=predict_fn, scorers=[herramienta_correcta, sin_inventar])
    return {"run_id": res.run_id, "metricas": res.metrics}


@paso("3b evaluación: scorer integrado (mlflow.genai.scorers.Safety) sin juez -> se espera error de juez")
def _():
    from mlflow.genai.scorers import Safety
    return str(Safety)


@paso("4a models from code: mlflow.pyfunc.log_model(python_model='agente_from_code.py')")
def _():
    import pandas as pd
    ruta = str(PICO / "agente_from_code.py")
    with mlflow.start_run(run_name="registro-agente"):
        info = mlflow.pyfunc.log_model(name="agente", python_model=ruta,
                                       registered_model_name="agente-retencion",
                                       input_example=pd.DataFrame({"pregunta": ["hola"]}))
    return {"model_uri": info.model_uri, "model_id": getattr(info, "model_id", None)}


@paso("4b alias: MlflowClient.set_registered_model_alias + load_model por alias + predict")
def _():
    from mlflow import MlflowClient
    c = MlflowClient()
    vs = c.search_model_versions("name='agente-retencion'")
    v = max(int(x.version) for x in vs)
    c.set_registered_model_alias("agente-retencion", "champion", v)
    m = mlflow.pyfunc.load_model("models:/agente-retencion@champion")
    import pandas as pd
    out = m.predict(pd.DataFrame({"pregunta": ["Di hola en una frase."]}))
    return {"version": v, "salida": out}


@paso("4c trazas del predict del agente cargado (autolog activo)")
def _():
    t = mlflow.get_trace(mlflow.get_last_active_trace_id())
    return {"spans": [s.name for s in t.data.spans]}


(PICO / "salidas" / "mlflow_resultados.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
print("resumen:", {k: v["ok"] for k, v in R.items()})
