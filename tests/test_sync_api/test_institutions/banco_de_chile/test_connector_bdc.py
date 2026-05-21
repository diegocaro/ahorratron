from datetime import datetime
from unittest.mock import MagicMock

import pytest

from ahorratron.sync_api.institutions.banco_de_chile.banco_de_chile import APIClient
from ahorratron.sync_api.institutions.banco_de_chile.connector import (
    BancoDeChileConnector,
)
from ahorratron.sync_api.models.transaction_models import (
    Merchant,
    Transaction,
    TransactionStatus,
    TransactionType,
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
