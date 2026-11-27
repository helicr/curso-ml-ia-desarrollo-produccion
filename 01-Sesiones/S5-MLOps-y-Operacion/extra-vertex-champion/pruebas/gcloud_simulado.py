"""Un `gcloud` SIMULADO (solo para las pruebas): ejecuta los scripts de scripts/*.sh de verdad contra una pequeña máquina de estados.

NO es Google Cloud ni lo imita por completo: solo implementa las órdenes que usan los scripts, con las reglas que dice la documentación
oficial (el reparto de tráfico debe sumar 100 y nombrar modelos desplegados; no se borra un endpoint con modelos desplegados) y los
nombres de campo JSON que los scripts SUPONEN (`deployedModels[].id/displayName`, `trafficSplit`, `versionAliases`, `labels`):
si Google los llama de otra forma, las pruebas pasan y el script falla en la nube. Por eso esos campos están marcados SIN VERIFICAR.

Estado en $FAKE_GCLOUD_ESTADO (JSON) y registro de las llamadas en $FAKE_GCLOUD_LOG (una por línea).
$FAKE_GCLOUD_PREDICCIONES: JSON con las predicciones que devuelve `endpoints predict` (se les pone version_mlflow del modelo que «contesta»).
"""
import json
import os
import sys
from pathlib import Path

ESTADO = Path(os.environ['FAKE_GCLOUD_ESTADO'])
REGISTRO = Path(os.environ['FAKE_GCLOUD_LOG'])
PROYECTO = os.environ.get('FAKE_GCLOUD_PROYECTO', 'project-prueba')
BOOLEANOS = {'--quiet', '--delete-tags', '--async', '--uniform-bucket-level-access', '--public-access-prevention'}


def cargar():
    if ESTADO.exists():
        return json.loads(ESTADO.read_text(encoding='utf-8'))
    return {'repos': [], 'imagenes': [], 'modelos': {}, 'endpoints': {}, 'siguiente_id': 1000, 'llamadas_predict': 0}


def guardar(e):
    ESTADO.write_text(json.dumps(e, indent=1), encoding='utf-8')


def analizar(args):
    palabras, flags, i = [], {}, 0
    while i < len(args):
        a = args[i]
        if a.startswith('--'):
            if '=' in a:
                k, v = a.split('=', 1)
                flags[k] = v
            elif a in BOOLEANOS or i + 1 >= len(args) or args[i + 1].startswith('--'):
                flags[a] = True
            else:
                flags[a] = args[i + 1]
                i += 1
        else:
            palabras.append(a)
        i += 1
    return palabras, flags


def error(msg, codigo=1):
    print(f'ERROR: (gcloud simulado) {msg}', file=sys.stderr)
    sys.exit(codigo)


def etiquetas(texto):
    return dict(p.split('=', 1) for p in texto.split(',')) if texto and texto is not True else {}


def reparto(texto):
    return {k: int(v) for k, v in (p.split('=') for p in texto.split(','))}


