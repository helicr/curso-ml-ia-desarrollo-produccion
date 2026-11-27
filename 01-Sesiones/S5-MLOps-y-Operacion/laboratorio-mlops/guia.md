# Laboratorio de MLOps clásico de S5: deriva, alias y alertas

Sobre el mismo caso del curso (retención a 90 días, Online Retail II) vas a hacer lo que hace un equipo de MLOps cada día con un modelo que **ya está en producción**: **medir si los datos o el modelo han cambiado**, **cambiar de versión y volver atrás sin miedo** y **dejar que GitHub avise** cuando algo se mueve. Sin claves, sin Google Cloud y sin coste por llamada.

> **El mensaje de la sesión:** un modelo en producción **se vigila, se versiona y se puede deshacer**. La alerta es el **rojo** de un run y un *issue*: sin él, nadie se entera.

Presentación: [`index.html`](index.html) (cada orden se copia con **⧉**). Workflow listo para copiar: [`monitoreo.yml`](monitoreo.yml).

| Laboratorio | Qué haces | Qué te llevas |
|---|---|---|
| **L1** · Deriva de datos | `deriva cortes` y `deriva datos`: PSI y KS de las 13 variables | El modelo **no avisa solo** de que los datos han cambiado |
| **L2** · Deriva de rendimiento | `deriva rendimiento`: el AUC por corte | Se mide **tarde**, y **medir con datos de entrenamiento engaña** |
| **L3** · Versionar y volver atrás | `alias_modelo`: una v2 distinta, `promover` y `volver` | Un alias es un **puntero**: deshacer es moverlo |
| **L4** · Alertas con GitHub Actions | El workflow `monitoreo.yml` y dos ramas de ensayo | La alerta **es el rojo** y un *issue* |
| **L5** · Costes y orden | Lo de S4: presupuesto y borrado | Avisar no es cortar; lo que creas, lo borras |

> **Estado de validación.** Todo lo de **L1 a L3** (las órdenes y las salidas de «Qué debes ver») se ejecutó el **26/11/2026** sobre una copia de ensayo del proyecto, en **Windows** con Python 3.11 y la muestra de 150 clientes: las cifras son reales. **Sin verificar:** las mismas órdenes **en un Codespace (Linux)**; **todo lo de GitHub Actions** (los dos runs, el *issue*, el comentario del segundo run y el permiso `issues: write`), cuyas capturas están **pendientes**; el tiempo de `--fuente completo` en un Codespace (**437 s** en el ensayo) y los minutos de Actions (**sin dato**). Del workflow sí se comprobó **en local**: YAML, permisos, órdenes y opciones, `bash -n` de cada paso, que el escenario `estable` da **salida 0** y el `deriva` **salida 1** sobre los datos reales, y que el resumen y el cuerpo del *issue* se generan bien.

> **Orden:** haz **L1 y L2 antes que L3**. L3 entrena una v2 con los **datos completos** y tu base local deja de ser la de la muestra, así que los números de L1 y L2 cambiarían. Al final de L3 se explica cómo volver a la muestra.

> **Si usas Windows (cmd o PowerShell 5.1) en vez del Codespace:** `&&` no existe y `;` no se usa para encadenar; en lugar de `echo "salida: $?"` usa `echo $LASTEXITCODE` (PowerShell) o `echo %ERRORLEVEL%` (cmd); `rm` es `del`, `cp` es `copy` y `mkdir -p` es `mkdir`. Las órdenes `python -m …` son iguales.

---

## 0. Piezas y palabras

| Palabra | Qué significa aquí |
|---|---|
| **Corte** | Una fecha para la que se calculan las 13 variables de cada cliente (la «foto» de ese día). El **«ahora»** es el día siguiente a la última factura: 2011-12-10 |
| **Deriva de datos** | Los clientes de hoy ya no se parecen a los de entrenamiento. Se mide **sin etiqueta**, solo con los datos |
| **Deriva de rendimiento** | El modelo acierta menos que antes (el **AUC** cae). Necesita la **etiqueta**, que llega 90 días tarde |
| **PSI** | *Population Stability Index*: cuánto cambia el reparto de una variable. Menos de 0,10 «estable», de 0,10 a 0,25 «moderado», más de 0,25 «cambio importante». Es una **convención del oficio, no una ley** |
| **KS** | Estadístico de Kolmogórov y Smirnov: distancia máxima entre dos distribuciones (0 = iguales, 1 = totalmente separadas) |
| **Alias** `champion` | Un puntero con nombre a una **versión** del modelo en MLflow: «la que manda». Cambiar de modelo es mover el puntero |
| ***Issue*** | Una incidencia abierta en el repositorio de GitHub (pestaña **Issues**): aquí, el aviso de la alerta |
| ***schedule*** | El disparador de GitHub Actions que lanza un workflow a una hora fija (*cron*). En un *fork* viene **desactivado** |

