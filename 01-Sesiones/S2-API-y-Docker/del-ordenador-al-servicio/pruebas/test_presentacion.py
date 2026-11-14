"""Pruebas de la presentación «Del ordenador al servicio» (sin navegador).

Qué vigilan: que index.html está al día con generar.py; que las salidas «reales» que muestra son las mismas que cita la guía
de texto; que lo que manda copiar existe en el proyecto; notas, minutos y partes de cada diapositiva; sin recursos externos.
El aspecto (que nada se salga del marco) se revisa en un navegador real: ver el README de la carpeta o generar.py.
"""
import importlib.util
import re
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parents[1]
RAIZ = AQUI.parents[2]
PROYECTO = RAIZ / '04-Proyecto-Base'
GUIA = PROYECTO / 'docs' / 'del-ordenador-al-servicio.md'

_spec = importlib.util.spec_from_file_location('generar_del_ordenador', AQUI / 'generar.py')
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)


@pytest.fixture(scope='module')
def html():
    return (AQUI / 'index.html').read_text(encoding='utf-8')


def secciones(texto):
    return re.findall(r'<section class="slide"([^>]*)>(.*?)</section>', texto, re.S)


def test_esta_al_dia_con_el_generador(html):
    assert html == G.html_completo(), 'index.html no coincide con generar.py: ejecuta  python generar.py'


def test_cada_diapositiva_tiene_titulo_parte_minutos_y_notas(html):
    s = secciones(html)
    assert len(s) == 27
    total = 0
    for attrs, _ in s:
        assert re.search(r'data-part="[ABCD]"', attrs) and re.search(r'data-title="[^"]+"', attrs), attrs[:80]
        notas = re.search(r'data-notes="([^"]*)"', attrs).group(1)
        assert len(notas) > 80, f'notas del ponente demasiado cortas: {attrs[:80]}'
        total += int(re.search(r'data-min="(\d+)"', attrs).group(1))
    assert 55 <= total <= 65, total        # la práctica de S2 dice «unos 60 minutos»


def test_las_salidas_reales_son_las_que_cita_la_guia():
    guia = GUIA.read_text(encoding='utf-8')
    # cada línea significativa de cada salida tiene que estar, tal cual, en la guía de texto
    for clave, salida in G.SALIDAS.items():
        if clave.startswith('local_'):
            continue
        for linea in salida.split('\n'):
            linea = linea.strip()
            if clave in ('docker_ps', 'compose_ps') and linea.split()[0] in ('interfaz', 'api'):
                linea = ' '.join(linea.split()[:5])          # la guía lleva también la columna [::] de IPv6
                assert re.search(r'\s+'.join(map(re.escape, linea.split())), guia), (clave, linea)
                continue
            # la guía puede recortar el final de un mensaje largo con «…» (a partir de «¿Está arrancada…?»)
            assert linea in guia or linea.split(' ¿')[0] in guia, f'la salida «{clave}» no coincide con la guía: {linea}'


def test_los_archivos_y_las_ordenes_existen_en_el_proyecto(html):
    for ruta in ('deploy/docker/interfaz.Dockerfile', 'deploy/docker/Dockerfile', 'deploy/docker/compose.yaml',
                 'deploy/docker/interfaz.Dockerfile.dockerignore', 'docs/del-ordenador-al-servicio.md', 'sql/fs/02_poblar_fs.sql'):
        assert ruta in html or ruta.replace('deploy/docker/', '') in html, ruta
        assert (PROYECTO / ruta).is_file(), ruta
    assert (AQUI / 'img' / 'interfaz-consulta.png').is_file()
    # lo que se describe del Dockerfile es lo que hay en el Dockerfile
    dockerfile = (PROYECTO / 'deploy' / 'docker' / 'interfaz.Dockerfile').read_text(encoding='utf-8')
    for trozo in ('FROM python:3.11-slim', 'CURSO_DB=/datos/curso.db', 'CURSO_DB_SOLO_LECTURA=1', 'CURSO_URL_API=http://api:8080',
                  'pip install -c requirements-api.lock -r requirements-interfaz.txt', 'USER 10001', 'EXPOSE 8090', '"--host", "0.0.0.0", "--port", "8090"'):
        assert trozo in dockerfile, trozo
    compose = (PROYECTO / 'deploy' / 'docker' / 'compose.yaml').read_text(encoding='utf-8')
    assert '../../data/processed:/datos:ro' in compose and 'condition: service_healthy' in compose


def test_cada_orden_tiene_su_boton_de_copiar_y_el_enlace_de_vuelta(html):
    ordenes = re.findall(r'<div class="tln"><span class="ps">\$</span> <code>(.*?)</code><button class="cp" data-t="(.*?)"', html)
    assert len(ordenes) >= 20
    for visible, copiar in ordenes:
        assert visible == copiar
    assert '<a id="bhome" href="../index.html"' in html


def test_sin_recursos_externos(html):
    assert not re.search(r'<(script|link|img|iframe)\b[^>]*\b(src|href)="https?://', html)


def test_dos_diagramas_de_arquitectura_con_ids_de_marcador_unicos(html):
    assert html.count('aria-label="Arquitectura de la exposición del modelo"') == 2
    ids = re.findall(r'<marker id="([^"]+)"', html)
    assert len(ids) == len(set(ids)), 'ids de marcador repetidos: el navegador pinta flechas sin punta'
    for ref in set(re.findall(r'url\(#([^)]+)\)', html)):
        assert ref in ids, ref
