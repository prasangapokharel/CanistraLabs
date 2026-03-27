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

    Monitors ICP transfers to user accounts and automatically converts
    ICP to cycles for seamless deployment experience.
    """

    def __init__(self, rosetta_client: RosettaClient = None):
        """Initialize funding detector."""
        self.rosetta = rosetta_client or RosettaClient(
            node_address="https://rosetta-api.internetcomputer.org",  # Explicit mainnet URL
            network_identifier="00000000000000020101",  # Use actual IC mainnet network ID
        )
        self.monitoring_active = False

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

            # Get ICP balance via Rosetta API using account_id directly
            balance_info = self.rosetta.get_account_balance_by_account_id(user.account_id)

            icp_balance = "0"
            if balance_info and "balances" in balance_info:
                for balance in balance_info["balances"]:
                    if balance.get("currency", {}).get("symbol") == "ICP":
                        icp_balance = balance["value"]
                        break

            # Get cycles balance via dfx
            cycles_balance = await ICPIdentityManager.check_wallet_balance(user)

            # Update user's cached balance
            user.wallet_cycles_balance = cycles_balance
            await session.flush()

            # Determine funding status
            icp_amount = int(icp_balance)
            cycles_amount = int(cycles_balance)

            # Minimum requirements (0.1 ICP or 20M cycles)
            min_icp_required = 10_000_000  # 0.1 ICP (8 decimals)
            min_cycles_required = 20_000_000  # 20M cycles

            is_funded = cycles_amount >= min_cycles_required
            has_pending_icp = icp_amount >= min_icp_required

            return {
                "funded": is_funded,
                "balance": icp_balance,
                "cycles_balance": cycles_balance,
                "needs_setup": False,
                "has_pending_icp": has_pending_icp,
                "auto_convert_available": has_pending_icp and not is_funded,
                "formatted_icp": self.rosetta.format_token_amount(icp_amount),
                "formatted_cycles": format_cycles(cycles_amount),
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
        if is_funded:
            return f"Wallet ready with {cycles_amount:,} cycles"
        elif has_pending_icp:
            icp_formatted = self.rosetta.format_token_amount(icp_amount)
            return f"Found {icp_formatted} - click to convert to cycles"
        else:
            return "Wallet needs funding - minimum 0.1 ICP required"

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

            dfx = DfxCommand(network="ic")

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
                    "message": f"Conversion failed: {result.get('error', 'Unknown error')}",
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

    async def get_funding_instructions(self, user: User) -> Dict[str, Any]:
        """
        Generate detailed funding instructions for a user.

        Args:
            user: User to generate instructions for

        Returns:
            Detailed funding instructions
        """
        if not user.principal_id:
            return {"error": "No ICP identity found", "instructions": []}

        # Check current status
        funding_status = self.check_user_funding_status_simple(user)

        instructions = [
            {
                "step": 1,
                "title": "Get Your ICP Address (Account ID)",
                "description": "This is your ICP funding address - NOT the Principal ID",
                "data": {
                    "account_id": user.account_id,
                    "principal_id": user.principal_id,
                    "funding_address": user.account_id,
                    "copyable": True,
                    "note": "⚠️ Send ICP to Account ID, not Principal ID",
                },
            },
            {
                "step": 2,
                "title": "Buy ICP Tokens",
                "description": "Purchase ICP from exchanges (minimum 0.1 ICP)",
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
                    "minimum_amount": "0.1 ICP",
                    "network": "Internet Computer (ICP)",
                    "warning": "⚠️ Use Account ID, not Principal ID for ICP transfers",
                },
            },
            {
                "step": 4,
                "title": "Automatic Conversion",
                "description": "We'll detect your deposit and offer to convert to cycles",
                "data": {"auto_detect": True, "refresh_endpoint": "/api/v1/wallet/refresh-balance"},
            },
        ]

        return {
            "principal_id": user.principal_id,
            "account_id": user.account_id,
            "current_status": {
                "funded": False,
                "balance": "0",
                "cycles_balance": "0",
                "needs_setup": False,
            },
            "instructions": instructions,
            "quick_links": {
                "nns_dapp": "https://nns.ic0.app/",
                "internet_identity": "https://identity.ic0.app/",
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
