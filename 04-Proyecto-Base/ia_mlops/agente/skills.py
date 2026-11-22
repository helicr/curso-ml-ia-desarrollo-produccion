"""Skills: el saber hacer del negocio, en archivos de texto que el agente carga solo cuando los necesita.

Una skill es una carpeta con un SKILL.md:

    ---
    name: cumplimiento                      <- nombre (el que el LLM usa para pedirla)
    description: Qué no se dice nunca...    <- una frase: cuándo sirve. Es lo ÚNICO que el agente ve siempre
    activar_si: descuento, correo           <- (opcional) palabras de la pregunta que la activan sin que el LLM la pida
    ---
    Instrucciones completas en Markdown...  <- el cuerpo: solo se carga si hace falta

Dos formas de cargar el cuerpo (el agente usa las dos, ver agente.py):
    1. A petición del LLM: ve el catálogo (nombre + descripción) y llama a la herramienta interna usar_skill(nombre).
    2. Por la pregunta: si contiene una palabra de `activar_si`, el cuerpo se inyecta en el prompt de sistema desde el primer paso.
       Se usa para las reglas que NO pueden depender de que un modelo pequeño se acuerde de pedirlas (cumplimiento).
"""
import unicodedata
from pathlib import Path

CARPETA = Path(__file__).resolve().parents[2] / 'skills'      # 04-Proyecto-Base/skills


def _plano(texto):
    """Minúsculas y sin tildes, para comparar «teléfono» con «telefono»."""
    return ''.join(c for c in unicodedata.normalize('NFD', texto.lower()) if unicodedata.category(c) != 'Mn')


def cargar_skills(carpeta=CARPETA):
    """Lee carpeta/*/SKILL.md y devuelve {nombre: {'descripcion', 'activar_si', 'cuerpo'}}."""
    skills = {}
    for archivo in sorted(Path(carpeta).glob('*/SKILL.md')):
        _, cabecera, cuerpo = archivo.read_text(encoding='utf-8').split('---', 2)       # frontmatter entre dos «---»
        datos = dict(linea.split(':', 1) for linea in cabecera.strip().splitlines() if ':' in linea)
        datos = {k.strip(): v.strip() for k, v in datos.items()}
        palabras = [_plano(p.strip()) for p in datos.get('activar_si', '').split(',') if p.strip()]
        skills[datos['name']] = {'descripcion': datos['description'], 'activar_si': palabras, 'cuerpo': cuerpo.strip()}
    return skills


def catalogo(skills):
    """Lo que ve el LLM siempre: una línea por skill."""
    return '\n'.join(f'- {nombre}: {s["descripcion"]}' for nombre, s in skills.items())


def activadas(skills, pregunta):
    """Nombres de las skills cuyas palabras clave aparecen en la pregunta."""
    p = _plano(pregunta)
    return [nombre for nombre, s in skills.items() if any(palabra in p for palabra in s['activar_si'])]
