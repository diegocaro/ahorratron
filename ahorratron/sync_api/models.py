from typing import List, Optional

from pydantic import BaseModel


### REQUEST MODELS ###
class MovimientosNoFacturadosRequest(BaseModel):
    idTarjeta: str
    codigoProducto: str
    tipoTarjeta: str
    mascara: str
    nombreTitular: str
    tipoCliente: str


class CuentaSeleccionada(BaseModel):
    nombreCliente: str
    rutCliente: str
    numero: str
    mascara: str
    codigoProducto: str
    claseCuenta: str
    moneda: str
    # selected: bool | None = None


class Cabecera(BaseModel):
    statusGenerico: bool = True
    paginacionDesde: int = 1


class GetCartolaCuentaRequest(BaseModel):
    cuentaSeleccionada: CuentaSeleccionada
    cabecera: Cabecera


#### RESPONSES MODELS ####
class Producto(BaseModel):
    id: str
    numero: str
    mascara: str
    codigo: str
    codigoMoneda: str
    alias: Optional[str]
    label: str
    tipo: str
    claseCuenta: str
    subProducto: Optional[str]
    estado: str
    detalleEstado: Optional[str]
    tarjetaHabiente: Optional[str]
    descripcionLogo: str
    tipoCliente: str


class ObtenerProductosResponse(BaseModel):
    rut: str
    nombre: str
    productos: List[Producto]


class MovimientoNoFacturado(BaseModel):
    origenTransaccion: str
    fechaTransaccion: int
    fechaTransaccionString: str
    montoCompra: float
    glosaTransaccion: str
    codigoComercioTBK: int
    codigoComercioINT: str
    nombreComercio: str
    rubroComercio: str
    codigoPaisComercio: str
    ciudad: str
    fechaAutorizacion: str
    horaAutorizacion: str
    numeroTarjeta: str
    descripcionTransaccion: str
    montoMonedaOrigen: str
    codigoMonedaOrigen: int
    despliegueCuotas: str
    numeroCuotas: str
    numeroTotalCuotas: str
    tipoTarjeta: str
    fechaAutorizacionString: str
    montoCompraString: str
    nombreTarjetaHabiente: str
    numeroTarjetaCompleto: Optional[str]


class NoFacturadosResponse(BaseModel):
    tarjetaHabiente: str
    fechaFacturacionAnterior: int
    fechaAhora: int
    fechaFacturacionAnteriorString: str
    fechaAhoraString: str
    fechaProximaFacturacionCalendario: str
    listaMovNoFactur: List[MovimientoNoFacturado]


class Movimiento(BaseModel):
    estado: Optional[str]
    descripcion: str
    monto: str
    saldo: str
    nombreCuenta: str
    numeroCuenta: str
    idCuenta: str
    canal: str
    tipo: str
    fecha: str
    fechaContable: str
    id: str
    numeroDocumento: str
    fechaContableMovimiento: int
    detalleGlosa: List[str]


class GetCartolaResponse(BaseModel):
    horaConsulta: str
    moneda: str
    saldoFinal: int
    totalCargos: int
    totalAbonos: int
    retencion1Dia: int
    retencionNDia: int
    montoAutorizado: int
    montoUtilizado: int
    saldoDisponible: int
    lineaCredito: int
    movimientos: List[Movimiento]
