"""Pruebas de verificar_s1.py. Un verificador que se equivoca da una falsa seguridad (o una falsa alarma), asi que se prueba con casos buenos y malos.

Ejecutar (con el entorno activo):   python -m pytest 03-Entorno/conda/pruebas -q
"""
import hashlib
import importlib.util
import re
import socket
import sys
from pathlib import Path

import pytest

CONDA = Path(__file__).resolve().parents[1]
RAIZ = CONDA.parents[1]
spec = importlib.util.spec_from_file_location('verificar_s1', CONDA / 'verificar_s1.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


def estados(resultados):
    return [r[0] for r in resultados]


# ------------------------------------------------------------------ lectura de environment.yml y comparacion de versiones
def test_lee_las_versiones_fijadas_ignorando_comentarios_y_python():
    texto = "name: x\ndependencies:\n  - python=3.11\n  # un comentario\n  - pandas=2.3.3   # con comentario\n  - scikit-learn=1.9.1\n  - pip\n  - pyyaml==6.0.3\n"
    assert v.leer_versiones_fijadas(texto) == {'pandas': '2.3.3', 'scikit-learn': '1.9.1', 'pyyaml': '6.0.3'}


def test_el_environment_yml_real_se_lee_entero():
    fijadas = v.leer_versiones_fijadas((CONDA / 'environment.yml').read_text(encoding='utf-8'))
    assert len(fijadas) >= 20 and fijadas['mlflow'] == '3.18.0' and 'python' not in fijadas


def test_distingue_paquete_que_falta_de_version_distinta_y_de_correcto():
    instaladas = {'pandas': '2.3.3', 'numpy': '2.5.0', 'PyYAML': '6.0.3'}
    faltan, distintas = v.comparar_versiones({'pandas': '2.3.3', 'numpy': '2.4.6', 'mlflow': '3.18.0', 'pyyaml': '6.0.3'}, instaladas.get)
    assert faltan == ['mlflow'] and distintas == [('numpy', '2.5.0', '2.4.6')]


def test_environment_yml_y_requirements_fijan_las_mismas_versiones():
    """Los tres archivos (environment.yml, requirements.txt, requirements-dev.txt) se mantienen a la vez: si uno cambia y otro no, esta prueba falla."""
    def norm(n):
        return n.lower().replace('_', '-')
    yml = {norm(k): x for k, x in v.leer_versiones_fijadas((CONDA / 'environment.yml').read_text(encoding='utf-8')).items()}
    pins = {}
    for nombre in ('requirements.txt', 'requirements-dev.txt'):
        for linea in (CONDA / nombre).read_text(encoding='utf-8').splitlines():
            m = re.match(r'^([A-Za-z0-9_.\-]+)==(\S+)$', linea.split('#')[0].strip())
            if m:
                pins[norm(m.group(1))] = m.group(2)
    assert pins == yml, {k: (pins.get(k), yml.get(k)) for k in set(pins) | set(yml) if pins.get(k) != yml.get(k)}


# ------------------------------------------------------------------ dato del caso
def test_lee_sha256sums_con_rutas_de_windows_y_marca_de_binario():
    h = 'a' * 64
    assert v.leer_sumas(f'{h}  bank-marketing\\x.csv\n{h} *y.csv\nbasura\n') == {'bank-marketing/x.csv': h, 'y.csv': h}


def test_huella_coincide_con_hashlib(tmp_path):
    f = tmp_path / 'a.bin'
    f.write_bytes(b'hola' * 1000)
    assert v.huella(f) == hashlib.sha256(b'hola' * 1000).hexdigest()


def montar_repo(tmp_path, contenido=b'a;b\n1;2\n3;4\n', huella_en_sumas=None):
    base = tmp_path / 'repo'
    datos = base / '02-Proyecto-Transversal' / 'datos'
    (datos / 'bank-marketing').mkdir(parents=True)
    (datos / 'bank-marketing' / 'bank-additional-full.csv').write_bytes(contenido)
    h = huella_en_sumas or hashlib.sha256(contenido).hexdigest()
    (datos / 'SHA256SUMS').write_text(f'{h}  bank-marketing/bank-additional-full.csv\n')
    return base


def test_dato_correcto(tmp_path, monkeypatch):
    monkeypatch.setattr(v, 'RAIZ', montar_repo(tmp_path))
    r = v.c_dato(None)
    assert estados(r) == [v.OK] and '2 filas de datos' in r[0][2]


def test_dato_modificado_falla_y_dice_como_restaurarlo(tmp_path, monkeypatch):
    base = montar_repo(tmp_path)
    (base / '02-Proyecto-Transversal' / 'datos' / 'bank-marketing' / 'bank-additional-full.csv').write_bytes(b'a;b\n1;2\n3;5\n')   # un byte distinto
    monkeypatch.setattr(v, 'RAIZ', base)
    r = v.c_dato(None)
    assert estados(r) == [v.FALLA] and 'huella no coincide' in r[0][2] and 'git restore' in r[0][3]


def test_dato_con_saltos_de_linea_de_windows_falla(tmp_path, monkeypatch):
    """El caso real: guardar el CSV con un editor que convierte \\n en \\r\\n cambia la huella."""
    base = montar_repo(tmp_path)
    ruta = base / '02-Proyecto-Transversal' / 'datos' / 'bank-marketing' / 'bank-additional-full.csv'
    ruta.write_bytes(ruta.read_bytes().replace(b'\n', b'\r\n'))
    monkeypatch.setattr(v, 'RAIZ', base)
    assert estados(v.c_dato(None)) == [v.FALLA]


def test_dato_ausente_falla(tmp_path, monkeypatch):
    monkeypatch.setattr(v, 'RAIZ', tmp_path)
    assert estados(v.c_dato(None)) == [v.FALLA]


# ------------------------------------------------------------------ repositorio, disco, puerto, sqlite, resultado
def test_repositorio_incompleto_falla_y_dice_que_clonar_la_rama_con_el_material(tmp_path, monkeypatch):
    monkeypatch.setattr(v, 'RAIZ', tmp_path)
    r = v.c_repositorio(None)
    assert r[0][0] == v.FALLA and '--branch develop' in r[0][3]


def test_ruta_con_espacios_o_onedrive_avisa(tmp_path, monkeypatch):
    base = tmp_path / 'One Drive' / 'curso'
    for marca in ('03-Entorno/conda/environment.yml', '04-Proyecto-Base/pyproject.toml', '02-Proyecto-Transversal/datos/bank-marketing/bank-additional-full.csv'):
        (base / marca).parent.mkdir(parents=True, exist_ok=True)
        (base / marca).write_text('x')
    monkeypatch.setattr(v, 'RAIZ', base)
    assert estados(v.c_repositorio(None)) == [v.OK, v.AVISO]


@pytest.mark.parametrize('libre_gb, esperado', [(50, v.OK), (2, v.AVISO), (0.5, v.FALLA)])
def test_disco(monkeypatch, libre_gb, esperado):
    monkeypatch.setattr(v.shutil, 'disk_usage', lambda _: type('U', (), {'free': libre_gb * 1e9})())
    assert estados(v.c_disco(None)) == [esperado]


def test_puerto_ocupado_avisa_y_propone_otro():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ocupado:
        try:
            ocupado.bind(('127.0.0.1', 5000))
            ocupado.listen()
        except OSError:
            pytest.skip('el puerto 5000 ya lo usa otro programa en este equipo')
        r = v.c_puerto(None)
    assert estados(r) == [v.AVISO] and '--port 5001' in r[0][3]


def test_un_puerto_recien_cerrado_no_cuenta_como_ocupado():
    """Regresion: con bind() el puerto salia «ocupado» justo despues de cerrar `mlflow ui` (TIME_WAIT) aunque nadie escuchara."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('127.0.0.1', 0))
    srv.listen()
    puerto = srv.getsockname()[1]
    cliente = socket.create_connection(('127.0.0.1', puerto))
    aceptado, _ = srv.accept()
    assert v.puerto_en_uso(puerto) is True               # mientras escucha, ocupado
    aceptado.close()
    cliente.close()
    srv.close()                                           # cierre activo del servidor: deja TIME_WAIT
    assert v.puerto_en_uso(puerto) is False


def _pytest_falso(monkeypatch, codigo, salida):
    monkeypatch.setattr(v.subprocess, 'run', lambda *a, **k: type('P', (), {'returncode': codigo, 'stdout': salida, 'stderr': ''})())


def test_pruebas_del_proyecto_muestran_la_linea_resumen_de_pytest(monkeypatch):
    _pytest_falso(monkeypatch, 0, '..............................  [100%]\n30 passed, 4 deselected in 8.38s\nlinea que un complemento imprime despues del resumen\n')
    r = v.c_pruebas(None)
    assert estados(r) == [v.OK] and r[0][2].startswith('30 passed, 4 deselected in 8.38s')


def test_pruebas_del_proyecto_que_fallan_dan_falla_con_el_resumen(monkeypatch):
    _pytest_falso(monkeypatch, 1, 'F.\nFAILED tests/test_x.py::test_a - assert 1 == 2\n=== 1 failed, 29 passed, 4 deselected in 5.01s ===\n')
    r = v.c_pruebas(None)
    assert estados(r) == [v.FALLA] and r[0][2] == '1 failed, 29 passed, 4 deselected in 5.01s'


def _con_versiones(monkeypatch, instaladas):
    monkeypatch.setattr(v, 'version_instalada', lambda n: instaladas.get(n))
    monkeypatch.setattr(v, 'leer_versiones_fijadas', lambda _t: {'pandas': '2.3.3', 'requests': '2.34.2'})


def test_un_paquete_cambiado_con_pip_propone_reinstalarlo_con_conda_y_no_env_update(monkeypatch):
    """Comprobado en un entorno real: `conda env update --prune` NO devuelve a su version un paquete que cambio pip; `conda install --force-reinstall` si."""
    _con_versiones(monkeypatch, {'pandas': '2.3.3', 'requests': '2.31.0'})
    r = v.c_paquetes(None)
    assert estados(r) == [v.AVISO]
    assert 'conda install --force-reinstall requests=2.34.2' in r[0][3]
    assert 'env update' not in r[0][3]


def test_un_paquete_que_falta_es_falla_y_propone_actualizar_antes_de_rehacer(monkeypatch):
    _con_versiones(monkeypatch, {'pandas': '2.3.3'})
    r = v.c_paquetes(None)
    assert estados(r) == [v.FALLA] and 'faltan 1 de 2: requests' in r[0][2]
    assert r[0][3].index('env update') < r[0][3].index('env remove')


def test_sqlite_con_funciones_de_ventana():
    assert estados(v.c_sqlite(None)) == [v.OK]


def test_un_aviso_no_bloquea_pero_una_falla_si():
    assert v.veredicto([(v.OK, 'a', '', ''), (v.AVISO, 'b', '', '')])[0] is True
    listo, texto = v.veredicto([(v.OK, 'a', '', ''), (v.FALLA, 'b', '', '')])
    assert listo is False and 'NO LISTO PARA S1' in texto and '1 FALLA' in texto


def test_el_informe_no_lleva_el_usuario_ni_el_correo(tmp_path):
    casa = tmp_path / 'Usuarios' / 'maria'
    texto = v.enmascarar(f'ruta {casa}/proyecto y {str(casa).replace("/", chr(92))}\\otra', casa)
    assert 'maria' not in texto and '~' in texto


def test_una_comprobacion_que_revienta_no_esconde_las_demas(monkeypatch):
    def rota(_):
        raise RuntimeError('boom')
    monkeypatch.setattr(v, 'COMPROBACIONES', [v.c_sqlite, rota])
    args = type('A', (), {'con_pruebas': False, 'sin_conda': False})()
    r = v.ejecutar(args)
    assert estados(r) == [v.OK, v.FALLA] and 'boom' in r[1][2]


def test_si_falla_el_entorno_el_informe_dice_por_donde_empezar():
    texto = v.formatear([(v.FALLA, 'entorno', 'estas en base', 'conda activate env-ia-mlops'), (v.FALLA, 'paquetes', 'faltan', 'rehaz')], None)
    assert 'Pista: empieza por arreglar' in texto and 'NO LISTO PARA S1' in texto
    assert 'Pista' not in v.formatear([(v.FALLA, 'dato Bank Marketing', 'x', 'y')], None)


def test_desde_el_entorno_actual_el_programa_termina_con_veredicto_y_guarda_un_informe_sin_usuario(tmp_path, monkeypatch, capsys):
    """Ejecuta main() completo. Fuera de env-ia-mlops puede haber FALLA (es lo esperado); lo que no puede haber es una excepcion sin controlar."""
    monkeypatch.chdir(tmp_path)
    codigo = v.main(['--informe', '--sin-conda'])
    salida = capsys.readouterr().out
    informe = (tmp_path / 'verificacion-s1.txt').read_text(encoding='utf-8')
    assert codigo in (0, 1) and 'Resultado:' in salida and 'Resultado:' in informe
    assert str(Path.home()) not in informe
