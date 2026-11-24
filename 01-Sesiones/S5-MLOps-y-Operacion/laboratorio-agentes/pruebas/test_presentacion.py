"""Pruebas de la presentación y la guía del «Laboratorio de agentes de S5» (sin navegador).

Qué vigilan: que index.html está al día con generar.py; entre 26 y 30 diapositivas, cada una con título, parte, minutos y notas,
con antetítulo numerado por partes; que todas las capturas citadas existen (salvo las pendientes que declare generar.py) y no
sobra ninguna; sin recursos externos, sin movimiento al pasar el ratón y con el botón «⌂ S5»; que las órdenes de la presentación
están en guia.md y citan módulos, pruebas, opciones, ramas y workflows que existen; que el código de los dos scripts de ejemplo es
el de la guía y compila; que las cifras coinciden con los JSON y los runs; que las siglas están explicadas; que el cierre tiene un
mensaje y cuatro tarjetas; que lo no verificado está dicho; y que ningún archivo lleva BOM, tabuladores sueltos, rutas personales ni secretos.
"""
import ast
import fnmatch
import importlib.util
import json
import re
from pathlib import Path

import pytest
import yaml

AQUI = Path(__file__).resolve().parents[1]
RAIZ = AQUI.parents[2]
PROYECTO = RAIZ / '04-Proyecto-Base'
GUIA = AQUI / 'guia.md'
CONFIGURAR = AQUI / 'CONFIGURAR-REPOSITORIO.md'
PICO = RAIZ / '00-Planificacion' / 's5-agentes' / '_pico'

_spec = importlib.util.spec_from_file_location('generar_laboratorio_agentes', AQUI / 'generar.py')
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)


@pytest.fixture(scope='module')
def html():
    return (AQUI / 'index.html').read_text(encoding='utf-8')


@pytest.fixture(scope='module')
def guia():
    return GUIA.read_text(encoding='utf-8')


def secciones(texto):
    return re.findall(r'<section class="slide[^"]*"([^>]*)>(.*?)</section>', texto, re.S)


def sin_etiquetas(texto):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', texto))


def todo_el_texto(html):
    return sin_etiquetas(' '.join(c for _, c in secciones(html)))


def leer(ruta):
    return Path(ruta).read_text(encoding='utf-8')


# ----------------------------------------------------------------------------------------------------------------------
# Estructura de la presentación
# ----------------------------------------------------------------------------------------------------------------------
def test_esta_al_dia_con_el_generador(html):
    assert html == G.html_completo(), 'index.html no coincide con generar.py: ejecuta  python generar.py'


def test_entre_26_y_30_diapositivas_cada_una_con_titulo_parte_minutos_y_notas(html):
    s = secciones(html)
    assert 26 <= len(s) <= 30, len(s)
    for attrs, cuerpo in s:
        assert re.search(r'data-part="[A-H]"', attrs), attrs
        m = re.search(r'data-min="(\d+)"', attrs)
        assert m and int(m.group(1)) > 0, attrs
        t = re.search(r'data-title="([^"]+)"', attrs)
        assert t and t.group(1).strip(), attrs
        n = re.search(r'data-notes="([^"]*)"', attrs)
        assert n and len(n.group(1)) > 80, f'notas demasiado cortas en {t.group(1)}'
        assert cuerpo.count('<h1>') == 1


def test_titulos_de_diapositiva_sin_repetir(html):
    titulos = [re.search(r'data-title="([^"]+)"', a).group(1) for a, _ in secciones(html)]
    assert len(titulos) == len(set(titulos))


def test_antetitulos_numerados_por_partes(html):
    s = secciones(html)
    letras = list(G.PARTES)
    for attrs, cuerpo in s:
        parte = re.search(r'data-part="([A-H])"', attrs).group(1)
        kick = re.search(r'<p class="kick">(.*?)</p>', cuerpo).group(1)
        assert kick.startswith(f'{letras.index(parte) + 1} · '), kick
    orden = [re.search(r'data-part="([A-H])"', a).group(1) for a, _ in s]
    assert orden == sorted(orden)
    assert set(orden) == set(G.PARTES)


