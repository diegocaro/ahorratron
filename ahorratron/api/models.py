from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Transaction(BaseModel):
    account: str
    amount: float
    date: datetime
    payee: Optional[str] = None
    notes: Optional[str] = None
    model_config = ConfigDict(extra="allow")


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
