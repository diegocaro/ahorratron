import json
import logging
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

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


class BancoDeChileConnector:
    DEFAULT_TIMEZONE = "America/Santiago"
    DATE_FORMAT_MOVIMIENTO_CARTOLA = "%Y%m%d %H:%M:%S"

    def __init__(self, client: APIClient):
        self._client = client

    def get_accounts(self, itemId: str) -> AccountsResponse:

        productos = self._client.get_productos()
        cuentas = [self._map_account_producto(itemId, c) for c in productos.productos]
        cuentas = [c for c in cuentas if c is not None]
        response = AccountsResponse(
            results=cuentas,
            total=len(cuentas),
            totalPages=1,  # Assuming all accounts fit in one page
            page=1,  # Default to first page
        )
        return response

    def get_account_by_id(self, accountId: str) -> Account:
        productos = self._client.get_productos()
        producto = next((p for p in productos.productos if p.id == accountId), None)
        if not producto:
            logger.warning(f"Account with id {accountId} not found in productos")
            raise ValueError(f"Account with id {accountId} not found")

        response = self._map_account_producto("not_needed_now", producto)
        if response is None:
            logger.warning(f"Error mapping account with id {accountId}")
            raise ValueError(f"Error mapping account with id {accountId}")
        return response

    def get_transactions(self, accountId: str) -> TransactionsResponse:
        productos = self._client.get_productos()
        producto = next((p for p in productos.productos if p.id == accountId), None)
        if not producto:
            logger.warning(f"Account with id {accountId} not found in productos")
            return TransactionsResponse(results=[], total=0, totalPages=0, page=0)

        if producto.tipo == "cuenta":
            transactions = self._get_transactions_cartola(productos, producto)
        else:
            logger.warning(
                f"Transactions for account type '{producto.tipo}' are not supported"
            )
            raise NotImplementedError(
                f"Transactions for account type '{producto.tipo}' are not supported"
            )

        return TransactionsResponse(
            results=transactions,
            total=len(transactions),
            totalPages=1,  # Assuming all transactions fit in one page
            page=1,  # Default to first page
        )

    def _get_transactions_cartola(
        self, productos: ObtenerProductosResponse, cuenta: Producto
    ) -> list[Transaction]:
        data = {
            "cuentaSeleccionada": {
                "nombreCliente": productos.nombre,
                "rutCliente": productos.rut,
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

        transactions = [
            self._map_transaction_movimiento(cartola, m) for m in cartola.movimientos
        ]
        transactions = [t for t in transactions if t is not None]
        return transactions

    def _map_transaction_movimiento(
        self, cartola: GetCartolaResponse, movimiento: Movimiento
    ) -> Optional[Transaction]:
        # example: 20250730 16:44:29
        dt = datetime.strptime(movimiento.fecha, self.DATE_FORMAT_MOVIMIENTO_CARTOLA)
        dt_local = dt.replace(tzinfo=ZoneInfo(self.DEFAULT_TIMEZONE))
        # dt_utc_iso = dt_local.astimezone(ZoneInfo("UTC")).isoformat()

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

        return Transaction(
            id=movimiento.id,
            date=dt_local.isoformat(),
            amount=monto,
            description=movimiento.descripcion,
            accountId=movimiento.idCuenta,
            type=transaction_type,
            currencyCode=cartola.moneda,
            status=estado,
        )

    def _map_account_producto(
        self, itemId: str, producto: Producto
    ) -> Optional[Account]:

        type_map = {
            "cuenta": (AccountType.BANK, AccountSubtype.CHECKING_ACCOUNT),
            "ahorro": (AccountType.BANK, AccountSubtype.SAVINGS_ACCOUNT),
            "tarjeta": (AccountType.CREDIT, AccountSubtype.CREDIT_CARD),
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

        bank_data = BankData(
            transferNumber=numero,
            closingBalance=0,
            automaticallyInvestedBalance=0,
        )

        return Account(
            id=producto.id,
            type=account_type,
            subtype=account_subtype,
            number=numero,
            name=producto.label,
            currencyCode=producto.codigoMoneda,
            itemId=itemId,
            balance=0.0,  # Fix this, get the balance from the transactions or cartola
            bankData=bank_data,
        )
