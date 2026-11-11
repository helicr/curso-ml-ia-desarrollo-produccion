"""Los ejemplos y las roturas de la guía de contenedores: ÚNICA FUENTE de los comandos.

Lo leen dos programas:
  ejecutar.py   ejecuta cada comando con Docker de verdad (en GitHub Actions) y guarda la salida real en salidas-reales.json
  generar.py    escribe la guía en texto y las presentaciones con esos mismos comandos y esas salidas

Un paso (`P`) es un comando que el alumno escribe tal cual en la terminal de su Codespace:
  cmd        el comando (una sola línea de shell)
  que        qué ha pasado, en una o dos frases (se muestra bajo la salida)
  rc         código de salida esperado: 0, un número, una lista de números o 'distinto' (cualquiera salvo 0)
  espera     expresión regular que la salida DEBE contener (si no, el ejecutor falla)
  no_espera  expresión regular que la salida NO debe contener
  pausa      segundos que el ejecutor espera ANTES de lanzarlo (el alumno, cuando haga falta, lo verá en la nota)
  mostrar    ('ultimas', n) o ('primeras', n): cuántas líneas de la salida se enseñan en la guía; None = todas
  norm       lista de (regex, reemplazo) que se aplican a la salida para quitar lo que cambia en cada ejecución
"""

FECHA = '10/11/2026'
CARPETA = '01-Sesiones/S2-API-y-Docker/contenedores/ejemplos'
IMAGEN_BASE = 'python:3.11-slim'

# Lo que cambia en cada ejecución y no enseña nada: se acorta o se sustituye (la guía avisa de ello).
NORM_ID = [
    (r'(?m)^([0-9a-f]{12})[0-9a-f]{52}$', r'\1…'),                 # identificador largo de contenedor (solo la línea)
    (r'sha256:([0-9a-f]{12})[0-9a-f]{52}', r'sha256:\1…'),          # resumen de imagen
    (r'"ts": [0-9.]+', '"ts": …'),                                   # marca de tiempo de los registros JSON
    (r'\x1b\[[0-9;]*m', ''),                                          # colores de la terminal
    (r'(?m)^WARNING: This output is designed for human readability.*\n', ''),   # aviso de `docker image ls` cuando no hay terminal
    (r'ref [a-z0-9]+::[a-z0-9]+', 'ref …'),                          # identificador interno de la caché de construcción
    (r'\(([0-9a-f]{12})[0-9a-f]{52}\)', r'(\1…)'),                    # identificador largo entre paréntesis (p. ej. el «endpoint» del error de puerto ocupado)
]


def P(cmd, que='', rc=0, espera=None, no_espera=None, pausa=0, mostrar=None, norm=()):
    return dict(cmd=cmd, que=que, rc=rc, espera=espera, no_espera=no_espera, pausa=pausa, mostrar=mostrar,
                norm=list(NORM_ID) + list(norm))


FILTRO_CAPAS = r'''2>&1 | grep -E "\[[0-9]+/[0-9]+\]|CACHED"'''

