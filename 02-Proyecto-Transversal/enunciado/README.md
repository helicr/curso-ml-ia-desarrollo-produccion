# Caso transversal: retención de clientes con Online Retail II (caso del instructor; el de los alumnos es Bank Marketing)

**Decisión del 09/11/2026:** el caso del instructor es **Online Retail II** (UCI, CC BY 4.0). Es didáctico y comprensible: una tienda online, clientes que compran
y vuelven, y una pregunta que cualquiera entiende.

> **Dado un cliente y una fecha de corte, ¿volverá a comprar en los 90 días siguientes?**

Por qué este caso: tiene dimensión temporal (permite una partición sin fuga), el dato original trae suciedad real que justifica cada capa
(duplicados, cancelaciones, códigos que no son productos, clientes nulos), cabe en un portátil y se explica sin estadística.
Todo el detalle está en `04-Proyecto-Base/` (README, `docs/modelo-de-datos.md`, cuadernos y paquete `ia_mlops`).

## Cómo se trabaja
El docente demuestra el caso con los **cinco cuadernos-pipeline** (00 a 04; el 00 simula la base operacional de la que se ingiere); el asistente reproduce y adapta **otro de estructura similar** (la tarea).
Cada avance presenta: resultado, ejecución, pruebas, una decisión, dificultades y pasos reproducibles.

## Entregas
Siguen el programa vigente (`00-Planificacion/programa.md`). Cada avance se presenta en la sesión siguiente.
1. **S1 → avance en S2:** capas RAW → MASTER → FS → ML, entrenamiento y métricas del caso de la tarea, **como cuadernos**.
2. **S2 → avance en S3:** API y contenedor. Aquí el pipeline ya es **Python**: la traducción de los cuadernos al paquete.
3. **S3 → avance en S4:** migración a GCP y despliegue. Opcional: módulo neuronal.
4. **S4 → avance en S5:** pipeline orquestado con GitHub Actions.
5. Repositorio e informe finales (posterior a S5).

Además, la tarea de cada sesión adapta el caso del instructor (por ejemplo, la de S1 añade una variable a Online Retail II y se decide con evidencia): es un ejercicio aparte de este avance.

## La tarea de los alumnos: caso propio (decidido el 09/11/2026)
Repetir la receta (RAW → MASTER → FS → ML → entrenamiento, con cuadernos, su traducción a `.py`, seguimiento en MLflow y pruebas) sobre **otro dataset** de estructura similar,
y llevarlo después a API, contenedor, GCP y workflow. El alumno trabaja con **uno de estos dos datasets de UCI** (licencia **CC BY 4.0**, leída en las fichas oficiales).
Las cifras de la tabla están **medidas** con los archivos que adjuntó el instructor (`../verificacion-datos-tarea/`).

| | **Default of Credit Card Clients** | **Bank Marketing** |
|---|---|---|
| Qué es | Clientes de tarjeta de crédito de un banco de Taiwán, abril–septiembre de 2005 | Llamadas de venta de un depósito a plazo de un banco portugués, mayo de 2008 a noviembre de 2010 |
| Pregunta | ¿Impagará el cliente el mes siguiente? | ¿Contratará el cliente el depósito a plazo? |
| Archivo | `default of credit card clients.xls` (5,3 MB): 30 000 filas, `ID` + 23 variables + objetivo, con **dos filas de encabezado** | `bank-additional-full.csv` (en `bank-additional.zip`, 434 KB): 41 188 filas, 20 variables + objetivo, separador `;` |
| Objetivo | 22,12 % de impagos (6 636 de 30 000) | 11,27 % de «sí» (4 640 de 41 188) |
| Entidad | El cliente | La llamada (no hay identificador de cliente: no se puede agregar por cliente) |
| Corte | Septiembre de 2005 (único): seis meses de estado de pago, factura y pago, y el objetivo es el mes siguiente | No hay columna de fecha, solo mes y día de la semana; el archivo está **ordenado por fecha**, con meses ausentes, y trae indicadores económicos (euribor a 3 meses, etc.) |
| Partición | Aleatoria y estratificada (un solo corte: no hay deriva temporal que mostrar) | Por orden de filas hay una **deriva extrema** (síes: 5,6 % en entrenamiento y 38,5 % en prueba). Aleatoria funciona mejor, pero probablemente es optimista porque filas de la misma época se parecen |
| Lo que obliga a MASTER | Encabezado doble; 35 duplicados exactos (sin `ID`); `EDUCATION` con 0, 5 y 6 (345 clientes) y `MARRIAGE` con 0 (54); `PAY_*` con −2 y 0; facturas negativas (590–688 por mes); formato ancho → largo; `PAY_0` sin `PAY_1` | «unknown» en `default` (8 597), `education` (1 731), `housing` y `loan` (990), `job` (330) y `marital` (80); 12 duplicados exactos; `pdays`=999 (39 673 filas) como «sin contacto previo»; `bank-additional.zip` trae basura de macOS y un `.Rhistory` |
| Variables de FS | Del pasado: utilización del límite, meses en retraso, retraso máximo, pago sobre factura, tendencia de la factura | `pdays`, `previous`, `poutcome` y las del cliente; las de la campaña, con cuidado |
| La trampa | Pocas: es el más sencillo | `duration` (duración de la llamada) **no se conoce antes de llamar**. La documentación del propio zip (`bank-additional-names.txt`) dice que debe descartarse en un modelo realista. La ficha de UCI no lo advierte |

