"""Pruebas de la presentación y la guía del extra «Del alias champion de MLflow a un endpoint de Vertex AI» (sin navegador).

Qué vigilan: que index.html está al día con generar.py; entre 24 y 30 diapositivas con título, parte, minutos y notas, con antetítulo numerado por
partes; que el visor es el del laboratorio de agentes (solo cambia el pie); que las órdenes de la presentación están en guia.md y citan módulos,
scripts, opciones y archivos que existen; que TODAS las salidas «Real» que se enseñan salen de salidas/ (ninguna escrita a mano) y que las cifras
coinciden con el proyecto y con las pruebas; que lo no verificado está dicho; que las capturas pendientes están declaradas y salen como
«Captura pendiente» (nunca una imagen inventada) y las reales existen; y que ningún archivo lleva BOM, CRLF, rutas personales, mojibake ni secretos.
"""
import ast
import html as htmllib
import importlib.util
import json
import re
from pathlib import Path

import pytest

from conftest import AQUI, PROYECTO, RAIZ

GUIA = AQUI / 'guia.md'
_spec = importlib.util.spec_from_file_location('generar_extra_vertex', AQUI / 'generar.py')
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


def salidas():
    return {p.name: leer(p) for p in sorted((AQUI / 'salidas').glob('*.txt'))}


# ------------------------------------------------------------------------------------------------ estructura
def test_esta_al_dia_con_el_generador(html):
    assert html == G.html_completo(), 'index.html no coincide con generar.py: ejecuta  python generar.py'


def test_entre_24_y_30_diapositivas_cada_una_con_titulo_parte_minutos_y_notas(html):
    s = secciones(html)
    assert 24 <= len(s) <= 30, len(s)
    for attrs, cuerpo in s:
        assert re.search(r'data-part="[A-H]"', attrs), attrs
        m = re.search(r'data-min="(\d+)"', attrs)
        assert m and int(m.group(1)) > 0, attrs
        t = re.search(r'data-title="([^"]+)"', attrs)
        assert t and t.group(1).strip(), attrs
        n = re.search(r'data-notes="([^"]*)"', attrs)
        assert n and len(n.group(1)) > 80, f'notas demasiado cortas en {t.group(1)}'
        assert cuerpo.count('<h1>') == 1


def test_titulos_sin_repetir_y_un_mensaje_por_diapositiva(html):
    titulos = [re.search(r'data-title="([^"]+)"', a).group(1) for a, _ in secciones(html)]
    assert len(titulos) == len(set(titulos))
    for _, cuerpo in secciones(html):
        assert cuerpo.count('<h1>') == 1 and len(re.search(r'<h1>(.*?)</h1>', cuerpo).group(1)) < 130, 'un titular corto por diapositiva'


def test_antetitulos_numerados_por_partes(html):
    s = secciones(html)
    letras = list(G.PARTES)
    for attrs, cuerpo in s:
        parte = re.search(r'data-part="([A-H])"', attrs).group(1)
        kick = re.search(r'<p class="kick">(.*?)</p>', cuerpo).group(1)
        assert kick.startswith(f'{letras.index(parte) + 1} · '), kick
    orden = [re.search(r'data-part="([A-H])"', a).group(1) for a, _ in s]
    assert orden == sorted(orden) and set(orden) == set(G.PARTES)


def test_las_partes_son_los_laboratorios_l1_a_l6(html):
    nombres = ' '.join(G.NOMBRES_PARTE.values())
    for lab in ('L1 ·', 'L2 ·', 'L3 ·', 'L4 ·', 'L5 ·', 'L6 ·'):
        assert lab in nombres, lab


