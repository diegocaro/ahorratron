import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ahorratron.sync_api.institutions.banco_falabella.banco_falabella import (
    BancoFalabellaAPI,
)
from ahorratron.sync_api.institutions.banco_falabella.connector import (
    BancoFalabellaConnector,
)
from ahorratron.sync_api.institutions.banco_falabella.models import (
    MovementsResponse,
    MovementStatus,
    ProductsResponse,
    currency_to_float,
)
from ahorratron.sync_api.models.account_models import AccountSubtype, AccountType
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
def movements_cmr_data():
    with open(TEST_DATA_DIR / "movements_cmr.json") as f:
        return json.load(f)


@pytest.fixture
def mock_client(productos_data, movements_data, movements_cmr_data):
    client = MagicMock(spec=BancoFalabellaAPI)
    client.get_products.return_value = ProductsResponse.model_validate(productos_data)

    def _movements(account_id: str):
        if account_id == "1234":
            return MovementsResponse.model_validate(movements_cmr_data)
        return MovementsResponse.model_validate(movements_data)

    client.get_movements.side_effect = _movements
    return client


@pytest.fixture
def connector(mock_client):
    return BancoFalabellaConnector(mock_client)


class TestCurrencyToFloat:
    def test_chilean_format(self):
        assert currency_to_float("$651.011") == 651011.0
        assert currency_to_float("1.234") == 1234.0
        assert currency_to_float(None) is None


class TestBancoFalabellaConnectorAccounts:
    def test_get_accounts_includes_checking_and_cmr(
        self, connector: BancoFalabellaConnector
    ):
        response = connector.get_accounts(itemId="item-1")
        assert response.total == 2
        by_id = {a.id: a for a in response.results}
        assert by_id["10000000001"].subtype == AccountSubtype.CHECKING_ACCOUNT
        assert by_id["10000000001"].type == AccountType.BANK
        assert by_id["1234"].subtype == AccountSubtype.CREDIT_CARD
        assert by_id["1234"].type == AccountType.CREDIT
        assert by_id["1234"].balance == 500000.0
        assert by_id["1234"].owner == "1234"
        assert by_id["10000000001"].taxNumber == "10000000001"

    def test_get_account_by_id(self, connector: BancoFalabellaConnector):
        account = connector.get_account_by_id("10000000001")
        assert account.number == "10000000001"


class TestBancoFalabellaConnectorTransactions:
    def test_checking_transactions(
        self, connector: BancoFalabellaConnector, mock_client
    ):
        response = connector.get_transactions(accountId="10000000001")
        mock_client.get_movements.assert_called_with("10000000001")
        assert len(response.results) == 3

    def test_abono_is_credit(self, connector: BancoFalabellaConnector):
        response = connector.get_transactions(accountId="10000000001")
        credits = [t for t in response.results if t.type == TransactionType.CREDIT]
        assert len(credits) == 2
        assert all(t.amount > 0 for t in credits)

    def test_cargo_is_debit(self, connector: BancoFalabellaConnector):
        response = connector.get_transactions(accountId="10000000001")
        debits = [t for t in response.results if t.type == TransactionType.DEBIT]
        assert len(debits) == 1
        assert debits[0].amount < 0

    def test_cmr_pending_and_posted(self, connector: BancoFalabellaConnector):
        response = connector.get_transactions(accountId="1234")
        assert len(response.results) == 3
        by_desc = {t.description: t for t in response.results}
        assert by_desc["SUPERMERCADO"].status == TransactionStatus.PENDING
        assert by_desc["FARMACIA"].status == TransactionStatus.POSTED
        # Pluggy CREDIT: purchases positive, payments negative (Actual negates)
        assert by_desc["SUPERMERCADO"].amount == 15990.0
        assert by_desc["SUPERMERCADO"].type == TransactionType.DEBIT
        assert by_desc["FARMACIA"].amount == 8900.0
        assert by_desc["PAGO CMR"].amount == -50000.0
        assert by_desc["PAGO CMR"].type == TransactionType.CREDIT

    def test_unknown_account_empty(
        self, connector: BancoFalabellaConnector, mock_client
    ):
        response = connector.get_transactions(accountId="nonexistent")
        mock_client.get_movements.assert_not_called()
        assert response.results == []


class TestCmrInstallmentsInDescription:
    def test_format_installments(self):
        fmt = BancoFalabellaAPI._format_installments
        assert fmt("1/12") == "01/12"
        assert fmt("3 de 6") == "03/06"
        assert fmt("01 / 12") == "01/12"
        assert fmt("1/1") is None
        assert fmt("") is None
        assert fmt("sin cuotas") is None

    def test_row_appends_cuota_suffix(self):
        api = BancoFalabellaAPI("u", "p")
        mov = api._row_to_cmr_movement(
            {
                "date": "20/07/2026",
                "description": "COMPRA CUOTAS SIN INTERES MP *MERCADO LIBRE",
                "amount_str": "-15990",
                "installments": "1/12",
            },
            "1234",
            MovementStatus.PENDING,
        )
        assert mov is not None
        assert (
            mov.description
            == "COMPRA CUOTAS SIN INTERES MP *MERCADO LIBRE 01/12"
        )


class TestCheckingPeriodPick:
    def test_uses_newest_calendar_month(self):
        opts = [
            ("1", "Últimos movimientos"),
            ("2", "Mes en curso"),
            ("07/2026", "07/2026"),
            ("06/2026", "06/2026"),
        ]
        assert BancoFalabellaAPI._pick_checking_periods(opts, 1) == [
            ("07/2026", "07/2026")
        ]

    def test_extra_months_when_configured(self):
        opts = [
            ("1", "Últimos movimientos"),
            ("07/2026", "07/2026"),
            ("06/2026", "06/2026"),
        ]
        assert BancoFalabellaAPI._pick_checking_periods(opts, 2) == [
            ("07/2026", "07/2026"),
            ("06/2026", "06/2026"),
        ]

    def test_zero_still_scrapes_one_month(self):
        opts = [("2", "Mes en curso"), ("07/2026", "07/2026")]
        assert BancoFalabellaAPI._pick_checking_periods(opts, 0) == [
            ("07/2026", "07/2026")
        ]


class TestFactoryRegistration:
    def test_banco_falabella_registered(self):
        from ahorratron.sync_api.core.factory import CONNECTORS

        assert "banco_falabella" in CONNECTORS
        connector_cls, client_cls = CONNECTORS["banco_falabella"]
        assert connector_cls is BancoFalabellaConnector
        assert client_cls is BancoFalabellaAPI
