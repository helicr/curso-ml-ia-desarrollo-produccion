# De on-premise a la nube

Guía en texto de la clase de apoyo «De on-premise a la nube» del curso «ML e IA: de desarrollo a producción». Es el mismo contenido que la presentación (`index.html`), con las notas del ponente al final de cada apartado. Los nombres, regiones y condiciones de Google Cloud se consultaron en su documentación pública el 25/11/2026; lo que no se pudo comprobar dice «sin dato». **Nada de lo que aquí aparece se ha ejecutado en Google Cloud**: las órdenes son plantillas.

## 1. Por qué la nube

### 1. De on-premise a la nube

Qué es la nube y por qué se usa, quiénes son los tres grandes proveedores, cómo se organiza **Google Cloud** y qué pasaría con lo que hemos construido en el curso si lo lleváramos allí: **nuestro Cloud Journey**.

Nube públicaAWS · Azure · Google CloudCloud Run · BigQuery · Vertex AICostes

**Cómo seguirla**

**← →** avanzan · **O** índice · **S** notas del ponente (con las fuentes) · **F** pantalla completa. Todo está también en texto en guia.md. Las cifras y nombres de Google Cloud se consultaron en su documentación pública el 25/11/2026; lo que no se pudo comprobar dice «sin dato».

> **Para el ponente.** Clase de apoyo, orientada a lo que se ha visto en el curso: pipeline raw, master, fs y ml, API con FastAPI, imagen Docker, MLflow y SQLite en local, y GitHub Actions con GHCR en la nube de GitHub. Objetivo: que cada persona entienda el mapa de la nube y pueda decir qué pieza de nuestro caso iría a qué servicio, con qué esfuerzo y con qué cuidado de costes. No se ha ejecutado nada en Google Cloud para preparar esta clase: todo lo de la nube viene de documentación pública, citada en las notas.

### 2. Lo que ya tenemos es nuestro «on-premise» simulado

**Datos**

Archivos en data/raw y la base **SQLite** con las capas raw_, master_, fs_ y ml_.

**Modelo**

Entrenamiento con scikit-learn y seguimiento en **MLflow** con SQLite y una carpeta local.

**Servicio**

API **FastAPI** en una imagen **Docker**, e interfaz que lee la base en solo lectura.

**Entrega**

**GitHub Actions** publica la imagen en **GHCR**, con un environment que exige aprobación.

**On-premise** significa «en instalaciones propias»: servidores que compras, instalas y mantienes tú. Nuestro portátil o Codespace hace de ese entorno.

**La pregunta de la clase:** si mañana hubiera que llevar esto a producción real en una empresa, ¿qué se movería a la nube, a qué servicio y con qué cuidado?

**Cómo está organizada la clase**

- 1 · Por qué la nube

- 2 · Los tres grandes

- 3 · Google Cloud

- 4 · Servicios

- 5 · Cloud Journey

- 6 · Costes

> **Para el ponente.** Recapitulación de lo construido, para anclar la clase en el caso conocido. La interfaz abre la SQLite en solo lectura; la API no lee datos: el modelo va dentro de la imagen (así se describe en la teoría de S3). Esto es lo que llamamos on-premise simulado: la situación de partida de muchos equipos, que ya tienen cosas funcionando y se preguntan cómo llevarlas a la nube sin romperlas. Sin cifras en esta diapositiva.

### 3. On-premise frente a nube: de comprar capacidad a pagar por uso

|  | On-premise | Nube pública |
|---|---|---|
| Dinero | CAPEX: inversión inicial en equipos | OPEX: gasto corriente por uso |
| Capacidad | se compra para el pico y se queda fija | elástica: sube y baja con la demanda |
| Plazo | semanas o meses hasta tener el equipo | minutos para crear un recurso |
| Mantenimiento | tuyo: hardware, parches, centro de datos | el proveedor se ocupa de la infraestructura |
| Servicios | los instalas y operas tú | gestionados: bases de datos, ML, colas… |
| Riesgo | quedarse corto o pagar capacidad sin usar | olvidar apagar y que el gasto crezca |

**Elasticidad** es poder aumentar o reducir recursos casi al instante. Es la ventaja principal; el riesgo asociado son los costes, por eso hay una parte entera sobre ellos.

*Esquema: Gráfica conceptual: la capacidad fija on-premise queda por encima de la demanda casi todo el tiempo; en la nube se paga solo la curva de demanda*

> **Para el ponente.** CAPEX (capital expenditure) es la inversión inicial en activos, como comprar servidores; OPEX (operating expenditure) es el gasto corriente, como pagar por lo consumido cada mes. La gráfica es una ilustración conceptual construida a mano para este curso: no representa datos reales ni mide ahorros; no se afirma que la nube sea siempre más barata (depende de cuánto se use y de cómo se opere). Concepto general, sin fuente numérica.

### 4. Cuanto más gestionado el servicio, menos te toca administrar

| Capa | On-premise | IaaS | PaaS | Serverless | SaaS |
|---|---|---|---|---|---|
| Aplicación | tú | tú | tú | tú (tu código o imagen) | proveedor |
| Datos | tú | tú | tú | tú | tú (tu contenido) |
| Entorno de ejecución | tú | tú | proveedor | proveedor | proveedor |
| Sistema operativo | tú | tú | proveedor | proveedor | proveedor |
| Servidores y virtualización | tú | proveedor | proveedor | proveedor | proveedor |
| Red, almacenamiento y centro de datos | tú | proveedor | proveedor | proveedor | proveedor |
| Ejemplos | tu sala de servidores | Compute Engine, Amazon EC2, Azure Virtual Machines | Cloud SQL, App Engine | Cloud Run, AWS Lambda, Azure Functions | Google Workspace, Microsoft 365 |

lo gestionas tú lo gestiona el proveedor

**Responsabilidad compartida**

El proveedor protege **la nube** (instalaciones, hardware, red base); tú proteges **lo que pones en ella**: identidades, permisos, datos y configuración. Cuanto más a la derecha, más cosas hace el proveedor, pero **tus datos y tus accesos siguen siendo tuyos**.

En el curso usaremos sobre todo **serverless con contenedores** (Cloud Run) y servicios **gestionados** (BigQuery, Cloud Storage), no máquinas virtuales.

> **Para el ponente.** La tabla simplifica: en la práctica hay matices (un servicio PaaS permite configurar parte del entorno de ejecución, y serverless suma escalado automático, incluso a cero, y pago por uso). IaaS es infraestructura como servicio, PaaS plataforma como servicio, SaaS software como servicio. El modelo de responsabilidad compartida es un concepto general de todos los proveedores; no se cita una fuente numérica. Los ejemplos son nombres de producto reales de cada proveedor.

