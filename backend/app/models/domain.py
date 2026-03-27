"""
Domain management models for ICP hosting platform.
Handles custom domain configuration and SSL certificate management.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


class DomainStatus(str, Enum):
    """Domain configuration status."""

    PENDING = "pending"  # Initial setup, DNS not configured
    DNS_CONFIGURED = "dns_configured"  # DNS records set up
    REGISTERING = "registering"  # Submitted to ICP boundary nodes
    ACTIVE = "active"  # Domain active with SSL
    FAILED = "failed"  # Registration failed
    EXPIRED = "expired"  # SSL certificate expired
    SUSPENDED = "suspended"  # Domain suspended


class DomainRegistrationStatus(str, Enum):
    """ICP boundary node registration status."""

    PENDING = "Pending"
    AVAILABLE = "Available"
    FAILED = "Failed"
    PROCESSING = "Processing"


class CustomDomain(Base):
    """Custom domain configuration for projects."""

    __tablename__ = "custom_domains"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    # Domain information
    domain_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subdomain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # For subdomains

    # Status tracking
    status: Mapped[str] = mapped_column(String(50), default=DomainStatus.PENDING, nullable=False)
    registration_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # ICP integration
    canister_id: Mapped[str] = mapped_column(String(255), nullable=False)
    icp_request_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # From boundary node registration

    # DNS configuration
    dns_configured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cname_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    txt_record_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    acme_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # SSL certificate
    ssl_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ssl_issued_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ssl_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Configuration data
    dns_instructions: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON with DNS setup
    ic_domains_content: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Content for .well-known/ic-domains

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="custom_domains")
    owner: Mapped["User"] = relationship("User", back_populates="custom_domains")
    verifications: Mapped[list["DomainVerification"]] = relationship(
        "DomainVerification",
        cascade="all, delete-orphan",
        foreign_keys="DomainVerification.domain_id",
    )

    def __repr__(self) -> str:
        return f"<CustomDomain(id={self.id}, domain={self.domain_name}, status={self.status})>"

    @property
    def full_domain(self) -> str:
        """Get the full domain name including subdomain if present."""
        if self.subdomain:
            return f"{self.subdomain}.{self.domain_name}"
        return self.domain_name

    @property
    def canister_url(self) -> str:
        """Get the original canister URL."""
        return f"https://{self.canister_id}.icp0.io/"

    @property
    def custom_url(self) -> str:
        """Get the custom domain URL."""
        return f"https://{self.full_domain}/"


class DomainVerification(Base):
    """DNS verification records and status tracking."""

    __tablename__ = "domain_verifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("custom_domains.id"), nullable=False)

    # Verification type
    record_type: Mapped[str] = mapped_column(String(10), nullable=False)  # CNAME, TXT, ALIAS
    record_name: Mapped[str] = mapped_column(String(255), nullable=False)  # Host/Name
    record_value: Mapped[str] = mapped_column(String(255), nullable=False)  # Target/Value

    # Verification status
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_checked: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<DomainVerification(id={self.id}, type={self.record_type}, verified={self.verified})>"
        )
