"""Application configuration settings using Pydantic Settings."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App Configuration
    app_name: str = "ICP Hosting Platform"
    app_version: str = "0.1.0"
    debug: bool = True
    environment: str = "development"

    # Database
    database_url: str = "postgresql://root:123456@localhost:5432/icp"
    database_echo: bool = False

    # JWT
    jwt_secret_key: str = "super-secret-icp-hosting-platform-key"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    jwt_refresh_expiration_days: int = 7

    # ICP Configuration
    wallet_principal_id: str = "ni5n2-efxui-dyqdu-2mnpr-atclq-d6snc-zdq5q-u6ibz-ibpkq-brjpj-gqe"
    icp_network: str = "local"
    dfx_network: str = "local"
    dfx_path: str = "/usr/local/bin/dfx"

    # Celery/Redis
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    redis_url: str = "redis://localhost:6379"

    # Application URLs
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"

    # Deployment
    auto_deploy_enabled: bool = True
    deployment_timeout_seconds: int = 300
    max_deployment_retries: int = 3

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


settings = get_settings()
