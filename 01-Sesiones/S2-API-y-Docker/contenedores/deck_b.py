"""Presentación 2: «Del Dockerfile a producción» (ejemplos 4, 5, 6, 8 y 9 de la guía práctica + el laboratorio de roturas)."""
import re

import datos
from datos import E, META
from diapos import (PIE_REAL, TAG_DOC, TAG_REAL, lista_final, mini, portada, practica, sal_pre)
from marco import Presentacion, capas, card, esc, flujo, fmt, tabla, ul

TITULO = 'Del Dockerfile a producción'
STORE = 'contenedores-dockerfile-produccion-hecho'
B = 'Contenedores 2 de 2'
NUBE = 'https://docs.cloud.google.com/run/docs/container-contract'
DOCKERFILE_CURSO = '04-Proyecto-Base/deploy/docker/Dockerfile'
# Fragmentos del Dockerfile del proyecto que citamos en la diapositiva «La imagen del curso»; las pruebas comprueban que existen.
FRAGMENTOS_DOCKERFILE_CURSO = [
    'FROM python:3.11-slim', 'PYTHONUNBUFFERED=1', 'COPY requirements-api.lock .', 'RUN pip install -r requirements-api.lock',
    'COPY ia_mlops/ ia_mlops/', 'COPY models/modelo_mlflow/ models/modelo_mlflow/', 'COPY models/metadatos.json models/metadatos.json',
    'RUN useradd --uid 10001', 'USER 10001', 'EXPOSE 8080', 'HEALTHCHECK --interval=30s', '"--host", "0.0.0.0"', '"--port", "8080"']
FRAGMENTOS_DOCKERIGNORE_CURSO = ['.git', '**/.env', '**/*.key', '**/credenciales*.json', 'data/', 'notebooks/', 'tests/']


def _ultimo(patron, texto):
    m = re.findall(patron, texto)
    if not m:
        raise SystemExit(f'no encuentro {patron!r} en la salida real:\n{texto}')
    return m[-1]


def _tam_disco(ej, k):
    """Valor de DISK USAGE de la segunda línea de `docker image ls`."""
    sal = datos.salida(ej, k)
    m = re.search(r'\n\S+\s+\S+\s+([0-9.]+[kMG]B)\s', sal)
    if not m:
        raise SystemExit(f'no encuentro DISK USAGE en:\n{sal}')
    return m.group(1)


