# SQLite: guía y chuleta

**Se usa en:** S0 (comprobar que el visor funciona) y S1 (el pipeline completo vive en una base SQLite). En S3 esas tablas se migran a BigQuery.

## Para qué sirve
SQLite es una base de datos **dentro de un solo archivo** (`.db`). No hay servidor que instalar ni usuario o contraseña: abres el archivo y ya puedes lanzar SQL.
En el curso hace de **«on-premise simulado»**: el pipeline RAW → MASTER → FS → ML escribe sus tablas en `04-Proyecto-Base/data/processed/curso.db`.

Tres ideas:
- **El archivo es la base.** Copiarlo es hacer una copia de seguridad; borrarlo es perderla.
- Es SQL estándar, con particularidades: tipos flexibles (`INTEGER`, `REAL`, `TEXT`, `BLOB`), las **fechas se guardan como texto ISO** (`2011-06-01`) y las **claves foráneas están desactivadas** salvo que ejecutes `PRAGMA foreign_keys = ON;` en cada conexión (el paquete `ia_mlops` ya lo hace).
- Si abres un archivo que no existe, SQLite **crea uno vacío en silencio**. Un `no such table` suele significar «abrí otro archivo».

## Dónde lanzar SQL: cuatro sitios
| Dónde | Para qué | Cómo |
|---|---|---|
| **DB Browser for SQLite** (visual) | Explorar tablas, ver datos, probar consultas. Es el visor de referencia del curso | Se instala con el script de S0. Menú Inicio → *DB Browser for SQLite* |
| **`sqlite3`** (línea de comandos) | Consultas rápidas, scripts `.sql`, importar y exportar CSV | Viene en el entorno `env-ia-mlops` (con el entorno activo: `sqlite3 --version`) |
| **Python** (`sqlite3` + `pandas`) | Usar los resultados en código y cuadernos | `import sqlite3` |
| **Extensión de VS Code** (opcional) | Ver tablas sin salir del editor | `qwtel.sqlite-viewer` (explorar) o `alexcvzz.vscode-sqlite` (consultas) |

El cliente `sqlite3` del entorno se comprobó en Linux; en Windows debería quedar disponible al activar el entorno, pero no se ha verificado.

### Obtener la base del curso
`curso.db` **no está en el repositorio** (se regenera). Créala con la muestra incluida (unos 7 segundos):
```text
conda activate env-ia-mlops
cd 04-Proyecto-Base
pip install -e .
python -m ia_mlops.pipeline
```
Después tendrás `data\processed\curso.db`. Borrarla y volver a ejecutar el pipeline la deja como nueva.

### Comprobación de S0 (checklist 7)
En cualquiera de los cuatro sitios, la consulta debe devolver una fila con un `1`:
```sql
SELECT 1 AS entorno_listo;
```
En DB Browser: *New Database* (o abre `curso.db`) → pestaña *Execute SQL* → escribe la consulta → `Ctrl+Intro` o `F5`.

## DB Browser for SQLite (visual)
Barra superior: **New Database**, **Open Database**, **Write Changes** y **Revert Changes**. Cuatro pestañas:
| Pestaña | Para qué |
|---|---|
| *Database Structure* | Tablas, columnas, índices. Clic derecho en una tabla → copiar la sentencia `CREATE` |
| *Browse Data* | Ver y filtrar filas como en una hoja de cálculo |
| *Edit Pragmas* | Ajustes de la base (claves foráneas, etc.) |
| *Execute SQL* | Escribir y ejecutar SQL. Si seleccionas un texto, solo se ejecuta la selección |

**Importante:** DB Browser **no guarda solo**. Después de cambiar datos o estructura, pulsa **Write Changes** (`Ctrl+S`); *Revert Changes* descarta lo pendiente.
Para mirar sin riesgo, ábrela solo lectura: *File → Open Database Read Only*. Si Python escribe a la vez que DB Browser tiene cambios sin guardar, verás `database is locked`.
Importar CSV: *File → Import → Table from CSV file…* · Exportar: *File → Export → Table(s) as CSV file…*.

## Crear una base de datos y tablas
La base se crea al abrirla por primera vez:
```text
sqlite3 mi.db
```
```sql
CREATE TABLE cliente (
    cliente_id INTEGER PRIMARY KEY,
    nombre     TEXT NOT NULL,
    pais       TEXT
);
CREATE TABLE pedido (
    pedido_id  INTEGER PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES cliente(cliente_id),
    fecha      TEXT NOT NULL,                 -- ISO: 2026-11-09
    importe    REAL CHECK (importe >= 0)
);
```
En DB Browser: *New Database* → asistente *Create Table*, o pega el `CREATE TABLE` en *Execute SQL*.
Lo habitual es guardar el SQL en un archivo `.sql` y ejecutarlo: `.read crear.sql` dentro de `sqlite3` (es lo mismo que hace el repositorio con `04-Proyecto-Base/sql/`).

