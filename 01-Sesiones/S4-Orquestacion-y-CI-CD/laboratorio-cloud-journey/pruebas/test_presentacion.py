"""Pruebas de la presentación, la guía y los scripts del «Laboratorio Cloud Journey» (sin navegador y sin tocar la nube).

Qué vigilan: que index.html está al día con generar.py; entre 24 y 30 diapositivas, cada una con título, parte, minutos y notas;
que las capturas citadas existen (salvo las pendientes, que salen como «Captura pendiente» y no se enlazan en la guía) y no
sobra ninguna; que las órdenes de la presentación están en guia.md, sin «&&», y citan archivos que existen y coinciden con
desplegar-gcp.yml; que las cifras del run real (nº 45519881368) coinciden entre presentación, guía y capturas; que
preparar-gcp-s4.sh imprime las cinco variables y limita WIF al repositorio; que borrar-gcp-s4.sh es idempotente, no borra el
proyecto ni sa-curso-ml-ia y tiene sintaxis válida; y que ningún archivo lleva BOM, CRLF, correos ni secretos.
"""
import importlib.util
import re
import shutil
import subprocess
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parents[1]
GUIA = AQUI / 'guia.md'
CONFIGURAR = AQUI / 'CONFIGURAR-GCP.md'
WORKFLOW = AQUI / 'desplegar-gcp.yml'
PREPARAR = AQUI / 'preparar-gcp-s4.sh'
BORRAR = AQUI / 'borrar-gcp-s4.sh'

_spec = importlib.util.spec_from_file_location('generar_cloud_journey', AQUI / 'generar.py')
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)

BASH = next((p for p in (r'C:\bk\software\git\bin\bash.exe', r'C:\Program Files\Git\bin\bash.exe') if Path(p).is_file()), None) or shutil.which('bash')


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


def existentes():
    return set(G.CAPTURAS) - set(G.PENDIENTES)


# ----------------------------------------------------------------------------------------------------------------------
# Estructura de la presentación
# ----------------------------------------------------------------------------------------------------------------------
def test_esta_al_dia_con_el_generador(html):
    assert html == G.html_completo(), 'index.html no coincide con generar.py: ejecuta  python generar.py'


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


def test_marco_de_los_laboratorios_zoom_con_clic_esc_y_flechas(html):
    for clave in ("k==='Escape'", "k==='ArrowRight'", "k==='ArrowLeft'", 'id="zoombox"', 'cursor:zoom-in', 'data-src="img/'):
        assert clave in html, clave


def test_dos_diagramas_as_is_y_to_be_y_el_de_wif(html):
    assert html.count('<svg viewBox') >= 5
    texto = todo_el_texto(html)
    for clave in ('AS-IS', 'TO-BE', 'Artifact Registry', 'Cloud Run', 'Vertex AI', 'Cloud Storage', 'pieza', 'Hoy', 'Mañana', 'Servicio'):
        assert clave.lower() in texto.lower(), clave


# ----------------------------------------------------------------------------------------------------------------------
# Capturas
# ----------------------------------------------------------------------------------------------------------------------
def test_las_capturas_existentes_estan_citadas_y_son_webp_y_las_pendientes_salen_como_pendientes(html):
    citadas = set(re.findall(r'(?:src|data-src)="img/([^"]+)"', html))
    assert citadas == existentes(), citadas ^ existentes()
    for nombre in citadas:
        f = AQUI / 'img' / nombre
        assert nombre.endswith('.webp') and f.stat().st_size > 5000, nombre
        datos = f.read_bytes()
        assert datos[:4] == b'RIFF' and datos[8:12] == b'WEBP', nombre
    en_disco = {p.name for p in (AQUI / 'img').glob('*.webp')}
    assert en_disco == existentes(), en_disco ^ existentes()
    for nombre in G.PENDIENTES:
        assert not (AQUI / 'img' / nombre).exists(), nombre
        assert f'img/{nombre}</span>' in html and f'data-img="{nombre}"' in html, nombre
    assert html.count('Captura pendiente</b>') == len(G.PENDIENTES)


