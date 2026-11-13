"""Pruebas de «Tu equipo listo para S1»: el contenido es coherente con el repositorio, con las salidas reales capturadas y con lo generado.

Ejecutar:  python -m pytest 01-Sesiones/S0-Presentacion-y-Entorno/slides/instalacion/pruebas -q
No necesitan Internet ni conda: leen archivos del repositorio.
"""
import json
import re
import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AQUI))
import contenido as C  # noqa: E402
import generar as G  # noqa: E402

RAIZ = AQUI.parents[3]
SESION = AQUI.parents[1]
SALIDAS = json.loads((AQUI / 'salidas-reales.json').read_text(encoding='utf-8'))['salidas']
PALABRA_PROHIBIDA = re.compile(r'gu[ií]a[\s_-]*burros?', re.I)      # nombre interno nuestro: no debe aparecer en nada que vea el alumno


def todos_los_comandos():
    for p in C.PASOS:
        for c in p['cmds']:
            yield p, c
        for e in p.get('extra', []):
            for c in e['cmds']:
                yield p, c


def texto_visible():
    """Todo el texto de contenido.py que acaba en las diapositivas o en la guia."""
    partes = []
    for p in C.PASOS:
        partes += [p['titulo'], p['por_que'], p['esperado'], p.get('val_nota', ''), p.get('real_nota', '')] + p['si_falla'] + p.get('ui', [])
        partes += [c['c'] + ' ' + c.get('nota', '') for c in p['cmds']]
    partes += [x for fila in C.ERRORES for x in fila] + [x for fila in C.LISTA_FINAL for x in fila] + C.NO_PROBADO
    return '\n'.join(partes)


# ------------------------------------------------------------------ estructura
def test_los_pasos_tienen_los_campos_obligatorios_y_ids_unicos():
    ids = [p['id'] for p in C.PASOS]
    assert len(ids) == len(set(ids))
    for p in C.PASOS:
        for campo in ('id', 'bloque', 'titulo', 'donde', 'por_que', 'cmds', 'esperado', 'si_falla', 'val'):
            assert p.get(campo), f'{p["id"]}: falta {campo}'
        assert p['bloque'] in C.BLOQUES and p['donde'] in C.DONDE and p['val'] in C.VAL_TEXTO
        assert all(c['c'].strip() for c in p['cmds'])


def test_el_orden_de_los_bloques_es_el_logico():
    orden = [p['bloque'] for p in C.PASOS]
    assert orden == sorted(orden), 'los bloques deben ir A, B, C, D, E, F'
    ids = [p['id'] for p in C.PASOS]
    assert ids.index('A1') < ids.index('A3') < ids.index('B1') < ids.index('C1') < ids.index('D1') < ids.index('D2') < ids.index('E2')


def test_los_pasos_sin_probar_en_windows_no_muestran_salida_real():
    for p in C.PASOS:
        if p['val'] == 'sin':
            assert 'real' not in p and not any(c.get('k') for c in p['cmds']), f'{p["id"]} es «sin probar» pero muestra una salida real'


# ------------------------------------------------------------------ salidas reales
def test_cada_clave_de_captura_tiene_salida_real_con_codigo_cero():
    claves = {c['k'] for _, c in todos_los_comandos() if c.get('k')}
    usadas = {k for p in C.PASOS for k in p.get('real', [])}
    assert claves <= set(SALIDAS), f'faltan en salidas-reales.json: {claves - set(SALIDAS)}'
    assert usadas <= set(SALIDAS)
    malas = {k: v['codigo'] for k, v in SALIDAS.items() if v['codigo'] != 0}
    assert not malas, f'comandos capturados con error: {malas}'


def test_las_salidas_reales_no_contienen_rutas_ni_usuario_del_equipo_de_captura():
    texto = json.dumps(SALIDAS, ensure_ascii=False)
    for prohibido in ('/tmp/', '/home/claude', '/root', 'captura-s0-', 'Repositorio: repo'):
        assert prohibido not in texto, f'la salida real contiene «{prohibido}»'


