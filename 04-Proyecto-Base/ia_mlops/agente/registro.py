"""Registro del agente en MLflow: el prompt de sistema versionado y el agente como modelo con alias (S5 · T04).

QUÉ VA A MLFLOW Y QUÉ NO (regla del curso: «lo que cambia el comportamiento y hay que poder comparar o deshacer, a MLflow»)

    pieza                    dónde                                         nombre                      alias
    prompt de sistema        registro de PROMPTS de MLflow 3               agente-retencion-sistema    produccion
    agente (config. + código) registro de MODELOS, «models from code»      agente-retencion            champion
    código del agente/MCP    git (se revisa en una PR)                     ia_mlops/agente/
    pesos del LLM            caché de Ollama (no se suben)

    Un ALIAS es un puntero con nombre a una versión. Cambiar de versión = mover el puntero; deshacer = volver a moverlo. Nada se borra.

LA CONFIGURACIÓN DEL AGENTE (lo que viaja con cada versión del modelo)
    llm_modelo + llm_url   qué LLM local usa
    prompt_nombre/_version qué versión del prompt (queda FIJADA: el agente registrado no cambia si luego se mueve el alias del prompt)
    mcp_version            versión del SDK de MCP con la que se probó
    skills                 qué skills lleva
    huella                 resumen (SHA-256) de prompt + modelo + skills: dos versiones con la misma huella son el mismo agente.
                           Es lo que usa la puerta de calidad (evaluacion.py) para decir «igual».

CLI (desde 04-Proyecto-Base):
    python -m ia_mlops.agente.registro registrar-prompt                 # registra agente.SISTEMA y le pone el alias `produccion`
    python -m ia_mlops.agente.registro registrar-agente                 # registra el agente (con la versión de prompt que tenga `produccion`)
    python -m ia_mlops.agente.registro alias agente --version 2         # mueve `champion` (un rollback es lo mismo, a una versión anterior)
    python -m ia_mlops.agente.registro mostrar

DÓNDE GUARDA: el mismo almacén que el resto del curso (models/mlflow.db), o el que diga CURSO_MLFLOW_URI, o --uri.
"""
import argparse
import hashlib
import json
import os
import sys
from importlib import metadata
from pathlib import Path

os.environ.setdefault('MLFLOW_ENABLE_ASYNC_TRACE_LOGGING', 'false')      # que la traza esté escrita al terminar el span (ver informe del pico T00)
os.environ.setdefault('MLFLOW_DISABLE_AGENT_HINT', '1')

from .. import config                                                     # noqa: E402
from . import llm as modulo_llm                                           # noqa: E402
from . import skills as modulo_skills                                     # noqa: E402
from .agente import SISTEMA                                               # noqa: E402

NOMBRE_PROMPT, ALIAS_PROMPT = 'agente-retencion-sistema', 'produccion'
NOMBRE_AGENTE, ALIAS_AGENTE = 'agente-retencion', 'champion'
EXPERIMENTO = 'agente-retencion'
ARCHIVO_MODELO = Path(__file__).with_name('agente_mlflow.py')            # el «código» que se registra (models from code)
MAX_PASOS = 6


class ErrorRegistro(RuntimeError):
    """Algo falta o no cuadra en el registro. El mensaje dice qué hacer."""


# ------------------------------------------------------------------------------------------------ conexión
def uri_por_defecto():
    return os.environ.get('CURSO_MLFLOW_URI') or 'sqlite:///' + (config.MODELOS / 'mlflow.db').as_posix()


def conectar(uri=None):
    """Apunta MLflow al almacén del curso (o al indicado) y devuelve la URI. Registro de modelos y de prompts: el mismo almacén
    (el registro sigue a la URI de seguimiento mientras no se fije aparte: por eso no se toca, y no se deja fijado a un valor viejo)."""
    import mlflow
    uri = uri or uri_por_defecto()
    mlflow.set_tracking_uri(uri)
    return uri


def _sha(texto):
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()[:16]


def version_mcp():
    try:
        return metadata.version('mcp')
    except metadata.PackageNotFoundError:
        return 'no instalado'