## Lo básico de SQL
```sql
INSERT INTO cliente (cliente_id, nombre, pais) VALUES (1, 'Ana', 'Peru');
INSERT INTO pedido (cliente_id, fecha, importe) VALUES (1, '2026-11-01', 120.5), (1, '2026-11-05', 80);

UPDATE pedido SET importe = 100 WHERE pedido_id = 2;     -- sin WHERE cambia TODAS las filas
DELETE FROM pedido WHERE pedido_id = 3;                  -- sin WHERE borra TODAS las filas

SELECT c.nombre, COUNT(*) AS pedidos, SUM(p.importe) AS total
FROM cliente c
JOIN pedido p USING (cliente_id)
WHERE p.fecha >= '2026-11-01'
GROUP BY c.cliente_id
ORDER BY total DESC
LIMIT 10;
```
Las restricciones protegen los datos: con `PRAGMA foreign_keys = ON;`, insertar un pedido de un cliente inexistente da `FOREIGN KEY constraint failed`, y un importe negativo da `CHECK constraint failed`.
Fechas: `date('2011-06-01', '+90 days')` suma días; `strftime('%Y-%m', fecha)` extrae año y mes.

## Chuleta de `sqlite3`
Los comandos que empiezan por **punto** son del cliente (no llevan `;`); las sentencias SQL sí.
| Quiero... | Comando |
|---|---|
| Abrir (o crear) una base | `sqlite3 data/processed/curso.db` |
| Ver las tablas | `.tables` |
| Ver cómo se creó una tabla | `.schema ml_particiones` |
| Ver sus columnas con tipos | `PRAGMA table_info(ml_dataset);` |
| Ver los índices | `.indexes` |
| Ver encabezados y columnas alineadas | `.headers on` y `.mode column` (otras: `.mode box`, `.mode csv`) |
| Ejecutar un archivo SQL | `.read crear.sql` |
| Importar un CSV a una tabla | `.mode csv` y `.import --skip 1 clientes.csv cliente` |
| Mandar el resultado a un archivo | `.output salida.csv` (y `.output stdout` para volver) |
| Volcar la base o una tabla a SQL | `.dump` · `.dump cliente` |
| Hacer una copia de seguridad | `.backup copia.db` |
| Ver el plan de una consulta | `EXPLAIN QUERY PLAN SELECT ...;` |
| Ayuda / salir | `.help` / `.quit` |

Consultas sin entrar en el cliente, útiles en scripts:
```text
sqlite3 -header -column data/processed/curso.db "SELECT COUNT(*) AS filas FROM raw_online_retail_ii;"
sqlite3 -header -csv data/processed/curso.db "SELECT * FROM ml_particiones;" > particiones.csv
```
**Windows:** CMD y PowerShell no entienden `sqlite3 mi.db < crear.sql` igual que Linux (PowerShell no admite `<`). Entra con `sqlite3 mi.db` y usa `.read crear.sql`.

## Desde Python
```python
import sqlite3
import pandas as pd

# Leer: la base del curso (se regenera, no escribas en ella)
con = sqlite3.connect("data/processed/curso.db")
con.execute("PRAGMA foreign_keys = ON")          # hay que activarlo en CADA conexión
filas = con.execute("SELECT particion, COUNT(*) FROM ml_dataset GROUP BY particion").fetchall()
df = pd.read_sql("SELECT * FROM fs_catalogo", con)    # consulta -> DataFrame
con.close()

# Escribir: en una base propia
mi = sqlite3.connect("mi.db")
mi.execute("CREATE TABLE IF NOT EXISTS nota (id INTEGER PRIMARY KEY, texto TEXT)")
df.to_sql("copia_catalogo", mi, if_exists="replace", index=False)    # DataFrame -> tabla
mi.execute("INSERT INTO nota (texto) VALUES (?)", ("hola",))         # usa ? y parámetros, nunca f-strings con datos
mi.commit()                                       # sin commit() no se guarda
mi.close()
```
El proyecto ya trae utilidades en `ia_mlops/db.py` (`conectar`, `ejecutar_script`, `escalar`) y la ruta de la base en `ia_mlops/config.py` (`CURSO_DB` la cambia).

