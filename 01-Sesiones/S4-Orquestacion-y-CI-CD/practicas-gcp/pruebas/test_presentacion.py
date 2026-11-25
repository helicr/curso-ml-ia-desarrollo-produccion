"""Pruebas de la presentación «Prácticas en Google Cloud» (index.html, hecha por generar.py). No necesitan navegador ni la nube.

Qué vigilan: que index.html está al día con generar.py; entre 25 y 30 diapositivas, cada una con título, parte, minutos y notas;
que el visor es el mismo del laboratorio Cloud Journey (zoom, Esc, ⧉ «Copiar todo», pie «x / total»); que todas las capturas
existen, son webp, se usan una vez y no llevan el banner del crédito de la prueba gratuita; que las órdenes se pueden copiar,
no usan «&&», dicen dónde se ejecutan y apuntan a carpetas y scripts que existen; que lo que dicen las diapositivas coincide con
los scripts de cada práctica (cuenta de servicio de GKE, espera de 120 s, versión de scikit-learn, modelo de Gemini...); que
las cifras reales del 25/11/2026 están y lo no verificado se marca; y que ningún archivo lleva BOM, CRLF ni datos personales.
"""
import importlib.util
import re
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location('generar_practicas_gcp', AQUI / 'generar.py')
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)


@pytest.fixture(scope='module')
def html():
    return (AQUI / 'index.html').read_text(encoding='utf-8')


def secciones(texto):
    return re.findall(r'<section class="slide[^"]*"([^>]*)>(.*?)</section>', texto, re.S)


def sin_etiquetas(texto):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', texto))


def todo_el_texto(html):
    return sin_etiquetas(' '.join(c for _, c in secciones(html)))


def leer(ruta):
    return (AQUI / ruta).read_text(encoding='utf-8')


def titulos(html):
    return [re.search(r'data-title="([^"]+)"', a).group(1) for a, _ in secciones(html)]


# ----------------------------------------------------------------------------------------------------------------------
# Estructura y visor
# ----------------------------------------------------------------------------------------------------------------------
def test_esta_al_dia_con_el_generador(html):
    assert html == G.html_completo(), 'index.html no coincide con generar.py: ejecuta  python generar.py'


def test_entre_25_y_30_diapositivas_cada_una_con_titulo_parte_minutos_y_notas(html):
    s = secciones(html)
    assert 25 <= len(s) <= 30, len(s)
    for attrs, cuerpo in s:
        assert re.search(r'data-part="[A-G]"', attrs), attrs
        m = re.search(r'data-min="(\d+)"', attrs)
        assert m and int(m.group(1)) > 0, attrs
        t = re.search(r'data-title="([^"]+)"', attrs)
        assert t and t.group(1).strip(), attrs
        n = re.search(r'data-notes="([^"]*)"', attrs)
        assert n and len(n.group(1)) > 80, f'notas demasiado cortas en {t.group(1)}'
        assert cuerpo.count('<h1>') == 1


def test_antetitulos_numerados_por_partes_y_todas_las_partes_presentes(html):
    s = secciones(html)
    letras = list(G.PARTES)
    for attrs, cuerpo in s:
        parte = re.search(r'data-part="([A-G])"', attrs).group(1)
        kick = re.search(r'<p class="kick">(.*?)</p>', cuerpo).group(1)
        assert kick.startswith(f'{letras.index(parte) + 1} · '), kick
    orden = [re.search(r'data-part="([A-G])"', a).group(1) for a, _ in s]
    assert orden == sorted(orden)
    assert set(orden) == set(G.PARTES)


def test_pie_con_posicion_x_de_total_y_un_boton_por_parte(html):
    assert '${i+1} / ${N}' in html and 'Prácticas en Google Cloud</span>' in html
    assert 'Laboratorio Cloud Journey</span>' not in html
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


def test_mismo_visor_que_el_cloud_journey_zoom_esc_flechas_y_copiar(html):
    for clave in ("k==='Escape'", "k==='ArrowRight'", "k==='ArrowLeft'", 'id="zoombox"', 'cursor:zoom-in', 'data-src="img/',
                  'Copiar todo', 'class="cp"', 'navigator.clipboard'):
        assert clave in html, clave
    cj = (AQUI.parent / 'laboratorio-cloud-journey' / 'index.html').read_text(encoding='utf-8')
    for clave in ('--fondo:#ffffff', "k==='Escape'", '.term{', '.cap figcaption', '.realbox'):
        assert clave in cj and clave in html, clave