# ------------------------------------------------------------------------------------------------ huella del agente
def huella_skills(skills):
    """{nombre: huella del contenido} de las skills: si cambia una coma de una skill, cambia su huella."""
    return {n: _sha(json.dumps(s, sort_keys=True, ensure_ascii=False)) for n, s in sorted(skills.items())}


def huella_agente(sistema, modelo, skills):
    """Huella de lo que define al agente: prompt de sistema + modelo de LLM + skills (su contenido). Dos agentes con la misma huella son el mismo."""
    return _sha(json.dumps({'sistema': sistema, 'modelo': modelo, 'skills': huella_skills(skills)}, sort_keys=True, ensure_ascii=False))


# ------------------------------------------------------------------------------------------------ prompt
def _cargar_prompt(referencia):
    import mlflow
    try:
        return mlflow.genai.load_prompt(referencia)
    except Exception as e:                                                  # noqa: BLE001 - MLflow lanza varios tipos según el caso
        raise ErrorRegistro(f'No se pudo cargar el prompt «{referencia}»: {e}') from e


def texto_del_prompt(version=None, alias=ALIAS_PROMPT):
    """El texto del prompt de sistema de una versión (o del alias, por defecto `produccion`)."""
    return _cargar_prompt(f'prompts:/{NOMBRE_PROMPT}/{version}' if version else f'prompts:/{NOMBRE_PROMPT}@{alias}').template


def registrar_prompt(texto=None, alias=ALIAS_PROMPT, mensaje=None):
    """Registra el prompt de sistema como versión nueva y mueve el alias a ella. Si ya es el texto del alias, no crea nada (idempotente).

    Devuelve {'nombre', 'version', 'alias', 'creada'}.
    """
    import mlflow
    texto = texto or SISTEMA
    try:
        actual = mlflow.genai.load_prompt(f'prompts:/{NOMBRE_PROMPT}@{alias}')
        if actual.template == texto:
            return {'nombre': NOMBRE_PROMPT, 'version': int(actual.version), 'alias': alias, 'creada': False}
    except Exception:                                                       # noqa: BLE001 - todavía no hay prompt o alias: se crea
        pass
    p = mlflow.genai.register_prompt(name=NOMBRE_PROMPT, template=texto, commit_message=mensaje or 'prompt de sistema del agente de retención')
    mlflow.genai.set_prompt_alias(NOMBRE_PROMPT, alias=alias, version=int(p.version))
    return {'nombre': NOMBRE_PROMPT, 'version': int(p.version), 'alias': alias, 'creada': True}


# ------------------------------------------------------------------------------------------------ agente
def configuracion(version_prompt=None, llm_modelo=None, llm_url=None, skills=None, max_pasos=MAX_PASOS):
    """La configuración que se registra con el agente. Sin `version_prompt`, la que tenga el alias `produccion`."""
    import mlflow
    if version_prompt is None:
        try:
            version_prompt = int(mlflow.genai.load_prompt(f'prompts:/{NOMBRE_PROMPT}@{ALIAS_PROMPT}').version)
        except Exception as e:                                              # noqa: BLE001
            raise ErrorRegistro(f'No hay prompt con el alias «{ALIAS_PROMPT}»: regístralo antes con «registrar-prompt».') from e
    skills = modulo_skills.cargar_skills() if skills is None else skills
    modelo = llm_modelo or os.environ.get('CURSO_LLM_MODELO') or modulo_llm.MODELO_POR_DEFECTO
    return {'llm_modelo': modelo, 'llm_url': llm_url or os.environ.get('CURSO_LLM_URL') or modulo_llm.URL_POR_DEFECTO,
            'prompt_nombre': NOMBRE_PROMPT, 'prompt_version': int(version_prompt), 'mcp_version': version_mcp(),
            'skills': sorted(skills), 'max_pasos': int(max_pasos),
            'huella': huella_agente(texto_del_prompt(version=version_prompt), modelo, skills)}


