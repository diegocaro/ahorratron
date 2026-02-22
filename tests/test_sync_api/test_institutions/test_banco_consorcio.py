import json
from pathlib import Path

import httpx
import pytest

from ahorratron.sync_api.institutions.banco_consorcio.banco_consorcio import (
    BancoConsorcioAPI,
    decrypt,
    encrypt,
)
from ahorratron.sync_api.institutions.banco_consorcio.models import (
    MovementsResponse,
    MovimientoTipo,
    NoFacturadosResponse,
    ProductsResponse,
)

TEST_DATA_DIR = Path(__file__).parent / "data" / "banco-consorcio"


def enc(data: dict) -> dict:
    return {"encryptedData": encrypt(data)}


@pytest.fixture
def no_facturados_data():
    with open(TEST_DATA_DIR / "no_facturados.json") as f:
        return json.load(f)


@pytest.fixture
def movements_data():
    with open(TEST_DATA_DIR / "movements.json") as f:
        return json.load(f)


@pytest.fixture
def productos_data():
    with open(TEST_DATA_DIR / "productos.json") as f:
        return json.load(f)


def test_validate_productos_data(productos_data):
    productos = ProductsResponse.model_validate(productos_data)
    assert isinstance(productos.products, list)
    assert len(productos.products) > 0


def test_validate_no_facturados_data(no_facturados_data):
    no_facturados = NoFacturadosResponse.model_validate(no_facturados_data)
    assert no_facturados.codigo
    assert isinstance(no_facturados.bodyResponse.tarjetas, list)

    assert len(no_facturados.bodyResponse.tarjetas) > 0
    # Here we need to assert transactions
    # m = no_facturados.bodyResponse.tarjetas[0]
    # expected_date = datetime.fromisoformat("2025-08-04T10:05:21")
    # assert expected_date == m.fecha_transaccion_iso

    # expected_fake_id = "3344-0-04/08/2025-10:05:21-12.45"
    # assert expected_fake_id == m.id_fake


def test_validate_movements_data(movements_data):
    movements = MovementsResponse.model_validate(movements_data)
    assert movements.dtoResponseCodigosEstadoHttp.codigo == "200"
    first_detalle = movements.dtoResponseSetResultados[0].detalle[0]
    assert first_detalle.tipo in [MovimientoTipo.ABONO, MovimientoTipo.CARGO]


@pytest.fixture
def api_client():
    client = BancoConsorcioAPI("username", "password")
    return client


def test_get_no_facturados(api_client, no_facturados_data):
    def mock_send(request, *args, **kwargs):
        return httpx.Response(200, json=no_facturados_data)

    transport = httpx.MockTransport(mock_send)
    api_client._session = httpx.Client(transport=transport)

    no_facturados = api_client.get_no_facturados()
    assert isinstance(no_facturados, NoFacturadosResponse)
    assert no_facturados.codigo == "200"
    assert len(no_facturados.bodyResponse.tarjetas) > 0


def test_get_movements(api_client, movements_data):
    def mock_send(request, *args, **kwargs):
        return httpx.Response(200, json=enc(movements_data))

    transport = httpx.MockTransport(mock_send)
    api_client._session = httpx.Client(transport=transport)

    movements = api_client.get_movements("1234567890")
    assert isinstance(movements, MovementsResponse)
    assert movements.dtoResponseCodigosEstadoHttp.codigo == "200"
    assert len(movements.dtoResponseSetResultados) > 0


def test_encrypt_decrypt_roundtrip():
    original_data = {"key": "value", "number": 123}
    encrypted = encrypt(original_data)
    decrypted = decrypt(encrypted)
    assert json.loads(decrypted) == original_data


def test_handle_response_with_encryption(api_client):
    test_data = {"key": "value"}
    encrypted_data = encrypt(test_data)

    def mock_send(request, *args, **kwargs):
        return httpx.Response(200, json={"encryptedData": encrypted_data})

    api_client._session = httpx.Client(transport=httpx.MockTransport(mock_send))
    response = api_client._session.get("http://test.com")

    result = api_client._handle_response(response, decrypt=True)
    assert result == test_data


def test_handle_response_without_encryption(api_client):
    test_data = {"key": "value"}

    def mock_send(request, *args, **kwargs):
        return httpx.Response(200, text=json.dumps(test_data))

    api_client._session = httpx.Client(transport=httpx.MockTransport(mock_send))
    response = api_client._session.get("http://test.com")

    result = api_client._handle_response(response, decrypt=False)
    assert result == test_data


def test_encrypt_param(api_client):
    param = "test_param"
    encrypted = api_client._encrypt_param(param)
    assert isinstance(encrypted, str)
    assert len(encrypted) > 0
    assert encrypted != param


def test_parse_session_storage(api_client):
    session_storage = [["token", "test_token"], ["user_id", "123"]]
    parsed = api_client._parse_session_storage(session_storage)
    assert parsed == {"token": "test_token", "user_id": "123"}
