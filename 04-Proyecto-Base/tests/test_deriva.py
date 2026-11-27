"""Pruebas de la deriva de datos y de rendimiento (ia_mlops/deriva.py). Sin red; la base y el modelo son los temporales de conftest.py."""
import hashlib
import json
import math

import numpy as np
import pytest

from ia_mlops import config, db, deriva, explotacion
from ia_mlops.deriva import ErrorDeriva


# ------------------------------------------------------------------------------------------------ PSI
def test_psi_es_cero_con_la_misma_muestra():
    x = np.random.default_rng(0).normal(size=500)
    assert deriva.psi(x, x) == pytest.approx(0.0, abs=1e-12)


def test_psi_es_alto_con_una_muestra_desplazada():
    x = np.random.default_rng(0).normal(size=500)
    valor = deriva.psi(x, x + 3.0)                                         # la campana se mueve 3 desviaciones
    assert valor > deriva.UMBRAL_PSI
    assert deriva.estado_psi(valor) == 'deriva'


def test_psi_pequeno_con_otra_muestra_de_la_misma_poblacion():
    azar = np.random.default_rng(1)
    assert deriva.psi(azar.normal(size=2000), azar.normal(size=2000)) < deriva.UMBRAL_AVISO_PSI


def test_psi_coincide_con_la_formula_hecha_a_mano():
    # 2 intervalos: la mediana de la referencia (2,5) los separa. p = [0,5; 0,5]; q = [0,75; 0,25]
    # PSI = (0,75 - 0,5) * ln(0,75 / 0,5) + (0,25 - 0,5) * ln(0,25 / 0,5)
    esperado = 0.25 * math.log(1.5) + (-0.25) * math.log(0.5)
    assert deriva.psi([1, 2, 3, 4], [1, 1, 1, 4], intervalos=2) == pytest.approx(esperado)
    detalle = deriva.psi_detalle([1, 2, 3, 4], [1, 1, 1, 4], intervalos=2)
    assert [round(i['referencia'], 2) for i in detalle['intervalos'][:2]] == [0.5, 0.5]
    assert [round(i['actual'], 2) for i in detalle['intervalos'][:2]] == [0.75, 0.25]


def test_variable_constante_igual_en_las_dos_muestras_no_deriva():
    assert deriva.psi([5] * 50, [5] * 80) == pytest.approx(0.0, abs=1e-12)


def test_variable_constante_que_cambia_deriva_y_no_da_infinito():
    valor = deriva.psi([5] * 50, [9] * 50)                                  # un intervalo queda vacío en cada lado: sin el suelo sería ln(0)
    assert math.isfinite(valor) and valor > deriva.UMBRAL_PSI


def test_el_suelo_anti_cero_evita_el_infinito_con_intervalos_vacios():
    ref = np.arange(100.0)
    valor = deriva.psi(ref, np.full(100, 1000.0))                           # toda la muestra actual fuera del rango de la referencia
    assert math.isfinite(valor) and valor > deriva.UMBRAL_PSI
    intervalos = deriva.psi_detalle(ref, np.full(100, 1000.0))['intervalos']
    assert intervalos[-2]['actual'] == pytest.approx(1.0)                   # todo cae en el último intervalo...
    assert intervalos[0]['actual'] == deriva.SUELO_PSI                      # ...y el primero, vacío, se queda en el suelo en vez de en 0


def test_los_nulos_forman_su_propio_intervalo():
    base = np.random.default_rng(2).normal(size=400)
    con_nulos = base.copy()
    con_nulos[:200] = np.nan                                                # de repente falta la mitad de los datos
    assert deriva.psi(base, con_nulos) > deriva.UMBRAL_PSI
    assert deriva.psi(con_nulos, con_nulos) == pytest.approx(0.0, abs=1e-12)    # los mismos nulos en los dos lados no son deriva
    detalle = deriva.psi_detalle(base, con_nulos)['intervalos'][-1]
    assert detalle['intervalo'] == 'nulo' and detalle['actual'] == pytest.approx(0.5)


def test_psi_sin_filas_es_un_error_claro():
    with pytest.raises(ErrorDeriva, match='No hay filas'):
        deriva.psi([], [1, 2, 3])


def test_umbrales_de_estado():
    assert deriva.estado_psi(0.05) == 'estable' and deriva.estado_psi(0.10) == 'estable'
    assert deriva.estado_psi(0.11) == 'moderada' and deriva.estado_psi(0.25) == 'moderada'
    assert deriva.estado_psi(0.2501) == 'deriva'
    assert deriva.estado_psi(0.30, umbral=0.5) == 'moderada'                # el umbral de alarma se puede cambiar


