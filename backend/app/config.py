"""Application configuration settings using Pydantic Settings."""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App Configuration
    app_name: str = "ICP Hosting Platform"
    app_version: str = "0.1.0"
    debug: bool = True
    environment: str = "development"

    # Database - CRITICAL: Must be set via environment variable for security
    database_url: str = Field(..., description="Database connection URL (required)")
    database_echo: bool = False

    # JWT - CRITICAL: Must be set via environment variable for security
    jwt_secret_key: str = Field(
        ..., min_length=32, description="JWT secret key (minimum 32 characters, required)"
    )
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    jwt_refresh_expiration_days: int = 7

    # ICP Configuration
    wallet_principal_id: str = "ni5n2-efxui-dyqdu-2mnpr-atclq-d6snc-zdq5q-u6ibz-ibpkq-brjpj-gqe"
    icp_network: str = "local"
    dfx_network: str = "local"
    dfx_path: str = "/usr/local/bin/dfx"

    # Celery/Redis - Use environment variables in production
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    redis_url: str = "redis://localhost:6379"

    # Application URLs - Use environment variables for different environments
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"

    # Email Configuration
    email_smtp_host: str = "localhost"
    email_smtp_port: int = 587
    email_smtp_username: str = ""
    email_smtp_password: str = ""
    email_smtp_use_tls: bool = True
    email_smtp_use_ssl: bool = False
    email_from_email: str = "noreply@icphosting.com"
    email_from_name: str = "ICP Hosting Platform"

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
    return Settings(_env_file=".env")


settings = get_settings()