def test_las_capturas_obligatorias_estan_previstas():
    previstas = {n.rsplit('.', 1)[0] for n in G.CAPTURAS}
    for n in ('gcp-01-proyectos', 'gcp-02-facturacion', 'gcp-03-facturacion-proyecto', 'gcp-20-cloudshell', 'gcp-23-preparar',
              'gcp-24-ar-y-politicas', 'gcp-12-politica-claves', 'gcp-09-cuentas-servicio', 'gcp-11-wif',
              'cj-01-variables-github', 'cj-02-run-desplegado', 'cj-03-resumen-cloudrun', 'cj-04-cloudrun-consola',
              'cj-05-artifact-registry', 'cj-06-vertex-modelo', 'cj-07-vertex-endpoint', 'cj-08-borrado'):
        assert n in previstas, n


def test_ya_no_quedan_capturas_pendientes_y_las_de_la_consola_llevan_el_banner_recortado(html):
    from PIL import Image
    assert G.PENDIENTES == [] and 'Captura pendiente</b>' not in html
    # la consola de Google Cloud trae arriba (y solo en la ventana grande) el aviso del crédito de la prueba gratuita: está recortado
    for nombre, alto in (('cj-04-cloudrun-consola', 755), ('cj-06-vertex-modelo', 755), ('cj-07-vertex-endpoint', 755)):
        with Image.open(AQUI / 'img' / f'{nombre}.webp') as im:
            assert im.size == (1424, alto), (nombre, im.size)
    with Image.open(AQUI / 'img' / 'cj-08-borrado.webp') as im:
        assert im.width > 1500 and 400 < im.height < 700


def test_las_capturas_descartadas_no_estan_ni_en_disco_ni_en_el_codigo(html, guia):
    for nombre in ('gcp-04-creditos', 'gcp-05-apis', 'gcp-06-iam'):
        assert nombre not in html and nombre not in guia
        assert not (AQUI / 'img' / f'{nombre}.webp').exists()


def test_cada_captura_tiene_texto_alternativo_con_contenido(html):
    for nombre, alt in G.CAPTURAS.items():
        assert len(alt) > 40, nombre
        assert f'alt="{G.esc(alt)}"' in html or nombre in G.PENDIENTES, nombre


def test_la_guia_cita_solo_capturas_que_existen_y_no_enlaza_las_pendientes(guia):
    for texto in (guia, CONFIGURAR.read_text(encoding='utf-8')):
        for ruta in re.findall(r'\]\((img/[^)]+)\)', texto):
            assert (AQUI / ruta).exists(), ruta
        for nombre in re.findall(r'img/([\w-]+\.webp)', texto):
            assert (AQUI / 'img' / nombre).exists(), nombre
    for n in G.PENDIENTES:
        assert n.rsplit('.', 1)[0] in guia, n          # se mencionan como pendientes
        assert f'(img/{n})' not in guia, n


def test_varias_capturas_en_una_diapositiva_donde_tiene_sentido(html):
    por_slide = [len(re.findall(r'<figure class="cap"', c)) for _, c in secciones(html)]
    assert max(por_slide) >= 3
    assert sum(1 for n in por_slide if n >= 2) >= 4
    assert sum(por_slide) == len(G.CAPTURAS)


def test_la_captura_de_aprobacion_avisa_de_que_es_del_laboratorio_anterior(html, guia):
    pie = re.search(r'gh-01-esperando-aprobacion\.webp".*?</figure>', html, re.S).group(0)
    assert 'laboratorio anterior' in pie
    assert 'laboratorio anterior' in guia


def test_la_captura_del_resumen_es_un_recorte_real_del_run():
    from PIL import Image
    with Image.open(AQUI / 'img' / 'cj-03-resumen-cloudrun.webp') as im:
        assert im.width > 800 and 150 < im.height < 400


# ----------------------------------------------------------------------------------------------------------------------
# Órdenes y archivos
# ----------------------------------------------------------------------------------------------------------------------
def test_cada_orden_tiene_su_boton_de_copiar_y_esta_en_la_guia(html, guia):
    for clave, orden in G.O.items():
        assert f'data-t="{G.esc(orden)}"' in html, f'{clave}: la orden no sale en ninguna diapositiva'
        assert orden in guia, f'{clave}: la orden no está en guia.md'


