"""IC mainnet / local cycle and ICP funding thresholds for deploy and convert."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from app.config import settings

# ~1 USD per trillion cycles (via XDR peg). Values from IC cycles cost docs + dfx forum.
MAINNET_CANISTER_CREATION_FEE = 500_000_000_000  # 500 BC — worst-case subnet fee
MAINNET_MIN_INSTALL_BUFFER = 100_000_000_000  # reserve for wasm/asset install
MAINNET_MIN_CYCLES_DEPLOY = MAINNET_CANISTER_CREATION_FEE + MAINNET_MIN_INSTALL_BUFFER  # 600 BC
MAINNET_RECOMMENDED_CYCLES = 2_000_000_000_000  # 2 TC — comfortable first deploy

LOCAL_MIN_CYCLES_DEPLOY = 20_000_000


def format_cycles(cycles_amount: int) -> str:
    if cycles_amount == 0:
        return "0 cycles"
    if cycles_amount >= 1_000_000_000_000:
        return f"{cycles_amount / 1_000_000_000_000:.3f} TC"
    if cycles_amount >= 1_000_000_000:
        return f"{cycles_amount / 1_000_000_000:.2f} BC"
    if cycles_amount >= 1_000_000:
        return f"{cycles_amount / 1_000_000:.1f} MC"
    return f"{cycles_amount:,} cycles"

# dfx cycles convert accepts small amounts; keep a tiny ICP reserve for ledger fees.
MIN_ICP_RESERVE_E8S = 100_000  # 0.001 ICP
MIN_ICP_CONVERT_E8S = 200_000  # 0.002 ICP (reserve + at least 0.001 to convert)


def is_mainnet_deploy() -> bool:
    return settings.effective_deploy_network == "ic"


def min_cycles_for_deploy() -> int:
    return MAINNET_MIN_CYCLES_DEPLOY if is_mainnet_deploy() else LOCAL_MIN_CYCLES_DEPLOY


def recommended_cycles_for_deploy() -> int:
    if is_mainnet_deploy():
        return MAINNET_RECOMMENDED_CYCLES
    return LOCAL_MIN_CYCLES_DEPLOY


def min_icp_to_convert_e8s() -> int:
    return MIN_ICP_CONVERT_E8S


def cycles_shortfall(cycles_balance: int) -> int:
    required = min_cycles_for_deploy()
    return max(0, required - cycles_balance)


def deploy_ready(cycles_balance: int) -> bool:
    return cycles_balance >= min_cycles_for_deploy()


def recommended_icp_for_deploy_shortfall(cycles_shortfall_amount: int) -> str:
    """Rough ICP estimate: ~1 ICP ≈ 1T cycles on mainnet (varies with CMC rate)."""
    if cycles_shortfall_amount <= 0:
        return "0"
    # Round up to 2 decimals; add small buffer for rate/fees
    icp = (cycles_shortfall_amount / 1_000_000_000_000) * 1.05
    return f"{max(0.01, round(icp, 2)):.2f}"


def funding_requirements(cycles_balance: int, icp_balance_e8s: int) -> Dict[str, Any]:
    """Structured funding criteria for wallet UI and deploy pre-checks."""
    required = min_cycles_for_deploy()
    recommended = recommended_cycles_for_deploy()
    shortfall = cycles_shortfall(cycles_balance)
    network = settings.effective_deploy_network

    return {
        "deploy_network": network,
        "cycles_balance": str(cycles_balance),
        "cycles_required": str(required),
        "cycles_recommended": str(recommended),
        "cycles_shortfall": str(shortfall),
        "formatted_cycles_required": format_cycles(required),
        "formatted_cycles_recommended": format_cycles(recommended),
        "formatted_cycles_shortfall": format_cycles(shortfall) if shortfall else "0 cycles",
        "deploy_ready": deploy_ready(cycles_balance),
        "min_icp_to_convert_e8s": str(min_icp_to_convert_e8s()),
        "min_icp_to_convert": "0.002 ICP",
        "recommended_icp_to_fund": recommended_icp_for_deploy_shortfall(shortfall),
        "icp_balance_e8s": str(icp_balance_e8s),
    }


def parse_cycles_from_dfx_error(error_text: str) -> Optional[int]:
    """Extract a cycles number from dfx stderr (e.g. 'need 3_100_000_000_000')."""
    if not error_text:
        return None
    match = re.search(r"(\d[\d_]+)\s*cycles", error_text, re.IGNORECASE)
    if match:
        return int(match.group(1).replace("_", ""))
    return None


def build_insufficient_cycles_error(
    cycles_balance: int,
    raw_error: str = "",
) -> Dict[str, Any]:
    """User-facing deploy failure payload."""
    required = min_cycles_for_deploy()
    shortfall = cycles_shortfall(cycles_balance)
    parsed = parse_cycles_from_dfx_error(raw_error)

    if parsed and parsed > required:
        required = parsed
        shortfall = max(0, required - cycles_balance)

    icp_hint = recommended_icp_for_deploy_shortfall(shortfall)

    if is_mainnet_deploy():
        summary = (
            f"Not enough cycles for mainnet deploy. You have {format_cycles(cycles_balance)}, "
            f"but need at least {format_cycles(required)} "
            f"(canister creation ~{format_cycles(MAINNET_CANISTER_CREATION_FEE)} + install buffer). "
            f"Convert about {icp_hint} ICP to cycles, refresh, then publish again."
        )
    else:
        summary = (
            f"Not enough cycles. You have {format_cycles(cycles_balance)}, "
            f"need at least {format_cycles(required)}."
        )

    return {
        "error_code": "insufficient_cycles",
        "message": summary,
        "cycles_balance": cycles_balance,
        "cycles_required": required,
        "cycles_shortfall": shortfall,
        "recommended_icp": icp_hint,
        "action": "Wallet → Convert: convert ICP to cycles, then Refresh balances.",
        "raw_error": raw_error[:500] if raw_error else None,
    }
