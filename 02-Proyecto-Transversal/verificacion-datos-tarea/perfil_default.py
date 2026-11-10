import sys, pandas as pd, numpy as np
ruta = sys.argv[1]
df = pd.read_excel(ruta, header=1, engine='xlrd')
print('forma:', df.shape); print('columnas:', list(df.columns))
print('\ndtypes distintos:', df.dtypes.value_counts().to_dict())
print('nulos totales:', int(df.isna().sum().sum()))
print('ID único:', df['ID'].is_unique, '· min/max ID:', df['ID'].min(), df['ID'].max())
t = 'default payment next month'
print('\nobjetivo (valores):', df[t].value_counts().to_dict(), '· tasa impago: %.4f' % df[t].mean())
sin_id = df.drop(columns=['ID'])
print('duplicados exactos (sin ID):', int(sin_id.duplicated().sum()))
for c in ['SEX','EDUCATION','MARRIAGE']:
    print('\n', c, df[c].value_counts().sort_index().to_dict())
pay = [c for c in df.columns if c.startswith('PAY_') and not c.startswith('PAY_AMT')]
print('\ncolumnas PAY_:', pay)
for c in pay:
    print(' ', c, df[c].value_counts().sort_index().to_dict())
bill = [c for c in df.columns if c.startswith('BILL_AMT')]
pamt = [c for c in df.columns if c.startswith('PAY_AMT')]
print('\nLIMIT_BAL min/mediana/max:', df.LIMIT_BAL.min(), df.LIMIT_BAL.median(), df.LIMIT_BAL.max())
print('AGE min/mediana/max:', df.AGE.min(), df.AGE.median(), df.AGE.max())
print('BILL_AMT negativos por mes:', {c:int((df[c]<0).sum()) for c in bill})
print('PAY_AMT negativos por mes:', {c:int((df[c]<0).sum()) for c in pamt})
print('clientes con BILL_AMT > LIMIT_BAL en algún mes:', int((df[bill].gt(df.LIMIT_BAL, axis=0)).any(axis=1).sum()))
print('clientes con las 6 facturas = 0 y los 6 pagos = 0:', int(((df[bill]==0).all(axis=1)&(df[pamt]==0).all(axis=1)).sum()))
print('\ntasa de impago por PAY_0:', df.groupby('PAY_0')[t].agg(['mean','size']).round(3).to_dict('index'))