EJEMPLOS = [
    # ------------------------------------------------------------------------------------------------ 1
    dict(id='e1', num=1, titulo='Imagen y contenedor', minutos=8, carpeta=None,
         resumen='Qué es una imagen, qué es un contenedor y por qué un contenedor «desaparece» cuando termina.',
         pasos=[
             P('docker pull python:3.11-slim',
               'Descarga la imagen: una plantilla de solo lectura con Linux y Python 3.11. La primera vez tarda; luego ya está en tu máquina.',
               espera=r'(Downloaded newer image|Image is up to date)', mostrar=('ultimas', 3)),
             P('docker image ls python:3.11-slim',
               'Lista las imágenes que tienes. Una imagen no se ejecuta: se usa para crear contenedores. (**Disk usage** es lo que ocupa descomprimida en disco; **content size**, lo que se descargó. Según tu versión de Docker las columnas pueden variar.)', espera=r'python'),
             P('docker run --rm python:3.11-slim python -c "import sys; print(sys.version)"',
               'Crea un contenedor desde la imagen, ejecuta un comando dentro, imprime y se borra solo (`--rm`).', espera=r'3\.11\.\d+'),
             P('docker run --rm python:3.11-slim sh -c "head -2 /etc/os-release"',
               'Dentro hay otro Linux, aunque tu Codespace sea otra cosa. Lo que ves es la imagen, no tu máquina.', espera=r'Debian'),
             P('docker ps -a',
               'Lista todos los contenedores, también los parados. Está vacía: los dos anteriores se borraron al terminar (`--rm`).',
               espera=r'CONTAINER ID', no_espera=r'python:3\.11-slim'),
             P('''docker run --name hola python:3.11-slim python -c "print('hola desde un contenedor')"''',
               'Esta vez sin `--rm` y con nombre. El proceso termina enseguida, pero el contenedor se queda.', espera=r'hola desde un contenedor'),
             P(r'docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"',
               'Sigue ahí, parado: `Exited (0)` significa que su proceso terminó bien.', espera=r'hola\s+python:3\.11-slim\s+Exited \(0\)'),
             P('docker rm hola', 'Borra el contenedor (la imagen sigue intacta).', espera=r'^hola$'),
         ],
         aprende=['Una **imagen** es la plantilla de solo lectura; un **contenedor** es una ejecución de esa imagen. De una imagen salen tantos contenedores como quieras.',
                  'Un contenedor **vive lo que vive su proceso**: cuando el comando termina, el contenedor se para (`Exited`).',
                  '`--rm` borra el contenedor al terminar; sin él se acumulan y hay que borrarlos con `docker rm`.'],
         piensa=['¿Qué pasa con la imagen cuando borras un contenedor?', '¿Por qué `docker ps` (sin `-a`) no mostraba `hola` aunque existiera?']),

    # ------------------------------------------------------------------------------------------------ 2
    dict(id='e2', num=2, titulo='Ciclo de vida y lo que se pierde', minutos=10, carpeta=None,
         resumen='Arrancar, mirar los registros, entrar, parar y volver a arrancar; y comprobar que lo escrito dentro desaparece con el contenedor.',
         pasos=[
             P('''docker run -d --name reloj python:3.11-slim sh -c "while true; do echo tic; sleep 1; done"''',
               '`-d` lo deja en segundo plano y devuelve su identificador. El proceso (un bucle) no termina nunca.', espera=r'^[0-9a-f]{12}…$'),
             P('docker logs --tail 3 reloj', 'Lo que el proceso escribe en pantalla (stdout) queda guardado: es donde la API deja sus registros.',
               pausa=3, espera=r'tic'),
             P('docker exec reloj sh -c "ls / | head -5"', '`exec` ejecuta otro comando **dentro** del contenedor que ya está en marcha.', espera=r'bin'),
             P('docker stop reloj', 'Pide al proceso que pare y, si no lo hace, lo mata a los 10 s. Aquí tarda **10 segundos**: el bucle de `sh` no atiende la señal de parada, y Docker lo mata (verás `Exited (137)`). Una API como uvicorn sí la atiende y para en un instante.', espera=r'^reloj$'),
             P(r'docker ps -a --format "table {{.Names}}\t{{.Status}}"', 'Parado, no borrado. `137` = 128 + 9: el proceso terminó por la señal 9 (KILL).', espera=r'reloj\s+Exited \(137\)'),
             P('docker start reloj', 'Un contenedor parado se puede volver a arrancar: conserva su configuración.', espera=r'^reloj$'),
             P(r'docker ps --format "table {{.Names}}\t{{.Status}}"', 'Vuelve a estar en marcha.', pausa=1, espera=r'reloj\s+Up'),
             P('docker rm -f reloj', '`-f` lo para y lo borra de una vez.', espera=r'^reloj$'),
             P('''docker run --name efimero python:3.11-slim sh -c "echo dato > /tmp/nota.txt && cat /tmp/nota.txt"''',
               'Escribe un archivo dentro del contenedor y lo lee: funciona.', espera=r'^dato$'),
             P('docker rm efimero', 'Borramos ese contenedor.', espera=r'^efimero$'),
             P('docker run --rm python:3.11-slim cat /tmp/nota.txt',
               'Un contenedor nuevo, de la misma imagen, no tiene el archivo: lo escrito dentro murió con el contenedor anterior.',
               rc='distinto', espera=r'No such file or directory'),
         ],
         aprende=['`docker logs` enseña lo que el proceso escribe en la salida estándar; por eso la API registra en JSON por pantalla, no en un archivo.',
                  '`exec` es tu forma de «entrar» a mirar; `stop`/`start` conservan el contenedor; `rm` lo destruye.',
                  '**Lo que se escribe dentro de un contenedor desaparece con él.** Para que algo sobreviva hay que usar un volumen (ejemplo 7) o guardarlo fuera.'],
         piensa=['¿Dónde guardarías las predicciones que genera una API si el contenedor puede borrarse en cualquier momento?',
                 '¿Qué diferencia hay entre `docker stop` y `docker rm`?']),

    # ------------------------------------------------------------------------------------------------ 3
    dict(id='e3', num=3, titulo='Puertos: llegar al contenedor desde fuera', minutos=10, carpeta=None,
         resumen='Por qué sin `-p` no se llega al servicio, qué hace `-p 8000:8000` y por qué la API escucha en `0.0.0.0`.',
         pasos=[
             P('docker run -d --name web python:3.11-slim python -m http.server 8000',
               'Un servidor web mínimo que escucha en el puerto 8000 **dentro** del contenedor. No publicamos ningún puerto.', espera=r'^[0-9a-f]{12}…$'),
             P('curl -sS --max-time 3 http://127.0.0.1:8000/', 'El servicio funciona, pero desde tu máquina no hay camino hasta él.',
               pausa=2, rc='distinto', espera=r'(Failed to connect|Connection refused)'),
             P('docker rm -f web', 'Lo borramos para repetirlo publicando el puerto.', espera=r'^web$'),
             P('docker run -d --name web -p 8000:8000 python:3.11-slim python -m http.server 8000',
               '`-p 8000:8000` conecta el puerto 8000 de tu máquina (izquierda) con el 8000 del contenedor (derecha).', espera=r'^[0-9a-f]{12}…$'),
             P('curl -sS -o /dev/null -w "%{http_code}\\n" http://127.0.0.1:8000/', 'Ahora responde 200.', pausa=2, espera=r'^200$'),
             P('docker port web', 'Muestra qué puertos están publicados.', espera=r'8000/tcp -> 0\.0\.0\.0:8000'),
             P('docker rm -f web', 'Borramos el anterior.', espera=r'^web$'),
             P('docker run -d --name web -p 8000:8000 python:3.11-slim python -m http.server 8000 --bind 127.0.0.1',
               'El mismo servidor, pero escuchando **solo en 127.0.0.1 dentro del contenedor**. Publicamos el puerto igual.', espera=r'^[0-9a-f]{12}…$'),
             P('curl -sS --max-time 3 http://127.0.0.1:8000/',
               'El puerto está publicado y aun así falla: el tráfico entra por la red del contenedor, no por su «127.0.0.1», y el servicio no lo atiende.',
               pausa=2, rc='distinto', espera=r'\((52|56)\)'),
             P('docker rm -f web', 'Limpiamos.', espera=r'^web$'),
         ],
         aprende=['Los puertos de un contenedor no son accesibles hasta que los **publicas** con `-p máquina:contenedor`.',
                  'Dentro del contenedor el servicio debe escuchar en **`0.0.0.0`** (todas las interfaces); si escucha solo en `127.0.0.1`, nadie de fuera lo alcanza. Por eso la API del curso arranca con `--host 0.0.0.0`.',
                  'Dos contenedores no pueden publicar el mismo puerto de tu máquina (lo verás en la rotura 1).'],
         piensa=['La respuesta a la pregunta del laboratorio de S2: ¿por qué el contenedor de la API escucha en `0.0.0.0` y no en `127.0.0.1`?']),

    # ------------------------------------------------------------------------------------------------ 4
    dict(id='e4', num=4, titulo='Tu primera imagen: Dockerfile y capas', minutos=10, carpeta='04-primera-imagen',
         resumen='Construir una imagen de cuatro líneas y ver que está hecha de capas.',
         pasos=[
             P('docker build --progress=plain -t saludo:1 . 2>&1 | grep -E "\\[[0-9]+/[0-9]+\\]|naming to"',
               'Construye la imagen `saludo:1` a partir del `Dockerfile` de esta carpeta (`.` es el **contexto**: la carpeta cuyos archivos puede copiar). Filtramos la salida para ver los **pasos**: uno por instrucción. (En tu terminal verás la salida con barras de progreso; aquí va en texto.)',
               espera=r'\[3/3\] COPY app\.py'),
             P('docker run --rm saludo:1', 'Un contenedor de tu imagen: ejecuta `app.py`.', espera=r'Hola desde un contenedor con Python 3\.11'),
             P(r'docker history --format "{{.Size}}\t{{.CreatedBy}}" saludo:1 | head -5',
               'Las capas, de la última a la primera: `CMD`, `COPY`, `WORKDIR` son las tuyas; debajo está la imagen base.', espera=r'COPY app\.py', mostrar=None,
               norm=[(r'\s+#\s*buildkit', '')]),
             P('docker image ls python:3.11-slim', 'Tamaño de la imagen base…', espera=r'python'),
             P('docker image ls saludo:1', '…y el de la tuya: casi lo mismo. Casi todo el peso viene de la base; tus cuatro líneas añaden muy poco.', espera=r'saludo'),
         ],
         aprende=['Un **Dockerfile** es una receta: cada instrucción (`FROM`, `WORKDIR`, `COPY`, `RUN`…) añade una **capa** a la imagen.',
                  '`FROM` elige la base; casi todo el tamaño viene de ella. `CMD` es lo que se ejecuta al crear un contenedor.',
                  'El **contexto** (`.`) es lo que Docker puede copiar a la imagen: solo lo que esté en esa carpeta.'],
         piensa=['¿Qué cambiarías para que imprima otro saludo? ¿Basta con editar `app.py`, o hay que volver a construir?']),

    # ------------------------------------------------------------------------------------------------ 5
    dict(id='e5', num=5, titulo='La caché de capas: construir sin esperar', minutos=12, carpeta='05-cache',
         resumen='Dos Dockerfiles que hacen lo mismo con distinto orden. Uno reinstala las dependencias a cada cambio; el otro no.',
         pasos=[
             P(f'docker build --progress=plain -f Dockerfile.malo -t cache:malo . {FILTRO_CAPAS}',
               '`Dockerfile.malo` copia todo el código y **después** instala las dependencias. Primera construcción: instala todo (el `WORKDIR` puede salir como `CACHED` porque el ejemplo anterior ya creó esa capa).',
               espera=r'RUN pip install', no_espera=r'RUN pip install[^\n]*\n#\d+ CACHED'),
             P('echo "# cambio" >> app.py', 'Cambiamos una sola línea del código.', mostrar=('primeras', 0)),
             P(f'docker build --progress=plain -f Dockerfile.malo -t cache:malo . {FILTRO_CAPAS}',
               'Se vuelve a ejecutar `RUN pip install`: el `COPY . .` cambió y arrastra todas las capas siguientes. Cada cambio de código cuesta una reinstalación completa.',
               espera=r'RUN pip install', no_espera=r'RUN pip install[^\n]*\n#\d+ CACHED'),
             P(f'docker build --progress=plain -f Dockerfile.bueno -t cache:bueno . {FILTRO_CAPAS}',
               '`Dockerfile.bueno` copia **solo `requirements.txt`**, instala, y copia el código al final. Primera construcción: instala.',
               espera=r'RUN pip install'),
             P('echo "# otro cambio" >> app.py', 'Otro cambio de código.', mostrar=('primeras', 0)),
             P(f'docker build --progress=plain -f Dockerfile.bueno -t cache:bueno . {FILTRO_CAPAS}',
               'Ahora `RUN pip install` sale con **CACHED**: Docker reutiliza la capa porque `requirements.txt` no cambió. Solo se rehace el `COPY app.py`.',
               espera=r'RUN pip install[^\n]*\n#\d+ CACHED'),
             P('docker run --rm cache:bueno', 'La imagen funciona igual.', espera=r'numpy 1\.26\.4'),
             P("sed -i '/^# /d' app.py", 'Quita las líneas que añadimos para dejar `app.py` como estaba.', mostrar=('primeras', 0)),
         ],
         aprende=['Docker reutiliza una capa si **ella y todas las anteriores** no han cambiado. Un cambio invalida esa capa y todas las siguientes.',
                  '**Regla de oro:** primero lo que casi nunca cambia (dependencias), al final lo que cambia siempre (tu código). Es lo que hace el `Dockerfile` del proyecto: `COPY requirements-api.lock` + `pip install`, y luego `COPY ia_mlops/`.',
                  'En un equipo, esto se traduce en minutos ahorrados en cada construcción, local y en CI.'],
         piensa=['En el `Dockerfile` del proyecto, ¿qué capa se reconstruye si cambias una línea de `ia_mlops/`? ¿Y si cambias `requirements-api.lock`?']),

    # ------------------------------------------------------------------------------------------------ 6
    dict(id='e6', num=6, titulo='Configuración y secretos: variables de entorno', minutos=10, carpeta='06-entorno',
         resumen='Pasar configuración al contenedor sin reconstruir la imagen, y por qué un secreto nunca va dentro de ella.',
         pasos=[
             P('docker build -q -t entorno:1 .', 'Una imagen que lee dos variables de entorno. (`-q` solo imprime el identificador de la imagen.)', espera=r'^sha256:'),
             P('docker run --rm entorno:1', 'Sin pasar nada: usa el valor por defecto que lleva la imagen y no ve el token.',
               espera=r'saludo: hola por defecto\ntoken presente: False'),
             P('docker run --rm -e SALUDO="hola desde -e" -e TOKEN_API=abc entorno:1', '`-e` pasa una variable **al arrancar**, sin tocar la imagen.',
               espera=r'saludo: hola desde -e\ntoken presente: True'),
             P(r'''printf 'SALUDO=desde archivo\nTOKEN_API=xyz\n' > mi.env''', 'Un archivo con las variables (`mi.env` está en `.gitignore`: no se sube).', mostrar=('primeras', 0)),
             P('docker run --rm --env-file mi.env entorno:1', '`--env-file` pasa todas las del archivo.', espera=r'saludo: desde archivo\ntoken presente: True'),
             P('docker build -f Dockerfile.mal -t entorno:mal . 2>&1 | grep SecretsUsedInArgOrEnv', 'Ahora la forma **incorrecta**: `ENV TOKEN_API=...` dentro del Dockerfile. La construcción funciona, pero Docker ya te avisa de que es mala idea.', espera=r'SecretsUsedInArgOrEnv'),
             P('docker history --no-trunc --format "{{.CreatedBy}}" entorno:mal | grep TOKEN_API',
               'El historial de la imagen lo enseña en claro…', espera=r'TOKEN_API'),
             P('docker inspect --format "{{.Config.Env}}" entorno:mal | grep -o "TOKEN_API=[^] ]*"', '…y `inspect` también. Quien tenga la imagen tiene el «secreto».', espera=r'TOKEN_API=no-es-un-secreto-real-123'),
             P('rm -f mi.env', 'Borra el archivo de ejemplo.', mostrar=('primeras', 0)),
         ],
         aprende=['La **configuración** (qué modelo, qué puerto, qué entorno) se pasa al arrancar con `-e` o `--env-file`: la misma imagen sirve para desarrollo y producción.',
                  'Un **secreto** (clave, contraseña, token) **nunca** va en `ENV`, en un `COPY` ni en la imagen: queda grabado en sus capas y se puede leer.',
                  'En la nube se inyectan desde un gestor de secretos (en GCP, Secret Manager, que veremos en S3) y llegan como variables o archivos montados al arrancar.'],
         piensa=['El `.dockerignore` del proyecto excluye `**/.env`, `**/*.key` y `**/credenciales*.json`. ¿Qué evita eso exactamente?']),

    # ------------------------------------------------------------------------------------------------ 7
    dict(id='e7', num=7, titulo='Volúmenes y montajes: datos que sobreviven', minutos=10, carpeta=None,
         resumen='Dos formas de que algo exista fuera del contenedor: un volumen que gestiona Docker y una carpeta tuya montada dentro.',
         pasos=[
             P('docker volume create datos', 'Un volumen es un almacenamiento que Docker guarda aparte de cualquier contenedor.', espera=r'^datos$'),
             P('docker run --rm -v datos:/datos python:3.11-slim sh -c "echo version 1 > /datos/nota.txt"', '`-v datos:/datos` monta el volumen en `/datos`. Escribimos un archivo y el contenedor se borra.', mostrar=('primeras', 0)),
             P('docker run --rm -v datos:/datos python:3.11-slim cat /datos/nota.txt', 'Otro contenedor, distinto, ve el mismo archivo: el dato sobrevivió.', espera=r'^version 1$'),
             P('mkdir -p modelo-demo && echo "modelo v1" > modelo-demo/modelo.txt', 'Ahora una carpeta **tuya** con un «modelo».', mostrar=('primeras', 0)),
             P('docker run --rm -v "$PWD/modelo-demo:/modelos:ro" python:3.11-slim cat /modelos/modelo.txt',
               'Montamos esa carpeta dentro del contenedor, en **solo lectura** (`:ro`).', espera=r'^modelo v1$'),
             P('echo "modelo v2" > modelo-demo/modelo.txt', 'Cambiamos el archivo en tu máquina…', mostrar=('primeras', 0)),
             P('docker run --rm -v "$PWD/modelo-demo:/modelos:ro" python:3.11-slim cat /modelos/modelo.txt',
               '…y el contenedor ve el cambio **sin reconstruir ninguna imagen**.', espera=r'^modelo v2$'),
             P('docker run --rm -v "$PWD/modelo-demo:/modelos:ro" python:3.11-slim sh -c "echo x > /modelos/otro.txt"',
               'Con `:ro` el contenedor no puede escribir en tu carpeta.', rc='distinto', espera=r'Read-only file system'),
             P('docker volume rm datos && rm -rf modelo-demo', 'Limpieza.', espera=r'^datos$'),
         ],
         aprende=['**Volumen** (`-v nombre:ruta`): lo gestiona Docker; sirve para datos que deben sobrevivir al contenedor (una base de datos, resultados).',
                  '**Montaje de carpeta** (`-v carpeta:ruta`): expone una carpeta tuya dentro; sirve para desarrollo y para cambiar datos o modelo sin reconstruir. `:ro` evita que el contenedor la modifique.',
                  'El proyecto del curso **copia el modelo dentro de la imagen** (`COPY models/...`): la imagen es autosuficiente y reproducible. Montarlo sería más flexible pero depende de que la carpeta esté donde toca.'],
         piensa=['¿Qué ventaja y qué riesgo tiene montar el modelo en lugar de copiarlo en la imagen?']),

    # ------------------------------------------------------------------------------------------------ 8
    dict(id='e8', num=8, titulo='Contexto, `.dockerignore`, tamaño y usuario no root', minutos=12, carpeta='08-contexto',
         resumen='Qué entra en la imagen sin que lo pienses, cómo evitarlo y por qué la imagen del curso no se ejecuta como root.',
         pasos=[
             P('dd if=/dev/zero of=datos-grandes.bin bs=1M count=50 status=none && du -h datos-grandes.bin', 'Creamos un archivo de 50 MB que **no** tiene nada que ver con la aplicación.', espera=r'50M'),
             P('docker build --progress=plain -t contexto:con-basura . 2>&1 | grep -E "transferring context|COPY \\. \\."',
               'Docker envía **toda la carpeta** (el contexto) al motor de construcción, incluido el archivo grande (la línea con MB), y el `COPY . .` lo mete en la imagen.', espera=r'transferring context: [0-9.]+MB'),
             P('docker image ls contexto:con-basura', 'La imagen engordó por un archivo que no usa: mira **DISK USAGE** (en nuestra ejecución, 240 MB frente a 187 MB de la imagen limpia que verás después). **CONTENT SIZE** casi no cambia solo porque un archivo lleno de ceros se comprime hasta casi nada.', espera=r'contexto'),
             P("printf 'datos-grandes.bin\\n' > .dockerignore", 'El `.dockerignore` lista lo que Docker debe **ignorar**.', mostrar=('primeras', 0)),
             P('docker build --progress=plain -t contexto:limpio . 2>&1 | grep -E "transferring context|COPY \\. \\."',
               'Mismo Dockerfile: el contexto ya no incluye el archivo grande (solo unos cientos de bytes).', espera=r'transferring context: [0-9.]+(B|kB) done'),
             P('docker image ls contexto:limpio', 'Y la imagen vuelve a su tamaño.', espera=r'contexto'),
             P('docker run --rm contexto:limpio', 'Por defecto el proceso corre como **root** (usuario 0) dentro del contenedor.', espera=r'numero 0'),
             P('docker build -q -f Dockerfile.noroot -t contexto:noroot .', '`Dockerfile.noroot` crea un usuario y cambia a él con `USER`. (`-q` solo imprime el identificador de la imagen.)', espera=r'^sha256:'),
             P('docker run --rm contexto:noroot', 'Ahora corre con el usuario 10001, sin privilegios: si alguien explota la aplicación, tiene menos margen.', espera=r'numero 10001'),
             P('rm -f datos-grandes.bin .dockerignore', 'Limpieza.', mostrar=('primeras', 0)),
         ],
         aprende=['`COPY . .` copia **todo lo que haya en el contexto**. Datos, claves, `.git`, cuadernos… todo acaba en la imagen salvo que lo excluyas en `.dockerignore`.',
                  'Un `.dockerignore` bien hecho hace la imagen más pequeña, la construcción más rápida y **evita filtrar secretos**. El del proyecto excluye `data/`, `notebooks/`, `tests/`, `.git`, claves…',
                  'Por defecto un contenedor corre como **root**. Producción exige un usuario sin privilegios (`USER`): es lo que hace la imagen del curso (usuario 10001).'],
         piensa=['Mira el `.dockerignore` de `04-Proyecto-Base/`. ¿Qué carpeta dejaría de ir en la imagen si la quitaras de ahí? ¿Y qué pasaría si `models/` estuviera en la lista?']),

    # ------------------------------------------------------------------------------------------------ 9
    dict(id='e9', num=9, titulo='Una API en un contenedor: salud, registros y límites', minutos=15, carpeta='09-api-minima',
         resumen='Una API pequeña (sin librerías) para ver, en miniatura, lo que hace la imagen del curso: comprobación de salud, registros JSON, usuario no root y límite de memoria.',
         pasos=[
             P('docker build -q -t api-minima:1 .', 'Imagen de una API de 40 líneas. Mira el `Dockerfile`: tiene `USER`, `EXPOSE` y un `HEALTHCHECK`.', espera=r'^sha256:'),
             P('docker run -d --name mini -p 8081:8080 -e MODELO=v2 --memory 128m api-minima:1',
               'Publica el puerto 8081, pasa la configuración (`MODELO`) y **limita la memoria a 128 MB**.', espera=r'^[0-9a-f]{12}…$'),
             P(r'docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"',
               'Recién arrancado: Docker aún no sabe si está sano (`health: starting`).', espera=r'mini\s+Up'),
             P(r'docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"',
               'Unos segundos después: el `HEALTHCHECK` del Dockerfile ha comprobado `/salud` y marca `healthy`. Es lo que usan los orquestadores para saber si reiniciarlo.',
               pausa=6, espera=r'\(healthy\)'),
             P('curl -s http://127.0.0.1:8081/modelo', 'La configuración llegó por la variable de entorno.', espera=r'"modelo": "v2"'),
             P('curl -s -o /dev/null -w "%{http_code}\\n" http://127.0.0.1:8081/nada', 'Una ruta que no existe responde 404.', espera=r'^404$'),
             P('docker logs mini', 'Los registros son JSON por pantalla, una línea por petición (incluidas las del healthcheck): fáciles de recoger y de filtrar.', espera=r'"evento": "arranque"'),
             P(r'docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}" mini', 'Memoria que usa frente al límite que le pusimos.', espera=r'/ 128MiB'),
             P('docker exec mini id -u', 'El proceso no es root.', espera=r'^10001$'),
             P('docker rm -f mini', 'Limpieza.', espera=r'^mini$'),
         ],
         aprende=['Una imagen de producción es mucho más que «que arranque»: **usuario sin privilegios**, **`HEALTHCHECK`**, **configuración por variables**, **registros por stdout** y **límites de recursos**. La imagen de la API del curso hace todo esto.',
                  '`docker ps` muestra la salud; `docker logs` los registros; `docker stats` el consumo; `docker exec` te deja mirar dentro.',
                  'Un límite de memoria que se supera mata el contenedor (lo verás en la rotura 4): un modelo grande necesita memoria suficiente.'],
         piensa=['Compara este `Dockerfile` con `04-Proyecto-Base/deploy/docker/Dockerfile`: ¿qué tienen igual y qué añade el del proyecto?']),
]

