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
    alias: str | None
    label: str
    tipo: str
    claseCuenta: str
    subProducto: str | None
    estado: str
    detalleEstado: str | None
    tarjetaHabiente: str | None
    descripcionLogo: str
    tipoCliente: str


class ObtenerProductosResponse(BaseModel):
    rut: str
    nombre: str
    productos: list[Producto]


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
    numeroTarjetaCompleto: str | None


class NoFacturadosResponse(BaseModel):
    tarjetaHabiente: str
    fechaFacturacionAnterior: int
    fechaAhora: int
    fechaFacturacionAnteriorString: str
    fechaAhoraString: str
    fechaProximaFacturacionCalendario: str
    listaMovNoFactur: list[MovimientoNoFacturado]


class Movimiento(BaseModel):
    estado: str | None
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
    detalleGlosa: list[str]


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
    movimientos: list[Movimiento]
