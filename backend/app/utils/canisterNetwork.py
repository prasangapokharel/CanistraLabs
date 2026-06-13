"""Detect whether a canister ID belongs to local dfx or IC mainnet."""

from __future__ import annotations

import re

# dfx local replica IDs embed 7777 / 77777 in segments (e.g. uxrrr-q7777-77774-qaaaq-cai).
_LOCAL_CANISTER_RE = re.compile(r"(?:^|-)(?:[a-z0-9]*7777|77777)(?:-|$)", re.IGNORECASE)


def is_local_canister_id(canister_id: str | None) -> bool:
    if not canister_id:
        return False
    return bool(_LOCAL_CANISTER_RE.search(canister_id.strip()))


def network_for_canister(canister_id: str | None) -> str:
    """Return ``local`` or ``ic`` based on canister ID shape."""
    return "local" if is_local_canister_id(canister_id) else "ic"


def canister_network_label(canister_id: str | None) -> str:
    return "local dfx replica" if is_local_canister_id(canister_id) else "IC mainnet"


class CanisterNetworkMismatchError(Exception):
    """Raised when an operation targets the wrong network for a canister ID."""

    def __init__(
        self,
        canister_id: str,
        *,
        canister_network: str,
        configured_network: str,
        operation: str = "manage",
    ):
        self.canister_id = canister_id
        self.canister_network = canister_network
        self.configured_network = configured_network
        self.operation = operation
        if canister_network == "local" and configured_network == "ic":
            msg = (
                f"Canister {canister_id} was deployed on the local dfx replica, not IC mainnet. "
                f"Start `dfx start` to {operation} it locally, or publish again to deploy a new mainnet canister."
            )
        elif canister_network == "ic" and configured_network == "local":
            msg = (
                f"Canister {canister_id} is on IC mainnet but the app is configured for local deploy. "
                f"Set DEPLOY_NETWORK=ic or redeploy locally."
            )
        else:
            msg = (
                f"Cannot {operation} canister {canister_id}: network mismatch "
                f"(canister={canister_network}, configured={configured_network})."
            )
        super().__init__(msg)
