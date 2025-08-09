import datetime
import json
import os

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from jose import jwe

from ahorratron.sync_api.connectors import get_connector
from ahorratron.sync_api.models.account_models import AccountsResponse

app = FastAPI()

SECRET_KEY = bytes.fromhex(os.environ["JWE_SECRET_KEY"])  # Must be 32 bytes for A256GCM
TOKEN_DURATION = datetime.timedelta(hours=12)
JWE_ALGORITHM = "A256GCM"


# Generate encrypted JWT (JWE) from a dictionary
def create_encrypted_token(data: dict) -> bytes:
    if not isinstance(data, dict):
        raise ValueError("Input data must be a dictionary.")
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        raise ValueError(
            "Both 'username' and 'password' are required in the token data."
        )
    payload = data.copy()
    payload["sub"] = username
    payload["exp"] = int(
        (datetime.datetime.now(datetime.UTC) + TOKEN_DURATION).timestamp()
    )
    encrypted_token = jwe.encrypt(
        json.dumps(payload), SECRET_KEY, algorithm=JWE_ALGORITHM
    )
    return encrypted_token


# Dependency to get current user and password from encrypted token
def get_decrypted_token(x_api_key: str = Header(..., alias="X-API-KEY")):
    try:
        decrypted = jwe.decrypt(x_api_key, SECRET_KEY)
        if decrypted is None:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        payload = json.loads(decrypted.decode())
        exp = payload.get("exp")
        if exp and datetime.datetime.now(datetime.UTC).timestamp() > exp:
            raise HTTPException(status_code=401, detail="Token expired")
        username = payload.get("username")
        password = payload.get("password")
        if not username or not password:
            raise HTTPException(
                status_code=401, detail="Invalid token: missing username or password"
            )
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@app.post("/auth")
async def auth(request: Request):
    data = await request.json()
    data["connector_id"] = "banco_de_chile"  # fixed connector for now
    try:
        token = create_encrypted_token(data)
        return {"apiKey": token}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/accounts", response_model=AccountsResponse)
def get_accounts(itemId: str, user_data: dict = Depends(get_decrypted_token)):
    connector = get_connector(user_data["connector_id"], user_data)
    response = connector.get_accounts(itemId=itemId)
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
