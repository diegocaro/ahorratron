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
    docs_url="/api/docs",
)


@app.middleware("http")
async def log_request_middleware(request, call_next):
    body = await request.body()
    logger.info(
        f"Incoming request: {request.method} {request.url.path} | Body: {body.decode('utf-8') if body else None}"
    )
    response = await call_next(request)
    return response


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


# @app.exception_handler(RequestValidationError)
# async def log_validation_exception(request, exc: RequestValidationError):
#     logger.error(f"Validation error: {exc.errors()} | Body: {exc.body}")
#     raise exc


def run_server():
    """Run the API server using uvicorn."""
    import uvicorn  # ignore[import-outside-toplevel]

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run_server()
