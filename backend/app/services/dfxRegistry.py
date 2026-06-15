"""Registry mapping dfx CLI commands to API routes and DfxCommand methods."""

from __future__ import annotations

from typing import Any, Dict, List

# Each entry: dfx CLI path, HTTP method, API path, DfxCommand method, notes
DFX_COMMAND_REGISTRY: List[Dict[str, Any]] = [
    {
        "dfx": "dfx --version",
        "method": "GET",
        "api": "/api/v1/dfx/version",
        "implemented": True,
        "category": "meta",
    },
    {
        "dfx": "dfx ping [network]",
        "method": "GET",
        "api": "/api/v1/dfx/ping",
        "implemented": True,
        "category": "network",
    },
    {
        "dfx": "dfx info <subcommand>",
        "method": "GET",
        "api": "/api/v1/dfx/info/{subcommand}",
        "implemented": True,
        "category": "network",
    },
    {
        "dfx": "dfx identity whoami",
        "method": "GET",
        "api": "/api/v1/dfx/identity/whoami",
        "implemented": True,
        "category": "identity",
    },
    {
        "dfx": "dfx identity get-principal",
        "method": "GET",
        "api": "/api/v1/dfx/identity/principal",
        "implemented": True,
        "category": "identity",
    },
    {
        "dfx": "dfx ledger account-id",
        "method": "GET",
        "api": "/api/v1/dfx/ledger/account-id",
        "implemented": True,
        "category": "ledger",
    },
    {
        "dfx": "dfx ledger balance",
        "method": "GET",
        "api": "/api/v1/dfx/ledger/balance",
        "implemented": True,
        "category": "ledger",
    },
    {
        "dfx": "dfx cycles balance",
        "method": "GET",
        "api": "/api/v1/dfx/cycles/balance",
        "implemented": True,
        "category": "cycles",
    },
    {
        "dfx": "dfx cycles convert --amount",
        "method": "POST",
        "api": "/api/v1/dfx/cycles/convert",
        "implemented": True,
        "category": "cycles",
    },
    {
        "dfx": "dfx cycles top-up <canister> <amount>",
        "method": "POST",
        "api": "/api/v1/dfx/cycles/top-up",
        "implemented": True,
        "category": "cycles",
    },
    {
        "dfx": "dfx wallet balance",
        "method": "GET",
        "api": "/api/v1/dfx/wallet/balance",
        "implemented": True,
        "category": "wallet",
    },
    {
        "dfx": "dfx canister create",
        "method": "POST",
        "api": "/api/v1/dfx/canister/create",
        "implemented": True,
        "category": "canister",
    },
    {
        "dfx": "dfx deploy [name]",
        "method": "POST",
        "api": "/api/v1/dfx/deploy",
        "implemented": True,
        "category": "deploy",
    },
    {
        "dfx": "dfx canister status <id>",
        "method": "GET",
        "api": "/api/v1/dfx/canister/{canister_id}/status",
        "implemented": True,
        "category": "canister",
    },
    {
        "dfx": "dfx canister info <id>",
        "method": "GET",
        "api": "/api/v1/dfx/canister/{canister_id}/info",
        "implemented": True,
        "category": "canister",
    },
    {
        "dfx": "dfx canister url <id>",
        "method": "GET",
        "api": "/api/v1/dfx/canister/{canister_id}/url",
        "implemented": True,
        "category": "canister",
    },
    {
        "dfx": "dfx canister start <id>",
        "method": "POST",
        "api": "/api/v1/dfx/canister/{canister_id}/start",
        "implemented": True,
        "category": "canister",
    },
    {
        "dfx": "dfx canister stop <id>",
        "method": "POST",
        "api": "/api/v1/dfx/canister/{canister_id}/stop",
        "implemented": True,
        "category": "canister",
    },
    {
        "dfx": "dfx canister delete <id> --yes",
        "method": "DELETE",
        "api": "/api/v1/dfx/canister/{canister_id}",
        "implemented": True,
        "category": "canister",
    },
    {
        "dfx": "dfx canister deposit-cycles <id> <amount>",
        "method": "POST",
        "api": "/api/v1/dfx/canister/{canister_id}/deposit-cycles",
        "implemented": True,
        "category": "canister",
    },
    {
        "dfx": "dfx deploy (project assets)",
        "method": "POST",
        "api": "/api/v1/dfx/projects/{project_id}/deploy",
        "implemented": True,
        "category": "deploy",
        "notes": "Official path via CanisterFactory + ICPService asset deploy",
    },
    {
        "dfx": "dfx deploy (update assets)",
        "method": "POST",
        "api": "/api/v1/dfx/projects/{project_id}/update-canister",
        "implemented": True,
        "category": "deploy",
    },
    {
        "dfx": "deployment history",
        "method": "GET",
        "api": "/api/v1/dfx/projects/{project_id}/deployments",
        "implemented": True,
        "category": "deploy",
    },
    {
        "dfx": "deployment status",
        "method": "GET",
        "api": "/api/v1/dfx/projects/{project_id}/deployments/{deployment_id}",
        "implemented": True,
        "category": "deploy",
    },
    {
        "dfx": "dfx canister stop/start (project)",
        "method": "POST",
        "api": "/api/v1/dfx/projects/{project_id}/power",
        "implemented": True,
        "category": "canister",
    },
    {
        "dfx": "dfx canister delete (project)",
        "method": "DELETE",
        "api": "/api/v1/dfx/projects/{project_id}/canister",
        "implemented": True,
        "category": "canister",
    },
    {
        "dfx": "dfx canister install",
        "method": "POST",
        "api": None,
        "implemented": False,
        "category": "canister",
        "notes": "Use project deploy/update endpoints",
    },
    {
        "dfx": "dfx canister call",
        "method": "POST",
        "api": None,
        "implemented": False,
        "category": "canister",
    },
    {
        "dfx": "dfx start / dfx stop",
        "method": "POST",
        "api": None,
        "implemented": False,
        "category": "replica",
        "notes": "Local replica only — use ./start.sh --local-dfx",
    },
]


def registry_summary() -> Dict[str, Any]:
    implemented = [c for c in DFX_COMMAND_REGISTRY if c["implemented"]]
    pending = [c for c in DFX_COMMAND_REGISTRY if not c["implemented"]]
    return {
        "total": len(DFX_COMMAND_REGISTRY),
        "implemented": len(implemented),
        "pending": len(pending),
        "commands": DFX_COMMAND_REGISTRY,
    }