### 5. Siglas y palabras que van a aparecer

| Palabra | Qué es |
|---|---|
| CAPEX / OPEX | Capital expenditure: inversión inicial. Operating expenditure: gasto corriente por uso |
| IaaS / PaaS / SaaS | Infraestructura, plataforma o software como servicio: cuánto gestiona el proveedor |
| región y zona | una región es una zona geográfica con centros de datos; una zona es una parte aislada dentro de ella. Se elige dónde viven tus recursos |
| SLA | Service Level Agreement: compromiso escrito del proveedor sobre la disponibilidad de un servicio |
| IAM | Identity and Access Management: quién (identidad) puede hacer qué (rol) sobre qué recurso |
| cuenta de servicio | identidad para un programa, no para una persona; se le dan solo los permisos que necesita |
| WIF | Workload Identity Federation: un programa de fuera de Google Cloud (como GitHub Actions) entra sin claves guardadas |
| API (de un servicio) | además de «nuestra API», cada servicio de Google Cloud se activa y se maneja por una API que hay que habilitar |
| FinOps | práctica de vigilar y optimizar el gasto en la nube entre técnica y finanzas |

> **Para el ponente.** Vocabulario mínimo. Insistir en tres: región y zona, porque de ahí sale el coste y la latencia; IAM y cuenta de servicio, porque la seguridad en la nube es sobre todo identidad; y WIF, que veremos con GitHub Actions. FinOps se menciona solo como idea. Definiciones generales, sin cifras.

## 2. Los tres grandes

### 6. Tres hiperescalares y algunos más

**Amazon Web Services**

**AWS**, de Amazon. Infraestructura, datos e IA como servicio, con presencia en todo el mundo.

ML: **Amazon SageMaker** · LLMs: **Amazon Bedrock**

**Microsoft Azure**

**Azure**, de Microsoft. Se integra con Microsoft 365 y con el directorio de identidades **Microsoft Entra ID**.

ML: **Azure Machine Learning** · LLMs: **Azure OpenAI**

**Google Cloud**

**GCP**, de Google. Destaca en datos (**BigQuery**), contenedores (**Kubernetes** lo creó Google) e IA.

ML: **Vertex AI** · LLMs: **Gemini**

**Qué es un hiperescalar**

Un proveedor con centros de datos repartidos por el mundo en **regiones**, un catálogo muy amplio de servicios, pago por uso y todo accesible por API. Hay otros: **Oracle Cloud Infrastructure**, **IBM Cloud** y **Alibaba Cloud**.

**Cuál elegir**

No hay una respuesta única: depende de **dónde están ya los datos y la identidad de la empresa**, de los servicios que se necesitan, del coste y de la región. Muchas empresas usan **más de una** (multinube). Cuota de mercado: **sin dato** verificado aquí; cambia cada trimestre y hay que citar un informe con fecha.

> **Para el ponente.** Los tres nombres y sus servicios de ML y LLMs son los de la tabla de la diapositiva siguiente. Sobre Kubernetes: lo creó Google y hoy es un proyecto abierto; Google Kubernetes Engine es su servicio gestionado. Cuotas de mercado, número de regiones y precios: no se citan porque no se han verificado en esta preparación; si alguien las pregunta, remitir a un informe de analistas con fecha o a la página de ubicaciones de cada proveedor. Nombres de producto: Amazon SageMaker AI (renombrado de SageMaker el 3/12/2024) y Azure OpenAI en Microsoft Foundry; para abreviar usamos los nombres cortos. Fuentes (consultadas el 25/11/2026): AWS · What is Amazon SageMaker AI, https://docs.aws.amazon.com/sagemaker/latest/dg/whatis.html; Microsoft Learn · Foundry Models sold by Azure, https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure.

### 7. Servicios equivalentes: cómputo, imágenes, datos

| Necesidad en nuestro caso | Hoy en el curso | AWS | Azure | Google Cloud |
|---|---|---|---|---|
| Máquina virtual | tu equipo | Amazon EC2 | Azure Virtual Machines | Compute Engine |
| Contenedores sin servidores | docker run | AWS App Runner, Amazon ECS con AWS Fargate | Azure Container Apps | Cloud Run |
| Kubernetes gestionado | solo demo del instructor | Amazon EKS | Azure Kubernetes Service (AKS) | Google Kubernetes Engine (GKE) |
| Registro de imágenes | GHCR | Amazon ECR | Azure Container Registry | Artifact Registry |
| Almacenamiento de objetos | carpeta data/raw | Amazon S3 | Azure Blob Storage | Cloud Storage |
| Base de datos relacional | SQLite | Amazon RDS | Azure SQL Database | Cloud SQL |
| Data warehouse | SQLite (capas) | Amazon Redshift | Azure Synapse Analytics | BigQuery |

En **negrita** los servicios de Google Cloud que usaría nuestro Cloud Journey. «Equivalente» no es «idéntico»: cambian límites, precios y detalles de manejo.

> **Para el ponente.** Primera mitad de la tabla de equivalencias. Los nombres de AWS y Azure son nombres de producto reales; se escribieron los nombres cortos habituales. Azure Synapse Analytics sigue descrito como servicio en su documentación (versión de 2025), aunque Microsoft también ofrece Microsoft Fabric para analítica; no se compara aquí. Para Spark gestionado en Azure se cita Azure Databricks; Synapse también ofrece Spark. No se comparan precios ni rendimiento. Fuente (consultadas el 25/11/2026): Microsoft Learn · What is Azure Synapse Analytics, https://learn.microsoft.com/en-us/azure/synapse-analytics/overview-what-is.

### 8. Servicios equivalentes: ML, LLMs, entrega y operación

| Necesidad en nuestro caso | Hoy en el curso | AWS | Azure | Google Cloud |
|---|---|---|---|---|
| Spark gestionado | no se usa (solo mención) | Amazon EMR | Azure Databricks | Dataproc |
| Plataforma de ML | MLflow local | Amazon SageMaker | Azure Machine Learning | Vertex AI |
| LLMs gestionados | fuera del curso base | Amazon Bedrock | Azure OpenAI | Gemini en Vertex AI |
| CI/CD | GitHub Actions | AWS CodePipeline y CodeBuild | Azure DevOps Pipelines | Cloud Build (o GitHub Actions) |
| Identidad y permisos | tu usuario | AWS IAM | Microsoft Entra ID y Azure RBAC | Cloud IAM |
| Secretos | archivo .env | AWS Secrets Manager | Azure Key Vault | Secret Manager |
| Monitorización y registros | logs en la salida estándar | Amazon CloudWatch | Azure Monitor | Cloud Logging y Monitoring |

