"""Construye los tres notebooks del extra «MCP en notebooks» a partir de las fuentes de los servidores.

    python construir_notebooks.py            # escribe 00_..., 01_..., 02_... SIN salidas
    python construir_notebooks.py --ejecutar # además los ejecuta y guarda las salidas reales (tarda 1-2 min; BigQuery solo si GCP_PROJECT está definido)

Los servidores (fuentes/mcp_datos.py y fuentes/mcp_modelo.py) se copian DENTRO de los notebooks con %%writefile: el alumno solo trabaja con notebooks.
"""
import sys
from pathlib import Path

import nbformat as nbf

AQUI = Path(__file__).resolve().parent
FUENTES = AQUI / 'fuentes'
NOTEBOOKS = ['00_preparar_entorno.ipynb', '01_mcp_datos_sqlite_y_bigquery.ipynb', '02_mcp_modelo_prediccion.ipynb']


def md(t):
    return nbf.v4.new_markdown_cell(t.strip('\n'))


def code(t):
    return nbf.v4.new_code_cell(t.strip('\n'))


def escribir_servidor(nombre):
    return code(f'%%writefile _trabajo/{nombre}\n' + (FUENTES / nombre).read_text(encoding='utf-8'))


PREPARAR = '''
import asyncio, json, os, sys, sqlite3
from pathlib import Path

AQUI = Path.cwd()
RAIZ = next(p for p in [AQUI, *AQUI.parents] if (p / '04-Proyecto-Base').is_dir())    # funciona en tu portátil y en un Codespace
PROYECTO = RAIZ / '04-Proyecto-Base'
BD = PROYECTO / 'data' / 'processed' / 'curso.db'
TRABAJO = AQUI / '_trabajo'
TRABAJO.mkdir(exist_ok=True)
print('Repositorio:', RAIZ.name, '| base de datos:', BD.name, 'existe' if BD.is_file() else 'NO EXISTE (mira el notebook 00)')
'''

CLIENTE = '''
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class ClienteMCP:
    """Lanza un servidor MCP como proceso hijo y habla con él por su entrada y salida estándar (transporte «stdio»).
    Es lo mismo que hacen VS Code, Claude Desktop o un agente: arrancan el servidor, le piden las herramientas y las llaman por nombre."""

    def __init__(self, script, **entorno):
        self.params = StdioServerParameters(command=sys.executable, args=[str(script)], env={**os.environ, **{k: str(v) for k, v in entorno.items()}})

    async def __aenter__(self):
        self._pila = AsyncExitStack()
        self._log = open(TRABAJO / 'servidor.err', 'w', encoding='utf-8')          # lo que el servidor escribe por stderr
        leer, escribir = await self._pila.enter_async_context(stdio_client(self.params, errlog=self._log))
        self.sesion = await self._pila.enter_async_context(ClientSession(leer, escribir))
        await self.sesion.initialize()
        return self

    async def __aexit__(self, *a):
        await self._pila.aclose()
        self._log.close()

    async def herramientas(self):
        return (await self.sesion.list_tools()).tools

    async def llamar(self, nombre, **argumentos):
        r = await self.sesion.call_tool(nombre, argumentos)
        if r.isError:                                                                # el propio protocolo rechazó los argumentos (tipos)
            return {'error_del_protocolo': r.content[0].text}
        return r.structuredContent or json.loads(r.content[0].text)
'''


