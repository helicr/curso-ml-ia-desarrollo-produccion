"""Explotación del modelo: puntuar a TODOS los clientes en la fecha de corte de hoy y sacar la lista de la campaña.

Es la última etapa del recorrido: ingesta → RAW → MASTER → FS → ML → modelo → servicio → **uso por el negocio**.
El negocio no pregunta por un cliente suelto: pregunta «¿a quién llamo esta semana?». Eso es una puntuación por lotes.

QUÉ HACE
  1. Elige el corte de explotación: por defecto, el día siguiente a la última factura que hay en MASTER (el «hoy» del dato).
  2. Calcula las 13 variables de ese corte con el MISMO SQL de la capa FS (sql/fs/02_poblar_fs.sql), en una tabla temporal:
     la capa FS del proyecto no se toca y la regla de oro (solo datos anteriores al corte) se cumple igual.
  3. Puntúa a todos los clientes:  --url  a través de la API (como en producción, en lotes de hasta 1000)
                                   sin --url, con el modelo de models/ (el mismo código que usa la API).
  4. Ordena de mayor a menor probabilidad, asigna deciles y marca la campaña: el --capacidad (fracción) con más probabilidad.
  5. Guarda reports/campana/campana_<corte>.csv (todos, ordenados) y .json (resumen y trazabilidad: modelo, huella, corte, origen).
  6. Avisa de lo que el modelo no vio al entrenar (valores fuera de rango): es la primera señal de que conviene reentrenar.

Uso (desde 04-Proyecto-Base, después de ejecutar el pipeline):
    python -m ia_mlops.explotacion --url http://127.0.0.1:8080     # a través de la API o del contenedor
    python -m ia_mlops.explotacion                                 # con el modelo local, sin API
    python -m ia_mlops.explotacion --capacidad 0.2 --top 15
    python -m ia_mlops.explotacion --comparar-con reports/campana/campana_2011-12-10.csv   # ¿cuántos clientes repiten?
"""
import argparse
import json
import math
import urllib.request
from datetime import datetime

import pandas as pd

from . import config, db
from .api.servicio import Servicio

LOTE_MAXIMO = 1000            # el contrato de /predecir/lote (esquemas.LoteClientes) admite hasta 1000 clientes


def corte_por_defecto(con):
    """El día siguiente a la última factura de MASTER: el «hoy» del dato."""
    corte = db.escalar(con, "SELECT date(MAX(fecha_factura), '+1 day') FROM master_facturas")
    if not corte:
        raise RuntimeError('MASTER está vacío: ejecuta antes  python -m ia_mlops.pipeline')
    return corte


def variables_en_corte(con, corte):
    """Las 13 variables de cada cliente en `corte`, calculadas con el SQL de FS sobre una tabla TEMPORAL.

    En SQLite un nombre sin esquema se busca primero en `temp`: la sentencia INSERT INTO fs_cliente_corte de
    02_poblar_fs.sql escribe así en la copia temporal y la tabla de la capa FS queda intacta.
    """
    if not db.escalar(con, "SELECT COUNT(*) FROM sqlite_master WHERE name = 'fs_cliente_corte'"):
        raise RuntimeError('No existe la capa FS: ejecuta antes  python -m ia_mlops.pipeline')
    con.execute('DROP TABLE IF EXISTS temp.fs_cliente_corte')
    con.execute('CREATE TEMP TABLE fs_cliente_corte AS SELECT * FROM main.fs_cliente_corte WHERE 0')
    try:
        db.ejecutar_sentencia(con, config.SQL / 'fs' / '02_poblar_fs.sql', {'corte': corte})
        df = pd.read_sql('SELECT * FROM temp.fs_cliente_corte ORDER BY cliente_id', con)
    finally:
        con.execute('DROP TABLE IF EXISTS temp.fs_cliente_corte')
    return df


