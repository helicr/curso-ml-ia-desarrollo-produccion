"""El agente como modelo de MLflow («models from code»): este archivo ES el modelo.

QUÉ ES «MODELS FROM CODE»
    Hasta MLflow 2 un modelo se guardaba «congelado» (pickle). Un agente no se congela bien (lleva un cliente de red, un proceso MCP...), así que
    MLflow 3 permite registrar el CÓDIGO: se le da la ruta de un .py que termina en `mlflow.models.set_model(...)`, y al cargarlo MLflow
    ejecuta ese archivo y recupera el objeto. Lo que cambia entre versiones del agente no son pesos, es su CONFIGURACIÓN:

        llm_modelo       qué LLM local usa (p. ej. hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF:Q4_K_M)
        prompt_version   qué versión del prompt de sistema (registro de prompts: agente-retencion-sistema)
        mcp_version      con qué versión del SDK de MCP se probó
        skills           qué skills lleva

    Esa configuración se guarda con `model_config` al registrar (ver registro.py) y es lo que se compara, se promociona (alias `champion`)
    o se deshace moviendo el alias.

Uso (después de registrarlo con registro.py):
    modelo = mlflow.pyfunc.load_model('models:/agente-retencion@champion')
    modelo.predict(pandas.DataFrame({'pregunta': ['Dame los 3 clientes con más probabilidad de volver a comprar']}))   # -> lista de respuestas

Para las pruebas: el objeto que hay dentro (`modelo.unwrap_python_model()`) admite `fabrica_llm` y `fabrica_caja`, para cambiar el LLM por uno
falso y las herramientas por funciones en memoria sin red.
"""
import contextlib
import os
import sys

import mlflow
from mlflow.pyfunc import PythonModel

try:                                    # al cargar el modelo, este archivo se ejecuta desde la copia que guardó MLflow: el proyecto debe verse
    import ia_mlops  # noqa: F401
except ModuleNotFoundError:
    sys.path.insert(0, os.environ.get('CURSO_RAIZ', os.getcwd()))


class AgenteRetencion(PythonModel):
    fabrica_llm = None          # función sin argumentos que devuelve un LLM (por defecto, Ollama con el modelo de la configuración)
    fabrica_caja = None         # función sin argumentos que devuelve una caja de herramientas (por defecto, el servidor MCP real)

    def load_context(self, context):
        """Se ejecuta una vez al cargar: lee la configuración registrada y el prompt de sistema de la versión fijada."""
        from ia_mlops.agente import skills as modulo_skills
        self.config = dict(context.model_config or {})
        self.sistema = mlflow.genai.load_prompt(f'prompts:/{self.config["prompt_nombre"]}/{self.config["prompt_version"]}').template
        todas = modulo_skills.cargar_skills()
        self.skills = {n: s for n, s in todas.items() if n in self.config.get('skills', list(todas))}

    def predict(self, context, model_input, params=None):
        from ia_mlops.agente.agente import Agente
        from ia_mlops.agente.cajas import CajaMCP
        from ia_mlops.agente.llm import ClienteOllama
        preguntas = list(model_input.iloc[:, 0]) if hasattr(model_input, 'iloc') else list(model_input)
        respuestas = []
        with contextlib.ExitStack() as pila:
            caja = self.fabrica_caja() if self.fabrica_caja else CajaMCP()
            if hasattr(caja, '__enter__'):
                caja = pila.enter_context(caja)
            for pregunta in preguntas:
                llm = self.fabrica_llm() if self.fabrica_llm else ClienteOllama(base_url=self.config.get('llm_url'), modelo=self.config.get('llm_modelo'))
                agente = Agente(llm, caja, self.skills, max_pasos=int(self.config.get('max_pasos', 6)), sistema=self.sistema)
                respuestas.append(agente.ejecutar(str(pregunta)).texto)
        return respuestas


mlflow.models.set_model(AgenteRetencion())
