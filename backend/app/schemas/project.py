"""Project schemas for request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, computed_field, model_validator

from app.utils.icpUtils import ICPService


class ProjectBase(BaseModel):
    """Base project schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    language: str = Field(default="html", pattern="^(html|motoko|rust)$")


class ProjectCreate(ProjectBase):
    """Schema for project creation."""

    code_content: Optional[str] = None


class ProjectUpdate(BaseModel):
    """Schema for project updates."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    code_content: Optional[str] = None


class ProjectResponse(ProjectBase):
    """Schema for project response."""

    id: int
    user_id: int
    status: str
    canister_id: Optional[str]
    principal_id: Optional[str]
    url: Optional[str]
    created_at: datetime
    updated_at: datetime
    deployed_at: Optional[datetime]

    @model_validator(mode="after")
    def sanitize_url(self) -> "ProjectResponse":
        """Only expose a URL when the project has a real deployed canister."""
        if not self.canister_id:
            self.url = None
        elif not self.url:
            self.url = ICPService.canister_public_url(self.canister_id)
        elif self.canister_id not in self.url:
            is_local = "127.0.0.1" in self.url or "localhost" in self.url
            if not is_local:
                self.url = ICPService.canister_public_url(self.canister_id)
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def display_status(self) -> str:
        if self.canister_id and self.status in {"active", "deployed"}:
            return "deployed"
        if self.status == "failed":
            return "failed"
        if self.canister_id:
            return "deployed"
        return self.status if self.status else "pending"

    class Config:
        from_attributes = True


class ProjectDetailResponse(ProjectResponse):
    """Detailed project response with code content."""

    code_content: Optional[str] = None


class ProjectDeployRequest(BaseModel):
    """Schema for deployment request."""

    code_content: Optional[str] = None
    force: bool = False


class CanisterPowerRequest(BaseModel):
    """Start or stop a project's canister."""

    enabled: bool


class ProjectDeployResponse(BaseModel):
    """Schema for deployment response."""

    project_id: int
    deployment_id: int
    status: str
    message: str
    canister_id: Optional[str] = None
    url: Optional[str] = None
    principal_id: Optional[str] = None
    cycles_balance: Optional[str] = None
    funding_required: Optional[bool] = None