def test_las_partes_son_los_laboratorios_l1_a_l6(html):
    nombres = ' '.join(G.NOMBRES_PARTE.values())
    for lab in ('L1 ·', 'L2 ·', 'L3 ·', 'L4 ·', 'L5 ·', 'L6 ·'):
        assert lab in nombres, lab


def test_pie_con_posicion_x_de_total_y_un_boton_por_parte(html):
    assert '${i+1} / ${N}' in html
    assert html.count('class="part"') == len(G.PARTES)
    assert '<span id="count">' in html


def test_fondo_blanco_y_nada_se_mueve_al_pasar_el_raton(html):
    assert '--fondo:#ffffff' in html
    assert ':hover' not in html and 'transition' not in html and 'animation' not in html


def test_sin_recursos_externos(html):
    assert not re.search(r'(src|href)="(https?:)?//', html)
    assert not re.search(r'@import|url\((["\']?)(https?:)?//', html)
    assert '<link' not in html and '<iframe' not in html
    for ruta in re.findall(r'(?:src|href|data-src)="([^"#]+)"', html):
        assert not ruta.startswith(('http', '//')), ruta


def test_boton_s5_al_indice_de_la_sesion(html):
    assert '<a id="bhome" href="../index.html"' in html and '⌂ S5' in html
    assert (AQUI.parent / 'index.html').exists()


def test_marco_de_los_laboratorios_de_s3_y_s4_zoom_con_clic_esc_y_flechas(html):
    for clave in ("k==='Escape'", "k==='ArrowRight'", "k==='ArrowLeft'", 'id="zoombox"', 'cursor:zoom-in', 'data-src="img/'):
        assert clave in html, clave


def test_el_visor_es_el_mismo_que_el_de_s4(html):
    """CSS y JS del marco, idénticos a los de la plantilla de S4 salvo el rótulo del pie y el botón de la sesión."""
    s4 = leer(RAIZ / '01-Sesiones' / 'S4-Orquestacion-y-CI-CD' / 'laboratorio-produccion-e2e' / 'index.html')
    js4 = re.search(r'<script>(.*?)</script>', s4, re.S).group(1)
    js5 = re.search(r'<script>(.*?)</script>', html, re.S).group(1)
    # solo cambian el rótulo del pie y las partes
    quitar = [r'ML e IA · S4 · Laboratorio de producción e2e', r'ML e IA · S5 · Laboratorio de agentes']
    js4 = js4.replace(quitar[0], 'PIE')
    js5 = js5.replace(quitar[1], 'PIE')
    js4 = re.sub(r'const PARTES=\{.*?\};', 'const PARTES={};', js4, flags=re.S)
    js5 = re.sub(r'const PARTES=\{.*?\};', 'const PARTES={};', js5, flags=re.S)
    assert js4 == js5


def test_sin_tabuladores_ni_asteriscos_sueltos_en_lo_que_se_proyecta(html):
    assert '\t' not in html
    texto = todo_el_texto(html)
    assert not re.search(r'(?<!/)\*\*', texto), 'un **negrita** sin convertir'
    assert not re.search(r'(?<!\w)`', texto), 'una `comilla` sin convertir'


# ----------------------------------------------------------------------------------------------------------------------
# Capturas
# ----------------------------------------------------------------------------------------------------------------------
def test_todas_las_capturas_citadas_existen_o_estan_declaradas_pendientes(html):
    pendientes = set(G.CAPTURAS_PENDIENTES)
    assert pendientes <= set(G.CAPTURAS)
    citadas = set(re.findall(r'(?:src|data-src)="img/([^"]+)"', html))
    assert citadas == set(G.CAPTURAS) - pendientes, 'cada captura prevista y no pendiente debe salir en alguna diapositiva'
    for nombre in citadas:
        assert nombre.endswith('.webp'), nombre
        f = AQUI / 'img' / nombre
        datos = f.read_bytes()
        assert len(datos) > 5000, nombre
        assert datos[:4] == b'RIFF' and datos[8:12] == b'WEBP', nombre
    for nombre in pendientes:
        assert not (AQUI / 'img' / nombre).exists(), f'{nombre} existe: quítala de CAPTURAS_PENDIENTES'
        assert f'img/{nombre}' in html            # sale su recuadro «Captura pendiente»
    assert ('Captura pendiente' in html) == bool(pendientes)
    en_disco = {p.name for p in (AQUI / 'img').glob('*.webp')}
    assert en_disco == set(G.CAPTURAS) - pendientes, en_disco ^ (set(G.CAPTURAS) - pendientes)


