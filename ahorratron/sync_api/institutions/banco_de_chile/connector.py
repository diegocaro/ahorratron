import logging
from typing import Optional

from ahorratron.sync_api.institutions.banco_de_chile.models import (
    ObtenerProductosResponse,
    Producto,
)
from ahorratron.sync_api.models.account_models import (
    Account,
    AccountsResponse,
    AccountSubtype,
    AccountType,
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
    def __init__(self, client: APIClient):
        self._client = client

    def get_accounts(self, itemId: str) -> AccountsResponse:

        productos = self._client.get_productos()
        cuentas = [
            self._map_account_producto(itemId, productos, c)
            for c in productos.productos
        ]
        cuentas = [c for c in cuentas if c is not None]
        response = AccountsResponse(
            results=cuentas,
            total=len(cuentas),
        )
        return response

    def _map_account_producto(
        self, itemId: str, response: ObtenerProductosResponse, producto: Producto
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

        return Account(
            id=producto.id,
            type=account_type,
            subtype=account_subtype,
            number=numero,
            name=producto.label,
            currencyCode=producto.codigoMoneda,
            itemId=itemId,
            balance=0.0,  # Balance is not provided in the response
        )
