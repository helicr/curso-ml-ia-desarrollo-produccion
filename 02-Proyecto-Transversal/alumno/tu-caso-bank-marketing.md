# Tu caso: Bank Marketing

Es el caso que desarrollas tú **de S1 a S5**, con la misma receta que el docente usa con Online Retail II: **RAW → MASTER → FS → ML → entrenamiento**, y después API, contenedor, GCP y workflow.
Esta hoja dice qué dato tienes, qué decisiones son tuyas y qué se entrega. Léela entera antes de S1.
La presentación [«Tu caso de S1 a S5»](../../01-Sesiones/S1-Datos-y-Entrenamiento/slides/caso-propio/index.html) resume lo mismo en 12 diapositivas.

> **Aquí no hay un modelo de referencia que alcanzar.** Lo que se evalúa es tu razonamiento, tus pruebas y que otra persona pueda repetir tu trabajo (ver [`rubrica-avance.md`](rubrica-avance.md)).

## 1. La pregunta
Un banco portugués llamó por teléfono a sus clientes para venderles un **depósito a plazo**, de mayo de 2008 a noviembre de 2010.

> **Antes de llamar a un cliente, ¿contratará el depósito a plazo?**

- Cada fila es **una llamada**. No hay identificador de cliente: no puedes agrupar por cliente ni saber si dos filas son la misma persona.
- El objetivo es la columna `y`: `yes` (contrató) o `no`.
- Solo puedes usar lo que se sabe **antes** de que el cliente conteste. Por eso **`duration` (la duración de la llamada) queda fuera del modelo**: ver el apartado 5.

## 2. El dato
- Archivo: `02-Proyecto-Transversal/datos/bank-marketing/bank-additional-full.csv` (separador `;`).
- Documentación del autor: `02-Proyecto-Transversal/datos/bank-marketing/bank-additional-names.txt`. **Léela entera.**
- Licencia **CC BY 4.0**: puedes usarlo citando la fuente (apartado 9).

Desde la raíz del repositorio, con el entorno `env-ia-mlops` activo, este comando lee el archivo:
```text
python -c "import pandas as pd; d = pd.read_csv('02-Proyecto-Transversal/datos/bank-marketing/bank-additional-full.csv', sep=';'); print(d.shape); print(d['y'].value_counts().to_dict())"
```
Debe imprimir:
```text
(41188, 21)
{'no': 36548, 'yes': 4640}
```
Para comprobar que tu copia es la original (desde la carpeta `02-Proyecto-Transversal/datos`; en PowerShell, `Get-FileHash -Algorithm SHA256 bank-marketing\bank-additional-full.csv` y compara con la línea de `SHA256SUMS`):
```text
sha256sum -c SHA256SUMS
```

**No hagas esto:**
- Abrirlo y guardarlo con Excel: cambia el archivo.
- Reordenar las filas: **el orden del archivo es la única información temporal** que tienes (está ordenado por fecha) y la necesitarás en S5.
- Editarlo a mano. Todo cambio se hace con código, sobre la copia de tu capa RAW.

## 3. Cifras para comprobar tu carga
Medidas sobre el archivo del repositorio. **Tu RAW debe cuadrar con ellas**: si no, algo falló en tu carga. Tu MASTER cambia según tus decisiones (si descartas filas idénticas, ya no tendrás 41 188 filas): lo que siempre debe cuadrar es `raw = master + descartes`.

| Qué | Valor |
|---|---|
| Filas · columnas | 41 188 · 21 (20 variables + `y`) |
| `y` = `yes` | 4 640 (11,27 %) |
| `y` = `no` | 36 548 |
| Filas idénticas a otra (en las 21 columnas) | 12 pares |
| Valores `unknown` | `job` 330 · `marital` 80 · `education` 1 731 · `default` 8 597 · `housing` 990 · `loan` 990 |
| `pdays` = 999 | 39 673 filas |
| `previous` > 0 y `pdays` = 999 a la vez | 4 110 filas |
| `poutcome` = `nonexistent` | 35 563 filas (son exactamente las de `previous` = 0) |
| Meses presentes | todos menos enero y febrero; no hay año ni fecha en ninguna columna |

