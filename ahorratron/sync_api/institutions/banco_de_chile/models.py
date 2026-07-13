import zoneinfo
from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel

from ahorratron.sync_api.utils.helpers import to_utc

DATE_FORMAT_MOVIMIENTO_CARTOLA = "%Y%m%d %H:%M:%S"
DATE_FORMAT_HORA_CONSULTA = "%d/%m/%Y %H:%M"
DATE_FORMAT_NO_FACTURADO = "%d/%m/%Y %H:%M:%S"
DATE_FORMAT_CUENTA_AHORRO_MOVIMIENTO = "%Y%m%d"
DATE_FORMAT_CUENTA_AHORRO_CARTOLA = "%d/%m/%Y"
DATE_REPLACE_STRING = " Hrs."


CHILE_TZ = zoneinfo.ZoneInfo("America/Santiago")


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
class ProductoTipo(StrEnum):
    CUENTA = "cuenta"
    CUENTA_CORRIENTE_MONEDA_LOCAL = "cuentaCorrienteMonedaLocal"
    AHORRO = "ahorro"
    LINEA = "linea"
    TARJETA = "tarjeta"
    SEGURO = "seguro"
    PAGO_AUTOMATICO = "pagoAutomatico"
    CREDITO_CONSUMO = "creditoConsumo"


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


class OrigenTransaccionTipo(StrEnum):
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
    def is_pending(self) -> bool:
        # las transcciones pendientes tienen una hora de autorizacion igual
        # a la hora en que se hizo la compra, extraño, pero bueno...
        return self.horaAutorizacion != "00:00:00"

    @property
    def fecha_transaccion_iso(self) -> datetime:
        # example: 30/07/2025 16:44:29
        return datetime.strptime(
            f"{self.fechaTransaccionString} {self.horaAutorizacion}",
            DATE_FORMAT_NO_FACTURADO,
        )

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

    @property
    def is_prepago(self) -> bool:
        return ".PREPAGO:" in self.glosaTransaccion.upper()


class NoFacturadosResponse(BaseModel):
    tarjetaHabiente: str
    fechaFacturacionAnterior: int
    fechaAhora: int
    fechaFacturacionAnteriorString: str
    fechaAhoraString: str
    fechaProximaFacturacionCalendario: str
    listaMovNoFactur: list[MovimientoNoFacturado]


class MovimientoTipo(StrEnum):
    CARGO = "cargo"
    ABONO = "abono"


class Movimiento(BaseModel):
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
    def fecha_isoformat(self) -> datetime:
        # example input: 20250730 16:44:29
        # example output: 2025-07-30T20:44:29+00:00
        return to_utc(datetime.strptime(self.fecha, DATE_FORMAT_MOVIMIENTO_CARTOLA))


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
    def hora_consulta_iso(self) -> datetime:
        return to_utc(
            datetime.strptime(
                self.horaConsulta.replace(DATE_REPLACE_STRING, ""),
                DATE_FORMAT_HORA_CONSULTA,
            )
        )


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
    def fecha_consulta_iso(self) -> datetime:
        # There is a bug in Actual Budget where it mishandles timezones
        dt = datetime.fromtimestamp(self.fechaConsulta // 1000, tz=CHILE_TZ)
        return dt.replace(tzinfo=None)


class GrupoTipo(StrEnum):
    PAGOS = "pagos"
    AVANCES_COMPRAS = "avancesCompras"
    GENERICO = "generico"
    CUOTAS = "cuotas"


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
    def fecha_transaccion_iso(self) -> datetime | None:
        if self.fechaTransaccion is None:
            return None
        # There is a bug in Actual Budget where it mishandles timezones
        dt = datetime.fromtimestamp(self.fechaTransaccion // 1000, tz=CHILE_TZ)
        return dt.replace(tzinfo=None)


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


class CuentaAhorroRequest(BaseModel):
    numeroCuenta: str
    # fechaDesde: str  # "%d/%m/%Y", opcional
    # fechaHasta: str  # "%d/%m/%Y", opcional


class MovimientoCuentaAhorro(BaseModel):
    tipo: str
    glosa: str
    monto: float
    fechaContable: str
    fechaEfectiva: str
    indicadorPosteo: str
    oficinaOrigen: str
    correlativoTransaccion: str
    codigoAgrupacion: str
    codigoTransaccion: str
    registro1: str
    registro2: str
    registro3: str
    registro4: str
    registro5: str
    registro6: str
    registro7: str
    registro8: str
    registro9: str

    @property
    def id_fake(self) -> str:
        fields = [
            self.tipo,
            self.codigoAgrupacion,
            self.codigoTransaccion,
            self.fechaEfectiva,
            self.fechaContable,
            self.oficinaOrigen,
            self.registro1,
            self.registro2,
            self.registro3,
            self.registro4,
            self.registro5,
            self.registro6,
            self.registro7,
            self.registro8,
            self.registro9,
            str(self.monto),
        ]
        return "-".join(fields)

    @property
    def fecha_contable_iso(self) -> datetime:
        return datetime.strptime(
            self.fechaContable, DATE_FORMAT_CUENTA_AHORRO_MOVIMIENTO
        )

    @property
    def fecha_efectiva_iso(self) -> datetime:
        return datetime.strptime(
            self.fechaEfectiva, DATE_FORMAT_CUENTA_AHORRO_MOVIMIENTO
        )


class CuentaAhorroResponse(BaseModel):
    listaMovimientos: list[MovimientoCuentaAhorro]
    codigoRetorno: str
    rutCliente: str
    numeroProducto: str
    saldoDisponible: float
    retencion1Dia: str
    retencion2Dia: str
    retencionMas2Dia: str
    girosRealizados: str | None = None
    girosPermitidos: str
    fechaProxCapInt: str
    fechaUltimaCartola: str
    fechaProximaLiquidReajustes: str

    @property
    def fecha_ultima_cartola_iso(self) -> datetime:
        return datetime.strptime(
            self.fechaUltimaCartola, DATE_FORMAT_CUENTA_AHORRO_CARTOLA
        )
