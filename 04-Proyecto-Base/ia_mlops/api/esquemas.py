"""Contrato de la API: que se recibe y que se devuelve.

Los limites de cada campo salen de como se construye la capa FS (sql/fs/02_poblar_fs.sql), NO de lo visto al entrenar: un cliente con mas
facturas que cualquiera de train es un cliente legitimo. Lo que el modelo no vio se avisa en `advertencias`; lo imposible se rechaza (422).

Se rechaza TODO campo desconocido (`extra='forbid'`): asi una variable que el modelo no usa, o que se conoce DESPUES del corte, devuelve 422
en vez de ignorarse en silencio.

Tambien se rechazan las combinaciones que FS nunca produce (p. ej. mas facturas en 90 dias que en total): son, casi seguro, un error de quien llama.
"""
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

EJEMPLO = {
    'recencia_dias': 35, 'frecuencia': 6, 'monto_total': 1250.40, 'ticket_medio': 208.4, 'unidades_total': 410, 'productos_distintos': 38,
    'antiguedad_dias': 310, 'frecuencia_90d': 2, 'monto_90d': 380.5, 'frecuencia_180d': 4, 'dias_medios_entre_compras': 55.0,
    'devoluciones': 1, 'es_reino_unido': 1,
}


class Cliente(BaseModel):
    """Lo que se sabe de un cliente en la fecha de corte, calculado SOLO con datos anteriores al corte (capa FS)."""
    model_config = ConfigDict(extra='forbid', json_schema_extra={'examples': [EJEMPLO]})

    recencia_dias: int = Field(ge=0, le=1000, description='Dias desde su ultima compra valida hasta el corte')
    frecuencia: int = Field(ge=1, le=100000, description='Facturas con ventas validas antes del corte (al menos 1: sin historia no hay variables)')
    monto_total: float = Field(ge=0, le=1e9, description='Gasto acumulado, en libras')
    ticket_medio: float = Field(ge=0, le=1e9, description='Gasto medio por factura = monto_total / frecuencia')
    unidades_total: int = Field(ge=0, le=100000000, description='Unidades compradas')
    productos_distintos: int = Field(ge=0, le=100000, description='Productos distintos comprados')
    antiguedad_dias: int = Field(ge=0, le=1000, description='Dias desde su primera compra valida hasta el corte')
    frecuencia_90d: int = Field(ge=0, le=100000, description='Facturas en los 90 dias previos al corte')
    monto_90d: float = Field(ge=0, le=1e9, description='Gasto en los 90 dias previos al corte')
    frecuencia_180d: int = Field(ge=0, le=100000, description='Facturas en los 180 dias previos al corte')
    dias_medios_entre_compras: Optional[float] = Field(
        default=None, ge=0, le=1000, description='Intervalo medio entre compras; null si solo hay una factura (el modelo lo imputa)')
    devoluciones: int = Field(ge=0, le=100000, description='Facturas de cancelacion antes del corte')
    es_reino_unido: Literal[0, 1] = Field(description='1 si el cliente es del Reino Unido, 0 si no')

    @model_validator(mode='after')
    def _coherencia(self):
        if self.antiguedad_dias < self.recencia_dias:
            raise ValueError('antiguedad_dias no puede ser menor que recencia_dias (la primera compra no puede ser posterior a la ultima)')
        if not self.frecuencia_90d <= self.frecuencia_180d <= self.frecuencia:
            raise ValueError('debe cumplirse frecuencia_90d <= frecuencia_180d <= frecuencia')
        if self.monto_90d > self.monto_total + 0.01:
            raise ValueError('monto_90d no puede superar a monto_total')
        if abs(self.ticket_medio * self.frecuencia - self.monto_total) > 0.01 * self.frecuencia + 0.01:
            raise ValueError('ticket_medio debe ser monto_total / frecuencia')
        if (self.frecuencia <= 1) != (self.dias_medios_entre_compras is None):
            raise ValueError('dias_medios_entre_compras es null si y solo si hay una sola factura')
        return self


class Prediccion(BaseModel):
    probabilidad: float = Field(ge=0, le=1, description='Probabilidad de que el cliente compre al menos una vez en los 90 dias siguientes al corte')
    modelo: str
    huella_datos: str = Field(description='Identifica con que datos se entreno el modelo')
    advertencias: list[str] = Field(default_factory=list, description='Cosas que el modelo no vio en el entrenamiento')


class LoteClientes(BaseModel):
    model_config = ConfigDict(extra='forbid')
    clientes: list[Cliente] = Field(min_length=1, max_length=1000)


class PrediccionLote(BaseModel):
    predicciones: list[Prediccion]


class InfoModelo(BaseModel):
    modelo: str
    objetivo: str
    huella_datos: str
    entrenado_en: str
    variables: list[str]
    filas: dict
    metricas_valid: dict
    versiones: dict


class Error(BaseModel):
    detalle: str
    id_peticion: Optional[str] = None
