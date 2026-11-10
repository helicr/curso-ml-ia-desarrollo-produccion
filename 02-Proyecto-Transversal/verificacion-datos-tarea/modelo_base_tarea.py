import sys, warnings, pandas as pd, numpy as np
warnings.filterwarnings('ignore')
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, average_precision_score
ruta_def, ruta_bank = sys.argv[1], sys.argv[2]

def evalua(nombre, modelo, Xtr, ytr, Xva, yva, Xte, yte):
    modelo.fit(Xtr, ytr)
    p = {k: modelo.predict_proba(X)[:,1] for k,X in [('valid',Xva),('test',Xte)]}
    print(f'  {nombre:<28} AUC valid {roc_auc_score(yva,p["valid"]):.3f} · test {roc_auc_score(yte,p["test"]):.3f}'
          f' | AP test {average_precision_score(yte,p["test"]):.3f} | prob. media test {p["test"].mean():.3f} (real {yte.mean():.3f})')

# ---------------- Default of Credit Card Clients ----------------
print('== Default of Credit Card Clients · partición aleatoria estratificada 70/15/15 (semilla 0)')
d = pd.read_excel(ruta_def, header=1, engine='xlrd')
y = d['default payment next month']; X = d.drop(columns=['ID','default payment next month'])
Xtr, Xr, ytr, yr = train_test_split(X, y, test_size=.30, stratify=y, random_state=0)
Xva, Xte, yva, yte = train_test_split(Xr, yr, test_size=.50, stratify=yr, random_state=0)
print('  filas train/valid/test:', len(Xtr), len(Xva), len(Xte), '· tasa impago', round(ytr.mean(),3), round(yva.mean(),3), round(yte.mean(),3))
evalua('regresión logística (crudo)', make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)), Xtr,ytr,Xva,yva,Xte,yte)
evalua('boosting (crudo)', HistGradientBoostingClassifier(random_state=0), Xtr,ytr,Xva,yva,Xte,yte)
def fs(X):
    X = X.copy()
    bill = [f'BILL_AMT{i}' for i in range(1,7)]; pay = [f'PAY_AMT{i}' for i in range(1,7)]; st = ['PAY_0','PAY_2','PAY_3','PAY_4','PAY_5','PAY_6']
    X['util_media'] = X[bill].mean(axis=1) / X['LIMIT_BAL']
    X['meses_retraso'] = (X[st] > 0).sum(axis=1)
    X['retraso_max'] = X[st].max(axis=1)
    X['pago_sobre_factura'] = X[pay].sum(axis=1) / X[bill].clip(lower=0).sum(axis=1).replace(0, np.nan)
    X['pago_sobre_factura'] = X['pago_sobre_factura'].fillna(0).clip(0, 5)
    X['tend_factura'] = X['BILL_AMT1'] - X['BILL_AMT6']
    return X
Ftr, Fva, Fte = fs(Xtr), fs(Xva), fs(Xte)
evalua('logística (+6 variables FS)', make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000)), Ftr,ytr,Fva,yva,Fte,yte)
evalua('boosting (+6 variables FS)', HistGradientBoostingClassifier(random_state=0), Ftr,ytr,Fva,yva,Fte,yte)

# ---------------- Bank Marketing ----------------
print('\n== Bank Marketing (bank-additional-full) · partición por orden de filas 70/15/15')
b = pd.read_csv(ruta_bank, sep=';')
yb = (b['y']=='yes').astype(int); Xb = b.drop(columns=['y'])
Xb['pdays_nunca'] = (Xb['pdays']==999).astype(int)
n = len(b); i70, i85 = int(n*.70), int(n*.85)
def pre(cols_drop):
    X = Xb.drop(columns=cols_drop)
    cat = X.select_dtypes(exclude='number').columns.tolist(); num = [c for c in X.columns if c not in cat]
    return X, ColumnTransformer([('n', StandardScaler(), num), ('c', OneHotEncoder(handle_unknown='ignore'), cat)])
for etiqueta, drop in [('con duration', []), ('sin duration', ['duration'])]:
    X, ct = pre(drop)
    sp = (X.iloc[:i70], yb.iloc[:i70], X.iloc[i70:i85], yb.iloc[i70:i85], X.iloc[i85:], yb.iloc[i85:])
    print(f' [{etiqueta}] por orden de filas')
    evalua('regresión logística', make_pipeline(ct, LogisticRegression(max_iter=3000)), *sp)
    evalua('boosting', make_pipeline(ct, HistGradientBoostingClassifier(random_state=0)), *sp)
    Xa, Xr2, ya, yr2 = train_test_split(X, yb, test_size=.30, stratify=yb, random_state=0)
    Xv2, Xt2, yv2, yt2 = train_test_split(Xr2, yr2, test_size=.50, stratify=yr2, random_state=0)
    print(f' [{etiqueta}] aleatoria estratificada (para comparar)')
    evalua('regresión logística', make_pipeline(ct, LogisticRegression(max_iter=3000)), Xa,ya,Xv2,yv2,Xt2,yt2)
    evalua('boosting', make_pipeline(ct, HistGradientBoostingClassifier(random_state=0)), Xa,ya,Xv2,yv2,Xt2,yt2)
