"""Pruebas de la presentación y la guía del «Laboratorio de cierre de S4: producción e2e» (sin navegador).

Qué vigilan: que index.html está al día con generar.py; entre 20 y 26 diapositivas, cada una con título, parte, minutos y notas,
con antetítulo numerado por partes; que todas las capturas citadas existen (y no sobra ninguna); sin recursos externos, sin
movimiento al pasar el ratón y con el botón «⌂ S4»; que las órdenes de la presentación están en guia.md y citan archivos y
ramas que existen y coinciden con los workflows; que las cifras de los runs coinciden entre presentación, guía y capturas;
que las siglas están explicadas; que el cierre tiene un mensaje y cuatro tarjetas; y que ningún archivo lleva BOM, rutas
personales ni secretos.
El archivo se llama test_presentacion.py para no chocar con test_nueva_version.py y compañía.
"""
import importlib.util
import re
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parents[1]
RAIZ = AQUI.parents[2]
GUIA = AQUI / 'guia.md'
CONFIGURAR = AQUI / 'CONFIGURAR-REPOSITORIO.md'
CODESPACE = AQUI / 'CODESPACE.md'

_spec = importlib.util.spec_from_file_location('generar_produccion_e2e', AQUI / 'generar.py')
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


# ----------------------------------------------------------------------------------------------------------------------
# Estructura de la presentación
# ----------------------------------------------------------------------------------------------------------------------
def test_esta_al_dia_con_el_generador(html):
    assert html == G.html_completo(), 'index.html no coincide con generar.py: ejecuta  python generar.py'


def test_entre_20_y_26_diapositivas_cada_una_con_titulo_parte_minutos_y_notas(html):
    s = secciones(html)
    assert 20 <= len(s) <= 26, len(s)
    for attrs, cuerpo in s:
        assert re.search(r'data-part="[A-G]"', attrs), attrs
        m = re.search(r'data-min="(\d+)"', attrs)
        assert m and int(m.group(1)) > 0, attrs
        t = re.search(r'data-title="([^"]+)"', attrs)
        assert t and t.group(1).strip(), attrs
        n = re.search(r'data-notes="([^"]*)"', attrs)
        assert n and len(n.group(1)) > 80, f'notas demasiado cortas en {t.group(1)}'
        assert cuerpo.count('<h1>') == 1


def test_antetitulos_numerados_por_partes(html):
    s = secciones(html)
    letras = list(G.PARTES)
    for attrs, cuerpo in s:
        parte = re.search(r'data-part="([A-G])"', attrs).group(1)
        kick = re.search(r'<p class="kick">(.*?)</p>', cuerpo).group(1)
        assert kick.startswith(f'{letras.index(parte) + 1} · '), kick
    # las partes aparecen en orden y todas tienen al menos una diapositiva
    orden = [re.search(r'data-part="([A-G])"', a).group(1) for a, _ in s]
    assert orden == sorted(orden)
    assert set(orden) == set(G.PARTES)


def test_pie_con_posicion_x_de_total_y_una_boton_por_parte(html):
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


def test_boton_s4_al_indice_de_la_sesion(html):
    assert '<a id="bhome" href="../index.html"' in html and '⌂ S4' in html
    assert (AQUI.parent / 'index.html').exists()


def test_marco_de_los_laboratorios_de_s3_zoom_con_clic_esc_y_flechas(html):
    for clave in ("k==='Escape'", "k==='ArrowRight'", "k==='ArrowLeft'", 'id="zoombox"', 'cursor:zoom-in', 'data-src="img/'):
        assert clave in html, clave


# ----------------------------------------------------------------------------------------------------------------------
# Capturas
# ----------------------------------------------------------------------------------------------------------------------
def test_todas_las_capturas_citadas_existen_y_no_sobra_ninguna(html):
    citadas = set(re.findall(r'(?:src|data-src)="img/([^"]+)"', html))
    assert not re.search(r'data-falta=', html)
    assert citadas == set(G.CAPTURAS), 'cada captura prevista debe salir en alguna diapositiva y viceversa'
    for nombre in citadas:
        assert nombre.endswith('.webp'), nombre
        f = AQUI / 'img' / nombre
        assert f.exists() and f.stat().st_size > 5000, nombre
        assert f.read_bytes()[:4] == b'RIFF' and f.read_bytes()[8:12] == b'WEBP', nombre
    assert 'Captura pendiente' not in html
    en_disco = {p.name for p in (AQUI / 'img').glob('*.webp')}
    assert en_disco == set(G.CAPTURAS), en_disco ^ set(G.CAPTURAS)


