"""Logica del servicio: carga del modelo, comprobacion del contrato y prediccion. No sabe nada de HTTP.

El modelo se carga en formato MLflow y su FIRMA es el contrato: si las variables que declara la firma no coinciden con las de
metadatos.json, o si el esquema de la API (esquemas.Cliente) no tiene las mismas variables que la firma, el servicio NO arranca listo
(mejor fallar al inicio que predecir con las columnas equivocadas).
"""
import json
from pathlib import Path

import pandas as pd

from .. import config


class ModeloNoDisponible(RuntimeError):
    pass


class ContratoRoto(RuntimeError):
    pass


class Servicio:
    def __init__(self, modelo, meta):
        self.modelo = modelo
        self.meta = meta
        self.variables = list(meta['variables'])

    @classmethod
    def cargar(cls, carpeta=None):
        """Carga models/modelo_mlflow y models/metadatos.json (o la carpeta indicada)."""
        carpeta = Path(carpeta or config.MODELOS)
        ruta_modelo, ruta_meta = carpeta / config.CARPETA_MODELO_MLFLOW, carpeta / 'metadatos.json'
        if not (ruta_modelo / 'MLmodel').exists() or not ruta_meta.exists():
            raise ModeloNoDisponible(f'No hay modelo en {carpeta}. Entrenalo antes: python -m ia_mlops.pipeline')
        import mlflow.models
        import mlflow.sklearn
        meta = json.loads(ruta_meta.read_text(encoding='utf-8'))
        firma = mlflow.models.Model.load(str(ruta_modelo)).signature
        if firma is None:
            raise ContratoRoto('El modelo no tiene firma: no se puede comprobar el contrato.')
        de_la_firma = [c.name for c in firma.inputs.inputs]
        if de_la_firma != meta['variables']:
            raise ContratoRoto(f'La firma del modelo {de_la_firma} no coincide con metadatos.json {meta["variables"]}.')
        return cls(mlflow.sklearn.load_model(str(ruta_modelo)), meta)

    def comprobar_esquema(self, campos_api):
        """El esquema de la API (Cliente) debe tener EXACTAMENTE las variables de la firma del modelo.

        Si se reentrena con una variable nueva y no se actualiza el esquema, sin esta comprobacion el servicio diria «listo» y fallaria
        en cada prediccion. Con ella, no arranca listo y /listo dice que variable falta.
        """
        faltan = [v for v in self.variables if v not in campos_api]
        sobran = [c for c in campos_api if c not in self.variables]
        if faltan or sobran:
            raise ContratoRoto(f'El esquema de la API no coincide con la firma del modelo. Faltan en la API: {faltan}. Sobran en la API: {sobran}. '
                               'Actualiza ia_mlops/api/esquemas.py (clase Cliente y EJEMPLO) o reentrena con las variables del esquema.')

    def advertencias(self, fila):
        """Valores validos que el modelo no vio al entrenar: no se rechazan, se avisan."""
        avisos = []
        if fila['dias_medios_entre_compras'] is None:
            avisos.append('dias_medios_entre_compras no informado: el modelo usa la mediana del entrenamiento.')
        for variable, (minimo, maximo) in self.meta['rangos_entrenamiento'].items():
            valor = fila[variable]
            if valor is not None and not minimo <= valor <= maximo:
                avisos.append(f'{variable}={valor} esta fuera del rango visto al entrenar [{minimo:g}, {maximo:g}]; la prediccion no tiene respaldo ahi.')
        return avisos

    def predecir(self, filas):
        """filas: lista de diccionarios con las variables. Devuelve una lista de (probabilidad, advertencias)."""
        df = pd.DataFrame(filas)[self.variables]
        # Una columna que solo trae None llega como object; la firma pide un numero (dias_medios_entre_compras es opcional).
        df['dias_medios_entre_compras'] = pd.to_numeric(df['dias_medios_entre_compras'], errors='coerce').astype('float64')
        prob = self.modelo.predict_proba(df)[:, 1]
        return [(float(p), self.advertencias(f)) for p, f in zip(prob, filas)]

    def info(self):
        m = self.meta
        return {k: m[k] for k in ('modelo', 'objetivo', 'huella_datos', 'entrenado_en', 'variables', 'filas', 'metricas_valid', 'versiones')}
