from decimal import Decimal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    embedding_model: str
    erp_connector_service_url: str
    exceptions_queue_url: str
    iva_rate: Decimal


settings = Settings()
