"""Pruebas de la clase «De on-premise a la nube» (sin navegador y sin tocar la nube).

Qué vigilan: que index.html y guia.md están al día con generar.py; entre 24 y 30 diapositivas, cada una con título, parte, minutos y
notas, con antetítulo numerado por partes; sin recursos externos, sin movimiento al pasar el ratón y con el botón «⌂ S4»; que hay
esquemas SVG y tablas de verdad (no solo listas); que los servicios de la tabla comparativa y del mapa están todos; que las siglas
están explicadas; que lo no comprobado dice «sin dato»; que las cifras que se muestran coinciden con las de las fuentes citadas;
que las órdenes de gcloud están en la guía y son plantillas; que el cierre tiene un mensaje y cuatro tarjetas; y que ningún archivo
lleva BOM, rutas personales ni secretos.
"""
import importlib.util
import re
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parents[1]
GUIA = AQUI / 'guia.md'

_spec = importlib.util.spec_from_file_location('generar_clase_nube', AQUI / 'generar.py')
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


def notas(html):
    return ' '.join(re.findall(r'data-notes="([^"]*)"', html))


# ----------------------------------------------------------------------------------------------------------------------
# Estructura
# ----------------------------------------------------------------------------------------------------------------------
def test_esta_al_dia_con_el_generador(html, guia):
    assert html == G.html_completo(), 'index.html no coincide con generar.py: ejecuta  python generar.py'
    assert guia == G.guia_md(), 'guia.md no coincide con generar.py: ejecuta  python generar.py'


def test_entre_24_y_30_diapositivas_cada_una_con_titulo_parte_minutos_y_notas(html):
    s = secciones(html)
    assert 24 <= len(s) <= 30, len(s)
    for attrs, cuerpo in s:
        assert re.search(r'data-part="[A-G]"', attrs), attrs
        m = re.search(r'data-min="(\d+)"', attrs)
        assert m and int(m.group(1)) > 0, attrs
        t = re.search(r'data-title="([^"]+)"', attrs)
        assert t and t.group(1).strip(), attrs
        n = re.search(r'data-notes="([^"]*)"', attrs)
        assert n and len(n.group(1)) > 80, f'notas demasiado cortas en {t.group(1)}'
        assert cuerpo.count('<h1>') == 1


def test_antetitulos_numerados_por_partes_y_en_orden(html):
    s = secciones(html)
    letras = list(G.PARTES)
    orden = []
    for attrs, cuerpo in s:
        parte = re.search(r'data-part="([A-G])"', attrs).group(1)
        kick = re.search(r'<p class="kick">(.*?)</p>', cuerpo).group(1)
        assert kick.startswith(f'{letras.index(parte) + 1} · '), kick
        orden.append(parte)
    assert orden == sorted(orden) and set(orden) == set(G.PARTES)


def test_pie_con_posicion_x_de_total_y_un_boton_por_parte(html):
    assert '${i+1} / ${N}' in html
    assert html.count('class="part"') == len(G.PARTES)


def test_fondo_blanco_y_nada_se_mueve_al_pasar_el_raton(html):
    assert '--fondo:#ffffff' in html
    assert ':hover' not in html and 'transition' not in html and 'animation' not in html


def test_sin_recursos_externos(html):
    assert not re.search(r'(src|href)="(https?:)?//', html)
    assert not re.search(r'@import|url\((["\']?)(https?:)?//', html)
    assert '<link' not in html and '<iframe' not in html and '<img' not in html


def test_boton_s4_y_teclas_del_visor(html):
    assert '<a id="bhome" href="../index.html"' in html and '⌂ S4' in html
    assert (AQUI.parent / 'index.html').exists()
    for clave in ("k==='Escape'", "k==='ArrowRight'", "k==='ArrowLeft'", "k==='o'", "k==='s'", "k==='f'"):
        assert clave in html, clave


def test_hay_infografias_svg_y_tablas_y_no_solo_listas(html):
    assert html.count('<svg') >= 7
    assert html.count('<table') >= 8
    for _, cuerpo in secciones(html):
        assert cuerpo.count('<li>') <= 12, 'demasiadas viñetas en una diapositiva'


