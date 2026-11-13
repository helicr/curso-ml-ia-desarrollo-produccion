"""Pruebas de la guía «Docker, Kubernetes y GKE». No necesitan Docker ni Internet: leen archivos del repositorio.

Ejecutar:  python -m pytest 03-Entorno/guia-docker-kubernetes-gke/pruebas -q
"""
import importlib.util
import re
from pathlib import Path

AQUI = Path(__file__).resolve().parents[1]
# Se carga con nombre propio: la guía de Codespaces también tiene un generar.py y pytest los ejecuta en la misma sesión.
_spec = importlib.util.spec_from_file_location('generar_guia_k8s', AQUI / 'generar.py')
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)

RAIZ = AQUI.parents[1]
K8S = RAIZ / '04-Proyecto-Base' / 'deploy' / 'kubernetes'
DEPLOY = (K8S / 'deployment.yaml').read_text(encoding='utf-8')
SERVICE = (K8S / 'service.yaml').read_text(encoding='utf-8')
DOCKERFILE = (RAIZ / '04-Proyecto-Base' / 'deploy' / 'docker' / 'Dockerfile').read_text(encoding='utf-8')
HTML = (AQUI / 'index.html').read_text(encoding='utf-8')
CHULETA = (AQUI / 'chuleta.md').read_text(encoding='utf-8')
EJERCICIOS = (AQUI / 'ejercicios.md').read_text(encoding='utf-8')


def test_lo_generado_esta_al_dia():
    assert HTML == G.construir(), 'index.html desactualizado: ejecuta python generar.py'


def test_cada_captura_existe_se_usa_y_va_embebida():
    citadas = G.capturas_citadas()
    assert len(citadas) == len(set(citadas)) >= 16
    for nombre in citadas:
        assert (AQUI / 'capturas' / f'{nombre}.webp').exists(), nombre
    sobrantes = {p.stem for p in (AQUI / 'capturas').glob('*.webp')} - set(citadas)
    assert not sobrantes, f'capturas sin usar: {sobrantes}'
    assert HTML.count('src="data:image/webp;base64,') == len(citadas)
    assert '<!--CAPTURA' not in HTML


def test_los_manifiestos_casan_con_la_imagen_y_con_la_guia():
    # puerto y usuario del Dockerfile
    assert 'EXPOSE 8080' in DOCKERFILE and 'USER 10001' in DOCKERFILE
    assert 'containerPort: 8080' in DEPLOY and 'runAsUser: 10001' in DEPLOY and 'runAsNonRoot: true' in DEPLOY
    assert 'targetPort: 8080' in SERVICE and 'port: 80' in SERVICE
    # probes: readiness en /listo y liveness en /salud (no al revés)
    lect = DEPLOY.split('readinessProbe:')[1].split('livenessProbe:')[0]
    viva = DEPLOY.split('livenessProbe:')[1]
    assert 'path: /listo' in lect and 'path: /salud' in viva
    # nombres y etiqueta que usan los comandos de la práctica
    assert 'name: retencion-api' in DEPLOY and 'name: retencion-api' in SERVICE
    assert DEPLOY.count('app: retencion-api') >= 3 and 'app: retencion-api' in SERVICE
    assert 'image: retencion-api:local' in DEPLOY and 'imagePullPolicy: IfNotPresent' in DEPLOY
    assert 'replicas: 2' in DEPLOY and '- name: api' in DEPLOY            # «api=…» en kubectl set image
    for cmd in ('kubectl apply -f deploy/kubernetes/', 'kind load docker-image retencion-api:local --name curso',
                'kubectl port-forward service/retencion-api 8080:80', 'kubectl rollout undo deployment/retencion-api',
                'kubectl set image deployment/retencion-api api=retencion-api:no-existe'):
        assert cmd in HTML, cmd


def test_los_ejercicios_usan_lo_que_hay_en_los_manifiestos():
    for viejo in ('replicas: 2', 'image: retencion-api:local', 'memory: 1Gi'):
        assert viejo in EJERCICIOS and viejo in DEPLOY, viejo       # los sed de los ejercicios encuentran su texto
    assert 'CURSO_MODELOS' in EJERCICIOS and 'CURSO_MODELOS' in DOCKERFILE


def test_gke_va_marcado_como_no_ejecutado_y_con_la_sintaxis_de_la_documentacion():
    assert 'sin ejecutar' in HTML.lower() and 'sin ejecutar' in CHULETA.lower()
    for texto in (HTML, CHULETA):
        assert 'gcloud container clusters create-auto curso-gke --location=us-central1' in texto
        assert 'gcloud container clusters get-credentials curso-gke --location us-central1' in texto
        assert '--region' not in texto, 'la documentación vigente usa --location'
        assert 'docs.cloud.google.com/kubernetes-engine/docs/deploy-app-cluster' in texto


def test_no_se_inventan_precios():
    for texto in (HTML, CHULETA, EJERCICIOS):
        assert not re.search(r'\d+([.,]\d+)?\s*(€|\$|USD|EUR)\b', texto.replace('0 € (cuota del Codespace)', '')), 'no se dan precios'


def test_sin_recursos_externos():
    assert not re.search(r'<(script|link|img|iframe)\b[^>]*\b(src|href)="https?://', HTML)
