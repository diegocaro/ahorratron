import json

from ahorratron.sync_api.institutions.banco_de_chile.models import (
    GetCartolaCuentaRequest,
    GetCartolaResponse,
    MovimientosNoFacturadosRequest,
    NoFacturadosResponse,
    ObtenerProductosResponse,
)


class DemoAPIClient:

    def login(self, username: str, password: str) -> None:
        pass

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
