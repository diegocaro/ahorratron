from datetime import datetime

import pytest
from pydantic import ValidationError

from ahorratron.api.models import Transaction


@pytest.mark.parametrize(
    "amount,expected_amount",
    [
        (1234.0, 1234.0),
        ("$16.870", 16870.0),
        ("$1,234.56", 1234.56),
        ("$1,234,444.56", 1234444.56),
        ("$1.234.231", 1234231.0),
        ("$1.234.231,56", 1234231.56),
    ],
)
def test_transaction_valid_amounts(amount: str | float, expected_amount: float):
    data = {
        "amount": amount,
        "date": "2025-07-11T22:40:59-04:00",
        "payee": "Tus Mascotas",
        "notes": "Apple Pay",
    }
    tx = Transaction(**data)
    assert tx.amount == expected_amount
    assert tx.payee == "Tus Mascotas"
    assert tx.notes == "Apple Pay"
    assert isinstance(tx.date, datetime)


def test_transaction_empty_payee_and_notes():
    data = {
        "amount": 100.0,
        "date": "2025-07-12T13:44:32-04:00",
        "payee": "",
        "notes": "here is a note",
    }
    with pytest.raises(ValidationError):
        Transaction(**data)


def test_transaction_invalid_amount_type():
    data = {
        "amount": "notanumber",
        "date": "2025-07-11T20:46:52-04:00",
        "payee": "Express de Lider",
        "notes": "Apple Pay",
    }
    with pytest.raises(ValidationError):
        Transaction(**data)  # type: ignore[arg-type]


def test_transaction_missing_required_fields():
    data = {
        "amount": 10.0,
        "payee": "Test",
        # missing date
    }
    with pytest.raises(ValidationError):
        Transaction(**data)
