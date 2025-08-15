import json

from ahorratron.sync_api.institutions.banco_de_chile.banco_de_chile import APIClient
from ahorratron.sync_api.institutions.banco_de_chile.connector import (
    BancoDeChileConnector,
)
from ahorratron.sync_api.institutions.banco_de_chile.models import (
    GetCartolaCuentaRequest,
    GetCartolaResponse,
    MovimientosNoFacturadosRequest,
    NoFacturadosResponse,
    ObtenerProductosResponse,
)
from ahorratron.sync_api.models.core_models import UserData


class BancoDeChileDemoConnector(BancoDeChileConnector):
    @classmethod
    def from_user_data(cls, user_data: UserData) -> "BancoDeChileDemoConnector":
        client = DemoAPIClient("", "")
        return cls(client)


class DemoAPIClient(APIClient):
    def get_productos(self, incluirTarjetas: bool = True) -> ObtenerProductosResponse:
        parsed = json.load(
            open("tests/test_sync_api/test_institutions/data/productos.json")
        )
        return ObtenerProductosResponse.model_validate(parsed)

    def get_no_facturados(
        self, data: MovimientosNoFacturadosRequest
    ) -> NoFacturadosResponse:
        parsed = json.load(
            open("tests/test_sync_api/test_institutions/data/no_facturados.json")
        )
        return NoFacturadosResponse.model_validate(parsed)

    def get_cartola(self, data: GetCartolaCuentaRequest) -> GetCartolaResponse:
        parsed = json.load(
            open("tests/test_sync_api/test_institutions/data/cartola.json")
        )
        return GetCartolaResponse.model_validate(parsed)
