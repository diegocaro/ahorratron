from pydantic import BaseModel, model_validator


class UserData(BaseModel, frozen=True):
    clientId: str
    clientSecret: str
    connector_id: str = "banco_de_chile"

    def __str__(self) -> str:
        return f"UserData(clientId={self.clientId}, connector_id={self.connector_id})"


class SessionData(BaseModel, frozen=True):
    exp: int | None = None
    user_data: UserData