Todas las órdenes de L1 a L3 son de **solo lectura sobre los datos** (`deriva` no escribe nada en la base ni en el registro) salvo `alias_modelo promover` y `volver`, que mueven un alias, y el pipeline del paso 2 de L3.

---

## 1. Preparar el entorno (una vez)

Terminal **bash** del Codespace (o de tu portátil), en tu *fork* del repositorio del curso, **desde `04-Proyecto-Base`**:

```bash
cd 04-Proyecto-Base
python -m pip install -r requirements-dev.txt
python -m ia_mlops.operacional
python -m ia_mlops.pipeline
```

El pipeline deja la base analítica (`data/processed/curso.db`), el modelo (`models/`) y **registra la versión 1** de `retencion-90d` en MLflow.

**Qué debes ver.** Sin errores. `OPERACIONAL: clientes 150 filas` … `lineas_factura 23,070 filas`; los cuatro pipelines con su tiempo; la comparación de modelos con `regresion_logistica   AUC valid 0.698 | test 0.747`; y al final:

```text
  Mejor modelo: regresion_logistica. Guardado en …/models/modelo.joblib
  Registrado en MLflow como «retencion-90d», version 1. Para verlo: python -m ia_mlops.mlflow_ui
```

Tarda unos 30 s en un portátil (el ensayo: 32 s). Con un Codespace nuevo verás «version 1»; si ya habías ejecutado el pipeline con `--forzar`, tendrás más versiones: usa **tus** números.

**Si falla.**
- **`No module named ia_mlops`:** no estás en `04-Proyecto-Base` (comprueba con `pwd`).
- **Windows con conda:** `0xc06d007f` al importar `scikit-learn` significa que falta `<entorno>\Library\bin` en el `PATH`: activa el entorno con `conda activate`.

---

## 2. L1 · Deriva de datos

### 2.1 Qué es y por qué el modelo no avisa solo

Un modelo **no se rompe**: sigue devolviendo una probabilidad para cualquier entrada. **No avisa** de que sus entradas ya no se parecen a las del entrenamiento. Por eso alguien tiene que **medirlo**: elegir un **corte de referencia** (el último de entrenamiento) y otro **actual**, y comparar cada una de las 13 variables con **PSI** y **KS**. No hace falta la etiqueta, así que se puede hacer **hoy**. Los datos del corte actual se calculan **al vuelo** con el mismo SQL de la capa FS que usó el entrenamiento, para que la comparación sea justa.

### 2.2 Los cortes guardados

```bash
python -m ia_mlops.deriva cortes
```

**Qué debes ver** (salida 0):

```text
Cortes guardados en fs_cliente_corte (10):
  2010-06-01     69 clientes  partición train  etiqueta a 90 días: sí
  2010-07-01     80 clientes  partición train  etiqueta a 90 días: sí
  2010-08-01     84 clientes  partición train  etiqueta a 90 días: sí
  2010-09-01     88 clientes  partición train  etiqueta a 90 días: sí
  2010-10-01     93 clientes  partición train  etiqueta a 90 días: sí
  2010-11-01    103 clientes  partición train  etiqueta a 90 días: sí
  2010-12-01    109 clientes  partición train  etiqueta a 90 días: sí
  2011-03-01    114 clientes  partición valid  etiqueta a 90 días: sí
  2011-06-01    119 clientes  partición test   etiqueta a 90 días: sí
  2011-09-01    131 clientes  partición test   etiqueta a 90 días: sí
Corte «ahora» (día siguiente a la última factura): 2011-12-10
```

Diez cortes de **69 a 131 clientes**: siete de **entrenamiento** (`train`), 2011-03-01 de **validación** y los dos últimos de **prueba** (`test`). Esa columna importará en L2.

**Si falla.** Sale 2 y un mensaje de error: falta ejecutar el pipeline (apartado 1).

### 2.3 Deriva de datos con datos reales

```bash
python -m ia_mlops.deriva datos --referencia 2010-12-01 --actual 2011-12-10
echo "salida: $?"
```

**Qué debes ver:**