def test_las_capturas_obligatorias_estan_previstas():
    esperadas = ({f'cfg-0{i}' for i in range(1, 5)} | {f'gh-0{i}' for i in (1, 2, 3, 4, 5, 6, 7, 8)}
                 | {'gh-10', 'gh-11', 'gh-12', 'gh-13'} | {f'panel-{i}' for i in range(1, 6)})
    previstas = {n.rsplit('.', 1)[0] for n in G.CAPTURAS}
    assert {p for p in previstas if any(p.startswith(e) for e in esperadas)} == previstas
    for e in esperadas:
        assert any(p.startswith(e) for p in previstas), e


def test_cada_captura_tiene_texto_alternativo_con_contenido(html):
    for nombre, alt in G.CAPTURAS.items():
        assert len(alt) > 40, nombre
        assert f'alt="{G.esc(alt)}"' in html, nombre


def test_la_guia_y_el_configurar_citan_capturas_que_existen(guia):
    for texto in (guia, CONFIGURAR.read_text(encoding='utf-8')):
        for ruta in re.findall(r'\]\((img/[^)]+)\)', texto):
            assert (AQUI / ruta).exists(), ruta


def test_varias_capturas_en_una_sola_diapositiva_donde_tiene_sentido(html):
    por_slide = [len(re.findall(r'<figure class="cap"', c)) for _, c in secciones(html)]
    assert max(por_slide) >= 4          # los cuatro ajustes de GitHub, en una sola diapositiva
    assert sum(1 for n in por_slide if n >= 2) >= 5
    assert sum(por_slide) == len(G.CAPTURAS)


def test_la_nota_de_la_captura_de_rechazo_esta_en_su_pie_y_es_fiel_al_codigo(html, guia):
    assert G.NOTA_GH13 in html.replace('&#x27;', "'") or 'se hizo antes de corregir el texto' in html
    pie = re.search(r'gh-13-nueva-rechazada\.webp".*?</figure>', html, re.S).group(0)
    assert 'antes de corregir el texto' in pie and 'empeora más que la tolerancia de -0.1' in pie and '+0.0485' in pie
    assert 'no mejora lo exigido (al menos +0.1, tolerancia de -0.1). No se publica.' in pie
    assert 'antes de corregir el texto' in guia
    codigo = (RAIZ / '04-Proyecto-Base' / 'ia_mlops' / 'produccion.py').read_text(encoding='utf-8')
    assert "no mejora lo exigido (al menos {-tolerancia:+g}, tolerancia de {tolerancia:g}). No se publica." in codigo


def test_la_captura_de_aprobacion_avisa_de_que_es_otro_run_del_mismo_escenario(html, guia):
    pie = re.search(r'gh-01-esperando-aprobacion\.webp".*?</figure>', html, re.S).group(0)
    assert 'run nº 3' in pie and 'nº 5' in pie
    assert 'run nº 3' in guia


# ----------------------------------------------------------------------------------------------------------------------
# Órdenes, ramas y workflows
# ----------------------------------------------------------------------------------------------------------------------
def test_cada_orden_de_terminal_tiene_su_boton_de_copiar_y_esta_en_la_guia(html, guia):
    for clave, orden in G.O.items():
        assert f'data-t="{G.esc(orden)}"' in html, f'{clave}: la orden no sale en ninguna diapositiva'
        assert orden in guia, f'{clave}: la orden no está en guia.md'


def test_las_ordenes_citan_archivos_y_carpetas_que_existen():
    assert (RAIZ / G.CARPETA).is_dir() and G.CARPETA == AQUI.relative_to(RAIZ).as_posix()
    for w in G.WORKFLOWS:
        assert (AQUI / w).is_file(), w
        assert w.rsplit('.', 1)[0] in G.O['cp'], w
    assert G.O['cp'].startswith(f'cp {G.CARPETA}/{{')
    assert (RAIZ / '04-Proyecto-Base' / 'deploy' / 'docker' / 'compose-produccion.yaml').is_file()
    assert (RAIZ / '04-Proyecto-Base' / 'models' / 'referencia.json').is_file()
    for modulo in ('operacional', 'pipeline', 'explotacion'):
        assert (RAIZ / '04-Proyecto-Base' / 'ia_mlops' / f'{modulo}.py').is_file(), modulo
        assert f'python -m ia_mlops.{modulo}' in G.O.values()


