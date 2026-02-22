from datetime import datetime, time
from enum import Enum
from typing import Any

from pydantic import BaseModel

TIME_FORMAT = "%H:%M:%S"
DATE_FORMAT = "%d/%m/%Y"


class MovimientoTipo(str, Enum):
    ABONO = "Abono"
    CARGO = "Cargo"


class ProductoNombreTipo(str, Enum):
    CUENTA_CORRIENTE = "Cuenta Corriente"
    LINEA_CREDITO = "Línea de Crédito"


class DetalleItem(BaseModel):
    identificador: str
    descripcion: str
    hora: str
    monto: str
    saldo: str
    tipo: MovimientoTipo

    @property
    def time(self) -> time:
        return datetime.strptime(self.hora, TIME_FORMAT).time()

    @property
    def monto_float(self) -> float:
        return float(self.monto.replace("$", "").replace(".", ""))


class DtoResponseSetResultado(BaseModel):
    fecha: str
    detalle: list[DetalleItem]

    @property
    def date(self) -> datetime:
        return datetime.strptime(self.fecha, DATE_FORMAT)


class DtoResponseCodigosEstadoHttp(BaseModel):
    codigo: str
    mensaje: str
    descripcion: str


class MovementsResponse(BaseModel):
    dtoResponseCodigosEstadoHttp: DtoResponseCodigosEstadoHttp
    dtoResponseSetResultados: list[DtoResponseSetResultado]


class ProductItem(BaseModel):
    nombreProducto: str
    numeroCuenta: str
    codigoProducto: str
    nombreCuenta: str
    prioridadProducto: int


class ProductsResponse(BaseModel):
    products: list[ProductItem]


class CreditCardMovement(BaseModel):
    pass


class CreditCard(BaseModel):
    nationalMovements: list[Any]
    internationalMovements: list[Any]
    numCard: str
    lastnumCard: str


class NoFacturadosBodyResponse(BaseModel):
    tarjetas: list[CreditCard]


class NoFacturadosResponse(BaseModel):
    codigo: str
    mensaje: str
    date: str
    errors: list[Any]
    bodyResponse: NoFacturadosBodyResponse
