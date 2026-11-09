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
1. Pipeline de datos, modelo y métricas, **como cuadernos** (revisión S2).
2. API y contenedor (S3). Aquí el pipeline ya es **Python**: la traducción de los cuadernos al paquete.
3. Migración a GCP y despliegue (S4). Opcional: módulo neuronal.
4. Pipeline orquestado con GitHub Actions (S5).
5. Repositorio e informe finales (posterior a S5).

## La tarea de los alumnos
Repetir la receta (RAW → MASTER → FS → ML → entrenamiento, con cuadernos y su traducción a `.py`) sobre **otro dataset** de estructura similar: una entidad, una fecha de corte,
un objetivo definido hacia el futuro y variables calculadas solo con el pasado. **El dataset de la tarea está por decidir** (ver `02-Proyecto-Transversal/dataset-candidatos.md`).

No publicar datos sensibles ni secretos. No evaluar solo mediante capturas.
