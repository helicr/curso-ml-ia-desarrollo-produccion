"""Historial de versiones del agente (agentes/historial-agente.json): quién está «en produccion», quién fue «anterior» o «retirada».

Es el equivalente, para el agente, de models/historial_versiones.json del modelo de S4 (que mantiene `ia_mlops.produccion historial`).
El agente aún no tiene esa orden en ia_mlops, así que la lógica vive aquí, SOLO con la biblioteca estándar (por eso los trabajos que abren
el pull request no necesitan instalar nada) y con pruebas en pruebas/test_workflows_agente.py.

    nueva     tras una versión aceptada: la que estaba en producción pasa a «anterior» y la nueva entra como «produccion»
    rollback  al volver atrás: la restaurada pasa a «produccion» y la que se deja, a «retirada»  (no se borra nada)
    prompt-de qué prompt llevaba una versión («actual» = el de agente.py; «nuevo» = prompts/sistema-v2.txt): lo usa el rollback

CLI:
    python historial_agente.py nueva --historial H --anterior FICHA_ANTERIOR --nueva FICHA_NUEVA [--prompt actual|nuevo] [--ejecucion URL]
    python historial_agente.py rollback --historial H --restaurada FICHA --retirada FICHA [--ejecucion URL]
    python historial_agente.py prompt-de --historial H --version N
Las «fichas» son archivos agentes/referencia-agente.json (la salida de `evaluacion crear-referencia`).
"""
import argparse
import json
import sys
from pathlib import Path

ESQUEMA = 1
METRICAS = ('acierto_herramienta', 'sin_inventar', 'respuestas_correctas')
PROMPTS = ('actual', 'nuevo')


def etiqueta_imagen(ficha):
    """interfaz-agente:v<N>-<huella del agente>: la misma etiqueta con la que agente-nueva-version.yml publica en GHCR."""
    return f"interfaz-agente:v{ficha['version']}-{ficha['huella_agente']}"


def entrada(ficha, estado, prompt='actual', ejecucion=None):
    return {'version': int(ficha['version']), 'estado': estado, 'etiqueta_imagen': etiqueta_imagen(ficha), 'huella_agente': ficha['huella_agente'],
            'llm': ficha.get('llm'), 'prompt': prompt, 'metricas': {m: ficha['metricas'].get(m) for m in METRICAS},
            'generado_en': ficha.get('generado_en'), 'ejecucion': ejecucion}


def leer(ruta):
    ruta = Path(ruta)
    if not ruta.exists():
        return {'esquema': ESQUEMA, 'versiones': []}
    d = json.loads(ruta.read_text(encoding='utf-8'))
    if d.get('esquema') != ESQUEMA or not isinstance(d.get('versiones'), list):
        raise ValueError(f'{ruta} no tiene el esquema {ESQUEMA} del historial del agente.')
    return d


def escribir(historial, ruta):
    historial['versiones'] = sorted(historial['versiones'], key=lambda e: e['version'])
    Path(ruta).write_text(json.dumps(historial, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')


def _buscar(historial, version):
    return next((e for e in historial['versiones'] if e['version'] == int(version)), None)


def _poner(historial, ficha, estado, **extra):
    """Pone la versión de la ficha en ese estado; si no estaba en el historial, la crea."""
    e = _buscar(historial, ficha['version'])
    if e is None:
        historial['versiones'].append(entrada(ficha, estado, **extra))
    else:
        e['estado'] = estado
        e.update({k: v for k, v in extra.items() if v is not None})
    return historial


def registrar_nueva(historial, anterior, nueva, prompt='actual', ejecucion=None):
    for e in historial['versiones']:
        if e['estado'] == 'produccion':
            e['estado'] = 'anterior'
    if anterior is not None and _buscar(historial, anterior['version']) is None:
        historial['versiones'].append(entrada(anterior, 'anterior'))
    antigua = _buscar(historial, nueva['version'])
    if antigua is not None:                                   # repetir la misma versión no la duplica: se sustituye
        historial['versiones'].remove(antigua)
    historial['versiones'].append(entrada(nueva, 'produccion', prompt=prompt, ejecucion=ejecucion))
    return historial


def registrar_rollback(historial, restaurada, retirada, ejecucion=None):
    for e in historial['versiones']:
        if e['estado'] == 'produccion':
            e['estado'] = 'retirada'
    _poner(historial, retirada, 'retirada')
    _poner(historial, restaurada, 'produccion', ejecucion=ejecucion)
    return historial


def prompt_de(historial, version):
    e = _buscar(historial, version)
    return (e or {}).get('prompt') or 'actual'


def _ficha(ruta):
    return json.loads(Path(ruta).read_text(encoding='utf-8'))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='orden', required=True)
    n = sub.add_parser('nueva')
    n.add_argument('--historial', required=True)
    n.add_argument('--anterior', help='ficha de la versión que sale de producción (si existe)')
    n.add_argument('--nueva', required=True)
    n.add_argument('--prompt', choices=PROMPTS, default='actual')
    n.add_argument('--ejecucion')
    r = sub.add_parser('rollback')
    r.add_argument('--historial', required=True)
    r.add_argument('--restaurada', required=True)
    r.add_argument('--retirada', required=True)
    r.add_argument('--ejecucion')
    p = sub.add_parser('prompt-de')
    p.add_argument('--historial', required=True)
    p.add_argument('--version', type=int, required=True)
    a = ap.parse_args(argv)
    try:
        h = leer(a.historial)
        if a.orden == 'prompt-de':
            print(prompt_de(h, a.version))
            return 0
        if a.orden == 'nueva':
            registrar_nueva(h, _ficha(a.anterior) if a.anterior and Path(a.anterior).exists() else None, _ficha(a.nueva), a.prompt, a.ejecucion)
        else:
            registrar_rollback(h, _ficha(a.restaurada), _ficha(a.retirada), a.ejecucion)
        escribir(h, a.historial)
    except (ValueError, KeyError, OSError) as e:
        print(f'Error: {e}', file=sys.stderr)
        return 2
    print('Historial del agente: ' + ', '.join(f"v{e['version']} {e['estado']}" for e in h['versiones']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