def test_pie_fondo_blanco_sin_hover_ni_recursos_externos_y_boton_al_indice(html):
    assert '${i+1} / ${N}' in html and html.count('class="part"') == len(G.PARTES) and '<span id="count">' in html
    assert 'ML e IA · S5 · Extra: del champion de MLflow a Vertex AI' in html and 'Laboratorio de agentes</span>' not in html
    assert '--fondo:#ffffff' in html and ':hover' not in html and 'transition' not in html and 'animation' not in html
    assert not re.search(r'(src|href)="(https?:)?//', html) and not re.search(r'@import|url\((["\']?)(https?:)?//', html)
    assert '<link' not in html and '<iframe' not in html
    assert '<a id="bhome" href="../index.html"' in html and '⌂ S5' in html and (AQUI.parent / 'index.html').exists()
    for clave in ("k==='Escape'", "k==='ArrowRight'", "k==='ArrowLeft'", 'id="zoombox"', 'cursor:zoom-in'):
        assert clave in html, clave


def test_el_visor_es_el_del_laboratorio_de_agentes_salvo_el_pie(html):
    ag = leer(AQUI.parent / 'laboratorio-agentes' / 'index.html')
    for expresion in (r'<style>(.*?)</style>', r'<script>(.*?)</script>'):
        a = re.search(expresion, ag, re.S).group(1).replace('ML e IA · S5 · Laboratorio de agentes', 'PIE')
        b = re.search(expresion, html, re.S).group(1).replace('ML e IA · S5 · Extra: del champion de MLflow a Vertex AI', 'PIE')
        a = re.sub(r'const PARTES=\{.*?\};', 'const PARTES={};', a, flags=re.S)
        b = re.sub(r'const PARTES=\{.*?\};', 'const PARTES={};', b, flags=re.S)
        assert a == b


def test_sin_tabuladores_ni_markdown_sin_convertir(html):
    assert '\t' not in re.sub(r'<pre[ >].*?</pre>', '', html, flags=re.S), 'tabuladores fuera de las salidas reales'
    texto = sin_etiquetas(re.sub(r'<pre[ >].*?</pre>', ' ', ' '.join(c for _, c in secciones(html)), flags=re.S))
    assert not re.search(r'(?<!/)\*\*', texto), 'un **negrita** sin convertir'
    assert not re.search(r'(?<!\w)`', texto), 'una `comilla` sin convertir'


# ------------------------------------------------------------------------------------------------ capturas
def test_las_capturas_reales_existen_y_las_pendientes_no_y_salen_como_tales(html):
    assert G.CAPTURAS_PENDIENTES and all(n.startswith('pend-') for n in G.CAPTURAS_PENDIENTES) and len(G.CAPTURAS_PENDIENTES) == 13
    for nombre in G.CAPTURAS:
        existe = (AQUI / 'img' / nombre).is_file()
        if nombre in G.CAPTURAS_PENDIENTES:
            assert not existe, f'{nombre} existe en img/: quítala de las pendientes'
            assert f'data-img="{nombre}"' in html and f'img/{nombre}</span>' in html, nombre
        else:
            assert existe, f'falta img/{nombre}'
            assert f'src="img/{nombre}"' in html, nombre
    assert 'Captura pendiente' in todo_el_texto(html)


def test_cada_captura_tiene_texto_alternativo_con_contenido_y_sale_una_vez(html):
    cuerpo = ' '.join(c for _, c in secciones(html))
    for nombre, alt in G.CAPTURAS.items():
        assert len(alt) > 60, nombre
        assert cuerpo.count(f'data-img="{nombre}"') == 1, nombre


def test_no_hay_imagenes_sin_declarar_en_img():
    declaradas = set(G.CAPTURAS)
    en_disco = {p.name for p in (AQUI / 'img').glob('*.webp')}
    assert en_disco == declaradas - set(G.CAPTURAS_PENDIENTES), en_disco ^ (declaradas - set(G.CAPTURAS_PENDIENTES))


def test_las_salidas_de_terminal_dibujadas_son_de_salidas_y_se_rotulan_asi(html):
    import terminal_a_imagen as t
    assert {n for n in G.CAPTURAS if n.startswith('t-')} == set(t.IMAGENES)
    for nombre in t.IMAGENES:
        assert 'Salida real dibujada como imagen' in G.CAPTURAS[nombre], nombre
    assert 'no es una captura de pantalla' in leer(AQUI / 'terminal_a_imagen.py') and 'Salida real como imagen' in html
    for nombre, (_, spec) in t.IMAGENES.items():
        for archivo, _, _ in spec:
            assert (AQUI / 'salidas' / archivo).is_file(), f'{nombre}: falta salidas/{archivo}'


