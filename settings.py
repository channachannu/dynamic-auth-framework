"""
settings.py
============
Application configuration from environment variables.

Create a .env file in the project root:
    DATABASE_URL=postgresql+asyncpg://daf_user:daf_secure@localhost:5432/daf
    APP_ENV=development
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    APP_NAME:            str = "Dynamic Auth Framework"
    APP_ENV:             str = "development"
    VERSION:             str = "1.0.0"
    DATABASE_URL:        str = "postgresql+asyncpg://daf_user:daf_secure@localhost:5432/daf"
    DEFAULT_PLACEHOLDER: str = "x"


app_settings = AppSettings()
