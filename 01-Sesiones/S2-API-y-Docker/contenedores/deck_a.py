"""Presentación 1: «Contenedores: el modelo mental» (ejemplos 1, 2, 3 y 7 de la guía práctica)."""
import datos
from datos import E, META
from diapos import (NOTA_ESTADO, PIE_REAL, TAG_DOC, TAG_REAL, lista_final, mini, portada, practica, sal_pre)
from marco import Presentacion, capas, card, esc, flujo, fmt, real, tabla, ul

TITULO = 'Contenedores: el modelo mental'
STORE = 'contenedores-modelo-mental-hecho'
B = 'Contenedores 1 de 2'
SOLO_NUBE = 'https://docs.cloud.google.com/run/docs/container-contract'


def modelo_mental():
    P = Presentacion(TITULO, STORE, 'modelo-mental', 'Las guías en texto (guia-practica.md) tienen el mismo contenido.')
    seg_stop = round(datos.segundos('e2', 3))
    seg_os = datos.segundos('e1', 3)

    # 1 -------------------------------------------------------------------------------------------- portada
    portada(P, 'ML e IA: de desarrollo a producción · Contenedores 1 de 2', TITULO,
            'Qué es una imagen, qué es un contenedor, por qué se para, qué se pierde al borrarlo y cómo se llega hasta él. Con cuatro prácticas en tu Codespace.',
            ['Docker', 'Imagen y contenedor', 'Puertos', 'Volúmenes', 'Antes de S2'])

    # 2 -------------------------------------------------------------------------------------------- el problema
    P.libre('El problema', B, 'Para qué sirve', '«En mi máquina funciona»',
            '<div class="cols" style="grid-template-columns:.9fr 1.1fr;margin-bottom:16px">'
            + card('Lo que cambia de un equipo a otro', ul([
                fmt('La **versión de Python** y de cada librería.'),
                fmt('El **sistema operativo** y los paquetes que trae.'),
                fmt('Las **variables de entorno** y los archivos que haya por ahí.')]))
            + card('La idea', '<p style="font-size:16.5px;line-height:1.4">Empaquetar el programa <b>con todo lo que necesita para ejecutarse</b> y ejecutar ese paquete '
                   'donde haga falta: tu Codespace, la integración continua o la nube.</p>', 'ok')
            + '</div>'
            + flujo([('Tu código', 'la API y el modelo', ''), ('+ Dependencias', 'las versiones exactas', ''), ('+ Sistema base', 'un Linux mínimo con Python', ''),
                     ('Imagen', 'todo empaquetado, de solo lectura', 'warn'), ('Contenedor', 'una ejecución de la imagen', 'ok')])
            + '<p class="small" style="margin-top:12px">La misma imagen que pruebas en tu Codespace es la que despliegas en la nube (Cloud Run, en S3): '
              'el entorno deja de depender de la máquina donde se ejecuta.</p>')

    # 3 -------------------------------------------------------------------------------------------- imagen y contenedor
    P.libre('Imagen y contenedor', B, 'Los dos conceptos', 'Una imagen es la plantilla; un contenedor, una ejecución',
            '<div style="display:flex;align-items:center;gap:18px;margin:6px 0 14px">'
            '<div class="card" style="flex:none;width:330px;border-color:var(--gold)"><h3>Imagen</h3><code>python:3.11-slim</code>'
            '<p class="small" style="margin-top:6px">Plantilla de <b>solo lectura</b>: un Linux mínimo con Python 3.11. Se descarga una vez y se reutiliza.</p></div>'
            '<div style="color:var(--gold);font-size:30px;font-weight:800">→</div>'
            + capas([('rw', 'Contenedor <code>hola</code>', 'una ejecución'), ('rw', 'Contenedor <code>reloj</code>', 'otra ejecución'),
                     ('rw', 'Contenedor <code>web</code>', 'otra más')]).replace('class="stack"', 'class="stack" style="flex:1"')
            + '</div>'
            '<div class="two">'
            + card('Lo que debes retener', ul([fmt('De **una** imagen salen **tantos** contenedores como quieras.'),
                                              fmt('Una imagen **no se ejecuta**: se usa para crear contenedores.'),
                                              fmt('Borrar un contenedor **no borra** la imagen.')]))
            + card('Así se ve la imagen en tu máquina (real)', sal_pre('e1', 1) + f'<p class="rn">`docker image ls python:3.11-slim` · {PIE_REAL}</p>'.replace('`', ''))
            + '</div>')

    # 4 -------------------------------------------------------------------------------------------- otro Linux
    P.libre('Dentro hay otro Linux', B, 'Contenedor no es máquina virtual', 'Dentro del contenedor hay otro Linux',
            '<div class="two">'
            + card('Medido en las pruebas', f'<p style="font-size:15.5px;line-height:1.4">La máquina que ejecutó los ejemplos era <b>{esc(META["sistema"])}</b>. '
                   'Dentro del contenedor:</p>' + sal_pre('e1', 3)
                   + f'<p class="rn">Lo que ves es la imagen, no tu máquina. Crear, ejecutar y borrar ese contenedor tardó {seg_os:.1f} s.</p>', 'ok')
            + card('Qué es y qué no es', tabla(['', 'Máquina virtual', 'Contenedor'], [
                ['Qué trae', 'Un sistema operativo completo, con su propio núcleo', 'Los archivos de la imagen y tu proceso'],
                ['El núcleo (kernel)', 'El suyo', 'El de la máquina anfitriona (compartido)'],
                ['Se parece a…', 'Otro ordenador dentro del tuyo', 'Un proceso aislado con su propio sistema de archivos']]))
            + '</div>'
            f'<p class="small" style="margin-top:12px">Tamaño de la imagen base en el equipo de pruebas: 189 MB en disco y 47,8 MB descargados (columnas <b>DISK USAGE</b> y <b>CONTENT SIZE</b>; '
            'según la versión de Docker las columnas pueden variar).</p>')

    # 5 -------------------------------------------------------------------------------------------- práctica A (ejemplo 1)
    practica(P, 'pa', B, 'Práctica A · Imagen y contenedor', 'e1', [0, 1, 3, 5, 6, 7],
             'Descarga la imagen, mira dentro del contenedor y comprueba que un contenedor parado sigue existiendo hasta que lo borras.',
             [1, 6],
             ['¿Qué pasa con la imagen cuando borras un contenedor?', '¿Por qué `docker ps` (sin `-a`) no mostraría `hola` aunque exista?'], max_lineas=4, carpeta=False)

    # 6 -------------------------------------------------------------------------------------------- vive lo que vive su proceso
    P.libre('Vive lo que vive su proceso', B, 'La regla más importante', 'Un contenedor vive lo que vive su proceso',
            flujo([('docker run', 'crea el contenedor', ''), ('Arranca', 'su proceso principal', ''), ('El proceso termina', 'o lo paran', 'warn'),
                   ('Se para', 'Exited (código)', 'bad')])
            + '<div class="pair mt">'
            + card('Termina bien · <code>Exited (0)</code>', '<p class="small" style="font-size:14.5px">Un <code>python -c "print(…)"</code> imprime y acaba.</p>' + sal_pre('e1', 6), 'ok')
            + card('Falla · <code>Exited (2)</code>', '<p class="small" style="font-size:14.5px">El <code>CMD</code> apunta a <code>aap.py</code> (errata): Python no lo encuentra (rotura 2).</p>'
                   + sal_pre('r2', 2), 'bad')
            + card(f'Lo matan · <code>Exited (137)</code>', f'<p class="small" style="font-size:14.5px">Un bucle infinito no acaba solo; <code>docker stop</code> tardó {seg_stop} s y terminó en 137 = 128 + 9 (señal KILL).</p>'
                   + sal_pre('e2', 4), 'warn')
            + card('No hace nada · <code>Exited (0)</code>', '<p class="small" style="font-size:14.5px"><code>docker run -d python:3.11-slim</code> sin programa: arranca y acaba al instante (rotura 5).</p>'
                   + sal_pre('r5', 2), 'warn')
            + '</div>')

    # 7 -------------------------------------------------------------------------------------------- ciclo de vida
    P.libre('Ciclo de vida', B, 'Los cuatro estados', 'Ciclo de vida: crear, arrancar, parar, borrar',
            flujo([('Created', 'existe, aún no ha arrancado', 'warn'), ('Up', 'en marcha', 'ok'), ('Exited', 'parado, sigue existiendo', 'bad'), ('Borrado', 'ya no existe', '')])
            + tabla(['Quiero…', 'Comando', 'Qué hace'], [
                ['crear y arrancar', '<code>docker run [-d] [--name x] imagen</code>', '<code>-d</code> lo deja en segundo plano'],
                ['parar', '<code>docker stop x</code>', 'pide parar; si no responde, lo mata a los 10 s'],
                ['volver a arrancar', '<code>docker start x</code>', 'conserva su configuración'],
                ['borrar', '<code>docker rm x</code> · <code>docker rm -f x</code>', '<code>-f</code> lo para y lo borra'],
                ['ver estado', '<code>docker ps -a</code>', 'sin <code>-a</code> solo los que están en marcha'],
                ['ver registros', '<code>docker logs [--tail n] x</code>', 'lo que el proceso escribe en pantalla'],
                ['entrar a mirar', '<code>docker exec x comando</code>', 'ejecuta algo dentro del contenedor en marcha']])
            + '<div class="row mt">' + mini('e2', 4, 3) + mini('e2', 6, 3) + '</div>')

    # 8 -------------------------------------------------------------------------------------------- práctica B (ejemplo 2)
    practica(P, 'pb', B, 'Práctica B · Ciclo de vida', 'e2', [0, 1, 3, 4, 5, 7],
             f'Arranca un contenedor que no termina, mira sus registros, párlo (tardará unos {seg_stop} s), comprueba el `Exited (137)` y vuelve a arrancarlo.',
             [1, 4, 6],
             ['¿Qué diferencia hay entre `docker stop` y `docker rm`?', '¿Por qué `docker stop` tardó tanto aquí y una API real suele parar al instante?'], max_lineas=4, carpeta=False)

    # 9 -------------------------------------------------------------------------------------------- lo escrito dentro se pierde
    P.libre('Lo escrito dentro se pierde', B, 'Efímero por diseño', 'Lo que escribes dentro de un contenedor muere con él',
            '<div class="cols" style="grid-template-columns:.85fr 1.15fr">'
            '<div>' + capas([('base', 'Capas de la imagen <code>python:3.11-slim</code>', 'solo lectura'),
                             ('mio', 'Tu código y tus archivos de la imagen', 'solo lectura'),
                             ('rw', '<b>Capa de escritura del contenedor</b>', 'se borra con <code>docker rm</code>')])
            + '<p class="small" style="margin-top:10px">Todo lo que el proceso escribe dentro va a la capa de abajo. Si borras el contenedor, desaparece.</p></div>'
            '<div class="side">' + mini('e2', 8, 3) + mini('e2', 10, 3, clase='bad')
            + card('Dónde guardar lo que debe sobrevivir', ul([fmt('Un **volumen** (siguiente diapositiva).'), fmt('Una **carpeta tuya montada** en el contenedor.'),
                                                                fmt('**Fuera**: una base de datos o un almacén de archivos.')], True))
            + '</div></div>'
            f'<p class="small" style="margin-top:10px">{TAG_DOC} Google documenta que el sistema de archivos de un contenedor en Cloud Run está en memoria y que lo escrito no persiste cuando la instancia se detiene '
            f'(<a href="{SOLO_NUBE}">contrato de contenedores</a>, consultado {E.FECHA}). Se comprobará en S3.</p>')

    # 10 ------------------------------------------------------------------------------------------- volúmenes y montajes
    P.libre('Volúmenes y montajes', B, 'Datos que sobreviven', 'Dos formas de que algo exista fuera del contenedor',
            '<div class="two">'
            + card('Volumen · lo gestiona Docker', '<p class="small" style="font-size:14.5px"><code>-v datos:/datos</code> · sirve para datos que deben sobrevivir (una base de datos, resultados).</p>'
                   + mini('e7', 2, 3, etiqueta='docker run --rm -v datos:/datos python:3.11-slim cat /datos/nota.txt') +
                   '<p class="rn">Otro contenedor, distinto, ve el archivo que escribió el anterior.</p>', 'ok')
            + card('Carpeta tuya montada', '<p class="small" style="font-size:14.5px"><code>-v "$PWD/modelo-demo:/modelos:ro"</code> · sirve para desarrollo y para cambiar datos o modelo sin reconstruir.</p>'
                   + mini('e7', 6, 3, etiqueta='…cat /modelos/modelo.txt (tras editar el archivo en tu máquina)')
                   + mini('e7', 7, 3, clase='bad', etiqueta='…sh -c "echo x > /modelos/otro.txt"  (con :ro)'), 'ok')
            + '</div>'
            + '<p style="font-size:16px;margin-top:12px">El proyecto del curso <b>copia el modelo dentro de la imagen</b> (<code>COPY models/…</code>): la imagen es autosuficiente y reproducible. '
              'Montarlo sería más flexible, pero depende de que la carpeta esté donde toca.</p>')

    # 11 ------------------------------------------------------------------------------------------- práctica C (ejemplo 7)
    practica(P, 'pc', B, 'Práctica C · Volúmenes y montajes', 'e7', [0, 1, 2, 3, 4, 5, 6, 7],
             'Escribe en un volumen desde un contenedor y léelo desde otro; monta una carpeta tuya en solo lectura, cámbiala y comprueba que el contenedor ve el cambio.',
             [2, 6, 7],
             ['¿Qué ventaja y qué riesgo tiene montar el modelo en lugar de copiarlo en la imagen?'], max_lineas=3)

    # 12 ------------------------------------------------------------------------------------------- puertos
    P.libre('Puertos', B, 'Llegar al contenedor desde fuera', 'Sin publicar el puerto, no hay camino hasta el servicio',
            flujo([('Tu máquina', 'curl http://127.0.0.1:8000', ''), ('Sin <code>-p</code>', 'no hay camino', 'bad'), ('Contenedor', 'el servicio escucha en el 8000', '')])
            + '<div style="height:8px"></div>'
            + flujo([('Tu máquina', 'curl http://127.0.0.1:8000', ''), ('<code>-p 8000:8000</code>', 'máquina : contenedor', 'ok'), ('Contenedor', 'el servicio escucha en el 8000', '')])
            + '<div class="row mt">' + mini('e3', 1, 3, clase='bad') + mini('e3', 4, 3) + mini('e3', 5, 3) + '</div>'
            + '<p style="font-size:16px;margin-top:10px">A la izquierda de <code>-p</code>, el puerto de <b>tu máquina</b>; a la derecha, el del <b>contenedor</b>. '
              'Dos contenedores no pueden publicar el mismo puerto de tu máquina (rotura 1).</p>')

    # 13 ------------------------------------------------------------------------------------------- 0.0.0.0
    P.libre('0.0.0.0, no 127.0.0.1', B, 'La pregunta del laboratorio de S2', 'Dentro del contenedor, el servicio escucha en 0.0.0.0',
            '<div class="pair">'
            + card('Escucha en <code>0.0.0.0</code> (todas las interfaces)', '<p class="small" style="font-size:14.5px"><code>python -m http.server 8000</code> con el puerto publicado.</p>'
                   + mini('e3', 4, 2), 'ok')
            + card('Escucha solo en <code>127.0.0.1</code>', '<p class="small" style="font-size:14.5px">El mismo servidor con <code>--bind 127.0.0.1</code> y el puerto publicado igual.</p>'
                   + mini('e3', 8, 2), 'bad')
            + '</div>'
            + '<p style="font-size:16.5px;line-height:1.42;margin-top:12px">El tráfico entra por la red del contenedor, no por su «127.0.0.1»: un servicio que solo escucha en el bucle local '
              '<b>no lo atiende nadie de fuera</b>, aunque el puerto esté publicado. Por eso la API del curso arranca con <code>--host 0.0.0.0</code>.</p>'
            f'<p class="small" style="margin-top:8px">{TAG_DOC} Cloud Run exige lo mismo: el contenedor debe escuchar en <code>0.0.0.0</code> en el puerto al que se envían las peticiones '
            f'(8080 por defecto) y no en <code>127.0.0.1</code> (<a href="{SOLO_NUBE}">contrato de contenedores</a>, {E.FECHA}).</p>')

    # 14 ------------------------------------------------------------------------------------------- práctica D (ejemplo 3)
    practica(P, 'pd', B, 'Práctica D · Puertos', 'e3', [0, 1, 2, 3, 4, 6, 7, 8, 9],
             'Compruébalo tú: primero sin publicar el puerto, luego publicándolo, y por último con el servicio escuchando solo en 127.0.0.1. Espera 2 s tras cada `docker run -d` antes del `curl`.',
             [1, 4, 8],
             ['La respuesta a la pregunta de S2: ¿por qué el contenedor de la API escucha en `0.0.0.0` y no en `127.0.0.1`?'], max_lineas=3, carpeta=False)

    # 15 ------------------------------------------------------------------------------------------- resumen
    P.libre('Resumen', B, 'Para llevarte', 'Seis ideas que ya puedes usar',
            '<div class="three" style="gap:12px">'
            + ''.join(card(f'{n}. {t}', f'<p class="small" style="font-size:14.5px;color:var(--text)">{fmt(c)}</p>') for n, t, c in [
                (1, 'Imagen ≠ contenedor', 'La imagen es la plantilla de solo lectura; el contenedor, una ejecución de ella.'),
                (2, 'Vive lo que vive su proceso', 'Si el proceso termina, el contenedor se para. `docker ps -a` + `docker logs` dicen por qué.'),
                (3, 'Lo escrito dentro se pierde', 'Para que algo sobreviva: volumen, carpeta montada o almacenamiento externo.'),
                (4, 'Hay que publicar el puerto', '`-p máquina:contenedor`. Un puerto de tu máquina, un contenedor.'),
                (5, 'Escucha en 0.0.0.0', 'En `127.0.0.1` nadie de fuera llega, aunque publiques el puerto.'),
                (6, 'Dentro hay otro Linux', 'Lo que ves es la imagen, no tu máquina; el núcleo sí es el del anfitrión.')])
            + '</div>')

    # 16 ------------------------------------------------------------------------------------------- lista final
    lista_final(P, 'Listo para el Dockerfile', B, [
        ('He descargado una imagen y he ejecutado un contenedor con `--rm` y otro sin él.', 'Práctica A'),
        ('Sé leer `docker ps -a` y explicar `Exited (0)` y `Exited (137)`.', 'Práctica B'),
        ('He comprobado que lo escrito dentro de un contenedor desaparece al borrarlo.', 'Ejemplo 2'),
        ('He usado un volumen y una carpeta montada en solo lectura.', 'Práctica C'),
        ('He publicado un puerto con `-p` y sé por qué el servicio debe escuchar en `0.0.0.0`.', 'Práctica D'),
    ], siguiente=('../del-dockerfile-a-produccion/index.html', 'Del Dockerfile a producción'))
    return P
