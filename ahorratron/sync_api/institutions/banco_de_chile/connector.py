import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from cachetools import TTLCache

import ahorratron.sync_api.utils.constants as c
from ahorratron.sync_api.core.connector import ConnectorBase
from ahorratron.sync_api.institutions.banco_de_chile.models import (
    CuentaAhorroRequest,
    CuentaAhorroResponse,
    GetCartolaCuentaRequest,
    GetCartolaResponse,
    GetSaldoResponse,
    GrupoTipo,
    Movimiento,
    MovimientoCuentaAhorro,
    MovimientoNoFacturado,
    MovimientosNoFacturadosRequest,
    MovimientoTipo,
    NoFacturadosResponse,
    ObtenerProductosResponse,
    OrigenTransaccionTipo,
    Producto,
    ProductoTipo,
    ResumenNacionalResponse,
    ResumenPorFechaRequest,
    TransaccionTarjeta,
)
from ahorratron.sync_api.models.account_models import (
    Account,
    AccountsResponse,
    AccountSubtype,
    AccountType,
    BankData,
)
from ahorratron.sync_api.models.transaction_models import (
    Merchant,
    Transaction,
    TransactionsResponse,
    TransactionStatus,
    TransactionType,
)

from .banco_de_chile import APIClient

logger = logging.getLogger(__name__)

"""
Documentation from Pluggy.ai
- https://docs.pluggy.ai/docs/accounts
- https://docs.pluggy.ai/reference/accounts-list
- https://www.postman.com/pluggy-official/pluggy-public/collection/wrl8bhb/pluggy

"""