Fíjate en la columna «Hoy en el curso»: casi todo lo que usamos tiene su equivalente gestionado. Lo que no se usa (Spark, LLMs) se queda en una mención.

> **Para el ponente.** Segunda mitad de la tabla. La plataforma de ML de AWS se llama hoy Amazon SageMaker AI (era Amazon SageMaker hasta el 3 de diciembre de 2024); Bedrock aparece dentro de la familia Amazon SageMaker según su documentación. La oferta de LLMs de Azure se documenta hoy como Azure OpenAI en Microsoft Foundry. En Google Cloud, Gemini se usa a través de Vertex AI. Fuentes (consultadas el 25/11/2026): AWS · What is Amazon SageMaker AI, https://docs.aws.amazon.com/sagemaker/latest/dg/whatis.html; Microsoft Learn · Foundry Models sold by Azure, https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure.

## 3. Orientado a Google Cloud

### 9. Organización, carpetas, proyectos y recursos

*Esquema: Jerarquía de recursos de Google Cloud: organización, carpetas, proyectos y recursos; los permisos se heredan hacia abajo*

**El proyecto es la unidad de trabajo**

- Todo recurso vive en **un proyecto**; sin proyecto no hay servicios, ni APIs, ni facturación.

- Un proyecto tiene un **ID único**, un nombre y **etiquetas** (labels) para filtrar.

- Los permisos y las políticas se **heredan** de arriba abajo.

- La **organización** requiere Google Workspace o Cloud Identity; una cuenta personal de prueba puede tener proyectos sin organización.

**Región y zonas**

**southamerica-west1** · Santiago, Chile

-a-b-c

Una **región** son varias **zonas** aisladas. Compute Engine lista tres zonas en Santiago.

> **Para el ponente.** La jerarquía es la de la documentación de Resource Manager: organización, carpetas (opcionales), proyectos y recursos; las políticas de permisos se heredan hacia abajo. Los nombres de carpetas y proyectos del dibujo son inventados como ejemplo. La organización requiere una cuenta de Google Workspace o de Cloud Identity; los usuarios de prueba gratuita o de nivel gratuito pueden tener proyectos sin padre. Las zonas de southamerica-west1 son a, b y c según la tabla de regiones y zonas de Compute Engine. Fuentes (consultadas el 25/11/2026): Resource Manager · Resource hierarchy, https://docs.cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy; Compute Engine · Regions and zones, https://docs.cloud.google.com/compute/docs/regions-zones.

### 10. Identidad: quién puede hacer qué, y sin claves guardadas

*Esquema: Workload Identity Federation: GitHub Actions presenta su token OIDC a Google STS, que lo cambia por acceso temporal de una cuenta de servicio con permisos mínimos sobre Artifact Registry, Cloud Run y Cloud Storage*

**IAM**

Una **identidad** (persona, grupo o cuenta de servicio) recibe un **rol** (conjunto de permisos) **sobre un recurso**. Regla de oro: el **mínimo privilegio**.

**Cuenta de servicio**

La identidad de **un programa**: la API en Cloud Run se ejecuta con una cuenta de servicio que solo puede leer lo que necesita.

**Workload Identity Federation**

GitHub Actions presenta su propio token a Google, que lo cambia por **acceso temporal**. Se evitan las **claves de cuenta de servicio**, que son credenciales potentes y un riesgo si se guardan mal.

> **Para el ponente.** WIF permite que cargas de trabajo de fuera de Google Cloud, entre ellas pipelines de CI/CD como GitHub, accedan con identidades de un proveedor externo en lugar de claves de cuenta de servicio; el intercambio sigue el estándar OAuth 2.0 token exchange, mediante pools de identidades y proveedores (GitHub figura entre los admitidos). La documentación recomienda dar acceso directamente sobre recursos o suplantar una cuenta de servicio con un token de corta vida. El dibujo es un esquema simplificado hecho para esta clase. En el curso, esto es el paso de «tu usuario y una clave» a «cuenta de servicio sin claves» (refactor). Fuente (consultadas el 25/11/2026): IAM · Workload Identity Federation, https://docs.cloud.google.com/iam/docs/workload-identity-federation.

### 11. Qué hace falta para empezar en Google Cloud

**Los cinco pasos**

- **Cuenta de Google** (personal o de empresa)

- **Proyecto**, mejor desechable para aprender

- **Facturación**: cuenta de facturación vinculada (la prueba gratuita pide un medio de pago)

- **Habilitar las APIs** de los servicios que vas a usar

- **Herramienta**: gcloud

en tu equipo o **Cloud Shell** en el navegador

**Antes de crear nada:** un presupuesto con alertas. Se explica en la parte de costes.

Terminal · plantilla (cambia los valores en MAYÚSCULAS; sin ejecutar en esta clase)

$ `gcloud auth login`

$ `gcloud config set project ID_PROYECTO`

$ `gcloud config set run/region southamerica-west1`

$ `gcloud billing projects link ID_PROYECTO --billing-account=ID_FACTURACION`

$ `gcloud services enable run.googleapis.com artifactregistry.googleapis.com storage.googleapis.com bigquery.googleapis.com secretmanager.googleapis.com aiplatform.googleapis.com`

**Habilitar una API**

Cada servicio llega por una API que se **habilita por proyecto**: un servicio sin habilitar da error de permiso aunque tengas el rol correcto.

> **Para el ponente.** Los cinco pasos son el flujo habitual; los comandos de gcloud son los de uso corriente (auth login, config set project, billing projects link, services enable) con valores de ejemplo en mayúsculas: no se han ejecutado para preparar esta clase. La documentación pública de la prueba gratuita indica que se crea una cuenta de facturación y un proyecto de ejemplo, y que se exige tarjeta u otro medio de pago válido durante la prueba. Cloud Shell figura entre los productos globales de la página de ubicaciones. Los nombres de las APIs (run, artifactregistry, storage, bigquery, secretmanager, aiplatform) siguen el patrón servicio.googleapis.com. Fuentes (consultadas el 25/11/2026): Google Cloud · Free cloud features, https://docs.cloud.google.com/free/docs/free-cloud-features; Google Cloud · Cloud locations, https://cloud.google.com/about/locations.

## 4. Los servicios que nos competen

### 12. Los servicios que nos competen, en un mapa

Datos

Cloud Storagearchivos y Parquet

BigQueryanalítica con SQL

Cómputo y contenedores

Artifact Registryimágenes

Cloud Runla API

GKEKubernetes

DataprocSpark

ML e IA

Vertex AIModel Registry

Vertex AIendpoints y pipelines