def nb00():
    return [
        md('''
# Extra de S5 · MCP en notebooks · 0. Preparar el entorno

En este extra montas **dos servidores MCP** sin salir de notebooks:

1. **`mcp-datos-master`**: un LLM consulta la capa *master* del caso Retail, **en SQLite o en BigQuery** (dos conectores, la misma interfaz).
2. **`mcp-modelo-retencion`**: el modelo de retención va dentro del MCP; le pasas un cliente y devuelve la predicción.

Este notebook solo comprueba que tienes lo necesario. Tarda un minuto. Si algo sale en rojo, dice qué hacer.
'''),
        code(PREPARAR),
        md('## 1. Instalar lo que añade este extra\n\nSolo hace falta una vez. Si ya hiciste el laboratorio de agentes de S5, `mcp` ya está.'),
        code('''
%pip install -q -r requisitos-extra-mcp.txt
import importlib.metadata as md
for paquete in ('mcp', 'google-cloud-bigquery', 'pyarrow', 'mlflow', 'pandas'):
    print(f'{paquete:<24}', md.version(paquete))
'''),
        md('## 2. Los datos y el modelo del proyecto\n\nNecesitas la base `curso.db` (capa master y variables) y el modelo registrado en MLflow. Los crea el pipeline de S1 (`python -m ia_mlops.pipeline`, unos 30 s con la muestra).'),
        code('''
import sqlite3
problemas = []
if not BD.is_file():
    problemas.append('Falta curso.db: desde 04-Proyecto-Base ejecuta  python -m ia_mlops.pipeline')
else:
    con = sqlite3.connect(BD)
    for t in ('master_clientes', 'master_facturas', 'master_lineas', 'master_productos', 'fs_produccion'):
        try:
            print(f'{t:<18}', con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0], 'filas')
        except sqlite3.OperationalError:
            problemas.append(f'Falta la tabla {t}: ejecuta  python -m ia_mlops.explotacion  (crea fs_produccion) tras el pipeline')
    con.close()

sys.path.insert(0, str(PROYECTO))
from ia_mlops import alias_modelo as A
try:
    uri, mlc = A.conectar()
    print()
    print(A.texto_estado(A.estado(mlc)))
except A.ErrorAlias as e:
    problemas.append(str(e))

print()
print('TODO LISTO' if not problemas else 'FALTA:\\n- ' + '\\n- '.join(problemas))
'''),
        md('''
## 3. BigQuery (opcional)

El notebook 01 tiene dos conectores. **SQLite funciona sin nada más.** Para el de BigQuery necesitas un proyecto de Google Cloud donde puedas crear un dataset:

```
gcloud auth application-default login
gcloud config set project TU_PROYECTO
export GCP_PROJECT=TU_PROYECTO        # en Windows (cmd): set GCP_PROJECT=TU_PROYECTO
```

Si no lo configuras, el notebook 01 se salta esas celdas y sigue con SQLite. **No uses el proyecto de tu trabajo**: el notebook crea y borra un dataset `curso_master` (22 000 filas, unos 2 MB; con el nivel gratuito de BigQuery no cuesta nada, pero es tu cuenta).
'''),
        code('''
HAY_BQ = False
if os.environ.get('GCP_PROJECT'):
    try:
        import google.auth
        google.auth.default()
        HAY_BQ = True
    except Exception as e:                                      # noqa: BLE001
        print('GCP_PROJECT está definido, pero no hay credenciales:', str(e)[:140])
print('BigQuery:', f"listo en el proyecto {os.environ['GCP_PROJECT']}" if HAY_BQ else 'no configurado (el notebook 01 usará solo SQLite)')
'''),
    ]


LLAMADAS_DATOS = '''
CASOS = [('listar_tablas', {}), ('describir_tabla', {'tabla': 'master_clientes'}), ('resumen_cliente', {'cliente_id': 12369}),
         ('ultimas_facturas', {'cliente_id': 12369, 'n': 2}), ('ventas_por_pais', {'n': 3}), ('top_productos', {'n': 3}),
         ('consulta_sql', {'sql': 'SELECT pais, COUNT(*) AS clientes FROM master_clientes GROUP BY pais ORDER BY clientes DESC, pais LIMIT 3'})]


async def ejecutar_casos(**entorno):
    async with ClienteMCP(TRABAJO / 'mcp_datos.py', **entorno) as c:
        return {nombre: await c.llamar(nombre, **args) for nombre, args in CASOS}
'''


