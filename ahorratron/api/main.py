"""FastAPI application for ahorratron"""

import logging
from typing import Optional

from fastapi import Depends, FastAPI, status
from fastapi.responses import JSONResponse

from .auth import verify_api_key
from .models import ErrorResponse, Transaction, TransactionResponse
from .service import ActualBudgetService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ahorratron API",
    description="API for processing Apple Pay transactions and integrating with Actual Budget",
    version="0.1.0",
)


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            message=str(exc), error_code="INTERNAL_ERROR"
        ).model_dump(),
    )


@app.get("/health")
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


@app.post("/add_transaction", response_model=TransactionResponse)
async def add_transaction(
    transaction: Transaction, api_key: str = Depends(verify_api_key)
) -> TransactionResponse:
    logger.info(f"Processing transaction for payee: {transaction}")
    service = ActualBudgetService()
    transaction_id = service.add_transaction(transaction)
    logger.info(f"Successfully added transaction with ID: {transaction_id}")
    return TransactionResponse(
        success=True,
        message="Transaction added successfully",
        transaction_id=transaction_id,
    )


@app.get("/transactions", response_model=list[dict])
async def get_transactions(
    account: Optional[str] = None, api_key: str = Depends(verify_api_key)
):
    service = ActualBudgetService()
    transactions = service.get_transactions(account)
    return transactions


def run_server():
    """Run the API server using uvicorn."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run_server()
