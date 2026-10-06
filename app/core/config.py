from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "Doctors on Call"
    APP_ENV: str = "development"
    DEBUG: bool = True
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None

    PROJECT_NAME: str = "Doctors on Call"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/docsoncall"
    REDIS_URL: str = "redis://localhost:6380/0"
    
    MINIO_ENDPOINT: str = "localhost:9002"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "hpr-documents"
    MINIO_SECURE: bool = False
    
    ABDM_CLIENT_ID: str = "sandbox_client_id"
    ABDM_CLIENT_SECRET: str = "sandbox_client_secret"
    ABDM_GATEWAY_URL: str = "https://dev.abdm.gov.in/api/hiecm/gateway/v3/sessions"
    ABDM_HPR_URL: str = "https://apihspsbx.abdm.gov.in"

    # LLM Configuration (OpenAI-compatible API)
    # Works with: Ollama, vLLM, OpenAI, Together, Groq, etc.
    LLM_ENABLED: bool = False  # Set to True when LLM is available
    LLM_BASE_URL: str = "http://localhost:11434/v1"  # Ollama default
    LLM_MODEL: str = "llama3.1"
    LLM_API_KEY: str = ""
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 1024

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()

    
