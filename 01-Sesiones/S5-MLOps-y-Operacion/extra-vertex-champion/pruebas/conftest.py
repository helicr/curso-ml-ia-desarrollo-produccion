"""Fixtures comunes de las pruebas del extra «del champion de MLflow a Vertex AI».

NUNCA se toca el registro de MLflow del proyecto (04-Proyecto-Base/models/mlflow.db): se trabaja sobre una COPIA en una carpeta
temporal (la base y los artefactos), y una prueba final comprueba que el original sigue idéntico (huella SHA-256 al empezar y al acabar).
Si el modelo no está entrenado en este equipo (models/mlflow.db ausente) las pruebas que lo necesitan se omiten con el aviso de qué hacer.
"""
import hashlib
import shutil
import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parents[1]
RAIZ = AQUI.parents[2]
PROYECTO = RAIZ / '04-Proyecto-Base'
for ruta in (AQUI, AQUI / 'imagen', PROYECTO):
    if str(ruta) not in sys.path:
        sys.path.insert(0, str(ruta))

REGISTRO_REAL = PROYECTO / 'models' / 'mlflow.db'


def _sha(ruta):
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest() if Path(ruta).exists() else None


HUELLA_AL_EMPEZAR = _sha(REGISTRO_REAL)


@pytest.fixture(scope='session')
def huella_registro_real_al_empezar():
    return HUELLA_AL_EMPEZAR


@pytest.fixture(scope='session')
def registro(tmp_path_factory):
    """COPIA del registro del proyecto: {'uri', 'carpeta'}. Omite si el proyecto no tiene modelo entrenado."""
    if not REGISTRO_REAL.exists() or not (PROYECTO / 'models' / 'mlartifacts').exists():
        pytest.skip('no hay models/mlflow.db: entrena antes con  python -m ia_mlops.pipeline  (desde 04-Proyecto-Base)')
    carpeta = tmp_path_factory.mktemp('registro') / 'models'
    carpeta.mkdir()
    shutil.copy2(REGISTRO_REAL, carpeta / 'mlflow.db')
    shutil.copytree(PROYECTO / 'models' / 'mlartifacts', carpeta / 'mlartifacts')
    return {'uri': 'sqlite:///' + (carpeta / 'mlflow.db').as_posix(), 'carpeta': carpeta}


@pytest.fixture(scope='session')
def cliente_mlflow(registro):
    from ia_mlops import alias_modelo
    return alias_modelo.conectar(registro['uri'])[1]


@pytest.fixture(scope='session')
def champion(registro, cliente_mlflow):
    """Deja en la COPIA el alias champion en la última versión y la anterior recordada: {'version', 'anterior'}."""
    from ia_mlops import alias_modelo, config
    nombre = config.MODELO_REGISTRADO
    versiones = sorted(int(v.version) for v in cliente_mlflow.search_model_versions(f"name='{nombre}'"))
    if not versiones:
        pytest.skip('el registro no tiene versiones de «retencion-90d»')
    if len(versiones) == 1:                                   # registro recién entrenado: se crea una segunda versión (copia de la primera)
        import mlflow
        mlflow.register_model(f'models:/{nombre}/{versiones[0]}', nombre)
        versiones.append(versiones[0] + 1)
    alias_modelo.promover(cliente_mlflow, versiones[-2])
    alias_modelo.promover(cliente_mlflow, versiones[-1])
    return {'version': versiones[-1], 'anterior': versiones[-2]}


@pytest.fixture(scope='session')
def manifiesto(registro, champion):
    import manifiesto_champion as mc
    return mc.generar(uri=registro['uri'])


@pytest.fixture(scope='session')
def contexto(registro, manifiesto, tmp_path_factory):
    """La carpeta de construcción de la imagen (lo que usa `docker build`), con el modelo del champion de la COPIA dentro."""
    import preparar_contexto
    destino = tmp_path_factory.mktemp('contexto') / 'vertex'
    preparar_contexto.preparar(manifiesto, destino, uri=registro['uri'])
    return destino
