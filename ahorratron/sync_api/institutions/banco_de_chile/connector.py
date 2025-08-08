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


class BancoDeChileConnector:
    def __init__(self, client: APIClient):
        self._client = client

    def get_accounts(self, itemId: str) -> AccountsResponse:

        productos = self._client.get_productos()
        cuentas = [
            self._map_account_producto(itemId, productos, c)
            for c in productos.productos
        ]
        response = AccountsResponse(
            results=cuentas,
            total=len(cuentas),
        )
        return response

    def _map_account_producto(
        self, itemId: str, response: ObtenerProductosResponse, producto: Producto
    ) -> Account:
        numero = producto.numero
        if producto.tipo == "cuenta":
            account_type = AccountType.BANK
            account_subtype = AccountSubtype.CHECKING_ACCOUNT
        elif producto.tipo == "ahorro":
            account_type = AccountType.BANK
            account_subtype = AccountSubtype.SAVINGS_ACCOUNT
        elif producto.tipo == "tarjeta":
            account_type = AccountType.CREDIT
            account_subtype = AccountSubtype.CREDIT_CARD
            numero = producto.mascara
        else:
            raise ValueError(f"Unknown account type: {producto.tipo}")

        return Account(
            id=producto.codigo,
            type=account_type,
            subtype=account_subtype,
            number=numero,
            name=response.nombre,
            currencyCode=producto.codigoMoneda,
            itemId=itemId,
            balance=0.0,  # Balance is not provided in the response
        )
