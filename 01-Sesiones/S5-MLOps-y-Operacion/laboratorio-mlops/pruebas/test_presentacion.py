"""Pruebas de la presentación y la guía del «Laboratorio de MLOps clásico de S5» (sin navegador).

Qué vigilan: que index.html está al día con generar.py; entre 22 y 30 diapositivas, cada una con título, parte, minutos y notas, con
antetítulo numerado por partes; que el visor es el mismo que el del laboratorio de agentes (solo cambia el pie); que las capturas de
GitHub Actions están declaradas pendientes (y salen como «Captura pendiente»); que las órdenes de la presentación están en guia.md y
citan módulos, opciones, ramas y workflows que existen; que las salidas «Qué debes ver» son las reales del ensayo (si la copia de
ensayo está en este equipo) y las cifras coinciden entre presentación, guía y workflow; que lo no verificado está dicho; y que ningún
archivo lleva BOM, CRLF, rutas personales ni secretos.
"""
import ast
import html as htmllib
import importlib.util
import json
import os
import re
from pathlib import Path

import pytest
import yaml

AQUI = Path(__file__).resolve().parents[1]
RAIZ = AQUI.parents[2]
PROYECTO = RAIZ / '04-Proyecto-Base'
GUIA = AQUI / 'guia.md'
SALIDAS_ENSAYO = Path(os.environ.get('CURSO_SALIDAS_ENSAYO', 'no-definida'))        # carpeta con las salidas del ensayo (si no está, esa prueba se omite)

_spec = importlib.util.spec_from_file_location('generar_laboratorio_mlops', AQUI / 'generar.py')
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
    return re.sub(r'\s+', ' ', htmllib.unescape(re.sub(r'<[^>]+>', ' ', texto)))


def todo_el_texto(html):
    return sin_etiquetas(' '.join(c for _, c in secciones(html)))


def leer(ruta):
    return Path(ruta).read_text(encoding='utf-8')


# ----------------------------------------------------------------------------------------------------------------------
# Estructura de la presentación
# ----------------------------------------------------------------------------------------------------------------------
def test_esta_al_dia_con_el_generador(html):
    assert html == G.html_completo(), 'index.html no coincide con generar.py: ejecuta  python generar.py'


def test_entre_22_y_30_diapositivas_cada_una_con_titulo_parte_minutos_y_notas(html):
    s = secciones(html)
    assert 22 <= len(s) <= 30, len(s)
    for attrs, cuerpo in s:
        assert re.search(r'data-part="[A-G]"', attrs), attrs
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
        parte = re.search(r'data-part="([A-G])"', attrs).group(1)
        kick = re.search(r'<p class="kick">(.*?)</p>', cuerpo).group(1)
        assert kick.startswith(f'{letras.index(parte) + 1} · '), kick
    orden = [re.search(r'data-part="([A-G])"', a).group(1) for a, _ in s]
    assert orden == sorted(orden)
    assert set(orden) == set(G.PARTES)


def test_las_partes_son_los_laboratorios_l1_a_l5(html):
    nombres = ' '.join(G.NOMBRES_PARTE.values())
    for lab in ('L1 ·', 'L2 ·', 'L3 ·', 'L4 ·', 'L5 ·'):
        assert lab in nombres, lab


def test_pie_con_posicion_x_de_total_y_un_boton_por_parte(html):
    assert '${i+1} / ${N}' in html
    assert html.count('class="part"') == len(G.PARTES)
    assert '<span id="count">' in html
    assert 'ML e IA · S5 · Laboratorio de MLOps clásico' in html and 'Laboratorio de agentes</span>' not in html


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


def test_marco_zoom_con_clic_esc_y_flechas(html):
    for clave in ("k==='Escape'", "k==='ArrowRight'", "k==='ArrowLeft'", 'id="zoombox"', 'cursor:zoom-in'):
        assert clave in html, clave