```text
Deriva de datos: referencia 2010-12-01 (109 clientes, fs_cliente_corte) frente a actual 2011-12-10 (148 clientes, calculado al vuelo)
PSI con 10 intervalos por cuantiles de la referencia (suelo 0.0001); umbral de alarma 0.25.
Los umbrales de PSI (0,10 y 0,25) son una convención de la industria, no una ley.

variable                        PSI      KS  estado
antiguedad_dias               2.830   0.736  deriva  <-- supera el umbral
recencia_dias                 0.437   0.259  deriva  <-- supera el umbral
frecuencia_180d               0.400   0.240  deriva  <-- supera el umbral
monto_90d                     0.293   0.213  deriva  <-- supera el umbral
frecuencia_90d                0.276   0.213  deriva  <-- supera el umbral
unidades_total                0.147   0.122  moderada
frecuencia                    0.137   0.145  moderada
dias_medios_entre_compras     0.115   0.128  moderada
productos_distintos           0.107   0.124  moderada
monto_total                   0.097   0.138  estable
devoluciones                  0.018   0.064  estable
ticket_medio                  0.012   0.064  estable
es_reino_unido                0.000   0.010  estable

DERIVA: 5 de 13 variables superan el umbral (antiguedad_dias, recencia_dias, frecuencia_180d, monto_90d, frecuencia_90d).
Ojo: con 109 clientes el PSI oscila por azar; es un aviso, no una sentencia.
salida: 1
```

- **Salida 1** = hay deriva (**0** = sin deriva, **2** = error). Un workflow puede decidir con ese número.
- **5 de 13** variables superan 0,25. Las mayores: `antiguedad_dias` (PSI **2,830**, KS 0,736), `recencia_dias` (0,437), `frecuencia_180d` (0,400), `monto_90d` (0,293) y `frecuencia_90d` (0,276). Las más bajas: `es_reino_unido` (0,000), `ticket_medio` (0,012) y `devoluciones` (0,018).
- **Lectura honesta:** `antiguedad_dias` crece para **todos** los clientes con solo dejar pasar un año: su PSI enorme es **esperable** y no pide por sí solo reentrenar. Las de **actividad reciente** (`recencia_dias`, `frecuencia_90d`, `frecuencia_180d`, `monto_90d`) sí dicen que el comportamiento cambió.

**Si falla.** `Error: La referencia «2010-12-1» no tiene la forma AAAA-MM-DD (por ejemplo 2011-12-10).` (salida 2): escribe la fecha con ceros, `2010-12-01`.

### 2.4 Cómo leer PSI y KS

`PSI = suma de (q − p) · ln(q / p)`, con **p** = fracción de clientes de la referencia en cada intervalo y **q** = la del corte actual. Los intervalos salen de los **cuantiles de la referencia**. Un ejemplo que cabe en la mano, con la referencia `[1, 2, 3, 4]` y el corte actual `[1, 1, 1, 4]`, dos intervalos (la mediana de la referencia, 2,5, los separa):

| intervalo | referencia (p) | actual (q) | aporte `(q − p) · ln(q / p)` |
|---|---|---|---|
| hasta 2,5 | 0,50 | 0,75 | 0,1014 |
| más de 2,5 | 0,50 | 0,25 | 0,1733 |
| nulo | 0,0001 | 0,0001 | 0,0000 |
| **PSI** | | | **0,2747** |

```bash
python -c "from ia_mlops import deriva; print(round(deriva.psi_detalle([1, 2, 3, 4], [1, 1, 1, 4], intervalos=2)['psi'], 4))"
```

**Qué debes ver:** `0.2747`.

- **Los umbrales son una convención del oficio, no una ley:** menos de **0,10** estable, de **0,10 a 0,25** moderado, más de **0,25** cambio importante. `--umbral-psi` deja cambiar el de alarma.
- **Suelo anti-cero:** `ln(q / p)` no existe si un intervalo está vacío, así que las fracciones menores que **0,0001** se suben a 0,0001. Es un parche numérico, no una teoría. El intervalo «nulo» existe para que el PSI cambie si de repente faltan datos.
- Con la **misma** muestra en los dos lados el PSI es exactamente **0**.
- El **KS** mira la distancia máxima entre las dos distribuciones **acumuladas**: 0 iguales, 1 separadas del todo.
- Con pocos clientes (aquí 109 y 148) el PSI oscila por azar: es un aviso, no una sentencia.

### 2.5 Ejercicio: otro par de cortes y otro umbral

```bash
python -m ia_mlops.deriva datos --referencia 2010-08-01 --actual 2010-09-01
echo "salida: $?"
python -m ia_mlops.deriva datos --referencia 2010-08-01 --actual 2010-09-01 --umbral-psi 0.5
echo "salida: $?"
python -m ia_mlops.deriva datos --referencia 2010-12-01 --actual 2011-12-10 --json reports/datos.json
python -c "import json; d = json.load(open('reports/datos.json', encoding='utf-8')); print(d['hay_deriva'], d['superan_umbral'])"
```