def _filas(df):
    """DataFrame -> lista de diccionarios con tipos JSON (enteros como int, NaN como None)."""
    filas = []
    for registro in df[config.FEATURES].to_dict(orient='records'):
        fila = {}
        for k, v in registro.items():
            if v is None or (isinstance(v, float) and math.isnan(v)):
                fila[k] = None
            elif k in ('monto_total', 'ticket_medio', 'monto_90d', 'dias_medios_entre_compras'):
                fila[k] = float(v)
            else:
                fila[k] = int(v)
        filas.append(fila)
    return filas


def _pedir(url, cuerpo=None, timeout=60):
    datos = None if cuerpo is None else json.dumps(cuerpo).encode('utf-8')
    req = urllib.request.Request(url, data=datos, headers={'Content-Type': 'application/json'}, method='POST' if datos else 'GET')
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8'))


def puntuar_api(filas, url):
    """Puntúa por la API en lotes. Devuelve (probabilidades, advertencias, info del modelo)."""
    url = url.rstrip('/')
    info = _pedir(f'{url}/modelo')
    probs, avisos = [], []
    for i in range(0, len(filas), LOTE_MAXIMO):
        respuesta = _pedir(f'{url}/predecir/lote', {'clientes': filas[i:i + LOTE_MAXIMO]})
        for p in respuesta['predicciones']:
            probs.append(p['probabilidad'])
            avisos.append(p['advertencias'])
    return probs, avisos, {'modelo': info['modelo'], 'huella_datos': info['huella_datos'], 'entrenado_en': info['entrenado_en']}


def puntuar_local(filas, carpeta=None):
    """Puntúa con el modelo de models/ usando el mismo código que la API (Servicio)."""
    servicio = Servicio.cargar(carpeta)
    resultado = servicio.predecir(filas)
    meta = servicio.meta
    return ([p for p, _ in resultado], [a for _, a in resultado],
            {'modelo': meta['modelo'], 'huella_datos': meta['huella_datos'], 'entrenado_en': meta['entrenado_en']})


def campana(con=None, corte=None, url=None, capacidad=0.10, carpeta_modelo=None, guardar=True):
    """Puntúa a todos los clientes en `corte` y devuelve (tabla ordenada, resumen). Con guardar=True, escribe CSV y JSON."""
    cierre = con is None
    con = con or db.conectar()
    try:
        corte = corte or corte_por_defecto(con)
        df = variables_en_corte(con, corte)
    finally:
        if cierre:
            con.close()
    if df.empty:
        raise RuntimeError(f'Ningún cliente tiene compras antes de {corte}.')
    filas = _filas(df)
    probs, avisos, info = puntuar_api(filas, url) if url else puntuar_local(filas, carpeta_modelo)

    tabla = pd.DataFrame({'cliente_id': df['cliente_id'].astype(int), 'probabilidad': probs,
                          'n_advertencias': [len(a) for a in avisos], 'advertencias': [' | '.join(a) for a in avisos]})
    tabla = tabla.sort_values(['probabilidad', 'cliente_id'], ascending=[False, True]).reset_index(drop=True)
    tabla.insert(0, 'puesto', range(1, len(tabla) + 1))
    tabla['decil'] = (tabla.index * 10 // len(tabla) + 1).astype(int)
    n_campana = max(1, math.ceil(capacidad * len(tabla)))
    tabla['en_campana'] = tabla['puesto'] <= n_campana
    por_decil = tabla.groupby('decil')['probabilidad'].mean().round(3).to_dict()
    resumen = {
        'corte': corte, 'origen': url or 'modelo local (models/)', 'generado_en': datetime.now().isoformat(timespec='seconds'),
        **info,
        'clientes_puntuados': int(len(tabla)), 'capacidad': capacidad, 'clientes_en_campana': int(n_campana),
        'probabilidad_minima_en_campana': round(float(tabla.loc[n_campana - 1, 'probabilidad']), 4),
        'probabilidad_media': round(float(tabla['probabilidad'].mean()), 4),
        'probabilidad_media_campana': round(float(tabla.loc[:n_campana - 1, 'probabilidad'].mean()), 4),
        'clientes_con_advertencias': int((tabla['n_advertencias'] > 0).sum()),
        'probabilidad_media_por_decil': {int(k): v for k, v in por_decil.items()},
    }
    if guardar:
        carpeta = config.REPORTES / 'campana'
        carpeta.mkdir(parents=True, exist_ok=True)
        tabla.to_csv(carpeta / f'campana_{corte}.csv', index=False)
        (carpeta / f'campana_{corte}.json').write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding='utf-8')
        resumen['archivos'] = [str((carpeta / f'campana_{corte}.{ext}').relative_to(config.RAIZ)) if config.RAIZ in carpeta.parents
                               else str(carpeta / f'campana_{corte}.{ext}') for ext in ('csv', 'json')]
    return tabla, resumen


