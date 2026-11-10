"""Pruebas del material «Tu caso: Bank Marketing» (hoja del alumno, plantilla y rúbrica del avance, y la presentación «Tu caso de S1 a S5»).

Ejecutar:  python -m pytest 01-Sesiones/S1-Datos-y-Entrenamiento/slides/caso-propio/pruebas -q
No necesitan Internet ni navegador: comprueban que las cifras de los textos coinciden con el CSV del repositorio, que la presentación está al día,
que los documentos y la presentación dicen lo mismo, que no se regala ninguna cifra de modelo y que todos los enlaces existen.
(El aspecto en un navegador real se revisa con comprobar_diseno.py, que necesita Playwright.)
"""
import ast
import html as hlib
import re
import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AQUI))
import deck as D  # noqa: E402
import generar as G  # noqa: E402
import hechos  # noqa: E402
from hechos import H, miles  # noqa: E402

RAIZ = hechos.RAIZ
ALUMNO = RAIZ / '02-Proyecto-Transversal' / 'alumno'
HOJA = ALUMNO / 'tu-caso-bank-marketing.md'
PLANTILLA = ALUMNO / 'plantilla-avance.md'
RUBRICA = ALUMNO / 'rubrica-avance.md'
DOCS = [HOJA, PLANTILLA, RUBRICA]
DECK = AQUI / 'index.html'
S1 = RAIZ / '01-Sesiones' / 'S1-Datos-y-Entrenamiento'
S2 = RAIZ / '01-Sesiones' / 'S2-API-y-Docker'
ENUNCIADO = RAIZ / '02-Proyecto-Transversal' / 'enunciado' / 'README.md'
PALABRA_PROHIBIDA = re.compile(r'gu[ií]a[\s_-]*burros?', re.I)


def leer(ruta):
    return ruta.read_text(encoding='utf-8').replace(' ', ' ')


def texto_html(ruta):
    h = leer(ruta)
    h = re.sub(r'<(script|style)\b.*?</\1>', ' ', h, flags=re.S)
    return re.sub(r'\s+', ' ', hlib.unescape(re.sub(r'<[^>]+>', ' ', h)))


def hoja_sin_codigo():
    return re.sub(r'```.*?```', '', leer(HOJA), flags=re.S)


# ------------------------------------------------------------------------------------------ las cifras
def test_las_cifras_medidas_coinciden_con_la_salida_real_de_s0():
    """Una fuente independiente: lo que imprimió el comando de lectura al preparar S0."""
    _, salida = hechos.salida_lectura()
    assert f'({H["filas"]}, {H["n_columnas"]})' in salida
    reales = ast.literal_eval(salida.split('\n')[1])   # {'no': ..., 'yes': ...}
    assert reales == {'no': H['no'], 'yes': H['si']}


def test_las_cifras_basicas_son_las_documentadas():
    assert H['filas'] == 41188 and H['n_columnas'] == 21 and H['n_variables'] == 20
    assert H['si'] + H['no'] == H['filas']
    assert H['pct_si'] == '11,27 %'
    assert H['columnas'][-1] == 'y' and 'duration' in H['columnas']
    assert H['grupos_identicos'] == H['pares_identicos'] == H['filas_extra_identicas'] == 12, 'la hoja habla de 12 pares: si hubiera tríos habría que decirlo'
    assert H['nonexistent_es_previous_0'] and H['poutcome_nonexistent'] == H['previous_0']
    assert H['duration_0_todas_no'] and H['duration_0'] == 4
    assert H['meses_ausentes'] == ['jan', 'feb']


def test_hay_seis_columnas_con_unknown_y_ninguna_otra():
    import csv
    with open(hechos.CSV, newline='', encoding='utf-8') as f:
        lector = csv.DictReader(f, delimiter=';')
        con = {c for fila in lector for c, v in fila.items() if v == 'unknown'}
    assert con == set(H['unknown']), 'otra columna tiene unknown y la hoja no lo cuenta'


