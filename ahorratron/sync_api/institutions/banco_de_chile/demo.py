import json
from pathlib import Path

from ahorratron.sync_api.institutions.banco_de_chile.models import (
    GetCartolaCuentaRequest,
    GetCartolaResponse,
    GetSaldoResponse,
    MovimientosNoFacturadosRequest,
    NoFacturadosResponse,
    ObtenerProductosResponse,
)

DATADIR = Path("tests/test_sync_api/test_institutions/data")


class DemoAPIClient:
    def __init__(self, username: str, password: str) -> None:
        pass

    def get_productos(self, incluirTarjetas: bool = True) -> ObtenerProductosResponse:
        parsed = json.load(open(DATADIR / "productos.json"))
        return ObtenerProductosResponse.model_validate(parsed)

    def get_no_facturados(
        self, data: MovimientosNoFacturadosRequest
    ) -> NoFacturadosResponse:
        parsed = json.load(open(DATADIR / "no_facturados.json"))
        return NoFacturadosResponse.model_validate(parsed)

    def get_cartola(self, data: GetCartolaCuentaRequest) -> GetCartolaResponse:
        parsed = json.load(open(DATADIR / "cartola.json"))
        return GetCartolaResponse.model_validate(parsed)

    def get_saldo(self, data: MovimientosNoFacturadosRequest) -> GetSaldoResponse:
        parsed = json.load(open(DATADIR / "saldo.json"))
        return GetSaldoResponse.model_validate(parsed)
