# Planificación · Puesta en producción de punta a punta (caso Online Retail II)

Estado: **propuesta del 22/11/2026, para revisión del instructor.** Cierra la parte de «llevar el modelo a producción» del curso con el caso del instructor (`retencion-90d`, ¿volverá a comprar en 90 días?). Tareas: [`TAREAS.md`](TAREAS.md).

Reglas de siempre: solo `develop`; no inventar cifras (lo no medido, «sin verificar»); sin secretos propios (solo el `GITHUB_TOKEN` de cada run, con permisos mínimos); sin rutas personales; todo lo que se cree en GitHub (paquetes, environments) se documenta y se puede borrar.

---

## 1. La idea en un minuto

El mismo modelo se usa de **tres maneras**, y cada una tiene su sitio:

*Corregido el 22/11/2026 a petición del instructor: la inferencia online (variables calculadas al vuelo) es un modo propio y distinto del bajo demanda.*

| Modo | La pregunta del negocio | Qué llega | De dónde salen las 13 variables | Frescura | Dónde corre | Base existente |
|---|---|---|---|---|---|---|
| **1 · Puntuación por lotes** (*batch*) | «¿A quién llamo hoy?» | nada: se puntúa a **todos** | el pipeline (FS en el corte del día) | la del último run diario | **GitHub Actions** diario (`schedule`) y a mano; campaña como artefacto y en el resumen | `ia_mlops.explotacion` |
| **2 · Inferencia bajo demanda** (*on-demand*) | «¿Qué probabilidad tiene el cliente 13599?» | un id (o varios) | **leídas** de la tabla FS ya calculada (`fs_cliente_corte`, último corte del pipeline): consulta rápida, sin cálculo | la del último run | API + un lector de la FS (Codespace; prueba en Actions) | `/predecir`, tabla FS (endpoint de lectura nuevo) |
| **3 · Inferencia online** (*features al vuelo*) | «El cliente 13599 acaba de comprar: ¿qué le ofrezco **ahora**?» | un id | **calculadas al vuelo** con el mismo SQL de la capa FS sobre las compras **hasta este momento** (sin fuga: solo datos anteriores al instante de la petición) | la de ahora | interfaz + API (Codespace) | interfaz de consulta (`/recomendar`, `explotacion.variables_en_corte`) |

**La demo que lo hace visible:** en el panel, el botón **«Simular una compra nueva»** inserta una factura para un cliente en la base operacional (copia de demo). La inferencia **online** cambia en el acto (recencia 0, frecuencia +1…); **bajo demanda** y **lote** no cambian hasta el siguiente run diario del pipeline. Es la diferencia entre los tres modos, vista en vivo, y la razón de ser de un *feature store* online.

Y una cuarta pieza que une las tres: **cómo entra una versión nueva del modelo** (reentrenar → comparar con la que está en producción → aprobar → publicar → los tres modos la usan → y cómo volver atrás).

**Interfaz nueva: «Panel de producción».** Una página con cuatro pestañas — *Lote*, *Bajo demanda*, *En línea* y *Versiones* — que enseña los tres modos con el mismo modelo, qué versión está en producción y el historial de versiones.

## 2. Qué aprende el alumno
1. Que «poner en producción» no es una cosa: son **modos distintos** según la pregunta, la latencia y el coste (lote: barato y programado; bajo demanda: rápido pero el que llama trae los datos; en línea: rápido y con los datos frescos, pero hay que calcularlos al vuelo sin fuga).
2. Que los tres modos usan **la misma versión** del modelo y deben dar **la misma probabilidad** para el mismo cliente y corte (se comprueba con `ia_mlops.modeling.comparar`).
3. Cómo **entra una versión nueva**: no se sustituye a mano; pasa una **puerta de calidad** (métrica frente a la de producción), una **aprobación** humana y queda **versionada** (imagen con etiqueta y huella); y cómo se hace **rollback**.
4. Cómo se comporta el **pipeline** cuando no cambia nada (idempotencia por huella: no reentrena), cuando cambian los datos (reentrena y compara) y cuando la versión nueva es peor (se para y no publica).

## 3. Dónde corre cada cosa (sin GCP)

| Pieza | GitHub (repo) | Codespaces | GitHub Actions |
|---|---|---|---|
| Código, datos de muestra, notebooks, workflows | ✓ | — | — |
| Desarrollo y demo en vivo de los modos 2 y 3 (compose: API + interfaz + panel) | — | ✓ | — |
| Pruebas (CI) y prueba de humo de los contenedores | — | — | ✓ (ya existe `validar-dos-contenedores.yml`) |
| **Modo 1: puntuación por lotes programada** | — | — | ✓ nuevo: `puntuar-lote.yml` (`schedule` semanal + `workflow_dispatch`) |
| **Nueva versión del modelo** (entrenar → comparar → construir → aprobar → publicar) | — | — | ✓ nuevo: `nueva-version.yml` (patrón del taller, ya probado en GitHub el 14/11/2026) |
| Dónde vive el modelo «en producción» | ✓ GHCR (imagen versionada) + `models/referencia.json` | lo descarga | lo usa |

