import re
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
            # Remove all non-digit, non-separator characters (e.g., currency symbols, spaces)
            v = re.sub(r"[^\d,\.]", "", v)
            # Case 1: Both '.' and ',' present (e.g., '1.234.567,89' or '1,234,567.89')
            if "." in v and "," in v:
                # If ',' is after the last '.', assume '.' is thousands and ',' is decimal (e.g., '1.234.567,89' -> 1234567.89)
                if v.rfind(",") > v.rfind("."):
                    v = v.replace(".", "")  # remove all thousands separators
                    v = v.replace(",", ".")  # convert decimal separator to '.'
                else:
                    # If '.' is after the last ',', assume ',' is thousands and '.' is decimal (e.g., '1,234,567.89' -> 1234567.89)
                    v = v.replace(",", "")  # remove all thousands separators
            # Case 2: Only ',' present (e.g., '1234,56')
            elif "," in v:
                v = v.replace(",", ".")  # treat ',' as decimal separator
            # Case 3: Multiple '.' present (e.g., '1.234.567')
            elif v.count(".") > 1:
                v = v.replace(".", "")  # treat all as thousands separators
            # Case 4: Single '.' present (e.g., '16.870')
            elif v.count(".") == 1:
                parts = v.split(".")
                # If only one dot and three digits after, treat as thousands (e.g., '16.870' -> 16870)
                if len(parts) == 2 and len(parts[1]) == 3:
                    v = "".join(parts)
                # Otherwise, treat as decimal (default float conversion)
            try:
                return float(v)
            except ValueError as exc:
                raise ValueError(f"Invalid amount: {v}") from exc
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
