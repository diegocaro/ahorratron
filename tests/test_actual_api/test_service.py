from datetime import datetime
from unittest.mock import MagicMock

import pytest

from ahorratron.actual_api.models import Transaction
from ahorratron.actual_api.service import ActualBudgetService


def test_add_transaction_with_autospec(monkeypatch: pytest.MonkeyPatch):
    """Simplified test using monkeypatch instead of patch/autospec"""
    mock_actual = MagicMock()
    mock_actual.return_value.__enter__.return_value.session = MagicMock()
    mock_actual.return_value.__enter__.return_value.commit = MagicMock()
    monkeypatch.setattr("ahorratron.actual_api.service.Actual", mock_actual)

    mock_create_transaction = MagicMock()
    mock_create_transaction.return_value.id = "1234"
    monkeypatch.setattr(
        "ahorratron.actual_api.service.create_transaction", mock_create_transaction
    )

    mock_get_account = MagicMock()
    monkeypatch.setattr("ahorratron.actual_api.service.get_account", mock_get_account)

    service = ActualBudgetService()
    transaction = Transaction(
        date=datetime(2024, 1, 1), payee="Test Payee", notes="Test Notes", amount=1000
    )

    result = service.add_transaction(transaction)

    # Assert
    mock_get_account.assert_called_once()
    mock_create_transaction.assert_called_once()
    assert mock_create_transaction.call_args.kwargs["amount"] == -1000
    assert mock_create_transaction.call_args.kwargs["payee"] == "Pago:Test Payee"
    mock_actual.return_value.__enter__.return_value.commit.assert_called_once()
    assert result == "1234"