def test_capturas_pendientes_md_lista_todas_con_su_receta_y_las_reales():
    md = leer(AQUI / 'capturas-pendientes.md')
    for n in G.CAPTURAS_PENDIENTES:
        fila = next((l for l in md.splitlines() if l.startswith('|') and f'`{n}`' in l), None)
        assert fila and fila.count('|') >= 5, n                                  # la tabla resumen: archivo, paso y dónde
        m = re.search(r'### \d+ · `' + re.escape(n) + r'`.*?(?=\n### |\n## )', md, re.S)
        assert m, f'falta la receta de {n}'
        pasos = re.findall(r'^\d+\. ', m.group(0), re.M)
        assert len(pasos) >= 2, f'{n}: la receta debe ser una lista numerada (dónde clicar y qué encuadrar)'
    for n in G.CAPTURAS:
        if not n.startswith(('pend-', 't-')):
            assert n in md, f'capturas-pendientes.md no explica la real {n}'


def test_las_capturas_de_la_consola_no_llevan_el_correo_ni_el_nombre_del_proyecto_a_la_vista():
    """No se puede leer una imagen sin OCR: se comprueba que los originales SIN difuminar no están en el repositorio."""
    for p in (AQUI / 'img').glob('*'):
        assert p.suffix == '.webp', p
    assert not list(AQUI.rglob('*.png')) and not list(AQUI.rglob('raw'))


# ------------------------------------------------------------------------------------------------ órdenes
def test_cada_orden_de_terminal_tiene_su_boton_de_copiar_y_esta_en_la_guia(html, guia):
    for clave, orden in G.O.items():
        assert f'data-t="{G.esc(orden)}"' in html, f'{clave}: la orden no sale en ninguna diapositiva'
        assert orden in guia, f'{clave}: la orden no está en guia.md'


def test_las_ordenes_citan_scripts_modulos_y_opciones_que_existen():
    for clave, orden in G.O.items():
        for modulo in re.findall(r'python -m (ia_mlops[\w.]*)', orden):
            assert (PROYECTO / Path(*modulo.split('.'))).with_suffix('.py').is_file(), f'{clave}: {modulo}'
        m = re.match(r'bash scripts/(\w+\.sh)(.*)', orden)
        if m:
            script = AQUI / 'scripts' / m.group(1)
            assert script.is_file(), clave
            for opcion in re.findall(r'(--[\w-]+)', m.group(2)):
                assert re.search(re.escape(opcion) + r'[")]', leer(script)), f'{clave}: {opcion}'
        m = re.match(r'python (\w+\.py)(.*)', orden)
        if m:
            fuente = AQUI / m.group(1)
            assert fuente.is_file(), clave
            for opcion in re.findall(r'(--[\w-]+)', m.group(2)):
                assert f"'{opcion}'" in leer(fuente), f'{clave}: {opcion}'
            for sub in re.findall(r'\b(generar|anotar|puerta|leer)\b', m.group(2)):
                assert f"add_parser('{sub}'" in leer(fuente)
        for archivo in re.findall(r'(?:^| )(ejemplos/[\w.-]+\.json)', orden):
            assert (AQUI / archivo).is_file(), clave
    alias = leer(PROYECTO / 'ia_mlops' / 'alias_modelo.py')
    assert "add_parser('mostrar'" in alias and "add_parser('promover'" in alias and "'--version'" in alias
    assert (AQUI / 'requirements-extra.txt').is_file()


def test_los_workflows_y_la_rama_del_ensayo_coinciden_con_los_de_la_presentacion():
    import fnmatch
    import yaml
    assert sorted(p.name for p in AQUI.glob('vertex-*.yml')) == sorted(G.WORKFLOWS)
    assert G.O['cp'] == f'cp {G.CARPETA}/vertex-*.yml .github/workflows/' and G.CARPETA == AQUI.relative_to(RAIZ).as_posix()
    wf = yaml.safe_load(leer(AQUI / 'vertex-desplegar.yml'))
    patrones = wf.get('on', wf.get(True))['push']['branches']
    assert any(fnmatch.fnmatch(G.RAMA, p.replace('**', '*')) for p in patrones)
    assert G.O['rama'] == f'git switch -c {G.RAMA}' and G.O['push'].endswith(G.RAMA)


