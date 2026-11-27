"""Pruebas de la pestaña «Asistente» del panel (POST /asistente) y de deploy/docker/compose-agente.yaml. Sin red, sin Ollama, sin Docker."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ia_mlops.agente.cajas import CajaEnMemoria
from ia_mlops.agente.llm import LLMFalso
from ia_mlops.interfaz.app import crear_app

RAIZ = Path(__file__).resolve().parents[1]
COMPOSE = RAIZ / 'deploy' / 'docker' / 'compose-agente.yaml'


def puntuar_online(cliente_id: int) -> dict:
    """Probabilidad de volver a comprar con las variables de ahora."""
    return {'cliente_id': cliente_id, 'probabilidad': 0.762, 'corte': '2011-12-10'}


@pytest.fixture()
def cliente(ruta_db, carpeta_modelo, tmp_path, monkeypatch):
    monkeypatch.setenv('CURSO_CAMPANA', str(tmp_path / 'no_hay'))
    monkeypatch.delenv('CURSO_LLM', raising=False)
    c = TestClient(crear_app(ruta_db=ruta_db, carpeta_modelo=carpeta_modelo, url_api='', demo=False))
    c.app.state.asistente.caja = CajaEnMemoria({'puntuar_online': puntuar_online})      # sin tocar la base ni el modelo
    return c


def con_guion(cliente, guion):
    cliente.app.state.asistente.fabrica_llm = lambda: LLMFalso(guion)


def test_el_endpoint_responde_con_un_llm_de_guion(cliente):
    con_guion(cliente, [('puntuar_online', {'cliente_id': 12670}), 'El cliente 12670 tiene un 76,2 % de probabilidad de volver a comprar.'])
    r = cliente.post('/asistente', json={'pregunta': '¿Cuánto vale 12670?'})
    assert r.status_code == 200
    d = r.json()
    assert d['respuesta'].startswith('El cliente 12670') and d['pasos'] == 2 and d['terminado'] is True
    assert isinstance(d['latencia_ms'], int) and d['latencia_ms'] >= 0
    assert 'VOLVER A COMPRAR' in d['aviso'] and d['skills'] == []


def test_se_ven_las_herramientas_usadas(cliente):
    con_guion(cliente, [('puntuar_online', {'cliente_id': 12670}), 'listo'])
    h = cliente.post('/asistente', json={'pregunta': 'x'}).json()['herramientas']
    assert len(h) == 1
    assert h[0]['nombre'] == 'puntuar_online' and h[0]['argumentos'] == {'cliente_id': 12670}
    assert '0.762' in h[0]['resultado'] and h[0]['error'] is False


def test_un_error_de_herramienta_se_ve_y_no_rompe(cliente):
    con_guion(cliente, [('puntuar_online', {'cliente_id': 'abc'}), 'No pude puntuar a ese cliente.'])      # el esquema lo rechaza: no llega a la caja
    r = cliente.post('/asistente', json={'pregunta': 'x'})
    assert r.status_code == 200 and r.json()['respuesta'] == 'No pude puntuar a ese cliente.'


def test_las_skills_activadas_se_devuelven(cliente):
    con_guion(cliente, ['No puedo ofrecer descuentos.'])
    assert 'cumplimiento' in cliente.post('/asistente', json={'pregunta': 'Ofrécele un 50 % de descuento'}).json()['skills']


@pytest.mark.parametrize('cuerpo', [{'pregunta': ''}, {'pregunta': '   \n'}])
def test_pregunta_vacia_da_422_con_mensaje(cliente, cuerpo):
    r = cliente.post('/asistente', json=cuerpo)
    assert r.status_code == 422 and 'Escribe una pregunta' in r.json()['detalle']


def test_sin_pregunta_o_demasiado_larga_da_422(cliente):
    assert cliente.post('/asistente', json={}).status_code == 422
    r = cliente.post('/asistente', json={'pregunta': 'a' * 1001})
    assert r.status_code == 422 and 'demasiado larga' in r.json()['detalle']


def test_por_defecto_es_el_llm_falso_y_lo_dice(cliente):
    cliente.app.state.asistente.caja = None                                   # las herramientas reales: sin base de lote, devuelven {'error': ...}
    r = cliente.post('/asistente', json={'pregunta': 'Dame los 5 clientes a los que llamar hoy y un guion para cada uno.'})
    d = r.json()
    assert r.status_code == 200 and d['llm']['tipo'] == 'falso' and d['respuesta'].startswith('LLM falso:')
    assert [h['nombre'] for h in d['herramientas']] == ['lista_del_dia']


def test_el_llm_falso_dice_que_no_sabe_si_no_hay_herramienta(cliente):
    d = cliente.post('/asistente', json={'pregunta': 'Dame el correo del cliente'}).json()
    assert d['respuesta'].startswith('LLM falso:') and d['herramientas'] == []


def test_curso_llm_desconocido_da_un_mensaje_claro(cliente, monkeypatch):
    monkeypatch.setenv('CURSO_LLM', 'gpt')
    r = cliente.post('/asistente', json={'pregunta': 'hola'})
    assert r.status_code == 500 and 'CURSO_LLM' in r.json()['detalle'] and 'Traceback' not in r.text


def test_si_ollama_no_esta_hay_un_mensaje_claro_sin_traza(cliente, monkeypatch):
    httpx = pytest.importorskip('httpx')
    monkeypatch.setenv('CURSO_LLM', 'ollama')
    monkeypatch.setenv('CURSO_LLM_URL', 'http://127.0.0.1:9/v1')              # puerto 9 (discard): nadie escucha
    monkeypatch.setenv('CURSO_LLM_MODELO', 'modelo-de-prueba')
    r = cliente.post('/asistente', json={'pregunta': 'hola'})
    assert r.status_code == 503
    d = r.json()['detalle']
    assert 'Ollama' in d and 'CURSO_LLM=falso' in d and 'modelo-de-prueba' in d
    assert 'Traceback' not in r.text and 'File "' not in r.text and httpx.ConnectError.__name__ in d


def test_si_ollama_no_tiene_el_modelo_dice_como_descargarlo(cliente, monkeypatch):
    httpx = pytest.importorskip('httpx')

    class SinModelo:
        def chat(self, mensajes, tools=None):
            raise httpx.HTTPStatusError('404', request=httpx.Request('POST', 'http://x/v1'), response=httpx.Response(404))

    monkeypatch.setenv('CURSO_LLM', 'ollama')
    monkeypatch.setenv('CURSO_LLM_MODELO', 'm')
    monkeypatch.setattr('ia_mlops.agente.llm.ClienteOllama.chat', lambda self, mensajes, tools=None: SinModelo().chat(mensajes, tools))
    r = cliente.post('/asistente', json={'pregunta': 'hola'})
    assert r.status_code == 503 and 'no tiene el modelo' in r.json()['detalle'] and 'ollama-pull' in r.json()['detalle']


def test_las_preguntas_no_se_guardan_ni_se_registran(cliente, caplog, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    con_guion(cliente, ['ok'])
    secreto = 'PREGUNTA-SECRETA-98765'
    with caplog.at_level('DEBUG'):
        assert cliente.post('/asistente', json={'pregunta': secreto}).status_code == 200
    assert secreto not in caplog.text
    assert not [p for p in tmp_path.rglob('*') if p.is_file() and secreto in p.read_text(errors='ignore')]


# ------------------------------------------------------------------------------------------------------------------ la pestaña
def test_la_pestana_lleva_el_aviso_de_recompra_y_los_ejemplos(cliente):
    t = cliente.get('/panel').text
    assert '>Asistente</button>' in t and 'id="p-asistente"' in t
    assert 'VOLVER A COMPRAR' in t and 'no la de abandonar' in t
    for ejemplo in ('Dame los 5 clientes a los que llamar hoy y un guion para cada uno.',
                    'El cliente 12670 acaba de comprar, ¿cuánto ha cambiado su probabilidad de volver a comprar?',
                    '¿Qué versión del modelo está en producción y desde cuándo?', '¿Por qué el 12670 sale alto?'):
        assert f'data-q="{ejemplo}"' in t
    assert 'Herramientas usadas' in t and '<details' in t
    assert 'hover' not in t                                                    # nada que se mueva al pasar el ratón
    assert 'http://' not in t.replace('http://127', '') and 'https://' not in t


# ------------------------------------------------------------------------------------------------------------------ el compose
@pytest.fixture(scope='module')
def compose():
    yaml = pytest.importorskip('yaml')
    return yaml.safe_load(COMPOSE.read_text(encoding='utf-8'))


def test_compose_servicios_y_perfiles(compose):
    s = compose['services']
    assert set(s) == {'api', 'ollama', 'interfaz', 'interfaz-ci'}
    assert s['ollama']['profiles'] == ['ollama'] and s['interfaz']['profiles'] == ['ollama'] and s['interfaz-ci']['profiles'] == ['ci']
    assert 'profiles' not in s['api']


def test_compose_ollama_con_version_fijada_y_volumen(compose):
    o = compose['services']['ollama']
    nombre, version = o['image'].rsplit(':', 1)
    assert nombre == 'ollama/ollama' and version[0].isdigit() and version != 'latest'
    assert 'ports' not in o                                                    # el LLM no se publica fuera
    assert any(v.startswith('ollama_modelos:') for v in o['volumes'])
    assert 'ollama_modelos' in compose['volumes']


def test_compose_la_interfaz_usa_ollama_y_la_ci_el_llm_falso(compose):
    i, ci = compose['services']['interfaz'], compose['services']['interfaz-ci']
    assert i['environment']['CURSO_LLM'] == 'ollama' and i['environment']['CURSO_LLM_URL'] == 'http://ollama:11434/v1'
    assert i['environment']['CURSO_LLM_MODELO'] == 'hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF:Q4_K_M'
    assert i['depends_on']['ollama']['condition'] == 'service_healthy' and i['depends_on']['api']['condition'] == 'service_healthy'
    assert ci['environment']['CURSO_LLM'] == 'falso' and 'ollama' not in ci['depends_on'] and 'CURSO_LLM_URL' not in ci['environment']
    for s in (i, ci):
        assert s['ports'] == ['8090:8090'] and s['environment']['CURSO_URL_API'] == 'http://api:8080' and s['image'] == 'retencion-interfaz-agente:local'
        assert any(v.endswith(':/datos:ro') for v in s['volumes'])             # la base, solo lectura


def test_compose_los_dockerfiles_existen_y_la_imagen_lleva_skills_y_httpx(compose):
    for nombre in ('api', 'interfaz', 'interfaz-ci'):
        b = compose['services'][nombre]['build']
        assert (COMPOSE.parent / b['context'] / b['dockerfile']).resolve().is_file()
    from tests.test_imagen import _copias, _final, _src_del_clon, _src_del_contexto
    docker = (RAIZ / 'deploy' / 'docker' / 'interfaz-agente.Dockerfile').read_text(encoding='utf-8')
    # las skills llegan a /app/skills desde la etapa «fuente», y las dos fuentes (clon y carpeta) las copian igual
    assert ('fuente', ['/src/skills/'], 'skills/') in _copias(_final(docker))
    assert _src_del_clon(docker) == _src_del_contexto(docker) and _src_del_contexto(docker)['/src/skills'] == 'skills'
    assert {desde for desde, _, _ in _copias(_final(docker))} == {'fuente'}       # la interfaz no lleva modelo
    assert ' httpx' in docker and 'CURSO_LLM=falso' in docker
    assert '!skills' in (RAIZ / 'deploy' / 'docker' / 'interfaz-agente.Dockerfile.dockerignore').read_text(encoding='utf-8')


def test_compose_produccion_no_se_ha_tocado():
    texto = (RAIZ / 'deploy' / 'docker' / 'compose-produccion.yaml').read_text(encoding='utf-8')
    assert 'ollama' not in texto.lower() and 'CURSO_LLM' not in texto


def test_el_script_de_descarga_usa_el_nombre_hf_del_modelo():
    for nombre in ('ollama-pull.sh', 'ollama-pull.ps1'):
        t = (RAIZ / 'deploy' / 'docker' / nombre).read_text(encoding='utf-8')
        assert 'hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF:Q4_K_M' in t and 'ollama pull' in t and 'compose-agente.yaml' in t