def main():
    args = sys.argv[1:]
    if args and args[0] == '__registrar_imagen':             # lo llama el docker simulado tras un docker push
        e = cargar()
        e['imagenes'].append(args[1])
        guardar(e)
        return
    with REGISTRO.open('a', encoding='utf-8') as f:
        f.write('gcloud ' + ' '.join(args) + '\n')
    palabras, flags = analizar(args)
    e = cargar()
    orden = ' '.join(palabras[:3])

    if palabras[:2] == ['config', 'set']:
        return
    if palabras[:2] == ['config', 'get-value']:
        print(PROYECTO)
        return
    if palabras[:2] == ['services', 'enable'] or palabras[:2] == ['auth', 'configure-docker']:
        return
    if orden == 'artifacts repositories describe':
        sys.exit(0 if palabras[3] in e['repos'] else 1)
    if orden == 'artifacts repositories create':
        e['repos'].append(palabras[3])
    elif orden == 'artifacts repositories delete':
        e['repos'].remove(palabras[3])
    elif orden == 'artifacts docker images':
        sub, imagen = palabras[3], palabras[4] if len(palabras) > 4 else ''
        if sub == 'describe':
            sys.exit(0 if imagen in e['imagenes'] else 1)
        if sub == 'delete':
            e['imagenes'] = [i for i in e['imagenes'] if not i.startswith(imagen)]
        if sub == 'list':
            print('\n'.join(i.rsplit(':', 1)[1] for i in e['imagenes'] if i.startswith(imagen)))
    elif orden == 'ai models describe':
        sys.exit(0 if palabras[3] in e['modelos'] else 1)
    elif orden == 'ai models upload':
        if '--artifact-uri' in flags:
            error('el modelo lleva su artefacto dentro de la imagen: no debe usarse --artifact-uri')
        for obligatoria in ('--container-image-uri', '--container-ports', '--container-predict-route', '--container-health-route', '--display-name', '--version-aliases'):
            if obligatoria not in flags:
                error(f'falta {obligatoria}')
        padre = flags.get('--parent-model')
        if padre:
            nombre = padre.rsplit('/', 1)[1]
            if nombre not in e['modelos']:
                error(f'el modelo padre {nombre} no existe')
        else:
            nombre = flags['--model-id']
            if nombre in e['modelos']:
                error(f'el modelo {nombre} ya existe: para otra versión usa --parent-model')
            e['modelos'][nombre] = {'versiones': []}
        versiones = e['modelos'][nombre]['versiones']
        nuevos = flags['--version-aliases'].split(',')
        for v in versiones:                                                   # un alias apunta a UNA versión (SIN VERIFICAR en Vertex real)
            v['versionAliases'] = [a for a in v['versionAliases'] if a not in nuevos]
        versiones.append({'versionId': str(len(versiones) + 1), 'versionAliases': nuevos, 'labels': etiquetas(flags.get('--labels')),
                          'imagen': flags['--container-image-uri'], 'puerto': flags['--container-ports'],
                          'rutaPredict': flags['--container-predict-route'], 'rutaSalud': flags['--container-health-route']})
    elif orden == 'ai models list-version':
        if palabras[3] not in e['modelos']:
            error('el modelo no existe')
        print(json.dumps(e['modelos'][palabras[3]]['versiones']))
    elif orden == 'ai models delete':
        e['modelos'].pop(palabras[3])
    elif orden == 'ai models list':
        print('\n'.join(e['modelos']))
    elif orden == 'ai endpoints describe':
        if palabras[3] not in e['endpoints']:
            sys.exit(1)
        print(json.dumps(e['endpoints'][palabras[3]]))
    elif orden == 'ai endpoints create':
        e['endpoints'][flags['--endpoint-id']] = {'deployedModels': [], 'trafficSplit': {}}
    elif orden == 'ai endpoints list':
        print('\n'.join(e['endpoints']))
    elif orden == 'ai endpoints deploy-model':
        ep = e['endpoints'][palabras[3]]
        modelo, _, version = flags['--model'].partition('@')
        if modelo not in e['modelos'] or not any(v['versionId'] == version for v in e['modelos'][modelo]['versiones']):
            error(f'no existe {flags["--model"]} en el Model Registry')
        if any(d['displayName'] == flags['--display-name'] for d in ep['deployedModels']):
            error('ese nombre ya está desplegado')
        if int(flags['--min-replica-count']) < 1:
            error('--min-replica-count debe ser al menos 1')
        nuevo = str(e['siguiente_id'])
        e['siguiente_id'] += 1
        r = reparto(flags['--traffic-split'])
        if sum(r.values()) != 100:
            error(f'el reparto debe sumar 100 y suma {sum(r.values())}')
        existentes = {d['id'] for d in ep['deployedModels']}
        if set(r) - {'0'} != existentes:
            error(f'el reparto debe nombrar a todos los modelos ya desplegados {sorted(existentes)} y la clave 0 para el nuevo: {r}')
        ep['deployedModels'].append({'id': nuevo, 'displayName': flags['--display-name'], 'model': modelo, 'modelVersionId': version, 'maquina': flags['--machine-type']})
        ep['trafficSplit'] = {(nuevo if k == '0' else k): v for k, v in r.items()}
    elif orden == 'ai endpoints update':
        ep = e['endpoints'][palabras[3]]
        r = reparto(flags['--traffic-split'])
        if sum(r.values()) != 100:
            error(f'el reparto debe sumar 100 y suma {sum(r.values())}')
        if set(r) != {d['id'] for d in ep['deployedModels']}:
            error('el reparto debe nombrar exactamente a los modelos desplegados')
        ep['trafficSplit'] = r
    elif orden == 'ai endpoints undeploy-model':
        ep = e['endpoints'][palabras[3]]
        ident = flags['--deployed-model-id']
        if ident not in {d['id'] for d in ep['deployedModels']}:
            error('ese modelo no está desplegado')
        ep['deployedModels'] = [d for d in ep['deployedModels'] if d['id'] != ident]
        ep['trafficSplit'].pop(ident, None)
    elif orden == 'ai endpoints delete':
        if e['endpoints'][palabras[3]]['deployedModels']:
            error('You can only delete the endpoint after all models have been undeployed from it.')
        e['endpoints'].pop(palabras[3])
    elif orden == 'ai endpoints predict':
        ep = e['endpoints'][palabras[3]]
        con_trafico = sorted((d for d in ep['deployedModels'] if ep['trafficSplit'].get(d['id'], 0) > 0), key=lambda d: d['id'])
        if not con_trafico:
            error('el endpoint no tiene ningún modelo con tráfico')
        elegido = con_trafico[e['llamadas_predict'] % len(con_trafico)]         # alterna entre las versiones con tráfico (determinista)
        e['llamadas_predict'] += 1
        version_mlflow = int(elegido['displayName'].rsplit('-v', 1)[1])
        base = json.loads(Path(os.environ['FAKE_GCLOUD_PREDICCIONES']).read_text(encoding='utf-8'))
        print(json.dumps([dict(p, version_mlflow=version_mlflow) for p in base]))
    else:
        error(f'orden no implementada en el simulador: {" ".join(args)}', 3)
    guardar(e)


if __name__ == '__main__':
    main()
