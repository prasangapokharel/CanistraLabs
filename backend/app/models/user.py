"""User model for database."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db import Base

if TYPE_CHECKING:
    from app.models.enrollment import ProjectEnrollment
    from app.models.project import Project
    from app.models.domain import CustomDomain


class User(Base):
    """User model for authentication and project ownership."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # ICP Identity Management (Encrypted)
    dfx_identity_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    principal_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    account_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    encrypted_identity_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    wallet_cycles_balance: Mapped[Optional[str]] = mapped_column(
        String(50), default="0", nullable=True
    )
    identity_created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    projects: Mapped[list["Project"]] = relationship(
        "Project", back_populates="owner", cascade="all, delete-orphan"
    )
    enrollments: Mapped[list["ProjectEnrollment"]] = relationship(
        "ProjectEnrollment", back_populates="user", cascade="all, delete-orphan"
    )
    custom_domains: Mapped[list["CustomDomain"]] = relationship(
        "CustomDomain", back_populates="owner", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"
