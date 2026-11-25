"""Explica en español la predicción de un cliente con un LLM GESTIONADO (Gemini en Vertex AI), sin claves: usa la sesión de Cloud Shell.

Es lo mismo que hace el agente de S5 con un LLM local (Ollama), pero con el modelo alojado en Google:
  1. El MODELO (regresión logística de 04-Proyecto-Base) calcula la probabilidad y cuánto pesa cada variable. Los números salen de él, no del LLM.
  2. El LLM solo REDACTA la explicación a partir de esos números (temperatura 0, instrucción de no inventar).
  3. Se comprueba que la probabilidad aparece en el texto.

Uso (Cloud Shell, con el entorno del proyecto):
  python explicar_prediccion.py --proyecto RUTA/04-Proyecto-Base --clientes ../clientes_ejemplo.json --cliente activo
SDK: google-genai (el recomendado hoy para Gemini en Vertex AI): https://docs.cloud.google.com/vertex-ai/generative-ai/docs/sdks/overview
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

INSTRUCCION = (
    'Eres un analista de retención de clientes. Explicas en español claro, para una persona de marketing sin formación técnica, '
    'una predicción de un modelo. Usa SOLO los datos que te doy: no inventes cifras, causas ni hechos sobre el cliente. '
    'Si un dato no está, dilo. Máximo 120 palabras. Cita la probabilidad como porcentaje y recuerda que dice qué empuja la '
    'probabilidad, no por qué compra la persona.'
)


def pesos_exactos(modelo, variables, valores):
    """Peso en logit de cada variable (coeficiente x valor ya imputado, con log1p y estandarizado). Suma + intercepto = logit del modelo."""
    import pandas as pd
    fila = pd.DataFrame([valores], columns=variables).astype(float)
    z = modelo[:-1].transform(fila)[0]
    coef = modelo.named_steps['modelo'].coef_[0]
    intercepto = float(modelo.named_steps['modelo'].intercept_[0])
    pesos = [float(c * v) for c, v in zip(coef, z)]
    logit = intercepto + sum(pesos)
    return pesos, 1.0 / (1.0 + math.exp(-logit))


def cita_la_probabilidad(texto, prob):
    """True si el texto escribe la probabilidad en % con 0, 1 o 2 decimales y coma o punto (83, 82,8, 82.8, 82,79, 82.79...).

    Se busca el número entero (sin pegarse a otros dígitos ni a un punto), así «250.83» o «2083» no cuentan como «83».
    Los asteriscos de Markdown (**82.79%**) no estorban.
    """
    plano = texto.replace(',', '.')
    for decimales in (0, 1, 2):
        cifra = re.escape(f'{prob * 100:.{decimales}f}')
        if re.search(rf'(?<![\d.]){cifra}(?!\d)', plano):
            return True
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--proyecto', required=True, help='carpeta 04-Proyecto-Base (con models/modelo.joblib)')
    ap.add_argument('--clientes', required=True)
    ap.add_argument('--cliente', default='activo')
    ap.add_argument('--id-proyecto-gcp', required=True)
    ap.add_argument('--ubicacion', default='global')
    ap.add_argument('--modelo-llm', default='gemini-3.1-flash-lite')
    ap.add_argument('--n', type=int, default=5, help='cuántas variables se le cuentan al LLM')
    a = ap.parse_args()

    proyecto = Path(a.proyecto).resolve()
    sys.path.insert(0, str(proyecto))
    import joblib
    from ia_mlops import config

    modelo = joblib.load(proyecto / 'models' / 'modelo.joblib')
    meta = json.loads((proyecto / 'models' / 'metadatos.json').read_text(encoding='utf-8'))
    variables = meta['variables']
    cliente = json.loads(Path(a.clientes).read_text(encoding='utf-8'))[a.cliente]

    pesos, prob = pesos_exactos(modelo, variables, [cliente[v] for v in variables])
    import pandas as pd
    prob_modelo = float(modelo.predict_proba(pd.DataFrame([[cliente[v] for v in variables]], columns=variables).astype(float))[0, 1])
    assert abs(prob - prob_modelo) < 1e-9, 'la descomposición no reproduce la probabilidad del modelo'
    segmento = next(s for s in config.SEGMENTOS_RECOMPRA if prob >= s['desde'])
    top = sorted(zip(variables, pesos), key=lambda t: -abs(t[1]))[:a.n]
    hechos = {
        'cliente': a.cliente, 'probabilidad_compra_90_dias': round(prob, 4), 'tramo': segmento['segmento'],
        'recomendacion_de_negocio': segmento['recomendacion'],
        'variables_que_mas_pesan': [{'variable': v, 'valor': cliente[v], 'efecto': 'sube' if p > 0 else 'baja', 'peso_logit': round(p, 3)} for v, p in top],
        'nota': 'peso_logit = coeficiente x valor transformado; positivo empuja la probabilidad hacia arriba.',
    }
    print('Hechos calculados por el MODELO (esto es lo único que ve el LLM):')
    print(json.dumps(hechos, indent=2, ensure_ascii=False))

    from google import genai
    from google.genai import types
    cliente_llm = genai.Client(vertexai=True, project=a.id_proyecto_gcp, location=a.ubicacion)
    print(f'\nLlamando a {a.modelo_llm} en Vertex AI (ubicación: {a.ubicacion})...')
    try:
        r = cliente_llm.models.generate_content(
            model=a.modelo_llm,
            contents='Explica esta predicción:\n' + json.dumps(hechos, ensure_ascii=False),
            config=types.GenerateContentConfig(system_instruction=INSTRUCCION, temperature=0, max_output_tokens=1024),
        )
    except Exception as e:      # noqa: BLE001 - se explica en claro qué mirar
        print(f'\nERROR al llamar a Gemini: {type(e).__name__}: {e}', file=sys.stderr)
        print('Mira "Si falla" en el README: modelo no encontrado en esa ubicación, API sin habilitar o falta de permisos.', file=sys.stderr)
        return 1
    texto = (r.text or '').strip()
    print('\nExplicación del LLM:\n' + texto)
    if r.usage_metadata:
        print(f'\nTokens: entrada={r.usage_metadata.prompt_token_count} salida={r.usage_metadata.candidates_token_count}')

    if not cita_la_probabilidad(texto, prob):
        print(f'\nAVISO: el texto no cita el {prob * 100:.1f} % del modelo. Un LLM puede redactar mal: revisa la explicación antes de usarla.')
        return 2
    print(f'\nOK: la explicación cita la probabilidad del modelo ({prob * 100:.1f} %).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
