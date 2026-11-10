"""Escribe la guía práctica (guia-practica.md) y el laboratorio (laboratorio-romper.md) a partir de ejemplos.py y salidas-reales.json."""
import datos
from datos import E, META

TITULO_GUIA = 'Contenedores con Docker: guía práctica en 9 ejemplos'
TITULO_LAB = 'Laboratorio «romperlo a propósito»: 5 fallos de contenedores y cómo diagnosticarlos'
PREVIO = '../../../03-Entorno/guia-codespaces/index.html'
MIN_BASICO = datos.minutos_total(E.EJEMPLOS[:6])
MIN_TOTAL = datos.minutos_total(E.EJEMPLOS)
MIN_LAB = datos.minutos_total(E.ROTURAS)

ESTADO = (f'> **Estado de esta guía.** Los comandos y las salidas son reales: se ejecutaron con Docker {META["docker"]} sobre {META["sistema"]} '
          f'(GitHub Actions, {E.FECHA}). **Todavía no se han ejecutado en un Codespace del curso.** En tu Codespace la versión de Docker puede ser otra: '
          'las columnas de `docker image ls`, los tiempos y los tamaños pueden diferir. Los identificadores largos (`…`) y las marcas de tiempo (`"ts": …`) '
          'se han acortado porque cambian en cada ejecución. Si algo no sale como aquí, copia el mensaje exacto: es lo que hay que comparar.')


def _bloque(codigo, leng=''):
    return [f'```{leng}', codigo, '```']


def _nota_rc(p):
    rc = p['rc']
    if rc == 0:
        return ''
    if rc == 'distinto':
        return '*Este comando falla a propósito: termina con un código distinto de 0.*'
    return f'*Este comando termina con código {rc}, y es lo que se espera.*'


def _paso_md(i, k, p, n):
    reg = datos.registro(i, k)
    m = [f'**{n}.** {p["que"]}', '']
    if p['pausa'] >= 2:
        m += [f'*Espera unos {p["pausa"]} segundos desde el comando anterior.*', '']
    m += _bloque(p['cmd'], 'bash') + ['']
    nota = _nota_rc(p)
    if nota:
        m += [nota, '']
    txt = datos.mostrado(p, reg)
    if txt:
        m += ['Salida:', ''] + _bloque(txt, 'text')
        if p['mostrar'] and p['mostrar'][0] == 'ultimas' and len(reg['salida'].rstrip('\n').split('\n')) > p['mostrar'][1]:
            m += [f'*(Solo se muestran las últimas {p["mostrar"][1]} líneas.)*', '']
    m += ['']
    return m


def _archivos_md(x):
    arch = datos.archivos_de(x)
    if not arch:
        return []
    m = ['**Archivos de la carpeta** (léelos antes de ejecutar nada):', '']
    for nombre, texto, leng in arch:
        m += [f'`{nombre}`', ''] + _bloque(texto, leng) + ['']
    return m


def _lista(items):
    return [f'- {t}' for t in items] + ['']


def guia_md():
    m = [f'# {TITULO_GUIA}', '',
         'Ejemplos sueltos, cada uno con sus comandos, lo que debes ver y lo que has aprendido, para entender qué es un contenedor antes del laboratorio de S2 '
         '(API del curso en Docker). Pensada para hacerla **tú solo en tu Codespace**, a tu ritmo.', '',
         ESTADO, '',
         '## Cómo usar esta guía', '',
         f'- **Dónde:** en la terminal de tu Codespace (si aún no lo tienes abierto, empieza por la [guía de Codespaces]({PREVIO})).',
         f'- **Cuánto:** mínimo recomendado antes de S2, los ejemplos 1 a 6 (≈{MIN_BASICO} min); completa, los 9 (≈{MIN_TOTAL} min). '
         'Son estimaciones, sin cronometrar con alumnado.',
         '- **Cómo:** copia cada comando tal cual, compara con la salida de la guía y lee el «qué ha pasado». Al final de cada ejemplo hay **qué has aprendido** y una pregunta para pensar.',
         '- **Dos presentaciones acompañan esta guía:** [Contenedores: el modelo mental](modelo-mental/index.html) (ejemplos 1, 2, 3 y 7) y '
         '[Del Dockerfile a producción](del-dockerfile-a-produccion/index.html) (ejemplos 4, 5, 6, 8 y 9).',
         f'- **Después:** el [laboratorio «romperlo a propósito»](laboratorio-romper.md) (≈{MIN_LAB} min), para practicar el diagnóstico.', '',
         '## Los nueve ejemplos de un vistazo', '',
         '| Nº | Ejemplo | Min | Carpeta | Qué te llevas |', '|---|---|---|---|---|']
    for x in E.EJEMPLOS:
        carpeta = f'`{x["carpeta"]}`' if x['carpeta'] else '(ninguna)'
        m.append(f'| {x["num"]} | {x["titulo"]} | {x["minutos"]} | {carpeta} | {x["resumen"]} |')
    m += ['', f'Las carpetas están en `{E.CARPETA}/`. Los ejemplos sin carpeta se hacen en una carpeta vacía que crea el primer comando.', '',
          '## Antes de empezar', '',
          'Comprueba que Docker responde (si falla, no sigas: avisa con el mensaje exacto):', '']
    m += _bloque('docker version', 'bash')
    m += ['', 'Debe mostrar dos bloques, **Client** y **Server**. Si solo aparece el cliente y el servidor da error, Docker no está en marcha en tu Codespace.', '']
    for x in E.EJEMPLOS:
        m += [f'## Ejemplo {x["num"]} · {x["titulo"]}', '', f'*{x["minutos"]} min · {x["resumen"]}*', '',
              '**Colócate en la carpeta:**', ''] + _bloque(datos.preparar_carpeta(x), 'bash') + ['']
        m += _archivos_md(x)
        for k, p in enumerate(x['pasos']):
            m += _paso_md(x['id'], k, p, k + 1)
        m += ['**Qué has aprendido**', ''] + _lista(x['aprende'])
        m += ['**Para pensar**', ''] + _lista(x['piensa'])
    m += ['## Chuleta de comandos (formas generales)', '',
          '| Para… | Forma general |', '|---|---|',
          '| Descargar una imagen | `docker pull imagen:etiqueta` |',
          '| Ver imágenes | `docker image ls` |',
          '| Crear y ejecutar un contenedor | `docker run [opciones] imagen [comando]` |',
          '| En segundo plano / con nombre / borrar al salir | `-d` / `--name nombre` / `--rm` |',
          '| Publicar un puerto | `-p puerto-de-tu-máquina:puerto-del-contenedor` |',
          '| Pasar variables | `-e NOMBRE=valor` o `--env-file archivo` |',
          '| Montar volumen o carpeta | `-v nombre:/ruta` o `-v carpeta:/ruta[:ro]` |',
          '| Limitar memoria | `--memory 128m` |',
          '| Ver contenedores (también parados) | `docker ps` (`-a` para todos) |',
          '| Ver los registros | `docker logs [--tail n] nombre` |',
          '| Ejecutar algo dentro | `docker exec nombre comando` |',
          '| Parar / arrancar / borrar | `docker stop` / `docker start` / `docker rm [-f]` |',
          '| Construir una imagen | `docker build [-f Dockerfile.x] -t nombre:etiqueta .` |',
          '| Ver las capas / la configuración | `docker history imagen` / `docker inspect objeto` |',
          '| Consumo de recursos | `docker stats --no-stream` |', '',
          '## Lo que esta guía no cubre (a propósito)', '',
          '- **Docker Compose**, varias imágenes a la vez, redes personalizadas y registros de imágenes: no hacen falta para S2 y se verán, en lo que toque, en S3.',
          '- **Cloud Run y Artifact Registry** (la nube de GCP): se ven en S3. En la presentación «Del Dockerfile a producción» hay una diapositiva con lo que Google documenta '
          'sobre el contenedor en Cloud Run; es lectura de su documentación, **no probada** en este material.', '']
    return '\n'.join(m).rstrip('\n') + '\n'