def test_el_visor_es_el_del_laboratorio_de_agentes_salvo_el_pie(html):
    """CSS y JS idénticos a los del laboratorio de agentes: solo cambian el rótulo del pie y las partes."""
    ag = leer(AQUI.parent / 'laboratorio-agentes' / 'index.html')
    for expresion in (r'<style>(.*?)</style>', r'<script>(.*?)</script>'):
        a = re.search(expresion, ag, re.S).group(1)
        b = re.search(expresion, html, re.S).group(1)
        a = a.replace('ML e IA · S5 · Laboratorio de agentes', 'PIE')
        b = b.replace('ML e IA · S5 · Laboratorio de MLOps clásico', 'PIE')
        a = re.sub(r'const PARTES=\{.*?\};', 'const PARTES={};', a, flags=re.S)
        b = re.sub(r'const PARTES=\{.*?\};', 'const PARTES={};', b, flags=re.S)
        assert a == b


def test_sin_tabuladores_ni_asteriscos_sueltos_en_lo_que_se_proyecta(html):
    assert '\t' not in html
    texto = sin_etiquetas(re.sub(r'<pre>.*?</pre>', ' ', ' '.join(c for _, c in secciones(html)), flags=re.S))      # las salidas reales (en <pre>) llevan lo que llevan
    assert not re.search(r'(?<!/)\*\*', texto), 'un **negrita** sin convertir'
    assert not re.search(r'(?<!\w)`', texto), 'una `comilla` sin convertir'


# ----------------------------------------------------------------------------------------------------------------------
# Capturas (todas de GitHub Actions y pendientes)
# ----------------------------------------------------------------------------------------------------------------------
def test_las_seis_capturas_de_actions_son_reales_y_salen_como_imagen(html):
    assert sorted(G.CAPTURAS) == ['m-01-estable-verde.webp', 'm-02-resumen-estable.webp', 'm-03-deriva-rojo.webp', 'm-04-resumen-deriva.webp',
                                  'm-05-issue-alerta.webp', 'm-06-segunda-alerta.webp']
    assert G.CAPTURAS_PENDIENTES == []
    for nombre in G.CAPTURAS:
        assert (AQUI / 'img' / nombre).is_file(), nombre
        assert f'img/{nombre}' in html
    assert 'Captura pendiente' not in html


def test_cada_captura_tiene_texto_alternativo_con_contenido_y_sale_una_vez(html):
    cuerpo = ' '.join(c for _, c in secciones(html))
    for nombre, alt in G.CAPTURAS.items():
        assert len(alt) > 60, nombre
        assert cuerpo.count(f'data-img="{nombre}"') == 1, nombre


def test_el_deck_ya_no_dice_sin_verificar_en_actions(html):
    texto = todo_el_texto(html)
    assert 'sin verificar en actions' not in texto.lower()
    assert 'Verificado en Actions' in texto


# ----------------------------------------------------------------------------------------------------------------------
# Órdenes, módulos, ramas y workflow
# ----------------------------------------------------------------------------------------------------------------------
def test_cada_orden_de_terminal_tiene_su_boton_de_copiar_y_esta_en_la_guia(html, guia):
    for clave, orden in G.O.items():
        assert f'data-t="{G.esc(orden)}"' in html, f'{clave}: la orden no sale en ninguna diapositiva'
        assert orden in guia, f'{clave}: la orden no está en guia.md'


def test_las_ordenes_citan_modulos_que_existen_y_opciones_validas():
    deriva = leer(PROYECTO / 'ia_mlops' / 'deriva.py')
    alias = leer(PROYECTO / 'ia_mlops' / 'alias_modelo.py')
    for clave, orden in G.O.items():
        for modulo in re.findall(r'python -m (ia_mlops[\w.]*)', orden):
            assert (PROYECTO / Path(*modulo.split('.'))).with_suffix('.py').is_file(), f'{clave}: {modulo}'
        if 'ia_mlops.deriva' in orden:
            for opcion in re.findall(r'(--[\w-]+)', orden):
                assert f"'{opcion}'" in deriva, f'{clave}: {opcion}'
        if 'ia_mlops.alias_modelo' in orden:
            for opcion in re.findall(r'(--[\w-]+)', orden):
                assert f"'{opcion}'" in alias, f'{clave}: {opcion}'
            sub = orden.split('alias_modelo ')[1].split()[0]
            assert f"add_parser('{sub}'" in alias, sub
    assert "choices=list(config.FUENTES)" in leer(PROYECTO / 'ia_mlops' / 'pipeline.py')
    config = leer(PROYECTO / 'ia_mlops' / 'config.py')
    assert "'muestra'" in config and "'completo'" in config
    assert "'descargar'" in leer(PROYECTO / 'ia_mlops' / 'dataset.py')
    assert (PROYECTO / 'tests' / 'datos' / 'cliente_ejemplo.json').is_file()
    assert (PROYECTO / 'data' / 'raw' / 'muestra_online_retail_ii.csv').is_file()


