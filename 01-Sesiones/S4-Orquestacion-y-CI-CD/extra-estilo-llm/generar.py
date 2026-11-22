"""Genera la presentación «Un LLM y el estilo de color» (index.html, junto a este archivo).

Extra de S4, 60 minutos: A) la idea (5), B) paso a paso en local o Codespace, un notebook por diapositiva (25),
C) los resultados de los tres actos (20) y D) orquestarlo en GitHub Actions (10).
El texto de apoyo, ya sin diapositivas, está en README.md y guia-pipeline.md.

Marco: el mismo de laboratorio-mlflow (S3): botón ⧉ para copiar cada orden y «Copiar todo», teclas ← → · O índice · S notas ·
F pantalla completa, reloj de minutos planificados, fondo blanco y nada que se mueva al pasar el ratón. Las capturas se
amplían con un clic; Esc o un clic las cierran.

Imágenes (CAPTURAS): las `p..` son capturas de las celdas de los notebooks ya ejecutados (convertidos a HTML con nbconvert y
fotografiados con un navegador sin ventana); las `x..` son de la pestaña Actions del run real; las demás son las figuras
del propio extra. Si falta alguna al generar, en su lugar sale un recuadro «Captura pendiente».

Cifras: salen de los notebooks ejecutados (configuración de clase: 300 fotos, 60 de test; 20 y 21/11/2026), de README.md,
de guia-pipeline.md (run 44854247545) y de checklist-actions.md. El notebook 03 no se entrega ejecutado: lleva la salida del
estudio técnico del 20/11/2026 escrita en bloques de texto, y así se dice en su diapositiva.

Uso:  python generar.py              escribe index.html
      python generar.py --comprobar  no escribe; sale con 1 si index.html no está al día
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / 'index.html'
IMG = AQUI / 'img'
RUN = '44854247545'
INICIO_SESION = 0           # el extra no tiene hora fija dentro de S4: el reloj cuenta desde 0
DURACION = 60
CLASE = 'Salida real · notebook ejecutado con la configuración de clase (300 fotos) · 20 y 21/11/2026'
ESTUDIO = 'Salida del estudio técnico del 20/11/2026 · el notebook 03 la lleva escrita en su texto'

# Imágenes que puede citar la presentación (nombre → qué enseña).
CAPTURAS = {
    'p00-versiones.webp': 'Notebook 00: versiones instaladas (torch con +cpu, sin errores)',
    'p01-comprobacion.webp': 'Notebook 01: 300 de 300 parejas se reproducen exactamente',
    'p02-metricas.webp': 'Notebook 02: % de JSON válido y error por ajuste frente a «neutro» y «media»',
    'p02-respuestas.webp': 'Notebook 02: solo 5 respuestas distintas en 60 fotos',
    'p03-resultados.webp': 'Notebook 03: resultados en test de B (error 0,310 frente a 0,259)',
    'p03-diagnostico.webp': 'Notebook 03: diagnóstico, aprende el formato y no la tarea',
    'p04-error.webp': 'Notebook 04: error por ajuste de cada versión',
    'p04-tabla.webp': 'Notebook 04: tabla comparativa completa',
    'p04-mlflow.webp': 'Notebook 04: alias «produccion» y «descartado» en MLflow',
    'p05-tabla.webp': 'Notebook 05: métricas de A3 y B3 y gráfico comparativo',
    'p05-ejemplos.webp': 'Notebook 05: ejemplos de frases del objetivo, A3 y B3',
    'p05-alucinaciones.webp': 'Notebook 05: análisis de las alucinaciones de B3',
    '01_antes_despues.png': 'Notebook 01: cuatro fotos originales y editadas con su JSON',
    '03_curva_perdida.png': 'Notebook 03: curva de pérdida de la LoRA (baja y se queda plana)',
    '04_panel_transferencia.png': 'Notebook 04: panel de transferencia de estilo de todas las versiones',
    '05_comparacion.png': 'Notebook 05: reglas, A3 y B3 en las cuatro métricas',
    '05_curva_perdida.png': 'Notebook 05: curva de pérdida de B3 (escala logarítmica)',
    'x01-grafo-actions.webp': 'Pestaña Actions: grafo del run, Success, 14 m 10 s, 13 artefactos',
    'x02-resumen-actions.webp': 'Pestaña Actions: resumen del run con la tabla comparativa',
}

# --- Órdenes (las pruebas comprueban que los archivos que citan existen) -------------------------------------------------
CARPETA = '01-Sesiones/S4-Orquestacion-y-CI-CD/extra-estilo-llm'
YML = '.github/workflows/extra-estilo-llm.yml'
RAW = ('https://raw.githubusercontent.com/helicr/curso-ml-ia-desarrollo-produccion/lab/extra-estilo-llm/'
       '.github/workflows/extra-estilo-llm.yml')


def papermill(nb, params, salida=None):
    salida = salida or nb
    return f'papermill {nb} "$ESTILO_TRABAJO/salidas/{salida}" {params}'


O = {
    'ir': f'cd {CARPETA}',
    'venv': 'python3.11 -m venv ~/venv-estilo',
    'activar': 'source ~/venv-estilo/bin/activate',
    'pip': 'pip install -r requisitos-extra-estilo.txt',
    'vars': 'export ESTILO_TRABAJO="$HOME/trabajo-estilo" HF_HOME="$HOME/hf-estilo"',
    'params': 'export MODELO="HuggingFaceTB/SmolVLM-256M-Instruct" RESOLUCION=224 N_EJEMPLOS=300 EPOCAS=3',
    'salidas': 'mkdir -p "$ESTILO_TRABAJO/salidas"',
    'jupyter': 'jupyter lab',
    'pm00': papermill('00_preparar_entorno.ipynb',
                      '-p MODELO "$MODELO" -p RESOLUCION "$RESOLUCION" -p N_EJEMPLOS "$N_EJEMPLOS" -p EPOCAS "$EPOCAS"'),
    'pm01': papermill('01_datos_fabricados.ipynb', '-p N_EJEMPLOS "$N_EJEMPLOS" -p RESOLUCION "$RESOLUCION"'),
    'pm02': papermill('02_zero_shot.ipynb', '-p MODELO "$MODELO" -p RESOLUCION "$RESOLUCION" -p N_EJEMPLOS "$N_EJEMPLOS"'),
    'pm03': papermill('03_fine_tuning_lora.ipynb',
                      '-p MODELO "$MODELO" -p RESOLUCION "$RESOLUCION" -p N_EJEMPLOS "$N_EJEMPLOS" -p EPOCAS "$EPOCAS"'),
    'pm04': papermill('04_comparar_y_transferir.ipynb',
                      '-p ETAPA completo -p MODELO "$MODELO" -p RESOLUCION "$RESOLUCION" -p N_EJEMPLOS "$N_EJEMPLOS" -p EPOCAS "$EPOCAS"'),
    'pm05': papermill('05_explicar_estilo.ipynb',
                      '-p MODELO "$MODELO" -p N_EJEMPLOS "$N_EJEMPLOS" -p N_FRASES 500 -p EPOCAS 2 -p FORMATO facil'),
    'mlflow': 'mlflow ui --backend-store-uri "sqlite:///$ESTILO_TRABAJO/mlflow.db"',
    # --- GitHub Actions ---
    'base': 'git switch develop',
    'pull': 'git pull',
    'rama': 'git switch -c lab/extra-estilo-llm',
    'cp': f'mkdir -p .github/workflows && cp {CARPETA}/extra-estilo-llm.yml .github/workflows/',
    'curl': f'curl -fsSL -o {YML} {RAW}',
    'status': 'git status',
    'add': f'git add {YML}',
    'commit': 'git commit -m "Extra S4: estilo de color con un LLM en GitHub Actions"',
    'push': 'git push -u origin lab/extra-estilo-llm',
    'git_nombre': 'git config user.name "Tu nombre"',
    'git_correo': 'git config user.email "tu-correo"',
}

# --- Salidas reales (de los notebooks ejecutados) ---------------------------------------------------------------------------
SALIDAS = {
    'n00': ('HuggingFaceTB/SmolVLM-256M-Instruct: licencia «apache-2.0»; 493.9 MB; 0.2 s\n'
            'MobileNetV3-small (ImageNet): 0.2 s\n'
            'Todo listo.\n'
            'Resumen guardado en <trabajo>/entorno.json'),
    'n01': ('300 fotos de 224 px; 150 gatos\n'
            "{'train': 210, 'val': 30, 'test': 60}\n"
            'Ninguna foto repetida entre partes: True\n'
            '300 de 300 parejas se reproducen exactamente aplicando su JSON a la original'),
    'n02': ('Versión A: 60 fotos; 5.61 s por foto de media (mín 3.52, máx 9.97)\n'
            'JSON válido (formato correcto): 55%\n'
            'ajuste          MAE  MAE norm.   neutro  media train\n'
            'MEDIA                    0.433    0.259        0.259\n'
            '5 respuestas distintas en 60 fotos\n'
            '60 respuestas con exposición 0,7 y temperatura -1 (los extremos del prompt)'),
    'n03a': ('trainable params: 1,843,200 || all params: 258,328,128 || trainable%: 0.7135\n'
             'Época 0: pérdida de validación 2.758\n'
             'Época 3: pérdida de entrenamiento (último lote) 0.484, validación 0.475\n'
             'Entrenamiento: 593 s, 159 pasos, 3.73 s por paso de 4 ejemplos\n'
             'Adaptador: 7.06 MB  |  pesos del modelo base (safetensors): 493.9 MB'),
    'n04': ('Versión ganadora (menor ΔE medio con el objetivo): C_color\n'
            'Runs creados en esta ejecución: [\'A_zero_shot\', \'C_mobilenet_ridge\', \'C_color_ridge\', \'D_reinhard\', '
            '\'2c_estadisticas_lora\', \'comparativa\']\n'
            'estilo-color-ridge v1: alias «produccion» (MAE normalizado 0.151)\n'
            'estilo-lora-adaptador v1: alias «descartado»'),
    'n05': ('A3: 208 s para 60 frases\n'
            "B3 {'pct_ajustes_sentido_correcto': 100.0, 'pct_ajustes_sentido_contrario': 0.0, 'pct_frases_con_alucinacion': 18.3, "
            "'pct_frases_espanol_longitud_ok': 100.0, 'pct_frases_perfectas': 81.7, 's_por_frase': 3.74}\n"
            'Entrenamiento: 933 s, 250 pasos, 3.73 s por paso de 4 ejemplos\n'
            'Adaptador: 7.06 MB | memoria pico del proceso: 2887.0 MB'),
    'ej1': ('AJUSTES : {"exposicion": 0.45, "temperatura": 0.5, "tinte": 0.03, "contraste": 1.35, "saturacion": 1.69}\n'
            'OBJETIVO: Para copiar este estilo, se sube bastante la exposición, se sube bastante la temperatura, '
            'se sube bastante el contraste y se sube bastante la saturación.\n'
            'A3      : La referencia es más luminosa, más magenta, con menos contraste y más saturada: se sube bastante la '
            'exposición, se lleva el tinte bastante hacia el magenta, … Ejemplo: Cambios: exposicion: sube bastante; …\n'
            'B3      : La referencia es más luminosa, más cálida, con más contraste y más saturada: se sube bastante la '
            'exposición, se sube bastante la temperatura, se sube bastante el contraste y se sube bastante la saturación.'),
    'ej2': ('Se inventa «exposicion» (intensidad real +0.00):\n'
            'Estilo más oscura, más fría, más magenta, con más contraste y menos saturada. Cambios: se baja un poco la '
            'temperatura, se lleva el tinte un poco hacia el magenta, se sube bastante el contraste y se baja bastante la saturación.'),
}


def esc(t):
    return html.escape(t, quote=True)


def md(t):
    """`código` y **negrita** a HTML (sobre texto ya seguro)."""
    t = esc(t)
    t = re.sub(r'`([^`]+)`', r'<span class="mono">\1</span>', t)
    return re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', t)


def term(titulo, claves):
    """Terminal: una orden por línea con su ⧉. Una clave que empieza por # es un comentario."""
    filas, todo = [], []
    for k in claves:
        if k.startswith('#'):
            filas.append(f'<div class="tln c">{esc(k)}</div>')
            continue
        orden = O[k]
        todo.append(orden)
        filas.append(f'<div class="tln"><span class="ps">$</span><code>{esc(orden)}</code>'
                     f'<button class="cp" data-t="{esc(orden)}" title="Copiar" aria-label="Copiar la orden">⧉</button></div>')
    boton = (f'<button class="cp cpall" data-t="{esc(chr(10).join(todo))}">⧉ Copiar todo</button>' if len(todo) > 1 else '')
    return (f'<div class="term"><div class="bar"><em>{esc(titulo)}</em>{boton}</div>'
            f'<div class="tls">{"".join(filas)}</div></div>')


