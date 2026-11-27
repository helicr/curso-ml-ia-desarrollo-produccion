"""Pruebas de la interfaz MCP: aplicación real, servidores MCP reales, curso.db y modelo reales. LLM falso salvo la prueba de Ollama."""
import getpass
import re
from pathlib import Path

import httpx
import pytest

import app as modulo_app
from conftest import eventos

UI = Path(__file__).resolve().parents[1]
ESTATICO = UI / 'estatico'

ARGS = {
    'listar_tablas': {}, 'describir_tabla': {'tabla': 'master_clientes'}, 'resumen_cliente': {'cliente_id': 12369},
    'ultimas_facturas': {'cliente_id': 12369, 'n': 3}, 'ventas_por_pais': {'n': 3}, 'top_productos': {'n': 3},
    'consulta_sql': {'sql': 'SELECT pais FROM master_clientes LIMIT 2'}, 'predecir_cliente': {'cliente_id': 12369},
    'predecir_variables': {'variables': {'recencia_dias': 30, 'frecuencia': 3}}, 'por_que': {'cliente_id': 12369, 'n': 3}, 'modelo_en_uso': {},
}


def llamar(c, herramienta, args=None):
    r = c.post('/api/herramienta', json={'herramienta': herramienta, 'argumentos': args or {}})
    assert r.status_code == 200, r.text
    return r.json()


# ------------------------------------------------------------------------------------------------ estado y herramientas
def test_estado(cliente):
    e = cliente.get('/api/estado').json()
    assert e['servidores']['datos']['vivo'] and e['servidores']['modelo']['vivo']
    nombres = {t['nombre'] for s in e['servidores'].values() for t in s['herramientas']}
    assert nombres == set(ARGS)
    assert all('inputSchema' in t for s in e['servidores'].values() for t in s['herramientas'])
    assert e['backend'] == 'sqlite'
    assert e['modelo']['alias'] == 'champion' and e['modelo']['version'] == e['modelo']['alias_champion']
    assert {'ok', 'url', 'modelo'} <= set(e['llm'])


@pytest.mark.parametrize('herramienta', sorted(ARGS))
def test_llamada_manual_a_cada_herramienta(cliente, herramienta):
    r = llamar(cliente, herramienta, ARGS[herramienta])
    assert r['ok'], r['resultado']
    assert r['servidor'] in ('datos', 'modelo') and r['ms'] >= 0


def test_resultados_con_sentido(cliente):
    p = llamar(cliente, 'predecir_cliente', {'cliente_id': 12369})['resultado']
    assert 0 <= p['probabilidad'] <= 1 and p['tramo'] in ('alta', 'media', 'baja') and len(p['variables']) == 13
    assert llamar(cliente, 'ventas_por_pais', {'n': 1})['resultado']['filas'][0]['pais']
    assert llamar(cliente, 'resumen_cliente', {'cliente_id': 99999999})['ok'] is False


def test_argumentos_invalidos_no_llegan_al_servidor(cliente):
    r = llamar(cliente, 'resumen_cliente', {'cliente_id': 'abc'})
    assert not r['ok'] and 'cliente_id' in r['resultado']['error']
    r = llamar(cliente, 'resumen_cliente', {})
    assert not r['ok'] and 'Falta' in r['resultado']['error']
    assert not llamar(cliente, 'no_existe', {})['ok']


def test_traza(cliente):
    antes = cliente.get('/api/traza').json()['ultimo_id']
    llamar(cliente, 'ventas_por_pais', {'n': 2})
    llamar(cliente, 'resumen_cliente', {'cliente_id': 99999999})
    t = cliente.get('/api/traza', params={'desde': antes}).json()['items']
    assert [x['herramienta'] for x in t] == ['ventas_por_pais', 'resumen_cliente']
    assert t[0]['ok'] and not t[1]['ok'] and t[1]['resumen'].startswith('error')
    assert {'hora', 'servidor', 'ms', 'argumentos', 'resultado'} <= set(t[0])
    assert t[0]['servidor'] == 'datos'