def test_ninguna_orden_usa_doble_ampersand_ni_tildes_en_gcloud():
    for clave, orden in G.O.items():
        assert '&&' not in orden, clave
        if orden.startswith('gcloud'):
            assert not re.search(r'[áéíóúñÁÉÍÓÚÑ]', orden), clave
    assert '--description="Imagenes del curso"' in G.O['crear_ar']


def test_las_ordenes_citan_archivos_y_carpetas_que_existen():
    assert G.CARPETA.endswith('laboratorio-cloud-journey') and AQUI.as_posix().endswith(G.CARPETA)
    assert G.RAMA.startswith('lab/cloud-journey/')
    assert G.O['cp'] == f'cp {G.CARPETA}/desplegar-gcp.yml .github/workflows/'
    assert G.O['ps_cp'] == f'Copy-Item {G.CARPETA}/desplegar-gcp.yml .github/workflows/'
    assert G.O['push'] == f'git push -u origin {G.RAMA}' and G.O['rama'] == f'git switch -c {G.RAMA}'
    assert G.O['cd_lab'] == f'cd ~/curso/{G.CARPETA}'
    for f in ('desplegar-gcp.yml', 'preparar-gcp-s4.sh', 'borrar-gcp-s4.sh', 'guia.md', 'CONFIGURAR-GCP.md'):
        assert (AQUI / f).is_file(), f
    assert f'nano {PREPARAR.name}' == G.O['editar'] and G.O['preparar'] == f'bash {PREPARAR.name}' and G.O['borrar'] == f'bash {BORRAR.name}'
    practica = AQUI.parent / 'practicas-gcp' / '04-vertex-modelo'
    for f in ('crear.sh', 'probar.sh', 'borrar.sh', 'README.md'):
        assert (practica / f).is_file(), f
    assert G.O['cd_vertex'] == 'cd ~/curso/01-Sesiones/S4-Orquestacion-y-CI-CD/practicas-gcp/04-vertex-modelo'
    assert '../practicas-gcp/04-vertex-modelo/README.md' in (AQUI / 'guia.md').read_text(encoding='utf-8')


def test_el_workflow_hace_lo_que_dicen_las_diapositivas(html):
    y = WORKFLOW.read_text(encoding='utf-8')
    assert "branches: ['lab/cloud-journey/**']" in y
    assert 'id-token: write' in y and 'environment: produccion' in y
    assert 'google-github-actions/auth@v2' in y and 'google-github-actions/setup-gcloud@v2' in y
    assert 'workload_identity_provider: ${{ vars.GCP_PROVEEDOR_WIF }}' in y and 'service_account: ${{ vars.GCP_CUENTA_DESPLIEGUE }}' in y
    assert 'gcloud auth configure-docker' in y and 'docker push' in y and 'gcloud run deploy' in y
    assert '--service-account="${{ vars.GCP_CUENTA_SERVICIO }}"' in y
    assert '--min-instances=0 --max-instances=1 --allow-unauthenticated' in y
    desplegar = y[y.index('  desplegar:'):]
    assert 'working-directory: .' in desplegar and 'id-token: write' in desplegar
    for n, _ in G.VARIABLES:
        assert f'vars.{n}' in y, n
    assert 'name: 1 · Construir y probar la imagen' in y and 'name: 2 · Publicar en Artifact Registry y desplegar en Cloud Run' in y
    texto = todo_el_texto(html)
    for clave in ('id-token: write', 'environment: produccion', 'google-github-actions/auth@v2', 'google-github-actions/setup-gcloud@v2',
                  'workload_identity_provider', 'service_account', 'gcloud auth configure-docker', 'docker push', 'gcloud run deploy',
                  '--service-account', '--min-instances=0 --max-instances=1 --allow-unauthenticated', 'working-directory: .'):
        assert clave in texto, clave


