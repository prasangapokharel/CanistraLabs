"""Automated funding detection service using ICRC Rosetta API."""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.services.rosettaClient import RosettaClient
from app.services.icpIdentityManager import ICPIdentityManager, ICPError
from app.config import settings
from app.utils.cycleRequirements import (
    deploy_ready,
    funding_requirements,
    min_cycles_for_deploy,
    min_icp_to_convert_e8s,
)

logger = logging.getLogger(__name__)


def format_cycles(cycles_amount: int) -> str:
    """
    Format cycles with appropriate units (T for trillion, B for billion, M for million).

    Args:
        cycles_amount: Number of cycles to format

    Returns:
        Formatted string with appropriate unit
    """
    if cycles_amount == 0:
        return "0 cycles"

    # Convert to trillions
    if cycles_amount >= 1_000_000_000_000:
        tc = cycles_amount / 1_000_000_000_000
        return f"{tc:.3f} TC"

    # Convert to billions
    elif cycles_amount >= 1_000_000_000:
        bc = cycles_amount / 1_000_000_000
        return f"{bc:.2f} BC"

    # Convert to millions
    elif cycles_amount >= 1_000_000:
        mc = cycles_amount / 1_000_000
        return f"{mc:.1f} MC"

    # Less than a million, show with commas
    else:
        return f"{cycles_amount:,} cycles"


