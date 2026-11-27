"""Pruebas de los tres workflows del extra (NO ejecutan GitHub Actions: leen los archivos y comprueban lo que prometen).

Estado de los workflows: SIN ENSAYAR en Actions. Aquí se comprueba el texto: YAML válido, disparadores, permisos mínimos, environment con aprobación,
entrada a Google Cloud sin claves (WIF), sin secretos en claro, concurrency, entradas validadas y que los comandos son los de comandos.md.
"""
import re
import subprocess
import shutil
from pathlib import Path

import pytest
import yaml

EXTRA = Path(__file__).resolve().parents[1]
COMANDOS = (EXTRA / 'comandos.md').read_text(encoding='utf-8')
NOMBRES = ['lote-composer.yml', 'dags-composer.yml', 'ensayo-airflow.yml']


def cargar(nombre):
    return yaml.safe_load((EXTRA / nombre).read_text(encoding='utf-8'))


def on(wf):
    return wf.get('on', wf.get(True))


def pasos(wf):
    for nombre, job in wf['jobs'].items():
        for p in job.get('steps', []):
            yield nombre, p


def scripts(wf):
    for nombre, p in pasos(wf):
        if 'run' in p:
            yield nombre, p.get('name', ''), p['run']


@pytest.mark.parametrize('nombre', NOMBRES)
def test_yaml_valido_con_permisos_minimos_y_concurrency(nombre):
    wf = cargar(nombre)
    assert wf['permissions'] == {'contents': 'read'}, 'permisos globales mínimos'
    assert wf['concurrency']['group'] and wf['concurrency']['cancel-in-progress'] in (True, False)
    for job in wf['jobs'].values():
        assert 'timeout-minutes' in job
        extra = set(job.get('permissions', {})) - {'contents', 'id-token'}
        assert not extra, f'permisos de más: {extra}'
    assert not (EXTRA.parents[2] / '.github' / 'workflows' / nombre).exists(), 'no se instalan en el repositorio'


@pytest.mark.parametrize('nombre', NOMBRES)
def test_sin_secretos_en_claro_ni_secrets(nombre):
    texto = (EXTRA / nombre).read_text(encoding='utf-8')
    assert '${{ secrets.' not in texto, 'sin secretos: se usan variables y WIF'
    assert not re.search(r'(AKIA|AIza|ghp_|-----BEGIN|private_key)', texto)
    assert 'credentials_json' not in texto, 'nada de claves JSON de cuenta de servicio'


@pytest.mark.parametrize('nombre', ['lote-composer.yml', 'dags-composer.yml'])
def test_entrada_a_google_cloud_sin_claves_y_con_aprobacion(nombre):
    wf = cargar(nombre)
    con_nube = [j for j, job in wf['jobs'].items() if any('google-github-actions/auth' in p.get('uses', '') for p in job['steps'])]
    assert len(con_nube) == 1
    job = wf['jobs'][con_nube[0]]
    assert job['environment'] == 'produccion'
    assert job['permissions'] == {'contents': 'read', 'id-token': 'write'}
    auth = next(p for p in job['steps'] if 'google-github-actions/auth' in p.get('uses', ''))
    assert set(auth['with']) == {'project_id', 'workload_identity_provider', 'service_account'}
    for v in ('GCP_PROYECTO', 'GCP_PROVEEDOR_WIF', 'COMPOSER_CUENTA'):
        assert f'vars.{v}' in str(auth['with'])
    for j, otro in wf['jobs'].items():                    # id-token solo donde se entra en Google
        if j != con_nube[0]:
            assert 'id-token' not in otro.get('permissions', {})