Model Gardeny Gemini

Entrega y seguridad

GitHub Actionscon WIF

Cloud BuildCI/CD de GCP

Secret Managersecretos

Cloud IAMpermisos

Operación y costes

Cloud Loggingregistros

Cloud Monitoringmétricas y alertas

Presupuestosy alertas de gasto

Son **dieciséis** recuadros, pero para nuestro caso solo hacen falta siete para empezar: **Cloud Storage, BigQuery, Artifact Registry, Cloud Run, Secret Manager, IAM y presupuestos**. El resto se suma después.

> **Para el ponente.** Mapa agrupado por función. Sirve de índice de las cuatro diapositivas siguientes. Para empezar en el caso del curso bastan siete servicios: lo mismo que se practica con los scripts de la teoría de S3 (archivos a Cloud Storage, tablas a BigQuery, imagen a Artifact Registry, servicio en Cloud Run, secreto en Secret Manager, cuenta de servicio y presupuesto). Sin cifras externas. El conteo «dieciséis» es el número de recuadros del mapa (Vertex AI aparece dos veces).

### 13. Datos y contenedores: para qué sirve cada uno en el curso

**Cloud Storage**

Qué es Almacenamiento de **objetos** en buckets: archivos de cualquier tipo, sin límite práctico de tamaño total.

En el curso Los archivos originales y los **Parquet** exportados de las tablas, con su huella SHA-256.

Hoy (local) carpeta data/raw

**BigQuery**

Qué es Almacén de datos **analítico** sin servidores: se consulta con **SQL** y se paga por almacenamiento y consultas.

En el curso Las capas master_, fs_ y ml_ como **copia analítica validada** de la SQLite.

Hoy (local) SQLite

**Artifact Registry**

Qué es Repositorio de **imágenes de contenedor** y paquetes dentro de tu proyecto, con permisos IAM.

En el curso La imagen retencion-api que hoy se publica en GHCR.

Hoy (local) GHCR (ghcr.io)

**Importante:** desplegar la API en la nube **no hace que lea BigQuery**. En el curso la API lleva el modelo dentro de la imagen; BigQuery recibe una copia analítica. Que el servicio consulte BigQuery sería un cambio de diseño (refactor).

**Cómo se sabe que los datos llegaron bien**

No basta con subirlos: se **valida** (mismos conteos, esquemas y agregados que en origen) y se comprueba la integridad. Cloud Storage informa de **MD5 y CRC32C**, no de SHA-256: por eso la huella SHA-256 se calcula en origen y se comprueba **descargando y recalculando**. Sin verificar hoy en la documentación vigente.

> **Para el ponente.** Las tres fichas siguen el mapa de equivalencias de la teoría de S3 (Cloud Storage para archivos, BigQuery para las capas, Artifact Registry para la imagen). La aclaración sobre la API que no lee BigQuery es la del propio material del curso. La afirmación de que Cloud Storage informa de MD5 y CRC32C pero no de SHA-256 está marcada en el material de S3 como sin verificar; aquí se mantiene esa marca. Las regiones donde existen estos servicios se tratan en la parte de costes.

### 14. Ejecutar el código: Cloud Run, GKE y Dataproc

**Cloud Run**

Qué es Ejecuta **contenedores** sin gestionar servidores: escala con las peticiones y puede **bajar a cero** instancias.

En el curso La **API FastAPI** (privada al principio), desplegada desde Artifact Registry.

Hoy (local) uvicorn o docker run

**GKE**

Qué es **Kubernetes** gestionado: tú decides más cosas (redes, nodos, versiones) y ganas control a cambio de operar más.

En el curso Alternativa a Cloud Run; en el curso solo hay una **demo del instructor**, sin ejecutar.

**Dataproc**

Qué es Clústeres de **Hadoop y Spark** gestionados para procesar volúmenes que no caben en una sola máquina.

En el curso Solo se **menciona**: nuestro conjunto de datos cabe en una máquina.

**¿Cloud Run o GKE?**

|  | Cloud Run | GKE |
|---|---|---|
| Qué gestionas | la imagen y su configuración | además, el clúster y sus nodos (según el modo) |
| Cuándo | una API o un trabajo en contenedor, sin demasiadas piezas | muchos servicios que se hablan entre sí, necesidades de red o de nodo especiales |
| Para nuestro caso | la opción de partida | solo si el crecimiento lo pide |

> **Para el ponente.** Cloud Run: contenedores sin servidores, con escalado automático; puede reducirse el mínimo de instancias a cero (así lo recomienda el material de S3 para no pagar sin uso). GKE y Dataproc se practican en las prácticas 02 y 03 (ejecutadas y borradas en Santiago el 25/11/2026). La comparación Cloud Run frente a GKE es una orientación general de la clase, no una recomendación oficial ni una medida.

### 15. Vertex AI: de registrar un modelo a servirlo

**Model Registry**

Qué es Catálogo de **versiones de modelos** con sus metadatos.

En el curso Sustituiría al registro de **MLflow** local, o convivirían.

Hoy (local) MLflow con SQLite y carpeta

**Endpoints**

Qué es Despliegue **gestionado** de un modelo para pedirle predicciones por red (en línea) o en lote.

En el curso El modo **online** de la clase de producción, como alternativa a Cloud Run.

**Pipelines**

Qué es Orquestación de pasos de entrenamiento y despliegue como flujo.

En el curso En el curso orquesta **GitHub Actions**; esto sería la otra vía.

**Model Garden**

Qué es Catálogo para descubrir y usar modelos, propios de Google, abiertos y de terceros.

En el curso Solo se menciona.

**Gemini en Vertex AI**

Qué es Modelos de lenguaje de Google accesibles por API desde la plataforma.

En el curso Fuera del caso base (el modelo de retención no es un LLM); útil para explicar resultados o agentes.

Nuestra pieza central, el **modelo de retención**, es un modelo clásico de scikit-learn: puede servirse en **Cloud Run** dentro de la imagen o desde un **endpoint de Vertex AI**. Elegir entre ambos es una decisión de diseño de la siguiente diapositiva.

> **Para el ponente.** Vertex AI agrupa varios servicios de ML. La documentación de ubicaciones lista Model Registry, predicción en línea y por lotes de modelos personalizados, entrenamiento y Pipelines entre las funciones disponibles en Santiago (diapositiva de regiones). La documentación actual presenta estas páginas bajo el nombre «Gemini Enterprise Agent Platform» aunque el producto y el SDK siguen llamándose Vertex AI; para esta clase se usa el nombre Vertex AI, que sigue vigente en las URL y en las funciones. Equivalencias con MLflow y GitHub Actions: las de la teoría de S3. Fuentes (consultadas el 25/11/2026): Vertex AI · Locations, https://docs.cloud.google.com/vertex-ai/docs/general/locations; Gemini en Vertex AI · Locations, https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/locations.

