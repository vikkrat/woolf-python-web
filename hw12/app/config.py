"""Validated configuration loaded from environment or .env."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Service settings; secrets have no production defaults."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str
    jwt_secret: str = Field(min_length=32)
    redis_url: str
    access_minutes: int = 15
    cache_seconds: int = 60
    cors_origins: list[str] = ["http://localhost:3000"]
    public_url: str = "http://localhost:8012"
    smtp_host: str = "mailpit"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_starttls: bool = False
    mail_from: str = "noreply@example.com"
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""
    me_limit: int = 10


settings = Settings()