def test_ks_mide_la_distancia_entre_distribuciones():
    x = np.random.default_rng(3).normal(size=300)
    assert deriva.ks(x, x) == pytest.approx(0.0)
    assert deriva.ks(x, x + 100) == pytest.approx(1.0)
    assert deriva.ks([np.nan], x) is None


# ------------------------------------------------------------------------------------------------ datos entre cortes
def test_las_variables_de_un_corte_vienen_de_la_tabla_o_se_calculan_al_vuelo(con):
    _, origen = deriva.variables_del_corte(con, '2010-12-01')
    assert origen == 'fs_cliente_corte'
    _, origen = deriva.variables_del_corte(con, '2010-12-02')
    assert origen == 'calculado al vuelo'
    with pytest.raises(ErrorDeriva, match='AAAA-MM-DD'):
        deriva.variables_del_corte(con, '01/12/2010')
    with pytest.raises(ErrorDeriva, match='no es una fecha válida'):
        deriva.variables_del_corte(con, '2010-13-45')
    with pytest.raises(ErrorDeriva, match='Ningún cliente'):
        deriva.variables_del_corte(con, '2000-01-01')


def test_un_corte_frente_a_si_mismo_no_deriva(con):
    r = deriva.deriva_de_datos(con, '2010-12-01', '2010-12-01')
    assert [v['variable'] for v in r['variables']] and len(r['variables']) == len(config.FEATURES) == 13
    assert all(v['psi'] == pytest.approx(0.0, abs=1e-12) for v in r['variables'])
    assert r['hay_deriva'] is False and r['superan_umbral'] == []


def test_el_calculo_al_vuelo_da_lo_mismo_que_la_tabla_guardada(con):
    # el corte guardado se compara con su propio cálculo al vuelo: la paridad hace que el PSI sea 0 en todas las variables
    guardado, _ = deriva.variables_del_corte(con, '2010-12-01')
    al_vuelo = explotacion.variables_en_corte(con, '2010-12-01')
    for v in config.FEATURES:
        assert deriva.psi(guardado[v], al_vuelo[v]) == pytest.approx(0.0, abs=1e-12), v


def test_dos_cortes_lejanos_derivan_y_la_tabla_sale_ordenada(con):
    r = deriva.deriva_de_datos(con, '2010-06-01', '2011-09-01')
    psis = [v['psi'] for v in r['variables']]
    assert psis == sorted(psis, reverse=True)
    assert r['hay_deriva'] and r['superan_umbral'] and set(r['superan_umbral']) <= set(config.FEATURES)
    assert all(v['psi'] > r['umbral_psi'] for v in r['variables'] if v['variable'] in r['superan_umbral'])
    assert all(v['ks'] is not None for v in r['variables'])
    # un umbral enorme: las mismas cifras ya no alarman
    assert deriva.deriva_de_datos(con, '2010-06-01', '2011-09-01', umbral=1e6)['hay_deriva'] is False


def test_el_texto_de_datos_dice_que_los_umbrales_son_una_convencion(con):
    texto = deriva.texto_datos(deriva.deriva_de_datos(con, '2010-06-01', '2011-09-01'))
    assert 'convención de la industria, no una ley' in texto and 'PSI' in texto and 'KS' in texto


def test_orden_cortes_lista_los_guardados_y_el_ahora(con):
    r = deriva.listar_cortes(con)
    guardados = [c['corte'] for c in r['guardados']]
    assert guardados == sorted(c for lista in config.CORTES.values() for c in lista)
    assert r['ahora'] == explotacion.corte_por_defecto(con)
    por_corte = {c['corte']: c for c in r['guardados']}
    assert por_corte['2011-09-01']['particion'] == 'test' and por_corte['2010-06-01']['particion'] == 'train'
    assert all(c['etiqueta'] for c in r['guardados'])                       # todos los cortes de entrenamiento tienen su ventana de 90 días completa


# ------------------------------------------------------------------------------------------------ AUC por corte
class ModeloFalso:
    """Puntúa 1 a quien tiene compras en los últimos 90 días y 0 al resto: con la etiqueta adecuada, el AUC es exacto."""

    def predict_proba(self, X):
        p = (X['frecuencia_90d'].to_numpy() > 0).astype(float)
        return np.column_stack([1 - p, p])


def _etiquetas(monkeypatch, que):
    """Cambia las etiquetas reales por unas conocidas: `que(df)` devuelve los cliente_id que «compran» (por corte)."""
    def falsas(con, corte):
        df, _ = deriva.variables_del_corte(con, corte)
        return set(df.loc[que[corte](df), 'cliente_id'])
    monkeypatch.setattr(deriva, 'etiquetas_en_corte', falsas)