def nb01():
    return [
        md('''
# Extra de S5 · MCP en notebooks · 1. Un MCP que consulta la capa master (SQLite y BigQuery)

**Qué vas a construir:** un servidor MCP que deja a un LLM hacer preguntas sobre los clientes, facturas y productos del caso Retail, **sin darle acceso libre a la base de datos**.

**Qué vas a aprender:**
- cómo se publica una consulta como *herramienta* con nombre, argumentos y una descripción que el LLM lee;
- por qué un «SQL libre» es peligroso y cómo se vigila en **capas** (herramientas fijas, vigilancia del SQL, conexión de solo lectura, topes de filas y de coste);
- cómo un mismo servidor habla con **dos motores** (SQLite y BigQuery) escondiéndolos tras un *conector*, y cómo se **comprueba que dan lo mismo**.

> Un MCP (Model Context Protocol) es un protocolo estándar para que un LLM use herramientas de un servidor sin ver su código ni su base de datos.
> En el laboratorio de agentes de S5 ya usaste `mcp-retencion` (lista de clientes y puntuación). Aquí construyes los tuyos desde cero.
'''),
        code(PREPARAR),
        md('''
## 1. El servidor

Lee el código con calma: es la parte importante. Cuatro ideas:

1. **Conectores** (`ConectorSQLite`, `ConectorBigQuery`): ofrecen `tabla()`, `columnas()` y `ejecutar()`. El resto del servidor no sabe qué motor hay detrás.
2. **Herramientas con nombre** (`resumen_cliente`, `ventas_por_pais`...): el SQL lo escribes tú, el LLM solo da un número. Es lo más seguro.
3. **`consulta_sql`**: el último recurso, vigilado por `validar_sql` (solo SELECT, una sentencia, sin comentarios, solo tablas `master_*`).
4. **Las capas que no dependen de nadie**: SQLite se abre en modo solo lectura (`mode=ro`), BigQuery tiene un tope de bytes (`maximum_bytes_billed`) y nunca se devuelven más de 50 filas.

La celda siguiente **escribe el servidor en el archivo `_trabajo/mcp_datos.py`** (así lo puede lanzar un proceso aparte, que es lo que hacen los clientes MCP).
'''),
        escribir_servidor('mcp_datos.py'),
        md('''
## 2. El cliente

Un servidor MCP no se usa a mano: lo arranca un cliente (VS Code, un agente...). Esta clase hace de cliente: lanza el servidor como proceso y le pide cosas.
Es la misma mecánica que usa cualquier cliente MCP, en 30 líneas.
'''),
        code(CLIENTE),
        md('## 3. Qué ofrece el servidor\n\nLo primero que hace un cliente es preguntar qué herramientas hay. **La descripción es lo que el LLM lee para decidir cuál usar**: por eso es corta y dice cuándo usarla.'),
        code('''
os.environ['CURSO_DB'] = str(BD)
async with ClienteMCP(TRABAJO / 'mcp_datos.py', CURSO_DB=BD, MCP_BACKEND='sqlite') as c:
    for h in await c.herramientas():
        print(f'• {h.name}\\n    {h.description}\\n    argumentos: {list(h.inputSchema.get("properties", {}))}\\n')
'''),
        md('## 4. Usarlo con SQLite\n\nSiete llamadas, una por herramienta. Fíjate en que la respuesta siempre dice qué `motor` la ha producido.'),
        code(LLAMADAS_DATOS + '''
resultados_sqlite = await ejecutar_casos(CURSO_DB=BD, MCP_BACKEND='sqlite')
for nombre, r in resultados_sqlite.items():
    print(f'--- {nombre}')
    print(json.dumps(r, ensure_ascii=False, default=str)[:420])
'''),
        md('''
## 5. Intentar romperlo

Un LLM puede equivocarse o ser engañado (por ejemplo, por un texto malicioso dentro de un dato). Estas son consultas que **nunca** deben ejecutarse.
Cada una se frena en una capa distinta: mira cuál.
'''),
        code('''
ATAQUES = {
    'borrar una tabla':               'DROP TABLE master_clientes',
    'modificar datos':                "UPDATE master_clientes SET pais = 'X'",
    'varias sentencias':              'SELECT 1; DELETE FROM master_lineas',
    'comentario para esconder algo':  'SELECT * FROM master_clientes -- WHERE pais = 1',
    'otra tabla (variables del modelo)': 'SELECT * FROM fs_produccion',
    'el catálogo del motor':          'SELECT name FROM sqlite_master',
    'tabla con ruta completa':        'SELECT * FROM main.master_clientes',
    'unir tablas con coma':           'SELECT * FROM master_clientes, master_facturas',
}
async with ClienteMCP(TRABAJO / 'mcp_datos.py', CURSO_DB=BD, MCP_BACKEND='sqlite') as c:
    for nombre, sql in ATAQUES.items():
        r = await c.llamar('consulta_sql', sql=sql)
        print(f'{nombre:<36} → {"RECHAZADA: " + r["error"] if "error" in r else "¡SE EJECUTÓ!"}')
    print()
    r = await c.llamar('consulta_sql', sql='SELECT * FROM master_lineas')
    print(f'SELECT * de 22 117 líneas → devuelve {r["n"]} filas (truncado: {r["truncado"]}): el tope de filas protege al LLM y a su contexto')
    r = await c.llamar('resumen_cliente', cliente_id='abc')
    print('cliente_id = "abc" →', r)
'''),
        md('''
**Lo que muestra la prueba**
- Las ocho las frena `validar_sql` (capa 2). Pero **no te fíes de una sola capa**: una expresión regular no es un analizador de SQL.
- Si una se colase, SQLite está abierto en solo lectura (capa 3) y un `UPDATE` fallaría igualmente. Compruébalo tú: quita la vigilancia a mano y prueba (ver el ejercicio 1 al final).
- El último caso lo rechaza el propio protocolo: la herramienta declara `cliente_id: int` y el SDK valida el tipo antes de llamar a tu función.
'''),
        md('''
## 6. BigQuery: el segundo conector

El servidor es **el mismo archivo**. Solo cambia una variable de entorno: `MCP_BACKEND=bigquery` (más `GCP_PROJECT` y `BQ_DATASET`).
Para que haya algo que consultar, primero subimos las cuatro tablas *master* a un dataset de tu proyecto.

> Esta parte necesita un proyecto de Google Cloud y credenciales (notebook 00, apartado 3). Si no las tienes, las celdas dicen «saltada» y puedes seguir.
'''),
        code('''
GCP_PROJECT = os.environ.get('GCP_PROJECT', '')
BQ_DATASET = os.environ.get('BQ_DATASET', 'curso_master')
BQ_LOCATION = os.environ.get('BQ_LOCATION', 'US')
HAY_BQ = False
if GCP_PROJECT:
    try:
        import google.auth
        google.auth.default()
        HAY_BQ = True
    except Exception as e:                                              # noqa: BLE001
        print('Credenciales de Google no disponibles:', str(e)[:140])
print(f'BigQuery: proyecto «{GCP_PROJECT}», dataset «{BQ_DATASET}»' if HAY_BQ else 'BigQuery SALTADO: define GCP_PROJECT y las credenciales (notebook 00, apartado 3).')
'''),
        code('''
TABLAS_MASTER = ['master_clientes', 'master_facturas', 'master_lineas', 'master_productos']
if HAY_BQ:
    import pandas as pd
    from google.cloud import bigquery
    bq = bigquery.Client(project=GCP_PROJECT)
    ds = bigquery.Dataset(f'{GCP_PROJECT}.{BQ_DATASET}')
    ds.location = BQ_LOCATION
    bq.create_dataset(ds, exists_ok=True)
    con = sqlite3.connect(BD)
    for t in TABLAS_MASTER:
        df = pd.read_sql(f'SELECT * FROM {t}', con)
        for col in df.columns:                                           # los enteros con huecos llegan como decimales: se devuelven a enteros
            if df[col].dtype == 'float64' and df[col].dropna().apply(float.is_integer).all():
                df[col] = df[col].astype('Int64')
        bq.load_table_from_dataframe(df, f'{GCP_PROJECT}.{BQ_DATASET}.{t}', job_config=bigquery.LoadJobConfig(write_disposition='WRITE_TRUNCATE')).result()
        print(f'{t:<18} {len(df):>6} filas subidas')
    con.close()
else:
    print('saltada')
'''),
        md('## 7. El mismo servidor, otro motor\n\nMismas siete llamadas. Debe responder lo mismo (salvo el campo `motor`).'),
        code('''
if HAY_BQ:
    resultados_bq = await ejecutar_casos(MCP_BACKEND='bigquery', GCP_PROJECT=GCP_PROJECT, BQ_DATASET=BQ_DATASET)
    for nombre, r in resultados_bq.items():
        print(f'--- {nombre}  [{r.get("motor", "?")}]')
        print(json.dumps(r, ensure_ascii=False, default=str)[:300])
else:
    print('saltada')
'''),
        md('''
## 8. ¿Dan lo mismo?

**Dos conectores que dan respuestas distintas no son dos conectores, son dos bugs.** La comprobación compara cada respuesta ignorando el motor, con una tolerancia de 0,01 en los decimales (los dos motores suman en otro orden).
'''),
        code('''
def igual(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(igual(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(igual(x, y) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return abs(a - b) <= 0.01
    return a == b

def sin_motor(r):
    r = json.loads(json.dumps(r, default=str))
    r.pop('motor', None)
    if r.get('tablas'):
        r['tablas'] = [dict(t) for t in r['tablas']]
    if r.get('columnas'):                       # los tipos se llaman distinto (INTEGER / INT64): se comparan solo los nombres
        r['columnas'] = [col['nombre'] for col in r['columnas']]
    if r.get('muestra') is not None:
        r['muestra'] = None
    return r

if HAY_BQ:
    for nombre in resultados_sqlite:
        ok = igual(sin_motor(resultados_sqlite[nombre]), sin_motor(resultados_bq[nombre]))
        print(f'{nombre:<20}', 'IGUAL' if ok else 'DISTINTO  <-- revisar')
        assert ok, nombre
    print('\\nLos dos conectores responden lo mismo.')
else:
    print('saltada')
'''),
        md('## 9. El tope de coste de BigQuery\n\nEn BigQuery se paga por bytes leídos. El servidor fija `maximum_bytes_billed`: si una consulta superara el tope, BigQuery **ni la ejecuta**. Lo forzamos con un tope absurdo de 1 byte.\n\n> **Truco:** BigQuery guarda en caché el resultado de una consulta repetida y esa respuesta **no se factura**, así que no pasaría por el tope. Por eso usamos una consulta que no hemos lanzado antes (`top_productos` con `n=7`). BigQuery responde que hacen falta al menos unos 20 MB (20 971 520 bytes): cobra por mínimos, no por bytes sueltos.'),
        code('''
if HAY_BQ:
    async with ClienteMCP(TRABAJO / 'mcp_datos.py', MCP_BACKEND='bigquery', GCP_PROJECT=GCP_PROJECT, BQ_DATASET=BQ_DATASET, MCP_BQ_MAX_BYTES=1) as c:
        r = await c.llamar('top_productos', n=7)
    print(r.get('error', r))
else:
    print('saltada')
'''),
        md('## 10. Limpiar\n\nSi subiste las tablas a BigQuery, bórralas: así no queda nada a tu nombre.'),
        code('''
BORRAR_DATASET = True
if HAY_BQ and BORRAR_DATASET:
    bq.delete_dataset(f'{GCP_PROJECT}.{BQ_DATASET}', delete_contents=True, not_found_ok=True)
    print(f'Dataset {BQ_DATASET} borrado.')
else:
    print('Nada que borrar' if not HAY_BQ else 'Dataset conservado (BORRAR_DATASET = False)')
'''),
        md('''
## 11. Conectar el servidor a un cliente de verdad

En VS Code (con GitHub Copilot en modo agente), un archivo `.vscode/mcp.json` en tu proyecto:

```json
{
  "servers": {
    "datos-master": {
      "type": "stdio",
      "command": "python",
      "args": ["01-Sesiones/S5-MLOps-y-Operacion/extra-mcp-notebooks/_trabajo/mcp_datos.py"],
      "env": { "CURSO_DB": "04-Proyecto-Base/data/processed/curso.db", "MCP_BACKEND": "sqlite" }
    }
  }
}
```

Para BigQuery cambia `MCP_BACKEND` por `bigquery` y añade `GCP_PROJECT` y `BQ_DATASET`. Pregúntale al agente «¿cuál es el país con más ventas?» y mira qué herramienta elige.

## Ejercicios

1. **Quita una capa.** Edita `validar_sql` para que acepte cualquier cosa y lanza `UPDATE master_clientes SET pais = 'X'`: ¿qué responde SQLite? (Debe fallar por ser de solo lectura.) Devuelve la vigilancia a su sitio.
2. **Añade una herramienta** `clientes_de_un_pais(pais, n)` con parámetros (nunca pegues el texto del país dentro del SQL: es lo que permite la inyección). Pruébala en los dos motores.
3. **Cambia el tope** `MAX_FILAS` a 5 y observa qué cambia en `consulta_sql`.
'''),
    ]


