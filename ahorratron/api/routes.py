import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends

from .auth import verify_api_key
from .models import Transaction, TransactionResponse
from .service import ActualBudgetService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    is_healty = True
    try:
        service = ActualBudgetService()
        if not service.health_check():
            is_healty = False
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        is_healty = False
    return {"status": "healthy" if is_healty else "unhealthy"}


@router.post("/add_transaction", response_model=TransactionResponse)
async def add_transaction(
    transaction: Transaction, api_key: str = Depends(verify_api_key)
) -> TransactionResponse:
    logger.info(f"Processing transaction: {transaction}")
    service = ActualBudgetService()
    transaction_id = service.add_transaction(transaction)
    logger.info(f"Successfully added transaction with ID: {transaction_id}")
    return TransactionResponse(
        success=True,
        message="Transaction added successfully",
        transaction_id=transaction_id,
    )


@router.get("/summary", response_model=dict)
async def get_summary(
    month: Optional[date] = None,
    api_key: str = Depends(verify_api_key),
):

    service = ActualBudgetService()
    return service.get_summary(month)