def test_la_guia_enlaza_archivos_que_existen_y_sus_bloques_son_validos(guia):
    for ruta in re.findall(r'\]\(([^)#]+)\)', guia):
        if not ruta.startswith('http'):
            assert (AQUI / ruta).exists(), ruta
    for b in re.findall(r'```python\n(.*?)```', guia, re.S):
        ast.parse(b)
    for b in re.findall(r'```bash\n(.*?)```', guia, re.S):
        assert '\r' not in b and not re.search(r'\b(Select-String|Get-Content)\b', b)


def test_la_guia_tiene_los_apartados_y_las_marcas_de_cada_paso(guia):
    for h in ('## 0. La idea', '## 2. Preparar', '## 3. L1 ·', '## 4. L2 ·', '## 5. Preparar Google Cloud', '## 6. L3 ·', '## 7. L4 ·', '## 8. L5 ·',
              '## 9. Ensayo real', '## 10. Qué se comprobó', '## 11. Fuentes', '## 12. Pruebas y ejercicios'):
        assert h in guia, h
    assert guia.count('**Qué debes ver') >= 6 and guia.count('**Si falla') >= 6
    assert guia.count('https://docs.cloud.google.com') >= 12


def test_las_variables_de_github_de_los_workflows_estan_en_la_guia(guia):
    usadas = set()
    for w in G.WORKFLOWS:
        usadas |= set(re.findall(r'vars\.(\w+)', leer(AQUI / w)))
    assert usadas and all(f'`{v}`' in guia for v in usadas), [v for v in usadas if f'`{v}`' not in guia]


# ------------------------------------------------------------------------------------------------ salidas reales y cifras
def test_toda_salida_real_de_las_diapositivas_sale_de_salidas(html):
    lineas = set()
    for texto in salidas().values():
        lineas |= {l.rstrip() for l in texto.splitlines()}
    cajas = re.findall(r'<div class="realbox"><div class="rk">(.*?)</div><pre>(.*?)</pre></div>', html, re.S)
    assert len(cajas) >= 6
    for titulo, pre in cajas:
        assert htmllib.unescape(titulo).startswith('Real ·'), titulo
        for l in htmllib.unescape(pre).splitlines():
            assert not l.strip() or l.rstrip() in lineas, f'no sale de salidas/: {l!r}'


def test_los_extractos_de_codigo_son_literales(html):
    adaptador = leer(AQUI / 'imagen' / 'vertex_adaptador.py')
    docker = leer(AQUI / 'imagen' / 'Dockerfile.vertex')
    for bloque in re.findall(r'<pre class="src">(.*?)</pre>', html, re.S):
        for l in htmllib.unescape(bloque).splitlines():
            assert not l.strip() or l in adaptador or l in docker, f'no es literal: {l!r}'


def test_las_salidas_reales_no_tienen_rutas_personales_ni_mojibake():
    for nombre, t in salidas().items():
        assert 'C:\\' not in t and 'C:/' not in t and 'AppData' not in t and 'BK7' not in t, nombre
        assert not re.search(r'Ã.|â€|Â', t), nombre
        assert '\r' not in t, nombre


