from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "Doctors on Call"
    APP_ENV: str = "development"
    DEBUG: bool = True
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None

    PROJECT_NAME: str = "Doctors on Call"
    # Mapped to 5433 to avoid host Postgres conflict
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/docsoncall"
    # Mapped to 6380 to avoid host Redis conflict
    REDIS_URL: str = "redis://localhost:6380/0"
    
    MINIO_ENDPOINT: str = "localhost:9004"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "hpr-documents"
    MINIO_SECURE: bool = False
    
    ABDM_CLIENT_ID: str = "sandbox_client_id"
    ABDM_CLIENT_SECRET: str = "sandbox_client_secret"
    ABDM_GATEWAY_URL: str = "https://dev.abdm.gov.in/api/hiecm/gateway/v3/sessions"
    ABDM_HPR_URL: str = "https://apihspsbx.abdm.gov.in/v4/int/api"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
