"""Pruebas del generador de PDF y de los PDF ya generados.

Las primeras no necesitan Chrome ni pandoc: revisan el manifiesto y las funciones puras.
Las del bloque «PDF generados» leen los archivos de `pdfs/` (no los generan): si cambias una fuente y no
regeneras, fallan, que es lo que se quiere.

Ejecutar:  python -m pytest 00-Planificacion/pdfs/pruebas -q
"""
import re
import shutil
import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import contenido_pdfs as C  # noqa: E402
import generar_pdfs as G  # noqa: E402

RAIZ = G.RAIZ
PALABRA_INTERNA = 'guia' + 'burros'  # escrita en dos trozos para que esta prueba no la contenga


def todos():
    return [(s, e) for s in C.SESIONES for e in s['elementos']]


def pdf(sesion_id, archivo):
    for s, e in todos():
        if s['id'] == sesion_id and e['archivo'] == archivo:
            return G.ruta_pdf(s, e)
    raise KeyError(archivo)


def texto_pagina(ruta, n):
    from pypdf import PdfReader
    return PdfReader(str(ruta)).pages[n - 1].extract_text() or ''


# ---------------------------------------------------------------------------
# Manifiesto
# ---------------------------------------------------------------------------
class TestManifiesto:
    def test_hay_s0_s1_y_s2(self):
        assert [s['id'] for s in C.SESIONES] == ['S0', 'S1', 'S2']

    @pytest.mark.parametrize('sesion,e', todos(), ids=[f"{s['id']}-{e['archivo']}" for s, e in todos()])
    def test_cada_origen_existe(self, sesion, e):
        assert (RAIZ / e['origen']).is_file(), e['origen']

    @pytest.mark.parametrize('sesion,e', todos(), ids=[f"{s['id']}-{e['archivo']}" for s, e in todos()])
    def test_campos_validos(self, sesion, e):
        assert e['tipo'] in ('presentacion', 'documento', 'pagina')
        assert e['grupo'] in C.GRUPOS
        assert e['titulo'].strip()
        assert re.fullmatch(r'\d\d-[a-z0-9]+(-[a-z0-9]+)*\.pdf', e['archivo']), e['archivo']
        esperado = '.md' if e['tipo'] == 'documento' else '.html'
        assert e['origen'].endswith(esperado)
        assert (e['tipo'] == 'presentacion') == (e['grupo'] == 'presentaciones')

    def test_archivos_sin_repetir_en_cada_carpeta(self):
        vistos = set()
        for s, e in todos():
            clave = str(G.ruta_pdf(s, e))
            assert clave not in vistos, clave
            vistos.add(clave)

    def test_numeracion_correlativa_por_carpeta(self):
        for s in C.SESIONES:
            for grupo in C.GRUPOS:
                nums = [int(e['archivo'][:2]) for e in s['elementos'] if e['grupo'] == grupo]
                assert nums == list(range(1, len(nums) + 1)), (s['id'], grupo, nums)

    def test_origenes_sin_repetir(self):
        origenes = [e['origen'] for _, e in todos()]
        assert len(origenes) == len(set(origenes))

    def test_ninguna_palabra_interna_en_el_manifiesto(self):
        texto = (AQUI.parent / 'contenido_pdfs.py').read_text(encoding='utf-8').lower()
        assert PALABRA_INTERNA not in texto
        assert PALABRA_INTERNA not in (AQUI.parent / 'generar_pdfs.py').read_text(encoding='utf-8').lower()

    def test_las_presentaciones_declaran_espera_razonable(self):
        for _, e in todos():
            if e['tipo'] == 'presentacion':
                assert 300 <= e['espera_ms'] <= 5000