# ----------------------------------------------------------------------------------------------------------------------
# Capturas
# ----------------------------------------------------------------------------------------------------------------------
def test_todas_las_capturas_existen_son_webp_se_usan_y_no_sobra_ninguna(html):
    citadas = re.findall(r'<img src="img/([^"]+)"', html)
    assert sorted(set(citadas)) == sorted(G.CAPTURAS), set(citadas) ^ set(G.CAPTURAS)
    assert len(citadas) == len(G.CAPTURAS), 'cada captura se usa una sola vez'
    for nombre in G.CAPTURAS:
        f = AQUI / 'img' / nombre
        assert nombre.endswith('.webp') and f.stat().st_size > 5000, nombre
        datos = f.read_bytes()
        assert datos[:4] == b'RIFF' and datos[8:12] == b'WEBP', nombre
    assert {p.name for p in (AQUI / 'img').iterdir()} == set(G.CAPTURAS)
    assert 'Captura pendiente</b>' not in html and 'class="tag warn">Pendiente' not in html


def test_cada_captura_tiene_texto_alternativo_que_dice_lo_que_se_ve(html):
    for nombre, alt in G.CAPTURAS.items():
        assert len(alt) > 100, nombre
        assert f'alt="{G.esc(alt)}"' in html, nombre


def test_las_capturas_no_llevan_el_banner_del_credito_ni_la_cabecera_de_cloud_shell():
    from PIL import Image
    for nombre in G.CAPTURAS:
        with Image.open(AQUI / 'img' / nombre) as im:
            im = im.convert('RGB')
            if nombre.startswith('cj-'):
                assert im.size == (1424, 755), (nombre, im.size)        # consola de Google Cloud con el banner recortado
            else:
                # terminal de Cloud Shell: arranca ya en el fondo oscuro (sin la barra blanca «Cloud Shell» de arriba)
                assert sum(im.getpixel((6, 4))) < 200, nombre
                assert im.width > 1300 and 90 < im.height < 900, (nombre, im.size)


# ----------------------------------------------------------------------------------------------------------------------
# Órdenes
# ----------------------------------------------------------------------------------------------------------------------
def test_cada_orden_tiene_su_boton_de_copiar_y_ninguna_usa_doble_ampersand(html):
    for clave, orden in G.O.items():
        assert f'data-t="{G.esc(orden)}"' in html, f'{clave}: la orden no sale en ninguna diapositiva'
        assert '&&' not in orden, clave
        if orden.startswith('gcloud'):
            assert not re.search(r'[áéíóúñÁÉÍÓÚÑ]', orden), clave


def test_las_ordenes_apuntan_a_carpetas_y_scripts_que_existen():
    assert G.CARPETA == '01-Sesiones/S4-Orquestacion-y-CI-CD/practicas-gcp' and AQUI.as_posix().endswith(G.CARPETA)
    assert G.O['cd_practicas'] == f'cd ~/curso/{G.CARPETA}'
    assert G.O['clonar'] == f'git clone -q --depth 1 -b develop https://github.com/$USUARIO_GH/{G.REPO}.git curso'
    for i, practica in enumerate(G.PRACTICAS, 1):
        assert G.O[f'cd_0{i}'] == f'cd ~/curso/{G.CARPETA}/{practica}'
        for s in ('crear.sh', 'probar.sh', 'borrar.sh', 'variables.sh'):
            assert (AQUI / practica / s).is_file(), f'{practica}/{s}'
    assert G.O['crear'] == 'bash crear.sh' and G.O['probar'] == 'bash probar.sh' and G.O['borrar'] == 'bash borrar.sh'
    assert (AQUI / 'borrar-todo.sh').is_file() and G.O['borrar_todo'] == 'bash borrar-todo.sh'
    assert G.O['cd_01_desde_02'] == f'cd ../{G.PRACTICAS[0]}' and (AQUI / '02-kubernetes-gke' / '..' / G.PRACTICAS[0]).resolve().is_dir()


def test_cada_terminal_dice_donde_se_ejecuta(html):
    tit = re.findall(r'<div class="bar"><em>(.*?)</em>', html)
    assert tit and all('Cloud Shell' in t for t in tit), tit
    assert 'Cloud Shell' in todo_el_texto(html) and 'la consola de Google Cloud' in todo_el_texto(html)


