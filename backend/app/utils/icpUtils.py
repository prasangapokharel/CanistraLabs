"""ICP/dfx integration utilities for canister management."""

import json
import re
import subprocess
import logging
import fcntl
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
import tempfile
import shutil
import os

from app.config import settings
from app.utils.canisterNetwork import network_for_canister
from app.utils.cycleRequirements import (
    MAINNET_RECOMMENDED_CYCLES,
    build_insufficient_cycles_error,
)

logger = logging.getLogger(__name__)

ASSET_CANISTER_NAME = "site"
DEPLOY_FILES_MARKER = "__ICP_FILES__:"
DFX_DEPLOY_LOCK_PATH = Path(tempfile.gettempdir()) / "icp-hosting-dfx-deploy.lock"


@contextmanager
def _dfx_deploy_lock():
    """Cross-process exclusive lock for dfx deploy operations."""
    DFX_DEPLOY_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DFX_DEPLOY_LOCK_PATH, "a+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


class ICPError(Exception):
    """Base exception for ICP-related errors."""

    pass


class DfxNotInstalledException(ICPError):
    """Raised when dfx is not installed."""

    pass


class CanisterCreationException(ICPError):
    """Raised when canister creation fails."""

    pass


class CanisterDeploymentException(ICPError):
    """Raised when canister deployment fails."""

    pass


