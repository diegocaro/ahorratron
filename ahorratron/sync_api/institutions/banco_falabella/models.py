"""Bank-side models for Banco Falabella (checking + CMR)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from ahorratron.sync_api.utils.constants import CHILE_TZ

DATE_FORMAT = "%d/%m/%Y"


def currency_to_float(value: str | None) -> float | None:
    """Convert Chilean currency string ($1.234.567) to float."""
    if value is None:
        return None
    cleaned = (
        value.replace("$", "")
        .replace(".", "")
        .replace(" ", "")
        .replace("\xa0", "")
        .replace(",", "")
        .strip()
    )
    if not cleaned or cleaned == "-":
        return None
    neg = cleaned.startswith("-") or (
        cleaned.startswith("(") and cleaned.endswith(")")
    )
    cleaned = cleaned.strip("-").strip("()")
    if not cleaned:
        return None
    amount = float(cleaned)
    return -amount if neg else amount


class ProductType(StrEnum):
    CHECKING = "checking"
    CREDIT_CARD = "credit_card"
    OTHER = "other"


class ProductItem(BaseModel):
    id: str
    name: str
    number: str
    type: ProductType
    balance: float = 0.0  # checking available / CMR cupo utilizado
    credit_limit: float | None = None
    available_credit: float | None = None


class ProductsResponse(BaseModel):
    products: list[ProductItem] = Field(default_factory=list)


class MovementTipo(StrEnum):
    CARGO = "cargo"
    ABONO = "abono"


class MovementStatus(StrEnum):
    POSTED = "posted"
    PENDING = "pending"


class MovementItem(BaseModel):
    id: str
    date: str  # DD/MM/YYYY
    description: str
    amount: float  # signed
    balance: float | None = None
    tipo: MovementTipo
    status: MovementStatus = MovementStatus.POSTED

    @property
    def datetime(self) -> datetime:
        return datetime.strptime(self.date, DATE_FORMAT).replace(tzinfo=CHILE_TZ)


class MovementsResponse(BaseModel):
    account_id: str
    movements: list[MovementItem] = Field(default_factory=list)