def test_las_ramas_de_ensayo_disparan_los_workflows_correspondientes():
    nv = (AQUI / 'nueva-version.yml').read_text(encoding='utf-8')
    rb = (AQUI / 'rollback.yml').read_text(encoding='utf-8')
    pl = (AQUI / 'puntuar-lote.yml').read_text(encoding='utf-8')
    vp = (AQUI / 'validar-produccion.yml').read_text(encoding='utf-8')
    assert "branches: ['lab/nueva-version/**']" in nv and "branches: ['lab/rollback/**']" in rb
    assert "branches: ['lab/**']" in pl and "branches: ['lab/**']" in vp
    for clave in ('muestra_push', 'rechazo_push', 'completo_push'):
        assert G.O[clave].startswith('git push -u origin lab/nueva-version/')
    for clave in ('rb1_push', 'rb2_push'):
        assert G.O[clave].startswith('git push -u origin lab/rollback/')
    # el nombre de la rama elige el escenario, tal como lo leen los workflows
    assert "contains(github.ref_name, 'completo')" in nv and "contains(github.ref_name, 'rechazo')" in nv and "'-0.10'" in nv
    assert 'completo-rechazo' in G.O['rechazo_rama'] and G.O['completo_rama'].endswith('lab/nueva-version/completo')
    assert G.O['muestra_rama'].endswith('lab/nueva-version/muestra')
    assert "contains(github.ref_name, 'sin-comprobar')" in rb and 'sin-comprobar' in G.O['rb2_rama']
    assert 'sin-comprobar' not in G.O['rb1_rama']
    # el primer push de la rama base lanza el lote y la validación (cambia su propio YAML)
    assert "'.github/workflows/puntuar-lote.yml'" in pl and "'.github/workflows/validar-produccion.yml'" in vp
    assert G.O['push'] == f'git push -u origin {G.RAMA_BASE}' and G.RAMA_BASE.startswith('lab/')


def test_el_grupo_de_concurrency_compartido_y_el_working_directory_de_publicar():
    nv = (AQUI / 'nueva-version.yml').read_text(encoding='utf-8')
    rb = (AQUI / 'rollback.yml').read_text(encoding='utf-8')
    assert 'group: nueva-version-modelo' in nv and 'group: nueva-version-modelo' in rb
    publicar = nv[nv.index('  publicar:'):nv.index('  referencia:')]
    assert 'working-directory: .' in publicar
    assert 'environment:' in publicar and 'produccion' in publicar


def test_el_cron_y_las_entradas_del_lote_son_los_de_la_presentacion(html, guia):
    pl = (AQUI / 'puntuar-lote.yml').read_text(encoding='utf-8')
    assert "cron: '17 5 * * *'" in pl
    for texto in (html, guia):
        assert '05:17 UTC' in texto
    for entrada in ('capacidad', 'corte', 'imagen'):
        assert f'      {entrada}:' in pl


def test_los_endpoints_citados_existen_en_la_interfaz():
    app = (RAIZ / '04-Proyecto-Base' / 'ia_mlops' / 'interfaz' / 'app.py').read_text(encoding='utf-8')
    for ruta in ("'/bajo-demanda/{cliente_id}'", "'/bajo-demanda'", "'/online/{cliente_id}'", "'/demo/compra'", "'/demo/reiniciar'", "'/listo'"):
        assert ruta in app, ruta
    panel = (RAIZ / '04-Proyecto-Base' / 'ia_mlops' / 'interfaz' / 'panel.py').read_text(encoding='utf-8')
    assert "'/panel'" in panel and "'/panel/versiones'" in panel
    assert '"8090:8090"' in (RAIZ / '04-Proyecto-Base' / 'deploy' / 'docker' / 'compose-produccion.yaml').read_text(encoding='utf-8')


