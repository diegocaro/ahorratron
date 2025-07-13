from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Transaction(BaseModel):
    amount: float
    date: datetime
    payee: str = Field(..., min_length=1)
    notes: Optional[str] = None
    model_config = ConfigDict(extra="allow")

    @field_validator("amount", mode="before")
    @classmethod
    def parse_amount(cls, v: float | str) -> float:
        if isinstance(v, str):
            v = v.replace("$", "").replace(".", "").replace(",", ".")
            try:
                return float(v)
            except ValueError:
                raise ValueError(f"Invalid amount: {v}")
        return float(v)


class TransactionResponse(BaseModel):
    """Response model for transaction operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    transaction_id: Optional[str] = Field(
        default=None, description="Generated transaction ID if successful"
    )


class ErrorResponse(BaseModel):
    """Error response model."""

    success: bool = Field(default=False, description="Always false for errors")
    message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(
        default=None, description="Error code for debugging"
    )
