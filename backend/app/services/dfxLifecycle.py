"""Start and verify the local dfx replica for dev and local-canister operations."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

_PING_INTERVAL_SEC = 2


def _dfx_project_root() -> Path:
    """Repo root containing dfx.json (parent of backend/)."""
    return Path(__file__).resolve().parents[3]


def _dfx_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = f"{Path.home() / '.local' / 'bin'}:{env.get('PATH', '')}"
    env["DFX_WARNING"] = "-mainnet_plaintext_identity"
    return env


def _dfx_bin() -> str:
    configured = (settings.dfx_path or "").strip()
    home_dfx = Path.home() / ".local" / "bin" / "dfx"
    if home_dfx.is_file():
        return str(home_dfx)
    if configured and Path(configured).exists():
        return configured
    found = shutil.which("dfx")
    return found or configured or "dfx"


def _is_pocketic_error(text: str) -> bool:
    lower = text.lower()
    return "pocketic" in lower or (
        "400 bad request" in lower and "/instances" in lower
    )


def is_local_replica_running() -> bool:
    """Return True if `dfx ping local` succeeds."""
    try:
        result = subprocess.run(
            [_dfx_bin(), "ping", "local"],
            capture_output=True,
            text=True,
            timeout=15,
            env=_dfx_env(),
            cwd=str(_dfx_project_root()),
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.debug("dfx ping local failed: %s", exc)
        return False


def _wait_for_local_replica(max_wait_seconds: int = 60) -> bool:
    """Poll until local replica responds or timeout."""
    deadline = time.monotonic() + max_wait_seconds
    while time.monotonic() < deadline:
        if is_local_replica_running():
            return True
        time.sleep(_PING_INTERVAL_SEC)
    return is_local_replica_running()


def _dfx_killall() -> None:
    """Stop stray dfx/PocketIC processes left from unclean shutdowns."""
    try:
        subprocess.run(
            [_dfx_bin(), "killall"],
            capture_output=True,
            text=True,
            timeout=30,
            env=_dfx_env(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.debug("dfx killall: %s", exc)


def _start_replica(*, clean: bool = False) -> tuple[int, str, str]:
    args = [_dfx_bin(), "start", "--background"]
    if clean:
        args.append("--clean")
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=120,
            env=_dfx_env(),
            cwd=str(_dfx_project_root()),
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
    except subprocess.TimeoutExpired:
        return -1, "", "dfx start timed out"


def ensure_local_replica() -> dict:
    """
    Start `dfx start --background` when enabled and the local replica is down.

    On PocketIC corruption (400 on /instances), kills stale processes and
    retries with `--clean`.
    """
    if not settings.dfx_auto_start:
        return {"auto_start": False, "running": is_local_replica_running(), "action": "disabled"}

    if is_local_replica_running():
        logger.info("dfx local replica already running")
        return {"auto_start": True, "running": True, "action": "already_running"}

    dfx = _dfx_bin()
    if not shutil.which(dfx) and not Path(dfx).is_file():
        logger.warning("dfx not found (%s) — skipping auto-start", dfx)
        return {"auto_start": True, "running": False, "action": "dfx_not_found"}

    _dfx_killall()

    try:
        logger.info("Starting dfx local replica: dfx start --background")
        returncode, stdout, stderr = _start_replica(clean=False)
        combined = f"{stdout}\n{stderr}"
        if returncode != 0 and "already running" not in combined.lower():
            logger.warning("dfx start returned %s: %s", returncode, combined[:500])

        running = _wait_for_local_replica(max_wait_seconds=60)
        action = "started" if running else "start_failed"

        if not running and _is_pocketic_error(combined):
            logger.warning("PocketIC state corrupt — retrying with dfx start --clean")
            _dfx_killall()
            returncode, stdout, stderr = _start_replica(clean=True)
            combined = f"{stdout}\n{stderr}"
            if returncode != 0 and "already running" not in combined.lower():
                logger.warning("dfx start --clean returned %s: %s", returncode, combined[:500])
            running = _wait_for_local_replica(max_wait_seconds=90)
            action = "started_clean" if running else "clean_failed"

        if running:
            logger.info("dfx local replica is running")
        else:
            logger.warning("dfx start finished but local replica is not responding")

        return {"auto_start": True, "running": running, "action": action}
    except OSError as exc:
        logger.warning("dfx auto-start failed: %s", exc)
        return {"auto_start": True, "running": False, "action": "error", "error": str(exc)}


def require_local_replica() -> None:
    """
    Ensure the local dfx replica is up before local-network operations.

    Raises RuntimeError with a user-facing message if unavailable.
    """
    if is_local_replica_running():
        return

    status = ensure_local_replica()
    if status.get("running") or _wait_for_local_replica(max_wait_seconds=30):
        return

    raise RuntimeError(
        "Local dfx replica is not running. The server tried to start it automatically "
        "(including PocketIC recovery) but it is still unavailable. "
        "Run `dfx killall && dfx start --background --clean` in the project root, "
        "or delete this project and deploy fresh on mainnet (Wallet → Convert cycles)."
    )
