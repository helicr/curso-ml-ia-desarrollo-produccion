"""Cambia el prompt de sistema del agente (la constante SISTEMA de ia_mlops/agente/agente.py) por el texto de un archivo.

PARA QUÉ SIRVE (y para qué NO)
    Es el ATAJO DIDÁCTICO de agente-nueva-version.yml: en clase no hay que editar el código a mano para ensayar «una versión nueva del
    agente». Las ramas lab/agente-version/prompt-nuevo y lab/agente-version/rechazo llaman a este script ANTES de evaluar y de
    construir la imagen, de modo que lo que se evalúa y lo que se construye llevan el prompt de prompts/sistema-v2.txt.
    En un flujo real NO se parchea nada en el workflow: el cambio de prompt llega en un commit de la rama, se revisa en un pull request
    y el workflow solo evalúa lo que hay. Este script modifica la copia de trabajo del runner; nunca hace commit.

USO (desde 04-Proyecto-Base, que es donde trabajan los pasos de los workflows):
    python ../01-Sesiones/S5-MLOps-y-Operacion/laboratorio-agentes/aplicar_prompt.py [--prompt ARCHIVO] [--agente agente.py]
Código de salida: 0 aplicado · 2 no se encontró SISTEMA (o el archivo ya no es Python válido tras el cambio).
"""
import argparse
import ast
import re
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
RAIZ_REPOSITORIO = LAB.parents[2]
AGENTE = RAIZ_REPOSITORIO / '04-Proyecto-Base' / 'ia_mlops' / 'agente' / 'agente.py'
PROMPT = LAB / 'prompts' / 'sistema-v2.txt'

# SISTEMA = ( 'texto' 'texto' ... )   y a continuación la línea  USAR_SKILL = ...
# (también reconoce el resultado de una aplicación anterior, SISTEMA = '...' en una línea: aplicar dos veces da lo mismo)
_BLOQUE = re.compile(r'^SISTEMA = (?:\(.*?\)|\'[^\n]*\'|"[^\n]*")\n(?=USAR_SKILL)', re.S | re.M)


class ErrorPrompt(RuntimeError):
    pass


def aplicar(codigo, prompt):
    """Devuelve el código de agente.py con SISTEMA = <prompt>. Falla si no encuentra exactamente un bloque SISTEMA."""
    texto = ' '.join(prompt.split())                    # una sola línea: los saltos del archivo no cambian el significado
    if not texto:
        raise ErrorPrompt('El archivo del prompt está vacío.')
    if len(_BLOQUE.findall(codigo)) != 1:
        raise ErrorPrompt('No encuentro un único bloque «SISTEMA = ( ... )» seguido de USAR_SKILL en agente.py: ¿cambió el archivo?')
    nuevo = _BLOQUE.sub(lambda _: 'SISTEMA = ' + repr(texto) + '\n', codigo)
    try:
        ast.parse(nuevo)
    except SyntaxError as e:
        raise ErrorPrompt(f'Tras el cambio agente.py no es Python válido: {e}') from e
    return nuevo


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--prompt', default=str(PROMPT), help='archivo con el texto del prompt (por defecto prompts/sistema-v2.txt)')
    ap.add_argument('--agente', default=str(AGENTE), help='agente.py que se modifica')
    a = ap.parse_args(argv)
    try:
        agente = Path(a.agente)
        nuevo = aplicar(agente.read_text(encoding='utf-8'), Path(a.prompt).read_text(encoding='utf-8'))
    except (ErrorPrompt, OSError) as e:
        print(f'Error: {e}', file=sys.stderr)
        return 2
    agente.write_text(nuevo, encoding='utf-8', newline='\n')
    print(f'Prompt de {a.prompt} aplicado a {agente} (solo en esta copia de trabajo; no se hace commit).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