def test_la_tolerancia_por_defecto_es_la_de_config_y_la_ficha_es_la_v1():
    cfg = (RAIZ / '04-Proyecto-Base' / 'ia_mlops' / 'config.py').read_text(encoding='utf-8')
    assert re.search(r'^TOLERANCIA_COMPARACION = 0\.02$', cfg, re.M)
    ficha = (RAIZ / '04-Proyecto-Base' / 'models' / 'referencia.json').read_text(encoding='utf-8')
    assert 'retencion-api:v1-35a94deb4e04ab4a' in ficha and '0.7470928' in ficha


# ----------------------------------------------------------------------------------------------------------------------
# Contenido obligatorio y cifras
# ----------------------------------------------------------------------------------------------------------------------
def test_los_tres_modos_y_el_panel_estan_en_la_presentacion_y_en_la_guia(html, guia):
    texto = todo_el_texto(html)
    for clave in ('puntuación por lotes', 'Bajo demanda', 'Online', 'schedule', 'Run workflow', 'Lote', 'Versiones',
                  '/bajo-demanda', '/online', 'fs_produccion', '8090', 'compra simulada'):
        assert clave.lower() in texto.lower(), clave
        assert clave.lower() in guia.lower(), clave


def test_configuracion_del_repositorio_con_los_textos_de_github(html, guia):
    texto = todo_el_texto(html)
    for clave in ('Settings', 'Environments', 'New environment', 'Required reviewers', 'Save protection rules', 'Workflow permissions',
                  'Allow GitHub Actions to create and approve pull requests'):
        assert clave in texto, clave
        assert clave in guia, clave
    assert 'activar' in texto.lower() and 'fork' in texto.lower()


def test_paso_de_aprobacion_y_fusion_con_los_textos_verificados(html, guia):
    texto = todo_el_texto(html)
    for clave in ('helicr requested your review to deploy to produccion', 'Review deployments', 'Approve and deploy',
                  'Merge pull request', 'Confirm merge', 'Referencia del modelo: v2-3521a0421905ba28', 'referencia/v2-45030152194'):
        assert clave in texto, clave
        assert clave in guia, clave


def test_las_cifras_de_los_runs_coinciden_en_presentacion_y_guia(html, guia):
    texto = todo_el_texto(html)
    cifras = ['45026646958', '45026646944', '45027468464', '45027468487', '45030152194', '45041023548', '45041634741',
              '55 s', '111 s', '4 s', '133 s', '64 s', '3 m 53 s', '191 s', '138 s', '17 s', '14 s', '10 s', '16 s',
              '0,7956', '0,7471', '+0,0485', 'v2-3521a0421905ba28', 'v1-35a94deb4e04ab4a', '148', '2011-12-10',
              '79,9 %', '76,2 %', '12670', '26,8 ms', '33,5 ms']
    for c in cifras:
        assert c in texto, c
    for c in ('45026646958', '45026646944', '45027468464', '45027468487', '45030152194', '45041023548', '45041634741',
              '55 s', '111 s', '133 s', '64 s', '3 m 53 s', '191 s', '138 s', '17 s', '14 s', '10 s', '16 s', '0,7956', '0,7471',
              '+0,0485', '79,9 %', '76,2 %', '12670', '26,8 ms', '33,5 ms', 'PR nº 3', 'PR nº 2'):
        assert c in guia, c
    assert G.RUN == {'lote': '45026646958', 'validar': '45026646944', 'igual': '45027468464', 'rechazo': '45027468487',
                     'completo': '45030152194', 'rollback_rojo': '45041023548', 'rollback_verde': '45041634741'}


def test_la_suma_de_los_trabajos_de_la_v2_es_la_del_cierre(html):
    assert 191 + 138 + 17 + 14 == 360        # 6 min
    assert '191 s + 138 s + 17 s + 14 s' in sin_etiquetas(secciones(html)[-1][1])


def test_los_mensajes_de_si_falla_estan_en_presentacion_y_guia(html, guia):
    texto = todo_el_texto(html)
    for clave in ('esperando aprobación bloquea', 'nueva-version-modelo', 'No such file or directory', 'working-directory: .',
                  'sin revisores', 'Allow GitHub Actions to create and approve pull requests'):
        assert clave in texto, clave
    for clave in ('bloquea', 'nueva-version-modelo', 'No such file or directory', 'working-directory: .', 'sin revisores'):
        assert clave in guia, clave


