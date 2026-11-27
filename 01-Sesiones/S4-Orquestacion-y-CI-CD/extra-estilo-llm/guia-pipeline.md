# Extra de S4: los notebooks del estilo de color, orquestados en GitHub Actions (~30 min)

Antes de esta guía conviene haber leído el [README](README.md) (los tres actos, los resultados y el glosario) y haber recorrido los notebooks 00 a 05. Es el paso siguiente al [pipeline de datos e2e de S3](../../S3-Despliegue-y-Redes-Neuronales/laboratorio-github-actions/guia-pipeline-e2e.md). Allí cada etapa del proyecto era un job. Aquí **cada notebook del extra es un job**: los mismos notebooks 00 a 05 que has leído, sin copiarlos a scripts, se ejecutan solos en los servidores de GitHub y dejan sus resultados como artefactos.

En tu copia del repositorio del curso (tu *fork*) vas a:

1. crear una rama `lab/extra-estilo-llm`;
2. añadir el workflow [`extra-estilo-llm.yml`](extra-estilo-llm.yml) en `.github/workflows/`;
3. verlo correr en la pestaña **Actions**: el grafo, los pasos de un notebook, los artefactos y el resumen.

No hace falta GPU, ni Codespace, ni Google Cloud.

> **Estado de validación.** El workflow se ejecutó de verdad el 21/11/2026 en el repositorio del profesor, rama `lab/extra-estilo-llm` (run [44854247545](https://github.com/helicr/curso-ml-ia-desarrollo-produccion/actions/runs/44854247545)): **Success, 14 min 10 s de principio a fin, 13 artefactos**. Los tiempos de este documento salen de ese run. Lo que **no** se ha verificado: un fork de otra cuenta (el aviso para activar Actions) y el run de un alumno.

---

## 1. La idea en un minuto

- **Notebooks como jobs.** Un *job* es un trabajo del workflow; cada notebook (00 a 05) corre en el suyo, en un *runner* (una máquina virtual nueva que GitHub presta mientras dura el job; aquí `ubuntu-latest`, sin GPU). `needs:` indica de qué job depende otro: hasta que no termina el primero, el segundo no arranca.
- **papermill.** Es la herramienta que ejecuta un notebook desde la línea de órdenes y le inyecta parámetros (`-p N_EJEMPLOS 60`) en su celda `parameters`. Guarda una copia **ya ejecutada**, con sus salidas, que se sube como artefacto para ver en qué celda se rompió algo.
- **Artefactos.** Como cada job empieza en una máquina vacía, lo que produce un notebook (las parejas de fotos, el adaptador LoRA, las métricas) se **sube** al terminar y lo **descarga** el job siguiente, igual que en S3.
- **Caché.** El modelo (494 MB) y las fotos de Oxford-IIIT Pet (~792 MB) se descargan la primera vez y se guardan en la caché de GitHub, para no bajarlos en cada run ni en cada job.
- **Parámetros pequeños a propósito.** En clase los notebooks usan 300 fotos y tardan ~24 min (el 03) y ~23 min (el 05). En Actions se usan 60 fotos y pocas épocas para que todo quepa en 14 minutos. **Sirve para comprobar que el pipeline funciona; las conclusiones del extra se sacan con la configuración de clase** (sección 6).

### El grafo

```text
0 · Pruebas ─► 1 · Preparar (00) ─► 2 · Datos (01) ─┬─► 3a · Zero-shot, A (02) ───────────┐
                                                    ├─► 3b · LoRA, B (03) ────────────────┼─► 4 · Comparar (04) ─┐
                                                    ├─► 3c · Base C y Reinhard D (04) ────┘                      ├─► 5 · Resumen
                                                    └─► 3d · Acto 3, explicar (05) ───────────────────────────────┘
```

Los cuatro jobs 3a, 3b, 3c y 3d tienen el mismo `needs: datos`, así que **corren a la vez**. `comparar` espera a 3a, 3b y 3c; `resumen` espera a `comparar` y a `explicar`.

Así lo dibuja GitHub en el **Summary** del run real (captura `x01-grafo-actions`):

![Grafo del run en la pestaña Actions: Pruebas, Preparar, Datos, cuatro jobs en paralelo, Comparar y Resumen; Success, 14 m 10 s, 13 artefactos](img/x01-grafo-actions.webp)

---

## 2. Guion del profesor (~30 min)

Antes de clase: deja abierto el [run real](https://github.com/helicr/curso-ml-ia-desarrollo-produccion/actions/runs/44854247545) en una pestaña y el archivo [`extra-estilo-llm.yml`](extra-estilo-llm.yml) en otra. Es el respaldo si algo falla en vivo (ver [`checklist-actions.md`](checklist-actions.md)).

| Min | Qué hacer | Qué decir / preguntar |
|---|---|---|
| 0–3 | Recordar los tres actos con la tabla de resultados del README | «Los notebooks ya los conocéis. ¿Cómo los ejecutaríais todos, en orden, sin acordaros de nada?» |
| 3–6 | Dibujar el grafo de la sección 1 en la pizarra | **Pregunta:** «¿Qué notebooks pueden correr a la vez?» → los que solo necesitan los datos: 02, 03, 04 (C y D) y 05 |
| 6–11 | Abrir `extra-estilo-llm.yml`. Recorrer `on:` (push a `lab/**` y `workflow_dispatch`), el bloque `env:` con los parámetros, y **un** job (`lora`): `needs: datos`, `download-artifact` con `name: datos`, la orden `papermill`, los dos `upload-artifact` | Señalar que los `name:` de subida y bajada **deben coincidir**. Enseñar `if: always()` en la subida del notebook ejecutado: se sube aunque falle |
| 11–14 | Pestaña **Actions** del repositorio: el workflow **Extra S4 · estilo de color con un LLM** y el run de la rama `lab/extra-estilo-llm` | Un run por cada `push` a `lab/**` |
| 14–18 | Entrar en el run: **Summary** y su **grafo**. Señalar la duración de cada caja y los cuatro jobs en paralelo | **Pregunta:** «¿Qué job tarda más? ¿Cuál es el cuello de botella del pipeline?» → 3b, el fine-tuning LoRA (352 s) |
| 18–22 | Clic en **3b · Fine-tuning LoRA** → desplegar el paso **Ejecutar 03_fine_tuning_lora.ipynb**: se ve la barra de papermill celda a celda | «Es el mismo notebook que habéis leído, ejecutado por una máquina» |
| 22–26 | Volver al **Summary**, sección de artefactos (13). **Descargar `comparacion`** (tabla CSV/JSON y panel PNG) y **`nb-04-comparar`** (el notebook 04 ejecutado, ábrelo en el navegador o en el editor) | «Esto es lo que se pasan los jobs y lo que os lleváis. Caducan a los 3 días (`retention-days: 3`)» |
| 26–29 | En el mismo **Summary**, el bloque escrito por **5 · Resumen**: las dos tablas (actos 1–2 y acto 3) | Lo escribe el job con `>> "$GITHUB_STEP_SUMMARY"`. **Pregunta clave:** «¿Qué conclusión sacáis de esta tabla?» → **ninguna sobre el LLM**: 60 fotos, 13 de test y 2 épocas solo prueban que el pipeline funciona |
| 29–30 | Cierre: los alumnos lanzan el suyo (sección 3) | «Esto es MLOps (llevar un modelo de ML del experimento a producción con procesos repetibles): el experimento se reproduce con un `push`» |

---

## 3. Pasos para el alumno

El archivo `extra-estilo-llm.yml` y la carpeta del extra estarán en `develop` **cuando el profesor lo publique**. Hasta entonces, el YAML se copia de la rama del profesor:

<https://raw.githubusercontent.com/helicr/curso-ml-ia-desarrollo-produccion/lab/extra-estilo-llm/.github/workflows/extra-estilo-llm.yml>

El workflow ejecuta los notebooks desde la carpeta `01-Sesiones/S4-Orquestacion-y-CI-CD/extra-estilo-llm/` **de tu repositorio**. Por eso tu fork debe tener esa carpeta en la rama desde la que partes (cuando el profesor la publique, bastará con sincronizar tu fork con `develop`).

**Antes de empezar (las dos rutas):** entra en la pestaña **Actions** de tu fork. En los forks, GitHub puede tener Actions desactivado al principio: **si ves un aviso** que pide activar los workflows, acéptalo (el texto exacto del botón: **sin verificar**).

### Ruta A · Solo con la web de GitHub (sin Codespace)

1. **Rama.** En tu fork, en el selector de ramas, elige `develop`, escribe `lab/extra-estilo-llm` y crea la rama a partir de `develop`. **El nombre debe empezar por `lab/`**: es lo que escucha el disparador.
2. **Copiar el YAML.** Abre en otra pestaña la URL *raw* de arriba (o, en el repositorio, el archivo `extra-estilo-llm.yml` y el botón **Raw**), selecciona todo y copia. No lo teclees a mano: la sangría se rompe.
3. **Crear el archivo.** Ya en tu rama `lab/extra-estilo-llm`: **Add file → Create new file**. Como nombre escribe exactamente `.github/workflows/extra-estilo-llm.yml` (al teclear las `/` GitHub crea las carpetas; el punto inicial y la carpeta `workflows` son obligatorios). Pega el contenido.
4. **Commit.** **Commit changes…** directamente en la rama `lab/extra-estilo-llm` (no en `develop`).
5. **Ver Actions.** Pestaña **Actions** → **Extra S4 · estilo de color con un LLM** → el run de tu commit. Sigue la sección 4.

### Ruta B · Por terminal (Codespace)

```bash
git switch develop
git pull
git switch -c lab/extra-estilo-llm
mkdir -p .github/workflows
cp 01-Sesiones/S4-Orquestacion-y-CI-CD/extra-estilo-llm/extra-estilo-llm.yml .github/workflows/
git status
git add .github/workflows/extra-estilo-llm.yml
git commit -m "Extra S4: estilo de color con un LLM en GitHub Actions"
git push -u origin lab/extra-estilo-llm
```

Si `cp` dice que el archivo no existe (tu `develop` aún no lo tiene), descárgalo de la rama del profesor:

```bash
curl -fsSL -o .github/workflows/extra-estilo-llm.yml \
  https://raw.githubusercontent.com/helicr/curso-ml-ia-desarrollo-produccion/lab/extra-estilo-llm/.github/workflows/extra-estilo-llm.yml
```

**Si falla:** si git pide nombre y correo, configúralos una vez con `git config user.name "Tu nombre"` y `git config user.email "tu-correo"` y repite el commit.

**Lanzarlo a mano.** Si el archivo está en la rama principal de tu fork, en **Actions → Extra S4 → Run workflow** puedes cambiar `n_ejemplos` (60), `epocas` (2) y `n_frases` (100). Con más fotos o épocas, el run tarda más. El botón solo aparece cuando el archivo está en la rama principal.

---

## 4. Qué debes ver

En **Actions** aparece un run de **Extra S4 · estilo de color con un LLM**; en su **Summary**, el grafo con 9 cajas: las dos primeras en cadena, luego cuatro a la vez y al final las dos últimas.

Tiempos reales del run del profesor (21/11/2026):

| Job | Duración | Notebook |
|---|---|---|
| 0 · Pruebas (sin modelos) | 31 s | pytest |
| 1 · Preparar entorno | 2 min 1 s (121 s) | 00 |
| 2 · Datos fabricados | 2 min 45 s (165 s) | 01 (la descarga del tar con `curl` fueron 34 s; queda en caché para los siguientes runs) |
| 3a · Zero-shot, versión A | 3 min 32 s (212 s) | 02 |
| 3b · Fine-tuning LoRA, versión B | 5 min 52 s (352 s) | 03 |
| 3c · Base C y Reinhard D | 1 min 49 s (109 s) | 04, etapa `c_d` |
| 3d · Acto 3, explicar | 5 min 23 s (323 s) | 05 |
| 4 · Comparar y transferir | 2 min 41 s (161 s) | 04, etapa `completo` |
| 5 · Resumen | 6 s | — |
| **Run completo** | **14 min 10 s** | 3a, 3b, 3c y 3d en paralelo |

Tus tiempos serán parecidos, no iguales: dependen de la máquina que te toque y de si las cachés están calientes (el primer run descarga el modelo y las fotos).

Además:

- **13 artefactos**: `nb-00-preparar`, `nb-01-datos`, `datos`, `nb-02-zero-shot`, `metricas-a`, `nb-03-lora`, `adaptador-lora`, `nb-04-c-d`, `metricas-c-d`, `nb-05`, `explicacion`, `nb-04-comparar` y `comparacion`. Los `nb-*` son cada notebook ya ejecutado.
- **Resumen** (captura `x02-resumen-actions`): la tabla de los actos 1-2 y la del acto 3.

![Resumen del run: tabla comparativa de los actos 1 y 2 y tabla del acto 3](img/x02-resumen-actions.webp)

Resultados del run (con parámetros de CI: 60 fotos, 58 parejas útiles —por qué 58 y no 60: sin verificar—, 40 de entrenamiento y 13 de test; 2 épocas; en el acto 3, 100 frases y 1 época). Son cifras **de CI**: no se comparan con las de clase del README (A 0,433; B 0,310; media 0,259; B3 con 100 % de sentido correcto). El error es el MAE normalizado de los notebooks 02 y 04 (error medio dividido por el rango de cada ajuste; 0 = perfecto); Ridge es la regresión lineal con penalización del notebook 04:

| Versión | Resultado del run |
|---|---|
| Media (contestar siempre la media) | MAE normalizado 0,234 |
| A zero-shot | 0,502 |
| B LoRA | 0,267 |
| C (MobileNetV3 + Ridge) | 0,229 |
| C_color (27 estadísticas + Ridge) | 0,151 |
| Acto 3, A3 sin entrenar | 43,6 % de sentido correcto, 53,8 % de alucinación, 0 % de frases perfectas |
| Acto 3, B3 con LoRA | 90,9 % de sentido correcto, 53,8 % de alucinación, 23,1 % de frases perfectas |

**Nota honesta.** C y C_color salen con las mismas cifras redondeadas que con las 300 fotos de clase (0,229 y 0,151) por casualidad: se comprobó con los datos de CI (0,22899 y 0,15092), y sus ΔE sí cambian. Con 13 fotos de test, estas cifras **no son conclusiones**: comprueban que el pipeline funciona.

---

## 5. Si falla

| Lo que ves | Causa probable | Qué hacer |
|---|---|---|
| No aparece ningún run | El archivo no está en `.github/workflows/extra-estilo-llm.yml` (con punto, en la **raíz**, no en una carpeta del extra); la rama no empieza por `lab/`; o Actions está desactivado en tu fork | Revisa la ruta y el nombre de la rama; mira el aviso de la pestaña **Actions** |
| El run falla sin llegar a los jobs | **YAML mal sangrado** al teclearlo o pegarlo | Copia de nuevo con el botón **Raw**, sin retocar |
| «Run workflow» no aparece | El archivo no está en la rama principal del fork | Usa el disparador por rama `lab/**` |
| Un job falla y los siguientes salen en gris (*skipped*) | Es lo esperado: con `needs:`, lo que depende de un job roto no se ejecuta | Busca la **primera caja roja** y su paso rojo; las grises no tienen nada que leer |
| Un job falla en `download-artifact` por artefacto no encontrado | El `name:` de subida y el de bajada no coinciden | Compáralos |
| Quieres saber en qué celda se rompió un notebook | — | Descarga el artefacto `nb-…` de ese job (se sube siempre, con `if: always()`) y ábrelo |
| Falla el job de pruebas con un `ModuleNotFoundError` | **Incidencia real del 21/11/2026:** faltaba `scikit-learn` en la instalación del job de pruebas | Añadir el paquete que falta al `pip install` del job `pruebas` (en el workflow ya está corregido) |
| Falla la descarga de las fotos (error HTTP) en el job 2 | **Incidencia real del 21/11/2026:** la descarga de Oxford-IIIT Pet con `urllib` de Python devolvió un error HTTP en el runner | El workflow ya descarga el tar con `curl` antes del notebook y lo guarda en la caché. Si lo ves en tu fork, comprueba que ese paso está en tu copia |
| Quieres ejecutar los notebooks en tu ordenador o Codespace y fallan (`No module named 'torch'`, `ConnectError` de Hugging Face) o tardan demasiado (el 03, unos 24 min; el 05, unos 23 min) | Las librerías del extra van aparte de las del proyecto; una red con proxy corporativo bloquea la descarga del modelo; en un Codespace de 2 núcleos pesan | Este pipeline los ejecuta por ti (parámetros pequeños). Si los quieres en local, mira «Si falla» del [`README.md`](README.md) |

Avisos que **no** son un fallo: «Node.js 20 is deprecated» en las acciones `@v4` y los avisos de Hugging Face sobre peticiones sin autenticar.

Para la víspera de clase y los fallos de configuración, consulta [`checklist-actions.md`](checklist-actions.md).

---

## 6. Límites

- **Los parámetros de CI son pequeños a propósito.** 60 fotos (13 de test), 2 épocas y, en el acto 3, 100 frases y 1 época. Las conclusiones del extra (A 0,433; B 0,310 frente a la media 0,259; C_color 0,151; el acto 3 con 500 frases) salen de los notebooks ejecutados con 300 fotos.
- **El runner no tiene GPU.** Es CPU, como el portátil con el que se midió el extra. Si subes `n_ejemplos` o `epocas`, el run tarda más.
- **Una sola ejecución verificada** en el repositorio del profesor. Un fork de otra cuenta, sin verificar.
- Las cachés (modelo y tar de Oxford) hacen que el primer run sea más lento que los siguientes.

## 7. Autoevaluación

1. ¿Por qué los jobs 3a, 3b, 3c y 3d corren a la vez? → porque los cuatro tienen `needs: datos` y nada más.
2. ¿Qué hace papermill que no haría `jupyter` a secas? → ejecuta el notebook desde la terminal inyectando parámetros en la celda `parameters` y guarda una copia ejecutada.
3. ¿Qué artefacto abrirías para ver en qué celda falló el 03? → `nb-03-lora`.
4. ¿Por qué la tabla del run no sirve para decidir si el LLM es mejor que la línea base? → 13 fotos de test y 2 épocas: solo prueba que el pipeline funciona.
