import json
from datetime import datetime
from pathlib import Path

import httpx
import pytest

from ahorratron.sync_api.institutions.banco_de_chile.banco_de_chile import APIClient
from ahorratron.sync_api.institutions.banco_de_chile.models import (
    CuentaAhorroRequest,
    CuentaAhorroResponse,
    FechasFacturacionResponse,
    GetCartolaCuentaRequest,
    GetCartolaResponse,
    GetSaldoResponse,
    MovimientosNoFacturadosRequest,
    NoFacturadosResponse,
    ObtenerProductosResponse,
    ResumenNacionalResponse,
)

TEST_DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def productos_data():
    with open(TEST_DATA_DIR / "productos.json") as f:
        return json.load(f)


@pytest.fixture
def no_facturados_data():
    with open(TEST_DATA_DIR / "no_facturados.json") as f:
        return json.load(f)


@pytest.fixture
def cartola_data():
    with open(TEST_DATA_DIR / "cartola.json") as f:
        return json.load(f)


@pytest.fixture
def saldo_data():
    with open(TEST_DATA_DIR / "saldo.json") as f:
        return json.load(f)


@pytest.fixture
def resumen_nacional_data():
    with open(TEST_DATA_DIR / "resumen_nacional.json") as f:
        return json.load(f)


@pytest.fixture
def fechas_facturacion_data():
    with open(TEST_DATA_DIR / "fechas_facturacion.json") as f:
        return json.load(f)


@pytest.fixture
def cuenta_ahorro_data():
    with open(TEST_DATA_DIR / "cuenta_ahorro.json") as f:
        return json.load(f)


def test_validate_productos_data(productos_data):
    productos = ObtenerProductosResponse.model_validate(productos_data)
    assert productos.rut
    assert len(productos.productos) > 0


def test_validate_no_facturados_data(no_facturados_data):
    no_facturados = NoFacturadosResponse.model_validate(no_facturados_data)
    assert no_facturados.tarjetaHabiente
    assert isinstance(no_facturados.listaMovNoFactur, list)

    assert len(no_facturados.listaMovNoFactur) > 0
    m = no_facturados.listaMovNoFactur[0]
    expected_date = datetime.fromisoformat("2025-08-04T10:05:21")
    assert expected_date == m.fecha_transaccion_iso

    expected_fake_id = "3344-0-04/08/2025-10:05:21-12.45"
    assert expected_fake_id == m.id_fake


def test_validate_cartola_data(cartola_data):
    cartola = GetCartolaResponse.model_validate(cartola_data)
    assert cartola.horaConsulta
    assert isinstance(cartola.movimientos, list)

    expected_date = datetime.fromisoformat("2025-08-05T18:48:00")
    assert expected_date == cartola.hora_consulta_iso

    assert len(cartola.movimientos) > 0
    m = cartola.movimientos[0]
    expected_date = datetime.fromisoformat("2025-08-04T15:40:35")
    assert expected_date == m.fecha_isoformat


def test_validate_saldo_data(saldo_data):
    saldo = GetSaldoResponse.model_validate(saldo_data)
    assert saldo.cupoTotalNacional >= 0
    assert saldo.cupoUtilizadoNacional >= 0

    expected_date = datetime.fromisoformat("2025-08-15T20:10:22")
    assert expected_date == saldo.fecha_consulta_iso


def test_validate_resumen_nacional_data(resumen_nacional_data):
    resumen = ResumenNacionalResponse.model_validate(resumen_nacional_data)
    assert isinstance(resumen.seccionOperaciones.transaccionesTarjetas, list)
    transacciones = resumen.seccionOperaciones.transaccionesTarjetas
    assert len(transacciones) > 0

    t = transacciones[0]
    expected_date = datetime.fromisoformat("2025-06-28T00:00:00")
    assert expected_date == t.fecha_transaccion_iso


def test_validate_fechas_facturacion_data(fechas_facturacion_data):
    fechas = FechasFacturacionResponse.model_validate(fechas_facturacion_data)
    assert fechas.numeroCuenta
    assert len(fechas.listaNacional) > 0


def test_validate_cuenta_ahorro_data(cuenta_ahorro_data):
    cuenta_ahorro = CuentaAhorroResponse.model_validate(cuenta_ahorro_data)
    assert len(cuenta_ahorro.listaMovimientos) > 0


@pytest.fixture
def api_client():
    client = APIClient("username", "password")
    return client


def test_get_productos(api_client, productos_data):
    def mock_send(request, *args, **kwargs):
        return httpx.Response(200, json=productos_data)

    transport = httpx.MockTransport(mock_send)
    api_client._session = httpx.Client(transport=transport)

    productos = api_client.get_productos(incluirTarjetas=True)
    assert isinstance(productos, ObtenerProductosResponse)
    assert len(productos.productos) > 0


def test_get_no_facturados(api_client, no_facturados_data, productos_data):
    def mock_send(request, *args, **kwargs):
        return httpx.Response(200, json=no_facturados_data)

    transport = httpx.MockTransport(mock_send)
    api_client._session = httpx.Client(transport=transport)

    productos = ObtenerProductosResponse.model_validate(productos_data)
    tarjeta = next(p for p in productos.productos if p.tipo == "tarjeta")
    data = {
        "idTarjeta": tarjeta.id,
        "codigoProducto": tarjeta.codigo,
        "tipoTarjeta": tarjeta.descripcionLogo,
        "mascara": tarjeta.mascara,
        "nombreTitular": tarjeta.tarjetaHabiente,
        "tipoCliente": tarjeta.tipoCliente,
    }
    request = MovimientosNoFacturadosRequest.model_validate(data)

    no_facturados = api_client.get_no_facturados(request)
    assert isinstance(no_facturados, NoFacturadosResponse)
    assert no_facturados.tarjetaHabiente


def test_get_cartola(api_client, cartola_data, productos_data):
    def mock_send(request, *args, **kwargs):
        return httpx.Response(200, json=cartola_data)

    transport = httpx.MockTransport(mock_send)
    api_client._session = httpx.Client(transport=transport)

    productos = ObtenerProductosResponse.model_validate(productos_data)
    cuenta = next(p for p in productos.productos if p.tipo == "cuenta")
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

    cartola = api_client.get_cartola(request)
    assert isinstance(cartola, GetCartolaResponse)
    assert cartola.horaConsulta
    assert isinstance(cartola.movimientos, list)


def test_get_cuenta_ahorro(api_client, cuenta_ahorro_data, productos_data):
    def mock_send(request, *args, **kwargs):
        return httpx.Response(200, json=cuenta_ahorro_data)

    transport = httpx.MockTransport(mock_send)
    api_client._session = httpx.Client(transport=transport)

    productos = ObtenerProductosResponse.model_validate(productos_data)
    cuenta = next(p for p in productos.productos if p.tipo == "ahorro")
    data = {
        "numeroCuenta": cuenta.numero,
    }
    request = CuentaAhorroRequest.model_validate(data)

    cuenta_ahorro = api_client.get_cuenta_ahorro(request)
    assert isinstance(cuenta_ahorro, CuentaAhorroResponse)
    assert len(cuenta_ahorro.listaMovimientos) > 0