GCP (Cloud Run) queda como siguiente paso, ya preparado en S3/S4; aquí no se usa.

## 4. Diseño

### 4.1 La versión «en producción» (decisión D1)
Propuesta: **la imagen de la API publicada en GitHub Container Registry (GHCR) con etiqueta de versión** (`retencion-api:v<N>-<huella>`) **más `models/referencia.json`** en el repositorio (versión, huella de datos, métricas de test, fecha, etiqueta de la imagen). Es lo que se hizo en el taller y funcionó: inmutable, sin servidor de MLflow, visible en GitHub. El registro de MLflow (alias `produccion`) se mantiene en local y en el artefacto del run, como en los laboratorios de S3.
Alternativas: artefacto de un run o *Release* de GitHub con la carpeta del modelo (más simple, menos realista).

### 4.2 Modo 1 · puntuación por lotes (`puntuar-lote.yml`)
`schedule` (p. ej. lunes temprano, hora UTC; los `schedule` en un *fork* vienen desactivados: se dice) + `workflow_dispatch` (entradas: corte, capacidad). Jobs: preparar datos (operacional + pipeline, idempotente) → puntuar con **la imagen de producción** (`docker run` de GHCR + `explotacion --url`) → resumen (tamaño de la campaña, probabilidad media, versión y huella del modelo, avisos de valores fuera de rango) → artefacto `campana_<corte>.csv/.json`. Comprobación: la versión que puntúa es la de `referencia.json`.

### 4.3 Modo 2 · bajo demanda (variables leídas de la FS)
Endpoint nuevo `GET /bajo-demanda/{cliente_id}` (en la interfaz): lee las 13 variables de `fs_cliente_corte` en el **último corte calculado por el pipeline** (consulta por clave, sin cálculo) → API `/predecir` → probabilidad, tramo, corte usado y versión del modelo. Si el cliente no está en ese corte, lo dice. Medir latencia (p50/p95). La API sigue igual (`/predecir` con 13 variables queda como la «inferencia cruda» que usan los tres modos).

### 4.4 Modo 3 · online (variables calculadas al vuelo)
La interfaz de consulta ya calcula las variables al vuelo con `explotacion.variables_en_corte`. Se convierte en un endpoint explícito `GET /online/{cliente_id}` que usa como corte **el instante de la petición** (todas las compras registradas hasta ahora en la base operacional de demo), con la misma regla de oro (solo datos anteriores al corte). Se añade `POST /demo/compra` (solo en modo demo, sobre una copia de la base) para simular una compra nueva. Pruebas: (a) **paridad**: con el mismo corte, online, bajo demanda y lote dan la misma probabilidad; (b) **frescura**: tras una compra simulada, online cambia y bajo demanda/lote no; (c) **sin fuga**: una compra posterior al corte pedido no entra. Medir latencia de punta a punta.

### 4.5 Panel de producción (interfaz)
Ampliar la interfaz de consulta (decisión D3) con un panel de cuatro pestañas, servido en el mismo contenedor:
- **Lote:** la última campaña (CSV del último run de `puntuar-lote`, descargado o montado), con enlace al run de Actions, versión y fecha.
- **Bajo demanda:** id de cliente → variables **leídas** de la FS (corte de ayer) → probabilidad, corte usado, versión, tiempo de respuesta.
- **Online:** id de cliente → variables **calculadas al vuelo** (ahora) → probabilidad, tramo y recomendación, tiempo de respuesta; botón **«Simular una compra nueva»** y, al lado, la comparación con lo que dicen bajo demanda y lote para el mismo cliente.
- **Versiones:** versión en producción (de `/modelo` y `referencia.json`), historial (versiones publicadas en GHCR y sus métricas), y la comparación **campeón frente a candidato** cuando hay una versión nueva pendiente.
Sin librerías externas (HTML + JS del propio servidor, como la interfaz actual).