def test_el_orden_de_borrado_la_01_despues_de_la_02(html):
    t = titulos(html)
    assert t.index('Borrar la 2 y luego la 1') > t.index('Práctica 2: probar') > t.index('Práctica 1: probar')
    texto = todo_el_texto(html)
    assert 'No ejecutes aún' in texto and 'la práctica 2 usa esta imagen' in texto
    todo = leer('borrar-todo.sh')
    assert todo.index('01-docker-artifact-registry') > todo.index('02-kubernetes-gke')


# ----------------------------------------------------------------------------------------------------------------------
# Lo que dicen las diapositivas = lo que hacen los scripts
# ----------------------------------------------------------------------------------------------------------------------
def test_practica_1_nombres_y_servicio_privado(html):
    texto = todo_el_texto(html)
    comun = leer('comun.sh')
    assert 'NOMBRE_REPO="curso-ml-imagenes"' in comun and 'ETIQUETA_IMAGEN="v1"' in comun
    assert 'NOMBRE_SERVICIO="retencion-api-practica"' in leer('01-docker-artifact-registry/variables.sh')
    assert '--no-allow-unauthenticated' in leer('01-docker-artifact-registry/crear.sh')
    for c in ('curso-ml-imagenes', 'retencion-api:v1', 'retencion-api-practica', '403', '422', 'OK: privado'):
        assert c in texto, c


def test_practica_2_cuenta_de_servicio_de_los_nodos(html):
    texto = todo_el_texto(html)
    var, crear = leer('02-kubernetes-gke/variables.sh'), leer('02-kubernetes-gke/crear.sh')
    assert 'SA_NODOS="sa-gke-nodos"' in var
    assert 'roles/container.defaultNodeServiceAccount' in var and 'roles/artifactregistry.reader' in var
    assert '--service-account="$SA_NODOS_EMAIL"' in crear
    for c in ('sa-gke-nodos', 'roles/container.defaultNodeServiceAccount', 'roles/artifactregistry.reader', '--service-account',
              'i/o timeout', 'successfully rolled out', 'OK: 2 replicas listas otra vez.', 'ClusterIP'):
        assert c in texto, c


def test_practica_3_espera_de_120_s_y_los_fallos_reales(html):
    texto = todo_el_texto(html)
    crear = leer('03-dataproc-spark/crear.sh')
    assert 'sleep 120' in crear and 'dataproc.autoscalingPolicies.use' in crear
    assert 'grep -E "(^|/)${PREFIJO_BATCH}-"' in leer('03-dataproc-spark/probar.sh')
    assert 'southamerica-west1' in leer('comun.sh') and 'REGION_SPARK' in leer('03-dataproc-spark/variables.sh')
    for c in ('dataproc.autoscalingPolicies.use', '120 s', 'countDistinct', 'COUNT(DISTINCT)', 'ignora los nulos', 'value(name)',
              'OK: 9 paises; facturas, clientes y monto coinciden con el calculo local.', '22 117', 'Santiago'):
        assert c in texto, c
    # la tabla por país es la salida real del 25/11/2026
    for fila in (('United Kingdom', '1140', '133', '344244.74'), ('France', '47', '5', '18857.36'), ('Portugal', '14', '3', '10780.8')):
        assert ' '.join(fila) in texto, fila


def test_practica_4_version_de_scikit_learn_y_clase_en_vez_de_probabilidad(html):
    texto = todo_el_texto(html)
    var = leer('04-vertex-modelo/variables.sh')
    assert 'sklearn-cpu.1-6:latest' in var and 'VERSION_SKLEARN="1.6.1"' in var and 'MAQUINA="e2-standard-2"' in var
    assert 'NOMBRE_MODELO="retencion-90d-sklearn"' in var and 'NOMBRE_ENDPOINT="retencion-90d-endpoint"' in var
    for c in ('scikit-learn 1.9.1', '1.6.1', 'retencion-90d-sklearn', 'retencion-90d-endpoint', 'e2-standard-2', '[1, 0]', 'clase',
              '0.6982', '0.8279', '0.2760', 'Model Registry', 'Extremos', '10 a 15 min', 'sin medir'):
        assert c in texto, c
    for variable in ('recencia_dias', 'es_reino_unido', 'dias_medios_entre_compras'):
        assert variable in texto, variable
    assert G.FUENTE_CREDITO in texto and 'desde el 16/11/2026' in texto and 'cobra' in texto


