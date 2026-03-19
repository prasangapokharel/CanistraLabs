"""Clean dfx command mapping service - minimal and essential only."""

import subprocess
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


class DfxCommand:
    """
    Clean, minimal dfx command mapper.
    Maps all dfx operations to simple Python functions with clear naming.
    """

    def __init__(self, network: str = "ic"):
        """Initialize with network (ic for mainnet, local for development)."""
        self.network = network
        self.dfxPath = self._getDfxPath()

    def _getDfxPath(self) -> str:
        """Get dfx executable path."""
        dfxPath = Path.home() / ".local" / "bin" / "dfx"
        return str(dfxPath) if dfxPath.exists() else "dfx"

    def _runCommand(self, args: List[str], identity: Optional[str] = None) -> Tuple[int, str, str]:
        """
        Execute dfx command with proper environment.

        Args:
            args: dfx command arguments
            identity: optional identity to use

        Returns:
            (returncode, stdout, stderr)
        """
        cmd = [self.dfxPath] + args
        if identity:
            cmd.extend(["--identity", identity])

        env = os.environ.copy()
        env["PATH"] = f"{Path.home() / '.local' / 'bin'}:{env.get('PATH', '')}"
        env["DFX_WARNING"] = "-mainnet_plaintext_identity"

        logger.info(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=300)
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            logger.error(f"Command failed: {e}")
            return 1, "", str(e)

    # =========================
    # IDENTITY COMMANDS
    # =========================

    def identityList(self) -> Dict[str, Any]:
        """List all identities: dfx identity list"""
        returncode, stdout, stderr = self._runCommand(["identity", "list"])

        identities = []
        current = None

        if returncode == 0:
            for line in stdout.strip().split("\n"):
                line = line.strip()
                if line:
                    if line.endswith(" *"):
                        current = line[:-2]
                        identities.append(line[:-2])
                    else:
                        identities.append(line)

        return {
            "success": returncode == 0,
            "identities": identities,
            "current": current,
            "error": stderr if returncode != 0 else None,
        }

    def identityNew(self, name: str) -> Dict[str, Any]:
        """Create new identity: dfx identity new <name>"""
        returncode, stdout, stderr = self._runCommand(["identity", "new", name])

        result = {"success": returncode == 0, "identityName": name}

        if returncode == 0:
            # Get principal and account ID
            result.update(self.identityGetPrincipal(name))
            result.update(self.ledgerGetAccountId(name))
        else:
            result["error"] = stderr

        return result

    def identityUse(self, name: str) -> Dict[str, Any]:
        """Switch identity: dfx identity use <name>"""
        returncode, stdout, stderr = self._runCommand(["identity", "use", name])

        return {
            "success": returncode == 0,
            "identityName": name,
            "message": stdout.strip() if returncode == 0 else stderr,
        }

    def identityWhoami(self) -> Dict[str, Any]:
        """Get current identity: dfx identity whoami"""
        returncode, stdout, stderr = self._runCommand(["identity", "whoami"])

        return {
            "success": returncode == 0,
            "current": stdout.strip() if returncode == 0 else None,
            "error": stderr if returncode != 0 else None,
        }

    def identityGetPrincipal(self, identity: Optional[str] = None) -> Dict[str, Any]:
        """Get principal ID: dfx identity get-principal"""
        returncode, stdout, stderr = self._runCommand(["identity", "get-principal"], identity)

        return {
            "success": returncode == 0,
            "principalId": stdout.strip() if returncode == 0 else None,
            "error": stderr if returncode != 0 else None,
        }

    def identityExport(self, name: str) -> Dict[str, Any]:
        """Export identity: dfx identity export <name>"""
        returncode, stdout, stderr = self._runCommand(["identity", "export", name])

        return {
            "success": returncode == 0,
            "privateKey": stdout.strip() if returncode == 0 else None,
            "error": stderr if returncode != 0 else None,
        }

    def identityUse(self, name: str) -> Dict[str, Any]:
        """Use identity: dfx identity use <name>"""
        returncode, stdout, stderr = self._runCommand(["identity", "use", name])

        return {
            "success": returncode == 0,
            "identity": name,
            "output": stdout.strip() if returncode == 0 else None,
            "error": stderr if returncode != 0 else None,
        }

    # =========================
    # LEDGER COMMANDS (ICP)
    # =========================

    def ledgerGetAccountId(self, identity: Optional[str] = None) -> Dict[str, Any]:
        """Get account ID: dfx ledger account-id"""
        returncode, stdout, stderr = self._runCommand(
            ["ledger", "account-id", "--network", self.network], identity
        )

        return {
            "success": returncode == 0,
            "accountId": stdout.strip() if returncode == 0 else None,
            "error": stderr if returncode != 0 else None,
        }

    def ledgerGetBalance(
        self, accountId: Optional[str] = None, identity: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get ICP balance: dfx ledger balance [account_id]"""
        cmd = ["ledger", "balance", "--network", self.network]
        if accountId:
            cmd.append(accountId)

        returncode, stdout, stderr = self._runCommand(cmd, identity)

        result = {"success": returncode == 0}

        if returncode == 0:
            balanceText = stdout.strip()
            # Parse "X.XXXXXXXX ICP"
            try:
                icpAmount = float(balanceText.split()[0])
                e8sAmount = int(icpAmount * 100_000_000)
            except:
                icpAmount = 0.0
                e8sAmount = 0

            result.update(
                {"balanceText": balanceText, "balanceIcp": icpAmount, "balanceE8s": e8sAmount}
            )
        else:
            result["error"] = stderr

        return result

    def ledgerSend(
        self, toAddress: str, amount: str, memo: str, identity: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send ICP: dfx ledger transfer <to> --amount <amount> --memo <memo>"""
        returncode, stdout, stderr = self._runCommand(
            [
                "ledger",
                "transfer",
                toAddress,
                "--amount",
                amount,
                "--memo",
                memo,
                "--network",
                self.network,
            ],
            identity,
        )

        return {
            "success": returncode == 0,
            "to": toAddress,
            "amount": amount,
            "memo": memo,
            "output": stdout.strip() if returncode == 0 else stderr,
        }

    # =========================
    # CYCLES COMMANDS
    # =========================

    def cyclesGetBalance(self, identity: Optional[str] = None) -> Dict[str, Any]:
        """Get cycles balance: dfx cycles balance"""
        returncode, stdout, stderr = self._runCommand(
            ["cycles", "balance", "--network", self.network], identity
        )

        result = {"success": returncode == 0}

        if returncode == 0:
            balanceText = stdout.strip()
            # Parse cycles amount from text like "1.234 TC (trillion cycles)."
            cyclesAmount = self._parseCyclesFromText(balanceText)

            result.update(
                {
                    "balanceText": balanceText,
                    "balanceCycles": cyclesAmount,
                    "balanceTc": cyclesAmount / 1_000_000_000_000,
                }
            )
        else:
            result["error"] = stderr

        return result

    def cyclesConvert(self, amount: str, identity: Optional[str] = None) -> Dict[str, Any]:
        """Convert ICP to cycles: dfx cycles convert --amount <amount>"""
        returncode, stdout, stderr = self._runCommand(
            ["cycles", "convert", "--amount", amount, "--network", self.network], identity
        )

        result = {
            "success": returncode == 0,
            "amount": amount,
            "output": stdout.strip() if returncode == 0 else stderr,
        }

        if returncode == 0:
            # Get new balance after conversion
            newBalance = self.cyclesGetBalance(identity)
            result["newBalance"] = newBalance

        return result

    def cyclesSend(
        self, toPrincipal: str, amount: str, identity: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send cycles: dfx cycles transfer <principal> <amount>"""
        returncode, stdout, stderr = self._runCommand(
            ["cycles", "transfer", toPrincipal, amount, "--network", self.network], identity
        )

        return {
            "success": returncode == 0,
            "to": toPrincipal,
            "amount": amount,
            "output": stdout.strip() if returncode == 0 else stderr,
        }

    def cyclesTopUp(
        self, canisterId: str, amount: str, identity: Optional[str] = None
    ) -> Dict[str, Any]:
        """Top up canister: dfx cycles top-up <canister_id> <amount>"""
        returncode, stdout, stderr = self._runCommand(
            ["cycles", "top-up", canisterId, amount, "--network", self.network], identity
        )

        return {
            "success": returncode == 0,
            "canisterId": canisterId,
            "amount": amount,
            "output": stdout.strip() if returncode == 0 else stderr,
        }

    # =========================
    # WALLET COMMANDS
    # =========================

    def walletGetBalance(self, identity: Optional[str] = None) -> Dict[str, Any]:
        """Get wallet balance: dfx wallet balance"""
        returncode, stdout, stderr = self._runCommand(
            ["wallet", "balance", "--network", self.network], identity
        )

        result = {"success": returncode == 0}

        if returncode == 0:
            balanceText = stdout.strip()
            cyclesAmount = self._parseCyclesFromText(balanceText)

            result.update(
                {"balanceText": balanceText, "balanceCycles": cyclesAmount, "walletExists": True}
            )
        else:
            result.update({"balanceCycles": 0, "walletExists": False, "error": stderr})

        return result

    # =========================
    # CANISTER COMMANDS
    # =========================

    def canisterCreate(
        self,
        name: Optional[str] = None,
        withCycles: Optional[str] = None,
        identity: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create canister: dfx canister create [name] [--with-cycles amount]"""
        cmd = ["canister", "create", "--network", self.network]

        if name:
            cmd.append(name)
        else:
            cmd.append("--all")

        if withCycles:
            cmd.extend(["--with-cycles", withCycles])

        returncode, stdout, stderr = self._runCommand(cmd, identity)

        result = {"success": returncode == 0}

        if returncode == 0:
            canisterId = self._extractCanisterId(stdout + stderr)
            result.update({"canisterId": canisterId, "name": name, "output": stdout.strip()})
        else:
            result["error"] = stderr

        return result

    def canisterGetStatus(self, canisterId: str, identity: Optional[str] = None) -> Dict[str, Any]:
        """Get canister status: dfx canister status <canister_id>"""
        returncode, stdout, stderr = self._runCommand(
            ["canister", "status", canisterId, "--network", self.network], identity
        )

        result = {"success": returncode == 0, "canisterId": canisterId}

        if returncode == 0:
            status = self._parseCanisterStatus(stdout)
            result.update({"status": status, "output": stdout.strip()})
        else:
            result["error"] = stderr

        return result

    def canisterDelete(self, canisterId: str, identity: Optional[str] = None) -> Dict[str, Any]:
        """Delete canister: dfx canister delete <canister_id>"""
        returncode, stdout, stderr = self._runCommand(
            ["canister", "delete", canisterId, "--network", self.network], identity
        )

        return {
            "success": returncode == 0,
            "canisterId": canisterId,
            "output": stdout.strip() if returncode == 0 else stderr,
        }

    def canisterDeploy(
        self, name: Optional[str] = None, identity: Optional[str] = None
    ) -> Dict[str, Any]:
        """Deploy canister: dfx deploy [name]"""
        cmd = ["deploy", "--network", self.network]

        if name:
            cmd.append(name)

        returncode, stdout, stderr = self._runCommand(cmd, identity)

        result = {"success": returncode == 0}

        if returncode == 0:
            result.update({"output": stdout.strip()})
        else:
            result["error"] = stderr

        return result

    # =========================
    # UTILITY FUNCTIONS
    # =========================

    def _parseCyclesFromText(self, text: str) -> int:
        """Parse cycles amount from dfx output text."""
        import re

        text = text.lower()

        # Try "X.XXX TC (trillion cycles)"
        tcMatch = re.search(r"(\d+\.?\d*)\s*tc", text)
        if tcMatch:
            return int(float(tcMatch.group(1)) * 1_000_000_000_000)

        # Try "XXXXXX cycles"
        cyclesMatch = re.search(r"(\d+)\s*cycles", text)
        if cyclesMatch:
            return int(cyclesMatch.group(1))

        return 0

    def _extractCanisterId(self, output: str) -> Optional[str]:
        """Extract canister ID from dfx output."""
        import re

        match = re.search(r"([a-z0-9]+-[a-z0-9]+-[a-z0-9]+-[a-z0-9]+-[a-z0-9]+)", output.lower())
        return match.group(1) if match else None

    def _parseCanisterStatus(self, output: str) -> Dict[str, Any]:
        """Parse canister status from dfx output."""
        status = {"status": "unknown", "cycles": 0, "memorySize": 0}

        for line in output.split("\n"):
            lineLower = line.lower().strip()

            if lineLower.startswith("status:"):
                status["status"] = line.split(":", 1)[1].strip()
            elif "cycles" in lineLower:
                import re

                match = re.search(r"(\d+)", line)
                if match:
                    status["cycles"] = int(match.group(1))
            elif "memory size" in lineLower:
                import re

                match = re.search(r"(\d+)", line)
                if match:
                    status["memorySize"] = int(match.group(1))

        return status

    # =========================
    # HIGH-LEVEL OPERATIONS
    # =========================

    def getUserStatus(self, identityName: str) -> Dict[str, Any]:
        """Get comprehensive user status with all balances."""
        result = {"identityName": identityName, "success": True, "balances": {}}

        try:
            # Get all balance types
            icp = self.ledgerGetBalance(identity=identityName)
            cycles = self.cyclesGetBalance(identity=identityName)
            wallet = self.walletGetBalance(identity=identityName)

            result["balances"] = {"icp": icp, "cycles": cycles, "wallet": wallet}

            # Calculate funding status
            icpAmount = icp.get("balanceE8s", 0)
            cyclesAmount = cycles.get("balanceCycles", 0)

            result["fundingStatus"] = {
                "hasIcp": icpAmount >= 10_000_000,  # 0.1 ICP
                "hasCycles": cyclesAmount >= 20_000_000,  # 20M cycles
                "canConvert": icpAmount >= 10_000_000,
                "readyToDeploy": cyclesAmount >= 20_000_000,
            }

        except Exception as e:
            result["success"] = False
            result["error"] = str(e)

        return result

    def autoConvertIcp(self, identityName: str, reserveIcp: float = 0.01) -> Dict[str, Any]:
        """Automatically convert available ICP to cycles, reserving some for fees."""
        try:
            # Get current ICP balance
            balance = self.ledgerGetBalance(identity=identityName)
            if not balance["success"]:
                return {"success": False, "error": "Could not get ICP balance"}

            icpAmount = balance["balanceIcp"]
            if icpAmount < (reserveIcp + 0.01):  # Need at least reserve + 0.01 to convert
                return {
                    "success": False,
                    "error": f"Insufficient ICP. Have {icpAmount}, need at least {reserveIcp + 0.01}",
                }

            # Calculate amount to convert
            convertAmount = icpAmount - reserveIcp

            # Round to 8 decimal places (e8s precision) to avoid floating point issues
            convertAmount = round(convertAmount, 8)

            # Convert to cycles
            result = self.cyclesConvert(str(convertAmount), identityName)

            if result["success"]:
                result["convertedAmount"] = convertAmount
                result["reservedAmount"] = reserveIcp

            return result

        except Exception as e:
            return {"success": False, "error": str(e)}
