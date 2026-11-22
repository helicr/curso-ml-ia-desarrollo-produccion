"""Escribe en Markdown (para $GITHUB_STEP_SUMMARY) el resultado de una evaluación del agente: métricas, por categoría y decisión.

Solo biblioteca estándar. Las cifras salen del informe de `evaluacion evaluar --json`, de la referencia y de la decisión de `evaluacion comparar --json`:
ninguna está escrita a mano aquí.

    python resumen_evaluacion.py --informe evaluacion.json [--referencia agentes/referencia-agente.json] [--decision decision.json]
"""
import argparse
import json
import sys
from pathlib import Path

ORDEN = ('acierto_herramienta', 'acierto_argumentos', 'sin_inventar', 'comprobaciones_ok', 'trampas_superadas', 'respuestas_correctas')
TITULOS = {'igual': 'IGUAL · nada que publicar', 'aceptada': 'ACEPTADA · dentro de la tolerancia', 'rechazada': 'RECHAZADA · no se publica'}


def _pct(x):
    return 'sin dato' if x is None else f'{100 * x:.0f} %'


def _num(x, unidad=''):
    return 'sin dato' if x is None else f'{x:g}{unidad}'


def markdown(informe, referencia=None, decision=None):
    m, c = informe['metricas'], informe['conteos']
    L = []
    if decision:
        L += [f"## Evaluación del agente · {TITULOS.get(decision['decision'], decision['decision'])}\n", f"{decision['motivo']}\n"]
    else:
        L += ['## Evaluación del agente\n']
    L += [f"LLM: `{informe['llm']}` · huella del agente `{informe['huella_agente']}` · {c['preguntas']} preguntas ({c['omitidas']} omitidas)\n"]
    cab = '| métrica | esta evaluación |' + (' referencia | diferencia |' if referencia else '')
    L += [cab, '|---|---|' + ('---|---|' if referencia else '')]
    for k in ORDEN:
        fila = f'| {k} | {_pct(m.get(k))} |'
        if referencia:
            r = referencia['metricas'].get(k)
            d = None if r is None or m.get(k) is None else m[k] - r
            fila += f" {_pct(r)} | {'sin dato' if d is None else f'{100 * d:+.0f} puntos'} |"
        L.append(fila)
    L += [f"| latencia p50 / p95 | {_num(m.get('latencia_p50_s'), ' s')} / {_num(m.get('latencia_p95_s'), ' s')} |" + (
        f" {_num(referencia['metricas'].get('latencia_p50_s'), ' s')} / {_num(referencia['metricas'].get('latencia_p95_s'), ' s')} | |" if referencia else ''),
          f"| cifras inventadas | {m.get('cifras_inventadas', 'sin dato')} |" + (f" {referencia['metricas'].get('cifras_inventadas', 'sin dato')} | |" if referencia else ''), '']
    L += ['### Por categoría\n', '| categoría | preguntas | correctas | acierto de herramienta | sin inventar | fallan |', '|---|---|---|---|---|---|']
    for cat, d in informe['por_categoria'].items():
        L.append(f"| {cat} | {d['preguntas']} | {d['correctas']} | {_pct(d['acierto_herramienta'])} | {_pct(d['sin_inventar'])} | {', '.join(d['fallidas']) or '-'} |")
    if informe.get('criticas_falladas'):
        L += ['', f"**Preguntas de seguridad falladas: {', '.join(informe['criticas_falladas'])}.** Se rechaza siempre, sin tolerancia."]
    if decision and decision.get('tolerancia') is not None:
        L += ['', f"Tolerancia de la puerta: {decision['tolerancia']:g} (una negativa es una exigencia de mejora)."]
    return '\n'.join(L) + '\n'


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--informe', required=True)
    ap.add_argument('--referencia')
    ap.add_argument('--decision')
    a = ap.parse_args(argv)
    try:
        informe = json.loads(Path(a.informe).read_text(encoding='utf-8'))
        referencia = json.loads(Path(a.referencia).read_text(encoding='utf-8')) if a.referencia else None
        decision = json.loads(Path(a.decision).read_text(encoding='utf-8')) if a.decision and Path(a.decision).exists() else None
        sys.stdout.reconfigure(encoding='utf-8')
        print(markdown(informe, referencia, decision))
    except (OSError, KeyError, ValueError) as e:
        print(f'Error: {e}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