def test_practica_5_gemini_global_y_la_cifra_del_aviso(html):
    texto = todo_el_texto(html)
    var = leer('05-vertex-llm/variables.sh')
    assert 'MODELO_LLM="${CURSO_MODELO_LLM:-gemini-3.1-flash-lite}"' in var
    assert 'REGION_GEMINI="${CURSO_REGION_GEMINI:-global}"' in leer('comun.sh')
    for c in ('gemini-3.1-flash-lite', 'global', 'google-genai 3.6.1', 'entrada=388', 'salida=171', '82.79%', 'falso positivo',
              'Model Garden', 'solo redacta'):
        assert c in texto, c
    # el arreglo de la práctica 05 acepta justo la cifra que escribió Gemini
    spec = importlib.util.spec_from_file_location('explicar_prediccion', AQUI / '05-vertex-llm' / 'explicar_prediccion.py')
    e = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(e)
    assert e.cita_la_probabilidad('una probabilidad del 82.79% de comprar', 0.8279)


def test_los_siete_fallos_reales_estan_en_la_tabla_si_algo_falla(html):
    cuerpo = dict(zip(titulos(html), [c for _, c in secciones(html)]))['Si algo falla']
    texto = sin_etiquetas(cuerpo)
    for c in ('dial tcp', 'i/o timeout', 'autoscalingPolicies.use', 'no hay lotes', '1 cliente de más', 'predictions: [1, 0]',
              '82.8 %', '82.79%', 'Imgenes', 'tildes', 'sin verificar'):
        assert c in texto, c
    assert texto.count('sí (25/11)') == 7


def test_cifras_reales_del_25_de_noviembre(html):
    texto = todo_el_texto(html)
    for c in ('25/11/2026', '0.828', '0.8278889191932244', '1140', '133', '344244.74', '9 países', 'Listed 0 items', 'project-curso-ml-ia',
              'southamerica-west1', '120 s', '0 claves'):
        assert c in texto, c
    assert 'sin dato' in texto.lower() and 'sin verificar' in texto.lower()


def test_el_cierre_tiene_un_mensaje_cuatro_tarjetas_y_preguntas(html):
    ultima = secciones(html)[-1][1]
    assert ultima.count('class="msg"') == 1 and ultima.count('class="card kpi"') == 4 and '¿Preguntas?' in ultima


def test_texto_en_espanol_con_tildes_en_lo_que_se_proyecta(html):
    texto = todo_el_texto(html)
    for palabra in ('práctica', 'clúster', 'predicción', 'configuración' if 'configuración' in texto else 'región', 'imagen', 'ejecución' if 'ejecución' in texto else 'comprobación'):
        assert palabra in texto, palabra
    for mal in (' practica ', ' prediccion ', ' cluster ', ' region '):
        assert mal not in texto.replace('`', ''), mal


# ----------------------------------------------------------------------------------------------------------------------
# Higiene de los archivos
# ----------------------------------------------------------------------------------------------------------------------
ARCHIVOS = ['generar.py', 'index.html', 'pruebas/test_presentacion.py']


@pytest.mark.parametrize('nombre', ARCHIVOS)
def test_sin_bom_en_utf8_y_con_lf(nombre):
    datos = (AQUI / nombre).read_bytes()
    assert not datos.startswith(b'\xef\xbb\xbf'), f'{nombre} lleva BOM'
    datos.decode('utf-8')
    assert b'\r\n' not in datos, f'{nombre} tiene finales de línea CRLF'


@pytest.mark.parametrize('nombre', ['generar.py', 'index.html'])
def test_sin_rutas_personales_correos_ni_credenciales(nombre):
    texto = (AQUI / nombre).read_text(encoding='utf-8')
    assert 'C:\\Users' not in texto and 'AppData' not in texto and not re.search(r'\bBK\d{5}\b', texto)
    assert not re.search(r'[\w.]+@[\w-]+\.(com|es|org)\b', texto)
    assert 'gmail' not in texto.lower() and 'cursomlops' not in texto.lower()
    assert not re.search(r'ghp_|github_pat_|BEGIN PRIVATE KEY|"private_key"', texto)


def test_el_unico_usuario_de_github_que_aparece_es_el_de_las_capturas_o_la_variable(html):
    usuarios = set(re.findall(r'github\.com/([\w$-]+)/', html))
    assert usuarios <= {'helicr', '$USUARIO_GH'}, usuarios
