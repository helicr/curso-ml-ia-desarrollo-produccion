"""Presentación «Tu caso de S1 a S5» (12 diapositivas). Resume `02-Proyecto-Transversal/alumno/tu-caso-bank-marketing.md`.

Usa el marco de las presentaciones de contenedores (`01-Sesiones/S2-API-y-Docker/contenedores/marco.py`), que a su vez
reutiliza el CSS y el JavaScript de la guía de Codespaces: todas las guías del curso se ven y se manejan igual.
Las cifras salen de `hechos.py` (medidas sobre el CSV del repositorio); no hay ninguna cifra de modelo.
"""
import importlib.util

from hechos import H, RAIZ, miles, salida_lectura

_ruta = RAIZ / '01-Sesiones' / 'S2-API-y-Docker' / 'contenedores' / 'marco.py'
_spec = importlib.util.spec_from_file_location('marco_contenedores', _ruta)
marco = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(marco)
Presentacion, card, check, esc, flujo, fmt, real, tabla, terminal, ul = (
    marco.Presentacion, marco.card, marco.check, marco.esc, marco.flujo, marco.fmt, marco.real, marco.tabla, marco.terminal, marco.ul)

TITULO = 'Tu caso de S1 a S5'
STORE = 'caso-propio-hecho'
B = 'Tu caso: Bank Marketing'
NB = ' '


def n(x):
    """Cifra con miles que no se parten al final de línea."""
    return miles(x).replace(' ', NB)


def c(texto):
    return f'<code>{esc(texto)}</code>'


def etiqueta(texto, clase=''):
    return f'<span class="tag {clase}">{esc(texto)}</span>'


def barra(patron):
    """Una fila de casillas: T entrenamiento, V validación, P prueba (ilustración, no son datos)."""
    color = {'T': 'var(--blue)', 'V': 'var(--gold)', 'P': 'var(--ok)'}
    return ('<div style="display:flex;gap:3px;margin:8px 0 4px">'
            + ''.join(f'<span style="flex:1;height:24px;border-radius:5px;background:{color[x]}"></span>' for x in patron) + '</div>')


LEYENDA = ('<p class="k" style="margin-bottom:6px"><span style="color:var(--blue)">■</span> entrenamiento · <span style="color:var(--gold)">■</span> validación · '
           '<span style="color:var(--ok)">■</span> prueba · ilustración, no son datos</p>')