# ---------------------------------------------------------------------------
# Funciones puras
# ---------------------------------------------------------------------------
class TestEnlaces:
    def test_relativo_a_archivo(self):
        r = G.enlaces_al_repositorio('<a href="../teoria/README.md">t</a>',
                                     '01-Sesiones/S1-Datos-y-Entrenamiento/practica/guia.md')
        assert f'{C.REPOSITORIO}/blob/{C.RAMA}/01-Sesiones/S1-Datos-y-Entrenamiento/teoria/README.md' in r

    def test_relativo_a_carpeta(self):
        r = G.enlaces_al_repositorio('<a href="../">c</a>', '01-Sesiones/S1-Datos-y-Entrenamiento/practica/guia.md')
        assert f'{C.REPOSITORIO}/tree/{C.RAMA}/01-Sesiones/S1-Datos-y-Entrenamiento"' in r

    def test_externos_y_anclas_no_cambian(self):
        for h in ('https://github.com/x', 'http://a.b', 'mailto:a@b.c', '#seccion'):
            assert G.enlaces_al_repositorio(f'<a href="{h}">x</a>', 'a/b.md') == f'<a href="{h}">x</a>'

    def test_conserva_el_fragmento(self):
        r = G.enlaces_al_repositorio('<a href="otro.md#paso-2">x</a>', '01-Sesiones/S1-Datos-y-Entrenamiento/README.md')
        assert r.count('#paso-2') == 1 and 'otro.md' in r

    def test_nunca_sale_file_url(self):
        r = G.enlaces_al_repositorio('<a href="x/y.md">x</a><a href="../../z">z</a>', '01-Sesiones/S0/README.md')
        assert 'file:' not in r


class TestResaltado:
    def test_python_se_colorea_y_se_conserva_el_texto(self):
        r = G.resaltar('<pre class="python"><code>def f(x):\n    return &quot;a&quot; &lt; x\n</code></pre>')
        assert 'class="codigo"' in r and '<span class="h-' in r
        assert 'def' in r and '&lt;' in r  # el menor que sigue escapado

    def test_lenguaje_desconocido_o_sin_lenguaje_no_falla(self):
        assert 'class="codigo"' in G.resaltar('<pre class="inventado"><code>x y\n</code></pre>')
        assert 'class="codigo"' in G.resaltar('<pre><code>x y\n</code></pre>')

    def test_bloque_largo_puede_partirse_entre_paginas(self):
        largo = '\n'.join(f'linea {i}' for i in range(60))
        assert 'codigo larga' in G.resaltar(f'<pre><code>{largo}\n</code></pre>')
        assert 'codigo larga' not in G.resaltar('<pre><code>corto\n</code></pre>')


@pytest.mark.skipif(not shutil.which('pandoc'), reason='falta pandoc')
class TestDocumentoHtml:
    def test_lista_de_tareas_tabla_y_codigo(self):
        md = '# T\n\n- [ ] uno\n- [x] dos\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n```bash\necho hola\n```\n'
        h = G.resaltar(G.pandoc_html(md))
        assert h.count('type="checkbox"') == 2
        assert '<table>' in h and '<th>a</th>' in h
        assert 'class="codigo"' in h and 'echo' in h

    def test_casilla_con_numero_no_se_convierte_en_lista_anidada(self):
        h = G.pandoc_html('- [ ] 1. Git instalado\n- [x] 10) VS Code\n')
        assert '<ol' not in h and h.count('type="checkbox"') == 2
        assert '1. Git instalado' in h and '10) VS Code' in h

    def test_proteger_numeros_solo_toca_casillas_numeradas(self):
        assert G.proteger_numeros_en_tareas('- [ ] 1. a') == '- [ ] 1\\. a'
        assert G.proteger_numeros_en_tareas('1. normal\n- [ ] sin numero\n- 2. no es casilla') == \
            '1. normal\n- [ ] sin numero\n- 2. no es casilla'

    def test_el_checklist_real_de_s0_sale_con_doce_casillas_y_sin_listas_anidadas(self):
        s = C.SESIONES[0]
        e = next(x for x in s['elementos'] if x['archivo'] == '02-checklist.pdf')
        h = G.pagina_documento(s, e)
        assert h.count('type="checkbox"') == 12 and '<ol' not in h

    def test_pagina_completa_de_un_documento_real(self):
        s = C.SESIONES[1]
        e = next(x for x in s['elementos'] if x['archivo'] == '02-guia-de-laboratorio.pdf')
        h = G.pagina_documento(s, e)
        assert h.startswith('<!doctype html>') and '<style>' in h
        assert C.CURSO in h and 'S1 · Datos y entrenamiento · Material del alumno' in h
        assert 'file:///' not in h
        assert PALABRA_INTERNA not in h.lower()


