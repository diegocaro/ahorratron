import datetime
import json
import logging
import os
from typing import Awaitable, Callable

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from jose import jwe, jwt

from ahorratron.sync_api.connectors import get_connector
from ahorratron.sync_api.models.account_models import Account, AccountsResponse
from ahorratron.sync_api.models.core_models import SessionData, UserData
from ahorratron.sync_api.models.transaction_models import TransactionsResponse

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

SECRET_KEY = bytes.fromhex(os.environ["JWE_SECRET_KEY"])  # Must be 32 bytes for A256GCM
TOKEN_DURATION = datetime.timedelta(hours=12)
JWE_ALGORITHM = "A256GCM"

JWT_SECRET = "test_jwt_secret"  # os.environ["JWT_SECRET_KEY"]  # TODO: UPDATE THIGS and use a separate secret for JWT signing
JWT_ALGORITHM = "HS256"  # Or RS256 if you want asymmetric signing

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


# Generate encrypted JWT (JWE) from a dictionary
def create_encrypted_token(data: SessionData) -> str:
    exp = int((datetime.datetime.now(datetime.UTC) + TOKEN_DURATION).timestamp())
    enc_payload = data.model_dump()
    enc_payload["exp"] = exp
    enc_token = jwe.encrypt(
        json.dumps(enc_payload), SECRET_KEY, algorithm=JWE_ALGORITHM
    )
    enc_token_str = enc_token.decode() if isinstance(enc_token, bytes) else enc_token

    payload = {"enc_token": enc_token_str, "exp:": exp}
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


# Dependency to get current user and password from encrypted token
def get_decrypted_token(x_api_key: str = Header(..., alias="X-API-KEY")) -> SessionData:
    try:
        # Decode JWT
        payload = jwt.decode(x_api_key, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        exp = payload.get("exp")
        if exp and datetime.datetime.now(datetime.UTC).timestamp() > exp:
            raise HTTPException(status_code=401, detail="Token expired")
        enc_token = payload.get("enc_token")
        if not enc_token:
            raise HTTPException(status_code=401, detail="Missing encrypted token")
        # Decrypt the encrypted token
        decrypted = jwe.decrypt(enc_token, SECRET_KEY)
        if decrypted is None:
            raise HTTPException(status_code=401, detail="Invalid encrypted token")
        session_data = SessionData.model_validate_json(decrypted.decode())
        return session_data
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


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
def get_accounts(itemId: str, session_data: SessionData = Depends(get_decrypted_token)):
    print(f"Session data: {session_data}")
    connector = get_connector(session_data.user_data)
    response = connector.get_accounts(itemId=itemId)
    logger.debug(f"Accounts response: {response}")
    return response


@app.get("/accounts/{accountId}", response_model=Account)
def get_account_by_id(
    accountId: str, session_data: SessionData = Depends(get_decrypted_token)
):
    connector = get_connector(session_data.user_data)
    response = connector.get_account_by_id(accountId=accountId)
    logger.debug(f"Account detail response: {response}")
    return response


@app.get("/transactions", response_model=TransactionsResponse)
def get_transactions(
    accountId: str, session_data: SessionData = Depends(get_decrypted_token)
):
    connector = get_connector(session_data.user_data)
    response = connector.get_transactions(accountId=accountId)
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