def test_auc_con_etiquetas_conocidas(con, carpeta_modelo, monkeypatch):
    compra_si_activo = lambda df: df['frecuencia_90d'] > 0          # noqa: E731 - coincide con el modelo falso: AUC 1
    compra_si_inactivo = lambda df: df['frecuencia_90d'] == 0       # noqa: E731 - lo contrario: AUC 0
    _etiquetas(monkeypatch, {'2011-03-01': compra_si_activo, '2011-06-01': compra_si_inactivo})
    r = deriva.rendimiento_por_corte(con, ['2011-03-01', '2011-06-01'], ModeloFalso(), tolerancia=0.05)
    a, b = r['cortes']
    assert a['auc'] == pytest.approx(1.0) and b['auc'] == pytest.approx(0.0)
    assert a['caida'] == pytest.approx(0.0) and b['caida'] == pytest.approx(1.0)      # la caída es frente al primer corte
    assert r['hay_alerta'] is True and r['caida_maxima'] == pytest.approx(1.0)


def test_la_tolerancia_se_compara_con_mayor_estricto(con, carpeta_modelo, monkeypatch):
    _etiquetas(monkeypatch, {'2011-03-01': lambda df: df['frecuencia_90d'] > 0, '2011-06-01': lambda df: df['frecuencia_90d'] == 0})
    cortes = ['2011-03-01', '2011-06-01']
    assert deriva.rendimiento_por_corte(con, cortes, ModeloFalso(), tolerancia=0.99)['hay_alerta'] is True      # caída 1,0 > 0,99
    assert deriva.rendimiento_por_corte(con, cortes, ModeloFalso(), tolerancia=1.0)['hay_alerta'] is False      # caída 1,0 no supera 1,0


def test_el_auc_real_por_corte_coincide_con_el_de_ml_dataset(con, carpeta_modelo):
    """Las etiquetas que se calculan aquí (sobre MASTER) deben ser las de ml_dataset: mismo modelo, mismo corte, mismo AUC."""
    import pandas as pd
    from sklearn.metrics import roc_auc_score
    modelo = deriva.cargar_modelo(carpeta_modelo)
    r = deriva.rendimiento_por_corte(con, ['2011-06-01', '2011-09-01'], modelo)
    for fila in r['cortes']:
        d = pd.read_sql('SELECT * FROM ml_dataset WHERE fecha_corte = ?', con, params=(fila['corte'],))
        esperado = roc_auc_score(d['y'], modelo.predict_proba(d[config.FEATURES].astype(float))[:, 1])
        assert fila['auc'] == pytest.approx(esperado) and fila['clientes'] == len(d) and fila['positivos'] == int(d['y'].sum())


def test_marca_que_cortes_son_de_entrenamiento_y_cuales_de_prueba(con, carpeta_modelo):
    modelo = deriva.cargar_modelo(carpeta_modelo)
    r = deriva.rendimiento_por_corte(con, ['2010-12-01', '2011-03-01', '2011-06-01'], modelo)
    assert [f['uso'] for f in r['cortes']] == ['entrenamiento', 'validación', 'prueba']
    sobreestima = [a for a in r['avisos'] if 'SOBREESTIMA' in a]
    assert len(sobreestima) == 1 and '2010-12-01' in sobreestima[0] and '2011-03-01' in sobreestima[0] and '2011-06-01' not in sobreestima[0]


def test_sin_cortes_de_entrenamiento_no_hay_aviso_de_sobreestimacion(con, carpeta_modelo):
    r = deriva.rendimiento_por_corte(con, ['2011-06-01', '2011-09-01'], deriva.cargar_modelo(carpeta_modelo))
    assert not any('SOBREESTIMA' in a for a in r['avisos'])


def test_un_corte_sin_etiqueta_se_lista_pero_no_se_mide(con, carpeta_modelo):
    ahora = explotacion.corte_por_defecto(con)                              # su ventana de 90 días no cabe en los datos
    r = deriva.rendimiento_por_corte(con, ['2011-06-01', ahora], deriva.cargar_modelo(carpeta_modelo))
    medido, sin = r['cortes']
    assert medido['auc'] is not None
    assert sin['auc'] is None and sin['caida'] is None and 'sin etiqueta' in sin['motivo']
    assert sin['uso'] == 'fuera de la partición'
    with pytest.raises(ErrorDeriva, match='Ningún corte tiene etiqueta'):
        deriva.rendimiento_por_corte(con, [ahora], deriva.cargar_modelo(carpeta_modelo))