class TestLeeme:
    def test_lista_todos_los_pdf(self):
        t = G.texto_leeme()
        for s, e in todos():
            assert f'{s["carpeta"]}/{C.GRUPOS[e["grupo"]][1]}/{e["archivo"]}' in t
            assert e['titulo'] in t

    def test_el_archivo_leeme_esta_al_dia(self):
        assert (RAIZ / C.CARPETA_SALIDA / 'LEEME.md').read_text(encoding='utf-8') == G.texto_leeme()

    def test_explica_lo_que_se_pierde(self):
        assert 'animaciones' in G.texto_leeme()


# ---------------------------------------------------------------------------
# Retoques de texto solo para el PDF
# ---------------------------------------------------------------------------
class TestRetoquesDeTexto:
    def test_cada_frase_a_retocar_existe_en_alguna_fuente(self):
        """Si cambias el texto de una diapositiva, el retoque deja de aplicarse: esta prueba avisa."""
        fuentes = ''.join((RAIZ / e['origen']).read_text(encoding='utf-8')
                          for s, e in todos() if e['tipo'] == 'presentacion')
        for antes, _ in G.RETOQUES_TEXTO:
            assert antes in fuentes, f'ya no existe en ninguna presentación: {antes[:60]}'

    def test_los_retoques_no_dejan_ordenes_de_pulsar_botones_ni_dejan_texto_vacio(self):
        for antes, despues in G.RETOQUES_TEXTO:
            assert 'Haz clic' not in despues and 'Pulsa' not in despues and 'pulsa' not in despues
            assert despues != antes
            assert G.PALABRA_INTERNA not in despues

    def test_no_se_repiten_pares(self):
        antes = [a for a, _ in G.RETOQUES_TEXTO]
        assert len(antes) == len(set(antes))