def test_clientes_concurrentes_y_cache(cliente):
    a = cliente.get('/api/clientes').json()
    assert len(a['clientes']) == 148 and a['fallos'] == 0 and a['version'] is not None
    assert {'cliente_id', 'probabilidad', 'tramo'} <= set(a['clientes'][0])
    b = cliente.get('/api/clientes').json()
    assert b['cacheado'] is True and b['version'] == a['version']


# ------------------------------------------------------------------------------------------------ chat con LLM falso
def test_chat_herramienta_que_existe(cliente, llm_falso):
    falso = llm_falso([('ventas_por_pais', {'n': 2}), 'Austria y Francia, según la herramienta.'])
    ev = eventos(cliente.post('/api/chat', json={'mensajes': [{'role': 'user', 'content': '¿Qué país vende más?'}]}))
    tipos = [e['tipo'] for e in ev]
    assert tipos == ['paso', 'llamada', 'resultado', 'paso', 'final', 'fin']
    llam, res = ev[1], ev[2]
    assert llam['servidor'] == 'datos' and llam['herramienta'] == 'ventas_por_pais' and res['ok'] and res['resultado']['filas']
    assert len(falso.llamadas[0]['tools']) == 11                                    # las herramientas de AMBOS servidores
    assert falso.llamadas[1]['mensajes'][-1]['role'] == 'tool'                      # el resultado vuelve al LLM


def test_chat_usa_los_dos_servidores(cliente, llm_falso):
    llm_falso([[('predecir_cliente', {'cliente_id': 12369}), ('resumen_cliente', {'cliente_id': 12369})], 'Listo.'])
    ev = eventos(cliente.post('/api/chat', json={'mensajes': [{'role': 'user', 'content': 'cliente 12369'}]}))
    assert {e['servidor'] for e in ev if e['tipo'] == 'resultado'} == {'modelo', 'datos'}


def test_chat_herramienta_inexistente(cliente, llm_falso):
    falso = llm_falso([('borrar_todo', {}), 'Esa herramienta no existe.'])
    ev = eventos(cliente.post('/api/chat', json={'mensajes': [{'role': 'user', 'content': 'borra'}]}))
    res = next(e for e in ev if e['tipo'] == 'resultado')
    assert not res['ok'] and 'no existe' in res['resultado']['error']
    assert ev[-2]['tipo'] == 'final'                                                # no revienta: sigue y responde
    assert 'no existe' in falso.llamadas[1]['mensajes'][-1]['content']


def test_chat_argumentos_invalidos(cliente, llm_falso):
    llm_falso([('resumen_cliente', {'cliente_id': 'doce'}), ('ultimas_facturas', {}), 'No pude.'])
    ev = eventos(cliente.post('/api/chat', json={'mensajes': [{'role': 'user', 'content': 'x'}]}))
    res = [e for e in ev if e['tipo'] == 'resultado']
    assert len(res) == 2 and not res[0]['ok'] and not res[1]['ok'] and ev[-2]['tipo'] == 'final'


def test_chat_argumentos_que_no_son_json(cliente, llm_falso):
    llm_falso([{'role': 'assistant', 'content': None, 'tool_calls': [{'id': 'a', 'type': 'function', 'function': {'name': 'ventas_por_pais', 'arguments': '{no es json'}}]}, 'Vale.'])
    ev = eventos(cliente.post('/api/chat', json={'mensajes': [{'role': 'user', 'content': 'x'}]}))
    assert 'JSON' in next(e for e in ev if e['tipo'] == 'resultado')['resultado']['error'] and ev[-2]['tipo'] == 'final'


def test_chat_limite_de_pasos(cliente, llm_falso):
    falso = llm_falso([('modelo_en_uso', {})], repetir=True)
    ev = eventos(cliente.post('/api/chat', json={'mensajes': [{'role': 'user', 'content': 'x'}]}))
    assert len(falso.llamadas) == modulo_app.MAX_PASOS == 5
    assert [e['tipo'] for e in ev][-2:] == ['limite', 'fin'] and sum(e['tipo'] == 'resultado' for e in ev) == 5