def test_preparar_imprime_las_cinco_variables_y_limita_wif_al_repositorio():
    s = PREPARAR.read_text(encoding='utf-8')
    for n, _ in G.VARIABLES:
        assert f'echo "{n}=' in s, n
    assert 'set -euo pipefail' in s and "--attribute-condition=\"assertion.repository=='$REPO_GITHUB'\"" in s
    assert 'FIN · todo listo' in s and '--budget-amount=20EUR' in s
    for rol in ('roles/artifactregistry.writer', 'roles/run.admin', 'roles/iam.serviceAccountUser', 'roles/iam.workloadIdentityUser'):
        assert rol in s, rol
    assert f'PROYECTO="{G.PROYECTO}"' in s and f'REGION="{G.REGION}"' in s and f'REPO_GITHUB="{G.USUARIO}/{G.REPO}"' in s
    assert 'sa-github-despliegue' in s and 'sa-cloudrun-retencion' in s
    # la cuenta del servicio no recibe ningún rol: solo se le da serviceAccountUser al desplegador
    assert 'projects add-iam-policy-binding' in s and 'SA_SERVICIO@$PROYECTO.iam.gserviceaccount.com" \\\n    --role="$ROL"' not in s


def test_preparar_distingue_activo_de_borrado_y_conserva_lo_validado():
    # El 25/11/2026 se ejecutó entero (73 líneas) en la cuenta del curso. El 26/11 se vio que, un día después de borrarlo todo, un
    # pool de WIF en estado DELETED respondía a «describe»: el script lo daba por existente y create-oidc fallaba con NOT_FOUND.
    # Ahora mira el ESTADO y restaura lo borrado (93 líneas). Ejecutado de verdad el 26/11: con todo ACTIVE («ya existe», FIN · todo
    # listo). Los bloques DELETED NO se han ejecutado a través del script (solo sus órdenes, a mano: pool y proveedor quedaron ACTIVE).
    s = PREPARAR.read_bytes()
    assert not s.startswith(b'\xef\xbb\xbf') and b'\r' not in s
    t = s.decode('utf-8')
    for clave in ("--format='value(state)'", 'case "$ESTADO_POOL"', 'case "$ESTADO_PROV"', 'workload-identity-pools undelete',
                  'providers undelete', 'providers update-oidc', 'DELETED)'):
        assert clave in t, clave
    # lo validado el 25/11 sigue ahí
    for linea in ('gcloud billing projects link', 'roles/artifactregistry.writer', 'roles/run.admin', 'roles/iam.workloadIdentityUser',
                  'gcloud billing budgets create', 'GCP_PROVEEDOR_WIF=', 'FIN · todo listo'):
        assert linea in t, linea


def test_borrar_es_idempotente_no_borra_el_proyecto_ni_sa_curso_ml_ia_y_lista_lo_que_queda():
    s = BORRAR.read_text(encoding='utf-8')
    assert s.startswith('#!/usr/bin/env bash') and 'set -euo pipefail' in s
    assert 'existe()' in s and s.count('existe gcloud') >= 5
    assert 'gcloud projects delete' not in s and 'gcloud iam service-accounts delete "sa-curso-ml-ia' not in s
    assert 'SA_CURSO' not in s
    cuentas_borradas = re.findall(r'for SA in ([^;]+); do', s)
    assert cuentas_borradas == ['"$SA_DESPLIEGUE" "$SA_SERVICIO"']
    for orden in ('gcloud run services delete', 'gcloud artifacts repositories delete', 'gcloud iam workload-identity-pools providers delete',
                  'gcloud iam workload-identity-pools delete', 'gcloud billing budgets delete', 'gcloud projects remove-iam-policy-binding'):
        assert orden in s, orden
    assert s.index('providers delete') < s.index('workload-identity-pools delete')     # primero el proveedor, luego el pool
    for listado in ('gcloud run services list', 'gcloud artifacts repositories list', 'gcloud iam workload-identity-pools list',
                    'gcloud billing budgets list', 'gcloud iam service-accounts list'):
        assert listado in s, listado
    assert 'DESVINCULAR_FACTURACION' in s and 'gcloud billing projects unlink' in s
    assert 'FIN · borrado terminado' in s
    # mismos nombres que el script de preparación
    p = PREPARAR.read_text(encoding='utf-8')
    for var in ('PROYECTO', 'REGION', 'FACTURACION', 'POOL', 'PROVEEDOR', 'SA_DESPLIEGUE', 'SA_SERVICIO'):
        assert re.search(rf'^{var}="[^"]+"', s, re.M).group(0) == re.search(rf'^{var}="[^"]+"', p, re.M).group(0), var
    assert 'REPO_AR="curso"' in s and 'SERVICIO="retencion-api"' in s and 'PRESUPUESTO="Curso ML e IA"' in s and 'Curso ML e IA' in p


