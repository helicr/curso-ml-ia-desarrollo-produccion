# Evidencia del avance 4 · pipeline orquestado con GitHub Actions

**Nombre:** …  **Fecha:** …  **Repositorio y rama:** … / `avance-4`  **Último commit:** …  **Tiempo dedicado (aprox.):** …

Se entrega a las 10:00 (hora de Perú) del viernes 27 de noviembre, con el formulario de Google del curso (según la hoja del caso). Esta evidencia es la que se presenta en S5. Lo que pide esta plantilla es lo que pide la [tarea](../tarea/README.md) y lo que mira la [rúbrica](../tarea/rubrica.md). Si algo no lo pudiste hacer, escríbelo: declararlo es parte de lo que se evalúa. No pegues claves, tokens, el ID de tu proyecto, tu correo ni el identificador de tu cuenta de facturación (tapa también las capturas).

## 1. Resultado
En cinco líneas como máximo: qué quedó funcionando y qué no.
…

## 2. El workflow
- Archivo: `.github/workflows/…`  · De qué plantilla partí (laboratorio, workflow de S3, otra) y qué cambié: …
- Qué lo dispara (`push`, `workflow_dispatch`) y en qué ramas: …
- Versiones fijadas (Python, librerías, `runs-on`) y cómo se instalan las dependencias (¿caché?): …
- `concurrency` y `timeout-minutes`, si los usé, y por qué: …

## 3. Las etapas

| Etapa | Trabajo (`job`) | Qué entra | Qué sale | Qué falla si se rompe |
|---|---|---|---|---|
| Datos | … | … | … | … |
| Entrenamiento | … | … | … | … |
| Métricas | … | … | … | … |
| Artefacto | … | … | … | … |

- Orden de los trabajos (`needs:`) y qué se pasa de uno a otro: …
- Cómo llegan los datos al runner (CSV en el repositorio, generados en el workflow, muestra de prueba…): …
- Artefactos que deja cada ejecución y cómo se descargan: …
- ¿Registré el modelo en MLflow? Cómo, y cómo salvé la carpeta (artefacto): …

## 4. Mis pruebas y comprobaciones
```
(pega aquí la salida de:  python -m pytest -q  en tu Codespace)
```

| Comprobación (prueba o puerta de calidad) | Qué regla de mi caso protege | ¿Falla si se rompe la regla? (cómo lo comprobé) |
|---|---|---|
| … | … | … |

## 5. Historial de ejecuciones

| | Commit | Enlace a la ejecución | Qué pasó |
|---|---|---|---|
| Rojo (provocado por una comprobación) | … | … | Comprobación que falló y línea del error: … |
| Verde (arreglo) | … | … | Qué cambié para arreglarlo: … |
| Verde al entregar (última de `avance-4`) | … | … | … |
| Otras ejecuciones relevantes | … | … | … |

- Cómo provoqué el rojo (rotura deliberada o fallo real): …
- Qué leí en el registro del workflow para saber qué fallaba: …

## 6. Fallos encontrados
Al menos dos. Separa los de infraestructura (YAML, dependencias, datos, permisos) de los de comprobación.

| # | Síntoma y línea del registro | Causa | Arreglo | Tipo (infraestructura / comprobación) |
|---|---|---|---|---|
| 1 | … | … | … | … |
| 2 | … | … | … | … |

- Diferencias entre mi Codespace y el runner, si las hubo: …

## 7. Permisos y secretos
- `permissions:` por trabajo, y por qué amplié alguno: …
- Secretos que usa (debería ser ninguno): …
- Comprobé que no hay claves, tokens ni `.env` en el repositorio: sí / no

## 8. Aprobación con *environment* (opcional)

| Qué | Hecho / sin hacer | Detalle |
|---|---|---|
| *Environment* con revisores creado (nombre exacto) | … | … |
| Comprobé que el trabajo **espera** (captura de «Review deployments», correo tapado) | … | … |
| Probé qué pasa si el *environment* no existe o tiene otro nombre | … | … |

## 9. Google Cloud (opcional)

| Qué | Hecho / sin hacer | Detalle (sin identificadores) |
|---|---|---|
| Entrada sin claves (WIF) | … | Variables usadas (no secretos): … |
| Lo que desplegué o subí | … | … |
| **Lo borré todo** (script o comandos usados) | … | Listados vacíos: … |
| Revisé la facturación | … | Sin importes ni identificadores: … |

- Si no pude: el motivo exacto (mensaje de error o paso que no se pudo dar): …

## 10. Una decisión
- **Contexto:** …
- **Opciones que consideré:** …
- **Evidencia** (enlaces a ejecuciones, métricas, tiempos del registro): …
- **Decisión:** …
- **Qué podría salir mal y qué haría después:** …

## 11. Lo que no pude hacer
Con el error exacto: …

## 12. Pasos para que otra persona lo reproduzca
1. …

## 13. Fuentes y ayuda recibida
- Dato: Moro, Rita y Cortez (2014), *Bank Marketing*, UCI Machine Learning Repository, https://doi.org/10.24432/C5K306 (licencia CC BY 4.0). Cambios que hice al dato: …
- Personas, documentación y herramientas (incluidas las de IA) que usé, y para qué: …