def test_chat_sin_llm_lo_dice_y_la_app_sigue(cliente):
    a = modulo_app.app.state.ajustes
    antes = (a.url, a.modelo)
    try:
        cliente.post('/api/ajustes', json={'url': 'http://127.0.0.1:9/v1', 'modelo': 'nada'})
        e = cliente.get('/api/estado').json()
        assert e['llm']['ok'] is False and 'ollama serve' in e['llm']['ayuda']
        ev = eventos(cliente.post('/api/chat', json={'mensajes': [{'role': 'user', 'content': 'hola'}]}))
        assert any(x['tipo'] == 'error_llm' and 'ollama' in x['texto'] for x in ev)
        assert llamar(cliente, 'modelo_en_uso')['ok']                               # el resto sigue funcionando
    finally:
        cliente.post('/api/ajustes', json={'url': antes[0], 'modelo': antes[1]})


def test_chat_valida_la_entrada(cliente):
    assert cliente.post('/api/chat', json={'mensajes': []}).status_code == 422
    assert cliente.post('/api/chat', json={'mensajes': [{'role': 'system', 'content': 'x'}]}).status_code == 422
    assert cliente.post('/api/chat', json={'mensajes': [{'role': 'assistant', 'content': 'x'}]}).status_code == 422


def _ollama():
    try:
        r = httpx.get('http://127.0.0.1:11434/v1/models', timeout=2)
        return any(m['id'] == 'qwen2.5:0.5b' for m in r.json()['data'])
    except Exception:                                    # noqa: BLE001
        return False


@pytest.mark.skipif(not _ollama(), reason='No hay Ollama con qwen2.5:0.5b en 127.0.0.1:11434')
def test_chat_con_ollama_real_no_rompe_el_bucle(cliente):
    """NO exige que el modelo acierte: solo que el bucle termina de forma ordenada."""
    ev = eventos(cliente.post('/api/chat', json={'mensajes': [{'role': 'user', 'content': '¿Qué país vende más?'}]}, timeout=600))
    assert ev and ev[-1]['tipo'] == 'fin'
    assert any(e['tipo'] in ('final', 'limite', 'error_llm') for e in ev)
    assert sum(e['tipo'] == 'paso' for e in ev) <= modulo_app.MAX_PASOS


# ------------------------------------------------------------------------------------------------ modelo: promover y volver
def test_promover_y_volver_cambia_la_version_sin_reiniciar(cliente, registro):
    _, _, ultima = registro
    pid = {k: id(s.sesion) for k, s in modulo_app.app.state.puente.servidores.items()}
    assert cliente.get('/api/modelo').json()['alias_champion'] is not None
    base = cliente.post('/api/modelo/promover', json={'version': ultima}).json()
    otra = ultima - 1
    r = cliente.post('/api/modelo/promover', json={'version': otra})
    assert r.status_code == 200 and r.json()['responde']['version'] == otra          # responde la versión nueva
    assert llamar(cliente, 'predecir_cliente', {'cliente_id': 12369})['resultado']['version_modelo'] == otra
    assert cliente.get('/api/clientes').json()['version'] == otra                    # la caché de clientes se invalida con la versión
    v = cliente.post('/api/modelo/volver')
    assert v.status_code == 200 and v.json()['responde']['version'] == ultima
    assert llamar(cliente, 'predecir_cliente', {'cliente_id': 12369})['resultado']['version_modelo'] == ultima
    assert pid == {k: id(s.sesion) for k, s in modulo_app.app.state.puente.servidores.items()}   # mismas sesiones: no se reinició nada
    assert base['cambio'] is not None


def test_promover_version_inexistente(cliente):
    r = cliente.post('/api/modelo/promover', json={'version': 999})
    assert r.status_code == 409 and 'No existe la versión 999' in r.json()['error']


