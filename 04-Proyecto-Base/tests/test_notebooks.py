"""Los cuadernos SON los pipelines; el paquete ia_mlops es su traduccion a .py.
Estas pruebas exigen que ambos produzcan EXACTAMENTE las mismas tablas y las mismas metricas.

Son lentas (ejecutan los cinco cuadernos): pytest -m lento   |   para omitirlas: pytest -m "not lento"
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from ia_mlops import config, db
from ia_mlops.modeling import train

papermill = pytest.importorskip('papermill')
pytestmark = pytest.mark.lento

CUADERNOS = ['00_pipeline_operacional', '01_pipeline_raw_a_master', '02_pipeline_master_a_fs', '03_pipeline_fs_a_ml',
             '04_entrenamiento_y_seguimiento']
TABLAS_OPERACIONALES = ['clientes', 'productos', 'facturas', 'lineas_factura']
TABLAS = ['raw_clientes', 'raw_productos', 'raw_facturas', 'raw_lineas_factura', 'master_clientes', 'master_productos',
          'master_facturas', 'master_lineas', 'master_descartes', 'fs_catalogo', 'fs_cliente_corte', 'ml_particiones', 'ml_dataset']


def _tabla(con, nombre):
    df = pd.read_sql(f'SELECT * FROM {nombre}', con)
    return df.sort_values(list(df.columns)).reset_index(drop=True)


def _comparar(ruta_a, ruta_b, tablas, sin_fecha):
    """Compara tablas enteras; las de sin_fecha, sin su columna de marca de tiempo."""
    a, b = db.conectar(ruta_a), db.conectar(ruta_b)
    try:
        for nombre in tablas:
            pd.testing.assert_frame_equal(_tabla(a, nombre), _tabla(b, nombre), obj=nombre)
        for nombre, columna in sin_fecha.items():
            pd.testing.assert_frame_equal(_tabla(a, nombre).drop(columns=columna), _tabla(b, nombre).drop(columns=columna), obj=nombre)
    finally:
        a.close(); b.close()


def _comparar_bases(carpeta_a, carpeta_b):
    """Compara la base operacional (retail.db) y la analitica (curso.db) de dos corridas."""
    _comparar(carpeta_a[0], carpeta_b[0], TABLAS_OPERACIONALES, {'origen_simulacion': 'creada_en'})
    _comparar(carpeta_a[1], carpeta_b[1], TABLAS, {'master_calidad': 'evaluado_en', 'raw_carga': 'extraido_en'})


@pytest.fixture(scope='module')
def corrida_cuadernos(tmp_path_factory):
    """Ejecuta los cinco cuadernos en orden con papermill, sobre carpetas temporales."""
    base = tmp_path_factory.mktemp('cuadernos')
    os.environ['CURSO_SIN_PANTALLA'] = '1'
    raiz = config.RAIZ
    for nombre in CUADERNOS:
        parametros = {'FUENTE': 'muestra', 'RUTA_OPERACIONAL': str(base / 'retail.db'), 'RUTA_DB': str(base / 'curso.db'),
                      'RUTA_MODELOS': str(base / 'models'), 'RUTA_REPORTES': str(base / 'reports')}
        declarados = {'00_pipeline_operacional': {'FUENTE', 'RUTA_OPERACIONAL'}, '01_pipeline_raw_a_master': {'RUTA_OPERACIONAL', 'RUTA_DB'},
                      '02_pipeline_master_a_fs': {'RUTA_DB', 'RUTA_REPORTES'},
                      '03_pipeline_fs_a_ml': {'RUTA_DB', 'RUTA_REPORTES'}, '04_entrenamiento_y_seguimiento': {'RUTA_DB', 'RUTA_MODELOS', 'RUTA_REPORTES'}}[nombre]
        papermill.execute_notebook(str(raiz / 'notebooks' / f'{nombre}.ipynb'), str(base / f'{nombre}.ipynb'),
                                   parameters={k: v for k, v in parametros.items() if k in declarados},
                                   cwd=str(raiz / 'notebooks'), progress_bar=False, kernel_name='python3')
    return base


def test_los_cuadernos_producen_las_mismas_tablas_que_el_paquete(corrida_cuadernos, ruta_operacional, ruta_db):
    _comparar_bases((ruta_operacional, ruta_db), (corrida_cuadernos / 'retail.db', corrida_cuadernos / 'curso.db'))


def test_los_cuadernos_producen_las_mismas_metricas_que_el_paquete(corrida_cuadernos, ruta_db, salidas_tmp):
    con = db.conectar(ruta_db)
    r = train.entrenar(con, usar_mlflow=False, verbose=False)
    con.close()
    nb = json.loads((corrida_cuadernos / 'reports' / 'metricas.json').read_text(encoding='utf-8'))
    assert nb['mejor'] == r['mejor']
    for modelo, por_particion in r['metricas'].items():
        for particion, metricas in por_particion.items():
            for k, v in metricas.items():
                assert nb['modelos'][modelo][particion][k] == pytest.approx(v, abs=1e-9), (modelo, particion, k)
    meta_nb = json.loads((corrida_cuadernos / 'models' / 'metadatos.json').read_text(encoding='utf-8'))
    assert meta_nb['huella_datos'] == r['metadatos']['huella_datos'] and meta_nb['variables'] == config.FEATURES


def test_los_cuadernos_dejan_los_artefactos_y_las_figuras(corrida_cuadernos):
    for ruta in ['models/modelo.joblib', 'models/metadatos.json', 'models/mlflow.db', 'reports/metricas.json',
                 'reports/figures/fs_distribuciones.png', 'reports/figures/ml_ventanas.png', 'reports/figures/importancia_variables.png']:
        assert (corrida_cuadernos / ruta).exists(), ruta


def test_los_cuadernos_traducidos_a_py_con_jupytext_tambien_producen_lo_mismo(corrida_cuadernos, tmp_path):
    """Traduccion LITERAL (jupytext). Los scripts leen sus rutas de las variables de entorno CURSO_*."""
    pytest.importorskip('jupytext')
    scripts = tmp_path / 'scripts'
    scripts.mkdir()
    for nombre in CUADERNOS:
        subprocess.run([sys.executable, '-m', 'jupytext', '--to', 'py:percent', str(config.RAIZ / 'notebooks' / f'{nombre}.ipynb'),
                        '-o', str(scripts / f'{nombre}.py')], check=True, capture_output=True)
    entorno = {**os.environ, 'CURSO_DB_OPERACIONAL': str(tmp_path / 'retail.db'), 'CURSO_DB': str(tmp_path / 'curso.db'),
               'CURSO_MODELOS': str(tmp_path / 'models'),
               'CURSO_REPORTES': str(tmp_path / 'reports'), 'CURSO_SIN_PANTALLA': '1', 'MPLBACKEND': 'Agg', 'PYTHONWARNINGS': 'ignore'}
    for nombre in CUADERNOS:
        r = subprocess.run([sys.executable, str(scripts / f'{nombre}.py')], cwd=str(config.RAIZ / 'notebooks'), env=entorno,
                           capture_output=True, text=True)
        assert r.returncode == 0, f'{nombre}.py fallo:\n{r.stderr[-1500:]}'
    _comparar_bases((corrida_cuadernos / 'retail.db', corrida_cuadernos / 'curso.db'), (tmp_path / 'retail.db', tmp_path / 'curso.db'))
    a = json.loads((corrida_cuadernos / 'reports' / 'metricas.json').read_text(encoding='utf-8'))
    b = json.loads((tmp_path / 'reports' / 'metricas.json').read_text(encoding='utf-8'))
    assert a['mejor'] == b['mejor']