def deck():
    P = Presentacion(TITULO, STORE, 'caso-propio', 'La hoja tu-caso-bank-marketing.md (02-Proyecto-Transversal/alumno) tiene el mismo contenido en texto.',
                     home_href='../../index.html', home_sesion='S1')
    cmd_lectura, salida_lectura_real = salida_lectura()
    u = H['unknown']

    # 1 -------------------------------------------------------------------------------------------- portada
    P.agregar('Portada', 'Inicio',
              '<div class="cover"><div class="kick">ML e IA: de desarrollo a producción · S1 a S5</div><h1>Tu caso: Bank Marketing</h1>'
              '<p class="sub2">Una pregunta, un dato y cuatro avances: de las capas RAW → MASTER → FS → ML hasta un servicio en GCP orquestado con GitHub Actions.</p>'
              '<div class="chips">' + ''.join(f'<span class="chip">{esc(t)}</span>' for t in ['Bank Marketing (UCI)', 'CC BY 4.0', f'{miles(H["filas"])} llamadas', 'De S1 a S5']) + '</div>'
              '<div class="card" style="max-width:1040px"><h3>Cómo usar estas diapositivas</h3>'
              '<p style="font-size:16.5px"><b>← →</b> navegan · <b>O</b> índice · <b>F</b> pantalla completa. La hoja <code>tu-caso-bank-marketing.md</code> tiene lo mismo en texto.</p>'
              '<p class="small" style="margin-top:8px">Las cifras son recuentos del archivo del repositorio, comprobados con código. <b>No hay ningún modelo de referencia</b>: '
              'se evalúa tu razonamiento, no que tu métrica sea alta.</p></div></div>')

    # 2 -------------------------------------------------------------------------------------------- la pregunta
    P.libre('La pregunta', B, 'El caso', 'Antes de llamar a un cliente: ¿contratará el depósito?',
            '<div class="cols" style="grid-template-columns:1.1fr .9fr;margin-bottom:14px">'
            + card('Qué pasó', ul([fmt('Un **banco portugués** llamó por teléfono a sus clientes para venderles un **depósito a plazo**.'),
                                   fmt('Las llamadas van de **mayo de 2008 a noviembre de 2010**.'),
                                   fmt('Cada fila es **una llamada**: no hay identificador de cliente.')]))
            + card('Lo que predices', '<p style="font-size:17px;line-height:1.42">La columna <code>y</code>: <b>sí</b> o <b>no</b>. '
                   'Solo puedes usar lo que se sabe <b>antes</b> de que el cliente conteste.</p>', 'ok')
            + '</div>'
            + '<div class="three">'
            + card('', f'<div class="num">{n(H["filas"])}</div><p class="k" style="margin-top:6px">llamadas (filas)</p>')
            + card('', f'<div class="num">{H["pct_si"].replace(" ", NB)}</div><p class="k" style="margin-top:6px">dijeron que sí ({n(H["si"])} llamadas)</p>')
            + card('', f'<div class="num">{H["n_variables"]} + 1</div><p class="k" style="margin-top:6px">variables, más el objetivo <code>y</code></p>')
            + '</div>'
            '<p class="small" style="margin-top:12px">Fuente: Moro, Rita y Cortez (2014), <i>Bank Marketing</i>, UCI Machine Learning Repository, '
            'licencia CC BY 4.0 (citarla es obligatorio). doi:10.24432/C5K306</p>')

    # 3 -------------------------------------------------------------------------------------------- misma receta, otro dato
    P.libre('Misma receta, otro dato', B, 'Lo que se repite y lo que cambia', 'Misma receta que el docente, otro dato',
            flujo([('RAW', 'el dato tal cual', ''), ('MASTER', 'limpio y ordenado', ''), ('FS', 'variables conocidas antes', ''),
                   ('ML', 'objetivo y partición', ''), ('Entrenamiento', 'modelos y MLflow', 'ok')])
            + '<div style="height:10px"></div>'
            + tabla(['', 'Caso del docente: Online Retail II', 'Tu caso: Bank Marketing'], [
                ['Pregunta', '¿Volverá el cliente a comprar en los 90 días siguientes?', 'Antes de llamar, ¿contratará el depósito?'],
                ['Una fila es', 'un cliente en una fecha de corte', 'una llamada (sin cliente identificable)'],
                ['Tiempo', 'fecha de corte explícita', 'solo mes y día de la semana; el archivo va ordenado por fecha'],
                ['Partición', 'temporal, por fecha de corte', 'aleatoria estratificada en S1 a S4; por orden de filas en S5'],
                ['La trampa', 'usar datos posteriores al corte', f'{c("duration")}: se conoce al terminar la llamada'],
                ['Suciedad', 'duplicados, cancelaciones, códigos que no son productos', f'{c("unknown")}, filas idénticas, {c("pdays")} = 999']]))

    # 4 -------------------------------------------------------------------------------------------- dónde está y cómo leerlo
    P.libre('Dónde está y cómo leerlo', B, 'El dato', 'Dónde está y cómo leerlo',
            terminal('Terminal · desde la raíz del repositorio, con el entorno env-ia-mlops', [cmd_lectura, 'cd 02-Proyecto-Transversal/datos', 'sha256sum -c SHA256SUMS'])
            + '<div class="two mt">'
            + card('Debe salir', real(salida_lectura_real)
                   + '<p class="rn">Salida real del primer comando, medida al preparar S0 (Linux). El tercero debe decir <b>OK</b> en cada línea.</p>', 'ok')
            + card('No hagas esto', ul([fmt('Abrirlo y guardarlo con **Excel**: cambia el archivo.'),
                                         fmt('**Reordenar las filas**: el orden es la única información temporal (y la necesitas en S5).'),
                                         fmt('Editarlo a mano: todo cambio, con código y sobre tu capa RAW.'),
                                         fmt('No leer `bank-additional-names.txt`: es la documentación del autor.')], True), 'bad')
            + '</div>')

    # 5 -------------------------------------------------------------------------------------------- variables en cuatro grupos
    def grupo(titulo, lineas, clase=''):
        return card(titulo, ''.join(f'<p style="font-size:15px;line-height:1.38;margin-bottom:2px">{x}</p>' for x in lineas), clase)

    P.libre('Las variables en cuatro grupos', B, 'Veinte variables y un objetivo', 'Las variables, en cuatro grupos',
            '<div class="two">'
            + grupo('Del cliente · 7', [f'{c("age")} edad · {c("job")} trabajo · {c("marital")} estado civil', f'{c("education")} estudios · {c("default")} crédito en mora',
                                        f'{c("housing")} crédito de vivienda · {c("loan")} préstamo personal'])
            + grupo('Del último contacto · 4', [f'{c("contact")} móvil o fijo · {c("month")} mes · {c("day_of_week")} día de la semana',
                                                f'<span style="text-decoration:line-through">{c("duration")}</span> duración de la llamada: <b>fuera del modelo</b>'], 'bad')
            + grupo('De campañas anteriores y de esta · 4', [f'{c("campaign")} contactos de esta campaña (<b>incluye la llamada actual</b>)',
                                                             f'{c("pdays")} días desde el último contacto anterior (999 es un código)',
                                                             f'{c("previous")} contactos anteriores · {c("poutcome")} resultado de la campaña anterior'])
            + grupo('Contexto económico · 5', [f'{c("emp.var.rate")} empleo · {c("cons.price.idx")} precios · {c("cons.conf.idx")} confianza',
                                               f'{c("euribor3m")} euríbor a 3 meses · {c("nr.employed")} empleados',
                                               '<span class="small">Indicadores del país (Banco de Portugal), no del cliente: trimestrales, mensuales y diarios.</span>'])
            + '</div>'
            f'<div class="card" style="margin-top:12px;border-color:var(--gold)"><p style="font-size:17px"><b>Objetivo:</b> {c("y")} · {c("yes")} si contrató el depósito, {c("no")} si no. '
            f'Hay {n(H["si"])} síes y {n(H["no"])} noes.</p></div>')

    # 6 -------------------------------------------------------------------------------------------- duration
    P.libre('La trampa: duration', B, 'La más importante', '`duration`: solo se conoce cuando la llamada termina',
            flujo([('Antes de llamar', 'sabes todo lo demás: cliente, campañas, contexto', 'ok'), ('Llamas', 'ocurre la conversación', 'warn'),
                   (c('duration'), 'solo existe aquí: cuántos segundos duró', 'bad'), (c('y'), 'sí o no', '')])
            + '<div class="two mt">'
            + card('Por qué queda fuera', ul([fmt('Una llamada larga suele ser una que **acaba bien**: usarla es darle al modelo lo que debe adivinar.'),
                                              fmt(f'El autor lo advierte en `bank-additional-names.txt`: con duración 0 la respuesta es «no» ({H["duration_0"]} filas de este archivo lo cumplen) '
                                                  'y recomienda descartarla en un modelo realista.')]), 'bad')
            + card('Qué haces', ul([fmt('Déjala **fuera de FS y de ML**.'),
                                    fmt('Escribe una **prueba que falle** si `duration` (o cualquier columna que no se conozca antes de llamar) vuelve a entrar.'),
                                    fmt('Si tu AUC te parece demasiado bueno, **sospecha de una fuga** antes de celebrarlo.')]), 'ok')
            + '</div>')

    # 7 -------------------------------------------------------------------------------------------- trampas de MASTER
    P.libre('Las trampas de MASTER', B, 'Lo que encuentras al limpiar', 'Lo que tendrás que decidir al limpiar',
            tabla(['Qué encuentras', 'Cifra en el archivo', 'Tu decisión'], [
                [f'{c("unknown")} en seis columnas', f'{c("job")} {n(u["job"])} · {c("marital")} {n(u["marital"])} · {c("education")} {n(u["education"])} · '
                 f'{c("default")} {n(u["default"])} · {c("housing")} {n(u["housing"])} · {c("loan")} {n(u["loan"])}', '¿Valor perdido, categoría o descartar filas?'],
                ['Filas idénticas', f'{H["pares_identicos"]} pares, iguales en las {H["n_columnas"]} columnas', 'Sin cliente no sabes si es la misma llamada. ¿Se descartan?'],
                [f'{c("pdays")} = 999', f'{n(H["pdays_999"])} filas; en {n(H["previous_pos_y_pdays_999"])} de ellas {c("previous")} &gt; 0', 'Es un código, no días. ¿Cómo lo representas?'],
                [f'{c("poutcome")} y {c("previous")}', f'{c("nonexistent")} ({n(H["poutcome_nonexistent"])}) son justo las filas con {c("previous")} = 0', 'Dicen lo mismo: ¿conservas las dos?'],
                ['Nombres con punto', f'{c("emp.var.rate")}, {c("cons.price.idx")}, {c("cons.conf.idx")}, {c("nr.employed")}', 'Renómbralas con una convención y anótala'],
            ])
            + '<p class="small" style="margin-top:10px">Lo que descartes no desaparece: queda en una tabla de descartes con su motivo, para que <b>raw = master + descartes</b>.</p>')

    # 8 -------------------------------------------------------------------------------------------- qué es FS aquí
    P.libre('FS: lo que se sabe antes de llamar', B, 'La capa FS en este caso', 'FS: lo que se sabe antes de marcar el número',
            '<p class="lead" style="margin-bottom:10px">Sin identificador de cliente no hay historial por cliente: FS es <b>una fila por llamada</b>, con las variables '
            'conocidas antes de llamar, y un <b>catálogo</b> que explica por qué se conocen.</p>'
            + tabla(['Variables', '¿Se conoce antes de llamar?', 'Qué decides'], [
                ['Del cliente (7)', etiqueta('Sí'), f'qué haces con {c("unknown")}'],
                [f'{c("contact")}, {c("month")}, {c("day_of_week")}', etiqueta('Sí'), f'se planifican con la llamada; cómo codificas {c("month")}, que no trae año'],
                [c('campaign'), etiqueta('Depende', 'mixto'), 'cuenta la llamada actual: úsala solo si puedes justificarlo'],
                [f'{c("pdays")}, {c("previous")}, {c("poutcome")}', etiqueta('Sí'), 'vienen de campañas anteriores; el 999'],
                ['Contexto económico (5)', etiqueta('Depende', 'mixto'), '¿estaba publicado el valor el día de la llamada?'],
                [c('duration'), etiqueta('No', 'sin'), 'fuera, con una prueba que lo vigila'],
            ]))

    # 9 -------------------------------------------------------------------------------------------- la partición
    P.libre('La partición', B, 'Cómo se reparten los datos', 'La partición: aleatoria ahora, por orden de filas en S5',
            LEYENDA
            + '<div class="two">'
            + card('S1 a S4 · aleatoria y estratificada', barra('TTVTTPTTTVTTPTTVTTTP')
                   + ul([fmt('La misma **proporción de síes** en entrenamiento, validación y prueba.'), fmt('Semilla fija y **guardada**.'),
                         fmt('Es **optimista**, y lo dejas escrito: probablemente porque las llamadas de una misma época se parecen y quedan repartidas entre entrenamiento y prueba.')], True), 'ok')
            + card('S5 · el mismo modelo, por orden de filas', barra('TTTTTTTTTTTTTTVVVPPP')
                   + ul([fmt('Las **primeras filas** entrenan y las **últimas** prueban: el orden del archivo es el del tiempo.'),
                         fmt('Compara con lo anterior y **explica la diferencia**; empieza mirando la proporción de síes en cada tramo.'),
                         fmt('Por eso no puedes reordenar el archivo.')], True), 'warn')
            + '</div>')

    # 10 ------------------------------------------------------------------------------------------- los avances
    P.libre('Los avances', B, 'Qué se entrega y cuándo', 'Cuatro avances y una entrega final',
            tabla(['Avance', 'Trabajas en', 'Presentas en', 'Entrega, a más tardar', 'Qué lleva'], [
                ['<b>1</b>', 'S1 y trabajo autónomo', 'S2', 'mié 18 nov, 10:00', 'Capas RAW → MASTER → FS → ML, entrenamiento y métricas, <b>como cuadernos</b>'],
                ['<b>2</b>', 'S2 y trabajo autónomo', 'S3', 'vie 20 nov, 10:00', 'El pipeline <b>ya en Python</b>, API, contenedor y pruebas. La Ruta B de la tarea de S2 es este avance'],
                ['<b>3</b>', 'S3 y trabajo autónomo', 'S4', 'mié 25 nov, 10:00', 'Migración a GCP y despliegue: inventario, datos migrados y validados, servicio y registros'],
                ['<b>4</b>', 'S4 y trabajo autónomo', 'S5', 'vie 27 nov, 10:00', 'Pipeline orquestado con GitHub Actions: workflow funcionando, historial y una decisión explicada'],
                ['<b>Final</b>', 'tras S5', 'por definir', 'por definir', 'Repositorio, informe y demostración, con la evaluación por orden de filas de S5'],
            ])
            + '<p class="small" style="margin-top:12px">Sesiones los miércoles y viernes, de 10:00 a 14:00 (hora de Perú). Cada avance se presenta en la <b>sesión siguiente</b> y se entrega antes de que empiece. '
              'Entre S2 y S3 y entre S4 y S5 solo hay dos días. Se entrega con el <b>formulario de Google del curso</b>: el instructor da el enlace en clase. '
              'Las tareas de cada sesión son un ejercicio aparte, salvo la Ruta B de S2.</p>')

    # 11 ------------------------------------------------------------------------------------------- qué lleva cada avance y la rúbrica
    P.libre('Cada avance y su rúbrica', B, 'Cómo se evalúa', 'Qué lleva cada avance y cómo se evalúa',
            '<div class="two">'
            + card('Cada avance presenta', ul([fmt('El **resultado**: qué funciona y qué no.'), fmt('Cómo se **ejecuta**, en orden y con versiones.'),
                                               fmt('Las **pruebas**, y que fallan si se rompe la regla.'), fmt('**Una decisión**, con evidencia.'),
                                               fmt('Las **dificultades** y lo que no pudiste ejecutar.'), fmt('Los **pasos** para que otra persona lo reproduzca.')], True)
                   + '<p class="small" style="margin-top:6px">Se entrega con <code>plantilla-avance.md</code>.</p>')
            + card('Rúbrica · 100 puntos', tabla(['Criterio', 'Peso'], [['Reproducibilidad', '20'], ['Técnica', '40'], ['Análisis y decisión', '40']])
                   + '<p class="small" style="margin-top:8px">Ver <code>rubrica-avance.md</code>. No hay modelo de referencia: una decisión de «no» bien argumentada vale tanto como una de «sí».</p>')
            + '</div>'
            + card('Alertas que limitan la nota', ul([fmt('`duration` (o algo que no se conoce antes de llamar) en el modelo: la **técnica** no supera 15.'),
                                                      fmt('Solo capturas, sin código ni pruebas ejecutables: la **reproducibilidad** no supera 8.'),
                                                      fmt('Sin citar la fuente del dato: la **reproducibilidad** no supera 15.')], True), 'warn', 'margin-top:12px')
            )

    # 12 ------------------------------------------------------------------------------------------- lista final
    items = [
        ('La huella de mi copia del CSV es correcta (`sha256sum -c SHA256SUMS`).', 'Dónde está'),
        (f'El comando de lectura imprime `({H["filas"]}, {H["n_columnas"]})` y el recuento de síes.', 'Dónde está'),
        ('He leído `bank-additional-names.txt` entera.', 'Dónde está'),
        ('Puedo explicar por qué `duration` queda fuera.', 'La trampa'),
        ('Sé qué decisiones son mías: `unknown`, filas idénticas, `pdays`, `campaign` e indicadores.', 'MASTER y FS'),
        ('Sé qué se entrega en cada avance y que no hay un modelo de referencia.', 'Los avances'),
    ]
    P.agregar('Lista final', B,
              f'{check([(fmt(t), esc(r)) for t, r in items], "fin")}'
              '<p class="small" style="margin-top:10px">Las marcas se guardan solo en este navegador.</p>'
              '<p style="margin-top:12px;font-size:16px">Siguiente: la hoja <code>02-Proyecto-Transversal/alumno/tu-caso-bank-marketing.md</code>, con lo mismo en texto y las decisiones una por una.</p>',
              cabecera=f'<div class="kick">{esc(B)}</div><h1>Listo para S1</h1>', zoom=1.4)
    return P