Con un 11,27 % de síes, un modelo que **siempre** dijera «no» acertaría el 88,73 % de las veces. Por eso se mira el AUC y la precisión media, no solo la exactitud.

## 4. Las variables, en cuatro grupos
La clasificación es la del autor. **Ojo** señala lo que tendrás que decidir.

**Del cliente (7)**
- `age`: edad. **Ojo:** en este archivo va de 17 a 98.
- `job`: tipo de trabajo (12 categorías). **Ojo:** tiene `unknown`.
- `marital`: estado civil. **Ojo:** `divorced` incluye viudos, según el autor; tiene `unknown`.
- `education`: nivel de estudios (8 categorías). **Ojo:** tiene `unknown`.
- `default`: ¿tiene crédito en mora? **Ojo:** solo 3 `yes`; 8 597 `unknown`. Además, `default` es una palabra reservada de SQL: en una tabla se escribe entre comillas (`"default"`) o se renombra.
- `housing`: ¿tiene crédito de vivienda? **Ojo:** tiene `unknown`.
- `loan`: ¿tiene préstamo personal? **Ojo:** tiene `unknown`.

**Del último contacto (4)**
- `contact`: tipo de contacto, `cellular` o `telephone`.
- `month`: mes del último contacto. **Ojo:** sin año.
- `day_of_week`: día de la semana (lunes a viernes).
- `duration`: duración de la llamada, en segundos. **Ojo: queda fuera del modelo.**

**De campañas anteriores y de esta (4)**
- `campaign`: contactos de esta campaña con este cliente. **Ojo:** incluye la llamada actual.
- `pdays`: días desde el último contacto de una campaña anterior. **Ojo:** 999 es un código, no días.
- `previous`: contactos antes de esta campaña.
- `poutcome`: resultado de la campaña anterior: `failure`, `nonexistent` o `success`.

**Contexto económico (5)** (indicadores del país publicados por el Banco de Portugal; no son del cliente)
- `emp.var.rate`: variación del empleo (trimestral).
- `cons.price.idx`: índice de precios al consumo (mensual).
- `cons.conf.idx`: índice de confianza del consumidor (mensual).
- `euribor3m`: euríbor a 3 meses (diaria).
- `nr.employed`: número de empleados (trimestral).

**Objetivo:** `y`.

## 5. La trampa: `duration`
`duration` es la duración de la llamada. **Solo se conoce cuando la llamada termina**, y una llamada larga suele ser una llamada que acaba bien: usarla es decirle al modelo lo que quieres que adivine.
El propio autor lo advierte en `bank-additional-names.txt`: si la duración es 0, la respuesta es «no» (pasa en 4 filas de este archivo), y recomienda descartarla en un modelo realista.

Qué haces:
1. Déjala **fuera de FS y de ML**.
2. Escribe una **prueba** que falle si `duration` (o cualquier columna que no se conozca antes de llamar) vuelve a entrar en las variables del modelo. Es tu equivalente de la prueba «no futuro» del caso del docente.
3. Si algún día tu AUC te parece demasiado bueno, **sospecha de una fuga** antes de celebrarlo.

## 6. Decisiones que son tuyas
En cada una, deja escrito en tu avance qué hiciste, **por qué** y qué efecto tuvo (cuántas filas, cuánto cambian las métricas si lo pruebas).

| Decisión | Lo que hay en el archivo | Preguntas |
|---|---|---|
| **`unknown`** | seis columnas (apartado 3) | ¿Lo tratas como valor perdido, como una categoría más o descartas filas? ¿Es lo mismo en `default` (8 597) que en `marital` (80)? Si descartas filas, ya no evalúas sobre las mismas llamadas: piensa si puedes comparar las métricas con y sin ese descarte. |
| **Filas idénticas** | 12 pares, iguales en las 21 columnas (también en `duration`) | Sin identificador de cliente no se sabe si es la misma llamada repetida o dos llamadas distintas con los mismos valores. ¿Qué haces? Lo descartado debe quedar en una tabla de descartes, con su motivo, para que `raw = master + descartes`. |
| **`pdays` = 999 y `previous`** | 4 110 filas con `previous` > 0 y `pdays` = 999, aunque la documentación dice que 999 es «no contactado antes» | Un 999 tratado como días es un valor enorme que no significa lo que parece. ¿Cómo lo representas (por ejemplo, una variable «fue contactado antes» y los días solo cuando existen)? ¿Qué haces con esas 4 110 filas? |
| **`campaign`** | cuenta **incluida** la llamada actual | ¿Lo conoces antes de marcar el número? Si la usas, explica en qué sentido. |
| **Indicadores económicos** | trimestrales, mensuales y diarios | ¿Estaba publicado el valor cuando se hizo la llamada? ¿Qué pasa con ellos al partir los datos? |
| **`month` y `day_of_week`** | sin año ni fecha | ¿Cómo los codificas? Con el año ausente, `month` mezcla campañas de años distintos. |