def test_los_esquemas_tienen_texto_alternativo_y_marcas_unicas(html):
    for svg in re.findall(r'<svg [^>]*>', html):
        assert 'aria-label="' in svg and len(svg) > 80
    ids = re.findall(r'<marker id="([^"]+)"', html)
    assert len(ids) == len(set(ids)), 'marcadores de flecha repetidos'


# ----------------------------------------------------------------------------------------------------------------------
# Contenido pedido
# ----------------------------------------------------------------------------------------------------------------------
def test_on_premise_frente_a_nube_y_modelos_de_servicio(html):
    t = todo_el_texto(html)
    for clave in ('CAPEX', 'OPEX', 'elástica', 'gestionados', 'responsabilidad compartida', 'IaaS', 'PaaS', 'SaaS', 'Serverless'):
        assert clave.lower() in t.lower(), clave


def test_hiperescalares_y_otros_proveedores(html):
    t = todo_el_texto(html)
    for clave in ('Amazon Web Services', 'Microsoft Azure', 'Google Cloud', 'Oracle Cloud', 'IBM Cloud', 'Alibaba Cloud'):
        assert clave in t, clave


SERVICIOS = {
    'AWS': ['Amazon EC2', 'Amazon EKS', 'Amazon ECR', 'Amazon S3', 'Amazon RDS', 'Amazon Redshift', 'Amazon EMR', 'Amazon SageMaker',
            'Amazon Bedrock', 'AWS IAM', 'AWS Secrets Manager', 'Amazon CloudWatch'],
    'Azure': ['Azure Virtual Machines', 'Azure Container Apps', 'Azure Kubernetes Service', 'Azure Container Registry', 'Azure Blob Storage',
              'Azure SQL Database', 'Azure Synapse Analytics', 'Azure Databricks', 'Azure Machine Learning', 'Azure OpenAI', 'Azure DevOps',
              'Microsoft Entra ID', 'Azure Key Vault', 'Azure Monitor'],
    'GCP': ['Compute Engine', 'Cloud Run', 'Google Kubernetes Engine', 'Artifact Registry', 'Cloud Storage', 'Cloud SQL', 'BigQuery',
            'Dataproc', 'Vertex AI', 'Gemini', 'Cloud Build', 'Cloud IAM', 'Secret Manager', 'Cloud Logging', 'Cloud Monitoring'],
}


def test_la_tabla_comparativa_cubre_las_doce_necesidades_con_los_tres_proveedores(html):
    t = todo_el_texto(html)
    for prov, nombres in SERVICIOS.items():
        for n in nombres:
            assert n in t, f'{prov}: falta {n}'
    for necesidad in ('Máquina virtual', 'Contenedores sin servidores', 'Kubernetes gestionado', 'Registro de imágenes',
                      'Almacenamiento de objetos', 'Base de datos relacional', 'Data warehouse', 'Spark gestionado', 'Plataforma de ML',
                      'LLMs gestionados', 'CI/CD', 'Identidad y permisos', 'Secretos', 'Monitorización'):
        assert necesidad in t, necesidad


def test_google_cloud_jerarquia_identidad_y_primeros_pasos(html):
    t = todo_el_texto(html)
    for clave in ('Organización', 'Carpeta', 'Proyecto', 'Recursos', 'southamerica-west1', 'Workload Identity Federation', 'cuenta de servicio',
                  'Cloud Shell', 'gcloud', 'Facturación', 'Habilitar las APIs', 'mínimo privilegio'):
        assert clave.lower() in t.lower(), clave


def test_los_servicios_del_curso_y_para_que_sirven(html):
    t = todo_el_texto(html)
    for s in ('Cloud Storage', 'BigQuery', 'Artifact Registry', 'Cloud Run', 'GKE', 'Dataproc', 'Model Registry', 'Endpoints', 'Pipelines',
              'Model Garden', 'Gemini', 'Cloud Build', 'GitHub Actions', 'Secret Manager', 'Cloud Logging', 'Cloud Monitoring', 'Presupuestos'):
        assert s in t, s
    assert t.count('En el curso') >= 12


