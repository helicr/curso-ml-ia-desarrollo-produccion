# Material del laboratorio extra de S2

El laboratorio está en [`../laboratorio-extra-de-punta-a-punta.md`](../laboratorio-extra-de-punta-a-punta.md).

| Archivo | Qué es |
|---|---|
| `img/de-punta-a-punta.svg` | El diagrama del recorrido (ingesta → modelo → servicio → explotación → ciclo). |
| `capturar.py` | Ejecuta el laboratorio entero en una carpeta temporal (no toca tus datos) y guarda las salidas reales. `python 01-Sesiones/S2-API-y-Docker/practica/extra/capturar.py` (con `--sin-completo` se salta los datos nuevos). |
| `salidas-reales.json` | Las salidas de la ejecución de referencia (Windows 11, 13/11/2026), de las que salen las del laboratorio. |

El código nuevo del proyecto: `04-Proyecto-Base/ia_mlops/explotacion.py` (puntuación por lotes y campaña) y su prueba `tests/test_explotacion.py`.
