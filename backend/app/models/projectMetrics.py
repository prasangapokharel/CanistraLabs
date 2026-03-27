"""Project metrics model for real-time monitoring."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Float, BigInteger, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db import Base

if TYPE_CHECKING:
    from app.models.project import Project


class ProjectMetrics(Base):
    """Project metrics model for real-time monitoring data."""

    __tablename__ = "project_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)

    # Storage metrics
    storage_used_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    storage_limit_bytes: Mapped[int] = mapped_column(
        BigInteger, default=2_147_483_648, nullable=False
    )  # 2GB default

    # Performance metrics
    avg_response_time_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    uptime_percentage: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)

    # Traffic metrics
    requests_today: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requests_total: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    bandwidth_used_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    # Cycle metrics
    cycles_balance: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    cycles_burned_today: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    cycles_burned_total: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    # Deployment metrics
    build_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    deployment_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    last_deployment_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Health status
    is_healthy: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_health_check: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    error_count_today: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # SSL and domain metrics
    ssl_status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    custom_domains_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project")

    def __repr__(self) -> str:
        return f"<ProjectMetrics(id={self.id}, project_id={self.project_id}, storage_used={self.storage_used_bytes})>"

    @property
    def storage_used_mb(self) -> float:
        """Get storage used in MB."""
        return round(self.storage_used_bytes / 1024 / 1024, 2)

    @property
    def storage_limit_mb(self) -> float:
        """Get storage limit in MB."""
        return round(self.storage_limit_bytes / 1024 / 1024, 2)

    @property
    def storage_usage_percentage(self) -> float:
        """Get storage usage percentage."""
        if self.storage_limit_bytes == 0:
            return 0.0
        return round((self.storage_used_bytes / self.storage_limit_bytes) * 100, 1)

    @property
    def deployment_size_mb(self) -> float:
        """Get deployment size in MB."""
        return round(self.deployment_size_bytes / 1024 / 1024, 2)

    @property
    def bandwidth_used_mb(self) -> float:
        """Get bandwidth used in MB."""
        return round(self.bandwidth_used_bytes / 1024 / 1024, 2)
