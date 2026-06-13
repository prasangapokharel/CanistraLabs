"""Canister model for database."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db import Base

if TYPE_CHECKING:
    from app.models.project import Project


class CanisterStatus(str, Enum):
    """Possible canister statuses."""

    PENDING = "pending"
    CREATING = "creating"
    ACTIVE = "active"
    FAILED = "failed"
    DELETED = "deleted"


class Canister(Base):
    """Canister model representing an ICP canister."""

    __tablename__ = "canisters"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    canister_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    # One user principal owns many canisters — must not be unique
    principal_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    canister_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default=CanisterStatus.PENDING, nullable=False)
    cycles_balance: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    memory_usage: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="canister")

    def __repr__(self) -> str:
        return f"<Canister(id={self.id}, principal_id={self.principal_id}, status={self.status})>"