def nb02():
    return [
        md('''
# Extra de S5 · MCP en notebooks · 2. Un MCP con el modelo dentro

**Qué vas a construir:** un servidor MCP que lleva **el modelo de retención embebido**. Le pasas un número de cliente y devuelve la probabilidad de que **vuelva a comprar en los próximos 90 días**, con su tramo y una recomendación.

**Qué vas a aprender:**
- publicar un modelo de ML como *herramienta* de un LLM;
- que el MCP **no carga un archivo**, sino `models:/retencion-90d@champion`: lo que mande el alias en MLflow. Así un **rollback** cambia lo que responde, sin reiniciar nada;
- comprobar la **paridad**: lo que dice el MCP debe ser exactamente lo que da el modelo cargado a mano;
- qué hacer con los errores: cliente que no existe, variable que sobra, texto en vez de número.

> Ojo con la lectura: la probabilidad es de **volver a comprar**. Alta = buena noticia. No es un «riesgo de abandono».
'''),
        code(PREPARAR),
        md('''
## 1. El modelo que manda ahora

Cada entrenamiento registra una versión nueva en MLflow. El alias `champion` es un puntero a «la versión que manda». Si todavía no hay un `champion` (lo normal si aún no hiciste el laboratorio de MLOps), el notebook promueve la última versión para poder trabajar.
'''),
        code('''
sys.path.insert(0, str(PROYECTO))
from ia_mlops import alias_modelo as A, config
uri, mlc = A.conectar()
estado = A.estado(mlc)
CHAMPION_PUESTO_AQUI = 'champion' not in estado['alias']
if CHAMPION_PUESTO_AQUI:
    ultima = max(v['version'] for v in estado['versiones'])
    A.promover(mlc, ultima)
    print(f'No había @champion: lo he puesto en la v{ultima}.\\n')
print(A.texto_estado(A.estado(mlc)))
'''),
        md('''
## 2. El servidor

Qué mirar en el código:
- **`modelo_champion()`** pregunta a MLflow a qué versión apunta el alias **en cada llamada** y solo recarga si cambió (la carga es lo caro).
- **`predecir_cliente`** lee las 13 variables del cliente de `fs_produccion` (en solo lectura) y las pasa al modelo. El LLM nunca ve el modelo ni la base de datos.
- **`predecir_variables`** es el «¿y si...?»: un cliente inventado. Valida los nombres y los tipos antes de puntuar.
- **`por_que`** reparte la probabilidad entre las variables. Es exacto porque el modelo es una regresión logística: peso = coeficiente × valor transformado.
- **`tramo_de`** convierte la probabilidad en alta, media o baja con la regla de negocio de `config.py`. **Es una regla de negocio, no sale del modelo.**
'''),
        escribir_servidor('mcp_modelo.py'),
        md('## 3. El cliente\n\nLa misma clase que en el notebook 01.'),
        code(CLIENTE),
        md('## 4. Qué ofrece\n\nLas descripciones dicen cuándo usar cada herramienta y cuándo no.'),
        code('''
ENTORNO = dict(MCP_PROYECTO=PROYECTO, CURSO_DB=BD, CURSO_MLFLOW_URI=uri)
async with ClienteMCP(TRABAJO / 'mcp_modelo.py', **ENTORNO) as c:
    for h in await c.herramientas():
        print(f'• {h.name}\\n    {h.description}\\n')
'''),
        md('## 5. Predecir un cliente'),
        code('''
async with ClienteMCP(TRABAJO / 'mcp_modelo.py', **ENTORNO) as c:
    r = await c.llamar('predecir_cliente', cliente_id=12369)
    print(json.dumps({k: v for k, v in r.items() if k != 'variables'}, ensure_ascii=False, indent=2))
    print('\\nvariables que usó el modelo:', r['variables'])
    print('\\n--- ¿por qué?')
    p = await c.llamar('por_que', cliente_id=12369, n=4)
    for v in p['variables_que_mas_pesan']:
        print(f'  {v["variable"]:<18} valor {v["valor"]:<8} peso {v["peso_logit"]:+.3f}  → {v["efecto"]} la probabilidad')
    print(f'  intercepto {p["intercepto_logit"]:+.3f}  logit total {p["logit_total"]:+.3f}  →  probabilidad {p["probabilidad"]}')
    print('\\n--- el modelo en uso')
    print(await c.llamar('modelo_en_uso'))
'''),
        md('## 6. ¿Y si...? Un cliente inventado\n\nPartimos del cliente de ejemplo del proyecto y movemos **una sola variable**: la recencia (días desde su última compra). La intuición dice que cuanto más tiempo sin comprar, menos probable que vuelva. **¿Qué dice el modelo?**'),
        code('''
import pandas as pd
ejemplo = json.loads((PROYECTO / 'tests' / 'datos' / 'cliente_ejemplo.json').read_text(encoding='utf-8'))
filas = []
async with ClienteMCP(TRABAJO / 'mcp_modelo.py', **ENTORNO) as c:
    for dias in (5, 35, 90, 180, 365):
        r = await c.llamar('predecir_variables', variables={**ejemplo, 'recencia_dias': dias})
        filas.append({'recencia_dias': dias, 'probabilidad': r['probabilidad'], 'tramo': r['tramo']})
    parcial = await c.llamar('predecir_variables', variables={'recencia_dias': 10})
pd.DataFrame(filas)
'''),
        code('''
print('Con solo una variable:', parcial['probabilidad'], '-', parcial['aviso'][:90] + '…')
'''),
        md('''
**Sorpresa: la probabilidad SUBE con la recencia**, al revés que la intuición. No es un fallo del MCP (lo comprobamos en el apartado 7: da exactamente lo que da el modelo).
Es lo que el modelo aprendió con estos datos; **no es una relación causal**, y con una muestra de 150 clientes y variables muy relacionadas entre sí (recencia, antigüedad y frecuencia) un coeficiente suelto puede engañar.
Tampoco hemos comprobado aquí por qué ocurre. Es una buena pregunta para el análisis de tu tarea. Además, mover **una** variable cada vez no equivale a un cliente real, porque en un cliente real las variables se mueven juntas.
'''),
        md('## 7. Paridad: el MCP no inventa nada\n\nCargamos el modelo **a mano**, sin MCP, y puntuamos a los mismos clientes. Las probabilidades tienen que coincidir (el MCP redondea a 4 decimales).'),
        code('''
import mlflow.sklearn
modelo = mlflow.sklearn.load_model(f'models:/{config.MODELO_REGISTRADO}@champion')
con = sqlite3.connect(BD)
ids = [r[0] for r in con.execute('SELECT cliente_id FROM fs_produccion ORDER BY cliente_id LIMIT 12')]
X = pd.read_sql('SELECT * FROM fs_produccion WHERE cliente_id IN (%s)' % ','.join(map(str, ids)), con).set_index('cliente_id')
con.close()
directo = modelo.predict_proba(X.loc[ids, config.FEATURES].astype(float))[:, 1]

async with ClienteMCP(TRABAJO / 'mcp_modelo.py', **ENTORNO) as c:
    por_mcp = [(await c.llamar('predecir_cliente', cliente_id=i))['probabilidad'] for i in ids]

tabla = pd.DataFrame({'cliente_id': ids, 'a mano': directo.round(4), 'por MCP': por_mcp})
tabla['diferencia'] = (tabla['a mano'] - tabla['por MCP']).abs()
print(tabla.to_string(index=False))
assert tabla['diferencia'].max() < 1e-4
print('\\nParidad exacta: la diferencia máxima es', tabla['diferencia'].max())
'''),
        md('''
## 8. Rollback sin reiniciar

Esta es la parte MLOps. Con el servidor **arrancado**, movemos el alias `champion` a otra versión (como harías en un rollback) y volvemos a preguntar. El MCP responde con la versión nueva **sin que lo reinicies ni toques su código**.

> Honestidad: todas las versiones de este curso se entrenaron con los mismos datos, así que **dan la misma probabilidad**. Lo que cambia es la versión que responde; con modelos de verdad distintos cambiaría también la cifra.
'''),
        code('''
estado = A.estado(mlc)
actual = estado['alias']['champion']
otra = next(v['version'] for v in estado['versiones'] if v['version'] != actual)
async with ClienteMCP(TRABAJO / 'mcp_modelo.py', **ENTORNO) as c:
    antes = await c.llamar('predecir_cliente', cliente_id=12369)
    print(f'1. el MCP responde con la v{antes["version_modelo"]}: probabilidad {antes["probabilidad"]}')
    A.promover(mlc, otra)
    despues = await c.llamar('predecir_cliente', cliente_id=12369)
    print(f'2. promovemos @champion a la v{otra}, SIN reiniciar el MCP → responde la v{despues["version_modelo"]}: probabilidad {despues["probabilidad"]}')
    A.volver(mlc)
    vuelta = await c.llamar('predecir_cliente', cliente_id=12369)
    print(f'3. rollback (volver) → responde la v{vuelta["version_modelo"]}: probabilidad {vuelta["probabilidad"]}')
assert (antes['version_modelo'], despues['version_modelo'], vuelta['version_modelo']) == (actual, otra, actual)
'''),
        md('## 9. Cuando algo sale mal\n\nUn MCP bueno **no se rompe**: devuelve un error claro que el LLM puede contar al usuario. Prueba estas entradas.'),
        code('''
MALAS = [('cliente que no existe', 'predecir_cliente', {'cliente_id': 1}),
         ('texto en vez de número', 'predecir_cliente', {'cliente_id': 'abc'}),
         ('variable que el modelo no conoce', 'predecir_variables', {'variables': {'edad': 40}}),
         ('valor que no es número', 'predecir_variables', {'variables': {'frecuencia': 'muchas'}}),
         ('sin variables', 'predecir_variables', {'variables': {}})]
async with ClienteMCP(TRABAJO / 'mcp_modelo.py', **ENTORNO) as c:
    for nombre, herramienta, args in MALAS:
        r = await c.llamar(herramienta, **args)
        print(f'{nombre:<34} → {str(r.get("error") or r.get("error_del_protocolo"))[:110]}')
'''),
        md('''
## 10. Conectarlo a un cliente de verdad

```json
{
  "servers": {
    "modelo-retencion": {
      "type": "stdio",
      "command": "python",
      "args": ["01-Sesiones/S5-MLOps-y-Operacion/extra-mcp-notebooks/_trabajo/mcp_modelo.py"],
      "env": { "MCP_PROYECTO": "04-Proyecto-Base", "CURSO_DB": "04-Proyecto-Base/data/processed/curso.db" }
    }
  }
}
```

Con los **dos** servidores a la vez, un agente puede contestar «¿qué cliente del Reino Unido tiene más probabilidad de volver y cuánto ha comprado?»: una pregunta a `mcp-datos-master` y otra a `mcp-modelo-retencion`.

## Ejercicios

1. **Una herramienta nueva** `comparar_clientes(a, b)` que devuelva las dos probabilidades y cuál es mayor.
2. **Un límite:** haz que `predecir_variables` rechace una `recencia_dias` negativa. ¿Dónde pondrías esa regla: en el MCP o en el modelo?
3. **Pensar:** `predecir_cliente` solo ve el último lote (`fs_produccion`). ¿Qué cambiaría si calculase las variables al vuelo, como `puntuar_online` en S4?
'''),
        code('''
if CHAMPION_PUESTO_AQUI:
    print('Este notebook puso @champion al empezar. Si quieres dejar el registro como estaba:')
    print("  mlc.delete_registered_model_alias(config.MODELO_REGISTRADO, 'champion')")
'''),
    ]


def escribir(nombre, celdas, ejecutar=False):
    nb = nbf.v4.new_notebook()
    nb.cells = celdas
    nb.metadata['kernelspec'] = {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}
    if ejecutar:
        from nbclient import NotebookClient
        NotebookClient(nb, timeout=900, kernel_name='python3', resources={'metadata': {'path': str(AQUI)}}).execute()
    nbf.write(nb, AQUI / nombre)
    print('escrito', nombre, 'con salidas' if ejecutar else 'sin salidas')


if __name__ == '__main__':
    ejecutar = '--ejecutar' in sys.argv
    solo = [a for a in sys.argv[1:] if not a.startswith('--')]
    for nombre, f in zip(NOTEBOOKS, (nb00, nb01, nb02)):
        if not solo or nombre[:2] in solo:
            escribir(nombre, f(), ejecutar)