### 16. Servir el modelo: Cloud Run o endpoint de Vertex AI

|  | API en Cloud Run (lo que hace el curso) | Endpoint de Vertex AI |
|---|---|---|
| Qué despliegas | una imagen con el modelo dentro y tu código de API | un modelo registrado en Model Registry, con su contenedor de servicio |
| Quién controla el contrato | tú: rutas, validación y formato propios | más estándar y menos flexible: sigue el formato de predicción de la plataforma |
| Versionado | la etiqueta de la imagen (v2-<huella>) | las versiones del modelo en el registro |
| Pipeline de entrega | GitHub Actions construye, prueba y despliega | GitHub Actions o Vertex AI Pipelines registran y despliegan |
| Coste base | puede bajar a cero cuando no hay tráfico | sin dato aquí: depende de la configuración del endpoint |
| Encaja si | la API tiene lógica propia (nuestra interfaz, tres modos de explotación) | se quiere una solución gestionada para el modelo y su monitoreo |

**Para el curso:** Cloud Run primero (rehost de lo que ya funciona); el endpoint de Vertex AI cuando se quiera registro gestionado (lo hace la práctica 04: ojo, cobra mientras existe).

> **Para el ponente.** Comparación orientativa hecha para esta clase a partir de la arquitectura del curso; no son medidas ni una recomendación oficial. El coste de un endpoint de Vertex AI no se ha consultado: se deja «sin dato». La ventaja de Cloud Run de poder bajar a cero instancias es la del material de S3. Si alguien pregunta por el monitoreo de modelos, recordar que la lista de funciones de Vertex AI en Santiago no incluye Model Monitoring (ver diapositiva de regiones). Fuente (consultadas el 25/11/2026): Vertex AI · Locations, https://docs.cloud.google.com/vertex-ai/docs/general/locations.

### 17. Entrega, secretos y operación: lo que rodea al código

**GitHub Actions + WIF**

Qué es El flujo de entrega del curso, que se **autentica sin claves** contra Google Cloud.

En el curso Publica la imagen y despliega; el environment produccion exige aprobación.

**Cloud Build**

Qué es Servicio de CI/CD de Google Cloud: construye imágenes y ejecuta pasos en la nube.

En el curso Alternativa a GitHub Actions; en el curso orquesta GitHub Actions.

**Secret Manager**

Qué es Guarda secretos con **versiones** y permisos; un servicio los monta o los lee.

En el curso Sustituye al archivo .env. En la demo, un valor de ejemplo que el servicio no consume.

Hoy (local) archivo .env

**Cloud Logging**

Qué es Reúne los **registros** de los servicios, con búsqueda.

En el curso El registro JSON de la API ya sirve sin cambiar el código.

Hoy (local) líneas JSON por la salida estándar

**Cloud Monitoring**

Qué es **Métricas y alertas** sobre el estado de los servicios.

En el curso Avisar si la API falla; la deriva del modelo se vería en S5.

**Presupuestos y alertas**

Qué es Límites de **aviso** de gasto sobre una cuenta de facturación.

En el curso Se crean **antes** que cualquier recurso.

Hoy (local) hardware fijo

> **Para el ponente.** Cloud Build figura entre los productos globales (sin dependencia de ubicación) de la página de ubicaciones de Google Cloud. Cloud Monitoring también aparece como producto global, con escenarios regionales en su documentación. El tratamiento de Secret Manager con un valor de ejemplo y el registro JSON que ya sirve para Cloud Logging son los del material de S3. Un presupuesto de alertas no corta el gasto: ver la diapositiva de presupuestos. Fuente (consultadas el 25/11/2026): Google Cloud · Cloud locations, https://cloud.google.com/about/locations.

## 5. Nuestro Cloud Journey

### 18. AS-IS: lo que hay hoy

*Esquema: Arquitectura actual: pipeline, SQLite, MLflow, imagen Docker, API e interfaz en local, y GitHub Actions con GHCR y aprobación en GitHub*

**Qué funciona**

- Todo el flujo de datos, entrenamiento, API y entrega.

- La entrega ya es **automática y con aprobación**.

**Qué limita**

- Todo en **una máquina**: sin escalado ni disponibilidad.

- SQLite y MLflow locales no se comparten en equipo.

**Qué ya es «de nube»**

- **GitHub Actions** y **GHCR** ya corren en la nube de GitHub.

- La imagen Docker es **portable**: base del rehost.

> **Para el ponente.** AS-IS es «como está hoy». El dibujo recoge el caso real del curso: pipeline raw, master, fs y ml sobre SQLite; MLflow local; imagen Docker con el modelo dentro; API FastAPI; interfaz que lee la base en solo lectura; GitHub Actions publicando en GHCR con aprobación en el environment produccion. Dibujo propio hecho para esta clase, sin cifras.

### 19. TO-BE: cómo sería en Google Cloud

*Esquema: Arquitectura en Google Cloud: GitHub Actions despliega con identidad federada la imagen en Artifact Registry y Cloud Run; los datos van a Cloud Storage y BigQuery; el modelo, registrado y servido en Vertex AI (práctica 04)*

Qué cambia: **dónde viven los datos, la imagen y el servicio**. Qué **no** cambia: el código del pipeline, la API y el flujo de entrega en GitHub Actions; solo se autentica con WIF.

> **Para el ponente.** TO-BE es «como sería». Todo el proyecto queda en una sola región, southamerica-west1 (Santiago), por cercanía a los alumnos, pero ver en la diapositiva de regiones qué partes de Vertex AI están disponibles allí. Los datos van a Cloud Storage y BigQuery; la imagen a Artifact Registry y se despliega en Cloud Run; GitHub Actions entra con identidad federada. Model Registry y el endpoint de Vertex AI se practican en la práctica 04 (ejecutada y borrada el 25/11/2026). Dibujo propio, sin cifras.

### 20. Qué se mueve, a qué servicio y con qué esfuerzo

| Pieza | Hoy | En Google Cloud | Estrategia | Esfuerzo |
|---|---|---|---|---|
| Archivos originales | data/raw | Cloud Storage | Replatform | bajo |
| Capas master, fs y ml | SQLite | BigQuery (vía Parquet) y validación | Replatform | medio |
| Imagen de la API | GHCR | Artifact Registry | Rehost | bajo |
| Servicio de la API | uvicorn o docker run | Cloud Run | Rehost | bajo |
| Configuración sensible | archivo .env | Secret Manager | Replatform | bajo |
| Identidad de la entrega | usuario y claves | cuenta de servicio + WIF | Refactor | medio |
| Registros | salida estándar | Cloud Logging | Replatform | bajo |
| Seguimiento y registro de modelos | MLflow local | Vertex AI Model Registry | Replatform o refactor | alto |
| Servir el modelo online | API en Docker | endpoint de Vertex AI (opcional) | Refactor | alto |
| Orquestación | GitHub Actions | se mantiene (o Cloud Build / Vertex AI Pipelines) | Retener | bajo |

