from typing import Any, List

from pydantic import BaseModel


class DetalleItem(BaseModel):
    identificador: str
    descripcion: str
    hora: str
    monto: str
    saldo: str
    tipo: str


class DtoResponseSetResultado(BaseModel):
    fecha: str
    detalle: List[DetalleItem]


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
