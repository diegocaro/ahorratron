from datetime import datetime, time
from enum import Enum
from typing import Any, overload

from pydantic import BaseModel

TIME_FORMAT = "%H:%M:%S"
DATE_FORMAT = "%d/%m/%Y"


@overload
def currency_to_float(value: None) -> None: ...


@overload
def currency_to_float(value: str) -> float: ...


def currency_to_float(value: str | None) -> float | None:
    """Convert Chilean currency string to float. Returns None if value is None."""
    if value is None:
        return None
    return float(value.replace("$", "").replace(".", ""))


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
        return currency_to_float(self.monto)


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
    key_account: str


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


class ResumenCuentaResponse(BaseModel):
    numeroCuenta: int
    saldoInicial: str
    saldoContable: str
    saldoDisponible: str
    totalCargos: str
    totalAbonos: str
    totalSobregiro: str | None
    totalRetenciones: str

    @property
    def saldo_disponible_float(self) -> float:
        return currency_to_float(self.saldoDisponible)
