# Guía de MLflow en el laboratorio

MLflow es la herramienta que usamos en el curso para dejar rastro de los experimentos:
parámetros, métricas, artefactos y, más adelante, un modelo registrado. Este texto es
original del taller y describe el convenio del aula, no un manual completo del producto.

## Qué problema resuelve

Entrenar un modelo sin registro es como cocinar sin anotar la receta. A la semana no
sabemos con qué tasa de aprendizaje, con qué umbral ni con qué archivo de datos se
obtuvo «aquel» resultado. MLflow guarda esa receta de forma reproducible.

## Convenio del curso

- *Tracking URI* por defecto en el portátil: **`http://127.0.0.1:5000`**.
- Nombre del experimento: **`retencion-clientes`**.
- En el Model Registry, el modelo que el equipo declara como listo para la API lleva
  el alias **`champion`**. Un candidato en evaluación puede llevar el alias `challenger`.
- Cada *run* debe tener un nombre legible (`baseline`, `sin-clase-desbalanceada`,
  `umbral-0.35`, etc.). Un hash suelto sin comentario no ayuda al revisor.

Para levantar la interfaz en el laboratorio:

```
mlflow ui --backend-store-uri sqlite:///mlruns.db --port 5000
```

El navegador se abre en `http://127.0.0.1:5000`. Si el puerto está ocupado, no cambies
de URI en silencio: documenta el puerto real en el PDF del Avance 3.

## Qué se registra en cada *run*

Como mínimo:

- Parámetros: tipo de modelo, hiperparámetros relevantes, semilla (en este curso la
  semilla por defecto es 42), versión del conjunto de datos.
- Métricas: *recall* de la clase positiva, *precision*, F1 y, si aplica, el área bajo
  la curva PR. En retención, un accuracy alto puede esconder que no detectamos bajas.
- Artefactos: matriz de confusión, un pequeño informe en Markdown y el bundle del
  modelo (por ejemplo con `mlflow.sklearn.log_model`).

No registres un secreto ni un volcado de datos personales de clientes.

## De un *run* a la API

La API del proyecto no debería cargar un pickle suelto con un nombre mágico. El
convenio es: la API apunta al alias `champion` del registro (o a una copia versionada
exportada desde ese alias). Así, promover un modelo es cambiar el alias, no reescribir
a mano una ruta en el servidor.

## Errores frecuentes en el aula

1. Levantar MLflow en un directorio distinto al del proyecto y «perder» los *runs*.
2. Olvidar fijar el experimento (`mlflow.set_experiment("retencion-clientes")`) y
   dejarlo todo en `Default`.
3. Registrar el modelo pero no asignar el alias `champion`.
4. Apuntar el *tracking URI* a un servicio remoto de pago que el equipo no va a
   poder demostrar en la defensa. En este avance, local basta.

## Relación con el resto del curso

MLflow no sustituye a Git. El código y la configuración van al repositorio; las
métricas y los artefactos pesados van al *tracking store*. Tampoco sustituye a
Docker: el modelo campeón se empaqueta después en `retencion-api:local`.
