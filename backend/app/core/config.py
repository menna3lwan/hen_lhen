"""Application configuration using Pydantic BaseSettings."""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    # App
    APP_NAME: str = "HenLehen"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://henlehen:henlehen_secret@localhost:5432/henlehen_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_AUTH_PER_MINUTE: int = 20

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 10
    UPLOAD_DIR: str = "uploads"
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp"]
    ALLOWED_DOC_TYPES: List[str] = ["application/pdf"]

    # S3 (optional — falls back to local storage)
    S3_BUCKET: str = ""
    S3_REGION: str = "me-south-1"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_ENDPOINT_URL: str = ""  # for MinIO / DigitalOcean Spaces

    # Payment Webhook
    PAYMENT_WEBHOOK_SECRET: str = "webhook-secret-change-in-production"

    # Cache TTL (seconds)
    CACHE_TTL_SPECIALTIES: int = 3600  # 1 hour
    CACHE_TTL_DOCTOR_PROFILE: int = 300  # 5 min

    @property
    def database_url_sync(self) -> str:
        """Sync DB URL for Alembic migrations."""
        return self.DATABASE_URL.replace("+asyncpg", "+psycopg2")

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [i.strip() for i in v.split(",")]
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


settings = Settings()