# --------------------------------------------------------------------------------------------------- roturas
ROTURAS = [
    dict(id='r1', num=1, titulo='El puerto ya está ocupado', minutos=5, carpeta=None,
         sintoma='Arrancas un segundo contenedor y Docker devuelve un error.',
         pasos=[
             P('docker run -d --name uno -p 8082:8000 python:3.11-slim python -m http.server 8000', 'El primero arranca bien.', espera=r'^[0-9a-f]{12}…$'),
             P('docker run -d --name dos -p 8082:8000 python:3.11-slim python -m http.server 8000', 'El segundo falla.', rc=125, espera=r'(port is already allocated|address already in use)'),
             P(r'docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"', 'Diagnóstico: `dos` se creó pero no arrancó (`Created`). El puerto 8082 de tu máquina ya lo tiene `uno`.', espera=r'dos\s+Created'),
         ],
         arreglo=[
             P('docker rm -f dos', 'Borra el que no arrancó.', espera=r'^dos$'),
             P('docker run -d --name dos -p 8083:8000 python:3.11-slim python -m http.server 8000', 'Publícalo en **otro puerto de tu máquina** (8083); dentro sigue siendo el 8000.', espera=r'^[0-9a-f]{12}…$'),
             P(r'docker ps --format "table {{.Names}}\t{{.Ports}}"', 'Los dos conviven.', espera=r'uno[\s\S]*dos|dos[\s\S]*uno'),
             P('docker rm -f uno dos', 'Limpieza.', espera=r'uno'),
         ],
         leccion='Cada puerto de tu máquina lo puede publicar un solo contenedor. Es el error `port is already allocated` del laboratorio de S2.'),

    dict(id='r2', num=2, titulo='El contenedor se para nada más arrancar', minutos=8, carpeta='R2-comando',
         sintoma='`docker run` termina al instante y no hace lo que esperas.',
         pasos=[
             P('docker build -q -t r2:1 .', 'La imagen se construye sin problemas.', espera=r'^sha256:'),
             P('docker run --name r2 r2:1', 'Pero el contenedor no hace lo que debería.', rc='distinto', espera=r"can't open file '/app/aap\.py'"),
             P(r'docker ps -a --format "table {{.Names}}\t{{.Status}}"', 'Diagnóstico 1: `Exited (2)`: el proceso terminó con error.', espera=r'r2\s+Exited \(2\)'),
             P('docker logs r2', 'Diagnóstico 2: el mensaje del proceso. Busca el archivo `aap.py`: el `CMD` del Dockerfile tiene una errata.', espera=r"aap\.py"),
         ],
         arreglo=[
             P("sed 's/aap.py/app.py/' Dockerfile > Dockerfile.arreglado", 'Corrige la errata en una copia del Dockerfile.', mostrar=('primeras', 0)),
             P('docker build -q -f Dockerfile.arreglado -t r2:2 .', 'Reconstruye.', espera=r'^sha256:'),
             P('docker run --rm r2:2', 'Ahora arranca.', espera=r'la aplicacion arranco bien'),
             P('docker rm r2 && rm Dockerfile.arreglado', 'Limpieza.', espera=r'^r2$'),
         ],
         leccion='Cuando un contenedor muere, el orden es: `docker ps -a` (¿cómo terminó?) → `docker logs` (¿qué dijo?) → corregir y reconstruir.'),

    dict(id='r3', num=3, titulo='La construcción falla: falta un archivo', minutos=8, carpeta='R3-copia',
         sintoma='`docker build` se detiene con un error de `COPY`.',
         pasos=[
             P('docker build -t r3:1 .', 'El `COPY` no encuentra el archivo del modelo.', rc='distinto', espera=r'not found', mostrar=('ultimas', 8)),
             P('ls', 'Diagnóstico: el Dockerfile copia `models/modelo.joblib` y esa carpeta no existe. Es el mismo error que en el proyecto del curso si no entrenas antes de construir.', espera=r'Dockerfile'),
         ],
         arreglo=[
             P('mkdir -p models && echo "modelo de ejemplo" > models/modelo.joblib', 'En el proyecto real, este paso es `python -m ia_mlops.pipeline` (genera `models/`).', mostrar=('primeras', 0)),
             P('docker build -q -t r3:2 .', 'Ahora construye.', espera=r'^sha256:'),
             P('docker run --rm r3:2', 'Y arranca.', espera=r'el modelo esta en la imagen'),
             P('rm -rf models', 'Limpieza.', mostrar=('primeras', 0)),
         ],
         leccion='Lo que `COPY` busca tiene que estar **dentro del contexto** y no estar excluido por `.dockerignore`. El modelo no viaja con el repositorio: se genera antes de construir.'),

    dict(id='r4', num=4, titulo='El contenedor muere por falta de memoria', minutos=8, carpeta=None,
         sintoma='El proceso desaparece sin mensaje de error y el código de salida es 137.',
         pasos=[
             P('''docker run --name oom --memory 64m --memory-swap 64m python:3.11-slim python -c "x = b'x' * (200 * 1024 * 1024); print('ok')"''',
               'Pedimos 200 MB dentro de un contenedor limitado a 64 MB. No hay traza de Python ni mensaje: lo mata el sistema.', rc=137),
             P(r'docker ps -a --format "table {{.Names}}\t{{.Status}}"', 'Diagnóstico 1: `Exited (137)` = 128 + 9: terminado con la señal 9 (KILL).', espera=r'oom\s+Exited \(137\)'),
             P('docker inspect --format "estado={{.State.Status}} salida={{.State.ExitCode}} oom={{.State.OOMKilled}}" oom',
               'Diagnóstico 2: el código es 137. El indicador `oom` (*Out Of Memory*) puede salir `true` o `false` según la versión de Docker y del kernel: **no te fíes solo de él**. La prueba definitiva es repetir con más memoria (abajo).',
               espera=r'salida=137'),
         ],
         arreglo=[
             P('''docker run --rm --memory 512m python:3.11-slim python -c "x = b'x' * (200 * 1024 * 1024); print('ok')"''', 'Con memoria suficiente funciona.', espera=r'^ok$'),
             P('docker rm oom', 'Limpieza.', espera=r'^oom$'),
         ],
         leccion='Un `137` significa «terminado a la fuerza» y, en un contenedor con límite, casi siempre es memoria: se confirma repitiendo con más. Cuando sirvas un modelo grande, el límite del contenedor (aquí `--memory`; en Cloud Run, la memoria del servicio) tiene que cubrirlo.'),

    dict(id='r5', num=5, titulo='«Arranca» pero no está en marcha', minutos=5, carpeta=None,
         sintoma='`docker run -d` devuelve un identificador, pero `docker ps` no muestra nada.',
         pasos=[
             P('docker run -d --name vacio python:3.11-slim', 'Arranca sin error.', espera=r'^[0-9a-f]{12}…$'),
             P('docker ps', 'No aparece: no está en marcha.', pausa=1, espera=r'CONTAINER ID', no_espera=r'vacio'),
             P(r'docker ps -a --format "table {{.Names}}\t{{.Status}}"', 'Diagnóstico: `Exited (0)` terminó **bien**… y enseguida.', espera=r'vacio\s+Exited \(0\)'),
             P('docker logs vacio', 'Sin salida: no hizo nada. Ejecutó `python` sin ningún script y sin terminal, así que el intérprete terminó al instante.', espera=None),
         ],
         arreglo=[
             P('docker run -d --name vivo python:3.11-slim sleep 300', 'Dale un proceso que no termine (un servidor, en la API real).', espera=r'^[0-9a-f]{12}…$'),
             P(r'docker ps --format "table {{.Names}}\t{{.Status}}"', 'Ahora sí está `Up`.', pausa=1, espera=r'vivo\s+Up'),
             P('docker rm -f vacio vivo', 'Limpieza.', espera=r'vacio'),
         ],
         leccion='Un contenedor vive lo que vive su proceso principal. Si «arranca» y desaparece, mira `docker ps -a` y `docker logs`: el proceso terminó.'),
]

TODOS = EJEMPLOS + ROTURAS