def test_cloud_journey_as_is_to_be_tabla_y_las_r(html):
    t = todo_el_texto(html)
    for clave in ('AS-IS', 'TO-BE', 'SQLite', 'GHCR', 'MLflow', 'GitHub Actions', 'Artifact Registry', 'Cloud Run', 'Rehost', 'Replatform',
                  'Refactor', 'Repurchase', 'Retire', 'Retain', 'Qué se mueve', 'Esfuerzo', 'sin medir'):
        assert clave in t, clave
    # el AS-IS y el TO-BE son esquemas distintos
    assert 'Arquitectura actual' in html and 'Arquitectura en Google Cloud' in html


def test_costes_region_y_buenas_practicas(html):
    t = todo_el_texto(html)
    for clave in ('Free Trial', 'Free Tier', 'Presupuesto', 'no corta el gasto', 'Apagar no es borrar', 'etiqueta', 'southamerica-east1',
                  'São Paulo', 'Model Monitoring', 'Gemini en Vertex AI', 'no listada'):
        assert clave.lower() in t.lower(), clave


def test_las_siglas_estan_explicadas(html):
    t = todo_el_texto(html)
    for sigla, explicacion in (('CAPEX', 'Capital expenditure'), ('OPEX', 'Operating expenditure'), ('SLA', 'Service Level Agreement'),
                               ('IAM', 'Identity and Access Management'), ('WIF', 'Workload Identity Federation'),
                               ('OIDC', 'OpenID Connect')):
        assert sigla in t and explicacion in t, sigla


# ----------------------------------------------------------------------------------------------------------------------
# Cifras, fuentes y honestidad
# ----------------------------------------------------------------------------------------------------------------------
def test_cada_fuente_citada_esta_en_las_notas_y_en_la_guia(html, guia):
    n = notas(html)
    for corto, (nombre, url) in G.FUENTES.items():
        assert url.startswith('https://') and ' ' not in url
        assert url in guia, f'{corto}: sin dirección en guia.md'
    usadas = [u for _, u in G.FUENTES.values() if u in n]
    assert len(usadas) >= 14, 'casi todas las fuentes deben aparecer en alguna nota del ponente'
    assert G.CONSULTA in n and G.CONSULTA in guia


def test_las_cifras_visibles_son_las_de_las_fuentes_citadas(html):
    t = todo_el_texto(html)
    # prueba gratuita y nivel gratuito: Google Cloud · Free cloud features (25/11/2026)
    for c in ('$300', '90 días', '30 días de gracia', '2 millones de peticiones', '1 TiB', '10 GiB', '5 GB-mes', 'us-east1', 'us-west1', 'us-central1'):
        assert c in t, c
    # presupuestos: Cloud Billing · Budgets
    assert '50 %, 90 % y 100 %' in t and "doesn't automatically cap" in t
    # zonas de Santiago: Compute Engine · Regions and zones
    assert '3 zonas' in t and all(z in t for z in ('-a', '-b', '-c'))
    # siete R de AWS
    assert 'AWS documenta siete' in t


def test_no_se_cita_el_importe_de_ninguna_cuenta_concreta(html, guia):
    for texto in (todo_el_texto(html), guia):
        assert not re.search(r'(saldo|crédito)\s+(de|restante|disponible)\s+(de\s+)?[\$€]?\s?\d', texto, re.I)
    assert 'ninguna cuenta concreta' in todo_el_texto(html)


def test_lo_no_comprobado_dice_sin_dato_y_no_se_inventan_cifras(html, guia):
    t = todo_el_texto(html).lower()
    for texto in (t, guia.lower()):
        assert 'sin dato' in texto and 'sin ejecutar' in texto
    # cuota de mercado, precios y regiones: nunca una cifra
    assert not re.search(r'\d+\s?%\s+(del\s+)?mercado', t)
    assert 'cuota de mercado' in t
    assert not re.search(r'(precio|cuesta|coste)[^.]{0,40}\$\s?\d', t)


def test_region_santiago_con_lo_que_hay_y_la_alternativa(html, guia):
    t = todo_el_texto(html)
    for clave in ('Cloud Storage', 'BigQuery', 'Artifact Registry', 'Cloud Run', 'Secret Manager', 'Vertex AI: modelos propios',
                  'Model Registry', 'Pipelines', 'Experiments', 'Explainable AI', 'endpoint global', 'southamerica-east1'):
        assert clave in t, clave
    assert 'no listada' in t
    cuerpo = [c for a, c in secciones(html) if 'La región: Santiago' in a][0]
    assert cuerpo.count('<span class="tag') >= 12
    for texto in (t, guia):
        assert 'alternativa' in texto and 'São Paulo' in texto