Es la misma estructura que el caso del instructor: una entidad, un corte, un objetivo hacia el futuro y variables calculadas **solo con el pasado**.

### Lo medido con un modelo base rápido
Una partición y una semilla (0), sin afinar: orden de magnitud, no solución de referencia. AUC en validación / prueba.

| Default of Credit Card Clients (aleatoria estratificada 70/15/15) | Valid | Test |
|---|---|---|
| Regresión logística, variables originales | 0,720 | 0,709 |
| Boosting, variables originales | 0,792 | 0,761 |
| Regresión logística + 6 variables de FS | 0,762 | 0,733 |
| Boosting + 6 variables de FS | 0,794 | 0,763 |

| Bank Marketing (AUC en prueba) | Orden de filas | Aleatoria |
|---|---|---|
| Con `duration` (logística / boosting) | 0,652 / 0,697 | 0,935 / 0,950 |
| Sin `duration` (logística / boosting) | 0,577 / 0,514 | 0,787 / 0,804 |

Lecturas: en Default, las variables de FS mejoran la logística (+0,02 a +0,04) y casi no cambian el boosting, un buen caso de «decide con evidencia».
En Bank Marketing, `duration` infla el AUC en unos 0,15, y la partición por orden de filas hunde el modelo hasta el azar (0,51 con boosting): es deriva real y un ejemplo excelente para S5, pero **mal primer modelo** para S1.

### Reglas
- Citar la fuente (obligatorio por la licencia): Yeh, I. (2009). *Default of Credit Card Clients* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C55S3H · Moro, S., Rita, P., & Cortez, P. (2014). *Bank Marketing* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5K306.
  La documentación del zip de Bank Marketing pide además citar a Moro, Cortez y Rita (2014), *A Data-Driven Approach to Predict the Success of Bank Telemarketing*, Decision Support Systems, doi:10.1016/j.dss.2014.03.001.
- Los filtros usan solo datos anteriores al corte; la prueba de «no futuro» debe seguir en verde.
- No publicar datos sensibles ni secretos. No evaluar solo mediante capturas.

### Estado (leer antes de impartir)
- **Hecho:** licencias leídas en las fichas oficiales; archivos recibidos, perfilados y con sha256; modelo base rápido (`../verificacion-datos-tarea/`).
- **No hecho:** base de referencia (RAW → MASTER → FS → ML con cuadernos y pruebas), script de descarga. La copia de los datos ya está en `../datos/` (ver su `LEEME.md`).
- **Hallazgo:** el `.xls` de Default **no se puede leer con `env-ia-mlops`**, que no trae `xlrd`. Se entrega ya convertido a CSV (`../datos/default-credit-card/`); queda decidir si se añade `xlrd` al entorno.
- **Decidido el 09/11/2026:** el caso de los alumnos es Bank Marketing y Default queda como referencia (`../datos/LEEME.md`); la comparación de arriba se conserva como contexto. **Por decidir:** las fechas de los avances. Ver `00-Planificacion/decisiones-y-pendientes.md` (puntos 15 a 18).
