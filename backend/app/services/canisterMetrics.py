"""ICP canister metrics — only data from ``dfx canister status`` (management canister)."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from app.utils.icpUtils import ICPError, ICPService

logger = logging.getLogger(__name__)


def format_cycles(cycles: int) -> str:
    if cycles >= 1_000_000_000_000:
        return f"{cycles / 1_000_000_000_000:.3f} TC"
    if cycles >= 1_000_000_000:
        return f"{cycles / 1_000_000_000:.3f} BC"
    if cycles >= 1_000_000:
        return f"{cycles / 1_000_000:.3f} MC"
    return f"{cycles:,} cycles"


def format_bytes(bytes_val: int) -> str:
    if bytes_val >= 1_073_741_824:
        return f"{bytes_val / 1_073_741_824:.2f} GB"
    if bytes_val >= 1_048_576:
        return f"{bytes_val / 1_048_576:.2f} MB"
    if bytes_val >= 1024:
        return f"{bytes_val / 1024:.2f} KB"
    return f"{bytes_val} B"


def format_duration_seconds(seconds: int) -> str:
    if seconds >= 86_400:
        return f"{seconds / 86_400:.1f} days"
    if seconds >= 3600:
        return f"{seconds / 3600:.1f} hours"
    return f"{seconds} sec"


def _empty_icp_metrics(checked_at: str, error: Optional[str] = None) -> dict[str, Any]:
    base = {
        "source": "dfx canister status",
        "checked_at": checked_at,
        "status": "not_deployed",
        "cycles_balance": 0,
        "cycles_formatted": "0",
        "idle_cycles_burned_per_day": 0,
        "idle_cycles_burned_per_day_formatted": "0",
        "memory_bytes": 0,
        "memory_formatted": "0 B",
        "freezing_threshold_seconds": 0,
        "freezing_threshold_formatted": "—",
        "reserved_cycles": 0,
        "reserved_cycles_formatted": "0",
        "reserved_cycles_limit": 0,
        "reserved_cycles_limit_formatted": "0",
        "compute_allocation": 0,
        "memory_allocation": 0,
        "number_of_queries": 0,
        "instructions_spent_in_queries": 0,
        "query_request_payload_bytes": 0,
        "query_request_payload_formatted": "0 B",
        "query_response_payload_bytes": 0,
        "query_response_payload_formatted": "0 B",
        "module_hash": None,
        "controllers": [],
        "fields": [],
    }
    if error:
        base["error"] = error
    return base


def _field_rows(raw: dict[str, Any]) -> list[dict[str, str]]:
    """Human-readable list of every ICP field for the UI."""
    rows = [
        {"label": "Status", "value": str(raw.get("status", "unknown"))},
        {"label": "Cycles balance (current)", "value": format_cycles(int(raw.get("cycles_balance") or 0))},
        {
            "label": "Idle cycles burned / day",
            "value": format_cycles(int(raw.get("idle_cycles_burned_per_day") or 0)),
        },
        {"label": "Memory size", "value": format_bytes(int(raw.get("memory_size") or 0))},
        {
            "label": "Freezing threshold",
            "value": format_duration_seconds(int(raw.get("freezing_threshold_seconds") or 0)),
        },
        {"label": "Reserved cycles", "value": format_cycles(int(raw.get("reserved_cycles") or 0))},
        {
            "label": "Reserved cycles limit",
            "value": format_cycles(int(raw.get("reserved_cycles_limit") or 0)),
        },
        {"label": "Compute allocation (%)", "value": str(raw.get("compute_allocation") or 0)},
        {"label": "Memory allocation (bytes)", "value": format_bytes(int(raw.get("memory_allocation") or 0))},
        {"label": "Number of queries", "value": f"{int(raw.get('number_of_queries') or 0):,}"},
        {
            "label": "Instructions spent (queries)",
            "value": f"{int(raw.get('instructions_spent_in_queries') or 0):,}",
        },
        {
            "label": "Query request payload (total)",
            "value": format_bytes(int(raw.get("query_request_payload_bytes") or 0)),
        },
        {
            "label": "Query response payload (total)",
            "value": format_bytes(int(raw.get("query_response_payload_bytes") or 0)),
        },
    ]
    if raw.get("module_hash"):
        rows.append({"label": "Module hash", "value": str(raw["module_hash"])})
    controllers = raw.get("controllers") or []
    if controllers:
        rows.append({"label": "Controllers", "value": ", ".join(controllers[:3]) + ("…" if len(controllers) > 3 else "")})
    return rows


def fetch_icp_canister_metrics(canister_id: Optional[str]) -> dict[str, Any]:
    """
    Fetch metrics directly from ICP through ``dfx canister status``.

    ICP provides:
    - Current cycles **balance** (remaining)
    - Idle cycles burned per day (estimated daily idle cost)
    - Cumulative query payload in/out (IC-reported ingress/egress for queries)
    - Memory, freezing threshold, reserved cycles, module hash, etc.

    ICP does **not** expose total lifetime cycles consumed for a canister.
    """
    checked_at = datetime.utcnow().isoformat()

    if not canister_id:
        return _empty_icp_metrics(checked_at)

    try:
        raw = ICPService.get_canister_status(canister_id)
    except ICPError as exc:
        logger.warning("ICP canister status failed for %s: %s", canister_id, exc)
        metrics = _empty_icp_metrics(checked_at, str(exc))
        metrics["status"] = "unknown"
        return metrics

    cycles = int(raw.get("cycles_balance") or raw.get("cycles") or 0)
    memory = int(raw.get("memory_size") or raw.get("memory_usage") or 0)
    idle = int(raw.get("idle_cycles_burned_per_day") or 0)
    freezing = int(raw.get("freezing_threshold_seconds") or 0)

    metrics = {
        "source": "dfx canister status",
        "checked_at": checked_at,
        "status": str(raw.get("status") or "unknown"),
        "cycles_balance": cycles,
        "cycles_formatted": format_cycles(cycles),
        "idle_cycles_burned_per_day": idle,
        "idle_cycles_burned_per_day_formatted": format_cycles(idle),
        "memory_bytes": memory,
        "memory_formatted": format_bytes(memory),
        "freezing_threshold_seconds": freezing,
        "freezing_threshold_formatted": format_duration_seconds(freezing) if freezing else "—",
        "reserved_cycles": int(raw.get("reserved_cycles") or 0),
        "reserved_cycles_formatted": format_cycles(int(raw.get("reserved_cycles") or 0)),
        "reserved_cycles_limit": int(raw.get("reserved_cycles_limit") or 0),
        "reserved_cycles_limit_formatted": format_cycles(int(raw.get("reserved_cycles_limit") or 0)),
        "compute_allocation": int(raw.get("compute_allocation") or 0),
        "memory_allocation": int(raw.get("memory_allocation") or 0),
        "number_of_queries": int(raw.get("number_of_queries") or 0),
        "instructions_spent_in_queries": int(raw.get("instructions_spent_in_queries") or 0),
        "query_request_payload_bytes": int(raw.get("query_request_payload_bytes") or 0),
        "query_request_payload_formatted": format_bytes(
            int(raw.get("query_request_payload_bytes") or 0)
        ),
        "query_response_payload_bytes": int(raw.get("query_response_payload_bytes") or 0),
        "query_response_payload_formatted": format_bytes(
            int(raw.get("query_response_payload_bytes") or 0)
        ),
        "module_hash": raw.get("module_hash"),
        "controllers": raw.get("controllers") or [],
        "fields": _field_rows(raw),
    }
    return metrics


def fetch_canister_metrics(canister_id: str, url: Optional[str] = None) -> dict[str, Any]:
    """Backward-compatible wrapper — ICP data only (url ignored)."""
    return fetch_icp_canister_metrics(canister_id)


def build_project_metrics(
    *,
    canister_id: Optional[str],
    url: Optional[str] = None,
    code_content: Optional[str] = None,
    project_name: str = "",
) -> dict[str, Any]:
    """Project metrics = ICP canister status only."""
    icp = fetch_icp_canister_metrics(canister_id)
    return {
        **icp,
        "project_name": project_name,
        "canister_id": canister_id,
        "url": url,
    }
