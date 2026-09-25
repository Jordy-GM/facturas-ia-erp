from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "exceptions-queue"
    environment: str = "development"
    database_url: str = (
        "postgresql+psycopg://facturas_user:change_me@postgres:5432/facturas_ia_erp"
    )
    host: str = "0.0.0.0"
    port: int = 8004

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