def real(clave, fuente=CLASE, pq=False):
    return f'<div class="realbox{" pq" if pq else ""}"><div class="rk">{esc(fuente)}</div><pre>{esc(SALIDAS[clave])}</pre></div>'


def cap(nombre, alto=None):
    """Imagen: se amplía con un clic. Si aún no está en img/, recuadro «Captura pendiente»."""
    if nombre not in CAPTURAS:
        raise KeyError(f'imagen no prevista: {nombre}')
    alt = CAPTURAS[nombre]
    estilo = f' style="max-height:{alto}px"' if alto else ''
    if (IMG / nombre).exists():
        return (f'<figure class="cap"><button class="capa" data-src="img/{nombre}" data-alt="{esc(alt)}" title="Clic para ampliar">'
                f'<img src="img/{nombre}" alt="{esc(alt)}"{estilo}></button><figcaption>{esc(alt)}</figcaption></figure>')
    alto_falta = f' style="min-height:{min(alto, 200)}px"' if alto else ''
    return (f'<figure class="cap"><div class="falta" data-falta="{nombre}"{alto_falta}><b>Captura pendiente</b>'
            f'<span class="mono">img/{nombre}</span><small>{esc(alt)}</small></div><figcaption>{esc(alt)}</figcaption></figure>')


def lista(items):
    return '<ul class="list">' + ''.join(f'<li>{md(i)}</li>' for i in items) + '</ul>'


def mira(items):
    return '<div class="card mira"><h3>Qué debes ver</h3>' + lista(items) + '</div>'


def falla(items):
    return '<div class="card falla"><h3>Si falla</h3>' + lista(items) + '</div>'


def hazlo(items, titulo='Haz esto'):
    return f'<div class="card"><h3>{esc(titulo)}</h3>' + lista(items) + '</div>'


def tag(clase, texto):
    return f'<span class="tag {clase}">{esc(texto)}</span>'


def tabla(cab, filas):
    th = ''.join(f'<th>{md(c)}</th>' for c in cab)
    tr = ''.join('<tr>' + ''.join(f'<td>{md(c)}</td>' for c in f) + '</tr>' for f in filas)
    return f'<table class="tbl"><tr>{th}</tr>{tr}</table>'


def barras(filas, maximo):
    """Barras estáticas: (nombre, valor, texto, clase). Clase «mal» = peor que contestar la media."""
    out = []
    for nombre, valor, texto, clase in filas:
        ancho = 0 if valor is None else round(valor / maximo * 100, 1)
        relleno = '' if valor is None else f'<i class="b {clase}" style="width:{ancho}%"></i>'
        out.append(f'<div class="brow"><span class="bn">{md(nombre)}</span><span class="bt">{relleno}</span>'
                   f'<span class="bv">{md(texto)}</span></div>')
    return '<div class="bars">' + ''.join(out) + '</div>'


PARTES = {'A': 'La idea', 'B': 'Paso a paso', 'C': 'Resultados', 'D': 'Actions'}
SLIDES = []


def _marcas_en_parrafos(cuerpo):
    """Los párrafos escritos a mano (<p class="small">) llevan **negrita** y `código` sin pasar por md()."""
    def una(m):
        t = re.sub(r'`([^`]+)`', r'<span class="mono">\1</span>', m.group(2))
        return m.group(1) + re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', t) + '</p>'
    cuerpo = re.sub(r'(<p class="small"[^>]*>)(.*?)</p>', una, cuerpo, flags=re.S)
    return re.sub(r'(<div class="callout"[^>]*>)(.*?)</div>',
                  lambda m: m.group(1) + re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>',
                                                re.sub(r'`([^`]+)`', r'<span class="mono">\1</span>', m.group(2))) + '</div>',
                  cuerpo, flags=re.S)


def slide(parte, minutos, titulo, kick, h1, cuerpo, notas):
    cuerpo = _marcas_en_parrafos(cuerpo)
    SLIDES.append(dict(parte=parte, min=minutos, titulo=titulo, notas=notas,
                       html=f'<p class="kick">{esc(kick)}</p><h1>{md(h1)}</h1>\n{cuerpo}'))


