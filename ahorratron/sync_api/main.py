import logging
from collections.abc import Awaitable, Callable

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, Response

from ahorratron.sync_api.config import LOG_LEVEL
from ahorratron.sync_api.core.credentials import parse_multi_credentials
from ahorratron.sync_api.models.account_models import Account, AccountsResponse
from ahorratron.sync_api.models.core_models import AuthRequest, SessionData
from ahorratron.sync_api.models.transaction_models import TransactionsResponse
from ahorratron.sync_api.service import Service
from ahorratron.sync_api.utils.token import create_encrypted_token, get_decrypted_token

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


app = FastAPI()


@app.middleware("http")
async def log_request_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    body: bytes = await request.body()
    logger.info("Incoming request: %s %s", request.method, request.url.path)
    logger.debug(
        "Headers: %s | Body: %s",
        dict(request.headers),
        body.decode("utf-8") if body else None,
    )
    response: Response = await call_next(request)
    return response


@app.post("/auth")
async def auth(request: AuthRequest):
    users = parse_multi_credentials(request.clientId, request.clientSecret)
    data = SessionData(users=users)
    try:
        token = create_encrypted_token(data)
        return {"apiKey": token}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/accounts", response_model=AccountsResponse)
async def get_accounts(
    itemId: str,
    session_data: SessionData = Depends(get_decrypted_token),
):
    response = Service().get_accounts(session_data.users, itemId)
    logger.debug(f"Accounts response: {response}")
    return response


@app.get("/accounts/{accountId}", response_model=Account)
async def get_account_by_id(
    accountId: str,
    session_data: SessionData = Depends(get_decrypted_token),
):
    response = Service().get_account_by_id(session_data.users, accountId)
    logger.debug(f"Account detail response: {response}")
    return response


@app.get("/transactions", response_model=TransactionsResponse)
async def get_transactions(
    accountId: str,
    session_data: SessionData = Depends(get_decrypted_token),
):
    response = Service().get_transactions(session_data.users, accountId)
    # logger.debug(f"Transactions response: {response}")
    return response


@app.get("/protected")
def protected_route(session_data: SessionData = Depends(get_decrypted_token)):
    institutions = [u.connector_id for u in session_data.users]
    return {
        "message": f"Hello! Connected to {len(session_data.users)} institution(s): {', '.join(institutions)}",
    }


def run_server():
    """Run the API server using uvicorn."""

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run_server()