def comparar_campanas(tabla, otra_csv):
    """Cuántos clientes de la campaña actual estaban también en otra (por ejemplo, la de antes de reentrenar)."""
    otra = pd.read_csv(otra_csv)
    a = set(tabla.loc[tabla['en_campana'], 'cliente_id'])
    b = set(otra.loc[otra['en_campana'], 'cliente_id'])
    return {'en_ambas': len(a & b), 'solo_ahora': len(a - b), 'solo_antes': len(b - a)}


def main(argv=None):
    ap = argparse.ArgumentParser(description='Puntúa a todos los clientes y saca la lista de la campaña.')
    ap.add_argument('--url', help='URL de la API (p. ej. http://127.0.0.1:8080). Sin ella, usa el modelo local.')
    ap.add_argument('--corte', help='Fecha de corte AAAA-MM-DD (por defecto, el día siguiente a la última factura)')
    ap.add_argument('--capacidad', type=float, default=0.10, help='Fracción de clientes a los que llega la campaña (0.10 = el 10 %%)')
    ap.add_argument('--top', type=int, default=10, help='Cuántos clientes mostrar en pantalla')
    ap.add_argument('--comparar-con', help='CSV de otra campaña para ver cuántos clientes repiten')
    a = ap.parse_args(argv)

    tabla, r = campana(corte=a.corte, url=a.url, capacidad=a.capacidad)
    print(f'Corte de explotación: {r["corte"]} · modelo {r["modelo"]} (huella {r["huella_datos"]}, entrenado {r["entrenado_en"]})')
    print(f'Origen de las predicciones: {r["origen"]}')
    print(f'Clientes puntuados: {r["clientes_puntuados"]} · probabilidad media {r["probabilidad_media"]:.3f}')
    print(f'Campaña: {r["clientes_en_campana"]} clientes (el {a.capacidad:.0%} con más probabilidad), '
          f'probabilidad media {r["probabilidad_media_campana"]:.3f}, mínima {r["probabilidad_minima_en_campana"]:.3f}')
    print(f'Clientes con advertencias (valores que el modelo no vio al entrenar): {r["clientes_con_advertencias"]}')
    print('Probabilidad media por decil: ' + ' · '.join(f'{k}: {v:.2f}' for k, v in r['probabilidad_media_por_decil'].items()))
    print(f'\nLos {a.top} primeros:')
    print(tabla.head(a.top)[['puesto', 'cliente_id', 'probabilidad', 'decil', 'n_advertencias']].to_string(index=False,
          formatters={'probabilidad': '{:.3f}'.format}))
    if a.comparar_con:
        c = comparar_campanas(tabla, a.comparar_con)
        print(f'\nFrente a {a.comparar_con}: {c["en_ambas"]} clientes en ambas campañas, '
              f'{c["solo_ahora"]} nuevos, {c["solo_antes"]} que salen.')
    print('\nGuardado en: ' + ' y '.join(r.get('archivos', [])))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
