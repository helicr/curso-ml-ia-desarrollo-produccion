"""Piezas comunes de las dos presentaciones de contenedores: portada, diapositiva de práctica, lista final, tarjetas de salida real."""
import datos
from datos import E, META
from marco import card, esc, fmt, terminal

PIE_REAL = f'Docker {META["docker"]} · {META["sistema"]} · GitHub Actions · {E.FECHA}'
TAG_REAL = '<span class="tag">Ejecutado con Docker real</span>'
TAG_DOC = '<span class="tag sin">Documentación · sin probar aquí</span>'

NOTA_ESTADO = (f'Comandos y salidas <b>reales</b>: ejecutados con Docker {META["docker"]} sobre {META["sistema"]} (GitHub Actions, {E.FECHA}). '
               '<b>Todavía no se han ejecutado en un Codespace del curso</b>: allí la versión de Docker, las columnas y los tiempos pueden diferir. '
               'Los identificadores largos se acortan con «…».')


def portada(P, kick, titulo, sub, chips, usar_extra=''):
    chips_html = ''.join(f'<span class="chip">{esc(c)}</span>' for c in chips)
    cuerpo = (f'<div class="cover"><div class="kick">{esc(kick)}</div><h1>{esc(titulo)}</h1><p class="sub2">{esc(sub)}</p>'
              f'<div class="chips">{chips_html}</div>'
              '<div class="card" style="max-width:1040px"><h3>Cómo usar estas diapositivas</h3>'
              '<p style="font-size:16.5px">Pulsa <b>⧉</b> junto a cada línea para copiarla y pégala en la terminal de tu Codespace, <b>de una en una</b>, leyendo lo que sale. '
              '<b>← →</b> navegan · <b>O</b> índice · <b>F</b> pantalla completa.' + (' ' + usar_extra if usar_extra else '') + '</p>'
              f'<p class="small" style="margin-top:8px">{NOTA_ESTADO}</p></div></div>')
    P.agregar('Portada', 'Inicio', cuerpo)


def pre_corta(txt, n):
    ls = txt.split('\n')
    if len(ls) <= n:
        return txt
    return ls[0] if n == 1 else '\n'.join(ls[:n - 1] + ['…'])


def mini(ej_id, k, max_lineas=6, etiqueta=None, clase='ok'):
    """Tarjeta con el comando (recortado) y su salida real."""
    x = datos.por_id(ej_id)
    p = datos.pasos_de(x)[k]
    sal = datos.mostrado(p, datos.registro(ej_id, k))
    cmd = etiqueta or p['cmd']
    if len(cmd) > 70:
        cmd = cmd[:67] + '…'
    ancho = int(max(34, min(80, max(max((len(l) for l in sal.split('\n')), default=0), 0.7 * len(cmd)))))   # las salidas y comandos anchos reciben más sitio en la fila
    return (f'<div class="card {clase} mini" style="flex:{ancho}"><div class="k">$ {esc(cmd)}</div>'
            f'<pre class="real g">{esc(pre_corta(sal, max_lineas)) if sal else "(sin salida)"}</pre></div>')


def sal_pre(ej_id, k, max_lineas=8):
    x = datos.por_id(ej_id)
    sal = datos.mostrado(datos.pasos_de(x)[k], datos.registro(ej_id, k))
    return f'<pre class="real g">{esc(pre_corta(sal, max_lineas))}</pre>'


def practica(P, id_, bloque, titulo, ej_id, idxs, intro, ver, piensa, max_lineas=6, carpeta=True):
    """Diapositiva de práctica: terminal a todo lo ancho (comandos del ejemplo, copiables de uno en uno), debajo la salida real y una pregunta."""
    x = datos.por_id(ej_id)
    cmds = ([datos.preparar_carpeta(x)] if carpeta else []) + [datos.cmd(ej_id, k) for k in idxs]
    term = terminal('Terminal del Codespace', cmds)
    salidas = ''.join(mini(ej_id, k, max_lineas) for k in ver)
    pensar = '<div class="card warn mini piensa"><b style="color:var(--gold)">PARA PENSAR</b> · ' + ' · '.join(fmt(t) for t in piensa) + '</div>'
    cabecera = f'<div class="kick"><span>{esc(bloque)} · Práctica · Ejemplo {x["num"]}</span>{TAG_REAL}</div><h1>{esc(titulo)}</h1>'
    cuerpo = (f'<p class="muted" style="font-size:15px;line-height:1.33">{fmt(intro)}</p>'
              f'<div class="wide">{term}</div>'
              '<div class="btns" style="margin-top:2px"><button class="btn hecho-btn">Marcar como hecho</button>'
              f'<span class="k">Selección de comandos; el ejemplo completo está en la guía práctica (ejemplo {x["num"]}).</span></div>'
              f'<div class="row mt" style="margin-top:6px">{salidas}</div>{pensar}')
    P.agregar(titulo, bloque, cuerpo, id_=id_, pie=f'{bloque} · Práctica', cabecera=cabecera, zoom=1.2)


def lista_final(P, titulo, bloque, items, siguiente=None):
    """items: (texto, referencia)."""
    from marco import check
    sig = ''
    if siguiente:
        href, texto = siguiente
        sig = f'<p style="margin-top:12px;font-size:16px">Siguiente: <a href="{href}">{esc(texto)} →</a></p>'
    cabecera = f'<div class="kick">{esc(bloque)}</div><h1>{esc(titulo)}</h1>'
    total = len({d['id'] for d in P.dias if d['id']})  # el texto inicial es el mismo que escribe el JS compartido al cargar
    cuerpo = (f'{check([(fmt(t), esc(r)) for t, r in items], "fin")}'
              f'<p class="small" style="margin-top:10px"><span id="cuenta">0 de {total} pasos marcados como hechos en este navegador</span>. '
              'Las marcas se guardan solo en este navegador.</p>' + sig)
    P.agregar(titulo, bloque, cuerpo, cabecera=cabecera, zoom=1.4)