@pytest.mark.skipif(BASH is None, reason='no hay bash para validar la sintaxis')
@pytest.mark.parametrize('script', [PREPARAR, BORRAR])
def test_sintaxis_de_los_scripts_con_bash_n(script):
    r = subprocess.run([BASH, '-n', str(script)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


# ----------------------------------------------------------------------------------------------------------------------
# Contenido obligatorio y cifras
# ----------------------------------------------------------------------------------------------------------------------
def test_las_cinco_variables_y_sus_valores_estan_en_presentacion_guia_y_configurar(html, guia):
    texto = todo_el_texto(html)
    config = CONFIGURAR.read_text(encoding='utf-8')
    assert G.WIF == 'projects/61343545797/locations/global/workloadIdentityPools/github/providers/github'
    assert G.SA_DESPLIEGUE == 'sa-github-despliegue@project-curso-ml-ia.iam.gserviceaccount.com'
    assert G.SA_SERVICIO == 'sa-cloudrun-retencion@project-curso-ml-ia.iam.gserviceaccount.com'
    for nombre, valor in G.VARIABLES:
        for t in (texto, guia, config):
            assert nombre in t and valor in t, (nombre, valor)
    assert 'Repository variables' in texto and 'New repository variable' in texto and 'Secrets and variables' in texto


def test_las_cifras_del_run_real_coinciden_en_presentacion_y_guia(html, guia):
    texto = todo_el_texto(html)
    assert G.RUN == '45519881368'
    for c in ('45519881368', '8 min 32 s', '1 min 49 s', '1 min 16 s', '0,8278889191932133', '0,828', '35a94deb4e04ab4a',
              'regresion_logistica', 'southamerica-west1', 'project-curso-ml-ia', 'retencion-api'):
        assert c in texto, c
    for c in ('45519881368', '8 min 32 s', '1 min 49 s', '1 min 16 s', '0.8278889191932133', '0,828', '35a94deb4e04ab4a',
              '{"estado":"ok"}', '{"estado":"listo"}', 'regresion_logistica', 'FIN · todo listo'):
        assert c in guia, c
    assert 'https://github.com/helicr/curso-ml-ia-desarrollo-produccion/actions/runs/45519881368' in html
    assert 'https://github.com/helicr/curso-ml-ia-desarrollo-produccion/actions/runs/45519881368' in guia


def test_pasos_aprobacion_y_textos_de_github(html, guia):
    texto = todo_el_texto(html)
    for clave in ('helicr requested your review to deploy to produccion', 'Review deployments', 'Approve and deploy',
                  'Settings', 'Variables', 'New repository variable'):
        assert clave in texto, clave
        assert clave in guia, clave


def test_cada_orden_dice_donde_se_ejecuta(html, guia):
    texto = todo_el_texto(html)
    for donde in ('Cloud Shell', 'tu terminal', 'la web de GitHub', 'la consola de Google Cloud', 'Windows PowerShell'):
        assert donde.lower() in texto.lower(), donde
        assert donde.lower() in guia.lower(), donde
    # todos los terminales de la presentación llevan título con su sitio
    titulos = re.findall(r'<div class="bar"><em>(.*?)</em>', html)
    assert titulos and all(re.search(r'Cloud Shell|terminal|PowerShell|Codespace', t) for t in titulos), titulos


def test_no_inventa_cifras_y_dice_lo_que_esta_sin_verificar(html, guia):
    texto = todo_el_texto(html)
    for t in (texto, guia):
        assert 'sin dato' in t.lower() and 'sin verificar' in t.lower()
        assert 'borrar-gcp-s4.sh' in t
        # el borrado se ejecutó de verdad el 25/11/2026 (captura cj-08): ya no puede decir que está sin ejecutar
        assert 'no ejecutado' not in t.lower() and 'no se ha ejecutado' not in t.lower()
    assert 'Coste' in texto and 'sin dato' in texto.lower()


def test_el_modelo_en_vertex_enlaza_la_practica_04(html, guia):
    texto = todo_el_texto(html)
    for t in (texto, guia):
        for clave in ('retencion-90d-sklearn', 'retencion-90d-endpoint', 'práctica 04', 'Model Registry', '1.6'):
            assert clave in t, clave
    assert '../practicas-gcp/04-vertex-modelo/README.md' in texto


def test_el_cierre_tiene_un_mensaje_cuatro_tarjetas_con_cifras_reales_y_preguntas(html):
    ultima = secciones(html)[-1][1]
    assert ultima.count('class="msg"') == 1
    assert ultima.count('class="card kpi"') == 4
    for cifra in ('8 min 32 s', '0,828', '0 claves', '20 €', '¿Preguntas?'):
        assert cifra in ultima, cifra


def test_las_siglas_estan_explicadas(html):
    texto = todo_el_texto(html)
    for sigla, explicacion in (('WIF', 'Workload Identity Federation'), ('OIDC', 'OpenID Connect'), ('Cloud Shell', 'terminal de Linux'),
                               ('Cuenta de servicio', 'identidad'), ('Región', 'Santiago'), ('Vertex AI', 'Model Registry')):
        assert sigla in texto and explicacion in texto, sigla


def test_costes_y_lecciones_reales(html, guia):
    texto = todo_el_texto(html)
    for t in (texto, guia):
        for clave in ('min-instances=0', '20 €', 'sin roles', 'Gemini', 'tildes', 'GKE', 'iam.disableServiceAccountKeyCreation' if t is guia else 'Sin claves'):
            assert clave in t, clave


def test_texto_en_espanol_con_tildes_en_lo_que_se_proyecta(html):
    texto = todo_el_texto(html)
    for palabra in ('producción', 'aprobación', 'configuración' if 'configuración' in texto else 'región', 'imagen', 'facturación'):
        assert palabra in texto, palabra
    for mal in ('aprobacion ', 'facturacion ', 'region ', 'Facturacion'):
        assert mal not in texto.replace('`produccion`', ''), mal


# ----------------------------------------------------------------------------------------------------------------------
# Higiene de los archivos
# ----------------------------------------------------------------------------------------------------------------------
ARCHIVOS = ['generar.py', 'index.html', 'guia.md', 'CONFIGURAR-GCP.md', 'preparar-gcp-s4.sh', 'borrar-gcp-s4.sh',
            'desplegar-gcp.yml', 'pruebas/test_presentacion.py']


@pytest.mark.parametrize('nombre', ARCHIVOS)
def test_sin_bom_en_utf8_y_con_lf(nombre):
    datos = (AQUI / nombre).read_bytes()
    assert not datos.startswith(b'\xef\xbb\xbf'), f'{nombre} lleva BOM'
    datos.decode('utf-8')
    assert b'\r\n' not in datos, f'{nombre} tiene finales de línea CRLF'


@pytest.mark.parametrize('nombre', ['generar.py', 'index.html', 'guia.md', 'CONFIGURAR-GCP.md', 'preparar-gcp-s4.sh', 'borrar-gcp-s4.sh'])
def test_sin_rutas_personales_correos_ni_credenciales(nombre):
    texto = (AQUI / nombre).read_text(encoding='utf-8')
    assert 'C:\\Users' not in texto and 'AppData' not in texto and not re.search(r'\bBK\d{5}\b', texto)
    assert not re.search(r'[\w.]+@[\w-]+\.(com|es|org)\b', texto)
    assert 'gmail' not in texto.lower() and 'cursomlops' not in texto.lower()
    assert not re.search(r'(?<!id-)\b(token|password|contraseña)\s*[:=]\s*(?!write)\S{6,}', texto, re.I)
    assert not re.search(r'ghp_|github_pat_|BEGIN PRIVATE KEY|"private_key"', texto)


def test_el_unico_usuario_de_github_que_aparece_es_el_de_las_capturas(html, guia):
    for texto in (html, guia):
        usuarios = set(re.findall(r'github\.com/([\w-]+)/', texto)) | set(re.findall(r'ghcr\.io/([\w-]+)/', texto))
        assert usuarios <= {'helicr', '$USUARIO_GH'}, usuarios
