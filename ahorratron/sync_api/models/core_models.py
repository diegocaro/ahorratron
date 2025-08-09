from typing import Optional

from pydantic import BaseModel


class UserData(BaseModel):
    clientId: str
    clientSecret: str
    connector_id: str = "banco_de_chile"


class SessionData(BaseModel):
    exp: Optional[int] = None
    user_data: UserData
