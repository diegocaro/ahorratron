from typing import Optional

from pydantic import BaseModel


class UserData(BaseModel, frozen=True):
    clientId: str
    clientSecret: str
    connector_id: str = "banco_de_chile"


class SessionData(BaseModel, frozen=True):
    exp: int | None = None
    user_data: UserData
