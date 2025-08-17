from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel

DATE_FORMAT_MOVIMIENTO_CARTOLA = "%Y%m%d %H:%M:%S"
DATE_FORMAT_HORA_CONSULTA = "%d/%m/%Y %H:%M"
DATE_FORMAT_NO_FACTURADO = "%d/%m/%Y %H:%M:%S"
DATE_REPLACE_STRING = " Hrs."


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


class ResumenPorFechaRequest(BaseModel):
    idTarjeta: str
    codigoProducto: str
    tipoTarjeta: str
    mascara: str
    nombreTitular: str
    fechaFacturacion: str
    numeroCuenta: str


#### RESPONSES MODELS ####
class ProductoTipo(str, Enum):
    CUENTA = "cuenta"
    CUENTA_CORRIENTE_MONEDA_LOCAL = "cuentaCorrienteMonedaLocal"
    AHORRO = "ahorro"
    LINEA = "linea"
    TARJETA = "tarjeta"
    SEGURO = "seguro"
    PAGO_AUTOMATICO = "pagoAutomatico"


class Producto(BaseModel):
    id: str
    numero: str
    mascara: str
    codigo: str
    codigoMoneda: str
    alias: str | None
    label: str
    tipo: ProductoTipo
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


class OrigenTransaccionTipo(str, Enum):
    NAC = "NAC"
    INT = "INT"


class MovimientoNoFacturado(BaseModel):
    origenTransaccion: OrigenTransaccionTipo
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

    @property
    def fecha_transaccion_iso(self) -> str:
        # example: 30/07/2025 16:44:29
        return datetime.strptime(
            f"{self.fechaTransaccionString} {self.horaAutorizacion}",
            DATE_FORMAT_NO_FACTURADO,
        ).isoformat()

    @property
    def id_fake(self) -> str:
        fields = [
            self.numeroTarjeta,
            str(self.codigoComercioTBK),
            self.fechaTransaccionString,
            self.horaAutorizacion,
            str(self.montoCompra),
        ]
        return "-".join(fields)


class NoFacturadosResponse(BaseModel):
    tarjetaHabiente: str
    fechaFacturacionAnterior: int
    fechaAhora: int
    fechaFacturacionAnteriorString: str
    fechaAhoraString: str
    fechaProximaFacturacionCalendario: str
    listaMovNoFactur: list[MovimientoNoFacturado]


class MovimientoTipo(str, Enum):
    CARGO = "cargo"
    ABONO = "abono"


class Movimiento(BaseModel):
    estado: str | None
    descripcion: str
    monto: str
    saldo: str
    nombreCuenta: str
    numeroCuenta: str
    idCuenta: str
    canal: str
    tipo: MovimientoTipo
    fecha: str
    fechaContable: str
    id: str
    numeroDocumento: str
    fechaContableMovimiento: int
    detalleGlosa: list[str]

    @property
    def fecha_isoformat(self) -> str:
        # example: 20250730 16:44:29
        return datetime.strptime(self.fecha, DATE_FORMAT_MOVIMIENTO_CARTOLA).isoformat()


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

    @property
    def hora_consulta_iso(self) -> str:
        return datetime.strptime(
            self.horaConsulta.replace(DATE_REPLACE_STRING, ""),
            DATE_FORMAT_HORA_CONSULTA,
        ).isoformat()


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

    @property
    def fecha_consulta_iso(self) -> str:
        return datetime.fromtimestamp(self.fechaConsulta / 1000).isoformat()


class GrupoTipo(str, Enum):
    PAGOS = "pagos"
    AVANCES_COMPRAS = "avancesCompras"
    GENERICO = "generico"


class TransaccionTarjeta(BaseModel):
    numReferencia: str
    nombreTarjeta: str
    fechaTransaccion: int | None
    fechaTransaccionString: str | None
    montoTransaccion: float
    descripcion: str
    ciudad: str
    cuotas: str
    nombreTitular: str
    # comercio: Any
    # rubro: Any
    totales: bool
    grupo: GrupoTipo
    tituloTotales: str | None
    cambioTarjeta: bool
    aclaracion: dict
    idMovimiento: str | None
    # estado: Any
    # comprobanteSiebel: Any
    # fechaComprobanteSiebel: Any
    idComprobante: str

    @property
    def fecha_transaccion_iso(self) -> str | None:
        if self.fechaTransaccion is None:
            return None
        return datetime.fromtimestamp(self.fechaTransaccion).isoformat()


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


class ResumenNacionalResponse(BaseModel):
    existeEstadoCuenta: bool
    resumen: Resumen
    proximosPeriodos: ProximosPeriodos
    seccionOperaciones: SeccionOperaciones
    seccionProductosServiciosVoluntarios: dict | None
    seccionCargosImpuestosAbonos: SeccionOperaciones
    seccionComprasEnCuotas: dict | None


class ItemFechaFacturacion(BaseModel):
    fechaFacturacion: date  # es un string con formato %Y-%m-%d
    existeEstadoCuentaNacional: str
    existeEstadoCuentaInternacional: str


class FechasFacturacionResponse(BaseModel):
    mensaje: str
    existenEstadosDeCuenta: bool
    listaNacional: list[ItemFechaFacturacion]
    numeroCuenta: str
    listaInternacional: list[ItemFechaFacturacion]
