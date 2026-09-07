import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ahorratron.sync_api.institutions.banco_de_chile.banco_de_chile import APIClient
from ahorratron.sync_api.institutions.banco_de_chile.connector import (
    BancoDeChileConnector,
)
from ahorratron.sync_api.institutions.banco_de_chile.models import (
    GrupoTipo,
    NoFacturadosResponse,
    TransaccionTarjeta,
)
from ahorratron.sync_api.models.transaction_models import (
    Merchant,
    Transaction,
    TransactionStatus,
    TransactionType,
)

TEST_DATA_DIR = Path(__file__).parent / "data"


def make_transaccion_tarjeta(
    grupo: GrupoTipo,
    monto: float = 100.0,
    descripcion: str = "Compra en comercio",
    idMovimiento: str = "mov-1",
) -> TransaccionTarjeta:
    return TransaccionTarjeta(
        numReferencia="1",
        nombreTarjeta="Tarjeta Test",
        fechaTransaccion=1722366000000,
        fechaTransaccionString="30/07/2025",
        montoTransaccion=monto,
        descripcion=descripcion,
        ciudad="Santiago",
        cuotas="1/1",
        nombreTitular="Test",
        totales=False,
        grupo=grupo,
        tituloTotales=None,
        cambioTarjeta=False,
        aclaracion={},
        idMovimiento=idMovimiento,
        idComprobante="comp-1",
    )


def make_transaction(id: str, date: str, amount: float = -100.0) -> Transaction:
    return Transaction(
        id=id,
        date=datetime.fromisoformat(date),
        amount=amount,
        description="Test",
        accountId="acc-1",
        type=TransactionType.DEBIT,
        currencyCode="CLP",
        status=TransactionStatus.POSTED,
        merchant=Merchant(name="Test"),
    )


@pytest.fixture
def connector():
    client = MagicMock(spec=APIClient)
    return BancoDeChileConnector(client)


@pytest.mark.parametrize(
    "grupo,expected_type",
    [
        (GrupoTipo.AVANCES_COMPRAS, TransactionType.DEBIT),
        (GrupoTipo.GENERICO, TransactionType.DEBIT),
        (GrupoTipo.PAGOS, TransactionType.CREDIT),
    ],
)
def test_map_transaction_facturado_known_groups_are_not_dropped(
    connector, grupo, expected_type
):
    movimiento = make_transaccion_tarjeta(grupo=grupo)

    result = connector._map_transaction_facturado(MagicMock(), movimiento)

    assert result is not None
    assert result.type == expected_type


def test_map_transaction_facturado_cuotas_is_skipped(connector):
    movimiento = make_transaccion_tarjeta(grupo=GrupoTipo.CUOTAS)

    result = connector._map_transaction_facturado(MagicMock(), movimiento)

    assert result is None


def test_no_facturados_before_facturados_are_removed(connector):
    facturados = [
        make_transaction("f1", "2025-07-01"),  # inicio facturación
        make_transaction("f2", "2025-07-15"),
        make_transaction("f3", "2025-07-31"),  # fin de facturación
    ]
    no_facturados = [
        make_transaction("nf1", "2025-06-28"),  # drop: antes de inicio facturación
        make_transaction("nf2", "2025-07-01"),  # duplicado
        make_transaction("nf3", "2025-07-15"),  # duplicado
        make_transaction("nf4", "2025-07-31"),  # duplicado
        make_transaction("nf5", "2025-08-01"),  # el primer no facturado real!
    ]

    result = connector._deduplicate_tarjeta_credito_transactions(
        facturados, no_facturados
    )

    ids = [t.id for t in result]
    assert "nf1" not in ids  # dropped: before facturados window
    assert "nf2" not in ids
    assert "nf3" not in ids
    assert "nf4" not in ids
    assert "nf5" in ids
    assert "f1" in ids
    assert "f2" in ids


def test_empty_facturados_returns_all_no_facturados(connector):
    no_facturados = [
        make_transaction("nf1", "2025-06-01"),
        make_transaction("nf2", "2025-06-15"),
    ]

    result = connector._deduplicate_tarjeta_credito_transactions([], no_facturados)

    assert len(result) == 2
    ids = [t.id for t in result]
    assert "nf1" in ids
    assert "nf2" in ids


def test_empty_no_facturados_returns_only_facturados(connector):
    facturados = [
        make_transaction("f1", "2025-07-01"),
        make_transaction("f2", "2025-07-15"),
    ]

    result = connector._deduplicate_tarjeta_credito_transactions(facturados, [])

    assert len(result) == 2
    ids = [t.id for t in result]
    assert "f1" in ids
    assert "f2" in ids


def test_both_empty_returns_empty(connector):
    result = connector._deduplicate_tarjeta_credito_transactions([], [])
    assert result == []


@pytest.fixture
def no_facturados_response():
    with open(TEST_DATA_DIR / "no_facturados.json") as f:
        return NoFacturadosResponse.model_validate(json.load(f))


def test_identical_no_facturados_get_different_ids(connector, no_facturados_response):
    """Dos compras confirmadas en el mismo comercio, día y monto.

    Al confirmarse pierden la hora de autorización (queda en 00:00:00), así que
    todos los campos del movimiento son idénticos y el id_fake colisiona.
    """
    confirmado = next(
        m for m in no_facturados_response.listaMovNoFactur if not m.is_pending
    )
    no_facturados_response.listaMovNoFactur = [
        confirmado.model_copy(),
        confirmado.model_copy(),
    ]
    connector._get_no_facturados_raw = MagicMock(return_value=no_facturados_response)
    connector._get_facturados_raw = MagicMock(
        return_value=MagicMock(
            seccionOperaciones=MagicMock(transaccionesTarjetas=[]),
            seccionCargosImpuestosAbonos=MagicMock(transaccionesTarjetas=[]),
        )
    )

    result = connector._get_transactions_tarjeta_credito(MagicMock())

    assert len(result) == 2
    # el primero conserva el id base, el repetido queda numerado
    assert {t.id for t in result} == {confirmado.id_fake, f"{confirmado.id_fake}#2"}
