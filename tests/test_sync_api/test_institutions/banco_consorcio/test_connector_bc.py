import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ahorratron.sync_api.institutions.banco_consorcio.banco_consorcio import (
    BancoConsorcioAPI,
)
from ahorratron.sync_api.institutions.banco_consorcio.connector import (
    BancoConsorcioConnector,
)
from ahorratron.sync_api.institutions.banco_consorcio.models import (
    MovementsResponse,
    ProductsResponse,
)
from ahorratron.sync_api.models.transaction_models import (
    TransactionStatus,
    TransactionType,
)

TEST_DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def productos_data():
    with open(TEST_DATA_DIR / "productos.json") as f:
        return json.load(f)


@pytest.fixture
def movements_data():
    with open(TEST_DATA_DIR / "movements.json") as f:
        return json.load(f)


@pytest.fixture
def no_facturados_data():
    with open(TEST_DATA_DIR / "no_facturados.json") as f:
        return json.load(f)


@pytest.fixture
def mock_client(productos_data, movements_data):
    client = MagicMock(spec=BancoConsorcioAPI)
    client.get_products.return_value = ProductsResponse.model_validate(productos_data)
    client.get_movements.return_value = MovementsResponse.model_validate(movements_data)
    return client


@pytest.fixture
def connector(mock_client):
    return BancoConsorcioConnector(mock_client)


class TestBancoConsorcioConnectorGetTransactions:
    def test_returns_transactions_for_valid_account(
        self, connector: BancoConsorcioConnector, mock_client
    ):
        response = connector.get_transactions(accountId="123123123")

        mock_client.get_movements.assert_called_once_with("123123123")
        assert response.next is None
        assert len(response.results) == 7

    def test_abono_is_credit_with_positive_amount(
        self, connector: BancoConsorcioConnector
    ):
        response = connector.get_transactions(accountId="123123123")

        abonos = [t for t in response.results if t.type == TransactionType.CREDIT]
        assert len(abonos) == 4
        assert all(t.amount > 0 for t in abonos)

    def test_cargo_is_debit_with_negative_amount(
        self, connector: BancoConsorcioConnector
    ):
        response = connector.get_transactions(accountId="123123123")

        cargos = [t for t in response.results if t.type == TransactionType.DEBIT]
        assert len(cargos) == 3
        assert all(t.amount < 0 for t in cargos)

    def test_all_transactions_are_posted(self, connector: BancoConsorcioConnector):
        response = connector.get_transactions(accountId="123123123")

        assert all(t.status == TransactionStatus.POSTED for t in response.results)

    def test_unknown_account_returns_empty(
        self, connector: BancoConsorcioConnector, mock_client
    ):
        response = connector.get_transactions(accountId="nonexistent")

        mock_client.get_movements.assert_not_called()
        assert response.next is None
        assert response.results == []
