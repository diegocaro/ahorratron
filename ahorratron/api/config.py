from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_key: str
    actual_url: str
    actual_password: str
    actual_file: str
    actual_default_account: str
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()  # type: ignore
