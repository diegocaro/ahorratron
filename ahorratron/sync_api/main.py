import logging
from collections.abc import Awaitable, Callable

import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, Response

from ahorratron.sync_api.models.account_models import Account, AccountsResponse
from ahorratron.sync_api.models.core_models import SessionData, UserData
from ahorratron.sync_api.models.transaction_models import TransactionsResponse
from ahorratron.sync_api.service import Service
from ahorratron.sync_api.utils.token import create_encrypted_token, get_decrypted_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI()


@app.middleware("http")
async def log_request_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    body: bytes = await request.body()
    logger.info(
        "Incoming request: %s %s | Headers: %s | Body: %s",
        request.method,
        request.url.path,
        dict(request.headers),
        body.decode("utf-8") if body else None,
    )
    response: Response = await call_next(request)
    return response


@app.post("/auth")
async def auth(request: UserData):
    data = SessionData(user_data=request)
    try:
        token = create_encrypted_token(data)
        logger.debug(f"Generated token: {token}")
        return {"apiKey": token}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/accounts", response_model=AccountsResponse)
def get_accounts(
    itemId: str,
    background_tasks: BackgroundTasks,
    session_data: SessionData = Depends(get_decrypted_token),
):
    logger.debug(f"Session data: {session_data}")
    response = Service(background_tasks).get_accounts(session_data.user_data, itemId)
    logger.debug(f"Accounts response: {response}")
    return response


@app.get("/accounts/{accountId}", response_model=Account)
def get_account_by_id(
    accountId: str,
    background_tasks: BackgroundTasks,
    session_data: SessionData = Depends(get_decrypted_token),
):
    response = Service(background_tasks).get_account_by_id(
        session_data.user_data, accountId
    )
    logger.debug(f"Account detail response: {response}")
    return response


@app.get("/transactions", response_model=TransactionsResponse)
def get_transactions(
    accountId: str,
    background_tasks: BackgroundTasks,
    session_data: SessionData = Depends(get_decrypted_token),
):
    response = Service(background_tasks).get_transactions(
        session_data.user_data, accountId
    )
    logger.info(f"Transactions response: {response}")
    return response


@app.get("/protected")
def protected_route(user_data: dict = Depends(get_decrypted_token)):
    return {
        "message": f"Hello, {user_data['username']}. Your password is securely encrypted in the token.",
        "data": user_data,
    }


def run_server():
    """Run the API server using uvicorn."""

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run_server()