class AutoFundingDetector:
    """
    Automated funding detection service.

    Monitors ICP/TESTICP transfers to user accounts and automatically converts
    tokens to cycles for seamless deployment experience.
    """

    def __init__(self, rosetta_client: RosettaClient = None):
        """Initialize funding detector."""
        self.rosetta = rosetta_client or self._build_rosetta_client()
        self.monitoring_active = False

    @staticmethod
    def _build_rosetta_client() -> RosettaClient:
        if settings.use_testicp:
            return RosettaClient(
                node_address=settings.rosetta_url,
                canister_id=settings.testicp_ledger_canister_id,
                network_identifier="mainnet",
            )
        return RosettaClient(
            node_address=settings.rosetta_url,
            canister_id=settings.icp_ledger_canister_id,
            network_identifier="mainnet",
        )

    def _get_balance_via_dfx(self, user: User) -> tuple[str, str]:
        from app.services.dfxCommand import DfxCommand

        if not user.dfx_identity_name:
            return "0", f"0 {settings.token_symbol}"

        dfx = DfxCommand.from_settings()
        balance = dfx.ledgerGetBalance(identity=user.dfx_identity_name)
        if balance.get("success"):
            e8s = str(balance.get("balanceE8s", 0))
            symbol = settings.token_symbol
            amount = balance.get("balanceIcp", 0)
            formatted = f"{amount:.8f} {symbol}".rstrip("0").rstrip(".")
            if formatted.endswith(f" {symbol}"):
                pass
            elif not formatted.endswith(symbol):
                formatted = f"{amount} {symbol}"
            return e8s, formatted
        return "0", f"0 {settings.token_symbol}"

    def _get_icp_balance_e8s(self, user: User) -> tuple[str, str]:
        """Return (balance_e8s, formatted_balance) for ICP or TESTICP."""
        if settings.use_testicp:
            return self._get_balance_via_dfx(user)

        try:
            balance_info = self.rosetta.get_account_balance_by_account_id(user.account_id)
            icp_balance = "0"
            if balance_info and "balances" in balance_info:
                for balance in balance_info["balances"]:
                    symbol = balance.get("currency", {}).get("symbol", "")
                    if symbol in ("ICP", "TESTICP", settings.token_symbol):
                        icp_balance = balance["value"]
                        break

            if icp_balance != "0":
                formatted = self.rosetta.format_token_amount(int(icp_balance))
                return icp_balance, formatted
        except Exception as e:
            logger.warning(f"Rosetta balance check failed, using dfx: {e}")

        return self._get_balance_via_dfx(user)

    async def check_user_funding_status(self, session: AsyncSession, user: User) -> Dict[str, Any]:
        """
        Check funding status for a specific user.

        Args:
            session: Database session
            user: User to check funding for

        Returns:
            Dictionary with funding status and balance information
        """
        try:
            if not user.principal_id or not user.account_id:
                return {
                    "funded": False,
                    "balance": "0",
                    "cycles_balance": "0",
                    "needs_setup": True,
                    "message": "No ICP identity found",
                }

            # Get token balance (ICP or TESTICP)
            icp_balance, formatted_icp = self._get_icp_balance_e8s(user)

            # Get cycles balance via dfx
            cycles_balance = await ICPIdentityManager.check_wallet_balance(user)

            # Update user's cached balance
            user.wallet_cycles_balance = cycles_balance
            await session.flush()

            # Determine funding status
            icp_amount = int(icp_balance)
            cycles_amount = int(cycles_balance)

            min_icp_required = min_icp_to_convert_e8s()
            min_cycles_required = min_cycles_for_deploy()

            is_funded = deploy_ready(cycles_amount)
            has_pending_icp = icp_amount >= min_icp_required
            req = funding_requirements(cycles_amount, icp_amount)

            return {
                "funded": is_funded,
                "balance": icp_balance,
                "cycles_balance": cycles_balance,
                "needs_setup": False,
                "has_pending_icp": has_pending_icp,
                "auto_convert_available": has_pending_icp,
                "formatted_icp": formatted_icp,
                "formatted_cycles": format_cycles(cycles_amount),
                "token_symbol": settings.token_symbol,
                "network": settings.wallet_network,
                "use_testicp": settings.use_testicp,
                "deploy_ready": is_funded,
                "requirements": req,
                "message": self._get_funding_message(
                    is_funded, has_pending_icp, icp_amount, cycles_amount
                ),
            }

        except Exception as e:
            logger.error(f"Failed to check funding status for user {user.id}: {str(e)}")
            return {
                "funded": False,
                "balance": "0",
                "cycles_balance": user.wallet_cycles_balance or "0",
                "needs_setup": False,
                "error": str(e),
                "message": "Unable to check funding status",
            }

    def _get_funding_message(
        self, is_funded: bool, has_pending_icp: bool, icp_amount: int, cycles_amount: int
    ) -> str:
        """Generate appropriate funding status message."""
        req = funding_requirements(cycles_amount, icp_amount)
        if is_funded:
            return f"Ready to deploy on {req['deploy_network']} ({format_cycles(cycles_amount)} available)"
        if cycles_amount > 0 and not is_funded:
            return (
                f"You have {format_cycles(cycles_amount)} but mainnet deploy needs at least "
                f"{req['formatted_cycles_required']}. Convert about {req['recommended_icp_to_fund']} ICP "
                f"to cycles, then refresh."
            )
        if has_pending_icp:
            icp_formatted = self.rosetta.format_token_amount(icp_amount)
            return f"Found {icp_formatted} — convert to cycles for mainnet deploy"
        if icp_amount > 0:
            icp_formatted = self.rosetta.format_token_amount(icp_amount)
            return (
                f"Found {icp_formatted} — need at least {req['min_icp_to_convert']} to convert "
                f"(ledger fee reserve)"
            )
        token = settings.token_symbol
        if settings.use_testicp:
            return f"Get free {token} from faucet.internetcomputer.org, then refresh"
        return (
            f"Deposit {token} to your Account ID. For a first mainnet deploy, "
            f"convert ~{req['recommended_icp_to_fund']} ICP to cycles."
        )

    async def auto_convert_icp_to_cycles(self, session: AsyncSession, user: User) -> Dict[str, Any]:
        """
        Automatically convert ICP to cycles using the clean dfxCommand service.

        Args:
            session: Database session
            user: User to convert ICP for

        Returns:
            Conversion result information
        """
        try:
            if not user.dfx_identity_name:
                raise ICPError("No ICP identity found for user")

            logger.info(f"Starting ICP to cycles conversion for user {user.id}")

            # Use the clean dfxCommand service
            from app.services.dfxCommand import DfxCommand

            dfx = DfxCommand.from_settings()

            # Auto-convert available ICP to cycles
            result = dfx.autoConvertIcp(user.dfx_identity_name)

            if result["success"]:
                # Get new cycles balance and update user
                newBalance = dfx.cyclesGetBalance(user.dfx_identity_name)
                if newBalance["success"]:
                    user.wallet_cycles_balance = str(newBalance["balanceCycles"])
                    await session.flush()

                logger.info(f"Conversion successful for user {user.id}")

                return {
                    "success": True,
                    "message": f"Successfully converted {result.get('convertedAmount', 0)} ICP to cycles",
                    "cycles_balance": newBalance.get("balanceCycles", 0),
                    "formatted_cycles": format_cycles(newBalance.get("balanceCycles", 0)),
                }
            else:
                return {
                    "success": False,
                    "message": result.get("error") or f"Conversion failed: {result.get('error', 'Unknown error')}",
                    "error": result.get("error"),
                }

        except Exception as e:
            logger.error(f"ICP to cycles conversion failed for user {user.id}: {str(e)}")
            return {"success": False, "message": f"Conversion failed: {str(e)}", "error": str(e)}

    async def monitor_funding_for_users(
        self, session: AsyncSession, user_ids: List[int] = None
    ) -> Dict[str, Any]:
        """
        Monitor funding status for multiple users.

        Args:
            session: Database session
            user_ids: Optional list of specific user IDs to monitor

        Returns:
            Summary of monitoring results
        """
        try:
            # Get users to monitor
            if user_ids:
                stmt = select(User).where(User.id.in_(user_ids))
            else:
                # Monitor users with identities who might need funding
                stmt = select(User).where(
                    User.dfx_identity_name.isnot(None), User.is_active == True
                )

            result = await session.execute(stmt)
            users = result.scalars().all()

            monitoring_results = {
                "monitored_users": len(users),
                "funded_users": 0,
                "pending_conversion": 0,
                "needs_funding": 0,
                "errors": 0,
                "user_statuses": [],
            }

            for user in users:
                try:
                    status = await self.check_user_funding_status(session, user)

                    user_result = {
                        "user_id": user.id,
                        "email": user.email,
                        "funded": status["funded"],
                        "has_pending_icp": status.get("has_pending_icp", False),
                        "message": status["message"],
                    }

                    if status["funded"]:
                        monitoring_results["funded_users"] += 1
                    elif status.get("has_pending_icp"):
                        monitoring_results["pending_conversion"] += 1
                    else:
                        monitoring_results["needs_funding"] += 1

                    monitoring_results["user_statuses"].append(user_result)

                except Exception as e:
                    logger.error(f"Failed to monitor user {user.id}: {str(e)}")
                    monitoring_results["errors"] += 1
                    monitoring_results["user_statuses"].append(
                        {"user_id": user.id, "email": user.email, "error": str(e)}
                    )

            await session.commit()

            logger.info(
                f"Funding monitoring complete: {monitoring_results['funded_users']}/{monitoring_results['monitored_users']} users funded"
            )

            return monitoring_results

        except Exception as e:
            logger.error(f"Funding monitoring failed: {str(e)}")
            return {"monitored_users": 0, "error": str(e)}

    async def get_funding_instructions(
        self, session: AsyncSession, user: User
    ) -> Dict[str, Any]:
        """
        Generate detailed funding instructions with live wallet status.
        """
        if not user.principal_id or not user.account_id:
            return {"error": "No ICP identity found", "instructions": []}

        funding_status = await self.check_user_funding_status(session, user)

        instructions = [
            {
                "step": 1,
                "title": f"Get Your {settings.token_symbol} Address (Account ID)",
                "description": "This is your funding address - NOT the Principal ID",
                "data": {
                    "account_id": user.account_id,
                    "principal_id": user.principal_id,
                    "funding_address": user.account_id,
                    "copyable": True,
                    "note": f"Send {settings.token_symbol} to Account ID, not Principal ID",
                },
            },
        ]

        if settings.use_testicp:
            instructions.extend(
                [
                    {
                        "step": 2,
                        "title": "Get Free TESTICP from Faucet",
                        "description": "Request 10 TESTICP tokens for development (no real ICP needed)",
                        "options": [
                            {
                                "name": "IC Test Token Faucet",
                                "url": "https://faucet.internetcomputer.org",
                            },
                        ],
                    },
                    {
                        "step": 3,
                        "title": "Paste Account ID in Faucet",
                        "description": "Select TESTICP and paste your Account ID above",
                        "data": {
                            "recipient": user.account_id,
                            "recipient_type": "Account ID",
                            "minimum_amount": "1 TESTICP",
                            "network": "Internet Computer (TESTICP)",
                        },
                    },
                ]
            )
        else:
            instructions.extend(
                [
                    {
                        "step": 2,
                        "title": "Buy ICP Tokens",
                        "description": "Purchase ICP from exchanges (minimum 0.01 ICP)",
                        "options": [
                            {"name": "Coinbase", "url": "https://coinbase.com"},
                            {"name": "Binance", "url": "https://binance.com"},
                            {"name": "Kraken", "url": "https://kraken.com"},
                        ],
                    },
                    {
                        "step": 3,
                        "title": "Transfer to Your ICP Address",
                        "description": "Send ICP to your Account ID (hex format)",
                        "data": {
                            "recipient": user.account_id,
                            "recipient_type": "Account ID",
                            "minimum_amount": "0.01 ICP",
                            "network": "Internet Computer (ICP)",
                            "warning": "Use Account ID, not Principal ID for ICP transfers",
                        },
                    },
                ]
            )

        instructions.append(
            {
                "step": 4,
                "title": "Automatic Conversion",
                "description": "We'll detect your deposit and offer to convert to cycles",
                "data": {"auto_detect": True, "refresh_endpoint": "/api/v1/wallet/refresh-balance"},
            }
        )

        return {
            "principal_id": user.principal_id,
            "account_id": user.account_id,
            "funding_address": user.account_id,
            "current_status": {
                "funded": funding_status.get("funded", False),
                "balance": funding_status.get("formatted_icp", funding_status.get("balance", "0")),
                "cycles_balance": funding_status.get("formatted_cycles", funding_status.get("cycles_balance", "0")),
                "needs_setup": funding_status.get("needs_setup", False),
                "auto_convert_available": funding_status.get("auto_convert_available", False),
                "has_pending_icp": funding_status.get("has_pending_icp", False),
            },
            "instructions": instructions,
            "quick_links": {
                "nns_dapp": "https://nns.ic0.app/",
                "internet_identity": "https://identity.ic0.app/",
                "testicp_faucet": "https://faucet.internetcomputer.org/",
                "dfinity_faucet": "https://faucet.dfinity.org/",
            },
        }

    async def check_user_funding_status_simple(self, user: User) -> Dict[str, Any]:
        """Simple funding status check without database session."""
        try:
            if not user.account_id:
                return {"funded": False, "balance": "0", "cycles_balance": "0", "needs_setup": True}

            # Simple return for now - in production, integrate with Rosetta API
            return {
                "funded": False,
                "balance": "0",
                "cycles_balance": user.wallet_cycles_balance or "0",
                "needs_setup": False,
                "message": "Ready to receive ICP funding",
            }
        except Exception as e:
            logger.error(f"Simple funding check failed: {str(e)}")
            return {"funded": False, "balance": "0", "cycles_balance": "0", "needs_setup": False}

    def is_rosetta_healthy(self) -> bool:
        """Check if Rosetta API is accessible."""
        return self.rosetta.is_healthy()

    def get_network_info(self) -> Dict[str, Any]:
        """Get network information from Rosetta API."""
        try:
            return {
                "network_status": self.rosetta.get_network_status(),
                "network_options": self.rosetta.get_network_options(),
                "token_info": self.rosetta.get_token_info(),
                "healthy": True,
            }
        except Exception as e:
            return {"error": str(e), "healthy": False}
