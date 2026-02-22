from pydantic import BaseModel, model_validator


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


class SessionData(BaseModel, frozen=True):
    exp: int | None = None
    user_data: UserData
