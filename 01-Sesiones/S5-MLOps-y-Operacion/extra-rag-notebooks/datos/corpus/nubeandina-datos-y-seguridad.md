# NubeAndina: política de datos, privacidad y seguridad

Política interna de la empresa ficticia NubeAndina S.A.C. Define dónde pueden vivir
los datos de clientes, cómo se autentican las personas y a quién se consulta en caso
de duda. Las cifras y nombres son inventados y sirven como hechos recuperables.

## Residencia de los datos

Los datos de clientes y de cooperativas **no pueden salir de la región
`southamerica-west1`** de Google Cloud (Santiago). Está prohibido copiar conjuntos de
producción a un portátil, a un Codespace personal o a una región de Estados Unidos
«porque el modelo entrena más rápido». Para experimentos se usa un conjunto
anonimizado llamado **`cosechanet-lab-2026`**, publicado en el bucket interno
`gs://nubeandina-lab-anon`.

Las copias de seguridad se replican dentro de la misma región, en otra zona. No hay
réplica transoceánica de datos de clientes.

## Responsable de protección de datos

La Delegada de Protección de Datos (DPO) es **Elena Quispe**. El correo interno de
consulta es `privacidad@nubeandina.example` (dominio de ejemplo, no real). Una
solicitud de acceso o de borrado de una cooperativa se responde en un plazo máximo
de **15 días laborables**.

No se envían ficheros de clientes por correo, ni siquiera a un integrante del equipo.
Se comparte un acceso temporal en el proyecto de GCP, con caducidad de 24 horas y
registro en la bitácora.

## Contraseñas y acceso

- Longitud mínima de contraseña: **14 caracteres**.
- Rotación: cada **180 días**.
- El segundo factor es obligatorio para cualquier cuenta que toque GCP, GitHub de la
  empresa o *Huella*.
- Está prohibido reutilizar la contraseña de NubeAndina en servicios personales.

Las claves de servicio de GCP no se guardan en el repositorio. Viven en el gestor
interno de secretos. Un secreto filtrado se rota el mismo día y se notifica a Elena
Quispe y a Pedro Villanueva.

## Modelos y trazabilidad

Un modelo que se sirva en `gke-prod-andina-01` debe tener un identificador de
experimento, un conjunto de datos versionado y un alias de registro (`champion` o
equivalente). No se despliegan cuadernos sueltos como servicio de producción.

Está prohibido enviar datos reales de cooperativas a una API pública de un proveedor
(aunque sea «solo para probar un prompt»). Para generar texto se usa un modelo
interno o un entorno acordado, con registros de entrada y salida sin campos
directamente identificativos.

## Incidencias

Una sospecha de filtración se reporta en menos de una hora al canal `#seguridad` y
a la DPO. El simulacro anual de incidente se hace en **noviembre**. El de 2026 está
previsto para el **12 de noviembre**.

Cualquier cifra distinta (por ejemplo, «las contraseñas se rotan cada 30 días» o
«los datos pueden estar en `us-east1`») no pertenece a esta política.
