# Guía · Docker, Kubernetes y GKE

Para S2 (Docker) y S3 (Kubernetes y GKE). Conceptos con dibujos, una **práctica real con kind** en el Codespace del curso, cómo sería en **GKE**, chuleta y ejercicios.

| Archivo | Qué es |
|---|---|
| `index.html` | Las diapositivas (34). Doble clic, sin conexión. ← → avanzar, **O** índice, **S** notas, **F** pantalla completa; el botón **⧉** copia cada bloque de comandos. **No se edita a mano**: sale de `plantilla.html`. |
| `plantilla.html` | La fuente de las diapositivas. Las marcas `<!--CAPTURA nombre|pie-->` se sustituyen por las capturas. |
| `generar.py` | `python generar.py` → `index.html` (incrusta `capturas/*.webp`). |
| `capturas/` | 16 capturas de la terminal del Codespace durante la práctica (13/11/2026). |
| `chuleta.md` | Vocabulario, Docker, kind, kubectl, estados y GKE, para imprimir. |
| `ejercicios.md` | Seis ejercicios con solución desplegable; cada uno dice si se comprobó. |
| `pruebas/test_guia.py` | Lo generado está al día, cada captura existe y se usa, los comandos casan con los manifiestos y la guía declara lo no probado. |

Manifiestos de la práctica: `04-Proyecto-Base/deploy/kubernetes/deployment.yaml` y `service.yaml` (2 réplicas, sin root, readiness `/listo`, liveness `/salud`).

## Bloques
- **A · Conceptos (10):** el mapa de código a GKE, Docker en un dibujo y su chuleta, por qué Kubernetes, las piezas (clúster, nodo, Deployment, ReplicaSet, pod, Service), declarativo frente a imperativo, el `deployment.yaml` comentado, readiness y liveness, kind frente a GKE.
- **B · Práctica con kind (18):** crear el clúster, cargar la imagen, desplegar, eventos y registros, hablar con la API (`port-forward` y `comparar`), autocuración, escalar y ver que el YAML manda, una actualización rota que no tira el servicio, `rollout undo`, una readiness rota y limpiar; y «Si algo falla».
- **C · GKE (3):** qué cambia, los comandos (Artifact Registry, Autopilot, LoadBalancer, borrar) y coste y cuidado.
- **D · Ejercicios, chuleta y fuentes (3).**

## Qué se probó y qué no
- **Probado en el Codespace del curso (13/11/2026, 2 núcleos):** toda la práctica B con kind v0.27.0 (Kubernetes v1.32.2) y kubectl v1.37.2, con la imagen del bloque 4 de S2. Tiempos: crear el clúster 1 min 4 s, cargar la imagen 42 s, desplegar unos 10 s, borrar 25 s. Hallazgos que la guía recoge: `port-forward service/…` muere si se borra el pod por el que iba; `rollout undo` avisa de que no actualiza la anotación de `apply`.
- **Sin ejecutar:** GKE, Artifact Registry, `docker push`, el Service `LoadBalancer` e IAM (comandos de la documentación oficial, consultada el 13/11/2026); los ejercicios 4 y 5 (solución según el código del proyecto y la documentación de Kubernetes).

## Regenerar y probar
```text
python 03-Entorno/guia-docker-kubernetes-gke/generar.py
python -m pytest 03-Entorno/guia-docker-kubernetes-gke/pruebas -q
```