def laboratorio_md():
    m = [f'# {TITULO_LAB}', '',
         f'Cinco fallos típicos de los contenedores. En cada uno **provocas el fallo, lo diagnosticas con los comandos de Docker y solo después miras el arreglo**. ≈{MIN_LAB} min en total.', '',
         ESTADO, '',
         '## Cómo trabajar', '',
         '1. Haz antes la [guía práctica](guia-practica.md) (ejemplos 1 a 6 como mínimo).',
         '2. En cada rotura: ejecuta los comandos de **Provócalo y diagnostica**, anota en la hoja de registro lo que ves y **escribe tu hipótesis** antes de abrir el arreglo.',
         '3. Despliega **Arreglo** y compara con tu hipótesis. Si no coincide, repite el diagnóstico con calma.', '',
         '## Las cinco roturas', '',
         '| Nº | Rotura | Min | Síntoma |', '|---|---|---|---|']
    for x in E.ROTURAS:
        m.append(f'| {x["num"]} | {x["titulo"]} | {x["minutos"]} | {x["sintoma"]} |')
    m += ['']
    for x in E.ROTURAS:
        m += [f'## Rotura {x["num"]} · {x["titulo"]}', '', f'*{x["minutos"]} min · Síntoma: {x["sintoma"]}*', '',
              '**Colócate en la carpeta:**', ''] + _bloque(datos.preparar_carpeta(x), 'bash') + ['']
        m += _archivos_md(x)
        m += ['### Provócalo y diagnostica', '']
        for k, p in enumerate(x['pasos']):
            m += _paso_md(x['id'], k, p, k + 1)
        m += ['**Antes de seguir:** ¿cuál es tu hipótesis de la causa? Apúntala en la hoja de registro.', '',
              '<details>', '<summary><b>Arreglo y lección</b> (ábrelo después de intentarlo)</summary>', '']
        n0 = len(x['pasos'])
        for j, p in enumerate(x['arreglo']):
            m += _paso_md(x['id'], n0 + j, p, j + 1)
        m += [f'**Lección.** {x["leccion"]}', '', '</details>', '']
    m += ['## Hoja de registro', '', 'Cópiala y rellénala mientras trabajas.', '',
          '| Rotura | Primer comando de diagnóstico | Qué viste | Mi hipótesis | Causa real |', '|---|---|---|---|---|']
    for x in E.ROTURAS:
        m.append(f'| {x["num"]}. {x["titulo"]} |  |  |  |  |')
    m += ['', '## Método de diagnóstico (el mismo en las cinco)', '',
          '1. **¿Está en marcha?** `docker ps -a` → ¿`Up` o `Exited (código)`?',
          '2. **¿Qué dijo?** `docker logs nombre` → el mensaje del proceso.',
          '3. **¿Cómo está configurado?** `docker inspect nombre` → estado, variables, límites.',
          '4. **¿Qué hay dentro?** `docker exec nombre comando` (solo si sigue en marcha).',
          '5. **Cambia una cosa, repite y comprueba.**', '']
    return '\n'.join(m).rstrip('\n') + '\n'