def test_lo_que_prometen_los_textos_coincide_con_las_salidas_reales():
    assert 'HUMO OK' in SALIDAS['humo']['salida'].splitlines()[-1]
    assert re.search(r'\b127 passed, 4 deselected\b', SALIDAS['pytest_rapido']['salida'])
    assert re.search(r'\b131 passed\b', SALIDAS['pytest_total']['salida'])
    assert 'LISTO PARA S1' in SALIDAS['verificar']['salida']
    assert '(41188, 21)' in SALIDAS['csv']['salida']
    assert SALIDAS['sqlite']['salida'].strip().endswith('(1,)')
    assert re.match(r'Python 3\.11\.\d+', SALIDAS['py_version']['salida'])
    assert C.ENTORNO in SALIDAS['py_exe']['salida']
    assert 'Uvicorn running on http://127.0.0.1:5000' in SALIDAS['mlflow_ui']['salida']
    ui = ' '.join(C.PASOS[[p['id'] for p in C.PASOS].index('E2')]['esperado'].split())
    assert '127 passed, 4 deselected' in ui and '131 passed' in ui


def test_el_verificador_capturado_no_tiene_fallas_ni_avisos():
    s = SALIDAS['verificar']['salida']
    assert re.search(r'0 FALLA', s)
    assert '[AVISO]' not in s, 'el equipo de captura debe quedar limpio (identidad de Git puesta, puerto 5000 libre)'


def test_la_fecha_de_las_salidas_es_la_del_contenido():
    meta = json.loads((AQUI / 'salidas-reales.json').read_text(encoding='utf-8'))['meta']
    d, m, a = C.FECHA_SALIDAS.split('/')
    assert meta['fecha'] == f'{a}-{m}-{d}'


# ------------------------------------------------------------------ coherencia con el repositorio
def _ruta_de_repo(texto):
    for m in re.finditer(r'(0\d-[A-Za-z0-9_\-]+(?:[\\/][A-Za-z0-9_.\-]+)+)', texto):
        yield m.group(1).replace('\\', '/')


def test_toda_ruta_del_repositorio_que_citan_los_comandos_existe():
    citadas = set()
    for _, c in todos_los_comandos():
        citadas |= set(_ruta_de_repo(c['c']))
    for p in C.PASOS:
        citadas |= set(_ruta_de_repo(p['por_que'] + ' ' + p['esperado'] + ' ' + ' '.join(p['si_falla']) + ' ' + ' '.join(p.get('ui', []))))
    assert citadas, 'no se detecto ninguna ruta: la prueba no comprueba nada'
    faltan = sorted(r for r in citadas if not (RAIZ / r.rstrip('.,;:)»')).exists())
    assert not faltan, f'rutas citadas que no existen en el repositorio: {faltan}'


def test_las_7_extensiones_son_las_del_resto_del_material():
    assert len(C.EXTENSIONES) == 7
    guia = (RAIZ / '03-Entorno' / 'guia-instalacion' / 'generar.py').read_text(encoding='utf-8') if (RAIZ / '03-Entorno' / 'guia-instalacion' / 'generar.py').exists() else ''
    plantilla = ''.join(p.read_text(encoding='utf-8') for p in (RAIZ / '03-Entorno' / 'guia-instalacion').glob('*') if p.is_file() and p.suffix in ('.py', '.html', '.json', '.md'))
    for e in C.EXTENSIONES:
        assert e in plantilla or e in guia, f'{e} no aparece en la guia interactiva de 03-Entorno'


def test_los_ids_de_winget_son_los_de_la_guia_interactiva():
    plantilla = ''.join(p.read_text(encoding='utf-8') for p in (RAIZ / '03-Entorno' / 'guia-instalacion').glob('*') if p.is_file() and p.suffix in ('.py', '.html', '.json', '.md'))
    for _, c in todos_los_comandos():
        m = re.match(r'winget install --id (\S+)', c['c'])
        if m:
            assert m.group(1) in plantilla, f'{m.group(1)} no aparece en la guia interactiva'


def test_el_numero_de_paquetes_del_texto_es_el_del_environment_yml():
    n = G.numero_de_paquetes()
    d1 = next(p for p in C.PASOS if p['id'] == 'D1')
    assert f'{n} paquetes' in d1['por_que']
    assert re.search(rf'{n} paquetes con la version fijada', SALIDAS['verificar']['salida'])