## 7. Cómo se traduce a las capas
Parte de la estructura de `04-Proyecto-Base/` (mismas carpetas: `sql/`, `notebooks/`, paquete Python, `tests/`, `models/`, `reports/`; ver su `docs/modelo-de-datos.md`). Los nombres de tablas de la columna central son orientativos: si cambias alguno, sé coherente en todo el proyecto.
Si copias `04-Proyecto-Base/` para empezar, cambia el nombre del paquete **y el `name` de su `pyproject.toml`**: si no, al instalar tu copia en el mismo entorno (`pip install -e .`) sustituye a la instalación del original y `import ia_mlops` carga la tuya (comprobado con `uv pip install -e`).
En SQL, los nombres con punto (`"emp.var.rate"`) y `"default"` necesitan comillas dobles; MASTER los renombra para no arrastrar el problema.

| Capa | Qué haces con Bank Marketing | Tablas (orientativas) | Qué compruebas |
|---|---|---|---|
| **RAW** | Cargas el CSV **tal cual**, sin limpiar, con el **número de fila original** y la huella del archivo | `raw_llamadas`, `raw_carga` | 41 188 filas; 4 640 síes |
| **MASTER** | Tipos correctos, nombres de columna sin puntos (`emp.var.rate`, `cons.price.idx`, `cons.conf.idx`, `nr.employed`), tus decisiones sobre `unknown`, duplicados y `pdays`; reglas de calidad | `master_llamadas`, `master_descartes`, `master_calidad` | `raw = master + descartes`; categorías dentro de lo que dice la documentación |
| **FS** | Una fila por llamada con las variables **conocidas antes de llamar**, y su catálogo (descripción, fórmula, unidad y por qué se conoce antes) | `fs_llamada`, `fs_catalogo` | `duration` no está; la prueba lo vigila |
| **ML** | Objetivo (`y` a 1 y 0) y partición aleatoria estratificada, con semilla, guardada en una tabla | `ml_dataset`, `ml_particiones` | proporción de síes parecida en las tres particiones |
| **Entrenamiento** | Los tres modelos del caso del docente (referencia sin aprender, regresión logística y *gradient boosting*), con AUC y precisión media en validación y prueba, registrados en MLflow | `models/`, `reports/` | dos ejecuciones comparables; la elección se hace con validación |

La **huella** de cada capa (cuántas filas y de dónde vienen) es lo que te permite decir «este modelo se entrenó con estos datos».

## 8. La partición
- **De S1 a S4: aleatoria y estratificada.** La misma proporción de síes en entrenamiento, validación y prueba, con una semilla fija y guardada. **Es optimista, y debes dejarlo escrito**: probablemente, porque las llamadas de una misma época se parecen y quedan repartidas entre entrenamiento y prueba. Una diferencia pequeña entre dos modelos o dos ejecuciones puede ser solo azar de la partición: si vas a decidir con ella, repite con otra semilla y anótalo.
- **En S5: el mismo modelo, evaluado por orden de filas** (las primeras para entrenar, las últimas para probar). Compara con lo anterior y explica la diferencia; empieza por mirar qué proporción de síes hay en cada tramo. No hace falta antes: si lo pruebas por tu cuenta, anótalo como exploración.

## 9. Qué se entrega y cuándo
Las sesiones son los **miércoles y viernes, de 10:00 a 14:00 (hora de Perú)**: S0 el miércoles 11 de noviembre, S1 el viernes 13, S2 el miércoles 18, S3 el viernes 20, S4 el miércoles 25 y S5 el viernes 27.