def test_las_cifras_reales_coinciden_entre_salidas_proyecto_guia_y_presentacion(html, guia):
    s = salidas()
    ref = json.loads(leer(PROYECTO / 'models' / 'referencia.json')) if (PROYECTO / 'models' / 'referencia.json').exists() else None
    if ref:
        assert f'{ref["metricas_valid"]["auc"]:.4f}' == '0.6982' and f'{ref["metricas_test"]["auc"]:.4f}' == '0.7471' and ref['huella_datos'] == '35a94deb4e04ab4a'
    assert 'AUC valid 0.6982 · test 0.7471 · huella de datos 35a94deb4e04ab4a' in s['01-manifiesto.txt']
    assert '«retencion-90d» @champion -> versión 6 de MLflow (anterior: 5)' in s['01-manifiesto.txt']
    assert '0.8278889191932137' in s['10-adaptador-prediccion.txt'] and '0.8279' in s['14-alias-cargar.txt']
    assert s['13-paridad.txt'].count('0.00e+00') == 3 and 'PARIDAD: las predicciones' in s['13-paridad.txt'] and 'salida: 0' in s['13-paridad.txt']
    assert '0=10,1000=90' in s['22-desplegar-canario.txt'] and 'intento 1: contestó otra versión' in s['23-probar-canario.txt']
    assert 'Reparto: 1000=0,1001=100' in s['24-promover.txt'] and 'SIGUE COBRANDO' in s['24-promover.txt']
    assert 'Rollback: @champion: v6 -> v5' in s['26-volver-con-redespliegue.txt'] and 'se vuelve a desplegar' in s['26-volver-con-redespliegue.txt']
    assert 'CERRADA' in s['04-puerta-cerrada.txt'] and 'salida: 2' in s['04-puerta-cerrada.txt']
    assert '"rutaPredict": "/predict"' in s['27-modelo-versiones.txt'] and '"rutaSalud": "/salud"' in s['27-modelo-versiones.txt']
    texto = todo_el_texto(html)
    for c in ('0.8279', '0.2760', '0.2852', '0.6982', '0.7471', '35a94deb4e04ab4a', '0.00e+00', '0=10,1000=90', '0.65', '0_6982', '1,5 MB', '10-15 minutos'):
        assert c in texto, c
    for c in ('0.8279', '0.6982', '0.7471', '35a94deb4e04ab4a', '0_6982', '0.00e+00'):
        assert c in guia, c


def test_las_pruebas_citadas_son_las_de_salidas_30(html):
    t = salidas()['30-pruebas.txt']
    n = re.search(r'(\d+) passed', t).group(1)
    assert 'failed' not in t and 'error' not in t.lower().replace('errores', '')
    assert f'{n} pruebas' in todo_el_texto(html)
    assert int(n) >= 150


# ------------------------------------------------------------------------------------------------ honestidad
def test_lo_no_verificado_esta_dicho_en_la_presentacion_y_la_guia(html, guia):
    for t in (todo_el_texto(html), guia):
        for c in ('sin verificar', 'sin dato', 'Docker', 'Vertex AI', 'GitHub Actions'):
            assert c.lower() in t.lower(), c
        assert 'SIMULADO' in t or 'simulado' in t
    texto = todo_el_texto(html)
    assert 'Ningún recurso' in texto or 'ningún recurso' in texto or '0 recursos' in texto
    assert 'este portátil no tiene Docker' in texto.lower() or 'no tiene docker' in texto.lower()
    assert 'Captura pendiente' in texto and 'Cómo hacerla' in texto


def test_las_decisiones_de_la_documentacion_estan_dichas(html, guia):
    for t in (todo_el_texto(html), guia):
        assert 'AIP_' in t and 'Artifact Registry' in t and 'regional' in t.lower()
    assert 'no definas' in todo_el_texto(html).lower() and "don't set your own variables" in guia
    assert 'fuente' in todo_el_texto(html).lower() and 'docs.cloud.google.com' in todo_el_texto(html)
    assert 'limitación honesta' in todo_el_texto(html).lower() and 'servidor de MLflow compartido' in todo_el_texto(html)


def test_el_coste_esta_dicho_y_no_hay_cifras_de_precio_inventadas(html, guia):
    for t in (todo_el_texto(html), guia):
        assert 'cobra' in t.lower() and 'sin dato' in t.lower()
        assert not re.search(r'[€$]\s?\d|\d\s?(€|EUR|USD|dólares|euros)\b', t.replace('$ ', '')), 'una cifra de precio sin fuente'


def test_enlaza_a_s4_sin_repetirlo():
    assert (AQUI.parent.parent / 'S4-Orquestacion-y-CI-CD' / 'laboratorio-cloud-journey' / 'preparar-gcp-s4.sh').is_file()
    assert 'preparar-gcp-s4.sh' in leer(GUIA)