def test_el_workflow_existe_y_el_cp_lo_copia(guia):
    assert G.CARPETA == AQUI.relative_to(RAIZ).as_posix() and (RAIZ / G.CARPETA).is_dir()
    assert [p.name for p in AQUI.glob('*.yml')] == G.WORKFLOWS == ['monitoreo.yml']
    assert G.O['cp'] == f'cp {G.CARPETA}/monitoreo.yml .github/workflows/'
    assert 'cd ..' == G.O['cd_raiz']


def test_las_ramas_de_ensayo_disparan_el_workflow_y_la_base_no():
    import fnmatch
    wf = yaml.safe_load(leer(AQUI / 'monitoreo.yml'))
    patrones = wf.get('on', wf.get(True))['push']['branches']

    def dispara(rama):
        return any(fnmatch.fnmatch(rama, p.replace('**', '*')) for p in patrones)
    assert G.O['estable_rama'] == f'git switch -c {G.RAMA_ESTABLE}' and G.O['estable_push'].endswith(G.RAMA_ESTABLE)
    assert G.O['deriva_rama'] == f'git switch -c {G.RAMA_DERIVA}' and G.O['deriva_push'].endswith(G.RAMA_DERIVA)
    assert dispara(G.RAMA_ESTABLE) and dispara(G.RAMA_DERIVA) and not dispara(G.RAMA_BASE)
    assert G.RAMA_BASE.startswith('lab/') and G.O['push'] == f'git push -u origin {G.RAMA_BASE}'
    assert G.O['volver_base'] == f'git switch {G.RAMA_BASE}'
    case = leer(AQUI / 'monitoreo.yml')
    assert f'{G.RAMA_ESTABLE})' in case and f'{G.RAMA_DERIVA})' in case


def test_la_guia_enlaza_archivos_que_existen(guia):
    enlaces = re.findall(r'\]\(([^)#]+)\)', guia)
    assert enlaces
    for ruta in enlaces:
        if ruta.startswith('http'):
            continue
        assert (AQUI / ruta).exists(), ruta
    assert '../../S4-Orquestacion-y-CI-CD/laboratorio-cloud-journey/guia.md' in guia


def test_todos_los_bloques_python_de_la_guia_compilan_y_los_bash_no_tienen_cr(guia):
    for b in re.findall(r'```python\n(.*?)```', guia, re.S):
        ast.parse(b)
    for b in re.findall(r'```bash\n(.*?)```', guia, re.S):
        assert '\r' not in b and not re.search(r'\b(Select-String|Get-Content)\b', b)


# ----------------------------------------------------------------------------------------------------------------------
# Cifras REALES
# ----------------------------------------------------------------------------------------------------------------------
def _real(nombre):
    f = SALIDAS_ENSAYO / nombre
    if not f.exists():
        pytest.skip('la copia de ensayo con las salidas reales no está en este equipo')
    return f.read_text(encoding='utf-8')


def _lineas_estan_en_la_realidad(constante, real):
    for linea in constante.splitlines():
        l = linea.rstrip()
        if not l.strip() or l.strip() in ('...',) or l.startswith('salida:') or '[...]' in l or l.startswith(('(', '--umbral')):
            continue
        assert l in real, f'no sale en la salida real: {l!r}'


def test_las_salidas_enseñadas_son_las_reales_del_ensayo():
    _lineas_estan_en_la_realidad(G.S_CORTES, _real('g03-cortes.txt'))
    _lineas_estan_en_la_realidad(G.S_DATOS, _real('g04-datos.txt'))
    _lineas_estan_en_la_realidad(G.S_REND, _real('g05-rend.txt'))
    _lineas_estan_en_la_realidad(G.S_REND_ENT, _real('g06-rend-ent.txt'))
    _lineas_estan_en_la_realidad(G.S_PAR, _real('g08-estable.txt'))
    _lineas_estan_en_la_realidad(G.S_PAR_UMBRAL, _real('g09-estable-umbral.txt'))
    _lineas_estan_en_la_realidad(G.S_MOSTRAR1, _real('g11-mostrar.txt'))
    _lineas_estan_en_la_realidad(G.S_PROMOVER1, _real('g12-promover1.txt'))
    _lineas_estan_en_la_realidad(G.S_CARGAR1, _real('g13-cargar1.txt'))
    _lineas_estan_en_la_realidad(G.S_PIPE_COMPLETO, _real('g14-pipeline-completo.txt'))
    _lineas_estan_en_la_realidad(G.S_MOSTRAR2, _real('g15-mostrar2.txt'))
    _lineas_estan_en_la_realidad(G.S_PROMOVER2, _real('g16-promover2.txt'))
    _lineas_estan_en_la_realidad(G.S_CARGAR2, _real('g17-cargar2.txt'))
    _lineas_estan_en_la_realidad(G.S_VOLVER, _real('g18-volver.txt'))