def test_lote_composer_entradas_y_comando():
    wf = cargar('lote-composer.yml')
    assert set(on(wf)) == {'workflow_dispatch'}
    assert set(on(wf)['workflow_dispatch']['inputs']) == {'corte', 'imagen', 'capacidad'}
    texto = (EXTRA / 'lote-composer.yml').read_text(encoding='utf-8')
    for v in ('COMPOSER_ENV', 'COMPOSER_REGION', 'GCP_PROYECTO', 'GCP_PROVEEDOR_WIF', 'COMPOSER_CUENTA'):
        assert v in texto
    # las entradas se pasan por variables de entorno (no pegadas en el script) y se validan
    for _, nombre, run in scripts(wf):
        assert '${{ inputs.' not in run, f'entrada pegada en un script: {nombre}'
    assert wf['jobs']['lanzar']['needs'] == 'entradas'
    cmd = next(r for _, n, r in scripts(wf) if 'Lanzar el DAG' in n)
    assert 'lanzar_lote.py' in cmd and '--auth google' in cmd and '--corte "$CORTE"' in cmd and '--imagen "$IMAGEN"' in cmd
    # coincide con comandos.md
    assert 'lanzar_lote.py --url $AIRFLOW_URL --auth google --corte 2011-12-10 --imagen' in COMANDOS
    assert 'gcloud composer environments describe $ENTORNO --location $REGION --format="value(config.airflowUri)"' in COMANDOS
    assert 'gcloud composer environments describe "${{ vars.COMPOSER_ENV }}" --location "${{ vars.COMPOSER_REGION }}" --format="value(config.airflowUri)"' in texto


def test_dags_composer_sube_los_dos_archivos_tras_las_pruebas():
    wf = cargar('dags-composer.yml')
    assert 'dags/**' in str(on(wf)['push']['paths']) and 'workflow_dispatch' in on(wf)
    assert wf['jobs']['subir']['needs'] == 'pruebas'
    assert 'id-token' not in wf['jobs']['pruebas'].get('permissions', {'contents': 'read'})
    run = next(r for _, n, r in scripts(wf) if 'Subir los DAG' in n)
    assert 'lote_logica.py' in run and 'retencion_lote.py' in run
    assert 'gcloud composer environments storage dags import --environment' in run and '--source=' in run
    assert 'gcloud composer environments storage dags import --environment $ENTORNO --location $REGION --source=$EXTRA/dags/retencion_lote.py' in COMANDOS
    espera = next(r for _, n, r in scripts(wf) if 'Esperar' in n)
    assert 'dags list -- --output=json' in espera and 'dags list -- --output=json' in COMANDOS


def test_ensayo_airflow_no_usa_la_nube_y_ejecuta_dags_test():
    wf = cargar('ensayo-airflow.yml')
    texto = (EXTRA / 'ensayo-airflow.yml').read_text(encoding='utf-8')
    assert 'google-github-actions' not in texto and 'id-token' not in texto and 'environment' not in wf['jobs']['ensayo']
    assert 'lab/composer/**' in on(wf)['push']['branches']
    assert 'constraints-${AIRFLOW_VERSION}/constraints-${PYTHON}.txt' in texto
    run = next(r for _, n, r in scripts(wf) if 'airflow dags test' in n)
    assert "airflow dags test retencion_lote 2011-12-10 --conf '{" in run
    assert 'airflow dags test retencion_lote 2011-12-10 --conf' in COMANDOS
    assert 'docker build -f "../$EXTRA/lote.Dockerfile"' in texto
    assert next(iter(wf['concurrency'].values())) == 'ensayo-airflow'


def test_cada_bloque_run_pasa_bash_n():
    candidatos = [r'C:\bk\software\git\bin\bash.exe', r'C:\Program Files\Git\bin\bash.exe', '/bin/bash', '/usr/bin/bash']
    bash = next((c for c in candidatos if Path(c).is_file()), None) or (shutil.which('bash') if 'mks' not in (shutil.which('bash') or '').lower() else None)
    if not bash:
        pytest.skip('no hay bash')
    for nombre in NOMBRES:
        for job, paso, run in scripts(cargar(nombre)):
            limpio = re.sub(r'\$\{\{[^}]*\}\}', 'X', run)
            r = subprocess.run([bash, '-n'], input=limpio, capture_output=True, text=True)
            if 'WSL' in (r.stderr or '') or 'wsl' in (r.stderr or '').lower():
                pytest.skip('bash es el de WSL sin distribución')
            assert r.returncode == 0, f'{nombre}/{paso}: {r.stderr}'


def test_los_comandos_del_cliente_existen():
    fuente = (EXTRA / 'lanzar_lote.py').read_text(encoding='utf-8')
    for opcion in ('--url', '--auth', '--corte', '--imagen', '--capacidad', '--espera', '--simular-url', '--resumen-md'):
        assert f"'{opcion}'" in fuente