def registrar_agente(alias=ALIAS_AGENTE, **opciones):
    """Registra el agente como modelo «from code» (versión nueva de `agente-retencion`) y, si `alias`, mueve el alias a ella.

    `opciones`: version_prompt, llm_modelo, llm_url, skills, max_pasos (ver configuracion). Devuelve {'nombre', 'version', 'alias', 'configuracion', 'run_id'}.
    """
    import mlflow
    from mlflow.models import ModelSignature
    from mlflow.types import ColSpec, Schema
    cfg = configuracion(**opciones)
    # La firma se da a mano: sin ella (y con un ejemplo de entrada) MLflow llamaría a predict() al registrar, y eso arrancaría el LLM y el servidor MCP.
    firma = ModelSignature(inputs=Schema([ColSpec('string', 'pregunta')]), outputs=Schema([ColSpec('string')]))
    mlflow.set_experiment(EXPERIMENTO)
    with mlflow.start_run(run_name=f'registro-{cfg["huella"]}') as run:
        mlflow.set_tag('huella_agente', cfg['huella'])        # (MLflow guarda además model_config como parámetros del run)
        info = mlflow.pyfunc.log_model(name='agente', python_model=str(ARCHIVO_MODELO), model_config=cfg, registered_model_name=NOMBRE_AGENTE, signature=firma)
    version = int(info.registered_model_version)
    if alias:
        mlflow.MlflowClient().set_registered_model_alias(NOMBRE_AGENTE, alias, str(version))
    return {'nombre': NOMBRE_AGENTE, 'version': version, 'alias': alias, 'configuracion': cfg, 'run_id': run.info.run_id}


def cargar_agente(alias=ALIAS_AGENTE, version=None):
    """Carga el agente registrado: models:/agente-retencion@champion (o una versión concreta). Se usa con .predict(DataFrame con la columna «pregunta»)."""
    import mlflow
    return mlflow.pyfunc.load_model(f'models:/{NOMBRE_AGENTE}/{version}' if version else f'models:/{NOMBRE_AGENTE}@{alias}')


def configuracion_registrada(alias=ALIAS_AGENTE, version=None):
    """La configuración con la que se registró una versión del agente (la que cuelga del alias, por defecto). No arranca nada: lee el MLmodel."""
    try:
        return dict(cargar_agente(alias, version).model_config)
    except Exception as e:                                                  # noqa: BLE001
        raise ErrorRegistro(f'No se pudo leer la configuración del agente ({version or "@" + alias}): {e}') from e

# ------------------------------------------------------------------------------------------------ alias
def mover_alias(que, version, alias=None):
    """Mueve un alias a otra versión: `que` es «prompt» (alias `produccion`) o «agente» (alias `champion`). Sirve para promocionar y para el rollback."""
    import mlflow
    version = int(version)
    if que == 'prompt':
        alias = alias or ALIAS_PROMPT
        _cargar_prompt(f'prompts:/{NOMBRE_PROMPT}/{version}')               # falla con un mensaje claro si esa versión no existe
        mlflow.genai.set_prompt_alias(NOMBRE_PROMPT, alias=alias, version=version)
        return {'que': que, 'nombre': NOMBRE_PROMPT, 'alias': alias, 'version': version}
    if que == 'agente':
        alias = alias or ALIAS_AGENTE
        cliente = mlflow.MlflowClient()
        try:
            cliente.get_model_version(NOMBRE_AGENTE, str(version))
        except Exception as e:                                              # noqa: BLE001
            raise ErrorRegistro(f'No existe la versión {version} de «{NOMBRE_AGENTE}»: {e}') from e
        cliente.set_registered_model_alias(NOMBRE_AGENTE, alias, str(version))
        return {'que': que, 'nombre': NOMBRE_AGENTE, 'alias': alias, 'version': version}
    raise ErrorRegistro(f'«{que}» no es ni «prompt» ni «agente».')


def estado():
    """Lo que hay registrado: versiones del prompt y del agente, y a qué versión apunta cada alias."""
    import mlflow
    cliente = mlflow.MlflowClient()
    prompts = []
    for alias in (ALIAS_PROMPT,):
        try:
            prompts.append({'alias': alias, 'version': int(mlflow.genai.load_prompt(f'prompts:/{NOMBRE_PROMPT}@{alias}').version)})
        except Exception:                                                   # noqa: BLE001
            pass
    agentes = []
    try:
        por_version = {}                                                    # alias -> versión (así los devuelve el registro)
        for nombre, v in (cliente.get_registered_model(NOMBRE_AGENTE).aliases or {}).items():
            por_version.setdefault(int(v), []).append(nombre)
        for v in cliente.search_model_versions(f"name='{NOMBRE_AGENTE}'"):
            agentes.append({'version': int(v.version), 'alias': sorted(por_version.get(int(v.version), [])), 'run_id': v.run_id})
    except Exception:                                                       # noqa: BLE001
        pass
    return {'prompt': {'nombre': NOMBRE_PROMPT, 'alias': prompts}, 'agente': {'nombre': NOMBRE_AGENTE, 'versiones': sorted(agentes, key=lambda a: a['version'])}}


