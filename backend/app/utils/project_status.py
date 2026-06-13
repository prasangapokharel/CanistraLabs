"""Normalize project status values for API consumers."""

from typing import Optional


def normalize_project_status(status: str, canister_id: Optional[str] = None) -> str:
    """Map internal DB status to frontend-friendly labels."""
    if canister_id and status in {"active", "deployed"}:
        return "deployed"
    if status == "active" and canister_id:
        return "deployed"
    return status