Cada avance se presenta en la **sesión siguiente** a aquella en la que se trabaja y se entrega **antes de que empiece: a las 10:00 (hora de Perú) de ese día**. Entre S1 y S2 y entre S3 y S4 hay cinco días; entre S2 y S3 y entre S4 y S5, solo dos, así que los avances 2 y 4 conviene empezarlos en cuanto termina la sesión. Se entrega rellenando el **formulario de Google del curso** (el instructor da el enlace en clase), una vez por avance: tu nombre, el número de avance, el enlace a tu rama o a tu carpeta comprimida y «qué no pude ejecutar». La hora de entrega es la que marca el formulario.

| Avance | Se trabaja en | Se presenta en | Entrega, a más tardar | Qué lleva |
|---|---|---|---|---|
| **1** | S1 y trabajo autónomo | S2 | mié 18 nov, 10:00 | Capas RAW → MASTER → FS → ML, entrenamiento y métricas, **como cuadernos** |
| **2** | S2 y trabajo autónomo | S3 | vie 20 nov, 10:00 | El pipeline **ya en Python** (la traducción de los cuadernos), API, contenedor y pruebas. **La Ruta B de la tarea de S2 es este avance** |
| **3** | S3 y trabajo autónomo | S4 | mié 25 nov, 10:00 | Migración a GCP y despliegue: inventario, datos migrados y validados, servicio desplegado y registros. Opcional: módulo neuronal |
| **4** | S4 y trabajo autónomo | S5 | vie 27 nov, 10:00 | Pipeline orquestado con GitHub Actions: workflow funcionando, historial de ejecuciones y una decisión explicada |
| **Final** | tras S5 | por definir | vie 11 dic, 10:00 | Repositorio, informe y demostración, con la evaluación por orden de filas de S5 |

Las tareas de cada sesión (por ejemplo, la de S1: añadir una variable al caso Online Retail II) son un ejercicio aparte de estos avances, salvo la Ruta B de S2.
Cada avance se entrega con [`plantilla-avance.md`](plantilla-avance.md) completada y se evalúa con [`rubrica-avance.md`](rubrica-avance.md). Entrégalo en tu repositorio personal, con una rama por avance (`avance-1`, `avance-2`…), o en una carpeta comprimida si no hay repositorio. Si tu repositorio es privado, añade al instructor como colaborador antes de entregar (su usuario lo indica en clase); si entregas una carpeta comprimida, súbela a tu nube y comparte el enlace con acceso para quien lo tenga. Para crear ramas y subirlas: [`git-y-ramas.md`](../../07-Recursos/guias/git-y-ramas.md).

## 10. Reglas
- **Cita la fuente** (la licencia la exige):
  - Moro, S., Rita, P., & Cortez, P. (2014). *Bank Marketing* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5K306
  - La documentación del autor pide además citar: S. Moro, P. Cortez y P. Rita, *A Data-Driven Approach to Predict the Success of Bank Telemarketing*, Decision Support Systems (2014), doi:10.1016/j.dss.2014.03.001.
  - Si cambias el dato (limpiar, renombrar), indícalo.
- No subas claves, tokens ni credenciales al repositorio.
- **No se evalúa solo con capturas**: entrega código, pruebas y pasos que otra persona pueda ejecutar.
- Declara lo que **no** pudiste ejecutar y el error exacto, y cita la ayuda que recibiste (personas y herramientas).

## Antes de S1
- [ ] La huella de mi copia es correcta (`sha256sum -c SHA256SUMS`).
- [ ] El comando de lectura imprime `(41188, 21)`.
- [ ] He leído `bank-additional-names.txt` entera.
- [ ] Puedo explicar por qué `duration` queda fuera.
- [ ] Sé qué decisiones son mías (apartado 6) y qué se entrega en cada avance (apartado 9).

**Documentos relacionados:** [`plantilla-avance.md`](plantilla-avance.md) · [`rubrica-avance.md`](rubrica-avance.md) · [presentación](../../01-Sesiones/S1-Datos-y-Entrenamiento/slides/caso-propio/index.html) · [datos](../datos/LEEME.md)
