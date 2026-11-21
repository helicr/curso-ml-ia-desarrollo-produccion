# Notas del workflow `extra-estilo-llm.yml` (borrador, con el acto 3)

El archivo se copiará a `.github/workflows/extra-estilo-llm.yml` en T20, con el instructor. Hoy **no** está en `.github/` y no se ha ejecutado nunca en GitHub.

## Grafo
```
pruebas → preparar (00) → datos (01) → ┬ zero-shot (02, A) ────────┐
                                       ├ lora (03, B) ─────────────┼→ comparar (04 completo) ┐
                                       ├ base-y-reinhard (04 c_d) ─┘                         ├→ resumen
                                       └ explicar (05, acto 3) ──────────────────────────────┘
```
`explicar` solo necesita `datos` (lee `val` y `test` de `parejas/`; el train se fabrica dentro del notebook), así que corre en paralelo con los tres jobs de los actos 1–2. `resumen` espera a `comparar` y a `explicar`.

## Artefactos
| Artefacto | Lo sube | Lo bajan |
|---|---|---|
| `datos` (carpeta de trabajo con `parejas/`) | datos | zero-shot, lora, base-y-reinhard, explicar, comparar |
| `metricas-a`, `adaptador-lora`, `metricas-c-d` | zero-shot, lora, base-y-reinhard | comparar |
| `explicacion` (`adaptador_explicacion/`, `metricas_explicacion.json`, `explicaciones.jsonl`) | explicar | resumen |
| `comparacion` | comparar | resumen |
| `nb-00-preparar`, `nb-01-datos`, `nb-02-zero-shot`, `nb-03-lora`, `nb-04-c-d`, `nb-04-comparar`, `nb-05` | cada job, con `if: always()` | nadie (se miran en la web) |

## Parámetros de CI elegidos y de dónde salen
| Parámetro | Valor | Origen |
|---|---|---|
| `N_EJEMPLOS` | 60 | INFORME, «Tamaño mínimo didáctico» (estimación, sin verificar en GitHub). Con 16 y 1 época el pipeline corre, pero B no aprende ni el formato (0 % de formato correcto, medido). |
| `EPOCAS` (actos 1–2) | 2 | INFORME, misma propuesta. |
| `RESOLUCION` | 224 | Ejecución de referencia. |
| `MODELO` | `HuggingFaceTB/SmolVLM-256M-Instruct` | Elegido en el estudio (apache-2.0). |
| `N_FRASES` (acto 3) | 100 | INFORME, ronda 4: «CI: `-p N_FRASES 100 -p EPOCAS 1`. Sin verificar». Entrada manual `n_frases`. |
| `EPOCAS` del 05 | 1 | Ídem. Variable propia (`EPOCAS_EXPLICAR`) para no mezclarla con las 2 épocas de B. |
| `FORMATO` | `facil` | Valor por defecto del 05; el formato `json` salió mucho peor (INFORME, rondas 3 y 4). |

Timeouts (`timeout-minutes`), con la referencia del INFORME anotada en el propio YAML: preparar 20, datos 20, zero-shot 20, lora 40, base-y-reinhard 15, explicar 40, comparar 15, resumen 5, pruebas 10. Los tiempos medidos son de un portátil de 12 hilos; **el runner estándar (4 vCPU) puede ser más lento: ajustar tras el run real**. Si se lanza a mano con N o épocas mayores, hay que subir los timeouts.

## Caché del tar de Oxford-IIIT Pet
`datos.py` descarga `images.tar.gz` (~792 MB) a `tempfile.gettempdir()/oxford_pets_images.tar.gz` si `ESTILO_TAR` no apunta a un archivo existente. En Linux eso es `/tmp`, y esa es la ruta que se cachea (`actions/cache@v4`, clave `oxford-iiit-pet-images-tar-v1`) y se pasa en `ESTILO_TAR`. El primer run lo descarga y lo guarda al terminar el job `datos` (si falla, no se guarda); los siguientes lo restauran. Está fuera de la carpeta de trabajo, así que no viaja en los artefactos.