def cifras_esperadas():
    u = H['unknown']
    return [
        miles(H['filas']), H['pct_si'], miles(H['si']), miles(H['no']), f'{H["pares_identicos"]} pares',
        ' · '.join(f'`{c}` {miles(u[c])}' for c in ['job', 'marital', 'education', 'default', 'housing', 'loan']),
        f'{miles(H["pdays_999"])} filas', f'{miles(H["previous_pos_y_pdays_999"])} filas', f'{miles(H["poutcome_nonexistent"])} filas',
        f'{H["pct_acierto_siempre_no"]} de las veces', f'de {H["edad_min"]} a {H["edad_max"]}', f'solo {H["default_yes"]} `yes`',
        f'pasa en {H["duration_0"]} filas',
    ]


def tabla_de_cifras():
    """La tabla del apartado 3 de la hoja, como {etiqueta: valor}."""
    t = leer(HOJA)
    bloque = t.split('## 3. Cifras para comprobar tu carga')[1].split('## 4.')[0]
    return {a.strip(): b.strip() for a, b in re.findall(r'^\| ([^|]+) \| ([^|]+) \|$', bloque, flags=re.M) if a.strip() not in ('Qué', '---')}


def test_la_tabla_de_cifras_de_la_hoja_es_exactamente_la_medida():
    u = H['unknown']
    assert tabla_de_cifras() == {
        'Filas · columnas': f'{miles(H["filas"])} · {H["n_columnas"]} ({H["n_variables"]} variables + `y`)',
        '`y` = `yes`': f'{miles(H["si"])} ({H["pct_si"]})',
        '`y` = `no`': miles(H['no']),
        f'Filas idénticas a otra (en las {H["n_columnas"]} columnas)': f'{H["pares_identicos"]} pares',
        'Valores `unknown`': ' · '.join(f'`{c}` {miles(u[c])}' for c in ['job', 'marital', 'education', 'default', 'housing', 'loan']),
        '`pdays` = 999': f'{miles(H["pdays_999"])} filas',
        '`previous` > 0 y `pdays` = 999 a la vez': f'{miles(H["previous_pos_y_pdays_999"])} filas',
        '`poutcome` = `nonexistent`': f'{miles(H["poutcome_nonexistent"])} filas (son exactamente las de `previous` = 0)',
        'Meses presentes': 'todos menos enero y febrero; no hay año ni fecha en ninguna columna',
    }


def test_todo_numero_con_miles_de_la_hoja_y_de_la_presentacion_es_una_cifra_medida():
    """Un número viejo olvidado en otro apartado (por ejemplo, en «Decisiones que son tuyas») no pasaría esta prueba."""
    medidas = {miles(H[k]) for k in ['filas', 'si', 'no', 'pdays_999', 'previous_pos_y_pdays_999', 'poutcome_nonexistent']} | {miles(v) for v in H['unknown'].values()}
    for ruta in [HOJA, DECK]:
        t = re.sub(r'```.*?```', '', leer(ruta) if ruta == HOJA else texto_html(ruta), flags=re.S)
        for grande in re.findall(r'(?<![\d.])\d{1,3}(?: \d{3})+(?![\d])', t):
            assert grande in medidas, f'{ruta.name}: «{grande}» no es una cifra medida'


@pytest.mark.parametrize('cifra', cifras_esperadas())
def test_la_hoja_dice_las_cifras_medidas(cifra):
    assert cifra in leer(HOJA), f'la hoja no contiene «{cifra}»'


def test_la_presentacion_usa_las_cifras_medidas():
    t = texto_html(DECK)
    u = H['unknown']
    for esperado in [miles(H['filas']), H['pct_si'], miles(H['si']), miles(H['no']), f'{H["pares_identicos"]} pares', f'{miles(H["pdays_999"])} filas',
                     f'{miles(H["previous_pos_y_pdays_999"])} de ellas', f'({miles(H["poutcome_nonexistent"])})', f'{H["duration_0"]} filas de este archivo',
                     f'({H["filas"]}, {H["n_columnas"]})'] + [f'{c} {miles(u[c])}' for c in u]:
        assert esperado in t, f'la presentación no contiene «{esperado}»'


def test_el_comando_de_lectura_es_el_verificado_en_s0_y_esta_en_la_hoja_y_en_la_presentacion():
    cmd, salida = hechos.salida_lectura()
    assert cmd in leer(HOJA)
    assert salida in leer(HOJA)
    assert hlib.escape(cmd, quote=True) in leer(DECK) and hlib.escape(salida, quote=True) in leer(DECK)


