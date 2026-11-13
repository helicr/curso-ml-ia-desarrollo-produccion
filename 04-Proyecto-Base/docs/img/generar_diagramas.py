"""Genera los diagramas del proyecto base (PNG) que usan los cuadernos y la documentacion.

Uso (desde la carpeta del proyecto):  python docs/img/generar_diagramas.py
Salida: docs/img/recorrido.png (el flujo completo) y docs/img/operacional_er.png (modelo E-R de retail.db).
"""
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

CARPETA = Path(__file__).resolve().parent
TINTA, GRIS = '#1f2937', '#6b7280'
COLOR = {'fuente': '#e5e7eb', 'oltp': '#fde68a', 'raw': '#fecaca', 'master': '#bfdbfe', 'fs': '#c7d2fe',
         'ml': '#bbf7d0', 'modelo': '#fbcfe8', 'mlflow': '#e9d5ff', 'api': '#ffffff'}


def caja(ax, x, y, w, h, titulo, texto, color, borde=TINTA, discontinua=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.02,rounding_size=0.12', fc=color, ec=borde, lw=1.4,
                                ls='--' if discontinua else '-'))
    ax.text(x + w / 2, y + h - 0.28, titulo, ha='center', va='top', fontsize=11.5, fontweight='bold', color=TINTA)
    ax.text(x + w / 2, y + h - 0.72, texto, ha='center', va='top', fontsize=8.6, color=TINTA, linespacing=1.35)


def flecha(ax, x1, y1, x2, y2, etiqueta=None, dy=0.18):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>', mutation_scale=14, lw=1.4, color=TINTA))
    if etiqueta:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + dy, etiqueta, ha='center', va='bottom', fontsize=8.4, color='#b45309', fontweight='bold')