def test_el_rollback_explica_los_dos_intentos(html, guia):
    texto = todo_el_texto(html)
    for t in (texto, guia):
        assert 'La imagen no está en GHCR' in t
        assert 'ghcr.io/helicr/retencion-api:v1-35a94deb4e04ab4a' in t
        assert 'nunca se publicó' in t
        assert 'retirada' in t and 'sin-comprobar' in t
        assert 'No se borra nada' in t or 'no borra' in t.lower()


def test_las_siglas_estan_explicadas(html):
    texto = todo_el_texto(html)
    for sigla, explicacion in (('GHCR', 'GitHub Container Registry'), ('PR', 'pull request'), ('environment', 'reglas de protección'),
                               ('huella', 'resumen corto de los datos'), ('AUC', 'área bajo la curva ROC'),
                               ('tolerancia', 'cuánto puede'), ('campeón', 'versión nueva que aspira a sustituirlo')):
        assert sigla in texto and explicacion in texto, sigla


def test_cierre_con_un_mensaje_y_cuatro_tarjetas_con_cifras_reales(html):
    ultima = secciones(html)[-1][1]
    assert ultima.count('class="msg"') == 1
    assert ultima.count('class="card kpi"') == 4
    for cifra in ('0,7471', '0,7956', '79,9 %', '76,2 %', '6 min', '16 s'):
        assert cifra in ultima, cifra


def test_lo_no_verificado_esta_dicho_y_no_se_inventan_cifras(html, guia):
    texto = todo_el_texto(html)
    assert 'sin dato' in texto.lower() and 'Sin verificar' in texto
    assert 'sin dato' in guia.lower() and 'Sin verificar' in guia
    assert 'sin verificar en codespace' in texto.lower()
    for t in (texto, guia):
        assert 'no en red' in t


def test_el_codespace_md_sigue_sin_verificar_y_no_se_ha_tocado_su_estado():
    assert 'sin verificar en Codespace' in CODESPACE.read_text(encoding='utf-8')


# ----------------------------------------------------------------------------------------------------------------------
# CONFIGURAR-REPOSITORIO.md
# ----------------------------------------------------------------------------------------------------------------------
def test_configurar_repositorio_recoge_lo_verificado_y_las_capturas_cfg():
    t = CONFIGURAR.read_text(encoding='utf-8')
    for n in ('cfg-01-environments', 'cfg-02-environment-revisores', 'cfg-03-actions-permisos', 'cfg-04-workflow-permissions'):
        assert f'img/{n}.webp' in t, n
    for clave in ('helicr requested your review to deploy to produccion', 'Review deployments', 'Approve and deploy', 'Save protection rules',
                  'Allow GitHub Actions to create and approve pull requests', '1 protection rule', '45027468464'):
        assert clave in t, clave
    # lo que ya está verificado no puede seguir marcado como «sin verificar»
    assert 'Esos textos exactos están **sin verificar**' not in t
    assert 'no se ha verificado todavía en Actions' not in t
    assert 'verificado el 22/11/2026' in t.lower() or 'verificados el 22/11/2026' in t.lower()


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
    texto = (AQUI / nombre).read_text(encoding='utf-8')
    assert 'C:\\Users' not in texto and 'AppData' not in texto and not re.search(r'\bBK\d{5}\b', texto)
    assert not re.search(r'[\w.]+@[\w-]+\.(com|es|org)', texto)
    assert not re.search(r'(token|password|contraseña)\s*[:=]\s*\S{6,}', texto, re.I)
    assert not re.search(r'ghp_|github_pat_', texto)


def test_el_unico_usuario_que_aparece_es_el_de_las_capturas(html, guia):
    for texto in (html, guia):
        usuarios = set(re.findall(r'github\.com/([\w-]+)/', texto)) | set(re.findall(r'ghcr\.io/([\w-]+)/', texto))
        assert usuarios <= {'helicr'}, usuarios


def test_texto_en_espanol_con_tildes_en_lo_que_se_proyecta(html):
    texto = todo_el_texto(html)
    for palabra in ('producción', 'versión', 'aprobación', 'configuración', 'imagen'):
        assert palabra in texto, palabra
    for mal in ('produccion de', 'version nueva', 'aprobacion '):
        assert mal not in texto.replace('`produccion`', ''), mal