# ---------------------------------------------------------------------------
# PDF generados
# ---------------------------------------------------------------------------
class TestPdfGenerados:
    def test_comprobar_no_encuentra_problemas(self):
        assert G.comprobar() == []

    def test_cuentan_con_metadatos_y_marcadores(self):
        from pypdf import PdfReader
        for s, e in todos():
            lector = PdfReader(str(G.ruta_pdf(s, e)))
            meta = lector.metadata
            assert e['titulo'] in meta.title and meta.author == C.AUTOR, e['archivo']
            if e['tipo'] == 'presentacion':
                assert len(lector.outline) == len(lector.pages), e['archivo']

    def test_ningun_pdf_tiene_enlaces_a_archivos_locales(self):
        for s, e in todos():
            assert b'file:///' not in G.ruta_pdf(s, e).read_bytes(), e['archivo']

    def test_s0_presentacion_contadores_con_su_valor_final(self):
        ruta = pdf('S0', '01-presentacion-principal.pdf')
        t11 = texto_pagina(ruta, 11)
        assert '20%' in t11 and t11.count('40%') == 2 and '0%\n' not in t11.replace('20%', '').replace('40%', '')
        assert '45 %' in texto_pagina(ruta, 5)

    def test_s0_presentacion_sin_botones_de_control(self):
        ruta = pdf('S0', '01-presentacion-principal.pdf')
        from pypdf import PdfReader
        todo = ' '.join(p.extract_text() or '' for p in PdfReader(str(ruta)).pages)
        for boton in ('Ver demo', 'Copiar comandos', 'Reiniciar conteo', 'Mostrar guía', 'Iniciar pausa'):
            assert boton not in todo, boton
        for orden in ('Haz clic', 'pulsa la opción', 'Se guarda en este navegador'):
            assert orden not in todo, orden

    def test_s0_terminales_muestran_la_salida_de_ejemplo(self):
        ruta = pdf('S0', '01-presentacion-principal.pdf')
        assert 'Hello from Docker!' in texto_pagina(ruta, 23)
        assert 'Receiving objects' in texto_pagina(ruta, 19)

    def test_s0_diapositivas_en_orden(self):
        ruta = pdf('S0', '01-presentacion-principal.pdf')
        for n in (1, 14, 31):
            assert f'{n} / 31' in texto_pagina(ruta, n).replace('  ', ' ')

    def test_presentacion_de_instalacion_sin_botones_de_copiar(self):
        ruta = pdf('S0', '02-tu-equipo-listo-para-s1.pdf')
        from pypdf import PdfReader
        todo = ' '.join(p.extract_text() or '' for p in PdfReader(str(ruta)).pages)
        assert 'Marcar como hecho' not in todo and 'Copiar todo' not in todo
        assert '⧉' not in todo and 'copia todo el bloque' not in todo
        assert 'Tu equipo listo para S1' in texto_pagina(ruta, 1)

    def test_s1_presentacion_sin_ordenes_de_hacer_clic(self):
        from pypdf import PdfReader
        ruta = pdf('S1', '01-presentacion-s1.pdf')
        todo = ' '.join(p.extract_text() or '' for p in PdfReader(str(ruta)).pages)
        assert 'Hacer clic' not in todo and 'Haz clic' not in todo

    def test_s2_presentacion_sin_ordenes_de_hacer_clic_ni_botones_de_control(self):
        from pypdf import PdfReader
        ruta = pdf('S2', '01-presentacion-s2.pdf')
        paginas = PdfReader(str(ruta)).pages
        assert len(paginas) == 21
        todo = ' '.join(p.extract_text() or '' for p in paginas)
        assert 'Hacer clic' not in todo and 'Haz clic' not in todo
        assert 'Pantalla completa (F)' not in todo

    def test_s2_guia_de_codespaces_sin_controles_de_la_pagina(self):
        from pypdf import PdfReader
        paginas = PdfReader(str(pdf('S2', '02-guia-de-codespaces.pdf'))).pages
        assert len(paginas) == 38          # con las diapositivas «Así se ve» del Codespace real (12/11/2026)
        todo = ' '.join(p.extract_text() or '' for p in paginas)
        for sobra in ('⧉', 'Marcar como hecho', 'Copiar todo', 'pasos marcados', 'en este navegador',
                      'C copia todo el bloque', 'file:///'):
            assert sobra not in todo, sobra
        assert 'Copia cada línea y pégala en la terminal del Codespace' in todo
        # lo esencial del laboratorio sigue en el PDF
        for debe in ('docker version', 'docker build -f deploy/docker/Dockerfile -t retencion-api:local .', '10001'):
            assert debe in todo.replace('\n', ' '), debe

    def test_s2_conserva_las_cifras_reales_de_la_practica(self):
        from pypdf import PdfReader
        todo = ' '.join(p.extract_text() or '' for p in PdfReader(str(pdf('S2', '01-presentacion-s2.pdf'))).pages)
        assert '0.8278889191932133' in todo.replace(' ', '') and '108 passed' in todo

    @pytest.mark.parametrize('archivo,paginas', [('03-contenedores-el-modelo-mental.pdf', 16), ('04-del-dockerfile-a-produccion.pdf', 17)])
    def test_s2_presentaciones_de_contenedores_sin_controles_y_con_lo_no_probado(self, archivo, paginas):
        from pypdf import PdfReader
        lector = PdfReader(str(pdf('S2', archivo)))
        assert len(lector.pages) == paginas
        todo = ' '.join(p.extract_text() or '' for p in lector.pages).replace('\n', ' ')
        for sobra in ('⧉', 'Marcar como hecho', 'pasos marcados', 'en este navegador', 'Pulsa', 'pulsa', 'Hacer clic', 'Haz clic',
                      'Pantalla completa', 'file:///'):
            assert sobra not in todo, sobra
        assert 'Copia cada línea y pégala en la terminal de tu Codespace' in todo
        assert 'Comprueba cada punto antes de pasar a lo siguiente' in todo
        # lo que no se ha probado sigue diciéndose en el PDF
        assert 'Todavía no se han ejecutado en un Codespace del curso' in todo
        assert 'docker 29.4.2'.lower() in todo.lower()
        assert 'sin probar aquí' in todo.lower()

    def test_s2_contenedores_conservan_las_salidas_reales_y_los_comandos(self):
        from pypdf import PdfReader
        def texto(archivo):
            return ' '.join(' '.join(p.extract_text() or '' for p in PdfReader(str(pdf('S2', archivo))).pages).split())
        modelo, produccion = texto('03-contenedores-el-modelo-mental.pdf'), texto('04-del-dockerfile-a-produccion.pdf')
        assert 'Exited (137)' in modelo and 'Failed to connect' in modelo and 'Connection reset by peer' in modelo
        assert '52.44MB' in produccion and '178B' in produccion and 'CACHED' in produccion and 'USER 10001' in produccion
        guia, lab = texto('08-guia-practica-de-contenedores.pdf'), texto('09-laboratorio-romper-a-proposito.pdf')
        assert 'docker run --rm' in guia and 'docker build --progress=plain' in guia and 'Exited (137)' in guia
        for n in range(1, 6):
            assert f'Rotura {n}' in lab, n
        assert 'Todavía no se han ejecutado en un Codespace' in guia and 'Todavía no se han ejecutado en un Codespace' in lab

    def test_los_pdf_de_documentos_estan_al_dia_con_su_fuente(self):
        """Cada título de la fuente Markdown (sin bloques de código) aparece en su PDF: si se edita el .md y no se regenera, falla.
        Se compara sin espacios ni marcas de código porque el PDF parte las líneas largas en cualquier punto."""
        from pypdf import PdfReader

        def limpio(s):
            return re.sub(r'\s+', '', re.sub(r'[`*_]', '', s)).lower()

        desactualizados = []
        for s, e in todos():
            if e['tipo'] != 'documento':
                continue
            texto = limpio(' '.join(p.extract_text() or '' for p in PdfReader(str(G.ruta_pdf(s, e))).pages))
            fuente = re.sub(r'```.*?```', '', (RAIZ / e['origen']).read_text(encoding='utf-8'), flags=re.S)
            titulos = [re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', h) for h in re.findall(r'^#{1,4} +(.+?)\s*$', fuente, re.M)]
            faltan = [h for h in titulos if limpio(h) not in texto]
            if faltan:
                desactualizados.append((s['id'], e['archivo'], faltan[:3]))
        assert desactualizados == [], f'PDF sin regenerar tras editar su fuente: {desactualizados}'

    def test_documentos_con_pie_de_pagina_en_todas_las_paginas(self):
        from pypdf import PdfReader
        for s, e in todos():
            if e['tipo'] != 'documento':
                continue
            lector = PdfReader(str(G.ruta_pdf(s, e)))
            n = len(lector.pages)
            for i, p in enumerate(lector.pages, 1):
                assert f'Página {i} de {n}' in (p.extract_text() or ''), (e['archivo'], i)

    def test_guia_rapida_conserva_comandos_y_tablas(self):
        ruta = pdf('S0', '01-guia-rapida-del-entorno.pdf')
        from pypdf import PdfReader
        todo = ' '.join(p.extract_text() or '' for p in PdfReader(str(ruta)).pages)
        assert 'conda env create' in todo and 'environment.yml' in todo and 'LISTO PARA S1' in todo

    def test_rubrica_conserva_los_porcentajes(self):
        ruta = pdf('S1', '04-rubrica.pdf')
        from pypdf import PdfReader
        todo = ' '.join(p.extract_text() or '' for p in PdfReader(str(ruta)).pages)
        assert '20' in todo and '40' in todo