def test_las_capturas_previstas_son_las_de_s5():
    previstas = {n.split('-')[1] for n in G.CAPTURAS}
    assert previstas == {f'{i:02d}' for i in range(1, 13)}
    for n in ('s5-09-rollback-parado.webp', 's5-10-rollback-pr.webp', 's5-11-pr-rollback.webp', 's5-12-panel-asistente.webp'):
        assert n in G.CAPTURAS, n


def test_cada_captura_tiene_texto_alternativo_con_contenido(html):
    for nombre, alt in G.CAPTURAS.items():
        assert len(alt) > 60, nombre
        if nombre not in G.CAPTURAS_PENDIENTES:
            assert f'alt="{G.esc(alt)}"' in html, nombre


def test_varias_capturas_en_una_sola_diapositiva_donde_tiene_sentido(html):
    por_slide = [len(re.findall(r'<figure class="cap"', c)) for _, c in secciones(html)]
    assert max(por_slide) >= 3
    assert sum(1 for n in por_slide if n >= 2) >= 3
    assert sum(por_slide) == len(G.CAPTURAS)


def test_la_nota_de_la_captura_de_rechazo_esta_en_su_pie_y_es_fiel_al_codigo(html, guia):
    pie = re.search(r's5-05-version-rechazo\.webp".*?</figure>', html, re.S).group(0)
    assert 'antes de corregir el texto' in pie and 'Empeora más que la tolerancia de -0.1' in pie and '(+0.00)' in pie
    assert 'No mejora lo exigido (al menos +0.1, tolerancia de -0.1)' in pie
    assert 'antes de corregir el texto' in guia and 'No mejora lo exigido (al menos +0.1, tolerancia de -0.1)' in guia
    codigo = leer(PROYECTO / 'ia_mlops' / 'agente' / 'evaluacion.py')
    assert "No mejora lo exigido (al menos {-tolerancia:+g}, tolerancia de {tolerancia:g}): " in codigo
    assert "Empeora más que la tolerancia de {tolerancia:g}: " in codigo


def test_la_captura_de_aprobacion_y_la_del_panel_avisan_de_lo_que_son(html, guia):
    pie = re.search(r's5-01-esperando-aprobacion\.webp".*?</figure>', html, re.S).group(0)
    assert 'antes de aprobar' in pie and G.RUN['nuevo'] in pie
    pie = re.search(r's5-12-panel-asistente\.webp".*?</figure>', html, re.S).group(0)
    assert 'LLM FALSO' in pie and 'No es la respuesta de un LLM real' in pie
    assert 'LLM falso' in guia


# ----------------------------------------------------------------------------------------------------------------------
# Órdenes, módulos, pruebas, ramas y workflows
# ----------------------------------------------------------------------------------------------------------------------
def test_cada_orden_de_terminal_tiene_su_boton_de_copiar_y_esta_en_la_guia(html, guia):
    for clave, orden in G.O.items():
        assert f'data-t="{G.esc(orden)}"' in html, f'{clave}: la orden no sale en ninguna diapositiva'
        assert orden in guia, f'{clave}: la orden no está en guia.md'


def test_los_dos_scripts_de_ejemplo_estan_iguales_en_la_guia_y_en_la_presentacion(html, guia):
    for nombre, codigo in (('mi_cliente_mcp.py', G.CLIENTE_MCP), ('agente_falso.py', G.AGENTE_FALSO)):
        assert codigo in guia, nombre
        assert f'data-t="{G.esc(codigo)}"' in html, nombre
        ast.parse(codigo)


def test_todos_los_bloques_python_de_la_guia_compilan(guia):
    bloques = re.findall(r'```python\n(.*?)```', guia, re.S)
    assert len(bloques) >= 3
    for b in bloques:
        ast.parse(b)


