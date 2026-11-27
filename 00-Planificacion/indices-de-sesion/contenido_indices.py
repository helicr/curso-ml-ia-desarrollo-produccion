"""Fuente del índice de cada sesión (`01-Sesiones/Sx-.../index.html`).

`generar_indices.py` crea un `index.html` dentro de cada carpeta de sesión con:
  - sus presentaciones y documentos (los de esta lista, con su descripción);
  - cualquier otro .html o .md que haya en la carpeta y no esté aquí: aparece solo, con el título que tenga el archivo;
  - qué componentes de la sesión existen y cuáles faltan (presentación, guion, teoría, práctica, tarea…).

Para describir un archivo nuevo o cambiar un texto: edita este archivo y ejecuta
`python 00-Planificacion/indices-de-sesion/generar_indices.py`. Si solo añades un archivo a la carpeta, basta con ejecutar el generador.
"""

CURSO = 'ML e IA: de desarrollo a producción'
SUBTITULO = 'Instructor: Helí Campos R · UNTRM · 2026-II'
REPO_GITHUB = 'https://github.com/helicr/curso-ml-ia-desarrollo-produccion'
RAMA = 'main'

CARPETA_SESIONES = '01-Sesiones'
ENTORNO = '03-Entorno'

# Grupos de enlaces dentro de la página de una sesión
PRESENTACIONES, ALUMNO, INSTRUCTOR = 'presentaciones', 'alumno', 'instructor'
GRUPOS = [(PRESENTACIONES, 'Presentaciones'), (ALUMNO, 'Para el alumno'), (INSTRUCTOR, 'Para el instructor')]


def deck(titulo, ruta, desc='', volver=False):
    """Presentación o página HTML (se abre siempre desde el disco). `volver`: lleva un enlace de regreso al índice de su sesión."""
    return dict(tipo='deck', grupo=PRESENTACIONES, titulo=titulo, ruta=ruta, desc=desc, volver=volver)


def doc(grupo, titulo, ruta, desc=''):
    """Documento (.md, .py, .yml): según el interruptor de la página se abre en GitHub o desde la carpeta local."""
    return dict(tipo='doc', grupo=grupo, titulo=titulo, ruta=ruta, desc=desc)


def alumno(titulo, ruta, desc=''):
    return doc(ALUMNO, titulo, ruta, desc)


def instructor(titulo, ruta, desc=''):
    return doc(INSTRUCTOR, titulo, ruta, desc)


# Componentes que se espera encontrar en una sesión y cómo se detectan (patrones relativos a la carpeta de la sesión)
COMPONENTES = {
    'presentacion': ('Presentación', ['slides/index.html']),
    'guion': ('Guion', ['guion.md']),
    'checklist': ('Checklist', ['checklist.md']),
    'teoria': ('Teoría', ['teoria/*.md']),
    'practica': ('Práctica', ['practica/*.md']),
    'tarea': ('Tarea', ['tarea/README.md']),
    'rubrica': ('Rúbrica', ['tarea/rubrica.md']),
    'evidencia': ('Plantilla de la evidencia', ['evidencias/*.md']),
}
TODOS = list(COMPONENTES)

# Estados de una sesión
PREPARADO = 'preparado'      # hay material de clase (lo probado y lo no probado está en ESTADO-DEL-PAQUETE.md)
SOLO_README = 'solo_readme'  # la carpeta solo tiene README.md
ESTADOS = {PREPARADO: ('Material preparado', 'ok'), SOLO_README: ('Solo README', 'warn')}

S0, S1, S2, S3, S4, S5 = (f'{CARPETA_SESIONES}/{n}' for n in (
    'S0-Presentacion-y-Entorno', 'S1-Datos-y-Entrenamiento', 'S2-API-y-Docker',
    'S3-Despliegue-y-Redes-Neuronales', 'S4-Orquestacion-y-CI-CD', 'S5-MLOps-y-Operacion'))

