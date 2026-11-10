import sys, pandas as pd, numpy as np
ruta_add, ruta_full = sys.argv[1], sys.argv[2]
d = pd.read_csv(ruta_add, sep=';')
print('bank-additional-full:', d.shape); print('columnas:', list(d.columns))
print('nulos (NaN):', int(d.isna().sum().sum()))
cat = d.select_dtypes(exclude='number').columns.tolist()
print('\n«unknown» por columna:', {c:int((d[c]=='unknown').sum()) for c in cat if (d[c]=='unknown').any()})
print('target y:', d['y'].value_counts().to_dict(), '· tasa sí: %.4f' % (d['y']=='yes').mean())
print('duplicados exactos:', int(d.duplicated().sum()))
print('pdays==999:', int((d.pdays==999).sum()), '· poutcome:', d.poutcome.value_counts().to_dict())
print('duration==0:', int((d.duration==0).sum()), '· y=yes entre ellos:', int(((d.duration==0)&(d.y=='yes')).sum()))
for c in ['job','marital','education','default','housing','loan','contact','month','day_of_week']:
    print(' ', c, d[c].value_counts().to_dict())
# orden temporal: reconstruir año por el cambio de mes
meses = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']
m = d['month'].map({k:i for i,k in enumerate(meses)}).to_numpy()
anio = 2008; ant = m[0]; ys=[]
for x in m:
    if x < ant: anio += 1
    ys.append(anio); ant = x
d['anio_inferido'] = ys
d['periodo'] = d['anio_inferido'].astype(str) + '-' + d['month']
orden = d['periodo'].drop_duplicates().tolist()
print('\nperiodos en orden de filas (reconstruidos):', orden)
print('retrocesos de mes dentro de un año (¿orden roto?):', int(sum(1 for i in range(1,len(m)) if m[i] < m[i-1])), '(esperado: 2 cambios de año)')
n = len(d); i70, i85 = int(n*.70), int(n*.85)
for nombre, sl in [('train 70%', slice(0,i70)), ('valid 15%', slice(i70,i85)), ('test 15%', slice(i85,n))]:
    s = d.iloc[sl]
    print(' ', nombre, len(s), 'filas · periodos', s['periodo'].iloc[0], '→', s['periodo'].iloc[-1], '· tasa sí: %.3f' % (s['y']=='yes').mean(),
          '· euribor3m medio %.2f' % s.euribor3m.mean())
print('euribor3m min/max:', d.euribor3m.min(), d.euribor3m.max(), '· nr.employed valores distintos:', d['nr.employed'].nunique())
print('\nsí por año inferido:', d.groupby('anio_inferido')['y'].apply(lambda s: round((s=='yes').mean(),3)).to_dict(), '· filas:', d.groupby('anio_inferido').size().to_dict())

f = pd.read_csv(ruta_full, sep=';')
print('\nbank-full:', f.shape, '· columnas:', list(f.columns))
print('nulos:', int(f.isna().sum().sum()), '· unknown:', {c:int((f[c]=='unknown').sum()) for c in f.select_dtypes(exclude='number').columns if (f[c]=='unknown').any()})
print('y tasa sí: %.4f' % (f.y=='yes').mean(), '· pdays==-1:', int((f.pdays==-1).sum()), '· education:', f.education.value_counts().to_dict())
print('month en orden de filas (primeros cambios):', f['month'].drop_duplicates().tolist()[:14])
