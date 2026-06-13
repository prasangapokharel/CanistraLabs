"""Application configuration settings using Pydantic Settings."""

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App Configuration
    app_name: str = "ICP Hosting Platform"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "production"

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

    # Encryption for custodial dfx identity keys (separate from JWT secret)
    encryption_key: Optional[str] = Field(
        default=None,
        min_length=32,
        description="Fernet encryption key material (32+ chars, required in production)",
    )

    # Admin/internal API protection (cron, mass deploy, etc.)
    admin_api_key: Optional[str] = Field(
        default=None,
        min_length=32,
        description="API key for admin/internal endpoints (X-Admin-Api-Key header)",
    )

    # CORS - comma-separated allowed origins (never use * with credentials)
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Auth policy
    require_email_verification: bool = False

    # ICP Configuration
    wallet_principal_id: str = ""
    icp_network: str = "ic"
    dfx_network: str = "ic"
    dfx_path: str = "/usr/local/bin/dfx"
    # TESTICP test ledger on IC mainnet (faucet.internetcomputer.org)
    use_testicp: bool = False
    testicp_ledger_canister_id: str = "xafvr-biaaa-aaaai-aql5q-cai"
    icp_ledger_canister_id: str = "rrkah-fqaaa-aaaaa-aaaaq-cai"
    rosetta_url: str = "https://rosetta-api.internetcomputer.org"
    # Where canisters are created (local = free dfx cycles; ic = mainnet)
    deploy_network: str = ""

    # Celery/Redis
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    redis_url: str = "redis://localhost:6379"

    # Application URLs
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
    async_deploy_enabled: bool = True
    deployment_timeout_seconds: int = 300
    max_deployment_retries: int = 3

    @field_validator("environment")
    @classmethod
    def normalize_environment(cls, value: str) -> str:
        return value.lower().strip()

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment in {"production", "prod"}

    @property
    def ledger_canister_id(self) -> Optional[str]:
        """Ledger canister for balance/convert commands (TESTICP or ICP)."""
        if self.use_testicp:
            return self.testicp_ledger_canister_id
        return self.icp_ledger_canister_id

    @property
    def wallet_network(self) -> str:
        """IC network for ICP ledger balance and cycles conversion."""
        if self.use_testicp:
            return self.icp_network if self.icp_network != "local" else "ic"
        return self.icp_network if self.icp_network != "local" else "ic"

    @property
    def token_symbol(self) -> str:
        return "TESTICP" if self.use_testicp else "ICP"

    @property
    def effective_deploy_network(self) -> str:
        """Network used for canister create/deploy (defaults to dfx_network)."""
        return self.deploy_network or self.dfx_network

    @property
    def effective_encryption_key(self) -> str:
        """Encryption key for identity storage; falls back to JWT secret in dev only."""
        if self.encryption_key:
            return self.encryption_key
        if self.is_production:
            raise ValueError("ENCRYPTION_KEY must be set in production")
        return self.jwt_secret_key

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings(_env_file=".env")


settings = get_settings()