**Esfuerzo**: valoración cualitativa del profesor para este caso, **sin medir**. Vale como orden de magnitud para priorizar, no como estimación de proyecto.

> **Para el ponente.** Las filas y las estrategias vienen del mapa de equivalencias de la teoría de S3 y de la guía de migración del curso; se añaden el servicio de modelos de Vertex AI y la fila de orquestación. La columna de esfuerzo es una valoración cualitativa hecha para esta clase: bajo cuando no se toca el código, medio cuando hay que validar datos o cambiar la forma de autenticarse, alto cuando cambia la forma de registrar o servir el modelo. No hay cifras de horas ni de coste: sin dato.

### 21. Las «R» de la migración y cuál aplica a cada pieza

**Rehost**

Lift and shift: mover tal cual.

**Nosotros:** la imagen Docker y la API en Cloud Run.

**Replatform**

Mover con ajustes mínimos a un servicio gestionado.

**Nosotros:** SQLite a BigQuery, archivos a Cloud Storage, .env a Secret Manager.

**Refactor**

Rediseñar para aprovechar la nube.

**Nosotros:** claves a identidad federada; servir el modelo desde Vertex AI.

**Repurchase**

Recomprar: sustituir por un producto de terceros.

**Nosotros:** ninguna pieza hoy; sería cambiar un componente propio por un servicio de pago.

**Retire**

Retirar: apagar lo que ya no aporta.

**Nosotros:** la SQLite como fuente, cuando BigQuery esté validado; recursos de ensayo al terminar.

**Retain**

Retener: dejarlo donde está.

**Nosotros:** el repositorio y GitHub Actions; los datos personales o sensibles no suben.

Las listas de «R» **varían según la fuente**: AWS documenta **siete** (añade Relocate, mover a la versión en nube de la misma plataforma). Lo que importa: **elegir una estrategia por pieza**, no una para todo.

> **Para el ponente.** AWS Prescriptive Guidance documenta siete estrategias («7 Rs»): Retire, Retain, Rehost, Relocate, Repurchase, Replatform y Refactor o re-architect; también indica que Refactor es la más compleja y costosa. El material del curso usa seis (rehost, replatform y refactor se practican; retener, retirar y recomprar solo se mencionan). Cuál lista usa hoy Google Cloud: sin verificar. Los ejemplos de «Nosotros» son los de la teoría de S3 y de la guía de migración, salvo Retire y Retain, que se plantean para esta clase. Fuente (consultadas el 25/11/2026): AWS Prescriptive Guidance · Migration strategies, https://docs.aws.amazon.com/prescriptive-guidance/latest/large-migration-guide/migration-strategies.html.

### 22. Una hoja de ruta de seis oleadas

*Esquema: Hoja de ruta en seis oleadas: evaluar, base, datos, servicio, modelo y operar*

**Antes de mover nada**

- **Inventario**: qué hay, cuánto ocupa y de qué depende.

- **Plan de vuelta atrás** escrito antes de crear nada.

**Mientras se mueve**

- **Validar** cada paso: conteos, esquemas y agregados.

- Datos y servicio se migran **por separado**.

**Después**

- **Medir el gasto** y ajustar tamaños.

- **Borrar** lo que ya no sirve: forma parte de la migración.

> **Para el ponente.** Las fases (evaluar, planificar, ejecutar y optimizar) son las del material del curso, que advierte que sus nombres no se han contrastado con la documentación vigente de Google Cloud; aquí se reparten en oleadas por pieza. Qué se practica en el curso: las oleadas 1 a 3, según el plan de S4; la 4 solo se menciona. Hoja de ruta propuesta para esta clase, sin plazos ni cifras.

## 6. Costes y buenas prácticas

### 23. Cómo se paga y qué es gratis

**Prueba gratuita (Free Trial)**

- Programa público: **$300** de crédito de bienvenida **válido 90 días**.

- Pide un **medio de pago válido**; no se cobra durante la prueba.

- No cubre **GPUs**, Marketplace ni aumentos de cuota; tampoco la **API de Gemini en AI Studio** ni modelos de terceros.

- Al terminar sin actualizar: la cuenta se cierra y los **datos se marcan para borrado**, con 30 días de gracia.

**Nivel gratuito mensual (Free Tier)**

- **Cloud Run**: 2 millones de peticiones al mes.

- **BigQuery**: 1 TiB de consultas y 10 GiB de almacenamiento al mes.

- **Cloud Storage**: 5 GB-mes, pero **solo** en us-east1

, us-west1 y us-central1.

- Lo que pase del límite se factura (o se descuenta del crédito).

**$300 · 90 días**

crédito y plazo del programa de prueba (cifra pública del programa; **no** el saldo de ninguna cuenta concreta)

**0 GB gratis**

en southamerica-west1: el nivel gratuito de Cloud Storage **no** cubre Santiago; ahí el almacenamiento se factura (o sale del crédito de la prueba)

**Pago por uso**

cómputo, almacenamiento, consultas y salida de red: **se factura lo que consumes**

> **Para el ponente.** Cifras y condiciones de la documentación pública de Google Cloud sobre prueba gratuita y nivel gratuito, consultada el 25/11/2026: 300 dólares de crédito válidos 90 días; medio de pago obligatorio; restricciones (sin GPUs, Marketplace ni aumentos de cuota; el crédito no cubre Gemini API en AI Studio ni modelos de socios, ni, para altas desde el 16/11/2026, los servicios de la plataforma Gemini); cierre de cuenta y 30 días de gracia; límites mensuales de Cloud Run, BigQuery y Cloud Storage. La cuenta de curso del profesor está en prueba gratuita: no se cita su saldo. Las condiciones cambian: comprobar antes de impartir. Fuente (consultadas el 25/11/2026): Google Cloud · Free cloud features, https://docs.cloud.google.com/free/docs/free-cloud-features.

### 24. Presupuestos con alertas, y apagar no es borrar

**Presupuesto con alertas**

- Se crea **antes** que cualquier recurso, sobre la cuenta de facturación.

- Umbrales por defecto: **50 %, 90 % y 100 %** del importe, sobre gasto real.