def test_las_ordenes_citan_modulos_y_pruebas_que_existen():
    for clave, orden in G.O.items():
        for modulo in re.findall(r'python -m (ia_mlops[\w.]*)', orden):
            ruta = PROYECTO / Path(*modulo.split('.'))
            assert ruta.with_suffix('.py').is_file() or (ruta / '__main__.py').is_file(), f'{clave}: {modulo}'
        for prueba in re.findall(r'tests/(test_\w+\.py)', orden):
            assert (PROYECTO / 'tests' / prueba).is_file(), f'{clave}: {prueba}'
    assert (PROYECTO / 'deploy' / 'docker' / 'compose-agente.yaml').is_file()
    assert 'deploy/docker/compose-agente.yaml' in G.O['compose_ci']


def test_las_opciones_y_subcomandos_de_las_ordenes_existen_en_el_codigo():
    ev = leer(PROYECTO / 'ia_mlops' / 'agente' / 'evaluacion.py')
    reg = leer(PROYECTO / 'ia_mlops' / 'agente' / 'registro.py')
    for opcion in ('--llm', '--json', '--solo', '--sin-mlflow', '--resultados'):
        assert f"'{opcion}'" in ev, opcion
    for sub in ("'evaluar'", "'comparar'", "'crear-referencia'"):
        assert sub in ev, sub
    for sub in ('registrar-prompt', 'registrar-agente', 'mostrar', 'alias'):
        assert sub in reg, sub
    assert "'--trazas'" in leer(PROYECTO / 'ia_mlops' / 'agente' / 'agente.py')
    assert "choices=['falso', 'ollama']" in ev
    for q in ('n01', 'n04', 't02'):
        assert q in leer(PROYECTO / 'agentes' / 'preguntas_oro.json')


def test_la_orden_de_skills_usa_funciones_que_existen_y_una_palabra_de_cumplimiento():
    sk = leer(PROYECTO / 'ia_mlops' / 'agente' / 'skills.py')
    assert 'def cargar_skills' in sk and 'def activadas' in sk
    cumplimiento = leer(PROYECTO / 'skills' / 'cumplimiento' / 'SKILL.md')
    assert 'descuento' in cumplimiento.split('---')[1]
    for nombre in ('cumplimiento', 'guion-de-llamada', 'informe-semanal'):
        assert (PROYECTO / 'skills' / nombre / 'SKILL.md').is_file(), nombre


def test_los_workflows_existen_y_el_cp_los_copia_todos():
    assert (RAIZ / G.CARPETA).is_dir() and G.CARPETA == AQUI.relative_to(RAIZ).as_posix()
    en_carpeta = sorted(p.name for p in AQUI.glob('agente-*.yml'))
    assert en_carpeta == sorted(G.WORKFLOWS)         # el comodín del cp copia exactamente estos cuatro
    assert G.O['cp'] == f'cp {G.CARPETA}/agente-*.yml .github/workflows/'


def _patrones(wf):
    on = wf.get('on', wf.get(True))
    return on['push']['branches']


def test_cada_rama_de_ensayo_dispara_el_workflow_correspondiente():
    wf = {n: yaml.safe_load(leer(AQUI / n)) for n in G.WORKFLOWS}

    def dispara(rama, nombre):
        return any(fnmatch.fnmatch(rama, p.replace('**', '*')) for p in _patrones(wf[nombre]))

    ramas = {'ci_push': 'agente-ci.yml', 'ev_push': 'agente-evaluar.yml', 'igual_push': 'agente-nueva-version.yml',
             'rechazo_push': 'agente-nueva-version.yml', 'nuevo_push': 'agente-nueva-version.yml',
             'rb1_push': 'agente-rollback.yml', 'rb2_push': 'agente-rollback.yml'}
    for clave, nombre in ramas.items():
        rama = G.O[clave].split()[-1]
        assert dispara(rama, nombre), f'{clave}: {rama} no dispara {nombre}'
        for otro in G.WORKFLOWS:
            if otro != nombre:
                assert not dispara(rama, otro), f'{rama} dispara también {otro}'
    # la rama base no dispara ningún workflow
    for nombre in G.WORKFLOWS:
        assert not dispara(G.RAMA_BASE, nombre)
    assert G.RAMA_BASE.startswith('lab/') and G.O['push'] == f'git push -u origin {G.RAMA_BASE}'
    # los escenarios se eligen por el nombre de la rama, tal como lo leen los workflows
    nv = leer(AQUI / 'agente-nueva-version.yml')
    assert "contains(github.ref_name, 'prompt-nuevo')" in nv and "contains(github.ref_name, 'rechazo')" in nv and "'-0.10'" in nv
    assert G.O['igual_rama'].endswith('lab/agente-version/igual') and G.O['rechazo_rama'].endswith('lab/agente-version/rechazo')
    assert G.O['nuevo_rama'].endswith('lab/agente-version/prompt-nuevo')
    rb = leer(AQUI / 'agente-rollback.yml')
    assert "contains(github.ref_name, 'sin-comprobar')" in rb and 'sin-comprobar' in G.O['rb2_rama'] and 'sin-comprobar' not in G.O['rb1_rama']


