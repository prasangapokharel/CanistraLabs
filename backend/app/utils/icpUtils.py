"""ICP/dfx integration utilities for canister management."""

import json
import subprocess
import logging
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
import tempfile
import shutil
import os

from app.config import settings

logger = logging.getLogger(__name__)


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

    DFX_NETWORK = "local"  # Use local for testing; change to "ic" for production

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
                    ["deploy", "--network", ICPService.DFX_NETWORK],
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
                    "network": ICPService.DFX_NETWORK,
                }

            except (CanisterCreationException, CanisterDeploymentException):
                raise
            except Exception as e:
                logger.error(f"Unexpected error during canister creation: {e}")
                raise CanisterCreationException(f"Unexpected error: {str(e)}")

    @staticmethod
    def update_canister(canister_id: str, code_content: str) -> Dict[str, Any]:
        """
        Update an existing canister's code.

        Args:
            canister_id: The canister ID to update
            code_content: New Motoko code to deploy

        Returns:
            Dictionary with update status and metadata

        Raises:
            CanisterDeploymentException: If update fails
        """
        if not ICPService._check_dfx_installed():
            raise DfxNotInstalledException("dfx is not installed or not in PATH")

        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                project_dir = Path(tmpdir) / "project"
                project_dir.mkdir()

                # Create a minimal dfx.json for existing canister
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

                # Create src directory and files
                src_dir = project_dir / "src"
                src_dir.mkdir()
                src_dir.joinpath("main.mo").write_text(code_content)

                # Update the canister
                returncode, stdout, stderr = ICPService._run_dfx_command(
                    [
                        "canister",
                        "install",
                        canister_id,
                        "--mode",
                        "upgrade",
                        "--network",
                        ICPService.DFX_NETWORK,
                    ],
                    cwd=str(project_dir),
                )

                if returncode != 0:
                    raise CanisterDeploymentException(
                        f"Failed to update canister {canister_id}: {stderr}"
                    )

                logger.info(f"Successfully updated canister: {canister_id}")

                return {
                    "canister_id": canister_id,
                    "status": "updated",
                    "timestamp": None,  # Would use datetime.utcnow() in production
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
                    ["build", "main", "--network", ICPService.DFX_NETWORK],
                    cwd=str(project_dir),
                )

                if returncode != 0:
                    logger.warning(f"dfx build returned non-zero: {stderr}")
                    # Continue anyway, the wasm might still be built

                # Find the built wasm file
                wasm_file = (
                    project_dir
                    / ".dfx"
                    / ICPService.DFX_NETWORK
                    / "canisters"
                    / "main"
                    / "main.wasm.gz"
                )
                if not wasm_file.exists():
                    # Try uncompressed
                    wasm_file = (
                        project_dir
                        / ".dfx"
                        / ICPService.DFX_NETWORK
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
                        ICPService.DFX_NETWORK,
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

actor {{
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

        try:
            returncode, stdout, stderr = ICPService._run_dfx_command(
                ["canister", "status", canister_id, "--network", ICPService.DFX_NETWORK],
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
            returncode, stdout, stderr = ICPService._run_dfx_command(
                ["canister", "delete", canister_id, "--network", ICPService.DFX_NETWORK],
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
    def _parse_canister_status(output: str) -> Dict[str, Any]:
        """Parse canister status from dfx output."""
        status_data = {
            "status": "running",
            "cycles": 0,
            "memory_usage": 0,
        }

        # Parse output for status information
        lines = output.split("\n")
        for line in lines:
            line_lower = line.lower()
            if "running" in line_lower:
                status_data["status"] = "running"
            elif "stopped" in line_lower:
                status_data["status"] = "stopped"
            elif "cycles" in line_lower:
                try:
                    # Try to extract numeric value
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if "cycles" in part.lower() and i + 1 < len(parts):
                            status_data["cycles"] = int(parts[i + 1])
                except (ValueError, IndexError):
                    pass

        return status_data

    @staticmethod
    def create_individual_canister(project_name: str, html_content: str) -> Dict[str, Any]:
        """
        Create a new individual canister for a project with HTML content.

        This creates a unique canister per project that serves HTML directly.
        Each canister gets its own unique ID and URL.

        Args:
            project_name: Name of the project (sanitized for dfx project name)
            html_content: HTML content to serve from the canister

        Returns:
            Dictionary containing canister_id, principal_id, url, and other metadata

        Raises:
            DfxNotInstalledException: If dfx is not installed
            CanisterCreationException: If canister creation fails
        """
        if not ICPService._check_dfx_installed():
            raise DfxNotInstalledException("dfx is not installed or not in PATH")

        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                # Sanitize project name for dfx project name (alphanumeric + underscore)
                sanitized_name = "".join(
                    c if c.isalnum() or c == "_" else "_" for c in project_name
                )
                sanitized_name = sanitized_name.lstrip("_")[
                    :30
                ]  # Max 30 chars, remove leading underscores

                if not sanitized_name:
                    sanitized_name = "project"

                project_dir = Path(tmpdir) / sanitized_name

                logger.info(f"Creating individual canister for project: {project_name}")

                # Create a new dfx project (use sanitized_name, not full path)
                returncode, stdout, stderr = ICPService._run_dfx_command(
                    ["new", "--no-frontend", sanitized_name],
                    cwd=tmpdir,
                )

                if returncode != 0:
                    raise CanisterCreationException(f"Failed to create dfx project: {stderr}")

                # Generate Motoko code that serves HTML
                motoko_code = ICPService._generate_html_serving_motoko(html_content)
                canister_src = project_dir / "src" / "main.mo"
                canister_src.write_text(motoko_code)

                logger.info(f"Generated Motoko code for HTML serving ({len(html_content)} bytes)")

                # Deploy the canister
                # Use "ic" for production mainnet deployment
                network = "ic"  # Production mainnet deployment
                returncode, stdout, stderr = ICPService._run_dfx_command(
                    ["deploy", "--network", network],
                    cwd=str(project_dir),
                )

                if returncode != 0:
                    raise CanisterDeploymentException(f"Failed to deploy canister: {stderr}")

                logger.info(f"Deployment output:\n{stdout}")
                logger.info(f"Deployment stderr:\n{stderr}")

                # Parse the deployment output to extract canister ID
                canister_id = ICPService._extract_canister_id(stdout)

                # If not found in stdout, try stderr
                if not canister_id:
                    canister_id = ICPService._extract_canister_id(stderr)
                    if canister_id:
                        logger.info(f"Canister ID found in stderr: {canister_id}")

                if not canister_id:
                    logger.error(
                        f"Could not extract canister ID from output:\nstdout: {stdout}\nstderr: {stderr}"
                    )
                    raise CanisterDeploymentException(
                        "Could not extract canister ID from deployment output"
                    )

                # Generate the canister URL
                canister_url = f"https://{canister_id}.icp0.io"

                logger.info(f"Successfully created individual canister: {canister_id}")

                return {
                    "canister_id": canister_id,
                    "principal_id": settings.wallet_principal_id,
                    "project_name": project_name,
                    "url": canister_url,
                    "status": "deployed",
                    "network": network,
                    "html_size_bytes": len(html_content),
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
        motoko_code = f'''
import Text "mo:base/Text";
import Blob "mo:base/Blob";
import Nat8 "mo:base/Nat8";

actor {{
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
    // Convert string to bytes for HTTP response
    let htmlBytes = Blob.toArray(Text.encodeUtf8(htmlContent));
    
    return {{
      body = Blob.fromArray(htmlBytes);
      headers = [
        {{"name" = "Content-Type"; "value" = "text/html; charset=utf-8"}},
        {{"name" = "Access-Control-Allow-Origin"; "value" = "*"}},
        {{"name" = "Cache-Control"; "value" = "public, max-age=3600"}},
        {{"name" = "Content-Length"; "value" = "{str(len(html_content))}"}},
      ];
      status_code = 200;
    }};
  }};
}};
'''
        return motoko_code