def dockerfile_a_produccion():
    P = Presentacion(TITULO, STORE, 'del-dockerfile-a-produccion', 'La guía en texto (guia-practica.md) tiene el mismo contenido.')
    ctx_malo = _ultimo(r'transferring context: ([0-9.]+[kMG]?B)', datos.salida('e8', 1))
    ctx_bueno = _ultimo(r'transferring context: ([0-9.]+[kMG]?B)', datos.salida('e8', 4))
    img_malo, img_bueno = _tam_disco('e8', 2), _tam_disco('e8', 5)
    t_malo, t_bueno = datos.segundos('e5', 2), datos.segundos('e5', 5)

    # 1 -------------------------------------------------------------------------------------------- portada
    portada(P, 'ML e IA: de desarrollo a producción · Contenedores 2 de 2', TITULO,
            'Cómo se escribe una imagen, por qué importa el orden de las líneas, qué no debe entrar y qué hace falta para que sea de producción. Con cinco prácticas y el laboratorio de roturas.',
            ['Dockerfile', 'Capas y caché', '.dockerignore', 'Secretos', 'Usuario no root', 'Healthcheck'])

    # 2 -------------------------------------------------------------------------------------------- anatomía
    docker4 = dict((n, t) for n, t, _ in datos.archivos_de(datos.por_id('e4')))['Dockerfile']
    P.libre('Anatomía de un Dockerfile', B, 'La receta de una imagen', 'Un Dockerfile es una receta: una instrucción, una capa',
            '<div class="cols" style="grid-template-columns:.75fr 1.25fr">'
            f'<div><pre class="real" style="font-size:15px;line-height:1.5;margin-top:0">{esc(docker4)}</pre>'
            '<p class="rn">El del ejemplo 4: cuatro líneas, una imagen que funciona.</p></div>'
            '<div>' + tabla(['Instrucción', 'Qué hace', 'Cuándo'], [
                ['<code>FROM</code>', 'Parte de una imagen base: un Debian 13 con Python 3.11', 'al construir'],
                ['<code>WORKDIR</code>', 'Carpeta de trabajo dentro de la imagen (la crea si no existe)', 'al construir'],
                ['<code>COPY</code>', 'Copia archivos del <b>contexto</b> (la carpeta del <code>.</code>) a la imagen', 'al construir'],
                ['<code>CMD</code>', 'El comando que ejecuta el contenedor al arrancar', '<b>al arrancar</b>']])
            + '<h3 style="margin-top:14px">Otras que verás hoy</h3>'
            + tabla(['', ''], [
                ['<code>RUN</code>', 'Ejecuta un comando al construir (<code>pip install</code>)'],
                ['<code>ENV</code>', 'Variable de entorno con un valor por defecto'],
                ['<code>USER</code>', 'Usuario con el que corre el proceso'],
                ['<code>EXPOSE</code>', 'Documenta el puerto; <b>no lo publica</b> (eso es <code>-p</code>)'],
                ['<code>HEALTHCHECK</code>', 'Cómo comprobar que el contenedor está sano']]).replace('<tr><th></th><th></th></tr>', '')
            + '</div></div>')

    # 3 -------------------------------------------------------------------------------------------- capas
    filas = []
    for i, linea in enumerate(datos.salida('e4', 2).split('\n')):
        tam, instr = linea.split('\t', 1)
        filas.append(('mio' if i < 3 else 'base', f'<code>{esc(instr)}</code>', tam))
    P.libre('Las capas', B, 'La imagen es una pila', 'Cada instrucción añade una capa de solo lectura',
            '<div class="cols" style="grid-template-columns:1.15fr .85fr">'
            '<div><h3>`docker history saludo:1` (real, de la última a la primera)</h3>'.replace('`', '') + capas(filas)
            + '<p class="rn">Dorado: las tuyas · azul: la imagen base (aquí solo se ven sus dos últimas). Las instrucciones que no tocan archivos (<code>CMD</code>) pesan 0 B.</p></div>'
            '<div class="side">'
            + card('Qué implica', ul([fmt('Una imagen = **una pila de capas**; el contenedor añade encima una fina de escritura.'),
                                     fmt('Las capas se **reutilizan** entre imágenes y entre construcciones.'),
                                     fmt('Casi todo el peso viene de la base; tus líneas añaden poco.')], True))
            + card('Reutilización, vista de verdad', '<p class="small" style="font-size:13.5px">En el ejemplo 5, <code>WORKDIR /app</code> salió <b>CACHED</b>: esa capa ya existía de la imagen anterior.</p>'
                   + sal_pre('e5', 0, 4), 'ok')
            + '</div></div>')

    # 4 -------------------------------------------------------------------------------------------- práctica A (ejemplo 4)
    practica(P, 'pa', B, 'Práctica A · Tu primera imagen', 'e4', [0, 1, 2, 3, 4],
             'Construye una imagen de cuatro líneas, ejecútala y mira sus capas y su tamaño. Antes de construir, abre `Dockerfile` y `app.py` en el editor y léelos.',
             [0, 2, 4],
             ['¿Qué cambiarías para que imprima otro saludo? ¿Basta con editar `app.py` o hay que volver a construir?'], max_lineas=5)

    # 5 -------------------------------------------------------------------------------------------- orden y caché
    P.libre('Orden y caché', B, 'La regla de oro', 'Lo que casi nunca cambia, primero; lo que cambia siempre, al final',
            '<div class="two">'
            + card('Orden malo · <code>Dockerfile.malo</code>', capas([
                ('base', '<code>FROM</code> + <code>WORKDIR</code>', 'reutilizadas'),
                ('mio', '<code>COPY . .</code>', 'cambia a cada edición'),
                ('rw', '<code>RUN pip install -r requirements.txt</code>', 'se rehace siempre')]), 'bad')
            + card('Orden bueno · <code>Dockerfile.bueno</code>', capas([
                ('base', '<code>FROM</code> + <code>WORKDIR</code>', 'reutilizadas'),
                ('base', '<code>COPY requirements.txt .</code>', 'reutilizada'),
                ('base', '<code>RUN pip install -r requirements.txt</code>', 'CACHED'),
                ('mio', '<code>COPY app.py .</code>', 'cambia a cada edición')]), 'ok')
            + '</div>'
            '<p class="rn">Azul: capa reutilizada · dorado: la capa que cambia · verde discontinuo: se rehace por arrastre.</p>'
            '<p style="font-size:16.5px;line-height:1.42;margin-top:8px">Docker reutiliza una capa si <b>ella y todas las anteriores</b> no han cambiado; un cambio invalida esa capa y las siguientes. '
            f'Es lo que hace el <code>Dockerfile</code> del proyecto: primero <code>COPY requirements-api.lock</code> y <code>pip install</code>, y después <code>COPY ia_mlops/</code> '
            f'(<code>{DOCKERFILE_CURSO}</code>).</p>')

    # 6 -------------------------------------------------------------------------------------------- práctica B (ejemplo 5)
    practica(P, 'pb', B, 'Práctica B · La caché de capas', 'e5', [0, 1, 2, 3, 4, 5],
             f'Construye los dos Dockerfiles, cambia una línea del código y reconstruye. En nuestra ejecución, el orden malo tardó {t_malo:.1f} s y el bueno {t_bueno:.1f} s '
             '(depende de la red y de la máquina: fíjate sobre todo en **CACHED**).',
             [2, 5],
             ['En el `Dockerfile` del proyecto, ¿qué capa se reconstruye si cambias una línea de `ia_mlops/`? ¿Y si cambias `requirements-api.lock`?'], max_lineas=5)

    # 7 -------------------------------------------------------------------------------------------- contexto y .dockerignore
    P.libre('Contexto y .dockerignore', B, 'Qué entra en la imagen sin que lo pienses', '`COPY . .` copia todo lo que haya en el contexto',
            flujo([('Carpeta', 'todo lo que hay en el <code>.</code>', ''), ('Contexto', 'Docker lo envía al motor de construcción', 'warn'),
                   ('<code>COPY . .</code>', 'lo mete en la imagen', 'bad')])
            + '<div class="two mt">'
            + card('Medido (real)', tabla(['', 'Sin <code>.dockerignore</code>', 'Con <code>.dockerignore</code>'], [
                ['Contexto enviado', f'<b>{ctx_malo}</b>', f'<b>{ctx_bueno}</b>'],
                ['Imagen (DISK USAGE)', f'<b>{img_malo}</b>', f'<b>{img_bueno}</b>']])
                   + '<p class="rn">Un archivo de 50 MB que no tiene nada que ver con la aplicación. <b>CONTENT SIZE</b> casi no cambia porque un archivo lleno de ceros se comprime hasta casi nada.</p>', 'ok')
            + card('Qué ganas con un buen <code>.dockerignore</code>', ul([
                fmt('Imagen **más pequeña** y construcción **más rápida**.'),
                fmt('**No filtras secretos**: el del proyecto excluye `**/.env`, `**/*.key` y `**/credenciales*.json`.'),
                fmt('Tampoco entran `.git`, `data/`, `notebooks/` ni `tests/`.')], True))
            + '</div>')

    # 8 -------------------------------------------------------------------------------------------- práctica C (ejemplo 8)
    practica(P, 'pc', B, 'Práctica C · Contexto y .dockerignore', 'e8', [0, 1, 2, 3, 4, 5],
             'Crea un archivo de 50 MB, construye con él, añade un `.dockerignore` y vuelve a construir. Fíjate en «transferring context» y en el tamaño de la imagen.',
             [1, 4],
             ['Mira el `.dockerignore` de `04-Proyecto-Base/`. ¿Qué carpeta dejaría de ir en la imagen si la quitaras de ahí? ¿Y qué pasaría si `models/` estuviera en la lista?'], max_lineas=4)

    # 9 -------------------------------------------------------------------------------------------- configuración y secretos
    P.libre('Configuración y secretos', B, 'Variables de entorno', 'La configuración va al arrancar; el secreto, nunca en la imagen',
            '<div class="two">'
            + card('Bien · al arrancar', '<p class="small" style="font-size:14px"><code>-e NOMBRE=valor</code> o <code>--env-file archivo</code>: la misma imagen sirve para desarrollo y producción.</p>'
                   + mini('e6', 2, 3) + mini('e6', 4, 3), 'ok')
            + card('Mal · <code>ENV TOKEN_API=…</code> en el Dockerfile', '<p class="small" style="font-size:14px">Construye sin error, pero queda grabado en las capas: quien tenga la imagen lo lee.</p>'
                   + mini('e6', 5, 2, clase='bad') + mini('e6', 6, 2, clase='bad'), 'bad')
            + '</div>'
            f'<p style="font-size:15.5px;line-height:1.4;margin-top:10px">Las claves reales se inyectan desde un <b>gestor de secretos</b> (en GCP, Secret Manager) y llegan al contenedor como variables o archivos al arrancar. '
            f'Eso se verá en S3. {TAG_DOC}</p>')

    # 10 ------------------------------------------------------------------------------------------- práctica D (ejemplo 6)
    practica(P, 'pd', B, 'Práctica D · Configuración y secretos', 'e6', [0, 1, 2, 3, 4, 5, 6, 8],
             'Pasa variables con `-e` y con un archivo, y comprueba con tus ojos que un `ENV` con un «secreto» queda a la vista en el historial de la imagen.',
             [2, 4, 6],
             ['El `.dockerignore` del proyecto excluye `**/.env`, `**/*.key` y `**/credenciales*.json`. ¿Qué evita eso exactamente?'], max_lineas=3)

    # 11 ------------------------------------------------------------------------------------------- imagen de producción
    usuario = f'Sin USER:\n{datos.salida("e8", 6)}\nCon USER 10001:\n{datos.salida("e8", 8)}'
    P.libre('Una imagen de producción', B, 'Más que «que arranque»', 'Lo que distingue una imagen de producción',
            '<div class="pair">'
            + card('Usuario sin privilegios', '<p class="small" style="font-size:14px"><code>USER 10001</code>: si alguien explota la aplicación, tiene menos margen.</p>'
                   f'<pre class="real g">{esc(usuario)}</pre>', 'ok')
            + card('Comprobación de salud', '<p class="small" style="font-size:14px"><code>HEALTHCHECK</code>: Docker (o la nube) sabe si responde.</p>' + sal_pre('e9', 3, 2), 'ok')
            + card('Registros por pantalla', '<p class="small" style="font-size:14px">JSON a stdout, una línea por petición: <code>docker logs</code>.</p>' + sal_pre('e9', 6, 3), 'ok')
            + card('Límites de recursos', '<p class="small" style="font-size:14px"><code>--memory 128m</code>. Si el proceso se pasa, lo matan: <code>137</code> (rotura 4).</p>' + sal_pre('e9', 7, 2), 'ok')
            + '</div>')

    # 12 ------------------------------------------------------------------------------------------- práctica E (ejemplo 9)
    practica(P, 'pe', B, 'Práctica E · Una API de producción en miniatura', 'e9', [0, 1, 3, 6, 7, 8, 9],
             'Una API de 40 líneas con usuario sin privilegios, `HEALTHCHECK`, registros JSON y límite de memoria. Espera ~6 s tras el `docker run` para ver `healthy` (antes sale `health: starting`).',
             [3, 6, 7],
             ['Compara este `Dockerfile` con `04-Proyecto-Base/deploy/docker/Dockerfile`: ¿qué tienen igual y qué añade el del proyecto?'], max_lineas=4)

    # 13 ------------------------------------------------------------------------------------------- la imagen del curso
    P.libre('La imagen del curso', B, DOCKERFILE_CURSO, 'La imagen de la API del curso, línea a línea',
            tabla(['En el Dockerfile del proyecto', 'Para qué', 'Dónde lo has visto'], [
                ['<code>FROM python:3.11-slim</code>', 'La misma base que los ejemplos', 'Ejemplos 1 y 4'],
                ['<code>ENV PYTHONUNBUFFERED=1 …</code>', 'Ajustes de Python y de pip y la ruta del modelo; ninguno es un secreto', 'Ejemplo 6'],
                ['<code>COPY requirements-api.lock .</code> + <code>RUN pip install -r …</code>', 'Dependencias <b>primero</b>: la capa solo se rehace si cambian las versiones', 'Ejemplo 5'],
                ['<code>COPY ia_mlops/ …</code> + <code>COPY models/modelo_mlflow/ …</code>', 'Solo el código y el modelo necesarios; el modelo viaja <b>dentro</b> de la imagen', 'Ejemplos 7 y 8 · rotura 3'],
                ['<code>.dockerignore</code>', 'Deja fuera datos, cuadernos, pruebas, <code>.git</code> y claves', 'Ejemplo 8'],
                ['<code>RUN useradd --uid 10001 …</code> + <code>USER 10001</code>', 'No se ejecuta como root', 'Ejemplos 8 y 9'],
                ['<code>EXPOSE 8080</code> + <code>HEALTHCHECK --interval=30s …</code>', 'Puerto de la API y comprobación de salud (en el ejemplo, cada 3 s para verlo en vivo)', 'Ejemplo 9'],
                ['<code>CMD ["uvicorn", … "--host", "0.0.0.0", "--port", "8080"]</code>', 'Proceso principal; escucha en todas las interfaces', 'Ejemplo 3']]))

    # 14 ------------------------------------------------------------------------------------------- nube
    P.libre('Qué cambia en la nube', B, 'Cloud Run · S3', 'Lo que Google documenta del contenedor en Cloud Run',
            f'<p style="margin-bottom:8px">{TAG_DOC}</p>'
            + tabla(['Tema', 'Qué dice la documentación de Google', 'Con lo que has practicado'], [
                ['Puerto y dirección', 'Debe escuchar en <code>0.0.0.0</code>, en el puerto al que se envían las peticiones (<b>8080</b> por defecto, configurable). Cloud Run inyecta la variable <code>PORT</code>.',
                 'Ejemplo 3 · la API del curso usa 8080 y 0.0.0.0'],
                ['Memoria', 'Si se supera el límite configurado, la instancia se termina.', 'Rotura 4 · código 137'],
                ['Sistema de archivos', 'Está en memoria y lo escrito no persiste cuando la instancia se detiene.', 'Ejemplos 2 y 7 · lo escrito dentro se pierde'],
                ['Secretos y registros', 'No consultado en este material.', 'Se verá en S3 (Secret Manager y registros)']])
            + f'<p class="small" style="margin-top:12px">Fuente: <a href="{NUBE}">{NUBE}</a> (consultada el {E.FECHA}; resumida con una herramienta de lectura). '
              '<b>No se ha desplegado nada en Cloud Run en este material</b>: en S3 lo comprobamos de verdad.</p>')

    # 15 ------------------------------------------------------------------------------------------- laboratorio de roturas
    primero = {'r1': 2, 'r2': 2, 'r3': 1, 'r4': 1, 'r5': 2}
    filas = [[f'{x["num"]}. {fmt(x["titulo"])}', fmt(x['sintoma']), f'<code>{esc(datos.cmd(x["id"], primero[x["id"]]))}</code>', f'{x["minutos"]} min']
             for x in E.ROTURAS]
    P.libre('Laboratorio: romperlo a propósito', B, f'≈{datos.minutos_total(E.ROTURAS)} min · laboratorio-romper.md', 'Laboratorio: cinco fallos que vas a provocar y arreglar',
            tabla(['Rotura', 'Síntoma', 'Primer comando', 'Tiempo'], filas)
            + '<div class="two mt">'
            + card('Cómo se trabaja', ul([fmt('**Provocas** el fallo y lo **diagnosticas** con Docker.'), fmt('Escribes tu **hipótesis** antes de ver el arreglo.'),
                                          fmt('Abres el **arreglo** y comparas.')], True), 'ok')
            + card('Qué te llevas', '<p class="small" style="font-size:14.5px;color:var(--text)">Un método para cuando un contenedor no hace lo que esperas, y que las cinco roturas '
                   'comparten. Los comandos y sus salidas reales están en <code>laboratorio-romper.md</code>.</p>') + '</div>')

    # 16 ------------------------------------------------------------------------------------------- método de diagnóstico
    P.libre('Método de diagnóstico', B, 'El mismo en las cinco roturas', 'Cuando algo falla: cuatro preguntas, siempre en este orden',
            flujo([('1 · ¿En marcha?', '<code>docker ps -a</code>', ''), ('2 · ¿Qué dijo?', '<code>docker logs x</code>', ''),
                   ('3 · ¿Cómo está?', '<code>docker inspect x</code>', ''), ('4 · ¿Qué hay dentro?', '<code>docker exec x …</code>', '')])
            + '<h3 style="margin-top:16px">Códigos de salida que has visto</h3>'
            + tabla(['Código', 'Significa', 'Dónde'], [
                ['<code>0</code>', 'El proceso terminó bien (a veces, demasiado pronto: rotura 5)', 'Ejemplo 1 · rotura 5'],
                ['<code>2</code>', 'El programa falló (aquí, no encontró <code>aap.py</code>)', 'Rotura 2'],
                ['<code>125</code>', '<code>docker run</code> no pudo arrancar el contenedor (aquí, puerto ocupado)', 'Rotura 1'],
                ['<code>137</code>', '128 + 9: terminado a la fuerza (un <code>stop</code> que no atiende, o falta de memoria)', 'Ejemplo 2 · rotura 4'],
                ['<code>1</code>', 'En <code>docker build</code>: la construcción falló (aquí, un <code>COPY</code> sin archivo)', 'Rotura 3']])
            + '<p class="small" style="margin-top:8px">Cambia <b>una</b> cosa cada vez, repite y comprueba.</p>')

    # 17 ------------------------------------------------------------------------------------------- lista final
    lista_final(P, 'Listo para el laboratorio', B, [
        ('He construido una imagen y he mirado sus capas.', 'Práctica A'),
        ('Sé ordenar un Dockerfile para aprovechar la caché y lo he visto con `CACHED`.', 'Práctica B'),
        ('He usado `.dockerignore` y he visto cambiar el contexto y el tamaño.', 'Práctica C'),
        ('Paso configuración con `-e` y sé por qué un secreto no va en `ENV`.', 'Práctica D'),
        ('He visto una imagen con usuario sin privilegios, `HEALTHCHECK`, registros y límite de memoria.', 'Práctica E'),
        ('Conozco el método de diagnóstico: `ps -a` → `logs` → `inspect` → `exec`.', 'Laboratorio'),
    ], siguiente=('../laboratorio-romper.md', 'Laboratorio «romperlo a propósito»'))
    return P