def test_nueva_version_y_rollback_comparten_grupo_y_el_environment_es_produccion():
    nv, rb = leer(AQUI / 'agente-nueva-version.yml'), leer(AQUI / 'agente-rollback.yml')
    assert 'group: agente-version' in nv and 'group: agente-version' in rb
    publicar = nv[nv.index('  publicar:'):nv.index('  referencia:')]
    assert 'environment:' in publicar and 'produccion' in publicar


def test_el_modelo_y_los_puertos_son_los_del_codigo_y_los_workflows():
    llm = leer(PROYECTO / 'ia_mlops' / 'agente' / 'llm.py')
    assert f"MODELO_POR_DEFECTO = '{G.MODELO}'" in llm
    assert "URL_POR_DEFECTO = 'http://127.0.0.1:11435/v1'" in llm and '127.0.0.1:11435' in G.O['host_ollama']
    assert G.MODELO in leer(AQUI / 'agente-evaluar.yml') and G.MODELO in leer(AQUI / 'agente-nueva-version.yml')
    assert 'OLLAMA_VERSION: "0.40.17"' in leer(AQUI / 'agente-evaluar.yml')
    assert 'MLFLOW_ENABLE_ASYNC_TRACE_LOGGING: "false"' in leer(AQUI / 'agente-evaluar.yml')
    assert G.O['pull3'] == f'ollama pull {G.MODELO}'


def test_mcp_esta_fijado_a_la_1_30_0_y_la_2_x_se_explica(html, guia):
    assert re.search(r'^mcp==1\.30\.0$', leer(PROYECTO / 'requirements-agente.txt'), re.M)
    for t in (todo_el_texto(html), guia):
        assert 'mcp==1.30.0' in t and 'FastMCP' in t and '2.x' in t


def test_el_servidor_precarga_el_modelo_antes_de_abrir_stdio(html, guia):
    srv = leer(PROYECTO / 'ia_mlops' / 'agente' / 'servidor_mcp.py')
    assert srv.index('herramientas.precargar()') < srv.index("servidor.run(transport='stdio')")
    for t in (todo_el_texto(html), guia):
        assert 'precarg' in t and 'stdio' in t


def test_las_cinco_herramientas_son_las_del_servidor(html, guia):
    srv = leer(PROYECTO / 'ia_mlops' / 'agente' / 'servidor_mcp.py')
    for h in ('lista_del_dia', 'puntuar_online', 'puntuar_bajo_demanda', 'version_en_produccion', 'por_que'):
        assert f"name='{h}'" in srv, h
        assert h in todo_el_texto(html) and h in guia, h
    assert 'referencia://modelo' in srv and 'referencia://modelo' in guia


# ----------------------------------------------------------------------------------------------------------------------
# Cifras
# ----------------------------------------------------------------------------------------------------------------------
def pct(x):
    return f'{round(x * 100)} %'


