import logging
from datetime import datetime
from functools import cached_property
from zoneinfo import ZoneInfo

from ahorratron.sync_api.core.connector import ConnectorBase
from ahorratron.sync_api.institutions.banco_de_chile.models import (
    GetCartolaCuentaRequest,
    GetCartolaResponse,
    Movimiento,
    ObtenerProductosResponse,
    Producto,
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
    DEFAULT_TIMEZONE = "America/Santiago"
    DATE_FORMAT_MOVIMIENTO_CARTOLA = "%Y%m%d %H:%M:%S"
    DATE_FORMAT_HORA_CONSULTA = "%d/%m/%Y %H:%M"

    def __init__(self, client: APIClient):
        self._client = client

        self._cache = {}

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

    @cached_property
    def _productos(self) -> ObtenerProductosResponse:
        return self._client.get_productos()

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

        if self._cache.get(cuenta.id):
            return self._cache[cuenta.id]
        cartola = self._client.get_cartola(request)
        self._cache[cuenta.id] = cartola
        return cartola

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
        # example: 20250730 16:44:29
        dt = datetime.strptime(movimiento.fecha, self.DATE_FORMAT_MOVIMIENTO_CARTOLA)
        dt_local = dt.replace(tzinfo=ZoneInfo(self.DEFAULT_TIMEZONE))

        # can be "cargo" or "abono"
        if movimiento.tipo == "cargo":
            transaction_type = TransactionType.DEBIT
        elif movimiento.tipo == "abono":
            transaction_type = TransactionType.CREDIT
        else:
            logger.error(f"Unknown transaction type: {movimiento.tipo}")
            return None

        monto = abs(float(movimiento.monto))
        if movimiento.tipo == "cargo":
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
            date=dt_local.isoformat(),
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
        type_map = {
            "cuenta": (AccountType.BANK, AccountSubtype.CHECKING_ACCOUNT),
            # "ahorro": (AccountType.BANK, AccountSubtype.SAVINGS_ACCOUNT),
            # "tarjeta": (AccountType.CREDIT, AccountSubtype.CREDIT_CARD),
        }
        tipo_info = type_map.get(producto.tipo)
        if tipo_info is None:
            logger.warning(
                f"Unknown account type: '{producto.tipo} for product {producto.codigo}"
            )
            return None
        account_type, account_subtype = tipo_info

        numero = producto.numero
        if producto.tipo == "tarjeta":
            numero = producto.mascara

        cartola = self._get_cartola_raw(producto)

        bank_data = BankData(
            transferNumber=numero,
            closingBalance=cartola.saldoDisponible,
            automaticallyInvestedBalance=0,
        )
        updated_at = datetime.strptime(
            cartola.horaConsulta.replace(" Hrs.", ""), self.DATE_FORMAT_HORA_CONSULTA
        )
        updated_at_local = updated_at.replace(tzinfo=ZoneInfo(self.DEFAULT_TIMEZONE))
        # dt_utc_iso = dt_local.astimezone(ZoneInfo("UTC")).isoformat()
        return Account(
            id=producto.id,
            type=account_type,
            subtype=account_subtype,
            number=numero,
            name=producto.label,
            currencyCode=producto.codigoMoneda,
            itemId=itemId,
            balance=cartola.saldoFinal,  # This can also be cartola.saldoDisponible, not sure which one is the best
            bankData=bank_data,
            updatedAt=updated_at_local.isoformat(),
        )