**Qué debes ver** (recortado):

```text
variable                        PSI      KS  estado
antiguedad_dias               0.410   0.261  deriva  <-- supera el umbral
recencia_dias                 0.228   0.175  moderada
monto_90d                     0.092   0.106  estable
...
DERIVA: 1 de 13 variables superan el umbral (antiguedad_dias).
salida: 1
```

y, con `--umbral-psi 0.5`:

```text
umbral de alarma 0.5.
variable                        PSI      KS  estado
antiguedad_dias               0.410   0.261  moderada
recencia_dias                 0.228   0.175  moderada
...
Sin deriva relevante: ninguna variable supera el umbral.
salida: 0
```

La última orden imprime `True ['antiguedad_dias', 'recencia_dias', 'frecuencia_180d', 'monto_90d', 'frecuencia_90d']`: así lo lee un workflow.

La **misma medición** da salida 1 con 0,25 y salida 0 con 0,5: cambió la **convención**, no los datos. Y un dato honesto: en esta muestra **ninguna de las 45 parejas de cortes** da salida 0 con el umbral 0,25 (se probaron todas): siempre hay alguna variable, casi siempre `antiguedad_dias`, que lo supera. Esa pareja (agosto→septiembre de 2010) con el umbral 0,5 es el escenario `estable` de L4. Prueba tú otros pares con `cortes`.

---

## 3. L2 · Deriva de rendimiento

### 3.1 Por qué se mide tarde

El modelo predice la probabilidad de que el cliente **vuelva a comprar en los próximos 90 días**. La **etiqueta** («¿compró?») solo se conoce **cuando pasan esos 90 días**. Mientras tanto solo puedes mirar la deriva de datos (L1). Por eso se **miran las dos**: la de datos avisa **pronto** (pero puede ser falsa alarma); la de rendimiento confirma **tarde**. El corte 2011-12-10 aparece como «sin etiqueta»: el corte + 90 días se sale de los datos.

### 3.2 El AUC por corte

```bash
python -m ia_mlops.deriva rendimiento --cortes 2011-03-01 2011-06-01 2011-09-01
echo "salida: $?"
```

**Qué debes ver** (salida 0):

```text
AUC del modelo en producción por corte (caída = AUC del primer corte medido, 2011-03-01, menos el de este corte; positiva = empeora; tolerancia 0.05). La tolerancia por defecto (0,05) es provisional: no sale de ninguna medición.

corte       uso                        clientes positivos      AUC    caída
2011-03-01  validación                      114        52   0.6982  +0.0000
2011-06-01  prueba                          119        46   0.7534  -0.0552
2011-09-01  prueba                          131        55   0.7423  -0.0441

AVISO: El corte 2011-03-01 es de entrenamiento o validación: el modelo se ajustó o se eligió con él y el AUC ahí SOBREESTIMA. Para una medida honesta usa cortes de prueba o posteriores al entrenamiento.
Sin deriva de rendimiento relevante.
salida: 0
```

AUC **0,6982** (validación, 114 clientes), **0,7534** (prueba, 119) y **0,7423** (prueba, 131). La caída es **negativa**: el AUC **mejora** frente al primer corte, así que la orden no se alarma. La **tolerancia** de 0,05 es **provisional**: no sale de ninguna medición.

**Si falla.** Sale 2 y un mensaje de error: falta el modelo; ejecuta `python -m ia_mlops.pipeline` (apartado 1).

### 3.3 La lección: medir con datos de entrenamiento engaña

```bash
python -m ia_mlops.deriva rendimiento --cortes 2010-12-01 2011-03-01 2011-06-01 2011-09-01
echo "salida: $?"
```

**Qué debes ver** (salida 1, recortado):

```text
corte       uso                        clientes positivos      AUC    caída
2010-12-01  entrenamiento                   109        41   0.8497  +0.0000
2011-03-01  validación                      114        52   0.6982  +0.1515
2011-06-01  prueba                          119        46   0.7534  +0.0963
2011-09-01  prueba                          131        55   0.7423  +0.1074

AVISO: Los cortes 2010-12-01, 2011-03-01 son de entrenamiento o validación: el modelo se ajustó o se eligió con ellos y el AUC ahí SOBREESTIMA. [...]
AVISO: El AUC cae 0.1515 respecto al primer corte medido (2010-12-01), más que la tolerancia de 0.05. Si ese primer corte es de entrenamiento, parte de la caída es sobreajuste y no deriva.
DERIVA DE RENDIMIENTO: sí.
salida: 1
```