def recorrido():
    fig, ax = plt.subplots(figsize=(16, 7.4))
    ax.set_xlim(0, 16); ax.set_ylim(0, 7.4); ax.axis('off')
    ax.text(8, 7.15, 'Del dato del negocio al modelo en producción: qué construye cada cuaderno', ha='center', fontsize=15,
            fontweight='bold', color=TINTA)

    # Fondos: los dos «mundos» de datos.
    ax.add_patch(FancyBboxPatch((2.0, 2.55), 2.3, 3.95, boxstyle='round,pad=0.02,rounding_size=0.15', fc='#fffbeb', ec='#d97706', lw=1, ls='--'))
    ax.text(3.15, 6.42, 'retail.db · operacional\n(el negocio escribe aquí)', ha='center', va='top', fontsize=8.3, color='#92400e')
    ax.add_patch(FancyBboxPatch((4.7, 2.55), 8.95, 3.95, boxstyle='round,pad=0.02,rounding_size=0.15', fc='#f8fafc', ec='#2563eb', lw=1, ls='--'))
    ax.text(9.17, 6.42, 'curso.db · base analítica (solo escribe el pipeline)', ha='center', va='top', fontsize=8.3, color='#1e40af')

    y, h, w = 2.85, 2.85, 1.8
    caja(ax, 0.1, y, 1.6, h, 'ARCHIVO', 'Online Retail II\n(UCI, CC BY 4.0)\n\nmuestra .csv\no Excel completo', COLOR['fuente'])
    caja(ax, 2.2, y, 1.9, h, 'OPERACIONAL', 'clientes\nproductos\nfacturas\nlineas_factura\n\nnormalizado,\ncon su suciedad', COLOR['oltp'])
    xs = [4.9, 7.15, 9.4, 11.65]
    datos = [('RAW', 'copia fiel de cada\ntabla de origen\n+ linaje y huella\n\nno se corrige nada', 'raw'),
             ('MASTER', 'dato depurado\ny relacional\n\ndescartes con motivo\nreglas de calidad', 'master'),
             ('FS', 'variables por\ncliente y fecha\nde corte\n\nsolo miran\nal pasado', 'fs'),
             ('ML', 'variables\n+ objetivo y\n+ partición\n(train/valid/test)\n\npor tiempo', 'ml')]
    for x, (t, d, c) in zip(xs, datos):
        caja(ax, x, y, w, h, t, d, COLOR[c])
    caja(ax, 14.0, 4.3, 1.9, 2.2, 'MLflow', 'el cuaderno de\nlaboratorio:\nexperimento\nretencion-90d,\nuna ejecución\npor modelo', COLOR['mlflow'])
    caja(ax, 14.0, 1.95, 1.9, 2.05, 'MODELO', 'el mejor, listo\npara usar:\nmodelo.joblib\nmetadatos.json', COLOR['modelo'])
    caja(ax, 14.0, 0.15, 1.9, 1.45, 'API (S2)', 'predice para\nun cliente', COLOR['api'], borde=GRIS, discontinua=True)

    yc = y + h / 2
    flecha(ax, 1.7, yc, 2.2, yc, '00', dy=0.1)
    flecha(ax, 4.1, yc, 4.9, yc, '01', dy=0.1)
    ax.text(4.5, yc - 0.12, 'ingesta', ha='center', va='top', fontsize=8, color='#b45309')
    for x in xs[:3]:
        flecha(ax, x + w, yc, x + w + 0.45, yc, {4.9: '01', 7.15: '02', 9.4: '03'}[x], dy=0.1)
    flecha(ax, 13.45, yc + 0.5, 14.0, 5.3, '04', dy=0.05)
    flecha(ax, 13.45, yc - 0.5, 14.0, 3.0, '04', dy=-0.45)
    flecha(ax, 14.95, 1.95, 14.95, 1.6)

    # Leyenda inferior: qué pregunta responde cada paso.
    preguntas = [(0.9, '¿De dónde\nviene el dato?'), (3.15, '¿Cómo lo guarda\nel negocio?'), (5.8, '¿Qué llegó,\ntal cual?'),
                 (8.05, '¿Qué es correcto\ny se puede usar?'), (10.3, '¿Qué sabemos de\ncada cliente?'), (12.55, '¿Qué queremos\npredecir?')]
    for x, t in preguntas:
        ax.text(x, 2.35, t, ha='center', va='top', fontsize=8.6, color=GRIS, style='italic')
    ax.text(0.1, 0.55, 'Pregunta de negocio: dado un cliente y una fecha de corte, ¿volverá a comprar en los 90 días siguientes?',
            fontsize=10, color=TINTA, fontweight='bold')
    ax.text(0.1, 0.2, 'Cada flecha es un cuaderno (00 a 04) y su traducción en el paquete ia_mlops. Cada capa se puede borrar y regenerar desde la anterior.',
            fontsize=9, color=GRIS)
    fig.savefig(CARPETA / 'recorrido.png', dpi=130, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def tabla_er(ax, x, y, nombre, filas, w=3.2):
    alto = 0.42 * (len(filas) + 1)
    ax.add_patch(FancyBboxPatch((x, y - alto), w, alto, boxstyle='round,pad=0.02,rounding_size=0.08', fc='white', ec=TINTA, lw=1.4))
    ax.add_patch(FancyBboxPatch((x, y - 0.42), w, 0.42, boxstyle='round,pad=0.02,rounding_size=0.08', fc=COLOR['oltp'], ec=TINTA, lw=1.4))
    ax.text(x + w / 2, y - 0.21, nombre, ha='center', va='center', fontsize=11, fontweight='bold', color=TINTA)
    for i, (clave, campo, tipo) in enumerate(filas):
        yy = y - 0.42 * (i + 1.5)
        ax.text(x + 0.12, yy, clave, ha='left', va='center', fontsize=8.5, fontweight='bold', color='#b45309')
        ax.text(x + 0.55, yy, campo, ha='left', va='center', fontsize=9, color=TINTA, fontweight='bold' if clave == 'PK' else 'normal')
        ax.text(x + w - 0.12, yy, tipo, ha='right', va='center', fontsize=8.3, color=GRIS)
    return alto


def operacional_er():
    fig, ax = plt.subplots(figsize=(12.4, 7.8))
    ax.set_xlim(0, 12.4); ax.set_ylim(0, 7.8); ax.axis('off')
    ax.text(6.2, 7.6, 'Base operacional «retail»: modelo entidad-relación', ha='center', fontsize=14, fontweight='bold', color=TINTA)
    tabla_er(ax, 0.3, 7.2, 'clientes', [('PK', 'cliente_id', 'INTEGER'), ('', 'fecha_alta', 'TEXT')])
    tabla_er(ax, 4.6, 7.2, 'facturas', [('PK', 'factura_id', 'TEXT'), ('FK', 'cliente_id', 'INTEGER · nulo'),
                                        ('', 'pais', 'TEXT'), ('', 'fecha_emision', 'TEXT')])
    tabla_er(ax, 4.6, 4.3, 'lineas_factura', [('PK', 'linea_id', 'INTEGER'), ('FK', 'factura_id', 'TEXT'),
                                              ('FK', 'codigo_producto', 'TEXT'), ('', 'descripcion', 'TEXT'),
                                              ('', 'cantidad', 'INTEGER'), ('', 'precio_unitario', 'REAL'), ('', 'registrada_en', 'TEXT')])
    tabla_er(ax, 8.9, 3.46, 'productos', [('PK', 'codigo_producto', 'TEXT'), ('', 'descripcion', 'TEXT')])

    def cardinalidad(x, y, texto, ha='center'):
        ax.text(x, y, texto, fontsize=10, fontweight='bold', color='#b45309', ha=ha, va='bottom')

    ax.plot([3.5, 4.6], [6.15, 6.15], color=TINTA, lw=1.4)          # clientes.cliente_id -> facturas.cliente_id
    cardinalidad(3.72, 6.2, '0..1'); cardinalidad(4.36, 6.2, '0..n')
    ax.plot([6.2, 6.2], [5.1, 4.3], color=TINTA, lw=1.4)            # facturas -> lineas_factura
    cardinalidad(6.32, 4.88, '1', ha='left'); cardinalidad(6.32, 4.34, '1..n', ha='left')
    ax.plot([7.8, 8.9], [2.83, 2.83], color=TINTA, lw=1.4)          # lineas_factura.codigo_producto -> productos
    cardinalidad(8.07, 2.88, '0..n'); cardinalidad(8.72, 2.88, '1')

    ax.text(0.3, 5.45, 'Claves', fontsize=10.5, fontweight='bold', color=TINTA)
    ax.text(0.3, 5.15, 'PK (clave primaria): identifica cada\nfila; no se repite.\n'
                       'FK (clave foránea): apunta a la PK de\notra tabla; la base impide que apunte\na algo que no existe.',
            fontsize=8.7, color=TINTA, va='top', linespacing=1.4)
    ax.text(0.3, 3.4, 'Relaciones (cardinalidad)', fontsize=10.5, fontweight='bold', color=TINTA)
    ax.text(0.3, 3.1, 'clientes 0..1 — 0..n facturas: un cliente\nhace muchas facturas; una factura puede\nno tener cliente (venta anónima).\n\n'
                      'facturas 1 — 1..n lineas_factura: una\nfactura tiene una o más líneas.\n\n'
                      'productos 1 — 0..n lineas_factura: cada\nlínea vende un producto del catálogo.',
            fontsize=8.7, color=TINTA, va='top', linespacing=1.4)
    ax.text(0.3, 0.3, 'Además: origen_simulacion (control, no es parte del negocio) guarda de qué archivo sale la simulación y su huella sha256.',
            fontsize=8.6, color=GRIS)
    fig.savefig(CARPETA / 'operacional_er.png', dpi=130, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def particiones():
    """Linea de tiempo de los cortes (variables hacia atras, objetivo hacia delante) y como se usan train, valid y test."""
    import sys
    from datetime import date, timedelta

    import matplotlib.dates as mdates

    sys.path.insert(0, str(CARPETA.parents[1]))
    from ia_mlops import config

    colores = {'train': '#60a5fa', 'valid': '#fbbf24', 'test': '#34d399'}
    inicio, fin_datos = date(2009, 12, 1), date(2011, 12, 9)
    cortes = [(p, date.fromisoformat(c)) for p, lista in config.CORTES.items() for c in lista]
    ventana = timedelta(days=config.VENTANA_OBJETIVO_DIAS)

    fig = plt.figure(figsize=(15, 10.2))
    ax = fig.add_axes([0.13, 0.47, 0.67, 0.45])
    fig.text(0.5, 0.965, 'Train, validación y test: se reparten por FECHA DE CORTE, no al azar', ha='center', fontsize=15, fontweight='bold', color=TINTA)
    for i, (part, c) in enumerate(reversed(cortes)):
        y = i
        ax.barh(y, (c - inicio).days, left=inicio, height=0.55, color='#e5e7eb', edgecolor='#9ca3af', lw=0.6)
        ax.barh(y, ventana.days, left=c, height=0.55, color=colores[part], edgecolor=TINTA, lw=0.8)
        ax.plot([c, c], [y - 0.38, y + 0.38], color=TINTA, lw=1.8)
        ax.text(c + ventana + timedelta(days=6), y, f'y: ¿compra antes del {(c + ventana).isoformat()}?', va='center', fontsize=7.8, color=GRIS,
                bbox=dict(fc='white', ec='none', pad=0.6), zorder=3)
    ax.set_yticks(range(len(cortes)))
    ax.set_yticklabels([f'corte {c.isoformat()}' for _, c in reversed(cortes)], fontsize=9)
    ax.axvline(fin_datos, color='#dc2626', lw=1.2, ls='--')
    ax.text(fin_datos + timedelta(days=8), len(cortes) - 0.35, 'último día con datos\n2011-12-09: ninguna ventana\npuede pasar de aquí', color='#dc2626', fontsize=8.5, ha='left', va='bottom')
    ax.set_xlim(inicio, date(2012, 8, 1)); ax.set_ylim(-0.7, len(cortes) + 0.6)
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10])); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.tick_params(axis='x', labelsize=9); ax.grid(axis='x', color='#f1f5f9'); ax.set_axisbelow(True)
    for lado in ('top', 'right'):
        ax.spines[lado].set_visible(False)
    # Llaves de cada particion, a la derecha.
    grupos = {'test': (0, 1), 'valid': (2, 2), 'train': (3, 9)}
    textos = {'train': 'TRAIN · 7 cortes mensuales\nel modelo APRENDE aquí',
              'valid': 'VALID · 1 corte\nse COMPARAN modelos\ny se elige el mejor',
              'test': 'TEST · 2 cortes\nexamen final: se mide\nel elegido UNA vez'}
    for part, (a, b) in grupos.items():
        x = 1.005
        ax.annotate('', xy=(x, (a - 0.3 + 0.7) / (len(cortes) + 1.3)), xycoords='axes fraction', xytext=(x, (b + 0.3 + 0.7) / (len(cortes) + 1.3)),
                    arrowprops=dict(arrowstyle='-', color=colores[part], lw=5))
        ax.text(1.02, ((a + b) / 2 + 0.7) / (len(cortes) + 1.3), textos[part], transform=ax.transAxes, va='center', fontsize=9.5,
                fontweight='bold', color=TINTA)
    ax.text(0.0, 1.03, 'Cada fila es UNA FECHA DE CORTE.   Gris: el pasado, con el que se calculan las variables (FS).   Color: la ventana de 90 días donde se mira el objetivo y.',
            transform=ax.transAxes, fontsize=9.5, color=TINTA)

    # Parte inferior: como se forma y como se carga.
    ab = fig.add_axes([0.02, 0.02, 0.96, 0.36]); ab.set_xlim(0, 16); ab.set_ylim(0, 5.2); ab.axis('off')
    ab.text(0.1, 5.0, '¿Cómo se obtiene cada partición y cómo se carga para entrenar?', fontsize=12.5, fontweight='bold', color=TINTA)
    caja(ab, 0.1, 0.5, 3.2, 4.0, '1 · ml_particiones', 'config.CORTES asigna cada\nfecha de corte a una partición\n\n2010-06-01 … 2010-12-01 → train\n2011-03-01 → valid\n2011-06-01, 2011-09-01 → test\n\n+ fin de su ventana (corte + 90 días)', '#f1f5f9')
    caja(ab, 3.8, 0.5, 3.8, 4.0, '2 · ml_dataset (cuaderno 03)', '1 fila = 1 cliente × 1 corte\n\nvariables ← fs_cliente_corte (pasado)\ny ← ¿compra válida en la ventana?\nparticion ← la de su corte (JOIN)\n\nsql/ml/02_poblar_ml.sql', '#bbf7d0')
    caja(ab, 8.1, 0.5, 3.0, 4.0, '3 · cuaderno 04 la lee', "pd.read_sql(\n 'SELECT * FROM ml_dataset')\n\ny la separa por la\ncolumna particion:\nX = las 13 variables\ny = la columna y", COLOR['modelo'])
    for j, (part, txt) in enumerate([('train', "X['train'], y['train']  →  modelo.fit(...)"), ('valid', "X['valid'], y['valid']  →  comparar AUC, elegir"),
                                     ('test', "X['test'], y['test']  →  medir el elegido, una vez")]):
        yy = 3.25 - j * 1.35
        ab.add_patch(FancyBboxPatch((11.7, yy), 4.2, 1.05, boxstyle='round,pad=0.02,rounding_size=0.1', fc=colores[part], ec=TINTA, lw=1.2))
        ab.text(11.85, yy + 0.75, f"df[df['particion'] == '{part}']", fontsize=8.6, color=TINTA, fontweight='bold', va='center', family='monospace')
        ab.text(11.85, yy + 0.32, txt, fontsize=8.4, color=TINTA, va='center')
        flecha(ab, 11.1, 2.5, 11.7, yy + 0.52)
    flecha(ab, 3.3, 2.5, 3.8, 2.5)
    flecha(ab, 7.6, 2.5, 8.1, 2.5)
    fig.savefig(CARPETA / 'particiones.png', dpi=120, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def mlflow_esquema():
    """Que hace el codigo, como organiza MLflow lo que apunta y donde lo guarda."""
    fig, ax = plt.subplots(figsize=(16, 9.2))
    ax.set_xlim(0, 16); ax.set_ylim(0, 9.2); ax.axis('off')
    ax.text(8, 9.0, 'MLflow: el cuaderno de laboratorio de los entrenamientos', ha='center', fontsize=15, fontweight='bold', color=TINTA)

    # 1. El codigo
    ax.text(0.15, 8.35, '1 · Lo que escribe tu código', fontsize=11.5, fontweight='bold', color=TINTA)
    pasos = [("mlflow.set_tracking_uri(\n 'sqlite:///models/mlflow.db')", '¿DÓNDE apunto?'),
             ("mlflow.set_experiment(\n 'retencion-90d')", '¿en qué\nEXPERIMENTO?'),
             ("with mlflow.start_run(\n   run_name='gradient_boosting'):", 'abre una EJECUCIÓN'),
             ("  mlflow.log_param('modelo', ...)\n  mlflow.log_metric('valid_auc', ...)", 'apunta lo DECIDIDO\ny lo MEDIDO'),
             ("  mlflow.sklearn.log_model(modelo, ...)", 'guarda el MODELO\n(solo el elegido)')]
    for i, (codigo, que) in enumerate(pasos):
        y = 6.95 - i * 1.42
        ax.add_patch(FancyBboxPatch((0.15, y), 3.4, 1.0, boxstyle='round,pad=0.02,rounding_size=0.08', fc='#0f172a', ec=TINTA))
        ax.text(0.25, y + 0.5, codigo, fontsize=7.4, family='monospace', color='#e2e8f0', va='center')
        ax.text(3.65, y + 0.5, que, fontsize=8.2, color='#b45309', fontweight='bold', va='center')
        if i:
            flecha(ax, 1.85, y + 1.42, 1.85, y + 1.0)

    # 2. Como lo organiza
    ax.text(5.6, 8.35, '2 · Cómo lo organiza MLflow', fontsize=11.5, fontweight='bold', color=TINTA)
    ax.add_patch(FancyBboxPatch((5.6, 0.45), 5.4, 7.6, boxstyle='round,pad=0.02,rounding_size=0.15', fc='#faf5ff', ec='#7c3aed', lw=1.4))
    ax.text(8.3, 7.8, 'EXPERIMENTO  «retencion-90d»', ha='center', fontsize=11, fontweight='bold', color='#5b21b6')
    ax.text(8.3, 7.45, 'agrupa todos los intentos del mismo problema', ha='center', fontsize=8.4, color='#5b21b6', style='italic')
    ejecuciones = [('referencia_sin_aprender', 'modelo, ventana, n_variables, huella', 'train_auc, valid_auc, test_auc…', '—'),
                   ('regresion_logistica', 'modelo, ventana, n_variables, huella', 'train_auc, valid_auc, test_auc…', '—'),
                   ('gradient_boosting', 'modelo, ventana, n_variables, huella', 'train_auc, valid_auc, test_auc…', '—'),
                   ('MEJOR-<el elegido>', 'modelo, huella', 'las del elegido', 'modelo + firma + ejemplo')]
    for i, (nombre, params, mets, art) in enumerate(ejecuciones):
        y = 5.75 - i * 1.55
        mejor = nombre.startswith('MEJOR')
        ax.add_patch(FancyBboxPatch((5.85, y), 4.9, 1.35, boxstyle='round,pad=0.02,rounding_size=0.08',
                                    fc=COLOR['modelo'] if mejor else 'white', ec=TINTA, lw=1.2))
        ax.text(5.98, y + 1.1, f'EJECUCIÓN (run): {nombre}', fontsize=8.8, fontweight='bold', color=TINTA, va='center')
        ax.text(5.98, y + 0.75, f'parámetros: {params}', fontsize=7.9, color=TINTA, va='center')
        ax.text(5.98, y + 0.47, f'métricas: {mets}', fontsize=7.9, color=TINTA, va='center')
        ax.text(5.98, y + 0.19, f'artefactos: {art}', fontsize=7.9, color=TINTA, va='center', fontweight='bold' if mejor else 'normal')
    ax.text(8.3, 0.62, 'Cada vez que ejecutas el cuaderno 04 se AÑADEN 4 ejecuciones nuevas:\nel experimento acumula el historial y permite comparar.',
            ha='center', fontsize=8, color='#5b21b6')

    # 3. Donde lo guarda
    ax.text(11.5, 8.35, '3 · Dónde lo guarda', fontsize=11.5, fontweight='bold', color=TINTA)
    caja(ax, 11.5, 5.05, 4.35, 3.0, 'models/mlflow.db', 'backend store (una base SQLite)\n\nexperimentos, ejecuciones,\nparámetros, métricas, etiquetas\ny fechas', '#e0e7ff')
    caja(ax, 11.5, 1.75, 4.35, 3.0, 'models/mlartifacts/', 'artifact store (carpetas)\n\nmodels/m-<id>/artifacts/\n  MLmodel · model.pkl · conda.yaml\n  requirements.txt · input_example.json', '#fce7f3')
    caja(ax, 11.5, 0.15, 4.35, 1.3, 'mlflow ui', 'lee mlflow.db y lo muestra en\nhttp://127.0.0.1:5000', '#ffffff', borde=GRIS, discontinua=True)
    flecha(ax, 11.0, 6.5, 11.5, 6.5)
    flecha(ax, 11.0, 1.2, 11.5, 3.2)
    ax.text(11.25, 6.68, 'texto y\nnúmeros', fontsize=7.5, color=GRIS, ha='center', va='bottom')
    ax.text(11.12, 2.35, 'archivos', fontsize=7.5, color=GRIS, ha='center', rotation=58)
    fig.savefig(CARPETA / 'mlflow.png', dpi=120, bbox_inches='tight', facecolor='white')
    plt.close(fig)


if __name__ == '__main__':
    recorrido()
    operacional_er()
    particiones()
    mlflow_esquema()
    print('Diagramas en', CARPETA)