def test_cuando_hay_dudas_se_dice_gke_dataproc_y_logging_sin_dato(html):
    t = todo_el_texto(html)
    assert 'GKE y Dataproc' in t and 'Cloud Logging: sin dato' in t


# ----------------------------------------------------------------------------------------------------------------------
# Órdenes y guía
# ----------------------------------------------------------------------------------------------------------------------
def test_las_ordenes_de_gcloud_estan_en_la_pagina_y_en_la_guia_y_son_plantillas(html, guia):
    for clave, orden in G.O.items():
        assert f'data-t="{G.esc(orden)}"' in html, f'{clave}: no sale en ninguna diapositiva'
        assert orden in guia, f'{clave}: no está en guia.md'
    for clave in ('proyecto', 'factura', 'borrar_proyecto', 'borrar_gcs', 'borrar_bq', 'borrar_ar'):
        assert re.search(r'ID_PROYECTO|NOMBRE_DEL_|REPOSITORIO|ID_FACTURACION', G.O[clave]), f'{clave} debe llevar un valor de ejemplo'
    assert G.REGION in G.O['region']


def test_la_guia_tiene_todas_las_diapositivas_y_las_notas(html, guia):
    n = len(secciones(html))
    assert len(re.findall(r'^### \d+\. ', guia, re.M)) == n
    assert guia.count('> **Para el ponente.**') == n
    assert '## Fuentes consultadas' in guia and guia.startswith('# De on-premise a la nube')
    assert '|---|' in guia


# ----------------------------------------------------------------------------------------------------------------------
# Cierre
# ----------------------------------------------------------------------------------------------------------------------
def test_cierre_con_un_mensaje_cuatro_tarjetas_y_preguntas(html):
    ultima = secciones(html)[-1][1]
    assert ultima.count('class="msg"') == 1
    assert ultima.count('class="card kpi"') == 4
    assert '¿Preguntas?' in ultima


def test_autoevaluacion_con_seis_preguntas(html):
    cuerpo = [c for a, c in secciones(html) if 'data-title="Autoevaluación"' in a][0]
    assert cuerpo.count('<h3>') == 6


# ----------------------------------------------------------------------------------------------------------------------
# Higiene
# ----------------------------------------------------------------------------------------------------------------------
ARCHIVOS = ['generar.py', 'index.html', 'guia.md', 'pruebas/test_presentacion.py']


@pytest.mark.parametrize('nombre', ARCHIVOS)
def test_sin_bom_utf8_y_finales_de_linea_lf(nombre):
    datos = (AQUI / nombre).read_bytes()
    assert not datos.startswith(b'\xef\xbb\xbf'), f'{nombre} lleva BOM'
    datos.decode('utf-8')
    assert b'\r\n' not in datos, f'{nombre} tiene finales de línea CRLF'


@pytest.mark.parametrize('nombre', ['generar.py', 'index.html', 'guia.md'])
def test_sin_rutas_personales_ni_credenciales(nombre):
    texto = (AQUI / nombre).read_text(encoding='utf-8')
    assert 'C:\\Users' not in texto and 'AppData' not in texto and not re.search(r'\bBK\d{5}\b', texto)
    assert not re.search(r'[\w.]+@[\w-]+\.(com|es|org)', texto)
    assert not re.search(r'(token|password|contraseña)\s*[:=]\s*\S{6,}', texto, re.I)
    assert not re.search(r'ghp_|github_pat_|AKIA[0-9A-Z]{12}|AIza[0-9A-Za-z_-]{20}', texto)


def test_texto_en_espanol_con_tildes_en_lo_que_se_proyecta(html):
    t = todo_el_texto(html)
    for palabra in ('producción', 'configuración', 'región', 'aprobación', 'facturación', 'organización'):
        assert palabra in t, palabra
    for mal in ('produccion de', 'facturacion', 'organizacion', 'configuracion'):
        assert mal not in t.replace('`produccion`', ''), mal