def test_el_csv_cuadra_con_su_huella_registrada():
    import hashlib
    sumas = (RAIZ / '02-Proyecto-Transversal' / 'datos' / 'SHA256SUMS').read_text(encoding='utf-8')
    esperada = next(l.split()[0] for l in sumas.splitlines() if l.endswith('bank-additional-full.csv'))
    assert hashlib.sha256(hechos.CSV.read_bytes()).hexdigest() == esperada


# ------------------------------------------------------------------------------------------ la presentación
def test_la_presentacion_esta_al_dia():
    for ruta, texto in G.contenidos().items():
        assert ruta.read_text(encoding='utf-8') == texto, 'ejecuta python generar.py en slides/caso-propio'


def test_son_doce_diapositivas_con_titulos_distintos():
    secciones = re.findall(r'<section class="slide"[^>]*data-title="([^"]*)"', DECK.read_text(encoding='utf-8'))
    assert len(secciones) == 12
    assert len(set(secciones)) == 12
    assert secciones[0] == 'Portada' and secciones[-1] == 'Lista final'


def test_el_boton_de_indice_lleva_al_indice_de_s1():
    h = DECK.read_text(encoding='utf-8')
    m = re.search(r'<a id="bhome" href="([^"]+)" title="([^"]+)">', h)
    assert m and m.group(2) == 'Volver al índice de la sesión S1'
    assert (DECK.parent / m.group(1)).resolve() == S1 / 'index.html'
    assert '<span class="tx">Índice de </span>S1</a>' in h


def test_el_marco_de_s2_sigue_apuntando_al_indice_de_s2_por_defecto():
    p = D.marco.Presentacion('t', 'clave', 'c', 'n')
    p.agregar('x', 'b', '<p>x</p>')
    assert 'href="../../index.html" title="Volver al índice de la sesión S2">⌂ <span class="tx">Índice de </span>S2</a>' in p.html()


def test_la_presentacion_no_da_instrucciones_de_pulsar_porque_el_pdf_no_las_puede_quitar():
    t = texto_html(DECK)
    assert 'Pulsa' not in t and 'pulsa' not in t and 'Haz clic' not in t


def test_la_presentacion_tiene_tres_lineas_copiables_y_cada_una_es_un_comando_completo():
    h = DECK.read_text(encoding='utf-8')
    copiables = [hlib.unescape(x) for x in re.findall(r'<button class="cp" data-t="([^"]*)"', h)]
    assert copiables == [hechos.salida_lectura()[0], 'cd 02-Proyecto-Transversal/datos', 'sha256sum -c SHA256SUMS']


# ------------------------------------------------------------------------------------------ nada de cifras de referencia
PRESENTE_EN = DOCS + [DECK]


@pytest.mark.parametrize('ruta', PRESENTE_EN, ids=lambda r: r.name)
def test_no_se_regalan_cifras_de_modelo(ruta):
    """Los AUC de referencia son del instructor (decisión del 10/11/2026): ni decimales de tres cifras, ni «AUC» seguido de un número, ni la deriva medida."""
    t = leer(ruta) if ruta != DECK else texto_html(ruta)
    assert not re.search(r'\b0[.,]\d{3}\b', t), 'hay un decimal de tres cifras (¿un AUC?)'
    assert not re.search(r'AUC[^.\n]{0,25}\b0[.,]\d', t), 'hay un AUC con cifra'
    for prohibida in ['38,5', '5,6 %', '0,935', '0,950', '0,787', '0,804']:
        assert prohibida not in t, f'«{prohibida}» es una cifra de referencia del instructor'


@pytest.mark.parametrize('ruta', PRESENTE_EN, ids=lambda r: r.name)
def test_no_aparece_la_palabra_prohibida(ruta):
    assert not PALABRA_PROHIBIDA.search(leer(ruta))


def test_los_documentos_no_enlazan_al_enunciado_del_instructor_que_si_trae_cifras():
    for ruta in DOCS + [DECK]:
        assert 'enunciado' not in leer(ruta), f'{ruta.name} apunta al enunciado, que contiene las cifras de referencia'
        assert 'verificacion-datos-tarea' not in leer(ruta)


