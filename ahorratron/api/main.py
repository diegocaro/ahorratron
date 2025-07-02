"""FastAPI application for ahorratron"""

import logging

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from .models import ErrorResponse
from .routes import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ahorratron API",
    description="API for processing Apple Pay transactions and integrating with Actual Budget",
    version="0.1.0",
)
app.include_router(router)


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


def run_server():
    """Run the API server using uvicorn."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run_server()