def test_las_cifras_de_la_referencia_del_agente_coinciden_con_el_json(html, guia):
    ref = json.loads(leer(PROYECTO / 'agentes' / 'referencia-agente.json'))
    m = ref['metricas']
    assert (pct(m['acierto_herramienta']), pct(m['acierto_argumentos']), pct(m['sin_inventar']), pct(m['trampas_superadas']),
            pct(m['respuestas_correctas'])) == ('80 %', '70 %', '96 %', '86 %', '76 %')
    assert (str(round(m['latencia_p50_s'], 1)).replace('.', ','), str(round(m['latencia_p95_s'], 1)).replace('.', ',')) == ('19,2', '104,9')
    assert ref['huella_agente'] == 'e90daa8a20bef846' and ref['llm'] == G.MODELO
    assert ref['por_categoria']['seguridad']['correctas'] == 5 and ref['criticas_falladas'] == []
    assert sorted(f for c in ref['por_categoria'].values() for f in c['fallidas']) == ['m02', 'n03', 'n08', 'n10', 'n11', 't05']
    for t in (todo_el_texto(html), guia):
        for c in ('80 %', '70 %', '96 %', '86 %', '76 %', '19,2 s', '104,9 s', 'e90daa8a20bef846', '5/5', 'n03', 'n08', 'n10', 'n11', 't05', 'm02', '0,800'):
            assert c in t, c


def test_la_tabla_del_pico_coincide_con_el_informe_y_esta_en_ambos(html, guia):
    informe = PICO / 'INFORME.md'
    if informe.exists():
        texto = leer(informe)
        for c in ('491 MB', '1,1 GB', '2,1 GB', '2,76 s', '4,58 s', '4,70 s', '680 MiB', '1369 MiB', '2355 MiB', '5,3'):
            assert c in texto, c
    for t in (todo_el_texto(html), guia):
        for c in ('491 MB', '1,1 GB', '2,1 GB', '2,76 s', '4,58 s', '4,70 s', '680 MiB', '1369 MiB', '2355 MiB', '80 %', '30 %', '100 %',
                  '1 de 2', '2 de 2', '7 de 10', '5,3'):
            assert c in t, c


def test_los_runs_y_sus_cifras_coinciden_en_presentacion_y_guia(html, guia):
    assert G.RUN == {'ci': '45067003924', 'igual': '45067009924', 'evaluar': '45067018776', 'rechazo': '45067472249',
                     'nuevo': '45069539053', 'rb_rojo': '45277896553', 'rb_verde': '45278456252'}
    cifras = ['4 min 7 s', '1 min 16 s', '15 min 30 s', '780 s', '13 min 37 s', '11 min 52 s', '2 min 12 s', '12 s', '15 s',
              '14 h 19 min', '1 min 24 s', '90 %', '84 %', '79 %', '-0,10', 'v2-68d30075097172de', '68d30075097172de',
              'interfaz-agente:v1-e90daa8a20bef846', 'PR nº 4', 'PR nº 5', 'referencia-agente/v2-45069539053']
    for t in (todo_el_texto(html), guia):
        for r in G.RUN.values():
            assert r in t, r
        for c in cifras:
            assert c in t.replace('nº 4', 'nº 4'), c
    assert '4 GB' in todo_el_texto(html) and '4 GB' in guia


def test_la_suma_de_los_trabajos_de_la_v2_y_la_duracion_total(html, guia):
    # 11 min 52 s + 2 min 12 s + 12 s + 15 s: unos 14 minutos de trabajo; el resto de las 14 h 19 min es la espera de la aprobación
    assert (11 * 60 + 52) + (2 * 60 + 12) + 12 + 15 == 871
    for t in (todo_el_texto(html), guia):
        assert 'espera de la aprobación' in t


def test_la_decision_de_cada_run_es_la_dicha(html, guia):
    for t in (todo_el_texto(html), guia):
        for c in ('IGUAL', 'RECHAZADA', 'ACEPTADA'):
            assert c in t, c
        assert 'no es determinista' in t and 't06' in t


def test_un_evaluador_tambien_se_prueba(html, guia):
    primera = json.loads(leer(PICO / 'salidas' / 'evaluacion_3b_primera_pasada.json')) if (PICO / 'salidas').is_dir() else None
    if primera:
        m = primera['metricas']
        assert (pct(m['acierto_herramienta']), pct(m['sin_inventar']), pct(m['respuestas_correctas'])) == ('76 %', '64 %', '44 %')
        assert pct(m['trampas_superadas']) == '50 %'
    for t in (todo_el_texto(html), guia):
        assert 'evaluador también se prueba' in t.lower() or 'un evaluador también se prueba' in t.lower()
        for c in ('64 %', '50 %', '44 %', 'fechas', 'frecuencia_180d', '100 %'):
            assert c in t, c


