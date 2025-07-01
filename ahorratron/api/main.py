"""
FastAPI application for ahorratron.
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import JSONResponse
import logging
from typing import Any

from .models import ApplePayTransaction, TransactionResponse, ErrorResponse
from .auth import verify_api_key
from ..actual_budget import actual_budget, ActualBudgetError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ahorratron API",
    description="API for processing Apple Pay transactions and integrating with Actual Budget",
    version="0.1.0"
)


@app.exception_handler(ActualBudgetError)
async def actual_budget_exception_handler(request, exc: ActualBudgetError):
    """Handle Actual Budget specific errors."""
    logger.error(f"Actual Budget error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            message=str(exc),
            error_code="ACTUAL_BUDGET_ERROR"
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            message="Internal server error",
            error_code="INTERNAL_ERROR"
        ).model_dump()
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post(
    "/add_transaction",
    response_model=TransactionResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        422: {"model": ErrorResponse, "description": "Validation Error"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def add_transaction(
    transaction: ApplePayTransaction,
    api_key: str = Depends(verify_api_key)
) -> TransactionResponse:
    """
    Add an Apple Pay transaction to the Actual Budget system.
    
    Args:
        transaction: Apple Pay transaction data
        api_key: Verified API key from X-API-KEY header
        
    Returns:
        TransactionResponse with success status and transaction ID
        
    Raises:
        HTTPException: For various error conditions
    """
    try:
        logger.info(f"Processing Apple Pay transaction for merchant: {transaction.merchant}")
        
        # Convert Apple Pay data to Actual Budget format
        actual_format = actual_budget.convert_apple_pay_to_actual_format(
            transaction.model_dump()
        )
        
        # Add transaction to Actual Budget
        transaction_id = actual_budget.add_transaction(actual_format)
        
        logger.info(f"Successfully added transaction with ID: {transaction_id}")
        
        return TransactionResponse(
            success=True,
            message="Transaction added successfully",
            transaction_id=transaction_id
        )
        
    except ActualBudgetError:
        # Re-raise to be handled by the exception handler
        raise
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid transaction data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error processing transaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process transaction"
        )


def run_server():
    """Run the API server using uvicorn."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)