# ------------------------------------------------------------------------------------------------ SQL con vigilancia
ATAQUES = ['DROP TABLE master_clientes', "UPDATE master_clientes SET pais = 'X'", 'SELECT 1; DELETE FROM master_clientes',
           'SELECT cliente_id FROM master_clientes -- todo', 'SELECT * FROM fs_produccion', 'SELECT name FROM sqlite_master',
           'SELECT * FROM main.master_clientes', 'SELECT a.cliente_id FROM master_clientes a, master_facturas b']


@pytest.mark.parametrize('sql', ATAQUES)
def test_ataques_sql_rechazados(cliente, sql):
    r = llamar(cliente, 'consulta_sql', {'sql': sql})
    assert not r['ok'] and r['resultado']['rechazada_por'] == 'vigilancia del SQL' and r['resultado']['error']


def test_sql_legitimo_pasa_y_tiene_tope(cliente):
    r = llamar(cliente, 'consulta_sql', {'sql': 'SELECT pais, COUNT(*) AS n FROM master_clientes GROUP BY pais'})
    assert r['ok'] and r['resultado']['n'] > 0
    r = llamar(cliente, 'consulta_sql', {'sql': 'SELECT * FROM master_lineas'})
    assert r['resultado']['n'] == 50 and r['resultado']['truncado'] is True


# ------------------------------------------------------------------------------------------------ backend
def test_bigquery_sin_proyecto_da_error_claro_y_sigue_en_sqlite(cliente, monkeypatch):
    monkeypatch.delenv('GCP_PROJECT', raising=False)
    r = cliente.post('/api/backend', json={'backend': 'bigquery'})
    assert r.status_code == 400 and 'GCP_PROJECT' in r.json()['error'] and 'SQLite' in r.json()['error']
    assert cliente.get('/api/estado').json()['backend'] == 'sqlite'
    assert llamar(cliente, 'listar_tablas')['resultado']['motor'] == 'sqlite'


def test_bigquery_sin_credenciales_da_error_claro(cliente, monkeypatch):
    monkeypatch.setattr(modulo_app, 'comprobar_bigquery', lambda p: 'No hay credenciales de Google (simulado).')
    r = cliente.post('/api/backend', json={'backend': 'bigquery', 'proyecto': 'proyecto-de-prueba'})
    assert r.status_code == 400 and 'credenciales' in r.json()['error']
    assert cliente.get('/api/estado').json()['backend'] == 'sqlite'
    assert cliente.post('/api/backend', json={'backend': 'bigquery', 'proyecto': 'MAL ID!'}).status_code == 400


def test_cambio_de_backend_con_conector_falso(cliente, monkeypatch, tmp_path):
    """Con un servidor de datos FALSO (sin BigQuery real): comprueba el reinicio solo del servidor de datos y la vuelta a SQLite."""
    falso = tmp_path / 'mcp_datos_falso.py'
    falso.write_text("from mcp.server.fastmcp import FastMCP\ns = FastMCP('falso')\n\n@s.tool(name='listar_tablas')\n"
                     "def listar_tablas() -> dict:\n    return {'motor': 'bigquery', 'tablas': []}\n\nif __name__ == '__main__':\n    s.run(transport='stdio')\n",
                     encoding='utf-8')
    p = modulo_app.app.state.puente
    modelo_antes = id(p.servidores['modelo'].sesion)
    monkeypatch.setattr(modulo_app, 'comprobar_bigquery', lambda proyecto: None)
    monkeypatch.setattr(p, 'script_bq', falso)
    try:
        r = cliente.post('/api/backend', json={'backend': 'bigquery', 'proyecto': 'proyecto-de-prueba'})
        assert r.status_code == 200 and r.json()['backend'] == 'bigquery'
        assert cliente.get('/api/estado').json()['backend'] == 'bigquery'
        assert id(p.servidores['modelo'].sesion) == modelo_antes                      # el servidor del modelo no se tocó
    finally:
        assert cliente.post('/api/backend', json={'backend': 'sqlite'}).status_code == 200
    assert cliente.get('/api/estado').json()['backend'] == 'sqlite'
    assert llamar(cliente, 'ventas_por_pais', {'n': 1})['ok']