def test_la_puerta_de_calidad_dice_las_cinco_reglas_y_la_tolerancia(html, guia):
    ev = leer(PROYECTO / 'ia_mlops' / 'agente' / 'evaluacion.py')
    assert 'TOLERANCIA_AGENTE = 0.10' in ev
    for t in (todo_el_texto(html), guia):
        for c in ('pregunta crítica', 'Siempre', 'huella del agente', 'tolerancia', '0,10', 'provisional', 'exigencia de mejora', 'aprobación humana'):
            assert c in t, c


# ----------------------------------------------------------------------------------------------------------------------
# Contenido obligatorio
# ----------------------------------------------------------------------------------------------------------------------
def test_el_sentido_de_la_probabilidad_es_recompra_y_el_3b_lo_confundio(html, guia):
    for t in (todo_el_texto(html), guia):
        assert 'VOLVER A COMPRAR' in t and 'abandono' in t and 'sigue en riesgo' in t and 'confundió' in t


def test_las_trampas_de_windows_estan_en_ambos(html, guia):
    for t in (todo_el_texto(html), guia):
        assert '0xc06d007f' in t and 'Library' in t and 'bin' in t and 'PATH' in t


def test_ollama_usa_el_nombre_hf_co_porque_el_corto_no_baja(html, guia):
    for t in (todo_el_texto(html), guia):
        assert 'hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF:Q4_K_M' in t and 'qwen2.5:3b' in t and 'no baja' in t
        assert 'sin ser administrador' in t.lower() or 'sin permisos de administrador' in t.lower()


def test_trazas_con_la_variable_asincrona_desactivada(html, guia):
    for t in (todo_el_texto(html), guia):
        assert 'MLFLOW_ENABLE_ASYNC_TRACE_LOGGING' in t and 'asíncron' in t


def test_aprobacion_fusion_y_rollback_con_los_textos_de_github(html, guia):
    for t in (todo_el_texto(html), guia):
        for c in ('helicr requested your review to deploy to produccion', 'Review deployments', 'Approve and deploy', 'Merge pull request',
                  'Confirm merge', 'Referencia del agente: v2-68d30075097172de', 'Rollback del agente: v2 a v1', 'La imagen no está en GHCR',
                  'nunca se publicó', 'retirada', 'sin-comprobar', 'No se borra nada', 'no mueve'):
            assert c in t or c.lower() in t.lower(), c
        assert 'git-credential-manager github login' in t


def test_tabla_de_que_va_en_mlflow_y_que_va_fuera(html, guia):
    for t in (todo_el_texto(html), guia):
        for c in ('Trazas', 'Prompts versionados', 'models from code', 'champion', 'produccion', 'código', 'GHCR', 'Secretos'):
            assert c in t, c


def test_los_seis_niveles_y_las_preguntas_de_oro(html, guia):
    for t in (todo_el_texto(html), guia):
        for c in ('Herramientas', 'Protocolo', 'LLM falso', 'LLM real', 'Seguridad', 'Humo del despliegue', '25 preguntas', 'normal', 'trampa',
                  'seguridad', 'sentido', 'oráculo'):
            assert c in t, c
    oro = json.loads(leer(PROYECTO / 'agentes' / 'preguntas_oro.json'))['preguntas']
    cuentas = {}
    for q in oro:
        cuentas[q['categoria']] = cuentas.get(q['categoria'], 0) + 1
    assert cuentas == {'normal': 11, 'trampa': 6, 'seguridad': 5, 'sentido': 3}


def test_las_siglas_estan_explicadas(html):
    texto = todo_el_texto(html)
    for sigla, explicacion in (('LLM', 'Large Language Model'), ('MCP', 'Model Context Protocol'), ('GGUF', 'formato del fichero del modelo'),
                               ('traza', 'registro de cada paso'), ('huella del agente', 'resumen corto de prompt de sistema'),
                               ('puerta de calidad', 'rechazada o aceptada'), ('GHCR', 'GitHub Container Registry'),
                               ('PR', 'pull request'), ('environment', 'reglas de protección')):
        assert sigla in texto and explicacion in texto, sigla


def test_el_extra_esta_marcado_como_no_implementado(html, guia):
    for t in (todo_el_texto(html), guia):
        assert 'no implementado' in t.lower() and 'solo planteado' in t.lower()
    texto = todo_el_texto(html)
    assert 'No hay código, capturas ni resultados' in texto


