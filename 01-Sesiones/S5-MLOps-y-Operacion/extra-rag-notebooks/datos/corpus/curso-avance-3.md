# Guía de entrega del Avance 3

El Avance 3 del curso *De Modelo a Producción* concentra el registro de experimentos
con MLflow y la integración continua con GitHub Actions. Esta guía detalla fechas,
formato y evidencias. Es un material original del taller.

## Fecha y canal

El Avance 3 se entrega el **viernes de la semana 4**, antes de las **23:59 hora de Lima**
(UTC-5). El único canal válido es Google Classroom, en la tarea titulada
«S3 · Tarea — Avance 3». No se aceptan envíos por correo, Drive compartido sin enlace
en Classroom, ni mensajes privados.

Si Classroom presenta una incidencia justificada, el equipo escribe al docente *antes*
de la hora de cierre y adjunta una captura del error. En ese caso excepcional se puede
usar un enlace de repositorio como respaldo, nunca como sustituto silencioso.

## Formato del PDF

- Extensión máxima: **8 páginas**, más una portada.
- Tipo de archivo: PDF. No se admite DOCX ni un enlace suelto a un cuaderno.
- Nombre del archivo: `Avance3_Apellido1_Apellido2.pdf`.
- La portada incluye: nombre del curso, número de equipo, integrantes, enlace al
  *fork* y hash del commit evaluado (los primeros 7 caracteres bastan).

La plantilla recomendada está en `01-Sesiones/S3-Despliegue-y-Redes-Neuronales/evidencias/plantilla-avance-3.md`
del repositorio oficial, rama `develop`.

## Evidencias mínimas

El PDF debe incluir, en este orden:

1. Objetivo del experimento y hipótesis (qué se compara y por qué).
2. Captura del experimento MLflow llamado **`retencion-clientes`**, con al menos dos
   *runs* etiquetados (por ejemplo `baseline` y `candidato`).
3. El *tracking URI* usado en el laboratorio, que por defecto es `http://127.0.0.1:5000`.
4. El modelo registrado en el Model Registry de MLflow con el alias **`champion`**.
5. El identificador del workflow de GitHub Actions: **`ci-retencion.yml`**. Debe
   aparecer una captura de una ejecución en verde (o una explicación de un fallo
   corregido, con la ejecución posterior en verde).
6. Cobertura de pruebas: el umbral del flujo de CI es **80 %**. Si la cobertura queda
   por debajo, el Avance 3 se considera incompleto.
7. Una sección breve de «lo que no funcionó» (media página). No se penaliza un
   problema bien documentado; se penaliza ocultarlo.

## Qué no es necesario

No hace falta un clúster real de Kubernetes en este avance. El manifiesto de ejemplo
y `kind` se trabajan en la sesión de despliegue, pero no son evidencia obligatoria del
Avance 3. Tampoco se exige GPU ni un servicio de pago de MLflow en la nube.

## Criterios de rúbrica (resumen)

- Trazabilidad (commit, experimento, alias `champion`): 8 puntos.
- Calidad del análisis de los *runs*: 6 puntos.
- CI en verde y cobertura ≥ 80 %: 4 puntos.
- Claridad del PDF: 2 puntos.

Total del avance: 20 puntos, que luego ponderan el 25 % de la nota del curso.