def test_la_etiqueta_existe_solo_si_la_ventana_cabe_en_los_datos(con):
    ahora = explotacion.corte_por_defecto(con)
    assert deriva._hay_etiqueta(con, '2011-06-01', ahora) is True
    assert deriva._hay_etiqueta(con, ahora, ahora) is False
    limite = db.escalar(con, "SELECT date(?, '-90 day')", (ahora,))        # justo el último corte cuya ventana cabe
    assert deriva._hay_etiqueta(con, limite, ahora) is True
    assert deriva._hay_etiqueta(con, db.escalar(con, "SELECT date(?, '+1 day')", (limite,)), ahora) is False


def test_sin_modelo_es_un_error_claro(tmp_path):
    with pytest.raises(ErrorDeriva, match='No hay modelo'):
        deriva.cargar_modelo(tmp_path)


# ------------------------------------------------------------------------------------------------ terminal y códigos de salida
@pytest.fixture()
def en_la_base(ruta_db, monkeypatch):
    monkeypatch.setattr(config, 'DB', ruta_db)
    monkeypatch.setattr(config, 'DB_SOLO_LECTURA', False)
    return ruta_db


def test_codigo_de_salida_de_datos(en_la_base, tmp_path, capsys):
    salida = tmp_path / 'datos.json'
    assert deriva.main(['datos', '--referencia', '2010-06-01', '--actual', '2011-09-01', '--json', str(salida)]) == 1     # alguna variable supera el umbral
    assert json.loads(salida.read_text(encoding='utf-8'))['hay_deriva'] is True
    assert 'supera el umbral' in capsys.readouterr().out
    assert deriva.main(['datos', '--referencia', '2010-12-01', '--actual', '2010-12-01']) == 0                       # sin deriva
    assert deriva.main(['datos', '--referencia', '2010-06-01', '--actual', '2011-09-01', '--umbral-psi', '1000']) == 0   # el umbral manda
    assert deriva.main(['datos', '--referencia', '2010-6-1', '--actual', '2011-09-01']) == 2                         # error
    assert 'AAAA-MM-DD' in capsys.readouterr().err


def test_codigo_de_salida_de_cortes_y_de_una_base_que_falta(en_la_base, tmp_path, monkeypatch, capsys):
    assert deriva.main(['cortes']) == 0
    assert '2011-09-01' in capsys.readouterr().out
    monkeypatch.setattr(config, 'DB', tmp_path / 'no_existe.db')
    monkeypatch.setattr(config, 'DB_SOLO_LECTURA', False)
    assert deriva.main(['cortes']) == 2
    assert 'No existe la base' in capsys.readouterr().err
    assert not (tmp_path / 'no_existe.db').exists()                         # solo lectura: ni siquiera la crea


def test_codigo_de_salida_de_rendimiento(en_la_base, carpeta_modelo, monkeypatch, tmp_path, capsys):
    salida = tmp_path / 'rendimiento.json'
    assert deriva.main(['rendimiento', '--cortes', '2011-06-01', '2011-09-01', '--tolerancia', '1', '--json', str(salida)]) == 0
    assert json.loads(salida.read_text(encoding='utf-8'))['hay_alerta'] is False
    _etiquetas(monkeypatch, {'2011-03-01': lambda df: df['frecuencia_90d'] > 0, '2011-06-01': lambda df: df['frecuencia_90d'] == 0})
    monkeypatch.setattr(deriva, 'cargar_modelo', lambda carpeta=None: ModeloFalso())
    assert deriva.main(['rendimiento', '--cortes', '2011-03-01', '2011-06-01']) == 1                       # el AUC se desploma
    assert 'DERIVA DE RENDIMIENTO: sí' in capsys.readouterr().out
    assert deriva.main(['rendimiento', '--cortes', '2011-03-01', 'ayer']) == 2


def test_todo_es_solo_lectura(en_la_base, carpeta_modelo, tmp_path):
    def huella():
        return hashlib.sha256(en_la_base.read_bytes()).hexdigest()
    antes = huella()
    deriva.main(['cortes'])
    deriva.main(['datos', '--referencia', '2010-12-01', '--actual', explotacion_ahora(en_la_base)])          # el «actual» se calcula al vuelo
    deriva.main(['rendimiento', '--cortes', '2011-06-01'])
    assert huella() == antes


def explotacion_ahora(ruta):
    c = db.conectar(ruta)
    try:
        return explotacion.corte_por_defecto(c)
    finally:
        c.close()