# =====================================================================================================================================
def construir():
    SLIDES.clear()

    # ------------------------------------------------------------------------------------------------ A · La idea (5 min)
    slide('A', 1, 'Portada', 'S4 · Extra · Un LLM y el estilo de color', 'Antes de afinar un LLM, **mide una línea base barata**', f'''
<div class="split" style="grid-template-columns:1.05fr .95fr">
 <div class="col">
  <p class="sub">En 60 minutos sigues, paso a paso, un experimento completo: un LLM de visión pequeño intenta leer el estilo de color de una foto, una regresión que entrena en segundos le gana, y después el mismo LLM sí funciona explicando con palabras. Al final lo orquestas en GitHub Actions.</p>
  <div class="card"><h3>Cómo seguirla</h3>{lista([
        'Cada orden lleva **⧉**: cópiala y pégala en tu terminal. **Copiar todo** copia el bloque entero.',
        'Las salidas y las capturas son **reales**: salen de los notebooks ya ejecutados. Clic en una captura para ampliarla; **Esc** la cierra.',
        'El extra es opcional: no entra en la tarea ni en la rúbrica.',
        'Teclas: **← →** avanzar · **O** índice · **S** notas · **F** pantalla completa.'])}</div>
 </div>
 <div class="card"><h3>El plan de la hora</h3>{tabla(['Parte', 'Min', 'Qué haces'], [
        ['**A · La idea**', '5', 'Los tres actos, glosario y qué se instala'],
        ['**B · Paso a paso**', '25', 'Los notebooks 00 a 05, uno por diapositiva'],
        ['**C · Resultados**', '20', 'Tabla, panel, frases y MLflow'],
        ['**D · Actions**', '10', 'El mismo experimento, orquestado en GitHub']])}</div>
</div>''',
          'Bienvenida. Este extra es opcional y no puntúa: sirve para ver un experimento de ML completo, incluido el fracaso honesto de un modelo grande frente a uno simple. Los notebooks se entregan con sus salidas, así que quien no pueda ejecutar nada puede seguirlo igual leyéndolos. Avise de que la parte B se puede hacer en vivo salvo los notebooks 03 y 05, que tardan unos veinte minutos cada uno.')

    slide('A', 2, 'Los tres actos', 'A · La idea', 'Tres actos, **un mensaje**', f'''
<div class="grid3">
 <div class="card"><h3>Acto 1 · El LLM intenta leer el estilo</h3><p class="small">¿Puede SmolVLM-256M escribir los 5 ajustes como JSON? (notebooks 02 y 03)</p>{lista([
        'Sin entrenar (A): **55 %** de JSON válido.',
        'Con LoRA (B): **100 %** de JSON válido, pero su error (**0,310**) es peor que contestar siempre la media (**0,259**).',
        'Aprende el **formato**, no la tarea.'])}</div>
 <div class="card"><h3>Acto 2 · Una línea base barata</h3><p class="small">¿Y si no usamos un LLM? (notebook 04)</p>{lista([
        'Una regresión (Ridge) sobre **27 estadísticas de color** entrena en segundos.',
        'Error **0,151**: es la mejor de todas.',
        'Se registra en MLflow como `produccion`.'])}</div>
 <div class="card"><h3>Acto 3 · El LLM explica en español</h3><p class="small">¿Y si le damos una tarea de lenguaje? (notebook 05)</p>{lista([
        'Con LoRA, **100 %** de sentido correcto frente a 40,7 % sin entrenar.',
        'Pero fluido no es correcto: **18,3 %** de frases con algún ajuste inventado.'])}</div>
</div>
<div class="callout" style="margin-top:14px"><b>El mensaje.</b> Usa cada herramienta para lo que sirve. Para <b>medir</b> un color, unas estadísticas y una regresión son más baratas y más exactas; el LLM brilla redactando. Y siempre: <b>mide primero la línea base</b> («contestar la media»); si tu modelo no la mejora, no ha aprendido nada de la foto.</div>
<p class="small" style="margin-top:10px;color:var(--muted)">Los datos se <b>fabrican</b>: a una foto se le aplican cinco ajustes de color conocidos (exposición, temperatura, tinte, contraste, saturación) y así la etiqueta sale exacta y gratis. Cifras de la configuración de clase: 300 fotos, 60 de test.</p>''',
          'Cuente la historia de los tres actos sin entrar en el código. En el acto 1 el LLM parece un éxito (JSON perfecto, pérdida que baja) y no lo es: su error es peor que contestar siempre la media. En el acto 2 una regresión barata gana. En el acto 3 el LLM sí funciona porque la tarea es de lenguaje. Cierre con la frase del mensaje: antes de afinar un LLM, mide una línea base barata.')

    slide('A', 1, 'Glosario mínimo', 'A · Glosario', 'Diez palabras para seguir el extra', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="card">{tabla(['Término', 'Qué significa aquí'], [
        ['**LLM / VLM**', 'Modelo de lenguaje grande: escribe texto palabra a palabra. El VLM (de visión) también mira una imagen. SmolVLM-256M: 256 millones de parámetros.'],
        ['**Zero-shot / one-shot**', 'Preguntar sin enseñar ningún ejemplo, o dando uno solo en la pregunta. No se entrena nada.'],
        ['**Fine-tuning y LoRA**', 'Afinar = seguir entrenando con tus datos. LoRA lo hace barato: congela el modelo y entrena matrices pequeñas añadidas.'],
        ['**Adaptador**', 'El archivo con esas matrices (7 MB), aparte del modelo base (494 MB).'],
        ['**JSON**', 'Texto con pares «nombre: valor», p. ej. `{"exposicion": 0.3}`.']])}</div>
 <div class="card">{tabla(['Término', 'Qué significa aquí'], [
        ['**MAE normalizado**', 'Error medio entre ajuste predicho y real, dividido por el ancho de su rango. 0 es perfecto.'],
        ['**Ridge**', 'Regresión lineal con penalización contra coeficientes exagerados; entrena en segundos.'],
        ['**ΔE, SSIM**', 'ΔE: diferencia de color con el resultado ideal (menor es mejor). SSIM: estructura conservada (1 = idéntica).'],
        ['**Alucinación**', 'Que el modelo afirme algo que no está en la entrada: aquí, mencionar un ajuste que no se tocó.'],
        ['**papermill**', 'Ejecuta un notebook desde la terminal cambiándole parámetros y guarda una copia ya ejecutada.']])}</div>
</div>''',
          'No lea el glosario entero: señale solo los términos que el alumno va a necesitar enseguida, que son LoRA, el MAE normalizado y papermill. Cada notebook vuelve a explicar lo suyo, así que nadie debe quedarse atrás por una palabra. El artefacto de GitHub Actions se explica en la parte D.')

    slide('A', 1, 'Qué se instala', 'A · Antes de empezar', 'Qué se instala y **cuánto ocupa**', f'''
<div class="split" style="grid-template-columns:1.05fr .95fr">
 <div class="col">
  <div class="card"><h3>Se instala en un entorno aparte</h3>{tabla(['Paquete', 'Para qué'], [
        ['`torch`, `torchvision` (CPU)', 'Las redes; el LLM de visión funciona sobre `torch`'],
        ['`transformers`, `peft`', 'Cargar SmolVLM; LoRA (notebook 03)'],
        ['`scikit-learn`, `scikit-image`', 'Ridge, color Lab, ΔE y SSIM'],
        ['`mlflow` 3.18', 'Registrar y comparar experimentos'],
        ['`papermill`, `jupyter`', 'Ejecutar los notebooks desde la terminal o en el navegador']])}
  <p class="small" style="margin-top:6px">Todas las versiones están fijadas en `requisitos-extra-estilo.txt`. Instalación medida: **102 s** para transformers, peft, accelerate, scikit-image, nbconvert, ipykernel y psutil sobre un entorno que ya tenía `torch` (la de `torch` no está medida).</p></div>
 </div>
 <div class="col">
  <div class="card"><h3>Descargas (van fuera del repositorio)</h3>{tabla(['Qué', 'Tamaño', 'Cuándo'], [
        ['SmolVLM-256M-Instruct', '493,9 MB', 'notebook 00'],
        ['MobileNetV3-small', '9,8 MB', 'notebook 00'],
        ['Fotos Oxford-IIIT Pet', '791,9 MB', 'notebook 01'],
        ['**Suma**', '**≈ 1,3 GB**', '']])}</div>
  <div class="card"><h3>Memoria y disco</h3>{lista([
        'Memoria pico medida: **1541 MB** en el 02, **2747 MB** en el 03 y **2887 MB** en el 05.',
        'CPU, sin GPU. Se recomiendan **8 GB de RAM** (mínimo previsto, sin verificar) y ~**2 GB** de disco libre.',
        'El adaptador LoRA pesa **7,06 MB**.'])}</div>
 </div>
</div>''',
          'Es la diapositiva de las preguntas prácticas: cuánto se baja y si cabe en el portátil. Las cifras salen del notebook 00 y del estudio técnico. Recuerde que los 8 GB de RAM son un mínimo previsto que no se ha verificado en un equipo de ese tamaño; quien no llegue puede seguir el extra leyendo los notebooks ya ejecutados.')

    # ------------------------------------------------------------------------------------------------ B · Paso a paso (25 min)
    slide('B', 3, 'Preparar el entorno', 'B · Paso 0 · terminal', 'Entorno, **carpeta de trabajo** y parámetros', f'''
<div class="split" style="grid-template-columns:1.1fr .9fr">
 <div class="col">
  {term('Terminal · Codespace, macOS, Linux, WSL o Git Bash', ['# desde la raíz del repositorio', 'ir', 'venv', 'activar', 'pip', 'vars', 'params', 'salidas'])}
  {falla(['`python3.11` no existe: `python --version` debe decir **3.11** (las versiones fijadas son las de Python 3.11).',
          'En PowerShell las variables se definen con `$env:NOMBRE = "valor"`; estas órdenes son de bash.'])}
 </div>
 <div class="col">
  <div class="card"><h3>Qué fija cada variable</h3>{tabla(['Variable', 'Para qué'], [
        ['`ESTILO_TRABAJO`', 'Carpeta de trabajo: fotos, parejas, resultados y `mlflow.db`. **Fuera del repositorio.**'],
        ['`HF_HOME`', 'Caché del modelo. Si no la defines, el código usa `<trabajo>/hf`.'],
        ['`MODELO`, `RESOLUCION`, `N_EJEMPLOS`, `EPOCAS`', 'Valores de clase (300 fotos, 3 épocas) para `papermill -p`, como el bloque `env:` del workflow.']])}</div>
  <div class="card falla"><h3>Ojo con el repositorio</h3>{lista([
        'El 01 y el 05 **reescriben figuras de `img/`**: `git status` las verá modificadas. No las subas: `git restore img/`.',
        'El 01 guarda las fotos ya extraídas: si bajas `N_EJEMPLOS` en otra ejecución, usa otra `ESTILO_TRABAJO`.'])}</div>
 </div>
</div>''',
          'Estas son las mismas variables que fija el workflow en su bloque env: ESTILO_TRABAJO y HF_HOME. Lo importante es que la carpeta de trabajo queda fuera del repositorio, para no ensuciarlo con cientos de megas. Si el alumno no define HF_HOME, el código usa una subcarpeta hf de la carpeta de trabajo. Avise del aviso de git status con las figuras de img/, que el 01 y el 05 reescriben al ejecutarse.')

    slide('B', 2, 'Dos formas de ejecutar', 'B · Paso 0 · cómo ejecutar', 'Jupyter, en vivo; **papermill**, como el workflow', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">
  <div class="card"><h3>Con Jupyter (celda a celda)</h3>{lista([
        'Lanza Jupyter **desde el mismo terminal**, con las variables ya definidas, y abre el `.ipynb` con el kernel «Python 3».',
        'Ejecuta las celdas en orden (**Mayús + Intro**).',
        'Sin tocar nada usa los valores pequeños de la celda `parameters`: **60 fotos y 2 épocas**. Para otros valores, cámbialos ahí o define `ESTILO_N_EJEMPLOS` y `ESTILO_EPOCAS` antes de abrir.'])}</div>
  {term('Terminal', ['ir', 'jupyter'])}
  <div class="card"><h3>Con papermill (lo que hace el workflow)</h3>{lista([
        '`papermill ENTRADA SALIDA -p NOMBRE valor`: pisa los valores de la celda `parameters`.',
        'Deja una copia **ya ejecutada** en `$ESTILO_TRABAJO/salidas/`: si algo falla, ahí ves en qué celda.'])}</div>
 </div>
 <div class="col">
  <div class="card"><h3>Quién necesita a quién (misma carpeta de trabajo)</h3>{tabla(['Notebook', 'Necesita', 'Deja'], [
        ['**00** preparar', 'nada', 'modelo y red en caché, `entorno.json`'],
        ['**01** datos', 'las fotos (se descargan)', '`parejas/` (train, val, test)'],
        ['**02** zero-shot', 'el 01', '`pred_A`, `metricas_A`'],
        ['**03** LoRA', 'el 01', 'adaptador, `pred_B`, `mlflow.db`'],
        ['**04** comparar', 'el 01, el 02 y el 03', 'tabla, panel, alias en MLflow'],
        ['**05** explicar', 'el 01', 'adaptador de la explicación, frases']])}</div>
  <div class="callout">Orden recomendado: <b>00 → 01 → 02 → 03 → 04 → 05</b>. El 05 solo necesita el 01: en el workflow corre a la vez que el 02, el 03 y el 04 (C y D).</div>
  <div class="card"><h3>Qué hacer en vivo y qué leer</h3>{lista([
        '**En vivo:** 00 (13 s), 01 (≈ 15 s), 02 (≈ 5 min).',
        '**Ya ejecutado:** 03 (24 min) y 05 (23 min); el 04 (≈ 40 s) necesita el 03.'])}</div>
 </div>
</div>''',
          'Explique las dos formas. Jupyter es para mirar y tocar; papermill es lo que hace el workflow: ejecuta el notebook entero desde la terminal, pisa los parámetros con -p y guarda la copia ejecutada. La tabla de dependencias evita el error más común, que es ejecutar el 04 sin haber hecho el 03. En clase se hacen en vivo el 00, el 01 y como mucho el 02; el 03 y el 05 se leen ya ejecutados porque tardan unos veinte minutos cada uno.')

    slide('B', 2, 'Notebook 00', 'B · Paso 1 · 00_preparar_entorno', '00 · Comprobar que **tu ordenador está listo**', f'''
<div class="split" style="grid-template-columns:1.05fr .95fr">
 <div class="col">
  {tag('vivo', 'En vivo · 13 s (la descarga del modelo, 51,7 s la primera vez)')}
  <p class="small">No entrena nada: comprueba versiones y licencia, descarga el modelo (493,9 MB) y la red pequeña (9,8 MB) a la caché y mira RAM y disco.</p>
  {term('Terminal · papermill', ['pm00'])}
  {real('n00', pq=True)}
  {falla(['Descarga lenta o parada: define `HTTPS_PROXY` y `HTTP_PROXY` antes de abrir Jupyter.',
          '«no space left»: cambia `ESTILO_TRABAJO` a un disco con más espacio.',
          '`ModuleNotFoundError: estilo`: abre el notebook desde dentro de la carpeta del extra.'])}
 </div>
 <div class="col capcol">{cap('p00-versiones.webp', 300)}
  {mira(['Python **3.11**, `torch` con **+cpu** y la lista de versiones sin errores.',
         'Licencia `apache-2.0` y **«Todo listo.»** al final.',
         'Con el modelo ya en caché la «descarga» tarda 0,2 s: no baja nada.'])}</div>
</div>''',
          'El 00 es la prueba de humo: si algo del entorno está mal, aquí se ve antes de gastar veinte minutos en el 03. La captura enseña las versiones instaladas; deben coincidir con las de requisitos-extra-estilo.txt. En la salida real la descarga tardó 0,2 s porque el modelo ya estaba en caché; la primera vez en el estudio previo fueron 51,7 s, según la red.')

    slide('B', 3, 'Notebook 01', 'B · Paso 2 · 01_datos_fabricados', '01 · **Fabricar** las fotos con ajustes conocidos', f'''
<div class="split" style="grid-template-columns:1.05fr .95fr">
 <div class="col">
  {tag('vivo', 'En vivo · 12–15 s con el tar ya descargado')}
  <p class="small">Aplica a cada foto cinco ajustes al azar, guarda (original, editada, JSON) y reparte por foto en train 70 %, val 10 % y test 20 %. Comprueba que las etiquetas valen.</p>
  {term('Terminal · papermill', ['pm01'])}
  {real('n01', pq=True)}
  {falla(['La descarga de 791,9 MB es lenta: bájala aparte y define `ESTILO_TAR` con la ruta del `images.tar.gz`.',
          'Bajas `N_EJEMPLOS` y salen solo gatos: borra la carpeta `fotos_<resolución>` o usa otra `ESTILO_TRABAJO`.'])}
 </div>
 <div class="col capcol">{cap('p01-comprobacion.webp', 120)}
  {cap('01_antes_despues.png', 250)}
  {mira(['**300 de 300** parejas se reproducen aplicando su JSON a la original.',
         'Con los valores por defecto (60 fotos) verás 60 de 60.'])}</div>
</div>''',
          'Este notebook explica por qué fabricar datos: la etiqueta es exacta y gratis porque la ponemos nosotros. La comprobación clave es la de las parejas: aplicar el JSON guardado a la original reproduce exactamente la editada. La figura de abajo muestra cuatro fotos con sus ajustes: en las que están cerca del neutro casi no se nota el cambio, y eso ya anticipa que no será fácil para un modelo. Ojo: este notebook reescribe dos figuras de img/.')

    slide('B', 4, 'Notebook 02', 'B · Paso 3 · 02_zero_shot', '02 · Versión A: preguntar al LLM **sin entrenarlo**', f'''
<div class="split" style="grid-template-columns:1.05fr .95fr">
 <div class="col">
  {tag('vivo', 'En vivo con paciencia · 320 s (≈ 5 s por foto de test)')}
  <p class="small">Carga SmolVLM-256M, le pide un JSON con los cinco ajustes y mide el % de JSON válido y el error frente a «neutro» y «media». Sin ayuda describe la foto; con el arranque `{{"exposicion":` escribe un JSON.</p>
  {term('Terminal · papermill', ['pm02'])}
  {real('n02', pq=True)}
  {falla(['«Faltan las parejas»: ejecuta antes el 01 sobre la misma `ESTILO_TRABAJO`.',
          'La celda lenta no muestra nada mientras trabaja: es normal (≈ 5 minutos).'])}
 </div>
 <div class="col capcol">{cap('p02-metricas.webp', 200)}
  {cap('p02-respuestas.webp', 120)}
  {mira(['**55 %** de JSON válido y error medio **0,433**, peor que «neutro» y «media» (0,259).',
         '**5 respuestas distintas** en 60 fotos: copia los extremos del prompt (0,7; −1; 0,2…).'])}</div>
</div>''',
          'Es el punto de partida. La tabla enseña que en los cinco ajustes el modelo se equivoca más que contestar siempre lo mismo, y la segunda captura explica por qué: no mira la foto, copia los extremos del rango que le dimos en el prompt. Se puede lanzar en vivo y, mientras tarda unos cinco minutos, dedicar ese tiempo a comentar el glosario o la diapositiva siguiente. La celda lenta no muestra nada mientras trabaja.')

    slide('B', 4, 'Notebook 03', 'B · Paso 4 · 03_fine_tuning_lora', '03 · Versión B: afinar con **LoRA**', f'''
<div class="split" style="grid-template-columns:1.05fr .95fr">
 <div class="col">
  {tag('leer', 'Mejor leerlo ya ejecutado · 1456 s (24 min)')}
  <p class="small">Congela el modelo y entrena solo **1 843 200 parámetros (0,71 %)**: 210 ejemplos, 3 épocas, curva de pérdida, error en test y registro en MLflow. Es el notebook más lento del extra.</p>
  {term('Terminal · papermill', ['pm03'])}
  {real('n03a', fuente=ESTUDIO, pq=True)}
  {falla(['`OSError` al cargar el modelo: ejecuta antes el 00 o revisa la red y el proxy.',
          '`database is locked`: otra ventana de MLflow tiene la base abierta; ciérrala.'])}
 </div>
 <div class="col capcol">{cap('p03-resultados.webp', 250)}
  {cap('03_curva_perdida.png', 150)}
  {mira(['La pérdida cae de **2,758 a 0,479** en la primera época y se queda plana.',
         'Formato correcto **100 %**, pero error **0,310 > 0,259**.',
         'Adaptador: **7,06 MB** frente a 493,9 MB del modelo.'])}</div>
</div>''',
          'Este notebook no se entrega ejecutado: lleva la salida del estudio técnico del 20 de noviembre escrita en bloques de texto, y las capturas son de esos bloques. Ejecutarlo entero lleva 24 minutos: unos 9 de preparar los ejemplos (el codificador de imagen, una sola vez por foto) y unos 10 de entrenamiento. Por eso conviene leerlo ya hecho. La lección: una curva de pérdida bonita y un formato perfecto no prueban que el modelo haya aprendido la tarea.')

    slide('B', 3, 'Notebook 04', 'B · Paso 5 · 04_comparar_y_transferir', '04 · Comparar con una **línea base barata**', f'''
<div class="split" style="grid-template-columns:1.05fr .95fr">
 <div class="col">
  {tag('vivo', 'En vivo si ya hay 02 y 03 · ≈ 40 s')}
  <p class="small">Añade C (MobileNet + Ridge), C_color (27 estadísticas + Ridge) y D (Reinhard), mide el error y la transferencia de estilo, dibuja el panel y registra los modelos en MLflow.</p>
  {term('Terminal · papermill', ['pm04'])}
  {real('n04', pq=True)}
  {falla(['No encuentra `B_lora`: el 03 no se ha ejecutado sobre esta carpeta de trabajo.',
          '`database is locked`: cierra la otra ventana de MLflow.'])}
 </div>
 <div class="col capcol">{cap('p04-tabla.webp', 215)}
  {cap('p04-mlflow.webp', 40)}
  {mira(['Gana **C_color** (menor ΔE medio con el objetivo: **7,500**).',
         'Dos alias en MLflow: `produccion` para `estilo-color-ridge` y `descartado` para el adaptador LoRA.'])}</div>
</div>''',
          'Este es el acto 2. La regresión sobre 27 estadísticas de color tarda unos seis segundos entre entrenar e inferir y gana en todo. Aviso importante: el 04 lee las predicciones del 02 y del 03 y busca en MLflow el run del 03, así que en directo solo se puede lanzar si el 03 se ha ejecutado antes sobre la misma carpeta de trabajo. Si no, se enseña ya ejecutado. Las filas de ΔE se explican en la parte de resultados.')

    slide('B', 4, 'Notebook 05', 'B · Paso 6 · 05_explicar_estilo', '05 · Acto 3: el LLM **explica con palabras**', f'''
<div class="split" style="grid-template-columns:1.05fr .95fr">
 <div class="col">
  {tag('leer', 'Mejor leerlo ya ejecutado · 1397 s (23 min)')}
  <p class="small">Convierte el JSON de ajustes en una frase en español. Los datos de entrenamiento son gratis: **500 JSON fabricados** y sus frases salen de unas reglas, sin fotos. Compara A3 (un ejemplo en el prompt) con B3 (LoRA).</p>
  {term('Terminal · papermill', ['pm05'])}
  {real('n05', pq=True)}
  {falla(['Pocas frases y 1 época es la configuración de CI: las cifras de clase salen con 500 frases y 2 épocas.',
          'El 05 también reescribe figuras de `img/`: `git restore img/` antes de hacer commit.'])}
 </div>
 <div class="col capcol">{cap('p05-tabla.webp', 215)}
  {mira(['B3: **100 %** de sentido correcto y **0 %** en sentido contrario; A3: 40,7 % y 39,5 %.',
         '**81,7 %** de frases perfectas (A3: 0 %).',
         'Pero **18,3 %** de frases con algún ajuste inventado.'])}
  {cap('05_curva_perdida.png', 130)}</div>
</div>''',
          'Este es el acto 3. Aquí el fine-tuning sí funciona porque la tarea es de lenguaje: convertir información estructurada en texto. La entrada es solo un JSON de cinco números, así que no hace falta ninguna foto y los datos salen de unas reglas, que además dan la verdad contra la que medir. Tarda 23 minutos en CPU, por eso se lee ya ejecutado. La pérdida de validación baja de 2,464 a 0,032 en escala logarítmica.')

    # ------------------------------------------------------------------------------------------------ C · Resultados (20 min)
    slide('C', 4, 'Tabla comparativa', 'C · Los tres actos juntos', 'Todas las versiones, **frente a contestar la media**', f'''
<div class="split" style="grid-template-columns:1.15fr .85fr">
 <div class="col">
  <div class="card"><h3>Error al leer los ajustes · MAE normalizado, 0 = perfecto</h3>{barras([
        ('**Media** (contestar siempre la media)', 0.259, '0,259', 'ref'),
        ('**A** · SmolVLM sin entrenar', 0.433, '0,433', 'mal'),
        ('**B** · SmolVLM con LoRA', 0.310, '0,310', 'mal'),
        ('**2c** · estadísticas en el prompt + LoRA', 0.244, '0,244', 'bien'),
        ('**C** · MobileNetV3-small + Ridge', 0.229, '0,229', 'bien'),
        ('**C_color** · 27 estadísticas + Ridge', 0.151, '**0,151**', 'bien'),
        ('**D** · Reinhard (sin aprendizaje)', None, 'no aplica: no predice ajustes', 'bien')], 0.5)}
  <p class="small" style="margin-top:8px"><span class="dot mal"></span> peor que la media · <span class="dot ref"></span> la media · <span class="dot bien"></span> mejor que la media</p></div>
  {mira(['Solo **C_color** gana con claridad: 0,151 frente a 0,259, en segundos y sin LLM.',
         '2c es el único LLM que mejora la media, por **0,015**, con 60 fotos de test y una sola semilla.'])}
 </div>
 <div class="col capcol">{cap('p04-error.webp', 150)}
  <div class="card"><h3>Qué pesa cada versión</h3>{tabla(['Versión', 'Entrenar', 'Tamaño'], [
        ['A', '0 s', '493,9 MB'], ['B', '1123 s', 'adaptador 7,06 MB'], ['C', '7,1 s', '9,71 MB'], ['C_color', '5,9 s', '0,001 MB']])}
  <p class="small" style="margin-top:6px">Fuente: tabla del notebook 04 (tiempo de B = 530 s de preparación + 593 s de entrenamiento).</p></div>
 </div>
</div>''',
          'Pregunta para el grupo antes de revelar: de estas versiones, ¿cuáles son peores que contestar siempre la media? Respuesta: A y B, las dos del LLM sin ayuda. La regresión de MobileNet apenas mejora, y la de las 27 estadísticas de color gana de largo. La tabla de la derecha pone coste al lado del error: C_color entrena en unos seis segundos y pesa casi nada. La fila 2c es una cita del estudio técnico, no se mide en el notebook.')

    slide('C', 3, 'Acto 1 en detalle', 'C · Acto 1', 'B aprende el **formato**, no la tarea', f'''
<div class="split" style="grid-template-columns:.9fr 1.1fr">
 <div class="col">
  {hazlo(['**A** (sin entrenar): 55 % de JSON válido y **5 respuestas distintas** en 60 fotos; las 60 repiten exposición 0,7 y temperatura −1, los extremos del prompt.',
          '**B** (LoRA): 100 % de JSON válido, pero solo **15 respuestas distintas**; dos casi iguales cubren 41 de las 60 fotos.',
          'Sus números **no siguen a los reales**: correlaciones entre −0,04 y 0,19.'], 'Qué se midió')}
  {cap('03_curva_perdida.png', 150)}
  <div class="callout">La pérdida bajó casi seis veces (2,758 → 0,479) y aun así el modelo no hace la tarea. Una curva bonita no demuestra nada; la <b>métrica contra la verdad</b> sí.</div>
 </div>
 <div class="col capcol">{cap('p03-diagnostico.webp', 400)}</div>
</div>''',
          'Esta es la diapositiva de la desconfianza. Tres medidas: cuántas respuestas distintas escribe, cuánto varían sus números frente a los reales, y si los sigue. En contraste la desviación del modelo es 0,013 cuando la real es 0,250. La captura es del bloque de salida del estudio técnico que lleva el notebook 03. Idea para llevarse: la pérdida de entrenamiento y el formato perfecto no prueban nada sin una línea base.')

    slide('C', 4, 'Panel de transferencia', 'C · Acto 2', 'Copiar el estilo de una foto a otra: **el panel**', f'''
<div class="split" style="grid-template-columns:1.25fr .75fr">
 <div class="col capcol">{cap('04_panel_transferencia.png', 440)}</div>
 <div class="col">
  <div class="card"><h3>ΔE medio con el objetivo (menor es mejor)</h3>{tabla(['Versión', 'ΔE'], [
        ['objetivo', '0,000'], ['sin cambio', '14,413'], ['A', '22,206'], ['B', '15,986'], ['C', '13,212'], ['**C_color**', '**7,500**'], ['D (Reinhard)', '14,367']])}</div>
  {mira(['**A y B**: tono casi igual en todas las filas; no siguen a la referencia.',
         '**C_color** se parece al objetivo en las filas 2, 3 y 4 (ΔE 6,8; 4,4; 5,1).',
         'En la fila 1 **todas** quedan en ΔE ≥ 19: un resultado malo también se enseña.'])}
 </div>
</div>''',
          'Cada fila es una pareja: la referencia, el contenido al que se copia el estilo, el objetivo (cómo debería quedar, porque conocemos los ajustes) y las versiones. Debajo de cada salida, su diferencia de color con el objetivo. D copia los colores de la referencia entera y por eso en la fila 1 tiñe de verde amarillento al perrito. Insista en la fila 1: el panel no se retoca, se muestra también lo que sale mal.')

    slide('C', 3, 'Acto 3: A3 frente a B3', 'C · Acto 3', 'Explicar con palabras: **100 % de sentido correcto**', f'''
<div class="split" style="grid-template-columns:1.1fr .9fr">
 <div class="col">
  <div class="card"><h3>60 JSON de test que ningún modelo ha visto</h3>{tabla(['Métrica', 'Reglas (techo)', 'A3 · un ejemplo', 'B3 · LoRA'], [
        ['Ajustes en el sentido correcto', '100 %', '40,7 %', '**100 %**'],
        ['Ajustes en sentido contrario', '0 %', '39,5 %', '**0 %**'],
        ['Frases con alucinación', '0 %', '58,3 %', '18,3 %'],
        ['En español y longitud razonable', '100 %', '0 %', '**100 %**'],
        ['Frases perfectas', '100 %', '0 %', '**81,7 %**'],
        ['Segundos por frase', '–', '3,46', '3,74']])}</div>
  {mira(['B3 se entrenó con **500 frases** fabricadas, 2 épocas y 933 s; la pérdida de validación bajó de 2,464 a 0,032.',
         'Aquí el fine-tuning **sí** funciona: la tarea es de lenguaje.'])}
 </div>
 <div class="col capcol">{cap('05_comparacion.png', 190)}
  <div class="card falla"><h3>Fluido no es correcto</h3>{lista([
        'El 18,3 % de las frases de B3 mencionan un ajuste que no se tocó.',
        'Esa cifra varió entre ejecuciones: **10,0 %, 15,0 % y 18,3 %**. No te fíes de una sola corrida.'])}</div>
 </div>
</div>''',
          'Compare las dos columnas de LLM. Sin entrenar, con un ejemplo en el prompt, el modelo imita en vez de entender: escribe la frase del ejemplo para cualquier JSON y sigue escribiendo el prompt, por eso el 0 % en español y longitud. Con LoRA y quinientas frases acierta el sentido de todo. El fallo que queda es la alucinación, y la advertencia final es de método: mida siempre contra una verdad y no se fíe de una sola ejecución.')

    slide('C', 3, 'Ejemplos de frases', 'C · Acto 3 · respuestas reales', 'Lo que escribe cada modelo, **tal cual**', f'''
<div class="split" style="grid-template-columns:1.1fr .9fr">
 <div class="col">
  {real('ej1', pq=True)}
  {real('ej2', fuente='Una alucinación de B3 · notebook 05, análisis del apartado 5', pq=True)}
  {cap('p05-alucinaciones.webp', 190)}
 </div>
 <div class="col capcol">{cap('p05-ejemplos.webp', 300)}
  {mira(['**A3** escribe la misma frase en los seis ejemplos y luego el eco «Ejemplo: Cambios: …»: no mira el JSON.',
         '**B3** acierta el sentido de los seis; cinco son perfectas.',
         'La alucinación suena natural: «Estilo más oscura…» con exposición casi nula (+0,00).'])}</div>
</div>''',
          'Lea en voz alta el primer ejemplo. A3 escribe la frase de su propio ejemplo del prompt y después repite el prompt; B3 redacta la frase correcta. El segundo recuadro es el caso que enseña por qué fluido no es correcto: la exposición no se tocó, intensidad real 0,00, y aun así la frase empieza por «más oscura». Fíjese también en que la concordancia incorrecta de «Estilo más oscura» viene de nuestra propia plantilla de reglas: B3 copia incluso los defectos de lo que le enseñamos.')

    slide('C', 3, 'MLflow: produccion y descartado', 'C · Registro de modelos', 'El ganador y el **candidato descartado**', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">
  {term('Terminal · tras ejecutar el 03 y el 04', ['mlflow'])}
  {real('n04', pq=True)}
  {falla(['`database is locked`: otra ventana de MLflow tiene la base abierta; ciérrala.'])}
 </div>
 <div class="col capcol">{cap('p04-mlflow.webp', 50)}
  <div class="card"><h3>Qué verás en la interfaz</h3>{lista([
        '**Experiments**: los runs `A_zero_shot`, `B_lora`, `C_mobilenet_ridge`, `C_color_ridge`, `D_reinhard`, `2c_estadisticas_lora` y `comparativa`.',
        '**Models**: `estilo-color-ridge` con el alias **`produccion`** y `estilo-lora-adaptador` con el alias **`descartado`** y el motivo en una etiqueta.'])}</div>
  <div class="callout">Una aplicación cargaría <span class="mono">models:/estilo-color-ridge@produccion</span>: cambiar de modelo es <b>mover el alias</b>, no tocar la aplicación.</div>
 </div>
</div>''',
          'El resultado de un experimento no queda en una tabla suelta: queda registrado. C_color se guarda como modelo del registro con el alias produccion; el adaptador LoRA de B se guarda como candidato descartado, con una etiqueta que dice por qué. Un resultado negativo bien medido también es un resultado. Enlace con S3: el alias es lo que en el laboratorio de MLflow se anticipó para este bloque. El 05 deja además sus dos runs, A3 y B3, en la misma base.')

    # ------------------------------------------------------------------------------------------------ D · Actions (10 min)
    slide('D', 1, 'El pipeline', 'D · Actions · la idea', 'Cada notebook es un **job**', f'''
<div class="card" style="padding:10px 14px"><pre class="code light">0 · Pruebas ─► 1 · Preparar (00) ─► 2 · Datos (01) ─┬─► 3a · Zero-shot, A (02) ───────────┐
                                                    ├─► 3b · LoRA, B (03) ────────────────┼─► 4 · Comparar (04) ─┐
                                                    ├─► 3c · Base C y Reinhard D (04) ────┘                      ├─► 5 · Resumen
                                                    └─► 3d · Acto 3, explicar (05) ───────────────────────────────┘</pre></div>
<div class="split" style="grid-template-columns:.8fr 1.2fr;margin-top:10px">
 <div class="col">
  <div class="callout">Los cuatro jobs 3a, 3b, 3c y 3d tienen el mismo `needs: datos`: <b>corren a la vez</b>. Los dos últimos esperan: `comparar` a 3a, 3b y 3c; `resumen` a `comparar` y a `explicar`.</div>
 </div>
 <div class="col">
  <div class="card"><h3>Cuatro ideas</h3>{lista([
        '**Job**: un trabajo del workflow, en una máquina nueva (`ubuntu-latest`, sin GPU). `needs:` dice de qué otro depende.',
        '**papermill**: ejecuta el notebook e inyecta parámetros; la copia ejecutada se sube siempre (`if: always()`).',
        '**Artefactos**: lo que un job produce lo sube y el siguiente lo baja. **Caché**: el modelo y las fotos no se bajan en cada job.',
        '**Parámetros pequeños** (60 fotos, 2 épocas): comprueban que el pipeline funciona; las conclusiones se sacan con la configuración de clase.'])}</div>
 </div>
</div>''',
          'Recuerde el grafo con la pizarra o con este esquema. Pregunta: ¿qué notebooks pueden correr a la vez? Los que solo necesitan los datos: el 02, el 03, el 04 en su etapa C y D, y el 05. El workflow no copia los notebooks a scripts: ejecuta los mismos que se han leído. Y un aviso desde ya: los parámetros del CI son pequeños a propósito, de modo que las cifras del run no se comparan con las de clase.')

    slide('D', 1, 'Crear la rama lab/', 'D · Actions · paso 1 de 4', 'Una rama que **empiece por `lab/`**', f'''
<div class="split" style="grid-template-columns:1.05fr .95fr">
 <div class="col">
  {term('Terminal · Codespace', ['base', 'pull', 'rama'])}
  {hazlo(['Antes, entra en la pestaña **Actions** de tu fork: en los forks puede venir desactivado. Si ves un aviso que pide activar los workflows, acéptalo.',
          'Tu fork debe tener la carpeta del extra en la rama de la que partes.'], 'Antes de empezar')}
 </div>
 <div class="col">
  {hazlo(['En tu fork, en el selector de ramas elige `develop`, escribe `lab/extra-estilo-llm` y crea la rama a partir de `develop`.'], 'Sin terminal (solo la web de GitHub)')}
  <div class="callout">El nombre <b>debe empezar por <span class="mono">lab/</span></b>: es lo que escucha el disparador del workflow (<span class="mono">push</span> a <span class="mono">lab/**</span>). Con otro nombre, no se lanza nada.</div>
 </div>
</div>''',
          'El disparador del workflow es un push a una rama lab barra barra. Si el alumno crea la rama con otro nombre, no pasa nada y es la causa más típica de que no aparezca ningún run. Avise también de que el fork puede traer Actions desactivado: el texto exacto del botón de activación no se ha verificado, así que diga solo que hay que aceptar el aviso de la pestaña Actions.')

    slide('D', 1, 'Copiar el workflow', 'D · Actions · paso 2 de 4', 'Copiar el YAML a **.github/workflows/**', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">
  {hazlo(['En el repositorio, abre `extra-estilo-llm.yml` y pulsa **Raw**; selecciona todo y copia.',
          'Ya en tu rama `lab/extra-estilo-llm`: **Add file → Create new file**.',
          'Nombre, exactamente: `.github/workflows/extra-estilo-llm.yml` (al teclear las `/` GitHub crea las carpetas).',
          'Pega el contenido y **Commit changes…** directamente en la rama `lab/extra-estilo-llm`, no en `develop`.'], 'Ruta A · en la web de GitHub')}
  <div class="callout">No teclees el YAML a mano: la <b>sangría se rompe</b>. Cópialo con <b>Raw</b>.</div>
 </div>
 <div class="col">
  {term('Ruta B · terminal, desde la raíz del repositorio', ['cp'])}
  {falla(['`cp` dice que no existe: tu `develop` aún no tiene el extra. Descárgalo de la rama del profesor:'])}
  {term('Plan B · descargar el YAML', ['curl'])}
  <p class="small">La ruta del archivo es exacta: con el punto inicial, en la **raíz** y no dentro de la carpeta del extra.</p>
 </div>
</div>''',
          'La ruta del archivo es lo que más falla: tiene que ser punto github barra workflows barra extra-estilo-llm.yml, en la raíz del repositorio y no dentro de la carpeta del extra. Hay dos rutas equivalentes. Desde la web: botón Raw, copiar, Add file, Create new file, pegar y commit en la rama lab. Desde la terminal: la orden con mkdir y cp. Si el develop del alumno todavía no tiene el extra, el plan B es bajar el YAML de la rama del profesor con curl.')

    slide('D', 1, 'Commit y push', 'D · Actions · paso 3 de 4', 'Commit y **push**: ahí arranca el run', f'''
<div class="split" style="grid-template-columns:1.1fr .9fr">
 <div class="col">
  {term('Terminal · en la rama lab/extra-estilo-llm', ['status', 'add', 'commit', 'push'])}
  {mira(['`git status` muestra solo `.github/workflows/extra-estilo-llm.yml` como archivo nuevo.',
         'Tras el `push`, el run aparece en la pestaña **Actions** (si activaste Actions en el fork **después** del push, haz otro push).'])}
 </div>
 <div class="col">
  {falla(['git pide nombre y correo: configúralos una vez y repite el commit.'])}
  {term('Solo la primera vez', ['git_nombre', 'git_correo'])}
  <div class="callout">Un run por cada <span class="mono">push</span> a <span class="mono">lab/**</span>. También se puede lanzar a mano con <b>Run workflow</b>, pero el botón solo aparece si el archivo está en la rama principal del fork.</div>
 </div>
</div>''',
          'Orden de los cuatro pasos: git status para ver el archivo nuevo, git add de la ruta exacta, commit y push con la opción -u. A partir de ese push arranca el workflow. Si Actions estaba desactivado en el fork y se activa después, hay que hacer otro push para que se lance. El lanzamiento manual existe, pero el botón Run workflow solo aparece cuando el archivo está en la rama principal.')

    slide('D', 2, 'Grafo y resumen', 'D · Actions · paso 4 de 4', 'Ver el **grafo** y el **resumen** del run', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col capcol">{cap('x01-grafo-actions.webp', 330)}</div>
 <div class="col capcol">{cap('x02-resumen-actions.webp', 330)}</div>
</div>
<div class="split" style="grid-template-columns:1fr 1fr;margin-top:10px">
 {hazlo(['Pestaña **Actions** → **Extra S4 · estilo de color con un LLM** → el run de tu commit → **Summary**.',
         '9 cajas: las dos primeras en cadena, cuatro a la vez, y al final las dos últimas.',
         'Clic en **3b · Fine-tuning LoRA** y despliega el paso **Ejecutar 03_fine_tuning_lora.ipynb**: verás la barra de papermill celda a celda.'], 'Haz esto')}
 {mira([f'Run real {RUN}, rama `lab/extra-estilo-llm`: **Success, 14 min 10 s, 13 artefactos**.',
        'El **cuello de botella** es el 3b (LoRA), el job más largo.',
        'El resumen lo escribe el job **5 · Resumen** con las dos tablas (actos 1-2 y acto 3).'])}
</div>''',
          f'Capturas del run real {RUN}, rama lab barra extra-estilo-llm, del 21 de noviembre. Pregunta: ¿qué job tarda más? El 3b, el fine-tuning con LoRA. Y, sobre la tabla del resumen: ¿qué conclusión sacáis del LLM? Ninguna: son 60 fotos, 13 de test y 2 épocas, y solo prueban que el pipeline funciona. Las conclusiones se sacan con los notebooks de clase.')

    slide('D', 2, 'Tiempos y artefactos', 'D · Actions · tiempos reales', f'El run {RUN}: **14 min 10 s**', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">
  <div class="card"><h3>Tiempo real de cada job (21/11/2026)</h3>{tabla(['Job', 'Duración', 'Notebook'], [
        ['0 · Pruebas (sin modelos)', '31 s', 'pytest'],
        ['1 · Preparar entorno', '2 min 1 s', '00'],
        ['2 · Datos fabricados', '2 min 45 s', '01'],
        ['3a · Zero-shot, A', '3 min 32 s', '02'],
        ['**3b · Fine-tuning LoRA, B**', '**5 min 52 s**', '03'],
        ['3c · Base C y Reinhard D', '1 min 49 s', '04 · `c_d`'],
        ['3d · Acto 3, explicar', '5 min 23 s', '05'],
        ['4 · Comparar y transferir', '2 min 41 s', '04 · `completo`'],
        ['5 · Resumen', '6 s', '–'],
        ['**Run completo**', '**14 min 10 s**', '3a, 3b, 3c y 3d en paralelo']])}</div>
 </div>
 <div class="col">
  {hazlo(['Entra en el **Summary** del run y baja a la sección de artefactos (13).',
          'Descarga **`comparacion`** (tabla CSV/JSON y panel PNG) y **`nb-04-comparar`** (el notebook 04 ejecutado).',
          'Los artefactos caducan a los **3 días** (`retention-days: 3`).'], 'Descargar artefactos')}
  <div class="card"><h3>Los 13 artefactos</h3><p class="small">`nb-00-preparar`, `nb-01-datos`, `datos`, `nb-02-zero-shot`, `metricas-a`, `nb-03-lora`, `adaptador-lora`, `nb-04-c-d`, `metricas-c-d`, `nb-05`, `explicacion`, `nb-04-comparar` y `comparacion`. Los `nb-*` son cada notebook ya ejecutado.</p></div>
  <div class="callout">Tus tiempos serán <b>parecidos, no iguales</b>: dependen de la máquina y de si las cachés están calientes (el primer run descarga el modelo y las fotos).</div>
 </div>
</div>''',
          'La tabla es la del run real. Si se suman los jobs en serie salen más de 20 minutos; el run entero fue de 14 minutos y 10 segundos porque 3a, 3b, 3c y 3d corren a la vez. Aprovechar para insistir en la diferencia entre el tiempo de clase del 03, 24 minutos con 300 fotos, y el del CI, menos de 6 minutos con 60 fotos y 2 épocas. Los artefactos de notebook se suben aunque falle el job, y eso permite abrir el notebook y ver en qué celda se rompió.')

    slide('D', 1, 'Si no aparece en Actions', 'D · Actions · antes de clase', 'Antes de clase y **si no aparece en Actions**', f'''
<div class="split" style="grid-template-columns:1fr 1fr">
 <div class="col">
  <div class="card falla"><h3>No aparece ningún run: comprueba por orden</h3>{lista([
        '¿Está el archivo en **`.github/workflows/extra-estilo-llm.yml`** (ruta exacta, con el punto inicial y en la raíz)?',
        '¿El nombre de la rama **empieza por `lab/`**, como pide el disparador `lab/**`?',
        '¿**Actions está activado** en el fork?',
        '¿El YAML es válido? GitHub muestra el error de sintaxis. Si se pegó mal, copia de nuevo con **Raw**, sin retocar.'])}</div>
  {hazlo(['Activaste Actions **después** del push: haz un push nuevo.',
          '«Run workflow» no aparece: el archivo no está en la rama principal; usa el disparador por rama `lab/**`.'], 'Dos casos más')}
 </div>
 <div class="col">
  <div class="card"><h3>La víspera (profesor)</h3>{lista([
        'El workflow está en su ruta exacta y hay un **run de prueba en verde** con su enlace guardado como respaldo.',
        'La pestaña Actions muestra el workflow y el run verde de respaldo está abierto en otra pestaña.'])}</div>
  <div class="card"><h3>Si falla un job</h3>{lista([
        'Lee el **primer paso en rojo**: ahí está el error.',
        'Los jobs siguientes salen **skipped**: no tienen nada que leer.',
        'Descarga el artefacto `nb-…` de ese job para ver en qué celda se rompió.',
        'Avisos que **no** son fallo: «Node.js 20 is deprecated» y los de Hugging Face sobre peticiones sin autenticar.'])}</div>
 </div>
</div>''',
          'Esta es la diapositiva de la víspera de clase y del diagnóstico: cuatro comprobaciones por orden. Las tres primeras explican casi todos los casos en los que no aparece ningún run: la ruta del archivo, el nombre de la rama frente al disparador y Actions activado en el fork. El respaldo es siempre el run verde del profesor. Estas comprobaciones salen de lo que falló en la sesión del 20 de noviembre y del run real del 21.')

    slide('D', 1, 'Autoevaluación', 'Cierre', 'Cuatro preguntas para llevarte', '''
<div class="grid2">
''' + ''.join(f'<div class="card"><h3>{i}. {md(p)}</h3><details><summary>Ver la respuesta</summary><p class="small">{md(r)}</p></details></div>' for i, (p, r) in enumerate([
        ('¿Por qué B, con 100 % de JSON válido, es peor que contestar siempre la media?',
         'Porque escribir el **formato** y acertar el **contenido** son cosas distintas: B repite casi la misma respuesta para fotos muy distintas (error 0,310 frente a 0,259). Por eso se mide primero la línea base.'),
        ('¿Por qué los jobs 3a, 3b, 3c y 3d corren a la vez?',
         'Porque los cuatro tienen `needs: datos` y nada más.'),
        ('¿Qué artefacto abrirías para ver en qué celda falló el 03?',
         '`nb-03-lora`: el notebook ejecutado se sube siempre, con `if: always()`.'),
        ('¿Por qué la tabla del run de Actions no sirve para decidir si el LLM es mejor que la línea base?',
         'Con 13 fotos de test y 2 épocas solo prueba que el pipeline funciona; las conclusiones salen de los notebooks con 300 fotos.')], 1)) + '</div>',
          'Lea cada pregunta y deje unos segundos antes de desplegar la respuesta. La primera resume el acto 1; las otras tres, la parte de GitHub Actions. Para quien quiera repetirlo solo: README.md recoge los tres actos, los resultados y el glosario, y guia-pipeline.md el recorrido de Actions paso a paso.')


# =====================================================================================================================================
CSS = r"""
:root{--bg:#ffffff;--text:#1d2733;--muted:#5b6673;--line:#d6dde6;--panel:#f6f8fb;--blue:#1f5fa8;--gold:#9a6a00;
  --ok:#1d7a4f;--bad:#b4323c;--code:#0f1b2a;--codetx:#e6eef8;
  --mono:ui-monospace,"Cascadia Code","SFMono-Regular",Consolas,Menlo,monospace;
  --sans:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:var(--sans);overflow:hidden}
button{font:inherit;color:inherit;cursor:pointer;background:none;border:0}
a{color:var(--blue)}
.mono,code,pre{font-family:var(--mono);font-variant-ligatures:none;font-feature-settings:"calt" 0,"liga" 0}
:focus-visible{outline:3px solid var(--blue);outline-offset:2px}
#viewport{position:fixed;left:0;right:0;top:0;bottom:46px;overflow:hidden;background:var(--bg)}
#stage{position:absolute;left:50%;top:50%;width:1280px;height:720px;transform:translate(-50%,-50%) scale(var(--s,1));transform-origin:center}
.slide{position:absolute;inset:0;padding:34px 60px 46px;display:none;background:var(--bg);overflow:hidden}
.slide.active{display:block}
.slide::before{content:"";position:absolute;left:0;right:0;top:0;height:4px;background:var(--blue)}
.kick{font-size:13.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--blue);font-weight:700;margin-bottom:4px}
h1{font-size:31px;line-height:1.15;margin-bottom:12px;font-weight:750}
h1 .mono{font-size:27px}
h3{font-size:18px;margin-bottom:5px;color:var(--text)}
p{font-size:17.5px;line-height:1.42}
.sub{font-size:20px;line-height:1.4;color:var(--muted)}
.small{font-size:16px;line-height:1.38}
.foot{position:absolute;left:60px;right:60px;bottom:14px;display:flex;justify-content:space-between;font-size:12px;letter-spacing:.06em;color:var(--muted);text-transform:uppercase}
.foot b{color:var(--blue)}
.split{display:grid;gap:16px}
.col{display:flex;flex-direction:column;gap:9px;min-width:0}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:10px 14px}
.card p{font-size:16.5px}
.callout{border-left:4px solid var(--blue);background:#eef4fb;padding:8px 12px;border-radius:8px;font-size:17px;line-height:1.4}
.mira{border-color:#9fd1b7;background:#f1faf5}.mira h3{color:var(--ok)}
.falla{border-color:#ebb7bb;background:#fdf3f4}.falla h3{color:var(--bad)}
.list{list-style:none}.list li{position:relative;padding-left:15px;font-size:16.5px;line-height:1.38;margin:3px 0}
.list li::before{content:"";position:absolute;left:2px;top:8px;width:6px;height:6px;border-radius:50%;background:var(--blue)}
.mira .list li::before{background:var(--ok)}.falla .list li::before{background:var(--bad)}
.tbl{border-collapse:collapse;width:100%;font-size:15px}
.tbl th{text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);border-bottom:2px solid var(--line);padding:4px 7px}
.tbl td{border-bottom:1px solid var(--line);padding:4px 7px;vertical-align:top;line-height:1.3}
.tbl .mono{font-size:13.5px}
.tag{display:inline-block;align-self:flex-start;padding:2px 12px;border-radius:999px;font-size:14.5px;font-weight:700;border:1.5px solid}
.tag.vivo{color:var(--ok);border-color:var(--ok);background:#f1faf5}
.tag.leer{color:var(--gold);border-color:var(--gold);background:#fff8e6}
.term{background:var(--code);border-radius:10px;overflow:hidden;border:1px solid #23344a}
.term .bar{display:flex;align-items:center;gap:8px;padding:5px 10px;background:#1a2a3e;color:#b8c7d9;font-size:13px}
.term .bar em{flex:1;font-style:normal}
.tls{padding:5px 8px 7px;font-family:var(--mono);font-size:14px;line-height:1.4}
.tln{display:flex;align-items:flex-start;gap:6px;padding:2px 4px}
.tln code{flex:1;white-space:pre-wrap;overflow-wrap:anywhere;color:var(--codetx)}
.tln.c{color:#8fa3b8;font-style:italic}
.ps{color:#7fd4a8}
pre.code{margin:0;padding:8px 12px 10px;font-family:var(--mono);font-size:11.6px;line-height:1.36;color:var(--codetx);white-space:pre-wrap;overflow-wrap:anywhere}
pre.code.light{color:var(--text);padding:2px 2px;font-size:12px;line-height:1.35;white-space:pre;overflow:hidden}
.cp{flex:none;min-width:26px;height:24px;border-radius:6px;border:1px solid #55708f;font-size:13px;color:#d8e4f2;background:#22364e}
.cp.ok{border-color:#7fd4a8;color:#7fd4a8}
.cpall{padding:0 10px;font-family:var(--sans);font-size:12px}
.realbox{border:1px solid #9fd1b7;border-radius:10px;padding:6px 10px;background:#fbfdfc}
.realbox .rk{font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--ok);font-weight:700;margin-bottom:3px}
.realbox pre{font-family:var(--mono);font-size:13.5px;line-height:1.36;white-space:pre-wrap;overflow-wrap:anywhere;color:var(--text)}
.realbox.pq pre{font-size:12.6px}
.capcol{gap:8px}
.cap{margin:0;display:flex;flex-direction:column;gap:3px;min-width:0}
.cap figcaption{font-size:13px;color:var(--muted)}
.capa{display:block;cursor:zoom-in;padding:0;text-align:left}
.capa img{display:block;max-width:100%;height:auto;border-radius:8px;border:1px solid var(--line);background:#fff}
.falta{display:flex;flex-direction:column;justify-content:center;align-items:center;gap:4px;min-height:120px;border:2px dashed #b9c3cf;border-radius:8px;background:#f8fafc;color:var(--muted);text-align:center;padding:10px}
.falta b{color:var(--text);font-size:16px}.falta small{font-size:12.5px}
.bars{display:flex;flex-direction:column;gap:7px}
.brow{display:grid;grid-template-columns:270px 1fr 150px;gap:10px;align-items:center;font-size:15.5px}
.bt{height:20px;background:#eef1f5;border-radius:5px;overflow:hidden;display:block}
.b{display:block;height:100%}
.b.mal,.dot.mal{background:var(--bad)}.b.bien,.dot.bien{background:var(--blue)}.b.ref,.dot.ref{background:#7b8794}
.dot{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:3px;vertical-align:-1px}
.bv{font-size:15.5px}
details summary{cursor:pointer;color:var(--blue);font-size:14.5px;margin-top:4px}
details p{margin-top:6px}
#bar{position:fixed;left:0;right:0;bottom:0;height:46px;display:flex;align-items:center;gap:6px;padding:0 10px;background:#f3f5f8;border-top:1px solid var(--line);font-size:13.5px}
#bar button,#bar a{padding:5px 10px;border-radius:7px;border:1px solid var(--line);background:#fff;text-decoration:none;color:var(--text)}
#bar .part.on{background:var(--blue);color:#fff;border-color:var(--blue)}
#bar .sp{flex:1}
#count,#clockref{color:var(--muted);padding:0 6px}
#prog{position:fixed;left:0;top:0;height:3px;background:var(--blue);z-index:5}
#notes{position:fixed;right:12px;bottom:56px;width:min(460px,92vw);max-height:60vh;overflow:auto;background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px 16px;box-shadow:0 8px 30px rgba(0,0,0,.15);display:none;z-index:10}
#notes.on{display:block}#notes p{font-size:15px}
#index{position:fixed;inset:0 0 46px 0;background:rgba(255,255,255,.98);display:none;overflow:auto;padding:24px 30px;z-index:9}
#index.on{display:block}
#idxgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:8px;margin-top:12px}
#idxgrid button{text-align:left;border:1px solid var(--line);border-radius:9px;padding:8px 10px;background:#fff;font-size:14px}
#idxgrid button small{display:block;color:var(--muted);font-size:12px}
#idxgrid button.cur{border-color:var(--blue);background:#eef4fb}
#zoom{position:fixed;inset:0;background:rgba(10,16,24,.88);display:none;align-items:center;justify-content:center;z-index:20;cursor:zoom-out;padding:20px}
#zoom.on{display:flex}
#zoom img{max-width:100%;max-height:100%;border-radius:6px;background:#fff}
#zoom p{position:absolute;bottom:10px;left:0;right:0;text-align:center;color:#e6eef8;font-size:14px}
@media print{#bar,#prog,#notes,#index,#zoom,.cp{display:none!important}}
"""

JS = r"""
(function(){
'use strict';
const $=s=>document.querySelector(s), $$=(s,r)=>[...(r||document).querySelectorAll(s)];
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const PARTES=__PARTES__, INICIO=__INICIO__;
async function copyText(t){try{await navigator.clipboard.writeText(t);return true}catch(e){try{const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();document.execCommand('copy');a.remove();return true}catch(e2){return false}}}
const slides=$$('.slide'), N=slides.length;
slides.forEach((s,i)=>{const f=document.createElement('div');f.className='foot';
  f.innerHTML=`<span>ML e IA · S4 · Extra: un LLM y el estilo de color</span><span><b>${esc(PARTES[s.dataset.part])}</b> · ${i+1} / ${N}</span>`;s.appendChild(f)});
const cum=[];(()=>{let t=0;slides.forEach(s=>{cum.push(t);t+=+s.dataset.min||0})})();
const TOTAL=cum[N-1]+(+slides[N-1].dataset.min||0);
let cur=0;
function go(i){i=Math.max(0,Math.min(N-1,i));cur=i;slides.forEach((s,k)=>s.classList.toggle('active',k===i));chrome();
  try{history.replaceState(null,'','#'+(i+1))}catch(e){}}
function chrome(){const s=slides[cur];
  $('#count').textContent=(cur+1)+' / '+N;
  $('#clockref').textContent='min '+cum[cur]+' de '+TOTAL;
  $('#prog').style.width=((cur+1)/N*100)+'%';
  $$('#bar .part').forEach(b=>b.classList.toggle('on',b.dataset.p===s.dataset.part));
  $('#notetext').innerHTML='<p>'+esc(s.dataset.notes||'')+'</p>';
  $('#notemin').textContent='Previsto: '+(s.dataset.min||0)+' min · acumulado '+cum[cur]+' de '+TOTAL;
  $$('#idxgrid button').forEach((b,k)=>b.classList.toggle('cur',k===cur))}
function fit(){const v=$('#viewport');$('#stage').style.setProperty('--s',Math.min(v.clientWidth/1280,v.clientHeight/720).toFixed(4))}
addEventListener('resize',fit);
$('#idxgrid').innerHTML=slides.map((s,i)=>`<button data-i="${i}"><small>${esc(PARTES[s.dataset.part])} · ${s.dataset.min} min · min ${INICIO+cum[i]}</small>${i+1}. ${esc(s.dataset.title)}</button>`).join('');
$('#idxgrid').addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;tog('#index',false);go(+b.dataset.i)});
function tog(sel,force){$(sel).classList.toggle('on',force)}
$('#bprev').onclick=()=>go(cur-1); $('#bnext').onclick=()=>go(cur+1);
$('#bidx').onclick=()=>tog('#index'); $('#bnotes').onclick=()=>tog('#notes');
$('#bfull').onclick=()=>{if(document.fullscreenElement)document.exitFullscreen();else if(document.documentElement.requestFullscreen)document.documentElement.requestFullscreen()};
$$('#bar .part').forEach(b=>b.onclick=()=>go(slides.findIndex(s=>s.dataset.part===b.dataset.p)));
const zoom=$('#zoom');
function cerrarZoom(){zoom.classList.remove('on');$('#zoom img').removeAttribute('src')}
zoom.addEventListener('click',cerrarZoom);
addEventListener('keydown',e=>{
  const t=e.target; if(t&&/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName))return; if(e.ctrlKey||e.metaKey||e.altKey)return;
  const k=e.key;
  if(k==='Escape'){if(zoom.classList.contains('on')){cerrarZoom();return}tog('#index',false);tog('#notes',false);return}
  if(zoom.classList.contains('on'))return;
  if(k==='ArrowRight'||k==='PageDown'||(k===' '&&!/^(BUTTON|A|SUMMARY)$/.test(t.tagName))){e.preventDefault();go(cur+1)}
  else if(k==='ArrowLeft'||k==='PageUp'){e.preventDefault();go(cur-1)}
  else if(k==='Home'){e.preventDefault();go(0)} else if(k==='End'){e.preventDefault();go(N-1)}
  else if(k==='o'||k==='O')tog('#index'); else if(k==='s'||k==='S')tog('#notes'); else if(k==='f'||k==='F')$('#bfull').click();
});
document.addEventListener('click',async e=>{
  const z=e.target.closest('.capa'); if(z){$('#zoom img').src=z.dataset.src;$('#zoom img').alt=z.dataset.alt;$('#zoom p').textContent=z.dataset.alt+' · clic o Esc para cerrar';zoom.classList.add('on');return}
  const b=e.target.closest('.cp'); if(!b)return; e.stopPropagation();
  const ok=await copyText(b.dataset.t); const tx=b.textContent; b.classList.add('ok'); b.textContent=ok?'✓ Copiado':'✗'; setTimeout(()=>{b.classList.remove('ok');b.textContent=tx},1200)});
fit(); const h=parseInt((location.hash||'').slice(1),10); go(isNaN(h)?0:h-1);
})();
"""


def html_completo():
    construir()
    secciones = []
    for s in SLIDES:
        secciones.append(f'<section class="slide" data-part="{s["parte"]}" data-min="{s["min"]}" data-title="{esc(s["titulo"])}"\n'
                         f' data-notes="{esc(s["notas"])}">\n{s["html"]}\n</section>')
    js = JS.replace('__PARTES__', json.dumps(PARTES, ensure_ascii=False)).replace('__INICIO__', str(INICIO_SESION))
    partes = ''.join(f'<button class="part" data-p="{k}">{esc(v)}</button>' for k, v in PARTES.items())
    return ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>Un LLM y el estilo de color · Extra S4 · ML e IA: de desarrollo a producción</title>\n'
            f'<!-- Generado por generar.py: no se edita a mano. -->\n<style>{CSS}</style>\n</head>\n<body>\n'
            '<div id="prog"></div>\n<div id="viewport"><div id="stage">\n\n' + '\n\n'.join(secciones) + '\n\n</div></div>\n\n'
            '<aside id="notes" aria-label="Notas del ponente"><h3>Notas del ponente</h3><div id="notetext"></div><p class="small" id="notemin"></p></aside>\n'
            '<div id="index" aria-label="Índice"><h2>Índice</h2><div id="idxgrid"></div></div>\n'
            '<div id="zoom" role="dialog" aria-label="Captura ampliada"><img alt=""><p></p></div>\n'
            '<nav id="bar" aria-label="Controles">\n'
            '  <button id="bprev" aria-label="Anterior">←</button><button id="bnext" aria-label="Siguiente">→</button>\n'
            f'  <span id="count">1 / 1</span><span id="clockref" title="Minuto planificado"></span>\n  {partes}\n  <span class="sp"></span>\n'
            '  <a id="bhome" href="../index.html" title="Volver al índice de la sesión S4">⌂ S4</a><button id="bidx">Índice (O)</button><button id="bnotes">Notas (S)</button><button id="bfull">Pantalla completa (F)</button>\n'
            '</nav>\n'
            '<noscript>Esta presentación necesita JavaScript. El mismo recorrido está en README.md y guia-pipeline.md.</noscript>\n\n'
            f'<script>{js}</script>\n</body>\n</html>\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--comprobar', action='store_true')
    a = ap.parse_args()
    nuevo = html_completo()
    actual = SALIDA.read_text(encoding='utf-8') if SALIDA.exists() else None
    faltan = [n for n in CAPTURAS if not (IMG / n).exists()]
    if a.comprobar:
        if actual != nuevo:
            print('DESFASADO: ejecuta python generar.py')
            sys.exit(1)
        print('al día')
        return
    if actual == nuevo:
        print('sin cambios')
    else:
        SALIDA.write_text(nuevo, encoding='utf-8')
        print(f'escrito {SALIDA.name}: {len(SLIDES)} diapositivas, {sum(s["min"] for s in SLIDES)} min')
    if faltan:
        print(f'imágenes pendientes ({len(faltan)}): ' + ', '.join(faltan))


if __name__ == '__main__':
    main()

