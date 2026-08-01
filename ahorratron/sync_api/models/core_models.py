import logging

from pydantic import BaseModel, Field, model_validator

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


class SessionData(BaseModel, frozen=True):
    exp: int | None = None
    # Legacy field kept for backward-compatible token deserialization
    user_data: UserData | None = None
    users: list[UserData] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _migrate_legacy(cls, data):
        """If an old-format token has ``user_data`` but no ``users``, migrate it."""
        if isinstance(data, dict) and "user_data" in data and not data.get("users"):
            ud = data["user_data"]
            if ud is not None:
                data["users"] = [ud]
        return data