- Puede avisar también por **previsión** de gasto.

**Un presupuesto de alertas no corta el gasto:** «Setting an alerts-only budget doesn't automatically cap Google Cloud … usage or spending». Solo avisa; alguien tiene que actuar.

**Etiquetas y tamaños**

- **Etiqueta todo**: curso

, responsable, caduca. Así se sabe qué es de quién.

- Cloud Run con **mínimo de instancias 0** y tamaños pequeños.

- Tablas con **caducidad** en las zonas de prueba.

*Esquema: Ciclo de vida de un recurso en la nube: crear con etiquetas, usar, apagar y borrar*

Terminal · limpieza al terminar (plantilla; sin ejecutar en esta clase)

$ `gcloud run services delete retencion-api --region=southamerica-west1`

$ `gcloud artifacts repositories delete REPOSITORIO --location=southamerica-west1`

$ `gcloud storage rm --recursive gs://NOMBRE_DEL_BUCKET`

$ `bq rm --recursive --force --dataset ID_PROYECTO:NOMBRE_DEL_DATASET`

# o, si el proyecto era desechable, de una vez

$ `gcloud projects delete ID_PROYECTO`

> **Para el ponente.** Umbrales por defecto de los presupuestos de Cloud Billing: 50, 90 y 100 por ciento del importe, calculados sobre el gasto real; pueden cambiarse y añadirse previsiones. La documentación advierte textualmente de que un presupuesto solo de alertas no limita el uso ni el gasto; hay presupuestos con tope de gasto, solo para servicios compatibles y a nivel de proyecto (no se detalla aquí). Los comandos de limpieza son plantillas con valores en mayúsculas: no se han ejecutado. Antes de borrar un proyecto, comprobar que no hay nada que conservar. Fuente (consultadas el 25/11/2026): Cloud Billing · Budgets, https://docs.cloud.google.com/billing/docs/how-to/budgets.

### 25. La región del curso: qué hay en Santiago

| Servicio | southamerica-west1 (Santiago) | southamerica-east1 (São Paulo) |
|---|---|---|
| Cloud Storage | sí región | sí región |
| BigQuery | sí | sí |
| Artifact Registry | sí | sí |
| Cloud Run | sí (nivel de precio 2) | sí (nivel de precio 2) |
| Secret Manager | sí secretos regionales | sí secretos regionales |
| GKE y Dataproc | sí comprobado: GKE Autopilot y Dataproc sin servidor funcionaron en Santiago (prácticas 02 y 03, 25/11/2026) | sin dato |
| Vertex AI: modelos propios | sí entrenamiento, predicción en línea y por lotes, Model Registry, Pipelines | sí y además Model Monitoring, Experiments y Explainable AI |
| Gemini en Vertex AI | no listada usar el endpoint global | sin dato aparece como región; sin detalle de modelos |

**Conclusión:** en Santiago caben nuestras piezas de partida y el Model Registry y los endpoints de Vertex AI. Si se necesita **Model Monitoring**, **Experiments** o **Explainable AI** de Vertex AI, la alternativa documentada es **southamerica-east1 (São Paulo)**. El nivel gratuito de Cloud Storage no cubre ninguna de las dos.

> **Para el ponente.** Disponibilidad según la documentación oficial, consultada el 25/11/2026. Vertex AI en southamerica-west1: AutoML tabular y de series temporales, inferencia por lotes y en línea y entrenamiento de modelos personalizados, Model Registry, Vector Search, Pipelines, TensorBoard y Vizier; no figuran Model Monitoring, Experiments, Explainable AI, etiquetado de datos ni Workbench. En southamerica-east1 figuran además Model Monitoring, Experiments y Explainable AI, y Workbench. Gemini: la página de regiones de Gemini no lista Santiago; São Paulo aparece como región pero las celdas de disponibilidad salieron vacías en la copia consultada, así que no se sabe qué modelos; existe endpoint global. Cloud Run: ambas regiones en nivel de precio 2. BigQuery, Artifact Registry y Cloud Storage: Santiago y São Paulo aparecen en sus listas de regiones. Secret Manager: ambas admiten secretos regionales; también existe replicación automática. Dataproc: la página no enumera regiones y remite a las de Compute Engine. GKE: la página consultada no nombra la región: sin dato. Nota de nombre: las páginas actuales de Vertex AI hablan de «Gemini Enterprise Agent Platform». Fuentes (consultadas el 25/11/2026): Vertex AI · Locations, https://docs.cloud.google.com/vertex-ai/docs/general/locations; Gemini en Vertex AI · Locations, https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/locations; Cloud Run · Locations, https://docs.cloud.google.com/run/docs/locations; BigQuery · Locations, https://docs.cloud.google.com/bigquery/docs/locations; Artifact Registry · Repository locations, https://docs.cloud.google.com/artifact-registry/docs/repositories/repo-locations; Cloud Storage · Locations, https://docs.cloud.google.com/storage/docs/locations; Secret Manager · Locations, https://docs.cloud.google.com/secret-manager/docs/locations; Compute Engine · Regions and zones, https://docs.cloud.google.com/compute/docs/regions-zones; Dataproc · Regional endpoints, https://docs.cloud.google.com/dataproc/docs/concepts/regional-endpoints.

### 26. Seis reglas para no arrepentirse

**1 Proyecto desechable**

Un proyecto solo para aprender, que se **borra entero** al acabar.

**2 Presupuesto primero**

Antes de crear el primer recurso, con alertas a **varios umbrales**.

**3 Una sola región**

Cerca de los usuarios (aquí, Santiago). Mover datos entre regiones suma complejidad y coste de red.

**4 Sin claves**

**Workload Identity Federation** en lugar de claves JSON; ningún secreto en el repositorio.

**5 Mínimo privilegio**

Una **cuenta de servicio por función** con un solo rol; secretos en **Secret Manager**.

**6 Etiquetar y borrar**

Todo con etiqueta y fecha de caducidad; **validar** antes de borrar el origen.

**Datos del curso:** ningún dato sensible ni personal en la nube del curso, y comprobar la licencia del conjunto de datos antes de subirlo.

> **Para el ponente.** Las seis reglas resumen el material del curso (proyecto desechable, presupuesto antes que cualquier recurso, una sola región, identidad sin claves, mínimo privilegio y limpieza) y las recomendaciones de la documentación citada en las diapositivas anteriores: WIF evita las claves de cuenta de servicio, que son credenciales potentes con riesgo si se gestionan mal; los presupuestos no cortan el gasto. La regla de datos es la de la guía de migración del curso. Sin cifras.

## 7. Cierre

### 27. Qué se comprobó de verdad y qué falta