## Qué se confirmó con el INFORME
- Parámetros de los notebooks: `N_EJEMPLOS`, `EPOCAS`, `RESOLUCION`, `MODELO`, `CARPETA_TRABAJO` (leída de `ESTILO_TRABAJO`) y, en el 04, `ETAPA` (`c_d` o `completo`); en el 05, además `N_FRASES` y `FORMATO`. El workflow los pasa con `papermill -p`.
- La tabla comparativa es `resultados/tabla_comparativa.csv` (el resumen la busca por «tabla» en el nombre).
- `metricas_explicacion.json` tiene las claves `A3` y `B3` con `pct_ajustes_sentido_correcto`, `pct_frases_con_alucinacion` y `pct_frases_perfectas` (leídas del notebook 05), más `n_test` y, en `B3`, `n_train` y `epocas`.
- Solo escriben `mlflow.db` el 03, el 04 `completo` y el 05 (runs A3 y B3). El 02 y el 04 `c_d` solo dejan JSON.
- Tiempos medidos en el portátil (referencia para los timeouts): ver el comentario sobre cada job.

## Sigue sin verificar hasta el run real
- Que el 05 y el módulo común existan en la carpeta del extra: hoy `05_explicar_estilo.ipynb` y `comun_estilo.py` están en `00-Planificacion/s4/_pico_llm_estilo/`, no junto a los notebooks 00–04 (que usan el paquete `estilo/`). Hay que traerlos y comprobar que importan lo mismo antes de T20.
- Los runs `A3_explicacion_one_shot` y `B3_explicacion_lora` del 05 se escriben en el `mlflow.db` del job `explicar`, que **no** se sube (el artefacto `explicacion` no lo incluye). Si se quieren ver en MLflow hay que subirlo (con cuidado de no pisar el de `adaptador-lora`).
- Resultados del 05 con N_FRASES = 100 y 1 época: no hay medida (la ejecución de referencia fue con 500 y 2 épocas: 100 % de sentido correcto, 18,3 % de alucinación). Con tan pocos datos es posible que sea peor.
- Con N_EJEMPLOS = 60 el test del 05 y del 02 es de unas 12 frases/fotos (partición 70/10/20 del INFORME): las cifras son para probar el pipeline, no para sacar conclusiones.
- El job `pruebas` instala solo pytest, pyyaml, numpy, pillow, scikit-image y matplotlib; hay que contrastarlo con lo que importen las pruebas de `pruebas/` y con `requisitos-extra-estilo.txt`.
- El índice de PyTorch CPU para Linux en `requisitos-extra-estilo.txt`.
- Que `actions/cache` restaure el modelo en los jobs paralelos (la caché solo se guarda si `preparar` termina bien) y el tar en `datos`.

## Qué mirar en el run real (T20)
1. **Tiempo por job** (comparar con los comentarios del YAML y ajustar `timeout-minutes`): sobre todo `lora` y `explicar`.
2. **Memoria**: ¿cabe en el runner estándar? Pico medido en el portátil: 2747 MB (03), 3019 MB (05 con 210 frases), 2887 MB (05 con 500 frases).
3. **Tamaño de los artefactos**: `datos`, `adaptador-lora`, `explicacion` (el adaptador pesa 7,06 MB) y `comparacion`; y de las cachés (modelo en `hf-cache`, tar de ~792 MB) frente a los límites de GitHub.
4. **Índice de PyTorch CPU en Linux**: que `pip install -r requisitos-extra-estilo.txt` resuelva torch sin CUDA.
5. **Caché del tar**: que el primer run lo guarde y el segundo lo restaure sin descargar nada (comparar el tiempo del job `datos`).
6. **Resumen**: que la página del run muestre las dos tablas (actos 1–2 y acto 3) y que la lista de artefactos coincida con la real.
7. Que en un fork de otra cuenta Actions esté activado y la rama `lab/**` dispare el run.

## Cómo se prueba
1. Ahora: `python -m pytest pruebas/test_workflow.py` (estática: disparadores, permisos, timeouts, grafo `needs:`, artefactos subida/bajada, notebooks 00–05, caché del tar, resumen con el acto 3).
2. T20: copiar a `.github/workflows/`, push a una rama `lab/…` del repo del profesor, anotar tiempos y artefactos; repetir en un fork limpio.
3. Cada notebook ejecutado se sube siempre como artefacto (`nb-*`), así un fallo se ve en su celda.
