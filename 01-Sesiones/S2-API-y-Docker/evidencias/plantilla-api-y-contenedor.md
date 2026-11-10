# Evidencia S2 · API, contenedor y comparación

**Nombre:** …  **Fecha:** …  **Ruta:** A (Online Retail II) / B (mi caso)  **Rama / carpeta:** …

## 1. Punto de partida
Modelo y caso: … · Variable(s) que entran al servicio: `…` · Cómo las incorporé (merge, receta…): …

## 2. Qué dijo la API antes de actualizar el contrato
Mensaje exacto de `/listo` y de `/predecir` con el esquema viejo (código y texto):
```
(pega aquí la respuesta)
```

## 3. El contrato
| Campo | Tipo | Límites | Por qué estos límites (cómo se calcula la variable) |
|---|---|---|---|
| `…` | … | … | … |

Regla(s) de coherencia con otras variables: …

## 4. Qué rechaza y qué solo avisa
| Caso | Código | Mensaje | ¿Por qué rechazar / avisar? |
|---|---|---|---|
| … | 422 | … | … |
| … | 200 con advertencia | … | … |

## 5. Pruebas
```
(pega aquí la salida de:  python -m pytest -q  )
```
Mis pruebas nuevas (archivo, nombre y qué comprueban): …

## 6. El contenedor
- Cómo lo construí (Codespace / CI / otro): …
- `docker image ls` (tamaño): …
- `/listo` y una predicción dentro del contenedor: …
- `docker exec … id -u`: …
- Qué contiene la imagen y qué dejé fuera (y cómo lo comprobé): …

## 7. El workflow
Enlace o texto del registro de una ejecución en verde, con el paso «Probar el contenedor»: …

## 8. Comparación de caminos
```
(pega aquí la salida de:  python -m ia_mlops.modeling.comparar --url http://127.0.0.1:8080  )
```
¿Alguna diferencia distinta de cero? ¿Cuál fue la causa? …

## 9. Límites y riesgos
Qué no pude comprobar, qué podría fallar en producción, qué haría con más tiempo: …

## 10. Dificultades
Error exacto y cómo lo resolví (o por qué no): …

## 11. Reproducir
Comandos, en orden: …

## 12. Ayuda recibida
Personas o herramientas: …