# ------------------------------------------------------------------------------------------ coherencia entre documentos
def test_los_enlaces_relativos_de_los_documentos_existen():
    for ruta in DOCS:
        for destino in re.findall(r'\]\(([^)#]+)(?:#[^)]*)?\)', leer(ruta)):
            if destino.startswith(('http://', 'https://', 'mailto:')):
                continue
            assert (ruta.parent / destino).resolve().exists(), f'{ruta.name}: el enlace «{destino}» no existe'


def test_la_hoja_enlaza_a_la_plantilla_la_rubrica_y_la_presentacion():
    t = leer(HOJA)
    assert '(plantilla-avance.md)' in t and '(rubrica-avance.md)' in t
    assert '(../../01-Sesiones/S1-Datos-y-Entrenamiento/slides/caso-propio/index.html)' in t


def tabla_de_avances():
    filas = re.findall(r'^\| \*\*(\d|Final)\*\* \| ([^|]+) \| ([^|]+) \| ', leer(HOJA), flags=re.M)
    return [(a, b.strip(), c.strip()) for a, b, c in filas]


def test_la_hoja_tiene_la_tabla_de_avances_del_enunciado():
    assert tabla_de_avances() == [('1', 'S1 y trabajo autónomo', 'S2'), ('2', 'S2 y trabajo autónomo', 'S3'), ('3', 'S3 y trabajo autónomo', 'S4'),
                                  ('4', 'S4 y trabajo autónomo', 'S5'), ('Final', 'tras S5', 'por definir')]
    e = leer(ENUNCIADO)
    for origen, destino in [('S1', 'S2'), ('S2', 'S3'), ('S3', 'S4'), ('S4', 'S5')]:
        assert f'{origen} → avance en {destino}' in e, f'el enunciado no dice «{origen} → avance en {destino}»'


def test_la_presentacion_tiene_la_misma_tabla_de_avances():
    t = texto_html(DECK)
    for a, trabajo, presenta in tabla_de_avances():
        assert f'{a} {trabajo} {presenta}' in t, f'la presentación no tiene la fila del avance {a}'


def test_la_ruta_b_de_s2_es_el_avance_2_en_los_tres_sitios():
    assert 'Ruta B' in leer(HOJA) and 'Ruta B' in texto_html(DECK)
    assert 'Bank Marketing' in leer(S2 / 'tarea' / 'README.md')


def test_las_fechas_se_dicen_por_definir_y_no_se_inventan():
    for t in [leer(HOJA), texto_html(DECK)]:
        assert 'no están definidas' in t
        assert not re.search(r'\b\d{1,2}/\d{1,2}/20\d\d\b|\b\d{1,2} de (enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre) de 20\d\d', t.replace('mayo de 2008 a noviembre de 2010', ''))


def pesos_de(ruta):
    filas = re.findall(r'^\| \*\*([^*|]+)\*\* \| (\d+) \|', leer(ruta), flags=re.M)
    return [(n.strip(), int(p)) for n, p in filas]


def test_la_rubrica_del_avance_pesa_20_40_40_como_las_de_s1_y_s2():
    esperado = [('Reproducibilidad', 20), ('Técnica', 40), ('Análisis y decisión', 40)]
    assert pesos_de(RUBRICA) == esperado
    assert pesos_de(S1 / 'tarea' / 'rubrica.md') == esperado
    assert pesos_de(S2 / 'tarea' / 'rubrica.md') == esperado
    assert sum(p for _, p in esperado) == 100


def test_la_rubrica_cubre_los_cuatro_avances_y_las_alertas_que_cita_la_presentacion():
    t = leer(RUBRICA)
    for avance in ['1 · capas y entrenamiento', '2 · Python, API y contenedor', '3 · GCP', '4 · GitHub Actions']:
        assert avance in t
    for alerta in ['no supera 15', 'no supera 8']:
        assert alerta in t and alerta in texto_html(DECK)
    assert 'duration' in t and 'raw = master + descartes' in t


def test_la_plantilla_pide_lo_que_dice_el_enunciado_de_cada_avance():
    """El enunciado: «resultado, ejecución, pruebas, una decisión, dificultades y pasos reproducibles»."""
    t = leer(PLANTILLA)
    for seccion in ['## 1. Resultado', '## 2. Cómo se ejecuta', '## 3. Pruebas', '## 4. Una decisión', '## 5. Dificultades', '## 7. Pasos para que otra persona lo reproduzca']:
        assert seccion in t
    for avance in ['### Avance 1', '### Avance 2', '### Avance 3', '### Avance 4']:
        assert avance in t
    assert 'resultado, ejecución, pruebas, una decisión, dificultades y pasos reproducibles' in leer(ENUNCIADO)


