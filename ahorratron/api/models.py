"""
Pydantic models for API request/response validation.
"""
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ApplePayTransaction(BaseModel):
    """Model for Apple Pay transaction data."""
    date: str = Field(..., description="Transaction date in YYYY-MM-DD format")
    amount: float = Field(..., description="Transaction amount")
    merchant: str = Field(..., description="Merchant name")
    category: str = Field(..., description="Transaction category")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional Apple Pay metadata")


class TransactionResponse(BaseModel):
    """Response model for transaction operations."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    transaction_id: Optional[str] = Field(default=None, description="Generated transaction ID if successful")


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = Field(default=False, description="Always false for errors")
    message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(default=None, description="Error code for debugging")