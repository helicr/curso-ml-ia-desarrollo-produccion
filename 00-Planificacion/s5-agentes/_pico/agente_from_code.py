"""Agente mínimo para el registro como «models from code» (MLflow pyfunc)."""
import mlflow
from mlflow.pyfunc import PythonModel


class AgentePico(PythonModel):
    def load_context(self, context):
        import openai
        self.cli = openai.OpenAI(base_url="http://127.0.0.1:11435/v1", api_key="ollama")
        self.modelo = "hf.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF:Q4_K_M"

    def predict(self, context, model_input, params=None):
        if hasattr(model_input, "iloc"):
            preguntas = list(model_input.iloc[:, 0])
        else:
            preguntas = list(model_input)
        out = []
        for q in preguntas:
            r = self.cli.chat.completions.create(
                model=self.modelo, temperature=0, seed=42,
                messages=[{"role": "system", "content": "Responde en una frase en español."},
                          {"role": "user", "content": str(q)}])
            out.append(r.choices[0].message.content)
        return out


mlflow.models.set_model(AgentePico())
