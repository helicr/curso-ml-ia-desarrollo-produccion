"""La lista explícita del Codespace (env-ia-mlops-linux-64.txt) está al día con environment.yml."""
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AQUI))
import generar_bloqueo_linux as g  # noqa: E402

LINEAS = g.SALIDA.read_text(encoding='utf-8').splitlines()
URLS = [l for l in LINEAS if l.startswith('https://')]
# https://conda.anaconda.org/conda-forge/<plataforma>/<nombre>-<versión>-<build>.conda
PAQUETES = {}
for u in URLS:
    nombre, version, _build = re.match(r'.*/([^/]+)-([^-]+)-([^-]+)\.(?:conda|tar\.bz2)$', u).groups()
    PAQUETES[nombre] = version


def test_formato_explicito():
    assert '@EXPLICIT' in LINEAS
    assert len(URLS) > 100
    assert all(u.startswith('https://conda.anaconda.org/conda-forge/') for u in URLS), 'solo conda-forge'
    assert all(('/linux-64/' in u) or ('/noarch/' in u) for u in URLS)


def test_cada_paquete_fijado_esta_con_su_version():
    fijados = g.fijados()
    assert fijados, 'environment.yml sin versiones fijadas'
    for nombre, version in fijados.items():
        assert nombre in PAQUETES, f'{nombre} no está en la lista explícita: regenerarla con generar_bloqueo_linux.py'
        assert PAQUETES[nombre] == version or PAQUETES[nombre].startswith(version + '.'), \
            f'{nombre}: environment.yml pide {version} y la lista trae {PAQUETES[nombre]}: regenerarla'


def test_postcreate_usa_la_lista():
    post = (AQUI.parents[1] / '.devcontainer' / 'postcreate.sh').read_text(encoding='utf-8')
    assert 'conda create -y -q -n env-ia-mlops --file 03-Entorno/conda/env-ia-mlops-linux-64.txt' in post
    assert '--override-channels' not in post, 'conda env create no admite --override-channels'


def test_devcontainer_docker_sin_moby():
    devc = (AQUI.parents[1] / '.devcontainer' / 'devcontainer.json').read_text(encoding='utf-8')
    assert '"moby": false' in devc, 'en Debian trixie la feature docker-in-docker falla con moby (el valor por defecto)'
    # con true, la extensión de Python escribe «conda activate base» en cada terminal nueva y deja fuera de env-ia-mlops
    assert '"python.terminal.activateEnvironment": false' in devc