El AUC en **entrenamiento** (2010-12-01) es **0,8497** y en validación **0,6982**: la «caída» de **0,1515** es en parte **sobreajuste**. **El modelo no ha cambiado**; solo lo medimos con datos que ya había visto. **La lección importante:** medir el rendimiento con datos de entrenamiento **engaña**; para una medida honesta, usa cortes de **prueba** o posteriores.

---

## 4. L3 · Versionar y volver atrás con alias

Cada entrenamiento registra una **versión** nueva de `retencion-90d` en MLflow. Un **alias** es un puntero con nombre a una versión: `champion` = «la que manda». **Cambiar de modelo es mover el puntero; deshacer es volver a moverlo. No se borra nada.**

### 4.1 Mostrar, promover y cargar

```bash
python -m ia_mlops.alias_modelo mostrar
python -m ia_mlops.alias_modelo promover --version 1
python -m ia_mlops.alias_modelo cargar
```

**Qué debes ver** (la primera línea, «Almacén de MLflow: …», es tu ruta):

```text
Modelo registrado «retencion-90d»: 1 versiones
  v1   alias: -            valid_auc 0.6982 · test_auc 0.7471
Alias: ninguno

@champion -> v1 (no había champion anterior: no se guardó a dónde volver).

Cargado models:/retencion-90d@champion -> versión 1
Probabilidad de comprar en 90 días del cliente de cliente_ejemplo.json: 0.8279
```

Cada orden imprime también la línea del almacén. Con **tres versiones idénticas** del mismo modelo, `cargar` da siempre 0,8279: el cambio de alias **no se notaría** en la probabilidad. Por eso el siguiente paso entrena una v2 **distinta**.

**Si falla.** `Error: No existe la versión 9 de «retencion-90d»: mira cuáles hay con  python -m ia_mlops.alias_modelo mostrar` (salida 2): pediste una versión que no está; `mostrar` te dice cuáles hay.

### 4.2 Una v2 que sea de verdad otra: los datos completos

El Excel completo de Online Retail II **no está en el repositorio** (pesa unos 45 MB): se baja de UCI y se verifica su huella.

```bash
python -m ia_mlops.dataset descargar
python -m ia_mlops.pipeline --fuente completo
```

> **Paciencia:** el segundo comando tardó **437 s** (más de 7 minutos) en el portátil del ensayo (rehace la base con 1,07 millones de filas, reentrena y registra la v2). En un Codespace: **sin verificar**. Después de esto, tu base y tu modelo locales **ya no son los de la muestra**.

**Qué debes ver.** `descargar`: `sha256: 572e36277c2390fbfde10664750731e0a86f55e33470d91919085f0408e67bfb` y `Listo: …/online_retail_II.xlsx`. El pipeline (recortado):

```text
  OPERACIONAL: clientes             5,942 filas
  OPERACIONAL: lineas_factura   1,067,371 filas
  ...
  ML: train  23,760 filas | tasa de recompra 48.1 %
  ML: valid   4,512 filas | tasa de recompra 35.1 %
  ML: test   10,132 filas | tasa de recompra 38.0 %
  regresion_logistica        AUC valid 0.786 | test 0.796 | precision media test 0.735
  ...
  Registrado en MLflow como «retencion-90d», version 2.
```

Y `python -m ia_mlops.alias_modelo mostrar` enseña ahora **dos** versiones: v1 con `valid_auc 0.6982 · test_auc 0.7471` y v2 con `valid_auc 0.7855 · test_auc 0.7956`. La v2 tiene otra **huella de datos** (`3521a0421905ba28`) que la v1 (`35a94deb4e04ab4a`).

### 4.3 Mover el puntero: promover la v2

```bash
python -m ia_mlops.alias_modelo promover --version 2
python -m ia_mlops.alias_modelo cargar
```

**Qué debes ver:**

```text
@champion: v1 -> v2. La v2 recuerda a la v1: para volver, `volver`. No se ha borrado nada.

Cargado models:/retencion-90d@champion -> versión 2
Probabilidad de comprar en 90 días del cliente de cliente_ejemplo.json: 0.7245
```

El mismo comando `cargar` da ahora **0.7245** (con la v1 daba **0.8279**): el alias decide qué modelo se sirve y esta vez **se nota**. `promover` guarda en la v2 una etiqueta `champion_anterior = 1`, que es lo que lee `volver`.

### 4.4 Volver atrás

```bash
python -m ia_mlops.alias_modelo volver
python -m ia_mlops.alias_modelo cargar
python -m ia_mlops.alias_modelo mostrar
```

