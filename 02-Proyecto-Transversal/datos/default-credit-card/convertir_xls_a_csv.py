"""Convierte el .xls original de Default of Credit Card Clients a CSV, sin cambiar ningun valor.

El .xls trae DOS filas de encabezado: la fila 1 tiene codigos (X1..X23, Y) y la fila 2 los nombres (ID, LIMIT_BAL, ...).
Aqui se usa la fila 2 como encabezado unico. El resto de filas se copia tal cual.

Necesita la libreria xlrd (el entorno env-ia-mlops NO la trae; los .xls antiguos no los lee openpyxl):
    uv run --no-project --with pandas --with xlrd python -I convertir_xls_a_csv.py default_of_credit_card_clients.xls default_of_credit_card_clients.csv
"""
import sys

import pandas as pd

origen, destino = sys.argv[1], sys.argv[2]
df = pd.read_excel(origen, header=1, engine='xlrd')
assert df.shape == (30000, 25), df.shape
df.to_csv(destino, index=False, lineterminator='\n')
print(f'{destino}: {len(df)} filas, {df.shape[1]} columnas')
