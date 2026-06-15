"""Parse dfx/IC replica errors into user-facing messages."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional


def parse_dfx_error(raw: str) -> Dict[str, Any]:
    text = (raw or "").strip()
    lower = text.lower()

    if "canister_not_found" in lower or "does not exist" in lower:
        return {
            "error_code": "canister_not_found",
            "message": (
                "This canister does not exist on the selected network. "
                "It may be a local dev canister while the app targets mainnet — "
                "publish again to deploy on IC, or start `dfx start` for local canisters."
            ),
            "action": "Republish the project for a new mainnet canister, or run dfx locally.",
        }

    if "insufficient cycles" in lower:
        return {
            "error_code": "insufficient_cycles",
            "message": (
                "Not enough cycles for this operation. "
                "Convert ICP to cycles on Wallet → Convert, refresh, then try again."
            ),
            "action": "Wallet → Convert → Refresh balances.",
        }

    if "couldn't send message" in lower and "stopped" in lower:
        return {
            "error_code": "canister_stopped",
            "message": "Canister is stopped. Turn it on from the project list or editor.",
            "action": "Toggle the project power switch to On.",
        }

    if "replica returned" in lower and "400" in lower:
        return {
            "error_code": "replica_rejected",
            "message": "The IC replica rejected this request. See details in debug mode.",
            "raw_error": text[:800],
        }

    if "connection refused" in lower or "could not connect" in lower:
        return {
            "error_code": "network_unreachable",
            "message": (
                "Cannot reach the Internet Computer network. "
                "For local canisters, run `dfx start --background`."
            ),
            "action": "Check dfx is running and your network settings.",
        }

    if "trying to connect to the local replica" in lower or "local replica" in lower:
        return {
            "error_code": "local_replica_down",
            "message": (
                "This canister was deployed locally but the dfx replica is not running. "
                "Run `dfx start --background`, or publish again to deploy on IC mainnet."
            ),
            "action": "Start dfx locally or republish for a mainnet canister.",
        }

    # Strip noisy stack traces for display; keep first meaningful line
    first_line = next((ln.strip() for ln in text.splitlines() if ln.strip()), text)
    return {
        "error_code": "dfx_error",
        "message": first_line[:500] if first_line else "dfx command failed",
        "raw_error": text[:800] if len(text) > len(first_line) else None,
    }


def http_error_detail(error: Exception, *, fallback: str, debug: bool) -> Any:
    """Build FastAPI detail: dict when structured, string in debug."""
    raw = str(error)
    parsed = parse_dfx_error(raw)
    if parsed.get("error_code") != "dfx_error" or debug:
        if debug and parsed.get("raw_error"):
            parsed["debug"] = raw
        return parsed
    return parsed.get("message") or (raw if debug else fallback)
