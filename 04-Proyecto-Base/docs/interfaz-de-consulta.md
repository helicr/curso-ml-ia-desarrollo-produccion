# La interfaz de consulta: del id del cliente a una recomendación

La API del modelo (`ia_mlops/api`, ver [`api-y-contenedor.md`](api-y-contenedor.md)) responde a una pregunta técnica: *dadas estas 13 variables, ¿qué probabilidad hay de recompra en 90 días?* Quien prepara la campaña hace otra pregunta: *¿qué hago con los clientes 12425, 13599 y 18108?* No conoce `frecuencia_180d` ni `dias_medios_entre_compras`, y no debería tener que calcularlas.

La interfaz (`ia_mlops/interfaz`) hace de puente entre las dos preguntas.

```text
  ids de cliente ──► variables en la fecha de corte ──► API del modelo ──► probabilidad ──► regla de negocio ──► tramo + recomendación
  (pantalla, CSV)    (sql/fs/02_poblar_fs.sql,          (/predecir/lote)                   (config.SEGMENTOS_RECOMPRA)
                      sobre una tabla temporal)
```

## Cómo se calculan las variables
No se inventa nada nuevo: se usa `explotacion.variables_en_corte`, la misma función del laboratorio extra.
- Ejecuta **el mismo SQL de la capa FS** (`sql/fs/02_poblar_fs.sql`) para la fecha de corte pedida, sobre una tabla temporal. La capa FS del proyecto no se toca.
- Por eso las variables son exactamente las del entrenamiento: con un corte que ya está en FS (por ejemplo `2011-09-01`), las pruebas comprueban que salen idénticas a las de `fs_cliente_corte`.
- Cumple la regla de oro: solo usa facturas anteriores al corte.
- **Fecha de corte.** Por defecto es el día siguiente a la última factura de MASTER (el «hoy» del dato: `2011-12-10`). Se puede elegir otra entre la primera factura y ese día; fuera de ese tramo la petición da 422.

Se puntúa a **todos** los clientes del corte, no solo a los pedidos. Así cada cliente lleva su **puesto** y su **decil** («está entre el 10 % con más probabilidad»). El resultado se guarda en memoria por corte y por huella del modelo: la segunda consulta del mismo corte es inmediata y, si se reentrena, la huella cambia y se recalcula.

## De la probabilidad a la recomendación
El modelo solo da la probabilidad. Convertirla en una acción **es una decisión de negocio**: los tramos y los textos están en `ia_mlops/config.py` y se cambian ahí, sin tocar el código.

| Tramo | Probabilidad | Recomendación (por defecto) |
|---|---|---|
| `alta` | ≥ 70 % | Comprará probablemente sin ayuda: comunicación habitual o venta cruzada; no gastar el incentivo. |
| `media` | 40–70 % | Indeciso: prioridad de la campaña de recompra; aquí un incentivo puede cambiar el resultado. |
| `baja` | < 40 % | Poco probable que compre en 90 días: contacto de recuperación de bajo coste o no invertir. |

Los umbrales son un punto de partida para discutir en clase, no un resultado del modelo. Con la muestra y el corte de hoy quedan 40 clientes en `alta`, 35 en `media` y 73 en `baja` (148 en total). Un cliente se marca **«revisar»** cuando el modelo avisa de valores que no vio al entrenar: la probabilidad no tiene respaldo ahí.

> **Ojo con la muestra.** El modelo se entrenó con cortes de 2010, en los que `antiguedad_dias` llega como mucho a 364. En el corte de hoy (diciembre de 2011) casi todos los clientes tienen más antigüedad, así que 132 de los 148 salen con «revisar». No es un fallo de la interfaz: es la primera señal de que conviene reentrenar (deriva, S5).

> **No confundir con la campaña del laboratorio extra.** `python -m ia_mlops.explotacion` marca `en_campana` al 10 % con **más** probabilidad. La interfaz propone dirigir el incentivo al tramo **medio**. Son dos criterios de negocio distintos; con qué objetivo se decide la campaña es una buena pregunta para el aula.

## Arrancarla
Desde `04-Proyecto-Base`, con el entorno activo y después de `python -m ia_mlops.pipeline`:
```text
# terminal 1: la API del modelo
python -m uvicorn ia_mlops.api.app:app --port 8080        # o: make api,  o el contenedor: docker run -p 8080:8080 retencion-api:local

# terminal 2: la interfaz, que llama a esa API
python -m ia_mlops.interfaz --url http://127.0.0.1:8080   # o: make interfaz
```
Se abre en <http://127.0.0.1:8090>. Sin `--url` (y sin la variable `CURSO_URL_API`) no llama a la API: usa el modelo de `models/` con el mismo código que la API. Sirve para probar sin la API, pero lo que se enseña en S2 es el camino por la API.