**Qué debes ver:**

```text
Rollback: @champion: v2 -> v1. La v2 sigue registrada; no se ha borrado nada.

Cargado models:/retencion-90d@champion -> versión 1
Probabilidad de comprar en 90 días del cliente de cliente_ejemplo.json: 0.8279

Modelo registrado «retencion-90d»: 2 versiones
  v1   alias: @champion    valid_auc 0.6982 · test_auc 0.7471
  v2   alias: -            valid_auc 0.7855 · test_auc 0.7956  (champion anterior: v1)
Alias: @champion -> v1
```

**Un alias es un puntero: deshacer es moverlo, no se borra nada.** La v2 sigue registrada, con sus métricas y su modelo.

**Si falla.** Si repites `volver`: `Error: La versión 1, que es @champion, no guardó una versión anterior: no hay a dónde volver. Si sabes cuál quieres, usa  promover --version N` (salida 2). Para ir a otra versión, `promover --version N`.

### 4.5 Lo que el alias gobierna y lo que no

El alias gobierna el **registro** de MLflow y a **cualquiera que cargue** `models:/retencion-90d@champion`. **No gobierna** la imagen Docker de la API: copia `models/modelo_mlflow` al construirse y **no lee el registro**, así que mover `champion` **no cambia** lo que responde la API ya desplegada. Un sistema real lo uniría así (aquí **no se implementa**):

1. Al mover el alias, un paso del workflow **exporta la versión champion** a `models/modelo_mlflow`.
2. Construye y publica la imagen con **la versión en su etiqueta**.
3. La despliega (o hace que la API **cargue por alias al arrancar**).

### 4.6 Volver a la muestra (si quieres repetir L1 y L2)

Tras 4.2 tu base local es la completa. Bórrala y rehaz la de la muestra, **en este orden**:

```bash
rm data/processed/curso.db
python -m ia_mlops.pipeline --fuente muestra
```

Registrará una **v3** idéntica a la v1 (AUC `0.6982` / `0.7471`) y **el alias no se mueve**. Con ello `deriva rendimiento` vuelve a dar `0.6982`, `0.7534` y `0.7423`.

**Si falla.** Si lanzas `--fuente muestra` **sin** borrar antes `curso.db`, falla con `R03_integridad_referencial: Violaciones de claves foráneas` (visto en el ensayo): quedan tablas de los datos completos. Borra `curso.db` y repite. **Sin verificar:** todo este apartado en un Codespace.

---

## 5. L4 · Alertas con GitHub Actions

### 5.1 El workflow

[`monitoreo.yml`](monitoreo.yml) hace lo mismo que L1 y L2, pero cada día y sin que nadie mire:

| Trabajo | Qué hace |
|---|---|
| **1 · Preparar datos y modelo** | Reconstruye la base operacional y entrena el modelo desde la muestra (`operacional` + `pipeline`), como `puntuar-lote.yml` de S4. Sube `models/` y `curso.db` como artefacto |
| **2 · Deriva de datos y de rendimiento** | Elige el escenario, lanza `deriva datos` y `deriva rendimiento` con `--json`, escribe el **resumen** con la tabla de PSI y sube los JSON. Los códigos de salida 0 y 1 **no** rompen el paso: un 1 es un resultado, un 2 sí es un error |
| **3 · Alerta** | Solo si algún código fue **1**: **abre un *issue*** con la etiqueta `alerta-deriva` (o comenta el que ya hay abierto) y **termina el run en ROJO** |

| Disparador | Cuándo | Qué mide |
|---|---|---|
| `schedule` | cada día a las **05:23 UTC** (un minuto «raro»: a las horas en punto GitHub va cargado y puede retrasarlo) | referencia 2010-12-01 frente al «ahora». En un *fork* viene **desactivado** |
| `workflow_dispatch` | a mano, con `referencia`, `actual` y `umbral_psi` | lo que escribas |
| `push` a `lab/monitoreo/**` | el **nombre de la rama** elige el escenario | `lab/monitoreo/estable` y `lab/monitoreo/deriva` |

**Seguridad:** sin secretos propios (solo el `GITHUB_TOKEN` de cada run); `contents: read` en todo y **`issues: write` solo en el trabajo de alerta**. El trabajo de alerta **no hace *checkout***, así que lleva `working-directory: .` (si no, heredaría la carpeta `04-Proyecto-Base` y fallaría: lección real de S4).

### 5.2 Copiarlo y subirlo

Terminal **bash**, en la **raíz del repositorio** (sal de `04-Proyecto-Base`):