class ICPService:
    """Service for managing ICP canisters and deployments."""

    @staticmethod
    def get_network() -> str:
        return settings.effective_deploy_network

    @staticmethod
    def _check_dfx_installed() -> bool:
        """Check if dfx is installed and available."""
        try:
            subprocess.run(["dfx", "--version"], capture_output=True, check=True, timeout=5)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            # Try the common installation path
            dfx_path = Path.home() / ".local" / "bin" / "dfx"
            if dfx_path.exists():
                return True
            return False

    @staticmethod
    def _get_dfx_path() -> str:
        """Get the path to dfx executable."""
        # Try the common installation path first
        dfx_path = Path.home() / ".local" / "bin" / "dfx"
        if dfx_path.exists():
            return str(dfx_path)
        # Fall back to PATH
        return "dfx"

    @staticmethod
    def _run_dfx_command(
        args: list, cwd: Optional[str] = None, timeout: int = 300
    ) -> Tuple[int, str, str]:
        """
        Run a dfx command and return the output.

        Args:
            args: List of dfx command arguments (dfx is prepended automatically)
            cwd: Working directory for the command
            timeout: Command timeout in seconds

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        dfx_path = ICPService._get_dfx_path()
        cmd = [dfx_path] + args
        logger.info(f"Running command: {' '.join(cmd)}")

        try:
            # Set up environment to ensure dfx has PATH and proper settings
            env = os.environ.copy()
            env["PATH"] = f"{Path.home() / '.local' / 'bin'}:{env.get('PATH', '')}"
            # Suppress the mainnet plaintext identity warning
            env["DFX_WARNING"] = "-mainnet_plaintext_identity"

            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            logger.error(f"dfx command timed out after {timeout}s: {' '.join(cmd)}")
            raise ICPError(f"dfx command timed out: {' '.join(cmd)}")
        except Exception as e:
            logger.error(f"Error running dfx command: {e}")
            raise ICPError(f"Error running dfx command: {str(e)}")

    @staticmethod
    def _run_dfx_command_with_input(
        args: List[str], input_text: str, cwd: Optional[str] = None, timeout: int = 60
    ) -> subprocess.CompletedProcess:
        """
        Run a dfx command with stdin input.

        Args:
            args: Arguments to pass to dfx
            input_text: Text to pass to stdin
            cwd: Working directory
            timeout: Timeout in seconds

        Returns:
            Completed subprocess result
        """
        dfx_path = ICPService._get_dfx_path()
        cmd = [dfx_path] + args
        logger.info(f"Running command with input: {' '.join(cmd)}")

        try:
            # Set up environment to ensure dfx has PATH and proper settings
            env = os.environ.copy()
            env["PATH"] = f"{Path.home() / '.local' / 'bin'}:{env.get('PATH', '')}"
            # Suppress the mainnet plaintext identity warning
            env["DFX_WARNING"] = "-mainnet_plaintext_identity"

            result = subprocess.run(
                cmd,
                cwd=cwd,
                input=input_text,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
            )
            return result
        except subprocess.TimeoutExpired:
            logger.error(f"dfx command timed out after {timeout}s: {' '.join(cmd)}")
            raise ICPError(f"dfx command timed out: {' '.join(cmd)}")
        except Exception as e:
            logger.error(f"Error running dfx command: {e}")
            raise ICPError(f"Error running dfx command: {str(e)}")

    @staticmethod
    def create_canister(project_name: str, code_content: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new canister on the ICP.

        Args:
            project_name: Name of the project (used as canister name)
            code_content: Optional Motoko code to deploy

        Returns:
            Dictionary containing canister_id, principal_id, and other metadata

        Raises:
            DfxNotInstalledException: If dfx is not installed
            CanisterCreationException: If canister creation fails
        """
        if not ICPService._check_dfx_installed():
            raise DfxNotInstalledException("dfx is not installed or not in PATH")

        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                # Create a new dfx project
                project_dir = Path(tmpdir) / project_name

                returncode, stdout, stderr = ICPService._run_dfx_command(
                    ["new", "--no-frontend", str(project_dir)],
                    cwd=tmpdir,
                )

                if returncode != 0:
                    raise CanisterCreationException(f"Failed to create dfx project: {stderr}")

                # If code_content is provided, replace the default code
                if code_content:
                    canister_src = project_dir / "src" / "main.mo"
                    canister_src.write_text(code_content)

                # Deploy the canister
                returncode, stdout, stderr = ICPService._run_dfx_command(
                    ["deploy", "--network", ICPService.get_network()],
                    cwd=str(project_dir),
                )

                if returncode != 0:
                    raise CanisterDeploymentException(f"Failed to deploy canister: {stderr}")

                # Parse the deployment output to extract canister ID and principal
                canister_id = ICPService._extract_canister_id(stdout)
                principal_id = settings.wallet_principal_id

                if not canister_id:
                    raise CanisterDeploymentException(
                        "Could not extract canister ID from deployment output"
                    )

                logger.info(f"Successfully created canister: {canister_id}")

                return {
                    "canister_id": canister_id,
                    "principal_id": principal_id,
                    "project_name": project_name,
                    "status": "deployed",
                    "network": ICPService.get_network(),
                }

            except (CanisterCreationException, CanisterDeploymentException):
                raise
            except Exception as e:
                logger.error(f"Unexpected error during canister creation: {e}")
                raise CanisterCreationException(f"Unexpected error: {str(e)}")

    @staticmethod
    def _dfx_networks_config() -> dict:
        return {
            "local": {"bind": "127.0.0.1:4943", "type": "ephemeral"},
            "ic": {"providers": ["https://ic0.app"], "type": "persistent"},
        }

    @staticmethod
    def _parse_deploy_content(code_content: str) -> Dict[str, str]:
        """Parse bundled HTML or multi-file deploy payload into asset paths."""
        content = code_content or ""
        if content.startswith(DEPLOY_FILES_MARKER):
            try:
                files = json.loads(content[len(DEPLOY_FILES_MARKER) :])
                if isinstance(files, dict) and files:
                    return {str(path): str(body) for path, body in files.items()}
            except json.JSONDecodeError:
                logger.warning("Invalid multi-file deploy payload; using index.html fallback")
        return {"index.html": content}

    @staticmethod
    def canister_public_url(canister_id: str, network: Optional[str] = None) -> str:
        """Public HTTP URL for a deployed canister (local replica or IC mainnet)."""
        cid = canister_id.strip()
        net = network or network_for_canister(canister_id)
        if net == "local":
            return f"http://{cid}.localhost:4943/"
        return f"https://{cid}.icp0.io/"

    @staticmethod
    def _write_asset_project(
        project_dir: Path,
        assets: Dict[str, str],
        network: str,
        canister_id: Optional[str] = None,
    ) -> None:
        """Prepare a minimal dfx project that deploys static assets."""
        assets_dir = project_dir / "src" / ASSET_CANISTER_NAME / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)

        for rel_path, body in assets.items():
            rel = rel_path.lstrip("/").replace("\\", "/")
            if ".." in rel.split("/"):
                raise CanisterDeploymentException(f"Invalid asset path: {rel_path}")
            target = assets_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")

        # Optional config — omit to use dfx defaults (avoids malformed json5 errors).
        dfx_json = {
            "canisters": {
                ASSET_CANISTER_NAME: {
                    "type": "assets",
                    "source": [f"src/{ASSET_CANISTER_NAME}/assets"],
                }
            },
            "networks": ICPService._dfx_networks_config(),
        }
        (project_dir / "dfx.json").write_text(json.dumps(dfx_json, indent=2))

        if canister_id:
            ids_dir = project_dir / ".dfx" / network
            ids_dir.mkdir(parents=True, exist_ok=True)
            (ids_dir / "canister_ids.json").write_text(
                json.dumps({ASSET_CANISTER_NAME: {network: canister_id}}, indent=2)
            )

    @staticmethod
    def _deploy_asset_canister(
        project_dir: Path,
        network: str,
        canister_id: Optional[str] = None,
        available_cycles: Optional[int] = None,
    ) -> str:
        """Deploy or upgrade the asset canister; return the canister ID."""
        base_cmd = ["deploy", ASSET_CANISTER_NAME, "--network", network, "--yes"]
        if network == "ic" and not canister_id and available_cycles:
            # Cap at recommended amount; dfx deducts creation fee from this deposit.
            with_cycles = min(available_cycles, MAINNET_RECOMMENDED_CYCLES)
            base_cmd.extend(["--with-cycles", str(with_cycles)])

        with _dfx_deploy_lock():
            if canister_id:
                cmd = base_cmd + ["--mode", "reinstall"]
                returncode, stdout, stderr = ICPService._run_dfx_command(
                    cmd, cwd=str(project_dir)
                )
                output = f"{stdout}\n{stderr}"
            else:
                returncode, stdout, stderr = ICPService._run_dfx_command(
                    base_cmd, cwd=str(project_dir)
                )
                output = f"{stdout}\n{stderr}"
                if returncode != 0:
                    err_text = stderr or stdout
                    if "insufficient cycles" in err_text.lower():
                        err = build_insufficient_cycles_error(
                            available_cycles or 0, err_text
                        )
                        raise CanisterDeploymentException(err["message"])
                    raise CanisterDeploymentException(
                        f"Failed to deploy asset canister: {err_text}"
                    )

                deployed_id = ICPService._extract_canister_id(output)
                if not deployed_id:
                    raise CanisterDeploymentException(
                        "Could not extract canister ID from asset deployment output"
                    )

                # New canisters: first install creates the ID but assets often 503
                # until a reinstall syncs files (local dfx quirk).
                ids_dir = project_dir / ".dfx" / network
                ids_dir.mkdir(parents=True, exist_ok=True)
                (ids_dir / "canister_ids.json").write_text(
                    json.dumps({ASSET_CANISTER_NAME: {network: deployed_id}}, indent=2)
                )
                returncode, stdout2, stderr2 = ICPService._run_dfx_command(
                    base_cmd + ["--mode", "reinstall"],
                    cwd=str(project_dir),
                )
                output = f"{output}\n{stdout2}\n{stderr2}"

            if returncode != 0:
                raise CanisterDeploymentException(
                    f"Failed to deploy asset canister: {stderr or stdout}"
                )

        deployed_id = ICPService._extract_canister_id(output) or canister_id
        if not deployed_id:
            raise CanisterDeploymentException(
                "Could not extract canister ID from asset deployment output"
            )
        ICPService._verify_canister_serves(deployed_id, network)
        return deployed_id

    @staticmethod
    def _verify_canister_serves(canister_id: str, network: str, attempts: int = 5) -> None:
        """Confirm the asset canister returns HTTP 200 for index after deploy."""
        url = ICPService.canister_public_url(canister_id, network)
        last_error = "unknown"
        for attempt in range(attempts):
            try:
                with urllib.request.urlopen(url, timeout=15) as response:
                    if response.status == 200:
                        return
                    last_error = f"HTTP {response.status}"
            except urllib.error.HTTPError as exc:
                last_error = f"HTTP {exc.code}"
            except Exception as exc:
                last_error = str(exc)
            if attempt < attempts - 1:
                time.sleep(1.5)
        raise CanisterDeploymentException(
            f"Canister {canister_id} deployed but site is not reachable ({last_error}). "
            "Click Publish again or check that dfx is running."
        )

    @staticmethod
    def _find_built_wasm(project_dir: Path, network: str) -> Path:
        for name in ("main.wasm.gz", "main.wasm"):
            wasm_file = project_dir / ".dfx" / network / "canisters" / "main" / name
            if wasm_file.exists():
                return wasm_file
        raise CanisterDeploymentException("Failed to find built wasm file after dfx build")

    @staticmethod
    def update_canister(canister_id: str, code_content: str) -> Dict[str, Any]:
        """
        Update an existing canister with new static assets (HTML/CSS/JS).

        Args:
            canister_id: The canister ID to update
            code_content: Bundled HTML or __ICP_FILES__ multi-file payload

        Returns:
            Dictionary with update status and metadata

        Raises:
            CanisterDeploymentException: If update fails
        """
        if not ICPService._check_dfx_installed():
            raise DfxNotInstalledException("dfx is not installed or not in PATH")

        network = network_for_canister(canister_id)
        assets = ICPService._parse_deploy_content(code_content)

        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                project_dir = Path(tmpdir) / "project"
                project_dir.mkdir()
                ICPService._write_asset_project(
                    project_dir, assets, network, canister_id=canister_id
                )
                deployed_id = ICPService._deploy_asset_canister(
                    project_dir, network, canister_id=canister_id
                )

                logger.info(f"Successfully updated asset canister: {deployed_id}")

                return {
                    "canister_id": deployed_id,
                    "url": ICPService.canister_public_url(deployed_id, network),
                    "status": "updated",
                    "timestamp": None,
                }

            except CanisterDeploymentException:
                raise
            except Exception as e:
                logger.error(f"Error updating canister: {e}")
                raise CanisterDeploymentException(f"Error updating canister: {str(e)}")

    @staticmethod
    def deploy_to_shared_canister(
        canister_id: str, project_path: str, code_content: str
    ) -> Dict[str, Any]:
        """
        Deploy files to a shared canister under a project-specific path.

        All projects share one canister and are organized by path:
        https://canister_id.ic0.app/project-{id}/

        Args:
            canister_id: The shared canister ID
            project_path: Project-specific path (e.g., "project-123")
            code_content: HTML/CSS/JS content or Motoko code

        Returns:
            Dictionary with deployment status

        Raises:
            CanisterDeploymentException: If deployment fails
        """
        if not ICPService._check_dfx_installed():
            raise DfxNotInstalledException("dfx is not installed or not in PATH")

        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                project_dir = Path(tmpdir) / "shared_deploy"
                project_dir.mkdir()

                # Create dfx.json for shared canister
                dfx_json = {
                    "canisters": {
                        "main": {
                            "type": "motoko",
                            "main": "src/main.mo",
                            "candid": "src/main.did",
                        }
                    },
                    "networks": {
                        "ic": {
                            "bind": "127.0.0.1:8000",
                            "type": "ephemeral",
                        }
                    },
                }

                (project_dir / "dfx.json").write_text(json.dumps(dfx_json, indent=2))

                # Create src directory
                src_dir = project_dir / "src"
                src_dir.mkdir()

                # Create Motoko wrapper that serves files from project path
                motoko_code = ICPService._create_path_router(project_path, code_content)
                src_dir.joinpath("main.mo").write_text(motoko_code)

                # Build the canister first
                returncode, stdout, stderr = ICPService._run_dfx_command(
                    ["build", "main", "--network", ICPService.get_network()],
                    cwd=str(project_dir),
                )

                if returncode != 0:
                    logger.warning(f"dfx build returned non-zero: {stderr}")
                    # Continue anyway, the wasm might still be built

                # Find the built wasm file
                wasm_file = (
                    project_dir
                    / ".dfx"
                    / ICPService.get_network()
                    / "canisters"
                    / "main"
                    / "main.wasm.gz"
                )
                if not wasm_file.exists():
                    # Try uncompressed
                    wasm_file = (
                        project_dir
                        / ".dfx"
                        / ICPService.get_network()
                        / "canisters"
                        / "main"
                        / "main.wasm"
                    )

                if not wasm_file.exists():
                    raise CanisterDeploymentException(
                        f"Failed to find built wasm file for canister {canister_id}"
                    )

                # Install the wasm to the shared canister
                returncode, stdout, stderr = ICPService._run_dfx_command(
                    [
                        "canister",
                        "install",
                        canister_id,
                        "--mode",
                        "upgrade",
                        "--wasm",
                        str(wasm_file),
                        "--network",
                        ICPService.get_network(),
                    ],
                    cwd=str(project_dir),
                )

                if returncode != 0:
                    raise CanisterDeploymentException(
                        f"Failed to deploy to shared canister {canister_id}: {stderr}"
                    )

                logger.info(f"Successfully deployed {project_path} to canister {canister_id}")

                return {
                    "canister_id": canister_id,
                    "project_path": project_path,
                    "status": "deployed",
                    "url": f"https://{canister_id}.ic0.app/{project_path}/",
                }

            except CanisterDeploymentException:
                raise
            except Exception as e:
                logger.error(f"Error deploying to shared canister: {e}")
                raise CanisterDeploymentException(f"Error deploying to shared canister: {str(e)}")

    @staticmethod
    def _create_path_router(project_path: str, content: str) -> str:
        """
        Create a Motoko canister that serves HTML content directly.

        Args:
            project_path: Project-specific path (e.g., "project-123" or "demo-app")
            content: HTML/CSS/JS content

        Returns:
            Motoko code that serves the content
        """
        # Escape special characters in content for Motoko string
        escaped_content = (
            content.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")
        )

        # Create a Motoko canister that serves HTML
        motoko_code = f'''
import Text "mo:base/Text";
import Blob "mo:base/Blob";
import Nat8 "mo:base/Nat8";
import Nat16 "mo:base/Nat16";

persistent actor {{
  let htmlContent = "{escaped_content}";

  public query func http_request(request : {{
    method : Text;
    url : Text;
    headers : [{{name : Text; value : Text}}];
    body : Blob;
  }}) : async {{
    body : Blob;
    headers : [{{name : Text; value : Text}}];
    status_code : Nat16;
  }} {{
    // Convert string to bytes
    let htmlBytes = Blob.toArray(Text.encodeUtf8(htmlContent));
    
    return {{
      body = Blob.fromArray(htmlBytes);
      headers = [
        {{"name" = "Content-Type"; "value" = "text/html; charset=utf-8"}},
        {{"name" = "Access-Control-Allow-Origin"; "value" = "*"}},
        {{"name" = "Cache-Control"; "value" = "public, max-age=3600"}},
        {{"name" = "Content-Length"; "value" = "{str(len(content))}"}},
      ];
      status_code = 200;
    }};
  }};
}};
'''
        return motoko_code

    @staticmethod
    def get_canister_status(canister_id: str) -> Dict[str, Any]:
        """
        Get the status of a canister.

        Args:
            canister_id: The canister ID to check

        Returns:
            Dictionary with canister status and metadata

        Raises:
            ICPError: If status check fails
        """
        if not ICPService._check_dfx_installed():
            raise DfxNotInstalledException("dfx is not installed or not in PATH")

        network = network_for_canister(canister_id)
        try:
            with _dfx_deploy_lock():
                returncode, stdout, stderr = ICPService._run_dfx_command(
                    ["canister", "status", canister_id, "--network", network],
                )

            if returncode != 0:
                raise ICPError(f"Failed to get canister status: {stderr}")

            # Parse status output
            status_data = ICPService._parse_canister_status(stdout)

            logger.info(f"Retrieved status for canister {canister_id}: {status_data}")

            return status_data

        except Exception as e:
            logger.error(f"Error getting canister status: {e}")
            raise ICPError(f"Error getting canister status: {str(e)}")

    @staticmethod
    def stop_canister(canister_id: str) -> Dict[str, Any]:
        """Stop a canister to reduce compute usage (site goes offline)."""
        if not ICPService._check_dfx_installed():
            raise DfxNotInstalledException("dfx is not installed or not in PATH")

        network = network_for_canister(canister_id)
        try:
            with _dfx_deploy_lock():
                returncode, stdout, stderr = ICPService._run_dfx_command(
                    ["canister", "stop", canister_id, "--network", network],
                )
            if returncode != 0:
                raise ICPError(f"Failed to stop canister: {stderr or stdout}")
            logger.info("Stopped canister %s on %s", canister_id, network)
            return {"canister_id": canister_id, "status": "stopped", "message": stdout.strip()}
        except ICPError:
            raise
        except Exception as e:
            raise ICPError(f"Error stopping canister: {str(e)}")

    @staticmethod
    def start_canister(canister_id: str) -> Dict[str, Any]:
        """Start a stopped canister."""
        if not ICPService._check_dfx_installed():
            raise DfxNotInstalledException("dfx is not installed or not in PATH")

        network = network_for_canister(canister_id)
        try:
            with _dfx_deploy_lock():
                returncode, stdout, stderr = ICPService._run_dfx_command(
                    ["canister", "start", canister_id, "--network", network],
                )
            if returncode != 0:
                raise ICPError(f"Failed to start canister: {stderr or stdout}")
            logger.info("Started canister %s on %s", canister_id, network)
            return {"canister_id": canister_id, "status": "running", "message": stdout.strip()}
        except ICPError:
            raise
        except Exception as e:
            raise ICPError(f"Error starting canister: {str(e)}")

    @staticmethod
    def delete_canister(canister_id: str) -> Dict[str, Any]:
        """
        Delete a canister from the ICP.

        Args:
            canister_id: The canister ID to delete

        Returns:
            Dictionary with deletion status

        Raises:
            ICPError: If deletion fails
        """
        if not ICPService._check_dfx_installed():
            raise DfxNotInstalledException("dfx is not installed or not in PATH")

        try:
            network = network_for_canister(canister_id)
            with _dfx_deploy_lock():
                returncode, stdout, stderr = ICPService._run_dfx_command(
                    [
                        "canister",
                        "delete",
                        canister_id,
                        "--network",
                        network,
                        "--yes",
                    ],
                )

            if returncode != 0:
                raise ICPError(f"Failed to delete canister: {stderr}")

            logger.info(f"Successfully deleted canister: {canister_id}")

            return {
                "canister_id": canister_id,
                "status": "deleted",
            }

        except Exception as e:
            logger.error(f"Error deleting canister: {e}")
            raise ICPError(f"Error deleting canister: {str(e)}")

    @staticmethod
    def _extract_canister_id(output: str) -> Optional[str]:
        """Extract canister ID from dfx output."""
        # Look for patterns like:
        # - "canister created with canister id: abc-123..."
        # - "Upgraded code for canister testcanister_backend, with canister ID abc-123"
        # - "Installed code for canister testcanister_backend, with canister ID abc-123"
        # - "canisterId=abc-123"

        import re

        # Pattern 1: Look for lines with "canister id:" or "canister ID:" followed by an ID
        for line in output.split("\n"):
            # "with canister id: xxx-xxx-..." or "with canister ID xxx-xxx-..."
            if "canister" in line.lower() and ("id:" in line.lower() or "id " in line.lower()):
                # Extract the ID using regex - look for pattern like xxx-xxx-xxx-xxx-xxx
                match = re.search(
                    r"([a-z0-9]+-[a-z0-9]+-[a-z0-9]+-[a-z0-9]+-[a-z0-9]+)", line.lower()
                )
                if match:
                    return match.group(1)

            # "canisterId=xxx-xxx-..."
            if "canisterid=" in line.lower():
                parts = line.split("=")
                candidate = parts[-1].strip().split("&")[0]
                match = re.search(
                    r"([a-z0-9]+-[a-z0-9]+-[a-z0-9]+-[a-z0-9]+-[a-z0-9]+)", candidate.lower()
                )
                if match:
                    return match.group(1)

        # Fallback: look for any canister ID pattern in the output
        match = re.search(r"([a-z0-9]+-[a-z0-9]+-[a-z0-9]+-[a-z0-9]+-[a-z0-9]+)", output.lower())
        if match:
            return match.group(1)

        return None

    @staticmethod
    def _parse_int_token(value: str) -> int:
        cleaned = value.replace("_", "").replace(",", "").strip()
        if cleaned.lower().startswith("nat(") and cleaned.endswith(")"):
            cleaned = cleaned[4:-1]
        return int(cleaned)

    @staticmethod
    def _parse_cycles_amount(text: str) -> int:
        """Parse cycle amounts including TC/BC/MC suffixes from dfx output."""
        line = text.lower().strip()
        tc_match = re.search(r"([\d_.]+)\s*tc\b", line)
        if tc_match:
            return int(float(tc_match.group(1).replace("_", "")) * 1_000_000_000_000)
        bc_match = re.search(r"([\d_.]+)\s*bc\b", line)
        if bc_match:
            return int(float(bc_match.group(1).replace("_", "")) * 1_000_000_000)
        mc_match = re.search(r"([\d_.]+)\s*mc\b", line)
        if mc_match:
            return int(float(mc_match.group(1).replace("_", "")) * 1_000_000)
        num_match = re.search(r"([\d_,]+)\s*cycles", line)
        if num_match:
            return ICPService._parse_int_token(num_match.group(1))
        plain = re.search(r"balance:\s*([\d_,]+)", line)
        if plain:
            return ICPService._parse_int_token(plain.group(1))
        return 0

    @staticmethod
    def _parse_canister_status(output: str) -> Dict[str, Any]:
        """Parse full ``dfx canister status`` output — all fields ICP exposes."""
        status_data: Dict[str, Any] = {
            "status": "unknown",
            "cycles": 0,
            "cycles_balance": 0,
            "memory_usage": 0,
            "memory_size": 0,
            "idle_cycles_burned_per_day": 0,
            "freezing_threshold_seconds": 0,
            "reserved_cycles": 0,
            "reserved_cycles_limit": 0,
            "compute_allocation": 0,
            "memory_allocation": 0,
            "number_of_queries": 0,
            "instructions_spent_in_queries": 0,
            "query_request_payload_bytes": 0,
            "query_response_payload_bytes": 0,
            "module_hash": None,
            "controllers": [],
            "raw_output": output.strip(),
        }

        for line in output.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue
            lower = stripped.lower()

            if lower.startswith("status:"):
                status_data["status"] = stripped.split(":", 1)[1].strip()
                continue

            if lower.startswith("controllers:"):
                controllers = stripped.split(":", 1)[1].strip()
                status_data["controllers"] = [c for c in controllers.split() if c]
                continue

            if lower.startswith("memory allocation:"):
                try:
                    status_data["memory_allocation"] = ICPService._parse_int_token(
                        stripped.split(":", 1)[1]
                    )
                except ValueError:
                    pass
                continue

            if lower.startswith("compute allocation:"):
                try:
                    status_data["compute_allocation"] = ICPService._parse_int_token(
                        stripped.split(":", 1)[1]
                    )
                except ValueError:
                    pass
                continue

            if lower.startswith("freezing threshold:"):
                try:
                    status_data["freezing_threshold_seconds"] = ICPService._parse_int_token(
                        stripped.split(":", 1)[1]
                    )
                except ValueError:
                    pass
                continue

            if "idle cycles burned per day" in lower:
                try:
                    status_data["idle_cycles_burned_per_day"] = ICPService._parse_int_token(
                        stripped.split(":", 1)[1]
                    )
                except ValueError:
                    pass
                continue

            if lower.startswith("memory size:") or lower.startswith("memory used:"):
                try:
                    memory = ICPService._parse_int_token(stripped.split(":", 1)[1])
                    status_data["memory_usage"] = memory
                    status_data["memory_size"] = memory
                except ValueError:
                    pass
                continue

            if lower.startswith("balance:"):
                cycles = ICPService._parse_cycles_amount(stripped)
                status_data["cycles"] = cycles
                status_data["cycles_balance"] = cycles
                continue

            if lower.startswith("reserved:") and "limit" not in lower:
                try:
                    status_data["reserved_cycles"] = ICPService._parse_cycles_amount(stripped)
                except ValueError:
                    pass
                continue

            if "reserved cycles limit" in lower:
                try:
                    status_data["reserved_cycles_limit"] = ICPService._parse_cycles_amount(stripped)
                except ValueError:
                    pass
                continue

            if lower.startswith("number of queries:"):
                try:
                    status_data["number_of_queries"] = ICPService._parse_int_token(
                        stripped.split(":", 1)[1]
                    )
                except ValueError:
                    pass
                continue

            if lower.startswith("instructions spent in queries:"):
                try:
                    status_data["instructions_spent_in_queries"] = ICPService._parse_int_token(
                        stripped.split(":", 1)[1]
                    )
                except ValueError:
                    pass
                continue

            if "total query request payload size" in lower:
                try:
                    status_data["query_request_payload_bytes"] = ICPService._parse_int_token(
                        stripped.split(":", 1)[1]
                    )
                except ValueError:
                    pass
                continue

            if "total query response payload size" in lower:
                try:
                    status_data["query_response_payload_bytes"] = ICPService._parse_int_token(
                        stripped.split(":", 1)[1]
                    )
                except ValueError:
                    pass
                continue

            if lower.startswith("module hash:"):
                status_data["module_hash"] = stripped.split(":", 1)[1].strip()
                continue

        return status_data

    @staticmethod
    def create_individual_canister(
        project_name: str,
        html_content: str,
        available_cycles: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create a new individual asset canister for a project.

        Each project gets its own asset canister that serves HTML/CSS/JS locally
        or on IC mainnet depending on ``effective_deploy_network``.

        Args:
            project_name: Name of the project (for logging)
            html_content: Bundled HTML or __ICP_FILES__ multi-file payload

        Returns:
            Dictionary containing canister_id, principal_id, url, and other metadata

        Raises:
            DfxNotInstalledException: If dfx is not installed
            CanisterCreationException: If canister creation fails
        """
        if not ICPService._check_dfx_installed():
            raise DfxNotInstalledException("dfx is not installed or not in PATH")

        network = settings.effective_deploy_network
        assets = ICPService._parse_deploy_content(html_content)

        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                project_dir = Path(tmpdir) / "project"
                project_dir.mkdir()

                logger.info(
                    f"Creating asset canister for project: {project_name} "
                    f"({len(assets)} file(s), network={network})"
                )

                ICPService._write_asset_project(project_dir, assets, network)
                canister_id = ICPService._deploy_asset_canister(
                    project_dir, network, available_cycles=available_cycles
                )
                canister_url = ICPService.canister_public_url(canister_id, network)

                total_bytes = sum(len(body) for body in assets.values())
                logger.info(f"Successfully created asset canister: {canister_id}")

                return {
                    "canister_id": canister_id,
                    "principal_id": settings.wallet_principal_id,
                    "project_name": project_name,
                    "url": canister_url,
                    "status": "deployed",
                    "network": network,
                    "html_size_bytes": total_bytes,
                }

            except (CanisterCreationException, CanisterDeploymentException):
                raise
            except Exception as e:
                logger.error(f"Unexpected error during individual canister creation: {e}")
                raise CanisterCreationException(f"Unexpected error: {str(e)}")

    @staticmethod
    def _generate_html_serving_motoko(html_content: str) -> str:
        """
        Generate Motoko code that serves HTML content directly.

        Creates a Motoko canister that implements the HTTP request interface
        to serve HTML with proper headers.

        Args:
            html_content: HTML content to embed and serve

        Returns:
            Motoko code as a string
        """
        # Escape special characters in content for Motoko string
        escaped_content = (
            html_content.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")
        )

        # Truncate if too large (Motoko has limits on string literals)
        max_size = 2_000_000  # 2MB limit for safety
        if len(escaped_content) > max_size:
            logger.warning(f"HTML content exceeds {max_size} bytes, will be truncated")
            escaped_content = escaped_content[:max_size]

        # Create a Motoko canister that serves HTML via HTTP interface
        # Use .replace() — Motoko record syntax `{name = ...}` breaks Python f-strings (PEP 701)
        content_len = str(len(html_content))
        motoko_code = (
            """
import Text "mo:base/Text";
import Blob "mo:base/Blob";
import Nat16 "mo:base/Nat16";

persistent actor {
  let htmlContent = "__HTML__";

  public query func http_request(request : {
    method : Text;
    url : Text;
    headers : [{name : Text; value : Text}];
    body : Blob;
  }) : async {
    body : Blob;
    headers : [{name : Text; value : Text}];
    status_code : Nat16;
  } {
    let htmlBytes = Blob.toArray(Text.encodeUtf8(htmlContent));
    return {
      body = Blob.fromArray(htmlBytes);
      headers = [
        {name = "Content-Type"; value = "text/html; charset=utf-8"},
        {name = "Access-Control-Allow-Origin"; value = "*"},
        {name = "Cache-Control"; value = "public, max-age=3600"},
        {name = "Content-Length"; value = "__LEN__"},
      ];
      status_code = 200 : Nat16;
    };
  };
};
"""
            .replace("__HTML__", escaped_content)
            .replace("__LEN__", content_len)
        )
        return motoko_code