En la página se pueden escribir uno o varios ids (separados por comas, espacios o saltos de línea), cargar una lista en **CSV o TXT** (si tiene cabecera se usa la columna `cliente_id`; si no, la primera), elegir la fecha de corte y descargar el resultado en CSV. El botón **Ejemplo** rellena cinco clientes repartidos por el ranking más uno que no existe (`99999`), para ver los tres tramos y el caso «sin predicción».

## Llamarla sin la página
```text
curl -X POST http://127.0.0.1:8090/recomendar -H "Content-Type: application/json" -d '{"cliente_ids": [13599, 18108, 13306, 99999]}'
curl "http://127.0.0.1:8090/recomendar/18108?corte=2011-09-01"
curl http://127.0.0.1:8090/estado
```
En PowerShell: `curl.exe` y comillas dobles escapadas, o `Invoke-RestMethod`. La documentación interactiva está en `/docs`.

Respuesta (recortada, con la muestra):
```json
{"corte": "2011-12-10", "origen": "http://127.0.0.1:8080", "modelo": "regresion_logistica", "clientes_en_el_corte": 148,
 "pedidos": 4, "encontrados": 3, "por_segmento": {"alta": 1, "media": 1, "baja": 1},
 "resultados": [{"cliente_id": 13599, "probabilidad": 0.9977, "segmento": "alta", "recomendacion": "Comprará probablemente sin ayuda: …",
                 "revisar": true, "puesto": 1, "decil": 1, "advertencias": ["antiguedad_dias=738 esta fuera del rango visto al entrenar [1, 364]; …"],
                 "variables": {"recencia_dias": 1, "frecuencia": 33, "…": "…"}}, "…"],
 "no_encontrados": [{"cliente_id": 99999, "motivo": "no existe en MASTER"}]}
```

| Código | Cuándo |
|---|---|
| 200 | Siempre que la petición tenga sentido, aunque algún id no tenga predicción. Ese id va en `no_encontrados` con su motivo: `no existe en MASTER`, o `sin compras válidas antes del corte` (es cliente, pero en esa fecha aún no tenía historia). |
| 422 | Lista vacía o de más de 1000 ids, un id que no es un número, fecha mal escrita, inexistente o fuera del dato, o un campo desconocido. |
| 503 | La API no responde o responde con error, no hay modelo, o no existe la capa FS. El `detalle` dice qué hacer. |

## Por qué es un servicio aparte y no un endpoint más de la API
- **La imagen del modelo no lleva datos de clientes.** La API recibe variables y devuelve probabilidades; no necesita `curso.db`. Si buscara las variables por id, la base entraría en la imagen (hoy `.dockerignore` la deja fuera a propósito).
- **Cada pieza cambia por un motivo distinto.** Se reentrena el modelo sin tocar la interfaz, y se cambian los umbrales sin reconstruir la imagen.
- **Es el patrón de producción.** Un servicio de variables (*feature store* en línea) delante del servicio del modelo. Aquí la base es SQLite y está en el mismo equipo; en S3 y S4, la API va a Cloud Run y la interfaz la llamaría por su URL.

Cómo se ejecutan las dos piezas en contenedores separados (red, volumen de solo lectura, Compose) y qué falta para producción: [`del-ordenador-al-servicio.md`](del-ordenador-al-servicio.md).

## Qué se probó
- `tests/test_interfaz.py` (18 pruebas, se ejecutan con `-m "not lento"`). Comprueban:
  - la probabilidad es la misma que la de `explotacion.campana`;
  - las variables son idénticas a las de la capa FS;
  - la regla de tramos, configurable;
  - ids repetidos, desconocidos y sin historia;
  - los seis casos de 422 y los dos de 503;
  - que la capa FS queda intacta, también con la base en solo lectura;
  - `/salud` y `/listo`;
  - y que **por la API real (uvicorn en otro proceso) da lo mismo que en local**.
- A mano en Windows (14/11/2026), contra la API arrancada con uvicorn: las mismas probabilidades que en local, y un 503 claro con la API parada.
- **Sin probar:** la página en un Codespace (el puerto 8090 está declarado en `.devcontainer/devcontainer.json`) y con el dato completo.
