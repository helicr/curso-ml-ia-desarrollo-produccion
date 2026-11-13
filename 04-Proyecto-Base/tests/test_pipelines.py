"""Los pipelines son INDEPENDIENTES (cada uno comprueba su entrada) e IDEMPOTENTES (repetirlos no cambia nada)."""
import shutil
import sqlite3
from contextlib import closing

import pytest

from ia_mlops import config, control, db, pipeline_ingesta_master, pipeline_ingesta_raw, pipeline_ml, pipeline_train

TABLAS = ['raw_lineas_factura', 'raw_carga', 'master_lineas', 'master_descartes', 'master_calidad', 'fs_cliente_corte', 'ml_dataset']


def _estado(ruta, tablas=TABLAS):
    """Huella del contenido de varias tablas: si no cambia, el estado de la base es el mismo."""
    with closing(db.conectar(ruta)) as con:
        return control.huella_tablas(con, *tablas)


def _ejecuciones_mlflow():
    with closing(sqlite3.connect(config.MODELOS / 'mlflow.db')) as c:
        return c.execute('SELECT COUNT(*) FROM runs').fetchone()[0]


@pytest.fixture()
def copia(rutas, tmp_path):
    """Copia de las dos bases de la sesion, para poder modificarlas sin afectar a otras pruebas."""
    operacional, analitica = rutas
    shutil.copy(operacional, tmp_path / 'retail.db')
    shutil.copy(analitica, tmp_path / 'curso.db')
    return tmp_path / 'retail.db', tmp_path / 'curso.db'


def test_cada_pipeline_sin_su_entrada_dice_que_ejecutar_antes(tmp_path):
    vacia = tmp_path / 'vacia.db'
    with pytest.raises(control.EntradaFaltanteError, match='ia_mlops.operacional'):
        pipeline_ingesta_raw.ejecutar(vacia, tmp_path / 'no_existe.db', verbose=False)
    for modulo, previo in [(pipeline_ingesta_master, 'pipeline_ingesta_raw'), (pipeline_ml, 'pipeline_ingesta_master'), (pipeline_train, 'pipeline_ml')]:
        with pytest.raises(control.EntradaFaltanteError, match=previo):
            modulo.ejecutar(vacia, verbose=False)


def test_ejecutar_otra_vez_sin_cambios_no_toca_nada(copia):
    operacional, analitica = copia
    antes = _estado(analitica, TABLAS + ['control_pipelines'])
    r = [pipeline_ingesta_raw.ejecutar(analitica, operacional, verbose=False),
         pipeline_ingesta_master.ejecutar(analitica, verbose=False),
         pipeline_ml.ejecutar(analitica, verbose=False)]
    assert [x['estado'] for x in r] == ['sin cambios'] * 3
    assert _estado(analitica, TABLAS + ['control_pipelines']) == antes     # ni siquiera cambian las marcas de tiempo


def test_forzar_reconstruye_y_el_contenido_es_el_mismo(copia):
    operacional, analitica = copia
    datos = ['raw_lineas_factura', 'master_lineas', 'master_descartes', 'fs_cliente_corte', 'ml_dataset']
    antes = _estado(analitica, datos)
    r = [pipeline_ingesta_raw.ejecutar(analitica, operacional, forzar=True, verbose=False),
         pipeline_ingesta_master.ejecutar(analitica, forzar=True, verbose=False),
         pipeline_ml.ejecutar(analitica, forzar=True, verbose=False)]
    assert [x['estado'] for x in r] == ['ejecutado'] * 3
    assert _estado(analitica, datos) == antes


def test_un_cambio_en_el_origen_se_detecta_y_se_reingiere(copia):
    operacional, analitica = copia
    with closing(db.conectar(operacional)) as c:      # el «negocio» borra una linea (de una factura con varias)
        c.execute('DELETE FROM lineas_factura WHERE linea_id = (SELECT MAX(linea_id) FROM lineas_factura WHERE factura_id IN '
                  '(SELECT factura_id FROM lineas_factura GROUP BY factura_id HAVING COUNT(*) > 1))')
        c.commit()
    antes = _estado(analitica, ['raw_lineas_factura'])
    assert pipeline_ingesta_raw.ejecutar(analitica, operacional, verbose=False)['estado'] == 'ejecutado'
    assert _estado(analitica, ['raw_lineas_factura']) != antes
    assert pipeline_ingesta_master.ejecutar(analitica, verbose=False)['estado'] == 'ejecutado'


def test_un_pipeline_se_puede_ejecutar_solo(copia):
    """pipeline_ml no necesita que se ejecuten los anteriores en la misma sesion: le basta con que MASTER exista."""
    _, analitica = copia
    assert pipeline_ml.ejecutar(analitica, forzar=True, verbose=False)['estado'] == 'ejecutado'


def test_el_orquestador_crea_el_operacional_si_falta_y_los_pipelines_sueltos_no(tmp_path):
    """En un clon recien hecho (CI, Codespace) `python -m ia_mlops.pipeline` funciona de una vez; el pipeline suelto, no."""
    from ia_mlops import pipeline
    with pytest.raises(control.EntradaFaltanteError):
        pipeline_ingesta_raw.ejecutar(tmp_path / 'curso.db', tmp_path / 'retail.db', verbose=False)
    assert not (tmp_path / 'retail.db').exists()
    r = pipeline.ejecutar(['pipeline_ingesta_raw'], ruta_db=tmp_path / 'curso.db', ruta_operacional=tmp_path / 'retail.db', verbose=False)
    assert (tmp_path / 'retail.db').exists() and r[0]['estado'] == 'ejecutado'


def test_entrenar_otra_vez_sin_cambios_no_duplica_ejecuciones_en_mlflow(copia, salidas_tmp):
    _, analitica = copia
    assert pipeline_train.ejecutar(analitica, verbose=False)['estado'] == 'ejecutado'
    n = _ejecuciones_mlflow()
    assert n == 4                                                    # tres modelos + MEJOR-<elegido>
    assert pipeline_train.ejecutar(analitica, verbose=False)['estado'] == 'sin cambios'
    assert _ejecuciones_mlflow() == n
    assert pipeline_train.ejecutar(analitica, forzar=True, verbose=False)['estado'] == 'ejecutado'
    assert _ejecuciones_mlflow() == n + 4
