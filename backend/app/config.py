from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "TrippieAutoAI"
    debug: bool = True

    database_url: str = f"sqlite:///{BASE_DIR / 'trippie_auto_ai.db'}"

    secret_key: str = "CHANGE_THIS_IN_PRODUCTION"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
