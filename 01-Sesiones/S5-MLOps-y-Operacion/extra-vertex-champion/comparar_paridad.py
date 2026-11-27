"""Paridad: lo que contesta Vertex frente a lo que da el MISMO modelo cargado a mano en local.

Carga el modelo MLflow de `--modelo-dir` con mlflow.sklearn (como `alias_modelo.cargar_y_puntuar`, sin pasar por el adaptador),
puntúa las mismas instancias y compara con la respuesta del endpoint: probabilidad (tolerancia 1e-9), clase y tramo.

Uso (desde esta carpeta):
    python comparar_paridad.py --respuesta respuesta.json --instancias instancias.json --modelo-dir build/vertex/modelo [--esperar-version 6]
    --respuesta   lo que imprime `gcloud ai endpoints predict --format json` (una lista) o {"predictions": [...]}
    --instancias  {"instances": [[13 números], ...]}   (lo que se envió)
    --esperar-version  si se indica, comprueba que contestó esa versión de MLflow (campo version_mlflow); si contestó otra, sale con 3
                       (con tráfico dividido una petición puede caer en la versión anterior: se vuelve a intentar)
Código de salida: 0 igual · 1 hay diferencias · 2 error de uso · 3 contestó otra versión.
"""
import argparse
import json
import math
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import manifiesto_champion as mc  # noqa: E402  (fija el sys.path del proyecto)

TOLERANCIA = 1e-9


def _predicciones(texto):
    datos = json.loads(texto)
    return datos['predictions'] if isinstance(datos, dict) else datos


def puntuar_local(modelo_dir, instancias):
    """[(probabilidad, clase, tramo)] del modelo cargado a mano."""
    import mlflow.sklearn
    import pandas as pd
    from ia_mlops import config
    modelo = mlflow.sklearn.load_model(str(Path(modelo_dir) / config.CARPETA_MODELO_MLFLOW))
    df = pd.DataFrame([{c: (float('nan') if v is None else float(v)) for c, v in zip(config.FEATURES, fila)} for fila in instancias])
    out = []
    for p in modelo.predict_proba(df)[:, 1]:
        p = float(p)
        tramo = next(s['segmento'] for s in config.SEGMENTOS_RECOMPRA if p >= s['desde'])
        out.append((p, int(p >= 0.5), tramo))
    return out


def comparar(respuesta, instancias, modelo_dir, esperar_version=None, tolerancia=TOLERANCIA):
    """Devuelve (codigo, lineas de texto)."""
    local = puntuar_local(modelo_dir, instancias)
    if len(respuesta) != len(local):
        return 1, [f'La respuesta trae {len(respuesta)} predicciones y se enviaron {len(local)} instancias.']
    lineas = ['instancia   probabilidad (Vertex)   probabilidad (local)   diferencia   clase   tramo   versión MLflow']
    ok = True
    versiones = set()
    for i, (r, (p, c, t)) in enumerate(zip(respuesta, local)):
        pv = r['probabilidad']
        dif = abs(pv - p)
        igual = dif <= tolerancia and r['clase'] == c and r['tramo'] == t and not math.isnan(pv)
        ok = ok and igual
        versiones.add(r.get('version_mlflow'))
        lineas.append(f'{i:<10}  {pv:<21.10f}   {p:<19.10f}   {dif:<10.2e}   {r["clase"]}/{c}   {r["tramo"]}/{t}   {r.get("version_mlflow")}  {"IGUAL" if igual else "DIFERENTE"}')
    if esperar_version is not None and versiones != {int(esperar_version)}:
        return 3, lineas + [f'Contestó la versión {sorted(v for v in versiones if v is not None)} y se esperaba la {esperar_version}: reintenta (tráfico dividido).']
    lineas.append('PARIDAD: las predicciones del endpoint y las del modelo local coinciden.' if ok else 'PARIDAD ROTA: hay diferencias.')
    return (0 if ok else 1), lineas


def main(argv=None):
    ap = argparse.ArgumentParser(description='Compara la respuesta del endpoint con el modelo local')
    ap.add_argument('--respuesta', required=True)
    ap.add_argument('--instancias', required=True)
    ap.add_argument('--modelo-dir', required=True)
    ap.add_argument('--esperar-version', type=int)
    ap.add_argument('--tolerancia', type=float, default=TOLERANCIA)
    a = ap.parse_args(argv)
    try:
        respuesta = _predicciones(Path(a.respuesta).read_text(encoding='utf-8'))
        instancias = json.loads(Path(a.instancias).read_text(encoding='utf-8'))['instances']
        codigo, lineas = comparar(respuesta, instancias, a.modelo_dir, a.esperar_version, a.tolerancia)
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f'Error: {e}', file=sys.stderr)
        return 2
    print('\n'.join(lineas))
    return codigo


if __name__ == '__main__':
    sys.exit(main())