```bash
cd ..
git switch develop
git pull
git switch -c lab/mlops-s5
mkdir -p .github/workflows
cp 01-Sesiones/S5-MLOps-y-Operacion/laboratorio-mlops/monitoreo.yml .github/workflows/
git add .github/workflows
git commit -m "Laboratorio de MLOps clásico de S5: workflow de monitoreo"
git push -u origin lab/mlops-s5
```

**Qué debes ver.** En la pestaña **Actions** de tu *fork*, a la izquierda, **«Monitoreo del modelo»**. Este push **no lanza el workflow**: `lab/mlops-s5` no es una rama de ensayo. **`Run workflow` solo aparece si el archivo está en la rama por defecto**; por eso los ensayos usan ramas. En un *fork*, antes, acepta el aviso para **activar las Actions**. La configuración del repositorio es la de S4 ([`CONFIGURAR-REPOSITORIO.md`](../laboratorio-agentes/CONFIGURAR-REPOSITORIO.md) remite a ella); aquí **no** hace falta el *environment* `produccion`, porque no hay despliegue.

**Si falla.** `git push` da 403: el gestor de credenciales tiene otra cuenta de GitHub (`git-credential-manager github login`). No aparece el workflow: comprueba que el archivo está en `.github/workflows/` de la rama y que activaste las Actions.

### 5.3 Escenario «estable»: nada que avisar

```bash
git switch lab/mlops-s5
git switch -c lab/monitoreo/estable
git push -u origin lab/monitoreo/estable
```

**Qué se espera ver** (**sin verificar en Actions** hasta que el profesor lo ensaye; **captura pendiente** `m-01-estable-verde`): los trabajos 1 y 2 en **verde** y el 3 **omitido** (gris). Mide la pareja **2010-08-01 → 2010-09-01** con umbral **0,50**: `antiguedad_dias` (0,410) queda «moderada» y la salida de `deriva datos` es **0** (**comprobado en local**). El resumen dice **«Sin alerta»** y enseña el AUC por corte (0.6982, 0.7534, 0.7423) (**captura pendiente** `m-02-resumen-estable`). **No se abre ningún *issue*.**

> **Honestidad:** «estable» **no** es «sin cambios»: es un par de cortes cercano **y un umbral más laxo**. Con 0,25 también habría alertado (apartado 2.5).

### 5.4 Escenario «deriva»: el rojo

```bash
git switch lab/mlops-s5
git switch -c lab/monitoreo/deriva
git push -u origin lab/monitoreo/deriva
```

**Qué se espera ver** (**sin verificar en Actions**; **capturas pendientes** `m-03-deriva-rojo` y `m-04-resumen-deriva`): los trabajos 1 y 2 en **verde** y el **3 · Alerta en ROJO**. Mide **2010-12-01 frente a 2011-12-10** con umbral **0,25**: la misma medición de L1, **salida 1**, **5 de 13** variables. El resumen dice **«ALERTA»** y marca las cinco variables con «**supera el umbral**» (PSI 2.830, 0.437, 0.400, 0.293 y 0.276). **La alerta es el rojo**: sin él, nadie se entera.

**Si falla.** `Rama de ensayo desconocida: …`: el nombre de la rama no es `lab/monitoreo/estable` ni `lab/monitoreo/deriva`; el workflow lo rechaza a propósito para que un error al teclear no pase en silencio.

### 5.5 El *issue* de alerta

Se espera (**sin verificar en Actions**; **captura pendiente** `m-05-issue-alerta`) un *issue* nuevo en la pestaña **Issues**, con la etiqueta **`alerta-deriva`** (se crea sola si no existe), de título **«Alerta de deriva: 5 variables superan el PSI 0.25 (referencia 2010-12-01, actual 2011-12-10)»** y un cuerpo con la tabla de las cinco variables (PSI y KS), el **enlace al run** y qué hacer. **Sin verificar:** que `gh issue create` funcione con solo `issues: write`.

**Qué hacer con una alerta:** abre el run, lee el resumen y decide si la deriva es **esperable** (`antiguedad_dias`) o **de comportamiento** (`recencia_dias`, `frecuencia_90d`…). Si el AUC de cortes de **prueba** cae, reentrena y promueve la versión nueva con alias (L3); si sale mal, `volver`.

### 5.6 Repetir el run: ningún *issue* nuevo

En la página del run, **Re-run all jobs**. Se espera (**sin verificar en Actions**; **captura pendiente** `m-06-segunda-alerta`) que el trabajo 3 **comente** en el *issue* ya abierto («Nueva medición con deriva») y **no abra otro**: una deriva que sigue ahí no llena la lista; hay **una alerta abierta** hasta que alguien la cierre.

