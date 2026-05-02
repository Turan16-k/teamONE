from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", case_sensitive=True)

    DATABASE_URL: str = "postgresql://user:password@localhost:5432/financial_platform"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    GEMINI_API_KEY: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"
    ENCRYPTION_KEY: str = ""

    APP_ENV: str = "development"
    DEBUG: bool = True
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