# ------------------------------------------------------------------------------------------------ CLI
def main(argv=None):
    ap = argparse.ArgumentParser(prog='python -m ia_mlops.agente.registro', description='Prompt y agente de retención en MLflow')
    ap.add_argument('--uri', help='almacén de MLflow (por defecto CURSO_MLFLOW_URI o models/mlflow.db)')
    sub = ap.add_subparsers(dest='orden', required=True)
    p = sub.add_parser('registrar-prompt', help='registra el prompt de sistema y mueve el alias `produccion`')
    p.add_argument('--archivo', help='texto del prompt en un archivo UTF-8 (por defecto, el de agente.py)')
    a = sub.add_parser('registrar-agente', help='registra el agente como modelo (models from code) y mueve `champion`')
    a.add_argument('--llm-modelo', help='modelo de LLM (por defecto, el de llm.py o CURSO_LLM_MODELO)')
    a.add_argument('--llm-url', help='URL de la API compatible con OpenAI del LLM')
    a.add_argument('--version-prompt', type=int, help='versión del prompt (por defecto, la del alias `produccion`)')
    a.add_argument('--sin-alias', action='store_true', help='no mover el alias `champion`')
    m = sub.add_parser('alias', help='mueve un alias a otra versión (promocionar o hacer rollback)')
    m.add_argument('que', choices=['prompt', 'agente'])
    m.add_argument('--version', type=int, required=True)
    m.add_argument('--nombre', help='alias (por defecto `produccion` para el prompt y `champion` para el agente)')
    s = sub.add_parser('mostrar', help='qué hay registrado y a qué apunta cada alias')
    s.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    try:
        print(f'Almacén de MLflow: {conectar(args.uri)}')
        if args.orden == 'registrar-prompt':
            texto = Path(args.archivo).read_text(encoding='utf-8') if args.archivo else None
            r = registrar_prompt(texto)
            print(('Prompt registrado' if r['creada'] else 'Sin cambios (el alias ya apunta a este texto)') + f': {r["nombre"]} v{r["version"]} → @{r["alias"]}')
        elif args.orden == 'registrar-agente':
            r = registrar_agente(alias=None if args.sin_alias else ALIAS_AGENTE, version_prompt=args.version_prompt,
                                 llm_modelo=args.llm_modelo, llm_url=args.llm_url)
            c = r['configuracion']
            print(f'Agente registrado: {r["nombre"]} v{r["version"]}' + (f' → @{r["alias"]}' if r['alias'] else ''))
            print(f'  LLM {c["llm_modelo"]} · prompt v{c["prompt_version"]} · mcp {c["mcp_version"]} · skills {c["skills"]} · huella {c["huella"]}')
        elif args.orden == 'alias':
            r = mover_alias(args.que, args.version, args.nombre)
            print(f'Alias movido: {r["nombre"]}@{r["alias"]} → v{r["version"]}')
        else:
            e = estado()
            if args.json:
                print(json.dumps(e, indent=2, ensure_ascii=False))
            else:
                print(f'Prompt «{e["prompt"]["nombre"]}»: ' + (', '.join(f'@{x["alias"]} → v{x["version"]}' for x in e['prompt']['alias']) or 'sin registrar'))
                print(f'Agente «{e["agente"]["nombre"]}»:' + ('' if e['agente']['versiones'] else ' sin registrar'))
                for v in e['agente']['versiones']:
                    print(f'  v{v["version"]}  alias: {", ".join("@" + x for x in v["alias"]) or "-"}')
        return 0
    except ErrorRegistro as e:
        print(f'Error: {e}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