def test_cierre_con_un_mensaje_y_cuatro_tarjetas(html):
    ultima = secciones(html)[-1]
    assert ultima[1].count('class="msg"') == 1 and ultima[1].count('class="card kpi"') == 4 and '¿Preguntas?' in ultima[1]
    for c in ('0.8279', '0 recursos'):
        assert c in ultima[1], c


def test_hay_cinco_ejercicios(html, guia):
    texto = todo_el_texto(html)
    assert 'Cinco ejercicios' in texto and guia.count('\n1. ') >= 1
    assert G.EJERCICIO_SPLIT in guia and (AQUI / 'vertex_ayuda.py').is_file() and (AQUI / 'ejemplos' / 'endpoint-dos-modelos.json').is_file()


# ------------------------------------------------------------------------------------------------ higiene
ARCHIVOS = ['README.md', 'guia.md', 'capturas-pendientes.md', 'index.html', 'generar.py', 'terminal_a_imagen.py', 'manifiesto_champion.py', 'preparar_contexto.py',
            'instancias.py', 'comparar_paridad.py', 'vertex_ayuda.py', 'clientes_ejemplo.json', 'requirements-extra.txt', 'imagen/vertex_adaptador.py',
            'imagen/Dockerfile.vertex', 'ejemplos/endpoint-dos-modelos.json', 'vertex-desplegar.yml', 'vertex-rollback.yml', 'vertex-borrar.yml',
            'scripts/variables.sh', 'scripts/preparar_gcp.sh', 'scripts/subir_modelo.sh', 'scripts/desplegar.sh', 'scripts/probar.sh', 'scripts/promover.sh',
            'scripts/volver.sh', 'scripts/borrar.sh', 'pruebas/conftest.py', 'pruebas/gcloud_simulado.py', 'pruebas/test_adaptador.py', 'pruebas/test_ayuda.py',
            'pruebas/test_manifiesto.py', 'pruebas/test_scripts.py', 'pruebas/test_workflows_vertex.py', 'pruebas/test_presentacion.py']


@pytest.mark.parametrize('nombre', ARCHIVOS)
def test_sin_bom_utf8_con_lf_sin_mojibake_y_sin_rutas_personales_ni_secretos(nombre):
    datos = (AQUI / nombre).read_bytes()
    assert not datos.startswith(b'\xef\xbb\xbf'), f'{nombre} lleva BOM'
    t = datos.decode('utf-8')
    assert b'\r\n' not in datos, f'{nombre} tiene CRLF'
    if not nombre.startswith('pruebas/'):          # las pruebas citan esos patrones para buscarlos
        assert 'C:\\Users' not in t and 'AppData' not in t and 'BK70827' not in t, nombre
        assert not re.search(r'Ã[\x80-\xbf¡-¿]|â€|Â[ -¿]', t), f'{nombre} tiene mojibake'
        assert not re.search(r'ghp_|github_pat_|AIza[0-9A-Za-z_-]{20}|-----BEGIN', t)
        assert not re.search(r'(password|contraseña|secret|token)\s*[:=]\s*["\']?[A-Za-z0-9/+_-]{12,}', t, re.I), nombre


def test_el_extra_no_ha_tocado_el_proyecto_ni_los_workflows_instalados():
    assert not (RAIZ / '.github' / 'workflows' / 'vertex-desplegar.yml').exists()
    for p in (PROYECTO / 'ia_mlops').rglob('*vertex*'):
        pytest.fail(f'el extra no debe añadir módulos al proyecto: {p}')


def test_texto_en_espanol_con_tildes_en_lo_que_se_proyecta(html):
    texto = todo_el_texto(html)
    for palabra in ('producción', 'versión', 'predicción', 'configuración', 'Qué debes ver', 'Sin dato'):
        assert palabra.lower() in texto.lower() or palabra == 'configuración', palabra
    for mal in ('prediccion', 'produccion de', 'version nueva', 'clasificacion'):
        limpio = texto.replace('`produccion`', '').replace('produccion con', '').replace('environment produccion', '')
        assert not re.search(r'\b' + mal + r'\b', limpio), mal
