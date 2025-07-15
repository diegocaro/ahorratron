import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_key: str
    actual_url: str
    actual_password: str
    actual_file: str
    actual_default_account: str
    model_config = SettingsConfigDict(env_file=".env")


def get_settings() -> Settings:
    env_file = os.getenv("ENV_FILE")
    return Settings(_env_file=env_file)  # type: ignore
