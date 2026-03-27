"""
Cron service for automated ICP to cycles conversion.

This service runs every 30 seconds to check user ICP balances and automatically
convert ICP to cycles when sufficient balance is available.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database.db import get_db, async_session_maker
from app.models.user import User
from app.services.autoFundingDetector import AutoFundingDetector
from app.services.rosettaClient import RosettaClient
from app.services.icpIdentityManager import ICPIdentityManager

logger = logging.getLogger(__name__)


def format_icp(raw_amount: int) -> str:
    """
    Format raw ICP amount to human-readable string.

    Args:
        raw_amount: Raw ICP amount in smallest unit (e8s)

    Returns:
        Formatted ICP amount string
    """
    # ICP has 8 decimals
    formatted_amount = raw_amount / (10**8)
    return f"{formatted_amount:.8f} ICP"


class ICPCronService:
    """Service for automated ICP to cycles conversion."""

    def __init__(self):
        self.auto_funding_detector = AutoFundingDetector()
        self.is_running = False
        self.conversion_interval = 30  # seconds
        self.min_icp_for_conversion = 100_000_000  # 1 ICP in e8s
        self.last_run = None
        self.stats = {
            "total_conversions": 0,
            "total_icp_converted": 0,
            "total_cycles_generated": 0,
            "last_conversion_time": None,
            "errors": 0,
        }

    async def start_service(self) -> Dict[str, Any]:
        """
        Start the cron service for automatic ICP to cycles conversion.

        Returns:
            Service start result
        """
        if self.is_running:
            return {
                "success": False,
                "message": "Cron service is already running",
                "status": "running",
            }

        self.is_running = True
        logger.info("Starting ICP to cycles cron service")

        # Start the background task
        asyncio.create_task(self._run_conversion_loop())

        return {
            "success": True,
            "message": "ICP to cycles cron service started successfully",
            "status": "running",
            "interval": f"{self.conversion_interval} seconds",
            "started_at": datetime.utcnow().isoformat(),
        }

    async def stop_service(self) -> Dict[str, Any]:
        """
        Stop the cron service.

        Returns:
            Service stop result
        """
        if not self.is_running:
            return {"success": False, "message": "Cron service is not running", "status": "stopped"}

        self.is_running = False
        logger.info("Stopping ICP to cycles cron service")

        return {
            "success": True,
            "message": "ICP to cycles cron service stopped successfully",
            "status": "stopped",
            "stopped_at": datetime.utcnow().isoformat(),
        }

    async def get_service_status(self) -> Dict[str, Any]:
        """
        Get current service status and statistics.

        Returns:
            Service status and stats
        """
        return {
            "status": "running" if self.is_running else "stopped",
            "interval": f"{self.conversion_interval} seconds",
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "stats": {
                "total_conversions": self.stats["total_conversions"],
                "total_icp_converted": format_icp(self.stats["total_icp_converted"]),
                "total_cycles_generated": f"{self.stats['total_cycles_generated']:,} cycles",
                "last_conversion_time": self.stats["last_conversion_time"],
                "errors": self.stats["errors"],
            },
            "uptime": (datetime.utcnow() - self.last_run).total_seconds() if self.last_run else 0,
        }

    async def trigger_manual_conversion(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Manually trigger ICP to cycles conversion for a specific user or all users.

        Args:
            user_id: Optional specific user ID to convert for

        Returns:
            Manual conversion result
        """
        logger.info(f"Manual conversion triggered for user_id: {user_id}")

        try:
            async with async_session_maker() as session:
                if user_id:
                    # Convert for specific user
                    user = await session.get(User, user_id)
                    if not user:
                        return {"success": False, "message": f"User {user_id} not found"}

                    result = await self._convert_user_icp_to_cycles(session, user)
                    await session.commit()
                    return result
                else:
                    # Convert for all eligible users
                    results = await self._process_all_users(session)
                    await session.commit()
                    return results

        except Exception as e:
            logger.error(f"Manual conversion failed: {str(e)}")
            return {"success": False, "message": f"Manual conversion failed: {str(e)}"}

    async def _run_conversion_loop(self):
        """
        Main conversion loop that runs every 30 seconds.
        """
        logger.info(f"Starting conversion loop with {self.conversion_interval}s interval")

        while self.is_running:
            try:
                await self._process_conversion_cycle()
                self.last_run = datetime.utcnow()

                # Wait for the next cycle
                await asyncio.sleep(self.conversion_interval)

            except Exception as e:
                logger.error(f"Conversion cycle failed: {str(e)}")
                self.stats["errors"] += 1
                # Continue running even if there's an error
                await asyncio.sleep(self.conversion_interval)

    async def _process_conversion_cycle(self):
        """
        Process one conversion cycle for all users.
        """
        logger.debug("Processing conversion cycle")

        try:
            async with async_session_maker() as session:
                results = await self._process_all_users(session)
                await session.commit()

                if results.get("conversions_performed", 0) > 0:
                    logger.info(
                        f"Conversion cycle completed: {results['conversions_performed']} conversions"
                    )

        except Exception as e:
            logger.error(f"Conversion cycle error: {str(e)}")
            raise

    async def _process_all_users(self, session: AsyncSession) -> Dict[str, Any]:
        """
        Process ICP to cycles conversion for all users with ICP identities.

        Args:
            session: Database session

        Returns:
            Processing results
        """
        try:
            # Get all users with DFX identities (potential ICP holders)
            result = await session.execute(
                select(User).where(
                    and_(User.dfx_identity_name.isnot(None), User.dfx_identity_name != "")
                )
            )
            users = result.scalars().all()

            conversions_performed = 0
            total_icp_converted = 0
            total_cycles_generated = 0
            errors = []

            for user in users:
                try:
                    conversion_result = await self._convert_user_icp_to_cycles(session, user)

                    if conversion_result.get("success") and conversion_result.get("converted"):
                        conversions_performed += 1
                        total_icp_converted += conversion_result.get("icp_amount", 0)
                        total_cycles_generated += conversion_result.get("cycles_generated", 0)

                        # Update stats
                        self.stats["total_conversions"] += 1
                        self.stats["total_icp_converted"] += conversion_result.get("icp_amount", 0)
                        self.stats["total_cycles_generated"] += conversion_result.get(
                            "cycles_generated", 0
                        )
                        self.stats["last_conversion_time"] = datetime.utcnow().isoformat()

                except Exception as e:
                    logger.error(f"Error converting ICP for user {user.id}: {str(e)}")
                    errors.append(f"User {user.id}: {str(e)}")
                    self.stats["errors"] += 1

            return {
                "success": True,
                "conversions_performed": conversions_performed,
                "total_icp_converted": format_icp(total_icp_converted),
                "total_cycles_generated": f"{total_cycles_generated:,} cycles",
                "users_processed": len(users),
                "errors": errors,
            }

        except Exception as e:
            logger.error(f"Error processing all users: {str(e)}")
            return {"success": False, "message": f"Error processing users: {str(e)}"}

    async def _convert_user_icp_to_cycles(
        self, session: AsyncSession, user: User
    ) -> Dict[str, Any]:
        """
        Convert ICP to cycles for a specific user if they have sufficient balance.

        Args:
            session: Database session
            user: User to convert ICP for

        Returns:
            Conversion result
        """
        try:
            # Check if user has sufficient ICP balance
            conversion_result = await self.auto_funding_detector.auto_convert_icp_to_cycles(
                session, user
            )

            if conversion_result.get("success"):
                logger.info(f"Successfully converted ICP to cycles for user {user.id}")
                return {
                    "success": True,
                    "converted": True,
                    "user_id": user.id,
                    "message": conversion_result.get("message", "Conversion successful"),
                    "icp_amount": conversion_result.get("icp_amount", 0),
                    "cycles_generated": conversion_result.get("cycles_balance", 0),
                }
            else:
                # No conversion needed or insufficient balance
                return {
                    "success": True,
                    "converted": False,
                    "user_id": user.id,
                    "message": conversion_result.get("message", "No conversion needed"),
                }

        except Exception as e:
            logger.error(f"Error converting ICP for user {user.id}: {str(e)}")
            return {
                "success": False,
                "converted": False,
                "user_id": user.id,
                "message": f"Conversion failed: {str(e)}",
            }


# Global instance
cron_service = ICPCronService()