## Las tablas del caso (`curso.db`)
Prefijos por capa. Detalle y diagrama en `04-Proyecto-Base/docs/modelo-de-datos.md`.
| Capa | Tablas |
|---|---|
| RAW | `raw_online_retail_ii`, `raw_carga` |
| MASTER | `master_clientes`, `master_productos`, `master_facturas`, `master_lineas`, `master_descartes`, `master_calidad` |
| FS | `fs_cliente_corte`, `fs_catalogo` |
| ML | `ml_dataset`, `ml_particiones` |

**No edites estas tablas a mano:** cada capa se regenera desde la anterior con el pipeline.

### Consultas para probar (con la muestra)
```sql
-- ¿Cuánto hay en cada capa?
SELECT COUNT(*) FROM raw_online_retail_ii;      -- 23 070
SELECT COUNT(*) FROM master_lineas;             -- 22 117
SELECT COUNT(*) FROM master_descartes;          --    953   (23 070 = 22 117 + 953)

-- Tasa de recompra por partición
SELECT particion, COUNT(*) AS filas, ROUND(100.0 * AVG(y), 1) AS tasa_pct
FROM ml_dataset GROUP BY particion ORDER BY MIN(fecha_corte);
-- train 626 · 50,8   valid 114 · 45,6   test 250 · 40,4

-- Países con más clientes
SELECT pais, COUNT(*) AS clientes FROM master_clientes GROUP BY pais ORDER BY clientes DESC LIMIT 5;

-- Los tres clientes que más han gastado (solo ventas válidas)
SELECT f.cliente_id, ROUND(SUM(l.monto_linea), 2) AS gasto
FROM master_facturas f JOIN master_lineas l ON l.factura_id = f.factura_id
WHERE l.es_venta_valida = 1
GROUP BY f.cliente_id ORDER BY gasto DESC LIMIT 3;

-- ¿Qué variables existen y qué significan?
SELECT * FROM fs_catalogo;
```
Con el dato **completo** (`python -m ia_mlops.pipeline --fuente completo`) las cifras son otras: es esperado.

## Errores frecuentes
| Mensaje o síntoma | Causa y solución |
|---|---|
| `no such table: ...` | Abriste otro archivo (SQLite creó uno vacío) o aún no ejecutaste el pipeline. Comprueba la ruta y `.tables`. |
| `database is locked` | Otro programa tiene la base con cambios sin guardar. Pulsa *Write Changes* o cierra DB Browser y reintenta. |
| Mis cambios no están al reabrir | En DB Browser faltó *Write Changes*; en Python faltó `con.commit()`. |
| `FOREIGN KEY constraint failed` | Intentas referenciar un registro que no existe. Es la restricción haciendo su trabajo. |
| `CHECK constraint failed` | El valor incumple la regla de la columna (por ejemplo, importe negativo). |
| `near "...": syntax error` | Falta una coma, un paréntesis o el `;` entre sentencias. Revisa la línea que indica. |
| Las fechas no ordenan o comparan bien | No están en formato ISO `AAAA-MM-DD`. En SQLite son texto: el formato importa. |

## Para S3: diferencias con BigQuery
Orientación, no tabla completa: BigQuery separa proyecto, conjunto de datos y tabla (`proyecto.dataset.tabla`); tiene tipos `DATE`/`TIMESTAMP` reales (en SQLite son texto); sus funciones de fecha son otras (`DATE_ADD`, `FORMAT_DATE`, en lugar de `date()`/`strftime`); y cobra por datos leídos, no por tiempo.
La migración y las validaciones de conteos y esquemas se tratan en `03-Entorno/guias/migracion-on-premise-a-gcp.md`.

## Qué se probó y qué no
Con **SQLite 3.54 en Linux** (09/11/2026), sobre la base real generada con la muestra: todas las consultas de «Consultas para probar» (las cifras de los comentarios son las obtenidas, y coinciden con `01-Sesiones/S1-Datos-y-Entrenamiento/practica/guia-laboratorio.md`);
crear una base y tablas con un script, importar un CSV, `INSERT`/`UPDATE`/`DELETE`/`JOIN`, los fallos de `FOREIGN KEY` y `CHECK`, `.dump`, `.backup`, `.indexes`, `EXPLAIN QUERY PLAN`, exportar a CSV, y el código de Python (`sqlite3`, `pandas.read_sql` y `to_sql`).
**No se probó** DB Browser for SQLite (es una aplicación de escritorio): sus pestañas, botones y atajos se tomaron de su documentación pública y de tutoriales. Tampoco `sqlite3` ni el script `.sql` en Windows, ni las dos extensiones de VS Code (solo se comprobó que existen con esos IDs).
