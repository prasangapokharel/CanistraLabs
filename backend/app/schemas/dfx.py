"""Pydantic schemas for the unified dfx API."""

from typing import Optional

from pydantic import BaseModel, Field


class DfxConvertRequest(BaseModel):
    amount: Optional[str] = Field(
        None, description="ICP amount to convert; omit for auto-convert"
    )


class DfxCyclesTopUpRequest(BaseModel):
    canister_id: str
    amount: str = Field(..., description="Cycles amount e.g. 500000000000")


class DfxCanisterCreateRequest(BaseModel):
    name: Optional[str] = None
    with_cycles: Optional[str] = Field(None, alias="withCycles")
    network: Optional[str] = None

    model_config = {"populate_by_name": True}


class DfxDeployRequest(BaseModel):
    name: Optional[str] = None
    with_cycles: Optional[str] = Field(None, alias="withCycles")
    network: Optional[str] = None

    model_config = {"populate_by_name": True}


class DfxDepositCyclesRequest(BaseModel):
    amount: str


class DfxProjectDeployRequest(BaseModel):
    code_content: Optional[str] = None


class DfxCanisterPowerRequest(BaseModel):
    enabled: bool = Field(..., description="True=start canister, False=stop")
