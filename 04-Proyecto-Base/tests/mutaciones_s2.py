"""Roturas deliberadas de S2: cambia UNA cosa en el codigo, en el Dockerfile o en las dependencias y comprueba que alguna prueba falla.

No es una prueba mas (no empieza por test_): es una forma de comprobar que las pruebas sirven. Cada rotura se deshace al terminar.
Uso, desde la carpeta del proyecto con el entorno activado:   python tests/mutaciones_s2.py
"""
import subprocess, sys, shutil, os
from pathlib import Path
R = Path(__file__).resolve().parents[1]      # la carpeta del proyecto
PY = sys.executable
env = dict(os.environ, MLFLOW_DISABLE_AGENT_HINT='1')
MUTACIONES = [
 ('la API deja de rechazar campos desconocidos','ia_mlops/api/esquemas.py',"extra='forbid', json_schema_extra","json_schema_extra",'tests/test_api.py'),
 ('se quita la comprobacion de coherencia entre variables','ia_mlops/api/esquemas.py',"    @model_validator(mode='after')\n    def _coherencia(self):","    @model_validator(mode='after')\n    def _coherencia(self):\n        return self\n    def _vieja(self):",'tests/test_api.py'),
 ('recencia_dias admite negativos','ia_mlops/api/esquemas.py',"recencia_dias: int = Field(ge=0,","recencia_dias: int = Field(ge=-10000,",'tests/test_api.py'),
 ('frecuencia admite 0 (cliente sin historia)','ia_mlops/api/esquemas.py',"frecuencia: int = Field(ge=1,","frecuencia: int = Field(ge=0,",'tests/test_api.py'),
 ('el esquema cambia el orden de dos variables','ia_mlops/api/esquemas.py',"    ticket_medio: float = Field(ge=0, le=1e9, description='Gasto medio por factura = monto_total / frecuencia')\n","",'tests/test_api.py'),
 ('no se comprueba la firma frente a los metadatos','ia_mlops/api/servicio.py',"if de_la_firma != meta['variables']:","if False:",'tests/test_api.py'),
 ('no se comprueba el esquema de la API frente a la firma al arrancar','ia_mlops/api/servicio.py',"        if faltan or sobran:\n            raise ContratoRoto(f'El esquema","        if False:\n            raise ContratoRoto(f'El esquema",'tests/test_api.py'),
 ('no se avisa de valores fuera del rango de entrenamiento','ia_mlops/api/servicio.py',"if valor is not None and not minimo <= valor <= maximo:","if False:",'tests/test_api.py'),
 ('el lote devuelve el orden invertido','ia_mlops/api/app.py',"for p, a in s.predecir([c.model_dump() for c in lote.clientes])]","for p, a in s.predecir([c.model_dump() for c in lote.clientes][::-1])]",'tests/test_api.py'),
 ('el error 500 revela el detalle interno','ia_mlops/api/app.py',"content={'detalle': 'Error interno', 'id_peticion': id_peticion}","content={'detalle': 'Error interno: ' + str(__import__('sys').exc_info()[1]), 'id_peticion': id_peticion}",'tests/test_api.py'),
 ('la app no configura el registro (el defecto real de S2 de la solucion)','ia_mlops/api/app.py',"    configurar_registro()\n\n    @asynccontextmanager","    @asynccontextmanager",'tests/test_api.py'),
 ('el servicio tarda en declararse listo: /listo siempre 200','ia_mlops/api/app.py',"    def listo(request: Request):\n        servicio_listo(request)\n        return","    def listo(request: Request):\n        return",'tests/test_api.py'),
 ('el Dockerfile copia el codigo antes de instalar','deploy/docker/Dockerfile',"COPY requirements-api.lock .\nRUN pip install -r requirements-api.lock\n","COPY ia_mlops/ ia_mlops/\nCOPY requirements-api.lock .\nRUN pip install -r requirements-api.lock\n",'tests/test_imagen.py'),
 ('el Dockerfile se ejecuta como root','deploy/docker/Dockerfile',"USER 10001\n","",'tests/test_imagen.py'),
 ('el Dockerfile pierde el HEALTHCHECK','deploy/docker/Dockerfile',"HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \\\n    CMD python -c \"import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/salud', timeout=2)\"\n","",'tests/test_imagen.py'),
 ('el Dockerfile usa otra version de Python','deploy/docker/Dockerfile',"FROM python:3.11-slim","FROM python:3.12-slim",'tests/test_imagen.py'),
 ('el Dockerfile copia los datos','deploy/docker/Dockerfile',"COPY models/metadatos.json models/metadatos.json","COPY models/metadatos.json models/metadatos.json\nCOPY data/ data/",'tests/test_imagen.py'),
 ('el Dockerfile apunta a otro modulo','deploy/docker/Dockerfile','"ia_mlops.api.app:app"','"ia_mlops.api.main:app"','tests/test_imagen.py'),
 ('.dockerignore excluye el modelo MLflow','.dockerignore',"models/mlflow.db\n","models/mlflow.db\nmodels/modelo_mlflow/\n",'tests/test_imagen.py'),
 ('.dockerignore deja de excluir los datos','.dockerignore',"data/\n","",'tests/test_imagen.py'),
 ('el archivo de versiones exactas no coincide','requirements-api.lock',"fastapi==0.162.2","fastapi==0.100.0",'tests/test_imagen.py'),
 ('la imagen instala mlflow completo','requirements-api.lock',"mlflow-skinny==3.18.0","mlflow-skinny==3.18.0\nmlflow==3.18.0",'tests/test_imagen.py'),
 ('train deja de exportar el modelo en formato MLflow','ia_mlops/modeling/train.py',"    exportar_modelo_mlflow(modelo, X['train'].head(200), config.MODELOS / config.CARPETA_MODELO_MLFLOW)\n","",'tests/test_api.py'),
 ('train guarda metadatos sin rangos','ia_mlops/modeling/train.py',"        'rangos_entrenamiento': rangos_de_entrenamiento(X['train']),\n","        'rangos_entrenamiento': {c: [-1e18, 1e18] for c in X['train'].columns},\n",'tests/test_api.py'),
]
res=[]
for nombre,arch,a,b,tests in MUTACIONES:
    p=R/arch; orig=p.read_text(encoding='utf-8')
    if a not in orig: res.append((nombre,'NO APLICA (no encuentra el texto)','')); continue
    p.write_text(orig.replace(a,b,1),encoding='utf-8')
    try:
        r=subprocess.run([PY,'-m','pytest',tests,'-q','-x','-p','no:cacheprovider','--no-header'],cwd=R,env=env,capture_output=True,text=True,timeout=600)
        fallos=[l for l in r.stdout.splitlines() if l.startswith('FAILED')]
        resumen=r.stdout.strip().splitlines()[-1]
        res.append((nombre,'DETECTADA' if r.returncode!=0 else 'NO DETECTADA',(fallos[0][:140] if fallos else resumen)))
    finally:
        p.write_text(orig,encoding='utf-8')
for n,e,d in res: print(f'[{n}] -> {e} | {d}')
print(); print(sum(1 for _,e,_ in res if e=='DETECTADA'),'de',len(res),'detectadas')
