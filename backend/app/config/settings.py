"""Application Configuration using Pydantic Settings."""

from functools import lru_cache
from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    APP_NAME: str = "Enterprise AI Platform"
    APP_ENV: str = "development"
    ENVIRONMENT: str | None = None
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    SECRET_KEY: str = "super-secret-key-change-in-production-must-be-32-chars-long"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/enterprise_ai"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/enterprise_ai"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 1800
    REDIS_URL: str = "redis://localhost:6379/0"
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"

    UPLOAD_DIR: str = "data/uploads"
    MODEL_DIR: str = "data/models"
    MAX_UPLOAD_SIZE_BYTES: int = 250 * 1024 * 1024  # 250MB

    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    # Security & Rate Limiting Controls
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_AUTH_PER_MINUTE: int = 30
    RATE_LIMIT_PREDICTION_PER_MINUTE: int = 120
    RATE_LIMIT_DEFAULT_PER_MINUTE: int = 300

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            v_trimmed = v.strip()
            if v_trimmed.startswith("[") and v_trimmed.endswith("]"):
                import json

                try:
                    parsed = json.loads(v_trimmed)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except Exception:
                    pass
            return [i.strip() for i in v_trimmed.split(",") if i.strip()]
        elif isinstance(v, list):
            return [str(i).strip() for i in v if str(i).strip()]
        return [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:8001",
            "http://127.0.0.1:8001",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
        ]

    @property
    def is_testing(self) -> bool:
        return self.APP_ENV == "testing" or self.ENVIRONMENT == "testing"


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