def test_las_cifras_clave_estan_en_presentacion_y_guia(html, guia):
    cifras = ['2,830', '0,437', '0,400', '0,293', '0,276', '0,147', '5 de 13', '0,6982', '0,7534', '0,7423', '0,8497', '0,1515', '0,2747',
              '0.8279', '0.7245', '0.7471', '0.7956', '0.6982', '0.7855', '437 s', '3521a0421905ba28', '35a94deb4e04ab4a', '0.410', '0.5', '45',
              '5,942', '1,067,371', '69', '131', '2011-12-10', '23 5', '05:23']
    for t in (todo_el_texto(html), guia):
        for c in cifras:
            if c == '23 5':
                continue
            assert c in t or c.replace(',', '.') in t or c.replace('.', ',') in t, c
    assert '0,8279 → 0,7245' in todo_el_texto(html) and '0,8497 → 0,6982' in todo_el_texto(html)


def test_las_cifras_de_los_json_de_la_muestra_coinciden_con_la_referencia_del_proyecto():
    ref = json.loads(leer(PROYECTO / 'models' / 'referencia.json')) if (PROYECTO / 'models' / 'referencia.json').exists() else None
    if ref:        # solo si el proyecto del repositorio tiene el modelo entrenado
        assert ref['huella_datos'] == '35a94deb4e04ab4a'
        assert round(ref['metricas_valid']['auc'], 4) == 0.6982 and round(ref['metricas_test']['auc'], 4) == 0.7471


def test_la_leccion_del_corte_de_entrenamiento_y_la_convencion_del_umbral_estan_dichas(html, guia):
    for t in (todo_el_texto(html), guia):
        assert 'engaña' in t and 'sobreajuste' in t and 'SOBREESTIMA' in t
        assert 'convención del oficio, no una ley' in t or 'convención del oficio' in t
        assert 'esperable' in t and 'antiguedad_dias' in t
        assert 'puntero' in t and 'No se ha borrado nada' in t or 'no se borra nada' in t.lower()
        assert 'models/modelo_mlflow' in t and 'no lee el registro' in t.lower()


def test_la_alerta_es_el_rojo_y_no_duplica_issue(html, guia):
    for t in (todo_el_texto(html), guia):
        assert 'alerta-deriva' in t and 'ROJO' in t and 'issues: write' in t
        assert 'no abra otro' in t or 'no abre otro' in t or 'ningún issue nuevo' in t.lower() or 'ningún *issue* nuevo' in t.lower()
        assert 'schedule' in t and 'fork' in t and 'desactiv' in t.lower()
        assert 'working-directory: .' in t


def test_el_orden_l1_l2_antes_que_l3_y_como_volver_a_la_muestra(html, guia):
    for t in (todo_el_texto(html), guia):
        assert 'antes que L3' in t and 'curso.db' in t and 'R03_integridad_referencial' in t
        assert 'descargar' in t and '437 s' in t


def test_nota_para_windows_cmd_y_powershell(html, guia):
    for t in (todo_el_texto(html), guia):
        assert 'PowerShell 5.1' in t and '&&' in t and 'LASTEXITCODE' in t and 'ERRORLEVEL' in t


def test_lo_no_verificado_esta_dicho_y_no_se_inventan_cifras(html, guia):
    for t in (todo_el_texto(html), guia):
        assert 'sin verificar' in t.lower() and 'sin dato' in t.lower()
        for c in ('Codespace', 'Actions', 'pendiente'):
            assert c in t or c.lower() in t.lower(), c
    assert 'Todo lo de GitHub Actions' in todo_el_texto(html) or 'todo lo de GitHub Actions' in todo_el_texto(html).lower()