def test_lo_no_verificado_esta_dicho_y_no_se_inventan_cifras(html, guia):
    for t in (todo_el_texto(html), guia):
        assert 'Sin verificar' in t or 'sin verificar' in t
        assert 'sin dato' in t.lower()
        for c in ('compose', 'Ollama dentro de Docker', 'Codespace', '@champion', 'extra'):
            assert c in t, c
    assert 'no de tu máquina' in todo_el_texto(html).lower() or 'no** de tu máquina' in guia or 'de tu máquina' in guia


def test_cierre_con_un_mensaje_y_cuatro_tarjetas_con_cifras_reales(html):
    ultima = secciones(html)[-1][1]
    assert ultima.count('class="msg"') == 1
    assert ultima.count('class="card kpi"') == 4
    for cifra in ('80 % → 90 %', '80 % y 30 %', '5/5', '1 min 24 s', '¿Preguntas?'):
        assert cifra in ultima, cifra
    assert 'se prueba, se evalúa, se versiona, se aprueba y se puede deshacer' in ultima


def test_la_guia_tiene_los_seis_laboratorios_y_el_extra(guia):
    for h in ('## 2. L1 ·', '## 3. L2 ·', '## 4. L3 ·', '## 5. L4 ·', '## 6. L5 ·', '## 7. L6 ·', '## 8. Extra ·'):
        assert h in guia, h
    assert guia.count('**Qué debes ver') >= 6
    assert guia.count('**Si falla') >= 5


def test_la_guia_enlaza_archivos_que_existen(guia):
    for ruta in re.findall(r'\]\(([^)#]+)\)', guia):
        if ruta.startswith('http'):
            continue
        assert (AQUI / ruta).exists(), ruta


def test_el_configurar_repositorio_apunta_a_los_cuatro_workflows():
    t = leer(CONFIGURAR)
    for w in G.WORKFLOWS:
        assert w in t, w


# ----------------------------------------------------------------------------------------------------------------------
# Higiene de los archivos
# ----------------------------------------------------------------------------------------------------------------------
ARCHIVOS = ['generar.py', 'index.html', 'guia.md', 'CONFIGURAR-REPOSITORIO.md', 'pruebas/test_presentacion.py']


@pytest.mark.parametrize('nombre', ARCHIVOS)
def test_sin_bom_y_en_utf8(nombre):
    datos = (AQUI / nombre).read_bytes()
    assert not datos.startswith(b'\xef\xbb\xbf'), f'{nombre} lleva BOM'
    datos.decode('utf-8')
    assert b'\r\n' not in datos, f'{nombre} tiene finales de línea CRLF'


@pytest.mark.parametrize('nombre', ['generar.py', 'index.html', 'guia.md', 'CONFIGURAR-REPOSITORIO.md'])
def test_sin_rutas_personales_ni_credenciales(nombre):
    texto = leer(AQUI / nombre)
    assert 'C:\\Users' not in texto and 'AppData' not in texto and not re.search(r'\bBK\d{5}\b', texto)   # usuarios corporativos
    assert not re.search(r'[\w.]+@[\w-]+\.(com|es|org)', texto)
    assert not re.search(r'(token|password|contraseña)\s*[:=]\s*\S{6,}', texto, re.I)
    assert not re.search(r'ghp_|github_pat_', texto)


def test_el_unico_usuario_que_aparece_es_el_de_las_capturas(html, guia):
    for texto in (html, guia):
        usuarios = set(re.findall(r'github\.com/([\w-]+)/', texto)) | set(re.findall(r'ghcr\.io/([\w-]+)/', texto))
        assert usuarios <= {'helicr', 'ollama'}, usuarios


def test_texto_en_espanol_con_tildes_en_lo_que_se_proyecta(html):
    texto = todo_el_texto(html)
    for palabra in ('producción', 'versión', 'aprobación', 'evaluación', 'configuración', 'imagen'):
        assert palabra in texto, palabra
    for mal in ('produccion de', 'version nueva', 'aprobacion ', 'evaluacion de'):
        assert mal not in texto.replace('`produccion`', ''), mal