class BancoDeChileConnector(ConnectorBase):
    def __init__(self, client: APIClient):
        self._client = client

        self._cache = TTLCache(maxsize=100, ttl=60)

    def get_accounts(self, itemId: str) -> AccountsResponse:
        cuentas = [
            self._map_account_producto(itemId, c) for c in self._productos.productos
        ]
        cuentas = [c for c in cuentas if c is not None]
        response = AccountsResponse(
            results=cuentas,
            total=len(cuentas),
            totalPages=1,  # Assuming all accounts fit in one page
            page=1,  # Default to first page
        )
        return response

    def get_account_by_id(self, accountId: str) -> Account:
        producto = next(
            (p for p in self._productos.productos if p.id == accountId), None
        )
        if not producto:
            raise ValueError(f"Account with id {accountId} not found")

        response = self._map_account_producto("not_needed_now", producto)
        if response is None:
            raise ValueError(f"Error mapping account with id {accountId}")
        return response

    def get_transactions(self, accountId: str) -> TransactionsResponse:
        producto = next(
            (p for p in self._productos.productos if p.id == accountId), None
        )
        if not producto:
            logger.warning(f"Account with id {accountId} not found in productos")
            return TransactionsResponse(results=[], total=0, totalPages=0, page=0)

        if producto.tipo == "cuenta":
            transactions = self._get_transactions_cartola(producto)
        elif producto.tipo == "tarjeta":
            transactions = self._get_transactions_tarjeta_credito(producto)
        elif producto.tipo == "ahorro":
            transactions = self._get_transactions_cuenta_ahorro(producto)
        else:
            raise NotImplementedError(
                f"Transactions for account type '{producto.tipo}' are not supported"
            )

        return TransactionsResponse(
            results=transactions,
            total=len(transactions),
            totalPages=1,  # Assuming all transactions fit in one page
            page=1,  # Default to first page
        )

    @property
    def _productos(self) -> ObtenerProductosResponse:
        key = "productos"
        if key not in self._cache:
            logger.info("Fetching productos from API")
            self._cache[key] = self._client.get_productos()
        else:
            logger.info("Using cached productos")
        return self._cache[key]

    def _get_cartola_raw(self, cuenta: Producto) -> GetCartolaResponse:
        data = {
            "cuentaSeleccionada": {
                "nombreCliente": self._productos.nombre,
                "rutCliente": self._productos.rut,
                "numero": cuenta.numero,
                "mascara": cuenta.mascara,
                # "selected": True, # Opcional
                "codigoProducto": cuenta.codigo,
                "claseCuenta": cuenta.claseCuenta,
                "moneda": cuenta.codigoMoneda,
            },
            "cabecera": {"statusGenerico": True, "paginacionDesde": 1},
        }
        request = GetCartolaCuentaRequest.model_validate(data)
        cartola = self._client.get_cartola(request)
        return cartola

    def _get_no_facturados_raw(self, tarjeta: Producto) -> NoFacturadosResponse:
        data = {
            "idTarjeta": tarjeta.id,
            "codigoProducto": tarjeta.codigo,
            "tipoTarjeta": tarjeta.descripcionLogo,
            "mascara": tarjeta.mascara,
            "nombreTitular": tarjeta.tarjetaHabiente,
            "tipoCliente": tarjeta.tipoCliente,
        }
        request = MovimientosNoFacturadosRequest.model_validate(data)
        no_facturados = self._client.get_no_facturados(request)
        return no_facturados

    def _get_saldo_raw(self, tarjeta: Producto) -> GetSaldoResponse:
        data = {
            "idTarjeta": tarjeta.id,
            "codigoProducto": tarjeta.codigo,
            "tipoTarjeta": tarjeta.descripcionLogo,
            "mascara": tarjeta.mascara,
            "nombreTitular": tarjeta.tarjetaHabiente,
            "tipoCliente": tarjeta.tipoCliente,
        }
        request = MovimientosNoFacturadosRequest.model_validate(data)
        saldo = self._client.get_saldo(request)
        return saldo

    def _get_facturados_raw(self, tarjeta: Producto) -> ResumenNacionalResponse:
        data_fechas = {
            "idTarjeta": tarjeta.id,
            "codigoProducto": tarjeta.codigo,
            "tipoTarjeta": tarjeta.descripcionLogo,
            "mascara": tarjeta.mascara,
            "nombreTitular": tarjeta.tarjetaHabiente,
            "tipoCliente": tarjeta.tipoCliente,
        }
        request = MovimientosNoFacturadosRequest.model_validate(data_fechas)
        fechas_facturacion = self._client.get_fechas_facturacion(request)
        mes_mas_reciente = max(
            e.fechaFacturacion for e in fechas_facturacion.listaNacional
        ).isoformat()
        data = {
            "idTarjeta": tarjeta.id,
            "codigoProducto": tarjeta.codigo,
            "tipoTarjeta": tarjeta.descripcionLogo,
            "mascara": tarjeta.mascara,
            "nombreTitular": tarjeta.tarjetaHabiente,
            # "tipoCliente": tarjeta.tipoCliente,
            "fechaFacturacion": mes_mas_reciente,
            "numeroCuenta": fechas_facturacion.numeroCuenta,
        }
        request = ResumenPorFechaRequest.model_validate(data)
        return self._client.get_resumen_nacional(request)

    def _get_cuenta_ahorro_raw(self, tarjeta: Producto) -> CuentaAhorroResponse:
        data = {
            "numeroCuenta": tarjeta.numero,
        }
        request = CuentaAhorroRequest.model_validate(data)
        return self._client.get_cuenta_ahorro(request)

    def _get_transactions_cartola(self, cuenta: Producto) -> list[Transaction]:
        cartola = self._get_cartola_raw(cuenta)
        transactions = [
            self._map_transaction_movimiento(cartola, m) for m in cartola.movimientos
        ]
        transactions = [t for t in transactions if t is not None]
        return transactions

    def _map_transaction_movimiento(
        self, cartola: GetCartolaResponse, movimiento: Movimiento
    ) -> Transaction | None:
        if movimiento.tipo == MovimientoTipo.CARGO:
            transaction_type = TransactionType.DEBIT
        elif movimiento.tipo == MovimientoTipo.ABONO:
            transaction_type = TransactionType.CREDIT
        else:
            logger.error(f"Unknown transaction type: {movimiento.tipo}")
            return None

        monto = abs(float(movimiento.monto))
        if movimiento.tipo == MovimientoTipo.CARGO:
            monto = -monto

        if movimiento.estado is None:
            estado = TransactionStatus.POSTED
        else:
            logger.error(f"Unknown transaction status: {movimiento.estado}")
            return None

        # balance = None
        # try:
        #     balance = float(movimiento.saldo)
        # except ValueError:
        #     logger.error(
        #         f"Error parsing balance for transaction {movimiento.id}: {movimiento.saldo}"
        #     )

        return Transaction(
            id=movimiento.id,
            date=movimiento.fecha_isoformat,
            amount=monto,
            # balance=balance,
            description=movimiento.descripcion,
            accountId=movimiento.idCuenta,
            type=transaction_type,
            currencyCode=cartola.moneda,
            status=estado,
            merchant=Merchant(
                name=movimiento.descripcion,
            ),
        )

    def _map_account_producto(self, itemId: str, producto: Producto) -> Account | None:
        if producto.tipo == ProductoTipo.CUENTA:
            return self._map_account_producto_cuenta(itemId, producto)
        elif producto.tipo == ProductoTipo.TARJETA:
            return self._map_account_producto_tarjeta_credito(itemId, producto)
        elif producto.tipo == ProductoTipo.AHORRO:
            return self._map_account_producto_cuenta_ahorro(itemId, producto)
        else:
            logger.warning(
                f"Unknown account type: '{producto.tipo} for product {producto.codigo}"
            )
            return None

    def _map_account_producto_cuenta(self, itemId: str, producto: Producto) -> Account:
        cartola = self._get_cartola_raw(producto)

        bank_data = BankData(
            transferNumber=producto.numero,
            closingBalance=cartola.saldoDisponible,
            automaticallyInvestedBalance=0,
        )

        return Account(
            id=producto.id,
            type=AccountType.BANK,
            subtype=AccountSubtype.CHECKING_ACCOUNT,
            number=producto.numero,
            name=producto.label,
            currencyCode=producto.codigoMoneda,
            itemId=itemId,
            balance=cartola.saldoFinal,  # This can also be cartola.saldoDisponible, not sure which one is the best
            bankData=bank_data,
            updatedAt=cartola.hora_consulta_iso,
        )

    def _map_account_producto_tarjeta_credito(
        self, itemId: str, producto: Producto
    ) -> Account:
        saldo = self._get_saldo_raw(producto)

        return Account(
            id=producto.id,
            type=AccountType.CREDIT,
            subtype=AccountSubtype.CREDIT_CARD,
            number=producto.mascara,
            name=producto.label,
            currencyCode=producto.codigoMoneda,
            itemId=itemId,
            balance=saldo.cupoUtilizadoNacional,  # Actual will automatically set this as negative for credit cards
            bankData=None,  # No bank data for credit cards
            updatedAt=saldo.fecha_consulta_iso,
        )

    def _map_account_producto_cuenta_ahorro(
        self, itemId: str, producto: Producto
    ) -> Account:
        cartola = self._get_cuenta_ahorro_raw(producto)

        bank_data = BankData(
            transferNumber=producto.numero,
            closingBalance=cartola.saldoDisponible,
            automaticallyInvestedBalance=0,
        )
        return Account(
            id=producto.id,
            type=AccountType.BANK,
            subtype=AccountSubtype.SAVINGS_ACCOUNT,
            number=producto.numero,
            name=producto.label,
            currencyCode=producto.codigoMoneda,
            itemId=itemId,
            balance=cartola.saldoDisponible,  # This can also be cartola.saldoDisponible, not sure which one is the best
            bankData=bank_data,
            updatedAt=cartola.fecha_ultima_cartola_iso,
        )

    def _get_transactions_tarjeta_credito(self, tarjeta: Producto) -> list[Transaction]:
        no_facturados = self._get_no_facturados_raw(tarjeta)
        transactions = [
            self._map_transaction_no_facturado(movimiento, tarjeta)
            for movimiento in no_facturados.listaMovNoFactur
        ]

        facturados = self._get_facturados_raw(tarjeta)
        transactions += [
            self._map_transaction_facturado(facturados, movimiento)
            for movimiento in facturados.seccionOperaciones.transaccionesTarjetas
            + facturados.seccionCargosImpuestosAbonos.transaccionesTarjetas
        ]
        transactions = [t for t in transactions if t is not None]

        return transactions

    def _map_transaction_no_facturado(
        self, movimiento: MovimientoNoFacturado, tarjeta: Producto
    ) -> Transaction | None:
        if movimiento.origenTransaccion != OrigenTransaccionTipo.NAC:
            logger.warning(
                f"Skipping non-national transaction {movimiento.descripcionTransaccion} {movimiento.montoCompra}"
            )
            return None

        if movimiento.montoCompra > 0:
            transaction_type = TransactionType.DEBIT
        else:
            transaction_type = TransactionType.CREDIT

        return Transaction(
            id=movimiento.id_fake,
            date=movimiento.fecha_transaccion_iso,
            amount=movimiento.montoCompra,
            # balance=balance,
            description=movimiento.glosaTransaccion,
            accountId=movimiento.numeroTarjeta,
            type=transaction_type,
            currencyCode=c.CLP,
            status=TransactionStatus.PENDING,
            merchant=Merchant(name=movimiento.glosaTransaccion),
        )

    def _map_transaction_facturado(
        self,
        facturado: ResumenNacionalResponse,
        movimiento: TransaccionTarjeta,
        currency_code: str = c.CLP,
    ) -> Transaction | None:
        if movimiento.totales or not movimiento.idMovimiento:
            logger.warning(
                f"Skipping totals or invalid transaction {movimiento.descripcion} {movimiento.montoTransaccion}"
            )
            return None
        if not movimiento.fechaTransaccion or not movimiento.fecha_transaccion_iso:
            logger.error(f"Transaction has no date")
            return None

        if movimiento.grupo in [GrupoTipo.AVANCES_COMPRAS, GrupoTipo.GENERICO]:
            transaction_type = TransactionType.DEBIT
            monto = movimiento.montoTransaccion
        elif movimiento.grupo == GrupoTipo.PAGOS:
            transaction_type = TransactionType.CREDIT
            monto = -abs(movimiento.montoTransaccion)
        else:
            logger.error(f"Unknown transaction type: {movimiento.grupo}")
            return None

        return Transaction(
            id=movimiento.idMovimiento,
            date=movimiento.fecha_transaccion_iso,
            amount=monto,
            # balance=balance,
            description=movimiento.descripcion,
            accountId=movimiento.nombreTarjeta,
            type=transaction_type,
            currencyCode=currency_code,
            status=TransactionStatus.POSTED,
            merchant=Merchant(name=movimiento.descripcion),
        )

    def _map_transaction_cuenta_ahorro(
        self, cuenta_ahorro: CuentaAhorroResponse, movimiento: MovimientoCuentaAhorro
    ) -> Transaction:
        if movimiento.monto > 0:
            transaction_type = TransactionType.CREDIT
        else:
            transaction_type = TransactionType.DEBIT

        return Transaction(
            id=movimiento.codigoTransaccion,
            date=movimiento.fecha_efectiva_iso,
            amount=movimiento.monto,
            # balance=balance,
            description=movimiento.glosa,
            accountId=cuenta_ahorro.numeroProducto,
            type=transaction_type,
            currencyCode=c.CLP,
            status=TransactionStatus.POSTED,
            merchant=Merchant(name=movimiento.glosa),
        )

    def _get_transactions_cuenta_ahorro(self, cuenta: Producto) -> list[Transaction]:
        cuenta_ahorro = self._get_cuenta_ahorro_raw(cuenta)
        transactions = [
            self._map_transaction_cuenta_ahorro(cuenta_ahorro, m)
            for m in cuenta_ahorro.listaMovimientos
        ]
        transactions = [t for t in transactions if t is not None]
        return transactions
