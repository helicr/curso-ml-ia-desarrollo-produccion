"""Configuracion del proyecto: rutas, fechas de corte, ventana del objetivo y lista de variables.

Caso transversal: Online Retail II (UCI, CC BY 4.0). Pregunta de negocio:
    «Dado un cliente y una fecha de corte, ¿volvera a comprar en los 90 dias siguientes?»

Todo lo que define el caso esta aqui, en un solo sitio: cambiar la ventana, los cortes o las variables no exige tocar el resto
del codigo. Los cuadernos repiten estos valores en su celda de parametros; las pruebas comprueban que dan el mismo resultado.

Las rutas se pueden cambiar con variables de entorno (util en pruebas y en contenedores):
    CURSO_DB_OPERACIONAL  base operacional «retail», la fuente   (por defecto data/external/retail.db)
    CURSO_DB       base SQLite analitica       (por defecto data/processed/curso.db)
    CURSO_DB_SOLO_LECTURA  1 = abrir esa base en solo lectura (el contenedor de la interfaz la recibe montada :ro)
    CURSO_URL_API  la API del modelo a la que llama la interfaz (en el contenedor: http://api:8080)
    CURSO_MODELOS  carpeta de modelos          (por defecto models/)
    CURSO_REPORTES carpeta de reportes         (por defecto reports/)
    CURSO_LOG_NIVEL nivel de registro de la API (por defecto INFO)
"""
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DATA_RAW = RAIZ / 'data' / 'raw'
DATA_PROCESSED = RAIZ / 'data' / 'processed'
SQL = RAIZ / 'sql'
# Dos bases: la OPERACIONAL simula el sistema de ventas (la fuente); la ANALITICA guarda las capas RAW a ML.
DB_OPERACIONAL = Path(os.environ.get('CURSO_DB_OPERACIONAL', RAIZ / 'data' / 'external' / 'retail.db'))
DB =Path(os.environ.get('CURSO_DB', DATA_PROCESSED / 'curso.db'))
DB_SOLO_LECTURA = os.environ.get('CURSO_DB_SOLO_LECTURA', '') == '1'   # 1 = abrir la base sin poder escribir (contenedor de la interfaz)
MODELOS = Path(os.environ.get('CURSO_MODELOS', RAIZ / 'models'))
REPORTES = Path(os.environ.get('CURSO_REPORTES', RAIZ / 'reports'))

# Archivos de los que se construye la base operacional (cuaderno 00).
#   muestra:  CSV pequeno incluido en el repositorio (150 clientes). Para pruebas, CI y clase.
#   completo: Excel original de UCI (1,07 millones de lineas). Se descarga con `python -m ia_mlops.dataset descargar`.
FUENTES = {
    'muestra': DATA_RAW / 'muestra_online_retail_ii.csv',
    'completo': DATA_RAW / 'online_retail_ii' / 'online_retail_II.xlsx',
}
URL_UCI = 'https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip'
SHA256_ZIP_UCI = '572e36277c2390fbfde10664750731e0a86f55e33470d91919085f0408e67bfb'

# Objetivo: el cliente compra al menos una vez en los VENTANA_OBJETIVO_DIAS siguientes al corte.
VENTANA_OBJETIVO_DIAS = 90

# Particion TEMPORAL. Las ventanas del objetivo no se solapan entre particiones:
#   el ultimo corte de train + 90 dias = el corte de valid; el de valid + 90 dias <= el primer corte de test.
CORTES = {
    'train': ['2010-06-01', '2010-07-01', '2010-08-01', '2010-09-01', '2010-10-01', '2010-11-01', '2010-12-01'],
    'valid': ['2011-03-01'],
    'test': ['2011-06-01', '2011-09-01'],
}

# Variables de la capa FS que usa el modelo (columnas de fs_cliente_corte).
FEATURES = [
    'recencia_dias', 'frecuencia', 'monto_total', 'ticket_medio', 'unidades_total', 'productos_distintos',
    'antiguedad_dias', 'frecuencia_90d', 'monto_90d', 'frecuencia_180d', 'dias_medios_entre_compras',
    'devoluciones', 'es_reino_unido',
]
OBJETIVO = 'y'

# El modelo en formato MLflow (con su FIRMA) que se guarda dentro de MODELOS. Es lo que carga la API y lo que se copia a la imagen Docker.
CARPETA_MODELO_MLFLOW = 'modelo_mlflow'

# MLflow: experimento (agrupa las ejecuciones) y nombre del modelo en el registro (cada entrenamiento crea una versión nueva).
EXPERIMENTO_MLFLOW = 'retencion-90d'
MODELO_REGISTRADO = 'retencion-90d'

# Interfaz de consulta (S2, ia_mlops/interfaz): de la PROBABILIDAD que da el modelo a una RECOMENDACION para el negocio.
# Es una regla de negocio, no sale del modelo: los umbrales y las acciones se acuerdan con quien hace la campaña y se cambian aquí.
# Se recorre en orden: el primer tramo cuyo «desde» no supere la probabilidad es el del cliente.
SEGMENTOS_RECOMPRA = [
    {'segmento': 'alta', 'desde': 0.70,
     'recomendacion': 'Comprará probablemente sin ayuda: comunicación habitual o venta cruzada; no gastar el incentivo.'},
    {'segmento': 'media', 'desde': 0.40,
     'recomendacion': 'Indeciso: prioridad de la campaña de recompra; aquí un incentivo puede cambiar el resultado.'},
    {'segmento': 'baja', 'desde': 0.0,
     'recomendacion': 'Poco probable que compre en 90 días: contacto de recuperación de bajo coste o no invertir.'},
]
URL_API = os.environ.get('CURSO_URL_API')   # la interfaz llama a la API del modelo aquí; sin valor, usa el modelo de models/ directamente