SESIONES = [
    dict(
        id='S0', titulo='Presentación y entorno', horas='2 h', carpeta=S0, estado=PREPARADO, esperados=['presentacion', 'guion', 'checklist', 'practica'],
        resumen='Parte A (curso, caso y entregas, 25 min), pausa de 15, Parte B (software local, repositorio, Codespaces, nube y diagnóstico, 70 min) y cierre de 10. '
                'Tarea: completar la preparación y leer el caso. Evidencia: entorno comprobado antes de S1.',
        nota='No tiene teoría ni tarea en archivos propios: la tarea es completar la preparación.',
        enlaces=[
            deck('Presentación principal', f'{S0}/slides/index.html', 'Parte A, pausa, Parte B y cierre. Teclas: ← → avanzar, O índice, S notas, F pantalla completa.', volver=True),
            deck('Tu equipo listo para S1', f'{S0}/slides/instalacion/index.html', 'Para copiar y pegar: instalación en orden, entorno desde environment.yml, pruebas y verificador.', volver=True),
            deck('Anexos de consulta', f'{S0}/slides/anexos/index.html', 'Anexos A–F: estadísticas, herramientas, calculadora de coste de Cloud Run y fuentes. Consulta; no suman a las dos horas de S0.'),
            deck('Plan docente', f'{S0}/slides/fuentes/plan-docente.html', 'Una página: programa, ritmo, reparto de S0 y cautelas.'),
            alumno('Guía rápida del entorno (S0 → S1)', f'{S0}/practica/guia-rapida-entorno-s0-s1.md', 'Lo mismo que «Tu equipo listo para S1», en texto.'),
            deck('Guía de instalación para Windows', f'{ENTORNO}/guia-instalacion/index.html', 'Interactiva: elige ruta y terminal, copia los comandos y marca tu progreso.'),
            alumno('Checklist de 12 comprobaciones', f'{S0}/checklist.md', 'Diagnóstico del entorno.'),
            alumno('Requisitos del entorno', f'{ENTORNO}/guias/requisitos.md', 'Qué se instala en tu equipo, qué se usa en la nube y qué versiones.'),
            alumno('Preparación paso a paso (Windows)', f'{ENTORNO}/guias/preparacion-paso-a-paso.md', 'Todo en uno con script o paso a paso; ruta sin instalación.'),
            alumno('Verificador para S1', f'{ENTORNO}/conda/verificar_s1.py', 'Termina en LISTO PARA S1; con --informe guarda verificacion-s1.txt.'),
            instructor('README de S0', f'{S0}/README.md'),
            instructor('Guion con tiempos', f'{S0}/guion.md', 'Minuto a minuto, diapositiva por diapositiva.'),
        ],
    ),
    dict(
        id='S1', titulo='Datos y entrenamiento', horas='4 h', carpeta=S1, estado=PREPARADO, esperados=TODOS,
        resumen='OPERACIONAL → RAW → MASTER → FS → ML con un cuaderno por capa, partición temporal, tres modelos comparados y seguimiento con MLflow. '
                'Tarea: añadir una variable a la capa FS del caso del instructor (Online Retail II) y decidir con evidencia.',
        nota='El caso propio de los alumnos (Bank Marketing) empieza aquí y sigue hasta S5: ver 02-Proyecto-Transversal/alumno/tu-caso-bank-marketing.md.',
        enlaces=[
            deck('Presentación de S1', f'{S1}/slides/index.html', 'Revisión del entorno, teoría, práctica, entrega y cierre.', volver=True),
            deck('Tu caso de S1 a S5 (Bank Marketing)', f'{S1}/slides/caso-propio/index.html', 'El caso propio del alumnado: la pregunta, el dato, las trampas, la partición y los cuatro avances.', volver=True),
            alumno('Teoría y glosario', f'{S1}/teoria/README.md'),
            alumno('Guía de laboratorio', f'{S1}/practica/guia-laboratorio.md', 'Paso a paso con presupuesto de tiempo.'),
            alumno('Tarea', f'{S1}/tarea/README.md'),
            alumno('Rúbrica', f'{S1}/tarea/rubrica.md', '20 % reproducibilidad · 40 % técnica · 40 % análisis y decisión.'),
            alumno('Plantilla de la decisión', f'{S1}/evidencias/plantilla-decision.md', 'La evidencia que se entrega.'),
            alumno('Checklist', f'{S1}/checklist.md'),
            alumno('Proyecto base (Online Retail II)', '04-Proyecto-Base/README.md', 'Cuadernos, paquete ia_mlops, pruebas y Makefile.'),
            alumno('Tu caso: Bank Marketing', '02-Proyecto-Transversal/alumno/tu-caso-bank-marketing.md', 'La hoja del caso propio: pregunta, dato, cifras para comprobar tu carga, decisiones tuyas y entregas.'),
            alumno('Plantilla de cada avance', '02-Proyecto-Transversal/alumno/plantilla-avance.md', 'Lo que se entrega en cada uno de los cuatro avances del caso propio.'),
            alumno('Rúbrica de cada avance', '02-Proyecto-Transversal/alumno/rubrica-avance.md', '20 % reproducibilidad · 40 % técnica · 40 % análisis y decisión.'),
            instructor('README de S1', f'{S1}/README.md', 'Agenda por minutos y qué está validado.'),
            instructor('Guion', f'{S1}/guion.md'),
        ],
    ),
    dict(
        id='S2', titulo='API y Docker', horas='4 h', carpeta=S2, estado=PREPARADO, esperados=TODOS,
        resumen='Del modelo guardado a un servicio: API con FastAPI cuyo contrato sale de la firma del modelo, errores 422/503/500, registros JSON, imagen Docker mínima, '
                'comparación de predicciones por todos los caminos y primer workflow de GitHub Actions. Tarea: llevar el modelo propio al mismo punto.',
        nota='Probado en Linux, en GitHub Actions y, el bloque 4, en un Codespace real del curso (12/11/2026). Sin probar: Docker en un equipo propio y los comandos en Windows. '
             'Los ejemplos de contenedores se ejecutaron con Docker real en GitHub Actions, no en un Codespace; lo que dicen de Cloud Run es solo la documentación de Google.',
        enlaces=[
            deck('Presentación de S2', f'{S2}/slides/index.html', 'Revisión del entorno, teoría, laboratorio de códigos, práctica, entrega y cierre.', volver=True),
            deck('Recap de S1: de los datos al modelo', '01-Sesiones/recap/recap-01/index.html',
                 'Para empezar: S1 en cinco minutos, con diagramas, las capas interactivas y una autoevaluación.'),
            alumno('Teoría y glosario', f'{S2}/teoria/README.md'),
            alumno('Guía de laboratorio', f'{S2}/practica/guia-laboratorio.md', 'Paso a paso con presupuesto de tiempo y salidas esperadas.'),
            alumno('Laboratorio extra: de la ingesta a la explotación', f'{S2}/practica/laboratorio-extra-de-punta-a-punta.md',
                   'Si sobra tiempo (unos 60 min): pipelines uno a uno, modelo registrado, API, la lista de la campaña y el ciclo con datos nuevos.'),
            deck('Laboratorio: exponer el servicio (del ordenador al servicio)', f'{S2}/del-ordenador-al-servicio/index.html',
                 'Las diapositivas del laboratorio de exponer el modelo (bloque 6 de la práctica; se abre también desde la diapositiva 19 de la presentación de S2). '
                 'Pros y contras de llevar un modelo a producción, la arquitectura de la exposición, de dos procesos en tu portátil a dos contenedores '
                 '(red, puertos, volumen de solo lectura, Compose) y el mapa a producción. Órdenes para copiar, salidas reales y capturas de cada paso en un Codespace real.', volver=True),
            alumno('Interfaz de consulta: del ordenador al servicio', f'{S2}/practica/interfaz-de-consulta.md',
                   'Unos 60 min: ids de cliente → probabilidad y recomendación, primero en tu ordenador y después en dos contenedores (API e interfaz) en el Codespace.'),
            alumno('Del ordenador al servicio (guía completa)', '04-Proyecto-Base/docs/del-ordenador-al-servicio.md',
                   'Desde lo básico (proceso, puerto, 127.0.0.1) hasta dos contenedores con red, volumen de solo lectura y Compose, y lo que falta para producción.'),
            alumno('La interfaz de consulta (detalle técnico)', '04-Proyecto-Base/docs/interfaz-de-consulta.md',
                   'Cómo se calculan las variables, la regla de negocio y los endpoints.'),
            alumno('Tarea', f'{S2}/tarea/README.md'),
            alumno('Rúbrica', f'{S2}/tarea/rubrica.md', '20 % reproducibilidad · 40 % técnica · 40 % análisis y decisión.'),
            alumno('Plantilla de la evidencia', f'{S2}/evidencias/plantilla-api-y-contenedor.md', 'La evidencia que se entrega.'),
            alumno('Checklist', f'{S2}/checklist.md'),
            alumno('La API y el contenedor', '04-Proyecto-Base/docs/api-y-contenedor.md', 'Contrato, errores, registros, imagen, workflow y qué se probó.'),
            deck('Codespaces: tu laboratorio de Docker en la nube', f'{ENTORNO}/guia-codespaces/index.html',
                 'Guía en diapositivas con capturas de un Codespace real: abrirlo (navegador o VS Code), el bloque 4 paso a paso y la cuota.', volver=True),
            alumno('Guía de Codespaces (versión en texto)', f'{ENTORNO}/guias/codespaces-para-el-alumnado.md', 'El mismo contenido, para leer sin diapositivas.'),
            deck('Contenedores 1: el modelo mental', f'{S2}/contenedores/modelo-mental/index.html',
                 'Obligatoria antes de S2: imagen y contenedor, ciclo de vida, lo que se pierde al borrar, puertos y volúmenes. Cuatro prácticas con salidas reales.', volver=True),
            deck('Contenedores 2: del Dockerfile a producción', f'{S2}/contenedores/del-dockerfile-a-produccion/index.html',
                 'Antes de S2: capas y caché, .dockerignore, secretos, usuario sin privilegios, healthcheck. Cinco prácticas con salidas reales.', volver=True),
            alumno('Contenedores: guía práctica con nueve ejemplos', f'{S2}/contenedores/guia-practica.md',
                   'Obligatorios antes de S2 los ejemplos 1 a 6 (unos 60 min); los nueve, unos 97 min (estimado). Se hacen en el Codespace.'),
            alumno('Contenedores: laboratorio «romperlo a propósito»', f'{S2}/contenedores/laboratorio-romper.md',
                   'Cinco fallos que provocas, diagnosticas y arreglas (unos 34 min; estimado).'),
            alumno('Docker y Kubernetes sin instalación local', f'{ENTORNO}/guias/docker-y-kubernetes-sin-instalacion-local.md', 'Cómo trabajar con Docker en Codespaces.'),
            alumno('Chuleta de Docker, kubectl y GKE', f'{ENTORNO}/guia-docker-kubernetes-gke/chuleta.md', 'Los comandos de Docker de S2 y, para S3, kubectl y GKE.'),
            instructor('README de S2', f'{S2}/README.md', 'Agenda por minutos y qué está validado.'),
            instructor('Guion', f'{S2}/guion.md'),
            instructor('Contenedores: cómo se generó y cómo regenerarlo', f'{S2}/contenedores/README.md', 'Una sola fuente de comandos, salidas reales de Docker, pruebas y comprobación de diseño.'),
            instructor('Material del laboratorio extra de S2', f'{S2}/practica/extra/README.md',
                       'El diagrama del recorrido y capturar.py, que ejecuta el laboratorio extra y guarda sus salidas reales.'),
        ],
    ),
    dict(
        id='S3', titulo='Laboratorios: el servicio de S2, MLflow, GitHub Actions y una red neuronal', horas='4 h', carpeta=S3, estado=PREPARADO,
        esperados=['guion', 'checklist', 'teoria', 'practica', 'tarea', 'rubrica', 'evidencia'],
        resumen='Cuatro laboratorios en el orden en que se construye el sistema: 1) el servicio de S2 (la API, la inferencia, las variables FS al vuelo y la interfaz); '
                '2) MLflow (de dónde sale el modelo: runs, comparación, firma y versiones del registro); 3) GitHub Actions (cada cambio se comprueba solo: '
                'verde, rojo, verde); 4) extra: una red neuronal, ¿perro o gato?, registrada en MLflow como un modelo más. GCP se explica para llegar a S4 con '
                'Google Cloud activado. Tarea (avance 3): workflow con una prueba propia en rojo y en verde, y Google Cloud activado.',
        nota='Cambio del 20/11/2026: la migración a GCP en vivo pasa a S4; la teoría y la guía de GCP de esta carpeta son material de preparación para S4. '
             'Las capturas son reales (Codespace del curso y GitHub Actions, 20/11/2026); en la red neuronal, entrenar, MLflow y predecir se capturaron en local. '
             'Las presentaciones de la sesión son los cuatro laboratorios (no hay slides/index.html). Minutos de cada bloque: en el guion.',
        enlaces=[
            deck('1 · Laboratorio-recap de S2: interfaz, inferencia y variables al vuelo', f'{S3}/laboratorio-recap-s2/index.html',
                 'Bloque 1 (70 min en clase). La API (/docs, una predicción y un lote), las variables FS calculadas al vuelo y comparadas con la tabla, la interfaz y vivo frente a listo. '
                 'Órdenes para copiar y capturas de un Codespace real.', volver=True),
            deck('2 · Laboratorio de MLflow: experimentos, comparación y registro de modelos', f'{S3}/laboratorio-mlflow/index.html',
                 'Bloque 2 (35 min). La base de MLflow del proyecto, la interfaz en el puerto 5000, runs y métricas, comparar modelos, la firma, '
                 'versiones del modelo registrado (reentrenar → versión 2) y cargarlo desde Python. Capturas reales del Codespace.', volver=True),
            deck('3 · Laboratorio de GitHub Actions: romper y arreglar', f'{S3}/laboratorio-github-actions/index.html',
                 'Bloque 3 (70 min). Un workflow que ejecuta las pruebas del proyecto en tu rama: verde, rotura a propósito, rojo, leer el registro y arreglar. Capturas reales.', volver=True),
            deck('4 · Extra: red neuronal, ¿perro o gato?', f'{S3}/laboratorio-red-neuronal/index.html',
                 'Bloque 4 (20 min). Transferencia: MobileNetV3-small congelada + regresión logística sobre fotos de Oxford-IIIT Pet; entrenar en segundos, '
                 'registrar en MLflow y predecir una foto (93 % en test: 6 fallos de 90). Replicarlo es autoestudio.', volver=True),
            deck('Recap de S2 (diapositivas resumen)', '01-Sesiones/recap/recap-02/index.html', 'S2 en cinco minutos, con autoevaluación.'),
            alumno('1 · Guía del laboratorio-recap de S2', f'{S3}/laboratorio-recap-s2/guia.md', 'El mismo recorrido en texto: cada orden, qué debes ver y si falla.'),
            alumno('2 · Guía del laboratorio de MLflow', f'{S3}/laboratorio-mlflow/guia.md', 'El mismo recorrido en texto: cada orden, qué debes ver y si falla.'),
            alumno('3 · Guía del laboratorio de GitHub Actions', f'{S3}/laboratorio-github-actions/guia.md', 'El YAML línea a línea y los ocho pasos del laboratorio.'),
            alumno('3 · El workflow del laboratorio', f'{S3}/laboratorio-github-actions/pruebas-proyecto.yml', 'Se copia en .github/workflows/ de tu copia del repositorio.'),
            alumno('3+ · Pipeline de datos e2e en GitHub Actions (guía paso a paso)', f'{S3}/laboratorio-github-actions/guia-pipeline-e2e.md',
                   'Un job por etapa (origen → RAW → MASTER → FS/ML → entrenar → API y campaña → resumen), encadenados con needs: y artefactos. Run real en verde: 6 min 49 s.'),
            alumno('3+ · El workflow del pipeline e2e', f'{S3}/laboratorio-github-actions/pipeline-e2e.yml', 'Se copia en .github/workflows/pipeline-e2e.yml de tu copia del repositorio.'),
            alumno('4 · Guía del laboratorio de red neuronal', f'{S3}/laboratorio-red-neuronal/guia.md', 'Instalar, preparar las fotos, entrenar, ver en MLflow y predecir.'),
            alumno('4 · Script del laboratorio de red neuronal', f'{S3}/laboratorio-red-neuronal/red_gato_perro.py', 'Subórdenes datos, entrenar y predecir.'),
            alumno('Tarea (avance 3)', f'{S3}/tarea/README.md', 'Entrega: miércoles 25/11/2026, 10:00 (hora de Perú).'),
            alumno('Rúbrica', f'{S3}/tarea/rubrica.md', '20 % reproducibilidad · 40 % técnica · 40 % análisis y decisión.'),
            alumno('Plantilla del avance 3', f'{S3}/evidencias/plantilla-avance-3.md', 'La evidencia que se entrega.'),
            alumno('Activa Google Cloud para S4', f'{S3}/preparar-gcp-para-s4.md', 'Lo obligatorio: cuenta de Google y Google Cloud activado; no crear nada todavía.'),
            alumno('Checklist', f'{S3}/checklist.md'),
            alumno('Teoría de la migración a GCP (para S4)', f'{S3}/teoria/README.md', 'Fases, estrategias, mapa de equivalencias, identidad, secretos y costes.'),
            alumno('Guía de migración a GCP (para S4)', f'{S3}/practica/guia-laboratorio.md', 'Ruta con nube y ruta sin nube; los pasos de GCP, sin verificar.'),
            alumno('SDK de Google Cloud en VS Code y en el Codespace', f'{ENTORNO}/guias/sdk-google-cloud-vscode-y-codespaces.md', 'Instalar gcloud, iniciar sesión sin pegar claves y comprobar la conexión.'),
            alumno('Ensayo local de la migración (para S4)', f'{S3}/practica/ensayo-local/LEEME.md', 'Salidas reales de exportar y validar sin nube; no es GCP.'),
            alumno('Guía de migración de local a GCP (general)', f'{ENTORNO}/guias/migracion-on-premise-a-gcp.md', 'El hilo de la migración, para S4.'),
            deck('Docker, Kubernetes y GKE', f'{ENTORNO}/guia-docker-kubernetes-gke/index.html',
                 'Autoestudio: conceptos, práctica con kind en el Codespace, GKE explicado, chuleta y ejercicios.'),
            instructor('README de S3', f'{S3}/README.md', 'Agenda y orden de uso del material.'),
            instructor('Guion', f'{S3}/guion.md', '240 min por bloques y qué hacer si algo falla.'),
            instructor('Carpeta slides/ (estado)', f'{S3}/slides/README.md', 'Vacía a propósito: las presentaciones de S3 son los cuatro laboratorios; lo demás es del plan previo (S4).'),
        ],
    ),
    dict(
        id='S4', titulo='Orquestación y CI/CD con GitHub Actions', horas='4 h', carpeta=S4, estado=PREPARADO, esperados=['guion', 'checklist', 'teoria', 'practica', 'tarea', 'rubrica', 'evidencia'],
        resumen='Workflows y disparadores, secretos y autenticación con GCP sin claves, pruebas, registro del modelo, imagen y despliegue con aprobación.',
        nota='Preparados por ahora: el laboratorio de cierre «Producción e2e del caso Retail» '
             '(carpeta laboratorio-produccion-e2e/: lote diario, bajo demanda, online con variables al vuelo, panel, versión nueva con '
             'aprobación y rollback, ensayados en GitHub Actions el 22/11/2026) y el extra «Un LLM y el estilo de color» (carpeta extra-estilo-llm/): '
             'notebooks ejecutados y pipeline en GitHub Actions con un run real en verde (21/11/2026). '
             'Ya ejecutado y borrado el 25/11/2026 en la cuenta de Google Cloud del curso: las cinco prácticas en Google Cloud '
             '(carpeta practicas-gcp/, con sus diapositivas paso a paso, salidas y capturas reales) y el laboratorio «Cloud Journey» '
             '(carpeta laboratorio-cloud-journey/: la API en Cloud Run desde GitHub Actions sin claves, el modelo en Vertex AI y el borrado). '
             'Preparada: la clase «De on-premise a la nube» (carpeta clase-onpremise-a-nube/). Sin verificar: clonar el fork de un alumno en Cloud Shell, '
             'el coste y el tiempo exacto del endpoint de Vertex.',
        enlaces=[
            instructor('README de S4', f'{S4}/README.md'),
            instructor('Guion de ensayo del profesor: recrear S4 antes de repetirlo con el alumnado', f'{S4}/guion-ensayo-profesor.md', 'Qué cambió desde el 25/11, por dónde empezar (práctica sin coste, luego Cloud Journey), qué decir y qué teclear, y las trampas conocidas.'),
            alumno('Teoría de S4', f'{S4}/teoria/README.md'),
            alumno('Guía de laboratorio de S4', f'{S4}/practica/guia-laboratorio.md'),
            alumno('Tarea de S4 (avance 4)', f'{S4}/tarea/README.md'),
            alumno('Rúbrica de S4', f'{S4}/tarea/rubrica.md'),
            alumno('Plantilla de la evidencia del avance 4', f'{S4}/evidencias/plantilla-avance-4.md'),
            alumno('Checklist de S4', f'{S4}/checklist.md'),
            instructor('Guion de S4', f'{S4}/guion.md', 'Fechado el 25/11: cambiar la fecha si se reutiliza.'),
            deck('Clase: de on-premise a la nube (diapositivas)', f'{S4}/clase-onpremise-a-nube/index.html',
                 '29 diapositivas: on-premise frente a nube, IaaS/PaaS/SaaS, los hiperescalares y sus servicios equivalentes, Google Cloud '
                 '(jerarquía, IAM, WIF), servicios para el curso (Cloud Run, GKE, Dataproc, Vertex AI, Gemini), nuestro Cloud Journey '
                 'AS-IS → TO-BE, costes y región; con fuentes.', volver=True),
            alumno('Clase: de on-premise a la nube (texto)', f'{S4}/clase-onpremise-a-nube/guia.md', 'Lo mismo en prosa, con las notas y las fuentes.'),
            alumno('Prácticas en Google Cloud (crear → probar → borrar)', f'{S4}/practicas-gcp/README.md',
                   'Docker + Artifact Registry + Cloud Run, Kubernetes en GKE, Spark en Dataproc, el modelo en Vertex AI y Gemini; '
                   'cada una con crear.sh, probar.sh y borrar.sh para Cloud Shell.'),
            deck('Prácticas en Google Cloud, paso a paso (diapositivas)', f'{S4}/practicas-gcp/index.html',
                 '27 diapositivas para el alumnado: por práctica, qué se aprende, qué crea, las órdenes para copiar en Cloud Shell, la salida y la captura reales, '
                 'los fallos que de verdad tuvimos y el borrado; costes y lecciones.', volver=True),
            deck('Laboratorio Cloud Journey: la API en Google Cloud sin claves (diapositivas)', f'{S4}/laboratorio-cloud-journey/index.html',
                 '29 diapositivas: preparar Google Cloud, variables de GitHub, desplegar con aprobación, probar la URL, el modelo en Vertex AI y borrar todo; '
                 'run real y capturas de la consola.', volver=True),
            alumno('Laboratorio Cloud Journey: guía paso a paso', f'{S4}/laboratorio-cloud-journey/guia.md', 'Cada orden, qué debes ver y si falla; lo mismo que las diapositivas, en texto.'),
            deck('Laboratorio de cierre: producción e2e del caso Retail (diapositivas)', f'{S4}/laboratorio-produccion-e2e/index.html',
                 '26 diapositivas: los tres modos de explotación, el panel, configurar el repositorio, versión nueva con puerta de calidad y aprobación, y rollback; capturas de runs reales.', volver=True),
            alumno('Laboratorio de cierre: guía paso a paso', f'{S4}/laboratorio-produccion-e2e/guia.md', 'Cada orden, qué debes ver y si falla.'),
            alumno('Configurar el repositorio (environment y permisos)', f'{S4}/laboratorio-produccion-e2e/CONFIGURAR-REPOSITORIO.md', 'Una sola vez, en Settings de tu fork; con capturas.'),
            alumno('Levantar el panel en el Codespace', f'{S4}/laboratorio-produccion-e2e/CODESPACE.md'),
            alumno('Workflow: puntuar por lotes (diario)', f'{S4}/laboratorio-produccion-e2e/puntuar-lote.yml'),
            alumno('Workflow: validar la producción completa', f'{S4}/laboratorio-produccion-e2e/validar-produccion.yml'),
            alumno('Workflow: nueva versión del modelo', f'{S4}/laboratorio-produccion-e2e/nueva-version.yml'),
            alumno('Workflow: rollback de la versión', f'{S4}/laboratorio-produccion-e2e/rollback.yml'),
            deck('Extra: un LLM y el estilo de color (diapositivas paso a paso)', f'{S4}/extra-estilo-llm/index.html',
                 '60 min. Instalar, ejecutar cada notebook (órdenes para copiar), los tres actos con sus cifras y capturas reales, y orquestarlo en GitHub Actions.', volver=True),
            alumno('Extra: un LLM y el estilo de color (tres actos)', f'{S4}/extra-estilo-llm/README.md',
                   'El LLM lee el estilo y falla, la línea base gana, el LLM lo explica con LoRA; notebooks y pipeline en GitHub Actions.'),
            alumno('Extra: el pipeline en GitHub Actions (guía)', f'{S4}/extra-estilo-llm/guia-pipeline.md'),
            alumno('Extra: checklist antes de usar Actions', f'{S4}/extra-estilo-llm/checklist-actions.md'),
            alumno('Extra 00 · preparar el entorno', f'{S4}/extra-estilo-llm/00_preparar_entorno.ipynb'),
            alumno('Extra 01 · datos fabricados', f'{S4}/extra-estilo-llm/01_datos_fabricados.ipynb'),
            alumno('Extra 02 · zero-shot', f'{S4}/extra-estilo-llm/02_zero_shot.ipynb'),
            alumno('Extra 03 · fine-tuning con LoRA', f'{S4}/extra-estilo-llm/03_fine_tuning_lora.ipynb'),
            alumno('Extra 04 · comparar y transferir', f'{S4}/extra-estilo-llm/04_comparar_y_transferir.ipynb'),
            alumno('Extra 05 · explicar el estilo', f'{S4}/extra-estilo-llm/05_explicar_estilo.ipynb'),
        ],
    ),
    dict(
        id='S5', titulo='MLOps y operación', horas='4 h', carpeta=S5, estado=PREPARADO, esperados=['guion', 'checklist', 'teoria', 'practica', 'tarea', 'rubrica', 'evidencia'],
        resumen='Versionado con alias de MLflow, deriva, monitoreo, registros y alertas, seguridad, rollback y costes. Tarea: repositorio, informe y demostración.',
        nota='Preparado por ahora: el laboratorio de agentes (carpeta laboratorio-agentes/: servidor MCP, un LLM local con Ollama, el agente con trazas '
             'en MLflow, skills, evaluación con 25 preguntas de oro y despliegue en GitHub con puerta de calidad, aprobación y rollback; '
             'cuatro workflows ensayados en GitHub Actions el 22 y 23/11/2026). Sin verificar: el compose con Ollama en Docker, el agente en un Codespace '
             'y el extra de dos agentes (solo planteado). Extra opcional: dos servidores MCP solo con notebooks (carpeta extra-mcp-notebooks/; BigQuery probado en Cloud Shell el 26/11/2026, los notebooks no en un Codespace). El MLOps clásico (deriva, alias champion y alerta) tiene su laboratorio, ensayado en GitHub Actions el 26/11/2026; los costes se explican en la teoría.',
        enlaces=[
            instructor('README de S5', f'{S5}/README.md'),
            instructor('Guion de la jornada del 27/11 (maratón): replicar repositorios, Dockerfiles, Actions de S4, recap de S4 y S5', f'{S5}/guion-jornada-27-11.md', 'Orden, qué decir, qué teclear, qué debes ver y si falla; sin recortes de tiempo.'),
            deck('Laboratorio de MLOps clásico: deriva, alias champion y alerta (diapositivas)', f'{S5}/laboratorio-mlops/index.html',
                 '27 diapositivas, unos 140 min: PSI y KS, AUC por corte, alias champion y rollback, y el workflow de monitoreo con issue de alerta; capturas de runs reales.', volver=True),
            alumno('Laboratorio de MLOps clásico: guía paso a paso', f'{S5}/laboratorio-mlops/guia.md', 'Cada orden, qué debes ver y si falla.'),
            alumno('Workflow: monitoreo del modelo', f'{S5}/laboratorio-mlops/monitoreo.yml'),
            alumno('MLOps clásico (detalle técnico)', '04-Proyecto-Base/docs/mlops-clasico.md'),
            alumno('Dónde se usa el modelo', '04-Proyecto-Base/docs/donde-se-usa-el-modelo.md', 'Los sitios donde se carga y se llama al modelo, y qué cambia con el alias champion.'),
            alumno('Teoría de S5', f'{S5}/teoria/README.md'),
            alumno('Guía de laboratorio de S5', f'{S5}/practica/guia-laboratorio.md'),
            alumno('Tarea de S5 (avance 5)', f'{S5}/tarea/README.md'),
            alumno('Rúbrica de S5', f'{S5}/tarea/rubrica.md'),
            alumno('Plantilla de la evidencia del avance 5', f'{S5}/evidencias/plantilla-avance-5.md'),
            alumno('Checklist de S5', f'{S5}/checklist.md'),
            instructor('Guion de S5', f'{S5}/guion.md'),
            deck('Recap final del curso: lo que ya sabes hacer (S0 a S5, diapositivas)', '01-Sesiones/recap/recap-final/index.html',
                 '48 diapositivas, ~71 min: el viaje de las 6 sesiones, mitos desmontados, qué te llevas de cada sesión con capturas reales, consejos, qué entregar (subir la tarea al Classroom, entrega final 11/12 a las 10:00 hora de Perú) y el repositorio que te llevas.', volver=True),
            deck('Clase: fundamentos de IA, LLM, RAG, agentes y sistemas agénticos (diapositivas)', f'{S5}/clase-fundamentos-ia-agentes/index.html',
                 '41 diapositivas, unos 64 min (propuesta; será la sesión de cierre y puede alargarse), de lo general a lo concreto: IA/ML/DL, transformers, LLM, embeddings, RAG, dato y contexto, herramientas y MCP, agentes, y dónde vive cada cosa en Google Cloud (12 capturas reales de la consola); notas del profesor en cada una.', volver=True),
            alumno('Clase de fundamentos: glosario', f'{S5}/clase-fundamentos-ia-agentes/glosario.md', 'Los términos de lo general a lo concreto, con un ejemplo de nuestro caso.'),
            deck('Laboratorio de agentes (diapositivas)', f'{S5}/laboratorio-agentes/index.html',
                 '30 diapositivas: servidor MCP, LLM local, agente y trazas, skills, evaluación con 25 preguntas de oro y despliegue en GitHub; capturas de runs reales.', volver=True),
            alumno('Laboratorio de agentes: guía paso a paso', f'{S5}/laboratorio-agentes/guia.md', 'L1 a L6 con cada orden, qué debes ver y si falla; el extra, solo planteado.'),
            alumno('Configurar el repositorio para los workflows del agente', f'{S5}/laboratorio-agentes/CONFIGURAR-REPOSITORIO.md', 'Remite a la configuración de S4 y explica lo nuevo.'),
            alumno('Workflow: CI del agente (LLM falso y humo)', f'{S5}/laboratorio-agentes/agente-ci.yml'),
            alumno('Workflow: evaluar con el LLM real', f'{S5}/laboratorio-agentes/agente-evaluar.yml'),
            alumno('Workflow: nueva versión del agente', f'{S5}/laboratorio-agentes/agente-nueva-version.yml'),
            alumno('Workflow: rollback del agente', f'{S5}/laboratorio-agentes/agente-rollback.yml'),
            deck('Extra: dos servidores MCP solo con notebooks (diapositivas)', f'{S5}/extra-mcp-notebooks/index.html',
                 '26 diapositivas, unos 72 min: un MCP que consulta la capa master en SQLite y BigQuery (con el SQL vigilado en capas) y un MCP con el modelo dentro, cargado por alias; salidas reales y prueba de BigQuery en Cloud Shell.', volver=True),
            alumno('Extra MCP · README (qué está probado y qué no)', f'{S5}/extra-mcp-notebooks/README.md'),
            alumno('Extra MCP 00 · preparar el entorno', f'{S5}/extra-mcp-notebooks/00_preparar_entorno.ipynb'),
            alumno('Extra MCP 01 · MCP de datos (SQLite y BigQuery)', f'{S5}/extra-mcp-notebooks/01_mcp_datos_sqlite_y_bigquery.ipynb'),
            alumno('Extra MCP 02 · MCP con el modelo (predicción)', f'{S5}/extra-mcp-notebooks/02_mcp_modelo_prediccion.ipynb'),
            deck('Extra MCP · laboratorio de la interfaz web (diapositivas)', f'{S5}/extra-mcp-notebooks/ui/index_slides.html',
                 '25 diapositivas tipo laboratorio, ~57 min: arrancar la interfaz paso a paso (cmd, PowerShell, Codespace), recorrido por las cinco pestañas con 17 capturas reales, 8 ataques SQL, promover y volver el alias, traza MCP y ejercicios; el chat con qwen2.5:0.5b se muestra tal cual, con sus fallos.', volver=True),
            alumno('Extra MCP · interfaz web que une los dos MCP y un LLM (README)', f'{S5}/extra-mcp-notebooks/ui/README.md', 'FastAPI en local, cinco pestañas: cliente, ¿y si…?, chat con el LLM, explorador MCP con SQL vigilado y modelo con alias; traza en vivo. 46 pruebas; BigQuery y Codespace sin verificar.'),
            deck('Extra: del champion de MLflow a un endpoint de Vertex AI desde Actions (diapositivas)', f'{S5}/extra-vertex-champion/index.html',
                 '30 diapositivas tipo laboratorio: imagen de predicción propia que devuelve la probabilidad, manifiesto con etiquetas MLflow↔Vertex, scripts de Cloud Shell (subir, desplegar con canario, probar, volver, borrar) y tres workflows de Actions; 216 pruebas con gcloud y docker simulados; Vertex, Docker y Actions reales sin verificar.', volver=True),
            alumno('Extra Vertex · README (qué está probado y qué no)', f'{S5}/extra-vertex-champion/README.md'),
            alumno('Extra Vertex · guía paso a paso (con coste y receta de ensayo)', f'{S5}/extra-vertex-champion/guia.md'),
            alumno('Extra Vertex · capturas pendientes (receta)', f'{S5}/extra-vertex-champion/capturas-pendientes.md'),
            alumno('Extra Vertex · workflow: desplegar', f'{S5}/extra-vertex-champion/vertex-desplegar.yml'),
            alumno('Extra Vertex · workflow: rollback', f'{S5}/extra-vertex-champion/vertex-rollback.yml'),
            alumno('Extra Vertex · workflow: borrar', f'{S5}/extra-vertex-champion/vertex-borrar.yml'),
            deck('Extra: el lote del modelo orquestado con Airflow de Google Cloud (diapositivas)', f'{S5}/extra-composer-batch/index.html',
                 '27 diapositivas tipo laboratorio: el DAG retencion_lote sobre la imagen que ya lleva el modelo, comandos manuales (Airflow local y Cloud Composer), la pestaña «Lote» de la interfaz, y GitHub Actions; capturas reales y 11 pendientes con su receta.', volver=True),
            alumno('Extra Composer · README (qué está probado y qué no)', f'{S5}/extra-composer-batch/README.md'),
            alumno('Extra Composer · comandos manuales paso a paso', f'{S5}/extra-composer-batch/comandos.md', 'Airflow local con Docker y Cloud Composer con gcloud; qué debes ver y si falla.'),
            alumno('Extra Composer · el DAG retencion_lote', f'{S5}/extra-composer-batch/dags/retencion_lote.py'),
            alumno('Extra Composer · workflow: lanzar el lote', f'{S5}/extra-composer-batch/lote-composer.yml'),
            alumno('Extra Composer · workflow: subir el DAG', f'{S5}/extra-composer-batch/dags-composer.yml'),
            alumno('Extra Composer · capturas pendientes (receta)', f'{S5}/extra-composer-batch/capturas-pendientes.md'),
        ],
    ),
]

LEYENDA = ('«Material preparado» significa que el material existe, no que esté probado en Windows ni en el proyector: '
           'eso se detalla en ESTADO-DEL-PAQUETE.md y en 03-Entorno/VALIDACION.md.')
