"""FastAPI application for ahorratron"""

import logging
from collections.abc import Awaitable, Callable

import uvicorn
from fastapi import FastAPI, Request, Response, status
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
async def log_request_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    body: bytes = await request.body()
    logger.info(
        "Incoming request: %s %s | Body: %s",
        request.method,
        request.url.path,
        body.decode("utf-8") if body else None,
    )
    response: Response = await call_next(request)
    return response


app.include_router(router)


@app.exception_handler(Exception)
async def general_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.error("Unexpected error: %s", str(exc))
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

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run_server()
