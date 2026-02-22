import logging
from datetime import date, datetime

from cachetools import TTLCache

import ahorratron.sync_api.utils.constants as c
from ahorratron.sync_api.core.connector import ConnectorBase
from ahorratron.sync_api.institutions.banco_consorcio.models import (
    DetalleItem,
    MovementsResponse,
    MovimientoTipo,
    ProductItem,
    ProductoNombreTipo,
    ProductsResponse,
)
from ahorratron.sync_api.models.account_models import (
    Account,
    AccountsResponse,
    AccountSubtype,
    AccountType,
)
from ahorratron.sync_api.models.transaction_models import (
    Merchant,
    Transaction,
    TransactionsResponse,
    TransactionStatus,
    TransactionType,
)

from .banco_consorcio import BancoConsorcioAPI

logger = logging.getLogger(__name__)


class BancoConsorcioConnector(ConnectorBase):
    def __init__(self, client: BancoConsorcioAPI):
        self._client = client
        self._cache = TTLCache(maxsize=100, ttl=60)

    def get_accounts(self, itemId: str) -> AccountsResponse:
        productos = self._productos
        cuentas = [self._map_account_producto(itemId, p) for p in productos.products]
        cuentas = [c for c in cuentas if c is not None]
        response = AccountsResponse(
            results=cuentas,
            total=len(cuentas),
            totalPages=1,
            page=1,
        )
        return response

    def get_account_by_id(self, accountId: str) -> Account:
        productos = self._productos
        producto = next(
            (p for p in productos.products if p.numeroCuenta == accountId), None
        )
        if not producto:
            raise ValueError(f"Account with id {accountId} not found")

        response = self._map_account_producto("not_needed_now", producto)
        if response is None:
            raise ValueError(f"Error mapping account with id {accountId}")
        return response

    def get_transactions(self, accountId: str) -> TransactionsResponse:
        productos = self._productos
        producto = next(
            (p for p in productos.products if p.numeroCuenta == accountId), None
        )
        if not producto:
            logger.warning(f"Account with id {accountId} not found in productos")
            return TransactionsResponse(results=[], total=0, totalPages=0, page=0)

        # Get movements for the account
        movements = self._client.get_movements(producto.numeroCuenta)
        transactions = self._map_transactions_from_movements(movements, producto)

        return TransactionsResponse(
            results=transactions,
            total=len(transactions),
            totalPages=1,
            page=1,
        )

    @property
    def _productos(self) -> ProductsResponse:
        key = "productos"
        if key not in self._cache:
            logger.info("Fetching productos from API")
            self._cache[key] = self._client.get_products()
        else:
            logger.info("Using cached productos")
        return self._cache[key]

    def _map_account_producto(
        self, itemId: str, producto: ProductItem
    ) -> Account | None:
        if producto.nombreProducto == ProductoNombreTipo.CUENTA_CORRIENTE:
            return self._map_account_producto_cuenta_corriente(itemId, producto)
        else:
            logger.warning(
                f"Unsupported product type: {producto.nombreProducto}, code {producto.codigoProducto}"
            )
            return None

    def _map_account_producto_cuenta_corriente(
        self, itemId: str, producto: ProductItem
    ) -> Account:
        return Account(
            id=producto.numeroCuenta,
            type=AccountType.BANK,
            subtype=AccountSubtype.CHECKING_ACCOUNT,
            number=producto.numeroCuenta,
            name=producto.nombreCuenta,
            currencyCode=c.CLP,
            itemId=itemId,
            balance=0.0,  # Not provided
            bankData=None,
            updatedAt=datetime.now(),
        )

    def _map_transactions_from_movements(
        self, movements: MovementsResponse, producto: ProductItem
    ) -> list[Transaction]:
        transactions = []
        for resultado in movements.dtoResponseSetResultados:
            for detalle in resultado.detalle:
                transaction = self._map_transaction_detalle(
                    detalle, resultado.date, producto
                )
                if transaction is not None:
                    transactions.append(transaction)
        return transactions

    def _map_transaction_detalle(
        self, detalle: DetalleItem, day: date, producto: ProductItem
    ) -> Transaction | None:
        # Parse the amount and determine transaction type
        monto = detalle.monto_float

        if detalle.tipo == MovimientoTipo.CARGO:
            transaction_type = TransactionType.DEBIT
            if monto > 0:
                monto = -monto
        elif detalle.tipo == MovimientoTipo.ABONO:
            transaction_type = TransactionType.CREDIT
            monto = abs(monto)
        else:
            logger.warning(f"Unknown transaction type: {detalle.tipo}")
            return None

        return Transaction(
            id=detalle.identificador,
            date=datetime.combine(day, detalle.time),
            amount=monto,
            description=detalle.descripcion,
            accountId=producto.numeroCuenta,
            type=transaction_type,
            currencyCode=c.CLP,
            status=TransactionStatus.POSTED,
            merchant=Merchant(name=detalle.descripcion),
        )