**Comprobado en la documentación oficial (25/11/2026)**

- Disponibilidad en Santiago y São Paulo de Cloud Storage, BigQuery, Artifact Registry, Cloud Run y Secret Manager.

- Funciones de Vertex AI en Santiago y en São Paulo; Gemini sin Santiago.

- Prueba gratuita ($300, 90 días) y límites mensuales; el de Cloud Storage solo en tres regiones de EE. UU.

- Presupuestos: umbrales 50, 90 y 100 %; no cortan el gasto.

- Jerarquía de recursos, WIF, y las siete «R» de AWS.

**Sin verificar o sin dato**

- **Sin ejecutar** en Google Cloud: ninguna orden de esta clase (hay plantillas).

- Cuota de mercado, número de regiones y precios de los proveedores: **sin dato**.

- GKE y Dataproc en São Paulo, y Cloud Logging: **sin dato** (en Santiago se comprobaron el 25/11/2026).

- Modelos de Gemini disponibles en São Paulo: **sin dato**.

- Coste de un endpoint de Vertex AI y horas de cada migración: **sin dato**.

- Nombres de producto de AWS y Azure: de sus documentaciones, pero no se comprobó cada fila.

Los servicios, las regiones y las condiciones de la nube **cambian**. Antes de impartir o de decidir: volver a mirar las páginas citadas en las notas del ponente (tecla **S**).

> **Para el ponente.** Diapositiva de honestidad. La lista de lo comprobado corresponde a páginas de documentación oficial leídas el 25/11/2026; ninguna orden se ejecutó contra Google Cloud para preparar esta clase. Lo no comprobado se dice sin dato. Las fuentes con dirección están en las notas de cada diapositiva y reunidas en guia.md.

### 28. Seis preguntas

**1. ¿Qué diferencia hay entre CAPEX y OPEX?**

CAPEX es la inversión inicial en equipos (on-premise); OPEX, el gasto corriente por uso (nube).

**2. ¿Por qué Cloud Run es «serverless»?**

No gestionas servidores: subes una imagen, escala con las peticiones y puede bajar a cero.

**3. ¿Qué cambia al pasar de claves a WIF?**

Ya no hay claves guardadas: GitHub presenta un token temporal y Google lo cambia por acceso de una cuenta de servicio.

**4. ¿Qué estrategia aplica a la imagen de la API y cuál a SQLite?**

**Rehost** para la imagen (se mueve tal cual); **replatform** para SQLite a BigQuery.

**5. ¿Un presupuesto con alertas evita pasarse de gasto?**

No: solo avisa. Hay que actuar, y apagar no es borrar.

**6. ¿Qué falta en Santiago respecto a São Paulo en Vertex AI?**

Model Monitoring, Experiments y Explainable AI no figuran en Santiago; Gemini no se lista allí.

> **Para el ponente.** Lea cada pregunta y deje que respondan antes de leer la respuesta. La sexta se contesta con la diapositiva de regiones, cuya fuente es la documentación de ubicaciones de Vertex AI y de Gemini consultada el 25/11/2026. La tercera enlaza con la diapositiva de identidad y la quinta con la de presupuestos.

### 29. A la nube se llega pieza a pieza, con presupuesto y borrando al final

Mover algo a la nube **no es copiarlo**: es elegir, **pieza a pieza**, qué servicio la sustituye, cómo se valida y cuánto cuesta, y **borrar** al final lo que ya no sirve.

**3 zonas**

tiene la región southamerica-west1 (Santiago): -a, -b y -c

**90 días**

de validez del crédito de la prueba gratuita pública de Google Cloud

**0 claves**

guardadas en GitHub si se entra con **Workload Identity Federation**

**50 · 90 · 100 %**

umbrales por defecto de un presupuesto con alertas: avisan, **no cortan**

¿Preguntas?

> **Para el ponente.** Cierre con un único mensaje. Las cuatro tarjetas son comprobables: las tres zonas de southamerica-west1 vienen de la tabla de regiones y zonas de Compute Engine; los 90 días, de la documentación pública de la prueba gratuita; las cero claves, de la descripción de Workload Identity Federation; y los umbrales 50, 90 y 100 por ciento, de la documentación de presupuestos. Fuentes (consultadas el 25/11/2026): Compute Engine · Regions and zones, https://docs.cloud.google.com/compute/docs/regions-zones; Google Cloud · Free cloud features, https://docs.cloud.google.com/free/docs/free-cloud-features; IAM · Workload Identity Federation, https://docs.cloud.google.com/iam/docs/workload-identity-federation; Cloud Billing · Budgets, https://docs.cloud.google.com/billing/docs/how-to/budgets. Siguiente paso en el curso: la práctica guiada de S4 y la operación del modelo en S5.

## Fuentes consultadas (25/11/2026)

- Google Cloud · Cloud locations: <https://cloud.google.com/about/locations>
- Vertex AI · Locations: <https://docs.cloud.google.com/vertex-ai/docs/general/locations>
- Gemini en Vertex AI · Locations: <https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/locations>
- Cloud Run · Locations: <https://docs.cloud.google.com/run/docs/locations>
- BigQuery · Locations: <https://docs.cloud.google.com/bigquery/docs/locations>
- Artifact Registry · Repository locations: <https://docs.cloud.google.com/artifact-registry/docs/repositories/repo-locations>
- Cloud Storage · Locations: <https://docs.cloud.google.com/storage/docs/locations>
- Secret Manager · Locations: <https://docs.cloud.google.com/secret-manager/docs/locations>
- Compute Engine · Regions and zones: <https://docs.cloud.google.com/compute/docs/regions-zones>
- Dataproc · Regional endpoints: <https://docs.cloud.google.com/dataproc/docs/concepts/regional-endpoints>
- Google Cloud · Free cloud features: <https://docs.cloud.google.com/free/docs/free-cloud-features>
- Cloud Billing · Budgets: <https://docs.cloud.google.com/billing/docs/how-to/budgets>
- Resource Manager · Resource hierarchy: <https://docs.cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy>
- IAM · Workload Identity Federation: <https://docs.cloud.google.com/iam/docs/workload-identity-federation>
- AWS Prescriptive Guidance · Migration strategies: <https://docs.aws.amazon.com/prescriptive-guidance/latest/large-migration-guide/migration-strategies.html>
- AWS · What is Amazon SageMaker AI: <https://docs.aws.amazon.com/sagemaker/latest/dg/whatis.html>
- Microsoft Learn · Foundry Models sold by Azure: <https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure>
- Microsoft Learn · What is Azure Synapse Analytics: <https://learn.microsoft.com/en-us/azure/synapse-analytics/overview-what-is>