def test_la_url_y_la_rama_de_clonado_son_las_acordadas():
    clon = next(c['c'] for _, c in todos_los_comandos() if c['c'].startswith('git clone'))
    assert clon == f'git clone --branch develop {C.REPO_URL}'
    assert C.REPO_URL.endswith(C.CARPETA_REPO + '.git')


# ------------------------------------------------------------------ lo generado
def test_lo_generado_esta_al_dia_con_el_contenido():
    assert (AQUI / 'index.html').read_text(encoding='utf-8') == G.construir_html(), 'index.html desactualizado: ejecuta python generar.py'
    assert G.SALIDA_MD.read_text(encoding='utf-8') == G.construir_md(), 'la guia desactualizada: ejecuta python generar.py'


def test_cada_comando_con_boton_copiar_se_copia_tal_cual():
    html = G.construir_html()
    for _, c in todos_los_comandos():
        assert f'data-t="{G.esc(c["c"])}"' in html, f'sin boton de copiar: {c["c"]}'


def test_las_diapositivas_incluyen_todos_los_pasos_y_las_secciones_de_ayuda():
    html = G.construir_html()
    dobles = sum(1 for p in C.PASOS if p.get('dividir'))
    assert html.count('<section class="slide"') == len(C.PASOS) + dobles + 3 + 1 + 4      # portada, mapa, antes · requisitos · errores, ayuda, lista, transparencia
    for p in C.PASOS:
        assert f'data-id="{p["id"]}"' in html
    for t in ('Errores frecuentes', 'Si algo falla y cómo pedir ayuda', 'Listo para S1', 'Qué se probó y qué no', '¿Qué archivo de requisitos uso?'):
        assert t in html


def test_la_guia_tiene_las_secciones_y_los_bloques_de_codigo_cerrados():
    md = G.SALIDA_MD.read_text(encoding='utf-8')
    assert md.startswith(f'# {G.TITULO_GUIA}')
    for sec in ('## Las tres reglas', '## El orden', '## Qué terminal usar', '## ¿Qué archivo de requisitos uso?', '## Paso a paso', '## Errores frecuentes',
                '## Si algo falla y cómo pedir ayuda', '## Listo para S1 cuando…', '## Comandos de todos los días', '## Qué se probó y qué no'):
        assert sec in md, sec
    assert md.count('```') % 2 == 0
    for p in C.PASOS:
        assert f'### {p["id"]} · ' in md


def test_la_guia_no_deja_etiquetas_html_sin_convertir():
    md = G.SALIDA_MD.read_text(encoding='utf-8')
    fuera_de_codigo = re.sub(r'```.*?```', '', md, flags=re.S)
    assert not re.search(r'</?(code|b|br)>', fuera_de_codigo)


def test_los_comandos_de_todos_los_dias_existen_de_verdad():
    """`pytest -k futuro` y la ruta de mlflow.db de S1 deben corresponder a algo real en 04-Proyecto-Base."""
    md = G.SALIDA_MD.read_text(encoding='utf-8')
    if '-k futuro' in md:
        assert any('futuro' in f.read_text(encoding='utf-8') for f in (RAIZ / '04-Proyecto-Base' / 'tests').glob('test_*.py')), 'no hay pruebas con «futuro»'
    assert 'sqlite:///models/mlflow.db' in md


# ------------------------------------------------------------------ nombre prohibido
@pytest.mark.parametrize('ruta', [
    AQUI / 'contenido.py', AQUI / 'generar.py', AQUI / 'capturar.py', AQUI / 'index.html', AQUI / 'salidas-reales.json',
    SESION / 'practica' / 'guia-rapida-entorno-s0-s1.md',
])
def test_el_nombre_interno_no_aparece_en_titulos_ni_contenido(ruta):
    assert ruta.exists(), ruta
    assert not PALABRA_PROHIBIDA.search(ruta.read_text(encoding='utf-8')), f'{ruta.name} contiene el nombre interno prohibido'
    assert not PALABRA_PROHIBIDA.search(ruta.name)


def test_los_titulos_son_los_acordados():
    assert G.TITULO_GUIA == 'Guía rápida del entorno (S0 → S1)'
    assert G.SALIDA_MD.name == 'guia-rapida-entorno-s0-s1.md'
    assert not PALABRA_PROHIBIDA.search(texto_visible())
