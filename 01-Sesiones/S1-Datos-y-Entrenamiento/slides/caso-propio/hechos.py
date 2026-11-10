"""Las cifras de Bank Marketing que aparecen en la hoja del alumno y en la presentación «Tu caso de S1 a S5».

Se miden aquí, sobre el CSV del repositorio y con el módulo `csv` (sin pandas). La presentación toma las cifras de aquí
y las pruebas comprueban que la hoja del alumno dice lo mismo. Nada de esto es un resultado de modelo: son recuentos del archivo.
"""
import csv
import json
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[3]
CSV = RAIZ / '02-Proyecto-Transversal' / 'datos' / 'bank-marketing' / 'bank-additional-full.csv'
S0_SALIDAS = RAIZ / '01-Sesiones' / 'S0-Presentacion-y-Entorno' / 'slides' / 'instalacion' / 'salidas-reales.json'
MESES = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
UNKNOWN_EN = ['job', 'marital', 'education', 'default', 'housing', 'loan']


def miles(n):
    """41188 -> '41 188' (espacio normal; en HTML se sustituye por uno que no parte la línea)."""
    return f'{n:,}'.replace(',', ' ')


def pct(a, b):
    """4640, 41188 -> '11,27 %'."""
    return f'{100 * a / b:.2f}'.replace('.', ',') + ' %'


def medir(ruta=CSV):
    with open(ruta, newline='', encoding='utf-8') as f:
        lector = csv.reader(f, delimiter=';')
        cab = next(lector)
        filas = list(lector)
    ix = {c: i for i, c in enumerate(cab)}

    def col(c):
        return [x[ix[c]] for x in filas]

    n = len(filas)
    y = Counter(col('y'))
    previas = [int(v) for v in col('previous')]
    pdays = [int(v) for v in col('pdays')]
    poutcome = col('poutcome')
    repetidas = Counter(map(tuple, filas))
    grupos = [v for v in repetidas.values() if v > 1]
    dur0 = [x[ix['y']] for x in filas if x[ix['duration']] == '0']
    meses = set(col('month'))
    return dict(
        columnas=cab,
        n_columnas=len(cab),
        n_variables=len(cab) - 1,
        filas=n,
        si=y['yes'],
        no=y['no'],
        pct_si=pct(y['yes'], n),
        pct_acierto_siempre_no=pct(y['no'], n),
        unknown={c: sum(1 for v in col(c) if v == 'unknown') for c in UNKNOWN_EN},
        pares_identicos=sum(1 for v in grupos if v == 2),
        grupos_identicos=len(grupos),
        filas_extra_identicas=sum(v - 1 for v in grupos),
        pdays_999=sum(1 for v in pdays if v == 999),
        previous_pos_y_pdays_999=sum(1 for p, d in zip(previas, pdays) if p > 0 and d == 999),
        previous_0=sum(1 for p in previas if p == 0),
        poutcome_nonexistent=sum(1 for v in poutcome if v == 'nonexistent'),
        nonexistent_es_previous_0=all((p == 0) == (o == 'nonexistent') for p, o in zip(previas, poutcome)),
        meses_ausentes=[m for m in MESES if m not in meses],
        duration_0=len(dur0),
        duration_0_todas_no=all(v == 'no' for v in dur0),
        edad_min=min(int(v) for v in col('age')),
        edad_max=max(int(v) for v in col('age')),
        default_yes=sum(1 for v in col('default') if v == 'yes'),
    )


def salida_lectura():
    """El comando de lectura y su salida real, tal como se midieron al preparar S0 (una sola fuente)."""
    d = json.loads(S0_SALIDAS.read_text(encoding='utf-8'))['salidas']['csv']
    return d['cmd'], d['salida']


H = medir()