def test_la_plantilla_de_cifras_pide_las_mismas_que_la_hoja_da():
    t = leer(PLANTILLA)
    assert 'comparar con el apartado 3 de la hoja' in t
    assert '## 3. Cifras para comprobar tu carga' in leer(HOJA)


def test_la_hoja_cita_la_fuente_y_dice_que_duration_queda_fuera():
    t = leer(HOJA)
    assert 'https://doi.org/10.24432/C5K306' in t
    assert 'doi:10.24432/C5K306' in texto_html(DECK)
    assert 'doi:10.1016/j.dss.2014.03.001' in t
    leeme = leer(RAIZ / '02-Proyecto-Transversal' / 'datos' / 'LEEME.md')
    assert 'https://doi.org/10.24432/C5K306' in leeme and 'doi:10.1016/j.dss.2014.03.001' in leeme
    assert '**`duration` (la duración de la llamada) queda fuera del modelo**' in t


def test_los_modelos_y_metricas_de_la_hoja_son_los_que_entrena_el_proyecto_base():
    train = (RAIZ / '04-Proyecto-Base' / 'ia_mlops' / 'modeling' / 'train.py').read_text(encoding='utf-8')
    for nombre in ['DummyClassifier', 'LogisticRegression', 'HistGradientBoostingClassifier', 'roc_auc_score', 'average_precision_score']:
        assert nombre in train
    assert 'referencia sin aprender, regresión logística y *gradient boosting*' in leer(HOJA)


def test_la_hoja_nombra_las_cuatro_capas_y_las_cuatro_decisiones_de_la_presentacion():
    t = leer(HOJA)
    for capa in ['**RAW**', '**MASTER**', '**FS**', '**ML**', '**Entrenamiento**']:
        assert capa in t
    d = texto_html(DECK)
    for decision in ['unknown', 'Filas idénticas', 'pdays', 'campaign', 'Contexto económico']:
        assert decision in d
    for decision in ['**`unknown`**', '**Filas idénticas**', '**`pdays` = 999 y `previous`**', '**`campaign`**', '**Indicadores económicos**']:
        assert decision in t


# ------------------------------------------------------------------------------------------ que las tablas se vean como tablas
def tablas_declaradas(texto):
    """Cuántas tablas hay: una por cada fila separadora (`|---|---|`) fuera de los bloques de código."""
    sin_codigo = re.sub(r'```.*?```', '', texto, flags=re.S)
    return len(re.findall(r'^\|[\s:|-]*---[\s:|-]*\|$', sin_codigo, flags=re.M))


@pytest.mark.parametrize('ruta', DOCS, ids=lambda r: r.name)
def test_cada_tabla_va_precedida_de_una_linea_en_blanco_y_sin_sangria(ruta):
    lineas = leer(ruta).split('\n')
    en_codigo = False
    for i, linea in enumerate(lineas):
        if linea.startswith('```'):
            en_codigo = not en_codigo
        if en_codigo:
            continue
        if re.match(r'^\s+\|', linea):
            pytest.fail(f'{ruta.name}, línea {i + 1}: tabla con sangría (queda dentro de una lista)')
        if linea.startswith('|') and i and not lineas[i - 1].startswith('|') and lineas[i - 1].strip():
            pytest.fail(f'{ruta.name}, línea {i + 1}: la tabla no tiene una línea en blanco antes y se vería como texto con barras')


@pytest.mark.parametrize('ruta', DOCS, ids=lambda r: r.name)
def test_pandoc_convierte_en_tabla_todas_las_tablas_declaradas(ruta):
    import shutil
    import subprocess
    if not shutil.which('pandoc'):
        pytest.skip('falta pandoc')
    r = subprocess.run(['pandoc', '-f', 'gfm', '-t', 'html5', '--no-highlight', '--wrap=none'], input=ruta.read_text(encoding='utf-8'),
                       capture_output=True, text=True, encoding='utf-8', check=True)
    assert r.stdout.count('<table') == tablas_declaradas(leer(ruta))