# ------------------------------------------------------------------------------------------------ privacidad
def test_no_se_filtran_rutas_ni_secretos(cliente, monkeypatch):
    monkeypatch.setenv('GCP_PROJECT', 'proyecto-secreto-de-prueba')
    textos = [cliente.get('/api/estado').text, cliente.get('/api/clientes').text, cliente.get('/api/modelo').text, cliente.get('/api/traza').text,
              cliente.get('/api/ajustes').text, llamar(cliente, 'describir_tabla', {'tabla': '../../etc'}).__str__(),
              cliente.post('/api/modelo/promover', json={'version': 999}).text, cliente.post('/api/backend', json={'backend': 'bigquery', 'proyecto': 'MAL'}).text]
    privados = [str(modulo_app.PROYECTO), modulo_app.PROYECTO.as_posix(), str(Path.home()), Path.home().as_posix(), 'C:\\Users', 'C:/Users']
    try:
        privados.append(getpass.getuser())
    except Exception:                                    # noqa: BLE001
        pass
    for t in textos:
        for p in privados:
            assert p.lower() not in t.lower(), f'se filtra «{p}»'
        assert not re.search(r'[A-Za-z]:[\\/]', t.replace('http://', '').replace('https://', '')), 'hay una ruta de disco en la respuesta'
    assert 'proyecto-secreto-de-prueba' not in textos[0]                              # ni el proyecto de Google del entorno


def test_solo_acepta_hosts_locales(cliente):
    assert cliente.get('/api/estado', headers={'host': 'evil.example.com'}).status_code == 400


def test_limpiar():
    assert 'C:' not in modulo_app.limpiar({'a': [f'ruta {modulo_app.PROYECTO}\\x']})['a'][0]


# ------------------------------------------------------------------------------------------------ HTML estático
def _fuentes():
    return {p.name: p.read_text(encoding='utf-8') for p in ESTATICO.iterdir() if p.suffix in ('.html', '.js', '.css')}


def test_sin_cdns_ni_recursos_externos():
    for nombre, txt in _fuentes().items():
        sin_ns = txt.replace('http://www.w3.org/2000/svg', '')
        assert not re.search(r'(?:src|href)\s*=\s*["\']\s*(?:https?:)?//', sin_ns), f'{nombre}: recurso externo'
        assert not re.search(r'url\(\s*["\']?(?:https?:)?//', sin_ns), f'{nombre}: url() externa'
        assert not re.search(r'@import', sin_ns), nombre
        assert not re.search(r'https?://(?!127\.0\.0\.1|localhost)', sin_ns), f'{nombre}: enlace a Internet'
    assert (ESTATICO / 'index.html').exists() and not list(ESTATICO.glob('*.min.js'))


def test_sin_dialogos_nativos():
    for nombre, txt in _fuentes().items():
        assert not re.search(r'\b(?:window\.)?(?:confirm|alert|prompt)\s*\(', txt), f'{nombre}: usa un diálogo nativo'
    assert 'alertdialog' in _fuentes()['index.html']


def test_rotulos_honestos_y_en_espanol():
    todo = '\n'.join(_fuentes().values())
    for frase in ['volver a comprar', 'no es un riesgo de abandono', 'sin verificar', 'no es causal', 'no es un cliente real', 'SUBE con la recencia',
                  'Un modelo pequeño se equivoca', 'no del LLM', 'Traza MCP', 'Qué NO pasa', 'Promover la v']:
        assert frase.lower() in todo.lower() or frase.lower() in todo.replace('\n', ' ').lower(), f'falta el rótulo «{frase}»'
    assert 'lang="es"' in _fuentes()['index.html']
    assert '\ufffd' not in todo and 'Ã' not in todo                                   # sin caracteres rotos


def test_portada_se_sirve(cliente):
    r = cliente.get('/')
    assert r.status_code == 200 and 'Retail' in r.text
    assert cliente.get('/estatico/app.js').status_code == 200 and cliente.get('/estatico/app.css').status_code == 200