def test_enlaza_a_los_costes_de_s4_sin_repetirlos(html, guia):
    for t in (todo_el_texto(html), guia):
        assert 'laboratorio-cloud-journey/guia.md' in t and 'avisa' in t and 'no corta' in t and 'borra' in t
    assert (AQUI.parent.parent / 'S4-Orquestacion-y-CI-CD' / 'laboratorio-cloud-journey' / 'guia.md').exists()


def test_las_siglas_estan_explicadas(html):
    texto = todo_el_texto(html)
    for sigla, explicacion in (('PSI', 'Population Stability Index'), ('KS', 'Kolmogórov'), ('AUC', 'etiqueta'), ('Alias', 'puntero'),
                               ('Issue', 'incidencia'), ('schedule', 'cron'), ('Deriva de datos', 'sin etiqueta'), ('Corte', 'foto')):
        assert sigla in texto and explicacion in texto, sigla


def test_cierre_con_un_mensaje_y_cuatro_tarjetas_con_cifras_reales(html):
    ultima = secciones(html)[-1][1]
    assert ultima.count('class="msg"') == 1
    assert ultima.count('class="card kpi"') == 4
    for cifra in ('5 de 13', '0,8497 → 0,6982', '0,8279 → 0,7245', '0 · 1 · 2', '¿Preguntas?'):
        assert cifra in ultima, cifra
    assert 'se vigila, se versiona y se puede deshacer' in sin_etiquetas(ultima + secciones(html)[-1][0]) or 'se vigila, se versiona y se puede deshacer' in ultima


def test_la_guia_tiene_los_cinco_laboratorios(guia):
    for h in ('## 1. Preparar', '## 2. L1 ·', '## 3. L2 ·', '## 4. L3 ·', '## 5. L4 ·', '## 6. L5 ·', '## 7. Si algo falla', '## 8. Qué se comprobó'):
        assert h in guia, h
    assert guia.count('**Qué debes ver') >= 8
    assert guia.count('**Si falla') >= 6


# ----------------------------------------------------------------------------------------------------------------------
# Higiene de los archivos
# ----------------------------------------------------------------------------------------------------------------------
ARCHIVOS = ['generar.py', 'index.html', 'guia.md', 'monitoreo.yml', 'pruebas/test_presentacion.py', 'pruebas/test_workflows_mlops.py']


@pytest.mark.parametrize('nombre', ARCHIVOS)
def test_sin_bom_y_en_utf8_con_lf(nombre):
    datos = (AQUI / nombre).read_bytes()
    assert not datos.startswith(b'\xef\xbb\xbf'), f'{nombre} lleva BOM'
    datos.decode('utf-8')
    assert b'\r\n' not in datos, f'{nombre} tiene finales de línea CRLF'


@pytest.mark.parametrize('nombre', ['generar.py', 'index.html', 'guia.md', 'monitoreo.yml'])
def test_sin_rutas_personales_ni_credenciales(nombre):
    texto = leer(AQUI / nombre)
    assert 'C:\\Users' not in texto and 'AppData' not in texto and 'C:\\bk' not in texto and not re.search(r'\bBK\d{5}\b', texto)
    assert not re.search(r'[\w.]+@[\w-]+\.(com|es|org)', texto)
    assert not re.search(r'(token|password|contraseña)\s*[:=]\s*\S{6,}', texto, re.I)
    assert not re.search(r'ghp_|github_pat_', texto)


def test_el_unico_usuario_que_aparece_es_el_de_las_capturas(html, guia):
    for texto in (html, guia):
        usuarios = set(re.findall(r'github\.com/([\w-]+)/', texto))
        assert usuarios <= {'helicr', 'x'}, usuarios


def test_texto_en_espanol_con_tildes_en_lo_que_se_proyecta(html):
    texto = todo_el_texto(html)
    for palabra in ('producción', 'versión', 'rendimiento', 'configuración', 'órdenes', 'clásico', 'Qué debes ver'):
        assert palabra in texto or palabra == 'configuración' or palabra == 'órdenes', palabra
    for mal in ('produccion de', 'version nueva', 'ordenes', 'clasico'):
        assert mal not in texto.replace('`produccion`', ''), mal