**Si falla.** `gh: Resource not accessible by integration` (**sin verificar**): faltan permisos de escritura de *issues*; en **Settings › Actions › General** comprueba los permisos del workflow.

### 5.7 Al terminar, limpia

1. **Cierra** el *issue* (botón *Close issue*).
2. Borra las dos ramas de ensayo:

```bash
git push origin --delete lab/monitoreo/estable
git push origin --delete lab/monitoreo/deriva
```

3. **Desactiva el workflow** en Actions (**«Monitoreo del modelo» › «···» › Disable workflow**): con los datos congelados del curso, el *schedule* diario avisaría **siempre**.

---

## 6. L5 · Costes y orden

Este laboratorio **no usa la nube de pago**. L1 a L3 usan tu **Codespace** (lo que ya tengas incluido en tu cuenta de GitHub) y L4 usa **minutos de GitHub Actions** (gratis en repositorios públicos; en uno privado cuentan contra tu cuota; los minutos exactos del workflow: **sin dato** hasta el ensayo del profesor). Lo que creas y **se borra**: las ramas `lab/monitoreo/*`, el *issue*, la etiqueta `alerta-deriva` y el workflow, desactivado.

De Google Cloud (S4), **sin repetirlo**: un **presupuesto** con alertas (en S4, 20 € al 50, 90 y 100 %) **avisa, no corta nada**; lo que más cobra si se olvida es lo que **sigue encendido** (un clúster, un endpoint) y se **borra** con los scripts de borrado, siempre. Guía completa: [Laboratorio Cloud Journey](../../S4-Orquestacion-y-CI-CD/laboratorio-cloud-journey/guia.md) (`01-Sesiones/S4-Orquestacion-y-CI-CD/laboratorio-cloud-journey/guia.md`).

**Dos reglas del oficio:** un aviso que nadie lee **no protege** (por eso la alerta es un rojo y un *issue*), y **lo que creas, lo borras**.

---

## 7. Si algo falla: casos

| Síntoma | Causa | Qué hacer | ¿Visto? |
|---|---|---|---|
| `No module named ia_mlops` | No estás en `04-Proyecto-Base` | `cd 04-Proyecto-Base` | previsto |
| `Error: La referencia «2010-12-1» no tiene la forma AAAA-MM-DD` | Fecha sin ceros (salida 2) | Escribe `2010-12-01` | sí (26/11) |
| `deriva` sale 1 con casi cualquier pareja de cortes | `antiguedad_dias` siempre crece con el tiempo | Léela como esperable; compara con `--umbral-psi` | sí (26/11) |
| `rendimiento` con un corte de entrenamiento da **salida 1** | El AUC en entrenamiento sobreestima | Empieza por un corte de **prueba** (L2) | sí (26/11) |
| `volver`: «no hay a dónde volver» (2) | Esa versión no guardó anterior | `promover --version N` | sí (26/11) |
| `--fuente muestra` falla con `R03_integridad_referencial` | Quedan tablas de los datos completos | `rm data/processed/curso.db` y repetir | sí (26/11) |
| `gh: Resource not accessible by integration` en la alerta | Falta permiso de escritura de *issues* | Revisa los permisos del workflow y de Actions | sin verificar |
| El *schedule* no corre | En un *fork* viene desactivado y solo corre en la rama por defecto | Actívalo en Actions o usa `workflow_dispatch` | previsto |

---

## 8. Qué se comprobó de verdad y qué falta

**Comprobado el 26/11/2026** (copia de ensayo, Windows, Python 3.11): `cortes`, `datos` (salida 1, 5 de 13), `rendimiento` (salidas 0 y 1); la v2 con datos completos (AUC de test **0.7956** frente a **0.7471**), `promover`, `cargar` (**0.7245** y **0.8279**) y `volver`; el workflow (YAML, permisos, órdenes y opciones, `bash -n`, escenarios `estable` → 0 y `deriva` → 1 sobre los datos reales, resumen y cuerpo del *issue*).

**Sin verificar o sin dato:**
- **Todo lo de GitHub Actions**: los dos runs, el *issue*, el comentario del segundo run y los permisos (`issues: write`). Las capturas `m-01` a `m-06` están **pendientes**.
- Las órdenes **en un Codespace** (Linux): se ejecutaron en Windows.
- El tiempo de `--fuente completo` en un Codespace (**437 s** en el ensayo) y los minutos de Actions: **sin dato**.
- Un **umbral de PSI** o una **tolerancia de AUC** razonables para el negocio: son convenciones, no salen de ninguna medición.
