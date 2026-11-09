# Caso transversal: retención de clientes con Online Retail II

**Decisión del 09/11/2026:** el caso del instructor es **Online Retail II** (UCI, CC BY 4.0). Es didáctico y comprensible: una tienda online, clientes que compran
y vuelven, y una pregunta que cualquiera entiende.

> **Dado un cliente y una fecha de corte, ¿volverá a comprar en los 90 días siguientes?**

Por qué este caso: tiene dimensión temporal (permite una partición sin fuga), el dato original trae suciedad real que justifica cada capa
(duplicados, cancelaciones, códigos que no son productos, clientes nulos), cabe en un portátil y se explica sin estadística.
Todo el detalle está en `04-Proyecto-Base/` (README, `docs/modelo-de-datos.md`, cuadernos y paquete `ia_mlops`).

## Cómo se trabaja
El docente demuestra el caso con los **cuatro cuadernos-pipeline**; el asistente reproduce y adapta **otro de estructura similar** (la tarea).
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
y llevarlo después a API, contenedor, GCP y workflow. El alumno trabaja con **uno de estos dos datasets de UCI** (licencia **CC BY 4.0**, leída en las fichas oficiales):

| | **Default of Credit Card Clients** | **Bank Marketing** |
|---|---|---|
| Qué es | Clientes de tarjeta de crédito de un banco de Taiwán, abril–septiembre de 2005 | Llamadas de venta de un depósito a plazo de un banco portugués, mayo de 2008 a noviembre de 2010 |
| Pregunta | ¿Impagará el cliente el mes siguiente? | ¿Contratará el cliente el depósito a plazo? |
| Tamaño | 30 000 clientes, 23 variables, un archivo `.xls` (5,3 MB) | 41 188 filas y 20 variables (`bank-additional-full.csv`, en `bank-additional.zip`, 434 KB) |
| Entidad | El cliente | La llamada (no hay identificador de cliente: no se puede agregar por cliente) |
| Corte | Septiembre de 2005 (único): seis meses de estado de pago, factura y pago, y el objetivo es el mes siguiente | No hay columna de fecha, solo mes y día de la semana; el archivo viene **ordenado por fecha** |
| Partición | Aleatoria y estratificada (hay un solo corte, así que no hay deriva temporal que mostrar) | Por orden de filas: lo más antiguo para entrenar, lo más reciente para validar y probar |
| Lo que obliga a MASTER | Pasar de formato ancho (un mes por columna) a largo (cliente × mes); nombres irregulares (`PAY_0`, `PAY_2`… sin `PAY_1`); categorías por perfilar | Categorías con «unknown» y definiciones que la ficha cuenta de dos formas (`education`, `contact`) |
| Variables de FS | Del pasado: utilización del límite, meses en retraso, retraso máximo, tendencia de pagos, pago sobre factura | `pdays`, `previous`, `poutcome` y las del cliente; el resto de la campaña, con cuidado |
| La trampa | Pocas: es el más sencillo | `duration` (duración de la llamada) **no se conoce antes de llamar**: la regla de oro obliga a excluirla. La ficha de UCI no lo advierte; comprobarlo en la documentación que viene dentro del zip |

Es la misma estructura que el caso del instructor: una entidad, un corte, un objetivo hacia el futuro y variables calculadas **solo con el pasado**.
**Default** es el camino más corto (un archivo, una fila por cliente); **Bank Marketing** es más delicado (fuga de datos y partición por orden).

### Reglas
- Citar la fuente (obligatorio por la licencia): Yeh, I. (2009). *Default of Credit Card Clients* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C55S3H · Moro, S., Rita, P., & Cortez, P. (2014). *Bank Marketing* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5K306.
- Los filtros usan solo datos anteriores al corte; la prueba de «no futuro» debe seguir en verde.
- No publicar datos sensibles ni secretos. No evaluar solo mediante capturas.

### Estado (leer antes de impartir)
- **Licencias:** verificadas el 09/11/2026 en las fichas oficiales (`02-Proyecto-Transversal/dataset-candidatos.md`).
- **Sin validar:** los archivos no se han descargado (el proxy del entorno bloquea UCI), no hay sha256, ni perfilado real, ni base de referencia, ni modelo base, ni pruebas. Las cifras de esta tabla salen de las fichas y de la lectura de terceros, no de los datos.
- **Pendiente de decidir:** si el alumno elige uno o se le asigna, y si se incluye una copia de los datos en el repositorio. Ver `00-Planificacion/decisiones-y-pendientes.md` (puntos 15 a 17).
