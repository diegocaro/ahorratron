import base64
import json
import logging

from pydantic import BaseModel, model_validator

logger = logging.getLogger(__name__)


class UserData(BaseModel, frozen=True):
    clientId: str
    clientSecret: str
    connector_id: str = "banco_de_chile"

    @model_validator(mode="before")
    @classmethod
    def parse_connector_id(cls, data):
        if isinstance(data, dict) and "clientId" in data:
            client_id = data["clientId"]
            if ";" in client_id:
                connector_id, real_client_id = client_id.split(";", 1)
                data["connector_id"] = connector_id
                data["clientId"] = real_client_id
        return data

    def __str__(self) -> str:
        return f"UserData(clientId={self.clientId}, connector_id={self.connector_id})"


class AuthRequest(BaseModel):
    """Raw auth request from the client (Actual Budget / Pluggy.ai)."""

    clientId: str
    clientSecret: str


def parse_multi_credentials(client_id: str, client_secret: str) -> list[UserData]:
    """Parse credentials into a list of UserData for one or more institutions.

    Supports two formats:

    1. **Multi-bank (base64 JSON)**::

        clientId:     base64({"banco_de_chile": "12345678-9", "banco_consorcio": "98765432-1"})
        clientSecret: base64({"banco_de_chile": "pass1", "banco_consorcio": "pass2"})

    2. **Single-bank (legacy)**::

        clientId:     "banco_de_chile;12345678-9"   (or just "12345678-9")
        clientSecret: "password"
    """
    try:
        ids = json.loads(base64.b64decode(client_id))
        secrets = json.loads(base64.b64decode(client_secret))
        if isinstance(ids, dict) and isinstance(secrets, dict):
            users: list[UserData] = []
            for connector_id, rut in ids.items():
                if connector_id not in secrets:
                    raise ValueError(
                        f"Missing password for institution '{connector_id}'"
                    )
                users.append(
                    UserData(
                        clientId=rut,
                        clientSecret=secrets[connector_id],
                        connector_id=connector_id,
                    )
                )
            if not users:
                raise ValueError("No institutions found in credentials")
            logger.info(
                "Parsed multi-bank credentials for: %s",
                [u.connector_id for u in users],
            )
            return users
    except (json.JSONDecodeError, UnicodeDecodeError, Exception) as exc:
        logger.debug("Not multi-bank format (%s), falling back to single-bank", exc)

    # Fallback: single institution (old format — connector_id;rut or just rut)
    return [UserData(clientId=client_id, clientSecret=client_secret)]


class SessionData(BaseModel, frozen=True):
    exp: int | None = None
    # Legacy field kept for backward-compatible token deserialization
    user_data: UserData | None = None
    users: list[UserData] = []

    @model_validator(mode="before")
    @classmethod
    def _migrate_legacy(cls, data):
        """If an old-format token has ``user_data`` but no ``users``, migrate it."""
        if isinstance(data, dict):
            if "user_data" in data and not data.get("users"):
                ud = data["user_data"]
                if ud is not None:
                    data["users"] = [ud]
        return data