### 4.6 Nueva versión del modelo (`nueva-version.yml`) y comportamiento del pipeline
Disparo a mano con entradas (de dónde salen los datos nuevos: decisión D2) → jobs:
1. **Entrenar** con los datos nuevos → si la huella de datos es la misma que la de producción: «nada que publicar» (idempotencia). Si no: **comparar** con `referencia.json` en la **misma ventana de test**; si empeora más que la tolerancia, **se para** (rojo, con mensaje claro) y no se construye nada.
2. **Construir y probar** la imagen nueva (prueba de humo: `/salud`, `/listo`, huella, una predicción) y **comparar predicciones** campeón frente a candidato sobre los mismos clientes (cuántos cambian de tramo).
3. **Aprobar:** espera la revisión manual del *environment* `produccion`.
4. **Publicar:** imagen en GHCR con su etiqueta; abre un **PR** que actualiza `models/referencia.json` (nunca push directo a `develop`/`main`).
5. Tras fusionar el PR, el siguiente `puntuar-lote` usa la versión nueva sin tocar nada más.
**Rollback:** revertir el PR de `referencia.json` (el lote siguiente vuelve a la imagen anterior, que sigue en GHCR). Se ensaya.

**Tres escenarios que se ensayan y se documentan con runs reales:** (a) sin datos nuevos → «nada que publicar»; (b) datos nuevos y versión peor → rechazada; (c) datos nuevos y versión aceptable → aprobada, publicada, PR, lote con la nueva; y (d) rollback.

### 4.7 Ajustes tras el inventario (22/11/2026, ver [`INVENTARIO.md`](INVENTARIO.md))
- **FS de producción:** `fs_cliente_corte` solo tiene los 10 cortes de entrenamiento (último 2011-09-01). El lote diario escribirá además las variables del **corte del día** en una tabla `fs_produccion` (cliente, corte, 13 variables, versión del pipeline); **bajo demanda lee de ahí** (último corte disponible) y el panel lo enseña.
- **Online:** hoy la interfaz no admite cortes posteriores a MASTER, no hay inserción de compras y el contenedor monta la base en solo lectura. Se añade un **modo demo** (variable de entorno) que trabaja sobre una **copia** de la base: admite el corte «ahora» y una tabla de **eventos de compra** recientes que el cálculo al vuelo suma a MASTER (simula el flujo que en producción llegaría por una cola). La base del proyecto no se toca.
- **Lote diario sin datos nuevos** repite la misma lista: es correcto y se enseña (idempotencia); para que cambie, la demo de «llegan datos» mueve el corte o usa el Excel completo (D2).
- **Entrenamiento:** hoy registra siempre una versión en MLflow, sin puerta ni alias; la puerta la pone `nueva-version.yml` con `referencia.json`, y al publicar se pone el alias `produccion` en el registro del artefacto.
- **Taller:** la cabecera de su `nueva-version.yml` dice que la publicación nunca se ejecutó, pero se ejecutó el 14/11/2026 (rechazada con tolerancia 0,02, aprobada con 0,10, publicación en GHCR y PR nº 1): la cabecera está desfasada.

## 5. Configuración que hace el administrador del repositorio (una vez, con el instructor)
Igual que en el taller: *environment* `produccion` con revisores; permiso para que Actions cree PR; visibilidad de los paquetes de GHCR. Se documenta con capturas. Nada de esto se hace sin la orden del instructor.

## 6. Riesgos
| Riesgo | Mitigación |
|---|---|
| Un *fork* no tiene `schedule` activo ni el *environment* | La guía lo dice; el alumno lo lanza con `workflow_dispatch`; el *environment* lo crea el alumno en su fork |
| GHCR privado por defecto | Paso documentado; prueba de que se descarga sin sesión |
| Cuota de Codespaces (el 20/11 se detuvo dos veces) | Los modos 2 y 3 también se prueban en Actions (compose) con capturas; el panel se puede abrir en local |
| Datos «nuevos» poco realistas | D2: usar el Excel completo frente a la muestra, o simular meses nuevos con cortes posteriores |
| Diferencias lote / en línea | Prueba que compara las tres rutas para los mismos clientes y corte |

## 7. Decisiones del instructor (22/11/2026)
1. **D1 · Dónde vive la versión en producción:** sin respuesta → se aplica la recomendación: imagen en GHCR + `models/referencia.json`.
2. **D2 · Datos de una versión nueva:** sin respuesta → recomendación: muestra → Excel completo (medir tiempos en Actions; si no cabe, simular meses nuevos moviendo el corte).
3. **D3 · Interfaz:** sin respuesta → recomendación: ampliar la interfaz de consulta con el panel.
4. **D4 · Ubicación:** **decidido: laboratorio de cierre de S4** → `01-Sesiones/S4-Orquestacion-y-CI-CD/laboratorio-produccion-e2e/`.
5. **D5 · Frecuencia del lote:** **decidido: diaria** (`schedule` diario; en un fork no se activa solo: se lanza a mano).
