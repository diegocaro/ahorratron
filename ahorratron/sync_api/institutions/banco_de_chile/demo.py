import json
from pathlib import Path

from ahorratron.sync_api.institutions.banco_de_chile.models import (
    CuentaAhorroRequest,
    CuentaAhorroResponse,
    GetCartolaCuentaRequest,
    GetCartolaResponse,
    GetSaldoResponse,
    MovimientosNoFacturadosRequest,
    NoFacturadosResponse,
    ObtenerProductosResponse,
)

DATADIR = Path("tests/test_sync_api/test_institutions/data")


class DemoAPIClient:
    # Implements a mock client that returns demo data from JSON files
    # using the APIClient interface
    def __init__(self, username: str, password: str) -> None:
        pass

    def get_productos(self, incluirTarjetas: bool = True) -> ObtenerProductosResponse:
        with open(DATADIR / "productos.json") as f:
            parsed = json.load(f)
        return ObtenerProductosResponse.model_validate(parsed)

    def get_no_facturados(
        self, data: MovimientosNoFacturadosRequest
    ) -> NoFacturadosResponse:
        with open(DATADIR / "no_facturados.json") as f:
            parsed = json.load(f)
        return NoFacturadosResponse.model_validate(parsed)

    def get_cartola(self, data: GetCartolaCuentaRequest) -> GetCartolaResponse:
        with open(DATADIR / "cartola.json") as f:
            parsed = json.load(f)
        return GetCartolaResponse.model_validate(parsed)

    def get_saldo(self, data: MovimientosNoFacturadosRequest) -> GetSaldoResponse:
        with open(DATADIR / "saldo.json") as f:
            parsed = json.load(f)
        return GetSaldoResponse.model_validate(parsed)

    def get_cuenta_ahorro(self, data: CuentaAhorroRequest) -> CuentaAhorroResponse:
        with open(DATADIR / "cuenta_ahorro.json") as f:
            parsed = json.load(f)
        return CuentaAhorroResponse.model_validate(parsed)
