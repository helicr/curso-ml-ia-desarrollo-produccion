---
name: informe-semanal
description: Cómo preparar el informe semanal para dirección, con una tabla y un párrafo, solo con cifras que salgan de las herramientas. Úsala cuando pidan un informe, un resumen semanal o un resumen para dirección.
activar_si: informe, resumen semanal, para dirección, para direccion
---
# Informe semanal para dirección

## Qué datos pedir (con herramientas, nunca de memoria)

1. `version_en_produccion`: versión del modelo, desde cuándo está y sus métricas de aprobación.
2. `lista_del_dia`: la lista de clientes de la última campaña, con su tramo y su probabilidad.

Si una herramienta devuelve un error, no lo tapes: escribe en el informe «sin dato» y el motivo en una línea.

## Estructura

**Tabla** (una fila por cliente de la lista; solo columnas que devuelvan las herramientas):

| Puesto | Cliente | Probabilidad | Tramo |
|---|---|---|---|

**Párrafo** (de tres a cinco frases, tono neutro, en español):
- qué versión del modelo está en producción y desde cuándo;
- cuántos clientes hay en cada tramo de la lista y cuál es la probabilidad más alta y la más baja de la tabla;
- una frase final que recuerde que las probabilidades son estimaciones del modelo, no certezas.

## Reglas

- Cada cifra del informe debe estar en la respuesta de una herramienta. Si no está, no la escribas.
- No hagas comparaciones con semanas anteriores ni previsiones de ingresos: no hay herramienta que lo dé.
- No incluyas datos personales (el caso no los tiene) ni ofrezcas descuentos.
