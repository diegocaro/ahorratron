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


class GetSaldoResponse(BaseModel):
    cupoTotalNacional: int
    cupoUtilizadoNacional: int
    cupoDisponibleNacional: int
    disponibleAvanceNacional: int
    porcentajeDisponibleNacional: int
    cupoTotalInternacional: float
    cupoUtilizadoInternacional: float
    cupoDisponibleInternacional: float
    disponibleAvanceInternacional: float
    porcentajeDisponibleInternacional: int
    fechaConsulta: int
    saldoCreditoCuotaCapital: int
    pagoMinimo: int
    montoFacturado: int
    pagarHastaFecha: str
    facturadoAlFecha: str
    existeEECC: bool
    pagarHasta: str
    facturadoAl: str


class TransaccionTarjeta(BaseModel):
    numReferencia: str
    nombreTarjeta: str
    fechaTransaccion: int
    fechaTransaccionString: str
    montoTransaccion: float
    descripcion: str
    ciudad: str
    cuotas: str
    nombreTitular: str
    # comercio: Any
    # rubro: Any
    totales: bool
    grupo: str
    tituloTotales: str | None
    cambioTarjeta: bool
    aclaracion: dict
    idMovimiento: str
    # estado: Any
    # comprobanteSiebel: Any
    # fechaComprobanteSiebel: Any
    idComprobante: str


class Resumen(BaseModel):
    cupo: float
    cupoUtilizado: float
    cupoDisponible: float
    montoFacturado: float
    pagoMinimo: float
    fechaFacturacionActual: str
    fechaVencimientoFacturacion: str
    fechaProximaFacturacion: str
    totalPagos: float
    totalCargosAutomaticos: float
    totalComprasCuotasAvances: float
    totalCargosAbonosCta: float
    tasaProxPerCredRot: float | None
    # traspasoMonedaNac: Any
    saldoAnteriorFacturado: float


class ProximosPeriodos(BaseModel):
    saldoCapitalCuotas: float
    vencimientoCuotas1: float
    vencimientoCuotas2: float
    vencimientoCuotas3: float
    vencimientoCuotas4: float
    mesVencimientoCuotas1: str
    mesVencimientoCuotas2: str
    mesVencimientoCuotas3: str
    mesVencimientoCuotas4: str
    tasaInteresCreditoRotativo: str
    tasaInteresCreditoCuotas: str


class SeccionOperaciones(BaseModel):
    totalTransacciones: float
    numeroDeTransacciones: int
    mensajeSinTransacciones: str | None
    fechaDesde: str
    fechaHasta: str
    transaccionesTarjetas: list[TransaccionTarjeta]


class ResumenPorFechaNacionalResponse(BaseModel):
    existeEstadoCuenta: bool
    resumen: Resumen
    proximosPeriodos: ProximosPeriodos
    seccionOperaciones: SeccionOperaciones
    seccionProductosServiciosVoluntarios: dict | None
    seccionCargosImpuestosAbonos: SeccionOperaciones
    seccionComprasEnCuotas: dict | None
