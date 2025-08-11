import datetime
import json
import os

from fastapi import Header, HTTPException
from jose import jwe, jwt

from ahorratron.sync_api.models.core_models import SessionData

SECRET_KEY = bytes.fromhex(os.environ["JWE_SECRET_KEY"])  # Must be 32 bytes for A256GCM
TOKEN_DURATION = datetime.timedelta(hours=12)
JWE_ALGORITHM = "A256GCM"

JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
JWT_ALGORITHM = "HS256"  # Or RS256 if you want asymmetric signing


# Generate encrypted JWT (JWE) from a dictionary
def create_encrypted_token(data: SessionData) -> str:
    enc_payload = data.model_dump()
    enc_token = jwe.encrypt(
        json.dumps(enc_payload), SECRET_KEY, algorithm=JWE_ALGORITHM
    )
    enc_token_str = enc_token.decode() if isinstance(enc_token, bytes) else enc_token

    payload = {
        "enc_token": enc_token_str,
        "exp": int((datetime.datetime.now(datetime.UTC) + TOKEN_DURATION).timestamp()),
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


# Dependency to get current user and password from encrypted token
def get_decrypted_token(x_api_key: str = Header(..., alias="X-API-KEY")) -> SessionData:
    try:
        # Decode JWT
        payload = jwt.decode(x_api_key, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
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
